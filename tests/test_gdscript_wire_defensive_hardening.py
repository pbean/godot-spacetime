"""
Runtime coverage for GDScript wire defensive hardening.
"""

from __future__ import annotations

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
