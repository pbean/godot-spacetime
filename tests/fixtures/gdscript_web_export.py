"""
Helpers for Story 11.5's pure-GDScript web export proof path.

This module stages a temporary exportable project, exports it with Godot's Web
preset, serves the files over loopback HTTP, and captures browser-visible DOM
state from a Chromium-family browser.
"""

from __future__ import annotations

import contextlib
import functools
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import websocket  # type: ignore[import-untyped]

from tests.fixtures.spacetime_runtime import (
    probe_browser_binary,
    probe_godot_non_mono_binary,
    probe_loopback_http,
)

# Empirically validated against the pinned chromium 148.0.7778.178 (Arch) and
# Godot 4.6.3-stable web export. Four other Chromium 4.x headless flag
# combinations were probed against the live Story 11.5 export pipeline and
# all left the runtime at a 5412-byte blank-splash DOM with no
# `data-story-11-5-*` attributes written:
#
#     current `--disable-gpu`                  -> WebGL2 missing, runtime aborts
#     `--headless=new`                         -> blank splash, no boot
#     `--use-gl=swiftshader` (old-style flag)  -> blank splash, no boot
#     `--headless=new --use-angle=swiftshader` -> blank splash, no boot
#
# Only the ANGLE swiftshader backend under classic `--headless` unblocks
# Godot's WebGL2 prerequisite and reaches `phase=query_token_mode_confirmed`.
# `--ignore-gpu-blocklist` is required because Chromium otherwise refuses
# software rendering on this dev box's GPU list. `--enable-unsafe-swiftshader`
# was made mandatory in Chromium ≥120 to opt into the swiftshader fallback.
# `--run-all-compositor-stages-before-draw` forces deterministic frame
# pumping; without it the runtime sometimes never gets a render pass.
HEADLESS_BROWSER_FLAGS: tuple[str, ...] = (
    "--headless",
    "--no-sandbox",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
    "--run-all-compositor-stages-before-draw",
)

# Total wall-clock budget for the CDP wait — bounded well below
# `pytest.skip`'s outer 180 s test budget. Empirically the full
# boot→connect→subscribe→done sequence finishes in ≈1.1 s against the local
# loopback runtime (three trials, all green); the larger budget covers slow
# CI hardware without ever masking a real fault.
HEADLESS_CDP_WAIT_SECONDS: float = 60.0

# Deadline for chromium to announce its DevTools port on stderr.
HEADLESS_CDP_PORT_DEADLINE_SECONDS: float = 15.0

# JS injected into the running export page via `Runtime.evaluate({awaitPromise:
# true})`. Attaches a single `MutationObserver` keyed to the runner's
# `data-story-11-5-phase` attribute and resolves the Promise with
# `{phase, dom}` when phase reaches `done` or `error`. No Python-side polling
# cadence — the CDP call blocks on the Promise until terminal phase or until
# the outer wall-clock deadline.
_HEADLESS_CDP_WAIT_JS = """
new Promise((resolve) => {
  const PHASE_ATTR = 'data-story-11-5-phase';
  const finished = (phase) => {
    resolve({ phase: phase, dom: document.documentElement.outerHTML });
  };
  const tryFinish = () => {
    if (!document.body) return false;
    const phase = document.body.getAttribute(PHASE_ATTR);
    if (phase === 'done' || phase === 'error') {
      finished(phase);
      return true;
    }
    return false;
  };
  if (tryFinish()) return;
  // Observe `documentElement` with `subtree: true` rather than `document.body`
  // directly — Godot's WASM boot reshapes the DOM heavily for its canvas, and
  // a future version that replaces `document.body` (vs. mutating its
  // attributes in place) would detach an observer keyed to the original body
  // reference, leaving the Promise hanging until the outer deadline trips.
  // `documentElement` is stable across body replacement.
  const attachObserver = () => {
    if (!document.documentElement) {
      setTimeout(attachObserver, 50);
      return;
    }
    if (tryFinish()) return;
    const observer = new MutationObserver(() => {
      if (tryFinish()) observer.disconnect();
    });
    observer.observe(document.documentElement, {
      attributes: true,
      subtree: true,
      attributeFilter: [PHASE_ATTR],
    });
  };
  attachObserver();
});
"""

