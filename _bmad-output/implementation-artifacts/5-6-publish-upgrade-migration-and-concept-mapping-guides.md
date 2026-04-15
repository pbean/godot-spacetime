# Story 5.6: Publish Upgrade, Migration, and Concept-Mapping Guides

Status: done

## Story

As a developer adopting or upgrading the SDK,
I want upgrade and migration guides that explain how this SDK maps to official SpacetimeDB concepts,
So that I can move from older setups or unofficial integrations without losing the mental model.

## Acceptance Criteria

1. **Given** an adopter is upgrading SDK versions or moving from custom or community integration code **When** they follow the published migration guidance **Then** they can identify the supported upgrade path between SDK releases
2. **And** they can understand the recommended migration path from custom protocol work or the community plugin to this SDK
3. **And** the guide explains how the Godot-facing model relates to official SpacetimeDB concepts and how future `GDScript` support fits the same product model

## Tasks / Subtasks

- [x] Task 1: Write `docs/migration-from-community-plugin.md` covering all three FR areas (AC: 1, 2, 3)
  - [x] 1.1 Opening paragraph — state purpose and scope (upgrade, migration, concept mapping); cross-reference `docs/runtime-boundaries.md` and `docs/compatibility-matrix.md` as authoritative sources
  - [x] 1.2 `## Upgrade Path Between SDK Releases` — steps to upgrade to a new SDK version; reference `docs/compatibility-matrix.md` for version baseline; cover plugin folder replacement, binding regeneration, compat panel check, and foundation validation (AC: 1)
  - [x] 1.3 `## Migration from the Community Plugin` — tables mapping community plugin patterns (`DbConnection.Builder()`, subscription builder, direct reducer methods, `connection.Db.*`) to this SDK equivalents (`SpacetimeClient` autoload, `SpacetimeSettings`, `Subscribe()`, `InvokeReducer()`, `GetRows()`, signals) (AC: 2)
  - [x] 1.4 `## Migration from Custom Protocol Work` — numbered steps to migrate from raw `SpacetimeDB.ClientSDK` or WebSocket code to this SDK; reference `demo/README.md` and `demo/DemoMain.cs` for the canonical end-to-end wiring example (AC: 2)
  - [x] 1.5 `## Godot SDK Model and SpacetimeDB Concepts` — concept mapping table: SpacetimeDB concept → this SDK equivalent, with `docs/runtime-boundaries.md` references for each row (AC: 3)
  - [x] 1.6 `## Multi-Runtime Product Model` — explain that `.NET` is the first delivery but the API model is Godot-native; state that signal names, autoload configuration, and `SpacetimeSettings` will remain stable when `GDScript` support ships; adopters' scene wiring transfers without change (AC: 3)
  - [x] 1.7 `## See Also` — cross-references to `docs/runtime-boundaries.md`, `docs/compatibility-matrix.md`, `docs/install.md`, `docs/quickstart.md`, `docs/troubleshooting.md`, `demo/README.md`

