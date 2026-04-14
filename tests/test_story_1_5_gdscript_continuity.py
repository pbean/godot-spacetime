"""
Story 1.5: Verify Future GDScript Continuity in Structure and Contracts
Automated continuity contract tests for all story deliverables.

Covers:
- Regression guards: docs/runtime-boundaries.md exists, all Public/ stubs present
- docs/runtime-boundaries.md has ## Future Runtime Seam section (AC #1, #3)
- The Future Runtime Seam section names Internal/Platform/GDScript/ as the concrete location (AC #3)
- The GDScript path appears there as a concrete location, not preceded by "e.g." (AC #3)
- docs/runtime-boundaries.md does not mix in legacy generic future-runtime examples (AC #1, #3)
- No Public/ C# filename contains runtime-bound terms (AC #2)
- No Public/ C# namespace declaration contains runtime-bound terms (AC #2)
- No Public/ C# type declaration contains runtime-bound terms (AC #2)
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


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _strip_cs_comments(source: str) -> str:
    # Remove block comments /* ... */
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    # Remove line comments // ...
    source = re.sub(r"//[^\n]*", "", source)
    return source


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Terms forbidden in type declarations and namespace declarations
RUNTIME_BOUND_TERMS = ["DotNet", "CSharp", "Managed"]

# Terms forbidden in Public/ filenames (broader — includes NET)
FILENAME_RUNTIME_BOUND_TERMS = ["DotNet", "CSharp", "Managed", "NET"]

# Public/ stub files from Story 1.3 — used for regression guards and filename checks
REQUIRED_PUBLIC_FILES = [
    "addons/godot_spacetime/src/Public/Connection/ConnectionState.cs",
    "addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs",
    "addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs",
    "addons/godot_spacetime/src/Public/Auth/ITokenStore.cs",
    "addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs",
    "addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs",
    "addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs",
    "addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs",
    "addons/godot_spacetime/src/Public/Logging/LogCategory.cs",
    "addons/godot_spacetime/src/Public/SpacetimeSettings.cs",
    "addons/godot_spacetime/src/Public/SpacetimeClient.cs",
]

# ---------------------------------------------------------------------------
# Regression Guards — re-assert Story 1.3 deliverables still present
# ---------------------------------------------------------------------------


def test_runtime_boundaries_doc_still_exists() -> None:
    """Regression guard: docs/runtime-boundaries.md still exists (extends Story 1.3 coverage)."""
    assert (ROOT / "docs" / "runtime-boundaries.md").is_file(), (
        "docs/runtime-boundaries.md is missing — regression from Story 1.3"
    )


@pytest.mark.parametrize("rel_path", REQUIRED_PUBLIC_FILES)
def test_public_stub_file_still_exists(rel_path: str) -> None:
    """Regression guard: all expected Public/ stub files from Story 1.3 still exist."""
    assert (ROOT / rel_path).is_file(), (
        f"Required Public/ stub missing — regression from Story 1.3: {rel_path}"
    )


# ---------------------------------------------------------------------------
# AC #1 / #3 — Future Runtime Seam section in docs/runtime-boundaries.md
# ---------------------------------------------------------------------------


def test_runtime_boundaries_has_future_runtime_seam_heading() -> None:
    """AC #1/#3: docs/runtime-boundaries.md must have a ## Future Runtime Seam heading."""
    content = _read("docs/runtime-boundaries.md")
    assert "## Future Runtime Seam" in content, (
        "docs/runtime-boundaries.md must contain a '## Future Runtime Seam' section "
        "(AC #1, #3)"
    )


def test_runtime_boundaries_names_gdscript_seam() -> None:
    """AC #3: the Future Runtime Seam section must name Internal/Platform/GDScript/ as the
    intended future GDScript runtime location."""
    content = _read("docs/runtime-boundaries.md")
    seam_section = _extract_future_seam_section(content)
    assert seam_section, f"'{_FUTURE_SEAM_HEADING}' section not found or empty"
    assert "Internal/Platform/GDScript/" in seam_section, (
        "The '## Future Runtime Seam' section must name "
        "Internal/Platform/GDScript/ as the intended future GDScript runtime "
        "location (AC #3)"
    )


def test_gdscript_seam_is_concrete_not_example() -> None:
    """AC #3: Internal/Platform/GDScript/ must appear in the Future Runtime Seam section as a
    concrete location, not an example."""
    content = _read("docs/runtime-boundaries.md")
    seam_section = _extract_future_seam_section(content)
    assert seam_section, f"'{_FUTURE_SEAM_HEADING}' section not found or empty"
    for line in seam_section.splitlines():
        if "Internal/Platform/GDScript/" in line:
            assert "e.g." not in line, (
                "Internal/Platform/GDScript/ must appear as a concrete "
                "named location, not as an example (AC #3)"
            )
            return
    pytest.fail(
        "Internal/Platform/GDScript/ not found in the '## Future Runtime Seam' "
        "section of docs/runtime-boundaries.md"
    )


def test_runtime_boundaries_drops_legacy_future_runtime_examples() -> None:
    """AC #1/#3: after Story 1.5, docs/runtime-boundaries.md must consistently describe the
    future runtime seam using the concrete GDScript location instead of legacy generic
    examples."""
    content = _read("docs/runtime-boundaries.md")
    for legacy_term in ["Internal/Platform/Native/", "GDNative", "GDExtension"]:
        assert legacy_term not in content, (
            "docs/runtime-boundaries.md must consistently describe the future runtime seam "
            "using Internal/Platform/GDScript/ rather than legacy generic examples "
            f"like '{legacy_term}' (AC #1, #3)"
        )


# ---------------------------------------------------------------------------
# AC #2 — Public/ filenames are runtime-neutral
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel_path", REQUIRED_PUBLIC_FILES)
def test_public_filename_is_runtime_neutral(rel_path: str) -> None:
    """AC #2: No Public/ C# filename contains runtime-bound terms."""
    filename = Path(rel_path).stem  # name without .cs extension
    for term in FILENAME_RUNTIME_BOUND_TERMS:
        assert term not in filename, (
            f"Public/ filename '{filename}' contains runtime-bound term '{term}'. "
            "Public/ filenames must be runtime-neutral (AC #2)"
        )


# ---------------------------------------------------------------------------
# AC #2 — Public/ namespace declarations are runtime-neutral
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cs_file",
    list(PUBLIC.rglob("*.cs")),
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_public_namespace_is_runtime_neutral(cs_file: Path) -> None:
    """AC #2: No Public/ C# namespace declaration contains runtime-bound terms."""
    source = _strip_cs_comments(cs_file.read_text(encoding="utf-8"))
    for line in source.splitlines():
        stripped = line.strip()
        if re.match(r"namespace\s+", stripped):
            for term in RUNTIME_BOUND_TERMS:
                assert term not in stripped, (
                    f"Public namespace in {cs_file.name} contains runtime-bound term "
                    f"'{term}': {stripped!r} (AC #2)"
                )


# ---------------------------------------------------------------------------
# AC #2 — Public/ type declarations are runtime-neutral
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cs_file",
    list(PUBLIC.rglob("*.cs")),
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_public_type_declarations_are_runtime_neutral(cs_file: Path) -> None:
    """AC #2: No Public/ C# type declaration (class/enum/interface/record/struct)
    contains runtime-bound terms. Comments are stripped before checking so that
    legitimate doc-comments about .NET do not produce false positives."""
    source = _strip_cs_comments(cs_file.read_text(encoding="utf-8"))
    for line in source.splitlines():
        stripped = line.strip()
        if re.search(r"\b(class|enum|interface|record|struct)\b", stripped):
            for term in RUNTIME_BOUND_TERMS:
                assert term not in stripped, (
                    f"Public type declaration in {cs_file.name} contains "
                    f"runtime-bound term '{term}': {stripped!r} (AC #2)"
                )


# ---------------------------------------------------------------------------
# Gap: AC #3 — Future Runtime Seam section contains explicit runtime-neutral statement
# ---------------------------------------------------------------------------

_FUTURE_SEAM_HEADING = "## Future Runtime Seam"


def _extract_future_seam_section(content: str) -> str:
    """Return the text of the '## Future Runtime Seam' section (up to the next ## heading)."""
    start = content.find(_FUTURE_SEAM_HEADING)
    if start == -1:
        return ""
    section = content[start + len(_FUTURE_SEAM_HEADING):]
    next_heading = re.search(r"\n## ", section)
    if next_heading:
        return section[: next_heading.start()]
    return section


def test_future_runtime_seam_has_explicit_runtime_neutral_statement() -> None:
    """AC #3: The '## Future Runtime Seam' section must contain an explicit statement
    that the Public/ contract is already runtime-neutral.  The story deliverable is
    'The `Public/` contract is already runtime-neutral.' — not merely the presence of
    the GDScript path."""
    content = _read("docs/runtime-boundaries.md")
    seam_section = _extract_future_seam_section(content)
    assert seam_section, f"'{_FUTURE_SEAM_HEADING}' section not found or empty"
    assert "runtime-neutral" in seam_section, (
        "The '## Future Runtime Seam' section must contain an explicit statement "
        "that the Public/ contract is already runtime-neutral (AC #3)"
    )


# ---------------------------------------------------------------------------
# Gap: AC #3 — Future Runtime Seam section enumerates the runtime-neutral type names
# ---------------------------------------------------------------------------

_RUNTIME_NEUTRAL_TYPE_NAMES = [
    "ConnectionState",
    "ITokenStore",
    "SubscriptionHandle",
    "SubscriptionAppliedEvent",
    "ReducerCallResult",
    "ReducerCallError",
    "SpacetimeSettings",
    "SpacetimeClient",
    "LogCategory",
]


@pytest.mark.parametrize("type_name", _RUNTIME_NEUTRAL_TYPE_NAMES)
def test_future_runtime_seam_enumerates_runtime_neutral_type(type_name: str) -> None:
    """AC #3: The '## Future Runtime Seam' section must enumerate each public type name
    as evidence that the Public/ contract requires no renaming for a GDScript runtime."""
    content = _read("docs/runtime-boundaries.md")
    seam_section = _extract_future_seam_section(content)
    assert seam_section, f"'{_FUTURE_SEAM_HEADING}' section not found or empty"
    assert type_name in seam_section, (
        f"The '## Future Runtime Seam' section must name '{type_name}' as a "
        "runtime-neutral public type (AC #3 — explicit runtime-neutral statement)"
    )


# ---------------------------------------------------------------------------
# Gap: Task 1 regression — Story 1.5 forward-reference placeholder was removed
# ---------------------------------------------------------------------------


def test_story_1_5_forward_reference_placeholder_removed() -> None:
    """Task 1 regression guard: the forward-reference placeholder sentence
    'Story 1.5 validates that the GDScript continuity contract holds across this boundary.'
    must have been removed from docs/runtime-boundaries.md.  It was left by Story 1.4
    and the Story 1.5 deliverable explicitly removes it."""
    content = _read("docs/runtime-boundaries.md")
    assert "Story 1.5 validates" not in content, (
        "docs/runtime-boundaries.md still contains the Story 1.5 forward-reference "
        "placeholder sentence — it must be removed as part of the Story 1.5 deliverable "
        "(Task 1)"
    )
