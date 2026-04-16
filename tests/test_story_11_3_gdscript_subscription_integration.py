"""
Story 11.3: GDScript subscription/cache integration smoke coverage

Runs a headless Godot scene that exercises the native GDScript subscription
lane against a real local SpacetimeDB runtime when available.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import (
    probe_godot_binary,
    probe_local_runtime,
    probe_spacetime_cli,
)

ROOT = Path(__file__).resolve().parents[1]
SCENE_PATH = "res://tests/godot_integration/gdscript_subscription_smoke.tscn"
SCENE = ROOT / "tests" / "godot_integration" / "gdscript_subscription_smoke.tscn"
RUNNER = ROOT / "tests" / "godot_integration" / "gdscript_subscription_smoke.gd"
FIXTURE_REMOTE_TABLES = (
    ROOT / "tests" / "fixtures" / "gdscript_generated" / "smoke_test" / "remote_tables.gd"
)
EVENT_PREFIX = "E2E-EVENT "
STEP_TIMEOUT_SECONDS = 45
TOTAL_TIMEOUT_SECONDS = 240
REQUIRED_STEPS = (
    "connect",
    "subscribe",
    "observe_row_change",
    "replace_success",
    "replace_failure",
)


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


def _parse_events_from_stdout(stdout: bytes) -> list[dict]:
    events: list[dict] = []
    text = stdout.decode("utf-8", errors="replace")
    for raw in text.splitlines():
        stripped = raw.strip()
        idx = stripped.find(EVENT_PREFIX)
        if idx == -1:
            continue
        payload = stripped[idx + len(EVENT_PREFIX):].strip()
        try:
            events.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    return events


def test_story_11_3_smoke_harness_files_exist() -> None:
    assert SCENE.exists(), "gdscript_subscription_smoke.tscn missing under tests/godot_integration/"
    assert RUNNER.exists(), "gdscript_subscription_smoke.gd missing under tests/godot_integration/"
    assert FIXTURE_REMOTE_TABLES.exists(), (
        "remote_tables.gd missing under tests/fixtures/gdscript_generated/smoke_test/"
    )


def test_story_11_3_runner_contract_strings_present() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "SPACETIME_E2E_HOST",
        "SPACETIME_E2E_MODULE",
        "SPACETIME_E2E_SERVER",
        "SPACETIME_E2E_CLI",
        "SPACETIME_E2E_VALUE",
        "SPACETIME_E2E_STEP_TIMEOUT",
        '"connect"',
        '"subscribe"',
        '"observe_row_change"',
        '"replace_success"',
        '"replace_failure"',
        '"subscription_applied"',
        '"subscription_failed"',
        '"row_changed"',
        "replace_subscription",
        "ping_insert",
        EVENT_PREFIX,
    ):
        assert expected in content, (
            "gdscript_subscription_smoke.gd must declare the headless contract and lifecycle payloads for Story 11.3. "
            f"Missing {expected!r}."
        )


def test_story_11_3_runner_uses_native_gdscript_subscription_lane() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "gdscript_connection_service.gd",
        "remote_tables.gd",
        "configure_bindings",
        "get_remote_tables",
        "subscription_applied.connect",
        "subscription_failed.connect",
        "row_changed.connect",
        "JSON.stringify",
    ):
        assert expected in content, (
            "gdscript_subscription_smoke.gd must drive the new native GDScript subscription/cache lane. "
            f"Missing {expected!r}."
        )


def test_story_11_3_integration_reuses_runtime_probes_and_smoke_test_module() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    for expected in (
        "probe_spacetime_cli",
        "probe_godot_binary",
        "probe_local_runtime",
        'str(ROOT / "spacetime" / "modules" / "smoke_test")',
    ):
        assert expected in content, (
            "Story 11.3 integration coverage must stay skip-safe and reuse the shared smoke_test runtime pattern. "
            f"Missing {expected!r}."
        )


def test_story_11_3_gdscript_subscription_smoke_e2e() -> None:
    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(f"SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    module_name = f"gdscript-subscription-smoke-{uuid.uuid4().hex[:12]}"
    try:
        _publish_module(cli_probe.path, runtime_probe.server, module_name)
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(exc.stderr or b'').decode('utf-8', 'replace')[:240]}"
        )
    except subprocess.TimeoutExpired:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish timed out after 180s"
        )

    e2e_value = f"story-11-3-{uuid.uuid4().hex[:8]}"

    with tempfile.TemporaryDirectory(prefix="story-11-3-godot-home-") as godot_home:
        env = os.environ.copy()
        env["HOME"] = godot_home
        env["XDG_DATA_HOME"] = godot_home
        env["XDG_CONFIG_HOME"] = godot_home
        env["SPACETIME_E2E_HOST"] = runtime_probe.host
        env["SPACETIME_E2E_MODULE"] = module_name
        env["SPACETIME_E2E_SERVER"] = runtime_probe.server
        env["SPACETIME_E2E_CLI"] = cli_probe.path
        env["SPACETIME_E2E_VALUE"] = e2e_value
        env["SPACETIME_E2E_STEP_TIMEOUT"] = str(STEP_TIMEOUT_SECONDS)

        start = time.monotonic()
        proc = subprocess.run(
            [
                godot_probe.path,
                "--headless",
                "--path",
                str(ROOT),
                SCENE_PATH,
            ],
            env=env,
            cwd=ROOT,
            capture_output=True,
            timeout=TOTAL_TIMEOUT_SECONDS,
        )
        elapsed = time.monotonic() - start

    events = _parse_events_from_stdout(proc.stdout or b"")
    assert elapsed < TOTAL_TIMEOUT_SECONDS, (
        f"gdscript subscription smoke harness did not finish within {TOTAL_TIMEOUT_SECONDS}s "
        f"(elapsed={elapsed:.1f}s)"
    )
    assert events, (
        "gdscript subscription smoke runner emitted no events. "
        f"godot exit={proc.returncode}. elapsed={elapsed:.2f}s. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-600:]}"
    )

    error_steps = [e for e in events if e.get("event") == "step" and e.get("status") == "error"]
    assert not error_steps, f"gdscript subscription smoke runner reported failing step(s): {error_steps}"

    step_sequence = [e["name"] for e in events if e.get("event") == "step" and e.get("status") == "ok"]
    assert step_sequence == list(REQUIRED_STEPS), (
        "gdscript subscription smoke runner must emit the full Story 11.3 lifecycle in strict order. "
        f"got step_sequence={step_sequence}"
    )

    steps = {e["name"]: e for e in events if e.get("event") == "step" and e.get("status") == "ok"}
    done = next((e for e in events if e.get("event") == "done"), None)
    row_events = [e for e in events if e.get("event") == "row_changed"]
    failed_events = [e for e in events if e.get("event") == "subscription_failed"]

    assert done is not None, f"missing done event in gdscript subscription smoke log: {events}"
    assert done.get("status") == "ok", f"done event reported failure: {done}"

    connect = steps["connect"]
    assert connect.get("state") == "Connected"
    assert connect.get("remote_tables_type") == "smoke_test"

    subscribe = steps["subscribe"]
    assert subscribe.get("table_handle") == "SmokeTest"
    assert subscribe.get("typed_cache_ready") is True
    assert subscribe.get("protocol_kind") == "SubscribeApplied"

    observe = steps["observe_row_change"]
    assert observe.get("value") == e2e_value
    assert observe.get("change_type") == "Insert"
    assert "typed_table_handle" in (observe.get("via") or [])
    assert "row_changed_event" in (observe.get("via") or [])

    replace_success = steps["replace_success"]
    assert replace_success.get("old_status") == "Superseded"
    assert replace_success.get("new_status") == "Active"
    assert replace_success.get("preserved_value") == e2e_value

    replace_failure = steps["replace_failure"]
    assert replace_failure.get("failed_handle_status") == "Closed"
    assert replace_failure.get("authoritative_status") == "Active"
    assert replace_failure.get("preserved_value") == e2e_value
    assert replace_failure.get("error_message"), (
        f"replace_failure step must surface the structured subscription error. got {replace_failure}"
    )

    assert row_events, f"missing row_changed events in gdscript subscription smoke log: {events}"
    assert failed_events, (
        "gdscript subscription smoke runner must surface a structured subscription_failed event "
        f"for the invalid replacement query. got events={events}"
    )

    assert proc.returncode == 0, (
        f"gdscript subscription smoke runner exited with code {proc.returncode}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )
