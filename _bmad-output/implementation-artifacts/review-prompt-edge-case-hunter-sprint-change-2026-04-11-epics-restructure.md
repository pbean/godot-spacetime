# Edge Case Hunter Review Prompt

Use this prompt in a separate session with read access to the repository. Do not rely on prior conversation context.

**Role:** `bmad-review-edge-case-hunter`
**Story spec:** `_bmad-output/implementation-artifacts/spec-sprint-change-2026-04-11-epics-restructure.md`
**Baseline commit:** `f44cda3c5c7a01c626f3c41213f334b6944039be`

## Review Goal

Inspect the diff and then explore the repository only where needed to find boundary-condition problems, traceability holes, sequencing mistakes, or acceptance-criteria gaps introduced or exposed by this story.

## Inputs

- Primary changed artifact: `_bmad-output/planning-artifacts/epics.md`
- Approved change source: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-11.md`
- Readiness trigger: `_bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.md`
- Story spec: `_bmad-output/implementation-artifacts/spec-sprint-change-2026-04-11-epics-restructure.md`

## Diff Reproduction

Run these commands locally and review the combined output:

```bash
git diff --no-ext-diff -- _bmad-output/planning-artifacts/epics.md _bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.md _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-11.md
git diff --no-index -- /dev/null _bmad-output/implementation-artifacts/spec-sprint-change-2026-04-11-epics-restructure.md
git diff --no-index -- /dev/null _bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.pre-rerun-132128.md
git diff --no-index -- /dev/null _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-11.pre-rerun-140138.md
```

## Constraints

- The worktree already contained unrelated planning-artifact edits when this story began. Do not blame those edits on this story unless the current change clearly caused or depended on them.
- Prioritize hidden sequencing defects, renumbering mismatches, FR traceability drift, and acceptance criteria that still lack objective evidence.
- Return findings only. No recap unless there are zero findings.

## Output Format

- `severity` | `category_suggestion` | `file:line` | finding

Where `category_suggestion` is one of `intent_gap`, `bad_spec`, `patch`, `defer`, or `reject`.

If there are no real findings, say `No findings.`
