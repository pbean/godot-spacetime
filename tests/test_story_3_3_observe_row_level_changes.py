"""
Story 3.3: Observe Row-Level Changes for Subscribed Data
Automated contract tests for all story deliverables.

Covers:
- RowChangeType.cs: file existence, namespace, enum values, isolation (AC: 2)
- RowChangedEvent.cs: file existence, namespace, class, properties, constructor, isolation (AC: 1, 2, 3)
- SpacetimeSdkRowCallbackAdapter.cs: file existence, namespace, interface, class, methods, expression trees (AC: 1, 2, 3)
- Generated RemoteTables sample: field-backed table handle shape used by the current SpacetimeDB generator
- SpacetimeConnectionService.cs: _rowCallbackAdapter field, IRowChangeEventSink impl, OnRowChanged event,
  RegisterCallbacks call, explicit interface methods, isolation (AC: 1, 2, 3)
- SpacetimeClient.cs: RowChangedEventHandler signal, HandleRowChanged handler, wiring, isolation (AC: 1, 2, 3)
- docs/runtime-boundaries.md: RowChanged, RowChangedEvent, RowChangeType, OldRow, NewRow, TableName,
  cast example, SubscriptionApplied reference, SpacetimeSdkRowCallbackAdapter reference (AC: 1, 2, 3)
- Regression guards: prior story deliverables must still pass
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# RowChangeType.cs — file existence and content (AC: 2)
# ---------------------------------------------------------------------------

def test_row_change_type_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Subscriptions/RowChangeType.cs"
    assert path.exists(), (
        "RowChangeType.cs must exist at Public/Subscriptions/RowChangeType.cs (AC 2)"
    )


def test_row_change_type_namespace_is_godot_spacetime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangeType.cs")
    assert "namespace GodotSpacetime.Subscriptions" in content, (
        "RowChangeType.cs must use namespace GodotSpacetime.Subscriptions (AC 2)"
    )


def test_row_change_type_is_public_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangeType.cs")
    assert "public enum RowChangeType" in content, (
        "RowChangeType.cs must declare 'public enum RowChangeType' (AC 2)"
    )


def test_row_change_type_has_insert_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangeType.cs")
    assert "Insert" in content, (
        "RowChangeType must contain 'Insert' value (AC 2)"
    )


def test_row_change_type_has_update_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangeType.cs")
    assert "Update" in content, (
        "RowChangeType must contain 'Update' value (AC 2)"
    )


def test_row_change_type_has_delete_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangeType.cs")
    assert "Delete" in content, (
        "RowChangeType must contain 'Delete' value (AC 2)"
    )


def test_row_change_type_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangeType.cs")
    assert "SpacetimeDB." not in content, (
        "RowChangeType.cs must NOT reference SpacetimeDB.* — public contract must stay runtime-neutral (AC 2)"
    )


# ---------------------------------------------------------------------------
# RowChangedEvent.cs — file existence and content (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_row_changed_event_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs"
    assert path.exists(), (
        "RowChangedEvent.cs must exist at Public/Subscriptions/RowChangedEvent.cs (AC 1, 2, 3)"
    )


def test_row_changed_event_namespace_is_godot_spacetime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "namespace GodotSpacetime.Subscriptions" in content, (
        "RowChangedEvent.cs must use namespace GodotSpacetime.Subscriptions (AC 1, 2, 3)"
    )


def test_row_changed_event_is_public_partial_class_ref_counted() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "public partial class RowChangedEvent : RefCounted" in content, (
        "RowChangedEvent.cs must declare 'public partial class RowChangedEvent : RefCounted' (AC 1, 2, 3)"
    )


def test_row_changed_event_has_table_name_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "TableName" in content, (
        "RowChangedEvent.cs must have TableName property (AC 1)"
    )


def test_row_changed_event_has_change_type_property_of_row_change_type() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "RowChangeType ChangeType" in content, (
        "RowChangedEvent.cs must have 'RowChangeType ChangeType' property (AC 2)"
    )


def test_row_changed_event_has_old_row_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "OldRow" in content, (
        "RowChangedEvent.cs must have OldRow property (AC 2)"
    )


def test_row_changed_event_has_new_row_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "NewRow" in content, (
        "RowChangedEvent.cs must have NewRow property (AC 2)"
    )


def test_row_changed_event_has_internal_constructor() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "internal RowChangedEvent(" in content, (
        "RowChangedEvent.cs must have 'internal RowChangedEvent(' constructor (AC 3)"
    )


def test_row_changed_event_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "SpacetimeDB." not in content, (
        "RowChangedEvent.cs must NOT reference SpacetimeDB.* — public contract must stay runtime-neutral (AC 3)"
    )


# ---------------------------------------------------------------------------
# SpacetimeSdkRowCallbackAdapter.cs — file existence and content (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_row_callback_adapter_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs"
    assert path.exists(), (
        "SpacetimeSdkRowCallbackAdapter.cs must exist at Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs (AC 1, 2, 3)"
    )


def test_row_callback_adapter_namespace_is_godot_spacetime_runtime_platform_dotnet() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "namespace GodotSpacetime.Runtime.Platform.DotNet" in content, (
        "SpacetimeSdkRowCallbackAdapter.cs must use namespace GodotSpacetime.Runtime.Platform.DotNet (AC 1)"
    )


def test_row_callback_adapter_has_row_change_event_sink_interface() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "internal interface IRowChangeEventSink" in content, (
        "SpacetimeSdkRowCallbackAdapter.cs must define 'internal interface IRowChangeEventSink' (AC 1, 2, 3)"
    )


def test_row_callback_adapter_interface_has_on_row_inserted() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "OnRowInserted" in content, (
        "IRowChangeEventSink must have OnRowInserted method (AC 1)"
    )


def test_row_callback_adapter_interface_has_on_row_deleted() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "OnRowDeleted" in content, (
        "IRowChangeEventSink must have OnRowDeleted method (AC 1)"
    )


def test_row_callback_adapter_interface_has_on_row_updated() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "OnRowUpdated" in content, (
        "IRowChangeEventSink must have OnRowUpdated method (AC 1)"
    )


def test_row_callback_adapter_is_internal_sealed_class() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "internal sealed class SpacetimeSdkRowCallbackAdapter" in content, (
        "SpacetimeSdkRowCallbackAdapter.cs must declare 'internal sealed class SpacetimeSdkRowCallbackAdapter' (AC 1)"
    )


def test_row_callback_adapter_has_register_callbacks_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "RegisterCallbacks" in content, (
        "SpacetimeSdkRowCallbackAdapter must have RegisterCallbacks method (AC 1)"
    )


def test_row_callback_adapter_uses_expression_lambda() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "Expression.Lambda" in content, (
        "SpacetimeSdkRowCallbackAdapter must use Expression.Lambda (reflection + expression trees pattern) (AC 1)"
    )


def test_row_callback_adapter_uses_add_event_handler() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "AddEventHandler" in content, (
        "SpacetimeSdkRowCallbackAdapter must use AddEventHandler to wire SDK events (AC 1)"
    )


def test_row_callback_adapter_uses_spacetimedb_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "using SpacetimeDB;" in content, (
        "SpacetimeSdkRowCallbackAdapter.cs must have 'using SpacetimeDB;' — allowed in Platform/DotNet isolation zone (AC 1)"
    )


def test_row_callback_adapter_wires_on_insert() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "OnInsert" in content, (
        "SpacetimeSdkRowCallbackAdapter must wire OnInsert event (AC 1)"
    )


def test_row_callback_adapter_wires_on_delete() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "OnDelete" in content, (
        "SpacetimeSdkRowCallbackAdapter must wire OnDelete event (AC 1)"
    )


def test_row_callback_adapter_wires_on_update() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "OnUpdate" in content, (
        "SpacetimeSdkRowCallbackAdapter must wire OnUpdate event (AC 1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — _rowCallbackAdapter, IRowChangeEventSink, OnRowChanged (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_connection_service_has_row_callback_adapter_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_rowCallbackAdapter" in content, (
        "SpacetimeConnectionService.cs must declare _rowCallbackAdapter field (AC 1, 2, 3)"
    )


def test_connection_service_references_spacetime_sdk_row_callback_adapter_type() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "SpacetimeSdkRowCallbackAdapter" in content, (
        "SpacetimeConnectionService.cs must reference SpacetimeSdkRowCallbackAdapter type (AC 1)"
    )


def test_connection_service_implements_row_change_event_sink() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IRowChangeEventSink" in content, (
        "SpacetimeConnectionService class declaration must include IRowChangeEventSink (AC 1, 2, 3)"
    )


def test_connection_service_has_on_row_changed_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnRowChanged" in content, (
        "SpacetimeConnectionService.cs must have OnRowChanged event (AC 1)"
    )


def test_connection_service_calls_register_callbacks() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RegisterCallbacks" in content, (
        "SpacetimeConnectionService.cs must call RegisterCallbacks (AC 1)"
    )


def test_connection_service_has_on_row_inserted_implementation() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IRowChangeEventSink.OnRowInserted" in content, (
        "SpacetimeConnectionService.cs must have explicit IRowChangeEventSink.OnRowInserted implementation (AC 1)"
    )


def test_connection_service_has_on_row_deleted_implementation() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IRowChangeEventSink.OnRowDeleted" in content, (
        "SpacetimeConnectionService.cs must have explicit IRowChangeEventSink.OnRowDeleted implementation (AC 1)"
    )


def test_connection_service_has_on_row_updated_implementation() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IRowChangeEventSink.OnRowUpdated" in content, (
        "SpacetimeConnectionService.cs must have explicit IRowChangeEventSink.OnRowUpdated implementation (AC 1)"
    )


def test_connection_service_references_row_change_type_insert() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RowChangeType.Insert" in content, (
        "SpacetimeConnectionService.cs must reference RowChangeType.Insert (AC 2)"
    )


def test_connection_service_references_row_change_type_delete() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RowChangeType.Delete" in content, (
        "SpacetimeConnectionService.cs must reference RowChangeType.Delete (AC 2)"
    )


def test_connection_service_references_row_change_type_update() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RowChangeType.Update" in content, (
        "SpacetimeConnectionService.cs must reference RowChangeType.Update (AC 2)"
    )


def test_connection_service_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "SpacetimeDB." not in content, (
        "SpacetimeConnectionService.cs must NOT reference SpacetimeDB.* (isolation boundary, AC 2, 3)"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.cs — RowChangedEventHandler signal, HandleRowChanged, wiring (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_row_changed_event_handler_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "RowChangedEventHandler" in content, (
        "SpacetimeClient.cs must have RowChangedEventHandler delegate declaration (AC 1)"
    )


def test_spacetime_client_row_changed_event_handler_has_signal_attribute() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "RowChangedEventHandler" in line:
            # Check that [Signal] appears above the delegate
            preceding = "\n".join(lines[max(0, i - 3):i])
            assert "[Signal]" in preceding, (
                "RowChangedEventHandler must be preceded by [Signal] attribute (AC 1)"
            )
            break


def test_spacetime_client_wires_on_row_changed() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "OnRowChanged += HandleRowChanged" in content, (
        "SpacetimeClient.cs must wire OnRowChanged += HandleRowChanged in _EnterTree (AC 1)"
    )


def test_spacetime_client_unwires_on_row_changed() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "OnRowChanged -= HandleRowChanged" in content, (
        "SpacetimeClient.cs must unwire OnRowChanged -= HandleRowChanged in _ExitTree (AC 1)"
    )


def test_spacetime_client_has_handle_row_changed_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleRowChanged" in content, (
        "SpacetimeClient.cs must have HandleRowChanged method (AC 1)"
    )


def test_spacetime_client_emits_row_changed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "EmitSignal(SignalName.RowChanged" in content, (
        "SpacetimeClient.cs must call EmitSignal(SignalName.RowChanged, ...) in HandleRowChanged (AC 1)"
    )


def test_spacetime_client_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SpacetimeDB." not in content, (
        "SpacetimeClient.cs must NOT reference SpacetimeDB.* (isolation boundary, AC 2, 3)"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md — Row Changes section (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_references_row_changed() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "RowChanged" in content, (
        "docs/runtime-boundaries.md must reference RowChanged signal (AC 1)"
    )


def test_runtime_boundaries_references_row_changed_event() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "RowChangedEvent" in content, (
        "docs/runtime-boundaries.md must reference RowChangedEvent (AC 1, 2, 3)"
    )


def test_runtime_boundaries_references_row_change_type() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "RowChangeType" in content, (
        "docs/runtime-boundaries.md must reference RowChangeType (AC 2)"
    )


def test_runtime_boundaries_references_old_row() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "OldRow" in content, (
        "docs/runtime-boundaries.md must reference OldRow property (AC 2)"
    )


def test_runtime_boundaries_references_new_row() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "NewRow" in content, (
        "docs/runtime-boundaries.md must reference NewRow property (AC 2)"
    )


def test_runtime_boundaries_references_table_name() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "TableName" in content, (
        "docs/runtime-boundaries.md must reference TableName property (AC 1)"
    )


def test_runtime_boundaries_has_cast_example_for_row_changes() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "(SpacetimeDB.Types." in content, (
        "docs/runtime-boundaries.md must show a cast example (e.g. '(SpacetimeDB.Types.') for row change events (AC 1)"
    )


def test_runtime_boundaries_references_subscription_applied_for_timing() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "SubscriptionApplied" in content, (
        "docs/runtime-boundaries.md must reference SubscriptionApplied for timing context (AC 1)"
    )


def test_runtime_boundaries_references_spacetime_sdk_row_callback_adapter() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "SpacetimeSdkRowCallbackAdapter" in content, (
        "docs/runtime-boundaries.md must reference SpacetimeSdkRowCallbackAdapter (AC 3)"
    )


# ---------------------------------------------------------------------------
# Regression guards — prior story deliverables must still pass
# ---------------------------------------------------------------------------

def test_connection_adapter_still_has_connection_property() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "Connection" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have Connection property (regression guard)"
    )


def test_connection_adapter_still_has_get_db_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "GetDb" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have GetDb() method (Story 3.2 regression guard)"
    )


def test_connection_adapter_still_has_open_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "Open" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have Open method (regression guard)"
    )


def test_connection_adapter_still_has_frame_tick() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "FrameTick" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have FrameTick method (regression guard)"
    )


def test_connection_adapter_still_has_close_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "Close" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have Close method (regression guard)"
    )


def test_subscription_adapter_still_has_subscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "Subscribe" in content, (
        "SpacetimeSdkSubscriptionAdapter.cs must still have Subscribe method (regression guard)"
    )


def test_subscription_adapter_still_has_subscription_event_sink_interface() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "ISubscriptionEventSink" in content, (
        "SpacetimeSdkSubscriptionAdapter.cs must still have ISubscriptionEventSink interface (regression guard)"
    )


def test_connection_service_still_has_subscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Subscribe" in content, (
        "SpacetimeConnectionService.cs must still have Subscribe method (regression guard)"
    )


def test_connection_service_still_has_on_subscription_applied() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnSubscriptionApplied" in content, (
        "SpacetimeConnectionService.cs must still have OnSubscriptionApplied event (regression guard)"
    )


def test_connection_service_still_has_subscription_registry() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionRegistry" in content, (
        "SpacetimeConnectionService.cs must still have _subscriptionRegistry field (regression guard)"
    )


def test_connection_service_still_has_cache_view_adapter() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_cacheViewAdapter" in content, (
        "SpacetimeConnectionService.cs must still have _cacheViewAdapter field (Story 3.2 regression guard)"
    )


def test_connection_service_still_has_get_rows_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "GetRows" in content, (
        "SpacetimeConnectionService.cs must still have GetRows method (Story 3.2 regression guard)"
    )


def test_connection_service_still_clears_subscription_registry_on_disconnect() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionRegistry.Clear()" in content, (
        "SpacetimeConnectionService.cs must still call _subscriptionRegistry.Clear() in ResetDisconnectedSessionState (regression guard)"
    )


def test_spacetime_client_still_has_subscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public SubscriptionHandle Subscribe(" in content, (
        "SpacetimeClient.cs must still have public Subscribe method (regression guard)"
    )


def test_spacetime_client_still_has_subscription_applied_event_handler() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionAppliedEventHandler" in content, (
        "SpacetimeClient.cs must still have SubscriptionAppliedEventHandler signal delegate (regression guard)"
    )


def test_spacetime_client_still_has_handle_subscription_applied() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleSubscriptionApplied" in content, (
        "SpacetimeClient.cs must still have HandleSubscriptionApplied handler (regression guard)"
    )


def test_spacetime_client_still_has_connection_state_changed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionStateChanged" in content, (
        "SpacetimeClient.cs must still have ConnectionStateChanged signal (regression guard)"
    )


def test_spacetime_client_still_has_connection_opened_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionOpenedEventHandler" in content, (
        "SpacetimeClient.cs must still have ConnectionOpenedEventHandler signal (regression guard)"
    )


def test_spacetime_client_still_has_get_rows_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "GetRows" in content, (
        "SpacetimeClient.cs must still have GetRows method (Story 3.2 regression guard)"
    )


def test_subscription_registry_still_has_register_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "Register" in content, (
        "SubscriptionRegistry.cs must still have Register method (regression guard)"
    )


def test_subscription_registry_still_has_unregister_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "Unregister" in content, (
        "SubscriptionRegistry.cs must still have Unregister method (regression guard)"
    )


def test_subscription_registry_still_has_clear_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "Clear" in content, (
        "SubscriptionRegistry.cs must still have Clear method (regression guard)"
    )


def test_subscription_registry_still_has_active_handles_property() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "ActiveHandles" in content, (
        "SubscriptionRegistry.cs must still have ActiveHandles property (regression guard)"
    )


def test_cache_view_adapter_still_has_set_db() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "SetDb" in content, (
        "CacheViewAdapter.cs must still have SetDb method (Story 3.2 regression guard)"
    )


def test_cache_view_adapter_still_has_get_rows() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "GetRows" in content, (
        "CacheViewAdapter.cs must still have GetRows method (Story 3.2 regression guard)"
    )


def test_runtime_boundaries_still_has_get_rows_reference() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "GetRows(" in content, (
        "docs/runtime-boundaries.md must still reference GetRows() (Story 3.2 regression guard)"
    )


def test_runtime_boundaries_still_has_handle_id_reference() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "HandleId" in content, (
        "docs/runtime-boundaries.md must still reference HandleId (regression guard)"
    )


def test_runtime_boundaries_still_has_applied_at_reference() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "AppliedAt" in content, (
        "docs/runtime-boundaries.md must still reference AppliedAt (regression guard)"
    )


def test_runtime_boundaries_still_has_cache_view_adapter_reference() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "CacheViewAdapter" in content, (
        "docs/runtime-boundaries.md must still reference CacheViewAdapter (Story 3.2 regression guard)"
    )


# ---------------------------------------------------------------------------
# Gap-fill: RowChangedEvent.cs — readonly properties and nullable types (AC: 2)
# ---------------------------------------------------------------------------

def test_row_changed_event_table_name_is_get_only_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "string TableName { get; }" in content, (
        "TableName must be a get-only property with no setter (AC 2)"
    )


def test_row_changed_event_old_row_is_nullable_object() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "object? OldRow" in content, (
        "OldRow must be declared as nullable object — null for Insert events (AC 2)"
    )


def test_row_changed_event_new_row_is_nullable_object() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    assert "object? NewRow" in content, (
        "NewRow must be declared as nullable object — null for Delete events (AC 2)"
    )


# ---------------------------------------------------------------------------
# Gap-fill: SpacetimeSdkRowCallbackAdapter.cs — imports, guards, helpers (AC: 1)
# ---------------------------------------------------------------------------

def test_row_callback_adapter_imports_system_reflection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "using System.Reflection;" in content, (
        "SpacetimeSdkRowCallbackAdapter.cs must import System.Reflection for runtime property discovery (AC 1)"
    )


def test_row_callback_adapter_imports_linq_expressions() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "using System.Linq.Expressions;" in content, (
        "SpacetimeSdkRowCallbackAdapter.cs must import System.Linq.Expressions for delegate synthesis (AC 1)"
    )


def test_row_callback_adapter_null_guards_arguments() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "ArgumentNullException.ThrowIfNull" in content, (
        "RegisterCallbacks must guard against null db and sink via ArgumentNullException.ThrowIfNull (AC 1)"
    )


def test_row_callback_adapter_uses_public_instance_binding_flags() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "BindingFlags.Public | BindingFlags.Instance" in content, (
        "SpacetimeSdkRowCallbackAdapter must enumerate table handles with BindingFlags.Public | BindingFlags.Instance (AC 1)"
    )


def test_row_callback_adapter_reads_public_fields_from_remote_tables() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "GetFields(BindingFlags.Public | BindingFlags.Instance)" in content, (
        "SpacetimeSdkRowCallbackAdapter must inspect public instance fields because generated RemoteTables "
        "exposes table handles as fields in the current SpacetimeDB generator (AC 1)"
    )


def test_row_callback_adapter_keeps_property_support_for_future_generator_shapes() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "GetProperties(BindingFlags.Public | BindingFlags.Instance)" in content, (
        "SpacetimeSdkRowCallbackAdapter must keep public instance property support so future generator "
        "shape changes do not break callback wiring (AC 1)"
    )


def test_row_callback_adapter_tracks_registered_db_instances_to_avoid_duplicate_wiring() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "ConditionalWeakTable<object, RegistrationMarker>" in content and "_registeredDbs" in content, (
        "SpacetimeSdkRowCallbackAdapter must track previously wired db instances so reconnect recovery "
        "does not register duplicate row callbacks on the same RemoteTables object (AC 1)"
    )


def test_row_callback_adapter_short_circuits_when_same_db_is_registered_twice() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "TryGetValue(db, out _)" in content and "_registeredDbs.Add(db, new RegistrationMarker())" in content, (
        "RegisterCallbacks must detect when the same db object is passed again and avoid duplicate event "
        "registration across reconnect recovery (AC 1)"
    )


def test_row_callback_adapter_dedupes_handles_seen_via_fields_and_properties() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "ReferenceEqualityComparer.Instance" in content and "seenHandles.Add(tableHandle)" in content, (
        "SpacetimeSdkRowCallbackAdapter must dedupe table handles by reference so a future generator "
        "exposing both fields and properties does not double-wire the same callback target (AC 1)"
    )


def test_row_callback_adapter_has_try_wire_update_event_helper() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "TryWireUpdateEvent" in content, (
        "SpacetimeSdkRowCallbackAdapter must have TryWireUpdateEvent helper (AC 1)"
    )


def test_row_callback_adapter_has_try_wire_row_event_helper() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "TryWireRowEvent" in content, (
        "SpacetimeSdkRowCallbackAdapter must have TryWireRowEvent helper (AC 1)"
    )


def test_row_callback_adapter_register_callbacks_is_internal_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert "internal void RegisterCallbacks" in content, (
        "RegisterCallbacks must be declared 'internal void' — not public (AC 1)"
    )


# ---------------------------------------------------------------------------
# Generated bindings sample — RemoteTables shape sanity checks
# ---------------------------------------------------------------------------

def test_demo_generated_remote_tables_exposes_table_handles_as_public_fields() -> None:
    content = _read("demo/generated/smoke_test/Tables/SmokeTest.g.cs")
    assert "public readonly SmokeTestHandle SmokeTest;" in content, (
        "The generated sample must expose table handles as public fields so Story 3.3 validates against "
        "the actual generator shape, not an imagined property-only shape"
    )


def test_demo_generated_db_connection_exposes_db_as_single_property_instance() -> None:
    content = _read("demo/generated/smoke_test/SpacetimeDBClient.g.cs")
    assert "public override RemoteTables Db { get; }" in content, (
        "The generated sample DbConnection must expose a stable RemoteTables Db property so reconnect "
        "recovery can reuse the same db object within a live connection session"
    )


# ---------------------------------------------------------------------------
# Gap-fill: SpacetimeConnectionService.cs — invocation semantics (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_connection_service_calls_register_callbacks_on_adapter_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_rowCallbackAdapter.RegisterCallbacks" in content, (
        "SpacetimeConnectionService must call _rowCallbackAdapter.RegisterCallbacks (not a bare function call) (AC 1)"
    )


def test_connection_service_calls_register_callbacks_with_this_as_sink() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RegisterCallbacks(db, this)" in content, (
        "SpacetimeConnectionService must pass 'this' as the IRowChangeEventSink sink (AC 1)"
    )


def test_connection_service_invokes_on_row_changed_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnRowChanged?.Invoke" in content, (
        "SpacetimeConnectionService must use OnRowChanged?.Invoke to raise row change events (AC 1)"
    )


def test_connection_service_insert_sets_null_old_row_and_row_as_new_row() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RowChangeType.Insert, null, row" in content, (
        "OnRowInserted must pass null for OldRow and the row for NewRow (AC 2)"
    )


def test_connection_service_delete_sets_row_as_old_row_and_null_new_row() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RowChangeType.Delete, row, null" in content, (
        "OnRowDeleted must pass the row for OldRow and null for NewRow (AC 2)"
    )


def test_connection_service_update_passes_old_row_then_new_row() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RowChangeType.Update, oldRow, newRow" in content, (
        "OnRowUpdated must pass oldRow then newRow in correct order (AC 2)"
    )


# ---------------------------------------------------------------------------
# Gap-fill: SpacetimeClient.cs — delegate signature and dispatch (AC: 1)
# ---------------------------------------------------------------------------

def test_spacetime_client_row_changed_delegate_accepts_row_changed_event_param() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "RowChangedEventHandler(RowChangedEvent" in content, (
        "RowChangedEventHandler delegate must accept a RowChangedEvent parameter (AC 1)"
    )


def test_spacetime_client_handle_row_changed_uses_signal_adapter_dispatch() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_signalAdapter.Dispatch" in content, (
        "SpacetimeClient must use _signalAdapter.Dispatch for thread-safe signal emission in HandleRowChanged (AC 1)"
    )


# ---------------------------------------------------------------------------
# Gap-fill: docs/runtime-boundaries.md — section content and code examples (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_has_observing_live_cache_updates_section() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Observing Live Cache Updates" in content, (
        "docs/runtime-boundaries.md must have 'Observing Live Cache Updates' section heading (AC 1)"
    )


def test_runtime_boundaries_has_row_changed_subscription_example() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "RowChanged +=" in content, (
        "docs/runtime-boundaries.md must show a RowChanged += subscription example (AC 1)"
    )


def test_runtime_boundaries_has_switch_on_change_type_example() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "switch (e.ChangeType)" in content, (
        "docs/runtime-boundaries.md must show a switch on e.ChangeType code example (AC 1)"
    )


def test_runtime_boundaries_documents_null_for_insert_old_row() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "`null` for `Insert`" in content, (
        "docs/runtime-boundaries.md must document that OldRow is null for Insert events (AC 2)"
    )


def test_runtime_boundaries_documents_null_for_delete_new_row() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "`null` for `Delete`" in content, (
        "docs/runtime-boundaries.md must document that NewRow is null for Delete events (AC 2)"
    )
