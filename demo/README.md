# godot-spacetime Demo

This sample project proves the supported setup path from install through first connection. Follow the steps below to reproduce the baseline workflow from a clean state.

**Version targets:** Godot `4.6.2`, `.NET 8+`, SpacetimeDB CLI `2.1+`

If you are validating a candidate addon artifact instead of the repository source, replace the workspace `addons/godot_spacetime/` directory with the artifact's `addons/godot_spacetime/` payload before opening the project. The rest of this sample flow stays the same.

## Prerequisites

- Godot editor: `4.6.2` (with .NET support)
- `.NET` SDK: `8.0+`
- SpacetimeDB CLI: `2.1+`

These match the **Supported Foundation Baseline** documented in `docs/install.md`.

## Setup

Follow these steps from the repository root to reach a first successful connection.

### Step 1 — Open repository root in Godot

Open the repository root folder (not the `demo/` subfolder) in Godot. The addon lives at `addons/godot_spacetime/` and must be loaded from the project root.
The repository root also pre-registers `DemoBootstrap` as an autoload in `project.godot` so the sample bootstrap message appears before `demo/DemoMain.tscn` runs.

### Step 2 — Enable `Godot Spacetime` in `Project > Project Settings > Plugins`

1. Go to `Project > Project Settings > Plugins`.
2. Locate `Godot Spacetime` in the plugin list.
3. Toggle the **Enable** checkbox to activate the plugin.

The plugin registers three editor bottom panels: `"Spacetime Codegen"`, `"Spacetime Compat"`, and `"Spacetime Status"`.

### Step 3 — Run foundation validation

```bash
python3 scripts/compatibility/validate-foundation.py
```

This restores and builds the solution, then validates the supported foundation baseline. If this step exits non-zero, see `docs/install.md` for troubleshooting.

### Step 4 — Generate bindings

```bash
bash scripts/codegen/generate-smoke-test.sh
```

This generates C# client bindings from the smoke test module and writes them to `demo/generated/smoke_test/`.

### Step 5 — Confirm bindings in `"Spacetime Codegen"` panel

Open the `"Spacetime Codegen"` bottom panel. When bindings are present and valid, the panel displays:

```
OK — bindings present
```

Also open `"Spacetime Compat"` to confirm:

```
OK — bindings match declared baseline
```

If either panel shows an error state, rerun Step 4 and confirm that `spacetime/modules/smoke_test/` exists.

### Step 6 — Create a `SpacetimeSettings` resource and assign it to `SpacetimeClient`

1. Right-click in the Godot FileSystem panel and select `New Resource` → choose `SpacetimeSettings`.
2. Set the `Host` field (for example, `localhost:3000`).
3. Set the `Database` field (for example, `my_module`).
4. Save the resource file.
5. Go to `Project > Project Settings > Autoload`, click the folder icon, and select `addons/godot_spacetime/src/Public/SpacetimeClient.cs`. Confirm the singleton name is `SpacetimeClient`, then click **Add**.
6. Select the `SpacetimeClient` autoload entry and assign your saved `SpacetimeSettings` resource to its `Settings` property in the Inspector.

### Step 7 — Open `demo/DemoMain.tscn`, run the project, and observe connection

1. Open `demo/DemoMain.tscn` as the main scene.
2. Run the project.
3. Observe the `"Spacetime Status"` panel show:

```
CONNECTED — active session established
```

The Output panel will first print `[Demo] Bootstrap ready — godot-spacetime addon enabled`, then log connection state transitions as `[Demo] Connection state: <state>`.

## Auth and Session Resume

`DemoMain` is wired with token persistence so authenticated sessions survive across runs.

**Default behavior:** On the first run, `DemoMain` opens an anonymous session. The server assigns a new identity for that session.

**Token persistence:** Before calling `Connect()`, `DemoMain` sets `Settings.TokenStore = new ProjectSettingsTokenStore()`. The SDK stores the server-assigned token under the Godot ProjectSetting key `spacetime/auth/token` once the session opens.

**Session resume:** On subsequent runs the stored token is automatically restored — no code change is required. The Output panel will show the previously assigned identity instead of `"(new — token will be stored)"`.

**Auth prerequisites:** The deployment must accept token-authenticated sessions. Both anonymous and token-authenticated sessions work with the smoke test module.

**External project guidance:** External projects outside this repository cannot access `ProjectSettingsTokenStore` directly because it is `internal` to the addon assembly. External projects should implement the public `GodotSpacetime.Auth.ITokenStore` interface and assign their implementation to `Settings.TokenStore`.

**Reset instructions:** To clear the stored token and start a fresh anonymous session, go to `Project > Project Settings` and remove the `spacetime/auth/token` entry, or, after confirming `Settings.TokenStore` is configured, call `await Settings.TokenStore.ClearTokenAsync()` before the next `Connect()` call.

## Subscription and Live State

After `Connected`, `DemoMain` subscribes to the smoke test table and observes live row changes.

- After the connection reaches `Connected`, `DemoMain` calls `Subscribe(["SELECT * FROM smoke_test"])`. The Output panel shows `"[Demo] Subscribed to smoke_test — awaiting initial sync"`.
- When the server confirms the subscription, `SubscriptionApplied` fires. `DemoMain` reads the local cache through `var db = _client.GetDb<RemoteTables>()`, then uses `db.SmokeTest.Iter().ToList()` and `db.SmokeTest.Count` to print `"[Demo] Subscription applied — N row(s) in smoke_test"` where N is the current cache count.
- Any live row mutations emit `"[Demo] Row changed — table: SmokeTest, type: Insert/Update/Delete"` for each change.
- The SQL subscription query still uses `smoke_test`, while the typed cache path uses the generated `RemoteTables` handle name `SmokeTest`. `GetRows("SmokeTest")` still exists as the PascalCase compatibility fallback when code only has a table name.

