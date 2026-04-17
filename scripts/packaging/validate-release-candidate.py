#!/usr/bin/env python3
"""
Validate a GodotSpacetime SDK release candidate against the supported workflow.

Usage:
    python3 scripts/packaging/validate-release-candidate.py [--version X.Y.Z] [--report PATH] [--skip-suite]

Defaults:
    --version      Read from addons/godot_spacetime/plugin.cfg
    --report       release-candidates/validation-report-v{version}.json (relative to repo root)
    --skip-suite   Flag: skip pytest suite run — for script self-testing only; must never
                   appear in a release-gate workflow

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
NOTICE_PREFIX = "addons/godot_spacetime/thirdparty/notices/"
EXCLUDED_EXTENSIONS = {".uid", ".import"}
EXCLUDED_PREFIXES = [
    "demo/",
    "tests/",
    "spacetime/",
    "scripts/",
    "_bmad-output/",
    "addons/godot_spacetime/tests/",
]
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


def remove_stale_candidate(candidate_path: Path) -> dict[str, str] | None:
    """Remove an older candidate ZIP so this run cannot validate stale output."""
    if not candidate_path.exists():
        return None

    try:
        candidate_path.unlink()
    except OSError as exc:
        return {
            "status": "fail",
            "detail": f"failed to remove stale candidate ZIP {candidate_path}: {exc}",
        }

    return None


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

    notices = [n for n in names if n.startswith(NOTICE_PREFIX)]
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
        help=(
            "Skip pytest suite run — for script self-testing only; "
            "must never appear in a release-gate workflow"
        ),
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
    stale_candidate_error = remove_stale_candidate(candidate_path)
    if stale_candidate_error is not None:
        checks["package"] = stale_candidate_error
    else:
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
    if checks["package"]["status"] == "pass":
        checks["packaging_checks"] = check_packaging_inline(candidate_path)
    else:
        checks["packaging_checks"] = {
            "status": "fail",
            "detail": (
                "Skipped because package step failed; candidate ZIP from this "
                "validation run is unavailable"
            ),
        }

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
