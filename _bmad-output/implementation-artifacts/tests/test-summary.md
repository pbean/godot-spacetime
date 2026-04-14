# Test Automation Summary — Story 1.3 & 1.4

## Story 1.3: Define Runtime-Neutral Public SDK Concepts and Terminology

### Generated Tests

- [x] `tests/test_story_1_3_sdk_concepts.py` — 100 tests, all passing

### Coverage Breakdown

#### File Existence (12 tests)
- [x] All 11 `addons/godot_spacetime/src/Public/**/*.cs` stubs present
- [x] `docs/runtime-boundaries.md` present

#### Namespace Declarations (11 tests)
- [x] Each Public/ stub declares the correct `GodotSpacetime.*` namespace per the canonical namespace table

#### No-SpacetimeDB Constraint (11 tests)
- [x] Zero `SpacetimeDB.` references in non-comment code across all 11 Public/ files

#### Type Shape Contracts (34 tests)
| Type | Tests |
|------|-------|
| `ConnectionState` | is enum, has exactly 4 values: Disconnected/Connecting/Connected/Degraded |
| `ConnectionStatus` | is record, has State + Description parameters |
| `ConnectionOpenedEvent` | is class |
| `ITokenStore` | is interface, imports System.Threading.Tasks, has 3 Task-based methods, no Godot import |
| `SubscriptionHandle` | is class |
| `SubscriptionAppliedEvent` | is class |
| `ReducerCallResult` | is record |
| `ReducerCallError` | is class |
| `LogCategory` | is enum, has Connection/Auth/Subscription/Reducer/Codegen |
| `SpacetimeSettings` | is `partial class : Resource`, has `[GlobalClass]`, has `[Export]` Host + Database |
| `SpacetimeClient` | is `partial class : Node`, doc-comment references `runtime-boundaries.md` |

#### `docs/runtime-boundaries.md` Content (24 tests)
- [x] Concept Vocabulary heading present
- [x] All 9 required concept sections
- [x] Runtime Boundaries section with all 3 zones (Public/, Internal/, Internal/Platform/DotNet/)
- [x] Future Runtime Seam section, LogCategory documented
- [x] No forbidden implementation terms (DbConnection, using SpacetimeDB)
- [x] All 11 public type names cross-referenced
- [x] ConnectionState workflow order: Disconnected → Connecting → Connected

#### `support-baseline.json` (2 tests)
- [x] `docs/runtime-boundaries.md` present in `required_paths` with `type: "file"`

---

## Story 1.4: Isolate the .NET Runtime Adapter Behind Internal Boundaries

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_1_4_adapter_boundary.py`

12 new tests added filling 6 discovered gaps. Total: 33 → **45** tests.

| New Test | Gap Filled | AC |
|----------|-----------|-----|
| `test_adapter_is_internal_sealed_class` ×3 | Class modifiers not verified; `public` regression undetectable | AC 1, 2 |
| `test_adapter_has_using_spacetimedb_directive` ×3 | Prior check searched full content including doc-comments; doesn't prove the import is in code | AC 1 |
| `test_adapter_has_idbconnection_stub_field` ×3 | `IDbConnection?` field (SDK type proof) was untested | AC 1 |
| `test_compatibility_matrix_spacetimedb_row_reflects_story_1_4` | Task 5 deliverable (exact row text) was untested | AC 3 |
| `test_support_baseline_spacetimedb_line_check_is_story_1_4` | Task 6 deliverable (`expected_line` + `version_key`) was untested | AC 3 |
| `test_runtime_boundaries_doc_names_dotnet_isolation_zone` | AC #3 was only asserted in story 1.3's suite | AC 3 |

### Original 33 tests (pre-gap)
- [x] Adapter file existence ×3
- [x] Adapter namespace `GodotSpacetime.Runtime.Platform.DotNet` ×3
- [x] No SpacetimeDB in any `Public/` file ×11
- [x] No SpacetimeDB outside `Internal/Platform/DotNet/` ×11
- [x] Adapters reference SpacetimeDB ×3
- [x] csproj `PackageReference Include="SpacetimeDB.ClientSDK"` ×1
- [x] csproj `Version="2.1.0"` ×1

---

## Story 1.5: Verify Future GDScript Continuity in Structure and Contracts

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_1_5_gdscript_continuity.py`

12 new tests added filling 4 discovered gaps. Total: 48 → **60** tests.

| New Test | Gap Filled | AC |
|----------|-----------|-----|
| `test_future_runtime_seam_has_explicit_runtime_neutral_statement` | No test guarded the explicit "Public/ contract is already runtime-neutral" statement in the Future Runtime Seam section — the seam path alone doesn't satisfy AC #3 | AC #3 |
| `test_future_runtime_seam_enumerates_runtime_neutral_type` ×9 | No test verified that all 9 public type names are enumerated in the runtime-neutral statement (spec requires listing them as evidence) | AC #3 |
| `test_story_1_5_forward_reference_placeholder_removed` | No test guarded that the Story 1.4 forward-reference placeholder sentence "Story 1.5 validates that the GDScript continuity contract holds across this boundary." was actually removed | Task 1 |
| `test_runtime_boundaries_drops_legacy_future_runtime_examples` | No test rejected the legacy `Internal/Platform/Native/`, `GDNative`, and `GDExtension` examples that would contradict the concrete `GDScript` seam | AC #1, #3 |