- [x] Task 2: Write `tests/test_story_5_6_publish_upgrade_migration_and_concept_mapping_guides.py` (AC: 1, 2, 3)
  - [x] 2.1 Existence test: `docs/migration-from-community-plugin.md` exists
  - [x] 2.2 Section presence tests — all six sections present: Upgrade Path Between SDK Releases, Migration from the Community Plugin, Migration from Custom Protocol Work, Godot SDK Model and SpacetimeDB Concepts, Multi-Runtime Product Model, See Also
  - [x] 2.3 FR30 upgrade content tests (AC: 1): contains `addons/godot_spacetime/`; contains `generate-smoke-test.sh`; contains `validate-foundation.py`; contains `INCOMPATIBLE`; contains `docs/compatibility-matrix.md` in upgrade section
  - [x] 2.4 FR31 community plugin content tests (AC: 2): contains `DbConnection.Builder()`; contains `SpacetimeSettings`; contains `SpacetimeClient.Subscribe`; contains `InvokeReducer`; contains `GetRows`; contains `ITokenStore`
  - [x] 2.5 FR31 signal migration tests (AC: 2): contains `ReducerCallFailed`; contains `ReducerCallSucceeded`; contains `SubscriptionApplied`; contains `SubscriptionFailed`
  - [x] 2.6 FR31 custom protocol content tests (AC: 2): contains `SpacetimeDB.ClientSDK` (or equivalent reference); contains `demo/DemoMain.cs`; contains `demo/README.md` in migration context
  - [x] 2.7 FR32 concept mapping table tests (AC: 3): contains `DbConnection` in concept mapping section; contains `SubscriptionHandle` in concept mapping; contains `RowChanged`; contains `ReducerCallError`; contains `IReducerArgs`
  - [x] 2.8 FR32 multi-runtime content tests (AC: 3): contains `GDScript`; contains signal stability statement (signal names stable reference); contains `SpacetimeSettings` in runtime model context
  - [x] 2.9 Cross-reference alignment tests (AC: 3): contains `docs/runtime-boundaries.md`; contains `docs/compatibility-matrix.md`; contains `demo/README.md` in See Also
  - [x] 2.10 Regression guards — prior story deliverables must remain intact:
    - `docs/install.md` exists
    - `docs/quickstart.md` exists
    - `docs/codegen.md` exists
    - `docs/connection.md` exists
    - `docs/runtime-boundaries.md` exists
    - `docs/compatibility-matrix.md` exists
    - `docs/troubleshooting.md` exists
    - `demo/README.md` exists
    - `demo/DemoMain.cs` exists
    - `addons/godot_spacetime/src/Public/SpacetimeClient.cs` exists
    - `docs/runtime-boundaries.md` contains `ConnectionState` (connection lifecycle terminology intact)
    - `docs/runtime-boundaries.md` contains `ITokenStore` (auth interface intact)
    - `docs/runtime-boundaries.md` contains `ReducerCallFailed` (reducer error model intact)
    - `docs/compatibility-matrix.md` contains `4.6.2` (version baseline intact)
    - `docs/troubleshooting.md` contains `TokenExpired` (Story 5.5 intact)
    - `demo/README.md` contains `Reducer Interaction` (Story 5.3 reducer section intact)
    - `demo/DemoMain.cs` contains `ReducerCallSucceeded` (Story 5.3 wiring intact)

## Dev Notes

### What This Story Delivers

Story 5.6 creates `docs/migration-from-community-plugin.md` — the final documentation deliverable of Epic 5. Stories 5.1–5.5 built the sample, wired the demo, published core docs, and created a troubleshooting guide. Story 5.6 closes the self-serve documentation set by answering three questions an adopter invariably asks when they arrive from an existing integration or an earlier attempt:

1. How do I upgrade from one SDK release to the next? (FR30)
2. How do I replace my existing integration — whether that's the community plugin or handwritten protocol code? (FR31)
3. How does the Godot-facing API model relate to official SpacetimeDB concepts, and what does the future `GDScript` path mean for what I build today? (FR32)

**This story is purely documentation.** No C# code changes. No addons/ changes. No demo/ changes. No modifications to existing docs.

### Critical Architecture Constraints

**Do NOT reinvent or contradict any existing doc.**
Every concept, type name, signal name, and method name in `docs/migration-from-community-plugin.md` must match the public API exactly as defined in `docs/runtime-boundaries.md` and `addons/godot_spacetime/src/Public/SpacetimeClient.cs`. The migration guide cross-references existing docs; it does not re-specify them.

**Use exact public API names everywhere.**
Public API terms that must be spelled exactly as they appear in `SpacetimeClient.cs` and `docs/runtime-boundaries.md`:
- Connection lifecycle: `ConnectionState`, `ConnectionStatus`, `ConnectionStateChanged`, `ConnectionOpened`, `ConnectionClosed`, `ConnectionOpenedEvent`, `ConnectionClosedEvent`
- Auth: `ConnectionAuthState`, `TokenExpired`, `AuthFailed`, `ITokenStore`, `ClearTokenAsync()`, `SpacetimeSettings`
- Subscriptions: `SubscriptionHandle`, `SubscriptionApplied`, `SubscriptionFailed`, `SubscriptionAppliedEvent`, `SubscriptionFailedEvent`, `ErrorMessage`
- Reducers: `ReducerCallResult`, `ReducerCallError`, `ReducerCallSucceeded`, `ReducerCallFailed`, `ReducerFailureCategory`, `InvokeReducer()`, `IReducerArgs`
- Cache access: `GetRows(string tableName)` returns `IEnumerable<object>` — this is the correct public cache-access pattern; do NOT reference `GetClient().Db.*` or `IRemoteDbContext` as public API (they are internal)
- Entry point: `SpacetimeClient`, `SpacetimeSettings`, `Connect()`
- Signals: `ConnectionStateChanged`, `ConnectionOpened`, `ConnectionClosed`, `SubscriptionApplied`, `SubscriptionFailed`, `RowChanged`, `ReducerCallSucceeded`, `ReducerCallFailed`

