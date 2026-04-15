# Story 6.3: Validate Release Candidates Against the Supported Workflow

Status: done

## Story

As the SDK maintainer,
I want automated validation to operate on the packaged candidate,
So that only candidate artifacts that pass the supported workflow are approved for publication.

## Acceptance Criteria

1. **Given** a packaged release candidate and documented compatibility targets **When** release validation runs against the documented supported workflow **Then** it produces a concrete validation output or report covering build validation, generated-binding checks, sample smoke coverage, release-packaging checks, and compatibility-target verification for that candidate
2. **And** regressions in those flows are surfaced before the release is approved for publication
3. **And** that validation output or report is the required publication gate consumed by the release process for Story 6.4

## Tasks / Subtasks

- [x] Task 1: Create `scripts/packaging/validate-release-candidate.py` (AC: 1, 2, 3)
  - [x] 1.1 Accept `--version` (default: read from `addons/godot_spacetime/plugin.cfg` via `configparser`) and `--report` (default: `release-candidates/validation-report-v{version}.json` relative to repo root) and `--skip-suite` (flag: skip pytest run, for testability only) arguments
  - [x] 1.2 Run `package-release.py` as subprocess: `[sys.executable, str(root / "scripts/packaging/package-release.py"), "--version", version]` — capture exit code and first 500 chars of stdout/stderr as `detail`; set check `package` status to "pass" on exit 0, "fail" otherwise
  - [x] 1.3 Run `validate-foundation.py` as subprocess: `[sys.executable, str(root / "scripts/compatibility/validate-foundation.py")]` — capture exit code and first 500 chars of stdout/stderr; set check `foundation` status to "pass" on exit 0, "fail" otherwise; this single subprocess covers build validation, generated-binding checks, path checks, and compatibility-target verification
  - [x] 1.4 If `--skip-suite` is set, set check `test_suite = {"status": "skipped", "detail": "Skipped by --skip-suite flag"}`; otherwise run `[sys.executable, "-m", "pytest", "-q", "--tb=short"]` as subprocess, capture exit code and first 500 chars of combined stdout/stderr as `detail`, set status "pass" on exit 0, "fail" otherwise
  - [x] 1.5 Perform packaging checks inline using `zipfile.ZipFile`: verify `release-candidates/godot-spacetime-v{version}.zip` exists; verify it contains `addons/godot_spacetime/plugin.cfg`, `addons/godot_spacetime/GodotSpacetimePlugin.cs`, at least one `.cs` file under `addons/godot_spacetime/src/`, and at least one `thirdparty/notices` entry; verify it contains NO `.uid` files, NO `.import` files, NO entries starting with `demo/`, `tests/`, `spacetime/`, `scripts/`, `_bmad-output/`, NO `.csproj` or `.sln` files, and ALL entries are under `addons/godot_spacetime/`; set check `packaging_checks` status to "pass" if all pass, "fail" with comma-joined error list otherwise
  - [x] 1.6 Compute overall `status` as `"pass"` if all check statuses are `"pass"` or `"skipped"`, otherwise `"fail"`; write JSON report to `report_path` (create parent on demand): `{"version": ..., "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": ..., "candidate": relative path string to ZIP, "checks": {"package": {...}, "foundation": {...}, "test_suite": {...}, "packaging_checks": {...}}}`
  - [x] 1.7 Print human-readable summary to stdout (version, per-check status lines, report path); exit 0 on "pass", exit 1 on "fail"

- [x] Task 2: Create `.github/workflows/release-validation.yml` (AC: 1, 2)
  - [x] 2.1 Create workflow with name `Release Validation`, trigger `workflow_dispatch` with optional `version` input (description: "Candidate version to validate (leave blank to read from plugin.cfg)", `required: false`, `default: ''`)
  - [x] 2.2 Single job `validate-release` on `ubuntu-latest` with steps: `actions/checkout@v4`, `actions/setup-dotnet@v4` (dotnet-version: `8.0.x`), `actions/setup-python@v5` (python-version: `"3.12"`), a "Validate release candidate" step that runs `python3 scripts/packaging/validate-release-candidate.py` (with `--version "${{ inputs.version }}"` appended only when the input is non-empty)
  - [x] 2.3 Add an "Upload validation report" step using `actions/upload-artifact@v4` with `if: always()`, artifact name `validation-report`, path `release-candidates/validation-report-*.json`, and `if-no-files-found: ignore`; this lets Story 6.4 consume the report as a CI artifact

