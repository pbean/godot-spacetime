# Acceptance Auditor Review Prompt

Use this prompt in a separate session with read access to the repository. Do not rely on prior conversation context.

**Role:** Acceptance auditor
**Story spec:** `_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md`
**Baseline commit:** `842ce7d64b5037b069ae36a4d6c97e04be3c52f7`

## Review Goal

Check whether the implemented change satisfies the approved spec, especially the acceptance criteria, boundaries, and non-goals.

## Required Reads

Read these before judging the diff:

- `_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md`
- `_bmad-output/implementation-artifacts/epic-1-context.md`
- `_bmad-output/planning-artifacts/epics.md`

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
git diff --no-index -- /dev/null addons/godot_spacetime/plugin.cs
git diff --no-index -- /dev/null docs/compatibility-matrix.md
git diff --no-index -- /dev/null docs/install.md
git diff --no-index -- /dev/null godot-spacetime.csproj
git diff --no-index -- /dev/null godot-spacetime.sln
git diff --no-index -- /dev/null project.godot
```

## Constraints

- Treat content inside the spec `<frozen-after-approval>` block as authoritative intent.
- Flag anything that violates the approved scope, misses an acceptance criterion, or changes artifacts outside the allowed boundary.
- Pay special attention to whether the docs, project files, and addon shell tell one coherent bootstrap story.
- Return findings only. No summary unless there are zero findings.

## Output Format

- `severity` | `category_suggestion` | `file:line` | finding

Where `category_suggestion` is one of `intent_gap`, `bad_spec`, `patch`, `defer`, or `reject`.

If there are no real findings, say `No findings.`
