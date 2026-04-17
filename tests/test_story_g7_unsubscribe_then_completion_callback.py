"""
Spec G7: UnsubscribeThen completion-callback sugar.

Structural contract tests covering:
- SpacetimeClient.UnsubscribeThen(SubscriptionHandle, Action onEnded) public method
  with ArgumentException -> PublishValidationFailure wrapping (AC 1, 4).
- SpacetimeConnectionService.UnsubscribeThen sibling to Unsubscribe: idempotent on
  Closed/Superseded, removes pending-replacement references, routes connected
  branch through TryUnsubscribeThen, falls back to inline GodotSignalAdapter.Dispatch
  when disconnected or when the adapter returns false; closes handle and unregisters;
  pending completion callbacks are canceled on disconnect to match the official
  C#/Unity SDK (AC 1, 2, 3, 5).
- SpacetimeSdkSubscriptionAdapter.TryUnsubscribeThen(object?, Action): reflects
  UnsubscribeThen(Action<T>) via Expression.Lambda, warns + returns false on null
  input, missing method, or invocation failure (AC 1, 5).
- SubscriptionHandle public surface is unchanged: no new public fields, properties,
  events, or signals (Never rule).
- Existing Unsubscribe(handle) path remains unchanged (AC 6).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CLIENT_CS = "addons/godot_spacetime/src/Public/SpacetimeClient.cs"
SERVICE_CS = "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
ADAPTER_CS = "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs"
HANDLE_CS = "addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _strip(rel: str) -> str:
    """Normalize whitespace for substring checks that should ignore formatting."""
    return re.sub(r"\s+", " ", _read(rel))


def _method_body(content: str, signature_marker: str) -> str:
    """Return the text of the first method whose signature contains signature_marker,
    from the opening brace through its matching closing brace."""
    idx = content.find(signature_marker)
    assert idx >= 0, f"signature marker {signature_marker!r} not found"
    brace_open = content.find("{", idx)
    assert brace_open >= 0
    depth = 0
    for i in range(brace_open, len(content)):
        ch = content[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[brace_open : i + 1]
    raise AssertionError("unterminated method body")


# ---------------------------------------------------------------------------
# SpacetimeClient.UnsubscribeThen — public method (AC 1, 4)
# ---------------------------------------------------------------------------

def test_spacetime_client_declares_unsubscribe_then_public_method() -> None:
    content = _strip(CLIENT_CS)
    assert "public void UnsubscribeThen( SubscriptionHandle handle, Action onEnded )" in content \
        or "public void UnsubscribeThen(SubscriptionHandle handle, Action onEnded)" in content, (
        "SpacetimeClient must expose public void UnsubscribeThen(SubscriptionHandle, Action) (AC 1)"
    )


def test_spacetime_client_unsubscribe_then_wraps_with_publish_validation_failure() -> None:
    content = _read(CLIENT_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert "_connectionService.UnsubscribeThen(" in body, (
        "SpacetimeClient.UnsubscribeThen must route through _connectionService.UnsubscribeThen (AC 1)"
    )
    assert "catch (ArgumentException" in body, (
        "SpacetimeClient.UnsubscribeThen must catch ArgumentException like Unsubscribe (AC 4)"
    )
    assert "PublishValidationFailure(" in body, (
        "SpacetimeClient.UnsubscribeThen must forward ArgumentException to PublishValidationFailure (AC 4)"
    )


def test_spacetime_client_unsubscribe_original_unchanged() -> None:
    """Regression guard: existing Unsubscribe(handle) signature stays untouched (AC 6)."""
    content = _strip(CLIENT_CS)
    assert "public void Unsubscribe(SubscriptionHandle handle)" in content \
        or "public void Unsubscribe( SubscriptionHandle handle )" in content, (
        "Existing Unsubscribe(handle) signature must remain unchanged (AC 6)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.UnsubscribeThen — routing (AC 1, 2, 3, 5)
# ---------------------------------------------------------------------------

def test_connection_service_declares_unsubscribe_then() -> None:
    content = _strip(SERVICE_CS)
    assert "public void UnsubscribeThen(SubscriptionHandle handle, Action onEnded)" in content \
        or "public void UnsubscribeThen( SubscriptionHandle handle, Action onEnded )" in content, (
        "SpacetimeConnectionService must expose public UnsubscribeThen(SubscriptionHandle, Action) (AC 1)"
    )


def test_connection_service_unsubscribe_then_validates_null_args() -> None:
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert '"handle must not be null"' in body, (
        "UnsubscribeThen must reject null handle (AC 4)"
    )
    assert '"onEnded must not be null"' in body, (
        "UnsubscribeThen must reject null onEnded callback (AC 4)"
    )


def test_connection_service_unsubscribe_then_idempotent_on_closed() -> None:
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    # idempotency: closed/superseded handles return early without invoking the callback
    assert "SubscriptionStatus.Closed" in body, (
        "UnsubscribeThen must no-op on Closed handles (AC 3)"
    )
    assert "SubscriptionStatus.Superseded" in body, (
        "UnsubscribeThen must no-op on Superseded handles (AC 3)"
    )


def test_connection_service_unsubscribe_then_clears_pending_replacements() -> None:
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert "RemovePendingReplacementReferences(handle.HandleId)" in body, (
        "UnsubscribeThen must mirror Unsubscribe's RemovePendingReplacementReferences call"
    )


def test_connection_service_unsubscribe_then_routes_connected_branch_through_adapter() -> None:
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert "ConnectionState.Connected" in body, (
        "UnsubscribeThen must check Connected state like Unsubscribe"
    )
    assert "TryUnsubscribeThen(" in body, (
        "UnsubscribeThen must call _subscriptionAdapter.TryUnsubscribeThen on the connected path (AC 1)"
    )
    assert "_subscriptionAdapter.MeasureUnsubscribePayloadBytes()" in body, (
        "UnsubscribeThen must record outbound bytes on adapter success, matching Unsubscribe"
    )


def test_connection_service_unsubscribe_then_inline_dispatch_fallback() -> None:
    """Disconnected branch and adapter-miss branch both invoke the forwarded
    callback inline. The main-thread wrapping is supplied by SpacetimeClient
    via GodotSignalAdapter before the callback reaches the service, matching
    how other SDK events reach the main thread."""
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert "forwardedOnEnded()" in body, (
        "UnsubscribeThen must invoke the forwarded onEnded callback in the "
        "disconnected and adapter-fallback branches (AC 2, 5)"
    )


def test_spacetime_client_unsubscribe_then_dispatches_on_main_thread() -> None:
    """SpacetimeClient wraps the user's onEnded with GodotSignalAdapter.Dispatch
    so the callback lands on the main thread regardless of whether the SDK's
    UnsubscribeThen fires from the receive thread or an inline service path."""
    content = _read(CLIENT_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert "_signalAdapter ??= new GodotSignalAdapter(this)" in body, (
        "SpacetimeClient.UnsubscribeThen must ensure a GodotSignalAdapter exists even before _EnterTree "
        "so the callback is always main-thread dispatched"
    )
    assert "Dispatch" in body, (
        "SpacetimeClient.UnsubscribeThen must wrap onEnded with _signalAdapter.Dispatch "
        "to guarantee main-thread delivery (AC 1, 2, 5)"
    )
    assert "_connectionService.UnsubscribeThen(handle, onEnded);" not in body, (
        "SpacetimeClient.UnsubscribeThen must not forward the raw callback and bypass main-thread dispatch"
    )


def test_connection_service_unsubscribe_then_falls_back_to_try_unsubscribe() -> None:
    """When the SDK lacks a reflectable UnsubscribeThen(Action<T>), the connected branch
    must still tear down via parameterless TryUnsubscribe before dispatching inline — the
    I/O matrix's 'SDK lacks reflectable UnsubscribeThen' row."""
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert "TryUnsubscribe(sdkSubscription)" in body, (
        "UnsubscribeThen must fall back to TryUnsubscribe when TryUnsubscribeThen returns false (AC 5)"
    )


