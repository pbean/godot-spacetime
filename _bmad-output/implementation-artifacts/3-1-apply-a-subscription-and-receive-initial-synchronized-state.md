# Story 3.1: Apply a Subscription and Receive Initial Synchronized State

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Godot developer,
I want to subscribe to server data from the SDK,
So that my client receives the initial synchronized state for the queries it depends on.

## Acceptance Criteria

**AC 1 — Given** an active supported client session and a valid subscription query set
**When** I apply the subscription through `SpacetimeClient.Subscribe(string[] queries)`
**Then** the client receives the initial synchronized state for the subscribed data set

**AC 2 — Given** a subscription was applied
**When** the SDK confirms the initial synchronization is complete
**Then** the `SpacetimeClient.SubscriptionApplied` signal fires with a `SubscriptionAppliedEvent`
**And** the event carries the `SubscriptionHandle` that was returned from `Subscribe()`
**And** the event carries the `AppliedAt` UTC timestamp

**AC 3 — Given** `SpacetimeClient.Subscribe()` is called
**Then** the SDK immediately returns a stable `SubscriptionHandle` with a unique `HandleId`
**And** the handle remains the same object referenced in the later `SubscriptionAppliedEvent`

## Tasks / Subtasks

- [x] Task 1 — Flesh out `SubscriptionHandle` (AC: 3)
  - [x] Add `public Guid HandleId { get; }` property
  - [x] Change constructor to `internal SubscriptionHandle()` with `HandleId = Guid.NewGuid()`
  - [x] Add `using System;` directive

- [x] Task 2 — Flesh out `SubscriptionAppliedEvent` (AC: 2)
  - [x] Add `public SubscriptionHandle Handle { get; }` property
  - [x] Add `public DateTimeOffset AppliedAt { get; }` property
  - [x] Add `internal SubscriptionAppliedEvent(SubscriptionHandle handle)` constructor — body must be: `Handle = handle; AppliedAt = DateTimeOffset.UtcNow;`
  - [x] Add `using System;` directive

- [x] Task 3 — Add `Connection` property to `SpacetimeSdkConnectionAdapter.cs` (AC: 1)
  - [x] Add `internal IDbConnection? Connection => _dbConnection;` after the `_dbConnection` field
  - [x] Add XML doc comment: "Provides access to the active IDbConnection for other Platform/DotNet adapters. Returns null when not connected."

- [x] Task 4 — Implement `SpacetimeSdkSubscriptionAdapter.cs` (AC: 1, 2)
  - [x] Add `ISubscriptionEventSink` interface above the class definition (same file pattern as `IConnectionEventSink` in `SpacetimeSdkConnectionAdapter.cs`)
    - `void OnSubscriptionApplied(SubscriptionHandle handle);`
    - `void OnSubscriptionError(SubscriptionHandle handle, Exception error);`
  - [x] Replace stub with full class implementation using Expression trees (see Dev Notes for exact code)
  - [x] Add `Subscribe(IDbConnection connection, string[] querySqls, ISubscriptionEventSink sink, SubscriptionHandle handle)` method
  - [x] Add private `InvokeWithDelegate(object builder, string methodName, Delegate callback)` helper
  - [x] Add private `CreateAppliedCallback(object builder, SubscriptionHandle handle, ISubscriptionEventSink sink)` using Expression.Lambda
  - [x] Add private `CreateErrorCallback(object builder, SubscriptionHandle handle, ISubscriptionEventSink sink)` using Expression.Lambda
  - [x] Remove stub `#pragma warning` suppression comments

- [x] Task 5 — Update `SpacetimeConnectionService.cs` (AC: 1, 2, 3)
  - [x] Add `using GodotSpacetime.Subscriptions;` and `using GodotSpacetime.Runtime.Subscriptions;`
  - [x] Change class declaration to `internal sealed class SpacetimeConnectionService : IConnectionEventSink, ISubscriptionEventSink`
  - [x] Add `private readonly SpacetimeSdkSubscriptionAdapter _subscriptionAdapter = new();`
  - [x] Add `private readonly SubscriptionRegistry _subscriptionRegistry = new();`
  - [x] Add `public event Action<SubscriptionAppliedEvent>? OnSubscriptionApplied;`
  - [x] Add `Subscribe(string[] querySqls)` method (see Dev Notes for exact code)
  - [x] Add `void ISubscriptionEventSink.OnSubscriptionApplied(SubscriptionHandle handle)` — fires `OnSubscriptionApplied` event
  - [x] Add `void ISubscriptionEventSink.OnSubscriptionError(SubscriptionHandle handle, Exception error)` — no-op stub (Story 3.5 implements failure surface)
  - [x] In `Disconnect(string description)`: add `_subscriptionRegistry.Clear();` before `_adapter.Close()`

- [x] Task 6 — Update `SpacetimeClient.cs` (AC: 1, 2, 3)
  - [x] Add `using GodotSpacetime.Subscriptions;`
  - [x] Add `[Signal] public delegate void SubscriptionAppliedEventHandler(SubscriptionAppliedEvent e);`
  - [x] Add `public SubscriptionHandle Subscribe(string[] querySqls)` that delegates to `_connectionService.Subscribe(querySqls)`
  - [x] In `_EnterTree()`: add `_connectionService.OnSubscriptionApplied += HandleSubscriptionApplied;`
  - [x] In `_ExitTree()`: add `_connectionService.OnSubscriptionApplied -= HandleSubscriptionApplied;`
  - [x] Add private `HandleSubscriptionApplied(SubscriptionAppliedEvent appliedEvent)` — follows same GodotSignalAdapter dispatch pattern as `HandleConnectionOpened`

