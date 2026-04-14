# Story 2.1: Define Auth Configuration and Token Storage Boundaries

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As the SDK maintainer,
I want explicit auth settings and a token storage abstraction,
So that session handling is secure, configurable, and not hard-coded to one persistence strategy.

## Acceptance Criteria

**AC 1 — Given** a supported SDK configuration surface
**When** authentication behavior is defined for the runtime
**Then** the SDK exposes explicit auth-related settings and a token storage boundary suitable for supported workflows
**And** default behavior does not silently persist credentials without developer intent
**And** token reuse and clearing behavior are documented at the same boundary

## Tasks / Subtasks

- [x] Task 1 — Create `Internal/Auth/MemoryTokenStore.cs` (AC: 1)
  - [x] Implement `ITokenStore` with in-memory storage (field-backed, no Godot/platform deps)
  - [x] Use `namespace GodotSpacetime.Runtime.Auth;`
  - [x] `GetTokenAsync` returns current `_token` value (or `null`)
  - [x] `StoreTokenAsync` sets `_token`
  - [x] `ClearTokenAsync` sets `_token = null`
  - [x] No references to `SpacetimeDB.*` or `Godot.*`

- [x] Task 2 — Create `Internal/Auth/ProjectSettingsTokenStore.cs` (AC: 1)
  - [x] Implement `ITokenStore` backed by `Godot.ProjectSettings`
  - [x] Use `namespace GodotSpacetime.Runtime.Auth;`
  - [x] Setting key constant: `"spacetime/auth/token"`
  - [x] `GetTokenAsync`: reads the key, returns `null` if not set or empty
  - [x] `StoreTokenAsync`: writes string value to the key
  - [x] `ClearTokenAsync`: sets the key to `string.Empty`
  - [x] Only Godot dependency is `Godot.ProjectSettings`; no `SpacetimeDB.*`

- [x] Task 3 — Create `Internal/Auth/TokenRedactor.cs` (AC: 1)
  - [x] `internal static class TokenRedactor`
  - [x] `public static string Redact(string? token)` method
  - [x] Returns `"<no token>"` for null or empty input
  - [x] Returns `"<redacted>"` for tokens 8 characters or fewer
  - [x] Returns `"{first4}…<redacted>"` for longer tokens
  - [x] No external dependencies

- [x] Task 4 — Update `Public/SpacetimeSettings.cs` (AC: 1)
  - [x] Add `using GodotSpacetime.Auth;` at top
  - [x] Add `public ITokenStore? TokenStore { get; set; }` property
  - [x] XML doc: "Optional token store for persisting session tokens between connections. If null (the default), tokens are not persisted when the process exits."
  - [x] **DO NOT** add `[Export]` — `ITokenStore` is not a Godot type; assigned in code
  - [x] Remove the "Additional settings (auth, logging) are added in later stories" comment line

- [x] Task 5 — Update `Internal/Connection/SpacetimeConnectionService.cs` (AC: 1)
  - [x] Add `using GodotSpacetime.Auth;` at top
  - [x] Add `private ITokenStore? _tokenStore;` field
  - [x] In `Connect()`: set `_tokenStore = settings.TokenStore;` (after `ValidateSettings`)
  - [x] In `IConnectionEventSink.OnConnected`: add `if (_tokenStore != null) _ = _tokenStore.StoreTokenAsync(token);`
  - [x] Fire-and-forget `_ =` is intentional — token store failures are not fatal to connection lifecycle (Story 2.4 handles recovery)
  - [x] Token value is **never** logged directly (use `TokenRedactor.Redact(token)` if any diagnostic output is added)

- [x] Task 6 — Update `docs/runtime-boundaries.md` (AC: 1)
  - [x] In the `Configuration — SpacetimeSettings` section, add `TokenStore` row to the property table
  - [x] Remove "Additional settings (auth, logging) are added in later stories" note from the settings description
  - [x] In the `Auth / Identity — ITokenStore` section: expand to include built-in options (`MemoryTokenStore`, `ProjectSettingsTokenStore`) and explicit "assign via code to `Settings.TokenStore`" guidance
  - [x] Add a "Token Clearing" paragraph documenting that `ITokenStore.ClearTokenAsync()` removes persisted state

