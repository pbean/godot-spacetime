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
  - '/home/pinkyd/dev/godot-spacetime/.agents/skills/bmad-testarch-test-design/resources/knowledge/test-priorities-matrix.md'
  - '/home/pinkyd/dev/godot-spacetime/.agents/skills/bmad-testarch-test-design/resources/knowledge/test-quality.md'
  - '/home/pinkyd/dev/godot-spacetime/.agents/skills/bmad-testarch-test-design/resources/knowledge/data-factories.md'
  - '/home/pinkyd/dev/godot-spacetime/.agents/skills/bmad-testarch-test-design/resources/knowledge/fixture-architecture.md'
---

# Test Design for QA: godot-spacetime .NET MVP

**Purpose:** Test execution recipe for the QA team. Defines what to test, how to test it, and what QA needs from other teams.

**Date:** 2026-04-09
**Author:** Pinkyd
**Status:** Draft
**Project:** godot-spacetime

**Related:** See Architecture doc (`test-design-architecture.md`) for testability blockers and mitigation ownership.

---

## Executive Summary

**Scope:** QA planning for the v1 Godot `.NET` SDK/plugin workflow: install, code generation, connection, auth/token resume, subscriptions, local cache access, reducer invocation, docs/sample fidelity, and release compatibility.

**Risk Summary:**

- Total Risks: 11 (7 high-priority score >=6, 3 medium, 1 low)
- Critical Categories: TECH, DATA, SEC, OPS

**Coverage Summary:**

- P0 tests: ~6 (core workflow, auth safety, cache correctness, release gates)
- P1 tests: ~8 (connection lifecycle, hosted parity, docs recovery, public contract checks)
- P2 tests: ~6 (secondary recovery paths, compatibility messaging, docs alignment)
- P3 tests: ~4 (benchmarks, logging polish, support-messaging validation)
- **Total:** ~24 tests (~6-8 weeks with 1 QA)

---

## Not in Scope

**Components or systems explicitly excluded from this test plan:**

| Item | Reasoning | Mitigation |
| ---- | --------- | ---------- |
| **Native `GDScript` runtime delivery** | Post-MVP scope; v1 ships `.NET` only | Protect runtime-neutral public concepts and keep handoff guidance explicit |
| **Web export/browser runtime support** | Godot `.NET` v1 does not support web export | Keep support matrix and release messaging explicit |
| **Broad mobile platform certification** | Initial scope is desktop-first supported targets | Publish exact supported version and platform pairings only |
| **AssetLib distribution workflow** | GitHub Releases are the v1 install path | Validate clean-room release installs and revisit AssetLib later |

**Note:** These exclusions are deliberate product-scope decisions, not test omissions by accident.

---

## Dependencies & Test Blockers

**CRITICAL:** QA cannot proceed without these items from other teams.

### Backend/Architecture Dependencies (Pre-Implementation)

**Source:** See Architecture doc "Quick Guide" for full mitigation ownership

1. **Deterministic runtime tick seam** - SDK Runtime - Before integration harness
   - Expose service-level control over connection advancement, reconnect transitions, and event draining.
   - This blocks stable assertions for lifecycle, subscription, and reducer behavior.

2. **Fixture module reset and seeded-state workflow** - Test Harness / Codegen - Before integration suite
   - Provide local fixture modules plus repeatable reset tooling for auth, subscription, reducer, and schema-drift scenarios.
   - This blocks parallel-safe setup and realistic edge-case coverage.

3. **Token-store contract and failure semantics** - Auth / SDK - Before auth sample freeze
   - Finalize save, load, clear, corrupt-token, and expired-token behavior.
   - This blocks auth-resume automation and security validation.

4. **Release compatibility gate** - CI / Release - Before first release candidate
   - Provide regeneration checks, clean-room install smoke, compatibility-matrix validation, and sample-backed release smoke.
   - This blocks release-readiness sign-off.

### QA Infrastructure Setup (Pre-Implementation)

1. **Fixture modules and harness** - QA + Dev
   - `spacetime/modules/smoke_test` baseline for happy-path coverage
   - `spacetime/modules/compatibility_fixture` for schema drift, reconnect, and replacement scenarios

2. **Test environments** - QA
   - Local: Godot `4.6.2` `.NET` project + standalone SpacetimeDB `2.1.0` + generated fixture bindings
   - CI/CD: clean-room runner that installs the release artifact, regenerates bindings, and executes `dotnet test` plus demo smoke
   - Staging/Hosted: Maincloud-compatible deployment with WSS/TLS and supported auth configuration

