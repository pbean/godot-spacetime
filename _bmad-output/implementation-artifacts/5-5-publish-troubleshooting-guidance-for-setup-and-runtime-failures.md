# Story 5.5: Publish Troubleshooting Guidance for Setup and Runtime Failures

Status: done

## Story

As an integrating developer,
I want troubleshooting guidance for common setup and runtime failures,
So that installation, auth, subscription, and schema-drift failures are diagnosable in one session.

## Acceptance Criteria

1. **Given** the current supported workflow docs and sample **When** I consult the troubleshooting guidance **Then** I can find documented failure modes for installation, code generation, local compatibility checks, connection, authentication, and subscriptions
2. **And** the guidance explains when regeneration, environment version changes, or configuration fixes are required
3. **And** the troubleshooting docs stay aligned with the sample behavior and current runtime terminology

## Tasks / Subtasks

- [x] Task 1: Write `docs/troubleshooting.md` covering all six failure domains (AC: 1, 2, 3)
  - [x] 1.1 Opening paragraph — state purpose, cross-reference `demo/README.md` and `docs/runtime-boundaries.md` as sources of truth for sample behavior and terminology
  - [x] 1.2 `## Installation and Foundation` — table of failure modes for `validate-foundation.py` and build errors; state supported baseline (Godot `4.6.2`, `.NET 8+`, SpacetimeDB `2.1+`); cross-reference `docs/install.md` and `docs/compatibility-matrix.md`
  - [x] 1.3 `## Code Generation` — table covering `"Spacetime Codegen"` panel states `MISSING` and `NOT CONFIGURED`; regeneration command; cross-reference `docs/codegen.md`
  - [x] 1.4 `## Compatibility Check` — table covering `"Spacetime Compat"` panel state `INCOMPATIBLE` for stale bindings and for old CLI; explain both the regeneration path and the CLI-update path; cross-reference `docs/compatibility-matrix.md`
  - [x] 1.5 `## Connection` — table covering `"Spacetime Status"` panel states `NOT CONFIGURED`, `DISCONNECTED`, and `DEGRADED`; add `ArgumentException` from `Connect()` as a programming fault row; note that `ArgumentException` fires synchronously before any connection attempt; cross-reference `docs/connection.md`
  - [x] 1.6 `## Authentication` — table of `ConnectionAuthState` values `TokenExpired` and `AuthFailed`; explain recovery for each; add `ITokenStore` throw fallback note; include demo-specific `ProjectSettingsTokenStore` reset instructions (remove `spacetime/auth/token` from Project Settings or call `ClearTokenAsync()`); cross-reference `docs/runtime-boundaries.md`
  - [x] 1.7 `## Subscriptions` — cover `SubscriptionFailed` signal; instruct developer to inspect `SubscriptionFailedEvent.ErrorMessage`; table of error message patterns (SQL syntax error → fix query; table name not found → regenerate bindings); cover `InvalidOperationException` when `Subscribe()` is called before `Connected`; note that prior authoritative cache state remains readable after failure; cross-reference `docs/runtime-boundaries.md`
  - [x] 1.8 `## Reducers` — two subsections: **Recoverable Runtime Failures** (arrive via `ReducerCallFailed` signal; table of `ReducerFailureCategory` values `Failed`, `OutOfEnergy`, `Unknown` with actions) and **Programming Faults** (do NOT fire `ReducerCallFailed`; surface via `GD.PushError` + `ConnectionStateChanged`; table of three faults: not Connected, null arg, non-`IReducerArgs`); cross-reference `demo/README.md` for expected output sequences; cross-reference `docs/runtime-boundaries.md`
  - [x] 1.9 `## See Also` — reference `docs/runtime-boundaries.md`, `demo/README.md`, `docs/quickstart.md`, `docs/install.md`, `docs/codegen.md`, `docs/compatibility-matrix.md`

