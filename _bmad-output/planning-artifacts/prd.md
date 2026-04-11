---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
inputDocuments:
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/product-brief-godot-spacetime.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/product-brief-godot-spacetime-distillate.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/research/domain-godot-spacetimedb-sdk-plugin-research-2026-04-09.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/research/technical-godot-spacetimedb-sdk-plugin-research-2026-04-09.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/ux-design-specification.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/implementation-readiness-report-2026-04-10.md'
workflowType: 'prd'
documentCounts:
  briefCount: 2
  researchCount: 2
  brainstormingCount: 0
  projectDocsCount: 0
classification:
  projectType: developer_tool
  domain: gaming
  complexity: high
  projectContext: greenfield
---

# Product Requirements Document - godot-spacetime

**Author:** Pinkyd
**Date:** 2026-04-09

## Executive Summary

This product is an open-source Godot SDK/plugin for SpacetimeDB `2.1+`. It exists to close a clear ecosystem gap: there is no official Godot integration, the current community option is not moving fast enough for real project needs, and Godot developers should not have to build or maintain their own client layer to use SpacetimeDB seriously.

The first release should provide a usable `.NET`-first path for real Godot projects. That means generated bindings, connection lifecycle management, authentication and token persistence, subscriptions, client-side cache access, row update callbacks, reducer invocation and reducer event handling, documentation, and a working sample. The goal is a dependable way to use SpacetimeDB in Godot now, not a novel abstraction.

This SDK should be packaged and structured as a serious upstream-aligned client path, not as a one-off compatibility shim. It should follow the official C#/Unity client model closely where that improves correctness, transferability, and upgrade confidence, while keeping the architecture open to a later native `GDScript` runtime when that becomes the right next step.

### What Makes This Special

This product is valuable because it closes an obvious ecosystem gap with a practical, credible implementation driven by real usage pressure. It is being built for an actual Godot project, which keeps the scope grounded in what must work instead of what sounds impressive.

The core differentiator is trust. A Godot developer should be able to look at this SDK and see a serious SpacetimeDB integration that maps cleanly to official client concepts, supports a realistic production workflow, and does not require betting on abandoned or lightly maintained tooling. The product wins if developers can adopt SpacetimeDB in Godot without feeling like they are stepping off the supported path.

## Project Classification

- Project Type: `developer_tool`
- Domain: `gaming` / game-development infrastructure
- Complexity: `high`
- Project Context: `greenfield`

## Success Criteria

### User Success

Godot developers can install the SDK into a supported `.NET` Godot project, generate bindings from a SpacetimeDB module, connect successfully, authenticate or resume with a token, subscribe to data, read the local cache, observe row updates, and invoke reducers without writing custom client protocol code.

The SDK feels credible enough to use in a real game project rather than as a demo-only integration. A developer should be able to follow the documentation and sample, get to a working end-to-end connection in a single setup session, and understand how the Godot-facing workflow maps to official SpacetimeDB concepts.

The “this solved my problem” moment is when a Godot developer stops thinking about transport and protocol details and can just use SpacetimeDB from Godot with the same core mental model they would expect from the official C#/Unity path.

### Business Success

Success for this product is measured primarily by practical adoption and maintenance viability, not direct revenue. The first business win is that it becomes stable enough to support your own project without bespoke integration work outside the SDK.

Within the first 3 months after initial release, success means:

- the SDK is actively used in your project,
- the repository has a tagged public release,
- the docs and sample are complete enough for self-serve onboarding,
- compatibility is explicitly documented for target Godot and SpacetimeDB versions.

Within 12 months, success means:

- at least 3 external Godot projects confirm successful integration,
- at least 1 external contributor or meaningful outside maintenance contribution appears,
- the project has a repeatable release/update rhythm for upstream SpacetimeDB and Godot changes.

### Technical Success

The v1 release reaches practical parity with the Unity plugin baseline for the defined scope: generated bindings, connection flow, auth/token persistence, subscriptions, cache access, row update callbacks, reducer invocation, reducer event handling, documentation, and a working sample.

The `.NET` runtime is stable enough that users do not need to patch protocol behavior themselves. Release artifacts, installation steps, and sample content are reproducible. The SDK has a documented compatibility matrix and automated validation for the critical connection and data-flow paths.

