"""
Unit tests for tests/fixtures/spacetime_runtime.py.

The probe helper is discovery-only, so these tests must pass green on ANY
developer machine — with or without a real SpacetimeDB runtime present, with
or without godot-mono installed. They drive both branches by manipulating PATH
and by stubbing `subprocess.run`.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.fixtures import spacetime_runtime
from tests.fixtures.spacetime_runtime import (
    ProbeResult,
    probe_browser_binary,
    probe_godot_binary,
    probe_godot_non_mono_binary,
    probe_local_runtime,
    probe_spacetime_cli,
)


class _FakeCompletedProcess:
    def __init__(
        self,
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture
def isolated_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Give the probes an empty PATH with just `tmp_path` so real binaries vanish."""
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.delenv("GODOT4", raising=False)
    monkeypatch.delenv("GODOT_BIN", raising=False)
    monkeypatch.delenv("SPACETIME_HOST", raising=False)
    return tmp_path


def _make_stub_binary(directory: Path, name: str) -> str:
    """Create an executable file on disk so shutil.which can find it."""
    binary = directory / name
    binary.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    return str(binary)


# ---------------------------------------------------------------------------
# probe_spacetime_cli
# ---------------------------------------------------------------------------


def test_probe_spacetime_cli_missing_from_path(isolated_path: Path) -> None:
    result = probe_spacetime_cli()
    assert not result.available
    assert "not found" in result.reason.lower()
    assert result.path == ""


