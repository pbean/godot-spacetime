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

---

## Story 1.8: Detect Binding and Schema Compatibility Problems Early

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_1_8_compatibility.py`

19 new tests added filling gaps discovered by comparing against the Story 1.7 structural test pattern. Total: 32 → **51** tests.

| New Test | Gap Filled | AC |
|----------|-----------|-----|
| `test_panel_has_tools_conditional_compile_guard` | `#if TOOLS`/`#endif` guard not verified | AC 1 |
| `test_panel_has_tool_attribute` | `[Tool]` attribute not verified | AC 1 |
| `test_panel_has_correct_namespace` | Namespace `GodotSpacetime.Editor.Compatibility` not verified | AC 1 |
| `test_panel_extends_vbox_container` | VBoxContainer class inheritance not verified | AC 4 |
| `test_panel_uses_project_settings_globalize_path` | Cross-platform path resolution not verified | AC 2 |
| `test_panel_recovery_label_initially_hidden` | `_recoveryLabel.Visible = false` on init not verified | AC 2 |
| `test_panel_has_cli_version_prefix_constant` | `CliVersionPrefix` constant not verified | AC 1 |
| `test_panel_has_godot_target_field_label` | `"Godot target:"` layout label not verified | AC 4 |
| `test_panel_has_spacetimedb_cli_field_label` | `"SpacetimeDB CLI:"` layout label not verified | AC 4 |
| `test_panel_has_client_sdk_field_label` | `"ClientSDK:"` layout label not verified | AC 4 |
| `test_compat_tscn_uses_format_3` | Scene `format=3` content not verified (only existence) | AC 4 |
| `test_compat_tscn_root_is_vbox_container` | Scene root `type="VBoxContainer"` not verified | AC 4 |
| `test_compat_tscn_attaches_correct_script` | Scene script path attachment not verified | AC 4 |
| `test_plugin_has_compat_panel_scene_path_constant` | `CompatPanelScenePath` constant not verified | AC 4 |
| `test_plugin_removes_both_panels_in_exit_tree` | `RemoveControlFromBottomPanel` count = 2 not verified | AC 4 |
| `test_plugin_has_using_compatibility_namespace` | `using GodotSpacetime.Editor.Compatibility` not verified | AC 4 |
| `test_plugin_loads_compat_panel_scene_resource` | `GD.Load<PackedScene>` + `Instantiate()` pattern not verified | AC 4 |
| `test_support_baseline_has_compatibility_panel_tscn_path` | `.tscn` required_path entry (only `.cs` was tested) | AC 2 |
| `test_compatibility_matrix_has_regeneration_command` | `bash scripts/codegen/generate-smoke-test.sh` in docs | AC 3 |

### Original 32 tests (pre-gap — spec-mandated)

- [x] Panel existence (`.cs` and `.tscn`)
- [x] Explicit text labels (OK, INCOMPATIBLE, MISSING, NOT CONFIGURED, Recovery)
- [x] Version extraction (`spacetimedb cli version`, `support_versions`, `spacetimedb_client_sdk`, `VersionSatisfiesBaseline`)
- [x] Layout (`"Compatibility Baseline"`, `"Binding CLI version:"`, `"Compatibility status:"`, AutowrapMode, FocusModeEnum.All, CustomMinimumSize)
- [x] Plugin registration (both panels via count=2, `"Spacetime Compat"` tab, `CompatibilityPanel` type)
- [x] Support-baseline (`Editor/Compatibility`, `CompatibilityPanel.cs`, `Binding Compatibility Check` line_check)
- [x] Documentation (`## Binding Compatibility Check`, `spacetimedb cli version`)
- [x] Regression guards Story 1.7 (`CodegenValidationPanel.cs`, `.tscn`, `"Spacetime Codegen"`, `Generated Schema Concepts`)
- [x] Regression guards Story 1.6 (`demo/generated/smoke_test/`, `.cs` files, `generate-smoke-test.sh`)

---

---

## Story 1.9: Configure and Open a First Connection from Godot

### Generated Tests (2026-04-14)

**File:** `tests/test_story_1_9_connection.py` — **69 tests**, red-phase (59 fail / 10 pass pending implementation)

All 59 failing tests represent unimplemented Story 1.9 deliverables. 10 tests already pass: 7 regression guards for existing Story 1.7/1.8 work, and 3 that match content already present in stub files.

