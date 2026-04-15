# Story 5.3: Demonstrate Reducer Interaction and Troubleshooting Comparison Paths

Status: done

## Story

As an external Godot developer,
I want the sample to show reducer calls and expected recovery behavior,
So that I can compare my runtime integration against known-good mutation flows when debugging.

## Acceptance Criteria

1. **Given** the sample is running against a supported environment **When** I trigger its documented gameplay interaction path **Then** the sample demonstrates reducer invocation plus the resulting success or recoverable-failure handling path
2. **And** the sample documents the expected observable states or messages I should compare during troubleshooting
3. **And** the sample remains aligned with the supported workflow described in the troubleshooting and runtime docs

## Tasks / Subtasks

- [x] Task 1: Extend `demo/DemoMain.cs` — wire reducer invocation and result handlers (AC: 1, 3)
  - [x] 1.1 Add `using GodotSpacetime.Reducers;` import (for `ReducerCallResult`, `ReducerCallError`, `ReducerFailureCategory`)
  - [x] 1.2 Add `using SpacetimeDB.Types;` import (for `Reducer.Ping` from generated bindings namespace `SpacetimeDB.Types`)
  - [x] 1.3 In `_Ready()`, wire two new signal handlers using `-= then +=` pattern (same pattern as existing signals):
    - `_client.ReducerCallSucceeded -= OnReducerCallSucceeded; _client.ReducerCallSucceeded += OnReducerCallSucceeded;`
    - `_client.ReducerCallFailed -= OnReducerCallFailed; _client.ReducerCallFailed += OnReducerCallFailed;`
  - [x] 1.4 In `_ExitTree()`, unsubscribe both new handlers from `_client` (same cleanup pattern as Story 5.2 handlers)
  - [x] 1.5 In `OnSubscriptionApplied()`, after printing the row count line, add: `_client!.InvokeReducer(new Reducer.Ping());` then print `"[Demo] Ping reducer invoked — awaiting server acknowledgement"`. Guard: only call `InvokeReducer` if `e.Handle == _subscriptionHandle` (current handle guard is already in place; the `InvokeReducer` call goes inside that guard after the row-count print)
  - [x] 1.6 Add `OnReducerCallSucceeded(ReducerCallResult result)` handler: print `$"[Demo] Reducer '{result.ReducerName}' succeeded (id: {result.InvocationId})"`
  - [x] 1.7 Add `OnReducerCallFailed(ReducerCallError error)` handler: print `$"[Demo] Reducer '{error.ReducerName}' failed — {error.FailureCategory}: {error.ErrorMessage} | guidance: {error.RecoveryGuidance}"`
  - [x] 1.8 Update the XML doc comment on the class from `"Story 5.3 adds reducer interaction"` to `"Story 5.3 — wires reducer invocation (Ping) and result handling via ReducerCallSucceeded / ReducerCallFailed signals."`

- [x] Task 2: Create `demo/scenes/reducer_smoke.tscn` (AC: 1)
  - [x] 2.1 Create minimal Godot scene file at `demo/scenes/reducer_smoke.tscn` matching the format of the existing `demo/scenes/connection_smoke.tscn`:
    ```
    [gd_scene format=3]

    [node name="ReducerSmoke" type="Node"]
    ```

- [x] Task 3: Update `demo/README.md` — document reducer interaction and troubleshooting comparison (AC: 2, 3)
  - [x] 3.1 Add `## Reducer Interaction` section after the `## Subscription and Live State` section and before `## Reset to Clean State`. The section must cover:
    - After `SubscriptionApplied` fires and the row count is logged, `DemoMain` automatically invokes the `Ping` reducer via `InvokeReducer(new Reducer.Ping())`
    - The call is asynchronous — the server acknowledgement arrives in a later frame (after `FrameTick` delivers the queued server message)
    - **Success path**: `ReducerCallSucceeded` fires with the reducer name and invocation ID: `[Demo] Reducer 'ping' succeeded (id: ...)`
    - **Failure path**: `ReducerCallFailed` fires with failure category (`Failed`, `OutOfEnergy`, or `Unknown`) plus machine-readable `RecoveryGuidance` for branching: `[Demo] Reducer 'ping' failed — <category>: <message> | guidance: <guidance>`
    - **Troubleshooting comparison path**: expected output for a healthy Ping flow is `succeeded` — if `ReducerCallFailed` appears instead, the category and recovery guidance identify whether to retry, check server logs, or back off
    - Full expected Output panel sequence (extending the Story 5.2 sequence):
      ```
      [Demo] Subscription applied — N row(s) in smoke_test
      [Demo] Ping reducer invoked — awaiting server acknowledgement
      [Demo] Reducer 'ping' succeeded (id: <invocation-id>)
      ```
    - Lifecycle terms `ReducerCallSucceeded` and `ReducerCallFailed` are defined in `docs/runtime-boundaries.md`
    - `ReducerFailureCategory` values (`Failed`, `OutOfEnergy`, `Unknown`) are documented in the SDK at `addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs`

