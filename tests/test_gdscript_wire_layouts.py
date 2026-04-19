"""
Byte-exact regression tests for the GDScript wire protocol.

For each client-fixture (Subscribe / CallReducer / Unsubscribe) this test
invokes the GDScript `encode_*` static helper via a Godot-headless harness
and asserts the emitted bytes match the captured `.bin` byte-for-byte.

For each server-fixture (InitialConnection / SubscribeApplied /
UnsubscribeApplied / ReducerResult) the test invokes
`GdscriptConnectionProtocol.parse_server_message` via the same harness and
asserts the structured Dictionary it returns matches a pinned expectation.

The fixtures themselves are produced by
`tests/fixtures/gdscript_wire/capture_wire_fixtures.py` — re-run that script
when `spacetime --version` or `SpacetimeDB.ClientSDK` NuGet changes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import probe_godot_binary

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "gdscript_wire"
HARNESS = FIXTURE_DIR / "parse_fixture_harness.gd"
HARNESS_RES = "res://tests/fixtures/gdscript_wire/parse_fixture_harness.gd"
EVENT_PREFIX = "WIRE-HARNESS "
HARNESS_TIMEOUT_SECONDS = 40


def _require_fixtures() -> Path:
    if not (FIXTURE_DIR / "manifest.json").exists():
        pytest.skip(
            "tests/fixtures/gdscript_wire/manifest.json missing — run "
            "tests/fixtures/gdscript_wire/capture_wire_fixtures.py to regenerate"
        )
    return FIXTURE_DIR


def _require_godot() -> str:
    godot = probe_godot_binary()
    if not godot.available:
        pytest.skip(f"godot-mono not available on PATH: {godot.reason}")
    return godot.path


def _invoke_harness(godot_path: str, harness_args: list[str]) -> dict:
    """Run the Godot headless harness and return the parsed JSON result."""
    cmd = [
        godot_path,
        "--headless",
        "--path",
        str(ROOT),
        "--script",
        HARNESS_RES,
        "++",  # sentinel; forgotten separator — actual user args come after `--`
    ]
    # Godot uses `--` to separate engine args from user script args. Use `++`
    # above as a placeholder marker; below we construct the canonical form.
    cmd = [
        godot_path,
        "--headless",
        "--path",
        str(ROOT),
        "--script",
        HARNESS_RES,
        "--",
        *harness_args,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=HARNESS_TIMEOUT_SECONDS,
            cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(
            f"harness timed out after {HARNESS_TIMEOUT_SECONDS}s: {exc}\n"
            f"cmd: {cmd}"
        )

    stdout = proc.stdout.decode("utf-8", "replace")
    stderr = proc.stderr.decode("utf-8", "replace")
    for line in stdout.splitlines():
        idx = line.find(EVENT_PREFIX)
        if idx == -1:
            continue
        payload = line[idx + len(EVENT_PREFIX):].strip()
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            continue
    pytest.fail(
        f"harness did not emit a WIRE-HARNESS result line (exit {proc.returncode}).\n"
        f"stdout tail: {stdout[-800:]}\n"
        f"stderr tail: {stderr[-400:]}"
    )
    raise AssertionError("unreachable")  # appeases type-checkers


def _load_manifest() -> dict:
    return json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))


def _fixture_path(name: str) -> str:
    path = FIXTURE_DIR / name
    if not path.exists():
        pytest.skip(f"fixture {name} missing — run capture_wire_fixtures.py")
    return str(path)


def _hex_of(path: str) -> str:
    return Path(path).read_bytes().hex().lower()


# ---------------------------------------------------------------------------
# Client-side wire encoders
# ---------------------------------------------------------------------------


def test_harness_file_exists() -> None:
    assert HARNESS.exists(), (
        "tests/fixtures/gdscript_wire/parse_fixture_harness.gd must be present "
        "alongside the capture script."
    )


def test_client_subscribe_encode_matches_fixture() -> None:
    _require_fixtures()
    godot = _require_godot()
    manifest = _load_manifest()
    entry = next(
        (frame for frame in manifest["frames"] if frame["kind"] == "subscribe"),
        None,
    )
    assert entry is not None, "manifest missing subscribe entry"
    expected_hex = _hex_of(_fixture_path(entry["file"]))
    queries_csv = "||".join(entry["queries"])
    result = _invoke_harness(
        godot,
        [
            "encode_subscribe",
            str(entry["request_id"]),
            str(entry["query_set_id"]),
            queries_csv,
        ],
    )
    assert result.get("ok"), f"harness reported error: {result}"
    got_hex = result["data"]["hex"].lower()
    assert got_hex == expected_hex, (
        "Subscribe wire bytes drifted from the pinned fixture. "
        f"expected={expected_hex}, got={got_hex}"
    )


def test_client_unsubscribe_encode_matches_fixture() -> None:
    _require_fixtures()
    godot = _require_godot()
    manifest = _load_manifest()
    entry = next(
        (frame for frame in manifest["frames"] if frame["kind"] == "unsubscribe"),
        None,
    )
    assert entry is not None, "manifest missing unsubscribe entry"
    expected_hex = _hex_of(_fixture_path(entry["file"]))
    result = _invoke_harness(
        godot,
        [
            "encode_unsubscribe",
            str(entry["request_id"]),
            str(entry["query_set_id"]),
            "0",  # Flags default
        ],
    )
    assert result.get("ok"), f"harness reported error: {result}"
    got_hex = result["data"]["hex"].lower()
    assert got_hex == expected_hex, (
        "Unsubscribe wire bytes drifted from the pinned fixture. "
        f"expected={expected_hex}, got={got_hex}"
    )


def test_client_call_reducer_encode_matches_fixture() -> None:
    _require_fixtures()
    godot = _require_godot()
    manifest = _load_manifest()
    entry = next(
        (frame for frame in manifest["frames"] if frame["kind"] == "call_reducer_ping_insert"),
        None,
    )
    assert entry is not None, "manifest missing call_reducer_ping_insert entry"
    expected_hex = _hex_of(_fixture_path(entry["file"]))
    args_value: str = entry["args_value"]
    args_utf8 = args_value.encode("utf-8")
    args_len_u32 = len(args_utf8).to_bytes(4, "little")
    args_bsatn = (args_len_u32 + args_utf8).hex()
    result = _invoke_harness(
        godot,
        [
            "encode_call_reducer",
            str(entry["request_id"]),
            entry["reducer_name"],
            args_bsatn,
        ],
    )
    assert result.get("ok"), f"harness reported error: {result}"
    got_hex = result["data"]["hex"].lower()
    assert got_hex == expected_hex, (
        "CallReducer wire bytes drifted from the pinned fixture. "
        f"expected={expected_hex}, got={got_hex}"
    )


# ---------------------------------------------------------------------------
# Server-side wire parsers
# ---------------------------------------------------------------------------


def test_server_initial_connection_parse_matches_fixture() -> None:
    _require_fixtures()
    godot = _require_godot()
    manifest = _load_manifest()
    entry = next(
        (frame for frame in manifest["frames"] if frame["kind"] == "initial_connection"),
        None,
    )
    assert entry is not None, "manifest missing initial_connection entry"
    fixture = _fixture_path(entry["file"])
    result = _invoke_harness(godot, ["parse_initial_connection", fixture])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "InitialConnection"
    assert data["tag"] == 0
    assert isinstance(data["identity"], str) and len(data["identity"]) == 64
    assert isinstance(data["connection_id"], str) and len(data["connection_id"]) == 32
    token = str(data["token"])
    assert token.startswith("eyJ"), f"expected JWT-shaped token, got {token[:32]!r}"
    assert token.count(".") == 2, "JWT must have three dot-separated segments"


def test_server_subscribe_applied_parse_matches_fixture() -> None:
    _require_fixtures()
    godot = _require_godot()
    manifest = _load_manifest()
    entry = next(
        (frame for frame in manifest["frames"] if frame["kind"] == "subscribe_applied"),
        None,
    )
    assert entry is not None, "manifest missing subscribe_applied entry"
    fixture = _fixture_path(entry["file"])
    result = _invoke_harness(godot, ["parse_subscribe_applied", fixture])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "SubscribeApplied"
    assert data["tag"] == 1
    assert int(data["request_id"]) == entry["request_id"]
    assert int(data["query_set_id"]) == entry["query_set_id"]
    assert isinstance(data["tables"], list), "tables must be a list"


def test_server_unsubscribe_applied_parse_matches_fixture() -> None:
    _require_fixtures()
    godot = _require_godot()
    manifest = _load_manifest()
    entry = next(
        (frame for frame in manifest["frames"] if frame["kind"] == "unsubscribe_applied"),
        None,
    )
    assert entry is not None, "manifest missing unsubscribe_applied entry"
    fixture = _fixture_path(entry["file"])
    result = _invoke_harness(godot, ["parse_unsubscribe_applied", fixture])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "UnsubscribeApplied"
    assert data["tag"] == 2
    assert int(data["request_id"]) == entry["request_id"]
    assert int(data["query_set_id"]) == entry["query_set_id"]


def test_server_reducer_result_parse_matches_fixture() -> None:
    _require_fixtures()
    godot = _require_godot()
    manifest = _load_manifest()
    entry = next(
        (frame for frame in manifest["frames"] if frame["kind"] == "reducer_result"),
        None,
    )
    assert entry is not None, "manifest missing reducer_result entry"
    fixture = _fixture_path(entry["file"])
    result = _invoke_harness(godot, ["parse_reducer_result", fixture])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ReducerResult"
    assert data["tag"] == 6
    assert int(data["request_id"]) == entry["request_id"]
    # v2 ReducerResult bundles TransactionUpdate inside Ok(ReducerOk) — we
    # expect the status to be Committed for a successful ping_insert call.
    assert data["status"] == "Committed", f"expected Committed, got {data['status']}"
    assert isinstance(data.get("query_sets"), list)
