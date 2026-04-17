"""
Spec G8: First-class Identity public type.

Structural contract tests covering:
- GodotSpacetime.Identity is a readonly struct in Public/Identity.cs, implements
  IEquatable<Identity>, declares == and != operators, overrides Equals(object)
  and GetHashCode, provides FromHexString and FromBytes factories (AC 2, 3).
- ToString() handles default(Identity) by returning 64 '0' characters (AC 3).
- FromHexString throws ArgumentException on bad input WITHOUT interpolating
  the raw input into the exception message (AC 6).
- ConnectionOpenedEvent carries a typed IdentityValue property alongside the
  unchanged Identity: string (AC 1, back-compat with Story 2.2).
- SpacetimeClient exposes a CurrentIdentity accessor that forwards to
  _connectionService.CurrentIdentity (AC 1, 4).
- SpacetimeConnectionService tracks CurrentIdentity, assigns it in
  HandleConnected via Identity.FromHexString, emits IdentityValue on the
  ConnectionOpenedEvent, and clears it to null in ResetDisconnectedSessionState
  and Disconnect (AC 1, 4).
- Public/Identity.cs contains no SpacetimeDB. references in non-comment code
  (AC 5, Story 1.3 isolation gate).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

IDENTITY_CS = "addons/godot_spacetime/src/Public/Identity.cs"
OPENED_EVENT_CS = "addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs"
CLIENT_CS = "addons/godot_spacetime/src/Public/SpacetimeClient.cs"
SERVICE_CS = "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _strip(rel: str) -> str:
    """Normalize whitespace for substring checks that should ignore formatting."""
    return re.sub(r"\s+", " ", _read(rel))


def _code_lines(text: str) -> str:
    """Strip C# comment forms so we can search non-comment code."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(
        ln for ln in text.splitlines()
        if not re.match(r"\s*(///|//)", ln)
    )


