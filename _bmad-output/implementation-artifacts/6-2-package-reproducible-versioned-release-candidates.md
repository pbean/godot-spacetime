# Story 6.2: Package Reproducible Versioned Release Candidates

Status: done

## Story

As the SDK maintainer,
I want reproducible versioned candidate artifacts for the addon,
So that the exact payload intended for adopters can be validated before publication.

## Acceptance Criteria

1. **Given** a candidate version and release metadata **When** I package the SDK for release validation **Then** the candidate artifact contains the distributable addon structure needed by end users and excludes demo or test-only assets
2. **And** the candidate artifact is versioned and reproducible so the same payload can later be published through the GitHub-release-first distribution flow
3. **And** required notices, licensing information, or install metadata needed by adopters are included with the candidate artifact set

## Tasks / Subtasks

- [x] Task 1: Create `scripts/packaging/package-release.py` (AC: 1, 2)
  - [x] 1.1 Create `scripts/packaging/` directory and `package-release.py` using the exact script structure in Dev Notes — accepts `--version` (default: read from `addons/godot_spacetime/plugin.cfg`) and `--output` (default: `release-candidates/godot-spacetime-v{version}.zip` relative to repo root)
  - [x] 1.2 Collect all files under `addons/godot_spacetime/` recursively and sort them; exclude `.uid` and `.import` files (Godot project-cache artifacts that regenerate automatically and are NOT part of the distributable addon)
  - [x] 1.3 Write a reproducible ZIP: set each `ZipInfo.date_time = (2020, 1, 1, 0, 0, 0)` and `ZipInfo.external_attr = 0o644 << 16` on every entry, so the same source files always produce identical archive content regardless of when the script runs
  - [x] 1.4 ZIP entries must preserve the full `addons/godot_spacetime/` path prefix (e.g., `addons/godot_spacetime/plugin.cfg`) so adopters can extract directly into their project root
  - [x] 1.5 Create `output_path.parent` on demand; print a manifest of included files and the resolved output path on success
  - [x] 1.6 Add `release-candidates/` to the root `.gitignore` (append after the `.NET` section) so binary release artifacts are never accidentally committed

- [x] Task 2: Create `addons/godot_spacetime/thirdparty/notices/` with SpacetimeDB.ClientSDK notice (AC: 3)
  - [x] 2.1 Create `addons/godot_spacetime/thirdparty/notices/` directory (architecture-designated location: "Third-party notices for redistributed dependencies stay under `addons/godot_spacetime/thirdparty/notices/`")
  - [x] 2.2 Create `addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt` using the exact content in Dev Notes — a brief adopter-facing attribution notice for the `SpacetimeDB.ClientSDK` NuGet dependency
  - [x] 2.3 Verify (no code change needed): since `thirdparty/notices/` falls under `addons/godot_spacetime/`, `package-release.py` automatically includes its contents in the ZIP with no special-casing required

- [x] Task 3: Write `tests/test_story_6_2_package_reproducible_versioned_release_candidates.py` (AC: 1, 2, 3)
  - [x] 3.1 Static existence tests: `scripts/packaging/` dir; `scripts/packaging/package-release.py`; `addons/godot_spacetime/thirdparty/notices/`; at least one notice file; spacetimedb notice file present; notice file is non-empty
  - [x] 3.2 Add `setup_module` / `teardown_module` hooks that run the packaging script once into a temp directory and clean up after — all functional tests share this single packaged ZIP (see Dev Notes for exact pattern)
  - [x] 3.3 Functional inclusion tests on the packaged ZIP: contains `addons/godot_spacetime/plugin.cfg`; contains `addons/godot_spacetime/GodotSpacetimePlugin.cs`; contains at least one `.cs` source file under `src/`; contains `thirdparty/notices/` entries
  - [x] 3.4 Functional exclusion tests: ZIP contains NO `.uid` files; NO `.import` files; NO entries starting with `demo/`, `tests/`, `spacetime/`, `scripts/`, or `_bmad-output/`; NO `.csproj` or `.sln` files
  - [x] 3.5 Versioning tests: output filename contains the `--version` value; default output path is under `release-candidates/`
  - [x] 3.6 Reproducibility test: run the packaging script twice with the same `--version`; verify sorted namelists are identical across both ZIPs
  - [x] 3.7 ZIP entry timestamp test: every ZIP entry has `date_time == (2020, 1, 1, 0, 0, 0)` (not the current wall clock time)
  - [x] 3.8 Notice content tests: `spacetimedb-client-sdk.txt` references `SpacetimeDB`, `clockworklabs`, `license` (case-insensitive), and a `github.com` URL
  - [x] 3.9 `.gitignore` test: root `.gitignore` contains `release-candidates/`
  - [x] 3.10 Regression guards: all prior Story 6.1 and earlier deliverables remain intact (see Dev Notes)