- [x] Task 4: Write `tests/test_story_5_3_demonstrate_reducer_interaction.py` (AC: 1, 2, 3)
  - [x] 4.1 Existence tests:
    - `demo/DemoMain.cs` exists (still present after modification)
    - `demo/README.md` exists (still present after modification)
    - `demo/scenes/reducer_smoke.tscn` exists (new file)
  - [x] 4.2 `demo/DemoMain.cs` content tests (AC: 1, 3):
    - Contains `GodotSpacetime.Reducers` (reducer result namespace import)
    - Contains `SpacetimeDB.Types` (generated bindings namespace import for `Reducer.Ping`)
    - Contains `ReducerCallSucceeded` (reducer success signal wired)
    - Contains `ReducerCallFailed` (reducer failure signal wired)
    - Contains `OnReducerCallSucceeded` (handler method present)
    - Contains `OnReducerCallFailed` (handler method present)
    - Contains `InvokeReducer` (reducer call made)
    - Contains `Reducer.Ping` (correct generated type used, not a string or custom class)
    - Contains `result.ReducerName` (reducer identity logged from success result)
    - Contains `result.InvocationId` (invocation instance logged from success result for correlation)
    - Contains `error.ReducerName` (reducer identity logged from failure)
    - Contains `error.FailureCategory` (failure category surfaced for troubleshooting branching)
    - Contains `error.RecoveryGuidance` (recovery guidance surfaced for troubleshooting path)
    - Contains `error.ErrorMessage` (error message surfaced for troubleshooting)
    - Contains `awaiting server acknowledgement` (async nature documented in output)
    - Contains `ReducerCallResult result` (typed parameter — not object — in handler signature)
    - Contains `ReducerCallError error` (typed parameter — not object — in handler signature)
  - [x] 4.3 `demo/README.md` content tests (AC: 2, 3):
    - Contains `## Reducer` (reducer section present)
    - Contains `Ping` (ping reducer referenced)
    - Contains `InvokeReducer` (invocation call documented)
    - Contains `ReducerCallSucceeded` (success lifecycle term aligned with docs)
    - Contains `ReducerCallFailed` (failure lifecycle term aligned with docs)
    - Contains `succeeded` (success path documented)
    - Contains `failed` (failure path documented)
    - Contains `FailureCategory` or `ReducerFailureCategory` (troubleshooting branching documented)
    - Contains `RecoveryGuidance` (recovery path documented)
    - Contains `awaiting server acknowledgement` (async nature documented)
    - Contains `docs/runtime-boundaries.md` (lifecycle vocabulary reference present)
  - [x] 4.4 `demo/scenes/reducer_smoke.tscn` content tests:
    - Contains `ReducerSmoke` (node name present)
    - Contains `gd_scene` (valid Godot scene header)
  - [x] 4.5 Regression guards — all prior deliverables must remain intact:
    - `demo/DemoMain.cs` exists (Story 5.1)
    - `demo/DemoMain.tscn` exists (Story 5.1)
    - `demo/autoload/DemoBootstrap.cs` exists (Story 5.1)
    - `demo/scenes/connection_smoke.tscn` exists (Story 5.1)
    - `project.godot` still contains `DemoBootstrap` autoload registration (Story 5.1 critical fix)
    - `docs/quickstart.md` exists (Story 1.10)
    - `docs/install.md` exists (Story 1.1)
    - `docs/codegen.md` exists (Story 1.6/1.7)
    - `demo/generated/smoke_test/` directory exists (Story 1.6)
    - `demo/generated/smoke_test/Reducers/Ping.g.cs` exists (generated binding)
    - `demo/generated/smoke_test/SpacetimeDBClient.g.cs` exists (generated binding)
    - `demo/generated/smoke_test/Tables/SmokeTest.g.cs` exists (generated binding)
    - `spacetime/modules/smoke_test/src/lib.rs` exists (smoke test source module)
    - `addons/godot_spacetime/src/Public/SpacetimeClient.cs` exists (SDK public boundary)
    - `demo/README.md` contains `TokenStore` (Story 5.2 auth section intact)
    - `demo/README.md` contains `## Subscription` (Story 5.2 subscription section intact)
    - `demo/DemoMain.cs` contains `SubscriptionApplied` (Story 5.2 signal intact)
    - `demo/DemoMain.cs` contains `ProjectSettingsTokenStore` (Story 5.2 auth intact)

