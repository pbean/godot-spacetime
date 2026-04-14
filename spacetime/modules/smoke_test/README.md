# Smoke Test Module

A minimal SpacetimeDB Rust module used as the canonical input for code generation workflows.

## Contents

- **Table:** `smoke_test` — `SmokeTest` struct with `id: u32` (primary key, auto-increment) and `value: String`
- **Reducer:** `ping` — no-op reducer that validates the generation and CLI invocation path

## Generated Output

Running `bash scripts/codegen/generate-smoke-test.sh` from the repository root generates C# client bindings from this module and writes them to `demo/generated/smoke_test/`.

## Usage

This module serves as the smoke-test input for Story 1.6+ code generation, quickstart, and first-connection validation workflows. It is not a production module.
