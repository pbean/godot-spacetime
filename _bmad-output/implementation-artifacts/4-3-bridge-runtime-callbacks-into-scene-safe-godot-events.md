# Story 4.3: Bridge Runtime Callbacks into Scene-Safe Godot Events

Status: done

## Story

As a Godot developer,
I want connection, subscription, and reducer callbacks bridged into scene-safe Godot events,
So that gameplay code can integrate SDK behavior through normal Godot flow instead of low-level transport objects.

## Acceptance Criteria

1. **Given** runtime lifecycle events occur inside the SDK **When** consuming Godot code subscribes to the supported event surface **Then** those events are available through Godot-friendly signals or equivalent scene-safe adapters
2. **Given** a connection session is established and then ends **When** the connection closes (clean or error) **Then** a `ConnectionClosed` signal fires on `SpacetimeClient` with a structured `ConnectionClosedEvent` payload carrying `CloseReason` (Clean or Error), `ErrorMessage`, and `ClosedAt`
3. **And** scene code can respond without taking ownership of transport advancement or reconnect policy
4. **And** the Godot-facing event names remain semantically aligned with the underlying runtime facts

## Tasks / Subtasks

- [x] Task 1: Create `ConnectionCloseReason.cs` and `ConnectionClosedEvent.cs` public types (AC: 1, 2)
  - [x] 1.1 Create `addons/godot_spacetime/src/Public/Connection/ConnectionCloseReason.cs`
    - Namespace: `GodotSpacetime.Connection`
    - `public enum ConnectionCloseReason` with cases: `Clean` (explicit disconnect or clean server-side close), `Error` (network/protocol error after the session was established)
    - XML doc on each case
  - [x] 1.2 Create `addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs`
    - Namespace: `GodotSpacetime.Connection`
    - `public partial class ConnectionClosedEvent : RefCounted` — Godot signal compatible (same pattern as `ConnectionOpenedEvent`)
    - Properties (all public getters/setters, same style as `ConnectionOpenedEvent`):
      - `public ConnectionCloseReason CloseReason { get; set; }`
      - `public string ErrorMessage { get; set; } = string.Empty;` — empty for Clean closes
      - `public DateTimeOffset ClosedAt { get; set; }`
    - XML doc: "raised when a live connection session ends; symmetric with `ConnectionOpenedEvent`; fires after `ConnectionStateChanged` transitions to Disconnected; does NOT fire for failed connect attempts (never reached Connected)"
    - Add `using System;` import for `DateTimeOffset`

