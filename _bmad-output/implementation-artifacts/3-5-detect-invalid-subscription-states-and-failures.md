# Story 3.5: Detect Invalid Subscription States and Failures

Status: done

## Story

As a Godot developer,
I want subscription failures and invalid states reported clearly,
so that bad queries or runtime subscription problems are diagnosable and recoverable.

## Acceptance Criteria

1. **Given** an invalid subscription query, rejected subscription, or runtime subscription failure **When** the SDK processes the subscription request or lifecycle update **Then** it surfaces an actionable failure state, event, or message instead of silent desynchronization
2. **Given** a subscription failure event fires **When** gameplay code receives it **Then** valid existing client state is not silently corrupted by the failed subscription change (existing subscriptions remain active and readable)
3. **Given** a subscription failure **When** gameplay code handles the event **Then** the event payload provides enough information for the developer to determine whether retry, query correction, or binding regeneration is the appropriate next step

## Tasks / Subtasks

- [x] Task 1: Create `SubscriptionFailedEvent` payload (AC: 1, 3)
  - [x] 1.1 Create `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs`
  - [x] 1.2 Inherit from `RefCounted` (required for Godot signal params — matches `SubscriptionAppliedEvent` pattern)
  - [x] 1.3 Namespace: `GodotSpacetime.Subscriptions`
  - [x] 1.4 Properties: `public SubscriptionHandle Handle { get; }`, `public string ErrorMessage { get; }`, `public DateTimeOffset FailedAt { get; }`
  - [x] 1.5 Constructor: `internal SubscriptionFailedEvent(SubscriptionHandle handle, Exception error)` — set `Handle = handle`, `ErrorMessage = error.Message`, `FailedAt = DateTimeOffset.UtcNow`
  - [x] 1.6 No `SpacetimeDB.*` imports — this is a public type in the SDK boundary

- [x] Task 2: Add `OnSubscriptionFailed` event to `SpacetimeConnectionService` (AC: 1, 2, 3)
  - [x] 2.1 Add `public event Action<SubscriptionFailedEvent>? OnSubscriptionFailed;` to `SpacetimeConnectionService.cs` — place it after the `OnSubscriptionApplied` event declaration
  - [x] 2.2 In `ISubscriptionEventSink.OnSubscriptionError` implementation: add `OnSubscriptionFailed?.Invoke(new SubscriptionFailedEvent(handle, error));` AFTER the existing cleanup code (`RemovePendingReplacementReferences`, `TryUnsubscribe`, `Unregister`, `handle.Close()`)
  - [x] 2.3 The "Story 3.5 will surface this error..." comment placeholder must be replaced by the actual invocation

- [x] Task 3: Add `SubscriptionFailed` signal to `SpacetimeClient` (AC: 1, 3)
  - [x] 3.1 Add `[Signal] public delegate void SubscriptionFailedEventHandler(SubscriptionFailedEvent e);` after the `SubscriptionApplied` signal declaration
  - [x] 3.2 Subscribe in `_EnterTree()`: `_connectionService.OnSubscriptionFailed += HandleSubscriptionFailed;`
  - [x] 3.3 Unsubscribe in `_ExitTree()`: `_connectionService.OnSubscriptionFailed -= HandleSubscriptionFailed;`
  - [x] 3.4 Add handler method `private void HandleSubscriptionFailed(SubscriptionFailedEvent failedEvent)` — follow the same `GodotSignalAdapter.Dispatch` pattern as `HandleSubscriptionApplied`
  - [x] 3.5 Handler body must use `_signalAdapter.Dispatch(() => EmitSignal(SignalName.SubscriptionFailed, failedEvent))` (deferred dispatch) or direct `EmitSignal` when `_signalAdapter == null` — mirrors `HandleSubscriptionApplied` exactly

