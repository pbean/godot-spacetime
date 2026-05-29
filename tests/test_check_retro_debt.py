"""
Detection tests for the bmad-create-story retro-debt gate
(`scripts/check-retro-debt.py`).

The helper lives outside `tests/` and its filename uses a hyphen, so it is
not importable by a normal `import`. It is loaded here via
`importlib.util.spec_from_file_location`, resolving `ROOT` with the same
`Path(__file__).resolve().parents[1]` idiom used in
`tests/test_gdscript_wire_layouts.py`.

Coverage:
  - the real `deferred-work.md` yields ZERO open lines (both `❌ Still
    outstanding` lines carry the `Not programmatically closable` exemption);
  - a synthetic untagged `❌ Still outstanding` line trips detection;
  - a fully-wrapped `~~… ❌ Still outstanding …~~` strikethrough line is NOT
    detected (the marker sits inside the struck span);
  - an OPEN `❌ Still outstanding` line that carries an incidental, unrelated
    `~~…~~` span elsewhere on the line IS still detected (marker-scoped
    strikethrough — the gate fails closed, not open);
  - `❌ Rejected` / bare-`❌` lines are NOT detected;
  - detection reads only the passed file (an archive/retro fixture full of
    `❌ Rejected` yields zero);
  - a missing path returns empty and the CLI exits 0.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check-retro-debt.py"
REAL_TRACKER = ROOT / "_bmad-output" / "implementation-artifacts" / "deferred-work.md"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_retro_debt", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


crd = _load_module()


def test_real_deferred_work_has_zero_open_debt():
    # Both `❌ Still outstanding` lines today carry `Not programmatically
    # closable` (D3), so the gate must see zero OPEN, non-exempt debt.
    text = REAL_TRACKER.read_text(encoding="utf-8")
    assert crd.find_open_debt(text) == []
    assert crd.has_exempt_debt(text) is True


def test_untagged_outstanding_line_is_detected():
    text = "❌ Still outstanding — synthetic untagged item that should trip the gate\n"
    open_lines = crd.find_open_debt(text)
    assert len(open_lines) == 1
    assert "synthetic untagged item" in open_lines[0]


def test_human_blocked_line_is_exempt():
    text = (
        "- **D3 — Manual editor verification** — ❌ Still outstanding. "
        "Not programmatically closable. Owner: Pinkyd.\n"
    )
    assert crd.find_open_debt(text) == []
    assert crd.has_exempt_debt(text) is True


def test_strikethrough_line_is_not_detected():
    text = "~~Old item — ❌ Still outstanding — now resolved~~\n"
    assert crd.find_open_debt(text) == []
    assert crd.has_exempt_debt(text) is False


def test_open_line_with_incidental_strikethrough_span_is_detected():
    # MARKER-SCOPED strikethrough: the `❌ Still outstanding` marker is OPEN
    # (outside any struck span); an incidental, unrelated `~~old approach~~`
    # span elsewhere on the line must NOT resolve it. The gate fails closed.
    text = "❌ Still outstanding. Replaces ~~old approach~~ but still broken.\n"
    open_lines = crd.find_open_debt(text)
    assert len(open_lines) == 1
    assert "still broken" in open_lines[0]


def test_open_line_with_trailing_struck_span_after_marker_is_detected():
    # The struck span sits entirely AFTER the live marker, so the marker is
    # still OPEN — must be reported.
    text = "❌ Still outstanding — see ~~the rejected fallback~~ for history.\n"
    assert len(crd.find_open_debt(text)) == 1


def test_multiple_markers_one_struck_one_open_is_detected():
    # MARKER-SCOPED, fail-closed across MULTIPLE markers on a (malformed) line:
    # the first `❌ Still outstanding` is struck (resolved restatement) but a
    # second one is OPEN. A single live marker must keep the line OPEN — the
    # gate must not fail open just because an earlier marker was resolved.
    text = (
        "~~OLD: ❌ Still outstanding (resolved)~~ — "
        "NEW: ❌ Still outstanding still broken\n"
    )
    open_lines = crd.find_open_debt(text)
    assert len(open_lines) == 1
    assert "still broken" in open_lines[0]


def test_fully_wrapped_marker_with_extra_span_stays_resolved():
    # The marker is inside the FIRST `~~…~~` span (fully wrapped / resolved);
    # a later incidental span does not change that. Stays uncounted.
    text = "~~done — ❌ Still outstanding — superseded~~ replaced by ~~note~~\n"
    assert crd.find_open_debt(text) == []


def test_bare_x_phrasings_are_not_detected():
    text = (
        "- ❌ Rejected — proposal turned down\n"
        "- ❌ NOT DONE — abandoned approach\n"
        "- ❌ some other bare marker line\n"
    )
    assert crd.find_open_debt(text) == []


def test_detection_reads_only_passed_file(tmp_path):
    # An archive/retro-style fixture full of `❌ Rejected` must contribute
    # zero detections when the CLI is pointed at it directly.
    archive = tmp_path / "deferred-work-archive.md"
    archive.write_text(
        "- ❌ Rejected — alt design A\n"
        "- ❌ NOT DONE — alt design B\n"
        "- ❌ Rejected — alt design C\n",
        encoding="utf-8",
    )
    assert crd.find_open_debt(archive.read_text(encoding="utf-8")) == []
    assert crd.main([str(archive)]) == 0


def test_cli_exits_nonzero_on_open_untagged_item(tmp_path):
    tracker = tmp_path / "deferred-work.md"
    tracker.write_text(
        "❌ Still outstanding — a brand new untagged item\n", encoding="utf-8"
    )
    assert crd.main([str(tracker)]) == 1


def test_cli_exits_zero_when_only_exempt(tmp_path):
    tracker = tmp_path / "deferred-work.md"
    tracker.write_text(
        "- D3 — ❌ Still outstanding. Not programmatically closable.\n",
        encoding="utf-8",
    )
    assert crd.main([str(tracker)]) == 0


def test_missing_path_returns_empty_and_exits_zero(tmp_path):
    missing = tmp_path / "does-not-exist.md"
    assert crd.main([str(missing)]) == 0
