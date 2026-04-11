---
stepsCompleted:
  - 'step-01-detect-mode'
  - 'step-02-load-context'
  - 'step-03-risk-and-testability'
  - 'step-04-coverage-plan'
  - 'step-05-generate-output'
lastStep: 'step-05-generate-output'
lastSaved: '2026-04-09T19:53:16-07:00'
workflowType: 'testarch-test-design'
inputDocuments:
  - '/home/pinkyd/dev/godot-spacetime/_bmad/tea/config.yaml'
  - '/home/pinkyd/dev/godot-spacetime/_bmad/bmm/config.yaml'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/prd.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/architecture.md'
  - '/home/pinkyd/dev/godot-spacetime/.agents/skills/bmad-testarch-test-design/resources/knowledge/risk-governance.md'
  - '/home/pinkyd/dev/godot-spacetime/.agents/skills/bmad-testarch-test-design/resources/knowledge/probability-impact.md'
  - '/home/pinkyd/dev/godot-spacetime/.agents/skills/bmad-testarch-test-design/resources/knowledge/test-levels-framework.md'
  - '/home/pinkyd/dev/godot-spacetime/.agents/skills/bmad-testarch-test-design/resources/knowledge/test-quality.md'
  - '/home/pinkyd/dev/godot-spacetime/.agents/skills/bmad-testarch-test-design/resources/knowledge/adr-quality-readiness-checklist.md'
---

# Test Design for Architecture: godot-spacetime .NET MVP

**Purpose:** Architectural concerns, testability gaps, and NFR requirements for review by Architecture and Dev teams. Serves as a contract between QA and Engineering on what must be addressed before test development begins.

**Date:** 2026-04-09
**Author:** Pinkyd
**Status:** Architecture Review Pending
**Project:** godot-spacetime
**PRD Reference:** `/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/prd.md`
**ADR Reference:** `/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/architecture.md`

---

## Executive Summary

**Scope:** System-level test design for the v1 desktop-first Godot `.NET` SDK/plugin covering install, binding generation, connection lifecycle, auth/token resume, subscriptions, local cache access, reducer invocation, sample-backed docs, and release compatibility.

**Business Context** (from PRD):

- **Revenue/Impact:** Trust and adoption product. Success is a credible upstream-aligned Godot client path that supports the maintainer's real project and at least three external projects after release.
- **Problem:** There is no credible official Godot integration for SpacetimeDB, and current community options do not meet real project reliability expectations.
- **GA Launch:** First tagged public release after clean-room install smoke, sample-backed workflow validation, and explicit version-pair verification for Godot `4.6.2` and SpacetimeDB `2.1.0`.

**Architecture** (from architecture doc):

- **Key Decision 1:** Use official `SpacetimeDB.ClientSDK` `2.1.0` under a Godot `.NET` plugin shell targeting Godot `4.6.2` and `.NET 8+`.
- **Key Decision 2:** Keep a runtime-neutral Godot-facing public service API with one connection owner, main-thread `FrameTick()` advancement, and signal-based event dispatch.
- **Key Decision 3:** Treat generated bindings and subscription-backed local cache as the canonical client data model, with explicit opt-in token persistence.

**Expected Scale** (from architecture):

- Desktop-first v1, one long-lived connection per database session
- Local standalone SpacetimeDB for development and Maincloud-compatible hosted support
- Exact version-pair validation rather than broad "2.x" compatibility claims

**Risk Summary:**

- **Total risks:** 11
- **High-priority (>=6):** 7 risks requiring immediate mitigation
- **Test effort:** ~24 scenarios (~6-8 weeks for 1 QA, ~3-4 weeks for 2 QAs)

---

## Quick Guide

### 🚨 BLOCKERS - Team Must Decide (Can't Proceed Without)

**Pre-Implementation Critical Path** - These must be completed before QA can write stable integration tests:

1. **B-01: Deterministic Runtime Tick Seam** - Expose a test-controlled path for advancing `FrameTick()` and draining pending events/signals without frame-timing heuristics (recommended owner: SDK Runtime)
2. **B-02: Fixture Module Reset Contract** - Provide repeatable seed/reset tooling for local and hosted fixture modules covering auth, subscription, reducer, and schema-drift scenarios (recommended owner: Test Harness / Codegen)
3. **B-03: Token Store Contract Freeze** - Finalize `ITokenStore` save/load/clear/failure semantics and token-redaction requirements before auth-resume automation starts (recommended owner: Auth / SDK)
4. **B-04: Compatibility Gate Contract** - Make regeneration, version-matrix validation, clean-room install smoke, and sample-backed release verification first-class CI gates (recommended owner: Release / CI)

**What we need from team:** Complete these 4 items pre-implementation or test development is blocked.

---

### ⚠️ HIGH PRIORITY - Team Should Validate (We Provide Recommendation, You Approve)

1. **R-005: Bootstrap Path Freeze** - Choose the default `SpacetimeClient` bootstrap pattern before quickstart/sample freeze (Public API / Docs)
2. **R-006: Hosted Parity Validation** - Add local and hosted smoke coverage under the same public settings contract so WSS/TLS/OIDC failures are found before release (CI / Release)
3. **R-010: Frame Budget Envelope** - Define the acceptable event/update volume and the batching/diagnostic response if runtime dispatch exceeds budget (SDK Runtime)

**What we need from team:** Review recommendations and approve the chosen direction before sample and release stories harden around the wrong assumptions.

---

### 📋 INFO ONLY - Solutions Provided (Review, No Decisions Needed)

1. **Test strategy:** Bias coverage toward unit and component tests, with only five full end-to-end Godot/demo smoke flows.
2. **Tooling:** `dotnet test`, headless Godot demo scenes, standalone SpacetimeDB fixture modules, GitHub Actions, structured SDK logs.
3. **Tiered CI/CD:** PR = fast local functional suite, Nightly = hosted parity and matrix checks, Weekly = endurance/high-update validation.
4. **Coverage:** ~24 scenarios prioritized P0-P3 with explicit risk links.
5. **Quality gates:** P0 pass rate 100%, P1 pass rate >=95%, all risks score >=6 mitigated or waived, release-install and version-pair smoke green.

**What we need from team:** Review and acknowledge the proposed guardrails.

---

## For Architects and Devs - Open Topics

### Architecturally Significant Requirements

| ASR ID | Requirement | Status | Why it Matters |
| ------ | ----------- | ------ | -------------- |
| ASR-01 | Single connection owner plus main-thread `FrameTick()` advancement | ACTIONABLE | Determines whether runtime behavior can be deterministic and testable |
| ASR-02 | Runtime-neutral public contract across `.NET` and future `GDScript` | ACTIONABLE | Prevents v1 from creating a forced rewrite later |
| ASR-03 | Generated bindings are the canonical client contract | ACTIONABLE | Release gating must catch schema drift before users do |
| ASR-04 | Token persistence is explicit, opt-in, and redacted in logs | ACTIONABLE | Security and diagnosability depend on it |
| ASR-05 | Exact compatibility matrix with sample-backed release validation | ACTIONABLE | Trust and maintainability depend on precise support claims |
| ASR-06 | Signal-based event dispatch into Godot scene-safe consumers | FYI | The direction is sound; the test seam around it still needs definition |

### Risk Assessment

**Total risks identified:** 11 (7 high-priority score >=6, 3 medium, 1 low)

