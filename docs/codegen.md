# Code Generation

## Prerequisites

- SpacetimeDB CLI: `2.1+` — install via the [SpacetimeDB installation guide](https://spacetimedb.com/install)
- Run from the repository root

## Generating Smoke Test Bindings

Run the provided script to generate C# client bindings from the smoke_test module:

```bash
bash scripts/codegen/generate-smoke-test.sh
```

The script outputs generated C# bindings to `demo/generated/smoke_test/`.

## Regenerating After Schema Changes

Rerun the same script after any schema change. The script clears the previous output before regenerating, so no manual cleanup is required:

```bash
bash scripts/codegen/generate-smoke-test.sh
```

## Foundation Validation

Run the shared foundation validation entrypoint to confirm the expected codegen-related inputs still exist and the support baseline has not drifted:

```bash
python3 scripts/compatibility/validate-foundation.py
```

The same entrypoint is used by `.github/workflows/validate-foundation.yml` after restore and build complete.

## Module and Fixture Locations

- `spacetime/modules/smoke_test/` is reserved for the future local smoke module used by quickstart and first-connection validation.
- `spacetime/modules/compatibility_fixture/` is reserved for future schema-drift and regeneration scenarios.
- `tests/fixtures/generated/` is reserved for read-only generated bindings consumed by tests.
- `tests/fixtures/settings/` is reserved for non-shipping test settings and environment fixtures.

## Source of Truth

The machine-checkable support baseline for the current foundation lives in `scripts/compatibility/support-baseline.json`.

Future code generation and compatibility stories should extend the existing validation entrypoint instead of replacing it with a separate manual-only path.
