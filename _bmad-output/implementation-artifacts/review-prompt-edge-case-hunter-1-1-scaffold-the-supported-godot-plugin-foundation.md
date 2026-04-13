# Edge Case Hunter Review Prompt

Use this prompt in a separate session with read access to the repository. Do not rely on prior conversation context.

**Role:** `bmad-review-edge-case-hunter`
**Story spec:** `_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md`
**Baseline commit:** `842ce7d64b5037b069ae36a4d6c97e04be3c52f7`

## Review Goal

Inspect the diff and then explore the repository only where needed to find boundary-condition problems, bootstrap gaps, version-consistency issues, or acceptance-criteria misses introduced or exposed by this story.

## Inputs

- Story spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md`
- Context doc: `_bmad-output/implementation-artifacts/epic-1-context.md`
- Key implementation files:
  - `project.godot`
  - `godot-spacetime.csproj`
  - `godot-spacetime.sln`
  - `addons/godot_spacetime/plugin.cfg`
  - `addons/godot_spacetime/GodotSpacetimePlugin.cs`
  - `README.md`
  - `docs/install.md`
  - `docs/compatibility-matrix.md`

## Diff Reproduction

Run these commands locally and review the combined output:

```bash
git diff --no-ext-diff -- _bmad-output/implementation-artifacts/sprint-status.yaml
git diff --no-index -- /dev/null README.md
git diff --no-index -- /dev/null _bmad-output/implementation-artifacts/deferred-work.md
git diff --no-index -- /dev/null _bmad-output/implementation-artifacts/epic-1-context.md
git diff --no-index -- /dev/null _bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md
git diff --no-index -- /dev/null addons/godot_spacetime/assets/icon.svg
git diff --no-index -- /dev/null addons/godot_spacetime/plugin.cfg
git diff --no-index -- /dev/null addons/godot_spacetime/GodotSpacetimePlugin.cs
git diff --no-index -- /dev/null docs/compatibility-matrix.md
git diff --no-index -- /dev/null docs/install.md
git diff --no-index -- /dev/null godot-spacetime.csproj
git diff --no-index -- /dev/null godot-spacetime.sln
git diff --no-index -- /dev/null project.godot
```

## Constraints

- Prioritize hidden setup defects, version-drift risks, plugin-enable assumptions, and repo-shape decisions that later stories would have to undo.
- Treat `.gitignore` as intentionally unchanged unless the new scaffold proves it is now insufficient.
- Return findings only. No recap unless there are zero findings.

## Output Format

- `severity` | `category_suggestion` | `file:line` | finding

Where `category_suggestion` is one of `intent_gap`, `bad_spec`, `patch`, `defer`, or `reject`.

If there are no real findings, say `No findings.`
