"""
Story 10.2: Generate Bindings from the Godot Editor via Server Schema Fetch

Static contract coverage for the editor-side schema fetch service, interactive
codegen panel additions, output safety guardrails, and documentation updates.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE_REL = "addons/godot_spacetime/src/Editor/Codegen/EditorCodegenService.cs"
RESULT_REL = "addons/godot_spacetime/src/Editor/Codegen/EditorCodegenResult.cs"
PANEL_REL = "addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _code_text(rel: str) -> str:
    lines: list[str] = []
    for line in _read(rel).splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("///"):
            continue
        lines.append(line)
    return "\n".join(lines)


def test_story_10_2_required_editor_codegen_files_exist() -> None:
    required = [
        SERVICE_REL,
        RESULT_REL,
        PANEL_REL,
        "tests/test_story_10_2_editor_codegen_integration.py",
        "docs/codegen.md",
        "docs/troubleshooting.md",
    ]
    for rel in required:
        assert (ROOT / rel).is_file(), (
            f"{rel} must exist for Story 10.2's editor-fetch codegen surface."
        )


def test_editor_codegen_service_declares_async_fetch_and_pipeline_surface() -> None:
    content = _read(SERVICE_REL)

    for expected in (
        "#if TOOLS",
        "internal sealed class EditorCodegenService",
        "GenerateBindingsAsync(",
        "FetchSchemaArtifactAsync(",
        "SendAnonymousGetAsync(",
        "spacetime",
        "--bin-path",
        "detect-godot-types.py",
    ):
        assert expected in content, (
            "EditorCodegenService must own the editor-only HTTP fetch + "
            f"codegen pipeline. Missing {expected!r}."
        )


def test_editor_codegen_result_is_a_value_type_with_required_fields() -> None:
    content = _read(RESULT_REL)
    for expected in (
        "record struct EditorCodegenResult",
        "bool IsSuccess",
        "string StatusMessage",
        "string? ErrorDetail",
    ):
        assert expected in content, (
            "EditorCodegenResult must remain the value-type contract used by "
            f"the panel. Missing {expected!r}."
        )


def test_codegen_panel_has_interactive_generation_controls() -> None:
    content = _read(PANEL_REL)
    for expected in (
        "_serverUrlEdit",
        "_moduleNameEdit",
        "_outputDirEdit",
        "_namespaceEdit",
        "_generateButton",
        "_generateStatusLabel",
        "_generateRecoveryLabel",
        '"Generate from Server"',
        '"Fetch & Generate"',
    ):
        assert expected in content, (
            "CodegenValidationPanel must extend the existing read-only panel "
            f"with the interactive generation UI. Missing {expected!r}."
        )


def test_codegen_panel_prepopulates_from_spacetimesettings() -> None:
    content = _read(PANEL_REL)
    for expected in (
        "SpacetimeSettings",
        "Host",
        "Database",
        "GeneratedBindingsNamespace",
        "ResolveGeneratedBindingsNamespace",
        "FindSpacetimeSettings",
    ):
        assert expected in content, (
            "CodegenValidationPanel must pre-populate server/module/namespace "
            f"fields from SpacetimeSettings. Missing {expected!r}."
        )


def test_editor_codegen_output_safety_guardrails_are_present() -> None:
    content = _read(SERVICE_REL)
    for expected in (
        "BLOCKED — output directory outside safe boundary",
        "generated",
        '"addons"',
        '"src"',
        '"tests"',
        '"docs"',
        '"scripts"',
        '".github"',
        '"demo", "generated"',
        '"tests", "fixtures", "generated"',
    ):
        assert expected in content, (
            "EditorCodegenService must keep codegen writes inside safe generated "
            f"boundaries. Missing {expected!r}."
        )


def test_docs_cover_editor_based_codegen_workflow() -> None:
    codegen = _read("docs/codegen.md")
    troubleshooting = _read("docs/troubleshooting.md")

    assert "## Editor-Based Codegen (Fetch from Server)" in codegen, (
        "docs/codegen.md must document the new editor-based codegen workflow."
    )
    for expected in (
        "SpacetimeSettings.Host",
        "SpacetimeSettings.Database",
        "GeneratedBindingsNamespace",
        "--bin-path",
        "anonymous",
        "generated boundary",
    ):
        assert expected in codegen, (
            f"docs/codegen.md must document {expected!r} for Story 10.2."
        )

    for expected in (
        "FAILED — could not reach server",
        "FAILED — server requires authentication",
        "BLOCKED — output directory outside safe boundary",
        "FAILED — spacetime CLI not found in PATH",
        "python3",
    ):
        assert expected in troubleshooting, (
            f"docs/troubleshooting.md must cover {expected!r} for Story 10.2."
        )


def test_editor_codegen_sources_do_not_leak_raw_spacetimedb_runtime_types() -> None:
    for rel in (SERVICE_REL, PANEL_REL):
        code_text = _code_text(rel)
        for forbidden in (
            "using SpacetimeDB;",
            "DbConnection",
            "RemoteTables",
            "IRemoteTableHandle",
        ):
            assert forbidden not in code_text, (
                "Story 10.2 editor-only sources must stay clear of raw runtime "
                f"types. Found {forbidden!r} in {rel}."
            )


def test_existing_codegen_panel_regression_tokens_remain_intact() -> None:
    content = _read(PANEL_REL)
    for expected in (
        "StatusOk",
        "StatusMissing",
        "StatusNotConfigured",
        "RecoveryCommand",
        "RelativeModuleSource",
        "RelativeOutputPath",
    ):
        assert expected in content, (
            "Story 10.2 must extend the existing codegen panel instead of "
            f"replacing its baseline behavior. Missing {expected!r}."
        )
