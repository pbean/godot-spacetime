# Blind Hunter Review Prompt

Use this prompt in a separate session with no conversation history and no project access beyond the diff output you paste after it.

**Role:** `bmad-review-adversarial-general`
**Story spec:** `_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md`
**Baseline commit:** `842ce7d64b5037b069ae36a4d6c97e04be3c52f7`

## Constraints

- Review only what the diff proves.
- Do not assume intent beyond the changed text.
- Return findings only. No summary unless there are zero findings.

## Diff Reproduction

Run these commands locally and paste the combined output after this prompt:

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

## Output Format

For each finding, use one flat bullet in this format:

- `severity` | `category_suggestion` | `file:line` | finding

Where `category_suggestion` is one of `intent_gap`, `bad_spec`, `patch`, `defer`, or `reject`.

If there are no real findings, say `No findings.`
