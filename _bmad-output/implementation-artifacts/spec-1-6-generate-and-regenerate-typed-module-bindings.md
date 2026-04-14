---
title: '1.6 Generate and Regenerate Typed Module Bindings'
type: 'feature'
created: '2026-04-14T00:00:00-07:00'
status: 'done'
baseline_commit: '5e7c7eb'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-2-establish-baseline-build-and-workflow-validation-early.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-3-define-runtime-neutral-public-sdk-concepts-and-terminology.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-4-isolate-the-net-runtime-adapter-behind-internal-boundaries.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-5-verify-future-gdscript-continuity-in-structure-and-contracts.md'
---

# Story 1.6: Generate and Regenerate Typed Module Bindings

Status: done

## Story

As a Godot developer,
I want to generate and regenerate client bindings from a SpacetimeDB module,
so that my project has typed access to the current schema.

## Acceptance Criteria

1. **Given** a supported SpacetimeDB module and the `spacetime` CLI, **when** I run the documented code generation workflow, **then** generated bindings are created in `demo/generated/smoke_test/` — the dedicated generated location intended for consumer, demo, or test use.
2. **And** rerunning the workflow after a schema change refreshes those generated artifacts without manual edits to generated files.
3. **And** the documented workflow exposes a repeatable command or script (`scripts/codegen/generate-smoke-test.sh`) for sample or fixture module inputs so automation can run the same generation path without manual repair of generated files.

## Deliverables

This story produces five concrete outputs:

1. **`spacetime/modules/smoke_test/` module source** — real Rust SpacetimeDB module with a minimal `SmokeTest` table and `ping` reducer that serves as the canonical smoke-test input for code generation
2. **`scripts/codegen/generate-smoke-test.sh`** — repeatable generation script that invokes `spacetime generate --lang csharp` targeting the smoke_test module and outputting to `demo/generated/smoke_test/`
3. **`demo/generated/smoke_test/`** — committed read-only C# bindings produced by running the codegen script; never hand-edited
4. **`docs/codegen.md`** — updated from placeholder to actual workflow documenting prerequisites, the generation command, output location, and regeneration instructions
5. **`tests/test_story_1_6_generate_bindings.py`** — pytest suite verifying module source structure, codegen script presence and content, committed generated artifact existence, and `docs/codegen.md` workflow content

`scripts/compatibility/support-baseline.json` is also updated to add the new `scripts/codegen/` directory, the script file, and the `demo/generated/smoke_test/` output path to `required_paths`, plus new `line_checks` entries for the new `docs/codegen.md` content.

No changes to `addons/godot_spacetime/src/` (Public/ or Internal/). Generated bindings are consumer-facing test/demo fixtures, not addon runtime source.

## Tasks / Subtasks

- [x] Task 1 — Create smoke_test Rust module source (AC: 1, 2, 3)
  - [x] Create `spacetime/modules/smoke_test/Cargo.toml` with `crate-type = ["cdylib"]` and the `spacetimedb` crate pinned to the version compatible with SpacetimeDB 2.1+ (see Dev Notes for the exact Cargo.toml template and crate version guidance)
  - [x] Create `spacetime/modules/smoke_test/src/lib.rs` with exactly:
    - One table named `smoke_test` using `SmokeTest` struct: `id: u32` (primary key, autoinc) and `value: String`
    - One no-op reducer named `ping` that validates the generation and invocation path
  - [x] Update `spacetime/modules/smoke_test/README.md` to replace the placeholder text with a description of the module, its table and reducer, and the generated output location (`demo/generated/smoke_test/`)

- [x] Task 2 — Create codegen script (AC: 3)
  - [x] Create `scripts/codegen/` directory
  - [x] Create `scripts/codegen/generate-smoke-test.sh` (see Dev Notes for exact script content):
    - Clears `demo/generated/smoke_test/` before each run (ensures regeneration is clean, not additive)
    - Invokes `spacetime generate --lang csharp` targeting `spacetime/modules/smoke_test/` with output to `demo/generated/smoke_test/`
    - Exits non-zero on failure
    - Is executable (`chmod +x scripts/codegen/generate-smoke-test.sh`)
    - Includes a header comment describing what it does and where to run it from

