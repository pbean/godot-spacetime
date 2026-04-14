# Story 1.9: Configure and Open a First Connection from Godot

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Godot developer,
I want to configure connection settings and observe lifecycle events from Godot,
so that I can verify the SDK connects to my target SpacetimeDB deployment.

## Acceptance Criteria

**AC 1 — Given** valid generated bindings and a `SpacetimeSettings` resource with a valid Host and Database,
**When** `SpacetimeClient.Connect()` is called,
**Then** the SDK transitions through `Connecting` → `Connected` lifecycle states and emits the appropriate signals.

**AC 2 — Given** any connection lifecycle transition,
**When** the state changes,
**Then** `connection_state_changed(ConnectionStatus)` is emitted with an explicit named state (`Disconnected`, `Connecting`, `Connected`, or `Degraded`) and a human-readable description — never a color-only indicator.

**AC 3 — Given** invalid or incomplete settings (blank Host or Database),
**When** `Connect()` is called,
**Then** the SDK produces actionable feedback identifying the blocking field and does NOT attempt a network connection.

**AC 4 — Given** a running connection,
**When** `SpacetimeClient.Disconnect()` is called,
**Then** the SDK transitions to `Disconnected` and emits `connection_state_changed`.

**AC 5 — Given** the Godot editor has the plugin enabled,
**When** the plugin is active,
**Then** a `"Spacetime Status"` bottom panel (`ConnectionAuthStatusPanel`) displays the current connection state with explicit text labels (no color-only cues) and keyboard-navigable controls.

**AC 6 — Given** an active connection session,
**When** `connection.opened` fires,
**Then** `ConnectionOpenedEvent` is emitted as a Godot signal with the connecting Host and Database in its payload.

**AC 7 — Given** the connection service boundary,
**When** inspecting ownership of `DbConnection` and `FrameTick()`,
**Then** both are encapsulated entirely inside `Internal/` — no scene node or `Public/` type holds a raw `SpacetimeDB.*` reference.

## Tasks / Subtasks

- [x] Task 1 — Implement `SpacetimeClient` runtime behavior (AC: 1, 2, 3, 4, 6)
  - [x] Add `[Export] public SpacetimeSettings? Settings { get; set; }` property
  - [x] Add `Connect()` method: validates Settings, delegates to `SpacetimeConnectionService`, emits `connection_state_changed`
  - [x] Add `Disconnect()` method: delegates to `SpacetimeConnectionService`, emits `connection_state_changed`
  - [x] Wire `_Process(double delta)` to call `SpacetimeConnectionService.FrameTick()` when connected
  - [x] Declare `[Signal] delegate void ConnectionStateChangedEventHandler(ConnectionStatus status)` 
  - [x] Declare `[Signal] delegate void ConnectionOpenedEventHandler(ConnectionOpenedEvent e)` 
  - [x] Update summary doc comment to reflect working implementation (remove "stub" language)

- [x] Task 2 — Implement `Internal/Connection/SpacetimeConnectionService.cs` (AC: 1, 2, 3, 4, 7)
  - [x] Owns `ConnectionStateMachine` and `SpacetimeSdkConnectionAdapter`
  - [x] Exposes `Connect(SpacetimeSettings settings)`, `Disconnect()`, `FrameTick()`
  - [x] Validates settings before delegating to adapter: blank Host or Database → `ArgumentException` with field name
  - [x] Fires C# events: `OnStateChanged(ConnectionStatus)`, `OnConnectionOpened(ConnectionOpenedEvent)`
  - [x] `SpacetimeClient` subscribes to these events and re-emits as Godot signals

- [x] Task 3 — Implement `Internal/Connection/ConnectionStateMachine.cs` (AC: 1, 2, 4)
  - [x] Manages valid transitions: `Disconnected → Connecting → Connected`, `Connected → Degraded`, `* → Disconnected`
  - [x] Exposes `Transition(ConnectionState next, string description)` — raises `InvalidOperationException` for illegal transitions
  - [x] Raises `StateChanged` event on each valid transition, passing a `ConnectionStatus` snapshot

