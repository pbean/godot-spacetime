"""
Story 1.3: Define Runtime-Neutral Public SDK Concepts and Terminology
Automated contract tests for all story deliverables.

Covers:
- File existence for all Public/ C# stubs and docs/runtime-boundaries.md
- Namespace declarations match the canonical namespace table
- No SpacetimeDB.* references in any Public/ source file
- Type shapes (enums, records, interfaces, classes) per spec
- docs/runtime-boundaries.md content contracts
- support-baseline.json includes docs/runtime-boundaries.md in required_paths
"""

from __future__ import annotations

import json
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


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# File Existence
# ---------------------------------------------------------------------------

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


@pytest.mark.parametrize("rel_path", REQUIRED_PUBLIC_FILES)
def test_public_stub_file_exists(rel_path: str) -> None:
    assert (ROOT / rel_path).is_file(), f"Required stub missing: {rel_path}"


def test_runtime_boundaries_doc_exists() -> None:
    assert (ROOT / "docs" / "runtime-boundaries.md").is_file(), (
        "docs/runtime-boundaries.md is missing (AC #4)"
    )


# ---------------------------------------------------------------------------
# Namespace Declarations
# ---------------------------------------------------------------------------

NAMESPACE_TABLE = [
    ("addons/godot_spacetime/src/Public/Connection/ConnectionState.cs", "GodotSpacetime.Connection"),
    ("addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs", "GodotSpacetime.Connection"),
    ("addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs", "GodotSpacetime.Connection"),
    ("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs", "GodotSpacetime.Auth"),
    ("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs", "GodotSpacetime.Subscriptions"),
    ("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs", "GodotSpacetime.Subscriptions"),
    ("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs", "GodotSpacetime.Reducers"),
    ("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs", "GodotSpacetime.Reducers"),
    ("addons/godot_spacetime/src/Public/Logging/LogCategory.cs", "GodotSpacetime.Logging"),
    ("addons/godot_spacetime/src/Public/SpacetimeSettings.cs", "GodotSpacetime"),
    ("addons/godot_spacetime/src/Public/SpacetimeClient.cs", "GodotSpacetime"),
]


@pytest.mark.parametrize("rel_path,expected_ns", NAMESPACE_TABLE)
def test_namespace_declaration(rel_path: str, expected_ns: str) -> None:
    content = _read(rel_path)
    # Accept both file-scoped (namespace Foo;) and block-scoped (namespace Foo {)
    pattern = rf"namespace\s+{re.escape(expected_ns)}\s*[;{{]"
    assert re.search(pattern, content), (
        f"{rel_path}: expected namespace '{expected_ns}' not found"
    )


# ---------------------------------------------------------------------------
# No SpacetimeDB References in Public/ Zone
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "cs_file",
    list(PUBLIC.rglob("*.cs")),
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_no_spacetimedb_reference_in_public(cs_file: Path) -> None:
    content = cs_file.read_text(encoding="utf-8")
    # Detect any actual code reference (using directive or type reference).
    # Allow the string "SpacetimeDB" in XML doc-comments (/// ...) and
    # in regular line comments (// ...) since prose mentions are fine.
    code_lines = [
        ln for ln in content.splitlines()
        if not re.match(r"\s*(///|//)", ln)
    ]
    code_text = "\n".join(code_lines)
    assert "SpacetimeDB." not in code_text, (
        f"{cs_file.relative_to(ROOT)}: SpacetimeDB.* reference found in non-comment code. "
        "Public/ zone must not reference SpacetimeDB.ClientSDK types."
    )


# ---------------------------------------------------------------------------
# ConnectionState — Enum Shape
# ---------------------------------------------------------------------------

def test_connection_state_is_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionState.cs")
    assert re.search(r"public\s+enum\s+ConnectionState", content), (
        "ConnectionState must be declared as a public enum"
    )


@pytest.mark.parametrize("value", ["Disconnected", "Connecting", "Connected", "Degraded"])
def test_connection_state_has_required_value(value: str) -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionState.cs")
    assert value in content, f"ConnectionState enum is missing value: {value}"


