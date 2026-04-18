"""
Story 10.2: live integration coverage for the editor-fetch codegen workflow.

This test is intentionally skip-safe when the local SpacetimeDB runtime or CLI
prerequisites are unavailable. When the runtime is reachable, it mirrors the
editor service's fetch -> --module-def generate -> detect-godot-types pipeline
and compares the result against a direct --module-path generation run.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import pytest

from tests.fixtures.spacetime_runtime import probe_local_runtime, probe_spacetime_cli

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "spacetime" / "modules" / "smoke_test"
POST_PROCESSOR = ROOT / "scripts" / "codegen" / "detect-godot-types.py"
TARGET_WASM = MODULE_PATH / "target" / "wasm32-unknown-unknown" / "release" / "smoke_test.opt.wasm"
SCHEMA_VERSION = 9


@pytest.fixture(scope="module")
def editor_codegen_artifacts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    cli_probe = probe_spacetime_cli()
    if not cli_probe.available:
        pytest.skip(f"spacetime CLI not available on PATH: {cli_probe.reason}")

    runtime_probe = probe_local_runtime(cli_probe.path)
    if not runtime_probe.available:
        pytest.skip(f"SpacetimeDB runtime unavailable: {runtime_probe.reason}")

    module_name = f"story-10-2-{uuid.uuid4().hex[:12]}"
    workspace = tmp_path_factory.mktemp("story-10-2-editor-codegen")
    hand_authored = workspace / "hand-authored.txt"
    hand_authored.write_text("leave-me-alone\n", encoding="utf-8")

    _publish_module(cli_probe.path, runtime_probe.server, module_name)

    downloaded_module_def = _download_module_def(
        runtime_probe.host,
        module_name,
        workspace / "downloaded-module-def.json",
    )

    editor_output = workspace / "generated" / "editor_output"
    cli_output = workspace / "generated" / "cli_output"

    _run_editor_equivalent_codegen(cli_probe.path, downloaded_module_def, editor_output)
    _run_cli_codegen(cli_probe.path, cli_output)

    return {
        "workspace": workspace,
        "hand_authored": hand_authored,
        "editor_output": editor_output,
        "cli_output": cli_output,
    }


def test_editor_codegen_integration_can_fetch_schema_from_live_server(
    editor_codegen_artifacts: dict[str, object],
) -> None:
    downloaded_module_def = Path(editor_codegen_artifacts["workspace"]) / "downloaded-module-def.json"
    assert downloaded_module_def.is_file(), (
        "The live integration path must fetch schema JSON from the "
        "SpacetimeDB HTTP surface before running codegen."
    )
    assert downloaded_module_def.stat().st_size > 0, (
        "The downloaded RawModuleDef artifact must be non-empty."
    )
    downloaded_document = json.loads(downloaded_module_def.read_text(encoding="utf-8"))
    assert list(downloaded_document) == ["V9"], (
        "The downloaded artifact must wrap the server schema as RawModuleDef V9 "
        "for the pinned spacetime generate --module-def path."
    )


def test_editor_codegen_integration_produces_generated_files(
    editor_codegen_artifacts: dict[str, object],
) -> None:
    editor_output = Path(editor_codegen_artifacts["editor_output"])
    cli_output = Path(editor_codegen_artifacts["cli_output"])

    editor_files = _hash_tree(editor_output)
    cli_files = _hash_tree(cli_output)

    assert editor_files, "Editor-equivalent codegen must produce generated files."
    assert any(path.endswith(".g.cs") for path in editor_files), (
        "Editor-equivalent codegen must produce .g.cs bindings."
    )
    assert editor_files == cli_files, (
        "The editor fetch/module-def/post-process flow must match the direct "
        "--module-path generation output exactly."
    )


def test_editor_codegen_integration_never_writes_outside_output_dir(
    editor_codegen_artifacts: dict[str, object],
) -> None:
    workspace = Path(editor_codegen_artifacts["workspace"])
    hand_authored = Path(editor_codegen_artifacts["hand_authored"])
    editor_output = Path(editor_codegen_artifacts["editor_output"]).relative_to(workspace).as_posix()
    cli_output = Path(editor_codegen_artifacts["cli_output"]).relative_to(workspace).as_posix()

    all_files = {
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
    }

    assert hand_authored.read_text(encoding="utf-8") == "leave-me-alone\n", (
        "Files outside the generated output directories must remain untouched."
    )
    assert all(
        rel == "hand-authored.txt" or
        rel == "downloaded-module-def.json" or
        rel.startswith(f"{editor_output}/") or
        rel.startswith(f"{cli_output}/")
        for rel in all_files
    ), (
        "The editor-equivalent pipeline must not write files outside the declared "
        f"generated output directories. Found: {sorted(all_files)}"
    )


def test_editor_codegen_download_helper_wraps_versioned_schema_json_for_module_def(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    schema_payload = json.dumps(
        {
            "typespace": {"types": []},
            "tables": [],
            "reducers": [],
            "misc_exports": [],
            "row_level_security": [],
        }
    ).encode("utf-8")

    def fake_fetch(url: str) -> tuple[bytes, str]:
        assert url.endswith("/v1/database/story-10-2-schema/schema?version=9")
        return schema_payload, "application/json"

    monkeypatch.setattr(
        "tests.test_story_10_2_editor_codegen_integration._fetch_bytes",
        fake_fetch,
    )

    destination = tmp_path / "downloaded-module-def.json"
    result = _download_module_def("127.0.0.1:3000", "story-10-2-schema", destination)

    assert result == destination
    assert json.loads(destination.read_text(encoding="utf-8")) == {
        "V9": json.loads(schema_payload.decode("utf-8"))
    }


def test_editor_codegen_download_helper_skips_when_anonymous_auth_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_fetch(url: str) -> tuple[bytes, str]:
        raise urllib.error.HTTPError(url, 401, "Unauthorized", hdrs=None, fp=None)

    monkeypatch.setattr(
        "tests.test_story_10_2_editor_codegen_integration._fetch_bytes",
        fake_fetch,
    )

    with pytest.raises(pytest.skip.Exception, match="anonymous schema access rejected"):
        _download_module_def("http://127.0.0.1:3000", "story-10-2-auth", tmp_path / "module-def.json")


def test_editor_codegen_download_helper_fails_when_schema_payload_is_not_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_fetch(url: str) -> tuple[bytes, str]:
        return b"\x00asm\x01\x00\x00\x00", "application/wasm"

    monkeypatch.setattr(
        "tests.test_story_10_2_editor_codegen_integration._fetch_bytes",
        fake_fetch,
    )

    with pytest.raises(AssertionError, match="Could not fetch a V9 RawModuleDef"):
        _download_module_def(
            "http://127.0.0.1:3000",
            "story-10-2-not-json",
            tmp_path / "module-def.json",
        )


def test_editor_codegen_download_helper_fails_when_schema_json_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_fetch(url: str) -> tuple[bytes, str]:
        return b"{not-valid-json", "application/json"

    monkeypatch.setattr(
        "tests.test_story_10_2_editor_codegen_integration._fetch_bytes",
        fake_fetch,
    )

    with pytest.raises(AssertionError, match="Could not fetch a V9 RawModuleDef"):
        _download_module_def(
            "http://127.0.0.1:3000",
            "story-10-2-invalid-json",
            tmp_path / "module-def.json",
        )


def test_editor_codegen_helper_detects_json_by_content_type_or_payload_prefix() -> None:
    assert _is_json_payload("application/json", b"\x00asm\x01\x00\x00\x00")
    assert _is_json_payload("application/octet-stream", b'  {"typespace": {}}')
    assert not _is_json_payload("application/octet-stream", b"\x00asm\x01\x00\x00\x00")


def test_editor_codegen_helper_normalizes_server_urls() -> None:
    assert _normalize_server_url("127.0.0.1:3000") == "http://127.0.0.1:3000/"
    assert _normalize_server_url("https://example.test/api") == "https://example.test/api/"


def test_editor_codegen_integration_helpers_avoid_hardcoded_sleeps() -> None:
    content = Path(__file__).read_text(encoding="utf-8")
    disallowed_sleep_call = "time" + ".sleep("
    assert disallowed_sleep_call not in content
    assert "timeout=30" in content
    assert "timeout=240" in content


def _publish_module(cli_path: str, server_nickname: str, module_name: str) -> None:
    result = subprocess.run(
        [
            cli_path,
            "publish",
            "--server",
            server_nickname,
            "--anonymous",
            "--module-path",
            str(MODULE_PATH),
            "--yes",
            module_name,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
    )
    if result.returncode != 0:
        pytest.skip(
            "SpacetimeDB runtime unavailable: smoke_test publish failed: "
            f"{(result.stderr or result.stdout).strip()[:240]}"
        )


def _download_module_def(server_host: str, module_name: str, destination: Path) -> Path:
    base_url = _normalize_server_url(server_host)
    schema_url = urllib.parse.urljoin(
        base_url,
        f"v1/database/{urllib.parse.quote(module_name)}/schema?version={SCHEMA_VERSION}",
    )

    try:
        payload, content_type = _fetch_bytes(schema_url)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            pytest.skip(
                "SpacetimeDB runtime unavailable: anonymous schema access rejected"
            )
        raise AssertionError(
            "Could not fetch a V9 RawModuleDef from the SpacetimeDB HTTP surface "
            f"for {module_name!r}. last_error={f'GET {schema_url} returned {exc.code} {exc.reason}'!r}"
        ) from exc
    except urllib.error.URLError as exc:
        pytest.skip(
            f"SpacetimeDB runtime unavailable: HTTP fetch failed: {exc.reason}"
        )

    if not _is_json_payload(content_type, payload):
        raise AssertionError(
            "Could not fetch a V9 RawModuleDef from the SpacetimeDB HTTP surface "
            f"for {module_name!r}. last_error={f'GET {schema_url} returned non-JSON content-type {content_type!r}'!r}"
        )

    try:
        wrapped_payload = _wrap_raw_module_def_v9(payload)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            "Could not fetch a V9 RawModuleDef from the SpacetimeDB HTTP surface "
            f"for {module_name!r}. last_error={f'Invalid schema JSON: {exc}'!r}"
        ) from exc

    destination.write_bytes(wrapped_payload)
    return destination


def _fetch_bytes(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
        content_type = response.headers.get_content_type()
    return payload, content_type


def _wrap_raw_module_def_v9(payload: bytes) -> bytes:
    document = json.loads(payload.decode("utf-8"))
    return json.dumps({"V9": document}, separators=(",", ":")).encode("utf-8")


def _normalize_server_url(server_host: str) -> str:
    if "://" not in server_host:
        server_host = f"http://{server_host}"
    return server_host.rstrip("/") + "/"


def _is_json_payload(content_type: str, payload: bytes) -> bool:
    if "json" in (content_type or "").lower():
        return True
    preview = payload[:32].decode("utf-8", errors="ignore").lstrip()
    return preview.startswith("{") or preview.startswith("[")


def _run_editor_equivalent_codegen(cli_path: str, module_def_path: Path, output_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="story-10-2-editor-cwd-") as temp_cwd:
        temp_cwd_path = Path(temp_cwd)
        (temp_cwd_path / "spacetimedb").mkdir()
        _run_subprocess(
            [
                cli_path,
                "generate",
                "--module-def",
                str(module_def_path),
                "--lang",
                "csharp",
                "--out-dir",
                str(output_dir),
                "--namespace",
                "SpacetimeDB.Types",
                "-y",
            ],
            env=os.environ.copy(),
            cwd=temp_cwd_path,
        )
    _run_subprocess(
        ["python3", str(POST_PROCESSOR), str(output_dir / "Types")],
        env=os.environ.copy(),
        cwd=ROOT,
    )


def _run_cli_codegen(cli_path: str, output_dir: Path) -> None:
    env = os.environ.copy()
    if TARGET_WASM.exists():
        env.setdefault("CARGO_NET_OFFLINE", "true")

    _run_subprocess(
        [
            cli_path,
            "generate",
            "--module-path",
            str(MODULE_PATH),
            "--lang",
            "csharp",
            "--out-dir",
            str(output_dir),
            "--namespace",
            "SpacetimeDB.Types",
            "-y",
        ],
        env=env,
        cwd=ROOT,
    )
    _run_subprocess(
        ["python3", str(POST_PROCESSOR), str(output_dir / "Types")],
        env=os.environ.copy(),
        cwd=ROOT,
    )


def _run_subprocess(command: list[str], *, env: dict[str, str], cwd: Path) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=240,
        env=env,
    )
    assert result.returncode == 0, (
        f"Command failed: {' '.join(command)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def _hash_tree(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes
