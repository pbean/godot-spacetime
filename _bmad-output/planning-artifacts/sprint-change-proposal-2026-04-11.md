---
changeDate: '2026-04-11'
project: 'godot-spacetime'
mode: 'batch'
changeTrigger: 'Implementation-readiness review identified late foundational stories in Epic 6, an oversized Epic 1 Story 1.3, an oversized Epic 6 Story 6.6, and weak objective evidence in some release and continuity acceptance criteria.'
scopeClassification: 'Moderate'
approvalStatus: 'approved'
approvedAt: '2026-04-11'
approvalEvidence:
  - 'Human approval recorded in the Codex planning checkpoint on 2026-04-11 before backlog edits were applied.'
handoffRecipients:
  - 'Backlog owner / planner'
  - 'Developer'
artifactsProposedForUpdate:
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/epics.md'
artifactsUpdatedAfterApproval:
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/epics.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.md'
artifactsReviewed:
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/prd.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/epics.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/architecture.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/ux-design-specification.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.md'
---

# Sprint Change Proposal

## 1. Issue Summary

This change proposal is triggered by the implementation-readiness assessment dated 2026-04-11. The assessment found that the planning set is close to implementation-ready, but the backlog still contains one sequencing defect and two story-sizing defects that are likely to create churn if sprint execution starts as written.

The concrete triggers are:

- `Epic 6`, `Stories 6.1-6.3` define runtime-neutral public-contract and adapter-boundary work that earlier implementation stories already depend on implicitly.
- `Epic 1`, `Story 1.3` combines core code generation, regeneration behavior, developer explanation, automation parity, and editor validation UX in one story.
- `Epic 6`, `Story 6.6` combines release-candidate validation, publish gating, and release publication in one story.
- Some Epic 6 continuity and release stories describe the intended outcome, but not always the concrete artifact or verification evidence that proves completion.

This is not a product-direction or MVP-scope change. It is a backlog-structure correction triggered before implementation begins.

## 2. Checklist Status

### Section 1: Understand the Trigger and Context

- `[x] 1.1` Triggering planning items identified: `Story 1.3`, `Stories 6.1-6.3`, and `Story 6.6`.
- `[x] 1.2` Core problem defined: backlog sequencing and story sizing do not match the architectural dependency structure.
- `[x] 1.3` Evidence captured from `implementation-readiness-report-2026-04-11.md` plus direct review of `epics.md`, `prd.md`, `architecture.md`, and `ux-design-specification.md`.

### Section 2: Epic Impact Assessment

- `[x] 2.1` Current impacted epics reviewed: `Epic 1` and `Epic 6`.
- `[x] 2.2` Epic-level changes defined: front-load the runtime-neutral foundation work into `Epic 1`, split the oversized stories, and narrow `Epic 6` to release and support operations.
- `[x] 2.3` Remaining epics reviewed for downstream impact; `Epics 2-5` remain structurally valid.
- `[x] 2.4` No new epic is required and no existing epic is invalidated.
- `[x] 2.5` Story order and effective implementation priority must change inside `Epic 1` and `Epic 6`; overall epic count stays the same.

### Section 3: Artifact Conflict and Impact Analysis

- `[x] 3.1` PRD reviewed: no PRD conflict found. The PRD already supports the proposed sequencing and scope.
- `[x] 3.2` Architecture reviewed: no architecture rewrite required. The architecture already expects early public-boundary discipline and release gating.
- `[x] 3.3` UX reviewed: no UX rewrite required. The UX commitments remain valid after the backlog restructuring.
- `[x] 3.4` Secondary artifact impact noted: sprint tracking will need regeneration after `epics.md` changes. No `sprint-status.yaml` exists yet.

### Section 4: Path Forward Evaluation

- `[x] 4.1` Option 1 Direct Adjustment: viable, medium effort, low-to-medium risk.
- `[ ] 4.2` Option 2 Potential Rollback: not viable; implementation has not started and there is nothing meaningful to roll back.
- `[ ] 4.3` Option 3 PRD MVP Review: not viable; MVP goals remain intact.
- `[x] 4.4` Selected approach: Option 1 Direct Adjustment.

