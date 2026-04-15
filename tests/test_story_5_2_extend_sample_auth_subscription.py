"""
Story 5.2: Extend the Sample Through Auth, Session Resume, and Live Subscription Flow
Automated contract tests for all story deliverables.

Covers:
- Task 3.1: Existence tests — demo/DemoMain.cs and demo/README.md still present
- Task 3.2: demo/DemoMain.cs content tests (AC: 1, 3)
- Task 3.3: demo/README.md content tests (AC: 2, 3)
- Task 3.4: Regression guards — all Story 5.1 deliverables remain intact
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Task 3.1: Existence tests
# ---------------------------------------------------------------------------

def test_demo_main_cs_exists() -> None:
    assert (ROOT / "demo" / "DemoMain.cs").exists(), (
        "demo/DemoMain.cs must exist after Story 5.2 modification (Task 3.1)"
    )


def test_demo_readme_exists() -> None:
    assert (ROOT / "demo" / "README.md").exists(), (
        "demo/README.md must exist after Story 5.2 modification (Task 3.1)"
    )


# ---------------------------------------------------------------------------
# Task 3.2: demo/DemoMain.cs content tests (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_demo_main_cs_has_auth_namespace_import() -> None:
    content = _read("demo/DemoMain.cs")
    assert "GodotSpacetime.Runtime.Auth" in content, (
        "demo/DemoMain.cs must import 'GodotSpacetime.Runtime.Auth' for auth namespace (AC: 1)"
    )


def test_demo_main_cs_has_subscriptions_namespace_import() -> None:
    content = _read("demo/DemoMain.cs")
    assert "GodotSpacetime.Subscriptions" in content, (
        "demo/DemoMain.cs must import 'GodotSpacetime.Subscriptions' for subscription types (AC: 1)"
    )


def test_demo_main_cs_has_project_settings_token_store() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ProjectSettingsTokenStore" in content, (
        "demo/DemoMain.cs must use 'ProjectSettingsTokenStore' to wire auth with built-in token persistence (AC: 1)"
    )


def test_demo_main_cs_has_token_store_assignment() -> None:
    content = _read("demo/DemoMain.cs")
    assert "TokenStore" in content, (
        "demo/DemoMain.cs must assign the 'TokenStore' property for token persistence (AC: 1)"
    )


def test_demo_main_cs_declares_subscription_handle_field() -> None:
    content = _read("demo/DemoMain.cs")
    assert "_subscriptionHandle" in content, (
        "demo/DemoMain.cs must declare '_subscriptionHandle' field for subscription lifecycle management (AC: 1)"
    )


def test_demo_main_cs_calls_subscribe() -> None:
    content = _read("demo/DemoMain.cs")
    assert "Subscribe(" in content, (
        "demo/DemoMain.cs must call 'Subscribe(' to initiate the subscription (AC: 1)"
    )


def test_demo_main_cs_subscribes_to_smoke_test_table() -> None:
    content = _read("demo/DemoMain.cs")
    assert "smoke_test" in content, (
        "demo/DemoMain.cs must reference 'smoke_test' as the subscription target table name (AC: 1)"
    )


def test_demo_main_cs_handles_subscription_applied() -> None:
    content = _read("demo/DemoMain.cs")
    assert "SubscriptionApplied" in content, (
        "demo/DemoMain.cs must handle 'SubscriptionApplied' signal to confirm subscription (AC: 1)"
    )


def test_demo_main_cs_handles_subscription_failed() -> None:
    content = _read("demo/DemoMain.cs")
    assert "SubscriptionFailed" in content, (
        "demo/DemoMain.cs must handle 'SubscriptionFailed' signal to observe subscription errors (AC: 1)"
    )


def test_demo_main_cs_handles_row_changed() -> None:
    content = _read("demo/DemoMain.cs")
    assert "RowChanged" in content, (
        "demo/DemoMain.cs must handle 'RowChanged' signal to observe live row mutations (AC: 1)"
    )


def test_demo_main_cs_calls_get_rows() -> None:
    content = _read("demo/DemoMain.cs")
    assert 'GetRows("SmokeTest")' in content, (
        'demo/DemoMain.cs must call \'GetRows("SmokeTest")\' to read the local cache with the generated PascalCase table name (AC: 1)'
    )


def test_demo_main_cs_handles_connection_opened() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ConnectionOpened" in content, (
        "demo/DemoMain.cs must handle 'ConnectionOpened' signal to log the session identity (AC: 1)"
    )


def test_demo_main_cs_handles_connection_closed() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ConnectionClosed" in content, (
        "demo/DemoMain.cs must handle 'ConnectionClosed' to reset its demo subscription state after a disconnect (AC: 1)"
    )


def test_demo_main_cs_calls_unsubscribe() -> None:
    content = _read("demo/DemoMain.cs")
    assert "Unsubscribe" in content, (
        "demo/DemoMain.cs must call 'Unsubscribe' to clean up the subscription in _ExitTree (AC: 1)"
    )


def test_demo_main_cs_guards_unsubscribe_with_active_status() -> None:
    content = _read("demo/DemoMain.cs")
    assert "SubscriptionStatus.Active" in content, (
        "demo/DemoMain.cs must guard Unsubscribe with 'SubscriptionStatus.Active' check (AC: 1)"
    )


def test_demo_main_cs_logs_identity_from_connection_opened_event() -> None:
    content = _read("demo/DemoMain.cs")
    assert "e.Identity" in content, (
        "demo/DemoMain.cs must log 'e.Identity' from ConnectionOpenedEvent for session identity output (AC: 1)"
    )


def test_demo_main_cs_logs_change_type_from_row_changed_event() -> None:
    content = _read("demo/DemoMain.cs")
    assert "e.ChangeType" in content, (
        "demo/DemoMain.cs must log 'e.ChangeType' from RowChangedEvent for row change type output (AC: 1)"
    )


def test_demo_main_cs_logs_error_message_from_subscription_failed_event() -> None:
    content = _read("demo/DemoMain.cs")
    assert "e.ErrorMessage" in content, (
        "demo/DemoMain.cs must log 'e.ErrorMessage' from SubscriptionFailedEvent for error output (AC: 1)"
    )


# ---------------------------------------------------------------------------
# Task 3.3: demo/README.md content tests (AC: 2, 3)
# ---------------------------------------------------------------------------

def test_demo_readme_has_auth_section() -> None:
    content = _read("demo/README.md")
    assert "## Auth" in content, (
        "demo/README.md must contain an '## Auth' section documenting the auth path (AC: 2)"
    )


def test_demo_readme_documents_token_store() -> None:
    content = _read("demo/README.md")
    assert "TokenStore" in content, (
        "demo/README.md must document 'TokenStore' for token persistence (AC: 2)"
    )


def test_demo_readme_references_project_settings_token_store() -> None:
    content = _read("demo/README.md")
    assert "ProjectSettingsTokenStore" in content, (
        "demo/README.md must reference 'ProjectSettingsTokenStore' as the built-in helper (AC: 2)"
    )


def test_demo_readme_references_itoken_store_interface() -> None:
    content = _read("demo/README.md")
    assert "ITokenStore" in content, (
        "demo/README.md must reference 'ITokenStore' for external project guidance (AC: 2)"
    )


def test_demo_readme_documents_spacetime_auth_token_project_setting() -> None:
    content = _read("demo/README.md")
    assert "spacetime/auth/token" in content, (
        "demo/README.md must document the 'spacetime/auth/token' ProjectSetting key for reset instructions (AC: 2)"
    )


def test_demo_readme_has_subscription_section() -> None:
    content = _read("demo/README.md")
    assert "## Subscription" in content, (
        "demo/README.md must contain a '## Subscription' section documenting the subscription flow (AC: 2)"
    )


def test_demo_readme_documents_smoke_test_subscription_target() -> None:
    content = _read("demo/README.md")
    assert "smoke_test" in content, (
        "demo/README.md must document 'smoke_test' as the subscription target (AC: 2)"
    )


def test_demo_readme_mentions_subscription_applied_lifecycle_term() -> None:
    content = _read("demo/README.md")
    assert "SubscriptionApplied" in content, (
        "demo/README.md must mention 'SubscriptionApplied' to align lifecycle language with docs (AC: 3)"
    )


def test_demo_readme_mentions_row_changed_lifecycle_term() -> None:
    content = _read("demo/README.md")
    assert "RowChanged" in content, (
        "demo/README.md must mention 'RowChanged' to align lifecycle language with docs (AC: 3)"
    )


def test_demo_readme_references_runtime_boundaries_md() -> None:
    content = _read("demo/README.md")
    assert "docs/runtime-boundaries.md" in content, (
        "demo/README.md must reference 'docs/runtime-boundaries.md' as the canonical lifecycle reference (AC: 3)"
    )


def test_demo_readme_documents_pascal_case_cache_read_name() -> None:
    content = _read("demo/README.md")
    assert 'GetRows("SmokeTest")' in content, (
        'demo/README.md must document that cache reads use the generated PascalCase table name via GetRows("SmokeTest") (AC: 3)'
    )


def test_demo_readme_lists_connected_before_identity_in_message_sequence() -> None:
    content = _read("demo/README.md")
    connected_index = content.index("[Demo] Connection state: CONNECTED — active session established")
    identity_index = content.index("[Demo] Session identity: (new — token will be stored)")
    assert connected_index < identity_index, (
        "demo/README.md must document the reviewed runtime order where the CONNECTED line appears before the identity line (AC: 3)"
    )


# ---------------------------------------------------------------------------
# Task 3.4: Regression guards — all Story 5.1 deliverables must remain intact
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


def test_demo_generated_smoke_test_reducers_ping_still_exists() -> None:
    assert (ROOT / "demo" / "generated" / "smoke_test" / "Reducers" / "Ping.g.cs").exists(), (
        "demo/generated/smoke_test/Reducers/Ping.g.cs must still exist — generated binding (regression guard)"
    )


def test_demo_generated_smoke_test_spacetimedbclient_still_exists() -> None:
    assert (ROOT / "demo" / "generated" / "smoke_test" / "SpacetimeDBClient.g.cs").exists(), (
        "demo/generated/smoke_test/SpacetimeDBClient.g.cs must still exist — generated binding (regression guard)"
    )


def test_demo_generated_smoke_test_tables_smoke_test_still_exists() -> None:
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


# ---------------------------------------------------------------------------
# Additional coverage: Story 5.2 implementation details not covered above
# ---------------------------------------------------------------------------

def test_demo_main_cs_imports_system_linq() -> None:
    content = _read("demo/DemoMain.cs")
    assert "using System.Linq;" in content, (
        "demo/DemoMain.cs must import 'System.Linq' to support .ToList() on GetRows result (AC: 1)"
    )


def test_demo_main_cs_subscribe_query_uses_full_sql_string() -> None:
    content = _read("demo/DemoMain.cs")
    assert '"SELECT * FROM smoke_test"' in content, (
        'demo/DemoMain.cs must use exact SQL string "SELECT * FROM smoke_test" in Subscribe call (AC: 1)'
    )


def test_demo_main_cs_token_store_guards_settings_null() -> None:
    content = _read("demo/DemoMain.cs")
    assert "_client.Settings != null" in content, (
        "demo/DemoMain.cs must guard TokenStore assignment with '_client.Settings != null' null-check (AC: 1)"
    )


def test_demo_main_cs_identity_handler_checks_null_or_empty() -> None:
    content = _read("demo/DemoMain.cs")
    assert "string.IsNullOrEmpty(e.Identity)" in content, (
        "demo/DemoMain.cs must use 'string.IsNullOrEmpty(e.Identity)' to detect a new anonymous session (AC: 1)"
    )


def test_demo_main_cs_nulls_handle_after_unsubscribe() -> None:
    content = _read("demo/DemoMain.cs")
    assert "_subscriptionHandle = null" in content, (
        "demo/DemoMain.cs must set '_subscriptionHandle = null' after Unsubscribe in _ExitTree (AC: 1)"
    )


def test_demo_main_cs_resubscribes_after_a_closed_or_failed_handle() -> None:
    content = _read("demo/DemoMain.cs")
    assert "_subscriptionHandle.Status != SubscriptionStatus.Active" in content, (
        "demo/DemoMain.cs must resubscribe when the previous handle is no longer Active so reconnect and failure paths can recover (AC: 1)"
    )


def test_demo_main_cs_clears_handle_for_failed_subscription_event() -> None:
    content = _read("demo/DemoMain.cs")
    assert "_subscriptionHandle == e.Handle" in content, (
        "demo/DemoMain.cs must clear its tracked handle when the current subscription fails so the demo can recover on the next connect (AC: 1)"
    )


def test_demo_main_cs_materializes_rows_with_to_list() -> None:
    content = _read("demo/DemoMain.cs")
    assert ".ToList()" in content, (
        "demo/DemoMain.cs must call '.ToList()' to materialize the GetRows IEnumerable for row count (AC: 1)"
    )


def test_demo_main_cs_xml_doc_references_story_52() -> None:
    content = _read("demo/DemoMain.cs")
    assert "Story 5.2" in content, (
        "demo/DemoMain.cs must have an XML doc comment referencing 'Story 5.2' per subtask 1.10 (AC: 1)"
    )


def test_demo_main_cs_exit_tree_deregisters_connection_opened() -> None:
    content = _read("demo/DemoMain.cs")
    assert "-= OnConnectionOpened" in content, (
        "demo/DemoMain.cs must deregister OnConnectionOpened handler (-=) to prevent leaks on scene reload (AC: 1)"
    )


def test_demo_main_cs_exit_tree_deregisters_connection_closed() -> None:
    content = _read("demo/DemoMain.cs")
    assert "-= OnConnectionClosed" in content, (
        "demo/DemoMain.cs must deregister OnConnectionClosed handler (-=) to prevent leaks on scene reload (AC: 1)"
    )


def test_demo_main_cs_exit_tree_deregisters_subscription_applied() -> None:
    content = _read("demo/DemoMain.cs")
    assert "-= OnSubscriptionApplied" in content, (
        "demo/DemoMain.cs must deregister OnSubscriptionApplied handler (-=) to prevent leaks on scene reload (AC: 1)"
    )


def test_demo_main_cs_exit_tree_deregisters_subscription_failed() -> None:
    content = _read("demo/DemoMain.cs")
    assert "-= OnSubscriptionFailed" in content, (
        "demo/DemoMain.cs must deregister OnSubscriptionFailed handler (-=) to prevent leaks on scene reload (AC: 1)"
    )


def test_demo_main_cs_exit_tree_deregisters_row_changed() -> None:
    content = _read("demo/DemoMain.cs")
    assert "-= OnRowChanged" in content, (
        "demo/DemoMain.cs must deregister OnRowChanged handler (-=) to prevent leaks on scene reload (AC: 1)"
    )


def test_demo_readme_has_auth_and_session_resume_section() -> None:
    content = _read("demo/README.md")
    assert "## Auth and Session Resume" in content, (
        "demo/README.md must contain exact heading '## Auth and Session Resume' (AC: 2)"
    )


def test_demo_readme_has_subscription_and_live_state_section() -> None:
    content = _read("demo/README.md")
    assert "## Subscription and Live State" in content, (
        "demo/README.md must contain exact heading '## Subscription and Live State' (AC: 2)"
    )


def test_demo_readme_documents_clear_token_async() -> None:
    content = _read("demo/README.md")
    assert "ClearTokenAsync" in content, (
        "demo/README.md must document 'ClearTokenAsync' for programmatic token reset instructions (AC: 2)"
    )


def test_demo_readme_mentions_anonymous_session() -> None:
    content = _read("demo/README.md")
    assert "anonymous" in content, (
        "demo/README.md must mention 'anonymous' session to document default unauthenticated behavior (AC: 2)"
    )


def test_demo_readme_shows_new_token_placeholder() -> None:
    content = _read("demo/README.md")
    assert "(new — token will be stored)" in content, (
        "demo/README.md must document the '(new — token will be stored)' placeholder shown on first-run identity output (AC: 2)"
    )


def test_demo_readme_mentions_authenticated_connected_status_for_restored_sessions() -> None:
    content = _read("demo/README.md")
    assert "authenticated session established" in content, (
        "demo/README.md must document the CONNECTED status text used when a stored token is restored (AC: 3)"
    )
