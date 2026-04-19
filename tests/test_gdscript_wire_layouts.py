"""
Byte-exact regression tests for the GDScript wire protocol.

For each client-fixture (Subscribe / CallReducer / Unsubscribe) this test
invokes the GDScript `encode_*` static helper via a Godot-headless harness
and asserts the emitted bytes match the captured `.bin` byte-for-byte.

For each server-fixture (InitialConnection / SubscribeApplied /
SubscriptionError / UnsubscribeApplied / ReducerResult) the test invokes
`GdscriptConnectionProtocol.parse_server_message` via the same harness and
asserts the structured Dictionary it returns matches a pinned expectation.

The fixtures themselves are produced by
`tests/fixtures/gdscript_wire/capture_wire_fixtures.py` — re-run that script
when `spacetime --version` or `SpacetimeDB.ClientSDK` NuGet changes.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import probe_godot_binary

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "gdscript_wire"
HARNESS = FIXTURE_DIR / "parse_fixture_harness.gd"
HARNESS_RES = "res://tests/fixtures/gdscript_wire/parse_fixture_harness.gd"
TOKEN_HARNESS = FIXTURE_DIR / "service_token_validation_harness.gd"
TOKEN_HARNESS_RES = "res://tests/fixtures/gdscript_wire/service_token_validation_harness.gd"
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


def _invoke_script_harness(godot_path: str, harness_res: str, harness_args: list[str]) -> dict:
    """Run a Godot headless harness and return the parsed JSON result."""
    cmd = [
        godot_path,
        "--headless",
        "--path",
        str(ROOT),
        "--script",
        harness_res,
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
        harness_res,
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


def _invoke_harness(godot_path: str, harness_args: list[str]) -> dict:
    return _invoke_script_harness(godot_path, HARNESS_RES, harness_args)


def _load_manifest() -> dict:
    return json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))


def _load_expected(name: str) -> dict:
    path = FIXTURE_DIR / name
    if not path.exists():
        pytest.skip(f"expected parser output {name} missing")
    return json.loads(path.read_text(encoding="utf-8"))


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
    assert TOKEN_HARNESS.exists(), (
        "tests/fixtures/gdscript_wire/service_token_validation_harness.gd must be present "
        "alongside the parse harness."
    )


def test_manifest_documents_unobserved_server_messages() -> None:
    manifest = _load_manifest()
    documented = {
        entry["kind"]: entry["reason"]
        for entry in manifest.get("unobserved_server_messages", [])
    }
    assert "OneOffQueryResult" in documented, (
        "manifest.json must explain why OneOffQueryResult remains a raw parser branch."
    )
    assert "ProcedureResult" in documented, (
        "manifest.json must explain why ProcedureResult remains a raw parser branch."
    )


def test_invalid_initial_connection_token_is_not_persisted() -> None:
    godot = _require_godot()
    result = _invoke_script_harness(
        godot,
        TOKEN_HARNESS_RES,
        ["simulate_initial_connection_token", "not-a-valid-jwt"],
    )
    assert result.get("ok"), f"harness reported error: {result}"
    assert result["data"] == {
        "session_token": "",
        "stored_token": "",
        "state": "Connected",
        "auth_state": "None",
    }


def test_valid_initial_connection_token_is_persisted() -> None:
    godot = _require_godot()
    valid_token = _load_expected("initial_connection_expected.json")["token"]
    result = _invoke_script_harness(
        godot,
        TOKEN_HARNESS_RES,
        ["simulate_initial_connection_token", valid_token],
    )
    assert result.get("ok"), f"harness reported error: {result}"
    assert result["data"] == {
        "session_token": valid_token,
        "stored_token": valid_token,
        "state": "Connected",
        "auth_state": "None",
    }


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
    assert result["data"] == _load_expected("initial_connection_expected.json")


def test_session_compression_hint_does_not_override_v2_envelope_dispatch() -> None:
    _require_fixtures()
    godot = _require_godot()
    fixture = _fixture_path("subscribe_applied_recv.bin")
    result = _invoke_harness(godot, ["parse_any_session_compressed", fixture])
    assert result.get("ok"), f"harness reported error: {result}"
    assert result["data"] == _load_expected("subscribe_applied_expected.json")


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
    assert result["data"] == _load_expected("subscribe_applied_expected.json")


def test_server_subscription_error_parse_matches_fixture() -> None:
    _require_fixtures()
    godot = _require_godot()
    manifest = _load_manifest()
    entry = next(
        (frame for frame in manifest["frames"] if frame["kind"] == "subscription_error"),
        None,
    )
    assert entry is not None, "manifest missing subscription_error entry"
    fixture = _fixture_path(entry["file"])
    result = _invoke_harness(godot, ["parse_any", fixture])
    assert result.get("ok"), f"harness reported error: {result}"
    assert result["data"] == _load_expected("subscription_error_expected.json")


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
    assert result["data"] == _load_expected("unsubscribe_applied_expected.json")


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
    assert result["data"] == _load_expected("reducer_result_expected.json")


def test_server_one_off_query_result_branch_stays_raw_until_fixture_exists(tmp_path: Path) -> None:
    godot = _require_godot()
    raw_fixture = tmp_path / "one_off_query_result.bin"
    raw_fixture.write_bytes(bytes([0x00, 0x05, 0xAA, 0xBB]))
    result = _invoke_harness(godot, ["parse_any", str(raw_fixture)])
    assert result.get("ok"), f"harness reported error: {result}"
    assert result["data"] == {"kind": "OneOffQueryResult", "tag": 5}


def test_server_procedure_result_branch_stays_raw_until_fixture_exists(tmp_path: Path) -> None:
    godot = _require_godot()
    raw_fixture = tmp_path / "procedure_result.bin"
    raw_fixture.write_bytes(bytes([0x00, 0x07, 0xDE, 0xAD]))
    result = _invoke_harness(godot, ["parse_any", str(raw_fixture)])
    assert result.get("ok"), f"harness reported error: {result}"
    assert result["data"] == {"kind": "ProcedureResult", "tag": 7}


def test_unknown_envelope_byte_becomes_protocol_error(tmp_path: Path) -> None:
    godot = _require_godot()
    broken_fixture = tmp_path / "bad_envelope.bin"
    broken_fixture.write_bytes(bytes([0x63, 0x01, 0x02]))
    result = _invoke_harness(godot, ["parse_any", str(broken_fixture)])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ProtocolError"
    assert "Unknown ServerMessage compression envelope byte" in data["error_message"]


def test_unsubscribe_applied_requires_full_packet_consumption(tmp_path: Path) -> None:
    godot = _require_godot()
    fixture_bytes = Path(_fixture_path("unsubscribe_applied_recv.bin")).read_bytes()
    broken_fixture = tmp_path / "unsubscribe_applied_with_trailer.bin"
    broken_fixture.write_bytes(fixture_bytes + b"\x99")
    result = _invoke_harness(godot, ["parse_any", str(broken_fixture)])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ProtocolError"
    assert "UnsubscribeApplied parse drift" in data["error_message"]


def test_reducer_result_requires_full_packet_consumption(tmp_path: Path) -> None:
    godot = _require_godot()
    fixture_bytes = Path(_fixture_path("reducer_result_recv.bin")).read_bytes()
    broken_fixture = tmp_path / "reducer_result_with_trailer.bin"
    broken_fixture.write_bytes(fixture_bytes + b"\x42")
    result = _invoke_harness(godot, ["parse_any", str(broken_fixture)])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ProtocolError"
    assert "ReducerResult parse drift" in data["error_message"]
