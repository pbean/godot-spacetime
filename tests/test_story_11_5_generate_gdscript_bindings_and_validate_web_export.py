"""
Story 11.5: Generate GDScript bindings and validate web export

Static contract coverage for the repo-owned GDScript emitter, generated fixture
layout, browser proof-path assets, and the documentation/support-policy updates.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "codegen" / "generate-gdscript-bindings.py"
SMOKE_SCRIPT_PATH = ROOT / "scripts" / "codegen" / "generate-gdscript-smoke-test.sh"
WEB_EXPORT_HELPER_PATH = ROOT / "tests" / "fixtures" / "gdscript_web_export.py"
WEB_EXPORT_RUNNER_PATH = ROOT / "tests" / "godot_integration" / "gdscript_web_export_runner.gd"
WEB_EXPORT_SCENE_PATH = ROOT / "tests" / "godot_integration" / "gdscript_web_export_runner.tscn"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "gdscript_generated" / "smoke_test"
CODEGEN_DOCS = ROOT / "docs" / "codegen.md"
TROUBLESHOOTING_DOCS = ROOT / "docs" / "troubleshooting.md"
COMPATIBILITY_DOCS = ROOT / "docs" / "compatibility-matrix.md"
STORY_11_3_STATIC_TEST = (
    ROOT / "tests" / "test_story_11_3_implement_gdscript_subscription_cache_and_row_event_system.py"
)
STORY_11_4_STATIC_TEST = (
    ROOT / "tests" / "test_story_11_4_implement_gdscript_reducer_invocation_and_result_handling.py"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_story_11_5_required_story_files_exist() -> None:
    required = [
        GENERATOR_PATH,
        SMOKE_SCRIPT_PATH,
        WEB_EXPORT_HELPER_PATH,
        WEB_EXPORT_RUNNER_PATH,
        WEB_EXPORT_SCENE_PATH,
        ROOT / "tests" / "test_story_11_5_gdscript_codegen_integration.py",
        ROOT / "tests" / "test_story_11_5_gdscript_web_export_integration.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    assert not missing, (
        "Story 11.5 must add the repo-owned GDScript codegen and browser proof-path surfaces. "
        f"Missing {missing}"
    )


def test_story_11_5_generated_fixture_layout_exists() -> None:
    required = [
        FIXTURE_DIR / "README.md",
        FIXTURE_DIR / "remote_tables.gd",
        FIXTURE_DIR / "remote_reducers.gd",
        FIXTURE_DIR / "spacetimedb_client.gd",
        FIXTURE_DIR / "Tables" / "smoke_test_table.gd",
        FIXTURE_DIR / "Tables" / "typed_entity_table.gd",
        FIXTURE_DIR / "Types" / "smoke_test.gd",
        FIXTURE_DIR / "Types" / "typed_entity.gd",
        FIXTURE_DIR / "Types" / "vec2f.gd",
        FIXTURE_DIR / "Types" / "entity_quat.gd",
        FIXTURE_DIR / "Types" / "rgba_color.gd",
        FIXTURE_DIR / "Types" / "vec3i.gd",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    assert not missing, (
        "Story 11.5 must replace the hand-authored smoke fixture with generated module artifacts. "
        f"Missing {missing}"
    )


def test_story_11_5_generated_fixture_files_have_banner_and_regen_command() -> None:
    generated_files = sorted(path for path in FIXTURE_DIR.rglob("*.gd"))
    assert generated_files, "Story 11.5 fixture tree must contain generated .gd files."
    for path in generated_files:
        content = _read(path)
        assert "AUTOMATICALLY GENERATED" in content, (
            f"{path.relative_to(ROOT)} must carry a generated-file banner."
        )
        assert "WILL NOT BE SAVED" in content, (
            f"{path.relative_to(ROOT)} must warn that manual edits are not preserved."
        )
        assert "bash scripts/codegen/generate-gdscript-smoke-test.sh" in content, (
            f"{path.relative_to(ROOT)} must embed the canonical regeneration command."
        )


def test_story_11_5_fixture_readme_documents_read_only_regeneration() -> None:
    content = _read(FIXTURE_DIR / "README.md")
    for expected in (
        "read-only",
        "bash scripts/codegen/generate-gdscript-smoke-test.sh",
        "tests/fixtures/gdscript_generated/smoke_test/",
        "pinned upstream CLI does not directly emit GDScript bindings",
        "scripts/codegen/generate-gdscript-bindings.py",
    ):
        assert expected in content, (
            "Story 11.5 fixture README must document the GDScript regeneration path and read-only status. "
            f"Missing {expected!r}."
        )


def test_story_11_5_generator_script_contract_strings_present() -> None:
    content = _read(GENERATOR_PATH)
    for expected in (
        "--csharp-bindings-dir",
        "--out-dir",
        "detect-godot-types.py",
        "remote_tables.gd",
        "remote_reducers.gd",
        "spacetimedb_client.gd",
        "get_table_contracts",
        "invoke_reducer",
    ):
        assert expected in content, (
            "generate-gdscript-bindings.py must expose the Story 11.5 generator contract. "
            f"Missing {expected!r}."
        )


def test_story_11_5_smoke_regeneration_script_drives_csharp_frontend_then_emitter() -> None:
    content = _read(SMOKE_SCRIPT_PATH)
    for expected in (
        "spacetime generate",
        "--lang csharp",
        "generate-gdscript-bindings.py",
        "tests/fixtures/gdscript_generated/smoke_test",
    ):
        assert expected in content, (
            "generate-gdscript-smoke-test.sh must run the official C# frontend first and then the repo-owned GDScript emitter. "
            f"Missing {expected!r}."
        )


def test_story_11_5_docs_cover_supported_gdscript_codegen_and_web_export_path() -> None:
    codegen = _read(CODEGEN_DOCS)
    troubleshooting = _read(TROUBLESHOOTING_DOCS)
    compatibility = _read(COMPATIBILITY_DOCS)

    for expected in (
        "generate-gdscript-smoke-test.sh",
        "tests/fixtures/gdscript_generated/smoke_test/",
        "There is no upstream `gdscript` target in the pinned CLI",
        "generate-gdscript-bindings.py",
    ):
        assert expected in codegen, (
            f"docs/codegen.md must document Story 11.5's GDScript workflow. Missing {expected!r}."
        )

    for expected in (
        "file://",
        "Compatibility",
        "query-token",
        "browser",
        "export template",
    ):
        assert expected in troubleshooting, (
            f"docs/troubleshooting.md must cover Story 11.5 browser/export failure modes. Missing {expected!r}."
        )

    for expected in (
        "| Native GDScript web export | `4.6.2` | Supported |",
        "| Godot C# web export | N/A | Out-of-Scope |",
    ):
        assert expected in compatibility, (
            "docs/compatibility-matrix.md must distinguish supported native GDScript web export from out-of-scope Godot C# web export. "
            f"Missing {expected!r}."
        )


def test_story_11_5_legacy_story_tests_assert_generated_fixture_surface() -> None:
    for path in (STORY_11_3_STATIC_TEST, STORY_11_4_STATIC_TEST):
        content = _read(path)
        for expected in (
            "README.md",
            "remote_reducers.gd",
            "spacetimedb_client.gd",
            "Tables",
            "generated",
        ):
            assert expected in content, (
                f"{path.name} must be tightened to validate the generated Story 11.5 fixture surface. "
                f"Missing {expected!r}."
            )
