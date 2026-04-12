---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/prd.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/architecture.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/product-brief-godot-spacetime.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/product-brief-godot-spacetime-distillate.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/implementation-readiness-report-2026-04-09.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/implementation-readiness-report-2026-04-10.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/ux-design-specification.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/research/domain-godot-spacetimedb-sdk-plugin-research-2026-04-09.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/research/technical-godot-spacetimedb-sdk-plugin-research-2026-04-09.md'
---

# godot-spacetime - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for godot-spacetime, decomposing the requirements from the PRD, UX Design, and Architecture artifacts into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Developers can install the SDK into a supported Godot project.
FR2: Developers can identify which Godot and SpacetimeDB versions are supported by a given SDK release.
FR3: Developers can follow a documented quickstart to reach a first working integration.
FR4: Developers can validate that the SDK is installed and configured correctly before building gameplay features.
FR5: Developers can use sample materials that demonstrate the supported end-to-end workflow.
FR6: Developers can generate client bindings for a SpacetimeDB module for use in Godot.
FR7: Developers can regenerate bindings when the server schema changes.
FR8: Developers can understand which generated bindings correspond to tables, reducers, events, and related schema concepts exposed by the SDK.
FR9: Developers can detect when generated client bindings and the target server schema are incompatible.
FR10: Developers can use a binding model that remains conceptually stable across supported SDK runtimes.
FR11: Developers can configure the SDK to connect to a target SpacetimeDB deployment.
FR12: Developers can establish a client connection from Godot to a supported SpacetimeDB database.
FR13: Developers can observe connection lifecycle changes relevant to application behavior.
FR14: Developers can authenticate a client session using supported SpacetimeDB identity flows.
FR15: Developers can persist and reuse authentication state where supported.
FR16: Developers can recover from common connection and identity failures using documented SDK behavior.
FR17: Developers can subscribe to server data through the SDK.
FR18: Developers can receive initial synchronized state for active subscriptions.
FR19: Developers can access synchronized local client state from Godot code.
FR20: Developers can observe row-level changes relevant to subscribed data.
FR21: Developers can change or replace active subscriptions during application runtime.
FR22: Developers can detect subscription failures or invalid subscription states.
FR23: Developers can invoke SpacetimeDB reducers through the SDK.
FR24: Developers can receive reducer-related results, events, or status information needed by gameplay code.
FR25: Developers can connect SDK callbacks and events to normal Godot application flow.
FR26: Developers can use the SDK for real gameplay/runtime interactions without writing custom protocol-layer code.
FR27: Developers can distinguish between successful runtime operations and recoverable failures.
FR28: Developers can find documentation for installation, setup, binding generation, connection flow, and runtime usage.
FR29: Developers can troubleshoot common integration failures using SDK documentation and examples.
FR30: Developers can identify how to upgrade between supported SDK releases.
FR31: Developers can identify how to adapt existing projects from custom integrations or community plugin usage to this SDK.
FR32: Developers can understand the intended relationship between the SDK's Godot-facing model and official SpacetimeDB concepts.
FR33: Maintainers can publish versioned SDK releases for external use.
FR34: Maintainers can define and communicate the compatibility status of each SDK release.
FR35: Maintainers can validate the core supported workflow against the documented version matrix before release.
FR36: Maintainers can use sample-backed validation to detect regressions in critical SDK flows.
FR37: Maintainers can document changes that affect adopters, including compatibility-impacting changes.
FR38: Maintainers can support a repeatable release/update workflow as Godot and SpacetimeDB evolve.
FR39: The product can deliver a `.NET` runtime without defining the SDK's core concepts in `.NET`-only terms.
FR40: The product can add a native `GDScript` runtime in a later phase without requiring a rewrite of the core product model.
FR41: Developers can understand a consistent high-level SDK mental model across supported runtimes.
FR42: The product can support runtime-specific implementations in one repository without fragmenting documentation, support policy, or product identity.

### NonFunctional Requirements

