# Story 4.2: Surface Reducer Results and Runtime Status to Gameplay Code

Status: done

## Story

As a Godot developer,
I want reducer-related results, events, and status surfaced through the SDK,
So that gameplay systems can react to the outcome of mutation attempts.

## Acceptance Criteria

1. **Given** a reducer invocation has been made **When** the runtime receives success, failure, or related reducer lifecycle information **Then** the SDK exposes that outcome through a structured result, event, or status surface
2. **Given** a reducer result is received **When** gameplay code handles the result **Then** it can distinguish the reducer operation and invocation instance the outcome belongs to
3. **Given** a reducer invocation fails **When** the SDK surfaces the failure **Then** failure information includes the failure category and a user-safe recovery or feedback path

## Tasks / Subtasks

- [x] Task 1: Populate `ReducerCallResult` and `ReducerCallError` public types (AC: 1, 2, 3)
  - [x] 1.1 Replace `public record ReducerCallResult;` stub in `Public/Reducers/ReducerCallResult.cs` with a `public partial class ReducerCallResult : RefCounted` (matches `SubscriptionAppliedEvent` Godot-compatible pattern)
  - [x] 1.2 Add `public string ReducerName { get; }` — identifies which reducer produced this result (satisfies AC 2: "distinguish the reducer operation")
  - [x] 1.3 Add `public DateTimeOffset CalledAt { get; }` — set to `DateTimeOffset.UtcNow` in constructor
  - [x] 1.4 Add `internal ReducerCallResult(string reducerName)` constructor — sets `ReducerName` and `CalledAt`
  - [x] 1.5 Add XML summary doc: raised when the server acknowledges a reducer invocation as committed; `ReducerName` identifies which reducer completed
  - [x] 1.6 Replace `public class ReducerCallError {}` stub in `Public/Reducers/ReducerCallError.cs` with a `public partial class ReducerCallError : RefCounted`
  - [x] 1.7 Add `public string ReducerName { get; }` — identifies which reducer failed
  - [x] 1.8 Add `public string ErrorMessage { get; }` — human-readable failure description from the server
  - [x] 1.9 Add `public ReducerFailureCategory FailureCategory { get; }` — failure category for branching logic
  - [x] 1.10 Add `public DateTimeOffset FailedAt { get; }` — set to `DateTimeOffset.UtcNow` in constructor
  - [x] 1.11 Add `internal ReducerCallError(string reducerName, string errorMessage, ReducerFailureCategory failureCategory)` constructor
  - [x] 1.12 Add XML summary doc: raised when a reducer invocation is rejected or fails on the server; `FailureCategory` guides whether gameplay code should retry or inform the user

- [x] Task 2: Create `ReducerFailureCategory.cs` (AC: 3)
  - [x] 2.1 Create `addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs`
  - [x] 2.2 Namespace: `GodotSpacetime.Reducers`
  - [x] 2.3 `public enum ReducerFailureCategory` with cases: `Failed` (server logic error or constraint), `OutOfEnergy` (server ran out of energy), `Unknown` (status could not be determined)
  - [x] 2.4 Add XML summary doc on each case explaining when to use each (retry context, energy wait, etc.)

