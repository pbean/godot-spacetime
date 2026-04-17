"""
Story 11.5: live GDScript codegen integration coverage.

Runs the real smoke-test codegen workflow in isolated temp directories so the
repo-owned GDScript emitter is validated against the pinned C# frontend rather
than inferred strings alone.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SMOKE_MODULE = ROOT / "spacetime" / "modules" / "smoke_test"
EMITTER = ROOT / "scripts" / "codegen" / "generate-gdscript-bindings.py"


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        pytest.skip(f"{name} not available on PATH")
    return path


def _run_csharp_codegen(module_root: Path, output_dir: Path, cargo_target_dir: Path) -> None:
    spacetime = _require_tool("spacetime")
    env = os.environ.copy()
    env["CARGO_NET_OFFLINE"] = "true"
    env["CARGO_TARGET_DIR"] = str(cargo_target_dir)

    generate = subprocess.run(
        [
            spacetime,
            "generate",
            "--lang",
            "csharp",
            "--namespace",
            "SpacetimeDB.Story115Integration",
            "--out-dir",
            str(output_dir),
            "--module-path",
            str(module_root),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
        check=False,
    )
    assert generate.returncode == 0, (
        "Story 11.5 integration coverage requires real C# bindings from the pinned CLI.\n"
        f"stdout:\n{generate.stdout}\n"
        f"stderr:\n{generate.stderr}"
    )


def _run_gdscript_codegen(csharp_bindings_dir: Path, output_dir: Path) -> None:
    python3 = _require_tool("python3")
    result = subprocess.run(
        [
            python3,
            str(EMITTER),
            "--csharp-bindings-dir",
            str(csharp_bindings_dir),
            "--out-dir",
            str(output_dir),
            "--module-name",
            "smoke_test",
            "--regen-command",
            "bash scripts/codegen/generate-gdscript-smoke-test.sh",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert result.returncode == 0, (
        "generate-gdscript-bindings.py must succeed for Story 11.5 integration coverage.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


@pytest.fixture(scope="session")
def story_11_5_codegen_outputs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    workspace = tmp_path_factory.mktemp("story-11-5-gdscript-codegen")
    csharp_output = workspace / "csharp_output"
    gdscript_output = workspace / "gdscript_output"
    _run_csharp_codegen(SMOKE_MODULE, csharp_output, workspace / "cargo-target")
    _run_gdscript_codegen(csharp_output, gdscript_output)
    return {
        "workspace": workspace,
        "csharp_output": csharp_output,
        "gdscript_output": gdscript_output,
    }


def test_story_11_5_codegen_integration_produces_expected_artifacts(
    story_11_5_codegen_outputs: dict[str, Path],
) -> None:
    output_dir = story_11_5_codegen_outputs["gdscript_output"]
    required = [
        output_dir / "README.md",
        output_dir / "remote_tables.gd",
        output_dir / "remote_reducers.gd",
        output_dir / "spacetimedb_client.gd",
        output_dir / "Tables" / "smoke_test_table.gd",
        output_dir / "Tables" / "typed_entity_table.gd",
        output_dir / "Types" / "smoke_test.gd",
        output_dir / "Types" / "typed_entity.gd",
        output_dir / "Types" / "vec2f.gd",
        output_dir / "Types" / "entity_quat.gd",
        output_dir / "Types" / "rgba_color.gd",
        output_dir / "Types" / "vec3i.gd",
    ]
    for path in required:
        assert path.is_file(), f"{path} must be produced by the real Story 11.5 codegen workflow."


def test_story_11_5_codegen_integration_emits_runtime_shaped_surface(
    story_11_5_codegen_outputs: dict[str, Path],
) -> None:
    output_dir = story_11_5_codegen_outputs["gdscript_output"]
    smoke_test_type = (output_dir / "Types" / "smoke_test.gd").read_text(encoding="utf-8")
    typed_entity_type = (output_dir / "Types" / "typed_entity.gd").read_text(encoding="utf-8")
    smoke_test_table = (output_dir / "Tables" / "smoke_test_table.gd").read_text(encoding="utf-8")
    remote_tables = (output_dir / "remote_tables.gd").read_text(encoding="utf-8")
    remote_reducers = (output_dir / "remote_reducers.gd").read_text(encoding="utf-8")
    client = (output_dir / "spacetimedb_client.gd").read_text(encoding="utf-8")

    for expected in ("extends Resource", "var id: int", "func to_dictionary()"):
        assert expected in smoke_test_type, (
            f"Generated smoke_test.gd must expose a typed Resource row surface. Missing {expected!r}."
        )
    for expected in ("Vector2", "Quaternion", "Color", "Vector3i"):
        assert expected in typed_entity_type, (
            f"Generated typed_entity.gd must preserve Godot-native type mapping. Missing {expected!r}."
        )
    for expected in (
        "extends RefCounted",
        'return "smoke_test"',
        "func decode_row(",
        "func get_primary_key(",
        "func iter()",
        "func replace_rows(",
    ):
        assert expected in smoke_test_table, (
            f"Generated smoke_test_table.gd must satisfy the Story 11.3 table-contract seam. Missing {expected!r}."
        )
    for expected in ("Tables/smoke_test_table.gd", "Tables/typed_entity_table.gd", "get_table_contracts"):
        assert expected in remote_tables, (
            f"Generated remote_tables.gd must preserve the stable aggregate preload surface. Missing {expected!r}."
        )
    for expected in ("BsatnWriterScript", "invoke_reducer", "func ping_insert(", "func ping("):
        assert expected in remote_reducers, (
            f"Generated remote_reducers.gd must own reducer argument encoding. Missing {expected!r}."
        )
    for expected in ("var tables", "var reducers", "func get_table_contracts()", "attach_connection"):
        assert expected in client, (
            f"Generated spacetimedb_client.gd must expose the module aggregate root. Missing {expected!r}."
        )


def test_story_11_5_codegen_integration_is_deterministic(
    story_11_5_codegen_outputs: dict[str, Path],
    tmp_path: Path,
) -> None:
    first_output = story_11_5_codegen_outputs["gdscript_output"]
    second_output = tmp_path / "gdscript_output_second"
    _run_gdscript_codegen(story_11_5_codegen_outputs["csharp_output"], second_output)

    first_files = sorted(path.relative_to(first_output) for path in first_output.rglob("*") if path.is_file())
    second_files = sorted(path.relative_to(second_output) for path in second_output.rglob("*") if path.is_file())
    assert first_files == second_files, "Story 11.5 GDScript codegen must emit a stable file set across reruns."

    for rel_path in first_files:
        first_text = (first_output / rel_path).read_text(encoding="utf-8")
        second_text = (second_output / rel_path).read_text(encoding="utf-8")
        assert first_text == second_text, f"Generated file {rel_path} must be byte-for-byte deterministic."


def test_story_11_5_codegen_integration_harness_avoids_hardcoded_sleeps() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    sanitized = source.replace('"time.sleep("', "")
    assert "time.sleep(" not in sanitized, (
        "Story 11.5 codegen integration coverage must rely on subprocess timeouts, not hardcoded sleeps."
    )
