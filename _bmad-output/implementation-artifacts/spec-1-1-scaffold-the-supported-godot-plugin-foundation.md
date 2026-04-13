---
title: '1.1 Scaffold the Supported Godot Plugin Foundation'
type: 'feature'
created: '2026-04-13T22:04:21-07:00'
status: 'done'
baseline_commit: '842ce7d64b5037b069ae36a4d6c97e04be3c52f7'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The repository does not yet contain a supported Godot `.NET` workspace or installable addon shell, so later runtime, validation, and code-generation work would be forced to invent structure while implementing deeper features. Without an explicit foundation, adopters also have no authoritative version baseline or bootstrap guidance for opening the repo as a supported Godot project.

**Approach:** Create the official Godot `.NET` project foundation at the repository root and scaffold the shipping addon under `addons/godot_spacetime/`, with the minimal plugin entrypoint, icon, and root solution files needed for later work. In the same slice, publish the initial support baseline and bootstrap steps in docs so a maintainer or adopter can restore dependencies, open the root Godot project, and enable the addon without moving folders around.

## Boundaries & Constraints

**Always:** Keep the repository root as the Godot development workspace; place the distributable addon at `addons/godot_spacetime/`; create a repo-root `godot-spacetime.sln`; add a C# plugin entrypoint plus `plugin.cfg`; declare the initial support baseline for Godot `4.6.2`, `.NET 8+`, and SpacetimeDB `2.1+`; document the required restore or build expectation before later validation or code-generation steps; keep naming and layout consistent with the planned addon boundary so later stories do not need repo restructuring.

**Ask First:** Renaming the addon from `godot_spacetime`; changing the declared support baseline; introducing extra shipping artifacts outside `addons/godot_spacetime/`; replacing the root Godot workspace approach with a different repo layout.

**Never:** Implement runtime connection, auth, code generation, compatibility UI, CI workflows, or sample/demo behavior in this story; define the public product model in `.NET`-only terms; ship generated bindings, fixtures, or demo assets as part of the addon foundation; require adopters to move the addon into a different folder layout to enable it.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fresh foundation | Repository has planning docs but no Godot project, solution, or addon shell | Root workspace contains `project.godot`, `godot-spacetime.sln`, a C# project file, and `addons/godot_spacetime/` with `plugin.cfg`, plugin entrypoint, and icon assets in place | N/A |
| Bootstrap guidance | A maintainer or adopter opens the repo before later validation or codegen exists | Docs state the supported versions, the required dependency restore or build step for C# scripts, and the expected Godot project opening or plugin-enable flow | Guidance makes the missing prerequisite explicit instead of assuming unstated setup knowledge |

</frozen-after-approval>

## Code Map

- `_bmad-output/implementation-artifacts/epic-1-context.md` -- distilled Epic 1 requirements, architecture constraints, and story sequencing.
- `_bmad-output/planning-artifacts/epics.md` -- Story 1.1 acceptance criteria and Epic 1 dependency chain.
- `_bmad-output/planning-artifacts/architecture.md` -- target repo layout, addon boundary, naming rules, and packaging constraints.
- `.gitignore` -- existing ignore rules already cover Godot and .NET build artifacts; likely needs only targeted adjustment if the scaffold introduces new local-state outputs.
- `project.godot` -- root Godot workspace file to create for local development and plugin enablement.
- `godot-spacetime.csproj` -- repo-root C# project that compiles the plugin entrypoint and future addon source.
- `godot-spacetime.sln` -- repo-root solution required by the story acceptance criteria.
- `addons/godot_spacetime/plugin.cfg` -- addon metadata and entrypoint registration.
- `addons/godot_spacetime/GodotSpacetimePlugin.cs` -- C# editor plugin entrypoint, named to match Godot's C# editor-plugin resolution expectations.
- `addons/godot_spacetime/assets/icon.svg` -- plugin icon referenced by `plugin.cfg`.
- `README.md` -- high-level install and repository bootstrap entrypoint for adopters.
- `docs/install.md` -- detailed bootstrap steps and Godot project expectations before later stories.
- `docs/compatibility-matrix.md` -- initial declared support baseline that later validation can check for drift.

## Tasks & Acceptance

**Execution:**
- [x] `project.godot` -- create the root Godot `.NET` workspace metadata for the repository -- establishes the repo as a supported Godot project instead of a docs-only folder.
- [x] `godot-spacetime.csproj` and `godot-spacetime.sln` -- add the repo-root C# project and classic solution file for the addon source -- satisfies the root solution requirement and gives Godot C# scripts a standard build target.
- [x] `addons/godot_spacetime/plugin.cfg`, `addons/godot_spacetime/GodotSpacetimePlugin.cs`, and `addons/godot_spacetime/assets/icon.svg` -- scaffold the official addon shell with a minimal C# plugin entrypoint and plugin metadata -- makes the addon enableable from a supported Godot project without folder moves.
- [x] `.gitignore` -- confirm or extend ignores only for scaffold-generated Godot/.NET local state -- keeps the new foundation usable without polluting version control.
- [x] `README.md`, `docs/install.md`, and `docs/compatibility-matrix.md` -- publish the support baseline and bootstrap guidance for restore, opening the root project, and enabling the addon -- gives adopters an explicit installation path before later validation and code-generation stories land.

