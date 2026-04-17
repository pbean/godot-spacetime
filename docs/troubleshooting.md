# Troubleshooting — GodotSpacetime SDK

This guide covers common failure modes for installation, code generation, compatibility checks, connection, authentication, subscriptions, and reducers. Each section states the visible indicator, the likely cause, and the recovery action.

`demo/README.md` is the source of truth for sample behavior. `docs/runtime-boundaries.md` is the source of truth for the runtime terminology used below.

## Installation and Foundation

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| `validate-foundation.py` exits non-zero | `.NET SDK` not found, wrong Godot version, or solution restore failure | Follow the error output; confirm `.NET 8.0+` is installed and Godot `4.6.2` is the editor target |
| Build errors on plugin enable | Solution incompatible with installed `.NET SDK` | Run `python3 scripts/compatibility/validate-foundation.py` and resolve reported issues; check `docs/install.md` for the supported baseline |

The supported baseline is Godot `4.6.2`, `.NET 8.0+`, and SpacetimeDB `2.1+`. See `docs/compatibility-matrix.md` for the full declared baseline.

## Code Generation

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| `"Spacetime Codegen"` panel shows `MISSING` | Bindings have not been generated yet | Run `bash scripts/codegen/generate-smoke-test.sh` from the repository root |
| `"Spacetime Codegen"` panel shows `NOT CONFIGURED` | `spacetime/modules/smoke_test/` does not exist | Confirm the module directory exists, then rerun `bash scripts/codegen/generate-smoke-test.sh` |
| `"Generate from Server"` shows `FAILED — could not reach server: ...` | Wrong server URL, server offline, or request timeout | Check the URL, confirm the server is running, and retry once the HTTP endpoint is reachable |
| `"Generate from Server"` shows `FAILED — server requires authentication` | The server rejected anonymous HTTP access with `401` or `403` | Use an anonymously accessible local/dev server; authenticated editor fetch is not supported in this release |
| `"Generate from Server"` shows `BLOCKED — output directory outside safe boundary` | The requested output directory is not under a generated path | Change the output path to `demo/generated/...`, `tests/fixtures/generated/...`, or another directory with a `generated` path segment |
| `"Generate from Server"` shows `FAILED — spacetime CLI not found in PATH` | `spacetime` CLI not installed or not exported on `PATH` | Install the SpacetimeDB CLI `2.1+` and restart the editor so `spacetime` is discoverable |
| `"Generate from Server"` shows `FAILED — generation error (see recovery guidance)` and mentions `python3` | `python3` is not installed or not exported on `PATH` for the Godot editor process | Install `python3`, confirm `python3 --version` works in the same shell/session, then retry generation |
| `spacetime` CLI command not found | SpacetimeDB CLI not installed | Install the SpacetimeDB CLI `2.1+` |
| Native GDScript fixture bindings are missing under `tests/fixtures/gdscript_generated/smoke_test/` | Story 11.5's repo-owned emitter has not been run yet | Run `bash scripts/codegen/generate-gdscript-smoke-test.sh` from the repository root |
| Attempting `spacetime generate --lang gdscript` fails | The pinned upstream CLI has no native GDScript target | Use `bash scripts/codegen/generate-gdscript-smoke-test.sh`; it runs the supported C# frontend first and then `generate-gdscript-bindings.py` |

Running `bash scripts/codegen/generate-smoke-test.sh` clears the previous output before regenerating — no manual cleanup is required. Generated bindings are written to `demo/generated/smoke_test/`.
Running `bash scripts/codegen/generate-gdscript-smoke-test.sh` clears and regenerates the read-only GDScript fixture at `tests/fixtures/gdscript_generated/smoke_test/`.

See `docs/codegen.md` for the full generation workflow and module locations.

## Compatibility Check

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| `"Spacetime Compat"` panel shows `INCOMPATIBLE` (bindings stale) | Module source has changed since bindings were last generated | Run `bash scripts/codegen/generate-smoke-test.sh` to regenerate |
| `"Spacetime Compat"` panel shows `INCOMPATIBLE` (CLI version) | Bindings were generated with an older CLI that does not satisfy the declared `2.1+` baseline | Update the SpacetimeDB CLI to `2.1+`, then rerun `bash scripts/codegen/generate-smoke-test.sh` |

The compatibility panel reads the CLI version embedded in generated bindings and compares it against the declared baseline. If regeneration does not resolve `INCOMPATIBLE`, check the CLI version with `spacetime version` and update to `2.1+`. See `docs/compatibility-matrix.md` for the declared baseline.

