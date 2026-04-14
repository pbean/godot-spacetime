# Story 2.2: Authenticate a Client Session Through Supported Identity Flows

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Godot developer,
I want to authenticate a client session using supported SpacetimeDB identity flows,
So that my client connects as an identified user instead of an unauthenticated transport.

## Acceptance Criteria

**AC 1 — Given** valid supported authentication input for a target deployment
**When** I start an authenticated session from Godot
**Then** the SDK applies the supported token or identity flow and opens an authenticated client session
**And** the SpacetimeDB builder receives the credentials token via `WithToken()` before the connection is opened

**AC 2 — Given** a successful authenticated connection
**When** the session is established
**Then** identity or session state needed by gameplay code is surfaced through the SDK boundary
**And** `ConnectionOpenedEvent` includes an `Identity` string property containing the server-assigned identity

**AC 3 — Given** an authenticated connection attempt that the server rejects
**When** the connection fails due to credential rejection
**Then** authentication failure produces actionable status and error feedback
**And** the `ConnectionStatus` transitions to `Disconnected` with `AuthState = AuthFailed` and a message naming the failure

**AC 4 — Given** the `ConnectionAuthStatusPanel` editor panel
**When** the connection is in any state
**Then** the panel distinguishes at least `Auth Required`, `Token Restored`, and `Auth Failed` with a recommended next action
**And** each auth state includes an explicit text label (not color-only)
**And** the panel remains keyboard-navigable and usable at narrow, standard, and wide editor widths

## Tasks / Subtasks

- [x] Task 1 — Create `Public/Connection/ConnectionAuthState.cs` (AC: 1, 3, 4)
  - [x] `namespace GodotSpacetime.Connection;`
  - [x] `public enum ConnectionAuthState` with values: `None`, `AuthRequired`, `TokenRestored`, `AuthFailed`
  - [x] XML doc each value (see Dev Notes for exact wording)

- [x] Task 2 — Update `Public/Connection/ConnectionStatus.cs` (AC: 3, 4)
  - [x] Add `public ConnectionAuthState AuthState { get; set; }` property
  - [x] Update parameterized constructor `ConnectionStatus(ConnectionState state, string description)` → `ConnectionStatus(ConnectionState state, string description, ConnectionAuthState authState = ConnectionAuthState.None)`
  - [x] Assign `AuthState = authState` in the constructor body

- [x] Task 3 — Update `Public/Connection/ConnectionOpenedEvent.cs` (AC: 2)
  - [x] Add `public string Identity { get; set; } = string.Empty;`
  - [x] XML doc: "Server-assigned identity string for the authenticated session. Empty for anonymous connections."

- [x] Task 4 — Update `Public/SpacetimeSettings.cs` (AC: 1)
  - [x] Add `public string? Credentials { get; set; }` property (no `[Export]`)
  - [x] XML doc: see Dev Notes for exact wording
  - [x] Placement: after `Database`, before `TokenStore`

- [x] Task 5 — Update `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` (AC: 1, 2)
  - [x] Change `IConnectionEventSink.OnConnected(string token)` → `OnConnected(string identity, string token)`
  - [x] In `Open()`: after `WithDatabaseName`, if `settings.Credentials` is non-null/non-whitespace, add `builder = InvokeMethod(builder, "WithToken", settings.Credentials);`
  - [x] In `CreateConnectCallback()`: capture `parameterExpressions[1]` (Identity struct) and call `ToString()` via expression tree; pass identity string as first arg to `OnConnected`, token as second (see Dev Notes for exact code)

- [x] Task 6 — Update `Internal/Connection/ConnectionStateMachine.cs` (AC: 3)
  - [x] Change `Transition(ConnectionState next, string description)` → `Transition(ConnectionState next, string description, ConnectionAuthState authState = ConnectionAuthState.None)`
  - [x] Pass `authState` to `ConnectionStatus` constructor
  - [x] Add `using GodotSpacetime.Connection;` if not present

