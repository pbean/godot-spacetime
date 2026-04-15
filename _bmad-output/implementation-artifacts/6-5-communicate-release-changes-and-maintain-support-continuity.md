# Story 6.5: Communicate Release Changes and Maintain Support Continuity

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As the SDK maintainer,
I want release communication and support continuity rules that protect adopters across updates,
so that changes remain understandable and the release workflow stays repeatable as compatibility targets evolve.

## Acceptance Criteria

1. **Given** a change affects adopters, compatibility, or supported workflow behavior **When** the release is documented **Then** the release notes or change log explain the adopter impact, compatibility implications, and any required migration or upgrade action
2. **And** the support and update guidance references the canonical compatibility matrix and the published release artifact as the source of truth
3. **And** the release-process reference or checklist records the communication step used for that version so future releases can follow the same path

## Tasks / Subtasks

- [x] Task 1: Create `CHANGELOG.md` at repo root (AC: 1)
  - [x] 1.1 Initialize with [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) 1.1.0 format: title `# Changelog`, preamble paragraph explaining the format and linking to keepachangelog.com and semver.org
  - [x] 1.2 Add empty `## [Unreleased]` section as the top release section (placeholder for in-flight changes between releases)
  - [x] 1.3 Add `## [0.1.0-dev] - 2026-04-15` section with three subsections:
    - `### Added`: bullet list of initial SDK deliverables: .NET addon (`addons/godot_spacetime/`), typed binding code generation (`scripts/codegen/`), authentication session flows (login, session resume, failure recovery), subscription management and local cache API, reducer invocation with scene-safe event callbacks, sample project (`demo/`), core documentation suite (install, quickstart, connection, codegen, troubleshooting, migration, runtime-boundaries), compatibility matrix and support policy (`docs/compatibility-matrix.md`), release packaging/validation/publication pipeline (`scripts/packaging/`, `.github/workflows/`)
    - `### Compatibility`: a single paragraph stating "This release targets the version combination declared in [`docs/compatibility-matrix.md`](docs/compatibility-matrix.md). See that document for the canonical supported Godot and SpacetimeDB version pair, support status definitions, and compatibility triage timeline."
    - `### Migration`: a single paragraph stating "This is the initial release. There is no prior GodotSpacetime SDK version to migrate from. Adopters migrating from the community plugin should consult [`docs/migration-from-community-plugin.md`](docs/migration-from-community-plugin.md) for concept mapping and upgrade guidance."
  - [x] 1.4 Add footer comparison links at the bottom of the file:
    - `[Unreleased]: https://github.com/clockworklabs/godot-spacetime/compare/v0.1.0-dev...HEAD`
    - `[0.1.0-dev]: https://github.com/clockworklabs/godot-spacetime/releases/tag/v0.1.0-dev`