def test_connection_state_has_exactly_four_values() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionState.cs")
    # Find the enum body between braces
    match = re.search(r"enum\s+ConnectionState\s*\{([^}]*)\}", content, re.DOTALL)
    assert match, "Could not parse ConnectionState enum body"
    body = match.group(1)
    # Extract identifiers (enum members): lines with an identifier followed by optional comma
    members = [
        m.group(1)
        for m in re.finditer(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:,|$)", body, re.MULTILINE)
        if m.group(1)  # skip empty matches
    ]
    assert len(members) == 4, (
        f"ConnectionState must have exactly 4 values, found {len(members)}: {members}"
    )


# ---------------------------------------------------------------------------
# ConnectionStatus — Public Type Shape
# ---------------------------------------------------------------------------

def test_connection_status_is_public_type() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs")
    assert re.search(r"public\s+(?:partial\s+)?(?:record|class)\s+ConnectionStatus", content), (
        "ConnectionStatus must be declared as a public record or class"
    )


def test_connection_status_has_state_and_description() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs")
    assert "ConnectionState" in content and "State" in content, (
        "ConnectionStatus must have a ConnectionState State parameter"
    )
    assert "Description" in content, (
        "ConnectionStatus must have a Description parameter"
    )


# ---------------------------------------------------------------------------
# ConnectionOpenedEvent — Class Exists
# ---------------------------------------------------------------------------

def test_connection_opened_event_is_class() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs")
    assert re.search(r"public\s+(?:partial\s+)?class\s+ConnectionOpenedEvent", content), (
        "ConnectionOpenedEvent must be declared as a public class"
    )


# ---------------------------------------------------------------------------
# ITokenStore — Interface Shape
# ---------------------------------------------------------------------------

def test_itoken_store_is_interface() -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert re.search(r"public\s+interface\s+ITokenStore", content), (
        "ITokenStore must be declared as a public interface"
    )


def test_itoken_store_uses_system_threading_tasks() -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert "using System.Threading.Tasks;" in content, (
        "ITokenStore.cs must import System.Threading.Tasks for Task-based methods"
    )


@pytest.mark.parametrize("signature_fragment", [
    "Task<string?> GetTokenAsync",
    "Task StoreTokenAsync",
    "Task ClearTokenAsync",
])
def test_itoken_store_has_required_method(signature_fragment: str) -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert signature_fragment in content, (
        f"ITokenStore is missing required method signature containing: {signature_fragment}"
    )


def test_itoken_store_has_no_godot_import() -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert "using Godot" not in content, (
        "ITokenStore must not import Godot types — it is a plain C# interface"
    )


# ---------------------------------------------------------------------------
# SubscriptionHandle and SubscriptionAppliedEvent — Class Shapes
# ---------------------------------------------------------------------------

def test_subscription_handle_is_class() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs")
    assert re.search(r"public\s+(?:partial\s+)?class\s+SubscriptionHandle", content), (
        "SubscriptionHandle must be declared as a public class (partial allowed for Godot RefCounted)"
    )


def test_subscription_applied_event_is_class() -> None:
    content = _read("addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs")
    assert re.search(r"public\s+(?:partial\s+)?class\s+SubscriptionAppliedEvent", content), (
        "SubscriptionAppliedEvent must be declared as a public class (partial allowed for Godot RefCounted)"
    )


# ---------------------------------------------------------------------------
# ReducerCallResult and ReducerCallError
# ---------------------------------------------------------------------------

def test_reducer_call_result_is_partial_class_ref_counted() -> None:
    # Story 4.2 replaced the stub record with partial class : RefCounted for Godot signal compatibility.
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    assert re.search(r"public\s+partial\s+class\s+ReducerCallResult", content), (
        "ReducerCallResult must be declared as a public partial class (replaced record stub in Story 4.2 "
        "for Godot signal compatibility — GodotObject-derived type required)"
    )


def test_reducer_call_error_is_partial_class_ref_counted() -> None:
    # Story 4.2 replaced the stub class with partial class : RefCounted for Godot signal compatibility.
    content = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert re.search(r"public\s+partial\s+class\s+ReducerCallError", content), (
        "ReducerCallError must be declared as a public partial class (replaced plain class stub in Story 4.2 "
        "for Godot signal compatibility — GodotObject-derived type required)"
    )


# ---------------------------------------------------------------------------
# LogCategory — Enum Shape
# ---------------------------------------------------------------------------