def test_connection_service_unsubscribe_then_closes_handle_and_unregisters() -> None:
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert "handle.Close()" in body, (
        "UnsubscribeThen must mark handle Closed like Unsubscribe (AC 1, 2)"
    )
    assert "_subscriptionRegistry.Unregister(handle.HandleId)" in body, (
        "UnsubscribeThen must unregister the handle like Unsubscribe (AC 1, 2)"
    )


def test_connection_service_unsubscribe_then_marks_terminal_before_wiring_sdk_callback() -> None:
    """If the SDK invokes UnsubscribeThen synchronously, the callback must already
    observe a terminal handle state and a clean registry."""
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    close_pos = body.find("handle.Close()")
    wire_pos = body.find("TryUnsubscribeThen(")
    assert close_pos != -1 and wire_pos != -1, "UnsubscribeThen must both close the handle and try SDK UnsubscribeThen"
    assert close_pos < wire_pos, (
        "UnsubscribeThen must mark the handle terminal before wiring the SDK callback so a synchronous "
        "ended callback cannot observe stale Active state"
    )


def test_connection_service_unsubscribe_unchanged() -> None:
    """Regression guard: existing Unsubscribe signature and body shape intact (AC 6)."""
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void Unsubscribe(SubscriptionHandle handle)")
    assert "_subscriptionAdapter.TryUnsubscribe(entry.SdkSubscription)" in body, (
        "Existing Unsubscribe body must still call TryUnsubscribe (not TryUnsubscribeThen) (AC 6)"
    )