NFR1: The SDK must support a first successful sample integration workflow, from install through live subscription update, without requiring excessive manual setup or debugging beyond the documented process.
NFR2: Runtime operations exposed through the SDK must be responsive enough for normal real-time gameplay usage in supported target environments.
NFR3: Binding generation, connection setup, subscription updates, cache access, and reducer invocation must be practical for day-to-day development workflows and real project use.
NFR4: The SDK must not require developers to introduce custom protocol-layer workarounds to achieve acceptable runtime behavior in supported scenarios.
NFR5: Authentication tokens and related identity state must be treated as sensitive data in SDK behavior and documentation.
NFR6: The SDK must document how authentication state is stored, reused, and cleared in supported workflows.
NFR7: The SDK must not encourage insecure default handling of credentials or connection state.
NFR8: Public documentation and sample usage must align with official SpacetimeDB authentication expectations and supported security models.
NFR9: The documented install, quickstart, and sample workflow must be reproducible for the supported version matrix.
NFR10: The SDK must provide deterministic behavior for the core supported flows: install, binding generation, connection, auth/token resume, subscriptions, cache access, row callbacks, and reducer invocation.
NFR11: Common failure states in setup, compatibility, connection, and runtime usage must be diagnosable through documentation, sample comparison, or explicit SDK feedback.
NFR12: Release packaging and published artifacts must be complete enough that supported adopters can use the SDK without maintainer intervention.
NFR13: The SDK must remain conceptually aligned with official SpacetimeDB client behavior so developers can transfer upstream knowledge into Godot usage.
NFR14: The SDK must integrate cleanly into normal Godot project structure and workflow for supported runtimes.
NFR15: The SDK must support a reproducible workflow for local development and for supported hosted SpacetimeDB deployments.
NFR16: The sample project, documentation, and release artifacts must describe the same supported integration path rather than diverging workflows.
NFR17: Each SDK release must explicitly state the supported Godot and SpacetimeDB versions it targets.
NFR18: The project must maintain a compatibility matrix and update it as supported version pairings change.
NFR19: The core supported workflow must be validated before release against the documented compatibility targets.
NFR20: The `.NET` runtime implementation must not create architectural debt that forces a rewrite of the core product model for future native `GDScript` support.
NFR21: Shared product concepts, generated-binding expectations, and runtime semantics must remain stable enough to support more than one runtime implementation in the same repository.
NFR22: Runtime-specific implementations may diverge where needed, but that divergence must not fragment the SDK's documentation, support policy, or overall product identity.
NFR23: The committed plugin/editor surfaces must remain usable in narrow, standard, and wide Godot editor panel widths.
NFR24: The committed plugin/editor surfaces must support keyboard navigation, visible focus, readable labels, and text or structure-based status messaging rather than color-only cues.

### Additional Requirements

- Starter template requirement: initialize the product from the official Godot `.NET` plugin scaffold, and treat creation of the plugin shell and solution structure as the first implementation story.
- Version baseline requirement: target Godot `4.6.2`, `.NET 8+`, SpacetimeDB `2.1+`, and `SpacetimeDB.ClientSDK` `2.1.0` for the initial shipping runtime.
- Scope constraint: v1 ships a `.NET`-first runtime; full native `GDScript` runtime delivery is out of scope for v1.
- Multi-runtime continuity requirement: keep the public SDK mental model, generated-binding concepts, connection lifecycle, auth, subscription, cache, and reducer semantics runtime-neutral so a later `GDScript` runtime does not require a core product rewrite.
- Repository structure requirement: keep the product in one repository, while allowing runtime-specific implementations where needed without fragmenting documentation, support policy, or product identity.
- Distribution requirement: package the SDK as a Godot addon/plugin and distribute it through GitHub Releases first; AssetLib distribution is explicitly deferred until packaging is mature.
- Platform constraint: Godot 4 C# web export is out of scope for v1 and must not be implied as supported.
- Code generation requirement: use generated bindings as the canonical schema contract, treat them as read-only artifacts, and regenerate them whenever schema changes affect client compatibility.
- Runtime ownership requirement: centralize `DbConnection`, cache mutation, reconnect policy, and main-thread `FrameTick()` advancement inside one runtime service boundary.
- API shape requirement: expose an autoload/service-based Godot API with signals and scene-safe helper adapters instead of letting scene nodes manage low-level transport objects directly.
- Data model requirement: use the subscription-backed local cache as the canonical client read model and reducers as the primary write path.
- Subscription lifecycle requirement: support scoped subscriptions with overlap-first replacement to reduce dropped updates and cache gaps during runtime query changes.
- Authentication requirement: support OIDC/JWT bearer token flows compatible with SpacetimeDB and SpacetimeAuth, with explicit token storage abstractions rather than hidden persistence.
- Security/logging requirement: redact tokens and credential-bearing values from logs by default and treat server-side authorization as the source of truth.
- Environment requirement: support both local standalone SpacetimeDB for development and Maincloud or equivalent hosted deployments for supported remote usage.
- Documentation requirement: ship installation, quickstart, codegen, troubleshooting, migration, runtime-boundaries, compatibility-matrix, and release-process documentation as first-class deliverables.
- Validation requirement: include GitHub Actions or equivalent CI coverage for build validation, sample smoke tests, generated-binding checks, and compatibility-matrix verification before release.
- Packaging boundary requirement: distribute only the addon/plugin as the shipping artifact; sample projects, generated demo/test bindings, and test fixtures stay outside the addon ZIP.
- Licensing/notices requirement: keep plugin licensing, official SDK dependency notices, and backend licensing posture clearly separated in shipped documentation and notices.

### UX Design Requirements

UX1: The MVP plugin/editor workflow must include setup and configuration forms plus dedicated surfaces for code generation validation, compatibility validation, connection/auth status, and actionable recovery guidance.
UX2: The committed plugin/editor workflow must support the code-first SDK model rather than replace runtime APIs with editor-only flows.
UX3: MVP status and recovery surfaces must use explicit lifecycle language, exact failure reasons, and visible next actions rather than vague labels or color-only signals.
UX4: The committed MVP plugin/editor surfaces must remain usable in narrow, standard, and wide Godot editor panel widths.
UX5: The committed MVP plugin/editor surfaces must support keyboard-accessible navigation, visible focus, readable labels, and structured validation messages.
UX6: Diagnostics/event-log and subscription/runtime-inspector surfaces are intentionally post-MVP unless implementation proves they are required to unblock the supported workflow.

