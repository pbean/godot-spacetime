# Story 3.4: Replace Active Subscriptions Safely During Runtime

Status: done

## Story

As a Godot developer,
I want to change or replace active subscriptions during runtime,
so that scene transitions and gameplay state changes can evolve live queries safely.

## Acceptance Criteria

1. **Given** one or more active subscriptions **When** `ReplaceSubscription(oldHandle, newQueries)` is called during an active `Connected` session **Then** the SDK supports the transition without requiring a full client restart
2. **Given** a replacement subscription is in progress **When** the new subscription is being synchronized **Then** the previous subscription set remains authoritative until the replacement set reaches a synchronized state or fails explicitly
3. **Given** a replacement subscription has been applied **When** gameplay code observes subscription state **Then** the updated subscription state is observable through the same `SubscriptionApplied` signal path with the new `SubscriptionHandle`
4. **Given** a caller holds a `SubscriptionHandle` **When** `Unsubscribe(handle)` is called **Then** the SDK closes that subscription scope and the handle transitions to a terminal status
5. **Given** `ReplaceSubscription` is called but the new subscription fails **When** the error arrives **Then** the old subscription is NOT unsubscribed — it remains active and the caller can retry

## Tasks / Subtasks

- [x] Task 1: Add `SubscriptionStatus` enum and `Status` to `SubscriptionHandle` (AC: 3, 4)
  - [x] 1.1 Create `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs` — public enum with values: `Active`, `Superseded`, `Closed`
  - [x] 1.2 Add `public SubscriptionStatus Status { get; private set; }` to `SubscriptionHandle` (initialized to `Active`)
  - [x] 1.3 Add `internal void Supersede()` → sets `Status = Superseded`
  - [x] 1.4 Add `internal void Close()` → sets `Status = Closed`
  - [x] 1.5 No `SpacetimeDB.*` import allowed in `Public/Subscriptions/` — status type must be runtime-neutral

- [x] Task 2: Enhance `SpacetimeSdkSubscriptionAdapter` to capture and expose SDK subscription lifecycle (AC: 1, 2, 4)
  - [x] 2.1 Change `Subscribe()` return type from `void` to `object?` — capture return value of `subscribeMethod.Invoke(builder, new object[] { querySqls })`
  - [x] 2.2 Add `internal bool TryUnsubscribe(object sdkSubscription)` method:
    - Use reflection to find a public instance method named `Unsubscribe` or `Close` with zero parameters on `sdkSubscription.GetType()`
    - If found: invoke it and return `true`
    - If not found: return `false` (graceful degradation — handle is marked Closed regardless)
  - [x] 2.3 Existing `ISubscriptionEventSink` interface — no changes needed
  - [x] 2.4 Keep all SDK type references strictly inside this adapter — no `SpacetimeDB.*` leaks

- [x] Task 3: Update `SubscriptionRegistry` to store SDK subscription objects (AC: 1, 2, 4)
  - [x] 3.1 Create internal record/class `SubscriptionEntry` inside `SubscriptionRegistry.cs` (or as its own internal file): `internal sealed record SubscriptionEntry(SubscriptionHandle Handle, object? SdkSubscription)`
  - [x] 3.2 Change `_handles` backing store from `Dictionary<Guid, SubscriptionHandle>` to `Dictionary<Guid, SubscriptionEntry>`
  - [x] 3.3 Update `Register(SubscriptionHandle handle, object? sdkSubscription)` signature — add `sdkSubscription` param
  - [x] 3.4 Update `Unregister(Guid)` and `ActiveHandles` to return `IReadOnlyCollection<SubscriptionEntry>`
  - [x] 3.5 Add `TryGetEntry(Guid handleId, out SubscriptionEntry? entry)` for lookup
  - [x] 3.6 Update `SpacetimeConnectionService` call sites for the new signature

