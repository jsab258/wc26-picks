# The quality ladder

STATUS: LIVE. Verified 2026-09-01.

CLAUDE.md's standing order is "the best possible result, not the first
working one", and it says plainly that a rule with no trigger point decays.
Its trigger point is this file: before an item is closed, the question is
asked here, and the next rung is either taken now or written down with a
name.

THIS FILE EXISTS BECAUSE THE RESPEC ORPHANED THE OLD ONE. The ladder lived
in game-design/queue.md, which v2 superseded, so from 31 Aug the mechanism
had no home in the tree anybody was working in. Nothing announced that. The
enforcement clause in CLAUDE.md kept reading as live while pointing at a
file the production queue no longer opens, which is this project's most
familiar failure wearing a governance hat.

## How to use it

One row per visible aspect. Current rung is what shipped. Next rung is the
better result available FROM RESOURCES WE HAVE, named concretely enough to
start. A blank next rung is not a finished aspect: it is a research task,
and it gets queued as one.

The ladder is not a backlog. A row belongs here only if a player or Jafar
would perceive the difference.

## Rows

| aspect | current rung | next rung, from resources we have |
|---|---|---|
| Brand identity | Eight brands with a register and a physical presence, verified against canon. | The STRINGS the world actually shows: a headline format for the Argus, a vendor-board line, a station ident and sign-off for Tideline, a chant and a tannoy line for the Town. Those are what the radio and dialogue lines consume, and without them a brand is a fact rather than a texture. |
| Dialogue, pub regular | 48 memory-conditioned lines, three rungs by three contexts, worst overlap 0.18 over 1,128 pairs. | A second archetype, so the repetition check runs ACROSS banks and not only inside one. One bank cannot be repetitive with itself in the way a street is repetitive. |
| Engine loop (D1) | Build, port and cook measured on the real machine; a UE compile is checked blind, one full round trip per hypothesis (median 10 min over 9 rows, before any cook or capture was in the loop). | Queue 032: the installed engine's own declarations for every symbol the emitter names, committed before the code is written; a compile-only lane that answers "does it compile" without a cook or a capture; everything engine-free compiled and run by g++ here before dispatch. |

## What is deliberately NOT on the ladder yet

Everything visual. The bar is the Meridian Test and the engine is undecided,
so a rung written today would be written against a renderer that may not be
the one that ships. That is a reason to wait, and it is recorded here so
that waiting is a decision rather than an oversight.

---

## The standing order in Jafar's words, carried from CLAUDE.md (2026-09-01, task 013)

CLAUDE.md was cut to standing rules plus pointers on 2026-09-01. The standing
order stays there as a law; the passage that gives it its force, in Jafar's
own words and with the examples that show what the order is against, moved
here because this file is the mechanism's home.

ONE EDIT WAS UNAVOIDABLE AND IS FLAGGED RATHER THAN MADE SILENTLY. Trigger
point 2 in the text below names `queue.md`. That was game-design/queue.md,
which the v2 respec superseded on 31 August, and it is the exact orphaning
recorded as lesson L23 in ledger-v2/studio-v2/learning.md: a live enforcement
clause pointing at a retired home, with nothing announcing it. THE LADDER'S
HOME IS THIS FILE. The close step that asks the question is in
production/queue/README.md under "Before an item moves to done/". The text is
left as written so the decay is visible rather than papered over.

### The standing order in Jafar's words, and its two trigger points

<!-- moved verbatim from CLAUDE.md lines 1569-1592 on 2026-09-01, task 013 -->

**And the standing order underneath both, 16 Aug, his words: "use creativity
and skill and available resources to get the best possible result in all
aspects of the game."** Not "make it work" — the best result AVAILABLE. The
first version of anything in this project has repeatedly been the first thing
that worked, declared done because it ran: 1K textures picked when 2K was one
field away, headless lamp posts shipped for weeks beside a fetched kit that
had heads, roughness maps left unfetched by a comment saying nothing samples
them — written by the same hand that could have made something sample them.

He asked how this gets ENFORCED, and the honest answer is that a rule with no
trigger point decays — this file is a list of proofs. So it has two:

1. **It lives here**, in the file read at every session start, which is the
   only thing the ephemeral container cannot lose.
2. **It is asked at close.** `queue.md` keeps a QUALITY LADDER — each visible
   aspect of the game, its current rung, and the known next rung from
   available resources. Before an item is closed, the question is "is this
   the best available result, or the first working one?" — and the next rung
   either gets taken now or goes onto the ladder with a name. An aspect whose
   next rung is blank is a research task, not a finished aspect.

The ladder turns "best possible" from a mood into a delta. The trap it
exists for: a pipeline that CAN ingest better assets is not the same as
better assets ingested — built is not running (rule 6), applied to quality.

## The D1b vignette scene (data, engine-neutral)

These rows describe the shared JSON and the tested layout, which survive the
engine decision, so they are not the "everything visual waits for a frame"
this file records elsewhere.

| aspect | current rung | next rung, from resources we have |
|---|---|---|
| Kerb | square 125 mm face, 915 mm blocks, gully recess cut to the measured grate | the 12 mm batter over the top 50 mm named in the JSON's kerb note, as a chamfer piece per block |
| Footed furniture | level on a 1 in 40 footway, 11 mm upslope corner float, measured | bedded: `footY = gy - halfFootprint * crossfall`; proof is floatMax near 0 and sinkMax near 0.022 on the same instrument |
| Placement bound | one scalar, widest footprint through the crossfall arithmetic | per-probe expected gap asserted to 1 mm, so a 10 mm float under a dustbin is seen |
| Crossover | kerb drops, footway does not ramp (125 mm over 2 m, named in Core) | ramp the footway over the crossover width |
| Surface tiling | WorldBuilder's 3 m and 3.5 m copied | each ambientCG set's stated physical size read at fetch and written into `surface_tiling` |
| Skies | 2K, the fetched rung | 4K, one path segment away, if the two slugs publish it |
| Kiosk and box | silhouettes at trade size, unlettered | operator mark and postal cypher as decals once item 030 lands |
| Night interiors | held `interior` material on the card | C11 cards from one `make-the-pictures` dispatch |
| Character | none placed (not yet admissible) | one held body with an idle, item 028; period wardrobe stays the research row the BOM named |
| HDRI binding | Host binds its own cube, same idiom as `SkyEnvironment` | one implementation: the Host calls `SkyEnvironment`'s loader, after the first frame |
