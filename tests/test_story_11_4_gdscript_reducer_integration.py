"""
Story 11.4: GDScript reducer invocation integration smoke coverage

Runs a headless Godot scene that exercises the native GDScript reducer lane
against a real local SpacetimeDB runtime when available.
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
SCENE_PATH = "res://tests/godot_integration/gdscript_reducer_smoke.tscn"
SCENE = ROOT / "tests" / "godot_integration" / "gdscript_reducer_smoke.tscn"
RUNNER = ROOT / "tests" / "godot_integration" / "gdscript_reducer_smoke.gd"
FIXTURE_CLIENT = (
    ROOT / "tests" / "fixtures" / "gdscript_generated" / "smoke_test" / "spacetimedb_client.gd"
)
EVENT_PREFIX = "E2E-EVENT "
STEP_TIMEOUT_SECONDS = 45
TOTAL_TIMEOUT_SECONDS = 240
REQUIRED_STEPS = (
    "connect",
    "configured_bindings",
    "subscribe",
    "invoke_ping",
    "invoke_ping_insert",
    "fault_guard_passed",
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
        payload = stripped[idx + len(EVENT_PREFIX) :].strip()
        try:
            events.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    return events


def test_story_11_4_smoke_harness_files_exist() -> None:
    assert SCENE.exists(), "gdscript_reducer_smoke.tscn missing under tests/godot_integration/"
    assert RUNNER.exists(), "gdscript_reducer_smoke.gd missing under tests/godot_integration/"
    assert FIXTURE_CLIENT.exists(), (
        "spacetimedb_client.gd missing under tests/fixtures/gdscript_generated/smoke_test/"
    )


def test_story_11_4_runner_contract_strings_present() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "SPACETIME_E2E_HOST",
        "SPACETIME_E2E_MODULE",
        "SPACETIME_E2E_SERVER",
        "SPACETIME_E2E_CLI",
        "SPACETIME_E2E_VALUE",
        "SPACETIME_E2E_STEP_TIMEOUT",
        '"connect"',
        '"configured_bindings"',
        '"subscribe"',
        '"invoke_ping"',
        '"invoke_ping_insert"',
        '"fault_guard_passed"',
        '"reducer_call_succeeded"',
        '"reducer_call_failed"',
        '"returned_empty_invocation_id"',
        "spacetimedb_client.gd",
        "reducers.ping",
        "reducers.ping_insert",
        "contract_count",
        EVENT_PREFIX,
    ):
        assert expected in content, (
            "gdscript_reducer_smoke.gd must declare the headless contract and lifecycle payloads for Story 11.4. "
            f"Missing {expected!r}."
        )


def test_story_11_4_runner_uses_native_gdscript_reducer_lane() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "gdscript_connection_service.gd",
        "spacetimedb_client.gd",
        "configure_bindings",
        "reducer_call_succeeded.connect",
        "reducer_call_failed.connect",
        "JSON.stringify",
    ):
        assert expected in content, (
            "gdscript_reducer_smoke.gd must drive the native GDScript reducer lane. "
            f"Missing {expected!r}."
        )


def test_story_11_4_integration_reuses_runtime_probes_and_smoke_test_module() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    for expected in (
        "probe_spacetime_cli",
        "probe_godot_binary",
        "probe_local_runtime",
        'str(ROOT / "spacetime" / "modules" / "smoke_test")',
    ):
        assert expected in content, (
            "Story 11.4 integration coverage must stay skip-safe and reuse the shared smoke_test runtime pattern. "
            f"Missing {expected!r}."
        )


def test_story_11_4_gdscript_reducer_smoke_e2e() -> None:
    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(f"SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    module_name = f"gdscript-reducer-smoke-{uuid.uuid4().hex[:12]}"
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

    e2e_value = f"story-11-4-{uuid.uuid4().hex[:8]}"

    with tempfile.TemporaryDirectory(prefix="story-11-4-godot-home-") as godot_home:
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
        f"gdscript reducer smoke harness did not finish within {TOTAL_TIMEOUT_SECONDS}s "
        f"(elapsed={elapsed:.1f}s)"
    )
    assert events, (
        "gdscript reducer smoke runner emitted no events. "
        f"godot exit={proc.returncode}. elapsed={elapsed:.2f}s. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-600:]}"
    )

    error_steps = [e for e in events if e.get("event") == "step" and e.get("status") == "error"]
    assert not error_steps, f"gdscript reducer smoke runner reported failing step(s): {error_steps}"

    step_sequence = [
        e["name"] for e in events if e.get("event") == "step" and e.get("status") == "ok"
    ]
    assert step_sequence == list(REQUIRED_STEPS), (
        "gdscript reducer smoke runner must emit the full Story 11.4 lifecycle in strict order. "
        f"got step_sequence={step_sequence}"
    )

    steps = {e["name"]: e for e in events if e.get("event") == "step" and e.get("status") == "ok"}
    done = next((e for e in events if e.get("event") == "done"), None)

    assert done is not None, f"missing done event in gdscript reducer smoke log: {events}"
    assert done.get("status") == "ok", f"done event reported failure: {done}"

    connect = steps["connect"]
    assert connect.get("state") == "Connected"

    configured = steps["configured_bindings"]
    assert configured.get("contract_count") == 2, (
        f"configured_bindings step must report 2 registered table contracts. got {configured}"
    )

    subscribe = steps["subscribe"]
    assert subscribe.get("subscribed") is True

    invoke_ping = steps["invoke_ping"]
    assert invoke_ping.get("reducer_name") == "ping", (
        f"invoke_ping step must report reducer_name='ping'. got {invoke_ping}"
    )
    assert invoke_ping.get("succeeded") is True, (
        f"invoke_ping step must report succeeded=true. got {invoke_ping}"
    )

    invoke_ping_insert = steps["invoke_ping_insert"]
    assert invoke_ping_insert.get("reducer_name") == "ping_insert", (
        f"invoke_ping_insert step must report reducer_name='ping_insert'. got {invoke_ping_insert}"
    )
    assert invoke_ping_insert.get("succeeded") is True
    assert invoke_ping_insert.get("row_observed") is True, (
        f"invoke_ping_insert step must report row_observed=true (row_changed Insert event). "
        f"got {invoke_ping_insert}"
    )

    fault_guard = steps["fault_guard_passed"]
    assert fault_guard.get("guard_triggered") is True, (
        f"fault_guard_passed step must confirm push_error fired for empty reducer name. "
        f"got {fault_guard}"
    )
    assert fault_guard.get("returned_empty_invocation_id") is True, (
        "fault_guard_passed step must prove invoke_reducer() rejected the empty reducer name "
        "synchronously by returning an empty invocation_id."
    )

    assert proc.returncode == 0, (
        f"gdscript reducer smoke runner exited with code {proc.returncode}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )
