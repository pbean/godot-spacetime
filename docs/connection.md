# Connection

`SpacetimeClient` is the Godot-facing entry point for connection lifecycle management. Assign a `SpacetimeSettings` resource, optionally set `CompressionMode` or `LightMode`, call `Connect()`, and observe the emitted signals to understand what the SDK is doing.

Story 10.1 keeps the existing single-autoload workflow intact with zero changes:
`ConnectionId` still defaults to `SpacetimeClient`, and
`GeneratedBindingsNamespace` still defaults to `SpacetimeDB.Types`.
Multi-module support is additive: create more than one `SpacetimeClient`, give
each instance a distinct `ConnectionId`, set the matching
`SpacetimeSettings.GeneratedBindingsNamespace`, then resolve the intended client
through `SpacetimeClient.TryGetClient(...)` or `GetClientOrThrow(...)`.

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

## Auth Token Transport

The client presents the auth token while opening the WebSocket connection. The transport depends on the platform because browsers cannot set custom WebSocket handshake headers.

- **.NET runtime (headless and desktop):** when `SpacetimeSettings.Credentials` is non-empty, the adapter calls `builder.WithToken(settings.Credentials)` at `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs:86-87`. The pinned `SpacetimeDB.ClientSDK 2.1.0` owns the wire-level framing; this repo only passes the token through.
- **GDScript native (desktop):** the rule `allow_header_auth := not OS.has_feature("web")` at `addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd:533` evaluates `true`, so `build_transport_request` at `addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd:42-64` sets `Authorization: Bearer <token>` as a handshake header on `WebSocketPeer`.
- **GDScript web export (browser):** the same rule evaluates `false`, so `build_transport_request` at `addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd:42-61` appends `?<query_token_key>=<token>` to the WebSocket URL instead. The default parameter name is exposed as `DEFAULT_QUERY_TOKEN_KEY` at `addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd:7`.

Non-web deployments that must force query-string transport — for example, reverse proxies that strip `Authorization` headers — can set `prefer_query_token` to `true` and optionally override the parameter name with `query_token_key`; those parameters are declared on `build_transport_request` at `addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd:42-48` and threaded through the GDScript runtime options at `addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd:217-218` and `addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd:534-540`.

For current platform support boundaries, including Godot C# web export remaining Out-of-Scope, see `docs/compatibility-matrix.md:17`.

For symptoms such as `auth_mode == "authorization-header"` on a web target, see [troubleshooting.md → Web Export (Native GDScript)](troubleshooting.md#web-export-native-gdscript).

## Multiple Clients

One `SpacetimeClient` still equals one connection owner. Story 10.1 does not
introduce a shared multiplexer service inside a single client.

For multiple modules:

- Keep the default client at `ConnectionId = "SpacetimeClient"` when you want to preserve the existing `/root/SpacetimeClient` autoload path.
- Give each additional client its own `ConnectionId` such as `"AnalyticsClient"` or `"ChatClient"`.
- Set `SpacetimeSettings.GeneratedBindingsNamespace` to the generated namespace for that client's module.
- Use `SpacetimeClient.TryGetClient("AnalyticsClient", out var client)` instead of crawling arbitrary scene-tree paths manually.

## Telemetry

`SpacetimeClient.CurrentTelemetry` exposes pull-based connection metrics without widening `ConnectionStatus` into a high-churn counter object.

The typed telemetry properties are:

- `MessagesSent`
- `MessagesReceived`
- `BytesSent`
- `BytesReceived`
- `ConnectionUptimeSeconds`
- `LastReducerRoundTripMilliseconds`
- `MessagesReceivedPerSecond`
- `MessagesSentPerSecond`
- `BytesReceivedPerSecond`
- `BytesSentPerSecond`

Units are explicit: counts for `MessagesSent` / `MessagesReceived`, bytes for `BytesSent` / `BytesReceived`, seconds for uptime, and milliseconds for reducer RTT. The four `*PerSecond` properties are derived rates — they refresh on-read against a 1-second minimum sliding baseline, so two reads inside the same 1-second bucket return the same value, and a fresh session reads `0.0` until the first full second of uptime elapses.

The same values are mirrored into Godot `Performance` custom monitors:

- `GodotSpacetime/Connection/MessagesSent`
- `GodotSpacetime/Connection/MessagesReceived`
- `GodotSpacetime/Connection/BytesSent`
- `GodotSpacetime/Connection/BytesReceived`
- `GodotSpacetime/Connection/UptimeSeconds`
- `GodotSpacetime/Reducers/LastRoundTripMilliseconds`
- `GodotSpacetime/Connection/MessagesReceivedPerSecond`
- `GodotSpacetime/Connection/MessagesSentPerSecond`
- `GodotSpacetime/Connection/BytesReceivedPerSecond`
- `GodotSpacetime/Connection/BytesSentPerSecond`

Reset behavior is deliberate:

- `Disconnect()` resets `CurrentTelemetry` to zero immediately — including the four `*PerSecond` rates.
- A later reconnect starts a fresh measurement window rather than carrying over the previous session.

On the pinned stack, `BytesSent` is measured from the SDK's serialized outbound payload path rather than from a documented public wire-byte counter. Story 9.3 validation records that observed runtime behavior instead of guessing.

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

Story 10.1 keeps this editor panel default-client-only. It follows the default
`ConnectionId = "SpacetimeClient"` client and does not attempt to present a
multi-client selector in the panel UI.

## See Also

- `docs/troubleshooting.md` — `## Reconnection Behavior` section documents the internal `ReconnectPolicy` defaults (3-attempt retry budget, `2^(attempt-1)` backoff), when retries engage, and misconfiguration symptoms.
- `docs/runtime-boundaries.md` — Complete signal catalog, authentication, subscriptions, cache, reducers, and the full public SDK concept vocabulary.
- `demo/README.md` — The canonical end-to-end sample demonstrating the full connection lifecycle from setup through reducer interaction.
- `docs/quickstart.md` — Step-by-step first-setup guide that exercises connection lifecycle as part of the full onboarding flow.
