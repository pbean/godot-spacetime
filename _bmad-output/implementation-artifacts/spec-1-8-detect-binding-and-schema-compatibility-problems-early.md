---
title: '1.8 Detect Binding and Schema Compatibility Problems Early'
type: 'feature'
created: '2026-04-14T00:00:00-07:00'
status: 'done'
baseline_commit: '89e9210'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-7-explain-generated-schema-concepts-and-validate-code-generation-state.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture.md'
---

# Story 1.8: Detect Binding and Schema Compatibility Problems Early

Status: done

## Story

As a Godot developer,
I want stale or incompatible generated bindings to fail clearly,
so that schema drift is actionable instead of mysterious.

## Acceptance Criteria

1. **Given** generated bindings that no longer match the target schema or supported version pair, **when** I validate or run the integration workflow, **then** the SDK or tooling reports the incompatibility with the exact failed check plus regeneration or version-guidance message.
2. **And** the failure happens before silent misuse of stale client bindings.
3. **And** the guidance points me to the supported compatibility or regeneration path.
4. **And** the compatibility and validation surface lists current target versions, compatibility status, and the next relevant action using text labels rather than color alone.

## Deliverables

This story produces six concrete outputs:

1. **`addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs`** — C# editor panel that shows declared baseline versions (Godot, SpacetimeDB CLI, ClientSDK), extracts the CLI version embedded in generated bindings, and reports OK / INCOMPATIBLE / MISSING / NOT CONFIGURED using explicit text labels.
2. **`addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn`** — Minimal Godot scene with `CompatibilityPanel` as the root, used by the plugin to mount the bottom panel.
3. **`addons/godot_spacetime/GodotSpacetimePlugin.cs` update** — Register `CompatibilityPanel` as a second bottom panel alongside the codegen panel, using the same scene-backed pattern established in Story 1.7.
4. **`docs/compatibility-matrix.md` update** — Add `## Binding Compatibility Check` section explaining the CLI version comment in generated files and how the panel validates it.
5. **`scripts/compatibility/support-baseline.json` update** — Add `required_paths` for `Editor/Compatibility/` dirs and files, plus a `line_checks` entry for the new docs section heading.
6. **`tests/test_story_1_8_compatibility.py`** — pytest suite verifying panel existence, explicit text labels, version extraction logic, plugin registration, support-baseline entries, and regression guards from Stories 1.6 and 1.7.

No changes to `addons/godot_spacetime/src/Public/` or `addons/godot_spacetime/src/Internal/`. No changes to `demo/generated/smoke_test/` (read-only artifacts stay untouched).

## Tasks / Subtasks