- [x] Task 2: Create `docs/release-process.md` (AC: 2, 3)
  - [x] 2.1 Header `# Release Process` with a one-paragraph maintainer-facing intro: "This document is the canonical release checklist for GodotSpacetime SDK maintainers. Follow the steps in order for each release. Record the communication step used for each version in the Release History table so future releases can follow the same path."
  - [x] 2.2 Section `## Release Checklist`: numbered steps covering the full release pipeline (each step references its script or workflow):
    1. **Update compatibility targets**: edit `docs/compatibility-matrix.md` and `scripts/compatibility/support-baseline.json` for the new version pair; update version references in `docs/install.md` if the supported baseline has changed
    2. **Package release candidate**: `python3 scripts/packaging/package-release.py [--version X.Y.Z]` — produces `release-candidates/godot-spacetime-vX.Y.Z.zip`
    3. **Validate release candidate**: `python3 scripts/packaging/validate-release-candidate.py [--version X.Y.Z]` (local) or trigger `.github/workflows/release-validation.yml` via GitHub Actions (CI) — produces `release-candidates/validation-report-vX.Y.Z.json`; the report must show `"status": "pass"` before proceeding
    4. **Publish release**: `python3 scripts/packaging/publish-release.py [--version X.Y.Z]` (local, requires `gh` CLI and `GH_TOKEN`) or trigger `.github/workflows/release.yml` via GitHub Actions; the script enforces the validation gate and publishes the exact validated candidate ZIP to GitHub Releases
    5. **Communicate changes**: update `CHANGELOG.md` with adopter-facing changes, compatibility implications, and any required migration action; the GitHub Release notes are auto-populated by `publish-release.py`; record this step in the Release History table below
  - [x] 2.3 Section `## Canonical Sources`:
    - "`docs/compatibility-matrix.md` is the canonical source of truth for supported Godot, .NET, and SpacetimeDB version combinations and support status definitions. All adopter-facing documentation that mentions version requirements references this file."
    - "GitHub Releases is the canonical distribution channel. The published addon ZIP is the exact validated candidate payload — adopters must install from a published GitHub Release, not from a cloned repo snapshot."
    - "`CHANGELOG.md` at the repo root records adopter-facing changes for each release. Each entry must explain adopter impact, compatibility implications, and any required migration action."
  - [x] 2.4 Section `## Release History`: a markdown table with columns `Version | Release Date | Communication Step` and an initial row for `0.1.0-dev | 2026-04-15 | CHANGELOG.md (§ Added, § Compatibility, § Migration) + GitHub Release notes via publish-release.py`
  - [x] 2.5 Section `## Notes`:
    - "Add a row to the Release History table for every published release so future maintainers can confirm which communication steps were used and replicate the same pattern."
    - "If the compatibility matrix changes between releases, update both `docs/compatibility-matrix.md` and the `### Compatibility` section of the corresponding CHANGELOG entry."

- [x] Task 3: Update `docs/install.md` to reference the canonical compatibility matrix (AC: 2)
  - [x] 3.1 At the end of the `## Supported Foundation Baseline` section, add this sentence on its own line after the bullet list: `For the authoritative version support declarations, support status definitions, and compatibility triage timeline, see [docs/compatibility-matrix.md](compatibility-matrix.md).`
  - [x] 3.2 Add `docs/compatibility-matrix.md` to the `## See Also` section at the bottom of the file: `- \`docs/compatibility-matrix.md\` for the canonical supported version matrix, support policy, and compatibility triage timeline.`
  - [x] 3.3 Do NOT modify any other section of `docs/install.md`. No version numbers, bootstrap steps, notes, or repository expectations should change.

- [x] Task 4: Create `tests/test_story_6_5_communicate_release_changes_and_maintain_support_continuity.py` (AC: 1, 2, 3)
  - [x] 4.1 Static existence tests: `CHANGELOG.md` at repo root exists; `docs/release-process.md` exists
  - [x] 4.2 CHANGELOG content tests (read the file once and run assertions against the text):
    - `"[0.1.0-dev]"` in changelog text
    - `"[Unreleased]"` in changelog text
    - `"compatibility-matrix"` in changelog text (lower-case match; confirms § Compatibility references the matrix)
    - `"migration"` in changelog text (case-insensitive; confirms § Migration exists)
    - `"keepachangelog"` in changelog text (confirms Keep a Changelog format header)
  - [x] 4.3 Release-process content tests (read the file once and run assertions against the text):
    - `"compatibility-matrix"` in release-process text (§ Canonical Sources)
    - `"CHANGELOG"` in release-process text (step 5 communication step)
    - `"0.1.0-dev"` in release-process text (Release History row)
    - `"package-release"` in release-process text (step 2 reference)
    - `"validate-release-candidate"` in release-process text (step 3 reference)
    - `"publish-release"` in release-process text (step 4 reference)
    - `"GitHub Releases"` in release-process text (§ Canonical Sources distribution channel)
  - [x] 4.4 `docs/install.md` reference test: `"compatibility-matrix"` in `docs/install.md` text (AC 2 — support guidance references canonical matrix)
  - [x] 4.5 Regression guards (assert all previously created files from stories 6.1–6.4 still exist):
    - `docs/compatibility-matrix.md`
    - `scripts/packaging/package-release.py`
    - `scripts/packaging/validate-release-candidate.py`
    - `scripts/packaging/publish-release.py`
    - `.github/workflows/release-validation.yml`
    - `.github/workflows/release.yml`
    - `scripts/compatibility/support-baseline.json`
    - `scripts/compatibility/validate-foundation.py`
    - `docs/install.md`
    - `docs/migration-from-community-plugin.md`

