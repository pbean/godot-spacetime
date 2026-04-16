"""
Story 7.1: Map Godot-Native Types in Generated Bindings

Contract tests verifying that the detect-godot-types post-processor exists,
is callable, is invoked by generate-smoke-test.sh, and has produced the
expected companion *.godot.g.cs files alongside the base bindings.

Coverage:
- 5.1  Post-processor script contracts
- 5.2  Companion file presence for matching structs
- 5.3  Companion file content assertions
- 5.4  Fallback: no companion file for non-matching structs
- 5.5  Source module contains the fixture structs
- 5.6  Codegen script updated to invoke post-processor
- 5.7  Regression guards — prior story contracts unbroken
- 5.8  detect_layout() unit tests for all 8 Godot type layouts (AC 3, AC 6)
- 5.9  Script execution and idempotency tests (Task 1.9, Task 1.10)
- 5.10 TypedEntity generated file existence (AC 1, 4)
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _load_detector():
    """Import detect-godot-types.py as a module (hyphen in filename requires importlib)."""
    spec = importlib.util.spec_from_file_location(
        "detect_godot_types",
        ROOT / "scripts/codegen/detect-godot-types.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# 5.1  Post-processor script contracts
# ---------------------------------------------------------------------------

def test_detect_godot_types_script_exists() -> None:
    assert (ROOT / "scripts/codegen/detect-godot-types.py").is_file(), (
        "scripts/codegen/detect-godot-types.py is missing"
    )


def test_detect_godot_types_script_has_no_syntax_errors() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile",
         str(ROOT / "scripts/codegen/detect-godot-types.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"detect-godot-types.py has a syntax error:\n{result.stderr}"
    )


def test_generate_smoke_test_sh_invokes_detect_godot_types() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "detect-godot-types.py" in content, (
        "generate-smoke-test.sh must invoke detect-godot-types.py"
    )


# ---------------------------------------------------------------------------
# 5.2  Companion file presence for matching structs
# ---------------------------------------------------------------------------

def test_vec2f_godot_companion_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Types/Vec2F.godot.g.cs").is_file(), (
        "Vec2F.godot.g.cs is missing — run scripts/codegen/generate-smoke-test.sh"
    )


def test_entity_quat_godot_companion_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Types/EntityQuat.godot.g.cs").is_file(), (
        "EntityQuat.godot.g.cs is missing — run scripts/codegen/generate-smoke-test.sh"
    )


def test_rgba_color_godot_companion_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Types/RgbaColor.godot.g.cs").is_file(), (
        "RgbaColor.godot.g.cs is missing — run scripts/codegen/generate-smoke-test.sh"
    )


def test_vec3i_godot_companion_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Types/Vec3I.godot.g.cs").is_file(), (
        "Vec3I.godot.g.cs is missing — run scripts/codegen/generate-smoke-test.sh"
    )


# ---------------------------------------------------------------------------
# 5.3  Companion file content assertions
# ---------------------------------------------------------------------------

def test_vec2f_companion_contains_implicit_operator() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec2F.godot.g.cs")
    assert "implicit operator" in content, (
        "Vec2F.godot.g.cs must contain 'implicit operator'"
    )


def test_vec2f_companion_references_vector2() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec2F.godot.g.cs")
    assert "Vector2" in content, (
        "Vec2F.godot.g.cs must contain 'Vector2'"
    )


def test_vec2f_companion_has_partial_class() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec2F.godot.g.cs")
    assert "partial class Vec2F" in content, (
        "Vec2F.godot.g.cs must contain 'partial class Vec2F'"
    )


def test_vec2f_companion_has_using_godot() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec2F.godot.g.cs")
    assert "using Godot;" in content, (
        "Vec2F.godot.g.cs must contain 'using Godot;'"
    )


def test_vec2f_companion_header_is_auto_generated() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec2F.godot.g.cs")
    assert "AUTOMATICALLY GENERATED" in content, (
        "Vec2F.godot.g.cs header must contain 'AUTOMATICALLY GENERATED'"
    )


def test_entity_quat_companion_references_quaternion() -> None:
    content = _read("demo/generated/smoke_test/Types/EntityQuat.godot.g.cs")
    assert "Quaternion" in content, (
        "EntityQuat.godot.g.cs must contain 'Quaternion'"
    )


def test_rgba_color_companion_references_color() -> None:
    content = _read("demo/generated/smoke_test/Types/RgbaColor.godot.g.cs")
    assert "Color" in content, (
        "RgbaColor.godot.g.cs must contain 'Color'"
    )


def test_vec3i_companion_references_vector3i() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec3I.godot.g.cs")
    assert "Vector3I" in content, (
        "Vec3I.godot.g.cs must contain 'Vector3I'"
    )


# ---------------------------------------------------------------------------
# 5.4  Fallback: no companion file for non-matching structs
# ---------------------------------------------------------------------------

def test_no_smoke_test_godot_companion() -> None:
    assert not (ROOT / "demo/generated/smoke_test/Types/SmokeTest.godot.g.cs").exists(), (
        "SmokeTest.godot.g.cs must NOT exist — SmokeTest layout does not match any Godot type"
    )


def test_no_not_a_godot_type_companion() -> None:
    assert not (ROOT / "demo/generated/smoke_test/Types/NotAGodotType.godot.g.cs").exists(), (
        "NotAGodotType.godot.g.cs must NOT exist — NotAGodotType layout does not match any Godot type"
    )


# ---------------------------------------------------------------------------
# 5.5  Source module has the fixture structs
# ---------------------------------------------------------------------------

def test_lib_rs_contains_vec2f() -> None:
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "Vec2F" in content, (
        "lib.rs must define the Vec2F fixture struct"
    )


def test_lib_rs_contains_entity_quat() -> None:
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "EntityQuat" in content, (
        "lib.rs must define the EntityQuat fixture struct"
    )


def test_lib_rs_contains_rgba_color() -> None:
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "RgbaColor" in content, (
        "lib.rs must define the RgbaColor fixture struct"
    )


def test_lib_rs_contains_vec3i() -> None:
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "Vec3I" in content, (
        "lib.rs must define the Vec3I fixture struct"
    )


def test_lib_rs_contains_not_a_godot_type() -> None:
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "NotAGodotType" in content, (
        "lib.rs must define the NotAGodotType fallback fixture struct"
    )


# ---------------------------------------------------------------------------
# 5.6  Codegen script updated
# ---------------------------------------------------------------------------

def test_generate_smoke_test_sh_references_detect_godot_types() -> None:
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "detect-godot-types.py" in content, (
        "generate-smoke-test.sh must reference detect-godot-types.py"
    )


# ---------------------------------------------------------------------------
# 5.7  Regression guards — prior story contracts unbroken
# ---------------------------------------------------------------------------

def test_smoke_test_g_cs_still_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Types/SmokeTest.g.cs").is_file(), (
        "Types/SmokeTest.g.cs is missing (regression from prior stories)"
    )


def test_ping_reducer_still_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Reducers/Ping.g.cs").is_file(), (
        "Reducers/Ping.g.cs is missing (regression from prior stories)"
    )


def test_ping_insert_reducer_still_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Reducers/PingInsert.g.cs").is_file(), (
        "Reducers/PingInsert.g.cs is missing (regression from prior stories)"
    )


# ---------------------------------------------------------------------------
# 5.3 (extended)  Deeper content assertions for EntityQuat, RgbaColor, Vec3I
# ---------------------------------------------------------------------------

def test_entity_quat_companion_has_implicit_operator() -> None:
    content = _read("demo/generated/smoke_test/Types/EntityQuat.godot.g.cs")
    assert "implicit operator" in content, (
        "EntityQuat.godot.g.cs must contain 'implicit operator'"
    )


def test_entity_quat_companion_has_partial_class() -> None:
    content = _read("demo/generated/smoke_test/Types/EntityQuat.godot.g.cs")
    assert "partial class EntityQuat" in content, (
        "EntityQuat.godot.g.cs must contain 'partial class EntityQuat'"
    )


def test_entity_quat_companion_has_using_godot() -> None:
    content = _read("demo/generated/smoke_test/Types/EntityQuat.godot.g.cs")
    assert "using Godot;" in content, (
        "EntityQuat.godot.g.cs must contain 'using Godot;'"
    )


def test_entity_quat_companion_header_is_auto_generated() -> None:
    content = _read("demo/generated/smoke_test/Types/EntityQuat.godot.g.cs")
    assert "AUTOMATICALLY GENERATED" in content, (
        "EntityQuat.godot.g.cs header must contain 'AUTOMATICALLY GENERATED'"
    )


def test_entity_quat_companion_has_bidirectional_conversion() -> None:
    content = _read("demo/generated/smoke_test/Types/EntityQuat.godot.g.cs")
    assert "operator Quaternion(EntityQuat" in content, (
        "EntityQuat.godot.g.cs must contain 'operator Quaternion(EntityQuat' (to-Godot direction)"
    )
    assert "operator EntityQuat(Quaternion" in content, (
        "EntityQuat.godot.g.cs must contain 'operator EntityQuat(Quaternion' (from-Godot direction)"
    )


def test_rgba_color_companion_has_implicit_operator() -> None:
    content = _read("demo/generated/smoke_test/Types/RgbaColor.godot.g.cs")
    assert "implicit operator" in content, (
        "RgbaColor.godot.g.cs must contain 'implicit operator'"
    )


def test_rgba_color_companion_has_partial_class() -> None:
    content = _read("demo/generated/smoke_test/Types/RgbaColor.godot.g.cs")
    assert "partial class RgbaColor" in content, (
        "RgbaColor.godot.g.cs must contain 'partial class RgbaColor'"
    )


def test_rgba_color_companion_has_using_godot() -> None:
    content = _read("demo/generated/smoke_test/Types/RgbaColor.godot.g.cs")
    assert "using Godot;" in content, (
        "RgbaColor.godot.g.cs must contain 'using Godot;'"
    )


def test_rgba_color_companion_header_is_auto_generated() -> None:
    content = _read("demo/generated/smoke_test/Types/RgbaColor.godot.g.cs")
    assert "AUTOMATICALLY GENERATED" in content, (
        "RgbaColor.godot.g.cs header must contain 'AUTOMATICALLY GENERATED'"
    )


def test_rgba_color_companion_has_bidirectional_conversion() -> None:
    content = _read("demo/generated/smoke_test/Types/RgbaColor.godot.g.cs")
    assert "operator Color(RgbaColor" in content, (
        "RgbaColor.godot.g.cs must contain 'operator Color(RgbaColor' (to-Godot direction)"
    )
    assert "operator RgbaColor(Color" in content, (
        "RgbaColor.godot.g.cs must contain 'operator RgbaColor(Color' (from-Godot direction)"
    )


def test_vec3i_companion_has_implicit_operator() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec3I.godot.g.cs")
    assert "implicit operator" in content, (
        "Vec3I.godot.g.cs must contain 'implicit operator'"
    )


def test_vec3i_companion_has_partial_class() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec3I.godot.g.cs")
    assert "partial class Vec3I" in content, (
        "Vec3I.godot.g.cs must contain 'partial class Vec3I'"
    )


def test_vec3i_companion_has_using_godot() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec3I.godot.g.cs")
    assert "using Godot;" in content, (
        "Vec3I.godot.g.cs must contain 'using Godot;'"
    )


def test_vec3i_companion_header_is_auto_generated() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec3I.godot.g.cs")
    assert "AUTOMATICALLY GENERATED" in content, (
        "Vec3I.godot.g.cs header must contain 'AUTOMATICALLY GENERATED'"
    )


def test_vec3i_companion_has_bidirectional_conversion() -> None:
    content = _read("demo/generated/smoke_test/Types/Vec3I.godot.g.cs")
    assert "operator Vector3I(Vec3I" in content, (
        "Vec3I.godot.g.cs must contain 'operator Vector3I(Vec3I' (to-Godot direction)"
    )
    assert "operator Vec3I(Vector3I" in content, (
        "Vec3I.godot.g.cs must contain 'operator Vec3I(Vector3I' (from-Godot direction)"
    )


# ---------------------------------------------------------------------------
# 5.8  detect_layout() unit tests for all 8 Godot type layouts (AC 3, AC 6)
# ---------------------------------------------------------------------------

def test_detect_layout_vector3_matches_three_float_xyz() -> None:
    """AC 3 (float variant): 3 float x/y/z → Vector3."""
    det = _load_detector()
    assert det.detect_layout("MyVec3", [("float", "X"), ("float", "Y"), ("float", "Z")]) == "Vector3", (
        "detect_layout must return 'Vector3' for 3 float X/Y/Z fields"
    )


def test_detect_layout_vector4_matches_four_float_xyzw_without_quat() -> None:
    """AC 6 (Vector4 disambiguation): 4 float x/y/z/w, name does NOT contain 'quat' → Vector4."""
    det = _load_detector()
    assert det.detect_layout("MyVec4", [("float", "X"), ("float", "Y"), ("float", "Z"), ("float", "W")]) == "Vector4", (
        "detect_layout must return 'Vector4' for 4 float X/Y/Z/W fields when name lacks 'quat'"
    )


def test_detect_layout_quaternion_requires_quat_in_name() -> None:
    """AC 6 (Quaternion disambiguation): 4 float x/y/z/w AND name contains 'quat' → Quaternion."""
    det = _load_detector()
    assert det.detect_layout("MyQuat", [("float", "X"), ("float", "Y"), ("float", "Z"), ("float", "W")]) == "Quaternion", (
        "detect_layout must return 'Quaternion' for 4 float X/Y/Z/W fields when name contains 'quat'"
    )


def test_detect_layout_quaternion_case_insensitive_quat_match() -> None:
    """AC 6: 'quat' in name is case-insensitive — 'Quaternion' in name triggers Quaternion, not Vector4."""
    det = _load_detector()
    assert det.detect_layout("EntityQuaternion", [("float", "X"), ("float", "Y"), ("float", "Z"), ("float", "W")]) == "Quaternion", (
        "detect_layout must treat 'quat' check as case-insensitive"
    )


def test_detect_layout_vector2i_matches_two_int_xy() -> None:
    """AC 3 (integer variants): 2 int x/y → Vector2I."""
    det = _load_detector()
    assert det.detect_layout("Pos2I", [("int", "X"), ("int", "Y")]) == "Vector2I", (
        "detect_layout must return 'Vector2I' for 2 int X/Y fields"
    )


def test_detect_layout_vector4i_matches_four_int_xyzw() -> None:
    """AC 3 (integer variants): 4 int x/y/z/w → Vector4I."""
    det = _load_detector()
    result = det.detect_layout("Bounds4I", [("int", "X"), ("int", "Y"), ("int", "Z"), ("int", "W")])
    assert result == "Vector4I", (
        "detect_layout must return 'Vector4I' for 4 int X/Y/Z/W fields"
    )


def test_detect_layout_no_match_mixed_types() -> None:
    """AC 2: mixed field types (float + int) → no match (fallback)."""
    det = _load_detector()
    assert det.detect_layout("Mixed", [("float", "X"), ("int", "Y")]) is None, (
        "detect_layout must return None for mixed-type fields"
    )


def test_detect_layout_no_match_wrong_field_count() -> None:
    """AC 2: single float field does not match any Godot layout."""
    det = _load_detector()
    assert det.detect_layout("Scalar", [("float", "X")]) is None, (
        "detect_layout must return None when field count matches no layout"
    )


def test_detect_layout_no_match_wrong_field_names() -> None:
    """AC 2: 2 float fields named A/B (not X/Y) → no match."""
    det = _load_detector()
    assert det.detect_layout("WrongNames", [("float", "A"), ("float", "B")]) is None, (
        "detect_layout must return None when field names do not match any Godot layout"
    )


# ---------------------------------------------------------------------------
# 5.9  Script execution and idempotency (Task 1.9, Task 1.10)
# ---------------------------------------------------------------------------

_DETECTOR_PATH = ROOT / "scripts/codegen/detect-godot-types.py"

# Minimal synthetic .g.cs that matches Vector2 layout
_SYNTHETIC_VEC2_CS = """\
// THIS FILE IS AUTOMATICALLY GENERATED BY SPACETIMEDB.
#nullable enable
using System.Runtime.Serialization;

