# Story 5.2: Extend the Sample Through Auth, Session Resume, and Live Subscription Flow

Status: done

## Story

As an external Godot developer,
I want the sample to cover authenticated live-state behavior,
so that I can compare my integration against a working reference for session and subscription flows.

## Acceptance Criteria

1. **Given** the sample project is configured for a supported deployment **When** I run the supported authenticated path **Then** the sample demonstrates auth or token restore, subscription startup, local cache reads, and visible row updates
2. **And** any auth prerequisites or optional setup are documented next to the sample flow
3. **And** the runtime flow matches the same lifecycle language and steps described in the docs

## Tasks / Subtasks

- [x] Task 1: Modify `demo/DemoMain.cs` — extend with auth, session resume, and subscription (AC: 1, 3)
  - [x] 1.1 Add `using System.Linq;`, `using GodotSpacetime.Runtime.Auth;`, and `using GodotSpacetime.Subscriptions;` imports
  - [x] 1.2 Add `private SubscriptionHandle? _subscriptionHandle;` field
  - [x] 1.3 In `_Ready()`, before `_client.Connect()`: wire all new signal handlers using -= then += pattern for `ConnectionOpened`, `ConnectionClosed`, `SubscriptionApplied`, `SubscriptionFailed`, `RowChanged`; and if `_client.Settings != null`, set `_client.Settings.TokenStore = new ProjectSettingsTokenStore()` to enable session token persistence
  - [x] 1.4 In the existing `OnConnectionStateChanged` handler: add a branch for `status.State == ConnectionState.Connected && (_subscriptionHandle == null || _subscriptionHandle.Status != SubscriptionStatus.Active)` that calls `_subscriptionHandle = _client!.Subscribe(new[] { "SELECT * FROM smoke_test" })` and prints `"[Demo] Subscribed to smoke_test — awaiting initial sync"`
  - [x] 1.5 Add `OnConnectionOpened(ConnectionOpenedEvent e)` handler: print `$"[Demo] Session identity: {(string.IsNullOrEmpty(e.Identity) ? "(new — token will be stored)" : e.Identity)}"` to indicate whether this is a fresh or restored session
  - [x] 1.6 Add `OnSubscriptionApplied(SubscriptionAppliedEvent e)` handler: call `var rows = _client!.GetRows("SmokeTest").ToList()` and print `$"[Demo] Subscription applied — {rows.Count} row(s) in smoke_test"`
  - [x] 1.7 Add `OnSubscriptionFailed(SubscriptionFailedEvent e)` handler: print `$"[Demo] Subscription failed: {e.ErrorMessage}"`
  - [x] 1.8 Add `OnRowChanged(RowChangedEvent e)` handler: print `$"[Demo] Row changed — table: {e.TableName}, type: {e.ChangeType}"`
  - [x] 1.9 In `_ExitTree()`: unsubscribe all newly added signal handlers using the same -= cleanup pattern; if `_subscriptionHandle != null && _subscriptionHandle.Status == SubscriptionStatus.Active`, call `_client.Unsubscribe(_subscriptionHandle)` and clear `_subscriptionHandle` after cleanup so reconnect/reload paths can resubscribe cleanly
  - [x] 1.10 Update the XML doc comment on the class to note that auth and subscription are now wired: `/// <summary>Demo scene extended through Story 5.2 — wires auth token persistence, subscription to smoke_test, and row-change observation. Story 5.3 adds reducer interaction.</summary>`