- [x] Task 7 — Create `Internal/Subscriptions/SubscriptionRegistry.cs` (AC: 3)
  - [x] Create `addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs`
  - [x] Namespace: `GodotSpacetime.Runtime.Subscriptions`
  - [x] `internal sealed class SubscriptionRegistry` with `Register(SubscriptionHandle)`, `Unregister(Guid)`, `ActiveHandles` readonly collection, and `Clear()` methods
  - [x] Backed by `Dictionary<Guid, SubscriptionHandle>` keyed on `HandleId`

- [x] Task 8 — Update `docs/runtime-boundaries.md` (AC: 1, 2, 3)
  - [x] Replace existing stub subscription section (lines 85–89) with full section (see Dev Notes for exact text)
  - [x] Add `SubscriptionAppliedEvent` property table
  - [x] Add usage example showing `Subscribe(string[] queries)` call
  - [x] Document the `Connected` precondition guard

- [x] Task 9 — Create `tests/test_story_3_1_subscription_apply.py` (AC: 1–3)
  - [x] Follow `ROOT`, `_read()`, `_lines()` pattern from `tests/test_story_2_4_failure_recovery.py`
  - [x] See Dev Notes for full test coverage list

- [x] Task 10 — Verify
  - [x] `python3 scripts/compatibility/validate-foundation.py` → exits 0
  - [x] `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
  - [x] `pytest tests/test_story_3_1_subscription_apply.py` → all pass
  - [x] `pytest -q` → full suite passes (665 + new story tests green)

## Dev Notes

### Scope: What This Story Is and Is Not

**In scope:**
- `SubscriptionHandle` with stable `HandleId` (Guid), internal constructor
- `SubscriptionAppliedEvent` with `Handle` and `AppliedAt` properties, internal constructor
- `SpacetimeSdkSubscriptionAdapter` — full subscription apply implementation using Expression trees (same reflection pattern as connection adapter)
- `ISubscriptionEventSink` interface (defined in `SpacetimeSdkSubscriptionAdapter.cs`)
- `SpacetimeSdkConnectionAdapter.Connection` internal property (exposes IDbConnection to sibling Platform/DotNet adapters)
- `SpacetimeConnectionService.Subscribe(string[] queries)` — guards on `Connected` state, creates handle, delegates to subscription adapter
- `SpacetimeConnectionService.OnSubscriptionApplied` event
- `SpacetimeConnectionService` implementing `ISubscriptionEventSink`
- `SubscriptionRegistry` in `Internal/Subscriptions/` (tracks active handles; used for cleanup on disconnect and future Story 3.4 replacement)
- `SpacetimeClient.Subscribe(string[] queries)` and `SubscriptionApplied` signal
- `docs/runtime-boundaries.md` subscription section update
- New test file `tests/test_story_3_1_subscription_apply.py`

**Out of scope:**
- Cache reads — accessing the synchronized cache data from Godot code is Story 3.2
- Row-level change callbacks — Story 3.3
- Subscription replacement — Story 3.4
- Subscription failure recovery surface — Story 3.5 (the `ISubscriptionEventSink.OnSubscriptionError` method is a no-op stub in this story)
- `SubscribeToAllTables()` convenience method — not required by Story 3.1 AC; add only if needed by the dev agent for completeness, but NOT required
- `SubscriptionQuerySet.cs` — part of the architecture directory but owned by Story 3.4 (query set management for replacement)
- `CacheViewAdapter.cs` — Story 3.2
- Demo/sample scenes for subscription flow — Epic 5

### What Already Exists — DO NOT RECREATE

| Component | Story | File |
|-----------|-------|------|
| `SubscriptionHandle` class (empty shell) | 1.3 | `Public/Subscriptions/SubscriptionHandle.cs` |
| `SubscriptionAppliedEvent` class (empty shell) | 1.3 | `Public/Subscriptions/SubscriptionAppliedEvent.cs` |
| `SpacetimeSdkSubscriptionAdapter` class (stub) | 1.4 | `Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` |
| `SpacetimeSdkConnectionAdapter` with `IDbConnection? _dbConnection` | 1.9 | `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` |
| `SpacetimeConnectionService` implementing `IConnectionEventSink` | 1.9, 2.x | `Internal/Connection/SpacetimeConnectionService.cs` |
| `GodotSignalAdapter.Dispatch(Action)` | 1.9 | `Internal/Events/GodotSignalAdapter.cs` |
| `SpacetimeClient` with `ConnectionStateChanged`, `ConnectionOpened` signals | 1.9, 2.x | `Public/SpacetimeClient.cs` |
| `ReconnectPolicy`, `ConnectionStateMachine` | 1.9 | `Internal/Connection/` |
| All auth infrastructure | 2.1–2.4 | `Internal/Auth/`, `Public/Auth/`, `Public/Connection/` |

### `SpacetimeSdkSubscriptionAdapter.cs` — Exact Implementation

The file should be fully replaced (it is currently a stub). The full implementation:

```csharp
using System;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using GodotSpacetime.Subscriptions;
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

