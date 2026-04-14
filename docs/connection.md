# Connection

`SpacetimeClient` is the Godot-facing entry point for connection lifecycle management. Assign a `SpacetimeSettings` resource, call `Connect()`, and observe the emitted signals to understand what the SDK is doing.

## Connection Lifecycle

The lifecycle is represented by `ConnectionState` and surfaced through the `connection_state_changed` Godot signal.

| State | Meaning |
| --- | --- |
| `Disconnected` | No active session exists, or a previous session has been closed. |
| `Connecting` | The SDK has accepted the current settings and is opening a session. |
| `Connected` | The session is open and the runtime can continue advancing work through `FrameTick()`. |
| `Degraded` | The session hit a recoverable problem and the runtime-owned reconnect policy is handling it. |

Each `connection_state_changed` emission includes a `ConnectionStatus` payload with both the named state and a human-readable description. The descriptions are explicit text, not color-only cues.

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