- [x] Task 2: Update `demo/README.md` — document auth and subscription extended demo paths (AC: 2, 3)
  - [x] 2.1 Add a `## Auth and Session Resume` section after the existing Step 7 content, covering:
    - Default behavior: `DemoMain` opens an anonymous session on first run; the server assigns a new identity
    - Token persistence: `DemoMain` now sets `Settings.TokenStore = new ProjectSettingsTokenStore()` before connecting; the SDK stores the server-assigned token under the Godot ProjectSetting key `spacetime/auth/token`
    - Session resume: on subsequent runs the stored token is automatically restored (no code change required); the Output panel shows the previously assigned identity instead of `"(new — token will be stored)"`
    - Auth prerequisites: the deployment must accept token-authenticated sessions; anonymous and token sessions both work with the smoke test module
    - External project guidance: external projects should implement the public `GodotSpacetime.Auth.ITokenStore` interface; `ProjectSettingsTokenStore` is an in-repo helper accessible because the demo and addon share an assembly
    - Reset instructions: clear the stored token by running `Project > Project Settings` and removing `spacetime/auth/token`, or, after confirming `Settings.TokenStore` is configured, call `await Settings.TokenStore.ClearTokenAsync()` before the next `Connect()` call
  - [x] 2.2 Add a `## Subscription and Live State` section after the auth section, covering:
    - After `Connected`, `DemoMain` calls `Subscribe(["SELECT * FROM smoke_test"])`; the Output panel shows `"[Demo] Subscribed to smoke_test — awaiting initial sync"`
    - After the server confirms the subscription, `SubscriptionApplied` fires: `DemoMain` reads the local cache with `GetRows("SmokeTest").ToList()` and Output shows `"[Demo] Subscription applied — N row(s) in smoke_test"` where N is the current cache count
    - Live row changes emit `"[Demo] Row changed — table: SmokeTest, type: Insert/Update/Delete"` on each mutation
    - Output panel expected message sequence: `[Demo] Bootstrap ready` → `[Demo] Connection state: CONNECTING ...` → `[Demo] Connection state: CONNECTED ...` → `[Demo] Subscribed to smoke_test ...` → `[Demo] Session identity: ...` → `[Demo] Subscription applied — ...`
    - The SQL query still uses `smoke_test`, but `GetRows()` follows the generated PascalCase table name `SmokeTest`
    - Lifecycle language (`SubscriptionApplied`, `RowChanged`) is defined in `docs/runtime-boundaries.md`

- [x] Task 3: Write `tests/test_story_5_2_extend_sample_auth_subscription.py` (AC: 1, 2, 3)
  - [x] 3.1 Existence tests:
    - `demo/DemoMain.cs` exists (still present after modification)
    - `demo/README.md` exists (still present after modification)
  - [x] 3.2 `demo/DemoMain.cs` content tests (AC: 1, 3):
    - Contains `GodotSpacetime.Runtime.Auth` (auth namespace import)
    - Contains `GodotSpacetime.Subscriptions` (subscription namespace import)
    - Contains `ProjectSettingsTokenStore` (auth wired up with built-in token persistence)
    - Contains `TokenStore` (token persistence property assigned)
    - Contains `_subscriptionHandle` (handle field declared for lifecycle management)
    - Contains `Subscribe(` (subscription call present)
    - Contains `smoke_test` (correct table name used in query)
    - Contains `SubscriptionApplied` (subscription confirmed signal handled)
    - Contains `SubscriptionFailed` (subscription failure signal handled)
    - Contains `RowChanged` (row change signal handled)
    - Contains `GetRows("SmokeTest")` (local cache read after subscription applied with the generated PascalCase table name)
    - Contains `ConnectionOpened` (connection opened signal handled for identity logging)
    - Contains `ConnectionClosed` (connection closed signal handled for reconnect-safe subscription reset)
    - Contains `Unsubscribe` (subscription cleanup in ExitTree)
    - Contains `SubscriptionStatus.Active` (guard before unsubscribe in cleanup)
    - Contains `e.Identity` (identity printed from ConnectionOpenedEvent)
    - Contains `e.ChangeType` (row change type printed from RowChangedEvent)
    - Contains `e.ErrorMessage` (error message printed from SubscriptionFailedEvent)
    - Contains `_subscriptionHandle.Status != SubscriptionStatus.Active` (resubscribe guard for reconnect/failure recovery)
  - [x] 3.3 `demo/README.md` content tests (AC: 2, 3):
    - Contains `## Auth` (auth section present)
    - Contains `TokenStore` (token persistence documented)
    - Contains `ProjectSettingsTokenStore` (built-in helper referenced in docs)
    - Contains `ITokenStore` (external project guidance present)
    - Contains `spacetime/auth/token` (project setting key documented for reset instructions)
    - Contains `## Subscription` (subscription section present)
    - Contains `smoke_test` (subscription target documented)
    - Contains `GetRows("SmokeTest")` (cache-read contract documented with generated PascalCase table name)
    - Contains `SubscriptionApplied` (lifecycle term aligned with docs)
    - Contains `RowChanged` (row change lifecycle term aligned with docs)
    - Documents the reviewed message order where `Connection state: CONNECTED ...` appears before `Session identity: ...`
    - Contains `authenticated session established` (restored-token connection status text documented)
    - Contains `docs/runtime-boundaries.md` (canonical lifecycle reference linked)
  - [x] 3.4 Regression guards — all prior deliverables must remain intact:
    - `demo/DemoMain.cs` exists (Story 5.1)
    - `demo/DemoMain.tscn` exists (Story 5.1)
    - `demo/autoload/DemoBootstrap.cs` exists (Story 5.1)
    - `demo/scenes/connection_smoke.tscn` exists (Story 5.1)
    - `project.godot` still contains `DemoBootstrap` autoload registration (Story 5.1 critical fix)
    - `docs/quickstart.md` exists (Story 1.10)
    - `docs/install.md` exists (Story 1.1)
    - `docs/codegen.md` exists (Story 1.6/1.7)
    - `demo/generated/smoke_test/` directory exists (Story 1.6)
    - `demo/generated/smoke_test/Reducers/Ping.g.cs` exists (generated binding)
    - `demo/generated/smoke_test/SpacetimeDBClient.g.cs` exists (generated binding)
    - `demo/generated/smoke_test/Tables/SmokeTest.g.cs` exists (generated binding)
    - `spacetime/modules/smoke_test/src/lib.rs` exists (smoke test source module)
    - `addons/godot_spacetime/src/Public/SpacetimeClient.cs` exists (SDK public boundary)

