"""
Story 11.2: Implement GDScript WebSocket Connection and Protocol Handling

Static contract coverage for the native GDScript runtime seam.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GDSCRIPT_DIR = (
    ROOT
    / "addons"
    / "godot_spacetime"
    / "src"
    / "Internal"
    / "Platform"
    / "GDScript"
)

SERVICE_PATH = GDSCRIPT_DIR / "gdscript_connection_service.gd"
PROTOCOL_PATH = GDSCRIPT_DIR / "connection_protocol.gd"
RECONNECT_PATH = GDSCRIPT_DIR / "reconnect_policy.gd"
TOKEN_CONTRACT_PATH = GDSCRIPT_DIR / "token_store.gd"
TOKEN_STORE_PATH = GDSCRIPT_DIR / "file_token_store.gd"
BSATN_READER_PATH = GDSCRIPT_DIR / "bsatn_reader.gd"
BSATN_WRITER_PATH = GDSCRIPT_DIR / "bsatn_writer.gd"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _service_src() -> str:
    return _read(SERVICE_PATH)


def _protocol_src() -> str:
    return _read(PROTOCOL_PATH)


def _reconnect_src() -> str:
    return _read(RECONNECT_PATH)


def _token_contract_src() -> str:
    return _read(TOKEN_CONTRACT_PATH)


def _token_store_src() -> str:
    return _read(TOKEN_STORE_PATH)


def test_story_11_2_required_gdscript_files_exist() -> None:
    required = [
        SERVICE_PATH,
        PROTOCOL_PATH,
        RECONNECT_PATH,
        TOKEN_CONTRACT_PATH,
        TOKEN_STORE_PATH,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    assert not missing, f"Missing Story 11.2 runtime files under Internal/Platform/GDScript/: {missing}"


def test_story_11_2_protocol_reuses_story_11_1_bsatn_helpers() -> None:
    content = _protocol_src()
    assert 'preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_reader.gd")' in content
    assert 'preload("res://addons/godot_spacetime/src/Internal/Platform/GDScript/bsatn_writer.gd")' in content
    assert "decompress_gzip" in content, (
        "connection_protocol.gd must route compressed inbound payloads through BsatnReader.decompress_gzip()"
    )


def test_story_11_2_bsatn_reader_and_writer_have_fixed_width_helpers() -> None:
    assert "func read_fixed_bytes" in _read(BSATN_READER_PATH)
    assert "func write_fixed_bytes" in _read(BSATN_WRITER_PATH)


def test_story_11_2_connection_service_uses_required_websocketpeer_client_apis() -> None:
    content = _service_src()
    for expected in (
        "connect_to_url(",
        ".poll()",
        ".get_ready_state()",
        ".get_available_packet_count()",
        ".get_packet()",
        ".put_packet(",
        ".close(",
    ):
        assert expected in content, (
            "gdscript_connection_service.gd must use the Godot-native WebSocketPeer client APIs. "
            f"Missing {expected!r}."
        )


def test_story_11_2_connection_service_exposes_runtime_neutral_lifecycle_signals() -> None:
    content = _service_src()
    for expected in (
        "signal state_changed(status)",
        "signal connection_opened(event)",
        "signal connection_closed(event)",
        "signal protocol_message(message)",
    ):
        assert expected in content, (
            "gdscript_connection_service.gd must expose the runtime-neutral lifecycle surface for the smoke harness. "
            f"Missing {expected!r}."
        )


def test_story_11_2_lifecycle_state_names_and_status_strings_match_repo_contract() -> None:
    content = _service_src()
    for expected in (
        'const STATE_DISCONNECTED := "Disconnected"',
        'const STATE_CONNECTING := "Connecting"',
        'const STATE_CONNECTED := "Connected"',
        'const STATE_DEGRADED := "Degraded"',
        "DISCONNECTED — not connected to SpacetimeDB",
        "CONNECTING — opening a session to %s/%s",
        "CONNECTED — active session established",
        "CONNECTED — authenticated session established",
        "CONNECTED — active session established after recovery",
        "DEGRADED — session experiencing issues; reconnecting",
    ):
        assert expected in content, (
            "Story 11.2 must preserve the documented connection lifecycle vocabulary and support strings. "
            f"Missing {expected!r}."
        )


def test_story_11_2_state_machine_semantics_match_connection_state_machine_cs() -> None:
    content = _service_src()
    for expected in (
        "STATE_DISCONNECTED:",
        "return next == STATE_CONNECTING",
        "STATE_CONNECTING:",
        "return next == STATE_CONNECTED or next == STATE_DISCONNECTED",
        "STATE_CONNECTED:",
        "return next == STATE_DEGRADED or next == STATE_DISCONNECTED",
        "STATE_DEGRADED:",
        "return next == STATE_CONNECTED or next == STATE_DISCONNECTED",
    ):
        assert expected in content, (
            "gdscript_connection_service.gd must mirror the .NET connection-state-machine transition rules. "
            f"Missing {expected!r}."
        )


def test_story_11_2_reconnect_policy_matches_dotnet_defaults() -> None:
    content = _reconnect_src()
    assert "const DEFAULT_MAX_ATTEMPTS := 3" in content
    assert "pow(2.0, attempt_number - 1)" in content, (
        "reconnect_policy.gd must use the exponential backoff formula 2^(attempt-1)."
    )
    assert '"attempt_number": _attempts_used' in content


def test_story_11_2_service_uses_reconnect_policy_wording_and_attempt_budget() -> None:
    content = _service_src()
    assert "_reconnect_policy.try_begin_retry()" in content
    assert "attempt %d/%d, backoff %ss" in content, (
        "gdscript_connection_service.gd must surface the retry budget and backoff in the Degraded message."
    )
    assert "_reconnect_policy.max_attempts" in content


def test_story_11_2_token_store_contract_and_default_path_exist() -> None:
    contract = _token_contract_src()
    implementation = _token_store_src()
    for expected in ("func get_token", "func store_token", "func clear_token"):
        assert expected in contract, f"token_store.gd must declare {expected}"
        assert expected in implementation, f"file_token_store.gd must implement {expected}"
    assert 'const DEFAULT_TOKEN_PATH := "user://spacetime/auth/token"' in implementation, (
        "file_token_store.gd must use user://spacetime/auth/token as the default persistence root."
    )
    assert "ProjectSettings.globalize_path(token_dir)" in implementation, (
        "file_token_store.gd must map user:// to an absolute writable directory for file-backed persistence."
    )


def test_story_11_2_auth_failure_routing_strings_are_present() -> None:
    content = _service_src()
    for expected in (
        "stored token was rejected",
        "authentication failed",
        "connection failed (credentials were provided but the cause is ambiguous)",
        'const AUTH_TOKEN_EXPIRED := "TokenExpired"',
        'const AUTH_AUTH_FAILED := "AuthFailed"',
        'const AUTH_CONNECT_FAILED := "ConnectFailed"',
    ):
        assert expected in content, (
            "gdscript_connection_service.gd must preserve the .NET auth failure classification wording. "
            f"Missing {expected!r}."
        )


def test_story_11_2_failed_connects_do_not_emit_connection_closed() -> None:
    content = _service_src()
    start = content.index("func _handle_connect_failure")
    end = content.index("func _schedule_retry_or_disconnect")
    segment = content[start:end]
    assert "emit_signal(\"connection_closed\"" not in segment, (
        "failed connect attempts must not emit connection_closed; only live-session endings may do that."
    )


def test_story_11_2_clean_close_polls_until_state_closed() -> None:
    content = _service_src()
    assert "WebSocketPeer.STATE_CLOSING" in content
    assert "WebSocketPeer.STATE_CLOSED" in content
    assert "_socket.close()" in content


def test_story_11_2_web_guardrails_exist_for_browser_auth_and_no_threads() -> None:
    service = _service_src()
    protocol = _protocol_src()
    for expected in (
        'var allow_header_auth := not OS.has_feature("web")',
        '"query-token"',
        '"authorization-header"',
        "prefer_query_token",
        "query_token_key",
    ):
        haystack = service + "\n" + protocol
        assert expected in haystack, (
            "Story 11.2 must keep desktop header auth and future browser query-token auth behind a small seam. "
            f"Missing {expected!r}."
        )
    for forbidden in ("Thread", ".start_thread", "WorkerThreadPool", "System.Net.WebSockets", "ClientWebSocket"):
        haystack = service + "\n" + protocol + "\n" + _token_store_src() + "\n" + _reconnect_src()
        assert forbidden not in haystack, (
            "Story 11.2 GDScript runtime path must stay main-thread-owned and free of .NET transport leakage. "
            f"Found forbidden token {forbidden!r}."
        )


def test_story_11_2_no_server_side_websocket_usage_or_dotnet_runtime_leakage() -> None:
    haystack = "\n".join(
        (
            _service_src(),
            _protocol_src(),
            _token_contract_src(),
            _token_store_src(),
            _reconnect_src(),
        )
    )
    for forbidden in ("accept_stream", "SpacetimeDB.", "Internal/Connection/", "Internal/Platform/DotNet/"):
        assert forbidden not in haystack, (
            "Story 11.2 must keep the native runtime inside Internal/Platform/GDScript/ without server-side "
            f"or .NET transport leakage. Found forbidden token {forbidden!r}."
        )


def test_story_11_2_compression_mode_consulted_when_draining_packets() -> None:
    content = _service_src()
    assert '_active_compression_mode != "None"' in content, (
        "gdscript_connection_service.gd must consult _active_compression_mode when calling parse_server_message "
        "so compressed inbound payloads are actually decompressed (Task 5.3)."
    )
    assert 'parse_server_message(packet, false)' not in content, (
        "gdscript_connection_service.gd must not hardcode is_compressed=false in _drain_packets."
    )


def test_story_11_2_protocol_errors_drive_connect_failure_or_retry_disconnect() -> None:
    content = _service_src()
    for expected in (
        '"ProtocolError"',
        "_handle_connect_failure(parse_error)",
        "_schedule_retry_or_disconnect(parse_error)",
    ):
        assert expected in content, (
            "gdscript_connection_service.gd must treat parser protocol errors as connection failures while "
            "CONNECTING and as retry/disconnect triggers once CONNECTED, so wire drift is not silently dropped. "
            f"Missing {expected!r}."
        )


def test_story_11_2_handshake_headers_guarded_for_web_compat() -> None:
    content = _service_src()
    assert "if not headers.is_empty():" in content, (
        "gdscript_connection_service.gd must only set socket.handshake_headers when headers are non-empty "
        "so the assignment is skipped on web exports where the property is unsupported (Task 6.4)."
    )


def test_story_11_2_query_token_transport_encodes_key_and_value() -> None:
    content = _protocol_src()
    for expected in (
        "var normalized_query_token_key := query_token_key.strip_edges()",
        "if normalized_query_token_key.is_empty():",
        "normalized_query_token_key = DEFAULT_QUERY_TOKEN_KEY",
        'url += "?%s=%s" % [normalized_query_token_key.uri_encode(), token.uri_encode()]',
    ):
        assert expected in content, (
            "connection_protocol.gd must percent-encode the query-token transport inputs and "
            "fall back to DEFAULT_QUERY_TOKEN_KEY when the override is blank. "
            f"Missing {expected!r}."
        )


def test_story_11_2_clear_token_deletes_file() -> None:
    content = _token_store_src()
    assert "DirAccess.remove_absolute" in content, (
        "file_token_store.gd clear_token() must remove the token file rather than overwriting with an empty string, "
        "so FileAccess.file_exists() returns false after clearing."
    )
    assert 'file.store_string("")' not in content, (
        "file_token_store.gd clear_token() must not overwrite with an empty string; delete the file instead."
    )


def test_story_11_2_single_runtime_service_owns_websocket_transport() -> None:
    service = _service_src()
    protocol = _protocol_src()
    other_files = [_token_contract_src(), _token_store_src(), _reconnect_src()]
    assert "WebSocketPeer" in service, (
        "gdscript_connection_service.gd must be the single runtime service that owns the WebSocketPeer transport."
    )
    for content in [protocol, *other_files]:
        assert "WebSocketPeer" not in content, (
            "Only gdscript_connection_service.gd should own transport concerns; helpers must stay runtime-agnostic."
        )


def test_story_11_2_connection_id_hex_matches_upstream_sdk_random_shape() -> None:
    content = _service_src()
    start = content.index("func _random_connection_id_hex")
    end = content.index("func ", start + 1)
    body = content[start:end]
    assert "RandomNumberGenerator.new()" in body, (
        "_random_connection_id_hex must mirror the upstream Unity SDK's ConnectionId.Random() shape by "
        "allocating a fresh RNG instance for a 16-byte uppercase-hex connection id."
    )
    assert "rng.randomize()" in body, (
        "_random_connection_id_hex must explicitly randomize the fresh RNG before rendering its 16 bytes."
    )
    assert "Crypto.new().generate_random_bytes(16)" not in body, (
        "_random_connection_id_hex must follow the upstream Unity SDK's non-Crypto ConnectionId.Random() "
        "path, not the repo's earlier GDScript-only CSPRNG variant."
    )
    assert 'return ""' not in body, (
        "_random_connection_id_hex must not introduce an empty-string failure branch; the upstream SDK's "
        "ConnectionId.Random() path always returns a 32-char hex id."
    )
