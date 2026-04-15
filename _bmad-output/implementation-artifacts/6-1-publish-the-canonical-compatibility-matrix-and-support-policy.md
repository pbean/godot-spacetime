# Story 6.1: Publish the Canonical Compatibility Matrix and Support Policy

Status: done

## Story

As an external adopter,
I want each SDK release to state its exact supported environment,
so that I know whether a given Godot and SpacetimeDB pairing is intended to work before I integrate it.

## Acceptance Criteria

1. **Given** a published or candidate SDK release **When** I inspect its compatibility documentation **Then** I can identify the exact supported Godot and SpacetimeDB versions targeted by that release
2. **And** the support policy distinguishes supported, experimental, deferred, or out-of-scope targets where relevant
3. **And** the compatibility matrix and support policy are the canonical source referenced by install docs, troubleshooting docs, release notes, and sample references

## Tasks / Subtasks

- [x] Task 1: Rewrite `docs/compatibility-matrix.md` as the canonical adopter-facing compatibility and support policy document (AC: 1, 2, 3)
  - [x] 1.1 Replace the opening paragraph — remove internal-story language ("for the repository foundation created in Story `1.1`"); replace with adopter-facing scope statement naming all docs that reference this as canonical: `docs/install.md`, `docs/quickstart.md`, `docs/troubleshooting.md`, and `docs/migration-from-community-plugin.md` (see exact wording in Dev Notes)
  - [x] 1.2 Rename the version table to `## Supported Version Baseline`; add a `Status` column with `Supported` for all current version rows
  - [x] 1.3 Add an Out-of-Scope row to the version table: Godot C# web export | N/A | Out-of-Scope (v1 constraint from architecture)
  - [x] 1.4 Add `## Support Policy` section (place before `## Binding Compatibility Check`) defining what each status value means — see Dev Notes for exact wording
  - [x] 1.5 Add `## Compatibility Triage Timeline` section (after `## Support Policy`) with the 14-day upstream triage SLA — see Dev Notes for exact wording
  - [x] 1.6 Add `## Version Change Guidance` section (after `## Compatibility Triage Timeline`) explaining what adopters should do when their version is not on the supported list — see Dev Notes for exact wording
  - [x] 1.7 Rewrite `## Scope of This Matrix` — remove "Story `1.1`" reference; replace with a one-sentence adopter-facing scope statement (see Dev Notes)
  - [x] 1.8 Keep `## Binding Compatibility Check` section content exactly unchanged — the technical instructions and code block are still accurate; do NOT modify any content in this section

- [x] Task 2 (C3, Epic 5 Retro): Clarify `ITokenStore` externalization boundary in `docs/runtime-boundaries.md` — one sentence addition only (closes prep item C3)
  - [x] 2.1 In the `### Auth / Identity — \`ITokenStore\`` section of `docs/runtime-boundaries.md`, locate the **Built-in implementations** block that ends with the `ProjectSettingsTokenStore` bullet
  - [x] 2.2 After the `ProjectSettingsTokenStore` bullet, add the following as a new standalone paragraph: "`ProjectSettingsTokenStore` is `internal sealed` — external developers must implement `GodotSpacetime.Auth.ITokenStore` directly; it cannot be instantiated from outside the SDK."
  - [x] 2.3 Do NOT modify any other content in `docs/runtime-boundaries.md` — this is a single sentence addition only

- [x] Task 3 (D1/C1, Epic 5 Retro): Resolve `ConnectionAuthState.AuthRequired` dead code (closes critical path item C1)
  - [x] 3.1 Search for ALL current references to `AuthRequired` across the repo before making any changes: `grep -r "AuthRequired" addons/ docs/ tests/` — record what you find
  - [x] 3.2 Remove `AuthRequired` from `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs` enum — this state was never set by the connection state machine and misleads external developers about the auth failure taxonomy; if you find it IS set in the state machine, do NOT remove it and record a blocker note in the Dev Agent Record instead
  - [x] 3.3 Remove the `| \`AuthRequired\` |` row from the `ConnectionAuthState` table in `docs/runtime-boundaries.md` (the row that reads "Credentials are expected but not provided (panel guidance)")
  - [x] 3.4 Update any remaining `AuthRequired` references in `addons/` source files: replace with `AuthFailed` or `TokenExpired` as the context requires, or remove if the reference is purely illustrative
  - [x] 3.5 Update any `AuthRequired` references in test files: if any assertion checks for the presence of `AuthRequired`, remove or update it
  - [x] 3.6 Run `dotnet build` and confirm a clean build before considering Task 3 complete

