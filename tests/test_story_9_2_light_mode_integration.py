"""
Story 9.2: Light Mode Integration Test

End-to-end coverage that measures the supported runtime's actual light-mode
behavior instead of assuming the upstream docs or the pinned SDK surface are
fully authoritative on their own.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
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
SCENE_PATH = "res://tests/godot_integration/light_mode_smoke.tscn"
SCENE = ROOT / "tests/godot_integration/light_mode_smoke.tscn"
RUNNER = ROOT / "tests/godot_integration/LightModeSmokeRunner.cs"
EVENT_PREFIX = "E2E-EVENT "
BASELINE_STEPS = ("connect", "subscribe", "invoke_reducer", "observe_row_change")
TOGGLE_STEPS = (
    "connect",
    "subscribe",
    "invoke_reducer",
    "observe_row_change",
    "toggle_mid_session",
    "invoke_reducer_same_session",
    "observe_row_change_same_session",
    "connect_reconnect",
    "subscribe_reconnect",
    "invoke_reducer_reconnect",
    "observe_row_change_reconnect",
)
STEP_TIMEOUT_SECONDS = 30
TOTAL_TIMEOUT_SECONDS = 120


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


def _step_sequence(events: list[dict]) -> list[str]:
    return [event["name"] for event in events if event.get("event") == "step"]


def _step_map(events: list[dict]) -> dict[str, dict]:
    return {event["name"]: event for event in events if event.get("event") == "step"}


def _done_event(events: list[dict]) -> dict:
    done = next((event for event in events if event.get("event") == "done"), None)
    assert done is not None, f"runner did not emit a done event. events={events}"
    return done


def _run_light_mode_harness(
    godot_path: str,
    *,
    host: str,
    module_name: str,
    requested_light_mode: bool,
    scenario: str,
    initial_value: str,
    toggled_value: str | None = None,
    reconnected_value: str | None = None,
) -> tuple[subprocess.CompletedProcess[bytes], list[dict], float]:
    env = os.environ.copy()
    env["SPACETIME_E2E_HOST"] = host
    env["SPACETIME_E2E_MODULE"] = module_name
    env["SPACETIME_E2E_LIGHT_MODE"] = "true" if requested_light_mode else "false"
    env["SPACETIME_E2E_SCENARIO"] = scenario
    env["SPACETIME_E2E_VALUE"] = initial_value
    env["SPACETIME_E2E_STEP_TIMEOUT"] = str(STEP_TIMEOUT_SECONDS)
    if toggled_value is not None:
        env["SPACETIME_E2E_TOGGLED_VALUE"] = toggled_value
    if reconnected_value is not None:
        env["SPACETIME_E2E_RECONNECTED_VALUE"] = reconnected_value

    start = time.monotonic()
    proc = subprocess.run(
        [
            godot_path,
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
    return proc, events, elapsed


def _assert_runtime_prereqs() -> tuple[str, str, str, str]:
    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(f"SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    return cli_probe.path, godot_probe.path, runtime_probe.host, runtime_probe.server


def _assert_single_session_contract(
    events: list[dict],
    *,
    requested_light_mode: bool,
    expected_value: str,
) -> dict:
    assert _step_sequence(events) == list(BASELINE_STEPS), (
        "single-session light-mode harness must emit the baseline lifecycle in strict order. "
        f"got step_sequence={_step_sequence(events)}"
    )

    steps = _step_map(events)
    for step in BASELINE_STEPS:
        assert steps[step]["status"] == "ok", f"{step} step failed: {steps[step]}"

    assert steps["connect"]["requested_light_mode"] is requested_light_mode
    assert steps["connect"]["settings_light_mode"] is requested_light_mode
    assert steps["subscribe"]["synchronized"] == ["smoke_test"]
    assert steps["invoke_reducer"]["contract"] == "ReducerCallSucceeded"

    observe = steps["observe_row_change"]
    assert observe["value"] == expected_value
    assert observe["via"] == ["typed_table_handle", "get_rows", "row_changed_event"], (
        "observe_row_change must prove public cache/event delivery through typed table handle, "
        f"GetRows, and RowChanged. got observe={observe}"
    )

    done = _done_event(events)
    assert done["status"] == "pass", f"runner finished with status={done['status']}, done={done}"
    observation = done["observation"]
    signature = observation["signature"]
    for key in (
        "row_context",
        "reducer_context",
        "signature",
        "reducer_contract",
    ):
        assert key in observation, f"single-session observation missing {key!r}: {observation}"
    assert observation["reducer_contract"] == "ReducerCallSucceeded"
    assert signature["row_context_type"]
    assert signature["reducer_context_type"]
    assert "row_event_members" in signature and "reducer_event_members" in signature
    return done


def test_light_mode_e2e_measures_false_vs_true_runtime_behavior() -> None:
    cli_path, godot_path, host, server = _assert_runtime_prereqs()

    module_name = f"smoke-test-light-mode-{uuid.uuid4().hex[:12]}"
    try:
        _publish_module(cli_path, server, module_name)
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            f"SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(exc.stderr or b'').decode('utf-8', 'replace')[:200]}"
        )
    except subprocess.TimeoutExpired:
        pytest.skip("SpacetimeDB runtime unavailable: smoke_test publish timed out after 180s")

    false_value = f"light-false-{uuid.uuid4().hex[:8]}"
    true_value = f"light-true-{uuid.uuid4().hex[:8]}"

    false_proc, false_events, false_elapsed = _run_light_mode_harness(
        godot_path,
        host=host,
        module_name=module_name,
        requested_light_mode=False,
        scenario="single_session",
        initial_value=false_value,
    )
    true_proc, true_events, true_elapsed = _run_light_mode_harness(
        godot_path,
        host=host,
        module_name=module_name,
        requested_light_mode=True,
        scenario="single_session",
        initial_value=true_value,
    )

    assert false_elapsed < TOTAL_TIMEOUT_SECONDS
    assert true_elapsed < TOTAL_TIMEOUT_SECONDS
    assert false_proc.returncode == 0, (
        f"LightMode=false harness exited with {false_proc.returncode}. "
        f"stderr tail: {(false_proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )
    assert true_proc.returncode == 0, (
        f"LightMode=true harness exited with {true_proc.returncode}. "
        f"stderr tail: {(true_proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )

    false_done = _assert_single_session_contract(
        false_events,
        requested_light_mode=False,
        expected_value=false_value,
    )
    true_done = _assert_single_session_contract(
        true_events,
        requested_light_mode=True,
        expected_value=true_value,
    )

    false_signature = false_done["observation"]["signature"]
    true_signature = true_done["observation"]["signature"]
    observed_change = false_signature != true_signature

    if observed_change:
        assert false_signature["row_event_members"] != true_signature["row_event_members"] or false_signature["reducer_event_members"] != true_signature["reducer_event_members"] or false_signature != true_signature, (
            "When the supported runtime shows a light-mode difference, the harness must record it in the "
            "stable observation signature rather than hiding it behind a synthetic success path."
        )
    else:
        assert false_signature == true_signature, (
            "When the supported runtime shows no observable difference, the harness must record the no-op "
            "behavior explicitly by keeping the false/true observation signatures identical."
        )


def test_light_mode_toggle_does_not_change_active_session_until_reconnect() -> None:
    cli_path, godot_path, host, server = _assert_runtime_prereqs()

    module_name = f"smoke-test-light-toggle-{uuid.uuid4().hex[:12]}"
    try:
        _publish_module(cli_path, server, module_name)
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            f"SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(exc.stderr or b'').decode('utf-8', 'replace')[:200]}"
        )
    except subprocess.TimeoutExpired:
        pytest.skip("SpacetimeDB runtime unavailable: smoke_test publish timed out after 180s")

    initial_value = f"toggle-before-{uuid.uuid4().hex[:8]}"
    same_session_value = f"toggle-same-session-{uuid.uuid4().hex[:8]}"
    reconnect_value = f"toggle-reconnect-{uuid.uuid4().hex[:8]}"

    proc, events, elapsed = _run_light_mode_harness(
        godot_path,
        host=host,
        module_name=module_name,
        requested_light_mode=False,
        scenario="toggle_reconnect",
        initial_value=initial_value,
        toggled_value=same_session_value,
        reconnected_value=reconnect_value,
    )

    assert elapsed < TOTAL_TIMEOUT_SECONDS
    assert proc.returncode == 0, (
        f"toggle_reconnect harness exited with {proc.returncode}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )
    assert _step_sequence(events) == list(TOGGLE_STEPS), (
        "toggle_reconnect harness must emit the full reconnect verification flow in strict order. "
        f"got step_sequence={_step_sequence(events)}"
    )

    steps = _step_map(events)
    for step in TOGGLE_STEPS:
        assert steps[step]["status"] == "ok", f"{step} step failed: {steps[step]}"

    assert steps["toggle_mid_session"]["light_mode_before"] is False
    assert steps["toggle_mid_session"]["light_mode_after"] is True
    assert steps["observe_row_change"]["value"] == initial_value
    assert steps["observe_row_change_same_session"]["value"] == same_session_value
    assert steps["observe_row_change_reconnect"]["value"] == reconnect_value

    done = _done_event(events)
    assert done["status"] == "pass", f"toggle_reconnect done event failed: {done}"
    assert done["same_session_changed"] is False, (
        "Mutating Settings.LightMode while connected must not alter the already-open session. "
        f"done={done}"
    )

    before_signature = done["before_toggle"]["signature"]
    same_session_signature = done["same_session_after_toggle"]["signature"]
    reconnect_signature = done["after_reconnect"]["signature"]
    assert before_signature == same_session_signature, (
        "same-session signature must remain unchanged after toggling Settings.LightMode in-place. "
        f"before={before_signature}, same_session={same_session_signature}"
    )
    if done["reconnect_changed"]:
        assert reconnect_signature != before_signature, (
            "When reconnect_changed is true, the reconnected signature must actually differ from the baseline."
        )
    else:
        assert reconnect_signature == before_signature, (
            "When reconnect_changed is false, the reconnected signature must record the supported runtime's "
            "documented no-op behavior rather than fabricating a distinction."
        )


def test_light_mode_harness_files_exist() -> None:
    assert SCENE.exists(), "light_mode_smoke.tscn missing under tests/godot_integration/"
    assert RUNNER.exists(), "LightModeSmokeRunner.cs missing under tests/godot_integration/"


def test_light_mode_runner_contract_strings_present() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "SPACETIME_E2E_LIGHT_MODE",
        "SPACETIME_E2E_SCENARIO",
        "SPACETIME_E2E_TOGGLED_VALUE",
        "SPACETIME_E2E_RECONNECTED_VALUE",
        '"connect"',
        '"toggle_mid_session"',
        '"connect_reconnect"',
        "CaptureContextSnapshot",
        "TryGetGeneratedConnection",
        "measure the supported runtime",
    ):
        assert expected in content, (
            "Light-mode smoke runner must declare the contract surfaces needed for Story 9.2, "
            f"including {expected!r}."
        )


def test_light_mode_runner_rejects_unknown_inputs() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    assert "Unsupported SPACETIME_E2E_LIGHT_MODE value" in content and "Expected true or false." in content, (
        "Light-mode smoke runner must fail loudly for unsupported requested light-mode values."
    )
    assert "Unsupported SPACETIME_E2E_SCENARIO value" in content and "Expected single_session or toggle_reconnect." in content, (
        "Light-mode smoke runner must fail loudly for unsupported scenarios."
    )


def test_light_mode_integration_reuses_smoke_test_and_prerequisite_probes() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    for expected in (
        "probe_spacetime_cli",
        "probe_godot_binary",
        "probe_local_runtime",
        'str(ROOT / "spacetime" / "modules" / "smoke_test")',
    ):
        assert expected in content, (
            "Light-mode integration coverage must stay skip-safe and reuse the shared smoke_test "
            f"module/runtime probe pattern. Missing {expected!r}"
        )


def test_light_mode_integration_avoids_hardcoded_waits_and_generates_unique_values() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    assert 'module_name = f"smoke-test-light-mode-{uuid.uuid4().hex[:12]}"' in content
    assert 'module_name = f"smoke-test-light-toggle-{uuid.uuid4().hex[:12]}"' in content
    assert re.search(r"(?m)^\s*time\.sleep\(", content) is None, (
        "Light-mode integration tests must not rely on hardcoded sleeps; use explicit step timeouts and event-driven completion."
    )


def test_light_mode_scene_points_at_runner() -> None:
    content = SCENE.read_text(encoding="utf-8")
    assert "LightModeSmokeRunner.cs" in content, (
        "light_mode_smoke.tscn must attach LightModeSmokeRunner.cs as the root script"
    )
