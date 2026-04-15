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

CANDIDATE_DIR = Path("release-candidates")


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


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_report(report_path: Path) -> dict:
    try:
        with report_path.open(encoding="utf-8") as fh:
            report = json.load(fh)
    except OSError as exc:
        fail(f"Failed to read validation report {report_path}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"Validation report is not valid JSON: {report_path} ({exc})")

    if not isinstance(report, dict):
        fail(f"Validation report root must be a JSON object: {report_path}")

    return report


def resolve_candidate_path(root: Path, candidate_value: object) -> Path:
    if not isinstance(candidate_value, str) or not candidate_value.strip():
        fail("Validation report is missing a candidate ZIP path.")

    candidate_rel = Path(candidate_value)
    if candidate_rel.is_absolute():
        fail(f"Candidate path must be relative to the repository root: {candidate_value}")

    candidate_path = (root / candidate_rel).resolve()
    allowed_root = (root / CANDIDATE_DIR).resolve()
    try:
        candidate_path.relative_to(allowed_root)
    except ValueError:
        fail(f"Candidate path must stay within {CANDIDATE_DIR.as_posix()}/: {candidate_value}")

    if candidate_path.suffix.lower() != ".zip":
        fail(f"Candidate path must point to a ZIP artifact: {candidate_value}")

    return candidate_path


def read_current_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        fail(f"Failed to resolve current commit for release tag target: {detail}")

    return result.stdout.strip()


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
    report = load_report(report_path)

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
    candidate_path = resolve_candidate_path(root, report.get("candidate"))
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
        "--target", read_current_commit(root),
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