- [x] Task 4: Write `tests/test_story_6_1_publish_the_canonical_compatibility_matrix_and_support_policy.py` (AC: 1, 2, 3)
  - [x] 4.1 Existence test: `docs/compatibility-matrix.md` exists
  - [x] 4.2 Section presence tests: `## Support Policy`, `## Compatibility Triage Timeline`, `## Version Change Guidance`, `## Supported Version Baseline`, `## Binding Compatibility Check` all present in compatibility-matrix.md
  - [x] 4.3 Support policy content tests (AC: 2): Support Policy section contains `Supported`, `Experimental`, `Deferred`, `Out-of-Scope`
  - [x] 4.4 Out-of-scope documentation test (AC: 2): compatibility matrix contains `web export` as an explicit out-of-scope entry
  - [x] 4.5 Version baseline content tests (AC: 1): `## Supported Version Baseline` section contains `4.6.2`, `2.1+`, `SpacetimeDB.ClientSDK`, `Godot.NET.Sdk`
  - [x] 4.6 Triage timeline test (AC: 1): `## Compatibility Triage Timeline` section contains `14 days`
  - [x] 4.7 Adopter-facing test (AC: 3): opening of `docs/compatibility-matrix.md` does NOT contain the string `Story \`1.1\`` (internal-story reference removed)
  - [x] 4.8 Canonical reference test (AC: 3): `docs/compatibility-matrix.md` contains `docs/install.md`, `docs/quickstart.md`, `docs/troubleshooting.md`, and `docs/migration-from-community-plugin.md` in the opening canonical reference statement
  - [x] 4.9 ITokenStore externalization test (C3): `docs/runtime-boundaries.md` contains `internal sealed` in the auth section
  - [x] 4.10 AuthRequired enum removal test (D1): `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs` content does NOT contain the string `AuthRequired`
  - [x] 4.11 Docs AuthRequired removal test (D1): `docs/runtime-boundaries.md` does NOT contain the table row string `| \`AuthRequired\` |`
  - [x] 4.12 Regression guards — all prior story deliverables must remain intact:
    - `docs/install.md` exists
    - `docs/quickstart.md` exists
    - `docs/codegen.md` exists
    - `docs/connection.md` exists
    - `docs/runtime-boundaries.md` exists
    - `docs/compatibility-matrix.md` exists
    - `docs/troubleshooting.md` exists
    - `docs/migration-from-community-plugin.md` exists
    - `demo/README.md` exists
    - `demo/DemoMain.cs` exists
    - `addons/godot_spacetime/src/Public/SpacetimeClient.cs` exists
    - `docs/compatibility-matrix.md` contains `4.6.2` (version baseline intact)
    - `docs/compatibility-matrix.md` contains `SpacetimeDB.ClientSDK` (SDK dependency intact)
    - `docs/runtime-boundaries.md` contains `ConnectionState` (connection lifecycle terminology intact)
    - `docs/runtime-boundaries.md` contains `ITokenStore` (auth interface intact)
    - `docs/runtime-boundaries.md` contains `ReducerCallFailed` (reducer error model intact)
    - `docs/troubleshooting.md` contains `TokenExpired` (Story 5.5 intact)
    - `docs/migration-from-community-plugin.md` contains `DbConnection.Builder()` (Story 5.6 intact)
    - `demo/README.md` contains `Reducer Interaction` (Story 5.3 intact)
    - `demo/DemoMain.cs` contains `ReducerCallSucceeded` (Story 5.3 wiring intact)

## Dev Notes

### What This Story Delivers

Story 6.1 opens Epic 6 by converting `docs/compatibility-matrix.md` from an internal development artifact (created in Story 1.1 to track the scaffold baseline) into a published, adopter-facing compatibility and support policy document ready to accompany the SDK release.

It also resolves two carry-forward items from the Epic 5 retrospective that were flagged as critical path preparation tasks for Epic 6 (per P3 action item — anchor all debt items as explicit story subtasks):

- **C1/D1**: Remove `ConnectionAuthState.AuthRequired` dead code — this state was never set by the connection state machine and would confuse external developers examining the auth failure taxonomy on first read
- **C3**: Add one sentence to `docs/runtime-boundaries.md` clarifying that `ProjectSettingsTokenStore` is `internal sealed`, so external developers know they must implement `ITokenStore` directly

