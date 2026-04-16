"""
Story 7.4: One-Off Query Integration Test

End-to-end integration test that drives the Godot-hosted SpacetimeClient facade
through connect -> invoke-reducer -> one-off-query against a real SpacetimeDB runtime
without ever applying a subscription for smoke_test.

Outcomes:
- PASS: runtime reachable, one-off query returns typed rows while cache paths stay empty
- SKIP: a prerequisite is missing (spacetime CLI, reachable runtime, godot-mono)
- FAIL: runtime reachable but any contract assertion fails
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import (
    probe_godot_binary,
    probe_local_runtime,
    probe_spacetime_cli,
)

ROOT = Path(__file__).resolve().parents[1]
SCENE_PATH = "res://tests/godot_integration/one_off_query_smoke.tscn"
REQUIRED_STEPS = ("connect", "invoke_reducer", "query", "validation_faults", "negative_query")
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


def test_one_off_query_e2e_without_subscription() -> None:
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

    module_name = f"smoke-test-query-{uuid.uuid4().hex[:12]}"
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

    e2e_value = f"one-off-{uuid.uuid4().hex[:8]}"

    env = os.environ.copy()
    env["SPACETIME_E2E_HOST"] = runtime_probe.host
    env["SPACETIME_E2E_MODULE"] = module_name
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
        f"one-off query harness did not finish within {TOTAL_TIMEOUT_SECONDS}s "
        f"(elapsed={elapsed:.1f}s)"
    )

    assert events, (
        "one-off query runner emitted no events. "
        f"godot exit={proc.returncode}. elapsed={elapsed:.2f}s. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-600:]}"
    )

    step_events = {e["name"]: e for e in events if e.get("event") == "step"}
    done_event = next((e for e in events if e.get("event") == "done"), None)

    for step in REQUIRED_STEPS:
        assert step in step_events, (
            f"{step} step missing from one-off query event log. got steps="
            f"{list(step_events.keys())}, done={done_event}"
        )
        assert step_events[step].get("status") == "ok", (
            f"{step} step failed: "
            f"{step_events[step].get('reason') or step_events[step]}"
        )

    connect = step_events["connect"]
    assert connect.get("cache_rows") == 0 and connect.get("cache_count") == 0, (
        "connect step must prove GetRows('SmokeTest') and GetDb<RemoteTables>().SmokeTest.Count "
        f"are both zero before any one-off query. got {connect}"
    )

    query = step_events["query"]
    assert query.get("value") == e2e_value and query.get("returned_count") == 1, (
        f"query step must return exactly one typed SmokeTest row with value={e2e_value!r}. got {query}"
    )
    assert query.get("cache_rows_before") == 0 and query.get("cache_count_before") == 0, (
        f"query step must start with an empty cache. got {query}"
    )
    assert query.get("cache_rows_after") == 0 and query.get("cache_count_after") == 0, (
        f"query step must leave GetRows/db.Count unchanged after the one-off query. got {query}"
    )
    assert query.get("observed_via") == ["query_async"], (
        "query step must observe the result through QueryAsync only, not SubscriptionApplied or RowChanged. "
        f"got observed_via={query.get('observed_via')}"
    )

    validation = step_events["validation_faults"]
    assert validation.get("blank_sql_exception") == "ArgumentException", (
        "Blank SQL must remain an explicit ArgumentException programming fault instead of becoming a typed runtime query error. "
        f"got {validation}"
    )
    assert validation.get("unsupported_row_type_exception") == "InvalidOperationException", (
        "Unsupported row types must remain an explicit InvalidOperationException programming fault. "
        f"got {validation}"
    )
    assert validation.get("cache_rows_after") == 0 and validation.get("cache_count_after") == 0, (
        f"Programming-fault validation checks must also leave the cache untouched. got {validation}"
    )

    negative = step_events["negative_query"]
    assert negative.get("failure_category") == "InvalidQuery", (
        f"negative query must map invalid SQL to OneOffQueryFailureCategory.InvalidQuery. got {negative}"
    )
    assert negative.get("target_table") == "smoke_test", (
        f"negative query must expose the target table identity. got {negative}"
    )
    assert negative.get("requested_row_type") == "SpacetimeDB.Types.SmokeTest", (
        f"negative query must expose the requested row type. got {negative}"
    )
    assert negative.get("exception_type") == "GodotSpacetime.Queries.OneOffQueryError", (
        f"negative query must surface the typed OneOffQueryError recoverable failure model. got {negative}"
    )
    assert negative.get("sql_clause") == "WHERE value =", (
        f"negative query must preserve the failing SQL clause on the typed error payload. got {negative}"
    )
    assert negative.get("error_message"), (
        f"negative query must expose a human-readable error message. got {negative}"
    )
    assert negative.get("recovery_guidance") and "Fix the SQL clause" in negative["recovery_guidance"], (
        f"negative query must expose actionable recovery guidance for InvalidQuery failures. got {negative}"
    )
    assert negative.get("cache_rows_after") == 0 and negative.get("cache_count_after") == 0, (
        f"negative query must also leave the cache untouched. got {negative}"
    )

    requested_at = negative.get("requested_at_utc")
    failed_at = negative.get("failed_at_utc")
    assert requested_at and failed_at, (
        f"negative query must expose UTC requested/failed timestamps. got {negative}"
    )

    requested_at_dt = _parse_utc_timestamp(requested_at)
    failed_at_dt = _parse_utc_timestamp(failed_at)
    assert requested_at_dt.utcoffset() == timedelta(0), (
        f"requested_at_utc must be UTC. got {requested_at}"
    )
    assert failed_at_dt.utcoffset() == timedelta(0), (
        f"failed_at_utc must be UTC. got {failed_at}"
    )
    assert failed_at_dt >= requested_at_dt, (
        f"failed_at_utc must be on or after requested_at_utc. got requested={requested_at}, failed={failed_at}"
    )

    assert done_event is not None, (
        f"one-off query runner did not emit done event. events={events}"
    )
    assert done_event.get("status") == "pass", (
        f"one-off query runner emitted done status={done_event.get('status')}, "
        f"reason={done_event.get('reason')}"
    )

    assert proc.returncode == 0, (
        f"one-off query runner exited with code {proc.returncode}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )


def test_one_off_query_harness_files_exist() -> None:
    scene = ROOT / "tests/godot_integration/one_off_query_smoke.tscn"
    runner = ROOT / "tests/godot_integration/OneOffQuerySmokeRunner.cs"
    assert scene.exists(), (
        "one_off_query_smoke.tscn missing under tests/godot_integration/"
    )
    assert runner.exists(), (
        "OneOffQuerySmokeRunner.cs missing under tests/godot_integration/"
    )


def _parse_utc_timestamp(raw: str) -> datetime:
    return datetime.fromisoformat(raw)
