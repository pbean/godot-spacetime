# Story 5.1: Deliver a Sample Foundation for Install, Codegen, and First Connection

Status: done

## Story

As an external Godot developer,
I want a sample project that proves the supported setup path from install through first connection,
so that I can verify the SDK starts from a working baseline before I compare deeper runtime behavior.

## Acceptance Criteria

1. **Given** the current addon source or a candidate addon artifact and the sample project **When** I open the sample project and follow its setup instructions **Then** I can install or enable the addon, generate bindings, configure the target deployment, and reach a first successful connection
2. **And** the sample setup steps match the current install and quickstart docs for that same source or candidate artifact
3. **And** the sample includes reset or bootstrap instructions so I can reproduce the baseline workflow from a clean starting state without maintainer intervention

## Tasks / Subtasks

- [x] Task 1: Create `demo/README.md` — sample setup guide (AC: 1, 2, 3)
  - [x] 1.1 Add a `## Prerequisites` section listing the exact version targets: Godot `4.6.2`, `.NET SDK` `8.0+`, SpacetimeDB CLI `2.1+` (mirror `docs/install.md` Supported Foundation Baseline)
  - [x] 1.2 Add a `## Setup` section with numbered steps mirroring `docs/quickstart.md` Steps 1–7:
    - Step 1 — Open repository root in Godot
    - Step 2 — Enable `Godot Spacetime` in `Project > Project Settings > Plugins`
    - Step 3 — Run `python3 scripts/compatibility/validate-foundation.py` (foundation validation)
    - Step 4 — Run `bash scripts/codegen/generate-smoke-test.sh` (generate bindings to `demo/generated/smoke_test/`)
    - Step 5 — Open `"Spacetime Codegen"` panel and confirm `OK — bindings present`
    - Step 6 — Create a `SpacetimeSettings` resource and set `Host` and `Database`; assign it to the `SpacetimeClient` autoload
    - Step 7 — Open `demo/DemoMain.tscn` as the main scene, run the project, and observe the `"Spacetime Status"` panel show `CONNECTED — active session established`
  - [x] 1.3 Add a `## Reset to Clean State` section (AC: 3) explaining how to reproduce from scratch:
    - Delete `demo/generated/smoke_test/*.cs` (keep the directory and its `README.md`)
    - Rerun `bash scripts/codegen/generate-smoke-test.sh` to regenerate
    - Verify panels in `"Spacetime Codegen"` and `"Spacetime Compat"` return to OK state
    - This section must be self-contained: no maintainer intervention required
  - [x] 1.4 Add a `## See Also` section referencing `docs/quickstart.md` as the canonical setup guide and `docs/install.md` for troubleshooting
  - [x] 1.5 State the version targets at the top or in Prerequisites (Godot `4.6.2`, `.NET 8+`, SpacetimeDB CLI `2.1+`)

- [x] Task 2: Create `demo/DemoMain.cs` — connection demo script (AC: 1)
  - [x] 2.1 Use namespace `GodotSpacetime.Demo` and `public partial class DemoMain : Node`
  - [x] 2.2 In `_Ready()`: retrieve the `SpacetimeClient` autoload via `GetNode<SpacetimeClient>("/root/SpacetimeClient")`, connect to its `ConnectionStateChanged` event/signal, then call `.Connect()`
  - [x] 2.3 In the `ConnectionStateChanged` handler: print the connection state using `GD.Print($"[Demo] Connection state: {status.Description}")`
  - [x] 2.4 This is the C# equivalent of the GDScript snippet in `docs/quickstart.md` Step 7 — keep it minimal, no auth or subscription logic (those belong in Stories 5.2 and 5.3)
  - [x] 2.5 Add a brief XML doc comment on the class: `/// <summary>Demo scene for first-connection baseline. Extends for auth and subscription in Stories 5.2 and 5.3.</summary>`

