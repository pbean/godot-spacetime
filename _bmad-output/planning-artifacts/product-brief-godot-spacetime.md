---
title: "Product Brief: godot-spacetime"
status: "complete"
created: "2026-04-09T15:15:57-07:00"
updated: "2026-04-09T15:21:14-07:00"
inputs:
  - "User discovery session in Codex on 2026-04-09"
  - "https://github.com/clockworklabs/com.clockworklabs.spacetimedbsdk"
  - "https://github.com/clockworklabs/spacetimedb-typescript-sdk"
  - "https://github.com/clockworklabs/com.clockworklabs.spacetimedbsdk-archive"
  - "https://github.com/flametime/Godot-SpacetimeDB-SDK/tree/stdb-v2-protocol"
  - "https://spacetimedb.com/docs/clients/"
  - "https://spacetimedb.com/docs/clients/codegen/"
  - "https://spacetimedb.com/docs/sdks/c-sharp/"
  - "https://spacetimedb.com/docs/sdks/typescript/"
  - "https://docs.godotengine.org/en/latest/getting_started/workflow/export/exporting_for_web.html"
  - "https://docs.godotengine.org/en/latest/tutorials/scripting/c_sharp/index.html"
---

# Product Brief: Godot SpacetimeDB SDK for SpacetimeDB 2.1+

## Executive Summary

SpacetimeDB now has a current stable 2.1.x release line and mature official client references for C#, TypeScript, and Unity, but Godot developers still lack a clean, credible path to build production clients against it. Today, Godot users either adapt tooling designed for other engines, depend on an unofficial GDScript SDK with known gaps, or implement protocol behavior themselves. That slows adoption, raises integration risk, and makes Godot feel like a second-tier target for SpacetimeDB.

This product creates an open-source Godot SDK/plugin for SpacetimeDB 2.1+ with a clean long-term foundation rather than a one-off compatibility layer. The core product decision is architectural: design for both `.NET` and `GDScript`, ship one runtime first, and avoid locking the core runtime model to C# assumptions that would make later `GDScript` support painful. The first release should prioritize `.NET` delivery for immediate usability and closer alignment with the official SDK model, while preserving a path to a native `GDScript` runtime for broader Godot adoption and eventual web-compatible workflows.

The first version should target practical parity with the Unity plugin baseline: generated module bindings, connection and auth flow, token persistence, subscriptions, client-side cache access, row update callbacks, reducer invocation and reducer event handling, usable documentation, and a sample integration. Generated bindings should follow the official C# generation model closely enough that upstream concepts, upgrade expectations, and developer mental models transfer cleanly into Godot. The immediate customer is the project owner building a real Godot game, but the product should be packaged and positioned for wider open-source use from the start.

## The Problem

Godot developers interested in SpacetimeDB 2.1+ face a tooling gap at exactly the point where they need confidence. The official SDK story is clear for C#, Unity, and TypeScript, but not for Godot. That creates three bad options: use Unity or pure C# assumptions that do not map cleanly to Godot workflows, rely on an unofficial Godot implementation with stated feature limitations, or hand-roll a client integration around a moving protocol surface.

The cost of the status quo is not just engineering time. It is ecosystem hesitation. Without a Godot-native SDK that feels stable and aligned with upstream behavior, individual developers postpone adoption, open-source contributors have no clear place to gather, and SpacetimeDB loses a potential entry point into the Godot community.

## The Solution

Build a Godot SDK/plugin for SpacetimeDB 2.1+ from a new, maintainable foundation informed by the official C# SDK, the TypeScript SDK, and the Unity plugin behavior. The product should expose the expected SpacetimeDB client capabilities in a Godot-friendly form: connection lifecycle management, token-based identity handling, generated module bindings, subscription management, synchronized local cache access, row-level update callbacks, and reducer invocation and result handling.

