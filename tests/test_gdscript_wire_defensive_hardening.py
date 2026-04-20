"""
Runtime coverage for GDScript wire defensive hardening.
"""

from __future__ import annotations

import gzip
import json
import subprocess
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import probe_godot_binary

ROOT = Path(__file__).resolve().parents[1]
EVENT_PREFIX = "WIRE-HARNESS "
HARNESS_TIMEOUT_SECONDS = 40
PARSE_HARNESS_RES = "res://tests/fixtures/gdscript_wire/parse_fixture_harness.gd"
SERVICE_HARNESS_RES = "res://tests/fixtures/gdscript_wire/service_defensive_hardening_harness.gd"


def _require_godot() -> str:
    godot = probe_godot_binary()
    if not godot.available:
        pytest.skip(f"godot-mono not available on PATH: {godot.reason}")
    return godot.path


def _run_harness_process(godot_path: str, harness_res: str, harness_args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            godot_path,
            "--headless",
            "--path",
            str(ROOT),
            "--script",
            harness_res,
            "--",
            *harness_args,
        ],
        capture_output=True,
        timeout=HARNESS_TIMEOUT_SECONDS,
        cwd=str(ROOT),
    )


def _parse_harness_result(proc: subprocess.CompletedProcess[bytes]) -> dict:
    stdout = proc.stdout.decode("utf-8", "replace")
    stderr = proc.stderr.decode("utf-8", "replace")
    for line in stdout.splitlines():
        idx = line.find(EVENT_PREFIX)
        if idx == -1:
            continue
        payload = line[idx + len(EVENT_PREFIX) :].strip()
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            continue
    pytest.fail(
        f"harness did not emit a WIRE-HARNESS result line (exit {proc.returncode}).\n"
        f"stdout tail: {stdout[-800:]}\n"
        f"stderr tail: {stderr[-800:]}"
    )
    raise AssertionError("unreachable")


def _write_unknown_row_size_hint_fixture(tmp_path: Path) -> Path:
    frame = bytearray()
    frame.append(0x00)  # envelope: None
    frame.append(0x04)  # variant: TransactionUpdate
    frame += (1).to_bytes(4, "little")  # query_set_count
    frame += (0).to_bytes(4, "little")  # query_set_id
    frame += (1).to_bytes(4, "little")  # table_count
    frame += (1).to_bytes(4, "little")  # table_name len
    frame += b"A"
    frame += (1).to_bytes(4, "little")  # update_count
    frame.append(0x01)  # table_update_rows variant: EventTable
    frame.append(0x63)  # row_size_hint tag = 99 (unknown)
    fixture_path = tmp_path / "unknown_row_size_hint.bin"
    fixture_path.write_bytes(bytes(frame))
    return fixture_path


def _write_gzip_enveloped_fixture(tmp_path: Path, payload: bytes, name: str) -> Path:
    frame = bytearray()
    frame.append(0x02)  # envelope: Gzip
    frame += gzip.compress(payload, mtime=0)
    fixture_path = tmp_path / name
    fixture_path.write_bytes(bytes(frame))
    return fixture_path