## Dev Notes

### What This Story Delivers

Story 5.3 completes the Epic 5 demo by adding reducer invocation and result handling to `DemoMain.cs`, closing the loop on the full supported integration lifecycle (connect → authenticate → subscribe → observe → mutate → react to result). The expected output for a healthy Ping call provides a concrete comparison baseline for developers troubleshooting their own reducer integration.

**Scope boundaries:**
- Only `demo/DemoMain.cs`, `demo/README.md`, `demo/scenes/reducer_smoke.tscn`, and the new test file are affected
- Do NOT create a separate `ReducerSmoke.cs` script — reducer interaction stays in `DemoMain.cs` (same assembly, same lifecycle node)
- `reducer_smoke.tscn` is a minimal placeholder scene (no script attached), matching `connection_smoke.tscn` format
- Do NOT modify the generated bindings in `demo/generated/smoke_test/` — they are read-only committed artifacts
- Do NOT modify `DemoBootstrap.cs`, `DemoMain.tscn`, `project.godot`, or any `addons/` files
- Do NOT modify any `docs/` files — documentation stories are Story 5.4+

### Critical Architecture Constraints

**`InvokeReducer` call timing:**
`InvokeReducer` must only be called after `ConnectionState.Connected` is reached. The safe call site in `DemoMain` is inside `OnSubscriptionApplied()`, which only fires after the connection is `Connected` and the subscription is confirmed. This is the correct place — do NOT call it in `_Ready()`, `OnConnectionStateChanged`, or before subscription is applied.

**`InvokeReducer` is a fire-and-forget call:**
`SpacetimeClient.InvokeReducer(object reducerArgs)` routes through `ReducerInvoker → SpacetimeSdkReducerAdapter`. The method returns immediately — it does NOT return the result. The server acknowledgement arrives asynchronously through `ReducerCallSucceeded` or `ReducerCallFailed` signals in a **later frame** (after `_Process → _connectionService.FrameTick()` delivers the queued server message). Do NOT await it, do NOT check a return value.

**Programming faults vs. server failures:**
`InvokeReducer` has two error categories:
- **Programming faults** (wrong state, null args, non-`IReducerArgs` object): surfaced via `ConnectionStateChanged` + `GD.PushError` — they do NOT fire `ReducerCallFailed`. These faults indicate developer error, not server-side outcomes.
- **Server failures** (rejected by server logic, out of energy): surfaced via `ReducerCallFailed` signal asynchronously. Handle in `OnReducerCallFailed`, not in `_Process`.

**`Reducer.Ping` type:**
The correct type is `SpacetimeDB.Types.Reducer.Ping` (from `demo/generated/smoke_test/Reducers/Ping.g.cs`). With `using SpacetimeDB.Types;` added, you can use `new Reducer.Ping()`. The type implements `IReducerArgs` with `ReducerName == "ping"`. The `ReducerCallResult.ReducerName` and `ReducerCallError.ReducerName` will both contain `"ping"` (lowercase, matching the server-side reducer name).

**Signal wiring pattern (established in Stories 5.1 and 5.2):**
Always use `handler -= ...` before `handler += ...` to prevent duplicate handlers. Apply the same `-= then +=` pattern to `ReducerCallSucceeded` and `ReducerCallFailed`. Unsubscribe in `_ExitTree()`.

**`ReducerCallResult` fields available (Story 4.2):**
```csharp
public string ReducerName { get; }    // "ping"
public string InvocationId { get; }   // opaque SDK-generated correlation ID
public DateTimeOffset CalledAt { get; }
public DateTimeOffset CompletedAt { get; }
```

**`ReducerCallError` fields available (Story 4.2):**
```csharp
public string ReducerName { get; }             // "ping"
public string InvocationId { get; }            // correlation ID
public string ErrorMessage { get; }            // human-readable server message
public ReducerFailureCategory FailureCategory { get; } // Failed | OutOfEnergy | Unknown
public string RecoveryGuidance { get; }        // user-safe branch guidance
public DateTimeOffset CalledAt { get; }
public DateTimeOffset FailedAt { get; }
```

