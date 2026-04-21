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
import re
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


def test_subscription_handle_splits_request_id_from_query_set_id() -> None:
    # The handle's `request_id` and `query_set_id` are conceptually distinct:
    # `request_id` correlates client->server frames; `query_set_id` is the
    # server's addressing id for the live subscription. On pinned 2.1.0 they
    # happen to be equal at construction, but the split must exist so a future
    # `SubscribeApplied` handler can reassign `query_set_id` without touching
    # `request_id`. The encode call site must read each by name — not
    # `handle.query_set_id` twice — so the wire abstraction stays honest even
    # when the runtime values drift apart.
    handle_src = (
        ROOT
        / "addons"
        / "godot_spacetime"
        / "src"
        / "Internal"
        / "Platform"
        / "GDScript"
        / "gdscript_subscription_handle.gd"
    ).read_text(encoding="utf-8")
    assert "var request_id" in handle_src, (
        "gdscript_subscription_handle.gd must declare `var request_id` as a distinct field from `query_set_id`."
    )
    assert "var query_set_id" in handle_src, (
        "gdscript_subscription_handle.gd must keep the `var query_set_id` field."
    )
    assert (
        "func _init(handle_id_value: int, request_id_value: int, query_set_id_value: int, query_sqls_value: Array = []) -> void:"
        in handle_src
    ), (
        "gdscript_subscription_handle.gd `_init` must accept explicit handle_id, request_id, query_set_id, and query_sqls parameters in that order."
    )

    service_src = (
        ROOT
        / "addons"
        / "godot_spacetime"
        / "src"
        / "Internal"
        / "Platform"
        / "GDScript"
        / "gdscript_connection_service.gd"
    ).read_text(encoding="utf-8")
    # The encode call site must read both fields by name.
    encode_needle = (
        "ConnectionProtocolScript.encode_subscribe(\n"
        "\t\tint(handle.request_id),\n"
        "\t\tint(handle.query_set_id),\n"
    )
    assert encode_needle in service_src, (
        "_send_subscribe_request must pass `int(handle.request_id)` and `int(handle.query_set_id)` "
        "as distinct arguments to encode_subscribe — not `handle.query_set_id` twice."
    )


def test_pinned_subscribe_fixture_keeps_request_and_query_set_ids_distinct() -> None:
    manifest = _load_manifest()
    entry = next(
        (frame for frame in manifest["frames"] if frame["kind"] == "subscribe"),
        None,
    )
    assert entry is not None, "manifest missing subscribe entry"
    assert int(entry["request_id"]) != int(entry["query_set_id"]), (
        "The pinned subscribe fixture must keep request_id and query_set_id distinct so "
        "service/runtime reviews do not silently collapse the two wire fields back together."
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


def test_zero_byte_packet_short_packet_yields_protocol_error(tmp_path: Path) -> None:
    # A 0-byte server frame must not crash the parser. The entry guard should
    # fail it into a ProtocolError BEFORE any BsatnReader.read_u8 call runs,
    # so the receive loop can route it to _schedule_retry_or_disconnect.
    godot = _require_godot()
    empty_fixture = tmp_path / "zero_byte.bin"
    empty_fixture.write_bytes(b"")
    result = _invoke_harness(godot, ["parse_any", str(empty_fixture)])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ProtocolError"
    assert "Empty ServerMessage packet" in data["error_message"]


def test_one_byte_envelope_only_short_packet_yields_protocol_error(tmp_path: Path) -> None:
    # A 1-byte envelope-only frame (no variant tag byte) must return
    # ProtocolError WITHOUT invoking BsatnReader.read_u8 — read_u8 on an empty
    # post-envelope buffer trips _fail → len(int) which raises a runtime error
    # instead of producing a routable ProtocolError.
    godot = _require_godot()
    one_byte_fixture = tmp_path / "one_byte.bin"
    one_byte_fixture.write_bytes(bytes([0x00]))
    result = _invoke_harness(godot, ["parse_any", str(one_byte_fixture)])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ProtocolError"
    # The short-packet entry guard must fire BEFORE the parser dispatches on
    # the variant tag — match either the existing "Empty" wording (if the
    # guard reuses it) or a "too short" variant.
    err = data["error_message"]
    assert ("Empty ServerMessage packet" in err) or ("too short" in err.lower()) or ("truncated" in err.lower()), (
        f"Short-packet guard must emit a recognisable ProtocolError substring. got {err!r}"
    )


def test_unknown_row_size_hint_tag_yields_top_level_protocol_error(tmp_path: Path) -> None:
    # A TransactionUpdate frame whose BSATN row-size-hint tag is neither 0
    # (FixedSize) nor 1 (RowOffsets) must surface as a top-level ProtocolError,
    # NOT as a best-effort-parsed TransactionUpdate with a "Unknown"-kind
    # size_hint that downstream iterations would then walk on garbage bytes.
    godot = _require_godot()
    # Synthesise a minimal-valid TransactionUpdate frame from the ground up so
    # the parser advances all the way into _parse_row_size_hint and hits the
    # unknown branch. Byte layout (little-endian) observed against the pinned
    # 2.1.0 wire in connection_protocol.gd:
    #   envelope(u8=0x00) | variant(u8=0x04=TransactionUpdate)
    #   query_set_count(u32=1) | query_set_id(u32=0)
    #   table_count(u32=1) | table_name(len u32=1 | "A")
    #   update_count(u32=1) | table_update_rows variant(u8=1=EventTable)
    #   row_size_hint tag(u8=0x63 = 99, unknown)
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

    bad_hint_fixture = tmp_path / "unknown_row_size_hint.bin"
    bad_hint_fixture.write_bytes(bytes(frame))
    result = _invoke_harness(godot, ["parse_any", str(bad_hint_fixture)])
    assert result.get("ok"), f"harness reported error: {result}"
    data = result["data"]
    assert data["kind"] == "ProtocolError", (
        "Unknown row-size-hint tag must surface as a top-level ProtocolError, "
        f"not a best-effort-parsed message. got kind={data.get('kind')!r}"
    )
    err = data["error_message"]
    assert "row size hint" in err.lower() or "row_size_hint" in err.lower() or "hint tag" in err.lower(), (
        f"ProtocolError must identify the row-size-hint failure. got {err!r}"
    )


def test_finish_disconnect_documents_emission_order_contract() -> None:
    # `_finish_disconnect` must carry an immediately preceding comment block
    # whose wording is version-locked by the spec: it must say "state_changed
    # first" and "connection_closed second" within 20 lines of the function,
    # and it must also name the `open_connection` reentry caveat plus the
    # `closed_at_unix_time` workaround.
    service_src = (
        ROOT
        / "addons"
        / "godot_spacetime"
        / "src"
        / "Internal"
        / "Platform"
        / "GDScript"
        / "gdscript_connection_service.gd"
    ).read_text(encoding="utf-8")
    lines = service_src.splitlines()
    func_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("func _finish_disconnect(")),
        -1,
    )
    assert func_idx >= 0, "gdscript_connection_service.gd must define `func _finish_disconnect(`"
    block_start = func_idx
    for idx in range(func_idx - 1, -1, -1):
        if lines[idx].startswith("#"):
            block_start = idx
            continue
        break
    assert block_start != func_idx, (
        "`_finish_disconnect` must carry an immediately preceding comment block."
    )
    assert (func_idx - block_start) <= 20, (
        "`_finish_disconnect` contract comment must live within 20 lines of the function. "
        f"Found {func_idx - block_start} comment lines."
    )
    preamble = "\n".join(lines[block_start:func_idx]).lower()
    assert "state_changed first" in preamble, (
        "`_finish_disconnect` must lock the exact phrase 'state_changed first'. "
        "Preamble was: " + preamble
    )
    assert "connection_closed second" in preamble, (
        "`_finish_disconnect` must lock the exact phrase 'connection_closed second'. "
        "Preamble was: " + preamble
    )
    assert "open_connection" in preamble, (
        "`_finish_disconnect` contract comment must describe the reentry caveat involving "
        "`open_connection`. Preamble was: " + preamble
    )
    assert "closed_at_unix_time" in preamble, (
        "`_finish_disconnect` contract comment must include the documented "
        "`closed_at_unix_time` workaround. Preamble was: " + preamble
    )


def test_drain_packets_caps_per_tick_backlog() -> None:
    # `_drain_packets` previously had no cap; a reconnect against a live table
    # with a large backlog froze the main thread. The cap keeps per-tick wall
    # time bounded and lets remaining packets drain on subsequent ticks. Pin
    # both the constant declaration and the loop-level `break` so a silent
    # regression (e.g., someone removing the break under the belief the cap is
    # "too conservative") fails the test.
    service_src = (
        ROOT
        / "addons"
        / "godot_spacetime"
        / "src"
        / "Internal"
        / "Platform"
        / "GDScript"
        / "gdscript_connection_service.gd"
    ).read_text(encoding="utf-8")
    # (a) Constant declared with a positive int value.
    const_match = re.search(
        r"^const\s+DRAIN_PACKETS_PER_TICK\s*:\s*int\s*=\s*(\d+)",
        service_src,
        re.MULTILINE,
    )
    assert const_match is not None, (
        "gdscript_connection_service.gd must declare `const DRAIN_PACKETS_PER_TICK: int = <positive int>`."
    )
    assert int(const_match.group(1)) > 0, (
        f"DRAIN_PACKETS_PER_TICK must be positive. got {const_match.group(1)}"
    )
    # (b) `_drain_packets` body references the constant AND contains a `break`.
    lines = service_src.splitlines()
    func_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("func _drain_packets(")),
        -1,
    )
    assert func_idx >= 0, "gdscript_connection_service.gd must define `func _drain_packets(`"
    # Collect the function body up to the next top-level `func ` (start of next function).
    body_lines: list[str] = []
    for ln in lines[func_idx + 1 :]:
        if ln.startswith("func "):
            break
        body_lines.append(ln)
    body = "\n".join(body_lines)
    const_idx = body.find("DRAIN_PACKETS_PER_TICK")
    assert const_idx >= 0, (
        "`_drain_packets` body must reference the DRAIN_PACKETS_PER_TICK constant."
    )
    # The `break` that exits the loop at the cap must appear AFTER the
    # DRAIN_PACKETS_PER_TICK reference AND within a few lines of it — otherwise
    # a future refactor that removes the cap's break but adds an unrelated
    # break elsewhere in the function body would still pass. Require the break
    # in the same logical block: within 3 non-empty lines after the constant
    # reference.
    tail = body[const_idx:]
    break_match = re.search(r"^\s+break\b", tail, re.MULTILINE)
    assert break_match is not None, (
        "`_drain_packets` body must contain a `break` statement that follows the "
        "DRAIN_PACKETS_PER_TICK reference and exits the loop at the cap."
    )
    intervening = tail[: break_match.start()]
    intervening_non_empty_lines = [ln for ln in intervening.splitlines() if ln.strip()]
    assert len(intervening_non_empty_lines) <= 3, (
        "The cap's `break` must follow the DRAIN_PACKETS_PER_TICK reference within 3 "
        f"non-empty lines; got {len(intervening_non_empty_lines)} lines in between: "
        f"{intervening_non_empty_lines}"
    )


def test_drain_packets_declares_teardown_drop_contract() -> None:
    # `_drain_packets` must carry a preceding comment block that names the
    # "teardown-drop contract" — handler-triggered synchronous teardown
    # (e.g. ProtocolError → `_finish_disconnect`) drops remaining OS-buffered
    # packets. The block must also name the rejected snapshot-drain alternative
    # and the explicit "pre-teardown packets dispatched into post-teardown
    # state" rationale so a future contributor cannot silently change the
    # semantics without updating the contract.
    service_src = (
        ROOT
        / "addons"
        / "godot_spacetime"
        / "src"
        / "Internal"
        / "Platform"
        / "GDScript"
        / "gdscript_connection_service.gd"
    ).read_text(encoding="utf-8")
    lines = service_src.splitlines()
    func_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("func _drain_packets(")),
        -1,
    )
    assert func_idx >= 0, "gdscript_connection_service.gd must define `func _drain_packets(`"
    block_start = func_idx
    for idx in range(func_idx - 1, -1, -1):
        if lines[idx].startswith("#"):
            block_start = idx
            continue
        break
    assert block_start != func_idx, (
        "`_drain_packets` must carry an immediately preceding comment block documenting "
        "the teardown-drop contract."
    )
    preamble = "\n".join(lines[block_start:func_idx])
    assert "teardown-drop contract" in preamble, (
        "`_drain_packets` preamble must lock the exact phrase 'teardown-drop contract'. "
        "Preamble was: " + preamble
    )
    assert "pre-teardown packets dispatched into post-teardown state" in preamble, (
        "`_drain_packets` preamble must name the rejected snapshot-drain rationale verbatim "
        "('pre-teardown packets dispatched into post-teardown state'). "
        "Preamble was: " + preamble
    )
    # Must also reference `_finish_disconnect` so the contract block points at
    # the actual teardown entry point rather than a hand-waving description.
    assert "_finish_disconnect" in preamble, (
        "`_drain_packets` preamble must reference `_finish_disconnect` as the teardown entry "
        "point. Preamble was: " + preamble
    )


def test_drain_packets_backlog_saturation_watermark() -> None:
    # The `_drain_packets` cap bounds per-tick wall time but not steady-state
    # backlog. A sustained-flood watermark pins operator observability: the
    # two thresholds (ticks + packets), the two runtime fields (counter + flag),
    # the increment/reset sites, and the single `push_warning` emit site must
    # all survive a silent refactor (e.g., someone removing the warn or
    # flipping the de-dup flag's semantics to "emit-per-tick").
    service_src = (
        ROOT
        / "addons"
        / "godot_spacetime"
        / "src"
        / "Internal"
        / "Platform"
        / "GDScript"
        / "gdscript_connection_service.gd"
    ).read_text(encoding="utf-8")
    # (a) Both thresholds declared as positive-int constants.
    ticks_match = re.search(
        r"^const\s+BACKLOG_SATURATION_TICKS\s*:\s*int\s*=\s*(\d+)",
        service_src,
        re.MULTILINE,
    )
    assert ticks_match is not None, (
        "gdscript_connection_service.gd must declare "
        "`const BACKLOG_SATURATION_TICKS: int = <positive int>`."
    )
    assert int(ticks_match.group(1)) > 0, (
        f"BACKLOG_SATURATION_TICKS must be positive. got {ticks_match.group(1)}"
    )
    recovery_match = re.search(
        r"^const\s+BACKLOG_RECOVERY_TICKS\s*:\s*int\s*=\s*(\d+)",
        service_src,
        re.MULTILINE,
    )
    assert recovery_match is not None, (
        "gdscript_connection_service.gd must declare "
        "`const BACKLOG_RECOVERY_TICKS: int = <positive int>` to gate the dedup-flag "
        "re-arm under hysteresis."
    )
    assert int(recovery_match.group(1)) > 0, (
        f"BACKLOG_RECOVERY_TICKS must be positive. got {recovery_match.group(1)}"
    )
    watermark_match = re.search(
        r"^const\s+BACKLOG_WATERMARK_PACKETS\s*:\s*int\s*=\s*(\d+)",
        service_src,
        re.MULTILINE,
    )
    assert watermark_match is not None, (
        "gdscript_connection_service.gd must declare "
        "`const BACKLOG_WATERMARK_PACKETS: int = <positive int>`."
    )
    watermark_value = int(watermark_match.group(1))
    # Watermark packets must strictly exceed the per-tick cap, otherwise the
    # "packets still buffered past the cap" semantic is incoherent (the cap
    # itself would trip the warning on a single saturated tick).
    cap_match = re.search(
        r"^const\s+DRAIN_PACKETS_PER_TICK\s*:\s*int\s*=\s*(\d+)",
        service_src,
        re.MULTILINE,
    )
    assert cap_match is not None, "DRAIN_PACKETS_PER_TICK must still be declared."
    assert watermark_value > int(cap_match.group(1)), (
        f"BACKLOG_WATERMARK_PACKETS ({watermark_value}) must strictly exceed "
        f"DRAIN_PACKETS_PER_TICK ({cap_match.group(1)})."
    )
    # (b) Both runtime fields declared with the expected default values.
    assert re.search(
        r"^var\s+_consecutive_saturated_ticks\s*:\s*int\s*=\s*0",
        service_src,
        re.MULTILINE,
    ), "`var _consecutive_saturated_ticks: int = 0` field declaration missing."
    assert re.search(
        r"^var\s+_backlog_warning_emitted\s*:\s*bool\s*=\s*false",
        service_src,
        re.MULTILINE,
    ), "`var _backlog_warning_emitted: bool = false` field declaration missing."
    assert re.search(
        r"^var\s+_consecutive_below_cap_ticks\s*:\s*int\s*=\s*0",
        service_src,
        re.MULTILINE,
    ), (
        "`var _consecutive_below_cap_ticks: int = 0` field declaration missing — "
        "required by the hysteresis gate added in the saturation-polish spec."
    )
    # (c) `_drain_packets` must hand off to the extracted state-machine helper
    # `_update_backlog_saturation`, which owns the thresholds / counter /
    # de-dup flag / warn-emit site. The extraction is what lets runtime tests
    # exercise the state machine without faking WebSocketPeer.
    lines = service_src.splitlines()
    func_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("func _drain_packets(")),
        -1,
    )
    assert func_idx >= 0, "`func _drain_packets(` must exist."
    drain_body_lines: list[str] = []
    for ln in lines[func_idx + 1 :]:
        if ln.startswith("func "):
            break
        drain_body_lines.append(ln)
    drain_body = "\n".join(drain_body_lines)
    assert "_update_backlog_saturation(" in drain_body, (
        "`_drain_packets` body must delegate to `_update_backlog_saturation(...)` so the "
        "state-machine transitions are unit-testable."
    )
    # The pre-teardown flush emission lives inline in `_drain_packets` (not in
    # `_update_backlog_saturation`) because every teardown arm resets the
    # saturation counter BEFORE control returns to the post-loop accounting.
    # `_drain_packets` must snapshot the pre-dispatch counter and hand it to
    # `_check_and_emit_pre_teardown_flush` so the flush sees the real
    # pre-teardown value, not the zeroed post-reset value.
    assert "saturated_ticks_before_dispatch" in drain_body, (
        "`_drain_packets` body must snapshot `_consecutive_saturated_ticks` into a "
        "`saturated_ticks_before_dispatch` local before each packet dispatch so the "
        "pre-teardown flush sees the real pre-reset counter value."
    )
    assert "_check_and_emit_pre_teardown_flush(" in drain_body, (
        "`_drain_packets` body must call `_check_and_emit_pre_teardown_flush(...)` after "
        "each packet dispatch so handler-induced teardowns get logged with the pre-reset "
        "saturation counter."
    )
    helper_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("func _update_backlog_saturation(")),
        -1,
    )
    assert helper_idx >= 0, (
        "`func _update_backlog_saturation(` must exist as the extracted state-machine helper."
    )
    helper_body_lines: list[str] = []
    for ln in lines[helper_idx + 1 :]:
        if ln.startswith("func "):
            break
        helper_body_lines.append(ln)
    helper_body = "\n".join(helper_body_lines)
    assert "BACKLOG_SATURATION_TICKS" in helper_body, (
        "`_update_backlog_saturation` body must reference BACKLOG_SATURATION_TICKS."
    )
    assert "BACKLOG_WATERMARK_PACKETS" in helper_body, (
        "`_update_backlog_saturation` body must reference BACKLOG_WATERMARK_PACKETS."
    )
    assert "_consecutive_saturated_ticks += 1" in helper_body, (
        "`_update_backlog_saturation` body must increment `_consecutive_saturated_ticks` "
        "exactly once per saturated tick. Expected literal `_consecutive_saturated_ticks += 1`."
    )
    assert "_consecutive_saturated_ticks = 0" in helper_body, (
        "`_update_backlog_saturation` body must zero `_consecutive_saturated_ticks` inline "
        "on every below-cap tick (within-episode counter semantics unchanged). Expected "
        "literal `_consecutive_saturated_ticks = 0` on the non-saturated branch."
    )
    assert "_consecutive_below_cap_ticks += 1" in helper_body, (
        "`_update_backlog_saturation` body must increment `_consecutive_below_cap_ticks` "
        "on each below-cap tick to implement the hysteresis gate."
    )
    assert "BACKLOG_RECOVERY_TICKS" in helper_body, (
        "`_update_backlog_saturation` body must reference BACKLOG_RECOVERY_TICKS to gate "
        "dedup-flag re-arm under the hysteresis contract."
    )
    assert "_backlog_warning_emitted = true" in helper_body, (
        "`_update_backlog_saturation` body must set `_backlog_warning_emitted = true` on "
        "the warn-emit branch to de-dup per-episode."
    )
    assert "_backlog_warning_emitted = false" in helper_body, (
        "`_update_backlog_saturation` body must clear `_backlog_warning_emitted = false` "
        "on the hysteresis-triggered re-arm branch."
    )
    push_warning_count = helper_body.count("push_warning(")
    assert push_warning_count >= 1, (
        "`_update_backlog_saturation` body must emit `push_warning(` at least once "
        "(the saturation warn)."
    )
    # Pre-teardown flush emission lives in a dedicated helper so it stays
    # direct-testable from the harness (no fake WebSocketPeer needed).
    flush_helper_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("func _check_and_emit_pre_teardown_flush(")),
        -1,
    )
    assert flush_helper_idx >= 0, (
        "`func _check_and_emit_pre_teardown_flush(` must exist so the pre-teardown flush "
        "can be direct-tested without standing up a fake WebSocketPeer."
    )
    flush_helper_body_lines: list[str] = []
    for ln in lines[flush_helper_idx + 1 :]:
        if ln.startswith("func "):
            break
        flush_helper_body_lines.append(ln)
    flush_helper_body = "\n".join(flush_helper_body_lines)
    assert "_socket == null" in flush_helper_body, (
        "`_check_and_emit_pre_teardown_flush` body must gate on `_socket == null` so the "
        "flush fires only when a handler has torn down the session."
    )
    assert "not warning_emitted_before_dispatch" in flush_helper_body, (
        "`_check_and_emit_pre_teardown_flush` body must gate on the pre-dispatch snapshot "
        "(`not warning_emitted_before_dispatch`) — the live `_backlog_warning_emitted` "
        "field is already zeroed by the teardown-path reset when control reaches the flush."
    )
    assert "BACKLOG_SATURATION_TICKS / 2" in flush_helper_body, (
        "`_check_and_emit_pre_teardown_flush` body must compare the snapshot against "
        "`BACKLOG_SATURATION_TICKS / 2` (half-threshold floor)."
    )
    assert "saturation symptom at teardown" in flush_helper_body, (
        "`_check_and_emit_pre_teardown_flush` body must emit a push_warning containing "
        "the literal `saturation symptom at teardown` substring so operators debugging a "
        "saturation-triggered disconnect see the symptom."
    )
    assert flush_helper_body.count("push_warning(") == 1, (
        "`_check_and_emit_pre_teardown_flush` body must emit exactly one `push_warning(` — "
        "the pre-teardown flush."
    )
    assert "_backlog_warning_emitted = true" not in flush_helper_body, (
        "`_check_and_emit_pre_teardown_flush` body must NOT set "
        "`_backlog_warning_emitted = true` — doing so would bleed the dedup flag across "
        "the degraded-reconnect cycle, since `_start_transport` does not run another "
        "`_reset_backlog_saturation_state()`. Within-session dedup is unnecessary "
        "because `_socket == null` blocks further drain iterations."
    )
    reset_helper_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("func _reset_backlog_saturation_state(")),
        -1,
    )
    assert reset_helper_idx >= 0, (
        "`func _reset_backlog_saturation_state(` must exist so disconnect/retry paths can "
        "clear saturation accounting without duplicating the field-reset logic."
    )
    reset_helper_body_lines: list[str] = []
    for ln in lines[reset_helper_idx + 1 :]:
        if ln.startswith("func "):
            break
        reset_helper_body_lines.append(ln)
    reset_helper_body = "\n".join(reset_helper_body_lines)
    assert "_consecutive_saturated_ticks = 0" in reset_helper_body, (
        "`_reset_backlog_saturation_state` must clear `_consecutive_saturated_ticks = 0`."
    )
    assert "_backlog_warning_emitted = false" in reset_helper_body, (
        "`_reset_backlog_saturation_state` must clear `_backlog_warning_emitted = false`."
    )
    assert "_consecutive_below_cap_ticks = 0" in reset_helper_body, (
        "`_reset_backlog_saturation_state` must clear `_consecutive_below_cap_ticks = 0` "
        "so the hysteresis counter starts fresh after a session reset."
    )
    # (d) `_reset_subscription_runtime` must clear both fields so a reconnect
    # starts with a fresh saturation-accounting window.
    reset_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("func _reset_subscription_runtime(")),
        -1,
    )
    assert reset_idx >= 0, "`func _reset_subscription_runtime(` must exist."
    reset_body_lines: list[str] = []
    for ln in lines[reset_idx + 1 :]:
        if ln.startswith("func "):
            break
        reset_body_lines.append(ln)
    reset_body = "\n".join(reset_body_lines)
    assert "_reset_backlog_saturation_state()" in reset_body, (
        "`_reset_subscription_runtime` must clear saturation accounting via "
        "`_reset_backlog_saturation_state()` so a reconnect does not carry pre-reset "
        "backlog accounting into the new session."
    )
    schedule_retry_idx = next(
        (i for i, ln in enumerate(lines) if ln.startswith("func _schedule_retry_or_disconnect(")),
        -1,
    )
    assert schedule_retry_idx >= 0, "`func _schedule_retry_or_disconnect(` must exist."
    schedule_retry_body_lines: list[str] = []
    for ln in lines[schedule_retry_idx + 1 :]:
        if ln.startswith("func "):
            break
        schedule_retry_body_lines.append(ln)
    schedule_retry_body = "\n".join(schedule_retry_body_lines)
    assert "_reset_backlog_saturation_state()" in schedule_retry_body, (
        "`_schedule_retry_or_disconnect` must clear backlog saturation state on the retry "
        "branch so a degraded reconnect starts a fresh episode window."
    )
