"""
Story 2.3: Restore a Previous Session from Persisted Auth State
Automated contract tests for all story deliverables.

Covers:
- SpacetimeConnectionService.cs: GetTokenAsync call, sync block, guard conditions, credentials injection,
  try/catch, block ordering before _credentialsProvided (AC: 1, 3, 4)
- docs/runtime-boundaries.md: Session Restoration section, GetTokenAsync, WithToken, TokenRestored refs
  (AC: 1, 2, 3)
- Regression guards: ITokenStore interface, _credentialsProvided, _tokenStore, _reconnectPolicy,
  StoreTokenAsync, WithToken, ConnectionAuthState values, ConnectionAuthStatusPanel labels
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — token restoration logic (AC: 1, 3, 4)
# ---------------------------------------------------------------------------

def test_connection_service_has_get_token_async_call() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "GetTokenAsync" in content, (
        "SpacetimeConnectionService.cs must call GetTokenAsync for token restoration (AC 1)"
    )


def test_connection_service_has_get_awaiter_get_result() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "GetAwaiter" in content, (
        "SpacetimeConnectionService.cs must use GetAwaiter().GetResult() to synchronously await the token task (AC 1)"
    )


def test_connection_service_restore_guarded_by_is_null_or_whitespace() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IsNullOrWhiteSpace(settings.Credentials)" in content, (
        "SpacetimeConnectionService.cs must guard restoration with IsNullOrWhiteSpace(settings.Credentials) "
        "to avoid overwriting explicit credentials (AC 3)"
    )


def test_connection_service_guards_null_token_store() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "settings.TokenStore != null" in content, (
        "SpacetimeConnectionService.cs must guard against null TokenStore before calling GetTokenAsync (AC 1)"
    )


def test_connection_service_injects_credentials_from_store() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "settings.Credentials = stored" in content, (
        "SpacetimeConnectionService.cs must inject the restored token into settings.Credentials (AC 1)"
    )


def test_connection_service_checks_stored_token_not_empty() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IsNullOrWhiteSpace(stored)" in content, (
        "SpacetimeConnectionService.cs must check that the stored token is non-empty before injecting "
        "(AC 3 — empty token falls back to anonymous)"
    )


def test_connection_service_has_get_result_in_sync_chain() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "GetResult()" in content, (
        "SpacetimeConnectionService.cs must call GetResult() to complete the synchronous await chain (AC 1)"
    )


def test_connection_service_restore_wrapped_in_try_block() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    # The file must contain a try block — both the existing OnConnected try and the new restoration try
    assert content.count("try") >= 2, (
        "SpacetimeConnectionService.cs must wrap token restoration in a try block (non-fatal failure, AC 4)"
    )


def test_connection_service_restore_has_catch_exception_block() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "catch (Exception)" in content, (
        "SpacetimeConnectionService.cs must have a catch (Exception) block making token restoration "
        "non-fatal (AC 4)"
    )


def test_connection_service_restore_block_before_credentials_provided() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    pos_restore = content.find("GetTokenAsync")
    pos_provided = content.find("_credentialsProvided =")
    assert pos_restore != -1 and pos_provided != -1, (
        "Both GetTokenAsync and _credentialsProvided = must exist in SpacetimeConnectionService.cs"
    )
    assert pos_restore < pos_provided, (
        "Token restoration block must appear BEFORE _credentialsProvided assignment so the restored "
        "token is picked up automatically (AC 1)"
    )


def test_connection_service_tracks_transient_restored_credentials() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "var restoredCredentials = false;" in content and "restoredCredentials = true;" in content, (
        "SpacetimeConnectionService.cs must track whether credentials came from token restoration so the "
        "restored token can be cleaned up after the connect attempt"
    )


def test_connection_service_clears_restored_credentials_after_open_attempt() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    pos_open = content.find("_adapter.Open(settings, this);")
    pos_finally = content.find("finally")
    pos_clear = content.find("settings.Credentials = null;")
    assert pos_open != -1 and pos_finally != -1 and pos_clear != -1, (
        "SpacetimeConnectionService.cs must clear a restored credential in a finally block after the open attempt"
    )
    assert pos_open < pos_finally < pos_clear, (
        "Restored credentials must be cleared only after _adapter.Open(settings, this) has been attempted"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md — Session Restoration documentation (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_runtime_boundaries_has_session_restoration_section() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Session Restoration" in content, (
        "docs/runtime-boundaries.md must document the Session Restoration behaviour (AC 1)"
    )


def test_runtime_boundaries_has_get_token_async_in_auth_section() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "GetTokenAsync" in content, (
        "docs/runtime-boundaries.md must reference GetTokenAsync in the auth/identity section (AC 1)"
    )


def test_runtime_boundaries_mentions_with_token_in_session_restoration() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "WithToken" in content, (
        "docs/runtime-boundaries.md must mention WithToken in the Session Restoration section (AC 1)"
    )


def test_runtime_boundaries_mentions_token_restored_in_session_restoration() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "TokenRestored" in content, (
        "docs/runtime-boundaries.md must mention ConnectionAuthState.TokenRestored in the Session Restoration "
        "section (AC 2)"
    )


def test_runtime_boundaries_mentions_sync_restore_expectation() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "waits synchronously for `GetTokenAsync()`" in content, (
        "docs/runtime-boundaries.md must explain that Connect() waits synchronously for GetTokenAsync() "
        "during session restoration"
    )


def test_runtime_boundaries_mentions_restored_token_not_retained() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "not retained on the settings resource after `Connect()` returns" in content, (
        "docs/runtime-boundaries.md must explain that restored tokens are not retained on the settings "
        "resource after Connect() returns"
    )


# ---------------------------------------------------------------------------
# Regression guards — ITokenStore interface intact
# ---------------------------------------------------------------------------

def test_itokenstore_cs_still_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Public/Auth/ITokenStore.cs").is_file(), (
        "addons/godot_spacetime/src/Public/Auth/ITokenStore.cs is missing (regression guard)"
    )


def test_itokenstore_has_get_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert "GetTokenAsync" in content, (
        "ITokenStore.cs must still declare GetTokenAsync (regression guard)"
    )


def test_itokenstore_has_store_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert "StoreTokenAsync" in content, (
        "ITokenStore.cs must still declare StoreTokenAsync (regression guard)"
    )


def test_itokenstore_has_clear_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Public/Auth/ITokenStore.cs")
    assert "ClearTokenAsync" in content, (
        "ITokenStore.cs must still declare ClearTokenAsync (regression guard)"
    )


# ---------------------------------------------------------------------------
# Regression guards — SpacetimeConnectionService.cs core fields and methods
# ---------------------------------------------------------------------------

def test_connection_service_still_has_credentials_provided_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_credentialsProvided" in content, (
        "SpacetimeConnectionService.cs must still have _credentialsProvided field (regression guard)"
    )


def test_connection_service_still_has_token_store_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_tokenStore" in content, (
        "SpacetimeConnectionService.cs must still have _tokenStore field (regression guard)"
    )


def test_connection_service_still_calls_store_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "StoreTokenAsync" in content, (
        "SpacetimeConnectionService.cs must still call StoreTokenAsync in OnConnected (regression guard)"
    )


def test_connection_service_still_has_on_connected_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnConnected(" in content, (
        "SpacetimeConnectionService.cs must still have OnConnected( method (regression guard)"
    )


def test_connection_service_still_has_reconnect_policy() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_reconnectPolicy" in content, (
        "SpacetimeConnectionService.cs must still have _reconnectPolicy field (regression guard)"
    )


# ---------------------------------------------------------------------------
# Regression guards — WithToken injection in adapter
# ---------------------------------------------------------------------------

def test_adapter_still_has_with_token_call() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "WithToken" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have WithToken call (regression guard)"
    )


# ---------------------------------------------------------------------------
# Regression guards — ConnectionAuthState enum values
# ---------------------------------------------------------------------------

def test_connection_auth_state_has_token_restored_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "TokenRestored" in content, (
        "ConnectionAuthState.cs must still contain 'TokenRestored' value (regression guard)"
    )


def test_connection_auth_state_has_auth_failed_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "AuthFailed" in content, (
        "ConnectionAuthState.cs must still contain 'AuthFailed' value (regression guard)"
    )


# ---------------------------------------------------------------------------
# Regression guards — ConnectionAuthStatusPanel labels
# ---------------------------------------------------------------------------

def test_auth_status_panel_has_token_restored_string() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "TOKEN RESTORED" in content, (
        "ConnectionAuthStatusPanel.cs must still contain 'TOKEN RESTORED' label (regression guard)"
    )


def test_auth_status_panel_has_auth_failed_string() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "AUTH FAILED" in content, (
        "ConnectionAuthStatusPanel.cs must still contain 'AUTH FAILED' label (regression guard)"
    )


# ---------------------------------------------------------------------------
# Isolation guard — no SpacetimeDB.* reference introduced by this story
# ---------------------------------------------------------------------------

def test_connection_service_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "SpacetimeDB." not in content, (
        "SpacetimeConnectionService.cs must not reference SpacetimeDB.* (isolation boundary, story 2.3 must not break this)"
    )
