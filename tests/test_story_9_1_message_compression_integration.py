"""
Story 9.1: Message Compression Integration Test

End-to-end integration coverage that drives the Godot-hosted SpacetimeClient
through connect -> subscribe -> invoke-reducer -> observe-row-change against a
real SpacetimeDB runtime while varying the requested compression mode.

Outcomes:
- PASS: runtime reachable, all lifecycle steps succeed, and the effective
        compression mode reported by ConnectionStatus matches expectations.
- SKIP: a prerequisite is missing (spacetime CLI, reachable runtime, godot-mono).
- FAIL: runtime reachable but any contract assertion fails.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
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
SCENE_PATH = "res://tests/godot_integration/compression_smoke.tscn"
SCENE = ROOT / "tests/godot_integration/compression_smoke.tscn"
RUNNER = ROOT / "tests/godot_integration/CompressionSmokeRunner.cs"
REQUIRED_STEPS = ("connect", "subscribe", "invoke_reducer", "observe_row_change")
STEP_TIMEOUT_SECONDS = 30
TOTAL_TIMEOUT_SECONDS = 120
EVENT_PREFIX = "E2E-EVENT "


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


@pytest.mark.parametrize(
    ("requested_mode", "expected_effective_mode"),
    [
        ("None", "None"),
        ("Gzip", "Gzip"),
        ("Brotli", "Gzip"),
    ],
    ids=("none", "gzip", "brotli"),
)
def test_message_compression_e2e(
    requested_mode: str,
    expected_effective_mode: str,
) -> None:
    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(
            f"SpacetimeDB runtime unavailable: {runtime_probe.reason}"
        )

    module_name = f"smoke-test-compression-{uuid.uuid4().hex[:12]}"
    try:
        _publish_module(cli_probe.path, runtime_probe.server, module_name)
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            f"SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(exc.stderr or b'').decode('utf-8', 'replace')[:200]}"
        )
    except subprocess.TimeoutExpired:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish timed out after 180s"
        )

    e2e_value = f"compression-{requested_mode.lower()}-{uuid.uuid4().hex[:8]}"

    env = os.environ.copy()
    env["SPACETIME_E2E_HOST"] = runtime_probe.host
    env["SPACETIME_E2E_MODULE"] = module_name
    env["SPACETIME_E2E_VALUE"] = e2e_value
    env["SPACETIME_E2E_COMPRESSION"] = requested_mode
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
        f"compression harness did not finish within {TOTAL_TIMEOUT_SECONDS}s "
        f"(elapsed={elapsed:.1f}s)"
    )

    assert events, (
        "compression runner emitted no events. "
        f"godot exit={proc.returncode}. elapsed={elapsed:.2f}s. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-600:]}"
    )

    step_sequence = [e["name"] for e in events if e.get("event") == "step"]
    assert step_sequence == list(REQUIRED_STEPS), (
        "compression harness must emit a single linear step sequence in the expected order. "
        f"got step_sequence={step_sequence}"
    )

    step_events = {e["name"]: e for e in events if e.get("event") == "step"}
    done_event = next((e for e in events if e.get("event") == "done"), None)

    for step in REQUIRED_STEPS:
        assert step in step_events, (
            f"{step} step missing from compression event log. got steps="
            f"{list(step_events.keys())}, done={done_event}"
        )
        assert step_events[step].get("status") == "ok", (
            f"{step} step failed: "
            f"{step_events[step].get('reason') or step_events[step]}"
        )

    connect = step_events["connect"]
    assert connect.get("requested_compression_mode") == requested_mode, (
        f"connect step must record requested compression {requested_mode!r}. got {connect}"
    )
    assert connect.get("effective_compression_mode") == expected_effective_mode, (
        "connect step must surface the effective compression mode from ConnectionStatus. "
        f"got {connect}"
    )
    assert connect.get("description"), (
        f"connect step must include the current status description. got {connect}"
    )

    subscribe = step_events["subscribe"]
    assert subscribe.get("effective_compression_mode") == expected_effective_mode, (
        "subscribe step must preserve the effective compression mode through the active session. "
        f"got {subscribe}"
    )
    assert subscribe.get("synchronized") == ["smoke_test"], (
        f"subscribe step must report the synchronized smoke_test table. got {subscribe}"
    )

    invoke = step_events["invoke_reducer"]
    assert invoke.get("reducer") == "ping_insert", (
        f"invoke_reducer step must use the smoke_test ping_insert reducer. got {invoke}"
    )
    assert invoke.get("effective_compression_mode") == expected_effective_mode, (
        f"invoke_reducer step must preserve effective compression mode. got {invoke}"
    )

    observe = step_events["observe_row_change"]
    channels = observe.get("via") or []
    assert "typed_table_handle" in channels and "get_rows" in channels and "row_changed_event" in channels, (
        "observe_row_change must confirm the inserted row via the typed table-handle path, GetRows, "
        f"and RowChangedEvent. got via={channels}"
    )
    assert observe.get("value") == e2e_value, (
        f"observe_row_change saw value={observe.get('value')!r}, expected {e2e_value!r}"
    )
    assert observe.get("effective_compression_mode") == expected_effective_mode, (
        "observe_row_change must report the effective compression mode observed by the live session. "
        f"got {observe}"
    )

    assert done_event is not None, (
        f"compression runner did not emit done event. events={events}"
    )
    assert done_event.get("status") == "pass", (
        f"compression runner emitted done status={done_event.get('status')}, "
        f"reason={done_event.get('reason')}"
    )

    assert proc.returncode == 0, (
        f"compression runner exited with code {proc.returncode}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )


def test_compression_harness_files_exist() -> None:
    assert SCENE.exists(), "compression_smoke.tscn missing under tests/godot_integration/"
    assert RUNNER.exists(), "CompressionSmokeRunner.cs missing under tests/godot_integration/"


def test_compression_runner_contract_strings_present() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "SPACETIME_E2E_COMPRESSION",
        '"connect"',
        '"subscribe"',
        '"invoke_reducer"',
        '"observe_row_change"',
        '"effective_compression_mode"',
        "ConnectionStatus",
    ):
        assert expected in content, (
            "Compression smoke runner must parameterize compression and emit the required lifecycle payloads "
            f"including {expected!r} (Task 5.2, AC1/AC2/AC4)"
        )


def test_compression_runner_rejects_unknown_requested_mode() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    assert "Unsupported SPACETIME_E2E_COMPRESSION value" in content and "Expected None, Gzip, or Brotli." in content, (
        "Compression smoke runner must fail loudly for unsupported requested modes instead of silently "
        "guessing a compression algorithm (critical error-case coverage)"
    )


def test_compression_integration_reuses_smoke_test_and_prerequisite_probes() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    for expected in (
        "probe_spacetime_cli",
        "probe_godot_binary",
        "probe_local_runtime",
        'str(ROOT / "spacetime" / "modules" / "smoke_test")',
    ):
        assert expected in content, (
            "Compression integration coverage must stay skip-safe and keep reusing the shared smoke_test "
            f"module/runtime probe pattern. Missing {expected!r}"
        )


def test_compression_integration_is_independent_and_avoids_hardcoded_waits() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    assert 'module_name = f"smoke-test-compression-{uuid.uuid4().hex[:12]}"' in content and 'e2e_value = f"compression-{requested_mode.lower()}-{uuid.uuid4().hex[:8]}"' in content, (
        "Compression integration tests must generate unique runtime identities so repeated or parallel runs "
        "do not share mutable state (independence checklist guard)"
    )
    assert re.search(r"(?m)^\s*time\.sleep\(", content) is None, (
        "Compression integration tests must not rely on hardcoded sleeps; use explicit step timeouts and event-driven completion instead"
    )


def test_compression_scene_points_at_runner() -> None:
    content = SCENE.read_text(encoding="utf-8")
    assert "CompressionSmokeRunner.cs" in content, (
        "compression_smoke.tscn must attach CompressionSmokeRunner.cs as the root script"
    )
