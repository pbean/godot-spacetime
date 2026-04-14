"""
Story 1.9: Configure and Open a First Connection from Godot
Automated contract tests for all story deliverables.

Covers:
- Existence of all new .cs and .tscn files
- SpacetimeClient.cs Connect/Disconnect/signals/_Process implementation (AC: 1,2,3,4,6)
- SpacetimeConnectionService.cs exposure surface (AC: 1,2,3,4,7)
- ConnectionStateMachine.cs states and Transition method (AC: 1,2,4)
- ReconnectPolicy.cs existence (AC: 2)
- SpacetimeSdkConnectionAdapter.cs SDK builder pattern, no stub pragma (AC: 1,7)
- GodotSignalAdapter.cs existence (AC: 2,6)
- ConnectionOpenedEvent.cs Host/Database/ConnectedAt payload (AC: 6)
- ConnectionAuthStatusPanel.cs explicit text labels, layout requirements (AC: 5)
- ConnectionAuthStatusPanel.tscn scene structure (AC: 5)
- GodotSpacetimePlugin.cs third panel registration (AC: 5)
- support-baseline.json new required paths
- docs/connection.md lifecycle documentation (AC: 2)
- Regression guards from Stories 1.7 and 1.8
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# Existence tests — all new .cs and .tscn files created in Story 1.9
# ---------------------------------------------------------------------------

def test_spacetime_connection_service_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs").is_file(), (
        "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs is missing"
    )


def test_connection_state_machine_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs").is_file(), (
        "addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs is missing"
    )


def test_reconnect_policy_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs").is_file(), (
        "addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs is missing"
    )


def test_godot_signal_adapter_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs").is_file(), (
        "addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs is missing"
    )


def test_connection_auth_status_panel_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs").is_file(), (
        "addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs is missing"
    )


def test_connection_auth_status_panel_tscn_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn").is_file(), (
        "addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn is missing"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.cs — runtime implementation (AC: 1, 2, 3, 4, 6)
# ---------------------------------------------------------------------------

def test_spacetime_client_has_connect_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "Connect(" in content, (
        "SpacetimeClient.cs must implement a Connect() method"
    )


def test_spacetime_client_has_disconnect_method() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "Disconnect(" in content, (
        "SpacetimeClient.cs must implement a Disconnect() method"
    )


def test_spacetime_client_has_connection_state_changed_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionStateChanged" in content, (
        "SpacetimeClient.cs must declare a ConnectionStateChanged signal"
    )


def test_spacetime_client_has_connection_opened_signal() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "ConnectionOpened" in content, (
        "SpacetimeClient.cs must declare a ConnectionOpened signal"
    )


def test_spacetime_client_has_frame_advancement() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "FrameTick" in content or "_Process" in content, (
        "SpacetimeClient.cs must wire FrameTick advancement via _Process"
    )


def test_spacetime_client_references_spacetime_settings() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "SpacetimeSettings" in content, (
        "SpacetimeClient.cs must reference SpacetimeSettings for the settings property"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — internal service (AC: 1, 2, 3, 4, 7)
# ---------------------------------------------------------------------------

def test_connection_service_has_connect_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Connect(" in content, (
        "SpacetimeConnectionService.cs must expose a Connect() method"
    )


def test_connection_service_has_disconnect_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Disconnect(" in content, (
        "SpacetimeConnectionService.cs must expose a Disconnect() method"
    )


def test_connection_service_has_frame_tick_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "FrameTick(" in content, (
        "SpacetimeConnectionService.cs must expose a FrameTick() method"
    )


def test_connection_service_has_state_changed_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnStateChanged" in content or "StateChanged" in content, (
        "SpacetimeConnectionService.cs must fire a state-changed event (OnStateChanged or StateChanged)"
    )


def test_connection_service_has_connection_opened_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnConnectionOpened" in content or "ConnectionOpened" in content, (
        "SpacetimeConnectionService.cs must fire a connection-opened event (OnConnectionOpened or ConnectionOpened)"
    )


# ---------------------------------------------------------------------------
# ConnectionStateMachine.cs — state transitions (AC: 1, 2, 4)
# ---------------------------------------------------------------------------

def test_state_machine_has_transition_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs")
    assert "Transition(" in content, (
        "ConnectionStateMachine.cs must expose a Transition() method"
    )


def test_state_machine_has_disconnected_state() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs")
    assert "Disconnected" in content, (
        "ConnectionStateMachine.cs must reference the Disconnected state"
    )


def test_state_machine_has_connecting_state() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs")
    assert "Connecting" in content, (
        "ConnectionStateMachine.cs must reference the Connecting state"
    )


def test_state_machine_has_connected_state() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs")
    assert "Connected" in content, (
        "ConnectionStateMachine.cs must reference the Connected state"
    )


def test_state_machine_has_degraded_state() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs")
    assert "Degraded" in content, (
        "ConnectionStateMachine.cs must reference the Degraded state"
    )


def test_state_machine_raises_state_changed_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs")
    assert "StateChanged" in content, (
        "ConnectionStateMachine.cs must raise a StateChanged event on each valid transition"
    )


# ---------------------------------------------------------------------------
# SpacetimeSdkConnectionAdapter.cs — SDK bridge (AC: 1, 7)
# ---------------------------------------------------------------------------

def test_sdk_adapter_uses_builder_pattern() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "DbConnection.Builder" in content or "WithUri" in content, (
        "SpacetimeSdkConnectionAdapter.cs must use the ClientSDK DbConnection.Builder() pattern"
    )


def test_sdk_adapter_has_frame_tick() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "FrameTick" in content, (
        "SpacetimeSdkConnectionAdapter.cs must implement FrameTick() to advance the ClientSDK loop"
    )


def test_sdk_adapter_removes_stub_pragma() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "#pragma warning disable CS0169" not in content, (
        "SpacetimeSdkConnectionAdapter.cs must not contain '#pragma warning disable CS0169' — "
        "the stub suppressor must be removed once _dbConnection is actively managed"
    )


# ---------------------------------------------------------------------------
# ConnectionOpenedEvent.cs — event payload (AC: 6)
# ---------------------------------------------------------------------------

def test_connection_opened_event_has_host() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs")
    assert "Host" in content, (
        "ConnectionOpenedEvent.cs must include a Host property"
    )


def test_connection_opened_event_has_database() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs")
    assert "Database" in content, (
        "ConnectionOpenedEvent.cs must include a Database property"
    )


def test_connection_opened_event_has_connected_at() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs")
    assert "ConnectedAt" in content, (
        "ConnectionOpenedEvent.cs must include a ConnectedAt timestamp property"
    )


# ---------------------------------------------------------------------------
# ConnectionAuthStatusPanel.cs — editor panel explicit text labels (AC: 5)
# ---------------------------------------------------------------------------

def test_status_panel_has_disconnected_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "DISCONNECTED \u2014 not connected to SpacetimeDB" in content, (
        "ConnectionAuthStatusPanel.cs must contain 'DISCONNECTED \u2014 not connected to SpacetimeDB'"
    )


def test_status_panel_has_connecting_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "CONNECTING \u2014 connection attempt in progress" in content, (
        "ConnectionAuthStatusPanel.cs must contain 'CONNECTING \u2014 connection attempt in progress'"
    )


def test_status_panel_has_connected_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "CONNECTED \u2014 active session established" in content, (
        "ConnectionAuthStatusPanel.cs must contain 'CONNECTED \u2014 active session established'"
    )


def test_status_panel_has_degraded_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "DEGRADED \u2014 session experiencing issues; reconnecting" in content, (
        "ConnectionAuthStatusPanel.cs must contain 'DEGRADED \u2014 session experiencing issues; reconnecting'"
    )


def test_status_panel_has_not_configured_text() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "NOT CONFIGURED \u2014 assign a SpacetimeSettings resource" in content, (
        "ConnectionAuthStatusPanel.cs must contain 'NOT CONFIGURED \u2014 assign a SpacetimeSettings resource'"
    )


def test_status_panel_has_focus_mode_all() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "FocusModeEnum.All" in content, (
        "ConnectionAuthStatusPanel.cs must set FocusModeEnum.All for keyboard navigation (AC: 5)"
    )


def test_status_panel_has_autowrap_mode() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "AutowrapMode" in content and "WordSmart" in content, (
        "ConnectionAuthStatusPanel.cs must enable AutowrapMode.WordSmart for narrow panel support (AC: 5)"
    )


def test_status_panel_has_custom_minimum_size() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "CustomMinimumSize" in content, (
        "ConnectionAuthStatusPanel.cs must set CustomMinimumSize for narrow panel support (AC: 5)"
    )


# ---------------------------------------------------------------------------
# ConnectionAuthStatusPanel.cs — structural requirements (following 1.8 pattern)
# ---------------------------------------------------------------------------

def test_status_panel_has_tools_conditional_compile_guard() -> None:
    """Panel must be wrapped in #if TOOLS to prevent compile errors in non-tool builds."""
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "#if TOOLS" in content, (
        "ConnectionAuthStatusPanel.cs must be wrapped in '#if TOOLS' guard"
    )
    assert "#endif" in content, (
        "ConnectionAuthStatusPanel.cs must close its '#if TOOLS' guard with '#endif'"
    )