### FR Coverage Map

FR1: Epic 1 - Install the SDK into a supported Godot project.
FR2: Epic 1 - Identify supported Godot and SpacetimeDB versions.
FR3: Epic 1 - Follow a quickstart to first working integration.
FR4: Epic 1 - Validate installation and configuration.
FR5: Epic 5 - Use sample materials that demonstrate the supported workflow.
FR6: Epic 1 - Generate client bindings for a SpacetimeDB module in Godot.
FR7: Epic 1 - Regenerate bindings when the server schema changes.
FR8: Epic 1 - Understand generated bindings and exposed schema concepts.
FR9: Epic 1 - Detect incompatibility between generated bindings and the target schema.
FR10: Epic 1 - Preserve a conceptually stable binding model across runtimes.
FR11: Epic 1 - Configure the SDK for a target SpacetimeDB deployment.
FR12: Epic 1 - Establish a client connection from Godot.
FR13: Epic 1 - Observe connection lifecycle changes.
FR14: Epic 2 - Authenticate a client session using supported identity flows.
FR15: Epic 2 - Persist and reuse authentication state.
FR16: Epic 2 - Recover from common connection and identity failures.
FR17: Epic 3 - Subscribe to server data through the SDK.
FR18: Epic 3 - Receive initial synchronized state for active subscriptions.
FR19: Epic 3 - Access synchronized local client state from Godot code.
FR20: Epic 3 - Observe row-level changes for subscribed data.
FR21: Epic 3 - Change or replace active subscriptions during runtime.
FR22: Epic 3 - Detect subscription failures or invalid states.
FR23: Epic 4 - Invoke SpacetimeDB reducers through the SDK.
FR24: Epic 4 - Receive reducer-related results, events, or status information.
FR25: Epic 4 - Connect SDK callbacks and events to normal Godot flow.
FR26: Epic 4 - Use the SDK for real gameplay interactions without custom protocol work.
FR27: Epic 4 - Distinguish successful runtime operations from recoverable failures.
FR28: Epic 5 - Find documentation for installation, setup, codegen, connection flow, and runtime usage.
FR29: Epic 5 - Troubleshoot common integration failures using documentation and examples.
FR30: Epic 5 - Upgrade between supported SDK releases.
FR31: Epic 5 - Adapt existing projects from custom integrations or community plugin usage.
FR32: Epic 5 - Understand the relationship between the Godot-facing model and official SpacetimeDB concepts.
FR33: Epic 6 - Publish versioned SDK releases for external use.
FR34: Epic 6 - Define and communicate compatibility status for each release.
FR35: Epic 6 - Validate the supported workflow against the documented version matrix before release.
FR36: Epic 6 - Use sample-backed validation to detect regressions.
FR37: Epic 6 - Document changes that affect adopters, including compatibility-impacting changes.
FR38: Epic 6 - Support a repeatable release and update workflow.
FR39: Epic 1 - Deliver a `.NET` runtime without defining the product in `.NET`-only terms.
FR40: Epic 1 - Add a native `GDScript` runtime later without rewriting the core product model.
FR41: Epic 1 - Preserve a consistent high-level mental model across runtimes.
FR42: Epic 1 - Support runtime-specific implementations in one repository without fragmenting documentation, support policy, or product identity.

## Epic List

### Epic 1: Install, Establish the SDK Boundary, and Reach a First Working Connection

Developers can install the SDK, confirm compatibility, establish the runtime-neutral product boundary, generate bindings, understand the generated surface, and establish an initial connection in Godot.
**FRs covered:** FR1, FR2, FR3, FR4, FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR39, FR40, FR41, FR42

### Epic 2: Authenticate and Sustain a Session

Developers can authenticate, persist and resume identity, and recover from common connection and session failures.
**FRs covered:** FR14, FR15, FR16

### Epic 3: Subscribe and Read Live Game State

Developers can subscribe to data, receive synchronized state, read the local cache, observe row updates, and evolve subscriptions during runtime.
**FRs covered:** FR17, FR18, FR19, FR20, FR21, FR22

### Epic 4: Invoke Reducers and Drive Gameplay Through SDK Events

Developers can invoke reducers, receive runtime results and events, and integrate SDK behavior into normal Godot gameplay without custom protocol plumbing.
**FRs covered:** FR23, FR24, FR25, FR26, FR27

### Epic 5: Onboard, Troubleshoot, and Migrate with Confidence

Developers can self-serve through docs, sample materials, troubleshooting, upgrade guidance, migration guidance, and a clear explanation of how the Godot model maps to official SpacetimeDB concepts.
**FRs covered:** FR5, FR28, FR29, FR30, FR31, FR32