- [x] Task 1 — Create `addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs` (AC: 1, 2, 3, 4)
  - [x] Wrap entire file in `#if TOOLS ... #endif` (same pattern as `CodegenValidationPanel.cs`)
  - [x] Add using directives inside the `#if TOOLS` block: `using System; using System.IO; using System.Linq; using System.Text.Json; using Godot;`
  - [x] Namespace: `GodotSpacetime.Editor.Compatibility`
  - [x] Class: `public partial class CompatibilityPanel : VBoxContainer`
  - [x] Mark `[Tool]` so it evaluates in editor context
  - [x] Declare constants:
    ```csharp
    private const string RelativeBaselineJson = "scripts/compatibility/support-baseline.json";
    private const string RelativeGeneratedClient = "demo/generated/smoke_test/SpacetimeDBClient.g.cs";
    private const string RelativeModuleSource = "spacetime/modules/smoke_test";
    private const string CliVersionPrefix = "// This was generated using spacetimedb cli version ";
    private const string CompatOk = "OK — bindings match declared baseline";
    private const string CompatIncompatible = "INCOMPATIBLE — bindings do not match declared baseline";
    private const string CompatMissing = "MISSING — run codegen to generate bindings";
    private const string CompatNotConfigured = "NOT CONFIGURED";
    private const string CompatRecovery = "Run: bash scripts/codegen/generate-smoke-test.sh";
    ```
  - [x] Declare private fields:
    - `Label _godotVersionLabel` — shows declared Godot target
    - `Label _stdbVersionLabel` — shows declared SpacetimeDB CLI baseline
    - `Label _clientSdkVersionLabel` — shows declared ClientSDK version
    - `Label _bindingVersionLabel` — shows extracted CLI version from generated file (or `"not found"`)
    - `Label _compatStatusLabel` — shows one of the four `Compat*` text constants
    - `Label _recoveryLabel` — shows `CompatRecovery` when status is INCOMPATIBLE or MISSING; empty otherwise
  - [x] In `_Ready()`: call `BuildLayout()` then `RefreshStatus()`
  - [x] `BuildLayout()`: `CustomMinimumSize = new Vector2(200, 0)`, then programmatically add in order:
    1. Header label: `"Compatibility Baseline"` (bold or larger via theme override `font_size = 14`)
    2. `"Godot target:"` + `_godotVersionLabel`
    3. `"SpacetimeDB CLI:"` + `_stdbVersionLabel`
    4. `"ClientSDK:"` + `_clientSdkVersionLabel`
    5. `HSeparator`
    6. `"Binding CLI version:"` + `_bindingVersionLabel`
    7. `HSeparator`
    8. `"Compatibility status:"` + `_compatStatusLabel`
    9. `_recoveryLabel` (initially hidden)
  - [x] `RefreshStatus()`:
    1. Read `scripts/compatibility/support-baseline.json` via `ResolveProjectPath()` + `File.ReadAllText()`
    2. Parse with `System.Text.Json.JsonDocument.Parse()` — extract `support_versions.godot_product`, `support_versions.spacetimedb`, `support_versions.spacetimedb_client_sdk`
    3. Populate `_godotVersionLabel.Text`, `_stdbVersionLabel.Text`, `_clientSdkVersionLabel.Text` from parsed JSON
    4. Check module source: if `!Directory.Exists(ResolveProjectPath(RelativeModuleSource))` → `SetStatus(CompatNotConfigured)`, return
    5. Check generated file: `var generatedPath = ResolveProjectPath(RelativeGeneratedClient)`; if `!File.Exists(generatedPath)` → `SetStatus(CompatMissing, CompatRecovery)`, return
    6. Extract CLI version: scan lines of `generatedPath` for line starting with `CliVersionPrefix`; extract the version token after the prefix (split on space, take index 0); store in `_bindingVersionLabel.Text`
    7. If no version found → `_bindingVersionLabel.Text = "version not found"`, `SetStatus(CompatMissing, CompatRecovery)`, return
    8. Compare extracted version against declared `spacetimedb` baseline using `VersionSatisfiesBaseline(extractedVersion, declaredStdb)`:
       - If satisfied → `SetStatus(CompatOk)`
       - If not satisfied → `SetStatus(CompatIncompatible, CompatRecovery)`
    9. Wrap the entire logic in a `try { } catch (Exception) { SetStatus(CompatNotConfigured); }` to guard against IO errors
  - [x] `VersionSatisfiesBaseline(string extracted, string baseline)` → `bool`:
    - Strip trailing `+` from baseline: `var minimum = baseline.TrimEnd('+');`
    - Split both on `'.'`
    - For each index in `minimumParts`: parse int, parse int from `extractedParts` (default 0 if missing)
    - If extracted part > minimum part → return `true` (higher major/minor)
    - If extracted part < minimum part → return `false`
    - After loop → return `true` (equal up to declared precision)
  - [x] `CreateFocusableLabel(string text = "")`:
    ```csharp
    return new Label { Text = text, FocusMode = FocusModeEnum.All, AutowrapMode = TextServer.AutowrapMode.WordSmart };
    ```
  - [x] `ResolveProjectPath(string relativePath)`:
    ```csharp
    return Path.Combine(ProjectSettings.GlobalizePath("res://"), relativePath);
    ```
  - [x] `SetStatus(string statusText, string recoveryText = "")`: set `_compatStatusLabel.Text`, `_recoveryLabel.Text`, `_recoveryLabel.Visible`
  - [x] All labels use `FocusMode = FocusModeEnum.All` and `AutowrapMode = TextServer.AutowrapMode.WordSmart` for keyboard navigation and narrow-panel wrapping (NFR24, NFR23)
  - [x] Do NOT invoke the `spacetime` CLI from within the panel (UX2 code-first model). Read-only status only.
  - [x] The panel must NOT use color as the sole status indicator — status is conveyed entirely through `_compatStatusLabel.Text`

