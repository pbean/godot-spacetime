#!/usr/bin/env python3
"""
check-retro-debt.py

Structural retro-debt gate for the bmad-create-story workflow.

Scans the deferred-work tracker
(`_bmad-output/implementation-artifacts/deferred-work.md`) for OPEN,
programmatically-trackable retro debt and signals create-story via the
exit code so the workflow can WARN-AND-CONFIRM before its first prompt.

Detection discipline (machine-parseable marker convention, documented in
the tracker header):
  - A line is OPEN debt only if it contains the literal token
    `❌ Still outstanding` AND that marker is not struck through.
    Strikethrough is MARKER-SCOPED: the line is resolved only when the
    `❌ Still outstanding` token itself sits inside a `~~…~~` span (the
    fully-wrapped resolved row). An incidental, unrelated `~~…~~` span
    elsewhere on an otherwise-OPEN line does NOT resolve it — the gate
    fails closed on a real OPEN debt line that merely quotes some struck
    text alongside the live marker.
  - A line that additionally contains `Not programmatically closable`
    is EXEMPT (permanently human-blocked, e.g. the D3 Godot-editor
    verification). Exempt lines never force the confirm — otherwise the
    permanently-open D3 item would brick create-story forever.
  - `❌ Rejected` / `❌ NOT DONE` and other bare-`❌` phrasings are NOT
    counted; only the full `❌ Still outstanding` token is.

Only the single tracker file is read. The archive
(`deferred-work-archive.md`) and the `epic-*-retro-*.md` snapshots are
known-stale and full of `❌ Rejected` / `❌ NOT DONE` false positives, so
they are never consulted.

Usage:
    python3 check-retro-debt.py [path/to/deferred-work.md]

Exit codes:
    0 — no OPEN debt (only exempt human-blocked debt, or none, or the
        tracker is absent); create-story is NOT forced to confirm.
    1 — at least one OPEN, non-exempt debt line; create-story must
        require a typed acknowledgment before its first prompt.
"""

from __future__ import annotations

import sys
from pathlib import Path

OPEN_DEBT_TOKEN = "❌ Still outstanding"
EXEMPT_TOKEN = "Not programmatically closable"
STRIKETHROUGH_MARKER = "~~"

# Resolved relative to the repo root, derived from this script's own path:
# scripts/check-retro-debt.py -> parents[1] is the repo root.
DEFAULT_TRACKER_RELATIVE = Path(
    "_bmad-output/implementation-artifacts/deferred-work.md"
)

LOUD_HEADER = "=== UNRESOLVED RETRO DEBT — create-story gate ==="


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_tracker_path() -> Path:
    return repo_root() / DEFAULT_TRACKER_RELATIVE


def _marker_is_struck_through(line: str) -> bool:
    """True only when EVERY `❌ Still outstanding` marker on the line is struck.

    Strikethrough detection is MARKER-SCOPED, not line-scoped: we walk the
    `~~`-delimited spans in markdown order (open, close, open, close, …) and
    report struck-through only when each marker's character offset falls inside
    a closed span. An incidental `~~…~~` span elsewhere on an otherwise-OPEN
    line therefore does NOT resolve it — the gate fails closed. A fully-wrapped
    `~~… ❌ Still outstanding …~~` row IS resolved, matching the frozen matrix.

    The tracker convention is one debt item per line, but a malformed line may
    carry more than one marker (e.g. a struck restatement followed by a live
    one). We fail closed: if ANY marker occurrence sits outside every closed
    span, the line is treated as OPEN. Only a line whose every marker is struck
    counts as resolved.
    """
    if OPEN_DEBT_TOKEN not in line:
        return False
    # Collect `~~` delimiter positions; they pair up open/close in document order.
    delimiters: list[int] = []
    search_from = 0
    while True:
        found = line.find(STRIKETHROUGH_MARKER, search_from)
        if found == -1:
            break
        delimiters.append(found)
        search_from = found + len(STRIKETHROUGH_MARKER)
    # Consume delimiters two at a time as [open, close) spans; an unpaired
    # trailing `~~` opens no closed span, so any marker after it stays OPEN.
    closed_spans: list[tuple[int, int]] = []
    for i in range(0, len(delimiters) - 1, 2):
        span_open = delimiters[i]
        span_close = delimiters[i + 1] + len(STRIKETHROUGH_MARKER)
        closed_spans.append((span_open, span_close))
    # Walk every marker occurrence; if any one is outside all closed spans the
    # line carries live OPEN debt and must NOT be treated as resolved.
    marker_at = line.find(OPEN_DEBT_TOKEN)
    while marker_at != -1:
        if not any(open_ <= marker_at < close_ for open_, close_ in closed_spans):
            return False
        marker_at = line.find(OPEN_DEBT_TOKEN, marker_at + len(OPEN_DEBT_TOKEN))
    return True


