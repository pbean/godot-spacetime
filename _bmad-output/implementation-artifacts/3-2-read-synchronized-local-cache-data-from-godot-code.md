# Story 3.2: Read Synchronized Local Cache Data from Godot Code

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Godot developer,
I want to access synchronized local client state from Godot code,
So that gameplay systems can read live game data without issuing custom network queries.

## Acceptance Criteria

**AC 1 — Given** a successfully applied subscription with synchronized state
**When** gameplay code calls `SpacetimeClient.GetRows("TableName")`
**Then** it receives all locally cached rows for that table as `IEnumerable<object>`
**And** each row can be cast to the generated row type (e.g., `(SpacetimeDB.Types.Player)row`)
**And** the call returns an empty sequence (not an exception) when the cache is empty

**AC 2 — Given** gameplay code uses `SpacetimeClient.GetRows()`
**Then** that read path does not require any direct call to transport-layer types outside the SDK
**And** gameplay code does not need to hold or manage a reference to `IDbConnection`

**AC 3 — Given** cache access is mediated by `SpacetimeClient.GetRows()`
**Then** gameplay code cannot mutate the cache or transport state through this path
**And** the SDK boundary (`SpacetimeClient`) is the only required import for cache reads

## Tasks / Subtasks

- [x] Task 1 — Add `GetDb()` to `SpacetimeSdkConnectionAdapter.cs` (AC: 1, 2)
  - [x] Add `internal object? GetDb()` method using reflection to get the `Db` property from `_dbConnection`
  - [x] Use `_dbConnection?.GetType().GetProperty("Db", BindingFlags.Public | BindingFlags.Instance)?.GetValue(_dbConnection)`
  - [x] Add XML doc comment (see Dev Notes for exact text)

- [x] Task 2 — Create `Internal/Cache/CacheViewAdapter.cs` (AC: 1, 2, 3)
  - [x] Create `addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs`
  - [x] Namespace: `GodotSpacetime.Runtime.Cache`
  - [x] `internal sealed class CacheViewAdapter` with `SetDb(object? db)` and `GetRows(string tableName)` methods
  - [x] `GetRows` uses `ArgumentNullException.ThrowIfNull(tableName)`, returns `[]` when `_db == null`
  - [x] `GetRows` uses reflection to find table property on `_db`, casts to `IEnumerable` and calls `.Cast<object>()`
  - [x] See Dev Notes for exact implementation

- [x] Task 3 — Update `SpacetimeConnectionService.cs` (AC: 1, 2, 3)
  - [x] Add `using GodotSpacetime.Runtime.Cache;` and `using System.Collections.Generic;`
  - [x] Add `private readonly CacheViewAdapter _cacheViewAdapter = new();` field
  - [x] In `IConnectionEventSink.OnConnected`: add `_cacheViewAdapter.SetDb(_adapter.GetDb());` after `_reconnectPolicy.Reset();`
  - [x] In `Disconnect(string description)`: add `_cacheViewAdapter.SetDb(null);` after `_subscriptionRegistry.Clear();`
  - [x] Add `public IEnumerable<object> GetRows(string tableName) => _cacheViewAdapter.GetRows(tableName);`

- [x] Task 4 — Update `SpacetimeClient.cs` (AC: 1, 2, 3)
  - [x] Add `using System.Collections.Generic;`
  - [x] Add `public IEnumerable<object> GetRows(string tableName)` that delegates to `_connectionService.GetRows(tableName)`

- [x] Task 5 — Update `docs/runtime-boundaries.md` (AC: 1, 2, 3)
  - [x] Replace the existing stub Cache section with full documentation (see Dev Notes for exact text)
  - [x] Document `GetRows()` usage, `IEnumerable<object>` casting pattern, and empty-sequence guard

- [x] Task 6 — Create `tests/test_story_3_2_read_synchronized_cache.py` (AC: 1–3)
  - [x] Follow `ROOT`, `_read()`, `_lines()` pattern from `tests/test_story_3_1_subscription_apply.py`
  - [x] See Dev Notes for full test coverage list

