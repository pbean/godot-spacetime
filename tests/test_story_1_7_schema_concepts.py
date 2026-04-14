"""
Story 1.7: Explain Generated Schema Concepts and Validate Code Generation State
Automated contract tests for all story deliverables.

Covers:
- Schema concepts section in docs/codegen.md
- CodegenValidationPanel.cs existence and explicit text labels
- CodegenValidationPanel.tscn existence
- GodotSpacetimePlugin.cs panel registration
- support-baseline.json new path and line_check entries
- Regression guards from Story 1.6
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# Schema concepts documentation (AC: 1)
# ---------------------------------------------------------------------------

def test_codegen_md_has_schema_concepts_section() -> None:
    lines = _lines("docs/codegen.md")
    assert "## Generated Schema Concepts" in lines, (
        "docs/codegen.md must contain '## Generated Schema Concepts' as an exact stripped line"
    )


def test_codegen_md_references_smoke_test_row_type() -> None:
    content = _read("docs/codegen.md")
    assert "SmokeTest" in content, (
        "docs/codegen.md must reference 'SmokeTest' (table row type)"
    )


def test_codegen_md_references_smoke_test_handle() -> None:
    content = _read("docs/codegen.md")
    assert "SmokeTestHandle" in content, (
        "docs/codegen.md must reference 'SmokeTestHandle' (table handle)"
    )


def test_codegen_md_references_ping_reducer() -> None:
    content = _read("docs/codegen.md")
    assert "Ping" in content, (
        "docs/codegen.md must reference 'Ping' (reducer proxy)"
    )


def test_codegen_md_references_spacetimedb_client() -> None:
    content = _read("docs/codegen.md")
    assert "SpacetimeDBClient.g.cs" in content, (
        "docs/codegen.md must reference 'SpacetimeDBClient.g.cs' (module binding registry)"
    )


# ---------------------------------------------------------------------------
# Editor panel existence tests (AC: 2)
# ---------------------------------------------------------------------------

def test_codegen_validation_panel_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs").is_file(), (
        "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs is missing"
    )


def test_codegen_validation_panel_tscn_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn").is_file(), (
        "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn is missing"
    )


# ---------------------------------------------------------------------------
# Panel explicit text label tests (AC: 3)
# ---------------------------------------------------------------------------

def test_panel_has_status_ok_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "OK — bindings present" in content, (
        "CodegenValidationPanel.cs must contain the literal 'OK — bindings present'"
    )


def test_panel_has_status_missing_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "MISSING — run codegen to generate" in content, (
        "CodegenValidationPanel.cs must contain the literal 'MISSING — run codegen to generate'"
    )


def test_panel_has_recovery_command_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "Run: bash scripts/codegen/generate-smoke-test.sh" in content, (
        "CodegenValidationPanel.cs must contain the literal 'Run: bash scripts/codegen/generate-smoke-test.sh'"
    )


def test_panel_has_module_source_field_label() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert '"Module source:"' in content, (
        "CodegenValidationPanel.cs must contain the field label '\"Module source:\"'"
    )


def test_panel_has_output_path_field_label() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert '"Output path:"' in content, (
        "CodegenValidationPanel.cs must contain the field label '\"Output path:\"'"
    )


# ---------------------------------------------------------------------------
# Plugin registration tests (AC: 2)
# ---------------------------------------------------------------------------

def test_plugin_registers_panel_with_add_control() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "AddControlToBottomPanel" in content, (
        "GodotSpacetimePlugin.cs must call 'AddControlToBottomPanel' to register the panel"
    )


def test_plugin_removes_panel_with_remove_control() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "RemoveControlFromBottomPanel" in content, (
        "GodotSpacetimePlugin.cs must call 'RemoveControlFromBottomPanel' to clean up the panel"
    )


# ---------------------------------------------------------------------------
# Support-baseline tests (AC: 2, 3)
# ---------------------------------------------------------------------------

def test_support_baseline_has_editor_codegen_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "addons/godot_spacetime/src/Editor/Codegen" in content, (
        "support-baseline.json must include 'addons/godot_spacetime/src/Editor/Codegen' in required_paths"
    )


def test_support_baseline_has_schema_concepts_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "Generated Schema Concepts" in content, (
        "support-baseline.json must include a line_check entry for 'Generated Schema Concepts'"
    )


# ---------------------------------------------------------------------------
# Panel structural correctness (AC: 2, 4)
# ---------------------------------------------------------------------------

def test_panel_has_tools_guard() -> None:
    """Panel must be wrapped in #if TOOLS to prevent compile errors in non-tool builds."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "#if TOOLS" in content, (
        "CodegenValidationPanel.cs must be wrapped in '#if TOOLS' guard"
    )


