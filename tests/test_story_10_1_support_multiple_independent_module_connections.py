"""
Story 10.1: Support Multiple Independent Module Connections

Static contract coverage for the additive multi-client lookup surface,
deterministic generated-binding selection, RowReceiver client selection, the
secondary generated fixture path, and the required documentation updates.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_story_10_1_required_files_exist() -> None:
    required = [
        "tests/test_story_10_1_multi_module_connections_integration.py",
        "tests/godot_integration/multi_module_smoke.tscn",
        "tests/godot_integration/MultiModuleSmokeRunner.cs",
        "tests/fixtures/generated/multi_module_smoke/README.md",
        "tests/fixtures/generated/multi_module_smoke/SpacetimeDBClient.g.cs",
        "tests/fixtures/generated/multi_module_smoke/Tables/SmokeTest.g.cs",
        "tests/fixtures/generated/multi_module_smoke/Reducers/PingInsert.g.cs",
    ]
    for rel in required:
        assert (ROOT / rel).is_file(), (
            f"{rel} must exist for Story 10.1's red-first test and harness gate "
            "(Task 0.1, Task 0.2, Task 0.3)."
        )


def test_secondary_generated_fixture_is_compiled_and_uses_a_distinct_namespace() -> None:
    csproj = _read("godot-spacetime.csproj")
    fixture_readme = _read("tests/fixtures/generated/multi_module_smoke/README.md")
    fixture_client = _read("tests/fixtures/generated/multi_module_smoke/SpacetimeDBClient.g.cs")

    assert "tests/fixtures/generated/**/*.cs" in csproj, (
        "godot-spacetime.csproj must intentionally compile the secondary generated fixture path "
        "so Story 10.1 can prove multiple generated namespaces in one assembly (Task 0.3, AC5)."
    )
    assert "read-only generated artifact" in fixture_readme.lower() and "do not edit" in fixture_readme.lower(), (
        "The secondary generated fixture README must explicitly mark the files as read-only generated artifacts "
        "(Task 5.5)."
    )
    assert "namespace SpacetimeDB.MultiModuleTypes" in fixture_client, (
        "Story 10.1 must compile a second generated binding set under a distinct namespace instead of reusing "
        "SpacetimeDB.Types (Task 0.3, Task 6.3, AC5)."
    )
    assert "namespace SpacetimeDB.Types" not in fixture_client, (
        "The secondary fixture must not stay in the default namespace or Story 10.1 cannot prove deterministic "
        "per-client binding selection (Task 0.4, AC5)."
    )


def test_spacetime_client_exposes_additive_identifier_and_lookup_surface() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")

    for expected in (
        "DefaultConnectionId",
        "ConnectionId",
        "TryGetClient(",
        "GetClientOrThrow(",
        "RegisterLiveClient(",
        "UnregisterLiveClient(",
    ):
        assert expected in content, (
            "SpacetimeClient must expose an additive identifier and lookup surface for multiple live clients "
            f"without replacing the existing instance API. Missing {expected!r} (Task 1.1, Task 1.2, AC4)."
        )

    assert '"/root/SpacetimeClient"' in content or '"SpacetimeClient"' in content, (
        "Story 10.1 must preserve the existing default single-client identity/path expectations for backward "
        "compatibility (Task 1.1, Task 1.5, AC3)."
    )


def test_spacetime_client_registers_on_enter_tree_and_rejects_duplicate_identifiers() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")

    assert "_EnterTree" in content and "_ExitTree" in content, (
        "Live client registry accuracy must be tied to scene-tree lifecycle hooks "
        "(Task 1.3, AC1/AC4)."
    )
    assert "already registered" in content or "duplicate" in content.lower(), (
        "Duplicate ConnectionId values must fail loudly and deterministically instead of silently letting one "
        "client shadow another (Task 1.4, AC1/AC2/AC4)."
    )
    for expected in (
        "Connect()",
        "Disconnect()",
        "Subscribe(",
        "ReplaceSubscription(",
        "GetDb<TDb>()",
        "GetRows(",
        "QueryAsync<TRow>(",
        "InvokeReducer(",
    ):
        assert expected in content, (
            f"Story 10.1 must preserve the existing instance API unchanged. Missing {expected!r} "
            "(Task 1.5, AC3)."
        )


def test_spacetime_settings_exposes_deterministic_generated_binding_selection() -> None:
    content = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")

    for expected in (
        "DefaultGeneratedBindingsNamespace",
        "GeneratedBindingsNamespace",
        "ResolveGeneratedBindingsNamespace",
    ):
        assert expected in content, (
            "SpacetimeSettings must expose an additive generated-binding selector that preserves the current "
            f"default namespace for single-module projects. Missing {expected!r} (Task 2.1, Task 2.4, AC3/AC5)."
        )


def test_generated_binding_resolution_is_namespace_scoped_not_first_type_wins() -> None:
    resolver_rel = "addons/godot_spacetime/src/Internal/Platform/DotNet/GeneratedBindingTypeResolver.cs"
    resolver = _read(resolver_rel)
    adapter = _read("addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs")

    assert "ResolveDbConnectionType" in resolver and "ResolveRemoteTablesType" in resolver, (
        "Story 10.1 must centralize generated binding resolution in Internal/Platform/DotNet so both connection "
        "setup and RowReceiver can use the same deterministic namespace-scoped logic (Task 2.2, Task 4.2, AC5)."
    )
    assert "generatedBindingsNamespace" in resolver, (
        "The resolver must key off an explicit generated namespace instead of the first matching type found in "
        "the AppDomain (Task 2.2, AC5)."
    )
    assert "SpacetimeDB.Types.DbConnection" not in adapter, (
        "The connection adapter must stop hard-coding SpacetimeDB.Types.DbConnection inside its own resolution "
        "path; Story 10.1 needs deterministic namespace-backed selection (Task 0.4, Task 2.2, AC5)."
    )
    assert "ResolveDbConnectionType(" in adapter and "settings" in adapter, (
        "SpacetimeSdkConnectionAdapter.Open() must resolve the generated DbConnection type from the configured "
        "SpacetimeSettings selector (Task 2.2, Task 2.4, AC5)."
    )


def test_public_surface_does_not_leak_raw_spacetimedb_runtime_types() -> None:
    public_files = [
        "addons/godot_spacetime/src/Public/SpacetimeClient.cs",
        "addons/godot_spacetime/src/Public/SpacetimeSettings.cs",
    ]
    for rel in public_files:
        content = _read(rel)
        code_lines = [
            line for line in content.splitlines()
            if not line.lstrip().startswith("///")
            and not line.lstrip().startswith("//")
        ]
        code_text = "\n".join(code_lines)
        for forbidden in (
            "using SpacetimeDB;",
            "IDbConnection",
            "DbConnection",
            "RemoteTableHandleBase",
        ):
            assert forbidden not in code_text, (
                "Story 10.1 must keep raw generated/runtime types behind the internal isolation boundary. "
                f"Found {forbidden!r} in {rel} (Task 2.3, Task 6.1)."
            )


def test_rowreceiver_supports_target_client_selection_and_scoped_table_resolution() -> None:
    content = _read("addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs")

    for expected in (
        "ClientPath",
        "/root/SpacetimeClient",
        "NotifyPropertyListChanged",
        "ResolveRemoteTablesType",
        "GetResolvedRemoteTablesTypeNameForInspection",
    ):
        assert expected in content, (
            "RowReceiver must additively support selecting a target client and scope its table-name discovery to "
            f"that client's generated binding set. Missing {expected!r} (Task 4.1, Task 4.2, Task 4.5, AC2/AC5)."
        )

    for forbidden in (
        "FindRemoteTablesType(Assembly assembly)",
        "ShouldSkipAssembly(",
    ):
        assert forbidden not in content, (
            "RowReceiver must stop scanning for the first RemoteTables type in loaded assemblies once multiple "
            f"module namespaces can coexist. Found stale token {forbidden!r} (Task 0.4, Task 4.2, AC5)."
        )


def test_connection_auth_status_panel_stays_narrow_and_default_client_only() -> None:
    panel = _read("addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs")
    docs = _read("docs/troubleshooting.md") + "\n" + _read("docs/runtime-boundaries.md")

    assert "TryGetClient" in panel or "SpacetimeClient" in panel, (
        "The status panel must continue binding through the supported public/runtime-neutral client surface "
        "(Task 4.4)."
    )
    assert "default-client-only" in docs.lower() or "default client only" in docs.lower(), (
        "If Story 10.1 keeps the editor status panel scoped to the default client, the docs must say so "
        "explicitly instead of implying full multi-client editor support (Task 4.4, Task 5.3)."
    )


def test_docs_cover_additive_multi_module_workflow_and_keep_single_module_defaults() -> None:
    expected = {
        "docs/codegen.md": (
            "--namespace",
            "multi-module",
            "SpacetimeDB.Types",
            "distinct namespaces",
        ),
        "docs/runtime-boundaries.md": (
            "one `SpacetimeClient` instance still equals one connection owner",
            "lookup-by-identifier",
            "/root/SpacetimeClient",
            "ClientPath",
        ),
        "docs/connection.md": (
            "ConnectionId",
            "GeneratedBindingsNamespace",
            "TryGetClient",
            "zero changes",
        ),
        "docs/troubleshooting.md": (
            "duplicate client identifiers",
            "wrong generated namespace",
            "default-client-only",
        ),
        "docs/quickstart.md": (
            "For multiple modules",
            "docs/connection.md",
        ),
        "demo/README.md": (
            "multi-client",
            "ClientPath",
            "/root/SpacetimeClient",
        ),
    }

    for rel, terms in expected.items():
        content = _read(rel)
        for term in terms:
            assert term in content, (
                f"{rel} must document {term!r} for Story 10.1 while preserving the default single-client path "
                "(Task 4.3, Task 5.1, Task 5.2, Task 5.3, Task 5.4)."
            )


def test_story_1_9_2_x_3_x_7_2_8_x_and_9_x_regression_anchors_remain_intact() -> None:
    client = _read("addons/godot_spacetime/src/Public/SpacetimeClient.cs")
    settings = _read("addons/godot_spacetime/src/Public/SpacetimeSettings.cs")
    runtime_docs = _read("docs/runtime-boundaries.md")
    troubleshooting = _read("docs/troubleshooting.md")

    for expected in (
        "CurrentTelemetry",
        "FrameTick",
        "Subscribe(",
        "ReplaceSubscription(",
        "GetDb<TDb>()",
        "QueryAsync<TRow>(",
        "InvokeReducer(",
    ):
        assert expected in client, (
            f"Story 10.1 must preserve the existing runtime surface and lifecycle ownership. Missing {expected!r} "
            "(Task 3.1, Task 3.5, Task 6.2)."
        )

    for expected in ("CompressionMode", "LightMode", "TokenStore"):
        assert expected in settings, (
            f"Story 10.1 must preserve existing connection settings from Stories 2.x and 9.x. Missing {expected!r} "
            "(Task 6.2)."
        )

    for expected in (
        "GetDb<TDb>()",
        "RowReceiver",
        "CurrentTelemetry",
        "Compression",
        "LightMode",
        "/root/SpacetimeClient",
    ):
        assert expected in runtime_docs or expected in troubleshooting, (
            f"Story 10.1 must keep the established docs anchors intact for prior stories. Missing {expected!r} "
            "(Task 4.3, Task 6.2)."
        )