def test_status_panel_has_tool_attribute() -> None:
    """Panel must have [Tool] so it evaluates in editor context."""
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "[Tool]" in content, (
        "ConnectionAuthStatusPanel.cs must have the [Tool] attribute"
    )


def test_status_panel_has_correct_namespace() -> None:
    """Panel must use the GodotSpacetime.Editor.Status namespace."""
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "GodotSpacetime.Editor.Status" in content, (
        "ConnectionAuthStatusPanel.cs must declare namespace GodotSpacetime.Editor.Status"
    )


def test_status_panel_extends_vbox_container() -> None:
    """Panel must extend VBoxContainer for vertical stacking in narrow panels."""
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "VBoxContainer" in content, (
        "ConnectionAuthStatusPanel.cs must extend VBoxContainer"
    )


# ---------------------------------------------------------------------------
# ConnectionAuthStatusPanel.tscn — scene content validation
# ---------------------------------------------------------------------------

def test_status_tscn_uses_format_3() -> None:
    """Scene file must use Godot 4 format=3."""
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn")
    assert "format=3" in content, (
        "ConnectionAuthStatusPanel.tscn must use 'format=3' (Godot 4 scene format)"
    )


def test_status_tscn_root_is_vbox_container() -> None:
    """Scene root must be VBoxContainer to match the class hierarchy."""
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn")
    assert 'type="VBoxContainer"' in content, (
        'ConnectionAuthStatusPanel.tscn root node must be type="VBoxContainer"'
    )