**`ReducerFailureCategory` values:**
- `Failed`: server logic error or constraint violation; retrying same args is unlikely to succeed
- `OutOfEnergy`: back off and retry after a delay
- `Unknown`: handle defensively; do not auto-retry

### Project Structure Notes

**Files to modify:**
- `demo/DemoMain.cs` — extend (do NOT recreate; preserve all existing `_Ready`, `_ExitTree`, and signal handler logic from Stories 5.1 and 5.2)
- `demo/README.md` — add `## Reducer Interaction` section after `## Subscription and Live State` (preserve all existing sections)

**Files to create:**
- `demo/scenes/reducer_smoke.tscn` — minimal placeholder scene (no script)
- `tests/test_story_5_3_demonstrate_reducer_interaction.py` — new test file

**Files NOT to touch:**
- `demo/DemoMain.tscn` — no scene changes needed
- `demo/autoload/DemoBootstrap.cs` — stays minimal stub
- `demo/scenes/connection_smoke.tscn` — unchanged
- `demo/generated/smoke_test/` — read-only generated artifacts
- `addons/godot_spacetime/` — SDK addon code is out of scope
- `spacetime/modules/smoke_test/` — Rust source module is out of scope
- All `docs/*.md` — documentation stories are Story 5.4+

**Architecture directory structure (after Story 5.3):**
```
demo/
├── DemoMain.tscn          ← unchanged
├── DemoMain.cs            ← MODIFIED (Task 1)
├── README.md              ← MODIFIED (Task 3)
├── autoload/
│   └── DemoBootstrap.cs   ← unchanged
├── generated/
│   └── smoke_test/        ← read-only, do not touch
└── scenes/
    ├── connection_smoke.tscn   ← unchanged
    └── reducer_smoke.tscn      ← NEW (Task 2)
```

### SDK Surface Reference

**`SpacetimeClient` signals used in this story:**
```csharp
// Signal (Godot C# event syntax)
public event ReducerCallSucceededEventHandler? ReducerCallSucceeded;
// Fires in a later frame after InvokeReducer() — after FrameTick delivers the server message
// Inspect ReducerCallResult.InvocationId to correlate to a specific call

public event ReducerCallFailedEventHandler? ReducerCallFailed;
// Fires in a later frame after InvokeReducer() when server rejects or fails the call
// Inspect ReducerCallError.FailureCategory to branch retry vs. user feedback

// Method
public void InvokeReducer(object reducerArgs);
// Pass a generated IReducerArgs instance — here: new SpacetimeDB.Types.Reducer.Ping()
// Must be called after ConnectionState.Connected
// Programming faults (null, wrong state, non-IReducerArgs) surfaced via ConnectionStateChanged + GD.PushError
```

**Generated `Reducer.Ping` type (from `demo/generated/smoke_test/Reducers/Ping.g.cs`):**
```csharp
// namespace: SpacetimeDB.Types
// Type: abstract partial class Reducer → sealed partial class Ping (nested)
// Implements: IReducerArgs
// ReducerName: "ping"
new SpacetimeDB.Types.Reducer.Ping()   // fully qualified
// OR with "using SpacetimeDB.Types;": new Reducer.Ping()
```

**Full C# namespaces for this story:**
```csharp
using System.Linq;                         // existing — .ToList()
using Godot;                               // existing — GD.Print, Node
using GodotSpacetime;                      // existing — SpacetimeClient
using GodotSpacetime.Connection;           // existing — ConnectionState, ConnectionStatus
using GodotSpacetime.Reducers;             // NEW — ReducerCallResult, ReducerCallError, ReducerFailureCategory
using GodotSpacetime.Runtime.Auth;         // existing — ProjectSettingsTokenStore
using GodotSpacetime.Subscriptions;        // existing — SubscriptionHandle, SubscriptionStatus, events
using SpacetimeDB.Types;                   // NEW — Reducer.Ping (generated binding type)
```

### Connection and Reducer Lifecycle Flow

