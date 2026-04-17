"""
Helpers for Story 11.5's pure-GDScript web export proof path.

This module stages a temporary exportable project, exports it with Godot's Web
preset, serves the files over loopback HTTP, and captures browser-visible DOM
state from a Chromium-family browser.
"""

from __future__ import annotations

import contextlib
import functools
import http.server
import os
import re
import shutil
import socketserver
import subprocess
import threading
from pathlib import Path

from tests.fixtures.spacetime_runtime import (
    probe_browser_binary,
    probe_godot_binary,
    probe_loopback_http,
)

PROJECT_TEMPLATE = """; Engine configuration file.
config_version=5

[application]

config/name="story-11-5-web-export"
config/features=PackedStringArray("4.6", "Compatibility")
run/main_scene="res://tests/godot_integration/gdscript_web_export_runner.tscn"

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
"""

EXPORT_PRESETS_TEMPLATE = """[preset.0]
name="Web"
platform="Web"
runnable=true
advanced_options=false
dedicated_server=false

[preset.0.options]
custom_template/debug=""
custom_template/release=""
variant/thread_support=0
threads/thread_support=0
html/export_icon=false
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
progressive_web_app/enabled=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
"""

CONFIG_TEMPLATE = """extends RefCounted

const HOST = {host}
const MODULE_NAME = {module_name}
const QUERY_TOKEN = {query_token}
const RENDERER_LABEL = "Compatibility"
"""


def probe_story_11_5_web_export_prereqs() -> dict[str, object]:
    """Return discovery-only prerequisite probes for Story 11.5."""
    godot = probe_godot_binary()
    browser = probe_browser_binary()
    loopback = probe_loopback_http()
    return {
        "godot": godot,
        "browser": browser,
        "loopback_http": loopback,
    }


def stage_web_export_project(
    *,
    repo_root: Path,
    project_dir: Path,
    bindings_dir: Path,
    host: str,
    module_name: str,
    query_token: str,
) -> dict[str, Path]:
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    runtime_source = repo_root / "addons" / "godot_spacetime" / "src" / "Internal" / "Platform" / "GDScript"
    if not runtime_source.is_dir():
        raise RuntimeError(f"Missing GDScript runtime source at {runtime_source}")
    shutil.copytree(
        runtime_source,
        project_dir / "addons" / "godot_spacetime" / "src" / "Internal" / "Platform" / "GDScript",
        dirs_exist_ok=True,
    )

    shutil.copytree(
        bindings_dir,
        project_dir / "tests" / "fixtures" / "gdscript_generated" / "smoke_test",
        dirs_exist_ok=True,
    )

    integration_dir = project_dir / "tests" / "godot_integration"
    integration_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        repo_root / "tests" / "godot_integration" / "gdscript_web_export_runner.gd",
        integration_dir / "gdscript_web_export_runner.gd",
    )
    shutil.copy2(
        repo_root / "tests" / "godot_integration" / "gdscript_web_export_runner.tscn",
        integration_dir / "gdscript_web_export_runner.tscn",
    )
    (integration_dir / "story_11_5_web_config.gd").write_text(
        CONFIG_TEMPLATE.format(
            host=_gd_string(host),
            module_name=_gd_string(module_name),
            query_token=_gd_string(query_token),
        ),
        encoding="utf-8",
    )

    (project_dir / "project.godot").write_text(PROJECT_TEMPLATE, encoding="utf-8")
    (project_dir / "export_presets.cfg").write_text(EXPORT_PRESETS_TEMPLATE, encoding="utf-8")

    return {
        "project_dir": project_dir,
        "project_file": project_dir / "project.godot",
        "export_presets": project_dir / "export_presets.cfg",
        "config_file": integration_dir / "story_11_5_web_config.gd",
    }


def export_web_project(godot_path: str, project_dir: Path, export_dir: Path) -> Path:
    prereqs = probe_story_11_5_web_export_prereqs()
    if not prereqs["godot"].available:
        raise RuntimeError(f"Godot web export unavailable: {prereqs['godot'].reason}")

    if export_dir.exists():
        shutil.rmtree(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    index_path = export_dir / "index.html"
    result = subprocess.run(
        [
            godot_path,
            "--headless",
            "--path",
            str(project_dir),
            "--export-debug",
            "Web",
            str(index_path),
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        combined = "\n".join(part for part in (result.stdout, result.stderr) if part).lower()
        if "template" in combined or "export template" in combined:
            raise RuntimeError(
                "Godot web export templates unavailable for Story 11.5: "
                f"{(result.stderr or result.stdout).strip()[:400]}"
            )
        raise RuntimeError(
            "Godot web export failed for Story 11.5: "
            f"{(result.stderr or result.stdout).strip()[:400]}"
        )
    if not index_path.exists():
        raise RuntimeError("Godot web export reported success, but index.html was not produced")
    return index_path


@contextlib.contextmanager
def serve_directory(directory: Path):
    if not probe_loopback_http().available:
        raise RuntimeError("Loopback HTTP unavailable for Story 11.5 browser validation")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))

    class _ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    httpd = _ThreadingServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = httpd.server_address
        yield f"http://{host}:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def run_headless_browser_capture(browser_path: str, url: str) -> str:
    prereqs = probe_story_11_5_web_export_prereqs()
    if not prereqs["browser"].available:
        raise RuntimeError(f"Browser unavailable for Story 11.5: {prereqs['browser'].reason}")

    result = subprocess.run(
        [
            browser_path,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=30000",
            "--dump-dom",
            url,
        ],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Headless browser validation failed for Story 11.5: "
            f"{(result.stderr or result.stdout).strip()[:400]}"
        )
    return result.stdout


def parse_story_state_from_dom(dom: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in re.findall(r'data-story-11-5-([a-z\\-]+)="([^"]*)"', dom):
        values[key.replace("-", "_")] = value
    return values


def _gd_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
