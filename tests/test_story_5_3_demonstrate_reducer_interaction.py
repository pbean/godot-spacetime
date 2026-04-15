"""
Story 5.3: Demonstrate Reducer Interaction and Troubleshooting Comparison Paths
Automated contract tests for all story deliverables.

Covers:
- Task 4.1: Existence tests — demo/DemoMain.cs, demo/README.md, demo/scenes/reducer_smoke.tscn
- Task 4.2: demo/DemoMain.cs content tests (AC: 1, 3)
- Task 4.3: demo/README.md content tests (AC: 2, 3)
- Task 4.4: demo/scenes/reducer_smoke.tscn content tests
- Task 4.5: Regression guards — all prior deliverables remain intact
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _assert_in_order(content: str, snippets: tuple[str, ...]) -> None:
    cursor = 0
    for snippet in snippets:
        index = content.find(snippet, cursor)
        assert index != -1, f"Expected to find {snippet!r} after offset {cursor}"
        cursor = index + len(snippet)


# ---------------------------------------------------------------------------
# Task 4.1: Existence tests
# ---------------------------------------------------------------------------

def test_demo_main_cs_exists() -> None:
    assert (ROOT / "demo" / "DemoMain.cs").exists(), (
        "demo/DemoMain.cs must exist after Story 5.3 modification (Task 4.1)"
    )


def test_demo_readme_exists() -> None:
    assert (ROOT / "demo" / "README.md").exists(), (
        "demo/README.md must exist after Story 5.3 modification (Task 4.1)"
    )


def test_reducer_smoke_tscn_exists() -> None:
    assert (ROOT / "demo" / "scenes" / "reducer_smoke.tscn").exists(), (
        "demo/scenes/reducer_smoke.tscn must exist — new scene created in Task 2 (Task 4.1)"
    )


# ---------------------------------------------------------------------------
# Task 4.2: demo/DemoMain.cs content tests (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_demo_main_cs_has_reducers_namespace_import() -> None:
    content = _read("demo/DemoMain.cs")
    assert "GodotSpacetime.Reducers" in content, (
        "demo/DemoMain.cs must import 'GodotSpacetime.Reducers' for ReducerCallResult, ReducerCallError, ReducerFailureCategory (AC: 1)"
    )


def test_demo_main_cs_has_spacetimedb_types_namespace_import() -> None:
    content = _read("demo/DemoMain.cs")
    assert "SpacetimeDB.Types" in content, (
        "demo/DemoMain.cs must import 'SpacetimeDB.Types' for Reducer.Ping generated binding type (AC: 1)"
    )


def test_demo_main_cs_wires_reducer_call_succeeded() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallSucceeded" in content, (
        "demo/DemoMain.cs must wire 'ReducerCallSucceeded' signal for reducer success handling (AC: 1)"
    )


def test_demo_main_cs_wires_reducer_call_failed() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallFailed" in content, (
        "demo/DemoMain.cs must wire 'ReducerCallFailed' signal for reducer failure handling (AC: 1)"
    )


def test_demo_main_cs_has_on_reducer_call_succeeded_handler() -> None:
    content = _read("demo/DemoMain.cs")
    assert "OnReducerCallSucceeded" in content, (
        "demo/DemoMain.cs must define 'OnReducerCallSucceeded' handler method (AC: 1)"
    )


def test_demo_main_cs_has_on_reducer_call_failed_handler() -> None:
    content = _read("demo/DemoMain.cs")
    assert "OnReducerCallFailed" in content, (
        "demo/DemoMain.cs must define 'OnReducerCallFailed' handler method (AC: 1)"
    )


def test_demo_main_cs_calls_invoke_reducer() -> None:
    content = _read("demo/DemoMain.cs")
    assert "InvokeReducer" in content, (
        "demo/DemoMain.cs must call 'InvokeReducer' to invoke a reducer (AC: 1)"
    )


def test_demo_main_cs_uses_reducer_ping_type() -> None:
    content = _read("demo/DemoMain.cs")
    assert "Reducer.Ping" in content, (
        "demo/DemoMain.cs must use 'Reducer.Ping' generated type — not a string or custom class (AC: 1)"
    )


def test_demo_main_cs_logs_result_reducer_name() -> None:
    content = _read("demo/DemoMain.cs")
    assert "result.ReducerName" in content, (
        "demo/DemoMain.cs must log 'result.ReducerName' to identify the reducer in the success path (AC: 1)"
    )


def test_demo_main_cs_logs_result_invocation_id() -> None:
    content = _read("demo/DemoMain.cs")
    assert "result.InvocationId" in content, (
        "demo/DemoMain.cs must log 'result.InvocationId' for invocation correlation in the success path (AC: 1)"
    )


def test_demo_main_cs_logs_error_reducer_name() -> None:
    content = _read("demo/DemoMain.cs")
    assert "error.ReducerName" in content, (
        "demo/DemoMain.cs must log 'error.ReducerName' to identify the reducer in the failure path (AC: 1)"
    )


def test_demo_main_cs_logs_error_failure_category() -> None:
    content = _read("demo/DemoMain.cs")
    assert "error.FailureCategory" in content, (
        "demo/DemoMain.cs must surface 'error.FailureCategory' for troubleshooting branching (AC: 1)"
    )


def test_demo_main_cs_logs_error_recovery_guidance() -> None:
    content = _read("demo/DemoMain.cs")
    assert "error.RecoveryGuidance" in content, (
        "demo/DemoMain.cs must surface 'error.RecoveryGuidance' for recovery path guidance (AC: 1)"
    )


def test_demo_main_cs_logs_error_message() -> None:
    content = _read("demo/DemoMain.cs")
    assert "error.ErrorMessage" in content, (
        "demo/DemoMain.cs must surface 'error.ErrorMessage' for human-readable failure message (AC: 1)"
    )


def test_demo_main_cs_documents_async_nature_in_output() -> None:
    content = _read("demo/DemoMain.cs")
    assert "awaiting server acknowledgement" in content, (
        "demo/DemoMain.cs must print 'awaiting server acknowledgement' to document the async nature of InvokeReducer (AC: 1)"
    )


def test_demo_main_cs_success_handler_uses_typed_parameter() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallResult result" in content, (
        "demo/DemoMain.cs must use typed 'ReducerCallResult result' parameter — not object — in success handler signature (AC: 1)"
    )


def test_demo_main_cs_failure_handler_uses_typed_parameter() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallError error" in content, (
        "demo/DemoMain.cs must use typed 'ReducerCallError error' parameter — not object — in failure handler signature (AC: 1)"
    )


def test_demo_main_cs_invokes_ping_after_handle_guard_and_row_count() -> None:
    content = _read("demo/DemoMain.cs")
    method = content[
        content.index("private void OnSubscriptionApplied")
        : content.index("private void OnSubscriptionFailed")
    ]
    assert "if (_subscriptionHandle != e.Handle)" in method, (
        "demo/DemoMain.cs must keep the SubscriptionApplied handle guard before reducer invocation (Task 1.5)"
    )
    _assert_in_order(
        method,
        (
            "if (_subscriptionHandle != e.Handle)",
            'GD.Print($"[Demo] Subscription applied — {rows.Count} row(s) in smoke_test");',
            "_client!.InvokeReducer(new Reducer.Ping());",
            'GD.Print("[Demo] Ping reducer invoked — awaiting server acknowledgement");',
        ),
    )


def test_demo_main_cs_success_log_matches_documented_contract() -> None:
    content = _read("demo/DemoMain.cs")
    assert """GD.Print($"[Demo] Reducer '{result.ReducerName}' succeeded (id: {result.InvocationId})");""" in content, (
        "demo/DemoMain.cs must keep the documented reducer success log contract for troubleshooting comparison (AC: 1, 2)"
    )


def test_demo_main_cs_failure_log_matches_documented_contract() -> None:
    content = _read("demo/DemoMain.cs")
    assert """GD.Print($"[Demo] Reducer '{error.ReducerName}' failed — {error.FailureCategory}: {error.ErrorMessage} | guidance: {error.RecoveryGuidance}");""" in content, (
        "demo/DemoMain.cs must keep the documented reducer failure log contract for troubleshooting comparison (AC: 1, 2)"
    )


# ---------------------------------------------------------------------------
# Task 4.3: demo/README.md content tests (AC: 2, 3)
# ---------------------------------------------------------------------------

def test_demo_readme_has_reducer_section() -> None:
    content = _read("demo/README.md")
    assert "## Reducer" in content, (
        "demo/README.md must contain a '## Reducer' section documenting reducer interaction (AC: 2)"
    )


def test_demo_readme_references_ping_reducer() -> None:
    content = _read("demo/README.md")
    assert "Ping" in content, (
        "demo/README.md must reference 'Ping' reducer (AC: 2)"
    )


def test_demo_readme_documents_invoke_reducer() -> None:
    content = _read("demo/README.md")
    assert "InvokeReducer" in content, (
        "demo/README.md must document 'InvokeReducer' call (AC: 2)"
    )


def test_demo_readme_mentions_reducer_call_succeeded_lifecycle_term() -> None:
    content = _read("demo/README.md")
    assert "ReducerCallSucceeded" in content, (
        "demo/README.md must mention 'ReducerCallSucceeded' lifecycle term aligned with docs (AC: 3)"
    )


def test_demo_readme_mentions_reducer_call_failed_lifecycle_term() -> None:
    content = _read("demo/README.md")
    assert "ReducerCallFailed" in content, (
        "demo/README.md must mention 'ReducerCallFailed' lifecycle term aligned with docs (AC: 3)"
    )


def test_demo_readme_documents_success_path() -> None:
    content = _read("demo/README.md")
    assert "succeeded" in content, (
        "demo/README.md must document the 'succeeded' success path output (AC: 2)"
    )


def test_demo_readme_documents_failure_path() -> None:
    content = _read("demo/README.md")
    assert "failed" in content, (
        "demo/README.md must document the 'failed' failure path output (AC: 2)"
    )


def test_demo_readme_documents_failure_category() -> None:
    content = _read("demo/README.md")
    assert ("FailureCategory" in content or "ReducerFailureCategory" in content), (
        "demo/README.md must document 'FailureCategory' or 'ReducerFailureCategory' for troubleshooting branching (AC: 2)"
    )


def test_demo_readme_documents_recovery_guidance() -> None:
    content = _read("demo/README.md")
    assert "RecoveryGuidance" in content, (
        "demo/README.md must document 'RecoveryGuidance' for recovery path (AC: 2)"
    )


def test_demo_readme_documents_async_nature() -> None:
    content = _read("demo/README.md")
    assert "awaiting server acknowledgement" in content, (
        "demo/README.md must document the async nature of InvokeReducer with 'awaiting server acknowledgement' (AC: 2)"
    )


def test_demo_readme_references_runtime_boundaries_md() -> None:
    content = _read("demo/README.md")
    assert "docs/runtime-boundaries.md" in content, (
        "demo/README.md must reference 'docs/runtime-boundaries.md' as the canonical lifecycle term reference (AC: 3)"
    )


def test_demo_readme_distinguishes_programming_faults_from_server_failures() -> None:
    content = _read("demo/README.md")
    assert "do **not** fire `ReducerCallFailed`" in content and "GD.PushError" in content, (
        "demo/README.md must distinguish calling-code programming faults from server-side reducer failures (AC: 2, 3)"
    )


def test_demo_readme_documents_programming_fault_examples() -> None:
    content = _read("demo/README.md")
    assert "before `Connected`, with `null`, or with a non-generated reducer arg" in content, (
        "demo/README.md must document concrete programming-fault examples for the reducer troubleshooting comparison path (AC: 2, 3)"
    )


# ---------------------------------------------------------------------------
# Task 4.4: demo/scenes/reducer_smoke.tscn content tests
# ---------------------------------------------------------------------------

def test_reducer_smoke_tscn_has_node_name() -> None:
    content = _read("demo/scenes/reducer_smoke.tscn")
    assert "ReducerSmoke" in content, (
        "demo/scenes/reducer_smoke.tscn must contain node name 'ReducerSmoke' (Task 4.4)"
    )


def test_reducer_smoke_tscn_has_valid_godot_scene_header() -> None:
    content = _read("demo/scenes/reducer_smoke.tscn")
    assert "gd_scene" in content, (
        "demo/scenes/reducer_smoke.tscn must contain 'gd_scene' valid Godot scene header (Task 4.4)"
    )


# ---------------------------------------------------------------------------
# Task 4.5: Regression guards — all prior deliverables must remain intact
# ---------------------------------------------------------------------------

def test_demo_main_cs_still_exists_regression() -> None:
    assert (ROOT / "demo" / "DemoMain.cs").exists(), (
        "demo/DemoMain.cs must still exist — Story 5.1 deliverable (regression guard)"
    )


def test_demo_main_tscn_still_exists() -> None:
    assert (ROOT / "demo" / "DemoMain.tscn").exists(), (
        "demo/DemoMain.tscn must still exist — Story 5.1 deliverable (regression guard)"
    )


def test_demo_autoload_bootstrap_cs_still_exists() -> None:
    assert (ROOT / "demo" / "autoload" / "DemoBootstrap.cs").exists(), (
        "demo/autoload/DemoBootstrap.cs must still exist — Story 5.1 deliverable (regression guard)"
    )


def test_demo_scenes_connection_smoke_tscn_still_exists() -> None:
    assert (ROOT / "demo" / "scenes" / "connection_smoke.tscn").exists(), (
        "demo/scenes/connection_smoke.tscn must still exist — Story 5.1 deliverable (regression guard)"
    )


def test_project_godot_still_registers_demo_bootstrap_autoload() -> None:
    content = _read("project.godot")
    assert "DemoBootstrap" in content, (
        "project.godot must still register DemoBootstrap autoload — Story 5.1 critical fix (regression guard)"
    )


def test_docs_quickstart_md_still_exists() -> None:
    assert (ROOT / "docs" / "quickstart.md").exists(), (
        "docs/quickstart.md must still exist — Story 1.10 deliverable (regression guard)"
    )


def test_docs_install_md_still_exists() -> None:
    assert (ROOT / "docs" / "install.md").exists(), (
        "docs/install.md must still exist — Story 1.1 deliverable (regression guard)"
    )


def test_docs_codegen_md_still_exists() -> None:
    assert (ROOT / "docs" / "codegen.md").exists(), (
        "docs/codegen.md must still exist — Story 1.6/1.7 deliverable (regression guard)"
    )


def test_demo_generated_smoke_test_directory_still_exists() -> None:
    assert (ROOT / "demo" / "generated" / "smoke_test").is_dir(), (
        "demo/generated/smoke_test/ directory must still exist — Story 1.6 deliverable (regression guard)"
    )


def test_demo_generated_reducers_ping_still_exists() -> None:
    assert (ROOT / "demo" / "generated" / "smoke_test" / "Reducers" / "Ping.g.cs").exists(), (
        "demo/generated/smoke_test/Reducers/Ping.g.cs must still exist — generated binding (regression guard)"
    )


def test_demo_generated_spacetimedbclient_still_exists() -> None:
    assert (ROOT / "demo" / "generated" / "smoke_test" / "SpacetimeDBClient.g.cs").exists(), (
        "demo/generated/smoke_test/SpacetimeDBClient.g.cs must still exist — generated binding (regression guard)"
    )


def test_demo_generated_tables_smoke_test_still_exists() -> None:
    assert (ROOT / "demo" / "generated" / "smoke_test" / "Tables" / "SmokeTest.g.cs").exists(), (
        "demo/generated/smoke_test/Tables/SmokeTest.g.cs must still exist — generated binding (regression guard)"
    )


def test_spacetime_modules_smoke_test_lib_rs_still_exists() -> None:
    assert (ROOT / "spacetime" / "modules" / "smoke_test" / "src" / "lib.rs").exists(), (
        "spacetime/modules/smoke_test/src/lib.rs must still exist — Rust source module (regression guard)"
    )


def test_addons_spacetime_client_cs_still_exists() -> None:
    assert (ROOT / "addons" / "godot_spacetime" / "src" / "Public" / "SpacetimeClient.cs").exists(), (
        "addons/godot_spacetime/src/Public/SpacetimeClient.cs must still exist — public SDK boundary (regression guard)"
    )


def test_demo_readme_still_has_token_store_story_52() -> None:
    content = _read("demo/README.md")
    assert "TokenStore" in content, (
        "demo/README.md must still contain 'TokenStore' — Story 5.2 auth section intact (regression guard)"
    )


def test_demo_readme_still_has_subscription_section_story_52() -> None:
    content = _read("demo/README.md")
    assert "## Subscription" in content, (
        "demo/README.md must still contain '## Subscription' — Story 5.2 subscription section intact (regression guard)"
    )


def test_demo_main_cs_still_has_subscription_applied_story_52() -> None:
    content = _read("demo/DemoMain.cs")
    assert "SubscriptionApplied" in content, (
        "demo/DemoMain.cs must still contain 'SubscriptionApplied' — Story 5.2 signal intact (regression guard)"
    )


def test_demo_main_cs_still_has_project_settings_token_store_story_52() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ProjectSettingsTokenStore" in content, (
        "demo/DemoMain.cs must still contain 'ProjectSettingsTokenStore' — Story 5.2 auth intact (regression guard)"
    )


# ---------------------------------------------------------------------------
# Gap tests: Signal wiring — double-wire pattern and _ExitTree cleanup
# ---------------------------------------------------------------------------

def test_demo_main_cs_uses_double_wiring_pattern_for_reducer_call_succeeded() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallSucceeded -=" in content and "ReducerCallSucceeded +=" in content, (
        "demo/DemoMain.cs must use '-= then +=' pattern for ReducerCallSucceeded to prevent duplicate handlers (Task 1.3)"
    )


def test_demo_main_cs_uses_double_wiring_pattern_for_reducer_call_failed() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallFailed -=" in content and "ReducerCallFailed +=" in content, (
        "demo/DemoMain.cs must use '-= then +=' pattern for ReducerCallFailed to prevent duplicate handlers (Task 1.3)"
    )


def test_demo_main_cs_unsubscribes_reducer_call_succeeded_in_exit_tree() -> None:
    content = _read("demo/DemoMain.cs")
    exit_tree_section = content[content.index("_ExitTree"):]
    assert "ReducerCallSucceeded -=" in exit_tree_section, (
        "demo/DemoMain.cs must unsubscribe 'ReducerCallSucceeded' handler in _ExitTree() cleanup (Task 1.4)"
    )


def test_demo_main_cs_unsubscribes_reducer_call_failed_in_exit_tree() -> None:
    content = _read("demo/DemoMain.cs")
    exit_tree_section = content[content.index("_ExitTree"):]
    assert "ReducerCallFailed -=" in exit_tree_section, (
        "demo/DemoMain.cs must unsubscribe 'ReducerCallFailed' handler in _ExitTree() cleanup (Task 1.4)"
    )


# ---------------------------------------------------------------------------
# Gap tests: reducer_smoke.tscn scene format and node type
# ---------------------------------------------------------------------------

def test_reducer_smoke_tscn_has_godot4_format_version() -> None:
    content = _read("demo/scenes/reducer_smoke.tscn")
    assert "format=3" in content, (
        "demo/scenes/reducer_smoke.tscn must contain 'format=3' matching Godot 4 scene format (Task 4.4)"
    )


def test_reducer_smoke_tscn_has_node_type_node() -> None:
    content = _read("demo/scenes/reducer_smoke.tscn")
    assert 'type="Node"' in content, (
        'demo/scenes/reducer_smoke.tscn must use type="Node" — minimal placeholder node with no script (Task 4.4)'
    )


# ---------------------------------------------------------------------------
# Gap tests: README section ordering
# ---------------------------------------------------------------------------

def test_demo_readme_reducer_section_placed_after_subscription_section() -> None:
    content = _read("demo/README.md")
    subscription_idx = content.index("## Subscription")
    reducer_idx = content.index("## Reducer")
    assert reducer_idx > subscription_idx, (
        "demo/README.md — '## Reducer Interaction' section must appear after '## Subscription and Live State' (Task 3.1)"
    )


def test_demo_readme_reducer_section_placed_before_reset_section() -> None:
    content = _read("demo/README.md")
    reducer_idx = content.index("## Reducer")
    reset_idx = content.index("## Reset")
    assert reducer_idx < reset_idx, (
        "demo/README.md — '## Reducer Interaction' section must appear before '## Reset to Clean State' (Task 3.1)"
    )


# ---------------------------------------------------------------------------
# Gap tests: README documentation depth (async, enum values, SDK reference)
# ---------------------------------------------------------------------------

def test_demo_readme_mentions_frame_tick_for_async_delivery() -> None:
    content = _read("demo/README.md")
    assert "FrameTick" in content, (
        "demo/README.md must mention 'FrameTick' to explain the async delivery mechanism for reducer results (AC: 2)"
    )


def test_demo_readme_documents_out_of_energy_failure_category() -> None:
    content = _read("demo/README.md")
    assert "OutOfEnergy" in content, (
        "demo/README.md must document 'OutOfEnergy' ReducerFailureCategory value for troubleshooting branching (AC: 2)"
    )


def test_demo_readme_references_reducer_failure_category_cs_path() -> None:
    content = _read("demo/README.md")
    assert "ReducerFailureCategory.cs" in content, (
        "demo/README.md must reference 'ReducerFailureCategory.cs' SDK path for enum value documentation (AC: 3)"
    )


# ---------------------------------------------------------------------------
# Gap tests: DemoMain.cs exact log message format
# ---------------------------------------------------------------------------

def test_demo_main_cs_has_ping_invoked_log_message() -> None:
    content = _read("demo/DemoMain.cs")
    assert "[Demo] Ping reducer invoked" in content, (
        "demo/DemoMain.cs must print '[Demo] Ping reducer invoked' as part of the documented output sequence (AC: 1)"
    )
