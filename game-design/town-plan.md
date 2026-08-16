# The town plan — a real town, drawn cheaply

> **STATUS — SPEC**, approved by Jafar 2026-08-16 ("go"). The plan of
> record for making LEDGER's city read as a real British port town.
> The benchmark conversation: GTA5 and KCD2 feel real because their
> space is organised by HUMAN logic; ours was organised by geometry
> logic. This spec is the conversion. Progress lives in the queue and
> the git log, not here.

## The vision

A coherent, atmospheric, stylised late-analog British port town.
Style stays cheap on purpose — low-poly vehicles, photo-textured
brick, noir light — and everything is spent on URBAN COHERENCE:
enclosure, hierarchy, grammar, purpose. The register ceiling is
top-tier stylised, not photoreal, and every frame must obey one
discipline: nothing in shot that a town would not have put there.

## The one structural decision

**The street GRAPH stays; its EXPRESSION is rebuilt.** Walkers,
traffic, addresses, confab spots, every spatial gate and nine days of
verdict history consume `StreetMap`'s nodes and edges — that contract
is sound and keeping it protects the whole simulation. What reads as
fake is how `WorldBuilder` renders that graph: detached boxes with
gaps, chamfered polygon pavements, abstract junctions, furniture
spam. All of that is replaceable per-edge and per-block without
moving a single node. The organic re-plan of the topology itself
(curved esplanade, medieval-ish lane pattern) is explicitly
POST-PLAYTEST — it multiplies risk across every system for a gain the
first four phases mostly deliver.

**Risk rule:** the new expression builds behind `TownPlan.Enabled`
beside the old paths. Decision point Tuesday noon: stable stills →
Wednesday ships the town; anything doubtful → the flag flips back and
Wednesday ships yesterday's proven world. No scenario harms the
playtest.

**Judgement rule:** every phase is judged on PLAYER-HEIGHT stills.
The elevated review camera has flattered this project repeatedly; the
street camera is where the playtest actually happens.

## Phase T1 — enclosure and the street ribbon *(the foundation)*

1. **Terraces.** Each block edge fills with a CONTIGUOUS row of
   building masses — shared party walls, varying widths and heights
   within one architectural language, chimney stacks on the party
   walls, rear yards inside the block. Gaps only where the plan says
   (alley mouths, yard gates). A street becomes two walls with sky
   between, which is the single change that makes it a street.
2. **The street ribbon.** Pavements as continuous strips following
   each edge at constant width, kerb lines unbroken through the run,
   junction corners as proper quadrants with radii. The chamfered
   plate-islands go. Roads keep their graph widths — the hierarchy
   (avenue, side street, service lane) is already in the edge data
   and starts being VISIBLE instead of incidental.
3. **Zoning made legible.** The prosperity ramp already grades the
   map; bind building KINDS to it — warehouse runs and yard walls by
   the docks, shopfront terraces on the spine, house terraces behind,
   the pub anchoring its corner. Landmarks for orientation: crane
   silhouettes over the dock district, a gasometer, the church-or-
   chapel mass. A skyline that says which way you are facing.

## Phase T2 — the ground floor, where eyes live

4. **Shopfronts.** Ground floors on commercial edges get the full
   fascia grammar: signboard ON the building (name painted, lit at
   night), display windows, recessed doorways, awnings (kit meshes
   already fetched), step and threshold. House doors get steps and
   surrounds. Detail budget concentrates 0–4m above pavement.
5. **Signs that make sense.** Free-standing sign spam deleted as a
   CLASS. British grammar instead: street name plates mounted on
   corner buildings (WorldText on walls — the system exists), at most
   one clustered post per junction where a plate has no wall, shop
   signs on shops. Sign count falls by roughly an order of magnitude
   and every survivor is where a council would have put it.
6. **Lamps and furniture by grammar.** Lamps with heads (kit road
   lights or procedural), kerb-edge placement at 25–30m alternating,
   postbox and phone box at planned corners (a red phone box is six
   boxes and glazing bars — procedural, on-brand, free), bins in
   alleys, benches where people wait.
7. **Parked cars.** Deterministic kerb slots along commercial and
   residential edges, filled 40–70% with the kit saloons in the town
   palette, registered as obstacles. The cheapest "lived-in" signal
   that exists.

## Phase T3 — visible purpose *(the sim made legible)*

8. Queue points at shelters, standing spots at the market square's
   edges, smokers outside the pub — DESTINATIONS bound to the
   schedules people already have. The social sim is the moat; this
   phase is its visibility.
9. Reaction animation: flinch, greeting, turn-to-look — clips already
   in the harvest, wired to perception events the sim already emits.
   Being visibly noticed is the strongest liveliness signal there is.

## Phase T4 — light and air

10. Noon grounding: real building shadows, ambient occlusion doing
    contact work in daylight, so nothing floats.
11. Motion everywhere cheap: chimney smoke, gulls over the docks,
    washing lines in alleys, neon flicker (exists), rain and puddles
    (exist). A frame with a dozen moving things reads alive.
12. Clouds on the gradient sky.

## Explicitly deferred (post-playtest)

The topology re-plan (organic pattern, curved esplanade), interiors
beyond the pub, mocap-grade animation (budget question, Jafar's
call), HDRP (same).

## Done, per phase, as something checkable

- T1: a player-height noon still where both sides of the street are
  continuous frontage, the kerb line runs unbroken to the corner, and
  no free-standing sign is in shot. `signs` in the verdict drops
  ~10x; `massInRoad` stays empty; walkers and traffic gates hold.
- T2: a shopfront legible AS a named shop in a noon still; lamp heads
  visible at night; parked cars in frame; phone box standing.
- T3: a queue visible at a shelter in at least one committed still;
  reaction events counted on the done line.
- T4: noon stills stop reading as pasted-on (judged, plus AO/shadow
  numbers); smoke and gulls in motion in the played build.
