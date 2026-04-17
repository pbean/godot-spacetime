"""
Story 8.2 — Support Multiple RowReceivers and Custom Filtering in Scenes
Static contract tests verifying:
- RowReceiver custom icon exists and is valid SVG
- GodotSpacetimePlugin loads the icon (not null placeholder)
- docs/runtime-boundaries.md describes multiple-receiver isolation and no-subscription behavior
- RowReceiver.cs uses multicast subscribe/unsubscribe pattern
- Story 8.1 regression anchors remain intact
"""

import os
import re
from functools import cache

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@cache
def read_file(rel_path: str) -> str:
    with open(os.path.join(REPO_ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


@cache
def read_row_receiver_docs_section() -> str:
    content = read_file("docs/runtime-boundaries.md")
    heading = "### RowReceiver — Scene-Tree Row Event Integration"
    assert heading in content, "runtime-boundaries.md must contain the RowReceiver section heading"

    _, remainder = content.split(heading, 1)
    next_heading_index = remainder.find("\n### ")
    if next_heading_index == -1:
        return remainder

    return remainder[:next_heading_index]


def get_import_section(rel_path: str, section_name: str) -> str:
    content = read_file(rel_path)
    marker = f"[{section_name}]"
    assert marker in content, f"{rel_path} must contain the [{section_name}] section"

    _, remainder = content.split(marker, 1)
    next_section_index = remainder.find("\n[")
    if next_section_index == -1:
        return remainder.strip()

    return remainder[:next_section_index].strip()


# ---------------------------------------------------------------------------
# AC 4 — Custom icon
# ---------------------------------------------------------------------------

def test_row_receiver_icon_svg_exists():
    path = os.path.join(REPO_ROOT, "addons/godot_spacetime/assets/row_receiver_icon.svg")
    assert os.path.isfile(path), "row_receiver_icon.svg must exist in assets/"


def test_row_receiver_icon_svg_is_valid_svg():
    content = read_file("addons/godot_spacetime/assets/row_receiver_icon.svg")
    assert "<svg" in content, "row_receiver_icon.svg must contain '<svg' (valid SVG)"


def test_row_receiver_icon_svg_uses_story_viewbox():
    content = read_file("addons/godot_spacetime/assets/row_receiver_icon.svg")
    assert 'viewBox="0 0 16 16"' in content, \
        "row_receiver_icon.svg must keep the story's 16×16 viewBox for editor legibility"


@pytest.mark.parametrize("color", ["#7dd3fc", "#38bdf8"])
def test_row_receiver_icon_svg_uses_story_palette(color: str):
    content = read_file("addons/godot_spacetime/assets/row_receiver_icon.svg").lower()
    assert color in content, \
        f"row_receiver_icon.svg must use the story's sky-blue palette color {color}"


def test_row_receiver_icon_import_exists():
    path = os.path.join(REPO_ROOT, "addons/godot_spacetime/assets/row_receiver_icon.svg.import")
    assert os.path.isfile(path), "row_receiver_icon.svg.import companion file must exist"


def test_row_receiver_icon_import_has_godot_uid():
    content = read_file("addons/godot_spacetime/assets/row_receiver_icon.svg.import")
    assert re.search(r'^uid="uid://[a-z0-9]{13}"$', content, re.MULTILINE), \
        "row_receiver_icon.svg.import must contain a fresh Godot uid:// identifier"


def test_row_receiver_icon_import_targets_row_receiver_asset():
    content = read_file("addons/godot_spacetime/assets/row_receiver_icon.svg.import")
    assert 'source_file="res://addons/godot_spacetime/assets/row_receiver_icon.svg"' in content, \
        "row_receiver_icon.svg.import must point at the row_receiver_icon.svg source asset"

    path_match = re.search(
        r'^path="(?P<path>res://\.godot/imported/row_receiver_icon\.svg-[a-z0-9]+\.ctex)"$',
        content,
        re.MULTILINE,
    )
    dest_match = re.search(
        r'^dest_files=\["(?P<path>res://\.godot/imported/row_receiver_icon\.svg-[a-z0-9]+\.ctex)"\]$',
        content,
        re.MULTILINE,
    )
    assert path_match, "row_receiver_icon.svg.import must declare a .godot/imported .ctex path"
    assert dest_match, "row_receiver_icon.svg.import must declare a matching dest_files .ctex entry"
    assert path_match.group("path") == dest_match.group("path"), \
        "row_receiver_icon.svg.import path and dest_files entries must use the same .ctex target"


def test_row_receiver_icon_import_reuses_icon_template_params():
    row_receiver_params = get_import_section(
        "addons/godot_spacetime/assets/row_receiver_icon.svg.import",
        "params",
    )
    icon_template_params = get_import_section(
        "addons/godot_spacetime/assets/icon.svg.import",
        "params",
    )
    assert row_receiver_params == icon_template_params, \
        "row_receiver_icon.svg.import must keep the same [params] block as icon.svg.import"


# ---------------------------------------------------------------------------
# AC 4 — Plugin loads the icon
# ---------------------------------------------------------------------------

def test_plugin_loads_row_receiver_icon():
    content = read_file("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert 'GD.Load<Texture2D>("res://addons/godot_spacetime/assets/row_receiver_icon.svg")' in content, \
        "GodotSpacetimePlugin.cs must load row_receiver_icon.svg for RowReceiver"


def test_plugin_does_not_have_null_icon_placeholder():
    content = read_file("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert 'null   // Story 8.2' not in content, \
        "GodotSpacetimePlugin.cs null icon placeholder must be replaced"


# ---------------------------------------------------------------------------
# AC 1, 2, 3 — docs/runtime-boundaries.md
# ---------------------------------------------------------------------------

def test_runtime_boundaries_describes_multiple_receiver_independence():
    content = read_row_receiver_docs_section()
    independence_markers = [
        "independently",
        "multicast",
        "do not affect",
        "independently subscribe",
    ]
    assert any(marker in content for marker in independence_markers), \
        "docs/runtime-boundaries.md must describe multiple-receiver independence"


def test_runtime_boundaries_describes_clientpath_for_multi_client_scenes():
    content = read_row_receiver_docs_section()
    assert "ClientPath" in content, \
        "docs/runtime-boundaries.md RowReceiver section must describe ClientPath for Story 10.1 multi-client scenes"


def test_runtime_boundaries_describes_no_subscription_silent_behavior():
    content = read_row_receiver_docs_section()
    assert "no active subscription" in content.lower(), \
        "docs/runtime-boundaries.md must describe no-active-subscription silent behavior"


# ---------------------------------------------------------------------------
# AC 1, 2 — RowReceiver.cs multicast pattern
# ---------------------------------------------------------------------------

def test_row_receiver_uses_multicast_subscribe():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "RowChanged +=" in content, \
        "RowReceiver.cs must use 'RowChanged +=' for multicast subscribe"


def test_row_receiver_uses_multicast_unsubscribe():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "RowChanged -=" in content, \
        "RowReceiver.cs must use 'RowChanged -=' for multicast unsubscribe (independent of other subscribers)"


# ---------------------------------------------------------------------------
# Story 8.1 regression anchors
# ---------------------------------------------------------------------------

def test_8_1_row_receiver_cs_exists():
    path = os.path.join(REPO_ROOT, "addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert os.path.isfile(path), "RowReceiver.cs must still exist (Story 8.1 regression)"


def test_8_1_row_receiver_has_tool_attribute():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "[Tool]" in content, "RowReceiver.cs must still have [Tool] attribute (Story 8.1 regression)"


def test_8_1_row_receiver_partial_class_node():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "partial class RowReceiver : Node" in content, \
        "RowReceiver.cs must still declare 'partial class RowReceiver : Node' (Story 8.1 regression)"


def test_8_1_row_receiver_has_event_handlers():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "RowInsertedEventHandler" in content, \
        "RowReceiver.cs must still contain RowInsertedEventHandler (Story 8.1 regression)"
    assert "RowUpdatedEventHandler" in content, \
        "RowReceiver.cs must still contain RowUpdatedEventHandler (Story 8.1 regression)"
    assert "RowDeletedEventHandler" in content, \
        "RowReceiver.cs must still contain RowDeletedEventHandler (Story 8.1 regression)"


def test_8_1_row_receiver_does_not_reference_internal_adapter():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "SpacetimeSdkRowCallbackAdapter" not in content, \
        "RowReceiver.cs must NOT reference SpacetimeSdkRowCallbackAdapter (Story 8.1 regression)"
    assert "IRowChangeEventSink" not in content, \
        "RowReceiver.cs must NOT reference IRowChangeEventSink (Story 8.1 regression)"


def test_8_1_plugin_has_add_custom_type_for_row_receiver():
    content = read_file("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "AddCustomType" in content, \
        "GodotSpacetimePlugin.cs must still contain AddCustomType (Story 8.1 regression)"
    assert 'RemoveCustomType("RowReceiver")' in content, \
        "GodotSpacetimePlugin.cs must still contain RemoveCustomType with 'RowReceiver' (Story 8.1 regression)"
    assert '"RowReceiver"' in content, \
        "GodotSpacetimePlugin.cs must still reference \"RowReceiver\" in AddCustomType (Story 8.1 regression)"


def test_8_1_runtime_boundaries_contains_row_receiver():
    content = read_row_receiver_docs_section()
    assert "RowReceiver" in content, \
        "docs/runtime-boundaries.md must still contain RowReceiver (Story 8.1 regression)"


def test_8_1_runtime_boundaries_no_parallel_dispatch_text():
    content = read_row_receiver_docs_section()
    assert "NOT a parallel dispatch path" in content or "not a parallel dispatch" in content.lower(), \
        "docs/runtime-boundaries.md must still contain 'NOT a parallel dispatch path' text (Story 8.1 regression)"


# ---------------------------------------------------------------------------
# AC 2 — Custom filtering: TableName filter and signal emissions
# ---------------------------------------------------------------------------

def test_row_receiver_filters_by_table_name_in_on_row_changed():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "e.TableName != TableName" in content, \
        "RowReceiver.cs must filter events with 'e.TableName != TableName' in OnRowChanged"


def test_row_receiver_emits_row_inserted_signal():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "EmitSignal(SignalName.RowInserted" in content, \
        "RowReceiver.cs must emit RowInserted signal via EmitSignal(SignalName.RowInserted, ...)"


def test_row_receiver_emits_row_updated_signal():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "EmitSignal(SignalName.RowUpdated" in content, \
        "RowReceiver.cs must emit RowUpdated signal via EmitSignal(SignalName.RowUpdated, ...)"


def test_row_receiver_emits_row_deleted_signal():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "EmitSignal(SignalName.RowDeleted" in content, \
        "RowReceiver.cs must emit RowDeleted signal via EmitSignal(SignalName.RowDeleted, ...)"


def test_row_receiver_has_export_table_name_property():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "[Export] public string TableName" in content, \
        "RowReceiver.cs must declare '[Export] public string TableName' property"


# ---------------------------------------------------------------------------
# AC 2 — Inspector dropdown: _GetPropertyList + PropertyHint.Enum
# ---------------------------------------------------------------------------

def test_row_receiver_has_get_property_list():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "_GetPropertyList()" in content, \
        "RowReceiver.cs must override _GetPropertyList() for the Inspector dropdown"


def test_row_receiver_get_property_list_uses_enum_hint():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "PropertyHint.Enum" in content, \
        "RowReceiver.cs must use PropertyHint.Enum in _GetPropertyList() for the TableName dropdown"


def test_row_receiver_should_skip_assembly_filters_system_assemblies():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "GeneratedBindingTypeResolver" in content and "ShouldSkipAssembly" not in content, \
        "Story 10.1 must replace RowReceiver's public assembly-skip scan with the internal generated-binding resolver"


def test_row_receiver_discover_table_names_finds_remote_tables_type():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "RemoteTables" in content, \
        "RowReceiver.cs must look for 'RemoteTables' type during table name discovery"


# ---------------------------------------------------------------------------
# AC 1 — Multiple-receiver isolation: editor guard and cleanup
# ---------------------------------------------------------------------------

def test_row_receiver_editor_hint_guard_in_ready():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "Engine.IsEditorHint()" in content, \
        "RowReceiver.cs must guard _Ready() with Engine.IsEditorHint() to prevent wiring in the editor"


def test_row_receiver_editor_hint_guard_in_exit_tree():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    # IsEditorHint is checked multiple times; confirm _ExitTree also returns early
    assert content.count("Engine.IsEditorHint()") >= 2, \
        "RowReceiver.cs must guard both _Ready() and _ExitTree() with Engine.IsEditorHint() (at least 2 occurrences)"


def test_row_receiver_is_instance_valid_guard_on_exit():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "IsInstanceValid(_client)" in content, \
        "RowReceiver.cs must use IsInstanceValid(_client) in _ExitTree to safely disconnect without affecting other receivers"


def test_row_receiver_nulls_client_reference_on_exit():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "_client = null" in content, \
        "RowReceiver.cs must set '_client = null' in _ExitTree to release the reference after disconnect"


def test_row_receiver_pushwarning_on_missing_client():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    # G6 (spec-g6-pluggable-logger-interface) rerouted the direct GD.PushWarning through the
    # SpacetimeLog facade. The default GodotConsoleLogSink still lands warning-level messages
    # on GD.PushWarning, preserving the Story 8.2 graceful-degrade intent.
    assert "SpacetimeLog.Warning" in content, (
        "RowReceiver.cs must log via SpacetimeLog.Warning (warning-level — not error-level) "
        "when SpacetimeClient autoload is not found (post-G6 routing)"
    )


def test_row_receiver_uses_root_autoload_path():
    content = read_file("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")
    assert "/root/SpacetimeClient" in content, \
        "RowReceiver.cs must look up the autoload at '/root/SpacetimeClient'"


# ---------------------------------------------------------------------------
# AC 1, 2 — docs/runtime-boundaries.md: inspector dropdown + editor guard + signals
# ---------------------------------------------------------------------------

def test_runtime_boundaries_documents_inspector_dropdown():
    content = read_row_receiver_docs_section()
    assert "dropdown" in content.lower() or "PROPERTY_HINT_ENUM" in content, \
        "docs/runtime-boundaries.md must describe the Inspector dropdown for the TableName property"


def test_runtime_boundaries_documents_editor_hint_guard():
    content = read_row_receiver_docs_section()
    assert "IsEditorHint" in content or "editor hint" in content.lower(), \
        "docs/runtime-boundaries.md must document the Engine.IsEditorHint() guard on RowReceiver"


def test_runtime_boundaries_documents_exit_tree_cleanup():
    content = read_row_receiver_docs_section()
    assert "_ExitTree" in content or "removed from the scene tree" in content or "disconnect" in content.lower(), \
        "docs/runtime-boundaries.md must describe RowReceiver cleanup on scene-tree removal"


def test_runtime_boundaries_documents_push_warning_on_missing_client():
    content = read_row_receiver_docs_section()
    assert "PushWarning" in content or "warning" in content.lower(), \
        "docs/runtime-boundaries.md must document that a warning (not an error) is issued when the autoload is missing"


def test_runtime_boundaries_documents_row_inserted_signal():
    content = read_row_receiver_docs_section()
    assert "row_inserted" in content or "RowInserted" in content, \
        "docs/runtime-boundaries.md must document the row_inserted signal emitted by RowReceiver"


def test_runtime_boundaries_documents_row_updated_signal():
    content = read_row_receiver_docs_section()
    assert "row_updated" in content or "RowUpdated" in content, \
        "docs/runtime-boundaries.md must document the row_updated signal emitted by RowReceiver"


def test_runtime_boundaries_documents_row_deleted_signal():
    content = read_row_receiver_docs_section()
    assert "row_deleted" in content or "RowDeleted" in content, \
        "docs/runtime-boundaries.md must document the row_deleted signal emitted by RowReceiver"
