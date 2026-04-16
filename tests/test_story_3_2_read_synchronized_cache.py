"""
Story 3.2: Read Synchronized Local Cache Data from Godot Code
Automated contract tests for all story deliverables.

Covers:
- CacheViewAdapter.cs: file existence, namespace, class, methods, IEnumerable, Cast, isolation (AC: 1, 2, 3)
- SpacetimeSdkConnectionAdapter.cs: GetDb method, reflection, XML doc, Connection regression guard (AC: 1)
- SpacetimeConnectionService.cs: _cacheViewAdapter field, SetDb wiring, GetRows delegation, isolation (AC: 1, 2, 3)
- SpacetimeClient.cs: GetRows method, IEnumerable<object>, delegation, isolation (AC: 1, 2, 3)
- docs/runtime-boundaries.md: GetRows, cast example, IEnumerable<object>, SubscriptionApplied, CacheViewAdapter, guard (AC: 1, 2, 3)
- Regression guards: prior story deliverables must still pass
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


def _section(rel: str, start: str, end: str) -> str:
    return _read(rel).split(start, 1)[1].split(end, 1)[0]


# ---------------------------------------------------------------------------
# CacheViewAdapter.cs — file existence and content (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_cache_view_adapter_file_exists() -> None:
    path = ROOT / "addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs"
    assert path.exists(), (
        "CacheViewAdapter.cs must exist at Internal/Cache/CacheViewAdapter.cs (AC 1, 2, 3)"
    )


def test_cache_view_adapter_namespace_is_godot_spacetime_runtime_cache() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "namespace GodotSpacetime.Runtime.Cache" in content, (
        "CacheViewAdapter.cs must use namespace GodotSpacetime.Runtime.Cache (AC 1)"
    )


def test_cache_view_adapter_is_internal_sealed_class() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "internal sealed class CacheViewAdapter" in content, (
        "CacheViewAdapter.cs must declare 'internal sealed class CacheViewAdapter' (AC 3)"
    )


def test_cache_view_adapter_has_set_db_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "SetDb" in content, (
        "CacheViewAdapter.cs must have SetDb method (AC 2)"
    )


def test_cache_view_adapter_has_get_rows_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "GetRows" in content, (
        "CacheViewAdapter.cs must have GetRows method (AC 1)"
    )


def test_cache_view_adapter_get_rows_accepts_string_table_name() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "string tableName" in content, (
        "CacheViewAdapter.GetRows must accept string tableName parameter (AC 1)"
    )


def test_cache_view_adapter_uses_non_generic_ienumerable() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "using System.Collections;" in content, (
        "CacheViewAdapter.cs must import System.Collections for non-generic IEnumerable (AC 1)"
    )
    assert "IEnumerable enumerable" in content or "is IEnumerable" in content, (
        "CacheViewAdapter.GetRows must use non-generic IEnumerable for tableHandle check (AC 1)"
    )


def test_cache_view_adapter_uses_cast_object() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert ".Cast<object>()" in content, (
        "CacheViewAdapter.GetRows must use .Cast<object>() to convert IEnumerable (AC 1)"
    )


def test_cache_view_adapter_uses_argument_null_exception() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "ArgumentNullException.ThrowIfNull" in content, (
        "CacheViewAdapter.GetRows must use ArgumentNullException.ThrowIfNull(tableName) (AC 1)"
    )


def test_cache_view_adapter_returns_empty_when_db_null() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "_db == null" in content or "_db is null" in content, (
        "CacheViewAdapter.GetRows must return empty sequence when _db is null (AC 1)"
    )


def test_cache_view_adapter_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "SpacetimeDB." not in content, (
        "CacheViewAdapter.cs must NOT reference SpacetimeDB.* — accesses Db via reflection only (AC 2, 3)"
    )


def test_cache_view_adapter_uses_reflection_binding_flags() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "BindingFlags.Public | BindingFlags.Instance" in content or \
           "BindingFlags.Public" in content, (
        "CacheViewAdapter.cs must use BindingFlags.Public | BindingFlags.Instance for reflection (AC 1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeSdkConnectionAdapter.cs — GetDb method (AC: 1)
# ---------------------------------------------------------------------------

def test_connection_adapter_has_get_db_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "GetDb" in content, (
        "SpacetimeSdkConnectionAdapter.cs must have GetDb method (AC 1)"
    )


def test_connection_adapter_get_db_uses_reflection_for_db_property() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert 'GetProperty("Db"' in content, (
        "SpacetimeSdkConnectionAdapter.GetDb must use GetProperty(\"Db\") via reflection (AC 1)"
    )


def test_connection_adapter_get_db_has_xml_doc_mentioning_remote_tables() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "RemoteTables" in content, (
        "SpacetimeSdkConnectionAdapter.GetDb XML doc must mention RemoteTables (AC 1)"
    )


def test_connection_adapter_still_has_connection_property() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "internal IDbConnection? Connection" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have Connection property (regression guard from Story 3.1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — _cacheViewAdapter, SetDb, GetRows (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_connection_service_has_cache_view_adapter_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_cacheViewAdapter" in content, (
        "SpacetimeConnectionService.cs must declare _cacheViewAdapter field (AC 1, 2, 3)"
    )


def test_connection_service_references_cache_view_adapter_type() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "CacheViewAdapter" in content, (
        "SpacetimeConnectionService.cs must reference CacheViewAdapter type (AC 1)"
    )


def test_connection_service_imports_runtime_cache() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "using GodotSpacetime.Runtime.Cache;" in content, (
        "SpacetimeConnectionService.cs must import 'using GodotSpacetime.Runtime.Cache;' (AC 1)"
    )


def test_connection_service_imports_system_collections_generic() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "using System.Collections.Generic;" in content, (
        "SpacetimeConnectionService.cs must import 'using System.Collections.Generic;' (AC 1)"
    )


def test_connection_service_sets_cache_view_adapter_on_connected() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_cacheViewAdapter.SetDb(_adapter.GetDb())" in content, (
        "SpacetimeConnectionService.cs must call _cacheViewAdapter.SetDb(_adapter.GetDb()) in OnConnected (AC 1)"
    )


def test_connection_service_clears_cache_view_adapter_on_disconnect() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_cacheViewAdapter.SetDb(null)" in content, (
        "SpacetimeConnectionService.cs must call _cacheViewAdapter.SetDb(null) in Disconnect (AC 1)"
    )


def test_connection_service_has_get_rows_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "GetRows" in content and "_cacheViewAdapter" in content, (
        "SpacetimeConnectionService.cs must have GetRows method delegating to _cacheViewAdapter (AC 1)"
    )


def test_connection_service_get_rows_delegates_to_cache_adapter() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_cacheViewAdapter.GetRows(tableName)" in content, (
        "SpacetimeConnectionService.GetRows must delegate to _cacheViewAdapter.GetRows(tableName) (AC 1)"
    )


def test_connection_service_clears_cache_view_on_connect_error() -> None:
    section = _section(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs",
        "void IConnectionEventSink.OnConnectError(Exception error)",
        "\n\n    void IConnectionEventSink.OnDisconnected(Exception? error)"
    )
    assert "ClearCacheView();" in section, (
        "SpacetimeConnectionService.OnConnectError must clear the cache view so GetRows() cannot expose stale rows after a failed connect"
    )


def test_connection_service_clears_cache_view_on_disconnect_error() -> None:
    section = _section(
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs",
        "private void HandleDisconnectError(Exception error)",
        "\n\n    private void Disconnect(string description)"
    )
    assert "ClearCacheView();" in section, (
        "SpacetimeConnectionService.HandleDisconnectError must clear the cache view so GetRows() returns empty when the connection is no longer active"
    )


def test_connection_service_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "SpacetimeDB." not in content, (
        "SpacetimeConnectionService.cs must NOT reference SpacetimeDB.* (isolation boundary, AC 2, 3)"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.cs — GetRows method (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_get_rows_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public IEnumerable<object> GetRows(" in content, (
        "SpacetimeClient.cs must have 'public IEnumerable<object> GetRows(' method (AC 1)"
    )


def test_spacetime_client_imports_system_collections_generic() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "using System.Collections.Generic;" in content, (
        "SpacetimeClient.cs must import 'using System.Collections.Generic;' (AC 1)"
    )


def test_spacetime_client_docs_mention_typed_and_legacy_cache_paths() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "GetDb<TDb>()" in content and "GetRows()" in content, (
        "SpacetimeClient.cs class documentation must mention both GetDb<TDb>() and GetRows() as public cache-read paths (Story 7.2 compatibility update)"
    )


def test_spacetime_client_get_rows_delegates_to_connection_service() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "_connectionService.GetRows(" in content, (
        "SpacetimeClient.GetRows must delegate to _connectionService.GetRows(tableName) (AC 1, 2)"
    )


def test_spacetime_client_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SpacetimeDB." not in content, (
        "SpacetimeClient.cs must NOT reference SpacetimeDB.* (isolation boundary, AC 2, 3)"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md — Cache section content (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_has_get_rows_reference() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "GetRows" in content, (
        "docs/runtime-boundaries.md must reference GetRows (AC 1)"
    )


def test_runtime_boundaries_has_cast_example() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "(SpacetimeDB.Types." in content or "cast" in content.lower(), (
        "docs/runtime-boundaries.md must show cast example for row types (AC 1)"
    )


def test_runtime_boundaries_references_ienumerable_object() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "IEnumerable<object>" in content, (
        "docs/runtime-boundaries.md must reference IEnumerable<object> return type (AC 1)"
    )


def test_runtime_boundaries_references_subscription_applied() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "SubscriptionApplied" in content, (
        "docs/runtime-boundaries.md must reference SubscriptionApplied timing guidance (AC 1)"
    )


def test_runtime_boundaries_references_cache_view_adapter() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "CacheViewAdapter" in content, (
        "docs/runtime-boundaries.md must reference CacheViewAdapter (AC 3)"
    )


def test_runtime_boundaries_has_empty_sequence_guard_explanation() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "empty sequence" in content or "empty" in content.lower() and "GetRows" in content, (
        "docs/runtime-boundaries.md must explain GetRows empty-sequence guard (AC 1)"
    )


def test_runtime_boundaries_spacetime_client_workflow_mentions_typed_and_legacy_cache_paths() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "SubscriptionAppliedEvent → read cache via GetDb<TDb>() / GetRows()" in content, (
        "docs/runtime-boundaries.md must show the typed GetDb<TDb>() path first while preserving GetRows() as the compatibility path (Story 7.2 compatibility update)"
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


def test_connection_service_still_has_subscribe_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Subscribe" in content and "string[]" in content, (
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


def test_connection_service_still_clears_subscription_registry_on_disconnect() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_subscriptionRegistry.Clear()" in content, (
        "SpacetimeConnectionService.cs must still call _subscriptionRegistry.Clear() in Disconnect (regression guard)"
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


def test_runtime_boundaries_still_has_subscribe_reference() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Subscribe(" in content, (
        "docs/runtime-boundaries.md must still reference Subscribe() (regression guard)"
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


# ---------------------------------------------------------------------------
# Gap coverage — CacheViewAdapter.cs imports and additional contracts
# ---------------------------------------------------------------------------

def test_cache_view_adapter_imports_system_linq() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "using System.Linq;" in content, (
        "CacheViewAdapter.cs must import System.Linq for .Cast<object>() (AC 1)"
    )


def test_cache_view_adapter_imports_system_reflection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "using System.Reflection;" in content, (
        "CacheViewAdapter.cs must import System.Reflection for BindingFlags (AC 1)"
    )


def test_cache_view_adapter_imports_system_collections_generic() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "using System.Collections.Generic;" in content, (
        "CacheViewAdapter.cs must import System.Collections.Generic for IEnumerable<object> return type (AC 1)"
    )


def test_cache_view_adapter_has_private_db_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "private object? _db" in content, (
        "CacheViewAdapter.cs must declare 'private object? _db' backing field (AC 1, 2)"
    )


def test_cache_view_adapter_get_rows_return_type_is_ienumerable_object() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "IEnumerable<object> GetRows(" in content, (
        "CacheViewAdapter.GetRows must declare return type IEnumerable<object> (AC 1)"
    )


def test_cache_view_adapter_returns_empty_when_table_handle_null() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "tableHandle is null" in content, (
        "CacheViewAdapter.GetRows must return empty sequence when tableHandle property value is null (AC 1)"
    )


def test_cache_view_adapter_throws_invalid_operation_for_unknown_table() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "InvalidOperationException" in content, (
        "CacheViewAdapter.GetRows must throw InvalidOperationException when table property is not found (AC 1)"
    )


def test_cache_view_adapter_error_message_references_remote_tables() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "RemoteTables" in content, (
        "CacheViewAdapter.GetRows error message must reference RemoteTables to guide developers (AC 1)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — SpacetimeSdkConnectionAdapter.cs GetDb() contract details
# ---------------------------------------------------------------------------

def test_connection_adapter_get_db_is_internal_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "internal object? GetDb()" in content, (
        "SpacetimeSdkConnectionAdapter.GetDb must be declared 'internal object? GetDb()' — not public (AC 1, 3)"
    )


def test_connection_adapter_get_db_uses_null_conditional_on_db_connection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "_dbConnection?." in content, (
        "SpacetimeSdkConnectionAdapter.GetDb must use null-conditional '?.' on _dbConnection for safe access (AC 1)"
    )


def test_connection_adapter_get_db_calls_get_value() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "GetValue(_dbConnection)" in content, (
        "SpacetimeSdkConnectionAdapter.GetDb must call GetValue(_dbConnection) to extract the Db property value (AC 1)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — SpacetimeConnectionService.cs field and method contracts
# ---------------------------------------------------------------------------

def test_connection_service_get_rows_has_public_ienumerable_object_signature() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "public IEnumerable<object> GetRows(" in content, (
        "SpacetimeConnectionService.GetRows must be 'public IEnumerable<object> GetRows(' (AC 1, 2)"
    )


def test_connection_service_cache_view_adapter_is_private_readonly() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "private readonly CacheViewAdapter _cacheViewAdapter" in content, (
        "SpacetimeConnectionService._cacheViewAdapter must be 'private readonly CacheViewAdapter' (AC 3)"
    )


def test_connection_service_cache_view_adapter_initialized_with_new() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_cacheViewAdapter = new()" in content, (
        "SpacetimeConnectionService._cacheViewAdapter must be initialized with '= new()' (AC 1)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — docs/runtime-boundaries.md additional references
# ---------------------------------------------------------------------------

def test_runtime_boundaries_references_remote_tables() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "RemoteTables" in content, (
        "docs/runtime-boundaries.md must reference RemoteTables type in the Cache section (AC 1)"
    )


def test_runtime_boundaries_references_invalid_operation_exception() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "InvalidOperationException" in content, (
        "docs/runtime-boundaries.md must reference InvalidOperationException for the throws-on-unknown-table guard (AC 1)"
    )


def test_runtime_boundaries_has_get_rows_player_code_example() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert 'GetRows("Player")' in content, (
        "docs/runtime-boundaries.md must show GetRows(\"Player\") code example in the Cache section (AC 1)"
    )
