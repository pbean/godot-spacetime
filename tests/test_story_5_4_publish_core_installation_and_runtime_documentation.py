"""
Story 5.4: Publish Core Installation and Runtime Documentation
Static file analysis tests — no Godot runtime, no pytest fixtures.
"""

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


def _section(content: str, heading: str) -> str:
    marker = f"## {heading}\n\n"
    start = content.find(marker)
    assert start != -1, f"Expected to find section heading {marker.strip()!r}"
    start += len(marker)

    next_heading = content.find("\n## ", start)
    if next_heading == -1:
        return content[start:].strip()

    return content[start:next_heading].strip()


# ---------------------------------------------------------------------------
# 5.1 Existence tests — all six core docs must be present
# ---------------------------------------------------------------------------

def test_docs_install_md_exists():
    assert (ROOT / "docs/install.md").exists(), "docs/install.md must exist"


def test_docs_quickstart_md_exists():
    assert (ROOT / "docs/quickstart.md").exists(), "docs/quickstart.md must exist"


def test_docs_codegen_md_exists():
    assert (ROOT / "docs/codegen.md").exists(), "docs/codegen.md must exist"


def test_docs_connection_md_exists():
    assert (ROOT / "docs/connection.md").exists(), "docs/connection.md must exist"


def test_docs_runtime_boundaries_md_exists():
    assert (ROOT / "docs/runtime-boundaries.md").exists(), "docs/runtime-boundaries.md must exist"


def test_docs_compatibility_matrix_md_exists():
    assert (ROOT / "docs/compatibility-matrix.md").exists(), "docs/compatibility-matrix.md must exist"


# ---------------------------------------------------------------------------
# 5.2 docs/install.md content tests (AC: 2, 3)
# ---------------------------------------------------------------------------

def test_install_md_contains_godot_version():
    content = _read("docs/install.md")
    assert "4.6.2" in content, "docs/install.md must state Godot version target 4.6.2 (AC2)"


def test_install_md_contains_dotnet_version():
    content = _read("docs/install.md")
    assert "8.0" in content, "docs/install.md must state .NET version target 8.0 (AC2)"


def test_install_md_contains_spacetimedb_version():
    content = _read("docs/install.md")
    assert "2.1" in content, "docs/install.md must state SpacetimeDB version target 2.1 (AC2)"


def test_install_md_references_demo_readme():
    content = _read("docs/install.md")
    assert "demo/README.md" in content, "docs/install.md must reference demo/README.md (AC3)"


def test_install_md_references_runtime_boundaries():
    content = _read("docs/install.md")
    assert "runtime-boundaries.md" in content, "docs/install.md must reference runtime-boundaries.md (AC1)"


def test_install_md_see_also_entries_match_story_contract():
    content = _read("docs/install.md")
    see_also = _section(content, "See Also")
    _assert_in_order(
        see_also,
        (
            "- `docs/connection.md` for connection lifecycle states, signals, and editor status labels.",
            "- `docs/quickstart.md` for the step-by-step first-setup workflow from install through first connection.",
            "- `demo/README.md` for the canonical end-to-end sample covering install, code generation, connection, auth, subscriptions, and reducer interaction.",
            "- `docs/runtime-boundaries.md` for the full runtime API reference covering connection, auth, subscriptions, cache, reducers, and the complete public SDK concept vocabulary.",
        ),
    )


# ---------------------------------------------------------------------------
# 5.3 docs/quickstart.md content tests (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_quickstart_md_contains_godot_version():
    content = _read("docs/quickstart.md")
    assert "4.6.2" in content, "docs/quickstart.md must state Godot version target 4.6.2 (AC2)"


def test_quickstart_md_contains_dotnet_version():
    content = _read("docs/quickstart.md")
    assert "8.0" in content, "docs/quickstart.md must state .NET version target 8.0 (AC2)"


def test_quickstart_md_contains_spacetimedb_version():
    content = _read("docs/quickstart.md")
    assert "2.1" in content, "docs/quickstart.md must state SpacetimeDB version target 2.1 (AC2)"


def test_quickstart_md_references_demo_readme():
    content = _read("docs/quickstart.md")
    assert "demo/README.md" in content, "docs/quickstart.md must reference demo/README.md (AC3)"


def test_quickstart_md_references_runtime_boundaries():
    content = _read("docs/quickstart.md")
    assert "runtime-boundaries.md" in content, "docs/quickstart.md must reference runtime-boundaries.md (AC1)"


