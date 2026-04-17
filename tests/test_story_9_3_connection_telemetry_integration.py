"""
Story 9.3: Connection Telemetry Integration Test

End-to-end coverage for connect -> subscribe -> invoke reducer -> observe row
change -> read telemetry -> disconnect -> reconnect -> read telemetry again.
The runtime test is skip-safe when local prerequisites are unavailable, and
static contract tests keep the harness red until the telemetry runner is fully
implemented.
"""

from __future__ import annotations

import json
import os
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
SCENE_PATH = "res://tests/godot_integration/telemetry_smoke.tscn"
SCENE = ROOT / "tests/godot_integration/telemetry_smoke.tscn"
RUNNER = ROOT / "tests/godot_integration/TelemetrySmokeRunner.cs"
EVENT_PREFIX = "E2E-EVENT "
EXPECTED_MONITOR_IDS = (
    "GodotSpacetime/Connection/MessagesSent",
    "GodotSpacetime/Connection/MessagesReceived",
    "GodotSpacetime/Connection/BytesSent",
    "GodotSpacetime/Connection/BytesReceived",
    "GodotSpacetime/Connection/UptimeSeconds",
    "GodotSpacetime/Reducers/LastRoundTripMilliseconds",
    "GodotSpacetime/Connection/MessagesReceivedPerSecond",
    "GodotSpacetime/Connection/MessagesSentPerSecond",
    "GodotSpacetime/Connection/BytesReceivedPerSecond",
    "GodotSpacetime/Connection/BytesSentPerSecond",
)
REQUIRED_STEPS = (
    "connect",
    "subscribe",
    "invoke_reducer",
    "observe_row_change",
    "read_telemetry",
    "disconnect",
    "connect_reconnect",
    "read_telemetry_reconnect",
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


def test_telemetry_harness_files_exist() -> None:
    assert SCENE.exists(), "telemetry_smoke.tscn missing under tests/godot_integration/"
    assert RUNNER.exists(), "TelemetrySmokeRunner.cs missing under tests/godot_integration/"


def test_telemetry_runner_contract_strings_present() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "SPACETIME_E2E_HOST",
        "SPACETIME_E2E_MODULE",
        "SPACETIME_E2E_VALUE",
        '"connect"',
        '"subscribe"',
        '"invoke_reducer"',
        '"observe_row_change"',
        '"read_telemetry"',
        '"disconnect"',
        '"connect_reconnect"',
        '"read_telemetry_reconnect"',
        '"messages_sent"',
        '"messages_received"',
        '"bytes_sent"',
        '"bytes_received"',
        '"connection_uptime_seconds"',
        '"last_reducer_round_trip_milliseconds"',
        '"performance_monitors"',
        '"monitor_matches_public_surface"',
        '"bytes_sent_proven"',
        '"bytes_sent_source"',
        '"stable_telemetry_instance_reused"',
        "CurrentTelemetry",
        "Performance.GetCustomMonitor",
    ):
        assert expected in content, (
            "Telemetry smoke runner must emit the required phase names and telemetry payload keys, including "
            f"{expected!r} (Task 6.2, Task 6.3, Task 6.4, Task 6.5, Task 6.6)."
        )


def test_telemetry_runner_rejects_fabricated_outbound_byte_claims() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "bytes_sent_proven",
        "bytes_sent_source",
        "fail loudly",
    ):
        assert expected in content, (
            "Story 9.3's runtime harness must encode the outbound-byte proof requirement explicitly instead of "
            f"silently accepting invented values. Missing {expected!r} in TelemetrySmokeRunner.cs (Task 0.4, Task 6.6)."
        )


def test_telemetry_integration_reuses_smoke_test_and_prerequisite_probes() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    for expected in (
        "probe_spacetime_cli",
        "probe_godot_binary",
        "probe_local_runtime",
        'str(ROOT / "spacetime" / "modules" / "smoke_test")',
    ):
        assert expected in content, (
            "Telemetry integration coverage must stay skip-safe and keep reusing the shared smoke_test "
            f"module/runtime probe pattern. Missing {expected!r}"
        )


def test_telemetry_integration_is_independent_and_avoids_hardcoded_waits() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    assert 'module_name = f"smoke-test-telemetry-{uuid.uuid4().hex[:12]}"' in content and 'env["SPACETIME_E2E_VALUE"] = f"telemetry-{uuid.uuid4().hex[:8]}"' in content, (
        "Telemetry integration coverage must isolate each run with unique module names and inserted values so "
        "story tests remain order-independent."
    )
    assert content.count("time.sleep(") == 1, (
        "Telemetry integration coverage must use explicit subprocess and step timeouts instead of hardcoded sleeps."
    )


