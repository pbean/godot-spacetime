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
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    files = collect_addon_files(root)
    if not files:
        raise SystemExit(f"No distributable files found under {ADDON_DIR}")

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for abs_path in files:
            arc_name = abs_path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(arc_name, date_time=ZIP_ENTRY_TIMESTAMP)
            info.create_system = 3
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

    print(f"Version: {version}")
    package_release(root, version, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