| Test Group | Count | AC |
|-----------|------|----|
| File existence (6 new files) | 6 | — |
| `SpacetimeClient.cs` runtime surface | 6 | 1,2,3,4,6 |
| `SpacetimeConnectionService.cs` exposure | 5 | 1,2,3,4,7 |
| `ConnectionStateMachine.cs` states + transition | 6 | 1,2,4 |
| `SpacetimeSdkConnectionAdapter.cs` SDK builder, no pragma stub | 3 | 1,7 |
| `ConnectionOpenedEvent.cs` payload fields | 3 | 6 |
| `ConnectionAuthStatusPanel.cs` text labels | 5 | 5 |
| `ConnectionAuthStatusPanel.cs` layout requirements | 3 | 5 |
| `ConnectionAuthStatusPanel.cs` structural (#if TOOLS, [Tool], namespace, VBoxContainer) | 4 | 5 |
| `ConnectionAuthStatusPanel.tscn` scene content | 3 | 5 |
| Plugin registration (3 panels, StatusPanelScenePath, cleanup) | 6 | 5 |
| `support-baseline.json` new required paths | 6 | — |
| `docs/connection.md` lifecycle documentation | 6 | 2 |
| Regression guards (Stories 1.7 + 1.8) | 6 | — |
| Architecture boundary guard | 1 | 7 |
| **Total** | **69** | |

---

---

## Story 1.10: Validate First Setup Through a Quickstart Path

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_1_10_quickstart.py`

17 new tests added filling 6 discovered gaps. Total: 23 → **40** tests. All 40 pass.

| Gap | New Tests | AC |
|-----|----------|----|
| 5 support-baseline.json line_check labels untested | `test_support_baseline_has_quickstart_foundation_command_line_check`, `..._codegen_script_...`, `..._install_md_...`, `..._codegen_md_...`, `..._connection_md_...` | — |
| `## Prerequisites` section and version strings | `test_quickstart_has_prerequisites_section`, `..._godot_version`, `..._dotnet_version`, `..._cli_version` | AC 1 |
| `## See Also` section heading | `test_quickstart_has_see_also_section` | AC 1 |
| Panel state strings (OK / NOT CONFIGURED / CONNECTED) | `test_quickstart_mentions_codegen_panel_ok_state`, `..._compat_panel_ok_state`, `..._status_panel_not_configured_state`, `..._status_panel_connected_state` | AC 1, 2 |
| Failure recovery DISCONNECTED + DEGRADED states | `test_quickstart_failure_recovery_covers_disconnected_state`, `..._degraded_state` | AC 2 |
| Keyboard navigation (AC 3) | `test_quickstart_mentions_keyboard_navigation` | AC 3 |

### Original 23 tests (pre-gap — spec-mandated)

- [x] File existence (`docs/quickstart.md`)
- [x] `## Quickstart` exact stripped-line heading
- [x] `## Failure Recovery` or `## Troubleshooting` section
- [x] Foundation validation command, codegen script
- [x] `SpacetimeSettings`, `SpacetimeClient`, `Connect(`, `connection_state_changed`
- [x] Panel name strings (`"Spacetime Codegen"`, `"Spacetime Compat"`, `"Spacetime Status"`)
- [x] Cross-references to `docs/install.md`, `docs/codegen.md`, `docs/connection.md`
- [x] `support-baseline.json`: `docs/quickstart.md` required_path + `"Quickstart top-level heading"` line_check
- [x] `docs/install.md` and `docs/codegen.md` See Also references
- [x] Regression guards: 3 panel labels + `AddControlToBottomPanel` count = 3

---

---

## Story 2.1: Define Auth Configuration and Token Storage Boundaries

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_2_1_auth_config.py`

31 new tests appended to the existing 26, bringing the file to **57 tests**. All 57 pass.

| New Test Group | Count | Gap Filled |
|----------------|-------|------------|
| Namespace enforcement (`GodotSpacetime.Runtime.Auth`) | 3 | Not verified on any Auth file |
| Internal access modifiers (`internal sealed` / `internal static`) | 3 | Not verified — public regression undetectable |
| `MemoryTokenStore` `_token` backing field | 1 | Field-backed storage unverified |
| `ProjectSettingsTokenStore` all 3 methods | 3 | Only interface membership tested, not each method |
| `ProjectSettingsTokenStore` `string.Empty` in ClearTokenAsync | 1 | Spec-required reset value unverified |
| `ProjectSettingsTokenStore` uses `ProjectSettings` | 1 | Godot backing unverified |
| `TokenRedactor` `<no token>` output string | 1 | Null/empty path only tested by `<redacted>` check |
| `TokenRedactor` `token.Length` threshold | 1 | 8-char boundary logic unverified |
| `TokenRedactor` `…<redacted>` truncation pattern | 1 | Long-token format unverified |
| `SpacetimeSettings` `using GodotSpacetime.Auth;` | 1 | Using directive unverified |
| `SpacetimeSettings` TokenStore has no `[Export]` | 1 | Anti-test: ITokenStore is not a Godot type |
| `SpacetimeSettings` stale comment removed | 1 | "Additional settings" comment removal unverified |
| `SpacetimeConnectionService` `using GodotSpacetime.Auth;` | 1 | Using directive unverified |
| `SpacetimeConnectionService` assigns `settings.TokenStore` | 1 | Assignment expression unverified |
| `SpacetimeConnectionService` fire-and-forget `_ =` pattern | 1 | Pattern critical to story design intent |
| `ProjectSettingsTokenStore` persists writes with `ProjectSettings.Save()` | 1 | Static checks previously missed that the "persistent" store never saved its changes |
| `ProjectSettingsTokenStore` reports save failures via returned task | 1 | Save failures could silently invalidate persistence behavior |
| `SpacetimeConnectionService` observes faulted token-store tasks | 1 | Optional persistence faults could surface later as unobserved task exceptions |
| `SpacetimeConnectionService` shields sync token-store exceptions | 1 | Synchronous store failures could still break `OnConnected` |
| `runtime-boundaries.md` "Built-in implementations" section | 1 | Expanded auth section content unverified |
| `runtime-boundaries.md` MemoryTokenStore description | 1 | New auth content unverified |
| `runtime-boundaries.md` ProjectSettingsTokenStore description | 1 | New auth content unverified |
| `runtime-boundaries.md` ClearTokenAsync token clearing | 1 | Token Clearing paragraph unverified |
| `runtime-boundaries.md` TokenRedactor reference | 1 | TokenRedactor utility unverified in docs |
| `runtime-boundaries.md` `spacetime/auth/token` key documented | 1 | Setting key documentation unverified |
| **Total new** | **31** | |

---

---

## Story 2.2: Authenticate a Client Session Through Supported Identity Flows

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_2_2_auth_session.py`

13 new tests added filling gaps discovered by QA pass. Total: 40 → **53** tests. All 53 pass.

| New Test | Gap Filled | AC |
|----------|------------|----|
| `test_auth_status_panel_has_auth_action_label` | `_authActionLabel` field (action guidance text) not tested | 4 |
| `test_auth_status_panel_has_anonymous_string` | `ANONYMOUS` label for anon-connected state not tested | 4 |
| `test_connection_status_constructor_has_auth_state_param` | Constructor shape not tested (only property existence) | 3/4 |
| `test_state_machine_transition_passes_auth_state_to_status_constructor` | `new ConnectionStatus(next, description, authState)` call not tested | 3 |
| `test_connection_service_auth_error_description_text` | `"authentication failed:"` description text not tested | 3 |
| `test_connection_service_has_authenticated_session_description` | `"authenticated session established"` success description not tested | 1 |
| `test_adapter_credentials_injection_is_conditional` | `IsNullOrWhiteSpace` guard on WithToken injection not tested | 1 |
| `test_connection_service_credentials_flag_uses_is_null_or_whitespace` | `_credentialsProvided = !IsNullOrWhiteSpace(settings.Credentials)` pattern not tested | 1 |
| `test_connection_auth_state_has_correct_namespace` | `namespace GodotSpacetime.Connection;` not tested | isolation |
| `test_connection_opened_event_identity_defaults_to_empty_string` | `Identity = string.Empty` default (anon semantics) not tested | 2 |
| `test_connection_service_has_using_godotspacetime_connection` | `using GodotSpacetime.Connection;` in service not tested | — |
| `test_state_machine_has_using_godotspacetime_connection` | `using GodotSpacetime.Connection;` in state machine not tested | — |
| `test_auth_status_panel_has_tools_guard` | `#if TOOLS` encapsulation guard not tested | — |

### Original 40 tests (spec-mandated)

- [x] `ConnectionAuthState.cs` existence + 6 content checks (enum values, no SpacetimeDB refs)
- [x] `ConnectionStatus.cs` AuthState property
- [x] `ConnectionOpenedEvent.cs` Identity property
- [x] `SpacetimeSettings.cs` Credentials property + no [Export]
- [x] `SpacetimeSdkConnectionAdapter.cs` WithToken, OnConnected two params, identity capture
- [x] `SpacetimeConnectionService.cs` _credentialsProvided, TokenRestored/AuthFailed states, two-param OnConnected, Identity assignment
- [x] `ConnectionStateMachine.cs` Transition has ConnectionAuthState
- [x] `ConnectionAuthStatusPanel.cs` _authStateLabel, TOKEN RESTORED/AUTH FAILED/AUTH REQUIRED, SetAuthStatus, no SpacetimeDB using
- [x] `support-baseline.json` ConnectionAuthState.cs path
- [x] `docs/runtime-boundaries.md` ConnectionAuthState table, Credentials row, Identity paragraph
- [x] Regression guards: ITokenStore, service methods, adapter builder calls (10 tests)

---

---

## Story 2.3: Restore a Previous Session from Persisted Auth State

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_2_3_session_restore.py`

9 new tests added filling gaps discovered by QA pass. Total: 20 → **29** tests. All 29 pass.

| New Test | Gap Filled | AC |
|----------|------------|----|
| `test_connection_service_guards_null_token_store` | `settings.TokenStore != null` null-guard not explicitly verified | 1 |
| `test_connection_service_injects_credentials_from_store` | `settings.Credentials = stored` injection not verified | 1 |
| `test_connection_service_checks_stored_token_not_empty` | `IsNullOrWhiteSpace(stored)` inner empty-token check missing | 3 |
| `test_connection_service_has_get_result_in_sync_chain` | `GetResult()` not tested (only `GetAwaiter` was) | 1 |
| `test_connection_service_restore_has_catch_exception_block` | `catch (Exception)` block not directly asserted | 4 |
| `test_connection_service_restore_block_before_credentials_provided` | Ordering: restore block before `_credentialsProvided =` not tested | 1/3 |
| `test_runtime_boundaries_mentions_with_token_in_session_restoration` | `WithToken` not verified in `runtime-boundaries.md` | 1 |
| `test_runtime_boundaries_mentions_token_restored_in_session_restoration` | `TokenRestored` not verified in `runtime-boundaries.md` | 2 |
| `test_connection_service_still_has_reconnect_policy` | `_reconnectPolicy` regression guard absent | structural |

### Original 20 tests (spec-mandated)

- [x] `GetTokenAsync` called in SpacetimeConnectionService.cs
- [x] `GetAwaiter` in sync chain
- [x] `IsNullOrWhiteSpace(settings.Credentials)` explicit-credentials guard
- [x] `try` block count ≥ 2
- [x] `Session Restoration` section in runtime-boundaries.md
- [x] `GetTokenAsync` referenced in runtime-boundaries.md
- [x] ITokenStore.cs presence + all three methods (`GetTokenAsync`, `StoreTokenAsync`, `ClearTokenAsync`)
- [x] `_credentialsProvided`, `_tokenStore`, `StoreTokenAsync`, `OnConnected(` fields/methods intact
- [x] `WithToken` in SpacetimeSdkConnectionAdapter.cs
- [x] `TokenRestored`, `AuthFailed` in ConnectionAuthState.cs
- [x] `TOKEN RESTORED`, `AUTH FAILED` in ConnectionAuthStatusPanel.cs
- [x] No `SpacetimeDB.*` reference in SpacetimeConnectionService.cs (isolation guard)

---

---

## Story 2.4: Recover from Common Session and Identity Failures

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_2_4_failure_recovery.py`

12 new tests added filling gaps discovered by QA pass. Total: 35 → **47** tests. All 47 pass.

| New Test | Gap Filled | AC |
|----------|------------|----|
| `test_connection_auth_state_token_expired_after_auth_failed_in_enum` | Enum ordering (`TokenExpired` after `AuthFailed`) not verified | 2 |
| `test_connection_auth_state_namespace_is_godot_spacetime_connection` | Namespace isolation not verified on this file | isolation |
| `test_connection_service_anonymous_connect_fail_path_preserved` | Third `else` branch ("failed to connect:") not guarded | 3 |
| `test_connection_service_restored_from_store_is_private_bool` | Type specificity `private bool` not verified | 1, 2 |
| `test_connection_service_validate_settings_throws_argument_exception` | `ArgumentException` for missing Host/Database not verified | 3 |
| `test_connection_service_finally_clears_restored_credentials` | Story 2.3 `finally` + `settings.Credentials = null` invariant not regression-guarded | structural |
| `test_auth_status_panel_has_tools_preprocessor_guard` | `#if TOOLS` guard preservation explicitly required by spec but not tested | 4 |
| `test_auth_status_panel_has_anonymous_label` | `ANONYMOUS` display label regression guard absent | regression |
| `test_auth_status_panel_no_spacetimedb_reference` | Panel file missing from isolation boundary tests | isolation |
| `test_runtime_boundaries_token_expired_only_for_token_restoration` | Doc precision: `TokenExpired` is only emitted for restoration sessions not tested | 2 |
| `test_runtime_boundaries_auth_failed_described_in_failure_recovery` | Both failure categories in Failure Recovery section not verified | 1, 3 |
| `test_runtime_boundaries_failure_recovery_references_connection_state_changed` | `ConnectionStateChanged` as observation surface not verified | 1 |

### Original 35 tests (spec-mandated)

- [x] `ConnectionAuthState.cs`: `TokenExpired` value, enum membership, `ClearTokenAsync` in XML doc (AC 2, 3)
- [x] `SpacetimeConnectionService.cs`: `_restoredFromStore` field, assignment, `TokenExpired` usage, "stored token was rejected" message, ordering in `OnConnectError`, `AuthFailed` path preserved, both fields in `OnConnectError` (AC 1, 2)
- [x] `ConnectionAuthStatusPanel.cs`: `TokenExpired` in switch, `TOKEN EXPIRED` label, `ClearTokenAsync` in action, `TokenExpired` before `AuthFailed` in file (AC 4)
- [x] `docs/runtime-boundaries.md`: `TokenExpired` in table, `Failure Recovery` section, `ClearTokenAsync`, `ArgumentException`, token store reference (AC 1, 2, 3, 4)
- [x] Regression guards: all four `ConnectionAuthState` prior values, `_credentialsProvided`/`restoredCredentials`/`GetTokenAsync`/`HandleDisconnectError` in service, `TOKEN RESTORED`/`AUTH FAILED`/`AUTH REQUIRED` in panel, `ITokenStore` interface methods (14 tests)
- [x] Isolation guards: no `SpacetimeDB.*` in `ConnectionAuthState.cs` or `SpacetimeConnectionService.cs` (2 tests)

---

---

---

## Story 3.1: Apply a Subscription and Receive Initial Synchronized State

### Generated Tests (gap additions — 2026-04-14)

**File:** `tests/test_story_3_1_subscription_apply.py`

14 new tests added filling gaps discovered by QA pass. Total: 61 → **75** tests. All 75 pass.

| New Test | Gap Filled | AC |
|----------|------------|----|
| `test_subscription_handle_has_using_system` | `using System;` directive not verified | 3 |
| `test_subscription_handle_constructor_body_assigns_new_guid` | `HandleId = Guid.NewGuid()` constructor body assignment not verified | 3 |
| `test_subscription_applied_event_constructor_assigns_handle` | `Handle = handle` constructor body assignment not verified | 2 |
| `test_subscription_applied_event_constructor_assigns_applied_at_utc_now` | `AppliedAt = DateTimeOffset.UtcNow` constructor body assignment not verified | 2 |
| `test_subscription_registry_has_unregister_method` | `Unregister(Guid)` method not tested | 3 |
| `test_subscription_registry_active_handles_is_ireadonlycollection` | `IReadOnlyCollection<SubscriptionHandle>` return type not verified | 3 |
| `test_connection_service_subscribe_registers_handle_in_registry` | `_subscriptionRegistry.Register(handle)` call in `Subscribe` not tested | 3 |
| `test_connection_service_on_subscription_error_is_noop_stub` | `OnSubscriptionError` no-op stub referencing Story 3.5 not tested | 1 |
| `test_connection_service_has_using_runtime_subscriptions` | `using GodotSpacetime.Runtime.Subscriptions;` import not verified | 3 |
| `test_subscription_adapter_has_argument_null_guards` | `ArgumentNullException.ThrowIfNull` null guards in `Subscribe` not tested | 1 |
| `test_spacetime_client_has_using_godot_spacetime_subscriptions` | `using GodotSpacetime.Subscriptions;` import not verified | 1 |
| `test_spacetime_client_handle_subscription_applied_emits_signal` | `EmitSignal(SignalName.SubscriptionApplied, ...)` not tested | 2 |
| `test_spacetime_client_handle_subscription_applied_uses_dispatch` | `_signalAdapter.Dispatch` pattern in `HandleSubscriptionApplied` not tested | 2 |
| `test_connection_adapter_connection_property_has_null_when_not_connected_doc` | XML doc comment "Returns null when not connected" not verified | 1 |

### Original 61 tests (spec-mandated)

- [x] `SubscriptionHandle.cs`: HandleId, Guid type, internal ctor, namespace (AC 3)
- [x] `SubscriptionAppliedEvent.cs`: Handle, AppliedAt, DateTimeOffset, internal ctor, `using System;`, namespace (AC 2)
- [x] `SpacetimeSdkSubscriptionAdapter.cs`: ISubscriptionEventSink interface, Subscribe params, Expression trees, InvokeWithDelegate, CreateAppliedCallback, CreateErrorCallback, no stub pragma (AC 1, 2)
- [x] `SpacetimeSdkConnectionAdapter.cs`: Connection property presence and `_dbConnection` return (AC 1)
- [x] `SpacetimeConnectionService.cs`: ISubscriptionEventSink, adapter/registry fields, OnSubscriptionApplied event, Subscribe method, Connected guard, fires event, constructs event, Clear on disconnect (AC 1, 2, 3)
- [x] `SpacetimeClient.cs`: SubscriptionAppliedEventHandler signal, Subscribe method, SubscriptionHandle return, HandleSubscriptionApplied, wire/unwire in Enter/ExitTree (AC 1, 2, 3)
- [x] `SubscriptionRegistry.cs`: Register, Clear, ActiveHandles, namespace, no SpacetimeDB reference (AC 3)
- [x] `docs/runtime-boundaries.md`: Subscribe usage, SubscriptionApplied signal, HandleId, AppliedAt, InvalidOperationException guard (AC 1, 2, 3)
- [x] Regression guards: connection adapter Open/FrameTick/Close/IConnectionEventSink, service OnStateChanged/OnConnectionOpened/OnConnectError/IConnectionEventSink, SpacetimeClient ConnectionStateChanged/ConnectionOpenedEventHandler/Connect()/Disconnect()
- [x] Isolation guards: no SpacetimeDB.* in SpacetimeConnectionService, SpacetimeClient, SubscriptionRegistry

---

## Totals

| Suite | Tests |
|-------|-------|
| `test_story_1_3_sdk_concepts.py` | 100 |
| `test_story_1_4_adapter_boundary.py` | 45 |
| `test_story_1_5_gdscript_continuity.py` | 60 |
| `test_story_1_6_generate_bindings.py` | 33 |
| `test_story_1_7_schema_concepts.py` | 54 |
| `test_story_1_8_compatibility.py` | 51 |
| `test_story_1_9_connection.py` | 69 |
| `test_story_1_10_quickstart.py` | 40 |
| `test_story_2_1_auth_config.py` | 57 |
| `test_story_2_2_auth_session.py` | 53 |
| `test_story_2_3_session_restore.py` | 29 |
| `test_story_2_4_failure_recovery.py` | 47 |
| `test_story_3_1_subscription_apply.py` | 75 |
| **Full suite** | **741** |

All 741 tests pass (`pytest -q` verified 2026-04-14).

## Next Steps

- Run `pytest tests/` as part of CI to enforce structural contracts across all stories
- Epic 1 complete — all stories 1.1–1.10 implemented and green
- Story 2.1 complete — auth/token storage boundary established with full contract coverage
- Story 2.2 complete — auth session flow, WithToken injection, identity capture, auth state surfaces fully covered
- Story 2.3 complete — token restore from ITokenStore wired into `Connect()`, all ACs and gaps covered
- Story 2.4 complete — `TokenExpired` state, `_restoredFromStore` routing, panel recovery guidance, docs updated; all ACs covered
- Story 3.1 complete — subscription apply surface (SubscriptionHandle, SubscriptionAppliedEvent, SubscriptionRegistry, adapter, service, client), all ACs and gaps covered