### Section 5: Sprint Change Proposal Components

- `[x] 5.1` Issue summary documented.
- `[x] 5.2` Epic impact and artifact adjustment needs documented.
- `[x] 5.3` Recommended path forward with rationale documented.
- `[x] 5.4` MVP impact and action plan documented.
- `[x] 5.5` Handoff plan documented.

### Section 6: Final Review and Handoff

- `[x] 6.1` Checklist reviewed for completeness.
- `[x] 6.2` Proposal reviewed for internal consistency.
- `[x] 6.3` User approved the Sprint Change Proposal for implementation.
- `[N/A] 6.4` `sprint-status.yaml` update skipped because no sprint status artifact exists in this repository yet.
- `[x] 6.5` Final handoff confirmed for backlog owner / planner and developer execution.

## 3. Impact Analysis

### Epic Impact

- `Epic 1` must absorb the runtime-neutral foundation work currently parked in `Epic 6` so the first implementation epic reflects the real dependency order.
- `Epic 1` needs one additional split to turn the current `Story 1.3` into smaller, independently completable slices.
- `Epic 6` should stop carrying foundational architecture work and instead focus on compatibility, packaging, validation, publication, and release communication.
- `Epic 6` needs one additional split to separate validation from publication.

### Artifact Conflict Assessment

- `prd.md`: no direct edit required.
- `architecture.md`: no direct edit required; the backlog should be brought into alignment with the existing architecture, not the other way around.
- `ux-design-specification.md`: no direct edit required.
- `epics.md`: direct edit required. The defects are contained in epic/story sequencing, scope, FR coverage grouping, and acceptance-criteria evidence.

### Technical Impact

- No MVP scope change.
- No requirement removal.
- No code rollback.
- Moderate backlog restructuring and renumbering inside `Epic 1` and `Epic 6`.
- Sprint planning artifacts will need regeneration after the corrected `epics.md` is approved.

## 4. Recommended Approach

### Option Review

- `Option 1: Direct Adjustment`
  - Effort: Medium
  - Risk: Low to Medium
  - Result: viable
- `Option 2: Potential Rollback`
  - Effort: High
  - Risk: Low
  - Result: not viable
- `Option 3: PRD MVP Review`
  - Effort: Medium
  - Risk: Medium
  - Result: not viable

### Selected Path

Apply a targeted backlog correction in place:

1. Move the runtime-neutral foundation stories from `Epic 6` into `Epic 1`.
2. Split the current `Story 1.3` into smaller implementation slices.
3. Split the current `Story 6.6` into validation and publication stories.
4. Tighten acceptance criteria so the continuity and release stories produce objective proof of completion.

### Why This Path

The architecture and requirements are already coherent. The backlog is the only artifact out of phase with that structure. Fixing the backlog directly is the shortest path to an implementable sprint plan.

## 5. Detailed Change Proposals

### Epics Document Changes

#### Epic List and FR Coverage Realignment

**Artifact:** `epics.md`  
**Section:** `FR Coverage Map` and `Epic List`

**OLD**

```md
### Epic 1: Install, Generate, and Reach a First Working Connection
**FRs covered:** FR1, FR2, FR3, FR4, FR6, FR7, FR8, FR9, FR11, FR12, FR13

### Epic 6: Publish a Trusted SDK and Evolve It Safely
**FRs covered:** FR10, FR33, FR34, FR35, FR36, FR37, FR38, FR39, FR40, FR41, FR42
```

**NEW**

```md
### Epic 1: Install, Establish the SDK Boundary, and Reach a First Working Connection
**FRs covered:** FR1, FR2, FR3, FR4, FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR39, FR40, FR41, FR42

### Epic 6: Publish and Operate a Trusted SDK Release
**FRs covered:** FR33, FR34, FR35, FR36, FR37, FR38
```

**Rationale:** The runtime-neutral public contract and adapter-boundary work are foundational to the first implementation epic, not late-stage release work.

#### Epic 1 Restructure

**Artifact:** `epics.md`  
**Section:** `Epic 1`

**OLD**