- [x] Task 4: Add `Unsubscribe` and `ReplaceSubscription` to `SpacetimeConnectionService` (AC: 1, 2, 3, 4, 5)
  - [x] 4.1 Add `public void Unsubscribe(SubscriptionHandle handle)`:
    - Guard: throw `ArgumentNullException.ThrowIfNull(handle)`
    - Guard: throw `InvalidOperationException` if `CurrentStatus.State != Connected`
    - Look up `SubscriptionEntry` in registry via `handle.HandleId`
    - Call `_subscriptionAdapter.TryUnsubscribe(entry.SdkSubscription)` (if SDK object exists)
    - Call `handle.Close()`
    - Call `_subscriptionRegistry.Unregister(handle.HandleId)`
  - [x] 4.2 Add `public SubscriptionHandle ReplaceSubscription(SubscriptionHandle oldHandle, string[] newQueries)` — overlap-first:
    - Guard: `ArgumentNullException.ThrowIfNull(oldHandle)` and `ArgumentNullException.ThrowIfNull(newQueries)`
    - Guard: throw `InvalidOperationException` if `CurrentStatus.State != Connected`
    - Guard: throw `InvalidOperationException` if `oldHandle.Status != SubscriptionStatus.Active`
    - Create `newHandle = new SubscriptionHandle()`; register it: `_subscriptionRegistry.Register(newHandle, null)` (SDK subscription stored after Subscribe call)
    - Wire replacement hook: intercept the `ISubscriptionEventSink.OnSubscriptionApplied` and `OnSubscriptionError` paths so that when `newHandle` is applied → unsubscribe `oldHandle` (overlap-first close); when `newHandle` errors → do NOT close `oldHandle`
    - Call `_subscriptionAdapter.Subscribe(connection, newQueries, sink, newHandle)` — capture returned SDK object and update the registry entry for `newHandle`
    - Return `newHandle`
  - [x] 4.3 Replacement hook strategy: add private `Dictionary<Guid, Guid>` field `_pendingReplacements` mapping `newHandleId → oldHandleId`; in `ISubscriptionEventSink.OnSubscriptionApplied`: after normal path, check if `handle.HandleId` is in `_pendingReplacements` and call `Unsubscribe(oldHandle)` then remove from map; in `OnSubscriptionError`: remove from `_pendingReplacements` without touching old handle
  - [x] 4.4 Update `Subscribe()` to capture SDK subscription return value: `var sdkSub = _subscriptionAdapter.Subscribe(connection, querySqls, this, handle)` — then update registry: `_subscriptionRegistry.UpdateSdkSubscription(handle.HandleId, sdkSub)`
    - Add `UpdateSdkSubscription(Guid, object?)` to `SubscriptionRegistry`

- [x] Task 5: Expose `Unsubscribe` and `ReplaceSubscription` on `SpacetimeClient` (AC: 1, 3, 4)
  - [x] 5.1 Add `public void Unsubscribe(SubscriptionHandle handle)` → delegates to `_connectionService.Unsubscribe(handle)` with same try/catch pattern as `Subscribe()`
  - [x] 5.2 Add `public SubscriptionHandle ReplaceSubscription(SubscriptionHandle oldHandle, string[] newQueries)` → delegates to `_connectionService.ReplaceSubscription(oldHandle, newQueries)` with try/catch for `ArgumentException` and `InvalidOperationException`

