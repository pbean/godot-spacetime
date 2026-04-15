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