- [x] Task 2 — Create `addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn` (AC: 4)
  - [x] Minimal Godot scene file using `format=3`:
    ```
    [gd_scene load_steps=2 format=3]

    [ext_resource type="Script" path="res://addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs" id="1_aaaaa"]

    [node name="CompatibilityPanel" type="VBoxContainer"]
    script = ExtResource("1_aaaaa")
    ```
  - [x] The UID field is optional in `format=3`; Godot assigns it on first open. `load_steps=2` counts the root node + ext_resource.
  - [x] The scene does NOT need to replicate the programmatic layout — the script constructs child nodes at `_Ready()` runtime.

- [x] Task 3 — Update `addons/godot_spacetime/GodotSpacetimePlugin.cs` (AC: 4)
  - [x] Add `using GodotSpacetime.Editor.Compatibility;` inside the `#if TOOLS` block (after existing `using GodotSpacetime.Editor.Codegen;`)
  - [x] Add constant: `private const string CompatPanelScenePath = "res://addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn";`
  - [x] Add private field: `private CompatibilityPanel? _compatPanel;`
  - [x] In `_EnterTree()`: after the codegen panel is registered, load and register the compat panel using the same scene-backed pattern:
    ```csharp
    var compatScene = GD.Load<PackedScene>(CompatPanelScenePath);
    if (compatScene != null)
    {
        var compatRoot = compatScene.Instantiate();
        _compatPanel = compatRoot as CompatibilityPanel;
        if (_compatPanel == null)
        {
            compatRoot.QueueFree();
            GD.PushError($"Compatibility panel scene root must be {nameof(CompatibilityPanel)}.");
        }
        else
        {
    #pragma warning disable CS0618
            AddControlToBottomPanel(_compatPanel, "Spacetime Compat");
    #pragma warning restore CS0618
        }
    }
    else
    {
        GD.PushError($"Failed to load compatibility panel scene: {CompatPanelScenePath}");
    }
    ```
  - [x] In `_ExitTree()`: clean up `_compatPanel` before the existing `GD.Print`:
    ```csharp
    if (_compatPanel != null)
    {
    #pragma warning disable CS0618
        RemoveControlFromBottomPanel(_compatPanel);
    #pragma warning restore CS0618
        _compatPanel.QueueFree();
        _compatPanel = null;
    }
    ```
  - [x] Keep all existing codegen panel logic and `GD.Print` statements unchanged

- [x] Task 4 — Update `docs/compatibility-matrix.md` (AC: 3)
  - [x] Append a new `## Binding Compatibility Check` section after the existing `## Scope of This Matrix` section:
    ```markdown
    ## Binding Compatibility Check

    The Compatibility panel in the Godot editor reads the CLI version comment embedded in generated bindings and compares it against the declared `spacetimedb` baseline. Generated files contain a comment on their second line in the form:

    ```
    // This was generated using spacetimedb cli version X.Y.Z (commit ...)
    ```

    The panel extracts the version token and checks that it satisfies the declared baseline (e.g. `2.1+` requires CLI `>= 2.1`). If the extracted version does not satisfy the declared baseline, the panel reports `INCOMPATIBLE — bindings do not match declared baseline` and shows the regeneration command.

    To resolve an INCOMPATIBLE state, run:

    ```bash
    bash scripts/codegen/generate-smoke-test.sh
    ```

    Story `1.8` implements this check. Stories `1.9` and `1.10` extend the quickstart to validate both binding compatibility and connection state before declaring the setup complete.
    ```
  - [x] The exact heading `## Binding Compatibility Check` must appear as a stripped line (becomes a new `line_check` in Task 5)

- [x] Task 5 — Update `scripts/compatibility/support-baseline.json` (AC: 2, 4)
  - [x] Add to `required_paths` (after the last `addons/godot_spacetime/src/Editor/Codegen` entry):
    ```json
    { "path": "addons/godot_spacetime/src/Editor/Compatibility", "type": "dir" },
    { "path": "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs", "type": "file" },
    { "path": "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn", "type": "file" }
    ```
  - [x] Add to `line_checks` (after the last `docs/codegen.md` check):
    ```json
    {
      "file": "docs/compatibility-matrix.md",
      "label": "Binding compatibility check section heading",
      "expected_line": "## Binding Compatibility Check"
    }
    ```

