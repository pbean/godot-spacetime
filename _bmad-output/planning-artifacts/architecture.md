---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/prd.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/product-brief-godot-spacetime.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/product-brief-godot-spacetime-distillate.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/research/domain-godot-spacetimedb-sdk-plugin-research-2026-04-09.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/research/technical-godot-spacetimedb-sdk-plugin-research-2026-04-09.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/ux-design-specification.md'
  - '/home/pinkyd/dev/godot-spacetime/_bmad-output/planning-artifacts/implementation-readiness-report-2026-04-10.md'
workflowType: 'architecture'
lastStep: 8
status: 'complete'
project_name: 'godot-spacetime'
user_name: 'Pinkyd'
date: '2026-04-09'
completedAt: '2026-04-09'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
The PRD defines 42 functional requirements across eight capability groups: installation/onboarding, schema and binding generation, connection and identity management, subscription and local cache access, reducer/runtime interaction, documentation and migration, release/compatibility operations, and multi-runtime continuity. Architecturally, this means the product is not a narrow networking helper. It must support a complete developer workflow from install through release, with generated bindings and runtime usage treated as core product surfaces rather than implementation details.

The requirements also make clear that the SDK must preserve a stable conceptual model across runtimes. The first release can ship on `.NET`, but the product cannot define its public mental model in `.NET`-only terms if it is expected to support a later native `GDScript` runtime without redesign.

**Non-Functional Requirements:**
The NFR set is dominated by responsiveness for real-time gameplay usage, secure and explicit token handling, deterministic core behavior, reproducible onboarding, alignment with official SpacetimeDB client concepts, and explicit compatibility discipline. The strongest architecture drivers are therefore predictable lifecycle ownership, schema/codegen compatibility management, release validation, documentation fidelity, and runtime-boundary clarity.

This project also treats maintainability as a product requirement. Compatibility matrices, sample-backed regression checks, and clear upgrade guidance are part of the expected system behavior, not post-release process extras.

**Scale & Complexity:**
This is a high-complexity developer-tooling project because it combines runtime integration, generated code workflows, packaging/distribution, support documentation, release operations, and protected future multi-runtime continuity in one product.

- Primary domain: developer tooling / game backend client SDK
- Complexity level: high
- Estimated architectural components: 8 core areas

### Technical Constraints & Dependencies

- The initial product target is SpacetimeDB `2.1+` with a `.NET`-first Godot integration path.
- Generated bindings and official client semantics are foundational dependencies, so schema evolution and upstream client changes directly affect compatibility.
- Runtime behavior must fit Godot's frame-loop and main-thread model; connection advancement, cache mutation, and callback delivery are core architectural concerns.
- Authentication and token persistence are first-class workflow requirements and must be explicit, documented, and security-sensitive.
- GitHub-release-first packaging, plugin installation, a working sample, and a compatibility matrix are part of the expected v1 product shape.
- The committed MVP editor surfaces are limited to setup/configuration, code generation validation, compatibility validation, connection and auth status, and actionable recovery guidance.
- Those committed editor surfaces must remain usable in narrow, standard, and wide Godot editor panel widths with keyboard-first operation for critical setup and recovery flows.
- Web export is intentionally out of scope for the first `.NET` release, but future runtime expansion remains an architectural requirement.

### Cross-Cutting Concerns Identified

- Version and schema compatibility management
- Generated binding workflow and artifact ownership
- Connection lifecycle, reconnection, and failure recovery
- Authentication token security and persistence behavior
- Subscription lifecycle and synchronized local cache semantics
- Row-level callback and reducer event delivery
- Godot integration around frame-loop and main-thread behavior
- Editor workflow clarity, recovery guidance, and accessibility for the committed plugin surfaces
- Documentation, sample fidelity, release engineering, and regression validation

## Starter Template Evaluation

### Primary Technology Domain

Desktop/plugin SDK for Godot, with a `.NET`-first runtime and future native `GDScript` continuity, based on project requirements analysis.

This is not best treated as a generic web, mobile, or API starter-template problem. The closest match is a Godot editor/plugin foundation plus supporting SpacetimeDB development tooling.

### Starter Options Considered

**Option 1: Official Godot `.NET` empty project + built-in plugin scaffold**
This is the strongest v1 starter foundation.

What it provides:
- Current official Godot plugin structure based on `addons/<plugin_name>/` and `plugin.cfg`
- Direct support for creating a C# plugin from the Godot editor
- Alignment with GitHub-release-first plugin packaging and installation expectations
- Minimal architectural assumptions beyond Godot's own plugin model

Architectural implications:
- Keeps the repo centered on the actual deliverable artifact: a Godot plugin/addon
- Avoids introducing game-template assumptions that do not fit an SDK product
- Leaves room to separate editor-facing plugin code, runtime SDK code, samples, and future `GDScript` work cleanly