**Example fixture pattern:**

```csharp
using Xunit;

public sealed record SmokeFixtureConfig(string ModuleName, string Host, bool UseStoredToken);

public static class SmokeFixtureFactory
{
    public static SmokeFixtureConfig Create(
        string moduleName = "smoke_test",
        string host = "ws://127.0.0.1:3000",
        bool useStoredToken = false)
        => new(moduleName, host, useStoredToken);
}

public sealed class ConnectionSmokeTests
{
    [Fact]
    public async Task Connection_smoke_reaches_connected_state()
    {
        var fixture = SmokeFixtureFactory.Create();
        await using var harness = await GodotHarness.StartAsync(fixture);

        await harness.AdvanceUntilAsync(() => harness.Client.IsConnected);

        Assert.True(harness.Client.IsConnected);
        Assert.Equal("Connected", harness.LastLifecycleEvent);
    }
}
```

---

## Risk Assessment

**Note:** Full mitigation detail lives in the Architecture doc. This section focuses on how QA will validate each risk.

### High-Priority Risks (Score >=6)

| Risk ID | Category | Description | Score | QA Test Coverage |
| ------- | -------- | ----------- | ----- | ---------------- |
| **R-001** | TECH | Nondeterministic runtime tick or callback ordering | **9** | Unit/component coverage for lifecycle ordering plus local end-to-end smoke on repeated runs |
| **R-002** | DATA | Subscription replacement or reconnect corrupts local cache semantics | **6** | Integration scenarios comparing cache snapshots before and after resubscribe/reconnect |
| **R-003** | SEC | Token persistence or diagnostics leak secrets | **6** | Resume-path tests, corrupt-token cases, and log-redaction assertions |
| **R-004** | TECH | Schema/binding drift reaches release | **9** | Regeneration, compile, and clean-room install/release smoke gates |
| **R-006** | OPS | Hosted behavior diverges from local behavior | **6** | Hosted parity smoke under the same public settings model as local |
| **R-007** | TECH | Public API drifts into runtime-specific concepts | **6** | Contract-level checks on public types, docs, and example flows |
| **R-010** | PERF | Update throughput exceeds frame budget | **6** | High-update fixture benchmark and event-dispatch observation |

### Medium/Low-Priority Risks

| Risk ID | Category | Description | Score | QA Test Coverage |
| ------- | -------- | ----------- | ----- | ---------------- |
| R-005 | BUS | Bootstrap contract remains ambiguous | 4 | Sample and quickstart walkthrough against the chosen bootstrap path |
| R-008 | OPS | Release package/install flow is incomplete | 4 | Clean-room install smoke on release artifacts |
| R-009 | BUS | Diagnostics are too weak for self-serve recovery | 4 | Setup/auth/version failure drills against docs and typed errors |
| R-011 | BUS | Support messaging overclaims unsupported platforms | 2 | Documentation and release-note wording checks |

---

## Entry Criteria

**QA testing cannot begin until all of the following are met:**

- [ ] Requirements and assumptions are agreed by Dev, QA, and Docs owners
- [ ] Test environments are provisioned and reachable
- [ ] Fixture modules, reset tooling, and generated bindings are available
- [ ] Deterministic runtime tick seam exists for automation
- [ ] Bootstrap contract is frozen and reflected in quickstart/sample content
- [ ] Candidate build or release artifact is available in a testable form

## Exit Criteria

**Testing phase is complete when all of the following are met:**

- [ ] All P0 tests are passing (100% pass rate)
- [ ] At least 95% of P1 tests are passing and any remaining failures are triaged and accepted
- [ ] No open high-priority / high-severity bugs remain against the supported workflow
- [ ] All score >=6 mitigations are complete or explicitly waived with owner and rationale
- [ ] Clean-room install smoke passes for the supported release artifact
- [ ] Supported Godot and SpacetimeDB version pair validation is green
- [ ] Automated coverage across P0/P1 scenarios is at least 80%
- [ ] High-update smoke stays within the agreed frame-budget envelope if performance claims are made

---

## Project Team (Optional)

| Name | Role | Testing Responsibilities |
| ---- | ---- | ------------------------ |
| Pinkyd | Maintainer / Dev Lead | Core SDK implementation, unit/component test support, release sign-off |
| TBD | QA Owner | Integration and end-to-end automation, regression gate ownership |
| TBD | Architect | Runtime-neutral contract review, blocker resolution |
| TBD | Docs / PM Owner | Quickstart, troubleshooting, migration, and support-messaging acceptance |

