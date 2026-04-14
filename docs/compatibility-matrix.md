# Compatibility Matrix

This file declares the current support baseline for the repository foundation created in Story `1.1`.

| Surface | Baseline | Notes |
| --- | --- | --- |
| Godot editor/runtime target | `4.6.2` | Product baseline for the initial shipping runtime. |
| Godot .NET build SDK | `Godot.NET.Sdk` `4.6.1` | Current stable official NuGet package used by the scaffold. |
| `.NET` SDK | `8.0+` | Use a local `.NET 8` SDK for restore and build. |
| SpacetimeDB server and CLI | `2.1+` | Declared product baseline for later code-generation and runtime stories. |
| `SpacetimeDB.ClientSDK` | `2.1.0` | Added as `PackageReference` in Story 1.4; the `.NET` adapter in `Internal/Platform/DotNet/` is the only permitted reference location. |

The machine-checkable source of truth for this baseline lives in `scripts/compatibility/support-baseline.json`, and `.github/workflows/validate-foundation.yml` enforces it through `python3 scripts/compatibility/validate-foundation.py`.

## Scope of This Matrix

Story `1.1` establishes the installation and project-structure baseline. It does not yet validate runtime flows against SpacetimeDB. Later stories are responsible for turning this declared baseline into automated compatibility checks and end-to-end validated workflows.

## Binding Compatibility Check

The Compatibility panel in the Godot editor reads the CLI version comment embedded in generated bindings and compares it against the declared `spacetimedb` baseline. Generated files contain that comment near the top of the file, after the generated-file warning banner, in the form:

```
// This was generated using spacetimedb cli version X.Y.Z (commit ...)
```

The panel extracts the version token and checks that it satisfies the declared baseline (e.g. `2.1+` requires CLI `>= 2.1`). The validation workflow also compares the latest relevant module-source file under `spacetime/modules/smoke_test/` against `demo/generated/smoke_test/SpacetimeDBClient.g.cs` so stale bindings fail before runtime use. If either check fails, the tooling reports the exact failed check together with the regeneration command.

To resolve an INCOMPATIBLE state, run:

```bash
bash scripts/codegen/generate-smoke-test.sh
```

Story `1.8` implements this check. Stories `1.9` and `1.10` extend the quickstart to validate both binding compatibility and connection state before declaring the setup complete.