```md
1.1 Scaffold the Supported Godot Plugin Foundation
1.2 Establish Baseline Build and Workflow Validation Early
1.3 Generate and Regenerate Typed Module Bindings
1.4 Detect Binding and Schema Compatibility Problems Early
1.5 Configure and Open a First Connection from Godot
1.6 Validate First Setup Through a Quickstart Path
```

**NEW**

```md
1.1 Scaffold the Supported Godot Plugin Foundation
1.2 Establish Baseline Build and Workflow Validation Early
1.3 Define Runtime-Neutral Public SDK Concepts and Terminology
1.4 Isolate the `.NET` Runtime Adapter Behind Internal Boundaries
1.5 Verify Future `GDScript` Continuity in Structure and Contracts
1.6 Generate and Regenerate Typed Module Bindings
1.7 Explain Generated Schema Concepts and Validate Code Generation State
1.8 Detect Binding and Schema Compatibility Problems Early
1.9 Configure and Open a First Connection from Godot
1.10 Validate First Setup Through a Quickstart Path
```

**Rationale:** This removes the hidden dependency on late `Epic 6` architecture stories and makes the old `Story 1.3` small enough to execute predictably.

#### Epic 1 Story Moves and Splits

**Artifact:** `epics.md`  
**Section:** `Epic 1` story bodies

**OLD**

```md
Story 1.3: Generate and Regenerate Typed Module Bindings
Implements: FR6, FR7, FR8, UX1, UX2, UX3, NFR23, NFR24

Story 6.1: Define Runtime-Neutral Public SDK Concepts and Terminology
Implements: FR10, FR41

Story 6.2: Isolate the `.NET` Runtime Adapter Behind Internal Boundaries
Implements: FR39, FR42

Story 6.3: Verify Future `GDScript` Continuity in Structure and Contracts
Implements: FR40, FR42
```

**NEW**

```md
Story 1.3: Define Runtime-Neutral Public SDK Concepts and Terminology
Implements: FR10, FR41

Story 1.4: Isolate the `.NET` Runtime Adapter Behind Internal Boundaries
Implements: FR39, FR42

Story 1.5: Verify Future `GDScript` Continuity in Structure and Contracts
Implements: FR40, FR42

Story 1.6: Generate and Regenerate Typed Module Bindings
Implements: FR6, FR7

Story 1.7: Explain Generated Schema Concepts and Validate Code Generation State
Implements: FR8, UX1, UX2, UX3, NFR23, NFR24
```

**Rationale:** Story ownership becomes sequential and explicit: define the product contract first, then build the implementation boundary, then deliver code generation in smaller slices.

#### Acceptance Criteria Tightening for Moved Foundation Stories

**Artifact:** `epics.md`  
**Section:** moved continuity and boundary stories

**OLD**

- Acceptance criteria described intended continuity and documentation outcomes, but not always the evidence artifact or objective proof of completion.

**NEW**

- `Story 1.3` should require a named public-concepts reference, such as `docs/runtime-boundaries.md` or equivalent, that uses the same terminology as the public API and sample guidance.
- `Story 1.4` should require that direct `SpacetimeDB.ClientSDK` references remain confined to `Internal/Platform/DotNet/` in the shipping addon code.
- `Story 1.5` should require a documented extension seam and repository location for a later native `GDScript` runtime.

**Rationale:** These stories become easier to verify and less vulnerable to subjective interpretation.

#### Epic 6 Restructure

**Artifact:** `epics.md`  
**Section:** `Epic 6`

**OLD**

```md
6.1 Define Runtime-Neutral Public SDK Concepts and Terminology
6.2 Isolate the `.NET` Runtime Adapter Behind Internal Boundaries
6.3 Verify Future `GDScript` Continuity in Structure and Contracts
6.4 Publish the Canonical Compatibility Matrix and Support Policy
6.5 Package Reproducible Versioned Release Candidates
6.6 Validate the Supported Workflow and Publish the Release
6.7 Communicate Release Changes and Preserve Product Continuity
```

**NEW**

```md
6.1 Publish the Canonical Compatibility Matrix and Support Policy
6.2 Package Reproducible Versioned Release Candidates
6.3 Validate Release Candidates Against the Supported Workflow
6.4 Publish Approved SDK Releases for External Use
6.5 Communicate Release Changes and Maintain Support Continuity
```