- [x] Task 3: Write `tests/test_story_6_3_validate_release_candidates_against_the_supported_workflow.py` (AC: 1, 2, 3)
  - [x] 3.1 Static existence tests: `scripts/packaging/validate-release-candidate.py` exists; `.github/workflows/release-validation.yml` exists
  - [x] 3.2 Add `setup_module` / `teardown_module` hooks: run `validate-release-candidate.py --version 0.1.0-dev --report {tmpdir}/report.json --skip-suite` as subprocess from repo root; assert exit code 0; assert report file exists; read and parse JSON into `_REPORT` module global
  - [x] 3.3 Report structure tests: report JSON parses; has top-level keys `version`, `status`, `candidate`, `checks`, `timestamp`
  - [x] 3.4 Report value tests: `report["version"] == "0.1.0-dev"`; `report["status"] == "pass"`; `report["candidate"]` contains `"godot-spacetime-v0.1.0-dev.zip"`; the candidate ZIP path exists as a file; `report["timestamp"]` contains `"T"` (ISO 8601 datetime separator)
  - [x] 3.5 Checks completeness tests: `report["checks"]` contains all four keys: `"package"`, `"foundation"`, `"test_suite"`, `"packaging_checks"`
  - [x] 3.6 Check structure tests: each of the four checks has both `"status"` and `"detail"` keys; `detail` is a non-empty string for each
  - [x] 3.7 Check status tests: `package` check status is `"pass"`; `foundation` check status is `"pass"`; `test_suite` check status is `"skipped"` (because `--skip-suite` was used in setup); `packaging_checks` check status is `"pass"`
  - [x] 3.8 Workflow content tests: `release-validation.yml` contains `workflow_dispatch`; contains `validate-release-candidate.py`; contains `upload-artifact`; contains `dotnet-version`
  - [x] 3.9 Publication gate tests: `report["status"] == "pass"` (the gate value Story 6.4 reads); the report file path ends in `.json` (machine-readable format)
  - [x] 3.10 Script help test: run `validate-release-candidate.py --help` as subprocess; assert exit code 0; assert `"--skip-suite"` in stdout (confirms the flag exists for testability)
  - [x] 3.11 Regression guards: `scripts/packaging/package-release.py` exists (Story 6.2); `scripts/compatibility/validate-foundation.py` exists; `scripts/compatibility/support-baseline.json` exists; `.github/workflows/validate-foundation.yml` exists; `addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt` exists; `docs/compatibility-matrix.md` exists; `docs/install.md` exists; `plugin.cfg` version is `0.1.0-dev`; `.gitignore` contains `release-candidates/`; `docs/compatibility-matrix.md` contains `4.6.2`; `docs/compatibility-matrix.md` contains `SpacetimeDB.ClientSDK`; `docs/runtime-boundaries.md` contains `internal sealed`; `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs` does NOT contain `AuthRequired`; `addons/godot_spacetime/src/Public/SpacetimeClient.cs` exists; `demo/README.md` exists

## Dev Notes

### What This Story Delivers

Story 6.3 creates the release validation infrastructure that gates the Story 6.4 publication step. The validation orchestration script calls `package-release.py` (from Story 6.2) and `validate-foundation.py` (from Story 1.8) as subprocesses, runs the `pytest` suite, and performs inline ZIP structural checks — then writes a machine-readable JSON report that Story 6.4 will read before publishing.

**Primary deliverables:**
- `scripts/packaging/validate-release-candidate.py` — standalone Python 3 orchestration script that produces a JSON validation report covering all five required check areas
- `.github/workflows/release-validation.yml` — on-demand CI workflow that runs the validation script and uploads the report as a CI artifact

**Secondary deliverable:**
- `tests/test_story_6_3_*.py` — verification suite covering script existence, report structure, check statuses, workflow content, and regression guards

**No C# changes.** No modifications to any existing file in `addons/`, `docs/`, `demo/`, `tests/`, or `scripts/compatibility/`. Do NOT modify `support-baseline.json`.

### How the Five AC Coverage Areas Map to Checks

| AC Coverage Area | Check Name | Implementation |
|---|---|---|
| Build validation | `foundation` | `validate-foundation.py` runs `dotnet restore` + `dotnet build` |
| Generated-binding checks | `foundation` | `validate-foundation.py` checks CLI version + staleness |
| Sample smoke coverage | `test_suite` | `pytest -q --tb=short` runs the full 2015-test suite |
| Release-packaging checks | `packaging_checks` | Inline `zipfile` inspection in the validation script |
| Compatibility-target verification | `foundation` | `validate-foundation.py` checks `support-baseline.json` line/version pinning |

Note: `validate-foundation.py` covers four of the five areas in a single subprocess call. Do NOT re-implement what `validate-foundation.py` already does.

### Critical Architecture Constraints

**Do NOT modify these files (regression test guard):**
- `scripts/compatibility/validate-foundation.py`
- `scripts/compatibility/support-baseline.json`
- `scripts/packaging/package-release.py`
- `.github/workflows/validate-foundation.yml`
- Any file under `addons/`, `docs/`, `demo/`, existing `tests/`

**`scripts/packaging/` is NOT in `support-baseline.json`** — do not add `validate-release-candidate.py` there. Story 6.3 does not extend the foundation baseline.

**`release-candidates/` is gitignored** — the output ZIP and JSON report are never committed. Both are produced fresh by the validation script.

**`--skip-suite` flag is for testability only** — the CI workflow NEVER passes `--skip-suite`. The flag exists so the story 6.3 test suite can call the validation script without causing recursive `pytest` calls.

**Publication gate contract**: Story 6.4 will read `release-candidates/validation-report-v{version}.json` and verify `report["status"] == "pass"`. Design the report format so this check is straightforward.

