"""
Runtime coverage for spec-gdscript-wire-drain-packets-hardening.

Drives `_update_backlog_saturation` — the state-machine helper extracted from
`_drain_packets` — across tick sequences so the saturation counter + de-dup
flag transitions can be observed without faking Godot's strongly-typed
WebSocketPeer. The static-contract layer lives in `test_gdscript_wire_layouts.py`
(landmark strings, const declarations, field declarations, reset-site wiring);
this module provides the behavioral layer.

The saturation modes drive `_update_backlog_saturation()` directly, while the
teardown mode runs `_drain_packets()` end-to-end against a throwaway local
WebSocket server so the mid-drain disconnect/drop contract is pinned against
the real loop.
"""

from __future__ import annotations

import base64
import hashlib
import json
import socket
import struct
import subprocess
import threading
import time
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import probe_godot_binary

ROOT = Path(__file__).resolve().parents[1]
EVENT_PREFIX = "WIRE-HARNESS "
HARNESS_TIMEOUT_SECONDS = 40
HARNESS_RES = "res://tests/fixtures/gdscript_wire/service_drain_packets_harness.gd"
BACKLOG_WARNING_PREFIX = "GDScript wire: backlog saturation"
_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _require_godot() -> str:
    godot = probe_godot_binary()
    if not godot.available:
        pytest.skip(f"godot-mono not available on PATH: {godot.reason}")
    return godot.path


def _run_harness_process(
    mode: str,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    godot_path = _require_godot()
    argv = [
        godot_path,
        "--headless",
        "--path",
        str(ROOT),
        "--script",
        HARNESS_RES,
        "--",
        mode,
    ]
    if extra_args:
        argv.extend(extra_args)
    return subprocess.run(
        argv,
        capture_output=True,
        timeout=HARNESS_TIMEOUT_SECONDS,
        cwd=str(ROOT),
    )


def _parse_harness_result(proc: subprocess.CompletedProcess[bytes], mode: str) -> dict:
    stdout = proc.stdout.decode("utf-8", "replace")
    stderr = proc.stderr.decode("utf-8", "replace")
    assert proc.returncode == 0, (
        f"harness exited {proc.returncode} for mode={mode!r}\n"
        f"stdout:\n{stdout}\nstderr:\n{stderr}"
    )
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
        f"harness emitted no WIRE-HARNESS event for mode={mode!r}\n"
        f"stdout:\n{stdout}\nstderr:\n{stderr}"
    )


def _run_harness(mode: str) -> dict:
    return _parse_harness_result(_run_harness_process(mode), mode)


def _unwrap(result: dict, mode: str) -> dict:
    assert result.get("ok") is True, (
        f"harness mode={mode!r} reported failure: {result.get('error', '<missing>')}"
    )
    return result["data"]


def _build_initial_connection_frame(token: str) -> bytes:
    token_bytes = token.encode("utf-8")
    identity = bytes(range(32))
    connection_id = bytes(0xA0 + i for i in range(16))
    return (
        bytes([0, 0])
        + identity
        + connection_id
        + struct.pack("<I", len(token_bytes))
        + token_bytes
    )


def _encode_binary_frame(payload: bytes) -> bytes:
    size = len(payload)
    if size < 126:
        header = bytes([0x82, size])
    elif size < 65536:
        header = bytes([0x82, 126]) + struct.pack("!H", size)
    else:
        header = bytes([0x82, 127]) + struct.pack("!Q", size)
    return header + payload