namespace SpacetimeDB.Types
{
    [SpacetimeDB.Type]
    [DataContract]
    public sealed partial class SyntheticVec2
    {
        public float X;
        public float Y;
    }
}
"""


def test_detect_godot_types_exits_zero_on_valid_dir() -> None:
    """Task 1.9: script exits 0 when given a readable directory."""
    result = subprocess.run(
        [sys.executable, str(_DETECTOR_PATH),
         str(ROOT / "demo/generated/smoke_test/Types")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"detect-godot-types.py must exit 0 on a valid Types/ dir. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_detect_godot_types_exits_one_on_missing_dir() -> None:
    """Task 1.9: script exits 1 when given a non-existent directory."""
    result = subprocess.run(
        [sys.executable, str(_DETECTOR_PATH), "/nonexistent/path/that/does/not/exist"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, (
        "detect-godot-types.py must exit 1 on a non-existent directory"
    )


def test_detect_godot_types_exits_one_on_missing_argument() -> None:
    """Task 1.9: script exits 1 when called without arguments."""
    result = subprocess.run(
        [sys.executable, str(_DETECTOR_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, (
        "detect-godot-types.py must exit 1 when called without arguments"
    )


def test_detect_godot_types_idempotent() -> None:
    """Task 1.10: re-running produces identical companion files (no duplicates, no stale files)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        (tmp_dir / "SyntheticVec2.g.cs").write_text(_SYNTHETIC_VEC2_CS, encoding="utf-8")

        # First run
        r1 = subprocess.run(
            [sys.executable, str(_DETECTOR_PATH), str(tmp_dir)],
            capture_output=True, text=True,
        )
        assert r1.returncode == 0, f"First run failed: {r1.stderr}"
        companion = tmp_dir / "SyntheticVec2.godot.g.cs"
        assert companion.is_file(), "Companion file not created on first run"
        content_first = companion.read_text(encoding="utf-8")

        # Second run (idempotency)
        r2 = subprocess.run(
            [sys.executable, str(_DETECTOR_PATH), str(tmp_dir)],
            capture_output=True, text=True,
        )
        assert r2.returncode == 0, f"Second run failed: {r2.stderr}"
        companions_after = list(tmp_dir.glob("*.godot.g.cs"))
        assert len(companions_after) == 1, (
            f"Idempotency: expected 1 companion file after re-run, got {len(companions_after)}"
        )
        content_second = companion.read_text(encoding="utf-8")
        assert content_first == content_second, (
            "Companion file content changed between runs — script is not idempotent"
        )