# ---------------------------------------------------------------------------
# SpacetimeSdkSubscriptionAdapter.TryUnsubscribeThen — reflection path (AC 1, 5)
# ---------------------------------------------------------------------------

def test_adapter_declares_try_unsubscribe_then() -> None:
    content = _strip(ADAPTER_CS)
    assert "internal bool TryUnsubscribeThen(object? sdkSubscription, Action onEnded)" in content \
        or "internal bool TryUnsubscribeThen( object? sdkSubscription, Action onEnded )" in content, (
        "SpacetimeSdkSubscriptionAdapter must declare internal bool TryUnsubscribeThen(object?, Action) (AC 1)"
    )


def test_adapter_try_unsubscribe_then_handles_null_input() -> None:
    content = _read(ADAPTER_CS)
    body = _method_body(content, "internal bool TryUnsubscribeThen(")
    # Guard against null SDK subscription object (pre-reflection degradation).
    assert "sdkSubscription == null" in body or "sdkSubscription is null" in body, (
        "TryUnsubscribeThen must return false on null input (AC 5)"
    )


def test_adapter_try_unsubscribe_then_reflects_action_generic() -> None:
    content = _read(ADAPTER_CS)
    body = _method_body(content, "internal bool TryUnsubscribeThen(")
    # The reflection probe resolves a method named "UnsubscribeThen" whose single parameter
    # type is Action<T>. The adapter must discover this via GetMethods/GetMethod.
    assert '"UnsubscribeThen"' in body, (
        "TryUnsubscribeThen must look up a method named UnsubscribeThen on the SDK handle (AC 1)"
    )
    assert "typeof(Action<>)" in body, (
        "TryUnsubscribeThen must require the parameter type to be Action<T> (AC 1)"
    )


def test_adapter_try_unsubscribe_then_builds_expression_lambda() -> None:
    content = _read(ADAPTER_CS)
    body = _method_body(content, "internal bool TryUnsubscribeThen(")
    assert "Expression.Lambda(" in body, (
        "TryUnsubscribeThen must build an Expression.Lambda for the SDK's Action<T> parameter (AC 1)"
    )
    assert "Expression.Parameter(" in body, (
        "TryUnsubscribeThen must introduce a ctx parameter for the SDK delegate signature (AC 1)"
    )


def test_adapter_try_unsubscribe_then_warns_on_failure_and_returns_false() -> None:
    content = _read(ADAPTER_CS)
    body = _method_body(content, "internal bool TryUnsubscribeThen(")
    # Fall-back path: reflection misses or invocation failure returns false without
    # propagating the exception. Both missing-method and invocation-failure branches
    # log a warning, matching the I/O matrix row for "SDK lacks reflectable method".
    assert "return false" in body, (
        "TryUnsubscribeThen must return false on null input, missing method, or invocation failure (AC 5)"
    )
    # Two warning sites: one under the missing-method branch, one under the invocation-
    # failure catch. Both are required by the I/O matrix row's "Warn via SpacetimeLog.Warning".
    assert body.count("SpacetimeLog.Warning") >= 2, (
        "TryUnsubscribeThen must warn on both missing-method and invocation-failure paths "
        "per the I/O matrix row for SDK lacking reflectable UnsubscribeThen (AC 5)"
    )


def test_connection_service_unsubscribe_then_absorbs_user_callback_exceptions() -> None:
    """A user-supplied onEnded that throws on the inline dispatch path must not escape
    the public Unsubscribe no-throw contract — absorb and surface via SpacetimeLog.Error."""
    content = _strip(SERVICE_CS)
    assert "private void DispatchPendingUnsubscribeThenCallback( Guid handleId )" in content \
        or "private void DispatchPendingUnsubscribeThenCallback(Guid handleId)" in content, (
        "UnsubscribeThen must route completion dispatch through a helper that can absorb user exceptions "
        "and enforce exactly-once behavior"
    )
    assert "SpacetimeLog.Error" in content, (
        "UnsubscribeThen completion dispatch must surface user-callback exceptions via SpacetimeLog.Error"
    )


