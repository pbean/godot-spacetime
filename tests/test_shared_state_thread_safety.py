"""
Cross-cutting shared-state thread-safety static guardrails.

These assertions intentionally stay structural — they pin the documented
concurrency contract (named gate `lock`s + `volatile` reference fence) to the
five shared-mutable fields the runtime-telemetry-hardening review cycle
bundled together:

  * ``SpacetimeLog._sink`` — ``volatile`` reference fence.
  * ``SpacetimeConnectionService._subscriptionRegistry``
  * ``SpacetimeConnectionService._pendingReplacements``
  * ``SpacetimeConnectionService._reconnectPolicy``
  * ``SpacetimeConnectionService.CurrentIdentity`` (backing field with
    locked accessors)

All four ``SpacetimeConnectionService`` fields share a single
``_connectionStateGate``; signal/event emission stays outside every lock
scope (snapshot-then-emit). The companion ``## Threading Model`` section in
``docs/runtime-boundaries.md`` documents the contract.

This file mirrors the structure of
``tests/test_story_runtime_telemetry_hardening.py``: a per-file ``_read()``
helper plus one test per protected field plus a docs-section test.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LOG_REL = "addons/godot_spacetime/src/Public/Logging/SpacetimeLog.cs"
SERVICE_REL = "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
DOCS_REL = "docs/runtime-boundaries.md"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_spacetimelog_sink_carries_volatile_reference_fence() -> None:
    content = _read(LOG_REL)
    # The static backing field must declare ``volatile`` so that a reader
    # picking up _sink from a Task.ContinueWith(..., TaskScheduler.Default)
    # continuation observes the publish/acquire fence.
    assert re.search(
        r"private\s+static\s+volatile\s+ILogSink\s+_sink\s*=",
        content,
    ), (
        f"{LOG_REL} must declare `_sink` as `private static volatile ILogSink _sink = ...`. "
        "The volatile keyword is the reference-fence required by the threading-model contract."
    )

    # The setter null-coalesce contract and SafeWrite local-snapshot pattern
    # must be preserved — volatile only adds the fence; it does not replace
    # the snapshot pattern that protects against between-read teardown.
    assert "?? GodotConsoleLogSink.Instance" in content, (
        f"{LOG_REL} setter must keep the `?? GodotConsoleLogSink.Instance` null-coalesce contract."
    )
    assert "var sink = _sink;" in content, (
        f"{LOG_REL} SafeWrite must keep the `var sink = _sink;` local-snapshot pattern."
    )


def test_connection_state_gate_is_declared() -> None:
    content = _read(SERVICE_REL)
    assert re.search(
        r"private\s+readonly\s+object\s+_connectionStateGate\s*=\s*new\s*\(\s*\)\s*;",
        content,
    ), (
        f"{SERVICE_REL} must declare a `private readonly object _connectionStateGate = new();` "
        "next to the existing `_pendingUnsubscribeThenCallbacksGate`. This is the named gate "
        "covering all four protected SpacetimeConnectionService fields."
    )


def test_subscription_registry_accesses_are_locked() -> None:
    content = _read(SERVICE_REL)
    # Every textual access of `_subscriptionRegistry.` must appear inside a
    # `lock (_connectionStateGate) { ... }` scope. The structural test counts
    # access tokens against lock-bracketed regions and asserts none escape.
    _assert_field_locked(content, "_subscriptionRegistry")


def test_pending_replacements_accesses_are_locked() -> None:
    content = _read(SERVICE_REL)
    _assert_field_locked(content, "_pendingReplacements")


def test_reconnect_policy_accesses_are_locked() -> None:
    content = _read(SERVICE_REL)
    _assert_field_locked(content, "_reconnectPolicy")


def test_current_identity_is_backing_field_with_locked_accessors() -> None:
    content = _read(SERVICE_REL)
    # The auto-property must be replaced with a manual property over a
    # backing field, both of whose accessors acquire the gate. The test
    # pins the backing-field name and the locked-accessor body shape.
    assert "private Identity? _currentIdentity" in content, (
        f"{SERVICE_REL} must declare a `_currentIdentity` backing field for CurrentIdentity. "
        "An auto-property cannot carry locked accessors."
    )
    # The CurrentIdentity property must remain on the type (no rename) and
    # must contain a get/set body that locks `_connectionStateGate`.
    assert re.search(
        r"internal\s+Identity\?\s+CurrentIdentity\s*\{[^}]*lock\s*\(\s*_connectionStateGate\s*\)",
        content,
        re.DOTALL,
    ), (
        f"{SERVICE_REL} CurrentIdentity must be a manual property whose getter and setter "
        "acquire `_connectionStateGate`."
    )

    # Every textual access of `_currentIdentity` (other than the declaration)
    # must appear inside a lock scope.
    _assert_field_locked(content, "_currentIdentity", skip_declaration=True)


def test_no_signal_emission_inside_connection_state_lock() -> None:
    content = _strip_comments(_read(SERVICE_REL))
    # Snapshot-then-emit contract: no signal/event Invoke may appear inside
    # a `lock (_connectionStateGate)` scope. Walk every such block and
    # assert it carries no `?.Invoke(`. `_stateMachine.Transition(` is also
    # forbidden because the state machine emits `StateChanged?.Invoke` indirectly;
    # putting it inside the lock lets a user signal handler re-enter under the
    # held gate.
    for block in _iter_lock_bodies(content, "_connectionStateGate"):
        for forbidden in ("?.Invoke(", ".Invoke(", "_stateMachine.Transition("):
            assert forbidden not in block, (
                f"{SERVICE_REL}: forbidden token {forbidden!r} detected inside a "
                "`lock (_connectionStateGate)` scope. The threading-model contract "
                "requires snapshot-inside, release, then emit. "
                f"Offending block:\n{block}"
            )


def test_runtime_boundaries_doc_has_threading_model_section() -> None:
    content = _read(DOCS_REL)
    assert "## Threading Model" in content, (
        f"{DOCS_REL} must append a `## Threading Model` section enumerating the protected fields, "
        "the `_connectionStateGate` ownership rule, the `volatile _sink` contract, and the "
        "snapshot-then-emit pattern."
    )

    # The section must enumerate the five protected fields explicitly so
    # reviewers can locate the contract from the docs alone.
    threading_section = content.split("## Threading Model", 1)[1]
    for token in (
        "_connectionStateGate",
        "_subscriptionRegistry",
        "_pendingReplacements",
        "_reconnectPolicy",
        "CurrentIdentity",
        "_sink",
        "volatile",
        "snapshot",
    ):
        assert token in threading_section, (
            f"{DOCS_REL} `## Threading Model` section must mention {token!r} so the contract "
            "is discoverable from docs alone."
        )

    # The section must link back to runtime-telemetry-hardening for the
    # `_stats` reference-return scope-precluded note.
    assert "runtime-telemetry-hardening" in threading_section or "_stats" in threading_section, (
        f"{DOCS_REL} `## Threading Model` section must reference the runtime-telemetry-hardening "
        "spec / `_stats` reference-return exclusion so future readers know why telemetry is out of "
        "scope here."
    )


# --- helpers ---------------------------------------------------------------


def _iter_lock_bodies(content: str, gate_name: str):
    """Yield every body (brace-block or single-statement) of a `lock (gate_name) ...` scope."""
    for lo, hi in _lock_ranges(content, gate_name):
        yield content[lo:hi]


def _lock_ranges(content: str, gate_name: str) -> list[tuple[int, int]]:
    """Return character ranges covering each `lock (gate_name) ...` body.

    Handles two forms:
      * ``lock (gate) { ... }`` (brace-balanced block body)
      * ``lock (gate) statement;`` (single-statement body terminated by ``;``)
    """
    pattern = re.compile(r"lock\s*\(\s*" + re.escape(gate_name) + r"\s*\)\s*")
    ranges: list[tuple[int, int]] = []
    for m in pattern.finditer(content):
        i = m.end()
        if i >= len(content):
            continue
        if content[i] == "{":
            start = i + 1
            depth = 1
            j = start
            while j < len(content) and depth > 0:
                ch = content[j]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                j += 1
            if depth == 0:
                ranges.append((start, j - 1))
        else:
            # Single-statement form: scan forward to the next ';' at depth 0,
            # honoring any nested `(...)` or `[...]` and string literals.
            start = i
            depth_paren = 0
            depth_brack = 0
            in_string = False
            in_char = False
            j = start
            while j < len(content):
                ch = content[j]
                if in_string:
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == '"':
                        in_string = False
                elif in_char:
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == "'":
                        in_char = False
                else:
                    if ch == '"':
                        in_string = True
                    elif ch == "'":
                        in_char = True
                    elif ch == "(":
                        depth_paren += 1
                    elif ch == ")":
                        depth_paren -= 1
                    elif ch == "[":
                        depth_brack += 1
                    elif ch == "]":
                        depth_brack -= 1
                    elif ch == ";" and depth_paren == 0 and depth_brack == 0:
                        ranges.append((start, j))
                        break
                j += 1
    return ranges


def _strip_comments(content: str) -> str:
    """Replace ``// line`` and ``/* block */`` comments with spaces so structural
    scans cannot trip on identifiers that only appear inside commentary."""
    out: list[str] = []
    i = 0
    n = len(content)
    in_string = False
    in_char = False
    while i < n:
        ch = content[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(content[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
        elif in_char:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(content[i + 1])
                i += 2
                continue
            if ch == "'":
                in_char = False
            i += 1
        else:
            if ch == '"':
                in_string = True
                out.append(ch)
                i += 1
            elif ch == "'":
                in_char = True
                out.append(ch)
                i += 1
            elif ch == "/" and i + 1 < n and content[i + 1] == "/":
                # line comment — replace with spaces up to newline
                j = content.find("\n", i)
                if j < 0:
                    j = n
                out.append(" " * (j - i))
                i = j
            elif ch == "/" and i + 1 < n and content[i + 1] == "*":
                # block comment — replace with spaces up to */
                j = content.find("*/", i + 2)
                if j < 0:
                    j = n
                else:
                    j += 2
                out.append(" " * (j - i))
                i = j
            else:
                out.append(ch)
                i += 1
    return "".join(out)


def _assert_field_locked(content: str, field_name: str, *, skip_declaration: bool = False) -> None:
    """
    Assert every reference to ``field_name`` (as a member-access or method-call
    site, e.g. ``field.Member``, ``field.Method(...)``, ``field = ...``,
    ``field;``) lies inside a ``lock (_connectionStateGate)`` scope.

    The declaration line(s) of the field itself are excluded — we only fence
    *use* sites, not the declaration. Comments are stripped before scanning so
    that documentation references to a field name do not generate false
    positives.
    """
    content = _strip_comments(content)

    # Build the set of (start, end) char ranges that belong to a
    # `lock (_connectionStateGate) ...` body (block or single statement).
    gate_ranges = _lock_ranges(content, "_connectionStateGate")

    def _in_gate(pos: int) -> bool:
        return any(lo <= pos < hi for lo, hi in gate_ranges)

    # Find every textual access to `field_name`, allowing for `.`, ` `, `=`,
    # `(`, `;`, `,`, `)` follow-tokens. Skip the declaration site(s).
    # Lookahead covers the common access shapes:
    #   `.`  member access     `_field.Member`
    #   ` `  whitespace        `_field = value`
    #   `=`  assignment        `_field=value`
    #   `;`  end of expression `return _field;`
    #   `,`  argument list     `Foo(_field, x)`
    #   `)`  closing paren     `Foo(_field)`
    #   `[`  indexer access    `_field[key]` (e.g. `_pendingReplacements[k] = v`)
    access_pattern = re.compile(r"\b" + re.escape(field_name) + r"(?=[\.\s=;,\)\[])")

    # Identify declaration-line offsets to skip (for both `private ... field;`
    # and `private ... field = new ...;` forms, plus the manual-property form
    # for the backing field).
    declaration_offsets: set[int] = set()
    if skip_declaration:
        decl_pattern = re.compile(
            r"private\s+(?:readonly\s+|static\s+|volatile\s+)*[\w\?<>,\s]+?\s+"
            + re.escape(field_name)
            + r"\b"
        )
        for m in decl_pattern.finditer(content):
            # mark the position of the field-name token within the declaration
            field_pos = content.find(field_name, m.start(), m.end())
            if field_pos >= 0:
                declaration_offsets.add(field_pos)
    else:
        # default: skip the single `private ... field` declaration line, which
        # ends in `= new ...();` and contains the field name once
        decl_pattern = re.compile(
            r"private\s+(?:readonly\s+|static\s+|volatile\s+)*[\w\?<>,\s]+?\s+"
            + re.escape(field_name)
            + r"\s*=\s*new"
        )
        for m in decl_pattern.finditer(content):
            field_pos = content.find(field_name, m.start(), m.end())
            if field_pos >= 0:
                declaration_offsets.add(field_pos)

    unlocked: list[str] = []
    for m in access_pattern.finditer(content):
        if m.start() in declaration_offsets:
            continue
        if _in_gate(m.start()):
            continue
        # Capture surrounding context for the failure message
        line_start = content.rfind("\n", 0, m.start()) + 1
        line_end = content.find("\n", m.end())
        if line_end < 0:
            line_end = len(content)
        line_no = content.count("\n", 0, m.start()) + 1
        unlocked.append(f"line {line_no}: {content[line_start:line_end].strip()}")

    assert not unlocked, (
        f"{SERVICE_REL}: every access of `{field_name}` must be inside a "
        f"`lock (_connectionStateGate)` scope. {len(unlocked)} unlocked access site(s) found:\n"
        + "\n".join(unlocked)
    )