---

## Test Coverage Plan

**IMPORTANT:** P0/P1/P2/P3 = **priority and risk level**, not execution timing. Execution timing is defined separately in the next section.

### P0 (Critical)

**Criteria:** Blocks core functionality + high risk + no workaround + affects the primary supported workflow

| Test ID | Requirement | Test Level | Risk Link | Notes |
| ------- | ----------- | ---------- | --------- | ----- |
| **P0-001** | FR1-FR4 install and first local connection work from a clean project | E2E | R-004 | Validates release artifact, addon enablement, and first working integration |
| **P0-002** | FR14-FR16 valid token resume and invalid-token recovery behave explicitly and safely | Component | R-003 | Covers valid, expired, corrupt, and cleared-token paths |
| **P0-003** | FR17-FR20 initial subscription sync populates cache and row callbacks fire exactly once | API | R-001, R-002 | Uses deterministic fixture module state |
| **P0-004** | FR21-FR22 subscription replacement and reconnect preserve cache correctness | API | R-002 | No stale, gapped, or duplicated row observations |
| **P0-005** | FR23-FR27 reducer invocation distinguishes success, recoverable failure, and connection-loss states | Component | R-001 | Typed runtime events must be explicit for gameplay code |
| **P0-006** | FR33-FR36 regeneration and compatibility gate fail fast on schema drift before release | Unit | R-004, R-008 | Treat as mandatory release blocker, not a best-effort check |

**Total P0:** ~6 tests

---

### P1 (High)

**Criteria:** Important features + medium/high risk + common workflows + hard workaround

| Test ID | Requirement | Test Level | Risk Link | Notes |
| ------- | ----------- | ---------- | --------- | ----- |
| **P1-001** | FR11-FR13 lifecycle state transitions and reconnect backoff are deterministic | Unit | R-001 | Covers state machine and retry sequencing |
| **P1-002** | FR15 plus NFR5-NFR7 opt-in token storage never persists by default and clear() fully removes reusable state | Component | R-003 | Protects secure default behavior |
| **P1-003** | FR11-FR16 hosted WSS/TLS path works with the same public settings model as local | E2E | R-006 | Required before any hosted support claim |
| **P1-004** | FR28-FR31 quickstart and troubleshooting recover from wrong host, module-down, and mismatch cases | E2E | R-009 | Measures self-serve recovery without maintainer help |
| **P1-005** | FR39-FR42 public API stays runtime-neutral and does not leak platform-SDK types | Unit | R-007 | Contract-level guard rather than behavior-only testing |
| **P1-006** | FR24-FR25 signal/event adapters stay scene-safe and do not expose transport internals | Component | R-001, R-007 | Focuses on public Godot-facing behavior |
| **P1-007** | FR35-FR38 release artifact installs cleanly and includes required docs/sample references | E2E | R-008 | Clean-room validation of the actual distribution path |
| **P1-008** | FR6-FR10 additive schema change and regeneration preserve conceptual mapping | API | R-004, R-007 | Covers tables, reducers, and events after regeneration |

**Total P1:** ~8 tests

---

### P2 (Medium)

**Criteria:** Secondary workflows + lower-risk recovery paths + documentation and compatibility fit checks

| Test ID | Requirement | Test Level | Risk Link | Notes |
| ------- | ----------- | ---------- | --------- | ----- |
| **P2-001** | FR9 incompatible bindings are detected before runtime use with explicit diagnostics | Unit | R-009 | Focuses on error quality, not only failure presence |
| **P2-002** | FR18-FR22 invalid subscription requests surface typed failure without destabilizing existing cache state | API | R-002 | Keeps prior good state intact |
| **P2-003** | FR11-FR16 unsupported version pair or bad config yields actionable status feedback | Component | R-005, R-009 | Supports troubleshooting and support burden reduction |
| **P2-004** | FR30-FR31 migration guidance from custom/community paths maps old concepts to the new SDK model | Unit | R-009 | Documentation contract check |
| **P2-005** | NFR13-NFR16 docs, sample, and release artifact describe the same supported path | E2E | R-005, R-008 | Prevents trust-damaging drift between surfaces |
| **P2-006** | NFR17-NFR19 compatibility matrix publication matches the actually validated version pair | Unit | R-008, R-011 | Prevents vague or stale support claims |

**Total P2:** ~6 tests

