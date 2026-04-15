# Story 3.3: Observe Row-Level Changes for Subscribed Data

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Godot developer,
I want row-level change notifications for subscribed data,
So that gameplay systems can react to inserts, updates, and removals as the cache changes.

## Acceptance Criteria

**AC 1 — Given** an active subscription and server-side row changes affecting subscribed data
**When** changes arrive at the client
**Then** the SDK emits a `RowChanged` signal on `SpacetimeClient` for each row-level change
**And** the signal payload (`RowChangedEvent`) includes the table name, change type (Insert/Update/Delete), and the affected row(s) as `object`
**And** each row object can be cast to the generated row type (e.g., `(SpacetimeDB.Types.SmokeTest)e.NewRow`)

**AC 2 — Given** gameplay code receives a `RowChangedEvent`
**Then** the event payload provides `OldRow` (null for inserts) and `NewRow` (null for deletes)
**And** the `ChangeType` enum distinguishes Insert, Update, and Delete without requiring inspection of `OldRow`/`NewRow` nullability

**AC 3 — Given** the `RowChanged` signal wiring
**Then** scene consumers do not need to reference any `SpacetimeDB.*` types to subscribe to or handle row change events
**And** the SDK boundary (`SpacetimeClient`) is the only required import for consuming row changes

## Tasks / Subtasks

- [x] Task 1 — Create `Public/Subscriptions/RowChangeType.cs` (AC: 2)
  - [x] Create `addons/godot_spacetime/src/Public/Subscriptions/RowChangeType.cs`
  - [x] Namespace: `GodotSpacetime.Subscriptions`
  - [x] `public enum RowChangeType` with values: `Insert`, `Update`, `Delete`
  - [x] No `SpacetimeDB.*` import (public contract must stay runtime-neutral)

- [x] Task 2 — Create `Public/Subscriptions/RowChangedEvent.cs` (AC: 1, 2, 3)
  - [x] Create `addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs`
  - [x] Namespace: `GodotSpacetime.Subscriptions`
  - [x] `public partial class RowChangedEvent : RefCounted` (Godot-safe, matches `SubscriptionAppliedEvent` pattern)
  - [x] Properties: `string TableName`, `RowChangeType ChangeType`, `object? OldRow`, `object? NewRow`
  - [x] `internal` constructor: `RowChangedEvent(string tableName, RowChangeType changeType, object? oldRow, object? newRow)`
  - [x] Add XML doc comments (see Dev Notes for exact text)
  - [x] No `SpacetimeDB.*` import

- [x] Task 3 — Create `Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs` (AC: 1, 2, 3)
  - [x] Create `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs`
  - [x] Namespace: `GodotSpacetime.Runtime.Platform.DotNet`
  - [x] Define `internal interface IRowChangeEventSink` with three methods (see Dev Notes for exact signatures)
  - [x] `internal sealed class SpacetimeSdkRowCallbackAdapter` with `RegisterCallbacks(object db, IRowChangeEventSink sink)` method
  - [x] `RegisterCallbacks` iterates the generated `RemoteTables` members, supports field-backed and property-backed table handles, and wires OnInsert/OnDelete/OnUpdate via Expression trees
  - [x] Use `using SpacetimeDB;` (allowed — this is Platform/DotNet isolation zone)
  - [x] See Dev Notes for full implementation

- [x] Task 4 — Update `SpacetimeConnectionService.cs` (AC: 1, 2, 3)
  - [x] Add `using GodotSpacetime.Subscriptions;`
  - [x] Add `private readonly SpacetimeSdkRowCallbackAdapter _rowCallbackAdapter = new();` field
  - [x] Add `public event Action<RowChangedEvent>? OnRowChanged;`
  - [x] Implement `IRowChangeEventSink` on the class (add to class declaration + implement three methods)
  - [x] In `IConnectionEventSink.OnConnected`: register row callbacks after `_cacheViewAdapter.SetDb(...)` (see Dev Notes)
  - [x] Add three explicit interface implementations: `OnRowInserted`, `OnRowDeleted`, `OnRowUpdated`

- [x] Task 5 — Update `SpacetimeClient.cs` (AC: 1, 2, 3)
  - [x] Add `[Signal] public delegate void RowChangedEventHandler(RowChangedEvent e);`
  - [x] Add `private void HandleRowChanged(RowChangedEvent e)` (see existing handler pattern)
  - [x] Wire/unwire in `_EnterTree` / `_ExitTree` via `_connectionService.OnRowChanged`
  - [x] No `SpacetimeDB.*` import

- [x] Task 6 — Update `docs/runtime-boundaries.md` (AC: 1, 2, 3)
  - [x] Add a new "Row Changes — Observing Live Cache Updates" section after the Cache section
  - [x] Document `RowChanged` signal, `RowChangedEvent` payload, cast pattern, `ChangeType` enum
  - [x] See Dev Notes for exact text