## Dev Notes

### What This Story Delivers

Story 5.2 extends the Story 5.1 demo baseline with three new capabilities visible in `demo/DemoMain.cs`:

1. **Token persistence (auth path):** `Settings.TokenStore` is set to a `ProjectSettingsTokenStore` before `Connect()` is called. On first run, the server assigns a new identity and the SDK stores the resulting token under `spacetime/auth/token` in Godot ProjectSettings (via `IConnectionEventSink.OnConnected → _tokenStore.StoreTokenAsync(token)`). On subsequent runs, `SpacetimeConnectionService.Connect()` reads the stored token via `GetTokenAsync()` and injects it as `settings.Credentials` — restoring the same session identity automatically.

2. **Subscription startup and cache reads:** After `ConnectionState.Connected` is reached, `Subscribe(["SELECT * FROM smoke_test"])` is called. When `SubscriptionApplied` fires, `GetRows("SmokeTest")` returns the current cache contents because `GetRows()` follows the generated PascalCase `RemoteTables` property name rather than the SQL table identifier. The smoke test module's SQL table is `smoke_test` (type: `SpacetimeDB.Types.SmokeTest`, fields: `uint Id`, `string Value`).

3. **Live row update observation:** `RowChanged` fires for each `Insert`, `Update`, or `Delete` mutation. The handler logs `TableName` (PascalCase: `"SmokeTest"`) and `ChangeType` (enum: `RowChangeType.Insert`, `.Update`, `.Delete`).

**Scope boundaries:**
- Do NOT add reducer calls — that belongs to Story 5.3 (`reducer_smoke.tscn`)
- Do NOT create new scene files — all Story 5.2 behavior lives in the modified `DemoMain.cs` and `README.md`
- Do NOT modify `DemoBootstrap.cs` — it stays as a minimal autoload stub
- Do NOT modify `DemoMain.tscn` — the scene structure is unchanged
- Do NOT touch the generated bindings in `demo/generated/smoke_test/` — they are read-only committed artifacts

### Critical Architecture Constraints

**`ProjectSettingsTokenStore` access:**
`ProjectSettingsTokenStore` is `internal sealed` in namespace `GodotSpacetime.Runtime.Auth`. It is accessible from `GodotSpacetime.Demo.DemoMain` because all C# scripts in the Godot project compile into a single assembly — the `internal` keyword is assembly-scoped, not namespace-scoped. External projects (outside this repo) CANNOT access `ProjectSettingsTokenStore` directly; they must implement `GodotSpacetime.Auth.ITokenStore` themselves. Document this distinction clearly in `demo/README.md`.