## Dev Notes

### What This Story Delivers

Story 6.5 closes Epic 6 by adding the communication layer that makes the release workflow repeatable and comprehensible to adopters. The previous stories (6.1–6.4) built the technical release pipeline; this story adds the human-readable artifacts that explain what changed, what is supported, and how to upgrade.

**Primary deliverables:**
- `CHANGELOG.md` (repo root) — adopter-facing record of changes per release in Keep a Changelog format; every entry must declare adopter impact, compatibility implications, and migration action
- `docs/release-process.md` — maintainer-facing release checklist that documents all five pipeline steps and records the communication step used per version in a Release History table

**Secondary deliverable:**
- Update `docs/install.md` — add two references to `docs/compatibility-matrix.md` so the install doc points to the canonical source of truth (the compatibility-matrix.md intro already claims install.md references it; this story closes that gap)

**Test deliverable:**
- `tests/test_story_6_5_communicate_release_changes_and_maintain_support_continuity.py` — static existence and content verification covering all four deliverables, plus regression guards for the full Epic 6 artifact set

**No C# changes.** No modifications to `addons/`, `spacetime/`, `demo/`, `scripts/compatibility/`, `scripts/codegen/`, `scripts/packaging/`, or any `.github/workflows/` file.

### Critical Architecture Constraints

**`docs/compatibility-matrix.md` is the canonical source of truth.** Story 6.1 established this. The CHANGELOG `### Compatibility` section and `docs/release-process.md` § Canonical Sources must reference it, not duplicate its content. Do NOT restate specific version numbers in CHANGELOG or release-process.md — point to the matrix instead.

**`CHANGELOG.md` belongs at the repo root**, not under `docs/`. This is the standard location expected by GitHub, package registries, and community tooling.

**`docs/release-process.md` is an expected architecture artifact.** The architecture document lists it in the `docs/` structure alongside `docs/compatibility-matrix.md`. It was not created in earlier stories because it requires the full pipeline (6.1–6.4) to exist first.

**Do NOT add `CHANGELOG.md` or `docs/release-process.md` to `scripts/compatibility/support-baseline.json`.** The support baseline tracks addon and tooling structure, not documentation files.

**`docs/install.md` update is additive only.** Append to the "Supported Foundation Baseline" section and the "See Also" section. Do not change any existing sentences, version numbers, or steps. The only change is adding the two compatibility-matrix references described in Task 3.

### Keep a Changelog Format Reference

Keep a Changelog 1.1.0 uses this structure. Follow it exactly for `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0-dev] - 2026-04-15

### Added

- ...

### Compatibility

...

### Migration

...

[Unreleased]: https://github.com/clockworklabs/godot-spacetime/compare/v0.1.0-dev...HEAD
[0.1.0-dev]: https://github.com/clockworklabs/godot-spacetime/releases/tag/v0.1.0-dev
```

