# Story 1.10: Validate First Setup Through a Quickstart Path

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Godot developer,
I want a quickstart validation path for first setup,
So that I can confirm installation and first connection before building gameplay features.

## Acceptance Criteria

**AC 1 — Given** a fresh supported Godot `.NET` project,
**When** I follow the quickstart and validation steps,
**Then** I can install or enable the addon, run code generation, configure the target database, review compatibility status, and reach a first successful connection.

**AC 2 — Given** a failure in any phase of the quickstart (installation, code generation, compatibility, or connection),
**When** the failure occurs,
**Then** the validation flow clearly distinguishes the failure category and surfaces a visible recovery action tied to the failing step.

**AC 3 — Given** the setup and validation surfaces in the Godot editor,
**When** a developer follows the quickstart,
**Then** the three bottom panels (`"Spacetime Codegen"`, `"Spacetime Compat"`, `"Spacetime Status"`) remain usable in narrow, standard, and wide editor panel widths with keyboard-only progression through the primary path.

## Tasks / Subtasks

- [x] Task 1 — Create `docs/quickstart.md` (AC: 1, 2, 3)
  - [x] Write prerequisites section: Godot `4.6.2`, `.NET 8+`, SpacetimeDB CLI `2.1+`
  - [x] Step 1 — Install: clone or download addon, enable plugin via `Project > Project Settings > Plugins`
  - [x] Step 2 — Foundation validation: `python3 scripts/compatibility/validate-foundation.py`; link to `docs/install.md`
  - [x] Step 3 — Code generation: `bash scripts/codegen/generate-smoke-test.sh`; reference "Spacetime Codegen" panel for status and recovery guidance; link to `docs/codegen.md`
  - [x] Step 4 — Compatibility check: reference "Spacetime Compat" panel; describe how it surfaces version match or mismatch
  - [x] Step 5 — Configure `SpacetimeSettings` resource: `[Export] Host` and `[Export] Database` fields; describe how to assign to `SpacetimeClient`
  - [x] Step 6 — Add `SpacetimeClient` as an autoload: `Project > Project Settings > Autoload`
  - [x] Step 7 — First connection from GDScript: `SpacetimeClient.Connect()`, `connection_state_changed` signal, monitor "Spacetime Status" panel
  - [x] Include a "Failure Recovery" section covering: install failures → `validate-foundation.py`, codegen failures → codegen panel recovery label, compatibility failures → compat panel recovery label, connection failures → status panel + `docs/connection.md`
  - [x] Include `## Quickstart` as the top-level section heading (required for line_check)
  - [x] Add `## See Also` pointing to `docs/install.md`, `docs/codegen.md`, `docs/connection.md`

- [x] Task 2 — Update `docs/install.md` See Also (AC: 1)
  - [x] Add `docs/quickstart.md` reference to the existing `## See Also` section

- [x] Task 3 — Update `docs/codegen.md` See Also (AC: 1)
  - [x] Add `docs/quickstart.md` reference to the existing `## See Also` section

- [x] Task 4 — Update `scripts/compatibility/support-baseline.json` (AC: 1, 2)
  - [x] Add to `required_paths`:
    - `{ "path": "docs/quickstart.md", "type": "file" }`
  - [x] Add to `line_checks`:
    - `{ "file": "docs/quickstart.md", "label": "Quickstart top-level heading", "expected_line": "## Quickstart" }`
    - `{ "file": "docs/quickstart.md", "label": "Quickstart install.md reference", "expected_line": "docs/install.md" }`
    - `{ "file": "docs/quickstart.md", "label": "Quickstart codegen.md reference", "expected_line": "docs/codegen.md" }`
    - `{ "file": "docs/quickstart.md", "label": "Quickstart connection.md reference", "expected_line": "docs/connection.md" }`
    - `{ "file": "docs/quickstart.md", "label": "Quickstart foundation validation command", "expected_line": "python3 scripts/compatibility/validate-foundation.py" }`
    - `{ "file": "docs/quickstart.md", "label": "Quickstart codegen script", "expected_line": "bash scripts/codegen/generate-smoke-test.sh" }`

