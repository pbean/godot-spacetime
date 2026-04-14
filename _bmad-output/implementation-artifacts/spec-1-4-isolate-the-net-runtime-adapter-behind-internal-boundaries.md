---
title: '1.4 Isolate the .NET Runtime Adapter Behind Internal Boundaries'
type: 'feature'
created: '2026-04-14T00:00:00-07:00'
status: 'done'
baseline_commit: '12f19d9'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-1-scaffold-the-supported-godot-plugin-foundation.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-2-establish-baseline-build-and-workflow-validation-early.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-3-define-runtime-neutral-public-sdk-concepts-and-terminology.md'
---

# Story 1.4: Isolate the `.NET` Runtime Adapter Behind Internal Boundaries

Status: done

## Story

As the SDK maintainer,
I want the shipping `.NET` runtime isolated behind internal boundaries,
So that v1 can ship on `.NET` without turning the product into a `.NET`-only fork.

## Acceptance Criteria

1. **Given** the `.NET` runtime is the first implementation, **when** the runtime boundary is enforced, **then** direct references to `SpacetimeDB.ClientSDK` remain confined to `addons/godot_spacetime/src/Internal/Platform/DotNet/` in the shipping addon code.
2. **And** public-facing SDK surfaces and editor code depend on stable contracts rather than upstream `.NET` implementation types — `Public/` types contain zero `SpacetimeDB.*` using statements or type references.
3. **And** the `docs/runtime-boundaries.md` reference explicitly names `Internal/Platform/DotNet/` as the `.NET`-specific implementation zone (already satisfied by Story 1.3; this story verifies the structural code matches the documentation).

## Deliverables

This story has five concrete outputs:

1. **`godot-spacetime.csproj` update** — add `SpacetimeDB.ClientSDK` 2.1.0 as a `PackageReference`
2. **`Internal/Platform/DotNet/` adapter stubs** — three stub classes that are the **only** location in the addon permitted to reference `SpacetimeDB.*` types
3. **`docs/compatibility-matrix.md` update** — update the `SpacetimeDB.ClientSDK` row to reflect it is now an active `PackageReference` (no longer "not referenced yet")
4. **`scripts/compatibility/support-baseline.json` update** — update the `line_check` for the compatibility-matrix.md `SpacetimeDB.ClientSDK` row to match the new exact text
5. **`tests/test_story_1_4_adapter_boundary.py`** — isolation contract tests proving the boundary is structurally enforced

The stubs in `Internal/Platform/DotNet/` do **not** implement any behavior. Stories 1.6+ add runtime implementation. This story is purely about structural isolation.

## Tasks / Subtasks

- [x] Task 1 — Update `godot-spacetime.csproj` (AC: 1)
  - [x] Add `<PackageReference Include="SpacetimeDB.ClientSDK" Version="2.1.0" />` inside a new or existing `<ItemGroup>` after the existing `Compile` include
  - [x] Verify `dotnet restore godot-spacetime.sln` succeeds (downloads the package)
  - [x] Verify `dotnet build godot-spacetime.sln -c Debug` succeeds with the new reference

- [x] Task 2 — Create `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` (AC: 1, 2)
  - [x] Namespace: `GodotSpacetime.Runtime.Platform.DotNet`
  - [x] `internal sealed class SpacetimeSdkConnectionAdapter`
  - [x] Add `using SpacetimeDB;` — establishes the only permitted SDK reference site
  - [x] Add `private IDbConnection? _dbConnection;` stub field — proves the zone references SDK types (note: SpacetimeDB.ClientSDK 2.1.0 exposes `IDbConnection` rather than a concrete `DbConnection` class)
  - [x] Add doc-comment citing this as the runtime isolation zone per `docs/runtime-boundaries.md`

- [x] Task 3 — Create `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` (AC: 1, 2)
  - [x] Namespace: `GodotSpacetime.Runtime.Platform.DotNet`
  - [x] `internal sealed class SpacetimeSdkSubscriptionAdapter`
  - [x] Add `using SpacetimeDB;` — part of the confined reference zone
  - [x] Stub only: private `IDbConnection?` field referencing the SDK type

- [x] Task 4 — Create `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` (AC: 1, 2)
  - [x] Namespace: `GodotSpacetime.Runtime.Platform.DotNet`
  - [x] `internal sealed class SpacetimeSdkReducerAdapter`
  - [x] Add `using SpacetimeDB;` — part of the confined reference zone
  - [x] Stub only: private `IDbConnection?` field referencing the SDK type

