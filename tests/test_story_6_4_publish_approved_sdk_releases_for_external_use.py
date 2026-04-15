"""Tests for Story 6.4: Publish Approved SDK Releases for External Use."""
from __future__ import annotations

import configparser
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISH_SCRIPT = ROOT / "scripts/packaging/publish-release.py"
VALIDATE_SCRIPT = ROOT / "scripts/packaging/validate-release-candidate.py"
RELEASE_WORKFLOW = ROOT / ".github/workflows/release.yml"
TEST_VERSION = "0.1.0-dev"
RELEASE_CANDIDATES_DIR = ROOT / "release-candidates"
VALIDATION_REPORT = RELEASE_CANDIDATES_DIR / f"validation-report-v{TEST_VERSION}.json"
CANDIDATE_ZIP = RELEASE_CANDIDATES_DIR / f"godot-spacetime-v{TEST_VERSION}.zip"

_DRY_RUN_OUTPUT: str = ""
_BACKUP_DIR: Path | None = None


def _backup_targets() -> None:
    global _BACKUP_DIR

    _BACKUP_DIR = Path(tempfile.mkdtemp(prefix="story-6-4-release-artifacts-"))
    for path in (VALIDATION_REPORT, CANDIDATE_ZIP):
        if path.exists():
            shutil.copy2(path, _BACKUP_DIR / path.name)


def _restore_targets() -> None:
    global _BACKUP_DIR

    if _BACKUP_DIR is None:
        return

    for path in (VALIDATION_REPORT, CANDIDATE_ZIP):
        if path.exists():
            path.unlink()

        backup_path = _BACKUP_DIR / path.name
        if backup_path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, path)

    shutil.rmtree(_BACKUP_DIR, ignore_errors=True)
    _BACKUP_DIR = None


def setup_module(module):
    global _DRY_RUN_OUTPUT
    _backup_targets()

    # Produce the candidate ZIP and validation report (--skip-suite avoids recursive pytest)
    validate_result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--version", TEST_VERSION, "--skip-suite"],
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
        [sys.executable, str(PUBLISH_SCRIPT), "--version", TEST_VERSION, "--dry-run"],
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


def teardown_module(module):
    _restore_targets()


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
    assert TEST_VERSION in _DRY_RUN_OUTPUT


# --- Report and candidate artifact tests ---

def test_validation_report_exists():
    assert VALIDATION_REPORT.exists()


def test_validation_report_status_is_pass():
    with VALIDATION_REPORT.open(encoding="utf-8") as fh:
        report = json.load(fh)
    assert report["status"] == "pass"


def test_candidate_zip_exists():
    assert CANDIDATE_ZIP.exists()


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


# --- Error path tests: publication gates ---

def test_gate_1_missing_report_exits_nonzero(tmp_path):
    """Gate 1: missing report exits 1."""
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(tmp_path / "nonexistent-report.json"),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_gate_1_missing_report_error_message(tmp_path):
    """Gate 1: error message says 'Validation report not found'."""
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(tmp_path / "nonexistent-report.json"),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Validation report not found" in result.stderr


