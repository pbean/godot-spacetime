#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_baseline(root: Path) -> dict:
    baseline_path = root / "scripts/compatibility/support-baseline.json"
    try:
        return json.loads(baseline_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        raise SystemExit(f"{baseline_path}: {exc}") from exc


def run_shared_command(root: Path, label: str, command: list[str]) -> list[str]:
    if not command:
        return [f"support-baseline.json: shared_commands.{label} is missing or empty"]

    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return [f"{label}: failed to start {' '.join(command)} ({exc})"]

    if result.returncode == 0:
        return []

    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part and part.strip()
    )
    detail = f"\n{output}" if output else ""
    return [f"{label}: command failed with exit code {result.returncode}:{detail}"]


def collect_required_path_errors(root: Path, entries: list[dict]) -> list[str]:
    errors: list[str] = []

    for entry in entries:
        rel_path = entry["path"]
        expected_type = entry["type"]
        path = root / rel_path

        if not path.exists():
            errors.append(f"{rel_path}: required {expected_type} is missing")
            continue

        if expected_type == "file" and not path.is_file():
            errors.append(f"{rel_path}: expected file but found different path type")
        elif expected_type == "dir" and not path.is_dir():
            errors.append(f"{rel_path}: expected directory but found different path type")

    return errors


def collect_line_check_errors(root: Path, checks: list[dict], versions: dict) -> list[str]:
    errors: list[str] = []

    for check in checks:
        rel_path = check["file"]
        path = root / rel_path
        if not path.exists():
            errors.append(f"{rel_path}: file missing for check '{check['label']}'")
            continue

        expected_line = check["expected_line"]
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
        matches = [line for line in lines if line == expected_line]

        if not matches:
            errors.append(
                f"{rel_path}: missing exact line for '{check['label']}' -> {expected_line}"
            )
            continue

        if len(matches) > 1 and not check.get("allow_multiple", False):
            errors.append(
                f"{rel_path}: duplicate exact line matches for '{check['label']}' -> {expected_line}"
            )

        version_key = check.get("version_key")
        if version_key:
            version_value = versions.get(version_key)
            if version_value is None:
                errors.append(
                    f"support-baseline.json: support_versions.{version_key} missing for '{check['label']}'"
                )
            elif version_value not in expected_line:
                errors.append(
                    f"support-baseline.json: support_versions.{version_key}='{version_value}' drifts from '{check['label']}' -> {expected_line}"
                )

    return errors


def main() -> int:
    root = repo_root()
    baseline = load_baseline(root)

    errors: list[str] = []
    commands = baseline.get("shared_commands", {})
    errors.extend(run_shared_command(root, "restore", commands.get("restore", [])))
    errors.extend(run_shared_command(root, "build", commands.get("build", [])))

    versions = baseline.get("support_versions", {})
    errors.extend(collect_required_path_errors(root, baseline.get("required_paths", [])))
    errors.extend(collect_line_check_errors(root, baseline.get("line_checks", []), versions))

    if errors:
        print("Foundation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Foundation validation passed.")
    print("Validated support baseline:")
    for key in sorted(versions):
        print(f"- {key}: {versions[key]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
