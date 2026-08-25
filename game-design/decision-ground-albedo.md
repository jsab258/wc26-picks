# Decision — ground albedo before decals (director, 25 Aug 2026)

> **STATUS — LOG, 2026-08-25. NOT CURRENT after the next dry landing is read.**
> Directed decision off the artifact-reader's dry-tour report
> (`agent-reports/dry-tour-stills-read.md`, verdict 6137608). Written here and
> not appended to `decisions-pending.md` because that file is, in its own
> header, the queue of things only Jafar can answer — nothing below needs him:
> the GTA band is his 21 Aug order and this is execution of it.
> `templates/decision.md` does not exist to copy; this doc states its shape.

## The finding this rules on, verified

The queue's standing conclusion — "the remaining visual gap is surface
history, add decals" — is overturned. The reader's evidence is confirmed
against the source in this session, not quoted: `Game/AssetLibrary.cs:423`
`TextureGrade = (0.74, 0.76, 0.80)` is the ground's base colour and the
wetness multiplier (`Core/LightModel.cs:600`, floor 0.55) is its ONLY
darkening lever; `SetWetness` (AssetLibrary.cs:681) walks the named
`WetSurfaces` set and writes `TextureGrade * AlbedoScale(wetness)`. Facades
get a second grade pass (0.84x), kit props were painted to 0.05–0.08, the
road never was. Sunlit ground reads ground÷frame 0.98–1.38 where the five
GTA references read 0.41–0.97; the reader's additive-lift recomputation
shows five of seven districts recover into or above the `groundPatch` band
once the lift is removed, and the honest detail residual on the one
correctly-exposed frame is ~19%, not ~86%. Every prior TextureGrade
iteration was judged on wet-masked frames — the comment's own history says
so once you know the wet term was hiding 45% of the albedo.

## Call 1 — ORDER: ground first, decals blocked on evidence. CONFIRMED.

The two fixes push the same number (`groundPatch`) in opposite directions;
landed together, neither is readable, and the decal work would be sized
against numbers inflated three-to-tenfold. Darken, land, re-measure, then
size the decals.

**The decal item moves from startable to BLOCKED-PENDING-EVIDENCE, slotted
directly under the ground item in `## Now`.** It unblocks when a landed dry
tour shows `groundOverFrame` in band (0.41–0.97, recomputed per run) on at
least 5 of 7 districts, and it is SIZED from the `groundPatch` re-read on
those in-band frames only. Expectation from the reader's arithmetic:
fairview is the one certain detail case; ironside is unreadable until its
camera is off the crane; the residual is about a fifth of its advertised
size. If the re-read says otherwise, the re-read wins.

## Call 2 — HOW FAR, AND ON WHAT AUTHORITY: a ground-only grade at 0.55,
derived from the project's own correct frame, refined by the printed series.

- **`TextureGrade` does not move.** It is the shared base for every textured
  surface, and everything else in the sunlit frames measures correct —
  brick reads brick, the facades sit at 0.84x via their own pass. Moving
  the shared constant would darken proven-correct surfaces and force a
  compensating facade/prop adjustment: two moves to accomplish one, and it
  destroys the evidence that the rest of the frame is right.
- **The builder adds a `GroundGrade` multiplier applied only to the
  `WetSurfaces` family**, folded into the same assignments `SetWetness`
  already writes, so wetness remains a multiplier on top and there is
  exactly one new lever.
- **First value 0.55 — not taste.** The one correct daylight ground in the
  set (`review_day1_noon`, wet 1.00) ran at effective albedo
  `TextureGrade x 0.55`; the entire in-band rain era ran at 0.59x. The
  game has already measured that this albedo reads as a British street.
  0.55 reproduces it on dry frames.
- **The gate is the reader's §6 instrument**: `groundOverFrame` per shot on
  the shot line, band 0.41–0.97 recomputed per run from the references,
  read on sunlit AND wet frames. Rule 2 order of operations: ship the
  printer with the change, read the landed series, adjust the constant
  once from evidence if out of band — never by eye.