- [x] Task 2: Write `tests/test_story_5_5_publish_troubleshooting_guidance_for_setup_and_runtime_failures.py` (AC: 1, 2, 3)
  - [x] 2.1 Existence test: `docs/troubleshooting.md` exists
  - [x] 2.2 Section presence tests — all eight sections present: Installation and Foundation, Code Generation, Compatibility Check, Connection, Authentication, Subscriptions, Reducers, See Also
  - [x] 2.3 Installation content tests (AC: 1, 2): contains `validate-foundation.py`; contains `4.6.2`; contains `8.0` (.NET version); contains `2.1` (SpacetimeDB version)
  - [x] 2.4 Code generation content tests (AC: 1, 2): contains `MISSING`; contains `NOT CONFIGURED`; contains `generate-smoke-test.sh`
  - [x] 2.5 Compatibility content tests (AC: 1, 2): contains `INCOMPATIBLE`; contains `regenerat` (covers regenerate/regeneration); contains `2.1+` in compat context
  - [x] 2.6 Connection content tests (AC: 1, 2): contains `ArgumentException`; contains `DEGRADED`; contains `Host` and `Database` in connection context
  - [x] 2.7 Authentication content tests (AC: 1, 2): contains `TokenExpired`; contains `AuthFailed`; contains `ClearTokenAsync`; contains `ITokenStore` (AC3 terminology); contains `ConnectionStateChanged` (AC3 signal terminology)
  - [x] 2.8 Subscriptions content tests (AC: 1, 2, 3): contains `SubscriptionFailed`; contains `SubscriptionFailedEvent` (AC3 terminology); contains `ErrorMessage`; contains `regenerat` in subscriptions context
  - [x] 2.9 Reducer content tests (AC: 1, 3): contains `ReducerCallFailed` (AC3 terminology); contains `ReducerFailureCategory` (AC3 terminology); contains `GD.PushError` (programming fault path, AC3); contains `OutOfEnergy`
  - [x] 2.10 Cross-reference alignment tests (AC: 3): contains `demo/README.md`; contains `runtime-boundaries.md`
  - [x] 2.11 Regression guards — prior story deliverables must remain intact:
    - `docs/install.md` exists
    - `docs/quickstart.md` exists
    - `docs/codegen.md` exists
    - `docs/connection.md` exists
    - `docs/runtime-boundaries.md` exists
    - `docs/compatibility-matrix.md` exists
    - `demo/README.md` exists
    - `demo/DemoMain.cs` exists
    - `docs/install.md` contains `Supported Foundation Baseline` (Story 1.1 intact)
    - `docs/quickstart.md` contains `Quickstart` (Story 1.10 intact)
    - `docs/runtime-boundaries.md` contains `ConnectionState` (connection lifecycle terminology intact)
    - `docs/runtime-boundaries.md` contains `ReducerCallFailed` (Story 4.4 reducer error model intact)
    - `docs/runtime-boundaries.md` contains `ITokenStore` (Story 2.1 auth interface intact)
    - `demo/README.md` contains `Reducer Interaction` (Story 5.3 reducer section intact)
    - `demo/DemoMain.cs` contains `ReducerCallSucceeded` (Story 5.3 wiring intact)
    - `addons/godot_spacetime/src/Public/SpacetimeClient.cs` exists (SDK public boundary intact)

## Dev Notes

### What This Story Delivers

Story 5.5 creates `docs/troubleshooting.md` — the single-stop diagnostic guide that closes the self-serve adoption loop opened by Stories 5.1–5.4. Stories 5.1–5.4 built the sample, wired the demo, and cross-linked the core docs. Story 5.5 converts the recoverable failure behaviors already defined in `docs/runtime-boundaries.md`, `docs/connection.md`, and `demo/README.md` into a concrete, scannable guide that a developer can use to diagnose problems within a single session.

**This story is purely documentation.** No C# code changes. No addons/ changes. No demo/ changes. No modifications to existing docs.

### Critical Architecture Constraints

**Do NOT reinvent or contradict any existing doc.**
Every failure mode described in `docs/troubleshooting.md` must match the behavior already specified in `docs/runtime-boundaries.md`, `docs/connection.md`, `docs/quickstart.md`, and `demo/README.md`. The troubleshooting guide is a navigation aid, not a new spec. If the existing docs describe a behavior one way, the troubleshooting guide must use the same language.

