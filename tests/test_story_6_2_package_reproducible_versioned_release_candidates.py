"""
Tests for Story 6.2: Package Reproducible Versioned Release Candidates

Validates:
- scripts/packaging/package-release.py exists and produces correct output (AC 1, 2)
- addons/godot_spacetime/thirdparty/notices/ exists with SpacetimeDB attribution (AC 3)
- Packaged ZIP excludes demo, tests, spacetime/ and Godot cache files (AC 1)
- Packaged ZIP is versioned and reproducible (AC 2)
- All prior story deliverables remain intact (regression guards)
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = ROOT / "scripts/packaging/package-release.py"

_TEMP_DIR: str | None = None
_PACKAGED_ZIP: Path | None = None


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def setup_module(module: object) -> None:
    global _TEMP_DIR, _PACKAGED_ZIP
    _TEMP_DIR = tempfile.mkdtemp(prefix="story_6_2_")
    _PACKAGED_ZIP = Path(_TEMP_DIR) / "godot-spacetime-v0.1.0-dev.zip"
    result = subprocess.run(
        [
            sys.executable, str(PACKAGE_SCRIPT),
            "--version", "0.1.0-dev",
            "--output", str(_PACKAGED_ZIP),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"package-release.py failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert _PACKAGED_ZIP.exists(), "packaging script did not create output ZIP"


def teardown_module(module: object) -> None:
    if _TEMP_DIR:
        shutil.rmtree(_TEMP_DIR, ignore_errors=True)


def _zip_names() -> list[str]:
    assert _PACKAGED_ZIP is not None
    with zipfile.ZipFile(_PACKAGED_ZIP) as zf:
        return sorted(zf.namelist())


# ---------------------------------------------------------------------------
# 3.1 Static existence tests
# ---------------------------------------------------------------------------

def test_packaging_directory_exists() -> None:
    assert (ROOT / "scripts/packaging").is_dir(), \
        "scripts/packaging/ directory must exist (AC 1, 2)"


def test_package_release_script_exists() -> None:
    assert PACKAGE_SCRIPT.exists(), \
        "scripts/packaging/package-release.py must exist (AC 1, 2)"


def test_thirdparty_notices_directory_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/thirdparty/notices").is_dir(), \
        "addons/godot_spacetime/thirdparty/notices/ directory must exist (AC 3)"


def test_thirdparty_notices_has_at_least_one_file() -> None:
    notices_dir = ROOT / "addons/godot_spacetime/thirdparty/notices"
    files = [f for f in notices_dir.iterdir() if f.is_file()]
    assert files, "thirdparty/notices/ must contain at least one notice file (AC 3)"


def test_spacetimedb_notice_file_exists() -> None:
    notices_dir = ROOT / "addons/godot_spacetime/thirdparty/notices"
    names = [f.name.lower() for f in notices_dir.iterdir() if f.is_file()]
    assert any("spacetimedb" in n for n in names), \
        "thirdparty/notices/ must contain a SpacetimeDB notice file (AC 3)"


def test_spacetimedb_notice_is_non_empty() -> None:
    notice = ROOT / "addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt"
    assert notice.exists() and notice.stat().st_size > 0, \
        "spacetimedb-client-sdk.txt must be non-empty (AC 3)"


# ---------------------------------------------------------------------------
# 3.2 / 3.3 Functional inclusion tests
# ---------------------------------------------------------------------------

def test_packaged_zip_exists() -> None:
    assert _PACKAGED_ZIP is not None and _PACKAGED_ZIP.exists(), \
        "Packaged ZIP must be created by package-release.py (AC 1)"


def test_packaged_zip_contains_plugin_cfg() -> None:
    names = _zip_names()
    assert "addons/godot_spacetime/plugin.cfg" in names, \
        "ZIP must contain addons/godot_spacetime/plugin.cfg (AC 1)"


def test_packaged_zip_contains_plugin_entrypoint() -> None:
    names = _zip_names()
    assert "addons/godot_spacetime/GodotSpacetimePlugin.cs" in names, \
        "ZIP must contain GodotSpacetimePlugin.cs (AC 1)"


def test_packaged_zip_contains_src_cs_files() -> None:
    names = _zip_names()
    src_files = [n for n in names if n.startswith("addons/godot_spacetime/src/") and n.endswith(".cs")]
    assert src_files, \
        "ZIP must contain .cs source files under addons/godot_spacetime/src/ (AC 1)"


def test_packaged_zip_contains_spacetimeclient() -> None:
    names = _zip_names()
    assert any("SpacetimeClient.cs" in n for n in names), \
        "ZIP must contain SpacetimeClient.cs (primary public facade) (AC 1)"


def test_packaged_zip_contains_thirdparty_notices() -> None:
    names = _zip_names()
    assert any("thirdparty/notices" in n for n in names), \
        "ZIP must contain thirdparty/notices entries (AC 3)"


def test_packaged_zip_contains_spacetimedb_notice() -> None:
    names = _zip_names()
    assert any("spacetimedb-client-sdk" in n for n in names), \
        "ZIP must contain the spacetimedb-client-sdk notice file (AC 3)"


def test_packaged_zip_has_reasonable_file_count() -> None:
    names = _zip_names()
    assert len(names) >= 10, \
        f"ZIP should contain at least 10 files; found {len(names)} (AC 1)"


def test_packaged_zip_opens_without_error() -> None:
    assert _PACKAGED_ZIP is not None
    with zipfile.ZipFile(_PACKAGED_ZIP) as zf:
        assert zf.testzip() is None, "ZIP must open without integrity errors (AC 1)"


# ---------------------------------------------------------------------------
# 3.4 Functional exclusion tests
# ---------------------------------------------------------------------------

def test_packaged_zip_excludes_uid_files() -> None:
    names = _zip_names()
    uid_files = [n for n in names if n.endswith(".uid")]
    assert not uid_files, \
        f"ZIP must not contain .uid files (Godot cache); found: {uid_files} (AC 1)"


def test_packaged_zip_excludes_import_files() -> None:
    names = _zip_names()
    import_files = [n for n in names if n.endswith(".import")]
    assert not import_files, \
        f"ZIP must not contain .import files (Godot cache); found: {import_files} (AC 1)"


def test_packaged_zip_excludes_demo() -> None:
    names = _zip_names()
    demo_files = [n for n in names if n.startswith("demo/")]
    assert not demo_files, \
        f"ZIP must not contain demo/ files; found: {demo_files} (AC 1)"


def test_packaged_zip_excludes_tests() -> None:
    names = _zip_names()
    test_files = [n for n in names if n.startswith("tests/")]
    assert not test_files, \
        f"ZIP must not contain tests/ files; found: {test_files} (AC 1)"


def test_packaged_zip_excludes_spacetime_modules() -> None:
    names = _zip_names()
    spacetime_files = [n for n in names if n.startswith("spacetime/")]
    assert not spacetime_files, \
        f"ZIP must not contain spacetime/ module files; found: {spacetime_files} (AC 1)"


def test_packaged_zip_excludes_scripts() -> None:
    names = _zip_names()
    script_files = [n for n in names if n.startswith("scripts/")]
    assert not script_files, \
        f"ZIP must not contain scripts/ files; found: {script_files} (AC 1)"


def test_packaged_zip_excludes_bmad_output() -> None:
    names = _zip_names()
    bmad_files = [n for n in names if n.startswith("_bmad-output/")]
    assert not bmad_files, \
        f"ZIP must not contain _bmad-output/ planning artifacts; found: {bmad_files} (AC 1)"


def test_packaged_zip_excludes_csproj() -> None:
    names = _zip_names()
    csproj_files = [n for n in names if n.endswith(".csproj")]
    assert not csproj_files, \
        f"ZIP must not contain .csproj files; found: {csproj_files} (AC 1)"


def test_packaged_zip_excludes_sln() -> None:
    names = _zip_names()
    sln_files = [n for n in names if n.endswith(".sln")]
    assert not sln_files, \
        f"ZIP must not contain .sln files; found: {sln_files} (AC 1)"


def test_packaged_zip_all_entries_under_addon() -> None:
    names = _zip_names()
    non_addon = [n for n in names if not n.startswith("addons/godot_spacetime/")]
    assert not non_addon, \
        f"All ZIP entries must be under addons/godot_spacetime/; unexpected entries: {non_addon} (AC 1)"


# ---------------------------------------------------------------------------
# 3.5 Versioning tests
# ---------------------------------------------------------------------------

def test_packaged_zip_filename_contains_version() -> None:
    assert _PACKAGED_ZIP is not None
    assert "0.1.0-dev" in _PACKAGED_ZIP.name, \
        f"ZIP filename must contain the version string '0.1.0-dev'; got {_PACKAGED_ZIP.name} (AC 2)"


def test_default_output_path_uses_release_candidates_dir() -> None:
    """Run without --output and verify the default path is under release-candidates/."""
    result = subprocess.run(
        [sys.executable, str(PACKAGE_SCRIPT), "--version", "0.1.0-test"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"package-release.py failed without --output flag:\n{result.stderr}"
    )
    assert "release-candidates" in result.stdout, \
        "Default output path must be under release-candidates/ (AC 2)"
    # Clean up the created file
    candidate = ROOT / "release-candidates" / "godot-spacetime-v0.1.0-test.zip"
    candidate.unlink(missing_ok=True)


def test_custom_version_appears_in_output() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "godot-spacetime-v9.9.9-custom.zip"
        result = subprocess.run(
            [sys.executable, str(PACKAGE_SCRIPT), "--version", "9.9.9-custom", "--output", str(out)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"packaging failed for custom version: {result.stderr}"
        assert out.exists(), "ZIP must be created at the specified --output path"
        assert "9.9.9-custom" in out.name


def test_version_read_from_plugin_cfg_by_default() -> None:
    """Running without --version reads the version from plugin.cfg."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test-default-version.zip"
        result = subprocess.run(
            [sys.executable, str(PACKAGE_SCRIPT), "--output", str(out)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"packaging failed with default version: {result.stderr}"
        # plugin.cfg contains version="0.1.0-dev"
        assert "0.1.0-dev" in result.stdout, \
            "Default version must be read from plugin.cfg (currently '0.1.0-dev')"


# ---------------------------------------------------------------------------
# 3.6 Reproducibility test
# ---------------------------------------------------------------------------

def test_package_is_reproducible() -> None:
    """Running the packaging script twice with the same version produces identical archive bytes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out1 = Path(tmpdir) / "run1.zip"
        out2 = Path(tmpdir) / "run2.zip"
        for out in (out1, out2):
            result = subprocess.run(
                [
                    sys.executable, str(PACKAGE_SCRIPT),
                    "--version", "repro-test",
                    "--output", str(out),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"packaging run failed: {result.stderr}"
        with zipfile.ZipFile(out1) as z1, zipfile.ZipFile(out2) as z2:
            names1 = sorted(z1.namelist())
            names2 = sorted(z2.namelist())
        assert names1 == names2, (
            "Packaging is not reproducible: file entry lists differ between runs\n"
            f"Run 1: {names1}\nRun 2: {names2}"
        )
        hash1 = hashlib.sha256(out1.read_bytes()).hexdigest()
        hash2 = hashlib.sha256(out2.read_bytes()).hexdigest()
        assert hash1 == hash2, (
            "Packaging is not reproducible: archive bytes differ between runs\n"
            f"Run 1 SHA256: {hash1}\nRun 2 SHA256: {hash2}"
        )


# ---------------------------------------------------------------------------
# 3.7 ZIP entry timestamp test (reproducibility)
# ---------------------------------------------------------------------------

def test_packaged_zip_entries_have_fixed_timestamp() -> None:
    assert _PACKAGED_ZIP is not None
    with zipfile.ZipFile(_PACKAGED_ZIP) as zf:
        for info in zf.infolist():
            assert info.date_time == (2020, 1, 1, 0, 0, 0), (
                f"ZIP entry '{info.filename}' has non-fixed timestamp {info.date_time}; "
                "all entries must use (2020, 1, 1, 0, 0, 0) for reproducibility (AC 2)"
            )


# ---------------------------------------------------------------------------
# 3.8 Notice content tests
# ---------------------------------------------------------------------------

def test_notice_references_spacetimedb() -> None:
    content = _read("addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt")
    assert "SpacetimeDB" in content, \
        "spacetimedb-client-sdk.txt must reference 'SpacetimeDB' (AC 3)"


def test_notice_references_clockworklabs() -> None:
    content = _read("addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt")
    assert "clockworklabs" in content.lower(), \
        "spacetimedb-client-sdk.txt must reference 'clockworklabs' (AC 3)"


def test_notice_references_license() -> None:
    content = _read("addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt")
    assert "license" in content.lower() or "LICENSE" in content, \
        "spacetimedb-client-sdk.txt must reference license information (AC 3)"


def test_notice_references_github_url() -> None:
    content = _read("addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt")
    assert "github.com" in content, \
        "spacetimedb-client-sdk.txt must include a github.com URL for the source project (AC 3)"


def test_notice_is_brief_attribution() -> None:
    content = _read("addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt")
    assert len(content) < 800, \
        "spacetimedb-client-sdk.txt must be a brief attribution notice, not a full license copy (AC 3)"


# ---------------------------------------------------------------------------
# 3.9 .gitignore test
# ---------------------------------------------------------------------------

def test_gitignore_includes_release_candidates() -> None:
    gitignore = _read(".gitignore")
    assert "release-candidates/" in gitignore, \
        ".gitignore must contain 'release-candidates/' to prevent committing binary artifacts (AC 2)"


def test_gitignore_places_release_candidates_after_dotnet_section() -> None:
    lines = _read(".gitignore").splitlines()
    release_index = lines.index("release-candidates/")
    python_cache_header_index = lines.index("# Python caches from validation scripts and pytest")
    dotnet_tail_index = lines.index("coverage*.xml")
    assert dotnet_tail_index < release_index < python_cache_header_index, (
        "release-candidates/ must be appended after the .NET section and before the Python cache section "
        "(Task 1.6 exact placement requirement)"
    )


# ---------------------------------------------------------------------------
# 3.10 Regression guards — prior story deliverables
# ---------------------------------------------------------------------------

def test_regression_docs_compatibility_matrix_exists() -> None:
    assert (ROOT / "docs/compatibility-matrix.md").exists(), \
        "docs/compatibility-matrix.md must still exist (Story 6.1 deliverable)"


def test_regression_compatibility_matrix_has_support_policy() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "## Support Policy" in content, \
        "docs/compatibility-matrix.md must contain '## Support Policy' (Story 6.1 deliverable)"


def test_regression_auth_required_not_in_enum() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "AuthRequired" not in content, \
        "ConnectionAuthState.cs must not contain AuthRequired (removed in Story 6.1)"


def test_regression_runtime_boundaries_has_internal_sealed() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "internal sealed" in content, \
        "docs/runtime-boundaries.md must contain 'internal sealed' sentence (Story 6.1 C3)"


def test_regression_docs_install_exists() -> None:
    assert (ROOT / "docs/install.md").exists(), "docs/install.md must exist (Story 5.4)"


def test_regression_docs_quickstart_exists() -> None:
    assert (ROOT / "docs/quickstart.md").exists(), "docs/quickstart.md must exist (Story 5.4)"


def test_regression_docs_codegen_exists() -> None:
    assert (ROOT / "docs/codegen.md").exists(), "docs/codegen.md must exist (Story 1.6/1.7)"


def test_regression_docs_connection_exists() -> None:
    assert (ROOT / "docs/connection.md").exists(), "docs/connection.md must exist (Story 5.4)"


def test_regression_docs_troubleshooting_exists() -> None:
    assert (ROOT / "docs/troubleshooting.md").exists(), "docs/troubleshooting.md must exist (Story 5.5)"


def test_regression_docs_migration_exists() -> None:
    assert (ROOT / "docs/migration-from-community-plugin.md").exists(), \
        "docs/migration-from-community-plugin.md must exist (Story 5.6)"


def test_regression_demo_readme_exists() -> None:
    assert (ROOT / "demo/README.md").exists(), "demo/README.md must exist (Story 5.3)"


def test_regression_demo_main_cs_exists() -> None:
    assert (ROOT / "demo/DemoMain.cs").exists(), "demo/DemoMain.cs must exist (Story 5.3)"


def test_regression_spacetime_client_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Public/SpacetimeClient.cs").exists(), \
        "addons/godot_spacetime/src/Public/SpacetimeClient.cs must exist"


def test_regression_plugin_cfg_version_intact() -> None:
    content = _read("addons/godot_spacetime/plugin.cfg")
    assert "version=" in content, "plugin.cfg must still contain version= field"
    assert "0.1.0-dev" in content, "plugin.cfg version must still be 0.1.0-dev"


def test_regression_compatibility_matrix_version_intact() -> None:
    content = _read("docs/compatibility-matrix.md")
    assert "4.6.2" in content, \
        "docs/compatibility-matrix.md version baseline 4.6.2 must be intact (Story 6.1)"
    assert "SpacetimeDB.ClientSDK" in content, \
        "docs/compatibility-matrix.md SpacetimeDB.ClientSDK entry must be intact (Story 6.1)"


# ---------------------------------------------------------------------------
# 3.11 ZIP entry attribute tests (reproducibility contract)
# ---------------------------------------------------------------------------

def test_packaged_zip_entries_have_correct_permissions() -> None:
    """Every ZIP entry must have external_attr = 0o644 << 16 for reproducibility (AC 2)."""
    expected_attr = 0o644 << 16
    assert _PACKAGED_ZIP is not None
    with zipfile.ZipFile(_PACKAGED_ZIP) as zf:
        for info in zf.infolist():
            assert info.external_attr == expected_attr, (
                f"ZIP entry '{info.filename}' has external_attr={info.external_attr:#010x}; "
                f"expected {expected_attr:#010x} (0o644 << 16) for reproducibility (AC 2)"
            )


def test_packaged_zip_entries_use_unix_create_system() -> None:
    """Every ZIP entry must declare create_system=3 so archive metadata stays cross-platform reproducible."""
    assert _PACKAGED_ZIP is not None
    with zipfile.ZipFile(_PACKAGED_ZIP) as zf:
        for info in zf.infolist():
            assert info.create_system == 3, (
                f"ZIP entry '{info.filename}' has create_system={info.create_system}; "
                "expected 3 (Unix) for stable permission metadata across platforms"
            )


def test_packaged_zip_entries_use_deflate_compression() -> None:
    """Every ZIP entry must use ZIP_DEFLATED compression (compress_type=8), not STORED."""
    assert _PACKAGED_ZIP is not None
    with zipfile.ZipFile(_PACKAGED_ZIP) as zf:
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_DEFLATED, (
                f"ZIP entry '{info.filename}' uses compress_type={info.compress_type}; "
                f"expected ZIP_DEFLATED ({zipfile.ZIP_DEFLATED})"
            )


def test_packaged_zip_entries_are_sorted() -> None:
    """ZIP entries must be in alphabetical order (Dev Notes: sort by as_posix() path)."""
    names = _zip_names()  # already sorted by _zip_names; verify the ZIP itself is ordered
    assert _PACKAGED_ZIP is not None
    with zipfile.ZipFile(_PACKAGED_ZIP) as zf:
        raw_names = [info.filename for info in zf.infolist()]
    assert raw_names == sorted(raw_names), (
        "ZIP entries are not in alphabetical order; "
        f"expected sorted order but got: {raw_names}"
    )


# ---------------------------------------------------------------------------
# 3.12 Script stdout contract tests
# ---------------------------------------------------------------------------

def test_script_prints_version_line() -> None:
    """Script must print 'Version: {version}' to stdout (main() output contract)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "godot-spacetime-v1.2.3-stdout.zip"
        result = subprocess.run(
            [sys.executable, str(PACKAGE_SCRIPT), "--version", "1.2.3-stdout", "--output", str(out)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"packaging failed: {result.stderr}"
        assert "Version: 1.2.3-stdout" in result.stdout, (
            f"stdout must contain 'Version: 1.2.3-stdout'; got:\n{result.stdout}"
        )


def test_script_prints_packaged_summary_line() -> None:
    """Script must print 'Packaged N files into <path>' to stdout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "godot-spacetime-v1.2.3-summary.zip"
        result = subprocess.run(
            [sys.executable, str(PACKAGE_SCRIPT), "--version", "1.2.3-summary", "--output", str(out)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"packaging failed: {result.stderr}"
        assert "Packaged" in result.stdout and "files into" in result.stdout, (
            f"stdout must contain 'Packaged N files into <path>'; got:\n{result.stdout}"
        )


def test_script_prints_resolved_output_path_for_relative_output() -> None:
    """Relative --output paths must be reported as resolved absolute paths on success."""
    relative_output = Path("tmp/story-6-2-resolved-output.zip")
    resolved_output = (ROOT / relative_output).resolve()
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [sys.executable, str(PACKAGE_SCRIPT), "--version", "1.2.3-resolved", "--output", str(relative_output)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"packaging failed: {result.stderr}"
        assert str(resolved_output) in result.stdout, (
            f"stdout must contain the resolved output path {resolved_output}; got:\n{result.stdout}"
        )
    finally:
        resolved_output.unlink(missing_ok=True)


def test_script_prints_candidate_line() -> None:
    """Script must print 'Candidate: {filename}' to stdout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "godot-spacetime-v1.2.3-cand.zip"
        result = subprocess.run(
            [sys.executable, str(PACKAGE_SCRIPT), "--version", "1.2.3-cand", "--output", str(out)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"packaging failed: {result.stderr}"
        assert "Candidate: godot-spacetime-v1.2.3-cand.zip" in result.stdout, (
            f"stdout must contain 'Candidate: godot-spacetime-v1.2.3-cand.zip'; got:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# 3.13 Architecture constraint: scripts/packaging/ not in support-baseline.json
# ---------------------------------------------------------------------------

def test_support_baseline_does_not_include_scripts_packaging() -> None:
    """scripts/packaging/ must NOT appear in support-baseline.json (Dev Notes constraint)."""
    import json
    baseline_path = ROOT / "scripts/compatibility/support-baseline.json"
    assert baseline_path.exists(), "scripts/compatibility/support-baseline.json must exist"
    data = json.loads(baseline_path.read_text(encoding="utf-8"))
    required_paths = [entry["path"] for entry in data.get("required_paths", [])]
    packaging_entries = [p for p in required_paths if "scripts/packaging" in p]
    assert not packaging_entries, (
        f"scripts/packaging must NOT be in support-baseline.json required_paths; "
        f"found: {packaging_entries}"
    )


# ---------------------------------------------------------------------------
# 3.14 Assets directory inclusion test
# ---------------------------------------------------------------------------

def test_packaged_zip_contains_assets_directory() -> None:
    """ZIP must contain at least one file under addons/godot_spacetime/assets/ (icon.svg)."""
    names = _zip_names()
    assets_files = [n for n in names if "assets/" in n]
    assert assets_files, \
        "ZIP must contain files under addons/godot_spacetime/assets/ (e.g. icon.svg) (AC 1)"


def test_packaged_zip_contains_icon_svg() -> None:
    """ZIP must contain assets/icon.svg (the addon's icon resource)."""
    names = _zip_names()
    assert "addons/godot_spacetime/assets/icon.svg" in names, \
        "ZIP must contain addons/godot_spacetime/assets/icon.svg (AC 1)"
