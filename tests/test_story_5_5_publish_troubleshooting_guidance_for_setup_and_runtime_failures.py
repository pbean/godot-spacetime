"""
Story 5.5: Publish Troubleshooting Guidance for Setup and Runtime Failures
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
    assert first_heading != -1, "Expected docs/troubleshooting.md to contain at least one level-2 section"
    return content[:first_heading].strip()


# ---------------------------------------------------------------------------
# 2.1 Existence test
# ---------------------------------------------------------------------------

def test_troubleshooting_md_exists():
    assert (ROOT / "docs/troubleshooting.md").exists(), "docs/troubleshooting.md must exist (Story 5.5)"


# ---------------------------------------------------------------------------
# 2.2 Section presence tests — all eight sections must be present
# ---------------------------------------------------------------------------

def test_troubleshooting_installation_section_present():
    content = _read("docs/troubleshooting.md")
    _section(content, "Installation and Foundation")


def test_troubleshooting_code_generation_section_present():
    content = _read("docs/troubleshooting.md")
    _section(content, "Code Generation")


def test_troubleshooting_compatibility_check_section_present():
    content = _read("docs/troubleshooting.md")
    _section(content, "Compatibility Check")


def test_troubleshooting_connection_section_present():
    content = _read("docs/troubleshooting.md")
    _section(content, "Connection")


def test_troubleshooting_authentication_section_present():
    content = _read("docs/troubleshooting.md")
    _section(content, "Authentication")


def test_troubleshooting_subscriptions_section_present():
    content = _read("docs/troubleshooting.md")
    _section(content, "Subscriptions")


def test_troubleshooting_reducers_section_present():
    content = _read("docs/troubleshooting.md")
    _section(content, "Reducers")


def test_troubleshooting_see_also_section_present():
    content = _read("docs/troubleshooting.md")
    _section(content, "See Also")


# ---------------------------------------------------------------------------
# 2.3 Installation content tests (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_troubleshooting_installation_contains_validate_foundation():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Installation and Foundation")
    assert "validate-foundation.py" in section, \
        "Installation section must reference validate-foundation.py (AC1)"


def test_troubleshooting_installation_contains_godot_version():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Installation and Foundation")
    assert "4.6.2" in section, \
        "Installation section must state Godot version 4.6.2 (AC2)"


def test_troubleshooting_installation_contains_dotnet_version():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Installation and Foundation")
    assert "8.0" in section, \
        "Installation section must state .NET version 8.0 (AC2)"


def test_troubleshooting_installation_contains_spacetimedb_version():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Installation and Foundation")
    assert "2.1" in section, \
        "Installation section must state SpacetimeDB version 2.1+ (AC2)"


# ---------------------------------------------------------------------------
# 2.4 Code generation content tests (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_troubleshooting_codegen_contains_missing():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Code Generation")
    assert "MISSING" in section, \
        "Code Generation section must cover MISSING panel state (AC1)"


def test_troubleshooting_codegen_contains_not_configured():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Code Generation")
    assert "NOT CONFIGURED" in section, \
        "Code Generation section must cover NOT CONFIGURED panel state (AC1)"


def test_troubleshooting_codegen_contains_generate_smoke_test():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Code Generation")
    assert "generate-smoke-test.sh" in section, \
        "Code Generation section must reference generate-smoke-test.sh regeneration command (AC1, AC2)"


# ---------------------------------------------------------------------------
# 2.5 Compatibility content tests (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_troubleshooting_compat_contains_incompatible():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Compatibility Check")
    assert "INCOMPATIBLE" in section, \
        "Compatibility Check section must cover INCOMPATIBLE panel state (AC1)"


def test_troubleshooting_compat_contains_regenerat():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Compatibility Check")
    assert "regenerat" in section.lower(), \
        "Compatibility Check section must explain regeneration path (AC2)"


def test_troubleshooting_compat_contains_version_baseline():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Compatibility Check")
    assert "2.1+" in section, \
        "Compatibility Check section must reference 2.1+ CLI baseline (AC2)"


# ---------------------------------------------------------------------------
# 2.6 Connection content tests (AC: 1, 2)
# ---------------------------------------------------------------------------

def test_troubleshooting_connection_contains_argument_exception():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "ArgumentException" in section, \
        "Connection section must cover ArgumentException programming fault (AC1)"


def test_troubleshooting_connection_contains_degraded():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "DEGRADED" in section, \
        "Connection section must cover DEGRADED panel state (AC1)"


def test_troubleshooting_connection_contains_host():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "Host" in section, \
        "Connection section must reference Host configuration field (AC2)"


def test_troubleshooting_connection_contains_database():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "Database" in section, \
        "Connection section must reference Database configuration field (AC2)"


# ---------------------------------------------------------------------------
# 2.7 Authentication content tests (AC: 1, 2, AC3 terminology)
# ---------------------------------------------------------------------------

def test_troubleshooting_auth_contains_token_expired():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "TokenExpired" in section, \
        "Authentication section must cover TokenExpired auth failure (AC1)"


def test_troubleshooting_auth_contains_auth_failed():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "AuthFailed" in section, \
        "Authentication section must cover AuthFailed auth failure (AC1)"


def test_troubleshooting_auth_contains_clear_token_async():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "ClearTokenAsync" in section, \
        "Authentication section must explain ClearTokenAsync recovery action (AC2)"


def test_troubleshooting_auth_contains_itoken_store():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "ITokenStore" in section, \
        "Authentication section must use ITokenStore terminology (AC3)"


def test_troubleshooting_auth_contains_connection_state_changed():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "ConnectionStateChanged" in section, \
        "Authentication section must reference ConnectionStateChanged signal (AC3)"


# ---------------------------------------------------------------------------
# 2.8 Subscriptions content tests (AC: 1, 2, 3)
# ---------------------------------------------------------------------------

def test_troubleshooting_subscriptions_contains_subscription_failed():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "SubscriptionFailed" in section, \
        "Subscriptions section must reference SubscriptionFailed signal (AC1)"


def test_troubleshooting_subscriptions_contains_subscription_failed_event():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "SubscriptionFailedEvent" in section, \
        "Subscriptions section must use SubscriptionFailedEvent terminology (AC3)"


def test_troubleshooting_subscriptions_contains_error_message():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "ErrorMessage" in section, \
        "Subscriptions section must reference ErrorMessage for recovery path (AC1)"


def test_troubleshooting_subscriptions_contains_regenerat():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "regenerat" in section.lower(), \
        "Subscriptions section must explain regeneration path for table-not-found errors (AC2)"


# ---------------------------------------------------------------------------
# 2.9 Reducer content tests (AC: 1, 3)
# ---------------------------------------------------------------------------

def test_troubleshooting_reducers_contains_reducer_call_failed():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "ReducerCallFailed" in section, \
        "Reducers section must reference ReducerCallFailed signal (AC3)"


def test_troubleshooting_reducers_contains_reducer_failure_category():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "ReducerFailureCategory" in section, \
        "Reducers section must use ReducerFailureCategory terminology (AC3)"


def test_troubleshooting_reducers_contains_gd_push_error():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "GD.PushError" in section, \
        "Reducers section must document GD.PushError programming fault surface (AC3)"


def test_troubleshooting_reducers_contains_out_of_energy():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "OutOfEnergy" in section, \
        "Reducers section must cover OutOfEnergy failure category (AC1)"


# ---------------------------------------------------------------------------
# 2.10 Cross-reference alignment tests (AC: 3)
# ---------------------------------------------------------------------------

def test_troubleshooting_references_demo_readme():
    content = _read("docs/troubleshooting.md")
    assert "demo/README.md" in content, \
        "docs/troubleshooting.md must reference demo/README.md (AC3)"


def test_troubleshooting_references_runtime_boundaries():
    content = _read("docs/troubleshooting.md")
    assert "runtime-boundaries.md" in content, \
        "docs/troubleshooting.md must reference runtime-boundaries.md (AC3)"


def test_troubleshooting_intro_references_behavior_and_terminology_sources():
    content = _read("docs/troubleshooting.md")
    intro = _intro(content)
    assert "sample behavior" in intro and "demo/README.md" in intro, \
        "Troubleshooting intro must identify demo/README.md as the sample-behavior source of truth (Task 1.1, AC3)"
    assert "runtime terminology" in intro and "docs/runtime-boundaries.md" in intro, \
        "Troubleshooting intro must identify docs/runtime-boundaries.md as the terminology source of truth (Task 1.1, AC3)"


# ---------------------------------------------------------------------------
# 2.11 Regression guards — prior story deliverables must remain intact
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


def test_demo_readme_md_exists():
    assert (ROOT / "demo/README.md").exists(), \
        "demo/README.md must exist (Story 5.3 sample regression)"


def test_demo_main_cs_exists():
    assert (ROOT / "demo/DemoMain.cs").exists(), \
        "demo/DemoMain.cs must exist (Story 5.1 C# script regression)"


def test_install_md_contains_supported_foundation_baseline():
    content = _read("docs/install.md")
    assert "Supported Foundation Baseline" in content, \
        "docs/install.md must still contain 'Supported Foundation Baseline' section (Story 1.1 intact)"


def test_quickstart_md_contains_quickstart():
    content = _read("docs/quickstart.md")
    assert "Quickstart" in content, \
        "docs/quickstart.md must still contain 'Quickstart' (Story 1.10 intact)"


def test_runtime_boundaries_md_contains_connection_state():
    content = _read("docs/runtime-boundaries.md")
    assert "ConnectionState" in content, \
        "docs/runtime-boundaries.md must still contain ConnectionState (connection lifecycle terminology intact)"


def test_runtime_boundaries_md_contains_reducer_call_failed():
    content = _read("docs/runtime-boundaries.md")
    assert "ReducerCallFailed" in content, \
        "docs/runtime-boundaries.md must still contain ReducerCallFailed (Story 4.4 reducer error model intact)"


def test_runtime_boundaries_md_contains_itoken_store():
    content = _read("docs/runtime-boundaries.md")
    assert "ITokenStore" in content, \
        "docs/runtime-boundaries.md must still contain ITokenStore (Story 2.1 auth interface intact)"


def test_demo_readme_contains_reducer_interaction():
    content = _read("demo/README.md")
    assert "Reducer Interaction" in content, \
        "demo/README.md must still contain 'Reducer Interaction' section (Story 5.3 reducer section intact)"


def test_demo_main_cs_contains_reducer_call_succeeded():
    content = _read("demo/DemoMain.cs")
    assert "ReducerCallSucceeded" in content, \
        "demo/DemoMain.cs must still contain ReducerCallSucceeded (Story 5.3 wiring intact)"


def test_spacetime_client_cs_exists():
    assert (ROOT / "addons/godot_spacetime/src/Public/SpacetimeClient.cs").exists(), \
        "addons/godot_spacetime/src/Public/SpacetimeClient.cs must exist (SDK public boundary intact)"


# ---------------------------------------------------------------------------
# QA gap fill: section-level cross-reference alignment (AC: 1, 3)
# Each section must cross-reference the authoritative doc it draws from.
# ---------------------------------------------------------------------------

def test_troubleshooting_installation_references_install_md():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Installation and Foundation")
    assert "docs/install.md" in section, \
        "Installation section must cross-reference docs/install.md (Task 1.2, AC1)"


def test_troubleshooting_codegen_references_codegen_md():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Code Generation")
    assert "docs/codegen.md" in section, \
        "Code Generation section must cross-reference docs/codegen.md (Task 1.3, AC1)"


def test_troubleshooting_compat_references_compatibility_matrix_md():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Compatibility Check")
    assert "docs/compatibility-matrix.md" in section, \
        "Compatibility Check section must cross-reference docs/compatibility-matrix.md (Task 1.4, AC1)"


def test_troubleshooting_connection_references_connection_md():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "docs/connection.md" in section, \
        "Connection section must cross-reference docs/connection.md (Task 1.5, AC1)"


def test_troubleshooting_auth_references_runtime_boundaries_md():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "runtime-boundaries.md" in section, \
        "Authentication section must cross-reference runtime-boundaries.md (Task 1.6, AC1)"


def test_troubleshooting_subscriptions_references_runtime_boundaries_md():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "runtime-boundaries.md" in section, \
        "Subscriptions section must cross-reference runtime-boundaries.md (Task 1.7, AC1)"


def test_troubleshooting_reducers_references_runtime_boundaries_md():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "runtime-boundaries.md" in section, \
        "Reducers section must cross-reference runtime-boundaries.md (Task 1.8, AC1)"


def test_troubleshooting_reducers_references_demo_readme():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "demo/README.md" in section, \
        "Reducers section must cross-reference demo/README.md for expected output sequences (Task 1.8, AC1)"


# ---------------------------------------------------------------------------
# QA gap fill: Connection section additional content (AC: 1, 2)
# Task 1.5 specifies NOT CONFIGURED, DISCONNECTED, SpacetimeSettings,
# SpacetimeClient must all appear in the Connection section.
# ---------------------------------------------------------------------------

def test_troubleshooting_connection_contains_not_configured():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "NOT CONFIGURED" in section, \
        "Connection section must cover NOT CONFIGURED panel state (Task 1.5, AC1)"


def test_troubleshooting_connection_contains_disconnected():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "DISCONNECTED" in section, \
        "Connection section must cover DISCONNECTED panel state (Task 1.5, AC1)"


def test_troubleshooting_connection_contains_spacetime_settings():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "SpacetimeSettings" in section, \
        "Connection section must reference SpacetimeSettings resource terminology (Task 1.5, AC3)"


def test_troubleshooting_connection_contains_spacetime_client():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "SpacetimeClient" in section, \
        "Connection section must reference SpacetimeClient terminology (Task 1.5, AC3)"


def test_troubleshooting_connection_locks_argument_exception_boundary():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Connection")
    assert "programming fault" in section and "synchronously" in section and "before any connection attempt" in section, \
        "Connection section must lock the synchronous ArgumentException programming-fault boundary (Task 1.5, AC2, AC3)"


# ---------------------------------------------------------------------------
# QA gap fill: Authentication section additional content (AC: 1, 2, 3)
# Task 1.6 explicitly requires ConnectionAuthState enum type, demo-specific
# ProjectSettingsTokenStore reset instructions, and spacetime/auth/token key.
# ---------------------------------------------------------------------------

def test_troubleshooting_auth_contains_connection_auth_state():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "ConnectionAuthState" in section, \
        "Authentication section must use ConnectionAuthState enum type name (Task 1.6, AC3)"


def test_troubleshooting_auth_contains_project_settings_token_store():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "ProjectSettingsTokenStore" in section, \
        "Authentication section must include demo-specific ProjectSettingsTokenStore reset instructions (Task 1.6, AC2)"


def test_troubleshooting_auth_contains_spacetime_auth_token():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "spacetime/auth/token" in section, \
        "Authentication section must specify spacetime/auth/token Project Settings key (Task 1.6, AC2)"


def test_troubleshooting_auth_locks_connection_closed_boundary_and_fallback():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Authentication")
    assert "ConnectionClosed" in section and "do not emit" in section, \
        "Authentication section must state that failed auth attempts do not emit ConnectionClosed (Task 1.6, AC3)"
    assert "falls back to anonymous" in section, \
        "Authentication section must keep the anonymous fallback when token restoration fails (Task 1.6, AC2)"


# ---------------------------------------------------------------------------
# QA gap fill: Subscriptions section additional content (AC: 1, 3)
# Task 1.7 explicitly requires InvalidOperationException precondition,
# SubscriptionHandle, SubscriptionAppliedEvent, and ConnectionState.
# ---------------------------------------------------------------------------

def test_troubleshooting_subscriptions_contains_invalid_operation_exception():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "InvalidOperationException" in section, \
        "Subscriptions section must cover InvalidOperationException when Subscribe() called before Connected (Task 1.7, AC1)"


def test_troubleshooting_subscriptions_contains_subscription_handle():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "SubscriptionHandle" in section, \
        "Subscriptions section must use SubscriptionHandle terminology (Task 1.7, AC3)"


def test_troubleshooting_subscriptions_contains_subscription_applied_event():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "SubscriptionAppliedEvent" in section, \
        "Subscriptions section must reference SubscriptionAppliedEvent in cross-reference (Task 1.7, AC3)"


def test_troubleshooting_subscriptions_contains_connection_state():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "ConnectionState" in section, \
        "Subscriptions section must reference ConnectionState.Connected precondition for Subscribe() (Task 1.7, AC3)"


def test_troubleshooting_subscriptions_describe_cleanup_and_readability():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Subscriptions")
    assert "Closed" in section and "cleaned up" in section and "authoritative subscription remains readable" in section, \
        "Subscriptions section must explain handle cleanup and authoritative-cache readability after failure (Task 1.7, AC1, AC3)"


# ---------------------------------------------------------------------------
# QA gap fill: Reducers section additional content (AC: 1, 3)
# Task 1.8 explicitly requires ReducerCallError, Unknown ReducerFailureCategory,
# InvokeReducer() method name, and Disconnected state terminology.
# ---------------------------------------------------------------------------

def test_troubleshooting_reducers_contains_reducer_call_error():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "ReducerCallError" in section, \
        "Reducers section must use ReducerCallError type name (Task 1.8, AC3)"


def test_troubleshooting_reducers_contains_unknown():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "Unknown" in section, \
        "Reducers section must cover Unknown ReducerFailureCategory value (Task 1.8, AC1)"


def test_troubleshooting_reducers_contains_invoke_reducer():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "InvokeReducer" in section, \
        "Reducers section must reference InvokeReducer() in programming faults table (Task 1.8, AC1)"


def test_troubleshooting_reducers_contains_disconnected():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "Disconnected" in section, \
        "Reducers section must reference ConnectionStateChanged(Disconnected) as programming fault indicator (Task 1.8, AC3)"


def test_troubleshooting_reducers_lock_two_path_structure():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Reducers")
    assert "### Recoverable Runtime Failures" in section and "### Programming Faults" in section, \
        "Reducers section must preserve the recoverable-vs-programming-fault split (Task 1.8, AC1)"
    assert "ReducerCallFailed" in section and "does **not** fire for programming faults" in section, \
        "Reducers section must state that programming faults do not raise ReducerCallFailed (Task 1.8, AC3)"


def test_troubleshooting_see_also_lists_required_references():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "See Also")
    required_references = (
        "docs/runtime-boundaries.md",
        "demo/README.md",
        "docs/quickstart.md",
        "docs/install.md",
        "docs/codegen.md",
        "docs/compatibility-matrix.md",
    )
    for reference in required_references:
        assert reference in section, \
            f"See Also section must include {reference} (Task 1.9, AC3)"