**`GetRows()` is the supported cache-access path.**
The generated `RemoteTables` type is an internal implementation detail. The supported public path for reading cache in gameplay code is `SpacetimeClient.GetRows("TableName")`, which returns `IEnumerable<object>`. Cast the results to the generated row type (e.g., `SmokeTest`). Do NOT document `connection.Db.*` or `IRemoteDbContext` as a direct public API surface — these are internal and accessed only via `CacheViewAdapter` reflection. Reference `docs/runtime-boundaries.md` for the authoritative cache access model.

**Do NOT describe anything that belongs to Story 5.7+ scope.**
This story creates `docs/migration-from-community-plugin.md` only. The `release-process.md` and release packaging (Epic 6) are out of scope.

**Do NOT modify any existing file in `docs/`.**
All seven existing docs — `install.md`, `quickstart.md`, `codegen.md`, `connection.md`, `runtime-boundaries.md`, `compatibility-matrix.md`, `troubleshooting.md` — are complete and must not be touched.

### Exact Content for `docs/migration-from-community-plugin.md`

**Opening paragraph:**
```
This guide covers three topics for adopters and upgraders: upgrading between SDK releases, migrating from the community plugin or custom protocol work, and understanding how the Godot-facing model maps to official SpacetimeDB concepts.

The canonical end-to-end implementation path is in `demo/README.md` and `demo/DemoMain.cs`. All public API terms used below are defined in `docs/runtime-boundaries.md`. The declared supported version baseline is in `docs/compatibility-matrix.md`.
```

**`## Upgrade Path Between SDK Releases` section:**

Opening sentence:
```
Each SDK release declares its exact supported Godot and SpacetimeDB versions in `docs/compatibility-matrix.md`. Verify your environment against the target release's baseline before upgrading.
```

Numbered steps:
```
1. Replace the `addons/godot_spacetime/` folder with the new SDK version.
2. Confirm your Godot and `.NET SDK` versions satisfy the declared baseline in `docs/compatibility-matrix.md`.
3. Run `bash scripts/codegen/generate-smoke-test.sh` to regenerate bindings against the current module.
4. Check the `"Spacetime Compat"` panel. If it shows `INCOMPATIBLE`, resolve using the instructions in `docs/compatibility-matrix.md` and `docs/troubleshooting.md`.
5. Run `python3 scripts/compatibility/validate-foundation.py` to confirm the environment baseline still passes.
```

Closing note:
```
If a release changes a public type name or signal signature, the release notes for that version state the required migration action. See `docs/compatibility-matrix.md` for the full declared baseline.
```

**`## Migration from the Community Plugin` section:**

Opening paragraph:
```
The SpacetimeDB community Godot plugin provided a thin C# wrapper around `SpacetimeDB.ClientSDK`. This SDK introduces Godot-native abstractions that replace those low-level wiring steps.
```

Sub-heading `### Configuration and Connection`:

Table (columns: Community plugin | This SDK):
1. `DbConnection.Builder().WithUri(...).WithModuleName(...).Build()` | Register `SpacetimeClient` as an autoload; assign a `SpacetimeSettings` resource with `Host` and `Database`
2. `connection.Connect()` with manual `FrameTick()` calls | `SpacetimeClient.Connect()` — lifecycle is managed via `_Process()` internally; no manual tick required
3. Direct token string on the connection builder | Assign an `ITokenStore` implementation to `Settings.TokenStore` before calling `Connect()`

Sub-heading `### Subscriptions`:

Table:
1. `connection.SubscriptionBuilder().OnApplied(...).Subscribe(new[] { query })` | `SpacetimeClient.Subscribe(new[] { query })` returns a `SubscriptionHandle`; connect the `SubscriptionApplied` and `SubscriptionFailed` signals
2. `SubscriptionHandle` applied callback | `SpacetimeClient.SubscriptionApplied` signal (`SubscriptionAppliedEvent` argument)
3. `SubscriptionHandle` error callback | `SpacetimeClient.SubscriptionFailed` signal (`SubscriptionFailedEvent` argument; inspect `ErrorMessage`)