**Primary deliverable:** Updated `docs/compatibility-matrix.md` (Task 1)
**Secondary deliverables:** One sentence in `docs/runtime-boundaries.md` (Task 2), removal of dead enum value and doc cleanup (Task 3)
**Validation:** New test file with regression guards (Task 4)

This story is predominantly documentation with one scoped C# code change (removing the `AuthRequired` enum value). The code change is limited to `ConnectionAuthState.cs` and its downstream references only.

### Critical Architecture Constraints

**`docs/compatibility-matrix.md` is the single canonical version source — do not duplicate version facts into other docs.**
All install, quickstart, troubleshooting, and migration docs already reference it. The Task 1 rewrite must not change the technical facts in the version table — only the framing, structure, and completeness.

**Do NOT create `docs/release-process.md`.**
That document is Epic 6 Story 6.4/6.5 scope. This story only modifies `docs/compatibility-matrix.md` and `docs/runtime-boundaries.md`.

**`AuthRequired` removal is the ONLY C# code change in this story.**
Do not modify any other enum value, public method signature, or public property in the addon. If removing `AuthRequired` from `ConnectionAuthState.cs` causes any compile error because some code path actually sets this state, that means the Epic 5 retro assessment was wrong — do NOT proceed with removal; record a blocker note in the Dev Agent Record.

**Do NOT modify any existing test files except to remove `AuthRequired` references if they exist there.**
All prior test files are regression-guarded and must pass unchanged or with only `AuthRequired` reference removals.

**Use exact public API names everywhere.**
All type names, signal names, and method names in the updated docs must match exactly as defined in `addons/godot_spacetime/src/Public/SpacetimeClient.cs` and `docs/runtime-boundaries.md`. Do not invent new names or paraphrase existing ones.

### Exact Content for `docs/compatibility-matrix.md` (Task 1)

**Complete rewritten file:**

```markdown
# Compatibility Matrix and Support Policy

This document is the canonical source of truth for GodotSpacetime SDK version support. It declares which Godot, .NET, and SpacetimeDB version combinations are currently targeted by this release, and what level of support each combination carries.

The following documentation references this file as the authoritative version baseline: `docs/install.md`, `docs/quickstart.md`, `docs/troubleshooting.md`, and `docs/migration-from-community-plugin.md`.

## Supported Version Baseline

| Surface | Version | Status |
|---------|---------|--------|
| Godot editor/runtime target | `4.6.2` | Supported |
| Godot .NET build SDK | `Godot.NET.Sdk` `4.6.1` | Supported |
| `.NET` SDK | `8.0+` | Supported |
| SpacetimeDB server and CLI | `2.1+` | Supported |
| `SpacetimeDB.ClientSDK` | `2.1.0` | Supported |
| Godot C# web export | N/A | Out-of-Scope |

The machine-checkable source of truth for this baseline lives in `scripts/compatibility/support-baseline.json`, and `.github/workflows/validate-foundation.yml` enforces it through `python3 scripts/compatibility/validate-foundation.py`.

## Support Policy

| Status | Meaning |
|--------|---------|
| **Supported** | This version combination is the declared target for the current release. It is validated in CI, covered in all documentation, and eligible for bug reports. |
| **Experimental** | This version combination has been tested informally but is not covered by CI or formal compatibility checks. It may work, but bugs may not be prioritized. |
| **Deferred** | This version combination is on the roadmap but not yet validated or targeted. It will appear as `Supported` in a future release when formally validated. |
| **Out-of-Scope** | This version combination is explicitly not supported and will not be investigated. Known out-of-scope targets include Godot C# web export and GDScript-only runtime delivery for v1. |

Only `Supported` entries are declared in the current release. `Experimental` and `Deferred` entries will be added in future releases as the compatibility matrix expands.

## Compatibility Triage Timeline

When upstream SpacetimeDB or Godot releases a new version, the following triage process applies:

1. Compatibility issues caused by upstream minor releases are assessed within **14 days** of the upstream release.
2. If the new version is compatible without SDK changes, a compatibility note is added to this file.
3. If SDK changes are required, an issue is filed and the affected version combination moves to `Experimental` until the SDK update ships.
4. Major upstream version changes are treated as new version targets and may require a new SDK release cycle.

## Version Change Guidance

If your Godot or SpacetimeDB version is not listed as `Supported`:

1. Run `python3 scripts/compatibility/validate-foundation.py` to identify which specific checks fail.
2. Check the `"Spacetime Compat"` panel in the Godot editor for binding version mismatch details.
3. Consult `docs/troubleshooting.md` for common environment mismatch failures and resolution steps.
4. File an issue with the version details if you believe your environment should be supported.

Version combinations that are not listed as `Supported` are not eligible for bug reports until they appear on the supported matrix.

## Binding Compatibility Check

The Compatibility panel in the Godot editor reads the CLI version comment embedded in generated bindings and compares it against the declared `spacetimedb` baseline. Generated files contain that comment near the top of the file, after the generated-file warning banner, in the form:

    // This was generated using spacetimedb cli version X.Y.Z (commit ...)

The panel extracts the version token and checks that it satisfies the declared baseline (e.g. `2.1+` requires CLI `>= 2.1`). The validation workflow also compares the latest relevant module-source file under `spacetime/modules/smoke_test/` against `demo/generated/smoke_test/SpacetimeDBClient.g.cs` so stale bindings fail before runtime use. If either check fails, the tooling reports the exact failed check together with the regeneration command.

To resolve an INCOMPATIBLE state, run:

    bash scripts/codegen/generate-smoke-test.sh

Story `1.8` implements this check. Stories `1.9` and `1.10` extend the quickstart to validate both binding compatibility and connection state before declaring the setup complete.

## Scope of This Matrix

This matrix declares the version baseline for the GodotSpacetime SDK release it accompanies. It does not cover runtime flow validation — that is the responsibility of the release validation workflow. Later releases will expand the matrix as new Godot or SpacetimeDB versions are validated.
```