- [x] Task 7 — Create `tests/test_story_3_3_observe_row_level_changes.py` (AC: 1–3)
  - [x] Follow `ROOT`, `_read()`, `_lines()` pattern from `tests/test_story_3_2_read_synchronized_cache.py`
  - [x] See Dev Notes for full test coverage list

- [x] Task 8 — Verify
  - [x] `python3 scripts/compatibility/validate-foundation.py` → exits 0
  - [x] `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
  - [x] `pytest tests/test_story_3_3_observe_row_level_changes.py` → all pass (117 tests)
  - [x] `pytest -q` → full suite passes (948 tests, 0 regressions)

## Dev Notes

### Scope: What This Story Is and Is Not

**In scope:**
- `RowChangeType.cs` — `Insert`, `Update`, `Delete` enum in `Public/Subscriptions/`
- `RowChangedEvent.cs` — event payload in `Public/Subscriptions/` with `TableName`, `ChangeType`, `OldRow?`, `NewRow?`
- `SpacetimeSdkRowCallbackAdapter.cs` — `IRowChangeEventSink` interface + reflection-based adapter in `Internal/Platform/DotNet/`
- `SpacetimeConnectionService` wiring: `_rowCallbackAdapter` field, `IRowChangeEventSink` impl, `OnRowChanged` event, `RegisterCallbacks()` call in `OnConnected`
- `SpacetimeClient.RowChanged` signal + `HandleRowChanged` handler
- `docs/runtime-boundaries.md` new section documenting row change events

**Out of scope:**
- Subscription replacement — Story 3.4
- Subscription failure recovery — Story 3.5
- Reducer invocation — Epic 4
- `OnBeforeDelete` event — not needed for AC; omit unless tests require it
- Per-table subscription filtering (scene code can filter on `RowChangedEvent.TableName`)
- `SubscriptionQuerySet.cs` — Story 3.4
- Typed generic `RowChangedEvent<TRow>` — use `object?` to stay runtime-neutral across the boundary

### What Already Exists — DO NOT RECREATE

| Component | Story | File |
|-----------|-------|------|
| `SpacetimeSdkConnectionAdapter` with `GetDb()` via reflection | 3.2 | `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` |
| `SpacetimeSdkSubscriptionAdapter` with Expression-tree pattern | 3.1 | `Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` |
| `IConnectionEventSink` interface (same file as connection adapter) | 3.1 | `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` |
| `ISubscriptionEventSink` interface (same file as subscription adapter) | 3.1 | `Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` |
| `SpacetimeConnectionService` implementing `IConnectionEventSink`, `ISubscriptionEventSink` | 3.1 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `CacheViewAdapter` with `SetDb(object? db)` and `GetRows(string tableName)` | 3.2 | `Internal/Cache/CacheViewAdapter.cs` |
| `SubscriptionRegistry` with `Register`, `Unregister`, `Clear`, `ActiveHandles` | 3.1 | `Internal/Subscriptions/SubscriptionRegistry.cs` |
| `SpacetimeClient` with `Subscribe()`, `SubscriptionApplied` signal, `GetRows()` | 3.1/3.2 | `Public/SpacetimeClient.cs` |
| `SubscriptionHandle` with `HandleId` (Guid), internal ctor | 3.1 | `Public/Subscriptions/SubscriptionHandle.cs` |
| `SubscriptionAppliedEvent` with `Handle`, `AppliedAt` | 3.1 | `Public/Subscriptions/SubscriptionAppliedEvent.cs` |
| `GodotSignalAdapter.Dispatch(Action)` — Callable.From().CallDeferred() | prior | `Internal/Events/GodotSignalAdapter.cs` |
| All auth infrastructure | 2.1–2.4 | `Internal/Auth/`, `Public/Auth/`, `Public/Connection/` |

### SpacetimeDB SDK Row Event API (VERIFIED via reflection on 2.1.0 DLL)

All events are on `RemoteTableHandle<TEventContext, TRow>` (and its base `RemoteTableHandleBase<TEventContext, TRow>`).
The delegate type is a nested `RowEventHandler` / `UpdateEventHandler` in the base class.

| Event | Signature | Note |
|-------|-----------|------|
| `OnInsert` | `(EventContext context, TRow row) -> void` | 2 params |
| `OnDelete` | `(EventContext context, TRow row) -> void` | 2 params |
| `OnBeforeDelete` | `(EventContext context, TRow row) -> void` | 2 params (skip in this story) |
| `OnUpdate` | `(EventContext context, TRow oldRow, TRow newRow) -> void` | 3 params |

Internal events (`OnInternalInsert`, `OnInternalDelete`) have signature `Action<TRow>` — **do not wire these**.

When iterating table properties on `RemoteTables`:
- `GetEvent("OnInsert")` finds it on the base class through inheritance — works correctly
- The `EventHandlerType` at runtime will be the closed generic (e.g., `RowEventHandler[EventContext, SmokeTest]`)
- Use `GetEvent("OnInsert")` → `EventHandlerType` → `GetMethod("Invoke")` → `GetParameters()` to extract the exact parameter types for Expression trees

### `Public/Subscriptions/RowChangeType.cs` — New File

```csharp
namespace GodotSpacetime.Subscriptions;

