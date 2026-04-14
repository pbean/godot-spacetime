"""
Story 1.4: Isolate the .NET Runtime Adapter Behind Internal Boundaries
Automated isolation contract tests for all story deliverables.

Covers:
- All three adapter files exist in Internal/Platform/DotNet/
- No SpacetimeDB references in any Public/ C# file (code lines only)
- No SpacetimeDB references in any addon C# file outside Internal/Platform/DotNet/
- SpacetimeDB.ClientSDK PackageReference present in godot-spacetime.csproj
- All three adapter files declare the GodotSpacetime.Runtime.Platform.DotNet namespace
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "addons" / "godot_spacetime" / "src" / "Public"
INTERNAL = ROOT / "addons" / "godot_spacetime" / "src" / "Internal"
DOTNET_ZONE = INTERNAL / "Platform" / "DotNet"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _code_lines(text: str) -> str:
    """Strip C# comment forms so we can search non-comment code."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(
        ln for ln in text.splitlines()
        if not re.match(r"\s*(///|//)", ln)
    )


def _has_spacetimedb_reference(text: str) -> bool:
    code_text = _code_lines(text)
    return bool(
        re.search(r"\b(?:global\s+)?using\s+SpacetimeDB(?:\.[A-Za-z_][A-Za-z0-9_.]*)?\s*;", code_text)
        or re.search(r"\bSpacetimeDB\.", code_text)
    )


# ---------------------------------------------------------------------------
# Task 2/3/4 — Adapter File Existence
# ---------------------------------------------------------------------------

ADAPTER_FILES = [
    "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs",
    "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs",
    "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs",
]


@pytest.mark.parametrize("rel_path", ADAPTER_FILES)
def test_adapter_file_exists(rel_path: str) -> None:
    assert (ROOT / rel_path).is_file(), f"Required adapter file missing: {rel_path}"


# ---------------------------------------------------------------------------
# Task 2/3/4 — Namespace Declarations
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel_path", ADAPTER_FILES)
def test_adapter_namespace(rel_path: str) -> None:
    content = _read(rel_path)
    expected_ns = "GodotSpacetime.Runtime.Platform.DotNet"
    pattern = rf"namespace\s+{re.escape(expected_ns)}\s*[;{{]"
    assert re.search(pattern, content), (
        f"{rel_path}: expected namespace '{expected_ns}' not found"
    )


# ---------------------------------------------------------------------------
# AC #1 — No SpacetimeDB in Public/ zone
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "cs_file",
    list(PUBLIC.rglob("*.cs")),
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_no_spacetimedb_in_public(cs_file: Path) -> None:
    content = cs_file.read_text(encoding="utf-8")
    assert not _has_spacetimedb_reference(content), (
        f"{cs_file.relative_to(ROOT)}: SpacetimeDB reference found in Public/ zone. "
        "Public/ must contain zero SpacetimeDB.* using statements or type references."
    )


# ---------------------------------------------------------------------------
# AC #1 — No SpacetimeDB in any addon C# file outside Internal/Platform/DotNet/
# ---------------------------------------------------------------------------

SRC_ROOT = ROOT / "addons" / "godot_spacetime" / "src"

NON_DOTNET_CS_FILES = [
    f for f in SRC_ROOT.rglob("*.cs")
    if DOTNET_ZONE not in f.parents
]