- [x] Task 6: Write test file (AC: 1, 2, 3, 4, 5)
  - [x] 6.1 Create `tests/test_story_3_4_replace_active_subscriptions_safely_during_runtime.py` — follow established test structure (ROOT, `_read()`, `_lines()` helpers)
  - [x] 6.2 Tests for `SubscriptionStatus.cs`: file exists, namespace, public enum, Active/Superseded/Closed values, no SpacetimeDB reference
  - [x] 6.3 Tests for `SubscriptionHandle.cs`: `Status` property present, `Supersede()`/`Close()` internal methods present, initialized to `Active`
  - [x] 6.4 Tests for `SpacetimeSdkSubscriptionAdapter.cs`: `Subscribe()` returns object (not void), `TryUnsubscribe(object)` method present, reflection-based unsubscribe lookup, no SDK types leak out
  - [x] 6.5 Tests for `SubscriptionRegistry.cs`: `SubscriptionEntry` type present, stores `Handle` + `SdkSubscription`, `TryGetEntry` method, `UpdateSdkSubscription` method
  - [x] 6.6 Tests for `SpacetimeConnectionService.cs`: `Unsubscribe(handle)` method present, `ReplaceSubscription(oldHandle, queries)` method present, `_pendingReplacements` field or equivalent, ISubscriptionEventSink checks pending replacements
  - [x] 6.7 Tests for `SpacetimeClient.cs`: `Unsubscribe(handle)` method present, `ReplaceSubscription(oldHandle, queries)` method present
  - [x] 6.8 Regression guards: prior story deliverables intact (SubscriptionApplied signal, RowChanged signal, GetRows, Subscribe, CacheViewAdapter.SetDb, SpacetimeSdkRowCallbackAdapter)

## Dev Notes

### Design Intent

This story implements **overlap-first subscription replacement** — the critical invariant is that the old subscription's data remains in the local cache until the new subscription is confirmed applied by the server. This prevents the gameplay code from ever observing an empty or partial cache during a scene transition.

The flow is:
```
[Gameplay] → ReplaceSubscription(oldHandle, newQueries)
               ↓
        Apply new subscription (Subscribe internally)
               ↓
        Server confirms new subscription applied
               ↓
        Unsubscribe old subscription (SDK-level close, if available)
        oldHandle.Supersede()
               ↓
        SubscriptionApplied signal fires with newHandle
               ↓
[Gameplay] receives newHandle, observes new data
```

If the new subscription fails before being applied, the old subscription is intentionally NOT closed — it remains active, data remains authoritative, gameplay code is unaffected.

### SDK Subscription Return Value Discovery

The key uncertainty is what `SubscriptionBuilder.Subscribe(string[])` returns in SpacetimeDB SDK 2.1.0. The adapter must discover this via reflection:

```csharp
// In SpacetimeSdkSubscriptionAdapter.Subscribe():
var result = subscribeMethod.Invoke(builder, new object[] { querySqls });
// result may be:
//   - null / void result → SDK doesn't return a lifecycle object → TryUnsubscribe returns false (graceful)
//   - an object with Unsubscribe() or Close() method → capture and use for explicit close
return result;  // pass back to service, store in registry
```

If the SDK returns `void`, `Invoke()` returns `null` — `TryUnsubscribe(null)` must handle null gracefully (return false). In this case, the overlap-first pattern still works correctly: old handle gets `Supersede()`'d after new subscription applies, the `SubscriptionRegistry` is cleaned up, and the SDK eventually GC's the old subscription. No behavioral gap for the gameplay code.

### Pending Replacement Tracking

The `_pendingReplacements` map lives on `SpacetimeConnectionService` (not the adapter or registry). It maps `newHandleId → oldHandleId` and is consulted inside `ISubscriptionEventSink.OnSubscriptionApplied`:

```csharp
void ISubscriptionEventSink.OnSubscriptionApplied(SubscriptionHandle handle)
{
    if (_pendingReplacements.TryGetValue(handle.HandleId, out var oldHandleId))
    {
        _pendingReplacements.Remove(handle.HandleId);
        // Overlap-first close: new subscription is live, now close the old one
        if (_subscriptionRegistry.TryGetEntry(oldHandleId, out var oldEntry))
        {
            _subscriptionAdapter.TryUnsubscribe(oldEntry.SdkSubscription);
            oldEntry.Handle.Supersede();
            _subscriptionRegistry.Unregister(oldHandleId);
        }
    }
    OnSubscriptionApplied?.Invoke(new SubscriptionAppliedEvent(handle));
}
```