## Connection

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| `"Spacetime Status"` panel shows `NOT CONFIGURED` | `SpacetimeSettings` resource not assigned to `SpacetimeClient`, or `SpacetimeClient` not registered as an autoload | Assign a `SpacetimeSettings` resource with `Host` and `Database` to the `SpacetimeClient` autoload entry in `Project > Project Settings > Autoload` |
| `"Spacetime Status"` panel shows `DISCONNECTED` after `Connect()` | `Host` or `Database` does not point to a running SpacetimeDB deployment | Verify SpacetimeDB is running at the configured `Host` and that the `Database` name matches the deployed module |
| `"Spacetime Status"` panel shows `DEGRADED` | The session hit a recoverable problem; reconnect policy is active | Wait for the reconnect policy to restore the session; check server availability if `DEGRADED` persists |
| `ArgumentException` thrown from `Connect()` | `Host` or `Database` is missing from `SpacetimeSettings` | Set both `Host` and `Database` fields before calling `Connect()` |

> **Note:** `ArgumentException` from `Connect()` is a **programming fault** — it fires synchronously before any connection attempt, not through the signal path. Set `Host` and `Database` before calling `Connect()`.

Connection lifecycle state transitions are surfaced through the `SpacetimeClient.ConnectionStateChanged` signal. See `docs/connection.md` for the complete state table and editor panel labels.

## Multi-Module Connections

Story 10.1 keeps the single-client path as the default and adds a multi-module
composition path on top of it.

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| `Connect()` fails during client registration or the project logs a duplicate-client error | duplicate client identifiers | Give each live `SpacetimeClient` a distinct `ConnectionId`; keep `SpacetimeClient` for the default client only |
| `Connect()` fails with a generated binding resolution message, or `GetDb<TDb>()` throws a wrong-type mismatch | wrong generated namespace | Set `SpacetimeSettings.GeneratedBindingsNamespace` to the namespace used when that module's bindings were generated |
| `RowReceiver` shows the wrong table dropdown or binds the wrong module | `ClientPath` points at the wrong client, or the selected client's bindings are not compiled | Point `ClientPath` at the intended client node and confirm the matching generated namespace is compiled into the project |
| `"Spacetime Status"` panel still shows only the default client while multiple clients are present | default-client-only panel behavior | This is expected in Story 10.1. Use `CurrentStatus` / `CurrentTelemetry` on the specific client instance for non-default connections |

## Telemetry

Story 9.3 adds `SpacetimeClient.CurrentTelemetry` plus Godot `Performance` custom monitor output for the core connection metrics. In Story 10.1 the custom monitor IDs remain tied to the default `SpacetimeClient` path; per-client telemetry for non-default connections still comes from each instance's `CurrentTelemetry` property.

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| `CurrentTelemetry.BytesSent` stays `0` after real reducer or subscription traffic | The session has not emitted any client request traffic yet, or the runtime proof path is not active | Drive a real `Subscribe()` or `InvokeReducer()` call, then verify `bytes_sent_proven` in the Story 9.3 harness before trusting the number |
| `Performance` monitor list does not show `GodotSpacetime/Connection/MessagesSent` | `SpacetimeClient` autoload is not in the scene tree, or the addon has not registered its custom monitor IDs yet | Confirm `SpacetimeClient` is registered as an autoload and has entered the tree before checking the monitor dock |
| Telemetry looks stale after a disconnect | The previous session ended and the metrics were reset | Re-read `CurrentTelemetry`; reset-to-zero on disconnect is the intended behavior |
| Reconnect shows a small fresh count instead of the old total | The new session has already observed fresh runtime traffic | This is expected. Story 9.3 guarantees reset semantics and a fresh measurement window, not preservation of the old totals |

The key monitor IDs are:

- `GodotSpacetime/Connection/MessagesSent`
- `GodotSpacetime/Connection/MessagesReceived`
- `GodotSpacetime/Connection/BytesSent`
- `GodotSpacetime/Connection/BytesReceived`
- `GodotSpacetime/Connection/UptimeSeconds`
- `GodotSpacetime/Reducers/LastRoundTripMilliseconds`

`ConnectionUptimeSeconds` is reported in seconds, reducer RTT is reported in milliseconds, and disconnect reset semantics are intentional.

Supported-stack caveat:

- The pinned runtime does not expose a straightforward documented outbound wire-byte counter.
- Story 9.3 therefore uses a runtime proof path based on the SDK's serialized outbound `ClientMessage` payloads.
- Repo docs treat that observed runtime proof as authoritative and do not invent a placeholder byte metric.

## Compression