**Signal wiring pattern (from Story 5.1):**
Always use `handler -= ...` before `handler += ...` in `_Ready()` to prevent duplicate handlers if the scene is reloaded. This is the established pattern in `DemoMain.cs` (Story 5.1 senior review added `_ExitTree` cleanup for exactly this reason). All new signal handlers follow the same pattern.

**Subscription lifecycle:**
- `Subscribe()` is only valid while `ConnectionState == Connected`. Call it inside the `OnConnectionStateChanged` handler only when the state is `Connected`.
- Guard with `_subscriptionHandle == null` to avoid double-subscribing if the `Connected` state is re-emitted.
- In `_ExitTree()`, check `_subscriptionHandle.Status == SubscriptionStatus.Active` before calling `Unsubscribe()` — the `Unsubscribe()` method is idempotent but the guard is explicit documentation of intent.

**`GetRows` return type:**
`SpacetimeClient.GetRows(string tableName)` returns `IEnumerable<object>`. Call `.ToList()` to materialize the count. The `tableName` argument must use the generated PascalCase table/property name (`"SmokeTest"`), while the SQL subscription query still uses the snake_case module table name (`"smoke_test"`). Each row is a `SpacetimeDB.Types.SmokeTest` instance; cast with `as SpacetimeDB.Types.SmokeTest` if typed access is needed (Story 5.2 only needs the count, so casting is not required).

**`RowChangedEvent.TableName` casing:**
The table name in `RowChangedEvent.TableName` is the PascalCase generated property name (`"SmokeTest"`), not the snake_case SQL name (`"smoke_test"`). The `GetRows()` call also uses the PascalCase generated property name, while `Subscribe()` still uses the snake_case SQL query. These are DIFFERENT strings in different contexts — do not confuse them.

**`ConnectionOpened` vs `ConnectionStateChanged` order:**
Both signals fire when a session opens. `ConnectionOpened` includes `Identity` (the server-assigned identity string). `ConnectionStateChanged` fires for state transitions including `Disconnected → Connecting → Connected`, and `SpacetimeConnectionService.OnConnected()` transitions to `Connected` before it emits `ConnectionOpened`. For the demo, log identity in `OnConnectionOpened` and initiate the subscription in `OnConnectionStateChanged(Connected)`, which means the demo's `CONNECTED` and `Subscribed` lines appear before the identity line in the Output panel. Do not subscribe inside `OnConnectionOpened` because `GetRows()` and `Subscribe()` may not be available until `Connected` state is confirmed.

**`SpacetimeSettings.Credentials` vs `TokenStore`:**
`Credentials` is set directly on `SpacetimeSettings` for one-time explicit token injection. `TokenStore` is the opt-in persistence layer. `SpacetimeConnectionService.Connect()` reads from `TokenStore.GetTokenAsync()` and sets `Credentials` only if `Credentials` is null/empty — this is the auto-restore path. The demo uses `TokenStore` only (leaves `Credentials` null); the SDK handles the restore transparently.

**`ConnectionOpenedEvent.Identity` for anonymous sessions:**
On first anonymous connect, `Identity` may be empty string until the server sends back the assigned identity. Check `string.IsNullOrEmpty(e.Identity)` and show a placeholder like `"(new — token will be stored)"` for clarity.

### Project Structure Notes

**Files to modify:**
- `demo/DemoMain.cs` — extend (do NOT recreate; preserve the existing `_Ready`, `_ExitTree`, and `OnConnectionStateChanged` logic)
- `demo/README.md` — add new sections (preserve all existing Steps 1–7 and Reset section; append new sections after Step 7)

**Files to create:**
- `tests/test_story_5_2_extend_sample_auth_subscription.py` — new test file

**Files NOT to touch:**
- `demo/DemoMain.tscn` — no scene changes needed
- `demo/autoload/DemoBootstrap.cs` — stays minimal stub
- `demo/scenes/connection_smoke.tscn` — structural placeholder unchanged
- `demo/generated/smoke_test/` — read-only generated artifacts
- `addons/godot_spacetime/` — SDK addon code is out of scope
- `spacetime/modules/smoke_test/` — Rust source module is out of scope
- All `docs/*.md` — documentation stories are Story 5.4+

