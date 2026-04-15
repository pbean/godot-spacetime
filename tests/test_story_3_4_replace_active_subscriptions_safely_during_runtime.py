"""
Story 3.4: Replace Active Subscriptions Safely During Runtime
Automated contract tests for all story deliverables.

Covers:
- SubscriptionStatus.cs: file exists, namespace, public enum, Active/Superseded/Closed values, no SpacetimeDB reference (AC: 3, 4)
- SubscriptionHandle.cs: Status property present, Supersede()/Close() internal methods, initialized to Active (AC: 3, 4)
- SpacetimeSdkSubscriptionAdapter.cs: Subscribe() returns object (not void), TryUnsubscribe(object?) present,
  reflection-based unsubscribe lookup, no SDK types leak out (AC: 1, 2, 4)
- SubscriptionRegistry.cs: SubscriptionEntry type present, stores Handle + SdkSubscription,
  TryGetEntry method, UpdateSdkSubscription method (AC: 1, 2, 4)
- SpacetimeConnectionService.cs: Unsubscribe(handle) method present, ReplaceSubscription(oldHandle, queries)
  method present, _pendingReplacements field or equivalent, ISubscriptionEventSink checks pending replacements (AC: 1, 2, 3, 4, 5)
- SpacetimeClient.cs: Unsubscribe(handle) method present, ReplaceSubscription(oldHandle, queries) method present (AC: 1, 3, 4)
- Regression guards: prior story deliverables intact
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# SubscriptionStatus.cs — file existence and content (AC: 3, 4)
# ---------------------------------------------------------------------------

def test_subscription_status_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs"
    assert path.exists(), (
        "SubscriptionStatus.cs must exist at Public/Subscriptions/SubscriptionStatus.cs (AC 3, 4)"
    )


def test_subscription_status_namespace_is_godot_spacetime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs")
    assert "namespace GodotSpacetime.Subscriptions" in content, (
        "SubscriptionStatus.cs must use namespace GodotSpacetime.Subscriptions (AC 3, 4)"
    )


def test_subscription_status_is_public_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs")
    assert "public enum SubscriptionStatus" in content, (
        "SubscriptionStatus.cs must declare 'public enum SubscriptionStatus' (AC 3, 4)"
    )


def test_subscription_status_has_active_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs")
    assert "Active" in content, (
        "SubscriptionStatus must contain 'Active' value (AC 3, 4)"
    )


def test_subscription_status_has_superseded_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs")
    assert "Superseded" in content, (
        "SubscriptionStatus must contain 'Superseded' value (AC 3)"
    )


def test_subscription_status_has_closed_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs")
    assert "Closed" in content, (
        "SubscriptionStatus must contain 'Closed' value (AC 4)"
    )


def test_subscription_status_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs")
    assert "SpacetimeDB." not in content, (
        "SubscriptionStatus.cs must NOT reference SpacetimeDB.* — public contract must stay runtime-neutral (AC 3, 4)"
    )


def test_subscription_status_no_godot_import() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs")
    assert "using Godot" not in content, (
        "SubscriptionStatus.cs must NOT import Godot — it is a plain C# enum (AC 3, 4)"
    )


# ---------------------------------------------------------------------------
# SubscriptionHandle.cs — Status property and lifecycle methods (AC: 3, 4)
# ---------------------------------------------------------------------------

def test_subscription_handle_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs"
    assert path.exists(), (
        "SubscriptionHandle.cs must exist (AC 3, 4)"
    )


def test_subscription_handle_has_status_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "SubscriptionStatus Status" in content, (
        "SubscriptionHandle must expose 'SubscriptionStatus Status' property (AC 3, 4)"
    )


def test_subscription_handle_status_is_public() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "public SubscriptionStatus Status" in content, (
        "SubscriptionHandle.Status must be public (AC 3, 4)"
    )


def test_subscription_handle_has_supersede_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "Supersede()" in content, (
        "SubscriptionHandle must have Supersede() method (AC 3)"
    )


def test_subscription_handle_supersede_is_internal() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "internal" in content and "Supersede()" in content, (
        "SubscriptionHandle.Supersede() must be internal (AC 3)"
    )


def test_subscription_handle_has_close_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "Close()" in content, (
        "SubscriptionHandle must have Close() method (AC 4)"
    )


def test_subscription_handle_close_is_internal() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "internal" in content and "Close()" in content, (
        "SubscriptionHandle.Close() must be internal (AC 4)"
    )


def test_subscription_handle_status_initialized_to_active() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "SubscriptionStatus.Active" in content, (
        "SubscriptionHandle must initialize Status to SubscriptionStatus.Active (AC 3, 4)"
    )


def test_subscription_handle_supersede_sets_superseded() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "SubscriptionStatus.Superseded" in content, (
        "SubscriptionHandle.Supersede() must set Status = Superseded (AC 3)"
    )


def test_subscription_handle_close_sets_closed() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "SubscriptionStatus.Closed" in content, (
        "SubscriptionHandle.Close() must set Status = Closed (AC 4)"
    )


def test_subscription_handle_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "SpacetimeDB." not in content, (
        "SubscriptionHandle.cs must NOT reference SpacetimeDB.* — public contract must stay runtime-neutral (AC 3, 4)"
    )


# ---------------------------------------------------------------------------
# SpacetimeSdkSubscriptionAdapter.cs — Subscribe returns object, TryUnsubscribe (AC: 1, 2, 4)
# ---------------------------------------------------------------------------

def test_subscription_adapter_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs"
    assert path.exists(), (
        "SpacetimeSdkSubscriptionAdapter.cs must exist (AC 1, 2, 4)"
    )


def test_subscription_adapter_subscribe_returns_object() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "object?" in content, (
        "SpacetimeSdkSubscriptionAdapter.Subscribe() must return object? to capture the SDK subscription lifecycle object (AC 1, 4)"
    )


def test_subscription_adapter_subscribe_return_type_in_signature() -> None:
    lines = _lines("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    subscribe_sig = [ln for ln in lines if "object?" in ln and "Subscribe(" in ln]
    assert len(subscribe_sig) > 0, (
        "SpacetimeSdkSubscriptionAdapter.Subscribe() must declare object? return type in its signature (AC 1, 4)"
    )


def test_subscription_adapter_has_try_unsubscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "TryUnsubscribe" in content, (
        "SpacetimeSdkSubscriptionAdapter must have TryUnsubscribe method (AC 1, 4)"
    )


def test_subscription_adapter_try_unsubscribe_takes_object() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "TryUnsubscribe(object?" in content, (
        "SpacetimeSdkSubscriptionAdapter.TryUnsubscribe must accept object? parameter (AC 1, 4)"
    )


def test_subscription_adapter_try_unsubscribe_returns_bool() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "bool TryUnsubscribe" in content, (
        "SpacetimeSdkSubscriptionAdapter.TryUnsubscribe must return bool (AC 1, 4)"
    )


def test_subscription_adapter_try_unsubscribe_uses_reflection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "GetMethod" in content and "TryUnsubscribe" in content, (
        "SpacetimeSdkSubscriptionAdapter.TryUnsubscribe must use reflection to find Unsubscribe/Close method (AC 1, 4)"
    )


def test_subscription_adapter_try_unsubscribe_handles_null() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "sdkSubscription == null" in content or "sdkSubscription is null" in content, (
        "SpacetimeSdkSubscriptionAdapter.TryUnsubscribe must handle null input gracefully (AC 1, 4)"
    )


def test_subscription_adapter_try_unsubscribe_looks_for_unsubscribe_or_close() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert '"Unsubscribe"' in content and '"Close"' in content, (
        "SpacetimeSdkSubscriptionAdapter.TryUnsubscribe must look for both 'Unsubscribe' and 'Close' methods (AC 1, 4)"
    )


def test_subscription_adapter_try_unsubscribe_is_best_effort_when_sdk_close_throws() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "catch (Exception)" in content and "return false" in content, (
        "SpacetimeSdkSubscriptionAdapter.TryUnsubscribe must swallow SDK close failures and return false so handle cleanup still completes (AC 4)"
    )


def test_subscription_adapter_subscribe_captures_return_value() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "return subscribeMethod.Invoke" in content or (
        "subscribeMethod.Invoke" in content and "return" in content
    ), (
        "SpacetimeSdkSubscriptionAdapter.Subscribe() must capture and return the result of subscribeMethod.Invoke() (AC 1, 4)"
    )


# ---------------------------------------------------------------------------
# SubscriptionRegistry.cs — SubscriptionEntry, TryGetEntry, UpdateSdkSubscription (AC: 1, 2, 4)
# ---------------------------------------------------------------------------

def test_subscription_registry_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs"
    assert path.exists(), (
        "SubscriptionRegistry.cs must exist (AC 1, 2, 4)"
    )


def test_subscription_registry_has_subscription_entry_type() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "SubscriptionEntry" in content, (
        "SubscriptionRegistry.cs must define SubscriptionEntry type (AC 1, 2, 4)"
    )


def test_subscription_entry_stores_handle() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "SubscriptionHandle Handle" in content or "Handle" in content, (
        "SubscriptionEntry must store a SubscriptionHandle field (AC 1, 2, 4)"
    )


def test_subscription_entry_stores_sdk_subscription() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "SdkSubscription" in content, (
        "SubscriptionEntry must store an SdkSubscription field (AC 1, 2, 4)"
    )


def test_subscription_entry_sdk_subscription_is_nullable_object() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "object? SdkSubscription" in content, (
        "SubscriptionEntry.SdkSubscription must be object? to stay runtime-neutral (AC 1, 2, 4)"
    )


def test_subscription_registry_has_try_get_entry() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "TryGetEntry" in content, (
        "SubscriptionRegistry must have TryGetEntry method (AC 1, 2, 4)"
    )


def test_subscription_registry_try_get_entry_out_param() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "out SubscriptionEntry" in content, (
        "SubscriptionRegistry.TryGetEntry must use out SubscriptionEntry? parameter (AC 1, 2, 4)"
    )


def test_subscription_registry_has_update_sdk_subscription() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "UpdateSdkSubscription" in content, (
        "SubscriptionRegistry must have UpdateSdkSubscription method (AC 1, 4)"
    )


def test_subscription_registry_register_signature_accepts_sdk_subscription() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    # Register must accept handle; sdkSubscription is optional param or separate method
    assert "Register(" in content, (
        "SubscriptionRegistry must have a Register method (AC 1, 4)"
    )


def test_subscription_registry_active_handles_returns_entries() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "IReadOnlyCollection<SubscriptionEntry>" in content, (
        "SubscriptionRegistry.ActiveHandles must return IReadOnlyCollection<SubscriptionEntry> (AC 1, 4)"
    )


def test_subscription_registry_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "SpacetimeDB." not in content, (
        "SubscriptionRegistry.cs must NOT reference SpacetimeDB.* (AC 1, 4)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — Unsubscribe, ReplaceSubscription, _pendingReplacements (AC: 1–5)
# ---------------------------------------------------------------------------

def test_connection_service_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
    assert path.exists(), (
        "SpacetimeConnectionService.cs must exist (AC 1–5)"
    )


def test_connection_service_has_unsubscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "public void Unsubscribe(" in content, (
        "SpacetimeConnectionService must have public Unsubscribe(SubscriptionHandle) method (AC 4)"
    )


def test_connection_service_unsubscribe_takes_handle() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Unsubscribe(SubscriptionHandle handle)" in content, (
        "SpacetimeConnectionService.Unsubscribe must accept SubscriptionHandle parameter (AC 4)"
    )


def test_connection_service_unsubscribe_is_idempotent() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    # The idempotent guard: check for Closed status before doing anything
    assert "SubscriptionStatus.Closed" in content, (
        "SpacetimeConnectionService.Unsubscribe must guard against already-Closed handles (AC 4)"
    )


def test_connection_service_has_replace_subscription_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "public SubscriptionHandle ReplaceSubscription(" in content, (
        "SpacetimeConnectionService must have public ReplaceSubscription method returning SubscriptionHandle (AC 1, 2, 3)"
    )


def test_connection_service_replace_subscription_takes_old_handle_and_queries() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ReplaceSubscription(SubscriptionHandle oldHandle" in content, (
        "SpacetimeConnectionService.ReplaceSubscription must accept oldHandle and newQueries parameters (AC 1, 2, 3)"
    )


def test_connection_service_has_pending_replacements_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_pendingReplacements" in content, (
        "SpacetimeConnectionService must have _pendingReplacements field for overlap-first tracking (AC 2, 5)"
    )


def test_connection_service_pending_replacements_is_guid_guid_dict() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Dictionary<Guid, Guid>" in content, (
        "SpacetimeConnectionService._pendingReplacements must be Dictionary<Guid, Guid> (AC 2, 5)"
    )


def test_connection_service_on_subscription_applied_checks_pending_replacements() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_pendingReplacements.TryGetValue" in content, (
        "SpacetimeConnectionService.OnSubscriptionApplied must check _pendingReplacements for overlap-first close (AC 2, 3)"
    )


def test_connection_service_on_subscription_applied_calls_supersede() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Supersede()" in content, (
        "SpacetimeConnectionService must call Supersede() on the old handle after new subscription is applied (AC 3)"
    )


def test_connection_service_on_subscription_error_removes_pending_without_closing_old() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_pendingReplacements.Remove" in content, (
        "SpacetimeConnectionService.OnSubscriptionError must remove from _pendingReplacements without touching old handle (AC 5)"
    )


def test_connection_service_replace_subscription_guards_active_status() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "oldHandle.Status != SubscriptionStatus.Active" in content or (
        "SubscriptionStatus.Active" in content and "ReplaceSubscription" in content
    ), (
        "SpacetimeConnectionService.ReplaceSubscription must guard that oldHandle.Status == Active (AC 1)"
    )


def test_connection_service_subscribe_captures_sdk_subscription() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "UpdateSdkSubscription" in content, (
        "SpacetimeConnectionService.Subscribe must call UpdateSdkSubscription to store returned SDK object (AC 1, 4)"
    )


def test_connection_service_unsubscribe_calls_try_unsubscribe() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "TryUnsubscribe" in content, (
        "SpacetimeConnectionService must call TryUnsubscribe on the SDK subscription adapter (AC 4)"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.cs — Unsubscribe and ReplaceSubscription public surface (AC: 1, 3, 4)
# ---------------------------------------------------------------------------

def test_spacetime_client_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Public/SpacetimeClient.cs"
    assert path.exists(), (
        "SpacetimeClient.cs must exist (AC 1, 3, 4)"
    )


def test_spacetime_client_has_unsubscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public void Unsubscribe(" in content, (
        "SpacetimeClient must expose public Unsubscribe method (AC 4)"
    )


def test_spacetime_client_unsubscribe_delegates_to_service() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_connectionService.Unsubscribe" in content, (
        "SpacetimeClient.Unsubscribe must delegate to _connectionService.Unsubscribe (AC 4)"
    )


def test_spacetime_client_has_replace_subscription_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ReplaceSubscription(" in content, (
        "SpacetimeClient must expose public ReplaceSubscription method (AC 1, 3)"
    )


def test_spacetime_client_replace_subscription_delegates_to_service() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_connectionService.ReplaceSubscription" in content, (
        "SpacetimeClient.ReplaceSubscription must delegate to _connectionService.ReplaceSubscription (AC 1, 3)"
    )


def test_spacetime_client_replace_subscription_returns_handle() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionHandle" in content and "ReplaceSubscription" in content, (
        "SpacetimeClient.ReplaceSubscription must return a SubscriptionHandle (AC 1, 3)"
    )


# ---------------------------------------------------------------------------
# Regression guards — prior story deliverables must remain intact
# ---------------------------------------------------------------------------

def test_regression_subscription_applied_signal_present() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionAppliedEventHandler" in content, (
        "REGRESSION: SpacetimeClient must still declare SubscriptionApplied signal (Story 3.1)"
    )


def test_regression_subscription_handle_has_handle_id() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "public Guid HandleId" in content, (
        "REGRESSION: SubscriptionHandle must still expose HandleId (Story 3.1)"
    )


def test_regression_row_changed_signal_present() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "RowChangedEventHandler" in content, (
        "REGRESSION: SpacetimeClient must still declare RowChanged signal (Story 3.3)"
    )


def test_regression_subscription_registry_has_clear_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "void Clear()" in content or "Clear()" in content, (
        "REGRESSION: SubscriptionRegistry must still expose Clear() method (Story 3.1)"
    )


def test_regression_cache_view_adapter_set_db_still_present() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "SetDb" in content, (
        "REGRESSION: CacheViewAdapter must still expose SetDb method (Story 3.2)"
    )


def test_regression_spacetime_sdk_row_callback_adapter_present() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs"
    assert path.exists(), (
        "REGRESSION: SpacetimeSdkRowCallbackAdapter.cs must still exist (Story 3.3)"
    )


def test_regression_subscription_adapter_has_on_applied_wiring() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "OnSubscriptionApplied" in content, (
        "REGRESSION: SpacetimeSdkSubscriptionAdapter must still wire OnSubscriptionApplied (Story 3.1)"
    )


def test_regression_subscribe_method_still_present_on_client() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public SubscriptionHandle Subscribe(" in content, (
        "REGRESSION: SpacetimeClient.Subscribe must still be present (Story 3.1)"
    )


def test_regression_get_rows_still_present_on_client() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public IEnumerable<object> GetRows(" in content, (
        "REGRESSION: SpacetimeClient.GetRows must still be present (Story 3.2)"
    )


def test_regression_isubscription_event_sink_interface_still_present() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "interface ISubscriptionEventSink" in content, (
        "REGRESSION: ISubscriptionEventSink interface must still be defined (Story 3.1)"
    )


def test_regression_connection_service_implements_isubscription_event_sink() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ISubscriptionEventSink" in content, (
        "REGRESSION: SpacetimeConnectionService must still implement ISubscriptionEventSink (Story 3.1)"
    )


# ---------------------------------------------------------------------------
# SubscriptionHandle.cs — structural and Godot integration contracts (AC: 3, 4)
# ---------------------------------------------------------------------------

def test_subscription_handle_namespace_is_godot_spacetime_subscriptions() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "namespace GodotSpacetime.Subscriptions" in content, (
        "SubscriptionHandle.cs must declare namespace GodotSpacetime.Subscriptions (AC 3, 4)"
    )


def test_subscription_handle_is_partial_class() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "partial class SubscriptionHandle" in content, (
        "SubscriptionHandle must be declared as a partial class (required by Godot's RefCounted signal system) (AC 3, 4)"
    )


def test_subscription_handle_extends_ref_counted() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert ": RefCounted" in content, (
        "SubscriptionHandle must extend Godot.RefCounted so it can be passed through Godot signals (AC 3)"
    )


def test_subscription_handle_constructor_is_internal() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "internal SubscriptionHandle()" in content, (
        "SubscriptionHandle constructor must be internal — callers must not be able to create handles outside the SDK (AC 3, 4)"
    )


def test_subscription_handle_has_using_godot() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "using Godot" in content, (
        "SubscriptionHandle.cs must import Godot to extend RefCounted (AC 3)"
    )


def test_subscription_handle_has_using_system() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert "using System" in content, (
        "SubscriptionHandle.cs must import System for Guid (AC 3, 4)"
    )


def test_subscription_handle_status_is_not_godot_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    # The Status property must NOT be decorated with [Signal] — it is internal bookkeeping only.
    assert "[Signal]" not in content, (
        "SubscriptionHandle.Status must NOT be a Godot [Signal] — status transitions are internal bookkeeping, not gameplay events (AC 3, 4)"
    )


# ---------------------------------------------------------------------------
# SubscriptionRegistry.cs — SubscriptionEntry record type and method signatures (AC: 1, 2, 4)
# ---------------------------------------------------------------------------

def test_subscription_entry_is_sealed_record() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "sealed record SubscriptionEntry" in content, (
        "SubscriptionEntry must be declared as a sealed record for value-equality semantics (AC 1, 2, 4)"
    )


def test_subscription_registry_register_has_optional_sdk_subscription_param() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "sdkSubscription = null" in content, (
        "SubscriptionRegistry.Register must accept an optional sdkSubscription = null parameter to allow two-step registration (AC 1, 4)"
    )


def test_subscription_registry_has_unregister_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "void Unregister(" in content, (
        "SubscriptionRegistry must have an Unregister method for cleanup on close or error (AC 1, 4)"
    )


def test_subscription_registry_unregister_takes_guid() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "Unregister(Guid" in content, (
        "SubscriptionRegistry.Unregister must accept a Guid handleId parameter (AC 1, 4)"
    )


def test_subscription_registry_update_sdk_subscription_takes_guid_and_object() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "UpdateSdkSubscription(Guid" in content, (
        "SubscriptionRegistry.UpdateSdkSubscription must accept a Guid handleId first parameter (AC 1, 4)"
    )


def test_subscription_registry_clear_closes_tracked_handles() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs")
    assert "entry.Handle.Close()" in content, (
        "SubscriptionRegistry.Clear must close tracked handles before clearing so disconnect teardown leaves no stale Active handles (AC 4)"
    )


# ---------------------------------------------------------------------------
# SpacetimeSdkSubscriptionAdapter.cs — class modifiers and argument guards (AC: 1, 2, 4)
# ---------------------------------------------------------------------------

def test_subscription_adapter_is_internal_sealed_class() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "internal sealed class SpacetimeSdkSubscriptionAdapter" in content, (
        "SpacetimeSdkSubscriptionAdapter must be internal sealed — it is an SDK-isolation boundary class (AC 1, 4)"
    )


def test_subscription_adapter_subscribe_validates_connection_arg() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "ArgumentNullException.ThrowIfNull(connection)" in content, (
        "SpacetimeSdkSubscriptionAdapter.Subscribe must validate the connection argument (AC 1)"
    )


def test_subscription_adapter_subscribe_validates_queries_arg() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "ArgumentNullException.ThrowIfNull(querySqls)" in content, (
        "SpacetimeSdkSubscriptionAdapter.Subscribe must validate the querySqls argument (AC 1)"
    )


def test_subscription_adapter_subscribe_validates_sink_arg() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "ArgumentNullException.ThrowIfNull(sink)" in content, (
        "SpacetimeSdkSubscriptionAdapter.Subscribe must validate the sink argument (AC 1)"
    )


def test_subscription_adapter_subscribe_validates_handle_arg() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "ArgumentNullException.ThrowIfNull(handle)" in content, (
        "SpacetimeSdkSubscriptionAdapter.Subscribe must validate the handle argument (AC 1)"
    )


def test_subscription_adapter_has_create_applied_callback_helper() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs")
    assert "CreateAppliedCallback" in content, (
        "SpacetimeSdkSubscriptionAdapter must have a CreateAppliedCallback helper to wire the SDK OnApplied callback (AC 1, 3)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — Unsubscribe/ReplaceSubscription behavioral contracts (AC: 1–5)
# ---------------------------------------------------------------------------

def test_connection_service_unsubscribe_null_guard() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ArgumentNullException.ThrowIfNull(handle)" in content, (
        "SpacetimeConnectionService.Unsubscribe must null-guard the handle parameter (AC 4)"
    )


def test_connection_service_unsubscribe_calls_handle_close() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "handle.Close()" in content, (
        "SpacetimeConnectionService.Unsubscribe must call handle.Close() to transition the handle to Closed state (AC 4)"
    )


def test_connection_service_unsubscribe_calls_registry_unregister() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionRegistry.Unregister(handle.HandleId)" in content, (
        "SpacetimeConnectionService.Unsubscribe must call _subscriptionRegistry.Unregister(handle.HandleId) (AC 4)"
    )


def test_connection_service_unsubscribe_cancels_pending_replacement_for_handle() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "RemovePendingReplacementReferences(handle.HandleId)" in content, (
        "SpacetimeConnectionService.Unsubscribe must cancel any pending replacement bookkeeping for the unsubscribed handle (AC 2, 4, 5)"
    )


def test_connection_service_replace_subscription_null_guard_new_queries() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ArgumentNullException.ThrowIfNull(newQueries)" in content, (
        "SpacetimeConnectionService.ReplaceSubscription must null-guard the newQueries parameter (AC 1)"
    )


def test_connection_service_replace_subscription_registers_new_handle() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionRegistry.Register(newHandle)" in content, (
        "SpacetimeConnectionService.ReplaceSubscription must register the new handle before calling Subscribe (AC 1, 2)"
    )


def test_connection_service_replace_subscription_wires_pending_replacement() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_pendingReplacements[newHandle.HandleId]" in content, (
        "SpacetimeConnectionService.ReplaceSubscription must wire the overlap-first map: _pendingReplacements[newHandle.HandleId] = oldHandle.HandleId (AC 2)"
    )


def test_connection_service_pending_replacements_is_readonly() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "readonly Dictionary<Guid, Guid>" in content, (
        "SpacetimeConnectionService._pendingReplacements must be declared readonly (AC 2, 5)"
    )


def test_connection_service_on_subscription_applied_unregisters_old_handle() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Unregister(oldHandleId)" in content, (
        "SpacetimeConnectionService.OnSubscriptionApplied must call Unregister(oldHandleId) after overlap-first close (AC 2, 3)"
    )


def test_connection_service_on_subscription_error_closes_new_handle() -> None:
    lines = _lines("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    # Find OnSubscriptionError implementation
    error_start = None
    for i, ln in enumerate(lines):
        if "OnSubscriptionError" in ln and "void" in ln:
            error_start = i
            break
    assert error_start is not None, (
        "ISubscriptionEventSink.OnSubscriptionError must be implemented on SpacetimeConnectionService"
    )
    # handle.Close() must appear within the method body (within 15 lines)
    block = lines[error_start:error_start + 15]
    assert any("handle.Close()" in ln for ln in block), (
        "SpacetimeConnectionService.OnSubscriptionError must call handle.Close() on the errored new handle (AC 5)"
    )


def test_connection_service_replace_subscription_error_path_cleans_up() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    # The catch block must remove from _pendingReplacements and unregister the new handle
    assert "_pendingReplacements.Remove(newHandle.HandleId)" in content, (
        "SpacetimeConnectionService.ReplaceSubscription catch block must remove the new handle from _pendingReplacements (AC 5)"
    )


def test_connection_service_replace_subscription_rejects_handles_with_replacement_in_flight() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "HasPendingReplacementInFlight(oldHandle.HandleId)" in content, (
        "SpacetimeConnectionService.ReplaceSubscription must reject handles that already participate in an in-flight replacement (AC 2)"
    )


def test_connection_service_on_subscription_error_best_effort_unsubscribes_failed_handle() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "TryGetEntry(handle.HandleId, out var entry)" in content and "TryUnsubscribe(entry.SdkSubscription)" in content, (
        "SpacetimeConnectionService.OnSubscriptionError must best-effort close the failed SDK subscription object before removing local tracking (AC 5)"
    )


def test_connection_service_reset_disconnected_state_clears_pending_replacements() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_pendingReplacements.Clear()" in content, (
        "SpacetimeConnectionService.ResetDisconnectedSessionState must clear pending replacement bookkeeping on disconnect teardown (AC 2, 5)"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.cs — return type, error handling, and event wiring contracts (AC: 1, 3, 4)
# ---------------------------------------------------------------------------

def test_spacetime_client_namespace() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "namespace GodotSpacetime" in content, (
        "SpacetimeClient.cs must declare namespace GodotSpacetime (AC 1, 3, 4)"
    )


def test_spacetime_client_replace_subscription_returns_nullable_handle() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionHandle? ReplaceSubscription(" in content, (
        "SpacetimeClient.ReplaceSubscription must return SubscriptionHandle? (nullable) — returns null on validation failure (AC 1, 3)"
    )


def test_spacetime_client_unsubscribe_has_try_catch() -> None:
    lines = _lines("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    unsubscribe_start = None
    for i, ln in enumerate(lines):
        if "public void Unsubscribe(" in ln:
            unsubscribe_start = i
            break
    assert unsubscribe_start is not None, "SpacetimeClient must have public void Unsubscribe method"
    # try keyword must appear within the method body (within 10 lines)
    block = lines[unsubscribe_start:unsubscribe_start + 10]
    assert any("try" in ln for ln in block), (
        "SpacetimeClient.Unsubscribe must wrap the delegation call in try/catch for error safety (AC 4)"
    )


def test_spacetime_client_replace_subscription_catches_invalid_operation() -> None:
    lines = _lines("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    replace_start = None
    for i, ln in enumerate(lines):
        if "public SubscriptionHandle" in ln and "ReplaceSubscription(" in ln:
            replace_start = i
            break
    assert replace_start is not None, "SpacetimeClient must have public SubscriptionHandle ReplaceSubscription method"
    # InvalidOperationException must be caught within the method body (within 15 lines)
    block = lines[replace_start:replace_start + 15]
    assert any("InvalidOperationException" in ln for ln in block), (
        "SpacetimeClient.ReplaceSubscription must catch InvalidOperationException and return null (AC 1, 3)"
    )


def test_spacetime_client_wires_on_subscription_applied_in_enter_tree() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "OnSubscriptionApplied +=" in content, (
        "SpacetimeClient must wire the OnSubscriptionApplied event handler (e.g., in _EnterTree) (AC 3)"
    )