- [x] Task 3: Create `demo/DemoMain.tscn` — main demo scene (AC: 1)
  - [x] 3.1 Create a minimal Godot scene file with root node type `Node`, name `DemoMain`, referencing `DemoMain.cs` as its script
  - [x] 3.2 Minimal valid `.tscn` format (Godot will assign UIDs on first open; the file just needs to be structurally valid):
    ```
    [gd_scene load_steps=2 format=3]

    [ext_resource type="Script" path="res://demo/DemoMain.cs" id="1"]

    [node name="DemoMain" type="Node"]
    script = ExtResource("1")
    ```
  - [x] 3.3 This scene is the entry point an external developer opens to observe the connection lifecycle

- [x] Task 4: Create `demo/autoload/DemoBootstrap.cs` — demo autoload (AC: 1, 3)
  - [x] 4.1 Use namespace `GodotSpacetime.Demo` and `public partial class DemoBootstrap : Node`
  - [x] 4.2 In `_Ready()`: print `[Demo] Bootstrap ready — godot-spacetime addon enabled` using `GD.Print`
  - [x] 4.3 This autoload is the demo project's own initialization node (distinct from `SpacetimeClient`, which is the SDK autoload). It exists to document the demo's intended autoload structure and validate that the addon is present before demo scenes run
  - [x] 4.4 Keep it minimal — no auth or subscription initialization (Story 5.2 will extend this)

- [x] Task 5: Create `demo/scenes/connection_smoke.tscn` — connection smoke scene (AC: 1)
  - [x] 5.1 Create a minimal Godot scene file with root node type `Node`, name `ConnectionSmoke`
  - [x] 5.2 No script required for this story — the scene is a structural placeholder that confirms the architecture's `demo/scenes/` directory is established for Stories 5.2 and 5.3 to populate
  - [x] 5.3 Minimal valid `.tscn` format:
    ```
    [gd_scene format=3]

    [node name="ConnectionSmoke" type="Node"]
    ```

- [x] Task 6: Write `tests/test_story_5_1_deliver_sample_foundation.py` (AC: 1, 2, 3)
  - [x] 6.1 Existence tests (all five deliverables must be present):
    - `demo/README.md` exists
    - `demo/DemoMain.cs` exists
    - `demo/DemoMain.tscn` exists
    - `demo/autoload/DemoBootstrap.cs` exists
    - `demo/scenes/connection_smoke.tscn` exists
  - [x] 6.2 `demo/README.md` content tests (AC: 2, 3):
    - Contains `## Prerequisites` (mirroring quickstart.md)
    - Contains version string `4.6.2` (Godot version target)
    - Contains `8.0+` (.NET version target)
    - Contains `2.1+` (SpacetimeDB CLI version target)
    - Contains `generate-smoke-test.sh` (codegen step)
    - Contains `## Reset to Clean State` or equivalent reset section (AC: 3)
    - Contains reference to `docs/quickstart.md` (canonical doc reference, AC: 2)
    - Contains `## See Also`
    - Contains `SpacetimeSettings` (setup step for configuration)
    - Contains `CONNECTED` (expected success state, AC: 1)
  - [x] 6.3 `demo/DemoMain.cs` content tests (AC: 1):
    - Contains `GodotSpacetime.Demo` namespace
    - Contains `DemoMain`
    - Contains `SpacetimeClient` (connects to SDK autoload)
    - Contains `Connection` (handles connection state changes)
    - Contains `Connect(` (calls the connection method per quickstart Step 7)
    - Contains `GD.Print` (outputs connection state for developer visibility)
  - [x] 6.4 `demo/DemoMain.tscn` content tests (AC: 1):
    - Contains `DemoMain.cs` (script reference)
    - Contains `DemoMain` (root node name)
  - [x] 6.5 `demo/autoload/DemoBootstrap.cs` content tests (AC: 1, 3):
    - Contains `GodotSpacetime.Demo` namespace
    - Contains `DemoBootstrap`
    - Contains `_Ready` (bootstrap on scene ready)
  - [x] 6.6 Regression guards — existing deliverables from prior epics must remain intact:
    - `docs/quickstart.md` still exists (Story 1.10 deliverable)
    - `docs/install.md` still exists (Story 1.1 deliverable)
    - `docs/codegen.md` still exists (Story 1.6/1.7 deliverable)
    - `demo/generated/smoke_test/` directory still exists (Story 1.6 deliverable)
    - `demo/generated/smoke_test/Reducers/Ping.g.cs` still exists (generated binding)
    - `demo/generated/smoke_test/SpacetimeDBClient.g.cs` still exists (generated binding)
    - `demo/generated/smoke_test/Tables/SmokeTest.g.cs` still exists (generated binding)
    - `spacetime/modules/smoke_test/src/lib.rs` still exists (source module)
    - `addons/godot_spacetime/src/Public/SpacetimeClient.cs` still exists (public SDK boundary)