**Use exact runtime terminology from `docs/runtime-boundaries.md`.**
Every enum value, signal name, type name, and method name in the troubleshooting guide must match the public API exactly:
- Connection lifecycle: `ConnectionState`, `ConnectionStatus`, `ConnectionStateChanged`, `ConnectionOpened`, `ConnectionClosed`
- Auth: `ConnectionAuthState`, `TokenExpired`, `AuthFailed`, `ITokenStore`, `ClearTokenAsync()`
- Subscriptions: `SubscriptionHandle`, `SubscriptionApplied`, `SubscriptionFailed`, `SubscriptionAppliedEvent`, `SubscriptionFailedEvent`, `ErrorMessage`
- Reducers: `ReducerCallResult`, `ReducerCallError`, `ReducerCallSucceeded`, `ReducerCallFailed`, `ReducerFailureCategory`, `Failed`, `OutOfEnergy`, `Unknown`, `RecoveryGuidance`, `InvokeReducer()`
- Entry point: `SpacetimeClient`, `SpacetimeSettings`, `Connect()`

**Do NOT describe `ConnectionClosed` as the auth failure path.**
Auth failures surface as `ConnectionStateChanged` events with a `ConnectionAuthState` value — NOT through `ConnectionClosed`. `ConnectionClosed` fires when a previously-Connected session ends. Auth failures that prevent a connection from ever reaching Connected do not fire `ConnectionClosed`.

**Programming faults are not gameplay conditions.**
The troubleshooting guide must clearly distinguish programming faults (wrong state, null args, non-`IReducerArgs`) from recoverable runtime failures. Programming faults surface via `GD.PushError` + `ConnectionStateChanged(Disconnected)`. The `ReducerCallFailed` signal does **not** fire for programming faults.

**`ArgumentException` from `Connect()` is a programming fault.**
`ArgumentException` fires synchronously before any connection attempt when `Host` or `Database` is missing in `SpacetimeSettings`. It is NOT a runtime failure observable through signals. The fix is to set both fields before calling `Connect()`.

**Do NOT create `docs/migration-from-community-plugin.md`.**
That is Story 5.6 scope. This story creates `docs/troubleshooting.md` only.

### Exact Content for `docs/troubleshooting.md`

**Opening paragraph:**
```
This guide covers common failure modes for installation, code generation, compatibility checks, connection, authentication, and subscriptions. Each section states the visible indicator, the likely cause, and the recovery action.

The canonical end-to-end implementation path is in `demo/README.md`. All lifecycle terms used below are defined in `docs/runtime-boundaries.md`.
```

**`## Installation and Foundation` section:**

Table with three columns: Visible Indicator / Likely Cause / Recovery Action.

Rows:
1. `validate-foundation.py` exits non-zero | `.NET SDK` not found, wrong Godot version, or solution restore failure | Follow the error output; confirm `.NET 8+` is installed and Godot `4.6.2` is the editor target
2. Build errors on plugin enable | Solution incompatible with installed `.NET SDK` | Run `python3 scripts/compatibility/validate-foundation.py` and resolve reported issues; check `docs/install.md` for the supported baseline

After table, one sentence:
```
The supported baseline is Godot `4.6.2`, `.NET 8+`, and SpacetimeDB `2.1+`. See `docs/compatibility-matrix.md` for the full declared baseline.
```

**`## Code Generation` section:**

Table:
1. `"Spacetime Codegen"` panel shows `MISSING` | Bindings have not been generated yet | Run `bash scripts/codegen/generate-smoke-test.sh` from the repository root
2. `"Spacetime Codegen"` panel shows `NOT CONFIGURED` | `spacetime/modules/smoke_test/` does not exist | Confirm the module directory exists, then rerun `bash scripts/codegen/generate-smoke-test.sh`
3. `spacetime` CLI command not found | SpacetimeDB CLI not installed | Install the SpacetimeDB CLI `2.1+`

After table:
```
Running `bash scripts/codegen/generate-smoke-test.sh` clears the previous output before regenerating — no manual cleanup is required. Generated bindings are written to `demo/generated/smoke_test/`.

See `docs/codegen.md` for the full generation workflow and module locations.
```

**`## Compatibility Check` section:**

Table:
1. `"Spacetime Compat"` panel shows `INCOMPATIBLE` (bindings stale) | Module source has changed since bindings were last generated | Run `bash scripts/codegen/generate-smoke-test.sh` to regenerate
2. `"Spacetime Compat"` panel shows `INCOMPATIBLE` (CLI version) | Bindings were generated with an older CLI that does not satisfy the declared `2.1+` baseline | Update the SpacetimeDB CLI to `2.1+`, then rerun `bash scripts/codegen/generate-smoke-test.sh`

