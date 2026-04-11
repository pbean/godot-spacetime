---
changeDate: '2026-04-10'
project: 'godot-spacetime'
mode: 'batch'
changeTrigger: 'Implementation-readiness review identified UX scope drift and story-quality issues in the planning artifacts.'
scopeClassification: 'Moderate'
artifactsUpdated:
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/prd.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/architecture.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/epics.md'
---

# Sprint Change Proposal

## 1. Issue Summary

The implementation-readiness assessment dated 2026-04-10 found that the planning set had drifted after `ux-design-specification.md` was added. The runtime concepts were still broadly aligned, but the planning artifacts no longer agreed on which editor/plugin surfaces were part of MVP, who owned those surfaces architecturally, or how they were represented in stories.

The most visible triggers were:

- the epics document still saying no standalone UX document existed
- old `Story 5.1` attempting to cover the entire sample workflow in one story
- old `Story 6.1` combining public contract definition, `.NET` isolation, and future-runtime continuity into one oversized story
- baseline CI/build/codegen validation appearing only near the end of the plan

Evidence came from the readiness report plus direct comparison of `prd.md`, `architecture.md`, `epics.md`, and `ux-design-specification.md`.

## 2. Checklist Status

### Section 1: Understand the Trigger and Context

- `[x] 1.1` Triggering planning items identified: Epic 1 first-run setup stories, old Story 5.1, and old Story 6.1.
- `[x] 1.2` Core problem defined: planning drift caused by a new UX artifact plus oversized and weakly testable stories.
- `[x] 1.3` Evidence captured from `implementation-readiness-report-2026-04-10.md`.

### Section 2: Epic Impact Assessment

- `[x] 2.1` Current impacted epics reviewed: Epics 1, 2, 5, and 6 required direct change; Epics 3 and 4 needed minor acceptance-criteria tightening.
- `[x] 2.2` Epic-level changes defined: explicit UX scope added to Epic 1 and Epic 2 stories; sample and runtime-neutral contract work split into smaller stories.
- `[x] 2.3` Remaining epics reviewed for downstream impact.
- `[x] 2.4` No new epic required; existing epics could absorb the change cleanly.
- `[x] 2.5` Epic priority kept intact, but baseline validation was moved earlier into Epic 1.

### Section 3: Artifact Conflict and Impact Analysis

- `[x] 3.1` PRD reviewed and updated to make MVP editor/plugin scope explicit.
- `[x] 3.2` Architecture reviewed and updated to assign ownership and validation responsibilities for committed MVP plugin surfaces.
- `[x] 3.3` UX specification consumed directly; its MVP surfaces and post-MVP deferrals were mapped into planning artifacts.
- `[x] 3.4` Secondary artifact impact noted: no `sprint-status.yaml` exists yet, so sprint tracking could not be updated in-place.

### Section 4: Path Forward Evaluation

- `[x] 4.1` Option 1 Direct Adjustment: viable, medium effort, low-to-medium risk.
- `[ ] 4.2` Option 2 Potential Rollback: not viable; no completed implementation existed to roll back and rollback would not solve planning drift.
- `[x] 4.3` Option 3 PRD MVP Review: partially viable; a targeted MVP scope clarification was required, but a full PRD reset was unnecessary.
- `[x] 4.4` Selected approach: Hybrid leaning Direct Adjustment. Clarify MVP editor scope, update architecture ownership, and repair stories in place.

### Section 5: Sprint Change Proposal Components

- `[x] 5.1` Issue summary documented.
- `[x] 5.2` Epic and artifact adjustments documented.
- `[x] 5.3` Recommended path and rationale documented.
- `[x] 5.4` MVP impact and action plan documented.
- `[x] 5.5` Handoff plan documented.

### Section 6: Final Review and Handoff

- `[x] 6.1` Checklist reviewed for completeness.
- `[x] 6.2` Proposal reviewed for consistency with updated artifacts.
- `[x] 6.3` Batch execution assumed from the user request to reconcile artifacts now.
- `[N/A] 6.4` `sprint-status.yaml` update skipped because no sprint status artifact exists in this repository yet.

## 3. Impact Analysis

### Epic Impact

- `Epic 1` now includes an explicit early validation story and explicit MVP setup/validation/status UX coverage.
- `Epic 2` now maps auth-state and recovery UX into the session stories.
- `Epic 5` now splits the sample workflow into three implementable stories instead of one oversized story.
- `Epic 6` now splits runtime-neutral continuity into three independently testable stories and leaves release hardening as a separate concern.

