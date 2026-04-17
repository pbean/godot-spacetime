# Project Conventions for AI Agents

## Empirical SDK Validation

**"Measure the pinned runtime; document what you measured."**

When a story makes a behavioral claim about a pinned dependency — the SpacetimeDB CLI, the SpacetimeDB ClientSDK NuGet, the Godot binary, an HTTP endpoint shape, or any external surface — verify the claim against the artifact actually installed in this repo's compatibility baseline before authoring tasks or acceptance criteria. Capture the verification in the story's Dev Notes (DLL reflection output, `--help` excerpt, real generated file path, etc.) so reviewers can reproduce it.

Upstream documentation, release notes, and changelogs may lag, contradict the shipped artifact, or describe a different version. The pinned artifact is the source of truth for this repo.

### Canonical examples from project history

- **Story 9.1** — Upstream Unreal docs say `Brotli` is "not implemented, defaults to Gzip." Local DLL reflection against the pinned `2.1.0` ClientSDK confirmed `SpacetimeDB.Compression.Brotli` exists and canonicalizes to `Gzip` on the wire. The addon documents and surfaces the canonicalization rather than inventing a custom Brotli path.
- **Story 10.3** — Story drafted with AC2 assuming scheduled reducers emit client bindings. Running `spacetime generate 2.1.0` against a real Rust module proved scheduled reducers are server-only — no `Reducers/ProcessJob.g.cs`, no `OnProcessJob` event, no `Dispatch()` case. The AC was rewritten to match observed output; the docs follow the same.
- **Story 11.5** — Story drafted assuming `spacetime generate --lang gdscript`. The pinned `2.1.0` CLI has no GDScript target. The generator was implemented as `scripts/codegen/generate-gdscript-bindings.py` parsing existing C# bindings as the schema source instead.

### How to apply

- Before writing tasks for any story that touches an external API, surface, flag, or generated artifact: run the relevant probe (`--help`, DLL reflection, `spacetime generate` against a fixture, etc.) and capture the output.
- If the observed behavior contradicts upstream docs, prefer the observation. Document the discrepancy in `docs/troubleshooting.md` or the story's Dev Notes — do not paper over it with a fallback that masks the real surface.
- During review, any AC that can't be tied back to observed runtime output is a documentation defect, not a missing implementation.
