"""
Story 9.3: Expose Connection Telemetry and Performance Metrics

Static contract coverage for the public telemetry surface, Godot Performance
monitor lifecycle, disconnect/reset semantics, and regression anchors from
Stories 1.9, 4.2, 9.1, and 9.2.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_connection_telemetry_stats_contract_exists() -> None:
    rel = "addons/godot_spacetime/src/Public/Connection/ConnectionTelemetryStats.cs"
    path = ROOT / rel
    assert path.exists(), (
        f"{rel} must exist as the public typed telemetry contract before Story 9.3 can ship "
        "(Task 1.1, AC1/AC2/AC5)."
    )

    content = path.read_text(encoding="utf-8")
    for expected in (
        "class ConnectionTelemetryStats",
        "public long MessagesSent",
        "public long MessagesReceived",
        "public long BytesSent",
        "public long BytesReceived",
        "public double ConnectionUptimeSeconds",
        "public double LastReducerRoundTripMilliseconds",
    ):
        assert expected in content, (
            "ConnectionTelemetryStats must expose the runtime-neutral numeric metrics promised by Story 9.3. "
            f"Missing {expected!r} (Task 1.1, AC1/AC2)."
        )
    for forbidden in ("SpacetimeDB.", "NetworkRequestTracker", "WebSocket", "ClientMessage"):
        assert forbidden not in content, (
            "The public telemetry contract must stay runtime-neutral and must not expose SDK transport types. "
            f"Found forbidden token {forbidden!r} in {rel} (Task 1.3)."
        )


def test_spacetime_client_exposes_pull_based_current_telemetry_and_monitor_ids() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "CurrentTelemetry" in content and "ConnectionTelemetryStats" in content, (
        "SpacetimeClient must expose a typed pull-based telemetry property on the Godot-facing service boundary "
        "without stuffing high-churn counters into ConnectionStatus (Task 1.2, AC1/AC2)."
    )
    for expected in (
        "GodotSpacetime/Connection/MessagesSent",
        "GodotSpacetime/Connection/MessagesReceived",
        "GodotSpacetime/Connection/BytesSent",
        "GodotSpacetime/Connection/BytesReceived",
        "GodotSpacetime/Connection/UptimeSeconds",
        "GodotSpacetime/Reducers/LastRoundTripMilliseconds",
        "Performance.HasCustomMonitor",
        "Performance.AddCustomMonitor",
        "Performance.GetCustomMonitor",
        "Performance.RemoveCustomMonitor",
    ):
        assert expected in content, (
            "SpacetimeClient must own the stable Godot Performance monitor lifecycle with the Story 9.3 IDs. "
            f"Missing {expected!r} (Task 3.1, Task 3.2, Task 3.3, AC3)."
        )


def test_service_and_adapter_keep_telemetry_collection_internal_and_resettable() -> None:
    collector_rel = "addons/godot_spacetime/src/Internal/Connection/ConnectionTelemetryCollector.cs"
    serializer_rel = "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkTelemetrySerializer.cs"
    collector_path = ROOT / collector_rel
    assert collector_path.exists(), (
        f"{collector_rel} must exist as the internal telemetry state owner attached to "
        "SpacetimeConnectionService (Task 2.1, AC1/AC4/AC5)."
    )
    serializer_path = ROOT / serializer_rel
    assert serializer_path.exists(), (
        f"{serializer_rel} must exist in Internal/Platform/DotNet/ so outbound byte proof stays inside the "
        ".NET isolation zone (Task 2.3, Task 2.6, Task 5.3)."
    )

    service = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    adapter = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    collector = collector_path.read_text(encoding="utf-8")
    serializer = serializer_path.read_text(encoding="utf-8")

    for expected in (
        "ConnectionTelemetryCollector",
        "CurrentTelemetry",
        "Reset",
        "SessionBoundConnectionSink",
        "SessionBoundReducerEventSink",
        "InitializeTrackerBaseline",
        "TryReadTrackerCounts",
    ):
        assert expected in service or expected in collector, (
            "Telemetry lifecycle must be owned by SpacetimeConnectionService and reset on disconnect/reconnect. "
            f"Missing {expected!r} across the service/collector pair (Task 2.1, Task 2.7, AC5)."
        )

    for expected in ("OnMessage", "DbConnectionBase", "stats", "NetworkRequestTracker"):
        assert expected in adapter, (
            "The .NET isolation zone must contain the supported-stack hooks for inbound traffic, request tracking, "
            f"and any outbound-byte proof path. Missing {expected!r} in the adapter (Task 2.3, Task 2.4, Task 2.5)."
        )

    for expected in ("ClientMessage", "ClientMessage.BSATN", "MeasureReducerPayloadBytes", "MeasureSubscribePayloadBytes"):
        assert expected in serializer, (
            "Outbound byte proof must remain inside Internal/Platform/DotNet/ and must be anchored to the pinned SDK's "
            f"real ClientMessage serializer path. Missing {expected!r} in {serializer_rel} (Task 2.6, Task 5.3, Task 6.6)."
        )


def test_public_surface_avoids_per_frame_telemetry_signals_and_snapshot_churn() -> None:
    client = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    service = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    collector = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionTelemetryCollector.cs")

    for forbidden in (
        "TelemetryUpdatedEventHandler",
        "TelemetryUpdated",
        "CreateTimer(",
    ):
        assert forbidden not in client and forbidden not in service and forbidden not in collector, (
            "Story 9.3 must stay pull-based and allocation-light. "
            f"Found forbidden per-frame/push token {forbidden!r} (Task 2.8, Task 3.4, AC4)."
        )

    assert "_stats = new();" in collector and "return _stats;" in collector, (
        "Story 9.3 must keep a single stable ConnectionTelemetryStats instance inside the collector and "
        "reuse it across session resets instead of allocating snapshots on demand (Task 1.4, AC4/AC5)."
    )
    assert "new ConnectionTelemetryStats" not in client and "new ConnectionTelemetryStats" not in service, (
        "SpacetimeClient and SpacetimeConnectionService must not allocate fresh telemetry snapshots during reads; "
        "the collector-owned stats object is the stable session boundary (Task 1.4, Task 2.8, AC4/AC5)."
    )


def test_docs_cover_telemetry_property_monitor_ids_units_and_reset_semantics() -> None:
    docs = {
        "docs/runtime-boundaries.md": (
            "CurrentTelemetry",
            "MessagesSent",
            "MessagesReceived",
            "BytesSent",
            "BytesReceived",
            "ConnectionUptimeSeconds",
            "LastReducerRoundTripMilliseconds",
            "GodotSpacetime/Connection/MessagesSent",
            "disconnect",
            "reconnect",
        ),
        "docs/connection.md": (
            "CurrentTelemetry",
            "GodotSpacetime/Connection/MessagesSent",
            "UptimeSeconds",
            "milliseconds",
            "reset",
        ),
        "docs/troubleshooting.md": (
            "CurrentTelemetry",
            "Performance",
            "monitor",
            "reset",
            "runtime proof",
        ),
        "docs/quickstart.md": (
            "CurrentTelemetry",
            "Performance",
            "GodotSpacetime/Connection/MessagesSent",
        ),
        "demo/README.md": (
            "CurrentTelemetry",
            "Performance",
            "LastReducerRoundTripMilliseconds",
        ),
    }
    for rel, expected_terms in docs.items():
        content = _read(rel)
        for expected in expected_terms:
            assert expected in content, (
                f"{rel} must document {expected!r} for Story 9.3 (Task 4.1, Task 4.2, Task 4.3, AC2/AC3/AC5)."
            )


def test_outbound_byte_tracking_requires_a_real_supported_path_not_a_placeholder() -> None:
    serializer = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkTelemetrySerializer.cs")
    assert "ClientMessage.BSATN" in serializer and "MeasureClientMessageBytes" in serializer, (
        "Story 9.3 must anchor outbound byte totals to the pinned SDK's ClientMessage serializer path inside "
        "Internal/Platform/DotNet/ (Task 2.6, Task 5.3, Task 6.6)."
    )
    for forbidden in (
        "BytesSent = 0",
        "MessagesSent *",
        "BytesSent += 1",
        "placeholder",
        "TODO fake bytes",
    ):
        assert forbidden not in serializer, (
            "Outbound byte counting must fail loudly rather than shipping an invented value. "
            f"Found suspicious token {forbidden!r} in the serializer path (Task 0.4, Task 2.6, Task 6.6)."
        )


def test_story_9_1_9_2_1_9_and_4_2_regression_anchors_remain_intact() -> None:
    connection_status = _read("addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs")
    reducer_result = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    reducer_error = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    adapter = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    settings = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")

    assert "ActiveCompressionMode" in connection_status, (
        "Story 9.3 must preserve Story 9.1's effective compression status surface."
    )
    assert "LightMode" in settings, (
        "Story 9.3 must preserve Story 9.2's LightMode setting surface."
    )
    assert "public DateTimeOffset CalledAt { get; }" in reducer_result
    assert "public DateTimeOffset CompletedAt { get; }" in reducer_result
    assert "public DateTimeOffset CalledAt { get; }" in reducer_error
    assert "public DateTimeOffset FailedAt { get; }" in reducer_error
    assert 'builder = InvokeMethod(builder, "WithCompression", MapCompressionMode(settings.CompressionMode));' in adapter