Maintenance status:
- Backed by current official Godot documentation
- Verified against current latest stable Godot release line `4.6.2`

**Option 2: Official `godot-cpp-template`**
This is a legitimate maintained template, but it is a poor primary v1 starter for this product.

What it provides:
- Official GDExtension quickstart template from `godotengine`
- Preconfigured cross-platform native build workflows
- Demo project and release packaging workflows

Why it is not the right v1 base:
- It optimizes for C++/GDExtension development, not `.NET`-first plugin delivery
- It adds native build complexity before the product has validated the core C#-first contract
- It is better treated as a future-path reference for low-level or native runtime work

Architectural implication:
- Useful as a future reference if native bindings or a lower-level runtime layer become necessary
- Not the right default foundation for the first release

**Option 3: SpacetimeDB CLI project/module templates**
These are useful, but they are supporting starters rather than the main repository starter.

What they provide:
- Current `spacetime init` and `spacetime dev` flows for server module scaffolding
- Sample client/module layouts and generated-binding workflows
- Good support for local integration testing and sample/demo modules

Why they are not the main starter:
- They scaffold SpacetimeDB apps/modules, not a Godot addon/plugin product
- They are better used for sample projects, integration harnesses, and test modules inside the repo
- They do not establish Godot plugin packaging, addon structure, or editor integration as the repo's primary shape

### Selected Starter: Official Godot `.NET` Plugin Scaffold

**Rationale for Selection:**
This is the best foundation for the architecture because it matches the real product artifact and the project's stated constraints.

It keeps the repo anchored to:
- Godot plugin packaging conventions
- `.NET`-first delivery
- official tooling rather than third-party template opinion
- minimal premature structure, which protects the future native `GDScript` path

It also avoids a common failure mode: choosing a starter optimized for games, web apps, or native extensions and then forcing the SDK product to inherit the wrong assumptions.

**Initialization Command:**

