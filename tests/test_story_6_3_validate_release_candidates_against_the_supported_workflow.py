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
_PROC: subprocess.CompletedProcess | None = None  # full result from setup_module run


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def setup_module(module: object) -> None:
    global _TEMP_DIR, _REPORT, _PROC
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
    _PROC = result  # retain for stdout content tests


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


# ===========================================================================
# Additional coverage: gaps identified by QA review
# ===========================================================================

import importlib.util as _importlib_util
import zipfile as _zipfile_mod


# ---------------------------------------------------------------------------
# Load validate-release-candidate module for direct unit testing
# (filename has hyphens so importlib is required)
# ---------------------------------------------------------------------------

def _load_validate_rc_module():
    spec = _importlib_util.spec_from_file_location(
        "validate_release_candidate",
        str(ROOT / "scripts/packaging/validate-release-candidate.py"),
    )
    mod = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_VRC = _load_validate_rc_module()


def _write_valid_zip(path) -> None:
    """Minimal valid candidate ZIP for check_packaging_inline unit tests."""
    with _zipfile_mod.ZipFile(path, "w") as zf:
        zf.writestr("addons/godot_spacetime/plugin.cfg", "[plugin]\nversion=0.1.0-dev\n")
        zf.writestr("addons/godot_spacetime/GodotSpacetimePlugin.cs", "// main\n")
        zf.writestr("addons/godot_spacetime/src/Foo.cs", "// source\n")
        zf.writestr("addons/godot_spacetime/thirdparty/notices/sdk.txt", "MIT\n")


# ---------------------------------------------------------------------------
# check_packaging_inline — success path
# ---------------------------------------------------------------------------

def test_packaging_inline_passes_with_minimal_valid_zip(tmp_path) -> None:
    z = tmp_path / "ok.zip"
    _write_valid_zip(z)
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "pass", f"expected pass; got: {result}"
    assert "entries" in result["detail"]


# ---------------------------------------------------------------------------
# check_packaging_inline — failure: file not found
# ---------------------------------------------------------------------------

def test_packaging_inline_fails_when_zip_missing(tmp_path) -> None:
    result = _VRC.check_packaging_inline(tmp_path / "absent.zip")
    assert result["status"] == "fail"
    assert "Candidate ZIP not found" in result["detail"]


# ---------------------------------------------------------------------------
# check_packaging_inline — failure: corrupt ZIP bytes
# ---------------------------------------------------------------------------

def test_packaging_inline_fails_when_zip_is_corrupt(tmp_path) -> None:
    p = tmp_path / "corrupt.zip"
    p.write_bytes(b"not a zip file at all")
    result = _VRC.check_packaging_inline(p)
    assert result["status"] == "fail"
    assert "ZIP integrity error" in result["detail"]


# ---------------------------------------------------------------------------
# check_packaging_inline — failure: missing required entries
# ---------------------------------------------------------------------------

def test_packaging_inline_fails_missing_plugin_cfg(tmp_path) -> None:
    z = tmp_path / "c.zip"
    with _zipfile_mod.ZipFile(z, "w") as zf:
        zf.writestr("addons/godot_spacetime/GodotSpacetimePlugin.cs", "x")
        zf.writestr("addons/godot_spacetime/src/A.cs", "x")
        zf.writestr("addons/godot_spacetime/thirdparty/notices/f.txt", "x")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert "plugin.cfg" in result["detail"]


def test_packaging_inline_fails_missing_godot_plugin_cs(tmp_path) -> None:
    z = tmp_path / "c.zip"
    with _zipfile_mod.ZipFile(z, "w") as zf:
        zf.writestr("addons/godot_spacetime/plugin.cfg", "x")
        zf.writestr("addons/godot_spacetime/src/A.cs", "x")
        zf.writestr("addons/godot_spacetime/thirdparty/notices/f.txt", "x")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert "GodotSpacetimePlugin.cs" in result["detail"]