- [x] Task 2: Add `OnConnectionClosed` event to `SpacetimeConnectionService` (AC: 1, 2)
  - [x] 2.1 Add `using GodotSpacetime.Connection;` import (check if already present — it is via `ConnectionStatus`/`ConnectionState`; add if missing)
  - [x] 2.2 Add `public event Action<ConnectionClosedEvent>? OnConnectionClosed;` alongside the other public events
  - [x] 2.3 Modify `private void Disconnect(string description)` to fire `ConnectionClosed`:
    - Capture `prevState = CurrentStatus.State` BEFORE calling `ResetDisconnectedSessionState()`
    - After `_stateMachine.Transition(ConnectionState.Disconnected, description)`: if `prevState is ConnectionState.Connected or ConnectionState.Degraded`, invoke `OnConnectionClosed?.Invoke(new ConnectionClosedEvent { CloseReason = ConnectionCloseReason.Clean, ClosedAt = DateTimeOffset.UtcNow })`
    - A teardown guard must suppress reentrant or late `OnDisconnected` callbacks while `_adapter.Close()` runs; the `prevState` check restricts Clean events to sessions that were live
  - [x] 2.4 Modify `private void HandleDisconnectError(Exception error)` to fire `ConnectionClosed`:
    - After `_stateMachine.Transition(ConnectionState.Disconnected, ...)` (the non-Degraded branch): invoke `OnConnectionClosed?.Invoke(new ConnectionClosedEvent { CloseReason = ConnectionCloseReason.Error, ErrorMessage = error.Message, ClosedAt = DateTimeOffset.UtcNow })`
    - Do NOT fire in the Degraded branch — session may recover, connection has not ended
  - [x] 2.5 Disconnect path checklist (Epic 3 Retro P1 pattern — required for all Story 4.x deliverables with new state):
    - Explicit `SpacetimeClient.Disconnect()` → `SpacetimeConnectionService.Disconnect()` → `Disconnect("description")` → `prevState = Connected` → fires `ConnectionClosed(Clean)` ✓
    - Connection lost mid-session (non-recoverable) → `OnDisconnected(error)` → `HandleDisconnectError` → goes to Disconnected → fires `ConnectionClosed(Error)` ✓
    - Degraded recovery → `HandleDisconnectError` returns early on Degraded branch → NO `ConnectionClosed` (session still alive) ✓
    - Failed connect (never reached Connected) → `OnConnectError` when Connecting → `ResetDisconnectedSessionState()` + state transition directly, not via `Disconnect(string)` helper → `prevState = Connecting` → `ConnectionClosed` does NOT fire ✓
    - Rapid reconnect via `Connect()` while Connected → `Connect()` calls `Disconnect("closing previous session")` → `prevState = Connected` → fires `ConnectionClosed(Clean)` for previous session ✓
    - `OnDisconnected(null)` fires from SDK (server-side clean close) → calls `Disconnect(...)` helper → `prevState = Connected` → fires `ConnectionClosed(Clean)` ✓
    - `OnDisconnected(null)` fires while teardown is in progress or after we already set state to Disconnected → teardown guard + Disconnected-state guard prevent double-fire ✓
  - [x] 2.6 Add `using System;` import if `DateTimeOffset.UtcNow` requires it (check existing imports)

- [x] Task 3: Add `ConnectionClosed` signal to `SpacetimeClient` (AC: 1, 2, 3, 4)
  - [x] 3.1 Add `[Signal]` delegate after `ConnectionOpenedEventHandler` (keep lifecycle signals grouped):
    ```csharp
    /// <summary>
    /// Emitted when a live connection session ends.
    /// Fires after <c>ConnectionStateChanged</c> transitions to <c>Disconnected</c>.
    /// <c>ConnectionCloseReason.Clean</c>: explicit <c>Disconnect()</c> or clean server-side close.
    /// <c>ConnectionCloseReason.Error</c>: session lost due to network or protocol error after being established.
    /// Does NOT fire for failed connect attempts — <c>ConnectionStateChanged</c> covers those via Disconnected state.
    /// </summary>
    [Signal]
    public delegate void ConnectionClosedEventHandler(ConnectionClosedEvent e);
    ```
  - [x] 3.2 In `_EnterTree()`, wire after `_connectionService.OnConnectionOpened += HandleConnectionOpened;`:
    `_connectionService.OnConnectionClosed += HandleConnectionClosed;`
  - [x] 3.3 In `_ExitTree()`, unwire after `_connectionService.OnConnectionOpened -= HandleConnectionOpened;`:
    `_connectionService.OnConnectionClosed -= HandleConnectionClosed;`
  - [x] 3.4 Add `HandleConnectionClosed` method following `HandleConnectionOpened` pattern exactly:
    ```csharp
    private void HandleConnectionClosed(ConnectionClosedEvent e)
    {
        if (_signalAdapter == null)
        {
            EmitSignal(SignalName.ConnectionClosed, e);
            return;
        }
        _signalAdapter.Dispatch(() => EmitSignal(SignalName.ConnectionClosed, e));
    }
    ```

