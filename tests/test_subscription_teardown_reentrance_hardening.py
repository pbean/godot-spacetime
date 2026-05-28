"""
Static guardrails for the subscription teardown/replace re-entry hardening (E7/E8).

These assertions stay structural — they pin the empirically-grounded contract that
makes the teardown paths safe against a synchronous SDK re-entry:

  * In ``Unsubscribe`` and ``OnSubscriptionError`` the registry
    ``Unregister(...)`` call sits inside a ``lock (_connectionStateGate)`` scope,
    so a synchronous ``OnSubscriptionError(sameHandle)`` re-entering from inside
    ``TryUnsubscribe`` finds the entry already removed (E7).
  * The ``_subscriptionAdapter.TryUnsubscribe(`` call never appears inside any
    ``lock (_connectionStateGate)`` scope (Always rule 2 / snapshot-then-emit).
  * ``SpacetimeSdkSubscriptionAdapter.TryUnsubscribe`` keeps its
    ``if (sdkSubscription == null) return false;`` null guard, which is what
    makes the E8 replace null-window safe with no SDK call.
  * The ``## Threading Model`` docs section records the re-entry / idempotency
    resolution.

The probe (Q5) settles E7: the pinned ClientSDK ``2.1.0`` handle is NOT
idempotent — a second ``Unsubscribe()``/``UnsubscribeThen()`` throws
``"Unsubscribe already called."``. The probe (Q6) settles E8: the local adapter
already returns ``false`` on null, so the null-window is documentation-only.

This file mirrors the structure of ``tests/test_shared_state_thread_safety.py``:
a per-file ``_read()`` helper, structural lock-scope scans, and a docs-section
test.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SERVICE_REL = "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
ADAPTER_REL = "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs"
DOCS_REL = "docs/runtime-boundaries.md"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_unsubscribe_unregister_is_gated_and_adapter_call_is_not() -> None:
    body = _strip_comments(_method_body(_read(SERVICE_REL), "public void Unsubscribe(SubscriptionHandle handle)"))
    _assert_unregister_gated(body, "Unsubscribe")
    _assert_try_unsubscribe_ungated(body, "Unsubscribe")


def test_on_subscription_error_unregister_is_gated_and_adapter_call_is_not() -> None:
    body = _strip_comments(
        _method_body(_read(SERVICE_REL), "void ISubscriptionEventSink.OnSubscriptionError(SubscriptionHandle handle, Exception error)")
    )
    _assert_unregister_gated(body, "OnSubscriptionError")
    _assert_try_unsubscribe_ungated(body, "OnSubscriptionError")


def test_adapter_keeps_null_guard() -> None:
    content = _read(ADAPTER_REL)
    # The Q6 resolution depends on this exact null short-circuit being the first
    # statement of TryUnsubscribe — it is what makes the E8 replace null-window
    # safe with no SDK call. Do NOT remove or weaken it.
    assert re.search(
        r"if\s*\(\s*sdkSubscription\s*==\s*null\s*\)\s*\n\s*return\s+false\s*;",
        content,
    ), (
        f"{ADAPTER_REL} TryUnsubscribe must keep its "
        "`if (sdkSubscription == null)\\n            return false;` null guard "
        "(the empirical Q6 basis for the E8 null-window safety)."
    )


def test_docs_threading_model_records_reentry_resolution() -> None:
    content = _read(DOCS_REL)
    assert "## Threading Model" in content, (
        f"{DOCS_REL} must keep the `## Threading Model` section."
    )
    section = content.split("## Threading Model", 1)[1]

    # The note must mention the re-entry resolution and the non-idempotent handle
    # behavior observed by the probe (Q5).
    assert "Unsubscribe already called." in section, (
        f"{DOCS_REL} `## Threading Model` must record that the 2.1.0 handle is NOT "
        'idempotent and throws "Unsubscribe already called." on a second call.'
    )
    for token in ("re-ent", "idempotent", "Unregister", "TryUnsubscribe"):
        assert token in section, (
            f"{DOCS_REL} `## Threading Model` must mention {token!r} so the E7/E8 "
            "re-entry / idempotency resolution is discoverable from docs alone."
        )

    # The note must also record the E8 null-window resolution.
    assert "sdkSubscription == null" in section, (
        f"{DOCS_REL} `## Threading Model` must record the E8 null-window resolution "
        "(`if (sdkSubscription == null) return false;`)."
    )


# --- helpers ---------------------------------------------------------------


def _assert_unregister_gated(body: str, method_label: str) -> None:
    gate_ranges = _lock_ranges(body, "_connectionStateGate")

    def _in_gate(pos: int) -> bool:
        return any(lo <= pos < hi for lo, hi in gate_ranges)

    matches = list(re.finditer(r"_subscriptionRegistry\.Unregister\s*\(", body))
    assert matches, (
        f"{SERVICE_REL} {method_label}: expected a `_subscriptionRegistry.Unregister(...)` call."
    )
    for m in matches:
        assert _in_gate(m.start()), (
            f"{SERVICE_REL} {method_label}: `_subscriptionRegistry.Unregister(...)` must sit inside a "
            "`lock (_connectionStateGate)` scope so a synchronous SDK re-entry's TryGetEntry finds "
            "the entry already removed (E7)."
        )


def _assert_try_unsubscribe_ungated(body: str, method_label: str) -> None:
    gate_ranges = _lock_ranges(body, "_connectionStateGate")

    def _in_gate(pos: int) -> bool:
        return any(lo <= pos < hi for lo, hi in gate_ranges)

    matches = list(re.finditer(r"_subscriptionAdapter\.TryUnsubscribe\s*\(", body))
    assert matches, (
        f"{SERVICE_REL} {method_label}: expected a `_subscriptionAdapter.TryUnsubscribe(...)` call."
    )
    for m in matches:
        assert not _in_gate(m.start()), (
            f"{SERVICE_REL} {method_label}: `_subscriptionAdapter.TryUnsubscribe(...)` must stay OUTSIDE "
            "every `lock (_connectionStateGate)` scope (Always rule 2 / snapshot-then-emit)."
        )


def _method_body(content: str, signature: str) -> str:
    """Return the brace-balanced body of the method whose signature line contains ``signature``."""
    idx = content.find(signature)
    assert idx >= 0, f"{SERVICE_REL}: could not locate method signature {signature!r}."
    brace = content.find("{", idx)
    assert brace >= 0, f"{SERVICE_REL}: could not locate opening brace for {signature!r}."
    depth = 0
    j = brace
    while j < len(content):
        ch = content[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[brace + 1 : j]
        j += 1
    raise AssertionError(f"{SERVICE_REL}: unbalanced braces for {signature!r}.")


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
                j = content.find("\n", i)
                if j < 0:
                    j = n
                out.append(" " * (j - i))
                i = j
            elif ch == "/" and i + 1 < n and content[i + 1] == "*":
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