The architecture also succeeds technically if it preserves a clean future path to native `GDScript` support without forcing a redesign of the product’s core concepts or generated binding model.

### Measurable Outcomes

- A new developer can go from install to first successful connection and live subscription update in under 60 minutes using the docs and sample.
- A supported sample project demonstrates binding generation, connection, auth/token resume, subscription updates, cache reads, row callbacks, and reducer invocation end to end.
- Your project uses the SDK without requiring custom protocol-layer code outside the SDK.
- Every release validates the supported Godot and SpacetimeDB version pairings for the core connection and data workflows.
- Compatibility issues caused by upstream SpacetimeDB minor releases are assessed and triaged within 14 days of the upstream release.
- External adopters can complete setup without direct maintainer intervention in a single session.
- The committed MVP plugin surfaces remain usable in narrow, standard, and wide Godot editor panel widths, and critical setup/recovery paths remain keyboard-accessible.

## Product Scope

### MVP - Minimum Viable Product

- `.NET`-first Godot SDK/plugin for SpacetimeDB `2.1+`
- Generated binding workflow aligned closely to the official C# model
- Connection lifecycle management
- Authentication and token persistence/resume
- Subscription management and synchronized local cache access
- Row update callbacks
- Reducer invocation and reducer event/result handling
- GitHub-release-first packaging
- Clear installation docs
- A working sample project
- Explicit compatibility matrix for the supported Godot and SpacetimeDB versions
- Minimal plugin/editor workflow surfaces for setup, code generation validation, compatibility checks, connection or auth status, and actionable recovery guidance
- Desktop-first usability for those committed plugin surfaces across common Godot editor panel widths

### MVP Editor Workflow Scope

The MVP does not commit to a broad editor shell. It does commit to the smallest set of plugin surfaces that materially reduce setup friction and make failure recovery explicit:

- basic setup and configuration forms
- a code generation configuration and validation panel
- a compatibility and validation panel
- a connection and auth status panel
- actionable recovery callouts at blocking failure points

These surfaces exist to support the code-first SDK workflow, not replace it. They must remain usable in narrow, standard, and wide Godot editor panel widths, support keyboard-driven progression through the core setup path, and never rely on color alone to communicate status or severity.

Diagnostics and event-log surfaces plus a dedicated subscription and runtime state inspector are explicitly post-MVP unless implementation proves one is required to unblock the core supported workflow.

### Growth Features (Post-MVP)

- Better onboarding and migration guidance for Godot developers coming from official C#/Unity concepts
- Broader platform coverage beyond the initial target platforms
- Improved packaging and possible AssetLib distribution
- Expanded diagnostics, runtime-inspector, or other editor ergonomics beyond the committed MVP surfaces where they reduce real setup friction
- Expanded upstream surface coverage such as procedures or event-table support if real usage justifies it
- Stronger automated compatibility testing across a wider version matrix

### Vision (Future)

- Native `GDScript` runtime support behind the same core product model
- A web-compatible path that does not depend on Godot `.NET` web support
- Wider adoption as the default Godot client path for SpacetimeDB
- A mature open-source project with outside contributors, stable release discipline, and trusted upstream-aligned behavior

## User Journeys

### Journey 1: Primary User - Success Path

**Pinkyd is building a real Godot game and needs SpacetimeDB to be usable now.**  
They start from a practical problem, not curiosity: there is no official Godot SDK, the accepted community path is not moving fast enough, and hand-rolling protocol behavior is a waste of time and risk. They install the plugin into a supported `.NET` Godot project, follow the quickstart, generate bindings from their module, wire up a connection, and see identity, subscriptions, and live cache updates working inside Godot.

The critical moment is not “the project compiles.” It is when gameplay code can invoke reducers and react to row updates without the developer thinking about transport internals. At that point, the SDK stops being an experiment and becomes infrastructure they can actually build the game on.

The journey succeeds when the developer can continue building game features instead of client plumbing. It fails if installation is fragile, generated bindings are confusing, connection/auth flows are opaque, or the Godot-facing workflow feels different enough from official SpacetimeDB concepts that the developer loses trust.

**Requirements revealed:**

