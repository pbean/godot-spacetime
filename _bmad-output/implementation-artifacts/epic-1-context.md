# Epic 1 Context: Install, Establish the SDK Boundary, and Reach a First Working Connection

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Epic 1 establishes the product's first credible adoption path: a Godot `.NET` addon that installs into a supported project, exposes a runtime-neutral SDK boundary, supports generated bindings as the schema contract, and reaches a first working connection without custom protocol code. This epic matters because the SDK has to look and behave like a real product from day one: explicit support versions, reproducible setup, clear compatibility expectations, and a repository structure that lets `.NET` ship first without forcing future `GDScript` support to rewrite the core model.

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

The supported baseline for the initial release is Godot `4.6.2`, `.NET 8+`, SpacetimeDB `2.1+`, and `SpacetimeDB.ClientSDK` `2.1.0`. The first-use workflow must be reproducible for an external adopter: install the addon into a supported Godot `.NET` project, follow documented setup steps, generate bindings from a module, validate compatibility, configure the target deployment, and reach a first successful connection in one session. The SDK must declare supported versions explicitly and keep installation, sample, and release guidance aligned with that version matrix.

Generated bindings are the canonical schema contract. They are read-only artifacts and must be regenerated when schema changes affect compatibility. Runtime behavior must stay deterministic for install, code generation, compatibility checks, connection setup, and later auth or subscription flows. Common failures in setup, compatibility, or connection must fail clearly with explicit guidance instead of silent drift or maintainer-only knowledge.

The public product model must stay runtime-neutral even though `.NET` ships first. Connection, auth, subscriptions, cache, reducers, lifecycle events, and generated-binding concepts should be described as product concepts, not as `.NET` implementation details. The product ships as a Godot addon/plugin distributed through GitHub Releases first. Only the addon is part of the shipping artifact; demos, generated fixtures, and test harnesses remain outside the addon ZIP.

## Technical Decisions

Repository structure is part of the architecture. The distributable addon root is `addons/godot_spacetime/`, with shipping code under that boundary and docs, demo content, generated fixtures, tests, and scripts outside it. The public SDK boundary is `addons/godot_spacetime/src/Public/`; implementation details live under `src/Internal/`; editor-only surfaces live under `src/Editor/`. Future `.NET`-specific SDK calls must stay isolated under `src/Internal/Platform/DotNet/`.

The Godot-facing API should center on an autoload or service-based boundary rather than scene-local transport ownership. One runtime service owns `DbConnection`, cache mutation, reconnect policy, and main-thread `FrameTick()` advancement. Generated bindings remain consumer-facing artifacts rather than addon runtime source. Naming and layout should stay consistent from the start: addon root uses `snake_case`, event identifiers use normalized lifecycle language, and public versus internal boundaries should be obvious in the tree.

Build and packaging assumptions should support GitHub-release-first distribution. The repo root serves as the Godot development workspace, while release packaging extracts only `addons/godot_spacetime/`. The foundation story should therefore create the official Godot `.NET` plugin shell and root workspace in a way that later stories can extend without repo restructuring.

## UX & Interaction Patterns

Editor surfaces in this epic support the code-first SDK model rather than replace it. Committed plugin UI categories are setup and configuration, code-generation validation, compatibility validation, connection and auth status, and actionable recovery guidance. Status messaging must use explicit lifecycle language and text labels, not color alone. Plugin surfaces need to remain usable in narrow, standard, and wide Godot editor panel widths, and keyboard navigation and visible focus are required for the committed flows.

## Cross-Story Dependencies

Story 1.1 is the base for the rest of the epic because it defines the root Godot workspace, addon location, naming, and version baseline. Story 1.2 extends that scaffold with CI and drift checks. Stories 1.3 through 1.5 lock down public terminology and internal boundaries before deeper runtime work. Stories 1.6 through 1.9 depend on those boundaries to add code generation, compatibility checks, and connection flow without reshaping the repo. Story 1.10 depends on the earlier stories because quickstart validation must exercise the supported install, codegen, compatibility, and connection path end to end.