- [x] Task 4: Write test file (AC: 1, 2, 3)
  - [x] 4.1 Create `tests/test_story_3_5_detect_invalid_subscription_states_and_failures.py` — follow established test structure (ROOT, `_read()`, `_lines()` helpers)
  - [x] 4.2 Tests for `SubscriptionFailedEvent.cs`: file exists at correct path, namespace `GodotSpacetime.Subscriptions`, class name `SubscriptionFailedEvent`, inherits `RefCounted`, properties `Handle`/`ErrorMessage`/`FailedAt` present, no `SpacetimeDB.*` import
  - [x] 4.3 Tests for `SpacetimeConnectionService.cs`: `OnSubscriptionFailed` event declaration present, `OnSubscriptionError` implementation invokes `OnSubscriptionFailed`, invocation appears after `handle.Close()` (cleanup-first ordering), placeholder comment removed
  - [x] 4.4 Tests for `SpacetimeClient.cs`: `SubscriptionFailedEventHandler` delegate present, `OnSubscriptionFailed` wired in `_EnterTree`, `OnSubscriptionFailed` unwired in `_ExitTree`, `HandleSubscriptionFailed` method present, deferred dispatch via `_signalAdapter` present
  - [x] 4.5 Regression guards: prior story deliverables intact — `SubscriptionApplied` signal, `RowChanged` signal, `GetRows`, `Subscribe`, `Unsubscribe`, `ReplaceSubscription`, `SubscriptionStatus`, `SubscriptionHandle.Status`, `_pendingReplacements`, `TryGetEntry` in registry

## Dev Notes

### Design Intent

Story 3.5 closes the last open leg of Epic 3's subscription lifecycle. Stories 3.1–3.4 established the apply-side event (`SubscriptionApplied`), local cache reads, row-change callbacks, and overlap-first replacement. The error side of the lifecycle exists in the infrastructure (`ISubscriptionEventSink.OnSubscriptionError`, called by reflection from the adapter), but was intentionally left un-surfaced, with a comment noting Story 3.5 would complete it.

The implementation is deliberately minimal: add the event payload type, add the event on the service, add the signal on the client. No new infrastructure is needed — the plumbing is already in place.

### What Already Exists (Do Not Reinvent)

- `ISubscriptionEventSink.OnSubscriptionError(SubscriptionHandle handle, Exception error)` — called by `SpacetimeSdkSubscriptionAdapter` via compiled lambdas (reflection-based); this already fires into `SpacetimeConnectionService.OnSubscriptionError`
- `SpacetimeConnectionService.OnSubscriptionError` implementation is already correct for cleanup (removes pending replacement, best-effort TryUnsubscribe, unregisters, closes handle) — Story 3.5 only adds the external event firing at the END
- `SubscriptionAppliedEvent` in `Public/Subscriptions/SubscriptionAppliedEvent.cs` — use as the direct structural model for `SubscriptionFailedEvent`
- `GodotSignalAdapter` — already handles Godot main-thread dispatch; same pattern as `HandleSubscriptionApplied`
- `LogCategory.Subscription` — already established for subscription events

### Signal and Event Naming Conventions

From the architecture naming rules:
- Domain event: `subscription.failed`
- C# event/signal delegate: `SubscriptionFailedEventHandler`
- Event payload class: `SubscriptionFailedEvent`
- Godot signal: `SubscriptionFailed`

This follows the exact same pattern as:
- Domain: `subscription.applied` → delegate `SubscriptionAppliedEventHandler` → payload `SubscriptionAppliedEvent` → signal `SubscriptionApplied`

### `SubscriptionFailedEvent` Properties

The three properties serve distinct developer needs:
- `Handle` — identifies which subscription failed (developer needs to know if it was a fresh subscribe or a replacement attempt)
- `ErrorMessage` — string from `error.Message` — provides the actionable SDK or server reason (e.g., "Unknown table 'player_stats'" guides the developer toward query correction or regeneration)
- `FailedAt` — timestamp for diagnostics, mirrors `SubscriptionAppliedEvent.AppliedAt`

Do NOT expose the raw `Exception` as a public property on `SubscriptionFailedEvent` — `Exception` cannot be passed as a Godot signal parameter. The `ErrorMessage` string is the correct boundary type.

### Error Ordering in `OnSubscriptionError`

The existing cleanup order in `SpacetimeConnectionService.OnSubscriptionError` must be preserved:
1. `RemovePendingReplacementReferences(handle.HandleId)` — clear pending replacement tracking
2. `_subscriptionAdapter.TryUnsubscribe(entry?.SdkSubscription)` — best-effort SDK close
3. `_subscriptionRegistry.Unregister(handle.HandleId)` — remove from registry
4. `handle.Close()` — mark handle as Closed
5. **NEW:** `OnSubscriptionFailed?.Invoke(new SubscriptionFailedEvent(handle, error))` — fire external event LAST

