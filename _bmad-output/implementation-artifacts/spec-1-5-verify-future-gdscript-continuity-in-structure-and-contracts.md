---
title: '1.5 Verify Future GDScript Continuity in Structure and Contracts'
type: 'feature'
created: '2026-04-14T00:00:00-07:00'
status: 'done'
baseline_commit: 'bd8acf3'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-2-establish-baseline-build-and-workflow-validation-early.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-3-define-runtime-neutral-public-sdk-concepts-and-terminology.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-4-isolate-the-net-runtime-adapter-behind-internal-boundaries.md'
---

# Story 1.5: Verify Future `GDScript` Continuity in Structure and Contracts

Status: done

## Story

As the SDK maintainer,
I want explicit proof that a later native `GDScript` runtime can extend the same product model,
So that future expansion does not require rewriting the public contract.

## Acceptance Criteria

1. **Given** the v1 runtime is `.NET`, **when** future-runtime continuity is reviewed, **then** the architecture identifies a documented extension seam a later native `GDScript` runtime would implement — specifically naming `Internal/Platform/GDScript/` as the intended repository location.
2. **And** the committed public concepts and docs do not need renaming or redefinition to support that later runtime — `Public/` type names contain no `.NET`-specific or runtime-bound terms (e.g., `DotNet`, `CSharp`, `Managed`).
3. **And** `docs/runtime-boundaries.md` names `Internal/Platform/GDScript/` as the intended repository location for a future native `GDScript` runtime implementation, with an explicit statement that the `Public/` contract is already runtime-neutral.

## Deliverables

This story has two concrete outputs:

1. **`docs/runtime-boundaries.md` update** — update the "Future Runtime Seam" section to replace the vague `Internal/Platform/Native/` example with the concrete `Internal/Platform/GDScript/` path, add an explicit statement that `Public/` type names are already runtime-neutral, and remove the forward-referencing "Story 1.5 validates…" placeholder left by Story 1.4
2. **`tests/test_story_1_5_gdscript_continuity.py`** — continuity contract tests proving the seam is documented and the public contract is already runtime-neutral

No C# source files are created or modified. This story is documentation and structural validation only.

## Tasks / Subtasks

- [x] Task 1 — Update `docs/runtime-boundaries.md` Future Runtime Seam section (AC: 1, 3)
  - [x] Find the `## Future Runtime Seam` section (currently around line 119)
  - [x] Replace the block including the vague `(e.g., Internal/Platform/Native/)` example with the updated block shown in Dev Notes below — this changes the example to the concrete `Internal/Platform/GDScript/` path
  - [x] Add an explicit statement that `Public/` type names (`ConnectionState`, `ITokenStore`, `SubscriptionHandle`, `ReducerCallResult`, etc.) carry no `.NET`-specific language and do not need renaming for a `GDScript` runtime
  - [x] Remove the self-referential "Story 1.5 validates that the GDScript continuity contract holds across this boundary." sentence (it was a placeholder; after this story it belongs in the dev record, not in shipped docs)
  - [x] Verify the rest of `docs/runtime-boundaries.md` is unchanged

- [x] Task 2 — Create `tests/test_story_1_5_gdscript_continuity.py` (AC: 1, 2, 3)
  - [x] Test AC 1/3: `docs/runtime-boundaries.md` contains a `## Future Runtime Seam` heading
  - [x] Test AC 3: `docs/runtime-boundaries.md` contains the literal path `Internal/Platform/GDScript/`
  - [x] Test AC 3: the path appears as a concrete named location, not preceded by `e.g.,`
  - [x] Test AC 2: no `Public/` C# filename contains runtime-bound terms (`DotNet`, `CSharp`, `Managed`, `NET`) — using `pytest.mark.parametrize` over the file list from Story 1.3
  - [x] Test AC 2: no `Public/` C# `namespace` declaration contains `DotNet`, `CSharp`, or `Managed`
  - [x] Test AC 2: no `Public/` C# type name (class/enum/interface/record declaration line) contains `DotNet`, `CSharp`, or `Managed`
  - [x] Regression guard: re-assert `docs/runtime-boundaries.md` exists (extends Story 1.3 coverage)
  - [x] Regression guard: re-assert all expected `Public/` stub files from Story 1.3 still exist

