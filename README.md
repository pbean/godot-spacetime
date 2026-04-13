# godot-spacetime

`godot-spacetime` is a Godot `.NET` addon that is being built as a maintained SpacetimeDB SDK for Godot projects. This repository is the root Godot development workspace and ships the addon from `addons/godot_spacetime/`.

## Current Foundation

Story `1.1` establishes the installable shell and bootstrap path:

- repo-root Godot project: `project.godot`
- repo-root C# project: `godot-spacetime.csproj`
- repo-root solution: `godot-spacetime.sln`
- shipping addon root: `addons/godot_spacetime/`

The runtime, code-generation, compatibility, auth, and sample flows are implemented in later stories. At this stage, the repository provides the supported addon foundation and the documented setup baseline those later stories will extend.

## Bootstrap

1. Install a supported Godot `.NET` editor and a `.NET 8` SDK.
2. Restore the root C# project:

   ```bash
   dotnet restore godot-spacetime.csproj
   ```

3. Build the solution once before enabling the plugin:

   ```bash
   dotnet build godot-spacetime.sln
   ```

4. Open this repository root in Godot.
5. In `Project > Project Settings > Plugins`, enable `Godot Spacetime`.

Godot C# editor plugins must be compiled before they can be enabled, so the restore/build step is part of the supported setup path.

## Support Baseline

See [docs/install.md](docs/install.md) for the bootstrap flow and [docs/compatibility-matrix.md](docs/compatibility-matrix.md) for the current support baseline and package notes.