## Dev Notes

### What This Story Delivers

Story 6.2 creates the packaging infrastructure for the GodotSpacetime SDK release flow. Story 6.3 will call `package-release.py` to produce a candidate and validate it against the supported workflow; Story 6.4 will use the same script in the GitHub release publication step.

**Primary deliverables:**
- `scripts/packaging/package-release.py` — standalone Python 3 script that produces a reproducible, versioned ZIP of `addons/godot_spacetime/` only
- `addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt` — adopter-facing attribution notice for the `SpacetimeDB.ClientSDK` NuGet dependency
- Root `.gitignore` entry for `release-candidates/`

**Secondary deliverable:**
- `tests/test_story_6_2_*.py` — verification suite covering existence, packaging correctness, exclusion guardrails, reproducibility, and regression guards

**No C# changes.** No modifications to any existing file in `addons/`, `docs/`, `demo/`, `tests/`, or `scripts/compatibility/`.

### Critical Architecture Constraints

**Only `addons/godot_spacetime/` is distributable.** These paths must NEVER appear in the release ZIP:
- `demo/` — sample scenes, DemoMain.cs, generated smoke-test bindings
- `tests/` — all test files and fixtures
- `spacetime/` — Rust modules and SpacetimeDB schema sources
- `scripts/` — development and CI tooling
- `_bmad-output/` — project planning artifacts
- `godot-spacetime.csproj`, `godot-spacetime.sln` — repo-level build config (these live outside `addons/`)

**Excluded file extensions within `addons/godot_spacetime/`:**
- `.uid` — Godot editor UID cache (e.g., `GodotSpacetimePlugin.cs.uid`); project-specific; adopters regenerate automatically when they add the addon to their own Godot project
- `.import` — Godot editor import cache (e.g., `assets/icon.svg.import`); same reason as `.uid`

**Reproducibility requirement:** The same source files must always produce the same ZIP content:
1. Sort files alphabetically by their `as_posix()` path before writing
2. Set each `ZipInfo.date_time = (2020, 1, 1, 0, 0, 0)` — strips real mtime from every entry
3. Set each `ZipInfo.external_attr = 0o644 << 16` — consistent Unix permissions

**ZIP path structure:** Preserve the full `addons/godot_spacetime/` prefix. Example entries:
```
addons/godot_spacetime/plugin.cfg
addons/godot_spacetime/GodotSpacetimePlugin.cs
addons/godot_spacetime/assets/icon.svg
addons/godot_spacetime/src/Public/SpacetimeClient.cs
...
addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt
```
This lets adopters unzip directly into their project root.

**Version source:** `addons/godot_spacetime/plugin.cfg` currently contains `version="0.1.0-dev"`. The script reads this field via `configparser`. The value includes the quotes in the file — strip them with `.strip('"')`.

**Output default:** `{repo_root}/release-candidates/godot-spacetime-v{version}.zip`. The `release-candidates/` directory is created on demand and gitignored.

**Architecture open question resolved:** "addon-only ZIP vs addon ZIP plus companion docs/sample references" — this story uses addon-only ZIP. The `docs/` directory is NOT included in the release artifact. Adopters install the addon folder and reference the published docs separately.

**Architecture boundary — `scripts/packaging/` is NOT currently in `support-baseline.json`.** Do NOT add it there. The `validate-foundation.py` script only enforces the baseline defined in `support-baseline.json`; Story 6.2 does not extend that baseline.

### Exact Script: `scripts/packaging/package-release.py`

