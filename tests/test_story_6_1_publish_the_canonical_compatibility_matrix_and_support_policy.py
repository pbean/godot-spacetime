"""
Tests for Story 6.1: Publish the Canonical Compatibility Matrix and Support Policy

Validates:
- docs/compatibility-matrix.md has been rewritten as an adopter-facing canonical document (AC 1, 2, 3)
- docs/runtime-boundaries.md has the ITokenStore externalization sentence (C3)
- ConnectionAuthState.AuthRequired dead code has been removed (D1/C1)
- All prior story deliverables remain intact (regression guards)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


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
# 4.1 Existence test
# ---------------------------------------------------------------------------

def test_compatibility_matrix_exists() -> None:
    path = ROOT / "docs" / "compatibility-matrix.md"
    assert path.exists(), "docs/compatibility-matrix.md must exist (AC 1)"


# ---------------------------------------------------------------------------
# 4.2 Section presence tests
# ---------------------------------------------------------------------------

def test_support_policy_section_present() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "## Support Policy\n" in content, (
        "docs/compatibility-matrix.md must contain '## Support Policy' section (AC 2)"
    )


def test_compatibility_triage_timeline_section_present() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "## Compatibility Triage Timeline\n" in content, (
        "docs/compatibility-matrix.md must contain '## Compatibility Triage Timeline' section (AC 1)"
    )


def test_version_change_guidance_section_present() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "## Version Change Guidance\n" in content, (
        "docs/compatibility-matrix.md must contain '## Version Change Guidance' section (AC 1)"
    )


def test_supported_version_baseline_section_present() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "## Supported Version Baseline\n" in content, (
        "docs/compatibility-matrix.md must contain '## Supported Version Baseline' section (AC 1)"
    )


def test_binding_compatibility_check_section_present() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "## Binding Compatibility Check\n" in content, (
        "docs/compatibility-matrix.md must contain '## Binding Compatibility Check' section"
    )


# ---------------------------------------------------------------------------
# 4.3 Support policy content tests (AC: 2)
# ---------------------------------------------------------------------------

def test_support_policy_contains_supported_status() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Support Policy")
    assert "Supported" in section, (
        "'## Support Policy' section must contain 'Supported' status value (AC 2)"
    )


def test_support_policy_contains_experimental_status() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Support Policy")
    assert "Experimental" in section, (
        "'## Support Policy' section must contain 'Experimental' status value (AC 2)"
    )


def test_support_policy_contains_deferred_status() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Support Policy")
    assert "Deferred" in section, (
        "'## Support Policy' section must contain 'Deferred' status value (AC 2)"
    )


def test_support_policy_contains_out_of_scope_status() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Support Policy")
    assert "Out-of-Scope" in section, (
        "'## Support Policy' section must contain 'Out-of-Scope' status value (AC 2)"
    )


# ---------------------------------------------------------------------------
# 4.4 Out-of-scope documentation test (AC: 2)
# ---------------------------------------------------------------------------

def test_web_export_listed_as_out_of_scope() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "web export" in content.lower(), (
        "docs/compatibility-matrix.md must contain 'web export' as an explicit out-of-scope entry (AC 2)"
    )


def test_web_export_row_has_out_of_scope_status() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "Out-of-Scope" in content, (
        "docs/compatibility-matrix.md must contain 'Out-of-Scope' in the version baseline table (AC 2)"
    )


# ---------------------------------------------------------------------------
# 4.5 Version baseline content tests (AC: 1)
# ---------------------------------------------------------------------------

def test_version_baseline_contains_godot_version() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Supported Version Baseline")
    assert "4.6.2" in section, (
        "'## Supported Version Baseline' must contain Godot version '4.6.2' (AC 1)"
    )


def test_version_baseline_contains_spacetimedb_version() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Supported Version Baseline")
    assert "2.1+" in section, (
        "'## Supported Version Baseline' must contain SpacetimeDB version '2.1+' (AC 1)"
    )


def test_version_baseline_contains_client_sdk_reference() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Supported Version Baseline")
    assert "SpacetimeDB.ClientSDK" in section, (
        "'## Supported Version Baseline' must contain 'SpacetimeDB.ClientSDK' (AC 1)"
    )


def test_version_baseline_contains_godot_net_sdk_reference() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Supported Version Baseline")
    assert "Godot.NET.Sdk" in section, (
        "'## Supported Version Baseline' must contain 'Godot.NET.Sdk' (AC 1)"
    )


def test_supported_version_baseline_rows_match_canonical_status_table() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Supported Version Baseline")
    for row in (
        "| Godot editor/runtime target | `4.6.2` | Supported |",
        "| Godot .NET build SDK | `Godot.NET.Sdk` `4.6.1` | Supported |",
        "| `.NET` SDK | `8.0+` | Supported |",
        "| SpacetimeDB server and CLI | `2.1+` | Supported |",
        "| `SpacetimeDB.ClientSDK` | `2.1.0` | Supported |",
        "| Godot C# web export | N/A | Out-of-Scope |",
    ):
        assert row in section, (
            f"'## Supported Version Baseline' must contain canonical row {row!r} (AC 1, 2)"
        )


# ---------------------------------------------------------------------------
# 4.6 Triage timeline test (AC: 1)
# ---------------------------------------------------------------------------

def test_triage_timeline_contains_14_days_sla() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Compatibility Triage Timeline")
    assert "14 days" in section, (
        "'## Compatibility Triage Timeline' must contain '14 days' upstream triage SLA (AC 1)"
    )


# ---------------------------------------------------------------------------
# 4.7 Adopter-facing test (AC: 3)
# ---------------------------------------------------------------------------

def test_no_internal_story_reference_in_opening() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "Story `1.1`" not in content[:500], (
        "Opening of docs/compatibility-matrix.md must NOT contain 'Story `1.1`' internal-story reference (AC 3)"
    )


# ---------------------------------------------------------------------------
# 4.8 Canonical reference test (AC: 3)
# ---------------------------------------------------------------------------

def test_canonical_reference_includes_install_md() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "docs/install.md" in content, (
        "docs/compatibility-matrix.md must reference 'docs/install.md' in canonical reference statement (AC 3)"
    )


def test_canonical_reference_includes_quickstart_md() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "docs/quickstart.md" in content, (
        "docs/compatibility-matrix.md must reference 'docs/quickstart.md' in canonical reference statement (AC 3)"
    )


def test_canonical_reference_includes_troubleshooting_md() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "docs/troubleshooting.md" in content, (
        "docs/compatibility-matrix.md must reference 'docs/troubleshooting.md' in canonical reference statement (AC 3)"
    )


def test_canonical_reference_includes_migration_md() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "docs/migration-from-community-plugin.md" in content, (
        "docs/compatibility-matrix.md must reference 'docs/migration-from-community-plugin.md' in canonical reference statement (AC 3)"
    )


# ---------------------------------------------------------------------------
# 4.9 ITokenStore externalization test (C3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_itoken_store_section_contains_internal_sealed() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "internal sealed" in content, (
        "docs/runtime-boundaries.md must contain 'internal sealed' in the auth section "
        "to clarify ProjectSettingsTokenStore externalization boundary (C3)"
    )


def test_runtime_boundaries_itoken_store_externalization_sentence_present() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "GodotSpacetime.Auth.ITokenStore" in content, (
        "docs/runtime-boundaries.md must contain the ITokenStore externalization guidance sentence (C3)"
    )


# ---------------------------------------------------------------------------
# 4.10 AuthRequired enum removal test (D1)
# ---------------------------------------------------------------------------

def test_auth_required_removed_from_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "AuthRequired" not in content, (
        "AuthRequired is dead code and must be removed from ConnectionAuthState enum (D1/C1 from Epic 5 retro)"
    )


# ---------------------------------------------------------------------------
# 4.11 Docs AuthRequired removal test (D1)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_no_auth_required_table_row() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "| `AuthRequired` |" not in content, (
        "AuthRequired must be removed from the ConnectionAuthState table in runtime-boundaries.md (D1)"
    )


def test_support_baseline_line_checks_match_canonical_status_table() -> None:
    baseline = json.loads(_read("scripts/compatibility/support-baseline.json"))
    entries = {
        entry["label"]: entry["expected_line"]
        for entry in baseline.get("line_checks", [])
        if entry.get("file") == "docs/compatibility-matrix.md"
    }
    expected_rows = {
        "Godot editor/runtime target": "| Godot editor/runtime target | `4.6.2` | Supported |",
        "Godot .NET build SDK": "| Godot .NET build SDK | `Godot.NET.Sdk` `4.6.1` | Supported |",
        ".NET SDK": "| `.NET` SDK | `8.0+` | Supported |",
        "SpacetimeDB server and CLI": "| SpacetimeDB server and CLI | `2.1+` | Supported |",
        "SpacetimeDB.ClientSDK": "| `SpacetimeDB.ClientSDK` | `2.1.0` | Supported |",
        "Godot C# web export": "| Godot C# web export | N/A | Out-of-Scope |",
    }
    for label, row in expected_rows.items():
        assert entries.get(label) == row, (
            "scripts/compatibility/support-baseline.json must keep compatibility-matrix line checks "
            f"in sync with the canonical status table for {label!r}"
        )


def test_binding_compatibility_check_section_preserved_verbatim() -> None:
    content = _read("docs/compatibility-matrix.md")
    expected = """The Compatibility panel in the Godot editor reads the CLI version comment embedded in generated bindings and compares it against the declared `spacetimedb` baseline. Generated files contain that comment near the top of the file, after the generated-file warning banner, in the form:

```
// This was generated using spacetimedb cli version X.Y.Z (commit ...)
```

The panel extracts the version token and checks that it satisfies the declared baseline (e.g. `2.1+` requires CLI `>= 2.1`). The validation workflow also compares the latest relevant module-source file under `spacetime/modules/smoke_test/` against the generated binding set under `demo/generated/smoke_test/`, using the newest generated `*.g.cs` artifact as the freshness watermark so schema-only table changes still validate correctly and stale bindings fail before runtime use. If either check fails, the tooling reports the exact failed check together with the regeneration command.

To resolve an INCOMPATIBLE state, run:

```bash
bash scripts/codegen/generate-smoke-test.sh
```

Story `1.8` implements this check. Stories `1.9` and `1.10` extend the quickstart to validate both binding compatibility and connection state before declaring the setup complete."""
    assert _section(content, "Binding Compatibility Check") == expected, (
        "'## Binding Compatibility Check' must remain exactly unchanged by Story 6.1 (Task 1.8)"
    )


# ---------------------------------------------------------------------------
# 4.12 Regression guards — all prior story deliverables must remain intact
# ---------------------------------------------------------------------------

def test_install_md_exists() -> None:
    assert (ROOT / "docs" / "install.md").exists(), "docs/install.md must exist (regression guard)"


def test_quickstart_md_exists() -> None:
    assert (ROOT / "docs" / "quickstart.md").exists(), "docs/quickstart.md must exist (regression guard)"


def test_codegen_md_exists() -> None:
    assert (ROOT / "docs" / "codegen.md").exists(), "docs/codegen.md must exist (regression guard)"


def test_connection_md_exists() -> None:
    assert (ROOT / "docs" / "connection.md").exists(), "docs/connection.md must exist (regression guard)"


def test_runtime_boundaries_md_exists() -> None:
    assert (ROOT / "docs" / "runtime-boundaries.md").exists(), (
        "docs/runtime-boundaries.md must exist (regression guard)"
    )


def test_compatibility_matrix_md_exists() -> None:
    assert (ROOT / "docs" / "compatibility-matrix.md").exists(), (
        "docs/compatibility-matrix.md must exist (regression guard)"
    )


def test_troubleshooting_md_exists() -> None:
    assert (ROOT / "docs" / "troubleshooting.md").exists(), (
        "docs/troubleshooting.md must exist (regression guard)"
    )


def test_migration_from_community_plugin_md_exists() -> None:
    assert (ROOT / "docs" / "migration-from-community-plugin.md").exists(), (
        "docs/migration-from-community-plugin.md must exist (regression guard)"
    )


def test_demo_readme_exists() -> None:
    assert (ROOT / "demo" / "README.md").exists(), "demo/README.md must exist (regression guard)"


def test_demo_main_cs_exists() -> None:
    assert (ROOT / "demo" / "DemoMain.cs").exists(), "demo/DemoMain.cs must exist (regression guard)"


def test_spacetime_client_cs_exists() -> None:
    assert (ROOT / "addons" / "godot_spacetime" / "src" / "Public" / "SpacetimeClient.cs").exists(), (
        "addons/godot_spacetime/src/Public/SpacetimeClient.cs must exist (regression guard)"
    )


def test_compatibility_matrix_godot_version_baseline_intact() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "4.6.2" in content, (
        "docs/compatibility-matrix.md must contain '4.6.2' — version baseline intact (regression guard)"
    )


def test_compatibility_matrix_sdk_dependency_intact() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "SpacetimeDB.ClientSDK" in content, (
        "docs/compatibility-matrix.md must contain 'SpacetimeDB.ClientSDK' — SDK dependency intact (regression guard)"
    )


def test_runtime_boundaries_connection_state_intact() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionState" in content, (
        "docs/runtime-boundaries.md must contain 'ConnectionState' — connection lifecycle terminology intact (regression guard)"
    )


def test_runtime_boundaries_itoken_store_intact() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ITokenStore" in content, (
        "docs/runtime-boundaries.md must contain 'ITokenStore' — auth interface intact (regression guard)"
    )


def test_runtime_boundaries_reducer_call_failed_intact() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallFailed" in content, (
        "docs/runtime-boundaries.md must contain 'ReducerCallFailed' — reducer error model intact (regression guard)"
    )


def test_troubleshooting_token_expired_intact() -> None:
    content = _read("docs/troubleshooting.md")
    assert "TokenExpired" in content, (
        "docs/troubleshooting.md must contain 'TokenExpired' — Story 5.5 intact (regression guard)"
    )


def test_migration_db_connection_builder_intact() -> None:
    content = _read("docs/migration-from-community-plugin.md")
    assert "DbConnection.Builder()" in content, (
        "docs/migration-from-community-plugin.md must contain 'DbConnection.Builder()' — Story 5.6 intact (regression guard)"
    )


def test_demo_readme_reducer_interaction_intact() -> None:
    content = _read("demo/README.md")
    assert "Reducer Interaction" in content, (
        "demo/README.md must contain 'Reducer Interaction' — Story 5.3 intact (regression guard)"
    )


def test_demo_main_reducer_call_succeeded_intact() -> None:
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallSucceeded" in content, (
        "demo/DemoMain.cs must contain 'ReducerCallSucceeded' — Story 5.3 wiring intact (regression guard)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — AC 1 version baseline completeness
# ---------------------------------------------------------------------------

def test_version_baseline_contains_dot_net_version() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Supported Version Baseline")
    assert "8.0+" in section, (
        "'## Supported Version Baseline' must contain .NET SDK version '8.0+' (AC 1)"
    )


def test_version_baseline_contains_godot_net_sdk_version_number() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Supported Version Baseline")
    assert "4.6.1" in section, (
        "'## Supported Version Baseline' must contain Godot.NET.Sdk version '4.6.1' (AC 1)"
    )


def test_version_baseline_contains_client_sdk_version_number() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Supported Version Baseline")
    assert "2.1.0" in section, (
        "'## Supported Version Baseline' must contain SpacetimeDB.ClientSDK version '2.1.0' (AC 1)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — document structure and title (AC 3)
# ---------------------------------------------------------------------------

def test_compatibility_matrix_has_adopter_facing_title() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert content.startswith("# Compatibility Matrix and Support Policy"), (
        "docs/compatibility-matrix.md must open with '# Compatibility Matrix and Support Policy' — "
        "confirms adopter-facing rewrite; internal title removed (AC 3)"
    )


def test_scope_of_this_matrix_section_present() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "## Scope of This Matrix\n" in content, (
        "docs/compatibility-matrix.md must contain '## Scope of This Matrix' section"
    )


# ---------------------------------------------------------------------------
# Gap coverage — canonical references in opening paragraph (AC 3)
# ---------------------------------------------------------------------------

def test_canonical_references_appear_before_first_section_heading() -> None:
    content = _read("docs/compatibility-matrix.md")
    first_heading_pos = content.find("\n## ")
    assert first_heading_pos != -1, "compatibility-matrix.md must have at least one ## section"
    opening = content[:first_heading_pos]
    for ref in (
        "docs/install.md",
        "docs/quickstart.md",
        "docs/troubleshooting.md",
        "docs/migration-from-community-plugin.md",
    ):
        assert ref in opening, (
            f"Canonical reference '{ref}' must appear in the opening paragraph before the first "
            f"'## ' section heading, not in a later section (AC 3)"
        )


# ---------------------------------------------------------------------------
# Gap coverage — full-document Story 1.1 reference removal (AC 3)
# ---------------------------------------------------------------------------

def test_no_story_1_1_reference_anywhere_in_document() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "Story `1.1`" not in content, (
        "docs/compatibility-matrix.md must NOT contain 'Story `1.1`' anywhere in the document — "
        "internal-story language fully removed (AC 3)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — AuthRequired enum reference removed from ConnectionAuthStatusPanel (D1)
# ---------------------------------------------------------------------------

def test_connection_auth_status_panel_no_auth_required_enum_reference() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "ConnectionAuthState.AuthRequired" not in content, (
        "ConnectionAuthStatusPanel.cs must not reference ConnectionAuthState.AuthRequired — "
        "the enum switch arm must be removed along with the dead enum value (D1/C1)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — C3 ITokenStore externalization sentence precision
# ---------------------------------------------------------------------------

def test_runtime_boundaries_externalization_sentence_names_project_settings_token_store() -> None:
    content = _read("docs/runtime-boundaries.md")
    # Locate the externalization sentence in the ITokenStore section
    pos = content.find("ProjectSettingsTokenStore` is `internal sealed`")
    assert pos != -1, (
        "docs/runtime-boundaries.md must contain the phrase "
        "'ProjectSettingsTokenStore` is `internal sealed`' — "
        "confirms the exact externalization sentence was added (C3)"
    )


def test_runtime_boundaries_externalization_sentence_states_cannot_be_instantiated() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "cannot be instantiated from outside the SDK" in content, (
        "docs/runtime-boundaries.md externalization sentence must state "
        "'cannot be instantiated from outside the SDK' (C3)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — Version Change Guidance references validate-foundation.py (AC 1)
# ---------------------------------------------------------------------------

def test_version_change_guidance_references_validate_foundation_script() -> None:
    content = _read("docs/compatibility-matrix.md")
    section = _section(content, "Version Change Guidance")
    assert "validate-foundation.py" in section, (
        "'## Version Change Guidance' must reference 'validate-foundation.py' so adopters "
        "can run it to identify failing checks (AC 1)"
    )