- [x] Task 6 — Create `tests/test_story_1_8_compatibility.py` (AC: 1, 2, 3, 4)
  - [x] Follow exact helper patterns from `tests/test_story_1_7_schema_concepts.py` — `ROOT`, `_read()`, `_lines()` at top
  - [x] Compatibility panel existence tests:
    - `addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs` exists
    - `addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn` exists
  - [x] Panel explicit text label tests (text content, not color-only):
    - Panel `.cs` content contains `CompatOk` or the literal `"OK — bindings match declared baseline"`
    - Panel `.cs` content contains `CompatIncompatible` or `"INCOMPATIBLE — bindings do not match declared baseline"`
    - Panel `.cs` content contains `CompatMissing` or `"MISSING — run codegen to generate bindings"`
    - Panel `.cs` content contains `CompatNotConfigured` or `"NOT CONFIGURED"`
    - Panel `.cs` content contains `CompatRecovery` or `"Run: bash scripts/codegen/generate-smoke-test.sh"`
  - [x] Panel version extraction tests:
    - Panel `.cs` content contains `"spacetimedb cli version"` (verifies CLI version comment is read)
    - Panel `.cs` content contains `"support_versions"` (verifies baseline JSON is read)
    - Panel `.cs` content contains `"spacetimedb_client_sdk"` (verifies ClientSDK version is shown)
    - Panel `.cs` content contains `VersionSatisfiesBaseline` (verifies version comparison method exists)
  - [x] Panel layout tests:
    - Panel `.cs` content contains `"Compatibility Baseline"` (header label text)
    - Panel `.cs` content contains `"Binding CLI version:"` (field label)
    - Panel `.cs` content contains `"Compatibility status:"` (field label)
    - Panel `.cs` content contains `AutowrapMode` (verifies narrow-panel label wrapping)
    - Panel `.cs` content contains `FocusModeEnum.All` (verifies keyboard navigation)
    - Panel `.cs` content contains `CustomMinimumSize` (verifies narrow-panel width constraint)
  - [x] Plugin registration tests:
    - `GodotSpacetimePlugin.cs` content contains two occurrences of `AddControlToBottomPanel` (both panels registered)
    - `GodotSpacetimePlugin.cs` content contains `"Spacetime Compat"` (compat panel tab label)
    - `GodotSpacetimePlugin.cs` content contains `CompatibilityPanel` (type reference)
  - [x] Support-baseline tests:
    - `scripts/compatibility/support-baseline.json` contains `addons/godot_spacetime/src/Editor/Compatibility`
    - `scripts/compatibility/support-baseline.json` contains `CompatibilityPanel.cs`
    - `scripts/compatibility/support-baseline.json` contains `Binding Compatibility Check`
  - [x] Documentation tests:
    - `docs/compatibility-matrix.md` contains `Binding Compatibility Check` (section heading)
    - `docs/compatibility-matrix.md` contains `spacetimedb cli version` (CLI comment format explained)
  - [x] Regression guards — Story 1.7 deliverables still present:
    - `addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.cs` exists
    - `addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn` exists
    - `GodotSpacetimePlugin.cs` contains `"Spacetime Codegen"` (codegen panel still registered)
    - `docs/codegen.md` contains `Generated Schema Concepts`
  - [x] Regression guards — Story 1.6 deliverables still present:
    - `demo/generated/smoke_test/` directory exists
    - At least one `.cs` file exists in `demo/generated/smoke_test/` (use `rglob("*.cs")`)
    - `scripts/codegen/generate-smoke-test.sh` exists

- [x] Task 7 — Verify all checks pass (AC: all)
  - [x] Run `python3 scripts/compatibility/validate-foundation.py` — exits 0
  - [x] Run `dotnet build godot-spacetime.sln -c Debug` — 0 errors, 0 warnings
  - [x] Run `pytest tests/test_story_1_8_compatibility.py` — all tests pass
  - [x] Run `pytest -q` — full suite still green (stories 1.3–1.8 all pass)