def test_quickstart_md_references_demo_main_cs():
    content = _read("docs/quickstart.md")
    assert "demo/DemoMain.cs" in content, "docs/quickstart.md must reference demo/DemoMain.cs for C# pattern (AC1)"


def test_quickstart_md_step_7_csharp_note_follows_gdscript_example():
    content = _read("docs/quickstart.md")
    step = content[
        content.index("### Step 7 — Connect and Observe Lifecycle")
        : content.index("## Failure Recovery")
    ]
    _assert_in_order(
        step,
        (
            'func _on_state_changed(status: ConnectionStatus) -> void:',
            '    print("Connection state: ", status.Description)',
            "For the C# equivalent, see `demo/DemoMain.cs` — the demo project uses C# and mirrors this step.",
            "`SpacetimeClient` must already be registered as an autoload",
        ),
    )


def test_quickstart_md_see_also_entries_match_story_contract():
    content = _read("docs/quickstart.md")
    see_also = _section(content, "See Also")
    _assert_in_order(
        see_also,
        (
            "docs/install.md\n— Installation prerequisites, bootstrap steps, and foundation validation details.",
            "docs/codegen.md\n— Code generation, schema concepts, and module locations.",
            "docs/connection.md\n— Connection lifecycle states, signals, and editor status labels.",
            "docs/runtime-boundaries.md\n— Full runtime API reference covering connection, auth, subscriptions, cache, reducers, and the complete signal catalog.",
            "demo/README.md\n— The canonical end-to-end sample. Mirrors these quickstart steps and extends them through auth, session resume, subscription, and reducer interaction.",
        ),
    )


# ---------------------------------------------------------------------------
# 5.4 docs/connection.md content tests (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_connection_md_has_see_also_section():
    content = _read("docs/connection.md")
    assert "See Also" in content, "docs/connection.md must have a See Also section"


def test_connection_md_references_runtime_boundaries():
    content = _read("docs/connection.md")
    assert "runtime-boundaries.md" in content, "docs/connection.md must reference runtime-boundaries.md (AC1)"


def test_connection_md_references_demo_readme():
    content = _read("docs/connection.md")
    assert "demo/README.md" in content, "docs/connection.md must reference demo/README.md (AC3)"


def test_connection_md_see_also_entries_match_story_contract():
    content = _read("docs/connection.md")
    see_also = _section(content, "See Also")
    _assert_in_order(
        see_also,
        (
            "- `docs/runtime-boundaries.md` — Complete signal catalog, authentication, subscriptions, cache, reducers, and the full public SDK concept vocabulary.",
            "- `demo/README.md` — The canonical end-to-end sample demonstrating the full connection lifecycle from setup through reducer interaction.",
            "- `docs/quickstart.md` — Step-by-step first-setup guide that exercises connection lifecycle as part of the full onboarding flow.",
        ),
    )


# ---------------------------------------------------------------------------
# 5.5 docs/runtime-boundaries.md content tests (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_md_references_demo_readme():
    content = _read("docs/runtime-boundaries.md")
    assert "demo/README.md" in content, "docs/runtime-boundaries.md must reference demo/README.md (AC3)"


def test_runtime_boundaries_md_references_demo_main_cs():
    content = _read("docs/runtime-boundaries.md")
    assert "demo/DemoMain.cs" in content, "docs/runtime-boundaries.md must reference demo/DemoMain.cs"


def test_runtime_boundaries_md_intro_demo_reference_stays_in_intro():
    content = _read("docs/runtime-boundaries.md")
    _assert_in_order(
        content,
        (
            "This document defines the public concept vocabulary for the GodotSpacetime SDK.",
            "The canonical end-to-end implementation of these concepts is the sample project at `demo/README.md` and `demo/DemoMain.cs`.",
            "## Concept Vocabulary",
        ),
    )


def test_runtime_boundaries_md_contains_connection_state():
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionState" in content, "docs/runtime-boundaries.md must document ConnectionState (connection lifecycle API)"


def test_runtime_boundaries_md_contains_itoken_store():
    content = _read("docs/runtime-boundaries.md")
    assert "ITokenStore" in content, "docs/runtime-boundaries.md must document ITokenStore (auth API)"


