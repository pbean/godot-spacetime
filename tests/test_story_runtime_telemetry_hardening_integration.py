"""
Executable proof for runtime telemetry hardening.

Runs a headless Godot scene that exercises ConnectionTelemetryCollector without
a live SpacetimeDB runtime. This is the behavioral proof lane for reconnect
rebasing, late-callback isolation, and monotonic rate refresh.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import probe_godot_binary

ROOT = Path(__file__).resolve().parents[1]
SCENE_PATH = "res://tests/godot_integration/telemetry_collector_hardening.tscn"
SCENE = ROOT / "tests/godot_integration/telemetry_collector_hardening.tscn"
RUNNER = ROOT / "tests/godot_integration/TelemetryCollectorHardeningRunner.cs"
EVENT_PREFIX = "E2E-EVENT "
TOTAL_TIMEOUT_SECONDS = 30
REQUIRED_STEPS = (
    "session_1_started",
    "session_1_rates",
    "session_2_reset",
    "old_session_callbacks_ignored",
    "session_2_traffic",
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


def test_runtime_hardening_harness_files_exist() -> None:
    assert SCENE.exists(), "telemetry_collector_hardening.tscn missing under tests/godot_integration/"
    assert RUNNER.exists(), "TelemetryCollectorHardeningRunner.cs missing under tests/godot_integration/"


def test_runtime_hardening_runner_contract_strings_present() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        '"session_1_started"',
        '"session_1_rates"',
        '"session_2_reset"',
        '"old_session_callbacks_ignored"',
        '"session_2_traffic"',
        '"messages_sent"',
        '"messages_received"',
        '"bytes_sent"',
        '"bytes_received"',
        '"connection_uptime_seconds"',
        '"last_reducer_round_trip_milliseconds"',
        '"messages_received_per_second"',
        '"messages_sent_per_second"',
        '"bytes_received_per_second"',
        '"bytes_sent_per_second"',
        '"stable_telemetry_instance_reused"',
        "InitializeTrackerBaseline",
        "SyncTrackerCounts",
    ):
        assert expected in content, (
            "The collector hardening runner must advertise the expected step names and telemetry payload keys. "
            f"Missing {expected!r}."
        )


def test_connection_telemetry_hardening_e2e() -> None:
    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    proc = subprocess.run(
        [
            godot_probe.path,
            "--headless",
            "--path",
            str(ROOT),
            SCENE_PATH,
        ],
        cwd=ROOT,
        capture_output=True,
        timeout=TOTAL_TIMEOUT_SECONDS,
    )
    events = _parse_events_from_stdout(proc.stdout or b"")

    assert events, (
        "collector hardening runner emitted no events. "
        f"godot exit={proc.returncode}. stdout tail="
        f"{(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]}. stderr tail="
        f"{(proc.stderr or b'').decode('utf-8', 'replace')[-600:]}"
    )

    step_sequence = [event["name"] for event in events if event.get("event") == "step"]
    assert step_sequence == list(REQUIRED_STEPS), (
        "collector hardening runner must emit the required phase sequence in order. "
        f"got step_sequence={step_sequence}"
    )

    steps = {event["name"]: event for event in events if event.get("event") == "step"}
    for step in REQUIRED_STEPS:
        assert steps[step]["status"] == "ok", f"{step} step failed: {steps[step]}"

    session_1_started = steps["session_1_started"]
    session_1_rates = steps["session_1_rates"]
    session_2_reset = steps["session_2_reset"]
    old_session_ignored = steps["old_session_callbacks_ignored"]
    session_2_traffic = steps["session_2_traffic"]

    assert session_1_started["stable_telemetry_instance_reused"] is True

    for key in (
        "messages_sent",
        "messages_received",
        "bytes_sent",
        "bytes_received",
        "connection_uptime_seconds",
        "last_reducer_round_trip_milliseconds",
        "messages_received_per_second",
        "messages_sent_per_second",
        "bytes_received_per_second",
        "bytes_sent_per_second",
    ):
        assert key in session_1_rates, f"session_1_rates missing {key!r}: {session_1_rates}"
        assert key in session_2_reset, f"session_2_reset missing {key!r}: {session_2_reset}"
        assert key in old_session_ignored, f"old_session_callbacks_ignored missing {key!r}: {old_session_ignored}"
        assert key in session_2_traffic, f"session_2_traffic missing {key!r}: {session_2_traffic}"

    assert session_1_rates["messages_sent"] == 1
    assert session_1_rates["messages_received"] == 1
    assert session_1_rates["bytes_sent"] == 32
    assert session_1_rates["bytes_received"] == 64
    assert session_1_rates["connection_uptime_seconds"] >= 1.0
    assert session_1_rates["messages_received_per_second"] > 0
    assert session_1_rates["messages_sent_per_second"] > 0
    assert session_1_rates["bytes_received_per_second"] > 0
    assert session_1_rates["bytes_sent_per_second"] > 0

    for zero_step in (session_2_reset, old_session_ignored):
        assert zero_step["messages_sent"] == 0
        assert zero_step["messages_received"] == 0
        assert zero_step["bytes_sent"] == 0
        assert zero_step["bytes_received"] == 0
        assert zero_step["last_reducer_round_trip_milliseconds"] == 0
        assert zero_step["messages_received_per_second"] == 0
        assert zero_step["messages_sent_per_second"] == 0
        assert zero_step["bytes_received_per_second"] == 0
        assert zero_step["bytes_sent_per_second"] == 0
        assert zero_step["stable_telemetry_instance_reused"] is True

    assert session_2_traffic["messages_sent"] == 1
    assert session_2_traffic["messages_received"] == 1
    assert session_2_traffic["bytes_sent"] == 24
    assert session_2_traffic["bytes_received"] == 40
    assert session_2_traffic["last_reducer_round_trip_milliseconds"] > 0
    assert session_2_traffic["messages_received_per_second"] > 0
    assert session_2_traffic["messages_sent_per_second"] > 0
    assert session_2_traffic["bytes_received_per_second"] > 0
    assert session_2_traffic["bytes_sent_per_second"] > 0
    assert session_2_traffic["stable_telemetry_instance_reused"] is True

    done = next((event for event in events if event.get("event") == "done"), None)
    assert done is not None, f"collector hardening runner did not emit done event. events={events}"
    assert done.get("status") == "pass", f"runner finished with {done}"
    assert done.get("stable_telemetry_instance_reused") is True
    assert proc.returncode == 0, (
        f"collector hardening runner exited with code {proc.returncode}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )
