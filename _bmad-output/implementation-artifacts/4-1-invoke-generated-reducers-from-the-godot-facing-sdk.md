# Story 4.1: Invoke Generated Reducers from the Godot-Facing SDK

Status: done

## Story

As a Godot developer,
I want to call SpacetimeDB reducers through the Godot-facing SDK,
So that gameplay code can mutate server state without implementing protocol details itself.

## Acceptance Criteria

1. **Given** an active supported client session and generated module bindings **When** gameplay code invokes a reducer through the SDK **Then** the call is routed through the supported generated reducer path rather than custom protocol code
2. **Given** a reducer invocation is made **When** the inputs are constructed using the generated binding types **Then** typed inputs required by the reducer are validated or enforced at the supported boundary
3. **Given** a `SpacetimeClient` node registered in the scene **When** a game script calls its public reducer invocation method **Then** the invocation path is available from normal Godot gameplay code

## Tasks / Subtasks

- [x] Task 1: Implement `SpacetimeSdkReducerAdapter` (AC: 1, 2)
  - [x] 1.1 Remove the `#pragma warning disable CS0169` and the dead `_dbConnection` field stub
  - [x] 1.2 Add private `IDbConnection?` field named `_dbConnection` (no pragma suppression needed once it is actually used)
  - [x] 1.3 Add `internal void SetConnection(IDbConnection? connection)` so the connection service can inject/clear the connection
  - [x] 1.4 Add `internal void Invoke(object reducerArgs)` — null-check `_dbConnection` first (return silently if null, log a warning via `GD.PushWarning` if available or `Console.Error.WriteLine`); cast `reducerArgs` to `SpacetimeDB.IReducerArgs` inside the adapter (isolation zone); call `_dbConnection.InternalCallReducer((IReducerArgs)reducerArgs)`
  - [x] 1.5 Add `internal void ClearConnection()` that sets `_dbConnection = null` (called on disconnect)
  - [x] 1.6 `using SpacetimeDB;` already present — only file allowed to reference SpacetimeDB reducer types

- [x] Task 2: Create `Internal/Reducers/ReducerInvoker.cs` (AC: 1, 2)
  - [x] 2.1 Create `addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs`
  - [x] 2.2 Namespace: `GodotSpacetime.Runtime.Reducers`
  - [x] 2.3 Class: `internal sealed class ReducerInvoker` — no SpacetimeDB imports
  - [x] 2.4 Hold a reference to `SpacetimeSdkReducerAdapter _adapter` (passed via constructor or set via `SetAdapter`)
  - [x] 2.5 Add `internal void Invoke(object reducerArgs)` — validate that reducerArgs is not null (throw `ArgumentNullException`); delegate to `_adapter.Invoke(reducerArgs)`
  - [x] 2.6 No state tracking in Story 4.1 (results/callbacks are Story 4.2) — this is intentionally minimal

- [x] Task 3: Wire `ReducerInvoker` into `SpacetimeConnectionService` (AC: 1, 3)
  - [x] 3.1 Add `private readonly SpacetimeSdkReducerAdapter _reducerAdapter = new();` field
  - [x] 3.2 Add `private readonly ReducerInvoker _reducerInvoker = new(/* inject adapter */);` (adapt construction approach to match existing field init pattern — prefer constructor injection if ReducerInvoker takes the adapter; otherwise pass adapter after construction)
  - [x] 3.3 In `IConnectionEventSink.OnConnected` (the sink callback where the service learns the connection is live): call `_reducerAdapter.SetConnection(_adapter.Connection)` — this is the correct injection point because `_adapter.Connection` is only guaranteed non-null once `OnConnected` fires
  - [x] 3.4 In `ResetDisconnectedSessionState()` (the shared teardown method called by both `private Disconnect(string description)` and `IConnectionEventSink.HandleDisconnectError`/`OnDisconnected`): add `_reducerAdapter.ClearConnection()` — placing it here covers ALL exit paths (explicit disconnect and connection-lost) in a single location
  - [x] 3.5 Add `public void InvokeReducer(object reducerArgs)` to `SpacetimeConnectionService`:
    - Check `CurrentStatus.State == ConnectionState.Connected`; if not, throw `InvalidOperationException("InvokeReducer() requires an active Connected session.")`
    - Delegate to `_reducerInvoker.Invoke(reducerArgs)`
  - [x] 3.6 **Disconnect path checklist (required per Epic 3 Retro action P1):**
    - Explicit disconnect via `SpacetimeClient.Disconnect()`: routes to `SpacetimeConnectionService.Disconnect()` → `private Disconnect(string)` → `ResetDisconnectedSessionState()` → `_reducerAdapter.ClearConnection()` ✓
    - Connection lost mid-session (`OnDisconnected` SDK callback fires): routes to `IConnectionEventSink.OnDisconnected` / `HandleDisconnectError` → `ResetDisconnectedSessionState()` → `_reducerAdapter.ClearConnection()` ✓ (same shared path)
    - Failed connect (never reached `Connected` state): `_reducerAdapter.SetConnection` never called; `InvokeReducer` state check prevents invoke when not `Connected`; no teardown needed ✓
    - Rapid reconnect (Disconnect + Connect): `ClearConnection()` in `ResetDisconnectedSessionState()` clears old connection; `SetConnection()` in `OnConnected` injects new one ✓

