"""
G10: Document web-export auth token transport.
Static file analysis tests — no Godot runtime, no pytest fixtures.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _section(content: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = content.find(marker)
    assert start != -1, f"Expected to find section heading {marker.strip()!r}"
    start += len(marker)
    next_heading = content.find("\n## ", start)
    if next_heading == -1:
        return content[start:].strip()
    return content[start:next_heading].strip()


def _line_containing(rel: str, needle: str) -> str:
    for line in _read(rel).splitlines():
        if needle in line:
            return line
    raise AssertionError(f"Expected to find line containing {needle!r} in {rel}")


def test_connection_md_has_auth_token_transport_section():
    content = _read("docs/connection.md")
    _section(content, "Auth Token Transport")


def test_auth_token_transport_section_names_both_mechanisms():
    body = _section(_read("docs/connection.md"), "Auth Token Transport")
    assert "Authorization: Bearer" in body, (
        "Auth Token Transport section must name the header transport by its canonical form"
    )
    assert "?<query_token_key>=" in body, (
        "Auth Token Transport section must name the query-string transport by its canonical URL shape"
    )


def test_auth_token_transport_section_cites_platform_branch_rule():
    body = _section(_read("docs/connection.md"), "Auth Token Transport")
    assert 'OS.has_feature("web")' in body, (
        "Auth Token Transport section must cite the OS.has_feature(\"web\") branch rule verbatim"
    )


def test_auth_token_transport_section_cites_source_files():
    body = _section(_read("docs/connection.md"), "Auth Token Transport")
    for expected in (
        "gdscript_connection_service.gd",
        "connection_protocol.gd",
        "SpacetimeSdkConnectionAdapter.cs",
        "WithToken",
        "query_token_key",
        "allow_header_auth",
        "build_transport_request",
        "DEFAULT_QUERY_TOKEN_KEY",
        "Godot C# web export | N/A | Out-of-Scope",
        "compatibility-matrix.md",
    ):
        assert expected in body, (
            f"Auth Token Transport section must cite {expected!r} as the empirical source"
        )


def test_auth_token_transport_section_documents_prefer_query_token_override():
    body = _section(_read("docs/connection.md"), "Auth Token Transport")
    for expected in ("prefer_query_token", "query_token_key"):
        assert expected in body, (
            f"Auth Token Transport section must document the {expected!r} override surface"
        )


def test_cited_source_files_still_contain_cited_symbols():
    """Guardrail: the doc cites symbols by name rather than line number; this test checks
    each cited symbol still lives in its cited source file so doc and code move together."""
    gdscript_service = _read(
        "addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd"
    )
    assert 'allow_header_auth := not OS.has_feature("web")' in gdscript_service, (
        "gdscript_connection_service.gd must still contain the platform-branch rule the doc cites"
    )
    assert '_prefer_query_token = bool(options.get("prefer_query_token"' in gdscript_service, (
        "gdscript_connection_service.gd must still contain the _prefer_query_token initialization from options the doc cites"
    )
    assert '_query_token_key = String(options.get("query_token_key"' in gdscript_service, (
        "gdscript_connection_service.gd must still contain the _query_token_key initialization from options the doc cites"
    )
    assert "ConnectionProtocolScript.build_transport_request(" in gdscript_service, (
        "gdscript_connection_service.gd must still invoke build_transport_request so the doc's call-site reference stays accurate"
    )

    protocol = _read(
        "addons/godot_spacetime/src/Internal/Platform/GDScript/connection_protocol.gd"
    )
    assert "build_transport_request" in protocol, (
        "connection_protocol.gd must still expose build_transport_request"
    )
    assert "prefer_query_token" in protocol, (
        "connection_protocol.gd must still expose the prefer_query_token override"
    )
    assert "DEFAULT_QUERY_TOKEN_KEY" in protocol, (
        "connection_protocol.gd must still expose DEFAULT_QUERY_TOKEN_KEY"
    )
    assert "query_token_key" in protocol, (
        "connection_protocol.gd must still expose the query_token_key override"
    )

    dotnet_adapter = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs"
    )
    assert "WithToken" in dotnet_adapter, (
        "SpacetimeSdkConnectionAdapter.cs must still invoke WithToken"
    )

    compatibility_matrix = _read("docs/compatibility-matrix.md")
    assert "| Godot C# web export | N/A | Out-of-Scope |" in compatibility_matrix, (
        "docs/compatibility-matrix.md must still carry the Godot C# web export Out-of-Scope row that the doc cites"
    )


def test_troubleshooting_web_export_row_links_to_auth_token_transport():
    row = _line_containing(
        "docs/troubleshooting.md",
        "| Browser auth mode is reported as `authorization-header` instead of `query-token` |",
    )
    assert "[connection.md → Auth Token Transport](connection.md#auth-token-transport)" in row, (
        "The Browser auth mode troubleshooting row itself must link to connection.md#auth-token-transport."
    )