- [x] Task 4: Update `docs/runtime-boundaries.md` (AC: 1, 2, 3, 4)
  - [x] 4.1 After the `ConnectionOpenedEvent` paragraph (currently describes `A ConnectionStatus value...`), add `ConnectionClosedEvent` documentation:
    - Brief description: fired when a live session ends; symmetric with `ConnectionOpenedEvent`
    - Property table:

      | Property | Type | Meaning |
      |----------|------|---------|
      | `CloseReason` | `ConnectionCloseReason` | `Clean`: explicit disconnect or server-side clean close. `Error`: session lost after being established. |
      | `ErrorMessage` | `string` | Non-empty when `CloseReason` is `Error`; empty string for Clean closes. |
      | `ClosedAt` | `DateTimeOffset` | UTC timestamp at which the SDK recorded the close event. |

    - Note: does NOT fire for failed connect attempts (never reached Connected); `ConnectionStateChanged` covers those
    - Note: fires after `ConnectionStateChanged` transitions to Disconnected
  - [x] 4.2 Add "Scene-Safe Signal Bridge" section (place after the Reducer Results section, before or at end):
    - Explain that all `SpacetimeClient` signals are dispatched through `GodotSignalAdapter.Dispatch(CallDeferred)` to ensure they fire on the Godot main thread, safe for scene tree access
    - Complete signal catalog (8 signals):

      | Signal | Payload | Category |
      |--------|---------|----------|
      | `ConnectionStateChanged` | `ConnectionStatus` | Connection lifecycle |
      | `ConnectionOpened` | `ConnectionOpenedEvent` | Connection lifecycle |
      | `ConnectionClosed` | `ConnectionClosedEvent` | Connection lifecycle |
      | `SubscriptionApplied` | `SubscriptionAppliedEvent` | Subscription lifecycle |
      | `SubscriptionFailed` | `SubscriptionFailedEvent` | Subscription lifecycle |
      | `RowChanged` | `RowChangedEvent` | Data |
      | `ReducerCallSucceeded` | `ReducerCallResult` | Reducer |
      | `ReducerCallFailed` | `ReducerCallError` | Reducer |

    - Transport advancement: `SpacetimeClient._Process()` calls `FrameTick()` on every frame while not Disconnected. Scene code must NOT call `FrameTick()` directly. Calling `FrameTick()` from multiple owners causes duplicate callback delivery.
    - Reconnect policy: `ReconnectPolicy` is owned internally by `SpacetimeConnectionService`. Scene code must NOT implement its own reconnect loop. Observe `ConnectionStateChanged` and `ConnectionClosed` to react to lifecycle changes.

