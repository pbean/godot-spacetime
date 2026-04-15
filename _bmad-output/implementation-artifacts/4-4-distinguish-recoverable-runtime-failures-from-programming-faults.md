# Story 4.4: Distinguish Recoverable Runtime Failures from Programming Faults

Status: done

## Story

As a Godot developer,
I want recoverable runtime failures distinguished from programming faults,
So that gameplay code can retry or inform the user appropriately without masking real defects.

## Acceptance Criteria

1. **Given** a runtime operation fails during reducer invocation or related gameplay interaction **When** the SDK reports the outcome **Then** recoverable operational failures are surfaced through structured runtime results or status events
2. **And** unrecoverable programming faults remain visible as diagnostics or exceptions rather than being silently downgraded
3. **And** the supported outcome model makes it clear how gameplay code should branch on success versus recoverable failure

## Tasks / Subtasks

- [x] Task 1: Fix `SpacetimeSdkReducerAdapter.Invoke()` null connection guard (AC: 2)
  - [x] 1.1 In `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs`, replace the null-connection silent-return with a throw:
    - **Remove:**
      ```csharp
      if (_dbConnection == null)
      {
          Console.Error.WriteLine("[GodotSpacetime] SpacetimeSdkReducerAdapter.Invoke called with no active connection — ignoring.");
          return;
      }
      ```
    - **Replace with:**
      ```csharp
      if (_dbConnection == null)
          throw new InvalidOperationException(
              "SpacetimeSdkReducerAdapter.Invoke requires an active DbConnection. " +
              "This is a programming fault — ensure ConnectionState.Connected is reached before invoking reducers.");
      ```
    - **Why:** The current `Console.Error.WriteLine` + `return` silently swallows the fault, violating the architecture principle "Unrecoverable programming faults remain exceptions and should not be hidden." By throwing, the exception is caught at `SpacetimeClient.InvokeReducer()` (which catches `InvalidOperationException`) and routed through `PublishValidationFailure()` → `GD.PushError(message)`, making the fault visible in the Godot error console.
    - **Note on `using System;`:** The existing file already imports `using System;` at the top (for `ArgumentNullException`, `ArgumentException`, `DateTimeOffset`, etc.) — the `using System;` import must NOT be removed. Only the `Console.Error.WriteLine` call is removed; the import stays.
    - **Behavioral note:** In practice this guard is never reached — `SpacetimeConnectionService.InvokeReducer()` throws `InvalidOperationException` before the adapter is called if not Connected. This is belt-and-suspenders: if the upper guard ever breaks, the error propagates visibly instead of silently.

- [x] Task 2: Update `runtime-boundaries.md` Guard description (AC: 3)
  - [x] 2.1 Find the **Guard:** paragraph in the "Reducer Invocation" section (currently: "If called in any other state, or with a non-`IReducerArgs` object, `ConnectionStateChanged` fires with a validation error description and the call is discarded.")
  - [x] 2.2 Replace that paragraph with an accurate description of the actual behavior:
    - Mention `InvalidOperationException` (wrong connection state), `ArgumentNullException` (null arg), `ArgumentException` (non-`IReducerArgs` type)
    - Explain these are caught at `SpacetimeClient.InvokeReducer()` — they do NOT propagate to game code as thrown exceptions
    - Explain `PublishValidationFailure`: fires `ConnectionStateChanged(Disconnected, message)` AND calls `GD.PushError(message)` — the error appears in the Godot error console
    - Clarify these are **programming faults** (code defects), not gameplay-handleable conditions

- [x] Task 3: Add "Programming Faults vs Recoverable Failures" section to `runtime-boundaries.md` (AC: 1, 2, 3)
  - [x] 3.1 Add a new subsection **"Reducer Error Model: Programming Faults vs Recoverable Failures"** after the Guard paragraph in the Reducer Invocation section. It must cover:
    - **Recoverable runtime failures** → come through `ReducerCallFailed` signal as `ReducerCallError` → branch on `FailureCategory` (`Failed`, `OutOfEnergy`, `Unknown`) → use `RecoveryGuidance` for player-facing feedback → these are expected gameplay conditions
    - **Programming faults** (SDK misuse) → `InvalidOperationException`/`ArgumentNullException`/`ArgumentException` caught at `SpacetimeClient` boundary → surfaced via `GD.PushError` + `ConnectionStateChanged(Disconnected)` → these are code defects, NOT conditions for `ReducerCallFailed` signal handlers
    - **Branching guidance table** (see Dev Notes §Reference Implementation below for the exact shape)
    - The key rule: **Never check `ReducerCallError.FailureCategory` when the fault is a programming error** — the `ReducerCallFailed` signal will not fire for programming faults; only `ConnectionStateChanged` + `GD.PushError` fire

- [x] Task 4: Write test file `tests/test_story_4_4_distinguish_recoverable_runtime_failures.py` (AC: 1, 2, 3)
  - [x] 4.1 Tests for Task 1 (adapter null guard change):
    - `SpacetimeSdkReducerAdapter.cs` null-connection guard throws `InvalidOperationException` (look for `throw new InvalidOperationException` inside `Invoke` method near `_dbConnection == null`)
    - `SpacetimeSdkReducerAdapter.cs` does NOT use `Console.Error.WriteLine` in `Invoke` (the silent swallow is gone)
    - `SpacetimeSdkReducerAdapter.cs` still checks `_dbConnection == null` (guard still present, just throws now)
    - `SpacetimeSdkReducerAdapter.cs` still imports `using System;` (the remove of `Console.Error` must not remove the using)
  - [x] 4.2 Tests for Task 2+3 (docs accurately describe the fault model):
    - `runtime-boundaries.md` Guard paragraph mentions `InvalidOperationException` (not just "ConnectionStateChanged fires")
    - `runtime-boundaries.md` mentions `GD.PushError` in the reducer context (programming fault visibility)
    - `runtime-boundaries.md` has a "programming fault" section or paragraph in the reducer area
    - `runtime-boundaries.md` distinguishes recoverable failures from programming faults explicitly
    - `runtime-boundaries.md` mentions `FailureCategory` in the context of recoverable failure branching
    - `runtime-boundaries.md` clarifies `ReducerCallFailed` does NOT fire for programming faults (or equivalent — only fires for server-side failures)
  - [x] 4.3 Regression guards — full fault chain still intact:
    - `SpacetimeConnectionService.cs` still throws `InvalidOperationException` for wrong connection state in `InvokeReducer()`
    - `ReducerInvoker.cs` still uses `ArgumentNullException.ThrowIfNull(reducerArgs)` (null guard at invoker layer)
    - `SpacetimeSdkReducerAdapter.cs` still throws `ArgumentException` for non-`IReducerArgs` type (type guard at adapter layer)
    - `SpacetimeClient.cs` `InvokeReducer` still catches `ArgumentNullException`, `ArgumentException`, `InvalidOperationException` (all three)
    - `SpacetimeClient.cs` `InvokeReducer` calls `PublishValidationFailure` for all caught fault types
    - `SpacetimeClient.cs` `PublishValidationFailure` calls `GD.PushError` (fault visibility in Godot console)
  - [x] 4.4 Regression guards — recoverable failure types still intact:
    - `ReducerCallError.cs` still has `FailureCategory` property (`ReducerFailureCategory` type)
    - `ReducerCallError.cs` still has `RecoveryGuidance` property
    - `ReducerFailureCategory.cs` still has `Failed`, `OutOfEnergy`, `Unknown` cases
    - `SpacetimeSdkReducerAdapter.cs` `ExtractAndDispatch` still maps `Status.Committed` → `OnReducerCallSucceeded`
    - `SpacetimeSdkReducerAdapter.cs` `ExtractAndDispatch` still maps `Status.Failed` → `OnReducerCallFailed` with `ReducerFailureCategory.Failed`
    - `SpacetimeSdkReducerAdapter.cs` `ExtractAndDispatch` still maps `Status.OutOfEnergy` → `OnReducerCallFailed` with `ReducerFailureCategory.OutOfEnergy`
  - [x] 4.5 Regression guards — Story 4.3 signal bridge still intact:
    - `SpacetimeClient.cs` `ConnectionClosedEventHandler` signal delegate still present
    - `SpacetimeClient.cs` `HandleConnectionClosed` method still present
    - `SpacetimeConnectionService.cs` `_isTearingDownConnection` teardown guard still present

## Dev Notes

### What This Story Delivers

Epic 4 established the full reducer invocation pipeline (4.1), recoverable failure payloads (4.2), and the scene-safe signal bridge (4.3). Story 4.4 completes the picture by:

1. **Fixing the one silent swallow** in the codebase: `SpacetimeSdkReducerAdapter.Invoke()` currently swallows a programming fault with `Console.Error.WriteLine` + `return` instead of throwing, preventing the error from reaching `GD.PushError`.
2. **Correcting and expanding the docs**: `runtime-boundaries.md` currently describes the Guard behavior inaccurately and does not explain the programming fault vs recoverable failure distinction.
3. **No new public types**: All existing types (`ReducerCallError`, `ReducerCallResult`, `ReducerFailureCategory`) already satisfy AC1 — recoverable failures are already surfaced through the signal system. This story adds zero new public surface area; it fixes an internal guard and clarifies documentation.

