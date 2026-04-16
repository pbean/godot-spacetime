"""
Story 9.1: Configure Message Compression for Client-Server Communication
Static contract tests for the public compression surface, adapter mapping,
status surface, and documentation updates.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_message_compression_mode_contract_exists() -> None:
    rel = "addons/godot_spacetime/src/Public/Connection/MessageCompressionMode.cs"
    path = ROOT / rel
    assert path.exists(), (
        f"{rel} must exist before the public compression contract can be consumed (Task 1.1, AC1)"
    )
    content = path.read_text(encoding="utf-8")
    for expected in ("enum MessageCompressionMode", "None", "Gzip", "Brotli"):
        assert expected in content, (
            "Story 9.1 must add a public runtime-neutral MessageCompressionMode enum "
            f"with {expected!r} in Public/Connection/ (Task 1.1, AC1)"
        )
    assert "SpacetimeDB." not in content, (
        "MessageCompressionMode must remain runtime-neutral and must not reference SpacetimeDB.* (Task 1.4)"
    )


def test_spacetime_settings_exports_opt_in_compression_mode() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "[Export]" in content and "public MessageCompressionMode CompressionMode { get; set; } = MessageCompressionMode.None;" in content, (
        "SpacetimeSettings must expose an exported CompressionMode property defaulting to None "
        "so compression stays opt-in for existing projects (Task 1.2, AC1)"
    )


def test_connection_status_exposes_active_compression_mode() -> None:
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs")
    assert "ActiveCompressionMode" in content, (
        "ConnectionStatus must expose ActiveCompressionMode so the effective session mode is observable (Task 1.3, AC4)"
    )
    assert "MessageCompressionMode activeCompressionMode = MessageCompressionMode.None" in content, (
        "ConnectionStatus must add a constructor parameter defaulting ActiveCompressionMode to None (Task 1.3, AC4)"
    )


def test_adapter_calls_with_compression_and_keeps_sdk_types_isolated() -> None:
    adapter_rel = "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs"
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "WithCompression" in content and "SpacetimeDB.Compression" in content and "MapCompressionMode(settings.CompressionMode)" in content, (
        "The .NET adapter must map MessageCompressionMode to SpacetimeDB.Compression "
        "and call WithCompression(...) inside Internal/Platform/DotNet only (Task 2.1, Task 2.2, AC1/AC3)"
    )
    offenders: list[str] = []
    for path in (ROOT / "addons/godot_spacetime/src").rglob("*.cs"):
        rel = path.relative_to(ROOT).as_posix()
        if rel == adapter_rel:
            continue
        if "SpacetimeDB.Compression" in path.read_text(encoding="utf-8"):
            offenders.append(rel)
    assert not offenders, (
        "SpacetimeDB.Compression must stay isolated to Internal/Platform/DotNet/. "
        f"Found offenders: {offenders}"
    )


def test_adapter_applies_compression_before_callbacks_and_build() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    compression_call = 'builder = InvokeMethod(builder, "WithCompression", MapCompressionMode(settings.CompressionMode));'
    compression_index = content.index(compression_call)

    for expected_later_call in (
        'builder = InvokeMethod(builder, "OnConnect", CreateConnectCallback(builder, sink));',
        'builder = InvokeMethod(builder, "OnConnectError", CreateConnectErrorCallback(builder, sink));',
        'builder = InvokeMethod(builder, "OnDisconnect", CreateDisconnectCallback(builder, sink));',
        '_dbConnection = (IDbConnection?)InvokeMethod(builder, "Build")',
    ):
        assert compression_index < content.index(expected_later_call), (
            "WithCompression(...) must be applied before callback registration and Build() so the "
            "requested mode always participates in connection setup (Task 2.2, AC1)"
        )


def test_adapter_keeps_transport_ownership_and_decompression_inside_the_sdk() -> None:
    forbidden_terms = (
        "System.Net.WebSockets",
        "ClientWebSocket",
        "System.IO.Compression",
        "BrotliStream",
        "GZipStream",
        "DeflateStream",
    )

    offenders: dict[str, list[str]] = {}
    for path in (ROOT / "addons/godot_spacetime/src").rglob("*.cs"):
        rel = path.relative_to(ROOT).as_posix()
        content = path.read_text(encoding="utf-8")
        hits = [term for term in forbidden_terms if term in content]
        if hits:
            offenders[rel] = hits

    assert not offenders, (
        "Story 9.1 must keep transport ownership and decompression in the pinned SDK rather than "
        "adding a parallel WebSocket owner or manual Brotli/Gzip streams. "
        f"Found forbidden terms in: {offenders}"
    )


def test_adapter_canonicalizes_brotli_to_effective_gzip_without_rewriting_other_modes() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    assert "MessageCompressionMode.Brotli => MessageCompressionMode.Gzip" in content, (
        "The adapter must surface the pinned 2.1.x runtime's Brotli->Gzip canonicalization explicitly "
        "through GetEffectiveCompressionMode() (Task 2.6, AC4)"
    )
    assert "_ => requestedCompressionMode" in content, (
        "GetEffectiveCompressionMode() must leave None and Gzip unchanged rather than rewriting all modes "
        "(Task 2.6, AC1/AC4)"
    )


def test_connection_service_tracks_effective_compression_mode_and_resets_on_disconnect() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "_activeCompressionMode" in content and "GetEffectiveCompressionMode(settings.CompressionMode)" in content, (
        "SpacetimeConnectionService must track the effective per-session compression mode using the adapter's runtime knowledge (Task 2.5, Task 2.6)"
    )
    assert "activeCompressionMode: _activeCompressionMode" in content and "_activeCompressionMode = MessageCompressionMode.None;" in content, (
        "SpacetimeConnectionService must publish the active compression mode through status transitions and reset it to None on disconnect (Task 2.5, AC4)"
    )


def test_status_panel_contains_compression_row_without_regressing_existing_labels() -> None:
    content = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "Compression:" in content and "_compressionValueLabel" in content and "status.ActiveCompressionMode" in content, (
        "ConnectionAuthStatusPanel must add a compression row that reads the effective mode "
        "while preserving the existing status/auth rows (Task 3.1, Task 3.2, AC4)"
    )
    assert "Settings.CompressionMode" not in content, (
        "ConnectionAuthStatusPanel must read the effective mode from ConnectionStatus, not infer it from SpacetimeSettings (Task 3.2)"
    )
    for expected in ("Current state:", "Auth state:", "TOKEN RESTORED", "AUTH REQUIRED"):
        assert expected in content, (
            f"ConnectionAuthStatusPanel must keep the existing {expected!r} anchor intact (regression guard)"
        )


def test_docs_cover_opt_in_default_and_effective_mode_surface() -> None:
    docs = {
        "docs/runtime-boundaries.md": ("CompressionMode", "ActiveCompressionMode", "Brotli", "Gzip"),
        "docs/connection.md": ("CompressionMode", "ActiveCompressionMode", "Compression"),
        "docs/quickstart.md": ("CompressionMode", "None"),
        "docs/troubleshooting.md": ("CompressionMode", "Compression", "Gzip"),
        "demo/README.md": ("CompressionMode", "ConnectionStatus", "ActiveCompressionMode"),
    }
    for rel, expected_terms in docs.items():
        content = _read(rel)
        for expected in expected_terms:
            assert expected in content, (
                f"{rel} must document {expected!r} for Story 9.1 (Task 3.3)"
            )


def test_story_1_9_and_story_2_auth_regression_anchors_remain_intact() -> None:
    connection_panel = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    assert "FocusModeEnum.All" in connection_panel and "AutowrapMode.WordSmart" in connection_panel, (
        "Compression status work must preserve the Story 1.9 panel accessibility anchors"
    )
    assert "ANONYMOUS" in connection_panel and "CONNECT FAILED" in connection_panel, (
        "Compression status work must preserve the Story 2.x auth-state labels"
    )
