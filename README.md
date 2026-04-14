# godot-spacetime

`godot-spacetime` is a Godot `.NET` addon that is being built as a maintained SpacetimeDB SDK for Godot projects. This repository is the root Godot development workspace and ships the addon from `addons/godot_spacetime/`.

## Current Foundation

Story `1.1` establishes the installable shell and bootstrap path:

- repo-root Godot project: `project.godot`
- repo-root C# project: `godot-spacetime.csproj`
- repo-root solution: `godot-spacetime.sln`
- shipping addon root: `addons/godot_spacetime/`

The runtime, code-generation, compatibility, auth, and sample flows are implemented in later stories. At this stage, the repository provides the supported addon foundation and the documented setup baseline those later stories will extend.

## Foundation Validation

Run the shared validation entrypoint to restore the solution, build the addon assembly, and confirm the current support baseline and future workflow prerequisites are still in place:

```bash
python3 scripts/compatibility/validate-foundation.py
```

This is the same entrypoint used by `.github/workflows/validate-foundation.yml`.

## Bootstrap

1. Install a supported Godot `.NET` editor and a `.NET 8` SDK.
2. Run the shared foundation validation lane:

   ```bash
   python3 scripts/compatibility/validate-foundation.py
   ```

3. Open this repository root in Godot.
4. In `Project > Project Settings > Plugins`, enable `Godot Spacetime`.

The shared validation lane restores `godot-spacetime.sln`, builds `godot-spacetime.sln -c Debug --no-restore`, and validates the documented support baseline before plugin enablement.

## Support Baseline

See [docs/install.md](docs/install.md) for the bootstrap flow and [docs/compatibility-matrix.md](docs/compatibility-matrix.md) for the current support baseline and package notes.
