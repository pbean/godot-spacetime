# Story 6.4: Publish Approved SDK Releases for External Use

Status: done

## Story

As the SDK maintainer,
I want to publish approved SDK releases from the validated candidate payload,
So that external adopters receive the exact artifact that passed release validation.

## Acceptance Criteria

1. **Given** a release candidate has passed the supported validation workflow **When** I publish the SDK release for external adopters **Then** the official release publishes the exact validated candidate payload rather than a newly rebuilt artifact
2. **And** the published release metadata and download assets match the validated version, compatibility targets, and adopter-facing install guidance
3. **And** the release output is suitable for the GitHub-release-first distribution path defined for the product

## Tasks / Subtasks

- [x] Task 1: Create `scripts/packaging/publish-release.py` (AC: 1, 2, 3)
  - [x] 1.1 Accept `--version` (default: read from `addons/godot_spacetime/plugin.cfg` via `configparser`), `--report` (default: `release-candidates/validation-report-v{version}.json` relative to repo root), and `--dry-run` (flag: skip `gh release create`, print what would happen and exit 0)
  - [x] 1.2 Gate 1 — Report must exist: if `report_path` does not exist → print error "Validation report not found: {report_path}. Run validate-release-candidate.py first." to stderr and exit 1
  - [x] 1.3 Gate 2 — Parse JSON report; Gate 3 — verify `report["version"] == version` → if mismatch, exit 1 with message "Report version '{report_version}' does not match requested publish version '{version}'."; Gate 4 — verify `report["status"] == "pass"` → if fail, print per-check failure summary from `report["checks"]` and exit 1
  - [x] 1.4 Warn (do NOT fail): if `report["checks"]["test_suite"]["status"] == "skipped"` → print to stderr "WARNING: test_suite was skipped in the validation report. CI releases should not skip the test suite."
  - [x] 1.5 Gate 5 — Resolve `candidate_path = repo_root() / report["candidate"]`; verify it exists → if not, exit 1 with "Candidate ZIP not found: {candidate_path}"
  - [x] 1.6 If `--dry-run`: print "DRY RUN: Would create GitHub Release v{version}", "DRY RUN: Would upload {candidate_path}", "DRY RUN: Release skipped." then exit 0
  - [x] 1.7 Run `gh release create v{version} {candidate_path} --title "GodotSpacetime SDK v{version}" --notes "{notes}"` as subprocess from repo root (see Dev Notes for exact notes string); capture stdout/stderr; print success summary and exit 0 on exit code 0; print error and exit 1 otherwise

- [x] Task 2: Create `.github/workflows/release.yml` (AC: 1, 2, 3)
  - [x] 2.1 Create workflow with name `Publish Release`, trigger `workflow_dispatch` with `version` input (description: "Version to publish (leave blank to read from plugin.cfg)", `required: false`, `default: ''`); add `permissions: contents: write` at workflow level (required for `gh release create`)
  - [x] 2.2 Single job `publish-release` on `ubuntu-latest` with steps: `actions/checkout@v4`, `actions/setup-dotnet@v4` (dotnet-version: `8.0.x`), `actions/setup-python@v5` (python-version: `"3.12"`), a "Validate release candidate" step that runs `python3 scripts/packaging/validate-release-candidate.py` (with `--version "${{ inputs.version }}"` appended only when the input is non-empty), a "Publish release" step that runs `python3 scripts/packaging/publish-release.py` (with `--version "${{ inputs.version }}"` appended only when the input is non-empty) with env `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}`
  - [x] 2.3 Add "Upload validation report" step using `actions/upload-artifact@v4` with `if: always()`, artifact name `validation-report`, path `release-candidates/validation-report-*.json`, and `if-no-files-found: ignore`