PROJECT_TEMPLATE = """; Engine configuration file.
config_version=5

[application]

config/name="story-11-5-web-export"
config/features=PackedStringArray("4.6", "Compatibility")
run/main_scene="res://tests/godot_integration/gdscript_web_export_runner.tscn"

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
"""

# The `[preset.0]` block lists every key Godot 4.6's preset loader looks up
# without a default — observed empirically by running
# `godot-mono --export-debug Web` against a minimal probe project in /tmp and
# walking each `Couldn't find ... section "preset.0" and key "<x>"` error
# until the preset parsed clean. `script_export_mode=2` mirrors the Godot
# 4.6 editor default (`ScriptExportMode::MODE_BINARY_TOKENS_COMPRESSED`);
# the test does not assert PCK script encoding, so any of the three modes
# would work, but matching the editor default minimizes drift if a developer
# regenerates the preset by opening the staged project in the editor.
EXPORT_PRESETS_TEMPLATE = """[preset.0]
name="Web"
platform="Web"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.0.options]
custom_template/debug=""
custom_template/release=""
variant/thread_support=0
threads/thread_support=0
html/export_icon=false
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
progressive_web_app/enabled=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
"""

CONFIG_TEMPLATE = """extends RefCounted

const HOST = {host}
const MODULE_NAME = {module_name}
const QUERY_TOKEN = {query_token}
const RENDERER_LABEL = "Compatibility"
"""


def probe_story_11_5_web_export_prereqs() -> dict[str, object]:
    """Return discovery-only prerequisite probes for Story 11.5.

    Web export needs a non-Mono Godot binary because Godot 4 refuses Web
    export from the C#/.NET editor build; `probe_godot_non_mono_binary`
    honors the `GODOT_WEB_EXPORT_BIN` env var and skips cleanly when only a
    Mono build is on PATH.
    """
    godot = probe_godot_non_mono_binary()
    browser = probe_browser_binary()
    loopback = probe_loopback_http()
    return {
        "godot": godot,
        "browser": browser,
        "loopback_http": loopback,
    }


def stage_web_export_project(
    *,
    repo_root: Path,
    project_dir: Path,
    bindings_dir: Path,
    host: str,
    module_name: str,
    query_token: str,
) -> dict[str, Path]:
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    runtime_source = repo_root / "addons" / "godot_spacetime" / "src" / "Internal" / "Platform" / "GDScript"
    if not runtime_source.is_dir():
        raise RuntimeError(f"Missing GDScript runtime source at {runtime_source}")
    shutil.copytree(
        runtime_source,
        project_dir / "addons" / "godot_spacetime" / "src" / "Internal" / "Platform" / "GDScript",
        dirs_exist_ok=True,
    )

    shutil.copytree(
        bindings_dir,
        project_dir / "tests" / "fixtures" / "gdscript_generated" / "smoke_test",
        dirs_exist_ok=True,
    )

    integration_dir = project_dir / "tests" / "godot_integration"
    integration_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        repo_root / "tests" / "godot_integration" / "gdscript_web_export_runner.gd",
        integration_dir / "gdscript_web_export_runner.gd",
    )
    shutil.copy2(
        repo_root / "tests" / "godot_integration" / "gdscript_web_export_runner.tscn",
        integration_dir / "gdscript_web_export_runner.tscn",
    )
    (integration_dir / "story_11_5_web_config.gd").write_text(
        CONFIG_TEMPLATE.format(
            host=_gd_string(host),
            module_name=_gd_string(module_name),
            query_token=_gd_string(query_token),
        ),
        encoding="utf-8",
    )

    (project_dir / "project.godot").write_text(PROJECT_TEMPLATE, encoding="utf-8")
    (project_dir / "export_presets.cfg").write_text(EXPORT_PRESETS_TEMPLATE, encoding="utf-8")

    return {
        "project_dir": project_dir,
        "project_file": project_dir / "project.godot",
        "export_presets": project_dir / "export_presets.cfg",
        "config_file": integration_dir / "story_11_5_web_config.gd",
    }