And in `ISubscriptionEventSink.OnSubscriptionError`:
```csharp
void ISubscriptionEventSink.OnSubscriptionError(SubscriptionHandle handle, Exception error)
{
    // Remove pending replacement entry WITHOUT touching old handle — old remains active
    _pendingReplacements.Remove(handle.HandleId);
    _subscriptionRegistry.Unregister(handle.HandleId);
    handle.Close();
    // Story 3.5 will surface this error to gameplay code
}
```

### SubscriptionRegistry Signature Change

`Register()` currently takes only a `SubscriptionHandle`. Story 3.4 needs to store the SDK subscription object too. The cleanest approach is a two-step pattern: `Register(handle)` then `UpdateSdkSubscription(handleId, sdkSub)` — because the SDK subscription object isn't available until after `Subscribe()` returns (which happens after `Register()` is called in the guard-then-register-then-subscribe flow). Alternatively, restructure to Register-after-Subscribe, but be careful not to create a race between Register and the synchronous AppliedCallback that could theoretically fire before Register completes in some SDK implementations.

Safest approach: keep `Register(handle)` as is, add `UpdateSdkSubscription(Guid, object?)` as a separate method called immediately after Subscribe returns.

### SubscriptionHandle.Status — NOT a Godot Signal

`SubscriptionHandle.Status` is a C# property. Do NOT add a Godot `[Signal]` for status changes on the handle itself — status transitions are internal bookkeeping, not gameplay events. The observable event for gameplay is `SubscriptionApplied` (new handle) which already fires through `SpacetimeClient`.

### No Connectivity Guard on Unsubscribe

While `Subscribe()` and `ReplaceSubscription()` require `Connected` state, `Unsubscribe()` should be more lenient — if called while `Disconnected`, it should simply mark the handle `Closed` and remove from registry without attempting an SDK call. This prevents errors during scene teardown when the connection may have already dropped.

Suggested guard in `Unsubscribe()`:
```csharp
public void Unsubscribe(SubscriptionHandle handle)
{
    ArgumentNullException.ThrowIfNull(handle);
    if (handle.Status == SubscriptionStatus.Closed) return;  // idempotent

    if (CurrentStatus.State == ConnectionState.Connected &&
        _subscriptionRegistry.TryGetEntry(handle.HandleId, out var entry))
    {
        _subscriptionAdapter.TryUnsubscribe(entry?.SdkSubscription);
    }
    handle.Close();
    _subscriptionRegistry.Unregister(handle.HandleId);
}
```

### File Structure Alignment

New files follow established conventions:
- `Public/Subscriptions/SubscriptionStatus.cs` — mirrors `RowChangeType.cs` pattern (public enum, GodotSpacetime.Subscriptions namespace, no SDK imports)

Modified files:
- `Public/Subscriptions/SubscriptionHandle.cs` — add `Status` property, `internal Supersede()`/`Close()`
- `Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` — return object?, add `TryUnsubscribe`
- `Internal/Subscriptions/SubscriptionRegistry.cs` — add `SubscriptionEntry`, `TryGetEntry`, `UpdateSdkSubscription`
- `Internal/Connection/SpacetimeConnectionService.cs` — add `Unsubscribe`, `ReplaceSubscription`, `_pendingReplacements`
- `Public/SpacetimeClient.cs` — expose `Unsubscribe`, `ReplaceSubscription`
- `tests/test_story_3_4_replace_active_subscriptions_safely_during_runtime.py` — new test file

### Project Structure Notes

- `SubscriptionStatus.cs` belongs in `Public/Subscriptions/` — it is a public type exposed on `SubscriptionHandle`
- `SubscriptionEntry` can be a private nested type inside `SubscriptionRegistry.cs` or an `internal` file at `Internal/Subscriptions/SubscriptionEntry.cs` — either is acceptable; prefer nesting to keep it co-located with its consumer
- All SpacetimeDB SDK reflection happens exclusively in `SpacetimeSdkSubscriptionAdapter` — the `TryUnsubscribe` method takes `object?` so the service layer never touches SDK types directly
- `_pendingReplacements` is a `Dictionary<Guid, Guid>` field on `SpacetimeConnectionService` — no new class needed