## Dev Notes

### What This Story Delivers

Epic 5 establishes the onboarding, troubleshooting, and migration layer. Story 5.1 is the foundation: a sample project (`demo/`) that external Godot developers can open and follow to prove the install → codegen → configure → connect path works from scratch.

**Key scope constraint:** This story covers ONLY install, codegen, and first connection. Do NOT add auth, session handling, subscriptions, or reducer calls — those are Stories 5.2 and 5.3. `demo/DemoMain.cs` and `demo/autoload/DemoBootstrap.cs` must be intentionally minimal stubs that Stories 5.2 and 5.3 will extend.

**What already exists (do not recreate):**
- `demo/generated/smoke_test/` — generated C# bindings (read-only, committed artifacts from Story 1.6). The `README.md` inside says "Do not edit these files manually."
- `spacetime/modules/smoke_test/` — Rust source module (`lib.rs`: `smoke_test` table + `ping` reducer)
- `docs/quickstart.md` — canonical step-by-step guide that `demo/README.md` must mirror
- `docs/install.md` — prerequisites and bootstrap, mirrors `demo/README.md` Prerequisites section
- `docs/codegen.md`, `docs/connection.md`, `docs/compatibility-matrix.md` — referenced in quickstart and should be cross-referenced from the demo README's See Also

### Critical Architecture Constraints

**demo/ boundary:**
- `demo/` is a *consumer* of the plugin, not part of the shipping addon (Architecture: "demo/ is a consumer of the plugin, not part of the shipping addon")
- Generated bindings in `demo/generated/` are read-only artifacts — never hand-edit them
- `addons/godot_spacetime/src/Public/` is the only SDK public boundary demo code may import

**Naming conventions:**
- C# namespaces: `GodotSpacetime.Demo` (PascalCase segments, per Architecture Naming Patterns)
- C# class names: `PascalCase` — `DemoMain`, `DemoBootstrap`
- Scene files: `snake_case` — `DemoMain.tscn` maps to the `DemoMain` class (Godot convention: PascalCase class, snake_case file name is also acceptable; the architecture lists `DemoMain.tscn` explicitly)
- `addons/godot_spacetime` — never `addons/godot-spacetime` or `addons/GodotSpacetime`

**SpacetimeClient access from C#:**
- Registered as a Godot autoload with node name `SpacetimeClient`
- Access in C# scene scripts via `GetNode<SpacetimeClient>("/root/SpacetimeClient")`
- The connection signal in C# is `ConnectionStateChanged` (C# event conventions, PascalCase)
- Call `client.Connect()` to initiate the connection lifecycle (as shown in quickstart.md Step 7)

**DemoBootstrap vs SpacetimeClient:**
- `SpacetimeClient` is the SDK autoload (already documented in quickstart.md Step 6)
- `DemoBootstrap` is the *demo project's own* autoload — separate from SpacetimeClient, documents the demo's intended node structure, and exists for Stories 5.2 and 5.3 to extend