/// <summary>
/// The type of row-level change in a subscribed table.
/// Corresponds to the <c>subscription.row_changed</c> SDK domain event.
/// </summary>
public enum RowChangeType
{
    /// <summary>A new row was inserted into the local cache.</summary>
    Insert,

    /// <summary>An existing row was updated in the local cache.</summary>
    Update,

    /// <summary>A row was removed from the local cache.</summary>
    Delete
}
```

### `Public/Subscriptions/RowChangedEvent.cs` — New File

```csharp
using System;
using Godot;

namespace GodotSpacetime.Subscriptions;

/// <summary>
/// Event payload raised when a row-level change occurs in a subscribed table.
/// Emitted by <see cref="GodotSpacetime.SpacetimeClient.RowChanged"/> after the
/// <c>SubscriptionApplied</c> signal fires and the subscription is active.
///
/// Corresponds to the <c>subscription.row_changed</c> SDK domain event.
///
/// See <c>docs/runtime-boundaries.md</c> — "Row Changes — Observing Live Cache Updates" for usage.
/// </summary>
public partial class RowChangedEvent : RefCounted
{
    /// <summary>
    /// The PascalCase name of the table in which the row changed.
    /// Matches the generated property name on the <c>RemoteTables</c> type
    /// (e.g., <c>"SmokeTest"</c> for a <c>smoke_test</c> module table).
    /// </summary>
    public string TableName { get; }

    /// <summary>
    /// The kind of row change: Insert, Update, or Delete.
    /// </summary>
    public RowChangeType ChangeType { get; }

    /// <summary>
    /// The row value before the change. Null for <see cref="RowChangeType.Insert"/> events.
    /// Cast to the generated row type to access typed fields.
    /// </summary>
    public object? OldRow { get; }

    /// <summary>
    /// The row value after the change. Null for <see cref="RowChangeType.Delete"/> events.
    /// Cast to the generated row type to access typed fields.
    /// </summary>
    public object? NewRow { get; }

    internal RowChangedEvent(
        string tableName,
        RowChangeType changeType,
        object? oldRow,
        object? newRow)
    {
        TableName = tableName;
        ChangeType = changeType;
        OldRow = oldRow;
        NewRow = newRow;
    }
}
```

### `Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs` — New File

```csharp
using System;
using System.Linq.Expressions;
using System.Reflection;
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

internal interface IRowChangeEventSink
{
    void OnRowInserted(string tableName, object row);
    void OnRowDeleted(string tableName, object row);
    void OnRowUpdated(string tableName, object oldRow, object newRow);
}

/// <summary>
/// Adapter for the SpacetimeDB .NET ClientSDK row-level change callback layer.
///
/// This class is the ONLY location in the codebase where SpacetimeDB.ClientSDK
/// row callback events may be referenced directly. Hooks into the generated
/// RemoteTableHandle events (OnInsert, OnDelete, OnUpdate) via reflection and
/// Expression trees, routing them to the GodotSpacetime-neutral
/// <see cref="IRowChangeEventSink"/> interface.
///
/// See <c>docs/runtime-boundaries.md</c> — "Internal/Platform/DotNet/ — The Runtime
/// Isolation Zone" for the architectural justification.
/// </summary>
internal sealed class SpacetimeSdkRowCallbackAdapter
{
    /// <summary>
    /// Registers insert, update, and delete callbacks on all table handles found in the
    /// generated RemoteTables object. Each callback routes row change events to
    /// <paramref name="sink"/> with the table name and boxed row values.
    ///
    /// Call immediately after <c>OnConnected</c> fires, with the live RemoteTables object
    /// from <c>SpacetimeSdkConnectionAdapter.GetDb()</c>. No explicit unregistration is
    /// needed on disconnect — the registered delegates are collected with the closed
    /// connection's RemoteTables graph once all GC roots to it are cleared.
    /// </summary>
    internal void RegisterCallbacks(object db, IRowChangeEventSink sink)
    {
        ArgumentNullException.ThrowIfNull(db);
        ArgumentNullException.ThrowIfNull(sink);

        foreach (var prop in db.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            var tableHandle = prop.GetValue(db);
            if (tableHandle == null) continue;

            var tableName = prop.Name;
            TryWireRowEvent(tableHandle, "OnInsert", tableName, sink, isDelete: false);
            TryWireRowEvent(tableHandle, "OnDelete", tableName, sink, isDelete: true);
            TryWireUpdateEvent(tableHandle, tableName, sink);
        }
    }

