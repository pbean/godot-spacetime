"""
Runtime telemetry hardening static guardrails.

These assertions intentionally stay structural. Behavioral proof for reconnect
carry-over, late-callback isolation, and real elapsed-time rate refresh lives in
tests/test_story_runtime_telemetry_hardening_integration.py.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COLLECTOR_REL = "addons/godot_spacetime/src/Internal/Connection/ConnectionTelemetryCollector.cs"
SERVICE_REL = "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
CLIENT_REL = "addons/godot_spacetime/src/Public/SpacetimeClient.cs"
STATS_REL = "addons/godot_spacetime/src/Public/Connection/ConnectionTelemetryStats.cs"
RUNNER_REL = "tests/godot_integration/TelemetryCollectorHardeningRunner.cs"
SCENE_REL = "tests/godot_integration/telemetry_collector_hardening.tscn"
INTEGRATION_REL = "tests/test_story_runtime_telemetry_hardening_integration.py"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_collector_uses_monotonic_elapsed_time_for_uptime_and_rate_refresh() -> None:
    content = _read(COLLECTOR_REL)
    for expected in (
        "using System.Diagnostics;",
        "Stopwatch.GetTimestamp()",
        "_connectedAtTimestamp",
        "_rateBaselineTimestamp",
        "GetElapsedSeconds",
    ):
        assert expected in content, (
            f"{COLLECTOR_REL} must keep the uptime/rate path on a monotonic Stopwatch-based elapsed source. "
            f"Missing {expected!r}."
        )
    assert "DateTimeOffset.UtcNow" not in content, (
        f"{COLLECTOR_REL} must not fall back to DateTimeOffset.UtcNow for uptime/rate deltas."
    )


def test_collector_keeps_session_scoped_callbacks_and_connect_time_tracker_baseline_separate() -> None:
    content = _read(COLLECTOR_REL)
    for expected in (
        "StartSession(long sessionId)",
        "InitializeTrackerBaseline(long sessionId, long messagesSent, long messagesReceived)",
        "SyncTrackerCounts(long sessionId, long messagesSent, long messagesReceived)",
        "RecordInboundMessage(long sessionId, int byteCount)",
        "RecordOutboundMessage(long sessionId, long byteCount)",
        "RecordReducerRoundTrip(long sessionId, DateTimeOffset calledAt, DateTimeOffset finishedAt)",
        "_trackerBaselineArmed",
    ):
        assert expected in content, (
            f"{COLLECTOR_REL} must keep session-scoped mutation paths and a dedicated tracker-baseline step. "
            f"Missing {expected!r}."
        )

    sync_body = content.split("internal void SyncTrackerCounts", 1)[1].split("internal void RecordReducerRoundTrip", 1)[0]
    assert "_trackerBaselineArmed" in sync_body and "_trackerBaselineArmed = true" not in sync_body, (
        "SyncTrackerCounts() must not arm the tracker baseline lazily on first read; connect-time baseline initialization "
        "must stay a separate step so early-session traffic is not reclassified as stale."
    )


def test_service_uses_session_bound_sinks_without_changing_public_telemetry_surface() -> None:
    service = _read(SERVICE_REL)
    client = _read(CLIENT_REL)
    stats = _read(STATS_REL)

    for expected in (
        "SessionBoundConnectionSink",
        "SessionBoundReducerEventSink",
        "_currentTransportSessionId",
        "_activeTelemetrySessionId",
        "_adapter.Open(settings, new SessionBoundConnectionSink(this, sessionId))",
        "_reducerAdapter.RegisterCallbacks(new SessionBoundReducerEventSink(this, sessionId))",
        "_telemetryCollector.InitializeTrackerBaseline(",
        "_telemetryCollector.SyncTrackerCounts(",
    ):
        assert expected in service, (
            f"{SERVICE_REL} must fence connection/reducer callbacks to the active transport session. Missing {expected!r}."
        )

    for forbidden in ("TelemetryUpdated", "ResetTelemetry", "TelemetrySessionId"):
        assert forbidden not in client and forbidden not in stats, (
            "Runtime hardening must stay internal-only and must not add new public telemetry signals or reset/session APIs. "
            f"Found forbidden token {forbidden!r}."
        )


def test_hardening_runner_artifacts_exist_and_encode_the_headless_contract() -> None:
    scene = ROOT / SCENE_REL
    runner = ROOT / RUNNER_REL
    integration = ROOT / INTEGRATION_REL
    assert scene.exists(), f"{SCENE_REL} missing under tests/godot_integration/"
    assert runner.exists(), f"{RUNNER_REL} missing under tests/godot_integration/"
    assert integration.exists(), f"{INTEGRATION_REL} must exist as the executable proof wrapper."

    runner_content = runner.read_text(encoding="utf-8")
    for expected in (
        '"session_1_started"',
        '"session_1_rates"',
        '"session_2_reset"',
        '"old_session_callbacks_ignored"',
        '"session_2_traffic"',
        '"messages_received_per_second"',
        '"messages_sent_per_second"',
        '"bytes_received_per_second"',
        '"bytes_sent_per_second"',
        '"stable_telemetry_instance_reused"',
        "ConnectionTelemetryCollector",
        "InitializeTrackerBaseline",
        "SyncTrackerCounts",
    ):
        assert expected in runner_content, (
            "The collector hardening runner must encode the step contract and collector API surface needed for the "
            f"runtime proof lane. Missing {expected!r}."
        )