- [x] Task 4: Add public `InvokeReducer` to `SpacetimeClient` (AC: 1, 2, 3)
  - [x] 4.1 Add `public void InvokeReducer(object reducerArgs)` to `SpacetimeClient.cs` — place it after `GetRows()`
  - [x] 4.2 Body: delegate to `_connectionService.InvokeReducer(reducerArgs)` with the same `InvalidOperationException` catch+`PublishValidationFailure` guard pattern used by `ReplaceSubscription` (note: `Subscribe` does NOT have a try/catch — use `ReplaceSubscription` as the model since both check connected state and throw `InvalidOperationException`)
  - [x] 4.3 Add XML summary doc: the method accepts a generated `IReducerArgs` instance (e.g. `new SpacetimeDB.Types.Reducer.Ping()`) and routes it through the supported generated reducer path; it must be called after `ConnectionState.Connected` is reached; throws or fires `ConnectionStateChanged` with a validation error if called in the wrong state
  - [x] 4.4 No new signal needed for Story 4.1 (reducer result events are Story 4.2)

- [x] Task 5: Update `docs/runtime-boundaries.md` (AC: 1, 3)
  - [x] 5.1 Add a `Reducer Invocation` section documenting: `SpacetimeClient.InvokeReducer(object reducerArgs)`, that the parameter must be an `IReducerArgs` instance from generated bindings, and that the invocation routes through `ReducerInvoker` → `SpacetimeSdkReducerAdapter` → the runtime SDK call
  - [x] 5.2 Note the isolation zone: SpacetimeDB reducer types are referenced only inside `SpacetimeSdkReducerAdapter`

- [x] Task 6: Write test file (AC: 1, 2, 3)
  - [x] 6.1 Create `tests/test_story_4_1_invoke_generated_reducers.py` — follow established test structure (`ROOT`, `_read()`, `_lines()` helpers)
  - [x] 6.2 Tests for `SpacetimeSdkReducerAdapter.cs`: file exists at `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs`, `Invoke` method present, `SetConnection` method present, `ClearConnection` method present, `using SpacetimeDB;` import present, old pragma-suppressed dead field is gone
  - [x] 6.3 Tests for `ReducerInvoker.cs`: file exists at `addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs`, namespace `GodotSpacetime.Runtime.Reducers`, class `ReducerInvoker` present, `Invoke` method present, NO SpacetimeDB import
  - [x] 6.4 Tests for `SpacetimeConnectionService.cs`: `_reducerAdapter` field present, `_reducerInvoker` field present, `InvokeReducer` method present, `SetConnection` call appears in the connect path, `ClearConnection` call appears in the disconnect/teardown path
  - [x] 6.5 Tests for `SpacetimeClient.cs`: `InvokeReducer` method present, `_connectionService.InvokeReducer` delegation call present
  - [x] 6.6 Tests for `docs/runtime-boundaries.md`: `InvokeReducer` mentioned, `ReducerInvoker` mentioned, `SpacetimeSdkReducerAdapter` mentioned
  - [x] 6.7 **Dynamic lifecycle test (required per Epic 3 Retro action P2):** At least one test that verifies `ClearConnection` appears inside the `ResetDisconnectedSessionState` method body in `SpacetimeConnectionService.cs` (static text check is acceptable since full lifecycle tests require a running server); the test must specifically check `ResetDisconnectedSessionState` — checking anywhere in the file is insufficient since `ClearConnection` must be in the shared teardown path that covers both explicit disconnect and connection-lost scenarios
  - [x] 6.8 Regression guards: prior story deliverables intact — `SubscriptionApplied` signal, `SubscriptionFailed` signal, `RowChanged` signal, `GetRows`, `Subscribe`, `Unsubscribe`, `ReplaceSubscription`, `SubscriptionStatus`, `SubscriptionHandle`, `_pendingReplacements`, `TryGetEntry` in registry, `OnSubscriptionFailed` event in service