- [x] Task 5 — Create `tests/test_story_1_10_quickstart.py` (AC: 1, 2, 3)
  - [x] Follow `ROOT`, `_read()`, `_lines()` pattern from Story 1.9 test exactly
  - [x] Existence test: `docs/quickstart.md` exists
  - [x] `docs/quickstart.md` content tests:
    - Contains `## Quickstart` heading
    - Contains `## Failure Recovery` or `## Troubleshooting` section
    - Contains `python3 scripts/compatibility/validate-foundation.py`
    - Contains `bash scripts/codegen/generate-smoke-test.sh`
    - Contains `SpacetimeSettings` (settings configuration explained)
    - Contains `SpacetimeClient` (autoload registration explained)
    - Contains `Connect(` (connect call shown)
    - Contains `connection_state_changed` (signal mentioned)
    - Contains `"Spacetime Codegen"` (panel referenced)
    - Contains `"Spacetime Compat"` (panel referenced)
    - Contains `"Spacetime Status"` (panel referenced)
    - Contains reference to `docs/install.md`
    - Contains reference to `docs/codegen.md`
    - Contains reference to `docs/connection.md`
  - [x] `support-baseline.json` tests:
    - Contains `docs/quickstart.md` (required path entry)
    - Contains `"Quickstart top-level heading"` (line_check label)
  - [x] `docs/install.md` tests:
    - Contains reference to `quickstart.md` in See Also section
  - [x] `docs/codegen.md` tests:
    - Contains reference to `quickstart.md` in See Also section
  - [x] Regression guards — Stories 1.7, 1.8, 1.9 panels still registered:
    - `GodotSpacetimePlugin.cs` still contains `"Spacetime Codegen"`
    - `GodotSpacetimePlugin.cs` still contains `"Spacetime Compat"`
    - `GodotSpacetimePlugin.cs` still contains `"Spacetime Status"`
    - `GodotSpacetimePlugin.cs` contains exactly THREE occurrences of `AddControlToBottomPanel`