def test_packaging_inline_fails_no_src_cs_files(tmp_path) -> None:
    z = tmp_path / "c.zip"
    with _zipfile_mod.ZipFile(z, "w") as zf:
        zf.writestr("addons/godot_spacetime/plugin.cfg", "x")
        zf.writestr("addons/godot_spacetime/GodotSpacetimePlugin.cs", "x")
        zf.writestr("addons/godot_spacetime/thirdparty/notices/f.txt", "x")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert "src/" in result["detail"] or "no .cs" in result["detail"].lower()


def test_packaging_inline_fails_no_notices_entry(tmp_path) -> None:
    z = tmp_path / "c.zip"
    with _zipfile_mod.ZipFile(z, "w") as zf:
        zf.writestr("addons/godot_spacetime/plugin.cfg", "x")
        zf.writestr("addons/godot_spacetime/GodotSpacetimePlugin.cs", "x")
        zf.writestr("addons/godot_spacetime/src/A.cs", "x")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert "notice" in result["detail"].lower()


def test_packaging_inline_requires_actual_notices_prefix(tmp_path) -> None:
    z = tmp_path / "c.zip"
    with _zipfile_mod.ZipFile(z, "w") as zf:
        zf.writestr("addons/godot_spacetime/plugin.cfg", "x")
        zf.writestr("addons/godot_spacetime/GodotSpacetimePlugin.cs", "x")
        zf.writestr("addons/godot_spacetime/src/A.cs", "x")
        zf.writestr("addons/godot_spacetime/src/thirdparty/notices_fake.txt", "x")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert "notice" in result["detail"].lower()


# ---------------------------------------------------------------------------
# check_packaging_inline — failure: excluded extensions
# ---------------------------------------------------------------------------

def test_packaging_inline_fails_uid_extension(tmp_path) -> None:
    z = tmp_path / "c.zip"
    _write_valid_zip(z)
    with _zipfile_mod.ZipFile(z, "a") as zf:
        zf.writestr("addons/godot_spacetime/scene.uid", "uid://x\n")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert ".uid" in result["detail"]


def test_packaging_inline_fails_import_extension(tmp_path) -> None:
    z = tmp_path / "c.zip"
    _write_valid_zip(z)
    with _zipfile_mod.ZipFile(z, "a") as zf:
        zf.writestr("addons/godot_spacetime/res.import", "[params]\n")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert ".import" in result["detail"]


# ---------------------------------------------------------------------------
# check_packaging_inline — failure: excluded prefixes
# ---------------------------------------------------------------------------

def test_packaging_inline_fails_demo_prefix(tmp_path) -> None:
    z = tmp_path / "c.zip"
    _write_valid_zip(z)
    with _zipfile_mod.ZipFile(z, "a") as zf:
        zf.writestr("demo/README.md", "# demo\n")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert "demo/" in result["detail"]


def test_packaging_inline_fails_tests_prefix(tmp_path) -> None:
    z = tmp_path / "c.zip"
    _write_valid_zip(z)
    with _zipfile_mod.ZipFile(z, "a") as zf:
        zf.writestr("tests/test_x.py", "pass\n")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert "tests/" in result["detail"]


def test_packaging_inline_fails_scripts_prefix(tmp_path) -> None:
    z = tmp_path / "c.zip"
    _write_valid_zip(z)
    with _zipfile_mod.ZipFile(z, "a") as zf:
        zf.writestr("scripts/packaging/validate-release-candidate.py", "# script\n")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert "scripts/" in result["detail"]


# ---------------------------------------------------------------------------
# check_packaging_inline — failure: excluded suffixes
# ---------------------------------------------------------------------------

def test_packaging_inline_fails_csproj_suffix(tmp_path) -> None:
    z = tmp_path / "c.zip"
    _write_valid_zip(z)
    with _zipfile_mod.ZipFile(z, "a") as zf:
        zf.writestr("addons/godot_spacetime/GodotSpacetime.csproj", "<Project/>\n")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert ".csproj" in result["detail"]


def test_packaging_inline_fails_sln_suffix(tmp_path) -> None:
    z = tmp_path / "c.zip"
    _write_valid_zip(z)
    with _zipfile_mod.ZipFile(z, "a") as zf:
        zf.writestr("addons/godot_spacetime/Solution.sln", "\n")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert ".sln" in result["detail"]


# ---------------------------------------------------------------------------
# check_packaging_inline — failure: entry outside addon prefix
# ---------------------------------------------------------------------------

def test_packaging_inline_fails_file_outside_addon_prefix(tmp_path) -> None:
    z = tmp_path / "c.zip"
    _write_valid_zip(z)
    with _zipfile_mod.ZipFile(z, "a") as zf:
        zf.writestr("README.md", "# project\n")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert "outside addon prefix" in result["detail"]


# ---------------------------------------------------------------------------
# check_packaging_inline — error list capped at 10
# ---------------------------------------------------------------------------

def test_packaging_inline_errors_capped_at_ten(tmp_path) -> None:
    """Detail is capped at 10 error segments even when there are many more violations."""
    z = tmp_path / "c.zip"
    with _zipfile_mod.ZipFile(z, "w") as zf:
        # No valid entries; 15 files each producing 3 errors = 49 total errors
        for i in range(15):
            zf.writestr(f"demo/extra_{i}.uid", "x")
    result = _VRC.check_packaging_inline(z)
    assert result["status"] == "fail"
    assert len(result["detail"].split("; ")) <= 10


# ---------------------------------------------------------------------------
# run_subprocess — unit tests
# ---------------------------------------------------------------------------

def test_run_subprocess_returns_pass_on_zero_exit() -> None:
    result = _VRC.run_subprocess([sys.executable, "-c", "print('ok')"], ROOT)
    assert result["status"] == "pass"
    assert isinstance(result["detail"], str) and result["detail"]


def test_run_subprocess_returns_fail_on_nonzero_exit() -> None:
    result = _VRC.run_subprocess(
        [sys.executable, "-c", "import sys; sys.exit(3)"], ROOT
    )
    assert result["status"] == "fail"
    assert "exit 3" in result["detail"]


def test_run_subprocess_detail_is_ok_when_no_output() -> None:
    result = _VRC.run_subprocess([sys.executable, "-c", "pass"], ROOT)
    assert result["status"] == "pass"
    assert result["detail"] == "OK"


def test_run_subprocess_truncates_detail_at_500_chars() -> None:
    long_str = "X" * 600
    result = _VRC.run_subprocess(
        [sys.executable, "-c", f"print({long_str!r})"],
        ROOT,
    )
    assert result["status"] == "pass"
    assert len(result["detail"]) <= 500


# ---------------------------------------------------------------------------
# main() orchestration — stale candidate handling
# ---------------------------------------------------------------------------

def test_main_rejects_stale_candidate_when_package_step_fails(tmp_path, monkeypatch) -> None:
    root = tmp_path
    report_path = root / "report.json"
    candidate_path = root / "release-candidates" / "godot-spacetime-v0.1.0-dev.zip"
    candidate_path.parent.mkdir(parents=True)
    _write_valid_zip(candidate_path)

    def _fake_run_subprocess(cmd, cwd):
        cmd_text = " ".join(str(part) for part in cmd)
        if "package-release.py" in cmd_text:
            return {"status": "fail", "detail": "exit 1: packaging failed"}
        if "validate-foundation.py" in cmd_text:
            return {"status": "pass", "detail": "foundation ok"}
        raise AssertionError(f"unexpected subprocess call: {cmd}")

    monkeypatch.setattr(_VRC, "repo_root", lambda: root)
    monkeypatch.setattr(_VRC, "run_subprocess", _fake_run_subprocess)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate-release-candidate.py",
            "--version", "0.1.0-dev",
            "--report", str(report_path),
            "--skip-suite",
        ],
    )

    exit_code = _VRC.main()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert not candidate_path.exists(), "stale candidate ZIP must be removed before packaging"
    assert report["status"] == "fail"
    assert report["checks"]["package"]["status"] == "fail"
    assert report["checks"]["packaging_checks"]["status"] == "fail"
    assert "package step failed" in report["checks"]["packaging_checks"]["detail"]


