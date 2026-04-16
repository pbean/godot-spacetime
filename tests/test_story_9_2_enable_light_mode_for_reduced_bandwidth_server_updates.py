"""
Story 9.2: Enable Light Mode for Reduced-Bandwidth Server Updates

Static contract coverage for the public light-mode setting, internal builder
wiring, public payload guardrails, documentation, and regression anchors from
Stories 3.3, 4.2/4.4, and 9.1.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_spacetime_settings_exports_opt_in_light_mode() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "[Export]" in content and "public bool LightMode { get; set; } = false;" in content, (
        "SpacetimeSettings must expose an exported LightMode property defaulting to false so the "
        "feature remains opt-in for existing projects (Task 1.1, Task 1.4, AC1/AC4)."
    )
    for expected in (
        "Defaults to <c>false</c>",
        "Changing this setting does not mutate an already-active session",
        "only takes effect the next time a connection is opened",
    ):
        assert expected in content, (
            f"SpacetimeSettings.LightMode XML docs must describe {expected!r} (Task 1.4, AC4/AC5)."
        )


def test_adapter_calls_with_light_mode_before_callbacks_and_build() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    light_mode_call = 'builder = InvokeMethod(builder, "WithLightMode", settings.LightMode);'
    compression_call = 'builder = InvokeMethod(builder, "WithCompression", MapCompressionMode(settings.CompressionMode));'
    assert light_mode_call in content, (
        "The .NET adapter must call WithLightMode(settings.LightMode) inside Internal/Platform/DotNet/ "
        "(Task 2.1, Task 2.2, AC1)."
    )
    assert content.index(compression_call) < content.index(light_mode_call), (
        "WithLightMode(...) must appear after WithCompression(...) in the builder call sequence so that "
        "both configuration calls are grouped together before callback registration and Build() (Task 2.1, AC1)."
    )
    for expected_later_call in (
        'builder = InvokeMethod(builder, "OnConnect", CreateConnectCallback(builder, sink));',
        'builder = InvokeMethod(builder, "OnConnectError", CreateConnectErrorCallback(builder, sink));',
        'builder = InvokeMethod(builder, "OnDisconnect", CreateDisconnectCallback(builder, sink));',
        '_dbConnection = (IDbConnection?)InvokeMethod(builder, "Build")',
    ):
        assert content.index(light_mode_call) < content.index(expected_later_call), (
            "WithLightMode(settings.LightMode) must be applied before callback registration and Build() "
            "so the active session is built with the requested light-mode setting (Task 2.1, Task 2.2, AC1)."
        )


def test_connection_service_keeps_light_mode_as_connect_time_behavior() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert "LightMode" not in content, (
        "SpacetimeConnectionService should keep light mode as connect-time adapter configuration rather than "
        "trying to mutate the active session in place (Task 2.4, AC5)."
    )


def test_light_mode_does_not_add_parallel_transport_code() -> None:
    forbidden_terms = (
        "System.Net.WebSockets",
        "ClientWebSocket",
        "TransactionUpdateLight",
        "TransactionUpdate",
        "protocol parser",
    )
    offenders: dict[str, list[str]] = {}
    for path in (ROOT / "addons/godot_spacetime/src").rglob("*.cs"):
        rel = path.relative_to(ROOT).as_posix()
        content = path.read_text(encoding="utf-8")
        hits = [term for term in forbidden_terms if term in content]
        if hits:
            offenders[rel] = hits

    assert not offenders, (
        "Story 9.2 must keep light-mode behavior inside the existing connection-service -> adapter path "
        "rather than introducing a parallel transport/parser implementation. "
        f"Found forbidden terms in: {offenders}"
    )


def test_public_row_and_reducer_payloads_do_not_gain_synthetic_metadata_fields() -> None:
    row_changed = _read("addons/godot_spacetime/src/Public/Subscriptions/RowChangedEvent.cs")
    reducer_result = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    reducer_error = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")

    for content, rel in (
        (row_changed, "RowChangedEvent.cs"),
        (reducer_result, "ReducerCallResult.cs"),
        (reducer_error, "ReducerCallError.cs"),
    ):
        for forbidden in (
            "CallerIdentity",
            "EnergyConsumed",
            "TotalHostExecutionDuration",
            "ReducerEventContext",
            "IReducerEventContext",
            "Event<Reducer>",
        ):
            assert forbidden not in content, (
                f"{rel} must not grow public reducer-metadata placeholders or low-level runtime types "
                f"for Story 9.2. Found forbidden token {forbidden!r}."
            )


def test_row_callback_adapter_still_discards_context_and_forwards_only_row_deltas() -> None:
    content = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkRowCallbackAdapter.cs")
    assert 'var ctxParam = Expression.Parameter(parameters[0].ParameterType, "ctx");' in content, (
        "Story 3.3's row callback adapter must still receive the generated context parameter explicitly."
    )
    assert "Expression.Call(sinkConst, sinkMethod, tableNameConst, rowAsObject)" in content, (
        "Insert/delete row callbacks must still forward only table name plus row payload to the public sink "
        "(Task 3.3, Story 3.3 regression anchor)."
    )
    assert "Expression.Call(sinkConst, sinkMethod, tableNameConst, oldRowAsObject, newRowAsObject)" in content, (
        "Update row callbacks must still forward only table name plus row payloads to the public sink "
        "(Task 3.3, Story 3.3 regression anchor)."
    )


def test_reducer_result_surfaces_remain_the_existing_story_4_2_and_4_4_contracts() -> None:
    result = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs")
    error = _read("addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs")
    assert "public string ReducerName { get; }" in result and "public string InvocationId { get; }" in result
    assert "public DateTimeOffset CalledAt { get; }" in result and "public DateTimeOffset CompletedAt { get; }" in result
    assert "public ReducerFailureCategory FailureCategory { get; }" in error
    assert "public string RecoveryGuidance { get; }" in error


def test_story_9_1_compression_wiring_remains_intact() -> None:
    adapter = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")
    service = _read("addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs")
    assert 'builder = InvokeMethod(builder, "WithCompression", MapCompressionMode(settings.CompressionMode));' in adapter
    assert "GetEffectiveCompressionMode(settings.CompressionMode)" in service
    assert "_activeCompressionMode = MessageCompressionMode.None;" in service


def test_docs_cover_light_mode_default_reconnect_semantics_and_supported_stack_ambiguity() -> None:
    docs = {
        "docs/runtime-boundaries.md": (
            "LightMode",
            "false",
            "next connection",
            "light_mode was removed in 2.0",
            "WithLightMode(bool)",
            "observed runtime behavior",
        ),
        "docs/connection.md": (
            "LightMode",
            "false",
            "next connection",
            "current session",
        ),
        "docs/quickstart.md": (
            "LightMode",
            "false",
            "next connection",
        ),
        "docs/troubleshooting.md": (
            "LightMode",
            "next connection",
            "no synthetic reducer metadata",
            "observed runtime behavior",
        ),
        "demo/README.md": (
            "LightMode",
            "false",
            "next connection",
        ),
    }
    for rel, expected_terms in docs.items():
        content = _read(rel)
        for expected in expected_terms:
            assert expected in content, (
                f"{rel} must document {expected!r} for Story 9.2 (Task 4.1, Task 4.2, Task 4.3, AC3/AC4/AC5)."
            )


def test_public_light_mode_boundary_stays_runtime_neutral() -> None:
    settings = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    assert "TransactionUpdateLight" not in settings and "SpacetimeDB." not in settings, (
        "The public LightMode surface must remain runtime-neutral and must not expose SpacetimeDB transport types "
        "(Task 1.3)."
    )