**Architecture directory structure (no new directories needed):**
```
demo/
├── DemoMain.tscn          ← unchanged
├── DemoMain.cs            ← MODIFIED (Task 1)
├── README.md              ← MODIFIED (Task 2)
├── autoload/
│   └── DemoBootstrap.cs   ← unchanged
├── generated/
│   └── smoke_test/        ← read-only, do not touch
└── scenes/
    └── connection_smoke.tscn  ← unchanged
    (reducer_smoke.tscn will be Story 5.3)
```

### SDK Surface Reference

**`SpacetimeClient` members used in this story:**
```csharp
// Property
public SpacetimeSettings? Settings { get; set; }  // set TokenStore before Connect()

// Signals (Godot C# event syntax)
public event ConnectionOpenedEventHandler? ConnectionOpened;       // Identity, Host, Database, ConnectedAt
public event SubscriptionAppliedEventHandler? SubscriptionApplied; // Handle, AppliedAt
public event SubscriptionFailedEventHandler? SubscriptionFailed;   // Handle, ErrorMessage, FailedAt
public event RowChangedEventHandler? RowChanged;                   // TableName, ChangeType, OldRow?, NewRow?

// Methods
public SubscriptionHandle Subscribe(string[] querySqls);           // call after Connected state
public void Unsubscribe(SubscriptionHandle handle);                // safe when not connected, idempotent
public IEnumerable<object> GetRows(string tableName);              // call after SubscriptionApplied
```

**`ConnectionOpenedEvent` fields:**
```csharp
public string Host { get; set; }
public string Database { get; set; }
public string Identity { get; set; }        // empty for anonymous until server assigns
public DateTimeOffset ConnectedAt { get; set; }
```

**`SubscriptionAppliedEvent` fields:**
```csharp
public SubscriptionHandle Handle { get; }
public DateTimeOffset AppliedAt { get; }
```

**`SubscriptionFailedEvent` fields:**
```csharp
public SubscriptionHandle Handle { get; }
public string ErrorMessage { get; }
public DateTimeOffset FailedAt { get; }
```

**`RowChangedEvent` fields:**
```csharp
public string TableName { get; }       // PascalCase: "SmokeTest" (not "smoke_test")
public RowChangeType ChangeType { get; } // RowChangeType.Insert / Update / Delete
public object? OldRow { get; }          // null for Insert; cast to SpacetimeDB.Types.SmokeTest
public object? NewRow { get; }          // null for Delete; cast to SpacetimeDB.Types.SmokeTest
```

**`SubscriptionHandle` relevant member:**
```csharp
public SubscriptionStatus Status { get; }  // Active, Superseded, or Closed
```

**`ProjectSettingsTokenStore` (internal — same assembly):**
```csharp
// namespace: GodotSpacetime.Runtime.Auth
// Persists token to ProjectSettings key "spacetime/auth/token"
// Implements: GodotSpacetime.Auth.ITokenStore
new ProjectSettingsTokenStore()
```

**Smoke test module table:**
- SQL name: `smoke_test` (used in `Subscribe()` and `GetRows()`)
- Generated C# type: `SpacetimeDB.Types.SmokeTest` (fields: `uint Id`, `string Value`)
- RowChangedEvent.TableName for this table: `"SmokeTest"` (PascalCase)
- Subscribe query: `"SELECT * FROM smoke_test"`

### C# Namespace and Namespacing Constraints

```csharp
using GodotSpacetime.Connection;            // ConnectionState, ConnectionStatus
using GodotSpacetime.Runtime.Auth;          // ProjectSettingsTokenStore (internal, same assembly)
using GodotSpacetime.Subscriptions;         // SubscriptionHandle, SubscriptionStatus,
                                            // SubscriptionAppliedEvent, SubscriptionFailedEvent, RowChangedEvent
using GodotSpacetime;                       // SpacetimeClient (namespace root)
using System.Linq;                          // .ToList() for IEnumerable<object>
using Godot;                               // GD.Print, Node
```

The demo namespace stays `GodotSpacetime.Demo` — do not change it.

### Naming Conventions (Architecture)

- C# class name: `DemoMain` (PascalCase, unchanged)
- File name: `DemoMain.cs` (matches class name per architecture naming patterns)
- Private fields: `_camelCase` — `_subscriptionHandle`, `_client` (already established)
- Method names: `PascalCase` — `OnConnectionOpened`, `OnSubscriptionApplied`, `OnSubscriptionFailed`, `OnRowChanged`

