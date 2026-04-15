"""
Story 2.2: Authenticate a Client Session Through Supported Identity Flows
Automated contract tests for all story deliverables.

Covers:
- Existence of ConnectionAuthState.cs (AC: 1, 3, 4)
- ConnectionAuthState.cs content: enum values, no SpacetimeDB references
- ConnectionStatus.cs: has AuthState property (AC: 3, 4)
- ConnectionOpenedEvent.cs: has Identity property (AC: 2)
- SpacetimeSettings.cs: has Credentials property, no [Export] on Credentials (AC: 1)
- SpacetimeSdkConnectionAdapter.cs: WithToken injection, identity capture (AC: 1, 2)
- SpacetimeConnectionService.cs: _credentialsProvided, auth state transitions (AC: 1, 2, 3)
- ConnectionStateMachine.cs: Transition has ConnectionAuthState param (AC: 3)
- ConnectionAuthStatusPanel.cs: auth state labels and method (AC: 4)
- support-baseline.json: contains ConnectionAuthState.cs
- docs/runtime-boundaries.md: ConnectionAuthState, Credentials, Identity docs
- Regression guards
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# Existence tests
# ---------------------------------------------------------------------------

def test_connection_auth_state_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs").is_file(), (
        "addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs is missing"
    )


# ---------------------------------------------------------------------------
# ConnectionAuthState.cs content tests
# ---------------------------------------------------------------------------

def test_connection_auth_state_has_enum_name() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "ConnectionAuthState" in content, (
        "ConnectionAuthState.cs must declare the ConnectionAuthState enum"
    )


def test_connection_auth_state_has_none_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "None," in content or "None\n" in content or content.endswith("None"), (
        "ConnectionAuthState.cs must contain a 'None' value"
    )


def test_connection_auth_state_has_token_restored_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "TokenRestored" in content, (
        "ConnectionAuthState.cs must contain a 'TokenRestored' value"
    )


def test_connection_auth_state_has_auth_failed_value() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "AuthFailed" in content, (
        "ConnectionAuthState.cs must contain an 'AuthFailed' value"
    )


def test_connection_auth_state_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "SpacetimeDB." not in content, (
        "ConnectionAuthState.cs must not reference SpacetimeDB.* (isolation boundary)"
    )


# ---------------------------------------------------------------------------
# ConnectionStatus.cs content tests
# ---------------------------------------------------------------------------

def test_connection_status_has_auth_state_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs")
    assert "AuthState" in content, (
        "ConnectionStatus.cs must declare an AuthState property"
    )


# ---------------------------------------------------------------------------
# ConnectionOpenedEvent.cs content tests
# ---------------------------------------------------------------------------

def test_connection_opened_event_has_identity_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs")
    assert "Identity" in content, (
        "ConnectionOpenedEvent.cs must declare an Identity property"
    )


# ---------------------------------------------------------------------------
# SpacetimeSettings.cs content tests
# ---------------------------------------------------------------------------

def test_spacetime_settings_has_credentials_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "Credentials" in content, (
        "SpacetimeSettings.cs must declare a Credentials property"
    )


def test_spacetime_settings_credentials_has_no_export_attribute() -> None:
    lines = _lines("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    for i, line in enumerate(lines):
        if "Credentials" in line and "public string?" in line:
            context_before = lines[max(0, i - 3):i]
            for ctx_line in context_before:
                assert "[Export]" not in ctx_line, (
                    "SpacetimeSettings.Credentials must NOT have [Export] — credentials are security-sensitive"
                )
            return
    assert False, "SpacetimeSettings.cs must contain the public string? Credentials property"


# ---------------------------------------------------------------------------
# SpacetimeSdkConnectionAdapter.cs content tests
# ---------------------------------------------------------------------------

def test_adapter_has_with_token_call() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "WithToken" in content, (
        "SpacetimeSdkConnectionAdapter.cs must contain a WithToken call for credentials injection"
    )


def test_adapter_on_connected_has_two_parameters() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "void OnConnected(string identity, string token)" in content, (
        "IConnectionEventSink.OnConnected must have two parameters: identity and token"
    )


def test_adapter_create_connect_callback_captures_identity() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "identityExpression" in content or "identityStringExpression" in content, (
        "SpacetimeSdkConnectionAdapter.CreateConnectCallback must capture the identity via expression tree"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs content tests
# ---------------------------------------------------------------------------

def test_connection_service_has_credentials_provided_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_credentialsProvided" in content, (
        "SpacetimeConnectionService.cs must have a _credentialsProvided field"
    )


def test_connection_service_has_token_restored_state() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ConnectionAuthState.TokenRestored" in content, (
        "SpacetimeConnectionService.cs must reference ConnectionAuthState.TokenRestored"
    )


def test_connection_service_has_auth_failed_state() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ConnectionAuthState.AuthFailed" in content, (
        "SpacetimeConnectionService.cs must reference ConnectionAuthState.AuthFailed"
    )


def test_connection_service_on_connected_has_two_parameters() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IConnectionEventSink.OnConnected(string identity, string token)" in content, (
        "SpacetimeConnectionService.OnConnected must have two parameters: identity and token"
    )


def test_connection_service_sets_identity_on_event() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Identity = identity" in content, (
        "SpacetimeConnectionService.OnConnected must set Identity = identity in the ConnectionOpenedEvent"
    )


# ---------------------------------------------------------------------------
# ConnectionStateMachine.cs content tests
# ---------------------------------------------------------------------------

def test_state_machine_transition_has_auth_state_param() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs")
    assert "ConnectionAuthState" in content, (
        "ConnectionStateMachine.Transition must include a ConnectionAuthState parameter"
    )


# ---------------------------------------------------------------------------
# ConnectionAuthStatusPanel.cs content tests
# ---------------------------------------------------------------------------

def test_auth_status_panel_has_auth_state_label() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "_authStateLabel" in content, (
        "ConnectionAuthStatusPanel.cs must declare a _authStateLabel field"
    )


def test_auth_status_panel_has_token_restored_string() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "TOKEN RESTORED" in content, (
        "ConnectionAuthStatusPanel.cs must contain 'TOKEN RESTORED' text"
    )


def test_auth_status_panel_has_auth_failed_string() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "AUTH FAILED" in content, (
        "ConnectionAuthStatusPanel.cs must contain 'AUTH FAILED' text"
    )


def test_auth_status_panel_has_auth_required_string() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "AUTH REQUIRED" in content, (
        "ConnectionAuthStatusPanel.cs must contain 'AUTH REQUIRED' text"
    )


def test_auth_status_panel_has_set_auth_status_method() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "SetAuthStatus" in content, (
        "ConnectionAuthStatusPanel.cs must contain a SetAuthStatus method"
    )


def test_auth_status_panel_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "using SpacetimeDB;" not in content, (
        "ConnectionAuthStatusPanel.cs must not add 'using SpacetimeDB;' (isolation boundary)"
    )


# ---------------------------------------------------------------------------
# support-baseline.json content tests
# ---------------------------------------------------------------------------

def test_support_baseline_has_connection_auth_state_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "ConnectionAuthState.cs" in content, (
        "support-baseline.json must include 'ConnectionAuthState.cs' in required_paths"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md content tests
# ---------------------------------------------------------------------------

def test_runtime_boundaries_has_connection_auth_state() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionAuthState" in content, (
        "docs/runtime-boundaries.md must document ConnectionAuthState"
    )


def test_runtime_boundaries_has_credentials_in_settings_table() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Credentials" in content, (
        "docs/runtime-boundaries.md must include Credentials in the SpacetimeSettings table"
    )


def test_runtime_boundaries_has_identity_in_auth_section() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionOpenedEvent.Identity" in content or "Identity" in content, (
        "docs/runtime-boundaries.md must document ConnectionOpenedEvent.Identity in the auth section"
    )


# ---------------------------------------------------------------------------
# Regression guards
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


def test_connection_service_still_has_connect_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Connect(" in content, (
        "SpacetimeConnectionService.cs must still have Connect( method (regression guard)"
    )


def test_connection_service_still_has_on_connected_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "OnConnected(" in content, (
        "SpacetimeConnectionService.cs must still have OnConnected( method (regression guard)"
    )


def test_connection_service_still_has_disconnect_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "Disconnect(" in content, (
        "SpacetimeConnectionService.cs must still have Disconnect( method (regression guard)"
    )


def test_connection_service_still_has_frame_tick_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "FrameTick(" in content, (
        "SpacetimeConnectionService.cs must still have FrameTick( method (regression guard)"
    )


def test_connection_service_still_has_token_store_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_tokenStore" in content, (
        "SpacetimeConnectionService.cs must still have _tokenStore field (regression guard)"
    )


def test_connection_service_still_calls_store_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "StoreTokenAsync" in content, (
        "SpacetimeConnectionService.cs must still call StoreTokenAsync (regression guard)"
    )


def test_adapter_still_has_with_uri() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "WithUri" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have WithUri call (regression guard)"
    )


def test_adapter_still_has_with_database_name() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "WithDatabaseName" in content, (
        "SpacetimeSdkConnectionAdapter.cs must still have WithDatabaseName call (regression guard)"
    )


# ---------------------------------------------------------------------------
# Gap coverage — AC precision and structural guards
# ---------------------------------------------------------------------------

def test_auth_status_panel_has_auth_action_label() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "_authActionLabel" in content, (
        "ConnectionAuthStatusPanel.cs must declare a _authActionLabel field for action guidance text (AC 4)"
    )


def test_auth_status_panel_has_anonymous_string() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "ANONYMOUS" in content, (
        "ConnectionAuthStatusPanel.cs must display 'ANONYMOUS' for connected sessions without credentials (AC 4)"
    )


def test_connection_status_constructor_has_auth_state_param() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs")
    assert "ConnectionAuthState authState" in content, (
        "ConnectionStatus must have a constructor parameter 'ConnectionAuthState authState' (AC 3/4)"
    )


def test_state_machine_transition_passes_auth_state_to_status_constructor() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs")
    assert "new ConnectionStatus(next, description, authState)" in content, (
        "ConnectionStateMachine.Transition must pass authState to ConnectionStatus constructor (AC 3)"
    )


def test_connection_service_auth_error_description_text() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "authentication failed:" in content, (
        "SpacetimeConnectionService.OnConnectError must include 'authentication failed:' in the auth-specific description (AC 3)"
    )


def test_connection_service_has_authenticated_session_description() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "authenticated session established" in content, (
        "SpacetimeConnectionService.OnConnected must use 'authenticated session established' description when credentials provided (AC 1)"
    )


def test_adapter_credentials_injection_is_conditional() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "IsNullOrWhiteSpace(settings.Credentials)" in content, (
        "SpacetimeSdkConnectionAdapter must guard WithToken injection with IsNullOrWhiteSpace check on Credentials (AC 1)"
    )


def test_connection_service_credentials_flag_uses_is_null_or_whitespace() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "IsNullOrWhiteSpace(settings.Credentials)" in content, (
        "SpacetimeConnectionService.Connect must set _credentialsProvided via IsNullOrWhiteSpace(settings.Credentials) (AC 1)"
    )


def test_connection_auth_state_has_correct_namespace() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "namespace GodotSpacetime.Connection;" in content, (
        "ConnectionAuthState.cs must declare namespace GodotSpacetime.Connection (isolation rule)"
    )


def test_connection_opened_event_identity_defaults_to_empty_string() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs")
    assert "Identity { get; set; } = string.Empty" in content, (
        "ConnectionOpenedEvent.Identity must default to string.Empty (AC 2: empty for anonymous connections)"
    )


def test_connection_service_has_using_godotspacetime_connection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "using GodotSpacetime.Connection;" in content, (
        "SpacetimeConnectionService.cs must have 'using GodotSpacetime.Connection;' to resolve ConnectionAuthState types"
    )


def test_state_machine_has_using_godotspacetime_connection() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/ConnectionStateMachine.cs")
    assert "using GodotSpacetime.Connection;" in content, (
        "ConnectionStateMachine.cs must have 'using GodotSpacetime.Connection;' to resolve ConnectionAuthState types"
    )


def test_auth_status_panel_has_tools_guard() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "#if TOOLS" in content, (
        "ConnectionAuthStatusPanel.cs must be wrapped in #if TOOLS to prevent it loading in non-editor builds"
    )
