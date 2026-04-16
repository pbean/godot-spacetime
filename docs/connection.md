# Connection

`SpacetimeClient` is the Godot-facing entry point for connection lifecycle management. Assign a `SpacetimeSettings` resource, optionally set `CompressionMode` or `LightMode`, call `Connect()`, and observe the emitted signals to understand what the SDK is doing.

## Connection Lifecycle

The lifecycle is represented by `ConnectionState` and surfaced through the `connection_state_changed` Godot signal.

| State | Meaning |
| --- | --- |
| `Disconnected` | No active session exists, or a previous session has been closed. |
| `Connecting` | The SDK has accepted the current settings and is opening a session. |
| `Connected` | The session is open and the runtime can continue advancing work through `FrameTick()`. |
| `Degraded` | The session hit a recoverable problem and the runtime-owned reconnect policy is handling it. |

Each `connection_state_changed` emission includes a `ConnectionStatus` payload with the named state, a human-readable description, and `ActiveCompressionMode` for the effective session compression mode. The descriptions are explicit text, not color-only cues.

Compression is opt-in through `SpacetimeSettings.CompressionMode`. The product default is `None`. On the pinned `2.1.x` client stack, a `Brotli` request currently surfaces as effective `Gzip`, and `ConnectionStatus.ActiveCompressionMode` reports that effective mode.

Light mode is opt-in through `SpacetimeSettings.LightMode`, and the product default is `false`. The setting is applied when a session is opened; changing `LightMode` on the settings resource while a current session is already connected does not reconfigure that current session and only takes effect on the next connection cycle.

## Signals

- `connection_state_changed(ConnectionStatus)` fires for lifecycle transitions such as `Disconnected -> Connecting -> Connected`.
- `connection_opened(ConnectionOpenedEvent)` fires when `connection.opened` is observed from the runtime adapter and includes `Host`, `Database`, and `ConnectedAt`.

## Editor Status Panel

When the plugin is enabled, the `"Spacetime Status"` bottom panel mirrors the current lifecycle state with explicit labels:

- `DISCONNECTED — not connected to SpacetimeDB`
- `CONNECTING — connection attempt in progress`
- `CONNECTED — active session established`
- `DEGRADED — session experiencing issues; reconnecting`
- `NOT CONFIGURED — assign a SpacetimeSettings resource`

The panel also includes a `Compression:` row sourced from `ConnectionStatus.ActiveCompressionMode` rather than from `SpacetimeSettings` alone. Typical values are:

- `None (opt-in default)`
- `Gzip`

## See Also

- `docs/troubleshooting.md` — `## Reconnection Behavior` section documents the internal `ReconnectPolicy` defaults (3-attempt retry budget, `2^(attempt-1)` backoff), when retries engage, and misconfiguration symptoms.
- `docs/runtime-boundaries.md` — Complete signal catalog, authentication, subscriptions, cache, reducers, and the full public SDK concept vocabulary.
- `demo/README.md` — The canonical end-to-end sample demonstrating the full connection lifecycle from setup through reducer interaction.
- `docs/quickstart.md` — Step-by-step first-setup guide that exercises connection lifecycle as part of the full onboarding flow.