- [x] Task 3: Write `tests/test_story_6_4_publish_approved_sdk_releases_for_external_use.py` (AC: 1, 2, 3)
  - [x] 3.1 Static existence tests: `scripts/packaging/publish-release.py` exists; `.github/workflows/release.yml` exists
  - [x] 3.2 Add `setup_module`/`teardown_module` hooks: (a) run `validate-release-candidate.py --version 0.1.0-dev --skip-suite` as subprocess from repo root; assert exit code 0 (produces both ZIP and report in `release-candidates/`); (b) run `publish-release.py --version 0.1.0-dev --dry-run` as subprocess from repo root; assert exit code 0; store combined stdout+stderr as `_DRY_RUN_OUTPUT` module global
  - [x] 3.3 Dry-run output tests: `"DRY RUN"` in `_DRY_RUN_OUTPUT`; `"0.1.0-dev"` in `_DRY_RUN_OUTPUT`
  - [x] 3.4 Report and candidate artifact tests: `release-candidates/validation-report-v0.1.0-dev.json` exists; parse it and assert `report["status"] == "pass"` (confirms the publication gate); `release-candidates/godot-spacetime-v0.1.0-dev.zip` exists
  - [x] 3.5 Script interface tests: run `publish-release.py --help` as subprocess; assert exit code 0; assert `"--dry-run"` in stdout
  - [x] 3.6 Workflow content tests: `release.yml` contains `workflow_dispatch`; contains `publish-release.py`; contains `validate-release-candidate.py`; contains `GITHUB_TOKEN`; contains `upload-artifact`
  - [x] 3.7 Regression guards: `scripts/packaging/validate-release-candidate.py` exists; `scripts/packaging/package-release.py` exists; `scripts/compatibility/validate-foundation.py` exists; `scripts/compatibility/support-baseline.json` exists; `.github/workflows/release-validation.yml` exists; `docs/compatibility-matrix.md` exists; `docs/install.md` exists; `plugin.cfg` version is `0.1.0-dev`; `.gitignore` contains `release-candidates/`

## Dev Notes

### What This Story Delivers

Story 6.4 closes the release pipeline by creating the publication step that consumes the validated candidate produced by Stories 6.2 and 6.3. The publish script reads the Story 6.3 validation report as its publication gate — it only proceeds when that report records `status == "pass"`. The on-demand GitHub Actions workflow runs validation inline and then publishes the resulting artifact to GitHub Releases.

**Primary deliverables:**
- `scripts/packaging/publish-release.py` — standalone Python 3 publication gate that reads the validation report, enforces the pass gate, and calls `gh release create` with the validated candidate ZIP
- `.github/workflows/release.yml` — on-demand CI workflow that runs validation then publishes; requires `permissions: contents: write`

**Secondary deliverable:**
- `tests/test_story_6_4_*.py` — verification suite covering script existence, dry-run behavior, report gate, workflow content, and regression guards

**No C# changes.** No modifications to any existing file in `addons/`, `docs/`, `demo/`, `tests/`, `scripts/compatibility/`, or `.github/workflows/release-validation.yml`. Do NOT modify `support-baseline.json` or `validate-foundation.py` or `package-release.py`.

### How the Publication Gate Works

Story 6.3 produces `release-candidates/validation-report-v{version}.json` with this structure:

```json
{
  "version": "0.1.0-dev",
  "timestamp": "2026-...",
  "status": "pass",
  "candidate": "release-candidates/godot-spacetime-v0.1.0-dev.zip",
  "checks": {
    "package":          {"status": "pass", "detail": "..."},
    "foundation":       {"status": "pass", "detail": "..."},
    "test_suite":       {"status": "pass"|"skipped", "detail": "..."},
    "packaging_checks": {"status": "pass", "detail": "..."}
  }
}
```

`publish-release.py` enforces **all four gates** before calling `gh release create`:
1. Report file exists at the expected path
2. `report["version"]` matches the `--version` arg
3. `report["status"] == "pass"` (the canonical gate)
4. Candidate ZIP resolved from `report["candidate"]` exists on disk

`test_suite == "skipped"` produces a **warning only** — this allows the test suite's setup_module to call `validate-release-candidate.py --skip-suite` (to avoid recursive pytest execution) and then call `publish-release.py --dry-run` without the dry-run failing. The CI workflow `release.yml` never passes `--skip-suite`, so in production the test_suite check is always `"pass"`.

### Critical Architecture Constraints

**The `release-candidates/` directory is gitignored.** The ZIP and JSON report are ephemeral — they must be freshly produced by each run of `validate-release-candidate.py`. The `release.yml` workflow always runs validation before publishing; it never assumes artifacts exist from a prior run.

