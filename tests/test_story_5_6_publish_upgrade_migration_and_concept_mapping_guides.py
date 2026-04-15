"""
Story 5.6: Publish Upgrade, Migration, and Concept-Mapping Guides
Static file analysis tests — no Godot runtime, no pytest fixtures.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _section(content: str, heading: str) -> str:
    marker = f"## {heading}\n\n"
    start = content.find(marker)
    assert start != -1, f"Expected to find section heading {marker.strip()!r}"
    start += len(marker)
    next_heading = content.find("\n## ", start)
    if next_heading == -1:
        return content[start:].strip()
    return content[start:next_heading].strip()


def _intro(content: str) -> str:
    first_heading = content.find("\n## ")
    assert first_heading != -1, "Expected docs/migration-from-community-plugin.md to contain at least one level-2 section"
    return content[:first_heading].strip()


# ---------------------------------------------------------------------------
# 2.1 Existence test
# ---------------------------------------------------------------------------

def test_migration_guide_exists():
    assert (ROOT / "docs/migration-from-community-plugin.md").exists(), \
        "docs/migration-from-community-plugin.md must exist (Story 5.6)"


# ---------------------------------------------------------------------------
# 2.2 Section presence tests — all six sections must be present
# ---------------------------------------------------------------------------

def test_migration_upgrade_section_present():
    content = _read("docs/migration-from-community-plugin.md")
    _section(content, "Upgrade Path Between SDK Releases")


def test_migration_community_plugin_section_present():
    content = _read("docs/migration-from-community-plugin.md")
    _section(content, "Migration from the Community Plugin")


def test_migration_custom_protocol_section_present():
    content = _read("docs/migration-from-community-plugin.md")
    _section(content, "Migration from Custom Protocol Work")


def test_migration_concept_mapping_section_present():
    content = _read("docs/migration-from-community-plugin.md")
    _section(content, "Godot SDK Model and SpacetimeDB Concepts")


def test_migration_multi_runtime_section_present():
    content = _read("docs/migration-from-community-plugin.md")
    _section(content, "Multi-Runtime Product Model")


def test_migration_see_also_section_present():
    content = _read("docs/migration-from-community-plugin.md")
    _section(content, "See Also")


# ---------------------------------------------------------------------------
# 2.3 FR30 upgrade content tests (AC: 1)
# ---------------------------------------------------------------------------

def test_migration_upgrade_contains_addons_path():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Upgrade Path Between SDK Releases")
    assert "addons/godot_spacetime/" in section, \
        "Upgrade section must reference addons/godot_spacetime/ folder replacement step (AC1)"


def test_migration_upgrade_contains_generate_smoke_test():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Upgrade Path Between SDK Releases")
    assert "generate-smoke-test.sh" in section, \
        "Upgrade section must reference generate-smoke-test.sh binding regeneration step (AC1)"


def test_migration_upgrade_contains_validate_foundation():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Upgrade Path Between SDK Releases")
    assert "validate-foundation.py" in section, \
        "Upgrade section must reference validate-foundation.py foundation validation step (AC1)"


def test_migration_upgrade_contains_incompatible():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Upgrade Path Between SDK Releases")
    assert "INCOMPATIBLE" in section, \
        "Upgrade section must reference INCOMPATIBLE compat panel state (AC1)"


def test_migration_upgrade_contains_compatibility_matrix():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Upgrade Path Between SDK Releases")
    assert "docs/compatibility-matrix.md" in section, \
        "Upgrade section must cross-reference docs/compatibility-matrix.md as version baseline (AC1)"


# ---------------------------------------------------------------------------
# 2.4 FR31 community plugin content tests (AC: 2)
# ---------------------------------------------------------------------------

def test_migration_contains_dbc_builder():
    content = _read("docs/migration-from-community-plugin.md")
    assert "DbConnection.Builder()" in content, \
        "migration guide must document DbConnection.Builder() as the community plugin pattern (AC2)"


def test_migration_contains_spacetime_settings():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "SpacetimeSettings" in section, \
        "Community plugin section must reference SpacetimeSettings as the SDK configuration resource (AC2)"


def test_migration_contains_spacetime_client_subscribe():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "SpacetimeClient.Subscribe" in section, \
        "Community plugin section must show SpacetimeClient.Subscribe as the subscription method (AC2)"


def test_migration_contains_invoke_reducer():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "InvokeReducer" in section, \
        "Community plugin section must show InvokeReducer as the reducer invocation method (AC2)"


def test_migration_contains_get_rows():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "GetRows" in section, \
        "Community plugin section must show GetRows as the public cache-access path (AC2)"


def test_migration_contains_itoken_store():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "ITokenStore" in section, \
        "Community plugin section must reference ITokenStore as the auth configuration interface (AC2)"


# ---------------------------------------------------------------------------
# 2.5 FR31 signal migration tests (AC: 2)
# ---------------------------------------------------------------------------

def test_migration_community_plugin_contains_reducer_call_failed():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "ReducerCallFailed" in section, \
        "Community plugin section must document ReducerCallFailed signal as SDK reducer error path (AC2)"


def test_migration_community_plugin_contains_reducer_call_succeeded():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "ReducerCallSucceeded" in section, \
        "Community plugin section must document ReducerCallSucceeded signal as SDK reducer success path (AC2)"


def test_migration_community_plugin_contains_subscription_applied():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "SubscriptionApplied" in section, \
        "Community plugin section must document SubscriptionApplied signal as SDK subscription success path (AC2)"


def test_migration_community_plugin_contains_subscription_failed():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "SubscriptionFailed" in section, \
        "Community plugin section must document SubscriptionFailed signal as SDK subscription error path (AC2)"


# ---------------------------------------------------------------------------
# 2.6 FR31 custom protocol content tests (AC: 2)
# ---------------------------------------------------------------------------

def test_migration_custom_protocol_contains_client_sdk():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from Custom Protocol Work")
    assert "SpacetimeDB.ClientSDK" in section, \
        "Custom protocol section must reference SpacetimeDB.ClientSDK as the raw integration being replaced (AC2)"


def test_migration_custom_protocol_contains_demo_main_cs():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from Custom Protocol Work")
    assert "demo/DemoMain.cs" in section, \
        "Custom protocol section must reference demo/DemoMain.cs as the canonical wiring example (AC2)"


def test_migration_custom_protocol_contains_demo_readme():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from Custom Protocol Work")
    assert "demo/README.md" in section, \
        "Custom protocol section must reference demo/README.md as the end-to-end wiring source (AC2)"


# ---------------------------------------------------------------------------
# 2.7 FR32 concept mapping table tests (AC: 3)
# ---------------------------------------------------------------------------

def test_migration_concept_mapping_contains_db_connection():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "DbConnection" in section, \
        "Concept mapping section must map DbConnection as the SpacetimeDB connection concept (AC3)"


def test_migration_concept_mapping_contains_subscription_handle():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "SubscriptionHandle" in section, \
        "Concept mapping section must map SubscriptionHandle in the concept table (AC3)"


def test_migration_concept_mapping_contains_row_changed():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "RowChanged" in section, \
        "Concept mapping section must map RowChanged signal as the row-update event (AC3)"


def test_migration_concept_mapping_contains_reducer_call_error():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "ReducerCallError" in section, \
        "Concept mapping section must map ReducerCallError as the reducer error type (AC3)"


def test_migration_concept_mapping_contains_ireducer_args():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "IReducerArgs" in section, \
        "Concept mapping section must reference IReducerArgs as the reducer argument interface (AC3)"


# ---------------------------------------------------------------------------
# 2.8 FR32 multi-runtime content tests (AC: 3)
# ---------------------------------------------------------------------------

def test_migration_multi_runtime_contains_gdscript():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Multi-Runtime Product Model")
    assert "GDScript" in section, \
        "Multi-Runtime section must reference GDScript as the future runtime path (AC3)"


def test_migration_multi_runtime_contains_signal_stability():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Multi-Runtime Product Model")
    assert "remain stable" in section, \
        "Multi-Runtime section must state that signal names will remain stable when GDScript support ships (AC3)"


def test_migration_multi_runtime_contains_spacetime_settings():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Multi-Runtime Product Model")
    assert "SpacetimeSettings" in section, \
        "Multi-Runtime section must reference SpacetimeSettings as a stable Godot-native surface (AC3)"


# ---------------------------------------------------------------------------
# 2.9 Cross-reference alignment tests (AC: 3)
# ---------------------------------------------------------------------------

def test_migration_see_also_contains_runtime_boundaries():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "See Also")
    assert "docs/runtime-boundaries.md" in section, \
        "See Also section must reference docs/runtime-boundaries.md (AC3)"


def test_migration_see_also_contains_compatibility_matrix():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "See Also")
    assert "docs/compatibility-matrix.md" in section, \
        "See Also section must reference docs/compatibility-matrix.md (AC3)"


def test_migration_see_also_contains_demo_readme():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "See Also")
    assert "demo/README.md" in section, \
        "See Also section must reference demo/README.md (AC3)"


# ---------------------------------------------------------------------------
# 2.10 Regression guards — prior story deliverables must remain intact
# ---------------------------------------------------------------------------

def test_docs_install_md_exists():
    assert (ROOT / "docs/install.md").exists(), \
        "docs/install.md must exist (Story 5.4 regression)"


def test_docs_quickstart_md_exists():
    assert (ROOT / "docs/quickstart.md").exists(), \
        "docs/quickstart.md must exist (Story 5.4 regression)"


def test_docs_codegen_md_exists():
    assert (ROOT / "docs/codegen.md").exists(), \
        "docs/codegen.md must exist (Story 5.4 regression)"


def test_docs_connection_md_exists():
    assert (ROOT / "docs/connection.md").exists(), \
        "docs/connection.md must exist (Story 5.4 regression)"


def test_docs_runtime_boundaries_md_exists():
    assert (ROOT / "docs/runtime-boundaries.md").exists(), \
        "docs/runtime-boundaries.md must exist (Story 5.4 regression)"


def test_docs_compatibility_matrix_md_exists():
    assert (ROOT / "docs/compatibility-matrix.md").exists(), \
        "docs/compatibility-matrix.md must exist (Story 5.4 regression)"


def test_docs_troubleshooting_md_exists():
    assert (ROOT / "docs/troubleshooting.md").exists(), \
        "docs/troubleshooting.md must exist (Story 5.5 regression)"


def test_demo_readme_md_exists():
    assert (ROOT / "demo/README.md").exists(), \
        "demo/README.md must exist (Story 5.3 sample regression)"


def test_demo_main_cs_exists():
    assert (ROOT / "demo/DemoMain.cs").exists(), \
        "demo/DemoMain.cs must exist (Story 5.1 C# script regression)"


def test_spacetime_client_cs_exists():
    assert (ROOT / "addons/godot_spacetime/src/Public/SpacetimeClient.cs").exists(), \
        "addons/godot_spacetime/src/Public/SpacetimeClient.cs must exist (SDK public boundary intact)"


def test_runtime_boundaries_md_contains_connection_state():
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionState" in content, \
        "docs/runtime-boundaries.md must still contain ConnectionState (connection lifecycle terminology intact)"


def test_runtime_boundaries_md_contains_itoken_store():
    content = _read("docs/runtime-boundaries.md")
    assert "ITokenStore" in content, \
        "docs/runtime-boundaries.md must still contain ITokenStore (Story 2.1 auth interface intact)"


def test_runtime_boundaries_md_contains_reducer_call_failed():
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallFailed" in content, \
        "docs/runtime-boundaries.md must still contain ReducerCallFailed (reducer error model intact)"


def test_compatibility_matrix_md_contains_version_baseline():
    content = _read("docs/compatibility-matrix.md")
    assert "4.6.2" in content, \
        "docs/compatibility-matrix.md must still contain 4.6.2 version baseline (Story 5.4 regression)"


def test_troubleshooting_md_contains_token_expired():
    content = _read("docs/troubleshooting.md")
    assert "TokenExpired" in content, \
        "docs/troubleshooting.md must still contain TokenExpired (Story 5.5 intact)"


def test_demo_readme_contains_reducer_interaction():
    content = _read("demo/README.md")
    assert "Reducer Interaction" in content, \
        "demo/README.md must still contain 'Reducer Interaction' section (Story 5.3 reducer section intact)"


def test_demo_main_cs_contains_reducer_call_succeeded():
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallSucceeded" in content, \
        "demo/DemoMain.cs must still contain ReducerCallSucceeded (Story 5.3 wiring intact)"


# ---------------------------------------------------------------------------
# GAP FILL: Opening paragraph cross-reference tests
# ---------------------------------------------------------------------------

def test_migration_intro_contains_demo_demoMain_cs():
    content = _read("docs/migration-from-community-plugin.md")
    intro = _intro(content)
    assert "demo/DemoMain.cs" in intro, \
        "Opening paragraph must reference demo/DemoMain.cs as the canonical end-to-end path"


def test_migration_intro_contains_demo_readme():
    content = _read("docs/migration-from-community-plugin.md")
    intro = _intro(content)
    assert "demo/README.md" in intro, \
        "Opening paragraph must reference demo/README.md as the canonical end-to-end path"


def test_migration_intro_contains_runtime_boundaries():
    content = _read("docs/migration-from-community-plugin.md")
    intro = _intro(content)
    assert "docs/runtime-boundaries.md" in intro, \
        "Opening paragraph must reference docs/runtime-boundaries.md as the public API vocabulary source"


def test_migration_intro_contains_compatibility_matrix():
    content = _read("docs/migration-from-community-plugin.md")
    intro = _intro(content)
    assert "docs/compatibility-matrix.md" in intro, \
        "Opening paragraph must reference docs/compatibility-matrix.md as the version baseline source"


# ---------------------------------------------------------------------------
# GAP FILL: Community plugin sub-section heading presence (### headings)
# ---------------------------------------------------------------------------

def test_migration_community_plugin_has_configuration_subsection():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "### Configuration and Connection" in section, \
        "Community plugin section must have '### Configuration and Connection' sub-heading"


def test_migration_community_plugin_has_subscriptions_subsection():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "### Subscriptions" in section, \
        "Community plugin section must have '### Subscriptions' sub-heading"


def test_migration_community_plugin_has_reducers_subsection():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "### Reducers" in section, \
        "Community plugin section must have '### Reducers' sub-heading"


def test_migration_community_plugin_has_cache_access_subsection():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "### Cache Access" in section, \
        "Community plugin section must have '### Cache Access' sub-heading"


# ---------------------------------------------------------------------------
# GAP FILL: Community plugin section — additional API terms
# ---------------------------------------------------------------------------

def test_migration_community_plugin_contains_row_changed():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "RowChanged" in section, \
        "Community plugin section must document RowChanged signal as the row-update event (AC2)"


def test_migration_community_plugin_contains_failure_category():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "FailureCategory" in section, \
        "Community plugin section must reference FailureCategory on ReducerCallError (AC2)"


def test_migration_community_plugin_contains_error_message():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "ErrorMessage" in section, \
        "Community plugin section must reference ErrorMessage on SubscriptionFailedEvent (AC2)"


def test_migration_community_plugin_contains_subscription_handle():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "SubscriptionHandle" in section, \
        "Community plugin section must reference SubscriptionHandle returned by Subscribe() (AC2)"


def test_migration_community_plugin_contains_reducer_call_result():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "ReducerCallResult" in section, \
        "Community plugin section must reference ReducerCallResult as the reducer success argument type (AC2)"


def test_migration_community_plugin_contains_reducer_call_error():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "ReducerCallError" in section, \
        "Community plugin section must reference ReducerCallError as the reducer failure argument type (AC2)"


def test_migration_community_plugin_contains_connection_db_wildcard():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from the Community Plugin")
    assert "connection.Db.*" in section, \
        "Community plugin section must document the generic connection.Db.* cache migration pattern (Task 1.3, AC2)"


# ---------------------------------------------------------------------------
# GAP FILL: Custom protocol section — additional terms from migration steps
# ---------------------------------------------------------------------------

def test_migration_custom_protocol_contains_connection_state_changed():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from Custom Protocol Work")
    assert "ConnectionStateChanged" in section, \
        "Custom protocol section must list ConnectionStateChanged as a signal to connect (AC2)"


def test_migration_custom_protocol_contains_get_rows():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from Custom Protocol Work")
    assert "GetRows" in section, \
        "Custom protocol section must reference GetRows as the replacement for manual table reads (AC2)"


def test_migration_custom_protocol_contains_invoke_reducer():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Migration from Custom Protocol Work")
    assert "InvokeReducer" in section, \
        "Custom protocol section must reference InvokeReducer as the replacement for direct reducer calls (AC2)"


# ---------------------------------------------------------------------------
# GAP FILL: Concept mapping section — additional terms not yet tested
# ---------------------------------------------------------------------------

def test_migration_concept_mapping_contains_connection_state_changed():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "ConnectionStateChanged" in section, \
        "Concept mapping section must map ConnectionStateChanged as the connection lifecycle signal (AC3)"


def test_migration_concept_mapping_contains_itoken_store():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "ITokenStore" in section, \
        "Concept mapping section must map ITokenStore as the auth token interface (AC3)"


def test_migration_concept_mapping_contains_reducer_call_succeeded():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "ReducerCallSucceeded" in section, \
        "Concept mapping section must map ReducerCallSucceeded signal as reducer success event (AC3)"


def test_migration_concept_mapping_contains_reducer_call_result():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "ReducerCallResult" in section, \
        "Concept mapping section must reference ReducerCallResult as the reducer success argument type (AC3)"


def test_migration_concept_mapping_contains_subscription_applied():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "SubscriptionApplied" in section, \
        "Concept mapping section must map SubscriptionApplied signal as subscription success event (AC3)"


def test_migration_concept_mapping_contains_subscription_failed():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Godot SDK Model and SpacetimeDB Concepts")
    assert "SubscriptionFailed" in section, \
        "Concept mapping section must map SubscriptionFailed signal as subscription error event (AC3)"


# ---------------------------------------------------------------------------
# GAP FILL: Multi-runtime section — additional signal names listed
# ---------------------------------------------------------------------------

def test_migration_multi_runtime_contains_row_changed():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Multi-Runtime Product Model")
    assert "RowChanged" in section, \
        "Multi-Runtime section must list RowChanged as a stable signal name when GDScript ships (AC3)"


def test_migration_multi_runtime_contains_connection_state_changed():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Multi-Runtime Product Model")
    assert "ConnectionStateChanged" in section, \
        "Multi-Runtime section must list ConnectionStateChanged as a stable signal name when GDScript ships (AC3)"


def test_migration_multi_runtime_contains_reducer_call_succeeded():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Multi-Runtime Product Model")
    assert "ReducerCallSucceeded" in section, \
        "Multi-Runtime section must list ReducerCallSucceeded as a stable signal name when GDScript ships (AC3)"


def test_migration_multi_runtime_contains_autoload_path():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Multi-Runtime Product Model")
    assert "autoload path" in section, \
        "Multi-Runtime section must state that the autoload path remains stable when GDScript support ships (Task 1.6, AC3)"


def test_migration_multi_runtime_contains_no_scene_rewire_requirement():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "Multi-Runtime Product Model")
    assert "will not need to rewire their scenes" in section, \
        "Multi-Runtime section must state that adopters' scene wiring transfers without change (Task 1.6, AC3)"


# ---------------------------------------------------------------------------
# GAP FILL: See Also section — completeness (all six cross-references present)
# ---------------------------------------------------------------------------

def test_migration_see_also_contains_install_md():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "See Also")
    assert "docs/install.md" in section, \
        "See Also section must reference docs/install.md (AC3 cross-reference completeness)"


def test_migration_see_also_contains_quickstart_md():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "See Also")
    assert "docs/quickstart.md" in section, \
        "See Also section must reference docs/quickstart.md (AC3 cross-reference completeness)"


def test_migration_see_also_contains_troubleshooting_md():
    content = _read("docs/migration-from-community-plugin.md")
    section = _section(content, "See Also")
    assert "docs/troubleshooting.md" in section, \
        "See Also section must reference docs/troubleshooting.md (AC3 cross-reference completeness)"