internal interface ISubscriptionEventSink
{
    void OnSubscriptionApplied(SubscriptionHandle handle);
    void OnSubscriptionError(SubscriptionHandle handle, Exception error);
}

/// <summary>
/// Adapter for the SpacetimeDB .NET ClientSDK subscription layer.
///
/// This class is the ONLY location in the codebase where SpacetimeDB.ClientSDK
/// subscription types may be referenced directly. All higher-level internal services
/// and all public SDK surfaces depend on the GodotSpacetime.* contracts rather
/// than on SpacetimeDB.* types.
///
/// See docs/runtime-boundaries.md — "Internal/Platform/DotNet/ — The Runtime
/// Isolation Zone" for the architectural justification.
/// </summary>
internal sealed class SpacetimeSdkSubscriptionAdapter
{
    /// <summary>
    /// Applies a subscription to the given connection for the specified SQL queries.
    /// Wires the SDK subscription applied and error callbacks to <paramref name="sink"/>.
    /// </summary>
    internal void Subscribe(
        IDbConnection connection,
        string[] querySqls,
        ISubscriptionEventSink sink,
        SubscriptionHandle handle)
    {
        ArgumentNullException.ThrowIfNull(connection);
        ArgumentNullException.ThrowIfNull(querySqls);
        ArgumentNullException.ThrowIfNull(sink);
        ArgumentNullException.ThrowIfNull(handle);

        var builderMethod = connection.GetType()
            .GetMethod("SubscriptionBuilder", BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException(
                "Generated DbConnection must expose a public SubscriptionBuilder() method. " +
                "Ensure bindings are generated and compiled before calling Subscribe().");

        var builder = builderMethod.Invoke(connection, null)
            ?? throw new InvalidOperationException("SubscriptionBuilder() returned null.");

        builder = InvokeWithDelegate(builder, "OnApplied", CreateAppliedCallback(builder, handle, sink));
        builder = InvokeWithDelegate(builder, "OnError", CreateErrorCallback(builder, handle, sink));

        var subscribeMethod = builder.GetType()
            .GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m =>
                m.Name == "Subscribe" &&
                m.GetParameters().Length == 1 &&
                m.GetParameters()[0].ParameterType == typeof(string[]))
            ?? throw new InvalidOperationException(
                "Generated SubscriptionBuilder must expose a Subscribe(string[]) method.");

        subscribeMethod.Invoke(builder, new object[] { querySqls });
    }

    private static object InvokeWithDelegate(object builder, string methodName, Delegate callback)
    {
        var method = builder.GetType()
            .GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m => m.Name == methodName && m.GetParameters().Length == 1)
            ?? throw new InvalidOperationException(
                $"Generated SubscriptionBuilder must expose {methodName}(callback) method.");

        return method.Invoke(builder, new object[] { callback })
            ?? throw new InvalidOperationException(
                $"SubscriptionBuilder.{methodName}() returned null.");
    }

    private static Delegate CreateAppliedCallback(
        object builder,
        SubscriptionHandle handle,
        ISubscriptionEventSink sink)
    {
        var onAppliedMethod = builder.GetType()
            .GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m => m.Name == "OnApplied" && m.GetParameters().Length == 1)
            ?? throw new InvalidOperationException(
                "Generated SubscriptionBuilder must expose OnApplied(callback) method.");

        var delegateType = onAppliedMethod.GetParameters()[0].ParameterType;
        var genericArgs = delegateType.GetGenericArguments();

        if (genericArgs.Length != 1)
            throw new InvalidOperationException(
                "OnApplied callback must be Action<T> with one context type parameter.");

        var contextParam = Expression.Parameter(genericArgs[0], "ctx");
        var sinkConst = Expression.Constant(sink);
        var handleConst = Expression.Constant(handle);
        var appliedMethod = typeof(ISubscriptionEventSink)
            .GetMethod(nameof(ISubscriptionEventSink.OnSubscriptionApplied))!;
        var body = Expression.Call(sinkConst, appliedMethod, handleConst);

        return Expression.Lambda(delegateType, body, contextParam).Compile();
    }

    private static Delegate CreateErrorCallback(
        object builder,
        SubscriptionHandle handle,
        ISubscriptionEventSink sink)
    {
        var onErrorMethod = builder.GetType()
            .GetMethods(BindingFlags.Public | BindingFlags.Instance)
            .FirstOrDefault(m => m.Name == "OnError" && m.GetParameters().Length == 1)
            ?? throw new InvalidOperationException(
                "Generated SubscriptionBuilder must expose OnError(callback) method.");

        var delegateType = onErrorMethod.GetParameters()[0].ParameterType;
        var genericArgs = delegateType.GetGenericArguments();

        if (genericArgs.Length != 2)
            throw new InvalidOperationException(
                "OnError callback must be Action<TContext, Exception> with two type parameters.");

        var contextParam = Expression.Parameter(genericArgs[0], "ctx");
        var exceptionParam = Expression.Parameter(genericArgs[1], "ex");
        var sinkConst = Expression.Constant(sink);
        var handleConst = Expression.Constant(handle);
        var errorMethod = typeof(ISubscriptionEventSink)
            .GetMethod(nameof(ISubscriptionEventSink.OnSubscriptionError))!;
        var body = Expression.Call(sinkConst, errorMethod, handleConst, exceptionParam);

        return Expression.Lambda(delegateType, body, contextParam, exceptionParam).Compile();
    }
}
```

**Key reflection pattern:** Same approach as `SpacetimeSdkConnectionAdapter` — uses `Expression.Lambda` to compile type-safe delegates without referencing generated `SpacetimeDB.Types.*` types directly. The callback types (`Action<SubscriptionEventContext>` and `Action<ErrorContext, Exception>`) are discovered via reflection and the parameters are built as `ParameterExpression` from the resolved generic arguments.

### `SpacetimeSdkConnectionAdapter.cs` — Single Addition

Add this property after the existing `private IDbConnection? _dbConnection;` field declaration:

```csharp
/// <summary>
/// Provides access to the active <c>IDbConnection</c> for sibling adapters in the
/// <c>Internal/Platform/DotNet/</c> isolation zone (e.g., <c>SpacetimeSdkSubscriptionAdapter</c>).
/// Returns <c>null</c> when not connected.
/// </summary>
internal IDbConnection? Connection => _dbConnection;
```

No other changes to the connection adapter in this story.

### `SpacetimeConnectionService.cs` — Exact Changes Required

**New using directives** (add at top):
```csharp
using GodotSpacetime.Subscriptions;
using GodotSpacetime.Runtime.Subscriptions;
```

**Class declaration change:**
```csharp
// Before:
internal sealed class SpacetimeConnectionService : IConnectionEventSink

