"""
Story 1.8: Detect Binding and Schema Compatibility Problems Early
Automated contract tests for all story deliverables.

Covers:
- CompatibilityPanel.cs existence and explicit text labels
- CompatibilityPanel.tscn existence
- GodotSpacetimePlugin.cs panel registration
- support-baseline.json new path and line_check entries
- docs/compatibility-matrix.md Binding Compatibility Check section
- Regression guards from Stories 1.6 and 1.7
"""

from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


def _load_validate_foundation_module():
    script_path = ROOT / "scripts/compatibility/validate-foundation.py"
    spec = importlib.util.spec_from_file_location("validate_foundation", script_path)
    assert spec is not None and spec.loader is not None, (
        f"Unable to load validate-foundation module from {script_path}"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Compatibility panel existence tests (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_compatibility_panel_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs").is_file(), (
        "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs is missing"
    )


def test_compatibility_panel_tscn_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn").is_file(), (
        "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn is missing"
    )


# ---------------------------------------------------------------------------
# Panel explicit text label tests (AC: 1, 2, 3, 4)
# ---------------------------------------------------------------------------

def test_panel_has_compat_ok_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "OK — bindings match declared baseline" in content, (
        "CompatibilityPanel.cs must contain 'OK — bindings match declared baseline'"
    )


def test_panel_has_compat_incompatible_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "INCOMPATIBLE — bindings do not match declared baseline" in content, (
        "CompatibilityPanel.cs must contain 'INCOMPATIBLE — bindings do not match declared baseline'"
    )


def test_panel_has_compat_missing_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "MISSING — run codegen to generate bindings" in content, (
        "CompatibilityPanel.cs must contain 'MISSING — run codegen to generate bindings'"
    )


def test_panel_has_compat_not_configured_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "NOT CONFIGURED" in content, (
        "CompatibilityPanel.cs must contain 'NOT CONFIGURED'"
    )


def test_panel_has_compat_recovery_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "Run: bash scripts/codegen/generate-smoke-test.sh" in content, (
        "CompatibilityPanel.cs must contain 'Run: bash scripts/codegen/generate-smoke-test.sh'"
    )


# ---------------------------------------------------------------------------
# Panel version extraction tests (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_panel_reads_cli_version_comment() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "spacetimedb cli version" in content, (
        "CompatibilityPanel.cs must read the CLI version comment (contains 'spacetimedb cli version')"
    )


def test_panel_reads_support_versions_from_json() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "support_versions" in content, (
        "CompatibilityPanel.cs must read 'support_versions' from baseline JSON"
    )


def test_panel_reads_client_sdk_version() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "spacetimedb_client_sdk" in content, (
        "CompatibilityPanel.cs must read 'spacetimedb_client_sdk' from baseline JSON"
    )


def test_panel_has_version_satisfies_baseline_method() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "VersionSatisfiesBaseline" in content, (
        "CompatibilityPanel.cs must implement the 'VersionSatisfiesBaseline' version comparison method"
    )


# ---------------------------------------------------------------------------
# Panel layout tests (AC: 4)
# ---------------------------------------------------------------------------

def test_panel_has_compatibility_baseline_header() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert '"Compatibility Baseline"' in content, (
        "CompatibilityPanel.cs must contain the header label '\"Compatibility Baseline\"'"
    )


def test_panel_has_binding_cli_version_field_label() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert '"Binding CLI version:"' in content, (
        "CompatibilityPanel.cs must contain the field label '\"Binding CLI version:\"'"
    )


def test_panel_has_compatibility_status_field_label() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert '"Compatibility status:"' in content, (
        "CompatibilityPanel.cs must contain the field label '\"Compatibility status:\"'"
    )


def test_panel_has_autowrap_for_narrow_layouts() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "AutowrapMode" in content and "WordSmart" in content, (
        "CompatibilityPanel.cs must enable AutowrapMode.WordSmart for narrow panel support"
    )


