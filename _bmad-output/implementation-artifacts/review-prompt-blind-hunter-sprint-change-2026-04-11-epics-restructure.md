# Blind Hunter Review Prompt

Use this prompt in a separate session with no conversation history and no project access beyond the diff output you paste after it.

**Role:** `bmad-review-adversarial-general`
**Story spec:** `_bmad-output/implementation-artifacts/spec-sprint-change-2026-04-11-epics-restructure.md`
**Baseline commit:** `f44cda3c5c7a01c626f3c41213f334b6944039be`

## Constraints

- Review only what the diff proves.
- Do not assume intent beyond the changed text.
- The worktree already contained unrelated planning-artifact edits when this story began. Findings that concern only those unrelated edits should be classified `reject` or `defer` unless the diff proves this story caused or exposed them.
- Return findings only. No summary unless there are zero findings.

## Diff Reproduction

Run these commands locally and paste the combined output after this prompt:

```bash
git diff --no-ext-diff -- _bmad-output/planning-artifacts/epics.md _bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.md _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-11.md
git diff --no-index -- /dev/null _bmad-output/implementation-artifacts/spec-sprint-change-2026-04-11-epics-restructure.md
git diff --no-index -- /dev/null _bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.pre-rerun-132128.md
git diff --no-index -- /dev/null _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-11.pre-rerun-140138.md
```

## Output Format

For each finding, use one flat bullet in this format:

- `severity` | `category_suggestion` | `file:line` | finding

Where `category_suggestion` is one of `intent_gap`, `bad_spec`, `patch`, `defer`, or `reject`.

If there are no real findings, say `No findings.`