- [x] Task 4 — Implement `Internal/Connection/ReconnectPolicy.cs` (AC: 2)
  - [x] Centralizes reconnect and retry logic (exponential backoff)
  - [x] Called by `SpacetimeConnectionService` when state degrades; gameplay code never implements its own retry loops
  - [x] Configurable max attempts; default = 3

- [x] Task 5 — Implement `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` (AC: 1, 7)
  - [x] Implement `Open(SpacetimeSettings settings)`: use the `DbConnection.Builder()` pattern from `SpacetimeDB.ClientSDK 2.1.0`
    - Builder wires `.WithUri($"wss://{settings.Host}")`, `.WithModuleName(settings.Database)`, `.OnConnect(...)`, `.OnDisconnect(...)`, `.OnError(...)` callbacks
    - Callbacks invoke `IConnectionEventSink` (an interface implemented by `SpacetimeConnectionService`) so the adapter stays decoupled
  - [x] Implement `FrameTick()`: calls `_dbConnection!.FrameTick()` — called every frame by `SpacetimeClient._Process()`
  - [x] Implement `Close()`: calls `_dbConnection?.Disconnect()` if not already null
  - [x] Remove `#pragma warning disable CS0169` stubs; `_dbConnection` is now actively managed
  - [x] This is the ONLY file in the codebase that imports `SpacetimeDB.*` types directly

- [x] Task 6 — Implement `Internal/Events/GodotSignalAdapter.cs` (AC: 2, 6)
  - [x] Receives C# events from `SpacetimeConnectionService` and marshals them to the Godot main thread
  - [x] Uses `Callable.From()` or `Godot.CallDeferred` if callbacks arrive off the main thread from the SDK
  - [x] Referenced by `SpacetimeClient` to bridge domain events to Godot signals

- [x] Task 7 — Update `Public/Connection/ConnectionOpenedEvent.cs` (AC: 6)
  - [x] Add `string Host` and `string Database` properties (values from `SpacetimeSettings` at connect time)
  - [x] Add `DateTimeOffset ConnectedAt` timestamp property
  - [x] Keep class non-static and default-constructible for Godot signal compatibility

- [x] Task 8 — Add `Editor/Status/ConnectionAuthStatusPanel` (AC: 5)
  - [x] Create `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs` — `#if TOOLS`, `[Tool]`, `VBoxContainer` root
  - [x] Follow EXACT pattern from `CompatibilityPanel.cs`: `BuildLayout()` in `_Ready()`, `RefreshStatus()`, explicit text constants
  - [x] Status states (text-only, no color-only cues):
    - `"DISCONNECTED — not connected to SpacetimeDB"` (StatusDisconnected)
    - `"CONNECTING — connection attempt in progress"` (StatusConnecting)
    - `"CONNECTED — active session established"` (StatusConnected)
    - `"DEGRADED — session experiencing issues; reconnecting"` (StatusDegraded)
    - `"NOT CONFIGURED — assign a SpacetimeSettings resource"` (StatusNotConfigured)
  - [x] Panel observes `SpacetimeClient` autoload (if present in scene tree) via `GetTree().Root.GetNodeOrNull<SpacetimeClient>("SpacetimeClient")`
  - [x] If `SpacetimeClient` not present: show `StatusNotConfigured`
  - [x] Apply `FocusModeEnum.All`, `AutowrapMode.WordSmart`, `CustomMinimumSize` — same as prior panels
  - [x] Create `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn` — minimal `VBoxContainer`-root scene
  - [x] Register in `GodotSpacetimePlugin.cs` as third panel (`"Spacetime Status"`) — follow existing compat panel block as template

- [x] Task 9 — Update `GodotSpacetimePlugin.cs` (AC: 5)
  - [x] Add `using GodotSpacetime.Editor.Status;` inside `#if TOOLS` block
  - [x] Add `private const string StatusPanelScenePath = "res://addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn";`
  - [x] Add `private ConnectionAuthStatusPanel? _statusPanel;`
  - [x] Add status panel registration block in `_EnterTree()` after compat block (same if/else structure)
  - [x] Add status panel cleanup block in `_ExitTree()` before compat cleanup (LIFO order)

