# Spacetime Modules

This directory reserves the repository-owned SpacetimeDB module inputs that later Epic 1 stories will use for code generation, compatibility checks, and smoke validation.

Story `1.2` does not implement module logic yet. It makes the expected locations discoverable so foundation validation can fail early if those inputs disappear or move.

Current reserved module inputs:

- `spacetime/modules/smoke_test/` for the future local smoke module used by first-connection and quickstart validation
- `spacetime/modules/compatibility_fixture/` for future schema-drift and compatibility scenarios
- `spacetime/modules/view_test/` for Story 10.4 database view-definition validation

These module directories are test and validation assets, not shipping addon content.
