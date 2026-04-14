# Code Generation Readiness

Story `1.2` does not implement the binding-generation workflow yet. It establishes the repo-owned inputs and validation hooks that later Epic 1 stories will extend.

## Current Readiness Gate

Run the shared foundation validation entrypoint to restore/build the current solution and confirm the expected codegen-related inputs still exist and the support baseline has not drifted:

```bash
python3 scripts/compatibility/validate-foundation.py
```

The same entrypoint is used by `.github/workflows/validate-foundation.yml` after restore and build complete.

## Reserved Repo Inputs

- `spacetime/modules/smoke_test/` is reserved for the future local smoke module used by quickstart and first-connection validation.
- `spacetime/modules/compatibility_fixture/` is reserved for future schema-drift and regeneration scenarios.
- `tests/fixtures/generated/` is reserved for read-only generated bindings consumed by tests.
- `tests/fixtures/settings/` is reserved for non-shipping test settings and environment fixtures.

## Source of Truth

The machine-checkable support baseline for the current foundation lives in `scripts/compatibility/support-baseline.json`.

Future code generation and compatibility stories should extend the existing validation entrypoint instead of replacing it with a separate manual-only path.