- [x] Task 7 — Verify
  - [x] `python3 scripts/compatibility/validate-foundation.py` → exits 0
  - [x] `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
  - [x] `pytest tests/test_story_3_2_read_synchronized_cache.py` → all pass
  - [x] `pytest -q` → full suite passes (all prior story tests green)

## Dev Notes

### Scope: What This Story Is and Is Not

**In scope:**
- `CacheViewAdapter` in `Internal/Cache/` — wraps the generated `RemoteTables` object and provides `GetRows(string tableName)` via reflection
- `SpacetimeSdkConnectionAdapter.GetDb()` — reflection accessor for the generated `Db` property on the active `IDbConnection`
- `SpacetimeConnectionService._cacheViewAdapter` field + `GetRows()` delegation method
- `SpacetimeConnectionService` wiring: `SetDb()` called in `OnConnected` and cleared in `Disconnect()`
- `SpacetimeClient.GetRows(string tableName)` — the public cache-access entry point
- `docs/runtime-boundaries.md` Cache section update
- New test file `tests/test_story_3_2_read_synchronized_cache.py`

**Out of scope:**
- Row-level change callbacks (insert/update/delete) — Story 3.3
- Subscription replacement — Story 3.4
- Subscription failure recovery — Story 3.5
- Reducer invocation — Epic 4
- `SubscriptionQuerySet.cs` — Story 3.4
- Typed `GetRows<T>()` generic overload — not in AC; add only if explicitly required
- Any caching of the `IEnumerable<object>` result — consumers call `GetRows()` per frame if needed

### What Already Exists — DO NOT RECREATE

| Component | Story | File |
|-----------|-------|------|
| `SpacetimeSdkConnectionAdapter` with `Connection` property | 3.1 | `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` |
| `SpacetimeSdkSubscriptionAdapter` with Expression-tree pattern | 3.1 | `Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` |
| `SpacetimeConnectionService` implementing `IConnectionEventSink`, `ISubscriptionEventSink` | 3.1 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `SubscriptionRegistry` with `Register`, `Unregister`, `Clear`, `ActiveHandles` | 3.1 | `Internal/Subscriptions/SubscriptionRegistry.cs` |
| `SpacetimeClient` with `Subscribe()`, `SubscriptionApplied` signal, `HandleSubscriptionApplied` | 3.1 | `Public/SpacetimeClient.cs` |
| `SubscriptionHandle` with `HandleId` (Guid), internal ctor | 3.1 | `Public/Subscriptions/SubscriptionHandle.cs` |
| `SubscriptionAppliedEvent` with `Handle`, `AppliedAt` | 3.1 | `Public/Subscriptions/SubscriptionAppliedEvent.cs` |
| All auth infrastructure | 2.1–2.4 | `Internal/Auth/`, `Public/Auth/`, `Public/Connection/` |

### `SpacetimeSdkConnectionAdapter.cs` — Single Addition

Add this method after the existing `internal IDbConnection? Connection => _dbConnection;` property:

```csharp
/// <summary>
/// Gets the generated <c>RemoteTables</c> object (the <c>Db</c> property of the active
/// <c>IDbConnection</c>) for use by the <c>CacheViewAdapter</c>.
/// Returns <c>null</c> when not connected or when the generated <c>DbConnection</c> type
/// does not expose a <c>Db</c> property.
/// </summary>
internal object? GetDb() =>
    _dbConnection?.GetType()
        .GetProperty("Db", BindingFlags.Public | BindingFlags.Instance)
        ?.GetValue(_dbConnection);
```

**Why reflection:** The `Db` property is on the generated concrete `DbConnection` type (e.g., `SpacetimeDB.Types.DbConnection`), NOT on the `IDbConnection` interface. Same isolation pattern as `SubscriptionBuilder()` in `SpacetimeSdkSubscriptionAdapter`.

No other changes to `SpacetimeSdkConnectionAdapter.cs` in this story.

### `Internal/Cache/CacheViewAdapter.cs` — New File

```csharp
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

namespace GodotSpacetime.Runtime.Cache;

/// <summary>
/// Provides read access to the synchronized local client cache through the generated RemoteTables object.
///
/// This adapter wraps the generated <c>Db</c> property of the active <c>IDbConnection</c>
/// and exposes it through a reflection-based enumeration path. Gameplay code must not access
/// the underlying transport state directly — use <c>SpacetimeClient.GetRows()</c> instead.
///
/// See <c>docs/runtime-boundaries.md</c> — "Cache — Reading Synchronized Local State" for usage.
/// </summary>
internal sealed class CacheViewAdapter
{
    private object? _db;