- [x] Task 3 — Run codegen and commit generated C# bindings (AC: 1, 2)
  - [x] Create `demo/` directory at repo root if it does not exist
  - [x] Create `demo/generated/smoke_test/` directory
  - [x] Run `bash scripts/codegen/generate-smoke-test.sh` with the `spacetime` CLI installed locally to produce the C# output
  - [x] Verify at least one `.cs` file is present in `demo/generated/smoke_test/` after generation
  - [x] Add `demo/generated/smoke_test/README.md` with an auto-generated artifact notice (see Dev Notes for exact text)
  - [x] Commit all generated files as read-only artifacts — do NOT add any hand-written `.cs` file to `demo/generated/smoke_test/`

- [x] Task 4 — Update `docs/codegen.md` (AC: 1, 2, 3)
  - [x] Replace the "Code Generation Readiness" placeholder content with the actual workflow (see Dev Notes for the complete required structure and exact preserved lines)
  - [x] New section: prerequisites (spacetime CLI, SpacetimeDB 2.1+)
  - [x] New section: generation command showing `bash scripts/codegen/generate-smoke-test.sh`
  - [x] New line: `The script outputs generated C# bindings to \`demo/generated/smoke_test/\`.` (exact line required by line_check)
  - [x] New section: regeneration instructions (run the same script after schema changes)
  - [x] **PRESERVE EXACTLY** all five existing lines currently checked by `validate-foundation.py` (see Dev Notes — these are not optional and must appear as exact stripped lines in the file)

- [x] Task 5 — Update `scripts/compatibility/support-baseline.json` (AC: 3)
  - [x] Add to `required_paths` (append after the existing `tests/fixtures/settings/.gitkeep` entry):
    - `{ "path": "scripts/codegen", "type": "dir" }`
    - `{ "path": "scripts/codegen/generate-smoke-test.sh", "type": "file" }`
    - `{ "path": "demo", "type": "dir" }`
    - `{ "path": "demo/generated", "type": "dir" }`
    - `{ "path": "demo/generated/smoke_test", "type": "dir" }`
  - [x] Add to `line_checks` (append after the existing `docs/codegen.md` checks):
    - `{ "file": "docs/codegen.md", "label": "Codegen script invocation", "expected_line": "bash scripts/codegen/generate-smoke-test.sh" }`
    - `{ "file": "docs/codegen.md", "label": "Generated output location", "expected_line": "The script outputs generated C# bindings to \`demo/generated/smoke_test/\`." }`