- [x] Task 3 — Verify all checks pass (AC: all)
  - [x] Run `python3 scripts/compatibility/validate-foundation.py` — exits 0 (no monitored lines are changing so this should stay green without any support-baseline.json changes)
  - [x] Run `dotnet build godot-spacetime.sln -c Debug` — succeeds with 0 errors and 0 warnings
  - [x] Run `pytest tests/test_story_1_5_gdscript_continuity.py` — all tests pass
  - [x] Run `pytest -q` — full suite still green

## Dev Notes

### What This Story Is (and Is Not)

**This story is documentation finalization and structural contract verification.** Story 1.4 created the Platform isolation zone and left a forward-referencing placeholder in `docs/runtime-boundaries.md`. Story 1.5 closes that placeholder and provides automated proof that the GDScript continuity contract already holds.

- **DO**: Update the "Future Runtime Seam" section in `docs/runtime-boundaries.md`. Write continuity tests.
- **DO NOT**: Create any C# source files. Modify `Public/` stubs. Modify `Internal/Platform/DotNet/` adapters. Modify `support-baseline.json` (no monitored lines are changing). Modify `docs/compatibility-matrix.md`. Touch `.github/workflows/`.

### Exact `docs/runtime-boundaries.md` Change

The current `## Future Runtime Seam` section reads:

```markdown
## Future Runtime Seam

`addons/godot_spacetime/src/Internal/Platform/` is the designated location for future runtime implementations. The `.NET` adapter currently lives in `Internal/Platform/DotNet/`. A future runtime adapter would be added as a sibling (e.g., `Internal/Platform/Native/`) and selected at build or load time without changing the public API.

This seam is reserved by architecture decision. Story 1.5 validates that the GDScript continuity contract holds across this boundary.
```

Replace the entire section (heading through the last paragraph) with:

```markdown
## Future Runtime Seam

`addons/godot_spacetime/src/Internal/Platform/` is the designated location for future runtime implementations. The `.NET` adapter lives in `Internal/Platform/DotNet/`. A future native `GDScript` runtime adapter would be added at `Internal/Platform/GDScript/` and selected at build or load time without changing the public API.

The `Public/` contract is already runtime-neutral. None of the public type names (`ConnectionState`, `ITokenStore`, `SubscriptionHandle`, `SubscriptionAppliedEvent`, `ReducerCallResult`, `ReducerCallError`, `SpacetimeSettings`, `SpacetimeClient`, `LogCategory`) carry `.NET`-specific implementation language. A later native `GDScript` runtime does not require renaming or redefining any of these public concepts.
```

Nothing else in `docs/runtime-boundaries.md` changes.

### Test File — Key Patterns

Follow the exact pattern established by `tests/test_story_1_3_sdk_concepts.py` and `tests/test_story_1_4_adapter_boundary.py`:

```python
ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "addons" / "godot_spacetime" / "src" / "Public"

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")
```

Use `pytest.mark.parametrize` for the multi-file assertions (same pattern as `test_story_1_3_sdk_concepts.py`).

**Runtime-neutral term check — strip comments before asserting:**

Use the same comment-stripping approach from `tests/test_story_1_4_adapter_boundary.py` when checking for forbidden terms in C# files:

```python
def _strip_cs_comments(source: str) -> str:
    # Remove block comments /* ... */
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    # Remove line comments // ...
    source = re.sub(r"//[^\n]*", "", source)
    return source
```

Then check for `.NET`-specific terms only in the comment-stripped source. This prevents false positives from `/// <summary>` doc-comments that legitimately describe the `.NET` runtime (since Public/ types document what they are vis-à-vis the runtime adapter).

**Forbidden terms in Public/ type/class/enum/interface/record declarations (comment-stripped):**

Check the declaration line only (line containing `class `, `enum `, `interface `, `record `, `struct `) — not the entire file body. The goal is to ensure the TYPE NAME is runtime-neutral. Example:

```python
RUNTIME_BOUND_TERMS = ["DotNet", "CSharp", "Managed"]

for cs_file in PUBLIC.rglob("*.cs"):
    source = _strip_cs_comments(cs_file.read_text(encoding="utf-8"))
    for line in source.splitlines():
        stripped = line.strip()
        if re.search(r'\b(class|enum|interface|record|struct)\b', stripped):
            for term in RUNTIME_BOUND_TERMS:
                assert term not in stripped, (
                    f"Public type declaration in {cs_file.name} contains "
                    f"runtime-bound term '{term}': {stripped!r}"
                )
```

