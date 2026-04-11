---
title: 'TEA Test Design -> BMAD Handoff Document'
version: '1.0'
workflowType: 'testarch-test-design-handoff'
inputDocuments:
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/test-artifacts/test-design-architecture.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/test-artifacts/test-design-qa.md'
sourceWorkflow: 'testarch-test-design'
generatedBy: 'TEA Master Test Architect'
generatedAt: '2026-04-09T19:53:16-07:00'
projectName: 'godot-spacetime'
---

# TEA -> BMAD Integration Handoff

## Purpose

This document bridges TEA's system-level test design outputs with BMAD epic/story decomposition. It identifies the risks, acceptance criteria, and instrumentation requirements that must flow into implementation planning so quality is not deferred until after the public contract hardens.

## TEA Artifacts Inventory

| Artifact | Path | BMAD Integration Point |
| -------- | ---- | ---------------------- |
| Test Design Document | `/home/pinkyd/dev/godot-spacetime/_bmad-output/test-artifacts/test-design-architecture.md` | Architecture blockers, risk ownership, release gates |
| Test Design Document | `/home/pinkyd/dev/godot-spacetime/_bmad-output/test-artifacts/test-design-qa.md` | Story acceptance criteria, test-level guidance, scenario priorities |
| Risk Assessment | Embedded in both documents | Epic risk classification and sequencing |
| Coverage Strategy | Embedded in QA document | Story-level test requirements and automation scope |

## Epic-Level Integration Guidance

### Risk References

The following risks should be represented explicitly at epic level:

- **R-001 / TECH / 9**: deterministic runtime tick ownership and ordered callback delivery
- **R-002 / DATA / 6**: cache correctness during subscription replacement and reconnect
- **R-003 / SEC / 6**: explicit token-store behavior and secret-redaction guarantees
- **R-004 / TECH / 9**: codegen and compatibility drift must fail before release, not after
- **R-006 / OPS / 6**: hosted WSS/TLS/auth parity must be validated before claiming support
- **R-007 / TECH / 6**: public API must stay runtime-neutral across `.NET` and future `GDScript`
- **R-010 / PERF / 6**: event/update throughput must stay inside the frame-budget envelope

### Quality Gates

- No implementation story that touches runtime lifecycle closes without deterministic local automation for that boundary.
- Stories affecting auth or persistence must include redaction and invalid-token behavior in acceptance criteria.
- Stories affecting codegen, compatibility, or release packaging must update the matrix and regeneration/install smoke gates.
- Hosted-support stories are not done until the same public settings model passes both local and hosted smoke.

## Story-Level Integration Guidance

### P0/P1 Test Scenarios -> Story Acceptance Criteria

- **Connection service stories:** must expose a deterministic test seam for advancing `FrameTick()` and asserting lifecycle ordering.
- **Subscription/cache stories:** must prove no stale or duplicated cache observations during replacement or reconnect.
- **Auth/token stories:** must define save/load/clear behavior, corrupt-token fallback, and log-redaction behavior.
- **Reducer/runtime interaction stories:** must differentiate success, recoverable failure, and disconnect scenarios with typed results/events.
- **Codegen and release stories:** must fail fast on schema drift and clean-room install regressions.
- **Docs/sample stories:** must validate quickstart, troubleshooting, and sample bootstrap against the implemented public contract.

### Data-TestId Requirements

This SDK is not DOM-centric. Instead of HTML `data-testid` attributes, implementation stories should provide stable test instrumentation through:

- Stable public signal names and event payload contracts
- Deterministic fixture-module names and scenario IDs
- Explicit log-category IDs for lifecycle, auth, subscription, and reducer paths
- Configurable settings/resource keys that can be asserted in tests without reflection hacks
- Public harness hooks for advancing runtime state in test environments

## Risk-to-Story Mapping

| Risk ID | Category | P×I | Recommended Story/Epic | Test Level |
| ------- | -------- | --- | ---------------------- | ---------- |
| R-001 | TECH | 3x3 | Runtime core / connection owner epic | Unit + Component |
| R-002 | DATA | 2x3 | Subscription registry and cache adapter epic | API / Integration |
| R-003 | SEC | 2x3 | Auth and token-store epic | Component |
| R-004 | TECH | 3x3 | Codegen and compatibility pipeline epic | Unit + Release smoke |
| R-006 | OPS | 2x3 | Hosted parity and release validation epic | E2E / Environment smoke |
| R-007 | TECH | 2x3 | Public API and multi-runtime contract epic | Unit / Contract |
| R-010 | PERF | 2x3 | Performance and event-throughput hardening epic | Component / Benchmark |

## Recommended BMAD -> TEA Workflow Sequence

1. **TEA Test Design** (`TD`) -> produces architecture, QA, and handoff artifacts
2. **BMAD Create Epics & Stories** -> consumes this handoff and embeds quality requirements
3. **TEA ATDD** (`AT`) -> generates failing acceptance tests for the highest-priority stories
4. **BMAD Implementation** -> implements with deterministic test seams and contract-safe APIs
5. **TEA Automate** (`TA`) -> expands into the planned unit/component/API/E2E suite
6. **TEA Trace** (`TR`) -> validates coverage completeness against risks and requirements

## Phase Transition Quality Gates

| From Phase | To Phase | Gate Criteria |
| ---------- | -------- | ------------- |
| Test Design | Epic/Story Creation | All score >=6 risks have mitigation owner and story destination |
| Epic/Story Creation | ATDD | Stories carry the required acceptance criteria and instrumentation hooks |
| ATDD | Implementation | Failing acceptance tests exist for the selected P0/P1 scenarios |
| Implementation | Test Automation | Deterministic local automation passes for the story boundary |
| Test Automation | Release | Supported version pair, clean-room install smoke, and hosted claims are validated |

