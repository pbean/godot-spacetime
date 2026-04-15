# Story 2.4: Recover from Common Session and Identity Failures

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Godot developer,
I want recoverable auth and session failures surfaced predictably,
So that my game can prompt for re-authentication, retry, or clear bad state without guesswork.

## Acceptance Criteria

**AC 1 — Given** an expired token, rejected identity, or interrupted authenticated session
**When** the SDK encounters the failure during connection or restoration
**Then** it exposes a recoverable failure state or event that gameplay code can handle explicitly

**AC 2 — Given** a stored token that was rejected by the server
**When** `AuthFailed`-equivalent failure occurs after token restoration
**Then** the failure state distinguishes a restored-token rejection from an explicit-credential rejection
**And** the recovery surface points developers explicitly to `Settings.TokenStore?.ClearTokenAsync()` as the correct reset path

**AC 3 — Given** any auth or session failure
**When** the failure is observed via `ConnectionStatus.AuthState`
**Then** recoverable operational failures are distinguishable from unrecoverable programming faults
**And** unrecoverable programming faults (e.g., invalid settings) remain thrown exceptions, not `ConnectionStatus` events

**AC 4 — Given** the `ConnectionAuthStatusPanel` in the editor
**When** an auth failure occurs (either `AuthFailed` or `TokenExpired`)
**Then** the panel identifies the likely cause and the recommended next step (retry, re-auth, or token clearing)
**And** the panel surfaces text that is actionable and specific — not just a generic "failed" label

## Tasks / Subtasks

- [x] Task 1 — Add `TokenExpired` to `ConnectionAuthState` (AC: 2, 3, 4)
  - [x] Add `TokenExpired` enum value with XML doc comment after `AuthFailed`
  - [x] Comment must specify: "A previously stored token was rejected. Clear the token store and reconnect."

- [x] Task 2 — Update `SpacetimeConnectionService.cs` (AC: 1, 2, 3)
  - [x] Add `_restoredFromStore` instance field (`private bool _restoredFromStore;`)
  - [x] In `Connect()`, after the restoration block, assign `_restoredFromStore = restoredCredentials;`
  - [x] In `OnConnectError()`, within the `Connecting` branch: check `_restoredFromStore` before `_credentialsProvided`
  - [x] If `_restoredFromStore` is true: emit `ConnectionState.Disconnected` with `ConnectionAuthState.TokenExpired`
    - Description: `"DISCONNECTED — stored token was rejected: {error.Message}"`
  - [x] If `_restoredFromStore` is false and `_credentialsProvided`: emit existing `AuthFailed` (no change to that path)
  - [x] Existing anonymous connect-fail path (`!_credentialsProvided`) is unchanged

- [x] Task 3 — Update `ConnectionAuthStatusPanel.cs` (AC: 4)
  - [x] Add `ConnectionAuthState.TokenExpired` arm to the switch expression in `SetAuthStatus`
  - [x] Label: `"TOKEN EXPIRED"`
  - [x] Action: `"Stored token was rejected. Call Settings.TokenStore?.ClearTokenAsync() to remove the invalid token, then reconnect."`
  - [x] Insert the `TokenExpired` arm before the `AuthFailed` arm in the switch

- [x] Task 4 — Update `docs/runtime-boundaries.md` (AC: 1, 2, 3)
  - [x] In the `ConnectionAuthState` table, add the `TokenExpired` row after `AuthFailed`
  - [x] After the `Session Restoration` paragraph, add a `Failure Recovery` paragraph (see Dev Notes for exact text)

- [x] Task 5 — Create `tests/test_story_2_4_failure_recovery.py` (AC: 1–4)
  - [x] Follow the `ROOT`, `_read()`, `_lines()` pattern from `tests/test_story_2_3_session_restore.py` exactly
  - [x] See Dev Notes for full test coverage list

