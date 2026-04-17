"""
Spec: Expose per-second delta rates on ConnectionTelemetryStats

Static-contract coverage for the four new rate properties
(MessagesReceivedPerSecond, MessagesSentPerSecond, BytesReceivedPerSecond,
BytesSentPerSecond), the four sibling `GodotSpacetime/Connection/*PerSecond`
Performance monitors, the 1-second sliding baseline refresh logic inside
ConnectionTelemetryCollector, and the doc augmentation.

The live integration lane (Story 9.3 telemetry smoke) is covered separately
and stays skip-safe; this module is static-source-only.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STATS_REL = "addons/godot_spacetime/src/Public/Connection/ConnectionTelemetryStats.cs"
COLLECTOR_REL = "addons/godot_spacetime/src/Internal/Connection/ConnectionTelemetryCollector.cs"
CLIENT_REL = "addons/godot_spacetime/src/Public/SpacetimeClient.cs"
INTEGRATION_REL = "tests/test_story_9_3_connection_telemetry_integration.py"
RUNNER_REL = "tests/godot_integration/TelemetrySmokeRunner.cs"
CONNECTION_DOC_REL = "docs/connection.md"
BOUNDARIES_DOC_REL = "docs/runtime-boundaries.md"

NEW_RATE_PROPERTIES = (
    "MessagesReceivedPerSecond",
    "MessagesSentPerSecond",
    "BytesReceivedPerSecond",
    "BytesSentPerSecond",
)

NEW_MONITOR_IDS = (
    "GodotSpacetime/Connection/MessagesReceivedPerSecond",
    "GodotSpacetime/Connection/MessagesSentPerSecond",
    "GodotSpacetime/Connection/BytesReceivedPerSecond",
    "GodotSpacetime/Connection/BytesSentPerSecond",
)

STORY_9_3_EXISTING_STATS_FIELDS = (
    "public long MessagesSent",
    "public long MessagesReceived",
    "public long BytesSent",
    "public long BytesReceived",
    "public double ConnectionUptimeSeconds",
    "public double LastReducerRoundTripMilliseconds",
)


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# AC1 — four new rate properties exist alongside Story 9.3's six absolute fields.
def test_stats_exposes_four_per_second_properties_and_preserves_existing_fields() -> None:
    content = _read(STATS_REL)
    for prop in NEW_RATE_PROPERTIES:
        assert f"public double {prop}" in content, (
            f"{STATS_REL} must expose `public double {prop} {{ get; internal set; }}` "
            f"as a derived rate property on the public telemetry contract."
        )
    for existing in STORY_9_3_EXISTING_STATS_FIELDS:
        assert existing in content, (
            f"Story 9.3's `{existing}` contract on ConnectionTelemetryStats must stay intact "
            f"— the per-second rate spec only adds, never replaces."
        )


# AC1 — the CurrentTelemetry getter must refresh rates alongside uptime.
def test_collector_refreshes_rates_inside_current_telemetry_getter() -> None:
    content = _read(COLLECTOR_REL)
    assert "RefreshRates" in content, (
        f"{COLLECTOR_REL} must define a private `RefreshRates()` helper that advances "
        "the 1-second sliding baseline and computes the four new rate stats."
    )
    # Both Refresh helpers must be invoked in the getter — the template is one-shot,
    # but a minimum substring check guarantees they sit on the same pull-based path.
    assert "RefreshUptime" in content and "RefreshRates" in content
    getter_region = content.split("internal ConnectionTelemetryStats CurrentTelemetry", 1)
    assert len(getter_region) == 2, "CurrentTelemetry getter shape must remain intact."
    after_getter = getter_region[1].split("return _stats;", 1)[0]
    assert "RefreshUptime" in after_getter and "RefreshRates" in after_getter, (
        "`RefreshRates()` must be called alongside `RefreshUptime()` inside the CurrentTelemetry getter "
        "to keep the contract pull-based (no per-frame timers, no push signals)."
    )


# AC4 — Reset() clears baseline timestamp, counters, and rate stats.
def test_collector_reset_clears_rate_baselines_and_rate_stats() -> None:
    content = _read(COLLECTOR_REL)
    # Baseline timestamp field must be present and nullable.
    assert "_rateBaselineUtc" in content, (
        f"{COLLECTOR_REL} must declare a `_rateBaselineUtc` field (DateTimeOffset?) "
        "to anchor the 1-second sliding window."
    )
    for baseline_field in (
        "_rateBaselineMessagesReceived",
        "_rateBaselineMessagesSent",
        "_rateBaselineBytesReceived",
        "_rateBaselineBytesSent",
    ):
        assert baseline_field in content, (
            f"{COLLECTOR_REL} must declare `{baseline_field}` to snapshot the last-baseline counter value."
        )

    # Reset() body must zero out rate stats AND clear the baseline timestamp.
    reset_marker = "internal void Reset()"
    assert reset_marker in content, "Reset() signature must remain intact."
    reset_body = content.split(reset_marker, 1)[1].split("}", 1)[0]
    assert "_rateBaselineUtc = null" in reset_body, (
        "Reset() must null out `_rateBaselineUtc` so the next session re-arms the baseline fresh."
    )
    for prop in NEW_RATE_PROPERTIES:
        assert f"_stats.{prop} = 0" in reset_body, (
            f"Reset() must zero `_stats.{prop}` so a pre-reconnect read returns 0.0 immediately."
        )


# AC2 — all ten monitor IDs live on SpacetimeClient, registered and removed symmetrically.
def test_client_registers_and_removes_all_ten_monitors() -> None:
    content = _read(CLIENT_REL)
    existing = (
        "GodotSpacetime/Connection/MessagesSent",
        "GodotSpacetime/Connection/MessagesReceived",
        "GodotSpacetime/Connection/BytesSent",
        "GodotSpacetime/Connection/BytesReceived",
        "GodotSpacetime/Connection/UptimeSeconds",
        "GodotSpacetime/Reducers/LastRoundTripMilliseconds",
    )
    for monitor_id in existing + NEW_MONITOR_IDS:
        assert monitor_id in content, (
            f"{CLIENT_REL} must declare the `{monitor_id}` StringName constant."
        )

    # Every new monitor must appear in both register and remove paths.
    register_marker = "private void RegisterPerformanceMonitors()"
    remove_marker = "private void RemovePerformanceMonitors()"
    assert register_marker in content and remove_marker in content
    register_body = content.split(register_marker, 1)[1].split("private void RemovePerformanceMonitors", 1)[0]
    remove_body = content.split(remove_marker, 1)[1].split("private static void EnsurePerformanceMonitor", 1)[0]
    for prop in NEW_RATE_PROPERTIES:
        monitor_const = f"{prop}MonitorId"
        assert monitor_const in register_body, (
            f"RegisterPerformanceMonitors() must register `{monitor_const}`."
        )
        assert monitor_const in remove_body, (
            f"RemovePerformanceMonitors() must remove `{monitor_const}`."
        )


# AC3 — new monitor registrations must respect OwnsPerformanceMonitors() gating.
def test_new_monitor_registrations_are_gated_by_owns_performance_monitors() -> None:
    content = _read(CLIENT_REL)
    enter_tree_marker = "public override void _EnterTree()"
    assert enter_tree_marker in content
    enter_tree_body = content.split(enter_tree_marker, 1)[1].split("public override void _ExitTree", 1)[0]
    # The single RegisterPerformanceMonitors() call in _EnterTree() must stay wrapped
    # in the OwnsPerformanceMonitors() conditional — that's how non-default clients
    # skip all ten monitors (the four new ones inherit gating via RegisterPerformanceMonitors).
    assert "if (OwnsPerformanceMonitors())" in enter_tree_body and "RegisterPerformanceMonitors()" in enter_tree_body, (
        "All ten monitors (six existing + four new) register through the single gated "
        "`if (OwnsPerformanceMonitors()) RegisterPerformanceMonitors();` call; a non-default "
        "ConnectionId client must not get any of the four new monitors."
    )


# AC2 — integration lane EXPECTED_MONITOR_IDS + runner dict both grow to 10.
def test_integration_expected_monitor_ids_and_runner_dict_include_new_ids() -> None:
    integration_content = _read(INTEGRATION_REL)
    runner_content = _read(RUNNER_REL)
    for monitor_id in NEW_MONITOR_IDS:
        assert monitor_id in integration_content, (
            f"{INTEGRATION_REL} must include `{monitor_id}` in EXPECTED_MONITOR_IDS "
            "so the integration comparison keeps parity with the registered set."
        )
        assert monitor_id in runner_content, (
            f"{RUNNER_REL} must read `{monitor_id}` via ReadMonitor so the runner's "
            "PerformanceMonitors dict keys match EXPECTED_MONITOR_IDS."
        )


# AC5 — docs contain both property names and monitor IDs.
def test_connection_doc_mentions_new_properties_and_monitor_ids() -> None:
    content = _read(CONNECTION_DOC_REL)
    for prop in NEW_RATE_PROPERTIES:
        assert prop in content, f"{CONNECTION_DOC_REL} must name `{prop}` in the telemetry section."
    for monitor_id in NEW_MONITOR_IDS:
        assert monitor_id in content, f"{CONNECTION_DOC_REL} must list the `{monitor_id}` monitor ID."
    # Story 9.3's locked tokens must stay intact.
    for locked in ("CurrentTelemetry", "MessagesSent", "BytesSent", "UptimeSeconds", "milliseconds", "reset"):
        assert locked in content, f"Story 9.3 locked token `{locked}` must remain in {CONNECTION_DOC_REL}."


def test_runtime_boundaries_doc_mentions_new_properties_and_monitor_ids() -> None:
    content = _read(BOUNDARIES_DOC_REL)
    for prop in NEW_RATE_PROPERTIES:
        assert prop in content, f"{BOUNDARIES_DOC_REL} must name `{prop}` in the ConnectionTelemetryStats concept documentation."
    for monitor_id in NEW_MONITOR_IDS:
        assert monitor_id in content, f"{BOUNDARIES_DOC_REL} must list the `{monitor_id}` monitor ID."
    for locked in ("CurrentTelemetry", "MessagesSent", "MessagesReceived", "BytesSent", "BytesReceived", "GodotSpacetime/Connection/MessagesSent"):
        assert locked in content, f"Story 9.3 locked token `{locked}` must remain in {BOUNDARIES_DOC_REL}."


# Negative guard — the spec explicitly forbids per-frame/push tokens on the collector/client.
def test_spec_remains_pull_based_with_no_new_push_tokens() -> None:
    for rel in (COLLECTOR_REL, CLIENT_REL, STATS_REL):
        content = _read(rel)
        for forbidden in (
            "TelemetryRateUpdated",
            "PerSecondUpdated",
            "CreateTimer(",
        ):
            assert forbidden not in content, (
                f"Per-second rate spec must stay pull-based. `{forbidden}` in {rel} would introduce "
                "the push-based shape Story 9.3 explicitly locked out."
            )
