"""
Story 7.4: Execute One-Off SQL Queries Outside Active Subscriptions
Static contract tests for the public query surface, error model, isolation boundary,
and documentation updates.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_spacetime_client_exposes_query_async_entrypoint() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public Task<TRow[]> QueryAsync<TRow>(string sqlClause, TimeSpan? timeout = null)" in content, (
        "SpacetimeClient must expose QueryAsync<TRow>(string sqlClause, TimeSpan? timeout = null) "
        "with an Async suffix and generated row type generic (Task 1.1, AC1)"
    )


def test_spacetime_client_query_docs_keep_raw_transport_types_out_of_public_signature() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "IDbConnection" in content and "DbConnection" in content and "RemoteTableHandleBase" in content, (
        "SpacetimeClient.QueryAsync XML docs must explicitly state that the public boundary "
        "does not expose raw IDbConnection, DbConnection, or RemoteTableHandleBase types (Tasks 1.2, 1.5)"
    )


def test_connection_service_exposes_query_async_delegate() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "public Task<TRow[]> QueryAsync<TRow>(string sqlClause, TimeSpan? timeout = null)" in content and "_queryAdapter.QueryAsync<TRow>(remoteTables, sqlClause, timeout)" in content, (
        "SpacetimeConnectionService must expose QueryAsync<TRow>() and delegate to the internal query adapter "
        "using the active generated RemoteTables object (Task 3.1, AC1/AC2)"
    )


def test_connection_service_keeps_programming_fault_guards_explicit() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "if (string.IsNullOrWhiteSpace(sqlClause))" in content and 'throw new ArgumentException("QueryAsync() requires a non-empty SQL clause.", nameof(sqlClause));' in content, (
        "Blank SQL must remain an explicit ArgumentException programming fault instead of a typed runtime query failure (AC3)"
    )
    assert "if (CurrentStatus.State != ConnectionState.Connected)" in content and "QueryAsync() requires an active Connected session." in content, (
        "Disconnected-state queries must remain an explicit InvalidOperationException programming fault (AC3)"
    )


def test_public_query_error_model_files_exist_and_expose_expected_contract() -> None:
    category = _read("addons/godot_spacetime/src/Public/Queries/OneOffQueryFailureCategory.cs")
    error = _read("addons/godot_spacetime/src/Public/Queries/OneOffQueryError.cs")

    for expected in ("InvalidQuery", "TimedOut", "Failed", "Unknown"):
        assert expected in category, (
            f"OneOffQueryFailureCategory must define {expected!r} (Task 2.2)"
        )

    assert "class OneOffQueryError : Exception" in error, (
        "OneOffQueryError must itself be the thrown typed recoverable error surface (Task 2.5, AC3)"
    )
    for expected in (
        "RequestedRowType",
        "TargetTable",
        "SqlClause",
        "FailureCategory",
        "ErrorMessage",
        "RecoveryGuidance",
        "RequestedAt",
        "FailedAt",
    ):
        assert expected in error, (
            f"OneOffQueryError must expose {expected} (Task 2.4, AC3)"
        )
    assert "RequestedAt = requestedAt;" in error and "FailedAt = DateTimeOffset.UtcNow;" in error, (
        "OneOffQueryError must populate UTC request/failure timestamps, not just declare the properties (Task 2.4, AC3)"
    )


def test_query_adapter_exists_only_under_internal_platform_dotnet() -> None:
    adapter_rel = "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkQueryAdapter.cs"
    adapter_path = ROOT / adapter_rel
    assert adapter_path.exists(), (
        "SpacetimeSdkQueryAdapter.cs must exist under Internal/Platform/DotNet/ (Task 3.2)"
    )

    offenders: list[str] = []
    for path in (ROOT / "addons/godot_spacetime/src").rglob("*.cs"):
        rel = path.relative_to(ROOT).as_posix()
        if rel == adapter_rel:
            continue

        content = path.read_text(encoding="utf-8")
        if "RemoteQuery(" in content or "IRemoteTableHandle" in content:
            offenders.append(rel)

    assert not offenders, (
        "SDK query-type references must stay isolated to Internal/Platform/DotNet/SpacetimeSdkQueryAdapter.cs. "
        f"Found query-type references in: {offenders}"
    )


def test_query_adapter_enforces_timeout_contract_and_typed_timeout_mapping() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkQueryAdapter.cs")
    assert "private static readonly TimeSpan DefaultTimeout = TimeSpan.FromSeconds(30);" in content and "timeout ?? DefaultTimeout" in content, (
        "QueryAsync must apply a default timeout so one-off queries cannot await forever when the caller omits timeout (Task 3.6, AC3)"
    )
    assert "timeout.Value <= TimeSpan.Zero" in content and '\"QueryAsync() timeout must be greater than zero when provided.\"' in content, (
        "Non-positive explicit timeouts must fail fast as programming faults rather than leaking into runtime query execution (AC3)"
    )
    assert "Task.WhenAny(queryTask, timeoutTask)" in content and "OneOffQueryFailureCategory.TimedOut" in content, (
        "The adapter must convert elapsed query timeouts into the typed TimedOut failure category (Task 3.6, AC3)"
    )


def test_spacetime_client_does_not_add_raw_query_transport_accessors() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "public IDbConnection" not in content and "public DbConnection" not in content and "public RemoteTableHandleBase" not in content, (
        "SpacetimeClient must not expose new raw transport/query accessors to support one-off queries (AC1/AC2)"
    )


def test_runtime_boundaries_docs_distinguish_cache_reads_subscriptions_and_one_off_queries() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "GetDb<TDb>()" in content and 'GetRows("TableName")' in content, (
        "runtime-boundaries.md must still document the local cache read paths from Story 7.2 (Task 4.2 regression guard)"
    )
    assert "QueryAsync<SmokeTest>" in content and "does **not** populate" in content and "Subscribe(...)" in content, (
        "runtime-boundaries.md must explicitly contrast cache reads, live subscriptions, and one-off query round-trips "
        "that do not populate the cache (Tasks 4.1, 4.2, 4.3)"
    )


def test_codegen_docs_note_table_handles_inherit_one_off_query_capability() -> None:
    content = _read("docs/codegen.md")
    assert "RemoteQuery(string)" in content and "Iter()" in content and "Count" in content and "Find(...)" in content and "Filter(...)" in content, (
        "docs/codegen.md must state that generated table handles inherit one-off query capability in addition to "
        "local Iter/Count/Find/Filter operations (Task 4.4)"
    )


def test_troubleshooting_docs_cover_invalid_sql_timeout_and_server_failures() -> None:
    content = _read("docs/troubleshooting.md")
    assert "## One-Off Queries" in content and "InvalidQuery" in content and "TimedOut" in content and "Failed" in content, (
        "docs/troubleshooting.md must cover one-off query troubleshooting for invalid SQL, timeout, and server-side failures (Task 4.5)"
    )


def test_demo_readme_documents_query_example_without_subscription() -> None:
    content = _read("demo/README.md")
    assert "QueryAsync<SmokeTest>" in content and "without creating a subscription" in content and "without backfilling the cache" in content, (
        "demo/README.md must include a one-off query example and explain that it fetches typed rows without "
        "creating a subscription or backfilling the cache (Task 4.6)"
    )


def test_story_7_2_and_7_3_docs_remain_intact() -> None:
    runtime_boundaries = _read("docs/runtime-boundaries.md")
    codegen = _read("docs/codegen.md")
    assert "GetDb<TDb>()" in runtime_boundaries and "Value.Filter" in runtime_boundaries, (
        "Story 7.2 typed cache access and Story 7.3 BTree filter docs must remain intact in runtime-boundaries.md"
    )
    assert 'Value.Filter("hello")' in codegen, (
        "Story 7.3 BTree filter usage example must remain intact in docs/codegen.md"
    )