def find_open_debt(text: str) -> list[str]:
    """Return the OPEN, non-exempt debt lines in ``text``.

    A line is OPEN debt when it carries the literal `❌ Still outstanding`
    token, that marker is not struck through (see ``_marker_is_struck_through``
    — only a `~~…~~` span wrapping the marker resolves it), and it is not
    flagged `Not programmatically closable` (human-blocked items are exempt so
    the gate never bricks on D3).
    """
    open_lines: list[str] = []
    for raw_line in text.splitlines():
        if OPEN_DEBT_TOKEN not in raw_line:
            continue
        if _marker_is_struck_through(raw_line):
            # Resolved items wrap the marker in ~~…~~; treat as closed.
            continue
        if EXEMPT_TOKEN in raw_line:
            # Permanently human-blocked (e.g. D3) — never forces the confirm.
            continue
        open_lines.append(raw_line.strip())
    return open_lines


def has_exempt_debt(text: str) -> bool:
    """True if any line is an exempt (human-blocked) `❌ Still outstanding` line."""
    for raw_line in text.splitlines():
        if OPEN_DEBT_TOKEN not in raw_line:
            continue
        if _marker_is_struck_through(raw_line):
            continue
        if EXEMPT_TOKEN in raw_line:
            return True
    return False


def _ensure_utf8_stdout() -> None:
    """Reconfigure stdout to UTF-8 once so emoji markers survive a cp1252 console.

    Hoisted out of ``_print`` (called once at ``main`` entry) so it does not
    mutate global stdout state on every emitted line.
    """
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")


def _print(message: str) -> None:
    """Write a single line to stdout (UTF-8 already armed by ``_ensure_utf8_stdout``)."""
    sys.stdout.write(message + "\n")


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdout()
    args = sys.argv[1:] if argv is None else argv
    tracker_path = Path(args[0]) if args else default_tracker_path()

    if not tracker_path.exists():
        _print(f"retro-debt gate: deferred-work tracker not found at {tracker_path}")
        _print("retro-debt gate: absence is not debt — proceeding.")
        return 0

    try:
        text = tracker_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        # An unreadable / non-UTF-8 tracker is not, in itself, retro debt; never
        # brick. UnicodeDecodeError is a UnicodeError subclass, so this catches
        # both a genuine I/O failure and a tracker that is not valid UTF-8.
        _print(f"retro-debt gate: could not read {tracker_path}: {exc}")
        _print("retro-debt gate: proceeding (read failure is not debt).")
        return 0

    open_lines = find_open_debt(text)

    if open_lines:
        _print(LOUD_HEADER)
        _print(
            f"{len(open_lines)} unresolved, programmatically-trackable retro "
            "debt item(s) detected in:"
        )
        _print(f"  {tracker_path}")
        _print("")
        for line in open_lines:
            _print(f"  • {line}")
        _print("")
        _print(
            "create-story should relay these to the user and require an "
            "explicit typed acknowledgment before continuing (WARN-AND-CONFIRM)."
        )
        return 1

    if has_exempt_debt(text):
        _print(
            "retro-debt gate: only human-blocked debt remains (D3) — proceeding."
        )
        return 0

    _print("retro-debt gate: no unresolved retro debt — proceeding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