// After:
internal sealed class SpacetimeConnectionService : IConnectionEventSink, ISubscriptionEventSink
```

**New fields** (add after `private bool _restoredFromStore;`):
```csharp
private readonly SpacetimeSdkSubscriptionAdapter _subscriptionAdapter = new();
private readonly SubscriptionRegistry _subscriptionRegistry = new();
```

**New event** (add after `public event Action<ConnectionOpenedEvent>? OnConnectionOpened;`):
```csharp
public event Action<SubscriptionAppliedEvent>? OnSubscriptionApplied;
```

**New `Subscribe` method** (add after `Disconnect()` public method):
```csharp
public SubscriptionHandle Subscribe(string[] querySqls)
{
    if (CurrentStatus.State != ConnectionState.Connected)
        throw new InvalidOperationException(
            "Subscribe() requires an active Connected session. " +
            "Call Connect() and wait for ConnectionState.Connected before applying subscriptions.");

    var connection = _adapter.Connection
        ?? throw new InvalidOperationException(
            "Not connected — no active IDbConnection. Call Connect() first.");

    var handle = new SubscriptionHandle();
    _subscriptionRegistry.Register(handle);
    _subscriptionAdapter.Subscribe(connection, querySqls, this, handle);
    return handle;
}
```

**`ISubscriptionEventSink` implementation** (add after the existing `IConnectionEventSink` implementations):
```csharp
void ISubscriptionEventSink.OnSubscriptionApplied(SubscriptionHandle handle)
{
    OnSubscriptionApplied?.Invoke(new SubscriptionAppliedEvent(handle));
}

void ISubscriptionEventSink.OnSubscriptionError(SubscriptionHandle handle, Exception error)
{
    // Subscription failure recovery is implemented in Story 3.5.
    // The error is observable via the SpacetimeDB SDK log output at the Platform/DotNet boundary.
}
```

**`Disconnect(string description)` update** — add `_subscriptionRegistry.Clear();` before `_adapter.Close();`:
```csharp
private void Disconnect(string description)
{
    _subscriptionRegistry.Clear();   // ← NEW: clear tracked subscriptions on disconnect
    _adapter.Close();
    _reconnectPolicy.Reset();
    // ... rest of method unchanged
}
```

### `SpacetimeClient.cs` — Exact Changes Required

**New using directive** (add at top):
```csharp
using GodotSpacetime.Subscriptions;
```

**New signal** (add after `ConnectionOpenedEventHandler` signal):
```csharp
[Signal]
public delegate void SubscriptionAppliedEventHandler(SubscriptionAppliedEvent e);
```

**New public method** (add after `Disconnect()` public method):
```csharp
public SubscriptionHandle Subscribe(string[] querySqls)
{
    return _connectionService.Subscribe(querySqls);
}
```

**`_EnterTree()` addition** (add after the existing `_connectionService.OnConnectionOpened += HandleConnectionOpened;` line):
```csharp
_connectionService.OnSubscriptionApplied += HandleSubscriptionApplied;
```

**`_ExitTree()` addition** (add after the existing `_connectionService.OnConnectionOpened -= HandleConnectionOpened;` line):
```csharp
_connectionService.OnSubscriptionApplied -= HandleSubscriptionApplied;
```

**New private handler** (add after `HandleConnectionOpened`):
```csharp
private void HandleSubscriptionApplied(SubscriptionAppliedEvent appliedEvent)
{
    if (_signalAdapter == null)
    {
        EmitSignal(SignalName.SubscriptionApplied, appliedEvent);
        return;
    }

    _signalAdapter.Dispatch(() => EmitSignal(SignalName.SubscriptionApplied, appliedEvent));
}
```

### `Internal/Subscriptions/SubscriptionRegistry.cs` — New File

```csharp
using System;
using System.Collections.Generic;
using GodotSpacetime.Subscriptions;

namespace GodotSpacetime.Runtime.Subscriptions;