def test_status_tscn_attaches_correct_script() -> None:
    """Scene must reference the ConnectionAuthStatusPanel.cs script."""
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn")
    assert "ConnectionAuthStatusPanel.cs" in content, (
        "ConnectionAuthStatusPanel.tscn must attach ConnectionAuthStatusPanel.cs as the node script"
    )


# ---------------------------------------------------------------------------
# GodotSpacetimePlugin.cs — third panel registration (AC: 5)
# ---------------------------------------------------------------------------

def test_plugin_registers_three_panels() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert content.count("AddControlToBottomPanel") == 3, (
        "GodotSpacetimePlugin.cs must call AddControlToBottomPanel three times (codegen + compat + status panels)"
    )


def test_plugin_has_spacetime_status_tab_label() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert '"Spacetime Status"' in content, (
        "GodotSpacetimePlugin.cs must register status panel with tab label 'Spacetime Status'"
    )


def test_plugin_references_connection_auth_status_panel_type() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "ConnectionAuthStatusPanel" in content, (
        "GodotSpacetimePlugin.cs must reference the ConnectionAuthStatusPanel type"
    )


def test_plugin_has_status_panel_scene_path_constant() -> None:
    """Plugin must declare StatusPanelScenePath constant with the correct scene path."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "StatusPanelScenePath" in content, (
        "GodotSpacetimePlugin.cs must declare a 'StatusPanelScenePath' constant"
    )
    assert "ConnectionAuthStatusPanel.tscn" in content, (
        "GodotSpacetimePlugin.cs StatusPanelScenePath must reference 'ConnectionAuthStatusPanel.tscn'"
    )


def test_plugin_removes_three_panels_in_exit_tree() -> None:
    """Plugin must call RemoveControlFromBottomPanel three times — once per registered panel."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert content.count("RemoveControlFromBottomPanel") == 3, (
        "GodotSpacetimePlugin.cs must call RemoveControlFromBottomPanel three times (codegen + compat + status cleanup)"
    )


def test_plugin_has_using_status_namespace() -> None:
    """Plugin must import the Editor.Status namespace to use ConnectionAuthStatusPanel."""
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert "GodotSpacetime.Editor.Status" in content, (
        "GodotSpacetimePlugin.cs must import 'GodotSpacetime.Editor.Status' namespace"
    )