- [x] Task 7 — Update `scripts/compatibility/support-baseline.json` (AC: 1)
  - [x] Add to `required_paths` (after existing connection service paths):
    - `{ "path": "addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs", "type": "file" }`
    - `{ "path": "addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs", "type": "file" }`
    - `{ "path": "addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs", "type": "file" }`
  - [x] Preserve ALL existing content, comments, and structure — append only

- [x] Task 8 — Create `tests/test_story_2_1_auth_config.py` (AC: 1)
  - [x] Follow `ROOT`, `_read()`, `_lines()` pattern from `tests/test_story_1_9_connection.py` exactly
  - [x] Existence tests: all three `Internal/Auth/*.cs` files
  - [x] `SpacetimeSettings.cs` has `TokenStore` property
  - [x] `MemoryTokenStore.cs`: implements `ITokenStore`, has `GetTokenAsync`, `StoreTokenAsync`, `ClearTokenAsync`, no `SpacetimeDB.` reference
  - [x] `ProjectSettingsTokenStore.cs`: implements `ITokenStore`, contains `spacetime/auth/token` key constant, no `SpacetimeDB.` reference
  - [x] `TokenRedactor.cs`: exists, contains `Redact` method, contains `<redacted>` output string
  - [x] `SpacetimeConnectionService.cs`: contains `_tokenStore`, contains `StoreTokenAsync`
  - [x] `support-baseline.json`: contains `Internal/Auth/MemoryTokenStore.cs`
  - [x] `docs/runtime-boundaries.md`: contains `TokenStore` in the settings table
  - [x] Regression guards: `ITokenStore.cs` still present with `GetTokenAsync`, `StoreTokenAsync`, `ClearTokenAsync`

- [x] Task 9 — Verify
  - [x] `python3 scripts/compatibility/validate-foundation.py` → exits 0
  - [x] `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
  - [x] `pytest tests/test_story_2_1_auth_config.py` → all pass
  - [x] `pytest -q` → full suite passes (stories 1.3–2.1 all green)

## Dev Notes

### Scope: What This Story Is and Is Not

Story 2.1 is an **infrastructure boundary story**. It defines and wires the auth/token storage layer so that Stories 2.2–2.4 can build on a stable foundation.

**In scope:**
- Creating the three `Internal/Auth/` implementation files
- Adding `TokenStore` property to `SpacetimeSettings`
- Wiring token storage into `SpacetimeConnectionService.OnConnected`
- Documenting the boundary in `runtime-boundaries.md`
- Tests and support-baseline entries for new files

**Out of scope (belongs to later stories):**
- Token restoration/reuse on reconnect (Story 2.3)
- Auth failure recovery and status distinctions (Story 2.4)
- Logging/log-category configuration (Story 5.x or later)
- OIDC/SpacetimeAuth identity flow implementation (Story 2.2)
- ConnectionState auth phases (`Auth Required`, `Token Restored`, `Auth Failed`) — these are Story 2.2

### What Already Exists — DO NOT RECREATE

| Component | Story Delivered | File |
|-----------|----------------|------|
| `ITokenStore` interface (3-method async) | 1.3 | `Public/Auth/ITokenStore.cs` |
| `LogCategory.Auth` enum value | 1.3 | `Public/Logging/LogCategory.cs` |
| `SpacetimeSettings` with Host/Database | 1.9 | `Public/SpacetimeSettings.cs` |
| `SpacetimeClient` with Connect/Disconnect | 1.9 | `Public/SpacetimeClient.cs` |
| `SpacetimeConnectionService` with `OnConnected(string token)` | 1.9 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `SpacetimeSdkConnectionAdapter` token flow | 1.9 | `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` |
| `ITokenStore` concept in `runtime-boundaries.md` | 1.3/1.9 | `docs/runtime-boundaries.md` |

### Existing Token Flow (Context for the Wiring Change)

The token already flows through the system from Story 1.9:
```
SpacetimeSdkConnectionAdapter.CreateConnectCallback()
  → IConnectionEventSink.OnConnected(string token)
    → SpacetimeConnectionService.OnConnected(string token)   ← token currently IGNORED here
