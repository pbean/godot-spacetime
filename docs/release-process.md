# Release Process

This document is the canonical release checklist for GodotSpacetime SDK maintainers. Follow the steps in order for each release. Record the communication step used for each version in the Release History table so future releases can follow the same path.

## Release Checklist

1. **Update compatibility targets**: edit `docs/compatibility-matrix.md` and `scripts/compatibility/support-baseline.json` for the new version pair; update version references in `docs/install.md` if the supported baseline has changed
2. **Package release candidate**: `python3 scripts/packaging/package-release.py [--version X.Y.Z]` — produces `release-candidates/godot-spacetime-vX.Y.Z.zip`
3. **Validate release candidate**: `python3 scripts/packaging/validate-release-candidate.py [--version X.Y.Z]` (local) or trigger `.github/workflows/release-validation.yml` via GitHub Actions (CI) — produces `release-candidates/validation-report-vX.Y.Z.json`; the report must show `"status": "pass"` before proceeding. The gate includes the Story 7.1 dynamic lifecycle test, which drives a real `Connect()` / `Subscribe()` / `InvokeReducer()` round-trip through a local SpacetimeDB daemon on `127.0.0.1:3000`. Local runs require the daemon to be reachable before invocation (see `docs/troubleshooting.md#running-a-local-spacetimedb-runtime-for-tests`); the CI workflow provisions it automatically. The `--skip-suite` flag bypasses the pytest lane and is reserved for script self-testing only — it must never appear in a release-gate workflow.
4. **Publish release**: `python3 scripts/packaging/publish-release.py [--version X.Y.Z]` (local, requires `gh` CLI and `GH_TOKEN`) or trigger `.github/workflows/release.yml` via GitHub Actions; the script enforces the validation gate and publishes the exact validated candidate ZIP to GitHub Releases
5. **Communicate changes**: update `CHANGELOG.md` with adopter-facing changes, compatibility implications, and any required migration action; the GitHub Release notes are auto-populated by `publish-release.py`; record this step in the Release History table below

## Canonical Sources

- `docs/compatibility-matrix.md` is the canonical source of truth for supported Godot, .NET, and SpacetimeDB version combinations and support status definitions. All adopter-facing documentation that mentions version requirements references this file.
- GitHub Releases is the canonical distribution channel. The published addon ZIP is the exact validated candidate payload — adopters must install from a published GitHub Release, not from a cloned repo snapshot.
- `CHANGELOG.md` at the repo root records adopter-facing changes for each release. Each entry must explain adopter impact, compatibility implications, and any required migration action.

## Release History

| Version | Release Date | Communication Step |
|---|---|---|
| 0.1.0-dev | 2026-04-15 | CHANGELOG.md (§ Added, § Compatibility, § Migration) + GitHub Release notes via publish-release.py |

## Notes

- Add a row to the Release History table for every published release so future maintainers can confirm which communication steps were used and replicate the same pattern.
- If the compatibility matrix changes between releases, update both `docs/compatibility-matrix.md` and the `### Compatibility` section of the corresponding CHANGELOG entry.