Firing the event last ensures that when gameplay code observes the event, the handle is already in `Closed` state and the registry is already cleaned up. This makes the event observation semantically consistent with the `SubscriptionApplied` pattern (handle is in `Active`/ready state when `SubscriptionApplied` fires).

### AC 2 — No Corruption of Existing State

This AC is already satisfied by Story 3.4's overlap-first replacement logic (`_pendingReplacements` cleanup). Story 3.5 does NOT need to add additional state protection — the cleanup code in `OnSubscriptionError` already ensures the old (authoritative) subscription is left untouched when a replacement fails. Story 3.5's job here is only to SURFACE the event so gameplay code knows a failure occurred, enabling it to take action without polling.

### File Structure

New files:
- `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs`

Modified files:
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` (Senior Developer Review comment cleanup)
- `docs/runtime-boundaries.md` (Senior Developer Review public-contract docs update)
- `tests/test_story_3_5_detect_invalid_subscription_states_and_failures.py` (new)

### Project Structure Notes

- `SubscriptionFailedEvent.cs` belongs in `Public/Subscriptions/` — mirrors `SubscriptionAppliedEvent.cs` exactly
- No `SpacetimeDB.*` allowed in `Public/Subscriptions/` — the `ErrorMessage` string extraction happens in the service layer (where SpacetimeDB types are still not allowed, but `System.Exception` is fine)
- SDK isolation zone: `Internal/Platform/DotNet/` — no functional Story 3.5 wiring changes were needed here; Senior Developer Review later cleaned up a stale adapter comment after the public failure surface shipped

### Testing Conventions (established in prior stories)

```python
ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]
```

Tests use string-presence checks. Baseline: **1063 tests** (end of Story 3.4). Story 3.5 should add ~50–70 new tests.

### References

- FR22: "Developers can detect subscription failures or invalid subscription states." [Source: `_bmad-output/planning-artifacts/epics.md#FR22`]
- Architecture error model: "Typed status/events for gameplay code; exceptions remain infrastructure-level signals rather than the primary gameplay contract" [Source: `_bmad-output/planning-artifacts/architecture.md#API & Communication Patterns`]
- Architecture naming: "Event payload objects end with `Event`" / "Error objects end with `Error`" — `SubscriptionFailedEvent` is an event payload (ends with `Event`), not a standalone error class [Source: `_bmad-output/planning-artifacts/architecture.md#Naming Conventions`]
- Story 3.4 note: "Story 3.5 will surface this error to gameplay code via a dedicated signal." [Source: `_bmad-output/implementation-artifacts/3-4-replace-active-subscriptions-safely-during-runtime.md#OnSubscriptionError`]
- `SubscriptionAppliedEvent` pattern: `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs`
- `HandleSubscriptionApplied` dispatch pattern: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- `GodotSignalAdapter.Dispatch` usage: `addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs`
- SDK isolation boundary: `docs/runtime-boundaries.md`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented `SubscriptionFailedEvent.cs` in `Public/Subscriptions/` mirroring `SubscriptionAppliedEvent` exactly — `public partial class` extending `RefCounted` with `Handle`, `ErrorMessage`, and `FailedAt` get-only properties; internal constructor extracts `error.Message` to keep `Exception` off the public/Godot boundary.
- Added `public event Action<SubscriptionFailedEvent>? OnSubscriptionFailed` to `SpacetimeConnectionService` after `OnSubscriptionApplied`. In `OnSubscriptionError`, fired the event last (after `RemovePendingReplacementReferences` → `TryUnsubscribe` → `Unregister` → `handle.Close()`) to ensure handle is already `Closed` and registry is already clean when gameplay code observes the event.
- Replaced the Story 3.5 placeholder comment in `SpacetimeConnectionService.OnSubscriptionError` with the actual `OnSubscriptionFailed?.Invoke(...)` call.
- Added `[Signal] SubscriptionFailedEventHandler` to `SpacetimeClient` after `SubscriptionAppliedEventHandler`; wired/unwired `HandleSubscriptionFailed` in `_EnterTree`/`_ExitTree`; implemented handler using identical `_signalAdapter.Dispatch` pattern as `HandleSubscriptionApplied` with null-guard fallback.
- Updated stale Story 3.1 regression test (`test_connection_service_on_subscription_error_is_noop_stub`) that checked for the now-removed placeholder comment — replaced assertion to verify `OnSubscriptionFailed` is present (Story 3.5 complete).
- Senior Developer Review auto-fix: documented `SubscriptionFailed` in the public runtime-boundaries contract and `SpacetimeClient` XML docs so the shipped SDK surface now explains the failure event, actionable `ErrorMessage`, and overlap-first replacement failure behavior.
- Senior Developer Review auto-fix: removed the stale Story 3.5 future-tense comment from `SpacetimeSdkSubscriptionAdapter.TryUnsubscribe()` and expanded Story 3.5 regression tests to lock the new docs/comment behavior in place.
- Validation after review fixes: foundation check passed, `dotnet build` passed, Story 3.5 + Story 3.1 contract suite passed (159 tests), and the full pytest suite passed (1148 tests). Story 3.5 coverage now stands at 80 contract tests.