## Dev Notes

### Critical: Generated Binding Shape — Inspect Before Implementing (Retro Action P3)

**This inspection is already done for Story 4.1** (satisfies Epic 3 Retro action P3: "Adopt generated bindings inspection as mandatory step before any SDK adapter story").

From `demo/generated/smoke_test/Reducers/Ping.g.cs`:

```csharp
public sealed partial class RemoteReducers : RemoteBase
{
    public void Ping()
    {
        conn.InternalCallReducer(new Reducer.Ping());  // conn: IDbConnection
    }
}
```

From `demo/generated/smoke_test/SpacetimeDBClient.g.cs`:
- `DbConnection` has `public readonly RemoteReducers Reducers;` — a **public field**, not a property (same field-vs-property surprise as Story 3.3; do not access via `.GetProperty("Reducers")` reflection)
- The generated reducer args type (e.g. `Reducer.Ping`) implements `SpacetimeDB.IReducerArgs`
- `IReducerArgs.ReducerName => "ping"` is the interface implementation

**The invocation path is `IDbConnection.InternalCallReducer(IReducerArgs args)` — a direct interface method on `IDbConnection`, no reflection needed.**

### What Already Exists (Do Not Reinvent)

- `SpacetimeSdkReducerAdapter.cs` at `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` — stub with `#pragma`-suppressed `IDbConnection?` field; replace entirely per Task 1
- `Public/Reducers/ReducerCallResult.cs` — stub `public record ReducerCallResult;` — DO NOT change in Story 4.1; it belongs to Story 4.2
- `Public/Reducers/ReducerCallError.cs` — stub `public class ReducerCallError {}` — DO NOT change in Story 4.1; it belongs to Story 4.2
- `Internal/Reducers/` directory does NOT exist yet — create it for `ReducerInvoker.cs`
- `SpacetimeConnectionService._adapter` (type `SpacetimeSdkConnectionAdapter`) exposes `internal IDbConnection? Connection => _dbConnection` — use `_adapter.Connection` to get the live connection, **but do not pass it directly to `ReducerInvoker`** (keep `_reducerAdapter` as a sibling field that is injected with the connection)

### Architecture Constraints — Isolation Zone

From `docs/runtime-boundaries.md` and architecture:
- `Internal/Platform/DotNet/` is the ONLY location that references `SpacetimeDB.*` types directly
- `SpacetimeConnectionService`, `ReducerInvoker`, and `SpacetimeClient` must NOT import `SpacetimeDB.*`
- The public API `SpacetimeClient.InvokeReducer(object reducerArgs)` takes `object` — this preserves the isolation zone
- The consuming developer calls: `_client.InvokeReducer(new SpacetimeDB.Types.Reducer.Ping())` — the C# type system enforces the `IReducerArgs` contract at the generated binding level, satisfying AC 2
- The adapter casts `object` → `IReducerArgs` and validates the type at the boundary inside `SpacetimeSdkReducerAdapter.Invoke`

### Service Pattern to Mirror (from SpacetimeConnectionService.Subscribe)