- [x] Task 5 — Update `docs/compatibility-matrix.md` (AC: 3)
  - [x] Replace the `SpacetimeDB.ClientSDK` row; new row must be:
    ```
    | `SpacetimeDB.ClientSDK` | `2.1.0` | Added as `PackageReference` in Story 1.4; the `.NET` adapter in `Internal/Platform/DotNet/` is the only permitted reference location. |
    ```
  - [x] Keep all other rows and surrounding prose unchanged

- [x] Task 6 — Update `scripts/compatibility/support-baseline.json` (AC: 3)
  - [x] Find the `line_check` entry with label `"SpacetimeDB.ClientSDK"` and update `expected_line` to match the exact new row text from Task 5:
    ```
    | `SpacetimeDB.ClientSDK` | `2.1.0` | Added as `PackageReference` in Story 1.4; the `.NET` adapter in `Internal/Platform/DotNet/` is the only permitted reference location. |
    ```
  - [x] The `version_key` field (`"spacetimedb_client_sdk"`) must remain unchanged

- [x] Task 7 — Create `tests/test_story_1_4_adapter_boundary.py` (AC: 1, 2, 3)
  - [x] Test adapter file existence: all three files present in `Internal/Platform/DotNet/`
  - [x] Test isolation: no `SpacetimeDB` pattern in any `Public/` C# file
  - [x] Test isolation: no `SpacetimeDB` pattern in any non-`Platform/DotNet/` addon C# file
  - [x] Test csproj: `SpacetimeDB.ClientSDK` `PackageReference` present in `godot-spacetime.csproj`
  - [x] Test namespace: adapter files declare `GodotSpacetime.Runtime.Platform.DotNet` namespace

- [x] Task 8 — Verify all checks pass (AC: all)
  - [x] Run `python3 scripts/compatibility/validate-foundation.py` — exits 0
  - [x] Run `dotnet build godot-spacetime.sln -c Debug` — succeeds with 0 warnings and 0 errors
  - [x] Run `pytest tests/test_story_1_4_adapter_boundary.py` — 47 passed

## Dev Notes

### What This Story Is (and Is Not)

**This story is structural boundary enforcement.** It proves that `SpacetimeDB.ClientSDK` is present in the project AND is referenced only from `Internal/Platform/DotNet/`. No runtime behavior is implemented here.

- **DO**: Add the NuGet reference. Create three stub adapter classes with `using SpacetimeDB;` and a private field referencing `IDbConnection`. Update the compatibility matrix.
- **DO NOT**: Implement any connection logic. Add `using SpacetimeDB.*` anywhere outside `Internal/Platform/DotNet/`. Modify the `Public/` types from Story 1.3. Add `SpacetimeDB.*` to `Internal/Connection/`, `Internal/Auth/`, or any other `Internal/` subfolder.

### Namespace Convention for `Internal/`

The `Internal/` folder is organizational (like `Public/`). To avoid colliding with `Public/` namespaces and to avoid the C# `internal` keyword as a namespace segment, `Internal/` maps to `Runtime` in the namespace:

| Folder | Namespace |
|--------|-----------|
| `src/Internal/Connection/` | `GodotSpacetime.Runtime.Connection` |
| `src/Internal/Auth/` | `GodotSpacetime.Runtime.Auth` |
| `src/Internal/Subscriptions/` | `GodotSpacetime.Runtime.Subscriptions` |
| `src/Internal/Cache/` | `GodotSpacetime.Runtime.Cache` |
| `src/Internal/Reducers/` | `GodotSpacetime.Runtime.Reducers` |
| `src/Internal/Events/` | `GodotSpacetime.Runtime.Events` |
| `src/Internal/Logging/` | `GodotSpacetime.Runtime.Logging` |
| `src/Internal/Compatibility/` | `GodotSpacetime.Runtime.Compatibility` |
| `src/Internal/Platform/DotNet/` | `GodotSpacetime.Runtime.Platform.DotNet` |

**This is the canonical namespace table for `Internal/` types.** Stories 1.5–1.9 depend on it. Any deviation causes fragmentation and contradicts the architecture pattern example:
`GodotSpacetime.Runtime.Connection.SpacetimeConnectionService`

