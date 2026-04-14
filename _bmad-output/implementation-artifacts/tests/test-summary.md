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

## Totals

| Suite | Tests |
|-------|-------|
| `test_story_1_3_sdk_concepts.py` | 100 |
| `test_story_1_4_adapter_boundary.py` | 45 |
| **Full suite** | **145** |

All 145 tests pass.

## Next Steps

- Run `pytest tests/` as part of CI to enforce structural contracts across both stories
- Story 1.5 (GDScript continuity seam) should add tests verifying the Public/Internal seam is accessible from GDScript