Sub-heading `### Reducers`:

Table:
1. `connection.Reducers.Ping()` (generated static method call) | `SpacetimeClient.InvokeReducer(new SpacetimeDB.Types.Reducer.Ping())` — pass a generated `IReducerArgs` instance
2. Reducer success callback | `SpacetimeClient.ReducerCallSucceeded` signal (`ReducerCallResult` argument)
3. Reducer error callback | `SpacetimeClient.ReducerCallFailed` signal (`ReducerCallError` argument; inspect `FailureCategory`)

Sub-heading `### Cache Access`:

Table:
1. `connection.Db.SmokeTest.Iter()` (direct `RemoteTables` access) | `SpacetimeClient.GetRows("SmokeTest")` returns `IEnumerable<object>`; cast each item to the generated row type (e.g., `SmokeTest`)
2. Row update callbacks on generated table handles | `SpacetimeClient.RowChanged` signal (`RowChangedEvent` argument; `TableName` identifies the table)

Closing note:
```
`GetRows()` is the supported public cache-access path. The underlying `RemoteTables` type is an internal implementation detail and must not be accessed directly from gameplay code. See `docs/runtime-boundaries.md` for the full cache model.
```

**`## Migration from Custom Protocol Work` section:**

Opening sentence:
```
If your existing integration uses raw `SpacetimeDB.ClientSDK` or a direct WebSocket connection to SpacetimeDB, the migration path is:
```

Numbered steps:
```
1. Remove the manual WebSocket or raw `SpacetimeDB.ClientSDK` connection code.
2. Add the `addons/godot_spacetime/` plugin and register `SpacetimeClient` as an autoload.
3. Assign a `SpacetimeSettings` resource with your `Host`, `Database`, and (optionally) `TokenStore`.
4. Run code generation via the `"Spacetime Codegen"` panel or `bash scripts/codegen/generate-smoke-test.sh` to get typed bindings.
5. Replace manual event handling with Godot signal connections on `SpacetimeClient` (`ConnectionStateChanged`, `SubscriptionApplied`, `SubscriptionFailed`, `ReducerCallSucceeded`, `ReducerCallFailed`, `RowChanged`).
6. Replace manual table reads with `SpacetimeClient.GetRows("TableName")`.
7. Replace direct reducer calls with `SpacetimeClient.InvokeReducer(new Reducer.X())`.
```

Closing sentence:
```
The complete end-to-end wiring path is demonstrated in `demo/README.md` and `demo/DemoMain.cs`.
```

**`## Godot SDK Model and SpacetimeDB Concepts` section:**

Opening sentence:
```
The Godot-facing API wraps SpacetimeDB's connection and event model in Godot-native patterns. The table below maps official SpacetimeDB concepts to their equivalents in this SDK:
```

Table (columns: SpacetimeDB concept | This SDK | Reference):
1. `DbConnection` (connection to a database) | `SpacetimeClient` autoload (`Node`) | `docs/runtime-boundaries.md` — Connection
2. `DbConnection.Builder()` configuration | `SpacetimeSettings` resource (`Host`, `Database`, `Credentials`, `TokenStore`) | `docs/runtime-boundaries.md` — SpacetimeClient
3. `DbConnection.Connect()` / `FrameTick()` | `SpacetimeClient.Connect()` (lifecycle advanced via `_Process()`) | `docs/connection.md`
4. `DbConnection.SubscriptionBuilder().Subscribe()` | `SpacetimeClient.Subscribe(string[])` returning `SubscriptionHandle` | `docs/runtime-boundaries.md` — Subscriptions
5. Subscription applied callback | `SpacetimeClient.SubscriptionApplied` signal (`SubscriptionAppliedEvent`) | `docs/runtime-boundaries.md` — Subscriptions
6. Subscription error callback | `SpacetimeClient.SubscriptionFailed` signal (`SubscriptionFailedEvent.ErrorMessage`) | `docs/runtime-boundaries.md` — Subscriptions
7. `DbContext.RemoteTables.*` (table cache access) | `SpacetimeClient.GetRows("TableName")` → `IEnumerable<object>` | `docs/runtime-boundaries.md` — Cache
8. Row update callbacks | `SpacetimeClient.RowChanged` signal (`RowChangedEvent`) | `docs/runtime-boundaries.md` — Cache
9. `connection.Reducers.X()` (generated method) | `SpacetimeClient.InvokeReducer(new Reducer.X())` where `Reducer.X` implements `IReducerArgs` | `docs/runtime-boundaries.md` — Reducer Invocation
10. Reducer success callback | `SpacetimeClient.ReducerCallSucceeded` signal (`ReducerCallResult`) | `docs/runtime-boundaries.md` — Reducer Error Model
11. Reducer error callback | `SpacetimeClient.ReducerCallFailed` signal (`ReducerCallError.FailureCategory`) | `docs/runtime-boundaries.md` — Reducer Error Model
12. Auth token / session identity | `ITokenStore` (assigned to `Settings.TokenStore`) | `docs/runtime-boundaries.md` — Auth / Identity
13. Connection lifecycle events | `SpacetimeClient.ConnectionStateChanged` signal (`ConnectionStatus.State`) | `docs/runtime-boundaries.md` — Connection Lifecycle