- installable Godot plugin/package structure
- clear quickstart and setup path
- binding generation workflow
- connection/auth/token lifecycle support
- subscriptions, local cache access, row callbacks, reducer invocation
- Godot-friendly API surface that still maps to official concepts

### Journey 2: Primary User - Edge Case and Recovery

**The same developer hits a failure during real integration.**  
Maybe the target SpacetimeDB version changed, generated bindings no longer match the server schema, token resume fails, or a subscription behaves differently than expected. The developer is already under pressure because this is inside an actual game project, not a sandbox.

Instead of falling into undocumented behavior, they get a recoverable path: explicit compatibility guidance, understandable errors, a sample project to compare against, and documentation that explains what changed and what to do next. The product proves its value here by making problems diagnosable rather than mysterious.

The emotional turning point is when a blocked developer can recover in one session without digging into raw protocol details or patching the SDK locally. The journey fails if troubleshooting depends on maintainer handholding or reverse-engineering upstream behavior.

**Requirements revealed:**

- documented compatibility matrix
- actionable error reporting and troubleshooting docs
- reproducible sample project for comparison
- clear upgrade/regeneration workflow
- release notes and migration guidance for breaking or behavior-changing updates

### Journey 3: External Godot Developer - Self-Serve Adoption

**A second Godot developer finds the repository because they also want SpacetimeDB in Godot.**  
They are not invested in the project history. They judge the SDK by whether it looks real, current, and adoptable. They read the README, download a tagged release, open the sample, and try to reproduce a working connection without maintainer help.

Their decision point comes quickly: either this looks like a serious client path with clear docs, supported versions, and a believable sample, or it looks like another half-maintained community experiment. If setup works in one session and the concepts line up with official SpacetimeDB documentation, trust goes up immediately.

The journey succeeds when an outside developer can adopt the SDK self-serve and believe it is safe to build on. It fails if onboarding is ambiguous, packaging is inconsistent, or the sample/demo does not reflect the real supported workflow.

**Requirements revealed:**

- public releases with clear versioning
- self-serve installation and onboarding docs
- sample project that matches documented flow
- explicit support policy for Godot and SpacetimeDB versions
- positioning as a serious upstream-aligned SDK, not just a repo dump

### Journey 4: Maintainer / Release Operator

**The maintainer needs to keep the SDK credible as Godot and SpacetimeDB evolve.**  
A new SpacetimeDB release lands, or a Godot update affects the supported environment. The maintainer needs to verify what still works, regenerate where needed, run validation against the sample and core flows, update compatibility notes, and publish a release without guessing.

This journey matters because the product’s promise is trust. If maintainers cannot confidently assess compatibility and ship updates, users will feel the project is drifting into the same maintenance gap it set out to fix.

The journey succeeds when upstream changes can be evaluated and released through a repeatable process. It fails if every upgrade becomes ad hoc investigation with no clear validation path.

**Requirements revealed:**

- repeatable release workflow
- automated validation of critical flows
- sample-backed regression checking
- compatibility matrix maintenance
- explicit criteria for supported version pairs
- clear boundaries between MVP support and future/runtime-expansion work

### Journey Requirements Summary

These journeys point to a small number of core capability areas the PRD has to cover:

- onboarding and installation that work without maintainer intervention
- binding generation and schema-aligned client workflow
- reliable connection, auth, subscription, cache, and reducer flows
- troubleshooting and recovery paths for version, auth, and integration failures
- sample-backed documentation that proves the expected workflow
- release and compatibility discipline strong enough to keep the SDK trustworthy over time

## Domain-Specific Requirements

### Compliance & Regulatory

This product does not have the kind of domain-specific regulatory burden seen in healthcare, fintech, or govtech. The main governance requirements are software licensing clarity, secure handling of authentication tokens, and honest platform support claims.

The SDK must clearly separate:

- the plugin's own license,
- any reused or redistributed code from the official SpacetimeDB C#/Unity SDK,
- and the separate licensing posture of the SpacetimeDB server.

If the project later targets AssetLib, packaging and repository metadata must stay consistent with Godot's distribution expectations.

### Technical Constraints

The most important constraints are ecosystem constraints, not legal ones:

- Godot `.NET` is the correct v1 path, but Godot 4 C# projects do not support web export, so web support is not a valid v1 promise.
- The SDK must align with the official SpacetimeDB C# client model closely enough to stay credible and maintainable.
- Connection advancement, cache mutation, and callback delivery need to fit Godot's main-thread and frame-loop model.
- Token persistence and resume behavior must be explicit and documented, because auth state is part of the normal client workflow.
- The SDK must treat compatibility discipline as a product requirement, not a maintenance afterthought.

### Integration Requirements

The core integrations the product has to support are:

- Godot `.NET` project setup and plugin packaging
- SpacetimeDB CLI-driven code generation workflow
- Official SpacetimeDB C# client/runtime integration
- Local development against standalone SpacetimeDB
- Hosted usage against Maincloud or equivalent supported SpacetimeDB deployments
- Sample-backed docs that show the supported end-to-end flow

### Risk Mitigations

The main domain-specific risks are:

- **Maintenance drift:** the SDK falls behind Godot or SpacetimeDB changes.
  Mitigation: explicit compatibility matrix, sample-backed regression checks, repeatable release workflow.

- **Trust failure:** the SDK feels unofficial in the bad sense, meaning fragile or abandoned.
  Mitigation: tagged releases, clear support policy, docs that map to official SpacetimeDB concepts.

- **Platform overclaiming:** users assume web support or broader platform support that does not really exist.
  Mitigation: precise support matrix and scoped release messaging.

- **Onboarding friction:** developers still have to reverse-engineer setup or protocol behavior.
  Mitigation: self-serve install docs, working sample, troubleshooting guidance, regeneration/update instructions.

## Developer Tool Specific Requirements

### Project-Type Overview

`godot-spacetime` is a developer SDK/plugin for using SpacetimeDB in Godot. It is not just a wrapper around network calls, and it cannot become a one-runtime dead end. The product must provide a practical `.NET` implementation first while preserving a stable product model that can later support a native `GDScript` runtime.

The product succeeds as a developer tool if installation, code generation, connection flow, and runtime usage are understandable, reproducible, and credible to external developers without maintainer intervention.

### Technical Architecture Considerations

The SDK must separate shared product concepts from runtime-specific implementation details. Connection lifecycle, generated binding concepts, cache semantics, subscriptions, reducer invocation, auth/token handling, and event/callback models must be designed so they remain valid across both `.NET` and future native `GDScript` runtimes.

The `.NET` implementation may ship first, but it must not define the product in a way that creates technical debt for `GDScript`. The v1 architecture must avoid C#-specific assumptions in the public mental model, binding contract, or overall API shape if those assumptions would force a later redesign.

Runtime-specific code should live beneath a stable Godot-facing contract. The implementation should make it possible to deliver `GDScript` later as another runtime path, not as a replacement product.

### Runtime Strategy

The product should be developed as one product in one repository. There is no need to split `.NET` and `GDScript` into separate repos unless there is a concrete operational reason later.

However, one repo does not mean one forced implementation. The SDK may use separate runtime-specific implementations, addons, packages, or modules inside the same repo if that is the cleanest way to preserve functionality and avoid technical debt.

The rule is:

- do not sacrifice `.NET` functionality just to keep `.NET` and `GDScript` artificially identical,
- do not design the `.NET` runtime in a way that blocks or forces rewrites for `GDScript`,
- and do not force a lowest-common-denominator plugin structure if separate runtime implementations in the same repo are cleaner.

Shared elements should be the product model, generated-binding concepts, docs, compatibility policy, examples where possible, and any runtime-neutral specifications or tests. Runtime-specific code should be allowed to diverge where necessary.

### Ongoing Architecture Check

Throughout the project, major decisions should be tested against two questions:

- does this make the future native `GDScript` runtime harder or force a rewrite?
- does this weaken the `.NET` implementation or remove needed functionality just to preserve symmetry?

If the answer to either is yes, the design should change. The goal is one coherent product in one repo, not one artificially unified implementation at any cost.

### Language Matrix

- **Shipping runtime in v1:** Godot `.NET/C#`
- **Architectural target from day one:** `.NET/C#` and native `GDScript`
- **Out of scope for v1:** full native `GDScript` runtime delivery
- **Non-negotiable constraint:** no v1 design choice should require rewriting the core product model to support `GDScript` later