---

### P3 (Low)

**Criteria:** Nice-to-have, exploratory, benchmark, or support-polish validation

| Test ID | Requirement | Test Level | Risk Link | Notes |
| ------- | ----------- | ---------- | --------- | ----- |
| **P3-001** | NFR2-NFR3 high-update benchmark records frame-budget behavior under stress fixture | Component | R-010 | Exploratory until performance envelope is formalized |
| **P3-002** | Logging verbosity modes remain structured and useful without exposing secrets | Unit | R-009 | Support-quality and diagnostics check |
| **P3-003** | Release docs and support matrix clearly exclude unsupported targets such as web export | Unit | R-011 | Messaging validation only |
| **P3-004** | Future-facing runtime-neutral terminology stays consistent across docs/examples | Unit | R-007 | Prevents accidental `.NET`-only language creep |

**Total P3:** ~4 tests

---

## Execution Strategy

**Philosophy:** Run every fast functional check in PRs. Defer only hosted, matrix, or long-running stress work that adds meaningful infrastructure or time overhead. This product has no browser surface, so the primary automation stack is `dotnet test` plus headless Godot/demo smoke, not a browser E2E runner.

### Every PR: `dotnet test` + headless Godot smoke (~10-15 min)

**All fast functional tests:**

- Unit tests for state machine, token redaction, compatibility rules, and public-contract guards
- Component tests for token-store behavior, event adapters, reducer result handling, and configuration failures
- Local fixture-module integration checks for subscription sync, replacement, reconnect, and regeneration smoke
- Headless demo smoke for clean install, first connection, and release-package sanity

**Why run in PRs:** Fast feedback and no external hosted dependency for the core supported workflow.

### Nightly: hosted parity + compatibility matrix jobs (~30-60 min)

**Longer environment-aware checks:**

- Hosted WSS/TLS/auth smoke against the supported deployment target
- Regenerated binding validation across the exact supported version pair
- Clean-room artifact install and sample-backed release rehearsal

**Why defer to nightly:** Requires hosted credentials, wider matrix coverage, and slower environment setup.

### Weekly: endurance and throughput validation (~hours)

**Long-running or lower-frequency checks:**

- High-update event throughput benchmark
- Reconnect/recovery soak test
- Release-install rehearsal from draft release assets

**Why defer to weekly:** Long runtime, lower day-to-day signal, and heavier infrastructure cost.

**Manual checks excluded from automation:**

- Human review of migration-guide clarity
- One-time walkthrough on a brand-new workstation
- Final editorial validation of release notes and support messaging

---

## QA Effort Estimate

**QA test development effort only** (excludes backend feature implementation and release-engineering work owned by other roles):

| Priority | Count | Effort Range | Notes |
| -------- | ----- | ------------ | ----- |
| P0 | ~6 | ~2-3 weeks | Deterministic harness, auth safety, cache correctness, release blockers |
| P1 | ~8 | ~2-3 weeks | Hosted parity, docs recovery, public contract, release install checks |
| P2 | ~6 | ~1-2 weeks | Compatibility messaging, migration/docs alignment, secondary failure paths |
| P3 | ~4 | ~3-5 days | Benchmarks and support-polish coverage |
| **Total** | ~24 | **~6-8 weeks** | **1 QA engineer, full-time** |

**Assumptions:**

- Includes test design, implementation, debugging, and CI integration
- Excludes ongoing maintenance and future matrix expansion
- Assumes fixture modules and deterministic runtime hooks exist when automation starts

**Dependencies from other teams:**

- See "Dependencies & Test Blockers" for what QA needs from SDK Runtime, Auth, Codegen, and Release owners

---

## Implementation Planning Handoff (Optional)

| Work Item | Owner | Target Milestone (Optional) | Dependencies/Notes |
| --------- | ----- | --------------------------- | ------------------ |
| Deterministic `FrameTick()` test seam | SDK Runtime | M1 | Blocks P0 lifecycle and reducer coverage |
| Fixture module reset/seed tooling | Dev / Test Harness | M1 | Required for auth, subscription, and reconnect scenarios |
| Token-store contract and redaction completion | Auth / SDK | M1 | Required before auth-resume automation |
| Hosted parity smoke environment | CI / Platform | M2 | Required before any hosted-support claim |
| Clean-room install and compatibility-matrix release job | Release Eng | M2 | Required before first tagged public release |

---

## Tooling & Access