class _FixtureWebSocketServer:
    def __init__(self, payloads: list[bytes]) -> None:
        self._payloads = payloads
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(1)
        self._sock.settimeout(5)
        self.port = int(self._sock.getsockname()[1])
        self._thread = threading.Thread(target=self._serve_once, daemon=True)
        self.error: Exception | None = None

    def __enter__(self) -> _FixtureWebSocketServer:
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self._sock.close()
        finally:
            self._thread.join(timeout=2)
        if self.error is not None and exc is None:
            raise AssertionError(f"fixture websocket server failed: {self.error}") from self.error

    def _serve_once(self) -> None:
        conn: socket.socket | None = None
        try:
            conn, _addr = self._sock.accept()
            conn.settimeout(5)
            request = b""
            while b"\r\n\r\n" not in request:
                chunk = conn.recv(4096)
                if not chunk:
                    raise RuntimeError("client closed during websocket handshake")
                request += chunk
            headers = self._parse_headers(request)
            key = headers.get("sec-websocket-key", "")
            if not key:
                raise RuntimeError("missing Sec-WebSocket-Key in handshake")
            accept = base64.b64encode(
                hashlib.sha1((key + _WS_GUID).encode("ascii")).digest()
            ).decode("ascii")
            response_lines = [
                "HTTP/1.1 101 Switching Protocols",
                "Upgrade: websocket",
                "Connection: Upgrade",
                f"Sec-WebSocket-Accept: {accept}",
            ]
            protocols = headers.get("sec-websocket-protocol", "")
            if "v2.bsatn.spacetimedb" in protocols:
                response_lines.append("Sec-WebSocket-Protocol: v2.bsatn.spacetimedb")
            conn.sendall(("\r\n".join(response_lines) + "\r\n\r\n").encode("ascii"))
            time.sleep(0.05)
            for payload in self._payloads:
                conn.sendall(_encode_binary_frame(payload))
            time.sleep(0.2)
        except Exception as exc:  # pragma: no cover - exercised via harness failure
            self.error = exc
        finally:
            if conn is not None:
                try:
                    conn.close()
                except OSError:
                    pass

    @staticmethod
    def _parse_headers(request: bytes) -> dict[str, str]:
        lines = request.decode("latin1").split("\r\n")
        headers: dict[str, str] = {}
        for line in lines[1:]:
            if not line:
                break
            name, sep, value = line.partition(":")
            if not sep:
                continue
            headers[name.strip().lower()] = value.strip()
        return headers


def test_transient_saturation_emits_no_warning() -> None:
    data = _unwrap(_run_harness("transient_saturation_no_warning"), "transient_saturation_no_warning")
    # Counter climbed during saturated ticks and reset to 0 on the recovery
    # tick. No tick entry shows `emitted: true`.
    timeline = data["timeline"]
    below_threshold = int(data["below_threshold"])
    assert len(timeline) == below_threshold + 1
    for i in range(below_threshold):
        entry = timeline[i]
        assert entry["saturated"] is True
        assert entry["counter"] == i + 1, (
            f"counter must climb monotonically during sub-threshold saturation; "
            f"tick {i} reported counter={entry['counter']}"
        )
        assert entry["emitted"] is False, (
            f"warning must not emit below the tick threshold; tick {i} emitted"
        )
    recovery = timeline[-1]
    assert recovery["saturated"] is False
    assert recovery["counter"] == 0, (
        f"recovery tick must reset counter to 0; got {recovery['counter']}"
    )
    assert recovery["emitted"] is False
    assert int(data["final_counter"]) == 0
    assert bool(data["final_emitted"]) is False


def test_sustained_saturation_emits_exactly_one_warning_per_episode() -> None:
    proc = _run_harness_process("sustained_saturation_single_warning")
    data = _unwrap(
        _parse_harness_result(proc, "sustained_saturation_single_warning"),
        "sustained_saturation_single_warning",
    )
    threshold = int(data["threshold"])
    first_emit = int(data["first_emit_tick"])
    history = data["emitted_history"]
    # The flag must flip true on exactly the (threshold - 1)-th tick index
    # (0-indexed) — that is, the BACKLOG_SATURATION_TICKS-th tick.
    assert first_emit == threshold - 1, (
        f"warning must fire on the {threshold}-th saturated tick "
        f"(0-indexed {threshold - 1}); first_emit_tick={first_emit}"
    )
    # Before the threshold: flag stays false. At and after the threshold: flag
    # stays true for the rest of the episode. This pins "one warning per
    # episode" — the flag is the observable, and subsequent saturated ticks
    # must not flip it back off (which would let it re-arm prematurely and
    # re-emit without an intervening recovery).
    for i, flag in enumerate(history):
        if i < threshold - 1:
            assert flag is False, (
                f"tick {i} must not have emitted yet (threshold={threshold}); flag={flag}"
            )
        else:
            assert flag is True, (
                f"tick {i} must have flag=true after threshold reached; flag={flag}"
            )
    assert bool(data["final_emitted"]) is True
    assert int(data["final_counter"]) == len(history)
    stderr = proc.stderr.decode("utf-8", "replace")
    assert stderr.count(BACKLOG_WARNING_PREFIX) == 1, (
        "sustained saturation must emit exactly one push_warning per episode; "
        f"stderr tail: {stderr[-1200:]}"
    )


