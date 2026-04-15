# Install

This repository is the Godot project root for local development of `godot-spacetime`. The distributable addon lives under `addons/godot_spacetime/` and can be enabled directly from this workspace without copying folders into a second project.

If you are validating a candidate addon artifact instead of the repository source, replace the workspace `addons/godot_spacetime/` directory with the artifact's `addons/godot_spacetime/` payload before opening the project. The bootstrap steps below stay the same.

## Supported Foundation Baseline

- Godot editor target: `4.6.2`
- `.NET` SDK: `8.0+`
- SpacetimeDB baseline: `2.1+`

## Bootstrap Steps

1. Install a supported Godot `.NET` editor and a local `.NET 8` SDK.
2. Run the shared foundation validation lane:

   ```bash
   python3 scripts/compatibility/validate-foundation.py
   ```

3. Open the repository root folder in Godot.
4. Go to `Project > Project Settings > Plugins`.
5. Enable `Godot Spacetime`.

The shared validation lane restores `godot-spacetime.sln`, builds `godot-spacetime.sln -c Debug --no-restore`, and validates the current support baseline before the editor tries to load the addon.
The support baseline metadata used by the validation script lives in `scripts/compatibility/support-baseline.json`.

## Repository Expectations

- The repository root stays the Godot workspace.
- The addon stays at `addons/godot_spacetime/`.
- Later validation, code-generation, and runtime stories extend this workspace instead of restructuring it.

## Notes

- The scaffold currently uses the official `Godot.NET.Sdk` NuGet package `4.6.1`, which is the latest stable package available at the time this foundation story was implemented.
- The product support baseline remains Godot `4.6.2`, `.NET 8+`, and SpacetimeDB `2.1+`; later validation stories should keep the declared baseline and implementation details in sync as upstream packages advance.
- Story `1.2` reserves the repo-owned codegen and fixture inputs described in `docs/codegen.md` so later validation and generation stories can extend one documented path.

## See Also

- `docs/connection.md` for connection lifecycle states, signals, and editor status labels.
- `docs/quickstart.md` for the step-by-step first-setup workflow from install through first connection.