| Tool or Service | Purpose | Access Required | Status |
| --------------- | ------- | --------------- | ------ |
| Godot `4.6.2` headless runner | Demo and runtime smoke scenes | Local and CI runners with `.NET` support | Pending |
| `.NET 8` SDK and `dotnet test` | Unit and component automation | Local and CI runners | Pending |
| Standalone SpacetimeDB `2.1.0` | Local integration fixture environment | Local and CI environment setup | Pending |
| Hosted Maincloud-compatible target | Hosted parity smoke | Staging credentials and endpoint | Pending |
| GitHub Actions artifact retention | Release rehearsal and clean-room install checks | Repo workflow permissions | Pending |

**Access requests needed (if any):**

- [ ] Hosted validation credentials and WSS endpoint for nightly/release smoke
- [ ] CI secret management for hosted auth and release-install rehearsal

---

## Interworking & Regression

**Services and components impacted by this feature:**

| Service/Component | Impact | Regression Scope | Validation Steps |
| ----------------- | ------ | ---------------- | ---------------- |
| **`addons/godot_spacetime/src/Public/`** | Public contract stability | Unit and component contract checks must pass | Confirm no direct platform-SDK type leakage |
| **`addons/godot_spacetime/src/Internal/Connection/`** | Lifecycle and reconnect correctness | Local smoke and reconnect tests must pass | Repeat connect/disconnect/reconnect fixture flows |
| **`addons/godot_spacetime/src/Internal/Subscriptions/` + `Cache/`** | Cache correctness under sync and replacement | Subscription sync and replacement suite must pass | Compare cache snapshots before/after handoff |
| **`addons/godot_spacetime/src/Internal/Auth/`** | Token safety and resume behavior | Resume/clear/redaction tests must pass | Inspect logs and persisted state alongside behavior |
| **`scripts/codegen/` + `tests/fixtures/generated/`** | Schema compatibility | Regeneration and compile smoke must pass | Diff generated output and enforce clean build |
| **`docs/` + `demo/`** | Onboarding trust and product credibility | Install walkthrough and quickstart smoke must pass | Validate docs against actual sample bootstrap path |

**Regression test strategy:**

- PR suite must stay green before merge: unit, component, local integration, and codegen smoke
- Hosted parity suite must pass before any release that claims hosted support
- Docs, sample, and release artifact are validated together; none get independent sign-off
- SDK, Docs, and Release owners must coordinate whenever bootstrap, public API, or packaging changes

---

## Appendix A: Code Examples & Tagging

**Trait-based tagging for selective execution:**

```csharp
using Xunit;

public sealed class SubscriptionCoverage
{
    [Fact]
    [Trait("Priority", "P0")]
    [Trait("Layer", "Integration")]
    [Trait("Risk", "R-002")]
    public async Task Subscription_replacement_preserves_cache_consistency()
    {
        var fixture = SmokeFixtureFactory.Create(moduleName: "compatibility_fixture");
        await using var harness = await GodotHarness.StartAsync(fixture);

        await harness.ConnectAsync();
        await harness.ReplaceSubscriptionAsync("SELECT * FROM players WHERE room_id = 'room_b'");
        await harness.AssertCacheSnapshotAsync("room_b");
    }
}
```

**Run specific tags:**

```bash
# Run only P0 tests
dotnet test --filter "Priority=P0"

# Run P0 + P1 tests
dotnet test --filter "(Priority=P0|Priority=P1)"

# Run tests for a specific risk
dotnet test --filter "Risk=R-003"

# Run all tests in CI
dotnet test
```

If a small Node-based release-check harness is added later, mirror this same priority/risk taxonomy there instead of creating a second tagging scheme.

---

## Appendix B: Knowledge Base References

- **Risk Governance:** `risk-governance.md` - Risk scoring methodology and release-gate framing
- **Probability and Impact:** `probability-impact.md` - 1-3 scoring rules and mitigation thresholds
- **Test Levels Framework:** `test-levels-framework.md` - Unit vs component vs API vs E2E selection
- **Test Priorities Matrix:** `test-priorities-matrix.md` - P0-P3 assignment logic
- **Test Quality:** `test-quality.md` - Determinism, isolation, and cleanup expectations
- **Data Factories:** `data-factories.md` - API-first and fixture-first setup patterns
- **Fixture Architecture:** `fixture-architecture.md` - Pure helper plus harness composition model

---

**Generated by:** BMad TEA Agent
**Workflow:** `bmad-testarch-test-design`
**Version:** 4.0 (BMad v6)