- [x] Task 7 — Update `Internal/Connection/SpacetimeConnectionService.cs` (AC: 1, 2, 3)
  - [x] Add `private bool _credentialsProvided;` field
  - [x] In `Connect()`: set `_credentialsProvided = !string.IsNullOrWhiteSpace(settings.Credentials);`
  - [x] Change `void IConnectionEventSink.OnConnected(string token)` → `void IConnectionEventSink.OnConnected(string identity, string token)`
  - [x] In `OnConnected`: determine `authState = _credentialsProvided ? ConnectionAuthState.TokenRestored : ConnectionAuthState.None`
  - [x] Update `Transition(Connected, ...)` calls to include `authState` (see Dev Notes for exact description strings)
  - [x] Update `ConnectionOpenedEvent` initializer to include `Identity = identity`
  - [x] In `OnConnectError`: when `State == Connecting && _credentialsProvided`, use `AuthFailed` state and auth-specific description (see Dev Notes)
  - [x] Add `using GodotSpacetime.Connection;` if not present (already has it)

- [x] Task 8 — Update `Editor/Status/ConnectionAuthStatusPanel.cs` (AC: 4)
  - [x] Add new labels: `_authStateLabel` and `_authActionLabel`
  - [x] In `BuildLayout()`: add `HSeparator`, `CreateFocusableLabel("Auth state:")`, `_authStateLabel`, `_authActionLabel` after the existing status labels
  - [x] In `RefreshStatus()`: call `SetAuthStatus(CurrentAuthState(), CurrentConnState())`
  - [x] Implement `private void SetAuthStatus(ConnectionAuthState auth, ConnectionState conn)` (see Dev Notes for exact text mapping)
  - [x] **Do not add** `using SpacetimeDB;` — all types must be `GodotSpacetime.*` or Godot types

- [x] Task 9 — Update `scripts/compatibility/support-baseline.json` (AC: 1)
  - [x] Append after existing `Public/Connection/` entries:
    - `{ "path": "addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs", "type": "file" }`
  - [x] Preserve ALL existing content, comments, and structure

- [x] Task 10 — Update `docs/runtime-boundaries.md` (AC: 2, 4)
  - [x] In `Connection Lifecycle — ConnectionState` section: add row for `ConnectionAuthState` (see Dev Notes)
  - [x] In `Configuration — SpacetimeSettings` table: add `Credentials` row
  - [x] In `Auth / Identity` section: add `ConnectionOpenedEvent.Identity` documentation

- [x] Task 11 — Create `tests/test_story_2_2_auth_session.py` (AC: 1–4)
  - [x] Follow `ROOT`, `_read()`, `_lines()` pattern from `tests/test_story_2_1_auth_config.py` exactly
  - [x] See Dev Notes for full test coverage list

- [ ] Review Follow-ups (AI)
  - [ ] [AI-Review][LOW] `ConnectionAuthState.AuthRequired` is defined in the enum and the panel has a match arm for it, but no state machine code path ever emits it. The default `_` arm already renders "AUTH REQUIRED" text for `None` state, making the explicit arm dead. Consider either emitting `AuthRequired` from `Connect()` when settings have no credentials, or removing the arm and relying on the default. [ConnectionAuthStatusPanel.cs:119, ConnectionStateMachine.cs]
  - [ ] [AI-Review][LOW] `OnConnectError` classifies ALL errors as `AuthFailed` when `_credentialsProvided == true`, including network errors and server-offline scenarios. AC 3 specifies "credential rejection" specifically. Distinguish auth-specific HTTP 401/403 responses from transport failures in Story 2.4. [SpacetimeConnectionService.cs:121-127]
  - [ ] [AI-Review][LOW] AUTH FAILED action text now says `Settings.TokenStore?.ClearTokenAsync()` (fixed in review). Verify wording remains accurate when Story 2.3 introduces automatic token restoration — the advice may need to mention clearing the TokenStore entry AND the Credentials field. [ConnectionAuthStatusPanel.cs:117]

