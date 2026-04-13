# Install

This repository is the Godot project root for local development of `godot-spacetime`. The distributable addon lives under `addons/godot_spacetime/` and can be enabled directly from this workspace without copying folders into a second project.

## Supported Foundation Baseline

- Godot editor target: `4.6.2`
- `.NET` SDK: `8.0+`
- SpacetimeDB baseline: `2.1+`

## Bootstrap Steps

1. Install a supported Godot `.NET` editor and a local `.NET 8` SDK.
2. Restore the repository C# project:

   ```bash
   dotnet restore godot-spacetime.csproj
   ```

3. Build the root solution:

   ```bash
   dotnet build godot-spacetime.sln
   ```

4. Open the repository root folder in Godot.
5. Go to `Project > Project Settings > Plugins`.
6. Enable `Godot Spacetime`.

The restore/build step is required before enabling the addon because Godot C# editor plugins must be compiled before the editor can load them.

## Repository Expectations

- The repository root stays the Godot workspace.
- The addon stays at `addons/godot_spacetime/`.
- Later validation, code-generation, and runtime stories extend this workspace instead of restructuring it.

## Notes

- The scaffold currently uses the official `Godot.NET.Sdk` NuGet package `4.6.1`, which is the latest stable package available at the time this foundation story was implemented.
- The product support baseline remains Godot `4.6.2`, `.NET 8+`, and SpacetimeDB `2.1+`; later validation stories should keep the declared baseline and implementation details in sync as upstream packages advance.
