"""
Story 7.1: Dynamic Lifecycle Integration Test (D1)

End-to-end integration test that drives the Godot-hosted SpacetimeClient facade
through connect -> subscribe -> invoke-reducer -> observe-row-change against a
real SpacetimeDB runtime. No mocks or fakes for any Internal/Platform/DotNet/
adapter class.

Three outcomes:
- PASS: runtime reachable, all lifecycle steps satisfy their contract assertions.
- SKIP: a prerequisite is missing (spacetime CLI, reachable runtime, godot-mono).
        The skip reason names the specific missing prerequisite.
- FAIL: runtime reachable but a lifecycle step missed its assertion, or timed out.
        The failure message names the first failed step.

The harness contract is declared here before the runner implementation lands
(Task 0 / P1 pattern from the Epic 6 retrospective). The contract assertions
below are the primary artifact of this file; the subprocess wiring is in
service of them.
"""

from __future__ import annotations

import json
import os
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
SCENE_PATH = "res://tests/godot_integration/lifecycle_smoke.tscn"
REQUIRED_STEPS = ("connect", "subscribe", "invoke_reducer", "observe_row_change")
STEP_TIMEOUT_SECONDS = 30
TOTAL_TIMEOUT_SECONDS = 120


def _publish_module(cli: str, server: str, module_name: str) -> None:
    """Publish the smoke_test module under a unique name for this test run.

    Raises subprocess.CalledProcessError on failure — the caller converts this
    into a pytest.skip with a specific reason. A dedicated per-run name keeps
    concurrent CI/dev runs from colliding on the same database identity.
    """
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


EVENT_PREFIX = "E2E-EVENT "


def _parse_events_from_stdout(stdout: bytes) -> list[dict]:
    """Extract JSON-per-line events from the runner's stdout.

    The C# runner emits one `E2E-EVENT <json>` line per step plus a final
    `done` event, interleaved with Godot's own startup/log output. We scan for
    the prefix and parse whatever follows it. stdout is authoritative because
    a file-based log isn't guaranteed to flush before Godot tears down the
    .NET process on `GetTree().Quit()`.
    """
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


def test_dynamic_lifecycle_e2e() -> None:
    """Drive SpacetimeClient through the full lifecycle against a real runtime.

    Contract (per spec-7-1-dynamic-lifecycle-integration-tests.md I/O matrix):
    - emits one `step` event per lifecycle stage in strict order: connect,
      subscribe, invoke_reducer, observe_row_change
    - emits a final `done` event with status `pass`
    - observe_row_change step must record typed_table_handle, get_rows, and
      row_changed_event as observation channels (AC 2: public cache surface,
      not transport)
    - total runtime under 120s
    """

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

    module_name = f"smoke-test-e2e-{uuid.uuid4().hex[:12]}"
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

    e2e_value = f"e2e-smoke-{uuid.uuid4().hex[:8]}"

    env = os.environ.copy()
    env["SPACETIME_E2E_HOST"] = runtime_probe.host
    env["SPACETIME_E2E_MODULE"] = module_name
    env["SPACETIME_E2E_VALUE"] = e2e_value
    env["SPACETIME_E2E_STEP_TIMEOUT"] = str(STEP_TIMEOUT_SECONDS)

    start = time.monotonic()
    # The runner calls GetTree().Quit() itself after emitting a done event,
    # so we do not pass --quit-after — letting Godot exit on its own ensures
    # async _Process iterations complete before teardown. Events are parsed
    # from the runner's stdout rather than a log file because the file writer
    # isn't guaranteed to flush when Godot tears down the .NET process.
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
        f"lifecycle harness did not finish within {TOTAL_TIMEOUT_SECONDS}s "
        f"(elapsed={elapsed:.1f}s)"
    )

    assert events, (
        "lifecycle runner emitted no events. "
        f"godot exit={proc.returncode}. elapsed={elapsed:.2f}s. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-600:]}"
    )

    step_events = {e["name"]: e for e in events if e.get("event") == "step"}
    done_event = next((e for e in events if e.get("event") == "done"), None)

    for step in REQUIRED_STEPS:
        assert step in step_events, (
            f"{step} step missing from lifecycle event log. got steps="
            f"{list(step_events.keys())}, done={done_event}"
        )
        assert step_events[step].get("status") == "ok", (
            f"{step} step failed: "
            f"{step_events[step].get('reason') or step_events[step]}"
        )

    assert done_event is not None, (
        f"lifecycle runner did not emit done event. events={events}"
    )
    assert done_event.get("status") == "pass", (
        f"lifecycle runner emitted done status={done_event.get('status')}, "
        f"reason={done_event.get('reason')}"
    )

    observe = step_events["observe_row_change"]
    channels = observe.get("via") or []
    assert "typed_table_handle" in channels and "get_rows" in channels and "row_changed_event" in channels, (
        "observe_row_change must confirm the inserted row via the typed table-handle path, GetRows, "
        f"and RowChangedEvent (public cache surface, not transport). got via={channels}"
    )
    assert observe.get("value") == e2e_value, (
        f"observe_row_change saw value={observe.get('value')!r}, expected "
        f"{e2e_value!r}"
    )

    assert proc.returncode == 0, (
        f"lifecycle runner exited with code {proc.returncode}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )


def test_dynamic_lifecycle_contract_file_exists() -> None:
    """Static guard: the runner scene + script must be present.

    Distinct from the dynamic test above so a missing harness still produces a
    clear failure under any PATH configuration (not just when runtime is reachable).
    The runner lives under tests/godot_integration/ rather than inside the
    addon directory so that the release ZIP (which excludes tests/) never
    carries the test fixture types — see the spec's Dev Agent Record.
    """
    scene = ROOT / "tests/godot_integration/lifecycle_smoke.tscn"
    runner = ROOT / "tests/godot_integration/LifecycleSmokeRunner.cs"
    assert scene.exists(), (
        "lifecycle_smoke.tscn missing under tests/godot_integration/"
    )
    assert runner.exists(), (
        "LifecycleSmokeRunner.cs missing under tests/godot_integration/"
    )