def test_unknown_row_size_hint_returns_protocol_error_without_reader_runtime_errors(tmp_path: Path) -> None:
    godot = _require_godot()
    fixture_path = _write_unknown_row_size_hint_fixture(tmp_path)
    proc = _run_harness_process(godot, PARSE_HARNESS_RES, ["parse_any", str(fixture_path)])
    assert proc.returncode == 0, (
        f"parse harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ProtocolError"
    assert "row size hint" in data["error_message"].lower()
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "BSATN buffer underrun" not in stderr, stderr
    assert "Assertion failed" not in stderr, stderr
    assert "SCRIPT ERROR:" not in stderr, stderr
    assert "Unsupported BSATN row size hint kind Unknown." not in stderr, stderr


def test_transaction_update_non_numeric_query_set_id_does_not_false_match_authoritative_handle() -> None:
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["transaction_update_non_numeric_id"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["applied_query_set_ids"] == []
    assert data["row_changed_events"] == []


def test_reducer_result_non_numeric_query_set_id_is_skipped_but_success_still_emits() -> None:
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reducer_result_non_numeric_id"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["applied_query_set_ids"] == [5]
    assert data["failure_events"] == []
    assert len(data["success_events"]) == 1
    assert data["success_events"][0]["reducer_name"] == "ping"
    assert data["success_events"][0]["invocation_id"] == "inv-7"


def test_parse_decompressed_payload_short_returns_protocol_error() -> None:
    # A Gzip-envelope frame whose decompressed payload is < 1 byte must surface
    # as a ProtocolError BEFORE `BsatnReader.new(payload)` is invoked. Pre-round
    # behaviour: `BsatnReader.read_u8()` on a 0-byte payload hits
    # `_fail → len(int)` and aborts the receive loop instead of producing a
    # routable ProtocolError.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        PARSE_HARNESS_RES,
        ["decompressed_payload_short"],
    )
    assert proc.returncode == 0, (
        f"parse harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ProtocolError"
    assert "Decompressed ServerMessage payload too short" in data["error_message"]
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "BSATN buffer underrun" not in stderr, stderr
    assert "Assertion failed" not in stderr, stderr


def test_parse_decompressed_tag_only_payload_returns_protocol_error(tmp_path: Path) -> None:
    # A compressed payload that decompresses to only the ServerMessage tag byte
    # must be rejected before any typed parser can run. Pre-patch behaviour:
    # the tag routed into `_parse_subscribe_applied`, which hit `read_u32()`
    # underruns and fabricated a bogus zero-valued message.
    godot = _require_godot()
    fixture_path = _write_gzip_enveloped_fixture(
        tmp_path,
        bytes([0x01]),  # SubscribeApplied tag only
        "decompressed_tag_only.bin",
    )
    proc = _run_harness_process(godot, PARSE_HARNESS_RES, ["parse_any", str(fixture_path)])
    assert proc.returncode == 0, (
        f"parse harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ProtocolError"
    assert "payload too short" in data["error_message"]
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "BSATN buffer underrun" not in stderr, stderr
    assert "SCRIPT ERROR" not in stderr, stderr
    assert "decode_u32" not in stderr, stderr


def test_reader_parse_failed_reentry_preserves_state() -> None:
    # Once `parse_failed` is latched, low-level reader helpers must return
    # typed zero/empty defaults without decoding or moving `_pos`.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        PARSE_HARNESS_RES,
        ["reader_parse_failed_reentry"],
    )
    assert proc.returncode == 0, (
        f"parse harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["u8_before_pos"] == 0
    assert data["u8_after_pos"] == 0
    assert data["u8_value"] == 0
    assert data["fixed_before_pos"] == 0
    assert data["fixed_after_pos"] == 0
    assert data["fixed_value_hex"] == ""
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "BSATN buffer underrun" not in stderr, stderr
    assert "SCRIPT ERROR" not in stderr, stderr
    assert "decode_u8" not in stderr, stderr


def test_service_authoritative_negative_query_set_id_returns_early() -> None:
    # A registered authoritative handle whose `query_set_id` is negative must
    # cause `_handle_transaction_update` to return early — no cache mutation,
    # no `row_changed` emission, one `push_warning` naming the defense. This
    # closes the authoritative-side stale-id match hole that the per-entry
    # `qs_id < 0` guard already closed on the bundled side.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["authoritative_negative_query_set_id"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["applied_query_set_ids"] == []
    assert data["row_changed_events"] == []
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "authoritative handle has negative query_set_id" in stderr, (
        f"expected authoritative-side defense warning in stderr. got tail: {stderr[-800:]}"
    )


def test_service_malformed_bundle_emits_single_summary_warning() -> None:
    # Five mixed-malformed entries + one valid entry for the authoritative
    # handle: the post-round behaviour collapses the three data-malformed
    # categories into one summary `push_warning` naming the count. The valid
    # entry still reaches the cache. The previous round's per-entry warning
    # substrings for those three categories must NOT appear in stderr.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["malformed_bundle_warning_storm_cap"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    # The valid entry still applies.
    assert data["applied_query_set_ids"] == [42]
    stderr = proc.stderr.decode("utf-8", "replace")
    # Exactly one summary warning, naming the count 5.
    summary_phrase = "Skipped 5 malformed entries in TransactionUpdate.query_sets"
    assert stderr.count(summary_phrase) == 1, (
        f"expected exactly one summary warning naming count=5; stderr tail: {stderr[-1200:]}"
    )
    # Previous-round per-entry warning substrings must not appear.
    assert "Skipping non-Dictionary TransactionUpdate.query_sets entry" not in stderr, stderr
    assert "Skipping TransactionUpdate.query_sets entry with non-integer query_set_id" not in stderr, stderr
    assert "Skipping TransactionUpdate.query_sets entry with missing/negative query_set_id" not in stderr, stderr


def test_next_request_id_is_monotonic_across_reset() -> None:
    # `_reset_subscription_runtime()` used to reset `_next_request_id` back to
    # `1`, which let a stale SubscribeApplied / ReducerResult still queued in
    # the WebSocket receive buffer from the prior session false-match a freshly
    # reserved id after reconnect. The counter must now be monotonic for the
    # life of the service instance — reserve, reset, reserve again, second id
    # strictly greater than the first.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["request_id_persists_across_reset"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    pre_reset_ids = [int(x) for x in data["pre_reset_ids"]]
    post_reset_id = int(data["post_reset_id"])
    # Pre-reset ids must themselves be monotonic (sanity check on
    # `_reserve_request_id()` itself).
    assert pre_reset_ids == sorted(pre_reset_ids), (
        f"pre_reset_ids must be monotonically increasing, got {pre_reset_ids}"
    )
    # The strict guarantee: post-reset id is greater than the LAST pre-reset
    # id. A re-introduced `_next_request_id = 1` inside
    # `_reset_subscription_runtime()` would produce post_reset_id=2 while
    # pre_reset_ids[-1]=3, which fails this assertion — so the test catches a
    # silent regression that a simple `post_reset_id > pre_reset_ids[0]` would
    # miss (since 2 > 1).
    assert post_reset_id > pre_reset_ids[-1], (
        "_next_request_id must be monotonic across _reset_subscription_runtime(); "
        f"got pre_reset_ids={pre_reset_ids}, post_reset_id={post_reset_id}"
    )


def test_subscribe_applied_rebinds_query_set_id_for_later_bundle_lookups() -> None:
    # The pending subscribe path still correlates by `request_id`, but once the
    # server acknowledges the subscription it may address the live query set by
    # a different `query_set_id`. The applied handler must copy that server id
    # onto the handle before later ReducerResult / TransactionUpdate lookups run
    # through `find_by_query_set_id(...)`.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["subscribe_applied_rebinds_query_set_id"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert int(data["handle_query_set_id"]) == 23
    assert int(data["resolved_handle_id"]) == 1
    assert data["applied_query_set_ids"] == [23]
    assert int(data["authoritative_handle_id"]) == 1
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "SCRIPT ERROR" not in stderr, stderr


def test_service_reducer_result_non_integer_request_id_does_not_crash() -> None:
    # A Dictionary-shaped top-level `request_id` must not crash the handler
    # (via `int(dict)` raising) and must not silently coerce to `0` to
    # false-match a pending-call entry at `request_id == 0`. The handler must
    # push_warning once, return early, and NOT emit success/failure signals.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reducer_result_non_integer_request_id"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    # No reducer signal emitted for the trap-at-zero pending call.
    assert data["success_events"] == []
    assert data["failure_events"] == []
    assert data["row_changed_events"] == []
    # The pending call at request_id=0 must still be held (no silent coercion).
    assert data["pending_still_holds_zero"] is True
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "non-integer request_id" in stderr, (
        f"expected non-integer-request-id warning in stderr. got tail: {stderr[-800:]}"
    )
    # No Godot runtime error from a typed cast on the Dictionary.
    assert "SCRIPT ERROR" not in stderr, stderr