**`## Multi-Runtime Product Model` section:**

Opening paragraph:
```
This SDK was designed for a multi-runtime future. The `.NET` runtime is the first delivery; a native `GDScript` runtime is planned as a future phase.
```

**Scene wiring is runtime-stable** sub-paragraph:
```
Signal names (`ConnectionStateChanged`, `SubscriptionApplied`, `SubscriptionFailed`, `ReducerCallSucceeded`, `ReducerCallFailed`, `RowChanged`), the autoload path, and the `SpacetimeSettings` resource are defined at the Godot-concept level. When `GDScript` support ships, these surfaces will remain stable. Adopters will not need to rewire their scenes or change their signal connections.
```

**The public concept model is Godot-native** sub-paragraph:
```
The types in `docs/runtime-boundaries.md` — `ConnectionState`, `ConnectionStatus`, `SubscriptionHandle`, `IReducerArgs`, `ITokenStore` — are defined in Godot-facing terms, not as direct `.NET` SDK types. The mental model therefore transfers to a future `GDScript` runtime path without redesign.
```

Closing sentence:
```
The formal requirements behind this design decision are FR39–FR42 and NFR20–NFR22 in `_bmad-output/planning-artifacts/prd.md`.
```

**`## See Also` section:**

```
- `docs/runtime-boundaries.md` — Complete public API vocabulary: all lifecycle states, signals, auth model, subscriptions, cache, and the reducer error model
- `docs/compatibility-matrix.md` — Declared supported version baseline; the authoritative reference for upgrade verification
- `docs/install.md` — Installation prerequisites and initial setup
- `docs/quickstart.md` — Step-by-step first-setup workflow
- `docs/troubleshooting.md` — Common failure modes and recovery actions for installation, codegen, connection, auth, subscriptions, and reducers
- `demo/README.md` — Canonical end-to-end sample demonstrating the complete SDK workflow
```

### Project Structure Notes

**Files to create:**
- `docs/migration-from-community-plugin.md` — migration, upgrade, and concept-mapping guide (Task 1)
- `tests/test_story_5_6_publish_upgrade_migration_and_concept_mapping_guides.py` — new test file (Task 2)

**Files NOT to touch (any modification will break prior story regression tests):**
- `docs/install.md` — complete; verified by Story 5.4 tests
- `docs/quickstart.md` — complete; verified by Story 5.4 tests
- `docs/codegen.md` — complete; verified by Story 1.6/1.7 tests
- `docs/connection.md` — complete; verified by Story 5.4 tests
- `docs/runtime-boundaries.md` — complete; verified by Story 5.4 tests
- `docs/compatibility-matrix.md` — complete; verified by Story 5.4 tests
- `docs/troubleshooting.md` — complete; verified by Story 5.5 tests
- `demo/README.md` — complete; verified by Story 5.3/5.4 tests
- `demo/DemoMain.cs` — complete; verified by Story 5.3 tests
- `addons/godot_spacetime/` — SDK addon code; out of scope for documentation story
- `spacetime/modules/smoke_test/` — Rust source; out of scope

**Docs directory after Story 5.6:**
```
docs/
├── install.md              ← unchanged
├── quickstart.md           ← unchanged
├── codegen.md              ← unchanged
├── connection.md           ← unchanged
├── runtime-boundaries.md   ← unchanged
├── compatibility-matrix.md ← unchanged
├── troubleshooting.md      ← unchanged
└── migration-from-community-plugin.md  ← NEW (Task 1)
```

### Test File Conventions