## Dev Notes

### Story Scope and Context

Story 1.7 created the first editor panel (`CodegenValidationPanel`) under `Editor/Codegen/` and established the plugin registration pattern. Story 1.8 adds the second committed MVP editor panel (`CompatibilityPanel`) under `Editor/Compatibility/` — the architecture explicitly names this as a distinct surface area. Stories 1.9 and 1.10 will add `Editor/Status/` and use the quickstart path.

**DO**: Add `Editor/Compatibility/CompatibilityPanel.cs`, `.tscn`, update plugin, update docs, update support-baseline, write tests.

**DO NOT**: Modify `addons/godot_spacetime/src/Public/` or `addons/godot_spacetime/src/Internal/`. Touch `demo/generated/smoke_test/` (read-only). Invoke the `spacetime` CLI from within panel code. Use color as the only status indicator. Modify `docs/codegen.md`, `docs/runtime-boundaries.md`, or `docs/install.md`. Modify `.github/workflows/`. Touch `tests/fixtures/generated/` (reserved for Story 1.9+).

### CLI Version Comment — The Compatibility Signal

Every file generated by `spacetime generate --lang csharp` starts with:
```
// THIS FILE IS AUTOMATICALLY GENERATED BY SPACETIMEDB. EDITS TO THIS FILE
// WILL NOT BE SAVED. MODIFY TABLES IN YOUR MODULE SOURCE CODE INSTEAD.

// This was generated using spacetimedb cli version 2.1.0 (commit 6981f48b4bc1a71c8dd9bdfe5a2c343f6370243d).
```

The canonical source for extracting the CLI version is `demo/generated/smoke_test/SpacetimeDBClient.g.cs` (the module binding registry file — always generated). Use `RelativeGeneratedClient = "demo/generated/smoke_test/SpacetimeDBClient.g.cs"` as the path constant.

The line to match starts with: `"// This was generated using spacetimedb cli version "` (use this as `CliVersionPrefix`). After the prefix, the first whitespace-delimited token is the version string (e.g. `"2.1.0"`). The rest of the line is the commit hash in parentheses — ignore it.

### Version Comparison — VersionSatisfiesBaseline

The declared baseline in `support-baseline.json` uses the format `"X.Y+"` (e.g. `"2.1+"`), meaning >= X.Y. The extracted CLI version uses `"X.Y.Z"` format.

Algorithm:
1. Strip trailing `+` from baseline string → `"2.1"`
2. Split both on `'.'` → `["2","1"]` and `["2","1","0"]`
3. Iterate baseline parts; for each index i:
   - Parse `extracted[i]` as int (default 0 if missing); parse `baseline[i]` as int
   - If `extracted > baseline` → `true` (higher major/minor wins immediately)
   - If `extracted < baseline` → `false`
4. After loop → `true` (equal up to declared precision)

Edge cases: `"2.1.0"` vs `"2.1+"` → true. `"2.0.5"` vs `"2.1+"` → false. `"3.0.0"` vs `"2.1+"` → true.

### Reading support-baseline.json in the Panel

Use `System.Text.Json.JsonDocument` (available in `net8.0` BCL without additional NuGet references):

```csharp
var jsonPath = ResolveProjectPath(RelativeBaselineJson);
var jsonText = File.ReadAllText(jsonPath);
using var doc = JsonDocument.Parse(jsonText);
var sv = doc.RootElement.GetProperty("support_versions");
var declaredGodot = sv.GetProperty("godot_product").GetString() ?? "?";
var declaredStdb = sv.GetProperty("spacetimedb").GetString() ?? "?";
var declaredClientSdk = sv.GetProperty("spacetimedb_client_sdk").GetString() ?? "?";
```

This is deterministic and avoids any Godot-specific JSON API dependencies. Wrap in a try/catch to handle missing file gracefully → `SetStatus(CompatNotConfigured)`.

### GodotSpacetimePlugin.cs Update — Registration Order