def test_panel_has_tool_attribute() -> None:
    """Panel must have [Tool] so it evaluates in editor context."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "[Tool]" in content, (
        "CodegenValidationPanel.cs must have the [Tool] attribute"
    )


def test_panel_extends_vbox_container() -> None:
    """Panel must extend VBoxContainer for vertical stacking that works in narrow widths (AC 4)."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "VBoxContainer" in content, (
        "CodegenValidationPanel.cs must extend VBoxContainer"
    )


def test_panel_has_correct_namespace() -> None:
    """Panel must use the GodotSpacetime.Editor.Codegen namespace."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "GodotSpacetime.Editor.Codegen" in content, (
        "CodegenValidationPanel.cs must declare namespace GodotSpacetime.Editor.Codegen"
    )


def test_panel_has_status_not_configured_text() -> None:
    """Panel must cover the NOT CONFIGURED state with explicit text (AC 3)."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "NOT CONFIGURED" in content, (
        "CodegenValidationPanel.cs must contain the literal 'NOT CONFIGURED' status text"
    )


def test_panel_assigns_not_configured_status_when_module_source_is_missing() -> None:
    """Panel must distinguish missing configuration from missing generated bindings (AC 2)."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "SetStatus(StatusNotConfigured" in content, (
        "CodegenValidationPanel.cs must assign StatusNotConfigured when the module source is unavailable"
    )
    assert "Directory.Exists(absoluteModuleSource)" in content, (
        "CodegenValidationPanel.cs must check the module source directory before treating codegen as merely missing"
    )


def test_panel_has_status_field_label() -> None:
    """Panel must show a 'Status:' field label so status text is identifiable (AC 2)."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert '"Status:"' in content, (
        "CodegenValidationPanel.cs must contain the field label '\"Status:\"'"
    )


# ---------------------------------------------------------------------------
# AC 3: Keyboard accessibility — explicit FocusMode on all labels
# ---------------------------------------------------------------------------

def test_panel_has_focus_mode_all_for_keyboard_navigation() -> None:
    """All labels must use FocusModeEnum.All for keyboard-accessible navigation (AC 3)."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "FocusModeEnum.All" in content, (
        "CodegenValidationPanel.cs must set FocusModeEnum.All on labels for keyboard accessibility (AC 3)"
    )


def test_panel_enables_autowrap_for_narrow_layouts() -> None:
    """Labels must wrap instead of relying on truncation in narrow panels (AC 4)."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "AutowrapMode" in content and "WordSmart" in content, (
        "CodegenValidationPanel.cs must enable label autowrap for narrow editor panels (AC 4)"
    )


# ---------------------------------------------------------------------------
# AC 4: Narrow panel width support
# ---------------------------------------------------------------------------

def test_panel_has_custom_minimum_size_for_narrow_panels() -> None:
    """Panel must set CustomMinimumSize with minimum width 200 to function in narrow editor panels (AC 4)."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "CustomMinimumSize" in content, (
        "CodegenValidationPanel.cs must set CustomMinimumSize for narrow panel support (AC 4)"
    )
    assert "200" in content, (
        "CodegenValidationPanel.cs CustomMinimumSize must specify 200 as the minimum width (AC 4)"
    )


# ---------------------------------------------------------------------------
# Plugin lifecycle and structural correctness (AC: 2)
# ---------------------------------------------------------------------------

def test_plugin_queues_free_panel_on_exit() -> None:
    """Plugin must call QueueFree on the panel in _ExitTree to avoid lifecycle crashes."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "QueueFree" in content, (
        "GodotSpacetimePlugin.cs must call QueueFree() on the panel in _ExitTree"
    )


def test_plugin_imports_editor_codegen_namespace() -> None:
    """Plugin must import the Editor.Codegen namespace to use CodegenValidationPanel."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "GodotSpacetime.Editor.Codegen" in content, (
        "GodotSpacetimePlugin.cs must import 'GodotSpacetime.Editor.Codegen' namespace"
    )


def test_plugin_has_tools_guard() -> None:
    """Plugin must be wrapped in #if TOOLS so editor code is excluded from non-tool builds."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "#if TOOLS" in content, (
        "GodotSpacetimePlugin.cs must be wrapped in '#if TOOLS' guard"
    )