```python
#!/usr/bin/env python3
"""
Package the GodotSpacetime SDK as a reproducible versioned release candidate.

Usage:
    python3 scripts/packaging/package-release.py [--version X.Y.Z] [--output PATH]

Defaults:
    --version  Read from addons/godot_spacetime/plugin.cfg
    --output   release-candidates/godot-spacetime-v{version}.zip (relative to repo root)
"""
from __future__ import annotations

import argparse
import configparser
import zipfile
from pathlib import Path

ADDON_DIR = Path("addons/godot_spacetime")
DEFAULT_OUTPUT_DIR = Path("release-candidates")

# File extensions excluded from the distributable ZIP (Godot project-cache files)
EXCLUDED_EXTENSIONS = {".uid", ".import"}

# Fixed timestamp for all ZIP entries — guarantees reproducibility
ZIP_ENTRY_TIMESTAMP = (2020, 1, 1, 0, 0, 0)
ZIP_ENTRY_PERMISSIONS = 0o644 << 16


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_version_from_plugin_cfg(root: Path) -> str:
    cfg_path = root / ADDON_DIR / "plugin.cfg"
    parser = configparser.ConfigParser()
    parser.read(str(cfg_path), encoding="utf-8")
    try:
        return parser["plugin"]["version"].strip('"')
    except KeyError as exc:
        raise SystemExit(f"Cannot read version from {cfg_path}: missing key {exc}") from exc


def collect_addon_files(root: Path) -> list[Path]:
    """Return all distributable files under addons/godot_spacetime/, sorted."""
    addon_root = root / ADDON_DIR
    return sorted(
        f for f in addon_root.rglob("*")
        if f.is_file() and f.suffix not in EXCLUDED_EXTENSIONS
    )


def package_release(root: Path, version: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    files = collect_addon_files(root)
    if not files:
        raise SystemExit(f"No distributable files found under {ADDON_DIR}")

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for abs_path in files:
            arc_name = abs_path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(arc_name, date_time=ZIP_ENTRY_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = ZIP_ENTRY_PERMISSIONS
            zf.writestr(info, abs_path.read_bytes())

    print(f"Packaged {len(files)} files into {output_path}")
    print(f"Candidate: {output_path.name}")
    for f in files:
        print(f"  {f.relative_to(root / ADDON_DIR)}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Package GodotSpacetime SDK release candidate"
    )
    parser.add_argument("--version", help="Version string (default: read from plugin.cfg)")
    parser.add_argument(
        "--output",
        help="Output ZIP path (default: release-candidates/godot-spacetime-v{version}.zip)",
    )
    args = parser.parse_args()

    root = repo_root()
    version = args.version or read_version_from_plugin_cfg(root)

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
    else:
        output_path = root / DEFAULT_OUTPUT_DIR / f"godot-spacetime-v{version}.zip"

    package_release(root, version, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Exact Content: `addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt`

```
SpacetimeDB.ClientSDK
https://github.com/clockworklabs/SpacetimeDB

This package includes a dependency on SpacetimeDB.ClientSDK by Clockwork Labs.
For license and attribution terms, see:
https://github.com/clockworklabs/SpacetimeDB/blob/master/LICENSE
```

### `.gitignore` Addition (append to root `.gitignore`)

After the `.NET` build outputs section, add:
```
# Release candidate archives (produced by scripts/packaging/package-release.py)
release-candidates/
```

### Project Structure After Story 6.2

```
scripts/
├── codegen/
│   └── generate-smoke-test.sh          ← unchanged
├── compatibility/
│   ├── validate-foundation.py          ← unchanged
│   └── support-baseline.json           ← unchanged
└── packaging/                          ← NEW directory
    └── package-release.py              ← NEW

addons/godot_spacetime/
├── plugin.cfg                          ← unchanged (version="0.1.0-dev")
├── GodotSpacetimePlugin.cs             ← unchanged
├── assets/                             ← unchanged
├── src/                                ← unchanged
└── thirdparty/
    └── notices/                        ← NEW directory
        └── spacetimedb-client-sdk.txt  ← NEW

release-candidates/                     ← created on demand; gitignored
```

**Files NOT to touch (modification breaks prior story regression tests):**
- All files under `docs/` — complete
- All files under `addons/godot_spacetime/src/` — SDK public API; no changes
- All files under `demo/` — complete
- All existing test files under `tests/`
- `scripts/compatibility/validate-foundation.py` — do NOT modify
- `scripts/compatibility/support-baseline.json` — do NOT add `scripts/packaging/` here

### Testing Approach

Test file: `tests/test_story_6_2_package_reproducible_versioned_release_candidates.py`

**Full test file structure:**

```python
"""
Tests for Story 6.2: Package Reproducible Versioned Release Candidates

Validates:
- scripts/packaging/package-release.py exists and produces correct output (AC 1, 2)
- addons/godot_spacetime/thirdparty/notices/ exists with SpacetimeDB attribution (AC 3)
- Packaged ZIP excludes demo, tests, spacetime/ and Godot cache files (AC 1)
- Packaged ZIP is versioned and reproducible (AC 2)
- All prior story deliverables remain intact (regression guards)
"""
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
    with tempfile.TemporaryDirectory() as tmpdir:
        # We cannot observe the default path directly without running from repo root,
        # but we can verify the script accepts no --output flag by inspecting its stdout
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
    """Running the packaging script twice with the same version produces identical entry lists."""
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
```

**Test count target: ~55 tests.** The exact count will depend on final naming but the structure above maps 1:1 to test functions.

### Validation Commands

```bash
# Run story-specific tests
pytest -q tests/test_story_6_2_package_reproducible_versioned_release_candidates.py