- [x] Task 6 — Verify
  - [x] `python3 scripts/compatibility/validate-foundation.py` → exits 0
  - [x] `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
  - [x] `pytest tests/test_story_2_4_failure_recovery.py` → all pass (47/47)
  - [x] `pytest -q` → full suite passes (665/665 green)

## Dev Notes

### Scope: What This Story Is and Is Not

**In scope:**
- Adding `ConnectionAuthState.TokenExpired` to distinguish restored-token rejection from explicit-credential rejection
- Tracking `_restoredFromStore` in `SpacetimeConnectionService` so `OnConnectError` can emit the correct auth state
- Updating `ConnectionAuthStatusPanel.SetAuthStatus` to handle `TokenExpired` with specific recovery text
- `docs/runtime-boundaries.md` documentation update (auth state table + Failure Recovery paragraph)
- New test file `tests/test_story_2_4_failure_recovery.py`

**Out of scope:**
- Retrying after auth failure — `ReconnectPolicy.TryBeginRetry` is NOT called for auth failures (only for `Connected`/`Degraded` disconnects). This is intentional: a rejected identity cannot recover via retry without new credentials.
- Modifying `ReconnectPolicy` logic — the policy already does not apply to auth failures (confirmed from `OnConnectError` which only calls `HandleDisconnectError` after a non-`Connecting` state)
- Auth failure during degraded reconnect — if a token expires mid-session (state goes `Connected → Degraded` → reconnect fails with auth error), `HandleDisconnectError` is called which currently transitions to `Disconnected` without auth state. This is accepted edge-case behavior; Story 2.4 covers the primary `Connecting` path only
- New public API on `SpacetimeClient` — `Settings.TokenStore.ClearTokenAsync()` is the existing and documented recovery path; no new SDK surface is needed
- Changing `SpacetimeSettings.Credentials` handling — token clearing resets future `Connect()` calls via the existing guard in `Connect()`

### What Already Exists — DO NOT RECREATE

| Component | Story | File |
|-----------|-------|------|
| `ConnectionAuthState` enum (`None`, `AuthRequired`, `TokenRestored`, `AuthFailed`) | 2.2 | `Public/Connection/ConnectionAuthState.cs` |
| `ConnectionStatus` with `.AuthState` | 2.2 | `Public/Connection/ConnectionStatus.cs` |
| `ConnectionStateMachine.Transition(state, description, authState)` | 2.2 | `Internal/Connection/ConnectionStateMachine.cs` |
| `SpacetimeConnectionService._credentialsProvided` | 2.2 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `SpacetimeConnectionService.OnConnectError` with `AuthFailed` on creds-provided | 2.2 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `SpacetimeConnectionService._tokenStore` | 2.1 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `SpacetimeConnectionService.Connect()` — token restoration block with `restoredCredentials` local | 2.3 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `ReconnectPolicy` — `TryBeginRetry`, `Reset`, `MaxAttempts` | 1.9 | `Internal/Connection/ReconnectPolicy.cs` |
| `ConnectionAuthStatusPanel.SetAuthStatus` with `AuthFailed` / `TokenRestored` arms | 2.2 | `Editor/Status/ConnectionAuthStatusPanel.cs` |
| `ITokenStore.ClearTokenAsync()` on the public interface | 1.3 | `Public/Auth/ITokenStore.cs` |
| `MemoryTokenStore` / `ProjectSettingsTokenStore` | 2.1 | `Internal/Auth/` |
| `docs/runtime-boundaries.md` — `ConnectionAuthState` table, `Session Restoration` paragraph | 2.3 | `docs/runtime-boundaries.md` |

### `ConnectionAuthState.cs` — Exact Change Required

Add after `AuthFailed`:

```csharp
/// <summary>
/// A previously stored token was rejected by the server.
/// Clear the token store via <c>Settings.TokenStore?.ClearTokenAsync()</c> and reconnect to establish a new session.
/// </summary>
TokenExpired,
```

Final enum order: `None`, `AuthRequired`, `TokenRestored`, `AuthFailed`, `TokenExpired`.

### `SpacetimeConnectionService.cs` — Exact Changes Required

**Field addition** (after the existing `private bool _credentialsProvided;` field):

```csharp
private bool _restoredFromStore;
```

**In `Connect()`,** after the existing restoration block (and the `_credentialsProvided = ...` line), add:

```csharp
_restoredFromStore = restoredCredentials;
```

The full relevant block (showing context — do not change anything else):

```csharp
// ... existing restoration block (Story 2.3) ...