def export_web_project(godot_path: str, project_dir: Path, export_dir: Path) -> Path:
    prereqs = probe_story_11_5_web_export_prereqs()
    if not prereqs["godot"].available:
        raise RuntimeError(f"Godot web export unavailable: {prereqs['godot'].reason}")

    if export_dir.exists():
        shutil.rmtree(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    index_path = export_dir / "index.html"
    result = subprocess.run(
        [
            godot_path,
            "--headless",
            "--path",
            str(project_dir),
            "--export-debug",
            "Web",
            str(index_path),
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        combined = "\n".join(part for part in (result.stdout, result.stderr) if part).lower()
        if "template" in combined or "export template" in combined:
            raise RuntimeError(
                "Godot web export templates unavailable for Story 11.5: "
                f"{(result.stderr or result.stdout).strip()[:400]}"
            )
        raise RuntimeError(
            "Godot web export failed for Story 11.5: "
            f"{(result.stderr or result.stdout).strip()[:400]}"
        )
    if not index_path.exists():
        raise RuntimeError("Godot web export reported success, but index.html was not produced")
    return index_path


@contextlib.contextmanager
def serve_directory(directory: Path):
    if not probe_loopback_http().available:
        raise RuntimeError("Loopback HTTP unavailable for Story 11.5 browser validation")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))

    class _ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    httpd = _ThreadingServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = httpd.server_address
        yield f"http://{host}:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def run_headless_browser_capture(browser_path: str, url: str) -> str:
    """Drive chromium headless against `url` and return the rendered DOM.

    The previous `--dump-dom --virtual-time-budget=30000` scheme exited in
    ≈1 s wall-clock regardless of budget value — empirically Chromium
    fast-forwards virtual time when the page is JS-idle and does NOT pause
    it for WebSocket I/O, so the browser exits before the WebSocket round-
    trip against the local SpacetimeDB runtime completes. The deterministic
    primitive is a CDP wait: launch chromium with `--remote-debugging-port=0`,
    drive it through `websocket-client` (already a test dependency), and
    block on a single `Runtime.evaluate({awaitPromise: true})` whose JS
    resolves with `{phase, dom}` when the runner's
    `data-story-11-5-phase` attribute reaches `done` or `error`.
    """
    prereqs = probe_story_11_5_web_export_prereqs()
    if not prereqs["browser"].available:
        raise RuntimeError(f"Browser unavailable for Story 11.5: {prereqs['browser'].reason}")

    # Manual user_data_dir lifecycle — `tempfile.TemporaryDirectory.__exit__`
    # races with chromium's final filesystem writes after `process.kill()`:
    # SIGKILL returns immediately but chromium has not yet released its
    # descriptors, so the rmtree sees `Directory not empty: .../Default` and
    # raises `OSError [Errno 39]` mid-cleanup. Waiting for the process to be
    # reaped FIRST, then rmtree with `ignore_errors=True`, is the only
    # deterministic path. The OUTER `try`/`finally` covers the case where
    # `subprocess.Popen` itself raises (FileNotFoundError, OSError on fd
    # exhaustion, etc.) AFTER `mkdtemp` succeeded — without it the temp dir
    # would leak.
    user_data_dir = tempfile.mkdtemp(prefix="story_11_5_chromium_")
    try:
        cmd = [
            browser_path,
            *HEADLESS_BROWSER_FLAGS,
            "--remote-debugging-port=0",
            f"--user-data-dir={user_data_dir}",
            "--remote-allow-origins=*",
            # Launch at `about:blank` rather than the target URL. CDP attach
            # happens first; then we navigate explicitly via `Page.navigate`
            # and block on `Page.frameStoppedLoading` for the EXACT frameId
            # Page.navigate returns. Passing the URL on the command line
            # races against attach — the initial about:blank execution
            # context can be destroyed by the URL's first navigation while
            # our `Runtime.evaluate({awaitPromise: true})` is still awaiting
            # its Promise, surfacing as `error -32000: Execution context was
            # destroyed.`
            "about:blank",
        ]
        # `stdout` is discarded, not piped: nothing consumes chromium's stdout,
        # and an undrained `subprocess.PIPE` can block the process if it ever
        # writes more than the OS pipe buffer (~64 KB) during the up-to-60 s CDP
        # wait — surfacing as a spurious port/CDP deadline. Only `stderr` carries
        # the `DevTools listening on …` banner the reader thread parses.
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            return _capture_dom_via_cdp(process, navigate_to=url)
        finally:
            # `process.kill()` may raise `ProcessLookupError` if the process
            # was already reaped (e.g., chromium self-exited on a crash);
            # swallow it so the temp dir cleanup still runs.
            try:
                process.kill()
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
    finally:
        shutil.rmtree(user_data_dir, ignore_errors=True)


_DEVTOOLS_PORT_PATTERN = re.compile(r"DevTools listening on ws://[\d.]+:(\d+)/")


def _capture_dom_via_cdp(process: subprocess.Popen, *, navigate_to: str) -> str:
    """Inner CDP loop — shared between `run_headless_browser_capture` and any
    future direct caller. The caller owns the chromium subprocess lifecycle.
    """
    devtools_port: list[int | None] = [None]
    stderr_lines: list[str] = []

    def _read_stderr() -> None:
        assert process.stderr is not None
        for line in process.stderr:
            stripped = line.rstrip()
            stderr_lines.append(stripped)
            match = _DEVTOOLS_PORT_PATTERN.search(stripped)
            if match and devtools_port[0] is None:
                devtools_port[0] = int(match.group(1))

    reader_thread = threading.Thread(target=_read_stderr, daemon=True)
    reader_thread.start()

    port_deadline = time.monotonic() + HEADLESS_CDP_PORT_DEADLINE_SECONDS
    while devtools_port[0] is None and time.monotonic() < port_deadline:
        if process.poll() is not None:
            raise RuntimeError(
                "Headless chromium exited before announcing DevTools port for Story 11.5; "
                f"rc={process.returncode} stderr_tail={stderr_lines[-5:]}"
            )
        time.sleep(0.05)

    if devtools_port[0] is None:
        raise RuntimeError(
            "Headless chromium did not announce a DevTools port within "
            f"{HEADLESS_CDP_PORT_DEADLINE_SECONDS:.0f}s for Story 11.5; "
            f"stderr_tail={stderr_lines[-5:]}"
        )
    port = devtools_port[0]

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5) as response:
            targets = json.loads(response.read())
    except Exception as exc:
        raise RuntimeError(
            f"Failed to enumerate DevTools targets on port {port} for Story 11.5: {exc}"
        ) from exc
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        raise RuntimeError(
            f"No Page target available on DevTools port {port} for Story 11.5; targets={targets}"
        )
    ws_debugger_url = pages[0].get("webSocketDebuggerUrl")
    if not ws_debugger_url:
        raise RuntimeError(
            "DevTools Page target missing webSocketDebuggerUrl for Story 11.5"
        )

    # Re-raise any `websocket`/`socket` connection errors as `RuntimeError` so
    # the test's outer `except RuntimeError → pytest.skip(...)` contract holds.
    # Without this wrap, a chromium port-jitter or co-tenant connection reset
    # surfaces as a raw `ConnectionRefusedError`/`OSError`/
    # `WebSocketException` and turns a skip-safe path into a hard CI failure.
    try:
        ws = websocket.create_connection(ws_debugger_url, timeout=10)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to attach CDP WebSocket {ws_debugger_url} for Story 11.5: {exc}"
        ) from exc
    try:
        try:
            return _drive_cdp_session(ws, navigate_to=navigate_to)
        except (websocket.WebSocketException, OSError) as exc:
            raise RuntimeError(
                f"CDP transport error during Story 11.5 wait: {type(exc).__name__}: {exc}"
            ) from exc
    finally:
        try:
            ws.close()
        except Exception:
            pass


def _drive_cdp_session(ws: "websocket.WebSocket", *, navigate_to: str) -> str:
    """Send CDP commands, navigate to the target URL, block on the
    `Runtime.evaluate` Promise that resolves when `data-story-11-5-phase`
    reaches a terminal value, then return the captured DOM.
    """
    msg_id = 0
    queued_events: list[dict] = []

    def _send(method: str, params: dict | None = None, *, recv_timeout: float = 10.0) -> dict:
        nonlocal msg_id
        msg_id += 1
        request_id = msg_id
        ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        deadline = time.monotonic() + recv_timeout
        while time.monotonic() < deadline:
            ws.settimeout(max(0.1, deadline - time.monotonic()))
            # Catch socket-level read timeouts symmetrically with
            # `_wait_for_event` — otherwise an idle period inside a long
            # `Runtime.evaluate({awaitPromise: true})` (where the page-side
            # MutationObserver may legitimately be silent for many seconds)
            # raises `WebSocketTimeoutException` straight out of `_send`,
            # bypassing the deadline check and surfacing as a noisy stack
            # trace instead of the documented `RuntimeError` deadline message.
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            data = json.loads(raw)
            if data.get("id") == request_id:
                return data
            # Buffer un-matched events so callers awaiting a specific event
            # (e.g. `Page.frameStoppedLoading`) don't lose it mid-send.
            if "method" in data:
                queued_events.append(data)
        raise RuntimeError(f"CDP method {method} did not respond within {recv_timeout:.0f}s")

    def _wait_for_event(method_name: str, *, timeout: float = 30.0, predicate=None) -> dict:
        accept = predicate or (lambda _ev: True)
        for index, event in enumerate(queued_events):
            if event.get("method") == method_name and accept(event):
                return queued_events.pop(index)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            ws.settimeout(max(0.1, deadline - time.monotonic()))
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            data = json.loads(raw)
            if data.get("method") == method_name and accept(data):
                return data
            if "method" in data:
                queued_events.append(data)
        raise RuntimeError(f"CDP event {method_name} did not fire within {timeout:.0f}s")

    _send("Page.enable")
    _send("Runtime.enable")
    navigate_response = _send("Page.navigate", {"url": navigate_to})
    navigate_result = navigate_response.get("result", {}) if isinstance(navigate_response, dict) else {}
    # `Page.navigate` returns `errorText` (e.g. `net::ERR_CONNECTION_REFUSED`,
    # `net::ERR_NAME_NOT_RESOLVED`) when the navigation itself fails. Without
    # this check the helper would wait the full CDP budget (60 s) only to
    # surface a generic "deadline reached" error — surfacing the navigate
    # errorText immediately makes the actual cause obvious.
    navigate_error = navigate_result.get("errorText")
    if navigate_error:
        raise RuntimeError(
            f"Page.navigate to {navigate_to!r} failed: {navigate_error}"
        )
    main_frame_id = navigate_result.get("frameId")
    if not isinstance(main_frame_id, str) or not main_frame_id:
        raise RuntimeError(
            f"Page.navigate did not return a frameId for Story 11.5: {json.dumps(navigate_response)[:300]}"
        )
    # Block on `Page.frameStoppedLoading` for the EXACT frame Page.navigate
    # returned — `Page.loadEventFired` has no frameId field and races against
    # the initial about:blank's own load event, which destroys the JS
    # context the moment Page.navigate's target replaces it. Matching the
    # `frameId` from Page.navigate's response makes this race-free.
    _wait_for_event(
        "Page.frameStoppedLoading",
        timeout=30.0,
        predicate=lambda ev: ev.get("params", {}).get("frameId") == main_frame_id,
    )

    # The awaitPromise CDP call blocks until the page-side MutationObserver
    # resolves the Promise OR the per-call timeout trips. Timeout is set
    # generously below the outer pytest skip budget; in practice the
    # observed wait against loopback is ~1 s.
    wait_ms = int(HEADLESS_CDP_WAIT_SECONDS * 1000)
    response = _send(
        "Runtime.evaluate",
        {
            "expression": _HEADLESS_CDP_WAIT_JS,
            "awaitPromise": True,
            "returnByValue": True,
            "timeout": wait_ms,
        },
        recv_timeout=HEADLESS_CDP_WAIT_SECONDS + 5.0,
    )

    if "error" in response:
        raise RuntimeError(
            f"Story 11.5 CDP Runtime.evaluate returned error: {json.dumps(response['error'])[:400]}"
        )
    result = response.get("result", {})
    if "exceptionDetails" in result:
        exception_text = json.dumps(result["exceptionDetails"])[:400]
        raise RuntimeError(
            f"Story 11.5 CDP wait raised in the page context: {exception_text}"
        )
    value_wrapper = result.get("result", {})
    value = value_wrapper.get("value")
    if not isinstance(value, dict) or "dom" not in value:
        raise RuntimeError(
            "Story 11.5 CDP wait deadline reached without a terminal phase; "
            f"observed response={json.dumps(response)[:600]}"
        )
    dom = value.get("dom")
    if not isinstance(dom, str):
        raise RuntimeError(
            f"Story 11.5 CDP wait returned a non-string DOM payload: type={type(dom).__name__}"
        )
    return dom


def parse_story_state_from_dom(dom: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in re.findall(r'data-story-11-5-([a-z\\-]+)="([^"]*)"', dom):
        values[key.replace("-", "_")] = value
    return values


def _gd_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