**GDScript seam document check:**

```python
def test_runtime_boundaries_names_gdscript_seam() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Internal/Platform/GDScript/" in content, (
        "docs/runtime-boundaries.md must name Internal/Platform/GDScript/ "
        "as the intended future GDScript runtime location (AC #3)"
    )

def test_gdscript_seam_is_concrete_not_example() -> None:
    content = _read("docs/runtime-boundaries.md")
    # Confirm the path appears without being preceded by "e.g.,"
    # (story 1.4 left the location as an example; story 1.5 makes it concrete)
    lines = content.splitlines()
    for line in lines:
        if "Internal/Platform/GDScript/" in line:
            assert "e.g." not in line, (
                "Internal/Platform/GDScript/ must appear as a concrete "
                "named location, not as an example (AC #3)"
            )
            return
    pytest.fail("Internal/Platform/GDScript/ not found in docs/runtime-boundaries.md")
```

### `support-baseline.json` — No Changes Required

`docs/runtime-boundaries.md` is listed in `required_paths` (file existence check only). There are no `line_checks` for that file. Since we are adding new content rather than changing a monitored line, `validate-foundation.py` will stay green without touching `support-baseline.json`.

If a future story wants to monitor the GDScript seam line, it can add a `line_check` entry at that point. Do **not** add one here.

### Existing Public/ Types Confirmed Runtime-Neutral (Story 1.3 / Story 1.4 Context)

From `addons/godot_spacetime/src/Public/`:

| File | Type Name | Namespace | Runtime-Neutral? |
|------|-----------|-----------|-----------------|
| `Connection/ConnectionState.cs` | `ConnectionState` enum | `GodotSpacetime.Connection` | ✅ |
| `Connection/ConnectionStatus.cs` | `ConnectionStatus` record | `GodotSpacetime.Connection` | ✅ |
| `Connection/ConnectionOpenedEvent.cs` | `ConnectionOpenedEvent` record | `GodotSpacetime.Connection` | ✅ |
| `Auth/ITokenStore.cs` | `ITokenStore` interface | `GodotSpacetime.Auth` | ✅ |
| `Subscriptions/SubscriptionHandle.cs` | `SubscriptionHandle` record/class | `GodotSpacetime.Subscriptions` | ✅ |
| `Subscriptions/SubscriptionAppliedEvent.cs` | `SubscriptionAppliedEvent` record | `GodotSpacetime.Subscriptions` | ✅ |
| `Reducers/ReducerCallResult.cs` | `ReducerCallResult` record | `GodotSpacetime.Reducers` | ✅ |
| `Reducers/ReducerCallError.cs` | `ReducerCallError` record | `GodotSpacetime.Reducers` | ✅ |
| `Logging/LogCategory.cs` | `LogCategory` enum | `GodotSpacetime.Logging` | ✅ |
| `SpacetimeSettings.cs` | `SpacetimeSettings` resource | `GodotSpacetime` | ✅ |
| `SpacetimeClient.cs` | `SpacetimeClient` node | `GodotSpacetime` | ✅ |

All type names and namespaces are already free of `.NET`-specific language. The tests in Task 2 enforce this contract going forward.

### Platform Zone Structure (Story 1.4 Context)

```
addons/godot_spacetime/src/Internal/Platform/
└── DotNet/                          ← current .NET adapter zone
    ├── SpacetimeSdkConnectionAdapter.cs    (stub, implemented in Story 1.9)
    ├── SpacetimeSdkSubscriptionAdapter.cs  (stub, implemented in later story)
    └── SpacetimeSdkReducerAdapter.cs       (stub, implemented in later story)
```

After Story 1.5, the documentation will declare:
```
addons/godot_spacetime/src/Internal/Platform/
├── DotNet/       ← current .NET adapter (SpacetimeDB.ClientSDK)
└── GDScript/     ← RESERVED: future native GDScript runtime (not created in this story)
```

The `GDScript/` directory is **documented only** in this story — not physically created. Creating an empty directory would add noise to the repo before any implementation exists.

