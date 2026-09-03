# Procedural density and surface history — how a team with no artists gets a hand-made street

> **STATUS: SPEC, 2026-08-25.**
> Research for M17.10 R2/R3 (`visual-bar-spec.md` §4). The question this
> answers is NOT "how did Rockstar do it" but **"what produces urban density
> and surface history when the only labour available is code, rules and CC0
> assets"**. Every recommendation names the file it lands in. Techniques we
> cannot build are marked **[NOTE — not a recommendation]**.
>
> **Evidence tags.** `[MEASURED]` = run in this repo this session, command
> named. `[SOURCE]` = from a cited page, URL in §10. `[INFERENCE]` = my
> reasoning on top of those, and flagged so it can be argued with.

---

## 0. FIRST: three things in the brief that the repo contradicts

Rule 1. I checked before writing the plan, and two of the three gaps are not
where they were thought to be.

**0.1 — "47 road models with exactly ONE placed" is true, and it is not 47
placeable props.** `ls ledger/Assets/Props/city-kit-roads` `[MEASURED]`:

| class | count | models |
|---|---|---|
| lamp columns | 7 | `light-{curved,square}`, `-double`, `-cross`, `construction-light` |
| traffic signals | 5 | `traffic-light`, `-hanging`, 3 × `-object-` heads |
| signs | 11 | `road-sign-{empty,stop,street,warning}` ± `-object-`/`-hanging`, 3 × `sign-highway-*` |
| site kit | 2 | `construction-barrier`, `construction-cone` |
| **road TILES with integral barriers** | **22** | `road-*-barrier` — bends, crossroads, driveways, roundabout, slants, splits |

So the real finding is better than the brief: **25 of the 47 are street
furniture that can be placed today against our procedural roads**, and the
other 22 are road SURFACE geometry that will fight `WorldBuilder`'s generated
carriageway and should be marked "not for this game" on the reach ledger
rather than left reading as unused work. `city-kit-suburban`'s 13 are 3
building types, **9 fence panels** and 1 planter — and the fences are the
prize, not the buildings (§4.4).

**Scale, measured** `python3 tools/prop-dimensions.py cone` `[MEASURED]`:
`construction-cone` is 7.50 × 9.38 × 7.50 kit units. A standard UK cone is
750 mm tall, so the kit reads **~12.5 units per metre** `[INFERENCE]`, which
puts `light-curved` (67.5) at 5.4 m and `traffic-light` (51.5) at 4.1 m —
both plausible for a British residential street. **Do not trust that factor
into a build**: measure one placed cone in `review_day1_noon.jpg` against a
1.7 m body before committing the scale constant.

**0.2 — "No overhead wires" is false.** `ledger/Assets/Scripts/Game/StreetFurniture.cs`
already has `BuildOverheadCables()` (cross-street cables every 7 m on
lanes/streets under 14 m wide, gated on both ends having a wall via
`WorldBuilder.MassAt`) and `BuildTelegraphPoles()` (avenues ≥ 45 m, a pole
every 30 m on one side, two wires per span) `[MEASURED]`. What is missing is
not the system, it is the **curve, the count and the vocabulary**: every wire
is two straight `Cube` primitives meeting 0.35 m low, there are no dropwires
to houses, no aerials, no washing lines. §5 is an upgrade, not a build.

**0.3 — decals are wired and the placement is roll-based, not rule-based.**
`DecalLayer.cs` (571 lines) loads 16 ambientCG sets from
`StreamingAssets/Decals/ambientcg` and places road/wall quads off
`Dressing.Roll` `[MEASURED]`. `Furniture.cs` places bins and bollards the
same way: `if (Dressing.Roll(n.X, n.Z, 31) < 0.55)` at a street NODE. That is
**a scatter with a stable seed** — it will never read as placed, because
nothing in it knows what a doorway is. That single fact is the subject of §1
and it is the highest-leverage change in this document.

---

## 1. THE ONE ARCHITECTURAL CHANGE THAT MAKES EVERYTHING ELSE CHEAP

**Placement rules belong in `Core`, as pure functions returning placements.**

Today the rules live in `Game/Furniture.cs` and `Game/DecalLayer.cs`, which do
not compile in this container. Every rule iteration therefore costs a
~28-minute Windows round trip and one Unity licence seat. That is why the
placement is a one-line roll: **nobody can afford to tune a rule that takes
half an hour to see.** This is `instruments.md`'s standing rule ("measurement
arithmetic and formatting live where the tests run") applied to placement, and
it is the same argument.

The shape:

```csharp
// Core/Placement.cs — pure, tested, no UnityEngine.
public struct Placed {
    public string Key;          // prop key or decal set name
    public double X, Z, Y;
    public double Yaw;          // degrees
    public double Scale;
    public string Anchor;       // "kerb", "servicedoor", "alleymouth", ...
}

public static class Placement {
    // Everything the rules need, and nothing that needs a GameObject.
    public static List<Placed> Street(StreetEdge e, IReadOnlyList<Dressed> faces,
                                      IReadOnlyList<Anchor> anchors, double prosperity);
}
```

`Game/Furniture.cs` shrinks to a loop that instantiates what the list says.
Three things fall out immediately:

- **Rules become unit-testable** in `CoreTests`, locally, in seconds. "A bin
  is never placed mid-frontage" becomes an assertion, not a hope.
- **A preview tool becomes possible.** `tools/placement-preview.py` reads a
  JSON dump of `Placement.Street` over the real town plan and draws a
  top-down SVG of every prop, its anchor and the clear walking strip. Rule 12:
  a feedback channel that costs seconds beats one that costs half an hour, and
  this one needs no Unity at all.
- **The verdict gets a real denominator** — `propsByAnchor=kerb:412/door:88/alley:37`
  answers "did the rules fire" separately from "did the props render", which
  `Placed` alone cannot (rule 3b).

**Build order:** do this FIRST, in the same batch as §2. Every subsequent
section assumes it. `[INFERENCE — the reasoning is the repo's own round-trip
cost, not a cited source.]`