`### Compatibility` and `### Migration` are non-standard subsections added to the standard Keep a Changelog change-type sections (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`). They are acceptable as additional subsections for SDK releases that need to communicate version support and upgrade paths.

### How Tests Work for Documentation Stories

Story 6.5 tests are entirely static file assertions — no subprocess invocations, no `setup_module`/`teardown_module` needed. The test pattern is:

```python
ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_PROCESS = ROOT / "docs" / "release-process.md"

def test_changelog_exists():
    assert CHANGELOG.exists()

def test_changelog_has_initial_version():
    assert "[0.1.0-dev]" in CHANGELOG.read_text(encoding="utf-8")
```

Read each file once with `.read_text(encoding="utf-8")` and store in a local variable, then run all content assertions against that variable to avoid redundant file I/O.

### Previous Story Intelligence (Stories 6.1–6.4)

- **Story 6.1** created `docs/compatibility-matrix.md` as the canonical version source. Its intro paragraph already claims: "The following documentation references this file as the authoritative version baseline: `docs/install.md`, `docs/quickstart.md`, `docs/troubleshooting.md`, and `docs/migration-from-community-plugin.md`." — Story 6.5 must close this gap for `docs/install.md` by actually adding the reference (Task 3). Do NOT modify `docs/compatibility-matrix.md`.
- **Story 6.2** established `scripts/packaging/package-release.py`. The release process checklist step 2 must reference it by exact script name.
- **Story 6.3** established `scripts/packaging/validate-release-candidate.py` and `.github/workflows/release-validation.yml`. The checklist step 3 references both paths.
- **Story 6.4** established `scripts/packaging/publish-release.py` and `.github/workflows/release.yml`. The checklist step 4 references both. The publish script also auto-generates GitHub Release notes from the tag — mention this in checklist step 5 so maintainers know they don't need to manually write the GitHub Release body.
- **Regression guard pattern**: Every story in Epic 6 includes regression guards asserting prior story deliverables still exist. Story 6.5 should guard all of 6.1–6.4's key files.

### Git History Patterns

The five Epic 6 commits share the commit message pattern `feat(story-6.X): <Story Title>`. The story 6.5 commit should follow: `feat(story-6.5): Communicate Release Changes and Maintain Support Continuity`.

### Project Structure Notes

- `CHANGELOG.md` → repo root; no subdirectory; standard location
- `docs/release-process.md` → `docs/` alongside `docs/compatibility-matrix.md`; architecture-specified target
- `tests/test_story_6_5_*.py` → `tests/` alongside existing story test files; follows naming convention `test_story_{epic}_{story}_{slug}.py`
- No changes to `addons/`, `spacetime/`, `demo/`, `scripts/`, or `.github/`

### References

- Epic 6 story 6.5 statement and ACs: `_bmad-output/planning-artifacts/epics.md` (Epic 6 § Story 6.5)
- FR37 ("Maintainers can document changes that affect adopters, including compatibility-impacting changes"): `_bmad-output/planning-artifacts/prd.md` (Release, Compatibility & Maintainer Operations)
- FR38 ("Maintainers can support a repeatable release/update workflow as Godot and SpacetimeDB evolve"): `_bmad-output/planning-artifacts/prd.md` (Release, Compatibility & Maintainer Operations)
- Architecture `docs/` structure listing `docs/release-process.md`: `_bmad-output/planning-artifacts/architecture.md` (Documentation Structure section)
- Architecture canonical distribution model: `_bmad-output/planning-artifacts/architecture.md` ("GitHub Releases first, with distributable ZIPs centered on the `addons/` plugin structure")
- Story 6.4 publication gate and exact script paths: `_bmad-output/implementation-artifacts/6-4-publish-approved-sdk-releases-for-external-use.md` (Dev Notes)
- Keep a Changelog format: https://keepachangelog.com/en/1.1.0/

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Created `CHANGELOG.md` at repo root in Keep a Changelog 1.1.0 format with `[Unreleased]` placeholder and `[0.1.0-dev] - 2026-04-15` section (§ Added, § Compatibility, § Migration) plus footer comparison links.
- Created `docs/release-process.md` with five-step release checklist referencing all pipeline scripts/workflows, § Canonical Sources declaring `docs/compatibility-matrix.md` and GitHub Releases as canonical sources, Release History table with initial 0.1.0-dev row, and § Notes for future maintainers.
- Updated `docs/install.md` additively: appended compatibility-matrix.md reference sentence to § Supported Foundation Baseline and added it to § See Also. No existing content modified.
- Created `tests/test_story_6_5_communicate_release_changes_and_maintain_support_continuity.py` with static existence/content verification for the new release artifacts plus regression guards for all Epic 6.1–6.4 deliverables.
- Senior Developer Review (AI) corrected the release-process communication-step guidance to match `publish-release.py`, hardened Story 6.5 coverage to 44 tests, reran validation (`44` story tests, `2192` full-suite tests), and synced story/sprint tracking to `done`.

### File List

- `CHANGELOG.md` (new)
- `docs/release-process.md` (new, review-hardened: corrected release-notes guidance to match `publish-release.py`)
- `docs/install.md` (updated)
- `tests/test_story_6_5_communicate_release_changes_and_maintain_support_continuity.py` (new, review-hardened to 44 tests)
- `_bmad-output/implementation-artifacts/6-5-communicate-release-changes-and-maintain-support-continuity.md` (story file updates: review notes, metadata, status)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status update: `6-5-communicate-release-changes-and-maintain-support-continuity` -> `done`)

## Senior Developer Review (AI)

- Reviewer: Pinkyd on 2026-04-15
- Outcome: Approve
- Story Context: No separate story-context artifact was found; review used the story file, `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/prd.md`, `docs/compatibility-matrix.md`, `scripts/packaging/publish-release.py`, and the changed implementation/test files.
- Epic Tech Spec: No separate epic tech spec artifact was found; `_bmad-output/planning-artifacts/architecture.md` provided the standards and architecture context.
- Tech Stack Reviewed: Markdown documentation, Python release tooling, and `pytest` contract tests.
- External References: No MCP/web lookup used; repository primary sources were sufficient for this review scope and network access is restricted in this environment.
- Git vs Story Discrepancies: 2 additional non-source automation artifacts were present under `_bmad-output/` during review (`_bmad-output/implementation-artifacts/tests/test-summary-6-5.md`, `_bmad-output/story-automator/orchestration-1-20260414-184146.md`).
- Findings fixed:
  - MEDIUM: `docs/release-process.md` claimed `publish-release.py` auto-populates GitHub Release notes "from the repository history" and attached that guidance to step 4 instead of the communication step. Fixed by removing the unsupported source-history claim and moving the auto-populated-notes guidance into step 5, matching the story requirement and actual script behavior.
  - MEDIUM: `tests/test_story_6_5_communicate_release_changes_and_maintain_support_continuity.py` reread the same documentation files on every assertion and only weakly checked the changelog footer links and release-process contract, so regressions against the exact story wording could slip through. Fixed by caching each file once, asserting the exact changelog footer URLs and release-history row, and covering the corrected release-notes guidance.
  - MEDIUM: The story artifact still reported pre-review `25` story tests / `2173` full-suite totals, had no `Senior Developer Review (AI)` section, and sprint tracking still showed `review`. Fixed by rerunning validation, updating the story record to `44` story tests and `2192` full-suite tests, and syncing story/sprint status to `done`.
- Validation:
  - `pytest -q tests/test_story_6_5_communicate_release_changes_and_maintain_support_continuity.py`
  - `pytest -q`
- Notes:
  - No CRITICAL issues remain after fixes.

## Change Log

- 2026-04-15: Implemented Story 6.5 — created CHANGELOG.md, docs/release-process.md, updated docs/install.md with compatibility-matrix references, and added the story verification suite.
- 2026-04-15: Senior Developer Review (AI) — corrected release-process communication guidance, hardened Story 6.5 coverage to 44 tests, reran validation (`44` story tests, `2192` full-suite tests), and marked the story done.
