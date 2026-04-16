"""
Story 7.3: Generate BTree Index Accessors for Non-Unique Indexed Columns
Static contract tests verifying BTree index generation from the smoke_test module.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# --- AC 1: BTree accessor generated for indexed column ---

def test_smoke_test_module_has_btree_index_declaration() -> None:
    """2.1 — Module source declares a BTree index on the smoke_test table."""
    content = _read("spacetime/modules/smoke_test/src/lib.rs")
    assert "btree" in content, (
        "lib.rs must declare a BTree index on the smoke_test table (Task 1.1)"
    )


def test_generated_smoke_test_table_has_btree_index_accessor() -> None:
    """2.2 — Generated SmokeTest handle contains a BTreeIndexBase accessor (AC1)."""
    content = _read("demo/generated/smoke_test/Tables/SmokeTest.g.cs")
    assert "BTreeIndexBase" in content, (
        "Tables/SmokeTest.g.cs must contain a BTreeIndexBase accessor (Task 1.5, AC1)"
    )


def test_generated_btree_accessor_uses_string_key_type() -> None:
    """2.3 — BTree accessor key type is string, matching value: String column (AC1)."""
    content = _read("demo/generated/smoke_test/Tables/SmokeTest.g.cs")
    assert "BTreeIndexBase<string>" in content, (
        "BTree accessor must use string key type matching the value: String column (Task 2.3, AC1)"
    )


def test_generated_btree_accessor_field_initialized_in_constructor() -> None:
    """2.4 — BTree accessor field is initialized in the constructor alongside UniqueIndex (AC2)."""
    content = _read("demo/generated/smoke_test/Tables/SmokeTest.g.cs")
    # The constructor must initialize the BTree accessor field with new(this), same as the
    # unique index field pattern (e.g. "Id = new(this);")
    assert "Value = new(this);" in content, (
        "BTree accessor field must be initialized in the constructor with new(this) pattern (Task 2.4, AC2)"
    )


# --- AC 4: Tables without BTree indexes generate no BTree accessor ---

def test_generated_typed_entity_has_no_btree_index() -> None:
    """2.5 — TypedEntity (no BTree declared) generates no BTreeIndexBase accessor (AC4)."""
    content = _read("demo/generated/smoke_test/Tables/TypedEntity.g.cs")
    assert "BTreeIndexBase" not in content, (
        "Tables/TypedEntity.g.cs must not contain a BTreeIndexBase — "
        "TypedEntity has no BTree index declared (Task 1.7, AC4)"
    )


# --- AC 2: BTree accessor coexists with unique index accessor ---

def test_generated_smoke_test_table_still_has_unique_index_class() -> None:
    """2.6 — Unique index class IdUniqueIndex is not removed by BTree addition (regression, AC2)."""
    content = _read("demo/generated/smoke_test/Tables/SmokeTest.g.cs")
    assert "IdUniqueIndex" in content, (
        "IdUniqueIndex must remain alongside the new BTree accessor (Task 2.6, AC2)"
    )


def test_generated_smoke_test_table_still_has_unique_index_base() -> None:
    """2.7 — UniqueIndexBase still present alongside BTreeIndexBase on same handle (regression, AC2)."""
    content = _read("demo/generated/smoke_test/Tables/SmokeTest.g.cs")
    assert "UniqueIndexBase" in content, (
        "UniqueIndexBase must coexist with BTreeIndexBase on SmokeTestHandle (Task 2.7, AC2)"
    )


# --- Story 7.2 regression: typed cache-read path unbroken ---

def test_spacetime_client_still_has_get_db_method() -> None:
    """2.8 — SpacetimeClient.GetDb<TDb>() typed cache path from Story 7.2 is unbroken (regression)."""
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    assert "GetDb<TDb>()" in content or "GetDb<" in content, (
        "SpacetimeClient.cs must still expose GetDb<TDb>() typed cache-read path from Story 7.2 "
        "(Task 2.8)"
    )


# --- Story 7.1 regression: Godot-type post-processor unbroken ---

def test_codegen_script_still_invokes_detect_godot_types() -> None:
    """2.9 — Codegen script still invokes detect-godot-types.py post-processor (regression)."""
    content = _read("scripts/codegen/generate-smoke-test.sh")
    assert "detect-godot-types.py" in content, (
        "generate-smoke-test.sh must still invoke detect-godot-types.py (Task 2.9)"
    )


def test_story_7_1_companion_files_still_exist() -> None:
    """2.10 — Story 7.1 Vec2F Godot companion file still exists (regression)."""
    companion = ROOT / "demo/generated/smoke_test/Types/Vec2F.godot.g.cs"
    assert companion.exists(), (
        "demo/generated/smoke_test/Types/Vec2F.godot.g.cs must exist — "
        "Story 7.1 companion files unbroken (Task 2.10)"
    )


# --- AC1 (structural): BTree class name convention and GetKey override ---

def test_generated_value_index_class_follows_column_name_convention() -> None:
    """3.1 — ValueIndex class follows the '{ColumnName}Index : BTreeIndexBase<TKey>' naming convention (AC1)."""
    content = _read("demo/generated/smoke_test/Tables/SmokeTest.g.cs")
    assert "class ValueIndex : BTreeIndexBase<string>" in content, (
        "Generated ValueIndex class must follow the '{ColumnName}Index : BTreeIndexBase<TKey>' convention — "
        "column 'value' (String) → 'ValueIndex : BTreeIndexBase<string>' (Task 3.1, AC1)"
    )


def test_generated_btree_accessor_overrides_get_key_with_correct_column() -> None:
    """3.2 — ValueIndex.GetKey override extracts row.Value to match the indexed column (AC1)."""
    content = _read("demo/generated/smoke_test/Tables/SmokeTest.g.cs")
    assert "GetKey(SmokeTest row) => row.Value" in content, (
        "ValueIndex.GetKey must return row.Value — confirming the correct column is indexed "
        "(Task 3.2, AC1)"
    )


# --- AC3: BTree accessor documentation ---

def test_codegen_docs_have_btree_index_accessor_section() -> None:
    """3.3 — docs/codegen.md has a BTree index accessor section documenting the generation pattern (AC3)."""
    content = _read("docs/codegen.md")
    assert "BTree index accessor" in content, (
        "docs/codegen.md must have a 'BTree index accessor' section describing the generation pattern "
        "(Task 3.3, AC3)"
    )


def test_codegen_docs_show_filter_usage_example() -> None:
    """3.4 — docs/codegen.md documents the Filter usage example with Value.Filter (AC3)."""
    content = _read("docs/codegen.md")
    assert 'Value.Filter("hello")' in content, (
        'docs/codegen.md must include a code example showing Value.Filter("hello") BTree filtered '
        "lookup (Task 3.4, AC3)"
    )


def test_runtime_boundaries_documents_btree_filter_usage() -> None:
    """3.5 — docs/runtime-boundaries.md documents the BTree filter accessor with Value.Filter usage (AC3)."""
    content = _read("docs/runtime-boundaries.md")
    assert "Value.Filter" in content, (
        "docs/runtime-boundaries.md must document the BTree filter path with a Value.Filter usage "
        "example (Task 3.5, AC3)"
    )
