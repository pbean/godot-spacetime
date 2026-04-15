# Test Automation Summary — Story 6.1 Gap Analysis

**Date:** 2026-04-15
**Story:** 6.1 — Publish the Canonical Compatibility Matrix and Support Policy
**Framework:** pytest (Python, static file-analysis pattern)

---

## Generated Tests

### Gap Tests Added to Story 6.1 Test File

File: `tests/test_story_6_1_publish_the_canonical_compatibility_matrix_and_support_policy.py`

11 new tests appended as `## Gap coverage` sections:

| Test | What It Guards |
|------|----------------|
| `test_version_baseline_contains_dot_net_version` | `.NET 8.0+` present in Supported Version Baseline (AC 1) |
| `test_version_baseline_contains_godot_net_sdk_version_number` | `Godot.NET.Sdk 4.6.1` version string in baseline (AC 1) |
| `test_version_baseline_contains_client_sdk_version_number` | `SpacetimeDB.ClientSDK 2.1.0` version string in baseline (AC 1) |
| `test_compatibility_matrix_has_adopter_facing_title` | Document opens with `# Compatibility Matrix and Support Policy` (AC 3) |
| `test_scope_of_this_matrix_section_present` | `## Scope of This Matrix` section exists (document completeness) |
| `test_canonical_references_appear_before_first_section_heading` | All 4 canonical doc refs appear in opening paragraph before first `##` (AC 3) |
| `test_no_story_1_1_reference_anywhere_in_document` | `Story \`1.1\`` absent from full document, not just first 500 chars (AC 3) |
| `test_connection_auth_status_panel_no_auth_required_enum_reference` | `ConnectionAuthState.AuthRequired` enum ref removed from panel switch (D1/C1) |
| `test_runtime_boundaries_externalization_sentence_names_project_settings_token_store` | Exact phrase `ProjectSettingsTokenStore\` is \`internal sealed\`` present (C3) |
| `test_runtime_boundaries_externalization_sentence_states_cannot_be_instantiated` | Phrase `cannot be instantiated from outside the SDK` present (C3) |
| `test_version_change_guidance_references_validate_foundation_script` | `validate-foundation.py` referenced in Version Change Guidance section (AC 1) |

---

## Coverage

| Area | Before | After |
|------|--------|-------|
| Story 6.1 test file | 46 tests | 57 tests |
| Full suite | 1937 passing | 1948 passing |
| Failures | 0 | 0 |

---

## Gaps Closed

- **AC 1 version completeness**: `.NET 8.0+`, `Godot.NET.Sdk 4.6.1`, and `SpacetimeDB.ClientSDK 2.1.0` now each have dedicated version-string checks in the Supported Version Baseline section.
- **AC 3 structural precision**: Canonical references verified in opening paragraph (not just anywhere in document); full-document `Story \`1.1\`` removal confirmed (stronger than the original 500-char window check).
- **D1/C1 panel enum reference**: `ConnectionAuthState.AuthRequired` enum reference removal from `ConnectionAuthStatusPanel.cs` now explicitly guarded — distinct from the `"AUTH REQUIRED"` display string which legitimately remains as a UX label.
- **C3 sentence precision**: `ProjectSettingsTokenStore` name and `cannot be instantiated` phrase verified — guards against paraphrase or omission of the required sentence.
- **Document completeness**: `## Scope of This Matrix` section presence and document title verified.
- **Version Change Guidance tooling ref**: `validate-foundation.py` reference in guidance section confirmed.

## Next Steps

- Run tests in CI on PR
- Story 6.1 is ready for review sign-off