def test_panel_has_focus_mode_all_for_keyboard_navigation() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "FocusModeEnum.All" in content, (
        "CompatibilityPanel.cs must set FocusModeEnum.All on labels for keyboard navigation"
    )


def test_panel_has_custom_minimum_size() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "CustomMinimumSize" in content, (
        "CompatibilityPanel.cs must set CustomMinimumSize for narrow panel support"
    )


# ---------------------------------------------------------------------------
# Plugin registration tests (AC: 4)
# ---------------------------------------------------------------------------

def test_plugin_registers_both_panels() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert content.count("AddControlToBottomPanel") == 2, (
        "GodotSpacetimePlugin.cs must call AddControlToBottomPanel twice (codegen + compat panels)"
    )


def test_plugin_has_spacetime_compat_tab_label() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert '"Spacetime Compat"' in content, (
        "GodotSpacetimePlugin.cs must register compat panel with tab label 'Spacetime Compat'"
    )


def test_plugin_references_compatibility_panel_type() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "CompatibilityPanel" in content, (
        "GodotSpacetimePlugin.cs must reference the CompatibilityPanel type"
    )


# ---------------------------------------------------------------------------
# Support-baseline tests (AC: 2, 4)
# ---------------------------------------------------------------------------

def test_support_baseline_has_editor_compatibility_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "addons/godot_spacetime/src/Editor/Compatibility" in content, (
        "support-baseline.json must include 'addons/godot_spacetime/src/Editor/Compatibility' in required_paths"
    )


def test_support_baseline_has_compatibility_panel_cs_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "CompatibilityPanel.cs" in content, (
        "support-baseline.json must include 'CompatibilityPanel.cs' in required_paths"
    )


def test_support_baseline_has_binding_compatibility_check_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "Binding Compatibility Check" in content, (
        "support-baseline.json must include a line_check entry for 'Binding Compatibility Check'"
    )


# ---------------------------------------------------------------------------
# Documentation tests (AC: 3)
# ---------------------------------------------------------------------------

def test_compatibility_matrix_has_binding_compatibility_check_section() -> None:
    lines = _lines("docs/compatibility-matrix.md")
    assert "## Binding Compatibility Check" in lines, (
        "docs/compatibility-matrix.md must contain '## Binding Compatibility Check' as an exact stripped line"
    )


def test_compatibility_matrix_references_cli_version_comment_format() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "spacetimedb cli version" in content, (
        "docs/compatibility-matrix.md must explain the CLI version comment format"
    )


def test_compatibility_matrix_describes_generated_header_block_instead_of_second_line() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "after the generated-file warning banner" in content, (
        "docs/compatibility-matrix.md must describe the real location of the CLI version comment"
    )


def test_compatibility_matrix_mentions_stale_binding_validation() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "stale bindings fail before runtime use" in content, (
        "docs/compatibility-matrix.md must explain that stale bindings are rejected during validation"
    )


# ---------------------------------------------------------------------------
# Regression guards — Story 1.7 deliverables still present
# ---------------------------------------------------------------------------

def test_codegen_validation_panel_cs_still_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs").is_file(), (
        "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs is missing (regression from Story 1.7)"
    )


def test_codegen_validation_panel_tscn_still_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn").is_file(), (
        "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn is missing (regression from Story 1.7)"
    )


def test_plugin_still_registers_codegen_panel() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert '"Spacetime Codegen"' in content, (
        "GodotSpacetimePlugin.cs must still register codegen panel with tab label 'Spacetime Codegen' (regression from Story 1.7)"
    )


def test_codegen_md_still_has_schema_concepts_section() -> None:
    content = _read("docs/codegen.md")
    assert "Generated Schema Concepts" in content, (
        "docs/codegen.md must still contain 'Generated Schema Concepts' (regression from Story 1.7)"
    )


# ---------------------------------------------------------------------------
# Regression guards — Story 1.6 deliverables still present
# ---------------------------------------------------------------------------