_credentialsProvided = !string.IsNullOrWhiteSpace(settings.Credentials);
_restoredFromStore = restoredCredentials;   // ← NEW: track source of credentials for failure routing
_reconnectPolicy.Reset();
```

**In `OnConnectError()`,** replace the existing `Connecting`-branch block:

**Before:**
```csharp
if (CurrentStatus.State == ConnectionState.Connecting)
{
    if (_credentialsProvided)
    {
        _stateMachine.Transition(
            ConnectionState.Disconnected,
            $"DISCONNECTED — authentication failed: {error.Message}",
            ConnectionAuthState.AuthFailed
        );
    }
    else
    {
        _stateMachine.Transition(
            ConnectionState.Disconnected,
            $"DISCONNECTED — failed to connect: {error.Message}"
        );
    }
    return;
}
```

**After:**
```csharp
if (CurrentStatus.State == ConnectionState.Connecting)
{
    if (_restoredFromStore)
    {
        _stateMachine.Transition(
            ConnectionState.Disconnected,
            $"DISCONNECTED — stored token was rejected: {error.Message}",
            ConnectionAuthState.TokenExpired
        );
    }
    else if (_credentialsProvided)
    {
        _stateMachine.Transition(
            ConnectionState.Disconnected,
            $"DISCONNECTED — authentication failed: {error.Message}",
            ConnectionAuthState.AuthFailed
        );
    }
    else
    {
        _stateMachine.Transition(
            ConnectionState.Disconnected,
            $"DISCONNECTED — failed to connect: {error.Message}"
        );
    }
    return;
}
```

**Why `_restoredFromStore` takes priority over `_credentialsProvided`:**
When a token is restored, both `_restoredFromStore = true` and `_credentialsProvided = true`. The `_restoredFromStore` check must come first so the specific recovery guidance ("clear token store") wins over the generic guidance ("verify credentials").

### `ConnectionAuthStatusPanel.cs` — Exact Change Required

In `SetAuthStatus`, insert the `TokenExpired` arm before the `AuthFailed` arm:

**Before:**
```csharp
var (label, action) = authState switch
{
    ConnectionAuthState.TokenRestored =>
        ("TOKEN RESTORED", "Session authenticated with provided credentials."),
    ConnectionAuthState.AuthFailed =>
        ("AUTH FAILED", "Credentials were rejected. Verify your token or call Settings.TokenStore?.ClearTokenAsync() to reset."),
    ConnectionAuthState.AuthRequired =>
        ("AUTH REQUIRED", "Configure Credentials on SpacetimeSettings to connect as an identified user."),
    _ when connState == ConnectionState.Connected =>
        ("ANONYMOUS", "Connected without credentials. No persistent identity."),
    _ =>
        ("AUTH REQUIRED", "Configure Credentials or a TokenStore before connecting as an identified user."),
};
```

**After:**
```csharp
var (label, action) = authState switch
{
    ConnectionAuthState.TokenRestored =>
        ("TOKEN RESTORED", "Session authenticated with provided credentials."),
    ConnectionAuthState.TokenExpired =>
        ("TOKEN EXPIRED", "Stored token was rejected. Call Settings.TokenStore?.ClearTokenAsync() to remove the invalid token, then reconnect."),
    ConnectionAuthState.AuthFailed =>
        ("AUTH FAILED", "Credentials were rejected. Verify your token or call Settings.TokenStore?.ClearTokenAsync() to reset."),
    ConnectionAuthState.AuthRequired =>
        ("AUTH REQUIRED", "Configure Credentials on SpacetimeSettings to connect as an identified user."),
    _ when connState == ConnectionState.Connected =>
        ("ANONYMOUS", "Connected without credentials. No persistent identity."),
    _ =>
        ("AUTH REQUIRED", "Configure Credentials or a TokenStore before connecting as an identified user."),
};
```

Note: the `#if TOOLS` wrapper and `[Tool]` attribute on this class are unchanged. All other methods in the file are unchanged.

### `docs/runtime-boundaries.md` — Required Additions