**Use the exact validated artifact.** `publish-release.py` resolves the candidate ZIP path from `report["candidate"]` (e.g., `"release-candidates/godot-spacetime-v0.1.0-dev.zip"`) rather than recomputing it. This is the "exact validated candidate payload" guarantee from AC 1.

**`scripts/packaging/` is NOT in `support-baseline.json`.** Do NOT add `publish-release.py` there.

**`gh` CLI must be authenticated** in the CI environment. The workflow passes `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` as an env var to the "Publish release" step. The `permissions: contents: write` line at workflow level is required for the `GITHUB_TOKEN` to have release-creation rights.

**Do NOT add a `--no-skip-suite-enforcement` flag** or any mechanism to suppress the skipped-test-suite warning in a way that could bypass the gate in CI. The warning is intentional signal.

### Exact Script: `scripts/packaging/publish-release.py`

```python
#!/usr/bin/env python3
"""
Publish a validated GodotSpacetime SDK release candidate to GitHub Releases.

Usage:
    python3 scripts/packaging/publish-release.py [--version X.Y.Z] [--report PATH] [--dry-run]

Defaults:
    --version  Read from addons/godot_spacetime/plugin.cfg
    --report   release-candidates/validation-report-v{version}.json (relative to repo root)
    --dry-run  Flag: skip gh release create, print what would happen and exit 0

Requirements:
    - A passing validation report must exist (run validate-release-candidate.py first)
    - gh (GitHub CLI) must be installed and authenticated
    - GH_TOKEN or GITHUB_TOKEN must be set in the environment

Exit 0 on success or dry-run.
Exit 1 if the report is missing, the candidate did not pass, or gh release create fails.
"""
from __future__ import annotations

import argparse
import configparser
import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_version_from_plugin_cfg(root: Path) -> str:
    cfg_path = root / "addons/godot_spacetime/plugin.cfg"
    parser = configparser.ConfigParser()
    parser.read(str(cfg_path), encoding="utf-8")
    try:
        return parser["plugin"]["version"].strip('"')
    except KeyError as exc:
        raise SystemExit(f"Cannot read version from {cfg_path}: missing key {exc}") from exc


def main() -> None:
    root = repo_root()

    parser = argparse.ArgumentParser(
        description="Publish a validated GodotSpacetime SDK release to GitHub Releases."
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Version to publish (default: read from addons/godot_spacetime/plugin.cfg)",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Path to validation report JSON (default: release-candidates/validation-report-v{version}.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip gh release create; print what would happen and exit 0",
    )
    args = parser.parse_args()

    version = args.version or read_version_from_plugin_cfg(root)
    report_path = (
        Path(args.report)
        if args.report
        else root / "release-candidates" / f"validation-report-v{version}.json"
    )
    if not report_path.is_absolute():
        report_path = root / report_path

    # Gate 1: Report must exist
    if not report_path.exists():
        print(
            f"ERROR: Validation report not found: {report_path}\n"
            "Run validate-release-candidate.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Gate 2: Parse report
    with report_path.open(encoding="utf-8") as fh:
        report = json.load(fh)

    # Gate 3: Version match
    if report.get("version") != version:
        print(
            f"ERROR: Report version '{report.get('version')}' does not match "
            f"requested publish version '{version}'.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Gate 4: Status must be pass
    if report.get("status") != "pass":
        print(
            f"ERROR: Validation did not pass (status={report.get('status')!r}).",
            file=sys.stderr,
        )
        checks = report.get("checks", {})
        for check_name, check_data in checks.items():
            status = check_data.get("status", "unknown")
            detail = check_data.get("detail", "")
            if status not in ("pass", "skipped"):
                print(f"  [{check_name}] {status}: {detail}", file=sys.stderr)
        sys.exit(1)

    # Warn: test_suite skipped
    test_suite = report.get("checks", {}).get("test_suite", {})
    if test_suite.get("status") == "skipped":
        print(
            "WARNING: test_suite was skipped in the validation report. "
            "CI releases should not skip the test suite.",
            file=sys.stderr,
        )

    # Gate 5: Candidate ZIP must exist
    candidate_rel = report.get("candidate", "")
    candidate_path = (root / candidate_rel).resolve()
    if not candidate_path.exists():
        print(
            f"ERROR: Candidate ZIP not found: {candidate_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    tag = f"v{version}"
    title = f"GodotSpacetime SDK {tag}"
    notes = (
        f"Release {tag} of the GodotSpacetime SDK.\n\n"
        "See [docs/compatibility-matrix.md](docs/compatibility-matrix.md) for supported "
        "Godot and SpacetimeDB versions.\n\n"
        "Install instructions: [docs/install.md](docs/install.md)"
    )

    if args.dry_run:
        print(f"DRY RUN: Would create GitHub Release {tag}")
        print(f"DRY RUN: Would upload {candidate_path}")
        print("DRY RUN: Release skipped.")
        sys.exit(0)

    cmd = [
        "gh", "release", "create", tag,
        str(candidate_path),
        "--title", title,
        "--notes", notes,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(f"ERROR: Failed to run gh: {exc}", file=sys.stderr)
        sys.exit(1)

    combined = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part and part.strip()
    )
    if result.returncode == 0:
        print(f"Release {tag} published successfully.")
        if combined:
            print(combined)
    else:
        print(
            f"ERROR: gh release create failed (exit {result.returncode}):",
            file=sys.stderr,
        )
        if combined:
            print(combined, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Exact Workflow: `.github/workflows/release.yml`

```yaml
name: Publish Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to publish (leave blank to read from plugin.cfg)'
        required: false
        default: ''