def test_demo_generated_smoke_test_dir_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test").is_dir(), (
        "demo/generated/smoke_test/ directory is missing (regression from Story 1.6)"
    )


def test_demo_generated_smoke_test_has_cs_files() -> None:
    cs_files = list((ROOT / "demo/generated/smoke_test").rglob("*.cs"))
    assert len(cs_files) > 0, (
        "demo/generated/smoke_test/ must contain at least one .cs file (regression from Story 1.6)"
    )


def test_codegen_script_still_exists() -> None:
    assert (ROOT / "scripts/codegen/generate-smoke-test.sh").is_file(), (
        "scripts/codegen/generate-smoke-test.sh is missing (regression from Story 1.6)"
    )


# ---------------------------------------------------------------------------
# CompatibilityPanel.cs structural requirements (#if TOOLS, [Tool], namespace)
# ---------------------------------------------------------------------------

def test_panel_has_tools_conditional_compile_guard() -> None:
    """Panel must be wrapped in #if TOOLS to prevent compile errors in non-tool builds."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "#if TOOLS" in content, (
        "CompatibilityPanel.cs must be wrapped in '#if TOOLS' guard"
    )
    assert "#endif" in content, (
        "CompatibilityPanel.cs must close its '#if TOOLS' guard with '#endif'"
    )


def test_panel_has_tool_attribute() -> None:
    """Panel must have [Tool] so it evaluates in editor context."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "[Tool]" in content, (
        "CompatibilityPanel.cs must have the [Tool] attribute"
    )


def test_panel_has_correct_namespace() -> None:
    """Panel must use the GodotSpacetime.Editor.Compatibility namespace."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "GodotSpacetime.Editor.Compatibility" in content, (
        "CompatibilityPanel.cs must declare namespace GodotSpacetime.Editor.Compatibility"
    )


def test_panel_extends_vbox_container() -> None:
    """Panel must extend VBoxContainer for vertical stacking in narrow panels."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "VBoxContainer" in content, (
        "CompatibilityPanel.cs must extend VBoxContainer"
    )


def test_panel_uses_project_settings_globalize_path() -> None:
    """Panel must use ProjectSettings.GlobalizePath for cross-platform path resolution."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "ProjectSettings.GlobalizePath" in content, (
        "CompatibilityPanel.cs must use ProjectSettings.GlobalizePath to resolve project-relative paths"
    )


def test_panel_recovery_label_initially_hidden() -> None:
    """Recovery label must start hidden so it only appears on INCOMPATIBLE/MISSING states (AC: 2)."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "Visible = false" in content, (
        "CompatibilityPanel.cs must set _recoveryLabel.Visible = false in BuildLayout (hidden by default)"
    )


def test_panel_has_cli_version_prefix_constant() -> None:
    """Panel must define the CliVersionPrefix constant used to locate the version comment."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "CliVersionPrefix" in content, (
        "CompatibilityPanel.cs must define a 'CliVersionPrefix' constant for the CLI version comment prefix"
    )


# ---------------------------------------------------------------------------
# Panel layout field labels not yet tested
# ---------------------------------------------------------------------------

def test_panel_has_godot_target_field_label() -> None:
    """Panel layout must include a 'Godot target:' field label."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert '"Godot target:"' in content, (
        "CompatibilityPanel.cs must contain the field label '\"Godot target:\"'"
    )


def test_panel_has_spacetimedb_cli_field_label() -> None:
    """Panel layout must include a 'SpacetimeDB CLI:' field label."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert '"SpacetimeDB CLI:"' in content, (
        "CompatibilityPanel.cs must contain the field label '\"SpacetimeDB CLI:\"'"
    )


def test_panel_has_client_sdk_field_label() -> None:
    """Panel layout must include a 'ClientSDK:' field label."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert '"ClientSDK:"' in content, (
        "CompatibilityPanel.cs must contain the field label '\"ClientSDK:\"'"
    )