def test_probe_spacetime_cli_present_but_broken(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_stub_binary(isolated_path, "spacetime")

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(returncode=1, stderr="segfault")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_spacetime_cli()
    assert not result.available
    assert "exited with 1" in result.reason
    assert "segfault" in result.reason


def test_probe_spacetime_cli_present_and_running(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _make_stub_binary(isolated_path, "spacetime")

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(returncode=0, stdout="spacetime 2.1.0")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_spacetime_cli()
    assert result.available
    assert result.path == path
    assert result.reason == ""


def test_probe_spacetime_cli_timeout_is_not_a_hard_fail(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_stub_binary(isolated_path, "spacetime")

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired(cmd="spacetime", timeout=10)

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_spacetime_cli()
    assert not result.available
    assert "timed out" in result.reason


# ---------------------------------------------------------------------------
# probe_godot_binary
# ---------------------------------------------------------------------------


def test_probe_godot_binary_missing(isolated_path: Path) -> None:
    result = probe_godot_binary()
    assert not result.available
    assert "no godot binary" in result.reason.lower()


def test_probe_godot_binary_respects_godot4_env(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    override = _make_stub_binary(tmp_path, "my-custom-godot")
    monkeypatch.setenv("GODOT4", override)

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(returncode=0, stdout="4.6.2.stable.mono.custom")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_godot_binary()
    assert result.available
    assert result.path == override


def test_probe_godot_binary_finds_godot_mono_on_path(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _make_stub_binary(isolated_path, "godot-mono")

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(returncode=0, stdout="Godot Engine v4.6.2")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_godot_binary()
    assert result.available
    assert result.path == path


def test_probe_godot_binary_rejects_non_mono_godot_on_path(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_stub_binary(isolated_path, "godot")

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(returncode=0, stdout="4.6.2.stable.arch_linux")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_godot_binary()
    assert not result.available
    assert "mono" in result.reason.lower() or ".net" in result.reason.lower()


def test_probe_godot_binary_reports_exec_failure(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_stub_binary(isolated_path, "godot-mono")

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(returncode=127)

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_godot_binary()
    assert not result.available
    assert "exited with 127" in result.reason


# ---------------------------------------------------------------------------
# probe_local_runtime
# ---------------------------------------------------------------------------


def test_probe_local_runtime_list_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"n": 0}

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        call_count["n"] += 1
        return _FakeCompletedProcess(returncode=2, stderr="no config found")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_local_runtime("/fake/spacetime")
    assert not result.available
    assert "exited 2" in result.reason
    assert "no config found" in result.reason
    assert call_count["n"] == 1  # short-circuits before ping


def test_probe_local_runtime_requested_server_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(
            returncode=0, stdout=" DEFAULT  HOSTNAME  PROTOCOL  NICKNAME\n"
        )

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    monkeypatch.setenv("SPACETIME_SERVER", "nonesuch")
    result = probe_local_runtime("/fake/spacetime")
    assert not result.available
    assert "no server nicknamed 'nonesuch'" in result.reason


def test_probe_local_runtime_nickname_substring_does_not_false_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A configured `local-staging` must not satisfy a probe for `local`.

    Regression guard for the earlier substring-match bug surfaced by review.
    """
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeCompletedProcess:
        if "list" in cmd:
            return _FakeCompletedProcess(
                returncode=0,
                stdout=(
                    " DEFAULT  HOSTNAME         PROTOCOL  NICKNAME\n"
                    "          10.0.0.5:3000   http      local-staging\n"
                ),
            )
        return _FakeCompletedProcess(returncode=0, stdout="Server is online: http://10.0.0.5:3000")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    monkeypatch.setenv("SPACETIME_SERVER", "local")
    result = probe_local_runtime("/fake/spacetime")
    assert not result.available
    assert "no server nicknamed 'local'" in result.reason


def test_probe_local_runtime_ping_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeCompletedProcess:
        calls.append(cmd)
        if "list" in cmd:
            return _FakeCompletedProcess(
                returncode=0, stdout="NICKNAME\nlocal (default)\n"
            )
        return _FakeCompletedProcess(returncode=1, stderr="connection refused")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_local_runtime("/fake/spacetime")
    assert not result.available
    assert "not reachable" in result.reason
    assert len(calls) == 2  # list then ping


def test_probe_local_runtime_ping_stdout_missing_host_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeCompletedProcess:
        if "list" in cmd:
            return _FakeCompletedProcess(returncode=0, stdout="NICKNAME\nlocal\n")
        return _FakeCompletedProcess(returncode=0, stdout="pong")  # no host line

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_local_runtime("/fake/spacetime")
    assert not result.available
    assert "did not report a host URL" in result.reason


def test_probe_local_runtime_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeCompletedProcess:
        if "list" in cmd:
            return _FakeCompletedProcess(
                returncode=0, stdout="NICKNAME\nlocal (default)\n"
            )
        return _FakeCompletedProcess(
            returncode=0,
            stdout="WARNING: This command is UNSTABLE\n"
            "Server is online: http://127.0.0.1:3000\n",
        )

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    monkeypatch.delenv("SPACETIME_SERVER", raising=False)
    result = probe_local_runtime("/fake/spacetime")
    assert result.available
    assert result.host == "http://127.0.0.1:3000"
    assert result.server == "local"
    assert result.path == "/fake/spacetime"


def test_probe_local_runtime_custom_server_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeCompletedProcess:
        if "list" in cmd:
            return _FakeCompletedProcess(returncode=0, stdout="my-dev-server\n")
        assert cmd[-1] == "my-dev-server"
        return _FakeCompletedProcess(
            returncode=0, stdout="Server is online: http://10.0.0.5:3000\n"
        )

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    monkeypatch.setenv("SPACETIME_SERVER", "my-dev-server")
    result = probe_local_runtime("/fake/spacetime")
    assert result.available
    assert result.server == "my-dev-server"
    assert result.host == "http://10.0.0.5:3000"


def test_probe_local_runtime_timeout_is_skip_not_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired(cmd="spacetime server list", timeout=10)

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_local_runtime("/fake/spacetime")
    assert not result.available
    assert "timed out" in result.reason


def test_probe_local_runtime_strips_ansi_from_ping_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A TTY-aware wrapper around the test harness can trick `spacetime server
    ping` into emitting SGR color codes around the host URL. The probe must
    strip them before parsing — otherwise SPACETIME_E2E_HOST gets fed an
    invalid URL like `\\x1b[32mhttp://...\\x1b[0m` and the dynamic lifecycle
    test fails with a confusing 'cannot dial' error."""

    def fake_run(cmd: list[str], **kwargs: Any) -> _FakeCompletedProcess:
        if "list" in cmd:
            return _FakeCompletedProcess(returncode=0, stdout="local\n")
        return _FakeCompletedProcess(
            returncode=0,
            stdout="\x1b[1mServer is online:\x1b[0m \x1b[32mhttp://127.0.0.1:3000\x1b[0m\n",
        )

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_local_runtime("/fake/spacetime")
    assert result.available
    assert result.host == "http://127.0.0.1:3000"


# ---------------------------------------------------------------------------
# ProbeResult shape (regression guard)
# ---------------------------------------------------------------------------


def test_probe_result_is_frozen() -> None:
    result = ProbeResult(available=True, path="/x")
    with pytest.raises(Exception):
        result.available = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Exec-time failure (PermissionError/OSError) must skip, never error
# ---------------------------------------------------------------------------


def test_probe_spacetime_cli_unrunnable_binary_skips(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_stub_binary(isolated_path, "spacetime")

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_spacetime_cli()
    assert not result.available
    assert "unrunnable" in result.reason


def test_probe_godot_binary_unrunnable_binary_skips(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_stub_binary(isolated_path, "godot-mono")

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        raise OSError(8, "Exec format error")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_godot_binary()
    assert not result.available
    assert "unrunnable" in result.reason


def test_probe_godot_non_mono_binary_unrunnable_binary_skips(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GODOT_WEB_EXPORT_BIN", raising=False)
    _make_stub_binary(isolated_path, "godot")

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_godot_non_mono_binary()
    assert not result.available
    assert "unrunnable" in result.reason


def test_probe_browser_binary_unrunnable_binary_skips(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BROWSER_BIN", raising=False)
    _make_stub_binary(isolated_path, "chromium")

    def fake_run(*args: Any, **kwargs: Any) -> Any:
        raise OSError(8, "Exec format error")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_browser_binary()
    assert not result.available
    assert "unrunnable" in result.reason


def test_probe_local_runtime_unrunnable_binary_skips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> Any:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_local_runtime("/fake/spacetime")
    assert not result.available
    assert "unrunnable" in result.reason


# ---------------------------------------------------------------------------
# Non-zero exit must surface the child's stderr in the skip reason
# ---------------------------------------------------------------------------


def test_probe_godot_binary_nonzero_exit_includes_stderr(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_stub_binary(isolated_path, "godot-mono")

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(returncode=1, stderr="export template missing")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_godot_binary()
    assert not result.available
    assert "exited with" in result.reason
    assert "export template missing" in result.reason


def test_probe_godot_non_mono_binary_nonzero_exit_includes_stderr(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GODOT_WEB_EXPORT_BIN", raising=False)
    _make_stub_binary(isolated_path, "godot")

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(returncode=1, stderr="export template missing")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_godot_non_mono_binary()
    assert not result.available
    assert "exited with" in result.reason
    assert "export template missing" in result.reason


def test_probe_browser_binary_nonzero_exit_includes_stderr(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BROWSER_BIN", raising=False)
    _make_stub_binary(isolated_path, "chromium")

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(returncode=1, stderr="export template missing")

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_browser_binary()
    assert not result.available
    assert "exited with" in result.reason
    assert "export template missing" in result.reason


# ---------------------------------------------------------------------------
# _looks_like_mono_godot_build: anchored markers, no dotnet false positive
# ---------------------------------------------------------------------------


def test_looks_like_mono_godot_build_ignores_incidental_dotnet_banner() -> None:
    banner = "Godot Engine v4.6.3.stable.arch_linux (dotnet runtime present)"
    assert (
        spacetime_runtime._looks_like_mono_godot_build("/usr/bin/godot", banner)
        is False
    )


def test_looks_like_mono_godot_build_still_detects_mono_banner() -> None:
    banner = "Godot Engine v4.6.3.stable.mono.arch_linux"
    assert (
        spacetime_runtime._looks_like_mono_godot_build("/usr/bin/godot", banner)
        is True
    )


def test_probe_godot_non_mono_binary_accepts_dotnet_mentioning_banner(
    isolated_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GODOT_WEB_EXPORT_BIN", raising=False)
    path = _make_stub_binary(isolated_path, "godot")

    def fake_run(*args: Any, **kwargs: Any) -> _FakeCompletedProcess:
        return _FakeCompletedProcess(
            returncode=0,
            stdout="Godot Engine v4.6.3.stable.arch_linux (dotnet runtime present)",
        )

    monkeypatch.setattr(spacetime_runtime.subprocess, "run", fake_run)
    result = probe_godot_non_mono_binary()
    assert result.available
    assert result.path == path


# ---------------------------------------------------------------------------
# mint_anonymous_identity / mint_anonymous_identity_token
# ---------------------------------------------------------------------------

# A token that satisfies the pinned 2.1.0 JWT shape canary (eyJ-prefix, two dots)
# and a 64-char hex identity. Uppercase here to confirm the `[0-9a-fA-F]{64}` validator
# accepts uppercase hex; the case-insensitive *comparison* itself is exercised by the
# live web-export e2e proof, not these mocked unit tests.
_VALID_TOKEN = "eyJhbGciOiJFUzI1NiJ9.eyJoZXhfaWRlbnRpdHkiOiJhYmMifQ.c2lnbmF0dXJl"
_VALID_IDENTITY = "C2008EC24BC2B2DB790A17EC53EC23D6C3835774ACBC0087AB2A40B44BA2EE7B"


class _FakeHTTPResponse:
    """Minimal stand-in for the `urllib.request.urlopen` context manager."""

    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self._status = status

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def getcode(self) -> int:
        return self._status

    def read(self) -> bytes:
        return self._body


def _patch_identity_response(
    monkeypatch: pytest.MonkeyPatch, payload: object, *, status: int = 200
) -> None:
    body = json.dumps(payload).encode("utf-8")

    def _fake_urlopen(request: Any, timeout: float = 0.0) -> _FakeHTTPResponse:
        return _FakeHTTPResponse(body, status)

    monkeypatch.setattr(spacetime_runtime.urllib.request, "urlopen", _fake_urlopen)


def test_mint_anonymous_identity_returns_identity_and_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_identity_response(
        monkeypatch, {"identity": _VALID_IDENTITY, "token": _VALID_TOKEN}
    )
    minted = spacetime_runtime.mint_anonymous_identity("http://127.0.0.1:3000")
    assert isinstance(minted, spacetime_runtime.MintedIdentity)
    assert minted.identity == _VALID_IDENTITY
    assert minted.token == _VALID_TOKEN


def test_mint_anonymous_identity_token_wrapper_returns_only_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_identity_response(
        monkeypatch, {"identity": _VALID_IDENTITY, "token": _VALID_TOKEN}
    )
    token = spacetime_runtime.mint_anonymous_identity_token("http://127.0.0.1:3000")
    assert token == _VALID_TOKEN


@pytest.mark.parametrize(
    "bad_identity",
    [
        "",  # empty
        "xyz",  # too short, non-hex
        "C2008EC2",  # too short
        _VALID_IDENTITY + "AB",  # too long (66 chars)
        "ZZ" * 32,  # 64 chars but non-hex
    ],
)
def test_mint_anonymous_identity_rejects_non_hex_identity(
    monkeypatch: pytest.MonkeyPatch, bad_identity: str
) -> None:
    _patch_identity_response(
        monkeypatch, {"identity": bad_identity, "token": _VALID_TOKEN}
    )
    with pytest.raises(spacetime_runtime.SpacetimeIdentityShapeError):
        spacetime_runtime.mint_anonymous_identity("http://127.0.0.1:3000")


def test_mint_anonymous_identity_rejects_missing_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_identity_response(monkeypatch, {"token": _VALID_TOKEN})
    with pytest.raises(spacetime_runtime.SpacetimeIdentityShapeError):
        spacetime_runtime.mint_anonymous_identity("http://127.0.0.1:3000")