```bash
# Create the repo-level solution with an explicit classic .sln file.
dotnet new sln --format sln -n godot-spacetime

# Then create the actual plugin shell in the Godot 4.6.2 .NET editor:
# Project -> Project Settings -> Plugins -> Create New Plugin
# Language: C#
# Activate now: No
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- Godot `.NET` / C# for the first shipping runtime
- Baseline requirement consistent with current Godot docs: `.NET 8+`
- Android export, if later needed, requires `.NET 9+`
- Web export remains out of scope for Godot 4 C# in v1

**Styling Solution:**
- Not applicable in the web-framework sense
- UI/editor surfaces should use Godot `Control` scenes and theme resources, not CSS-based tooling

**Build Tooling:**
- Godot `.NET` editor project as the engine-facing build environment
- External IDE/editor expected for serious C# work
- GitHub Releases aligns with current Godot plugin installation guidance

**Testing Framework:**
- The starter does not force a test framework
- This is a benefit for this project, because SDK validation should be architecture-driven:
  sample-backed integration tests, compatibility checks, and binding-generation verification

**Code Organization:**
- `addons/<plugin_name>/` as the distributable plugin root
- Plugin shell and editor integration live in the addon structure
- Runtime SDK layers, generated bindings, samples, and test harnesses can remain separate from the minimal plugin entrypoint
- This supports one repo without forcing one monolithic implementation shape

**Development Experience:**
- Official plugin-creation flow inside Godot
- Immediate compatibility with standard Godot plugin enable/disable workflow
- Good fit for GitHub ZIP/release installation and later AssetLib readiness
- Keeps the foundation intentionally thin so later architecture decisions remain explicit

**Note:** Project initialization using this official Godot `.NET` plugin scaffold should be the first implementation story. A SpacetimeDB sample module starter should be treated as a supporting sample/test-harness story, not as the core repository starter.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Runtime core: official `SpacetimeDB.ClientSDK` `2.1.0` under a Godot `.NET` plugin shell targeting Godot `4.6.2` and `.NET 8+`
- Public SDK contract: runtime-neutral Godot-facing service API; the product mental model must not be `.NET`-only
- Execution model: single connection owner, main-thread `FrameTick()` advancement, and signal-based event dispatch into Godot
- Data model: generated bindings plus subscription-backed local cache as the canonical client data source
- Token handling: explicit token storage abstraction; no hidden always-on credential persistence in the core SDK

**Important Decisions (Shape Architecture):**
- One repository with separate plugin, runtime, generated binding, sample, and test areas
- GitHub Actions for validation and GitHub Releases for distribution
- Local standalone SpacetimeDB for development and Maincloud-compatible hosted support
- Structured SDK logging and explicit compatibility-matrix ownership

**Deferred Decisions (Post-MVP):**
- Native `GDScript` runtime implementation
- Web-export-compatible runtime path
- AssetLib distribution
- Diagnostics/event-log and subscription/runtime-inspector tooling beyond the committed MVP editor surfaces
- Broad mobile validation beyond the initial supported desktop-first path

### Data Architecture

- Authoritative backend: SpacetimeDB `v2.1.0`
- Client contract: generated C# bindings are canonical; no separate custom REST or GraphQL contract for gameplay/runtime use
- Local reads: subscription-backed client cache exposed through the runtime core
- Writes: reducers first; procedures only where upstream capability or product scope specifically requires them
- Validation strategy: schema-driven compile-time types from generated bindings, plus runtime boundary validation for SDK configuration and reducer inputs
- Migration strategy: additive-first schema evolution, binding regeneration on schema change, and release-by-release compatibility declaration against exact Godot and SpacetimeDB versions

### Authentication & Security

- Authentication method: OIDC/JWT bearer tokens compatible with SpacetimeDB and SpacetimeAuth flows
- Authorization source of truth: server module authorization, not client-side gating
- Token persistence: opt-in storage provider abstraction in the SDK core; sample implementations may persist tokens, but the core runtime should not silently do so
- Transport policy: HTTPS/WSS for hosted environments; standalone/local development is documented as a separate trust zone
- Secrets policy: tokens and credential-bearing headers are redacted from logs and diagnostics by default

### API & Communication Patterns

- Public API shape: autoload/service-based Godot API with signals and scene-safe helper adapters
- Connection model: one long-lived `DbConnection` per configured database session
- Update model: explicit main-thread ownership of `FrameTick()` inside the runtime service
- Error model: typed status/events for gameplay code; exceptions remain infrastructure-level signals rather than the primary gameplay contract
- Subscription model: scoped subscriptions with overlap-first replacement to reduce cache gaps and dropped updates
- Multi-runtime continuity: future native `GDScript` runtime must preserve connection, auth, subscription, cache, and reducer concepts even if implementation details diverge

### Frontend Architecture

- This product is not a traditional frontend application
- The MVP editor surface area is limited to setup/configuration forms, a Code Generation Configuration and Validation Panel, a Compatibility and Validation Panel, a Connection and Auth Status Panel, and inline or panel-based recovery callouts
- Diagnostics/event-log and subscription/runtime-inspector surfaces remain post-MVP unless the documented core workflow proves they are required
- Editor/runtime UI surfaces use Godot `Control` scenes and shared theme resources
- Shared editor components must preserve explicit text-plus-structure status cues, visible keyboard focus, and layout collapse across narrow, standard, and wide editor panel widths
- Runtime state ownership stays in the SDK service layer, not in arbitrary scene nodes
- Scene code consumes SDK events through signals and adapters rather than direct transport objects

### Infrastructure & Deployment

- Development environment: local standalone SpacetimeDB by default
- Hosted environment: Maincloud or equivalent supported hosted deployment
- CI/CD: GitHub Actions for build validation, sample smoke tests, generated-binding checks, and compatibility-matrix verification
- Packaging: GitHub Releases first, with distributable ZIPs centered on the `addons/` plugin structure
- Configuration: explicit project-level settings/resource for host, database, auth, and logging options
- UX validation: committed plugin surfaces are checked for keyboard navigation, non-color-only status cues, and narrow/standard/wide panel behavior as part of implementation validation
- Monitoring/logging: SDK log categories with normal and verbose modes; no mandatory third-party telemetry in v1
- Scaling approach: narrow subscriptions, one connection owner, and exact tested version-pair support rather than vague `2.x` compatibility claims

### Decision Impact Analysis

**Implementation Sequence:**
1. Create the Godot `.NET` plugin shell and solution structure
2. Add baseline CI/build/codegen/version-consistency validation so foundational drift fails early
3. Build the runtime core around generated bindings and a single connection owner
4. Add auth/token storage abstraction and configuration resource
5. Add the committed setup, validation, status, and recovery editor surfaces around the SDK boundary
6. Add subscription/cache and reducer event adapters
7. Add sample project and local test module
8. Add release packaging and the compatibility matrix

**Cross-Component Dependencies:**
- Main-thread connection ownership shapes the public API and event model
- Generated bindings and migration policy shape release cadence and compatibility documentation
- Token storage abstraction affects runtime API, sample design, and future `GDScript` portability
- GitHub-release packaging and `addons/` structure constrain repository layout from day one

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
9 areas where AI agents could make incompatible choices:
1. Addon folder and namespace naming
2. Generated-code ownership boundaries
3. Public SDK type and file naming
4. Event, signal, and callback naming
5. Runtime state ownership and mutation rules
6. Configuration and token-storage placement
7. Error/result/logging structure
8. Test and sample placement
9. Sample-module schema naming for owned SpacetimeDB fixtures

### Naming Patterns

**Database Naming Conventions:**
These apply only to sample, fixture, and test SpacetimeDB modules owned by this repo.

- Tables use singular `snake_case`: `player`, `session_token`
- Columns use `snake_case`: `identity_id`, `created_at`
- Foreign keys use `<entity>_id`: `player_id`
- Indexes use `idx_<table>_<column>`: `idx_player_identity_id`

Reason:
This keeps SQL, docs, and generated schema references predictable and avoids mixed `camelCase`/`snake_case` drift in sample modules.

**API Naming Conventions:**
This project does not expose a primary REST or GraphQL surface. “API” here means the public Godot/C# SDK contract.

- Public C# classes, structs, enums, delegates, and methods use `PascalCase`
- Interfaces use `I` prefix: `ITokenStore`
- Async methods use `Async` suffix only when they actually return `Task` or `Task<T>`
- Services end with `Service`: `SpacetimeConnectionService`
- Adapters end with `Adapter`: `GodotSignalAdapter`
- Config resources end with `Settings` or `Config`, not both for the same concept:
  `SpacetimeSettings`
- Result objects end with `Result`
- Error objects end with `Error`
- Event payload objects end with `Event`

**Code Naming Conventions:**
- Addon root folder uses `snake_case`: `addons/godot_spacetime`
- C# namespaces use `PascalCase` segments: `GodotSpacetime.Runtime.Auth`
- C# source files use `PascalCase.cs` and match the primary public type name
- Godot scenes, resources, and non-C# asset files use `snake_case`
- Private fields use `_camelCase`
- Parameters and locals use `camelCase`
- Constants use `PascalCase` unless language/tooling requires otherwise

### Structure Patterns

**Project Organization:**
- Distributable plugin code lives under the addon root and is the only code assumed to ship to end users
- Generated bindings live in a dedicated generated subtree and are never hand-edited
- Handwritten wrappers, facades, and adapters live outside the generated subtree
- Editor-only code is isolated from runtime-facing code
- Sample projects and sample modules are separate from the distributable addon
- Tests live outside the shipping addon boundary

**File Structure Patterns:**
- One public C# type per file unless a Godot or generated-code pattern requires otherwise
- Folder structure mirrors namespaces for handwritten C# code
- Shared utilities only exist when at least two runtime areas need them; otherwise keep helpers local to the owning feature
- Configuration assets/resources are grouped under a dedicated config/settings area
- Token storage implementations are grouped under auth/storage, not scattered across runtime features

### Format Patterns

**API Response Formats:**
The SDK should not invent web-style response wrappers. Public runtime operations use one of two patterns:

- Typed return values for synchronous local operations
- Typed result/event objects for connection, auth, subscription, and reducer lifecycle changes

Rules:
- Do not mix raw strings, booleans, and nullable values as the primary error contract
- Recoverable runtime failures surface as typed errors or status events
- Unrecoverable programming faults remain exceptions and should not be hidden

**Data Exchange Formats:**
- External JSON or config payloads use `snake_case` when this repo owns the format
- C# public properties remain `PascalCase`
- Timestamps are UTC and represented externally as ISO 8601 strings
- Runtime time values should use `DateTimeOffset` at boundaries rather than local time
- Booleans remain `true`/`false`; never `0`/`1`
- Null is preferred over magic sentinel strings such as `"none"` or `"unknown"`

### Communication Patterns

**Event System Patterns:**
There are three layers and they must stay aligned:

- Domain event identifiers use lowercase dotted names: `connection.opened`, `auth.token_restored`, `subscription.applied`
- C# event/signal delegate and payload type names use the PascalCase equivalent:
  `ConnectionOpenedEvent`, `SubscriptionAppliedEvent`
- Godot-facing signal concepts must use the same semantic names as the runtime event they represent

Rules:
- Event names describe facts, not commands
- Payloads include only the data needed by consumers
- Payload shapes are stable and additive-first
- Do not create two names for the same lifecycle transition

**State Management Patterns:**
- The connection service is the sole owner of mutable connection/session state
- The runtime core is the sole owner of `DbConnection` advancement and cache mutation
- Scene nodes and feature adapters consume snapshots, queries, and events; they do not mutate transport state directly
- Use explicit lifecycle enums or status objects instead of scattered boolean flags where more than two states exist

Examples:
- Prefer `ConnectionState.Connecting`
- Avoid `IsConnecting`, `HasConnected`, and `NeedsReconnect` spread across multiple classes

### Process Patterns

**Error Handling Patterns:**
- Validate configuration at startup or explicit initialization boundaries
- Validate reducer invocation inputs before dispatch if the boundary is not already strongly typed
- Centralize reconnect and retry policy in the connection service
- Do not implement ad hoc retry loops in feature-specific code
- Distinguish user-facing operational errors from internal diagnostics
- Logs are structured by category: `connection`, `auth`, `subscription`, `reducer`, `codegen`, `compatibility`

**Loading State Patterns:**
- Long-lived runtime flows use explicit states, not generic `is_loading`
- Short-lived UI interactions may use local booleans, but shared runtime services must expose named lifecycle states
- Loading completion is driven by concrete lifecycle events such as `connection.opened` or `subscription.applied`
- Scene code must not infer readiness by timing assumptions or frame counts

### Enforcement Guidelines

**All AI Agents MUST:**
- Treat generated bindings as read-only and extend them only through wrappers, adapters, or partial-safe boundaries explicitly designated for that purpose
- Keep `DbConnection`, cache mutation, and `FrameTick()` ownership in one runtime service boundary
- Follow the naming and folder conventions exactly before introducing any new top-level pattern

**Pattern Enforcement:**
- New code should be checked against namespace, file, and folder conventions during review
- Any new external format must declare its naming and timestamp conventions where it is introduced
- If a feature cannot fit the current pattern, update the architecture document before adding a second convention
- Pattern violations should be corrected at the first touched opportunity rather than allowed to accumulate

### Pattern Examples

**Good Examples:**
- `addons/godot_spacetime/plugin.cfg`
- `GodotSpacetime.Runtime.Connection.SpacetimeConnectionService`
- `GodotSpacetime.Runtime.Auth.ITokenStore`
- `connection.opened`
- `SubscriptionAppliedEvent`
- sample fixture table `session_token` with column `identity_id`

**Anti-Patterns:**
- Editing generated binding files directly
- Mixing `addons/godot-spacetime`, `addons/godot_spacetime`, and `addons/GodotSpacetime`
- Exposing both `OnConnected`, `ConnectionOpened`, and `connection_opened` for the same lifecycle fact without a documented mapping
- Letting scene nodes call `FrameTick()` or own reconnect policy
- Returning `bool` plus `out string` from runtime operations that need structured failure information

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
godot-spacetime/
├── README.md
├── LICENSE
├── .editorconfig
├── .gitattributes
├── .gitignore
├── global.json
├── Directory.Build.props
├── godot-spacetime.sln
├── project.godot
├── icon.svg
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── release.yml
│       └── compatibility.yml
├── addons/
│   └── godot_spacetime/
│       ├── plugin.cfg
│       ├── plugin.cs
│       ├── assets/
│       │   └── icon.svg
│       ├── src/
│       │   ├── Public/
│       │   │   ├── SpacetimeClient.cs
│       │   │   ├── SpacetimeSettings.cs
│       │   │   ├── Auth/
│       │   │   │   └── ITokenStore.cs
│       │   │   ├── Connection/
│       │   │   │   ├── ConnectionState.cs
│       │   │   │   ├── ConnectionStatus.cs
│       │   │   │   └── ConnectionOpenedEvent.cs
│       │   │   ├── Subscriptions/
│       │   │   │   ├── SubscriptionHandle.cs
│       │   │   │   └── SubscriptionAppliedEvent.cs
│       │   │   ├── Reducers/
│       │   │   │   ├── ReducerCallResult.cs
│       │   │   │   └── ReducerCallError.cs
│       │   │   └── Logging/
│       │   │       └── LogCategory.cs
│       │   ├── Internal/
│       │   │   ├── Connection/
│       │   │   │   ├── SpacetimeConnectionService.cs
│       │   │   │   ├── ConnectionStateMachine.cs
│       │   │   │   └── ReconnectPolicy.cs
│       │   │   ├── Auth/
│       │   │   │   ├── MemoryTokenStore.cs
│       │   │   │   ├── ProjectSettingsTokenStore.cs
│       │   │   │   └── TokenRedactor.cs
│       │   │   ├── Subscriptions/
│       │   │   │   ├── SubscriptionRegistry.cs
│       │   │   │   └── SubscriptionQuerySet.cs
│       │   │   ├── Cache/
│       │   │   │   └── CacheViewAdapter.cs
│       │   │   ├── Reducers/
│       │   │   │   └── ReducerInvoker.cs
│       │   │   ├── Events/
│       │   │   │   └── GodotSignalAdapter.cs
│       │   │   ├── Logging/
│       │   │   │   └── SpacetimeLogger.cs
│       │   │   ├── Compatibility/
│       │   │   │   └── SupportedVersionMatrix.cs
│       │   │   └── Platform/
│       │   │       └── DotNet/
│       │   │           ├── SpacetimeSdkConnectionAdapter.cs
│       │   │           ├── SpacetimeSdkSubscriptionAdapter.cs
│       │   │           └── SpacetimeSdkReducerAdapter.cs
│       │   └── Editor/
│       │       ├── GodotSpacetimeEditorPlugin.cs
│       │       ├── Setup/
│       │       │   └── SetupPanel.tscn
│       │       ├── Codegen/
│       │       │   └── CodegenValidationPanel.tscn
│       │       ├── Compatibility/
│       │       │   └── CompatibilityPanel.tscn
│       │       ├── Status/
│       │       │   └── ConnectionAuthStatusPanel.tscn
│       │       └── Shared/
│       │           └── RecoveryCallout.tscn
│       └── thirdparty/
│           └── notices/
├── docs/
│   ├── install.md
│   ├── quickstart.md
│   ├── codegen.md
│   ├── troubleshooting.md
│   ├── migration-from-community-plugin.md
│   ├── compatibility-matrix.md
│   ├── runtime-boundaries.md
│   └── release-process.md
├── demo/
│   ├── DemoMain.tscn
│   ├── DemoMain.cs
│   ├── autoload/
│   │   └── DemoBootstrap.cs
│   ├── generated/
│   │   └── smoke_test/
│   │       └── ModuleBindings.cs
│   ├── scenes/
│   │   ├── connection_smoke.tscn
│   │   └── reducer_smoke.tscn
│   └── assets/
│       └── ui/
├── spacetime/
│   ├── modules/
│   │   ├── smoke_test/
│   │   └── compatibility_fixture/
│   ├── schema/
│   └── config/
├── tests/
│   ├── unit/
│   │   ├── Connection/
│   │   ├── Auth/
│   │   ├── Subscriptions/
│   │   └── Reducers/
│   ├── integration/
│   │   ├── connection_lifecycle/
│   │   ├── token_resume/
│   │   ├── subscription_sync/
│   │   └── reducer_calls/
│   ├── fixtures/
│   │   ├── generated/
│   │   ├── settings/
│   │   └── modules/
│   └── helpers/
├── scripts/
│   ├── codegen/
│   ├── packaging/
│   └── compatibility/
└── _bmad-output/
    └── planning-artifacts/
        └── architecture.md
```