Compression is opt-in through `SpacetimeSettings.CompressionMode` and defaults to `None`. The effective mode for an active session is exposed through `ConnectionStatus.ActiveCompressionMode` and mirrored in the `"Spacetime Status"` panel's `Compression:` row.

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| `"Spacetime Status"` shows `Compression: None (opt-in default)` while connected | `CompressionMode` was left at the product default | Set `SpacetimeSettings.CompressionMode` to `Gzip` or `Brotli` before calling `Connect()` if you want compressed transport |
| `"Spacetime Status"` shows `Compression: Gzip` after selecting `Brotli` | The pinned `2.1.x` client runtime currently canonicalizes `Brotli` requests to effective `Gzip` | This is the expected behavior for the supported stack; inspect `ConnectionStatus.ActiveCompressionMode` for the effective mode rather than assuming the raw request stays unchanged |

The current supported runtime did not expose a reproducible unsupported-compression failure path during Story 9.1 validation, so the addon does not add speculative retry-to-`None` fallback logic on top of the upstream SDK.

## Light Mode

`SpacetimeSettings.LightMode` is opt-in and defaults to `false`. Like the other transport-facing settings, it is read when a connection is opened; changing it while connected only affects the next connection cycle.

Story 9.2 keeps the public `RowChangedEvent`, `ReducerCallResult`, and `ReducerCallError` payloads free of synthetic reducer metadata. That means no synthetic reducer metadata fields such as caller identity or energy consumed appear on the public payloads just because `LightMode` is enabled.

The repo treats observed runtime behavior as the source of truth here because the official upgrade guide says `light_mode` was removed in `2.0`, while the pinned local `2.1.0` builder still exposes `WithLightMode(bool)`. If Story 9.2 validation on your supported stack records no observable difference between `LightMode=false` and `LightMode=true`, that no-op is the correct documented outcome for this repo rather than a missing feature to paper over.

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| Toggling `LightMode` during an active session does not change current row/reducer behavior | `LightMode` is a next-connection setting, not a live mutable session knob | Disconnect and reconnect to apply the changed value |
| Public row/reducer payloads still omit reducer metadata while `LightMode=true` | This is the intended public boundary; the SDK does not add synthetic reducer metadata fields to public payloads | Inspect the Story 9.2 integration harness for low-level callback-context observations instead of widening gameplay payloads |
| Local runtime validation shows no observable difference between `LightMode=false` and `LightMode=true` | The supported stack may currently treat `WithLightMode(bool)` as a no-op in practice | Document that observed runtime behavior and keep the public API shape unchanged |

## Reconnection Behavior

`SpacetimeClient` owns an internal `ReconnectPolicy` that engages automatically when a previously `Connected` session encounters a transport error. Scene code must **not** implement its own reconnect loop — observe `ConnectionStateChanged` and `ConnectionClosed` instead. See `docs/runtime-boundaries.md` for the ownership contract.

**Defaults for this release:**

- Retry budget: **3 attempts**
- Backoff schedule: `2^(attempt-1)` seconds → **1s, 2s, 4s**
- Retries trigger only from the `Connected` state. A failure during `Connecting` transitions straight to `Disconnected` and does not consume the retry budget.
- The retry budget resets to zero on the next successful `Connected` transition.
- The retry count and backoff are internal constants in this release and are not exposed through `SpacetimeSettings`.

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| `"Spacetime Status"` panel flickers `DEGRADED` then returns to `CONNECTED` | A transient transport error occurred; the reconnect policy restored the session | No action required — this is the expected recovery path |
| `"Spacetime Status"` panel stays `DEGRADED` across successive retry messages | The underlying fault is not transient (server down, network partition, DNS failure) | Inspect server availability and transport reachability; resolve the root cause before the retry budget exhausts |
| `"Spacetime Status"` panel transitions `DEGRADED` → `DISCONNECTED` and `ConnectionClosed` fires with `ConnectionCloseReason.Error` | The retry budget of 3 attempts was exhausted without a successful recovery | Restore the server or transport and call `Connect()` again; the policy resets on the next successful connection |
| Scene code races the internal policy with its own retry loop | Duplicate reconnect logic layered on top of `SpacetimeClient` | Remove the scene-side loop; observe `ConnectionStateChanged` and `ConnectionClosed` — the policy is owned by `SpacetimeClient` |

During each retry, `ConnectionStateChanged` delivers a `Degraded` status whose description has the form:

```
DEGRADED — session experiencing issues; reconnecting (attempt N/3, backoff Xs): <error>
```

Matching this pattern in logs is the canonical way to observe retry progress. A symptom of **misconfiguration** — rather than a transient fault — is the session reaching `DEGRADED` and then `DISCONNECTED` on every `Connect()` attempt with the same root-cause `<error>`; this indicates the retry policy is working as intended but the underlying `Host`, `Database`, or transport configuration is wrong.