# ---------------------------------------------------------------------------
# support-baseline.json — new required paths (AC: 5)
# ---------------------------------------------------------------------------

def test_support_baseline_has_editor_status_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "addons/godot_spacetime/src/Editor/Status" in content, (
        "support-baseline.json must include 'addons/godot_spacetime/src/Editor/Status' in required_paths"
    )


def test_support_baseline_has_connection_auth_status_panel_cs_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "ConnectionAuthStatusPanel.cs" in content, (
        "support-baseline.json must include 'ConnectionAuthStatusPanel.cs' in required_paths"
    )


def test_support_baseline_has_connection_auth_status_panel_tscn_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "ConnectionAuthStatusPanel.tscn" in content, (
        "support-baseline.json must include 'ConnectionAuthStatusPanel.tscn' in required_paths"
    )


def test_support_baseline_has_internal_connection_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "addons/godot_spacetime/src/Internal/Connection" in content, (
        "support-baseline.json must include 'addons/godot_spacetime/src/Internal/Connection' in required_paths"
    )


def test_support_baseline_has_connection_md_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "docs/connection.md" in content, (
        "support-baseline.json must include 'docs/connection.md' in required_paths"
    )


def test_support_baseline_has_connection_lifecycle_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "Connection Lifecycle" in content, (
        "support-baseline.json must include a line_check entry for 'Connection Lifecycle' in docs/connection.md"
    )


# ---------------------------------------------------------------------------
# docs/connection.md — lifecycle documentation (AC: 2)
# ---------------------------------------------------------------------------

def test_connection_md_has_lifecycle_section() -> None:
    lines = _lines("docs/connection.md")
    assert "## Connection Lifecycle" in lines, (
        "docs/connection.md must contain '## Connection Lifecycle' as an exact stripped line"
    )


def test_connection_md_documents_disconnected_state() -> None:
    content = _read("docs/connection.md")
    assert "Disconnected" in content, (
        "docs/connection.md must document the 'Disconnected' connection state"
    )


def test_connection_md_documents_connecting_state() -> None:
    content = _read("docs/connection.md")
    assert "Connecting" in content, (
        "docs/connection.md must document the 'Connecting' connection state"
    )


def test_connection_md_documents_connected_state() -> None:
    content = _read("docs/connection.md")
    assert "Connected" in content, (
        "docs/connection.md must document the 'Connected' connection state"
    )


def test_connection_md_documents_degraded_state() -> None:
    content = _read("docs/connection.md")
    assert "Degraded" in content, (
        "docs/connection.md must document the 'Degraded' connection state"
    )


def test_connection_md_references_signal_name() -> None:
    content = _read("docs/connection.md")
    assert "connection_state_changed" in content, (
        "docs/connection.md must reference the 'connection_state_changed' Godot signal name"
    )


# ---------------------------------------------------------------------------
# Regression guards — Stories 1.7 and 1.8 panels still present and registered
# ---------------------------------------------------------------------------

def test_codegen_validation_panel_cs_still_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs").is_file(), (
        "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs is missing (regression from Story 1.7)"
    )


def test_codegen_validation_panel_tscn_still_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn").is_file(), (
        "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn is missing (regression from Story 1.7)"
    )


def test_compatibility_panel_cs_still_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs").is_file(), (
        "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs is missing (regression from Story 1.8)"
    )


def test_compatibility_panel_tscn_still_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn").is_file(), (
        "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn is missing (regression from Story 1.8)"
    )


def test_plugin_still_registers_codegen_panel() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert '"Spacetime Codegen"' in content, (
        "GodotSpacetimePlugin.cs must still register codegen panel with tab label 'Spacetime Codegen' (regression from Story 1.7)"
    )


def test_plugin_still_registers_compat_panel() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert '"Spacetime Compat"' in content, (
        "GodotSpacetimePlugin.cs must still register compat panel with tab label 'Spacetime Compat' (regression from Story 1.8)"
    )


# ---------------------------------------------------------------------------
# Regression guard — architecture boundary intact
# ---------------------------------------------------------------------------

def test_sdk_adapter_is_in_internal_platform_dotnet() -> None:
    """SpacetimeSdkConnectionAdapter must remain in Internal/Platform/DotNet/ — boundary regression."""
    assert (ROOT / "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs").is_file(), (
        "SpacetimeSdkConnectionAdapter.cs must remain in Internal/Platform/DotNet/ (architecture boundary regression)"
    )
