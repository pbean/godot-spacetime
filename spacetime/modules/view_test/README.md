# View Test Module

A minimal SpacetimeDB Rust module used to validate database view-definition
code generation for Story 10.4.

## Contents

- **Table:** `player` — `Player` rows with `id`, `name`, `level`, and `active`
- **Views:** `players_for_level_two`, `player_one`
- **Reducer:** `seed_players` — helper used only to populate fixture data if the
  module is exercised dynamically

## Generated Output

Running `bash scripts/codegen/generate-view-test.sh` from the repository root
generates C# client bindings from this module and writes them to
`tests/fixtures/generated/view_test/`.

## Usage

This module exists for repository-owned QA coverage of view-definition bindings.
It is not a production module.