def test_detect_godot_types_generates_correct_companion_for_synthetic_vec2() -> None:
    """Integration: script detects Vector2 layout and writes a valid companion."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        (tmp_dir / "SyntheticVec2.g.cs").write_text(_SYNTHETIC_VEC2_CS, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(_DETECTOR_PATH), str(tmp_dir)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        companion = tmp_dir / "SyntheticVec2.godot.g.cs"
        assert companion.is_file(), "Companion not generated for Vector2-layout synthetic type"
        content = companion.read_text(encoding="utf-8")
        assert "Vector2" in content, "Companion must reference Vector2"
        assert "implicit operator" in content, "Companion must contain implicit operator"
        assert "SyntheticVec2" in content, "Companion must reference the class name"


def test_detect_godot_types_skips_non_matching_synthetic_type() -> None:
    """AC 2: script writes no companion for a struct that does not match any layout."""
    non_matching = """\
// THIS FILE IS AUTOMATICALLY GENERATED BY SPACETIMEDB.
#nullable enable
namespace SpacetimeDB.Types
{
    [SpacetimeDB.Type]
    public sealed partial class WeirdType
    {
        public float Foo;
        public float Bar;
        public int Baz;
    }
}
"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        (tmp_dir / "WeirdType.g.cs").write_text(non_matching, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(_DETECTOR_PATH), str(tmp_dir)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert not (tmp_dir / "WeirdType.godot.g.cs").exists(), (
            "Script must NOT generate a companion for a non-matching struct layout"
        )