/// <summary>
/// Tracks active <see cref="SubscriptionHandle"/> instances within the current session.
/// Used by <c>SpacetimeConnectionService</c> to maintain a stable reference to every
/// subscription scope that has been applied and to clean up on session end.
/// </summary>
internal sealed class SubscriptionRegistry
{
    private readonly Dictionary<Guid, SubscriptionHandle> _handles = new();

    /// <summary>Registers a handle when a subscription is applied.</summary>
    internal void Register(SubscriptionHandle handle)
    {
        _handles[handle.HandleId] = handle;
    }

    /// <summary>Removes a handle when a subscription is unsubscribed or errors.</summary>
    internal void Unregister(Guid handleId)
    {
        _handles.Remove(handleId);
    }

    /// <summary>All currently tracked active subscription handles.</summary>
    internal IReadOnlyCollection<SubscriptionHandle> ActiveHandles => _handles.Values;

    /// <summary>Clears all tracked handles — called when a session disconnects.</summary>
    internal void Clear()
    {
        _handles.Clear();
    }
}
```

### `docs/runtime-boundaries.md` — Required Update

**Replace lines 85–89** (the existing stub Subscriptions section):

```markdown
### Subscriptions — `SubscriptionHandle` and `SubscriptionAppliedEvent`

A **Subscription** is a query scope that keeps a local cache slice synchronized with the server. You apply a subscription through [`SpacetimeClient.Subscribe(string[] queries)`](../addons/godot_spacetime/src/Public/SpacetimeClient.cs) once `ConnectionState.Connected` is reached. The SDK returns a [`SubscriptionHandle`](../addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs) immediately; the handle's `HandleId` is stable for the lifetime of the scope.

**Applying a subscription:**
```csharp
// In a ConnectionStateChanged handler or after verifying Connected state:
var handle = SpacetimeClient.Subscribe(new[] { "SELECT * FROM player" });
// handle.HandleId is assigned immediately and stays stable
```

**Guard:** `Subscribe()` throws `InvalidOperationException` if called before `ConnectionState.Connected`. It is safe to call from a `ConnectionStateChanged` handler once the state reaches `Connected`.

When the initial synchronization is complete, the `SpacetimeClient.SubscriptionApplied` signal fires with a [`SubscriptionAppliedEvent`](../addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs). After that point, the local cache reflects the subscribed data and is ready to read through generated binding types.

| `SubscriptionAppliedEvent` property | Type | Meaning |
|-------------------------------------|------|---------|
| `Handle` | `SubscriptionHandle` | The handle whose subscription is now synchronized. Same object returned from `Subscribe()`. |
| `AppliedAt` | `DateTimeOffset` | UTC timestamp at which the SDK confirmed the subscription was applied. |
```

### Test File Coverage — `tests/test_story_3_1_subscription_apply.py`

#### `SubscriptionHandle.cs` content tests (AC: 3)
- Contains `HandleId` property
- `HandleId` is `Guid` type
- Contains `internal SubscriptionHandle()` constructor pattern
- Namespace is `GodotSpacetime.Subscriptions`

#### `SubscriptionAppliedEvent.cs` content tests (AC: 2)
- Contains `Handle` property of `SubscriptionHandle` type
- Contains `AppliedAt` property of `DateTimeOffset` type
- Contains `internal SubscriptionAppliedEvent(SubscriptionHandle handle)` constructor
- Namespace is `GodotSpacetime.Subscriptions`
- Contains `using System;` for `DateTimeOffset`

#### `SpacetimeSdkSubscriptionAdapter.cs` content tests (AC: 1, 2)
- Contains `ISubscriptionEventSink` interface definition
- Interface contains `OnSubscriptionApplied` method
- Interface contains `OnSubscriptionError` method
- Contains `Subscribe` method with `IDbConnection`, `string[]`, `ISubscriptionEventSink`, `SubscriptionHandle` parameters
- Contains `Expression.Lambda` or `Expression.Call` (Expression tree usage)
- Contains `InvokeWithDelegate` helper method
- No stub `#pragma warning disable CS0169` (removed the stub)
- Contains `CreateAppliedCallback` method
- Contains `CreateErrorCallback` method

#### `SpacetimeSdkConnectionAdapter.cs` content tests (AC: 1)
- Contains `internal IDbConnection? Connection` property
- `Connection` property returns `_dbConnection`

#### `SpacetimeConnectionService.cs` content tests (AC: 1, 2, 3)
- Contains `ISubscriptionEventSink` in class declaration
- Contains `_subscriptionAdapter` field
- Contains `_subscriptionRegistry` field
- Contains `OnSubscriptionApplied` event
- Contains `Subscribe` method accepting `string[]`
- Contains `ConnectionState.Connected` check in `Subscribe`
- Contains `OnSubscriptionApplied?.Invoke` call
- Contains `SubscriptionAppliedEvent` construction
- Contains `_subscriptionRegistry.Clear()` call

#### `SpacetimeClient.cs` content tests (AC: 1, 2, 3)
- Contains `SubscriptionApplied` signal (`SubscriptionAppliedEventHandler` delegate)
- Contains `Subscribe` method
- Subscribe method returns `SubscriptionHandle`
- Contains `HandleSubscriptionApplied` private method
- Contains `OnSubscriptionApplied +=` and `-=` in `_EnterTree`/`_ExitTree`