- [x] Task 10 — Update `support-baseline.json` and docs (AC: 5)
  - [x] Add to `required_paths`:
    - `{ "path": "addons/godot_spacetime/src/Editor/Status", "type": "dir" }`
    - `{ "path": "addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs", "type": "file" }`
    - `{ "path": "addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn", "type": "file" }`
    - `{ "path": "addons/godot_spacetime/src/Internal/Connection", "type": "dir" }`
    - `{ "path": "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs", "type": "file" }`
    - `{ "path": "addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs", "type": "file" }`
    - `{ "path": "addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs", "type": "file" }`
    - `{ "path": "addons/godot_spacetime/src/Internal/Events", "type": "dir" }`
    - `{ "path": "addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs", "type": "file" }`
    - `{ "path": "docs/connection.md", "type": "file" }`
  - [x] Add to `line_checks` (for `docs/connection.md`):
    - `{ "file": "docs/connection.md", "label": "Connection lifecycle section heading", "expected_line": "## Connection Lifecycle" }`
  - [x] Create `docs/connection.md` with a `## Connection Lifecycle` section explaining the four states and signal names
  - [x] Add `docs/connection.md` reference to `docs/install.md` and `docs/codegen.md` "see also" sections (if applicable)

- [x] Task 11 — Create `tests/test_story_1_9_connection.py` (AC: 1–7)
  - [x] Follow `ROOT`, `_read()`, `_lines()` pattern from Story 1.8 test
  - [x] Existence tests: all new `.cs` and `.tscn` files exist
  - [x] `SpacetimeClient.cs` tests:
    - Contains `Connect(` (method present)
    - Contains `Disconnect(` (method present)
    - Contains `ConnectionStateChanged` (signal declaration)
    - Contains `ConnectionOpened` (signal declaration)
    - Contains `FrameTick` or `_Process` (advancement wired)
    - Contains `SpacetimeSettings` (settings property or type reference)
  - [x] `SpacetimeConnectionService.cs` tests:
    - Contains `Connect(`
    - Contains `Disconnect(`
    - Contains `FrameTick(`
    - Contains `OnStateChanged` or `StateChanged`
    - Contains `OnConnectionOpened` or `ConnectionOpened`
  - [x] `ConnectionStateMachine.cs` tests:
    - Contains `Transition(`
    - Contains `Disconnected` and `Connecting` and `Connected` and `Degraded`
    - Contains `StateChanged`
  - [x] `SpacetimeSdkConnectionAdapter.cs` tests:
    - Contains `DbConnection.Builder` or `WithUri` (SDK builder used)
    - Contains `FrameTick`
    - Does NOT contain `#pragma warning disable CS0169` (stub stubs removed)
  - [x] `ConnectionOpenedEvent.cs` tests:
    - Contains `Host`
    - Contains `Database`
    - Contains `ConnectedAt`
  - [x] Editor panel tests (same text-constant pattern as 1.8):
    - `ConnectionAuthStatusPanel.cs` contains `"DISCONNECTED — not connected to SpacetimeDB"`
    - `ConnectionAuthStatusPanel.cs` contains `"CONNECTING — connection attempt in progress"`
    - `ConnectionAuthStatusPanel.cs` contains `"CONNECTED — active session established"`
    - `ConnectionAuthStatusPanel.cs` contains `"DEGRADED — session experiencing issues; reconnecting"`
    - `ConnectionAuthStatusPanel.cs` contains `"NOT CONFIGURED — assign a SpacetimeSettings resource"`
    - `ConnectionAuthStatusPanel.cs` contains `FocusModeEnum.All`
    - `ConnectionAuthStatusPanel.cs` contains `AutowrapMode`
    - `ConnectionAuthStatusPanel.cs` contains `CustomMinimumSize`
  - [x] Plugin registration tests:
    - `GodotSpacetimePlugin.cs` contains THREE occurrences of `AddControlToBottomPanel`
    - `GodotSpacetimePlugin.cs` contains `"Spacetime Status"`
    - `GodotSpacetimePlugin.cs` contains `ConnectionAuthStatusPanel`
  - [x] support-baseline.json tests:
    - Contains `addons/godot_spacetime/src/Editor/Status`
    - Contains `ConnectionAuthStatusPanel.cs`
    - Contains `addons/godot_spacetime/src/Internal/Connection`
    - Contains `docs/connection.md`
  - [x] docs/connection.md tests:
    - Contains `Connection Lifecycle` section heading
    - Contains `Disconnected` and `Connecting` and `Connected` and `Degraded`
    - Contains `connection_state_changed` (signal name)
  - [x] Regression guards — Stories 1.7 and 1.8 panels still present and registered
  - [x] Regression guard: `SpacetimeSdkConnectionAdapter.cs` still in `Internal/Platform/DotNet/` (boundary intact)