### Epic 6: Publish and Operate a Trusted SDK Release

Maintainers can publish compatibility guidance, package and validate release candidates, publish approved releases, and communicate changes through a repeatable release workflow.
**FRs covered:** FR33, FR34, FR35, FR36, FR37, FR38

## Epic 1: Install, Establish the SDK Boundary, and Reach a First Working Connection

Developers can install the SDK, confirm compatibility, establish the runtime-neutral product boundary, generate bindings, understand the generated surface, and establish an initial connection in Godot.

### Story 1.1: Scaffold the Supported Godot Plugin Foundation

As the SDK maintainer,
I want the repository initialized as an official Godot `.NET` addon with explicit version targets,
So that adopters start from a supported, installable foundation.

**Implements:** FR1, FR2

**Acceptance Criteria:**

**Given** a fresh repository for the SDK
**When** the plugin foundation is initialized
**Then** a repo-level classic `godot-spacetime.sln` exists at the repository root
**And** the repo contains a Godot `.NET` addon shell created from the official Godot plugin scaffold under `addons/<plugin_name>/` with `plugin.cfg` and a C# plugin entrypoint
**And** the initial support baseline for Godot `4.6.2`, `.NET 8+`, and SpacetimeDB `2.1+` is declared in project docs or release metadata
**And** the repository bootstrap guidance states the required `.NET` dependency restore expectation and any initial Godot project configuration needed before later validation or code-generation workflows run
**And** the addon can be enabled in a supported Godot `.NET` project without ad hoc folder restructuring

### Story 1.2: Establish Baseline Build and Workflow Validation Early

As the SDK maintainer,
I want baseline automation for build, repository readiness, and support-version consistency in place before deeper runtime work,
So that foundational drift fails early and later workflow checks can extend one validation path instead of starting from scratch.

**Implements:** NFR9, NFR19

**Acceptance Criteria:**

**Given** the scaffolded repo and declared support targets
**When** baseline validation runs on a candidate change
**Then** it builds the solution and addon entrypoint through CI or equivalent automation
**And** it verifies that the documented prerequisites, scripts, and fixture or module inputs needed for later binding-generation validation are present and discoverable without requiring the code-generation workflow itself to exist yet
**And** it fails clearly when support-version declarations drift out of sync across docs, scripts, or validation configuration
**And** later binding-generation and release-hardening validation can extend the same workflow rather than replacing it with a separate manual-only process

### Story 1.3: Define Runtime-Neutral Public SDK Concepts and Terminology

As the SDK maintainer,
I want the public Godot-facing SDK concepts defined in runtime-neutral language,
So that adopters learn one product model even though `.NET` ships first.

**Implements:** FR10, FR41

**Acceptance Criteria:**

**Given** the initial shipping runtime is `.NET`
**When** the public SDK contract is documented
**Then** connection, auth, subscription, cache, reducer, and generated-binding concepts are named and described without requiring `.NET`-specific implementation knowledge
**And** the same concept language is used consistently across public API docs, sample guidance, and architecture notes
**And** adopters can understand the supported workflow without treating upstream `.NET` types as the product's primary mental model
**And** a named public-concepts reference such as `docs/runtime-boundaries.md` or equivalent uses the same terminology as the public API and sample guidance

### Story 1.4: Isolate the `.NET` Runtime Adapter Behind Internal Boundaries

As the SDK maintainer,
I want the shipping `.NET` runtime isolated behind internal boundaries,
So that v1 can ship on `.NET` without turning the product into a `.NET`-only fork.

**Implements:** FR39, FR42

**Acceptance Criteria:**

**Given** the `.NET` runtime is the first implementation
**When** the runtime boundary is enforced
**Then** direct references to `SpacetimeDB.ClientSDK` remain confined to `Internal/Platform/DotNet/` in the shipping addon code
**And** public-facing SDK surfaces and editor code depend on stable contracts rather than upstream `.NET` implementation types
**And** the runtime-boundaries reference or equivalent architecture note explicitly names `Internal/Platform/DotNet/` as the `.NET`-specific implementation area while the public SDK and editor surfaces are documented outside that location

### Story 1.5: Verify Future `GDScript` Continuity in Structure and Contracts

As the SDK maintainer,
I want explicit proof that a later native `GDScript` runtime can extend the same product model,
So that future expansion does not require rewriting the public contract.

**Implements:** FR40, FR42

**Acceptance Criteria:**

**Given** the v1 runtime is `.NET`
**When** future-runtime continuity is reviewed
**Then** the architecture identifies a documented extension seam a later native `GDScript` runtime would implement
**And** the committed public concepts and docs do not need renaming or redefinition to support that later runtime
**And** a runtime-boundaries or architecture reference names the intended repository location for a later native `GDScript` runtime implementation

### Story 1.6: Generate and Regenerate Typed Module Bindings

As a Godot developer,
I want to generate and regenerate client bindings from a SpacetimeDB module,
So that my project has typed access to the current schema.