### Artifact Conflicts Resolved

- `prd.md` now states which plugin/editor surfaces are MVP commitments and which remain post-MVP.
- `architecture.md` now lists the UX spec as an input, gives committed editor surfaces architectural owners, and adds validation responsibility for responsive/accessibility behavior.
- `epics.md` now consumes the UX artifact directly, introduces explicit UX/NFR requirements, and removes the stale claim that no standalone UX document existed.

### Technical Impact

- No product-scope rollback was required.
- The main implementation-sequencing change is moving baseline CI/build/codegen/version-consistency validation into Epic 1.
- Backlog/story identifiers changed in Epic 1, Epic 5, and Epic 6, so future sprint tracking should be generated from the revised `epics.md`.

## 4. Recommended Approach

### Option Review

- `Option 1: Direct Adjustment`
  - Effort: Medium
  - Risk: Low to Medium
  - Result: viable
- `Option 2: Potential Rollback`
  - Effort: High
  - Risk: Medium
  - Result: not viable
- `Option 3: PRD MVP Review`
  - Effort: Low to Medium
  - Risk: Low
  - Result: partially viable as a scoped clarification, not as a full replanning

### Selected Path

Use a hybrid of Option 1 and a targeted Option 3 adjustment:

1. Clarify the MVP editor/plugin commitment in the PRD.
2. Reflect that commitment in the architecture with explicit component ownership and validation rules.
3. Repair the epic/story breakdown in place by adding UX coverage, splitting oversized stories, tightening vague acceptance criteria, and moving baseline validation earlier.

### Why This Path

It resolves the real ambiguity without reopening the whole product definition. The core PRD and architecture were already strong. The failure was traceability and story quality, not product direction.

## 5. Detailed Change Proposals

### PRD Changes

**Artifact:** `prd.md`  
**Sections:** Product Scope, MVP Editor Workflow Scope, Implementation Considerations, MVP Feature Set, Non-Functional Requirements

**OLD**

- MVP scope referenced editor ergonomics only as a vague post-MVP idea.
- No explicit decision existed about which plugin/editor surfaces were committed for v1.
- No dedicated PRD-level quality requirements existed for editor-surface responsiveness or accessibility.

**NEW**

- Added an explicit MVP editor workflow scope covering setup/configuration forms, code generation validation, compatibility validation, connection/auth status, and recovery callouts.
- Deferred diagnostics/event-log and subscription/runtime-inspector surfaces to post-MVP unless they become blockers.
- Added `NFR23` and `NFR24` for editor-surface usability across panel widths and keyboard/non-color-only accessibility behavior.

**Rationale:** This removes scope ambiguity without widening the MVP.

### Architecture Changes

**Artifact:** `architecture.md`  
**Sections:** inputDocuments, Technical Constraints, Frontend Architecture, Infrastructure & Deployment, Decision Impact Analysis, Structure Patterns, Component Boundaries

**OLD**

- Architecture described editor surfaces only generically through Godot `Control` scenes and editor isolation.
- No owner directories or validation responsibilities were defined for UX-specified panels.
- CI/build/codegen validation remained late in the implementation sequence.

**NEW**

- Added the UX specification and readiness report as architecture inputs.
- Defined the committed MVP editor surface area and explicitly deferred broader diagnostics/runtime-inspector tooling.
- Assigned structure ownership through `Editor/Setup/`, `Editor/Codegen/`, `Editor/Compatibility/`, `Editor/Status/`, and `Editor/Shared/`.
- Added UX validation responsibilities for keyboard navigation, non-color-only status cues, and narrow/standard/wide panel behavior.
- Moved baseline validation earlier in the implementation sequence.

**Rationale:** The UX-defined surfaces now have architectural owners and quality gates instead of informal intent.

### Story Changes

#### Story 1.1 Acceptance Criteria Tightening

**OLD**

- Story 1.1 required a Godot `.NET` addon shell and version baseline, but did not explicitly require the repo-level `.sln` or official Godot scaffold flow.

**NEW**

- Story 1.1 now requires `godot-spacetime.sln` at repo root and the official Godot `.NET` plugin scaffold under `addons/<plugin_name>/` with `plugin.cfg` and a C# entrypoint.