The architecture should deliberately separate runtime-agnostic concepts from runtime-specific implementations. Connection semantics, schema and generated binding contracts, event models, and cache abstractions should not assume C# as the permanent runtime. The generated binding layer should align with the official C# model wherever possible rather than inventing a Godot-only contract. That makes it possible to ship a `.NET` runtime first for immediate value while preserving a realistic follow-up path to a native `GDScript` runtime without rewriting the product around different concepts later.

## What Makes This Different

This is not a thin Godot wrapper over existing SDKs, and it is not a direct continuation of the unofficial branch as the product foundation. It is a Godot-first client SDK shaped by upstream client behavior but designed around Godot adoption realities.

Its main differentiation is strategic, not cosmetic:

- It gives Godot developers a SpacetimeDB 2.1+ path that aligns with official client concepts rather than inventing a separate model.
- It treats dual-runtime support as an architectural requirement from day one, even though delivery is phased.
- It prioritizes long-term maintainability and open-source credibility over the shortest path to a working demo.
- It uses real production needs from the primary user as the forcing function, which reduces the risk of building a showcase SDK that feels incomplete in actual game development.

## Who This Serves

The primary user for v1 is the project owner: a Godot developer who needs a dependable SpacetimeDB 2.x client integration for an actual game and wants an implementation solid enough to build on, not just evaluate.

The secondary users are other Godot developers exploring SpacetimeDB who want an open-source SDK that feels native to the engine, follows the official client model, and signals that Godot is a serious target. Over time, the product should also serve contributors who want to extend the SDK toward native `GDScript` runtime support and broader platform reach.

## Success Criteria

The first release is successful if it enables a real Godot game to use SpacetimeDB 2.1+ with the same essential client capabilities expected from the Unity baseline:

- A developer can generate bindings, connect to a database, authenticate or resume identity with a token, subscribe to data, query the local cache, observe row changes, and call reducers from Godot.
- The `.NET` implementation is usable in the primary user's game without bespoke protocol workarounds outside the SDK.
- The architecture clearly isolates runtime-specific pieces so a later `GDScript` runtime does not require redesigning the generated binding model or public mental model.
- Another Godot developer can install the plugin, follow the docs, and reproduce a working sample integration without direct maintainer help in a single setup session.
- The repository is credible as an open-source project: documented, sample-backed, and structured for external contribution.

## Scope

### In Scope for v1

- New implementation with a clean long-term architecture rather than inheriting the unofficial Godot SDK as the core product base
- `.NET`-first runtime delivery
- Product behavior that meets the same practical v1 expectations as the Unity plugin baseline
- Generated module binding workflow for Godot clients
- Binding generation modeled on the official C# generation flow and concepts
- Connection lifecycle and token-based auth handling
- Subscription management and client-side cache access
- Row callbacks and reducer invocation and response handling
- GitHub-release-first distribution, plus Godot plugin packaging, documentation, and a sample project suitable for real evaluation and use
- Public open-source release posture from the start

### Explicitly Out of Scope for v1

- Full native `GDScript` runtime parity on day one
- Features beyond the Unity plugin baseline
- Procedures, event-table support, and other advanced surfaces not already required by the Unity plugin parity target
- Web export runtime support in the initial release
- Godot AssetLib distribution in the initial release
- Advanced visual tooling or editor workflows beyond what is necessary to install, configure, and use the SDK
- Speculative protocol features, advanced performance tuning, or convenience layers not validated by the Unity baseline or immediate product need

## Vision

If this succeeds, the project becomes the default Godot client path for SpacetimeDB: an open-source SDK that matches upstream concepts, ships dependable `.NET` support against the current stable 2.1+ line, and extends into a first-class native `GDScript` runtime without fracturing the developer experience.

Over the next two to three years, that could evolve into a broader Godot ecosystem asset: stable multi-runtime support, stronger onboarding and samples, packaging that reduces installation friction, and eventually a credible story for the parts of the Godot audience that care deeply about `GDScript`-first workflows and web-friendly deployment paths. The near-term win is not just one working SDK. It is establishing Godot as a real, supportable client platform for SpacetimeDB 2.1+ and the broader 2.x era.