### The Fault Chain (How Programming Faults Surface)

```
SpacetimeClient.InvokeReducer(object reducerArgs)
  ├─ catch (ArgumentNullException ex)  → PublishValidationFailure(ex.Message)
  ├─ catch (ArgumentException ex)      → PublishValidationFailure(ex.Message)
  └─ catch (InvalidOperationException ex) → PublishValidationFailure(ex.Message)

PublishValidationFailure(string message)
  ├─ HandleStateChanged(new ConnectionStatus(ConnectionState.Disconnected, message))
  │     → fires ConnectionStateChanged signal
  └─ GD.PushError(message)
        → visible in Godot error console (Editor Output panel / in-game error overlay)
```

**Fault sources:**
- `ReducerInvoker.Invoke(null)` → `ArgumentNullException.ThrowIfNull(reducerArgs)` → caught as `ArgumentNullException`
- `SpacetimeSdkReducerAdapter.Invoke(notIReducerArgs)` → `throw new ArgumentException(...)` → caught as `ArgumentException`
- `SpacetimeConnectionService.InvokeReducer()` when not Connected → `throw new InvalidOperationException(...)` → caught as `InvalidOperationException`
- **After Task 1 fix**: `SpacetimeSdkReducerAdapter.Invoke()` when `_dbConnection == null` → `throw new InvalidOperationException(...)` → caught as `InvalidOperationException`

**Important behavior detail:** `PublishValidationFailure` updates `SpacetimeClient._currentStatus` to `Disconnected` and fires `ConnectionStateChanged`. This is a deliberate design choice — programming faults surface as state change events at the Godot boundary, consistent with Godot's philosophy of not letting C# exceptions propagate unhandled from gameplay code. The underlying `_connectionService` connection is NOT actually disconnected by this. The `GD.PushError` is the primary visibility mechanism for developers to diagnose the fault.

### The Recoverable Failure Path (Already Implemented — Do Not Change)

```
SpacetimeSdkReducerAdapter.ExtractAndDispatch(sink, ctx)
  ├─ Status.Committed → sink.OnReducerCallSucceeded(...)  → ReducerCallSucceeded signal
  ├─ Status.Failed    → sink.OnReducerCallFailed(..., ReducerFailureCategory.Failed, ...)    → ReducerCallFailed signal
  ├─ Status.OutOfEnergy → sink.OnReducerCallFailed(..., ReducerFailureCategory.OutOfEnergy, ...) → ReducerCallFailed signal
  └─ default          → sink.OnReducerCallFailed(..., ReducerFailureCategory.Unknown, ...)   → ReducerCallFailed signal
```

Recoverable failures arrive **asynchronously** after the server responds. They ALWAYS go through `ReducerCallFailed` with a structured `ReducerCallError`. **Do NOT route programming faults through this path** — `ReducerCallFailed` is reserved for server-acknowledged outcomes.

### Reference Implementation for Docs Section (Task 3)

The "Reducer Error Model: Programming Faults vs Recoverable Failures" section should include a table like:

| Condition | How it surfaces | What gameplay code does |
|-----------|----------------|------------------------|
| Server rejects reducer (logic/constraint) | `ReducerCallFailed` → `ReducerCallError.FailureCategory = Failed` | Branch on `FailureCategory`; show player error |
| Server out of energy | `ReducerCallFailed` → `ReducerCallError.FailureCategory = OutOfEnergy` | Back off, retry after delay |
| Status unclear (SDK internal) | `ReducerCallFailed` → `ReducerCallError.FailureCategory = Unknown` | Handle defensively, do not auto-retry |
| Called while not Connected | `ConnectionStateChanged(Disconnected)` + `GD.PushError` | Fix the calling code; not a gameplay condition |
| Called with null args | `ConnectionStateChanged(Disconnected)` + `GD.PushError` | Fix the calling code; not a gameplay condition |
| Called with non-IReducerArgs type | `ConnectionStateChanged(Disconnected)` + `GD.PushError` | Fix the calling code; not a gameplay condition |

### Why `using System;` Must NOT Be Removed

`SpacetimeSdkReducerAdapter.cs` uses `using System;` for: `ArgumentNullException`, `ArgumentException`, `DateTimeOffset`, `ConditionalWeakTable`, `Guid`. Removing `Console.Error.WriteLine` removes the `Console` usage but does NOT make `System` unused. The `using System;` import must remain.

### Project Structure Notes

