"""In-engine behavioral proof for the ConnectionStateMachine.CurrentStatus fence.

The volatile-fence *contract* is pinned structurally by
``tests/test_shared_state_thread_safety.py``. This module supplies the
*behavioral* proof the spec calls for: a freshly constructed machine reports
``Disconnected``; ``Transition`` round-trips each new state through the fenced
field and fires ``StateChanged`` with the post-transition status; an illegal
transition throws and leaves ``CurrentStatus`` unchanged.

It MUST run inside the Godot runtime rather than the plain xUnit
``GodotSpacetime.Tests`` host. ``CurrentStatus`` is a ``ConnectionStatus``,
which derives from ``Godot.RefCounted``; constructing a ``RefCounted`` subclass
without the Godot engine bootstrap hard-crashes the process (SIGSEGV / exit
139) because GodotSharp's native interop pointers are null. Empirically
verified against the pinned GodotSharp 4.6.1: a standalone ``new
ConnectionStatus(...)`` prints up to the call site, then dies with no managed
exception and exit 139.

The proof therefore runs as a headless ``godot-mono`` scene
(``tests/godot_integration/ConnectionStateMachineFenceRunner.cs`` +
``connection_state_machine_fence.tscn``) and is gated/skipped when no Godot Mono
binary is discoverable, matching the repo's other godot_integration harnesses.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import os

import pytest

from tests.fixtures.spacetime_runtime import probe_godot_binary

ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tests" / "godot_integration" / "ConnectionStateMachineFenceRunner.cs"
SCENE_PATH = "res://tests/godot_integration/connection_state_machine_fence.tscn"
PROJECT_CSPROJ = ROOT / "godot-spacetime.csproj"

EVENT_PREFIX = "E2E-EVENT "

EXPECTED_STEPS = (
    "initial_status_disconnected",
    "transition_connecting_round_trips",
    "transition_connected_round_trips",
    "state_changed_fired_with_post_transition_status",
    "illegal_transition_throws_and_status_unchanged",
)


def _parse_events(stdout: bytes) -> list[dict]:
    events: list[dict] = []
    for line in (stdout or b"").decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line.startswith(EVENT_PREFIX):
            continue
        try:
            events.append(json.loads(line[len(EVENT_PREFIX):]))
        except json.JSONDecodeError:
            continue
    return events


def _build_csharp() -> None:
    """Build the addon assembly so godot-mono can load the C# runner.

    Skips (rather than fails) when the .NET SDK or build is unavailable so the
    lane stays green on hosts without the .NET toolchain, matching the
    skip-safe posture of the other integration harnesses.
    """
    try:
        result = subprocess.run(
            ["dotnet", "build", str(PROJECT_CSPROJ)],
            cwd=ROOT,
            capture_output=True,
            timeout=600,
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        pytest.skip(f"dotnet SDK not runnable for the C# fence runner: {exc}")
    except subprocess.TimeoutExpired:
        pytest.skip("dotnet build of the addon assembly timed out")
    if result.returncode != 0:
        pytest.fail(
            "dotnet build of godot-spacetime.csproj failed before the fence runner could load.\n"
            f"stdout tail: {(result.stdout or b'').decode('utf-8', 'replace')[-1200:]}\n"
            f"stderr tail: {(result.stderr or b'').decode('utf-8', 'replace')[-1200:]}"
        )


def _run_fence_runner() -> list[dict]:
    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available: {godot_probe.reason}")

    if not RUNNER_PATH.exists():
        pytest.fail("ConnectionStateMachineFenceRunner.cs missing under tests/godot_integration/")

    _build_csharp()

    with tempfile.TemporaryDirectory(prefix="cstatus-fence-home-") as godot_home:
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
                SCENE_PATH,
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            timeout=120,
        )

    events = _parse_events(proc.stdout or b"")
    assert proc.returncode == 0, (
        f"ConnectionStateMachine fence runner exited with {proc.returncode}. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]} "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-1200:]}"
    )
    assert events, (
        "ConnectionStateMachine fence runner emitted no E2E-EVENT lines. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-1200:]} "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-1200:]}"
    )
    return events


def test_connection_state_machine_fence_behavioral_proof() -> None:
    events = _run_fence_runner()

    by_name = {e.get("name"): e for e in events if e.get("event") == "step"}
    for step in EXPECTED_STEPS:
        assert step in by_name, (
            f"fence runner did not emit the {step!r} step. Emitted steps: {sorted(by_name)}"
        )
        assert by_name[step].get("status") == "ok", (
            f"fence runner step {step!r} failed: {by_name[step]}"
        )

    done = [e for e in events if e.get("event") == "done"]
    assert done and done[-1].get("status") == "pass", (
        f"fence runner did not report a passing done event: {done}"
    )