After table:
```
The compatibility panel reads the CLI version embedded in generated bindings and compares it against the declared baseline. If regeneration does not resolve `INCOMPATIBLE`, check the CLI version with `spacetime version` and update to `2.1+`. See `docs/compatibility-matrix.md` for the declared baseline.
```

**`## Connection` section:**

Table:
1. `"Spacetime Status"` panel shows `NOT CONFIGURED` | `SpacetimeSettings` resource not assigned to `SpacetimeClient`, or `SpacetimeClient` not registered as an autoload | Assign a `SpacetimeSettings` resource with `Host` and `Database` to the `SpacetimeClient` autoload entry in `Project > Project Settings > Autoload`
2. `"Spacetime Status"` panel shows `DISCONNECTED` after `Connect()` | `Host` or `Database` does not point to a running SpacetimeDB deployment | Verify SpacetimeDB is running at the configured `Host` and that the `Database` name matches the deployed module
3. `"Spacetime Status"` panel shows `DEGRADED` | The session hit a recoverable problem; reconnect policy is active | Wait for the reconnect policy to restore the session; check server availability if `DEGRADED` persists
4. `ArgumentException` thrown from `Connect()` | `Host` or `Database` is missing from `SpacetimeSettings` | Set both `Host` and `Database` fields before calling `Connect()`

After table, a NOTE paragraph:
```
`ArgumentException` from `Connect()` is a **programming fault** — it fires synchronously before any connection attempt, not through the signal path. Set `Host` and `Database` before calling `Connect()`.

Connection lifecycle state transitions are surfaced through the `SpacetimeClient.ConnectionStateChanged` signal. See `docs/connection.md` for the complete state table and editor panel labels.
```

**`## Authentication` section:**

Opening:
```
Authentication failures surface through `SpacetimeClient.ConnectionStateChanged` — not as exceptions. The `ConnectionAuthState` value on the resulting `ConnectionStatus` identifies the failure category:
```

Table with columns: ConnectionAuthState / Meaning / Recovery Action:
1. `TokenExpired` | A previously stored token was rejected by the server | Call `Settings.TokenStore?.ClearTokenAsync()` to remove the invalid token; the next `Connect()` call falls back to anonymous
2. `AuthFailed` | Explicit credentials were rejected | Update `Settings.Credentials` with a valid token before reconnecting

After table:
```
If the configured `ITokenStore` throws, `Connect()` falls back to anonymous without corrupting session state. Check the `ITokenStore` implementation for errors.
```

Then a subsection or bold note for demo-specific reset:
```
**Clearing a persisted token in the demo (`ProjectSettingsTokenStore`):**

Go to `Project > Project Settings` and remove the `spacetime/auth/token` entry, or call:

```csharp
await Settings.TokenStore.ClearTokenAsync();
```

before the next `Connect()` call.
```

After, cross-reference:
```
See `docs/runtime-boundaries.md` for the complete `ConnectionAuthState` reference and `ITokenStore` interface.
```

**`## Subscriptions` section:**

Opening:
```
Subscription failures surface through the `SpacetimeClient.SubscriptionFailed` signal. After the signal fires, the `SubscriptionHandle` transitions to `Closed` and the failed registry entry is cleaned up. Any previously authoritative subscription remains readable.

Inspect `SubscriptionFailedEvent.ErrorMessage` to determine the recovery path:
```

Table: ErrorMessage pattern / Likely Cause / Recovery Action:
1. SQL syntax error | The query string passed to `Subscribe()` is malformed | Fix the query string; verify against the SQL subset supported by SpacetimeDB
2. Table name not found | The table name in the query does not match the generated `RemoteTables` property | Regenerate bindings with `bash scripts/codegen/generate-smoke-test.sh`; confirm the module source exists

After table:
```
`Subscribe()` throws `InvalidOperationException` if called before `ConnectionState.Connected`. Wait for `SpacetimeClient.ConnectionStateChanged` to reach `Connected` before calling `Subscribe()`.

See `docs/runtime-boundaries.md` for the full `SubscriptionHandle`, `SubscriptionAppliedEvent`, and `SubscriptionFailedEvent` API reference.
```