- **The wet stack is the known risk, with a named answer.** Wet frames will
  now run ~0.55 x 0.55 = 0.30x, darker than the calibrated wet look. If
  the gate shows wet frames leaving band, the lever is RAISING
  `AlbedoScale`'s floor (wet no longer needs to supply the darkness dry
  never had) — not touching `GroundGrade`. One lever per question.
- **Facades and props get no matching adjustment.** Their relationship to
  the road changes BY DESIGN: the road is the thing that is wrong relative
  to them, and they are the control group that proves the fix landed where
  it was aimed.
- **The `TextureGrade` comment gains an ITERATION 3 entry** recording that
  iterations 1–2 were judged on wet-masked frames — rule 1's second
  corollary; the "stills are the judge" sentence is now a number.

## Call 3 — PREMISE: the band's ceiling is physics, Meridian sits mid-band.

The reference band is not Los Santos taste. Ground darker than its own
frame is a material fact — tarmac is the darkest large surface in a
daylight scene in every reference, sunny or not — so the CEILING (0.97) is
a physical bound any believable street obeys and ours violates. Within the
band, Meridian should sit at the MIDDLE, not the top: an overcast, sooted,
damp British port has darker ground than sun-bleached LA concrete, and the
noir grade wants a dark road for lamps and wet reflections to pop off —
`LightModel`'s own written rationale for the wet look. So: matching the
band serves the premise; matching its top would not. Final judge of "reads
British" is the still against `review_day1_noon`'s ground (rule 4) — the
number gates it, the picture confirms it.

## Call 4 — QUEUE ORDER for the next stretch (17-min round trips, visual first)

1. **(CI, one batched dispatch)** `GroundGrade` 0.55 + `groundOverFrame`
   instrument + `tourBlockerShare` + ironside camera re-site (off the
   crane; its ground band currently measures nothing, so re-siting it in
   the darkening build confounds no reading — the fix's evidence is the
   six unmoved cameras) + the ITERATION 3 comment. The `ref-bench`
   selftest/ceiling fix already assigned lands with or before this so the
   verdict is read on a green instrument.
2. **Read the landing**: `groundOverFrame` series first; `groundPatch`
   re-read only on in-band frames; AND the queue item 1 `shadowRatio` fork
   is re-judged HERE, not on the current landing — a shadow ratio taken on
   a doubled albedo is not evidence about ambient fill. No lighting lever
   moves before this read.
3. **Decal item**, unblocked and sized per Call 1, or closed small if the
   re-read says the residual is fairview plus noise.
4. **Then the rest of the visual stage as queued**: sky reflection source
   (decided 24 Aug), ambient fill off the post-fix series.

For the record: `ref-bench.py --selftest` RED (3/78) — this build's own
camera re-site invalidated its rejecting fixture, and the low-content
annotation has a floor and no ceiling, so ironside (the emptiest frame in
the set) is never flagged. Builder already assigned; noted here as an
instrument our own change broke, per rule 3.

---

# Batch review — the ordered batch, reviewed (director, 25 Aug 2026)

> Review of the systems-builder batch this record ordered (report:
> `agent-reports/ground-grade-and-tour-blocker.md`; diff read line by line,
> and every load-bearing claim re-verified against the tree in this session:
> the four `BaseColour` call sites, `WetSurfaces` membership, the seven emit
> keys, `WorldBuilder.Tint`'s MPB write, both plinth sites). Verdict:
> **APPROVED WITH ONE AMENDMENT** — the two white plinths join the batch.
> One reviewed commit after the amendment lands and verify is green.

## A. The four-site wiring — APPROVED, and it is the decision, not creep.

The question: this record said "folded into the same assignments
`SetWetness` already writes"; the builder wired FOUR sites through one new
`BaseColour` function (`AssetLibrary.cs:321, :572, :826, :840`). Ruling:
the record's sentence described a mechanism and, taken literally, contained
a latent fault the builder was right to refuse — `SetWetness` early-returns
on unchanged wetness, so a wetness-loop-only grade leaves any material
built after the last weather move WHITE until the weather next changes: a
fault nothing photographs until it does. The grade belongs on the DRY base,
which is what `BaseColour` is. Verified: all four prior expressions were
character-identical (`textured ? TextureGrade : SurfaceSpec.For(logical)
.Tint`), i.e. one idea in four implementations — the exact shape rule 1's
third corollary exists for — and after the change `TextureGrade` is read in
exactly one code site (:537). Non-ground surfaces pass through `BaseColour`
unchanged, so no behaviour outside the ground family moves. The Concrete
contamination of the facade control group (4% of the noon sample, and not
new behaviour — every rainy frame already drove `mat_concrete` to 0.55) is
named in the constant's comment with its designated fix (split the family,
not the number). **Do not re-litigate: four sites is the decision.**