## Authentication

Authentication failures surface through `SpacetimeClient.ConnectionStateChanged` — not as exceptions. The `ConnectionAuthState` value on the resulting `ConnectionStatus` identifies the failure category:

Auth failures that prevent a session from reaching `Connected` do not emit `ConnectionClosed`.

| ConnectionAuthState | Meaning | Recovery Action |
|--------------------|---------|-----------------|
| `TokenExpired` | A previously stored token was rejected by the server | Call `Settings.TokenStore?.ClearTokenAsync()` to remove the invalid token; the next `Connect()` call falls back to anonymous |
| `AuthFailed` | Explicit credentials were confirmed rejected (HTTP 401/403) | Update `Settings.Credentials` with a valid token before reconnecting |
| `ConnectFailed` | Connection failed while credentials were provided, but the cause is ambiguous (e.g., network timeout, server offline) | Check `ConnectionStatus.Description` for the underlying error; retry the connection or verify network connectivity |

If the configured `ITokenStore` throws, `Connect()` falls back to anonymous without corrupting session state. Check the `ITokenStore` implementation for errors.

**Clearing a persisted token in the demo (`ProjectSettingsTokenStore`):**

Go to `Project > Project Settings` and remove the `spacetime/auth/token` entry, or call:

```csharp
await Settings.TokenStore.ClearTokenAsync();
```

before the next `Connect()` call.

See `docs/runtime-boundaries.md` for the complete `ConnectionAuthState` reference and `ITokenStore` interface.

## Subscriptions

Subscription failures surface through the `SpacetimeClient.SubscriptionFailed` signal. After the signal fires, the `SubscriptionHandle` transitions to `Closed` and the failed registry entry is cleaned up. Any previously authoritative subscription remains readable.

Inspect `SubscriptionFailedEvent.ErrorMessage` to determine the recovery path:

| ErrorMessage pattern | Likely Cause | Recovery Action |
|---------------------|-------------|-----------------|
| SQL syntax error | The query string passed to `Subscribe()` is malformed | Fix the query string; verify against the SQL subset supported by SpacetimeDB |
| Table name not found | The table name in the query does not match the generated `RemoteTables` property | Regenerate bindings with `bash scripts/codegen/generate-smoke-test.sh`; confirm the module source exists |

`Subscribe()` throws `InvalidOperationException` if called before `ConnectionState.Connected`. Wait for `SpacetimeClient.ConnectionStateChanged` to reach `Connected` before calling `Subscribe()`.

See `docs/runtime-boundaries.md` for the full `SubscriptionHandle`, `SubscriptionAppliedEvent`, and `SubscriptionFailedEvent` API reference.

## One-Off Queries

`SpacetimeClient.QueryAsync<TRow>()` reuses the active connection and auth boundary for a one-off remote round-trip. It does **not** create a subscription and does **not** populate the local cache returned by `GetDb<TDb>()` / `GetRows()`.

Recoverable runtime failures are thrown as `OneOffQueryError`; branch on `OneOffQueryError.FailureCategory`:

| OneOffQueryFailureCategory | Visible Indicator | Likely Cause | Recovery Action |
|----------------------------|-------------------|-------------|-----------------|
| `InvalidQuery` | `QueryAsync<TRow>()` throws `OneOffQueryError` with `FailureCategory=InvalidQuery` | The SQL clause is malformed or uses an unsupported query shape | Fix the clause and retry; one-off queries target the generated table selected by `TRow` |
| `TimedOut` | `QueryAsync<TRow>()` throws `OneOffQueryError` with `FailureCategory=TimedOut` | The explicit or default timeout elapsed before the server replied | Verify server health and query shape; retry with a longer timeout only if the query is expected to be slow |
| `Failed` | `QueryAsync<TRow>()` throws `OneOffQueryError` with `FailureCategory=Failed` | Server-side runtime failure unrelated to a client programming fault | Capture diagnostics, check server logs, and retry only after confirming the failure is transient |
| `Unknown` | `QueryAsync<TRow>()` throws `OneOffQueryError` with `FailureCategory=Unknown` | The upstream failure could not be classified safely | Avoid automatic retries; surface a safe generic error and capture diagnostics |

Programming faults remain explicit exceptions rather than `OneOffQueryError` values:

| Fault | Visible Indicator | Recovery Action |
|-------|-------------------|-----------------|
| Blank/whitespace SQL clause | `ArgumentException` from `QueryAsync<TRow>()` | Pass a non-empty clause such as `WHERE value = 'hello'` |
| Called before `ConnectionState.Connected` | `InvalidOperationException` from `QueryAsync<TRow>()` | Wait for `Connected` before issuing the one-off query |
| Unsupported generated row type | `InvalidOperationException` from `QueryAsync<TRow>()` | Use a generated row type from the active module bindings |