### Test File Conventions (from Story 5.1)

Tests are static file analysis using `pathlib.Path` — no Godot runtime, no pytest fixtures:

```python
ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")
```

Test function names: `test_<file_slug>_<what_is_checked>`. All assertions include a descriptive failure message string.

### Connection Lifecycle Flow for This Story

Expected Output panel message sequence (from Story 5.2):
```
[Demo] Bootstrap ready — godot-spacetime addon enabled     ← DemoBootstrap (unchanged)
[Demo] Connection state: CONNECTING — opening a session... ← OnConnectionStateChanged
[Demo] Connection state: CONNECTED — active session ...    ← OnConnectionStateChanged
[Demo] Subscribed to smoke_test — awaiting initial sync    ← inside OnConnectionStateChanged(Connected)
[Demo] Session identity: (new — token will be stored)      ← OnConnectionOpened (first run)
[Demo] Subscription applied — N row(s) in smoke_test       ← OnSubscriptionApplied
```

On second run (session resumed):
```
[Demo] Connection state: CONNECTED — authenticated session established  ← OnConnectionStateChanged
[Demo] Session identity: <hex identity string>                          ← same identity as first run
```

### References

- Story user story and AC: `_bmad-output/planning-artifacts/epics.md`, Epic 5 § Story 5.2
- Story 5.1 (foundation): `_bmad-output/implementation-artifacts/5-1-deliver-a-sample-foundation-for-install-codegen-and-first-connection.md`
- Previous story test baseline: 1525 tests passing (from Story 5.1 senior review)
- Architecture demo structure: `_bmad-output/planning-artifacts/architecture.md` § Complete Project Directory Structure
- Architecture boundary rule (demo is consumer): `_bmad-output/planning-artifacts/architecture.md` § Architectural Boundaries
- Naming patterns: `_bmad-output/planning-artifacts/architecture.md` § Naming Patterns
- `SpacetimeClient` public surface: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- `SpacetimeSettings` (TokenStore, Credentials): `addons/godot_spacetime/src/Public/SpacetimeSettings.cs`
- `ITokenStore` public interface: `addons/godot_spacetime/src/Public/Auth/ITokenStore.cs`
- `ProjectSettingsTokenStore` (internal): `addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs`
- `ConnectionOpenedEvent`: `addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs`
- `SubscriptionAppliedEvent`: `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs`
- `SubscriptionFailedEvent`: `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionFailedEvent.cs`
- `RowChangedEvent`: `addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs`
- `SubscriptionHandle`, `SubscriptionStatus`: `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs`
- Auth token-restore logic: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` § `Connect()` (lines 78–94) and § `IConnectionEventSink.OnConnected()` (lines 255–280)
- Smoke test table type: `demo/generated/smoke_test/Types/SmokeTest.g.cs`
- Smoke test module query reference: `demo/generated/smoke_test/SpacetimeDBClient.g.cs` § `QueryBuilder.AllTablesSqlQueries()`
- Runtime lifecycle docs: `docs/runtime-boundaries.md`
- Connection lifecycle docs: `docs/connection.md`
- Quickstart (canonical setup reference): `docs/quickstart.md`
- FR5: Sample project that proves supported setup path [Source: `_bmad-output/planning-artifacts/epics.md`]
- NFR16: Reproducible onboarding path [Source: `_bmad-output/planning-artifacts/epics.md`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blockers encountered. Senior Developer Review corrected the cache-read contract, reconnect cleanup, and lifecycle/documentation mismatches before closing the story.

### Completion Notes List

- Extended `demo/DemoMain.cs` with auth token persistence (`ProjectSettingsTokenStore`), subscription to `smoke_test`, reconnect-safe subscription lifecycle handling (`ConnectionClosed`, failed-handle reset, and active-status resubscribe guard), and the reviewed PascalCase cache read via `GetRows("SmokeTest")`.
- Updated `demo/README.md` with `## Auth and Session Resume` and `## Subscription and Live State` sections documenting token persistence, session resume, the `SmokeTest` cache-read contract, restored-session status text, and the reviewed Output-panel message order.
- Expanded `tests/test_story_5_2_extend_sample_auth_subscription.py` to 66 contract tests covering the reviewed runtime contract, reconnect cleanup, and README ordering/docs alignment. All 66 story tests pass.
- Validation: `dotnet build godot-spacetime.sln -c Debug --no-restore` succeeds with 0 errors / 0 warnings; full `pytest -q` regression is green at 1591 tests.