### Exact Content Addition for `docs/runtime-boundaries.md` (Task 2)

Locate the `### Auth / Identity — \`ITokenStore\`` section. Find the `**Built-in implementations**` block that lists two bullets ending with:

```
- `ProjectSettingsTokenStore` — persists the token to Godot `ProjectSettings` under the key `spacetime/auth/token`. Suitable for development environments; review your distribution's security model before enabling in production.
```

After this bullet (and the close of the implementations block), add the following as a new standalone paragraph:

```
`ProjectSettingsTokenStore` is `internal sealed` — external developers must implement `GodotSpacetime.Auth.ITokenStore` directly; it cannot be instantiated from outside the SDK.
```

Do NOT change any other text, heading, or table in `docs/runtime-boundaries.md`.

### AuthRequired Removal Detail (Task 3)

`ConnectionAuthState.AuthRequired` was defined in `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs`. Per Epic 5 Retrospective item D1/C1: this state is never set by the connection state machine. It was originally intended as an editor-panel guidance state but ended up as dead code in the runtime auth taxonomy.

The actual auth failure states used by the connection state machine are `AuthFailed` (credentials rejected) and `TokenExpired` (previously stored token rejected). `None` and `TokenRestored` are the normal states. `AuthRequired` fits none of these runtime transitions.

**Why this matters for a public release:** External developers reading `ConnectionAuthState` will see `AuthRequired` and attempt to handle it in their game code, potentially registering signal handlers or state checks for a condition that never fires. This is a silent developer experience failure that is cheap to fix now and expensive to explain in every release of documentation.

**Exact grep command to run first:**
```bash
grep -r "AuthRequired" addons/ docs/ tests/ --include="*.cs" --include="*.md" --include="*.py"
```

**Expected findings:**
- `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs` — the enum value (remove it)
- `docs/runtime-boundaries.md` — table row (remove it)
- Possibly editor panel code in `addons/godot_spacetime/src/Editor/` (replace with `None` or `AuthFailed` as appropriate)
- Possibly Story 2.x test files (remove assertion or replace check)

**If `AuthRequired` is found in the connection state machine** (`SpacetimeConnectionService.cs`, `ConnectionStateMachine.cs`, or any `Internal/Connection/` file that sets `ConnectionAuthState.AuthRequired` as an output value), do NOT proceed with removal — record the finding as a blocker in the Dev Agent Record and leave Task 3 incomplete with a note explaining the discrepancy.

### Project Structure Notes