## Reducers

Reducer call outcomes fall into two distinct categories that must not be conflated.

### Recoverable Runtime Failures

These arrive asynchronously through the `SpacetimeClient.ReducerCallFailed` signal. Branch on `ReducerCallError.FailureCategory`:

| ReducerFailureCategory | Meaning | Recovery Action |
|------------------------|---------|-----------------|
| `Failed` | Server rejected the reducer call (logic error or constraint) | Check server logs; retrying with the same arguments is unlikely to succeed |
| `OutOfEnergy` | Server ran out of energy | Back off and retry after a delay |
| `Unknown` | Status could not be determined | Handle defensively; do not retry automatically without additional context |

### Programming Faults

These surface via `GD.PushError` in the Godot Output panel and `SpacetimeClient.ConnectionStateChanged`. The `ReducerCallFailed` signal does **not** fire for programming faults.

| Fault | Visible Indicator | Recovery Action |
|-------|-------------------|-----------------|
| `InvokeReducer()` called while not `Connected` | `GD.PushError` + `ConnectionStateChanged(Disconnected)` | Wait for `ConnectionState.Connected` before calling `InvokeReducer()` |
| `InvokeReducer()` called with `null` | `GD.PushError` + `ConnectionStateChanged(Disconnected)` | Pass a valid generated `IReducerArgs` instance (e.g., `new SpacetimeDB.Types.Reducer.Ping()`) |
| `InvokeReducer()` called with a non-`IReducerArgs` type | `GD.PushError` + `ConnectionStateChanged(Disconnected)` | Use a generated binding type from `SpacetimeDB.Types.Reducer.*` |

For the expected success and failure output message sequences, see the `## Reducer Interaction` section in `demo/README.md`.

See `docs/runtime-boundaries.md` for the complete reducer error model and `ReducerFailureCategory` reference.

### Scheduled Reducers

If a scheduled reducer is not firing, verify that a row has been inserted into the corresponding scheduled table with a valid `ScheduleAt` value (e.g., `new SpacetimeDB.ScheduleAt.Interval(new SpacetimeDB.TimeDuration(microseconds))`). Scheduled reducers are server-triggered — they do not appear in `RemoteReducers` and cannot be invoked directly with `InvokeReducer()`.

## Web Export (Native GDScript)

Story 11.5 validates native GDScript web delivery through a dedicated pure-GDScript export fixture. It does **not** export the repo root C# / Forward Plus project.

| Visible Indicator | Likely Cause | Recovery Action |
|-------------------|-------------|-----------------|
| Browser proof path fails before export and mentions `Compatibility` | The staged project is using the wrong renderer or the repo root C# project shape instead of the dedicated pure-GDScript fixture | Export the dedicated Story 11.5 fixture only; the project must omit the `C#` feature and use the Compatibility renderer |
| Browser load hangs or the exported page shows a blank startup | The export was opened via `file://` instead of being served over HTTP | Serve the exported directory over local HTTP and load `index.html` from `http://127.0.0.1:...`; do not use `file://` |
| Web export fails with a missing template message | Godot web export templates are not installed for the local Godot binary | Install the matching web export template set for the current Godot binary, then rerun the Story 11.5 browser lane |
| Browser validation skips because no browser binary is available | Chromium/Chrome-family browser prerequisite missing | Install a supported browser binary or set `BROWSER_BIN=/path/to/browser` before rerunning the Story 11.5 web-export test |
| Browser auth mode is reported as `authorization-header` instead of `query-token` | The validation path is not exercising the web-export auth seam correctly | In browser/web mode, validate credentials through the query-token transport path; web exports must not rely on WebSocket handshake headers |

The Story 11.5 web-export proof path is skip-safe by design. Missing local runtime access, missing browser binaries, missing export templates, or loopback HTTP restrictions should skip the browser lane with explicit prerequisite messages instead of failing the entire static suite.

## See Also

- `docs/runtime-boundaries.md` — Complete public API vocabulary, all lifecycle states, signals, and the reducer error model
- `demo/README.md` — Canonical end-to-end sample; expected output message sequences for each lifecycle phase
- `docs/quickstart.md` — Step-by-step setup guide with phase-specific failure indicators and recovery actions
- `docs/install.md` — Installation prerequisites and foundation validation details
- `docs/codegen.md` — Code generation workflow and module locations
- `docs/compatibility-matrix.md` — Declared supported version baseline