**`## Reducers` section:**

Opening note:
```
Reducer call outcomes fall into two distinct categories that must not be conflated.
```

Subsection `### Recoverable Runtime Failures`:
```
These arrive asynchronously through the `SpacetimeClient.ReducerCallFailed` signal. Branch on `ReducerCallError.FailureCategory`:
```

Table: ReducerFailureCategory / Meaning / Recovery Action:
1. `Failed` | Server rejected the reducer call (logic error or constraint) | Check server logs; retrying with the same arguments is unlikely to succeed
2. `OutOfEnergy` | Server ran out of energy | Back off and retry after a delay
3. `Unknown` | Status could not be determined | Handle defensively; do not retry automatically without additional context

Subsection `### Programming Faults`:
```
These surface via `GD.PushError` in the Godot Output panel and `SpacetimeClient.ConnectionStateChanged`. The `ReducerCallFailed` signal does **not** fire for programming faults.
```

Table: Fault / Visible Indicator / Recovery Action:
1. `InvokeReducer()` called while not `Connected` | `GD.PushError` + `ConnectionStateChanged(Disconnected)` | Wait for `ConnectionState.Connected` before calling `InvokeReducer()`
2. `InvokeReducer()` called with `null` | `GD.PushError` + `ConnectionStateChanged(Disconnected)` | Pass a valid generated `IReducerArgs` instance (e.g., `new SpacetimeDB.Types.Reducer.Ping()`)
3. `InvokeReducer()` called with a non-`IReducerArgs` type | `GD.PushError` + `ConnectionStateChanged(Disconnected)` | Use a generated binding type from `SpacetimeDB.Types.Reducer.*`

After table:
```
For the expected success and failure output message sequences, see the `## Reducer Interaction` section in `demo/README.md`.

See `docs/runtime-boundaries.md` for the complete reducer error model and `ReducerFailureCategory` reference.
```

**`## See Also` section:**

```
- `docs/runtime-boundaries.md` — Complete public API vocabulary, all lifecycle states, signals, and the reducer error model
- `demo/README.md` — Canonical end-to-end sample; expected output message sequences for each lifecycle phase
- `docs/quickstart.md` — Step-by-step setup guide with phase-specific failure indicators and recovery actions
- `docs/install.md` — Installation prerequisites and foundation validation details
- `docs/codegen.md` — Code generation workflow and module locations
- `docs/compatibility-matrix.md` — Declared supported version baseline
```

### Project Structure Notes

**Files to create:**
- `docs/troubleshooting.md` — new troubleshooting guide (Task 1)
- `tests/test_story_5_5_publish_troubleshooting_guidance_for_setup_and_runtime_failures.py` — new test file (Task 2)

**Files NOT to touch (any modification will break prior story regression tests):**
- `docs/install.md` — complete; verified by Story 5.4 tests
- `docs/quickstart.md` — complete; verified by Story 5.4 tests
- `docs/codegen.md` — complete; verified by Story 1.6/1.7 tests
- `docs/connection.md` — complete; verified by Story 5.4 tests
- `docs/runtime-boundaries.md` — complete; verified by Story 5.4 tests
- `docs/compatibility-matrix.md` — complete; verified by Story 5.4 tests
- `demo/README.md` — complete; verified by Story 5.3/5.4 tests
- `demo/DemoMain.cs` — complete; verified by Story 5.3 tests
- `addons/godot_spacetime/` — SDK addon code; out of scope for documentation story
- `spacetime/modules/smoke_test/` — Rust source; out of scope

**Docs directory after Story 5.5:**
```
docs/
├── install.md            ← unchanged
├── quickstart.md         ← unchanged
├── codegen.md            ← unchanged
├── connection.md         ← unchanged
├── runtime-boundaries.md ← unchanged
├── compatibility-matrix.md ← unchanged
└── troubleshooting.md    ← NEW (Task 1)
```

### Test File Conventions

Same static-file-analysis pattern as Stories 5.1–5.4:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")
```

Helper used in Story 5.4 that should be reused:
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

Test function naming: `test_<file_slug>_<what_is_checked>`. All assertions include a descriptive failure message string.

Existence check pattern:
```python
def test_troubleshooting_md_exists():
    assert (ROOT / "docs/troubleshooting.md").exists(), "docs/troubleshooting.md must exist (Story 5.5)"