#### `SubscriptionRegistry.cs` existence and content tests (AC: 3)
- File exists at `addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs`
- Contains `Register` method
- Contains `Clear` method
- Contains `ActiveHandles` property
- Namespace is `GodotSpacetime.Runtime.Subscriptions`

#### `docs/runtime-boundaries.md` content tests (AC: 1, 2, 3)
- Contains `Subscribe(` usage example (the method call)
- Contains `SubscriptionApplied` signal reference
- Contains `HandleId` property reference
- Contains `AppliedAt` property reference
- Contains `InvalidOperationException` guard description

#### Regression guards (must still pass from earlier stories)
- `SpacetimeSdkConnectionAdapter.cs` still has `Open`, `FrameTick`, `Close` methods
- `SpacetimeSdkConnectionAdapter.cs` still has `IConnectionEventSink` interface
- `SpacetimeConnectionService.cs` still has `OnStateChanged`, `OnConnectionOpened`, `OnConnectError` references
- `SpacetimeConnectionService.cs` still implements `IConnectionEventSink`
- `SpacetimeClient.cs` still has `ConnectionStateChanged` signal and `ConnectionOpened` signal
- `SpacetimeClient.cs` still has `Connect()` and `Disconnect()` methods
- `tests/test_story_2_4_failure_recovery.py` → all tests still pass
- `tests/test_story_2_3_session_restore.py` → all tests still pass
- `tests/test_story_1_9_connection.py` → all tests still pass

### File Locations — DO and DO NOT

**DO modify:**
```
addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs       (add HandleId, internal ctor)
addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs (add Handle, AppliedAt, internal ctor)
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs  (add Connection property)
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs  (full implementation)
addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs  (ISubscriptionEventSink, Subscribe, events)
addons/godot_spacetime/src/Public/SpacetimeClient.cs                        (Subscribe method, SubscriptionApplied signal)
docs/runtime-boundaries.md                                                  (subscription section update)
```

**DO create:**
```
addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs
tests/test_story_3_1_subscription_apply.py
```

**DO NOT touch:**
```
addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs    (Transition API unchanged)
addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs           (reconnect logic unchanged)
addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs         (auth state unchanged)
addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs            (status unchanged)
addons/godot_spacetime/src/Internal/Auth/                                   (auth unchanged)
addons/godot_spacetime/src/Public/Auth/ITokenStore.cs                       (token store interface unchanged)
addons/godot_spacetime/src/Editor/                                          (no editor changes needed)
scripts/compatibility/support-baseline.json                                 (no new tracked files)
demo/generated/                                                             (generated files — read-only)
```

### Cross-Story Awareness

- **Story 1.3** established `SubscriptionHandle` and `SubscriptionAppliedEvent` as empty placeholder classes. Story 3.1 fills them in without breaking the namespace contract.
- **Story 1.4** established `SpacetimeSdkSubscriptionAdapter` as a stub with `IDbConnection? _dbConnection` to prove the isolation boundary. Story 3.1 replaces the stub with a full implementation — the `_dbConnection` field was only needed to establish the boundary at that stage.
- **Story 1.9** established `SpacetimeSdkConnectionAdapter` with `IDbConnection _dbConnection`. Story 3.1 exposes `Connection => _dbConnection` so the subscription adapter can get access without coupling the two adapters directly.
- **Story 2.x** established the `SpacetimeConnectionService` structure with `IConnectionEventSink`. Story 3.1 adds a second interface implementation (`ISubscriptionEventSink`) following the exact same dispatch pattern.
- **Story 3.2** (read cache data) will use the `SubscriptionAppliedEvent.Handle` to know when the cache is ready to read. The `HandleId` on the handle provides a stable identifier for associating the applied event with specific subscriptions.
- **Story 3.4** (replace subscriptions) will use `SubscriptionRegistry.ActiveHandles` and `SubscriptionQuerySet` to track and replace active query sets. `SubscriptionQuerySet.cs` is deferred to Story 3.4 — do NOT create it in Story 3.1.
- **Story 3.5** (subscription failure recovery) will implement `ISubscriptionEventSink.OnSubscriptionError` fully. The no-op stub in Story 3.1 is intentional.
- **Disconnect behavior:** The `_subscriptionRegistry.Clear()` call in `Disconnect()` prevents stale handles from Story 3.1 being referenced after a session ends. This is needed because Stories 3.4 and 3.5 will query the registry to manage active subscriptions.

### Namespace and Isolation Rules

- `SubscriptionHandle.cs` and `SubscriptionAppliedEvent.cs` are in `GodotSpacetime.Subscriptions` — no new usings beyond `System`
- `SpacetimeSdkSubscriptionAdapter.cs` is in `GodotSpacetime.Runtime.Platform.DotNet` — imports `SpacetimeDB` (for `IDbConnection`) and `GodotSpacetime.Subscriptions` (for `SubscriptionHandle`)
- `SpacetimeConnectionService.cs` adds `GodotSpacetime.Subscriptions` and `GodotSpacetime.Runtime.Subscriptions` imports
- `SpacetimeClient.cs` adds `GodotSpacetime.Subscriptions` import
- `SubscriptionRegistry.cs` is in `GodotSpacetime.Runtime.Subscriptions`
- NO `SpacetimeDB.*` references in any file outside `Internal/Platform/DotNet/` — the isolation boundary is preserved
- `SpacetimeClient` (in `GodotSpacetime` root namespace) may reference `GodotSpacetime.Subscriptions` public types — this is the intended SDK boundary