def test_detect_godot_types_skips_type_with_extra_public_field() -> None:
    """AC 2: extra public fields must block layout mapping instead of being ignored."""
    mixed = """\
// THIS FILE IS AUTOMATICALLY GENERATED BY SPACETIMEDB.
#nullable enable
namespace SpacetimeDB.Types
{
    [SpacetimeDB.Type]
    public sealed partial class MixedVec2
    {
        public float X;
        public float Y;
        public string Label;
    }
}
"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        (tmp_dir / "MixedVec2.g.cs").write_text(mixed, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(_DETECTOR_PATH), str(tmp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert not (tmp_dir / "MixedVec2.godot.g.cs").exists(), (
            "Script must NOT generate a companion when extra public instance fields are present"
        )


def test_detect_godot_types_exits_one_on_parse_failure() -> None:
    """Task 1.9: malformed annotated types must fail with exit 1."""
    malformed = """\
// THIS FILE IS AUTOMATICALLY GENERATED BY SPACETIMEDB.
#nullable enable
namespace SpacetimeDB.Types
{
    [SpacetimeDB.Type]
    public sealed class BrokenType
    {
        public float X;
        public float Y;
    }
}
"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        (tmp_dir / "BrokenType.g.cs").write_text(malformed, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(_DETECTOR_PATH), str(tmp_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            "detect-godot-types.py must exit 1 when an annotated generated type "
            "cannot be parsed safely"
        )
        assert "Error parsing" in result.stderr, (
            "Parse failures must produce an explicit error message"
        )