permissions:
  contents: write

jobs:
  publish-release:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: 8.0.x

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Validate release candidate
        run: |
          if [ -n "${{ inputs.version }}" ]; then
            python3 scripts/packaging/validate-release-candidate.py --version "${{ inputs.version }}"
          else
            python3 scripts/packaging/validate-release-candidate.py
          fi

      - name: Publish release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          if [ -n "${{ inputs.version }}" ]; then
            python3 scripts/packaging/publish-release.py --version "${{ inputs.version }}"
          else
            python3 scripts/packaging/publish-release.py
          fi

      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: validation-report
          path: release-candidates/validation-report-*.json
          if-no-files-found: ignore
```

### Exact Test: `tests/test_story_6_4_publish_approved_sdk_releases_for_external_use.py`

```python
"""Tests for Story 6.4: Publish Approved SDK Releases for External Use."""
from __future__ import annotations

import configparser
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISH_SCRIPT = ROOT / "scripts/packaging/publish-release.py"
VALIDATE_SCRIPT = ROOT / "scripts/packaging/validate-release-candidate.py"
RELEASE_WORKFLOW = ROOT / ".github/workflows/release.yml"

_DRY_RUN_OUTPUT: str = ""


def setup_module(module):
    global _DRY_RUN_OUTPUT

    # Produce the candidate ZIP and validation report (--skip-suite avoids recursive pytest)
    validate_result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--version", "0.1.0-dev", "--skip-suite"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate_result.returncode == 0, (
        f"validate-release-candidate.py failed:\n"
        f"{validate_result.stdout}\n{validate_result.stderr}"
    )

    # Exercise the publication gate in dry-run mode (no gh CLI required)
    publish_result = subprocess.run(
        [sys.executable, str(PUBLISH_SCRIPT), "--version", "0.1.0-dev", "--dry-run"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert publish_result.returncode == 0, (
        f"publish-release.py --dry-run failed:\n"
        f"{publish_result.stdout}\n{publish_result.stderr}"
    )
    _DRY_RUN_OUTPUT = publish_result.stdout + publish_result.stderr


# --- Static existence tests ---

def test_publish_script_exists():
    assert PUBLISH_SCRIPT.exists()


def test_release_workflow_exists():
    assert RELEASE_WORKFLOW.exists()


# --- Script interface tests ---

def test_publish_script_help_exits_zero():
    result = subprocess.run(
        [sys.executable, str(PUBLISH_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


def test_publish_script_help_exposes_dry_run_flag():
    result = subprocess.run(
        [sys.executable, str(PUBLISH_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "--dry-run" in result.stdout


# --- Dry-run output tests ---

def test_dry_run_output_mentions_dry_run():
    assert "DRY RUN" in _DRY_RUN_OUTPUT


def test_dry_run_output_mentions_version():
    assert "0.1.0-dev" in _DRY_RUN_OUTPUT


# --- Report and candidate artifact tests ---

def test_validation_report_exists():
    assert (ROOT / "release-candidates" / "validation-report-v0.1.0-dev.json").exists()


def test_validation_report_status_is_pass():
    report_path = ROOT / "release-candidates" / "validation-report-v0.1.0-dev.json"
    with report_path.open(encoding="utf-8") as fh:
        report = json.load(fh)
    assert report["status"] == "pass"


def test_candidate_zip_exists():
    assert (ROOT / "release-candidates" / "godot-spacetime-v0.1.0-dev.zip").exists()


# --- Workflow content tests ---

def test_release_workflow_has_workflow_dispatch():
    assert "workflow_dispatch" in RELEASE_WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_has_publish_script():
    assert "publish-release.py" in RELEASE_WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_has_validate_script():
    assert "validate-release-candidate.py" in RELEASE_WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_has_github_token():
    assert "GITHUB_TOKEN" in RELEASE_WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_has_upload_artifact():
    assert "upload-artifact" in RELEASE_WORKFLOW.read_text(encoding="utf-8")


# --- Regression guards ---

def test_validate_release_candidate_script_exists():
    assert (ROOT / "scripts/packaging/validate-release-candidate.py").exists()


def test_package_release_script_exists():
    assert (ROOT / "scripts/packaging/package-release.py").exists()


def test_validate_foundation_script_exists():
    assert (ROOT / "scripts/compatibility/validate-foundation.py").exists()


def test_support_baseline_exists():
    assert (ROOT / "scripts/compatibility/support-baseline.json").exists()


def test_release_validation_workflow_exists():
    assert (ROOT / ".github/workflows/release-validation.yml").exists()


def test_compatibility_matrix_exists():
    assert (ROOT / "docs/compatibility-matrix.md").exists()


def test_install_docs_exist():
    assert (ROOT / "docs/install.md").exists()


def test_plugin_cfg_version_is_dev():
    cfg_path = ROOT / "addons/godot_spacetime/plugin.cfg"
    parser = configparser.ConfigParser()
    parser.read(str(cfg_path), encoding="utf-8")
    assert parser["plugin"]["version"].strip('"') == "0.1.0-dev"


def test_gitignore_excludes_release_candidates():
    gitignore = ROOT / ".gitignore"
    assert gitignore.exists()
    assert "release-candidates/" in gitignore.read_text(encoding="utf-8")
```

### Previous Story Learnings (Story 6.3)

- **`--skip-suite` pattern**: Story 6.3 established this flag for testability. Use it in story 6.4's `setup_module` to avoid recursive pytest execution. The `--dry-run` flag in `publish-release.py` plays the same role.
- **Subprocess capture pattern**: Use `capture_output=True, text=True, check=False`. Combine stdout+stderr for detail: `"\n".join(part.strip() for part in (result.stdout, result.stderr) if part and part.strip())`.
- **Version read pattern**: Identical `read_version_from_plugin_cfg()` function — copy it exactly. Do not add a new utility module; keep it self-contained in the script.
- **`repo_root()` pattern**: `Path(__file__).resolve().parents[2]` — scripts are two directories deep under repo root.
- **Report path default**: `release-candidates/validation-report-v{version}.json` relative to repo root.
- **Relative path in report**: `report["candidate"]` is a relative path string (e.g., `"release-candidates/godot-spacetime-v0.1.0-dev.zip"`). Resolve it with `repo_root() / report["candidate"]`.
- **Workflow trigger pattern**: Identical `workflow_dispatch` + optional `version` input pattern as `release-validation.yml`. Use the same shell conditional: `if [ -n "${{ inputs.version }}" ]; then ... fi`.
- **CI artifact upload**: Same `actions/upload-artifact@v4` pattern with `if: always()`.

### Project Structure Notes

- `scripts/packaging/publish-release.py` — new file; follows existing `package-release.py` and `validate-release-candidate.py` structure
- `.github/workflows/release.yml` — new file; architecture-specified target for the GitHub Releases distribution workflow (architecture.md lists it under `FR: SDK Installation & Onboarding`)
- `tests/test_story_6_4_*.py` — new file; follows story 6.3 test naming and structure
- **Nothing else changes**: no modifications to `addons/`, `docs/`, `demo/`, `spacetime/`, `scripts/compatibility/`, `scripts/codegen/`, or existing `.github/workflows/` files

### References

- Story 6.3 publication gate design: `_bmad-output/implementation-artifacts/6-3-validate-release-candidates-against-the-supported-workflow.md` (Dev Notes, "Publication gate contract" section)
- Architecture GitHub-release distribution decision: `_bmad-output/planning-artifacts/architecture.md` (Infrastructure & Deployment: "GitHub Releases first, with distributable ZIPs centered on the `addons/` plugin structure")
- Architecture workflow file mapping: `_bmad-output/planning-artifacts/architecture.md` (Requirements to Structure Mapping: `.github/workflows/release.yml` under SDK Installation & Onboarding)
- FR33 definition: `_bmad-output/planning-artifacts/prd.md` (Release, Compatibility & Maintainer Operations)
- NFR12: `_bmad-output/planning-artifacts/prd.md` ("Release packaging and published artifacts must be complete enough that supported adopters can use the SDK without maintainer intervention")

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented `scripts/packaging/publish-release.py` with publication gates for report existence, valid JSON, version match, status==pass, candidate ZIP confinement under `release-candidates/`, and candidate ZIP existence. Dry-run mode prints what would happen and exits 0 without calling `gh`.
- Created `.github/workflows/release.yml` with `workflow_dispatch` trigger, optional `version` input, `permissions: contents: write`, inline validation step before publish step, and artifact upload on `always()`.
- Created `tests/test_story_6_4_publish_approved_sdk_releases_for_external_use.py` with regression coverage for static existence, script interface, dry-run output, workflow content, publication-gate failures, release-command metadata, and cleanup behavior.
- Senior review hardened release publication by rejecting malformed JSON reports, blocking candidate-path escapes, and pinning `gh release create` to the validated `HEAD` commit with `--target`.
- Targeted story validation passes with 45 tests.

### File List

- `scripts/packaging/publish-release.py` (new)
- `.github/workflows/release.yml` (new)
- `tests/test_story_6_4_publish_approved_sdk_releases_for_external_use.py` (new)

## Change Log

- 2026-04-15: Implemented publish-release.py script, release.yml CI workflow, and story verification suite for release publication (Date: 2026-04-15)
- 2026-04-15: Senior review auto-fixed publish gate hardening gaps, corrected story metadata drift, and revalidated the story suite with 45 passing tests (Date: 2026-04-15)

## Senior Developer Review (AI)

### Outcome

Approve

### Review Notes

- Reviewed stack: Python 3 packaging scripts, GitHub Actions workflow YAML, and GitHub CLI release publishing.
- No separate story-context file or epic tech spec file was found for story 6.4; review used `_bmad-output/planning-artifacts/architecture.md`, `docs/install.md`, `docs/compatibility-matrix.md`, and the existing release-validation scripts as the governing references.
- Fixed a task-completion mismatch in Task 3.2: the story claimed `setup_module` and `teardown_module` hooks, but the test file only implemented setup. The review added backup/restore-based setup and teardown so the suite cleans up its generated artifacts.
- Hardened `scripts/packaging/publish-release.py` so malformed validation reports fail with a clear error instead of raising a raw `JSONDecodeError` traceback.
- Hardened `scripts/packaging/publish-release.py` so `report["candidate"]` must be a repo-relative ZIP under `release-candidates/`, preventing a tampered report from uploading arbitrary files outside the validated artifact directory.
- Hardened `scripts/packaging/publish-release.py` so `gh release create` uses `--target <HEAD SHA>`, which keeps the release tag pinned to the validated commit instead of falling back to the default branch tip when the tag does not already exist.
- Expanded the story verification suite to 45 passing tests, including malformed-report handling, candidate-path escape rejection, command-argument capture for `gh release create`, and artifact cleanup/restore behavior.
- Corrected the story File List and stale completion-note claims so the review record matches the implementation now on disk.

### References Captured

- Local references: `_bmad-output/planning-artifacts/architecture.md`, `docs/install.md`, `docs/compatibility-matrix.md`, `scripts/packaging/validate-release-candidate.py`
- Web fallback references: https://cli.github.com/manual/gh_release_create , https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow , https://docs.github.com/en/actions/configuring-and-managing-workflows/authenticating-with-the-github_token