### SDK `SubscriptionBuilder` API Reference

From the generated bindings (`demo/generated/smoke_test/SpacetimeDBClient.g.cs`), the subscription API is:

```csharp
// conn is IDbConnection from generated DbConnection
conn.SubscriptionBuilder()                        // returns SpacetimeDB.Types.SubscriptionBuilder
    .OnApplied(Action<SubscriptionEventContext>)   // callback when sync complete
    .OnError(Action<ErrorContext, Exception>)      // callback on subscription failure
    .Subscribe(string[] querySqls)                // returns SDK SubscriptionHandle, starts sync
```

The `SubscriptionEventContext` and `ErrorContext` are generated types in `SpacetimeDB.Types`. Our adapter crosses the isolation boundary using `Expression.Lambda` to create compiled delegates — the generated types are discovered via reflection so the adapter code does NOT directly reference any `SpacetimeDB.Types.*` generated types.

### Verification Sequence

Run in order — each must pass before the next:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_3_1_subscription_apply.py
pytest -q
```

**Troubleshooting:**
- If `dotnet build` fails on `ISubscriptionEventSink`: ensure the interface is in `GodotSpacetime.Runtime.Platform.DotNet` namespace and `SpacetimeConnectionService` adds `using GodotSpacetime.Runtime.Platform.DotNet;` (or the interface is accessible without a using through the existing namespace reference)
- If `dotnet build` fails on `SubscriptionRegistry`: ensure the `using GodotSpacetime.Runtime.Subscriptions;` is added to `SpacetimeConnectionService.cs`
- If `dotnet build` fails on `SpacetimeSdkConnectionAdapter.Connection`: verify the property is added to the class body (not outside it) and uses `internal` access modifier
- If Expression tree compile fails at runtime: check that `delegateType.GetGenericArguments()` returns non-empty array — this means the generated `SubscriptionBuilder.OnApplied` method signature changed; verify against the actual generated file in `demo/generated/`
- If `SubscriptionApplied` signal fails to emit: verify `HandleSubscriptionApplied` is wired in `_EnterTree` and unwired in `_ExitTree`; verify `_signalAdapter` null check follows the same pattern as `HandleConnectionOpened`
- If regression tests fail: verify `_restoredFromStore`, `_credentialsProvided`, auth state fields, and the reconnect policy are unchanged in `SpacetimeConnectionService`

### Project Structure Notes

- New file `Internal/Subscriptions/SubscriptionRegistry.cs` creates the `Internal/Subscriptions/` directory — this directory is called for in the architecture document
- `SubscriptionQuerySet.cs` is also in the architecture for `Internal/Subscriptions/` but belongs to Story 3.4 — do NOT pre-create it
- `Internal/Cache/CacheViewAdapter.cs` (also in architecture) belongs to Story 3.2 — do NOT pre-create it
- The `SpacetimeSdkSubscriptionAdapter.cs` replacement removes the story-1.4 stub. The stub served its purpose (established the isolation boundary); now the full implementation takes its place

### References

- Story 3.1 AC and epic context: [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 3, Story 3.1]
- FR17 (subscribe to server data) and FR18 (receive initial synchronized state): [Source: `_bmad-output/planning-artifacts/epics.md` — FR map]
- Architecture: subscription model uses scoped subscriptions, `SubscriptionBuilder`, applied event forwarding: [Source: `_bmad-output/planning-artifacts/architecture.md` — API & Communication Patterns]
- Architecture: `Internal/Platform/DotNet/` is the only zone referencing `SpacetimeDB.*` types: [Source: `_bmad-output/planning-artifacts/architecture.md` — Project Structure & Boundaries]
- Architecture: event names describe facts, payload shapes additive-first: [Source: `_bmad-output/planning-artifacts/architecture.md` — Communication Patterns]
- Architecture file structure: `Internal/Subscriptions/SubscriptionRegistry.cs`, `Internal/Cache/CacheViewAdapter.cs`: [Source: `_bmad-output/planning-artifacts/architecture.md` — Project Structure]
- SDK subscription API: `conn.SubscriptionBuilder().OnApplied(...).OnError(...).Subscribe(string[])`: [Source: `demo/generated/smoke_test/SpacetimeDBClient.g.cs`]
- Reflection/Expression tree pattern for crossing the isolation boundary: [Source: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` — CreateConnectCallback pattern]
- `GodotSignalAdapter.Dispatch` pattern for scene-safe signal emission: [Source: `addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs`]
- Existing `IConnectionEventSink` pattern: [Source: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs`]
- Stub `SpacetimeSdkSubscriptionAdapter`: [Source: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs`]
- Runtime boundaries documentation: [Source: `docs/runtime-boundaries.md`]
- Story 2.4 for latest `SpacetimeConnectionService` state: [Source: `_bmad-output/implementation-artifacts/spec-2-4-recover-from-common-session-and-identity-failures.md`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- GD0202 build error on `SubscriptionAppliedEvent` signal parameter: resolved by making both `SubscriptionHandle` and `SubscriptionAppliedEvent` `partial class : RefCounted` — same pattern as `ConnectionOpenedEvent` and `ConnectionStatus`. This is a Godot C# requirement for all custom signal parameter types.
- Regression failures in test_story_1_3_sdk_concepts.py: regex `public\s+class\s+SubscriptionHandle` didn't account for `partial` keyword. Updated to `public\s+(?:partial\s+)?class\s+SubscriptionHandle`.
- Regression failure in test_story_1_4_adapter_boundary.py: `test_adapter_has_idbconnection_stub_field` checked for `IDbConnection\?` (nullable field from stub). Story 3.1 replaces stub with real implementation using `IDbConnection connection` (non-nullable parameter). Updated regex to `IDbConnection` without nullable marker.

### Completion Notes List

- ✅ Task 1: `SubscriptionHandle` fleshed out — `Guid HandleId`, `internal SubscriptionHandle()` constructor. Made `partial class : RefCounted` (required by Godot for signal parameter compatibility). `using System;` added.
- ✅ Task 2: `SubscriptionAppliedEvent` fleshed out — `SubscriptionHandle Handle`, `DateTimeOffset AppliedAt`, `internal SubscriptionAppliedEvent(SubscriptionHandle handle)` constructor. Made `partial class : RefCounted` for same reason as SubscriptionHandle. `using System;` added.
- ✅ Task 3: `SpacetimeSdkConnectionAdapter.Connection` property added — `internal IDbConnection? Connection => _dbConnection;` with XML doc comment.
- ✅ Task 4: `SpacetimeSdkSubscriptionAdapter` stub replaced with full Expression-tree implementation. `ISubscriptionEventSink` interface, `Subscribe()`, `InvokeWithDelegate()`, `CreateAppliedCallback()`, `CreateErrorCallback()` all implemented. Stub `#pragma warning` removed.
- ✅ Task 5: `SpacetimeConnectionService` updated — added `ISubscriptionEventSink`, new fields, `OnSubscriptionApplied` event, `Subscribe()` method with `Connected` guard, `ISubscriptionEventSink` explicit implementations, `_subscriptionRegistry.Clear()` in `Disconnect()`.
- ✅ Task 6: `SpacetimeClient` updated — `using GodotSpacetime.Subscriptions;`, `SubscriptionAppliedEventHandler` signal, `Subscribe()` public method, `_EnterTree`/`_ExitTree` event wiring, `HandleSubscriptionApplied` using same GodotSignalAdapter dispatch pattern.
- ✅ Task 7: `SubscriptionRegistry.cs` created at `Internal/Subscriptions/` — `Register`, `Unregister`, `ActiveHandles`, `Clear` methods. Namespace `GodotSpacetime.Runtime.Subscriptions`.
- ✅ Task 8: `docs/runtime-boundaries.md` subscription section updated — added `Subscribe()` usage example, `SubscriptionApplied` signal reference, `HandleId` stable identifier, `AppliedAt` property table, `InvalidOperationException` guard description.
- ✅ Task 9: `tests/test_story_3_1_subscription_apply.py` created — 61 tests covering all ACs, isolation guards, and regression guards.
- ✅ Task 10: All verifications pass — `validate-foundation.py` exits 0, `dotnet build` 0 errors/warnings, 61/61 new tests pass, 727/727 full suite passes.

### File List

addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs
addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs
addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs
addons/godot_spacetime/src/Public/SpacetimeClient.cs
addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs
docs/runtime-boundaries.md
tests/test_story_3_1_subscription_apply.py
tests/test_story_1_3_sdk_concepts.py
tests/test_story_1_4_adapter_boundary.py

### Change Log

- 2026-04-14: Story 3.1 implemented — subscription apply and initial sync state surface complete. `SubscriptionHandle` and `SubscriptionAppliedEvent` fleshed out. `SpacetimeSdkSubscriptionAdapter` stub replaced with full Expression-tree implementation. `SpacetimeConnectionService` and `SpacetimeClient` wired for subscription flow. `SubscriptionRegistry` created. `docs/runtime-boundaries.md` subscription section updated. 61 new tests added; prior tests updated for `partial class` and stub→implementation transition.
- 2026-04-14: Senior developer review auto-fix applied. Tightened `SubscriptionHandle` and `SubscriptionAppliedEvent` to getter-only public properties, added synchronous subscribe-failure cleanup in `SpacetimeConnectionService`, and expanded Story 3.1 regression coverage.

## Senior Developer Review (AI)

### Reviewer

Codex (GPT-5)

### Outcome

Approve

### References Used

- No dedicated Story Context or Epic 3 context artifact was present; `_bmad-output/planning-artifacts/architecture.md` and `docs/runtime-boundaries.md` were used as the applicable standards references.
- No MCP documentation resources were available in-session. The subscription contract was verified against `demo/generated/smoke_test/SpacetimeDBClient.g.cs` and installed `SpacetimeDB.ClientSDK` 2.1.0 metadata from the local NuGet cache.

### Findings Fixed

1. `SubscriptionHandle.HandleId` was implemented as `get; private set;` instead of the getter-only contract required by Task 1, weakening the story's stable-handle guarantee.
2. `SubscriptionAppliedEvent.Handle` and `AppliedAt` were implemented as `get; private set;` instead of the getter-only contract required by Task 2, weakening the event immutability promised by the story.
3. `SpacetimeConnectionService.Subscribe()` registered the handle before adapter setup but did not unregister it when the adapter failed synchronously, leaving stale handles in `SubscriptionRegistry` after invalid input or reflection/setup failures.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_3_1_subscription_apply.py`
- `pytest -q`