---

## 2. RANKED — the five that change a frame soonest

Ranked by visible-impact-per-unit-work, with the build named. Detail in the
numbered sections.

| # | technique | what it changes in the frame | build | assets |
|---|---|---|---|---|
| **1** | **Anchor-rule placement of the 25 roads-kit furniture models + 9 suburban fences** (§3) | pavements stop being empty; lamps, signals, signs, cones, fences make a silhouette down the street | `Core/Placement.cs` rules + `Furniture.cs` loop | **none — already on disk** |
| **2** | **British road markings from the real TSRGD numbers** (§6.4) | the ground carries information: zebras, stop lines, give-way, centre dashes, box junctions, worn arrows. Reads as Britain in one glance | generate quads/textures in code, feed existing `LedgerDecal` | **none — pure numbers** |
| **3** | **Wire upgrade: catenary sag, dropwires to eaves, TV aerials, washing lines** (§5) | the sky — the brightest band in every reference frame — gets cut by structure; the street reads enclosed | rewrite `Wires`/`Cable` as one combined polyline mesh | **none — primitives** |
| **4** | **Vertex-colour contact dirt and wear, computed at generation** (§4.1) | every object grounded; corners and bases darkened; no surface one flat tone. This is the PS3-era method and the repo's own scorecard already says GTA V used it | write colours in `WorldBuilder`; one custom surface shader | **none** |
| **5** | **Facade grammar with terrace-level coherence + shopfront recess** (§7) | buildings stop being boxes with a texture: rhythm, depth, chimney stacks, door-colour variety | `Core` split/repeat grammar; recess is 4 quads | **none** (kit optional) |

Everything below #5 — poster stacks, graffiti, the tide line, hex-tiling — is
real and lower-yield-per-hour. They are in §4 and §6 with the same treatment.

---

## 3. PROCEDURAL PLACEMENT THAT READS AS INTENTIONAL

### 3.1 Why our current placement cannot read as placed

`Dressing.Roll(x, z, salt) < 0.55` at a node is a **hash-stable uniform
scatter**. Stability is right and is worth keeping — the same corner has the
same bin every run, which is what makes stills comparable. But uniform
scatter has two properties a real street does not:

- it has **no anchor** — nothing about the position is caused by a doorway, a
  kerb, a corner or a wall, so the eye finds no reason for the object;
- it **clusters and gaps at low frequency**, which is exactly what the human
  visual system is most sensitive to. Uniform random sampling produces
  low-frequency clustering; blue-noise/Poisson-disk distributions do not
  `[SOURCE — Bridson; blue-noise discussion]`.

### 3.2 The rule vocabulary — anchors, not surfaces

**The single principle: scatter over ANCHORS, never over area.** An anchor is
a named feature the town plan already knows about. Ours, all derivable from
existing data `[MEASURED — `StreetMap.Edges/Node`, `Dressing.Facade` returns
`List<Dressed>`, `WorldBuilder.BlockSetback`, `MassAt`, `PointClear`]`:

| anchor | derived from | props it feeds |
|---|---|---|
| **kerb line** | edge centreline ± `Width/2` | lamps, bollards, gullies, parked cars, double yellows, cones |
| **furniture zone** | kerb line + 0.6–1.0 m inward | every standing object; nothing goes mid-pavement |
| **shop door** | `Dressed` premises with `HasFascia` | A-boards, planters, litter bin, gum density, poster stack |
| **service door** | rear/side elevation, no fascia | wheelie bins, crates, pallets, oil stain |
| **alley mouth** | `Kind == "lane"` meeting a wider edge | graffiti, bins, puddle, a leaning bicycle |
| **junction corner** | node with degree ≥ 3, corner radius arc | phone box, pillar box, fingerpost, litter bin, drain, tactile paving |
| **party-wall line** | facade bay boundaries | drainpipes, chimney stacks, aerials, terrace breaks |
| **quay edge** | dock district boundary | bollards, mooring rings, tide line, crates, chain |

If a prop has no anchor, it should not exist. That one test removes the
sprinkled look before any spacing number is chosen.

### 3.3 The rules people actually use

Concrete, in the form the brief asked for. Sources marked; the rest is
`[INFERENCE]` from British street practice and should be argued with, not
trusted.

**Alignment and clustering (this is real published guidance, not taste).**
UK council street-furniture guidance says items should be **sited close to
other elements — lamp columns, bus shelters — to reduce the area furniture
takes up collectively**, that **bollards must line up with each other and be
regularly spaced**, and that **bins must not obstruct pedestrian flow**
`[SOURCE — RBKC/Camden street furniture guidance, via search]`. That is three
implementable rules for free:

1. **CO-LOCATE.** A new prop prefers a position within 2 m of an existing one
   over a free stretch of kerb. Implement as: place the "leaders" first
   (lamps, signals, shelters), then run every follower kind with a *bonus*
   for proximity to a leader. This is the exact inverse of Poisson-disk and it
   is why real streets have bare stretches and knots.
2. **ALIGN.** Everything in the furniture zone shares one offset from the kerb
   per street, per side. Jitter the offset by ±0.05 m, not ±0.5 m.
3. **RESERVE THE DESIRE LINE.** Keep a continuous 1.2–1.5 m clear strip on the
   pavement. Any placement that breaks it is rejected and retried at the next
   anchor — which is also a gameplay rule, because `NpcWalker` uses that strip.

**Spline-driven spawning with recipes.** Production systems place props along
street splines by recipe — e.g. *garbage cans at every intersection, street
lights every 15 m*, with decals scattered over the road `[SOURCE — 80.lv
"Building Urban Playgrounds", via search snippet]`. Tiny Glade picks props
**near windows, doors and gates, selected by CONTEXT — wall alignment, paths,
grass** `[SOURCE — same]`. Far Cry 5's toolkit shipped dedicated **fence and
power-line tools that build along splines** `[SOURCE — GDC 2018 / PlayStation
Blog coverage, via search]`. Marvel's Spider-Man placed open-world content by
rule: **at least 150 m apart, on alternate sides of the street, and more than
9 m from a crosswalk** `[SOURCE — SIGGRAPH 2019 talk, via search snippet;
the PDF itself is egress-blocked from this container]`.

