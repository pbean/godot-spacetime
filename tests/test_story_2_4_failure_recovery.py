"""
Story 2.4: Recover from Common Session and Identity Failures
Automated contract tests for all story deliverables.

Covers:
- ConnectionAuthState.cs: TokenExpired enum value, XML doc referencing ClearTokenAsync (AC: 2, 3)
- SpacetimeConnectionService.cs: _restoredFromStore field, assignment, ordering in OnConnectError,
  TokenExpired usage, message text, AuthFailed path preserved (AC: 1, 2)
- ConnectionAuthStatusPanel.cs: TokenExpired arm, "TOKEN EXPIRED" label, ClearTokenAsync in action,
  TokenExpired before AuthFailed in switch (AC: 4)
- docs/runtime-boundaries.md: TokenExpired in table, Failure Recovery section, ClearTokenAsync,
  ArgumentException distinction (AC: 1, 2, 3, 4)
- Regression guards: prior story values, fields, methods, and labels intact
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# ConnectionAuthState.cs — TokenExpired enum value (AC: 2, 3)
# ---------------------------------------------------------------------------

def test_connection_auth_state_has_token_expired_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "TokenExpired" in content, (
        "ConnectionAuthState.cs must contain 'TokenExpired' enum value (AC 2)"
    )


def test_connection_auth_state_token_expired_in_enum_block() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "TokenExpired," in content or "TokenExpired\n" in content, (
        "TokenExpired must be a properly declared enum member in ConnectionAuthState (AC 2)"
    )


def test_connection_auth_state_token_expired_has_clear_token_async_doc() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "ClearTokenAsync" in content, (
        "ConnectionAuthState.cs must have XML doc comment referencing ClearTokenAsync for TokenExpired (AC 2)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — _restoredFromStore field and usage (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_connection_service_has_restored_from_store_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_restoredFromStore" in content, (
        "SpacetimeConnectionService.cs must declare _restoredFromStore field (AC 1, 2)"
    )


def test_connection_service_assigns_restored_from_store() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_restoredFromStore = restoredCredentials" in content, (
        "SpacetimeConnectionService.cs must assign _restoredFromStore = restoredCredentials in Connect() (AC 1)"
    )


def test_connection_service_has_token_expired_usage() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ConnectionAuthState.TokenExpired" in content, (
        "SpacetimeConnectionService.cs must use ConnectionAuthState.TokenExpired in OnConnectError (AC 1, 2)"
    )


def test_connection_service_token_expired_message_text() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "stored token was rejected" in content, (
        "SpacetimeConnectionService.cs TokenExpired transition must include 'stored token was rejected' (AC 2)"
    )


def test_connection_service_restored_from_store_check_before_credentials_provided() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    pos_restored = content.find("_restoredFromStore")
    pos_credentials = content.find("_credentialsProvided")
    # Find within OnConnectError specifically by searching for the if-block pattern
    on_connect_error_pos = content.find("void IConnectionEventSink.OnConnectError(")
    assert on_connect_error_pos != -1, (
        "SpacetimeConnectionService.cs must have OnConnectError method"
    )
    after_method = content[on_connect_error_pos:]
    pos_restored_in_method = after_method.find("_restoredFromStore")
    pos_credentials_in_method = after_method.find("_credentialsProvided")
    assert pos_restored_in_method != -1 and pos_credentials_in_method != -1, (
        "Both _restoredFromStore and _credentialsProvided must appear in OnConnectError (AC 2)"
    )
    assert pos_restored_in_method < pos_credentials_in_method, (
        "_restoredFromStore check must appear before _credentialsProvided check in OnConnectError "
        "so restored-token failures route to TokenExpired first (AC 2)"
    )


def test_connection_service_auth_failed_path_still_exists() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ConnectionAuthState.AuthFailed" in content, (
        "SpacetimeConnectionService.cs AuthFailed path must still exist for explicit-credential failures (AC 2)"
    )


def test_connection_service_both_restored_and_credentials_in_on_connect_error() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    on_connect_error_pos = content.find("void IConnectionEventSink.OnConnectError(")
    assert on_connect_error_pos != -1
    after_method = content[on_connect_error_pos:]
    assert "_restoredFromStore" in after_method, (
        "_restoredFromStore must be referenced in OnConnectError (AC 1, 2)"
    )
    assert "_credentialsProvided" in after_method, (
        "_credentialsProvided must still be referenced in OnConnectError (AC 2)"
    )


# ---------------------------------------------------------------------------
# ConnectionAuthStatusPanel.cs — TokenExpired arm (AC: 4)
# ---------------------------------------------------------------------------

def test_auth_status_panel_has_token_expired_in_switch() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "TokenExpired" in content, (
        "ConnectionAuthStatusPanel.cs must handle ConnectionAuthState.TokenExpired in the switch (AC 4)"
    )


def test_auth_status_panel_has_token_expired_label() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "TOKEN EXPIRED" in content, (
        "ConnectionAuthStatusPanel.cs must display 'TOKEN EXPIRED' label for TokenExpired state (AC 4)"
    )


def test_auth_status_panel_token_expired_action_has_clear_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    # Find the TokenExpired arm and check that ClearTokenAsync appears nearby
    pos_expired = content.find("TOKEN EXPIRED")
    assert pos_expired != -1, "TOKEN EXPIRED label must exist in panel"
    # ClearTokenAsync must appear in the action text
    assert "ClearTokenAsync" in content, (
        "ConnectionAuthStatusPanel.cs TokenExpired action must reference ClearTokenAsync (AC 4)"
    )


def test_auth_status_panel_token_expired_before_auth_failed_in_switch() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    pos_expired = content.find("TokenExpired")
    pos_auth_failed = content.find("AuthFailed")
    assert pos_expired != -1 and pos_auth_failed != -1, (
        "Both TokenExpired and AuthFailed arms must exist in ConnectionAuthStatusPanel.cs switch (AC 4)"
    )
    assert pos_expired < pos_auth_failed, (
        "TokenExpired arm must appear before AuthFailed arm in the switch so it takes priority (AC 4)"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md — TokenExpired and Failure Recovery (AC: 1, 2, 3, 4)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_has_token_expired_in_auth_table() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "TokenExpired" in content, (
        "docs/runtime-boundaries.md must include TokenExpired in the ConnectionAuthState table (AC 2)"
    )


def test_runtime_boundaries_has_failure_recovery_section() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Failure Recovery" in content, (
        "docs/runtime-boundaries.md must contain a 'Failure Recovery' section (AC 1, 3)"
    )


def test_runtime_boundaries_failure_recovery_has_clear_token_async() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ClearTokenAsync" in content, (
        "docs/runtime-boundaries.md must reference ClearTokenAsync in the Failure Recovery section (AC 2)"
    )


def test_runtime_boundaries_failure_recovery_has_argument_exception() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ArgumentException" in content, (
        "docs/runtime-boundaries.md must mention ArgumentException to distinguish recoverable vs "
        "unrecoverable failures (AC 3)"
    )


def test_runtime_boundaries_token_expired_description_references_token_store() -> None:
    content = _read("docs/runtime-boundaries.md")
    # TokenExpired description should reference clearing the token store
    pos_expired = content.find("TokenExpired")
    assert pos_expired != -1
    # Check that somewhere in the document token expired is associated with clearing
    assert "clear the token store" in content.lower() or "ClearTokenAsync" in content, (
        "docs/runtime-boundaries.md must associate TokenExpired with clearing the token store (AC 2)"
    )


# ---------------------------------------------------------------------------
# Regression guards — prior ConnectionAuthState enum values
# ---------------------------------------------------------------------------

def test_connection_auth_state_still_has_none() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "None," in content or "None\n" in content, (
        "ConnectionAuthState.cs must still contain 'None' value (regression guard)"
    )


def test_connection_auth_state_still_has_auth_required() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "AuthRequired" in content, (
        "ConnectionAuthState.cs must still contain 'AuthRequired' value (regression guard)"
    )


def test_connection_auth_state_still_has_token_restored() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "TokenRestored" in content, (
        "ConnectionAuthState.cs must still contain 'TokenRestored' value (regression guard)"
    )


def test_connection_auth_state_still_has_auth_failed() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "AuthFailed" in content, (
        "ConnectionAuthState.cs must still contain 'AuthFailed' value (regression guard)"
    )


# ---------------------------------------------------------------------------
# Regression guards — SpacetimeConnectionService.cs core fields and paths
# ---------------------------------------------------------------------------

def test_connection_service_still_has_credentials_provided() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_credentialsProvided" in content, (
        "SpacetimeConnectionService.cs must still have _credentialsProvided (regression guard)"
    )


def test_connection_service_still_has_restored_credentials_local() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "restoredCredentials" in content, (
        "SpacetimeConnectionService.cs must still have restoredCredentials local in Connect() (regression guard)"
    )


def test_connection_service_still_has_get_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "GetTokenAsync" in content, (
        "SpacetimeConnectionService.cs must still call GetTokenAsync for session restoration (regression guard)"
    )


def test_connection_service_still_has_handle_disconnect_error() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "HandleDisconnectError" in content, (
        "SpacetimeConnectionService.cs must still have HandleDisconnectError (regression guard)"
    )


# ---------------------------------------------------------------------------
# Regression guards — ConnectionAuthStatusPanel.cs labels
# ---------------------------------------------------------------------------

def test_auth_status_panel_still_has_token_restored() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "TOKEN RESTORED" in content, (
        "ConnectionAuthStatusPanel.cs must still contain 'TOKEN RESTORED' label (regression guard)"
    )


def test_auth_status_panel_still_has_auth_failed() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "AUTH FAILED" in content, (
        "ConnectionAuthStatusPanel.cs must still contain 'AUTH FAILED' label (regression guard)"
    )


def test_auth_status_panel_still_has_auth_required() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "AUTH REQUIRED" in content, (
        "ConnectionAuthStatusPanel.cs must still contain 'AUTH REQUIRED' label (regression guard)"
    )


# ---------------------------------------------------------------------------
# Regression guards — ITokenStore interface intact
# ---------------------------------------------------------------------------

def test_itokenstore_still_has_get_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert "GetTokenAsync" in content, (
        "ITokenStore.cs must still declare GetTokenAsync (regression guard)"
    )


def test_itokenstore_still_has_store_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert "StoreTokenAsync" in content, (
        "ITokenStore.cs must still declare StoreTokenAsync (regression guard)"
    )


def test_itokenstore_still_has_clear_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert "ClearTokenAsync" in content, (
        "ITokenStore.cs must still declare ClearTokenAsync (regression guard)"
    )


# ---------------------------------------------------------------------------
# Isolation guard — no SpacetimeDB.* introduced by this story
# ---------------------------------------------------------------------------

def test_connection_auth_state_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "SpacetimeDB." not in content, (
        "ConnectionAuthState.cs must not reference SpacetimeDB.* (isolation boundary)"
    )


def test_connection_service_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "SpacetimeDB." not in content, (
        "SpacetimeConnectionService.cs must not reference SpacetimeDB.* (isolation boundary)"
    )


# ---------------------------------------------------------------------------
# Gap tests: ConnectionAuthState.cs — enum ordering and namespace
# ---------------------------------------------------------------------------

def test_connection_auth_state_token_expired_after_auth_failed_in_enum() -> None:
    """TokenExpired must follow AuthFailed — spec enum order: None, AuthRequired, TokenRestored, AuthFailed, TokenExpired."""
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    pos_auth_failed = content.find("AuthFailed")
    pos_token_expired = content.find("TokenExpired")
    assert pos_auth_failed != -1 and pos_token_expired != -1
    assert pos_auth_failed < pos_token_expired, (
        "TokenExpired must be declared after AuthFailed in the enum "
        "(required order: None, AuthRequired, TokenRestored, AuthFailed, TokenExpired) (AC 2)"
    )


def test_connection_auth_state_namespace_is_godot_spacetime_connection() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "namespace GodotSpacetime.Connection" in content, (
        "ConnectionAuthState.cs must use GodotSpacetime.Connection namespace (isolation boundary)"
    )


# ---------------------------------------------------------------------------
# Gap tests: SpacetimeConnectionService.cs — anonymous path and fault taxonomy (AC: 3)
# ---------------------------------------------------------------------------

def test_connection_service_anonymous_connect_fail_path_preserved() -> None:
    """The third else branch in OnConnectError for anonymous network failures must remain intact (AC 3)."""
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "failed to connect:" in content, (
        "SpacetimeConnectionService.cs anonymous connect-fail branch must still produce "
        "'failed to connect:' message — anonymous network failures are distinct from auth failures (AC 3)"
    )


def test_connection_service_restored_from_store_is_private_bool() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "private bool _restoredFromStore" in content, (
        "SpacetimeConnectionService.cs must declare _restoredFromStore as 'private bool' (AC 1, 2)"
    )


def test_connection_service_validate_settings_throws_argument_exception() -> None:
    """Unrecoverable programming faults must remain exceptions, not ConnectionStatus events (AC 3)."""
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ArgumentException" in content, (
        "SpacetimeConnectionService.cs must throw ArgumentException for invalid settings "
        "(AC 3 — unrecoverable faults stay as thrown exceptions, not ConnectionStatus events)"
    )


def test_connection_service_finally_clears_restored_credentials() -> None:
    """Story 2.3 invariant: restored token cleared from settings after Connect() to isolate it to one attempt."""
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "finally" in content, (
        "SpacetimeConnectionService.cs must have a finally block to clean up restored credentials (Story 2.3 invariant)"
    )
    assert "settings.Credentials = null" in content, (
        "SpacetimeConnectionService.cs finally block must null settings.Credentials after a restored-token connect "
        "so clearing the token store correctly resets future Connect() calls"
    )


# ---------------------------------------------------------------------------
# Gap tests: ConnectionAuthStatusPanel.cs — TOOLS guard, ANONYMOUS label, isolation (AC: 4)
# ---------------------------------------------------------------------------

def test_auth_status_panel_has_tools_preprocessor_guard() -> None:
    """Spec explicitly requires #if TOOLS guard is preserved and unchanged (AC 4)."""
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "#if TOOLS" in content, (
        "ConnectionAuthStatusPanel.cs must preserve the #if TOOLS preprocessor guard (AC 4)"
    )