# ---------------------------------------------------------------------------
# 5.10 TypedEntity generated file existence (AC 1, 4)
# ---------------------------------------------------------------------------

def test_types_typed_entity_g_cs_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Types/TypedEntity.g.cs").is_file(), (
        "Types/TypedEntity.g.cs is missing — run scripts/codegen/generate-smoke-test.sh"
    )


def test_tables_typed_entity_g_cs_exists() -> None:
    assert (ROOT / "demo/generated/smoke_test/Tables/TypedEntity.g.cs").is_file(), (
        "Tables/TypedEntity.g.cs is missing — run scripts/codegen/generate-smoke-test.sh"
    )


def test_types_typed_entity_references_vec2f() -> None:
    content = _read("demo/generated/smoke_test/Types/TypedEntity.g.cs")
    assert "Vec2F" in content, (
        "Types/TypedEntity.g.cs must reference Vec2F (position field)"
    )


def test_types_typed_entity_references_entity_quat() -> None:
    content = _read("demo/generated/smoke_test/Types/TypedEntity.g.cs")
    assert "EntityQuat" in content, (
        "Types/TypedEntity.g.cs must reference EntityQuat (orientation field)"
    )


def test_types_typed_entity_references_rgba_color() -> None:
    content = _read("demo/generated/smoke_test/Types/TypedEntity.g.cs")
    assert "RgbaColor" in content, (
        "Types/TypedEntity.g.cs must reference RgbaColor (color field)"
    )


def test_types_typed_entity_references_vec3i() -> None:
    content = _read("demo/generated/smoke_test/Types/TypedEntity.g.cs")
    assert "Vec3I" in content, (
        "Types/TypedEntity.g.cs must reference Vec3I (tile field)"
    )
