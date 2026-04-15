# Story 5.4: Publish Core Installation and Runtime Documentation

Status: done

## Story

As an adopting developer,
I want documentation for installation, setup, code generation, connection flow, and runtime usage,
So that I can integrate the SDK self-serve in a supported Godot project.

## Acceptance Criteria

1. **Given** a fresh supported project and the addon source or a candidate addon artifact **When** I follow the published documentation **Then** I can install the addon, understand dependency expectations, generate bindings, configure the target deployment, and use the core runtime surfaces
2. **And** the docs clearly state the current supported Godot and SpacetimeDB version targets for that source or candidate artifact
3. **And** the docs reference the sample project as the canonical end-to-end example

## Tasks / Subtasks

- [x] Task 1: Update `docs/install.md` — add demo and runtime API cross-references (AC: 1, 3)
  - [x] 1.1 Add `demo/README.md` to the existing `## See Also` section with the description: `the canonical end-to-end sample covering install, code generation, connection, auth, subscriptions, and reducer interaction.`
  - [x] 1.2 Add `docs/runtime-boundaries.md` to `## See Also` with the description: `Full runtime API reference covering connection, auth, subscriptions, cache, reducers, and the complete public SDK concept vocabulary.`

- [x] Task 2: Update `docs/quickstart.md` — add demo and runtime API cross-references, add C# pattern note (AC: 1, 2, 3)
  - [x] 2.1 In Step 7 (Connect and Observe Lifecycle), after the existing GDScript snippet, add a note: `For the C# equivalent, see demo/DemoMain.cs — the demo project uses C# and mirrors this step.`
  - [x] 2.2 Add `demo/README.md` to the existing `## See Also` section with the description: `The canonical end-to-end sample. Mirrors these quickstart steps and extends them through auth, session resume, subscription, and reducer interaction.`
  - [x] 2.3 Add `docs/runtime-boundaries.md` to `## See Also` with the description: `Full runtime API reference covering connection, auth, subscriptions, cache, reducers, and the complete signal catalog.`

- [x] Task 3: Update `docs/connection.md` — add See Also section with API and demo references (AC: 1, 3)
  - [x] 3.1 Add a `## See Also` section at the end of the document containing:
    - `docs/runtime-boundaries.md` — Complete signal catalog, authentication, subscriptions, cache, reducers, and the full public SDK concept vocabulary.
    - `demo/README.md` — The canonical end-to-end sample demonstrating the full connection lifecycle from setup through reducer interaction.
    - `docs/quickstart.md` — Step-by-step first-setup guide that exercises connection lifecycle as part of the full onboarding flow.

- [x] Task 4: Update `docs/runtime-boundaries.md` — add canonical sample reference in intro (AC: 3)
  - [x] 4.1 After the opening paragraph ("This document defines the public concept vocabulary…"), add the sentence: `The canonical end-to-end implementation of these concepts is the sample project at \`demo/README.md\` and \`demo/DemoMain.cs\`.`