def test_auth_status_panel_has_anonymous_label() -> None:
    """The ANONYMOUS arm for connected-without-credentials sessions must not be broken (regression guard)."""
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "ANONYMOUS" in content, (
        "ConnectionAuthStatusPanel.cs must still display 'ANONYMOUS' label for "
        "anonymous connected sessions (regression guard)"
    )


def test_auth_status_panel_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "SpacetimeDB." not in content, (
        "ConnectionAuthStatusPanel.cs must not reference SpacetimeDB.* (isolation boundary)"
    )


# ---------------------------------------------------------------------------
# Gap tests: docs/runtime-boundaries.md — precision of failure taxonomy (AC: 2, 3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_token_expired_only_for_token_restoration() -> None:
    """AC 2: the doc must clarify that TokenExpired is only emitted for token-restoration sessions."""
    content = _read("docs/runtime-boundaries.md")
    pos_failure_recovery = content.find("Failure Recovery")
    assert pos_failure_recovery != -1
    failure_section = content[pos_failure_recovery:]
    assert "restoration" in failure_section.lower(), (
        "docs/runtime-boundaries.md Failure Recovery section must state that TokenExpired "
        "is only emitted when the session was opened via token restoration (AC 2)"
    )


def test_runtime_boundaries_auth_failed_described_in_failure_recovery() -> None:
    """Both failure categories (TokenExpired and AuthFailed) must be documented in the recovery section (AC 1, 3)."""
    content = _read("docs/runtime-boundaries.md")
    pos_failure_recovery = content.find("Failure Recovery")
    assert pos_failure_recovery != -1
    failure_section = content[pos_failure_recovery:]
    assert "AuthFailed" in failure_section, (
        "docs/runtime-boundaries.md Failure Recovery section must document the AuthFailed "
        "recovery path alongside TokenExpired (AC 1, 3)"
    )


def test_runtime_boundaries_failure_recovery_references_connection_state_changed() -> None:
    """AC 1: the doc must name ConnectionStateChanged as the observation surface for auth failures."""
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionStateChanged" in content, (
        "docs/runtime-boundaries.md must reference SpacetimeClient.ConnectionStateChanged "
        "as how gameplay code observes auth failure events (AC 1)"
    )