**`test_suite` skipped vs. failed**: When `--skip-suite` is used, `test_suite` gets `{"status": "skipped", ...}` and the overall status is still `"pass"`. Story 6.4 may optionally enforce that `test_suite` is not "skipped" before publishing; that is Story 6.4's concern.

### Exact Script: `scripts/packaging/validate-release-candidate.py`

```python
#!/usr/bin/env python3
"""
Validate a GodotSpacetime SDK release candidate against the supported workflow.

Usage:
    python3 scripts/packaging/validate-release-candidate.py [--version X.Y.Z] [--report PATH] [--skip-suite]

Defaults:
    --version      Read from addons/godot_spacetime/plugin.cfg
    --report       release-candidates/validation-report-v{version}.json (relative to repo root)
    --skip-suite   Flag: skip pytest suite run (use only for testing this script itself)

Checks performed and written to the JSON report:
    package          - Run scripts/packaging/package-release.py to produce the candidate ZIP
    foundation       - Run scripts/compatibility/validate-foundation.py (build + bindings + paths + compat targets)
    test_suite       - Run pytest -q --tb=short (sample smoke coverage; skipped with --skip-suite)
    packaging_checks - Verify candidate ZIP structure inline (inclusions, exclusions)

Exit 0 if overall status is "pass" (all checks pass or are skipped).
Exit 1 if any check fails.
"""
from __future__ import annotations

import argparse
import configparser
import datetime
import json
import subprocess
import sys
import zipfile
from pathlib import Path

PACKAGE_SCRIPT = Path("scripts/packaging/package-release.py")
FOUNDATION_SCRIPT = Path("scripts/compatibility/validate-foundation.py")
CANDIDATE_DIR = Path("release-candidates")
REPORT_PREFIX = "validation-report-v"

REQUIRED_ZIP_ENTRIES = [
    "addons/godot_spacetime/plugin.cfg",
    "addons/godot_spacetime/GodotSpacetimePlugin.cs",
]
EXCLUDED_EXTENSIONS = {".uid", ".import"}
EXCLUDED_PREFIXES = ["demo/", "tests/", "spacetime/", "scripts/", "_bmad-output/"]
EXCLUDED_SUFFIXES = [".csproj", ".sln"]
REQUIRED_ZIP_PREFIX = "addons/godot_spacetime/"


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


def run_subprocess(cmd: list[str], cwd: Path) -> dict[str, str]:
    """Run a subprocess and return {"status": "pass"|"fail", "detail": str}."""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {"status": "fail", "detail": f"failed to start: {exc}"}

    combined = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part and part.strip()
    )
    detail = combined[:500] if combined else "OK"

    if result.returncode == 0:
        return {"status": "pass", "detail": detail}
    return {"status": "fail", "detail": f"exit {result.returncode}: {detail}"}


def check_packaging_inline(candidate_path: Path) -> dict[str, str]:
    """Verify the candidate ZIP structure without re-running package-release.py."""
    if not candidate_path.exists():
        return {"status": "fail", "detail": f"Candidate ZIP not found: {candidate_path}"}

    try:
        with zipfile.ZipFile(candidate_path) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile as exc:
        return {"status": "fail", "detail": f"ZIP integrity error: {exc}"}

    errors: list[str] = []

    for required in REQUIRED_ZIP_ENTRIES:
        if required not in names:
            errors.append(f"missing required entry: {required}")

    src_files = [n for n in names if n.startswith("addons/godot_spacetime/src/") and n.endswith(".cs")]
    if not src_files:
        errors.append("no .cs files found under addons/godot_spacetime/src/")

    notices = [n for n in names if "thirdparty/notices" in n]
    if not notices:
        errors.append("no thirdparty/notices entries found")

    for name in names:
        if any(name.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            errors.append(f"excluded extension: {name}")
        if any(name.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            errors.append(f"excluded prefix: {name}")
        if any(name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
            errors.append(f"excluded suffix: {name}")
        if not name.startswith(REQUIRED_ZIP_PREFIX):
            errors.append(f"outside addon prefix: {name}")

    if errors:
        return {"status": "fail", "detail": "; ".join(errors[:10])}

    return {
        "status": "pass",
        "detail": (
            f"ZIP structure OK: {len(names)} entries, "
            f"{len(src_files)} src files, {len(notices)} notices, "
            "no exclusions violated"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate GodotSpacetime SDK release candidate against the supported workflow"
    )
    parser.add_argument("--version", help="Version string (default: read from plugin.cfg)")
    parser.add_argument(
        "--report",
        help="Output JSON report path (default: release-candidates/validation-report-v{version}.json)",
    )
    parser.add_argument(
        "--skip-suite",
        action="store_true",
        help="Skip pytest suite run (for testing this script only; never use in CI)",
    )
    args = parser.parse_args()

    root = repo_root()
    version = args.version or read_version_from_plugin_cfg(root)
    candidate_path = root / CANDIDATE_DIR / f"godot-spacetime-v{version}.zip"

    if args.report:
        report_path = Path(args.report)
        if not report_path.is_absolute():
            report_path = Path.cwd() / report_path
    else:
        report_path = root / CANDIDATE_DIR / f"{REPORT_PREFIX}{version}.json"

    checks: dict[str, dict[str, str]] = {}

    # 1. Package the release candidate
    print(f"[1/4] Packaging release candidate v{version}...")
    checks["package"] = run_subprocess(
        [sys.executable, str(root / PACKAGE_SCRIPT), "--version", version],
        cwd=root,
    )

    # 2. Foundation validation (build + bindings + paths + compatibility targets)
    print("[2/4] Running foundation validation...")
    checks["foundation"] = run_subprocess(
        [sys.executable, str(root / FOUNDATION_SCRIPT)],
        cwd=root,
    )

    # 3. Test suite (sample smoke coverage)
    if args.skip_suite:
        print("[3/4] Skipping test suite (--skip-suite flag)")
        checks["test_suite"] = {"status": "skipped", "detail": "Skipped by --skip-suite flag"}
    else:
        print("[3/4] Running test suite (sample smoke coverage)...")
        checks["test_suite"] = run_subprocess(
            [sys.executable, "-m", "pytest", "-q", "--tb=short"],
            cwd=root,
        )

    # 4. Packaging structure checks
    print("[4/4] Checking candidate ZIP structure...")
    checks["packaging_checks"] = check_packaging_inline(candidate_path)

    # Overall status
    overall = (
        "pass"
        if all(c["status"] in ("pass", "skipped") for c in checks.values())
        else "fail"
    )

    # Candidate path as relative string for portability
    try:
        candidate_rel = str(candidate_path.relative_to(root))
    except ValueError:
        candidate_rel = str(candidate_path)

    report: dict = {
        "version": version,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": overall,
        "candidate": candidate_rel,
        "checks": checks,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Print human-readable summary
    print()
    print(f"Release candidate validation — v{version}")
    print(f"Overall status: {overall.upper()}")
    for name, result in checks.items():
        symbol = "✓" if result["status"] == "pass" else ("~" if result["status"] == "skipped" else "✗")
        detail_preview = result["detail"][:80].replace("\n", " ")
        print(f"  {symbol} {name}: {result['status']} — {detail_preview}")
    print(f"Report written: {report_path}")

    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

### Exact Workflow: `.github/workflows/release-validation.yml`

```yaml
name: Release Validation

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Candidate version to validate (leave blank to read from plugin.cfg)'
        required: false
        default: ''