**Rationale:** Prevents divergence from the chosen starter path.

#### New Story 1.2 for Early Validation

**OLD**

- Baseline CI/build/codegen/version-consistency validation was deferred to late release stories.

**NEW**

- Added `Story 1.2: Establish Baseline Build and Workflow Validation Early`.

**Rationale:** Greenfield work now gets feedback before multiple epics stack on top of an unvalidated foundation.

#### UX Coverage in Epic 1 and Epic 2

**OLD**

- First-run setup, code generation, compatibility, auth state, and recovery UX were not represented in stories even though the UX spec existed.

**NEW**

- Added UX and NFR traceability to Stories `1.3`, `1.4`, `1.5`, `1.6`, `2.2`, and `2.4`.
- Acceptance criteria now reference concrete status, validation, and recovery surfaces plus keyboard and panel-width usability expectations.

**Rationale:** Implementation cannot now claim story completion while ignoring the committed MVP workflow UX.

#### Old Story 5.1 Split

**OLD**

- `Story 5.1` covered install, code generation, connection, auth/token resume, subscriptions, cache reads, row updates, reducer invocation, and troubleshooting comparison in one story.

**NEW**

- `Story 5.1`: sample foundation for install, codegen, and first connection
- `Story 5.2`: auth/session resume and live subscription flow
- `Story 5.3`: reducer interaction and troubleshooting comparison paths

**Rationale:** The sample work is now sized for incremental delivery and validation.

#### Old Story 6.1 Split

**OLD**

- `Story 6.1` combined runtime-neutral terminology, `.NET` boundary isolation, and future `GDScript` continuity into one broad story.

**NEW**

- `Story 6.1`: runtime-neutral public concepts and terminology
- `Story 6.2`: `.NET` adapter isolation behind internal boundaries
- `Story 6.3`: explicit future `GDScript` continuity verification

**Rationale:** Each continuity concern is now independently reviewable and testable.

#### Acceptance Criteria Tightening in Runtime Stories

**OLD**

- Subscription replacement and reducer-result stories used vague language around continuity and recovery quality.

**NEW**

- `Story 3.4` now requires the previous subscription set to remain authoritative until replacement synchronizes or fails explicitly.
- `Story 4.2` now requires reducer results to identify the operation/invocation instance plus failure category and recovery/feedback path.

**Rationale:** These stories are now observable and testable instead of interpretive.

## 6. PRD MVP Impact and Action Plan

### MVP Impact

The MVP is still achievable without widening scope. The change is clarifying which UX-defined editor surfaces are committed and explicitly deferring broader diagnostics surfaces that would otherwise create planning ambiguity.

### Action Plan

1. Implement Epic 1 in the revised order: `1.1` foundation, `1.2` baseline validation, then the first-run workflow stories.
2. Use the revised Epic 5 sample breakdown to validate the supported path incrementally instead of waiting for one large end-to-end sample story.
3. Use the revised Epic 6 split to protect runtime neutrality without blocking release planning on a single cross-cutting mega-story.
4. Generate sprint tracking from the revised `epics.md` before implementation starts, since no `sprint-status.yaml` currently exists.
5. Re-run the implementation-readiness workflow after backlog/sprint status is regenerated.

## 7. Implementation Handoff

### Scope Classification

`Moderate`

### Handoff Recipients

- `Developer`: implement from the revised Epic 1 sequencing and updated story IDs.
- `Backlog owner / planner`: regenerate sprint tracking from the revised `epics.md`.

### Responsibilities

- Developer: start with Stories `1.1` and `1.2`, then proceed through the newly scoped setup and validation flow.
- Backlog owner / planner: regenerate implementation tracking so the new story IDs for Epics 1, 5, and 6 are reflected consistently.

### Success Criteria

- MVP editor/plugin scope is explicit and consistent across PRD, architecture, and epics.
- Story sizing is reasonable for single-implementation slices.
- Baseline validation is sequenced before deep runtime work.
- A fresh implementation-readiness pass no longer flags stale UX assumptions or oversized story scope.

## 8. Execution Summary

- Issue addressed: UX scope drift plus oversized and weakly testable stories
- Change scope: Moderate
- Artifacts modified: `prd.md`, `architecture.md`, `epics.md`
- Routed to: Developer plus backlog owner/planner

This proposal has already been applied to the planning artifacts in batch mode to match the user request to reconcile the planning set now.