def test_log_category_is_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Logging/LogCategory.cs")
    assert re.search(r"public\s+enum\s+LogCategory", content), (
        "LogCategory must be declared as a public enum"
    )


@pytest.mark.parametrize("value", ["Connection", "Auth", "Subscription", "Reducer", "Codegen"])
def test_log_category_has_required_value(value: str) -> None:
    content = _read("addons/godot_spacetime/src/Public/Logging/LogCategory.cs")
    assert re.search(rf"\b{value}\b", content), (
        f"LogCategory enum is missing required value: {value}"
    )


# ---------------------------------------------------------------------------
# SpacetimeSettings — Godot Resource
# ---------------------------------------------------------------------------

def test_spacetime_settings_is_partial_resource() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert re.search(r"partial\s+class\s+SpacetimeSettings\s*:\s*Resource", content), (
        "SpacetimeSettings must be declared as: partial class SpacetimeSettings : Resource"
    )


def test_spacetime_settings_has_global_class_attribute() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "[GlobalClass]" in content, (
        "SpacetimeSettings must have the [GlobalClass] attribute for Godot editor visibility"
    )


@pytest.mark.parametrize("property_name", ["Host", "Database"])
def test_spacetime_settings_has_exported_property(property_name: str) -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    # The [Export] attribute must appear before the property declaration
    pattern = rf"\[Export\][^;]*{property_name}"
    assert re.search(pattern, content, re.DOTALL), (
        f"SpacetimeSettings must have an [Export] property named {property_name}"
    )