# ---------------------------------------------------------------------------
# Integration: script reads version from plugin.cfg when --version is omitted
# ---------------------------------------------------------------------------

def test_script_reads_version_from_plugin_cfg(tmp_path) -> None:
    """Running without --version must default to plugin.cfg version (0.1.0-dev)."""
    report = tmp_path / "no_version_flag_report.json"
    proc = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--report", str(report), "--skip-suite"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"Script exited {proc.returncode}:\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    data = json.loads(report.read_text("utf-8"))
    assert data["version"] == "0.1.0-dev", (
        f"Version must be read from plugin.cfg as '0.1.0-dev'; got '{data['version']}'"
    )


# ---------------------------------------------------------------------------
# Integration: default report path (no --report flag)
# ---------------------------------------------------------------------------

def test_script_default_report_path_is_under_release_candidates() -> None:
    """Script writes report to release-candidates/validation-report-v{ver}.json by default."""
    default_report = ROOT / "release-candidates" / "validation-report-v0.1.0-dev.json"
    proc = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--version", "0.1.0-dev", "--skip-suite"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"Script exited {proc.returncode}:\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert default_report.exists(), f"Default report not found at {default_report}"
    data = json.loads(default_report.read_text("utf-8"))
    assert data["status"] == "pass"


# ---------------------------------------------------------------------------
# Human-readable stdout — using _PROC captured in setup_module
# ---------------------------------------------------------------------------

def test_script_stdout_progress_marker_1of4() -> None:
    assert "[1/4]" in _PROC.stdout, "stdout must contain '[1/4]' packaging progress marker"


def test_script_stdout_progress_marker_2of4() -> None:
    assert "[2/4]" in _PROC.stdout, "stdout must contain '[2/4]' foundation progress marker"


def test_script_stdout_progress_marker_3of4() -> None:
    assert "[3/4]" in _PROC.stdout, "stdout must contain '[3/4]' test-suite progress marker"


def test_script_stdout_progress_marker_4of4() -> None:
    assert "[4/4]" in _PROC.stdout, "stdout must contain '[4/4]' packaging-checks progress marker"


def test_script_stdout_overall_status_line() -> None:
    assert "Overall status:" in _PROC.stdout, "stdout must contain 'Overall status:' summary line"


def test_script_stdout_mentions_report_path() -> None:
    assert "Report written:" in _PROC.stdout, "stdout must announce the written report path"


# ---------------------------------------------------------------------------
# Report portability: candidate field is relative
# ---------------------------------------------------------------------------

def test_report_candidate_is_relative_path() -> None:
    """candidate must be a relative path string so it is portable across environments (AC 1)."""
    assert not _REPORT["candidate"].startswith("/"), (
        f"Report 'candidate' must be relative, not absolute; got: {_REPORT['candidate']}"
    )


# ---------------------------------------------------------------------------
# Workflow: additional structural content checks
# ---------------------------------------------------------------------------

def test_workflow_upload_step_runs_on_always() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "if: always()" in content, \
        "Upload step must have 'if: always()' so report is captured even when validation fails (AC 2)"


def test_workflow_upload_ignores_missing_files() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "if-no-files-found: ignore" in content, \
        "Upload step must set 'if-no-files-found: ignore' for graceful CI runs with no report"


def test_workflow_artifact_named_validation_report() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "name: validation-report" in content, \
        "Artifact must be named 'validation-report' for Story 6.4 consumption (AC 3)"


def test_workflow_uses_checkout_v4() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "actions/checkout@v4" in content, \
        "Workflow must use actions/checkout@v4"


def test_workflow_uses_setup_python_v5() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "actions/setup-python@v5" in content, \
        "Workflow must use actions/setup-python@v5 (consistent with validate-foundation.yml)"


def test_workflow_version_input_required_false() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "required: false" in content, \
        "version input must be 'required: false' so workflow runs without an explicit version"


def test_workflow_job_runs_on_ubuntu_latest() -> None:
    content = _read(".github/workflows/release-validation.yml")
    assert "ubuntu-latest" in content, \
        "validate-release job must run on ubuntu-latest"