def test_runtime_boundaries_md_contains_subscription_handle():
    content = _read("docs/runtime-boundaries.md")
    assert "SubscriptionHandle" in content, "docs/runtime-boundaries.md must document SubscriptionHandle (subscription API)"


def test_runtime_boundaries_md_contains_reducer_call_result():
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallResult" in content, "docs/runtime-boundaries.md must document ReducerCallResult (reducer success API)"


def test_runtime_boundaries_md_contains_reducer_call_error():
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallError" in content, "docs/runtime-boundaries.md must document ReducerCallError (reducer failure API)"


def test_runtime_boundaries_md_contains_spacetime_client():
    content = _read("docs/runtime-boundaries.md")
    assert "SpacetimeClient" in content, "docs/runtime-boundaries.md must document SpacetimeClient (entry point)"


def test_runtime_boundaries_md_contains_get_rows():
    content = _read("docs/runtime-boundaries.md")
    assert "GetRows" in content, "docs/runtime-boundaries.md must document GetRows (cache API)"


def test_runtime_boundaries_md_contains_row_changed():
    content = _read("docs/runtime-boundaries.md")
    assert "RowChanged" in content, "docs/runtime-boundaries.md must document RowChanged (row change signal)"


def test_runtime_boundaries_md_contains_invoke_reducer():
    content = _read("docs/runtime-boundaries.md")
    assert "InvokeReducer" in content, "docs/runtime-boundaries.md must document InvokeReducer (reducer invocation)"


def test_runtime_boundaries_md_contains_reducer_failure_category():
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerFailureCategory" in content, "docs/runtime-boundaries.md must document ReducerFailureCategory (failure branching)"


# ---------------------------------------------------------------------------
# 5.6 docs/compatibility-matrix.md content tests (AC: 2)
# ---------------------------------------------------------------------------

def test_compatibility_matrix_md_contains_godot_version():
    content = _read("docs/compatibility-matrix.md")
    assert "4.6.2" in content, "docs/compatibility-matrix.md must state Godot version target 4.6.2 (AC2)"


def test_compatibility_matrix_md_contains_dotnet_version():
    content = _read("docs/compatibility-matrix.md")
    assert "8.0" in content, "docs/compatibility-matrix.md must state .NET version target 8.0 (AC2)"


def test_compatibility_matrix_md_contains_spacetimedb_version():
    content = _read("docs/compatibility-matrix.md")
    assert "2.1" in content, "docs/compatibility-matrix.md must state SpacetimeDB version target 2.1 (AC2)"


# ---------------------------------------------------------------------------
# 5.7 Regression guards — all prior story deliverables must remain intact
# ---------------------------------------------------------------------------

def test_install_md_has_supported_foundation_baseline():
    content = _read("docs/install.md")
    assert "Supported Foundation Baseline" in content, \
        "docs/install.md must still contain 'Supported Foundation Baseline' section (Story 1.1 regression)"


def test_install_md_has_validate_foundation_script():
    content = _read("docs/install.md")
    assert "validate-foundation.py" in content, \
        "docs/install.md must still reference validate-foundation.py (Story 1.2 regression)"


def test_quickstart_md_has_quickstart_heading():
    content = _read("docs/quickstart.md")
    assert "Quickstart" in content, \
        "docs/quickstart.md must still contain 'Quickstart' heading (Story 1.10 regression)"


def test_quickstart_md_has_spacetime_settings():
    content = _read("docs/quickstart.md")
    assert "SpacetimeSettings" in content, \
        "docs/quickstart.md must still reference SpacetimeSettings (Story 1.9 regression)"


def test_quickstart_md_has_spacetime_client():
    content = _read("docs/quickstart.md")
    assert "SpacetimeClient" in content, \
        "docs/quickstart.md must still reference SpacetimeClient (Story 1.9 regression)"


def test_codegen_md_has_generate_smoke_test_sh():
    content = _read("docs/codegen.md")
    assert "generate-smoke-test.sh" in content, \
        "docs/codegen.md must still reference generate-smoke-test.sh (Story 1.6 regression)"


def test_codegen_md_has_demo_generated_smoke_test():
    content = _read("docs/codegen.md")
    assert "demo/generated/smoke_test" in content, \
        "docs/codegen.md must still reference demo/generated/smoke_test output path (Story 1.6 regression)"


def test_connection_md_has_connection_state():
    content = _read("docs/connection.md")
    assert "ConnectionState" in content, \
        "docs/connection.md must still contain ConnectionState state table (Story 1.9 regression)"