**Modified files (Task 1 + Task 2 + Task 3):**
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` — fix null-connection guard in `Invoke()`
- `docs/runtime-boundaries.md` — fix Guard paragraph + add Programming Faults vs Recoverable Failures section

**New file (Task 4):**
- `tests/test_story_4_4_distinguish_recoverable_runtime_failures.py`

**No new public types** — the existing `ReducerCallError`, `ReducerCallResult`, and `ReducerFailureCategory` already satisfy AC1.

**File placement:** `SpacetimeSdkReducerAdapter.cs` is at `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` — this is the ONLY file in the codebase that imports `SpacetimeDB.*`. The `using System;` at the top must NOT be removed (see note above).

**Existing test NOT broken by Task 1:**  
`test_reducer_adapter_invoke_guards_null_connection` (in `tests/test_story_4_1_invoke_generated_reducers.py`) checks only for `_dbConnection == null` guard PRESENCE — it does NOT assert `return` or `Console.Error`. The fix (changing to `throw`) will NOT break this test.

**Architecture alignment:**
- Architecture doc: "Unrecoverable programming faults remain exceptions and should not be hidden." [Source: `_bmad-output/planning-artifacts/architecture.md`, Format Patterns section]
- Architecture doc: "Distinguish user-facing operational errors from internal diagnostics." [Source: `_bmad-output/planning-artifacts/architecture.md`, Error Handling Patterns section]
- Architecture doc: "Recoverable runtime failures surface as typed errors or status events." [Source: `_bmad-output/planning-artifacts/architecture.md`, Format Patterns section]

### References

- FR27: "Developers can distinguish between successful runtime operations and recoverable failures." [Source: `_bmad-output/planning-artifacts/prd.md`]
- Architecture error model: "Recoverable runtime failures surface as typed errors or status events. Unrecoverable programming faults remain exceptions and should not be hidden." [Source: `_bmad-output/planning-artifacts/architecture.md`, Format Patterns → API Response Formats]
- Architecture error handling: "Distinguish user-facing operational errors from internal diagnostics." [Source: `_bmad-output/planning-artifacts/architecture.md`, Process Patterns → Error Handling Patterns]
- Silent swallow location: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs`, `Invoke()` method, lines 62-67
- Guard documentation (to fix): `docs/runtime-boundaries.md`, "Reducer Invocation" section, **Guard:** paragraph (currently says "ConnectionStateChanged fires")
- `PublishValidationFailure` pattern: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`, lines 227-230
- `SpacetimeClient.InvokeReducer()` catch chain: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`, lines 199-217
- `SpacetimeConnectionService.InvokeReducer()` throws `InvalidOperationException` for wrong state: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`, lines 237-244
- `ReducerInvoker.Invoke()` null guard: `addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs`, lines 22-26
- `ReducerCallError` + `ReducerFailureCategory` recoverable failure types: `addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs`, `ReducerFailureCategory.cs`
- Existing null guard test (NOT broken): `tests/test_story_4_1_invoke_generated_reducers.py`, `test_reducer_adapter_invoke_guards_null_connection` (line 441)
- Test baseline: 1434 tests (end of Story 4.3 senior review)
- Tech stack: Godot 4.6.2, .NET 8+, SpacetimeDB.ClientSDK 2.1.0

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was straightforward. One regression caught and fixed during test run: my rewording of the Guard paragraph changed "non-`IReducerArgs` object" to "non-`IReducerArgs` type", which broke an existing 4.1 test (`test_runtime_boundaries_mentions_invalid_reducer_argument_guard`). Fixed by restoring the word "object" in the new Guard text.

### Completion Notes List

- **Task 1**: Replaced `Console.Error.WriteLine` + silent `return` in `SpacetimeSdkReducerAdapter.Invoke()` with `throw new InvalidOperationException(...)`. The `using System;` import was preserved — it is still needed for `ArgumentNullException`, `ArgumentException`, `DateTimeOffset`, `ConditionalWeakTable`, and `Guid`. The belt-and-suspenders guard now propagates visibly via `GD.PushError` through the existing `SpacetimeClient.InvokeReducer()` catch chain.
- **Task 2+3**: Updated the Guard paragraph in `docs/runtime-boundaries.md` to name the three exception types (`InvalidOperationException`, `ArgumentNullException`, `ArgumentException`) and explain they are caught at `SpacetimeClient` and surfaced via `GD.PushError`. Added a full "Reducer Error Model: Programming Faults vs Recoverable Failures" subsection with a branching table covering all six conditions. The `ReducerCallFailed`-does-not-fire-for-programming-faults rule is clearly stated.
- **Task 4**: 29 new tests written and passing (1463 total, 0 failures). Tests cover: Task 1 adapter guard change, Task 2+3 doc accuracy, full fault chain regression guards, recoverable failure type regression guards, and Story 4.3 signal bridge regression guards.

### File List

- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` (modified)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (modified — public XML docs aligned during senior review)
- `docs/runtime-boundaries.md` (modified)
- `tests/test_story_4_4_distinguish_recoverable_runtime_failures.py` (new, then modified during senior review to tighten method/section-scoped assertions and lock the `ConnectionClosed` clarification)
- `_bmad-output/implementation-artifacts/tests/test-summary.md` (modified — Story 4.4 review summary updated to 35 story tests / 1469 suite tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — story status synced to done)

