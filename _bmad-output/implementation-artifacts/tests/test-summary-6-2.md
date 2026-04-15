# Test Automation Summary — Story 6.2

**Date:** 2026-04-15
**Story:** 6.2 — Package Reproducible Versioned Release Candidates

---

## Gap Discovery Results

All 52 pre-existing Story 6.2 tests passed. Gap analysis identified 9 untested
behavioral contracts. All gaps were auto-applied.

---

## Generated Tests

### Gap Tests Added — `tests/test_story_6_2_package_reproducible_versioned_release_candidates.py`

| Section | Test | Gap Covered |
|---------|------|-------------|
| 3.11 | `test_packaged_zip_entries_have_correct_permissions` | `external_attr = 0o644 << 16` per reproducibility contract (Dev Notes AC 2) |
| 3.11 | `test_packaged_zip_entries_use_deflate_compression` | `compress_type = ZIP_DEFLATED` on every entry |
| 3.11 | `test_packaged_zip_entries_are_sorted` | Alphabetical entry order in raw ZIP (not just namelist) |
| 3.12 | `test_script_prints_version_line` | stdout `"Version: {version}"` line from `main()` |
| 3.12 | `test_script_prints_packaged_summary_line` | stdout `"Packaged N files into <path>"` line |
| 3.12 | `test_script_prints_candidate_line` | stdout `"Candidate: {filename}"` line |
| 3.13 | `test_support_baseline_does_not_include_scripts_packaging` | `scripts/packaging/` must NOT be in `support-baseline.json` (Dev Notes architecture constraint) |
| 3.14 | `test_packaged_zip_contains_assets_directory` | `assets/` directory inclusion |
| 3.14 | `test_packaged_zip_contains_icon_svg` | `assets/icon.svg` specifically included |

---

## Coverage

- Story 6.2 ACs: 3/3 fully covered
- CLI output contract: version line, summary line, candidate line
- Reproducibility contract: fixed timestamp, fixed permissions, DEFLATE compression, sorted entries
- Architecture isolation: `scripts/packaging/` excluded from `support-baseline.json`
- Content: addon files, assets, notices all verified

## Results

```
61 passed in 0.30s
```

## Next Steps

- Story 6.3 will call `package-release.py` in the GitHub release validation flow
- Story 6.4 will use the same script for publication