def test_runtime_boundaries_md_has_reducer_call_failed():
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallFailed" in content, \
        "docs/runtime-boundaries.md must still contain ReducerCallFailed (Story 4.4 regression)"


def test_runtime_boundaries_md_has_itoken_store_regression():
    content = _read("docs/runtime-boundaries.md")
    assert "ITokenStore" in content, \
        "docs/runtime-boundaries.md must still contain ITokenStore (Story 2.1 regression)"


def test_runtime_boundaries_md_has_subscription_applied():
    content = _read("docs/runtime-boundaries.md")
    assert "SubscriptionApplied" in content, \
        "docs/runtime-boundaries.md must still contain SubscriptionApplied (Story 3.1 regression)"


def test_runtime_boundaries_md_has_row_changed_regression():
    content = _read("docs/runtime-boundaries.md")
    assert "RowChanged" in content, \
        "docs/runtime-boundaries.md must still contain RowChanged (Story 3.3 regression)"


def test_demo_readme_md_exists():
    assert (ROOT / "demo/README.md").exists(), \
        "demo/README.md must exist (Story 5.1 sample regression)"


def test_demo_main_cs_exists():
    assert (ROOT / "demo/DemoMain.cs").exists(), \
        "demo/DemoMain.cs must exist (Story 5.1 C# script regression)"


def test_demo_main_cs_has_reducer_call_succeeded():
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallSucceeded" in content, \
        "demo/DemoMain.cs must still contain ReducerCallSucceeded (Story 5.3 reducer wiring regression)"


def test_spacetime_client_cs_exists():
    assert (ROOT / "addons/godot_spacetime/src/Public/SpacetimeClient.cs").exists(), \
        "addons/godot_spacetime/src/Public/SpacetimeClient.cs must exist (SDK public boundary regression)"


# ---------------------------------------------------------------------------
# Gap coverage — story-specified insertions not yet verified
# ---------------------------------------------------------------------------

def test_connection_md_references_quickstart():
    content = _read("docs/connection.md")
    assert "docs/quickstart.md" in content, \
        "docs/connection.md must reference docs/quickstart.md in See Also (Task 3.1)"


def test_quickstart_md_has_failure_recovery_section():
    content = _read("docs/quickstart.md")
    assert "Failure Recovery" in content, \
        "docs/quickstart.md must contain a Failure Recovery section (AC1 — recovery path for adopters)"


def test_install_md_has_bootstrap_steps_section():
    content = _read("docs/install.md")
    assert "Bootstrap Steps" in content, \
        "docs/install.md must contain a Bootstrap Steps section (AC1 — installation path)"


# ---------------------------------------------------------------------------
# Gap coverage — runtime-boundaries.md additional API surfaces (AC1)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_md_contains_subscription_failed():
    content = _read("docs/runtime-boundaries.md")
    assert "SubscriptionFailed" in content, \
        "docs/runtime-boundaries.md must document SubscriptionFailed signal (AC1 — subscription failure path)"


def test_runtime_boundaries_md_contains_connection_closed():
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionClosed" in content, \
        "docs/runtime-boundaries.md must document ConnectionClosed signal (AC1 — connection close boundary)"


def test_runtime_boundaries_md_contains_connection_auth_state():
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionAuthState" in content, \
        "docs/runtime-boundaries.md must document ConnectionAuthState (AC1 — auth state enum)"


def test_runtime_boundaries_md_contains_log_category():
    content = _read("docs/runtime-boundaries.md")
    assert "LogCategory" in content, \
        "docs/runtime-boundaries.md must document LogCategory (AC1 — logging subsystem)"


def test_runtime_boundaries_md_contains_spacetime_settings():
    content = _read("docs/runtime-boundaries.md")
    assert "SpacetimeSettings" in content, \
        "docs/runtime-boundaries.md must document SpacetimeSettings (AC1 — configuration resource)"


def test_runtime_boundaries_md_contains_row_changed_event():
    content = _read("docs/runtime-boundaries.md")
    assert "RowChangedEvent" in content, \
        "docs/runtime-boundaries.md must document RowChangedEvent payload type (AC1 — row change data surface)"


def test_runtime_boundaries_md_contains_reducer_call_succeeded():
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallSucceeded" in content, \
        "docs/runtime-boundaries.md must document ReducerCallSucceeded signal (AC1 — complete signal catalog)"