**Output panel expected message sequence:**

```
[Demo] Bootstrap ready — godot-spacetime addon enabled
[Demo] Connection state: CONNECTING — opening a session to <host>/<database>
[Demo] Connection state: CONNECTED — active session established
[Demo] Subscribed to smoke_test — awaiting initial sync
[Demo] Session identity: (new — token will be stored)
[Demo] Subscription applied — N row(s) in smoke_test
```

The `Connected` line appears before the identity line because the SDK transitions to `ConnectionState.Connected` before it emits `ConnectionOpened`, and the demo starts the subscription from the `Connected` state handler.

On the second run (session resumed), the `Connected` line changes to `"[Demo] Connection state: CONNECTED — authenticated session established"` and the identity line shows the previously assigned hex identity string instead of the `"(new — token will be stored)"` placeholder.

The lifecycle terms `SubscriptionApplied` and `RowChanged` are defined in `docs/runtime-boundaries.md`.

## One-Off Query Example

One-off queries are a separate path from subscriptions. They reuse the current connection and authentication boundary, fetch typed rows from the server, and do **not** create a subscription or populate the local cache.

```csharp
var rows = await _client.QueryAsync<SmokeTest>("WHERE value = 'hello'");
foreach (var row in rows)
{
    GD.Print($"[Demo] One-off row: {row.Id} {row.Value}");
}
```

Compare the read modes:

- `GetDb<RemoteTables>()` and `GetRows("SmokeTest")` read the subscription-backed local cache.
- `Subscribe(["SELECT * FROM smoke_test"])` creates the live synchronized cache slice that powers `SubscriptionApplied` and `RowChanged`.
- `QueryAsync<SmokeTest>(...)` performs a remote one-off query without creating a subscription and without backfilling the cache counts or rows used by the subscription path.

## Reducer Interaction

After `SubscriptionApplied` fires and the row count is logged, `DemoMain` automatically invokes the `Ping` reducer via `InvokeReducer(new Reducer.Ping())`.

The call is asynchronous — the server acknowledgement arrives in a later frame (after `FrameTick` delivers the queued server message).

**Success path:** `ReducerCallSucceeded` fires with the reducer name and invocation ID:

```
[Demo] Reducer 'ping' succeeded (id: ...)
```

**Failure path:** `ReducerCallFailed` fires with failure category (`Failed`, `OutOfEnergy`, or `Unknown`) plus machine-readable `RecoveryGuidance` for branching:

```
[Demo] Reducer 'ping' failed — <category>: <message> | guidance: <guidance>
```

**Troubleshooting comparison path:** The expected output for a healthy Ping flow is `succeeded` — if `ReducerCallFailed` appears instead, the category and recovery guidance identify whether to retry, check server logs, or back off.

**Programming faults are a separate path:** If `InvokeReducer()` is called before `Connected`, with `null`, or with a non-generated reducer arg, the SDK surfaces the problem through `ConnectionStateChanged` plus `GD.PushError`. Those calling-code faults do **not** fire `ReducerCallFailed`, so compare them against the runtime-boundaries programming-fault guidance instead of the server-failure path above.

**Full expected Output panel sequence (extending the Story 5.2 sequence):**

```
[Demo] Subscription applied — N row(s) in smoke_test
[Demo] Ping reducer invoked — awaiting server acknowledgement
[Demo] Reducer 'ping' succeeded (id: <invocation-id>)
```

The lifecycle terms `ReducerCallSucceeded` and `ReducerCallFailed` are defined in `docs/runtime-boundaries.md`.

`ReducerFailureCategory` values (`Failed`, `OutOfEnergy`, `Unknown`) are documented in the SDK at `addons/godot_spacetime/src/Public/Reducers/ReducerFailureCategory.cs`.

## Reset to Clean State

To reproduce the baseline workflow from scratch without maintainer intervention:

1. Delete the generated bindings (keep the directory and its `README.md`):

   ```bash
   find demo/generated/smoke_test -type f -name '*.cs' -delete
   ```

   This removes the generated C# bindings from the root, `Reducers/`, `Tables/`, and `Types/` folders while keeping the directory structure and `demo/generated/smoke_test/README.md` intact.

2. Rerun the codegen script to regenerate:

   ```bash
   bash scripts/codegen/generate-smoke-test.sh
   ```

3. Open Godot and verify:
   - `"Spacetime Codegen"` panel shows `OK — bindings present`
   - `"Spacetime Compat"` panel shows `OK — bindings match declared baseline`

After these steps the project is back to a clean, reproducible state. No maintainer intervention is required.

## See Also

- `docs/quickstart.md` — the canonical step-by-step setup guide for this repository. `demo/README.md` mirrors its steps; if the two diverge, `docs/quickstart.md` is authoritative.
- `docs/install.md` — installation prerequisites, bootstrap steps, and foundation validation details.
- `docs/codegen.md` — code generation, schema concepts, and module locations.
- `docs/connection.md` — connection lifecycle states, signals, and editor status labels.
- `docs/compatibility-matrix.md` — the declared support baseline for CLI and SDK versions.