#### High-Priority Risks (Score >=6) - IMMEDIATE ATTENTION

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| **R-001** | **TECH** | `FrameTick()` ownership or callback delivery becomes nondeterministic, causing lifecycle and signal-order regressions | 3 | 3 | **9** | Single runtime owner plus deterministic test seam and ordered event assertions | SDK Runtime | Before runtime core merge |
| **R-002** | **DATA** | Overlap-first subscription replacement or reconnect leaves stale, gapped, or duplicated local cache state | 2 | 3 | **6** | Define subscription invariants and validate with fixture-module resubscribe/reconnect scenarios | SDK Runtime | Before subscription freeze |
| **R-003** | **SEC** | Token persistence or diagnostics leak JWTs, or invalid tokens are silently reused | 2 | 3 | **6** | Freeze `ITokenStore` semantics, redact secrets, and cover valid/expired/corrupt token paths | Auth / SDK | Before auth sample freeze |
| **R-004** | **TECH** | Schema and generated-binding drift reach release undetected, breaking the supported workflow | 3 | 3 | **9** | Regenerate bindings in CI, compile fixtures, and fail release on mismatch | Release / Codegen | Before first release candidate |
| **R-006** | **OPS** | Local standalone validation passes while hosted WSS/TLS/OIDC paths fail late | 2 | 3 | **6** | Add local + hosted parity smoke with shared fixture modules and config contracts | CI / Release | Before public beta |
| **R-007** | **TECH** | Public API becomes C#-specific and forces a future `GDScript` rewrite or documentation split | 2 | 3 | **6** | Review public types and docs against runtime-neutral contract before API freeze | Architecture / Public API | Before public API freeze |
| **R-010** | **PERF** | High-frequency row/reducer updates exceed frame budget or back up signal dispatch | 2 | 3 | **6** | Benchmark event throughput, batch per-frame work, and expose diagnostics | SDK Runtime | Before hosted load validation |

#### Medium-Priority Risks (Score 3-5)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-005 | BUS | Bootstrap path is not frozen, causing docs/sample/setup drift | 2 | 2 | 4 | Choose and document one default bootstrap contract early | Public API / Docs |
| R-008 | OPS | Release ZIP/package composition is incomplete, causing failed installs or missing companion assets | 2 | 2 | 4 | Add clean-room install-from-release job and artifact manifest validation | Release Eng |
| R-009 | BUS | Diagnostics and troubleshooting are too weak for self-serve recovery | 2 | 2 | 4 | Standardize typed errors, log categories, and troubleshooting workflows | SDK + Docs |

#### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |
| R-011 | BUS | Users infer unsupported web/platform coverage from vague messaging | 1 | 2 | 2 | Monitor and keep support matrix explicit |

#### Risk Category Legend

- **TECH**: Technical and architecture risks
- **SEC**: Security and secret-handling risks
- **PERF**: Performance and frame-budget risks
- **DATA**: Data integrity and cache-consistency risks
- **BUS**: Trust, onboarding, and product-credibility risks
- **OPS**: Release, environment, and operational validation risks

---

### Testability Concerns and Architectural Gaps

**🚨 ACTIONABLE CONCERNS - Architecture Team Must Address**

#### 1. Blockers to Fast Feedback (WHAT WE NEED FROM ARCHITECTURE)

| Concern | Impact | What Architecture Must Provide | Owner | Timeline |
| ------- | ------ | ------------------------------ | ----- | -------- |
| **No deterministic runtime test seam** | Flaky connection, subscription, and reducer assertions; hard to prove event ordering | A service-level path to advance ticks and drain events/signals without real frame waits | SDK Runtime | Before integration harness |
| **No fixture reset/seed contract** | Parallel tests and edge states cannot be reproduced safely | Fixture modules plus repeatable reset/seed tooling for local and hosted validation targets | Test Harness / Codegen | Before auth/subscription/reducer tests |
| **Token-store lifecycle not frozen** | Resume-path tests cannot cover valid, expired, or corrupt token behavior reliably | Final `ITokenStore` save/load/clear/failure semantics and log-redaction guarantees | Auth / SDK | Before auth docs/sample freeze |
| **Release compatibility gate not executable yet** | Core regressions can reach a tagged release | CI-owned regeneration, matrix, clean-room install, and sample-backed release smoke gates | Release / CI | Before first RC |

#### 2. Architectural Improvements Needed (WHAT SHOULD BE CHANGED)

1. **Freeze the consumer bootstrap contract**
   - **Current problem:** The architecture leaves manual setup, helper node, and autoload-assisted registration open.
   - **Required change:** Choose one default bootstrap path and document alternates only if supported.
   - **Impact if not fixed:** Quickstart, sample, and integration tests will drift from each other.
   - **Owner:** Public API / Docs
   - **Timeline:** Before quickstart and sample freeze