**Rationale:** `Epic 6` should focus on release and support operations after the core runtime boundary is already established.

#### Story 6.6 Split

**Artifact:** `epics.md`  
**Section:** `Epic 6` story bodies

**OLD**

```md
Story 6.6: Validate the Supported Workflow and Publish the Release
Implements: FR33, FR35, FR36
```

**NEW**

```md
Story 6.3: Validate Release Candidates Against the Supported Workflow
Implements: FR35, FR36

Story 6.4: Publish Approved SDK Releases for External Use
Implements: FR33
```

**Rationale:** Validation and publication are distinct gates. Splitting them improves testability and keeps the release path sequential.

#### Acceptance Criteria Tightening for Release Stories

**Artifact:** `epics.md`  
**Section:** `Epic 6` release stories

**OLD**

- Release validation and release publication were partially combined, and evidence artifacts were implied more than specified.

**NEW**

- `Story 6.3` should require a concrete validation output or report covering build validation, generated-binding checks, sample smoke coverage, packaging checks, and compatibility-target verification.
- `Story 6.4` should require publication of the exact validated release-candidate payload, not a newly rebuilt artifact.
- `Story 6.5` should require release notes or change-log outputs that reference compatibility impact and any required adopter action.

**Rationale:** These changes make release completion auditable and reduce ambiguity at publish time.

### PRD, Architecture, and UX Changes

No direct edits are recommended for `prd.md`, `architecture.md`, or `ux-design-specification.md`. Those artifacts already support the corrected structure.

## 6. PRD MVP Impact and Action Plan

### MVP Impact

The MVP is unchanged. This proposal restructures the backlog so the existing MVP can be implemented with less rework risk.

### High-Level Action Plan

1. Update `epics.md` with the new `Epic 1` and `Epic 6` structure.
2. Regenerate the FR coverage map and epic summaries inside `epics.md` to match the moved and split stories.
3. Regenerate sprint planning or sprint status artifacts after the backlog is approved.
4. Re-run implementation readiness after the epics update if you want a post-correction verification pass before coding starts.

## 7. Implementation Handoff

### Scope Classification

`Moderate`

### Handoff Recipients

- `Backlog owner / planner`: update `epics.md` and regenerate sprint-planning artifacts.
- `Developer`: implement only after the corrected story sequence is approved and sprint planning is regenerated.

### Responsibilities

- Backlog owner / planner:
  - apply the `epics.md` restructuring,
  - regenerate sprint planning or sprint status artifacts,
  - preserve renumbering consistency across story references.
- Developer:
  - treat the moved foundation stories as prerequisites for subsequent Epic 1 implementation,
  - treat release publication as gated by prior validation output,
  - avoid starting coding from the pre-correction story order.

### Success Criteria

- No foundational runtime-boundary story sits behind implementation work that depends on it.
- No oversized story in `Epic 1` or `Epic 6` bundles multiple implementation phases into one backlog item.
- Release publication is explicitly downstream of release-candidate validation.
- Sprint planning can be generated from the corrected backlog without hidden sequencing defects.

## 8. Execution Summary

- Issue addressed: late foundational stories plus oversized implementation and release stories
- Change scope: Moderate
- Artifacts proposed for update: `epics.md`
- Routed to: backlog owner/planner, then developer after backlog regeneration

## 9. Approval and Final Handoff

- Approval status: Approved
- Approval evidence: Human approval recorded in the Codex planning checkpoint on 2026-04-11 before backlog edits were applied
- Scope classification: Moderate
- Primary handoff: backlog owner / planner to update `epics.md` and regenerate sprint-planning artifacts
- Secondary handoff: developer to implement only after the corrected backlog and regenerated sprint plan are in place
- Sprint-status note: no `sprint-status.yaml` artifact exists in this repository, so no sprint-status file was updated

## 10. Execution Record

- Planning artifacts updated after approval: `epics.md` was corrected and `implementation-readiness-report-2026-04-11.md` was rerun against the corrected backlog.
- Consistency status: the proposal, epics, and readiness assessment now reflect the same corrected Epic 1 and Epic 6 structure.