**1. Update the `ConnectionAuthState` table** (in the "Auth / Identity" section). The table currently ends with `AuthFailed`. Append one row:

| Auth State | Meaning |
|------------|---------|
| `TokenExpired` | A previously stored token was rejected; clear the token store and reconnect. |

**2. Add a `Failure Recovery` paragraph** immediately after the `Session Restoration` paragraph in the `Auth / Identity — ITokenStore` section:

```markdown
**Failure Recovery:** Auth failures surface as `ConnectionStatus` events, not exceptions — gameplay code
observes them through `SpacetimeClient.ConnectionStateChanged`. The `ConnectionAuthState` value on the
resulting status identifies the failure category and the recommended recovery path:

- `TokenExpired` — A stored token was rejected. Call `Settings.TokenStore?.ClearTokenAsync()` to remove
  the invalid token; the next `Connect()` call will fall back to anonymous (or use fresh credentials if
  `Settings.Credentials` is set). This state is only emitted when the session was opened via token
  restoration.
- `AuthFailed` — Explicit credentials were rejected. Update `Settings.Credentials` with a valid token
  before reconnecting.

Recoverable auth failures are distinct from unrecoverable programming faults (e.g., missing `Host` or
`Database`) which throw `ArgumentException` synchronously from `Connect()` before any connection attempt.
The separation ensures that gameplay error-handling code only needs to react to the `ConnectionStatus`
event stream for expected runtime failures, not catch exceptions from the SDK connection path.
```

### Test File Coverage — `tests/test_story_2_4_failure_recovery.py`

#### `ConnectionAuthState.cs` content tests (AC: 2, 3)
- Contains `TokenExpired` enum value
- `TokenExpired` is defined in the `ConnectionAuthState` namespace/enum
- Contains XML doc comment referencing `ClearTokenAsync` for `TokenExpired`

#### `SpacetimeConnectionService.cs` content tests (AC: 1, 2)
- Contains `_restoredFromStore` field declaration
- Contains assignment `_restoredFromStore = restoredCredentials`
- Contains `_restoredFromStore` branch before `_credentialsProvided` branch in `OnConnectError` (ordering check)
- Contains `ConnectionAuthState.TokenExpired` usage
- `TokenExpired` transition message contains `"stored token was rejected"`
- `AuthFailed` path still exists (not removed by this story)
- Both `_restoredFromStore` and `_credentialsProvided` referenced in the `OnConnectError` method

#### `ConnectionAuthStatusPanel.cs` content tests (AC: 4)
- Contains `TokenExpired` in the switch expression
- Contains `"TOKEN EXPIRED"` label string
- Contains `"ClearTokenAsync"` in the `TokenExpired` action text
- `TokenExpired` arm appears before `AuthFailed` arm in file (ordering check — `TokenExpired` must take priority)

#### `docs/runtime-boundaries.md` content tests (AC: 1, 2, 3, 4)
- Contains `TokenExpired` in the auth state table
- Contains `Failure Recovery` section header or bold text
- Contains `ClearTokenAsync` in the failure recovery section
- Contains `ArgumentException` distinction (recoverable vs unrecoverable separation documented)
- Contains `TokenExpired` description referencing clearing the token store

#### Regression guards (must still pass from earlier stories)
- `ConnectionAuthState.cs` still has `None`, `AuthRequired`, `TokenRestored`, `AuthFailed`
- `SpacetimeConnectionService.cs` still has `_credentialsProvided`, `restoredCredentials`, `GetTokenAsync`, `HandleDisconnectError`
- `ConnectionAuthStatusPanel.cs` still has `TOKEN RESTORED`, `AUTH FAILED`, `AUTH REQUIRED` strings
- `ITokenStore.cs` still has `GetTokenAsync`, `StoreTokenAsync`, `ClearTokenAsync`
- `tests/test_story_2_3_session_restore.py` → all tests still pass
- `tests/test_story_2_2_auth_session.py` → all tests still pass
- `tests/test_story_1_4_adapter_boundary.py` → all tests still pass (isolation boundary not broken)

### File Locations — DO and DO NOT