## B. The predicted out-of-band wet case — APPROVED AS SHIPPED. The wet
reading is part of what this build exists to obtain.

Predicted: dry 0.78–0.98 (in band, top), wet 0.39–0.49 against a floor of
0.41. Ruling: `AlbedoScale`'s floor does NOT move in this dispatch, for
three reasons in descending weight. (1) The review days are wet by the
weather roll (day 1 wet 1.00, day 2 0.61 — the "review days are dry" claim
was corrected in the tour-move commit), so the landed verdict carries the
wet `groundOverFrame` series in the SAME round trip as the dry tour: the
measurement this decision needs arrives without a second dispatch. (2)
Moving both levers at once makes an in-band wet reading unattributable —
the exact confound reasoning that blocked the decals in Call 1. Batching is
for independent changes; two levers on one number is not batching, it is
blinding. (3) The predicted miss is a prediction with a stated
g-dependence, overlapping the band edge; adjusting a constant from it is
rule 2's definition of an invented bound.

**Pre-authorized now so the next session does not re-litigate:** if the
landed wet series is below band, the next batch raises `AlbedoScale`'s
floor ONCE, computed from the landed number, and `GroundGrade` does not
move. If wet lands IN band, nothing moves and the risk paragraph in the
constant's comment is marked resolved-by-measurement.

**One amendment to the read instruction:** the "reads British" still
comparison is against the ARCHIVED `review_day1_noon` from run 6137608.
This landing's own day1_noon runs at 0.30x and is the wet case UNDER TEST —
comparing the new frame to itself would grade the exam with the answer
sheet missing.

## C. `tourBlockerShare` — APPROVED. It is an instrument, not an unread number.

