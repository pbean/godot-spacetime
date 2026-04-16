# Generated Bindings Fixture — multi_module_smoke

This directory is a read-only generated artifact used by Story 10.1 tests.

It mirrors the committed `demo/generated/smoke_test/` bindings under a second
namespace, `SpacetimeDB.MultiModuleTypes`, so the Godot assembly can compile
two generated binding sets at once and verify deterministic per-client binding
selection.

Do not edit these files by hand.

When the local SpacetimeDB toolchain can regenerate fixtures directly, refresh
this directory from the `spacetime/modules/smoke_test/` module with:

```bash
spacetime generate \
  --lang csharp \
  --namespace SpacetimeDB.MultiModuleTypes \
  --out-dir tests/fixtures/generated/multi_module_smoke \
  --module-path spacetime/modules/smoke_test
python3 scripts/codegen/detect-godot-types.py tests/fixtures/generated/multi_module_smoke/Types
```
