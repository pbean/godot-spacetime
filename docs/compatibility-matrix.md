# Compatibility Matrix and Support Policy

This document is the canonical source of truth for GodotSpacetime SDK version support. It declares which Godot, .NET, and SpacetimeDB version combinations are currently targeted by this release, and what level of support each combination carries.

The following documentation references this file as the authoritative version baseline: `docs/install.md`, `docs/quickstart.md`, `docs/troubleshooting.md`, and `docs/migration-from-community-plugin.md`.

## Supported Version Baseline

| Surface | Version | Status |
|---------|---------|--------|
| Godot editor/runtime target | `4.6.2` | Supported |
| Godot .NET build SDK | `Godot.NET.Sdk` `4.6.1` | Supported |
| `.NET` SDK | `8.0+` | Supported |
| SpacetimeDB server and CLI | `2.1+` | Supported |
| `SpacetimeDB.ClientSDK` | `2.1.0` | Supported |
| Godot C# web export | N/A | Out-of-Scope |

The machine-checkable source of truth for this baseline lives in `scripts/compatibility/support-baseline.json`, and `.github/workflows/validate-foundation.yml` enforces it through `python3 scripts/compatibility/validate-foundation.py`.

## Support Policy

| Status | Meaning |
|--------|---------|
| **Supported** | This version combination is the declared target for the current release. It is validated in CI, covered in all documentation, and eligible for bug reports. |
| **Experimental** | This version combination has been tested informally but is not covered by CI or formal compatibility checks. It may work, but bugs may not be prioritized. |
| **Deferred** | This version combination is on the roadmap but not yet validated or targeted. It will appear as `Supported` in a future release when formally validated. |
| **Out-of-Scope** | This version combination is explicitly not supported and will not be investigated. Known out-of-scope targets include Godot C# web export and GDScript-only runtime delivery for v1. |

Only `Supported` entries are declared in the current release. `Experimental` and `Deferred` entries will be added in future releases as the compatibility matrix expands.

## Compatibility Triage Timeline

When upstream SpacetimeDB or Godot releases a new version, the following triage process applies:

1. Compatibility issues caused by upstream minor releases are assessed within **14 days** of the upstream release.
2. If the new version is compatible without SDK changes, a compatibility note is added to this file.
3. If SDK changes are required, an issue is filed and the affected version combination moves to `Experimental` until the SDK update ships.
4. Major upstream version changes are treated as new version targets and may require a new SDK release cycle.

## Version Change Guidance

If your Godot or SpacetimeDB version is not listed as `Supported`:

1. Run `python3 scripts/compatibility/validate-foundation.py` to identify which specific checks fail.
2. Check the `"Spacetime Compat"` panel in the Godot editor for binding version mismatch details.
3. Consult `docs/troubleshooting.md` for common environment mismatch failures and resolution steps.
4. File an issue with the version details if you believe your environment should be supported.

Version combinations that are not listed as `Supported` are not eligible for bug reports until they appear on the supported matrix.

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

## Scope of This Matrix

This matrix declares the version baseline for the GodotSpacetime SDK release it accompanies. It does not cover runtime flow validation — that is the responsibility of the release validation workflow. Later releases will expand the matrix as new Godot or SpacetimeDB versions are validated.