### Architectural Boundaries

**API Boundaries:**
- The public SDK boundary is `addons/godot_spacetime/src/Public/`
- End-user gameplay code may depend only on `Public/` types and the plugin entrypoints
- `Internal/` is implementation-only and may change without changing the intended public contract
- The plugin does not ship application-specific generated bindings; generated module bindings belong to consuming projects, demos, or test fixtures

**Component Boundaries:**
- `Editor/` contains editor-only plugin behavior and must not own runtime networking logic
- `Editor/Setup/`, `Editor/Codegen/`, `Editor/Compatibility/`, and `Editor/Status/` own the committed MVP setup, validation, status, and recovery surfaces
- `Editor/Shared/` owns reusable callouts, status rows, and accessibility helpers shared by committed plugin surfaces
- `Public/` contains stable Godot-facing facades, settings, contracts, and event types
- `Internal/Connection/` owns `DbConnection`, reconnect policy, and lifecycle state
- `Internal/Platform/DotNet/` is the only area that talks directly to `SpacetimeDB.ClientSDK`
- `Internal/Events/` translates runtime facts into Godot-facing signals/events
- `demo/` is a consumer of the plugin, not part of the shipping addon

**Service Boundaries:**
- `SpacetimeClient` is the top-level service boundary exposed to Godot consumers
- Token persistence crosses only through `ITokenStore`
- Reducer invocation crosses only through the reducer service/invoker layer
- Subscription registration crosses only through the subscription registry/service boundary