Checked against the instrument rules item by item, on the tree: it ships
its denominators (`tourBlockerHits=<hits>/<rays cast>`, 7x84;
`shotBlockerShareShots`), so seven 0.00s are distinguishable from a tally
that never ran (rule 3b); its statistic is named at the tally, at the
field, and at the emit — max over OBJECTS, last-wins per kept vantage like
its three sibling fractions, peak + median pair on the street shots with
the peak's object and distance captured in the SAME assignment (the
`deedWitnesses` fault, pre-empted); the bound is printed beside every
reading (`tourBlockerReach=8.0`) and `BlockerReachM` is declared NOT
MEASURED with the printer that will set it (each entry carries the winning
collider's distance); there is NO gate, deliberately, series first —
rule 2's order of operations, correctly refused rather than invented. The
accepting case is planted, not hoped for: the tour goes clear by design in
this same commit, so the street shots — measured at `shotNearFracWorst=
0.23` / `shotMidBefore=0.64` on 6137608 — are the world in which the
asserted thing can happen (rule 5b's corollary). The justification for a
new number over a bound on `midFrac` is evidence, not prose: three landed
statistics over distances watched a crane at 4m and the median ranked that
camera clearest. Residual risk accepted: `Dictionary<Collider,int>` and
`StreetMap.Node` resolving `ironside_j2_1` first compile on Windows — that
is what the round trip is for, and `tourResited=3/3` is the number that
says the ironside lookup did not silently fall back to the crane. The
builder's §7.4 (a bound, after two or three landings) goes to the queue.

## D. The white plinths — AMENDED INTO THIS BATCH. Two deletions, ordered.

Verified before ruling: `WorldBuilder.Tint` (:2551) writes MPB `_Color`,
which REPLACES the shared material's colour per renderer — its own
docstring says "multiply", which is true against the texture and false
against the material colour, and the `PostBox_drum` comment twenty lines
below (:2467) records this same mechanism misbehaving once already. So
`PhoneBox_plinth` (:2433) and `PostBox_plinth` (:2461) render raw texture
at `Color.white`: they receive neither `GroundGrade` nor wetness and never
have — against a 0.55 road they become the brightest ground-level surfaces
in every frame containing a phone box or pillar box, and there is a phone
box or pillar box in most street frames.

**The order to the builder:** unwrap the two `Tint(..., Color.white)`
calls so both plinths carry the shared `AssetLibrary.Concrete` material
bare. That is the whole change — the shared material already carries
`GroundGrade` and the wetness walk, and staying on the shared material
costs no draw call. Nothing else in `WorldBuilder.cs` moves in this batch.

Why in-batch and not queued: the round trip's deliverable is a still a
human reads against the archived reference (rule 4), and a known white
disc at the foot of every phone box is exactly the artefact that poisons
that read — we would be discounting a fault we chose to ship. It is the
same visual system, it cannot confound the measurement (plinths are far too
small to move a band mean; the facade control group is untouched), and the
batching rule makes it free. The yellow lines and zebra MPBs STAY: paint
reading lighter than wet tarmac is correct behaviour, not a fault. A note
(not an item) goes to the queue to revisit only if a landed still says the
paint reads wrong.

## E. The queue while the build is in flight — non-CI, three startable.

`## Now` order (Jafar's sequence; instruments-first within it because two
of these selftests are latent commit-blockers and item 2 depends on the
tool item 1 repairs):

1. **Repin two rejecting fixtures to synthetic cases** —
   `tools/clip-motion.py:439` asserts `Joe.fbx` has no animation take;
   `tools/prop-dimensions.py:337` asserts `police.fbx` reproduces a bug.
   Same fault class as the ref-bench selftest just fixed: a fixture pinned
   to a real asset goes RED when the project improves, and a red verify
   blocks every commit at the worst possible moment. Per the instruments
   rule: accepting case is the live repo, rejecting fixture is synthetic.
2. **`city-kit-roads` survey** (47 models, ONE named — the densest unused
   kit and all ground-level): `prop-dimensions` on every model AFTER item
   1, placement plan written. Game-layer wiring batches into the NEXT
   dispatch, after the ground landing is read.
3. **`city-kit-suburban`, entire kit unreached** — 13 models, zero named,
   per `prop-reach`'s per-kit numbers (the ~150 figure is the all-kits
   no-name-match total, not this kit; do not quote them interchangeably).
   Same measure-first treatment as item 2.
4. Standing work if 1–3 exhaust: read a system, or turn a still into a
   number.

BLOCKED-PENDING-EVIDENCE on this landing, listed so nobody starts them:
the decals item (unchanged); **the `LightModel.cs:137` aperture ceiling**
(its measured basis included the white road — re-judging it on pre-fix
frames re-measures the fault; builder's §7.2, agreed); the `shadowRatio`
fork (already bound to this landing); the `shotBlockerShare` bound (two or
three landed series first, builder's §7.4); the ironside-is-empty WORLD
item (builder's §7.3 — its evidence is this landing's ironside frame,
which for the first time can tell "empty" from "behind a crane").

## What the next session must NOT re-litigate

- Four-site `BaseColour` wiring is the decision; do not "simplify" it back
  to the wetness loop — that reintroduces the white-until-weather fault.
- `AlbedoScale`'s floor moves only off the LANDED wet series, once, and
  `GroundGrade` never moves in the same batch as the floor.
- The still reference is the ARCHIVED 6137608 `review_day1_noon`.
- The plinths stay on the bare shared material — do not "restore" a tint
  via MPB, and do not extend the fix to the yellow/zebra paint without a
  landed still saying the paint is wrong.
- `frame-drift` will read ironside's row as enormous drift next landing.
  That is the declared regime break, not a regression.
