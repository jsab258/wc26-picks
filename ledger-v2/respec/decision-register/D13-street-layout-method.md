# D13: street layout method

STATUS: DECIDED 2026-09-02 by Jafar, dictated and recorded by the resident.
Premise level: it governs how the town itself comes into being. Answers the
pending card "How does Meridian's map get drawn?", raised by Jafar the same
day when he asked whether the layout would be copied from OpenStreetMap.

## The decision

**Phase A Meridian is drawn by hand from canon.** Option B of the three that
were put. Authored as data in the world source of truth (D1: JSON or YAML
world source of truth, generators emit engine content, binary assets are
build products), with real British port towns studied as reference and
NOTHING IMPORTED.

## The riders, all five, as given

1. **A town form bible comes before any drawing.** Morphology rules
   extracted by eye from two or three real port town references: how streets
   meet the harbour, terrace orientation to contour, alley and ginnel
   frequency, block size variance, where the railway or a cutting divides the
   town. The bible is the spec the layout is authored AND VERIFIED against.

2. **The street plan is a gameplay instrument with testable requirements**,
   written into the layout spec:
   - each district contains at least one information venue at a route
     crossing;
   - phone box and police station distances make the witness run
     interceptable at measured timings;
   - sightline pockets and overlooked yards are placed deliberately;
   - escape routes exist and are countable.

   Verified, not vibes.

3. **A reads-as-real gate.** Mechanical morphology comparison against the
   reference towns (block size variance, intersection angles, dead end
   ratio), PLUS the street level screenshot judge per D7.

4. **Scope is the Phase A town only.** Option A (traced skeleton with
   alteration, attribution, and the derived database legal check) RE-OPENS BY
   DEFAULT at Phase B kickoff for the region, where the footprint maths flips.
   Option C is rejected for the town per the authored breadth doctrine
   (vision pillar 4, constitution law 5); a grammar may be considered at
   Phase B for countryside filler only, always with an authoring pass.

5. **Reference study and internal analysis carry no licence obligation.**
   Nothing shipped derives from imported geodata under this decision. Licence
   allowlist item 6 stands UNCHANGED for any future use.

## Why the riders are the decision and not decoration

Option B on its own is the expensive option, and the expense buys nothing
unless the map is authored against something. Rider 1 is what stops "by hand"
meaning "from imagination": a hand-drawn town that has never been compared to
a real one reads as a film set, and the morphology of a real port is the part
that is hard to invent and easy to copy by eye without copying any data.

Rider 2 is why this project is drawing its own map at all. A traced road
graph is optimised for nothing: it has no reason to put an information venue
where routes cross, no reason to make a witness run interceptable, no reason
to place an overlooked yard. In a game whose moat is who saw you and who
talked, those are the map. Making them testable requirements is what keeps
"the street plan is a gameplay instrument" from being a sentence in a
document.

Rider 3 is the honest half. Hand-authoring against taste alone puts the whole
map inside the one bottleneck D7 exists to widen, so it gets a mechanical
comparison as well as a judged one.

Rider 4 keeps the expensive answer bounded to the footprint that justifies
it, and names the moment it is reconsidered rather than leaving it to be
re-argued from scratch. Roadmap row 5 already says the region's gates are set
at kickoff, so this rider lands where the roadmap already opens.

## What this does not decide

The bible's reference towns are not chosen here. The layout spec's numbers
(how many escape routes is enough, what interception timing is the target)
are not set here and must be measured before they are set, per the standing
rule against a threshold with no series behind it. Nothing here says what the
data format is beyond D1's JSON or YAML.

## Not yet queued, and named rather than assumed

The three riders that are work (the town form bible, the layout spec with its
testable requirements, the reads-as-real gate) are NOT in the queue as this
record is written. Queue refill is a director trigger and this record is a
resident applying dictated text, so the items are named here for the next
director spawn rather than filed by the hand that recorded the decision.