- [x] Task 12 — Verify
  - [x] `python3 scripts/compatibility/validate-foundation.py` → exits 0
  - [x] `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
  - [x] `pytest tests/test_story_1_9_connection.py` → all pass
  - [x] `pytest -q` → full suite passes (stories 1.3–1.9 all green)

## Dev Notes

### Scope and What Already Exists

Story 1.9 **activates** the connection layer. Most public contract types were stubbed in earlier stories — DO NOT recreate them, just implement them:

| File | State Before 1.9 | Action |
|------|-----------------|--------|
| `Public/SpacetimeClient.cs` | Empty Node stub | **Implement** Connect/Disconnect/signals/_Process |
| `Public/SpacetimeSettings.cs` | Has Host + Database [Export] | **No change** — complete as-is |
| `Public/Connection/ConnectionState.cs` | Complete enum | **No change** |
| `Public/Connection/ConnectionStatus.cs` | Complete record | **No change** |
| `Public/Connection/ConnectionOpenedEvent.cs` | Empty stub | **Add** Host, Database, ConnectedAt |
| `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` | Stub with `_dbConnection` field | **Implement** Open/FrameTick/Close |
| `Internal/Connection/SpacetimeConnectionService.cs` | Does not exist | **Create** |
| `Internal/Connection/ConnectionStateMachine.cs` | Does not exist | **Create** |
| `Internal/Connection/ReconnectPolicy.cs` | Does not exist | **Create** |
| `Internal/Events/GodotSignalAdapter.cs` | Does not exist | **Create** |
| `Editor/Status/ConnectionAuthStatusPanel.cs` | Does not exist | **Create** |
| `Editor/Status/ConnectionAuthStatusPanel.tscn` | Does not exist | **Create** |

### Architecture — Layer Ownership (CRITICAL)

```
SpacetimeClient (Public, autoload, Godot Node)
    │  owns FrameTick pump (_Process → service.FrameTick())
    │  emits Godot signals (connection_state_changed, connection_opened)
    │  subscribes to C# events from SpacetimeConnectionService
    ▼
SpacetimeConnectionService (Internal/Connection/)
    │  owns ConnectionStateMachine and ReconnectPolicy
    │  validates SpacetimeSettings before connecting
    │  fires C# events: OnStateChanged, OnConnectionOpened
    ▼
SpacetimeSdkConnectionAdapter (Internal/Platform/DotNet/)
    │  ONLY place that imports SpacetimeDB.* types directly
    │  implements Open(settings), FrameTick(), Close()
    │  calls ClientSDK DbConnection.Builder() pattern
    │  invokes IConnectionEventSink callbacks on lifecycle events
    ▼