### Testing Conventions (from 3.3 established patterns)

```python
ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]
```

Tests use string-presence checks for correctness. For story 3.4 specifically, add contract-level tests:
- `TryGetEntry` method present in `SubscriptionRegistry` (prevents regression of tracking gap)
- `_pendingReplacements` or equivalent key structure present in `SpacetimeConnectionService` (verifies overlap-first is wired)
- `SubscriptionStatus.Active` present in `SubscriptionHandle` (verifies handle tracks state)

Baseline: **948 passing tests** (end of Story 3.3). Story 3.4 should add ~90–120 new tests.

### References

- FR21: "Developers can change or replace active subscriptions during application runtime." [Source: `_bmad-output/planning-artifacts/prd.md#Functional Requirements`]
- Architecture: "Subscription model: scoped subscriptions with overlap-first replacement to reduce cache gaps and dropped updates" [Source: `_bmad-output/planning-artifacts/architecture.md#API & Communication Patterns`]
- Story 3.1 established `ISubscriptionEventSink`, `SubscriptionHandle`, `SubscriptionRegistry`, `SpacetimeSdkSubscriptionAdapter` [Source: `_bmad-output/implementation-artifacts/3-1-apply-a-subscription-and-receive-initial-synchronized-state.md`]
- Story 3.3 established idempotent registration guard pattern (HashSet<object>) and review finding that SDK 2.1.0 uses fields (not just properties) [Source: `_bmad-output/implementation-artifacts/3-3-observe-row-level-changes-for-subscribed-data.md`]
- SDK isolation zone: `Internal/Platform/DotNet/` is the ONLY location where `SpacetimeDB.*` imports are permitted [Source: `docs/runtime-boundaries.md`]
- `GodotSignalAdapter.Dispatch(() => EmitSignal(...))` is the required pattern for deferred signal dispatch [Source: `addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented overlap-first subscription replacement as specified in Dev Notes. `_pendingReplacements` (Dictionary<Guid,Guid>) on SpacetimeConnectionService maps newHandleId → oldHandleId; old handle is Supersede()'d and unregistered only after new subscription reaches applied state.
- `SpacetimeSdkSubscriptionAdapter.Subscribe()` now returns `object?` — the raw SDK subscription object captured via `subscribeMethod.Invoke()`. `TryUnsubscribe(object?)` uses reflection to find `Unsubscribe()` or `Close()` zero-param methods on the returned object, degrades gracefully on null or SDK close failures, and never blocks local handle teardown.
- `SubscriptionRegistry` refactored to store `SubscriptionEntry` records (Handle + SdkSubscription). `TryGetEntry` and `UpdateSdkSubscription` added. `ActiveHandles` now returns `IReadOnlyCollection<SubscriptionEntry>`, and disconnect teardown closes tracked handles before clearing the registry so stale session handles do not remain `Active`.
- `SubscriptionStatus` is a plain C# enum (no Godot, no SpacetimeDB imports) — mirrors RowChangeType.cs pattern. `SubscriptionHandle` gains `Status` property (public), `Supersede()` and `Close()` (internal).
- `Unsubscribe()` is lenient with connection state: SDK close only attempted when Connected; handle always marked Closed and removed from registry. Idempotent for already-Closed handles, and pending replacement bookkeeping is canceled when a handle is explicitly unsubscribed.
- Error path (AC 5): `OnSubscriptionError` removes the failed new handle from `_pendingReplacements`, best-effort closes its SDK subscription object, and leaves the old subscription authoritative. `ReplaceSubscription()` now rejects overlapping in-flight replacements so only the currently authoritative handle can be swapped.
- Created `tests/test_story_3_4_replace_active_subscriptions_safely_during_runtime.py` — 110 tests covering all ACs, best-effort unsubscribe cleanup, disconnect teardown, replacement guardrails, and regression coverage; all pass.
- Full suite: 1063 tests, 0 regressions (baseline was 948).

### File List

- addons/godot_spacetime/src/Public/Subscriptions/SubscriptionStatus.cs (new)
- addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs (modified)
- addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs (modified)
- addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs (modified)
- addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs (modified)
- addons/godot_spacetime/src/Public/SpacetimeClient.cs (modified)
- tests/test_story_3_4_replace_active_subscriptions_safely_during_runtime.py (new)
- _bmad-output/implementation-artifacts/tests/test-summary.md (modified — Story 3.4 summary updated to 110 tests / 1063 suite tests)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified — story status synced to done)

## Change Log

- 2026-04-14: Implemented Story 3.4 — overlap-first subscription replacement, Unsubscribe/ReplaceSubscription APIs, SubscriptionStatus enum, SubscriptionHandle lifecycle methods, SubscriptionRegistry/SubscriptionEntry refactor, SpacetimeSdkSubscriptionAdapter SDK object capture and TryUnsubscribe.
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 1 High, 4 Medium fixed. Fixes: SDK unsubscribe cleanup is now best-effort so handle state transitions always complete, disconnect teardown now closes tracked handles and clears pending replacements, overlap-first replacement rejects concurrent swaps, and verification artifacts were synced to 110 story tests / 1063 suite tests. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 1 additional non-source automation artifact was present under `_bmad-output/story-automator/` beyond the implementation File List.

### Findings Fixed

- HIGH: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` let reflection invocation failures from SDK `Unsubscribe()` / `Close()` escape, so `Unsubscribe()` and overlap-first replacement completion could abort before `handle.Close()`, `handle.Supersede()`, and registry cleanup ran, leaving stale `Active` handles and breaking AC 2 through AC 4.
- MEDIUM: `addons/godot_spacetime/src/Internal/Subscriptions/SubscriptionRegistry.cs` and `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` only dropped registry state on disconnect teardown, so tracked handles could survive dead sessions with `Status == Active` and `_pendingReplacements` could leak into the next connection lifecycle.
- MEDIUM: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` did not cancel pending replacement bookkeeping when `Unsubscribe(handle)` was called, so canceling an in-flight replacement could still let a late `OnSubscriptionApplied` callback supersede the old authoritative handle unexpectedly.
- MEDIUM: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` accepted `ReplaceSubscription()` calls for handles already participating in an in-flight replacement, allowing overlapping swap requests with ambiguous authoritative state and duplicate apply paths.
- MEDIUM: Story 3.4 still reported stale verification evidence in the implementation record and test summary, so the reviewed code and the recorded validation counts diverged.

### Actions Taken

- Made `TryUnsubscribe()` best-effort, so SDK close failures now return `false` instead of blocking local handle cleanup and replacement completion.
- Closed tracked handles during registry clear, cleared `_pendingReplacements` on disconnect teardown, and canceled pending replacement bookkeeping from `Unsubscribe(handle)`.
- Guarded `ReplaceSubscription()` so only a currently authoritative handle without another replacement already in flight can be replaced.
- Added six Story 3.4 contract tests covering best-effort unsubscribe failures, disconnect teardown cleanup, pending replacement cancellation, and overlapping replacement guards.
- Re-ran foundation validation, build verification, the story test file, and the full pytest suite after the fix.
- Synced the story completion notes, file list, change log, test summary, story status, and sprint-status entry with the reviewed 110-test / 1063-suite result.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `python3 -m pytest tests/test_story_3_4_replace_active_subscriptions_safely_during_runtime.py -q`
- `python3 -m pytest -q`

### Reference Check

- No dedicated Story Context or Epic 3 tech-spec artifact was present; `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/prd.md`, and `docs/runtime-boundaries.md` were used as the applicable planning and standards references.
- Tech stack validated during review: Godot `.NET` support baseline `4.6.1`, Godot product `4.6.2`, `.NET` `8.0+`, `SpacetimeDB.ClientSDK` `2.1.0`.
- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `_bmad-output/planning-artifacts/prd.md`
- Local reference: `docs/runtime-boundaries.md`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
