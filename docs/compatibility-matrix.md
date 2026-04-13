# Compatibility Matrix

This file declares the current support baseline for the repository foundation created in Story `1.1`.

| Surface | Baseline | Notes |
| --- | --- | --- |
| Godot editor/runtime target | `4.6.2` | Product baseline for the initial shipping runtime. |
| Godot .NET build SDK | `Godot.NET.Sdk` `4.6.1` | Current stable official NuGet package used by the scaffold. |
| `.NET` SDK | `8.0+` | Use a local `.NET 8` SDK for restore and build. |
| SpacetimeDB server and CLI | `2.1+` | Declared product baseline for later code-generation and runtime stories. |
| `SpacetimeDB.ClientSDK` | `2.1.0` planned runtime baseline | Not referenced by the scaffold-only foundation yet, but this is the intended package target for later Epic 1 runtime stories. |

## Scope of This Matrix

Story `1.1` establishes the installation and project-structure baseline. It does not yet validate runtime flows against SpacetimeDB. Later stories are responsible for turning this declared baseline into automated compatibility checks and end-to-end validated workflows.