```csharp
// Pattern: check state → get connection → delegate to adapter
public SubscriptionHandle Subscribe(string[] querySqls)
{
    if (CurrentStatus.State != ConnectionState.Connected)
        throw new InvalidOperationException("Subscribe() requires an active Connected session...");
    var connection = _adapter.Connection
        ?? throw new InvalidOperationException("Not connected — no active IDbConnection...");
    ...
    _subscriptionAdapter.Subscribe(connection, querySqls, this, handle);
}
```

For `InvokeReducer`, use the same state check. The connection is already injected into `_reducerAdapter` via `SetConnection`, so the adapter call is `_reducerAdapter.Invoke(reducerArgs)` directly.

### Error Handling for Invalid reducerArgs Type

Inside `SpacetimeSdkReducerAdapter.Invoke(object reducerArgs)`:
- Cast with `as` and null-check, OR use `is` pattern match: `if (reducerArgs is not SpacetimeDB.IReducerArgs args) throw new ArgumentException(...)`
- This provides a clear error when non-IReducerArgs object is mistakenly passed

### Disconnect Path Coverage (Required — Epic 3 Retro Action P1)

Every stateful adapter story must enumerate all disconnect paths in dev notes.

**`SpacetimeSdkReducerAdapter` has one piece of state: `_dbConnection`.**

| Exit Path | Handling |
|-----------|----------|
| `SpacetimeClient.Disconnect()` explicit | `SpacetimeConnectionService.Disconnect()` → `_adapter.Close()` → should also call `_reducerAdapter.ClearConnection()` in the same teardown sequence |
| `OnDisconnected` callback from SDK (connection lost, server closed) | `IConnectionEventSink.OnDisconnected` in `SpacetimeConnectionService` — add `_reducerAdapter.ClearConnection()` here too |
| Connection never reached `Connected` (connect failed) | `_reducerAdapter.SetConnection` is only called in the connected path; `InvokeReducer` state check prevents invoke when not `Connected`; no cleanup needed |
| Rapid reconnect (Disconnect + Connect) | `ClearConnection()` called on disconnect; `SetConnection()` called on next connected; adapter correctly tracks new connection |

### Dynamic Lifecycle Test (Required — Epic 3 Retro Action P2)

Story 4.1 has a stateful adapter (`_dbConnection` in the reducer adapter). At least one test in the test file must verify that `ClearConnection` or equivalent teardown is visible in the disconnect path of `SpacetimeConnectionService.cs`. A static text-presence check on the source file is acceptable (full lifecycle tests require a live server).

### File Structure

New files:
- `addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs`
- `tests/test_story_4_1_invoke_generated_reducers.py`