SpacetimeDB.ClientSDK 2.1.0 (NuGet — network layer)
```

**Do NOT** reference `SpacetimeDB.*` types anywhere outside `Internal/Platform/DotNet/`. The existing `SpacetimeSdkReducerAdapter.cs` and `SpacetimeSdkSubscriptionAdapter.cs` are the pattern — connection adapter follows the same boundary rule.

### SpacetimeSdkConnectionAdapter — Correct ClientSDK Usage

The ClientSDK 2.1.0 uses a builder pattern. The adapter's `Open()` method should follow this structure:

```csharp
// Inside SpacetimeSdkConnectionAdapter.Open(SpacetimeSettings settings, IConnectionEventSink sink)
_dbConnection = DbConnection.Builder()
    .WithUri($"wss://{settings.Host}")
    .WithModuleName(settings.Database)
    .OnConnect((conn, identity, token) => sink.OnConnected(identity, token))
    .OnConnectError(err => sink.OnConnectError(err))
    .OnDisconnect((conn, err) => sink.OnDisconnected(err))
    .Build();
```

Callbacks from ClientSDK may arrive on a background thread — `GodotSignalAdapter` must marshal them to the main thread via `Callable.From()` / `.CallDeferred()` before emitting Godot signals.

### SpacetimeClient — Signal Declarations for C#

Godot signal declarations in C# use the delegate pattern:

```csharp
[Signal]
public delegate void ConnectionStateChangedEventHandler(ConnectionStatus status);

[Signal]
public delegate void ConnectionOpenedEventHandler(ConnectionOpenedEvent e);
```

Emit via: `EmitSignal(SignalName.ConnectionStateChanged, status);`

GDScript consumers connect with: `SpacetimeClient.connection_state_changed.connect(_on_state_changed)`

### ConnectionStateMachine — Legal Transitions

| From | To | Description |
|------|----|-------------|
| Disconnected | Connecting | Connect() called |
| Connecting | Connected | SDK OnConnect fired |
| Connecting | Disconnected | Connection failed |
| Connected | Degraded | Session lost, auto-retrying |
| Degraded | Connected | Reconnect succeeded |
| Degraded | Disconnected | Max retries exceeded |
| Connected | Disconnected | Disconnect() called |

Illegal transitions raise `InvalidOperationException` — they signal a programming error, not a runtime fault.

### Editor Panel — ConnectionAuthStatusPanel Pattern

Follow `CompatibilityPanel.cs` EXACTLY (Story 1.8 deliverable). Key requirements:
- Class is in namespace `GodotSpacetime.Editor.Status`
- Wrapped in `#if TOOLS` / `#endif`
- Decorated with `[Tool]`
- Root is `VBoxContainer`
- `BuildLayout()` called from `_Ready()`
- `RefreshStatus()` called from `_Ready()` and on signal connect
- Text status constants as `private const string` fields
- `FocusModeEnum.All` on interactive controls
- `AutowrapMode.WordSmart` on label nodes
- `CustomMinimumSize` set for narrow panel support
- NO color as the sole status indicator

The panel should attempt `GetTree().Root.GetNodeOrNull<SpacetimeClient>("SpacetimeClient")` in `_Ready()`. If found, connect to `connection_state_changed` and call `RefreshStatus()` on each change. If not found, display `StatusNotConfigured`.

### GodotSpacetimePlugin.cs — Third Panel Registration

The compat panel block is the exact template to follow. Add status panel AFTER compat block in `_EnterTree()` and BEFORE compat cleanup in `_ExitTree()`. Three fields at class top:
- `private const string StatusPanelScenePath = "res://addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn";`
- `private ConnectionAuthStatusPanel? _statusPanel;`

After adding the status panel, `GodotSpacetimePlugin.cs` should contain exactly **three** `AddControlToBottomPanel` calls.

### File Locations — DO and DO NOT

**DO create/modify:**
```
addons/godot_spacetime/src/Public/SpacetimeClient.cs                    (implement)
addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs   (add payload)
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs  (implement)
addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs  (create)
addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs      (create)
addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs             (create)
addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs              (create)
addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs         (create)
addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn       (create)
addons/godot_spacetime/GodotSpacetimePlugin.cs                                (add 3rd panel)
scripts/compatibility/support-baseline.json                                   (add paths + line_check)
docs/connection.md                                                            (create)
tests/test_story_1_9_connection.py                                            (create)
```

