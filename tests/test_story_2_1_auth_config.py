"""
Story 2.1: Define Auth Configuration and Token Storage Boundaries
Automated contract tests for all story deliverables.

Covers:
- Existence of all three Internal/Auth/*.cs files
- SpacetimeSettings.cs has TokenStore property (AC: 1)
- MemoryTokenStore.cs: implements ITokenStore, has all three async methods, no SpacetimeDB. reference (AC: 1)
- ProjectSettingsTokenStore.cs: implements ITokenStore, has spacetime/auth/token key, no SpacetimeDB. reference (AC: 1)
- TokenRedactor.cs: exists, has Redact method, has <redacted> output string (AC: 1)
- SpacetimeConnectionService.cs: has _tokenStore field and StoreTokenAsync call (AC: 1)
- support-baseline.json: contains Internal/Auth/MemoryTokenStore.cs path (AC: 1)
- docs/runtime-boundaries.md: contains TokenStore in settings table (AC: 1)
- Regression guards: ITokenStore.cs still present with all three methods
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]


# ---------------------------------------------------------------------------
# Existence tests — all three Internal/Auth/*.cs files
# ---------------------------------------------------------------------------

def test_memory_token_store_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs").is_file(), (
        "addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs is missing"
    )


def test_project_settings_token_store_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs").is_file(), (
        "addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs is missing"
    )


def test_token_redactor_cs_exists() -> None:
    assert (ROOT / "addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs").is_file(), (
        "addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs is missing"
    )


# ---------------------------------------------------------------------------
# SpacetimeSettings.cs — has TokenStore property (AC: 1)
# ---------------------------------------------------------------------------

def test_spacetime_settings_has_token_store_property() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "TokenStore" in content, (
        "SpacetimeSettings.cs must declare a TokenStore property"
    )


def test_spacetime_settings_token_store_is_nullable_itokenstore() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "ITokenStore?" in content, (
        "SpacetimeSettings.cs TokenStore must be typed as ITokenStore?"
    )


# ---------------------------------------------------------------------------
# MemoryTokenStore.cs — implements ITokenStore, methods, no SpacetimeDB. ref
# ---------------------------------------------------------------------------

def test_memory_token_store_implements_itokenstore() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs")
    assert "ITokenStore" in content, (
        "MemoryTokenStore.cs must implement ITokenStore"
    )


def test_memory_token_store_has_get_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs")
    assert "GetTokenAsync" in content, (
        "MemoryTokenStore.cs must implement GetTokenAsync"
    )


def test_memory_token_store_has_store_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs")
    assert "StoreTokenAsync" in content, (
        "MemoryTokenStore.cs must implement StoreTokenAsync"
    )


def test_memory_token_store_has_clear_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs")
    assert "ClearTokenAsync" in content, (
        "MemoryTokenStore.cs must implement ClearTokenAsync"
    )


def test_memory_token_store_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs")
    assert "SpacetimeDB." not in content, (
        "MemoryTokenStore.cs must not reference SpacetimeDB.* (isolation boundary)"
    )


def test_memory_token_store_no_godot_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs")
    assert "Godot." not in content, (
        "MemoryTokenStore.cs must not reference Godot.* (pure in-memory, no platform deps)"
    )


# ---------------------------------------------------------------------------
# ProjectSettingsTokenStore.cs — implements ITokenStore, key constant, no SpacetimeDB. ref
# ---------------------------------------------------------------------------

def test_project_settings_token_store_implements_itokenstore() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "ITokenStore" in content, (
        "ProjectSettingsTokenStore.cs must implement ITokenStore"
    )


def test_project_settings_token_store_has_setting_key() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "spacetime/auth/token" in content, (
        "ProjectSettingsTokenStore.cs must contain the 'spacetime/auth/token' key constant"
    )


def test_project_settings_token_store_no_spacetimedb_reference() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "SpacetimeDB." not in content, (
        "ProjectSettingsTokenStore.cs must not reference SpacetimeDB.* (isolation boundary)"
    )


# ---------------------------------------------------------------------------
# TokenRedactor.cs — has Redact method and <redacted> output string
# ---------------------------------------------------------------------------

def test_token_redactor_has_redact_method() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs")
    assert "Redact" in content, (
        "TokenRedactor.cs must contain a Redact method"
    )


def test_token_redactor_has_redacted_string() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs")
    assert "<redacted>" in content, (
        "TokenRedactor.cs must contain '<redacted>' as an output string"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — has _tokenStore field and StoreTokenAsync call
# ---------------------------------------------------------------------------

def test_connection_service_has_token_store_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_tokenStore" in content, (
        "SpacetimeConnectionService.cs must have a _tokenStore field"
    )


def test_connection_service_calls_store_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "StoreTokenAsync" in content, (
        "SpacetimeConnectionService.cs must call StoreTokenAsync in OnConnected"
    )


# ---------------------------------------------------------------------------
# support-baseline.json — contains Internal/Auth/MemoryTokenStore.cs
# ---------------------------------------------------------------------------

def test_support_baseline_has_memory_token_store_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "Internal/Auth/MemoryTokenStore.cs" in content, (
        "support-baseline.json must include 'Internal/Auth/MemoryTokenStore.cs' in required_paths"
    )


def test_support_baseline_has_project_settings_token_store_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "Internal/Auth/ProjectSettingsTokenStore.cs" in content, (
        "support-baseline.json must include 'Internal/Auth/ProjectSettingsTokenStore.cs' in required_paths"
    )


def test_support_baseline_has_token_redactor_path() -> None:
    content = _read("scripts/compatibility/support-baseline.json")
    assert "Internal/Auth/TokenRedactor.cs" in content, (
        "support-baseline.json must include 'Internal/Auth/TokenRedactor.cs' in required_paths"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md — contains TokenStore in settings table
# ---------------------------------------------------------------------------

def test_runtime_boundaries_has_token_store_in_settings_table() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "TokenStore" in content, (
        "docs/runtime-boundaries.md must include TokenStore in the SpacetimeSettings property table"
    )


# ---------------------------------------------------------------------------
# Regression guards — ITokenStore.cs still present with all three methods
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
# Internal/Auth/*.cs — Namespace enforcement (GodotSpacetime.Runtime.Auth)
# ---------------------------------------------------------------------------

def test_memory_token_store_uses_runtime_auth_namespace() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs")
    assert "namespace GodotSpacetime.Runtime.Auth" in content, (
        "MemoryTokenStore.cs must use namespace GodotSpacetime.Runtime.Auth"
    )


def test_project_settings_token_store_uses_runtime_auth_namespace() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "namespace GodotSpacetime.Runtime.Auth" in content, (
        "ProjectSettingsTokenStore.cs must use namespace GodotSpacetime.Runtime.Auth"
    )


def test_token_redactor_uses_runtime_auth_namespace() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs")
    assert "namespace GodotSpacetime.Runtime.Auth" in content, (
        "TokenRedactor.cs must use namespace GodotSpacetime.Runtime.Auth"
    )


# ---------------------------------------------------------------------------
# Internal/Auth/*.cs — Access modifiers (internal, not public)
# ---------------------------------------------------------------------------

def test_memory_token_store_is_internal_sealed_class() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs")
    assert "internal sealed class MemoryTokenStore" in content, (
        "MemoryTokenStore.cs must be declared 'internal sealed class' (not public)"
    )


def test_project_settings_token_store_is_internal_sealed_class() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "internal sealed class ProjectSettingsTokenStore" in content, (
        "ProjectSettingsTokenStore.cs must be declared 'internal sealed class' (not public)"
    )


def test_token_redactor_is_internal_static_class() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs")
    assert "internal static class TokenRedactor" in content, (
        "TokenRedactor.cs must be declared 'internal static class' (not public)"
    )


# ---------------------------------------------------------------------------
# MemoryTokenStore.cs — backing field
# ---------------------------------------------------------------------------

def test_memory_token_store_has_token_backing_field() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/MemoryTokenStore.cs")
    assert "_token" in content, (
        "MemoryTokenStore.cs must use a '_token' field for backing storage"
    )


# ---------------------------------------------------------------------------
# ProjectSettingsTokenStore.cs — all three async methods and ClearTokenAsync detail
# ---------------------------------------------------------------------------

def test_project_settings_token_store_has_get_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "GetTokenAsync" in content, (
        "ProjectSettingsTokenStore.cs must implement GetTokenAsync"
    )


def test_project_settings_token_store_has_store_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "StoreTokenAsync" in content, (
        "ProjectSettingsTokenStore.cs must implement StoreTokenAsync"
    )


def test_project_settings_token_store_has_clear_token_async() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "ClearTokenAsync" in content, (
        "ProjectSettingsTokenStore.cs must implement ClearTokenAsync"
    )


def test_project_settings_token_store_clear_uses_string_empty() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "string.Empty" in content, (
        "ProjectSettingsTokenStore.ClearTokenAsync must set the key to string.Empty (not null)"
    )


def test_project_settings_token_store_uses_project_settings() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "ProjectSettings" in content, (
        "ProjectSettingsTokenStore.cs must use Godot.ProjectSettings for persistence"
    )


def test_project_settings_token_store_saves_after_writes() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "ProjectSettings.Save()" in content, (
        "ProjectSettingsTokenStore.cs must call ProjectSettings.Save() so tokens persist across process restarts"
    )


def test_project_settings_token_store_reports_save_failures() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs")
    assert "Task.FromException" in content and "InvalidOperationException" in content, (
        "ProjectSettingsTokenStore.cs must surface ProjectSettings save failures through the returned Task"
    )


# ---------------------------------------------------------------------------
# TokenRedactor.cs — all three output strings and length threshold
# ---------------------------------------------------------------------------

def test_token_redactor_has_no_token_string() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs")
    assert "<no token>" in content, (
        "TokenRedactor.cs must return '<no token>' for null or empty input"
    )


def test_token_redactor_has_length_threshold_check() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs")
    assert "token.Length" in content, (
        "TokenRedactor.cs must use token.Length for the short-token threshold check"
    )


def test_token_redactor_has_truncated_redacted_pattern() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Auth/TokenRedactor.cs")
    assert "…<redacted>" in content, (
        "TokenRedactor.cs must produce '…<redacted>' suffix for tokens longer than 8 characters"
    )


# ---------------------------------------------------------------------------
# SpacetimeSettings.cs — using directive, no [Export] on TokenStore, no stale comment
# ---------------------------------------------------------------------------

def test_spacetime_settings_has_using_godotspacetime_auth() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "using GodotSpacetime.Auth;" in content, (
        "SpacetimeSettings.cs must have 'using GodotSpacetime.Auth;' to resolve ITokenStore"
    )


def test_spacetime_settings_token_store_has_no_export_attribute() -> None:
    lines = _lines("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    for i, line in enumerate(lines):
        if "public ITokenStore?" in line and "TokenStore" in line:
            context_before = lines[max(0, i - 3):i]
            for ctx_line in context_before:
                assert "[Export]" not in ctx_line, (
                    "SpacetimeSettings.TokenStore must NOT have [Export] — ITokenStore is not a Godot type"
                )
            return
    assert False, "SpacetimeSettings.cs must contain the public ITokenStore? TokenStore property"


def test_spacetime_settings_no_stale_additional_settings_comment() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "Additional settings" not in content, (
        "SpacetimeSettings.cs must not contain the stale 'Additional settings' comment (removed in Story 2.1)"
    )


# ---------------------------------------------------------------------------
# SpacetimeConnectionService.cs — using directive, assignment, fire-and-forget pattern
# ---------------------------------------------------------------------------

def test_connection_service_has_using_godotspacetime_auth() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "using GodotSpacetime.Auth;" in content, (
        "SpacetimeConnectionService.cs must have 'using GodotSpacetime.Auth;' to resolve ITokenStore"
    )


def test_connection_service_assigns_token_store_from_settings() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_tokenStore = settings.TokenStore" in content, (
        "SpacetimeConnectionService.Connect() must assign '_tokenStore = settings.TokenStore;'"
    )


def test_connection_service_uses_fire_and_forget_pattern() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_ = _tokenStore.StoreTokenAsync" in content, (
        "SpacetimeConnectionService.OnConnected must use fire-and-forget '_ = _tokenStore.StoreTokenAsync' pattern"
    )


def test_connection_service_observes_faulted_token_store_tasks() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "ContinueWith" in content and "OnlyOnFaulted" in content, (
        "SpacetimeConnectionService.OnConnected must observe faulted token-store tasks so optional persistence failures stay non-fatal"
    )


def test_connection_service_shields_sync_token_store_exceptions() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "catch (Exception)" in content, (
        "SpacetimeConnectionService.OnConnected must shield connection success from synchronous token-store exceptions"
    )


# ---------------------------------------------------------------------------
# docs/runtime-boundaries.md — expanded auth section content
# ---------------------------------------------------------------------------

def test_runtime_boundaries_has_built_in_implementations_section() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "Built-in implementations" in content, (
        "docs/runtime-boundaries.md must contain a 'Built-in implementations' section in the auth docs"
    )


def test_runtime_boundaries_has_memory_token_store_description() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "MemoryTokenStore" in content, (
        "docs/runtime-boundaries.md must describe MemoryTokenStore in the auth section"
    )


def test_runtime_boundaries_has_project_settings_token_store_description() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ProjectSettingsTokenStore" in content, (
        "docs/runtime-boundaries.md must describe ProjectSettingsTokenStore in the auth section"
    )


def test_runtime_boundaries_has_clear_token_async_reference() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "ClearTokenAsync" in content, (
        "docs/runtime-boundaries.md must document token clearing via ClearTokenAsync"
    )


def test_runtime_boundaries_has_token_redactor_reference() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "TokenRedactor" in content, (
        "docs/runtime-boundaries.md must reference TokenRedactor for safe diagnostic representations"
    )


def test_runtime_boundaries_documents_setting_key() -> None:
    content = _read("docs/runtime-boundaries.md")
    assert "spacetime/auth/token" in content, (
        "docs/runtime-boundaries.md must document the 'spacetime/auth/token' ProjectSettings key"
    )