That last one is the shape to copy exactly: **a minimum separation, an
alternation, and a keep-out from a named feature.** Three numbers per prop
kind, and it produces placement that reads as decided.

**Our recipe table** (`[INFERENCE]`, to be tuned from the preview tool, not
invented into a gate — rule 2):

| prop | anchor | spacing / count | alternation | keep-out |
|---|---|---|---|---|
| lamp column | furniture zone | 25–35 m | alternate sides if street < 9 m | 1.5 m from any doorway |
| litter bin | junction corner, shop door, stop | ≤ 1 per 60 m | — | must be within 2 m of a leader |
| wheelie bins (2–4) | **service door only** | 1 per service door, p≈0.6 | — | **never on a fascia frontage** |
| builder's skip | kerb, in front of a repaired house | ≤ 1 per 200 m | — | not across a dropped kerb; cones at both ends |
| bollard run | corner radius, build-out | 1.2–2.0 m apart, ≥ 3 in a run, aligned | — | — |
| bench | back to wall or railing, facing road | near stop or green only | — | never mid-pavement facing a wall |
| cones | roadworks patch | **groups of ≥ 3 in a line**, one gap | — | a lone cone only at p ≈ 0.1, as debris |
| phone box / pillar box | junction corner | 1 per district | — | never mid-terrace |
| A-board | 0.5 m out from a retail frontage | p≈0.4 per shop, daytime | — | inside the clear strip → reject |
| gully / drain cover | kerb, camber low point | 25–30 m, always at corners | — | — |
| parked car | kerb where double yellows ABSENT | prosperity-driven density | alternate side per street | never across a driveway |
| planter | flanking a shop door | **in pairs** | — | — |

**The clustering grammar (the part that makes it look hand-made).** Set
dressing advice is consistent: build **asymmetric, fractal clusters** — "a
repeated logic" — and **break the pattern with hero props and controlled
asymmetry**, but stop short of imitating natural mess, which reads overdone
`[SOURCE — Level Design Book / environment-art playbooks, via search]`.
Implementable as a **leader/follower** pass:

```
leader  := rule-placed prop at an anchor
follower:= 1..3 props within 1.5 m of the leader, chosen from that leader's
           companion set, with a RELATION: leaning(wall|leader),
           stacked(leader), knocked-over(ground), spilled(radius 0.6)
```

A bin gets a bin bag and a flattened box. A skip gets two pallets and a
cone. A lamp gets a bin and a bicycle. **Followers are what read as history;
leaders are what read as municipal.**

### 3.4 Poisson-disk vs rules — what each is for

Poisson-disk sampling rejects any candidate closer than `r` to an accepted
one, giving blue noise: no large clusters, no large gaps, irregular at high
frequency `[SOURCE — Bridson SIGGRAPH 2007]`. Bridson's algorithm is ~40
lines and runs in O(n) with a background grid.

**Use it for exactly one thing: choosing which anchors get used**, with `r` =
the recipe's minimum spacing, sampling in 1-D along the kerb parameter rather
than in 2-D over the pavement. Do **not** use it for the prop position — the
position comes from the anchor. Jittered/stratified sampling is the cheaper
cousin and reduces but does not eliminate clustering `[SOURCE]`; along a
1-D kerb the difference is small, so **jittered-grid along the kerb is
adequate and Poisson is a refinement**, not a prerequisite `[INFERENCE]`.

### 3.5 Wave Function Collapse — **[NOTE — not a recommendation for us]**

WFC produces output that matches the input *locally*; **it has no global
structure**, and it cannot directly enforce global requirements such as
connectivity, uniqueness or ordering without bolted-on constraints that
substantially increase setup cost `[SOURCE — boristhebrave; WFC constraint
literature]`. Our city already HAS its global structure — `StreetMap`,
districts, `Dressing.KindAt`, a hand-authored town plan. WFC would replace the
one part we are happy with and would not touch the part that is empty. Read
it as ruled out with a reason, so nobody re-derives it as promising.

Where a WFC-ish idea *does* pay: **adjacency tables for facade modules**
(§7.3) — "a shopfront module may not sit above a shopfront module", "a bay
window may not neighbour a garage". That is a local constraint, which is the
thing WFC is good at, and it needs about 30 lines, not a solver.

---

## 4. PROCEDURAL WEATHERING AND SURFACE HISTORY

The reference argument is already in `visual-bar-spec.md` §2 frame 3:
**dirt + depth + density carry a frame with no interesting light in it.**
This section is how to compute that dirt rather than paint it.

### 4.1 Vertex-colour weathering — the highest-value item here

We **generate** our geometry, which means we know its topology at build time.
That is a bigger advantage than any shader: a painted AO map is what you do
when you did not author the mesh.

Baking AO into vertex colours is standard for meshes that use tiled textures,
precisely because tiling prevents unique lighting living in the texture, and
it needs no UV unwrap `[SOURCE — polycount wiki / VertexDirt]`. Its weakness
is that resolution follows vertex density `[SOURCE]` — which for us is a
subdivision parameter, not a constraint.

**Write three channels at generation time in `WorldBuilder`:**

| channel | meaning | computation |
|---|---|---|
| **R — contact** | how enclosed this vertex is | `smoothstep(0, 1.5m, height above ground)` × `1 - concavity` at party-wall and wall/ground joins |
| **G — exposure** | rain-washed vs sheltered | `saturate(dot(normal, up))` × `1 - shelteredBy(overhang, awning, arch)` |
| **B — wear** | polished by traffic | proximity to door threshold, kerb edge, handrail, stair nose |

