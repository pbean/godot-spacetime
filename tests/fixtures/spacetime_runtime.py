"""
Runtime availability probes for Story 7.1 dynamic lifecycle integration test.

This helper is DISCOVERY-ONLY. It does not install, start, or stop anything.
Running a local SpacetimeDB instance and installing godot-mono are the
developer's responsibility; this module only answers "is it reachable right
now?" so the dynamic lifecycle test can distinguish skip-on-missing-prereq
from fail-on-assertion.

The probes are deliberately side-effect-free so the probe unit tests can run
green on any developer machine, with or without a real runtime present.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass

# Matches the CSI/SGR ANSI escape sequences `spacetime server ping` may emit
# when its stdout is attached to a TTY. Strips colors and cursor-control codes
# so the host parser sees the raw `Server is online: <host>` line regardless
# of whether a developer wrapper has tricked the CLI into colorized output.
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

DEFAULT_SPACETIME_SERVER = "local"
# Binary name preference order. godot-mono is the test's required harness.
# Plain `godot` is only accepted when its version output identifies a Mono/.NET
# build, so a non-C# Godot binary still yields a clean skip instead of a later
# harness load failure.
GODOT_BINARY_CANDIDATES = ("godot-mono", "godot4-mono", "godot", "godot4")
# Non-Mono Godot binary candidates used exclusively by the Story 11.5 web-export
# proof path. Godot 4 refuses Web export from the C#/.NET editor build even when
# the staged project itself is pure GDScript, so the web-export lane has to dial
# a non-Mono binary; the regular `GODOT_BINARY_CANDIDATES` would silently dead-
# end at the export step. Empirically observed against Godot 4.6.3 mono:
# "Exporting to Web is currently not supported in Godot 4 when using C#/.NET."
NON_MONO_GODOT_BINARY_CANDIDATES = ("godot", "godot4")
BROWSER_BINARY_CANDIDATES = (
    "chromium",
    "chromium-browser",
    "google-chrome",
    "google-chrome-stable",
    "chrome",
    "microsoft-edge",
    "microsoft-edge-stable",
)


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of a discovery probe.

    `available=True` means the probed surface can be used by the caller right
    now. `path` carries the resolved executable path when applicable; `host`
    carries the reachable SpacetimeDB host URL for the runtime probe; `server`
    carries the spacetime CLI's server nickname so callers can pass it through
    to `spacetime publish --server <nickname>`. `reason` is populated only
    when `available=False` and always names the specific missing prerequisite
    so the test skip message is unambiguous.
    """

    available: bool
    path: str = ""
    host: str = ""
    server: str = ""
    reason: str = ""


def probe_spacetime_cli() -> ProbeResult:
    """Return whether the `spacetime` CLI is discoverable and runnable.

    Uses the PATH-resolved executable and asks it for its version. Does not
    probe a live server — that is `probe_local_runtime`'s job.
    """
    path = shutil.which("spacetime")
    if path is None:
        return ProbeResult(available=False, reason="spacetime not found on PATH")
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            available=False, reason="spacetime --version timed out after 10s"
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return ProbeResult(
            available=False, reason=f"spacetime CLI at {path} unrunnable: {exc}"
        )
    if result.returncode != 0:
        return ProbeResult(
            available=False,
            reason=f"spacetime --version exited with {result.returncode}: "
            f"{(result.stderr or '').strip()[:200]}",
        )
    return ProbeResult(available=True, path=path)


