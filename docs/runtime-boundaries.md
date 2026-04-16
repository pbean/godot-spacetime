# Runtime Boundaries — GodotSpacetime SDK Concepts

This document defines the public concept vocabulary for the GodotSpacetime SDK. All public API docs, sample guidance, and architecture notes use this terminology. You do not need to know how the first shipping runtime works to use this SDK because those implementation details stay behind the runtime boundary.

The canonical end-to-end implementation of these concepts is the sample project at `demo/README.md` and `demo/DemoMain.cs`.

## Concept Vocabulary

### Connection

A **Connection** is a session link from a Godot game client to a configured SpacetimeDB database. The entry point is [`SpacetimeClient`](#spacetimeclient), which you register as an autoload. Once configured and started, `SpacetimeClient` manages the full connection lifecycle without requiring direct interaction with any underlying runtime types.

### Connection Lifecycle — `ConnectionState`

The lifecycle of a connection is expressed as a [`ConnectionState`](../addons/godot_spacetime/src/Public/Connection/ConnectionState.cs) enum:

| State | Meaning |
|-------|---------|
| `Disconnected` | No active connection attempt. The initial state before `Connect()` is called, and the terminal state after a clean disconnect. |
| `Connecting` | An attempt to reach the database is in progress. |
| `Connected` | A live session is established and subscriptions may be applied. |
| `Degraded` | The session is experiencing trouble (e.g., transient network loss) but has not fully disconnected. Recovery is attempted automatically. |

A [`ConnectionStatus`](../addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs) value pairs a `ConnectionState` with a human-readable description for logging and UI display. [`ConnectionOpenedEvent`](../addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs) represents the successful-open boundary rather than every lifecycle transition.

[`ConnectionClosedEvent`](../addons/godot_spacetime/src/Public/Connection/ConnectionClosedEvent.cs) is the symmetric close-boundary event: it fires when a live session ends, after `ConnectionStateChanged` transitions to `Disconnected`. It does **not** fire for failed connect attempts (the session never reached `Connected`); `ConnectionStateChanged` covers those via the `Disconnected` state.

| Property | Type | Meaning |
|----------|------|---------|
| `CloseReason` | `ConnectionCloseReason` | `Clean`: explicit disconnect or server-side clean close. `Error`: session lost after being established. |
| `ErrorMessage` | `string` | Non-empty when `CloseReason` is `Error`; empty string for Clean closes. |
| `ClosedAt` | `DateTimeOffset` | UTC timestamp at which the SDK recorded the close event. |

A [`ConnectionAuthState`](../addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs) enum
accompanies `ConnectionStatus` and identifies the authentication phase:

| Auth State | Meaning |
|------------|---------|
| `None` | No authentication context. Anonymous session or pre-connection state. |
| `TokenRestored` | Restored or provided credentials were accepted; session is authenticated. |
| `AuthFailed` | Provided credentials were confirmed rejected (HTTP 401/403); auth-specific failure. |
| `ConnectFailed` | Connection failed while credentials were provided, but the cause is ambiguous (e.g., network timeout). Check `ConnectionStatus.Description` for detail. |
| `TokenExpired` | A previously stored token was rejected; clear the token store and reconnect. |

### Auth / Identity — `ITokenStore`

Session identity is token-based. The SDK does not dictate how tokens are persisted; instead, you provide an [`ITokenStore`](../addons/godot_spacetime/src/Public/Auth/ITokenStore.cs) implementation:

```csharp
Task<string?> GetTokenAsync();
Task StoreTokenAsync(string token);
Task ClearTokenAsync();
```

This is opt-in. If no `ITokenStore` is provided, tokens are not persisted across sessions. The interface is async so that persistence backends can use async I/O, but the current `Connect()` session-restoration path waits synchronously for `GetTokenAsync()` before opening the connection. Token stores used for restoration should therefore return promptly and avoid long-running work on the main thread.

**Built-in implementations** (from `Internal/Auth/`):
- `MemoryTokenStore` — retains the token in memory for the current process lifetime only. Tokens survive reconnects within a session but are cleared when the process exits.
- `ProjectSettingsTokenStore` — persists the token to Godot `ProjectSettings` under the key `spacetime/auth/token`. Suitable for development environments; review your distribution's security model before enabling in production.

`ProjectSettingsTokenStore` is `internal sealed` — external developers must implement `GodotSpacetime.Auth.ITokenStore` directly; it cannot be instantiated from outside the SDK.

Assign via code to `Settings.TokenStore` before calling `Connect()`. The built-in implementations are in `Internal/`; they are not exported to the Godot inspector.

**Token Clearing:** To clear persisted auth state, call `Settings.TokenStore?.ClearTokenAsync()` when a token store is configured. Token values are never logged raw; the `TokenRedactor` utility in `Internal/Auth/` produces safe diagnostic representations.

**Session Identity:** When a connection opens, the server assigns or restores an identity.
The identity string is included in [`ConnectionOpenedEvent.Identity`](../addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs).
For anonymous connections, the identity is a new server-assigned value; for credential-bearing connections,
it is the identity associated with the provided token.

**Session Restoration:** When `SpacetimeSettings.TokenStore` is configured and `Credentials` is not explicitly
set, `Connect()` calls `GetTokenAsync()` on the token store before opening the connection. If a non-empty
token is returned, it is injected via `WithToken()` — identical to setting `Credentials` explicitly for that
open call. The restored value is not retained on the settings resource after `Connect()` returns, so clearing
the token store resets future restoration attempts. A
successful restored session emits `ConnectionAuthState.TokenRestored` and surfaces the server identity via
`ConnectionOpenedEvent.Identity`. If no token is stored or the store throws, the connection falls back
cleanly to anonymous without leaving corrupted session state.

**Failure Recovery:** Auth failures surface as `ConnectionStatus` events, not exceptions — gameplay code
observes them through `SpacetimeClient.ConnectionStateChanged`. The `ConnectionAuthState` value on the
resulting status identifies the failure category and the recommended recovery path:

- `TokenExpired` — A stored token was rejected. Call `Settings.TokenStore?.ClearTokenAsync()` to remove
  the invalid token; the next `Connect()` call will fall back to anonymous (or use fresh credentials if
  `Settings.Credentials` is set). This state is only emitted when the session was opened via token
  restoration.
- `AuthFailed` — Explicit credentials were confirmed rejected by the server (HTTP 401/403). Update
  `Settings.Credentials` with a valid token before reconnecting.
- `ConnectFailed` — The connection failed while credentials were provided, but the error could not be
  confirmed as an authentication rejection. This typically indicates a network issue (timeout, DNS
  failure, server offline). Check `ConnectionStatus.Description` for the underlying error detail.
  Retry the connection; if the issue persists, verify network connectivity before assuming a credential
  problem.

Recoverable auth failures are distinct from unrecoverable programming faults (e.g., missing `Host` or
`Database`) which throw `ArgumentException` synchronously from `Connect()` before any connection attempt.
The separation ensures that gameplay error-handling code only needs to react to the `ConnectionStatus`
event stream for expected runtime failures, not catch exceptions from the SDK connection path.

### Subscriptions — `SubscriptionHandle`, `SubscriptionAppliedEvent`, and `SubscriptionFailedEvent`

A **Subscription** is a query scope that keeps a local cache slice synchronized with the server. You apply a subscription through [`SpacetimeClient.Subscribe(string[] queries)`](../addons/godot_spacetime/src/Public/SpacetimeClient.cs) once `ConnectionState.Connected` is reached. The SDK returns a [`SubscriptionHandle`](../addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs) immediately; the handle's `HandleId` is stable for the lifetime of the scope.

**Applying a subscription:**
```csharp
// In a ConnectionStateChanged handler or after verifying Connected state:
var handle = SpacetimeClient.Subscribe(new[] { "SELECT * FROM player" });
// handle.HandleId is assigned immediately and stays stable
```

**Guard:** `Subscribe()` throws `InvalidOperationException` if called before `ConnectionState.Connected`. It is safe to call from a `ConnectionStateChanged` handler once the state reaches `Connected`.

When the initial synchronization is complete, the `SpacetimeClient.SubscriptionApplied` signal fires with a [`SubscriptionAppliedEvent`](../addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs). After that point, the local cache reflects the subscribed data and is ready to read through `SpacetimeClient.GetRows()` and generated row casts.

| `SubscriptionAppliedEvent` property | Type | Meaning |
|-------------------------------------|------|---------|
| `Handle` | `SubscriptionHandle` | The handle whose subscription is now synchronized. Same object returned from `Subscribe()`. |
| `AppliedAt` | `DateTimeOffset` | UTC timestamp at which the SDK confirmed the subscription was applied. |

If a subscription is rejected or later enters an error path, the `SpacetimeClient.SubscriptionFailed` signal fires with a [`SubscriptionFailedEvent`](../addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs). The failed handle has already transitioned to `Closed`, the failed registry entry has been cleaned up, and any still-authoritative subscription remains readable.

| `SubscriptionFailedEvent` property | Type | Meaning |
|------------------------------------|------|---------|
| `Handle` | `SubscriptionHandle` | The handle whose subscription request failed. This is the same handle returned from `Subscribe()` or `ReplaceSubscription()`. |
| `ErrorMessage` | `string` | Human-readable failure detail from the runtime error, used to decide whether query correction, binding regeneration, or a retry is the right next step. |
| `FailedAt` | `DateTimeOffset` | UTC timestamp at which the SDK recorded the failure event. |

### Cache — Reading Synchronized Local State

The **Cache** is the local synchronized read model populated by active subscriptions. Reads from the cache are always local — no network round-trip. The cache is populated and kept current by the SDK runtime; you read from it after the `SubscriptionApplied` signal fires. If a replacement subscription fails, the previously authoritative synchronized state remains readable.

**Supported cache-access path:** `SpacetimeClient.GetRows(string tableName)` returns an `IEnumerable<object>` of all currently cached rows for the specified table. The table name must match the generated property name on the `RemoteTables` type — PascalCase, case-sensitive (e.g., `"Player"` for a `Player` table).

**Reading cache rows:**
```csharp
// In a SubscriptionApplied handler or after verifying the cache is ready:
foreach (var row in SpacetimeClient.GetRows("Player"))
{
    var player = (SpacetimeDB.Types.Player)row;
    GD.Print(player.Name);
}
```

**Guard:** `GetRows()` returns an empty sequence — not an exception — when the connection is not active or the cache is empty for the requested table. It throws `InvalidOperationException` only if the table name does not exist in the generated `RemoteTables` type (coding error, not a runtime condition).

Cache access is mediated by `CacheViewAdapter` (in `Internal/Cache/`) which wraps the generated `RemoteTables` object via reflection. Gameplay code must not access the underlying transport state directly — always go through `SpacetimeClient.GetRows()`.

### Row Changes — Observing Live Cache Updates

After the `SubscriptionApplied` signal fires, the SDK emits a `RowChanged` signal on `SpacetimeClient` each time a subscribed table row is inserted, updated, or removed by the server. Connect to this signal to drive gameplay reactions without polling `GetRows()` every frame.

**Signal payload:** [`RowChangedEvent`](../addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs)

| Property | Type | Meaning |
|----------|------|---------|
| `TableName` | `string` | PascalCase table name matching the generated `RemoteTables` property (e.g., `"SmokeTest"`) |
| `ChangeType` | `RowChangeType` | `Insert`, `Update`, or `Delete` |
| `OldRow` | `object?` | Row before the change; `null` for `Insert` events |
| `NewRow` | `object?` | Row after the change; `null` for `Delete` events |

**Reacting to row changes:**
```csharp
SpacetimeClient.RowChanged += OnRowChanged;

private void OnRowChanged(RowChangedEvent e)
{
    if (e.TableName != "SmokeTest") return;

    switch (e.ChangeType)
    {
        case RowChangeType.Insert:
            var inserted = (SpacetimeDB.Types.SmokeTest)e.NewRow!;
            GD.Print($"Inserted: {inserted.Value}");
            break;
        case RowChangeType.Update:
            var old = (SpacetimeDB.Types.SmokeTest)e.OldRow!;
            var updated = (SpacetimeDB.Types.SmokeTest)e.NewRow!;
            GD.Print($"Updated: {old.Value} → {updated.Value}");
            break;
        case RowChangeType.Delete:
            var deleted = (SpacetimeDB.Types.SmokeTest)e.OldRow!;
            GD.Print($"Deleted: {deleted.Value}");
            break;
    }
}
```

Row change dispatch is mediated by `SpacetimeSdkRowCallbackAdapter` (in `Internal/Platform/DotNet/`) which wires into the generated `RemoteTableHandle` events via reflection. Scene code must not access those events directly — always use the `SpacetimeClient.RowChanged` signal.

### Reducers — `ReducerCallResult` and `ReducerCallError`

A **Reducer** is a server-side callable procedure. You invoke reducers through generated binding types. The SDK surfaces the outcome as a [`ReducerCallResult`](../addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs) on success, or a [`ReducerCallError`](../addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs) when the call fails or is rejected.

Reducer results arrive **asynchronously** — the signal fires in a later frame than `InvokeReducer()` was called, after `FrameTick` delivers queued server messages. Gameplay code must **not** expect synchronous correlation between `InvokeReducer()` and `ReducerCallSucceeded`/`ReducerCallFailed`. Use `InvocationId` to correlate the outcome to the specific reducer call that produced it.

**`ReducerCallResult` properties:**

| Property | Type | Meaning |
|----------|------|---------|
| `ReducerName` | `string` | Identifies which reducer produced this result. |
| `InvocationId` | `string` | Opaque SDK-generated identifier for the specific reducer invocation instance. |
| `CalledAt` | `DateTimeOffset` | UTC timestamp recorded when the SDK accepted the reducer invocation. |
| `CompletedAt` | `DateTimeOffset` | UTC timestamp recorded when the SDK surfaced the committed result. |

**`ReducerCallError` properties:**

| Property | Type | Meaning |
|----------|------|---------|
| `ReducerName` | `string` | Identifies which reducer failed. |
| `InvocationId` | `string` | Opaque SDK-generated identifier for the specific reducer invocation instance. |
| `CalledAt` | `DateTimeOffset` | UTC timestamp recorded when the SDK accepted the reducer invocation. |
| `ErrorMessage` | `string` | Human-readable failure description from the server. |
| `FailureCategory` | `ReducerFailureCategory` | Failure category for branching gameplay error handling. |
| `RecoveryGuidance` | `string` | User-safe retry or feedback guidance derived from the failure category. |
| `FailedAt` | `DateTimeOffset` | UTC timestamp recorded when the SDK surfaced the failure. |

**`ReducerFailureCategory` enum — failure branching guidance:**

| Value | When it fires | Recommended action |
|-------|---------------|-------------------|
| `Failed` | Server rejected the reducer (logic error or constraint) | Check server logs or module logic; retrying with the same arguments is unlikely to succeed. |
| `OutOfEnergy` | Server ran out of energy | Back off and retry after a delay, or inform the player that the action is temporarily unavailable. |
| `Unknown` | Status could not be determined | Handle defensively; do not retry automatically without additional context. |

### Reducer Invocation

**`SpacetimeClient.InvokeReducer(object reducerArgs)`** is the public entry point for calling server-side reducers from gameplay code.

The `reducerArgs` parameter must be an `IReducerArgs` instance from the generated bindings for your module (e.g. `new SpacetimeDB.Types.Reducer.Ping()`). The C# type system enforces the `IReducerArgs` contract at the generated binding level.

**Invocation path:**
```
SpacetimeClient.InvokeReducer(object reducerArgs)
  └─ SpacetimeConnectionService.InvokeReducer(object reducerArgs)    [state check: Connected]
       └─ ReducerInvoker.Invoke(object reducerArgs)                   [null validation]
            └─ SpacetimeSdkReducerAdapter.Invoke(object reducerArgs)  [IReducerArgs cast + dispatch]
                 └─ runtime SDK reducer call                          [SpacetimeDB client runtime]
```

**Isolation zone:** `SpacetimeDB.*` reducer types are referenced **only** inside `SpacetimeSdkReducerAdapter` (in `Internal/Platform/DotNet/`). `ReducerInvoker`, `SpacetimeConnectionService`, and `SpacetimeClient` do not import `SpacetimeDB.*`.

**Guard:** `InvokeReducer()` requires `ConnectionState.Connected`. Calling it in any other connection state throws `InvalidOperationException`; calling it with a `null` argument throws `ArgumentNullException`; calling it with a non-`IReducerArgs` object (wrong argument type) throws `ArgumentException`. These exceptions are caught at `SpacetimeClient.InvokeReducer()` — they do **not** propagate to game code as thrown exceptions. Instead, `PublishValidationFailure` fires `ConnectionStateChanged(Disconnected, message)` and calls `GD.PushError(message)`, making the fault visible in the Godot error console (Editor Output panel / in-game error overlay). These are **programming faults** (code defects), not gameplay-handleable conditions — fix the calling code rather than handling them in gameplay error handlers.

#### Reducer Error Model: Programming Faults vs Recoverable Failures

Reducer call outcomes fall into two distinct categories that must not be conflated:

**Recoverable runtime failures** arrive asynchronously after the server responds. They always fire the `ReducerCallFailed` signal with a structured `ReducerCallError`. Branch on `ReducerCallError.FailureCategory` to determine the appropriate gameplay response and use `RecoveryGuidance` for player-facing feedback. These are expected gameplay conditions.

**Programming faults** (SDK misuse) are caught synchronously at `SpacetimeClient.InvokeReducer()` before any server contact occurs. They surface via `GD.PushError` + `ConnectionStateChanged(Disconnected)` — the `ReducerCallFailed` signal does **not** fire for programming faults. This validation-failure path is diagnostic surfacing, not a session-close notification: it does **not** emit `ConnectionClosed`. Fix the calling code; these are not conditions to handle in `ReducerCallFailed` signal handlers.

| Condition | How it surfaces | What gameplay code does |
|-----------|----------------|------------------------|
| Server rejects reducer (logic/constraint) | `ReducerCallFailed` → `ReducerCallError.FailureCategory = Failed` | Branch on `FailureCategory`; show player error |
| Server out of energy | `ReducerCallFailed` → `ReducerCallError.FailureCategory = OutOfEnergy` | Back off, retry after delay |
| Status unclear (SDK internal) | `ReducerCallFailed` → `ReducerCallError.FailureCategory = Unknown` | Handle defensively, do not auto-retry |
| Called while not Connected | `ConnectionStateChanged(Disconnected)` + `GD.PushError` | Fix the calling code; not a gameplay condition |
| Called with null args | `ConnectionStateChanged(Disconnected)` + `GD.PushError` | Fix the calling code; not a gameplay condition |
| Called with non-`IReducerArgs` type | `ConnectionStateChanged(Disconnected)` + `GD.PushError` | Fix the calling code; not a gameplay condition |

**Key rule:** Never check `ReducerCallError.FailureCategory` when the fault is a programming error — the `ReducerCallFailed` signal will not fire for programming faults; only `ConnectionStateChanged` + `GD.PushError` fire.

**Example usage:**
```csharp
// After ConnectionState.Connected is reached:
_client.InvokeReducer(new SpacetimeDB.Types.Reducer.Ping());
```

### Reducer Results

After an invocation reaches the server, the SDK delivers the outcome through an outbound callback path:

```
SpacetimeSdkReducerAdapter.RegisterCallbacks → per-reducer event hooks
  └─ TrackPendingInvocation(reducerName) when InvokeReducer() is accepted
  └─ ExtractAndDispatch(IReducerEventSink sink, object ctx)
       └─ TakePendingInvocation(reducerName)
       └─ status: Status.Committed → IReducerEventSink.OnReducerCallSucceeded
       └─ status: Status.Failed → IReducerEventSink.OnReducerCallFailed (ReducerFailureCategory.Failed + RecoveryGuidance)
       └─ status: Status.OutOfEnergy → IReducerEventSink.OnReducerCallFailed (ReducerFailureCategory.OutOfEnergy + RecoveryGuidance)
SpacetimeConnectionService.IReducerEventSink → ReducerCallResult / ReducerCallError payloads
SpacetimeClient.ReducerCallSucceeded / ReducerCallFailed signals → gameplay code
```

**Isolation zone:** `SpacetimeDB.Status` pattern matching happens **only** inside `SpacetimeSdkReducerAdapter.ExtractAndDispatch`. No `SpacetimeDB.*` types cross the boundary into `IReducerEventSink`, `SpacetimeConnectionService`, or `SpacetimeClient`. `ReducerFailureCategory` is a plain C# enum in the public `GodotSpacetime.Reducers` namespace with no `SpacetimeDB` dependency.

**Callback registration and correlation:** `RegisterCallbacks` is called in `IConnectionEventSink.OnConnected` immediately after `SetConnection`, when the connection is live. A `ConditionalWeakTable` idempotency guard on the `Reducers` object prevents double-registration if the same connection instance survives a `Degraded → Connected` recovery. The reducer adapter also tracks pending invocations by reducer name so each callback can surface the original `InvocationId` and `CalledAt` back to gameplay code.

**`ReducerCallSucceeded` / `ReducerCallFailed` signals:** These are dispatched through `GodotSignalAdapter.Dispatch` (CallDeferred), ensuring they fire on the main thread. Gameplay code can safely read from the scene tree in signal handlers. Inspect `ReducerCallError.RecoveryGuidance` when presenting player-safe feedback for failed reducer calls.

### Scene-Safe Signal Bridge

Once `SpacetimeClient` has entered the scene tree, its signals are dispatched through [`GodotSignalAdapter`](../addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs) using `Callable.From(action).CallDeferred()`. This queues each signal emission on the Godot main thread's next idle frame, making it safe to access the scene tree from any signal handler without manual thread marshalling. The direct `EmitSignal` fallback only exists for the pre-`_EnterTree()` edge case where no adapter has been initialized yet.

**Complete signal catalog:**

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

**Transport advancement:** `SpacetimeClient._Process()` calls `FrameTick()` on every frame while the connection is not `Disconnected`. Scene code must **not** call `FrameTick()` directly. Calling `FrameTick()` from multiple owners causes duplicate callback delivery.

**Reconnect policy:** `ReconnectPolicy` is owned internally by `SpacetimeConnectionService`. Scene code must **not** implement its own reconnect loop. Observe `ConnectionStateChanged` and `ConnectionClosed` to react to lifecycle changes.

### Generated Bindings

**Generated Bindings** are read-only C# types generated from a SpacetimeDB module schema using the `spacetimedb generate` command. They are specific to each module and live outside the addon itself. Generated types give you:

- Typed table row classes for cache reads
- Typed reducer invocation methods
- Typed event callbacks for row insert/update/delete changes

Generated bindings use the `GodotSpacetime.*` namespace vocabulary for event handling but are generated per-project, not shipped with the addon.

See [`docs/codegen.md`](./codegen.md) for the generation workflow.

### Configuration — `SpacetimeSettings`

[`SpacetimeSettings`](../addons/godot_spacetime/src/Public/SpacetimeSettings.cs) is a Godot `Resource` you create in the editor and assign to `SpacetimeClient`. It holds the configuration for a connection:

| Property | Type | Purpose |
|----------|------|---------|
| `Host` | `string` | The SpacetimeDB server address |
| `Database` | `string` | The target database name on the server |
| `Credentials` | `string?` | Optional token for authenticated sessions; passed to `WithToken()`. `null` = anonymous connection. |
| `TokenStore` | `ITokenStore?` | Optional token persistence provider; `null` by default (tokens not persisted) |

### SpacetimeClient — The SDK Entry Point

[`SpacetimeClient`](../addons/godot_spacetime/src/Public/SpacetimeClient.cs) is the top-level Godot-facing service. It is a `Node` registered as an autoload, so it is available from any scene. The intended workflow is:

```
SpacetimeClient (autoload, configured with SpacetimeSettings)
  └─ Connect()
       └─ ConnectionState events (Disconnected → Connecting → Connected)
            └─ Apply subscriptions (returns SubscriptionHandle)
                 ├─ SubscriptionAppliedEvent → read cache via GetRows() and generated row casts
                 │    └─ Invoke reducers → ReducerCallResult / ReducerCallError events
                 └─ SubscriptionFailedEvent → inspect ErrorMessage and decide whether to retry, correct the query, or regenerate bindings
```

You interact with `SpacetimeClient` through its public API; the underlying runtime handling is not part of the SDK surface.

---

## Runtime Boundaries

The GodotSpacetime codebase enforces three structural zones:

### `Public/` — The SDK Contract

`addons/godot_spacetime/src/Public/` contains the types listed in this document. These are the only types consumers of the SDK interact with directly. They may reference:
- `Godot.*` types
- `System.*` types
- Other `GodotSpacetime.*` public types

They must **never** reference runtime-specific transport or adapter types.

### `Internal/` — Implementation Zone

`addons/godot_spacetime/src/Internal/` contains implementation code that supports the public surface. Internal types may change without changing the public contract. Consumers of the SDK do not use internal types directly.

### `Internal/Platform/DotNet/` — The Runtime Isolation Zone

`addons/godot_spacetime/src/Internal/Platform/DotNet/` is the **only** zone in the codebase that is permitted to reference the underlying `.NET` client runtime. All adapter code that translates between the `GodotSpacetime.*` public surface and the current managed runtime lives here.

This isolation means that if a future native `GDScript` runtime is added, only the `Internal/Platform/` zone changes — the `Public/` contract and all code that depends on it remain stable.

---

## Future Runtime Seam

`addons/godot_spacetime/src/Internal/Platform/` is the designated location for future runtime implementations. The `.NET` adapter lives in `Internal/Platform/DotNet/`. A future native `GDScript` runtime adapter would be added at `Internal/Platform/GDScript/` and selected at build or load time without changing the public API.

The `Public/` contract is already runtime-neutral. None of the public type names (`ConnectionState`, `ITokenStore`, `SubscriptionHandle`, `SubscriptionAppliedEvent`, `ReducerCallResult`, `ReducerCallError`, `SpacetimeSettings`, `SpacetimeClient`, `LogCategory`) carry `.NET`-specific implementation language. A later native `GDScript` runtime does not require renaming or redefining any of these public concepts.

---

## Logging — `LogCategory`

[`LogCategory`](../addons/godot_spacetime/src/Public/Logging/LogCategory.cs) is an enum used to tag SDK log output by subsystem:

| Value | Subsystem |
|-------|-----------|
| `Connection` | Connection lifecycle events |
| `Auth` | Token store operations and identity events |
| `Subscription` | Subscription apply, remove, and error events |
| `Reducer` | Reducer call dispatch and result handling |
| `Codegen` | Generated binding load and schema validation events |

Log filtering by category is configured through `SpacetimeSettings` (added in a later story).