**Files to modify:**
- `docs/compatibility-matrix.md` — full rewrite per exact content in Dev Notes (Task 1)
- `docs/runtime-boundaries.md` — one sentence addition in ITokenStore built-in implementations block (Task 2); `AuthRequired` table row removed (Task 3)
- `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs` — remove `AuthRequired` enum value (Task 3)
- Any test file or addon source file where `AuthRequired` is referenced (Task 3, find via grep)

**Files to create:**
- `tests/test_story_6_1_publish_the_canonical_compatibility_matrix_and_support_policy.py` (Task 4)

**Files NOT to touch (modification will break prior story regression tests):**
- `docs/install.md` — complete; verified by Story 5.4 tests
- `docs/quickstart.md` — complete; verified by Story 5.4 tests
- `docs/codegen.md` — complete; verified by Story 1.6/1.7 tests
- `docs/connection.md` — complete; verified by Story 5.4 tests
- `docs/troubleshooting.md` — complete; verified by Story 5.5 tests
- `docs/migration-from-community-plugin.md` — complete; verified by Story 5.6 tests
- `demo/README.md` — complete; verified by Story 5.3/5.4 tests
- `demo/DemoMain.cs` — complete; verified by Story 5.3 tests
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` — SDK public API; out of scope
- All other `addons/godot_spacetime/src/` files not named `ConnectionAuthState.cs`
- `spacetime/modules/smoke_test/` — Rust source; out of scope

**Docs directory after Story 6.1:**
```
docs/
├── install.md                          ← unchanged
├── quickstart.md                       ← unchanged
├── codegen.md                          ← unchanged
├── connection.md                       ← unchanged
├── runtime-boundaries.md               ← modified (1 sentence added Task 2; AuthRequired row removed Task 3)
├── compatibility-matrix.md             ← rewritten (Task 1)
├── troubleshooting.md                  ← unchanged
└── migration-from-community-plugin.md  ← unchanged
```

### Test File Conventions

Same static-file-analysis pattern as Stories 5.x:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")
```

Reuse the `_section()` helper established in Story 5.4 (for `##` level headings):
```python
def _section(content: str, heading: str) -> str:
    marker = f"## {heading}\n\n"
    start = content.find(marker)
    assert start != -1, f"Expected to find section heading {marker.strip()!r}"
    start += len(marker)
    next_heading = content.find("\n## ", start)
    if next_heading == -1:
        return content[start:].strip()
    return content[start:next_heading].strip()
```

For the `AuthRequired` C# source removal test:
```python
def test_auth_required_removed_from_enum():
    content = _read("addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs")
    assert "AuthRequired" not in content, \
        "AuthRequired is dead code and must be removed from ConnectionAuthState enum (D1/C1 from Epic 5 retro)"
```

For the docs table row removal test (match the markdown table cell pattern):
```python
def test_runtime_boundaries_no_auth_required_table_row():
    content = _read("docs/runtime-boundaries.md")
    assert "| `AuthRequired` |" not in content, \
        "AuthRequired must be removed from the ConnectionAuthState table in runtime-boundaries.md (D1)"
```

Test function naming: `test_<file_slug>_<what_is_checked>`. All assertions include a descriptive failure message string.

### Git Intelligence (Recent Work Patterns)

- All Stories 5.x commits: `feat(story-5.x): Brief Title`; Story 6.1 should follow: `feat(story-6.1): Publish Canonical Compatibility Matrix and Support Policy`
- Recent work is purely documentation stories (5.1–5.6) — this story adds a scoped C# code change (enum removal); `dotnet build` validation is now required in addition to `pytest`
- Current full test suite baseline: **1,893 tests passing** (from Story 5.6 senior review; Story 5.6 delivered 85 tests bringing the total from 1808 to 1893)
- All test files live in `tests/` root directory as `test_story_*.py` — do NOT create in a subdirectory
- Test file for Story 6.1: `tests/test_story_6_1_publish_the_canonical_compatibility_matrix_and_support_policy.py`
- Story 5.5 had 83 tests; Story 5.6 had 85 tests — aim for comparable coverage given the breadth of this story's changes

### Validation Commands

```bash
# Verify C# builds cleanly after AuthRequired removal (Task 3)
dotnet build

# Run story-specific tests
pytest -q tests/test_story_6_1_publish_the_canonical_compatibility_matrix_and_support_policy.py

# Full regression suite
pytest -q
```

Expected: `dotnet build` clean; story test file passes; full suite passes with no regressions (1893+ tests).