**Implements:** FR6, FR7

**Acceptance Criteria:**

**Given** a supported SpacetimeDB module and the `spacetime` CLI
**When** I run the documented code generation workflow
**Then** generated bindings are created in a dedicated generated location intended for consumer, demo, or test use
**And** rerunning the workflow after a schema change refreshes those generated artifacts without manual edits to generated files
**And** the documented workflow exposes a repeatable command or script for sample or fixture module inputs so automation can run the same generation path without manual repair of generated files

### Story 1.7: Explain Generated Schema Concepts and Validate Code Generation State

As a Godot developer,
I want clear explanations of generated schema concepts plus visible code-generation status and recovery guidance,
So that I can understand the generated surface and diagnose code-generation problems from the supported editor workflow.

**Implements:** FR8, UX1, UX2, UX3, NFR23, NFR24

**Acceptance Criteria:**

**Given** generated bindings and configured code-generation inputs
**When** I inspect the supported code-generation docs or editor surface
**Then** the workflow explains which generated types correspond to tables, reducers, events, and other exposed schema concepts
**And** the code-generation configuration and validation surface shows module source, output location, last generation result, and the next recovery action when configuration or generation fails
**And** the status messaging uses explicit text labels, visible focus, and keyboard-accessible navigation rather than color-only cues
**And** the committed code-generation surface remains usable in narrow, standard, and wide editor panel widths

### Story 1.8: Detect Binding and Schema Compatibility Problems Early

As a Godot developer,
I want stale or incompatible generated bindings to fail clearly,
So that schema drift is actionable instead of mysterious.

**Implements:** FR9, UX1, UX3, NFR23, NFR24

**Acceptance Criteria:**

**Given** generated bindings that no longer match the target schema or supported version pair
**When** I validate or run the integration workflow
**Then** the SDK or tooling reports the incompatibility with the exact failed check plus regeneration or version-guidance message
**And** the failure happens before silent misuse of stale client bindings
**And** the guidance points me to the supported compatibility or regeneration path
**And** the compatibility and validation surface lists current target versions, compatibility status, and the next relevant action using text labels rather than color alone

### Story 1.9: Configure and Open a First Connection from Godot

As a Godot developer,
I want to configure connection settings and observe lifecycle events from Godot,
So that I can verify the SDK connects to my target deployment.

**Implements:** FR11, FR12, FR13, UX1, UX2, UX3, NFR23, NFR24

**Acceptance Criteria:**

**Given** valid generated bindings and supported connection settings
**When** I start the client from Godot
**Then** the SDK establishes a connection to the target SpacetimeDB deployment and surfaces connection lifecycle states or events relevant to application flow
**And** invalid or incomplete settings produce actionable feedback tied to the blocking field or runtime state without requiring custom protocol debugging
**And** connection ownership remains inside the SDK service boundary rather than scene-local transport code
**And** the connection status surface exposes explicit states such as `Disconnected`, `Connecting`, `Connected`, and `Degraded`

### Story 1.10: Validate First Setup Through a Quickstart Path

As a Godot developer,
I want a quickstart validation path for first setup,
So that I can confirm installation and first connection before building gameplay features.

**Implements:** FR3, FR4, UX1, UX4, UX5, NFR23, NFR24

**Acceptance Criteria:**

**Given** a fresh supported Godot `.NET` project
**When** I follow the quickstart and validation steps
**Then** I can install or enable the addon, run code generation, configure the target database, review compatibility status, and reach a first successful connection
**And** the validation flow clearly distinguishes installation, code generation, compatibility, and connection failures with visible recovery actions
**And** the setup and validation surfaces remain usable in narrow, standard, and wide editor panel widths with keyboard-only progression through the primary path

## Epic 2: Authenticate and Sustain a Session

Developers can authenticate, persist and resume identity, and recover from common connection and session failures.

### Story 2.1: Define Auth Configuration and Token Storage Boundaries

As the SDK maintainer,
I want explicit auth settings and a token storage abstraction,
So that session handling is secure, configurable, and not hard-coded to one persistence strategy.

**Implements:** FR15

**Acceptance Criteria:**

**Given** a supported SDK configuration surface
**When** authentication behavior is defined for the runtime
**Then** the SDK exposes explicit auth-related settings and a token storage boundary suitable for supported workflows
**And** default behavior does not silently persist credentials without developer intent
**And** token reuse and clearing behavior are documented at the same boundary

### Story 2.2: Authenticate a Client Session Through Supported Identity Flows

As a Godot developer,
I want to authenticate a client session using supported SpacetimeDB identity flows,
So that my client connects as an identified user instead of an unauthenticated transport.

**Implements:** FR14, UX1, UX3, NFR23, NFR24

**Acceptance Criteria:**

**Given** valid supported authentication input for a target deployment
**When** I start an authenticated session from Godot
**Then** the SDK applies the supported token or identity flow and opens an authenticated client session
**And** identity or session state needed by gameplay code is surfaced through the SDK boundary
**And** authentication failure produces actionable status or error feedback
**And** the connection and auth status surface distinguishes at least `Auth Required`, `Token Restored`, and `Auth Failed` with a recommended next action

