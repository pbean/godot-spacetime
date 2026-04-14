# Story 2.3: Restore a Previous Session from Persisted Auth State

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Godot developer,
I want a previously persisted session restored when supported,
So that returning users can resume without repeating the full auth flow every time.

## Acceptance Criteria

**AC 1 — Given** a `SpacetimeSettings` with a `TokenStore` configured and no explicit `Credentials`
**When** `Connect()` is called
**Then** the SDK calls `settings.TokenStore.GetTokenAsync()` before opening the connection
**And** if a non-empty token is returned, it is injected via the `WithToken()` path (i.e., set on `settings.Credentials` before `_adapter.Open()`)

**AC 2 — Given** a successful connection using a restored token
**When** the session is established
**Then** the connection behaves identically to an explicit-credentials connection
**And** `_credentialsProvided` is `true`, so `ConnectionAuthState.TokenRestored` is emitted
**And** the server-returned token is stored back via the existing `StoreTokenAsync(token)` call in `OnConnected`

**AC 3 — Given** no stored token in the configured token store (`GetTokenAsync()` returns `null` or empty)
**When** `Connect()` is called
**Then** the SDK falls back cleanly to an anonymous connection
**And** `settings.Credentials` is not mutated, `_credentialsProvided` stays `false`, and no `WithToken()` is injected

**AC 4 — Given** the token store throws an exception during `GetTokenAsync()`
**When** `Connect()` is called
**Then** the exception is caught silently and the connection proceeds without credentials
**And** no corrupted session state is left behind

## Tasks / Subtasks

- [x] Task 1 — Update `SpacetimeConnectionService.Connect()` (AC: 1, 2, 3, 4)
  - [x] After `_tokenStore = settings.TokenStore;` and BEFORE `_credentialsProvided = ...`, insert the token restoration block
  - [x] Condition: `settings.TokenStore != null && string.IsNullOrWhiteSpace(settings.Credentials)`
  - [x] Call: `settings.TokenStore.GetTokenAsync().GetAwaiter().GetResult()` inside a `try/catch (Exception)`
  - [x] If result is non-null and non-whitespace: set `settings.Credentials = stored`
  - [x] Catch block: no-op — token restoration failure is non-fatal
  - [x] The existing `_credentialsProvided = !string.IsNullOrWhiteSpace(settings.Credentials);` line directly after the block now picks up the restored value automatically
  - [x] No other files changed; `WithToken()` injection and `StoreTokenAsync` are already wired from Story 2.2

- [x] Task 2 — Update `docs/runtime-boundaries.md` (AC: 1, 2, 3)
  - [x] In `Auth / Identity` section, after the `Session Identity` paragraph added in 2.2, add a `Session Restoration` paragraph
  - [x] Explain: when `TokenStore` is configured but `Credentials` is empty, `Connect()` calls `GetTokenAsync()` before opening the connection
  - [x] State: a returned token is injected via `WithToken()`; no stored token falls back cleanly to anonymous
  - [x] Note: restoration failure is non-fatal; the connection proceeds without credentials

- [x] Task 3 — Create `tests/test_story_2_3_session_restore.py` (AC: 1–4)
  - [x] Follow the `ROOT`, `_read()`, `_lines()` pattern from `tests/test_story_2_2_auth_session.py` exactly
  - [x] See Dev Notes for full test coverage list