The codegen panel is registered first (`"Spacetime Codegen"`), then the compat panel (`"Spacetime Compat"`). Both use the same `#pragma warning disable CS0618` pattern for the deprecated bottom-panel API. Both load their respective `.tscn` scenes via `GD.Load<PackedScene>()`.

Field declarations at class top:
```csharp
private const string CodegenPanelScenePath = "..."; // already exists
private const string CompatPanelScenePath = "res://addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn";
private CodegenValidationPanel? _codegenPanel; // already exists
private CompatibilityPanel? _compatPanel;
```

In `_EnterTree()`: codegen registration block runs first (unchanged), then compat registration block runs. Both blocks are guarded with null checks and `GD.PushError()` fallback. The `GD.Print("Godot Spacetime plugin enabled.")` line runs after both registrations.

In `_ExitTree()`: compat cleanup runs first (before codegen cleanup), then the existing codegen cleanup block. The `GD.Print("Godot Spacetime plugin disabled.")` line runs after both cleanups.

### CompatibilityPanel.tscn — Minimal Valid Format

```
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs" id="1_aaaaa"]

[node name="CompatibilityPanel" type="VBoxContainer"]
script = ExtResource("1_aaaaa")
```

The `uid` field is optional in `format=3`; Godot will assign one on first open. If the build fails due to a missing UID, open the scene in the Godot editor once to let it assign a UID and re-commit.

### support-baseline.json Update — Exact JSON Snippets

**Add to `required_paths`** (after the last `addons/godot_spacetime/src/Editor/Codegen/CodegenValidationPanel.tscn` entry):

```json
    { "path": "addons/godot_spacetime/src/Editor/Compatibility", "type": "dir" },
    { "path": "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs", "type": "file" },
    { "path": "addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn", "type": "file" }
```

**Add to `line_checks`** (after the last `docs/codegen.md` check — the `"Schema concepts section heading"` entry):

```json
    {
      "file": "docs/compatibility-matrix.md",
      "label": "Binding compatibility check section heading",
      "expected_line": "## Binding Compatibility Check"
    }
```

### docs/compatibility-matrix.md Update

Add at the end of the file, after the existing `## Scope of This Matrix` section:

```markdown
## Binding Compatibility Check

The Compatibility panel in the Godot editor reads the CLI version comment embedded in generated bindings and compares it against the declared `spacetimedb` baseline. Generated files contain a comment on their second line in the form:

```
// This was generated using spacetimedb cli version X.Y.Z (commit ...)
```

The panel extracts the version token and checks that it satisfies the declared baseline (e.g. `2.1+` requires CLI `>= 2.1`). If the extracted version does not satisfy the declared baseline, the panel reports `INCOMPATIBLE — bindings do not match declared baseline` and shows the regeneration command.

To resolve an INCOMPATIBLE state, run:

```bash
bash scripts/codegen/generate-smoke-test.sh
```

Story `1.8` implements this check. Stories `1.9` and `1.10` extend the quickstart to validate both binding compatibility and connection state before declaring the setup complete.
```

The exact heading `## Binding Compatibility Check` must appear as a stripped line.

### Verification After Implementation

Run all four commands in order:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_1_8_compatibility.py
pytest -q
```

Expected outcomes:
- `validate-foundation.py` — exits 0 (new required paths and line_check all resolve)
- `dotnet build` — 0 errors, 0 warnings
- `pytest tests/test_story_1_8_compatibility.py` — all tests pass
- `pytest -q` — full suite passes (stories 1.3–1.8 all green)

**Troubleshooting:**
- If `dotnet build` fails with `CS0246 type or namespace CompatibilityPanel not found` in `GodotSpacetimePlugin.cs`: verify `using GodotSpacetime.Editor.Compatibility;` is inside the `#if TOOLS` block and `CompatibilityPanel.cs` is wrapped in `#if TOOLS`.
- If `dotnet build` fails with `System.Text.Json not found`: this is unexpected in `net8.0` — verify `<TargetFramework>net8.0</TargetFramework>` in the `.csproj`. No additional NuGet reference is needed.
- If `validate-foundation.py` fails on new `required_paths`: verify the paths in `support-baseline.json` exactly match the file paths created (check `Editor/Compatibility` vs `Editor/Compat`).
- If `validate-foundation.py` fails on new `line_check`: verify `docs/compatibility-matrix.md` has `## Binding Compatibility Check` as an exact stripped line.
- If the Godot editor shows a plugin error for the compat scene: open `CompatibilityPanel.tscn` once in the editor to assign UID, then re-commit.
- If `test_plugin_registers_both_panels` fails: verify `GodotSpacetimePlugin.cs` contains two distinct `AddControlToBottomPanel` calls — one for codegen, one for compat.