**DO modify:**
```
addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs       (add TokenExpired)
addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs  (_restoredFromStore + OnConnectError update)
addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs     (TokenExpired arm in SetAuthStatus)
docs/runtime-boundaries.md                                                (auth state table + Failure Recovery paragraph)
```

**DO create:**
```
tests/test_story_2_4_failure_recovery.py
```

**DO NOT touch:**
```
addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs         (no changes — auth failures correctly bypass retry)
addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs  (Transition API is sufficient as-is)
addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs          (no changes needed)
addons/godot_spacetime/src/Public/SpacetimeSettings.cs                    (Credentials and TokenStore unchanged)
addons/godot_spacetime/src/Public/Auth/ITokenStore.cs                     (stable interface)
addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs              (no changes)
addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs     (no changes)
addons/godot_spacetime/src/Public/SpacetimeClient.cs                      (no public API changes)
scripts/compatibility/support-baseline.json                               (no new tracked files)
tests/test_story_1_*.py                                                   (regression only)
tests/test_story_2_1_*.py                                                 (regression only)
tests/test_story_2_2_*.py                                                 (regression only)
tests/test_story_2_3_*.py                                                 (regression only)
```

### Cross-Story Awareness

- **Story 2.2** established `_credentialsProvided`, `ConnectionAuthState.AuthFailed`, and the `OnConnectError` dispatch. Story 2.4 adds a new check *before* `_credentialsProvided` to route restored-token failures to `TokenExpired`.
- **Story 2.3** added the `restoredCredentials` local variable and the token restoration block in `Connect()`. Story 2.4 promotes that local to an instance field (`_restoredFromStore`) so `OnConnectError` can read it later.
- **Story 2.3 review fix** — the `finally { if (restoredCredentials) settings.Credentials = null; }` block clears the restored token from the settings resource. The `_restoredFromStore` field is set inside `Connect()` before `_adapter.Open()`, so it remains accurate for the lifetime of the connection attempt regardless of the `finally` cleanup.
- **Story 2.3 Cross-Story note** — the existing `AUTH FAILED` panel text already reads "Verify your token or call Settings.TokenStore?.ClearTokenAsync() to reset." This is intentionally kept for the explicit-credentials-rejected case (`AuthFailed`). Story 2.4 adds a dedicated `TokenExpired` path with sharper recovery guidance for the token-store case.
- **ReconnectPolicy** — not changed in this story. Auth failures during the `Connecting` phase never enter `HandleDisconnectError` and thus never invoke `TryBeginRetry`. This is correct: retrying a rejected identity without clearing credentials would loop indefinitely. The `Degraded → reconnect → auth-fail` edge case (expired token mid-session) defers to a future story; `HandleDisconnectError` will still transition to `Disconnected` but without auth state, which is acceptable for Epic 2 scope.

### Namespace and Isolation Rules

- `ConnectionAuthState.cs` is in `GodotSpacetime.Connection` — no new usings needed
- `SpacetimeConnectionService.cs` already imports `GodotSpacetime.Connection` — `ConnectionAuthState.TokenExpired` is directly accessible
- `ConnectionAuthStatusPanel.cs` already imports `GodotSpacetime.Connection` — `ConnectionAuthState.TokenExpired` is directly accessible
- The `#if TOOLS` guard on `ConnectionAuthStatusPanel.cs` must be preserved; do not remove it
- No `SpacetimeDB.*` references should be introduced in any modified file — the adapter isolation boundary is unchanged

### Failure Taxonomy (Architecture Alignment)

Architecture specifies:
> Recoverable runtime failures surface as typed errors or status events.
> Unrecoverable programming faults remain exceptions and should not be hidden.

Story 2.4 completes this contract for the auth surface:

| Failure Category | How Surfaced | Auth State | Recovery |
|-----------------|--------------|------------|----------|
| Invalid settings (missing Host/Database) | `ArgumentException` thrown from `Connect()` | N/A | Fix settings resource |
| Stored token rejected | `ConnectionStatus` event | `TokenExpired` | `ClearTokenAsync()`, then reconnect |
| Explicit credentials rejected | `ConnectionStatus` event | `AuthFailed` | Update `Settings.Credentials`, then reconnect |
| Network failure (anonymous) | `ConnectionStatus` event | `None` | Retry `Connect()` |
| Session lost post-connect | `ConnectionStatus` event (Degraded → Disconnected) | `None` | Retry `Connect()` |

