# Test Fixture Inputs

This directory reserves repo-owned inputs for test and validation stories.

- `tests/fixtures/generated/` is the future home for read-only generated bindings used by tests and compatibility checks.
- `tests/fixtures/generated/multi_module_smoke/` is the Story 10.1 read-only secondary generated binding fixture used to compile a second module namespace into the same Godot assembly.
- `tests/fixtures/generated/view_test/` is the Story 10.4 read-only generated fixture for database view-definition bindings.
- `tests/fixtures/settings/` is the future home for non-shipping settings or configuration fixtures used by automation.

These fixture assets stay outside the distributable addon ZIP.