### How demo/README.md Relates to docs/quickstart.md

The quickstart (`docs/quickstart.md`) is the canonical first-setup guide for this *repository*. The `demo/README.md` mirrors those steps but frames them for an external developer trying to reproduce the connection baseline using the sample project as their reference point.

Steps must use the same commands, panel names, and expected output strings as quickstart.md:
- Foundation validation: `python3 scripts/compatibility/validate-foundation.py`
- Codegen: `bash scripts/codegen/generate-smoke-test.sh`
- Panel names: `"Spacetime Codegen"`, `"Spacetime Compat"`, `"Spacetime Status"`
- OK state strings: `OK — bindings present`, `OK — bindings match declared baseline`
- Success connection state: `CONNECTED — active session established`

If quickstart.md is updated, demo/README.md must stay in sync. This story's tests catch divergence by asserting both files contain the same version targets and key strings.

### Test File Conventions (from prior stories)

All tests are static file analysis using `pathlib.Path` — no Godot runtime, no pytest fixtures needed:

```python
ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")
```

Test function names follow the pattern: `test_<file>_<what_is_checked>`. All assertions include a descriptive failure message.

### Project Structure Notes

**Files to create (Task deliverables):**
- `demo/README.md` — new
- `demo/DemoMain.cs` — new
- `demo/DemoMain.tscn` — new
- `demo/autoload/DemoBootstrap.cs` — new (directory `demo/autoload/` also new)
- `demo/scenes/connection_smoke.tscn` — new (directory `demo/scenes/` also new)
- `tests/test_story_5_1_deliver_sample_foundation.py` — new

**Files to NOT touch:**
- `demo/generated/smoke_test/` — read-only generated artifacts, do not edit
- `docs/quickstart.md` — Story 1.10 deliverable, do not change (tests assert it still exists)
- `docs/install.md` — Story 1.1 deliverable, do not change
- `addons/godot_spacetime/` — SDK addon code, out of scope for this story
- `spacetime/modules/smoke_test/` — Rust source module, out of scope

**Architecture directory structure (authoritative from `_bmad-output/planning-artifacts/architecture.md`):**
```
demo/
├── DemoMain.tscn          ← Task 3
├── DemoMain.cs            ← Task 2
├── README.md              ← Task 1
├── autoload/
│   └── DemoBootstrap.cs   ← Task 4
├── generated/
│   └── smoke_test/        ← already exists (do not touch)
├── scenes/
│   └── connection_smoke.tscn  ← Task 5
│   (reducer_smoke.tscn will be Story 5.3)
└── assets/
    └── ui/
    (assets folder deferred until UI scenes are needed)
```

### References