**DO NOT touch:**
```
addons/godot_spacetime/src/Public/SpacetimeSettings.cs                 (complete as-is)
addons/godot_spacetime/src/Public/Connection/ConnectionState.cs        (complete as-is)
addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs       (complete as-is)
addons/godot_spacetime/src/Public/Auth/ITokenStore.cs                  (auth is Story 2.x)
addons/godot_spacetime/src/Public/Subscriptions/**                     (subscriptions Story 3.x)
addons/godot_spacetime/src/Public/Reducers/**                          (reducers Story 4.x)
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs
addons/godot_spacetime/src/Editor/Codegen/**                           (Story 1.7 — unchanged)
addons/godot_spacetime/src/Editor/Compatibility/**                     (Story 1.8 — unchanged)
demo/generated/smoke_test/**                                            (read-only generated)
spacetime/modules/**                                                    (module source)
scripts/codegen/**                                                      (codegen scripts)
docs/codegen.md                                                         (unchanged)
docs/runtime-boundaries.md                                              (unchanged)
docs/install.md                                                         (unchanged)
.github/workflows/                                                      (no CI changes)
tests/fixtures/                                                         (reserved)
```

### Namespace Conventions

- Public types: `namespace GodotSpacetime;` or `namespace GodotSpacetime.Connection;`
- Internal connection: `namespace GodotSpacetime.Runtime.Connection;` (follow `SpacetimeSdkConnectionAdapter` which uses `GodotSpacetime.Runtime.Platform.DotNet`)
- Internal events: `namespace GodotSpacetime.Runtime.Events;`
- Editor Status panel: `namespace GodotSpacetime.Editor.Status;`

### Testing Standards

Follow Story 1.8's `tests/test_story_1_8_compatibility.py` exactly:
- `ROOT = Path(__file__).resolve().parents[1]`
- `_read(rel: str) -> str` helper
- `_lines(rel: str) -> list[str]` helper
- Tests are pure static file/content checks — no dotnet execution, no Godot editor, no live network
- INCLUDE regression guards for Story 1.7 and 1.8 panel registrations in `GodotSpacetimePlugin.cs`
- Each test has a clear assertion message explaining what should have been found

### Verification Sequence

Run in order — each step must pass before the next:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_1_9_connection.py
pytest -q
```

**Troubleshooting:**
- If `dotnet build` fails with `CS0246 type not found SpacetimeConnectionService`: verify namespace and `using` directives in `SpacetimeClient.cs`
- If `dotnet build` fails with `DbConnection not found`: verify `using SpacetimeDB;` is inside `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` only — not in any other file
- If `dotnet build` fails signal declaration error: Godot signal delegates must end in `EventHandler` suffix (e.g., `ConnectionStateChangedEventHandler`) per Godot C# conventions
- If `validate-foundation.py` fails on `Editor/Status` paths: verify exact paths match what was created (`Status` not `status`)
- If compat panel test regression fires in pytest: verify `GodotSpacetimePlugin.cs` still has both `"Spacetime Codegen"` and `"Spacetime Compat"` tab labels after adding status panel

### Cross-Story Awareness

- **Story 1.10** (Validate First Setup Through a Quickstart Path) depends on 1.9's connection being functional — it will walk through the full flow from install → codegen → compatibility check → connect
- **Story 2.x** (Auth) will extend `SpacetimeSettings` with token/credential fields — leave it extension-friendly, no breaking changes to Host/Database
- `Internal/Connection/ReconnectPolicy.cs` is created this story but full reconnect logic may be deferred — the architecture boundary must exist even if the retry implementation is minimal
- `Editor/Status/ConnectionAuthStatusPanel` is named "Auth" even though auth is Story 2.x — the panel surface is shared; auth status display will be added in Story 2.x without renaming the panel

### Project Structure Notes

**Alignment with unified project structure:**
- New `Internal/Connection/` folder follows the established `Internal/Platform/DotNet/` pattern
- New `Internal/Events/` folder is explicitly named in the architecture document
- `Editor/Status/` is explicitly named in the architecture document as the next editor surface area
- All `Internal/` folders are implementation-only and never imported from `Public/`

**Detected conflicts or variances:**
- None. All paths match architecture spec exactly.

### References

- Architecture connection layer: [Source: docs/architecture.md — "Internal/Connection/", "Data Flow" sections]
- Architecture enforcement: [Source: docs/architecture.md — "Enforcement Guidelines"]
- Public API shape: [Source: docs/architecture.md — "Core Architectural Decisions — API & Communication Patterns"]
- Story 1.8 editor panel pattern: [Source: _bmad-output/implementation-artifacts/spec-1-8-detect-binding-and-schema-compatibility-problems-early.md — Dev Notes]
- Connection state transitions: [Source: _bmad-output/planning-artifacts/epics.md — Story 1.9 Technical Requirements]
- UX requirements (explicit text, keyboard nav, narrow panels): [Source: epics.md — UX1, UX2, UX3, NFR23, NFR24]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_1_9_connection.py`
- `pytest -q`