### Story 2.3: Restore a Previous Session from Persisted Auth State

As a Godot developer,
I want a previously persisted session restored when supported,
So that returning users can resume without repeating the full auth flow every time.

**Implements:** FR15

**Acceptance Criteria:**

**Given** a valid stored token in the configured token store
**When** the client starts or reconnect logic attempts session restoration
**Then** the SDK reuses the stored auth state through the token storage abstraction
**And** successful token restoration resumes the session without requiring a new manual login step
**And** a missing or invalid stored token falls back cleanly without leaving corrupted session state behind

### Story 2.4: Recover from Common Session and Identity Failures

As a Godot developer,
I want recoverable auth and session failures surfaced predictably,
So that my game can prompt for re-authentication, retry, or clear bad state without guesswork.

**Implements:** FR16, UX1, UX3, NFR24

**Acceptance Criteria:**

**Given** an expired token, rejected identity, or interrupted authenticated session
**When** the SDK encounters the failure during connection or restoration
**Then** it exposes a recoverable failure state or event that gameplay code can handle explicitly
**And** developers can clear or replace the stored auth state through the supported SDK path
**And** recoverable operational failures are distinguishable from unrecoverable programming faults
**And** the recovery surface identifies the likely cause plus whether retry, re-authentication, or token clearing is the recommended next step

## Epic 3: Subscribe and Read Live Game State

Developers can subscribe to data, receive synchronized state, read the local cache, observe row updates, and evolve subscriptions during runtime.

### Story 3.1: Apply a Subscription and Receive Initial Synchronized State

As a Godot developer,
I want to subscribe to server data from the SDK,
So that my client receives the initial synchronized state for the queries it depends on.

**Implements:** FR17, FR18

**Acceptance Criteria:**

**Given** an active supported client session and a valid subscription query set
**When** I apply the subscription through the SDK
**Then** the client receives the initial synchronized state for the subscribed data set
**And** the SDK exposes subscription success in a way gameplay code can observe
**And** the subscription is tracked through a stable SDK-owned handle or boundary

### Story 3.2: Read Synchronized Local Cache Data from Godot Code

As a Godot developer,
I want to access synchronized local client state from Godot code,
So that gameplay systems can read live game data without issuing custom network queries.

**Implements:** FR19

**Acceptance Criteria:**

**Given** a successfully applied subscription with synchronized state
**When** gameplay code reads through the SDK's supported cache-access path
**Then** it can retrieve current client-side state using the generated model
**And** those reads do not require custom protocol-layer calls outside the SDK
**And** cache access remains behind the SDK service boundary rather than direct transport mutation

### Story 3.3: Observe Row-Level Changes for Subscribed Data

As a Godot developer,
I want row-level change notifications for subscribed data,
So that gameplay systems can react to inserts, updates, and removals as the cache changes.

**Implements:** FR20

**Acceptance Criteria:**

**Given** an active subscription and server-side row changes affecting subscribed data
**When** changes arrive at the client
**Then** the SDK emits row-level callbacks or events with enough context for gameplay code to react
**And** the notifications are aligned with the generated data model exposed by the SDK
**And** scene consumers are not required to mutate transport state directly to receive updates

### Story 3.4: Replace Active Subscriptions Safely During Runtime

As a Godot developer,
I want to change or replace active subscriptions during runtime,
So that scene transitions and gameplay state changes can evolve live queries safely.

**Implements:** FR21

**Acceptance Criteria:**

**Given** one or more active subscriptions
**When** I apply a replacement or changed subscription set at runtime
**Then** the SDK supports the transition without requiring a full client restart
**And** the previous subscription set remains authoritative until the replacement set reaches a synchronized state or fails explicitly
**And** the updated subscription state becomes observable to gameplay code through the same SDK boundary

### Story 3.5: Detect Invalid Subscription States and Failures

As a Godot developer,
I want subscription failures and invalid states reported clearly,
So that bad queries or runtime subscription problems are diagnosable and recoverable.

**Implements:** FR22

**Acceptance Criteria:**

**Given** an invalid subscription query, rejected subscription, or runtime subscription failure
**When** the SDK processes the subscription request or lifecycle update
**Then** it surfaces an actionable failure state, event, or message instead of silent desynchronization
**And** valid existing client state is not silently corrupted by the failed subscription change
**And** the response tells the developer whether retry, query correction, or regeneration is the appropriate next step

## Epic 4: Invoke Reducers and Drive Gameplay Through SDK Events

Developers can invoke reducers, receive runtime results and events, and integrate SDK behavior into normal Godot gameplay without custom protocol plumbing.

### Story 4.1: Invoke Generated Reducers from the Godot-Facing SDK

As a Godot developer,
I want to call SpacetimeDB reducers through the Godot-facing SDK,
So that gameplay code can mutate server state without implementing protocol details itself.

**Implements:** FR23, FR26

**Acceptance Criteria:**