Modified files:
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` (implement stub)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (add `_reducerAdapter`, `_reducerInvoker`, `InvokeReducer`, connect/disconnect wiring)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (add `public InvokeReducer`)
- `docs/runtime-boundaries.md` (document reducer invocation path)

### Tech Debt to Be Aware Of (Do NOT fix in this story)

- `ConnectionAuthState.AuthRequired` dead code — 3 epics overdue (D1 from Epic 3 retro). Story 4.4 requires a clean taxonomy. Story 4.1 does NOT touch the auth state model.
- `ReducerCallResult` and `ReducerCallError` stubs in `Public/Reducers/` — populated in Story 4.2.
- Editor panel verification (Retro D4) — belongs to Epic 5.

### Project Structure Notes

- `Internal/Reducers/` must be created as a new folder; no existing folder to place `ReducerInvoker.cs` in
- `ReducerInvoker` namespace: `GodotSpacetime.Runtime.Reducers` — mirrors `GodotSpacetime.Runtime.Subscriptions` for the subscription registry
- `SpacetimeSdkReducerAdapter` namespace: `GodotSpacetime.Runtime.Platform.DotNet` — already present in the stub file, keep it
- `SpacetimeClient.InvokeReducer` placement: after `GetRows()`, before `_Process()`
- **Namespace note:** The existing stubs `ReducerCallResult.cs` and `ReducerCallError.cs` in `Public/Reducers/` use namespace `GodotSpacetime.Reducers` (public, no `Runtime` segment). The new `ReducerInvoker.cs` is in `Internal/Reducers/` and uses `GodotSpacetime.Runtime.Reducers` — this is correct and intentional (mirrors `GodotSpacetime.Runtime.Subscriptions` vs `GodotSpacetime.Subscriptions` pattern)

### References

- FR23: "Developers can invoke SpacetimeDB reducers through the SDK." [Source: `_bmad-output/planning-artifacts/epics.md#Epic 4`]
- FR26: "Developers can use the SDK for real gameplay interactions without custom protocol work." [Source: `_bmad-output/planning-artifacts/epics.md#Epic 4`]
- Generated binding invocation path: `conn.InternalCallReducer(new Reducer.Ping())` [Source: `demo/generated/smoke_test/Reducers/Ping.g.cs:20`]
- `RemoteReducers` is a public **field** (`public readonly RemoteReducers Reducers`) not a property [Source: `demo/generated/smoke_test/SpacetimeDBClient.g.cs:586`]
- Isolation zone: `Internal/Platform/DotNet/ is the ONLY area that talks directly to SpacetimeDB.ClientSDK` [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural Boundaries`]
- Reducer adapter planned structure: `Internal/Reducers/ReducerInvoker.cs`, `Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs`, `Public/Reducers/ReducerCallResult.cs`, `Public/Reducers/ReducerCallError.cs` [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping`]
- Service `Subscribe` pattern to mirror: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs:114`
- Signal dispatch pattern: `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (HandleSubscriptionApplied/HandleSubscriptionFailed)
- Epic 3 Retro action P1 (disconnect path checklist): `_bmad-output/implementation-artifacts/epic-3-retro-2026-04-14.md#Action Items`
- Epic 3 Retro action P2 (dynamic lifecycle test): `_bmad-output/implementation-artifacts/epic-3-retro-2026-04-14.md#Action Items`
- Epic 3 Retro action P3 (bindings inspection): `_bmad-output/implementation-artifacts/epic-3-retro-2026-04-14.md#Action Items` — satisfied by this story
- Test baseline: 1148 tests (end of Epic 3 / Story 3.5)
- Tech stack: Godot `4.6.2`, `.NET 8+`, `SpacetimeDB.ClientSDK 2.1.0`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented `SpacetimeSdkReducerAdapter` replacing the pragma-suppressed stub: added `SetConnection`, `Invoke` (with `IReducerArgs` validation at the isolation boundary, concrete-type dispatch through the SDK reducer call, null-connection guard via `Console.Error.WriteLine`), and `ClearConnection`. `using SpacetimeDB;` is the only file in the codebase that references SpacetimeDB reducer types directly.
- Created `Internal/Reducers/ReducerInvoker.cs` with namespace `GodotSpacetime.Runtime.Reducers` — no SpacetimeDB imports; validates non-null and delegates to adapter.
- Wired `ReducerInvoker` into `SpacetimeConnectionService`: added `_reducerAdapter` and `_reducerInvoker` fields (constructor injection); `SetConnection` called in `OnConnected`; `ClearConnection` placed in `ResetDisconnectedSessionState()` covering all disconnect paths (explicit, connection-lost, and degraded recovery).
- Added `public void InvokeReducer(object reducerArgs)` to `SpacetimeConnectionService` with state guard (`InvalidOperationException` when not `Connected`) and to `SpacetimeClient` with the `ReplaceSubscription`-pattern try/catch → `PublishValidationFailure`, including invalid reducer-argument validation at the Godot-facing boundary.
- Updated `docs/runtime-boundaries.md` with a "Reducer Invocation" section documenting the call path, isolation zone, and invalid reducer-argument guard. Used runtime-neutral vocabulary (no `DbConnection` or `using SpacetimeDB` references in the doc).
- Wrote and extended `tests/test_story_4_1_invoke_generated_reducers.py` to 61 tests covering adapter structure, ReducerInvoker isolation, service wiring, SpacetimeClient delegation, docs coverage, compile-surface reducer dispatch, dynamic lifecycle teardown (`ClearConnection` in `ResetDisconnectedSessionState`), and regression guards.
- Senior Developer Review (AI) auto-fixed the reducer dispatch build break, aligned invalid reducer-argument handling with the Godot-facing validation boundary, and synced the story/test artifacts with the reviewed result.
- Build: 0 errors, 0 warnings; `validate-foundation.py` exits 0; 1210/1210 tests pass.