- [x] Task 6 — Create `tests/test_story_1_6_generate_bindings.py` (AC: 1, 2, 3)
  - [x] Follow exact helper patterns from `tests/test_story_1_3_sdk_concepts.py` — `ROOT`, `_read()`, `_lines()` at top
  - [x] Module source structure tests:
    - `spacetime/modules/smoke_test/Cargo.toml` exists
    - Cargo.toml contains `crate-type = ["cdylib"]` (exact string; required for SpacetimeDB WASM)
    - `spacetime/modules/smoke_test/src/lib.rs` exists
    - `lib.rs` contains the string `smoke_test` (table definition)
    - `lib.rs` contains the string `ping` (reducer definition)
  - [x] Codegen script tests:
    - `scripts/codegen/generate-smoke-test.sh` exists
    - Script content contains `spacetime generate`
    - Script content contains `--lang csharp`
    - Script content contains `smoke_test` (module path reference)
    - Script content contains `demo/generated/smoke_test` (output path reference)
  - [x] Generated bindings tests:
    - `demo/generated/smoke_test/` directory exists
    - At least one `.cs` file exists in `demo/generated/smoke_test/` (use `rglob("*.cs")`)
  - [x] docs/codegen.md content tests:
    - `docs/codegen.md` contains `generate-smoke-test.sh`
    - `docs/codegen.md` contains `demo/generated/smoke_test`
  - [x] Regression guards (prior story deliverables still present):
    - `docs/codegen.md` exists (re-assert from story 1.2)
    - `spacetime/modules/smoke_test/` directory exists (re-assert from story 1.2)
    - `tests/fixtures/generated/` directory exists (re-assert from story 1.2)
    - (No C# source regressions needed — this story does not touch addon source)

- [x] Task 7 — Verify all checks pass (AC: all)
  - [x] Run `python3 scripts/compatibility/validate-foundation.py` — exits 0 (new required paths and line_checks in baseline must resolve correctly)
  - [x] Run `dotnet build godot-spacetime.sln -c Debug` — succeeds with 0 errors and 0 warnings (no changes to addon C# source)
  - [x] Run `pytest tests/test_story_1_6_generate_bindings.py` — all tests pass
  - [x] Run `pytest -q` — full suite still green (stories 1.3 + 1.4 + 1.5 + 1.6 tests all pass)

## Dev Notes

### Story Scope and Context

Story 1.6 is the first story to produce content in the code-generation pipeline. Stories 1.1–1.5 built the structure foundation (plugin scaffold, validation lane, public SDK concepts, runtime boundary isolation, GDScript continuity). Story 1.6 creates the smoke-test module source, the repeatable generation script, and the first committed generated C# bindings.

Story 1.7 depends on Story 1.6's generated output to explain and document the generated types. Story 1.8 depends on both the smoke_test module structure and `tests/fixtures/generated/` (separate from `demo/generated/`) for schema-drift and compatibility validation. Ensure `demo/generated/smoke_test/` has stable, well-formed generated output before marking this story done.

**DO**: Create the Rust module, create the codegen script, run it to produce committed C# output, update `docs/codegen.md`, update `support-baseline.json`, and write the test suite.

**DO NOT**: Modify `addons/godot_spacetime/src/` (Public/ or Internal/Platform/DotNet/). Modify `docs/runtime-boundaries.md`, `docs/compatibility-matrix.md`, or `docs/install.md`. Modify `.github/workflows/`. Touch `tests/fixtures/generated/` (that is reserved for Story 1.8+). Touch `spacetime/modules/compatibility_fixture/` (reserved for Story 1.8). Add generated files to the addon — generated bindings stay in `demo/generated/`, not in `addons/`.

### SpacetimeDB 2.1 Rust Module SDK — Crate Version

The Rust `spacetimedb` crate for server module development is versioned independently from the SpacetimeDB server. For SpacetimeDB 2.1.x:

- Check `https://crates.io/crates/spacetimedb` for the current stable release
- Verify the crate's documented compatibility with SpacetimeDB 2.1 in the crate changelog or SpacetimeDB release notes
- The expected Cargo.toml structure:

```toml
[package]
name = "smoke_test"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
spacetimedb = "1.1"  # verify exact version for SpacetimeDB 2.1 at crates.io
```

> **Developer action required:** Confirm the correct `spacetimedb` crate version for SpacetimeDB 2.1 before writing Cargo.toml. If `1.1.x` does not compile or is incompatible with the 2.1 server, consult the SpacetimeDB GitHub releases page. The crate version pinned here becomes the project's codegen baseline.

### SpacetimeDB 2.1 Module Source Pattern

Minimal `src/lib.rs` using SpacetimeDB 2.x attribute macros:

```rust
use spacetimedb::{spacetimedb, ReducerContext};

#[spacetimedb(table(name = smoke_test, public))]
pub struct SmokeTest {
    #[primarykey]
    #[autoinc]
    pub id: u32,
    pub value: String,
}

#[spacetimedb(reducer)]
pub fn ping(_ctx: ReducerContext) {
    // No-op smoke reducer: validates the generation and CLI invocation path.
}
```

> **Developer note:** The `spacetimedb` macro attribute style (wrapper `#[spacetimedb(table(...))]` vs flat `#[table]`) varies by crate version. Verify the correct form in the crate documentation for the version you pin. The essential contract for this story is: one table named `smoke_test` with at minimum `id` (primary key) and `value: String`, plus one reducer named `ping`. The exact macro syntax is secondary to the table/reducer names, which are stable across Story 1.6–1.8.

### `spacetime generate` CLI Command

The generation command for SpacetimeDB 2.1 C# client bindings:

```bash
spacetime generate \
  --lang csharp \
  --out-dir demo/generated/smoke_test/ \
  --project-path spacetime/modules/smoke_test/
```

> **Developer action required:** Run `spacetime generate --help` to confirm the exact flag names for your installed CLI version. The flags `--out-dir` and `--project-path` may be named differently in some CLI versions (e.g., `--outdir`, `--module-path`). Capture the exact working invocation in `generate-smoke-test.sh`.

### Codegen Script — Exact Content

`scripts/codegen/generate-smoke-test.sh` should follow this structure:

```bash
#!/usr/bin/env bash
# generate-smoke-test.sh
#
# Generates C# client bindings from the smoke_test SpacetimeDB module.
# Output is committed to demo/generated/smoke_test/ as read-only artifacts.
#
# Usage (run from repo root):
#   bash scripts/codegen/generate-smoke-test.sh
#
# Prerequisites:
#   - spacetime CLI installed (SpacetimeDB 2.1+)
#   - Run from the repository root

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/demo/generated/smoke_test"
MODULE_PATH="${REPO_ROOT}/spacetime/modules/smoke_test"

echo "Clearing previous output: ${OUTPUT_DIR}"
rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"

echo "Running spacetime generate..."
spacetime generate \
  --lang csharp \
  --out-dir "${OUTPUT_DIR}" \
  --project-path "${MODULE_PATH}"

echo "Generated bindings written to: ${OUTPUT_DIR}"
ls -1 "${OUTPUT_DIR}"
```

Make it executable: `chmod +x scripts/codegen/generate-smoke-test.sh`

### Expected Generated Output Structure

For a minimal module with one table and one reducer, `spacetime generate --lang csharp` in SpacetimeDB 2.x typically produces a C# namespace tree. Expected output at minimum:

```
demo/generated/smoke_test/
├── SmokeTest.cs           — table row type (or embedded in ModuleBindings.cs)
├── Reducers/
│   └── Ping.cs            — reducer proxy (or flat: Ping.cs)
└── ModuleBindings.cs      — aggregate binding registry
```

> **Developer verification required:** After running the script, verify which files are produced. The exact filenames and directory structure depend on the CLI version. The test only checks that at least one `.cs` file exists; however, Story 1.7 will reference the type names. Verify the generated types (`SmokeTest`, `Ping`) are present and follow the expected patterns before marking this story done.

### `docs/codegen.md` — Exact Required Lines

Five existing lines in `docs/codegen.md` are checked by `validate-foundation.py` (via `support-baseline.json` `line_checks`). These **must appear as exact stripped lines** in the updated file. Do not reword, reformat, or remove them:

```
python3 scripts/compatibility/validate-foundation.py
- `spacetime/modules/smoke_test/` is reserved for the future local smoke module used by quickstart and first-connection validation.
- `spacetime/modules/compatibility_fixture/` is reserved for future schema-drift and regeneration scenarios.
- `tests/fixtures/generated/` is reserved for read-only generated bindings consumed by tests.
- `tests/fixtures/settings/` is reserved for non-shipping test settings and environment fixtures.
```

Two new exact lines are added to `line_checks` by this story's Task 5 and must appear in the updated file:

```
bash scripts/codegen/generate-smoke-test.sh
The script outputs generated C# bindings to `demo/generated/smoke_test/`.
```

A safe structure for the updated `docs/codegen.md` that satisfies all line_checks:

```markdown
# Code Generation

## Prerequisites

- SpacetimeDB CLI: `2.1+` — install via the [SpacetimeDB installation guide](https://spacetimedb.com/install)
- Run from the repository root

## Generating Smoke Test Bindings

Run the provided script to generate C# client bindings from the smoke_test module:

```bash
bash scripts/codegen/generate-smoke-test.sh
```

The script outputs generated C# bindings to `demo/generated/smoke_test/`.

## Regenerating After Schema Changes

Rerun the same script after any schema change. The script clears the previous output before regenerating, so no manual cleanup is required:

```bash
bash scripts/codegen/generate-smoke-test.sh
```

## Foundation Validation

Run the shared foundation validation entrypoint to confirm the expected codegen-related inputs still exist and the support baseline has not drifted:

```bash
python3 scripts/compatibility/validate-foundation.py
```

The same entrypoint is used by `.github/workflows/validate-foundation.yml` after restore and build complete.

## Module and Fixture Locations

- `spacetime/modules/smoke_test/` is reserved for the future local smoke module used by quickstart and first-connection validation.
- `spacetime/modules/compatibility_fixture/` is reserved for future schema-drift and regeneration scenarios.
- `tests/fixtures/generated/` is reserved for read-only generated bindings consumed by tests.
- `tests/fixtures/settings/` is reserved for non-shipping test settings and environment fixtures.

## Source of Truth

The machine-checkable support baseline for the current foundation lives in `scripts/compatibility/support-baseline.json`.

Future code generation and compatibility stories should extend the existing validation entrypoint instead of replacing it with a separate manual-only path.
```

> The reserved-path section lines must match exactly (the `` ` `` backtick pairs, the punctuation, the article wording). Copy them from the current `docs/codegen.md` rather than retyping them.

### `demo/generated/smoke_test/README.md` — Exact Content

```markdown
# Generated Bindings — smoke_test module

These files are generated by `scripts/codegen/generate-smoke-test.sh` and committed as read-only artifacts.

**Do not edit these files manually.** To refresh after a schema change, run:

```bash
bash scripts/codegen/generate-smoke-test.sh
```

Generated with: `spacetime generate --lang csharp`
Source module: `spacetime/modules/smoke_test/`
```

### Test File — Key Patterns

Follow the exact pattern from `tests/test_story_1_3_sdk_concepts.py`:

```python
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
```

Key test function structure to implement (fill in assertions per Task 6):

```python
# --- Module source ---

def test_smoke_test_cargo_toml_exists() -> None: ...
def test_smoke_test_cargo_toml_is_cdylib() -> None: ...  # 'crate-type = ["cdylib"]' in content
def test_smoke_test_lib_rs_exists() -> None: ...
def test_smoke_test_lib_rs_defines_smoke_test_table() -> None: ...  # "smoke_test" in content
def test_smoke_test_lib_rs_defines_ping_reducer() -> None: ...  # "ping" in content

# --- Codegen script ---

def test_codegen_script_exists() -> None: ...
def test_codegen_script_calls_spacetime_generate() -> None: ...
def test_codegen_script_targets_csharp() -> None: ...  # "--lang csharp" in content
def test_codegen_script_targets_smoke_test_module() -> None: ...
def test_codegen_script_targets_demo_generated_output() -> None: ...

# --- Generated bindings ---

def test_generated_smoke_test_dir_exists() -> None: ...
def test_generated_smoke_test_contains_cs_files() -> None: ...
    # cs_files = list((ROOT / "demo/generated/smoke_test").rglob("*.cs"))
    # assert len(cs_files) > 0

# --- docs/codegen.md ---

def test_codegen_doc_references_generation_script() -> None: ...
def test_codegen_doc_references_demo_generated_output() -> None: ...

# --- Regression guards ---

def test_docs_codegen_md_still_exists() -> None: ...
def test_smoke_test_module_dir_still_exists() -> None: ...
def test_fixtures_generated_dir_still_exists() -> None: ...
```

### `support-baseline.json` Update — Exact JSON Snippets

**Add to `required_paths`** (after the last existing entry `tests/fixtures/settings/.gitkeep`):

```json
    { "path": "scripts/codegen", "type": "dir" },
    { "path": "scripts/codegen/generate-smoke-test.sh", "type": "file" },
    { "path": "demo", "type": "dir" },
    { "path": "demo/generated", "type": "dir" },
    { "path": "demo/generated/smoke_test", "type": "dir" }
```

**Add to `line_checks`** (after the last existing `docs/codegen.md` check — the `"Fixture settings path"` entry):

```json
    {
      "file": "docs/codegen.md",
      "label": "Codegen script invocation",
      "expected_line": "bash scripts/codegen/generate-smoke-test.sh"
    },
    {
      "file": "docs/codegen.md",
      "label": "Generated output location",
      "expected_line": "The script outputs generated C# bindings to `demo/generated/smoke_test/`."
    }
```

> **Note:** `"allow_multiple": true` is not needed for the codegen script line because the `bash scripts/codegen/generate-smoke-test.sh` line appears in code blocks in two places in the proposed `docs/codegen.md` template above (Quick Start and Regeneration sections). If `validate-foundation.py` flags a duplicate, add `"allow_multiple": true` to the `"Codegen script invocation"` check.

### Namespace and Addon Boundary

Generated C# bindings from `spacetime generate` use a namespace determined by the SpacetimeDB CLI — typically derived from the module name or database name. **Do not** manually add the `GodotSpacetime` namespace to generated files. Generated bindings live entirely outside the addon namespace contract (`GodotSpacetime.*` is for addon source only). The test suite does not assert anything about the namespace of generated files.

### Verification After Implementation

Run all four commands in order:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_1_6_generate_bindings.py
pytest -q
```

Expected outcomes:
- `validate-foundation.py` — exits 0 (new required paths and line_checks all resolve)
- `dotnet build` — 0 errors, 0 warnings (no addon C# source changes)
- `pytest tests/test_story_1_6_generate_bindings.py` — all tests pass
- `pytest -q` — full suite passes (stories 1.3 + 1.4 + 1.5 + 1.6 all green)

**Troubleshooting:**

- If `validate-foundation.py` fails on the new `line_checks`: verify the exact stripped lines in `docs/codegen.md` match the `expected_line` values in `support-baseline.json`. Even a trailing period or backtick difference causes a miss.
- If `test_smoke_test_cargo_toml_is_cdylib` fails: ensure Cargo.toml has `crate-type = ["cdylib"]` in that exact array literal form.
- If `test_generated_smoke_test_contains_cs_files` fails: the codegen was not run or its output was not staged. Run `bash scripts/codegen/generate-smoke-test.sh` (with `spacetime` CLI installed) and stage all files in `demo/generated/smoke_test/`.
- If `validate-foundation.py` flags `"allow_multiple"` on the `bash scripts/codegen/generate-smoke-test.sh` line: add `"allow_multiple": true` to that `line_check` entry in `support-baseline.json`.

### Git Context: Recent Commits

- `5e7c7eb` feat(story-1.5): Verify Future GDScript Continuity in Structure and Contracts — adds `docs/runtime-boundaries.md` GDScript seam update, 60-test continuity suite; 207 total tests passing
- `bd8acf3` feat(story-1.4): Isolate the .NET Runtime Adapter Behind Internal Boundaries — `Internal/Platform/DotNet/` adapters with `IDbConnection`, `SpacetimeDB.ClientSDK 2.1.0` PackageReference
- `12f19d9` feat(story-1.3): Define Runtime-Neutral Public SDK Concepts and Terminology — all `Public/` stubs, `docs/runtime-boundaries.md`

Story 1.6 is the first to touch `scripts/codegen/`, `spacetime/modules/smoke_test/src/`, and `demo/`. You are establishing conventions for these directories. Follow the general project patterns (snake_case filenames in `scripts/`, paths matching the architecture specification exactly).

### Project Structure for This Story

**Files to create:**
```
spacetime/modules/smoke_test/Cargo.toml              — Rust module manifest with cdylib + spacetimedb dep
spacetime/modules/smoke_test/src/lib.rs              — minimal SmokeTest table + ping reducer
scripts/codegen/generate-smoke-test.sh               — repeatable generation script
demo/generated/smoke_test/                           — committed C# output (one or more .cs files)
demo/generated/smoke_test/README.md                  — auto-generated artifact notice
tests/test_story_1_6_generate_bindings.py            — pytest verification suite
```

**Files to update:**
```
spacetime/modules/smoke_test/README.md               — replace placeholder with module description
docs/codegen.md                                      — replace placeholder with actual workflow
scripts/compatibility/support-baseline.json          — add new required_paths and line_checks
```

**Files to NOT touch:**
```
addons/godot_spacetime/src/**                        — addon source unchanged
docs/runtime-boundaries.md                          — GDScript seam doc; do not modify
docs/compatibility-matrix.md                        — no version changes
docs/install.md                                     — unchanged
.github/workflows/                                  — no CI changes
godot-spacetime.csproj                              — no build changes
tests/fixtures/generated/                           — reserved for Story 1.8+
spacetime/modules/compatibility_fixture/             — reserved for Story 1.8
tests/test_story_1_3_sdk_concepts.py                — no regressions to existing tests
tests/test_story_1_4_adapter_boundary.py            — no regressions to existing tests
tests/test_story_1_5_gdscript_continuity.py         — no regressions to existing tests
```

### Cross-Story Dependencies

- **Story 1.2** established `validate-foundation.py` and `support-baseline.json` — Story 1.6 extends both; never replaces or resets them
- **Story 1.7** reads the generated output from `demo/generated/smoke_test/` to explain schema concepts — the generated types must be valid, present, and stable
- **Story 1.8** validates binding/schema compatibility using `spacetime/modules/compatibility_fixture/` (separate from Story 1.6's smoke_test module) — do not conflate the two module inputs
- **Story 1.9** (first connection) will reference the generated bindings at runtime — ensure table name `smoke_test` and reducer name `ping` are stable

### References

- [Source: epics.md#Story 1.6] — Acceptance criteria and FR6/FR7 coverage
- [Source: architecture.md#Code Structure] — `scripts/codegen/`, `demo/generated/`, `spacetime/modules/` location decisions
- [Source: architecture.md#Data Boundaries] — "Generated bindings in demo/generated/ and tests/fixtures/generated/ are read-only artifacts"
- [Source: architecture.md#Requirements to Structure Mapping] — `docs/codegen.md`, `scripts/codegen/`, `spacetime/modules/`, `demo/generated/`, `tests/fixtures/generated/` as the Schema & Binding Workflow components
- [Source: docs/codegen.md] — Current placeholder content; the five exact preserved lines are listed verbatim in this story's Dev Notes
- [Source: scripts/compatibility/support-baseline.json] — Existing required_paths and line_checks; Task 5 appends to both sections
- [Source: spec-1-2] — Validation lane; Story 1.6 extends `support-baseline.json` following the same pattern
- [Source: spec-1-3] — Public/ namespace convention; generated bindings use a separate namespace
- [Source: spec-1-5] — Most recent prior story; test file patterns (`ROOT`, `_read`, `_lines`, no `_strip_cs_comments` needed here)
- [Source: spacetime/modules/smoke_test/README.md] — Current placeholder to replace in Task 1
- [Source: tests/fixtures/README.md] — Confirms `tests/fixtures/generated/` is separate from `demo/generated/`
- [Source: epic-1-context.md#Cross-Story Dependencies] — Story 1.6 through 1.9 dependency chain

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation completed without blockers.

### Completion Notes List

- Task 1: Created `spacetime/modules/smoke_test/Cargo.toml` with `crate-type = ["cdylib"]` and pinned `spacetimedb = "=1.12.0"` as the exact Story 1.6 codegen baseline compatible with the current CLI workflow. Created `src/lib.rs` using the flat `#[table]`/`#[reducer]` macro API that the installed toolchain compiles successfully, defining the `smoke_test` table and the `ping` no-op reducer. Updated `README.md` replacing the placeholder text.
- Task 2: Created `scripts/codegen/generate-smoke-test.sh` using the working `--module-path` flag for the installed `spacetime` CLI. The script now clears the output dir, regenerates the committed `README.md`, uses `set -euo pipefail`, builds through a temporary `CARGO_TARGET_DIR`, and removes the module-local `Cargo.lock` so reruns do not leave Rust build noise behind.
- Task 3: Ran `bash scripts/codegen/generate-smoke-test.sh` against the installed `spacetime` CLI — the workflow compiled the module and regenerated `Tables/SmokeTest.g.cs`, `Types/SmokeTest.g.cs`, `Reducers/Ping.g.cs`, and `SpacetimeDBClient.g.cs` while preserving `demo/generated/smoke_test/README.md` as part of the repeatable output set.
- Task 4: Replaced `docs/codegen.md` placeholder with full workflow doc. All five existing line_check lines preserved exactly, plus two new lines (`bash scripts/codegen/generate-smoke-test.sh` and `The script outputs generated C# bindings to \`demo/generated/smoke_test/\`.`).
- Task 5: Extended `support-baseline.json` with 5 new `required_paths` entries and 2 new `line_checks` entries. Added `"allow_multiple": true` to the codegen script invocation check (appears in two code blocks in docs/codegen.md).
- Task 6: Created `tests/test_story_1_6_generate_bindings.py` with 37 tests covering module source, codegen script, generated output, doc content, regeneration safeguards, and regression guards. All 37 pass.
- Task 7: All verification checks pass — `validate-foundation.py` exits 0, `dotnet build` 0 errors/0 warnings, `pytest -q tests/test_story_1_6_generate_bindings.py` 37/37 passed, `pytest -q` 244/244 passed.

### File List

**Created:**
- `spacetime/modules/smoke_test/Cargo.toml`
- `spacetime/modules/smoke_test/src/lib.rs`
- `scripts/codegen/generate-smoke-test.sh`
- `demo/generated/smoke_test/README.md`
- `demo/generated/smoke_test/SpacetimeDBClient.g.cs`
- `demo/generated/smoke_test/Tables/SmokeTest.g.cs`
- `demo/generated/smoke_test/Types/SmokeTest.g.cs`
- `demo/generated/smoke_test/Reducers/Ping.g.cs`
- `tests/test_story_1_6_generate_bindings.py`

**Modified:**
- `spacetime/modules/smoke_test/README.md`
- `docs/codegen.md`
- `scripts/compatibility/support-baseline.json`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- 2026-04-14: Story 1.6 implemented — created the `smoke_test` Rust module source, added the repeatable `scripts/codegen/generate-smoke-test.sh` workflow, committed the generated C# bindings under `demo/generated/smoke_test/`, updated `docs/codegen.md`, extended `scripts/compatibility/support-baseline.json`, and added `tests/test_story_1_6_generate_bindings.py`.
- 2026-04-14: Senior developer review auto-fix — pinned the Rust module dependency to the exact `spacetimedb` baseline, updated the codegen script to recreate the committed generated README and keep Cargo build artifacts out of the repo, hardened the story tests to cover the regeneration path, corrected the recorded verification counts to `37/37` and `244/244`, and marked the story done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 non-source automation artifact changes under `_bmad-output/`; excluded from the source review surface.

### Findings Fixed

- HIGH: `scripts/codegen/generate-smoke-test.sh` deleted the required `demo/generated/smoke_test/README.md` on every rerun because it cleared the whole output directory and never restored the committed notice file, so the documented regeneration path broke Task 3 and caused `pytest -q` to fail after regeneration.
- MEDIUM: `spacetime/modules/smoke_test/Cargo.toml` used `spacetimedb = "1.1"`, which is a semver range rather than an exact baseline pin, so the story did not actually guarantee reproducible code generation across machines.
- MEDIUM: The standard codegen workflow left module-local Rust build artifacts behind (`spacetime/modules/smoke_test/target/` from prior runs and `Cargo.lock` on each new run), creating avoidable git noise and story/file-list discrepancies after routine regeneration.
- MEDIUM: `tests/test_story_1_6_generate_bindings.py` did not cover the regeneration-specific contracts, so the README-deletion regression and build-artifact drift could pass the story-specific suite until the script was executed manually.
- MEDIUM: The Dev Agent Record overstated the verification evidence (`17/17` and `224/224`) relative to the current suite, reducing confidence in the review artifact.

### Actions Taken

- Updated `scripts/codegen/generate-smoke-test.sh` to recreate `demo/generated/smoke_test/README.md` after code generation, route Cargo build output through a temporary target directory, and clean up the module-local `Cargo.lock`.
- Pinned `spacetimedb` in `spacetime/modules/smoke_test/Cargo.toml` to `=1.12.0`, matching the working Story 1.6 baseline used by the installed CLI workflow.
- Hardened `tests/test_story_1_6_generate_bindings.py` to enforce the exact crate pin plus the regeneration and cleanup safeguards in the codegen script.
- Re-ran the live code generation workflow and removed the stale module-local `target/` directory left by earlier runs so the review finished from a clean story-specific source surface.
- Corrected the story Completion Notes, Change Log, and verification counts, then updated the story status and sprint tracking after the fixes validated cleanly.

### Validation

- `bash scripts/codegen/generate-smoke-test.sh`
- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest -q tests/test_story_1_6_generate_bindings.py`
- `pytest -q`

### Reference Check

- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `docs/codegen.md`
- Local reference: `spacetime/modules/smoke_test/Cargo.toml`
- Local reference: `scripts/codegen/generate-smoke-test.sh`
- MCP doc search: no resources available in this session
