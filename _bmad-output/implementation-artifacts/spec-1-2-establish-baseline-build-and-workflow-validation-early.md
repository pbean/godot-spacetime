---
title: '1.2 Establish Baseline Build and Workflow Validation Early'
type: 'feature'
created: '2026-04-13T17:27:10-07:00'
status: 'done'
baseline_commit: '2e5c7a1406e21cc07a692352465abc97612163d8'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md'
  - '{project-root}/_bmad-output/test-artifacts/test-design/godot-spacetime-handoff.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story `1.1` created the supported Godot addon foundation, but the repository still has no automated validation lane to prove that foundation keeps building, no machine-checkable support baseline, and no discoverable placeholder inputs for the later codegen and compatibility stories. Without that baseline now, version drift and missing workflow prerequisites will accumulate until deeper runtime stories are forced to debug repo hygiene and release trust at the same time.

**Approach:** Add one reusable foundation-validation path that CI and local maintainers can both run. That path should restore and build the current solution, verify the declared support baseline stays consistent across docs and config, and check that the repo-owned script, fixture, and SpacetimeDB module locations needed by later binding-generation validation already exist and are documented even though code generation itself is not implemented yet.

## Boundaries & Constraints

**Always:** Keep this story focused on one extendable validation lane; validate the existing repo-root solution and addon scaffold rather than inventing a second build path; make support-version declarations machine-checkable and fail with file-specific drift messages; create discoverable repo-owned placeholder locations for later `spacetime/modules/`, `tests/fixtures/`, and validation-script inputs in the architecture-approved tree; keep runtime, auth, subscription, connection, and real code-generation behavior out of scope.

**Ask First:** Changing the declared support baseline for Godot, `.NET`, or SpacetimeDB; requiring hosted services, secrets, or a real SpacetimeDB instance in the baseline workflow; adding release packaging or sample/runtime smoke beyond the foundation build and readiness checks.

**Never:** Implement actual binding generation, runtime connection logic, editor UX panels, sample gameplay flow, or release packaging in this story; create a parallel one-off validation script that later stories would need to replace; depend on manual Godot editor interaction to pass the baseline validation job.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Foundation validation passes | Solution, docs, support baseline metadata, and prerequisite paths all match the declared foundation state | Local script and CI workflow complete successfully after restore/build plus readiness checks | N/A |
| Support baseline drift | A doc or config file declares a different Godot, `.NET`, SpacetimeDB, or planned package version than the validation baseline | Validation exits non-zero and names the exact file and mismatched value | Failure message tells the maintainer which declaration must be updated |
| Missing future-workflow prerequisites | Required validation/script/module/fixture placeholder paths are absent or undocumented | Validation exits non-zero and reports the missing path or missing discoverability doc | Failure message points to the expected repo location so the missing prerequisite is obvious |

</frozen-after-approval>

## Code Map

- `_bmad-output/implementation-artifacts/epic-1-context.md` -- distilled Epic 1 constraints, including the requirement for one reusable validation lane and future codegen/release extension.
- `_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md` -- previous story continuity for the repo-root workspace, addon boundary, and explicit support baseline already shipped.
- `_bmad-output/test-artifacts/test-design/godot-spacetime-handoff.md` -- quality handoff that says codegen and compatibility drift must fail before release and that related stories should extend shared gates.
- `godot-spacetime.sln` and `godot-spacetime.csproj` -- existing foundation build targets the validation lane must restore/build.
- `README.md`, `docs/install.md`, and `docs/compatibility-matrix.md` -- current human-readable support declarations that need drift checks.
- `.github/workflows/` -- missing CI location that should own the baseline foundation-validation workflow.
- `scripts/compatibility/` -- architecture-approved home for reusable support-baseline and readiness checks; currently absent.
- `spacetime/modules/` and `tests/fixtures/` -- architecture-approved future codegen and validation inputs that need placeholder structure and discoverability before the real workflows land.
- `docs/codegen.md` -- architecture-planned doc location for explaining repo-owned codegen inputs and readiness expectations; currently absent.

## Tasks & Acceptance

**Execution:**
- [x] `.github/workflows/validate-foundation.yml` -- add one CI workflow that restores and builds `godot-spacetime.sln`, then runs the repo foundation-validation entrypoint -- creates the extendable automation lane later stories can grow instead of replace.
- [x] `scripts/compatibility/support-baseline.json` and `scripts/compatibility/validate-foundation.py` -- add a machine-readable support baseline plus a validation script that checks version declarations, required docs, and required repo paths with clear failure messages -- makes foundational drift and missing prerequisites fail early.
- [x] `spacetime/modules/README.md`, `spacetime/modules/smoke_test/README.md`, `spacetime/modules/compatibility_fixture/README.md`, `tests/fixtures/README.md`, `tests/fixtures/generated/.gitkeep`, and `tests/fixtures/settings/.gitkeep` -- create discoverable placeholder module and fixture inputs for later codegen, compatibility, and test automation stories -- satisfies readiness checks without shipping generated bindings or real fixture logic yet.
- [x] `README.md`, `docs/install.md`, `docs/compatibility-matrix.md`, and `docs/codegen.md` -- document the new validation entrypoint, the source-of-truth support baseline, and where later codegen-related repo inputs live -- keeps human guidance aligned with the automated checks.
- [x] `.gitignore` -- ignore any new validation-script local state only if the chosen implementation introduces it, otherwise leave it unchanged -- avoids unnecessary repo noise while keeping the story minimal.

