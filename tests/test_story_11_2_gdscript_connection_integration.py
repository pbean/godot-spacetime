"""
Story 11.2: GDScript connection integration smoke coverage

Runs a headless Godot scene that exercises the native GDScript connection
service against a real local SpacetimeDB runtime when available.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import (
    probe_godot_binary,
    probe_local_runtime,
    probe_spacetime_cli,
)

ROOT = Path(__file__).resolve().parents[1]
SCENE_PATH = "res://tests/godot_integration/gdscript_connection_smoke.tscn"
SCENE = ROOT / "tests/godot_integration/gdscript_connection_smoke.tscn"
RUNNER = ROOT / "tests/godot_integration/gdscript_connection_smoke.gd"
EVENT_PREFIX = "E2E-EVENT "
STEP_TIMEOUT_SECONDS = 30
TOTAL_TIMEOUT_SECONDS = 180
REQUIRED_STEPS = (
    "connect_anonymous",
    "disconnect_clean",
    "observe_degraded",
    "recover_connection",
    "restored_token_rejected",
    "anonymous_fallback",
)
EXPECTED_STATE_SEQUENCE = [
    "Connecting",
    "Connected",
    "Disconnected",
    "Connecting",
    "Connected",
    "Degraded",
    "Connected",
    "Disconnected",
    "Connecting",
    "Disconnected",
    "Connecting",
    "Connected",
]


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


def _parse_events_from_stdout(stdout: bytes) -> list[dict]:
    events: list[dict] = []
    text = stdout.decode("utf-8", errors="replace")
    for raw in text.splitlines():
        stripped = raw.strip()
        idx = stripped.find(EVENT_PREFIX)
        if idx == -1:
            continue
        payload = stripped[idx + len(EVENT_PREFIX):].strip()
        try:
            events.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    return events


def test_story_11_2_smoke_harness_files_exist() -> None:
    assert SCENE.exists(), "gdscript_connection_smoke.tscn missing under tests/godot_integration/"
    assert RUNNER.exists(), "gdscript_connection_smoke.gd missing under tests/godot_integration/"


def test_story_11_2_runner_encodes_required_env_contract_and_steps() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "SPACETIME_E2E_HOST",
        "SPACETIME_E2E_MODULE",
        "SPACETIME_E2E_STEP_TIMEOUT",
        "SPACETIME_E2E_TOKEN_PATH",
        '"connect_anonymous"',
        '"disconnect_clean"',
        '"observe_degraded"',
        '"recover_connection"',
        '"restored_token_rejected"',
        '"anonymous_fallback"',
    ):
        assert expected in content, (
            "gdscript_connection_smoke.gd must declare the step contract and environment inputs for the headless lane. "
            f"Missing {expected!r}."
        )


def test_story_11_2_runner_uses_native_gdscript_runtime_seam() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "gdscript_connection_service.gd",
        "file_token_store.gd",
        "force_transport_fault_for_testing",
        '_emit_event("state"',
        '_emit_event("connection_closed"',
        "JSON.stringify",
        EVENT_PREFIX,
    ):
        assert expected in content, (
            "gdscript_connection_smoke.gd must drive the native GDScript service and emit JSON-per-line events. "
            f"Missing {expected!r}."
        )


def test_story_11_2_integration_reuses_runtime_probes_and_smoke_test_module() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    for expected in (
        "probe_spacetime_cli",
        "probe_godot_binary",
        "probe_local_runtime",
        'str(ROOT / "spacetime" / "modules" / "smoke_test")',
    ):
        assert expected in content, (
            "Story 11.2 integration coverage must stay skip-safe and reuse the shared smoke_test runtime pattern. "
            f"Missing {expected!r}."
        )


def test_story_11_2_gdscript_connection_smoke_e2e() -> None:
    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(f"SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    module_name = f"gdscript-conn-smoke-{uuid.uuid4().hex[:12]}"
    try:
        _publish_module(cli_probe.path, runtime_probe.server, module_name)
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(exc.stderr or b'').decode('utf-8', 'replace')[:240]}"
        )
    except subprocess.TimeoutExpired:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish timed out after 180s"
        )

    with tempfile.TemporaryDirectory(prefix="story-11-2-godot-home-") as godot_home:
        env = os.environ.copy()
        env["HOME"] = godot_home
        env["XDG_DATA_HOME"] = godot_home
        env["XDG_CONFIG_HOME"] = godot_home
        env["SPACETIME_E2E_HOST"] = runtime_probe.host
        env["SPACETIME_E2E_MODULE"] = module_name
        env["SPACETIME_E2E_STEP_TIMEOUT"] = str(STEP_TIMEOUT_SECONDS)
        env["SPACETIME_E2E_TOKEN_PATH"] = "user://spacetime/test_story_11_2/token"

        start = time.monotonic()
        proc = subprocess.run(
            [
                godot_probe.path,
                "--headless",
                "--path",
                str(ROOT),
                SCENE_PATH,
            ],
            env=env,
            cwd=ROOT,
            capture_output=True,
            timeout=TOTAL_TIMEOUT_SECONDS,
        )
        elapsed = time.monotonic() - start

    events = _parse_events_from_stdout(proc.stdout or b"")
    assert elapsed < TOTAL_TIMEOUT_SECONDS, (
        f"gdscript connection smoke harness did not finish within {TOTAL_TIMEOUT_SECONDS}s "
        f"(elapsed={elapsed:.1f}s)"
    )
    assert events, (
        "gdscript connection smoke runner emitted no events. "
        f"godot exit={proc.returncode}. elapsed={elapsed:.2f}s. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-600:]}"
    )

    error_steps = [e for e in events if e.get("event") == "step" and e.get("status") == "error"]
    assert not error_steps, f"gdscript connection smoke runner reported failing step(s): {error_steps}"

    step_sequence = [e["name"] for e in events if e.get("event") == "step" and e.get("status") == "ok"]
    assert step_sequence == list(REQUIRED_STEPS), (
        "gdscript connection smoke runner must emit the full Story 11.2 lifecycle in strict order. "
        f"got step_sequence={step_sequence}"
    )

    steps = {e["name"]: e for e in events if e.get("event") == "step" and e.get("status") == "ok"}
    done = next((e for e in events if e.get("event") == "done"), None)
    state_events = [e for e in events if e.get("event") == "state"]
    close_events = [e for e in events if e.get("event") == "connection_closed"]

    assert done is not None, f"missing done event in gdscript connection smoke log: {events}"
    assert done.get("status") == "ok", f"done event reported failure: {done}"
    assert state_events, f"missing lifecycle state events in gdscript connection smoke log: {events}"

    assert steps["connect_anonymous"].get("state") == "Connected"
    assert steps["connect_anonymous"].get("auth_state") == "None"
    assert steps["connect_anonymous"].get("identity"), "initial anonymous connect must report a server identity"

    assert steps["disconnect_clean"].get("close_reason") == "Clean"

    degraded_description = steps["observe_degraded"].get("description", "")
    assert degraded_description.startswith(
        "DEGRADED — session experiencing issues; reconnecting (attempt 1/3"
    ), (
        "the recovery step must surface the documented Degraded message with attempt 1/3 wording. "
        f"got {degraded_description!r}"
    )

    assert steps["recover_connection"].get("description") == "CONNECTED — active session established after recovery"
    assert steps["recover_connection"].get("token_restored") is True

    assert steps["restored_token_rejected"].get("auth_state") == "TokenExpired"
    assert steps["restored_token_rejected"].get("token_cleared") is True

    assert steps["anonymous_fallback"].get("auth_state") == "None"
    assert steps["anonymous_fallback"].get("identity"), "anonymous fallback must establish a live session identity"
    assert steps["anonymous_fallback"].get("token_present") is True

    observed_states = [str(event.get("state", "")) for event in state_events]
    assert observed_states == EXPECTED_STATE_SEQUENCE, (
        "gdscript connection smoke runner must observe the Story 11.2 lifecycle state sequence in order. "
        f"got observed_states={observed_states}"
    )

    token_expired_disconnect = next(
        (
            event
            for event in state_events
            if event.get("state") == "Disconnected" and event.get("auth_state") == "TokenExpired"
        ),
        None,
    )
    assert token_expired_disconnect is not None, (
        "restored-token rejection must surface as a Disconnected state with TokenExpired auth semantics."
    )
    assert str(token_expired_disconnect.get("description", "")).startswith(
        "DISCONNECTED — stored token was rejected:"
    ), token_expired_disconnect

    assert len(close_events) == 2, (
        "connection_closed should only fire for the two live-session clean disconnects in the Story 11.2 smoke lane. "
        f"got close_events={close_events}"
    )
    assert [event.get("close_reason") for event in close_events] == ["Clean", "Clean"], close_events
    assert all(not event.get("error_message") for event in close_events), close_events