### Cross-Story Awareness

- **Story 1.9** will add `Editor/Status/ConnectionAuthStatusPanel` following the same plugin registration pattern. The compat panel registration block in `GodotSpacetimePlugin.cs` should be clean enough to serve as the pattern template.
- **Story 1.10** exercises the full quickstart path and will rely on both the codegen panel and compatibility panel being present and returning correct status.
- **`tests/fixtures/generated/`** remains reserved for later stories that introduce schema-mutation or multi-version fixture testing.
- **`spacetime/modules/compatibility_fixture/`** remains reserved for future schema-drift scenarios; Story 1.8 does not populate it.

### Project Structure for This Story

**Files to create:**
```
addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs   — editor panel (#if TOOLS)
addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn  — minimal Godot scene
tests/test_story_1_8_compatibility.py                                    — pytest suite
```

**Files to update:**
```
addons/godot_spacetime/GodotSpacetimePlugin.cs       — add compat panel registration
docs/compatibility-matrix.md                          — add "Binding Compatibility Check" section
scripts/compatibility/support-baseline.json           — add Editor/Compatibility/ paths + line_check
```

**Files to NOT touch:**
```
addons/godot_spacetime/src/Public/**                 — public SDK surface unchanged
addons/godot_spacetime/src/Internal/**               — internal SDK unchanged
demo/generated/smoke_test/**                         — read-only generated artifacts
spacetime/modules/**                                 — module source unchanged
scripts/codegen/**                                   — codegen scripts unchanged
docs/codegen.md                                      — schema concepts doc unchanged
docs/runtime-boundaries.md                           — GDScript seam doc unchanged
docs/install.md                                      — unchanged
.github/workflows/                                   — no CI changes
tests/fixtures/generated/                            — reserved for Story 1.9+
addons/godot_spacetime/src/Editor/Codegen/**         — Story 1.7 deliverables unchanged
```

### Git Context: Recent Commits

- `89e9210` feat(story-1.7): Adds `CodegenValidationPanel.cs` (`#if TOOLS`, scene-backed, explicit text labels), `CodegenValidationPanel.tscn`, plugin registration in `GodotSpacetimePlugin.cs`, `docs/codegen.md` schema-concepts section, `support-baseline.json` Editor/Codegen paths. 291 tests green.
- `2d08914` feat(story-1.6): Adds `spacetime/modules/smoke_test/`, `scripts/codegen/generate-smoke-test.sh`, `demo/generated/smoke_test/` generated bindings, `docs/codegen.md` codegen guidance.
- `bd8acf3` feat(story-1.4): `Internal/Platform/DotNet/` adapters with `SpacetimeDB.ClientSDK 2.1.0` PackageReference.

Story 1.8 follows the exact patterns established in Story 1.7: `#if TOOLS` guard, `[Tool]` attribute, `VBoxContainer` root, programmatic layout in `BuildLayout()`, `RefreshStatus()` called from `_Ready()`, explicit text status constants, `FocusModeEnum.All` for keyboard navigation, `AutowrapMode.WordSmart` for narrow panels, `ProjectSettings.GlobalizePath("res://")` for path resolution, scene-backed plugin registration via `GD.Load<PackedScene>()`.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_No issues encountered._

### Completion Notes List

