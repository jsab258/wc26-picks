# Tier-2 Character Pipeline — Spec v1 (2026-07-26)

> **STATUS: SPEC.** The design for the Tier-2 character generation pipeline. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees
> with the roadmap is out of date about what got built, not about what
> was intended.

The machine that makes density purchasable (player direction: build density
via AI generation, not manual work). Target: the doc §5 middle ring —
150–300 generated-then-curated characters, each mechanically individual.
This spec is the build plan for the generator; implementation is a future
session's work (needs an API key for batch generation).

## Card template (generated per character)

Every Tier-2 card is the same markdown shape the engine already parses,
plus three generator-only fields validated before acceptance:

- Standard sections: `# Name`, `id`, `tier: ambient`, Summary, Personality,
  Speech Style, Hard Facts (3–5, each checkable).
- **secret**: one line + kind (shameful|criminal per the exposure-lethal
  taxonomy in Hooks.cs) + `knownBy` (0–2 other character ids).
- **need**: one thing they want that the player could supply (the recruit/
  befriend hook — doc §5 "mechanical individuality").
- **connections**: 2–4 ties with weights 0.3–0.8 into the social graph
  (validator rejects orphans and cliques > 6).
- **schedule**: 2–5 anchored stops (place id + hour) on the district map.
- **traits**: greed/nerve/loyalty each 0.05–0.9.

## Script validator (runs on every generated batch, no LLM)

1. Schedule feasibility: stops exist on the map, hours ordered, walkable
   distances between consecutive stops at NPC speed.
2. Lore greps: no contradictions with hard-fact registry (dates of Mickey's
   death, the fire, district names); registry extracted from Tier-1 cards.
3. Trait ranges + at least one trait outside [0.4, 0.6] (no beige people).
4. Secret sanity: owner exists, knownBy ids exist, kind valid.
5. Graph health: connected component check; average degree 2–4.
6. Name/id uniqueness against the whole cast.
Failures reject the card back to regeneration with the failure reason in
the prompt (self-healing batch loop).

## Promotion flow (ambient → core)

Attention promotes (doc §5): when a player has N conversations with an
ambient character or their loyalty crosses 0.7, flag for promotion — a
curation pass deepens the card (hand-touch), tier flips to core (stronger
model), memory file carries over unchanged. Demotion never happens;
attention is a one-way door.

## Cost estimate (per 100 cards, Sonnet-class generation)

~2.5k tokens out per card + validator retries (~20%) ≈ 300k output tokens
≈ low single-digit dollars per 100 cards. Curation is the real cost:
budget ~2 min human skim per card, batch-reviewable in a table.

## First milestone (buildable next session)

A hand-authored sample ring of 6–10 cards written IN this template
(market vendor, dock hand, night cabbie, pawnbroker, priest's housekeeper,
ferry ticket clerk) to prove the fields and validator rules on real
content before any batch generation. Wire into CastSetup-style loader.
