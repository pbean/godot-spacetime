"""
Story 10.1: Multi-Module Connections Integration Test

Publishes the existing smoke_test module twice under distinct database names,
compiles two generated namespaces into the same Godot assembly, and verifies
that two live SpacetimeClient instances stay isolated.
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
SCENE_PATH = "res://tests/godot_integration/multi_module_smoke.tscn"
SCENE = ROOT / "tests/godot_integration/multi_module_smoke.tscn"
RUNNER = ROOT / "tests/godot_integration/MultiModuleSmokeRunner.cs"
FIXTURE_ROOT = ROOT / "tests/fixtures/generated/multi_module_smoke"
EVENT_PREFIX = "E2E-EVENT "
STEP_TIMEOUT_SECONDS = 30
TOTAL_TIMEOUT_SECONDS = 180
REQUIRED_STEPS = (
    "verify_rowreceiver_module_selection",
    "connect_client_a",
    "connect_client_b",
    "lookup_clients",
    "subscribe_client_a",
    "subscribe_client_b",
    "invoke_client_a",
    "observe_client_a",
    "disconnect_client_a",
    "assert_client_b_still_connected",
    "invoke_client_b",
    "observe_client_b",
    "reconnect_client_a",
    "resubscribe_client_a",
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


def test_multi_module_harness_files_exist() -> None:
    assert SCENE.exists(), "multi_module_smoke.tscn missing under tests/godot_integration/"
    assert RUNNER.exists(), "MultiModuleSmokeRunner.cs missing under tests/godot_integration/"
    assert FIXTURE_ROOT.is_dir(), "tests/fixtures/generated/multi_module_smoke/ fixture directory missing"


def test_multi_module_runner_contract_strings_present() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "SPACETIME_E2E_MODULE_A",
        "SPACETIME_E2E_MODULE_B",
        "SPACETIME_E2E_VALUE_A",
        "SPACETIME_E2E_VALUE_B",
        '"verify_rowreceiver_module_selection"',
        '"connect_client_a"',
        '"connect_client_b"',
        '"lookup_clients"',
        '"observe_client_a"',
        '"observe_client_b"',
        "SpacetimeClient.TryGetClient",
        "GeneratedBindingsNamespace",
        "RowReceiver",
        "GetResolvedRemoteTablesTypeNameForInspection",
        "SpacetimeDB.MultiModuleTypes",
    ):
        assert expected in content, (
            "The multi-module smoke runner must encode the two-client contract, namespace split, and lookup surface "
            f"before Story 10.1 can be considered implemented. Missing {expected!r}."
        )


def test_multi_module_runner_fails_loudly_on_contract_violations() -> None:
    content = RUNNER.read_text(encoding="utf-8")
    for expected in (
        "missing required env vars",
        "timed out after",
        "unexpected row receiver binding types",
        "TryGetClient failed to resolve",
        "GetClientOrThrow resolved the wrong client",
        '"cross_talk_count"',
    ):
        assert expected in content, (
            "The multi-module smoke runner must fail loudly when bootstrap, lookup, or isolation contracts break. "
            f"Missing {expected!r} in MultiModuleSmokeRunner.cs."
        )


def test_multi_module_integration_reuses_smoke_test_and_prerequisite_probes() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    for expected in (
        "probe_spacetime_cli",
        "probe_godot_binary",
        "probe_local_runtime",
        'str(ROOT / "spacetime" / "modules" / "smoke_test")',
    ):
        assert expected in content, (
            "Multi-module integration coverage must stay skip-safe and keep reusing the shared smoke_test "
            f"module/runtime probe pattern. Missing {expected!r}."
        )


def test_multi_module_integration_is_independent_and_avoids_hardcoded_waits() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    assert 'module_a = f"smoke-test-multi-a-{uuid.uuid4().hex[:12]}"' in content and 'module_b = f"smoke-test-multi-b-{uuid.uuid4().hex[:12]}"' in content, (
        "Multi-module integration coverage must isolate each run with unique database names so the two-client "
        "runtime assertions remain order-independent."
    )
    assert 'value_a = f"multi-a-{uuid.uuid4().hex[:8]}"' in content and 'value_b = f"multi-b-{uuid.uuid4().hex[:8]}"' in content, (
        "Multi-module integration coverage must isolate each run with unique inserted values per client."
    )
    assert content.count("time.sleep(") == 1, (
        "Multi-module integration coverage must use explicit subprocess and step timeouts instead of hardcoded sleeps."
    )


def test_multi_module_connections_e2e() -> None:
    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(f"SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    module_a = f"smoke-test-multi-a-{uuid.uuid4().hex[:12]}"
    module_b = f"smoke-test-multi-b-{uuid.uuid4().hex[:12]}"
    try:
        _publish_module(cli_probe.path, runtime_probe.server, module_a)
        _publish_module(cli_probe.path, runtime_probe.server, module_b)
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(exc.stderr or b'').decode('utf-8', 'replace')[:240]}"
        )
    except subprocess.TimeoutExpired:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish timed out after 180s"
        )

    value_a = f"multi-a-{uuid.uuid4().hex[:8]}"
    value_b = f"multi-b-{uuid.uuid4().hex[:8]}"

    env = os.environ.copy()
    env["SPACETIME_E2E_HOST"] = runtime_probe.host
    env["SPACETIME_E2E_MODULE_A"] = module_a
    env["SPACETIME_E2E_MODULE_B"] = module_b
    env["SPACETIME_E2E_VALUE_A"] = value_a
    env["SPACETIME_E2E_VALUE_B"] = value_b
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
        f"multi-module harness did not finish within {TOTAL_TIMEOUT_SECONDS}s "
        f"(elapsed={elapsed:.1f}s)"
    )
    assert events, (
        "multi-module runner emitted no events. "
        f"godot exit={proc.returncode}. elapsed={elapsed:.2f}s. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-600:]}"
    )

    step_sequence = [e["name"] for e in events if e.get("event") == "step"]
    assert step_sequence == list(REQUIRED_STEPS), (
        "multi-module harness must emit the full two-client lifecycle in strict order. "
        f"got step_sequence={step_sequence}"
    )

    steps = {e["name"]: e for e in events if e.get("event") == "step"}
    done = next((e for e in events if e.get("event") == "done"), None)

    for step in REQUIRED_STEPS:
        assert step in steps, f"missing step {step!r} in event log: {events}"
        assert steps[step].get("status") == "ok", (
            f"{step} failed: {steps[step].get('reason') or steps[step]}"
        )

    verify_rowreceiver = steps["verify_rowreceiver_module_selection"]
    assert verify_rowreceiver.get("client_a_remote_tables_type") == "SpacetimeDB.Types.RemoteTables"
    assert verify_rowreceiver.get("client_b_remote_tables_type") == "SpacetimeDB.MultiModuleTypes.RemoteTables"
    assert verify_rowreceiver.get("table_names") == ["SmokeTest", "TypedEntity"]

    assert steps["connect_client_a"].get("client_id") == "SpacetimeClient"
    assert steps["connect_client_a"].get("generated_namespace") == "SpacetimeDB.Types"
    assert steps["connect_client_a"].get("database") == module_a

    assert steps["connect_client_b"].get("client_id") == "AnalyticsClient"
    assert steps["connect_client_b"].get("generated_namespace") == "SpacetimeDB.MultiModuleTypes"
    assert steps["connect_client_b"].get("database") == module_b

    assert steps["lookup_clients"].get("resolved_ids") == [
        "SpacetimeClient",
        "AnalyticsClient",
    ], (
        "lookup_clients must prove the public lookup-by-identifier surface resolves both live connections."
    )

    assert steps["subscribe_client_a"].get("synchronized") == ["smoke_test"]
    assert steps["subscribe_client_b"].get("synchronized") == ["smoke_test"]

    observe_a = steps["observe_client_a"]
    assert observe_a.get("value") == value_a
    assert observe_a.get("client_id") == "SpacetimeClient"
    assert observe_a.get("cross_talk_count") == 0
    assert observe_a.get("via") == ["typed_table_handle", "get_rows", "row_changed_event"]

    observe_b = steps["observe_client_b"]
    assert observe_b.get("value") == value_b
    assert observe_b.get("client_id") == "AnalyticsClient"
    assert observe_b.get("cross_talk_count") == 0
    assert observe_b.get("via") == ["typed_table_handle", "get_rows", "row_changed_event"]

    assert steps["assert_client_b_still_connected"].get("state") == "Connected", (
        "disconnecting client A must not tear down client B."
    )
    assert steps["resubscribe_client_a"].get("synchronized") == ["smoke_test"], (
        "client A must be able to reconnect and resubscribe after client B stayed connected."
    )

    assert done is not None, f"multi-module runner did not emit done event. events={events}"
    assert done.get("status") == "pass", (
        f"multi-module runner emitted done status={done.get('status')}, reason={done.get('reason')}"
    )

    assert proc.returncode == 0, (
        f"multi-module runner exited with code {proc.returncode}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-400:]}"
    )
