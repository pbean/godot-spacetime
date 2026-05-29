"""
Story 11.5: GDScript web-export integration coverage.

Stages a temporary pure-GDScript project, exports it to Web/HTML5, serves the
result over local HTTP, and validates the browser-visible lifecycle state when
all local prerequisites are available.
"""

from __future__ import annotations

import importlib.util
import subprocess
import uuid
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import (
    SpacetimeIdentityShapeError,
    mint_anonymous_identity,
    probe_browser_binary,
    probe_godot_non_mono_binary,
    probe_local_runtime,
    probe_loopback_http,
    probe_spacetime_cli,
)

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "tests" / "fixtures" / "gdscript_web_export.py"
RUNNER_PATH = ROOT / "tests" / "godot_integration" / "gdscript_web_export_runner.gd"
SCENE_PATH = ROOT / "tests" / "godot_integration" / "gdscript_web_export_runner.tscn"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "gdscript_generated" / "smoke_test"
EVENT_PREFIX = "STORY_11_5_WEB_EXPORT"


def _load_helper_module():
    spec = importlib.util.spec_from_file_location("tests.fixtures.gdscript_web_export", HELPER_PATH)
    assert spec is not None and spec.loader is not None, (
        "Story 11.5 web-export integration requires tests/fixtures/gdscript_web_export.py."
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _publish_module(cli: str, server: str, module_name: str) -> None:
    subprocess.run(
        [
            cli,
            "publish",
            "--server",
            server,
            "--anonymous",
            "--module-path",
            str(ROOT / "spacetime" / "modules" / "smoke_test"),
            "--yes",
            module_name,
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        timeout=180,
    )


def test_story_11_5_web_export_harness_files_exist() -> None:
    required = [HELPER_PATH, RUNNER_PATH, SCENE_PATH, FIXTURE_DIR / "spacetimedb_client.gd"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    assert not missing, (
        "Story 11.5 browser/export coverage requires dedicated staging and runner assets. "
        f"Missing {missing}"
    )


def test_story_11_5_web_export_runner_contract_strings_present() -> None:
    content = RUNNER_PATH.read_text(encoding="utf-8")
    for expected in (
        "JavaScriptBridge",
        "transport_request_ready",
        "query_token_mode_confirmed",
        "connected",
        "done",
        "spacetimedb_client.gd",
        "data-story-11-5-phase",
        "data-story-11-5-transport-mode",
    ):
        assert expected in content, (
            "gdscript_web_export_runner.gd must surface browser-visible lifecycle milestones for Story 11.5. "
            f"Missing {expected!r}."
        )


def test_story_11_5_web_export_helper_reuses_shared_prerequisite_probes() -> None:
    content = HELPER_PATH.read_text(encoding="utf-8")
    for expected in (
        "probe_godot_non_mono_binary",
        "probe_browser_binary",
        "probe_loopback_http",
        "Compatibility",
        "export_presets.cfg",
        "index.html",
        # The empirically validated ANGLE swiftshader headless flag set —
        # `--disable-gpu` and `--virtual-time-budget` must NOT come back; they
        # leave the runtime at a blank-splash DOM with no WebGL2.
        "HEADLESS_BROWSER_FLAGS",
        "--use-angle=swiftshader",
        # The CDP wait is the only deterministic primitive that blocks until
        # the runner reaches a terminal `data-story-11-5-phase`.
        "MutationObserver",
        "Runtime.evaluate",
        "remote-debugging-port",
    ):
        assert expected in content, (
            "tests/fixtures/gdscript_web_export.py must stage the dedicated web-export fixture and reuse shared prerequisite probes. "
            f"Missing {expected!r}."
        )


def test_story_11_5_web_export_integration_reuses_shared_runtime_probes() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    for expected in (
        "probe_spacetime_cli",
        "probe_local_runtime",
        "probe_godot_non_mono_binary",
        "probe_browser_binary",
        "probe_loopback_http",
        # The placeholder `query_token="story-11-5-browser-token"` previously
        # baked into staging gets HTTP 401'd by SpacetimeDB 2.1.0 mid-
        # handshake. The token must be minted from the live runtime at test
        # time so the WebSocket upgrade actually succeeds.
        "mint_anonymous_identity",
        # The shape-drift exception subclass must not be silently caught by
        # the test's RuntimeError handler — pinning ensures a regression that
        # drops the subclass import or the explicit re-raise gets caught.
        "SpacetimeIdentityShapeError",
    ):
        assert expected in content, (
            "Story 11.5 web-export integration coverage must stay skip-safe and use shared prerequisite probes. "
            f"Missing {expected!r}."
        )


def test_story_11_5_gdscript_web_export_e2e(tmp_path: Path) -> None:
    if not HELPER_PATH.exists():
        pytest.skip("Story 11.5 web-export helper is not implemented yet")

    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    godot_probe = probe_godot_non_mono_binary()
    if not godot_probe.available:
        pytest.skip(f"non-Mono Godot binary not available for Web export: {godot_probe.reason}")

    browser_probe = probe_browser_binary()
    if not browser_probe.available:
        pytest.skip(f"browser binary not available on PATH: {browser_probe.reason}")

    loopback_probe = probe_loopback_http()
    if not loopback_probe.available:
        pytest.skip(f"loopback HTTP unavailable: {loopback_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(f"SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    module_name = f"gdscript-web-export-{uuid.uuid4().hex[:12]}"
    try:
        _publish_module(cli_probe.path, runtime_probe.server, module_name)
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(exc.stderr or b'').decode('utf-8', 'replace')[:240]}"
        )
    except subprocess.TimeoutExpired:
        pytest.skip("SpacetimeDB runtime unavailable: smoke_test publish timed out after 180s")

    # SpacetimeDB 2.1.0 rejects unsigned/placeholder query tokens during the
    # WebSocket upgrade handshake with `HTTP Authentication failed; no valid
    # credentials available`. Mint a real ES256-signed JWT from the live local
    # runtime at test time — the previous fixture string `story-11-5-browser-
    # token` cannot be valid across `spacetime start` resets.
    #
    # Catch plain `RuntimeError` only — `SpacetimeIdentityShapeError` (a
    # subclass) intentionally bypasses this skip path so server contract
    # drift from pinned 2.1.0 fails loud, per the spec's Code Map directive
    # ("shape drift still fails loud") and the Empirical SDK Validation
    # principle (a future server major changing the response shape is a
    # documentation defect to surface, not a transient skip).
    try:
        minted = mint_anonymous_identity(runtime_probe.host)
    except SpacetimeIdentityShapeError:
        raise
    except RuntimeError as exc:
        pytest.skip(
            "SpacetimeDB runtime cannot mint an anonymous identity token for "
            f"the Story 11.5 web-export proof path: {exc}"
        )
    query_token = minted.token

    helper = _load_helper_module()
    project_dir = tmp_path / "web_project"
    export_dir = tmp_path / "web_export"

    helper.stage_web_export_project(
        repo_root=ROOT,
        project_dir=project_dir,
        bindings_dir=FIXTURE_DIR,
        host=runtime_probe.host,
        module_name=module_name,
        query_token=query_token,
    )

    project_godot = (project_dir / "project.godot").read_text(encoding="utf-8")
    export_presets = (project_dir / "export_presets.cfg").read_text(encoding="utf-8")
    assert '"C#"' not in project_godot, "Story 11.5 web-export fixture must not stage a C# project."
    assert "Compatibility" in project_godot, "Story 11.5 web-export fixture must use the Compatibility renderer."
    assert "thread" in export_presets.lower(), "Story 11.5 web-export preset must explicitly disable thread support."

    try:
        index_path = helper.export_web_project(godot_probe.path, project_dir, export_dir)
    except RuntimeError as exc:
        pytest.skip(str(exc))

    with helper.serve_directory(export_dir) as base_url:
        try:
            dom = helper.run_headless_browser_capture(
                browser_probe.path,
                f"{base_url}/{index_path.name}",
            )
        except RuntimeError as exc:
            pytest.skip(str(exc))

    state = helper.parse_story_state_from_dom(dom)
    assert state.get("phase") == "done", f"browser export did not reach terminal success state: {state}"
    assert state.get("connected") == "true", f"browser export did not report a live connection: {state}"
    assert state.get("transport_mode") == "query-token", (
        "browser export must prove the web auth seam uses query-token transport when credentials are supplied. "
        f"Observed state: {state}"
    )
    assert state.get("project_has_csharp") == "false", (
        "browser proof path must stage a dedicated pure-GDScript project, not the repo root C# project. "
        f"Observed state: {state}"
    )
    assert state.get("renderer") == "Compatibility", (
        "browser proof path must record the Compatibility renderer in machine-readable state. "
        f"Observed state: {state}"
    )
    # G10 identity-equality: the server is proven to authenticate `?token=` as the token's
    # identity; this asserts the GDScript web client actually connects AS that identity over the
    # web transport (not anonymously). The GDScript parser (connection_protocol.fixed_width_bytes_to_hex)
    # reverses the little-endian wire identity bytes into the server's canonical byte order and
    # uppercases them, so both strings carry the SAME byte order and differ only in case — hence
    # `.lower()` is the correct, order-safe comparison (verified against the pinned wire fixture).
    assert state.get("identity", "").lower() == minted.identity.lower(), (
        "browser export over the ?token= transport must authenticate as the minted token's "
        "identity — the InitialConnection identity must equal the server-reported identity for "
        f"that token. minted identity={minted.identity!r}, observed identity={state.get('identity')!r}. "
        f"Full state: {state}"
    )
