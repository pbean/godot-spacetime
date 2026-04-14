"""
Story 1.10: Validate First Setup Through a Quickstart Path
Automated contract tests for all story deliverables.

Covers:
- Existence of docs/quickstart.md
- docs/quickstart.md content: heading, prerequisites, failure recovery, commands, API references, panel names
- docs/quickstart.md panel state strings: codegen OK, compat OK, status NOT CONFIGURED, CONNECTED
- docs/quickstart.md failure recovery: DISCONNECTED and DEGRADED states
- docs/quickstart.md keyboard navigation mention (AC: 3)
- docs/quickstart.md See Also section
- support-baseline.json: quickstart.md path and all six line_check entries
- docs/install.md: quickstart.md See Also reference
- docs/codegen.md: quickstart.md See Also reference
- Regression guards — Stories 1.7, 1.8, 1.9 panels still registered in GodotSpacetimePlugin.cs
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# Existence test
# ---------------------------------------------------------------------------

def test_quickstart_md_exists() -> None:
    assert (ROOT / "docs/quickstart.md").is_file(), (
        "docs/quickstart.md is missing — Task 1 deliverable"
    )


# ---------------------------------------------------------------------------
# docs/quickstart.md — content tests
# ---------------------------------------------------------------------------

def test_quickstart_has_quickstart_heading() -> None:
    lines = _lines("docs/quickstart.md")
    assert "## Quickstart" in lines, (
        "docs/quickstart.md must contain '## Quickstart' as an exact stripped line (required for line_check)"
    )


def test_quickstart_has_failure_recovery_section() -> None:
    content = _read("docs/quickstart.md")
    assert "## Failure Recovery" in content or "## Troubleshooting" in content, (
        "docs/quickstart.md must contain a '## Failure Recovery' or '## Troubleshooting' section"
    )


def test_quickstart_has_foundation_validation_command() -> None:
    content = _read("docs/quickstart.md")
    assert "python3 scripts/compatibility/validate-foundation.py" in content, (
        "docs/quickstart.md must contain 'python3 scripts/compatibility/validate-foundation.py'"
    )


def test_quickstart_has_codegen_script() -> None:
    content = _read("docs/quickstart.md")
    assert "bash scripts/codegen/generate-smoke-test.sh" in content, (
        "docs/quickstart.md must contain 'bash scripts/codegen/generate-smoke-test.sh'"
    )


def test_quickstart_explains_spacetime_settings() -> None:
    content = _read("docs/quickstart.md")
    assert "SpacetimeSettings" in content, (
        "docs/quickstart.md must explain SpacetimeSettings resource configuration"
    )


def test_quickstart_explains_spacetime_client() -> None:
    content = _read("docs/quickstart.md")
    assert "SpacetimeClient" in content, (
        "docs/quickstart.md must explain SpacetimeClient autoload registration"
    )


def test_quickstart_uses_actual_spacetime_client_autoload_path() -> None:
    content = _read("docs/quickstart.md")
    assert "addons/godot_spacetime/src/Public/SpacetimeClient.cs" in content, (
        "docs/quickstart.md must point the autoload step at the actual SpacetimeClient script path"
    )


def test_quickstart_shows_connect_call() -> None:
    content = _read("docs/quickstart.md")
    assert "Connect(" in content, (
        "docs/quickstart.md must show the Connect() call"
    )


def test_quickstart_mentions_connection_state_changed_signal() -> None:
    content = _read("docs/quickstart.md")
    assert "connection_state_changed" in content, (
        "docs/quickstart.md must mention the connection_state_changed signal"
    )


def test_quickstart_references_codegen_panel() -> None:
    content = _read("docs/quickstart.md")
    assert '"Spacetime Codegen"' in content, (
        "docs/quickstart.md must reference the '\"Spacetime Codegen\"' panel by name"
    )


def test_quickstart_references_compat_panel() -> None:
    content = _read("docs/quickstart.md")
    assert '"Spacetime Compat"' in content, (
        "docs/quickstart.md must reference the '\"Spacetime Compat\"' panel by name"
    )


def test_quickstart_references_status_panel() -> None:
    content = _read("docs/quickstart.md")
    assert '"Spacetime Status"' in content, (
        "docs/quickstart.md must reference the '\"Spacetime Status\"' panel by name"
    )


def test_quickstart_references_install_md() -> None:
    content = _read("docs/quickstart.md")
    assert "docs/install.md" in content, (
        "docs/quickstart.md must contain a reference to docs/install.md"
    )


def test_quickstart_references_codegen_md() -> None:
    content = _read("docs/quickstart.md")
    assert "docs/codegen.md" in content, (
        "docs/quickstart.md must contain a reference to docs/codegen.md"
    )


def test_quickstart_references_connection_md() -> None:
    content = _read("docs/quickstart.md")
    assert "docs/connection.md" in content, (
        "docs/quickstart.md must contain a reference to docs/connection.md"
    )


# ---------------------------------------------------------------------------
# support-baseline.json — quickstart.md entries
# ---------------------------------------------------------------------------

def test_support_baseline_has_quickstart_md_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "docs/quickstart.md" in content, (
        "support-baseline.json must include 'docs/quickstart.md' in required_paths"
    )


def test_support_baseline_has_quickstart_heading_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert '"Quickstart top-level heading"' in content, (
        "support-baseline.json must include a line_check entry with label 'Quickstart top-level heading'"
    )


# ---------------------------------------------------------------------------
# docs/install.md — quickstart.md See Also reference
# ---------------------------------------------------------------------------

def test_install_md_references_quickstart() -> None:
    content = _read("docs/install.md")
    assert "quickstart.md" in content, (
        "docs/install.md must reference quickstart.md in its See Also section"
    )


# ---------------------------------------------------------------------------
# docs/codegen.md — quickstart.md See Also reference
# ---------------------------------------------------------------------------

def test_codegen_md_references_quickstart() -> None:
    content = _read("docs/codegen.md")
    assert "quickstart.md" in content, (
        "docs/codegen.md must reference quickstart.md in its See Also section"
    )


# ---------------------------------------------------------------------------
# Regression guards — Stories 1.7, 1.8, 1.9 panels still registered
# ---------------------------------------------------------------------------

def test_plugin_still_has_spacetime_codegen_label() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert '"Spacetime Codegen"' in content, (
        "GodotSpacetimePlugin.cs must still register 'Spacetime Codegen' panel (regression from Story 1.7)"
    )


def test_plugin_still_has_spacetime_compat_label() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert '"Spacetime Compat"' in content, (
        "GodotSpacetimePlugin.cs must still register 'Spacetime Compat' panel (regression from Story 1.8)"
    )


def test_plugin_still_has_spacetime_status_label() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert '"Spacetime Status"' in content, (
        "GodotSpacetimePlugin.cs must still register 'Spacetime Status' panel (regression from Story 1.9)"
    )


def test_plugin_still_registers_three_panels() -> None:
    content = _read("addons/godot_spacetime/GodotSpacetimePlugin.cs")
    assert content.count("AddControlToBottomPanel") == 3, (
        "GodotSpacetimePlugin.cs must call AddControlToBottomPanel exactly three times (codegen + compat + status)"
    )


# ---------------------------------------------------------------------------
# support-baseline.json — remaining five quickstart.md line_check labels
# ---------------------------------------------------------------------------

def test_support_baseline_has_quickstart_foundation_command_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert '"Quickstart foundation validation command"' in content, (
        "support-baseline.json must include a line_check entry with label "
        "'Quickstart foundation validation command'"
    )


def test_support_baseline_has_quickstart_codegen_script_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert '"Quickstart codegen script"' in content, (
        "support-baseline.json must include a line_check entry with label 'Quickstart codegen script'"
    )


def test_support_baseline_has_quickstart_install_md_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert '"Quickstart install.md reference"' in content, (
        "support-baseline.json must include a line_check entry with label 'Quickstart install.md reference'"
    )


def test_support_baseline_has_quickstart_codegen_md_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert '"Quickstart codegen.md reference"' in content, (
        "support-baseline.json must include a line_check entry with label 'Quickstart codegen.md reference'"
    )


def test_support_baseline_has_quickstart_connection_md_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert '"Quickstart connection.md reference"' in content, (
        "support-baseline.json must include a line_check entry with label 'Quickstart connection.md reference'"
    )


# ---------------------------------------------------------------------------
# docs/quickstart.md — prerequisites section (AC: 1)
# ---------------------------------------------------------------------------

def test_quickstart_has_prerequisites_section() -> None:
    content = _read("docs/quickstart.md")
    assert "## Prerequisites" in content, (
        "docs/quickstart.md must contain a '## Prerequisites' section (AC: 1)"
    )


def test_quickstart_prerequisites_states_godot_version() -> None:
    content = _read("docs/quickstart.md")
    assert "4.6.2" in content, (
        "docs/quickstart.md must state the required Godot version (4.6.2) in Prerequisites (AC: 1)"
    )


def test_quickstart_prerequisites_states_dotnet_version() -> None:
    content = _read("docs/quickstart.md")
    assert "8.0+" in content, (
        "docs/quickstart.md must state the required .NET SDK version (8.0+) in Prerequisites (AC: 1)"
    )


def test_quickstart_prerequisites_states_cli_version() -> None:
    content = _read("docs/quickstart.md")
    assert "2.1+" in content, (
        "docs/quickstart.md must state the required SpacetimeDB CLI version (2.1+) in Prerequisites (AC: 1)"
    )


# ---------------------------------------------------------------------------
# docs/quickstart.md — See Also section (AC: 1)
# ---------------------------------------------------------------------------

def test_quickstart_has_see_also_section() -> None:
    content = _read("docs/quickstart.md")
    assert "## See Also" in content, (
        "docs/quickstart.md must contain a '## See Also' section (AC: 1)"
    )


# ---------------------------------------------------------------------------
# docs/quickstart.md — panel state strings (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_quickstart_mentions_codegen_panel_ok_state() -> None:
    content = _read("docs/quickstart.md")
    assert "bindings present" in content, (
        "docs/quickstart.md must show the 'Spacetime Codegen' OK state string "
        "('bindings present') so developers know what success looks like (AC: 1)"
    )


def test_quickstart_mentions_compat_panel_ok_state() -> None:
    content = _read("docs/quickstart.md")
    assert "bindings match declared baseline" in content, (
        "docs/quickstart.md must show the 'Spacetime Compat' OK state string "
        "('bindings match declared baseline') so developers know what success looks like (AC: 1)"
    )


def test_quickstart_explains_compatibility_depends_on_generated_bindings() -> None:
    content = _read("docs/quickstart.md")
    assert "generated bindings are up to date" in content, (
        "docs/quickstart.md must describe compatibility in terms of generated binding freshness, "
        "which is what the CompatibilityPanel actually validates"
    )


def test_quickstart_mentions_status_panel_not_configured_state() -> None:
    content = _read("docs/quickstart.md")
    assert "NOT CONFIGURED" in content, (
        "docs/quickstart.md must show the 'Spacetime Status' NOT CONFIGURED state "
        "so developers know the expected intermediate state before Connect() (AC: 1)"
    )


def test_quickstart_mentions_status_panel_connected_state() -> None:
    content = _read("docs/quickstart.md")
    assert "CONNECTED \u2014 active session established" in content, (
        "docs/quickstart.md must show the 'Spacetime Status' CONNECTED state string "
        "so developers know what a successful connection looks like (AC: 1)"
    )


# ---------------------------------------------------------------------------
# docs/quickstart.md — failure recovery completeness (AC: 2)
# ---------------------------------------------------------------------------

def test_quickstart_failure_recovery_covers_disconnected_state() -> None:
    content = _read("docs/quickstart.md")
    assert "DISCONNECTED" in content, (
        "docs/quickstart.md Failure Recovery must reference the DISCONNECTED panel state "
        "as a visible indicator for connection failures (AC: 2)"
    )


def test_quickstart_failure_recovery_covers_degraded_state() -> None:
    content = _read("docs/quickstart.md")
    assert "DEGRADED" in content, (
        "docs/quickstart.md Failure Recovery must reference the DEGRADED panel state "
        "as a visible indicator for session issues (AC: 2)"
    )


# ---------------------------------------------------------------------------
# docs/quickstart.md — keyboard accessibility (AC: 3)
# ---------------------------------------------------------------------------

def test_quickstart_mentions_keyboard_navigation() -> None:
    content = _read("docs/quickstart.md")
    assert "keyboard" in content.lower(), (
        "docs/quickstart.md must mention keyboard navigation — AC: 3 requires "
        "keyboard-only progression through the primary path"
    )