Complete expected Output panel sequence after Story 5.3 (first run, healthy environment):
```
[Demo] Bootstrap ready — godot-spacetime addon enabled         ← DemoBootstrap (unchanged)
[Demo] Connection state: CONNECTING — opening a session...     ← OnConnectionStateChanged
[Demo] Connection state: CONNECTED — active session ...        ← OnConnectionStateChanged
[Demo] Subscribed to smoke_test — awaiting initial sync        ← OnConnectionStateChanged(Connected)
[Demo] Session identity: (new — token will be stored)          ← OnConnectionOpened
[Demo] Subscription applied — N row(s) in smoke_test           ← OnSubscriptionApplied
[Demo] Ping reducer invoked — awaiting server acknowledgement  ← OnSubscriptionApplied (after row count)
[Demo] Reducer 'ping' succeeded (id: <invocation-id>)         ← OnReducerCallSucceeded (later frame)
```

On failure (server rejects or out of energy):
```
[Demo] Reducer 'ping' failed — Failed: <message> | guidance: <guidance>
```

**Async delivery guarantee:** The `ReducerCallSucceeded`/`ReducerCallFailed` signal fires after `_Process → _connectionService.FrameTick()` processes the queued server acknowledgement. It arrives in a frame AFTER the frame where `InvokeReducer` was called. Do NOT expect synchronous confirmation.

### C# Pattern for `DemoMain.cs` Reducer Section

```csharp
// In _Ready(), after RowChanged signal wiring:
_client.ReducerCallSucceeded -= OnReducerCallSucceeded;
_client.ReducerCallSucceeded += OnReducerCallSucceeded;

_client.ReducerCallFailed -= OnReducerCallFailed;
_client.ReducerCallFailed += OnReducerCallFailed;

// In _ExitTree(), after RowChanged cleanup:
_client.ReducerCallSucceeded -= OnReducerCallSucceeded;
_client.ReducerCallFailed -= OnReducerCallFailed;

// In OnSubscriptionApplied, AFTER the row count print and INSIDE the e.Handle guard:
_client!.InvokeReducer(new Reducer.Ping());
GD.Print("[Demo] Ping reducer invoked — awaiting server acknowledgement");

// New handler methods:
private void OnReducerCallSucceeded(ReducerCallResult result)
{
    GD.Print($"[Demo] Reducer '{result.ReducerName}' succeeded (id: {result.InvocationId})");
}

private void OnReducerCallFailed(ReducerCallError error)
{
    GD.Print($"[Demo] Reducer '{error.ReducerName}' failed — {error.FailureCategory}: {error.ErrorMessage} | guidance: {error.RecoveryGuidance}");
}
```

### Test File Conventions (from Story 5.1 and 5.2)

Tests are static file analysis using `pathlib.Path` — no Godot runtime, no pytest fixtures:

```python
ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")
```

Test function names: `test_<file_slug>_<what_is_checked>`. All assertions include a descriptive failure message string.

### References

- Story user story and AC: `_bmad-output/planning-artifacts/epics.md`, Epic 5 § Story 5.3
- Previous story (5.2): `_bmad-output/implementation-artifacts/5-2-extend-the-sample-through-auth-session-resume-and-live-subscription-flow.md`
- Previous story test baseline: 1591 tests passing (from Story 5.2 senior review)
- `SpacetimeClient` public surface: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- `ReducerCallResult`: `addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs`
- `ReducerCallError`: `addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs`
- `ReducerFailureCategory`: `addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs`
- Generated `Reducer.Ping`: `demo/generated/smoke_test/Reducers/Ping.g.cs`
- Architecture demo structure: `_bmad-output/planning-artifacts/architecture.md` § Complete Project Directory Structure
- Architecture boundary rule (demo is consumer): `_bmad-output/planning-artifacts/architecture.md` § Architectural Boundaries
- Reducer invocation chain: `addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs` → `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs`
- FR5: Sample project that proves supported setup path [Source: epics.md]
- NFR16: Reproducible onboarding path [Source: epics.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

Subtask 1.8 doc comment: Story 5.2 regression test (`test_demo_main_cs_xml_doc_references_story_52`) asserts "Story 5.2" must remain in `DemoMain.cs`. The story 5.3 task 1.8 "from...to" phrasing targets the placeholder phrase within the original comment. Resolved by updating only the placeholder portion: kept "Demo scene extended through Story 5.2 — ..." prefix and replaced "Story 5.3 adds reducer interaction" with the specified new text.
Senior Developer Review corrected the reducer troubleshooting docs so programming faults are not conflated with `ReducerCallFailed`, and expanded Story 5.3 tests to lock the reviewed invocation-order and log-contract behavior.

### Completion Notes List

- Extended `demo/DemoMain.cs` with `GodotSpacetime.Reducers` and `SpacetimeDB.Types` imports, `ReducerCallSucceeded`/`ReducerCallFailed` signal wiring (with `-= then +=` pattern), `InvokeReducer(new Reducer.Ping())` call inside `OnSubscriptionApplied()` handle guard, `OnReducerCallSucceeded` and `OnReducerCallFailed` handler methods, and cleanup in `_ExitTree()`.
- Created `demo/scenes/reducer_smoke.tscn` as a minimal placeholder scene (no script) matching `connection_smoke.tscn` format.
- Updated `demo/README.md` with `## Reducer Interaction` guidance covering success path, failure path, async `FrameTick` delivery, troubleshooting comparison output sequence, and the reviewed distinction between server-side reducer failures and programming faults surfaced through `ConnectionStateChanged` + `GD.PushError`.
- Expanded `tests/test_story_5_3_demonstrate_reducer_interaction.py` to 68 contract tests covering existence, DemoMain.cs content, README.md content, reducer_smoke.tscn content, regression guards, reviewed invocation ordering, exact reducer log strings, and programming-fault troubleshooting guidance. All 68 story tests pass.
- Validation: `dotnet build godot-spacetime.sln -c Debug --no-restore` succeeds with 0 errors / 0 warnings; full `pytest -q` regression is green at 1659 tests.

### File List

- `demo/DemoMain.cs` (modified)
- `demo/README.md` (modified, review-updated)
- `demo/scenes/reducer_smoke.tscn` (created)
- `tests/test_story_5_3_demonstrate_reducer_interaction.py` (created, review-expanded)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status updated)

