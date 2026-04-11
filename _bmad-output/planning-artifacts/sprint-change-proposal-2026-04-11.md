---
changeDate: '2026-04-11'
project: 'godot-spacetime'
mode: 'batch'
changeTrigger: 'Implementation-readiness review identified two forward dependencies and one incomplete starter-template story in the planning artifacts.'
scopeClassification: 'Moderate'
artifactsUpdated:
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/epics.md'
---

# Sprint Change Proposal

## 1. Issue Summary

The implementation-readiness assessment dated 2026-04-11 found that the planning set is broadly sound but still contains three story-level defects that would create execution ambiguity if implementation started as written.

The concrete triggers were:

- `Story 1.2` depended on a binding-generation validation flow that is only established in `Story 1.3`.
- `Story 6.5` assumed release-workflow validation had already passed even though that validation was defined in `Story 6.6`.
- `Story 1.1` did not explicitly capture dependency-restore and initial project-configuration expectations for the starter template.

Evidence came from `implementation-readiness-report-2026-04-11.md` plus direct review of `epics.md`, `prd.md`, `architecture.md`, and `ux-design-specification.md`.

## 2. Checklist Status

### Section 1: Understand the Trigger and Context

- `[x] 1.1` Triggering stories identified: `1.1`, `1.2`, `1.3`, `6.5`, and `6.6`.
- `[x] 1.2` Core problem defined: story sequencing and acceptance criteria drift, not a product-direction change.
- `[x] 1.3` Evidence captured from `implementation-readiness-report-2026-04-11.md`.

### Section 2: Epic Impact Assessment

- `[x] 2.1` Current impacted epics reviewed: `Epic 1` and `Epic 6` required direct change.
- `[x] 2.2` Epic-level changes defined: tighten `Story 1.1`, narrow `Story 1.2`, extend `Story 1.3`, and restructure the package/validate/publish flow across `Stories 6.5` and `6.6`.
- `[x] 2.3` Remaining epics reviewed for downstream impact; no additional epic changes required.
- `[x] 2.4` No new epic required and no epic is invalidated.
- `[x] 2.5` Epic order stays intact; only within-epic sequencing and gating semantics were corrected.

### Section 3: Artifact Conflict and Impact Analysis

- `[x] 3.1` PRD reviewed: no PRD conflict found. The issue was downstream interpretation of already-correct installation and release requirements.
- `[x] 3.2` Architecture reviewed: no architecture rewrite required. The current implementation sequence already expects early validation and release gating.
- `[x] 3.3` UX reviewed: no UX change required. The readiness issues are sequencing and starter-foundation completeness, not UI-surface scope.
- `[x] 3.4` Secondary artifact impact noted: no `sprint-status.yaml` exists yet, so sprint tracking cannot be updated in-place.

### Section 4: Path Forward Evaluation

- `[x] 4.1` Option 1 Direct Adjustment: viable, low effort, low risk.
- `[ ] 4.2` Option 2 Potential Rollback: not viable; there is no implementation state to roll back and rollback would not improve story sequencing.
- `[ ] 4.3` Option 3 PRD MVP Review: not needed; MVP scope remains intact.
- `[x] 4.4` Selected approach: Option 1 Direct Adjustment.

### Section 5: Sprint Change Proposal Components

- `[x] 5.1` Issue summary documented.
- `[x] 5.2` Epic impact and artifact adjustments documented.
- `[x] 5.3` Recommended path and rationale documented.
- `[x] 5.4` MVP impact and high-level action plan documented.
- `[x] 5.5` Handoff plan documented.

### Section 6: Final Review and Handoff

- `[x] 6.1` Checklist reviewed for completeness.
- `[x] 6.2` Proposal reviewed for consistency with the corrected backlog.
- `[x] 6.3` Batch execution assumed from the user request to correct course from the readiness report now.
- `[N/A] 6.4` `sprint-status.yaml` update skipped because no sprint status artifact exists in this repository yet.

## 3. Impact Analysis

### Epic Impact

- `Epic 1` keeps its intended sequence, but `Story 1.2` no longer depends on `Story 1.3` to be complete.
- `Epic 1` starter-template expectations are now explicit enough to support implementation handoff.
- `Epic 6` now distinguishes candidate packaging from the later validate-and-publish gate, which restores sequential independence.

### Artifact Conflict Assessment

- `prd.md`: no direct edit required. The PRD already requires dependency expectations in installation guidance plus release validation before publication.
- `architecture.md`: no direct edit required. The architecture already calls for early validation and release gating against packaged artifacts.
- `ux-design-specification.md`: no direct edit required. No committed UX flow changes were introduced by this correction.
- `epics.md`: direct edit required because the defects were contained in story wording, sequencing assumptions, and traceability.

### Technical Impact

- No MVP scope change.
- No new epic or story ID was introduced.
- The backlog is safer to implement because each corrected story can now be completed using only prior stories plus its own scope.

## 4. Recommended Approach

### Option Review

- `Option 1: Direct Adjustment`
  - Effort: Low
  - Risk: Low
  - Result: viable
- `Option 2: Potential Rollback`
  - Effort: High
  - Risk: Low to Medium
  - Result: not viable
- `Option 3: PRD MVP Review`
  - Effort: Medium
  - Risk: Medium
  - Result: not viable for this issue