Then a surface shader multiplies: dirt where R is low, streaks where G is
high on a vertical, bleached wear where B is high. **Unity's built-in
Standard shader does not read vertex colours**; a custom surface shader with a
vertex modifier and `float4 color : COLOR` in the input struct does
`[SOURCE — Unity surface-shader manual, via search]`. We already ship nine
hand-written shaders, so this is a normal-sized change, and it is
**built-in-pipeline native — no URP needed.**

**Why it beats decals for this job:** it costs zero draw calls, zero texture
memory and zero overdraw, it darkens every corner in the town at once, and it
is the technique the repo's own GTA V scorecard lists as "baked AO in
textures/verts — vertex-bake still open".

### 4.2 The tide line — the one weathering effect a port has and nothing else does

A **world-space horizontal band**: below `quayY + 0.6 m`, walls and quay
stone get a bleached salt band with a fairly hard top edge; below `quayY +
0.2 m`, a green-black weed band. One comparison against world Y in the
shader, no texture, no mask, no placement pass. Nothing else in this document
says "port" as loudly for as little work `[INFERENCE]`.

Add the same idea at the other end: a **splash band** 0.0–0.4 m up every
kerbside wall, which is road spray, and is why real British walls are dark at
the bottom.

### 4.3 Streaking below sills and rooflines

The physical rule is simple: **water is shed by a horizontal ledge and runs
down what is under it.** Since we place the sills, parapets and string
courses, we know every ledge.

Two implementations, both built-in-safe:

- **Decal quad per ledge** (do this): a `Leaking005` quad — already on disk
  `[MEASURED]` — 1–2 m tall, hung directly below every sill and at every
  parapet drip, width = ledge width, alpha fading downward. Deterministic,
  batched, no shader work.
- **Shader gradient**: blend a vertical streak mask by surface inclination,
  the standard approach being to modulate horizontal-vs-vertical rain effects
  by the world-space surface normal `[SOURCE — rain/streak shader writeups,
  via search]`. Cheaper per-pixel, but it cannot know where the ledge is
  without the vertex channel from §4.1 — so it is the *second* step, after
  4.1 lands.

Rust streaks get the same treatment under every metal fixing: brackets,
downpipe clips, railings, signage bolts.

### 4.4 Detail maps — free surface grain in the built-in pipeline

Unity's Standard shader has **Secondary/Detail maps: a second albedo and
normal, with independent tiling and offset and optionally a second UV set,
plus a detail mask** `[SOURCE — Unity manual]`. Tiled small and repeated many
times, they give sharp close-up detail without a huge base texture.

This is free density at player height, which is where all five reference
frames are shot. **Apply to: brick (mortar grain), asphalt (aggregate),
paving (grit), render (float marks).** No fetch, no new asset, one material
field.

### 4.5 Moss, damp and the shade rule

`Moss001` is on disk `[MEASURED]`. The placement rule is physical and
computable: **moss where it is damp and dark** — north-facing (in the UK),
low (< 1.5 m), and sheltered, i.e. exactly `G low + R low` from §4.1.
Pavement-crack weeds follow the same rule at slab joints, using the
Quaternius grass tufts listed in `visual-bar-sources.md` §F.

### 4.6 Stochastic / hex tiling — **[NOTE — optional, and modern]**

Heitz & Neyret's hex-tiling breaks tiling repetition by sampling a texture at
three randomly-offset hex tiles and blending with a variance-preserving
operator; Mikkelsen's adaptation replaces the expensive histogram step with a
contrast ramp, and there is an MIT demo repository `[SOURCE — JCGT paper;
mmikk/hextile-demo]`. It costs 3 texture fetches plus a blend per material.

**PS3-era games did not do this** (it is a 2018–2022 technique). Our bar is a
2013 console game, and the era-correct answers to repetition are detail maps
(§4.4), vertex colour (§4.1) and decals (§6) — all of which we need anyway.
Park hex-tiling until those three have landed and the ground still reads
tiled.

---

## 5. OVERHEAD WIRES — the cheapest silhouette in the project

### 5.1 Why they matter more than their cost

`visual-bar-spec.md`'s own reference decomposition says it twice: frame 2 is
"almost nothing but light... poles and wires as silhouettes", and **the WIRES
are what give the sky depth**. The value structure work in R0 is making the
sky the brightest broad surface in the frame — which means a bright, empty,
untouched band across the top of every shot. Wires are the only thing in this
document that puts structure INTO that band, and they cost a few hundred
triangles.

### 5.2 The curve — use a parabola, and know why

The hanging-cable shape is `y = a·cosh(x/a)`, sag `D = (T/w)·[cosh(wL/2T) − 1]`.
**For overhead-line work the curve is normally approximated as a parabola,
with sag error below 0.5% when sag/span is under about 5%**
`[SOURCE — overhead-conductor sag references]`.

Our spans are 30 m with sag well under 1.5 m — a ratio of ~4% — so the
parabola is exact enough to be indistinguishable, and it removes the
`cosh` inversion entirely:

```csharp
// Core/Catenary.cs — pure, testable, no Unity.
// u in [0,1] along the span; sag is the metres the middle hangs below
// the straight line between the two ends. Parabolic, because at
// sag/span < 5% the error against a true catenary is under 0.5%.
public static Vector3 Point(Vector3 a, Vector3 b, double sag, double u)
{
    var straight = Lerp(a, b, u);
    straight.y -= (float)(4.0 * sag * u * (1.0 - u));
    return straight;
}
```

Sample 8–10 points per span. Anything more is invisible; anything less shows
the bend that `Cable()`'s own comment admits to today.

### 5.3 What actually hangs over a British port town in the late-analog years

This is the part that makes it OUR street and not Los Santos. Ranked by
silhouette value `[INFERENCE, with the catenary-lighting and pole facts
sourced]`:

1. **TV aerials on every chimney stack.** A 6–10 element yagi per household,
   pointing the same way down a whole terrace (they all face the same
   transmitter) with two or three wrong ones. This is the single most
   period-specific silhouette available and it is completely absent from
   modern cities — which is why a modern reference photo will never suggest
   it. Cost: ~20 triangles each, built from primitives.
2. **BT telegraph poles with DROPWIRES.** Poles are typically **8–10 m tall**
   and the maximum dropwire/aerial-cable span is **60 m** `[SOURCE — UK pole
   guidance / GPO material, via search]`. Our poles are 7 m and spaced 30 m
   `[MEASURED]` — inside spec, fine. **The missing detail is the dropwire**:
   a thin wire from the pole's crossarm down to a bracket at each house's
   eaves. A pole with 8 wires fanning out to 8 houses reads instantly as
   Britain; two parallel wires read as a fence in the sky.
3. **Catenary-suspended street lighting.** A lamp hung on a cable strung
   between two buildings, used to **eliminate the visual clutter of lamp-post
   rows and save space on narrow streets**, long popular in continental
   Europe and increasingly in the UK `[SOURCE — catenary lighting industry
   pages]`. This is the correct lamp for our narrow lanes, and we already
   have the cable system to hang it on.
4. **Washing lines across back alleys and courts** — the domestic version, and
   a social-memory hook: whose washing is out tells you who is home.
5. **Bunting and festoon lighting** on a seafront or above a market street.
6. **Dockside**: crane cables, mooring lines, chain, and the derrick lines of
   a moored vessel.

### 5.4 The build

Replace `Segment()`'s per-segment `CreatePrimitive(Cube)` with **one combined
mesh for all wires in a district**, built as a camera-agnostic quad strip
(2 triangles per segment instead of 12) or a 3-sided extrusion:

- one `Mesh`, one material, **one draw call for the whole town's wires**;
- **clamp apparent width** so a wire never falls under ~1.2 px (the §7.11
  clamp `visual-bar-spec.md` already specifies) — a wire that aliases in and
  out between frames is worse than no wire;
- sag from span: `sag = span × 0.025` for telecom, `× 0.04` for a washing
  line, `× 0.01` for a lighting catenary under tension.

**Verdict keys to add** (rule 3b, denominators included): `wireSpans`,
`wireDropwires`, `wireAerials`, `wireSegments`, and `wireSkyCover` — the
fraction of the sky band above the horizon that has any wire pixel in it, per
`ref_1..ref_5` still. That last one is the number that answers "does the sky
have structure", which no count can.

---

## 6. DECALS AT SCALE

### 6.1 What is available to us, honestly

| approach | verdict |
|---|---|
| **URP Decal Renderer Feature** | **NOT AVAILABLE.** URP-only `[SOURCE — Unity URP docs]`. We are built-in. |
| **Built-in `Projector` component** | **DO NOT USE for static decals.** It re-renders the receiving geometry: Unity draws the mesh once, then again for the projector, roughly doubling triangles — bad when the ground is one large batched mesh `[SOURCE — Unity forum/manual discussion]`. |
| **Mesh decals (a quad or a projected mesh, drawn as normal geometry)** | **This is our road.** Low rendering cost, works in a forward renderer `[SOURCE — Driven Decals docs]`. It is also what our `LedgerDecal` already is. |
| **Runtime shader projection** | for dynamic marks (bullet holes, footprints) only. Not needed. |

`Anatta336/driven-decals` is **MIT** (examples CC-BY 4.0) `[SOURCE — its
documentation]` and is URP-targeted, but the useful part is the *idea*, not
the code: project the decal quad through the surface below it and bake the
result into a mesh that conforms. A built-in fork exists
(`SmirnovVladimirPanoramik/driven-decals-built-in`) — **check its licence at
fetch time before taking a line of it.**

### 6.2 Making thousands cheap

Our shader is hand-written (`Hidden/LedgerDecal`, `Blend DstColor Zero`,
`ZWrite Off`, `Offset -1,-1`) `[MEASURED]`, which matters: **GPU instancing
does not work with Shader Graph shaders in the built-in pipeline**
`[SOURCE — Unity manual]`, and ours is not one, so instancing is open to us.

Two levels, do both:

1. **Atlas + instancing.** Put all road grime into one atlas page and all
   wall grime into another; give each decal quad its UV rect via
   `MaterialPropertyBlock`; enable instancing. Draw calls collapse from
   one-per-decal to a handful. This alone unblocks "thousands".
2. **Combine per block.** For decals that never move — which is all of ours,
   since placement is deterministic — build **one combined mesh per block per
   atlas page** with `Mesh.CombineMeshes` at world-build time. That is
   **one draw call per block**, no per-object overhead at all, and it is
   exactly the PS3-era answer. Cost: the combine pass at load, and the loss of
   per-decal culling (irrelevant at block granularity).

**Watch the overdraw, not the draw calls.** Multiply-blended quads are
fill-bound. Cap decals per square metre and keep them off each other; the
verdict should print `decalOverlapWorst` (the most decal quads any sampled
pixel has stacked) beside the count, or "thousands of decals" will land as a
frame-rate regression that reads as a mystery.

### 6.3 Where decals go — the placement rules

Same anchor discipline as §3. `[INFERENCE, physically derived; the GTA road
practice in the last row is sourced.]`