### File List

- `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs` (new)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (modified)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (modified — public XML docs updated to describe the failure path)
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` (modified — stale Story 3.5 future-tense comment removed during review)
- `docs/runtime-boundaries.md` (modified — `SubscriptionFailedEvent` and failure-path contract documented)
- `tests/test_story_3_5_detect_invalid_subscription_states_and_failures.py` (new)
- `tests/test_story_3_1_subscription_apply.py` (modified — stale placeholder-comment assertion updated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — story status synced to done)

## Change Log

- 2026-04-14: Implemented Story 3.5 — `SubscriptionFailedEvent`, `OnSubscriptionFailed`, `SubscriptionFailed` signal wiring, and Story 3.5 regression coverage added for invalid subscription states and lifecycle failures.
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 0 High, 3 Medium fixed. Fixes: public SDK docs now cover `SubscriptionFailed` / `SubscriptionFailedEvent`, `SpacetimeSdkSubscriptionAdapter` no longer carries a stale Story 3.5 future-tense comment, and Story 3.5 regression tests now lock the review fixes. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 2 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List (`_bmad-output/story-automator/orchestration-1-20260414-184146.md` and `_bmad-output/implementation-artifacts/tests/test-summary.md`).

### Findings Fixed

- MEDIUM: `docs/runtime-boundaries.md` and the public XML docs in `addons/godot_spacetime/src/Public/SpacetimeClient.cs` still described only the apply-side subscription path, so the shipped public contract omitted the new `SubscriptionFailed` / `SubscriptionFailedEvent` surface and the overlap-first replacement failure semantics required by AC 1 through AC 3.
- MEDIUM: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` still contained a stale comment claiming Story 3.5 would add the failure surface in the future, which was now factually wrong and misleading for maintainers reading the adapter boundary.
- MEDIUM: `tests/test_story_3_5_detect_invalid_subscription_states_and_failures.py` did not guard the new public docs or stale adapter comment, so the review fixes could regress without the story contract suite detecting it.

### Actions Taken

- Updated `docs/runtime-boundaries.md` to document `SubscriptionFailed`, `SubscriptionFailedEvent`, the actionable `ErrorMessage` payload, and the guarantee that a failed replacement leaves the authoritative cache state readable.
- Updated `SpacetimeClient` XML docs so the top-level SDK entry point documents the failure event and replacement-failure behavior alongside the apply path.
- Removed the stale Story 3.5 future-tense comment from `SpacetimeSdkSubscriptionAdapter.TryUnsubscribe()`.
- Added four Story 3.5 regression tests covering the public docs and adapter comment cleanup.
- Re-ran foundation validation, `dotnet build`, the Story 3.5 + Story 3.1 contract suite, and the full pytest suite after applying the fixes.
- Synced the story status and sprint-status entry to `done`.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln`
- `pytest -q tests/test_story_3_5_detect_invalid_subscription_states_and_failures.py tests/test_story_3_1_subscription_apply.py`
- `pytest -q`

### Reference Check

- No dedicated Story Context or Epic 3 tech-spec artifact was present; `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/epics.md`, and `docs/runtime-boundaries.md` were used as the applicable planning and standards references.
- Tech stack validated during review: Godot `.NET` SDK `4.6.1`, Godot product `4.6.2`, `.NET` `8.0+`, `SpacetimeDB.ClientSDK` `2.1.0`.
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