This means generated bindings, lifecycle semantics, and public SDK concepts must be defined in runtime-neutral terms even where the first implementation uses the official C# client.

### Installation Methods

The initial installation path should be GitHub-release-first with Godot plugin/addon packaging suitable for real project use. Installation must be documented as a standard, repeatable workflow rather than a maintainer-assisted process.

The install flow must cover:

- supported Godot and SpacetimeDB versions,
- required `.NET` project setup,
- dependency expectations,
- binding generation steps,
- plugin/addon placement and enablement,
- and first successful connection validation.

AssetLib distribution can come later, but v1 must not depend on it.

### API Surface

The public SDK surface must cover the core SpacetimeDB client workflow expected by Godot developers:

- generated module bindings,
- connection lifecycle,
- authentication and token resume,
- subscriptions,
- synchronized local cache access,
- row update callbacks,
- reducer invocation,
- reducer result/event handling.

The API should stay close to official SpacetimeDB client concepts while still feeling usable in Godot. It should not become a thin copy of C# syntax, but it also must not invent a separate Godot-only conceptual model that would make upstream behavior harder to understand or maintain.

### Code Examples

The SDK must ship with at least one complete sample project that proves the intended workflow end to end. Examples must show binding generation, connection setup, auth/token handling, subscriptions, cache reads, row callbacks, and reducer invocation in a real Godot context.

Examples should optimize for transferability:

- practical quickstart for first-time adopters,
- realistic sample structure for real project integration,
- and documentation/examples written so the future `GDScript` runtime can follow the same conceptual flow even if implementation details differ.

### Migration Guide

The documentation must include migration guidance for the most likely adoption paths:

- moving from no SDK / custom protocol work,
- moving from the community plugin,
- and upgrading across supported SpacetimeDB or SDK releases.

The migration story must make the architecture stance explicit: `.NET` is the first delivery runtime, but the SDK's product model is being built so future `GDScript` support extends the same concepts rather than replacing them.

### Implementation Considerations

V1 should still prioritize core SDK correctness over broad editor tooling. The committed MVP editor scope is limited to setup, validation, status, and recovery surfaces that remove real setup friction. Deeper diagnostics shells and runtime-inspector views should stay post-MVP unless they become necessary to support the documented workflow without maintainer intervention.

Release engineering is part of the product. Version support, compatibility notes, regeneration guidance, sample validation, and predictable release packaging are required for this SDK to be credible as a developer tool.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** problem-solving MVP with production-credible core infrastructure

The MVP is not trying to prove general market excitement through breadth. It is trying to prove that Godot developers can use SpacetimeDB seriously through a supported SDK path that works. It should optimize for correctness, credibility, and end-to-end usability rather than feature count.

**Resource Requirements:** one strong primary maintainer/developer with Godot, `.NET`, and SpacetimeDB integration skills is enough to reach MVP if scope is kept tight. Additional help in docs, testing, and sample-project validation improves reliability but should not be required to define the first release.

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**

- primary developer successful install and end-to-end integration
- primary developer recovery from normal versioning or setup failures
- external developer self-serve onboarding through docs and sample
- maintainer release/update workflow for supported versions

**Must-Have Capabilities:**

- Godot `.NET`-first SDK/plugin for SpacetimeDB `2.1+`
- architecture designed from day one to support future native `GDScript` without core rewrites
- generated binding workflow aligned with official C# concepts
- connection lifecycle management
- authentication, token persistence, and token resume
- subscriptions and synchronized local cache access
- row update callbacks
- reducer invocation and reducer event/result handling
- Godot-friendly API surface that stays conceptually aligned with official SpacetimeDB clients
- one working sample project
- installation guide, quickstart, troubleshooting guidance, and compatibility matrix
- committed setup, validation, status, and recovery plugin surfaces for the supported workflow
- reproducible release packaging and basic validation of critical flows

### Post-MVP Features

**Phase 2 (Post-MVP):**

- improved onboarding and migration guides
- stronger automated compatibility testing
- broader platform validation beyond the initial supported targets
- diagnostics event logs, subscription/runtime inspectors, and other editor ergonomics beyond the committed MVP surfaces
- clearer support workflows for upgrades and release cadence
- possible AssetLib distribution once packaging is mature