- [x] Task 3: Extend `SpacetimeSdkReducerAdapter` with `IReducerEventSink` and callback registration (AC: 1, 2, 3)
  - [x] 3.1 Add `IReducerEventSink` interface to `SpacetimeSdkReducerAdapter.cs` (same file — mirrors how `IRowChangeEventSink` lives in `SpacetimeSdkRowCallbackAdapter.cs`)
    - `void OnReducerCallSucceeded(string reducerName)` 
    - `void OnReducerCallFailed(string reducerName, string errorMessage, ReducerFailureCategory failureCategory)`
  - [x] 3.2 Add `using System.Linq.Expressions; using System.Reflection;` imports and `using GodotSpacetime.Reducers;` (the namespace of `ReducerFailureCategory`)
  - [x] 3.3 Add `ConditionalWeakTable<object, RegistrationMarker>` field `_registeredReducers` with nested `private sealed class RegistrationMarker;` — prevents double-registration on Degraded→Connected recovery (mirrors `SpacetimeSdkRowCallbackAdapter._registeredDbs`)
  - [x] 3.4 Add `internal void RegisterCallbacks(IReducerEventSink sink)` method:
    - Guard: return early if `_dbConnection == null`
    - Get the `Reducers` object from `_dbConnection` via reflection: **USE `GetField("Reducers", ...)` not `GetProperty` — SpacetimeDB 2.1.0 exposes `Reducers` as a public field, not a property** (same discovery as Story 3.3 field-vs-property lesson; confirmed in `demo/generated/smoke_test/SpacetimeDBClient.g.cs:586`: `public readonly RemoteReducers Reducers;`)
    - Guard: return if `reducers == null`
    - Idempotency guard: `if (!_registeredReducers.TryGetValue(reducers, out _)) _registeredReducers.Add(reducers, new RegistrationMarker()); else return;`
    - Iterate: `foreach (var evt in reducers.GetType().GetEvents(BindingFlags.Public | BindingFlags.Instance))`
    - For each event, call `TryWireReducerEvent(reducers, evt, sink)`
  - [x] 3.5 Add `private static void TryWireReducerEvent(object reducers, EventInfo evt, IReducerEventSink sink)`:
    - Get `invoke = evt.EventHandlerType?.GetMethod("Invoke")`; return if null
    - Get `parameters = invoke.GetParameters()`
    - **Filter: only wire events with exactly 1 parameter** — this naturally excludes `InternalOnUnhandledReducerError` (2 params: `ReducerEventContext, Exception`) and any future non-reducer events
    - Build expression tree lambda: `var ctxParam = Expression.Parameter(parameters[0].ParameterType, "ctx")`
    - Wire lambda body: call `SpacetimeSdkReducerAdapter.ExtractAndDispatch` (static helper) with `Expression.Constant(sink)` and `Expression.Convert(ctxParam, typeof(object))`
    - Compile and add: `evt.AddEventHandler(reducers, Expression.Lambda(evt.EventHandlerType!, body, ctxParam).Compile())`
  - [x] 3.6 Add `private static void ExtractAndDispatch(IReducerEventSink sink, object ctx)` static helper:
    - Extract `ReducerEvent`: `var reducerEvent = ctx.GetType().GetField("Event")?.GetValue(ctx);` — `Event` is a PUBLIC READONLY FIELD on the generated `ReducerEventContext` (confirmed from `demo/generated/smoke_test/SpacetimeDBClient.g.cs:121`: `public readonly ReducerEvent<Reducer> Event;`)
    - Guard: if `reducerEvent == null`, call `sink.OnReducerCallFailed("unknown", "Reducer event context unavailable", ReducerFailureCategory.Unknown); return;`
    - Extract reducer name: get `Reducer` property via reflection: `var reducerArgsObj = reducerEvent.GetType().GetProperty("Reducer")?.GetValue(reducerEvent);` — `ReducerEvent<R>.Reducer` is a property (confirmed from SDK inspection: `R Reducer` property on `ReducerEvent<R>`)
    - Extract name: `var reducerName = (reducerArgsObj as IReducerArgs)?.ReducerName ?? "unknown";` — `IReducerArgs` is already imported via `using SpacetimeDB;`
    - Extract status: `var status = reducerEvent.GetType().GetProperty("Status")?.GetValue(reducerEvent) as SpacetimeDB.Status;` — can cast directly since `SpacetimeDB.Status` is available via `using SpacetimeDB;`
    - Guard: if `status == null`, call `sink.OnReducerCallFailed(reducerName, "Status unavailable", ReducerFailureCategory.Unknown); return;`
    - Pattern-match on status: `switch (status) { case Status.Committed: ... case Status.Failed failed: ... case Status.OutOfEnergy: ... default: ... }`

  **Status discriminated union structure — verified from SDK reflection (SpacetimeDB.ClientSDK 2.1.0):**
  ```
  SpacetimeDB.Status  (abstract base in SpacetimeDB namespace)
    .Committed  — property Committed_ (Unit type, ignore)
    .Failed     — property Failed_ (string: failure reason)
    .OutOfEnergy — property OutOfEnergy_ (Unit type, ignore)
  ```

  Pattern-match dispatch:
  ```csharp
  switch (status)
  {
      case Status.Committed:
          sink.OnReducerCallSucceeded(reducerName);
          break;
      case Status.Failed failed:
          sink.OnReducerCallFailed(reducerName, failed.Failed_ ?? "Reducer failed", ReducerFailureCategory.Failed);
          break;
      case Status.OutOfEnergy:
          sink.OnReducerCallFailed(reducerName, "Out of energy — reducer not executed", ReducerFailureCategory.OutOfEnergy);
          break;
      default:
          sink.OnReducerCallFailed(reducerName, $"Unexpected reducer status: {status.GetType().Name}", ReducerFailureCategory.Unknown);
          break;
  }
  ```

