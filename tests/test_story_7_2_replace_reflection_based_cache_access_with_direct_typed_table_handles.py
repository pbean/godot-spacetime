"""
Story 7.2: Replace Reflection-Based Cache Access with Direct Typed Table Handles
Static contract tests for the typed cache-read surface, compatibility fallback,
demo/docs updates, and public boundary guardrails.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_cache_view_adapter_has_typed_get_db_signature() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "internal TDb? GetDb<TDb>() where TDb : class" in content, (
        "CacheViewAdapter must expose internal TDb? GetDb<TDb>() where TDb : class (Task 1.1)"
    )


def test_cache_view_adapter_typed_get_db_returns_null_when_cache_inactive() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "if (_db == null)" in content and "return null;" in content, (
        "CacheViewAdapter.GetDb<TDb>() must return null when no cache view is active (Task 1.2)"
    )


def test_cache_view_adapter_typed_get_db_uses_direct_type_check() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "_db is TDb typedDb" in content, (
        "CacheViewAdapter.GetDb<TDb>() must return the active generated RemoteTables instance through a direct type check (Task 1.3)"
    )


def test_cache_view_adapter_typed_get_db_invalid_operation_mentions_active_and_requested_types() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "InvalidOperationException" in content and "_db.GetType()" in content and "typeof(TDb)" in content, (
        "CacheViewAdapter.GetDb<TDb>() must throw InvalidOperationException naming the active and requested types when the wrong generated module type is requested (Task 1.4)"
    )


def test_cache_view_adapter_docs_explain_typed_path_and_legacy_fallback() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs")
    assert "GetDb<TDb>()" in content and "GetRows()" in content and "fallback" in content.lower(), (
        "CacheViewAdapter XML docs must describe GetDb<TDb>() as the direct typed path and GetRows() as the backward-compatible fallback (Task 1.5)"
    )


def test_connection_service_has_typed_get_db_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "public TDb? GetDb<TDb>() where TDb : class" in content and "_cacheViewAdapter.GetDb<TDb>()" in content, (
        "SpacetimeConnectionService must expose GetDb<TDb>() and delegate to CacheViewAdapter (Task 2.1)"
    )


def test_spacetime_client_has_typed_get_db_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public TDb? GetDb<TDb>() where TDb : class" in content and "_connectionService.GetDb<TDb>()" in content, (
        "SpacetimeClient must expose GetDb<TDb>() and delegate to SpacetimeConnectionService (Task 2.2)"
    )


def test_spacetime_client_typed_get_db_docs_reference_subscription_applied_main_thread_and_idbconnection() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SubscriptionApplied" in content and "main-thread" in content and "IDbConnection" in content, (
        "SpacetimeClient.GetDb<TDb>() XML docs must describe post-SubscriptionApplied main-thread cache reads and explicitly say the method does not expose IDbConnection (Task 2.3)"
    )


def test_get_rows_remains_present_on_service_and_public_client() -> None:
    service = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    client = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public IEnumerable<object> GetRows(" in service and "public IEnumerable<object> GetRows(" in client, (
        "GetRows() must remain available on both SpacetimeConnectionService and SpacetimeClient as a compatibility path (Task 2.4)"
    )


def test_public_client_does_not_add_raw_idbconnection_accessor() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public IDbConnection" not in content and "public object GetDb" not in content, (
        "SpacetimeClient must not add a public raw IDbConnection or object-typed cache accessor (Task 2.5)"
    )


def test_demo_main_uses_typed_remote_tables_path() -> None:
    content = _read("demo/DemoMain.cs")
    assert "GetDb<RemoteTables>()" in content and "db.SmokeTest.Iter()" in content and "db.SmokeTest.Count" in content, (
        "demo/DemoMain.cs must demonstrate typed cache access through GetDb<RemoteTables>() plus SmokeTest.Iter() and SmokeTest.Count (Task 3.1)"
    )


def test_demo_readme_documents_typed_path_and_legacy_fallback() -> None:
    content = _read("demo/README.md")
    assert "GetDb<RemoteTables>()" in content and 'GetRows("SmokeTest")' in content, (
        'demo/README.md must document GetDb<RemoteTables>() as the primary cache path and GetRows("SmokeTest") as the compatibility fallback (Task 3.2)'
    )


def test_runtime_boundaries_documents_typed_path_and_compatibility_path() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "GetDb<TDb>()" in content and 'GetRows("TableName")' in content and "main-thread" in content, (
        "docs/runtime-boundaries.md must document both GetDb<TDb>() and GetRows(\"TableName\") plus the main-thread cache-read contract (Tasks 3.3, 3.4)"
    )


def test_migration_guide_maps_connection_db_patterns_to_typed_get_db_first() -> None:
    content = _read("docs/migration-from-community-plugin.md")
    assert "connection.Db.SmokeTest.Iter()" in content and "GetDb<RemoteTables>()" in content and "GetRows" in content, (
        "docs/migration-from-community-plugin.md must map community-plugin RemoteTables access to GetDb<RemoteTables>() first and GetRows() second (Task 3.5)"
    )


def test_codegen_docs_cross_link_table_handles_to_public_get_db_usage() -> None:
    content = _read("docs/codegen.md")
    assert "SpacetimeClient.GetDb<TDb>()" in content, (
        "docs/codegen.md must cross-link generated RemoteTables table handles to the public SpacetimeClient.GetDb<TDb>() usage path (Task 3.6)"
    )


def test_lifecycle_smoke_runner_has_typed_table_handle_check() -> None:
    content = _read("tests/godot_integration/LifecycleSmokeRunner.cs")
    assert "CheckTypedTableHandle" in content and "GetDb<RemoteTables>" in content, (
        "LifecycleSmokeRunner.cs must implement CheckTypedTableHandle() using GetDb<RemoteTables>() "
        "so the observe_row_change step verifies the typed table-handle path (Task 4.3)"
    )


def test_lifecycle_smoke_runner_observe_row_change_reports_all_channels() -> None:
    content = _read("tests/godot_integration/LifecycleSmokeRunner.cs")
    assert (
        "_sawTypedTableHandle" in content
        and "_sawGetRows" in content
        and "_sawRowChangedEvent" in content
        and '"typed_table_handle"' in content
        and '"get_rows"' in content
        and '"row_changed_event"' in content
    ), (
        "LifecycleSmokeRunner.cs must gate observe_row_change completion on all three observation channels "
        "(typed_table_handle, get_rows, row_changed_event) and emit them all in the step payload (Task 4.3)"
    )