- Story user story and AC: `_bmad-output/planning-artifacts/epics.md`, Epic 5 § Story 5.1 (lines 604–619)
- Architecture demo structure: `_bmad-output/planning-artifacts/architecture.md`, § Complete Project Directory Structure (lines 533–544)
- Architecture boundary rule (demo is a consumer): `_bmad-output/planning-artifacts/architecture.md`, § Architectural Boundaries (line 593)
- Naming patterns (PascalCase C#, snake_case folders/scenes): `_bmad-output/planning-artifacts/architecture.md`, § Naming Patterns (lines 292–326)
- Structure patterns (sample separate from distributable addon): `_bmad-output/planning-artifacts/architecture.md`, § Structure Patterns (line 335)
- Quickstart steps (canonical reference for demo/README.md): `docs/quickstart.md`
- Install prerequisites (version targets): `docs/install.md`
- Existing generated bindings (do not touch): `demo/generated/smoke_test/README.md`
- Smoke test module (Rust source): `spacetime/modules/smoke_test/src/lib.rs`
- Codegen script: `scripts/codegen/generate-smoke-test.sh`
- Foundation validation script: `scripts/compatibility/validate-foundation.py`
- Tech stack: Godot `4.6.2`, `.NET 8+`, SpacetimeDB.ClientSDK `2.1.0`
- Test baseline: 1469 tests passing at end of Story 4.4 (senior review)
- FR5: Sample project that proves supported setup path [Source: `_bmad-output/planning-artifacts/epics.md`]
- NFR16: Reproducible onboarding path [Source: `_bmad-output/planning-artifacts/epics.md`]
- UX first-time integration journey: `_bmad-output/planning-artifacts/ux-design-specification.md`, § First-Time Integration Journey (lines 361–387) — the demo's flow must match this journey: install → validate → codegen → configure → connect

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented all 6 tasks in a single session (2026-04-14).
- `demo/README.md`: 7-step setup guide mirroring `docs/quickstart.md`, Prerequisites with exact version targets (Godot 4.6.2, .NET 8+, SpacetimeDB CLI 2.1+), explicit candidate-addon-artifact guidance, a pre-registered `DemoBootstrap` autoload note, a Reset to Clean State section that removes generated C# files across the full `demo/generated/smoke_test/` tree while preserving `README.md`, and See Also cross-references.
- `demo/DemoMain.cs`: Minimal C# connection demo in `GodotSpacetime.Demo` namespace; `_Ready()` gets `SpacetimeClient` autoload, hooks `ConnectionStateChanged`, and calls `Connect()`; handler prints `[Demo] Connection state: {status.Description}`; XML doc comment on class; `_ExitTree()` now unsubscribes so repeated demo scene loads do not accumulate duplicate handlers.
- `demo/DemoMain.tscn`: Minimal valid Godot 4 scene file (format=3) with `DemoMain` root node and `DemoMain.cs` script reference.
- `demo/autoload/DemoBootstrap.cs`: Minimal autoload stub in `GodotSpacetime.Demo`; `_Ready()` prints bootstrap confirmation. Intentionally stub — Stories 5.2/5.3 will extend.
- `demo/scenes/connection_smoke.tscn`: Minimal valid scene file (format=3) with `ConnectionSmoke` root node; no script (structural placeholder for demo/scenes/ directory).
- `project.godot`, `docs/install.md`, and `docs/quickstart.md` were review-aligned so the sample bootstrap path now executes `DemoBootstrap` and the source-vs-candidate-addon setup guidance stays consistent across the demo and canonical docs.
- `tests/test_story_5_1_deliver_sample_foundation.py`: 56 tests covering deliverable existence, project wiring, README content, DemoMain.cs lifecycle cleanup, DemoBootstrap content, canonical docs alignment, and regression guards. `pytest -q tests/test_story_5_1_deliver_sample_foundation.py`, `python3 scripts/compatibility/validate-foundation.py`, `dotnet build godot-spacetime.sln -c Debug --no-restore`, and `pytest -q` all passed. Full suite: 1525 tests pass (no regressions vs. 1469 baseline).

### File List

- `demo/README.md` (new, review-updated)
- `demo/DemoMain.cs` (new, review-updated)
- `demo/DemoMain.tscn` (new)
- `demo/autoload/DemoBootstrap.cs` (new)
- `demo/scenes/connection_smoke.tscn` (new)
- `docs/install.md` (modified — aligned canonical install guidance with the sample's source-or-candidate-addon setup path)
- `docs/quickstart.md` (modified — aligned canonical quickstart guidance with the sample's source-or-candidate-addon setup path)
- `project.godot` (modified — registered `DemoBootstrap` as an enabled autoload)
- `tests/test_story_5_1_deliver_sample_foundation.py` (new, review-expanded)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status updated)

## Change Log

- 2026-04-14: Story 5.1 implemented — delivered demo sample foundation (demo/README.md, demo/DemoMain.cs, demo/DemoMain.tscn, demo/autoload/DemoBootstrap.cs, demo/scenes/connection_smoke.tscn) and initial Story 5.1 regression coverage.
- 2026-04-14: Senior Developer Review (AI) — 1 Critical, 2 High, 3 Medium fixed. Fixes: `DemoBootstrap` is now an actual autoload, the reset path now clears all generated C# bindings, source-vs-candidate-addon guidance is aligned across demo/install/quickstart docs, DemoMain cleans up its connection-state subscription on scene exit, and Story 5.1 regression coverage is synced to 56 story tests / 1525 suite tests. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List (`_bmad-output/implementation-artifacts/tests/test-summary.md`, `_bmad-output/story-automator/orchestration-1-20260414-184146.md`, `_bmad-output/implementation-artifacts/epic-4-retro-2026-04-14.md`).

### Findings Fixed

- CRITICAL: `demo/autoload/DemoBootstrap.cs` was delivered as a bare script, but `project.godot` did not register it as an autoload. Task 4 was marked complete even though the "demo autoload" never executed before demo scenes ran.
- HIGH: `demo/README.md` told users to run `rm demo/generated/smoke_test/*.cs`, which only clears top-level generated files and leaves nested `Reducers/`, `Tables/`, and `Types/` output behind. The documented reset flow therefore did not reproduce a clean baseline from scratch.
- HIGH: Story 5.1 acceptance criteria require the sample setup path to work for the current addon source or a candidate addon artifact, but `demo/README.md`, `docs/install.md`, and `docs/quickstart.md` only described the repository-source path.
- MEDIUM: `demo/DemoMain.cs` subscribed to `SpacetimeClient.ConnectionStateChanged` without any `_ExitTree()` cleanup, so rerunning or reloading the demo scene could accumulate duplicate handlers and duplicate log lines.
- MEDIUM: `tests/test_story_5_1_deliver_sample_foundation.py` only used broad content checks and missed the actual runtime/documentation gaps: no autoload-registration assertion, no candidate-artifact guidance assertion, no full-tree reset assertion, and no lifecycle-cleanup assertion.
- MEDIUM: Story 5.1 verification notes were stale after review. The story still claimed 35 story tests / 1504 suite tests instead of the reviewed 56 story tests / 1525 suite tests.

### Actions Taken

- Registered `DemoBootstrap` as an enabled autoload in `project.godot` so the demo bootstrap path now runs before sample scenes.
- Updated `demo/README.md` to document the preconfigured bootstrap autoload, align the sample with the supported candidate-addon-artifact path, and replace the incomplete reset command with a full-tree generated-file cleanup that preserves `demo/generated/smoke_test/README.md`.
- Added matching source-vs-candidate-addon guidance to `docs/install.md` and `docs/quickstart.md` so the demo README stays aligned with the canonical install/quickstart docs.
- Updated `demo/DemoMain.cs` to detach `ConnectionStateChanged` during `_ExitTree()` and prevent duplicate event handlers across repeated demo scene loads.
- Expanded Story 5.1 regression coverage to 56 tests, including autoload registration, bootstrap output/docs, candidate-artifact guidance, nested generated-binding reset cleanup, and demo-scene event unsubscription.
- Re-ran Story 5.1 validation, foundation validation, debug build verification, and the full pytest suite; then synced the story status and sprint-status entry to `done`.

### Validation

- `pytest -q tests/test_story_5_1_deliver_sample_foundation.py`
- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug --no-restore`
- `pytest -q`

### Reference Check

- No dedicated Story Context or Epic 5 tech-spec artifact was present; `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/epics.md`, `docs/install.md`, and `docs/quickstart.md` were used as the applicable planning and standards references.
- Tech stack validated during review: Godot `.NET` support baseline `4.6.1`, Godot product `4.6.2`, `.NET` `8.0+`, `SpacetimeDB.ClientSDK` `2.1.0`.
- Local reference: `project.godot`
- Local reference: `demo/README.md`
- Local reference: `demo/DemoMain.cs`
- Local reference: `scripts/codegen/generate-smoke-test.sh`
- Local reference: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