- Implemented `CompatibilityPanel.cs` under `Editor/Compatibility/` following exact `#if TOOLS`, `[Tool]`, `VBoxContainer` pattern from Story 1.7's `CodegenValidationPanel.cs`.
- Version comparison uses `VersionSatisfiesBaseline()` which correctly handles the `"X.Y+"` baseline format against `"X.Y.Z"` extracted CLI versions.
- `RefreshStatus()` reads `support-baseline.json` via `System.Text.Json.JsonDocument` (no extra NuGet reference needed for `net8.0`). All four status states (OK, INCOMPATIBLE, MISSING, NOT CONFIGURED) are text-only; no color dependency.
- Plugin restructured from early-return pattern to if/else blocks so both panels register independently with a single `GD.Print` at the end of `_EnterTree`.
- `validate-foundation.py` exits 0 — new `required_paths` and `line_check` all resolve.
- `dotnet build` — 0 errors, 0 warnings.
- `pytest tests/test_story_1_8_compatibility.py` — 59/59 passed after review hardening.
- `pytest -q` — 351/351 passed (full suite including stories 1.3–1.8 plus review coverage).

### File List

**Created:**
- `addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs`
- `addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.tscn`
- `tests/test_story_1_8_compatibility.py`

**Modified:**
- `addons/godot_spacetime/GodotSpacetimePlugin.cs`
- `docs/compatibility-matrix.md`
- `scripts/compatibility/support-baseline.json`
- `scripts/compatibility/validate-foundation.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/spec-1-8-detect-binding-and-schema-compatibility-problems-early.md`

## Change Log

- 2026-04-14: Story 1.8 implementation complete — added `CompatibilityPanel.cs` and `.tscn` under `Editor/Compatibility/`, registered second bottom panel ("Spacetime Compat") in `GodotSpacetimePlugin.cs`, added `## Binding Compatibility Check` section to `docs/compatibility-matrix.md`, added `Editor/Compatibility/` paths and line_check to `support-baseline.json`, wrote 32-test pytest suite in `tests/test_story_1_8_compatibility.py`. All 324 suite tests green.
- 2026-04-14: Senior review auto-fixes applied — hardened compatibility validation to reject stale bindings and unsupported CLI versions in both the panel and `validate-foundation.py`, corrected compatibility docs, expanded regression coverage to 59 story tests / 351 total tests, and synced story + sprint tracking to `done`.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve
Git vs Story Discrepancies: 3 additional changes were present beyond the original File List: 2 non-source automation artifacts under `_bmad-output/` plus 1 review-time source edit to `scripts/compatibility/validate-foundation.py` required to make AC 1 and AC 2 true in the documented validation workflow.

### Findings Fixed

- HIGH: `scripts/compatibility/validate-foundation.py` only checked required paths and exact lines, so the documented validation workflow could still pass while stale bindings or an unsupported generated CLI version remained in place.
- MEDIUM: `addons/godot_spacetime/src/Editor/Compatibility/CompatibilityPanel.cs` only exposed a generic incompatible/missing state and left the binding-version field blank in fallback paths, so the panel did not report the exact failed check or stable placeholder text when compatibility inputs were missing.
- LOW: `docs/compatibility-matrix.md` told users the CLI-version comment lived on the "second line", but the committed generated file places it after the two-line generated warning banner and blank separator.

### Actions Taken

- Hardened `scripts/compatibility/validate-foundation.py` with generated-CLI baseline checks, stale-binding detection against relevant module source files, and exact regeneration guidance so the non-editor validation path now enforces Story 1.8's compatibility contract.
- Updated `CompatibilityPanel.cs` to reset fallback values consistently, keep the binding-version label explicit in failure states, detect stale bindings before runtime use, and surface specific incompatibility reasons together with the supported regeneration command.
- Corrected `docs/compatibility-matrix.md` so the generated-file comment location matches the committed artifacts and the docs now explain that validation rejects stale bindings before runtime use.
- Expanded `tests/test_story_1_8_compatibility.py` with regression coverage for the stricter panel behavior and the new validation-workflow helpers, then revalidated the story-specific and full test suites.
- Corrected the story status metadata, File List, and validation counts, then synced sprint tracking to `done`.

### Validation

- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_1_8_compatibility.py`
- `pytest -q`

### Reference Check

- Local reference: `_bmad-output/planning-artifacts/architecture.md`
- Local reference: `_bmad-output/implementation-artifacts/spec-1-7-explain-generated-schema-concepts-and-validate-code-generation-state.md`
- Local reference: `docs/compatibility-matrix.md`
- Local reference: `demo/generated/smoke_test/SpacetimeDBClient.g.cs`