**Data Boundaries:**
- SpacetimeDB is the only authoritative backend data source
- Generated bindings in `demo/generated/` and `tests/fixtures/generated/` are read-only artifacts
- Cache access stays behind runtime adapters; scenes and demos consume exposed queries/events rather than mutate cached transport state directly
- Compatibility and schema fixture modules in `spacetime/modules/` are test assets, not addon runtime code

### Requirements to Structure Mapping

**Feature/FR Mapping:**
- SDK Installation & Onboarding
  - `README.md`
  - `docs/install.md`
  - `docs/quickstart.md`
  - `addons/godot_spacetime/plugin.cfg`
  - `.github/workflows/release.yml`

- Schema & Binding Workflow
  - `docs/codegen.md`
  - `scripts/codegen/`
  - `spacetime/modules/`
  - `demo/generated/`
  - `tests/fixtures/generated/`

- Connection & Identity Management
  - `addons/godot_spacetime/src/Public/Auth/`
  - `addons/godot_spacetime/src/Public/Connection/`
  - `addons/godot_spacetime/src/Internal/Auth/`
  - `addons/godot_spacetime/src/Internal/Connection/`

- Data Subscription & Local State Access
  - `addons/godot_spacetime/src/Public/Subscriptions/`
  - `addons/godot_spacetime/src/Internal/Subscriptions/`
  - `addons/godot_spacetime/src/Internal/Cache/`