### Completion Notes List

- Implemented the connection runtime path in `SpacetimeClient`, `SpacetimeConnectionService`, `ConnectionStateMachine`, `ReconnectPolicy`, and `GodotSignalAdapter`.
- Implemented the `.NET` connection adapter with reflection-based builder wiring so the addon can discover the generated `DbConnection` type at runtime without compiling generated bindings into the addon assembly.
- Added the `Spacetime Status` editor panel, connection lifecycle documentation, support-baseline entries, and static contract coverage for Story 1.9.
- Adjusted older Story 1.3 and 1.8 regression tests so they validate the public contract and preserved panel registrations without blocking the new Godot-compatible signal payload types or third bottom panel.

### File List

- `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- `addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs`
- `addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs`
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs`
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs`
- `addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs`
- `addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs`
- `addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs`
- `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs`
- `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.tscn`
- `addons/godot_spacetime/GodotSpacetimePlugin.cs`
- `docs/connection.md`
- `docs/install.md`
- `docs/codegen.md`
- `scripts/compatibility/support-baseline.json`
- `tests/test_story_1_9_connection.py`
- `tests/test_story_1_3_sdk_concepts.py`
- `tests/test_story_1_8_compatibility.py`

## Senior Developer Review (AI)

### Reviewer

Pinkyd on 2026-04-14

### Outcome

Approved after auto-fix pass.

### Findings

- `SpacetimeClient.cs` was still a stub, so AC 1, 2, 3, 4, and 6 were not implemented.
- `SpacetimeSdkConnectionAdapter.cs` still contained only the `_dbConnection` stub and pragma suppression, so there was no runtime open/tick/close path.
- Required `Internal/Connection/*`, `Internal/Events/GodotSignalAdapter.cs`, editor status panel assets, and `docs/connection.md` were missing.
- `support-baseline.json` did not yet track the new Story 1.9 runtime/editor/doc paths.
- The story artifact was still `ready-for-dev` with an empty `File List`, so the review started from an unreviewable documentation state.
- Godot signal payload constraints rejected the original plain CLR payload types, so the public connection payloads had to be converted to Godot-compatible `RefCounted` classes.
- Full-suite regression tests from Stories 1.3 and 1.8 needed follow-up updates because they assumed the older payload declaration form and a fixed two-panel plugin layout.

### Notes

- MCP documentation search was unavailable in this session, so the SDK adapter behavior was verified against local NuGet package metadata and the generated `demo/generated/smoke_test/SpacetimeDBClient.g.cs` source instead.
- No critical issues remained after the fixes and verification pass.

## Change Log

- 2026-04-14: Senior developer review auto-fix pass completed; implemented Story 1.9 runtime/editor/docs/test deliverables, updated regression tests, and verified foundation/build/pytest status.
