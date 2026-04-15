# Quickstart

This guide walks through first-time setup and validation for `godot-spacetime` — from plugin install through a first successful connection.

If you are validating a candidate addon artifact instead of the repository source, replace the workspace `addons/godot_spacetime/` directory with the artifact's `addons/godot_spacetime/` payload before opening the project. The rest of this quickstart stays the same.

## Prerequisites

- Godot editor: `4.6.2`
- `.NET` SDK: `8.0+`
- SpacetimeDB CLI: `2.1+`

## Quickstart

### Step 1 — Install and Enable the Plugin

Clone or download the repository, then open the repository root folder in Godot.

1. Go to `Project > Project Settings > Plugins`.
2. Locate `Godot Spacetime` in the plugin list.
3. Toggle the **Enable** checkbox to activate the plugin.

The plugin registers three editor bottom panels: `"Spacetime Codegen"`, `"Spacetime Compat"`, and `"Spacetime Status"`. These panels remain usable in narrow, standard, and wide editor panel widths. All primary actions are keyboard-reachable.

### Step 2 — Validate the Foundation

Run the shared foundation validation lane from the repository root:

```bash
python3 scripts/compatibility/validate-foundation.py
```

The script restores and builds the solution, then validates the documented support baseline. If this step exits non-zero, see `docs/install.md` for troubleshooting.

### Step 3 — Generate Client Bindings

Run the code generation script from the repository root:

```bash
bash scripts/codegen/generate-smoke-test.sh
```

The script generates C# client bindings from the smoke test module and writes them to `demo/generated/smoke_test/`.

Open the `"Spacetime Codegen"` bottom panel to confirm status. When bindings are present and valid, the panel displays:

```
OK — bindings present
```

If the panel shows `MISSING` or `NOT CONFIGURED`, rerun the script and confirm that `spacetime/modules/smoke_test/` exists. See `docs/codegen.md` for additional guidance.

### Step 4 — Review Compatibility Status

Open the `"Spacetime Compat"` bottom panel. When the generated bindings are up to date and were produced with a CLI version that satisfies the declared baseline, the panel displays:

```
OK — bindings match declared baseline
```

If the panel shows `INCOMPATIBLE`, rerun `bash scripts/codegen/generate-smoke-test.sh`. If the bindings were generated with an older CLI, update the CLI to version `2.1+` before regenerating. See `docs/compatibility-matrix.md` for the declared baseline.

### Step 5 — Configure SpacetimeSettings

Create a `SpacetimeSettings` resource in the Godot editor:

1. Right-click in the FileSystem panel.
2. Select `New Resource` → choose `SpacetimeSettings`.
3. Set the `Host` field (for example, `localhost:3000`).
4. Set the `Database` field (for example, `my_module`).
5. Save the resource file.

The `SpacetimeSettings` resource exposes `[Export] Host` and `[Export] Database` fields. Both are inspector-assignable.

### Step 6 — Add SpacetimeClient as Autoload

Register `SpacetimeClient` so it is available everywhere in the project:

1. Go to `Project > Project Settings > Autoload`.
2. Click the folder icon and select `addons/godot_spacetime/src/Public/SpacetimeClient.cs`.
3. Confirm the singleton name is `SpacetimeClient`, then click **Add**.
4. Select the new autoload entry and assign your saved `SpacetimeSettings` resource to the `Settings` property in the Inspector.

The `"Spacetime Status"` panel will show:

```
NOT CONFIGURED — assign a SpacetimeSettings resource
```

until `Settings` is assigned. This is the expected state before Step 7.

### Step 7 — Connect and Observe Lifecycle

In a scene script or autoload, call `Connect()` and observe the `connection_state_changed` signal:

```gdscript
# In your scene script or autoload:
func _ready() -> void:
    SpacetimeClient.connection_state_changed.connect(_on_state_changed)
    SpacetimeClient.Connect()

func _on_state_changed(status: ConnectionStatus) -> void:
    print("Connection state: ", status.Description)
```

`SpacetimeClient` must already be registered as an autoload and have a `SpacetimeSettings` resource with `Host` and `Database` assigned before calling `Connect()`.

After `Connect()` succeeds, the `"Spacetime Status"` panel shows:

```
CONNECTED — active session established
```

## Failure Recovery

Each phase of the quickstart produces a distinct visible failure indicator and a specific recovery action.

| Failure Phase | Visible Indicator | Recovery Action |
|---|---|---|
| Foundation / install | `validate-foundation.py` exits non-zero | Follow error output; check `docs/install.md` |
| Code generation | `"Spacetime Codegen"` shows `MISSING` or `NOT CONFIGURED` | Run `bash scripts/codegen/generate-smoke-test.sh`; confirm `spacetime/modules/smoke_test/` exists |
| Compatibility | `"Spacetime Compat"` shows `INCOMPATIBLE` | Run `bash scripts/codegen/generate-smoke-test.sh`; if the bindings were generated with an older CLI, update it to `2.1+` first; check `docs/compatibility-matrix.md` |
| Settings / autoload | `"Spacetime Status"` shows `NOT CONFIGURED` | Assign `SpacetimeSettings` resource with `Host` and `Database`; register `SpacetimeClient` as autoload |
| Connection | `"Spacetime Status"` shows `DISCONNECTED` or `DEGRADED` | Verify `Host` and `Database` point to a running SpacetimeDB deployment; check `docs/connection.md` |

## See Also

docs/install.md
— Installation prerequisites, bootstrap steps, and foundation validation details.

docs/codegen.md
— Code generation, schema concepts, and module locations.

docs/connection.md
— Connection lifecycle states, signals, and editor status labels.