- [x] Task 4: Implement `IReducerEventSink` in `SpacetimeConnectionService` and add public events (AC: 1, 2, 3)
  - [x] 4.1 Add `IReducerEventSink` to `SpacetimeConnectionService`'s implemented interfaces: `internal sealed class SpacetimeConnectionService : IConnectionEventSink, ISubscriptionEventSink, IRowChangeEventSink, IReducerEventSink`
  - [x] 4.2 Add `using GodotSpacetime.Reducers;` import
  - [x] 4.3 Add `public event Action<ReducerCallResult>? OnReducerCallSucceeded;` — mirrors `OnSubscriptionApplied` pattern
  - [x] 4.4 Add `public event Action<ReducerCallError>? OnReducerCallFailed;` — mirrors `OnSubscriptionFailed` pattern
  - [x] 4.5 In `IConnectionEventSink.OnConnected`, add `_reducerAdapter.RegisterCallbacks(this);` immediately after the existing `_reducerAdapter.SetConnection(_adapter.Connection);` line — connection is live at this point, correct injection window
  - [x] 4.6 Add explicit interface implementation for `IReducerEventSink`:
    ```csharp
    void IReducerEventSink.OnReducerCallSucceeded(string reducerName)
    {
        OnReducerCallSucceeded?.Invoke(new ReducerCallResult(reducerName));
    }
    
    void IReducerEventSink.OnReducerCallFailed(string reducerName, string errorMessage, ReducerFailureCategory failureCategory)
    {
        OnReducerCallFailed?.Invoke(new ReducerCallError(reducerName, errorMessage, failureCategory));
    }
    ```
  - [x] 4.7 **Disconnect path checklist (required per Epic 3 Retro action P1):**
    - Explicit disconnect via `SpacetimeClient.Disconnect()`: routes to `SpacetimeConnectionService.Disconnect()` → `ResetDisconnectedSessionState()` → `_reducerAdapter.ClearConnection()` (already in 4.1 path) — when connection is released, the `Reducers` object is collected by GC; no in-flight callbacks expected after disconnect ✓
    - Connection lost mid-session (`OnDisconnected` callback fires): routes to `HandleDisconnectError` → `ResetDisconnectedSessionState()` → `_reducerAdapter.ClearConnection()` ✓
    - Failed connect (never reached `Connected` state): `RegisterCallbacks` only called in `OnConnected` path — never reached ✓
    - Rapid reconnect (Disconnect + Connect): `_registeredReducers` ConditionalWeakTable entry for old `Reducers` object is GC-collected; new `Reducers` object from new connection is registered fresh in next `RegisterCallbacks` call ✓
    - Degraded recovery (`Connected → Degraded → Connected`): `ClearConnection()` is NOT called during Degraded state (only `ClearCacheView`); same `_dbConnection` instance may be reused; `_registeredReducers` idempotency guard prevents double-registration for same `Reducers` instance ✓
    - `OnReducerCallSucceeded` / `OnReducerCallFailed` events: these are plain C# events with no external state; cleared by GC when connection service is collected ✓

- [x] Task 5: Add signals and handlers to `SpacetimeClient` (AC: 1, 2, 3)
  - [x] 5.1 Add `using GodotSpacetime.Reducers;` import
  - [x] 5.2 Add signal declarations (place after `RowChangedEventHandler`):
    ```csharp
    [Signal]
    public delegate void ReducerCallSucceededEventHandler(ReducerCallResult result);
    
    [Signal]
    public delegate void ReducerCallFailedEventHandler(ReducerCallError error);
    ```
  - [x] 5.3 In `_EnterTree()`, wire new events (after `OnRowChanged` wiring):
    ```csharp
    _connectionService.OnReducerCallSucceeded += HandleReducerCallSucceeded;
    _connectionService.OnReducerCallFailed += HandleReducerCallFailed;
    ```
  - [x] 5.4 In `_ExitTree()`, unwire new events (after `OnRowChanged` unwiring):
    ```csharp
    _connectionService.OnReducerCallSucceeded -= HandleReducerCallSucceeded;
    _connectionService.OnReducerCallFailed -= HandleReducerCallFailed;
    ```
  - [x] 5.5 Add private handler methods (mirror `HandleRowChanged` pattern with `GodotSignalAdapter.Dispatch`):
    ```csharp
    private void HandleReducerCallSucceeded(ReducerCallResult result)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.ReducerCallSucceeded, result);
            return;
        }
        _signalAdapter.Dispatch(() => EmitSignal(SignalName.ReducerCallSucceeded, result));
    }
    
    private void HandleReducerCallFailed(ReducerCallError error)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.ReducerCallFailed, error);
            return;
        }
        _signalAdapter.Dispatch(() => EmitSignal(SignalName.ReducerCallFailed, error));
    }
    ```
  - [x] 5.6 Add XML summary doc for the two signal delegates explaining the event model (async, server-side confirmation, GodotSignalAdapter deferred dispatch for thread safety)

