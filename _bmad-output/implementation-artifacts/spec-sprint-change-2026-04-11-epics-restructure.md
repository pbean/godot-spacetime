---
title: 'Restructure epics for the approved sprint change proposal'
type: 'chore'
created: '2026-04-11'
status: 'done'
baseline_commit: 'f44cda3c5c7a01c626f3c41213f334b6944039be'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `_bmad-output/planning-artifacts/epics.md` still places runtime-boundary foundation stories late in Epic 6, keeps Epic 1 Story 1.3 and Epic 6 Story 6.6 oversized, and leaves some acceptance criteria too subjective to verify cleanly. That backlog structure conflicts with the approved 2026-04-11 sprint-change proposal and the architecture dependency order it is meant to support.

**Approach:** Update only `epics.md` so Epic 1 absorbs the runtime-neutral foundation work, the oversized Epic 1 and Epic 6 stories are split into smaller sequential stories, the FR coverage map and epic summaries match the new ownership, and the affected acceptance criteria name concrete evidence of completion. Leave PRD, architecture, UX, and unrelated planning artifacts unchanged.

## Boundaries & Constraints

**Always:** Preserve the approved scope and rationale from `sprint-change-proposal-2026-04-11.md`; keep acceptance criteria in Given/When/Then form; keep Epics 2-5 structurally unchanged; keep story numbering and FR ownership internally consistent everywhere inside `epics.md`; make the moved foundation stories clearly precede the implementation work that depends on them.

**Ask First:** If `epics.md` now contains newer manual edits that materially conflict with the approved proposal; if applying the approved restructuring would require direct edits to `prd.md`, `architecture.md`, or `ux-design-specification.md`; if any story move would force a requirement to change rather than just move or split.

**Never:** Change MVP scope, add new product requirements, rewrite unrelated epic content, start implementation code, or revert unrelated planning-artifact edits already present in the worktree.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Approved backlog correction | Approved `sprint-change-proposal-2026-04-11.md` and current `epics.md` structure | `epics.md` shows the revised Epic 1 and Epic 6 titles, FR coverage, story ordering, story splits, and tighter evidence-based acceptance criteria | N/A |
| Conflicting artifact drift | Current `epics.md` differs from the proposal in ways that make the approved edit ambiguous | Stop before speculative edits and surface the mismatch to the human | Do not rewrite around the conflict silently |

</frozen-after-approval>

## Code Map

- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-11.md` -- approved source of truth for the required Epic 1 and Epic 6 restructuring
- `_bmad-output/planning-artifacts/implementation-readiness-report-2026-04-11.md` -- source of the sequencing, sizing, and evidence problems the proposal resolves
- `_bmad-output/planning-artifacts/epics.md` -- target artifact whose FR map, epic summaries, story list, and acceptance criteria need correction

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/planning-artifacts/epics.md` -- realign the FR Coverage Map and Epic List so Epic 1 becomes the runtime-foundation-first epic and Epic 6 becomes the release-operations epic -- removes the hidden dependency on late foundational stories
- [x] `_bmad-output/planning-artifacts/epics.md` -- renumber and rewrite Epic 1 story headings and bodies so stories 1.3-1.5 move from old Epic 6, old Story 1.3 is split into new Stories 1.6 and 1.7, and later Epic 1 stories shift accordingly -- makes the early implementation path sequential and reviewable
- [x] `_bmad-output/planning-artifacts/epics.md` -- rewrite Epic 6 around compatibility, packaging, validation, publication, and release communication, including splitting old Story 6.6 into new Stories 6.3 and 6.4 -- makes release publication explicitly downstream of validation
- [x] `_bmad-output/planning-artifacts/epics.md` -- tighten acceptance criteria in moved foundation stories and revised release stories so each requires objective completion evidence named in the proposal -- reduces subjective interpretation during implementation readiness and sprint planning