- [x] Task 5: Write `tests/test_story_5_4_publish_core_installation_and_runtime_documentation.py` (AC: 1, 2, 3)
  - [x] 5.1 Existence tests — all six core docs must be present:
    - `docs/install.md` exists
    - `docs/quickstart.md` exists
    - `docs/codegen.md` exists
    - `docs/connection.md` exists
    - `docs/runtime-boundaries.md` exists
    - `docs/compatibility-matrix.md` exists
  - [x] 5.2 `docs/install.md` content tests (AC: 2, 3):
    - Contains `4.6.2` (Godot version target stated)
    - Contains `8.0` (`.NET` version target stated)
    - Contains `2.1` (SpacetimeDB version target stated)
    - Contains `demo/README.md` (demo cross-reference present — AC3)
    - Contains `runtime-boundaries.md` (runtime API cross-reference present — AC1)
  - [x] 5.3 `docs/quickstart.md` content tests (AC: 1, 2, 3):
    - Contains `4.6.2` (Godot version target stated)
    - Contains `8.0` (`.NET` version target stated)
    - Contains `2.1` (SpacetimeDB version target stated)
    - Contains `demo/README.md` (demo cross-reference present — AC3)
    - Contains `runtime-boundaries.md` (runtime API cross-reference present — AC1)
    - Contains `demo/DemoMain.cs` (C# pattern reference present — AC1)
  - [x] 5.4 `docs/connection.md` content tests (AC: 1, 3):
    - Contains `See Also` (See Also section present)
    - Contains `runtime-boundaries.md` (runtime API cross-reference present — AC1)
    - Contains `demo/README.md` (demo cross-reference present — AC3)
  - [x] 5.5 `docs/runtime-boundaries.md` content tests (AC: 1, 3):
    - Contains `demo/README.md` (sample reference present — AC3)
    - Contains `demo/DemoMain.cs` (C# implementation reference present)
    - Contains `ConnectionState` (connection lifecycle API documented)
    - Contains `ITokenStore` (auth API documented)
    - Contains `SubscriptionHandle` (subscription API documented)
    - Contains `ReducerCallResult` (reducer success API documented)
    - Contains `ReducerCallError` (reducer failure API documented)
    - Contains `SpacetimeClient` (entry point documented)
    - Contains `GetRows` (cache API documented)
    - Contains `RowChanged` (row change signal documented)
    - Contains `InvokeReducer` (reducer invocation documented)
    - Contains `ReducerFailureCategory` (failure branching documented)
  - [x] 5.6 `docs/compatibility-matrix.md` content tests (AC: 2):
    - Contains `4.6.2` (Godot version target stated)
    - Contains `8.0` (`.NET` version target stated)
    - Contains `2.1` (SpacetimeDB version target stated)
  - [x] 5.7 Regression guards — all prior story deliverables must remain intact:
    - `docs/install.md` contains `Supported Foundation Baseline` (Story 1.1 section intact)
    - `docs/install.md` contains `validate-foundation.py` (Story 1.2 validation step intact)
    - `docs/quickstart.md` contains `Quickstart` (Story 1.10 structure intact)
    - `docs/quickstart.md` contains `SpacetimeSettings` (Story 1.9 config step intact)
    - `docs/quickstart.md` contains `SpacetimeClient` (Story 1.9 autoload step intact)
    - `docs/codegen.md` contains `generate-smoke-test.sh` (Story 1.6 script reference intact)
    - `docs/codegen.md` contains `demo/generated/smoke_test` (Story 1.6 output path intact)
    - `docs/connection.md` contains `ConnectionState` (Story 1.9 state table intact)
    - `docs/runtime-boundaries.md` contains `ReducerCallFailed` (Story 4.4 error model intact)
    - `docs/runtime-boundaries.md` contains `ITokenStore` (Story 2.1 auth interface intact)
    - `docs/runtime-boundaries.md` contains `SubscriptionApplied` (Story 3.1 subscription lifecycle intact)
    - `docs/runtime-boundaries.md` contains `RowChanged` (Story 3.3 row change signal intact)
    - `demo/README.md` exists (Story 5.1 sample intact)
    - `demo/DemoMain.cs` exists (Story 5.1 C# script intact)
    - `demo/DemoMain.cs` contains `ReducerCallSucceeded` (Story 5.3 reducer wiring intact)
    - `addons/godot_spacetime/src/Public/SpacetimeClient.cs` exists (SDK public boundary intact)

## Dev Notes

### What This Story Delivers

Story 5.4 completes the Epic 5 documentation surface. All the core docs were created or extended during implementation stories (1.x–4.x) and represent accurate, tested content. Story 5.4's job is to wire them together as a coherent self-serve adoption path for external developers and to reference the sample project (Stories 5.1–5.3) as the canonical end-to-end example.

**The four targeted doc edits:**
- `docs/install.md`: Add `demo/README.md` and `docs/runtime-boundaries.md` to "See Also"
- `docs/quickstart.md`: Add `demo/README.md`, `docs/runtime-boundaries.md` to "See Also"; add C# note in Step 7
- `docs/connection.md`: Add a full `## See Also` section (currently has none)
- `docs/runtime-boundaries.md`: Add one sentence after the intro paragraph pointing to the demo

**Why this matters for AC1–AC3:**
- AC1: Without the demo reference and runtime-boundaries.md in the installation path, there's no navigation link from "I installed the plugin" to "here is the complete runtime API I need for real usage." The quickstart → runtime-boundaries.md → demo path closes that gap.
- AC2: Version targets (`4.6.2`, `.NET 8+`, `2.1+`) are already declared in install.md, quickstart.md, and compatibility-matrix.md. The tests verify they stay there.
- AC3: Currently no core doc references `demo/README.md`. After this story, install.md, quickstart.md, connection.md, and runtime-boundaries.md all point to it.

**Scope boundaries:**
- Only `docs/install.md`, `docs/quickstart.md`, `docs/connection.md`, `docs/runtime-boundaries.md`, and the new test file are modified
- Do NOT touch `docs/codegen.md` or `docs/compatibility-matrix.md` — they are self-contained and complete
- Do NOT create `docs/troubleshooting.md` — that is Story 5.5 scope
- Do NOT create `docs/migration-from-community-plugin.md` — that is Story 5.6 scope
- Do NOT modify any `addons/`, `demo/`, or `spacetime/` files — documentation changes only

### Critical Architecture Constraints

**Do NOT recreate or restructure any doc:**
Each doc was created and extended by multiple prior implementation stories and has been validated by their test suites. This story adds to them; it does NOT refactor their structure or replace their content.

**Precise insertion points for each doc edit:**

`docs/install.md` — Existing `## See Also` section at the bottom:
```
- `docs/connection.md` for connection lifecycle states, signals, and editor status labels.
- `docs/quickstart.md` for the step-by-step first-setup workflow from install through first connection.
```
Add two entries after the existing two lines:
```
- `demo/README.md` for the canonical end-to-end sample covering install, code generation, connection, auth, subscriptions, and reducer interaction.
- `docs/runtime-boundaries.md` for the full runtime API reference covering connection, auth, subscriptions, cache, reducers, and the complete public SDK concept vocabulary.
```

`docs/quickstart.md` — Step 7 currently reads:
```gdscript
# In your scene script or autoload:
func _ready() -> void:
    SpacetimeClient.connection_state_changed.connect(_on_state_changed)
    SpacetimeClient.Connect()

func _on_state_changed(status: ConnectionStatus) -> void:
    print("Connection state: ", status.Description)
```
After the code block (before the next paragraph), add:
```
For the C# equivalent, see `demo/DemoMain.cs` — the demo project uses C# and mirrors this step.
```

`docs/quickstart.md` — Existing `## See Also` at the bottom:
```
docs/install.md
— Installation prerequisites, bootstrap steps, and foundation validation details.

docs/codegen.md
— Code generation, schema concepts, and module locations.

docs/connection.md
— Connection lifecycle states, signals, and editor status labels.
```
Add two entries after the existing three:
```
docs/runtime-boundaries.md
— Full runtime API reference covering connection, auth, subscriptions, cache, reducers, and the complete signal catalog.

demo/README.md
— The canonical end-to-end sample. Mirrors these quickstart steps and extends them through auth, session resume, subscription, and reducer interaction.
```

`docs/connection.md` — The document currently ends at line 32 (the `DEGRADED` state panel label). Append a new section:
```
## See Also

- `docs/runtime-boundaries.md` — Complete signal catalog, authentication, subscriptions, cache, reducers, and the full public SDK concept vocabulary.
- `demo/README.md` — The canonical end-to-end sample demonstrating the full connection lifecycle from setup through reducer interaction.
- `docs/quickstart.md` — Step-by-step first-setup guide that exercises connection lifecycle as part of the full onboarding flow.
```

`docs/runtime-boundaries.md` — The document opens with:
```
# Runtime Boundaries — GodotSpacetime SDK Concepts

This document defines the public concept vocabulary for the GodotSpacetime SDK. All public API docs, sample guidance, and architecture notes use this terminology. You do not need to know how the first shipping runtime works to use this SDK because those implementation details stay behind the runtime boundary.
```
After that opening paragraph, insert:
```
The canonical end-to-end implementation of these concepts is the sample project at `demo/README.md` and `demo/DemoMain.cs`.
```

**Do NOT change content that is verified by prior story tests.** Any existing regression tests from Stories 1.x–5.3 check for specific strings in these docs. Adding to the `See Also` sections and inserting the one-sentence sample reference cannot break those checks.

### Project Structure Notes

**Files to modify:**
- `docs/install.md` — append two "See Also" entries
- `docs/quickstart.md` — add C# note in Step 7 and two "See Also" entries
- `docs/connection.md` — append `## See Also` section (currently absent)
- `docs/runtime-boundaries.md` — insert one sentence after opening paragraph

**Files to create:**
- `tests/test_story_5_4_publish_core_installation_and_runtime_documentation.py` — new test file

**Files NOT to touch:**
- `docs/codegen.md` — complete and self-contained; no changes needed
- `docs/compatibility-matrix.md` — complete and self-contained; no changes needed
- `demo/README.md` — story 5.1–5.3 deliverable; not modified here
- `demo/DemoMain.cs` — story 5.3 deliverable; not modified here
- `addons/` — SDK addon code is out of scope
- `spacetime/` — Rust module source is out of scope

**Architecture docs directory structure (existing):**
```
docs/
├── install.md            ← MODIFIED (Task 1) — add See Also entries
├── quickstart.md         ← MODIFIED (Task 2) — add C# note + See Also entries
├── codegen.md            ← unchanged
├── connection.md         ← MODIFIED (Task 3) — add See Also section
├── runtime-boundaries.md ← MODIFIED (Task 4) — add sample reference sentence
└── compatibility-matrix.md  ← unchanged
```

### Test File Conventions (from Stories 5.1–5.3)

Tests are static file analysis using `pathlib.Path` — no Godot runtime, no pytest fixtures:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")
```

Test function names: `test_<file_slug>_<what_is_checked>`. All assertions include a descriptive failure message string.

For existence checks:
```python
def test_docs_install_md_exists():
    assert (ROOT / "docs/install.md").exists(), "docs/install.md must exist"
```

For content checks:
```python
def test_install_md_references_demo_readme():
    content = _read("docs/install.md")
    assert "demo/README.md" in content, "docs/install.md must reference demo/README.md (AC3)"
```

### References

- Story user story and AC: `_bmad-output/planning-artifacts/epics.md`, Epic 5 § Story 5.4
- FR28: "Developers can find documentation for installation, setup, binding generation, connection flow, and runtime usage." [Source: `_bmad-output/planning-artifacts/prd.md` § Documentation, Troubleshooting & Migration]
- Architecture doc structure: `_bmad-output/planning-artifacts/architecture.md` § Complete Project Directory Structure
- Architecture FR mapping (SDK Installation & Onboarding, Documentation): `_bmad-output/planning-artifacts/architecture.md` § Requirements to Structure Mapping
- `docs/install.md` — existing, complete (Stories 1.1, 1.2)
- `docs/quickstart.md` — existing, complete (Story 1.10)
- `docs/codegen.md` — existing, complete (Stories 1.6, 1.7)
- `docs/connection.md` — existing, minimal (Story 1.9)
- `docs/runtime-boundaries.md` — existing, comprehensive (Stories 1.3, 2.x, 3.x, 4.x)
- `docs/compatibility-matrix.md` — existing, complete (Story 1.8)
- `demo/README.md` — canonical sample (Stories 5.1, 5.2, 5.3)
- `demo/DemoMain.cs` — C# implementation reference (Stories 5.1, 5.2, 5.3)
- Previous story (5.3): `_bmad-output/implementation-artifacts/5-3-demonstrate-reducer-interaction-and-troubleshooting-comparison-paths.md`
- Previous story test baseline: 1659 tests passing (from Story 5.3 senior review)
- NFR16: Reproducible onboarding path [Source: epics.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `pytest -q tests/test_story_5_4_publish_core_installation_and_runtime_documentation.py`
- `pytest -q`

### Completion Notes List

- Task 1 (docs/install.md): Appended two See Also entries — `demo/README.md` and `docs/runtime-boundaries.md`. Exact insertion point: after the two existing See Also bullets. No other content changed.
- Task 2 (docs/quickstart.md): Added C# note after Step 7 GDScript snippet referencing `demo/DemoMain.cs`; appended `docs/runtime-boundaries.md` and `demo/README.md` entries to existing See Also section. No other content changed.
- Task 3 (docs/connection.md): Appended a new `## See Also` section (document previously had none) with three entries: `runtime-boundaries.md`, `demo/README.md`, `docs/quickstart.md`.
- Task 4 (docs/runtime-boundaries.md): Inserted one sentence after the opening paragraph pointing to `demo/README.md` and `demo/DemoMain.cs`. No other content changed.
- Task 5 (test file): The story 5.4 contract suite now contains 66 static analysis tests. Senior review hardening added exact placement/order assertions for `docs/install.md` `## See Also`, `docs/quickstart.md` Step 7 and `## See Also`, `docs/connection.md` `## See Also`, and the `docs/runtime-boundaries.md` intro insertion. Validation: `pytest -q tests/test_story_5_4_publish_core_installation_and_runtime_documentation.py` → `66 passed`; `pytest -q` → `1725 passed`.

### File List

- `docs/install.md` — modified (Task 1): added two See Also entries
- `docs/quickstart.md` — modified (Task 2): added C# note in Step 7, added two See Also entries
- `docs/connection.md` — modified (Task 3): added new See Also section
- `docs/runtime-boundaries.md` — modified (Task 4): inserted sample reference sentence after opening paragraph
- `tests/test_story_5_4_publish_core_installation_and_runtime_documentation.py` — created and review-hardened (Task 5): 66 tests

### Senior Developer Review (AI)

- Reviewer: Codex (GPT-5) on 2026-04-14
- Outcome: Approve
- Story Context: No separate story-context artifact was found; review used the story file, planning architecture, public SDK sources, and the modified docs/tests as the primary sources.
- Epic Tech Spec: No separate epic tech spec artifact was found; `_bmad-output/planning-artifacts/architecture.md` was used for structure and standards context.
- Tech Stack Reviewed: Godot `4.6.2`, `.NET 8+`, SpacetimeDB `2.1+`, Python `pytest` static contract tests.
- External References: No MCP/web lookup used; repository primary sources were sufficient for this review scope and network access is restricted in this environment.
- Findings fixed:
  - MEDIUM: `tests/test_story_5_4_publish_core_installation_and_runtime_documentation.py` only presence-checked the new doc cross-references, so regressions in `## See Also` placement or exact required descriptions could pass unnoticed. Fixed with section/order contract tests for `docs/install.md`, `docs/quickstart.md`, and `docs/connection.md`.
  - MEDIUM: The story-required placement of the Step 7 C# note and the `docs/runtime-boundaries.md` intro sentence was not verified. Fixed with ordered placement assertions that lock both insertion points.
  - MEDIUM: This story record claimed a 51-test file and a `1710/1710` passing suite, but the actual baseline under review was 61 passing story tests. Corrected the record after hardening and rerunning validation (`66` story tests, `1725` full-suite tests).
- Validation:
  - `pytest -q tests/test_story_5_4_publish_core_installation_and_runtime_documentation.py`
  - `pytest -q`

## Change Log

- 2026-04-14: Wired docs/install.md, docs/quickstart.md, docs/connection.md, and docs/runtime-boundaries.md together as a coherent adoption path by adding See Also cross-references and a C# demo pointer; created the Story 5.4 static analysis suite.
- 2026-04-14: Senior review hardened the Story 5.4 contract tests around exact section placement and ordering, corrected stale story metadata, reran validation (`66` story tests, `1725` full-suite tests), and marked the story done.
