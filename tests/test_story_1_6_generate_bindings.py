"""
Story 1.6: Generate and Regenerate Typed Module Bindings
Automated contract tests for all story deliverables.

Covers:
- Smoke test module source structure (Cargo.toml, src/lib.rs)
- Codegen script existence and content
- Committed generated C# bindings in demo/generated/smoke_test/
- docs/codegen.md updated with the actual generation workflow
- Regression guards: story 1.2 reserved paths still present
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# Module source
# ---------------------------------------------------------------------------

def test_smoke_test_cargo_toml_exists() -> None:
    assert (ROOT / "spacetime/modules/smoke_test/Cargo.toml").is_file(), (
        "spacetime/modules/smoke_test/Cargo.toml is missing"
    )


def test_smoke_test_cargo_toml_is_cdylib() -> None:
    content = _read("spacetime/modules/smoke_test/Cargo.toml")
    assert 'crate-type = ["cdylib"]' in content, (
        'Cargo.toml must contain crate-type = ["cdylib"] for SpacetimeDB WASM compilation'
    )


def test_smoke_test_lib_rs_exists() -> None:
    assert (ROOT / "spacetime/modules/smoke_test/src/lib.rs").is_file(), (
        "spacetime/modules/smoke_test/src/lib.rs is missing"
    )


def test_smoke_test_lib_rs_defines_smoke_test_table() -> None:
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "smoke_test" in content, (
        "lib.rs must define a table named smoke_test"
    )


def test_smoke_test_lib_rs_defines_ping_reducer() -> None:
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "ping" in content, (
        "lib.rs must define a reducer named ping"
    )


# ---------------------------------------------------------------------------
# Codegen script
# ---------------------------------------------------------------------------

def test_codegen_script_exists() -> None:
    assert (ROOT / "scripts/codegen/generate-smoke-test.sh").is_file(), (
        "scripts/codegen/generate-smoke-test.sh is missing"
    )


def test_codegen_script_calls_spacetime_generate() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "spacetime generate" in content, (
        "generate-smoke-test.sh must invoke 'spacetime generate'"
    )


def test_codegen_script_targets_csharp() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "--lang csharp" in content, (
        "generate-smoke-test.sh must pass '--lang csharp' to spacetime generate"
    )


def test_codegen_script_targets_smoke_test_module() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "smoke_test" in content, (
        "generate-smoke-test.sh must reference the smoke_test module path"
    )


def test_codegen_script_targets_demo_generated_output() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "demo/generated/smoke_test" in content, (
        "generate-smoke-test.sh must reference 'demo/generated/smoke_test' as output path"
    )


# ---------------------------------------------------------------------------
# Generated bindings
# ---------------------------------------------------------------------------

def test_generated_smoke_test_dir_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test").is_dir(), (
        "demo/generated/smoke_test/ directory is missing — run scripts/codegen/generate-smoke-test.sh"
    )


def test_generated_smoke_test_contains_cs_files() -> None:
    cs_files = list((ROOT / "demo/generated/smoke_test").rglob("*.cs"))
    assert len(cs_files) > 0, (
        "demo/generated/smoke_test/ must contain at least one .cs file — "
        "run scripts/codegen/generate-smoke-test.sh and commit the output"
    )


# ---------------------------------------------------------------------------
# docs/codegen.md
# ---------------------------------------------------------------------------

def test_codegen_doc_references_generation_script() -> None:
    content = _read("docs/codegen.md")
    assert "generate-smoke-test.sh" in content, (
        "docs/codegen.md must reference generate-smoke-test.sh"
    )


def test_codegen_doc_references_demo_generated_output() -> None:
    content = _read("docs/codegen.md")
    assert "demo/generated/smoke_test" in content, (
        "docs/codegen.md must reference demo/generated/smoke_test"
    )


# ---------------------------------------------------------------------------
# Regression guards
# ---------------------------------------------------------------------------

def test_docs_codegen_md_still_exists() -> None:
    assert (ROOT / "docs/codegen.md").is_file(), (
        "docs/codegen.md is missing (regression from story 1.2)"
    )


def test_smoke_test_module_dir_still_exists() -> None:
    assert (ROOT / "spacetime/modules/smoke_test").is_dir(), (
        "spacetime/modules/smoke_test/ is missing (regression from story 1.2)"
    )


def test_fixtures_generated_dir_still_exists() -> None:
    assert (ROOT / "tests/fixtures/generated").is_dir(), (
        "tests/fixtures/generated/ is missing (regression from story 1.2)"
    )


# ---------------------------------------------------------------------------
# Module source field contract (cascade into generated C# column names)
# ---------------------------------------------------------------------------

def test_smoke_test_lib_rs_defines_id_field() -> None:
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "pub id" in content or "id:" in content, (
        "lib.rs must define an 'id' field — this becomes the C# Id column used by Stories 1.7+"
    )


def test_smoke_test_lib_rs_defines_value_field() -> None:
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "pub value" in content or "value:" in content, (
        "lib.rs must define a 'value' field — this becomes the C# Value column used by Stories 1.7+"
    )


def test_smoke_test_cargo_toml_has_spacetimedb_dependency() -> None:
    content = _read("spacetime/modules/smoke_test/Cargo.toml")
    assert "spacetimedb" in content, (
        "Cargo.toml must declare a spacetimedb dependency for the module to compile"
    )


def test_smoke_test_cargo_toml_pins_exact_spacetimedb_version() -> None:
    content = _read("spacetime/modules/smoke_test/Cargo.toml")
    assert 'spacetimedb = "=1.12.0"' in content, (
        "Cargo.toml must pin the exact spacetimedb crate version used for the Story 1.6 baseline"
    )


# ---------------------------------------------------------------------------
# Codegen script safety contract (AC3: must exit non-zero on failure)
# ---------------------------------------------------------------------------

def test_codegen_script_has_strict_error_mode() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "set -euo pipefail" in content, (
        "generate-smoke-test.sh must use 'set -euo pipefail' to satisfy AC3 (exits non-zero on failure)"
    )


def test_codegen_script_recreates_generated_readme() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "README.md" in content and "Generated Bindings — smoke_test module" in content, (
        "generate-smoke-test.sh must recreate demo/generated/smoke_test/README.md after clearing the output directory"
    )


def test_codegen_script_uses_temp_cargo_target_dir() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "CARGO_TARGET_DIR" in content and "mktemp -d" in content, (
        "generate-smoke-test.sh must keep Cargo target output outside the repo so regeneration does not leave target/ behind"
    )


def test_codegen_script_cleans_up_module_cargo_lock() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "Cargo.lock" in content and "rm -f" in content, (
        "generate-smoke-test.sh must clean up the smoke_test module Cargo.lock so regeneration does not leave repo-noise behind"
    )


# ---------------------------------------------------------------------------
# Generated file structure (specific files referenced by Stories 1.7 and 1.9)
# ---------------------------------------------------------------------------

def test_generated_types_smoke_test_file_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Types/SmokeTest.g.cs").is_file(), (
        "demo/generated/smoke_test/Types/SmokeTest.g.cs is missing — "
        "this file is referenced by Story 1.7 for type documentation"
    )


def test_generated_reducers_ping_file_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Reducers/Ping.g.cs").is_file(), (
        "demo/generated/smoke_test/Reducers/Ping.g.cs is missing — "
        "this file is referenced by Story 1.7 and required for Story 1.9 runtime use"
    )


def test_generated_tables_smoke_test_file_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Tables/SmokeTest.g.cs").is_file(), (
        "demo/generated/smoke_test/Tables/SmokeTest.g.cs is missing"
    )


def test_generated_spacetimedb_client_file_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/SpacetimeDBClient.g.cs").is_file(), (
        "demo/generated/smoke_test/SpacetimeDBClient.g.cs is missing — "
        "this is the aggregate binding registry required for Story 1.9 connection setup"
    )


# ---------------------------------------------------------------------------
# Generated type and reducer names (stable contract for Stories 1.7, 1.9)
# ---------------------------------------------------------------------------

def test_generated_types_contains_smoke_test_class() -> None:
    content = _read("demo/generated/smoke_test/Types/SmokeTest.g.cs")
    assert "class SmokeTest" in content, (
        "Types/SmokeTest.g.cs must define 'class SmokeTest' — Stories 1.7 and 1.9 reference this type"
    )


def test_generated_reducers_contains_ping_method() -> None:
    content = _read("demo/generated/smoke_test/Reducers/Ping.g.cs")
    assert "Ping" in content, (
        "Reducers/Ping.g.cs must contain 'Ping' — Story 1.9 invokes this reducer by name"
    )


def test_generated_files_have_autogen_banner() -> None:
    content = _read("demo/generated/smoke_test/SpacetimeDBClient.g.cs")
    assert "THIS FILE IS AUTOMATICALLY GENERATED BY SPACETIMEDB" in content, (
        "SpacetimeDBClient.g.cs is missing the auto-generated banner — "
        "generated files must never be hand-edited"
    )


# ---------------------------------------------------------------------------
# demo/generated/smoke_test/README.md (required deliverable from Task 3)
# ---------------------------------------------------------------------------

def test_demo_generated_readme_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/README.md").is_file(), (
        "demo/generated/smoke_test/README.md is missing — "
        "required deliverable from Task 3 (auto-generated artifact notice)"
    )


def test_demo_generated_readme_mentions_script() -> None:
    content = _read("demo/generated/smoke_test/README.md")
    assert "generate-smoke-test.sh" in content, (
        "demo/generated/smoke_test/README.md must reference generate-smoke-test.sh"
    )


# ---------------------------------------------------------------------------
# support-baseline.json — Task 5 new entries
# ---------------------------------------------------------------------------

def test_support_baseline_has_codegen_script_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "scripts/codegen/generate-smoke-test.sh" in content, (
        "support-baseline.json must include 'scripts/codegen/generate-smoke-test.sh' in required_paths"
    )


def test_support_baseline_has_demo_generated_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "demo/generated/smoke_test" in content, (
        "support-baseline.json must include 'demo/generated/smoke_test' in required_paths"
    )


def test_support_baseline_has_codegen_script_line_check() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "bash scripts/codegen/generate-smoke-test.sh" in content, (
        "support-baseline.json must include 'bash scripts/codegen/generate-smoke-test.sh' line_check"
    )