Same static-file-analysis pattern as Stories 5.1–5.5:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")
```

Reuse the `_section()` helper established in Story 5.4:
```python
def _section(content: str, heading: str) -> str:
    marker = f"## {heading}\n\n"
    start = content.find(marker)
    assert start != -1, f"Expected to find section heading {marker.strip()!r}"
    start += len(marker)
    next_heading = content.find("\n## ", start)
    if next_heading == -1:
        return content[start:].strip()
    return content[start:next_heading].strip()
```

Test function naming: `test_<file_slug>_<what_is_checked>`. All assertions include a descriptive failure message string.

Existence check pattern:
```python
def test_migration_guide_exists():
    assert (ROOT / "docs/migration-from-community-plugin.md").exists(), \
        "docs/migration-from-community-plugin.md must exist (Story 5.6)"
```

Section presence check (uses `_section()` which asserts existence):
```python
def test_migration_upgrade_section_present():
    content = _read("docs/migration-from-community-plugin.md")
    _section(content, "Upgrade Path Between SDK Releases")
```

Content check pattern:
```python
def test_migration_contains_dbc_builder():
    content = _read("docs/migration-from-community-plugin.md")
    assert "DbConnection.Builder()" in content, \
        "migration guide must document DbConnection.Builder() as the community plugin pattern (AC2)"
```

### Git Intelligence (Recent Work Patterns)

- Recent commits are all documentation-only stories (5.1–5.5): `feat(story-5.x):`
- Story 5.5 test file: 83 static-analysis tests, uses `_read()` + `_section()` + `_intro()` helpers
- **Current full test suite baseline: 1808 tests passing** (from Story 5.5 senior review; baseline was 1725 at start of Epic 5)
- All test files are in `tests/` root directory as `test_story_*.py` — do NOT put new test file in a subdirectory
- Commit message pattern: `feat(story-5.6): Publish Upgrade, Migration, and Concept-Mapping Guides`

### Validation Commands

```bash
pytest -q tests/test_story_5_6_publish_upgrade_migration_and_concept_mapping_guides.py
pytest -q
```

Expected: story test file passes; full suite passes with no regressions (1808+ tests).

### References

- Story user story and AC: `_bmad-output/planning-artifacts/epics.md`, Epic 5 § Story 5.6
- FR30: "Developers can identify how to upgrade between supported SDK releases." [Source: `_bmad-output/planning-artifacts/prd.md` § Documentation, Troubleshooting & Migration]
- FR31: "Developers can identify how to adapt existing projects from custom integrations or community plugin usage to this SDK." [Source: `_bmad-output/planning-artifacts/prd.md` § Documentation, Troubleshooting & Migration]
- FR32: "Developers can understand the intended relationship between the SDK's Godot-facing model and official SpacetimeDB concepts." [Source: `_bmad-output/planning-artifacts/prd.md` § Documentation, Troubleshooting & Migration]
- `docs/migration-from-community-plugin.md` is an expected file in both the architecture directory structure and the FR→structure mapping for "Documentation, Troubleshooting & Migration" [Source: `_bmad-output/planning-artifacts/architecture.md` § Complete Project Directory Structure + Requirements to Structure Mapping]
- Multi-runtime product model context: FR39–FR42, NFR20–NFR22 [Source: `_bmad-output/planning-artifacts/prd.md` § Multi-Runtime Product Continuity + NFRs]
- `SpacetimeClient` public API surface (correct method/signal names): `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- Cache access pattern (`GetRows()` is the public path; `IRemoteDbContext`/`RemoteTables` are internal): `docs/runtime-boundaries.md` § Cache, `addons/godot_spacetime/src/Public/SpacetimeClient.cs` line 186–187
- Test file pattern: `tests/test_story_5_5_publish_troubleshooting_guidance_for_setup_and_runtime_failures.py` (83 tests)
- Previous story (5.5): `_bmad-output/implementation-artifacts/5-5-publish-troubleshooting-guidance-for-setup-and-runtime-failures.md`
- Story 5.5 dev notes explicitly call out: "Do NOT create `docs/migration-from-community-plugin.md`. That is Story 5.6 scope."
- Current test suite baseline: 1808 passing (from Story 5.5 senior review)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation proceeded without blockers.

### Completion Notes List