- Reducer Invocation & Runtime Interaction
  - `addons/godot_spacetime/src/Public/Reducers/`
  - `addons/godot_spacetime/src/Internal/Reducers/`
  - `addons/godot_spacetime/src/Internal/Events/`

- Editor Workflow & Recovery UX
  - `addons/godot_spacetime/src/Editor/Setup/`
  - `addons/godot_spacetime/src/Editor/Codegen/`
  - `addons/godot_spacetime/src/Editor/Compatibility/`
  - `addons/godot_spacetime/src/Editor/Status/`
  - `addons/godot_spacetime/src/Editor/Shared/`
  - `docs/quickstart.md`
  - `docs/troubleshooting.md`

- Documentation, Troubleshooting & Migration
  - `docs/troubleshooting.md`
  - `docs/migration-from-community-plugin.md`
  - `docs/runtime-boundaries.md`

- Release, Compatibility & Maintainer Operations
  - `.github/workflows/`
  - `docs/compatibility-matrix.md`
  - `docs/release-process.md`
  - `addons/godot_spacetime/src/Internal/Compatibility/`
  - `scripts/compatibility/`
  - `scripts/packaging/`

- Multi-Runtime Product Continuity
  - `addons/godot_spacetime/src/Public/`
  - `addons/godot_spacetime/src/Internal/Platform/DotNet/`
  - `docs/runtime-boundaries.md`