- [x] Task 4 — Verify
  - [x] `python3 scripts/compatibility/validate-foundation.py` → exits 0
  - [x] `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
  - [x] `pytest tests/test_story_2_3_session_restore.py` → all pass
  - [x] `pytest -q` → full suite passes (stories 1.3–2.3 all green)

## Dev Notes

### Scope: What This Story Is and Is Not

**In scope:**
- Inserting pre-connect token restoration into `SpacetimeConnectionService.Connect()` using the existing `ITokenStore.GetTokenAsync()` boundary
- Feeding the restored token through the `settings.Credentials` → `WithToken()` path already established in Story 2.2
- Non-fatal handling when the token store is absent, returns empty, or throws
- `docs/runtime-boundaries.md` documentation update
- New test file `tests/test_story_2_3_session_restore.py`

**Out of scope (belongs to Story 2.4):**
- Distinguishing expired-token `AuthFailed` from network failures
- Recovery guidance for bad stored tokens (clear + re-auth flow)
- `ReconnectPolicy` changes
- `ConnectionAuthStatusPanel` updates — the existing `TokenRestored` and `AuthFailed` labels already cover this story's outcomes

### What Already Exists — DO NOT RECREATE

| Component | Story | File |
|-----------|-------|------|
| `ITokenStore` with `GetTokenAsync()` | 1.3 | `Public/Auth/ITokenStore.cs` |
| `MemoryTokenStore` | 2.1 | `Internal/Auth/MemoryTokenStore.cs` |
| `ProjectSettingsTokenStore` | 2.1 | `Internal/Auth/ProjectSettingsTokenStore.cs` |
| `SpacetimeSettings.Credentials` property | 2.2 | `Public/SpacetimeSettings.cs` |
| `SpacetimeSettings.TokenStore` property | 2.1 | `Public/SpacetimeSettings.cs` |
| `WithToken()` injection in `SpacetimeSdkConnectionAdapter.Open()` | 2.2 | `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` |
| `_credentialsProvided` field and `ConnectionAuthState.TokenRestored` tracking | 2.2 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `StoreTokenAsync(token)` call in `IConnectionEventSink.OnConnected` | 2.1/2.2 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `ConnectionAuthState.TokenRestored` / `AuthFailed` enum values | 2.2 | `Public/Connection/ConnectionAuthState.cs` |
| `ConnectionAuthStatusPanel` with TOKEN RESTORED / AUTH FAILED labels | 2.2 | `Editor/Status/ConnectionAuthStatusPanel.cs` |

### Key Design Decision: Sync Blocking Is Safe Here

Both built-in token stores (`MemoryTokenStore`, `ProjectSettingsTokenStore`) implement `GetTokenAsync()` as `Task.FromResult(...)` — synchronous completion wrapped in a Task. There is no actual async work.

Using `.GetAwaiter().GetResult()` is safe because:
- Godot's main thread has no `SynchronizationContext` that would cause a deadlock
- Both built-in stores complete synchronously
- Custom `ITokenStore` implementations should also complete quickly for session restoration; the contract does not promise long-running behavior

This preserves the synchronous `Connect()` public API on `SpacetimeClient` and `SpacetimeConnectionService` without changes.

### `SpacetimeConnectionService.cs` — Exact Change Required

Insert the token restoration block between `_tokenStore = settings.TokenStore;` and `_credentialsProvided = ...`:

**Before:**
```csharp
_host = settings.Host.Trim();
_database = settings.Database.Trim();
_tokenStore = settings.TokenStore;
_credentialsProvided = !string.IsNullOrWhiteSpace(settings.Credentials);
_reconnectPolicy.Reset();
```

**After:**
```csharp
_host = settings.Host.Trim();
_database = settings.Database.Trim();
_tokenStore = settings.TokenStore;
var restoredCredentials = false;

// Story 2.3: restore a previous session from the token store when no explicit credentials are set
if (settings.TokenStore != null && string.IsNullOrWhiteSpace(settings.Credentials))
{
    try
    {
        var stored = settings.TokenStore.GetTokenAsync().GetAwaiter().GetResult();
        if (!string.IsNullOrWhiteSpace(stored))
        {
            settings.Credentials = stored;
            restoredCredentials = true;
        }
    }
    catch (Exception)
    {
        // Token restoration failure is non-fatal — proceed without credentials
    }
}

_credentialsProvided = !string.IsNullOrWhiteSpace(settings.Credentials);
_reconnectPolicy.Reset();

