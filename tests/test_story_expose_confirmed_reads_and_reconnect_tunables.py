"""
Spec: expose-confirmed-reads-and-reconnect-tunables

Static contract coverage for the new SpacetimeSettings exports (ConfirmedReads,
MaxReconnectAttempts, InitialBackoffSeconds), the adapter wiring for
WithConfirmedReads, the ReconnectPolicy constructor-guard upgrade, the
service's reconfigure-on-Connect() pattern, the SpacetimeDB.* isolation
invariant, and the troubleshooting.md "Tuning" subsection.

Style mirrors tests/test_story_9_1_*.py and tests/test_story_9_2_*.py:
path-based assertions, source-text substring checks, no runtime imports.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETTINGS_REL = "addons/godot_spacetime/src/Public/SpacetimeSettings.cs"
ADAPTER_REL = "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs"
POLICY_REL = "addons/godot_spacetime/src/Internal/Connection/ReconnectPolicy.cs"
SERVICE_REL = "addons/godot_spacetime/src/Internal/Connection/SpacetimeConnectionService.cs"
DOCS_REL = "docs/troubleshooting.md"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# (a) SpacetimeSettings exports + defaults + XML docs
# ---------------------------------------------------------------------------

def test_spacetime_settings_exposes_confirmed_reads_with_default_false() -> None:
    content = _read(SETTINGS_REL)
    assert "[Export]" in content and "public bool ConfirmedReads { get; set; } = false;" in content, (
        "SpacetimeSettings must export ConfirmedReads defaulting to false so the feature is opt-in "
        "(spec Task: SpacetimeSettings exports)."
    )
    for expected in (
        "Defaults to <c>false</c>",
        "next time a connection is opened",
        "WithConfirmedReads(bool)",
    ):
        assert expected in content, (
            f"SpacetimeSettings.ConfirmedReads XML docs must describe {expected!r}."
        )


def test_spacetime_settings_exposes_max_reconnect_attempts_with_default_three() -> None:
    content = _read(SETTINGS_REL)
    assert "[Export]" in content and "public int MaxReconnectAttempts { get; set; } = 3;" in content, (
        "SpacetimeSettings must export MaxReconnectAttempts defaulting to 3 so the default retry "
        "budget reproduces the pre-spec baseline byte-identically."
    )
    for expected in (
        "Defaults to <c>3</c>",
        "next time <c>Connect()</c> is called",
        "at least <c>1</c>",
    ):
        assert expected in content, (
            f"SpacetimeSettings.MaxReconnectAttempts XML docs must describe {expected!r}."
        )


def test_spacetime_settings_exposes_initial_backoff_seconds_with_default_one() -> None:
    content = _read(SETTINGS_REL)
    assert (
        "[Export]" in content
        and "public double InitialBackoffSeconds { get; set; } = 1.0;" in content
    ), (
        "SpacetimeSettings must export InitialBackoffSeconds defaulting to 1.0 so the default "
        "backoff schedule (1s/2s/4s) reproduces the pre-spec baseline byte-identically."
    )
    for expected in (
        "Defaults to <c>1.0</c>",
        "next time <c>Connect()</c> is called",
        "2×",
        "positive finite number",
        "double.NaN",
    ):
        assert expected in content, (
            f"SpacetimeSettings.InitialBackoffSeconds XML docs must describe {expected!r}."
        )


def test_spacetime_settings_public_surface_stays_runtime_neutral() -> None:
    content = _read(SETTINGS_REL)
    assert "SpacetimeDB." not in content, (
        "SpacetimeSettings must remain runtime-neutral and must not reference SpacetimeDB.* types "
        "(Story 9.1/9.2 boundary invariant extended to the new ConfirmedReads / reconnect fields)."
    )


# ---------------------------------------------------------------------------
# (b) Adapter call order: WithCompression → WithLightMode → WithConfirmedReads
#     → WithToken? → OnConnect → OnConnectError → OnDisconnect → Build
# ---------------------------------------------------------------------------

def test_adapter_invokes_with_confirmed_reads_in_canonical_position() -> None:
    content = _read(ADAPTER_REL)
    confirmed_call = 'builder = InvokeMethod(builder, "WithConfirmedReads", settings.ConfirmedReads);'
    compression_call = (
        'builder = InvokeMethod(builder, "WithCompression", MapCompressionMode(settings.CompressionMode));'
    )
    light_mode_call = 'builder = InvokeMethod(builder, "WithLightMode", settings.LightMode);'
    token_call = 'builder = InvokeMethod(builder, "WithToken", settings.Credentials);'
    connect_cb = 'builder = InvokeMethod(builder, "OnConnect", CreateConnectCallback(builder, sink));'
    connect_err_cb = 'builder = InvokeMethod(builder, "OnConnectError", CreateConnectErrorCallback(builder, sink));'
    disconnect_cb = 'builder = InvokeMethod(builder, "OnDisconnect", CreateDisconnectCallback(builder, sink));'
    build_call = '_dbConnection = (IDbConnection?)InvokeMethod(builder, "Build")'

    assert confirmed_call in content, (
        "The .NET adapter must call WithConfirmedReads(settings.ConfirmedReads) so the pinned "
        "ClientSDK 2.1.0 WithConfirmedReads(Boolean) knob is wired from SpacetimeSettings."
    )

    compression_index = content.index(compression_call)
    light_mode_index = content.index(light_mode_call)
    confirmed_index = content.index(confirmed_call)
    token_index = content.index(token_call)
    connect_cb_index = content.index(connect_cb)
    connect_err_index = content.index(connect_err_cb)
    disconnect_cb_index = content.index(disconnect_cb)
    build_index = content.index(build_call)

    assert compression_index < light_mode_index < confirmed_index, (
        "WithConfirmedReads(...) must appear after WithLightMode(...) (which itself follows "
        "WithCompression(...)) so configuration calls stay grouped in their canonical order."
    )
    assert confirmed_index < token_index, (
        "WithConfirmedReads(...) must be applied before the optional WithToken(...) block so "
        "configuration is finalized before credentials are injected."
    )
    for later in (connect_cb_index, connect_err_index, disconnect_cb_index, build_index):
        assert confirmed_index < later, (
            "WithConfirmedReads(...) must be applied before callback registration and Build() so "
            "the requested read mode participates in connection setup."
        )


# ---------------------------------------------------------------------------
# (c) SpacetimeDB.* isolation: the only place SDK symbols may be referenced
#     is Internal/Platform/DotNet/.
# ---------------------------------------------------------------------------

def test_spacetime_db_runtime_types_stay_isolated_to_dotnet_platform() -> None:
    isolation_root = ROOT / "addons/godot_spacetime/src/Internal/Platform/DotNet/"
    offenders: dict[str, list[str]] = {}
    for path in (ROOT / "addons/godot_spacetime/src").rglob("*.cs"):
        try:
            path.relative_to(isolation_root)
            continue  # inside the isolation zone — allowed
        except ValueError:
            pass

        content = path.read_text(encoding="utf-8")
        hits: list[str] = []
        # `using SpacetimeDB;` or `using SpacetimeDB.Foo;` directives are the authoritative
        # signal that a file imports SDK runtime types. Substring checks on "SpacetimeDB."
        # alone would false-positive on doc comments that intentionally name the isolation
        # boundary in XML docs.
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("using SpacetimeDB;") or stripped.startswith("using SpacetimeDB."):
                hits.append(stripped)
        if hits:
            offenders[path.relative_to(ROOT).as_posix()] = hits

    assert not offenders, (
        "SpacetimeDB.* runtime types must stay isolated to Internal/Platform/DotNet/. "
        f"Found SDK using-directives outside the isolation zone: {offenders}"
    )


# ---------------------------------------------------------------------------
# (d) ReconnectPolicy ctor signature + guards
# ---------------------------------------------------------------------------

def test_reconnect_policy_constructor_accepts_initial_backoff_and_guards_both_args() -> None:
    content = _read(POLICY_REL)
    assert "public ReconnectPolicy(int maxAttempts = 3, double initialBackoffSeconds = 1.0)" in content, (
        "ReconnectPolicy must accept (int maxAttempts = 3, double initialBackoffSeconds = 1.0) so "
        "the service can reconfigure the policy from SpacetimeSettings at Connect() time without "
        "breaking the default-construction baseline."
    )
    # maxAttempts guard — preserved from the pre-spec contract
    assert 'throw new ArgumentOutOfRangeException(nameof(maxAttempts)' in content, (
        "ReconnectPolicy must keep throwing ArgumentOutOfRangeException when maxAttempts < 1 so "
        "validation failures route through SpacetimeClient.Connect's ArgumentException catch path."
    )
    assert "maxAttempts < 1" in content, (
        "ReconnectPolicy must explicitly guard maxAttempts < 1 (pre-spec invariant)."
    )
    # initialBackoffSeconds guard — new in this spec
    assert 'throw new ArgumentOutOfRangeException(nameof(initialBackoffSeconds)' in content, (
        "ReconnectPolicy must throw ArgumentOutOfRangeException when initialBackoffSeconds is "
        "non-positive so invalid settings surface via PublishValidationFailure."
    )
    assert "initialBackoffSeconds <= 0" in content, (
        "ReconnectPolicy must explicitly guard initialBackoffSeconds <= 0 (spec validation guard)."
    )
    assert "requires positive initial backoff" in content, (
        "ReconnectPolicy's initialBackoffSeconds validation message must name the positive-backoff "
        "contract so operators can diagnose misconfiguration from the published description."
    )


def test_reconnect_policy_delay_formula_scales_by_initial_backoff() -> None:
    content = _read(POLICY_REL)
    assert "InitialBackoffSeconds * Math.Pow(2, attemptNumber - 1)" in content, (
        "ReconnectPolicy.TryBeginRetry must compute the delay as "
        "InitialBackoffSeconds * Math.Pow(2, attemptNumber - 1) so (a) the default 1.0 reproduces "
        "the 1s/2s/4s baseline and (b) a tuned 0.5s initial backoff yields 0.5/1/2/4/8s."
    )
    assert "public double InitialBackoffSeconds { get; }" in content, (
        "ReconnectPolicy must expose the resolved InitialBackoffSeconds so reviewers can observe "
        "which value is in effect for a given session."
    )


# ---------------------------------------------------------------------------
# (e) SpacetimeConnectionService rebuilds its ReconnectPolicy every Connect()
# ---------------------------------------------------------------------------

def test_connection_service_reconfigures_reconnect_policy_at_connect_time() -> None:
    content = _read(SERVICE_REL)
    # The field must no longer be `readonly` with a constructor-time initializer fixing the
    # retry budget — Connect() now owns policy construction from live settings.
    assert "private readonly ReconnectPolicy _reconnectPolicy" not in content, (
        "SpacetimeConnectionService must not keep _reconnectPolicy as a readonly field so Connect() "
        "can reconstruct the policy from SpacetimeSettings every time a session begins."
    )
    assert "private ReconnectPolicy _reconnectPolicy = new();" in content, (
        "SpacetimeConnectionService must keep a non-readonly _reconnectPolicy initialized to a "
        "default-constructed ReconnectPolicy so the field is never null before Connect() runs."
    )
    # Connect() must rebuild the policy from the incoming settings before the existing Reset()
    # call (mirroring how _activeCompressionMode is read from settings per-Connect).
    reconstruct = (
        "_reconnectPolicy = new ReconnectPolicy(settings.MaxReconnectAttempts, settings.InitialBackoffSeconds);"
    )
    assert reconstruct in content, (
        "SpacetimeConnectionService.Connect() must reconstruct _reconnectPolicy from the incoming "
        "SpacetimeSettings so MaxReconnectAttempts / InitialBackoffSeconds take effect on the next "
        "Connect() call (matches the XML-doc contract)."
    )
    reconstruct_index = content.index(reconstruct)
    reset_index = content.index("_reconnectPolicy.Reset();", reconstruct_index)
    assert reconstruct_index < reset_index, (
        "The new-policy assignment must precede the Reset() call so Reset() operates on the "
        "freshly constructed policy rather than the prior session's."
    )


def test_connection_service_keeps_reconnect_tuning_inside_the_isolation_zone() -> None:
    # The new settings must only flow through the service and into the adapter-owned policy;
    # no public surface should expose the runtime policy object, so no public .cs file
    # should grow a reference to MaxReconnectAttempts / InitialBackoffSeconds apart from
    # SpacetimeSettings.cs itself (the opt-in boundary).
    public_root = ROOT / "addons/godot_spacetime/src/Public"
    allow_rel = "addons/godot_spacetime/src/Public/SpacetimeSettings.cs"
    offenders: dict[str, list[str]] = {}
    for path in public_root.rglob("*.cs"):
        rel = path.relative_to(ROOT).as_posix()
        if rel == allow_rel:
            continue
        content = path.read_text(encoding="utf-8")
        hits = [
            term
            for term in ("MaxReconnectAttempts", "InitialBackoffSeconds")
            if term in content
        ]
        if hits:
            offenders[rel] = hits

    assert not offenders, (
        "Reconnect tunables must stay encapsulated: only SpacetimeSettings.cs may reference "
        "MaxReconnectAttempts / InitialBackoffSeconds inside the Public surface. "
        f"Found references elsewhere: {offenders}"
    )


# ---------------------------------------------------------------------------
# (f) docs/troubleshooting.md — Tuning subsection inside Reconnection Behavior
# ---------------------------------------------------------------------------

def _reconnection_behavior_section() -> str:
    content = _read(DOCS_REL)
    marker = "## Reconnection Behavior"
    start = content.index(marker)
    # Next top-level heading ends the section
    rest = content[start + len(marker):]
    end_rel = rest.find("\n## ")
    return content[start:] if end_rel == -1 else content[start:start + len(marker) + end_rel]


def test_troubleshooting_reconnection_section_keeps_story_5_5_locked_strings() -> None:
    # Regression guard: the spec explicitly must not touch paragraphs that contain the
    # Story-5.5-locked strings. Re-check the critical locks here so a future refactor
    # of this Tuning content can't accidentally break the sibling Story 5.5 suite.
    section = _reconnection_behavior_section()
    for locked in (
        "3 attempts",
        "1s, 2s, 4s",
        "reconnecting (attempt N/3, backoff Xs)",
        "ReconnectPolicy",
        "DEGRADED",
        "CONNECTED",
        "DISCONNECTED",
        "ConnectionStateChanged",
        "ConnectionClosed",
        "misconfiguration",
    ):
        assert locked in section, (
            f"Reconnection Behavior section must keep Story-5.5-locked string {locked!r} intact."
        )


def test_troubleshooting_reconnection_section_documents_new_tuning_knobs() -> None:
    section = _reconnection_behavior_section()
    assert "### Tuning" in section, (
        "Reconnection Behavior must gain a 'Tuning' subsection so the new SpacetimeSettings knobs "
        "are discoverable from the same section that already documents the defaults."
    )
    for expected in (
        "SpacetimeSettings.MaxReconnectAttempts",
        "SpacetimeSettings.InitialBackoffSeconds",
        "`3`",
        "`1.0`",
    ):
        assert expected in section, (
            f"Reconnection Behavior 'Tuning' subsection must document {expected!r}."
        )
