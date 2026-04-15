"""
Story 4.4: Distinguish Recoverable Runtime Failures from Programming Faults
Automated contract tests for all story deliverables.

Covers:
- Task 1: SpacetimeSdkReducerAdapter.cs null-connection guard now throws InvalidOperationException
  instead of silently returning (AC: 2)
- Task 2+3: docs/runtime-boundaries.md Guard paragraph accurately describes fault types;
  new section distinguishes programming faults from recoverable failures (AC: 1, 2, 3)
- Regression guards: full fault chain intact (AC: 1, 2, 3)
- Regression guards: recoverable failure types still intact (AC: 1)
- Regression guards: Story 4.3 signal bridge still intact
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


def _extract_method_body(content: str, signature: str) -> str:
    start = content.find(signature)
    assert start != -1, f"Could not find method signature: {signature}"

    brace_start = content.find("{", start)
    assert brace_start != -1, f"Could not find method body start: {signature}"

    depth = 0
    for index in range(brace_start, len(content)):
        char = content[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[brace_start + 1:index]

    raise AssertionError(f"Could not find method body end: {signature}")


def _extract_reducer_invocation_section() -> str:
    content = _read("docs/runtime-boundaries.md")
    match = re.search(
        r"### Reducer Invocation\n(?P<section>.*?)(?=\n### |\Z)",
        content,
        re.DOTALL,
    )
    assert match, "Could not locate the 'Reducer Invocation' section in runtime-boundaries.md"
    return match.group("section")


# ---------------------------------------------------------------------------
# Task 1: SpacetimeSdkReducerAdapter.cs null-connection guard (AC: 2)
# ---------------------------------------------------------------------------

def test_adapter_null_connection_guard_throws_invalid_operation() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    body = _extract_method_body(content, "internal void Invoke(object reducerArgs)")
    assert "throw new InvalidOperationException" in body, (
        "SpacetimeSdkReducerAdapter.Invoke must throw InvalidOperationException when "
        "_dbConnection is null — programming fault must not be silently swallowed (AC: 2)"
    )


def test_adapter_null_connection_guard_does_not_use_console_error_writeline_in_invoke() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    body = _extract_method_body(content, "internal void Invoke(object reducerArgs)")
    assert "Console.Error.WriteLine" not in body, (
        "SpacetimeSdkReducerAdapter must NOT use Console.Error.WriteLine to swallow the "
        "null-connection fault — the silent return is removed in Task 1 (AC: 2)"
    )


def test_adapter_still_checks_db_connection_null_guard() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    body = _extract_method_body(content, "internal void Invoke(object reducerArgs)")
    assert "_dbConnection == null" in body or "_dbConnection is null" in body, (
        "SpacetimeSdkReducerAdapter.Invoke must still check _dbConnection for null "
        "before attempting an invocation (AC: 2)"
    )


def test_adapter_still_imports_using_system() -> None:
    lines = _lines(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    assert "using System;" in lines, (
        "SpacetimeSdkReducerAdapter.cs must retain 'using System;' — removing "
        "Console.Error.WriteLine does not make System unused (AC: 2)"
    )


# ---------------------------------------------------------------------------
# Task 2+3: docs/runtime-boundaries.md — accurate fault model (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_guard_mentions_invalid_operation_exception() -> None:
    section = _extract_reducer_invocation_section()
    assert "InvalidOperationException" in section, (
        "runtime-boundaries.md Guard paragraph must mention InvalidOperationException "
        "for wrong-connection-state fault (AC: 3)"
    )


def test_runtime_boundaries_mentions_gd_push_error_in_reducer_context() -> None:
    section = _extract_reducer_invocation_section()
    assert "GD.PushError" in section, (
        "runtime-boundaries.md must mention GD.PushError so developers know where "
        "programming faults appear (AC: 2)"
    )


def test_runtime_boundaries_has_programming_fault_section() -> None:
    section = _extract_reducer_invocation_section()
    assert "programming fault" in section.lower(), (
        "runtime-boundaries.md must have a 'programming fault' section or paragraph "
        "in the reducer area (AC: 2, 3)"
    )


def test_runtime_boundaries_distinguishes_recoverable_from_programming_faults() -> None:
    section = _extract_reducer_invocation_section()
    assert "Recoverable" in section or "recoverable" in section, (
        "runtime-boundaries.md must explicitly distinguish recoverable failures from "
        "programming faults (AC: 1, 3)"
    )
    assert "programming fault" in section.lower() or "Programming Fault" in section, (
        "runtime-boundaries.md must name 'programming fault' category explicitly (AC: 2, 3)"
    )


def test_runtime_boundaries_mentions_failure_category_for_recoverable_branching() -> None:
    section = _extract_reducer_invocation_section()
    assert "FailureCategory" in section, (
        "runtime-boundaries.md must mention FailureCategory in the context of "
        "recoverable failure branching (AC: 1, 3)"
    )


def test_runtime_boundaries_clarifies_reducer_call_failed_does_not_fire_for_programming_faults() -> None:
    section = _extract_reducer_invocation_section()
    assert "ReducerCallFailed" in section, (
        "runtime-boundaries.md must reference ReducerCallFailed signal (AC: 1, 3)"
    )
    # The doc must clarify that ReducerCallFailed does NOT fire for programming faults.
    # We check for the key phrase or equivalent from the story tasks.
    lower = section.lower()
    assert (
        "does not fire for programming fault" in lower
        or "will not fire for programming fault" in lower
        or "reducercallfailed signal does not fire" in lower
        or "reducercallfailed signal will not fire" in lower
        or "not fire for programming" in lower
    ), (
        "runtime-boundaries.md must clarify that ReducerCallFailed does NOT fire for "
        "programming faults — only for server-side failures (AC: 2, 3)"
    )


# ---------------------------------------------------------------------------
# Regression guards — full fault chain still intact (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_connection_service_throws_invalid_operation_for_wrong_state() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert "InvalidOperationException" in content, (
        "SpacetimeConnectionService.cs must still throw InvalidOperationException for "
        "wrong connection state in InvokeReducer() (regression guard)"
    )
    assert "InvokeReducer" in content, (
        "SpacetimeConnectionService.cs must still expose an InvokeReducer method (regression guard)"
    )


def test_reducer_invoker_uses_argument_null_exception_throw_if_null() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs"
    )
    assert "ArgumentNullException.ThrowIfNull" in content, (
        "ReducerInvoker.cs must still use ArgumentNullException.ThrowIfNull(reducerArgs) "
        "for null guard at the invoker layer (regression guard)"
    )


def test_adapter_still_throws_argument_exception_for_non_ireducer_args() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    body = _extract_method_body(content, "internal void Invoke(object reducerArgs)")
    assert "ArgumentException" in body, (
        "SpacetimeSdkReducerAdapter.cs must still throw ArgumentException for "
        "non-IReducerArgs type (regression guard)"
    )


def test_spacetime_client_invoke_reducer_catches_argument_null_exception() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    body = _extract_method_body(content, "public void InvokeReducer(object reducerArgs)")
    assert "ArgumentNullException" in body, (
        "SpacetimeClient.cs InvokeReducer must still catch ArgumentNullException (regression guard)"
    )


def test_spacetime_client_invoke_reducer_catches_argument_exception() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    body = _extract_method_body(content, "public void InvokeReducer(object reducerArgs)")
    assert "ArgumentException" in body, (
        "SpacetimeClient.cs InvokeReducer must still catch ArgumentException (regression guard)"
    )


def test_spacetime_client_invoke_reducer_catches_invalid_operation_exception() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    body = _extract_method_body(content, "public void InvokeReducer(object reducerArgs)")
    assert "InvalidOperationException" in body, (
        "SpacetimeClient.cs InvokeReducer must still catch InvalidOperationException (regression guard)"
    )


def test_spacetime_client_invoke_reducer_calls_publish_validation_failure() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    body = _extract_method_body(content, "public void InvokeReducer(object reducerArgs)")
    assert "PublishValidationFailure" in body, (
        "SpacetimeClient.cs InvokeReducer must still call PublishValidationFailure for "
        "all caught fault types (regression guard)"
    )


def test_spacetime_client_publish_validation_failure_calls_gd_push_error() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    body = _extract_method_body(content, "private void PublishValidationFailure(string message)")
    assert "GD.PushError" in body, (
        "SpacetimeClient.cs PublishValidationFailure must still call GD.PushError for "
        "fault visibility in the Godot console (regression guard)"
    )


# ---------------------------------------------------------------------------
# Regression guards — recoverable failure types still intact (AC: 1)
# ---------------------------------------------------------------------------

def test_reducer_call_error_has_failure_category_property() -> None:
    content = _read(
        "addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs"
    )
    assert "FailureCategory" in content, (
        "ReducerCallError.cs must still have FailureCategory property (regression guard)"
    )


def test_reducer_call_error_has_recovery_guidance_property() -> None:
    content = _read(
        "addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs"
    )
    assert "RecoveryGuidance" in content, (
        "ReducerCallError.cs must still have RecoveryGuidance property (regression guard)"
    )


def test_reducer_failure_category_has_failed_case() -> None:
    content = _read(
        "addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs"
    )
    assert "Failed" in content, (
        "ReducerFailureCategory.cs must still have 'Failed' case (regression guard)"
    )


def test_reducer_failure_category_has_out_of_energy_case() -> None:
    content = _read(
        "addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs"
    )
    assert "OutOfEnergy" in content, (
        "ReducerFailureCategory.cs must still have 'OutOfEnergy' case (regression guard)"
    )


def test_reducer_failure_category_has_unknown_case() -> None:
    content = _read(
        "addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs"
    )
    assert "Unknown" in content, (
        "ReducerFailureCategory.cs must still have 'Unknown' case (regression guard)"
    )


def test_adapter_extract_and_dispatch_maps_committed_to_succeeded() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    assert "Status.Committed" in content and "OnReducerCallSucceeded" in content, (
        "SpacetimeSdkReducerAdapter.ExtractAndDispatch must still map Status.Committed "
        "→ OnReducerCallSucceeded (regression guard)"
    )


def test_adapter_extract_and_dispatch_maps_failed_to_call_failed_with_failed_category() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    assert "Status.Failed" in content and "ReducerFailureCategory.Failed" in content, (
        "SpacetimeSdkReducerAdapter.ExtractAndDispatch must still map Status.Failed "
        "→ OnReducerCallFailed with ReducerFailureCategory.Failed (regression guard)"
    )


def test_adapter_extract_and_dispatch_maps_out_of_energy_to_call_failed_with_out_of_energy_category() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    assert "Status.OutOfEnergy" in content and "ReducerFailureCategory.OutOfEnergy" in content, (
        "SpacetimeSdkReducerAdapter.ExtractAndDispatch must still map Status.OutOfEnergy "
        "→ OnReducerCallFailed with ReducerFailureCategory.OutOfEnergy (regression guard)"
    )


# ---------------------------------------------------------------------------
# Regression guards — Story 4.3 signal bridge still intact
# ---------------------------------------------------------------------------

def test_spacetime_client_connection_closed_event_handler_delegate_present() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionClosedEventHandler" in content, (
        "SpacetimeClient.cs ConnectionClosedEventHandler signal delegate must still be "
        "present (Story 4.3 regression guard)"
    )


def test_spacetime_client_handle_connection_closed_method_present() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "HandleConnectionClosed" in content, (
        "SpacetimeClient.cs HandleConnectionClosed method must still be present "
        "(Story 4.3 regression guard)"
    )


def test_connection_service_is_tearing_down_connection_guard_present() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    )
    assert "_isTearingDownConnection" in content, (
        "SpacetimeConnectionService.cs _isTearingDownConnection teardown guard must "
        "still be present (Story 4.3 regression guard)"
    )


# ---------------------------------------------------------------------------
# Gap coverage: message quality, section heading, default fallback, state change
# ---------------------------------------------------------------------------

def test_adapter_null_connection_throw_message_mentions_programming_fault() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    body = _extract_method_body(content, "internal void Invoke(object reducerArgs)")
    assert "This is a programming fault" in body, (
        "SpacetimeSdkReducerAdapter.Invoke null-connection throw must include the phrase "
        "'This is a programming fault' in its message so developers receive a clear "
        "diagnostic (AC: 2, Task 1.1)"
    )


def test_runtime_boundaries_has_reducer_error_model_section_heading() -> None:
    section = _extract_reducer_invocation_section()
    assert "#### Reducer Error Model: Programming Faults vs Recoverable Failures" in section, (
        "runtime-boundaries.md must contain the section heading "
        "'Reducer Error Model: Programming Faults vs Recoverable Failures' "
        "as specified by Task 3 (AC: 1, 2, 3)"
    )


def test_adapter_extract_and_dispatch_uses_unknown_for_default_fallback() -> None:
    content = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
    )
    assert "ReducerFailureCategory.Unknown" in content, (
        "SpacetimeSdkReducerAdapter.ExtractAndDispatch must use ReducerFailureCategory.Unknown "
        "for the default/fallback case (unrecognized or unavailable status) (regression guard)"
    )


def test_spacetime_client_publish_validation_failure_fires_connection_state_changed_disconnected() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    body = _extract_method_body(content, "private void PublishValidationFailure(string message)")
    assert "ConnectionState.Disconnected" in body, (
        "SpacetimeClient.PublishValidationFailure must fire ConnectionStateChanged with "
        "ConnectionState.Disconnected — this is the Godot-visible signal side of fault surfacing "
        "alongside GD.PushError (AC: 2, regression guard)"
    )


def test_runtime_boundaries_has_key_rule_about_failure_category_check() -> None:
    section = _extract_reducer_invocation_section()
    lower = section.lower()
    assert (
        "never check" in lower
        or "key rule" in lower
    ), (
        "runtime-boundaries.md must include the 'Key rule' / 'Never check ReducerCallError.FailureCategory' "
        "guidance statement so developers know FailureCategory is irrelevant for programming faults (AC: 3)"
    )


def test_runtime_boundaries_clarifies_programming_faults_do_not_emit_connection_closed() -> None:
    section = _extract_reducer_invocation_section()
    lower = section.lower()
    assert "ConnectionClosed" in section, (
        "runtime-boundaries.md must mention ConnectionClosed in the reducer fault model so "
        "programming-fault Disconnected status is not mistaken for a session-close event"
    )
    assert (
        "does not emit `connectionclosed`" in lower
        or "does not emit connectionclosed" in lower
        or "not a session-close notification" in lower
        or "not a clean-session-close notification" in lower
    ), (
        "runtime-boundaries.md must clarify that reducer programming faults do not emit "
        "ConnectionClosed — they are diagnostic surfacing, not a clean session-close signal"
    )