```

Section presence check pattern (use `_section()` helper — it asserts the section exists):
```python
def test_troubleshooting_installation_section_present():
    content = _read("docs/troubleshooting.md")
    _section(content, "Installation and Foundation")
```

Content check pattern:
```python
def test_troubleshooting_covers_token_expired():
    content = _read("docs/troubleshooting.md")
    assert "TokenExpired" in content, "docs/troubleshooting.md must cover TokenExpired auth failure (AC1, AC3)"
```

### Git Intelligence (Recent Work Patterns)

- Recent commits are all documentation-only stories (5.1–5.4): `feat(story-5.x):`
- Story 5.4 test file: 66 static-analysis tests, uses `_read()` + `_section()` + `_assert_in_order()` helpers
- Current full test suite baseline: **1725 tests passing** (from Story 5.4 senior review)
- All tests are in `tests/` root directory as `test_story_*.py` files — do NOT put new test file in a subdirectory

### Validation Commands

```bash
pytest -q tests/test_story_5_5_publish_troubleshooting_guidance_for_setup_and_runtime_failures.py
pytest -q
```

Expected: story test file passes; full suite passes with no regressions.

### References

- Story user story and AC: `_bmad-output/planning-artifacts/epics.md`, Epic 5 § Story 5.5
- FR29: "Developers can troubleshoot common integration failures using SDK documentation and examples." [Source: `_bmad-output/planning-artifacts/prd.md` § Documentation, Troubleshooting & Migration]
- `docs/troubleshooting.md` is an expected file in both the architecture directory structure and the FR→structure mapping for "Editor Workflow & Recovery UX" and "Documentation, Troubleshooting & Migration" [Source: `_bmad-output/planning-artifacts/architecture.md` § Complete Project Directory Structure + Requirements to Structure Mapping]
- All failure modes described in this story derive from behaviors already specified in: `docs/runtime-boundaries.md`, `docs/connection.md`, `docs/quickstart.md`, `demo/README.md`
- Reducer programming fault vs. recoverable runtime failure distinction: `docs/runtime-boundaries.md` § Reducer Error Model + `_bmad-output/implementation-artifacts/5-3-demonstrate-reducer-interaction-and-troubleshooting-comparison-paths.md` § Critical Architecture Constraints
- Test file pattern: `tests/test_story_5_4_publish_core_installation_and_runtime_documentation.py` (66 tests, `_read`, `_section`, `_assert_in_order` helpers)
- Current test suite baseline: 1725 passing (from Story 5.4 senior review)
- Previous story (5.4): `_bmad-output/implementation-artifacts/5-4-publish-core-installation-and-runtime-documentation.md`
- NFR16: Reproducible onboarding path [Source: epics.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- One test failure on initial run: `test_troubleshooting_installation_contains_dotnet_version` — doc used `.NET 8+` but test expected `8.0`. Fixed by updating to `.NET 8.0+` in both table row and baseline sentence to align with install.md version notation.

### Completion Notes List

- ✅ Created `docs/troubleshooting.md` — single-stop diagnostic guide covering all required sections: Installation and Foundation, Code Generation, Compatibility Check, Connection, Authentication, Subscriptions, Reducers, See Also
- ✅ All exact runtime terminology from `docs/runtime-boundaries.md` used: `ConnectionAuthState`, `TokenExpired`, `AuthFailed`, `ITokenStore`, `ClearTokenAsync()`, `SubscriptionFailed`, `SubscriptionFailedEvent`, `ErrorMessage`, `ReducerCallFailed`, `ReducerFailureCategory`, `GD.PushError`, `InvokeReducer()`
- ✅ Programming fault vs. recoverable runtime failure distinction preserved (Reducers section)
- ✅ `ArgumentException` from `Connect()` correctly documented as a synchronous programming fault, not a signal-path failure
- ✅ Auth failure path correctly documents `ConnectionStateChanged` (not `ConnectionClosed`) as the auth failure surface
- ✅ Created 54-test validation file covering existence, section presence, content, cross-references, and regression guards
- ✅ Full regression suite: 1779 tests passing (1725 baseline + 54 new), zero regressions
- ✅ QA gap-fill pass: added 23 additional assertions covering section-level cross-references, ConnectionAuthState/ProjectSettingsTokenStore/spacetime auth key, InvalidOperationException/SubscriptionHandle/SubscriptionAppliedEvent, ReducerCallError/Unknown/InvokeReducer/Disconnected, and Connection section panel states; suite now 77 tests, 1802 total passing
- ✅ Senior review hardening pass: clarified the troubleshooting intro/auth lifecycle boundaries, added 6 contract tests for source-of-truth wording, synchronous connection-fault semantics, auth `ConnectionClosed` exclusion, subscription cleanup/readability, reducer path separation, and `## See Also` completeness; suite now 83 tests, 1808 total passing