def test_gate_2_invalid_json_exits_nonzero(tmp_path):
    """Gate 2: malformed JSON exits 1 instead of raising a traceback."""
    report_path = tmp_path / "validation-report-v0.1.0-dev.json"
    report_path.write_text("{invalid json", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_gate_2_invalid_json_error_message(tmp_path):
    """Gate 2: malformed JSON reports a clear validation error."""
    report_path = tmp_path / "validation-report-v0.1.0-dev.json"
    report_path.write_text("{invalid json", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Validation report is not valid JSON" in result.stderr


def test_gate_3_version_mismatch_exits_nonzero(tmp_path):
    """Gate 3: report version != requested version exits 1."""
    report = {
        "version": "9.9.9",
        "status": "pass",
        "candidate": "release-candidates/godot-spacetime-v9.9.9.zip",
        "checks": {},
    }
    report_path = tmp_path / "validation-report-v9.9.9.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", "1.0.0",
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_gate_3_version_mismatch_error_message(tmp_path):
    """Gate 3: error message says 'does not match'."""
    report = {
        "version": "9.9.9",
        "status": "pass",
        "candidate": "release-candidates/godot-spacetime-v9.9.9.zip",
        "checks": {},
    }
    report_path = tmp_path / "validation-report-v9.9.9.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", "1.0.0",
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "does not match" in result.stderr


def test_gate_4_failed_status_exits_nonzero(tmp_path):
    """Gate 4: status != 'pass' exits 1."""
    report = {
        "version": TEST_VERSION,
        "status": "fail",
        "candidate": str(CANDIDATE_ZIP.relative_to(ROOT)),
        "checks": {
            "package": {"status": "fail", "detail": "ZIP missing required files"},
        },
    }
    report_path = tmp_path / f"validation-report-v{TEST_VERSION}.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_gate_4_failed_status_error_message(tmp_path):
    """Gate 4: error message says 'Validation did not pass'."""
    report = {
        "version": TEST_VERSION,
        "status": "fail",
        "candidate": str(CANDIDATE_ZIP.relative_to(ROOT)),
        "checks": {
            "package": {"status": "fail", "detail": "ZIP missing required files"},
        },
    }
    report_path = tmp_path / f"validation-report-v{TEST_VERSION}.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Validation did not pass" in result.stderr


def test_gate_4_failed_status_includes_check_detail(tmp_path):
    """Gate 4: per-check failure details appear in stderr."""
    report = {
        "version": TEST_VERSION,
        "status": "fail",
        "candidate": str(CANDIDATE_ZIP.relative_to(ROOT)),
        "checks": {
            "package": {"status": "fail", "detail": "ZIP missing required files"},
        },
    }
    report_path = tmp_path / f"validation-report-v{TEST_VERSION}.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "ZIP missing required files" in result.stderr


def test_gate_5_missing_zip_exits_nonzero(tmp_path):
    """Gate 5: missing candidate ZIP exits 1."""
    report = {
        "version": TEST_VERSION,
        "status": "pass",
        "candidate": f"release-candidates/godot-spacetime-v{TEST_VERSION}-MISSING.zip",
        "checks": {
            "package": {"status": "pass", "detail": "ok"},
            "foundation": {"status": "pass", "detail": "ok"},
            "test_suite": {"status": "pass", "detail": "ok"},
            "packaging_checks": {"status": "pass", "detail": "ok"},
        },
    }
    report_path = tmp_path / f"validation-report-v{TEST_VERSION}.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_gate_5_missing_zip_error_message(tmp_path):
    """Gate 5: error message says 'Candidate ZIP not found'."""
    report = {
        "version": TEST_VERSION,
        "status": "pass",
        "candidate": f"release-candidates/godot-spacetime-v{TEST_VERSION}-MISSING.zip",
        "checks": {
            "package": {"status": "pass", "detail": "ok"},
            "foundation": {"status": "pass", "detail": "ok"},
            "test_suite": {"status": "pass", "detail": "ok"},
            "packaging_checks": {"status": "pass", "detail": "ok"},
        },
    }
    report_path = tmp_path / f"validation-report-v{TEST_VERSION}.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Candidate ZIP not found" in result.stderr


def test_gate_5_rejects_absolute_candidate_path(tmp_path):
    """Gate 5: report candidate cannot escape the repo via an absolute path."""
    report = {
        "version": TEST_VERSION,
        "status": "pass",
        "candidate": str(CANDIDATE_ZIP.resolve()),
        "checks": {
            "package": {"status": "pass", "detail": "ok"},
            "foundation": {"status": "pass", "detail": "ok"},
            "test_suite": {"status": "pass", "detail": "ok"},
            "packaging_checks": {"status": "pass", "detail": "ok"},
        },
    }
    report_path = tmp_path / f"validation-report-v{TEST_VERSION}.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "must be relative to the repository root" in result.stderr


def test_gate_5_rejects_candidate_outside_release_candidates(tmp_path):
    """Gate 5: report candidate must stay under release-candidates/."""
    report = {
        "version": TEST_VERSION,
        "status": "pass",
        "candidate": "addons/godot_spacetime/plugin.cfg",
        "checks": {
            "package": {"status": "pass", "detail": "ok"},
            "foundation": {"status": "pass", "detail": "ok"},
            "test_suite": {"status": "pass", "detail": "ok"},
            "packaging_checks": {"status": "pass", "detail": "ok"},
        },
    }
    report_path = tmp_path / f"validation-report-v{TEST_VERSION}.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "must stay within release-candidates/" in result.stderr


# --- Dry-run output completeness ---

def test_dry_run_output_mentions_would_create_release():
    assert "DRY RUN: Would create GitHub Release" in _DRY_RUN_OUTPUT


def test_dry_run_output_mentions_would_upload():
    assert "DRY RUN: Would upload" in _DRY_RUN_OUTPUT


def test_dry_run_output_mentions_release_skipped():
    assert "DRY RUN: Release skipped." in _DRY_RUN_OUTPUT


# --- Skipped test_suite warning (setup_module uses --skip-suite) ---

def test_dry_run_warns_when_test_suite_skipped():
    assert "WARNING: test_suite was skipped" in _DRY_RUN_OUTPUT


# --- Script help: additional flags ---

def test_publish_script_help_exposes_report_flag():
    result = subprocess.run(
        [sys.executable, str(PUBLISH_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "--report" in result.stdout


def test_publish_script_help_exposes_version_flag():
    result = subprocess.run(
        [sys.executable, str(PUBLISH_SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "--version" in result.stdout


# --- Workflow structural completeness ---

def test_release_workflow_has_permissions_contents_write():
    assert "contents: write" in RELEASE_WORKFLOW.read_text(encoding="utf-8")


def test_release_workflow_has_always_condition():
    assert "if: always()" in RELEASE_WORKFLOW.read_text(encoding="utf-8")


def test_publish_release_passes_expected_gh_arguments(tmp_path):
    args_path = tmp_path / "gh-args.json"
    fake_gh = tmp_path / "gh"
    fake_gh.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['GH_CAPTURE']).write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n"
        "print('created release')\n",
        encoding="utf-8",
    )
    fake_gh.chmod(0o755)

    report = {
        "version": TEST_VERSION,
        "status": "pass",
        "candidate": str(CANDIDATE_ZIP.relative_to(ROOT)),
        "checks": {
            "package": {"status": "pass", "detail": "ok"},
            "foundation": {"status": "pass", "detail": "ok"},
            "test_suite": {"status": "pass", "detail": "ok"},
            "packaging_checks": {"status": "pass", "detail": "ok"},
        },
    }
    report_path = tmp_path / f"validation-report-v{TEST_VERSION}.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    git_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert git_head.returncode == 0

    env = os.environ.copy()
    env["GH_CAPTURE"] = str(args_path)
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        [
            sys.executable, str(PUBLISH_SCRIPT),
            "--version", TEST_VERSION,
            "--report", str(report_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0

    gh_args = json.loads(args_path.read_text(encoding="utf-8"))
    assert gh_args[:3] == ["release", "create", f"v{TEST_VERSION}"]
    assert str(CANDIDATE_ZIP) in gh_args
    assert gh_args[gh_args.index("--title") + 1] == f"GodotSpacetime SDK v{TEST_VERSION}"
    assert gh_args[gh_args.index("--target") + 1] == git_head.stdout.strip()

    notes = gh_args[gh_args.index("--notes") + 1]
    assert "docs/compatibility-matrix.md" in notes
    assert "docs/install.md" in notes
