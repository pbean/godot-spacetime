"""
Story 4.1: Invoke Generated Reducers from the Godot-Facing SDK
Automated contract tests for all story deliverables.

Covers:
- SpacetimeSdkReducerAdapter.cs: file exists, Invoke/SetConnection/ClearConnection methods present,
  using SpacetimeDB import present, old pragma-suppressed dead field is gone (AC: 1, 2)
- ReducerInvoker.cs: file exists, correct namespace, class present, Invoke method present,
  NO SpacetimeDB import (AC: 1, 2)
- SpacetimeConnectionService.cs: _reducerAdapter field present, _reducerInvoker field present,
  InvokeReducer method present, SetConnection call in connect path, ClearConnection in
  ResetDisconnectedSessionState (AC: 1, 3)
- SpacetimeClient.cs: InvokeReducer method present, delegation to _connectionService.InvokeReducer (AC: 1, 2, 3)
- docs/runtime-boundaries.md: InvokeReducer, ReducerInvoker, SpacetimeSdkReducerAdapter mentioned (AC: 1, 3)
- Review regression guards: concrete-type reducer dispatch compiles against the SDK generic method
  and invalid reducer argument types are surfaced through the Godot-facing validation path
- Dynamic lifecycle test: ClearConnection inside ResetDisconnectedSessionState (Epic 3 Retro P1/P2)
- Regression guards: prior story deliverables intact (AC: 1, 2, 3)
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# SpacetimeSdkReducerAdapter.cs (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_reducer_adapter_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    assert path.exists(), (
        "SpacetimeSdkReducerAdapter.cs must exist at Internal/Platform/DotNet/ (AC 1, 2)"
    )


def test_reducer_adapter_has_invoke_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "void Invoke(" in content, (
        "SpacetimeSdkReducerAdapter must have an Invoke method (AC 1, 2)"
    )


def test_reducer_adapter_has_set_connection_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "void SetConnection(" in content, (
        "SpacetimeSdkReducerAdapter must have a SetConnection method (AC 1)"
    )


def test_reducer_adapter_has_clear_connection_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "void ClearConnection(" in content, (
        "SpacetimeSdkReducerAdapter must have a ClearConnection method (AC 1)"
    )


def test_reducer_adapter_has_spacetimedb_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "using SpacetimeDB;" in content, (
        "SpacetimeSdkReducerAdapter.cs must import SpacetimeDB — it is the isolation zone (AC 1, 2)"
    )


def test_reducer_adapter_no_pragma_warning_suppress() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "#pragma warning disable CS0169" not in content, (
        "Old pragma-suppressed dead field must be removed — _dbConnection is now actively used (AC 1)"
    )


def test_reducer_adapter_invoke_takes_object_arg() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "Invoke(object reducerArgs)" in content, (
        "SpacetimeSdkReducerAdapter.Invoke must accept 'object reducerArgs' (AC 1, 2)"
    )


def test_reducer_adapter_invokes_internal_call_reducer() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "InternalCallReducer" in content, (
        "SpacetimeSdkReducerAdapter.Invoke must call IDbConnection.InternalCallReducer (AC 1)"
    )


def test_reducer_adapter_casts_to_ireducer_args() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "IReducerArgs" in content, (
        "SpacetimeSdkReducerAdapter.Invoke must cast reducerArgs to IReducerArgs at the boundary (AC 2)"
    )


def test_reducer_adapter_set_connection_is_internal() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "internal void SetConnection(" in content, (
        "SetConnection must be internal (AC 1)"
    )


def test_reducer_adapter_invoke_is_internal() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "internal void Invoke(" in content, (
        "Invoke must be internal (AC 1, 2)"
    )


def test_reducer_adapter_clear_connection_is_internal() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "internal void ClearConnection(" in content, (
        "ClearConnection must be internal (AC 1)"
    )


# ---------------------------------------------------------------------------
# ReducerInvoker.cs (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_reducer_invoker_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs"
    assert path.exists(), (
        "ReducerInvoker.cs must exist at Internal/Reducers/ReducerInvoker.cs (AC 1, 2)"
    )


def test_reducer_invoker_namespace_is_correct() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    assert "namespace GodotSpacetime.Runtime.Reducers" in content, (
        "ReducerInvoker.cs must use namespace GodotSpacetime.Runtime.Reducers (AC 1)"
    )


def test_reducer_invoker_class_is_present() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    assert "class ReducerInvoker" in content, (
        "File must declare 'class ReducerInvoker' (AC 1, 2)"
    )


def test_reducer_invoker_class_is_internal_sealed() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    assert "internal sealed class ReducerInvoker" in content, (
        "ReducerInvoker must be 'internal sealed class' (AC 1)"
    )


def test_reducer_invoker_has_invoke_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    assert "void Invoke(" in content, (
        "ReducerInvoker must have an Invoke method (AC 1, 2)"
    )


def test_reducer_invoker_no_spacetimedb_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    assert "using SpacetimeDB" not in content, (
        "ReducerInvoker.cs must NOT import SpacetimeDB — isolation zone is SpacetimeSdkReducerAdapter only (AC 1, 2)"
    )


def test_reducer_invoker_no_spacetimedb_reference_in_body() -> None:
    # Check that no non-comment code line references SpacetimeDB types directly.
    # Doc comments may mention "SpacetimeDB.*" as constraint documentation — that is allowed.
    lines = _lines("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    code_lines_with_spacetimedb = [
        ln for ln in lines
        if "SpacetimeDB." in ln and not ln.startswith("//") and not ln.startswith("///") and not ln.startswith("*")
    ]
    assert len(code_lines_with_spacetimedb) == 0, (
        "ReducerInvoker must NOT reference SpacetimeDB.* types in code (comments allowed for documentation): "
        + str(code_lines_with_spacetimedb)
    )


def test_reducer_invoker_invoke_takes_object_arg() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    assert "Invoke(object reducerArgs)" in content, (
        "ReducerInvoker.Invoke must accept 'object reducerArgs' (AC 1, 2)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_connection_service_has_reducer_adapter_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_reducerAdapter" in content, (
        "SpacetimeConnectionService must have a _reducerAdapter field (AC 1)"
    )


def test_connection_service_has_reducer_invoker_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_reducerInvoker" in content, (
        "SpacetimeConnectionService must have a _reducerInvoker field (AC 1)"
    )


def test_connection_service_has_invoke_reducer_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "void InvokeReducer(" in content, (
        "SpacetimeConnectionService must have an InvokeReducer method (AC 1, 3)"
    )


def test_connection_service_invoke_reducer_is_public() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "public void InvokeReducer(" in content, (
        "SpacetimeConnectionService.InvokeReducer must be public (AC 1, 3)"
    )


def test_connection_service_set_connection_call_in_connect_path() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_reducerAdapter.SetConnection(" in content, (
        "SpacetimeConnectionService must call _reducerAdapter.SetConnection in the connect path (AC 1)"
    )


def test_connection_service_clear_connection_in_reset_state() -> None:
    """
    Dynamic lifecycle test (Epic 3 Retro action P2):
    Verifies ClearConnection is inside ResetDisconnectedSessionState — the shared teardown
    method that covers both explicit disconnect and connection-lost paths.
    """
    lines = _lines("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")

    # Find the ResetDisconnectedSessionState method body
    in_method = False
    found_clear = False
    brace_depth = 0

    for line in lines:
        if "ResetDisconnectedSessionState()" in line and "private" in line:
            in_method = True
            brace_depth = 0
            continue

        if in_method:
            brace_depth += line.count("{") - line.count("}")
            if "_reducerAdapter.ClearConnection()" in line:
                found_clear = True
            if brace_depth < 0:
                # Exited the method body
                break

    assert found_clear, (
        "ClearConnection() must appear inside ResetDisconnectedSessionState() — "
        "this shared teardown covers both explicit disconnect and connection-lost paths "
        "(Epic 3 Retro action P1/P2, AC 1)"
    )


def test_connection_service_invoke_reducer_checks_connected_state() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "InvokeReducer() requires an active Connected session" in content, (
        "SpacetimeConnectionService.InvokeReducer must check ConnectionState.Connected and throw (AC 1, 3)"
    )


def test_connection_service_no_spacetimedb_import() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "using SpacetimeDB" not in content, (
        "SpacetimeConnectionService must NOT import SpacetimeDB — isolation zone is the adapter (AC 1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.cs (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_invoke_reducer_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "void InvokeReducer(" in content, (
        "SpacetimeClient must have an InvokeReducer method (AC 1, 2, 3)"
    )


def test_spacetime_client_invoke_reducer_is_public() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public void InvokeReducer(" in content, (
        "SpacetimeClient.InvokeReducer must be public (AC 1, 2, 3)"
    )


def test_spacetime_client_invoke_reducer_delegates_to_service() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_connectionService.InvokeReducer(" in content, (
        "SpacetimeClient.InvokeReducer must delegate to _connectionService.InvokeReducer (AC 1, 2, 3)"
    )


def test_spacetime_client_invoke_reducer_takes_object_arg() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "InvokeReducer(object reducerArgs)" in content, (
        "SpacetimeClient.InvokeReducer must accept 'object reducerArgs' (AC 1, 2)"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_mentions_invoke_reducer() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "InvokeReducer" in content, (
        "docs/runtime-boundaries.md must document the InvokeReducer entry point (AC 1, 3)"
    )


def test_runtime_boundaries_mentions_reducer_invoker() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerInvoker" in content, (
        "docs/runtime-boundaries.md must document ReducerInvoker in the invocation path (AC 1)"
    )


def test_runtime_boundaries_mentions_spacetime_sdk_reducer_adapter() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "SpacetimeSdkReducerAdapter" in content, (
        "docs/runtime-boundaries.md must document SpacetimeSdkReducerAdapter as the isolation adapter (AC 1)"
    )


# ---------------------------------------------------------------------------
# Regression guards — prior story deliverables intact (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_regression_subscription_applied_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionApplied" in content, (
        "Regression: SubscriptionApplied signal must still be present in SpacetimeClient"
    )


def test_regression_subscription_failed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionFailed" in content, (
        "Regression: SubscriptionFailed signal must still be present in SpacetimeClient"
    )


def test_regression_row_changed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "RowChanged" in content, (
        "Regression: RowChanged signal must still be present in SpacetimeClient"
    )


def test_regression_get_rows_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "GetRows" in content, (
        "Regression: GetRows must still be present in SpacetimeClient"
    )


def test_regression_subscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public SubscriptionHandle Subscribe(" in content, (
        "Regression: Subscribe must still be present in SpacetimeClient"
    )


def test_regression_unsubscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public void Unsubscribe(" in content, (
        "Regression: Unsubscribe must still be present in SpacetimeClient"
    )


def test_regression_replace_subscription_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReplaceSubscription" in content, (
        "Regression: ReplaceSubscription must still be present in SpacetimeClient"
    )


def test_regression_subscription_status_type_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs"
    assert path.exists(), (
        "Regression: SubscriptionStatus.cs must still exist"
    )


def test_regression_subscription_handle_has_status() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "SubscriptionStatus" in content, (
        "Regression: SubscriptionHandle must still have SubscriptionStatus property"
    )


def test_regression_pending_replacements_in_service() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_pendingReplacements" in content, (
        "Regression: _pendingReplacements must still be present in SpacetimeConnectionService"
    )


def test_regression_try_get_entry_in_registry() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "TryGetEntry" in content, (
        "Regression: TryGetEntry must still be used in SpacetimeConnectionService"
    )


def test_regression_on_subscription_failed_event_in_service() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnSubscriptionFailed" in content, (
        "Regression: OnSubscriptionFailed event must still be present in SpacetimeConnectionService"
    )


# ---------------------------------------------------------------------------
# Gap coverage — behavioral contracts not covered by the story's task 6 checklist
# ---------------------------------------------------------------------------

def test_reducer_adapter_class_is_internal_sealed() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "internal sealed class SpacetimeSdkReducerAdapter" in content, (
        "SpacetimeSdkReducerAdapter must be 'internal sealed class' (AC 1, 2)"
    )


def test_reducer_adapter_has_db_connection_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "_dbConnection" in content, (
        "SpacetimeSdkReducerAdapter must declare a _dbConnection field to hold the active connection (AC 1)"
    )


def test_reducer_adapter_invoke_guards_null_connection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "_dbConnection == null" in content or "_dbConnection is null" in content, (
        "SpacetimeSdkReducerAdapter.Invoke must guard against a null connection and return silently (AC 1)"
    )


def test_reducer_adapter_invoke_throws_for_non_reducer_args_type() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "ArgumentException" in content, (
        "SpacetimeSdkReducerAdapter.Invoke must throw ArgumentException when reducerArgs does not "
        "implement IReducerArgs — type validation at the isolation boundary (AC 2)"
    )


def test_reducer_adapter_uses_concrete_type_dispatch_for_internal_call_reducer() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs")
    assert "dynamic typedReducerArgs = reducerArgs;" in content and \
           "_dbConnection.InternalCallReducer(typedReducerArgs);" in content, (
        "SpacetimeSdkReducerAdapter.Invoke must dispatch InternalCallReducer using the concrete "
        "generated reducer type so the SDK generic constraint compiles"
    )


def test_reducer_invoker_constructor_takes_adapter_parameter() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    assert "ReducerInvoker(SpacetimeSdkReducerAdapter" in content, (
        "ReducerInvoker constructor must accept a SpacetimeSdkReducerAdapter parameter "
        "to support constructor injection from SpacetimeConnectionService (AC 1)"
    )


def test_reducer_invoker_invoke_throws_for_null_reducer_args() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    assert "ArgumentNullException.ThrowIfNull(reducerArgs)" in content or \
           ("ArgumentNullException" in content and "reducerArgs" in content), (
        "ReducerInvoker.Invoke must throw ArgumentNullException when reducerArgs is null (AC 2)"
    )


def test_reducer_invoker_invoke_delegates_to_adapter() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs")
    assert "_adapter.Invoke(reducerArgs)" in content, (
        "ReducerInvoker.Invoke must delegate to _adapter.Invoke(reducerArgs) to route through the adapter (AC 1)"
    )


def test_connection_service_reducer_invoker_injected_with_reducer_adapter() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "new ReducerInvoker(_reducerAdapter)" in content, (
        "SpacetimeConnectionService must construct ReducerInvoker by injecting _reducerAdapter "
        "so both share the same adapter instance (AC 1)"
    )


def test_connection_service_invoke_reducer_delegates_to_invoker() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_reducerInvoker.Invoke(" in content, (
        "SpacetimeConnectionService.InvokeReducer must delegate to _reducerInvoker.Invoke() "
        "to route through the ReducerInvoker → adapter chain (AC 1)"
    )


def test_spacetime_client_invoke_reducer_catches_argument_null_exception() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "catch (ArgumentNullException" in content, (
        "SpacetimeClient.InvokeReducer must catch ArgumentNullException and route to "
        "PublishValidationFailure — mirrors the ReplaceSubscription error-handling pattern (AC 2, 3)"
    )


def test_spacetime_client_invoke_reducer_catches_argument_exception() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "catch (ArgumentException" in content, (
        "SpacetimeClient.InvokeReducer must catch ArgumentException from invalid reducer argument "
        "types and route it through PublishValidationFailure (AC 2, 3)"
    )


def test_runtime_boundaries_mentions_ireducer_args() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "IReducerArgs" in content, (
        "docs/runtime-boundaries.md must document IReducerArgs as the required type for reducer arguments (AC 2)"
    )


def test_runtime_boundaries_mentions_invalid_reducer_argument_guard() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "non-`IReducerArgs` object" in content, (
        "docs/runtime-boundaries.md must explain that invalid reducer argument objects surface as "
        "validation failures on the Godot-facing boundary"
    )


# ---------------------------------------------------------------------------
# Explicit teardown — reducer registration GC-only tech debt resolution (Epic 3 retro D3)
# ---------------------------------------------------------------------------


def test_reducer_adapter_clear_connection_clears_registered_reducers() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    lines = content.splitlines()
    in_method = False
    found_clear = False
    brace_depth = 0

    for line in lines:
        stripped = line.strip()
        if "void ClearConnection()" in stripped:
            in_method = True
            brace_depth = 0
            continue

        if in_method:
            brace_depth += stripped.count("{") - stripped.count("}")
            if "_registeredReducers.Clear()" in stripped:
                found_clear = True
            if brace_depth < 0:
                break

    assert found_clear, (
        "ClearConnection() must call _registeredReducers.Clear() to force fresh "
        "callback registration on reconnect instead of relying on GC-only "
        "ConditionalWeakTable cleanup (Epic 3 retro D3)"
    )
