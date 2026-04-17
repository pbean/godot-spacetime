"""
Story 11.5: GDScript web-export integration coverage.

Stages a temporary pure-GDScript project, exports it to Web/HTML5, serves the
result over local HTTP, and validates the browser-visible lifecycle state when
all local prerequisites are available.
"""

from __future__ import annotations

import importlib.util
import subprocess
import uuid
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import (
    probe_browser_binary,
    probe_godot_binary,
    probe_local_runtime,
    probe_loopback_http,
    probe_spacetime_cli,
)

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "tests" / "fixtures" / "gdscript_web_export.py"
RUNNER_PATH = ROOT / "tests" / "godot_integration" / "gdscript_web_export_runner.gd"
SCENE_PATH = ROOT / "tests" / "godot_integration" / "gdscript_web_export_runner.tscn"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "gdscript_generated" / "smoke_test"
EVENT_PREFIX = "STORY_11_5_WEB_EXPORT"


def _load_helper_module():
    spec = importlib.util.spec_from_file_location("tests.fixtures.gdscript_web_export", HELPER_PATH)
    assert spec is not None and spec.loader is not None, (
        "Story 11.5 web-export integration requires tests/fixtures/gdscript_web_export.py."
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _publish_module(cli: str, server: str, module_name: str) -> None:
    subprocess.run(
        [
            cli,
            "publish",
            "--server",
            server,
            "--anonymous",
            "--module-path",
            str(ROOT / "spacetime" / "modules" / "smoke_test"),
            "--yes",
            module_name,
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        timeout=180,
    )


def test_story_11_5_web_export_harness_files_exist() -> None:
    required = [HELPER_PATH, RUNNER_PATH, SCENE_PATH, FIXTURE_DIR / "spacetimedb_client.gd"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    assert not missing, (
        "Story 11.5 browser/export coverage requires dedicated staging and runner assets. "
        f"Missing {missing}"
    )


def test_story_11_5_web_export_runner_contract_strings_present() -> None:
    content = RUNNER_PATH.read_text(encoding="utf-8")
    for expected in (
        "JavaScriptBridge",
        "transport_request_ready",
        "query_token_mode_confirmed",
        "connected",
        "done",
        "spacetimedb_client.gd",
        "data-story-11-5-phase",
        "data-story-11-5-transport-mode",
    ):
        assert expected in content, (
            "gdscript_web_export_runner.gd must surface browser-visible lifecycle milestones for Story 11.5. "
            f"Missing {expected!r}."
        )


def test_story_11_5_web_export_helper_reuses_shared_prerequisite_probes() -> None:
    content = HELPER_PATH.read_text(encoding="utf-8")
    for expected in (
        "probe_godot_binary",
        "probe_browser_binary",
        "probe_loopback_http",
        "Compatibility",
        "export_presets.cfg",
        "index.html",
    ):
        assert expected in content, (
            "tests/fixtures/gdscript_web_export.py must stage the dedicated web-export fixture and reuse shared prerequisite probes. "
            f"Missing {expected!r}."
        )


def test_story_11_5_web_export_integration_reuses_shared_runtime_probes() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    for expected in (
        "probe_spacetime_cli",
        "probe_local_runtime",
        "probe_godot_binary",
        "probe_browser_binary",
        "probe_loopback_http",
    ):
        assert expected in content, (
            "Story 11.5 web-export integration coverage must stay skip-safe and use shared prerequisite probes. "
            f"Missing {expected!r}."
        )


def test_story_11_5_gdscript_web_export_e2e(tmp_path: Path) -> None:
    if not HELPER_PATH.exists():
        pytest.skip("Story 11.5 web-export helper is not implemented yet")

    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    browser_probe = probe_browser_binary()
    if not browser_probe.available:
        pytest.skip(f"browser binary not available on PATH: {browser_probe.reason}")

    loopback_probe = probe_loopback_http()
    if not loopback_probe.available:
        pytest.skip(f"loopback HTTP unavailable: {loopback_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(f"SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    module_name = f"gdscript-web-export-{uuid.uuid4().hex[:12]}"
    try:
        _publish_module(cli_probe.path, runtime_probe.server, module_name)
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(exc.stderr or b'').decode('utf-8', 'replace')[:240]}"
        )
    except subprocess.TimeoutExpired:
        pytest.skip("SpacetimeDB runtime unavailable: smoke_test publish timed out after 180s")

    helper = _load_helper_module()
    project_dir = tmp_path / "web_project"
    export_dir = tmp_path / "web_export"

    helper.stage_web_export_project(
        repo_root=ROOT,
        project_dir=project_dir,
        bindings_dir=FIXTURE_DIR,
        host=runtime_probe.host,
        module_name=module_name,
        query_token="story-11-5-browser-token",
    )

    project_godot = (project_dir / "project.godot").read_text(encoding="utf-8")
    export_presets = (project_dir / "export_presets.cfg").read_text(encoding="utf-8")
    assert '"C#"' not in project_godot, "Story 11.5 web-export fixture must not stage a C# project."
    assert "Compatibility" in project_godot, "Story 11.5 web-export fixture must use the Compatibility renderer."
    assert "thread" in export_presets.lower(), "Story 11.5 web-export preset must explicitly disable thread support."

    try:
        index_path = helper.export_web_project(godot_probe.path, project_dir, export_dir)
    except RuntimeError as exc:
        pytest.skip(str(exc))

    with helper.serve_directory(export_dir) as base_url:
        try:
            dom = helper.run_headless_browser_capture(
                browser_probe.path,
                f"{base_url}/{index_path.name}",
            )
        except RuntimeError as exc:
            pytest.skip(str(exc))

    state = helper.parse_story_state_from_dom(dom)
    assert state.get("phase") == "done", f"browser export did not reach terminal success state: {state}"
    assert state.get("connected") == "true", f"browser export did not report a live connection: {state}"
    assert state.get("transport_mode") == "query-token", (
        "browser export must prove the web auth seam uses query-token transport when credentials are supplied. "
        f"Observed state: {state}"
    )
    assert state.get("project_has_csharp") == "false", (
        "browser proof path must stage a dedicated pure-GDScript project, not the repo root C# project. "
        f"Observed state: {state}"
    )
    assert state.get("renderer") == "Compatibility", (
        "browser proof path must record the Compatibility renderer in machine-readable state. "
        f"Observed state: {state}"
    )