def test_adapter_try_unsubscribe_unchanged() -> None:
    """Regression guard: existing TryUnsubscribe(object?) body intact (AC 6)."""
    content = _read(ADAPTER_CS)
    body = _method_body(content, "internal bool TryUnsubscribe(object? sdkSubscription)")
    assert '"Unsubscribe"' in body, (
        "Existing TryUnsubscribe must still look up parameterless Unsubscribe/Close (AC 6)"
    )


# ---------------------------------------------------------------------------
# SubscriptionHandle — public surface unchanged (Never rule)
# ---------------------------------------------------------------------------

def test_subscription_handle_public_surface_unchanged() -> None:
    content = _read(HANDLE_CS)
    # The Never rule forbids adding new public fields, properties, events, or signals.
    # Keep the public surface as {HandleId, Status} only.
    public_members = re.findall(r"^\s*public\s+[^/\n]+", content, flags=re.MULTILINE)
    non_ctor = [m for m in public_members if "SubscriptionHandle(" not in m]
    # partial class declaration and the two properties are the only public members
    assert len(non_ctor) <= 3, (
        f"SubscriptionHandle public surface must not grow past {{HandleId, Status}}; "
        f"found public members: {non_ctor}"
    )
    assert "public Guid HandleId" in content, "HandleId public getter must remain"
    assert "public SubscriptionStatus Status" in content, "Status public getter must remain"
    # Forbid any new Signal attribute on SubscriptionHandle.
    assert "[Signal]" not in content, (
        "Never rule: SubscriptionHandle must not gain any [Signal] attributes"
    )


# ---------------------------------------------------------------------------
# Runtime isolation — SDK types stay inside Internal/Platform/DotNet
# ---------------------------------------------------------------------------

def test_client_does_not_reference_spacetimedb_sdk_for_unsubscribe_then() -> None:
    """SDK context types (Action<SubscriptionEventContext>, etc.) must not leak
    to the public client surface."""
    content = _read(CLIENT_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert "SpacetimeDB." not in body, (
        "Public SpacetimeClient.UnsubscribeThen must not reference SpacetimeDB.* types (Always rule)"
    )


def test_connection_service_unsubscribe_then_does_not_reference_spacetimedb_sdk() -> None:
    content = _read(SERVICE_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert "SpacetimeDB." not in body, (
        "SpacetimeConnectionService.UnsubscribeThen must not reference SpacetimeDB.* types (Always rule)"
    )


def test_spacetime_client_unsubscribe_then_validates_before_wrapping() -> None:
    content = _read(CLIENT_CS)
    body = _method_body(content, "public void UnsubscribeThen(")
    assert '"handle must not be null"' in body, (
        "SpacetimeClient.UnsubscribeThen must preserve the public handle-validation message before wrapping"
    )
    assert '"onEnded must not be null"' in body, (
        "SpacetimeClient.UnsubscribeThen must validate the raw user callback before wrapping so null remains observable"
    )


def test_connection_service_tracks_pending_unsubscribe_then_callbacks_for_exactly_once_dispatch() -> None:
    content = _read(SERVICE_CS)
    assert "_pendingUnsubscribeThenCallbacks" in content, (
        "SpacetimeConnectionService must track pending UnsubscribeThen callbacks so sdk and fallback paths "
        "can share exactly-once dispatch"
    )
    assert "RegisterPendingUnsubscribeThenCallback(" in content, (
        "UnsubscribeThen must register a pending callback before wiring the sdk/fallback paths"
    )
    assert "DispatchPendingUnsubscribeThenCallback(" in content, (
        "UnsubscribeThen must dispatch through a shared helper to avoid duplicate callback delivery"
    )


def test_connection_service_disconnect_cancels_pending_unsubscribe_then_callbacks() -> None:
    content = _read(SERVICE_CS)
    body = _method_body(content, "private void ResetDisconnectedSessionState()")
    assert "CancelPendingUnsubscribeThenCallbacks()" in body or "_pendingUnsubscribeThenCallbacks.Clear()" in body, (
        "Disconnect teardown must cancel pending UnsubscribeThen completion callbacks to match the official "
        "C#/Unity SDK semantics when disconnect wins before UnsubscribeApplied"
    )