**Cross-Cutting Concerns:**
- Logging
  - `addons/godot_spacetime/src/Public/Logging/`
  - `addons/godot_spacetime/src/Internal/Logging/`

- Configuration
  - `addons/godot_spacetime/src/Public/SpacetimeSettings.cs`
  - `tests/fixtures/settings/`

- Samples and regression proof
  - `demo/`
  - `tests/integration/`
  - `spacetime/modules/`

### Integration Points

**Internal Communication:**
- Demo scenes call into `Public/SpacetimeClient`
- `Public/` facades delegate to `Internal/` services
- `Internal/` services use `Platform/DotNet/` adapters for official SDK calls
- `Internal/Events/` publishes normalized lifecycle events back to `Public/` types and Godot signals

**External Integrations:**
- `Platform/DotNet/` integrates with `SpacetimeDB.ClientSDK`
- `scripts/codegen/` integrates with the `spacetime` CLI
- `spacetime/modules/` integrates with local standalone SpacetimeDB and hosted validation targets
- `.github/workflows/` integrates with CI, release packaging, and compatibility checks

**Data Flow:**
1. Config loads through `SpacetimeSettings`
2. `SpacetimeClient` initializes the connection service
3. `Platform/DotNet/` opens and advances the official client connection
4. Subscription data enters the local cache
5. Internal adapters publish normalized events/results
6. Demo or consuming gameplay code reacts via public service calls and signals

### File Organization Patterns

**Configuration Files:**
- Repo-wide build/tooling config stays at root
- End-user plugin config lives in the addon root
- Runtime SDK settings live in `Public/SpacetimeSettings.cs`
- Test-only settings live under `tests/fixtures/settings/`

**Source Organization:**
- Only `addons/godot_spacetime/` is distributable
- `Public/` and `Internal/` separate contract from implementation
- Editor code stays outside runtime code
- Platform-specific SDK integration stays under `Internal/Platform/`

**Test Organization:**
- `tests/unit/` for isolated runtime logic
- `tests/integration/` for lifecycle and end-to-end SDK behavior
- `tests/fixtures/` for generated bindings, modules, and settings used by tests

**Asset Organization:**
- Shipping addon assets stay under `addons/godot_spacetime/assets/`
- Demo-only scenes and art stay under `demo/`
- Third-party notices for redistributed dependencies stay under `addons/godot_spacetime/thirdparty/notices/`

### Development Workflow Integration

**Development Server Structure:**
- The repo root is the Godot development workspace
- `demo/` provides smoke-test entry scenes inside that workspace
- `spacetime/modules/` provides local modules for iterative development and compatibility checks

**Build Process Structure:**
- Godot builds the root workspace for local development
- Release packaging extracts only `addons/godot_spacetime/`
- Code generation scripts refresh demo/test fixture bindings, not addon runtime source

