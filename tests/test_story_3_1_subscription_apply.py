"""
Story 3.1: Apply a Subscription and Receive Initial Synchronized State
Automated contract tests for all story deliverables.

Covers:
- SubscriptionHandle.cs: HandleId property, Guid type, internal ctor, namespace (AC: 3)
- SubscriptionAppliedEvent.cs: Handle, AppliedAt, internal ctor, System using (AC: 2)
- SpacetimeSdkSubscriptionAdapter.cs: ISubscriptionEventSink interface, Subscribe method,
  Expression trees, InvokeWithDelegate, CreateAppliedCallback, CreateErrorCallback (AC: 1, 2)
- SpacetimeSdkConnectionAdapter.cs: Connection property returning _dbConnection (AC: 1)
- SpacetimeConnectionService.cs: ISubscriptionEventSink, Subscribe, events, registry (AC: 1, 2, 3)
- SpacetimeClient.cs: SubscriptionApplied signal, Subscribe, HandleSubscriptionApplied (AC: 1, 2, 3)
- SubscriptionRegistry.cs: existence, Register, Clear, ActiveHandles, namespace (AC: 3)
- docs/runtime-boundaries.md: Subscribe usage, SubscriptionApplied, HandleId, AppliedAt (AC: 1, 2, 3)
- Regression guards: prior story values still intact
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# SubscriptionHandle.cs — HandleId property and internal ctor (AC: 3)
# ---------------------------------------------------------------------------

def test_subscription_handle_has_handle_id_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "HandleId" in content, (
        "SubscriptionHandle.cs must contain 'HandleId' property (AC 3)"
    )


def test_subscription_handle_handle_id_is_getter_only() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "public Guid HandleId { get; }" in content, (
        "SubscriptionHandle.cs must expose HandleId as a getter-only property so the handle stays stable (AC 3)"
    )


def test_subscription_handle_id_is_guid_type() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "Guid" in content, (
        "SubscriptionHandle.cs must declare HandleId as Guid type (AC 3)"
    )


def test_subscription_handle_has_internal_constructor() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "internal SubscriptionHandle()" in content, (
        "SubscriptionHandle.cs must have 'internal SubscriptionHandle()' constructor (AC 3)"
    )


def test_subscription_handle_namespace_is_godot_spacetime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "namespace GodotSpacetime.Subscriptions" in content, (
        "SubscriptionHandle.cs must use namespace GodotSpacetime.Subscriptions (AC 3)"
    )


# ---------------------------------------------------------------------------
# SubscriptionAppliedEvent.cs — Handle, AppliedAt, internal ctor (AC: 2)
# ---------------------------------------------------------------------------

def test_subscription_applied_event_has_handle_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "SubscriptionHandle" in content and "Handle" in content, (
        "SubscriptionAppliedEvent.cs must have 'Handle' property of SubscriptionHandle type (AC 2)"
    )


def test_subscription_applied_event_handle_is_getter_only() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "public SubscriptionHandle Handle { get; }" in content, (
        "SubscriptionAppliedEvent.cs must expose Handle as a getter-only property so the applied event stays immutable (AC 2)"
    )


def test_subscription_applied_event_has_applied_at_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "AppliedAt" in content, (
        "SubscriptionAppliedEvent.cs must have 'AppliedAt' property (AC 2)"
    )


def test_subscription_applied_event_applied_at_is_getter_only() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "public DateTimeOffset AppliedAt { get; }" in content, (
        "SubscriptionAppliedEvent.cs must expose AppliedAt as a getter-only property so the applied timestamp stays immutable (AC 2)"
    )


def test_subscription_applied_event_applied_at_is_datetimeoffset() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "DateTimeOffset" in content, (
        "SubscriptionAppliedEvent.cs AppliedAt must be DateTimeOffset type (AC 2)"
    )


def test_subscription_applied_event_has_internal_constructor() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "internal SubscriptionAppliedEvent(SubscriptionHandle handle)" in content, (
        "SubscriptionAppliedEvent.cs must have internal constructor taking SubscriptionHandle (AC 2)"
    )


def test_subscription_applied_event_has_using_system() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "using System;" in content, (
        "SubscriptionAppliedEvent.cs must have 'using System;' for DateTimeOffset (AC 2)"
    )


def test_subscription_applied_event_namespace_is_godot_spacetime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "namespace GodotSpacetime.Subscriptions" in content, (
        "SubscriptionAppliedEvent.cs must use namespace GodotSpacetime.Subscriptions (AC 2)"
    )


# ---------------------------------------------------------------------------
# SpacetimeSdkSubscriptionAdapter.cs — ISubscriptionEventSink and implementation (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_subscription_adapter_has_isubscription_event_sink_interface() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "ISubscriptionEventSink" in content, (
        "SpacetimeSdkSubscriptionAdapter.cs must contain ISubscriptionEventSink interface (AC 1, 2)"
    )


def test_subscription_adapter_interface_has_on_subscription_applied() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "OnSubscriptionApplied" in content, (
        "ISubscriptionEventSink must declare OnSubscriptionApplied method (AC 2)"
    )


def test_subscription_adapter_interface_has_on_subscription_error() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "OnSubscriptionError" in content, (
        "ISubscriptionEventSink must declare OnSubscriptionError method (AC 1)"
    )


def test_subscription_adapter_has_subscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "IDbConnection connection" in content, (
        "SpacetimeSdkSubscriptionAdapter must have Subscribe method taking IDbConnection (AC 1)"
    )
    assert "string[] querySqls" in content, (
        "SpacetimeSdkSubscriptionAdapter Subscribe must accept string[] querySqls (AC 1)"
    )
    assert "ISubscriptionEventSink sink" in content, (
        "SpacetimeSdkSubscriptionAdapter Subscribe must accept ISubscriptionEventSink sink (AC 1)"
    )
    assert "SubscriptionHandle handle" in content, (
        "SpacetimeSdkSubscriptionAdapter Subscribe must accept SubscriptionHandle handle (AC 1)"
    )


def test_subscription_adapter_uses_expression_trees() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "Expression.Lambda" in content or "Expression.Call" in content, (
        "SpacetimeSdkSubscriptionAdapter must use Expression.Lambda or Expression.Call (AC 1)"
    )


def test_subscription_adapter_has_invoke_with_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "InvokeWithDelegate" in content, (
        "SpacetimeSdkSubscriptionAdapter must have InvokeWithDelegate helper method (AC 1)"
    )


def test_subscription_adapter_has_create_applied_callback() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "CreateAppliedCallback" in content, (
        "SpacetimeSdkSubscriptionAdapter must have CreateAppliedCallback method (AC 2)"
    )


def test_subscription_adapter_has_create_error_callback() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "CreateErrorCallback" in content, (
        "SpacetimeSdkSubscriptionAdapter must have CreateErrorCallback method (AC 1)"
    )


def test_subscription_adapter_has_no_stub_pragma_warning() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "#pragma warning disable CS0169" not in content, (
        "SpacetimeSdkSubscriptionAdapter.cs must not contain stub '#pragma warning disable CS0169' (AC 1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeSdkConnectionAdapter.cs — Connection property (AC: 1)
# ---------------------------------------------------------------------------

def test_connection_adapter_has_connection_property() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "internal IDbConnection? Connection" in content, (
        "SpacetimeSdkConnectionAdapter.cs must have 'internal IDbConnection? Connection' property (AC 1)"
    )


def test_connection_adapter_connection_returns_db_connection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "Connection => _dbConnection" in content, (
        "SpacetimeSdkConnectionAdapter.cs Connection property must return _dbConnection (AC 1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — ISubscriptionEventSink, Subscribe, events (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_connection_service_implements_isubscription_event_sink() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ISubscriptionEventSink" in content, (
        "SpacetimeConnectionService.cs must implement ISubscriptionEventSink (AC 1, 2)"
    )


def test_connection_service_has_subscription_adapter_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionAdapter" in content, (
        "SpacetimeConnectionService.cs must declare _subscriptionAdapter field (AC 1)"
    )


def test_connection_service_has_subscription_registry_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionRegistry" in content, (
        "SpacetimeConnectionService.cs must declare _subscriptionRegistry field (AC 3)"
    )


def test_connection_service_has_on_subscription_applied_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnSubscriptionApplied" in content, (
        "SpacetimeConnectionService.cs must declare OnSubscriptionApplied event (AC 2)"
    )


def test_connection_service_has_subscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Subscribe" in content and "string[]" in content, (
        "SpacetimeConnectionService.cs must have Subscribe method accepting string[] (AC 1)"
    )


def test_connection_service_subscribe_checks_connected_state() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ConnectionState.Connected" in content, (
        "SpacetimeConnectionService.cs Subscribe must check for ConnectionState.Connected (AC 1)"
    )


def test_connection_service_fires_on_subscription_applied() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnSubscriptionApplied?.Invoke" in content, (
        "SpacetimeConnectionService.cs must fire OnSubscriptionApplied event (AC 2)"
    )


def test_connection_service_constructs_subscription_applied_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "SubscriptionAppliedEvent" in content, (
        "SpacetimeConnectionService.cs must construct SubscriptionAppliedEvent (AC 2)"
    )


def test_connection_service_clears_subscription_registry_on_disconnect() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionRegistry.Clear()" in content, (
        "SpacetimeConnectionService.cs must call _subscriptionRegistry.Clear() in Disconnect (AC 3)"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.cs — SubscriptionApplied signal, Subscribe, handler (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_subscription_applied_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionAppliedEventHandler" in content, (
        "SpacetimeClient.cs must declare SubscriptionAppliedEventHandler signal delegate (AC 2)"
    )


def test_spacetime_client_has_subscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public SubscriptionHandle Subscribe(" in content, (
        "SpacetimeClient.cs must have public Subscribe method (AC 1)"
    )


def test_spacetime_client_subscribe_returns_subscription_handle() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionHandle Subscribe(" in content, (
        "SpacetimeClient.cs Subscribe method must return SubscriptionHandle (AC 3)"
    )


def test_spacetime_client_has_handle_subscription_applied() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleSubscriptionApplied" in content, (
        "SpacetimeClient.cs must have HandleSubscriptionApplied private handler (AC 2)"
    )


def test_spacetime_client_wires_subscription_applied_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "OnSubscriptionApplied +=" in content, (
        "SpacetimeClient.cs must wire OnSubscriptionApplied += in _EnterTree (AC 2)"
    )


def test_spacetime_client_unwires_subscription_applied_in_exit_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "OnSubscriptionApplied -=" in content, (
        "SpacetimeClient.cs must unwire OnSubscriptionApplied -= in _ExitTree (AC 2)"
    )


# ---------------------------------------------------------------------------
# SubscriptionRegistry.cs — existence and content (AC: 3)
# ---------------------------------------------------------------------------

def test_subscription_registry_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs"
    assert path.exists(), (
        "SubscriptionRegistry.cs must exist at Internal/Subscriptions/SubscriptionRegistry.cs (AC 3)"
    )


def test_subscription_registry_has_register_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "Register" in content, (
        "SubscriptionRegistry.cs must have Register method (AC 3)"
    )


def test_subscription_registry_has_clear_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "Clear" in content, (
        "SubscriptionRegistry.cs must have Clear method (AC 3)"
    )


def test_subscription_registry_has_active_handles_property() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "ActiveHandles" in content, (
        "SubscriptionRegistry.cs must have ActiveHandles property (AC 3)"
    )


def test_subscription_registry_namespace_is_godot_spacetime_runtime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "namespace GodotSpacetime.Runtime.Subscriptions" in content, (
        "SubscriptionRegistry.cs must use namespace GodotSpacetime.Runtime.Subscriptions (AC 3)"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md — subscription section content (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_has_subscribe_usage_example() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Subscribe(" in content, (
        "docs/runtime-boundaries.md must contain Subscribe() usage example (AC 1)"
    )


def test_runtime_boundaries_references_subscription_applied_signal() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "SubscriptionApplied" in content, (
        "docs/runtime-boundaries.md must reference SubscriptionApplied signal (AC 2)"
    )


def test_runtime_boundaries_references_handle_id() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "HandleId" in content, (
        "docs/runtime-boundaries.md must reference HandleId property (AC 3)"
    )


def test_runtime_boundaries_references_applied_at() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "AppliedAt" in content, (
        "docs/runtime-boundaries.md must reference AppliedAt property (AC 2)"
    )


def test_runtime_boundaries_has_invalid_operation_exception_guard() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "InvalidOperationException" in content, (
        "docs/runtime-boundaries.md must describe InvalidOperationException guard for Subscribe() (AC 1)"
    )


# ---------------------------------------------------------------------------
# Regression guards — prior story deliverables must still pass
# ---------------------------------------------------------------------------

def test_connection_adapter_still_has_open_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "public void Open(" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have Open method (regression guard)"
    )


def test_connection_adapter_still_has_frame_tick() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "FrameTick" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have FrameTick method (regression guard)"
    )


def test_connection_adapter_still_has_close_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "public void Close()" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have Close method (regression guard)"
    )


def test_connection_adapter_still_has_iconnection_event_sink() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "IConnectionEventSink" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have IConnectionEventSink interface (regression guard)"
    )


def test_connection_service_still_has_on_state_changed() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnStateChanged" in content, (
        "SpacetimeConnectionService.cs must still have OnStateChanged event (regression guard)"
    )


def test_connection_service_still_has_on_connection_opened() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnConnectionOpened" in content, (
        "SpacetimeConnectionService.cs must still have OnConnectionOpened event (regression guard)"
    )


def test_connection_service_still_has_on_connect_error() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnConnectError" in content, (
        "SpacetimeConnectionService.cs must still reference OnConnectError (regression guard)"
    )


def test_connection_service_still_implements_iconnection_event_sink() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IConnectionEventSink" in content, (
        "SpacetimeConnectionService.cs must still implement IConnectionEventSink (regression guard)"
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


def test_spacetime_client_still_has_connect_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public void Connect()" in content, (
        "SpacetimeClient.cs must still have Connect() method (regression guard)"
    )


def test_spacetime_client_still_has_disconnect_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public void Disconnect()" in content, (
        "SpacetimeClient.cs must still have Disconnect() method (regression guard)"
    )


# ---------------------------------------------------------------------------
# Isolation guard — no SpacetimeDB.* in files outside Platform/DotNet
# ---------------------------------------------------------------------------

def test_connection_service_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "SpacetimeDB." not in content, (
        "SpacetimeConnectionService.cs must not reference SpacetimeDB.* (isolation boundary)"
    )


def test_spacetime_client_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SpacetimeDB." not in content, (
        "SpacetimeClient.cs must not reference SpacetimeDB.* (isolation boundary)"
    )


def test_subscription_registry_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "SpacetimeDB." not in content, (
        "SubscriptionRegistry.cs must not reference SpacetimeDB.* (isolation boundary)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — SubscriptionHandle.cs (AC: 3)
# ---------------------------------------------------------------------------

def test_subscription_handle_has_using_system() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "using System;" in content, (
        "SubscriptionHandle.cs must have 'using System;' for Guid type (AC 3)"
    )


def test_subscription_handle_constructor_body_assigns_new_guid() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "HandleId = Guid.NewGuid()" in content, (
        "SubscriptionHandle constructor body must assign HandleId = Guid.NewGuid() (AC 3)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — SubscriptionAppliedEvent.cs (AC: 2)
# ---------------------------------------------------------------------------

def test_subscription_applied_event_constructor_assigns_handle() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "Handle = handle" in content, (
        "SubscriptionAppliedEvent constructor body must assign 'Handle = handle' (AC 2)"
    )


def test_subscription_applied_event_constructor_assigns_applied_at_utc_now() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert "AppliedAt = DateTimeOffset.UtcNow" in content, (
        "SubscriptionAppliedEvent constructor body must assign 'AppliedAt = DateTimeOffset.UtcNow' (AC 2)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — SubscriptionRegistry.cs (AC: 3)
# ---------------------------------------------------------------------------

def test_subscription_registry_has_unregister_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "Unregister" in content, (
        "SubscriptionRegistry.cs must have Unregister method (AC 3)"
    )


def test_subscription_registry_active_handles_is_ireadonlycollection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "IReadOnlyCollection" in content, (
        "SubscriptionRegistry.cs ActiveHandles must be typed as IReadOnlyCollection (AC 3)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — SpacetimeConnectionService.cs (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_connection_service_subscribe_registers_handle_in_registry() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionRegistry.Register(handle)" in content, (
        "SpacetimeConnectionService.Subscribe must call _subscriptionRegistry.Register(handle) (AC 3)"
    )


def test_connection_service_subscribe_unregisters_handle_on_synchronous_failure() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionRegistry.Unregister(handle.HandleId)" in content, (
        "SpacetimeConnectionService.Subscribe must remove a handle from the registry when adapter setup fails synchronously"
    )


def test_connection_service_on_subscription_error_is_implemented() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnSubscriptionError" in content, (
        "SpacetimeConnectionService.cs must have OnSubscriptionError implementation (AC 1)"
    )
    assert "OnSubscriptionFailed" in content, (
        "SpacetimeConnectionService.OnSubscriptionError must surface the failure via OnSubscriptionFailed (Story 3.5 complete)"
    )


def test_connection_service_has_using_runtime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "using GodotSpacetime.Runtime.Subscriptions;" in content, (
        "SpacetimeConnectionService.cs must import 'using GodotSpacetime.Runtime.Subscriptions;' (AC 3)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — SpacetimeSdkSubscriptionAdapter.cs (AC: 1)
# ---------------------------------------------------------------------------

def test_subscription_adapter_has_argument_null_guards() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "ArgumentNullException.ThrowIfNull" in content, (
        "SpacetimeSdkSubscriptionAdapter.Subscribe must guard parameters with ArgumentNullException.ThrowIfNull (AC 1)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — SpacetimeClient.cs (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_using_godot_spacetime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "using GodotSpacetime.Subscriptions;" in content, (
        "SpacetimeClient.cs must import 'using GodotSpacetime.Subscriptions;' (AC 1)"
    )


def test_spacetime_client_handle_subscription_applied_emits_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SignalName.SubscriptionApplied" in content, (
        "SpacetimeClient.cs HandleSubscriptionApplied must emit SignalName.SubscriptionApplied (AC 2)"
    )


def test_spacetime_client_handle_subscription_applied_uses_dispatch() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_signalAdapter.Dispatch" in content and "SubscriptionApplied" in content, (
        "SpacetimeClient.cs HandleSubscriptionApplied must use _signalAdapter.Dispatch pattern (AC 2)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — SpacetimeSdkConnectionAdapter.cs (AC: 1)
# ---------------------------------------------------------------------------

def test_connection_adapter_connection_property_has_null_when_not_connected_doc() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "Returns" in content and "null" in content and "not connected" in content, (
        "SpacetimeSdkConnectionAdapter.cs Connection property must have XML doc stating it returns null when not connected (AC 1)"
    )