def test_recovery_re_arms_de_dup_flag_for_next_episode() -> None:
    proc = _run_harness_process("recovery_re_arms_de_dup_flag")
    data = _unwrap(
        _parse_harness_result(proc, "recovery_re_arms_de_dup_flag"),
        "recovery_re_arms_de_dup_flag",
    )
    episode1 = data["episode1"]
    post_recovery = data["post_recovery"]
    episode2 = data["episode2"]
    # Episode 1: threshold reached → flag set.
    assert episode1["emitted"] is True
    # After BACKLOG_RECOVERY_TICKS consecutive below-cap ticks (hysteresis
    # re-arm window), counter is back at 0 and the dedup flag has cleared.
    assert post_recovery["counter"] == 0, (
        f"after the hysteresis re-arm window, counter must be 0; got {post_recovery['counter']}"
    )
    assert post_recovery["emitted"] is False, (
        f"after BACKLOG_RECOVERY_TICKS consecutive below-cap ticks the dedup flag must clear; "
        f"got emitted={post_recovery['emitted']}"
    )
    # Episode 2: flag must re-fire. If the recovery had failed to clear the
    # flag, episode 2 would reach threshold with emitted=True already set by
    # episode 1 — visually identical to the true re-fire, which would mask a
    # de-dup-flag-stuck regression. The `post_recovery` assertion above closes
    # that gap.
    assert episode2["emitted"] is True
    stderr = proc.stderr.decode("utf-8", "replace")
    assert stderr.count(BACKLOG_WARNING_PREFIX) == 2, (
        "recovery must re-arm the next episode so the warning emits once per "
        f"episode. stderr tail: {stderr[-1200:]}"
    )


def test_below_watermark_suppresses_warning_even_at_threshold() -> None:
    data = _unwrap(
        _run_harness("below_watermark_suppresses_warning"),
        "below_watermark_suppresses_warning",
    )
    # Counter climbs through the full tick_count even though the buffer size is
    # at the watermark (not strictly greater). The warning must not emit.
    assert int(data["counter"]) == int(data["tick_count"])
    assert bool(data["emitted"]) is False, (
        f"warning must require `buffered_after > BACKLOG_WATERMARK_PACKETS` (strict); "
        f"emit at the watermark is a silent regression. emitted={data['emitted']}"
    )


def test_reset_subscription_runtime_clears_saturation_state() -> None:
    data = _unwrap(_run_harness("reset_clears_saturation_state"), "reset_clears_saturation_state")
    pre_reset = data["pre_reset"]
    post_reset = data["post_reset"]
    assert pre_reset["emitted"] is True
    assert pre_reset["counter"] > 0
    assert post_reset["counter"] == 0, (
        f"_reset_subscription_runtime must clear `_consecutive_saturated_ticks`; "
        f"got counter={post_reset['counter']}"
    )
    assert post_reset["emitted"] is False, (
        f"_reset_subscription_runtime must clear `_backlog_warning_emitted`; "
        f"got emitted={post_reset['emitted']}"
    )


def test_retry_disconnect_clears_saturation_state_before_next_transport() -> None:
    data = _unwrap(
        _run_harness("retry_disconnect_clears_saturation_state"),
        "retry_disconnect_clears_saturation_state",
    )
    assert data["current_state"] == "Degraded"
    assert int(data["counter"]) == 0, (
        "retry scheduling must clear `_consecutive_saturated_ticks` so the next "
        f"transport starts a fresh episode. got counter={data['counter']}"
    )
    assert bool(data["emitted"]) is False, (
        "retry scheduling must clear `_backlog_warning_emitted` so the next "
        f"episode can emit a fresh warning. got emitted={data['emitted']}"
    )
    assert bool(data["socket_cleared"]) is True
    assert float(data["next_retry_at_seconds"]) >= 0.0