    private static void TryWireRowEvent(
        object tableHandle,
        string eventName,
        string tableName,
        IRowChangeEventSink sink,
        bool isDelete)
    {
        var evt = tableHandle.GetType().GetEvent(eventName);
        if (evt?.EventHandlerType == null) return;

        var invoke = evt.EventHandlerType.GetMethod("Invoke");
        if (invoke == null) return;

        var parameters = invoke.GetParameters();
        if (parameters.Length != 2) return;   // (TContext context, TRow row)

        var ctxParam = Expression.Parameter(parameters[0].ParameterType, "ctx");
        var rowParam = Expression.Parameter(parameters[1].ParameterType, "row");
        var sinkConst = Expression.Constant(sink);
        var tableNameConst = Expression.Constant(tableName);
        var rowAsObject = Expression.Convert(rowParam, typeof(object));

        var sinkMethod = isDelete
            ? typeof(IRowChangeEventSink).GetMethod(nameof(IRowChangeEventSink.OnRowDeleted))!
            : typeof(IRowChangeEventSink).GetMethod(nameof(IRowChangeEventSink.OnRowInserted))!;

        var body = Expression.Call(sinkConst, sinkMethod, tableNameConst, rowAsObject);
        var lambda = Expression.Lambda(evt.EventHandlerType, body, ctxParam, rowParam).Compile();
        evt.AddEventHandler(tableHandle, (Delegate)lambda);
    }

    private static void TryWireUpdateEvent(object tableHandle, string tableName, IRowChangeEventSink sink)
    {
        var evt = tableHandle.GetType().GetEvent("OnUpdate");
        if (evt?.EventHandlerType == null) return;

        var invoke = evt.EventHandlerType.GetMethod("Invoke");
        if (invoke == null) return;

        var parameters = invoke.GetParameters();
        if (parameters.Length != 3) return;   // (TContext context, TRow oldRow, TRow newRow)

        var ctxParam = Expression.Parameter(parameters[0].ParameterType, "ctx");
        var oldRowParam = Expression.Parameter(parameters[1].ParameterType, "oldRow");
        var newRowParam = Expression.Parameter(parameters[2].ParameterType, "newRow");
        var sinkConst = Expression.Constant(sink);
        var tableNameConst = Expression.Constant(tableName);
        var oldRowAsObject = Expression.Convert(oldRowParam, typeof(object));
        var newRowAsObject = Expression.Convert(newRowParam, typeof(object));

        var sinkMethod = typeof(IRowChangeEventSink).GetMethod(nameof(IRowChangeEventSink.OnRowUpdated))!;
        var body = Expression.Call(sinkConst, sinkMethod, tableNameConst, oldRowAsObject, newRowAsObject);
        var lambda = Expression.Lambda(evt.EventHandlerType, body, ctxParam, oldRowParam, newRowParam).Compile();
        evt.AddEventHandler(tableHandle, (Delegate)lambda);
    }
}
```

**Key points:**
- `using SpacetimeDB;` is required here (Platform/DotNet isolation zone — only place allowed)
- Does NOT import `SpacetimeDB.Types.*` — accesses table handles via reflection only
- `TryWire*` methods silently skip events that don't exist on the given table handle type (graceful degradation)
- Parameter count guards (`if (parameters.Length != 2)` / `if (parameters.Length != 3)`) prevent wiring `OnInternalInsert`/`OnInternalDelete` which have `Action<TRow>` (1 param) signatures
- Expression trees match the exact closed generic delegate type — same pattern as `SpacetimeSdkSubscriptionAdapter.CreateAppliedCallback()`
- No explicit unregistration needed — delegates are collected with the RemoteTables graph when `_adapter.Close()` + `_cacheViewAdapter.SetDb(null)` clear all GC roots to the old connection

### `SpacetimeConnectionService.cs` — Required Changes

**New using directive** (add at top after existing usings):
```csharp
using GodotSpacetime.Subscriptions;
```

**Class declaration update** (add `IRowChangeEventSink` to implements list):
```csharp
internal sealed class SpacetimeConnectionService : IConnectionEventSink, ISubscriptionEventSink, IRowChangeEventSink
```

**New field** (add after `_cacheViewAdapter` field):
```csharp
private readonly SpacetimeSdkRowCallbackAdapter _rowCallbackAdapter = new();
```

**New event** (add after `OnSubscriptionApplied` event):
```csharp
public event Action<RowChangedEvent>? OnRowChanged;
```

**`IConnectionEventSink.OnConnected` addition** (add after `_cacheViewAdapter.SetDb(_adapter.GetDb());`):
```csharp
var db = _adapter.GetDb();
if (db != null)
    _rowCallbackAdapter.RegisterCallbacks(db, this);
