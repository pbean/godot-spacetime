# Migration, Upgrade, and Concept-Mapping Guide

This guide covers three topics for adopters and upgraders: upgrading between SDK releases, migrating from the community plugin or custom protocol work, and understanding how the Godot-facing model maps to official SpacetimeDB concepts.

The canonical end-to-end implementation path is in `demo/README.md` and `demo/DemoMain.cs`. All public API terms used below are defined in `docs/runtime-boundaries.md`. The declared supported version baseline is in `docs/compatibility-matrix.md`.

## Upgrade Path Between SDK Releases

Each SDK release declares its exact supported Godot and SpacetimeDB versions in `docs/compatibility-matrix.md`. Verify your environment against the target release's baseline before upgrading.

1. Replace the `addons/godot_spacetime/` folder with the new SDK version.
2. Confirm your Godot and `.NET SDK` versions satisfy the declared baseline in `docs/compatibility-matrix.md`.
3. Run `bash scripts/codegen/generate-smoke-test.sh` to regenerate bindings against the current module.
4. Check the `"Spacetime Compat"` panel. If it shows `INCOMPATIBLE`, resolve using the instructions in `docs/compatibility-matrix.md` and `docs/troubleshooting.md`.
5. Run `python3 scripts/compatibility/validate-foundation.py` to confirm the environment baseline still passes.

If a release changes a public type name or signal signature, the release notes for that version state the required migration action. See `docs/compatibility-matrix.md` for the full declared baseline.

## Migration from the Community Plugin

The SpacetimeDB community Godot plugin provided a thin C# wrapper around `SpacetimeDB.ClientSDK`. This SDK introduces Godot-native abstractions that replace those low-level wiring steps.

### Configuration and Connection

| Community plugin | This SDK |
|---|---|
| `DbConnection.Builder().WithUri(...).WithModuleName(...).Build()` | Register `SpacetimeClient` as an autoload; assign a `SpacetimeSettings` resource with `Host` and `Database` |
| `connection.Connect()` with manual `FrameTick()` calls | `SpacetimeClient.Connect()` — lifecycle is managed via `_Process()` internally; no manual tick required |
| Direct token string on the connection builder | Assign an `ITokenStore` implementation to `Settings.TokenStore` before calling `Connect()` |

### Subscriptions

| Community plugin | This SDK |
|---|---|
| `connection.SubscriptionBuilder().OnApplied(...).Subscribe(new[] { query })` | `SpacetimeClient.Subscribe(new[] { query })` returns a `SubscriptionHandle`; connect the `SubscriptionApplied` and `SubscriptionFailed` signals |
| `SubscriptionHandle` applied callback | `SpacetimeClient.SubscriptionApplied` signal (`SubscriptionAppliedEvent` argument) |
| `SubscriptionHandle` error callback | `SpacetimeClient.SubscriptionFailed` signal (`SubscriptionFailedEvent` argument; inspect `ErrorMessage`) |

### Reducers

| Community plugin | This SDK |
|---|---|
| `connection.Reducers.Ping()` (generated static method call) | `SpacetimeClient.InvokeReducer(new SpacetimeDB.Types.Reducer.Ping())` — pass a generated `IReducerArgs` instance |
| Reducer success callback | `SpacetimeClient.ReducerCallSucceeded` signal (`ReducerCallResult` argument) |
| Reducer error callback | `SpacetimeClient.ReducerCallFailed` signal (`ReducerCallError` argument; inspect `FailureCategory`) |

### Cache Access

| Community plugin | This SDK |
|---|---|
| `connection.Db.SmokeTest.Iter()` (direct `RemoteTables` access) | `SpacetimeClient.GetRows("SmokeTest")` returns `IEnumerable<object>`; cast each item to the generated row type (e.g., `SmokeTest`) |
| Row update callbacks on generated table handles | `SpacetimeClient.RowChanged` signal (`RowChangedEvent` argument; `TableName` identifies the table) |

Any `connection.Db.*` cache walk from the community plugin maps to the same public SDK surface: `SpacetimeClient.GetRows("TableName")` against the generated PascalCase table name.

`GetRows()` is the supported public cache-access path. The underlying `RemoteTables` type is an internal implementation detail and must not be accessed directly from gameplay code. See `docs/runtime-boundaries.md` for the full cache model.

## Migration from Custom Protocol Work

If your existing integration uses raw `SpacetimeDB.ClientSDK` or a direct WebSocket connection to SpacetimeDB, the migration path is:

1. Remove the manual WebSocket or raw `SpacetimeDB.ClientSDK` connection code.
2. Add the `addons/godot_spacetime/` plugin and register `SpacetimeClient` as an autoload.
3. Assign a `SpacetimeSettings` resource with your `Host`, `Database`, and (optionally) `TokenStore`.
4. Run code generation via the `"Spacetime Codegen"` panel or `bash scripts/codegen/generate-smoke-test.sh` to get typed bindings.
5. Replace manual event handling with Godot signal connections on `SpacetimeClient` (`ConnectionStateChanged`, `SubscriptionApplied`, `SubscriptionFailed`, `ReducerCallSucceeded`, `ReducerCallFailed`, `RowChanged`).
6. Replace manual table reads with `SpacetimeClient.GetRows("TableName")`.
7. Replace direct reducer calls with `SpacetimeClient.InvokeReducer(new Reducer.X())`.

