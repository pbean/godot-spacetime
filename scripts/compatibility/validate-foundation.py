#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CLI_VERSION_PREFIX = "// This was generated using spacetimedb cli version "
RECOVERY_COMMAND = "bash scripts/codegen/generate-smoke-test.sh"
RELATIVE_MODULE_SOURCE = Path("spacetime/modules/smoke_test")
RELATIVE_GENERATED_CLIENT = Path("demo/generated/smoke_test/SpacetimeDBClient.g.cs")


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


def version_satisfies_baseline(extracted: str, baseline: str) -> bool:
    minimum_parts = baseline.rstrip("+").split(".")
    extracted_parts = extracted.split(".")

    for index, minimum_part in enumerate(minimum_parts):
        try:
            minimum_value = int(minimum_part)
        except ValueError:
            minimum_value = 0

        if index < len(extracted_parts):
            try:
                extracted_value = int(extracted_parts[index])
            except ValueError:
                extracted_value = 0
        else:
            extracted_value = 0

        if extracted_value > minimum_value:
            return True
        if extracted_value < minimum_value:
            return False

    return True


def extract_cli_version(generated_client: Path) -> str | None:
    try:
        lines = generated_client.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return None

    for line in lines:
        if line.startswith(CLI_VERSION_PREFIX):
            parts = line[len(CLI_VERSION_PREFIX):].split()
            return parts[0] if parts else None

    return None


def relevant_module_files(module_root: Path) -> list[Path]:
    files: list[Path] = []

    cargo_toml = module_root / "Cargo.toml"
    if cargo_toml.is_file():
        files.append(cargo_toml)

    src_root = module_root / "src"
    if src_root.is_dir():
        files.extend(sorted(src_root.rglob("*.rs")))

    return files


def collect_binding_compatibility_errors(root: Path, versions: dict) -> list[str]:
    errors: list[str] = []
    module_root = root / RELATIVE_MODULE_SOURCE
    generated_client = root / RELATIVE_GENERATED_CLIENT

    if not module_root.is_dir():
        return errors

    if not generated_client.is_file():
        return [
            f"{RELATIVE_GENERATED_CLIENT.as_posix()}: generated binding registry is missing; run {RECOVERY_COMMAND}"
        ]

    extracted_version = extract_cli_version(generated_client)
    if not extracted_version:
        errors.append(
            f"{RELATIVE_GENERATED_CLIENT.as_posix()}: missing CLI version comment "
            f"'{CLI_VERSION_PREFIX}...'; run {RECOVERY_COMMAND}"
        )
    else:
        baseline = versions.get("spacetimedb")
        if baseline is None:
            errors.append(
                "support-baseline.json: support_versions.spacetimedb missing for binding compatibility checks"
            )
        elif not version_satisfies_baseline(extracted_version, baseline):
            errors.append(
                f"{RELATIVE_GENERATED_CLIENT.as_posix()}: generated binding CLI {extracted_version} "
                f"does not satisfy declared baseline {baseline}; run {RECOVERY_COMMAND}"
            )

    module_files = relevant_module_files(module_root)
    if not module_files:
        return errors

    try:
        newest_source = max(module_files, key=lambda path: path.stat().st_mtime_ns)
        generated_mtime = generated_client.stat().st_mtime_ns
    except OSError as exc:
        errors.append(f"{RELATIVE_GENERATED_CLIENT.as_posix()}: failed to compare source freshness ({exc})")
        return errors

    if newest_source.stat().st_mtime_ns > generated_mtime:
        errors.append(
            f"{RELATIVE_GENERATED_CLIENT.as_posix()}: generated bindings are stale because "
            f"{newest_source.relative_to(root).as_posix()} is newer; run {RECOVERY_COMMAND}"
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
    errors.extend(collect_binding_compatibility_errors(root, versions))

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
