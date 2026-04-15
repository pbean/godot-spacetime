# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0-dev] - 2026-04-15

### Added

- .NET addon (`addons/godot_spacetime/`)
- Typed binding code generation (`scripts/codegen/`)
- Authentication session flows (login, session resume, failure recovery)
- Subscription management and local cache API
- Reducer invocation with scene-safe event callbacks
- Sample project (`demo/`)
- Core documentation suite (install, quickstart, connection, codegen, troubleshooting, migration, runtime-boundaries)
- Compatibility matrix and support policy (`docs/compatibility-matrix.md`)
- Release packaging/validation/publication pipeline (`scripts/packaging/`, `.github/workflows/`)

### Compatibility

This release targets the version combination declared in [`docs/compatibility-matrix.md`](docs/compatibility-matrix.md). See that document for the canonical supported Godot and SpacetimeDB version pair, support status definitions, and compatibility triage timeline.

### Migration

This is the initial release. There is no prior GodotSpacetime SDK version to migrate from. Adopters migrating from the community plugin should consult [`docs/migration-from-community-plugin.md`](docs/migration-from-community-plugin.md) for concept mapping and upgrade guidance.

[Unreleased]: https://github.com/clockworklabs/godot-spacetime/compare/v0.1.0-dev...HEAD
[0.1.0-dev]: https://github.com/clockworklabs/godot-spacetime/releases/tag/v0.1.0-dev