| decal | anchor rule | why |
|---|---|---|
| **gutter grime** | a continuous 0.3–0.5 m strip against every kerb, ALWAYS | water runs to the kerb; a clean gutter is the tell that a road is fake |
| **oil / drip stains** | parked-car bays, junction stop lines, taxi ranks, loading bays, garage forecourts | engines idle where traffic stops |
| **tar seams** | along the carriageway centre, along the kerb joint, and **perpendicular scars** from the building line to the centre | the perpendicular ones are service trenches — gas, water, cable — and they are the marks real roads have that game roads never do |
| **patch rectangles** | axis-aligned to the road, 1.5–4 m, at junction mouths and over the trench scars | patches follow digs, not randomness |
| **worn markings** | on top of the §6.4 fresh markings at 30–60% alpha, heaviest in the wheel tracks | paint wears where tyres run, not uniformly |
| **manhole / gully covers** | kerb line every 25–30 m; centre-line covers at junctions | `ManholeCover011` is on disk |
| **poster stacks** | blank wall panels 1.2–2.4 m above pavement, **clustered in overlapping stacks of 3–6** near shop doors, bus stops and alley mouths; torn at the stack's edges | one poster reads as a sign; six overlapping read as time passing |
| **graffiti** | alley walls, roller shutters, bridge/underpass abutments, the backs of signs; height band 0.8–2.2 m | a tag needs an arm's reach and no witness |
| **chewing gum** | density peaks within 3 m of any threshold or stop | people stand where they wait |
| **rust streaks** | below every metal fixing (§4.3) | |
| **road surface itself** | GTA V used **separate tiling textures for kerb, road and pavement as submesh materials**, with many marks baked into the road texture and decals kept for special cases `[SOURCE — polycount discussion of GTA V road texturing, via search]` | this is the era-correct split, and it argues for a **richer base road texture** as well as decals — not decals alone |

### 6.4 British road markings — free density from real numbers

Nothing here needs an asset. The UK Traffic Signs Manual Chapter 5 gives the
dimensions `[SOURCE — TSM Ch.5 / TSRGD, via search of Wikisource + DfT PDF]`:

| marking | specification |
|---|---|
| **double yellow lines** | **75 mm** wide at ≤ 40 mph (100 mm above, 50 mm in sensitive areas); laid ~**250 mm** from the carriageway edge; **the gap between the two lines equals the line width** |
| **zebra crossing stripes** | black and white equal, **not less than 500 mm nor more than 715 mm** wide |
| **stop line** | continuous, **200 mm** (urban) or 300 mm |
| **give-way line** | broken, **500 mm mark / 500 mm gap**, **200 mm** wide |
| **give-way triangle** | leading edge **2100–2750 mm** back from the transverse marking |
| **centre line** | **4 m mark / 2 m gap** at ≤ 40 mph (6 m / 3 m above) |

We already draw double yellows in `Furniture.BuildYellowLines()` `[MEASURED]`
— **check the width against 75 mm and the gap rule at the next landing.**
Everything else in that table is a new generator of maybe 150 lines in
`Core`, emitting quads for `DecalLayer` to draw, and it makes every junction
in the game read as a British junction. **Add box junctions, SLOW/BUS
legends, hatched centre islands and parking bay corners from the same
generator.**

Judged as impact-per-hour this is second only to the furniture pass, because
it needs no download, no licence check and no artist judgement — only
arithmetic — and it lands on the ground plane, which the reference
decomposition calls the widest tonal variety in the frame.

---

## 7. MODULAR KIT-BASHING AND FACADE GENERATION

### 7.1 The grammar

CityEngine's CGA is the canonical form and the vocabulary transfers directly.
**CGA has no loop; repetition is the split operator with `*`**, and the
standard facade workflow is **facade → floors → tiles, where a tile is wall
plus window**; the ground floor is split at a fixed height and the upper
floors repeat with `~` so a whole number of floors always fits whatever the
building height is `[SOURCE — CityEngine Tutorial 6/9]`. The Houdini variant
of the same idea splits a **level grammar** (vertical) from a **bucket
grammar** (horizontal), with rules written as strings like `C|(A)*|C` —
corner, repeating bay, corner — and a JSON building-definition file per style
`[SOURCE — kiryha Houdini wiki, fetched]`.

**That maps onto `Core` almost unchanged**, and `Dressing.Facade` already
returns a `List<Dressed>` — so the grammar has a home and a caller.

```
Terrace  := Break | House{5..12} | Break                // coherence unit
House    := Ground | Upper{n} | Roofline
Ground   := Door | Bay{1..2}          (retail: Fascia | Recess | Stall)
Upper    := Bay{2..3}
Bay      := Pier | Window | Pier
Roofline := Eaves | Parapet | ChimneyStack(shared, every 2 houses)
```

### 7.2 The British numbers

`[SOURCE — terraced-housing references, via search]`:

- terrace frontage **4.5–6 m** typically, **3 m at the smallest, 7 m+ at the
  largest**;
- plan depth **15–18 m** to the rear;
- **2 storeys** normally, 3½ with a half-basement in hilly ground (a port
  town on a slope is exactly that case);
- symmetrical door/window arrangement, steep pitched roof;
- bay windows from the 1850s–60s on the ground floor, two-storey bays later;
  front gardens from **1 m** to 10 m in better areas.

Those are the parameters, not decoration. A generator with frontage 4.8 m,
storey 2.9 m, ground 3.1 m produces a terrace; the same generator at 8 m and
4 m produces something that is not British and nobody will be able to say why.

### 7.3 How to avoid the obvious repetition — vary at the RIGHT level

**This is where our procedural boxes are going wrong, and it is a
counter-intuitive fix.** Randomising each building independently is what
makes a street look generated. A real terrace is the opposite: it was built
in one go by one builder, so **rhythm, brick, string course, roof pitch and
storey height are IDENTICAL for 5–12 houses at a time**, and everything that
varies is what the residents did afterwards.

So: pick per **terrace** — brick tone, bay width, storey height, window
subdivision, roof pitch, string course, cornice. Pick per **house** — door
colour, curtain state, whether the window has been replaced with UPVC (a
1990s tell), net curtains, front boundary (wall/railing/hedge/nothing), bin
presence, a satellite dish, a repaint. Terrace BREAKS are where variety is
allowed: a corner shop, a bomb-gap infill, a chapel, an alley, a change of
level.

`[INFERENCE, and it is the strongest single claim in this section: it is
also free — it is a change in WHERE the random rolls are taken, not in how
many.]`