**Phase 3 (Expansion):**

- native `GDScript` runtime implementation under the same overall product model
- broader parity between `.NET` and `GDScript` runtimes where justified
- web-compatible path through non-`.NET` runtime support
- expanded upstream feature coverage such as additional procedure or advanced event surfaces if real adoption requires them
- maturation into the default Godot client path for SpacetimeDB

### Risk Mitigation Strategy

**Technical Risks:**  
The largest technical risk is building the `.NET` runtime in a way that later forces `GDScript` redesign, or weakening the `.NET` implementation to preserve artificial symmetry. Mitigation: keep one repo, allow runtime-specific implementations where needed, and evaluate major design decisions against both runtime-expansion and no-regression criteria.

A second technical risk is version drift across Godot and SpacetimeDB. Mitigation: explicit compatibility matrix, sample-backed validation, repeatable release flow, and clear regeneration/update guidance.

**Market Risks:**  
The biggest market risk is that the SDK solves the problem only for its maintainer and never looks credible to outside adopters. Mitigation: public releases, self-serve docs, realistic sample project, and a product stance clearly aligned with official SpacetimeDB concepts.

**Resource Risks:**  
The biggest resource risk is trying to deliver `.NET`, `GDScript`, broad platform support, and polished tooling all at once. Mitigation: keep MVP focused on the `.NET` runtime and the shared architecture contract, defer nonessential ergonomics, and treat future `GDScript` support as a protected architectural requirement rather than an immediate delivery commitment.

## Functional Requirements

### SDK Installation & Onboarding

- FR1: Developers can install the SDK into a supported Godot project.
- FR2: Developers can identify which Godot and SpacetimeDB versions are supported by a given SDK release.
- FR3: Developers can follow a documented quickstart to reach a first working integration.
- FR4: Developers can validate that the SDK is installed and configured correctly before building gameplay features.
- FR5: Developers can use sample materials that demonstrate the supported end-to-end workflow.

### Schema & Binding Workflow

- FR6: Developers can generate client bindings for a SpacetimeDB module for use in Godot.
- FR7: Developers can regenerate bindings when the server schema changes.
- FR8: Developers can understand which generated bindings correspond to tables, reducers, events, and related schema concepts exposed by the SDK.
- FR9: Developers can detect when generated client bindings and the target server schema are incompatible.
- FR10: Developers can use a binding model that remains conceptually stable across supported SDK runtimes.

### Connection & Identity Management

- FR11: Developers can configure the SDK to connect to a target SpacetimeDB deployment.
- FR12: Developers can establish a client connection from Godot to a supported SpacetimeDB database.
- FR13: Developers can observe connection lifecycle changes relevant to application behavior.
- FR14: Developers can authenticate a client session using supported SpacetimeDB identity flows.
- FR15: Developers can persist and reuse authentication state where supported.
- FR16: Developers can recover from common connection and identity failures using documented SDK behavior.

### Data Subscription & Local State Access

- FR17: Developers can subscribe to server data through the SDK.
- FR18: Developers can receive initial synchronized state for active subscriptions.
- FR19: Developers can access synchronized local client state from Godot code.
- FR20: Developers can observe row-level changes relevant to subscribed data.
- FR21: Developers can change or replace active subscriptions during application runtime.
- FR22: Developers can detect subscription failures or invalid subscription states.

### Reducer Invocation & Runtime Interaction

- FR23: Developers can invoke SpacetimeDB reducers through the SDK.
- FR24: Developers can receive reducer-related results, events, or status information needed by gameplay code.
- FR25: Developers can connect SDK callbacks and events to normal Godot application flow.
- FR26: Developers can use the SDK for real gameplay/runtime interactions without writing custom protocol-layer code.
- FR27: Developers can distinguish between successful runtime operations and recoverable failures.

### Documentation, Troubleshooting & Migration