def test_plugin_loads_panel_scene_resource() -> None:
    """The shipped .tscn should be the dock surface the plugin mounts."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "CodegenValidationPanel.tscn" in content, (
        "GodotSpacetimePlugin.cs must reference CodegenValidationPanel.tscn when mounting the dock"
    )
    assert "GD.Load<PackedScene>" in content and "Instantiate()" in content, (
        "GodotSpacetimePlugin.cs must load and instantiate the packed scene for the dock surface"
    )


# ---------------------------------------------------------------------------
# Scene file structural validation (AC: 2)
# ---------------------------------------------------------------------------

def test_tscn_uses_format_3() -> None:
    """Scene file must use Godot 4 format=3."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn")
    assert "format=3" in content, (
        "CodegenValidationPanel.tscn must use 'format=3' (Godot 4 scene format)"
    )


def test_tscn_root_is_vbox_container() -> None:
    """Scene root must be VBoxContainer to match the class hierarchy."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn")
    assert 'type="VBoxContainer"' in content, (
        'CodegenValidationPanel.tscn root node must be type="VBoxContainer"'
    )


def test_tscn_attaches_correct_script() -> None:
    """Scene must reference the CodegenValidationPanel.cs script."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn")
    assert "CodegenValidationPanel.cs" in content, (
        "CodegenValidationPanel.tscn must attach CodegenValidationPanel.cs as the node script"
    )


# ---------------------------------------------------------------------------
# Schema concepts docs — additional namespace and type coverage (AC: 1)
# ---------------------------------------------------------------------------

def test_codegen_md_references_spacetimedb_types_namespace() -> None:
    """Schema concepts section must mention the SpacetimeDB.Types namespace (AC 1)."""
    content = _read("docs/codegen.md")
    assert "SpacetimeDB.Types" in content, (
        "docs/codegen.md must reference the 'SpacetimeDB.Types' namespace in the schema concepts section"
    )


def test_codegen_md_references_remote_tables() -> None:
    """Schema concepts section must reference RemoteTables (module binding registry component) (AC 1)."""
    content = _read("docs/codegen.md")
    assert "RemoteTables" in content, (
        "docs/codegen.md must reference 'RemoteTables' (module binding registry component)"
    )


def test_codegen_md_references_remote_reducers() -> None:
    """Schema concepts section must reference RemoteReducers (AC 1)."""
    content = _read("docs/codegen.md")
    assert "RemoteReducers" in content, (
        "docs/codegen.md must reference 'RemoteReducers'"
    )


def test_codegen_md_references_event_context() -> None:
    """Schema concepts section must reference EventContext (AC 1)."""
    content = _read("docs/codegen.md")
    assert "EventContext" in content, (
        "docs/codegen.md must reference 'EventContext'"
    )


# ---------------------------------------------------------------------------
# Support-baseline — individual file/dir entry coverage (AC: 2)
# ---------------------------------------------------------------------------

def test_support_baseline_has_editor_dir_path() -> None:
    """support-baseline.json must register the top-level Editor/ directory."""
    content = _read("scripts/compatibility/support-baseline.json")
    assert '"addons/godot_spacetime/src/Editor"' in content, (
        "support-baseline.json must include the 'addons/godot_spacetime/src/Editor' directory entry"
    )


def test_support_baseline_has_panel_cs_path() -> None:
    """support-baseline.json must register CodegenValidationPanel.cs as a required file."""
    content = _read("scripts/compatibility/support-baseline.json")
    assert "CodegenValidationPanel.cs" in content, (
        "support-baseline.json must include 'CodegenValidationPanel.cs' in required_paths"
    )


def test_support_baseline_has_panel_tscn_path() -> None:
    """support-baseline.json must register CodegenValidationPanel.tscn as a required file."""
    content = _read("scripts/compatibility/support-baseline.json")
    assert "CodegenValidationPanel.tscn" in content, (
        "support-baseline.json must include 'CodegenValidationPanel.tscn' in required_paths"
    )


# ---------------------------------------------------------------------------
# Regression guards (Story 1.6 deliverables still present)
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


def test_codegen_md_still_references_generate_script() -> None:
    content = _read("docs/codegen.md")
    assert "generate-smoke-test.sh" in content, (
        "docs/codegen.md must still reference generate-smoke-test.sh (regression from Story 1.6)"
    )


def test_codegen_md_still_references_demo_generated_output() -> None:
    content = _read("docs/codegen.md")
    assert "demo/generated/smoke_test" in content, (
        "docs/codegen.md must still reference demo/generated/smoke_test (regression from Story 1.6)"
    )


def test_panel_checks_generated_cs_files_recursively() -> None:
    """Generated bindings can live below the output root, so the panel must inspect subdirectories."""
    content = _read("addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs")
    assert "SearchOption.AllDirectories" in content, (
        "CodegenValidationPanel.cs must search recursively for generated .cs files"
    )