[Source: architecture.md#Naming Patterns, architecture.md#Pattern Examples]

### csproj PackageReference — Exact Format

Add the reference inside a second `<ItemGroup>` after the existing compile `<ItemGroup>`:

```xml
<ItemGroup>
  <PackageReference Include="SpacetimeDB.ClientSDK" Version="2.1.0" />
</ItemGroup>
```

**Do not** put it inside the `<ItemGroup>` that contains the `<Compile Include="addons/godot_spacetime/**/*.cs" />` line.

The package is referenced from NuGet. `dotnet restore` will download it. The existing `.gitignore` already excludes `obj/` and `bin/` from commits.

[Source: architecture.md#Core Architectural Decisions, support-baseline.json `spacetimedb_client_sdk: "2.1.0"`]

### Adapter Stub Pattern

All three adapters follow the same pattern. Example for the connection adapter:

```csharp
using SpacetimeDB;

namespace GodotSpacetime.Runtime.Platform.DotNet;

/// <summary>
/// Adapter for the SpacetimeDB .NET ClientSDK connection layer.
///
/// This class is the ONLY location in the codebase where <c>SpacetimeDB.ClientSDK</c>
/// types may be referenced directly. All higher-level internal services and all public
/// SDK surfaces depend on the <c>GodotSpacetime.*</c> contracts rather than on
/// <c>SpacetimeDB.*</c> types.
///
/// See <c>docs/runtime-boundaries.md</c> — "Internal/Platform/DotNet/ — The Runtime
/// Isolation Zone" for the architectural justification.
///
/// Runtime implementation is added in Story 1.9.
/// </summary>
internal sealed class SpacetimeSdkConnectionAdapter
{
    // Stub — references IDbConnection to establish the isolation boundary.
    // Implementation (Builder construction, FrameTick advancement, etc.) is added in Story 1.9.
    private IDbConnection? _dbConnection;
}
```

The subscription and reducer adapters follow the same pattern: same `using SpacetimeDB;`, same namespace, same `private IDbConnection? _dbConnection;` stub field. The only differences are the class name and the doc-comment describing what that adapter eventually handles.

### Critical: Compatibility Matrix Update

`support-baseline.json` enforces an **exact-line match** for the `SpacetimeDB.ClientSDK` row in `docs/compatibility-matrix.md`. When you update the row text, you MUST also update `support-baseline.json` to match. If you update the matrix but not the JSON (or vice versa), `validate-foundation.py` will fail with a line-check error.

**Current text** (from Story 1.1 / before this story):
```
| `SpacetimeDB.ClientSDK` | `2.1.0` planned runtime baseline | Not referenced by the scaffold-only foundation yet, but this is the intended package target for later Epic 1 runtime stories. |
```

**New text** (after this story):
```
| `SpacetimeDB.ClientSDK` | `2.1.0` | Added as `PackageReference` in Story 1.4; the `.NET` adapter in `Internal/Platform/DotNet/` is the only permitted reference location. |
```

Update both files atomically. Run `python3 scripts/compatibility/validate-foundation.py` immediately after to confirm the check passes.

### Isolation Enforcement — What the Tests Verify

The isolation tests strip C# line/block comments and look for actual SDK references in non-comment code (for example `using SpacetimeDB;` directives or qualified uses like `SpacetimeDB.IDbConnection`).

Test logic:
1. Collect all `*.cs` files under `addons/godot_spacetime/src/Public/` — assert none contain `SpacetimeDB`
2. Collect all `*.cs` files under `addons/godot_spacetime/src/` excluding `Internal/Platform/DotNet/` — assert none contain `SpacetimeDB`
3. Confirm `Internal/Platform/DotNet/` adapter files DO contain `SpacetimeDB`
4. Check `godot-spacetime.csproj` for `PackageReference Include="SpacetimeDB.ClientSDK"`
5. Check all three adapter files declare `namespace GodotSpacetime.Runtime.Platform.DotNet`

Follow the existing test pattern from `tests/test_story_1_3_sdk_concepts.py`. Use `pytest.mark.parametrize` for the multi-file assertions.

### File Compilation — No Additional csproj Changes

The existing glob `<Compile Include="addons/godot_spacetime/**/*.cs" />` already picks up all files created under `src/Internal/Platform/DotNet/`. No further `csproj` changes are needed beyond the `PackageReference`.

### Architecture: Three Zones

From `docs/runtime-boundaries.md` (Story 1.3):

1. **`Public/`** — Stable Godot-facing contract. **Zero** `SpacetimeDB.*` references. Types from Story 1.3.
2. **`Internal/`** — Implementation zone. May change without changing public contract. **Zero** `SpacetimeDB.*` references (except through `Platform/DotNet/`).
3. **`Internal/Platform/DotNet/`** — The ONLY zone where `SpacetimeDB.*` references are permitted.

Story 1.4 proves zone 3 exists and is structurally isolated from zones 1 and 2.

[Source: architecture.md#Architectural Boundaries]

### Verification After Implementation

Run all three in order:

```bash
python3 scripts/compatibility/validate-foundation.py
dotnet build godot-spacetime.sln -c Debug
pytest tests/test_story_1_4_adapter_boundary.py
```

All three must succeed. If `dotnet build` fails, likely causes:
- `IDbConnection` not found — means `SpacetimeDB.ClientSDK` NuGet restore did not succeed or the wrong package reference/version is in use; run `dotnet restore` explicitly first
- Namespace mismatch — verify `namespace GodotSpacetime.Runtime.Platform.DotNet;` in all three adapter files
- Duplicate symbol — check that no `Public/` type was accidentally given the same name as an adapter

If `validate-foundation.py` fails, the most likely cause is Task 5 and Task 6 being out of sync (matrix text does not exactly match the `expected_line` in `support-baseline.json`).

### Git Context: Recent Commits

- `12f19d9` feat(story-1.3): Define Runtime-Neutral Public SDK Concepts and Terminology — creates all `Public/` stubs and `docs/runtime-boundaries.md`
- `006e66c` feat: establish baseline workflow validation — adds `scripts/compatibility/`, validates foundation lane

Story 1.3's key patterns that Story 1.4 must follow:
- Namespace conventions above — **must continue the `GodotSpacetime.*` pattern exactly**
- Foundation validation must stay green — **updating the baseline JSON when changing monitored files is mandatory**
- One public C# type per file — adapter stubs are `internal`, so they can technically coexist, but follow the same pattern

### Project Structure for This Story

**Files to create:**
```
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs
addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs
tests/test_story_1_4_adapter_boundary.py
```

**Files to update:**
```
godot-spacetime.csproj                               — add SpacetimeDB.ClientSDK PackageReference
docs/compatibility-matrix.md                        — update SpacetimeDB.ClientSDK row description
scripts/compatibility/support-baseline.json         — update SpacetimeDB.ClientSDK line_check expected_line
```

**Files to NOT touch:**
```
addons/godot_spacetime/src/Public/**/*.cs           — Public stubs from Story 1.3; do not modify
docs/runtime-boundaries.md                          — already names Internal/Platform/DotNet/ (AC #3 pre-satisfied)
addons/godot_spacetime/GodotSpacetimePlugin.cs      — plugin entrypoint; no changes needed
scripts/compatibility/validate-foundation.py        — no script changes needed
.github/workflows/validate-foundation.yml           — no CI changes needed
```

### References

- [Source: architecture.md#Architectural Boundaries] — `Internal/Platform/DotNet/` is the only permitted `SpacetimeDB.*` zone
- [Source: architecture.md#Naming Patterns] — `GodotSpacetime.Runtime.*` namespace for `Internal/` types
- [Source: architecture.md#Pattern Examples] — `GodotSpacetime.Runtime.Connection.SpacetimeConnectionService` reference
- [Source: epics.md#Story 1.4] — Acceptance criteria and FR39/FR42 coverage
- [Source: epics.md#Story 1.5] — GDScript continuity story that validates the seam created here
- [Source: spec-1-3] — Namespace canonical table; `Public/` types established here are the contract
- [Source: spec-1-3#Dev Notes: Architecture: Public vs Internal vs Platform] — "Story 1.4 creates the `Internal/` layer" and "Story 1.4 creates the adapter types here [in `Internal/Platform/DotNet/`]"
- [Source: docs/runtime-boundaries.md#Internal/Platform/DotNet/] — AC #3 already satisfied; verify structural match
- [Source: scripts/compatibility/support-baseline.json] — exact line_check must be updated atomically with compatibility-matrix.md

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Build failure on first attempt: `DbConnection` type does not exist in `SpacetimeDB.ClientSDK` 2.1.0. The package exposes `IDbConnection` (interface) and `DbConnectionBase<TConn, TEvent, TTables>` (generic class). Fixed by using `IDbConnection?` for the stub fields in all three adapters.

### Completion Notes List

- Added `SpacetimeDB.ClientSDK 2.1.0` as a `PackageReference` in `godot-spacetime.csproj` in a separate `<ItemGroup>` after the `Compile` include.
- Created three adapter stub classes under `addons/godot_spacetime/src/Internal/Platform/DotNet/` — all use `using SpacetimeDB;` and `namespace GodotSpacetime.Runtime.Platform.DotNet`. Stub field uses `IDbConnection?` (the actual SDK connection interface in 2.1.0; the spec referenced `DbConnection` which doesn't exist as a concrete type in this version).
- Updated `docs/compatibility-matrix.md` SpacetimeDB.ClientSDK row to reflect active PackageReference status.
- Updated `scripts/compatibility/support-baseline.json` `expected_line` for the SpacetimeDB.ClientSDK line check atomically with the matrix update.
- Created `tests/test_story_1_4_adapter_boundary.py` with 47 isolation contract tests covering: file existence, namespace declarations, comment-safe reference detection, no SpacetimeDB in Public/, no SpacetimeDB outside DotNet zone, adapters reference SpacetimeDB, csproj PackageReference, and doc/baseline alignment.
- Added Python cache ignores to `.gitignore` and removed stray `tests/__pycache__/` bytecode from the repo surface so validation runs do not create review noise.
- All validation commands pass: `dotnet restore godot-spacetime.sln` completes successfully, `validate-foundation.py` exits 0, `dotnet build` succeeds with 0 warnings and 0 errors, `pytest tests/test_story_1_4_adapter_boundary.py` passes 47/47, and `pytest -q` passes 147/147.

### File List

- `.gitignore` — ignore Python cache artifacts generated by repo validation
- `godot-spacetime.csproj` — added `SpacetimeDB.ClientSDK 2.1.0` PackageReference
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkConnectionAdapter.cs` — new adapter stub
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkSubscriptionAdapter.cs` — new adapter stub
- `addons/godot_spacetime/src/Internal/Platform/DotNet/SpacetimeSdkReducerAdapter.cs` — new adapter stub
- `docs/compatibility-matrix.md` — updated SpacetimeDB.ClientSDK row
- `scripts/compatibility/support-baseline.json` — updated SpacetimeDB.ClientSDK line_check expected_line
- `tests/test_story_1_4_adapter_boundary.py` — new isolation contract test suite (47 tests, including comment-safe SDK reference detection)

### Change Log

- feat(story-1.4): isolate .NET runtime adapter behind Internal/Platform/DotNet/ boundaries (2026-04-14)
- 2026-04-14: Senior developer review auto-fix — corrected the story record to match real restore/build/test outputs, aligned the dev notes around `IDbConnection`, hardened the isolation matcher against comment-only false positives, and ignored/cleaned Python cache artifacts from the test surface.

## Senior Developer Review (AI)

Reviewer: Pinkyd
Date: 2026-04-14
Outcome: Approve

### Findings Fixed

- HIGH: The story Dev Notes still instructed follow-on work to use `DbConnection`, but the implemented addon boundary and compiled package surface for this story rely on `IDbConnection`; leaving the broken example in place would mislead later stories into non-compiling code.
- MEDIUM: Task 8 and the Completion Notes overstated verification evidence (`33 passed`, `133/133`, and expected CS0169 warnings) even though the current restore/build/test outputs are different, reducing trust in the reviewable artifact.
- MEDIUM: `tests/test_story_1_4_adapter_boundary.py` claimed to inspect code-only references but actually matched raw `SpacetimeDB` substrings, so comment-only mentions could trigger false failures unrelated to the acceptance criteria.
- MEDIUM: Python bytecode under `tests/__pycache__/` was not ignored, and one `.pyc` file was already tracked in the repo, creating machine-generated review noise outside the actual story surface.

### Actions Taken

- Corrected the story Dev Notes, adapter example, and verification records so the artifact now reflects the compiled `IDbConnection` boundary and the real restore/build/test results.
- Hardened the Story 1.4 isolation tests to strip block comments, detect real SDK references, and explicitly cover comment-only false-positive cases.
- Added Python cache ignore rules and removed the stray test bytecode artifact from the working tree.
- Updated the story File List and Change Log so the review fixes are documented alongside the implementation.

### Validation

- `dotnet restore godot-spacetime.sln`
- `python3 scripts/compatibility/validate-foundation.py`
- `dotnet build godot-spacetime.sln -c Debug`
- `pytest tests/test_story_1_4_adapter_boundary.py`
- `pytest -q`

### Reference Check

- Local reference: `_bmad-output/planning-artifacts/architecture.md` (`Core Architectural Decisions`, `Naming Patterns`, `Pattern Examples`, `Architectural Boundaries`)
- Local reference: `docs/runtime-boundaries.md`
- Web fallback reference: SpacetimeDB C# reference — https://spacetimedb.com/docs/2.0.0-rc1/clients/c-sharp/