def test_connection_telemetry_e2e() -> None:
    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(f"SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    module_name = f"smoke-test-telemetry-{uuid.uuid4().hex[:12]}"
    try:
        _publish_module(cli_probe.path, runtime_probe.server, module_name)
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(exc.stderr or b'').decode('utf-8', 'replace')[:200]}"
        )
    except subprocess.TimeoutExpired:
        pytest.skip("SpacetimeDB runtime unavailable: smoke_test publish timed out after 180s")

    env = os.environ.copy()
    env["SPACETIME_E2E_HOST"] = runtime_probe.host
    env["SPACETIME_E2E_MODULE"] = module_name
    env["SPACETIME_E2E_VALUE"] = f"telemetry-{uuid.uuid4().hex[:8]}"
    env["SPACETIME_E2E_STEP_TIMEOUT"] = str(STEP_TIMEOUT_SECONDS)

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
        f"telemetry harness did not finish within {TOTAL_TIMEOUT_SECONDS}s "
        f"(elapsed={elapsed:.1f}s)"
    )
    assert events, (
        "telemetry runner emitted no events. "
        f"godot exit={proc.returncode}. stdout tail="
        f"{(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]}. stderr tail="
        f"{(proc.stderr or b'').decode('utf-8', 'replace')[-600:]}"
    )

    step_sequence = [event["name"] for event in events if event.get("event") == "step"]
    assert step_sequence == list(REQUIRED_STEPS), (
        "telemetry harness must emit the required phase sequence in order. "
        f"got step_sequence={step_sequence}"
    )

    steps = {event["name"]: event for event in events if event.get("event") == "step"}
    for step in REQUIRED_STEPS:
        assert steps[step]["status"] == "ok", f"{step} step failed: {steps[step]}"

    telemetry_step = steps["read_telemetry"]
    disconnect_step = steps["disconnect"]
    reconnect_connect_step = steps["connect_reconnect"]
    reconnect_step = steps["read_telemetry_reconnect"]

    for key in (
        "messages_sent",
        "messages_received",
        "bytes_sent",
        "bytes_received",
        "connection_uptime_seconds",
        "last_reducer_round_trip_milliseconds",
        "performance_monitors",
        "monitor_matches_public_surface",
        "bytes_sent_proven",
        "bytes_sent_source",
    ):
        assert key in telemetry_step, (
            f"read_telemetry must expose {key!r} from both the public telemetry surface and monitor layer. "
            f"got {telemetry_step}"
        )

    assert telemetry_step["monitor_matches_public_surface"] is True, (
        "Performance custom monitors must agree with the pull-based CurrentTelemetry surface within the harness "
        "tolerances instead of drifting independently."
    )
    assert telemetry_step["messages_sent"] >= 1
    assert telemetry_step["messages_received"] >= 1
    assert telemetry_step["bytes_received"] >= 1
    assert telemetry_step["connection_uptime_seconds"] >= 0
    assert telemetry_step["last_reducer_round_trip_milliseconds"] > 0
    assert telemetry_step["bytes_sent_source"] == "sdk_client_message_bsatn", (
        "Story 9.3 anchors outbound-byte proof to the pinned SDK ClientMessage.BSATN serializer path."
    )
    assert telemetry_step["bytes_sent_proven"] is True, (
        "Story 9.3 must prove outbound-byte telemetry against the supported runtime rather than emitting a guess."
    )
    assert sorted(telemetry_step["performance_monitors"]) == sorted(EXPECTED_MONITOR_IDS)
    assert all(value >= 0 for value in telemetry_step["performance_monitors"].values())

    assert disconnect_step["messages_sent"] == 0
    assert disconnect_step["messages_received"] == 0
    assert disconnect_step["bytes_sent"] == 0
    assert disconnect_step["bytes_received"] == 0
    assert disconnect_step["connection_uptime_seconds"] == 0
    assert disconnect_step["last_reducer_round_trip_milliseconds"] == 0
    assert disconnect_step["monitor_matches_public_surface"] is True

    assert reconnect_connect_step["stable_telemetry_instance_reused"] is True, (
        "Story 9.3 must reuse the same ConnectionTelemetryStats object across disconnect/reconnect instead of "
        "allocating a fresh surface for the next session."
    )

    assert reconnect_step["messages_sent"] == 0
    assert reconnect_step["messages_received"] == 0
    assert reconnect_step["bytes_sent"] == 0
    assert reconnect_step["bytes_received"] == 0
    assert reconnect_step["connection_uptime_seconds"] >= 0
    assert reconnect_step["last_reducer_round_trip_milliseconds"] == 0
    assert reconnect_step["monitor_matches_public_surface"] is True
    assert reconnect_step["bytes_sent_source"] == ""
    assert sorted(reconnect_step["performance_monitors"]) == sorted(EXPECTED_MONITOR_IDS)
    assert all(value >= 0 for value in reconnect_step["performance_monitors"].values())

    done = next((event for event in events if event.get("event") == "done"), None)
    assert done is not None, f"telemetry runner did not emit done event. events={events}"
    assert done.get("status") == "pass", f"runner finished with {done}"
    assert done.get("stable_telemetry_instance_reused") is True
    assert done.get("bytes_sent_source") == "sdk_client_message_bsatn"
    assert done.get("bytes_sent_proven") is True
    assert proc.returncode == 0, (
        f"telemetry runner exited with code {proc.returncode}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )
