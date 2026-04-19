"""
Capture authoritative 2.1.0 WebSocket frames for the GDScript wire-protocol fixtures.

This script is the *oracle* for `tests/test_gdscript_wire_layouts.py`. It:

  1. Probes the pinned runtime (spacetime CLI, local SpacetimeDB server).
  2. Publishes the `smoke_test` module under a fresh uniquely-named database.
  3. Opens a WebSocket with subprotocol `v2.bsatn.spacetimedb` (the protocol
     the pinned `SpacetimeDB.ClientSDK 2.1.0` NuGet actually negotiates — the
     older `v1.bsatn.spacetimedb` subprotocol corresponds to a legacy wire the
     2.1.0 server still accepts but rejects the pinned SDK's own encodings on).
  4. Scripts a short session: receive InitialConnection -> send Subscribe ->
     receive SubscribeApplied -> send CallReducer(ping_insert) -> receive
     ReducerResult -> send Unsubscribe -> receive UnsubscribeApplied.
  5. Writes each sent/received frame as `<dir>/<kind>_<direction>.bin` plus a
     `manifest.json` entry describing the capture.

Re-run whenever the pinned `spacetime --version` or `SpacetimeDB.ClientSDK`
NuGet changes (tracked in `scripts/compatibility/support-baseline.json`).

Exits 0 on success; nonzero with a diagnostic line on any failure.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# websocket-client 1.x sync API; installed as a transitive dependency already.
import websocket  # type: ignore[import-untyped]

# Make the repo's `tests/` package importable regardless of cwd.
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.fixtures.spacetime_runtime import (  # noqa: E402
    probe_local_runtime,
    probe_spacetime_cli,
)

FIXTURE_DIR = Path(__file__).resolve().parent

# The pinned `SpacetimeDB.ClientSDK 2.1.0` NuGet negotiates `v2.bsatn.spacetimedb`
# (confirmed by MITM capture of a full .NET SDK session against the pinned
# 2.1.0 server). The older `v1.bsatn.spacetimedb` subprotocol corresponds to
# an earlier wire the same server still accepts but whose field orderings
# have since been swapped in v2 — notably InitialConnection's Identity/
# ConnectionId/Token ordering, and all server messages now gaining a leading
# compression byte prefix.
SUBPROTOCOL = "v2.bsatn.spacetimedb"
RECEIVE_TIMEOUT_SECONDS = 15.0

# ClientMessage variant indices — observed against the pinned 2.1.0 server
# after switching to v2. These match the SDK's declared nested-type order in
# `SpacetimeDB.ClientApi.ClientMessage`.
CLIENT_TAG_SUBSCRIBE = 0
CLIENT_TAG_UNSUBSCRIBE = 1
CLIENT_TAG_ONE_OFF_QUERY = 2
CLIENT_TAG_CALL_REDUCER = 3
CLIENT_TAG_CALL_PROCEDURE = 4

# ServerMessage variant indices — observed against the pinned 2.1.0 server.
# Every server frame is prefixed with a compression byte (0=None, 1=Brotli,
# 2=Gzip) so the variant is at byte[1], not byte[0]. Matches the SDK's
# declared nested-type order in `SpacetimeDB.ClientApi.ServerMessage`.
SERVER_TAG_INITIAL_CONNECTION = 0
SERVER_TAG_SUBSCRIBE_APPLIED = 1
SERVER_TAG_UNSUBSCRIBE_APPLIED = 2
SERVER_TAG_SUBSCRIPTION_ERROR = 3
SERVER_TAG_TRANSACTION_UPDATE = 4
SERVER_TAG_ONE_OFF_QUERY_RESULT = 5
SERVER_TAG_REDUCER_RESULT = 6
SERVER_TAG_PROCEDURE_RESULT = 7

SERVER_TAG_NAMES = {
    SERVER_TAG_INITIAL_CONNECTION: "InitialConnection",
    SERVER_TAG_SUBSCRIBE_APPLIED: "SubscribeApplied",
    SERVER_TAG_UNSUBSCRIBE_APPLIED: "UnsubscribeApplied",
    SERVER_TAG_SUBSCRIPTION_ERROR: "SubscriptionError",
    SERVER_TAG_TRANSACTION_UPDATE: "TransactionUpdate",
    SERVER_TAG_ONE_OFF_QUERY_RESULT: "OneOffQueryResult",
    SERVER_TAG_REDUCER_RESULT: "ReducerResult",
    SERVER_TAG_PROCEDURE_RESULT: "ProcedureResult",
}

UNOBSERVED_SERVER_MESSAGES = [
    {
        "kind": "OneOffQueryResult",
        "reason": (
            "Not emitted by the pinned smoke_test capture workflow. The native "
            "GDScript runtime keeps this branch as raw_payload passthrough until "
            "an authoritative fixture exists."
        ),
    },
    {
        "kind": "ProcedureResult",
        "reason": (
            "The smoke_test module defines no procedures, so the pinned capture "
            "workflow cannot produce this frame. The parser keeps the branch raw "
            "until a real capture proves its wire layout."
        ),
    },
]


def _die(msg: str, code: int = 1) -> "None":
    sys.stderr.write(f"[capture_wire_fixtures] ERROR: {msg}\n")
    sys.exit(code)


def _pack_u8(v: int) -> bytes:
    return bytes([v & 0xFF])


def _pack_u32_le(v: int) -> bytes:
    return int(v & 0xFFFFFFFF).to_bytes(4, "little", signed=False)


def _pack_string(s: str) -> bytes:
    utf8 = s.encode("utf-8")
    return _pack_u32_le(len(utf8)) + utf8


def _pack_bytes(b: bytes) -> bytes:
    return _pack_u32_le(len(b)) + b


def _build_subscribe_frame(request_id: int, query_set_id: int, queries: list[str]) -> bytes:
    """
    Observed wire layout for `ClientMessage.Subscribe` against the pinned
    `SpacetimeDB.ClientSDK 2.1.0` NuGet speaking to the pinned 2.1.0 server
    over subprotocol `v2.bsatn.spacetimedb`:

        tag(u8=0) | RequestId(u32) | QuerySetId(u32) | QueryStrings(array<string>)

    Field order matches the SDK's declared `Subscribe { RequestId, QuerySetId,
    QueryStrings }` struct. No leading reserved u32 — the server accepts this
    41-byte encoding for a single-query subscribe.
    """
    body = _pack_u32_le(request_id) + _pack_u32_le(query_set_id) + _pack_u32_le(len(queries))
    for q in queries:
        body += _pack_string(q)
    return _pack_u8(CLIENT_TAG_SUBSCRIBE) + body


def _build_unsubscribe_frame(request_id: int, query_set_id: int, flags: int = 0) -> bytes:
    """
    Observed wire layout for `ClientMessage.Unsubscribe`:

        tag(u8=1) | RequestId(u32) | QuerySetId(u32) | Flags(u8)
    """
    body = _pack_u32_le(request_id) + _pack_u32_le(query_set_id) + _pack_u8(flags)
    return _pack_u8(CLIENT_TAG_UNSUBSCRIBE) + body


def _build_call_reducer_frame(request_id: int, reducer_name: str, args_bytes: bytes, flags: int = 0) -> bytes:
    """
    Observed wire layout for `ClientMessage.CallReducer`:

        tag(u8=3) | RequestId(u32) | Flags(u8) | Reducer(string) | Args(bytes)

    Field order matches the SDK's declared struct. Note that the variant tag
    is 3 (not 2) — Subscribe=0, Unsubscribe=1, OneOffQuery=2, CallReducer=3,
    CallProcedure=4.
    """
    body = (
        _pack_u32_le(request_id)
        + _pack_u8(flags)
        + _pack_string(reducer_name)
        + _pack_bytes(args_bytes)
    )
    return _pack_u8(CLIENT_TAG_CALL_REDUCER) + body


def _write_fixture(direction: str, kind: str, payload: bytes, manifest: list[dict], extra: dict[str, Any]) -> None:
    fname = f"{kind}_{direction}.bin"
    (FIXTURE_DIR / fname).write_bytes(payload)
    entry = {
        "file": fname,
        "direction": direction,
        "kind": kind,
        "length": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        **extra,
    }
    manifest.append(entry)


def _spacetime_version_line(cli: str) -> str:
    try:
        out = subprocess.run([cli, "--version"], capture_output=True, text=True, timeout=10)
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        _die(f"spacetime --version failed: {exc}")
    for line in out.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("spacetimedb tool version"):
            return stripped
    return out.stdout.strip().splitlines()[-1] if out.stdout else ""


def _publish_module(cli: str, server: str, module_name: str, root: Path) -> None:
    proc = subprocess.run(
        [
            cli,
            "publish",
            "--server", server,
            "--anonymous",
            "--module-path", str(root / "spacetime" / "modules" / "smoke_test"),
            "--yes",
            module_name,
        ],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(root),
    )
    if proc.returncode != 0:
        _die(
            f"spacetime publish {module_name!r} failed (exit {proc.returncode}):\n"
            f"stderr: {proc.stderr[-600:]}\n"
            f"stdout: {proc.stdout[-600:]}"
        )


def _host_to_ws_url(host: str, module_name: str, connection_id_hex: str) -> str:
    if host.startswith("https://"):
        scheme_swapped = "wss://" + host[len("https://"):]
    elif host.startswith("http://"):
        scheme_swapped = "ws://" + host[len("http://"):]
    else:
        scheme_swapped = "ws://" + host
    # Query parameters observed on the .NET SDK's actual handshake — the server
    # uses `connection_id` to stabilise the client identity across reconnects
    # and `compression` to negotiate frame compression. `compression=None`
    # keeps us in uncompressed mode for deterministic fixture bytes.
    return (
        f"{scheme_swapped}/v1/database/{module_name}/subscribe"
        f"?connection_id={connection_id_hex}&compression=None&confirmed=false"
    )


def _recv_frame(ws: "websocket.WebSocket", context: str) -> bytes:
    ws.settimeout(RECEIVE_TIMEOUT_SECONDS)
    try:
        op, data = ws.recv_data(control_frame=False)
    except websocket.WebSocketTimeoutException:
        _die(f"timeout waiting for {context} after {RECEIVE_TIMEOUT_SECONDS}s")
    except websocket.WebSocketException as exc:
        _die(f"websocket error while receiving {context}: {exc}")
    if op != websocket.ABNF.OPCODE_BINARY:
        _die(f"expected BINARY frame for {context}, got opcode {op}: {data!r}")
    if not isinstance(data, (bytes, bytearray)):
        _die(f"non-binary payload for {context}: {type(data)!r}")
    return bytes(data)


def _server_variant(frame: bytes) -> int:
    """Return the ServerMessage variant tag after the compression byte prefix."""
    if len(frame) < 2:
        _die(f"server frame too short ({len(frame)} bytes) to carry a variant")
    if frame[0] != 0:
        # None=0, Brotli=1, Gzip=2 — for deterministic fixtures we pass
        # compression=None on the URL so the server should always send 0.
        _die(f"unexpected compression byte 0x{frame[0]:02x} — capture requires compression=None on the URL")
    return frame[1]


def _expect_server_variant(frame: bytes, expected: int, context: str) -> None:
    actual = _server_variant(frame)
    if actual != expected:
        _die(
            f"expected ServerMessage variant {expected} ({SERVER_TAG_NAMES.get(expected, '?')}) "
            f"for {context}, got {actual} ({SERVER_TAG_NAMES.get(actual, '?')}). "
            f"frame head: {frame[:32].hex()}"
        )


def main() -> int:
    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        _die(f"spacetime CLI unavailable: {cli_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        _die(f"local SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    version_line = _spacetime_version_line(cli_probe.path)
    module_name = f"gdscript-wire-fixtures-{uuid.uuid4().hex[:12]}"

    print(f"[capture_wire_fixtures] publishing {module_name} to {runtime_probe.server} ...", flush=True)
    _publish_module(cli_probe.path, runtime_probe.server, module_name, ROOT)
    time.sleep(1.0)

    connection_id_hex = uuid.uuid4().hex.upper()
    ws_url = _host_to_ws_url(runtime_probe.host, module_name, connection_id_hex)
    print(f"[capture_wire_fixtures] connecting to {ws_url} ...", flush=True)
    ws = websocket.create_connection(
        ws_url,
        subprotocols=[SUBPROTOCOL],
        timeout=RECEIVE_TIMEOUT_SECONDS,
    )

    manifest: list[dict] = []
    captured_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    shared_meta = {
        "spacetime_version_line": version_line,
        "module_name": module_name,
        "server_nickname": runtime_probe.server,
        "server_host": runtime_probe.host,
        "subprotocol": SUBPROTOCOL,
        "captured_at": captured_at,
        "connection_id": connection_id_hex,
    }

    try:
        # 1. InitialConnection (server -> client, unsolicited on accept)
        init_frame = _recv_frame(ws, "InitialConnection")
        _expect_server_variant(init_frame, SERVER_TAG_INITIAL_CONNECTION, "InitialConnection")
        _write_fixture("recv", "initial_connection", init_frame, manifest, {
            "scenario": "fresh-anonymous-connect",
            **shared_meta,
        })
        print(f"  got InitialConnection ({len(init_frame)} bytes)", flush=True)

        # 2. Subscribe (client -> server) + SubscribeApplied (server -> client)
        subscribe_request_id = 17
        subscribe_query_set_id = 23
        subscribe_queries = ["SELECT * FROM smoke_test"]
        subscribe_frame = _build_subscribe_frame(subscribe_request_id, subscribe_query_set_id, subscribe_queries)
        ws.send_binary(subscribe_frame)
        _write_fixture("sent", "subscribe", subscribe_frame, manifest, {
            "scenario": "subscribe-all-smoke-test",
            "request_id": subscribe_request_id,
            "query_set_id": subscribe_query_set_id,
            "queries": subscribe_queries,
            **shared_meta,
        })
        applied = _recv_frame(ws, "SubscribeApplied")
        _expect_server_variant(applied, SERVER_TAG_SUBSCRIBE_APPLIED, "SubscribeApplied")
        _write_fixture("recv", "subscribe_applied", applied, manifest, {
            "scenario": "subscribe-all-smoke-test-applied",
            "request_id": subscribe_request_id,
            "query_set_id": subscribe_query_set_id,
            **shared_meta,
        })
        print(f"  got SubscribeApplied ({len(applied)} bytes)", flush=True)

        # 2b. Invalid Subscribe -> SubscriptionError. This pins the live
        # v2 replacement-failure frame shape instead of relying only on the
        # synthetic parser probe from Story 11.3.
        invalid_request_id = 24
        invalid_query_set_id = 24
        invalid_queries = ["SELECT * FROM definitely_missing_table"]
        invalid_subscribe_frame = _build_subscribe_frame(
            invalid_request_id,
            invalid_query_set_id,
            invalid_queries,
        )
        ws.send_binary(invalid_subscribe_frame)
        subscription_error = _recv_frame(ws, "SubscriptionError")
        _expect_server_variant(subscription_error, SERVER_TAG_SUBSCRIPTION_ERROR, "SubscriptionError")
        _write_fixture("recv", "subscription_error", subscription_error, manifest, {
            "scenario": "subscribe-invalid-query-error",
            "request_id": invalid_request_id,
            "query_set_id": invalid_query_set_id,
            "queries": invalid_queries,
            **shared_meta,
        })
        print(f"  got SubscriptionError ({len(subscription_error)} bytes)", flush=True)

        # 3. CallReducer(ping_insert, "<e2e_value>") -> ReducerResult + TransactionUpdate
        reducer_request_id = 99
        e2e_value = f"wire-fixture-{uuid.uuid4().hex[:8]}"
        # ping_insert's single arg is a String; BSATN-encoded as u32 len + utf8.
        args_bsatn = _pack_string(e2e_value)
        call_frame = _build_call_reducer_frame(reducer_request_id, "ping_insert", args_bsatn)
        ws.send_binary(call_frame)
        _write_fixture("sent", "call_reducer_ping_insert", call_frame, manifest, {
            "scenario": "call-reducer-ping-insert",
            "request_id": reducer_request_id,
            "reducer_name": "ping_insert",
            "args_value": e2e_value,
            **shared_meta,
        })

        # Server replies with TransactionUpdate + ReducerResult. Order is not
        # strictly specified by the protocol.
        seen_reducer_result = False
        seen_transaction_update = False
        for _ in range(4):
            if seen_reducer_result and seen_transaction_update:
                break
            try:
                ws.settimeout(5.0)
                op, data = ws.recv_data(control_frame=False)
            except websocket.WebSocketTimeoutException:
                break
            frame = bytes(data) if isinstance(data, (bytes, bytearray)) else b""
            variant = _server_variant(frame)
            if variant == SERVER_TAG_REDUCER_RESULT and not seen_reducer_result:
                _write_fixture("recv", "reducer_result", frame, manifest, {
                    "scenario": "reducer-result-ping-insert-committed",
                    "request_id": reducer_request_id,
                    "reducer_name": "ping_insert",
                    **shared_meta,
                })
                seen_reducer_result = True
                print(f"  got ReducerResult ({len(frame)} bytes)", flush=True)
            elif variant == SERVER_TAG_TRANSACTION_UPDATE and not seen_transaction_update:
                _write_fixture("recv", "transaction_update", frame, manifest, {
                    "scenario": "transaction-update-after-ping-insert",
                    "associated_reducer_request_id": reducer_request_id,
                    "associated_reducer_name": "ping_insert",
                    "associated_args_value": e2e_value,
                    **shared_meta,
                })
                seen_transaction_update = True
                print(f"  got TransactionUpdate ({len(frame)} bytes)", flush=True)
            else:
                _die(
                    f"unexpected ServerMessage variant {variant} ({SERVER_TAG_NAMES.get(variant, '?')}) "
                    f"during reducer followup; frame head: {frame[:32].hex()}"
                )

        if not seen_reducer_result:
            _die("did not observe ReducerResult for ping_insert within 4 frames")
        # TransactionUpdate may be optional — record whether we saw one but
        # don't fail the capture if the server chose to bundle the row into
        # ReducerResult.Result instead.
        if not seen_transaction_update:
            print("  (no standalone TransactionUpdate — row may be embedded in ReducerResult)", flush=True)

        # 4. Unsubscribe (client -> server) + UnsubscribeApplied (server -> client)
        unsubscribe_request_id = 101
        unsubscribe_frame = _build_unsubscribe_frame(unsubscribe_request_id, subscribe_query_set_id)
        ws.send_binary(unsubscribe_frame)
        _write_fixture("sent", "unsubscribe", unsubscribe_frame, manifest, {
            "scenario": "unsubscribe-query-set",
            "request_id": unsubscribe_request_id,
            "query_set_id": subscribe_query_set_id,
            **shared_meta,
        })
        unapplied = _recv_frame(ws, "UnsubscribeApplied")
        _expect_server_variant(unapplied, SERVER_TAG_UNSUBSCRIBE_APPLIED, "UnsubscribeApplied")
        _write_fixture("recv", "unsubscribe_applied", unapplied, manifest, {
            "scenario": "unsubscribe-applied",
            "request_id": unsubscribe_request_id,
            "query_set_id": subscribe_query_set_id,
            **shared_meta,
        })
        print(f"  got UnsubscribeApplied ({len(unapplied)} bytes)", flush=True)

    finally:
        try:
            ws.close()
        except Exception:  # noqa: BLE001
            pass

    manifest_path = FIXTURE_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "generated_by": "tests/fixtures/gdscript_wire/capture_wire_fixtures.py",
                "spacetime_version_line": version_line,
                "captured_at": captured_at,
                "unobserved_server_messages": UNOBSERVED_SERVER_MESSAGES,
                "frames": manifest,
            },
            indent=2,
            sort_keys=False,
        ) + "\n",
        encoding="utf-8",
    )

    print(
        f"[capture_wire_fixtures] wrote {len(manifest)} fixtures + manifest.json to {FIXTURE_DIR}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