# Verify packaging script runs standalone
python3 scripts/packaging/package-release.py --version 0.1.0-dev --output /tmp/test-rc.zip
unzip -l /tmp/test-rc.zip | head -20

# Verify exclusions manually
unzip -l /tmp/test-rc.zip | grep -E "\.(uid|import)$" && echo "FAIL: cache files found" || echo "OK: no cache files"
unzip -l /tmp/test-rc.zip | grep "^demo/" && echo "FAIL: demo found" || echo "OK: no demo"

# Full regression suite (must still be 1951+ tests)
pytest -q
```

Expected: story test file passes; `pytest -q` passes with 1951+ tests; no regressions.

### Git Intelligence

- Commit pattern: `feat(story-6.2): Package Reproducible Versioned Release Candidates`
- No `dotnet build` required (no C# changes in this story)
- No modifications to existing test files
- Current test baseline: **1,951 passing** (from Story 6.1 Dev Agent Record)
- Scripts in this project use Python for complex tooling (`validate-foundation.py`) and shell for simple invocations (`generate-smoke-test.sh`); `package-release.py` follows the Python pattern

### References

- Story AC source: `_bmad-output/planning-artifacts/epics.md` § Epic 6, Story 6.2
- NFR12: Release packaging and published artifacts must be complete enough that supported adopters can use the SDK without maintainer intervention [Source: `_bmad-output/planning-artifacts/prd.md`]
- Distribution: GitHub-release-first, distributable ZIPs centered on the `addons/` plugin structure [Source: `_bmad-output/planning-artifacts/architecture.md` § Packaging decisions]
- Only `addons/godot_spacetime/` is distributable; demo and test fixtures never ship [Source: `_bmad-output/planning-artifacts/architecture.md` § Development Workflow Integration]
- Third-party notices location: `addons/godot_spacetime/thirdparty/notices/` [Source: `_bmad-output/planning-artifacts/architecture.md` § Asset Organization]
- `scripts/packaging/` ownership: Release, Compatibility & Maintainer Operations [Source: `_bmad-output/planning-artifacts/architecture.md` § Ownership Map]
- Open question resolved (addon-only ZIP): [Source: `_bmad-output/planning-artifacts/architecture.md` § Gap Analysis Results]
- `plugin.cfg` current version: `0.1.0-dev` [Source: `addons/godot_spacetime/plugin.cfg`]
- Current test baseline: 1,951 passing [Source: Story 6.1 Dev Agent Record]
- `.uid` and `.import` files are Godot project-cache artifacts, not distributable addon files [Source: architecture structure — `*.uid` exists for `GodotSpacetimePlugin.cs.uid` and `*.import` for `assets/icon.svg.import`]
- Previous story: `_bmad-output/implementation-artifacts/6-1-publish-the-canonical-compatibility-matrix-and-support-policy.md`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

One test failure during implementation: `test_version_read_from_plugin_cfg_by_default` expected the version string `0.1.0-dev` in stdout when `--output` is explicitly set. Fixed by adding `print(f"Version: {version}")` to `main()` before calling `package_release()`.

### Completion Notes List

- Implemented `scripts/packaging/package-release.py` — standalone Python 3 packaging script that collects all files under `addons/godot_spacetime/` (sorted, excluding `.uid` and `.import`), writes a reproducible ZIP with fixed timestamps `(2020, 1, 1, 0, 0, 0)`, permissions `0o644 << 16`, and `ZipInfo.create_system = 3`, preserving full `addons/godot_spacetime/` path prefixes and reporting resolved output paths on success.
- Created `addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt` with adopter-facing attribution notice for the `SpacetimeDB.ClientSDK` NuGet dependency (auto-included in ZIP via recursive `addons/` collection).
- Added `release-candidates/` to root `.gitignore` immediately after the `.NET` section as required by Task 1.6.
- Wrote and review-hardened `tests/test_story_6_2_package_reproducible_versioned_release_candidates.py` to 64 tests covering: static existence, functional inclusion/exclusion, versioning, stdout contracts, exact `.gitignore` placement, byte-level reproducibility, ZIP metadata invariants, notice content, and regression guards for all prior stories.
- Full test suite: **2015 passing** (1951 baseline + 64 new). No regressions.
- No C# changes; review fixes were confined to packaging, `.gitignore`, test, and story-tracking artifacts.

### File List

- `scripts/packaging/package-release.py` (new, review-hardened: resolved output path reporting and cross-platform-stable ZIP metadata)
- `addons/godot_spacetime/thirdparty/notices/spacetimedb-client-sdk.txt` (new)
- `.gitignore` (modified — moved `release-candidates/` immediately after the `.NET` section)
- `tests/test_story_6_2_package_reproducible_versioned_release_candidates.py` (new, review-hardened to 64 tests)
- `_bmad-output/implementation-artifacts/6-2-package-reproducible-versioned-release-candidates.md` (story file updates: review notes, metadata, status)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status update: `6-2-package-reproducible-versioned-release-candidates` -> `done`)

### Senior Developer Review (AI)

- Reviewer: Pinkyd on 2026-04-15
- Outcome: Approve
- Story Context: No separate story-context artifact was found; review used the story file, `_bmad-output/planning-artifacts/epics.md`, `_bmad-output/planning-artifacts/architecture.md`, and the changed implementation/test files.
- Epic Tech Spec: No separate epic tech spec artifact was found; `_bmad-output/planning-artifacts/architecture.md` provided the standards and architecture context.
- Tech Stack Reviewed: Python 3 packaging tooling, Godot `4.6.2` addon layout, `pytest` contract tests, Git-tracked story automation artifacts.
- External References: No MCP/web lookup used; repository primary sources were sufficient for this review scope and network access is restricted in this environment.
- Git vs Story Discrepancies: 2 additional non-source automation artifacts were present under `_bmad-output/` during review (`_bmad-output/implementation-artifacts/tests/test-summary-6-2.md`, `_bmad-output/story-automator/orchestration-1-20260414-184146.md`).
- Findings fixed:
  - CRITICAL: `.gitignore` placed `release-candidates/` under the packaging outputs block instead of immediately after the `.NET` section, so Task 1.6 was marked complete while its exact placement requirement was unmet. Fixed by moving the entry and locking that placement in the story suite.
  - HIGH: `scripts/packaging/package-release.py` left `ZipInfo.create_system` implicit, so ZIP headers could vary by maintainer OS even with fixed timestamps and permissions. Fixed by pinning `create_system = 3` for every entry.
  - MEDIUM: `scripts/packaging/package-release.py` did not guarantee a resolved absolute output path in success output for relative `--output` values, even though Task 1.5 requires the resolved output path. Fixed by resolving the output path before packaging and adding a stdout contract test.
  - MEDIUM: `tests/test_story_6_2_package_reproducible_versioned_release_candidates.py` only compared ZIP namelists across repeated runs, so byte-level reproducibility regressions in ZIP metadata could slip past AC 2 coverage. Fixed by asserting matching archive SHA256s across runs.
  - MEDIUM: `tests/test_story_6_2_package_reproducible_versioned_release_candidates.py` only presence-checked `.gitignore` for `release-candidates/`, which let the Task 1.6 placement regression escape.
  - MEDIUM: The story artifact still reported the pre-gap-analysis `52` story tests / `2003` full-suite totals, had no `Senior Developer Review (AI)` section, and sprint tracking still showed `review`. Fixed by rerunning validation, updating the story record, and syncing status to `done`.
- Validation:
  - `pytest -q tests/test_story_6_2_package_reproducible_versioned_release_candidates.py`
  - `pytest -q`
- Notes:
  - No CRITICAL issues remain after fixes.

## Change Log

- 2026-04-15: Story 6.2 implemented — packaging script, thirdparty notice, .gitignore update, and 52-test verification suite added. 2003 tests passing.
- 2026-04-15: Senior Developer Review (AI) — fixed `.gitignore` placement, hardened the release packager's reproducibility/output-path behavior, expanded Story 6.2 coverage to 64 tests, reran validation (`64` story tests, `2015` full-suite tests), and marked the story done.