- [x] Task 6: Update `docs/runtime-boundaries.md` (AC: 1, 2, 3)
  - [x] 6.1 Update the existing "Reducers — `ReducerCallResult` and `ReducerCallError`" section to document the now-populated types: add `ReducerName`, `CalledAt`, `FailureCategory`, `ErrorMessage`, `FailedAt`, and `ReducerFailureCategory` enum
  - [x] 6.2 Add a "Reducer Results" section documenting the complete outbound result path:
    ```
    SpacetimeSdkReducerAdapter.RegisterCallbacks → per-reducer event hooks
      └─ ExtractAndDispatch(IReducerEventSink sink, object ctx)
           └─ status: Status.Committed → IReducerEventSink.OnReducerCallSucceeded
           └─ status: Status.Failed → IReducerEventSink.OnReducerCallFailed (ReducerFailureCategory.Failed)
           └─ status: Status.OutOfEnergy → IReducerEventSink.OnReducerCallFailed (ReducerFailureCategory.OutOfEnergy)
    SpacetimeConnectionService.IReducerEventSink → ReducerCallResult / ReducerCallError payloads
    SpacetimeClient.ReducerCallSucceeded / ReducerCallFailed signals → gameplay code
    ```
  - [x] 6.3 Note isolation zone: `SpacetimeDB.Status` pattern matching happens ONLY in `SpacetimeSdkReducerAdapter.ExtractAndDispatch` — no SpacetimeDB types cross the boundary
  - [x] 6.4 Note that reducer results arrive asynchronously (after `FrameTick` delivers queued events from the server); gameplay code should NOT expect synchronous correlation between `InvokeReducer()` call and signal arrival
  - [x] 6.5 Add `ReducerFailureCategory` branching guidance: `Failed` → check server logs or module logic; `OutOfEnergy` → back off and retry or inform the player; `Unknown` → defensive handling

- [x] Task 7: Write test file (AC: 1, 2, 3)
  - [x] 7.1 Create `tests/test_story_4_2_surface_reducer_results.py` — follow `test_story_4_1_invoke_generated_reducers.py` structure
  - [x] 7.2 Tests for `ReducerCallResult.cs`:
    - File exists at `Public/Reducers/ReducerCallResult.cs`
    - Is `partial class` (not `record`) — Godot signal compatibility requires `GodotObject`-derived type
    - Extends `RefCounted` — class declaration line contains `: RefCounted`
    - `ReducerName` property present
    - `CalledAt` property present
    - Internal constructor with `string reducerName` parameter
    - Namespace `GodotSpacetime.Reducers`
  - [x] 7.3 Tests for `ReducerCallError.cs`:
    - File exists at `Public/Reducers/ReducerCallError.cs`
    - Is `partial class : RefCounted`
    - `ReducerName` property present
    - `ErrorMessage` property present
    - `FailureCategory` property present
    - `FailedAt` property present
    - Internal constructor present
    - Namespace `GodotSpacetime.Reducers`
  - [x] 7.4 Tests for `ReducerFailureCategory.cs`:
    - File exists at `Public/Reducers/ReducerFailureCategory.cs`
    - `enum ReducerFailureCategory` declared
    - `Failed` case present
    - `OutOfEnergy` case present
    - `Unknown` case present
    - Namespace `GodotSpacetime.Reducers`
  - [x] 7.5 Tests for `SpacetimeSdkReducerAdapter.cs`:
    - `IReducerEventSink` interface declared in the file
    - `OnReducerCallSucceeded` method signature in interface
    - `OnReducerCallFailed` method signature in interface
    - `RegisterCallbacks` method present
    - `ExtractAndDispatch` method present (static helper)
    - `ConditionalWeakTable` or `_registeredReducers` field present (idempotency guard)
    - `GetField("Reducers"` present — verifies correct field access for SpacetimeDB 2.1.0 (not `GetProperty`)
    - `"Event"` string present — verifies field access for `ReducerEventContext.Event`
    - `Status.Committed` or `Status.Failed` or `Status.OutOfEnergy` pattern match present — verifies direct status handling inside isolation zone
    - `using System.Linq.Expressions;` import present
    - `using System.Reflection;` import present
    - Does NOT contain `SpacetimeDB.` import that appears OUTSIDE the existing isolation zone file scope (all SpacetimeDB.Status usage is within this file — isolation maintained)
  - [x] 7.6 Tests for `SpacetimeConnectionService.cs`:
    - `IReducerEventSink` in the interface list on the class declaration
    - `OnReducerCallSucceeded` event present
    - `OnReducerCallFailed` event present
    - `RegisterCallbacks(this)` call present in the file (wired in `OnConnected`)
    - `IReducerEventSink.OnReducerCallSucceeded` explicit implementation present
    - `IReducerEventSink.OnReducerCallFailed` explicit implementation present
    - `new ReducerCallResult(` present — verifies result payload construction
    - `new ReducerCallError(` present — verifies error payload construction
  - [x] 7.7 Tests for `SpacetimeClient.cs`:
    - `ReducerCallSucceededEventHandler` signal delegate declared
    - `ReducerCallFailedEventHandler` signal delegate declared
    - `HandleReducerCallSucceeded` method present
    - `HandleReducerCallFailed` method present
    - `OnReducerCallSucceeded +=` wiring in `_EnterTree`
    - `OnReducerCallFailed +=` wiring in `_EnterTree`
    - `OnReducerCallSucceeded -=` unwiring in `_ExitTree`
    - `OnReducerCallFailed -=` unwiring in `_ExitTree`
    - `EmitSignal(SignalName.ReducerCallSucceeded` dispatch present
    - `EmitSignal(SignalName.ReducerCallFailed` dispatch present
    - `_signalAdapter.Dispatch` used in both handlers (thread-safe deferred dispatch)
  - [x] 7.8 Tests for `docs/runtime-boundaries.md`:
    - `ReducerCallResult` mentioned (already exists — verify still present)
    - `ReducerCallError` mentioned (already exists — verify still present)
    - `ReducerFailureCategory` mentioned
    - `ReducerCallSucceeded` mentioned
    - `ReducerCallFailed` mentioned
    - `RegisterCallbacks` mentioned
    - `IReducerEventSink` mentioned
    - Async result delivery documented (key concept for gameplay code)
  - [x] 7.9 **Dynamic lifecycle test (required per Epic 3 Retro action P2):** Verify that `RegisterCallbacks(this)` appears inside `OnConnected` in `SpacetimeConnectionService.cs` — check that this call exists within the method body scope, not just anywhere in the file (use context-aware check: look for both `OnConnected` and `RegisterCallbacks` in the same block)
  - [x] 7.10 Regression guards: all Story 4.1 deliverables intact — `InvokeReducer` in `SpacetimeConnectionService`, `InvokeReducer` in `SpacetimeClient`, `ReducerInvoker` class, `SpacetimeSdkReducerAdapter.Invoke`, `SetConnection`, `ClearConnection`; all Story 3.x signals (`SubscriptionApplied`, `SubscriptionFailed`, `RowChanged`, `GetRows`, `Subscribe`, `ReplaceSubscription`)