Standard supporting practice: use **modular variation rules, decals, set
dressing and material changes, and break patterns with hero props and unique
silhouettes**; and pair modular kits with **decals for grime, leaks and
damage — the combination is how modern environments avoid the "too clean
modular kit" look** `[SOURCE — environment-art guides, via search]`.

### 7.4 Trim sheets

A trim sheet is a texture built from horizontal strips — concrete base, metal
edging, moulding — where a mesh slides its UVs along a strip and reuses it at
any length; **one 2K sheet can texture an entire building kit**, and after it
exists, texturing a new mesh is a UV operation rather than a texturing
project `[SOURCE — trim-sheet workflow guides, via search]`.

For us the honest reading is: **a trim sheet is an artist deliverable, and we
have no artist.** But two things make it reachable anyway `[INFERENCE]`:

- a trim sheet can be **assembled in code** from CC0 tiling materials we
  already fetch (ambientCG): crop a 256-px strip of brick, one of stone, one
  of painted render, one of corrugated steel, stack them into one 2K page,
  and write the strip table as JSON. That is a Python job in
  `tools/citypack/`, not an art job.
- our geometry is generated, so assigning UVs to strips is a formula.

**Payoff:** the whole facade kit — sills, lintels, string courses, plinths,
cornices, downpipes, shutters — draws in one material.

### 7.5 Depth is the cheapest of all facade work

Frames 1 and 3 in the reference set are carried by recess. Numbers that are
correct for a British high street `[INFERENCE]`:

| element | depth |
|---|---|
| shopfront recess (door set back between two windows) | 0.3–0.6 m |
| door reveal in a terrace | 0.12–0.20 m |
| window reveal | 0.10–0.15 m |
| sill projection | 0.04–0.06 m |
| string course / plinth | 0.03–0.05 m |
| parapet above eaves | 0.2–0.4 m |
| downpipe standoff | 0.05 m |

A recess is four extra quads and one dark material, and it converts a painted
facade into a facade with an inside. **This is the highest ratio of visible
depth to triangles in the whole document.**

---

## 8. ASSETS — everything free, nothing bought

**Standing constraint: no purchases, no accounts, ever.** Restating what is
already established in `visual-bar-sources.md` plus what this research adds:

| source | licence | status |
|---|---|---|
| already on disk: 4 Kenney city kits, car kit, base-mesh, 16 ambientCG decal sets | CC0 | **use these first — §2 items 1, 2 and 4 need NO fetch at all** |
| ambientCG (`ambientcg.com/get?file=<ID>_2K-PNG.zip`) | CC0 | proven CI pattern; more `Leaking*`, `RoadLines*`, `Sticker*`, `Moss*` available |
| Kenney | CC0, no account | proven |
| Poly Haven | CC0 | proven pattern |
| The Base Mesh via `M3-org/base-meshes` GitHub mirror | CC0 | the ONE host reachable from this dev container |
| OpenGameArt | CC0 per item — **read each page** | proven |
| Poly Pizza | **per item CC0 or CC-BY 3.0** | **must read the licence per model and write attribution** |
| `3dtexel.com` — claims 280+ CC0 decals incl. graffiti | claimed CC0 | **[UNVERIFIED — egress-blocked from here AND from the research container. Verify from CI, read the licence text, before taking a byte.]** |
| Sketchfab CC0 graffiti decal sets (`karlwirbelwind`, 2048², albedo + opacity) | CC0 1.0 stated on the pages | `[SOURCE — search]`, unfetched; **needs a CI verification pass** |
| `mmikk/hextile-demo`, `Anatta336/driven-decals` | MIT (assets CC-BY 4.0) | reference only; §4.6 and §6.1 |
| Quaternius Downtown MegaKit | CC0 | **EXCLUDED — itch.io needs one manual click. Do not build a pipeline around it.** |

**Nothing in the top five of §2 requires any fetch.** That is deliberate: a
recommendation that begins with a download begins with a CI round trip.

---

## 9. WHAT TO MEASURE (so none of this lands unverified)

Rule 3b and `instruments.md`: every new number ships its denominator and says
what statistic it is.

| key | statistic | question |
|---|---|---|
| `propsByAnchor=kerb:N/door:N/alley:N/corner:N` | counts | did the RULES fire, per anchor kind — separately from whether meshes loaded |
| `propsRejectedClearStrip` | count | how often the desire-line reservation bit; a zero here with a high placed count means the guard never ran |
| `furniturePer50m` | median across street edges, **peak beside it** | density, and whether one street ate the budget |
| `propLeaderFollower` | ratio | are we producing clusters or a sprinkle |
| `markingKinds` | count of distinct marking types emitted | §6.4 landed at all |
| `decalOverlapWorst` | max stacked quads at any sampled pixel | the fill-rate risk, before it reads as a mystery regression |
| `wireSpans` / `wireDropwires` / `wireAerials` | counts | §5 vocabulary present |
| `wireSkyCover` | fraction of sky band with a wire pixel, **per `ref_N` still** | the only one that answers "does the sky have structure" |
| `vertexDirtWritten` | count of vertices given colours / total vertices | §4.1 ran (a zero with no denominator is indistinguishable from "not wired") |

And the one that is not a number: **the biggest-visible-difference sentence
from `visual-bar-spec.md` R1**, written at every landing. Three identical
sentences in a row means this plan is the wrong plan, whatever it says here.

---

## 10. SOURCES

Search-tool results; **`80.lv`, `polycount.com`, `adriancourreges.com`,
`history.siggraph.org`, `docs.unity3d.com`, `en.wikipedia.org`,
`boristhebrave.com`, `3dtexel.com`, `rbkc.gov.uk`, `aiandgames.com` and
`tools.engineer` are all egress-blocked from this container** — claims from
them are marked as coming via search snippets rather than a page I read. Only
`github.com` fetched cleanly.