**Acceptance Criteria:**
- Given a fresh clone of the repository, when a maintainer inspects the root workspace, then `project.godot`, `godot-spacetime.csproj`, and `godot-spacetime.sln` exist at the repository root and the addon shell exists under `addons/godot_spacetime/`.
- Given the addon scaffold is present, when the repository is opened as a supported Godot `.NET` project, then the plugin can be enabled from the standard plugin flow without moving addon files into a different project structure.
- Given an adopter reads the bootstrap docs, when they prepare to use the repository foundation, then the docs explicitly declare Godot `4.6.2`, `.NET 8+`, and SpacetimeDB `2.1+` as the initial support baseline and call out the required dependency restore or build expectation before later validation or code generation.
- Given later stories need runtime, editor, and packaging work, when they build on this foundation, then they can extend the existing root workspace and addon boundary instead of reshaping the repository layout first.

## Design Notes

This story should stay narrowly focused on the installable shell. The scaffold should create the same root facts future stories depend on, but it should not pre-implement runtime boundaries or editor UX beyond the minimal plugin entrypoint.

Expected shape after this story:

```text
project.godot
godot-spacetime.csproj
godot-spacetime.sln
addons/godot_spacetime/
  plugin.cfg
  GodotSpacetimePlugin.cs
  assets/icon.svg
docs/
  install.md
  compatibility-matrix.md
```

## Spec Change Log

- 2026-04-13: Review patches after adversarial, edge-case, and acceptance review.
  Trigger: review findings on malformed solution metadata, incorrect Release mapping, repo-wide C# compile globs, missing plugin icon metadata, and Release-unsafe editor-plugin compilation.
  Amended: constrained `godot-spacetime.csproj` compile items to `addons/godot_spacetime/**/*.cs`, fixed `godot-spacetime.sln` Release configuration, added `#if TOOLS` guard to the editor plugin class, wired plugin icon metadata in `plugin.cfg`, and aligned `docs/compatibility-matrix.md` with the planned `SpacetimeDB.ClientSDK 2.1.0` runtime baseline.
  Avoids: a scaffold that appears valid in Debug but breaks Release builds, compiles future non-addon C# files into the shipping assembly, or drifts from the declared runtime package baseline.
  KEEP: repo-root workspace, addon boundary, explicit bootstrap docs, and the minimal plugin shell shape.

- 2026-04-13: Post-review editor verification fixes after running the real Godot `4.6.2` editor.
  Trigger: editor-side verification showed the addon existed but could not be enabled until plugin metadata matched Godot's C# editor-plugin loading expectations.
  Amended: switched `plugin.cfg` to addon-relative `icon` and `script` paths and renamed the C# plugin entry file to `GodotSpacetimePlugin.cs` so the file name and plugin class name align during editor-plugin resolution.
  Avoids: Godot resolving the script as `res://addons/.../res://...`, and silent editor refusal to enable the plugin even after the project builds.
  KEEP: the same plugin class name, addon location, and documented “build before enable” bootstrap flow.

## Verification

**Commands:**
- `dotnet sln godot-spacetime.sln list` -- expected: the root solution exists and lists the repo C# project.
- `dotnet build godot-spacetime.sln` -- expected: the scaffold compiles successfully once Godot C# assets and restore are in place.
- Temporary editor-side verifier in a temp clone after `dotnet build godot-spacetime.sln` -- expected: `EditorInterface.set_plugin_enabled("res://addons/godot_spacetime/plugin.cfg", true)` reports `enabled=true`.

**Manual checks (if no CLI):**
- Open the repository root as a Godot `.NET` project and confirm the plugin appears under the standard plugin management UI with the expected name and icon.
- Review `README.md`, `docs/install.md`, and `docs/compatibility-matrix.md` and confirm they declare the support baseline and the restore or build prerequisite before later validation or code-generation flows.

## Suggested Review Order

**Build Boundary**

- Start here; it constrains compilation to the shipping addon surface.
  [`godot-spacetime.csproj:1`](../../godot-spacetime.csproj#L1)

- Confirm Debug and Release are both real solution configurations.
  [`godot-spacetime.sln:1`](../../godot-spacetime.sln#L1)

- Check the root Godot workspace metadata and icon wiring.
  [`project.godot:1`](../../project.godot#L1)

**Addon Shell**

- Verify the plugin metadata matches the documented install surface.
  [`plugin.cfg:1`](../../addons/godot_spacetime/plugin.cfg#L1)

- Confirm the editor plugin file/class naming and tools-only guard match editor expectations.
  [`GodotSpacetimePlugin.cs:1`](../../addons/godot_spacetime/GodotSpacetimePlugin.cs#L1)

- Inspect the shared icon asset referenced by the workspace and addon.
  [`icon.svg:1`](../../addons/godot_spacetime/assets/icon.svg#L1)

**Bootstrap Contract**

- Read the maintainer-facing entrypoint before the detailed install docs.
  [`README.md:1`](../../README.md#L1)

- Verify the supported enablement flow and explicit version notes.
  [`install.md:1`](../../docs/install.md#L1)

- Check the declared compatibility baseline and planned runtime package target.
  [`compatibility-matrix.md:1`](../../docs/compatibility-matrix.md#L1)

**Planning Context**

- Confirm the scaffold still matches the distilled Epic 1 constraints.
  [`epic-1-context.md:1`](./epic-1-context.md#L1)
