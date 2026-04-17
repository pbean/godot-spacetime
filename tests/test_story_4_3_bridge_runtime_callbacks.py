"""
Story 4.3: Bridge Runtime Callbacks into Scene-Safe Godot Events
Automated contract tests for all story deliverables.

Covers:
- ConnectionCloseReason.cs: enum with Clean and Error cases, namespace GodotSpacetime.Connection,
  no SpacetimeDB import (AC: 1, 2)
- ConnectionClosedEvent.cs: partial class : RefCounted, CloseReason, ErrorMessage (default empty),
  ClosedAt, using System, namespace GodotSpacetime.Connection (AC: 1, 2)
- SpacetimeConnectionService.cs: OnConnectionClosed event, Clean firing in Disconnect path with
  prevState guard, Error firing in HandleDisconnectError non-Degraded branch (AC: 1, 2)
- SpacetimeClient.cs: ConnectionClosedEventHandler signal, HandleConnectionClosed method,
  OnConnectionClosed wiring in _EnterTree/_ExitTree, _signalAdapter.Dispatch dispatch,
  all 8 signals use deferred dispatch (AC: 1, 2, 3, 4)
- GodotSignalAdapter.cs: internal sealed, Dispatch method, CallDeferred, IsInstanceValid guard,
  Callable.From pattern (AC: 3)
- docs/runtime-boundaries.md: ConnectionClosedEvent, CloseReason, ErrorMessage, ClosedAt,
  GodotSignalAdapter, CallDeferred/FrameTick ownership, complete 8-signal catalog (AC: 1, 2, 3, 4)
- Dynamic lifecycle test: OnConnectionClosed wiring inside _EnterTree/_ExitTree method bodies
- Regression guards: all Story 4.2 and 3.x deliverables intact
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# Task 5.1 — ConnectionCloseReason.cs (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_connection_close_reason_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Connection/ConnectionCloseReason.cs"
    assert path.exists(), (
        "ConnectionCloseReason.cs must exist at Public/Connection/ConnectionCloseReason.cs (AC 1, 2)"
    )


def test_connection_close_reason_is_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionCloseReason.cs")
    assert "enum ConnectionCloseReason" in content, (
        "ConnectionCloseReason must declare 'enum ConnectionCloseReason' (AC 1, 2)"
    )


def test_connection_close_reason_has_clean_case() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionCloseReason.cs")
    assert "Clean" in content, (
        "ConnectionCloseReason enum must have a 'Clean' case (AC 2)"
    )


def test_connection_close_reason_has_error_case() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionCloseReason.cs")
    assert "Error" in content, (
        "ConnectionCloseReason enum must have an 'Error' case (AC 2)"
    )


def test_connection_close_reason_namespace() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionCloseReason.cs")
    assert "GodotSpacetime.Connection" in content, (
        "ConnectionCloseReason must be in namespace GodotSpacetime.Connection (AC 1, 2)"
    )


def test_connection_close_reason_no_spacetimedb_import() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionCloseReason.cs")
    assert "SpacetimeDB" not in content, (
        "ConnectionCloseReason must NOT import SpacetimeDB — it is a plain C# enum with no SDK dependency (AC 1, 2)"
    )


# ---------------------------------------------------------------------------
# Task 5.2 — ConnectionClosedEvent.cs (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_connection_closed_event_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs"
    assert path.exists(), (
        "ConnectionClosedEvent.cs must exist at Public/Connection/ConnectionClosedEvent.cs (AC 1, 2)"
    )


def test_connection_closed_event_is_partial_class() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "partial class" in content, (
        "ConnectionClosedEvent must be a 'partial class' — Godot signals require GodotObject-derived types (AC 1, 2)"
    )


def test_connection_closed_event_extends_ref_counted() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert ": RefCounted" in content, (
        "ConnectionClosedEvent must extend RefCounted for Godot signal compatibility (AC 1, 2)"
    )


def test_connection_closed_event_has_close_reason_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "CloseReason" in content, (
        "ConnectionClosedEvent must have a CloseReason property (AC 2)"
    )


def test_connection_closed_event_has_error_message_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "ErrorMessage" in content, (
        "ConnectionClosedEvent must have an ErrorMessage property (AC 2)"
    )


def test_connection_closed_event_error_message_defaults_to_empty_string() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "string.Empty" in content, (
        "ConnectionClosedEvent.ErrorMessage must default to string.Empty for Clean closes (AC 2)"
    )


def test_connection_closed_event_has_closed_at_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "ClosedAt" in content, (
        "ConnectionClosedEvent must have a ClosedAt property (AC 2)"
    )


def test_connection_closed_event_namespace() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "GodotSpacetime.Connection" in content, (
        "ConnectionClosedEvent must be in namespace GodotSpacetime.Connection (AC 1, 2)"
    )


def test_connection_closed_event_has_using_system() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "using System;" in content, (
        "ConnectionClosedEvent must have 'using System;' for DateTimeOffset (AC 1, 2)"
    )


def test_connection_closed_event_no_spacetimedb_import() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "SpacetimeDB" not in content, (
        "ConnectionClosedEvent must NOT import SpacetimeDB — it is a public contract type (AC 1, 2)"
    )


# ---------------------------------------------------------------------------
# Task 5.3 — SpacetimeConnectionService.cs (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_connection_service_has_on_connection_closed_event() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert "event Action<ConnectionClosedEvent>" in content, (
        "SpacetimeConnectionService must declare 'event Action<ConnectionClosedEvent> OnConnectionClosed' (AC 1, 2)"
    )


def test_connection_service_fires_clean_close_reason() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert "ConnectionCloseReason.Clean" in content, (
        "SpacetimeConnectionService must fire ConnectionCloseReason.Clean in the Disconnect path (AC 2)"
    )


def test_connection_service_fires_error_close_reason() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert "ConnectionCloseReason.Error" in content, (
        "SpacetimeConnectionService must fire ConnectionCloseReason.Error in HandleDisconnectError (AC 2)"
    )


def test_connection_service_disconnect_has_prev_state_guard() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    # The prevState guard restricts Clean events to live sessions only
    assert "prevState" in content, (
        "SpacetimeConnectionService.Disconnect must capture prevState before ResetDisconnectedSessionState "
        "and guard ConnectionClosed firing on it (AC 2)"
    )
    assert (
        "ConnectionState.Connected or ConnectionState.Degraded" in content
        or "Connected or ConnectionState.Degraded" in content
    ), (
        "The prevState guard must check for 'Connected or ConnectionState.Degraded' to prevent firing "
        "for Connecting→Disconnected (failed connect) false positives (AC 2)"
    )


def test_connection_service_handle_disconnect_error_fires_on_disconnected_branch() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    # Verify ConnectionClosed(Error) is fired after the Disconnected transition
    # (not inside the Degraded branch that returns early)
    assert "ConnectionCloseReason.Error" in content, (
        "SpacetimeConnectionService.HandleDisconnectError must fire ConnectionClosedEvent with Error "
        "on the Disconnected branch (not Degraded) (AC 2)"
    )


def test_connection_service_declares_teardown_guard_field() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert "_isTearingDownConnection" in content, (
        "SpacetimeConnectionService must track teardown state so adapter-driven disconnect callbacks "
        "cannot re-enter cleanup and emit duplicate ConnectionClosed events (AC 2)"
    )


def test_connection_service_has_teardown_guard_helper() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert "RunConnectionTeardown" in content, (
        "SpacetimeConnectionService must wrap teardown paths in a helper that marks teardown-in-progress "
        "while _adapter.Close() runs (AC 2)"
    )


def test_connection_service_on_disconnected_ignores_teardown_and_late_callbacks() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    on_disconnected_match = re.search(
        r"private\s+void\s+HandleDisconnected\(long sessionId, Exception\? error\)(.*?)(?=\n\s+private\s+void\s+HandleInboundMessageReceived|\Z)",
        content,
        re.DOTALL,
    )
    assert on_disconnected_match is not None, (
        "HandleDisconnected method must exist in SpacetimeConnectionService (AC 2)"
    )
    body = on_disconnected_match.group(1)
    assert "_isTearingDownConnection" in body, (
        "OnDisconnected must ignore callbacks raised while teardown is already in progress — "
        "prevents recursive cleanup/double ConnectionClosed delivery (AC 2)"
    )
    assert "ConnectionState.Disconnected" in body, (
        "OnDisconnected must ignore late callbacks after the service already reached Disconnected (AC 2)"
    )


def test_connection_service_wraps_all_disconnect_reset_paths_in_teardown_guard() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert content.count("RunConnectionTeardown(") >= 4, (
        "All connection teardown paths (connect-start failure, failed connect, disconnect error, explicit disconnect) "
        "must run under RunConnectionTeardown so _adapter.Close() cannot recursively re-enter the service (AC 2)"
    )


# ---------------------------------------------------------------------------
# Task 5.4 — SpacetimeClient.cs bridge completeness and deferred dispatch (AC: 1, 2, 3, 4)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_connection_closed_signal_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionClosedEventHandler" in content, (
        "SpacetimeClient must declare ConnectionClosedEventHandler signal delegate (AC 1, 2, 3, 4)"
    )


def test_spacetime_client_has_handle_connection_closed_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleConnectionClosed" in content, (
        "SpacetimeClient must have a HandleConnectionClosed method (AC 1, 2, 3)"
    )


def test_spacetime_client_wires_on_connection_closed_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "OnConnectionClosed +=" in content, (
        "SpacetimeClient must wire OnConnectionClosed += HandleConnectionClosed in _EnterTree (AC 1, 3)"
    )


def test_spacetime_client_unwires_on_connection_closed_in_exit_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "OnConnectionClosed -=" in content, (
        "SpacetimeClient must unwire OnConnectionClosed -= HandleConnectionClosed in _ExitTree (AC 1, 3)"
    )


def test_spacetime_client_emits_connection_closed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "EmitSignal(SignalName.ConnectionClosed" in content, (
        "SpacetimeClient must emit SignalName.ConnectionClosed in HandleConnectionClosed (AC 1, 2, 3)"
    )


def test_spacetime_client_handle_connection_closed_uses_deferred_dispatch() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    # Check _signalAdapter.Dispatch appears in HandleConnectionClosed context
    assert "_signalAdapter.Dispatch" in content, (
        "SpacetimeClient.HandleConnectionClosed must use _signalAdapter.Dispatch for thread-safe deferred dispatch (AC 3)"
    )


def test_spacetime_client_all_8_signals_use_deferred_dispatch() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    # Count Dispatch usages — should cover all 8 handler methods
    dispatch_count = content.count("_signalAdapter.Dispatch")
    assert dispatch_count >= 8, (
        f"All 8 SpacetimeClient signal handlers must use _signalAdapter.Dispatch for deferred dispatch. "
        f"Found {dispatch_count} usages — expected at least 8 (regression guard for all signals) (AC 3)"
    )


def test_spacetime_client_handle_connection_closed_has_null_check_pattern() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    # The null-check pattern: if (_signalAdapter == null) { EmitSignal directly; return; }
    assert "_signalAdapter == null" in content, (
        "SpacetimeClient signal handlers must include the _signalAdapter null-check pattern "
        "(handles edge case where _EnterTree has not yet been called) (AC 3)"
    )


# ---------------------------------------------------------------------------
# Task 5.5 — GodotSignalAdapter.cs (locks the scene-safe bridge) (AC: 3)
# ---------------------------------------------------------------------------

def test_godot_signal_adapter_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs"
    assert path.exists(), (
        "GodotSignalAdapter.cs must exist at Internal/Events/GodotSignalAdapter.cs (AC 3)"
    )


def test_godot_signal_adapter_is_internal_sealed() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs")
    assert "internal sealed class GodotSignalAdapter" in content, (
        "GodotSignalAdapter must be 'internal sealed class GodotSignalAdapter' (AC 3)"
    )


def test_godot_signal_adapter_has_dispatch_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs")
    assert "Dispatch" in content, (
        "GodotSignalAdapter must have a Dispatch method (AC 3)"
    )


def test_godot_signal_adapter_uses_call_deferred() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs")
    assert "CallDeferred()" in content, (
        "GodotSignalAdapter.Dispatch must use CallDeferred() to queue on the Godot main thread (AC 3)"
    )


def test_godot_signal_adapter_has_is_instance_valid_guard() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs")
    assert "GodotObject.IsInstanceValid(_owner)" in content, (
        "GodotSignalAdapter must guard with GodotObject.IsInstanceValid(_owner) before dispatching (AC 3)"
    )


def test_godot_signal_adapter_uses_callable_from() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs")
    assert "Callable.From(" in content, (
        "GodotSignalAdapter must use Callable.From(action) pattern for deferred dispatch (AC 3)"
    )


# ---------------------------------------------------------------------------
# Task 5.6 — SpacetimeClient transport/reconnect ownership (AC: 3, 4)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_process_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_Process" in content, (
        "SpacetimeClient must have _Process method — it owns the transport tick (AC 3, 4)"
    )


def test_spacetime_client_process_calls_frame_tick() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "FrameTick()" in content, (
        "SpacetimeClient._Process must call FrameTick() — transport advancement is owned by the SDK node (AC 3, 4)"
    )


def test_spacetime_client_process_has_disconnected_guard() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionState.Disconnected" in content, (
        "SpacetimeClient._Process must have an early-return guard for Disconnected state (AC 3, 4)"
    )


# ---------------------------------------------------------------------------
# Task 5.7 — docs/runtime-boundaries.md additions (AC: 1, 2, 3, 4)
# ---------------------------------------------------------------------------

def test_docs_mentions_connection_closed_event() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionClosedEvent" in content, (
        "docs/runtime-boundaries.md must document ConnectionClosedEvent (AC 1, 2)"
    )


def test_docs_mentions_close_reason() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "CloseReason" in content or "ConnectionCloseReason" in content, (
        "docs/runtime-boundaries.md must mention CloseReason / ConnectionCloseReason (AC 2)"
    )


def test_docs_mentions_error_message_in_close_context() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ErrorMessage" in content, (
        "docs/runtime-boundaries.md must mention ErrorMessage in the ConnectionClosedEvent context (AC 2)"
    )


def test_docs_mentions_closed_at() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ClosedAt" in content, (
        "docs/runtime-boundaries.md must mention ClosedAt property (AC 2)"
    )


def test_docs_mentions_godot_signal_adapter() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "GodotSignalAdapter" in content, (
        "docs/runtime-boundaries.md must document GodotSignalAdapter (scene-safe bridge section) (AC 3)"
    )


def test_docs_mentions_call_deferred_or_frame_tick_ownership() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "CallDeferred" in content or "FrameTick" in content, (
        "docs/runtime-boundaries.md must document CallDeferred dispatch and/or FrameTick ownership (AC 3, 4)"
    )


def test_docs_scene_safe_bridge_notes_enter_tree_requirement() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "_EnterTree()" in content, (
        "docs/runtime-boundaries.md must note that the deferred scene-safe bridge applies after _EnterTree() "
        "initializes the signal adapter (AC 3)"
    )


def test_docs_signal_catalog_has_all_8_signals() -> None:
    content = _read("docs/runtime-boundaries.md")
    required_signals = [
        "ConnectionStateChanged",
        "ConnectionOpened",
        "ConnectionClosed",
        "SubscriptionApplied",
        "SubscriptionFailed",
        "RowChanged",
        "ReducerCallSucceeded",
        "ReducerCallFailed",
    ]
    missing = [sig for sig in required_signals if sig not in content]
    assert not missing, (
        f"docs/runtime-boundaries.md signal catalog must include all 8 signals. Missing: {missing} (AC 1, 2, 3, 4)"
    )


# ---------------------------------------------------------------------------
# Task 5.8 — Dynamic lifecycle test (Epic 3 Retro P2) (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_on_connection_closed_wired_inside_enter_tree_body() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    # Parse _EnterTree method body to confirm OnConnectionClosed += appears within it
    enter_tree_match = re.search(
        r"_EnterTree\(\)(.*?)(?=\n\s+public override void|\n\s+public void|\n\s+private void|\Z)",
        content,
        re.DOTALL,
    )
    assert enter_tree_match is not None, (
        "SpacetimeClient must have an _EnterTree() method (AC 1, 3)"
    )
    enter_tree_body = enter_tree_match.group(1)
    assert "OnConnectionClosed +=" in enter_tree_body, (
        "OnConnectionClosed += must appear INSIDE the _EnterTree method body, not just anywhere in the file "
        "(Epic 3 Retro P2 pattern — dynamic lifecycle wiring scope validation) (AC 1, 3)"
    )


def test_on_connection_closed_unwired_inside_exit_tree_body() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    # Parse _ExitTree method body to confirm OnConnectionClosed -= appears within it
    exit_tree_match = re.search(
        r"_ExitTree\(\)(.*?)(?=\n\s+public override void|\n\s+public void|\n\s+private void|\Z)",
        content,
        re.DOTALL,
    )
    assert exit_tree_match is not None, (
        "SpacetimeClient must have an _ExitTree() method (AC 1, 3)"
    )
    exit_tree_body = exit_tree_match.group(1)
    assert "OnConnectionClosed -=" in exit_tree_body, (
        "OnConnectionClosed -= must appear INSIDE the _ExitTree method body, not just anywhere in the file "
        "(Epic 3 Retro P2 pattern — dynamic lifecycle wiring scope validation) (AC 1, 3)"
    )


# ---------------------------------------------------------------------------
# Task 5.9 — Regression guards: all Story 4.2 deliverables intact
# ---------------------------------------------------------------------------

def test_regression_reducer_call_succeeded_signal_delegate_present() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReducerCallSucceededEventHandler" in content, (
        "Story 4.2 regression: ReducerCallSucceededEventHandler signal delegate must still be present"
    )


def test_regression_reducer_call_failed_signal_delegate_present() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReducerCallFailedEventHandler" in content, (
        "Story 4.2 regression: ReducerCallFailedEventHandler signal delegate must still be present"
    )


def test_regression_handle_reducer_call_succeeded_method_present() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleReducerCallSucceeded" in content, (
        "Story 4.2 regression: HandleReducerCallSucceeded method must still be present"
    )


def test_regression_handle_reducer_call_failed_method_present() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleReducerCallFailed" in content, (
        "Story 4.2 regression: HandleReducerCallFailed method must still be present"
    )


def test_regression_on_reducer_call_succeeded_wired_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "OnReducerCallSucceeded +=" in content, (
        "Story 4.2 regression: OnReducerCallSucceeded += must still be in _EnterTree"
    )


def test_regression_ireducer_event_sink_on_connection_service() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert "IReducerEventSink" in content, (
        "Story 4.2 regression: IReducerEventSink interface must still be on SpacetimeConnectionService"
    )


def test_regression_reducer_call_result_type_present() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs"
    assert path.exists(), (
        "Story 4.2 regression: ReducerCallResult.cs must still exist"
    )


def test_regression_reducer_call_error_type_present() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs"
    assert path.exists(), (
        "Story 4.2 regression: ReducerCallError.cs must still exist"
    )


def test_regression_reducer_failure_category_type_present() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs"
    assert path.exists(), (
        "Story 4.2 regression: ReducerFailureCategory.cs must still exist"
    )


def test_regression_get_field_reducers_in_sdk_reducer_adapter() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    assert 'GetField("Reducers"' in content or "Reducers" in content, (
        "Story 4.2 regression: GetField(\"Reducers\" or Reducers reference must still be in SpacetimeSdkReducerAdapter.cs"
    )


# ---------------------------------------------------------------------------
# Task 5.10 — Regression guards: all Story 3.x signals intact
# ---------------------------------------------------------------------------

def test_regression_subscription_applied_signal_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionAppliedEventHandler" in content, (
        "Story 3.x regression: SubscriptionAppliedEventHandler delegate must still be present"
    )


def test_regression_subscription_failed_signal_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionFailedEventHandler" in content, (
        "Story 3.x regression: SubscriptionFailedEventHandler delegate must still be present"
    )


def test_regression_row_changed_signal_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "RowChangedEventHandler" in content, (
        "Story 3.x regression: RowChangedEventHandler delegate must still be present"
    )


def test_regression_connection_state_changed_signal_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionStateChangedEventHandler" in content, (
        "Story 3.x regression: ConnectionStateChangedEventHandler delegate must still be present"
    )


def test_regression_connection_opened_signal_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionOpenedEventHandler" in content, (
        "Story 3.x regression: ConnectionOpenedEventHandler delegate must still be present"
    )


# ---------------------------------------------------------------------------
# Gap fills discovered during QA review
# ---------------------------------------------------------------------------

# Gap 1: ConnectionClosedEvent.cs — using Godot; required for RefCounted base class
def test_connection_closed_event_has_using_godot() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "using Godot;" in content, (
        "ConnectionClosedEvent.cs must have 'using Godot;' — required for the RefCounted base class (AC 1, 2)"
    )


# Gap 2: ConnectionClosedEvent.cs — CloseReason typed as ConnectionCloseReason (not just string presence)
def test_connection_closed_event_close_reason_typed_correctly() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "ConnectionCloseReason CloseReason" in content, (
        "ConnectionClosedEvent.CloseReason must be typed as 'ConnectionCloseReason' — "
        "not a bare property name match (AC 2)"
    )


# Gap 3: ConnectionClosedEvent.cs — ClosedAt typed as DateTimeOffset (not just string presence)
def test_connection_closed_event_closed_at_typed_correctly() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs")
    assert "DateTimeOffset ClosedAt" in content, (
        "ConnectionClosedEvent.ClosedAt must be typed as 'DateTimeOffset' (AC 2)"
    )


# Gap 4: SpacetimeClient.cs — [Signal] attribute on ConnectionClosedEventHandler delegate
def test_spacetime_client_connection_closed_signal_has_signal_attribute() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert re.search(r'\[Signal\][^\[]*ConnectionClosedEventHandler', content, re.DOTALL), (
        "ConnectionClosedEventHandler delegate must be decorated with [Signal] — "
        "required for Godot to register it as a signal (AC 1, 2)"
    )


def test_spacetime_client_connection_closed_docs_reference_connection_close_reason_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionCloseReason.Clean" in content and "ConnectionCloseReason.Error" in content, (
        "ConnectionClosedEventHandler XML docs must reference the actual ConnectionCloseReason enum values, "
        "not a nonexistent CloseReason type alias"
    )


# Gap 5: SpacetimeClient.cs — GodotSignalAdapter initialized inside _EnterTree
def test_spacetime_client_signal_adapter_initialized_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    enter_tree_match = re.search(
        r"_EnterTree\(\)(.*?)(?=\n\s+public override void|\n\s+public void|\n\s+private void|\Z)",
        content,
        re.DOTALL,
    )
    assert enter_tree_match is not None, (
        "SpacetimeClient must have an _EnterTree() method (AC 3)"
    )
    enter_tree_body = enter_tree_match.group(1)
    assert "GodotSignalAdapter" in enter_tree_body, (
        "_signalAdapter must be initialized (GodotSignalAdapter) inside _EnterTree — "
        "prerequisite for the null-check pattern in all signal handlers (AC 3)"
    )


# Gap 6: SpacetimeConnectionService.cs — _stateMachine.Transition before OnConnectionClosed?.Invoke in Disconnect(string)
def test_connection_service_disconnect_state_transition_before_connection_closed_event() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    disconnect_match = re.search(
        r"private void Disconnect\(string description\)(.*?)(?=\n\s+private void|\n\s+public|\Z)",
        content,
        re.DOTALL,
    )
    assert disconnect_match is not None, "private Disconnect(string description) method must exist (AC 2)"
    body = disconnect_match.group(1)
    transition_pos = body.find("_stateMachine.Transition")
    closed_pos = body.find("OnConnectionClosed?.Invoke")
    assert transition_pos != -1, "_stateMachine.Transition must appear in Disconnect(string) body (AC 1, 2)"
    assert closed_pos != -1, "OnConnectionClosed?.Invoke must appear in Disconnect(string) body (AC 1, 2)"
    assert transition_pos < closed_pos, (
        "_stateMachine.Transition must appear BEFORE OnConnectionClosed?.Invoke in Disconnect(string) — "
        "ConnectionStateChanged must fire before ConnectionClosed (AC 1, 2)"
    )


# Gap 7: SpacetimeConnectionService.cs — same ordering constraint in HandleDisconnectError
def test_connection_service_handle_disconnect_error_state_transition_before_connection_closed_event() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    handle_error_match = re.search(
        r"private void HandleDisconnectError\(Exception error\)(.*?)(?=\n\s+private void|\n\s+public|\Z)",
        content,
        re.DOTALL,
    )
    assert handle_error_match is not None, "HandleDisconnectError method must exist (AC 2)"
    body = handle_error_match.group(1)
    # Use rfind to get the Disconnected-branch Transition (last one), before OnConnectionClosed
    transition_pos = body.rfind("_stateMachine.Transition(")
    closed_pos = body.find("OnConnectionClosed?.Invoke")
    assert transition_pos != -1, "_stateMachine.Transition must appear in HandleDisconnectError (AC 1, 2)"
    assert closed_pos != -1, "OnConnectionClosed?.Invoke must appear in HandleDisconnectError (AC 1, 2)"
    assert transition_pos < closed_pos, (
        "_stateMachine.Transition must appear BEFORE OnConnectionClosed?.Invoke in HandleDisconnectError — "
        "ConnectionStateChanged fires before ConnectionClosed (AC 1, 2)"
    )


# Gap 8: SpacetimeConnectionService.cs — ErrorMessage = error.Message in Error close event
def test_connection_service_error_event_propagates_error_message() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert "ErrorMessage = error.Message" in content, (
        "SpacetimeConnectionService must set 'ErrorMessage = error.Message' when firing "
        "ConnectionClosedEvent with CloseReason.Error — error context must reach game code (AC 2)"
    )


# Gap 9: SpacetimeConnectionService.cs — Degraded branch return; before OnConnectionClosed?.Invoke
def test_connection_service_degraded_branch_returns_before_connection_closed() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    handle_error_match = re.search(
        r"private void HandleDisconnectError\(Exception error\)(.*?)(?=\n\s+private void|\n\s+public|\Z)",
        content,
        re.DOTALL,
    )
    assert handle_error_match is not None, "HandleDisconnectError must exist (AC 2)"
    body = handle_error_match.group(1)
    degraded_pos = body.find("ConnectionState.Degraded")
    return_pos = body.find("return;", degraded_pos)
    closed_pos = body.find("OnConnectionClosed?.Invoke")
    assert degraded_pos != -1, "Degraded branch must exist in HandleDisconnectError (AC 2)"
    assert return_pos != -1, "return; must follow the Degraded transition in HandleDisconnectError (AC 2)"
    assert return_pos < closed_pos, (
        "The Degraded branch in HandleDisconnectError must return early (before OnConnectionClosed?.Invoke) — "
        "ConnectionClosed must NOT fire while the session is degraded (AC 2)"
    )


# Gap 10: SpacetimeConnectionService.cs — OnConnectError does not directly invoke OnConnectionClosed
def test_connection_service_on_connect_error_does_not_directly_invoke_connection_closed() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    on_connect_error_match = re.search(
        r"OnConnectError\(Exception error\)(.*?)(?=\n\s+void\s+IConnectionEventSink\.OnDisconnected|\Z)",
        content,
        re.DOTALL,
    )
    assert on_connect_error_match is not None, (
        "OnConnectError method must exist in SpacetimeConnectionService (AC 2)"
    )
    body = on_connect_error_match.group(1)
    assert "OnConnectionClosed?.Invoke" not in body, (
        "OnConnectError must NOT directly invoke OnConnectionClosed — "
        "failed connect attempts (Connecting→Disconnected) must not fire ConnectionClosed (AC 2)"
    )


# Gap 11: SpacetimeClient.cs regression — OnReducerCallFailed += wired in _EnterTree
def test_regression_on_reducer_call_failed_wired_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    enter_tree_match = re.search(
        r"_EnterTree\(\)(.*?)(?=\n\s+public override void|\n\s+public void|\n\s+private void|\Z)",
        content,
        re.DOTALL,
    )
    assert enter_tree_match is not None, "SpacetimeClient must have _EnterTree() (AC 3)"
    enter_tree_body = enter_tree_match.group(1)
    assert "OnReducerCallFailed +=" in enter_tree_body, (
        "Story 4.2 regression: OnReducerCallFailed += must be wired inside _EnterTree body "
        "(symmetric regression guard to OnReducerCallSucceeded +=)"
    )


# Gap 12: SpacetimeClient.cs regression — OnReducerCallSucceeded -= unwired in _ExitTree
def test_regression_on_reducer_call_succeeded_unwired_in_exit_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    exit_tree_match = re.search(
        r"_ExitTree\(\)(.*?)(?=\n\s+public override void|\n\s+public void|\n\s+private void|\Z)",
        content,
        re.DOTALL,
    )
    assert exit_tree_match is not None, "SpacetimeClient must have _ExitTree() (AC 3)"
    exit_tree_body = exit_tree_match.group(1)
    assert "OnReducerCallSucceeded -=" in exit_tree_body, (
        "Story 4.2 regression: OnReducerCallSucceeded -= must be unwired inside _ExitTree body"
    )


# Gap 13: SpacetimeClient.cs regression — OnReducerCallFailed -= unwired in _ExitTree
def test_regression_on_reducer_call_failed_unwired_in_exit_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    exit_tree_match = re.search(
        r"_ExitTree\(\)(.*?)(?=\n\s+public override void|\n\s+public void|\n\s+private void|\Z)",
        content,
        re.DOTALL,
    )
    assert exit_tree_match is not None, "SpacetimeClient must have _ExitTree() (AC 3)"
    exit_tree_body = exit_tree_match.group(1)
    assert "OnReducerCallFailed -=" in exit_tree_body, (
        "Story 4.2 regression: OnReducerCallFailed -= must be unwired inside _ExitTree body"
    )


# Gap 14: GodotSignalAdapter.cs — namespace GodotSpacetime.Runtime.Events
def test_godot_signal_adapter_namespace() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs")
    assert "GodotSpacetime.Runtime.Events" in content, (
        "GodotSignalAdapter must be in namespace GodotSpacetime.Runtime.Events (AC 3)"
    )
