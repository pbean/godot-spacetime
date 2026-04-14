---
title: '1.3 Define Runtime-Neutral Public SDK Concepts and Terminology'
type: 'feature'
created: '2026-04-14T00:00:00-07:00'
status: 'done'
baseline_commit: '006e66c'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-2-establish-baseline-build-and-workflow-validation-early.md'
---

# Story 1.3: Define Runtime-Neutral Public SDK Concepts and Terminology

Status: done

## Story

As the SDK maintainer,
I want the public Godot-facing SDK concepts defined in runtime-neutral language,
so that adopters learn one product model even though `.NET` ships first.

## Acceptance Criteria

1. **Given** the initial shipping runtime is `.NET`, **when** the public SDK contract is documented, **then** connection, auth, subscription, cache, reducer, and generated-binding concepts are named and described without requiring `.NET`-specific implementation knowledge.
2. **And** the same concept language is used consistently across public API docs, sample guidance, and architecture notes.
3. **And** adopters can understand the supported workflow without treating upstream `.NET` types as the product's primary mental model.
4. **And** a named public-concepts reference (`docs/runtime-boundaries.md`) uses the same terminology as the public API and sample guidance.

## Deliverables

This story has two concrete outputs:

1. **`docs/runtime-boundaries.md`** — the named runtime-neutral concept reference (AC #4 primary deliverable)
2. **`addons/godot_spacetime/src/Public/` stub C# types** — establish named API surface without any implementation or `SpacetimeDB.ClientSDK` references (AC #1, #2, #3)
3. **`scripts/compatibility/support-baseline.json` update** — add `docs/runtime-boundaries.md` to `required_paths` so the foundation validation lane enforces its presence

The stubs do **not** implement any behavior. Stories 1.4 and 1.5 build on this vocabulary; stories 1.6+ fill in the runtime behavior.

## Tasks / Subtasks

- [x] Task 1 — Create `docs/runtime-boundaries.md` (AC: 1, 2, 3, 4)
  - [x] Write sections covering: Connection, ConnectionState, Auth/ITokenStore, Subscriptions, Cache, Reducers, GeneratedBindings, SpacetimeClient, SpacetimeSettings
  - [x] Use runtime-neutral names throughout; do not mention `DbConnection`, `SpacetimeDB.ClientSDK`, or any `.NET`-SDK type names
  - [x] Reference the exact C# type names from `Public/` so doc and code are in sync
  - [x] Describe the intended workflow: SpacetimeClient (autoload) → ConnectionState events → Subscription → Cache reads → Reducer invocations
  - [x] Include a "Runtime Boundaries" section that names `Internal/Platform/DotNet/` as the isolation zone for future `.NET`-specific implementation details (sets up Story 1.4)
  - [x] Include a "Future Runtime Seam" note naming `addons/godot_spacetime/src/Internal/Platform/` as the location for later runtimes (sets up Story 1.5)

- [x] Task 2 — Create `addons/godot_spacetime/src/Public/Connection/` stubs (AC: 1, 2)
  - [x] `ConnectionState.cs` — enum: `Disconnected`, `Connecting`, `Connected`, `Degraded`; namespace `GodotSpacetime.Connection`
  - [x] `ConnectionStatus.cs` — value record/struct: `State`, `Description`; namespace `GodotSpacetime.Connection`
  - [x] `ConnectionOpenedEvent.cs` — event payload class; namespace `GodotSpacetime.Connection`

- [x] Task 3 — Create `addons/godot_spacetime/src/Public/Auth/` stub (AC: 1, 2)
  - [x] `ITokenStore.cs` — interface with async `GetTokenAsync`, `StoreTokenAsync`, `ClearTokenAsync` members; namespace `GodotSpacetime.Auth`

- [x] Task 4 — Create `addons/godot_spacetime/src/Public/Subscriptions/` stubs (AC: 1, 2)
  - [x] `SubscriptionHandle.cs` — handle class (initially empty besides the namespace/type name); namespace `GodotSpacetime.Subscriptions`
  - [x] `SubscriptionAppliedEvent.cs` — event payload class; namespace `GodotSpacetime.Subscriptions`

- [x] Task 5 — Create `addons/godot_spacetime/src/Public/Reducers/` stubs (AC: 1, 2)
  - [x] `ReducerCallResult.cs` — result value record; namespace `GodotSpacetime.Reducers`
  - [x] `ReducerCallError.cs` — error class; namespace `GodotSpacetime.Reducers`

- [x] Task 6 — Create `addons/godot_spacetime/src/Public/Logging/` stub (AC: 1, 2)
  - [x] `LogCategory.cs` — enum: `Connection`, `Auth`, `Subscription`, `Reducer`, `Codegen`; namespace `GodotSpacetime.Logging`

- [x] Task 7 — Create `addons/godot_spacetime/src/Public/SpacetimeSettings.cs` (AC: 1, 2)
  - [x] `partial class SpacetimeSettings : Resource` with `[Export]` properties: `Host`, `Database`; namespace `GodotSpacetime`
  - [x] Do NOT reference `SpacetimeDB.*` types

- [x] Task 8 — Create `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (AC: 1, 2, 3)
  - [x] `partial class SpacetimeClient : Node` — top-level Godot-facing service boundary; namespace `GodotSpacetime`
  - [x] Stub only: no implementation, no `SpacetimeDB.*` references
  - [x] Add a doc-comment that names this as the autoload entry point and references the concept vocabulary in `docs/runtime-boundaries.md`

- [x] Task 9 — Update `scripts/compatibility/support-baseline.json` (AC: 4)
  - [x] Add `{ "path": "docs/runtime-boundaries.md", "type": "file" }` to `required_paths`

- [x] Task 10 — Verify foundation validation still passes (AC: all)
  - [x] Run `python3 scripts/compatibility/validate-foundation.py` — must exit 0
  - [x] Confirm dotnet build still succeeds (new stubs must compile; no `SpacetimeDB.*` references)

## Dev Notes

### What This Story Is (and Is Not)

**This story is vocabulary + scaffolding.** It creates the named concept set and the named type set that later stories implement. No SpacetimeDB runtime behavior is implemented here.

- **DO**: Create docs and stubs. Add compile-safe skeleton C# types. Document runtime-neutral concepts.
- **DO NOT**: Add `SpacetimeDB.ClientSDK` to the `csproj`. Add any `using SpacetimeDB.*;` references. Implement connection logic, auth flows, or runtime behavior. Create `Internal/` files (that's Story 1.4).

### Build Constraint — No SpacetimeDB.ClientSDK Reference

The `godot-spacetime.csproj` does **not** reference `SpacetimeDB.ClientSDK` yet. It must remain that way after this story. All `Public/` stubs must compile using only:
- `Godot.*` types (available via `Godot.NET.Sdk/4.6.1`)
- `System.*` types
- Their own inter-references within `GodotSpacetime.*`

If you accidentally add a `SpacetimeDB.*` reference, the build will fail and the foundation validation will break.

### File Compilation — No csproj Changes Needed

`godot-spacetime.csproj` already includes all `.cs` files under `addons/godot_spacetime/`:
```xml
<Compile Include="addons/godot_spacetime/**/*.cs" />
```
New `.cs` files placed under `addons/godot_spacetime/src/Public/` are automatically compiled. **Do not modify the csproj.**

### Namespace Conventions

The root namespace is `GodotSpacetime` (set in `csproj` as `<RootNamespace>GodotSpacetime</RootNamespace>`).

Follow the architecture naming rule: "Folder structure mirrors namespaces for handwritten C# code."

Treating `src/Public/` as organizational (not namespace segments), the sub-namespaces are:
| Folder | Namespace |
|--------|-----------|
| `src/Public/` | `GodotSpacetime` |
| `src/Public/Connection/` | `GodotSpacetime.Connection` |
| `src/Public/Auth/` | `GodotSpacetime.Auth` |
| `src/Public/Subscriptions/` | `GodotSpacetime.Subscriptions` |
| `src/Public/Reducers/` | `GodotSpacetime.Reducers` |
| `src/Public/Logging/` | `GodotSpacetime.Logging` |

Root-level Public types (`SpacetimeClient`, `SpacetimeSettings`) live in `GodotSpacetime`.

This is the canonical namespace table. **Story 1.4 must use these same namespaces when creating `Internal/` types.** Any deviation causes fragmentation.

### Architecture: Public vs Internal vs Platform

The architecture draws three hard lines:

1. **`Public/`** — The stable Godot-facing contract. Only these types are part of the consumer API. Story 1.3 creates these stubs.
2. **`Internal/`** — Implementation only. May change without changing the public contract. Story 1.4 creates this layer.
3. **`Internal/Platform/DotNet/`** — The only zone that may reference `SpacetimeDB.ClientSDK` types. Story 1.4 creates the adapter types here.

`docs/runtime-boundaries.md` must name all three zones explicitly so Story 1.4's developer knows which zone owns what.

[Source: architecture.md#Architectural Boundaries]

### Concept Vocabulary for `docs/runtime-boundaries.md`

The doc must define these concepts in **SDK terms**, not `.NET` library terms:

| SDK Concept | C# Type Name | What It Is |
|-------------|-------------|-----------|
| Connection | `SpacetimeClient` (entry point) / `ConnectionState` (lifecycle) | A session link from Godot to a configured SpacetimeDB database |
| Connection Lifecycle | `ConnectionState` enum | `Disconnected` → `Connecting` → `Connected`; can degrade and reconnect |
| Auth / Identity | `ITokenStore` | Token-based session identity; opt-in persistence through the token store abstraction |
| Subscription | `SubscriptionHandle`, `SubscriptionAppliedEvent` | A query scope that keeps a local cache slice synchronized |
| Cache | (no direct public type yet; surfaced through generated bindings) | The local synchronized read model populated by active subscriptions |
| Reducer | `ReducerCallResult`, `ReducerCallError` | A server-side callable procedure; results surface as typed SDK events |
| Generated Bindings | (external to addon; generated per module) | Read-only C# types generated from a SpacetimeDB module schema |
| Configuration | `SpacetimeSettings` | Godot Resource holding host, database, auth, and logging options |

**Critical**: The doc must NOT say "uses `DbConnection` under the hood" or "wraps `SpacetimeDB.ClientSDK`". The `.NET` SDK is an implementation detail confined to `Internal/Platform/DotNet/`. Adopters see only the `GodotSpacetime.*` surface.

[Source: epic-1-context.md#Requirements & Constraints, architecture.md#Core Architectural Decisions]

### SpacetimeClient Must Be a Godot Node

`SpacetimeClient` is the top-level service autoload. It must be a `partial class SpacetimeClient : Node` so it can be registered as an autoload in `project.godot`.

Do **not** make it a plain C# class, `Resource`, or `RefCounted` — it needs to participate in the Godot scene lifecycle for `FrameTick()` advancement (that behavior comes in Story 1.9, but the type must be established now).

### SpacetimeSettings Is a Godot Resource

`SpacetimeSettings` should extend `Resource` and use `[GlobalClass]` and `[Export]` attributes so it can be inspected in the Godot editor. Minimum exported properties for the stub: `Host` (string), `Database` (string).

Story 1.4 will add settings for auth and logging. Keep the stub minimal.

### ITokenStore — async, Task-based

`ITokenStore` is a plain C# interface. Its methods should be `Task`-returning:
```csharp
Task<string?> GetTokenAsync();
Task StoreTokenAsync(string token);
Task ClearTokenAsync();
```
This is the only `System.Threading.Tasks` import needed in the Auth stub — no Godot types required. It keeps the interface runtime-neutral and async-safe.

[Source: architecture.md#Authentication & Security]

### ConnectionState — Four States, No More

Use exactly four states to match the architecture:
```csharp
public enum ConnectionState { Disconnected, Connecting, Connected, Degraded }
```
The architecture mandates: "Use explicit lifecycle enums or status objects instead of scattered boolean flags where more than two states exist" and explicitly names these four states in the Connection Status Panel spec. Do not add states like `Reconnecting` or `Failed` — they are not in the committed architecture.

[Source: architecture.md#State Management Patterns, epics.md Story 1.9 AC]

### Event Naming Pattern

Follow the architecture event naming rules:
- Domain event names use lowercase dotted form: `connection.opened`, `subscription.applied`
- C# payload type names use PascalCase equivalent: `ConnectionOpenedEvent`, `SubscriptionAppliedEvent`
- Godot signals use the same semantic names

Event payload types use the `Event` suffix (per architecture naming conventions). Keep payloads minimal in the stubs — just establish the type names.

[Source: architecture.md#Event System Patterns]

### Validation Lane — support-baseline.json Update

After creating `docs/runtime-boundaries.md`, add it to `scripts/compatibility/support-baseline.json`'s `required_paths` array:
```json
{ "path": "docs/runtime-boundaries.md", "type": "file" }
```
Add it after the existing `docs/codegen.md` entry to keep the paths grouped. The validation script will then enforce its presence on every run.

**Do not add** path checks for individual `Public/` C# files to the baseline — the build already validates them by compiling. Adding them to the JSON baseline would create unnecessary brittleness.

### Git Context: Recent Commits

- `006e66c` feat: establish baseline workflow validation (Story 1.2 — adds scripts/compatibility/, .github/workflows/validate-foundation.yml, spacetime/modules/ and tests/fixtures/ structure)
- `e23e107` feat: scaffold the supported godot plugin foundation (Story 1.1 — establishes addons/godot_spacetime/, GodotSpacetimePlugin.cs, plugin.cfg)

Story 1.2 verification notes: the shared validation lane required tightening after initial implementation (exact-line checks, typed path checks, shared entrypoint for local + CI). Keep that discipline: if you add anything to the validation baseline, use exact-line checks rather than substring matching.

### Project Structure Notes

**Files to create (this story):**
```
docs/runtime-boundaries.md
addons/godot_spacetime/src/Public/SpacetimeClient.cs
addons/godot_spacetime/src/Public/SpacetimeSettings.cs
addons/godot_spacetime/src/Public/Connection/ConnectionState.cs
addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs
addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs
addons/godot_spacetime/src/Public/Auth/ITokenStore.cs
addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs
addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs
addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs
addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs
addons/godot_spacetime/src/Public/Logging/LogCategory.cs
```

**Files to update (this story):**
```
scripts/compatibility/support-baseline.json  — add docs/runtime-boundaries.md to required_paths
```

**Files to NOT touch:**
```
addons/godot_spacetime/GodotSpacetimePlugin.cs  — don't modify the plugin shell
godot-spacetime.csproj                          — no csproj changes needed
scripts/compatibility/validate-foundation.py    — no script changes needed
.github/workflows/validate-foundation.yml      — no CI changes needed
docs/install.md, docs/codegen.md               — no changes needed; terminology is already correct
```

**Alignment with architecture repo structure:**
The architecture document shows this Public/ folder structure as the target:
```
addons/godot_spacetime/src/
  Public/
    SpacetimeClient.cs
    SpacetimeSettings.cs
    Auth/ITokenStore.cs
    Connection/ConnectionState.cs, ConnectionStatus.cs, ConnectionOpenedEvent.cs
    Subscriptions/SubscriptionHandle.cs, SubscriptionAppliedEvent.cs
    Reducers/ReducerCallResult.cs, ReducerCallError.cs
    Logging/LogCategory.cs
```
Story 1.3 creates exactly this set of files. Story 1.4 creates the `Internal/` layer.

[Source: architecture.md#Project Structure (full directory tree)]

### Verification After Implementation

Run both of these and confirm they succeed:
```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
```

The first verifies the baseline lane (including `docs/runtime-boundaries.md` is now present). The second verifies the new stubs compile without `SpacetimeDB.*` references.

If `dotnet build` fails, check for:
- Any `using SpacetimeDB.*;` import (must not exist)
- Any circular type references between stubs (ITokenStore, SpacetimeClient must not reference each other at this stub stage)
- Missing `using System.Threading.Tasks;` in `ITokenStore.cs` (the only non-Godot import needed)

### References

- [Source: architecture.md#Architectural Boundaries] — Public/Internal/Platform zones
- [Source: architecture.md#Naming Patterns] — Namespace and type naming conventions
- [Source: architecture.md#State Management Patterns] — ConnectionState enum requirement
- [Source: architecture.md#Event System Patterns] — Event payload naming
- [Source: architecture.md#Authentication & Security] — ITokenStore async pattern
- [Source: epics.md#Story 1.3] — Acceptance criteria and FR10/FR41 coverage
- [Source: epics.md#Story 1.4] — Isolation story that builds on this vocabulary
- [Source: epics.md#Story 1.5] — GDScript continuity story that validates the seam
- [Source: epic-1-context.md#Requirements & Constraints] — Runtime-neutral model requirement
- [Source: spec-1-2-establish-baseline-build-and-workflow-validation-early.md#Spec Change Log] — Validation lane hardening lessons (exact-line checks, shared entrypoint)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

No blockers. Initial implementation validation gates passed on first run:
- `python3 scripts/compatibility/validate-foundation.py` → Foundation validation passed
- `dotnet build godot-spacetime.sln -c Debug` → Build succeeded, 0 Warnings, 0 Errors

SpacetimeDB reference check confirmed: only doc-comment prose mentions the name — no `using SpacetimeDB.*` imports or `SpacetimeDB.*` type references in any Public/ file.

Review auto-fix verification passed after correcting the public-concepts doc and tightening Story 1.3 contract tests:
- `pytest tests/test_story_1_3_sdk_concepts.py` → Passed
- `python3 scripts/compatibility/validate-foundation.py` → Foundation validation passed
- `dotnet build godot-spacetime.sln -c Debug` → Build succeeded, 0 Warnings, 0 Errors

### Completion Notes List

- Created `docs/runtime-boundaries.md` with full concept vocabulary covering all eight SDK concepts (Connection, ConnectionState, Auth/ITokenStore, Subscriptions, Cache, Reducers, GeneratedBindings, Configuration/SpacetimeSettings, SpacetimeClient), the three structural zones (Public/, Internal/, Internal/Platform/DotNet/), and the Future Runtime Seam note naming `Internal/Platform/` for later runtimes.
- Created 12 C# stub files in `addons/godot_spacetime/src/Public/` covering all required namespaces. All stubs compile with only `Godot.*` and `System.*` imports — zero SpacetimeDB.ClientSDK dependencies.
- Added `docs/runtime-boundaries.md` to `scripts/compatibility/support-baseline.json` required_paths, immediately after the existing `docs/codegen.md` entry.
- No csproj changes needed — `<Compile Include="addons/godot_spacetime/**/*.cs" />` glob picks up all new files automatically.
- All ACs satisfied after review auto-fix: removed runtime-package references from `docs/runtime-boundaries.md`, aligned lifecycle wording with the available public types, and tightened Story 1.3 contract tests so the runtime-neutral doc requirement is enforced.

### File List

- `docs/runtime-boundaries.md` (new)
- `addons/godot_spacetime/src/Public/SpacetimeClient.cs` (new)
- `addons/godot_spacetime/src/Public/SpacetimeSettings.cs` (new)
- `addons/godot_spacetime/src/Public/Connection/ConnectionState.cs` (new)
- `addons/godot_spacetime/src/Public/Connection/ConnectionStatus.cs` (new)
- `addons/godot_spacetime/src/Public/Connection/ConnectionOpenedEvent.cs` (new)
- `addons/godot_spacetime/src/Public/Auth/ITokenStore.cs` (new)
- `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionHandle.cs` (new)
- `addons/godot_spacetime/src/Public/Subscriptions/SubscriptionAppliedEvent.cs` (new)
- `addons/godot_spacetime/src/Public/Reducers/ReducerCallResult.cs` (new)
- `addons/godot_spacetime/src/Public/Reducers/ReducerCallError.cs` (new)
- `addons/godot_spacetime/src/Public/Logging/LogCategory.cs` (new)
- `scripts/compatibility/support-baseline.json` (modified — added docs/runtime-boundaries.md to required_paths)
- `tests/test_story_1_3_sdk_concepts.py` (new)

### Change Log

- 2026-04-14: Story implemented — created `docs/runtime-boundaries.md` (runtime-neutral concept reference), 12 C# public SDK stubs in `addons/godot_spacetime/src/Public/`, and added `docs/runtime-boundaries.md` to `support-baseline.json` required_paths. Foundation validation passes; dotnet build succeeds with 0 warnings and 0 errors.
- 2026-04-14: Senior developer review auto-fix — removed runtime-package leakage from `docs/runtime-boundaries.md`, clarified the lifecycle wording around `ConnectionOpenedEvent`, added the missing Story 1.3 contract-test coverage, updated the story File List, and re-ran pytest/foundation/build validation.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve

### Findings Fixed

- HIGH: `docs/runtime-boundaries.md` exposed `SpacetimeDB.ClientSDK` in the public concept reference, which violated Task 1 and Acceptance Criteria 1 and 3's runtime-neutral documentation requirement.
- MEDIUM: `docs/runtime-boundaries.md` implied `ConnectionOpenedEvent` represented all connection lifecycle transitions even though the available public type only describes the successful-open boundary.
- MEDIUM: `tests/test_story_1_3_sdk_concepts.py` explicitly allowed the public-concepts reference to mention `SpacetimeDB.ClientSDK`, so the story contract regression was not caught automatically.
- MEDIUM: The Dev Agent Record file list omitted `tests/test_story_1_3_sdk_concepts.py`, leaving the implemented review surface incompletely documented.

### Actions Taken

- Removed runtime-package references from `docs/runtime-boundaries.md` and rewrote the lifecycle paragraph so it stays consistent with `ConnectionStatus` and `ConnectionOpenedEvent`.
- Strengthened Story 1.3 contract tests to forbid `SpacetimeDB.ClientSDK` in the public concept reference and to reject the incorrect lifecycle wording.
- Added the missing test file to the story File List and updated review/change-log records to match the fixed implementation.

### Validation

- `pytest tests/test_story_1_3_sdk_concepts.py`
- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`

### Reference Check

- Web fallback reference: Godot `Node` docs — https://docs.godotengine.org/en/4.6/classes/class_node.html
- Web fallback reference: Godot `Resource` docs — https://docs.godotengine.org/en/4.6/classes/class_resource.html
- Web fallback reference: Godot C# `GlobalClass` docs — https://docs.godotengine.org/en/4.6/tutorials/scripting/c_sharp/c_sharp_global_classes.html