### File List

- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` (modified — implemented stub)
- `addons/godot_spacetime/src/Internal/Reducers/ReducerInvoker.cs` (new)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (modified — added reducer fields, wiring, InvokeReducer)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (modified — added public InvokeReducer)
- `docs/runtime-boundaries.md` (modified — added Reducer Invocation section)
- `tests/test_story_4_1_invoke_generated_reducers.py` (new)
- `_bmad-output/implementation-artifacts/tests/test-summary.md` (modified — Story 4.1 summary updated to 61 tests / 1210 suite tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — story status synced to done)

## Change Log

- 2026-04-14: Story 4.1 implemented — reducer invocation path wired from `SpacetimeClient.InvokeReducer` through `ReducerInvoker` → `SpacetimeSdkReducerAdapter` → runtime SDK call. Isolation zone maintained: only `SpacetimeSdkReducerAdapter` references SpacetimeDB types. All disconnect paths covered via `ResetDisconnectedSessionState()`. 47 new tests added; full suite 1196/1196 green.
- 2026-04-14: Senior Developer Review (AI) — 1 Critical, 3 Medium fixed. Fixes: reducer dispatch now uses the concrete generated type so the SDK build succeeds, invalid reducer argument failures now stay on the Godot-facing validation path, reducer docs/tests now lock the reviewed boundary behavior, and verification artifacts were synced to 61 story tests / 1210 suite tests. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 1 additional non-source automation artifact was present under `_bmad-output/story-automator/` beyond the implementation File List.

### Findings Fixed

- CRITICAL: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` called `IDbConnection.InternalCallReducer()` through an `IReducerArgs` interface value, but the SpacetimeDB SDK surface is generic (`InternalCallReducer<T>(T)` with a concrete-type constraint), so Story 4.1 was marked review-ready while the solution did not compile.
- MEDIUM: `addons/godot_spacetime/src/Public/SpacetimeClient.cs` only translated `ArgumentNullException` and `InvalidOperationException` into `PublishValidationFailure`, so an invalid non-`IReducerArgs` reducer object escaped the Godot-facing validation boundary as a raw `ArgumentException`.
- MEDIUM: `docs/runtime-boundaries.md` documented the connected-state guard for `InvokeReducer()` but omitted the invalid reducer-argument validation path, leaving the public runtime guidance behind the reviewed implementation.
- MEDIUM: Story 4.1 verification artifacts still reported 47 story tests and 1196 suite tests and did not record the review-side regression additions, leaving stale evidence in the implementation record.

### Actions Taken

- Updated `SpacetimeSdkReducerAdapter.Invoke()` to validate `IReducerArgs` and dispatch `InternalCallReducer()` through the concrete generated reducer type so the SDK generic constraint is satisfied.
- Extended `SpacetimeClient.InvokeReducer()` so invalid reducer argument failures are surfaced through `PublishValidationFailure`, matching the Godot-facing validation pattern used elsewhere in the SDK.
- Added three Story 4.1 regression tests covering concrete-type reducer dispatch, public `ArgumentException` handling, and the documented invalid-argument guard.
- Re-ran foundation validation, debug build verification, the Story 4.1 test file, and the full pytest suite after the fixes.
- Synced the story completion notes, file list, change log, test summary, story status, and sprint-status entry with the reviewed 61-test / 1210-suite result.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `python3 -m pytest tests/test_story_4_1_invoke_generated_reducers.py -q`
- `python3 -m pytest -q`

### Reference Check

- No dedicated Story Context or Epic 4 tech-spec artifact was present; `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/epics.md`, and `docs/runtime-boundaries.md` were used as the applicable planning and standards references.
- Tech stack validated during review: Godot `.NET` support baseline `4.6.1`, Godot product `4.6.2`, `.NET` `8.0+`, `SpacetimeDB.ClientSDK` `2.1.0`.
- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `_bmad-output/planning-artifacts/epics.md`
- Local reference: `docs/runtime-boundaries.md`
- Local reference: `demo/generated/smoke_test/Reducers/Ping.g.cs`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