def test_teardown_tick_treated_as_not_saturated() -> None:
    data = _unwrap(
        _run_harness("teardown_treated_as_not_saturated"),
        "teardown_treated_as_not_saturated",
    )
    assert int(data["pre_teardown_counter"]) > 0, (
        "harness should have primed the counter before the teardown tick"
    )
    assert int(data["post_teardown_counter"]) == 0, (
        f"a teardown tick (saturated_this_tick=false) must snap the counter to 0; "
        f"got {data['post_teardown_counter']}"
    )
    assert bool(data["post_teardown_emitted"]) is False


def test_pre_teardown_flush_fires_above_half_threshold() -> None:
    proc = _run_harness_process("pre_teardown_flush_fires_above_half_threshold")
    data = _unwrap(
        _parse_harness_result(proc, "pre_teardown_flush_fires_above_half_threshold"),
        "pre_teardown_flush_fires_above_half_threshold",
    )
    assert int(data["snapshot"]) > 0
    # The flush helper intentionally does NOT set `_backlog_warning_emitted`
    # (that would bleed across the degraded-reconnect cycle — see the helper's
    # comment). The stderr count is the real observable for emission.
    assert bool(data["live_flag"]) is False, (
        "flush helper must not mutate `_backlog_warning_emitted`; the flag must stay "
        f"whatever the teardown reset left it (false). got live_flag={data['live_flag']}"
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    assert stderr.count("saturation symptom at teardown") == 1, (
        "flush must emit exactly one push_warning containing "
        f"'saturation symptom at teardown'. stderr tail: {stderr[-1200:]}"
    )


def _read_saturation_threshold_constant() -> int:
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
    import re as _re

    match = _re.search(
        r"^const\s+BACKLOG_SATURATION_TICKS\s*:\s*int\s*=\s*(\d+)",
        service_src,
        _re.MULTILINE,
    )
    assert match is not None, (
        "gdscript_connection_service.gd must still declare BACKLOG_SATURATION_TICKS"
    )
    return int(match.group(1))


def test_pre_teardown_flush_suppressed_below_half_threshold() -> None:
    proc = _run_harness_process("pre_teardown_flush_suppressed_below_half")
    data = _unwrap(
        _parse_harness_result(proc, "pre_teardown_flush_suppressed_below_half"),
        "pre_teardown_flush_suppressed_below_half",
    )
    half_threshold = _read_saturation_threshold_constant() // 2
    assert int(data["snapshot"]) < half_threshold, (
        f"harness should have seeded a snapshot below the half-threshold floor ({half_threshold}); "
        f"got {data['snapshot']}"
    )
    assert bool(data["emitted"]) is False, (
        "_check_and_emit_pre_teardown_flush must suppress when snapshot is below "
        f"the half-threshold floor; got emitted={data['emitted']}"
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "saturation symptom at teardown" not in stderr, (
        "no flush warning should appear on stderr when the snapshot is below the floor. "
        f"stderr tail: {stderr[-1200:]}"
    )


def test_pre_teardown_flush_suppressed_when_already_emitted() -> None:
    proc = _run_harness_process("pre_teardown_flush_suppressed_when_already_emitted")
    data = _unwrap(
        _parse_harness_result(proc, "pre_teardown_flush_suppressed_when_already_emitted"),
        "pre_teardown_flush_suppressed_when_already_emitted",
    )
    # The flush checks the pre-dispatch flag snapshot — when it was already set,
    # the flush suppresses itself and never touches the live flag.
    assert bool(data["emitted"]) is False, (
        "flush must not touch `_backlog_warning_emitted` when the pre-dispatch snapshot "
        f"shows a warning was already emitted; got emitted={data['emitted']}"
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "saturation symptom at teardown" not in stderr, (
        "flush warning must not appear when the pre-dispatch flag snapshot was true. "
        f"stderr tail: {stderr[-1200:]}"
    )


def test_hysteresis_single_recovery_does_not_rearm_de_dup_flag() -> None:
    proc = _run_harness_process("hysteresis_single_recovery_does_not_rearm")
    data = _unwrap(
        _parse_harness_result(proc, "hysteresis_single_recovery_does_not_rearm"),
        "hysteresis_single_recovery_does_not_rearm",
    )
    assert data["after_warn_emitted"] is True
    assert data["post_single_recovery_emitted"] is True, (
        "a single below-cap tick must NOT re-arm the dedup flag under hysteresis; "
        f"got post_single_recovery_emitted={data['post_single_recovery_emitted']}"
    )
    assert data["second_episode"]["emitted"] is True
    stderr = proc.stderr.decode("utf-8", "replace")
    # Exactly ONE warning across the whole session — flapping produces no spam.
    assert stderr.count(BACKLOG_WARNING_PREFIX) == 1, (
        "flapping workload must NOT produce a second warning when recovery is only one "
        f"tick long. stderr tail: {stderr[-1200:]}"
    )


def test_hysteresis_n_consecutive_recoveries_rearm_de_dup_flag() -> None:
    proc = _run_harness_process("hysteresis_n_recoveries_rearm")
    data = _unwrap(
        _parse_harness_result(proc, "hysteresis_n_recoveries_rearm"),
        "hysteresis_n_recoveries_rearm",
    )
    assert data["after_warn_emitted"] is True
    assert data["pre_rearm_emitted"] is True, (
        "dedup flag must still be set after only BACKLOG_RECOVERY_TICKS - 1 below-cap ticks; "
        f"got pre_rearm_emitted={data['pre_rearm_emitted']}"
    )
    assert data["post_rearm_emitted"] is False, (
        "the full BACKLOG_RECOVERY_TICKS hysteresis window must clear the dedup flag; "
        f"got post_rearm_emitted={data['post_rearm_emitted']}"
    )
    assert data["second_episode"]["emitted"] is True
    stderr = proc.stderr.decode("utf-8", "replace")
    # Two warnings total — the first episode and the second after full hysteresis.
    assert stderr.count(BACKLOG_WARNING_PREFIX) == 2, (
        "full hysteresis recovery must re-arm the next episode so a second warning fires. "
        f"stderr tail: {stderr[-1200:]}"
    )


def test_mid_drain_teardown_drops_remaining_packets_and_disconnects_cleanly() -> None:
    payloads = [
        _build_initial_connection_frame("first"),
        b"\x00",
        _build_initial_connection_frame("third"),
        _build_initial_connection_frame("fourth"),
    ]
    with _FixtureWebSocketServer(payloads) as server:
        proc = _run_harness_process(
            "mid_drain_teardown_disconnects_and_drops_remaining_packets",
            [str(server.port)],
        )
        data = _unwrap(
            _parse_harness_result(proc, "mid_drain_teardown_disconnects_and_drops_remaining_packets"),
            "mid_drain_teardown_disconnects_and_drops_remaining_packets",
        )
    assert data["protocol_kinds"] == ["InitialConnection", "ProtocolError"], (
        "mid-drain teardown harness must dispatch the first valid frame and the "
        f"second ProtocolError frame before disconnect. got {data['protocol_kinds']}"
    )
    assert int(data["initial_connection_messages"]) == 1
    assert bool(data["reached_disconnected"]) is True, (
        "service must reach STATE_DISCONNECTED after the mid-drain ProtocolError. "
        f"got reached_disconnected={data['reached_disconnected']}"
    )
    assert bool(data["socket_cleared"]) is True
    assert data["current_state"] == "Disconnected", (
        "mid-drain teardown must leave the service in STATE_DISCONNECTED. "
        f"got {data['current_state']}"
    )
    stderr = proc.stderr.decode("utf-8", "replace")
    assert "SCRIPT ERROR" not in stderr, stderr
    assert "Assertion failed" not in stderr, stderr