- [x] Task 6 — Verify
  - [x] `python3 scripts/compatibility/validate-foundation.py` → exits 0
  - [x] `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
  - [x] `pytest tests/test_story_1_10_quickstart.py` → all pass
  - [x] `pytest -q` → full suite passes (stories 1.3–1.10 all green)

## Dev Notes

### Scope and What Already Exists

Story 1.10 is a **documentation and test story**. No new C# runtime code is needed. All runtime infrastructure was delivered in Stories 1.1–1.9:

| Component | Story Delivered | Current State |
|-----------|----------------|---------------|
| Plugin foundation | 1.1 | Complete — `addons/godot_spacetime/` |
| Foundation validation | 1.2 | Complete — `scripts/compatibility/validate-foundation.py` |
| Runtime-neutral concepts | 1.3 | Complete — `docs/runtime-boundaries.md` |
| `.NET` boundary enforcement | 1.4 | Complete — `Internal/Platform/DotNet/` |
| GDScript continuity proof | 1.5 | Complete — boundary verification |
| Code generation | 1.6 | Complete — `scripts/codegen/generate-smoke-test.sh` |
| "Spacetime Codegen" panel | 1.7 | Complete — `Editor/Codegen/CodegenValidationPanel.cs` |
| "Spacetime Compat" panel | 1.8 | Complete — `Editor/Compatibility/CompatibilityPanel.cs` |
| `SpacetimeClient` runtime | 1.9 | Complete — `Public/SpacetimeClient.cs` |
| "Spacetime Status" panel | 1.9 | Complete — `Editor/Status/ConnectionAuthStatusPanel.cs` |
| Connection lifecycle docs | 1.9 | Complete — `docs/connection.md` |

**DO NOT recreate any of the above.** Story 1.10 only adds `docs/quickstart.md`, a test file, and three small updates to existing docs and `support-baseline.json`.

### What Needs to Be Created

```
docs/quickstart.md                              (create)
tests/test_story_1_10_quickstart.py             (create)
```

### What Needs to Be Updated (Minimally)

```
docs/install.md                                 (add quickstart.md to See Also)
docs/codegen.md                                 (add quickstart.md to See Also)
scripts/compatibility/support-baseline.json     (add path + line_checks)
```

### DO NOT Touch

```
addons/godot_spacetime/src/**         (runtime code — complete from 1.1–1.9)
addons/godot_spacetime/GodotSpacetimePlugin.cs   (complete from 1.9 — 3 panels)
demo/**                               (read-only generated)
spacetime/modules/**                  (module source — unchanged)
scripts/codegen/**                    (codegen scripts — unchanged)
tests/test_story_1_*.py               (existing tests — only add regression guards)
.github/workflows/                    (no CI changes)
```

### `docs/quickstart.md` — Required Structure

The quickstart must follow the seven-step first-setup flow. Below is the required structure and key content requirements for each step:

```markdown
# Quickstart

## Prerequisites
- Godot editor: `4.6.2`
- `.NET` SDK: `8.0+`
- SpacetimeDB CLI: `2.1+`

## Quickstart

### Step 1 — Install and Enable the Plugin
...enable plugin via Project Settings > Plugins...

### Step 2 — Validate the Foundation
```bash
python3 scripts/compatibility/validate-foundation.py
```
...link to docs/install.md...

### Step 3 — Generate Client Bindings
```bash
bash scripts/codegen/generate-smoke-test.sh
```
...open "Spacetime Codegen" panel to confirm status...link to docs/codegen.md...

### Step 4 — Review Compatibility Status
...open "Spacetime Compat" panel...describes version match or mismatch...

### Step 5 — Configure SpacetimeSettings
...assign Host and Database fields...

### Step 6 — Add SpacetimeClient as Autoload
...Project > Project Settings > Autoload...

### Step 7 — Connect and Observe Lifecycle
```gdscript
SpacetimeClient.Connect()
```
...connection_state_changed signal..."Spacetime Status" panel...

## Failure Recovery
...distinguishes: install, codegen, compatibility, connection failures...

## See Also
- docs/install.md
- docs/codegen.md
- docs/connection.md
```

**Critical content requirements for line_check:**
- The file must contain exactly `## Quickstart` as a top-level heading (used by line_check in support-baseline.json)
- Must reference `python3 scripts/compatibility/validate-foundation.py` (exact string for line_check)
- Must reference `bash scripts/codegen/generate-smoke-test.sh` (exact string for line_check)
- Must include `docs/install.md`, `docs/codegen.md`, `docs/connection.md` references (for line_check)

### `support-baseline.json` — Additions Only

Add to the `required_paths` array (after the existing `docs/connection.md` entry):
```json
{ "path": "docs/quickstart.md", "type": "file" }
```

Add to the `line_checks` array (after the existing connection.md entry):
```json
{
  "file": "docs/quickstart.md",
  "label": "Quickstart top-level heading",
  "expected_line": "## Quickstart"
},
{
  "file": "docs/quickstart.md",
  "label": "Quickstart foundation validation command",
  "expected_line": "python3 scripts/compatibility/validate-foundation.py"
},
{
  "file": "docs/quickstart.md",
  "label": "Quickstart codegen script",
  "expected_line": "bash scripts/codegen/generate-smoke-test.sh"
},
{
  "file": "docs/quickstart.md",
  "label": "Quickstart install.md reference",
  "expected_line": "docs/install.md"
},
{
  "file": "docs/quickstart.md",
  "label": "Quickstart codegen.md reference",
  "expected_line": "docs/codegen.md"
},
{
  "file": "docs/quickstart.md",
  "label": "Quickstart connection.md reference",
  "expected_line": "docs/connection.md"
}
```

**Important:** Preserve ALL existing content, comments, and structure in `support-baseline.json`. Only append — do not reorder or reformat existing entries.

### `docs/install.md` — Minimal Update

The existing `## See Also` section currently reads:
```markdown
## See Also

- `docs/connection.md` for connection lifecycle states, signals, and editor status labels.
```

Add a quickstart reference. The exact phrasing can vary but must contain the string `quickstart.md`:
```markdown
- `docs/quickstart.md` for the step-by-step first-setup workflow from install through first connection.
```

### `docs/codegen.md` — Minimal Update

The existing `## See Also` section currently reads:
```markdown
## See Also

- `docs/connection.md` for the connection lifecycle that generated bindings eventually run against.
```

Add a quickstart reference. The exact phrasing can vary but must contain the string `quickstart.md`:
```markdown
- `docs/quickstart.md` for the step-by-step first-setup workflow that exercises code generation as part of the full flow.
```

### Test File Pattern

Follow the Story 1.9 test file exactly. Key structure:

```python
"""
Story 1.10: Validate First Setup Through a Quickstart Path
...
"""

from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

def _lines(rel: str) -> list[str]:
    return [ln.strip() for ln in _read(rel).splitlines()]
```

All tests are **pure static file/content checks** — no dotnet execution, no Godot editor launch, no live network calls.

### GDScript Connection Example for Quickstart

The quickstart doc should show a minimal GDScript snippet demonstrating the quickstart connection flow. Reference the actual public API from Story 1.9:

```gdscript
# In your scene script or autoload:
func _ready() -> void:
    SpacetimeClient.connection_state_changed.connect(_on_state_changed)
    SpacetimeClient.Connect()

func _on_state_changed(status: ConnectionStatus) -> void:
    print("Connection state: ", status.Description)
```

`SpacetimeClient` must already be registered as an autoload. The `SpacetimeSettings` resource with `Host` and `Database` must be assigned to `SpacetimeClient.Settings` before calling `Connect()`. Both are inspector-assignable `[Export]` properties.

### SpacetimeSettings Resource — How to Create

The quickstart should explain how to create a `SpacetimeSettings` resource:

1. In the Godot editor, right-click in the FileSystem panel
2. Select `New Resource` → choose `SpacetimeSettings`
3. Set `Host` (e.g., `localhost:3000`) and `Database` (e.g., `my_module`)
4. Assign the resource to the `Settings` property on the `SpacetimeClient` node in the inspector

### Editor Panel State at Each Quickstart Step

Understanding which panel shows what helps the developer verify progress:

| Quickstart Step | Panel to Check | Expected State When OK |
|----------------|----------------|------------------------|
| Step 3 — Code generation | "Spacetime Codegen" | `OK — bindings present` |
| Step 4 — Compatibility review | "Spacetime Compat" | `OK — bindings match declared baseline` |
| Step 5–6 — Settings + autoload | "Spacetime Status" | `NOT CONFIGURED — assign a SpacetimeSettings resource` (expected until Step 7) |
| Step 7 — After Connect() | "Spacetime Status" | `CONNECTED — active session established` |

### Failure Recovery Reference

| Failure Phase | Visible Indicator | Recovery Action |
|---------------|-------------------|-----------------|
| Foundation / install | `validate-foundation.py` exits non-zero | Follow error output; check `docs/install.md` |
| Code generation | "Spacetime Codegen" → `MISSING` or `NOT CONFIGURED` | Run `bash scripts/codegen/generate-smoke-test.sh`; check that `spacetime/modules/smoke_test/` exists |
| Compatibility | "Spacetime Compat" → `INCOMPATIBLE` | Regenerate bindings after updating CLI; check `docs/compatibility-matrix.md` |
| Settings / autoload | "Spacetime Status" → `NOT CONFIGURED` | Assign `SpacetimeSettings` resource with `Host` and `Database`; register `SpacetimeClient` as autoload |
| Connection | "Spacetime Status" → `DISCONNECTED` or `DEGRADED` | Verify `Host` and `Database` point to a running SpacetimeDB deployment; check `docs/connection.md` |

### Cross-Story Awareness

- **Story 2.x** (Auth) will extend `SpacetimeSettings` with auth/token fields. The quickstart should not mention auth configuration — it is not part of the first-connection flow.
- **Story 5.x** (Sample + Docs) will add a richer sample project. The quickstart created here is the minimal validated first-use path; it is not the same as the full sample walkthrough.
- **Epic 6** (Release) will validate this quickstart path against the compatibility matrix before release.
- The "Spacetime Status" panel is named with "Auth" in the class name (`ConnectionAuthStatusPanel`) because auth status will share the surface in Story 2.x — do not rename it.

### Architecture Compliance

The quickstart doc must reference only the public API (`SpacetimeClient`, `SpacetimeSettings`) — never internal types (`SpacetimeConnectionService`, `ConnectionStateMachine`, `SpacetimeSdkConnectionAdapter`). The internal boundary is invisible to consuming developers and must remain so.

Do not suggest that developers call `FrameTick()` directly — it is driven internally by `SpacetimeClient._Process()` after `Connect()`.

### Verification Sequence

Run in order — each step must pass before the next:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_1_10_quickstart.py
pytest -q
```

**Troubleshooting:**
- If `validate-foundation.py` fails with `docs/quickstart.md`: quickstart.md must exist at that exact path with the exact heading `## Quickstart`
- If a `quickstart.md` line_check fails: the expected line must appear verbatim (no surrounding whitespace matters, but the text must match exactly)
- If pytest fails on regression guards: verify `GodotSpacetimePlugin.cs` still has all three `AddControlToBottomPanel` calls and all three panel label strings unchanged

### File Locations — DO and DO NOT

**DO create:**
```
docs/quickstart.md                                (create)
tests/test_story_1_10_quickstart.py               (create)
```

**DO update (minimally):**
```
docs/install.md                                   (add quickstart.md See Also)
docs/codegen.md                                   (add quickstart.md See Also)
scripts/compatibility/support-baseline.json       (add path + line_checks)
```

**DO NOT touch:**
```
addons/godot_spacetime/src/**                     (all C# — complete from 1.1–1.9)
addons/godot_spacetime/GodotSpacetimePlugin.cs    (3-panel plugin — complete)
demo/**                                           (read-only generated)
spacetime/modules/**                              (module source)
scripts/codegen/**                                (codegen scripts)
.github/workflows/                                (no CI changes)
tests/test_story_1_3_sdk_concepts.py              (regression guard)
tests/test_story_1_8_compatibility.py             (regression guard)
tests/test_story_1_9_connection.py                (regression guard)
```

### References

- Epic 1 goal and cross-story dependencies: [Source: `_bmad-output/implementation-artifacts/epic-1-context.md`]
- Story 1.10 AC: [Source: `_bmad-output/planning-artifacts/epics.md` — Story 1.10]
- FR3/FR4 coverage: [Source: `_bmad-output/planning-artifacts/epics.md` — FR Coverage Map]
- Architecture quickstart doc requirement: [Source: `_bmad-output/planning-artifacts/architecture.md` — `docs/quickstart.md` in project structure]
- Architecture Editor/Workflow mapping: [Source: `_bmad-output/planning-artifacts/architecture.md` — "Editor Workflow & Recovery UX"]
- UX requirements (panel widths, keyboard nav): [Source: `_bmad-output/planning-artifacts/epics.md` — UX4, UX5, NFR23, NFR24]
- Story 1.9 dev notes (what connect() does, status panel): [Source: `_bmad-output/implementation-artifacts/spec-1-9-configure-and-open-a-first-connection-from-godot.md`]
- Test pattern: [Source: `tests/test_story_1_9_connection.py`]
- support-baseline.json current state: [Source: `scripts/compatibility/support-baseline.json`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `python3 scripts/compatibility/validate-foundation.py` → passed
- `dotnet build godot-spacetime.sln -c Debug` → 0 errors, 0 warnings
- `pytest tests/test_story_1_10_quickstart.py` → 42/42 passed after review hardening
- `pytest -q` → 467/467 passed (full suite, zero regressions)

### Completion Notes List

- Created `docs/quickstart.md` with all seven steps (prerequisites, install, foundation validation, codegen, compat review, settings config, connection + lifecycle). Includes Failure Recovery table and See Also section. Line_check exactness required bare-path lines in See Also section (stripped lines must equal exactly `docs/install.md`, `docs/codegen.md`, `docs/connection.md`).
- Updated `docs/install.md` See Also with `quickstart.md` reference.
- Updated `docs/codegen.md` See Also with `quickstart.md` reference.
- Updated `scripts/compatibility/support-baseline.json`: added `docs/quickstart.md` to `required_paths` and appended six `line_checks` entries covering heading, commands, and cross-references.
- Created `tests/test_story_1_10_quickstart.py` following the Story 1.9 test pattern; the review hardening pass expanded it to 42 assertions covering the quickstart doc, support baseline entries, and panel-registration regressions.
- Senior review auto-fix corrected the quickstart autoload instructions to use `addons/godot_spacetime/src/Public/SpacetimeClient.cs` and updated compatibility guidance to match the actual `CompatibilityPanel` behavior around binding freshness and declared baseline checks.

### File List

**Created:**
- `docs/quickstart.md`
- `tests/test_story_1_10_quickstart.py`

**Modified:**
- `docs/install.md`
- `docs/codegen.md`
- `scripts/compatibility/support-baseline.json`
- `_bmad-output/implementation-artifacts/spec-1-10-validate-first-setup-through-a-quickstart-path.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

- Implemented Story 1.10 — created `docs/quickstart.md`, `tests/test_story_1_10_quickstart.py`; updated `docs/install.md`, `docs/codegen.md`, `scripts/compatibility/support-baseline.json` (Date: 2026-04-14)
- 2026-04-14: Senior review auto-fixes applied — corrected quickstart autoload and compatibility instructions to match the committed implementation, expanded Story 1.10 regression coverage to 42 story tests / 467 total tests, and synced story + sprint tracking to `done`.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 2 additional non-source automation artifacts were present under `_bmad-output/` beyond the implementation File List.

### Findings Fixed

- HIGH: `docs/quickstart.md` Step 6 told developers to select a nonexistent `SpacetimeClient` node from `addons/godot_spacetime/`, while the actual autoload target is the script `addons/godot_spacetime/src/Public/SpacetimeClient.cs`; that made the documented first-connection path unreliable.
- HIGH: `docs/quickstart.md` Step 4 described the `"Spacetime Compat"` panel as checking the installed CLI version, but `CompatibilityPanel.cs` actually validates the generated binding CLI comment plus source freshness against the declared baseline, so the recovery guidance did not match the real failure modes.
- MEDIUM: the Dev Agent Record still claimed `23` story tests and `448` total tests even though the current implementation and review pass produced different results, leaving stale verification evidence in the story artifact.

### Actions Taken

- Corrected the quickstart autoload instructions to point at `addons/godot_spacetime/src/Public/SpacetimeClient.cs` and clarified the post-add inspector step for assigning `SpacetimeSettings`.
- Rewrote the compatibility step and failure-recovery guidance so it now matches the committed `CompatibilityPanel.cs` behavior: generated bindings must be current and produced by a CLI version that satisfies the declared baseline.
- Expanded `tests/test_story_1_10_quickstart.py` with regression coverage for the autoload path and compatibility wording so those documentation errors do not recur silently.
- Updated the story record, File List, and verification counts, then synced story + sprint tracking to `done`.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_1_10_quickstart.py`
- `pytest -q`

### Reference Check

- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `_bmad-output/implementation-artifacts/epic-1-context.md`
- Local reference: `docs/connection.md`
- Local reference: `addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs`
- Local reference: `addons/godot_spacetime/src/Public/SpacetimeClient.cs`
- MCP documentation search was attempted, but no MCP resources or templates were available in this session.