def test_spacetime_settings_no_spacetimedb_types() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "SpacetimeDB." not in content, (
        "SpacetimeSettings must not reference SpacetimeDB.* types"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient — Godot Node
# ---------------------------------------------------------------------------

def test_spacetime_client_is_partial_node() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert re.search(r"partial\s+class\s+SpacetimeClient\s*:\s*Node", content), (
        "SpacetimeClient must be declared as: partial class SpacetimeClient : Node"
    )


def test_spacetime_client_references_runtime_boundaries_doc() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "runtime-boundaries.md" in content, (
        "SpacetimeClient doc-comment must reference docs/runtime-boundaries.md (AC #2, #3)"
    )


def test_spacetime_client_no_spacetimedb_types() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    # Exclude comment lines
    code_lines = [
        ln for ln in content.splitlines()
        if not re.match(r"\s*(///|//)", ln)
    ]
    assert "SpacetimeDB." not in "\n".join(code_lines), (
        "SpacetimeClient must not reference SpacetimeDB.* types in code"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md — Content Contracts
# ---------------------------------------------------------------------------

DOC_PATH = "docs/runtime-boundaries.md"


def test_runtime_boundaries_doc_has_concept_vocabulary_heading() -> None:
    content = _read(DOC_PATH)
    assert "## Concept Vocabulary" in content or "# Concept Vocabulary" in content, (
        "runtime-boundaries.md must have a Concept Vocabulary section"
    )


@pytest.mark.parametrize("section_marker", [
    "### Connection",
    "### Connection Lifecycle",
    "### Auth",
    "### Subscriptions",
    "### Cache",
    "### Reducers",
    "### Generated Bindings",
    "### Configuration",
    "### SpacetimeClient",
])
def test_runtime_boundaries_doc_has_concept_section(section_marker: str) -> None:
    content = _read(DOC_PATH)
    assert section_marker in content, (
        f"runtime-boundaries.md is missing required concept section: '{section_marker}'"
    )


def test_runtime_boundaries_doc_has_runtime_boundaries_section() -> None:
    content = _read(DOC_PATH)
    assert "## Runtime Boundaries" in content, (
        "runtime-boundaries.md must have a '## Runtime Boundaries' section (AC #4)"
    )


def test_runtime_boundaries_doc_names_three_zones() -> None:
    content = _read(DOC_PATH)
    assert "Public/" in content, "runtime-boundaries.md must name the Public/ zone"
    assert "Internal/" in content, "runtime-boundaries.md must name the Internal/ zone"
    assert "Internal/Platform/DotNet/" in content, (
        "runtime-boundaries.md must name the Internal/Platform/DotNet/ isolation zone"
    )


def test_runtime_boundaries_doc_has_future_runtime_seam_section() -> None:
    content = _read(DOC_PATH)
    assert "Future Runtime Seam" in content, (
        "runtime-boundaries.md must have a 'Future Runtime Seam' section (sets up Story 1.5)"
    )


def test_runtime_boundaries_doc_has_logging_section() -> None:
    content = _read(DOC_PATH)
    assert "LogCategory" in content, (
        "runtime-boundaries.md must document the LogCategory enum"
    )


@pytest.mark.parametrize("forbidden_term", [
    "DbConnection",
    "using SpacetimeDB",
    "SpacetimeDB.ClientSDK",
])
def test_runtime_boundaries_doc_omits_implementation_detail(forbidden_term: str) -> None:
    content = _read(DOC_PATH)
    assert forbidden_term not in content, (
        f"runtime-boundaries.md must not expose implementation detail '{forbidden_term}'. "
        "The doc must use only runtime-neutral SDK vocabulary (AC #1, #3)."
    )


@pytest.mark.parametrize("type_name", [
    "ConnectionState",
    "ConnectionStatus",
    "ConnectionOpenedEvent",
    "ITokenStore",
    "SubscriptionHandle",
    "SubscriptionAppliedEvent",
    "ReducerCallResult",
    "ReducerCallError",
    "SpacetimeSettings",
    "SpacetimeClient",
    "LogCategory",
])
def test_runtime_boundaries_doc_references_public_type(type_name: str) -> None:
    content = _read(DOC_PATH)
    assert type_name in content, (
        f"runtime-boundaries.md must reference public type '{type_name}' "
        "to keep doc and code in sync (AC #2)"
    )


def test_runtime_boundaries_doc_no_spacetimedb_clientsdk_directive() -> None:
    content = _read(DOC_PATH)
    assert "uses `DbConnection` under the hood" not in content, (
        "runtime-boundaries.md must not say 'uses DbConnection under the hood'"
    )
    assert "wraps `SpacetimeDB.ClientSDK`" not in content, (
        "runtime-boundaries.md must not say 'wraps SpacetimeDB.ClientSDK'"
    )


def test_runtime_boundaries_doc_does_not_treat_connection_opened_event_as_full_lifecycle() -> None:
    content = _read(DOC_PATH)
    assert "State transitions surface as [`ConnectionOpenedEvent`" not in content, (
        "runtime-boundaries.md must not imply ConnectionOpenedEvent represents every "
        "connection lifecycle transition"
    )


def test_runtime_boundaries_doc_connection_state_workflow_order() -> None:
    """The SpacetimeClient workflow diagram must show the correct state progression."""
    content = _read(DOC_PATH)
    # Verify the workflow mentions the expected state sequence
    disconnected_pos = content.find("Disconnected")
    connecting_pos = content.find("Connecting")
    connected_pos = content.find("Connected")
    assert disconnected_pos != -1, "runtime-boundaries.md must mention Disconnected state"
    assert connecting_pos != -1, "runtime-boundaries.md must mention Connecting state"
    assert connected_pos != -1, "runtime-boundaries.md must mention Connected state"
    # Workflow should show progression order
    assert disconnected_pos < connecting_pos < connected_pos, (
        "runtime-boundaries.md should present ConnectionState values in lifecycle order: "
        "Disconnected → Connecting → Connected"
    )


# ---------------------------------------------------------------------------
# support-baseline.json — docs/runtime-boundaries.md in required_paths
# ---------------------------------------------------------------------------

def test_support_baseline_includes_runtime_boundaries_doc() -> None:
    baseline = json.loads(_read("scripts/compatibility/support-baseline.json"))
    required_paths = baseline.get("required_paths", [])
    paths = [entry["path"] for entry in required_paths]
    assert "docs/runtime-boundaries.md" in paths, (
        "support-baseline.json required_paths must include 'docs/runtime-boundaries.md' (AC #4, Task 9)"
    )


def test_support_baseline_runtime_boundaries_entry_is_file_type() -> None:
    baseline = json.loads(_read("scripts/compatibility/support-baseline.json"))
    required_paths = baseline.get("required_paths", [])
    entry = next(
        (e for e in required_paths if e["path"] == "docs/runtime-boundaries.md"),
        None,
    )
    assert entry is not None, "docs/runtime-boundaries.md entry missing from required_paths"
    assert entry.get("type") == "file", (
        "docs/runtime-boundaries.md entry in required_paths must have type='file'"
    )
