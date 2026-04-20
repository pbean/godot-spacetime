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

import os
import re
import shutil
import socket
import subprocess
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
    except FileNotFoundError:
        return ProbeResult(
            available=False, reason=f"spacetime CLI at {path} disappeared before exec"
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            available=False, reason="spacetime --version timed out after 10s"
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
    except FileNotFoundError:
        return ProbeResult(
            available=False,
            reason=f"Godot binary at {resolved} disappeared before exec",
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            available=False, reason="godot --version timed out after 15s"
        )
    if result.returncode != 0:
        return ProbeResult(
            available=False,
            reason=f"{resolved} --version exited with {result.returncode}",
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
    except FileNotFoundError:
        return ProbeResult(
            available=False,
            reason=f"browser binary at {resolved} disappeared before exec",
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            available=False,
            reason="browser --version timed out after 15s",
        )
    if result.returncode != 0:
        return ProbeResult(
            available=False,
            reason=f"{resolved} --version exited with {result.returncode}",
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
        or ".net" in lowered_output
        or "dotnet" in lowered_output
    )


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
