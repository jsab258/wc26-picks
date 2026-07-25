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
| 2026-07-25 | M2 shipped | CI-validated end-to-end (run 17, commit 3e65f72): 2-day sim completed 2 night drops with 2 NPC witnesses, banked heat-taxed takings ($74 at heat 0.44), patience 1.00, verdict Ongoing, 0 errors, targeted discredit verified. 140 core checks green. Next: player PC playtest of the LEDGER-Windows artifact, then tuning |
| 2026-07-25 | M3 plan | **Approved (player decision), contingent on the playtest confirming the loop.** RPG-elements audit vs GTA5/KCD2: we already run KCD's schedule/witness/gossip spine and GTA's heat-as-wanted-level at boutique scale. M3 adds, in priority order: (1) **disguise/appearance** — day vs night clothing toggle feeding witness confidence (the double-life trope; plugs straight into the rumor engine); (2) **bar investment** — spend takings on stock/regulars for higher base income and rumor-dampening, closing the economy loop (invest in the legit life vs defend the hidden one); (3) **schedule-conflict story beats** — authored double-booking dilemmas (a day-world invitation landing exactly on a drop window); (4) **consequential loyalty** — make per-NPC loyalty visible and mechanically meaningful beyond bribe outcomes. Deliberately rejected: grindable stats (reading people, not numbers, is the skill), survival needs (job windows already force presence), minigames (conversation is the minigame). Institutional escalation (constable investigating at high heat) deferred to M4 |

| 2026-07-25 | Full week green | Run 18 (e05e4e7): the entire 7-day campaign played in-engine in CI — 0 errors, pass=True. The no-damage-control sim bot survived (verdict Ongoing) but paid for it: 4 drops made, 2 missed (patience 0.52 — likely the new street furniture snagging the straight-line auto-mover; humans steer around, watch item), 4 NPC witnesses, final heat 0.56, takings $659 over 6 closes (~$110/day vs $220 base — the heat tax visibly biting), cash $1269. Night render: bright-pixel share up from ~0.5-2% to 13.1% (meanLuma 0.226) — the arm lamps read. This exact artifact (LEDGER-Windows, run 18) is the playtest build |
| 2026-07-25 | M3 shipped | Four steps, each CI-validated on the full-week sim: **M3.1** PlayerKnowledge + Ledger UI (belief-state replaces omniscient verbs; witness/warning/admission channels — CI: 7 knownLeads from 6 witnesses); **M3.2** clean/dirty money + till laundering $120/day, Lena suspects unexplained hoards (CI: $450 dirty earned, $360 washed, $90 pending — conservation exact); **M3.3** runner's coat (0.6 witness confidence, daylight-sighting cost) + morning summary card — coated week measurably safer (heat 0.42 vs 0.56, takings $772 vs $659), which obsoleted the end-snapshot transport criterion (now "ever reached day circle"); **M3.4** conflict beats (Ada's tea d3, Rocco's toast d5, windows inside the drop window; no hard locks). Adversarial review workflow pre-CI caught 2 blockers on M3.4: beat spot auto-attending from bar-door foot traffic, and an invite asserting unbacked lore — both fixed before build |
| 2026-07-25 | Roadmap reconciled | Design-doc reread found missed systems, folded into `roadmap.md` (supersedes doc §11 numbering): **"never ground truth" violation** (DC verbs read the real mill; M3 adds PlayerKnowledge + Ledger UI v0), **clean/dirty money + laundering** (absorbs bar-investment idea, M3), **secrets-as-loot/hooks** (novelty claim #3, unbuilt → M4), **suspicion behavior thresholds** and **Det. Mara Ossei** (the "constable" already authored in doc §8 → M4), **end-of-day ledger summary** (M3), **persistence as pillar P5** (save/load → M4), cost-per-hour telemetry (M3), output validator (M5). Flagged open: cast drift (our Sam/Ada vs doc's coworker/landlady — recommend keeping approved cards), melee combat stays deferred, drop-window vs no-hard-timers rule watched at playtest |

| 2026-07-25 | M4.1 shipped | Secrets-as-loot hooks (novelty claim #3) CI-validated (run 26): Core Secret/SecretsBook, weak hook = one favor, strong hook = standing leash (Tick/Bribe/Intimidate/Leads all honor it — refused, never backfired); 4 authored secrets with loyalty-gated confession (0.75) / sharing (0.65) channels; hook button + WHAT YOU HOLD ledger section. Adversarial review caught 3 blockers pre-CI: a day-one freebie (Rocco's loyalty == share floor), the unenforced no-backfire promise, and Lena's "secret" being something her card openly admits — re-authored to the hiding place (player decision). 198 core checks |
| 2026-07-25 | M4.2+M4.3 shipped | CI-validated together (run 28). **M4.2**: §6.4 escalation ladder — Uneasy probes in conversation, Suspicious NPCs seek partners and CompareNotes (directed, deterministic, leash-respecting; 8 checks), Confronting NPCs block the player's path and force the conversation; **Det. Mara Ossei** spawns when heat first crosses 0.6 (patrol schedule, core-tier card, not in the gossip mill — she listens; her presence stretches rumor half-life 96→144h); sim bot bare-faced days 1-2/coated from day 3 so both disguise and Ossei paths run in CI. **M4.3**: SaveCodec (13 checks, 219 total) — the whole lived week round-trips (rumors at exact confidence, leashes, denial caps, handled knowledge, beats, campaign); autosave at morning close, F5, load-on-boot, restart deletes; in-engine saveLoadOk criterion every CI week. M4.2 reviewed inline (workflow review infra failed structured-output; empty results treated as NO clean bill) |
| 2026-07-25 | Batch decisions | Four player decisions cleared in one round: (1) **Cast drift — keep the approved cards** (Sam the go-between, Ada the teacher); "first friend/coworker" re-homes in a new character when the day job exists; doc §8 revised at the slice. (2) **Combat — deferred past the vertical slice**; revisit as its own milestone only if the slice needs it. (3) **Love interest — Noor the journalist** for the slice; intimacy as exposure risk, romance and gossip mechanically entangled. (4) **Drop window — judge at playtest**; soften to lateness-decay only if it feels like a countdown |

## Documents

- `design-doc.md` — founding design document (LEDGER)
- `research-mechanics.md` — retention/innovation/AI-NPC research with sources
- `m0-plan.md` — M0 tech-spike build plan
- `roadmap.md` — reconciled milestone roadmap M3+ (2026-07-25, supersedes design-doc §11 numbering)
