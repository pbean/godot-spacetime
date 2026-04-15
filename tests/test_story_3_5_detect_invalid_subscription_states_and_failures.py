"""
Story 3.5: Detect Invalid Subscription States and Failures
Automated contract tests for all story deliverables.

Covers:
- SubscriptionFailedEvent.cs: file exists, namespace, class name, inherits RefCounted,
  properties Handle/ErrorMessage/FailedAt, constructor signature, no SpacetimeDB.* import (AC: 1, 3)
- SpacetimeConnectionService.cs: OnSubscriptionFailed event declaration, OnSubscriptionError
  invokes OnSubscriptionFailed, invocation appears after handle.Close(), placeholder comment removed (AC: 1, 2, 3)
- SpacetimeClient.cs: SubscriptionFailedEventHandler delegate, OnSubscriptionFailed wired in
  _EnterTree, unwired in _ExitTree, HandleSubscriptionFailed method, deferred dispatch via
  _signalAdapter (AC: 1, 3)
- Regression guards: prior story deliverables intact — SubscriptionApplied, RowChanged,
  GetRows, Subscribe, Unsubscribe, ReplaceSubscription, SubscriptionStatus, SubscriptionHandle.Status,
  _pendingReplacements, TryGetEntry in registry (AC: 2)
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# SubscriptionFailedEvent.cs — file existence and content (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_subscription_failed_event_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs"
    assert path.exists(), (
        "SubscriptionFailedEvent.cs must exist at Public/Subscriptions/SubscriptionFailedEvent.cs (AC 1, 3)"
    )


def test_subscription_failed_event_namespace_is_godot_spacetime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "namespace GodotSpacetime.Subscriptions" in content, (
        "SubscriptionFailedEvent.cs must use namespace GodotSpacetime.Subscriptions (AC 1, 3)"
    )


def test_subscription_failed_event_class_name_is_correct() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "class SubscriptionFailedEvent" in content, (
        "File must declare 'class SubscriptionFailedEvent' (AC 1, 3)"
    )


def test_subscription_failed_event_is_public() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "public partial class SubscriptionFailedEvent" in content, (
        "SubscriptionFailedEvent must be 'public partial class' (AC 1, 3)"
    )


def test_subscription_failed_event_inherits_ref_counted() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "RefCounted" in content, (
        "SubscriptionFailedEvent must inherit from RefCounted — required for Godot signal params (AC 1, 3)"
    )


def test_subscription_failed_event_inherits_ref_counted_in_declaration() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "SubscriptionFailedEvent : RefCounted" in content, (
        "SubscriptionFailedEvent class declaration must extend RefCounted directly (AC 1, 3)"
    )


def test_subscription_failed_event_has_handle_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "SubscriptionHandle Handle" in content, (
        "SubscriptionFailedEvent must have a 'SubscriptionHandle Handle' property (AC 1, 3)"
    )


def test_subscription_failed_event_handle_property_is_public() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "public SubscriptionHandle Handle" in content, (
        "SubscriptionFailedEvent.Handle must be public (AC 1, 3)"
    )


def test_subscription_failed_event_has_error_message_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "string ErrorMessage" in content, (
        "SubscriptionFailedEvent must have a 'string ErrorMessage' property (AC 3)"
    )


def test_subscription_failed_event_error_message_property_is_public() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "public string ErrorMessage" in content, (
        "SubscriptionFailedEvent.ErrorMessage must be public (AC 3)"
    )


def test_subscription_failed_event_has_failed_at_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "DateTimeOffset FailedAt" in content, (
        "SubscriptionFailedEvent must have a 'DateTimeOffset FailedAt' property (AC 3)"
    )


def test_subscription_failed_event_failed_at_property_is_public() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "public DateTimeOffset FailedAt" in content, (
        "SubscriptionFailedEvent.FailedAt must be public (AC 3)"
    )


def test_subscription_failed_event_properties_are_get_only() -> None:
    lines = _lines("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    handle_line = next((ln for ln in lines if "SubscriptionHandle Handle" in ln), None)
    assert handle_line is not None, "Handle property line not found"
    assert "{ get; }" in handle_line, (
        "SubscriptionFailedEvent.Handle must be a get-only property '{ get; }' (AC 1, 3)"
    )


def test_subscription_failed_event_error_message_is_get_only() -> None:
    lines = _lines("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    msg_line = next((ln for ln in lines if "string ErrorMessage" in ln), None)
    assert msg_line is not None, "ErrorMessage property line not found"
    assert "{ get; }" in msg_line, (
        "SubscriptionFailedEvent.ErrorMessage must be a get-only property '{ get; }' (AC 3)"
    )


def test_subscription_failed_event_failed_at_is_get_only() -> None:
    lines = _lines("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    at_line = next((ln for ln in lines if "DateTimeOffset FailedAt" in ln), None)
    assert at_line is not None, "FailedAt property line not found"
    assert "{ get; }" in at_line, (
        "SubscriptionFailedEvent.FailedAt must be a get-only property '{ get; }' (AC 3)"
    )


def test_subscription_failed_event_constructor_takes_handle_and_exception() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "SubscriptionFailedEvent(SubscriptionHandle handle, Exception error)" in content, (
        "Constructor must take (SubscriptionHandle handle, Exception error) (AC 1, 3)"
    )


def test_subscription_failed_event_constructor_is_internal() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "internal SubscriptionFailedEvent(" in content, (
        "Constructor must be 'internal' — only the SDK creates this payload (AC 1, 3)"
    )


def test_subscription_failed_event_sets_error_message_from_exception() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "error.Message" in content, (
        "Constructor must set ErrorMessage = error.Message to extract safe boundary type (AC 3)"
    )


def test_subscription_failed_event_sets_failed_at_utc_now() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "DateTimeOffset.UtcNow" in content, (
        "Constructor must set FailedAt = DateTimeOffset.UtcNow (AC 3)"
    )


def test_subscription_failed_event_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "SpacetimeDB." not in content, (
        "SubscriptionFailedEvent.cs must NOT reference SpacetimeDB.* — public boundary type (AC 1, 3)"
    )


def test_subscription_failed_event_does_not_expose_raw_exception() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    # Exception should only appear in the constructor signature, not as a property type
    lines = _lines("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    exception_property_lines = [
        ln for ln in lines
        if "Exception" in ln and "{ get;" in ln
    ]
    assert len(exception_property_lines) == 0, (
        "SubscriptionFailedEvent must NOT expose a raw Exception property — "
        "Exception cannot be passed as a Godot signal parameter (AC 1, 3)"
    )


def test_subscription_failed_event_using_godot() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "using Godot" in content, (
        "SubscriptionFailedEvent.cs must import Godot (for RefCounted base class) (AC 1, 3)"
    )


def test_subscription_failed_event_using_system() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "using System" in content, (
        "SubscriptionFailedEvent.cs must import System (for Exception and DateTimeOffset) (AC 1, 3)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — OnSubscriptionFailed event and invocation (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_connection_service_has_on_subscription_failed_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnSubscriptionFailed" in content, (
        "SpacetimeConnectionService must declare OnSubscriptionFailed event (AC 1, 2, 3)"
    )


def test_connection_service_on_subscription_failed_event_is_action_of_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Action<SubscriptionFailedEvent>? OnSubscriptionFailed" in content, (
        "OnSubscriptionFailed must be 'Action<SubscriptionFailedEvent>?' (AC 1, 2, 3)"
    )


def test_connection_service_on_subscription_failed_event_is_public() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "public event Action<SubscriptionFailedEvent>? OnSubscriptionFailed" in content, (
        "OnSubscriptionFailed must be a public event (AC 1, 2, 3)"
    )


def test_connection_service_on_subscription_failed_declared_after_on_subscription_applied() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    applied_pos = content.find("OnSubscriptionApplied")
    failed_pos = content.find("OnSubscriptionFailed")
    assert applied_pos != -1, "OnSubscriptionApplied must be present"
    assert failed_pos != -1, "OnSubscriptionFailed must be present"
    assert applied_pos < failed_pos, (
        "OnSubscriptionFailed must be declared after OnSubscriptionApplied (AC 1, 2, 3)"
    )


def test_connection_service_on_subscription_error_invokes_on_subscription_failed() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnSubscriptionFailed?.Invoke(" in content, (
        "OnSubscriptionError must invoke OnSubscriptionFailed?.Invoke(...) (AC 1, 2, 3)"
    )


def test_connection_service_failed_invocation_passes_new_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "new SubscriptionFailedEvent(handle, error)" in content, (
        "OnSubscriptionFailed must be invoked with 'new SubscriptionFailedEvent(handle, error)' (AC 1, 3)"
    )


def test_connection_service_failed_invocation_is_after_handle_close() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    close_pos = content.find("handle.Close();")
    invoke_pos = content.find("OnSubscriptionFailed?.Invoke(")
    assert close_pos != -1, "handle.Close() must be present in OnSubscriptionError"
    assert invoke_pos != -1, "OnSubscriptionFailed?.Invoke(...) must be present"
    assert close_pos < invoke_pos, (
        "OnSubscriptionFailed must be invoked AFTER handle.Close() to ensure handle is in Closed "
        "state when gameplay code observes the event (AC 1, 2, 3)"
    )


def test_connection_service_failed_invocation_is_after_unregister() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    unregister_pos = content.find("_subscriptionRegistry.Unregister(handle.HandleId);")
    invoke_pos = content.find("OnSubscriptionFailed?.Invoke(")
    assert unregister_pos != -1, "_subscriptionRegistry.Unregister must be present"
    assert invoke_pos != -1, "OnSubscriptionFailed?.Invoke(...) must be present"
    assert unregister_pos < invoke_pos, (
        "OnSubscriptionFailed must be invoked AFTER Unregister — registry must be clean (AC 2)"
    )


def test_connection_service_failed_invocation_is_after_remove_pending_replacements() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    remove_pos = content.find("RemovePendingReplacementReferences(handle.HandleId)")
    invoke_pos = content.find("OnSubscriptionFailed?.Invoke(")
    assert remove_pos != -1, "RemovePendingReplacementReferences must be present"
    assert invoke_pos != -1, "OnSubscriptionFailed?.Invoke(...) must be present"
    assert remove_pos < invoke_pos, (
        "OnSubscriptionFailed must be invoked AFTER RemovePendingReplacementReferences — "
        "pending replacement tracking must be cleaned up first (AC 2)"
    )


def test_connection_service_placeholder_comment_removed() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Story 3.5 will surface this error" not in content, (
        "The placeholder comment 'Story 3.5 will surface this error...' must be removed (AC 1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.cs — SubscriptionFailed signal and handler (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_subscription_failed_signal_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionFailedEventHandler" in content, (
        "SpacetimeClient must declare SubscriptionFailedEventHandler signal delegate (AC 1, 3)"
    )


def test_spacetime_client_subscription_failed_delegate_is_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    lines = _lines("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    signal_attr_idx = None
    for i, ln in enumerate(lines):
        if "[Signal]" in ln:
            if i + 1 < len(lines) and "SubscriptionFailedEventHandler" in lines[i + 1]:
                signal_attr_idx = i
                break
    assert signal_attr_idx is not None, (
        "SubscriptionFailedEventHandler delegate must be annotated with [Signal] (AC 1, 3)"
    )


def test_spacetime_client_subscription_failed_delegate_takes_event_param() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionFailedEventHandler(SubscriptionFailedEvent e)" in content, (
        "SubscriptionFailedEventHandler must take a SubscriptionFailedEvent parameter (AC 1, 3)"
    )


def test_spacetime_client_subscription_failed_delegate_declared_after_applied() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    applied_pos = content.find("SubscriptionAppliedEventHandler")
    failed_pos = content.find("SubscriptionFailedEventHandler")
    assert applied_pos != -1, "SubscriptionAppliedEventHandler must be present"
    assert failed_pos != -1, "SubscriptionFailedEventHandler must be present"
    assert applied_pos < failed_pos, (
        "SubscriptionFailedEventHandler must be declared after SubscriptionAppliedEventHandler (AC 1, 3)"
    )


def test_spacetime_client_wires_on_subscription_failed_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    enter_tree_section = content[content.find("_EnterTree()"):content.find("_ExitTree()")]
    assert "OnSubscriptionFailed += HandleSubscriptionFailed" in enter_tree_section, (
        "SpacetimeClient._EnterTree() must subscribe OnSubscriptionFailed += HandleSubscriptionFailed (AC 1, 3)"
    )


def test_spacetime_client_unwires_on_subscription_failed_in_exit_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    exit_tree_end = content.find("public void Connect()")
    exit_tree_section = content[content.find("_ExitTree()"):exit_tree_end]
    assert "OnSubscriptionFailed -= HandleSubscriptionFailed" in exit_tree_section, (
        "SpacetimeClient._ExitTree() must unsubscribe OnSubscriptionFailed -= HandleSubscriptionFailed (AC 1, 3)"
    )


def test_spacetime_client_has_handle_subscription_failed_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleSubscriptionFailed" in content, (
        "SpacetimeClient must have a HandleSubscriptionFailed method (AC 1, 3)"
    )


def test_spacetime_client_handle_subscription_failed_is_private() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "private void HandleSubscriptionFailed(SubscriptionFailedEvent" in content, (
        "HandleSubscriptionFailed must be 'private void HandleSubscriptionFailed(SubscriptionFailedEvent ...)' (AC 1, 3)"
    )


def test_spacetime_client_handle_subscription_failed_emits_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SignalName.SubscriptionFailed" in content, (
        "HandleSubscriptionFailed must emit SignalName.SubscriptionFailed (AC 1, 3)"
    )


def test_spacetime_client_handle_subscription_failed_uses_deferred_dispatch() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    # The handler method contains a Dispatch call referencing SubscriptionFailed
    failed_handler_start = content.find("HandleSubscriptionFailed(SubscriptionFailedEvent")
    failed_handler_end = content.find("\n    }", failed_handler_start)
    handler_body = content[failed_handler_start:failed_handler_end]
    assert "_signalAdapter.Dispatch(" in handler_body, (
        "HandleSubscriptionFailed must use _signalAdapter.Dispatch() for deferred Godot main-thread dispatch (AC 1, 3)"
    )


def test_spacetime_client_handle_subscription_failed_has_null_guard_for_signal_adapter() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    failed_handler_start = content.find("HandleSubscriptionFailed(SubscriptionFailedEvent")
    failed_handler_end = content.find("\n    }", failed_handler_start)
    handler_body = content[failed_handler_start:failed_handler_end]
    assert "_signalAdapter == null" in handler_body, (
        "HandleSubscriptionFailed must guard for _signalAdapter == null (direct EmitSignal fallback) (AC 1, 3)"
    )


def test_spacetime_client_handle_subscription_failed_passes_event_to_emit() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    failed_handler_start = content.find("HandleSubscriptionFailed(SubscriptionFailedEvent")
    failed_handler_end = content.find("\n    }", failed_handler_start)
    handler_body = content[failed_handler_start:failed_handler_end]
    assert "failedEvent" in handler_body, (
        "HandleSubscriptionFailed must pass the failedEvent to EmitSignal (AC 1, 3)"
    )


# ---------------------------------------------------------------------------
# Regression guards — prior story deliverables intact (AC: 2)
# ---------------------------------------------------------------------------

def test_regression_subscription_applied_signal_intact() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionAppliedEventHandler" in content, (
        "Regression: SubscriptionApplied signal must still be present (AC 2)"
    )


def test_regression_row_changed_signal_intact() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "RowChangedEventHandler" in content, (
        "Regression: RowChanged signal must still be present (AC 2)"
    )


def test_regression_get_rows_intact() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "GetRows(" in content, (
        "Regression: GetRows() method must still be present (AC 2)"
    )


def test_regression_subscribe_intact() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public SubscriptionHandle Subscribe(" in content, (
        "Regression: Subscribe() method must still be present (AC 2)"
    )


def test_regression_unsubscribe_intact() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public void Unsubscribe(" in content, (
        "Regression: Unsubscribe() method must still be present (AC 2)"
    )


def test_regression_replace_subscription_intact() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReplaceSubscription(" in content, (
        "Regression: ReplaceSubscription() method must still be present (AC 2)"
    )


def test_regression_subscription_status_file_intact() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs"
    assert path.exists(), (
        "Regression: SubscriptionStatus.cs must still exist (AC 2)"
    )


def test_regression_subscription_status_has_active() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs")
    assert "Active" in content, (
        "Regression: SubscriptionStatus.Active must still be present (AC 2)"
    )


def test_regression_subscription_handle_status_property_intact() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "public SubscriptionStatus Status" in content, (
        "Regression: SubscriptionHandle.Status property must still be present (AC 2)"
    )


def test_regression_pending_replacements_field_intact() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_pendingReplacements" in content, (
        "Regression: _pendingReplacements field must still be present in SpacetimeConnectionService (AC 2)"
    )


def test_regression_try_get_entry_intact() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "TryGetEntry" in content, (
        "Regression: TryGetEntry method must still be present in SubscriptionRegistry (AC 2)"
    )


def test_regression_on_subscription_applied_service_event_intact() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "public event Action<SubscriptionAppliedEvent>? OnSubscriptionApplied" in content, (
        "Regression: OnSubscriptionApplied event must still be present in SpacetimeConnectionService (AC 2)"
    )


def test_regression_on_row_changed_service_event_intact() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "public event Action<RowChangedEvent>? OnRowChanged" in content, (
        "Regression: OnRowChanged event must still be present in SpacetimeConnectionService (AC 2)"
    )


def test_regression_subscription_applied_event_file_intact() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs"
    assert path.exists(), (
        "Regression: SubscriptionAppliedEvent.cs must still exist (AC 2)"
    )


def test_regression_handle_subscription_applied_intact() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleSubscriptionApplied" in content, (
        "Regression: HandleSubscriptionApplied method must still be present in SpacetimeClient (AC 2)"
    )


def test_regression_handle_row_changed_intact() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleRowChanged" in content, (
        "Regression: HandleRowChanged method must still be present in SpacetimeClient (AC 2)"
    )


def test_regression_on_subscription_applied_wired_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    enter_tree_section = content[content.find("_EnterTree()"):content.find("_ExitTree()")]
    assert "OnSubscriptionApplied += HandleSubscriptionApplied" in enter_tree_section, (
        "Regression: OnSubscriptionApplied must still be wired in _EnterTree (AC 2)"
    )


def test_regression_on_subscription_applied_unwired_in_exit_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    exit_tree_end = content.find("public void Connect()")
    exit_tree_section = content[content.find("_ExitTree()"):exit_tree_end]
    assert "OnSubscriptionApplied -= HandleSubscriptionApplied" in exit_tree_section, (
        "Regression: OnSubscriptionApplied must still be unwired in _ExitTree (AC 2)"
    )


def test_regression_on_row_changed_wired_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    enter_tree_section = content[content.find("_EnterTree()"):content.find("_ExitTree()")]
    assert "OnRowChanged += HandleRowChanged" in enter_tree_section, (
        "Regression: OnRowChanged must still be wired in _EnterTree (AC 2)"
    )


# ---------------------------------------------------------------------------
# Gap: SubscriptionFailedEvent.cs — constructor body assignments (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_subscription_failed_event_constructor_assigns_handle() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "Handle = handle" in content, (
        "Constructor body must assign 'Handle = handle' to set the payload's Handle property (AC 1, 3)"
    )


def test_subscription_failed_event_constructor_assigns_error_message_from_exception() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs")
    assert "ErrorMessage = error.Message" in content, (
        "Constructor body must assign 'ErrorMessage = error.Message' — extracts safe boundary "
        "string from the Exception before it crosses the public API (AC 3)"
    )


# ---------------------------------------------------------------------------
# Gap: SpacetimeConnectionService.cs — OnSubscriptionError implementation detail (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_connection_service_on_subscription_error_is_explicit_interface_implementation() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "void ISubscriptionEventSink.OnSubscriptionError(" in content, (
        "OnSubscriptionError must be declared as an explicit ISubscriptionEventSink interface "
        "implementation 'void ISubscriptionEventSink.OnSubscriptionError(' (AC 1)"
    )


def test_connection_service_on_subscription_error_uses_try_get_entry() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    error_start = content.find("void ISubscriptionEventSink.OnSubscriptionError(")
    next_method = content.find("void IRowChangeEventSink.", error_start)
    error_section = content[error_start:next_method]
    assert "TryGetEntry" in error_section, (
        "OnSubscriptionError must call _subscriptionRegistry.TryGetEntry to guard the TryUnsubscribe "
        "call against a missing registry entry (AC 1, 2)"
    )


def test_connection_service_on_subscription_error_remove_pending_before_try_get_entry() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    error_start = content.find("void ISubscriptionEventSink.OnSubscriptionError(")
    next_method = content.find("void IRowChangeEventSink.", error_start)
    error_section = content[error_start:next_method]
    remove_pos = error_section.find("RemovePendingReplacementReferences(")
    try_get_pos = error_section.find("TryGetEntry")
    assert remove_pos != -1, "RemovePendingReplacementReferences must be called in OnSubscriptionError"
    assert try_get_pos != -1, "TryGetEntry must be called in OnSubscriptionError"
    assert remove_pos < try_get_pos, (
        "RemovePendingReplacementReferences must be called BEFORE TryGetEntry in OnSubscriptionError — "
        "pending replacement references must be cleared before SDK-level unsubscribe (AC 2)"
    )


def test_connection_service_on_subscription_error_try_unsubscribe_before_unregister() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    error_start = content.find("void ISubscriptionEventSink.OnSubscriptionError(")
    next_method = content.find("void IRowChangeEventSink.", error_start)
    error_section = content[error_start:next_method]
    unsub_pos = error_section.find("TryUnsubscribe(")
    unregister_pos = error_section.find("Unregister(handle.HandleId)")
    assert unsub_pos != -1, "TryUnsubscribe must be called in OnSubscriptionError (AC 1, 2)"
    assert unregister_pos != -1, "Unregister must be called in OnSubscriptionError (AC 2)"
    assert unsub_pos < unregister_pos, (
        "TryUnsubscribe must be called BEFORE Unregister in OnSubscriptionError — "
        "SDK close must precede registry cleanup (AC 1, 2)"
    )


def test_connection_service_on_subscription_error_unregister_before_handle_close() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    error_start = content.find("void ISubscriptionEventSink.OnSubscriptionError(")
    next_method = content.find("void IRowChangeEventSink.", error_start)
    error_section = content[error_start:next_method]
    unregister_pos = error_section.find("Unregister(handle.HandleId)")
    close_pos = error_section.find("handle.Close()")
    assert unregister_pos != -1, "Unregister must be called in OnSubscriptionError"
    assert close_pos != -1, "handle.Close() must be called in OnSubscriptionError"
    assert unregister_pos < close_pos, (
        "Unregister must be called BEFORE handle.Close() in OnSubscriptionError — "
        "registry must be fully cleaned up before the handle is marked Closed (AC 2)"
    )


def test_connection_service_on_subscription_error_does_not_touch_old_handle_comment() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "WITHOUT touching old handle" in content or "old remains active" in content, (
        "OnSubscriptionError must have a comment documenting that the old subscription handle is "
        "intentionally NOT closed during a replacement failure — this communicates the AC 2 semantic "
        "to future maintainers (AC 2)"
    )


# ---------------------------------------------------------------------------
# Gap: Public docs and adapter comments must reflect the shipped failure surface
# ---------------------------------------------------------------------------

def test_runtime_boundaries_documents_subscription_failed_signal() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "SubscriptionFailed" in content, (
        "docs/runtime-boundaries.md must document the SubscriptionFailed signal now that Story 3.5 "
        "has added the public failure surface (AC 1, 3)"
    )


def test_runtime_boundaries_documents_subscription_failed_event_payload() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "SubscriptionFailedEvent" in content and "ErrorMessage" in content and "FailedAt" in content, (
        "docs/runtime-boundaries.md must describe SubscriptionFailedEvent and its actionable payload "
        "fields so developers can diagnose failures from the public contract docs (AC 1, 3)"
    )


def test_spacetime_client_summary_mentions_subscription_failed_event() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionFailedEvent when a request is rejected or later errors" in content, (
        "SpacetimeClient XML summary must mention SubscriptionFailedEvent so the public entry-point "
        "docs reflect both the apply and failure subscription paths (AC 1, 3)"
    )


def test_subscription_adapter_no_longer_has_story_3_5_future_tense_comment() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "Story 3.5 will add an explicit failure surface" not in content, (
        "SpacetimeSdkSubscriptionAdapter must not carry a stale Story 3.5 future-tense comment now "
        "that the failure surface has shipped"
    )


# ---------------------------------------------------------------------------
# Gap: SpacetimeClient.cs — HandleSubscriptionFailed null-branch and dispatch content (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_spacetime_client_handle_subscription_failed_null_branch_emits_correct_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    handler_start = content.find("private void HandleSubscriptionFailed(SubscriptionFailedEvent")
    handler_end = content.find("\n    }", handler_start)
    handler_body = content[handler_start:handler_end]
    null_branch_start = handler_body.find("_signalAdapter == null")
    null_branch_end = handler_body.find("return;", null_branch_start)
    null_branch = handler_body[null_branch_start:null_branch_end]
    assert "SignalName.SubscriptionFailed" in null_branch, (
        "HandleSubscriptionFailed null-guard branch must emit 'SignalName.SubscriptionFailed' directly "
        "— this is the fallback path used before the node enters the Godot tree (AC 1, 3)"
    )


def test_spacetime_client_handle_subscription_failed_dispatch_lambda_emits_subscription_failed() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    handler_start = content.find("private void HandleSubscriptionFailed(SubscriptionFailedEvent")
    handler_end = content.find("\n    }", handler_start)
    handler_body = content[handler_start:handler_end]
    dispatch_start = handler_body.find("_signalAdapter.Dispatch(")
    dispatch_end = handler_body.find(");", dispatch_start)
    dispatch_call = handler_body[dispatch_start:dispatch_end]
    assert "SignalName.SubscriptionFailed" in dispatch_call, (
        "HandleSubscriptionFailed _signalAdapter.Dispatch lambda must reference "
        "'SignalName.SubscriptionFailed' inside the deferred call (AC 1, 3)"
    )


def test_spacetime_client_handle_subscription_failed_dispatch_lambda_passes_event() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    handler_start = content.find("private void HandleSubscriptionFailed(SubscriptionFailedEvent")
    handler_end = content.find("\n    }", handler_start)
    handler_body = content[handler_start:handler_end]
    dispatch_start = handler_body.find("_signalAdapter.Dispatch(")
    dispatch_end = handler_body.find(");", dispatch_start)
    dispatch_call = handler_body[dispatch_start:dispatch_end]
    assert "failedEvent" in dispatch_call, (
        "HandleSubscriptionFailed _signalAdapter.Dispatch lambda must pass 'failedEvent' to "
        "EmitSignal — the event payload must reach gameplay code (AC 1, 3)"
    )


# ---------------------------------------------------------------------------
# Gap regression: SpacetimeClient.cs — OnRowChanged unwired in _ExitTree (AC: 2)
# ---------------------------------------------------------------------------

def test_regression_on_row_changed_unwired_in_exit_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    exit_tree_end = content.find("public void Connect()")
    exit_tree_section = content[content.find("_ExitTree()"):exit_tree_end]
    assert "OnRowChanged -= HandleRowChanged" in exit_tree_section, (
        "Regression: OnRowChanged must still be unwired in _ExitTree — "
        "all event subscriptions must be symmetric (AC 2)"
    )