**Acceptance Criteria:**
- Given the updated FR Coverage Map and Epic List, when Epic 1 and Epic 6 are reviewed, then Epic 1 owns FR1, FR2, FR3, FR4, FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR39, FR40, FR41, and FR42 with the revised runtime-boundary title, and Epic 6 owns only FR33, FR34, FR35, FR36, FR37, and FR38 with the revised release-operations title.
- Given the updated Epic 1 section, when the stories are read in order, then runtime-neutral concepts, `.NET` adapter isolation, and future `GDScript` continuity appear before binding generation, and the previous combined binding-generation story is split into a generation/regeneration story and a schema-concepts plus validation-state story.
- Given the updated Epic 6 section, when the release flow is read in order, then compatibility policy, candidate packaging, release-candidate validation, approved-release publication, and release communication are separate sequential stories, with publication depending on the validated candidate payload rather than a fresh rebuild.
- Given the affected moved and release stories, when acceptance criteria are reviewed, then they require concrete evidence such as a named runtime-boundaries reference, adapter-reference confinement to `Internal/Platform/DotNet/`, a documented future-runtime extension seam, a validation output/report for release checks, publication of the exact validated candidate payload, and release notes that call out compatibility impact or required adopter action.

## Spec Change Log

## Design Notes

This is an artifact-correction task, not a product-definition task. The edit should bring `epics.md` into line with the already-approved proposal and the existing architecture, not reinterpret them.

The riskiest failure mode is partial renumbering: updating story titles without also updating epic summaries, FR ownership, or acceptance-criteria evidence. Review should therefore follow the same top-down order as the document: FR map, epic list, Epic 1 body, then Epic 6 body.

## Verification

**Commands:**
- `rg -n "^### Epic 1:|^### Epic 6:|^### Story 1\\.|^### Story 6\\." _bmad-output/planning-artifacts/epics.md` -- expected: Epic 1 title and stories 1.1-1.10 appear in the new order, and Epic 6 title and stories 6.1-6.5 appear in the new order
- `rg -n "FR10: Epic 1|FR39: Epic 1|FR40: Epic 1|FR41: Epic 1|FR42: Epic 1|FR33: Epic 6|FR38: Epic 6" _bmad-output/planning-artifacts/epics.md` -- expected: FR ownership matches the approved realignment

**Manual checks (if no CLI):**
- Read the Epic 1 and Epic 6 summaries and confirm they describe the corrected scope rather than the pre-change scope.
- Read the acceptance criteria for Stories 1.3, 1.4, 1.5, 6.3, 6.4, and 6.5 and confirm each includes concrete verification evidence rather than only intent statements.

## Suggested Review Order

**Backlog Realignment**

- Start with the revised epic summaries to grasp the corrected backlog shape.
  [`epics.md:177`](../planning-artifacts/epics.md#L177)

- Confirm the FR ownership moves that pull runtime-boundary work into Epic 1.
  [`epics.md:141`](../planning-artifacts/epics.md#L141)

- See how Epic 6 is narrowed to release operations only.
  [`epics.md:202`](../planning-artifacts/epics.md#L202)

**Epic 1 Foundation Sequencing**

- Runtime-neutral product concepts now lead the implementation path.
  [`epics.md:246`](../planning-artifacts/epics.md#L246)

- Adapter isolation now names a concrete boundary artifact and location.
  [`epics.md:263`](../planning-artifacts/epics.md#L263)

- Future `GDScript` continuity now names a concrete repository seam.
  [`epics.md:279`](../planning-artifacts/epics.md#L279)

- Code generation is split down to generation and regeneration only.
  [`epics.md:295`](../planning-artifacts/epics.md#L295)

- Generated-schema explanation and validation state are split into their own story.
  [`epics.md:311`](../planning-artifacts/epics.md#L311)

**Release Gating**

- Compatibility policy now starts the release epic.
  [`epics.md:704`](../planning-artifacts/epics.md#L704)

- Candidate packaging is separated from later validation and publication.
  [`epics.md:720`](../planning-artifacts/epics.md#L720)

- Validation now produces the concrete gate consumed by publication.
  [`epics.md:736`](../planning-artifacts/epics.md#L736)

- Publication is tied to the exact validated candidate payload.
  [`epics.md:752`](../planning-artifacts/epics.md#L752)

- Release communication now records a repeatable checklist step.
  [`epics.md:768`](../planning-artifacts/epics.md#L768)

**Follow-up**

- Deferred work captures the out-of-scope auditability and report-regeneration tasks.
  [`deferred-work.md:1`](deferred-work.md#L1)