def test_panel_defaults_binding_version_to_version_not_found() -> None:
    """Fallback states must not leave the binding version label blank."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert 'BindingVersionNotFound = "version not found"' in content, (
        "CompatibilityPanel.cs must define a fallback 'version not found' binding version label"
    )
    assert "ResetDisplayValues" in content, (
        "CompatibilityPanel.cs must reset its display values before computing status"
    )


def test_panel_checks_for_stale_module_sources() -> None:
    """Compatibility panel must reject generated bindings older than the module source."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "File.GetLastWriteTimeUtc" in content, (
        "CompatibilityPanel.cs must compare module-source and generated-binding write times"
    )
    assert "EnumerateFiles(modulePath, \"*.rs\"" in content, (
        "CompatibilityPanel.cs must inspect Rust module source files when checking for stale bindings"
    )
    assert "is newer than generated bindings" in content, (
        "CompatibilityPanel.cs must report stale bindings with an exact failed-check message"
    )


def test_panel_reports_version_baseline_failure_with_exact_reason() -> None:
    """Version incompatibilities must include the specific failing baseline comparison."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs")
    assert "does not satisfy declared baseline" in content, (
        "CompatibilityPanel.cs must report the extracted CLI version and declared baseline in incompatible states"
    )


# ---------------------------------------------------------------------------
# CompatibilityPanel.tscn content validation
# ---------------------------------------------------------------------------

def test_compat_tscn_uses_format_3() -> None:
    """Scene file must use Godot 4 format=3."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn")
    assert "format=3" in content, (
        "CompatibilityPanel.tscn must use 'format=3' (Godot 4 scene format)"
    )


def test_compat_tscn_root_is_vbox_container() -> None:
    """Scene root must be VBoxContainer to match the class hierarchy."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn")
    assert 'type="VBoxContainer"' in content, (
        'CompatibilityPanel.tscn root node must be type="VBoxContainer"'
    )


def test_compat_tscn_attaches_correct_script() -> None:
    """Scene must reference the CompatibilityPanel.cs script."""
    content = _read("addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn")
    assert "CompatibilityPanel.cs" in content, (
        "CompatibilityPanel.tscn must attach CompatibilityPanel.cs as the node script"
    )


# ---------------------------------------------------------------------------
# Plugin structural completeness for story 1.8
# ---------------------------------------------------------------------------

def test_plugin_has_compat_panel_scene_path_constant() -> None:
    """Plugin must declare CompatPanelScenePath constant with the correct scene path."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "CompatPanelScenePath" in content, (
        "GodotSpacetimePlugin.cs must declare a 'CompatPanelScenePath' constant"
    )
    assert "CompatibilityPanel.tscn" in content, (
        "GodotSpacetimePlugin.cs CompatPanelScenePath must reference 'CompatibilityPanel.tscn'"
    )


def test_plugin_removes_both_panels_in_exit_tree() -> None:
    """Plugin must call RemoveControlFromBottomPanel twice — once per registered panel (AC: 4)."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert content.count("RemoveControlFromBottomPanel") == 2, (
        "GodotSpacetimePlugin.cs must call RemoveControlFromBottomPanel twice (codegen + compat cleanup)"
    )


def test_plugin_has_using_compatibility_namespace() -> None:
    """Plugin must import the Editor.Compatibility namespace to use CompatibilityPanel."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "GodotSpacetime.Editor.Compatibility" in content, (
        "GodotSpacetimePlugin.cs must import 'GodotSpacetime.Editor.Compatibility' namespace"
    )


