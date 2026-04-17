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
        "WithToken",
    ):
        assert expected in body, (
            f"Auth Token Transport section must cite {expected!r} as the empirical source"
        )


def test_auth_token_transport_section_documents_prefer_query_token_override():
    body = _section(_read("docs/connection.md"), "Auth Token Transport")
    assert "prefer_query_token" in body, (
        "Auth Token Transport section must document the prefer_query_token override"
    )


def test_cited_source_files_still_contain_cited_symbols():
    """Guardrail: if the source files the doc cites drift, this test fails so the doc and
    the code move together. The doc names three files and four symbols; we assert each
    symbol still lives in its cited file."""
    gdscript_service = _read(
        "addons/godot_spacetime/src/Internal/Platform/GDScript/gdscript_connection_service.gd"
    )
    assert 'allow_header_auth := not OS.has_feature("web")' in gdscript_service, (
        "gdscript_connection_service.gd must still contain the platform-branch rule the doc cites"
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

    dotnet_adapter = _read(
        "addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs"
    )
    assert "WithToken" in dotnet_adapter, (
        "SpacetimeSdkConnectionAdapter.cs must still invoke WithToken"
    )
    assert "prefer_query_token" not in dotnet_adapter, (
        ".NET adapter must not carry the GDScript-side prefer_query_token surface "
        "(doc says the override affects only the GDScript path)"
    )


def test_troubleshooting_web_export_row_links_to_auth_token_transport():
    content = _read("docs/troubleshooting.md")
    section = _section(content, "Web Export (Native GDScript)")
    assert "Browser auth mode is reported as `authorization-header`" in section, (
        "Existing Browser auth mode row must still be present in Web Export section"
    )
    assert "connection.md#auth-token-transport" in section, (
        "Browser auth mode recovery action must link to connection.md#auth-token-transport"
    )
