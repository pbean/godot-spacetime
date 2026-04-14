# Runtime Boundaries — GodotSpacetime SDK Concepts

This document defines the public concept vocabulary for the GodotSpacetime SDK. All public API docs, sample guidance, and architecture notes use this terminology. You do not need to know how the first shipping runtime works to use this SDK because those implementation details stay behind the runtime boundary.

## Concept Vocabulary

### Connection

A **Connection** is a session link from a Godot game client to a configured SpacetimeDB database. The entry point is [`SpacetimeClient`](#spacetimeclient), which you register as an autoload. Once configured and started, `SpacetimeClient` manages the full connection lifecycle without requiring direct interaction with any underlying runtime types.

### Connection Lifecycle — `ConnectionState`

The lifecycle of a connection is expressed as a [`ConnectionState`](../addons/godot_spacetime/src/Public/Connection/ConnectionState.cs) enum:

| State | Meaning |
|-------|---------|
| `Disconnected` | No active connection attempt. The initial state before `Connect()` is called, and the terminal state after a clean disconnect. |
| `Connecting` | An attempt to reach the database is in progress. |
| `Connected` | A live session is established and subscriptions may be applied. |
| `Degraded` | The session is experiencing trouble (e.g., transient network loss) but has not fully disconnected. Recovery is attempted automatically. |

A [`ConnectionStatus`](../addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs) value pairs a `ConnectionState` with a human-readable description for logging and UI display. [`ConnectionOpenedEvent`](../addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs) represents the successful-open boundary rather than every lifecycle transition.

### Auth / Identity — `ITokenStore`

Session identity is token-based. The SDK does not dictate how tokens are persisted; instead, you provide an [`ITokenStore`](../addons/godot_spacetime/src/Public/Auth/ITokenStore.cs) implementation:

```csharp
Task<string?> GetTokenAsync();
Task StoreTokenAsync(string token);
Task ClearTokenAsync();
```

This is opt-in. If no `ITokenStore` is provided, tokens are not persisted across sessions. The interface is async so that any persistence backend (files, OS keychain, platform services) can be used without blocking the game thread.

### Subscriptions — `SubscriptionHandle` and `SubscriptionAppliedEvent`

A **Subscription** is a query scope that keeps a local cache slice synchronized with the server. You apply a subscription through `SpacetimeClient`; the SDK returns a [`SubscriptionHandle`](../addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs) you can use to manage that scope.

When the initial synchronization for a subscription is complete, a [`SubscriptionAppliedEvent`](../addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs) is raised. After that point, the local cache reflects the subscribed data.

### Cache

The **Cache** is the local synchronized read model populated by active subscriptions. Reads from the cache are always local (no network round-trip). The cache is populated and kept current by the SDK runtime; you read from it through generated binding types specific to your module's schema.

There is no direct public cache type in the core SDK — cache access is surfaced through **Generated Bindings** (see below).

### Reducers — `ReducerCallResult` and `ReducerCallError`

A **Reducer** is a server-side callable procedure. You invoke reducers through generated binding types. The SDK surfaces the outcome as a [`ReducerCallResult`](../addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs) on success, or a [`ReducerCallError`](../addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs) when the call fails or is rejected.

Reducer results arrive asynchronously as SDK events, not as direct return values, because the execution happens on the server.

### Generated Bindings

**Generated Bindings** are read-only C# types generated from a SpacetimeDB module schema using the `spacetimedb generate` command. They are specific to each module and live outside the addon itself. Generated types give you:

- Typed table row classes for cache reads
- Typed reducer invocation methods
- Typed event callbacks for row insert/update/delete changes

Generated bindings use the `GodotSpacetime.*` namespace vocabulary for event handling but are generated per-project, not shipped with the addon.

See [`docs/codegen.md`](./codegen.md) for the generation workflow.

### Configuration — `SpacetimeSettings`

[`SpacetimeSettings`](../addons/godot_spacetime/src/Public/SpacetimeSettings.cs) is a Godot `Resource` you create in the editor and assign to `SpacetimeClient`. It holds the configuration for a connection:

| Property | Type | Purpose |
|----------|------|---------|
| `Host` | `string` | The SpacetimeDB server address |
| `Database` | `string` | The target database name on the server |

Additional settings (auth, logging) are added in later stories and appear as exported properties visible in the Godot editor inspector.

### SpacetimeClient — The SDK Entry Point

[`SpacetimeClient`](../addons/godot_spacetime/src/Public/SpacetimeClient.cs) is the top-level Godot-facing service. It is a `Node` registered as an autoload, so it is available from any scene. The intended workflow is:

```
SpacetimeClient (autoload, configured with SpacetimeSettings)
  └─ Connect()
       └─ ConnectionState events (Disconnected → Connecting → Connected)
            └─ Apply subscriptions (returns SubscriptionHandle)
                 └─ SubscriptionAppliedEvent → read from Cache via generated bindings
                      └─ Invoke reducers → ReducerCallResult / ReducerCallError events
```

You interact with `SpacetimeClient` through its public API; the underlying runtime handling is not part of the SDK surface.

---

## Runtime Boundaries

The GodotSpacetime codebase enforces three structural zones:

### `Public/` — The SDK Contract

`addons/godot_spacetime/src/Public/` contains the types listed in this document. These are the only types consumers of the SDK interact with directly. They may reference:
- `Godot.*` types
- `System.*` types
- Other `GodotSpacetime.*` public types

They must **never** reference runtime-specific transport or adapter types.

### `Internal/` — Implementation Zone

`addons/godot_spacetime/src/Internal/` contains implementation code that supports the public surface. Internal types may change without changing the public contract. Consumers of the SDK do not use internal types directly.

### `Internal/Platform/DotNet/` — The Runtime Isolation Zone

`addons/godot_spacetime/src/Internal/Platform/DotNet/` is the **only** zone in the codebase that is permitted to reference the underlying `.NET` client runtime. All adapter code that translates between the `GodotSpacetime.*` public surface and the current managed runtime lives here.

This isolation means that if a future runtime (e.g., a GDNative or GDExtension implementation) is added, only the `Internal/Platform/` zone changes — the `Public/` contract and all code that depends on it remain stable.

---

## Future Runtime Seam

`addons/godot_spacetime/src/Internal/Platform/` is the designated location for future runtime implementations. The `.NET` adapter currently lives in `Internal/Platform/DotNet/`. A future runtime adapter would be added as a sibling (e.g., `Internal/Platform/Native/`) and selected at build or load time without changing the public API.

This seam is reserved by architecture decision. Story 1.5 validates that the GDScript continuity contract holds across this boundary.

---

## Logging — `LogCategory`

[`LogCategory`](../addons/godot_spacetime/src/Public/Logging/LogCategory.cs) is an enum used to tag SDK log output by subsystem:

| Value | Subsystem |
|-------|-----------|
| `Connection` | Connection lifecycle events |
| `Auth` | Token store operations and identity events |
| `Subscription` | Subscription apply, remove, and error events |
| `Reducer` | Reducer call dispatch and result handling |
| `Codegen` | Generated binding load and schema validation events |

Log filtering by category is configured through `SpacetimeSettings` (added in a later story).
