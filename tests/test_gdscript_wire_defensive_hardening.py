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


def test_parse_corrupt_gzip_envelope_without_magic_bytes_returns_distinct_protocol_error() -> None:
    # A Gzip-envelope frame whose body does NOT start with `1F 8B` must route
    # to the new "Corrupt compressed envelope: missing gzip magic bytes"
    # protocol error, distinct from the "Decompressed ServerMessage payload
    # too short" error reserved for valid-envelope-empty-result cases.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        PARSE_HARNESS_RES,
        ["corrupt_gzip_envelope_no_magic"],
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
    assert "Corrupt compressed envelope: missing gzip magic bytes" in data["error_message"], (
        "corrupt envelope must surface the new distinct protocol error; got "
        f"{data['error_message']!r}"
    )
    # Reserved error string for the valid-envelope-empty-result case must NOT appear.
    assert "Decompressed ServerMessage payload too short" not in data["error_message"], (
        "corrupt envelope must NOT collapse into the valid-envelope-empty error; got "
        f"{data['error_message']!r}"
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "BSATN buffer underrun" not in stderr, stderr
    assert "SCRIPT ERROR" not in stderr, stderr


def test_bundle_truncation_cap_transaction_update_processes_cap_prefix_and_emits_one_summary() -> None:
    # Send MAX_BUNDLED_QUERY_SETS + 100 entries through the TransactionUpdate
    # handler, all matching the authoritative handle. The cap must truncate to
    # exactly the first MAX_BUNDLED_QUERY_SETS entries and emit exactly one
    # summary `push_warning` containing "Clamping" and the overflow count.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["bundle_truncation_cap_transaction_update"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    cap = int(data["cap"])
    overflow = int(data["overflow"])
    total_entries = int(data["total_entries"])
    assert cap > 0 and overflow > 0
    assert total_entries == cap + overflow
    assert int(data["applied_count"]) == cap, (
        "TransactionUpdate handler must process exactly MAX_BUNDLED_QUERY_SETS entries "
        f"under truncation; got applied={data['applied_count']}, cap={cap}"
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    clamping_count = stderr.count("Clamping TransactionUpdate.query_sets")
    assert clamping_count == 1, (
        "truncation must emit exactly one summary warning for the TransactionUpdate "
        f"path; got {clamping_count}. stderr tail: {stderr[-1200:]}"
    )
    assert f"skipped {overflow} additional entries" in stderr, (
        f"truncation summary warning must report the exact skipped-count phrase "
        f"`skipped {overflow} additional entries`; a format-arg swap (e.g. printing "
        f"the cap value in the skipped slot) must fail this test. stderr tail: {stderr[-1200:]}"
    )


def test_bundle_at_cap_processes_all_entries_and_emits_no_truncation_warning() -> None:
    # AC4: at-cap (`bundle_size == MAX_BUNDLED_QUERY_SETS`) must process every
    # entry and NOT emit a truncation summary warning. The gate uses strict
    # `>`, so at-cap is the boundary case that proves the strictness.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["bundle_at_cap_emits_no_warning"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    at_cap = int(data["at_cap"])
    assert at_cap > 0
    assert int(data["applied_count"]) == at_cap, (
        "at-cap bundle must process every entry (bundle_size == cap); "
        f"got applied={data['applied_count']}, cap={at_cap}"
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "Clamping TransactionUpdate.query_sets" not in stderr, (
        "at-cap boundary must NOT emit the truncation summary warning — the gate is "
        f"strict `>`. stderr tail: {stderr[-1200:]}"
    )


def test_bundle_truncation_cap_reducer_result_processes_cap_prefix_and_emits_one_summary() -> None:
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["bundle_truncation_cap_reducer_result"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    cap = int(data["cap"])
    overflow = int(data["overflow"])
    assert int(data["applied_count"]) == cap, (
        "ReducerResult handler must process exactly MAX_BUNDLED_QUERY_SETS entries "
        f"under truncation; got applied={data['applied_count']}, cap={cap}"
    )
    # reducer_call_succeeded must still fire after the truncation.
    assert len(data["success_events"]) == 1
    stderr = proc.stderr.decode("utf-8", "replace")
    clamping_count = stderr.count("Clamping ReducerResult.query_sets")
    assert clamping_count == 1, (
        "truncation must emit exactly one summary warning for the ReducerResult "
        f"path; got {clamping_count}. stderr tail: {stderr[-1200:]}"
    )
    assert f"skipped {overflow} additional entries" in stderr, (
        f"ReducerResult truncation summary must report the exact skipped-count phrase. "
        f"stderr tail: {stderr[-1200:]}"
    )


def test_reserve_request_id_wraps_at_u32_boundary_forces_disconnect() -> None:
    # The monotonic counter hits the u32 wire-encoding boundary (`0xFFFFFFFF`)
    # only after ~4.29 billion reservations. The wrap-guard must push_error
    # AND schedule a retry/disconnect so the wire never sees a wrapped id that
    # could false-match a pending entry from near the counter's start.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reserve_request_id_wraps_forces_disconnect"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    # Returned id is the last valid u32 — wire-valid even though the session
    # is being torn down.
    assert int(data["returned_id"]) == 0xFFFFFFFF
    assert int(data["next_request_id_after"]) == 0x100000000
    # Retry path transitions state to Degraded and disposes the socket.
    assert data["current_state"] == "Degraded", (
        "wrap-guard must route through `_schedule_retry_or_disconnect`, which "
        f"transitions to Degraded; got {data['current_state']}"
    )
    assert bool(data["socket_cleared"]) is True
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "u32 boundary" in stderr, (
        f"wrap-guard must emit a push_error containing 'u32 boundary'. stderr tail: {stderr[-1200:]}"
    )


def test_unsubscribe_null_socket_does_not_burn_request_id() -> None:
    # If `_socket == null` at the moment of unsubscribe (state still reports
    # CONNECTED due to concurrent teardown), the new null-socket check BEFORE
    # `_reserve_request_id()` must keep the counter unchanged. Monotonicity
    # means burned ids accumulate, so this guards against long-lived services
    # prematurely approaching the u32 wrap.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["unsubscribe_null_socket_does_not_burn_request_id"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert int(data["next_request_id_before"]) == int(data["next_request_id_after"]), (
        f"null-socket unsubscribe must NOT burn a request_id; "
        f"before={data['next_request_id_before']} after={data['next_request_id_after']}"
    )
    assert int(data["pending_unsubscribes_size"]) == 0, (
        "null-socket unsubscribe must not populate `_pending_unsubscribes`; "
        f"got size={data['pending_unsubscribes_size']}"
    )


def test_unsubscribe_applied_erases_pending_entry_and_no_ops_on_stale_id() -> None:
    # `_handle_unsubscribe_applied` must look up the reserved request_id in
    # `_pending_unsubscribes` and erase the matching entry. A stale /
    # unmatched request_id (e.g. a frame from a prior session surfaced after
    # reset) must silently no-op.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["unsubscribe_applied_erases_pending_entry"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert int(data["size_after_mismatch"]) == 2
    assert bool(data["still_has_17_after_mismatch"]) is True
    # After the matched request_id + query_set_id frame: size dropped from 2 to
    # 1 (entry 17 erased), entry 42 still present.
    assert int(data["size_after_match"]) == 1
    assert bool(data["still_has_42"]) is True
    # After the stale frame: size unchanged, no error pushed.
    assert int(data["size_after_stale"]) == 1
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "SCRIPT ERROR" not in stderr, stderr
    assert "non-integer request_id" not in stderr, (
        "stale UnsubscribeApplied (integer request_id, just unknown) must not trigger "
        f"the non-integer warning. stderr tail: {stderr[-1200:]}"
    )


def test_unsubscribe_send_failure_does_not_record_pending_entry() -> None:
    # If Godot refuses the outbound packet after a request_id was reserved, the
    # id is burned but must not be recorded as a pending unsubscribe. No server
    # ack can arrive for a packet that was never accepted by the socket.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["unsubscribe_send_failure_does_not_record_pending"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert int(data["next_request_id_after"]) == int(data["next_request_id_before"]) + 1
    assert int(data["pending_unsubscribes_size"]) == 0


def test_reset_subscription_runtime_emits_synthetic_failure_for_pending_subscribes() -> None:
    # On teardown, callers waiting for a terminal event on their in-flight
    # subscribe must observe one. `_reset_subscription_runtime` now emits a
    # synthetic `subscription_failed` event per pending entry BEFORE clearing
    # the map. Pending unsubscribes are cleared silently (Ask First scoped out
    # of this spec).
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reset_subscription_runtime_emits_synthetic_failure"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    events = data["subscription_failed_events"]
    assert len(events) == 1, (
        f"reset with one pending subscribe must emit exactly one subscription_failed; got {len(events)}"
    )
    event = events[0]
    assert int(event["handle_id"]) == 42
    assert "Connection lost before SubscribeApplied" in str(event["error_message"]), (
        f"synthetic failure must cite the connection-lost reason verbatim; got {event['error_message']!r}"
    )
    assert "failed_at_unix_time" in event
    assert data["handle_status_after"] == "Closed"
    # Both pending maps must be empty after reset.
    assert int(data["pending_subscriptions_size_after"]) == 0
    assert int(data["pending_unsubscribes_size_after"]) == 0


def test_reset_subscription_runtime_fails_pending_replacement_old_handle() -> None:
    # When teardown hits mid-replacement, `_reset_subscription_runtime` must emit a
    # synthetic `subscription_failed` for the OLD handle referenced by
    # `_pending_replacements.values()` BEFORE clearing the map — callers tracking the
    # pre-replacement handle across a teardown would otherwise observe asymmetric
    # semantics vs. the server-error path. Old-handle emission fires first, then the
    # new-handle emission from the existing `_pending_subscriptions` iteration.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reset_subscription_runtime_fails_pending_replacement_old_handle"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    events = data["subscription_failed_events"]
    assert len(events) == 2, (
        f"teardown mid-replacement must emit exactly two subscription_failed signals "
        f"(old handle then new handle); got {len(events)}: {events!r}"
    )
    # Old handle fires first.
    assert int(events[0]["handle_id"]) == 42, (
        f"first synthetic failure must name the OLD handle id (42); got {events[0]!r}"
    )
    assert "pre-replacement" in str(events[0]["error_message"]).lower(), (
        f"old-handle payload must distinguish the replacement case; got {events[0]['error_message']!r}"
    )
    assert "failed_at_unix_time" in events[0]
    # New handle fires second via the existing `_pending_subscriptions` loop.
    assert int(events[1]["handle_id"]) == 43, (
        f"second synthetic failure must name the NEW handle id (43); got {events[1]!r}"
    )
    assert "Connection lost before SubscribeApplied" in str(events[1]["error_message"]), (
        f"new-handle payload must match the existing pending-subscribe message; got {events[1]['error_message']!r}"
    )
    # Both handles must be transitioned to Closed.
    assert data["old_handle_status_after"] == "Closed"
    assert data["new_handle_status_after"] == "Closed"
    # Both pending maps cleared.
    assert int(data["pending_subscriptions_size_after"]) == 0
    assert int(data["pending_replacements_size_after"]) == 0


def test_reset_subscription_runtime_handles_missing_old_handle_gracefully() -> None:
    # Edge: `_pending_replacements[43] = 42` but id=42 was already unregistered
    # mid-flight (racing superseded path). The synthetic failure for id=42 still
    # fires and no crash occurs — `try_get_handle` returns null and the emission
    # skips the `close()` call.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reset_subscription_runtime_missing_old_handle_does_not_crash"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    events = data["subscription_failed_events"]
    # Only the old-handle synthetic fires (no pending subscribe for the new handle
    # in this scenario — the `_pending_replacements` entry alone drives emission).
    assert len(events) == 1
    assert int(events[0]["handle_id"]) == 42
    assert int(data["pending_subscriptions_size_after"]) == 0
    assert int(data["pending_replacements_size_after"]) == 0


def test_reset_subscription_runtime_dedupes_duplicate_replacement_old_handles() -> None:
    # Defensive edge: duplicate old-handle ids in `_pending_replacements.values()`
    # must not double-emit a synthetic terminal event.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reset_subscription_runtime_dedupes_duplicate_replacement_old_handles"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    events = data["subscription_failed_events"]
    assert len(events) == 1
    assert int(events[0]["handle_id"]) == 42
    assert data["old_handle_status_after"] == "Closed"
    assert int(data["pending_replacements_size_after"]) == 0


def test_reset_subscription_runtime_reentrant_old_failure_still_fails_new_handle() -> None:
    # A synchronous old-handle failure listener can mutate pending maps by
    # unsubscribing the replacement handle. Reset must still emit the new-handle
    # terminal failure from a pre-emission snapshot.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reset_subscription_runtime_reentrant_old_failure_still_fails_new_handle"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    events = data["subscription_failed_events"]
    assert int(data["reentrant_unsubscribe_count"]) == 1
    assert [int(event["handle_id"]) for event in events] == [42, 43]
    assert data["old_handle_status_after"] == "Closed"
    assert data["new_handle_status_after"] == "Closed"
    assert int(data["pending_subscriptions_size_after"]) == 0
    assert int(data["pending_replacements_size_after"]) == 0


def test_retry_teardown_resets_subscription_runtime_and_fails_pending_subscribe() -> None:
    # Degraded retry creates a new wire session without replaying subscriptions.
    # It must therefore clear old subscription runtime immediately, not wait
    # for retry exhaustion.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["retry_teardown_resets_subscription_runtime"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["current_state"] == "Degraded"
    assert bool(data["socket_cleared"]) is True
    events = data["subscription_failed_events"]
    assert len(events) == 1
    assert int(events[0]["handle_id"]) == 42
    assert data["handle_status_after"] == "Closed"
    assert int(data["pending_subscriptions_size_after"]) == 0
    assert int(data["pending_unsubscribes_size_after"]) == 0


def test_reset_subscription_runtime_shares_single_failed_at_unix_time() -> None:
    # Spec spec-gdscript-wire-teardown-emission-hardening (item 412): a single
    # teardown failing one pending-replacement old handle and one pending subscribe
    # must stamp BOTH synthetic `subscription_failed` events with an IDENTICAL
    # `failed_at_unix_time`. The fix hoists one wall-clock read shared by both
    # emission loops; two independent reads could skew the two events apart.
    #
    # NOTE on what this test does and does NOT prove: the AUTHORITATIVE regression
    # guard for the single-read shape is the static-contract test
    # `test_reset_subscription_runtime_hoists_single_teardown_timestamp` in
    # `tests/test_gdscript_wire_layouts.py` — it pins exactly one
    # `Time.get_unix_time_from_system()` call hoisted into a shared
    # `failed_at_unix_time` local referenced by both payloads. This runtime test
    # only confirms end-to-end that both synthetic emissions propagate the ONE
    # shared value through `emit_signal` -> JSON; it does NOT by itself distinguish
    # a single read from two near-simultaneous reads (which usually tie at the same
    # value). Do not weaken the static-contract test on the strength of this one.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reset_subscription_runtime_shares_single_failed_at_unix_time"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    events = data["subscription_failed_events"]
    assert int(data["event_count"]) == 2, f"expected two emissions, got {data['event_count']}"
    assert len(events) == 2
    # Emission order unchanged: old handle (42) first, new handle (43) second.
    assert [int(event["handle_id"]) for event in events] == [42, 43]
    timestamps = [event["failed_at_unix_time"] for event in events]
    assert timestamps[0] == timestamps[1], (
        "Both synthetic `subscription_failed` events from a single teardown must "
        f"carry an identical `failed_at_unix_time`. Got {timestamps!r}."
    )
    assert float(timestamps[0]) > 0.0, (
        "`failed_at_unix_time` must be a real wall-clock unix time, not zero. "
        f"Got {timestamps[0]!r}."
    )


def test_reset_subscription_runtime_deferred_handler_runs_outside_guard() -> None:
    # spec-gdscript-wire-teardown-deferred-emission: synthetic `subscription_failed`
    # is emitted via `call_deferred`, so a connected handler runs only AFTER the
    # synchronous teardown completes and `_resetting_subscription_runtime` is restored
    # to false. That is what makes a hard-erroring handler unable to wedge the guard —
    # the guard is already cleared before any handler runs. The harness records the
    # guard value seen from inside the deferred handler and runs a SECOND teardown to
    # prove the guard was never wedged.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reset_subscription_runtime_handler_runs_after_guard_cleared"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    # Guard restored synchronously, before any deferred handler runs.
    assert data["guard_immediately_after_first"] is False, (
        "`_resetting_subscription_runtime` must be restored to false synchronously, "
        "before the deferred `subscription_failed` emission fires."
    )
    # The deferred handler observes the guard already cleared — so a handler that
    # hard-errored could not wedge it.
    assert data["guard_seen_inside_handler_first"] is False, (
        "A deferred `subscription_failed` handler must observe "
        "`_resetting_subscription_runtime == false` — proving emission happens outside "
        "the guarded region, so a raising handler cannot wedge the guard."
    )
    # Both teardowns still emit exactly one event — the guard was never wedged.
    assert int(data["first_event_count"]) == 1, data
    assert int(data["second_event_count"]) == 1, (
        "A second teardown must still emit; a wedged guard would early-return and emit "
        f"nothing. Got {data['second_event_count']}."
    )
    assert data["guard_after_second"] is False


def test_subscribe_rejected_while_degraded_adds_no_pending() -> None:
    # Spec spec-gdscript-wire-teardown-emission-hardening (item 413): a
    # synchronous `subscribe()` issued during teardown (state DEGRADED, socket
    # non-null — the retry path) is rejected by the Connected-state gate. It must
    # return null and add NO `_pending_subscriptions` entry, so no re-subscribe
    # packet can leak onto a dying socket.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["subscribe_rejected_while_degraded_adds_no_pending"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["current_state"] == "Degraded"
    assert bool(data["subscribe_returned_null"]) is True, (
        "`subscribe()` while DEGRADED must return null (rejected by the "
        "Connected-state gate)."
    )
    assert int(data["pending_subscriptions_size_before"]) == 0
    assert int(data["pending_subscriptions_size_after"]) == 0, (
        "A rejected `subscribe()` must not add a `_pending_subscriptions` entry."
    )


def test_reentrant_subscribe_during_teardown_is_rejected() -> None:
    # Deferred-emission reentrant flow (originally
    # spec-gdscript-wire-teardown-emission-hardening item 413; emission model updated by
    # spec-gdscript-wire-teardown-deferred-emission): a `subscription_failed` handler that
    # calls `subscribe()` from the DEFERRED emission of a real `_reset_subscription_runtime()`
    # teardown (state DEGRADED, socket non-null — the retry path) must be rejected by the
    # public `subscribe()` Connected-state gate. The reentrant `subscribe()` returns null and
    # leaks NO `_pending_subscriptions` entry, so a re-subscribe packet can never reach the
    # dying socket. Higher fidelity than
    # `test_subscribe_rejected_while_degraded_adds_no_pending`, which exercises a standalone
    # DEGRADED `subscribe()` rather than one issued from a real teardown's deferred handler.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reentrant_subscribe_during_teardown_rejected"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    # Teardown must emit TWO synthetic failures (one pending replacement + one
    # pending subscribe). The two-emission setup is what exercises the handler's
    # one-shot guard — a single emission would leave the disarm path dead.
    assert int(data["emission_count"]) == 2, (
        "teardown must emit two `subscription_failed` events (pending replacement + "
        f"pending subscribe) to exercise the one-shot guard; got {data['emission_count']}."
    )
    # The reentrant path must actually be exercised — otherwise the assertions
    # below would pass vacuously.
    assert data["handler_fired"] is True, (
        "the `subscription_failed` handler must have fired from the deferred emission so "
        "the reentrant `subscribe()` was genuinely attempted."
    )
    # The one-shot `_reentrant_subscribe_armed` guard must hold across BOTH
    # emissions: the handler attempts the re-subscribe exactly once, not once per
    # emitted event. A regression that drops the guard would attempt twice.
    assert int(data["reentrant_subscribe_attempt_count"]) == 1, (
        "the handler's one-shot guard must permit exactly ONE reentrant `subscribe()` "
        "attempt across the two teardown emissions; got "
        f"{data['reentrant_subscribe_attempt_count']}."
    )
    assert data["reentrant_subscribe_returned_null"] is True, (
        "a `subscribe()` issued from a real teardown's deferred `subscription_failed` handler "
        "(state DEGRADED) must be rejected by the Connected-state gate and return null."
    )
    assert int(data["pending_added_by_reentrant_subscribe"]) == 0, (
        "the rejected reentrant `subscribe()` must not leak a `_pending_subscriptions` "
        f"entry; got delta={data['pending_added_by_reentrant_subscribe']}."
    )
    assert data["current_state"] == "Degraded"


def test_reset_subscription_runtime_survives_malformed_pending_entry() -> None:
    # Spec `spec-gdscript-wire-teardown-guard-exception-safety` (item A): the
    # pending-subscribe emission loop in `_reset_subscription_runtime` reads the
    # handle_id off each `_pending_subscriptions` value. A malformed value (a
    # primitive, or an Object without `handle_id`) must be SKIPPED, not allowed to
    # raise — GDScript has no try/finally, so a raise between the guard set-true and
    # the `_resetting_subscription_runtime = false` bookend would leave the guard
    # stuck `true` and turn every later teardown into the entry-guard early return.
    # Pins: (a) valid entries still fail while malformed ones are skipped; (b) the
    # guard is restored after a teardown that hit a malformed entry; (c) a SECOND
    # teardown still emits for a freshly-seeded handle (proving no wedge).
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["reset_subscription_runtime_survives_malformed_pending_entry"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    # (a) The valid handle (id=42) still fails; the primitive and bare-Object
    # entries are skipped rather than raising.
    first_ids = [int(e["handle_id"]) for e in data["first_failed_events"]]
    assert first_ids == [42], (
        "the valid pending handle must still emit `subscription_failed` while the two "
        f"malformed entries are skipped; got handle_ids {first_ids}."
    )
    assert int(data["pending_subscriptions_size_after_first"]) == 0
    # (b) Guard restored — the malformed entry did not bypass the bookend.
    assert data["guard_after_first"] is False, (
        "`_resetting_subscription_runtime` must be restored to false after a teardown "
        "that encountered a malformed pending entry; a stuck guard would wedge all "
        "future teardowns."
    )
    # (c) A second teardown still runs a full emission (not a silent early-return).
    second_ids = [int(e["handle_id"]) for e in data["second_failed_events"]]
    assert second_ids == [99], (
        "a second `_reset_subscription_runtime()` must still emit for a freshly-seeded "
        f"handle (id=99), proving the guard did not wedge; got {second_ids}."
    )
    assert data["guard_after_second"] is False


def test_replace_subscription_rejected_during_disconnect_teardown() -> None:
    # spec-gdscript-wire-teardown-deferred-emission: synthetic `subscription_failed`
    # is emitted DEFERRED, so a handler that calls `replace_subscription()` runs only
    # after the disconnect teardown has fully completed — including `_finish_disconnect`'s
    # DISCONNECTED transition. The handler therefore sees a terminal DISCONNECTED state
    # and is rejected up front by `replace_subscription()`'s own Connected-state gate:
    # it returns null, leaks no pending entry, and sends no frame. (Under the prior
    # synchronous emission the handler ran mid-teardown with state still reading
    # Connected and was instead stopped by `_send_subscribe_request`'s null-socket gate;
    # deferring emission makes the rejection uniform and simpler.)
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["replace_subscription_rejected_during_disconnect_teardown"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    # The reentrant path must actually be exercised, or the assertions pass vacuously.
    assert data["replace_handler_fired"] is True, (
        "the `subscription_failed` handler must have fired from the deferred emission so "
        "`replace_subscription()` was genuinely attempted."
    )
    # State Disconnected confirms the deferred handler runs after the full teardown
    # (including `_finish_disconnect`'s DISCONNECTED transition), so the up-front
    # Connected-state gate is what rejects `replace_subscription()`.
    assert data["current_state"] == "Disconnected", (
        "under deferred emission the handler runs after `_finish_disconnect`'s "
        "DISCONNECTED transition, so the session must read Disconnected."
    )
    assert data["replace_returned_null"] is True, (
        "`replace_subscription()` issued from the deferred handler against a terminal "
        "DISCONNECTED session must be rejected and return null."
    )
    # No transient pending entry survives the teardown.
    assert int(data["pending_subscriptions_size_after"]) == 0
    assert int(data["pending_replacements_size_after"]) == 0
    # The valid pending subscribe (id=43) that drove the handler still emitted.
    failed_ids = [int(e["handle_id"]) for e in data["subscription_failed_events"]]
    assert failed_ids == [43], (
        "the pending subscribe that drove the handler must still emit its synthetic "
        f"failure; got handle_ids {failed_ids}."
    )


def test_replace_subscription_rejected_while_degraded_adds_no_pending() -> None:
    # Spec `spec-gdscript-wire-teardown-guard-exception-safety` I/O matrix
    # (retry-teardown row): a `replace_subscription()` issued while state is DEGRADED is
    # rejected by its own up-front Connected-state gate, returns null, and adds no
    # pending replacement/subscription entry. This is the retry-path counterpart to the
    # disconnect-window test above (state Connected + null socket, rejected deeper in
    # `_send_subscribe_request`) — distinct rejection mechanisms, both pinned.
    godot = _require_godot()
    proc = _run_harness_process(
        godot,
        SERVICE_HARNESS_RES,
        ["replace_subscription_rejected_while_degraded"],
    )
    assert proc.returncode == 0, (
        f"service harness exited with {proc.returncode}.\n"
        f"stdout tail: {proc.stdout.decode('utf-8', 'replace')[-800:]}\n"
        f"stderr tail: {proc.stderr.decode('utf-8', 'replace')[-800:]}"
    )
    result = _parse_harness_result(proc)
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["current_state"] == "Degraded"
    assert data["replace_returned_null"] is True, (
        "`replace_subscription()` while DEGRADED must return null (rejected by its own "
        "Connected-state gate before reaching `_begin_subscription`)."
    )
    assert int(data["pending_subscriptions_size_before"]) == 0
    assert int(data["pending_subscriptions_size_after"]) == 0
    assert int(data["pending_replacements_size_after"]) == 0