try
{
    _adapter.Open(settings, this);
}
finally
{
    if (restoredCredentials)
        settings.Credentials = null;
}
```

The restored token still flows through `settings.Credentials` before `_adapter.Open()`, but the review fix clears it in a `finally` after the open attempt so the same `SpacetimeSettings` resource does not retain stale restored credentials.

**Why this works end-to-end:**
1. `settings.TokenStore.GetTokenAsync()` returns the previously stored token (saved by `StoreTokenAsync(token)` in `OnConnected` during a prior session)
2. `settings.Credentials = stored` feeds it into the existing `WithToken()` injection in `SpacetimeSdkConnectionAdapter.Open()`
3. `_credentialsProvided = true` → `ConnectionAuthState.TokenRestored` fires on successful connection (existing behavior)
4. `OnConnected(identity, token)` → `StoreTokenAsync(token)` saves the (potentially refreshed) token for the next session (existing behavior)
5. The transient restored credential is cleared after the open attempt, so `Settings.TokenStore?.ClearTokenAsync()` still resets future connects when the same settings resource is reused
6. If no token found or exception: `settings.Credentials` stays null, `_credentialsProvided = false`, anonymous connection proceeds

### `docs/runtime-boundaries.md` — Required Addition

In the `Auth / Identity` section, after the `Session Identity` paragraph (added in 2.2):

```markdown
**Session Restoration:** When `SpacetimeSettings.TokenStore` is configured and `Credentials` is not explicitly
set, `Connect()` calls `GetTokenAsync()` on the token store before opening the connection. If a non-empty
token is returned, it is injected via `WithToken()` — identical to setting `Credentials` explicitly for that
open call. The restored value is not retained on the settings resource after `Connect()` returns, so clearing
the token store resets future restoration attempts. A
successful restored session emits `ConnectionAuthState.TokenRestored` and surfaces the server identity via
`ConnectionOpenedEvent.Identity`. If no token is stored or the store throws, the connection falls back
cleanly to anonymous without leaving corrupted session state.
```

### Test File Coverage — `tests/test_story_2_3_session_restore.py`

`SpacetimeConnectionService.cs` content tests (restoration logic):
- Contains `GetTokenAsync` reference (token restore call)
- Contains `GetAwaiter().GetResult()` or `GetAwaiter` (sync block on token task)
- Contains `IsNullOrWhiteSpace` check guarding the restore block (does not overwrite explicit credentials)
- Contains restoration wrapped in `try` block (non-fatal failure handling)
- Ensures a restored credential is tracked and cleared after the open attempt so the settings resource does not retain a stale restored token

`docs/runtime-boundaries.md` content tests:
- Contains `Session Restoration` heading or text (new documentation)
- Contains `GetTokenAsync` in the auth/identity section
- Documents that `Connect()` waits synchronously for `GetTokenAsync()` during restoration and that restored tokens are not retained on the settings resource

Regression guards (must still pass from earlier stories):
- `Public/Auth/ITokenStore.cs` still present with `GetTokenAsync`, `StoreTokenAsync`, `ClearTokenAsync`
- `SpacetimeConnectionService.cs` still has `_credentialsProvided`, `_tokenStore`, `OnConnected(`, `StoreTokenAsync`, `WithToken` (indirectly via adapter)
- `SpacetimeSdkConnectionAdapter.cs` still has `WithToken` call
- `Public/Connection/ConnectionAuthState.cs` still has `TokenRestored` and `AuthFailed`
- `ConnectionAuthStatusPanel.cs` still has `TOKEN RESTORED` and `AUTH FAILED` strings
- `tests/test_story_2_2_auth_session.py` → all tests still pass
- `tests/test_story_1_4_adapter_boundary.py` → all tests still pass (isolation not broken)

### File Locations — DO and DO NOT

**DO modify:**
```
addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs  (token restore in Connect)
docs/runtime-boundaries.md                                                     (session restoration doc)
```

**DO create:**
```
tests/test_story_2_3_session_restore.py
```

**DO NOT touch:**
```
addons/godot_spacetime/src/Public/Auth/ITokenStore.cs                        (stable interface)
addons/godot_spacetime/src/Public/SpacetimeSettings.cs                       (Credentials and TokenStore already exist)
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs  (WithToken already wired)
addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs     (no change needed)
addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs            (Story 2.4)
addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs                 (no changes)
addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs        (no changes)
addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs        (TOKEN RESTORED label already correct)
addons/godot_spacetime/src/Public/SpacetimeClient.cs                         (no public API changes)
scripts/compatibility/support-baseline.json                                  (no new files created)
tests/test_story_1_*.py                                                       (regression only)
tests/test_story_2_1_*.py                                                     (regression only)
tests/test_story_2_2_*.py                                                     (regression only)
```

### Cross-Story Awareness

- **Story 2.2** established `settings.Credentials` → `WithToken()` injection, `_credentialsProvided`, `ConnectionAuthState.TokenRestored`, and `StoreTokenAsync(token)` in `OnConnected`. Story 2.3 completes the loop by restoring the stored token into `settings.Credentials` before `Open()`.
- **Story 2.4** (Recover from Failures) will handle the case where the restored token is rejected — distinguishing expired-token `AuthFailed` from network failures, and providing recovery guidance (e.g., "call `ClearTokenAsync()` to reset"). Story 2.3 does not add recovery logic — `AuthFailed` with a restored token falls through the existing error path in `OnConnectError`.
- **Story 2.2 AI-Review item [LOW]:** The panel action text for `AUTH FAILED` reads `"Credentials were rejected. Verify your token or call Settings.TokenStore?.ClearTokenAsync() to reset."` — this remains accurate after the review fix. When a restored token causes `AuthFailed`, calling `ClearTokenAsync()` on the store removes the bad token and the transient injected credential is cleared after `Connect()`, so the next attempt falls back to anonymous cleanly.

### Namespace and Isolation Rules

- Only `Internal/Connection/SpacetimeConnectionService.cs` changes — it already has `using GodotSpacetime.Auth;`
- No new `using SpacetimeDB.*` directives anywhere — the `GetTokenAsync()` call is on `ITokenStore`, which is in `GodotSpacetime.Auth`
- The isolation test in `test_story_1_4_adapter_boundary.py` verifies `SpacetimeDB.` references exist ONLY in `Internal/Platform/DotNet/` — this story does not touch that boundary

### Verification Sequence

Run in order — each must pass before the next:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_2_3_session_restore.py
pytest -q
```

**Troubleshooting:**
- If `dotnet build` fails on `GetAwaiter()`: verify the `try` block uses the correct fully-qualified call chain — `settings.TokenStore.GetTokenAsync().GetAwaiter().GetResult()`; no additional `using` should be required since `Task<T>` is in `System.Threading.Tasks` which is already imported
- If `test_story_1_4_adapter_boundary.py` fails: verify no `SpacetimeDB.` reference was accidentally introduced — the change is inside `SpacetimeConnectionService.cs` which must not reference `SpacetimeDB.*`
- If existing regression tests fail: confirm the token restore block is inserted BETWEEN `_tokenStore = settings.TokenStore;` and `_credentialsProvided = ...`, preserving all other lines in `Connect()` unchanged

### Project Structure Notes

- No new files are added to `addons/` — the change is a single method modification inside `Internal/Connection/SpacetimeConnectionService.cs`
- No `support-baseline.json` update needed (no new tracked files)
- Namespace follows existing pattern: `SpacetimeConnectionService` is in `GodotSpacetime.Runtime.Connection`

### References

- Story 2.3 AC and epic context: [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 2, Story 2.3]
- FR15 (token storage abstraction, session persistence): [Source: `_bmad-output/planning-artifacts/epics.md` — FR map]
- Story 2.2 dev notes — "Out of scope: Story 2.3 will call `settings.TokenStore?.GetTokenAsync()` before `Open()`": [Source: `_bmad-output/implementation-artifacts/spec-2-2-authenticate-a-client-session-through-supported-identity-flows.md` — Scope section]
- Story 2.2 cross-story note — `WithToken()` injection path Story 2.3 will use: [Source: same — Cross-Story Awareness section]
- Story 2.2 AI-Review [LOW] — panel text accuracy after token restoration: [Source: same — Tasks section]
- Architecture auth section — explicit token storage abstraction, opt-in persistence: [Source: `_bmad-output/planning-artifacts/architecture.md` — Authentication & Security]
- `MemoryTokenStore.GetTokenAsync()` returns `Task.FromResult(_token)` (sync): [Source: `addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs`]
- `ProjectSettingsTokenStore.GetTokenAsync()` returns `Task.FromResult(...)` (sync): [Source: `addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs`]
- `SpacetimeConnectionService.Connect()` current implementation: [Source: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`]
- `SpacetimeSettings.Credentials` and `TokenStore` properties: [Source: `addons/godot_spacetime/src/Public/SpacetimeSettings.cs`]
- Test file pattern (`ROOT`, `_read()`, `_lines()`): [Source: `tests/test_story_2_2_auth_session.py`]
- Epic 1 retro — verify third-party APIs, editor verification lessons: [Source: `_bmad-output/implementation-artifacts/epic-1-retro-2026-04-14.md`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Inserted token restoration into `SpacetimeConnectionService.Connect()` between `_tokenStore` assignment and `_credentialsProvided` assignment. Guard condition: `TokenStore != null && IsNullOrWhiteSpace(Credentials)`. Sync block via `.GetAwaiter().GetResult()` remains safe per dev notes (both built-in stores use `Task.FromResult`).
- Senior Developer Review fix: restored credentials are cleared in a `finally` after `_adapter.Open(settings, this)` so a reused `SpacetimeSettings` resource does not retain a stale restored token and `Settings.TokenStore?.ClearTokenAsync()` remains effective.
- Added **Session Restoration** documentation clarifying synchronous restore expectations and that restored tokens are not retained on the settings resource after `Connect()` returns.
- Created and expanded `tests/test_story_2_3_session_restore.py` to 33 tests covering all ACs, regression guards, and the post-review restored-credential cleanup path. All 33 pass. Full suite: 618 passed, 0 failures.

### File List

- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (modified — token restoration block in Connect() with transient restored-credential cleanup)
- `docs/runtime-boundaries.md` (modified — Session Restoration docs plus synchronous restore expectations)
- `tests/test_story_2_3_session_restore.py` (created — contract tests for ACs 1–4, regression guards, and review-fix behavior)

## Change Log

- 2026-04-14: Story implemented — token restoration block added to `SpacetimeConnectionService.Connect()`, Session Restoration paragraph added to `docs/runtime-boundaries.md`, test file `tests/test_story_2_3_session_restore.py` created (29 tests, all green). Full suite: 614 passed.
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 1 High, 2 Medium fixed. Fixes: transient restored credentials are cleared after the open attempt so `Settings.TokenStore?.ClearTokenAsync()` remains effective; runtime-boundaries docs now describe the synchronous restoration path and cleanup behavior; `tests/test_story_2_3_session_restore.py` expanded to 33 tests with the full suite revalidated at 618 passing; story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List.

### Findings Fixed

- HIGH: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` left a restored token in `SpacetimeSettings.Credentials` after `_adapter.Open()`, so clearing the token store would not actually reset a reused settings resource on the next `Connect()` call.
- MEDIUM: `docs/runtime-boundaries.md` still described `ITokenStore` as a purely async/non-blocking boundary even though Story 2.3 now waits synchronously on `GetTokenAsync()` during `Connect()`, which understated the requirement that restore-backed token stores return promptly.
- MEDIUM: the story artifact still claimed `20` story tests and `605` total tests even though the actual review surface already contained `29` story tests and the suite was at `614`, leaving stale verification evidence in the implementation record.

### Actions Taken

- Cleared restored credentials in a `finally` after `_adapter.Open(settings, this)` when the token came from `TokenStore`, preserving the `WithToken()` path without retaining stale credentials on the settings resource.
- Updated `docs/runtime-boundaries.md` to document the synchronous restoration wait and the transient restored-token cleanup behavior.
- Expanded `tests/test_story_2_3_session_restore.py` to 33 tests with regression guards for transient restored-credential cleanup and corrected the story record to match the real verification counts and rerun results.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_2_3_session_restore.py`
- `pytest -q`

### Reference Check

- Local reference: `_bmad-output/planning-artifacts/epics.md`
- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `docs/runtime-boundaries.md`
- Local reference: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`
- Local reference: `tests/test_story_2_3_session_restore.py`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