- FR28: Developers can find documentation for installation, setup, binding generation, connection flow, and runtime usage.
- FR29: Developers can troubleshoot common integration failures using SDK documentation and examples.
- FR30: Developers can identify how to upgrade between supported SDK releases.
- FR31: Developers can identify how to adapt existing projects from custom integrations or community plugin usage to this SDK.
- FR32: Developers can understand the intended relationship between the SDK's Godot-facing model and official SpacetimeDB concepts.

### Release, Compatibility & Maintainer Operations

- FR33: Maintainers can publish versioned SDK releases for external use.
- FR34: Maintainers can define and communicate the compatibility status of each SDK release.
- FR35: Maintainers can validate the core supported workflow against the documented version matrix before release.
- FR36: Maintainers can use sample-backed validation to detect regressions in critical SDK flows.
- FR37: Maintainers can document changes that affect adopters, including compatibility-impacting changes.
- FR38: Maintainers can support a repeatable release/update workflow as Godot and SpacetimeDB evolve.

### Multi-Runtime Product Continuity

- FR39: The product can deliver a `.NET` runtime without defining the SDK's core concepts in `.NET`-only terms.
- FR40: The product can add a native `GDScript` runtime in a later phase without requiring a rewrite of the core product model.
- FR41: Developers can understand a consistent high-level SDK mental model across supported runtimes.
- FR42: The product can support runtime-specific implementations in one repository without fragmenting documentation, support policy, or product identity.

## Non-Functional Requirements

### Performance

- NFR1: The SDK must support a first successful sample integration workflow, from install through live subscription update, without requiring excessive manual setup or debugging beyond the documented process.
- NFR2: Runtime operations exposed through the SDK must be responsive enough for normal real-time gameplay usage in supported target environments.
- NFR3: Binding generation, connection setup, subscription updates, cache access, and reducer invocation must be practical for day-to-day development workflows and real project use.
- NFR4: The SDK must not require developers to introduce custom protocol-layer workarounds to achieve acceptable runtime behavior in supported scenarios.

### Security

- NFR5: Authentication tokens and related identity state must be treated as sensitive data in SDK behavior and documentation.
- NFR6: The SDK must document how authentication state is stored, reused, and cleared in supported workflows.
- NFR7: The SDK must not encourage insecure default handling of credentials or connection state.
- NFR8: Public documentation and sample usage must align with official SpacetimeDB authentication expectations and supported security models.

### Reliability

- NFR9: The documented install, quickstart, and sample workflow must be reproducible for the supported version matrix.
- NFR10: The SDK must provide deterministic behavior for the core supported flows: install, binding generation, connection, auth/token resume, subscriptions, cache access, row callbacks, and reducer invocation.
- NFR11: Common failure states in setup, compatibility, connection, and runtime usage must be diagnosable through documentation, sample comparison, or explicit SDK feedback.
- NFR12: Release packaging and published artifacts must be complete enough that supported adopters can use the SDK without maintainer intervention.

### Integration

- NFR13: The SDK must remain conceptually aligned with official SpacetimeDB client behavior so developers can transfer upstream knowledge into Godot usage.
- NFR14: The SDK must integrate cleanly into normal Godot project structure and workflow for supported runtimes.
- NFR15: The SDK must support a reproducible workflow for local development and for supported hosted SpacetimeDB deployments.
- NFR16: The sample project, documentation, and release artifacts must describe the same supported integration path rather than diverging workflows.

### Maintainability & Compatibility

- NFR17: Each SDK release must explicitly state the supported Godot and SpacetimeDB versions it targets.
- NFR18: The project must maintain a compatibility matrix and update it as supported version pairings change.
- NFR19: The core supported workflow must be validated before release against the documented compatibility targets.
- NFR20: The `.NET` runtime implementation must not create architectural debt that forces a rewrite of the core product model for future native `GDScript` support.
- NFR21: Shared product concepts, generated-binding expectations, and runtime semantics must remain stable enough to support more than one runtime implementation in the same repository.
- NFR22: Runtime-specific implementations may diverge where needed, but that divergence must not fragment the SDK's documentation, support policy, or overall product identity.

### Editor Workflow Quality

- NFR23: The committed plugin/editor surfaces must remain usable in narrow, standard, and wide Godot editor panel widths.
- NFR24: The committed plugin/editor surfaces must support keyboard navigation, visible focus, readable labels, and text or structure-based status messaging rather than color-only cues.