**Given** an active supported client session and generated module bindings
**When** gameplay code invokes a reducer through the SDK
**Then** the call is routed through the supported generated reducer path rather than custom protocol code
**And** typed inputs required by the reducer are validated or enforced at the supported boundary
**And** the invocation path is available from normal Godot gameplay code

### Story 4.2: Surface Reducer Results and Runtime Status to Gameplay Code

As a Godot developer,
I want reducer-related results, events, and status surfaced through the SDK,
So that gameplay systems can react to the outcome of mutation attempts.

**Implements:** FR24

**Acceptance Criteria:**

**Given** a reducer invocation has been made
**When** the runtime receives success, failure, or related reducer lifecycle information
**Then** the SDK exposes that outcome through a structured result, event, or status surface
**And** gameplay code can distinguish the reducer operation and invocation instance the outcome belongs to
**And** failure information includes the failure category and a user-safe recovery or feedback path

### Story 4.3: Bridge Runtime Callbacks into Scene-Safe Godot Events

As a Godot developer,
I want connection, subscription, and reducer callbacks bridged into scene-safe Godot events,
So that gameplay code can integrate SDK behavior through normal Godot flow instead of low-level transport objects.

**Implements:** FR25

**Acceptance Criteria:**

**Given** runtime lifecycle events occur inside the SDK
**When** consuming Godot code subscribes to the supported event surface
**Then** those events are available through Godot-friendly signals or equivalent scene-safe adapters
**And** scene code can respond without taking ownership of transport advancement or reconnect policy
**And** the Godot-facing event names remain semantically aligned with the underlying runtime facts

### Story 4.4: Distinguish Recoverable Runtime Failures from Programming Faults

As a Godot developer,
I want recoverable runtime failures distinguished from programming faults,
So that gameplay code can retry or inform the user appropriately without masking real defects.

**Implements:** FR27

**Acceptance Criteria:**

**Given** a runtime operation fails during reducer invocation or related gameplay interaction
**When** the SDK reports the outcome
**Then** recoverable operational failures are surfaced through structured runtime results or status events
**And** unrecoverable programming faults remain visible as diagnostics or exceptions rather than being silently downgraded
**And** the supported outcome model makes it clear how gameplay code should branch on success versus recoverable failure

## Epic 5: Onboard, Troubleshoot, and Migrate with Confidence

Developers can self-serve through docs, sample materials, troubleshooting, upgrade guidance, migration guidance, and a clear explanation of how the Godot model maps to official SpacetimeDB concepts.

### Story 5.1: Deliver a Sample Foundation for Install, Codegen, and First Connection

As an external Godot developer,
I want a sample project that proves the supported setup path from install through first connection,
So that I can verify the SDK starts from a working baseline before I compare deeper runtime behavior.

**Implements:** FR5, NFR16

**Acceptance Criteria:**

**Given** the current addon source or a candidate addon artifact and the sample project
**When** I open the sample project and follow its setup instructions
**Then** I can install or enable the addon, generate bindings, configure the target deployment, and reach a first successful connection
**And** the sample setup steps match the current install and quickstart docs for that same source or candidate artifact
**And** the sample includes reset or bootstrap instructions so I can reproduce the baseline workflow from a clean starting state without maintainer intervention

### Story 5.2: Extend the Sample Through Auth, Session Resume, and Live Subscription Flow

As an external Godot developer,
I want the sample to cover authenticated live-state behavior,
So that I can compare my integration against a working reference for session and subscription flows.

**Implements:** FR5, NFR16

**Acceptance Criteria:**

**Given** the sample project is configured for a supported deployment
**When** I run the supported authenticated path
**Then** the sample demonstrates auth or token restore, subscription startup, local cache reads, and visible row updates
**And** any auth prerequisites or optional setup are documented next to the sample flow
**And** the runtime flow matches the same lifecycle language and steps described in the docs

### Story 5.3: Demonstrate Reducer Interaction and Troubleshooting Comparison Paths

As an external Godot developer,
I want the sample to show reducer calls and expected recovery behavior,
So that I can compare my runtime integration against known-good mutation flows when debugging.

**Implements:** FR5, NFR16

**Acceptance Criteria:**

**Given** the sample is running against a supported environment
**When** I trigger its documented gameplay interaction path
**Then** the sample demonstrates reducer invocation plus the resulting success or recoverable-failure handling path
**And** the sample documents the expected observable states or messages I should compare during troubleshooting
**And** the sample remains aligned with the supported workflow described in the troubleshooting and runtime docs

### Story 5.4: Publish Core Installation and Runtime Documentation

As an adopting developer,
I want documentation for installation, setup, code generation, connection flow, and runtime usage,
So that I can integrate the SDK self-serve in a supported Godot project.

**Implements:** FR28

**Acceptance Criteria:**

**Given** a fresh supported project and the addon source or a candidate addon artifact
**When** I follow the published documentation
**Then** I can install the addon, understand dependency expectations, generate bindings, configure the target deployment, and use the core runtime surfaces
**And** the docs clearly state the current supported Godot and SpacetimeDB version targets for that source or candidate artifact
**And** the docs reference the sample project as the canonical end-to-end example

