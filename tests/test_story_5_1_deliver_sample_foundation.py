"""
Story 5.1: Deliver a Sample Foundation for Install, Codegen, and First Connection
Automated contract tests for all story deliverables.

Covers:
- Task 1: demo/README.md existence and content (AC: 1, 2, 3)
- Task 2: demo/DemoMain.cs existence and content (AC: 1)
- Task 3: demo/DemoMain.tscn existence and content (AC: 1)
- Task 4: demo/autoload/DemoBootstrap.cs existence and content (AC: 1, 3)
- Task 5: demo/scenes/connection_smoke.tscn existence (AC: 1)
- Project wiring: project.godot autoload registration for DemoBootstrap (AC: 1, 3)
- Task 6: Regression guards — prior epic deliverables still intact
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Task 6.1: Existence tests — all five deliverables must be present
# ---------------------------------------------------------------------------

def test_demo_readme_exists() -> None:
    assert (ROOT / "demo" / "README.md").exists(), (
        "demo/README.md must exist — sample setup guide deliverable (Task 1)"
    )


def test_demo_main_cs_exists() -> None:
    assert (ROOT / "demo" / "DemoMain.cs").exists(), (
        "demo/DemoMain.cs must exist — connection demo script deliverable (Task 2)"
    )


def test_demo_main_tscn_exists() -> None:
    assert (ROOT / "demo" / "DemoMain.tscn").exists(), (
        "demo/DemoMain.tscn must exist — main demo scene deliverable (Task 3)"
    )


def test_demo_autoload_bootstrap_cs_exists() -> None:
    assert (ROOT / "demo" / "autoload" / "DemoBootstrap.cs").exists(), (
        "demo/autoload/DemoBootstrap.cs must exist — demo autoload deliverable (Task 4)"
    )


def test_demo_scenes_connection_smoke_tscn_exists() -> None:
    assert (ROOT / "demo" / "scenes" / "connection_smoke.tscn").exists(), (
        "demo/scenes/connection_smoke.tscn must exist — connection smoke scene deliverable (Task 5)"
    )


def test_project_godot_registers_demo_bootstrap_autoload() -> None:
    content = _read("project.godot")
    assert 'DemoBootstrap="*res://demo/autoload/DemoBootstrap.cs"' in content, (
        "project.godot must register DemoBootstrap as an enabled autoload so the demo bootstrap path actually runs (AC: 1, 3)"
    )


# ---------------------------------------------------------------------------
# Task 6.2: demo/README.md content tests (AC: 2, 3)
# ---------------------------------------------------------------------------

def test_demo_readme_has_prerequisites_section() -> None:
    content = _read("demo/README.md")
    assert "## Prerequisites" in content, (
        "demo/README.md must contain '## Prerequisites' mirroring quickstart.md (AC: 2)"
    )


def test_demo_readme_has_godot_version_target() -> None:
    content = _read("demo/README.md")
    assert "4.6.2" in content, (
        "demo/README.md must contain version string '4.6.2' for Godot version target (AC: 2)"
    )


def test_demo_readme_has_dotnet_version_target() -> None:
    content = _read("demo/README.md")
    assert "8.0+" in content, (
        "demo/README.md must contain '8.0+' for .NET version target (AC: 2)"
    )


def test_demo_readme_has_spacetimedb_cli_version_target() -> None:
    content = _read("demo/README.md")
    assert "2.1+" in content, (
        "demo/README.md must contain '2.1+' for SpacetimeDB CLI version target (AC: 2)"
    )


def test_demo_readme_references_generate_smoke_test_sh() -> None:
    content = _read("demo/README.md")
    assert "generate-smoke-test.sh" in content, (
        "demo/README.md must reference 'generate-smoke-test.sh' for the codegen step (AC: 2)"
    )


def test_demo_readme_has_reset_section() -> None:
    content = _read("demo/README.md")
    assert "## Reset to Clean State" in content, (
        "demo/README.md must contain '## Reset to Clean State' or equivalent reset section (AC: 3)"
    )


def test_demo_readme_references_quickstart_md() -> None:
    content = _read("demo/README.md")
    assert "docs/quickstart.md" in content, (
        "demo/README.md must reference 'docs/quickstart.md' as the canonical doc reference (AC: 2)"
    )


def test_demo_readme_has_see_also_section() -> None:
    content = _read("demo/README.md")
    assert "## See Also" in content, (
        "demo/README.md must contain a '## See Also' section"
    )


def test_demo_readme_references_spacetime_settings() -> None:
    content = _read("demo/README.md")
    assert "SpacetimeSettings" in content, (
        "demo/README.md must reference 'SpacetimeSettings' for the configuration setup step (AC: 1)"
    )


def test_demo_readme_mentions_connected_success_state() -> None:
    content = _read("demo/README.md")
    assert "CONNECTED" in content, (
        "demo/README.md must mention 'CONNECTED' as the expected connection success state (AC: 1)"
    )


def test_demo_readme_mentions_candidate_addon_artifact_flow() -> None:
    content = _read("demo/README.md")
    assert "candidate addon artifact" in content, (
        "demo/README.md must explain how to validate the sample against a candidate addon artifact as well as the repository source (AC: 1, 2)"
    )


def test_demo_readme_mentions_demo_bootstrap_autoload() -> None:
    content = _read("demo/README.md")
    assert "DemoBootstrap" in content, (
        "demo/README.md must document the demo bootstrap autoload so external developers can verify the intended sample node structure (AC: 1, 3)"
    )


def test_demo_readme_reset_section_clears_nested_generated_bindings() -> None:
    content = _read("demo/README.md")
    assert "find demo/generated/smoke_test -type f -name '*.cs' -delete" in content, (
        "demo/README.md reset instructions must remove generated C# files from nested output folders as well as the root so the sample truly resets to a clean state (AC: 3)"
    )


def test_demo_readme_mentions_bootstrap_ready_output() -> None:
    content = _read("demo/README.md")
    assert "[Demo] Bootstrap ready" in content, (
        "demo/README.md must describe the DemoBootstrap output so the sample bootstrap path is observable to external developers (AC: 1, 3)"
    )


# ---------------------------------------------------------------------------
# Task 6.3: demo/DemoMain.cs content tests (AC: 1)
# ---------------------------------------------------------------------------

def test_demo_main_cs_has_godotspacetime_demo_namespace() -> None:
    content = _read("demo/DemoMain.cs")
    assert "GodotSpacetime.Demo" in content, (
        "demo/DemoMain.cs must use 'GodotSpacetime.Demo' namespace (AC: 1)"
    )


def test_demo_main_cs_has_demo_main_class() -> None:
    content = _read("demo/DemoMain.cs")
    assert "DemoMain" in content, (
        "demo/DemoMain.cs must declare the 'DemoMain' class (AC: 1)"
    )


def test_demo_main_cs_references_spacetime_client() -> None:
    content = _read("demo/DemoMain.cs")
    assert "SpacetimeClient" in content, (
        "demo/DemoMain.cs must reference 'SpacetimeClient' to connect to the SDK autoload (AC: 1)"
    )


def test_demo_main_cs_handles_connection_state_change() -> None:
    content = _read("demo/DemoMain.cs")
    assert "Connection" in content, (
        "demo/DemoMain.cs must handle connection state changes (ConnectionStateChanged) (AC: 1)"
    )


def test_demo_main_cs_calls_connect() -> None:
    content = _read("demo/DemoMain.cs")
    assert "Connect(" in content, (
        "demo/DemoMain.cs must call Connect() to initiate the connection lifecycle (AC: 1)"
    )


def test_demo_main_cs_uses_gd_print() -> None:
    content = _read("demo/DemoMain.cs")
    assert "GD.Print" in content, (
        "demo/DemoMain.cs must use GD.Print to output connection state for developer visibility (AC: 1)"
    )


def test_demo_main_cs_implements_exit_tree_cleanup() -> None:
    content = _read("demo/DemoMain.cs")
    assert "_ExitTree" in content, (
        "demo/DemoMain.cs must clean up its event subscription on _ExitTree so repeated demo scene loads do not accumulate handlers"
    )


def test_demo_main_cs_unhooks_connection_state_changed_event() -> None:
    content = _read("demo/DemoMain.cs")
    assert "-= OnConnectionStateChanged" in content, (
        "demo/DemoMain.cs must unhook ConnectionStateChanged when the scene leaves the tree to avoid duplicate logging on rerun"
    )


# ---------------------------------------------------------------------------
# Task 6.4: demo/DemoMain.tscn content tests (AC: 1)
# ---------------------------------------------------------------------------

def test_demo_main_tscn_references_demo_main_cs_script() -> None:
    content = _read("demo/DemoMain.tscn")
    assert "DemoMain.cs" in content, (
        "demo/DemoMain.tscn must reference 'DemoMain.cs' as its script (AC: 1)"
    )


def test_demo_main_tscn_has_demo_main_root_node() -> None:
    content = _read("demo/DemoMain.tscn")
    assert "DemoMain" in content, (
        "demo/DemoMain.tscn must declare 'DemoMain' as the root node name (AC: 1)"
    )


# ---------------------------------------------------------------------------
# Task 6.5: demo/autoload/DemoBootstrap.cs content tests (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_demo_bootstrap_cs_has_godotspacetime_demo_namespace() -> None:
    content = _read("demo/autoload/DemoBootstrap.cs")
    assert "GodotSpacetime.Demo" in content, (
        "demo/autoload/DemoBootstrap.cs must use 'GodotSpacetime.Demo' namespace (AC: 1)"
    )


def test_demo_bootstrap_cs_has_demo_bootstrap_class() -> None:
    content = _read("demo/autoload/DemoBootstrap.cs")
    assert "DemoBootstrap" in content, (
        "demo/autoload/DemoBootstrap.cs must declare the 'DemoBootstrap' class (AC: 1)"
    )


def test_demo_bootstrap_cs_has_ready_method() -> None:
    content = _read("demo/autoload/DemoBootstrap.cs")
    assert "_Ready" in content, (
        "demo/autoload/DemoBootstrap.cs must implement '_Ready' for bootstrap on scene ready (AC: 1, 3)"
    )


# ---------------------------------------------------------------------------
# Task 6.6: Regression guards — prior epic deliverables must remain intact
# ---------------------------------------------------------------------------

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


def test_docs_connection_md_still_exists() -> None:
    assert (ROOT / "docs" / "connection.md").exists(), (
        "docs/connection.md must still exist — referenced in demo/README.md See Also section (regression guard)"
    )


def test_docs_compatibility_matrix_md_still_exists() -> None:
    assert (ROOT / "docs" / "compatibility-matrix.md").exists(), (
        "docs/compatibility-matrix.md must still exist — referenced in demo/README.md See Also section (regression guard)"
    )


# ---------------------------------------------------------------------------
# Additional content tests — connection_smoke.tscn (AC: 1)
# ---------------------------------------------------------------------------

def test_connection_smoke_tscn_has_connection_smoke_root_node() -> None:
    content = _read("demo/scenes/connection_smoke.tscn")
    assert "ConnectionSmoke" in content, (
        "demo/scenes/connection_smoke.tscn must declare 'ConnectionSmoke' as the root node name (AC: 1)"
    )


# ---------------------------------------------------------------------------
# Additional content tests — DemoMain.cs (AC: 1)
# ---------------------------------------------------------------------------

def test_demo_main_cs_has_xml_doc_comment() -> None:
    content = _read("demo/DemoMain.cs")
    assert "<summary>" in content, (
        "demo/DemoMain.cs must have an XML doc <summary> comment on the class (Task 2.5)"
    )


def test_demo_main_cs_declares_partial_class() -> None:
    content = _read("demo/DemoMain.cs")
    assert "partial class" in content, (
        "demo/DemoMain.cs must declare 'public partial class DemoMain : Node' (Task 2.1)"
    )


def test_demo_main_cs_hooks_connection_state_changed_event() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ConnectionStateChanged" in content, (
        "demo/DemoMain.cs must hook the 'ConnectionStateChanged' event (Task 2.2)"
    )


# ---------------------------------------------------------------------------
# Additional content tests — DemoBootstrap.cs (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_demo_bootstrap_cs_calls_gd_print() -> None:
    content = _read("demo/autoload/DemoBootstrap.cs")
    assert "GD.Print" in content, (
        "demo/autoload/DemoBootstrap.cs must call GD.Print to confirm bootstrap (Task 4.2)"
    )


# ---------------------------------------------------------------------------
# Additional README content tests (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_demo_readme_references_validate_foundation_script() -> None:
    content = _read("demo/README.md")
    assert "validate-foundation.py" in content, (
        "demo/README.md must reference 'validate-foundation.py' for the foundation validation step (AC: 2)"
    )


def test_demo_readme_mentions_spacetime_codegen_panel() -> None:
    content = _read("demo/README.md")
    assert "Spacetime Codegen" in content, (
        "demo/README.md must reference the 'Spacetime Codegen' panel by name (AC: 1, 2)"
    )


def test_demo_readme_mentions_spacetime_status_panel() -> None:
    content = _read("demo/README.md")
    assert "Spacetime Status" in content, (
        "demo/README.md must reference the 'Spacetime Status' panel by name (AC: 1)"
    )


def test_demo_readme_has_ok_bindings_present_status() -> None:
    content = _read("demo/README.md")
    assert "OK — bindings present" in content, (
        "demo/README.md must contain 'OK — bindings present' as the expected codegen success state (AC: 1, 2)"
    )


def test_demo_readme_shows_demo_connection_state_output() -> None:
    content = _read("demo/README.md")
    assert "[Demo] Connection state:" in content, (
        "demo/README.md must describe the '[Demo] Connection state:' output to orient developers (AC: 1)"
    )


def test_docs_install_mentions_candidate_addon_artifact_flow() -> None:
    content = _read("docs/install.md")
    assert "candidate addon artifact" in content, (
        "docs/install.md must explain the supported candidate addon artifact bootstrap path so demo/README.md can stay aligned with the canonical install guide (AC: 2)"
    )


def test_docs_quickstart_mentions_candidate_addon_artifact_flow() -> None:
    content = _read("docs/quickstart.md")
    assert "candidate addon artifact" in content, (
        "docs/quickstart.md must explain the supported candidate addon artifact quickstart path so demo/README.md stays aligned with the canonical setup guide (AC: 2)"
    )
