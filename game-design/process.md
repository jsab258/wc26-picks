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

## Documents

- `design-doc.md` — founding design document (LEDGER)
- `research-mechanics.md` — retention/innovation/AI-NPC research with sources
- `m0-plan.md` — current milestone build plan