The complete end-to-end wiring path is demonstrated in `demo/README.md` and `demo/DemoMain.cs`.

## Godot SDK Model and SpacetimeDB Concepts

The Godot-facing API wraps SpacetimeDB's connection and event model in Godot-native patterns. The table below maps official SpacetimeDB concepts to their equivalents in this SDK:

| SpacetimeDB concept | This SDK | Reference |
|---|---|---|
| `DbConnection` (connection to a database) | `SpacetimeClient` autoload (`Node`) | `docs/runtime-boundaries.md` — Connection |
| `DbConnection.Builder()` configuration | `SpacetimeSettings` resource (`Host`, `Database`, `Credentials`, `TokenStore`) | `docs/runtime-boundaries.md` — SpacetimeClient |
| `DbConnection.Connect()` / `FrameTick()` | `SpacetimeClient.Connect()` (lifecycle advanced via `_Process()`) | `docs/connection.md` |
| `DbConnection.SubscriptionBuilder().Subscribe()` | `SpacetimeClient.Subscribe(string[])` returning `SubscriptionHandle` | `docs/runtime-boundaries.md` — Subscriptions |
| Subscription applied callback | `SpacetimeClient.SubscriptionApplied` signal (`SubscriptionAppliedEvent`) | `docs/runtime-boundaries.md` — Subscriptions |
| Subscription error callback | `SpacetimeClient.SubscriptionFailed` signal (`SubscriptionFailedEvent.ErrorMessage`) | `docs/runtime-boundaries.md` — Subscriptions |
| `DbContext.RemoteTables.*` (table cache access) | `SpacetimeClient.GetRows("TableName")` → `IEnumerable<object>` | `docs/runtime-boundaries.md` — Cache |
| Row update callbacks | `SpacetimeClient.RowChanged` signal (`RowChangedEvent`) | `docs/runtime-boundaries.md` — Cache |
| `connection.Reducers.X()` (generated method) | `SpacetimeClient.InvokeReducer(new Reducer.X())` where `Reducer.X` implements `IReducerArgs` | `docs/runtime-boundaries.md` — Reducer Invocation |
| Reducer success callback | `SpacetimeClient.ReducerCallSucceeded` signal (`ReducerCallResult`) | `docs/runtime-boundaries.md` — Reducer Error Model |
| Reducer error callback | `SpacetimeClient.ReducerCallFailed` signal (`ReducerCallError.FailureCategory`) | `docs/runtime-boundaries.md` — Reducer Error Model |
| Auth token / session identity | `ITokenStore` (assigned to `Settings.TokenStore`) | `docs/runtime-boundaries.md` — Auth / Identity |
| Connection lifecycle events | `SpacetimeClient.ConnectionStateChanged` signal (`ConnectionStatus.State`) | `docs/runtime-boundaries.md` — Connection Lifecycle |

## Multi-Runtime Product Model

This SDK was designed for a multi-runtime future. The `.NET` runtime is the first delivery; a native `GDScript` runtime is planned as a future phase.

**Scene wiring is runtime-stable**

Signal names (`ConnectionStateChanged`, `SubscriptionApplied`, `SubscriptionFailed`, `ReducerCallSucceeded`, `ReducerCallFailed`, `RowChanged`), the autoload path, and the `SpacetimeSettings` resource are defined at the Godot-concept level. When `GDScript` support ships, these surfaces will remain stable. Adopters will not need to rewire their scenes or change their signal connections.

**The public concept model is Godot-native**

The types in `docs/runtime-boundaries.md` — `ConnectionState`, `ConnectionStatus`, `SubscriptionHandle`, `IReducerArgs`, `ITokenStore` — are defined in Godot-facing terms, not as direct `.NET` SDK types. The mental model therefore transfers to a future `GDScript` runtime path without redesign.

The formal requirements behind this design decision are FR39–FR42 and NFR20–NFR22 in `_bmad-output/planning-artifacts/prd.md`.

## See Also

- `docs/runtime-boundaries.md` — Complete public API vocabulary: all lifecycle states, signals, auth model, subscriptions, cache, and the reducer error model
- `docs/compatibility-matrix.md` — Declared supported version baseline; the authoritative reference for upgrade verification
- `docs/install.md` — Installation prerequisites and initial setup
- `docs/quickstart.md` — Step-by-step first-setup workflow
- `docs/troubleshooting.md` — Common failure modes and recovery actions for installation, codegen, connection, auth, subscriptions, and reducers
- `demo/README.md` — Canonical end-to-end sample demonstrating the complete SDK workflow