## Dev Notes

### Critical: SDK Inspection Results for Story 4.2 (Satisfies Epic 3 Retro P3)

Inspection performed on `SpacetimeDB.ClientSDK 2.1.0` via Assembly reflection.

**`ReducerEvent<R>` (SpacetimeDB.ReducerEvent`1):**
- `Timestamp Timestamp` — server-side timestamp  
- `Status Status` — the result status (success/failure)
- `Identity CallerIdentity` — identity that invoked the reducer
- `Nullable<ConnectionId> CallerConnectionId`
- `Nullable<Energy> EnergyConsumed`
- `R Reducer` — **PROPERTY** (not field) holding the reducer args

**`SpacetimeDB.Status` discriminated union:**
- Nested cases: `Committed`, `Failed`, `OutOfEnergy`, `BSATN`
- `Status.Committed` — property `Committed_` (Unit; no payload needed)
- `Status.Failed` — property `Failed_` (string: failure reason from server)
- `Status.OutOfEnergy` — property `OutOfEnergy_` (Unit; no payload needed)

**Key findings:**
- `Status` is in the `SpacetimeDB` namespace — can be used directly via C# `switch` in `SpacetimeSdkReducerAdapter` which already has `using SpacetimeDB;`
- `ReducerEvent<R>.Reducer` is a **property** (unlike table handles which are FIELDS in SpacetimeDB 2.1.0)
- `ReducerEventContext.Event` is a **public readonly FIELD** (from generated `SpacetimeDBClient.g.cs:121`: `public readonly ReducerEvent<Reducer> Event;`)

### What Already Exists (Do Not Reinvent)

- `SpacetimeSdkReducerAdapter.cs` at `Internal/Platform/DotNet/` — has `SetConnection`, `Invoke`, `ClearConnection` from Story 4.1; extend with `IReducerEventSink`, `RegisterCallbacks`, `ExtractAndDispatch`
- `SpacetimeSdkRowCallbackAdapter.cs` — THE REFERENCE IMPLEMENTATION for the reflection-based event registration pattern; Story 4.2 reducer callback wiring follows the same approach
- `GodotSignalAdapter.Dispatch(Action)` — already exists; use it for thread-safe deferred signal dispatch in `HandleReducerCallSucceeded` / `HandleReducerCallFailed`
- `ISubscriptionEventSink` explicit interface implementation pattern in `SpacetimeConnectionService` — mirror this for `IReducerEventSink`
- `SubscriptionAppliedEvent` / `SubscriptionFailedEvent` — reference models for `ReducerCallResult` / `ReducerCallError` shape

### Per-Reducer Event Wiring — Why 1-Parameter Filter Works

`RemoteReducers` in SpacetimeDB 2.1.0 exposes:
```csharp
// Per-reducer events (want these):
public event PingHandler? OnPing;           // delegate void PingHandler(ReducerEventContext ctx) — 1 param

// Error aggregate (do NOT register for this):
internal event Action<ReducerEventContext, Exception>? InternalOnUnhandledReducerError;  // 2 params
// Note: InternalOnUnhandledReducerError is INTERNAL so GetEvents(Public | Instance) already excludes it
// But the 1-param filter provides defense-in-depth regardless
```

Since `InternalOnUnhandledReducerError` is `internal`, `GetEvents(BindingFlags.Public | BindingFlags.Instance)` already excludes it. The 1-parameter filter is a defense-in-depth guard for any future SDK version changes.

### Important: `ReducerCallResult` Must Be `partial class : RefCounted`, Not `record`

The current stubs use `record` and `class`. Godot signals require `Variant`-compatible payload types. `RefCounted : GodotObject` satisfies this — the same pattern used by `SubscriptionAppliedEvent`, `SubscriptionFailedEvent`, and `RowChangedEvent`.

The internal constructors prevent external construction — only the SDK creates result/error payloads.

### Degraded Recovery — Idempotency Guard Is Critical

On `Connected → Degraded → Connected` recovery, `IConnectionEventSink.OnConnected` fires again. If the same `IDbConnection` instance is reused, `SetConnection` is called again with the same connection, and `RegisterCallbacks(this)` would be called again.

The `ConditionalWeakTable<object, RegistrationMarker> _registeredReducers` guard using the `Reducers` object identity prevents double-registration. Without this guard, every per-reducer event would fire twice per outcome after the first reconnect.

### Architecture Constraints

- `SpacetimeDB.Status` pattern matching is ONLY in `SpacetimeSdkReducerAdapter.ExtractAndDispatch` — never in `ReducerInvoker`, `SpacetimeConnectionService`, or `SpacetimeClient`
- `IReducerEventSink` is the boundary — `SpacetimeConnectionService` receives reducer name, invocation correlation (`InvocationId`, `CalledAt`), failure category, and recovery guidance as runtime-neutral types, not SpacetimeDB types
- `ReducerCallResult` / `ReducerCallError` constructors are `internal` — only the service creates them
- `ReducerFailureCategory` is a plain C# enum in the public `GodotSpacetime.Reducers` namespace — no SpacetimeDB dependency

### Async Result Model for Gameplay Code

Reducer results arrive ASYNCHRONOUSLY. The `FrameTick()` in `_Process` advances the SpacetimeDB connection which delivers queued server messages. A `ReducerCallSucceeded` or `ReducerCallFailed` signal will fire in a LATER FRAME than `InvokeReducer()` was called. Gameplay code must NOT assume synchronous correlation.

The `GodotSignalAdapter.Dispatch` (CallDeferred) ensures signals fire on the main thread's next frame — safe for gameplay code that reads from the scene tree.

### Disconnect Path Coverage (Required — Epic 3 Retro Action P1)

`SpacetimeSdkReducerAdapter` gains new state: `_registeredReducers` (ConditionalWeakTable).

| Exit Path | Handling |
|-----------|----------|
| Explicit disconnect (`SpacetimeClient.Disconnect()`) | `ResetDisconnectedSessionState()` → `_reducerAdapter.ClearConnection()` (Story 4.1 path intact); registered callbacks are GC-collected when `Reducers` object is collected |
| Connection lost (`OnDisconnected` from SDK) | Same `ResetDisconnectedSessionState()` path ✓ |
| Failed connect (never reached `Connected`) | `RegisterCallbacks` only called in `OnConnected` — never reached ✓ |
| Rapid reconnect | Old `Reducers` object GC-collected; new connection creates new `Reducers` instance; registered fresh ✓ |
| Degraded recovery | Same `_dbConnection` / `Reducers` instance; `_registeredReducers` idempotency guard prevents double-registration ✓ |

`SpacetimeConnectionService` new events (`OnReducerCallSucceeded`, `OnReducerCallFailed`):
- Plain C# events, no external state; collected with the service ✓

### File Structure

New files:
- `addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs`
- `tests/test_story_4_2_surface_reducer_results.py`

Modified files:
- `addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs` (replace stub — must change from `record` to `partial class : RefCounted`)
- `addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs` (replace stub — must change from plain `class` to `partial class : RefCounted`)
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` (add `IReducerEventSink`, `RegisterCallbacks`, `ExtractAndDispatch`, `_registeredReducers`)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (add `IReducerEventSink` interface, `OnReducerCallSucceeded`/`OnReducerCallFailed` events, `RegisterCallbacks(this)` in `OnConnected`)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (add `ReducerCallSucceeded`/`ReducerCallFailed` signals and handlers, wire events)
- `docs/runtime-boundaries.md` (update reducer types section, add reducer results path, add `ReducerFailureCategory` guidance)

### Tech Debt to Be Aware Of (Do NOT fix in this story)

- `ConnectionAuthState.AuthRequired` dead code — 3+ epics overdue (retro D1). Story 4.4 requires a clean taxonomy for FR27. Story 4.2 does NOT touch auth state.
- Row callback GC-only teardown (`SpacetimeSdkRowCallbackAdapter`) — not addressed in 4.2
- Reducer callbacks use the same GC-based teardown pattern (when the connection is closed, the `Reducers` object is collected carrying the callbacks with it) — acceptable for Story 4.2; could be made explicit in a future cleanup story
- `ReconnectPolicy` documentation — still missing from `docs/connection.md`

### References

- FR24: "Developers can receive reducer-related results, events, or status information needed by gameplay code." [Source: `_bmad-output/planning-artifacts/epics.md#Epic 4`]
- Story 4.1 established: `SpacetimeClient.InvokeReducer` → `SpacetimeConnectionService.InvokeReducer` → `ReducerInvoker.Invoke` → `SpacetimeSdkReducerAdapter.Invoke` → SDK call
- `ReducerEvent<R>` structure confirmed: `Status Status`, `R Reducer` (property) [Source: SpacetimeDB.ClientSDK 2.1.0 reflection inspection]
- `Status` discriminated union: `Committed`, `Failed` (`.Failed_` string), `OutOfEnergy` [Source: SpacetimeDB.ClientSDK 2.1.0 reflection inspection]
- `ReducerEventContext.Event` is a public readonly FIELD [Source: `demo/generated/smoke_test/SpacetimeDBClient.g.cs:121`]
- `Reducers` is a public field on `DbConnection` [Source: `demo/generated/smoke_test/SpacetimeDBClient.g.cs:586`]
- Per-reducer event delegate signature: `void PingHandler(ReducerEventContext ctx)` — single parameter [Source: `demo/generated/smoke_test/Reducers/Ping.g.cs:15-16`]
- Expression tree adapter reference: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs`
- Signal dispatch pattern reference: `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (HandleRowChanged)
- `ISubscriptionEventSink` explicit implementation pattern: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`
- Epic 3 Retro P1 (disconnect path checklist): `_bmad-output/implementation-artifacts/epic-3-retro-2026-04-14.md#Action Items`
- Epic 3 Retro P2 (dynamic lifecycle test): `_bmad-output/implementation-artifacts/epic-3-retro-2026-04-14.md#Action Items`
- Epic 3 Retro P3 (bindings inspection): satisfied above
- Test baseline: 1210 tests (end of Story 4.1)
- Tech stack: Godot `4.6.2`, `.NET 8+`, `SpacetimeDB.ClientSDK 2.1.0`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blocking issues encountered. Two stale tests in `test_story_1_3_sdk_concepts.py` validated the old stub declarations (`public record ReducerCallResult` and `public class ReducerCallError`). Updated these tests to validate the new `public partial class : RefCounted` declarations per Story 4.2 requirements.

### Completion Notes List

- **Task 1**: Replaced `public record ReducerCallResult;` stub with `public partial class ReducerCallResult : RefCounted`, adding `ReducerName`, `CalledAt`, internal constructor, and XML docs. Same for `ReducerCallError` with `ReducerName`, `ErrorMessage`, `FailureCategory`, `FailedAt`, internal constructor.
- **Task 2**: Created `ReducerFailureCategory.cs` with `Failed`, `OutOfEnergy`, `Unknown` enum cases and XML docs explaining each case's retry/feedback guidance.
- **Task 3**: Extended `SpacetimeSdkReducerAdapter.cs` with `IReducerEventSink` interface, `_registeredReducers` ConditionalWeakTable guard, `RegisterCallbacks` method using `GetField("Reducers")` (SpacetimeDB 2.1.0 field, not property), `TryWireReducerEvent` with 1-parameter filter (excludes InternalOnUnhandledReducerError), and `ExtractAndDispatch` with `GetField("Event")` access and `Status.Committed/Failed/OutOfEnergy` pattern match.
- **Task 4**: Added `IReducerEventSink` to `SpacetimeConnectionService` class declaration, `using GodotSpacetime.Reducers;`, `OnReducerCallSucceeded`/`OnReducerCallFailed` events, `RegisterCallbacks(this)` wired immediately after `SetConnection` in `OnConnected`, and explicit interface implementations constructing `ReducerCallResult`/`ReducerCallError`.
- **Task 5**: Added `using GodotSpacetime.Reducers;`, `ReducerCallSucceededEventHandler`/`ReducerCallFailedEventHandler` signal delegates with XML docs, wired in `_EnterTree`/`_ExitTree`, and handler methods using `_signalAdapter.Dispatch` for thread-safe deferred dispatch.
- **Task 6**: Updated `docs/runtime-boundaries.md` — expanded Reducers section with `ReducerCallResult`/`ReducerCallError` property tables, `ReducerFailureCategory` branching table, added "Reducer Results" section with full outbound path diagram, isolation zone note, and async delivery note.
- **Task 7**: Created `tests/test_story_4_2_surface_reducer_results.py` with 77 tests covering all deliverables, dynamic lifecycle test for `RegisterCallbacks` inside `OnConnected`, and full regression guards for 4.1 and 3.x stories.
- **Senior Review (AI)**: Auto-fixed the missing invocation-instance correlation and recovery-path surface. `ReducerCallResult` / `ReducerCallError` now carry `InvocationId`; `ReducerCallResult` adds `CompletedAt`; `ReducerCallError` adds `CalledAt` and `RecoveryGuidance`; `SpacetimeSdkReducerAdapter` now tracks pending invocations so async callbacks map back to the original reducer call.
- **All 1342 tests pass** (`tests/test_story_4_2_surface_reducer_results.py`: 127, full suite: 1342).

### File List

New files:
- `addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs`
- `tests/test_story_4_2_surface_reducer_results.py`

Modified files:
- `addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs` (replaced record stub with partial class : RefCounted)
- `addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs` (replaced plain class stub with partial class : RefCounted)
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` (added IReducerEventSink, RegisterCallbacks, ExtractAndDispatch, _registeredReducers)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (added IReducerEventSink, OnReducerCallSucceeded/Failed events, RegisterCallbacks(this) in OnConnected, explicit implementations)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (added ReducerCallSucceeded/Failed signals and handlers, wired events)
- `docs/runtime-boundaries.md` (expanded Reducers section, added Reducer Results section with path diagram and async delivery note)
- `tests/test_story_1_3_sdk_concepts.py` (updated stale stub type tests for ReducerCallResult/ReducerCallError)
- `_bmad-output/implementation-artifacts/tests/test-summary.md` (modified — Story 4.2 review summary updated to 127 story tests / 1342 suite tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — story status synced to done)

### Change Log

- 2026-04-14: Story 4.2 implemented — reducer result surface: ReducerCallResult, ReducerCallError, ReducerFailureCategory types; IReducerEventSink callback path from SpacetimeSdkReducerAdapter through SpacetimeConnectionService to SpacetimeClient signals; docs updated; 77 new tests, 1292 total passing.
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 2 High, 2 Medium fixed. Fixes: reducer outcomes now carry invocation correlation (`InvocationId`, call timestamps) so repeated in-flight reducer calls are distinguishable; failure payloads now include explicit `RecoveryGuidance`; reducer callback dispatch now preserves the original call context through pending-invocation tracking; docs/tests/artifacts were synced to 127 story tests / 1342 suite tests. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List (`_bmad-output/story-automator/orchestration-1-20260414-184146.md`, `_bmad-output/implementation-artifacts/tests/test-summary.md`, and `_bmad-output/implementation-artifacts/sprint-status.yaml`).

### Findings Fixed

- HIGH: AC 2 was not actually satisfied. `ReducerCallResult` / `ReducerCallError` only exposed `ReducerName` plus receipt-time timestamps, so two in-flight calls to the same reducer were indistinguishable once async callbacks arrived.
- HIGH: AC 3 was only partially satisfied. `ReducerCallError` exposed `FailureCategory` and `ErrorMessage`, but it did not carry any explicit user-safe recovery or feedback path in the surfaced payload.
- MEDIUM: The reducer timestamps were receipt-time only, so gameplay code had no stable way to tie an async success/failure back to the original accepted invocation.
- MEDIUM: Story 4.2 verification evidence was stale after review. The story/test summary still reflected the pre-review counts and there were no regression checks locking the correlation/recovery-path behavior that AC 2 and AC 3 require.

### Actions Taken

- Added `InvocationId` to both reducer payload types, `CompletedAt` to `ReducerCallResult`, and `CalledAt` plus `RecoveryGuidance` to `ReducerCallError`.
- Updated `SpacetimeSdkReducerAdapter` to track pending reducer invocations by reducer name, remove abandoned entries on synchronous invoke failure, and preserve invocation correlation through async callback dispatch.
- Converted `ExtractAndDispatch` to an instance method so the callback path can use adapter-owned correlation state while keeping SpacetimeDB-specific reflection and status handling inside the isolation zone.
- Updated `docs/runtime-boundaries.md` so the public contract documents invocation correlation, pending-invocation tracking, and user-safe recovery guidance.
- Expanded `tests/test_story_4_2_surface_reducer_results.py` to 127 tests covering the reviewed contract and revalidated the full suite and debug build.
- Synced the story status, change log, test summary, and sprint-status entry to the reviewed `done` result.

### Validation

- `python3 -m pytest tests/test_story_4_2_surface_reducer_results.py -q`
- `dotnet build godot-spacetime.sln -c Debug`
- `python3 -m pytest -q`

### Reference Check

- No dedicated Story Context or Epic 4 tech-spec artifact was present; `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/epics.md`, and `docs/runtime-boundaries.md` were used as the applicable planning and standards references.
- Tech stack validated during review: Godot `.NET` support baseline `4.6.1`, Godot product `4.6.2`, `.NET` `8.0+`, `SpacetimeDB.ClientSDK` `2.1.0`.
- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `_bmad-output/planning-artifacts/epics.md`
- Local reference: `docs/runtime-boundaries.md`
- Local reference: `demo/generated/smoke_test/SpacetimeDBClient.g.cs`
- Local reference: `demo/generated/smoke_test/Reducers/Ping.g.cs`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