**Placement and procedural systems**
- Marvel's Spider-Man, SIGGRAPH 2019 Talks — https://history.siggraph.org/wp-content/uploads/2022/09/2019-Talks-Santiago_Procedural-System-Assisted-Authoring.pdf *(blocked; the 150 m / alternate sides / 9 m-from-crosswalk rule is from the search summary)*
- Building Urban Playgrounds for Video Games — https://80.lv/articles/building-urban-playgrounds-for-video-games *(blocked; spline recipes, bins at intersections, lights every 15 m)*
- Procedural World Generation of Far Cry 5, GDC 2018 — https://www.gdcvault.com/play/1025557/Procedural-World-Generation-of-Far and https://blog.playstation.com/2018/03/22/the-procedural-world-generation-of-far-cry-5/ *(fence and power-line spline tools)*
- Procedural City, Houdini wiki — https://github.com/kiryha/Houdini/wiki/Procedural-City **[FETCHED]** *(level/bucket grammar, `C|(A)*|C`, BDF)*
- Environment Art — https://book.leveldesignbook.com/process/env-art *(fractal asymmetric clusters, clutter control)*
- Bridson, Fast Poisson Disk Sampling — https://www.cs.ubc.ca/~rbridson/docs/bridson-siggraph07-poissondisk.pdf
- WFC tips and tricks — https://www.boristhebrave.com/2020/02/08/wave-function-collapse-tips-and-tricks/ *(blocked; "no global structure")*
- Extend WFC to Large-Scale Content Generation — https://arxiv.org/pdf/2308.07307
- Enhancing WFC with design-level constraints — https://dl.acm.org/doi/10.1145/3337722.3337752

**Weathering, decals, shaders**
- Unity, Secondary Maps (Detail Maps) & Detail Mask — https://docs.unity3d.com/Manual/StandardShaderMaterialParameterDetail.html
- Unity, Surface Shaders (vertex colour via a vertex modifier) — https://docs.unity3d.com/Manual/SL-SurfaceShaders.html
- Unity, Projector component (Built-In) — https://docs.unity3d.com/Manual/class-Projector.html
- Unity, GPU instancing (not available to Shader Graph shaders in BiRP) — https://docs.unity3d.com/6000.3/Documentation/Manual/GPUInstancing.html
- URP Decal Renderer Feature (URP-only) — https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@14.0/manual/renderer-feature-decal.html
- Driven Decals documentation — https://github.com/Anatta336/driven-decals/blob/master/Documentation~/DrivenDecals.md **[FETCHED]** *(MIT; mesh-vs-shader projection; "mesh generation is relatively slow")*
- Built-in fork — https://github.com/SmirnovVladimirPanoramik/driven-decals-built-in
- Ambient occlusion vertex colour — http://wiki.polycount.com/wiki/Ambient_occlusion_vertex_color
- Fewes/VertexColorBaker — https://github.com/Fewes/VertexColorBaker
- Practical Real-Time Hex-Tiling (Mikkelsen) — https://jcgt.org/published/0011/03/05/paper-lowres.pdf ; demo https://github.com/mmikk/hextile-demo
- GTA V road texturing discussion — https://polycount.com/discussion/130070/gta-5-road-texturing-technique *(blocked; kerb/road/pavement as separate tiling submesh materials, marks mostly baked in, decals for special cases)*
- GTA V Graphics Study — https://www.adriancourreges.com/blog/2015/11/02/gta-v-graphics-study/ *(blocked here; already summarised in `visual-bar-spec.md` §3)*

**British specifics**
- Traffic Signs Manual Chapter 5, Road Markings — https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/773421/traffic-signs-manual-chapter-05.pdf and https://en.wikisource.org/wiki/Traffic_Signs_Manual/Chapter_5/2009/20
- Street furniture good practice — https://www.rbkc.gov.uk/sites/default/files/media/documents/Chapter%204%20-%20Street%20Furniture.pdf and https://www.camden.gov.uk/documents/20142/3777134/Street+Furniture.pdf
- Terraced houses in the UK — https://ukhousing.fandom.com/wiki/Terraced_house and https://www.propertyinvestmentsuk.co.uk/terraced-house-through-time/
- GPO poles — https://www.britishtelephones.com/gpo/pole.htm
- Catenary suspended street lighting — https://www.externalworksindex.co.uk/category/4-13728/Catenary-suspended-street-lighting/
- Catenary sag / parabolic approximation — https://industrialmonitordirect.com/blogs/knowledgebase/catenary-sag-calculator-level-and-unlevel-span-formulas-for-overhead-conductors and https://polesnwires.com/articles/conductor-length-and-sag/

**Assets**
- ambientCG — https://ambientcg.com/ · Sketchfab CC0 graffiti decals — https://sketchfab.com/3d-models/cco-decal-graffiti-textures-37d78e03040041bdb9158c7ce4aa7cd8 · 3DTexel decals *(unverified)* — https://3dtexel.com/decals/

---

## 11. WHAT I COULD NOT ESTABLISH

Named so the next session does not spend the time again.

- **No production source for street-prop DENSITY numbers** (props per 100 m in
  GTA V or comparable). Every density figure in §3.3 is `[INFERENCE]` and must
  be set from a printed series off the preview tool, not from this document
  (rule 2).
- **The Spider-Man rules are second-hand.** The 150 m / alternate-sides / 9 m
  numbers come from a search summary of the SIGGRAPH talk, not from the PDF.
  Treat the SHAPE as the finding and the numbers as illustrative.
- **`3dtexel.com`'s CC0 claim is unverified** and must be checked from CI
  before any byte of it enters the repo.
- **No CC0 source found for**: K6 phone box, pillar box, bus shelter, telegraph
  pole, TV aerial, dock crane, parking meter. `visual-bar-sources.md` already
  rules these as author-in-Core, and this research agrees — they are primitive
  compositions, and the aerial in particular (§5.3) is worth more than its
  triangle count.
- **Whether the roads-kit tiles can be salvaged.** 22 models are road surfaces
  with integral barriers; whether the barrier can be separated from the tarmac
  without a modelling package is unknown. Cheapest test: import one and read
  its submesh count.
