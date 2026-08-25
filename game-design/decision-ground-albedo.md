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