## Change Log

- 2026-04-14: Story 5.3 implementation complete — reducer invocation (Ping) and result handling wired in DemoMain.cs, reducer_smoke.tscn scene created, README Reducer Interaction section added, 51 initial tests written.
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 1 High, 3 Medium fixed. Fixes: reducer troubleshooting docs now distinguish server failures from programming faults, Story 5.3 tests now lock the SubscriptionApplied invocation order and exact reducer log contract, and verification artifacts were synced to 68 story tests / 1659 suite tests. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List (`_bmad-output/implementation-artifacts/sprint-status.yaml`, `_bmad-output/implementation-artifacts/tests/test-summary.md`, `_bmad-output/story-automator/orchestration-1-20260414-184146.md`).

### Findings Fixed

- HIGH: `demo/README.md` documented only `ReducerCallSucceeded` / `ReducerCallFailed` outcomes and omitted the programming-fault comparison path described in `docs/runtime-boundaries.md`. That left the story's troubleshooting guidance incomplete and misaligned with the supported reducer workflow required by AC 2 and AC 3.
- MEDIUM: `tests/test_story_5_3_demonstrate_reducer_interaction.py` only checked loose token presence around the reducer invocation, so a regression could move `InvokeReducer(new Reducer.Ping())` outside the `SubscriptionApplied` handle guard or ahead of the row-count log while still passing.
- MEDIUM: The Story 5.3 tests did not lock the exact reducer success/failure log strings, so the documented comparison output could drift without a failing regression test.
- MEDIUM: Story 5.3 verification notes were stale after automation and no longer matched the reviewed test totals.

### Actions Taken

- Updated `demo/README.md` to distinguish server-acknowledged reducer failures from programming faults surfaced through `ConnectionStateChanged` + `GD.PushError`, including that those calling-code faults do not emit `ReducerCallFailed`.
- Expanded Story 5.3 contract coverage to assert the reviewed `OnSubscriptionApplied()` guard/order, the exact reducer success/failure log strings, and the reducer programming-fault troubleshooting guidance in the demo README.
- Updated this story artifact's completion notes and change log, then synced the story status and sprint-status entry to `done`.

### Validation

- `pytest -q tests/test_story_5_3_demonstrate_reducer_interaction.py`
- `dotnet build godot-spacetime.sln -c Debug --no-restore`
- `pytest -q`

### Reference Check

- No dedicated Story Context or Epic 5 tech-spec artifact was present; `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/architecture.md`, `docs/runtime-boundaries.md`, and the reviewed SDK source files were used as the applicable planning and standards references.
- Tech stack validated during review: Godot `.NET` sample code in C#, `.NET` `8.0+`, `pytest`, and the in-repo generated smoke-test bindings / runtime docs.
- Local reference: `demo/DemoMain.cs`
- Local reference: `demo/README.md`
- Local reference: `tests/test_story_5_3_demonstrate_reducer_interaction.py`
- Local reference: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- Local reference: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`
- Local reference: `addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs`
- Local reference: `docs/runtime-boundaries.md`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
