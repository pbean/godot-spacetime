# Epic 1 Context: Install, Establish the SDK Boundary, and Reach a First Working Connection

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Epic 1 establishes the first trustworthy adoption path for `godot-spacetime`: a supported Godot `.NET` addon that installs cleanly, declares exact support targets, preserves a runtime-neutral product model, supports generated bindings as the schema contract, and reaches a first working connection without custom protocol work. This epic matters because every later auth, subscription, and reducer story depends on the repo, validation path, terminology, and runtime boundaries looking like a real SDK instead of a collection of one-off integration experiments.

## Stories

- Story 1.1: Scaffold the Supported Godot Plugin Foundation
- Story 1.2: Establish Baseline Build and Workflow Validation Early
- Story 1.3: Define Runtime-Neutral Public SDK Concepts and Terminology
- Story 1.4: Isolate the `.NET` Runtime Adapter Behind Internal Boundaries
- Story 1.5: Verify Future `GDScript` Continuity in Structure and Contracts
- Story 1.6: Generate and Regenerate Typed Module Bindings
- Story 1.7: Explain Generated Schema Concepts and Validate Code Generation State
- Story 1.8: Detect Binding and Schema Compatibility Problems Early
- Story 1.9: Configure and Open a First Connection from Godot
- Story 1.10: Validate First Setup Through a Quickstart Path

## Requirements & Constraints

The initial supported baseline is Godot `4.6.2`, `.NET 8+`, SpacetimeDB `2.1+`, and the planned `SpacetimeDB.ClientSDK` `2.1.0` runtime package. Install, quickstart, and validation guidance must make those support boundaries explicit and keep them consistent across docs, scripts, and automation so maintainers can detect drift before deeper runtime work lands.

The first-use workflow has to be reproducible for an external adopter. A developer should be able to install the addon into a supported Godot project, understand the setup steps, discover the inputs later code generation needs, validate compatibility and readiness, configure a target deployment, and reach a first successful connection without maintainer-only knowledge. Failures in setup, schema compatibility, or connection flow should surface as clear, diagnosable guidance rather than silent or ad hoc behavior.

Generated bindings are the canonical schema contract. They are treated as read-only artifacts and later stories must regenerate them whenever schema changes affect compatibility. Even before the code-generation workflow exists, the repo should already have a validation path that can check for prerequisite assets, documented inputs, and version consistency.

The public product model must stay runtime-neutral even though `.NET` ships first. Connection, auth, subscription, cache, reducer, and generated-binding concepts should read like SDK concepts, not like thin wrappers around upstream `.NET` implementation types. The repo must stay structured so a later native `GDScript` runtime can reuse the same product language and workflow instead of forcing a redesign.

## Technical Decisions

The repository root is the Godot development workspace, and the shipping addon lives under `addons/godot_spacetime/`. Public SDK surface area belongs under `addons/godot_spacetime/src/Public/`, internal implementation under `src/Internal/`, editor-only tooling under `src/Editor/`, and future `.NET` runtime-specific code under `src/Internal/Platform/DotNet/`. That structure is part of the product contract and later stories should extend it instead of restructuring the repo.

The Godot-facing API should center on an autoload or service boundary rather than scene-local transport ownership. One runtime service will later own `DbConnection`, cache mutation, reconnect behavior, and main-thread `FrameTick()` advancement. Generated bindings remain consumer-facing outputs rather than addon runtime source files.

Validation and release hardening are part of the architecture, not follow-up process work. GitHub Actions or equivalent automation should be able to build the solution, verify readiness inputs for later workflows, check support-version consistency, and eventually extend into code-generation, sample smoke, and release checks without replacing the baseline path. Packaging remains GitHub-release-first, and only the addon belongs in the shipping artifact.

## UX & Interaction Patterns

Epic 1 editor surfaces stay code-first and focused on trust-building setup tasks. The committed categories are setup and configuration, code-generation validation, compatibility validation, connection and auth status, and actionable recovery guidance. Status messaging should use explicit lifecycle language with clear next actions instead of vague labels or color-only signals.

Plugin and editor surfaces need to remain usable in narrow, standard, and wide Godot panel widths, with keyboard navigation, visible focus, readable labels, and structured validation messages. Recovery guidance should appear near the point of failure so setup, schema, compatibility, and connection issues are understandable without digging through raw logs.

## Cross-Story Dependencies

Story 1.1 establishes the root workspace, addon location, and support baseline that every later Epic 1 story builds on. Story 1.2 adds the reusable validation lane that later code-generation and release-hardening checks should extend. Stories 1.3 through 1.5 lock the terminology and runtime boundaries before deeper runtime work. Stories 1.6 through 1.9 then add code generation, compatibility validation, and first-connection behavior on top of that foundation. Story 1.10 depends on the earlier stories because quickstart validation must exercise the supported install, validation, code-generation, and connection path end to end.
