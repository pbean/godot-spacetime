"""
Spec: Pluggable public logger interface (G6)

Static-contract coverage for the new GodotSpacetime.Logging.{LogLevel, ILogSink,
GodotConsoleLogSink, SpacetimeLog} public surface, the SpacetimeSettings.LogSink
wiring slot, the SpacetimeClient._EnterTree sink installation, the three active
runtime call-site rewrites (SpacetimeClient.PublishValidationFailure,
RowReceiver._Ready, SpacetimeSdkReducerAdapter.RegisterCallbacks), and the
runtime-boundaries doc augmentation.

Style mirrors tests/test_story_expose_per_second_telemetry_rates.py and peers:
path-based assertions, source-text substring checks, no runtime imports.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LOGLEVEL_REL = "addons/godot_spacetime/src/Public/Logging/LogLevel.cs"
ILOGSINK_REL = "addons/godot_spacetime/src/Public/Logging/ILogSink.cs"
CONSOLESINK_REL = "addons/godot_spacetime/src/Public/Logging/GodotConsoleLogSink.cs"
SPACETIMELOG_REL = "addons/godot_spacetime/src/Public/Logging/SpacetimeLog.cs"
LOGCATEGORY_REL = "addons/godot_spacetime/src/Public/Logging/LogCategory.cs"
SETTINGS_REL = "addons/godot_spacetime/src/Public/SpacetimeSettings.cs"
CLIENT_REL = "addons/godot_spacetime/src/Public/SpacetimeClient.cs"
ROWRECEIVER_REL = "addons/godot_spacetime/src/Public/Scenes/RowReceiver.cs"
REDUCER_ADAPTER_REL = "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs"
DOCS_REL = "docs/runtime-boundaries.md"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# New public surface — files + namespace
# ---------------------------------------------------------------------------

def test_loglevel_file_exists_in_public_logging_namespace() -> None:
    content = _read(LOGLEVEL_REL)
    assert "namespace GodotSpacetime.Logging" in content
    assert re.search(r"public\s+enum\s+LogLevel", content), (
        "LogLevel must be a public enum in GodotSpacetime.Logging"
    )


def test_loglevel_has_exactly_three_values() -> None:
    content = _read(LOGLEVEL_REL)
    match = re.search(r"enum\s+LogLevel\s*\{([^}]*)\}", content, re.DOTALL)
    assert match, "Could not parse LogLevel enum body"
    body = match.group(1)
    members = [
        m.group(1)
        for m in re.finditer(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:,|$)", body, re.MULTILINE)
        if m.group(1)
    ]
    assert members == ["Info", "Warning", "Error"], (
        f"LogLevel must declare exactly Info/Warning/Error in order; got {members}"
    )


def test_ilogsink_interface_shape() -> None:
    content = _read(ILOGSINK_REL)
    assert "namespace GodotSpacetime.Logging" in content
    assert re.search(r"public\s+interface\s+ILogSink", content), (
        "ILogSink must be a public interface"
    )
    # Single method: Write(LogLevel, LogCategory, string, Exception?)
    assert re.search(
        r"void\s+Write\s*\(\s*LogLevel\s+\w+\s*,\s*LogCategory\s+\w+\s*,\s*string\s+\w+\s*,\s*System\.Exception\?\s+\w+\s*=\s*null\s*\)",
        content,
    ), "ILogSink.Write must take (LogLevel, LogCategory, string, System.Exception? = null)"


def test_godot_console_log_sink_default_instance_and_routing() -> None:
    content = _read(CONSOLESINK_REL)
    assert "namespace GodotSpacetime.Logging" in content
    assert re.search(
        r"public\s+sealed\s+class\s+GodotConsoleLogSink\s*:\s*ILogSink",
        content,
    ), "GodotConsoleLogSink must be sealed and implement ILogSink"
    assert re.search(
        r"public\s+static\s+readonly\s+GodotConsoleLogSink\s+Instance\s*=\s*new\s*\(\s*\)\s*;",
        content,
    ), "GodotConsoleLogSink must expose public static readonly Instance"

    # Level-to-GD-method binding must be present on the correct case arms.
    # Regex tolerates whitespace between the case label, GD call, and break.
    for level, gd_call in (
        ("Info", "GD.Print"),
        ("Warning", "GD.PushWarning"),
        ("Error", "GD.PushError"),
    ):
        assert re.search(
            rf"case\s+LogLevel\.{level}\s*:\s*{re.escape(gd_call)}\s*\(",
            content,
        ), f"LogLevel.{level} must route to {gd_call} in the switch"

    # A default arm must exist so future LogLevel values are never silently dropped.
    # Allow an intervening comment between `default:` and the GD.* call.
    assert re.search(r"default\s*:[^}]*?GD\.(Print|PushWarning|PushError)\s*\(", content, re.DOTALL), (
        "GodotConsoleLogSink.Write switch must have a default arm routing to a GD.* method"
    )

    # Category prefix literal: the f-string must actually interpolate {category}.
    assert re.search(r"\$\"\s*\[\s*\{\s*category\s*\}\s*\]", content), (
        "GodotConsoleLogSink.Write must prefix messages with `[{category}] `"
    )

    # Exception append: when exception != null, the interpolated string incorporates it.
    assert re.search(r"exception\s*!=\s*null", content), (
        "GodotConsoleLogSink must null-check the exception before appending it"
    )
    assert "{exception}" in content, (
        "GodotConsoleLogSink must interpolate the exception into the output message"
    )


def test_spacetimelog_facade_default_sink_is_godot_console_sink() -> None:
    content = _read(SPACETIMELOG_REL)
    assert "namespace GodotSpacetime.Logging" in content
    assert re.search(
        r"public\s+static\s+class\s+SpacetimeLog",
        content,
    ), "SpacetimeLog must be a public static class"
    # Sink accessor exists and the backing state initializes to GodotConsoleLogSink.Instance.
    # The accessor may be a plain auto-property or a get/set pair over a backing field —
    # both shapes are acceptable, but the default value must be GodotConsoleLogSink.Instance.
    assert "GodotConsoleLogSink.Instance" in content, (
        "SpacetimeLog must reference GodotConsoleLogSink.Instance as the initial sink value"
    )
    assert re.search(r"public\s+static\s+ILogSink\s+Sink\b", content), (
        "SpacetimeLog must declare `public static ILogSink Sink`"
    )
    # Null-safety: assigning null to Sink must coalesce back to the default sink.
    assert re.search(r"\?\?\s*GodotConsoleLogSink\.Instance", content), (
        "SpacetimeLog.Sink setter must coalesce null assignments to GodotConsoleLogSink.Instance"
    )
    # Three one-liner helpers forwarding into the facade.
    for level in ("Info", "Warning", "Error"):
        assert f"public static void {level}(" in content, (
            f"SpacetimeLog.{level} helper must be present"
        )
    # Facade must guard against throws from the custom sink (honor the ILogSink
    # XML contract "a faulty sink must not take down the SDK runtime call site").
    assert re.search(r"catch\s*\(\s*(System\.)?Exception\s+\w+\s*\)", content), (
        "SpacetimeLog helpers must wrap sink writes in a try/catch so misbehaving sinks "
        "cannot propagate exceptions into SDK call sites"
    )


# ---------------------------------------------------------------------------
# SpacetimeSettings.LogSink property
# ---------------------------------------------------------------------------

def test_spacetime_settings_exposes_logsink_plain_property() -> None:
    content = _read(SETTINGS_REL)
    # Must be a plain ILogSink? property (NOT [Export]-decorated — interfaces can't be exported)
    assert re.search(
        r"public\s+ILogSink\?\s+LogSink\s*\{\s*get\s*;\s*set\s*;\s*\}",
        content,
    ), "SpacetimeSettings must declare LogSink as a plain ILogSink? property"

    # Guard against accidental [Export] on the property. Slice the 400 characters
    # immediately preceding the declaration and fail if any [Export] attribute
    # appears in that span — this catches the attribute whether it sits on the
    # line above the property or on the same line.
    match = re.search(r"public\s+ILogSink\?\s+LogSink\b", content)
    assert match is not None
    preceding = content[max(0, match.start() - 400):match.start()]
    # Find the last closing `}` (end of previous member) or opening `{` (class body)
    # before the LogSink declaration, and examine only the gap between them.
    separators = [m.end() for m in re.finditer(r"[{};]", preceding)]
    gap_start = separators[-1] if separators else 0
    gap = preceding[gap_start:]
    assert "[Export]" not in gap, (
        "SpacetimeSettings.LogSink must not be [Export]-decorated — Godot cannot export "
        "an interface-typed property, and the TokenStore precedent uses a plain property"
    )

    # using directive pulls in the logging namespace
    assert "using GodotSpacetime.Logging;" in content, (
        "SpacetimeSettings.cs must import GodotSpacetime.Logging for ILogSink"
    )


# ---------------------------------------------------------------------------
# SpacetimeClient wiring + PublishValidationFailure routing
# ---------------------------------------------------------------------------

def test_spacetime_client_imports_logging_namespace() -> None:
    content = _read(CLIENT_REL)
    assert "using GodotSpacetime.Logging;" in content, (
        "SpacetimeClient.cs must import GodotSpacetime.Logging"
    )


def test_spacetime_client_enter_tree_installs_sink_before_all_lifecycle_setup() -> None:
    content = _read(CLIENT_REL)
    enter_tree = re.search(
        r"public\s+override\s+void\s+_EnterTree\s*\(\s*\)\s*\{(.*?)\n\s*\}",
        content,
        re.DOTALL,
    )
    assert enter_tree, "Could not locate _EnterTree body"
    body = enter_tree.group(1)
    sink_idx = body.find("SpacetimeLog.Sink = Settings.LogSink")
    assert sink_idx >= 0, "_EnterTree must assign SpacetimeLog.Sink from Settings.LogSink"

    # Sink installation must precede every lifecycle-setup step that could itself
    # emit a diagnostic — RegisterLiveClient (can throw on duplicate ConnectionId),
    # RegisterPerformanceMonitors, and every _connectionService.On* hook-up. If a
    # future log site is added inside any of these, it must route through the
    # app-configured sink, not the process default.
    for marker, description in (
        ("RegisterLiveClient(", "RegisterLiveClient() call"),
        ("RegisterPerformanceMonitors(", "RegisterPerformanceMonitors() call"),
        ("_connectionService.OnStateChanged", "first _connectionService.On* hook-up"),
    ):
        marker_idx = body.find(marker)
        assert marker_idx >= 0, f"Could not locate {description} in _EnterTree"
        assert sink_idx < marker_idx, (
            f"Sink installation must happen before the {description} so any diagnostic "
            f"emitted during setup routes through the app-configured sink"
        )

    # Null guard: only assign when Settings.LogSink is non-null
    assert re.search(
        r"if\s*\(\s*Settings\?\.LogSink\s*!=\s*null\s*\)\s*SpacetimeLog\.Sink\s*=\s*Settings\.LogSink\s*;",
        body,
    ), "Sink installation must be guarded by `Settings?.LogSink != null`"


def test_publish_validation_failure_routes_through_spacetime_log() -> None:
    content = _read(CLIENT_REL)
    method = re.search(
        r"private\s+void\s+PublishValidationFailure\s*\([^)]*\)\s*\{(.*?)\n\s*\}",
        content,
        re.DOTALL,
    )
    assert method, "Could not locate PublishValidationFailure body"
    body = method.group(1)
    assert "SpacetimeLog.Error(LogCategory.Connection, message)" in body, (
        "PublishValidationFailure must log via SpacetimeLog.Error(LogCategory.Connection, message)"
    )
    # The raw GD.PushError(message) must be gone from this method.
    assert "GD.PushError(message)" not in body, (
        "PublishValidationFailure must no longer call GD.PushError directly"
    )


def test_spacetime_client_invoke_reducer_xml_doc_updated() -> None:
    content = _read(CLIENT_REL)
    # The XML doc comment on InvokeReducer previously said "plus GD.PushError" — after G6 it names SpacetimeLog.Error.
    assert "plus <c>SpacetimeLog.Error</c>" in content, (
        "InvokeReducer XML doc must reference SpacetimeLog.Error instead of GD.PushError"
    )


# ---------------------------------------------------------------------------
# RowReceiver + SpacetimeSdkReducerAdapter routing
# ---------------------------------------------------------------------------

ROWRECEIVER_ORIGINAL_MESSAGE_FRAGMENT = (
    "RowReceiver: target SpacetimeClient not found at "
)

REDUCER_ORIGINAL_MESSAGE_FRAGMENT = (
    "SpacetimeSdkReducerAdapter: failed to wire reducer event"
)


def test_row_receiver_imports_logging_namespace() -> None:
    content = _read(ROWRECEIVER_REL)
    assert "using GodotSpacetime.Logging;" in content


def test_row_receiver_routes_through_spacetime_log_warning() -> None:
    content = _read(ROWRECEIVER_REL)
    # Original message text preserved (no byte-level regression)
    assert ROWRECEIVER_ORIGINAL_MESSAGE_FRAGMENT in content, (
        "RowReceiver must retain the original warning message text verbatim"
    )
    # Routed through SpacetimeLog.Warning with Subscription category (tolerate multi-line formatting)
    assert re.search(
        r"SpacetimeLog\.Warning\s*\(\s*LogCategory\.Subscription\s*,",
        content,
    ), "RowReceiver must log via SpacetimeLog.Warning(LogCategory.Subscription, ...)"
    # Raw GD.PushWarning is gone
    assert "GD.PushWarning(" not in content, (
        "RowReceiver must no longer call GD.PushWarning directly"
    )


def test_reducer_adapter_imports_logging_namespace() -> None:
    content = _read(REDUCER_ADAPTER_REL)
    assert "using GodotSpacetime.Logging;" in content


def test_reducer_adapter_routes_through_spacetime_log_error_with_exception() -> None:
    content = _read(REDUCER_ADAPTER_REL)
    assert REDUCER_ORIGINAL_MESSAGE_FRAGMENT in content, (
        "SpacetimeSdkReducerAdapter must retain the original error message text verbatim"
    )
    # Must pass the caught exception `ex` through as the fourth argument — dropping exception
    # context regresses diagnosability and is explicitly forbidden by the spec's Never rule.
    assert re.search(
        r"SpacetimeLog\.Error\s*\(\s*LogCategory\.Reducer\s*,[^;]*?,\s*ex\s*\)\s*;",
        content,
        re.DOTALL,
    ), "SpacetimeSdkReducerAdapter must call SpacetimeLog.Error(LogCategory.Reducer, ..., ex)"
    assert "Godot.GD.PushError(" not in content, (
        "SpacetimeSdkReducerAdapter must no longer call Godot.GD.PushError directly"
    )


# ---------------------------------------------------------------------------
# Existing LogCategory surface — regression guard
# ---------------------------------------------------------------------------

def test_log_category_five_values_preserved() -> None:
    content = _read(LOGCATEGORY_REL)
    for value in ("Connection", "Auth", "Subscription", "Reducer", "Codegen"):
        assert re.search(rf"\b{value}\b", content), (
            f"LogCategory must still declare the {value} value"
        )


# ---------------------------------------------------------------------------
# Public/ isolation boundary — new logging files must be SpacetimeDB-free
# (Story 1.3's parametrized test covers rglob; this is a narrower positive
# guard so a regression surfaces inside this module.)
# ---------------------------------------------------------------------------

def test_new_logging_files_have_no_spacetimedb_reference() -> None:
    for rel in (LOGLEVEL_REL, ILOGSINK_REL, CONSOLESINK_REL, SPACETIMELOG_REL):
        content = _read(rel)
        code_lines = [
            ln for ln in content.splitlines()
            if not re.match(r"\s*(///|//)", ln)
        ]
        code_text = "\n".join(code_lines)
        assert "SpacetimeDB." not in code_text, (
            f"{rel}: SpacetimeDB.* reference found in non-comment code"
        )


# ---------------------------------------------------------------------------
# runtime-boundaries.md augmentation
# ---------------------------------------------------------------------------

def test_runtime_boundaries_names_all_new_logging_tokens() -> None:
    content = _read(DOCS_REL)
    for token in (
        "ILogSink",
        "LogLevel",
        "SpacetimeLog",
        "GodotConsoleLogSink",
        "SpacetimeSettings.LogSink",
    ):
        assert token in content, (
            f"docs/runtime-boundaries.md must name `{token}` in the logging section"
        )
    # Existing LogCategory rows preserved — five values + LogCategory itself.
    for preserved in ("LogCategory", "Connection", "Auth", "Subscription", "Reducer", "Codegen"):
        assert preserved in content, (
            f"docs/runtime-boundaries.md must retain existing LogCategory token `{preserved}`"
        )
    # The "added in a later story" placeholder is gone.
    assert "added in a later story" not in content, (
        "docs/runtime-boundaries.md must no longer carry the `added in a later story` placeholder"
    )