```

Full updated block for clarity:
```csharp
void IConnectionEventSink.OnConnected(string identity, string token)
{
    _reconnectPolicy.Reset();
    _cacheViewAdapter.SetDb(_adapter.GetDb());          // wire cache view on connect
    var db = _adapter.GetDb();                          // ← NEW: wire row callbacks
    if (db != null)
        _rowCallbackAdapter.RegisterCallbacks(db, this);  // ← NEW
    if (_tokenStore != null)
    { ... }
```

**New explicit interface implementations** (add after `ISubscriptionEventSink.OnSubscriptionError`):
```csharp
void IRowChangeEventSink.OnRowInserted(string tableName, object row)
{
    OnRowChanged?.Invoke(new RowChangedEvent(tableName, RowChangeType.Insert, null, row));
}

void IRowChangeEventSink.OnRowDeleted(string tableName, object row)
{
    OnRowChanged?.Invoke(new RowChangedEvent(tableName, RowChangeType.Delete, row, null));
}

void IRowChangeEventSink.OnRowUpdated(string tableName, object oldRow, object newRow)
{
    OnRowChanged?.Invoke(new RowChangedEvent(tableName, RowChangeType.Update, oldRow, newRow));
}
```

**No changes** to `ResetDisconnectedSessionState()`, `ClearCacheView()`, or `Disconnect()` — row callback cleanup is handled automatically via GC once `_cacheViewAdapter.SetDb(null)` and `_adapter.Close()` clear the GC roots to the old RemoteTables.

### `SpacetimeClient.cs` — Required Changes

**New signal** (add after `SubscriptionAppliedEventHandler`):
```csharp
[Signal]
public delegate void RowChangedEventHandler(RowChangedEvent e);
```

**New using directive** (add if not present — `GodotSpacetime.Subscriptions` may already be imported via existing using):
`RowChangedEvent` and `RowChangeType` live in `GodotSpacetime.Subscriptions`, same namespace as `SubscriptionAppliedEvent`. No new using needed if namespace glob is already there. Check existing imports — add only if missing.

**Wire in `_EnterTree`** (add after existing event wires):
```csharp
_connectionService.OnRowChanged += HandleRowChanged;
```

**Unwire in `_ExitTree`** (add after existing unwires):
```csharp
_connectionService.OnRowChanged -= HandleRowChanged;
```

**New handler method** (add after `HandleSubscriptionApplied`):
```csharp
private void HandleRowChanged(RowChangedEvent rowChangedEvent)
{
    if (_signalAdapter == null)
    {
        EmitSignal(SignalName.RowChanged, rowChangedEvent);
        return;
    }

    _signalAdapter.Dispatch(() => EmitSignal(SignalName.RowChanged, rowChangedEvent));
}
```

### `docs/runtime-boundaries.md` — Required Addition

**Add this section** immediately after the "Cache — Reading Synchronized Local State" section (before the "Reducers" section):

```markdown
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
```

### Test File Coverage — `tests/test_story_3_3_observe_row_level_changes.py`

#### `RowChangeType.cs` content tests (AC: 2)
- File exists at `Public/Subscriptions/RowChangeType.cs`
- Namespace is `GodotSpacetime.Subscriptions`
- Contains `public enum RowChangeType`
- Contains `Insert` value
- Contains `Update` value
- Contains `Delete` value
- Does NOT contain `SpacetimeDB.` string (isolation boundary)

#### `RowChangedEvent.cs` content tests (AC: 1, 2, 3)
- File exists at `Public/Subscriptions/RowChangedEvent.cs`
- Namespace is `GodotSpacetime.Subscriptions`
- Contains `public partial class RowChangedEvent : RefCounted`
- Has `TableName` property
- Has `ChangeType` property of type `RowChangeType`
- Has `OldRow` property
- Has `NewRow` property
- Has `internal RowChangedEvent(` constructor
- Does NOT contain `SpacetimeDB.` string (isolation boundary)

#### `SpacetimeSdkRowCallbackAdapter.cs` content tests (AC: 1, 2, 3)
- File exists at `Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs`
- Namespace is `GodotSpacetime.Runtime.Platform.DotNet`
- Contains `internal interface IRowChangeEventSink`
- Contains `OnRowInserted` method on interface
- Contains `OnRowDeleted` method on interface
- Contains `OnRowUpdated` method on interface
- Contains `internal sealed class SpacetimeSdkRowCallbackAdapter`
- Contains `RegisterCallbacks` method
- Uses `Expression.Lambda` (reflection + expression trees pattern)
- Uses `AddEventHandler`
- Uses `using SpacetimeDB;` (allowed — isolation zone)
- Contains `OnInsert` string (wires insert event)
- Contains `OnDelete` string (wires delete event)
- Contains `OnUpdate` string (wires update event)

#### `SpacetimeConnectionService.cs` content tests (AC: 1, 2, 3)
- Contains `_rowCallbackAdapter` field
- Contains `SpacetimeSdkRowCallbackAdapter` type reference
- Contains `IRowChangeEventSink` in class declaration
- Contains `OnRowChanged` event
- Contains `RegisterCallbacks` call in body
- Contains explicit `IRowChangeEventSink.OnRowInserted` implementation
- Contains explicit `IRowChangeEventSink.OnRowDeleted` implementation
- Contains explicit `IRowChangeEventSink.OnRowUpdated` implementation
- Contains `RowChangeType.Insert` reference
- Contains `RowChangeType.Delete` reference
- Contains `RowChangeType.Update` reference
- Does NOT contain `SpacetimeDB.` (isolation boundary — row callback adapter handles that)

#### `SpacetimeClient.cs` content tests (AC: 1, 2, 3)
- Contains `RowChangedEventHandler` delegate declaration
- Contains `[Signal]` above `RowChangedEventHandler`
- Contains `OnRowChanged += HandleRowChanged` wiring
- Contains `OnRowChanged -= HandleRowChanged` unwiring
- Contains `HandleRowChanged` method
- Contains `EmitSignal(SignalName.RowChanged` call
- Does NOT contain `SpacetimeDB.` (isolation boundary)

#### `docs/runtime-boundaries.md` content tests (AC: 1, 2, 3)
- Contains `RowChanged` reference
- Contains `RowChangedEvent` reference
- Contains `RowChangeType` reference
- Contains `OldRow` reference
- Contains `NewRow` reference
- Contains `TableName` reference
- Contains cast example (e.g., `(SpacetimeDB.Types.` or similar cast description)
- Contains `SubscriptionApplied` reference (timing context preserved from Story 3.2)
- Contains `SpacetimeSdkRowCallbackAdapter` reference

#### Regression guards — prior story deliverables must still pass
- `SpacetimeSdkConnectionAdapter.cs` still has `Connection` property
- `SpacetimeSdkConnectionAdapter.cs` still has `GetDb()` method (Story 3.2)
- `SpacetimeSdkConnectionAdapter.cs` still has `Open`, `FrameTick`, `Close` methods
- `SpacetimeSdkSubscriptionAdapter.cs` still has `Subscribe` method, `ISubscriptionEventSink` interface
- `SpacetimeConnectionService.cs` still has `Subscribe`, `OnSubscriptionApplied`, `_subscriptionRegistry`
- `SpacetimeConnectionService.cs` still has `_cacheViewAdapter`, `GetRows` method (Story 3.2)
- `SpacetimeConnectionService.cs` still has `_subscriptionRegistry.Clear()` in `ResetDisconnectedSessionState`
- `SpacetimeClient.cs` still has `Subscribe`, `SubscriptionAppliedEventHandler`, `HandleSubscriptionApplied`
- `SpacetimeClient.cs` still has `ConnectionStateChanged`, `ConnectionOpened` signals
- `SpacetimeClient.cs` still has `GetRows` method (Story 3.2)
- `SubscriptionRegistry.cs` still has `Register`, `Unregister`, `Clear`, `ActiveHandles`
- `CacheViewAdapter.cs` still has `SetDb`, `GetRows` (Story 3.2)
- `docs/runtime-boundaries.md` still has `GetRows(`, `SubscriptionApplied`, `HandleId`, `AppliedAt`
- `docs/runtime-boundaries.md` still has `CacheViewAdapter` reference (Story 3.2)

### Architecture Compliance

- `RowChangeType` and `RowChangedEvent` are in `Public/Subscriptions/` — consistent with `SubscriptionHandle` and `SubscriptionAppliedEvent`
- `SpacetimeSdkRowCallbackAdapter` is in `Internal/Platform/DotNet/` — the ONLY zone where `SpacetimeDB.*` may be imported; follows identical placement rule as `SpacetimeSdkConnectionAdapter` and `SpacetimeSdkSubscriptionAdapter`
- `IRowChangeEventSink` is defined in `SpacetimeSdkRowCallbackAdapter.cs` — follows pattern of `IConnectionEventSink` in `SpacetimeSdkConnectionAdapter.cs` and `ISubscriptionEventSink` in `SpacetimeSdkSubscriptionAdapter.cs`
- `SpacetimeConnectionService` implements `IRowChangeEventSink` explicitly — same pattern as `IConnectionEventSink` and `ISubscriptionEventSink` explicit implementations already present
- `RowChangedEvent.OldRow` and `RowChangedEvent.NewRow` are typed as `object?` — no generated-type import needed in `Public/` zone
- Signal naming: `RowChanged` / `RowChangedEventHandler` — follows `SubscriptionApplied` / `SubscriptionAppliedEventHandler` pattern
- Domain event concept: `subscription.row_changed` → `RowChangedEvent` — follows naming convention

### Previous Story Intelligence (Stories 3.1 and 3.2)

**From Story 3.2:**
- `_cacheViewAdapter.SetDb(_adapter.GetDb())` call pattern in `OnConnected` — place `_rowCallbackAdapter.RegisterCallbacks(db, this)` immediately after
- `_adapter.GetDb()` uses `BindingFlags.Public | BindingFlags.Instance` reflection on `_dbConnection` — `RegisterCallbacks` iterates `RemoteTables` properties with the same flags
- No explicit cleanup needed for the cache adapter's SetDb(null) clears GC roots — row callback delegates follow the same automatic cleanup model
- Field-per-feature pattern: `private readonly CacheViewAdapter _cacheViewAdapter = new();` → `private readonly SpacetimeSdkRowCallbackAdapter _rowCallbackAdapter = new();`

**From Story 3.1:**
- `ISubscriptionEventSink` explicit implementations in `SpacetimeConnectionService` — add `IRowChangeEventSink` explicit implementations in the same style
- Expression-tree delegate pattern for SDK boundary crossing: `SpacetimeSdkSubscriptionAdapter.CreateAppliedCallback()` — `TryWireRowEvent()` uses the same `Expression.Lambda(delegateType, body, params).Compile()` approach
- `GodotSignalAdapter.Dispatch(() => EmitSignal(...))` dispatch pattern — reuse for `HandleRowChanged` on `SpacetimeClient`
- Prior test count at end of Story 3.1: 665+ tests; Story 3.2 raised it to 821 — new story adds to this baseline

### Developer Guardrails

**DO NOT:**
- Place `RowChangedEvent.cs` or `RowChangeType.cs` in `Internal/` — they are public SDK types
- Import `SpacetimeDB.*` in `RowChangedEvent.cs`, `SpacetimeConnectionService.cs`, or `SpacetimeClient.cs`
- Wire `OnInternalInsert` or `OnInternalDelete` events — these have `Action<TRow>` (1 param) vs `RowEventHandler` (2 params); the parameter count guard `if (parameters.Length != 2)` intentionally skips them
- Call `_rowCallbackAdapter.RegisterCallbacks(null, ...)` — only call with the live db value; guard with `if (db != null)`
- Add explicit unregistration logic in `Disconnect()` or `ClearCacheView()` — cleanup is automatic via GC once `_adapter.Close()` + `_cacheViewAdapter.SetDb(null)` clear GC roots to the closed RemoteTables
- Expose `IDbConnection`, `RemoteTables`, or any `SpacetimeDB.Types.*` type on `SpacetimeClient` — the public API is `RowChanged` signal + `RowChangedEvent` only

**DO:**
- Call `_rowCallbackAdapter.RegisterCallbacks(db, this)` in `OnConnected` after `_cacheViewAdapter.SetDb(...)` (so both cache and callbacks are wired atomically when a connection opens)
- Guard with `if (db != null)` before calling `RegisterCallbacks` — `GetDb()` returns null defensively when not connected
- Use `Expression.Convert(rowParam, typeof(object))` to box typed row values before passing to `IRowChangeEventSink` — same boxing approach as `CacheViewAdapter.GetRows()` using `.Cast<object>()`
- Keep `TryWireRowEvent` and `TryWireUpdateEvent` as `private static` helpers — no instance state needed
- Verify test isolation: `SpacetimeDB.` must not appear in `RowChangeType.cs`, `RowChangedEvent.cs`, `SpacetimeConnectionService.cs`, or `SpacetimeClient.cs`

### Git Intelligence

Recent commits:
- `feat(story-3.2)` — Added `CacheViewAdapter`, `GetDb()` on connection adapter, `GetRows()` on `SpacetimeClient`; 75 story tests + 821 total tests
- `feat(story-3.1)` — Added subscription adapter, registry, `Subscribe()`, `SubscriptionApplied` signal, `SpacetimeSdkConnectionAdapter.Connection` property
- Pattern: each story commit is one atomic unit covering all files changed

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blockers encountered. Implementation matched story spec exactly.

### Completion Notes List

- Created `RowChangeType.cs` — public enum with Insert, Update, Delete values; no SpacetimeDB.* import
- Created `RowChangedEvent.cs` — public partial class inheriting RefCounted; TableName, ChangeType, OldRow?, NewRow? properties; internal constructor; no SpacetimeDB.* import
- Created `SpacetimeSdkRowCallbackAdapter.cs` — IRowChangeEventSink interface + adapter using Expression trees to wire OnInsert/OnDelete/OnUpdate on generated RemoteTables members via reflection; review hardening added support for field-backed table handles and idempotent re-registration protection across reconnect recovery; uses `using SpacetimeDB;` (Platform/DotNet zone only)
- Updated `SpacetimeConnectionService.cs` — added IRowChangeEventSink to class declaration, _rowCallbackAdapter field, OnRowChanged event, RegisterCallbacks call in OnConnected after SetDb, explicit IRowChangeEventSink implementations routing to OnRowChanged with correct RowChangeType values
- Updated `SpacetimeClient.cs` — added RowChangedEventHandler [Signal], HandleRowChanged method (follows _signalAdapter dispatch pattern), wire/unwire in _EnterTree/_ExitTree
- Updated `docs/runtime-boundaries.md` — added "Row Changes — Observing Live Cache Updates" section with payload table, code example, and SpacetimeSdkRowCallbackAdapter reference
- Created `tests/test_story_3_3_observe_row_level_changes.py` — 117 tests covering all ACs, generated bindings shape checks, reconnect-registration guards, and regression coverage; all pass
- Full suite: 948 tests, 0 regressions (baseline was 821)

### File List

- addons/godot_spacetime/src/Public/Subscriptions/RowChangeType.cs (new)
- addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs (new)
- addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs (new)
- addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs (modified)
- addons/godot_spacetime/src/Public/SpacetimeClient.cs (modified)
- docs/runtime-boundaries.md (modified)
- tests/test_story_3_3_observe_row_level_changes.py (new)
- _bmad-output/implementation-artifacts/tests/test-summary.md (modified — Story 3.3 summary updated to 117 tests / 948 suite tests)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified — story status synced to done)

### Change Log

- feat(story-3.3): Add row-level change observation for subscribed data (2026-04-14)
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 2 High, 2 Medium fixed. Fixes: adapter now wires actual field-backed generated table handles, row callback registration is idempotent across reconnect recovery, Story 3.3 tests now cover generator shape and reconnect guards, and verification artifacts were synced to 117 story tests / 948 suite tests. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 1 additional non-source automation artifact was present under `_bmad-output/story-automator/` beyond the implementation File List.

### Findings Fixed

- HIGH: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs` enumerated only public properties on the generated `RemoteTables` object, but the current SpacetimeDB 2.1.0 generator exposes table handles as public fields (for example `demo/generated/smoke_test/Tables/SmokeTest.g.cs`), so `RowChanged` callbacks would never wire for the actual generated client shape and AC 1 was not satisfied.
- HIGH: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs` re-added delegates every time `OnConnected` fired, so a `Connected -> Degraded -> Connected` recovery path on the same live `Db` object could emit duplicate row-change events after reconnect.
- MEDIUM: `tests/test_story_3_3_observe_row_level_changes.py` only asserted string presence and did not validate the generated field-backed `RemoteTables` shape or reconnect-registration guard, which allowed the non-functional adapter wiring to pass review.
- MEDIUM: Story 3.3 still reported 87 story tests and 918 suite tests and did not record the review-side artifact updates, leaving stale verification evidence in the implementation record.

### Actions Taken

- Updated `SpacetimeSdkRowCallbackAdapter` to inspect public instance fields and properties, dedupe handles by reference, and short-circuit repeated registration for the same `Db` object.
- Added seven Story 3.3 contract tests covering the generated sample `RemoteTables` field shape plus the adapter's idempotent registration guard.
- Re-ran foundation validation, build verification, the story test file, and the full pytest suite after the fix.
- Synced the story completion notes, verification counts, file list, change log, test summary, story status, and sprint-status entry with the reviewed 117-test / 948-suite result.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_3_3_observe_row_level_changes.py`
- `pytest -q`

### Reference Check

- No dedicated Story Context or Epic 3 tech-spec artifact was present; `_bmad-output/planning-artifacts/architecture.md` and the generated sample bindings were used as the applicable planning and implementation references.
- Tech stack validated during review: Godot `4.6.2`, `.NET` `8.0+`, `SpacetimeDB.ClientSDK` `2.1.0`.
- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `docs/runtime-boundaries.md`
- Local reference: `demo/generated/smoke_test/SpacetimeDBClient.g.cs`
- Local reference: `demo/generated/smoke_test/Tables/SmokeTest.g.cs`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