jobs:
  validate-release:
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

      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: validation-report
          path: release-candidates/validation-report-*.json
          if-no-files-found: ignore
```

### Project Structure After Story 6.3

```
scripts/
├── codegen/
│   └── generate-smoke-test.sh              ← unchanged
├── compatibility/
│   ├── validate-foundation.py              ← unchanged (do NOT modify)
│   └── support-baseline.json              ← unchanged (do NOT modify)
└── packaging/
    ├── package-release.py                 ← unchanged (Story 6.2)
    └── validate-release-candidate.py      ← NEW

.github/
└── workflows/
    ├── validate-foundation.yml            ← unchanged (do NOT modify)
    └── release-validation.yml             ← NEW

release-candidates/                        ← gitignored; created on demand
    godot-spacetime-v0.1.0-dev.zip        ← produced by validation run; gitignored
    validation-report-v0.1.0-dev.json     ← produced by validation run; gitignored
```

**Files NOT to touch (modification breaks prior story regression tests):**
- All files under `docs/`
- All files under `addons/godot_spacetime/src/`
- All files under `demo/`
- All existing test files under `tests/`
- `scripts/compatibility/validate-foundation.py`
- `scripts/compatibility/support-baseline.json`
- `scripts/packaging/package-release.py`
- `.github/workflows/validate-foundation.yml`
- `.gitignore` (already has `release-candidates/`)

### Testing Approach

Test file: `tests/test_story_6_3_validate_release_candidates_against_the_supported_workflow.py`

**Full test file structure:**

```python
"""
Tests for Story 6.3: Validate Release Candidates Against the Supported Workflow

Validates:
- scripts/packaging/validate-release-candidate.py exists and produces correct JSON report (AC 1, 2)
- .github/workflows/release-validation.yml exists with correct structure (AC 1, 2)
- Validation report is the required publication gate for Story 6.4 (AC 3)
- All prior story deliverables remain intact (regression guards)
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = ROOT / "scripts/packaging/validate-release-candidate.py"
WORKFLOW_FILE = ROOT / ".github/workflows/release-validation.yml"

_TEMP_DIR: str | None = None
_REPORT: dict | None = None


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def setup_module(module: object) -> None:
    global _TEMP_DIR, _REPORT
    _TEMP_DIR = tempfile.mkdtemp(prefix="story_6_3_")
    report_path = str(Path(_TEMP_DIR) / "report.json")
    result = subprocess.run(
        [
            sys.executable, str(VALIDATE_SCRIPT),
            "--version", "0.1.0-dev",
            "--report", report_path,
            "--skip-suite",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"validate-release-candidate.py failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    report_file = Path(report_path)
    assert report_file.exists(), "validation script did not create report file"
    _REPORT = json.loads(report_file.read_text(encoding="utf-8"))


def teardown_module(module: object) -> None:
    if _TEMP_DIR:
        shutil.rmtree(_TEMP_DIR, ignore_errors=True)


# ---------------------------------------------------------------------------
# 3.1 Static existence tests
# ---------------------------------------------------------------------------

def test_validate_release_candidate_script_exists() -> None:
    assert VALIDATE_SCRIPT.exists(), \
        "scripts/packaging/validate-release-candidate.py must exist (AC 1)"


def test_release_validation_workflow_exists() -> None:
    assert WORKFLOW_FILE.exists(), \
        ".github/workflows/release-validation.yml must exist (AC 1)"


# ---------------------------------------------------------------------------
# 3.3 Report structure tests
# ---------------------------------------------------------------------------

def test_report_is_valid_json() -> None:
    assert _REPORT is not None, "Report must parse as valid JSON"


def test_report_has_version_key() -> None:
    assert "version" in _REPORT, "Report must have 'version' key (AC 1)"


def test_report_has_status_key() -> None:
    assert "status" in _REPORT, "Report must have 'status' key (AC 3)"


def test_report_has_candidate_key() -> None:
    assert "candidate" in _REPORT, "Report must have 'candidate' key (AC 1)"


def test_report_has_checks_key() -> None:
    assert "checks" in _REPORT, "Report must have 'checks' key (AC 1)"


def test_report_has_timestamp_key() -> None:
    assert "timestamp" in _REPORT, "Report must have 'timestamp' key (AC 1)"


# ---------------------------------------------------------------------------
# 3.4 Report value tests
# ---------------------------------------------------------------------------

def test_report_version_matches_input() -> None:
    assert _REPORT["version"] == "0.1.0-dev", \
        "Report version must match --version input (AC 1)"


def test_report_status_is_pass() -> None:
    assert _REPORT["status"] == "pass", \
        f"Report status must be 'pass'; got '{_REPORT['status']}' (AC 1, 2)"


def test_report_candidate_contains_version() -> None:
    assert "godot-spacetime-v0.1.0-dev.zip" in _REPORT["candidate"], \
        "Report candidate path must contain the versioned ZIP name (AC 1)"


def test_report_candidate_zip_exists() -> None:
    candidate_path = ROOT / _REPORT["candidate"]
    assert candidate_path.exists(), \
        f"Report candidate ZIP must exist at {candidate_path} (AC 1)"


def test_report_timestamp_is_iso_format() -> None:
    assert "T" in _REPORT["timestamp"], \
        "Report timestamp must be ISO 8601 format containing 'T' separator (AC 1)"


# ---------------------------------------------------------------------------
# 3.5 Checks completeness tests
# ---------------------------------------------------------------------------

def test_checks_has_package_key() -> None:
    assert "package" in _REPORT["checks"], \
        "checks must contain 'package' key (AC 1)"


def test_checks_has_foundation_key() -> None:
    assert "foundation" in _REPORT["checks"], \
        "checks must contain 'foundation' key — covers build + bindings + compat-targets (AC 1)"


def test_checks_has_test_suite_key() -> None:
    assert "test_suite" in _REPORT["checks"], \
        "checks must contain 'test_suite' key (AC 1)"


def test_checks_has_packaging_checks_key() -> None:
    assert "packaging_checks" in _REPORT["checks"], \
        "checks must contain 'packaging_checks' key (AC 1)"


# ---------------------------------------------------------------------------
# 3.6 Check structure tests
# ---------------------------------------------------------------------------

def test_package_check_has_status_and_detail() -> None:
    check = _REPORT["checks"]["package"]
    assert "status" in check and "detail" in check, \
        "package check must have 'status' and 'detail' keys"
    assert isinstance(check["detail"], str) and check["detail"], \
        "package check detail must be a non-empty string"


def test_foundation_check_has_status_and_detail() -> None:
    check = _REPORT["checks"]["foundation"]
    assert "status" in check and "detail" in check, \
        "foundation check must have 'status' and 'detail' keys"
    assert isinstance(check["detail"], str) and check["detail"], \
        "foundation check detail must be a non-empty string"


def test_test_suite_check_has_status_and_detail() -> None:
    check = _REPORT["checks"]["test_suite"]
    assert "status" in check and "detail" in check, \
        "test_suite check must have 'status' and 'detail' keys"
    assert isinstance(check["detail"], str) and check["detail"], \
        "test_suite check detail must be a non-empty string"


def test_packaging_checks_has_status_and_detail() -> None:
    check = _REPORT["checks"]["packaging_checks"]
    assert "status" in check and "detail" in check, \
        "packaging_checks check must have 'status' and 'detail' keys"
    assert isinstance(check["detail"], str) and check["detail"], \
        "packaging_checks check detail must be a non-empty string"


# ---------------------------------------------------------------------------
# 3.7 Check status tests
# ---------------------------------------------------------------------------

def test_package_check_passes() -> None:
    assert _REPORT["checks"]["package"]["status"] == "pass", \
        f"package check must pass; got '{_REPORT['checks']['package']['status']}' " \
        f"detail: {_REPORT['checks']['package']['detail']}"


def test_foundation_check_passes() -> None:
    assert _REPORT["checks"]["foundation"]["status"] == "pass", \
        f"foundation check must pass; got '{_REPORT['checks']['foundation']['status']}' " \
        f"detail: {_REPORT['checks']['foundation']['detail']}"


def test_test_suite_check_skipped_with_skip_suite_flag() -> None:
    assert _REPORT["checks"]["test_suite"]["status"] == "skipped", \
        "test_suite check must be 'skipped' when --skip-suite is used (AC 1)"
    assert "--skip-suite" in _REPORT["checks"]["test_suite"]["detail"], \
        "test_suite skipped detail must reference --skip-suite flag"


def test_packaging_checks_passes() -> None:
    assert _REPORT["checks"]["packaging_checks"]["status"] == "pass", \
        f"packaging_checks must pass; got '{_REPORT['checks']['packaging_checks']['status']}' " \
        f"detail: {_REPORT['checks']['packaging_checks']['detail']}"


def test_packaging_checks_detail_mentions_entries() -> None:
    detail = _REPORT["checks"]["packaging_checks"]["detail"]
    assert "entries" in detail, \
        "packaging_checks detail must mention entry count (AC 1)"


# ---------------------------------------------------------------------------
# 3.8 Workflow content tests
# ---------------------------------------------------------------------------

def test_workflow_has_workflow_dispatch_trigger() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "workflow_dispatch" in content, \
        "release-validation.yml must have workflow_dispatch trigger (AC 1)"


def test_workflow_references_validation_script() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "validate-release-candidate.py" in content, \
        "release-validation.yml must reference validate-release-candidate.py (AC 1)"


def test_workflow_uploads_artifact() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "upload-artifact" in content, \
        "release-validation.yml must upload validation report as artifact (AC 3)"


def test_workflow_sets_up_dotnet() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "dotnet-version" in content, \
        "release-validation.yml must set up .NET (required for foundation validation)"


def test_workflow_uses_python_312() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "3.12" in content, \
        "release-validation.yml must specify Python 3.12 to match validate-foundation.yml"


# ---------------------------------------------------------------------------
# 3.9 Publication gate tests (AC 3)
# ---------------------------------------------------------------------------

def test_report_status_pass_is_the_publication_gate() -> None:
    """Report status 'pass' is the machine-readable gate consumed by Story 6.4."""
    assert _REPORT["status"] == "pass", \
        "Publication gate: report status must be 'pass' before Story 6.4 can publish (AC 3)"


def test_report_is_json_file() -> None:
    """Report is machine-readable JSON, not just stdout."""
    assert VALIDATE_SCRIPT.exists()
    # Verify the script writes a .json report (checked via setup_module)
    assert isinstance(_REPORT, dict), \
        "Report must be a JSON dict for Story 6.4 machine consumption (AC 3)"


# ---------------------------------------------------------------------------
# 3.10 Script interface test
# ---------------------------------------------------------------------------

def test_script_help_mentions_skip_suite() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "--help must exit 0"
    assert "--skip-suite" in result.stdout, \
        "--help output must mention --skip-suite flag (testability contract)"


# ---------------------------------------------------------------------------
# 3.11 Regression guards — prior story deliverables
# ---------------------------------------------------------------------------

def test_regression_package_release_script_exists() -> None:
    assert (ROOT / "scripts/packaging/package-release.py").exists(), \
        "scripts/packaging/package-release.py must still exist (Story 6.2)"


def test_regression_validate_foundation_script_exists() -> None:
    assert (ROOT / "scripts/compatibility/validate-foundation.py").exists(), \
        "scripts/compatibility/validate-foundation.py must still exist (Story 1.8)"


def test_regression_support_baseline_json_exists() -> None:
    assert (ROOT / "scripts/compatibility/support-baseline.json").exists(), \
        "scripts/compatibility/support-baseline.json must still exist (Story 1.8)"


def test_regression_validate_foundation_yml_exists() -> None:
    assert (ROOT / ".github/workflows/validate-foundation.yml").exists(), \
        ".github/workflows/validate-foundation.yml must still exist (Story 1.8)"


def test_regression_thirdparty_notices_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/thirdparty/notices").is_dir(), \
        "addons/godot_spacetime/thirdparty/notices/ must still exist (Story 6.2)"


def test_regression_spacetimedb_notice_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt").exists(), \
        "spacetimedb-client-sdk.txt must still exist (Story 6.2)"


def test_regression_docs_compatibility_matrix_exists() -> None:
    assert (ROOT / "docs/compatibility-matrix.md").exists(), \
        "docs/compatibility-matrix.md must still exist (Story 6.1)"


def test_regression_docs_install_exists() -> None:
    assert (ROOT / "docs/install.md").exists(), "docs/install.md must exist (Story 5.4)"


def test_regression_docs_quickstart_exists() -> None:
    assert (ROOT / "docs/quickstart.md").exists(), "docs/quickstart.md must exist (Story 5.4)"


def test_regression_plugin_cfg_version_intact() -> None:
    content = _read("addons/godot_spacetime/plugin.cfg")
    assert "0.1.0-dev" in content, "plugin.cfg version must still be 0.1.0-dev"


def test_regression_gitignore_includes_release_candidates() -> None:
    assert "release-candidates/" in _read(".gitignore"), \
        ".gitignore must contain 'release-candidates/' (Story 6.2)"


def test_regression_compatibility_matrix_version_intact() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "4.6.2" in content, "compatibility-matrix.md version baseline 4.6.2 must be intact (Story 6.1)"
    assert "SpacetimeDB.ClientSDK" in content, \
        "compatibility-matrix.md SpacetimeDB.ClientSDK entry must be intact (Story 6.1)"


def test_regression_runtime_boundaries_has_internal_sealed() -> None:
    assert "internal sealed" in _read("docs/runtime-boundaries.md"), \
        "docs/runtime-boundaries.md must contain 'internal sealed' (Story 6.1)"


def test_regression_auth_required_not_in_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "AuthRequired" not in content, \
        "ConnectionAuthState.cs must not contain AuthRequired (removed in Story 6.1)"


def test_regression_spacetime_client_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Public/SpacetimeClient.cs").exists(), \
        "SpacetimeClient.cs must still exist"


def test_regression_demo_readme_exists() -> None:
    assert (ROOT / "demo/README.md").exists(), "demo/README.md must exist (Story 5.3)"
```

**Test count target: ~45 tests.** The structure above maps 1:1 to test functions.

### Validation Commands

```bash
# Run story-specific tests (uses --skip-suite internally via setup_module)
pytest -q tests/test_story_6_3_validate_release_candidates_against_the_supported_workflow.py

# Run full validation manually (no --skip-suite; runs pytest internally — takes longer)
python3 scripts/packaging/validate-release-candidate.py --version 0.1.0-dev

# Verify report was written
cat release-candidates/validation-report-v0.1.0-dev.json | python3 -m json.tool

# Quick check: story gate value
python3 -c "import json; r=json.load(open('release-candidates/validation-report-v0.1.0-dev.json')); print(r['status'])"

# Full regression suite (must still be 2015+ tests)
pytest -q
```

Expected: story test file passes (~45 tests); `pytest -q` passes with 2055+ tests (2015 baseline + ~40 new); no regressions.

### Git Intelligence

- Commit pattern: `feat(story-6.3): Validate Release Candidates Against the Supported Workflow`
- No `dotnet build` required (no C# changes in this story)
- No modifications to existing test files
- Current test baseline: **2015 passing** (from Story 6.2 Dev Agent Record)
- Scripts in this project use Python for complex tooling and shell for simple invocations; `validate-release-candidate.py` follows the Python pattern established by `validate-foundation.py` and `package-release.py`
- The script uses only Python stdlib (`argparse`, `configparser`, `datetime`, `json`, `subprocess`, `sys`, `zipfile`, `pathlib`) — no external dependencies

### Story 6.4 Integration Note

Story 6.4 (Publish Approved SDK Releases) will:
1. Read `release-candidates/validation-report-v{version}.json`
2. Assert `report["status"] == "pass"` as the publication gate (AC 3)
3. Use `report["candidate"]` as the path to the validated ZIP to publish

This means:
- The report path convention `release-candidates/validation-report-v{version}.json` must be stable
- The `status` and `candidate` keys must be present in the report (verified by story 6.3 tests)
- Story 6.4 should ideally also assert that `report["checks"]["test_suite"]["status"] != "skipped"` to prevent publishing from a `--skip-suite` run

### References

- Story AC source: `_bmad-output/planning-artifacts/epics.md` § Epic 6, Story 6.3
- FR35: Maintainers can validate the core supported workflow against the documented version matrix before release
- FR36: Maintainers can use sample-backed validation to detect regressions in critical SDK flows
- NFR19: The core supported workflow must be validated before release against the documented compatibility targets [Source: `_bmad-output/planning-artifacts/epics.md` § NFR19]
- CI/CD architecture: GitHub Actions for build validation, sample smoke tests, generated-binding checks, and compatibility-matrix verification [Source: `_bmad-output/planning-artifacts/architecture.md` § Core Architectural Decisions]
- Release, Compatibility & Maintainer Operations ownership: `scripts/packaging/`, `.github/workflows/`, `docs/release-process.md` [Source: `_bmad-output/planning-artifacts/architecture.md` § Requirements to Structure Mapping]
- `validate-foundation.py` covers: `dotnet restore`, `dotnet build`, path checks, line/version checks, binding compatibility — do not re-implement [Source: `scripts/compatibility/validate-foundation.py`]
- `package-release.py` produces `release-candidates/godot-spacetime-v{version}.zip` with `addons/godot_spacetime/` content only [Source: `_bmad-output/implementation-artifacts/6-2-package-reproducible-versioned-release-candidates.md`]
- `release-candidates/` is gitignored [Source: `.gitignore` — added in Story 6.2]
- `--skip-suite` flag is required for testability to avoid recursive pytest calls when the story's own test suite calls the validation script [Source: this story design decision]
- `support-baseline.json` must not be modified [Source: Story 6.2 Dev Notes — `scripts/packaging/` is NOT in the baseline]
- Current test baseline: 2015 passing [Source: Story 6.2 Dev Agent Record]
- `ZipInfo.create_system = 3` is set by `package-release.py` for cross-platform stability [Source: Story 6.2 Senior Developer Review]
- Previous story: `_bmad-output/implementation-artifacts/6-2-package-reproducible-versioned-release-candidates.md`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Created `scripts/packaging/validate-release-candidate.py`: orchestrates package-release.py, validate-foundation.py, pytest suite (skippable via --skip-suite), and inline ZIP structural checks; writes machine-readable JSON report to `release-candidates/validation-report-v{version}.json`; exits 0 on pass, 1 on fail
- Created `.github/workflows/release-validation.yml`: on-demand workflow_dispatch CI workflow with optional version input; runs validation script and uploads JSON report as artifact; .NET 8.0.x + Python 3.12 toolchain matches validate-foundation.yml
- Created `tests/test_story_6_3_validate_release_candidates_against_the_supported_workflow.py`: review-hardened to 88 tests covering script existence, report structure, check statuses, workflow content, publication gate contract, exact packaging constraints, stale-candidate failure handling, `--help` interface, and regression guards for all prior story deliverables
- Full regression suite: 2103 passed; zero regressions
- Senior Developer Review (AI) auto-fixed stale-candidate validation behavior, tightened `thirdparty/notices/` ZIP verification, reran validation, and synced story/sprint tracking to `done`
- No C# changes; review fixes were confined to Python, test, and story-tracking artifacts

### File List

- scripts/packaging/validate-release-candidate.py (new, review-hardened: stale candidate cleanup + exact `thirdparty/notices/` prefix enforcement)
- .github/workflows/release-validation.yml (new)
- tests/test_story_6_3_validate_release_candidates_against_the_supported_workflow.py (new, review-hardened to 88 tests)
- _bmad-output/implementation-artifacts/6-3-validate-release-candidates-against-the-supported-workflow.md (story file updates: review notes, metadata, status)
- _bmad-output/implementation-artifacts/sprint-status.yaml (status update: `6-3-validate-release-candidates-against-the-supported-workflow` -> `done`)

### Senior Developer Review (AI)

- Reviewer: Pinkyd on 2026-04-15
- Outcome: Approve
- Story Context: No separate story-context artifact was found; review used the story file, `_bmad-output/planning-artifacts/architecture.md`, and the changed implementation/test files.
- Epic Tech Spec: No separate epic tech spec artifact was found; `_bmad-output/planning-artifacts/architecture.md` provided the standards and architecture context.
- Tech Stack Reviewed: Python 3 release-validation tooling, GitHub Actions workflow YAML, `pytest` contract/unit tests, Git-tracked story automation artifacts.
- External References: No MCP/web lookup used; repository primary sources were sufficient for this review scope and network access is restricted in this environment.
- Git vs Story Discrepancies: 2 additional non-source automation artifacts were present under `_bmad-output/` during review (`_bmad-output/implementation-artifacts/tests/test-summary-6-3.md`, `_bmad-output/story-automator/orchestration-1-20260414-184146.md`).
- Findings fixed:
  - HIGH: `scripts/packaging/validate-release-candidate.py` could reuse a stale `release-candidates/godot-spacetime-v{version}.zip` when the packaging subprocess failed, so `packaging_checks` could report against an older artifact instead of the current validation run. Fixed by removing any existing candidate before packaging and failing `packaging_checks` whenever the package step fails.
  - MEDIUM: `scripts/packaging/validate-release-candidate.py` treated any ZIP entry containing `thirdparty/notices` as sufficient, so a malformed path like `addons/godot_spacetime/src/thirdparty/notices_fake.txt` could satisfy Task 1.5 without a real notices payload. Fixed by requiring the exact `addons/godot_spacetime/thirdparty/notices/` prefix.
  - MEDIUM: `tests/test_story_6_3_validate_release_candidates_against_the_supported_workflow.py` did not cover stale-candidate package failures or the exact notices-prefix contract, so both regressions could slip through review. Fixed by expanding the story suite to 88 tests with direct unit coverage for both cases.
  - MEDIUM: The story artifact still reported the pre-review 50-test / 2065-pass counts, had no `Senior Developer Review (AI)` section, and sprint tracking still showed `review`. Fixed by rerunning validation, updating the story record, and syncing the story/sprint status to `done`.
- Validation:
  - `pytest -q tests/test_story_6_3_validate_release_candidates_against_the_supported_workflow.py`
  - `pytest -q`
- Notes:
  - No CRITICAL issues remain after fixes.

## Change Log

- 2026-04-15: Story 6.3 implemented — created validate-release-candidate.py orchestration script, release-validation.yml CI workflow, and the validation test suite (Date: 2026-04-15)
- 2026-04-15: Senior Developer Review (AI) — fixed stale-candidate validation behavior, tightened `thirdparty/notices/` ZIP validation, expanded Story 6.3 coverage to 88 tests, reran validation (`88` story tests, `2103` full-suite tests), and marked the story done.