**Deployment Structure:**
- End-user distribution is the packaged addon folder from GitHub Releases
- Demo and test fixtures never ship as part of the addon ZIP
- Compatibility and release workflows operate from root scripts and CI definitions

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
The architecture is internally consistent. Godot `4.6.2`, `.NET 8+`, and `SpacetimeDB.ClientSDK` `2.1.0` fit the chosen `.NET`-first runtime strategy. The decision to isolate official SDK calls in `Internal/Platform/DotNet/` aligns with the requirement to preserve a future native `GDScript` path. The plugin/addon distribution boundary also matches the GitHub-release-first packaging model.

**Pattern Consistency:**
The implementation patterns support the decisions already made. Naming rules, generated-code boundaries, event naming, token-storage abstraction, and main-thread runtime ownership all reinforce the architectural choices instead of competing with them. The patterns are specific enough to reduce agent drift without forcing premature implementation details.

**Structure Alignment:**
The project structure supports the architecture cleanly. `Public/` vs `Internal/` separates stable contract from implementation, `Editor/` is isolated from runtime networking concerns, sample and test fixtures are kept outside the distributable addon, and the structure leaves a clean seam for later runtime expansion.

### Requirements Coverage Validation ✅

**Feature Coverage:**
All eight functional requirement groups have a mapped architectural home:
- installation/onboarding
- schema/codegen workflow
- connection/identity
- subscriptions/cache
- reducer/runtime interaction
- docs/troubleshooting/migration
- release/compatibility operations
- multi-runtime continuity

No functional requirement category is missing an architectural boundary or owner.

**Functional Requirements Coverage:**
The architecture supports all 42 functional requirements at the category level. The public SDK boundary, internal runtime services, sample/demo workspace, codegen/test fixtures, and release/compatibility workflows collectively cover the required developer journey from installation through real runtime use and maintainer operations.

**Non-Functional Requirements Coverage:**
- Performance is addressed through cache-centric reads, scoped subscriptions, and explicit main-thread connection ownership.
- Security is addressed through OIDC/JWT alignment, token redaction, explicit token-store abstraction, and server-side authorization as source of truth.
- Reliability is addressed through typed lifecycle events, centralized reconnect policy, integration-test boundaries, and compatibility-matrix ownership.
- Maintainability is addressed through generated-binding boundaries, one-repo structure, public/internal separation, and release validation workflows.

### Implementation Readiness Validation ✅

**Decision Completeness:**
All critical decisions that block implementation are documented with concrete versions or explicit boundaries. The deferred items are correctly separated from MVP architecture rather than left ambiguous.

**Structure Completeness:**
The structure is specific enough for implementation agents to know where shipping addon code, internal runtime code, tests, docs, scripts, demo content, and SpacetimeDB fixtures belong.

**Pattern Completeness:**
The high-risk conflict points are covered:
- naming
- generated code ownership
- connection ownership
- events/signals
- config/token storage
- logging/error shape
- test/sample placement
- editor surface ownership, accessibility, and responsive layout rules

This is sufficient for coordinated multi-agent implementation.

### Gap Analysis Results

**Critical Gaps:**
- None identified.

**Important Gaps:**
- The exact consumer bootstrap pattern for `SpacetimeClient` is not frozen yet:
  manual setup, helper node, or autoload-assisted registration.
  This is not a blocker because the service boundary and ownership model are already defined.
- The exact release artifact composition is not frozen yet:
  addon-only ZIP vs addon ZIP plus companion docs/sample references.
  This is a release-story detail, not an architectural hole.

**Nice-to-Have Gaps:**
- A later ADR or short follow-up note for public API ergonomics would help implementation consistency.
- A dedicated doc for codegen lifecycle examples would reduce onboarding ambiguity further.

### Validation Issues Addressed

No contradictory decisions or structural conflicts were found during validation.

The two important gaps above are intentionally left as implementation-level choices because the architecture already constrains them enough to avoid divergent designs:
- runtime ownership and public boundary already constrain bootstrap choices
- addon-only distribution boundary already constrains release packaging choices

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- Strong alignment with current official Godot and SpacetimeDB foundations
- Clean separation between public contract, internal runtime, editor code, and fixtures
- Explicit multi-runtime protection without weakening the `.NET`-first implementation
- Good implementation guidance for AI agents through structure and pattern rules

**Areas for Future Enhancement:**
- Finalize public bootstrap ergonomics during implementation
- Add a focused public API ergonomics note if the first implementation surfaces friction
- Expand compatibility automation as the supported matrix grows

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and public/internal boundaries
- Treat generated bindings as read-only
- Centralize connection ownership, reconnect policy, and `FrameTick()` advancement

**First Implementation Priority:**
Create the Godot `.NET` plugin shell, establish the `Public/` and `Internal/` boundaries, and implement the single-owner connection service around `SpacetimeDB.ClientSDK` `2.1.0`.