## Change Log

- 2026-04-14: Story 4.4 implemented — fixed null-connection silent swallow in SpacetimeSdkReducerAdapter.Invoke() (throw instead of return), updated runtime-boundaries.md Guard paragraph with accurate exception types, added Programming Faults vs Recoverable Failures error model section and branching table, added 29 new tests (1463 total passing).
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 0 High, 4 Medium fixed. Fixes: reducer programming-fault docs now use a real subsection heading and clarify that the validation-failure path does not emit `ConnectionClosed`; `SpacetimeClient.InvokeReducer` XML docs now match the reviewed fault model; Story 4.4 tests now assert against the specific reducer methods/docs section; story/test artifacts were synced to the reviewed 35 story tests / 1469 suite tests. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` beyond the original implementation File List (`_bmad-output/story-automator/orchestration-1-20260414-184146.md`, `_bmad-output/implementation-artifacts/tests/test-summary.md`, and `_bmad-output/implementation-artifacts/sprint-status.yaml`).

### Findings Fixed

- MEDIUM: `docs/runtime-boundaries.md` added the reducer error-model content, but the new section was formatted as bold text instead of a real subsection heading and it did not clarify that the programming-fault validation path does not emit `ConnectionClosed`. That left the reducer docs weaker than the story asked for and easy to misread against the earlier connection-lifecycle section.
- MEDIUM: `addons/godot_spacetime/src/Public/SpacetimeClient.cs` still exposed stale XML docs on `InvokeReducer()`. IDE consumers only saw generic "validation error" wording instead of the reviewed programming-fault vs recoverable-failure contract and `GD.PushError` visibility path.
- MEDIUM: `tests/test_story_4_4_distinguish_recoverable_runtime_failures.py` relied on broad file-level string checks for several reducer-path assertions. Those tests could stay green even if the specific `Invoke()` / `InvokeReducer()` bodies or reducer docs section regressed while the same tokens appeared elsewhere in the file.
- MEDIUM: Story 4.4 verification artifacts were stale after review. The story-specific test summary still reported 34 Story 4.4 tests / 1468 suite tests, but the reviewed result is 35 Story 4.4 tests / 1469 suite tests.

### Actions Taken

- Promoted the reducer error-model text in `docs/runtime-boundaries.md` to a real subsection heading and clarified that the reducer programming-fault validation path is diagnostic surfacing, not a `ConnectionClosed` session-close event.
- Updated `SpacetimeClient.InvokeReducer()` XML docs to describe the reviewed programming-fault boundary, including `ConnectionStateChanged` + `GD.PushError` surfacing and the fact that `ReducerCallFailed` remains reserved for server outcomes.
- Tightened Story 4.4 regression tests by extracting the concrete `Invoke()`, `InvokeReducer()`, and `PublishValidationFailure()` method bodies plus the reducer-doc section before asserting behavior, and added an explicit regression check for the new `ConnectionClosed` clarification.
- Re-ran Story 4.1 through 4.4 reducer contract tests, `dotnet build`, and the full pytest suite after the review fixes.
- Synced the Story 4.4 status and sprint-status entry to `done`, and updated the shared 4.4 test summary to the reviewed 35 / 1469 counts.

### Validation

- `pytest -q tests/test_story_4_4_distinguish_recoverable_runtime_failures.py tests/test_story_4_1_invoke_generated_reducers.py tests/test_story_4_2_surface_reducer_results.py tests/test_story_4_3_bridge_runtime_callbacks.py`
- `dotnet build godot-spacetime.sln`
- `pytest -q`

### Reference Check

- No dedicated Story Context or Epic 4 tech-spec artifact was present; `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/prd.md`, and `docs/runtime-boundaries.md` were used as the applicable planning and standards references.
- Tech stack validated during review: Godot `4.6.2`, `.NET` `8.0+`, `SpacetimeDB.ClientSDK` `2.1.0`.
- Local references reviewed: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs`, `addons/godot_spacetime/src/Public/SpacetimeClient.cs`, `docs/runtime-boundaries.md`.
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