The existing seam-location assertions were also tightened so `Internal/Platform/GDScript/` must appear inside the `## Future Runtime Seam` section itself, not merely somewhere in the document.

### Original 48 tests (pre-gap)

- [x] `test_runtime_boundaries_doc_still_exists` — regression guard (Story 1.3)
- [x] `test_public_stub_file_still_exists` ×11 — regression guard (Story 1.3)
- [x] `test_runtime_boundaries_has_future_runtime_seam_heading` — AC #1/#3
- [x] `test_runtime_boundaries_names_gdscript_seam` — AC #3: `Internal/Platform/GDScript/` present
- [x] `test_gdscript_seam_is_concrete_not_example` — AC #3: not preceded by `e.g.`
- [x] `test_public_filename_is_runtime_neutral` ×11 — AC #2: filenames
- [x] `test_public_namespace_is_runtime_neutral` ×11 — AC #2: namespace declarations
- [x] `test_public_type_declarations_are_runtime_neutral` ×11 — AC #2: type declaration lines

---

## Story 1.6: Generate and Regenerate Typed Module Bindings

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_1_6_generate_bindings.py`

16 new tests added filling 8 discovered gaps. Total: 17 → **33** tests.

| New Test | Gap Filled | Downstream Risk |
|----------|-----------|----------------|
| `test_smoke_test_lib_rs_defines_id_field` | Field name `id` not verified; cascades into C# `Id` column | Story 1.7+ |
| `test_smoke_test_lib_rs_defines_value_field` | Field name `value` not verified; cascades into C# `Value` column | Story 1.7+ |
| `test_smoke_test_cargo_toml_has_spacetimedb_dependency` | Module won't compile without the crate dep | AC 1, 2 |
| `test_codegen_script_has_strict_error_mode` | `set -euo pipefail` not verified; AC3 requires exit non-zero on failure | AC 3 |
| `test_generated_types_smoke_test_file_exists` | Specific file `Types/SmokeTest.g.cs` not guarded | Story 1.7 |
| `test_generated_reducers_ping_file_exists` | Specific file `Reducers/Ping.g.cs` not guarded | Story 1.7, 1.9 |
| `test_generated_tables_smoke_test_file_exists` | Specific file `Tables/SmokeTest.g.cs` not guarded | Story 1.7 |
| `test_generated_spacetimedb_client_file_exists` | `SpacetimeDBClient.g.cs` (aggregate registry) not guarded | Story 1.9 |
| `test_generated_types_contains_smoke_test_class` | `class SmokeTest` type name stability not verified | Story 1.7, 1.9 |
| `test_generated_reducers_contains_ping_method` | `Ping` reducer name stability not verified | Story 1.9 |
| `test_generated_files_have_autogen_banner` | No guard against hand-editing generated output | Ongoing |
| `test_demo_generated_readme_exists` | Required deliverable from Task 3 had no test | Task 3 |
| `test_demo_generated_readme_mentions_script` | README content correctness unverified | Task 3 |
| `test_support_baseline_has_codegen_script_path` | Task 5 `required_paths` entry unverified | Task 5 |
| `test_support_baseline_has_demo_generated_path` | Task 5 `required_paths` entry unverified | Task 5 |
| `test_support_baseline_has_codegen_script_line_check` | Task 5 `line_checks` entry unverified | Task 5 |

### Original 17 tests (pre-gap)

- [x] Module source: Cargo.toml + lib.rs existence, cdylib, table name `smoke_test`, reducer name `ping`
- [x] Codegen script: exists, calls `spacetime generate`, `--lang csharp`, `smoke_test` module, `demo/generated/smoke_test` output
- [x] Generated bindings: dir exists, ≥1 `.cs` file
- [x] `docs/codegen.md`: references `generate-smoke-test.sh` and `demo/generated/smoke_test`
- [x] Regression guards: `docs/codegen.md` exists, `spacetime/modules/smoke_test/` dir, `tests/fixtures/generated/` dir

---

## Totals

| Suite | Tests |
|-------|-------|
| `test_story_1_3_sdk_concepts.py` | 100 |
| `test_story_1_4_adapter_boundary.py` | 45 |
| `test_story_1_5_gdscript_continuity.py` | 60 |
| `test_story_1_6_generate_bindings.py` | 33 |
| **Full suite** | **240** |

All 240 tests pass (`pytest -q` verified 2026-04-14).

## Next Steps

- Run `pytest tests/` as part of CI to enforce structural contracts across all stories
- Story 1.7 (explain generated types) should add tests referencing `SmokeTest`/`Ping` type names and `SpacetimeDB.Types` namespace
- Story 1.9 (first connection) should add integration tests using `DbConnection`, `SmokeTest` table, and `Ping` reducer
