"""
Story 4.2: Surface Reducer Results and Runtime Status to Gameplay Code
Automated contract tests for all story deliverables.

Covers:
- ReducerCallResult.cs: partial class : RefCounted, ReducerName, InvocationId, CalledAt, CompletedAt,
  internal constructor (AC: 1, 2)
- ReducerCallError.cs: partial class : RefCounted, ReducerName, InvocationId, CalledAt, ErrorMessage,
  FailureCategory, RecoveryGuidance, FailedAt, internal constructor (AC: 1, 2, 3)
- ReducerFailureCategory.cs: enum with Failed, OutOfEnergy, Unknown cases (AC: 3)
- SpacetimeSdkReducerAdapter.cs: IReducerEventSink interface, RegisterCallbacks, ExtractAndDispatch,
  ConditionalWeakTable idempotency guard, correct field access for Reducers and Event,
  Status pattern match (AC: 1, 2, 3)
- SpacetimeConnectionService.cs: IReducerEventSink interface, events, RegisterCallbacks wiring,
  explicit implementations constructing result/error payloads (AC: 1, 2, 3)
- SpacetimeClient.cs: ReducerCallSucceeded/ReducerCallFailed signals, handler methods,
  _EnterTree/_ExitTree wiring, _signalAdapter.Dispatch for thread-safe dispatch (AC: 1, 2, 3)
- docs/runtime-boundaries.md: ReducerFailureCategory, ReducerCallSucceeded, ReducerCallFailed,
  RegisterCallbacks, IReducerEventSink, async delivery note (AC: 1, 2, 3)
- Dynamic lifecycle test: RegisterCallbacks(this) inside OnConnected (Epic 3 Retro P2)
- Regression guards: all Story 4.1 and 3.x deliverables intact
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# ReducerCallResult.cs (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_reducer_call_result_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs"
    assert path.exists(), (
        "ReducerCallResult.cs must exist at Public/Reducers/ReducerCallResult.cs (AC 1, 2)"
    )


def test_reducer_call_result_is_partial_class_not_record() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "partial class" in content, (
        "ReducerCallResult must be a 'partial class' — Godot signals require GodotObject-derived types, "
        "not records (AC 1, 2)"
    )
    assert "public record" not in content, (
        "ReducerCallResult must NOT be a record — Godot signal compatibility requires partial class : RefCounted"
    )


def test_reducer_call_result_extends_ref_counted() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert ": RefCounted" in content, (
        "ReducerCallResult must extend RefCounted — class declaration must contain ': RefCounted' (AC 1, 2)"
    )


def test_reducer_call_result_has_reducer_name_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "ReducerName" in content, (
        "ReducerCallResult must have a ReducerName property — identifies which reducer produced this result (AC 2)"
    )


def test_reducer_call_result_has_invocation_id_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "InvocationId" in content, (
        "ReducerCallResult must have an InvocationId property — gameplay code needs invocation-instance "
        "correlation instead of reducer-name-only matching (AC 2)"
    )


def test_reducer_call_result_has_called_at_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "CalledAt" in content, (
        "ReducerCallResult must have a CalledAt property — UTC timestamp of the accepted reducer call (AC 1, 2)"
    )


def test_reducer_call_result_has_completed_at_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "CompletedAt" in content, (
        "ReducerCallResult must have a CompletedAt property — UTC timestamp of success delivery (AC 1)"
    )


def test_reducer_call_result_has_internal_constructor() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "internal ReducerCallResult(" in content, (
        "ReducerCallResult must have an internal constructor — only the SDK creates result payloads (AC 1, 2)"
    )
    assert "string invocationId" in content and "DateTimeOffset calledAt" in content, (
        "ReducerCallResult constructor must capture invocation correlation data "
        "(string invocationId, DateTimeOffset calledAt) so success events can identify the call instance (AC 2)"
    )


def test_reducer_call_result_namespace_is_correct() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "namespace GodotSpacetime.Reducers" in content, (
        "ReducerCallResult.cs must use namespace GodotSpacetime.Reducers (AC 1)"
    )


# ---------------------------------------------------------------------------
# ReducerCallError.cs (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_reducer_call_error_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs"
    assert path.exists(), (
        "ReducerCallError.cs must exist at Public/Reducers/ReducerCallError.cs (AC 1, 2, 3)"
    )


def test_reducer_call_error_is_partial_class() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "partial class" in content, (
        "ReducerCallError must be a 'partial class' — Godot signals require GodotObject-derived types (AC 1)"
    )


def test_reducer_call_error_extends_ref_counted() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert ": RefCounted" in content, (
        "ReducerCallError must extend RefCounted — class declaration must contain ': RefCounted' (AC 1)"
    )


def test_reducer_call_error_has_reducer_name_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "ReducerName" in content, (
        "ReducerCallError must have a ReducerName property — identifies which reducer failed (AC 2)"
    )


def test_reducer_call_error_has_invocation_id_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "InvocationId" in content, (
        "ReducerCallError must have an InvocationId property — failure outcomes must identify the "
        "specific reducer invocation instance they belong to (AC 2)"
    )


def test_reducer_call_error_has_called_at_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "CalledAt" in content, (
        "ReducerCallError must have a CalledAt property — failure payloads need the original call time "
        "for async correlation (AC 1, 2)"
    )


def test_reducer_call_error_has_error_message_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "ErrorMessage" in content, (
        "ReducerCallError must have an ErrorMessage property — human-readable failure description (AC 3)"
    )


def test_reducer_call_error_has_failure_category_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "FailureCategory" in content, (
        "ReducerCallError must have a FailureCategory property — guides branching error handling (AC 3)"
    )


def test_reducer_call_error_has_recovery_guidance_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "RecoveryGuidance" in content, (
        "ReducerCallError must have a RecoveryGuidance property — AC 3 requires the failure payload "
        "to surface a user-safe retry or feedback path, not just a category enum"
    )


def test_reducer_call_error_has_failed_at_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "FailedAt" in content, (
        "ReducerCallError must have a FailedAt property — UTC timestamp of failure (AC 1)"
    )


def test_reducer_call_error_has_internal_constructor() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "internal ReducerCallError(" in content, (
        "ReducerCallError must have an internal constructor — only the SDK creates error payloads (AC 1, 3)"
    )


def test_reducer_call_error_namespace_is_correct() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "namespace GodotSpacetime.Reducers" in content, (
        "ReducerCallError.cs must use namespace GodotSpacetime.Reducers (AC 1)"
    )


# ---------------------------------------------------------------------------
# ReducerFailureCategory.cs (AC: 3)
# ---------------------------------------------------------------------------

def test_reducer_failure_category_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs"
    assert path.exists(), (
        "ReducerFailureCategory.cs must exist at Public/Reducers/ReducerFailureCategory.cs (AC 3)"
    )


def test_reducer_failure_category_declares_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs")
    assert "enum ReducerFailureCategory" in content, (
        "ReducerFailureCategory.cs must declare 'enum ReducerFailureCategory' (AC 3)"
    )


def test_reducer_failure_category_has_failed_case() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs")
    assert "Failed" in content, (
        "ReducerFailureCategory must have a 'Failed' case — server logic error or constraint (AC 3)"
    )


def test_reducer_failure_category_has_out_of_energy_case() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs")
    assert "OutOfEnergy" in content, (
        "ReducerFailureCategory must have an 'OutOfEnergy' case — server ran out of energy (AC 3)"
    )


def test_reducer_failure_category_has_unknown_case() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs")
    assert "Unknown" in content, (
        "ReducerFailureCategory must have an 'Unknown' case — defensive handling when status unavailable (AC 3)"
    )


def test_reducer_failure_category_namespace_is_correct() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs")
    assert "namespace GodotSpacetime.Reducers" in content, (
        "ReducerFailureCategory.cs must use namespace GodotSpacetime.Reducers (AC 3)"
    )


# ---------------------------------------------------------------------------
# SpacetimeSdkReducerAdapter.cs (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_reducer_adapter_has_ireducer_event_sink_interface() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "interface IReducerEventSink" in content, (
        "IReducerEventSink interface must be declared in SpacetimeSdkReducerAdapter.cs — "
        "mirrors IRowChangeEventSink in SpacetimeSdkRowCallbackAdapter.cs (AC 1, 2, 3)"
    )


def test_reducer_adapter_sink_has_on_succeeded_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "OnReducerCallSucceeded" in content, (
        "IReducerEventSink must have an OnReducerCallSucceeded method signature (AC 1)"
    )


def test_reducer_adapter_sink_has_on_failed_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "OnReducerCallFailed" in content, (
        "IReducerEventSink must have an OnReducerCallFailed method signature (AC 1, 3)"
    )


def test_reducer_adapter_has_register_callbacks_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "RegisterCallbacks" in content, (
        "SpacetimeSdkReducerAdapter must have a RegisterCallbacks method (AC 1)"
    )


def test_reducer_adapter_has_extract_and_dispatch_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "ExtractAndDispatch" in content, (
        "SpacetimeSdkReducerAdapter must have an ExtractAndDispatch static helper (AC 1, 2, 3)"
    )


def test_reducer_adapter_has_registered_reducers_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "_registeredReducers" in content, (
        "SpacetimeSdkReducerAdapter must have _registeredReducers ConditionalWeakTable — "
        "idempotency guard prevents double-registration on Degraded→Connected recovery (AC 1)"
    )


def test_reducer_adapter_has_conditional_weak_table() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "ConditionalWeakTable" in content, (
        "SpacetimeSdkReducerAdapter must use ConditionalWeakTable for idempotency guard (AC 1)"
    )


def test_reducer_adapter_uses_get_field_for_reducers() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert 'GetField("Reducers"' in content, (
        "SpacetimeSdkReducerAdapter must use GetField(\"Reducers\") — SpacetimeDB 2.1.0 exposes Reducers "
        "as a public field, not a property (same lesson as Story 3.3 field-vs-property) (AC 1)"
    )


def test_reducer_adapter_uses_event_field_access() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert '"Event"' in content, (
        "SpacetimeSdkReducerAdapter must use GetField(\"Event\") — ReducerEventContext.Event is a "
        "public readonly field, confirmed from generated SpacetimeDBClient.g.cs:121 (AC 1)"
    )


def test_reducer_adapter_has_status_committed_case() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "Status.Committed" in content, (
        "SpacetimeSdkReducerAdapter must pattern-match Status.Committed — success case (AC 1)"
    )


def test_reducer_adapter_has_status_failed_case() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "Status.Failed" in content, (
        "SpacetimeSdkReducerAdapter must pattern-match Status.Failed — server logic error (AC 3)"
    )


def test_reducer_adapter_has_status_out_of_energy_case() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "Status.OutOfEnergy" in content, (
        "SpacetimeSdkReducerAdapter must pattern-match Status.OutOfEnergy — energy failure (AC 3)"
    )


def test_reducer_adapter_has_linq_expressions_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "using System.Linq.Expressions;" in content, (
        "SpacetimeSdkReducerAdapter.cs must import System.Linq.Expressions for expression tree lambda "
        "compilation (AC 1)"
    )


def test_reducer_adapter_has_reflection_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "using System.Reflection;" in content, (
        "SpacetimeSdkReducerAdapter.cs must import System.Reflection for EventInfo / BindingFlags (AC 1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_connection_service_implements_ireducer_event_sink() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IReducerEventSink" in content, (
        "SpacetimeConnectionService must implement IReducerEventSink (AC 1)"
    )


def test_connection_service_class_declaration_includes_ireducer_event_sink() -> None:
    lines = _lines("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    class_lines = [ln for ln in lines if "class SpacetimeConnectionService" in ln]
    assert len(class_lines) > 0, "SpacetimeConnectionService class declaration not found"
    assert "IReducerEventSink" in class_lines[0], (
        "IReducerEventSink must appear in the SpacetimeConnectionService class declaration (AC 1)"
    )


def test_connection_service_has_on_reducer_call_succeeded_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnReducerCallSucceeded" in content, (
        "SpacetimeConnectionService must have an OnReducerCallSucceeded event (AC 1)"
    )


def test_connection_service_has_on_reducer_call_failed_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnReducerCallFailed" in content, (
        "SpacetimeConnectionService must have an OnReducerCallFailed event (AC 1, 3)"
    )


def test_connection_service_has_register_callbacks_wiring() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RegisterCallbacks(" in content and "SessionBoundReducerEventSink" in content, (
        "SpacetimeConnectionService must wire reducer callbacks in the connect path, and runtime hardening now "
        "requires a session-bound reducer sink instead of passing `this` directly (AC 1)."
    )


def test_connection_service_has_explicit_on_succeeded_implementation() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IReducerEventSink.OnReducerCallSucceeded" in content, (
        "SpacetimeConnectionService must have explicit IReducerEventSink.OnReducerCallSucceeded "
        "implementation (AC 1)"
    )


def test_connection_service_has_explicit_on_failed_implementation() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IReducerEventSink.OnReducerCallFailed" in content, (
        "SpacetimeConnectionService must have explicit IReducerEventSink.OnReducerCallFailed "
        "implementation (AC 1, 3)"
    )


def test_connection_service_constructs_reducer_call_result() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "new ReducerCallResult(" in content, (
        "SpacetimeConnectionService must construct ReducerCallResult — result payload creation (AC 1, 2)"
    )


def test_connection_service_constructs_reducer_call_error() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "new ReducerCallError(" in content, (
        "SpacetimeConnectionService must construct ReducerCallError — error payload creation (AC 1, 3)"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.cs (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_reducer_call_succeeded_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReducerCallSucceededEventHandler" in content, (
        "SpacetimeClient must declare ReducerCallSucceededEventHandler signal delegate (AC 1)"
    )


def test_spacetime_client_has_reducer_call_failed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReducerCallFailedEventHandler" in content, (
        "SpacetimeClient must declare ReducerCallFailedEventHandler signal delegate (AC 1, 3)"
    )


def test_spacetime_client_has_handle_reducer_call_succeeded_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleReducerCallSucceeded" in content, (
        "SpacetimeClient must have a HandleReducerCallSucceeded method (AC 1)"
    )


def test_spacetime_client_has_handle_reducer_call_failed_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleReducerCallFailed" in content, (
        "SpacetimeClient must have a HandleReducerCallFailed method (AC 1, 3)"
    )


def test_spacetime_client_wires_on_reducer_call_succeeded_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_connectionService.OnReducerCallSucceeded +=" in content, (
        "SpacetimeClient must wire OnReducerCallSucceeded in _EnterTree (AC 1)"
    )


def test_spacetime_client_wires_on_reducer_call_failed_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_connectionService.OnReducerCallFailed +=" in content, (
        "SpacetimeClient must wire OnReducerCallFailed in _EnterTree (AC 1, 3)"
    )


def test_spacetime_client_unwires_on_reducer_call_succeeded_in_exit_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_connectionService.OnReducerCallSucceeded -=" in content, (
        "SpacetimeClient must unwire OnReducerCallSucceeded in _ExitTree (AC 1)"
    )


def test_spacetime_client_unwires_on_reducer_call_failed_in_exit_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_connectionService.OnReducerCallFailed -=" in content, (
        "SpacetimeClient must unwire OnReducerCallFailed in _ExitTree (AC 1, 3)"
    )


def test_spacetime_client_emits_reducer_call_succeeded_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "EmitSignal(SignalName.ReducerCallSucceeded" in content, (
        "SpacetimeClient must emit ReducerCallSucceeded signal in the handler (AC 1)"
    )


def test_spacetime_client_emits_reducer_call_failed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "EmitSignal(SignalName.ReducerCallFailed" in content, (
        "SpacetimeClient must emit ReducerCallFailed signal in the handler (AC 1, 3)"
    )


def test_spacetime_client_uses_signal_adapter_dispatch_for_reducer_succeeded() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_signalAdapter.Dispatch" in content, (
        "SpacetimeClient must use _signalAdapter.Dispatch for thread-safe deferred dispatch in "
        "reducer signal handlers (AC 1)"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_mentions_reducer_call_result() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallResult" in content, (
        "docs/runtime-boundaries.md must document ReducerCallResult (AC 1, 2)"
    )


def test_runtime_boundaries_mentions_reducer_call_error() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallError" in content, (
        "docs/runtime-boundaries.md must document ReducerCallError (AC 1, 3)"
    )


def test_runtime_boundaries_mentions_reducer_failure_category() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerFailureCategory" in content, (
        "docs/runtime-boundaries.md must document ReducerFailureCategory enum (AC 3)"
    )


def test_runtime_boundaries_mentions_reducer_call_succeeded() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallSucceeded" in content, (
        "docs/runtime-boundaries.md must document ReducerCallSucceeded signal (AC 1)"
    )


def test_runtime_boundaries_mentions_reducer_call_failed() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallFailed" in content, (
        "docs/runtime-boundaries.md must document ReducerCallFailed signal (AC 1, 3)"
    )


def test_runtime_boundaries_mentions_register_callbacks() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "RegisterCallbacks" in content, (
        "docs/runtime-boundaries.md must document RegisterCallbacks in the reducer results path (AC 1)"
    )


def test_runtime_boundaries_mentions_ireducer_event_sink() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "IReducerEventSink" in content, (
        "docs/runtime-boundaries.md must document IReducerEventSink as the boundary interface (AC 1)"
    )


def test_runtime_boundaries_documents_async_result_delivery() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "asynchronous" in content.lower() or "async" in content.lower(), (
        "docs/runtime-boundaries.md must note that reducer results arrive asynchronously — "
        "key concept for gameplay code (AC 1)"
    )


# ---------------------------------------------------------------------------
# Dynamic lifecycle test: RegisterCallbacks inside OnConnected (Epic 3 Retro P2)
# ---------------------------------------------------------------------------

def test_register_callbacks_inside_on_connected() -> None:
    """
    Dynamic lifecycle test (Epic 3 Retro P2):
    Verifies that the reducer callback wiring still happens inside the OnConnected
    method body in SpacetimeConnectionService — not just anywhere in the file.
    """
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    handle_connected = content.split("private void HandleConnected(", 1)
    assert len(handle_connected) == 2, (
        "SpacetimeConnectionService must keep a dedicated HandleConnected(...) connect-path helper."
    )
    handle_connected_body = handle_connected[1].split("private void HandleConnectError", 1)[0]

    assert "RegisterCallbacks(new SessionBoundReducerEventSink(this, sessionId))" in handle_connected_body, (
        "Reducer callback wiring must appear inside OnConnected() — runtime hardening still requires the live "
        "connection injection window, but now through a session-bound sink (Epic 3 Retro P2, AC 1)."
    )


# ---------------------------------------------------------------------------
# Regression guards — Story 4.1 deliverables intact
# ---------------------------------------------------------------------------

def test_regression_4_1_invoke_reducer_in_service() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "InvokeReducer" in content, (
        "Regression 4.1: InvokeReducer must still be present in SpacetimeConnectionService"
    )


def test_regression_4_1_invoke_reducer_in_client() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "InvokeReducer" in content, (
        "Regression 4.1: InvokeReducer must still be present in SpacetimeClient"
    )


def test_regression_4_1_reducer_invoker_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs"
    assert path.exists(), (
        "Regression 4.1: ReducerInvoker.cs must still exist"
    )


def test_regression_4_1_reducer_adapter_invoke_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "internal void Invoke(" in content, (
        "Regression 4.1: SpacetimeSdkReducerAdapter.Invoke must still be present"
    )


def test_regression_4_1_reducer_adapter_set_connection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "internal void SetConnection(" in content, (
        "Regression 4.1: SpacetimeSdkReducerAdapter.SetConnection must still be present"
    )


def test_regression_4_1_reducer_adapter_clear_connection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "internal void ClearConnection(" in content, (
        "Regression 4.1: SpacetimeSdkReducerAdapter.ClearConnection must still be present"
    )


def test_regression_3x_subscription_applied_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionApplied" in content, (
        "Regression 3.x: SubscriptionApplied signal must still be present in SpacetimeClient"
    )


def test_regression_3x_subscription_failed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionFailed" in content, (
        "Regression 3.x: SubscriptionFailed signal must still be present in SpacetimeClient"
    )


def test_regression_3x_row_changed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "RowChanged" in content, (
        "Regression 3.x: RowChanged signal must still be present in SpacetimeClient"
    )


def test_regression_3x_get_rows_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "GetRows" in content, (
        "Regression 3.x: GetRows must still be present in SpacetimeClient"
    )


def test_regression_3x_subscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public SubscriptionHandle Subscribe(" in content, (
        "Regression 3.x: Subscribe must still be present in SpacetimeClient"
    )


def test_regression_3x_replace_subscription_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReplaceSubscription" in content, (
        "Regression 3.x: ReplaceSubscription must still be present in SpacetimeClient"
    )


# ---------------------------------------------------------------------------
# Gap coverage: ReducerCallResult.cs — precise property types and imports
# ---------------------------------------------------------------------------

def test_reducer_call_result_called_at_is_date_time_offset() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "DateTimeOffset CalledAt" in content, (
        "ReducerCallResult.CalledAt must be typed 'DateTimeOffset' — UTC timestamp for the accepted "
        "reducer call; a different type would break async correlation semantics (AC 1, 2)"
    )


def test_reducer_call_result_reducer_name_is_string() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "string ReducerName" in content, (
        "ReducerCallResult.ReducerName must be typed 'string' — identifies which reducer produced "
        "this result and must be passable to GDScript without boxing (AC 2)"
    )


def test_reducer_call_result_invocation_id_is_string() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "string InvocationId" in content, (
        "ReducerCallResult.InvocationId must be typed 'string' — an opaque string identifier is easy "
        "to compare from both C# and GDScript without custom marshaling (AC 2)"
    )


def test_reducer_call_result_completed_at_is_date_time_offset() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "DateTimeOffset CompletedAt" in content, (
        "ReducerCallResult.CompletedAt must be typed 'DateTimeOffset' — success delivery time needs a "
        "stable timestamp type for telemetry and debugging (AC 1)"
    )


def test_reducer_call_result_has_system_import() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert "using System;" in content, (
        "ReducerCallResult.cs must import System for DateTimeOffset (AC 1)"
    )


# ---------------------------------------------------------------------------
# Gap coverage: ReducerCallError.cs — precise constructor signature and types
# ---------------------------------------------------------------------------

def test_reducer_call_error_internal_constructor_has_correct_params() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "internal ReducerCallError(" in content, (
        "ReducerCallError must have an internal constructor — only the SDK creates error payloads (AC 1, 3)"
    )
    assert all(
        fragment in content
        for fragment in (
            "string invocationId",
            "DateTimeOffset calledAt",
            "ReducerFailureCategory failureCategory",
            "string recoveryGuidance",
        )
    ), (
        "ReducerCallError constructor must capture invocation correlation and recovery guidance "
        "(invocationId, calledAt, failureCategory, recoveryGuidance) so AC 2 and AC 3 are surfaced "
        "through the failure payload"
    )


def test_reducer_call_error_failed_at_is_date_time_offset() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "DateTimeOffset FailedAt" in content, (
        "ReducerCallError.FailedAt must be typed 'DateTimeOffset' — UTC timestamp for failure "
        "arrival; must match ReducerCallResult.CalledAt type for symmetric pattern (AC 1)"
    )


def test_reducer_call_error_called_at_is_date_time_offset() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "DateTimeOffset CalledAt" in content, (
        "ReducerCallError.CalledAt must be typed 'DateTimeOffset' — failure payloads need the original "
        "call timestamp for async correlation with gameplay state (AC 1, 2)"
    )


def test_reducer_call_error_invocation_id_is_string() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "string InvocationId" in content, (
        "ReducerCallError.InvocationId must be typed 'string' — an opaque string identifier keeps the "
        "failure surface Godot-friendly while distinguishing invocation instances (AC 2)"
    )


def test_reducer_call_error_failure_category_typed_as_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "ReducerFailureCategory FailureCategory" in content, (
        "ReducerCallError.FailureCategory must be typed 'ReducerFailureCategory' — typed enum "
        "required for GDScript switch-on-value branching; 'object' or 'int' would break AC 3"
    )


def test_reducer_call_error_recovery_guidance_is_string() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "string RecoveryGuidance" in content, (
        "ReducerCallError.RecoveryGuidance must be typed 'string' — AC 3 requires a user-safe feedback "
        "path that gameplay code can present directly without runtime-specific mapping"
    )


# ---------------------------------------------------------------------------
# Gap coverage: ReducerFailureCategory.cs — isolation and case count
# ---------------------------------------------------------------------------

def test_reducer_failure_category_has_no_spacetime_db_dependency() -> None:
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs")
    assert "SpacetimeDB" not in content, (
        "ReducerFailureCategory.cs must NOT import or reference SpacetimeDB — it is a pure "
        "GodotSpacetime public type with no runtime dependency; SpacetimeDB.Status mapping "
        "happens only inside SpacetimeSdkReducerAdapter (isolation zone, AC 3)"
    )


def test_reducer_failure_category_has_exactly_three_cases() -> None:
    lines = _lines("addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs")
    # Match stripped enum member lines: trailing comma allowed, no extra tokens
    enum_cases = [
        ln for ln in lines
        if ln.rstrip(",") in ("Failed", "OutOfEnergy", "Unknown")
    ]
    assert len(enum_cases) == 3, (
        f"ReducerFailureCategory must have exactly 3 cases (Failed, OutOfEnergy, Unknown), "
        f"found {len(enum_cases)} — extra cases require a dedicated story (AC 3)"
    )


# ---------------------------------------------------------------------------
# Gap coverage: SpacetimeSdkReducerAdapter.cs — structural details
# ---------------------------------------------------------------------------

def test_reducer_adapter_is_sealed_class() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "internal sealed class SpacetimeSdkReducerAdapter" in content, (
        "SpacetimeSdkReducerAdapter must be 'internal sealed class' — sealed prevents unintended "
        "subclassing inside the isolation zone (AC 1)"
    )


def test_reducer_adapter_has_spacetime_db_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "using SpacetimeDB;" in content, (
        "SpacetimeSdkReducerAdapter.cs must import SpacetimeDB — Status pattern-match and "
        "IReducerArgs cast both require it; removing this import breaks the isolation boundary (AC 1, 3)"
    )


def test_reducer_adapter_has_godot_spacetime_reducers_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "using GodotSpacetime.Reducers;" in content, (
        "SpacetimeSdkReducerAdapter.cs must import GodotSpacetime.Reducers to reference "
        "ReducerFailureCategory in ExtractAndDispatch and in the IReducerEventSink interface (AC 3)"
    )


def test_reducer_adapter_has_runtime_compile_services_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "using System.Runtime.CompilerServices;" in content, (
        "SpacetimeSdkReducerAdapter.cs must import System.Runtime.CompilerServices for "
        "ConditionalWeakTable (the idempotency guard type) (AC 1)"
    )


def test_reducer_adapter_namespace_is_runtime_platform_dot_net() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "namespace GodotSpacetime.Runtime.Platform.DotNet;" in content, (
        "SpacetimeSdkReducerAdapter.cs must use namespace GodotSpacetime.Runtime.Platform.DotNet — "
        "correctly placed in the internal runtime isolation zone (AC 1)"
    )


def test_reducer_adapter_extract_and_dispatch_is_private_instance_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "private void ExtractAndDispatch" in content, (
        "ExtractAndDispatch must be a private instance method — callback dispatch now needs access to "
        "adapter-owned pending invocation state while remaining outside the public/internal API surface (AC 1, 2)"
    )


def test_reducer_adapter_has_default_status_case() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "default:" in content, (
        "SpacetimeSdkReducerAdapter.ExtractAndDispatch must have a 'default:' case in the status "
        "switch — defensive handling for unexpected SDK status values routes to Unknown category (AC 3)"
    )


def test_reducer_adapter_tracks_pending_invocations() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "_pendingInvocations" in content and "TrackPendingInvocation" in content and "TakePendingInvocation" in content, (
        "SpacetimeSdkReducerAdapter must track pending reducer invocations so callbacks can surface "
        "InvocationId and CalledAt for the correct reducer call instance (AC 2)"
    )


def test_reducer_adapter_ireducer_sink_succeeded_takes_string_reducer_name() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert (
        "void OnReducerCallSucceeded(string reducerName, string invocationId, DateTimeOffset calledAt)"
        in content
    ), (
        "IReducerEventSink.OnReducerCallSucceeded must take reducerName, invocationId, and calledAt — "
        "success callbacks need operation and invocation-instance correlation data (AC 2)"
    )


def test_reducer_adapter_ireducer_sink_failed_takes_three_params() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert all(
        fragment in content
        for fragment in (
            "void OnReducerCallFailed(",
            "string reducerName",
            "string invocationId",
            "DateTimeOffset calledAt",
            "string errorMessage",
            "ReducerFailureCategory failureCategory",
            "string recoveryGuidance",
        )
    ), (
        "IReducerEventSink.OnReducerCallFailed must take reducerName, invocationId, calledAt, "
        "errorMessage, failureCategory, and recoveryGuidance so the failure surface satisfies AC 2 and AC 3"
    )
 

def test_reducer_adapter_surfaces_recovery_guidance() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "GetRecoveryGuidance" in content and "recoveryGuidance" in content, (
        "SpacetimeSdkReducerAdapter must derive user-safe recovery guidance inside the isolation zone "
        "before surfacing failure payloads through IReducerEventSink (AC 3)"
    )


# ---------------------------------------------------------------------------
# Gap coverage: SpacetimeConnectionService.cs — event types and call ordering
# ---------------------------------------------------------------------------

def test_connection_service_on_reducer_call_succeeded_event_type() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "event Action<ReducerCallResult>?" in content, (
        "SpacetimeConnectionService.OnReducerCallSucceeded must be typed 'event Action<ReducerCallResult>?' "
        "— mirrors OnSubscriptionApplied pattern; a wrong generic param breaks the SpacetimeClient wiring (AC 1)"
    )


def test_connection_service_on_reducer_call_failed_event_type() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "event Action<ReducerCallError>?" in content, (
        "SpacetimeConnectionService.OnReducerCallFailed must be typed 'event Action<ReducerCallError>?' "
        "— mirrors OnSubscriptionFailed pattern; a wrong generic param breaks the SpacetimeClient wiring (AC 1, 3)"
    )


def test_connection_service_has_reducers_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "using GodotSpacetime.Reducers;" in content, (
        "SpacetimeConnectionService.cs must import GodotSpacetime.Reducers to reference "
        "ReducerCallResult and ReducerCallError in the event declarations and explicit implementations (AC 1)"
    )


def test_connection_service_set_connection_before_register_callbacks() -> None:
    """
    SetConnection must appear before RegisterCallbacks in the file to preserve the
    OnConnected call order: adapter must have a live connection before callbacks are wired.
    """
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    set_pos = content.find("_reducerAdapter.SetConnection(")
    reg_pos = content.find("_reducerAdapter.RegisterCallbacks(")
    assert set_pos != -1, "_reducerAdapter.SetConnection must be present"
    assert reg_pos != -1, "_reducerAdapter.RegisterCallbacks must be present"
    assert set_pos < reg_pos, (
        "_reducerAdapter.SetConnection must appear before _reducerAdapter.RegisterCallbacks — "
        "the adapter needs a live connection reference before callbacks can be wired (AC 1, Epic 3 Retro P2)"
    )


# ---------------------------------------------------------------------------
# Gap coverage: SpacetimeClient.cs — import, delegate params, dispatch lambdas
# ---------------------------------------------------------------------------

def test_spacetime_client_has_reducers_import() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "using GodotSpacetime.Reducers;" in content, (
        "SpacetimeClient.cs must import GodotSpacetime.Reducers to reference ReducerCallResult and "
        "ReducerCallError in signal delegate declarations and handler method signatures (AC 1)"
    )


def test_spacetime_client_reducer_call_succeeded_signal_takes_reducer_call_result() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReducerCallSucceededEventHandler(ReducerCallResult result)" in content, (
        "ReducerCallSucceededEventHandler delegate must take 'ReducerCallResult result' — "
        "gameplay code receives the full result object with ReducerName, InvocationId, and CalledAt (AC 1, 2)"
    )


def test_spacetime_client_reducer_call_failed_signal_takes_reducer_call_error() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReducerCallFailedEventHandler(ReducerCallError error)" in content, (
        "ReducerCallFailedEventHandler delegate must take 'ReducerCallError error' — "
        "gameplay code receives FailureCategory, RecoveryGuidance, InvocationId, and ReducerName for branching (AC 1, 2, 3)"
    )


def test_spacetime_client_handlers_have_null_check_for_signal_adapter() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_signalAdapter == null" in content, (
        "SpacetimeClient reducer signal handlers must guard against null _signalAdapter — "
        "fallback to synchronous EmitSignal when the adapter is not yet wired (AC 1)"
    )


def test_spacetime_client_reducer_succeeded_dispatch_uses_lambda() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_signalAdapter.Dispatch(() => EmitSignal(SignalName.ReducerCallSucceeded" in content, (
        "HandleReducerCallSucceeded must use '_signalAdapter.Dispatch(() => EmitSignal(SignalName.ReducerCallSucceeded' "
        "lambda — ensures the signal fires on the main thread via CallDeferred (AC 1)"
    )


def test_spacetime_client_reducer_failed_dispatch_uses_lambda() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_signalAdapter.Dispatch(() => EmitSignal(SignalName.ReducerCallFailed" in content, (
        "HandleReducerCallFailed must use '_signalAdapter.Dispatch(() => EmitSignal(SignalName.ReducerCallFailed' "
        "lambda — ensures the signal fires on the main thread via CallDeferred (AC 1, 3)"
    )


# ---------------------------------------------------------------------------
# Gap coverage: docs/runtime-boundaries.md — completeness of result-path docs
# ---------------------------------------------------------------------------

def test_runtime_boundaries_documents_extract_and_dispatch() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ExtractAndDispatch" in content, (
        "docs/runtime-boundaries.md must document ExtractAndDispatch in the reducer results path — "
        "this is the critical isolation-zone dispatch step (AC 1)"
    )


def test_runtime_boundaries_documents_isolation_zone() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Isolation zone" in content or "isolation zone" in content, (
        "docs/runtime-boundaries.md must document the isolation zone concept for the reducer path — "
        "SpacetimeDB.* types referenced only inside SpacetimeSdkReducerAdapter (AC 1, 2, 3)"
    )


def test_runtime_boundaries_documents_reducer_call_result_reducer_name_property() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerName" in content, (
        "docs/runtime-boundaries.md must document ReducerCallResult.ReducerName — "
        "lets gameplay code identify which reducer outcome arrived (AC 2)"
    )


def test_runtime_boundaries_documents_reducer_call_result_invocation_id_property() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "InvocationId" in content, (
        "docs/runtime-boundaries.md must document InvocationId — gameplay code needs an explicit "
        "invocation-instance correlation key rather than reducer-name-only matching (AC 2)"
    )


def test_runtime_boundaries_documents_reducer_call_result_called_at_property() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "CalledAt" in content, (
        "docs/runtime-boundaries.md must document ReducerCallResult.CalledAt — "
        "UTC timestamp for invocation identification (AC 1)"
    )


def test_runtime_boundaries_documents_reducer_call_result_completed_at_property() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "CompletedAt" in content, (
        "docs/runtime-boundaries.md must document ReducerCallResult.CompletedAt — gameplay code and "
        "telemetry need the async success-delivery timestamp (AC 1)"
    )


def test_runtime_boundaries_documents_reducer_call_error_error_message_property() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ErrorMessage" in content, (
        "docs/runtime-boundaries.md must document ReducerCallError.ErrorMessage — "
        "human-readable failure description for gameplay feedback (AC 3)"
    )


def test_runtime_boundaries_documents_reducer_call_error_recovery_guidance_property() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "RecoveryGuidance" in content, (
        "docs/runtime-boundaries.md must document ReducerCallError.RecoveryGuidance — AC 3 requires "
        "the failure payload to include a user-safe retry or feedback path"
    )


def test_runtime_boundaries_documents_reducer_call_error_failed_at_property() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "FailedAt" in content, (
        "docs/runtime-boundaries.md must document ReducerCallError.FailedAt — "
        "UTC timestamp for failure event logging and correlation (AC 1)"
    )


def test_runtime_boundaries_documents_pending_invocation_tracking() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "TrackPendingInvocation" in content and "TakePendingInvocation" in content, (
        "docs/runtime-boundaries.md must document the pending-invocation correlation path so the "
        "reviewed reducer surface clearly explains how InvocationId is preserved across async callbacks"
    )


def test_runtime_boundaries_documents_main_thread_dispatch() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "GodotSignalAdapter" in content or "main thread" in content.lower(), (
        "docs/runtime-boundaries.md must document thread-safe signal dispatch — "
        "gameplay code must know ReducerCallSucceeded/Failed signals are safe to access the scene tree (AC 1)"
    )