### Selected Path

Apply a narrow backlog correction in place:

1. Tighten `Story 1.1` so the starter-template foundation includes dependency and initial-configuration expectations.
2. Narrow `Story 1.2` to baseline build and repository-readiness validation instead of assuming completed code generation.
3. Extend `Story 1.3` so it establishes the repeatable code-generation command that later automation will call.
4. Split release packaging from validate-and-publish gating across `Stories 6.5` and `6.6` without renumbering the epic.

### Why This Path

The planning set does not need new requirements, a rewritten architecture, or an MVP reset. It only needs the story boundaries repaired so implementation can proceed without hidden forward dependencies.

## 5. Detailed Change Proposals

### Story Changes

#### Story 1.1 Starter-Template Completeness

**Story:** `1.1`  
**Section:** Acceptance Criteria

**OLD**

- The story required the repo-level solution, official Godot `.NET` addon shell, version baseline, and addon enablement.

**NEW**

- Added an acceptance criterion requiring repository bootstrap guidance to state the `.NET` dependency-restore expectation and any initial Godot project configuration needed before validation or code-generation workflows run.

**Rationale:** This closes the only readiness gap in the starter-template story without widening scope.

#### Story 1.2 Forward Dependency Removal

**Story:** `1.2`  
**Section:** Story description and Acceptance Criteria

**OLD**

- The story promised baseline automation for build, code generation, and support-version consistency.
- Its acceptance criteria required a documented binding-generation check against sample or fixture inputs.

**NEW**

- The story now covers build, repository readiness, and support-version consistency.
- Its acceptance criteria now verify the prerequisites, scripts, and fixture or module inputs needed for later binding-generation validation without requiring the code-generation workflow itself to exist yet.
- The extension point for later binding-generation and release-hardening checks remains explicit.

**Rationale:** `Story 1.2` is now independently completable in sequence while still protecting the early-validation goal from the architecture.

#### Story 1.3 Code-Generation Automation Hook

**Story:** `1.3`  
**Section:** Acceptance Criteria

**OLD**

- The story established generation, regeneration, schema-concept explanation, and UX validation for code generation.

**NEW**

- Added an acceptance criterion requiring the documented code-generation workflow to expose a repeatable command or script for sample or fixture module inputs so later automation can run the same path without manual repair.

**Rationale:** The code-generation story now owns the first fully real binding-generation path, which removes the forward dependency from `Story 1.2`.

#### Stories 6.5 and 6.6 Release Gating Repair

**Stories:** `6.5`, `6.6`  
**Section:** Titles, story descriptions, traceability, and Acceptance Criteria

**OLD**

- `Story 6.5` packaged and published a release only after the supported workflow checks had passed.
- `Story 6.6` defined those supported workflow checks afterward.

**NEW**

- `Story 6.5` now packages reproducible versioned candidate artifacts for validation and maps to `NFR12`.
- `Story 6.6` now validates the packaged candidate and uses passing validation as the gate to publish the official external release, while implementing `FR33`, `FR35`, and `FR36`.

**Rationale:** Release packaging, validation, and publication are now sequenced as candidate package -> validate -> publish, which matches the PRD and removes the forward dependency without introducing new story IDs.

### PRD, Architecture, and UX Changes

No direct edits are required in `prd.md`, `architecture.md`, or `ux-design-specification.md`. Those artifacts already support the corrected sequencing.

## 6. PRD MVP Impact and Action Plan

### MVP Impact

The MVP is unchanged. This correction makes the current MVP backlog implementable; it does not widen, reduce, or redirect scope.

### Action Plan

1. Start implementation with the corrected `Epic 1` sequence: `1.1`, then `1.2`, then `1.3`.
2. Treat `Story 1.3` as the first place where real binding-generation automation becomes executable.
3. In `Epic 6`, produce candidate artifacts in `6.5` and only publish the external release once `6.6` validation passes.
4. Generate sprint tracking from the corrected `epics.md` before implementation begins, since no sprint status file exists yet.
5. Re-run implementation readiness after sprint tracking exists or before coding starts if you want a clean post-correction verification pass.

## 7. Implementation Handoff

### Scope Classification

`Moderate`

### Handoff Recipients

- `Backlog owner / planner`: accept the corrected story boundaries and regenerate sprint tracking.
- `Developer`: implement from the corrected sequence and gating rules in `epics.md`.

### Responsibilities

- Backlog owner / planner: regenerate the sprint/backlog status view from the corrected `epics.md`.
- Developer: implement `Epic 1` and `Epic 6` using the new independence rules, especially the `1.2` -> `1.3` and `6.5` -> `6.6` handoffs.

### Success Criteria

- No story in `Epic 1` or `Epic 6` requires a later story to exist before it can be completed.
- The starter-template story states the dependency and configuration expectations needed for downstream work.
- Release publication is explicitly gated by supported-workflow validation rather than assumed ahead of it.

## 8. Execution Summary

- Issue addressed: story-level forward dependencies plus incomplete starter-template handoff criteria
- Change scope: Moderate
- Artifacts modified: `epics.md`
- Routed to: Backlog owner/planner plus developer

This proposal has already been applied to the planning artifacts in batch mode to match the user request to correct course from the readiness report now.
