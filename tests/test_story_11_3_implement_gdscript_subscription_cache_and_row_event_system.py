"""
Story 11.3: Implement GDScript subscription, cache, and row event system

Static seam checks plus parser-frame coverage for the native GDScript runtime.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import probe_godot_binary

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
HANDLE_PATH = GDSCRIPT_DIR / "gdscript_subscription_handle.gd"
REGISTRY_PATH = GDSCRIPT_DIR / "gdscript_subscription_registry.gd"
CACHE_PATH = GDSCRIPT_DIR / "gdscript_cache_store.gd"
ROW_EVENT_PATH = GDSCRIPT_DIR / "gdscript_row_changed_event.gd"
TABLE_CONTRACT_PATH = GDSCRIPT_DIR / "gdscript_table_contract.gd"

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "gdscript_generated" / "smoke_test"
FIXTURE_README = FIXTURE_DIR / "README.md"
FIXTURE_REMOTE_TABLES = FIXTURE_DIR / "remote_tables.gd"
FIXTURE_REMOTE_REDUCERS = FIXTURE_DIR / "remote_reducers.gd"
FIXTURE_CLIENT = FIXTURE_DIR / "spacetimedb_client.gd"
FIXTURE_SMOKE_TEST = FIXTURE_DIR / "Tables" / "smoke_test_table.gd"
FIXTURE_TYPED_ENTITY = FIXTURE_DIR / "Tables" / "typed_entity_table.gd"

PARSER_PROBE_PATH = ROOT / "tests" / "godot_integration" / "gdscript_protocol_parser_probe.gd"
PARSER_PROBE_SCENE_PATH = "res://tests/godot_integration/gdscript_protocol_parser_probe.tscn"
EVENT_PREFIX = "E2E-EVENT "


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _service_src() -> str:
    return _read(SERVICE_PATH)


def _protocol_src() -> str:
    return _read(PROTOCOL_PATH)


def _parse_events_from_stdout(stdout: bytes) -> list[dict]:
    events: list[dict] = []
    text = stdout.decode("utf-8", errors="replace")
    for raw in text.splitlines():
        stripped = raw.strip()
        idx = stripped.find(EVENT_PREFIX)
        if idx == -1:
            continue
        payload = stripped[idx + len(EVENT_PREFIX):].strip()
        try:
            events.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    return events


def _run_parser_probe() -> list[dict]:
    godot_probe = probe_godot_binary()
    if not godot_probe.available:
        pytest.skip(f"godot-mono not available on PATH: {godot_probe.reason}")

    if not PARSER_PROBE_PATH.exists():
        pytest.fail("gdscript_protocol_parser_probe.gd missing under tests/godot_integration/")

    with tempfile.TemporaryDirectory(prefix="story-11-3-parser-probe-home-") as godot_home:
        env = os.environ.copy()
        env["HOME"] = godot_home
        env["XDG_DATA_HOME"] = godot_home
        env["XDG_CONFIG_HOME"] = godot_home
        proc = subprocess.run(
            [
                godot_probe.path,
                "--headless",
                "--path",
                str(ROOT),
                PARSER_PROBE_SCENE_PATH,
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            timeout=60,
        )
    events = _parse_events_from_stdout(proc.stdout or b"")
    assert proc.returncode == 0, (
        f"protocol parser probe exited with {proc.returncode}. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-800:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-800:]}"
    )
    assert events, (
        "protocol parser probe emitted no events. "
        f"stdout tail: {(proc.stdout or b'').decode('utf-8', 'replace')[-800:]}. "
        f"stderr tail: {(proc.stderr or b'').decode('utf-8', 'replace')[-800:]}"
    )
    return events


def test_story_11_3_required_gdscript_files_exist() -> None:
    required = [
        SERVICE_PATH,
        PROTOCOL_PATH,
        HANDLE_PATH,
        REGISTRY_PATH,
        CACHE_PATH,
        ROW_EVENT_PATH,
        TABLE_CONTRACT_PATH,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    assert not missing, (
        "Story 11.3 must add the subscription/cache helper files under "
        f"Internal/Platform/GDScript/: {missing}"
    )


def test_story_11_3_service_declares_subscription_domain_signals() -> None:
    content = _service_src()
    for expected in (
        "signal subscription_applied(event)",
        "signal subscription_failed(event)",
        "signal row_changed(event)",
    ):
        assert expected in content, (
            "gdscript_connection_service.gd must surface the subscription-domain signals for Story 11.3. "
            f"Missing {expected!r}."
        )


def test_story_11_3_service_exposes_subscription_lifecycle_methods() -> None:
    content = _service_src()
    for expected in (
        "func subscribe(query_sqls: Array)",
        "func unsubscribe(handle: Object)",
        "func replace_subscription(old_handle: Object, new_queries: Array)",
        "func get_remote_tables()",
    ):
        assert expected in content, (
            "gdscript_connection_service.gd must expose the subscription/cache surface for Story 11.3. "
            f"Missing {expected!r}."
        )


def test_story_11_3_service_tracks_pending_replacements_and_request_correlation() -> None:
    content = _service_src()
    for expected in (
        "_next_request_id",
        "_next_handle_id",
        "_pending_subscriptions",
        "_pending_replacements",
        "request_id → handle".replace("→", "->"),
        "_pending_subscriptions.is_empty()",
    ):
        assert expected in content, (
            "Story 11.3 must keep explicit request/handle correlation, overlap-first replacement state, "
            f"and an in-flight subscription guard. Missing {expected!r}."
        )


def test_story_11_3_service_routes_subscription_messages_from_drain_packets() -> None:
    content = _service_src()
    for expected in (
        'emit_signal("protocol_message", message.duplicate(true))',
        '"SubscribeApplied"',
        '"SubscriptionError"',
        '"TransactionUpdate"',
        "_handle_subscribe_applied(",
        "_handle_subscription_error(",
        "_handle_transaction_update(",
    ):
        assert expected in content, (
            "Story 11.3 must extend _drain_packets() to route the new structured subscription messages "
            f"while preserving protocol_message emission. Missing {expected!r}."
        )


def test_story_11_3_protocol_parses_structured_subscription_messages() -> None:
    content = _protocol_src()
    for expected in (
        "_parse_subscribe_applied(",
        "_parse_subscription_error(",
        "_parse_transaction_update(",
        "_parse_query_rows(",
        "_parse_table_update_rows(",
        "_parse_bsatn_row_list(",
    ):
        assert expected in content, (
            "connection_protocol.gd must parse subscription-owned messages into structured envelopes. "
            f"Missing {expected!r}."
        )
    for forbidden in (
        'return _raw_message("SubscribeApplied", tag, payload)',
        'return _raw_message("SubscriptionError", tag, payload)',
        'return _raw_message("TransactionUpdate", tag, payload)',
    ):
        assert forbidden not in content, (
            "Story 11.3 must stop returning raw-payload-only placeholders for subscription-owned messages. "
            f"Found forbidden snippet {forbidden!r}."
        )


def test_story_11_3_protocol_reuses_story_11_1_helpers_and_single_compression_lane() -> None:
    content = _protocol_src()
    assert "BsatnReaderScript.new(" in content
    assert "decompress_gzip" in content
    for expected in (
        "read_u32",
        "read_string",
        "read_array_len",
        "read_fixed_bytes",
    ):
        assert expected in content, (
            "connection_protocol.gd must reuse Story 11.1 BSATN helpers for Story 11.3 parsing. "
            f"Missing {expected!r}."
        )
    for forbidden in ("StreamPeerBuffer", "Compression", "zlib", "brotli"):
        assert forbidden not in content, (
            "Story 11.3 must not introduce a second binary parsing or decompression path in connection_protocol.gd. "
            f"Found forbidden token {forbidden!r}."
        )


def test_story_11_3_fixture_bindings_stay_outside_addon_shipping_boundary() -> None:
    required = [
        FIXTURE_README,
        FIXTURE_REMOTE_TABLES,
        FIXTURE_REMOTE_REDUCERS,
        FIXTURE_CLIENT,
        FIXTURE_SMOKE_TEST,
        FIXTURE_TYPED_ENTITY,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    assert not missing, (
        "Story 11.3 needs test-only GDScript bindings under tests/fixtures/gdscript_generated/smoke_test/. "
        f"Missing {missing}"
    )
    addon_generated = list((ROOT / "addons").rglob("*gdscript_generated*"))
    assert not addon_generated, (
        "Test-only fixture bindings must stay outside addons/ so Story 11.5 remains the shipping-codegen story. "
        f"Found unexpected addon paths: {[str(path.relative_to(ROOT)) for path in addon_generated]}"
    )


def test_story_11_3_fixture_bindings_are_generated_artifacts() -> None:
    readme = _read(FIXTURE_README)
    assert "read-only" in readme
    assert "generate-gdscript-smoke-test.sh" in readme

    for path in (FIXTURE_REMOTE_TABLES, FIXTURE_REMOTE_REDUCERS, FIXTURE_CLIENT, FIXTURE_SMOKE_TEST, FIXTURE_TYPED_ENTITY):
        content = _read(path)
        assert "AUTOMATICALLY GENERATED" in content, (
            f"{path.relative_to(ROOT)} must carry the Story 11.5 generated-file banner."
        )
        assert "WILL NOT BE SAVED" in content, (
            f"{path.relative_to(ROOT)} must preserve the Story 11.5 read-only warning."
        )


def test_story_11_3_native_gdscript_lane_avoids_dotnet_transport_and_editor_scope_creep() -> None:
    sources: list[str] = []
    for path in (
        SERVICE_PATH,
        PROTOCOL_PATH,
        HANDLE_PATH,
        REGISTRY_PATH,
        CACHE_PATH,
        ROW_EVENT_PATH,
        TABLE_CONTRACT_PATH,
    ):
        if path.exists():
            sources.append(_read(path))
    haystack = "\n".join(sources)
    for forbidden in (
        "SpacetimeDB.",
        "Internal/Platform/DotNet/",
        "System.Net.WebSockets",
        "ClientWebSocket",
        "EditorPlugin",
        "EditorInspector",
        "accept_stream",
    ):
        assert forbidden not in haystack, (
            "Story 11.3 must stay in the native GDScript runtime seam without .NET transport or editor-panel leakage. "
            f"Found forbidden token {forbidden!r}."
        )


def test_story_11_3_protocol_parser_probe_exists() -> None:
    assert PARSER_PROBE_PATH.exists(), (
        "Story 11.3 parser-frame coverage requires gdscript_protocol_parser_probe.gd under tests/godot_integration/."
    )


def test_story_11_3_protocol_parser_handles_synthesized_frames() -> None:
    events = _run_parser_probe()
    parsed = {event["name"]: event for event in events if event.get("event") == "parsed"}
    assert {"subscribe_applied", "subscription_error", "transaction_update"} <= parsed.keys(), (
        "protocol parser probe must emit parsed events for subscribe_applied, subscription_error, "
        f"and transaction_update. got {list(parsed.keys())}"
    )

    subscribe_applied = parsed["subscribe_applied"]
    assert subscribe_applied.get("kind") == "SubscribeApplied"
    assert subscribe_applied.get("request_id") == 55
    assert subscribe_applied.get("query_set_id") == 77
    assert subscribe_applied.get("tables") == [
        {
            "table_name": "smoke_test",
            "row_count": 2,
        }
    ]

    subscription_error = parsed["subscription_error"]
    assert subscription_error.get("kind") == "SubscriptionError"
    assert subscription_error.get("request_id") == 55
    assert subscription_error.get("query_set_id") == 77
    assert subscription_error.get("error_message") == "bad sql"

    transaction_update = parsed["transaction_update"]
    assert transaction_update.get("kind") == "TransactionUpdate"
    assert transaction_update.get("query_set_ids") == [77]
    assert transaction_update.get("tables") == [
        {
            "table_name": "smoke_test",
            "variants": ["PersistentTable"],
            "insert_count": 1,
            "delete_count": 1,
        }
    ]