- ✅ Created `docs/migration-from-community-plugin.md` with all six required sections: Upgrade Path Between SDK Releases, Migration from the Community Plugin, Migration from Custom Protocol Work, Godot SDK Model and SpacetimeDB Concepts, Multi-Runtime Product Model, See Also.
- ✅ All public API names match exactly as specified in Dev Notes (SpacetimeClient, SpacetimeSettings, ITokenStore, GetRows(), InvokeReducer(), ReducerCallSucceeded, ReducerCallFailed, SubscriptionApplied, SubscriptionFailed, RowChanged, ConnectionStateChanged, SubscriptionHandle, IReducerArgs, ReducerCallResult, ReducerCallError).
- ✅ No existing docs modified — all seven prior docs intact.
- ✅ Created `tests/test_story_5_6_publish_upgrade_migration_and_concept_mapping_guides.py` with static-analysis coverage across all subtasks 2.1–2.10; suite now 85 tests after review hardening.
- ✅ Senior review hardening pass: clarified the generic `connection.Db.*` → `SpacetimeClient.GetRows("TableName")` migration rule and added 3 contract tests covering the generic cache-migration pattern plus multi-runtime autoload-path and scene-wiring stability.
- ✅ Current validation: `85` story tests passing; full suite `1893` passing (was `1808`, +`85`) with no regressions.
- ✅ All three ACs satisfied: FR30 upgrade path (AC1), FR31 community plugin/custom protocol migration (AC2), FR32 concept mapping and multi-runtime model (AC3).

### File List

- `docs/migration-from-community-plugin.md` (created, review-clarified generic `connection.Db.*` cache migration guidance)
- `tests/test_story_5_6_publish_upgrade_migration_and_concept_mapping_guides.py` (created, review-hardened: 85 tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status updated)

## Senior Developer Review (AI)

- Reviewer: Pinkyd on 2026-04-15
- Outcome: Approve
- Story Context: No separate story-context artifact was found; review used the story file, `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/prd.md`, the authoritative docs, and the new docs/tests as the primary sources.
- Epic Tech Spec: No separate Epic 5 tech spec artifact was found; `_bmad-output/planning-artifacts/architecture.md` and `_bmad-output/planning-artifacts/epics.md` were used for requirements and standards context.
- Tech Stack Reviewed: Markdown documentation contracts, Godot `4.6.2`, `.NET 8.0+`, SpacetimeDB `2.1+`, Python `pytest` static contract tests.
- External References: MCP resource discovery returned no available resources in this session; repository primary sources were sufficient and no web lookup was used.
- Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` during review (`_bmad-output/implementation-artifacts/sprint-status.yaml`, `_bmad-output/implementation-artifacts/tests/test-summary-5-6.md`, `_bmad-output/story-automator/orchestration-1-20260414-184146.md`).
- Findings fixed:
  - MEDIUM: `docs/migration-from-community-plugin.md` only demonstrated `connection.Db.SmokeTest.Iter()` and left the broader `connection.Db.*` cache-migration rule implicit, even though Task 1.3 requires a general pattern mapping. Fixed by making the generic `connection.Db.*` → `SpacetimeClient.GetRows("TableName")` rule explicit.
  - MEDIUM: `tests/test_story_5_6_publish_upgrade_migration_and_concept_mapping_guides.py` did not lock the generic `connection.Db.*` cache-migration statement, the multi-runtime autoload-path stability promise, or the guarantee that adopters do not need to rewire scenes when `GDScript` support ships. Fixed with 3 additional contract tests.
  - MEDIUM: The story artifact's completion notes claimed a 53-test story suite and a 1861-test full-suite result, but the actual validated implementation already contained 82 story tests and the full suite passed at 1890 before review hardening. Fixed by rerunning validation and correcting the story record to the current 85/1893 totals.
  - MEDIUM: The story artifact was still in `review`, had no `Senior Developer Review (AI)` section, and sprint tracking still showed `review`. Fixed by appending this review and syncing both story status fields to `done`.
- Validation:
  - `pytest -q tests/test_story_5_6_publish_upgrade_migration_and_concept_mapping_guides.py`
  - `pytest -q`

## Change Log

- 2026-04-14: Story 5.6 implemented — created migration, upgrade, and concept-mapping guide and validation suite (claude-sonnet-4-6)
- 2026-04-15: Senior Developer Review (AI) — clarified generic `connection.Db.*` migration guidance, hardened Story 5.6 contract coverage to 85 tests, reran validation (`85` story tests, `1893` full-suite tests), and marked the story done.
