# Collaboration Process & Decision Log

## Roles

- **Jafar** — creative director and decision-maker. Not a developer; usually on mobile.
  Minimal manual work on his side.
- **Claude** — designer, engineer, producer. Does the building, researching, and drafting.

## Working agreement (standing, applies to every future session)

1. **Every design, story, character, and UI decision goes to Jafar as a short choice**:
   2–4 options, one marked recommended, phrased to be answerable from a phone in seconds.
   No decision of that kind is made silently.
2. **Purely technical/implementation details** (code structure, libraries, refactors,
   pipelines) are Claude's to decide autonomously — surfaced only if they constrain design.
3. Everything durable lives in this repo under `game-design/` (and later the Unity project),
   never only in chat. Each session updates the decision log below.
4. Manual steps for Jafar are batched, rare, and come with exact instructions
   (e.g. one-time account creation, API keys, playtesting a build).

## Decision log

| Date | Decision | Choice |
|------|----------|--------|
| 2026-07-24 | Engine | Unity 6 (HDRP quality target, URP fallback) |
| 2026-07-24 | Concept | LEDGER — double-life open-city game: slice-of-life × bottom-up crime sim (fusion of concepts "Family Business" + "Year One") |
| 2026-07-24 | Graphics bar | High-quality 3D ("good indie realism"); explicitly NOT low-poly/stylized; not expected to be AAA |
| 2026-07-24 | Scale | Big city, large cast (hundreds of characters, 3-tier system) |
| 2026-07-24 | AI NPCs | LLM-driven dialogue + voice + persistent markdown memory (Stanford memory/reflection architecture) |
| 2026-07-24 | Combat | Yes, core verb — melee-first (Sleeping Dogs lineage), guns rare and consequential; moderate explicitness, no gore |
| 2026-07-24 | Timers | No hard countdowns/deadlines anywhere; pressure via escalation only |
| 2026-07-24 | Architecture | Content-as-data separability so the project can later be forked into variant editions without touching sim/engine code |
| 2026-07-24 | Next milestone | M0 tech spike (see `m0-plan.md`) |
| 2026-07-24 | Playtest hardware | Mid-range gaming PC (~2025 build) → perf target 60 fps @ 1080–1440p, HDRP medium-high |
| 2026-07-24 | Build pipeline | GitHub Actions on windows-latest: buildalon unity-setup + license-file-free Personal activation (UNITY_EMAIL/UNITY_PASSWORD secrets only) + headless CiBuild. Unity pinned 6000.0.58f1 (44b8bf3a3225). Verified green end to end; special-character password works; no Unity Hub / .ulf needed |
| 2026-07-24 | Lena's card | Keep the draft: dry 31-year bookkeeper, loyal to Marek, guards the real ledger until trust is earned |
| 2026-07-24 | Voice direction | ElevenLabs cloud for development (implementation at a later milestone); shipping economics revisited later |
| 2026-07-24 | Protagonist | Fixed authored character (name TBD with Jafar); NPCs get pre-seeded history about the family |
| 2026-07-24 | Roadmap order | Visual upgrade BEFORE M1 gossip (player decision — overrides earlier M1-first plan). Needs an asset-budget decision (~$50–200) at kickoff |
| 2026-07-24 | Asset budget | Tier 1 approved: ~$40–60 one-time realistic city/environment pack now; character system (Character Creator 365, ~$99/yr) deferred to the vertical slice. Free CC0 materials (Poly Haven/ambientCG) + Mixamo animations used throughout |
| 2026-07-24 | Self-testing | Two-layer harness: SimHarness AI playtest (LLM player + LLM judge vs Lena's brain; fake mode in CI always, live mode via ANTHROPIC_API_KEY secret) + in-engine SimDirector (-simdays N: accelerated days, waypoint player, error capture, screenshots, sim-report.json) run on every Windows build |
| 2026-07-24 | Asset pipeline | `AssetLibrary.cs`: world requests surfaces/props by logical name; resolves from a drop-in pack at `StreamingAssets/CityPack/` (textures/*.png, materials/*.json, props.bundle) first, else procedurally-generated tiling textures (brick/asphalt/slab/plank/plaster), else flat tint. A purchased Asset Store pack drops in with **no code change**; CI (no pack) still gets textured materials |
| 2026-07-24 | Render pipeline | Staying on Unity **built-in** RP for now (HDRP was trimmed from the manifest for headless build speed/reliability). Push lighting/materials as far as built-in allows (gradient ambient, fog, PBR smoothness/metallic, procedural albedo). HDRP swap is a **deliberate later step** at the vertical-slice stage — it needs in-editor RenderPipelineAsset config + HDRP/Lit shader remap and must not be attempted from a headless build with no editor to verify |
| 2026-07-25 | M1 direction | Gossip/double-life novelty built first (player decision): rumor network with day/night circles, confidence decay, contradiction-driven exposure — then the player's side (leads awareness + bribe/intimidate/discredit/lie-low with backfires) |
| 2026-07-25 | Damage-control UI | **In-conversation options** (player decision): verb buttons appear under the chat box only while talking to an NPC who is carrying a rumor about you (live-priced payoff, lean on, plant doubt); free-typed talk remains. Rejected: dedicated "word on the street" management screen; hybrid see-remotely/act-in-person (may revisit hybrid when more NPCs are conversational) |
| 2026-07-25 | Cast cards | **Approved as drafted** (player decision): Rocco the 20-year doorman (night circle, bribable/cowable), Ada the retired schoolteacher (day circle, both bribe and threat backfire), Sam the go-between (both circles, folds to anything, spreads fastest). Cards live in CastSetup.cs and stay hand-editable |
| 2026-07-25 | M2 scope | **All three pillars at once** (player decision): (1) stakes — street-heat meter from day-circle rumor entrenchment, exposure lose state + survive-the-week win state; (2) economy — bar income tied to street reputation, so bribes spend money the rumor itself is shrinking; (3) night side — a nightly outfit job that is the SOURCE of new witnesses/rumors, with outfit patience as the second lose axis. Playtest tuning folds in when the player reaches a PC |

## Documents

- `design-doc.md` — founding design document (LEDGER)
- `research-mechanics.md` — retention/innovation/AI-NPC research with sources
- `m0-plan.md` — current milestone build plan
