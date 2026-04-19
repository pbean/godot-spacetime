"""
Story 11.4: Implement GDScript reducer invocation and result handling

Static seam checks plus parser-frame coverage for the native GDScript reducer lane.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import probe_godot_binary

ROOT = Path(__file__).resolve().parents[1]
GDSCRIPT_DIR = (
    ROOT
    / "addons"
    / "godot_spacetime"
    / "src"
    / "Internal"
    / "Platform"
    / "GDScript"
)

SERVICE_PATH = GDSCRIPT_DIR / "gdscript_connection_service.gd"
PROTOCOL_PATH = GDSCRIPT_DIR / "connection_protocol.gd"
WRITER_PATH = GDSCRIPT_DIR / "bsatn_writer.gd"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "gdscript_generated" / "smoke_test"
FIXTURE_README = FIXTURE_DIR / "README.md"
FIXTURE_REMOTE_REDUCERS = FIXTURE_DIR / "remote_reducers.gd"
FIXTURE_CLIENT = FIXTURE_DIR / "spacetimedb_client.gd"
FIXTURE_TABLES_DIR = FIXTURE_DIR / "Tables"

REDUCER_PARSER_PROBE_PATH = ROOT / "tests" / "godot_integration" / "gdscript_reducer_parser_probe.gd"
REDUCER_PARSER_PROBE_SCENE_PATH = "res://tests/godot_integration/gdscript_reducer_parser_probe.tscn"
EVENT_PREFIX = "E2E-EVENT "
PARSER_PROBE_TIMEOUT_SECONDS = 180


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _service_src() -> str:
    return _read(SERVICE_PATH)


def _protocol_src() -> str:
    return _read(PROTOCOL_PATH)


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


@lru_cache(maxsize=1)
def _run_reducer_parser_probe() -> list[dict]:
    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    if not REDUCER_PARSER_PROBE_PATH.exists():
        pytest.fail(
            "gdscript_reducer_parser_probe.gd missing under tests/godot_integration/"
        )

    with tempfile.TemporaryDirectory(
        prefix="story-11-4-reducer-parser-probe-home-"
    ) as godot_home:
        env = os.environ.copy()
        env["HOME"] = godot_home
        env["XDG_DATA_HOME"] = godot_home
        env["XDG_CONFIG_HOME"] = godot_home
        proc = subprocess.run(
            [
                godot_probe.path,
                "--headless",
                "--path",
                str(ROOT),
                REDUCER_PARSER_PROBE_SCENE_PATH,
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            timeout=PARSER_PROBE_TIMEOUT_SECONDS,
        )
    events = _parse_events_from_stdout(proc.stdout or b"")
    assert proc.returncode == 0, (
        f"reducer parser probe exited with {proc.returncode}. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-800:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-800:]}"
    )
    assert events, (
        "reducer parser probe emitted no events. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-800:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-800:]}"
    )
    return events


# ── Static contract tests ───────────────────────────────────────────────────


def test_story_11_4_protocol_defines_client_call_reducer_constant() -> None:
    content = _protocol_src()
    assert "CLIENT_MESSAGE_CALL_REDUCER" in content, (
        "connection_protocol.gd must define CLIENT_MESSAGE_CALL_REDUCER constant for Story 11.4."
    )
    assert "CLIENT_MESSAGE_CALL_REDUCER := 3" in content, (
        "CLIENT_MESSAGE_CALL_REDUCER must be assigned 3 to match the pinned "
        "SpacetimeDB 2.1.0 ClientMessage variant order "
        "(Subscribe=0, Unsubscribe=1, OneOffQuery=2, CallReducer=3, CallProcedure=4)."
    )


def test_story_11_4_protocol_implements_reducer_result_parser() -> None:
    content = _protocol_src()
    assert "_parse_reducer_result(" in content, (
        "connection_protocol.gd must implement _parse_reducer_result() for Story 11.4."
    )
    assert 'return _raw_message("ReducerResult", tag, payload)' not in content, (
        "Story 11.4 must stop returning raw-payload-only placeholder for ReducerResult (tag 6). "
        "Route to _parse_reducer_result() instead."
    )


def test_story_11_4_service_declares_reducer_signals() -> None:
    content = _service_src()
    for expected in (
        "signal reducer_call_succeeded(event)",
        "signal reducer_call_failed(event)",
    ):
        assert expected in content, (
            f"gdscript_connection_service.gd must declare reducer signals for Story 11.4. Missing {expected!r}."
        )


def test_story_11_4_service_has_invoke_reducer_method() -> None:
    content = _service_src()
    assert "func invoke_reducer(" in content, (
        "gdscript_connection_service.gd must implement invoke_reducer() for Story 11.4."
    )


def test_story_11_4_service_has_pending_invocation_tracking_state() -> None:
    content = _service_src()
    for expected in (
        "_pending_reducer_calls",
        "_next_invocation_id",
    ):
        assert expected in content, (
            "gdscript_connection_service.gd must declare pending invocation tracking state for Story 11.4. "
            f"Missing {expected!r}."
        )


def test_story_11_4_service_has_recovery_guidance_constants() -> None:
    content = _service_src()
    for expected in (
        "REDUCER_RECOVERY_GUIDANCE_FAILED",
        "REDUCER_RECOVERY_GUIDANCE_OUT_OF_ENERGY",
        "REDUCER_RECOVERY_GUIDANCE_UNKNOWN",
        "Check the reducer inputs or server-side rules before retrying",
        "Back off and retry later",
        "Do not retry automatically",
    ):
        assert expected in content, (
            "gdscript_connection_service.gd must declare recovery guidance constants matching the .NET runtime. "
            f"Missing {expected!r}."
        )


def test_story_11_4_service_has_handle_reducer_result_method() -> None:
    content = _service_src()
    assert "_handle_reducer_result(" in content, (
        "gdscript_connection_service.gd must implement _handle_reducer_result() for Story 11.4."
    )


def test_story_11_4_service_routes_reducer_result_in_drain_packets() -> None:
    content = _service_src()
    for expected in (
        '"ReducerResult"',
        "_handle_reducer_result(",
    ):
        assert expected in content, (
            "gdscript_connection_service.gd _drain_packets() must route ReducerResult messages for Story 11.4. "
            f"Missing {expected!r}."
        )


def test_story_11_4_service_protocol_message_still_fires_for_reducer_result() -> None:
    content = _service_src()
    assert 'emit_signal("protocol_message", message.duplicate(true))' in content, (
        "Story 11.4 must preserve protocol_message emission for all messages including ReducerResult. "
        "The Story 11.2 smoke harness and debug tooling depend on this."
    )


def test_story_11_4_service_reset_clears_pending_reducer_state() -> None:
    content = _service_src()
    assert "_pending_reducer_calls.clear()" in content, (
        "gdscript_connection_service.gd _reset_subscription_runtime() must clear _pending_reducer_calls "
        "to prevent stale correlation after reconnect (Story 11.4 AC 4)."
    )
    assert "_next_invocation_id = 1" in content, (
        "gdscript_connection_service.gd _reset_subscription_runtime() must reset _next_invocation_id to 1 "
        "on disconnect (Story 11.4 AC 4)."
    )


def test_story_11_4_retry_teardown_clears_pending_reducer_state() -> None:
    content = _service_src()
    retry_start = content.index("func _schedule_retry_or_disconnect")
    retry_end = content.index("func _finish_disconnect")
    retry_body = content[retry_start:retry_end]
    assert "_reset_pending_reducer_runtime()" in retry_body, (
        "gdscript_connection_service.gd must clear pending reducer state before transport retry/reconnect "
        "so stale reducer invocations do not survive a degraded recovery cycle."
    )


def test_story_11_4_bsatn_writer_has_write_bytes() -> None:
    content = _read(WRITER_PATH)
    assert "func write_bytes(" in content, (
        "bsatn_writer.gd must have write_bytes() method for reducer arg encoding (Story 11.4)."
    )


def test_story_11_4_smoke_harness_files_exist() -> None:
    smoke_gd = ROOT / "tests" / "godot_integration" / "gdscript_reducer_smoke.gd"
    smoke_tscn = ROOT / "tests" / "godot_integration" / "gdscript_reducer_smoke.tscn"
    assert smoke_gd.exists(), "gdscript_reducer_smoke.gd missing under tests/godot_integration/"
    assert smoke_tscn.exists(), "gdscript_reducer_smoke.tscn missing under tests/godot_integration/"


def test_story_11_4_generated_fixture_surface_exists() -> None:
    required = [
        FIXTURE_README,
        FIXTURE_REMOTE_REDUCERS,
        FIXTURE_CLIENT,
        FIXTURE_TABLES_DIR,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    assert not missing, (
        "Story 11.4 regression coverage must keep validating the Story 11.5 generated fixture surface. "
        f"Missing {missing}"
    )
    for path in (FIXTURE_REMOTE_REDUCERS, FIXTURE_CLIENT):
        content = _read(path)
        assert "AUTOMATICALLY GENERATED" in content
        assert "WILL NOT BE SAVED" in content


def test_story_11_4_reducer_parser_probe_exists() -> None:
    assert REDUCER_PARSER_PROBE_PATH.exists(), (
        "Story 11.4 parser-frame coverage requires gdscript_reducer_parser_probe.gd under "
        "tests/godot_integration/."
    )


def test_story_11_4_native_gdscript_lane_avoids_dotnet_leakage() -> None:
    sources: list[str] = []
    for path in (SERVICE_PATH, PROTOCOL_PATH):
        if path.exists():
            sources.append(_read(path))
    haystack = "\n".join(sources)
    for forbidden in (
        "SpacetimeDB.",
        "Internal/Platform/DotNet/",
        "System.Net.WebSockets",
        "ClientWebSocket",
        "accept_stream",
        "WebSocketServer",
    ):
        assert forbidden not in haystack, (
            "Story 11.4 must stay in the native GDScript runtime seam without .NET transport leakage. "
            f"Found forbidden token {forbidden!r}."
        )


# ── Parser-level unit tests with synthesized BSATN frames ──────────────────


def test_story_11_4_reducer_parser_probe_handles_committed_status() -> None:
    events = _run_reducer_parser_probe()
    parsed = {event["name"]: event for event in events if event.get("event") == "parsed"}
    assert "reducer_result_committed" in parsed, (
        "reducer parser probe must emit a parsed event for Committed ReducerResult. "
        f"got events: {[e.get('name') for e in events]}"
    )
    committed = parsed["reducer_result_committed"]
    assert committed.get("kind") == "ReducerResult", (
        f"Committed ReducerResult parse result must have kind=ReducerResult. got {committed}"
    )
    assert committed.get("request_id") == 42, (
        f"Committed ReducerResult must echo request_id=42. got {committed}"
    )
    # Observed spacetime 2.1.0 / v2.bsatn.spacetimedb: the ReducerResult wire
    # does not carry reducer_name; the service correlates through its
    # `_pending_reducer_calls` map keyed on request_id. See capture fixture
    # tests/fixtures/gdscript_wire/reducer_result_recv.bin.
    assert committed.get("reducer_name") == "", (
        f"v2 ReducerResult wire does not include reducer_name. got {committed}"
    )
    assert committed.get("status") == "Committed", (
        f"Committed ReducerResult must have status='Committed'. got {committed}"
    )
    assert committed.get("error_message") == "", (
        f"Committed ReducerResult must have empty error_message. got {committed}"
    )


def test_story_11_4_reducer_parser_probe_handles_failed_status() -> None:
    events = _run_reducer_parser_probe()
    parsed = {event["name"]: event for event in events if event.get("event") == "parsed"}
    assert "reducer_result_failed" in parsed, (
        "reducer parser probe must emit a parsed event for Failed ReducerResult. "
        f"got events: {[e.get('name') for e in events]}"
    )
    failed = parsed["reducer_result_failed"]
    assert failed.get("kind") == "ReducerResult"
    assert failed.get("request_id") == 43
    # v2 ReducerResult wire omits reducer_name — see committed-status test.
    assert failed.get("reducer_name") == ""
    assert failed.get("status") == "Failed"
    assert failed.get("error_message") == "validation error"


def test_story_11_4_reducer_parser_probe_handles_out_of_energy_status() -> None:
    events = _run_reducer_parser_probe()
    parsed = {event["name"]: event for event in events if event.get("event") == "parsed"}
    assert "reducer_result_out_of_energy" in parsed, (
        "reducer parser probe must emit a parsed event for OutOfEnergy ReducerResult. "
        f"got events: {[e.get('name') for e in events]}"
    )
    out_of_energy = parsed["reducer_result_out_of_energy"]
    assert out_of_energy.get("kind") == "ReducerResult"
    assert out_of_energy.get("request_id") == 44
    # v2 ReducerResult wire omits reducer_name.
    assert out_of_energy.get("reducer_name") == ""
    # The v2 SDK's declared ReducerOutcome does not include OutOfEnergy — the
    # probe therefore encodes Err(bytes) and the parser reports status=Failed.
    # The legacy OutOfEnergy classification survives in the service's
    # `_handle_reducer_result` failure_category branch, which the smoke e2e
    # test_story_11_4_gdscript_reducer_smoke_e2e still exercises.
    assert out_of_energy.get("status") == "Failed"


def test_story_11_4_reducer_parser_probe_handles_unknown_status() -> None:
    events = _run_reducer_parser_probe()
    parsed = {event["name"]: event for event in events if event.get("event") == "parsed"}
    assert "reducer_result_unknown_status" in parsed, (
        "reducer parser probe must emit a parsed event for an unrecognised ReducerResult status tag. "
        f"got events: {[e.get('name') for e in events]}"
    )
    unknown = parsed["reducer_result_unknown_status"]
    assert unknown.get("kind") == "ReducerResult", (
        f"Unknown-tag ReducerResult parse result must still have kind=ReducerResult. got {unknown}"
    )
    assert unknown.get("request_id") == 45, (
        f"Unknown-tag ReducerResult must echo request_id=45. got {unknown}"
    )
    # v2 ReducerResult wire omits reducer_name.
    assert unknown.get("reducer_name") == ""
    assert unknown.get("status") == "Unknown", (
        f"Unknown-tag ReducerResult must map to status='Unknown'. got {unknown}"
    )


# ── Service signal payload completeness ────────────────────────────────────


def test_story_11_4_service_handle_reducer_result_emits_failure_category() -> None:
    content = _service_src()
    assert '"failure_category"' in content, (
        "gdscript_connection_service.gd _handle_reducer_result() must include 'failure_category' "
        "in reducer_call_failed event payloads so callers can distinguish Failed/OutOfEnergy/Unknown "
        "without parsing the error_message string."
    )
    for expected_value in ('"Failed"', '"OutOfEnergy"', '"Unknown"'):
        assert expected_value in content, (
            f"gdscript_connection_service.gd must emit failure_category value {expected_value} "
            "in one of the reducer_call_failed branches."
        )


def test_story_11_4_service_handle_reducer_result_emits_recovery_guidance() -> None:
    content = _service_src()
    assert '"recovery_guidance"' in content, (
        "gdscript_connection_service.gd _handle_reducer_result() must include 'recovery_guidance' "
        "in reducer_call_failed event payloads so callers receive actionable remediation text."
    )
    for expected_ref in (
        "REDUCER_RECOVERY_GUIDANCE_FAILED",
        "REDUCER_RECOVERY_GUIDANCE_OUT_OF_ENERGY",
        "REDUCER_RECOVERY_GUIDANCE_UNKNOWN",
    ):
        assert f'"recovery_guidance": {expected_ref}' in content, (
            f"gdscript_connection_service.gd must assign {expected_ref} to the 'recovery_guidance' key "
            "in the corresponding reducer_call_failed branch."
        )


def test_story_11_4_service_invoke_reducer_guard_messages() -> None:
    content = _service_src()
    assert "invoke_reducer() requires an active Connected session." in content, (
        "gdscript_connection_service.gd invoke_reducer() must push_error with "
        "'invoke_reducer() requires an active Connected session.' when called outside Connected state."
    )
    assert "invoke_reducer() requires a non-empty reducer_name." in content, (
        "gdscript_connection_service.gd invoke_reducer() must push_error with "
        "'invoke_reducer() requires a non-empty reducer_name.' to prevent silent no-ops."
    )


def test_story_11_4_service_normalizes_reducer_name_before_dispatch() -> None:
    content = _service_src()
    assert "var clean_reducer_name := reducer_name.strip_edges()" in content, (
        "gdscript_connection_service.gd invoke_reducer() should normalize reducer_name once before "
        "tracking or sending it, so accidental leading/trailing whitespace does not reach the wire."
    )
    # The normalized name must flow into the wire encoder. After the Story
    # G-WIRE-2.1.0-ALIGN refactor the service delegates to the pure static
    # encoder `ConnectionProtocolScript.encode_call_reducer(request_id,
    # clean_reducer_name, args_bytes)` so the wire fixture in
    # tests/fixtures/gdscript_wire/call_reducer_ping_insert_sent.bin can be
    # re-derived from a shim without a socket.
    assert "encode_call_reducer(request_id, clean_reducer_name, args_bytes)" in content, (
        "gdscript_connection_service.gd invoke_reducer() must pass the normalized reducer_name "
        "into ConnectionProtocolScript.encode_call_reducer(...) so the wire fixture stays a "
        "byte-for-byte replay of the pinned 2.1.0 encoding."
    )


def test_story_11_4_service_untracked_result_fallback() -> None:
    content = _service_src()
    assert '"untracked-"' in content or "\"untracked-\"" in content or "'untracked-'" in content, (
        "gdscript_connection_service.gd _handle_reducer_result() must generate a fallback "
        "'untracked-' invocation_id when a ReducerResult arrives with no matching pending call, "
        "so the signal payload is always well-formed."
    )
    assert "_pending_reducer_calls.get(request_id)" in content, (
        "gdscript_connection_service.gd must look up the pending call by request_id before "
        "falling back to the untracked path."
    )