### File List

- `docs/troubleshooting.md` (new, review-clarified)
- `tests/test_story_5_5_publish_troubleshooting_guidance_for_setup_and_runtime_failures.py` (new, review-hardened: 83 tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status updated)

## Senior Developer Review (AI)

- Reviewer: Pinkyd on 2026-04-14
- Outcome: Approve
- Story Context: No separate story-context artifact was found; review used the story file, `_bmad-output/planning-artifacts/architecture.md`, `_bmad-output/planning-artifacts/epics.md`, the authoritative docs, and the new docs/tests as the primary sources.
- Epic Tech Spec: No separate Epic 5 tech spec artifact was found; `_bmad-output/planning-artifacts/architecture.md` and `_bmad-output/planning-artifacts/epics.md` were used for requirements and standards context.
- Tech Stack Reviewed: Markdown documentation contracts, Godot `4.6.2`, `.NET 8.0+`, SpacetimeDB `2.1+`, Python `pytest` static contract tests.
- External References: MCP resource discovery returned no available resources in this session; repository primary sources were sufficient and no web lookup was used.
- Git vs Story Discrepancies: 3 additional non-source automation artifacts were present under `_bmad-output/` during review (`_bmad-output/implementation-artifacts/sprint-status.yaml`, `_bmad-output/implementation-artifacts/tests/test-summary.md`, `_bmad-output/story-automator/orchestration-1-20260414-184146.md`).
- Findings fixed:
  - MEDIUM: `docs/troubleshooting.md` referenced the canonical docs but did not explicitly identify `demo/README.md` as the source of truth for sample behavior or mention reducer troubleshooting in the opening scope sentence, which left Task 1.1 / AC 3 phrased more loosely than intended. Fixed by tightening the introduction.
  - MEDIUM: The Authentication section documented `ConnectionStateChanged`, but it left the `ConnectionClosed` boundary implicit even though that lifecycle distinction is a critical runtime rule. Fixed by stating that failed auth attempts that never reach `Connected` do not emit `ConnectionClosed`.
  - MEDIUM: `tests/test_story_5_5_publish_troubleshooting_guidance_for_setup_and_runtime_failures.py` did not lock several story-critical semantics: the intro source-of-truth contract, the synchronous `ArgumentException` programming-fault note, the auth `ConnectionClosed` boundary / anonymous fallback, the subscription cleanup and authoritative-readability guarantee, the reducer two-path structure, and the full `## See Also` reference set. Fixed with 6 additional contract tests.
  - MEDIUM: The story artifact was still in `review`, carried a future-dated `2026-04-15` implementation entry, and had no `Senior Developer Review (AI)` section or sprint sync, so the review state and project tracking were stale. Fixed by correcting the record, appending this review, and syncing sprint tracking to `done`.
- Validation:
  - `pytest -q tests/test_story_5_5_publish_troubleshooting_guidance_for_setup_and_runtime_failures.py`
  - `pytest -q`

## Change Log

- 2026-04-14: Story created — comprehensive context engine analysis completed
- 2026-04-14: Story implemented — created docs/troubleshooting.md and 54-test validation suite; 1779 tests passing
- 2026-04-14: QA gap-fill — added 23 assertions (54→77 tests); full suite 1779→1802 passing
- 2026-04-14: Senior Developer Review (AI) — clarified troubleshooting source-of-truth/auth lifecycle wording, hardened Story 5.5 contract coverage to 83 tests, reran validation (`83` story tests, `1808` full-suite tests), and marked the story done.