@pytest.mark.parametrize(
    "cs_file",
    NON_DOTNET_CS_FILES,
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_no_spacetimedb_outside_dotnet_zone(cs_file: Path) -> None:
    content = cs_file.read_text(encoding="utf-8")
    assert not _has_spacetimedb_reference(content), (
        f"{cs_file.relative_to(ROOT)}: SpacetimeDB reference found outside "
        "Internal/Platform/DotNet/ zone. Only the DotNet adapter zone may reference "
        "SpacetimeDB.ClientSDK types."
    )


# ---------------------------------------------------------------------------
# AC #1 — DotNet zone DOES reference SpacetimeDB (confirms the zone is active)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel_path", ADAPTER_FILES)
def test_adapter_references_spacetimedb(rel_path: str) -> None:
    content = _read(rel_path)
    assert _has_spacetimedb_reference(content), (
        f"{rel_path}: expected SpacetimeDB reference not found. "
        "Adapter stubs must reference SpacetimeDB to prove zone isolation."
    )


# ---------------------------------------------------------------------------
# Task 1 — csproj PackageReference
# ---------------------------------------------------------------------------

def test_csproj_has_spacetimedb_package_reference() -> None:
    content = _read("godot-spacetime.csproj")
    assert 'PackageReference Include="SpacetimeDB.ClientSDK"' in content, (
        "godot-spacetime.csproj must contain a PackageReference for SpacetimeDB.ClientSDK"
    )


def test_csproj_spacetimedb_version_is_2_1_0() -> None:
    content = _read("godot-spacetime.csproj")
    assert 'Version="2.1.0"' in content, (
        "godot-spacetime.csproj SpacetimeDB.ClientSDK PackageReference must specify Version=\"2.1.0\""
    )


# ---------------------------------------------------------------------------
# Gap: Adapter class modifiers — internal sealed class (AC: 1, 2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel_path", ADAPTER_FILES)
def test_adapter_is_internal_sealed_class(rel_path: str) -> None:
    content = _read(rel_path)
    code_text = _code_lines(content)
    assert re.search(r"internal\s+sealed\s+class\s+\w+", code_text), (
        f"{rel_path}: adapter must be declared 'internal sealed class'. "
        "Public adapters would leak SDK implementation details across the boundary."
    )


# ---------------------------------------------------------------------------
# Gap: Specific using SpacetimeDB; directive in non-comment code (AC: 1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel_path", ADAPTER_FILES)
def test_adapter_has_using_spacetimedb_directive(rel_path: str) -> None:
    content = _read(rel_path)
    code_text = _code_lines(content)
    assert re.search(r"using\s+SpacetimeDB\s*;", code_text), (
        f"{rel_path}: adapter must have 'using SpacetimeDB;' in non-comment code. "
        "The directive is the explicit SDK import that proves zone ownership."
    )


# ---------------------------------------------------------------------------
# Gap: IDbConnection? stub field in each adapter (AC: 1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel_path", ADAPTER_FILES)
def test_adapter_has_idbconnection_stub_field(rel_path: str) -> None:
    content = _read(rel_path)
    code_text = _code_lines(content)
    assert re.search(r"IDbConnection\?", code_text), (
        f"{rel_path}: adapter must declare a private 'IDbConnection?' stub field "
        "to prove it references SDK types. IDbConnection is the connection interface "
        "in SpacetimeDB.ClientSDK 2.1.0 (no concrete DbConnection class exists)."
    )


# ---------------------------------------------------------------------------
# Gap: Task 5 — compatibility-matrix.md SpacetimeDB.ClientSDK row (AC: 3)
# ---------------------------------------------------------------------------

_COMPAT_ROW = (
    "| `SpacetimeDB.ClientSDK` | `2.1.0` | Added as `PackageReference` in Story 1.4; "
    "the `.NET` adapter in `Internal/Platform/DotNet/` is the only permitted reference location. |"
)


def test_compatibility_matrix_spacetimedb_row_reflects_story_1_4() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert _COMPAT_ROW in content, (
        "docs/compatibility-matrix.md SpacetimeDB.ClientSDK row must reflect the Story 1.4 "
        "PackageReference addition and name Internal/Platform/DotNet/ as the only permitted "
        "reference location. Check that Task 5 was applied and the row text matches exactly."
    )


# ---------------------------------------------------------------------------
# Gap: Task 6 — support-baseline.json line_check updated to Story 1.4 text (AC: 3)
# ---------------------------------------------------------------------------

def test_support_baseline_spacetimedb_line_check_is_story_1_4() -> None:
    import json
    baseline = json.loads(_read("scripts/compatibility/support-baseline.json"))
    line_checks = baseline.get("line_checks", [])
    entry = next(
        (lc for lc in line_checks if lc.get("label") == "SpacetimeDB.ClientSDK"),
        None,
    )
    assert entry is not None, (
        "support-baseline.json must contain a line_check entry with label 'SpacetimeDB.ClientSDK'"
    )
    assert entry.get("expected_line") == _COMPAT_ROW, (
        "support-baseline.json SpacetimeDB.ClientSDK line_check 'expected_line' must match "
        "the Story 1.4 compatibility-matrix.md row exactly. "
        f"Expected: {_COMPAT_ROW!r}. "
        f"Found: {entry.get('expected_line')!r}"
    )
    assert entry.get("version_key") == "spacetimedb_client_sdk", (
        "support-baseline.json SpacetimeDB.ClientSDK entry must keep version_key='spacetimedb_client_sdk'"
    )


# ---------------------------------------------------------------------------
# Gap: AC #3 — docs/runtime-boundaries.md explicitly names the DotNet isolation zone
# ---------------------------------------------------------------------------

def test_runtime_boundaries_doc_names_dotnet_isolation_zone() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Internal/Platform/DotNet/" in content, (
        "docs/runtime-boundaries.md must explicitly name 'Internal/Platform/DotNet/' as the "
        ".NET-specific implementation zone (Story 1.4 AC #3 — structural code must match docs)."
    )


def test_reference_detector_ignores_comment_only_mentions() -> None:
    content = """
// using SpacetimeDB;
/// SpacetimeDB.ClientSDK mention in XML docs
/* SpacetimeDB.IDbConnection? _dbConnection; */
namespace Example;
"""
    assert not _has_spacetimedb_reference(content)


def test_reference_detector_matches_real_sdk_references() -> None:
    using_directive = "using SpacetimeDB;\nnamespace Example;"
    qualified_reference = "namespace Example;\ninternal sealed class Sample { private SpacetimeDB.IDbConnection? _dbConnection; }"
    assert _has_spacetimedb_reference(using_directive)
    assert _has_spacetimedb_reference(qualified_reference)