### References

- Story user story and AC: `_bmad-output/planning-artifacts/epics.md`, Epic 6 § Story 6.1
- FR34: Adopters can identify the exact supported Godot and SpacetimeDB version matrix for each SDK release and understand its support policy [Source: `_bmad-output/planning-artifacts/prd.md` § Release & Distribution]
- NFR17: Each SDK release must explicitly state the supported Godot and SpacetimeDB versions it targets [Source: `_bmad-output/planning-artifacts/architecture.md`]
- NFR18: The project must maintain a compatibility matrix and update it as supported version pairings change [Source: `_bmad-output/planning-artifacts/architecture.md`]
- NFR19: The core supported workflow must be validated before release against the documented compatibility targets [Source: `_bmad-output/planning-artifacts/architecture.md`]
- `docs/compatibility-matrix.md` established Story 1.1 as foundation baseline; Story 1.8 added binding compatibility check section [Source: `_bmad-output/planning-artifacts/architecture.md` § Complete Project Directory Structure]
- `docs/release-process.md` is a future deliverable — do NOT create in this story (architecture references it but it is Epic 6.4/6.5 scope)
- Epic 5 Retrospective: D1 (AuthRequired dead code), C1 (critical pre-Epic-6 blocker), C3 (ITokenStore externalization sentence), P3 (anchor debt items in stories) [Source: `_bmad-output/implementation-artifacts/epic-5-retro-2026-04-15.md`]
- Previous story (5.6): `_bmad-output/implementation-artifacts/5-6-publish-upgrade-migration-and-concept-mapping-guides.md`
- `ConnectionAuthState.cs` location: `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs`
- `ProjectSettingsTokenStore` is `internal sealed` in `addons/godot_spacetime/src/Internal/Auth/ProjectSettingsTokenStore.cs` [Source: architecture directory structure]
- `docs/runtime-boundaries.md` ITokenStore section: "Built-in implementations" block with `MemoryTokenStore` and `ProjectSettingsTokenStore` bullets [Source: read in this session]
- `ConnectionAuthState` table in `docs/runtime-boundaries.md` currently includes: None, AuthRequired, TokenRestored, AuthFailed, TokenExpired [Source: read in this session]
- Triage SLA source: "Compatibility issues caused by upstream SpacetimeDB minor releases are assessed and triaged within 14 days of the upstream release." [Source: `_bmad-output/planning-artifacts/prd.md` § Measurable Outcomes]
- Current test suite baseline: 1,893 passing [Source: `_bmad-output/implementation-artifacts/5-6-publish-upgrade-migration-and-concept-mapping-guides.md` § Dev Agent Record]
- Architecture packaging boundary: only `addons/godot_spacetime/` ships; demo, tests, spacetime/ modules excluded [Source: `_bmad-output/planning-artifacts/architecture.md` § Packaging]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

**Task 3.1 AuthRequired grep findings (pre-removal):**
- `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs` — enum value (removed)
- `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs` — switch arm in `SetAuthStatus()` (removed; fallthrough `_ =>` arm covers the same visual state for anonymous connections)
- `docs/runtime-boundaries.md` — `ConnectionAuthState` table row (removed)
- `tests/test_story_2_4_failure_recovery.py` — `test_connection_auth_state_still_has_auth_required()` assertion (removed); enum order docstring updated to remove `AuthRequired` from order description
- `tests/test_story_2_2_auth_session.py` — `test_connection_auth_state_has_auth_required_value()` assertion (removed)
- `addons/godot_spacetime/src/Internal/` — **no references found** — confirmed `AuthRequired` was never set by the connection state machine; removal proceeded without blocker

**Post-review alignment:** Senior review restored the canonical Story 6.1 status row for `SpacetimeDB.ClientSDK` (`| Supported |`), updated `scripts/compatibility/support-baseline.json` to match the new table, updated the Story 1.4 regression to assert the canonical row instead of the legacy Notes text, and expanded Story 6.1 tests to verify the exact status-table rows and preserve the `## Binding Compatibility Check` section verbatim.

### Completion Notes List

- **Task 1:** `docs/compatibility-matrix.md` rewritten as adopter-facing document. New title, new opening paragraph with canonical reference statement, `## Supported Version Baseline` table with Status column and Out-of-Scope web export row, all current supported rows now using `Supported`, `## Support Policy` section with all four status definitions, `## Compatibility Triage Timeline` with 14-day SLA, `## Version Change Guidance` with triage steps, rewritten `## Scope of This Matrix`, and the `## Binding Compatibility Check` section restored verbatim.
- **Task 2:** `docs/runtime-boundaries.md` — one sentence added after `ProjectSettingsTokenStore` bullet clarifying `internal sealed` externalization boundary (closes Epic 5 Retro item C3).
- **Task 3:** `ConnectionAuthState.AuthRequired` removed from enum (`ConnectionAuthState.cs`), editor panel switch arm removed (`ConnectionAuthStatusPanel.cs`), doc table row removed (`runtime-boundaries.md`). Two test files updated to remove assertions guarding the now-removed value. `dotnet build` clean.
- **Task 4:** 60-test file written covering all ACs, C3, D1, exact compatibility-matrix status rows, support-baseline synchronization, Binding Compatibility Check preservation, and full regression guard suite. `python3 scripts/compatibility/validate-foundation.py`, targeted pytest, `dotnet build godot-spacetime.sln -c Debug`, and full `pytest -q` all pass (1951 tests).

### File List

- `docs/compatibility-matrix.md` — full rewrite (Task 1)
- `docs/runtime-boundaries.md` — one sentence added (Task 2); `AuthRequired` table row removed (Task 3)
- `addons/godot_spacetime/src/Public/Connection/ConnectionAuthState.cs` — `AuthRequired` enum value removed (Task 3)
- `addons/godot_spacetime/src/Editor/Status/ConnectionAuthStatusPanel.cs` — `AuthRequired` switch arm removed (Task 3)
- `tests/test_story_2_4_failure_recovery.py` — `AuthRequired` presence assertion removed; enum order docstring updated (Task 3)
- `tests/test_story_2_2_auth_session.py` — `AuthRequired` presence assertion removed (Task 3)
- `scripts/compatibility/support-baseline.json` — compatibility-matrix line checks updated to canonical Status rows; added out-of-scope web export row validation (review fix)
- `tests/test_story_1_4_adapter_boundary.py` — compatibility-matrix row expectation updated to canonical Story 6.1 Supported row (review fix)
- `tests/test_story_6_1_publish_the_canonical_compatibility_matrix_and_support_policy.py` — new test file, 60 tests including canonical row and verbatim-section guards (Task 4, review fix)

### Change Log

- feat(story-6.1): Rewrite compatibility-matrix.md as adopter-facing canonical document with support policy (2026-04-15)
- fix(story-6.1): Add ITokenStore `internal sealed` externalization sentence to runtime-boundaries.md (2026-04-15)
- fix(story-6.1): Remove ConnectionAuthState.AuthRequired dead code — enum, editor panel, and docs (2026-04-15)
- fix(review-6.1): Align compatibility-matrix status rows, support-baseline validation, and regression coverage with the canonical Story 6.1 support policy (2026-04-15)

## Senior Developer Review (AI)

### Reviewer

Pinkyd

### Outcome

Approve

### Findings

- [fixed][high] `docs/compatibility-matrix.md` left the `SpacetimeDB.ClientSDK` row in the legacy Story 1.4 notes format instead of the canonical Story 6.1 `Supported` status, so Task 1.2 / AC 1 was not fully implemented.
- [fixed][medium] `scripts/compatibility/support-baseline.json` still enforced pre-6.1 compatibility-matrix lines, which caused `python3 scripts/compatibility/validate-foundation.py` to fail against the rewritten document.
- [fixed][medium] `tests/test_story_1_4_adapter_boundary.py` still pinned the obsolete compatibility-matrix row text, which forced a workaround instead of allowing the canonical Story 6.1 row.
- [fixed][medium] `tests/test_story_6_1_publish_the_canonical_compatibility_matrix_and_support_policy.py` did not assert the exact status-table rows or the support-baseline synchronization, so the regression escaped the story test suite.
- [fixed][medium] `docs/compatibility-matrix.md` reformatted the `## Binding Compatibility Check` code blocks, violating Task 1.8's requirement to keep that section unchanged.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `pytest -q tests/test_story_1_4_adapter_boundary.py tests/test_story_1_8_compatibility.py tests/test_story_6_1_publish_the_canonical_compatibility_matrix_and_support_policy.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest -q`

### Notes

- No CRITICAL issues remain after fixes.