### Namespace Convention (Inherited from Story 1.4)

The `Internal/` folder maps to `Runtime` in the C# namespace. A future GDScript adapter would follow the same pattern:

| Folder | Namespace |
|--------|-----------|
| `src/Internal/Platform/DotNet/` | `GodotSpacetime.Runtime.Platform.DotNet` |
| `src/Internal/Platform/GDScript/` (future) | `GodotSpacetime.Runtime.Platform.GDScript` |

This is documented in `spec-1-4` Dev Notes and should not be re-invented.

### Critical: `IDbConnection` in Story 1.4 Adapters

Story 1.4 discovered that `SpacetimeDB.ClientSDK` 2.1.0 exposes `IDbConnection` (interface), not a concrete `DbConnection` class. The three adapter stubs use `private IDbConnection? _dbConnection;`. This is relevant if any future story reads these adapters — do not be confused by the fact that the architecture doc mentions `DbConnection` by name in some places; the actual SDK type is the interface.

### Verification After Implementation

Run all four in order:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_1_5_gdscript_continuity.py
pytest -q
```

Expected outcomes:
- `validate-foundation.py` — exits 0 (no baseline changes)
- `dotnet build` — 0 errors, 0 warnings (no C# changes)
- `pytest tests/test_story_1_5_gdscript_continuity.py` — all tests pass
- `pytest -q` — full suite passes (stories 1.3 + 1.4 + 1.5 tests)

If `test_gdscript_seam_is_concrete_not_example` fails after the update, confirm the section replacement in Task 1 removed the `e.g.,` qualifier from the GDScript path line.

### Git Context: Recent Commits

- `bd8acf3` feat(story-1.4): Isolate the .NET Runtime Adapter Behind Internal Boundaries — creates `Internal/Platform/DotNet/` adapters, adds `SpacetimeDB.ClientSDK 2.1.0` PackageReference, 47 isolation tests
- `12f19d9` feat(story-1.3): Define Runtime-Neutral Public SDK Concepts and Terminology — creates all `Public/` stubs and `docs/runtime-boundaries.md`

Story 1.5 patterns that continue from prior work:
- Test file naming: `tests/test_story_1_5_gdscript_continuity.py`
- Test helpers: `ROOT`, `_read()`, `_lines()`, `_strip_cs_comments()` from prior files
- No modification to any file not explicitly listed in deliverables

### Project Structure for This Story

**Files to update:**
```
docs/runtime-boundaries.md                         — update Future Runtime Seam section
```

**Files to create:**
```
tests/test_story_1_5_gdscript_continuity.py        — continuity contract test suite
```

**Files to NOT touch:**
```
addons/godot_spacetime/src/Public/**/*.cs           — runtime-neutral; tests prove this, no changes needed
addons/godot_spacetime/src/Internal/Platform/DotNet/  — adapter stubs from Story 1.4; do not modify
docs/compatibility-matrix.md                        — no version changes
scripts/compatibility/support-baseline.json         — no monitored lines changing
.github/workflows/                                  — no CI changes
godot-spacetime.csproj                              — no build changes
```

### References

- [Source: epics.md#Story 1.5] — Acceptance criteria and FR40/FR42 coverage
- [Source: architecture.md#Architectural Boundaries] — `Internal/Platform/DotNet/` is the only SpacetimeDB.* zone; `Internal/Platform/` is the designated future runtime location
- [Source: architecture.md#Multi-Runtime Product Continuity] — "future native GDScript runtime must preserve connection, auth, subscription, cache, and reducer concepts"
- [Source: architecture.md#API & Communication Patterns] — "Multi-runtime continuity: future native GDScript runtime must preserve… even if implementation details diverge"
- [Source: docs/runtime-boundaries.md#Future Runtime Seam] — current text with Story 1.5 placeholder to be replaced
- [Source: spec-1-3] — Canonical Public/ type list and namespace table
- [Source: spec-1-4] — Namespace table for Internal/ types; `IDbConnection` discovery note; test comment-stripping pattern
- [Source: tests/test_story_1_3_sdk_concepts.py] — Test file pattern to follow (parametrize, _read, _lines helpers)
- [Source: tests/test_story_1_4_adapter_boundary.py] — `_strip_cs_comments` comment-safe reference detection pattern

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Task 1 complete: Updated `docs/runtime-boundaries.md` — replaced the `## Future Runtime Seam` section to name `Internal/Platform/GDScript/` as the concrete future runtime location, added explicit statement that `Public/` type names are already runtime-neutral, and removed the Story 1.5 placeholder sentence.
- Task 2 complete: Created `tests/test_story_1_5_gdscript_continuity.py` — 60 tests covering all three ACs: `## Future Runtime Seam` section presence, `Internal/Platform/GDScript/` as a concrete seam inside that section, no legacy generic future-runtime examples elsewhere in `docs/runtime-boundaries.md`, no runtime-bound terms in `Public/` filenames/namespaces/type declarations, plus regression guards for Story 1.3 deliverables.
- Task 3 complete: All four validation commands pass — `validate-foundation.py` exits 0 (no baseline changes needed), `dotnet build` 0 errors 0 warnings (no C# files touched), `pytest tests/test_story_1_5_gdscript_continuity.py` 60/60 pass, `pytest -q` 207/207 pass.
- All ACs satisfied: architecture identifies `Internal/Platform/GDScript/` as the documented extension seam (AC 1); all `Public/` type names confirmed free of `.NET`-specific language by automated tests (AC 2); `docs/runtime-boundaries.md` names the concrete path with explicit runtime-neutral statement (AC 3).

### File List

- `docs/runtime-boundaries.md` — updated `## Future Runtime Seam` section
- `tests/test_story_1_5_gdscript_continuity.py` — new continuity contract test suite (60 tests)

## Change Log

- 2026-04-14: Story 1.5 implemented — updated `docs/runtime-boundaries.md` Future Runtime Seam section to name `Internal/Platform/GDScript/` as the concrete future runtime location and declare the `Public/` contract runtime-neutral; created `tests/test_story_1_5_gdscript_continuity.py` continuity contract suite; all validations pass.
- 2026-04-14: Senior developer review auto-fix — aligned the runtime-isolation prose with the concrete future `GDScript` seam, tightened the continuity tests to keep the seam in the `## Future Runtime Seam` section and reject legacy future-runtime examples, corrected the recorded verification counts to `60/60` and `207/207`, and marked the story done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 non-source automation artifact changes under `_bmad-output/`; excluded from the source review surface.

### Findings Fixed

- MEDIUM: `docs/runtime-boundaries.md` still described the future runtime generically as a `GDNative` or `GDExtension` implementation in the runtime-isolation section, which diluted Story 1.5's concrete `Internal/Platform/GDScript/` continuity seam.
- MEDIUM: `tests/test_story_1_5_gdscript_continuity.py` only proved that `Internal/Platform/GDScript/` appeared somewhere in the document; it did not verify that the path lived in the `## Future Runtime Seam` section the story actually updates.
- MEDIUM: The Story 1.5 continuity tests allowed legacy generic future-runtime examples (`Internal/Platform/Native/`, `GDNative`, `GDExtension`) to remain elsewhere in `docs/runtime-boundaries.md`, so the document could drift while the suite stayed green.
- MEDIUM: The Dev Agent Record overstated the verification evidence (`48/48` and `195/195`) relative to the current suite, reducing trust in the reviewable artifact.

### Actions Taken

- Updated `docs/runtime-boundaries.md` so both runtime-boundary paragraphs now point to the future native `GDScript` seam instead of mixing generic legacy runtime examples with the concrete contract.
- Hardened `tests/test_story_1_5_gdscript_continuity.py` to verify the `Internal/Platform/GDScript/` path appears inside the `## Future Runtime Seam` section and to reject legacy future-runtime examples anywhere in the document.
- Corrected the story Completion Notes, File List counts, and Change Log so the artifact now matches the current 60-test Story 1.5 suite and the 207-test full suite.
- Updated the story status and sprint-tracking status after the fixes and verification completed cleanly.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest -q tests/test_story_1_5_gdscript_continuity.py`
- `pytest -q`

### Reference Check

- Local reference: `_bmad-output/planning-artifacts/architecture.md` (`Requirements Overview`, `API & Communication Patterns`)
- Local reference: `docs/runtime-boundaries.md`
- MCP doc search: no resources available in this session
