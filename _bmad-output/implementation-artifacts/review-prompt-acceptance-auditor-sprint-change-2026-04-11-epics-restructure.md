# Acceptance Auditor Review Prompt

Use this prompt in a separate session with read access to the repository. Do not rely on prior conversation context.

**Role:** Acceptance auditor
**Story spec:** `_bmad-output/implementation-artifacts/spec-sprint-change-2026-04-11-epics-restructure.md`
**Baseline commit:** `f44cda3c5c7a01c626f3c41213f334b6944039be`

## Review Goal

Check whether the implemented change satisfies the approved spec, especially the acceptance criteria, boundaries, and non-goals. The spec `context:` list is empty, so use only the spec plus repository files needed to verify compliance.

## Required Reads

Read these before judging the diff:

- `_bmad-output/implementation-artifacts/spec-sprint-change-2026-04-11-epics-restructure.md`
- `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-11.md`

## Diff Reproduction

Run these commands locally and review the combined output:

```bash
git diff --no-ext-diff -- _bmad-output/planning-artifacts/epics.md _bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.md _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-11.md
git diff --no-index -- /dev/null _bmad-output/implementation-artifacts/spec-sprint-change-2026-04-11-epics-restructure.md
git diff --no-index -- /dev/null _bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.pre-rerun-132128.md
git diff --no-index -- /dev/null _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-11.pre-rerun-140138.md
```

## Constraints

- Treat content inside the spec `<frozen-after-approval>` block as authoritative intent.
- Flag anything that violates the approved scope, misses a required acceptance criterion, or changes artifacts outside the allowed boundary.
- The worktree already contained unrelated planning-artifact edits when this story began. Findings about those edits should be `defer` or `reject` unless the current story caused or depended on them.
- Return findings only. No summary unless there are zero findings.

## Output Format

- `severity` | `category_suggestion` | `file:line` | finding

Where `category_suggestion` is one of `intent_gap`, `bad_spec`, `patch`, `defer`, or `reject`.

If there are no real findings, say `No findings.`
