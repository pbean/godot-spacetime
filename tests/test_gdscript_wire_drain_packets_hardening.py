"""
Runtime coverage for spec-gdscript-wire-drain-packets-hardening.

Drives `_update_backlog_saturation` — the state-machine helper extracted from
`_drain_packets` — across tick sequences so the saturation counter + de-dup
flag transitions can be observed without faking Godot's strongly-typed
WebSocketPeer. The static-contract layer lives in `test_gdscript_wire_layouts.py`
(landmark strings, const declarations, field declarations, reset-site wiring);
this module provides the behavioral layer.

The teardown-drop contract itself is primarily enforced by the preamble
landmark test and the structural shape of `_update_backlog_saturation`'s
not-saturated branch. The `teardown_treated_as_not_saturated` mode below pins
the state-machine side of that contract: whatever call site enters the helper
with `saturated_this_tick == false` collapses the episode regardless of prior
counter, which is how `_drain_packets` reports a handler-induced teardown
(`_socket == null`) into the accounting.
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
HARNESS_RES = "res://tests/fixtures/gdscript_wire/service_drain_packets_harness.gd"


def _require_godot() -> str:
    godot = probe_godot_binary()
    if not godot.available:
        pytest.skip(f"godot-mono not available on PATH: {godot.reason}")
    return godot.path


def _run_harness(mode: str) -> dict:
    godot_path = _require_godot()
    proc = subprocess.run(
        [
            godot_path,
            "--headless",
            "--path",
            str(ROOT),
            "--script",
            HARNESS_RES,
            "--",
            mode,
        ],
        capture_output=True,
        timeout=HARNESS_TIMEOUT_SECONDS,
        cwd=str(ROOT),
    )
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
        f"harness emitted no WIRE-HARNESS event for mode={mode!r}\n"
        f"stdout:\n{stdout}\nstderr:\n{stderr}"
    )


def _unwrap(result: dict, mode: str) -> dict:
    assert result.get("ok") is True, (
        f"harness mode={mode!r} reported failure: {result.get('error', '<missing>')}"
    )
    return result["data"]


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
    data = _unwrap(
        _run_harness("sustained_saturation_single_warning"),
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


def test_recovery_re_arms_de_dup_flag_for_next_episode() -> None:
    data = _unwrap(_run_harness("recovery_re_arms_de_dup_flag"), "recovery_re_arms_de_dup_flag")
    episode1 = data["episode1"]
    post_recovery = data["post_recovery"]
    episode2 = data["episode2"]
    # Episode 1: threshold reached → flag set.
    assert episode1["emitted"] is True
    # Recovery tick: both fields clear.
    assert post_recovery["counter"] == 0, (
        f"recovery tick must zero the counter; got {post_recovery['counter']}"
    )
    assert post_recovery["emitted"] is False, (
        f"recovery tick must clear the de-dup flag; got emitted={post_recovery['emitted']}"
    )
    # Episode 2: flag must re-fire. If the recovery had failed to clear the
    # flag, episode 2 would reach threshold with emitted=True already set by
    # episode 1 — visually identical to the true re-fire, which would mask a
    # de-dup-flag-stuck regression. The `post_recovery` assertion above closes
    # that gap.
    assert episode2["emitted"] is True


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