### File List

- `demo/DemoMain.cs` — modified (Task 1; review-fixed cache-table naming and reconnect-safe subscription cleanup)
- `demo/README.md` — modified (Task 2; review-aligned lifecycle order, cache-read contract, and restored-session wording)
- `tests/test_story_5_2_extend_sample_auth_subscription.py` — created and review-expanded (Task 3; 66 contract tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — modified (status updated)

## Change Log

- 2026-04-14: Story 5.2 implemented — extended DemoMain.cs with auth token persistence, subscription lifecycle, and live row observation; added auth and subscription documentation to demo/README.md; created 43-test contract test file. All ACs satisfied.
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 2 High, 2 Medium fixed. Fixes: `DemoMain` now reads cache data through the correct PascalCase `GetRows("SmokeTest")` contract, the sample resets/resubscribes its subscription handle across disconnect/failure paths, the README/story lifecycle order now matches the actual `Connected` then `ConnectionOpened` runtime sequence, and Story 5.2 regression coverage is synced to 66 story tests / 1591 total passing. Story status set to done.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 2 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List (`_bmad-output/implementation-artifacts/tests/test-summary.md`, `_bmad-output/story-automator/orchestration-1-20260414-184146.md`).

### Findings Fixed

- HIGH: `demo/DemoMain.cs` called `GetRows("smoke_test")`, but the SDK cache boundary resolves generated `RemoteTables` members by PascalCase property name. The delivered demo would throw `InvalidOperationException` instead of showing the initial synchronized row count.
- HIGH: `demo/README.md` and the story artifact documented the Output-panel sequence as `Session identity` before `Connection state: CONNECTED ...`, but `SpacetimeConnectionService.OnConnected()` transitions to `Connected` before it emits `ConnectionOpened`. The published sample flow therefore contradicted the actual runtime lifecycle language required by AC 3.
- MEDIUM: `demo/DemoMain.cs` never cleared `_subscriptionHandle` when the session closed or the current subscription failed. After a disconnect, reconnect, or failed subscription attempt, the demo would keep a stale non-null handle and skip the next `Subscribe()` call.
- MEDIUM: `tests/test_story_5_2_extend_sample_auth_subscription.py` only asserted loose string presence, so it blessed the broken snake_case cache read and did not lock the reviewed reconnect/order behavior.

### Actions Taken

- Updated `demo/DemoMain.cs` to listen for `ConnectionClosed`, clear failed/closed handles, resubscribe when the tracked handle is no longer `Active`, and read the cache via `GetRows("SmokeTest").ToList()` while keeping the SQL subscription query on `smoke_test`.
- Updated `demo/README.md` and this story artifact to document the PascalCase cache-read contract, the reviewed `Connected` → `Subscribed` → `Session identity` output order, and the restored-token `CONNECTED — authenticated session established` status text.
- Expanded Story 5.2 contract coverage to 66 tests, including exact `GetRows("SmokeTest")` assertions, reconnect cleanup, and README message-order checks.
- Re-ran Story 5.2 validation plus a full solution regression pass, then synced the story status and sprint-status entry to `done`.

### Validation

- `pytest -q tests/test_story_5_2_extend_sample_auth_subscription.py`
- `dotnet build godot-spacetime.sln -c Debug --no-restore`
- `pytest -q`

### Reference Check

- No dedicated Story Context or Epic 5 tech-spec artifact was present; `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/architecture.md`, `docs/runtime-boundaries.md`, and the reviewed SDK source files were used as the applicable planning and standards references.
- Tech stack validated during review: Godot `.NET` sample code in C#, `.NET` `8.0+`, `pytest`, and the in-repo generated smoke-test bindings / runtime docs.
- Local reference: `demo/DemoMain.cs`
- Local reference: `demo/README.md`
- Local reference: `tests/test_story_5_2_extend_sample_auth_subscription.py`
- Local reference: `addons/godot_spacetime/src/Internal/Cache/CacheViewAdapter.cs`
- Local reference: `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`
- Local reference: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- Local reference: `docs/runtime-boundaries.md`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