- [x] Task 5: Write test file `tests/test_story_4_3_bridge_runtime_callbacks.py` (AC: 1, 2, 3, 4)
  - [x] 5.1 Tests for `ConnectionCloseReason.cs`:
    - File exists at `Public/Connection/ConnectionCloseReason.cs`
    - `enum ConnectionCloseReason` declared
    - `Clean` case present
    - `Error` case present
    - Namespace `GodotSpacetime.Connection`
    - Does NOT import `SpacetimeDB` (plain C# enum, no SDK dependency)
  - [x] 5.2 Tests for `ConnectionClosedEvent.cs`:
    - File exists at `Public/Connection/ConnectionClosedEvent.cs`
    - Is `partial class : RefCounted` (Godot signal compatibility)
    - `CloseReason` property present
    - `ErrorMessage` property present with default empty string
    - `ClosedAt` property present
    - Namespace `GodotSpacetime.Connection`
    - `using System;` import present (DateTimeOffset)
    - Does NOT import `SpacetimeDB`
  - [x] 5.3 Tests for `SpacetimeConnectionService.cs`:
    - `OnConnectionClosed` event declared (look for `event Action<ConnectionClosedEvent>`)
    - `ConnectionCloseReason.Clean` invocation present (fires on Disconnect path)
    - `ConnectionCloseReason.Error` invocation present (fires on HandleDisconnectError path)
    - `ConnectionClosed` firing in `Disconnect` is guarded by `prevState` check (look for `Connected or ConnectionState.Degraded` or similar guard)
    - `HandleDisconnectError` fires `ConnectionClosed` on the Disconnected branch (not Degraded)
  - [x] 5.4 Tests for `SpacetimeClient.cs` — bridge completeness and deferred dispatch pattern:
    - `ConnectionClosedEventHandler` signal delegate declared
    - `HandleConnectionClosed` method present
    - `OnConnectionClosed +=` wiring in `_EnterTree`
    - `OnConnectionClosed -=` unwiring in `_ExitTree`
    - `EmitSignal(SignalName.ConnectionClosed` dispatch present
    - `_signalAdapter.Dispatch` used in `HandleConnectionClosed` (thread-safe deferred dispatch)
    - **All 8 signals use deferred dispatch (regression guard):** verify `_signalAdapter.Dispatch` appears in all 8 handler methods by checking all `HandleConnection`, `HandleSubscription`, `HandleRow`, `HandleReducer` methods
    - `_signalAdapter` null-check pattern present in `HandleConnectionClosed` (mirrors `HandleConnectionOpened` exactly)
  - [x] 5.5 Tests for `GodotSignalAdapter.cs` (lock the scene-safe bridge implementation):
    - File exists at `Internal/Events/GodotSignalAdapter.cs`
    - Class is `internal sealed`
    - `Dispatch` method present
    - `CallDeferred()` used inside `Dispatch` (the mechanism making signals scene-safe)
    - `GodotObject.IsInstanceValid(_owner)` guard present (prevent dispatch to destroyed nodes)
    - `Callable.From(action)` pattern used (standard Godot deferred callable)
  - [x] 5.6 Tests for transport/reconnect ownership (`SpacetimeClient.cs`):
    - `_Process` method present (owns transport tick)
    - `FrameTick()` call present inside `_Process` (transport advancement owned by SDK node)
    - Early return guard for `Disconnected` state present in `_Process` (no wasted ticks)
  - [x] 5.7 Tests for `docs/runtime-boundaries.md` additions:
    - `ConnectionClosedEvent` mentioned
    - `ConnectionCloseReason` or `CloseReason` mentioned
    - `ErrorMessage` in close context mentioned
    - `ClosedAt` mentioned
    - `GodotSignalAdapter` mentioned (scene-safe bridge section)
    - `CallDeferred` or `FrameTick` ownership documented
    - Signal catalog complete: all 8 signals (ConnectionStateChanged, ConnectionOpened, ConnectionClosed, SubscriptionApplied, SubscriptionFailed, RowChanged, ReducerCallSucceeded, ReducerCallFailed) appear in docs
  - [x] 5.8 Dynamic lifecycle test (Epic 3 Retro P2 pattern): verify `OnConnectionClosed +=` appears within `_EnterTree` method body and `OnConnectionClosed -=` within `_ExitTree` body in `SpacetimeClient.cs` — not just anywhere in the file
  - [x] 5.9 Regression guards — all Story 4.2 deliverables intact:
    - `ReducerCallSucceededEventHandler` / `ReducerCallFailedEventHandler` signal delegates still present
    - `HandleReducerCallSucceeded` / `HandleReducerCallFailed` methods still present
    - `OnReducerCallSucceeded +=` / `OnReducerCallFailed +=` in `_EnterTree` still present
    - `IReducerEventSink` interface still on `SpacetimeConnectionService` class declaration
    - `ReducerCallResult`, `ReducerCallError`, `ReducerFailureCategory` types still present
    - `GetField("Reducers"` in `SpacetimeSdkReducerAdapter.cs` still present
  - [x] 5.10 Regression guards — all Story 3.x signals intact:
    - `SubscriptionAppliedEventHandler`, `SubscriptionFailedEventHandler`, `RowChangedEventHandler` delegates still present
    - `ConnectionStateChangedEventHandler`, `ConnectionOpenedEventHandler` still present

## Dev Notes

### What This Story Adds (and Why It's the Missing Piece)

The existing SDK surface bridges `OnConnect` → `ConnectionOpened` (with structured payload: Host, Database, Identity, ConnectedAt). The `OnDisconnect` SDK callback currently only routes to `ConnectionStateChanged` with Disconnected state — there is no symmetric structured event for when the session ends.

Story 4.3 adds `ConnectionClosed` + `ConnectionClosedEvent`, completing the connection lifecycle bridge:
- `OnConnect` → `ConnectionOpened` ✓ (stories 1.9, 1.10)
- `OnDisconnect` → `ConnectionClosed` ← **added here**
- `OnSubscriptionApplied` → `SubscriptionApplied` ✓ (story 3.1)
- `OnSubscriptionError` → `SubscriptionFailed` ✓ (story 3.5)
- Per-row events → `RowChanged` ✓ (story 3.3)
- Per-reducer events → `ReducerCallSucceeded`/`ReducerCallFailed` ✓ (story 4.2)

The `GodotSignalAdapter.Dispatch(CallDeferred)` mechanism already exists and is the scene-safe bridge for all signals. Story 4.3 locks this behavior with tests and documents the complete catalog.

Architecture doc naming convention (line 371-373) defines: "Domain event identifiers use lowercase dotted names: `connection.opened`... C# event/signal delegate and payload type names use the PascalCase equivalent: `ConnectionOpenedEvent`." The `connection.closed` event → `ConnectionClosedEvent` follows this convention exactly.

### Reference Implementation

**`ConnectionOpenedEvent` IS the reference** for `ConnectionClosedEvent` shape:
- File: `addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs`
- `public partial class ConnectionOpenedEvent : RefCounted` — Godot signal compatible
- Properties with public getters/setters (no constructor needed)
- `using Godot;` for `RefCounted`, `using System;` for `DateTimeOffset`

**`HandleConnectionOpened` IS the reference** for `HandleConnectionClosed` in `SpacetimeClient`:
```csharp
private void HandleConnectionOpened(ConnectionOpenedEvent openedEvent)
{
    if (_signalAdapter == null)
    {
        EmitSignal(SignalName.ConnectionOpened, openedEvent);
        return;
    }
    _signalAdapter.Dispatch(() => EmitSignal(SignalName.ConnectionOpened, openedEvent));
}
```
The `HandleConnectionClosed` method must be identical in structure, substituting `ConnectionClosed` for `ConnectionOpened`.

### Where ConnectionClosed Fires (Exact Code Injection Points)

**`private void Disconnect(string description)` in `SpacetimeConnectionService.cs`:**

Fires `ConnectionClosed(Clean)` when `prevState` is `Connected` or `Degraded`:

```csharp
private void Disconnect(string description)
{
    var prevState = CurrentStatus.State;
    RunConnectionTeardown(() =>
    {
        ResetDisconnectedSessionState();
        if (CurrentStatus.State != ConnectionState.Disconnected)
            _stateMachine.Transition(ConnectionState.Disconnected, description);
    });
    // Fire ConnectionClosed only for live sessions (Connected or Degraded)
    // Prevents firing for: Connecting→Disconnected (failed connect)
    // Reentrant teardown callbacks are blocked by RunConnectionTeardown + the OnDisconnected guard
    if (prevState is ConnectionState.Connected or ConnectionState.Degraded)
        OnConnectionClosed?.Invoke(new ConnectionClosedEvent
        {
            CloseReason = ConnectionCloseReason.Clean,
            ClosedAt = DateTimeOffset.UtcNow,
        });
}
```

**CRITICAL:** Capture `prevState = CurrentStatus.State` BEFORE `ResetDisconnectedSessionState()` — `ResetDisconnectedSessionState()` calls `_adapter.Close()` which modifies the adapter, but `CurrentStatus.State` is owned by `_stateMachine` and is not reset there. Verify `CurrentStatus` is the state machine's value, not the adapter's.

**`private void HandleDisconnectError(Exception error)` in `SpacetimeConnectionService.cs`:**

Fires `ConnectionClosed(Error)` only when transitioning to Disconnected (not Degraded):

```csharp
private void HandleDisconnectError(Exception error)
{
    ClearCacheView();
    if (CurrentStatus.State == ConnectionState.Connected && _reconnectPolicy.TryBeginRetry(out var attemptNumber, out var delay))
    {
        _stateMachine.Transition(
            ConnectionState.Degraded,
            $"DEGRADED — session experiencing issues; reconnecting (attempt {attemptNumber}/{_reconnectPolicy.MaxAttempts}, backoff {delay.TotalSeconds:0.#}s): {error.Message}"
        );
        return;
        // NO ConnectionClosed here — session is degraded, not ended
    }
    RunConnectionTeardown(() =>
    {
        ResetDisconnectedSessionState();
        _stateMachine.Transition(ConnectionState.Disconnected, $"DISCONNECTED — connection lost: {error.Message}");
    });
    OnConnectionClosed?.Invoke(new ConnectionClosedEvent
    {
        CloseReason = ConnectionCloseReason.Error,
        ErrorMessage = error.Message,
        ClosedAt = DateTimeOffset.UtcNow,
    });
}
```

### What ConnectionClosed Does NOT Fire For

- **Failed connect** (`OnConnectError` in Connecting state): `OnConnectError` calls `ResetDisconnectedSessionState()` + state transition DIRECTLY, not through `Disconnect(string)`. The session was Connecting (never Connected), so no closed event. `ConnectionStateChanged` with Disconnected covers this case.
- **Degraded transitions**: `HandleDisconnectError` returns early before firing. Session is alive, just impaired.
- **Double-fire prevention**: `RunConnectionTeardown()` suppresses SDK-driven `OnDisconnect` callbacks while `_adapter.Close()` runs, and `OnDisconnected` ignores late callbacks once the service is already `Disconnected`.

### GodotSignalAdapter — The Scene-Safe Bridge Mechanism

Once `SpacetimeClient` has entered the scene tree, `Internal/Events/GodotSignalAdapter.cs` is the mechanism that makes signal delivery scene-safe:
```csharp
internal sealed class GodotSignalAdapter
{
    private readonly Node _owner;
    public void Dispatch(Action action)
    {
        if (!GodotObject.IsInstanceValid(_owner))
            return;
        Callable.From(action).CallDeferred();
    }
}
```

`CallDeferred()` queues the action on the Godot main thread's next idle frame — safe for scene tree access from signal handlers. Every signal handler in `SpacetimeClient` uses this pattern.

The `null` guard on `_signalAdapter` in each handler (`if (_signalAdapter == null) { EmitSignal directly; return; }`) handles the edge case where `_EnterTree` has not yet been called (e.g., before the node enters the scene tree). In normal usage, `_signalAdapter` is initialized in `_EnterTree` and is non-null for all signal delivery.

### Signal Ordering (ConnectionClosed fires after ConnectionStateChanged)

For all close paths, `_stateMachine.Transition(Disconnected, ...)` fires `ConnectionStateChanged` BEFORE `OnConnectionClosed?.Invoke(...)`. Game code will see:
1. `ConnectionStateChanged` → state is now Disconnected
2. `ConnectionClosed` → reason and error details

This mirrors how `ConnectionOpened` fires AFTER `ConnectionStateChanged` transitions to Connected. Consistent ordering.

### Existing Namespace Imports

`SpacetimeConnectionService.cs` already imports `GodotSpacetime.Connection` (for `ConnectionState`, `ConnectionStatus`, `ConnectionAuthState`). The `ConnectionCloseReason` and `ConnectionClosedEvent` types are in the same namespace — no new imports needed.

`SpacetimeClient.cs` already imports `GodotSpacetime.Connection` (for `ConnectionStatus`, `ConnectionOpenedEvent`). The `ConnectionClosedEvent` is in the same namespace — no new imports needed.

### Project Structure Notes

New files:
- `addons/godot_spacetime/src/Public/Connection/ConnectionCloseReason.cs`
- `addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs`
- `tests/test_story_4_3_bridge_runtime_callbacks.py`

Modified files:
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (add `OnConnectionClosed` event; modify `Disconnect(string)` and `HandleDisconnectError` to fire it)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (add `ConnectionClosed` signal + `HandleConnectionClosed`, wire in `_EnterTree`/`_ExitTree`)
- `docs/runtime-boundaries.md` (add `ConnectionClosedEvent` doc, add scene-safe bridge section with complete 8-signal catalog)

Naming conventions follow architecture doc:
- `ConnectionCloseReason.cs` in `Public/Connection/` (same folder as `ConnectionState.cs`, `ConnectionOpenedEvent.cs`)
- `ConnectionClosedEvent.cs` in `Public/Connection/`
- `ConnectionClosedEventHandler` delegate name (Godot convention: `{SignalName}EventHandler`)

### References

- FR25: "Developers can connect SDK callbacks and events to normal Godot application flow." [Source: `_bmad-output/planning-artifacts/prd.md`]
- Architecture naming convention — event identifiers and PascalCase equivalents: [Source: `_bmad-output/planning-artifacts/architecture.md`, lines 371-374]
- Architecture signal catalog authority: "Godot-facing signal concepts must use the same semantic names as the runtime event they represent" [Source: architecture.md line 374]
- Reference for `ConnectionOpenedEvent` shape: `addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs`
- Reference for `HandleConnectionOpened` pattern: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- `GodotSignalAdapter` implementation: `addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs`
- Existing `SpacetimeConnectionService.Disconnect(string)` and `HandleDisconnectError`: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (lines ~427-425, 410-424)
- Epic 3 Retro P1 (disconnect path checklist) pattern: `_bmad-output/implementation-artifacts/epic-3-retro-2026-04-14.md#Action Items` — required for all Epic 4 stateful adapter changes
- Epic 3 Retro P2 (dynamic lifecycle test) pattern: applied to `OnConnectionClosed +=` wiring scope
- Story 4.2 established: `ReducerCallSucceeded`/`ReducerCallFailed` signals, `GodotSignalAdapter.Dispatch` pattern
- Story 4.1 established: `InvokeReducer` path, `ReducerInvoker`, `SpacetimeSdkReducerAdapter.Invoke`, `SetConnection`, `ClearConnection`
- Story 3.x established: `SubscriptionApplied`, `SubscriptionFailed`, `RowChanged`, `GetRows`, `Subscribe`, `ReplaceSubscription`
- Test baseline: 1342 tests (end of Story 4.2 senior review)
- Tech stack: Godot 4.6.2, .NET 8+, SpacetimeDB.ClientSDK 2.1.0

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Created `ConnectionCloseReason.cs` enum with `Clean` and `Error` cases; no SpacetimeDB dependency; XML-documented.
- Created `ConnectionClosedEvent.cs` as `public partial class : RefCounted` mirroring `ConnectionOpenedEvent` shape; `ErrorMessage` defaults to `string.Empty`; `using System` for DateTimeOffset.
- Added `public event Action<ConnectionClosedEvent>? OnConnectionClosed` to `SpacetimeConnectionService` alongside existing events.
- Modified `Disconnect(string)`: captures `prevState` before `ResetDisconnectedSessionState()`, fires `ConnectionClosed(Clean)` only when `prevState is Connected or Degraded`, and review-hardened teardown with `RunConnectionTeardown()` so adapter-driven callbacks cannot double-fire or recurse through the disconnect path.
- Modified `HandleDisconnectError`: fires `ConnectionClosed(Error)` only on the Disconnected branch (after `_stateMachine.Transition`); Degraded branch exits early via `return` with no event; teardown is guarded against recursive `OnDisconnected` callbacks during `_adapter.Close()`.
- Added `ConnectionClosedEventHandler` signal to `SpacetimeClient` with corrected XML enum references, wired `OnConnectionClosed` in `_EnterTree`/`_ExitTree`, and added `HandleConnectionClosed` using the same null-check + deferred dispatch pattern as `HandleConnectionOpened`.
- All 8 `SpacetimeClient` signals now use `_signalAdapter.Dispatch` for thread-safe deferred dispatch.
- Updated `docs/runtime-boundaries.md`: added `ConnectionClosedEvent` property table after `ConnectionOpenedEvent` paragraph; added "Scene-Safe Signal Bridge" section with complete 8-signal catalog, transport advancement and reconnect policy ownership notes, and clarified the pre-`_EnterTree()` direct-emission edge case.
- Expanded `tests/test_story_4_3_bridge_runtime_callbacks.py` to 82 contract tests covering teardown reentrancy guards and reviewed docs. Full suite: 1434 tests, 0 failures.

### File List

- `addons/godot_spacetime/src/Public/Connection/ConnectionCloseReason.cs` (new)
- `addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs` (new)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (modified)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (modified)
- `docs/runtime-boundaries.md` (modified)
- `tests/test_story_4_3_bridge_runtime_callbacks.py` (new)
- `_bmad-output/implementation-artifacts/tests/test-summary.md` (modified — Story 4.3 review summary updated to 82 story tests / 1434 suite tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — story status synced to done)

## Change Log

- 2026-04-14: Story 4.3 implemented — added ConnectionClosed signal + ConnectionClosedEvent type; bridged OnDisconnect SDK callback into scene-safe Godot event; documented complete 8-signal catalog and scene-safe bridge mechanism in runtime-boundaries.md; 62 new contract tests added (1414 total).
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 1 High, 2 Medium fixed. Fixes: disconnect teardown is now guarded against reentrant or late SDK `OnDisconnected` callbacks so `ConnectionClosed` cannot double-fire; public docs now reference `ConnectionCloseReason` correctly and describe the pre-`_EnterTree()` signal-emission edge case; story/test artifacts were synced to the reviewed 82 story tests / 1434 suite tests. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List (`_bmad-output/story-automator/orchestration-1-20260414-184146.md`, `_bmad-output/implementation-artifacts/tests/test-summary.md`, and `_bmad-output/implementation-artifacts/sprint-status.yaml`).

### Findings Fixed

- HIGH: `SpacetimeConnectionService` teardown could recursively re-enter through SDK-driven `OnDisconnected` callbacks because `_adapter.Close()` ran during disconnect/error cleanup without any teardown guard. In the synchronous callback case, that could emit duplicate `ConnectionClosed` events and re-run disconnect cleanup against a session already being torn down.
- MEDIUM: Public 4.3 docs were not exact. `SpacetimeClient.ConnectionClosedEventHandler` XML comments referenced a nonexistent `CloseReason.*` type alias, and `docs/runtime-boundaries.md` overstated the scene-safe bridge by omitting the pre-`_EnterTree()` direct-emit edge case.
- MEDIUM: Story 4.3 verification evidence was stale after review. The story file still claimed `62` story tests / `1414` suite tests, while the auxiliary summary needed to reflect the reviewed `82` / `1434` result.

### Actions Taken

- Added `_isTearingDownConnection` plus `RunConnectionTeardown()` in `SpacetimeConnectionService`, and guarded `OnDisconnected` so teardown/late callbacks are ignored instead of recursively re-entering disconnect handling.
- Wrapped every `ResetDisconnectedSessionState()` path that can close the adapter during connect-start failure, failed-connect cleanup, disconnect-error cleanup, and explicit disconnect.
- Corrected `SpacetimeClient` XML docs to reference `ConnectionCloseReason.Clean` / `ConnectionCloseReason.Error` and clarified the `_EnterTree()` requirement for deferred scene-safe signal dispatch in `docs/runtime-boundaries.md`.
- Expanded `tests/test_story_4_3_bridge_runtime_callbacks.py` to 82 contract tests covering the teardown guard and reviewed docs, then synced the story, summary, and sprint-status artifacts to the reviewed counts and `done` status.

### Validation

- `python3 -m pytest tests/test_story_4_3_bridge_runtime_callbacks.py -q`
- `dotnet build godot-spacetime.sln -c Debug`
- `python3 -m pytest -q`

### Reference Check

- No dedicated Story Context or Epic 4 tech-spec artifact was present; `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/prd.md`, and `docs/runtime-boundaries.md` were used as the applicable planning and standards references.
- Tech stack validated during review: Godot `4.6.2`, `.NET` `8.0+`, `SpacetimeDB.ClientSDK` `2.1.0`.
- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `_bmad-output/planning-artifacts/prd.md`
- Local reference: `docs/runtime-boundaries.md`
- Local reference: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs`
- MCP documentation search was attempted, but no MCP resources were available in this session.