**Acceptance Criteria:**
- Given a clean checkout on a supported runner, when the foundation validation workflow runs, then it restores and builds `godot-spacetime.sln` and reports success without requiring manual Godot editor steps.
- Given the documented support baseline drifts across docs, config, or validation metadata, when the validation entrypoint runs, then it fails with a clear message that identifies the mismatched file and value.
- Given later binding-generation and compatibility stories have not been implemented yet, when a maintainer inspects the repository and runs validation, then the expected script, module, and fixture input locations are already present and discoverable through repo docs instead of tribal knowledge.
- Given future stories add codegen, compatibility, or release hardening checks, when they extend validation, then they can add to the existing workflow and validation entrypoint rather than introducing a separate manual-only path.

## Spec Change Log

- 2026-04-13: Review-driven validation-lane hardening after acceptance and edge-case review.
  Trigger: reviewers found that local docs and CI did not actually share one full entrypoint, malformed baseline JSON produced a traceback, and substring/path-existence checks could false-pass drift.
  Amended: moved restore/build into `scripts/compatibility/validate-foundation.py`, pointed CI and docs at that shared lane, tightened baseline checks to exact lines plus typed paths, and aligned the machine-readable metadata with the new entrypoint contract.
  Avoids: local/CI drift, unclear malformed-baseline failures, and false-positive readiness checks that would miss version or path regressions.
  KEEP: the single workflow lane, machine-readable baseline metadata, and placeholder module/fixture structure introduced by Story `1.2`.

## Design Notes

This story is about validation shape, not runtime behavior. The most important design constraint is that local and CI validation share one entrypoint so future stories can bolt on additional checks without forking policy.

Expected structure after this story:

```text
.github/workflows/validate-foundation.yml
scripts/compatibility/
  support-baseline.json
  validate-foundation.py
spacetime/modules/
  README.md
  smoke_test/README.md
  compatibility_fixture/README.md
tests/fixtures/
  README.md
  generated/.gitkeep
  settings/.gitkeep
docs/codegen.md
```

## Verification

**Commands:**
- `python3 scripts/compatibility/validate-foundation.py` -- expected: restores `godot-spacetime.sln`, builds `godot-spacetime.sln -c Debug --no-restore`, and then passes only when docs/config/paths match exactly.

**Manual checks (if no CLI):**
- Open the new CI workflow file and confirm it runs the same validation entrypoint used locally.
- Inspect `docs/codegen.md`, `spacetime/modules/`, and `tests/fixtures/` and confirm they explain the placeholder inputs as future workflow prerequisites rather than as already-implemented codegen/runtime behavior.

## Suggested Review Order

**Shared Lane**

- Centralizes restore, build, and readiness checks behind one reusable entrypoint.
  [`validate-foundation.py:14`](../../scripts/compatibility/validate-foundation.py#L14)

- CI now delegates to that same entrypoint instead of duplicating command flow.
  [`validate-foundation.yml:1`](../../.github/workflows/validate-foundation.yml#L1)

**Drift Contract**

- Encodes support versions, typed required paths, and exact-line checks in one baseline file.
  [`support-baseline.json:1`](../../scripts/compatibility/support-baseline.json#L1)

- Captures the review-driven hardening that tightened the lane after subagent findings.
  [`spec-1-2-establish-baseline-build-and-workflow-validation-early.md:68`](./spec-1-2-establish-baseline-build-and-workflow-validation-early.md#L68)

**Bootstrap Story**

- High-level maintainer entrypoint now matches the shared validation lane.
  [`README.md:16`](../../README.md#L16)

- Detailed install guidance mirrors the same bootstrap and enablement sequence.
  [`install.md:11`](../../docs/install.md#L11)

- Codegen readiness points future stories at the same validation contract.
  [`codegen.md:1`](../../docs/codegen.md#L1)

**Future Inputs**

- Reserves canonical SpacetimeDB module roots without pretending codegen exists yet.
  [`modules/README.md:1`](../../spacetime/modules/README.md#L1)

- Reserves non-shipping fixture roots for later generated bindings and settings.
  [`fixtures/README.md:1`](../../tests/fixtures/README.md#L1)