- [x] Task 12 — Verify
  - [x] `python3 scripts/compatibility/validate-foundation.py` → exits 0
  - [x] `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
  - [x] `pytest tests/test_story_2_2_auth_session.py` → all pass
  - [x] `pytest -q` → full suite passes (stories 1.3–2.2 all green)

## Dev Notes

### Scope: What This Story Is and Is Not

**In scope:**
- `ConnectionAuthState` enum (new public type)
- `ConnectionStatus.AuthState` property (extends existing type)
- `ConnectionOpenedEvent.Identity` property (extends existing event)
- `SpacetimeSettings.Credentials` property (explicit token for `WithToken()` injection)
- `WithToken()` injection into the builder when `Credentials` is set
- Identity string capture from the `OnConnect` callback and surfacing via `ConnectionOpenedEvent`
- Auth-specific state transitions: `TokenRestored`, `AuthFailed`
- `ConnectionAuthStatusPanel` auth state section (Auth Required / Token Restored / Auth Failed)
- Support-baseline and docs updates

**Out of scope (belongs to Story 2.3):**
- Pre-connect token restore from `ITokenStore.GetTokenAsync()` — that is Story 2.3
- Story 2.3 will call `settings.TokenStore?.GetTokenAsync()` before calling `Open()` and inject the result via the `Credentials` path established here

**Out of scope (belongs to Story 2.4):**
- Distinguishing auth failure subtypes (expired, rejected, network)
- Recovery guidance beyond the auth-specific description string
- `ReconnectPolicy` changes for auth failures

### What Already Exists — DO NOT RECREATE

| Component | Story | File |
|-----------|-------|------|
| `ITokenStore` (3-method async interface) | 1.3 | `Public/Auth/ITokenStore.cs` |
| `SpacetimeSettings` with `Host`, `Database`, `TokenStore` | 1.9 / 2.1 | `Public/SpacetimeSettings.cs` |
| `SpacetimeClient` with `Connect()`/`Disconnect()` | 1.9 | `Public/SpacetimeClient.cs` |
| `ConnectionState` enum (4 values) | 1.9 | `Public/Connection/ConnectionState.cs` |
| `ConnectionStatus(state, description)` | 1.9 | `Public/Connection/ConnectionStatus.cs` |
| `ConnectionOpenedEvent` with Host/Database/ConnectedAt | 1.9 | `Public/Connection/ConnectionOpenedEvent.cs` |
| `SpacetimeConnectionService` with `_tokenStore`, `OnConnected(string token)` | 1.9 / 2.1 | `Internal/Connection/SpacetimeConnectionService.cs` |
| `ConnectionStateMachine.Transition(state, description)` | 1.9 | `Internal/Connection/ConnectionStateMachine.cs` |
| `SpacetimeSdkConnectionAdapter.Open()` builder pattern | 1.9 | `Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` |
| `ConnectionAuthStatusPanel` (connection-only, no auth states) | 1.9 | `Editor/Status/ConnectionAuthStatusPanel.cs` |
| `MemoryTokenStore`, `ProjectSettingsTokenStore`, `TokenRedactor` | 2.1 | `Internal/Auth/*.cs` |

### Confirmed SpacetimeDB SDK API (SpacetimeDB.ClientSDK 2.1.0)

**Builder methods (confirmed via reflection):**
```
DbConnectionBuilder<T>.WithToken(String token)   ← USE THIS for credentials injection
DbConnectionBuilder<T>.WithUri(String uri)
DbConnectionBuilder<T>.WithDatabaseName(String nameOrAddress)
DbConnectionBuilder<T>.OnConnect(ConnectCallback cb)
DbConnectionBuilder<T>.Build()
```

**`OnConnect` callback delegate signature (confirmed):**
```
ConnectCallback: (DbConnection conn, Identity identity, String token) -> Void
```
- Parameter index 0: `DbConnection` connection (SpacetimeDB type — discard in expression)
- Parameter index 1: `SpacetimeDB.Identity` struct — convert to string via `.ToString()`
- Parameter index 2 (last): `String` token — pass to `OnConnected` as-is

**`SpacetimeDB.Identity`:**
- `IsValueType = true` (struct)
- `ToString()` returns the identity string representation
- MUST NOT cross the `Internal/Platform/DotNet/` isolation boundary as a typed value

### `SpacetimeSdkConnectionAdapter.cs` — Exact Changes Required

**Step 1 — Update `IConnectionEventSink` interface** (inside the same file):
```csharp
internal interface IConnectionEventSink
{
    void OnConnected(string identity, string token);    // ← ADD identity param
    void OnConnectError(Exception error);
    void OnDisconnected(Exception? error);
}
```

**Step 2 — In `Open()`, inject credentials after `WithDatabaseName` and before callbacks:**
```csharp
builder = InvokeMethod(builder, "WithUri", NormalizeUri(settings.Host));
builder = InvokeMethod(builder, "WithDatabaseName", settings.Database);

// Story 2.2: inject credentials token when provided
if (!string.IsNullOrWhiteSpace(settings.Credentials))
    builder = InvokeMethod(builder, "WithToken", settings.Credentials);

builder = InvokeMethod(builder, "OnConnect", CreateConnectCallback(builder, sink));
```

**Step 3 — `CreateConnectCallback()` — capture identity AND token:**
```csharp
private static Delegate CreateConnectCallback(object builder, IConnectionEventSink sink)
{
    var delegateType = GetCallbackType(builder, "OnConnect");
    var invoke = delegateType.GetMethod("Invoke")
        ?? throw new InvalidOperationException("Generated OnConnect callback is missing an Invoke method.");
    var parameters = invoke.GetParameters();
    var parameterExpressions = CreateParameters(parameters);
    var sinkExpression = Expression.Constant(sink);

    // param[1] = SpacetimeDB.Identity struct; call ToString() to cross the isolation boundary
    var identityExpression = parameterExpressions[1];
    var toStringMethod = identityExpression.Type.GetMethod("ToString", Type.EmptyTypes)
        ?? typeof(object).GetMethod("ToString", Type.EmptyTypes)!;
    var identityStringExpression = Expression.Call(identityExpression, toStringMethod);

    // param[^1] = string token (last parameter)
    var tokenExpression = parameterExpressions[^1];

    var body = Expression.Call(
        sinkExpression,
        typeof(IConnectionEventSink).GetMethod(nameof(IConnectionEventSink.OnConnected))!,
        identityStringExpression,
        tokenExpression
    );

    return Expression.Lambda(delegateType, body, parameterExpressions).Compile();
}
```

### `SpacetimeConnectionService.cs` — Exact Changes Required

**Add field:**
```csharp
private bool _credentialsProvided;
```
Place with the other private fields (`_tokenStore`, etc.).

**In `Connect()` — after `_tokenStore = settings.TokenStore;`:**
```csharp
_credentialsProvided = !string.IsNullOrWhiteSpace(settings.Credentials);
```

**Replace `void IConnectionEventSink.OnConnected(string token)` implementation:**
```csharp
void IConnectionEventSink.OnConnected(string identity, string token)
{
    _reconnectPolicy.Reset();
    if (_tokenStore != null)
    {
        // Optional token persistence must never break a successful connection.
        try
        {
            _ = _tokenStore.StoreTokenAsync(token).ContinueWith(
                static completedTask => _ = completedTask.Exception,
                CancellationToken.None,
                TaskContinuationOptions.OnlyOnFaulted | TaskContinuationOptions.ExecuteSynchronously,
                TaskScheduler.Default
            );
        }
        catch (Exception)
        {
        }
    }

    var authState = _credentialsProvided ? ConnectionAuthState.TokenRestored : ConnectionAuthState.None;

    if (CurrentStatus.State != ConnectionState.Connected)
    {
        var description = CurrentStatus.State == ConnectionState.Degraded
            ? "CONNECTED — active session established after recovery"
            : _credentialsProvided
                ? "CONNECTED — authenticated session established"
                : "CONNECTED — active session established";
        _stateMachine.Transition(ConnectionState.Connected, description, authState);
    }

    OnConnectionOpened?.Invoke(
        new ConnectionOpenedEvent
        {
            Host = _host,
            Database = _database,
            Identity = identity,
            ConnectedAt = DateTimeOffset.UtcNow,
        }
    );
}
```

**Replace `void IConnectionEventSink.OnConnectError(Exception error)` implementation:**
```csharp
void IConnectionEventSink.OnConnectError(Exception error)
{
    _adapter.Close();

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

    HandleDisconnectError(error);
}
```

Also add `using GodotSpacetime.Connection;` near the top if not already present (it already has `using GodotSpacetime.Auth;`).

### `ConnectionStateMachine.cs` — Exact Changes Required

**Change method signature:**
```csharp
// Before:
public void Transition(ConnectionState next, string description)

// After:
public void Transition(ConnectionState next, string description, ConnectionAuthState authState = ConnectionAuthState.None)
```

**Change body:**
```csharp
CurrentStatus = new ConnectionStatus(next, description, authState);
```

**Add using if not present:**
```csharp
using GodotSpacetime.Connection;
```

### `ConnectionAuthState.cs` — Full File Content

```csharp
namespace GodotSpacetime.Connection;

/// <summary>
/// The authentication phase of a <see cref="ConnectionStatus"/>.
/// Complements <see cref="ConnectionState"/> with auth-specific context.
/// </summary>
public enum ConnectionAuthState
{
    /// <summary>No authentication context. Anonymous connection, or a state with no auth flow in progress.</summary>
    None,

    /// <summary>Credentials are expected but not configured. Informational — used by status surfaces to guide configuration.</summary>
    AuthRequired,

    /// <summary>Provided credentials were accepted by the server. The session is authenticated.</summary>
    TokenRestored,

    /// <summary>Provided credentials were rejected. The connection did not complete due to an authentication failure.</summary>
    AuthFailed,
}
```

### `SpacetimeSettings.cs` — Exact Change Required

Add after `Database` property, before `TokenStore`:
```csharp
/// <summary>
/// Optional credentials token for authenticated sessions.
/// When set, this value is passed to <c>WithToken()</c> on the SpacetimeDB connection builder,
/// connecting as an identified user rather than an anonymous transport.
/// If null or empty (the default), the connection opens anonymously and the server assigns a new identity.
/// Story 2.3 adds automatic pre-connect restoration from <see cref="TokenStore"/>.
/// Token values are never logged raw — use <c>TokenRedactor</c> for diagnostic output.
/// </summary>
public string? Credentials { get; set; }
```

No `[Export]` — credentials are a security-sensitive value; they must be assigned via code, not the Godot editor inspector.

### `ConnectionAuthStatusPanel.cs` — Exact Changes Required

**Add fields:**
```csharp
private Label _authStateLabel = null!;
private Label _authActionLabel = null!;
```

**In `BuildLayout()` — after the `_detailLabel` line:**
```csharp
AddChild(new HSeparator());

AddChild(CreateFocusableLabel("Auth state:"));
_authStateLabel = CreateFocusableLabel();
AddChild(_authStateLabel);

_authActionLabel = CreateFocusableLabel();
AddChild(_authActionLabel);
```

**In `RefreshStatus()` — after the `SetStatus(...)` calls:**

Replace the existing `RefreshStatus()` body with:
```csharp
private void RefreshStatus()
{
    TryBindClient();

    if (_client == null)
    {
        _autoloadLabel.Text = "Missing";
        SetStatus(StatusNotConfigured, "Add SpacetimeClient as an autoload to observe lifecycle state here.");
        SetAuthStatus(ConnectionAuthState.None, ConnectionState.Disconnected);
        return;
    }

    _autoloadLabel.Text = "SpacetimeClient";

    if (_client.Settings == null
        || string.IsNullOrWhiteSpace(_client.Settings.Host)
        || string.IsNullOrWhiteSpace(_client.Settings.Database))
    {
        SetStatus(StatusNotConfigured, "Assign a SpacetimeSettings resource with Host and Database values.");
        SetAuthStatus(ConnectionAuthState.None, ConnectionState.Disconnected);
        return;
    }

    var status = _client.CurrentStatus;
    SetStatus(MapStatus(status.State), status.Description);
    SetAuthStatus(status.AuthState, status.State);
}
```

**Add `SetAuthStatus()` method:**
```csharp
private void SetAuthStatus(ConnectionAuthState authState, ConnectionState connState)
{
    var (label, action) = authState switch
    {
        ConnectionAuthState.TokenRestored =>
            ("TOKEN RESTORED", "Session authenticated with provided credentials."),
        ConnectionAuthState.AuthFailed =>
            ("AUTH FAILED", "Credentials were rejected. Verify your token or call ClearTokenAsync() to reset."),
        ConnectionAuthState.AuthRequired =>
            ("AUTH REQUIRED", "Configure Credentials on SpacetimeSettings to connect as an identified user."),
        _ when connState == ConnectionState.Connected =>
            ("ANONYMOUS", "Connected without credentials. No persistent identity."),
        _ =>
            ("AUTH REQUIRED", "Configure Credentials or a TokenStore before connecting as an identified user."),
    };

    _authStateLabel.Text = label;
    _authActionLabel.Text = action;
}
```

**Note on `status.AuthState`**: `ConnectionStatus` is a Godot `RefCounted` partial class. The `AuthState` property is a C# property, not a `[Export]`. Access it as `status.AuthState` from within the panel code (same process, no cross-language boundary).

### `docs/runtime-boundaries.md` — Required Changes

**1. In `Connection Lifecycle` section — add table row after the `ConnectionState` table:**
```markdown
A [`ConnectionAuthState`](../addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs) enum
accompanies `ConnectionStatus` and identifies the authentication phase:

| Auth State | Meaning |
|------------|---------|
| `None` | No authentication context. Anonymous session or pre-connection state. |
| `AuthRequired` | Credentials are expected but not provided (panel guidance). |
| `TokenRestored` | Provided credentials were accepted; session is authenticated. |
| `AuthFailed` | Provided credentials were rejected; auth-specific failure. |
```

**2. In `Configuration — SpacetimeSettings` table — add row after `Database`:**
```markdown
| `Credentials` | `string?` | Optional token for authenticated sessions; passed to `WithToken()`. `null` = anonymous connection. |
```

**3. In `Auth / Identity` section — add after the token clearing paragraph:**
```markdown
**Session Identity:** When a connection opens, the server assigns or restores an identity.
The identity string is included in [`ConnectionOpenedEvent.Identity`](../addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs).
For anonymous connections, the identity is a new server-assigned value; for credential-bearing connections,
it is the identity associated with the provided token.
```

### Test File Coverage — `tests/test_story_2_2_auth_session.py`

Existence tests:
- `Public/Connection/ConnectionAuthState.cs` exists

`ConnectionAuthState.cs` content tests:
- Contains `ConnectionAuthState` enum name
- Contains `None` value
- Contains `AuthRequired` value
- Contains `TokenRestored` value
- Contains `AuthFailed` value
- No `SpacetimeDB.` references (isolation)

`ConnectionStatus.cs` content tests:
- Contains `AuthState` property

`ConnectionOpenedEvent.cs` content tests:
- Contains `Identity` property

`SpacetimeSettings.cs` content tests:
- Contains `Credentials` property
- No `[Export]` annotation near `Credentials` (security — not in Godot inspector)

`SpacetimeSdkConnectionAdapter.cs` content tests:
- Contains `WithToken` call (token injection)
- `OnConnected` interface declaration has two parameters (identity + token)
- `CreateConnectCallback` references `identityStringExpression` or `identityExpression` (identity capture)

`SpacetimeConnectionService.cs` content tests:
- Contains `_credentialsProvided` field
- Contains `ConnectionAuthState.TokenRestored`
- Contains `ConnectionAuthState.AuthFailed`
- `OnConnected` implementation has two parameters
- Contains `Identity = identity` in the event initializer

`ConnectionStateMachine.cs` content tests:
- `Transition` method signature includes `ConnectionAuthState` parameter

`ConnectionAuthStatusPanel.cs` content tests:
- Contains `_authStateLabel`
- Contains `TOKEN RESTORED` string
- Contains `AUTH FAILED` string
- Contains `AUTH REQUIRED` string
- Contains `SetAuthStatus` method name

`support-baseline.json` content tests:
- Contains `ConnectionAuthState.cs`

`docs/runtime-boundaries.md` content tests:
- Contains `ConnectionAuthState`
- Contains `Credentials` in the settings table
- Contains `ConnectionOpenedEvent.Identity` or `Identity` in the auth section

Regression guards (must still pass):
- `Public/Auth/ITokenStore.cs` still present with `GetTokenAsync`
- `SpacetimeConnectionService.cs` still has `Connect(`, `OnConnected(`, `Disconnect(`, `FrameTick(`
- `SpacetimeConnectionService.cs` still has `_tokenStore` and `StoreTokenAsync`
- `SpacetimeSdkConnectionAdapter.cs` still has `WithUri` and `WithDatabaseName`
- `tests/test_story_1_4_adapter_boundary.py` still passes (SpacetimeDB isolation)

### Namespace and Isolation Rules

- `ConnectionAuthState` uses namespace `GodotSpacetime.Connection` (matches `ConnectionState`, `ConnectionStatus`)
- `ConnectionAuthStatusPanel.cs` must NOT reference `SpacetimeDB.*`
- `SpacetimeSdkConnectionAdapter.cs` identity conversion must use `.ToString()` via expression tree — do not cast to `string` or reference `SpacetimeDB.Identity` by name outside this file
- The isolation test in `test_story_1_4_adapter_boundary.py` verifies `SpacetimeDB.` references exist ONLY in `Internal/Platform/DotNet/` — new auth code must pass this

### Verification Sequence

Run in order — each step must pass before the next:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_2_2_auth_session.py
pytest -q
```

**Troubleshooting:**
- If `dotnet build` fails with `'ConnectionAuthState' is not a valid expression term`: check `using GodotSpacetime.Connection;` is present in `ConnectionStateMachine.cs` and `SpacetimeConnectionService.cs`
- If `test_story_1_4_adapter_boundary.py` fails: the expression-tree identity conversion must NOT import `SpacetimeDB.Identity` by name — use `identityExpression.Type.GetMethod("ToString", Type.EmptyTypes)` instead of `typeof(SpacetimeDB.Identity)` 
- If build fails on `IConnectionEventSink.OnConnected` signature mismatch: ensure both the interface definition (in `SpacetimeSdkConnectionAdapter.cs`) and the implementation (in `SpacetimeConnectionService.cs`) are updated to `OnConnected(string identity, string token)`
- If `ConnectionStatus.AuthState` causes a Godot registration error: `ConnectionAuthState` must be a plain C# enum with no `[Export]`, and `ConnectionStatus.AuthState` must be a plain property — Godot handles enum properties on `RefCounted` without issues
- If panel doesn't compile on `status.AuthState`: verify `ConnectionStatus` is in scope with the new property (it's a partial class in the same namespace)

### File Locations — DO and DO NOT

**DO create:**
```
addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs
tests/test_story_2_2_auth_session.py
```

**DO modify:**
```
addons/godot_spacetime/src/Public/SpacetimeSettings.cs                (add Credentials property)
addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs       (add AuthState property)
addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs  (add Identity property)
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs  (WithToken injection, identity capture)
addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs           (auth state tracking)
addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs               (add authState param)
addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs                  (auth state display)
scripts/compatibility/support-baseline.json                            (add ConnectionAuthState.cs)
docs/runtime-boundaries.md                                             (auth state docs)
```

**DO NOT touch:**
```
addons/godot_spacetime/src/Public/Auth/ITokenStore.cs               (stable interface)
addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs         (no changes needed)
addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs
addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs
addons/godot_spacetime/src/Public/SpacetimeClient.cs                 (no changes needed — passes Settings as-is)
addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs    (Story 2.4)
addons/godot_spacetime/src/Internal/Events/GodotSignalAdapter.cs
addons/godot_spacetime/src/Editor/Setup/
addons/godot_spacetime/src/Editor/Codegen/
addons/godot_spacetime/src/Editor/Compatibility/
addons/godot_spacetime/src/Editor/Shared/
demo/**
spacetime/modules/**
scripts/codegen/**
.github/workflows/
tests/test_story_1_*.py       (only regression guards)
tests/test_story_2_1_*.py     (only regression guards)
```

### Cross-Story Awareness

- **Story 2.3** (Restore a Previous Session) will call `Settings.TokenStore?.GetTokenAsync()` before `Open()` and, if a token is returned, set it on `settings.Credentials` OR pass it directly to `Open()` before calling the adapter. The `WithToken()` injection established here is the path that Story 2.3 will complete by feeding in the persisted token.
- **Story 2.4** (Recover from Failures) will handle `AuthFailed` recovery: surfacing clear guidance for re-authentication, clearing bad state, and distinguishing auth from network failures.
- **Story 5.x** (Docs) will include credentials configuration in the quickstart path.

### Project Structure Notes

All new types follow the existing namespace-mirrors-folder pattern:
- `ConnectionAuthState.cs` → `Public/Connection/` → `GodotSpacetime.Connection` ✓
- No new folders are created; all new files go into existing directories

### References

- Story 2.2 AC and epic context: [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 2, Story 2.2]
- FR14 (authenticate via supported identity flows): [Source: `_bmad-output/planning-artifacts/epics.md` — FR map]
- NFR23, NFR24 (panel width/keyboard nav): [Source: `_bmad-output/planning-artifacts/epics.md` — NFR section]
- UX1, UX3 (auth status surface, explicit lifecycle language): [Source: `_bmad-output/planning-artifacts/epics.md` — UX section]
- Architecture auth section (OIDC/JWT, `WithToken`, explicit lifecycle enums): [Source: `_bmad-output/planning-artifacts/architecture.md` — Authentication & Security, State Management Patterns]
- Architecture file structure: [Source: `_bmad-output/planning-artifacts/architecture.md` — Complete Project Directory Structure]
- `DbConnectionBuilder.WithToken(String)` confirmed: reflection inspection of `SpacetimeDB.ClientSDK 2.1.0`
- `OnConnect` callback: `(DbConnection conn, Identity identity, String token)` confirmed: reflection inspection of `SpacetimeDB.ClientSDK 2.1.0`
- `SpacetimeDB.Identity` is a value type with `ToString()`: confirmed via reflection
- Story 2.1 dev notes (connection auth phases are Story 2.2, ITokenStore wiring foundation): [Source: `_bmad-output/implementation-artifacts/spec-2-1-define-auth-configuration-and-token-storage-boundaries.md`]
- Epic 1 retro (verify third-party APIs before writing ACs, editor panel verification): [Source: `_bmad-output/implementation-artifacts/epic-1-retro-2026-04-14.md`]
- Isolation boundary rule: [Source: `tests/test_story_1_4_adapter_boundary.py`]
- Test file pattern: [Source: `tests/test_story_2_1_auth_config.py`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Created `ConnectionAuthState.cs` enum with four values (None, AuthRequired, TokenRestored, AuthFailed) in `GodotSpacetime.Connection` namespace, no SpacetimeDB references.
- Updated `ConnectionStatus` constructor to accept optional `ConnectionAuthState authState` parameter; `AuthState` property added.
- Added `Identity` property to `ConnectionOpenedEvent` with XML doc.
- Added `Credentials` property to `SpacetimeSettings` (no `[Export]`, placed after `Database`, before `TokenStore`) with full XML doc explaining security sensitivity.
- Updated `IConnectionEventSink.OnConnected` interface from `(string token)` to `(string identity, string token)` in `SpacetimeSdkConnectionAdapter.cs`.
- Added `WithToken` injection in `Open()` when `settings.Credentials` is non-null/non-whitespace.
- Updated `CreateConnectCallback()` to capture `parameterExpressions[1]` (SpacetimeDB.Identity struct), call `ToString()` via expression tree to cross the isolation boundary, and pass identity string + token to `OnConnected`.
- Updated `ConnectionStateMachine.Transition()` to accept optional `ConnectionAuthState authState` and pass it to `ConnectionStatus` constructor.
- Updated `SpacetimeConnectionService`: added `_credentialsProvided` field; sets it in `Connect()`; updated `OnConnected(string identity, string token)` to determine `authState = _credentialsProvided ? TokenRestored : None`, uses auth-aware description strings, sets `Identity = identity` in event; updated `OnConnectError` to transition with `AuthFailed` when credentials were provided.
- Updated `ConnectionAuthStatusPanel`: added `_authStateLabel` and `_authActionLabel` fields; extended `BuildLayout()` with HSeparator and auth state section; replaced `RefreshStatus()` body to call `SetAuthStatus()`; added `SetAuthStatus()` method with TOKEN RESTORED / AUTH FAILED / AUTH REQUIRED / ANONYMOUS labels.
- Added `ConnectionAuthState.cs` path to `support-baseline.json`.
- Updated `docs/runtime-boundaries.md`: added `ConnectionAuthState` table after ConnectionState table; added `Credentials` row to SpacetimeSettings table; added Session Identity paragraph in Auth section.
- Created `tests/test_story_2_2_auth_session.py` with 53 tests covering all ACs and regression guards; all pass.
- All verifications passed: `validate-foundation.py` → ok, `dotnet build` → 0 errors 0 warnings, `pytest test_story_2_2` → 53/53, `pytest -q` → 585/585.

### File List

- `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs` (created)
- `addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs` (modified)
- `addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs` (modified)
- `addons/godot_spacetime/src/Public/SpacetimeSettings.cs` (modified)
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` (modified)
- `addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs` (modified)
- `addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs` (modified)
- `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs` (modified)
- `scripts/compatibility/support-baseline.json` (modified)
- `docs/runtime-boundaries.md` (modified)
- `tests/test_story_2_2_auth_session.py` (created)

## Change Log

- 2026-04-14: Story 2.2 implemented — ConnectionAuthState enum, auth state tracking in ConnectionStatus/StateMachine/ConnectionService, Identity surfaced via ConnectionOpenedEvent, WithToken credentials injection in adapter, ConnectionAuthStatusPanel auth state section, support-baseline and docs updates. 53 new tests added; 585 total passing.
- 2026-04-14: Senior Developer Review (AI) — 0 Critical, 0 High, 2 Medium fixed, 3 Low tracked as action items. Fixes: Completion Notes test count corrected (40→53, 572→585); AUTH FAILED panel action text clarified to reference `Settings.TokenStore?.ClearTokenAsync()`. Story status set to done.
