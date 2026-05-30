"""
G3/G4: Full observability parity — surface all 9 SDK NetworkRequestTrackers.

Static-contract coverage for the new public `CategoryTelemetry` surface, the 9
nested properties on `ConnectionTelemetryStats`, the SDK-isolated flatten in the
adapter, in-place reset in the collector, the four new `GodotSpacetime/Reducers/*`
Performance monitors, the pull-based (no-push) shape, and doc parity.

Mirrors the shape of `test_story_expose_per_second_telemetry_rates.py` (static
source only — the live integration lane stays in the Story 9.3 telemetry smoke).
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CATEGORY_REL = "addons/godot_spacetime/src/Public/Connection/CategoryTelemetry.cs"
STATS_REL = "addons/godot_spacetime/src/Public/Connection/ConnectionTelemetryStats.cs"
ADAPTER_REL = "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs"
COLLECTOR_REL = "addons/godot_spacetime/src/Internal/Connection/ConnectionTelemetryCollector.cs"
SERVICE_REL = "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
CLIENT_REL = "addons/godot_spacetime/src/Public/SpacetimeClient.cs"

FORBIDDEN_SDK_TOKENS = ("SpacetimeDB.", "NetworkRequestTracker", "WebSocket", "ClientMessage", "TimeSpan")

CATEGORY_SCALARS = (
    "public double MinMs",
    "public double MaxMs",
    "public double AllTimeMinMs",
    "public double AllTimeMaxMs",
    "public long SampleCount",
    "public long PendingRequests",
)

NINE_CATEGORIES = (
    "Reducers",
    "Procedures",
    "Subscriptions",
    "OneOffQueries",
    "AllReducers",
    "ParseMessageQueue",
    "ParseMessage",
    "ApplyMessageQueue",
    "ApplyMessage",
)

# The 10 locked Story-9.3 / per-second numeric fields that MUST stay byte-for-byte.
LOCKED_STATS_FIELDS = (
    "public long MessagesSent",
    "public long MessagesReceived",
    "public long BytesSent",
    "public long BytesReceived",
    "public double ConnectionUptimeSeconds",
    "public double LastReducerRoundTripMilliseconds",
    "public double MessagesReceivedPerSecond",
    "public double MessagesSentPerSecond",
    "public double BytesReceivedPerSecond",
    "public double BytesSentPerSecond",
)

NEW_MONITOR_IDS = (
    "GodotSpacetime/Reducers/LatencyMinMs",
    "GodotSpacetime/Reducers/LatencyMaxMs",
    "GodotSpacetime/Reducers/SampleCount",
    "GodotSpacetime/Reducers/PendingRequests",
)


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# AC1 (part) — CategoryTelemetry exists, carries the six scalars, no SDK tokens.
def test_category_telemetry_contract_exists_and_is_runtime_neutral() -> None:
    path = ROOT / CATEGORY_REL
    assert path.exists(), f"{CATEGORY_REL} must exist as the runtime-neutral per-tracker public shape."
    content = path.read_text(encoding="utf-8")
    assert "class CategoryTelemetry : RefCounted" in content, (
        "CategoryTelemetry must be a public RefCounted nested object."
    )
    for scalar in CATEGORY_SCALARS:
        assert f"{scalar} {{ get; internal set; }}" in content, (
            f"CategoryTelemetry must expose `{scalar} {{ get; internal set; }}` (units + 0.0 convention XML-doc'd)."
        )
    for forbidden in FORBIDDEN_SDK_TOKENS:
        assert forbidden not in content, (
            f"CategoryTelemetry must stay runtime-neutral; found forbidden token {forbidden!r} in {CATEGORY_REL}."
        )


# AC1 — ConnectionTelemetryStats declares 9 CategoryTelemetry props, keeps 10 numeric fields, no SDK tokens.
def test_connection_telemetry_stats_declares_nine_categories_and_preserves_ten_fields() -> None:
    content = _read(STATS_REL)
    for category in NINE_CATEGORIES:
        assert f"public CategoryTelemetry {category} {{ get; }}" in content, (
            f"ConnectionTelemetryStats must expose `public CategoryTelemetry {category} {{ get; }}` "
            "initialized once to new() so the instance is stable across resets."
        )
    # Each category property must be initialized inline so it is allocated exactly once.
    assert content.count("} = new();") >= len(NINE_CATEGORIES), (
        "Each of the 9 CategoryTelemetry properties must be initialized once with `= new();` at construction."
    )
    for locked in LOCKED_STATS_FIELDS:
        assert f"{locked} {{ get; internal set; }}" in content, (
            f"ConnectionTelemetryStats must preserve the locked numeric field `{locked}` byte-for-byte."
        )
    for forbidden in FORBIDDEN_SDK_TOKENS:
        assert forbidden not in content, (
            f"ConnectionTelemetryStats must stay runtime-neutral; found forbidden token {forbidden!r}."
        )


# Reconciliation guard (2026-05-29 G3/G4 live-lane capture): each per-tracker XML doc comment on
# ConnectionTelemetryStats must match the MEASURED population. ParseMessageQueue and ApplyMessageQueue
# populate from inbound traffic (NOT expected-empty); AllReducers is the one aggregate the pinned 2.1.0
# client never fills (expected-empty). Catches the comment regression shipped in b4ce0f5 and runs on every
# host. The live counterpart asserts the same distribution in test_story_9_3_connection_telemetry_integration.py.
def test_pipeline_tracker_doc_comments_match_measured_population() -> None:
    content = _read(STATS_REL)

    def _summary(prop: str) -> str:
        # Isolate exactly this property's own <summary>...</summary> block (the nearest one preceding
        # the declaration), bounded at </summary> so a neighbor's comment can never bleed in. Guarded
        # so a removed declaration/summary fails with a clear message, not an opaque ValueError.
        marker = f"public CategoryTelemetry {prop} {{ get; }}"
        assert marker in content, f"ConnectionTelemetryStats must declare `{marker}`."
        before = content[: content.index(marker)]
        start = before.rindex("<summary>")
        end = before.index("</summary>", start)
        return before[start:end].lower()

    for populated in ("ParseMessageQueue", "ApplyMessageQueue"):
        summary = _summary(populated)
        assert "expected-empty" not in summary, (
            f"{populated} populates on the pinned 2.1.0 client (measured live lane); its XML doc must not "
            "claim 'expected-empty'. See the 2026-05-29 G3/G4 live-lane reconciliation."
        )
        assert "populated" in summary, (
            f"{populated}'s XML doc must state it is populated from inbound message traffic."
        )

    assert "expected-empty" in _summary("AllReducers"), (
        "AllReducers is the one aggregate the pinned 2.1.0 client does not fill; its XML doc must keep the "
        "'expected-empty' claim so the inverse direction stays pinned."
    )


# AC1 — the adapter is the only place SDK tuples are unwrapped; flatten reads all 9 trackers.
def test_adapter_reads_all_nine_trackers_and_isolates_the_flatten() -> None:
    content = _read(ADAPTER_REL)
    for expected in (
        "TryReadCategoryTelemetry",
        "CategoryTrackerReading",
        "GetMinMaxTimes",
        "AllTimeMin",
        "AllTimeMax",
        "GetRequestsAwaitingResponse",
        "GetSampleCount",
    ):
        assert expected in content, (
            f"SpacetimeSdkConnectionAdapter must reference `{expected}` to read + flatten the 9 trackers."
        )
    # All nine reflected tracker field names must be read in the fixed order.
    for tracker_field in (
        "ReducerRequestTracker",
        "ProcedureRequestTracker",
        "SubscriptionRequestTracker",
        "OneOffRequestTracker",
        "AllReducersTracker",
        "ParseMessageQueueTracker",
        "ParseMessageTracker",
        "ApplyMessageQueueTracker",
        "ApplyMessageTracker",
    ):
        assert tracker_field in content, (
            f"Adapter must read the empirically-confirmed tracker field `{tracker_field}`."
        )
    # null-coalesce flatten to 0.0 for the latency scalars.
    assert "?? 0.0" in content, (
        "Adapter must coalesce null GetMinMaxTimes/AllTime values to 0.0 in the flatten layer."
    )


# AC6 — the service forwards the flatten output into the collector with no per-read allocation.
def test_service_wires_category_sync_on_a_preallocated_buffer() -> None:
    content = _read(SERVICE_REL)
    assert "CategoryTrackerReading[]" in content, (
        "SpacetimeConnectionService must own a preallocated CategoryTrackerReading[] buffer."
    )
    assert "TryReadCategoryTelemetry" in content and "SyncCategoryTelemetry" in content, (
        "SyncTrackerCountsForActiveSession() must read category telemetry and forward it to the collector."
    )
    sync_body = content.split("private void SyncTrackerCountsForActiveSession", 1)[1].split("private long AllocateTransportSessionId", 1)[0]
    assert "TryReadCategoryTelemetry" in sync_body and "SyncCategoryTelemetry" in sync_body, (
        "Category telemetry must refresh from inside the read-time SyncTrackerCountsForActiveSession() hook."
    )
    assert "new CategoryTrackerReading[" not in sync_body, (
        "The read-time hook must reuse the service-owned buffer, never allocate a fresh one per read."
    )


# AC4/AC5 — collector resets each category in place and keeps a single stable _stats instance.
def test_collector_resets_categories_in_place_and_keeps_single_stats_instance() -> None:
    content = _read(COLLECTOR_REL)
    assert "SyncCategoryTelemetry" in content, "Collector must expose SyncCategoryTelemetry()."
    # Re-anchor the Story 9.3 single-instance guarantee.
    assert "_stats = new();" in content and "return _stats;" in content, (
        "Collector must keep a single stable ConnectionTelemetryStats instance reused across resets."
    )
    # The reset must zero categories in place, NOT reallocate the nested objects.
    reset_body = content.split("private void ResetNoLock()", 1)[1].split("private void RefreshUptime", 1)[0]
    for scalar in ("MinMs = 0", "MaxMs = 0", "AllTimeMinMs = 0", "AllTimeMaxMs = 0", "SampleCount = 0", "PendingRequests = 0"):
        assert scalar in reset_body, (
            f"ResetNoLock() must zero each category scalar in place (`{scalar}`)."
        )
    assert "new CategoryTelemetry" not in content, (
        "The collector must never re-new the nested CategoryTelemetry objects; they are reset in place "
        "so reference identity is preserved across session resets."
    )


# AC5 — SpacetimeClient registers AND removes all four new monitor IDs under the single gated call.
def test_client_registers_and_removes_four_new_reducer_monitors() -> None:
    content = _read(CLIENT_REL)
    for monitor_id in NEW_MONITOR_IDS:
        assert monitor_id in content, f"{CLIENT_REL} must declare the `{monitor_id}` StringName constant."

    register_body = content.split("private void RegisterPerformanceMonitors()", 1)[1].split("private void RemovePerformanceMonitors", 1)[0]
    remove_body = content.split("private void RemovePerformanceMonitors()", 1)[1].split("private static void EnsurePerformanceMonitor", 1)[0]
    for const in (
        "ReducersLatencyMinMsMonitorId",
        "ReducersLatencyMaxMsMonitorId",
        "ReducersSampleCountMonitorId",
        "ReducersPendingRequestsMonitorId",
    ):
        assert const in register_body, f"RegisterPerformanceMonitors() must register `{const}`."
        assert const in remove_body, f"RemovePerformanceMonitors() must remove `{const}`."

    # The new monitors must still go through the single OwnsPerformanceMonitors()-gated call.
    enter_tree_body = content.split("public override void _EnterTree()", 1)[1].split("public override void _ExitTree", 1)[0]
    assert "if (OwnsPerformanceMonitors())" in enter_tree_body and "RegisterPerformanceMonitors()" in enter_tree_body, (
        "All monitors (including the four new Reducers/* ones) inherit the single gated registration call; "
        "a non-default ConnectionId client must register none of them."
    )

    # The existing 10 monitor IDs must remain untouched.
    for existing in (
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
    ):
        assert existing in content, f"Existing locked monitor `{existing}` must remain registered."


# AC6 — no per-frame push tokens introduced anywhere on the surface.
def test_surface_stays_pull_based_with_no_push_tokens() -> None:
    for rel in (CATEGORY_REL, STATS_REL, COLLECTOR_REL, SERVICE_REL, CLIENT_REL):
        content = _read(rel)
        for forbidden in ("CreateTimer(", "TelemetryUpdated", "PerSecondUpdated"):
            assert forbidden not in content, (
                f"G3/G4 must stay pull-based; found forbidden push token {forbidden!r} in {rel}."
            )


# Docs name the categories, units, the 0.0 convention, the 4 monitors, and reset.
def test_docs_cover_categories_units_monitors_and_reset() -> None:
    connection = _read("docs/connection.md")
    boundaries = _read("docs/runtime-boundaries.md")
    troubleshooting = _read("docs/troubleshooting.md")

    for category in NINE_CATEGORIES:
        assert category in connection, f"docs/connection.md must name the `{category}` category."
        assert category in boundaries, f"docs/runtime-boundaries.md must name the `{category}` category."

    for monitor_id in NEW_MONITOR_IDS:
        assert monitor_id in connection, f"docs/connection.md must list the `{monitor_id}` monitor."
        assert monitor_id in boundaries, f"docs/runtime-boundaries.md must list the `{monitor_id}` monitor."
        assert monitor_id in troubleshooting, f"docs/troubleshooting.md must list the `{monitor_id}` monitor."

    # Units + empty-value convention + expected-empty trackers + reset semantics.
    for term in ("milliseconds", "in flight", "0.0", "AllReducers", "ParseMessageQueue", "ApplyMessageQueue", "reset"):
        assert term in connection, f"docs/connection.md must document `{term}` for the per-category surface."
    for term in ("milliseconds", "in-flight", "expected-empty", "reset"):
        assert term in boundaries, f"docs/runtime-boundaries.md must document `{term}` for the per-category surface."