```

Story 2.1 makes `SpacetimeConnectionService.OnConnected` store the token:
```
SpacetimeConnectionService.OnConnected(string token)
  → if (_tokenStore != null) _ = _tokenStore.StoreTokenAsync(token);  ← ADD THIS
```

The `_tokenStore` field is populated from `settings.TokenStore` when `Connect()` is called.

### `SpacetimeConnectionService.cs` — Exact Change Required

Current `Connect()` body (around line 34-36):
```csharp
_host = settings.Host.Trim();
_database = settings.Database.Trim();
_reconnectPolicy.Reset();
```

After change:
```csharp
_host = settings.Host.Trim();
_database = settings.Database.Trim();
_tokenStore = settings.TokenStore;
_reconnectPolicy.Reset();
```

Current `OnConnected` body starts with:
```csharp
void IConnectionEventSink.OnConnected(string token)
{
    _reconnectPolicy.Reset();
    ...
```

After change, add the store call after `_reconnectPolicy.Reset()`:
```csharp
void IConnectionEventSink.OnConnected(string token)
{
    _reconnectPolicy.Reset();
    if (_tokenStore != null)
        _ = _tokenStore.StoreTokenAsync(token);
    ...
```

### `SpacetimeSettings.cs` — Exact Change Required

Add `using GodotSpacetime.Auth;` after the existing `using Godot;` line.

Add the `TokenStore` property after `Database`:
```csharp
/// <summary>
/// Optional token store for persisting session tokens between connections.
/// If null (the default), tokens are not persisted when the process exits.
/// Assign a <see cref="ITokenStore"/> implementation to enable opt-in session persistence.
/// Built-in options: <c>MemoryTokenStore</c> (in-memory, non-persistent) or
/// <c>ProjectSettingsTokenStore</c> (persists to Godot ProjectSettings).
/// </summary>
public ITokenStore? TokenStore { get; set; }
```

Remove the class-level XML doc comment line: `/// Additional settings (auth, logging) are added in later stories.`

### New File Structure

```
addons/godot_spacetime/src/Internal/Auth/   ← CREATE THIS DIRECTORY
    MemoryTokenStore.cs                      ← CREATE
    ProjectSettingsTokenStore.cs             ← CREATE
    TokenRedactor.cs                         ← CREATE
```

**MemoryTokenStore.cs namespace:** `GodotSpacetime.Runtime.Auth`
**ProjectSettingsTokenStore.cs namespace:** `GodotSpacetime.Runtime.Auth`
**TokenRedactor.cs namespace:** `GodotSpacetime.Runtime.Auth`

### Namespace and Isolation Rules

- `Internal/Auth/` files use namespace `GodotSpacetime.Runtime.Auth` (matches `Internal/Connection/` pattern)
- `Internal/Auth/` files must NOT reference `SpacetimeDB.*` (Story 1.4 isolation boundary)
- `MemoryTokenStore.cs` must NOT reference `Godot.*` (pure C# in-memory, no platform deps)
- `ProjectSettingsTokenStore.cs` MAY reference `Godot.ProjectSettings` only
- `TokenRedactor.cs` must NOT reference `SpacetimeDB.*` or `Godot.*`
- The test in `test_story_1_3_sdk_concepts.py` verifies `SpacetimeDB.*` only appears in `Internal/Platform/DotNet/` — confirm the new files don't break this

### Fire-and-Forget Token Storage Design

The `_ = _tokenStore.StoreTokenAsync(token)` pattern is intentional. Justification:
- Connection lifecycle state transitions must complete synchronously from the SDK callback
- Token storage failure is not fatal to connection success (session is established regardless)
- Story 2.4 addresses recovery from auth state failures
- If token storage fails silently, the worst outcome is a non-persistent session (the same as if no store was provided)

Do NOT `await` the token store call inside `OnConnected` — this is a synchronous SDK callback context.

### `docs/runtime-boundaries.md` — Required Changes

**1. SpacetimeSettings table** — change from:
```
| `Host` | `string` | The SpacetimeDB server address |
| `Database` | `string` | The target database name on the server |
```
To:
```
| `Host` | `string` | The SpacetimeDB server address |
| `Database` | `string` | The target database name on the server |
| `TokenStore` | `ITokenStore?` | Optional token persistence provider; `null` by default (tokens not persisted) |
```

**2. Remove** the note: "Additional settings (auth, logging) are added in later stories and appear as exported properties visible in the Godot editor inspector."

**3. Auth / Identity section** — add after the existing interface code block:

> **Built-in implementations** (from `Internal/Auth/`):
> - `MemoryTokenStore` — retains the token in memory for the current process lifetime only. Tokens survive reconnects within a session but are cleared when the process exits.
> - `ProjectSettingsTokenStore` — persists the token to Godot `ProjectSettings` under the key `spacetime/auth/token`. Suitable for development environments; review your distribution's security model before enabling in production.
>
> Assign via code to `Settings.TokenStore` before calling `Connect()`. The built-in implementations are in `Internal/`; they are not exported to the Godot inspector.
>
> To clear persisted auth state, call `Settings.TokenStore.ClearTokenAsync()`. Token values are never logged raw; the `TokenRedactor` utility in `Internal/Auth/` produces safe diagnostic representations.

### Test File Pattern

Follow `tests/test_story_1_9_connection.py` exactly:

```python
"""
Story 2.1: Define Auth Configuration and Token Storage Boundaries
...
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]
```

All tests are **pure static file/content checks** — no dotnet execution, no Godot editor launch, no live network.

### `support-baseline.json` — Verification

Current last entries in `required_paths` include connection service files. Insert the three new `Internal/Auth/` paths after the last `Internal/Connection/` entry. Preserve ALL existing content — do not reformat or reorder.

### Regression Guards Required

The following must remain true after this story:
- `tests/test_story_1_3_sdk_concepts.py` — `SpacetimeDB.` references exist ONLY in `Internal/Platform/DotNet/` (new `Internal/Auth/` files must have zero `SpacetimeDB.` references)
- `tests/test_story_1_9_connection.py` — `SpacetimeConnectionService.cs` still has `Connect(`, `OnConnected(`, `Disconnect(`, `FrameTick(`
- `Public/Auth/ITokenStore.cs` unchanged — `GetTokenAsync`, `StoreTokenAsync`, `ClearTokenAsync` all present
- `SpacetimeClient.cs` unchanged — it already passes `Settings` to the connection service, which now reads `TokenStore` from `Settings`

### Verification Sequence

Run in order — each step must pass before the next:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_2_1_auth_config.py
pytest -q
```

**Troubleshooting:**
- If `dotnet build` fails with namespace errors: check that `Internal/Auth/` files use `GodotSpacetime.Runtime.Auth` not `GodotSpacetime.Auth` (that's the Public namespace)
- If `test_story_1_3_sdk_concepts.py` fails with SpacetimeDB isolation test: check `ProjectSettingsTokenStore.cs` — it must not reference `SpacetimeDB.*`
- If build fails on `ITokenStore?` in SpacetimeSettings: ensure `using GodotSpacetime.Auth;` is added to `SpacetimeSettings.cs`

### File Locations — DO and DO NOT

**DO create:**
```
addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs
addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs
addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs
tests/test_story_2_1_auth_config.py
```

**DO modify:**
```
addons/godot_spacetime/src/Public/SpacetimeSettings.cs      (add TokenStore property)
addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs  (wire token store)
docs/runtime-boundaries.md                                   (update settings table + auth section)
scripts/compatibility/support-baseline.json                  (add 3 required paths)
```

**DO NOT touch:**
```
addons/godot_spacetime/src/Public/Auth/ITokenStore.cs        (complete from 1.3 — 3-method interface)
addons/godot_spacetime/src/Public/SpacetimeClient.cs         (no changes needed — passes Settings as-is)
addons/godot_spacetime/src/Internal/Platform/DotNet/**       (SDK adapter — isolation boundary intact)
addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs
addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs
addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs
addons/godot_spacetime/src/Editor/**                         (editor panels — no auth changes this story)
demo/**
spacetime/modules/**
scripts/codegen/**
.github/workflows/
tests/test_story_1_*.py                                      (existing tests — only regression guards)
```

### Cross-Story Awareness

- **Story 2.2** (Authenticate a Client Session) will extend `SpacetimeConnectionService` with actual OIDC/JWT token injection into the builder. The `ITokenStore` wired here is the foundation for that.
- **Story 2.3** (Restore a Previous Session) will call `Settings.TokenStore?.GetTokenAsync()` before `Connect()` to restore a prior token. The `TokenStore` property added here is the injection point.
- **Story 2.4** (Recover from Failures) will add proper error handling around token store operations — the fire-and-forget pattern here is acceptable for now.
- **Story 5.x** (Docs) will include auth configuration in the sample project and docs — the `ProjectSettingsTokenStore` is the documented sample choice.
- **`ConnectionAuthStatusPanel.cs`** is named with "Auth" because it will display auth status in Story 2.2 — do not rename it.

### References

- Story 2.1 AC and epic context: [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 2, Story 2.1]
- FR14, FR15, FR16 (auth requirements): [Source: `_bmad-output/planning-artifacts/prd.md` — Connection & Identity Management]
- NFR5-8 (security/token requirements): [Source: `_bmad-output/planning-artifacts/prd.md` — Security NFRs]
- Architecture auth section (OIDC/JWT, token abstraction, isolation): [Source: `_bmad-output/planning-artifacts/architecture.md` — Authentication & Security]
- Architecture file structure (`Internal/Auth/` layout): [Source: `_bmad-output/planning-artifacts/architecture.md` — File Structure]
- Architecture implementation sequence (step 4): [Source: `_bmad-output/planning-artifacts/architecture.md` — Implementation Sequence]
- Token flow: `SpacetimeSdkConnectionAdapter.CreateConnectCallback()` → `IConnectionEventSink.OnConnected`: [Source: `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs`]
- Existing `SpacetimeConnectionService.OnConnected` (currently ignores token): [Source: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`]
- Epic 1 retro — `ITokenStore` no reference implementation was High-severity tech debt: [Source: `_bmad-output/implementation-artifacts/epic-1-retro-2026-04-14.md`]
- Isolation boundary rule (no `SpacetimeDB.*` outside `Internal/Platform/DotNet/`): [Source: `tests/test_story_1_3_sdk_concepts.py`]
- Test file pattern: [Source: `tests/test_story_1_9_connection.py`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation proceeded cleanly with no blockers.

### Completion Notes List

- Created `Internal/Auth/MemoryTokenStore.cs`: field-backed `ITokenStore` with no Godot/SpacetimeDB dependencies.
- Created `Internal/Auth/ProjectSettingsTokenStore.cs`: `ITokenStore` backed by `Godot.ProjectSettings` at key `spacetime/auth/token`; no `SpacetimeDB.*` reference.
- Created `Internal/Auth/TokenRedactor.cs`: static utility with `Redact(string?)` — returns `<no token>`, `<redacted>`, or `{first4}…<redacted>` depending on token length.
- Updated `SpacetimeSettings.cs`: added `using GodotSpacetime.Auth;` and `ITokenStore? TokenStore` property with full XML doc; removed stale "later stories" comment.
- Updated `SpacetimeConnectionService.cs`: added `using GodotSpacetime.Auth;`, `_tokenStore` field, wired `_tokenStore = settings.TokenStore` in `Connect()`, and fire-and-forget token persistence in `OnConnected`.
- Updated `docs/runtime-boundaries.md`: added `TokenStore` row to settings table, removed stale "later stories" note, expanded Auth/Identity section with built-in implementations and Token Clearing paragraph.
- Updated `scripts/compatibility/support-baseline.json`: appended three `Internal/Auth/` file paths after existing connection service entries.
- Senior review fix: `ProjectSettingsTokenStore` now persists writes via `ProjectSettings.Save()` and surfaces save failures through the returned `Task`.
- Senior review fix: `SpacetimeConnectionService` now observes optional token-store failures so persistence remains non-fatal to connection success.
- Created and expanded `tests/test_story_2_1_auth_config.py`: 57 static file/content tests — all pass.
- All validations pass: `validate-foundation.py` exits 0, `dotnet build` → 0 errors/0 warnings, `pytest tests/test_story_2_1_auth_config.py` → 57/57, `pytest -q` → 527/527.

### File List

- `addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs` (created)
- `addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs` (created)
- `addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs` (created)
- `addons/godot_spacetime/src/Public/SpacetimeSettings.cs` (modified)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (modified)
- `docs/runtime-boundaries.md` (modified)
- `scripts/compatibility/support-baseline.json` (modified)
- `tests/test_story_2_1_auth_config.py` (created)

## Change Log

- Story 2.1 implementation complete — auth/token storage boundary established (Date: 2026-04-14)
  - Created `Internal/Auth/` directory with `MemoryTokenStore`, `ProjectSettingsTokenStore`, and `TokenRedactor`
  - Wired `ITokenStore` into `SpacetimeSettings` and `SpacetimeConnectionService`
  - Updated `runtime-boundaries.md` with `TokenStore` property table row and built-in implementation docs
  - Updated `support-baseline.json` with three new `Internal/Auth/` paths
  - Added initial `test_story_2_1_auth_config.py` coverage for the auth boundary
- Senior Developer review fixes applied (Date: 2026-04-14)
  - Persisted `ProjectSettingsTokenStore` writes with `ProjectSettings.Save()` and surfaced save failures through the returned task
  - Hardened `SpacetimeConnectionService` so optional token-store failures remain observed and non-fatal
  - Expanded `test_story_2_1_auth_config.py` to 57 tests and revalidated the full 527-test suite

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List.

### Findings Fixed

- HIGH: `addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs` claimed persistent token storage but never saved `ProjectSettings` after `SetSetting`, so stored tokens would be lost across process restarts despite the story docs advertising persistence.
- MEDIUM: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` treated token persistence as fire-and-forget, but synchronous `ITokenStore` failures could still escape `OnConnected` and fault the connection callback path.
- MEDIUM: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` also left asynchronously faulted token-store tasks unobserved, which could surface later as noisy runtime exceptions even though the story intent was "non-fatal optional persistence."
- MEDIUM: the story record still claimed `26` story tests and `496` total tests even though the committed review surface now validates `57` story tests and `527` total tests, leaving stale verification evidence in the artifact.

### Actions Taken

- Added `ProjectSettings.Save()`-backed persistence in `ProjectSettingsTokenStore` and return a faulted task when the save fails.
- Wrapped token-store persistence in guarded fire-and-forget handling so synchronous exceptions are swallowed and faulted tasks are observed.
- Expanded `tests/test_story_2_1_auth_config.py` with persistence and token-store failure-handling regression guards.
- Updated the story record and change log with the post-review behavior and verification counts, then synced story + sprint tracking to `done`.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_2_1_auth_config.py`
- `pytest -q`

### Reference Check

- Local reference: `_bmad-output/planning-artifacts/epics.md` (used as the Story 2.1 context source; no separate Epic 2 context/tech-spec artifact was present)
- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `docs/runtime-boundaries.md`
- Local reference: `addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs`
- Local reference: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