### Story 5.5: Publish Troubleshooting Guidance for Setup and Runtime Failures

As an integrating developer,
I want troubleshooting guidance for common setup and runtime failures,
So that installation, auth, subscription, and schema-drift failures are diagnosable in one session.

**Implements:** FR29

**Acceptance Criteria:**

**Given** the current supported workflow docs and sample
**When** I consult the troubleshooting guidance
**Then** I can find documented failure modes for installation, code generation, local compatibility checks, connection, authentication, and subscriptions
**And** the guidance explains when regeneration, environment version changes, or configuration fixes are required
**And** the troubleshooting docs stay aligned with the sample behavior and current runtime terminology

### Story 5.6: Publish Upgrade, Migration, and Concept-Mapping Guides

As a developer adopting or upgrading the SDK,
I want upgrade and migration guides that explain how this SDK maps to official SpacetimeDB concepts,
So that I can move from older setups or unofficial integrations without losing the mental model.

**Implements:** FR30, FR31, FR32

**Acceptance Criteria:**

**Given** an adopter is upgrading SDK versions or moving from custom or community integration code
**When** they follow the published migration guidance
**Then** they can identify the supported upgrade path between SDK releases
**And** they can understand the recommended migration path from custom protocol work or the community plugin to this SDK
**And** the guide explains how the Godot-facing model relates to official SpacetimeDB concepts and how future `GDScript` support fits the same product model

## Epic 6: Publish and Operate a Trusted SDK Release

Maintainers can publish compatibility guidance, package and validate release candidates, publish approved releases, and communicate changes through a repeatable release workflow.

### Story 6.1: Publish the Canonical Compatibility Matrix and Support Policy

As an external adopter,
I want each SDK release to state its exact supported environment,
So that I know whether a given Godot and SpacetimeDB pairing is intended to work before I integrate it.

**Implements:** FR34

**Acceptance Criteria:**

**Given** a published or candidate SDK release
**When** I inspect its compatibility documentation
**Then** I can identify the exact supported Godot and SpacetimeDB versions targeted by that release
**And** the support policy distinguishes supported, experimental, deferred, or out-of-scope targets where relevant
**And** the compatibility matrix and support policy are the canonical source referenced by install docs, troubleshooting docs, release notes, and sample references

### Story 6.2: Package Reproducible Versioned Release Candidates

As the SDK maintainer,
I want reproducible versioned candidate artifacts for the addon,
So that the exact payload intended for adopters can be validated before publication.

**Implements:** NFR12

**Acceptance Criteria:**

**Given** a candidate version and release metadata
**When** I package the SDK for release validation
**Then** the candidate artifact contains the distributable addon structure needed by end users and excludes demo or test-only assets
**And** the candidate artifact is versioned and reproducible so the same payload can later be published through the GitHub-release-first distribution flow
**And** required notices, licensing information, or install metadata needed by adopters are included with the candidate artifact set

### Story 6.3: Validate Release Candidates Against the Supported Workflow

As the SDK maintainer,
I want automated validation to operate on the packaged candidate,
So that only candidate artifacts that pass the supported workflow are approved for publication.

**Implements:** FR35, FR36

**Acceptance Criteria:**

**Given** a packaged release candidate and documented compatibility targets
**When** release validation runs against the documented supported workflow
**Then** it produces a concrete validation output or report covering build validation, generated-binding checks, sample smoke coverage, release-packaging checks, and compatibility-target verification for that candidate
**And** regressions in those flows are surfaced before the release is approved for publication
**And** that validation output or report is the required publication gate consumed by the release process for Story 6.4

### Story 6.4: Publish Approved SDK Releases for External Use

As the SDK maintainer,
I want to publish approved SDK releases from the validated candidate payload,
So that external adopters receive the exact artifact that passed release validation.

**Implements:** FR33

**Acceptance Criteria:**

**Given** a release candidate has passed the supported validation workflow
**When** I publish the SDK release for external adopters
**Then** the official release publishes the exact validated candidate payload rather than a newly rebuilt artifact
**And** the published release metadata and download assets match the validated version, compatibility targets, and adopter-facing install guidance
**And** the release output is suitable for the GitHub-release-first distribution path defined for the product

### Story 6.5: Communicate Release Changes and Maintain Support Continuity

As the SDK maintainer,
I want release communication and support continuity rules that protect adopters across updates,
So that changes remain understandable and the release workflow stays repeatable as compatibility targets evolve.

**Implements:** FR37, FR38

**Acceptance Criteria:**

**Given** a change affects adopters, compatibility, or supported workflow behavior
**When** the release is documented
**Then** the release notes or change log explain the adopter impact, compatibility implications, and any required migration or upgrade action
**And** the support and update guidance references the canonical compatibility matrix and the published release artifact as the source of truth
**And** the release-process reference or checklist records the communication step used for that version so future releases can follow the same path
