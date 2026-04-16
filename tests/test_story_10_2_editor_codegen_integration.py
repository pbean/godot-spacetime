"""
Story 10.2: live integration coverage for the editor-fetch codegen workflow.

This test is intentionally skip-safe when the local SpacetimeDB runtime or CLI
prerequisites are unavailable. When the runtime is reachable, it mirrors the
editor service's fetch -> --bin-path generate -> detect-godot-types pipeline
and compares the result against a direct --module-path generation run.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
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

    downloaded_wasm = _download_module_artifact(
        runtime_probe.host,
        module_name,
        workspace / "downloaded-module.wasm",
    )

    editor_output = workspace / "generated" / "editor_output"
    cli_output = workspace / "generated" / "cli_output"

    _run_editor_equivalent_codegen(cli_probe.path, downloaded_wasm, editor_output)
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
    downloaded_wasm = Path(editor_codegen_artifacts["workspace"]) / "downloaded-module.wasm"
    assert downloaded_wasm.is_file(), (
        "The live integration path must fetch a wasm/schema artifact from the "
        "SpacetimeDB HTTP surface before running codegen."
    )
    assert downloaded_wasm.stat().st_size > 0, (
        "The downloaded module artifact must be non-empty."
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
        "The editor fetch/bin-path/post-process flow must match the direct "
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
        rel == "downloaded-module.wasm" or
        rel.startswith(f"{editor_output}/") or
        rel.startswith(f"{cli_output}/")
        for rel in all_files
    ), (
        "The editor-equivalent pipeline must not write files outside the declared "
        f"generated output directories. Found: {sorted(all_files)}"
    )


def test_editor_codegen_download_helper_accepts_direct_binary_response(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    binary_payload = b"\x00asm\x01\x00\x00\x00"

    def fake_fetch(url: str) -> tuple[bytes, str]:
        assert url.endswith("/v1/database/story-10-2-binary")
        return binary_payload, "application/wasm"

    monkeypatch.setattr(
        "tests.test_story_10_2_editor_codegen_integration._fetch_bytes",
        fake_fetch,
    )

    destination = tmp_path / "downloaded-module.wasm"
    result = _download_module_artifact("127.0.0.1:3000", "story-10-2-binary", destination)

    assert result == destination
    assert destination.read_bytes() == binary_payload


def test_editor_codegen_download_helper_follows_nested_download_urls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    binary_payload = b"\x00asm\x01\x00\x00\x00"

    def fake_fetch(url: str) -> tuple[bytes, str]:
        if url.endswith("/v1/database/story-10-2-json"):
            return (
                json.dumps({"artifact": {"wasm_download_url": "/artifacts/story-10-2-json.wasm"}}).encode(
                    "utf-8"
                ),
                "application/json",
            )
        if url.endswith("/artifacts/story-10-2-json.wasm"):
            return binary_payload, "application/wasm"
        raise AssertionError(f"unexpected URL fetched: {url}")

    monkeypatch.setattr(
        "tests.test_story_10_2_editor_codegen_integration._fetch_bytes",
        fake_fetch,
    )

    destination = tmp_path / "downloaded-module.wasm"
    result = _download_module_artifact("http://127.0.0.1:3000", "story-10-2-json", destination)

    assert result == destination
    assert destination.read_bytes() == binary_payload


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
        _download_module_artifact("http://127.0.0.1:3000", "story-10-2-auth", tmp_path / "module.wasm")


def test_editor_codegen_download_helper_fails_when_json_has_no_downloadable_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fake_fetch(url: str) -> tuple[bytes, str]:
        if url.endswith("/v1/database/story-10-2-no-artifact"):
            return json.dumps({"module": {"name": "story-10-2-no-artifact"}}).encode("utf-8"), "application/json"
        raise urllib.error.HTTPError(url, 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr(
        "tests.test_story_10_2_editor_codegen_integration._fetch_bytes",
        fake_fetch,
    )

    with pytest.raises(AssertionError, match="Could not fetch a downloadable wasm artifact"):
        _download_module_artifact(
            "http://127.0.0.1:3000",
            "story-10-2-no-artifact",
            tmp_path / "module.wasm",
        )


def test_editor_codegen_helper_detects_json_by_content_type_or_payload_prefix() -> None:
    assert _is_json_payload("application/json", b"\x00asm\x01\x00\x00\x00")
    assert _is_json_payload("application/octet-stream", b'  {"artifact": "/module.wasm"}')
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


def _download_module_artifact(server_host: str, module_name: str, destination: Path) -> Path:
    base_url = _normalize_server_url(server_host)
    candidate_urls = [
        urllib.parse.urljoin(base_url, f"v1/database/{urllib.parse.quote(module_name)}"),
        urllib.parse.urljoin(base_url, f"v1/database/{urllib.parse.quote(module_name)}/wasm"),
        urllib.parse.urljoin(base_url, f"v1/database/{urllib.parse.quote(module_name)}/schema"),
    ]

    last_error = ""
    last_json_payload: bytes | None = None

    for url in candidate_urls:
        try:
            payload, content_type = _fetch_bytes(url)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                pytest.skip(
                    "SpacetimeDB runtime unavailable: anonymous schema access rejected"
                )
            if exc.code == 404:
                continue
            last_error = f"GET {url} returned {exc.code} {exc.reason}"
            continue
        except urllib.error.URLError as exc:
            pytest.skip(
                f"SpacetimeDB runtime unavailable: HTTP fetch failed: {exc.reason}"
            )

        if not _is_json_payload(content_type, payload):
            destination.write_bytes(payload)
            return destination

        last_json_payload = payload
        download_url = _extract_download_url(payload, base_url)
        if download_url is None:
            continue

        nested_payload, nested_content_type = _fetch_bytes(download_url)
        if _is_json_payload(nested_content_type, nested_payload):
            last_json_payload = nested_payload
            continue

        destination.write_bytes(nested_payload)
        return destination

    preview = ""
    if last_json_payload:
        preview = last_json_payload.decode("utf-8", errors="replace")[:200]

    raise AssertionError(
        "Could not fetch a downloadable wasm artifact from the SpacetimeDB HTTP "
        f"surface for {module_name!r}. last_error={last_error!r}, json_preview={preview!r}"
    )


def _fetch_bytes(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
        content_type = response.headers.get_content_type()
    return payload, content_type


def _extract_download_url(payload: bytes, base_url: str) -> str | None:
    document = json.loads(payload.decode("utf-8"))
    return _find_download_url(document, base_url)


def _find_download_url(value: object, base_url: str) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str) and _looks_like_artifact_key(key):
                return urllib.parse.urljoin(base_url, item)
        for item in value.values():
            found = _find_download_url(item, base_url)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_download_url(item, base_url)
            if found:
                return found
    return None


def _looks_like_artifact_key(key: str) -> bool:
    lowered = key.lower()
    return (
        "wasm" in lowered or
        "download" in lowered or
        "artifact" in lowered or
        "module" in lowered
    )


def _normalize_server_url(server_host: str) -> str:
    if "://" not in server_host:
        server_host = f"http://{server_host}"
    return server_host.rstrip("/") + "/"


def _is_json_payload(content_type: str, payload: bytes) -> bool:
    if "json" in (content_type or "").lower():
        return True
    preview = payload[:32].decode("utf-8", errors="ignore").lstrip()
    return preview.startswith("{") or preview.startswith("[")


def _run_editor_equivalent_codegen(cli_path: str, wasm_path: Path, output_dir: Path) -> None:
    _run_subprocess(
        [
            cli_path,
            "generate",
            "--bin-path",
            str(wasm_path),
            "--lang",
            "csharp",
            "--out-dir",
            str(output_dir),
            "--namespace",
            "SpacetimeDB.Types",
            "-y",
        ],
        env=os.environ.copy(),
    )
    _run_subprocess(["python3", str(POST_PROCESSOR), str(output_dir / "Types")], env=os.environ.copy())


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
    )
    _run_subprocess(["python3", str(POST_PROCESSOR), str(output_dir / "Types")], env=os.environ.copy())


def _run_subprocess(command: list[str], *, env: dict[str, str]) -> None:
    result = subprocess.run(
        command,
        cwd=ROOT,
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