    /// <summary>
    /// Sets the generated <c>RemoteTables</c> object to use for cache reads.
    /// Called by <see cref="GodotSpacetime.Runtime.Connection.SpacetimeConnectionService"/>
    /// when a connection is established (<c>OnConnected</c>) and cleared on disconnect.
    /// </summary>
    internal void SetDb(object? db) => _db = db;

    /// <summary>
    /// Returns all rows currently in the local client cache for the specified table name.
    /// The table name must match the generated property name on the <c>RemoteTables</c> type
    /// (case-sensitive, PascalCase — e.g., <c>"Player"</c>, <c>"Monster"</c>).
    ///
    /// Returns an empty sequence when no connection is active or the subscription cache is empty.
    /// Each returned object can be cast to the corresponding generated row type.
    /// </summary>
    /// <exception cref="InvalidOperationException">
    /// Thrown when the table name does not exist in the generated <c>RemoteTables</c> type.
    /// Ensure bindings are generated for a module that declares the requested table.
    /// </exception>
    internal IEnumerable<object> GetRows(string tableName)
    {
        ArgumentNullException.ThrowIfNull(tableName);

        if (_db == null)
            return [];

        var tableProperty = _db.GetType()
            .GetProperty(tableName, BindingFlags.Public | BindingFlags.Instance)
            ?? throw new InvalidOperationException(
                $"Table '{tableName}' not found in the generated RemoteTables. " +
                $"Ensure bindings are generated for a module that declares a table named '{tableName}'.");

        var tableHandle = tableProperty.GetValue(_db);
        if (tableHandle is null)
            return [];

        if (tableHandle is IEnumerable enumerable)
            return enumerable.Cast<object>();

        throw new InvalidOperationException(
            $"Table handle for '{tableName}' does not implement IEnumerable. " +
            $"Ensure bindings are generated from a compatible SpacetimeDB module version.");
    }
}
```

**Key points:**
- Does NOT reference `SpacetimeDB.*` anywhere — isolation test will verify
- Uses `System.Collections.IEnumerable` (non-generic) to enumerate table handles without referencing generated types
- `.Cast<object>()` from `System.Linq` converts `IEnumerable` → `IEnumerable<object>`
- Returns `[]` (empty array expression) when `_db` is null — no exception
- Empty collection path: same `[]` return when `tableHandle` is null
- `InvalidOperationException` (not `ArgumentException`) when table not found — consistent with `Subscribe()` guard pattern

### `SpacetimeConnectionService.cs` — Required Changes

**New using directives** (add at top):
```csharp
using System.Collections.Generic;
using GodotSpacetime.Runtime.Cache;
```

**New field** (add after `_subscriptionRegistry` field):
```csharp
private readonly CacheViewAdapter _cacheViewAdapter = new();
```

**`IConnectionEventSink.OnConnected` addition** (add after `_reconnectPolicy.Reset();`):
```csharp
_cacheViewAdapter.SetDb(_adapter.GetDb());
```

Full updated `OnConnected` beginning for clarity:
```csharp
void IConnectionEventSink.OnConnected(string identity, string token)
{
    _reconnectPolicy.Reset();
    _cacheViewAdapter.SetDb(_adapter.GetDb());   // ← NEW: wire cache view on connect
    if (_tokenStore != null)
    { ... }
```

**`Disconnect(string description)` addition** (add after `_subscriptionRegistry.Clear();`):
```csharp
_cacheViewAdapter.SetDb(null);   // ← NEW: clear cache view on disconnect
```

Full updated `Disconnect` for clarity:
```csharp
private void Disconnect(string description)
{
    _subscriptionRegistry.Clear();
    _cacheViewAdapter.SetDb(null);   // ← NEW
    _adapter.Close();
    _reconnectPolicy.Reset();
    ...
}
```

**New `GetRows` method** (add after `Subscribe()` public method):
```csharp
public IEnumerable<object> GetRows(string tableName) => _cacheViewAdapter.GetRows(tableName);
```

### `SpacetimeClient.cs` — Required Changes

**New using directive** (add at top):
```csharp
using System.Collections.Generic;
```

**New public method** (add after `Subscribe()` public method):
```csharp
public IEnumerable<object> GetRows(string tableName) =>
    _connectionService.GetRows(tableName);
```

### `docs/runtime-boundaries.md` — Required Update

**Replace** the existing stub Cache section (lines 105–109):
```markdown
### Cache

The **Cache** is the local synchronized read model populated by active subscriptions. Reads from the cache are always local (no network round-trip). The cache is populated and kept current by the SDK runtime; you read from it through generated binding types specific to your module's schema.

There is no direct public cache type in the core SDK — cache access is surfaced through **Generated Bindings** (see below).
```

**With** this full section:

```markdown
### Cache — Reading Synchronized Local State

The **Cache** is the local synchronized read model populated by active subscriptions. Reads from the cache are always local — no network round-trip. The cache is populated and kept current by the SDK runtime; you read from it after the `SubscriptionApplied` signal fires.

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
```

### Test File Coverage — `tests/test_story_3_2_read_synchronized_cache.py`

#### `CacheViewAdapter.cs` content tests (AC: 1, 2, 3)
- File exists at `Internal/Cache/CacheViewAdapter.cs`
- Namespace is `GodotSpacetime.Runtime.Cache`
- Contains `internal sealed class CacheViewAdapter`
- Has `SetDb` method
- Has `GetRows` method
- `GetRows` signature accepts `string tableName`
- Uses `IEnumerable` (non-generic, from `System.Collections`)
- Uses `.Cast<object>()`
- Uses `ArgumentNullException.ThrowIfNull`
- Does NOT contain `SpacetimeDB.` string (isolation boundary)

#### `SpacetimeSdkConnectionAdapter.cs` content tests (AC: 1)
- Has `GetDb` method
- Method uses `GetProperty("Db"` via reflection
- Has XML doc comment mentioning `RemoteTables`
- Still has `Connection` property (regression guard from Story 3.1)

#### `SpacetimeConnectionService.cs` content tests (AC: 1, 2, 3)
- Contains `_cacheViewAdapter` field
- Contains `CacheViewAdapter` type reference
- Imports `GodotSpacetime.Runtime.Cache`
- Imports `System.Collections.Generic`
- Contains `_cacheViewAdapter.SetDb(_adapter.GetDb())` call
- Contains `_cacheViewAdapter.SetDb(null)` call (disconnect clear)
- Has `GetRows` method delegating to `_cacheViewAdapter`
- Does NOT contain `SpacetimeDB.` (isolation boundary)

#### `SpacetimeClient.cs` content tests (AC: 1, 2, 3)
- Has `public IEnumerable<object> GetRows(` method signature
- Imports `System.Collections.Generic`
- Delegates to `_connectionService.GetRows(`
- Does NOT contain `SpacetimeDB.` (isolation boundary)

#### `docs/runtime-boundaries.md` content tests (AC: 1, 2, 3)
- Contains `GetRows` reference
- Contains cast example (`(SpacetimeDB.Types.` or equivalent casting description)
- Contains `IEnumerable<object>` reference
- Contains `SubscriptionApplied` reference (timing guidance)
- Contains `CacheViewAdapter` reference
- Contains empty-sequence guard explanation

#### Regression guards — prior story deliverables must still pass
- `SpacetimeSdkConnectionAdapter.cs` still has `Connection` property
- `SpacetimeSdkConnectionAdapter.cs` still has `Open`, `FrameTick`, `Close` methods
- `SpacetimeConnectionService.cs` still has `Subscribe`, `OnSubscriptionApplied`, `_subscriptionRegistry`
- `SpacetimeConnectionService.cs` still has `_subscriptionRegistry.Clear()` in `Disconnect`
- `SpacetimeClient.cs` still has `Subscribe`, `SubscriptionAppliedEventHandler`, `HandleSubscriptionApplied`
- `SpacetimeClient.cs` still has `ConnectionStateChanged`, `ConnectionOpened` signals
- `SubscriptionRegistry.cs` still has `Register`, `Unregister`, `Clear`, `ActiveHandles`
- `docs/runtime-boundaries.md` still has `Subscribe(`, `SubscriptionApplied`, `HandleId`, `AppliedAt`

### Architecture Compliance

- `CacheViewAdapter` is in `Internal/Cache/` exactly as specified in the architecture directory structure
- `CacheViewAdapter` namespace follows convention: `GodotSpacetime.Runtime.Cache`
- `CacheViewAdapter` does NOT reference `SpacetimeDB.*` — the `Db` property access happens via reflection, not typed import
- `GetDb()` is placed in `SpacetimeSdkConnectionAdapter` (in `Platform/DotNet/`) where SpacetimeDB imports are allowed
- `SpacetimeClient.GetRows()` is the only public cache-access path — gameplay code does NOT get a reference to `IDbConnection`, `RemoteTables`, or any transport type
- `SpacetimeConnectionService` remains the sole owner of `DbConnection` state — `_cacheViewAdapter` is wired through the service, not exposed directly
- `System.Collections.IEnumerable` + `System.Linq.Cast<object>()` is the correct cross-boundary enumeration strategy — no generated type import needed in `CacheViewAdapter`

### Previous Story Intelligence (Story 3.1)

From Story 3.1 implementation:

- **Reflection pattern confirmed:** `SpacetimeSdkSubscriptionAdapter` uses `connection.GetType().GetMethod("SubscriptionBuilder", ...)` — `GetDb()` uses the same `GetProperty("Db", ...)` pattern
- **No `SpacetimeDB.*` outside Platform/DotNet:** `SpacetimeConnectionService` and `SpacetimeClient` pass the connection via `var` type inference — `CacheViewAdapter` uses `object?` to stay isolated
- **Field-per-feature pattern:** `_subscriptionAdapter`, `_subscriptionRegistry` added as `private readonly` fields in `SpacetimeConnectionService` — `_cacheViewAdapter` follows the same pattern
- **Disconnect cleanup:** `_subscriptionRegistry.Clear()` was added before `_adapter.Close()` in `Disconnect(string)` — `_cacheViewAdapter.SetDb(null)` goes immediately after `_subscriptionRegistry.Clear()`
- **OnConnected wiring:** auth token store wiring happened after `_reconnectPolicy.Reset()` — `_cacheViewAdapter.SetDb()` also goes after `_reconnectPolicy.Reset()`, before the token store block
- **Test pattern:** `ROOT`, `_read(rel)`, `_lines(rel)` helpers; test method names `test_<component>_<assertion>()`
- **Prior test count:** 665+ tests pass at end of Story 3.1; new story tests add to this baseline

### Git Intelligence

Recent commits confirm:
- `feat(story-3.1)` — Added subscription adapter, subscription registry, wired `SpacetimeClient.Subscribe()` and `SubscriptionApplied` signal; `SpacetimeSdkConnectionAdapter.Connection` property added
- `feat(story-2.4)` — `ConnectionAuthState`, token recovery routing — no overlap with Story 3.2
- Pattern: each story commit is one atomic unit covering all files changed

### Developer Guardrails

**DO NOT:**
- Place `CacheViewAdapter` in `Internal/Platform/DotNet/` — the architecture puts it in `Internal/Cache/`
- Add `using SpacetimeDB;` to `CacheViewAdapter.cs` — it accesses `Db` via reflection only
- Expose `IDbConnection` or `RemoteTables` on `SpacetimeClient` — the public API is `GetRows(string tableName)` only
- Add `GetDb()` to `IDbConnection` or try to modify the interface — it is from the SpacetimeDB SDK
- Call `_adapter.GetDb()` before the connection is open — `GetDb()` returns `null` safely when `_dbConnection` is null
- Use `System.Collections.Generic.IEnumerable<T>` in `CacheViewAdapter.GetRows()` — use non-generic `System.Collections.IEnumerable` for `tableHandle is IEnumerable` check, then `.Cast<object>()` via Linq

**DO:**
- Call `_cacheViewAdapter.SetDb(_adapter.GetDb())` in `OnConnected` (the `IConnectionEventSink` explicit implementation in `SpacetimeConnectionService`)
- Call `_cacheViewAdapter.SetDb(null)` in `Disconnect(string description)` after `_subscriptionRegistry.Clear()`
- Return `[]` (not `throw`) when `_db == null` — matches AC 1 empty-sequence guard
- Use `BindingFlags.Public | BindingFlags.Instance` in the reflection calls to match the generated type's property visibility
- Verify test isolation: `SpacetimeDB.` must not appear in `CacheViewAdapter.cs`, `SpacetimeConnectionService.cs`, or `SpacetimeClient.cs`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_No blockers encountered._

### Completion Notes List

- Created `Internal/Cache/CacheViewAdapter.cs` — reflection-based `GetRows(string tableName)` returning `IEnumerable<object>`; no `SpacetimeDB.*` imports; isolation boundary enforced
- Added `GetDb()` to `SpacetimeSdkConnectionAdapter` — reflection on `_dbConnection` for `Db` property; same pattern as `SubscriptionBuilder()`
- Updated `SpacetimeConnectionService` — added `_cacheViewAdapter` field, wired `SetDb` in `OnConnected`, cleared the cache view on failed/lost connection paths, and added `GetRows()` delegation
- Updated `SpacetimeClient` and `docs/runtime-boundaries.md` — public guidance now points to `GetRows()` as the cache-read path and calls out generated row casts explicitly
- Created `tests/test_story_3_2_read_synchronized_cache.py` — 75 tests covering all ACs, connection-loss cleanup, documentation contracts, and regression guards
- Senior Developer Review (AI) auto-fixed stale cache cleanup on disconnect-error paths and synced the story/test artifacts with the reviewed result
- Build: 0 errors, 0 warnings; `validate-foundation.py` exits 0; 821/821 tests pass

### File List

- `addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs` (new)
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` (modified)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (modified)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (modified)
- `docs/runtime-boundaries.md` (modified)
- `tests/test_story_3_2_read_synchronized_cache.py` (new)
- `_bmad-output/implementation-artifacts/tests/test-summary.md` (modified — Story 3.2 summary updated to 75 tests / 821 suite tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — story status synced to done)

### Change Log

- 2026-04-14: Story 3.2 implementation complete — added `CacheViewAdapter`, `GetDb()`, `GetRows()` cache-read path through `SpacetimeClient`; 54 new tests; 800 total tests green
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 1 High, 3 Medium fixed. Fixes: cache view now clears on failed and lost connection paths; public docs now consistently point to `GetRows()`; Story 3.2 verification updated to 75 story tests and 821 total passing. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 1 additional non-source automation artifact was present under `_bmad-output/story-automator/` beyond the implementation File List.

### Findings Fixed

- HIGH: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` only cleared the cache view during explicit `Disconnect()`, so failed or lost connections could leave `GetRows()` backed by stale `Db` state while the story docs promised empty reads when the connection was not active.
- MEDIUM: Story 3.2 had no regression coverage for failed/lost connection cleanup, so the stale-cache path could return after refactors without tripping tests.
- MEDIUM: `addons/godot_spacetime/src/Public/SpacetimeClient.cs` and `docs/runtime-boundaries.md` still described cache reads as “via generated bindings” instead of the new `GetRows()` boundary, leaving the public guidance inconsistent with AC 2 and AC 3.
- MEDIUM: The story artifact still reported 54 story tests and 800 suite tests and did not record the review-side artifact updates, leaving stale verification evidence in the implementation record.

### Actions Taken

- Added cache-view cleanup on failed connect and disconnect-error paths, while preserving the existing explicit-disconnect cleanup path.
- Added four regression tests covering cache invalidation on connection loss plus the public `GetRows()` documentation path.
- Updated `SpacetimeClient` XML docs and `docs/runtime-boundaries.md` so the supported cache-read path is consistently `GetRows()` followed by generated row casts.
- Synced the story completion notes, file list, change log, test summary, story status, and sprint-status entry with the reviewed 75-test / 821-suite result.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_3_2_read_synchronized_cache.py`
- `pytest -q`

### Reference Check

- No dedicated Story Context or Epic 3 tech-spec artifact was present; `_bmad-output/planning-artifacts/epics.md` and `_bmad-output/planning-artifacts/architecture.md` were used as the applicable planning references.
- Tech stack validated during review: Godot `4.6.2`, `.NET` `8.0+`, `SpacetimeDB.ClientSDK` `2.1.0`.
- Local reference: `docs/runtime-boundaries.md`
- Local reference: `demo/generated/smoke_test/SpacetimeDBClient.g.cs`
- Local reference: `demo/generated/smoke_test/Tables/SmokeTest.g.cs`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
