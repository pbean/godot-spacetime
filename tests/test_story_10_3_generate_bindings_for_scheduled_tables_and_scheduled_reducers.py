"""
Story 10.3: Generate Bindings for Scheduled Tables and Scheduled Reducers

Static contract coverage asserting:
- The Rust scheduled_test module exists with the expected table/reducer declarations
- The generated fixture includes typed handles for both scheduled and regular tables
- ScheduleAt appears as a column type (from the SpacetimeDB.ClientSDK / BSATN.Runtime NuGet)
- Scheduled reducers are server-only: process_job is NOT in RemoteReducers (correct behavior)
- Regular reducers (RecordResult) still appear in RemoteReducers normally
- The non-scheduled smoke_test generated bindings are unchanged (AC4 regression anchor)
- The fixture compiles as part of godot-spacetime.csproj
- Documentation covers the scheduled table/reducer pattern and the server-trigger distinction
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Required files exist (Task 0 / AC 1,2,3,4)
# ---------------------------------------------------------------------------

def test_story_10_3_required_files_exist() -> None:
    required = [
        # Rust scheduled_test module
        "spacetime/modules/scheduled_test/Cargo.toml",
        "spacetime/modules/scheduled_test/src/lib.rs",
        # Codegen script
        "scripts/codegen/generate-scheduled-test.sh",
        # Generated fixture root
        "tests/fixtures/generated/scheduled_test/README.md",
        "tests/fixtures/generated/scheduled_test/SpacetimeDBClient.g.cs",
        # Scheduled table
        "tests/fixtures/generated/scheduled_test/Tables/ScheduledJob.g.cs",
        "tests/fixtures/generated/scheduled_test/Types/ScheduledJob.g.cs",
        # Regular control table
        "tests/fixtures/generated/scheduled_test/Tables/JobResult.g.cs",
        "tests/fixtures/generated/scheduled_test/Types/JobResult.g.cs",
        # Regular control reducer (scheduled reducers are server-only; no ProcessJob.g.cs is generated)
        "tests/fixtures/generated/scheduled_test/Reducers/RecordResult.g.cs",
        # Documentation
        "docs/codegen.md",
    ]
    for rel in required:
        assert (ROOT / rel).is_file(), (
            f"{rel} must exist for Story 10.3 (Task 0.1)."
        )


# ---------------------------------------------------------------------------
# AC 1 — Scheduled table generates typed handle and row type
# ---------------------------------------------------------------------------

def test_scheduled_fixture_uses_distinct_namespace() -> None:
    client = _read("tests/fixtures/generated/scheduled_test/SpacetimeDBClient.g.cs")
    assert "namespace SpacetimeDB.ScheduledTestTypes" in client, (
        "The scheduled_test fixture must use a distinct namespace "
        "'SpacetimeDB.ScheduledTestTypes' (Dev Notes, Fixture Derivation Fallback)."
    )
    assert "namespace SpacetimeDB.Types" not in client, (
        "The scheduled_test fixture must not use the default namespace to avoid "
        "class conflicts with the primary smoke_test bindings."
    )


def test_remote_tables_contains_scheduled_job_and_job_result() -> None:
    client = _read("tests/fixtures/generated/scheduled_test/SpacetimeDBClient.g.cs")
    assert "AddTable(ScheduledJob = new(conn))" in client, (
        "RemoteTables must register a ScheduledJob handle so the scheduled table "
        "is accessible via GetDb<TDb>() (AC1, Task 3.1)."
    )
    assert "AddTable(JobResult = new(conn))" in client, (
        "RemoteTables must register a JobResult handle (regular control table) (AC1, Task 3.1)."
    )


def test_query_builder_includes_scheduled_and_regular_tables() -> None:
    client = _read("tests/fixtures/generated/scheduled_test/SpacetimeDBClient.g.cs")
    assert "From.ScheduledJob().ToSql()" in client, (
        "QueryBuilder.AllTablesSqlQueries() must include ScheduledJob so it is "
        "subscribable via Subscribe() (AC1, Task 3.1)."
    )
    assert "From.JobResult().ToSql()" in client, (
        "QueryBuilder.AllTablesSqlQueries() must include JobResult (control table) (AC1, Task 3.1)."
    )
    assert "ScheduledJob()" in client, (
        "QueryBuilder.From must expose a ScheduledJob() method (AC1, Task 3.1)."
    )
    assert "JobResult()" in client, (
        "QueryBuilder.From must expose a JobResult() method (AC1, Task 3.1)."
    )


def test_scheduled_job_row_type_has_schedule_at_column() -> None:
    row_type = _read("tests/fixtures/generated/scheduled_test/Types/ScheduledJob.g.cs")
    assert "SpacetimeDB.ScheduleAt" in row_type, (
        "ScheduledJob row type must use SpacetimeDB.ScheduleAt as the column type — "
        "this is a built-in SDK type from the BSATN.Runtime NuGet package, NOT a "
        "hand-written wrapper (AC1, Dev Notes, Task 3.3)."
    )
    assert 'DataMember(Name = "scheduled_at")' in row_type, (
        "The scheduled_at column must be annotated with [DataMember(Name = 'scheduled_at')] "
        "for BSATN serialization (AC1, Task 3.3)."
    )
    assert "ulong ScheduledId" in row_type or "public ulong ScheduledId" in row_type, (
        "ScheduledJob row type must have a ScheduledId (ulong) primary key field (AC1, Task 3.3)."
    )
    assert "string Payload" in row_type or "public string Payload" in row_type, (
        "ScheduledJob row type must have a Payload (string) user column (AC1, Task 3.3)."
    )


def test_scheduled_job_table_handle_exists() -> None:
    handle = _read("tests/fixtures/generated/scheduled_test/Tables/ScheduledJob.g.cs")
    assert "ScheduledJobHandle" in handle, (
        "Tables/ScheduledJob.g.cs must define a ScheduledJobHandle (AC1, Task 3.2)."
    )
    assert "RemoteTableHandle" in handle, (
        "ScheduledJobHandle must extend RemoteTableHandle<EventContext, ScheduledJob> (AC1, Task 3.2)."
    )
    assert "UniqueIndex" in handle or "UniqueIndexBase" in handle, (
        "ScheduledJobHandle must define a UniqueIndex for the scheduled_id primary key (AC1, Task 3.2)."
    )
    assert "ulong" in handle, (
        "The primary key index on ScheduledJobHandle must use ulong type (AC1, Task 3.2)."
    )


def test_scheduled_job_cols_includes_schedule_at() -> None:
    handle = _read("tests/fixtures/generated/scheduled_test/Tables/ScheduledJob.g.cs")
    assert "SpacetimeDB.ScheduleAt" in handle, (
        "ScheduledJobCols must include a Col<ScheduledJob, SpacetimeDB.ScheduleAt> entry "
        "for the scheduled_at column (AC1, Task 3.2)."
    )


def test_job_result_row_type_is_regular() -> None:
    row_type = _read("tests/fixtures/generated/scheduled_test/Types/JobResult.g.cs")
    assert "SpacetimeDB.ScheduleAt" not in row_type, (
        "JobResult is a regular (non-scheduled) table row type and must NOT contain ScheduleAt (AC4)."
    )
    assert "uint Id" in row_type or "public uint Id" in row_type, (
        "JobResult row type must have an Id (uint) primary key field (AC1, control)."
    )
    assert "string Result" in row_type or "public string Result" in row_type, (
        "JobResult row type must have a Result (string) field (AC1, control)."
    )


# ---------------------------------------------------------------------------
# AC 2 — Scheduled reducers are server-only; regular reducers are exposed
# ---------------------------------------------------------------------------

def test_scheduled_reducer_process_job_is_NOT_in_remote_reducers() -> None:
    """
    AC 2 clarification: In SpacetimeDB 1.12.0 / CLI 2.1.0, scheduled reducers
    (process_job) are server-triggered and NOT exposed in the generated
    RemoteReducers surface. There is no OnProcessJob event or client-side
    invocation method — the scheduler triggers the reducer, not the client.

    The correct scheduling pattern is to INSERT a row into the scheduled table
    with a ScheduleAt value. The server handles execution.
    """
    client = _read("tests/fixtures/generated/scheduled_test/SpacetimeDBClient.g.cs")
    reducer = _read("tests/fixtures/generated/scheduled_test/Reducers/RecordResult.g.cs")
    combined = client + reducer
    assert "ProcessJob" not in combined, (
        "process_job is a scheduled reducer (server-only). It must NOT appear as a "
        "client-callable reducer in the generated bindings. This is correct SpacetimeDB "
        "behavior — scheduled reducers are not exposed to clients via RemoteReducers (AC2, Task 4.4)."
    )


def test_regular_reducer_record_result_is_in_remote_reducers() -> None:
    reducer_file = _read("tests/fixtures/generated/scheduled_test/Reducers/RecordResult.g.cs")
    assert "OnRecordResult" in reducer_file, (
        "OnRecordResult event must be in RemoteReducers for the regular control reducer (AC2)."
    )
    assert "InvokeRecordResult" in reducer_file, (
        "InvokeRecordResult dispatch must be in RemoteReducers for the regular control reducer (AC2)."
    )
    assert '"record_result"' in reducer_file, (
        "Reducer.RecordResult must return 'record_result' as its ReducerName (AC2)."
    )
    assert "IReducerArgs" in reducer_file, (
        "Reducer.RecordResult must implement IReducerArgs (AC2)."
    )


def test_dispatch_contains_record_result_not_process_job() -> None:
    client = _read("tests/fixtures/generated/scheduled_test/SpacetimeDBClient.g.cs")
    assert "Reducer.RecordResult" in client, (
        "DbConnection.Dispatch() must include a case for Reducer.RecordResult (AC2, Task 4.3)."
    )
    assert "Reducer.ProcessJob" not in client, (
        "DbConnection.Dispatch() must NOT include a case for Reducer.ProcessJob — "
        "scheduled reducers are not dispatched as client reducer events (AC2, Task 4.4)."
    )


# ---------------------------------------------------------------------------
# AC 3 — Scheduled table/reducer distinction is documented
# ---------------------------------------------------------------------------

def test_codegen_docs_cover_scheduled_tables_section() -> None:
    docs = _read("docs/codegen.md")
    assert "Scheduled Tables" in docs, (
        "docs/codegen.md must have a 'Scheduled Tables' section (AC3, Task 5.1)."
    )


def test_codegen_docs_cover_schedule_at_type() -> None:
    docs = _read("docs/codegen.md")
    assert "ScheduleAt" in docs, (
        "docs/codegen.md must document the ScheduleAt type (AC3, Task 5.1)."
    )


def test_codegen_docs_explain_server_triggered_distinction() -> None:
    docs = _read("docs/codegen.md")
    assert "server" in docs.lower() and (
        "trigger" in docs.lower() or "scheduled" in docs.lower()
    ), (
        "docs/codegen.md must explain that scheduled reducers are server-triggered "
        "(AC3, Task 5.1)."
    )


def test_codegen_docs_show_rust_scheduling_attribute() -> None:
    docs = _read("docs/codegen.md")
    assert "scheduled(" in docs, (
        "docs/codegen.md must show the Rust #[table(scheduled(...))] attribute syntax "
        "for declaring a scheduled table (AC3, Task 5.1)."
    )


def test_codegen_docs_show_scheduling_insert_pattern() -> None:
    docs = _read("docs/codegen.md")
    assert "ScheduleAt" in docs and (
        "Interval" in docs or "Duration" in docs or "Time" in docs
    ), (
        "docs/codegen.md must show how to schedule using ScheduleAt variants "
        "when inserting a row into the scheduled table (AC3, Task 5.1)."
    )


def test_codegen_docs_do_not_use_record_result_as_the_scheduling_example() -> None:
    docs = _read("docs/codegen.md")
    scheduling_section = docs.split("### Scheduling from Client Code", 1)[1].split(
        "### Scheduled Reducers Are Server-Triggered",
        1,
    )[0]
    assert 'Reducer.RecordResult("queued via reducer")' not in scheduling_section, (
        "docs/codegen.md must not present RecordResult as the reducer that schedules "
        "jobs — it only writes to job_result and does not enqueue scheduled_job rows."
    )
    assert "Reducer.EnqueueJob" in scheduling_section, (
        "docs/codegen.md must show that scheduling happens through a regular reducer "
        "that inserts into the scheduled table (AC3)."
    )
    assert "does not enqueue `scheduled_job` rows" in docs, (
        "docs/codegen.md must explicitly distinguish the Story 10.3 control reducer "
        "from a real scheduling reducer so the example cannot be misread (AC3)."
    )


# ---------------------------------------------------------------------------
# AC 4 — Regression: smoke_test bindings are unchanged
# ---------------------------------------------------------------------------

def test_smoke_test_bindings_unchanged_by_story_10_3() -> None:
    smoke_client = _read("demo/generated/smoke_test/SpacetimeDBClient.g.cs")
    assert "ScheduledJob" not in smoke_client, (
        "demo/generated/smoke_test/SpacetimeDBClient.g.cs must NOT contain ScheduledJob — "
        "the non-scheduled module must emit unchanged bindings (AC4, Task 3.4)."
    )
    assert "ProcessJob" not in smoke_client, (
        "demo/generated/smoke_test/SpacetimeDBClient.g.cs must NOT contain ProcessJob (AC4, Task 3.4)."
    )
    assert "ScheduleAt" not in smoke_client, (
        "demo/generated/smoke_test/SpacetimeDBClient.g.cs must NOT contain ScheduleAt (AC4, Task 3.4)."
    )
    assert "SmokeTest" in smoke_client, (
        "demo/generated/smoke_test/SpacetimeDBClient.g.cs must still contain the original SmokeTest table (AC4)."
    )
    assert "Ping" in smoke_client, (
        "demo/generated/smoke_test/SpacetimeDBClient.g.cs must still contain the original Ping reducer (AC4)."
    )


# ---------------------------------------------------------------------------
# Structural: compile glob, fixture namespace, README
# ---------------------------------------------------------------------------

def test_fixture_is_compiled_by_csproj_glob() -> None:
    csproj = _read("godot-spacetime.csproj")
    assert 'tests/fixtures/generated/**/*.cs' in csproj, (
        "godot-spacetime.csproj must compile the fixture via tests/fixtures/generated/**/*.cs glob "
        "(established in Story 10.1, verified in Task 2.4)."
    )


def test_fixture_readme_marks_files_as_generated() -> None:
    readme = _read("tests/fixtures/generated/scheduled_test/README.md")
    assert "read-only generated artifact" in readme.lower() or "do not edit" in readme.lower(), (
        "tests/fixtures/generated/scheduled_test/README.md must mark the files as "
        "read-only generated artifacts (Task 2.3)."
    )


def test_rust_module_declares_scheduled_job_table_and_process_job_reducer() -> None:
    lib_rs = _read("spacetime/modules/scheduled_test/src/lib.rs")
    assert "scheduled_job" in lib_rs, (
        "spacetime/modules/scheduled_test/src/lib.rs must declare a scheduled_job table (AC1, Task 1.2)."
    )
    assert "scheduled(process_job)" in lib_rs, (
        "The scheduled_job table must use the scheduled(process_job) attribute (AC1, Task 1.2)."
    )
    assert "ScheduleAt" in lib_rs, (
        "The scheduled_job struct must include a spacetimedb::ScheduleAt field (AC1, Task 1.2)."
    )
    assert "process_job" in lib_rs, (
        "spacetime/modules/scheduled_test/src/lib.rs must declare a process_job reducer (AC2, Task 1.2)."
    )
    assert "job_result" in lib_rs, (
        "spacetime/modules/scheduled_test/src/lib.rs must declare a job_result control table (AC1, Task 1.2)."
    )
    assert "record_result" in lib_rs, (
        "spacetime/modules/scheduled_test/src/lib.rs must declare a record_result control reducer (AC2, Task 1.2)."
    )


def test_rust_module_cargo_toml_matches_smoke_test_spacetimedb_version() -> None:
    scheduled_toml = _read("spacetime/modules/scheduled_test/Cargo.toml")
    smoke_toml = _read("spacetime/modules/smoke_test/Cargo.toml")
    assert "spacetimedb" in scheduled_toml, (
        "scheduled_test/Cargo.toml must declare the spacetimedb dependency (Task 1.1)."
    )
    import re
    smoke_version = re.search(r'spacetimedb\s*=\s*["\']?=?([0-9.]+)', smoke_toml)
    if smoke_version:
        assert smoke_version.group(1) in scheduled_toml, (
            f"scheduled_test/Cargo.toml must pin the same spacetimedb version "
            f"({smoke_version.group(1)}) as smoke_test/Cargo.toml (Task 1.3)."
        )


# ---------------------------------------------------------------------------
# Gap coverage: troubleshooting.md (Task 5.2 / AC 3)
# ---------------------------------------------------------------------------

def test_troubleshooting_docs_cover_scheduled_reducers() -> None:
    """AC3 / Task 5.2: troubleshooting.md must have a scheduled reducer section."""
    docs = _read("docs/troubleshooting.md")
    assert "Scheduled Reducer" in docs or "scheduled reducer" in docs.lower(), (
        "docs/troubleshooting.md must document scheduled reducers (AC3, Task 5.2)."
    )
    assert "ScheduleAt" in docs, (
        "docs/troubleshooting.md must mention ScheduleAt so developers know how to "
        "queue the scheduler (AC3, Task 5.2)."
    )
    assert "server" in docs.lower() and (
        "trigger" in docs.lower() or "invoke" in docs.lower() or "invoked" in docs.lower()
    ), (
        "docs/troubleshooting.md must explain that scheduled reducers are server-triggered "
        "and cannot be called directly (AC3, Task 5.2)."
    )


# ---------------------------------------------------------------------------
# Gap coverage: ProcessJob.g.cs file does NOT exist (AC 2 — server-only)
# ---------------------------------------------------------------------------

def test_process_job_reducer_file_does_not_exist() -> None:
    """
    spacetime generate 2.1.0 does NOT emit Reducers/ProcessJob.g.cs for scheduled reducers.
    Verifying the file is absent (not just that its contents are absent) makes the
    server-only guarantee explicit and guards against accidental re-introduction.
    """
    absent = ROOT / "tests/fixtures/generated/scheduled_test/Reducers/ProcessJob.g.cs"
    assert not absent.exists(), (
        "Reducers/ProcessJob.g.cs must NOT exist in the scheduled_test fixture — "
        "process_job is a scheduled reducer (server-only) and spacetime generate 2.1.0 "
        "does not emit client bindings for it (AC2, Task 4.1)."
    )


# ---------------------------------------------------------------------------
# Gap coverage: JobResultHandle (control table handle) structure
# ---------------------------------------------------------------------------

def test_job_result_handle_exists_with_uint_primary_key() -> None:
    handle = _read("tests/fixtures/generated/scheduled_test/Tables/JobResult.g.cs")
    assert "JobResultHandle" in handle, (
        "Tables/JobResult.g.cs must define a JobResultHandle class (AC1, control table)."
    )
    assert "RemoteTableHandle" in handle, (
        "JobResultHandle must extend RemoteTableHandle<EventContext, JobResult> (AC1)."
    )
    assert "IdUniqueIndex" in handle, (
        "JobResultHandle must define an IdUniqueIndex for the uint primary key (AC1)."
    )
    assert "uint" in handle, (
        "The primary key index on JobResultHandle must use uint type (AC1, Task 3.2)."
    )


def test_job_result_remote_table_name_is_job_result() -> None:
    handle = _read("tests/fixtures/generated/scheduled_test/Tables/JobResult.g.cs")
    assert '"job_result"' in handle, (
        "JobResultHandle.RemoteTableName must be 'job_result' to match the Rust table "
        "name — this is the value the SDK uses for subscription SQL queries (AC1)."
    )


def test_scheduled_job_remote_table_name_is_scheduled_job() -> None:
    handle = _read("tests/fixtures/generated/scheduled_test/Tables/ScheduledJob.g.cs")
    assert '"scheduled_job"' in handle, (
        "ScheduledJobHandle.RemoteTableName must be 'scheduled_job' to match the Rust "
        "table name (AC1, Task 3.2)."
    )


# ---------------------------------------------------------------------------
# Gap coverage: ScheduledJob default constructor uses null! for ScheduledAt
# ---------------------------------------------------------------------------

def test_scheduled_job_default_ctor_uses_null_bang_for_schedule_at() -> None:
    """
    SpacetimeDB.ScheduleAt is a reference type (discriminated union). The generated
    default constructor must initialize it with null! (not new()) to satisfy the
    nullable reference type annotation without introducing a hand-written wrapper.
    This verifies the SDK type is used as-is from BSATN.Runtime.
    """
    row_type = _read("tests/fixtures/generated/scheduled_test/Types/ScheduledJob.g.cs")
    assert "null!" in row_type, (
        "ScheduledJob default constructor must use 'null!' to initialize ScheduledAt — "
        "SpacetimeDB.ScheduleAt is a SDK reference type and the generated code uses "
        "null! rather than a no-arg constructor call (AC1, Dev Notes, Task 3.3)."
    )


# ---------------------------------------------------------------------------
# Gap coverage: RecordResult reducer DataMember annotation and field
# ---------------------------------------------------------------------------

def test_record_result_reducer_has_data_member_annotation() -> None:
    reducer = _read("tests/fixtures/generated/scheduled_test/Reducers/RecordResult.g.cs")
    assert 'DataMember(Name = "result")' in reducer, (
        "Reducer.RecordResult must have [DataMember(Name = 'result')] on the Result "
        "field for BSATN deserialization (AC2)."
    )
    assert "public string Result" in reducer, (
        "Reducer.RecordResult must declare 'public string Result' (AC2)."
    )


def test_record_result_has_public_invocation_method_on_remote_reducers() -> None:
    """
    RemoteReducers.RecordResult(string result) is the client-callable method.
    This is distinct from InvokeRecordResult (internal dispatch).
    """
    reducer = _read("tests/fixtures/generated/scheduled_test/Reducers/RecordResult.g.cs")
    assert "public void RecordResult(string result)" in reducer, (
        "RemoteReducers must expose a public RecordResult(string result) method for "
        "client code to invoke the reducer (AC2)."
    )


# ---------------------------------------------------------------------------
# Gap coverage: ScheduledJobCols completeness
# ---------------------------------------------------------------------------

def test_scheduled_job_cols_has_all_three_columns() -> None:
    handle = _read("tests/fixtures/generated/scheduled_test/Tables/ScheduledJob.g.cs")
    assert "ScheduledId" in handle, (
        "ScheduledJobCols must include a Col entry for ScheduledId (ulong) (AC1, Task 3.2)."
    )
    assert "SpacetimeDB.ScheduleAt" in handle, (
        "ScheduledJobCols must include a Col entry for ScheduledAt (SpacetimeDB.ScheduleAt) (AC1)."
    )
    assert "Payload" in handle, (
        "ScheduledJobCols must include a Col entry for Payload (string) (AC1, Task 3.2)."
    )


# ---------------------------------------------------------------------------
# Gap coverage: SpacetimeDB.Type + DataContract attributes on row types
# ---------------------------------------------------------------------------

def test_scheduled_job_row_type_has_bsatn_attributes() -> None:
    row_type = _read("tests/fixtures/generated/scheduled_test/Types/ScheduledJob.g.cs")
    assert "[SpacetimeDB.Type]" in row_type, (
        "ScheduledJob row type must be annotated with [SpacetimeDB.Type] for BSATN "
        "type registration (AC1)."
    )
    assert "[DataContract]" in row_type, (
        "ScheduledJob row type must be annotated with [DataContract] for serialization (AC1)."
    )


def test_job_result_row_type_has_bsatn_attributes() -> None:
    row_type = _read("tests/fixtures/generated/scheduled_test/Types/JobResult.g.cs")
    assert "[SpacetimeDB.Type]" in row_type, (
        "JobResult row type must be annotated with [SpacetimeDB.Type] (AC1, control)."
    )
    assert "[DataContract]" in row_type, (
        "JobResult row type must be annotated with [DataContract] (AC1, control)."
    )


# ---------------------------------------------------------------------------
# Gap coverage: generated file header confirms real codegen (not hand-written)
# ---------------------------------------------------------------------------

def test_generated_client_file_has_spacetimedb_codegen_header() -> None:
    client = _read("tests/fixtures/generated/scheduled_test/SpacetimeDBClient.g.cs")
    assert "AUTOMATICALLY GENERATED BY SPACETIMEDB" in client, (
        "SpacetimeDBClient.g.cs must have the standard SpacetimeDB codegen header — "
        "this confirms the fixture is a real generated artifact, not hand-written (Task 2.2)."
    )


def test_generated_client_file_records_spacetimedb_cli_version() -> None:
    client = _read("tests/fixtures/generated/scheduled_test/SpacetimeDBClient.g.cs")
    assert "spacetimedb cli version" in client.lower(), (
        "SpacetimeDBClient.g.cs must record the spacetimedb CLI version used to generate "
        "it — this supports reproducibility and future compatibility audits (Task 2.2)."
    )
