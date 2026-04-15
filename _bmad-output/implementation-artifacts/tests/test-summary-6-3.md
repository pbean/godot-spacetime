# Test Automation Summary — Story 6.3

## Generated Tests

### API / Integration Tests

- [x] `tests/test_story_6_3_validate_release_candidates_against_the_supported_workflow.py`
  — Validation orchestration script, CI workflow, and publication gate (86 tests total)

## Coverage Added (36 new tests)

### `check_packaging_inline` — unit tests (16 tests)

| Test | What it covers |
|---|---|
| `test_packaging_inline_passes_with_minimal_valid_zip` | Success path with a minimal conforming ZIP |
| `test_packaging_inline_fails_when_zip_missing` | Non-existent path → `"Candidate ZIP not found"` |
| `test_packaging_inline_fails_when_zip_is_corrupt` | Bad bytes → `"ZIP integrity error"` |
| `test_packaging_inline_fails_missing_plugin_cfg` | Required entry `plugin.cfg` absent |
| `test_packaging_inline_fails_missing_godot_plugin_cs` | Required entry `GodotSpacetimePlugin.cs` absent |
| `test_packaging_inline_fails_no_src_cs_files` | No `.cs` files under `src/` |
| `test_packaging_inline_fails_no_notices_entry` | No `thirdparty/notices` entries |
| `test_packaging_inline_fails_uid_extension` | `.uid` file in ZIP (excluded extension) |
| `test_packaging_inline_fails_import_extension` | `.import` file in ZIP (excluded extension) |
| `test_packaging_inline_fails_demo_prefix` | `demo/` prefix (excluded prefix) |
| `test_packaging_inline_fails_tests_prefix` | `tests/` prefix (excluded prefix) |
| `test_packaging_inline_fails_scripts_prefix` | `scripts/` prefix (excluded prefix) |
| `test_packaging_inline_fails_csproj_suffix` | `.csproj` suffix (excluded suffix) |
| `test_packaging_inline_fails_sln_suffix` | `.sln` suffix (excluded suffix) |
| `test_packaging_inline_fails_file_outside_addon_prefix` | Entry outside `addons/godot_spacetime/` |
| `test_packaging_inline_errors_capped_at_ten` | Error list is sliced to 10 max |

### `run_subprocess` — unit tests (4 tests)

| Test | What it covers |
|---|---|
| `test_run_subprocess_returns_pass_on_zero_exit` | Exit 0 → `"pass"` status |
| `test_run_subprocess_returns_fail_on_nonzero_exit` | Exit N → `"fail"` with `"exit N"` detail |
| `test_run_subprocess_detail_is_ok_when_no_output` | No stdout/stderr → `detail == "OK"` |
| `test_run_subprocess_truncates_detail_at_500_chars` | 600-char output truncated to ≤ 500 |

### Integration — default behavior (2 tests)

| Test | What it covers |
|---|---|
| `test_script_reads_version_from_plugin_cfg` | `--version` omitted → reads `0.1.0-dev` from `plugin.cfg` |
| `test_script_default_report_path_is_under_release_candidates` | `--report` omitted → writes to `release-candidates/validation-report-v{ver}.json` |

### Human-readable stdout (6 tests)

| Test | What it covers |
|---|---|
| `test_script_stdout_progress_marker_1of4` | `[1/4]` packaging progress line |
| `test_script_stdout_progress_marker_2of4` | `[2/4]` foundation progress line |
| `test_script_stdout_progress_marker_3of4` | `[3/4]` test-suite progress line |
| `test_script_stdout_progress_marker_4of4` | `[4/4]` packaging-checks progress line |
| `test_script_stdout_overall_status_line` | `Overall status:` summary line |
| `test_script_stdout_mentions_report_path` | `Report written:` path announcement |

### Report portability (1 test)

| Test | What it covers |
|---|---|
| `test_report_candidate_is_relative_path` | `candidate` is a relative path (not `/...`) |

### Workflow structural checks (7 tests)

| Test | What it covers |
|---|---|
| `test_workflow_upload_step_runs_on_always` | Upload step has `if: always()` (AC 2) |
| `test_workflow_upload_ignores_missing_files` | `if-no-files-found: ignore` present |
| `test_workflow_artifact_named_validation_report` | Artifact named `validation-report` (AC 3) |
| `test_workflow_uses_checkout_v4` | `actions/checkout@v4` used |
| `test_workflow_uses_setup_python_v5` | `actions/setup-python@v5` used |
| `test_workflow_version_input_required_false` | `version` input is `required: false` |
| `test_workflow_job_runs_on_ubuntu_latest` | Job uses `ubuntu-latest` runner |

## Results

| Metric | Count |
|---|---|
| Tests before QA review | 50 |
| Tests added | 36 |
| **Total tests** | **86** |
| Passing | 86 |
| Failing | 0 |
| Run time | 2.57s |

## Next Steps

- Run full test suite (`pytest -q`) to confirm no regressions in other stories
- Story 6.4 can consume the publication gate contract verified by these tests
