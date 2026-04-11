---
title: "Product Brief Distillate: godot-spacetime"
type: llm-distillate
source: "product-brief-godot-spacetime.md"
created: "2026-04-09T15:22:33-07:00"
purpose: "Token-efficient context for downstream PRD creation"
---

# Product Brief Distillate: Godot SpacetimeDB SDK

## Product Intent

- Build an open-source Godot SDK/plugin for SpacetimeDB with a clean long-term architecture, not a one-off compatibility shim.
- Initial product target is SpacetimeDB `2.1+`, chosen as a best-practice stable baseline instead of promising compatibility with every future `2.x` change upfront.
- Primary immediate user is the project owner building a real Godot game; broader goal is external open-source adoption across the Godot ecosystem.

## Core Product Strategy

- Architecture must be designed for both `.NET` and `GDScript`, even though delivery is phased.
- Ship one runtime first, but do not let core abstractions assume C# permanently; later native `GDScript` support should be an extension path, not a redesign.
- Delivery order chosen in discovery: `.NET` first, `GDScript` later.
- Rationale for `.NET` first: closest alignment with official SpacetimeDB client behavior and strongest path to a commercially credible v1.
- Rationale for eventual `GDScript`: critical for broader Godot adoption and for keeping web-export-compatible futures open.

## V1 Scope Signals

- Use the Unity plugin as the practical v1 feature baseline.
- V1 must include generated module bindings, connection flow, token persistence/auth flow, subscriptions, client-side cache access, row update callbacks, reducer invocation, reducer event/result handling, documentation, and a sample integration.
- V1 should be packaged as a real Godot plugin and released publicly from the start.
- Distribution decision made in discovery: GitHub-release-first.
- AssetLib distribution is intentionally deferred, not required for initial success.

## Technical Direction

- Generated bindings should follow the official C# generation model as closely as possible.
- Commercial viability requirement from user: avoid inventing a Godot-only binding contract if upstream C# concepts can transfer cleanly.
- Runtime-agnostic layer should preserve common concepts across implementations: connection lifecycle, schema contracts, event model, cache semantics, reducer/procedure mental model, and auth/token handling.
- Runtime-specific implementations should sit beneath that shared contract so future `.NET` and native `GDScript` clients can share the same product mental model.
- TypeScript SDK is a supporting API/DX reference, not the main contract source.
- Archived Unity SDK is useful as a behavior baseline and usage reference, but not as the canonical implementation source because the current official C# repo now covers Unity too.

## Competitive / Reference Context

- Official references used in discovery:
- `clockworklabs/com.clockworklabs.spacetimedbsdk` is the current canonical C# baseline and explicitly also covers Unity usage.
- `clockworklabs/spacetimedb-typescript-sdk` plus current TypeScript docs help validate cross-language API expectations and builder-style connection patterns.
- `clockworklabs/com.clockworklabs.spacetimedbsdk-archive` is historical/reference material for Unity behaviors and usage examples.
- `flametime/Godot-SpacetimeDB-SDK` branch `stdb-v2-protocol` is active, useful as a Godot reference, but not chosen as the product foundation.
- Why not build directly on `flametime` as the core plan: user explicitly prioritized a cleaner long-term foundation over the fastest bootstrap path.

## Findings From Research

- Upstream SpacetimeDB is actively current, with latest release `v2.1.0` published March 24, 2026.
- Current client docs confirm common SDK expectations across languages: generated bindings, connection builder/lifecycle, subscriptions, local cache access, row callbacks, reducer calls, and procedure support.
- Godot web export matters strategically because official Godot docs indicate Godot 4 `.NET/C#` projects do not support web export; this increases the long-term importance of a native `GDScript` runtime if broad Godot adoption is the goal.
- The unofficial Godot branch already demonstrates user-facing Godot patterns that matter, including addon installation, generated bindings, singleton/module access, subscriptions, local cache querying, row receivers, and reducer callbacks.
- The same unofficial branch also advertises limitations that validate the clean-slate decision for product framing: nested type limitations, missing Brotli support, no procedures, no event tables, and some doc/version drift.

## User Constraints And Preferences

- User wants the SDK first for personal use, but explicitly wants it viable for open-source Godot adoption.
- User prefers a long-term cleaner implementation over extending an unofficial branch unless there were strong reasons otherwise.
- User wants the product to be commercially viable for users, which pushed the decision toward the official C# generation model and official client semantics.
- User did not ask for immediate full parity across `.NET` and `GDScript`; phased delivery is acceptable if architecture remains compatible with both.

## Rejected Or Deferred Ideas

- Rejected as primary foundation: directly building the product on top of the unofficial `flametime` branch.
- Rejected for v1: full native `GDScript` runtime parity.
- Rejected for v1: web export runtime support.
- Rejected for v1: features beyond the Unity plugin baseline.
- Rejected for v1: AssetLib-first or AssetLib-required distribution.
- Rejected for v1: speculative advanced features such as procedures/event-table support unless they are later proven necessary to meet or exceed the baseline.

## Risks To Carry Into PRD

- Dual-runtime ambition can create architectural overreach; PRD should define the minimum shared contract needed now versus what can wait for `GDScript` phase two.
- “Unity parity” needs translation into explicit Godot acceptance criteria; otherwise it remains a loose benchmark rather than a buildable scope.
- Following the official C# generation model too literally could produce a Godot API that feels unnatural; PRD should distinguish between preserving upstream concepts and copying surface syntax.
- GitHub-release-first lowers launch friction, but PRD should still define installation expectations clearly so adoption is not blocked by packaging friction.
- The decision to target `2.1+` reduces immediate compatibility ambiguity, but PRD should specify the upgrade/compatibility policy for future SpacetimeDB minor releases.

## Open Questions

- What exact Godot version or versions should be supported in v1?
- What target platforms beyond desktop matter for the first `.NET` release, especially mobile?
- How much editor tooling is necessary for v1 beyond installation/configuration basics?
- What does “commercially viable” mean operationally for this repo: support expectations, release cadence, API stability guarantees, migration guides, or paid-friendly licensing posture?
- How should sample content be scoped: minimal connectivity demo, gameplay-oriented sample, or migration-style reference from Unity/C# concepts into Godot?

## PRD Handoff Notes

- Treat this project as a developer tool / SDK product, not just a code package.
- The main product promise is trust: Godot developers should feel they are using a serious, upstream-aligned SpacetimeDB client path.
- Preserve the phased message in downstream docs and requirements: `.NET` first is a delivery choice, not a statement that `GDScript` is secondary forever.
- PRD should likely break work into at least these themes: shared architecture contract, `.NET` runtime implementation, codegen workflow, Godot packaging/onboarding, sample app/docs, and future-native `GDScript` expansion path.