### Verification Sequence

Run in order — each must pass before the next:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_2_4_failure_recovery.py
pytest -q
```

**Troubleshooting:**
- If `dotnet build` fails on `TokenExpired`: ensure the new enum value is inside the `ConnectionAuthState` enum block in `ConnectionAuthState.cs` and is correctly accessible from `SpacetimeConnectionService.cs` and `ConnectionAuthStatusPanel.cs`
- If switch expression fails to compile: C# exhaustive switch requires all enum values to be handled OR a discard arm (`_`) at the end. `ConnectionAuthStatusPanel.SetAuthStatus` already has a discard arm — adding `TokenExpired` before it is sufficient
- If test ordering check fails: verify `_restoredFromStore` check comes before the `_credentialsProvided` check in `OnConnectError` — use `content.index("_restoredFromStore")` < `content.index("_credentialsProvided")` in the relevant test
- If regression tests fail: verify no changes were made to `GetTokenAsync` call, `restoredCredentials` local, or the `_credentialsProvided` assignment in `Connect()`

### Project Structure Notes

- No new files are added to `addons/` — changes are limited to three existing files
- No `support-baseline.json` update needed (no new tracked files)
- `ConnectionAuthState.cs` is in `Public/Connection/` which is the correct location for public-facing SDK state enums
- Namespace follows existing pattern: all modified files already import `GodotSpacetime.Connection`

### References

- Story 2.4 AC and epic context: [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 2, Story 2.4]
- FR16 (recover from common connection and identity failures): [Source: `_bmad-output/planning-artifacts/epics.md` — FR map]
- Architecture: recoverable failures surface as typed status events; faults remain exceptions: [Source: `_bmad-output/planning-artifacts/architecture.md` — Implementation Patterns]
- Architecture: centralize reconnect and retry policy in the connection service: [Source: `_bmad-output/planning-artifacts/architecture.md` — Anti-Patterns]
- UX3: explicit lifecycle language, exact failure reasons, visible next actions: [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — UX Direction section]
- Story 2.3 dev notes — "Out of scope: distinguishing expired-token AuthFailed from network failures": [Source: `_bmad-output/implementation-artifacts/spec-2-3-restore-a-previous-session-from-persisted-auth-state.md` — Scope section]
- Story 2.3 cross-story — "Story 2.4 will handle token-store path rejection; Story 2.3 falls through existing AuthFailed path": [Source: same — Cross-Story Awareness section]
- Story 2.2 — `OnConnectError`, `_credentialsProvided`, `AuthFailed` state origin: [Source: `_bmad-output/implementation-artifacts/spec-2-2-authenticate-a-client-session-through-supported-identity-flows.md`]
- `ConnectionAuthState.cs` current values: [Source: `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs`]
- `SpacetimeConnectionService.cs` current Connect/OnConnectError implementation: [Source: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`]
- `ConnectionAuthStatusPanel.cs` current SetAuthStatus switch: [Source: `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs`]
- `ReconnectPolicy.cs` — TryBeginRetry only called from HandleDisconnectError: [Source: `addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs`]
- `docs/runtime-boundaries.md` — ConnectionAuthState table + Session Restoration paragraph: [Source: `docs/runtime-boundaries.md`]
- Test file pattern (`ROOT`, `_read()`, `_lines()`): [Source: `tests/test_story_2_3_session_restore.py`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

Senior Developer Review (AI) auto-fixed the remaining review issues: stale verification counts in the story record, inaccurate `TokenRestored` wording in the editor/docs, and token-clearing guidance that omitted the null-safe `TokenStore` access pattern.

### Completion Notes List

- Added `TokenExpired` enum value to `ConnectionAuthState` with XML doc referencing `ClearTokenAsync`.
- Added `_restoredFromStore` instance field to `SpacetimeConnectionService`; assigned from `restoredCredentials` local in `Connect()` after the restoration block.
- Updated `OnConnectError()` to check `_restoredFromStore` first (before `_credentialsProvided`), routing restored-token rejections to `TokenExpired` and preserving the existing `AuthFailed` path for explicit-credential rejections.
- Added `TokenExpired` arm to `ConnectionAuthStatusPanel.SetAuthStatus` switch before `AuthFailed`, with specific recovery guidance referencing `ClearTokenAsync()`.
- Updated `docs/runtime-boundaries.md`: added `TokenExpired` row to the `ConnectionAuthState` table and added `Failure Recovery` paragraph after `Session Restoration`.
- Senior Developer Review (AI) corrected `TokenRestored` wording in the panel/docs so restored sessions are not described as explicit-credential sessions.
- Senior Developer Review (AI) aligned runtime-boundaries token-clearing guidance with the null-safe `Settings.TokenStore?.ClearTokenAsync()` recovery path.
- Created `tests/test_story_2_4_failure_recovery.py` with 47 tests covering all ACs and regression guards.
- All 47 story-specific tests pass; full suite 665/665 green; `dotnet build` 0 errors, 0 warnings.

### File List

- `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs` (modified — added `TokenExpired`)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (modified — `_restoredFromStore` field + `OnConnectError` routing)
- `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs` (modified — `TokenExpired` arm in switch)
- `docs/runtime-boundaries.md` (modified — `TokenExpired` table row + Failure Recovery paragraph)
- `tests/test_story_2_4_failure_recovery.py` (created — 47 contract tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status updated)

## Change Log

- Added `ConnectionAuthState.TokenExpired` enum value with XML doc comment referencing `ClearTokenAsync()` (Date: 2026-04-14)
- Added `_restoredFromStore` field to `SpacetimeConnectionService`; updated `OnConnectError` to route restored-token rejections to `TokenExpired` before checking `_credentialsProvided` for `AuthFailed` (Date: 2026-04-14)
- Added `TokenExpired` arm to `ConnectionAuthStatusPanel.SetAuthStatus` with actionable recovery text (Date: 2026-04-14)
- Updated `docs/runtime-boundaries.md`: `TokenExpired` table row + Failure Recovery paragraph (Date: 2026-04-14)
- Created `tests/test_story_2_4_failure_recovery.py` — 47 contract tests covering all ACs and regression guards (Date: 2026-04-14)
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 0 High, 3 Medium fixed. Fixes: `TokenRestored` guidance now reflects restored as well as explicit credentials; runtime-boundaries token-clearing guidance now uses `Settings.TokenStore?.ClearTokenAsync()`; story verification counts corrected to 47 story tests and 665 total passing. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List.

### Findings Fixed

- MEDIUM: `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs` described `TokenRestored` as "provided credentials" even though the same state is emitted for token-store restoration, making the panel’s success guidance inaccurate for restored sessions.
- MEDIUM: `docs/runtime-boundaries.md` repeated the same inaccurate `TokenRestored` description and separately documented token clearing as `Settings.TokenStore.ClearTokenAsync()`, which contradicted the null-safe recovery path used elsewhere in this story.
- MEDIUM: the story artifact still claimed `35` story tests and `653` total tests even though the current review surface already validates at `47` story tests and `665` total tests, leaving stale verification evidence in the implementation record.

### Actions Taken

- Updated `ConnectionAuthStatusPanel.SetAuthStatus()` so `TokenRestored` guidance covers both restored and explicit credential flows.
- Updated `docs/runtime-boundaries.md` so `TokenRestored` semantics match the actual runtime behavior and token-clearing guidance consistently points to `Settings.TokenStore?.ClearTokenAsync()`.
- Corrected the story verification record, completion notes, file list counts, and change log to match the actual `pytest` results and review outcome.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_2_4_failure_recovery.py`
- `pytest -q`

### Reference Check

- Local reference: `_bmad-output/planning-artifacts/epics.md`
- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `_bmad-output/planning-artifacts/ux-design-specification.md`
- Local reference: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`
- Local reference: `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs`
- Local reference: `docs/runtime-boundaries.md`
- Local reference: `tests/test_story_2_4_failure_recovery.py`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