2. **Define subscription correctness invariants**
   - **Current problem:** "Overlap-first replacement" is named, but the invariant set is not yet precise.
   - **Required change:** Specify when a replacement is considered applied, how stale handles are prevented from publishing, and how reconnect handoff preserves cache state.
   - **Impact if not fixed:** Cache correctness remains hard to prove and easy to regress.
   - **Owner:** SDK Runtime
   - **Timeline:** Before subscription implementation freeze

3. **Codify hosted-environment parity**
   - **Current problem:** Local standalone is specified, hosted support is named, but their smoke path and auth differences are not codified.
   - **Required change:** Define local/hosted config fixtures, WSS/TLS assumptions, and hosted smoke cadence.
   - **Impact if not fixed:** Hosted failures will surface late, after local validation is already green.
   - **Owner:** CI / Release
   - **Timeline:** Before public beta

---

### Testability Assessment Summary

#### What Works Well

- ✅ `Public/` vs `Internal/` boundaries isolate the official SDK from the stable product contract.
- ✅ Single connection ownership, reconnect policy, and signal-based dispatch are called out early instead of being left emergent.
- ✅ Generated bindings, fixture modules, demo content, and release packaging all have explicit architectural homes.
- ✅ Token persistence is already treated as explicit and opt-in, which is the correct security baseline.

#### Accepted Trade-offs (No Action Required)

For the v1 `.NET` MVP, the following trade-offs are acceptable:

- **No web export support in v1** - This is consistent with the Godot `.NET` constraint and should stay explicit in release messaging.
- **No mandatory third-party telemetry in v1** - Structured SDK logs and sample-backed smoke validation are sufficient if they remain actionable.
- **Native `GDScript` runtime is deferred** - Acceptable as long as public concepts, docs, and naming stay runtime-neutral.

This is acceptable product scoping, not accidental technical debt, as long as the guardrails above are enforced.

---

### Risk Mitigation Plans (High-Priority Risks >=6)

#### R-001: Nondeterministic runtime tick or callback ordering (Score: 9) - BLOCKER

**Mitigation Strategy:**

1. Keep `DbConnection`, reconnect policy, and `FrameTick()` ownership inside one runtime service boundary.
2. Add a deterministic test hook that advances ticks and drains pending events/signals without hard waits.
3. Add unit and component tests for lifecycle ordering, reconnect transitions, and signal emission order.

**Owner:** SDK Runtime  
**Timeline:** Before runtime core merge  
**Status:** Planned  
**Verification:** Repeated local smoke runs produce identical connection-state and callback ordering for the same fixture scenario.

#### R-002: Subscription replacement or reconnect corrupts cache semantics (Score: 6) - HIGH

**Mitigation Strategy:**

1. Define subscription registry invariants for overlap-first replacement, stale-handle rejection, and reconnect handoff.
2. Build fixture modules with deterministic row versions and targeted resubscribe/reconnect scenarios.
3. Add integration checks that compare cache snapshots before and after replacement/reconnect.

**Owner:** SDK Runtime  
**Timeline:** Before subscription freeze  
**Status:** Planned  
**Verification:** Resubscribe and reconnect scenarios pass repeatedly with no duplicated or missing rows in the observed cache.

#### R-003: Token persistence or diagnostics leak secrets (Score: 6) - HIGH

**Mitigation Strategy:**

1. Freeze `ITokenStore` semantics for save, load, clear, and invalid-state handling.
2. Redact tokens and credential-bearing headers from all SDK log categories by default.
3. Add explicit valid, expired, corrupt, and cleared-token scenarios to sample and regression coverage.

**Owner:** Auth / SDK  
**Timeline:** Before auth sample freeze  
**Status:** Planned  
**Verification:** Resume-path coverage passes and captured logs contain no raw tokens or credential headers.