def test_plugin_loads_compat_panel_scene_resource() -> None:
    """Plugin must load and instantiate the compat panel scene using GD.Load<PackedScene>."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "GD.Load<PackedScene>" in content, (
        "GodotSpacetimePlugin.cs must use GD.Load<PackedScene> to load the compat panel scene"
    )
    assert "Instantiate()" in content, (
        "GodotSpacetimePlugin.cs must call Instantiate() to create the compat panel from the scene"
    )


# ---------------------------------------------------------------------------
# Support-baseline tscn path entry
# ---------------------------------------------------------------------------

def test_support_baseline_has_compatibility_panel_tscn_path() -> None:
    """support-baseline.json must register CompatibilityPanel.tscn as a required file."""
    content = _read("scripts/compatibility/support-baseline.json")
    assert "CompatibilityPanel.tscn" in content, (
        "support-baseline.json must include 'CompatibilityPanel.tscn' in required_paths"
    )


# ---------------------------------------------------------------------------
# Validation workflow compatibility checks
# ---------------------------------------------------------------------------

def test_validate_foundation_version_satisfies_baseline_helper() -> None:
    module = _load_validate_foundation_module()
    assert module.version_satisfies_baseline("2.1.0", "2.1+")
    assert module.version_satisfies_baseline("3.0.0", "2.1+")
    assert not module.version_satisfies_baseline("2.0.5", "2.1+")


def test_validate_foundation_rejects_incompatible_cli_version(tmp_path: Path) -> None:
    module = _load_validate_foundation_module()
    module_root = tmp_path / "spacetime/modules/smoke_test/src"
    module_root.mkdir(parents=True)
    (tmp_path / "spacetime/modules/smoke_test/Cargo.toml").write_text(
        "[package]\nname = \"smoke_test\"\n",
        encoding="utf-8",
    )
    (module_root / "lib.rs").write_text("// module\n", encoding="utf-8")

    generated = tmp_path / "demo/generated/smoke_test/SpacetimeDBClient.g.cs"
    generated.parent.mkdir(parents=True)
    generated.write_text(
        f"{module.CLI_VERSION_PREFIX}2.0.5 (commit deadbeef).\n",
        encoding="utf-8",
    )

    errors = module.collect_binding_compatibility_errors(tmp_path, {"spacetimedb": "2.1+"})
    assert any("does not satisfy declared baseline 2.1+" in error for error in errors), (
        "validate-foundation.py must reject generated bindings whose CLI version is below the declared baseline"
    )


def test_validate_foundation_rejects_stale_bindings(tmp_path: Path) -> None:
    module = _load_validate_foundation_module()
    module_root = tmp_path / "spacetime/modules/smoke_test/src"
    module_root.mkdir(parents=True)
    cargo = tmp_path / "spacetime/modules/smoke_test/Cargo.toml"
    cargo.write_text("[package]\nname = \"smoke_test\"\n", encoding="utf-8")
    source = module_root / "lib.rs"
    source.write_text("// module\n", encoding="utf-8")

    generated = tmp_path / "demo/generated/smoke_test/SpacetimeDBClient.g.cs"
    generated.parent.mkdir(parents=True)
    generated.write_text(
        f"{module.CLI_VERSION_PREFIX}2.1.0 (commit deadbeef).\n",
        encoding="utf-8",
    )

    older = time.time() - 60
    newer = time.time() - 5
    os.utime(generated, (older, older))
    os.utime(source, (newer, newer))
    os.utime(cargo, (newer - 1, newer - 1))

    errors = module.collect_binding_compatibility_errors(tmp_path, {"spacetimedb": "2.1+"})
    assert any("generated bindings are stale because" in error for error in errors), (
        "validate-foundation.py must reject generated bindings older than the relevant module source"
    )


# ---------------------------------------------------------------------------
# Documentation completeness
# ---------------------------------------------------------------------------

def test_compatibility_matrix_has_regeneration_command() -> None:
    """compatibility-matrix.md must include the regeneration command for INCOMPATIBLE state (AC: 3)."""
    content = _read("docs/compatibility-matrix.md")
    assert "bash scripts/codegen/generate-smoke-test.sh" in content, (
        "docs/compatibility-matrix.md must include 'bash scripts/codegen/generate-smoke-test.sh' regeneration command"
    )