def _method_body(content: str, signature_marker: str) -> str:
    """Return the text of the first method whose signature contains signature_marker,
    from the opening brace through its matching closing brace."""
    idx = content.find(signature_marker)
    assert idx >= 0, f"signature marker {signature_marker!r} not found"
    brace_open = content.find("{", idx)
    assert brace_open >= 0
    depth = 0
    for i in range(brace_open, len(content)):
        ch = content[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[brace_open : i + 1]
    raise AssertionError("unterminated method body")


# ---------------------------------------------------------------------------
# Identity.cs — file existence + shape (AC 2, 3)
# ---------------------------------------------------------------------------

def test_identity_file_exists() -> None:
    assert (ROOT / IDENTITY_CS).is_file(), f"{IDENTITY_CS} must be created"


def test_identity_namespace_is_godotspacetime() -> None:
    content = _read(IDENTITY_CS)
    assert "namespace GodotSpacetime;" in content or "namespace GodotSpacetime\n{" in content, (
        "Identity must live in the top-level GodotSpacetime namespace"
    )


def test_identity_is_readonly_struct() -> None:
    content = _strip(IDENTITY_CS)
    assert re.search(r"public\s+readonly\s+(?:partial\s+)?struct\s+Identity\b", content), (
        "Identity must be declared as a public readonly struct (AC 2)"
    )


def test_identity_implements_iequatable() -> None:
    content = _strip(IDENTITY_CS)
    assert "IEquatable<Identity>" in content, (
        "Identity must implement IEquatable<Identity> (AC 2)"
    )


def test_identity_overrides_equals_object_and_gethashcode() -> None:
    content = _strip(IDENTITY_CS)
    assert re.search(r"public\s+override\s+bool\s+Equals\s*\(\s*object", content), (
        "Identity must override Equals(object?) (AC 2)"
    )
    assert re.search(r"public\s+override\s+int\s+GetHashCode\s*\(", content), (
        "Identity must override GetHashCode() (AC 2)"
    )


def test_identity_declares_equality_operators() -> None:
    content = _strip(IDENTITY_CS)
    assert re.search(r"public\s+static\s+bool\s+operator\s*==\s*\(\s*Identity", content), (
        "Identity must declare operator == (AC 2)"
    )
    assert re.search(r"public\s+static\s+bool\s+operator\s*!=\s*\(\s*Identity", content), (
        "Identity must declare operator != (AC 2)"
    )


def test_identity_declares_from_hex_string_factory() -> None:
    content = _strip(IDENTITY_CS)
    assert re.search(r"public\s+static\s+Identity\s+FromHexString\s*\(\s*string", content), (
        "Identity must expose static FromHexString(string) factory (AC 2)"
    )


def test_identity_declares_from_bytes_factory() -> None:
    content = _strip(IDENTITY_CS)
    assert re.search(r"public\s+static\s+Identity\s+FromBytes\s*\(\s*ReadOnlySpan<byte>", content), (
        "Identity must expose static FromBytes(ReadOnlySpan<byte>) factory (AC 2)"
    )


def test_identity_declares_to_string_override() -> None:
    content = _strip(IDENTITY_CS)
    assert re.search(r"public\s+override\s+string\s+ToString\s*\(", content), (
        "Identity must override ToString() (AC 2, 3)"
    )


def test_identity_default_renders_sixty_four_zero_chars() -> None:
    """AC 3: default(Identity).ToString() must return exactly 64 '0' characters.
    Enforced structurally: the source must contain the 64-zero literal used by
    the default-value render path."""
    content = _read(IDENTITY_CS)
    zeroes_64 = "0" * 64
    assert zeroes_64 in content, (
        "Identity.cs must include the 64-char all-zeros hex literal used for "
        "the default(Identity).ToString() render (AC 3)"
    )


# ---------------------------------------------------------------------------
# Identity.cs — no SpacetimeDB.* references (AC 5)
# ---------------------------------------------------------------------------

def test_identity_has_no_spacetimedb_references() -> None:
    """AC 5: Identity.cs must contain zero SpacetimeDB. references in non-comment code
    so the Story 1.3 isolation gate (test_no_spacetimedb_reference_in_public) stays green."""
    content = _read(IDENTITY_CS)
    code_text = _code_lines(content)
    assert "SpacetimeDB." not in code_text, (
        "Identity.cs must not reference SpacetimeDB.* types (AC 5 — Story 1.3 isolation gate)"
    )
    assert not re.search(r"\busing\s+SpacetimeDB(?:\.|;)", code_text), (
        "Identity.cs must not `using SpacetimeDB...` (AC 5 — Story 1.3 isolation gate)"
    )


# ---------------------------------------------------------------------------
# Identity.FromHexString — ArgumentException without echoing input (AC 6)
# ---------------------------------------------------------------------------

def test_identity_from_hex_string_throws_argument_exception_without_input_echo() -> None:
    """AC 6: FromHexString must throw ArgumentException but must NOT interpolate
    the raw input into the exception message — token values (and identity-lookalike
    inputs) must never appear verbatim in diagnostics."""
    content = _read(IDENTITY_CS)
    body = _method_body(content, "public static Identity FromHexString(")
    assert "throw new ArgumentException(" in body, (
        "FromHexString must throw ArgumentException on invalid input (AC 6)"
    )
    # Reject string interpolation or format patterns that would embed the parameter.
    # The input parameter is conventionally named `hex` in this spec.
    assert not re.search(r'\$"[^"]*\{\s*hex\s*[}:]', body), (
        "FromHexString exception message must not interpolate the raw `hex` input (AC 6)"
    )
    assert not re.search(r'string\.Format\s*\([^)]*\bhex\b', body), (
        "FromHexString exception message must not string.Format the raw `hex` input (AC 6)"
    )
    # A safe diagnostic names the expected format (64 hex chars). Enforce that positive marker.
    assert re.search(r"64\s+hex", body, re.IGNORECASE), (
        "FromHexString exception message should name the expected '64 hex' format (AC 6)"
    )


# ---------------------------------------------------------------------------
# ConnectionOpenedEvent — typed IdentityValue alongside unchanged Identity string (AC 1, back-compat)
# ---------------------------------------------------------------------------

def test_connection_opened_event_declares_identity_value_property() -> None:
    content = _strip(OPENED_EVENT_CS)
    assert re.search(r"public\s+Identity\s+IdentityValue\s*\{\s*get;\s*set;\s*\}", content), (
        "ConnectionOpenedEvent must declare public Identity IdentityValue { get; set; } (AC 1)"
    )


def test_connection_opened_event_identity_string_property_unchanged() -> None:
    """Regression guard: the existing string Identity property defaults to string.Empty,
    matching the Story 2.2 contract pinned in test_story_2_2_auth_session.py."""
    content = _read(OPENED_EVENT_CS)
    assert "Identity { get; set; } = string.Empty" in content, (
        "ConnectionOpenedEvent.Identity (string) must remain non-nullable with string.Empty default"
    )


def test_connection_opened_event_has_using_godotspacetime() -> None:
    content = _read(OPENED_EVENT_CS)
    # Identity type lives in GodotSpacetime namespace; the event file sits in
    # GodotSpacetime.Connection so it needs an explicit using.
    assert "using GodotSpacetime;" in content, (
        "ConnectionOpenedEvent.cs must `using GodotSpacetime;` to resolve the Identity type"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient.CurrentIdentity forwarding (AC 1, 4)
# ---------------------------------------------------------------------------

def test_spacetime_client_declares_current_identity_accessor() -> None:
    content = _strip(CLIENT_CS)
    assert re.search(
        r"public\s+Identity\?\s+CurrentIdentity\s*=>\s*_connectionService\.CurrentIdentity",
        content,
    ), (
        "SpacetimeClient must expose public Identity? CurrentIdentity forwarding "
        "to _connectionService.CurrentIdentity (AC 1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService — identity tracking, assignment, teardown clearing (AC 1, 4)
# ---------------------------------------------------------------------------

def test_connection_service_declares_current_identity_property() -> None:
    content = _strip(SERVICE_CS)
    assert re.search(
        r"internal\s+Identity\?\s+CurrentIdentity\s*\{\s*get;\s*private\s+set;\s*\}",
        content,
    ), (
        "SpacetimeConnectionService must expose internal Identity? CurrentIdentity "
        "{ get; private set; } (AC 1)"
    )


def test_connection_service_handle_connected_assigns_current_identity() -> None:
    content = _read(SERVICE_CS)
    body = _method_body(content, "private void HandleConnected(")
    assert "Identity.FromHexString(" in body, (
        "HandleConnected must parse the adapter-delivered identity string via "
        "Identity.FromHexString (AC 1)"
    )
    assert "CurrentIdentity =" in body, (
        "HandleConnected must assign CurrentIdentity (AC 1)"
    )


def test_connection_service_emits_identity_value_on_opened_event() -> None:
    """HandleConnected must populate ConnectionOpenedEvent.IdentityValue from
    CurrentIdentity (via direct ?? default or a snapshot local) so consumers
    see the typed identity on the open event (AC 1)."""
    content = _read(SERVICE_CS)
    body = _method_body(content, "private void HandleConnected(")
    direct = re.search(r"IdentityValue\s*=\s*CurrentIdentity\s*\?\?\s*default", body) is not None
    # Snapshot pattern: a local captures `CurrentIdentity ?? default` and the event
    # assigns IdentityValue = <that local>. This protects against a concurrent
    # teardown nulling CurrentIdentity between assignment and event emission.
    snapshot_local = re.search(
        r"var\s+(\w+)\s*=\s*CurrentIdentity\s*\?\?\s*default\s*;", body)
    snapshot = False
    if snapshot_local:
        local_name = snapshot_local.group(1)
        snapshot = re.search(rf"IdentityValue\s*=\s*{re.escape(local_name)}\b", body) is not None
    assert direct or snapshot, (
        "HandleConnected must emit IdentityValue on the ConnectionOpenedEvent derived "
        "from CurrentIdentity — either directly (IdentityValue = CurrentIdentity ?? default) "
        "or via a captured snapshot local (AC 1)"
    )


def test_connection_service_clears_current_identity_in_reset() -> None:
    content = _read(SERVICE_CS)
    body = _method_body(content, "private void ResetDisconnectedSessionState(")
    assert "CurrentIdentity = null" in body, (
        "ResetDisconnectedSessionState must clear CurrentIdentity to null (AC 4 — "
        "session-scoped state teardown rule)"
    )


def test_connection_service_clears_current_identity_on_disconnect() -> None:
    """AC 4: Disconnect(reason) must clear CurrentIdentity to null to cover the
    code path that does not route through ResetDisconnectedSessionState."""
    content = _read(SERVICE_CS)
    body = _method_body(content, "private void Disconnect(string ")
    assert "CurrentIdentity = null" in body, (
        "Disconnect(reason) must clear CurrentIdentity to null (AC 4)"
    )