def probe_godot_binary() -> ProbeResult:
    """Return whether a Godot (mono) binary is discoverable and runnable.

    Accepts any of `GODOT_BINARY_CANDIDATES`. The `GODOT4` or `GODOT_BIN`
    environment variable, if set, takes precedence. Runs the resolved binary
    with `--version --headless` to confirm it is not a broken symlink and to
    reject non-Mono builds that cannot host the C# integration harness.
    """
    override = os.environ.get("GODOT4") or os.environ.get("GODOT_BIN")
    candidates: tuple[str, ...]
    if override:
        candidates = (override,)
    else:
        candidates = GODOT_BINARY_CANDIDATES

    resolved: str | None = None
    for candidate in candidates:
        found = shutil.which(candidate) if os.path.basename(candidate) == candidate else (
            candidate if os.path.isfile(candidate) and os.access(candidate, os.X_OK) else None
        )
        if found:
            resolved = found
            break

    if resolved is None:
        return ProbeResult(
            available=False,
            reason=f"no Godot binary found on PATH (tried {', '.join(candidates)})",
        )

    try:
        result = subprocess.run(
            [resolved, "--headless", "--version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            available=False, reason="godot --version timed out after 15s"
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return ProbeResult(
            available=False,
            reason=f"Godot binary at {resolved} unrunnable: {exc}",
        )
    if result.returncode != 0:
        return ProbeResult(
            available=False,
            reason=f"{resolved} --version exited with {result.returncode}: "
            f"{(result.stderr or '').strip()[:200]}",
        )
    if not _looks_like_mono_godot_build(resolved, result.stdout or ""):
        return ProbeResult(
            available=False,
            reason=(
                f"{resolved} does not appear to be a Godot Mono/.NET build "
                "required by the C# integration harness"
            ),
        )
    return ProbeResult(available=True, path=resolved)


def probe_godot_non_mono_binary() -> ProbeResult:
    """Return whether a non-Mono Godot binary is discoverable and runnable.

    Story 11.5's web-export proof path requires a non-Mono Godot 4.x binary
    because Godot 4 explicitly refuses Web export from the C#/.NET editor
    build, even when the staged project itself is pure GDScript. The
    optional `GODOT_WEB_EXPORT_BIN` environment variable takes precedence
    over the PATH-discovered `NON_MONO_GODOT_BINARY_CANDIDATES`; an unset or
    empty `GODOT_WEB_EXPORT_BIN` falls back to PATH discovery (empty string
    is treated as unset so a leftover `export GODOT_WEB_EXPORT_BIN=` in a
    shell rc behaves the same as never having set the var). Mono builds are
    rejected so the web-export lane skips with an explicit reason rather
    than wedging at the rc=0/no-`index.html` failure mode that Godot's mono
    build exhibits when asked to Web-export. Mono detection looks at both
    `--version` stdout and stderr because some packaged Godot variants emit
    the version banner to stderr only.
    """
    override = os.environ.get("GODOT_WEB_EXPORT_BIN")
    candidates: tuple[str, ...]
    using_override = bool(override and override.strip())
    if using_override:
        candidates = (override,)
    else:
        candidates = NON_MONO_GODOT_BINARY_CANDIDATES

    resolved: str | None = None
    for candidate in candidates:
        found = shutil.which(candidate) if os.path.basename(candidate) == candidate else (
            candidate if os.path.isfile(candidate) and os.access(candidate, os.X_OK) else None
        )
        if found:
            resolved = found
            break

    if resolved is None:
        if using_override:
            reason = (
                f"GODOT_WEB_EXPORT_BIN={override!r} did not resolve to a runnable "
                "non-Mono Godot binary; point it at an absolute path to a non-Mono Godot 4.x build"
            )
        else:
            reason = (
                f"no non-Mono Godot binary found on PATH (tried {', '.join(candidates)}); "
                "set GODOT_WEB_EXPORT_BIN=/path/to/godot to point at a non-Mono Godot 4.x binary"
            )
        return ProbeResult(available=False, reason=reason)

    try:
        result = subprocess.run(
            [resolved, "--headless", "--version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            available=False, reason="godot --version timed out after 15s"
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return ProbeResult(
            available=False,
            reason=f"Godot binary at {resolved} unrunnable: {exc}",
        )
    if result.returncode != 0:
        return ProbeResult(
            available=False,
            reason=f"{resolved} --version exited with {result.returncode}: "
            f"{(result.stderr or '').strip()[:200]}",
        )
    # Some packaged Godot variants print the version banner to stderr only;
    # concatenate both so a Mono build cannot hide its `.mono.` marker by
    # writing to the unchecked stream.
    version_text = (result.stdout or "") + "\n" + (result.stderr or "")
    if not _looks_like_non_mono_godot_build(resolved, version_text):
        return ProbeResult(
            available=False,
            reason=(
                f"{resolved} appears to be a Mono/.NET Godot build; "
                "Web export requires a non-Mono binary"
            ),
        )
    return ProbeResult(available=True, path=resolved)


def probe_browser_binary() -> ProbeResult:
    """Return whether a Chromium-family browser is discoverable and runnable.

    The optional `BROWSER_BIN` environment variable takes precedence. The
    browser is validated via `--version` because Story 11.5's browser/export
    lane must skip cleanly instead of assuming a GUI browser is installed.
    """
    override = os.environ.get("BROWSER_BIN")
    candidates: tuple[str, ...]
    if override:
        candidates = (override,)
    else:
        candidates = BROWSER_BINARY_CANDIDATES

    resolved: str | None = None
    for candidate in candidates:
        found = shutil.which(candidate) if os.path.basename(candidate) == candidate else (
            candidate if os.path.isfile(candidate) and os.access(candidate, os.X_OK) else None
        )
        if found:
            resolved = found
            break

    if resolved is None:
        return ProbeResult(
            available=False,
            reason=f"no Chromium-family browser found on PATH (tried {', '.join(candidates)})",
        )

    try:
        result = subprocess.run(
            [resolved, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            available=False,
            reason="browser --version timed out after 15s",
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return ProbeResult(
            available=False,
            reason=f"browser binary at {resolved} unrunnable: {exc}",
        )
    if result.returncode != 0:
        return ProbeResult(
            available=False,
            reason=f"{resolved} --version exited with {result.returncode}: "
            f"{(result.stderr or '').strip()[:200]}",
        )
    return ProbeResult(available=True, path=resolved)


def probe_loopback_http() -> ProbeResult:
    """Return whether the current environment can bind a local HTTP server.

    Story 11.5's browser lane must serve exported files over HTTP rather than
    `file://`. This probe stays discovery-only: it binds an ephemeral socket,
    captures the assigned port, and then closes immediately without serving.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except OSError as exc:
        return ProbeResult(
            available=False,
            reason=f"loopback HTTP socket creation failed: {exc}",
        )

    try:
        sock.bind(("127.0.0.1", 0))
        host, port = sock.getsockname()
    except OSError as exc:
        return ProbeResult(
            available=False,
            reason=f"loopback HTTP bind failed on 127.0.0.1: {exc}",
        )
    finally:
        sock.close()

    return ProbeResult(
        available=True,
        host=f"http://{host}:{port}",
    )


def probe_local_runtime(spacetime_cli_path: str) -> ProbeResult:
    """Return whether a SpacetimeDB server is reachable via the spacetime CLI.

    The target server nickname comes from the `SPACETIME_SERVER` env var and
    defaults to `local` — the standard nickname that the CLI creates for
    127.0.0.1:3000 on first install. Callers running against a dev or CI
    server can override by setting `SPACETIME_SERVER=<nickname>`.

    Probes in two passes:
    1. `spacetime server list` — confirms the CLI has configured servers.
       Without this even a running daemon is unreachable to the CLI.
    2. `spacetime server ping <nickname>` — confirms the chosen server is
       responding right now. A running-but-unreachable daemon skips rather
       than fails, so flaky local setups don't turn into spurious test failures.

    On success, the ping response line `Server is online: <host>` is parsed
    so callers know the canonical host URL to pass through to the Godot
    runner via `SPACETIME_E2E_HOST`.
    """
    server = os.environ.get("SPACETIME_SERVER", DEFAULT_SPACETIME_SERVER)

    try:
        list_result = subprocess.run(
            [spacetime_cli_path, "server", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            available=False, reason="spacetime server list timed out after 10s"
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return ProbeResult(
            available=False,
            reason=f"spacetime CLI at {spacetime_cli_path} unrunnable: {exc}",
        )
    if list_result.returncode != 0:
        return ProbeResult(
            available=False,
            reason=f"spacetime server list exited {list_result.returncode}: "
            f"{(list_result.stderr or '').strip()[:200]}",
        )
    if not _server_nickname_configured(list_result.stdout or "", server):
        return ProbeResult(
            available=False,
            reason=f"spacetime CLI has no server nicknamed {server!r} configured",
        )

    try:
        ping_result = subprocess.run(
            [spacetime_cli_path, "server", "ping", server],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            available=False,
            reason=f"spacetime server ping {server} timed out after 10s",
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return ProbeResult(
            available=False,
            reason=f"spacetime CLI at {spacetime_cli_path} unrunnable: {exc}",
        )
    if ping_result.returncode != 0:
        return ProbeResult(
            available=False,
            reason=f"spacetime server ping {server} exited "
            f"{ping_result.returncode} — server {server!r} not reachable",
        )

    host = _parse_ping_host(ping_result.stdout or "")
    if not host:
        return ProbeResult(
            available=False,
            reason=f"spacetime server ping {server} did not report a host URL "
            f"in stdout: {(ping_result.stdout or '').strip()[:200]}",
        )

    return ProbeResult(
        available=True,
        path=spacetime_cli_path,
        host=host,
        server=server,
    )


class SpacetimeIdentityShapeError(RuntimeError):
    """Raised when `POST /v1/identity` returns a body that doesn't match the
    pinned SpacetimeDB 2.1.0 contract — missing/empty `token`, non-JSON body,
    JSON list/null root, or a JWT shape that wouldn't be accepted by the
    server's WebSocket upgrade.

    Callers that translate `RuntimeError` into `pytest.skip(...)` must NOT
    swallow this subclass — shape drift is a "loud failure" signal under the
    Empirical SDK Validation principle (a future server major changing the
    response shape is a documentation defect to surface, not a transient
    skip).
    """


def mint_anonymous_identity_token(runtime_host: str, *, timeout: float = 10.0) -> str:
    """Mint a fresh anonymous SpacetimeDB JWT from a live local runtime.

    POSTs to `<runtime_host>/v1/identity` and returns the `token` field. Story
    11.5's web-export proof path passes this JWT as the `?token=` query
    parameter on the WebSocket subscribe URL — placeholder strings get
    rejected by SpacetimeDB 2.1.0 mid-handshake with `HTTP Authentication
    failed; no valid credentials available` so the token must be a real
    ES256-signed JWT the running server can verify.

    Observed shape against the pinned spacetime 2.1.0 local runtime:
        {"identity": "<64-hex-bytes>", "token": "<jwt, len≈386, starts with eyJ>"}

    Raises:
      - `RuntimeError` (plain) on a transient runtime/HTTP failure
        (unreachable host, non-2xx status, connection error) — callers should
        translate this into `pytest.skip(...)`.
      - `SpacetimeIdentityShapeError` on response shape drift (non-JSON body,
        list/null root, missing `token` key, empty/whitespace `token`, or a
        value that fails the JWT shape canary `eyJ`-prefix + two dots).
        Callers must let this surface — it indicates a server contract drift
        from pinned 2.1.0, which should fail loud rather than skip.
    """
    normalized_host = (runtime_host or "").rstrip("/")
    if not normalized_host:
        raise RuntimeError("mint_anonymous_identity_token requires a non-empty runtime host URL")
    url = f"{normalized_host}/v1/identity"
    request = urllib.request.Request(url, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.getcode()
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"POST {url} returned HTTP {exc.code} {exc.reason}; "
            "local SpacetimeDB runtime cannot mint an anonymous identity token"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"POST {url} failed: {exc.reason}; "
            "local SpacetimeDB runtime is not reachable for token minting"
        ) from exc

    if status < 200 or status >= 300:
        raise RuntimeError(
            f"POST {url} returned non-2xx status {status}; "
            "local SpacetimeDB runtime cannot mint an anonymous identity token"
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SpacetimeIdentityShapeError(
            f"POST {url} returned non-JSON body: {body[:120]!r}"
        ) from exc

    if not isinstance(payload, dict) or "token" not in payload:
        observed_keys = sorted(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
        raise SpacetimeIdentityShapeError(
            f"POST {url} response shape drifted from the pinned spacetime 2.1.0 contract: "
            f"expected a JSON object with key 'token', observed {observed_keys}"
        )

    token = payload.get("token")
    if not isinstance(token, str) or not token.strip():
        raise SpacetimeIdentityShapeError(
            f"POST {url} returned an empty or non-string 'token' field"
        )
    # JWT shape canary: pinned spacetime 2.1.0 emits an ES256-signed JWT that
    # always starts with `eyJ` (base64-encoded `{"alg":...}` header) and has
    # exactly two `.` separators (header.payload.signature). Anything else
    # would be rejected by the server's WebSocket upgrade as malformed; better
    # to surface the drift here than to debug an HTTP 401 mid-handshake.
    if not token.startswith("eyJ") or token.count(".") != 2:
        raise SpacetimeIdentityShapeError(
            f"POST {url} returned a value in 'token' that does not match the pinned spacetime "
            f"2.1.0 JWT shape (eyJ-prefix + two dots); observed prefix={token[:8]!r}, "
            f"dot_count={token.count('.')}"
        )
    return token


def _parse_ping_host(stdout: str) -> str:
    """Extract `Server is online: <host>` from `spacetime server ping` output.

    Strips ANSI escape sequences before scanning so a TTY-aware wrapper around
    the test harness cannot produce a host like `\x1b[32mhttp://...\x1b[0m`
    that the dynamic lifecycle test then refuses to dial.
    """
    marker = "Server is online:"
    for line in stdout.splitlines():
        stripped = _ANSI_ESCAPE.sub("", line).strip()
        idx = stripped.find(marker)
        if idx != -1:
            return stripped[idx + len(marker):].strip()
    return ""


def _looks_like_mono_godot_build(path: str, version_output: str) -> bool:
    """Return whether the resolved Godot binary appears to support C#/.NET."""
    lowered_path = os.path.basename(path).lower()
    lowered_output = version_output.lower()
    return (
        "mono" in lowered_path
        or "mono" in lowered_output
        or re.search(r"\.mono\b", lowered_output) is not None
        or re.search(r"\.net\b", lowered_output) is not None
    )


def _looks_like_non_mono_godot_build(path: str, version_output: str) -> bool:
    """Negation of `_looks_like_mono_godot_build`.

    A binary qualifies as non-Mono only when the Mono detector fails to flag
    it on the same surface (basename + combined `--version` stdout/stderr).
    The gate is therefore only as strong as `_looks_like_mono_godot_build`'s
    recall on the pinned Godot line. For the pinned Godot 4.6.x runtime, real
    Mono builds always emit `.mono.` in their `--version` string (e.g.
    `Godot Engine v4.6.3.stable.mono.arch_linux.<sha>`), so the negation
    holds in practice — but a hypothetical Mono build with a stripped/custom
    version banner and a non-`mono` basename would slip through. Callers
    should not infer stronger guarantees than that.
    """
    return not _looks_like_mono_godot_build(path, version_output)


def _server_nickname_configured(list_stdout: str, nickname: str) -> bool:
    """Return True when `spacetime server list` has an exact nickname entry.

    Matches the nickname as a whole token in any column of any output line so a
    configured server called `local-staging` does not shadow a lookup for
    `local`, and vice versa. Ignores the header line by requiring the token to
    not be a PATH-style heading (case-sensitive match is fine — nicknames are
    lowercased by the spacetime CLI).
    """
    for line in list_stdout.splitlines():
        tokens = line.split()
        if nickname in tokens:
            return True
    return False