#### R-004: Binding/schema drift reaches release (Score: 9) - BLOCKER

**Mitigation Strategy:**

1. Regenerate bindings from fixture modules in CI on every API-affecting change.
2. Compile the sample and test fixtures against regenerated output.
3. Fail release workflows when the compatibility matrix, generation step, or sample smoke diverges.

**Owner:** Release / Codegen  
**Timeline:** Before first release candidate  
**Status:** Planned  
**Verification:** The supported Godot/SpacetimeDB version pair passes regeneration, compile, and clean-room install smoke before release publication.

#### R-006: Hosted validation diverges from local validation (Score: 6) - HIGH

**Mitigation Strategy:**

1. Maintain shared fixture modules and public settings for both local and hosted targets.
2. Run hosted WSS/TLS/auth smoke on a nightly or pre-release cadence.
3. Publish any environment-specific constraints in the compatibility matrix and troubleshooting docs.

**Owner:** CI / Release  
**Timeline:** Before public beta  
**Status:** Planned  
**Verification:** The same smoke suite passes against both local standalone and hosted targets for each claimed supported version pair.

#### R-007: Public API becomes runtime-specific instead of product-neutral (Score: 6) - HIGH

**Mitigation Strategy:**

1. Review every public API addition against the runtime-neutral contract before merge.
2. Keep direct `SpacetimeDB.ClientSDK` dependencies isolated to `Internal/Platform/DotNet`.
3. Treat docs, examples, and public names as shared product contract, not C# wrappers.

**Owner:** Architecture / Public API  
**Timeline:** Before public API freeze  
**Status:** Planned  
**Verification:** Public contract review shows no direct platform-SDK types exposed to consuming Godot code.

#### R-010: Update throughput exceeds frame budget (Score: 6) - HIGH

**Mitigation Strategy:**

1. Benchmark high-update fixture scenarios before release-hardening.
2. Add bounded batching or deferred dispatch when per-frame work exceeds the agreed envelope.
3. Emit verbose diagnostics for dropped, deferred, or coalesced work so performance failures are diagnosable.

**Owner:** SDK Runtime  
**Timeline:** Before hosted load validation  
**Status:** Planned  
**Verification:** High-update smoke stays inside the agreed frame budget without losing subscription or reducer event fidelity.

---

### Assumptions and Dependencies

#### Assumptions

1. Godot `4.6.2`, `.NET 8+`, and `SpacetimeDB.ClientSDK` `2.1.0` remain the exact MVP baseline during initial implementation.
2. Fixture modules under `spacetime/modules/` can serve as the authoritative regression harness for the supported workflows.
3. Local standalone and hosted validation targets are close enough conceptually that one public settings model can cover both.

#### Dependencies

1. Local standalone fixture module plus reset tooling - required by integration test implementation start
2. Hosted validation target with supported auth configuration - required by public beta and release candidate
3. Final bootstrap decision for `SpacetimeClient` - required by quickstart and sample freeze
4. Release pipeline with clean-room install smoke and matrix publication - required by first tagged release

#### Risks to Plan

- **Risk:** Upstream Godot or SpacetimeDB minor changes land during MVP.
  - **Impact:** Compatibility matrix, fixture modules, and release claims become stale.
  - **Contingency:** Re-run regeneration, sample smoke, and hosted/local parity before claiming support.

- **Risk:** Hosted validation access arrives late.
  - **Impact:** Release confidence is limited to local standalone validation.
  - **Contingency:** Do not claim hosted support until hosted smoke is green and documented.

---

**End of Architecture Document**

**Next Steps for Architecture Team:**

1. Approve the four blockers and assign owners.
2. Freeze bootstrap and token-store contracts before sample hardening.
3. Make compatibility and hosted-parity checks executable release gates.
4. Review public API additions against the runtime-neutral contract.

**Next Steps for QA Team:**

1. Use the companion QA document for the scenario matrix and execution plan.
2. Start by automating local fixture-module smoke after the runtime tick seam exists.
3. Defer hosted parity and high-update benchmarks until local deterministic coverage is stable.
