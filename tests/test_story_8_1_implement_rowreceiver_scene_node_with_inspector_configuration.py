"""
Story 8.1: Implement the RowReceiver Scene Node with Inspector Configuration
Static contract tests for the RowReceiver node class, plugin registration,
documentation updates, and no-parallel-dispatch enforcement.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROWRECEIVER_PATH = "addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs"
GENERATED_BINDING_RESOLVER_PATH = "addons/godot_spacetime/src/Internal/Platform/DotNet/GeneratedBindingTypeResolver.cs"
PLUGIN_PATH = "addons/godot_spacetime/GodotSpacetimePlugin.cs"
RUNTIME_BOUNDARIES_PATH = "docs/runtime-boundaries.md"
DEMO_README_PATH = "demo/README.md"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Task 4.2 — RowReceiver.cs structural assertions
# ---------------------------------------------------------------------------

def test_rowreceiver_file_exists() -> None:
    path = ROOT / ROWRECEIVER_PATH
    assert path.exists(), (
        f"RowReceiver.cs must exist at {ROWRECEIVER_PATH} (Task 1.1, AC1)"
    )


def test_rowreceiver_has_tool_attribute() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "[Tool]" in content, (
        "RowReceiver must have the [Tool] attribute so it runs in editor mode "
        "for Inspector dropdown population (Task 1.2, AC2)"
    )


def test_rowreceiver_is_partial_class_extending_node() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "partial class RowReceiver : Node" in content, (
        "RowReceiver must be declared as 'partial class RowReceiver : Node' "
        "to conform to Godot C# partial class requirements (Task 1.1, AC1)"
    )


def test_rowreceiver_has_export_and_tablename_property() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "[Export]" in content, (
        "RowReceiver must have an [Export] attribute for the TableName property (Task 1.3, AC2)"
    )
    assert "TableName" in content, (
        "RowReceiver must define a TableName property (Task 1.3, AC1/AC2)"
    )


def test_rowreceiver_additively_supports_clientpath_while_preserving_default_path() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "ClientPath" in content, (
        "RowReceiver must expose ClientPath as the additive multi-client selector from Story 10.1."
    )
    assert "/root/SpacetimeClient" in content, (
        "RowReceiver must preserve the default /root/SpacetimeClient path for existing scenes."
    )


def test_rowreceiver_has_all_three_signal_handlers() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "RowInsertedEventHandler" in content, (
        "RowReceiver must declare RowInsertedEventHandler signal delegate (Task 1.6, AC1)"
    )
    assert "RowUpdatedEventHandler" in content, (
        "RowReceiver must declare RowUpdatedEventHandler signal delegate (Task 1.6, AC1)"
    )
    assert "RowDeletedEventHandler" in content, (
        "RowReceiver must declare RowDeletedEventHandler signal delegate (Task 1.6, AC1)"
    )


def test_rowreceiver_guards_with_editor_hint() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "Engine.IsEditorHint()" in content, (
        "RowReceiver must guard runtime wiring with Engine.IsEditorHint() "
        "to prevent event subscription during scene editing (Tasks 1.7, 1.8, 1.9, AC3)"
    )


def test_rowreceiver_implements_exit_tree() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "_ExitTree" in content, (
        "RowReceiver must override _ExitTree() to cleanly disconnect from "
        "SpacetimeClient.RowChanged (Task 1.9, AC4)"
    )


def test_rowreceiver_does_not_reference_forbidden_internal_types() -> None:
    content = _read(ROWRECEIVER_PATH)

    forbidden = [
        "SpacetimeSdkRowCallbackAdapter",
        "IRowChangeEventSink",
        "SpacetimeSdkConnectionAdapter",
        "RemoteTableHandleBase",
        "DbConnection",
        "IDbConnection",
    ]
    for symbol in forbidden:
        assert symbol not in content, (
            f"RowReceiver must NOT reference {symbol!r} — it must NOT introduce a parallel "
            f"event dispatch path (Dev Notes: Critical Constraint, Task 4.2, AC1)"
        )


def test_rowreceiver_uses_spacetime_client_row_changed_signal() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "RowChanged" in content, (
        "RowReceiver must subscribe to SpacetimeClient.RowChanged as its sole event source "
        "(Dev Notes: Critical Constraint, Task 1.7, AC1)"
    )


def test_rowreceiver_uses_instance_valid_guard_in_exit_tree() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "IsInstanceValid" in content, (
        "RowReceiver._ExitTree() must use IsInstanceValid() to guard disconnect "
        "in case the autoload was already freed (Task 1.9, AC4)"
    )


# ---------------------------------------------------------------------------
# Task 4.2 — Plugin registration assertions
# ---------------------------------------------------------------------------

def test_plugin_registers_rowreceiver_as_custom_type() -> None:
    content = _read(PLUGIN_PATH)
    assert 'AddCustomType' in content, (
        "GodotSpacetimePlugin must call AddCustomType (Task 2.1, AC1)"
    )
    assert '"RowReceiver"' in content, (
        'GodotSpacetimePlugin must pass "RowReceiver" to AddCustomType (Task 2.1, AC1)'
    )


def test_plugin_removes_rowreceiver_on_exit() -> None:
    content = _read(PLUGIN_PATH)
    assert 'RemoveCustomType' in content, (
        "GodotSpacetimePlugin must call RemoveCustomType (Task 2.2, AC1)"
    )
    assert '"RowReceiver"' in content, (
        'GodotSpacetimePlugin must pass "RowReceiver" to RemoveCustomType (Task 2.2, AC1)'
    )


# ---------------------------------------------------------------------------
# Task 4.2 — Documentation assertions
# ---------------------------------------------------------------------------

def test_runtime_boundaries_documents_rowreceiver() -> None:
    content = _read(RUNTIME_BOUNDARIES_PATH)
    assert "RowReceiver" in content, (
        "docs/runtime-boundaries.md must document the RowReceiver node (Task 3.1, AC1)"
    )


def test_runtime_boundaries_explains_no_parallel_dispatch() -> None:
    content = _read(RUNTIME_BOUNDARIES_PATH)
    assert "NOT a parallel dispatch path" in content or "not a parallel dispatch" in content.lower(), (
        "docs/runtime-boundaries.md must explain that RowReceiver is NOT a parallel dispatch path "
        "(Task 3.1, AC1)"
    )


def test_runtime_boundaries_documents_spacetime_client_autoload_requirement() -> None:
    content = _read(RUNTIME_BOUNDARIES_PATH)
    assert "/root/SpacetimeClient" in content, (
        "docs/runtime-boundaries.md must document that RowReceiver requires SpacetimeClient "
        "at /root/SpacetimeClient (Task 3.1, AC1)"
    )


def test_runtime_boundaries_documents_rowreceiver_clientpath_addition() -> None:
    content = _read(RUNTIME_BOUNDARIES_PATH)
    assert "ClientPath" in content, (
        "docs/runtime-boundaries.md must document RowReceiver.ClientPath for the additive Story 10.1 path."
    )


def test_demo_readme_documents_rowreceiver() -> None:
    content = _read(DEMO_README_PATH)
    assert "RowReceiver" in content, (
        "demo/README.md must document RowReceiver usage (Task 3.2, AC1)"
    )


def test_demo_readme_has_gdscript_example() -> None:
    content = _read(DEMO_README_PATH)
    assert "row_inserted" in content and "row_updated" in content and "row_deleted" in content, (
        "demo/README.md must show GDScript signal connection examples for "
        "row_inserted, row_updated, row_deleted (Task 3.2, AC1)"
    )


def test_demo_readme_has_csharp_example() -> None:
    content = _read(DEMO_README_PATH)
    assert "RowInserted" in content and "RowUpdated" in content and "RowDeleted" in content, (
        "demo/README.md must show C# event handler examples for "
        "RowInserted, RowUpdated, RowDeleted (Task 3.2, AC1)"
    )


def test_runtime_boundaries_documents_field_backed_generated_tables() -> None:
    content = _read(RUNTIME_BOUNDARIES_PATH)
    assert "public fields today" in content or "public fields" in content, (
        "docs/runtime-boundaries.md must document that current generated RemoteTables table members "
        "are field-backed so the Inspector dropdown guidance matches the real generated bindings "
        "(review regression guard)"
    )


# ---------------------------------------------------------------------------
# Task 4.2 — Story 7.x regression anchors
# ---------------------------------------------------------------------------

def test_story_7x_query_async_anchor_intact() -> None:
    content = _read(RUNTIME_BOUNDARIES_PATH)
    assert "QueryAsync" in content, (
        "Story 7.4 QueryAsync anchor must remain intact in docs/runtime-boundaries.md "
        "(Task 4.2 regression guard)"
    )


def test_story_7x_btree_index_anchor_intact() -> None:
    content = _read(RUNTIME_BOUNDARIES_PATH)
    assert "BTree" in content or "Value.Filter" in content, (
        "Story 7.3 BTree index filter anchor must remain intact in docs/runtime-boundaries.md "
        "(Task 4.2 regression guard)"
    )


def test_story_7x_typed_cache_access_anchor_intact() -> None:
    content = _read(RUNTIME_BOUNDARIES_PATH)
    assert "GetDb<TDb>()" in content, (
        "Story 7.2 typed cache access anchor (GetDb<TDb>()) must remain intact "
        "in docs/runtime-boundaries.md (Task 4.2 regression guard)"
    )


# ---------------------------------------------------------------------------
# Gap-fill assertions — structural details not covered by initial Task 4.2 tests
# ---------------------------------------------------------------------------

def test_rowreceiver_has_correct_namespace() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "namespace GodotSpacetime.Scenes" in content, (
        "RowReceiver must be in namespace GodotSpacetime.Scenes — the folder/namespace mirror "
        "convention requires Public/Scenes/ → GodotSpacetime.Scenes (Task 1.1, architecture rules)"
    )


def test_rowreceiver_has_get_property_list_override() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "_GetPropertyList" in content, (
        "RowReceiver must override _GetPropertyList() to return the PROPERTY_HINT_ENUM dropdown "
        "for the TableName property so the Inspector shows a table-name dropdown (Task 1.4, AC2)"
    )


def test_rowreceiver_has_discover_table_names_method() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "DiscoverTableNames" in content, (
        "RowReceiver must implement DiscoverTableNames() — the static method that scans "
        "AppDomain assemblies for a RemoteTables type and returns its property names (Task 1.5, AC2)"
    )


def test_rowreceiver_get_property_list_uses_property_hint_enum() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "PropertyHint.Enum" in content or "PROPERTY_HINT_ENUM" in content, (
        "RowReceiver._GetPropertyList() must use PropertyHint.Enum (PROPERTY_HINT_ENUM) to "
        "render a dropdown in the Inspector for the TableName property (Task 1.4, AC2)"
    )


def test_rowreceiver_discover_table_names_uses_internal_generated_binding_resolver() -> None:
    row_receiver = _read(ROWRECEIVER_PATH)
    resolver = _read(GENERATED_BINDING_RESOLVER_PATH)
    assert "GeneratedBindingTypeResolver" in row_receiver and "GetRemoteTableNames" in row_receiver, (
        "Story 10.1 must keep RowReceiver table-name discovery routed through the internal generated-binding "
        "resolver instead of doing first-type-wins assembly scans in the public scene node."
    )
    assert "ResolveRemoteTablesType" in resolver, (
        "GeneratedBindingTypeResolver must provide the namespace-scoped RemoteTables resolution path used by "
        "RowReceiver inspector discovery."
    )


def test_rowreceiver_no_longer_uses_public_first_type_wins_assembly_scans() -> None:
    content = _read(ROWRECEIVER_PATH)
    for forbidden in (
        "AppDomain.CurrentDomain.GetAssemblies()",
        "ShouldSkipAssembly",
        "SafeGetTypes",
    ):
        assert forbidden not in content, (
            "Story 10.1 must remove the old first-type-wins assembly scan from RowReceiver and keep generated-type "
            f"reflection inside Internal/Platform/DotNet/. Found stale token {forbidden!r}."
        )


def test_rowreceiver_discover_table_names_scans_for_remote_tables_type_name() -> None:
    resolver = _read(GENERATED_BINDING_RESOLVER_PATH)
    assert '"RemoteTables"' in resolver, (
        "GeneratedBindingTypeResolver must still resolve the generated RemoteTables type by name for inspector "
        "table discovery."
    )
    assert "generatedBindingsNamespace" in resolver, (
        "Story 10.1 RowReceiver discovery must be namespace-scoped so multiple generated modules can coexist."
    )


def test_rowreceiver_discover_table_names_supports_field_backed_generated_tables() -> None:
    content = _read(GENERATED_BINDING_RESOLVER_PATH)
    assert "GetFields" in content, (
        "RowReceiver.DiscoverTableNames() must read public instance fields because the current "
        "SpacetimeDB 2.1.x generated RemoteTables surface exposes table handles as fields, not only "
        "properties (AC2 regression guard)"
    )
    assert "BindingFlags.DeclaredOnly" in content, (
        "RowReceiver.DiscoverTableNames() must scope member discovery to members declared on "
        "RemoteTables so inherited framework members do not leak into the Inspector dropdown "
        "(AC2 regression guard)"
    )


def test_rowreceiver_signals_carry_row_changed_event_payload() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "RowChangedEvent" in content, (
        "RowReceiver signal delegates must use RowChangedEvent as the payload type — "
        "RowChangedEvent extends RefCounted which is Godot-signal-compatible; plain C# row "
        "objects are not (Task 1.6, AC1, Signal Design Decision)"
    )


def test_rowreceiver_has_on_row_changed_handler() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "OnRowChanged" in content, (
        "RowReceiver must implement the OnRowChanged(RowChangedEvent e) handler that filters "
        "by TableName and emits the appropriate sub-signal (Task 1.8, AC1)"
    )


def test_rowreceiver_on_row_changed_filters_by_table_name() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "e.TableName" in content, (
        "RowReceiver.OnRowChanged must compare e.TableName against the configured TableName "
        "property to scope events to a single table (Task 1.8, AC1)"
    )


def test_rowreceiver_on_row_changed_dispatches_all_three_change_types() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "RowChangeType.Insert" in content, (
        "RowReceiver.OnRowChanged must handle RowChangeType.Insert to emit row_inserted (Task 1.8, AC1)"
    )
    assert "RowChangeType.Update" in content, (
        "RowReceiver.OnRowChanged must handle RowChangeType.Update to emit row_updated (Task 1.8, AC1)"
    )
    assert "RowChangeType.Delete" in content, (
        "RowReceiver.OnRowChanged must handle RowChangeType.Delete to emit row_deleted (Task 1.8, AC1)"
    )


def test_rowreceiver_emits_signal_in_on_row_changed() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "EmitSignal" in content, (
        "RowReceiver.OnRowChanged must call EmitSignal to fire the scoped sub-signal "
        "after matching the TableName and ChangeType (Task 1.8, AC1)"
    )


def test_rowreceiver_uses_push_warning_not_push_error_for_missing_autoload() -> None:
    content = _read(ROWRECEIVER_PATH)
    # G6 (spec-g6-pluggable-logger-interface) rerouted the direct GD.PushWarning through
    # the SpacetimeLog facade. The default GodotConsoleLogSink still lands the message on
    # GD.PushWarning (warning-level route), preserving the Story 8.1 graceful-degrade intent.
    assert "SpacetimeLog.Warning" in content, (
        "RowReceiver._Ready() must log via SpacetimeLog.Warning when SpacetimeClient "
        "autoload is absent — the node must not hard-fail in scenes that don't use SpacetimeDB "
        "(Task 1.7, Dev Notes; post-G6 routing)"
    )
    assert "SpacetimeLog.Error" not in content and "GD.PushError" not in content, (
        "RowReceiver must not route the missing-autoload case through SpacetimeLog.Error "
        "or GD.PushError — warning-level only, so the node degrades gracefully instead of "
        "raising a hard editor error (Task 1.7, Dev Notes; post-G6 routing)"
    )


def test_rowreceiver_subscribes_to_row_changed_with_plus_equals() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "RowChanged +=" in content, (
        "RowReceiver._Ready() must subscribe to SpacetimeClient.RowChanged via the += operator "
        "(Task 1.7, AC1)"
    )


def test_rowreceiver_unsubscribes_from_row_changed_with_minus_equals() -> None:
    content = _read(ROWRECEIVER_PATH)
    assert "RowChanged -=" in content, (
        "RowReceiver._ExitTree() must unsubscribe from SpacetimeClient.RowChanged via the -= "
        "operator to avoid orphaned signal connections after the node leaves the tree "
        "(Task 1.9, AC4)"
    )


def test_plugin_passes_node_as_base_type_to_add_custom_type() -> None:
    content = _read(PLUGIN_PATH)
    assert '"Node"' in content, (
        'GodotSpacetimePlugin.AddCustomType must pass "Node" as the base type string — '
        "RowReceiver extends Node, so the Godot type system must know its parent (Task 2.1, AC1)"
    )
