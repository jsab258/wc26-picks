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

---

# Post-audit ruling — the ref-bench measurement audit, A–E (director, 25 Aug 2026)

> Ruling on `agent-reports/refbench-measurement-audit.md` (13 findings),
> made AFTER the batch above was approved and BEFORE its landing is read.
> This is the SAME decision record continued, not a new one: A–D amend
> rulings made in this file, so they live where those rulings live.
> Verified in this session against the code, not quoted from the audit:
> the band geometry (`ref-bench.py:390`, consumed `:724`, divided `:758`)
> and the same-quantity comment at `:736–743` the audit disproves; the HUD
> mask (`:395`); `PATCH_FLOOR` (`:405`); the zero-series claim (my own
> grep: 0 hits for any ref-bench key across `sim-shots/verdict.txt` and
> every `runs/*.txt`); and both lint-conditional-reach sites — where I
> found one correction that changes a severity call (§E below).

## A. The ground-grade dispatch STANDS. Re-confirmed so nobody re-litigates
it off the audit.

Grounds, in descending weight, none of which the audit's corrections touch:

1. **`GroundGrade` 0.55 was never derived from the band's absolute value.**
   Call 2 derived it from the project's own history — the archived correct
   frame ran at effective `TextureGrade x 0.55`, the in-band rain era at
   0.59x. The audit's 2x2 moves the in-band COUNT; it cannot move that
   derivation.
2. **The direction survives every correction the auditor could construct**
   — 0/1/4/1 of 7 in band across the four variants, never a majority — and
   F1's own centre-third measurement convicts the ground MORE precisely:
   on 6 of 7 districts the road corridor is BRIGHTER than the band mean
   (+0.10..+0.27 luma), so a road-only numerator worsens our inversion.
3. **The source-code facts of the original finding are untouched**: base
   0.74–0.80, wetness the only darkening lever, facades and props graded
   while the road never was.

One risk carried forward with its name (F5): the 0.55 sizing was
cross-checked against "1.23–1.38", which is the worst four of seven;
gullwing, hook and strip sit near 1.0 unmasked and may land LOW after the
grade. That is what the landing read is for, and the pre-authorization in
§B of the batch review already covers it: one adjustment, from the landed
number, never before it.

## B. The decal unblock condition is REWRITTEN. "5 of 7 in band 0.41–0.97"
is RETIRED — it was mine, and it fails three ways at once.

F1: the two sides of the ratio are not the same quantity (reference band
horizontal spread 0.029–0.159, districts 0.248–0.493, no overlap — the
references' band is one surface, ours is road plus roofs plus facades that
`GroundGrade` does not touch, so the loop "adjust once if out of band"
would chase a number the facades are holding up). F3: 0.41–0.97 is the
reader's UNMASKED band while the instrument the gate names prints its
MASKED band 0.387..0.981, and the two disagree most at exactly the band
edge where the pass/fail lands. F5: the constant was written beside the
word "recomputed", the shape that decays.

The replacement, in rule 2's order of operations:

1. **Ordered now, one dispatch of instrument work: the ground-material
   render mask for the seven district shots.** The sim knows which pixels
   are `WetSurfaces`; one extra render per district shot, family flat
   white, everything else black, is a free road mask. ref-bench consumes
   it and prints the masked road mean and its ratio per district; in the
   same change, `groundOverLower` prints beside `groundOverFrame` (F2's
   four-line printer) and the band's left/centre/right means print per
   image (F10 — the number announces its own contamination). The
   references need no mask: their band is one surface to 0.03–0.16, which
   is what F1 measured. This settles F1, F4 and F10 and collapses F2's
   bracket to one number — the auditor's own cheapest-decisive call,
   adopted.
2. **No numeric band is written today.** The printer lands, the masked
   series is read, and the band is set from evidence then — quoted from
   the instrument's printed line each run, never as a constant in a doc.
3. **Decals unblock on a director close-out of the masked read**: masked
   road ratios in family with the references on the post-grade landing,
   and the decal work sized from the masked numbers. Until the mask
   exists, no in-band COUNT on unmasked district frames gates anything —
   the audit's sentence, adopted verbatim.

## C. F9: local-only ref-bench readings may EXPLORE and may not GATE.

Confirmed by my own grep, not the auditor's: no ref-bench key has ever
reached a verdict — 0 hits across `verdict.txt` and all `runs/*.txt`. The
entire GTA comparison to date is hand-run, which is exactly how F3
happened: two people ran the same tool locally and produced two different
instruments. Standing rule from here: **no bound is set on any ref-bench
dimension until that dimension has a landed series in the verdict.** The
first fix is already in flight — Call 4 item 1 ordered the
`groundOverFrame` per-shot emit into the dispatched batch. First-landing
order: cross-check the sim-emitted value against ref-bench run on the same
committed frames BEFORE quoting either; encoding noise is measured at
0.001, so any larger disagreement is an instrument question and is settled
first (rule 3). Thereafter one instrument per job: ref-bench owns the
reference comparison (only it can see the references), the verdict owns
series and constancy.

## D. READ BEFORE OPENING THE LANDING — two numbers that will mislead.

- **`groundPatch` WILL NOT MOVE, and that is the instrument working, not
  the fix failing.** Verified multiplicative-invariant to k=0.25 on every
  district; clipped ground pixels 0.000–0.001, so there is no detail to
  un-clip. Written prediction (F6, adopted): the seven district values
  land unchanged to three decimals — 0.029 / 0.105 / 0.132 / 0.172 /
  0.256 / 0.273 / 0.152. If any of them MOVES, the grade was not purely
  multiplicative and THAT is the finding. An unchanged `groundPatch` on
  in-band frames remains the honest decal-residual number: it measures
  detail, which the grade does not touch.
- **Night and wet `groundPatch` will FALL for arithmetic reasons** (F12):
  below a window mean of 8/255 the divisor becomes `PATCH_FLOOR` and the
  ratio goes linear in exposure. Do not read that as "the darkening
  destroyed detail at night". The floored-window count printer (beside
  `patchWindows=330`, zero today on every district) goes to the queue as a
  ref-bench item with F2/F10's printers.

## E. lint-conditional-reach: REAL, QUEUED as the repin item's third site —
NOT the per-commit emergency reported, and here is the verified correction.

The builder's §2 (fixture-unpinning.md:449) says the tool "writes to a
tracked Game-layer source file on disk, during `verify.py`, on every
commit". **Checked against the code: false in the part that sets the
severity.** `verify.py:554` runs the tool WITHOUT `--selftest` — plain
`audit()`, which only reads — and a repo-wide grep finds NOTHING that
invokes the selftest. The rewrite of `Audio.cs`
(`lint-conditional-reach.py:121`) is reached only by a hand-run
`--selftest`. So there is no per-commit corruption window. Rule 3, applied
to the finding: the hazard exists, the exposure claim was wrong.

Both faults stand where they actually live: a kill mid-selftest leaves
`Audio.cs` holding `NothingAtAll`, and one legitimate `OnnxSpeech` caller
outside `Audio.cs` — ordinary live-speech work — turns the hand-run
selftest red for the project doing MORE. Ruling: **not stop-everything.
It joins the already-queued fixture-repin item (batch review §E item 1) as
its third site** — same fault class, same fix, exactly as the builder
specified at fixture-unpinning.md:460: the rejecting case becomes a
SYNTHETIC conditional type in a tmpdir copy, touching no tracked file.
That item is already top of the non-CI queue; this does not jump the
landing read. Interim standing orders: nobody runs
`lint-conditional-reach.py --selftest` by hand until the repin lands, and
`NothingAtAll` appearing in `Audio.cs` is this signature — restore the
file from git, do not diagnose a compile error.

## Additions to "what the next session must NOT re-litigate"

- **The ground-grade dispatch stands.** The audit changed the GATE, not
  the decision. Do not withdraw or resize `GroundGrade` off the audit;
  the one authorized adjustment comes from the landed masked read.
- **The "5 of 7 in band 0.41–0.97" unblock is retired.** Its replacement
  is §B above: mask instrument → landed series → band from evidence →
  director close-out. Do not resurrect the written constant, in either its
  masked or unmasked form.
- **`groundPatch` unchanged at the landing is the instrument working.**
  The prediction is written in §D; read it before the verdict.
- **Local ref-bench runs are exploration, not gate evidence.** A bound
  needs a landed verdict series first, and the reference comparison quotes
  ref-bench's own printed band, not a doc.
- **The lint-conditional-reach rewrite does NOT run on commit** — verified
  at `verify.py:554`. Do not stop the line for it, and do not run its
  selftest by hand until the repin lands.

---

# Final confirmation — plinth execution and batch state (director, 25 Aug 2026)

> Confirmation row before commit, per the escalation rule (HEAD moved after
> the amendment; the ordered change had not been seen executed). Not a new
> analysis; both rulings above hold.

- **Plinth execution CONFIRMED against the §D order.** Diff read
  (`WorldBuilder.cs` only, 47+/9-): the only executable-code changes are
  the two ordered `Tint(..., Color.white)` unwraps; every other changed
  line is a comment. The comment-only additions are ACCEPTED — "nothing
  else moves" in §D governed behaviour, and comment repairs beside a fix
  are rule 1's second corollary being obeyed, not scope creep. The three
  resident-authorized repairs (class docstring's "purchased pack" vs
  section 0; `Tint`'s "multiply" claim; `PhoneBox`'s docstring) are
  RATIFIED.
- **The `PhoneBox` docstring repair verified against source, this
  session**: `MakeBoxCol` (:3998) assigns `sharedMaterial =
  AssetLibrary.Opaque(c)` — a real shared material, no property block —
  and body/cap/dome route through it; only `PhoneBox_bar_*` (:2464) still
  uses `Tint`. The builder's two self-corrections (dropping the "and a
  build" cost claim; the drum's not-reaching-the-renderer failure mode
  kept distinct from the replace-not-multiply one) both make the record
  MORE accurate and stand.
- **§D reading instruction re-confirmed for the landing read**: the seven
  `groundPatch` values are predicted unchanged to three decimals (written
  in §D above — read them there, they are not restated here); the numbers
  that SHOULD move are the district ground means (down by roughly the
  grade factor) and `groundOverFrame` (toward band). `groundPatch`
  unchanged is the instrument working.
- **APPROVE-TO-COMMIT** for the batch as presented: `AssetLibrary.cs`,
  `SimDirector.cs`, `WorldBuilder.cs`, plus the two staged tool files,
  one reviewed commit, verify green with this row supplying the cadence.

# Mask instrument batch — director review (25 Aug 2026)

> Executes §B item 1 of the 25 Aug audit ruling (the retired "5 of 7 in
> band 0.41–0.97" gate, replaced by mask instrument → landed series → band
> from evidence). Diff read in full (390 lines); decoration claims verified
> against `AssetLibrary.cs` live code this session (`"mat_" + logical`
> :547, `logical + "_b"` :270, `baseMat.name + "#g" + g` :315).
> APPROVE-TO-COMMIT — after the restore above.

- **A. The ray-grid sampler is ACCEPTED as the execution of "§B render
  mask" — and the record here is the correction of §B's mechanism, not an
  erosion of it.** §B suggested a flat-white second render; the builder's
  substitution reads the COMMITTED frame's own pixels, which is the better
  instrument by this project's own rules — a second render is a different
  photograph from the one a person opens. For the next session, in terms
  that cannot be misread: **every `groundMask*` value is a MEAN over at
  most 2,304 ray samples (64x36 grid), classified by the COLLIDER under
  the sample, not a per-pixel measurement.** Its two known blind spots:
  collider-less geometry is invisible (whatever stands behind it is
  credited the pixel, luma included), and multi-material meshes classify
  as submesh 0. Do not compare these values against a per-pixel mask
  without saying so, and do not "fix" a small disagreement with ref-bench
  band numbers — they are different quantities by design (§B/F1).
  One knowing deviation ratified: `groundMaskThirdsBy` is thirds of the
  GROUND SAMPLES, not F10's thirds of the fixed band. Since the band
  instrument is retired, the masked thirds are the replacement quantity;
  the unmasked band thirds die with the band.
- **B. The Core file and CoreTests change are RATIFIED as anti-duplication,
  verified not claimed**: `SurfaceNames.cs` holds NO surface list — it
  takes the logicals as an argument, and the only list remains
  `AssetLibrary.WetSurfaces` (add a surface there and the mask follows
  with no other edit). The CoreTests array is a FIXTURE pinning the string
  rule against today's four names, which Core could not read from the Game
  layer anyway. The placement reason is the load-bearing one and it is
  correct: a matcher inside the Game layer ships unrun here, and an unrun
  classifier that matches nothing is exactly the silent-zero fault. The
  scope excess over the brief is approved for this reason.
- **C. The eight keys CONFIRMED against the diff**: all eight on the done
  line; denominators lead (`groundMaskShots=m/o`, `groundMaskRays`
  cast/hit/renderer/ground, `groundMaskSurfaces`); `nothing_measured` is
  underscored; `name:none@0/2304` distinguishes ran-and-found-nothing from
  never-ran; `groundMaskAcross` names itself a statistic of the tour
  (min..max/med/n over seven shots). One legible asymmetry noted, not
  blocking: a shot with zero ground rows only in `MeanBy` (as `none@`),
  so the other three lists carry fewer name-keyed rows — discoverable via
  the `none@` row, and a `GetPixels` failure shows as measured<offered
  plus an `_errors` entry.
- **D. NO BOUND, NO GATE — confirmed against the diff, not the report.**
  No gate-list change, no comparison against any constant, no threshold
  anywhere in the 390 lines; the done-line additions are pure printers and
  the comment says so. §B item 2 stands executed as written.

**READING INSTRUCTION FOR THE LANDING — write nothing about ground until
this paragraph is applied.** Read `groundMaskRays` first, as a chain:

- **`cast/hit/renderer/ground` with ground ≈ 0 and seven `none@0/2304`
  rows**: the instrument found no ground, visibly. Do NOT set any band, do
  NOT add colliders speculatively, do NOT loosen the name rule. The chain
  says where it died: hit≈0 → colliders absent (roads are `CreatePrimitive`
  slabs, so this would be surprising — verify before believing, rule 3);
  renderer≪hit → the collider→renderer lookup; ground≈0 with renderer
  healthy → live material names vs the string rule. Next dispatch adds ONE
  diagnostic printer — the most-hit unmatched material names — and nothing
  else changes until it lands.
- **ground healthy and rows plausible**: the series starts. Per §B item 2
  and §C, no band is set off ONE landing — read at least a short series,
  cross-check frame-level quantities against ref-bench on the same stills
  where both exist (0.001 encoding-noise bound applies), then set the band
  from the printed series in a dated section here.

Quality-ladder note at this close: the next rung for this instrument has a
name — the per-pixel replacement-shader mask, rejected today for headless
cost. It goes on the ladder, taken only if the sampler's blind spots are
ever shown (by a still or the cross-check) to bias a real reading.

---

# Landing 14f964a read — ruling on A–F (director, 25 Aug 2026)

> Ruling on the 14f964a landing: verdict GREEN, `districtGround`
> col:0.41,0.42,0.44 as predicted, `tourResited=3/3` — and the
> artifact-reader's frame measurements
> (`agent-reports/landing-14f964a-stills.md`, F0–F12) showing every dry
> frame's ground at 0.66–0.94 luma while wet frames read correct. Verified
> in this session, not quoted from either report: `districtGround` is ONE
> RAY, fired in downtown only (`SimDirector.cs:10450`,
> `SurfaceUnder(cam, 0.5, 0.12)`); `frames.tsv` carries `rain` and `wet`
> as the last two columns of EVERY row including the seven district rows;
> `hunt_day*` appears in no agent report except the reader's own
> exclusion of it.

## A. PARTIAL — and the fork MOVES TO THE LIGHTING STACK. `GroundGrade`
does not move again in either direction.

The grade landed at source and the rendered dry street did not follow.
Three pieces of evidence, none of them prose:

1. **Source vs rendered on the same material family**: the printed graded
   albedo is 0.41–0.44; the reader's dry road patches measure 0.77–0.94.
   That is a 1.8–2.2x gain the material cannot supply — a colour cannot
   render brighter than the light path makes it.
2. **The near/far gradient inside ONE frame**: hook road near 0.771, hook
   road far 0.944 (244,240,237), same material, same weather, same
   exposure. Albedo is constant along a road; only a distance-dependent
   additive term (fog/atmosphere blending toward a near-white colour) can
   produce that gradient. This is the internal control that convicts the
   light path rather than the surface.
3. **The clean rain=0/wet=0 split**: the wet path multiplies these same
   materials down to 0.218/0.057 and the frame reads as the best British
   street this project has produced (reader §7). The materials are proven
   CAPABLE of reading right; what differs between the good frames and the
   snow frames is the dry-sun illumination path, not the surface.

**A further albedo step is REFUSED.** Compensating a ~2x lighting lift
with albedo puts the ground near 0.22 — and it would re-break the wet
frames that 0.55 was derived FROM (Call 2: the archived correct frame ran
at exactly this multiplier). That is moving the proven lever to hide an
unmeasured one, the shape rule 2 forbids.

**One honest caveat, recorded so the conclusion is falsifiable**: the
prediction "the material moved as ordered" is proven by ONE ray at ONE
point in ONE district — `districtGround` fires only in downtown
(`SimDirector.cs:10450`). The family-wide claim currently rests on the
code reading (the four-site `BaseColour` wiring), not on a printed number.
The reader's numbers are CONSISTENT with all four members graded plus one
uniform ~1.9x dry lift (0.42 x 1.9 ≈ 0.80, which is what pavement
measures) — but consistent-with is not proven, which is what §B below
buys.

**What falsifies this ruling**, in writing: (a) `groundAlbedoBy` (ordered
below) shows any `WetSurfaces` member off-grade at source → the albedo
work is unfinished for THAT member and the lighting conclusion is
premature for it; (b) the masked dry per-name rendered means land ≈ the
source albedo → the reader's 14px patches were contaminated and the
INSTRUMENT is the next question (rule 3) — no lighting lever moves on
that outcome either.

**Consequence for the blocked list**: the `LightModel.cs:137` aperture
ceiling item's stated blocker — "re-judging it on pre-fix frames
re-measures the fault" — is DISCHARGED: post-fix frames now exist. It
unblocks for MEASUREMENT. The lever itself moves ONCE, after the masked
series lands, sized from the landed dry/wet ratio — never by eye, never
in the same batch as any albedo change. The `shadowRatio` fork (Call 4
item 2 bound it to this landing) is re-judged AFTER the mask lands, on
the same series, because a shadow ratio taken under an unmeasured 2x lift
is not evidence about ambient fill either.

## B. The mask batch ALREADY carries most of the answer. ONE addition
before dispatch; nothing else joins.

The decisive read is: **per-name ground-classified rendered mean
(`groundMaskMeanBy`, already in the approved batch) DIVIDED BY per-name
SOURCE albedo, per shot, split dry vs wet.** Ratio ≈1 on dry shots →
hypothesis (b) above, instrument question. Ratio ≈2 and uniform across
members → one downstream lift; size the lighting move from it. Ratio
uneven across members → the un-moved member is named by its own row.

- **ADD before dispatch: `groundAlbedoBy`** — the source albedo of each
  `WetSurfaces` member as the sim holds it at shot time, per name, on the
  done line, `/`-separated, no spaces. One printer, cannot confound, and
  without it the division above compares a measurement against an
  assumption. This supersedes the single-ray `districtGround` as the
  family-wide source check.
- **Do NOT add the rain/wet pairing** — verified this session: `rain` and
  `wet` are the last two columns of every `frames.tsv` row including the
  district rows. The pairing is a JOIN at read time, not a printer.
- **The >0.80 blown fraction and `groundLumaNoon`**: NOT into this batch.
  `groundMaskMeanBy` per name per shot carries the level; a mean at 0.8+
  answers the fork. The blown-fraction and the reader's other printers
  (F2 `brightestObj`, F3 `nightBrightestSurface`, F5 `skylineFootGap`,
  F7 `camClear`, F10 `districtBodies`, F12 `decalYawErr`, F9
  `clipsUntextured`) form the NEXT instrument batch, queued by name —
  the approved batch is waiting on a gate fix and every addition beyond
  one line delays the round trip that settles A.
- The §B-item-1 reading instruction above (the `groundMaskRays` chain)
  stands unchanged and is read FIRST.

## C. The decal unblock condition is UNCHANGED. The frames change the
expectation, not the mechanism.

Masked series → band from evidence → director close-out, exactly as
written in the audit ruling §B. What the frames add: the masked dry read
will almost certainly land far out of family, so **expect decals to stay
blocked through the lighting fix** — the sizing read happens on frames
whose ground is in family, dry AND wet, which is at least two landings
away. Do not unblock on the mask landing alone. F12 attaches to the decal
item as a named sub-fault: 1081 decals are placed and the visible ones sit
~45° off the road axis — `decalYawErr` (median angle vs road segment,
count beside it) ships in the second instrument batch and the decal work,
when it unblocks, fixes orientation before adding anything.

## D. Skyline: D2 is a PREMISE VIOLATION, ruled now in writing; D1 and D2
are ONE work item, ranked directly behind the ground-lighting lever.

1. **The towers float** (25px of sky between base and horizon at
   copper x=670, visible in strip and hook): real, high-confidence, a
   world-geometry fault. Evidence printer: `skylineFootGap` with the
   count of towers examined, so a zero is legible.
2. **Twelve-plus black glass skyscrapers on the horizon**: nothing in
   section 0, `visual-bar-spec.md`'s Meridian decomposition, or any brief
   claims to draw them, and a forest of forty-storey curtain-wall towers
   contradicts the stated premise directly — a British port town in the
   late-analog eighties/nineties skylines with dock cranes, gasometers,
   chimney stacks, church spires, warehouse rooflines, and at most a
   handful of sixties/seventies council slabs. **The proposal (this
   skyline) is wrong; the premise stands.** This is execution of the
   written premise and of the 21 Aug visual order ("on Meridian's
   content"), so it does not need Jafar's sign-off — but it IS a change he
   will see, so the next update he asks for names it in one plain line.
3. **One item, not two**: the same placement code that draws the towers
   is where they float, so the builder brief is "replace the skyline
   proxy set with period-correct silhouettes AND seat their bases on the
   ground plane, shipping `skylineFootGap` in the same change as its own
   evidence". Ranked: after the ground-lighting lever (the snow street
   outranks everything), ahead of decals and all other F-items — it is
   the first thing the eye finds in five of seven district shots and it
   reads as the wrong city.

## E. The frames.tsv provenance fault: fixed in the NEXT COMMIT TRAIN, and
no landed conclusion is poisoned — checked, not assumed.

The fault is exactly the staging rule's blind spot from the other side:
`sim-shots-stage.sh` stages by name, `hunt_*` is not in the name list, and
the sim writes `frames.tsv` rows for shots whose JPEGs never stage — so
the ledger describes pictures that are not on disk (row 0.079 vs file
0.114). The fix, ordered as tool work (non-CI, rides the next commit):
**add `hunt_*` to the by-name stage list, conditional on the sim having
written the file THIS run, and emit `framesStaged=N/M` naming any row
whose picture did not stage** — the reader's own proposal, adopted; it is
rule 3b's denominator applied to the ledger itself.

Invalidation check, done this session: `hunt_day` appears in no agent
report except the reader's own exclusion of it, so no picture-derived
conclusion ever read those frames. The ledger ROWS are honest sim
measurements of what was rendered (frame-drift compares rows, not JPEGs),
so no number-derived conclusion is poisoned either. **Nothing landed needs
retraction.** Severity stays high on principle — this is the evidence
channel lying about what it holds — which is why it rides the next train
rather than the queue.

## F. The space-in-value keys: NOW, folded into the mask dispatch.

`bodyAlbedo`, `rounds`, `worstWorldPair`, `gapWhy`, `massInRoad`,
`speechVoicesWhy` — every listed key, reformatted to `/`-and-`..`
notation per the instruments rule, in the same `SimDirector` emit code the
mask batch already touches. Format-only, cannot confound any reading, and
`verdict-read.py` currently truncates `bodyAlbedo` to `[0.01` with no
sign of loss — the documented silent-truncation fault live in six places.
Not a separate round trip; not the queue.

## The next dispatch, in one list

1. The approved mask instrument batch (after its gate fix), plus ONE
   addition: `groundAlbedoBy` (§B above).
2. The six space-in-value key reformats (§F).
3. The `frames.tsv` staging fix + `framesStaged=N/M` (§E — tool/workflow
   side of the same train).
4. **Nothing that moves a lever.** No exposure change, no `GroundGrade`
   change, no `AlbedoScale` change, no skyline geometry, no decals.

In parallel, non-CI: brief the skyline item (§D) so it is ready to
dispatch the moment the masked read lands; queue the second instrument
batch (§B's printer list) by name.

## Additions to "what the next session must NOT re-litigate"

- **`GroundGrade` does not move again off dry frames, in either
  direction.** The snow readings are a lighting-path finding; the one
  authorized albedo-side adjustment remains §B's `AlbedoScale`-floor
  clause, off the landed masked WET series only.
- **No lighting lever moves before the masked series lands.** The
  aperture-ceiling item is unblocked for measurement only; its move is
  sized from the landed dry/wet ratio, once.
- **`districtGround` col matching the prediction proves one ray in
  downtown, not the family.** `groundAlbedoBy` is the family-wide source
  check; do not quote the single ray as it.
- **The skyline towers are ruled off-premise** (this section, §D). Do not
  re-open "maybe they are intended"; the premise is written and they
  contradict it.
- **F8 (face shards) is untouched** — the reader marked it low-confidence
  and said do not touch a rig on it; that stands until `skinBurst` or a
  noon re-shoot says otherwise.

---

# Verdict-integrity batch review — ruling on A–E (director, 25 Aug 2026)

> Review of the builder batch executing items 2, 3 and the `groundAlbedoBy`
> half of item 1 from the 14f964a dispatch list above. Every load-bearing
> claim verified against the tree this session, not the report:
> `GroundAlbedoEmit` (`AssetLibrary.cs:923`, call site `SimDirector.cs:
> 15735`), `lint_text`/`spaced_values` and both selftest halves
> (`verdict-read.py:107–194, 322–354`), the ungated `--spaced` wiring
> (`verify.py:1413–1430`), `frames_staged_line` and its three-case selftest
> (`sim-shots-stage.sh`), `KitAlbedoCap`/`KitAlbedoListed`
> (`SimDirector.cs:9600–9652`), `prop-reach.py:128,136` still parsing the
> `+Nmore` tail, and the six space-fix sites (`SimDirector.cs:4433, 13937,
> 14440, 14458, 14533` plus `AlbedoRead`). RULING: **APPROVE-TO-COMMIT
> after three one-line comment corrections**, listed under D and B below —
> within the resident's hand-apply authority; no code changes required.

- **A. AWAITING THE LANDING, not CONFIRMED — recorded so nobody quotes it
  settled.** The emitter is right (one loop, `TryGetValue` never
  `Material()`, `not-built` in words, denominator from the same pass) and
  it IS called on the done line. But the four values
  0.412/0.437/0.428/0.401 are ILLUSTRATIVE: grep of `verdict.txt` and
  every `runs/*.txt` finds no `groundAlbedoBy` anywhere — the only
  occurrences in the tree are the builder's report and the `SPACED_GOOD`
  selftest fixture. The Game layer does not run in this container, so no
  process has ever read those materials. "All four members on grade" and
  "the §A falsifier did not fire" are the OUTPUT of the dispatch this
  batch unblocks, not facts about the tree today. §A's PARTIAL ruling
  above stands exactly as written, caveat included, until the landing is
  read. Standing instruction from the near-miss: a report showing an emit
  that has never landed writes the word "illustrative" beside it — this
  report did so for `framesStaged` ("first real reading, with its caveat
  stated") and not for FAULT 4, and the difference nearly became a
  confirmed conclusion.
- **B. CONFIRMED — the split and the non-gate are both right.** The
  diagnosis is verified in code: `lint_text` flattens `[...]` to a space
  before matching, so it is an unbalanced-delimiter lint and `key=[a b c]`
  was deleted unexamined; `SELFTEST_GOOD` enshrined that shape as required
  acceptance. `spaced_values` closes the hole with the correct
  distinction (`name[...]` group vs `name=[...]` flat-namespace value),
  ships its denominator, announces its cap, and both selftest halves run.
  Six emitters fixed and verified at their sites; leaving `verdictSpaced=
  39/110` UNGATED is right — gating today reds every commit until CI
  lands, the ratchet rule — and the gate trigger is already written where
  it belongs (`verify.py`: becomes a gate when a landed verdict reads 0).
  ONE correction: the `spaced_values` docstring says "five live keys" and
  lists six — fix the word. AND the 33 remaining spaced keys get a NAMED
  queue item ("spaced-value backlog, 33 keys, list via `--spaced`");
  `queue.md` currently has no row for them and adjacent work without a
  name evaporates.
- **C. CONFIRMED — placement and the zero are both legible.** The
  `SimShotsStage:` line is appended by the stage script to the verdict
  and per-run copy, never the sim's done line, which is correct because
  staging does not exist until the sim exits. The 0/29 case cannot
  masquerade: in CI a run with no sim passes frames-flag 0 and prints
  WORDS (`no-ledger-this-run`), so `framesStaged=0/29` in a landed
  verdict genuinely means "ledger written, nothing photographed" — a
  finding there, correctly. The local 0/29 was a hand-run with flag 1
  against the stale tsv and is captioned as such in the report. Checked:
  the tracked `verdict.txt` carries NO SimShotsStage line, so the
  hand-run did not pollute the channel — but note the hazard: running
  the script (not `--selftest`) in this checkout appends to the tracked
  verdict. Do not hand-run it outside the selftest.
- **D. CONFIRMED AS DESIGN; discharge completes at the landing — plus two
  comment corrections required before commit.** Cap 96 over 38 families,
  `kitAlbedoListed=shown/total` beside it, `+Nmore` tail shape unchanged
  and `prop-reach.py` parses it — structurally the survey blocker is
  discharged, and `38/38` is the expected shape, not a landed number: the
  first landing confirms it. The corrections: `SimDirector.cs:9582–83`
  still says "Capped at ten" and `:9624–31` still argues "24, NOT 10 …
  24 covers every family" — two stale comment layers asserting constants
  the code no longer holds, in the one batch whose subject is claims
  decaying. Reconcile both to point at `KitAlbedoCap` (rule 1, second
  corollary).
- **E. JUDGEMENT: the choke point is right; its residence is not, and the
  move is a named queue item, not a blocker.** One function every
  free-text value passes through is the correct boundary — approve that.
  But `NoSpaces` lives in the Game layer, which never compiles here, so
  the guard itself ships unrun — and this project's own precedent, written
  three files away for exactly this reason (`SurfaceNames` moved to Core;
  `AssetLibrary.cs:961–964`), says string rules live in Core where
  CoreTests exercise them. Sited in `SimDirector` it is also unreachable
  from `AssetLibrary`'s emitters: `GroundAlbedoEmit` already hand-builds
  its space-free strings, which is the one-idea-two-implementations seed
  in the same batch that fixed three instances of it. Queue item, by
  name: "move `NoSpaces` to Core with accepting+rejecting CoreTest,
  redirect the five call sites" — cheap at five sites, expensive at
  forty, so it goes near the top of non-CI work.

**Net: APPROVE-TO-COMMIT** once the three one-line comment fixes are
applied (D's two stale layers, B's five→six) and the two queue items are
written (spaced-value backlog; NoSpaces-to-Core). Then dispatch the train
as listed above — it is what turns §A's AWAITING into a reading.

---

# Measurement audit of the 14f964a ruling — §A re-ruled leg by leg (director, 25 Aug 2026)

> Ruling on the measurement audit of "Landing 14f964a read — ruling on
> A–F" above. Every load-bearing claim re-verified against the tree this
> session, not quoted from the audit: `SurfaceUnder`'s col is
> `sm.GetColor("_Color")` — the tint alone, in its stored (gamma) value,
> texture excluded — at `SimDirector.cs:8726–8727`, printed `:8750`, with
> `tex:` beside it naming the texture it ignores; `MatAlbedo` is
> `m.color.linear` luma × `MeanTexLuma` (`AssetLibrary.cs:1311–1316`);
> the project is `ColorSpace.Linear` (`CiBuild.cs:42`); the mask pools
> ONE sum per shot with no per-material split (`SimDirector.cs:
> 10706–10727`, `gSum += l` behind a single `IsGroundSurface` test); the
> `AssetLibrary.cs:915–917` comment orders a division across keys that
> share no name; ref-bench masks HUD rects on BOTH sides
> (`ref-bench.py:394–396`). The probe series I pulled from `runs/`
> myself: `noonFacadeMat` d: wanders 6.7–9.2 across landed runs, and run
> 3ecefd4 hit `mat_concrete_b` where every neighbouring run hit
> `mat_brick_grey_b` — WORSE than the audit stated: the single ray does
> not just move, it sometimes lands on a different surface. Adopted from
> the audit without re-running here, and marked so: the `gates.py
> --series` refusal of `meanLuma` (three values on three lines, 319/323
> runs) and `shadowDrop`'s bimodal 88-run series.

## A. §A is NARROWED and its verdict RE-AFFIRMED — it stands on leg 2
alone, and the record says so in these words.

- **Leg 1 is STRUCK.** "Source 0.41–0.44 vs rendered 0.77–0.94 is a
  1.8–2.2x gain no material can supply" compared ONE FACTOR of the
  source — the gamma-stored tint, texture excluded — against the FULL
  rendered result. The two instruments agree exactly once converted:
  0.41,0.42,0.44 IS `TextureGrade x GroundGrade` in stored values, so
  the landing proved the tint was ASSIGNED and proved nothing about
  gain. Everything downstream of the 2x dies with it: the "~2x lift"
  phrase, the "0.42 x 1.9 ≈ 0.80" consistency arithmetic, and any
  sizing of a lighting move from that factor. **The magnitude of the
  dry lift is today UNMEASURED.**
- **Leg 2 STANDS and is sufficient.** Hook road 0.771 near / 0.944 far —
  same material, same frame, same instant, same space. Albedo cannot
  vary with distance; only the light path can produce that gradient.
  Every operative order survives on this leg unchanged: `GroundGrade`
  does not move in either direction, the lever is the lighting stack,
  no lighting lever moves before the masked series lands, and §A's
  falsifiers (a) and (b) stand as written.
- Why this is recorded rather than quietly absorbed: a conclusion that
  keeps its verdict while losing half its reasoning is exactly how a
  wrong premise survives. The next session must know WHICH evidence the
  standing orders rest on, or a future challenge to the dead leg will
  read as a challenge to the ruling itself.

## B. `groundGainBy` — ORDERED into the mask dispatch. The `:915–917`
comment is FALSE-ON-ARRIVAL and is rewritten in the same change.

The division that comment orders cannot be performed: `groundMaskMeanBy`
is keyed by DISTRICT, `groundAlbedoBy` by MATERIAL, and the pooling loop
adds every ground ray into one sum per shot. It shipped in a batch I
approved — noted for the record: a comment describing a FUTURE read
decays exactly like one describing past behaviour, and this one was
false the day it was written. The auditor's fix is adopted:

1. Inside `GroundMaskRead`, where the ray already holds
   `rend.sharedMaterial`, bucket per material name and emit
   `groundGainBy=[asphalt:<renderedLinear>/<sourceAlbedo>=<ratio>/...]`
   — numerator and denominator from the SAME ray at the SAME instant,
   both linear. One dictionary, no extra render, space-free values, a
   rays-per-bucket denominator per the instruments rule.
2. **The source side goes through `MatAlbedo` itself** — the same helper
   `groundAlbedoBy` uses — per this project's own written rule at
   `AssetLibrary.cs:1318–1321`: one instrument on both sides, or the
   comparison is two instruments arguing.
3. **The emit's comment names the colour space of BOTH sides**, because
   this entire section exists because a space went unnamed. Known
   confusable, written in advance: first landed ratios clustering near
   2.05 (≈ 0.55 / 0.267) are the signature of a gamma/linear mismatch
   INSIDE the instrument — suspect that before concluding anything about
   light (rule 3).
4. No gate, no bound, series first. The landed ratio is what SIZES the
   lighting move; nothing moves in this dispatch.

## C. The GTA magnitude claim is WITHDRAWN; the direction is retained;
the mattes are APPROVED; the in-engine HUD mask is REFUSED.

- Kept, 7 of 7: our dry ground is brighter relative to its frame than
  every reference. WITHDRAWN wherever quoted: any FACTOR between us and
  the references. Three biases point two ways (reference-band non-ground
  content — cars, riders, fences; our dark sky; the HUD-mask asymmetry),
  and the auditor's +2%..+25% band for the first is self-declared
  hunch-bounded, off an eye-drawn mask. A withdrawn magnitude with a
  retained direction is the honest reading and it changes no decision:
  nothing standing was sized from the factor.
- **Five hand-painted ground mattes, committed once beside the
  references — APPROVED.** Cheap, permanent, and it converts the
  reference side from "band with unknown contamination" to a measured
  surface. Content-wrangler task, queued by name; not blocking the
  dispatch.
- **The proposed HUD mask on our in-engine side is REFUSED.** The audit
  ruling §C already assigned the reference comparison to ref-bench
  EXCLUSIVELY, where the mask is symmetric by construction; the
  in-engine `groundMaskOverFrameBy` is a series-and-constancy
  instrument and is never quoted against a reference number. A second
  HUD-mask implementation in-engine is one idea in two implementations
  — the seed rule 1's third corollary exists to kill. The standing rule
  gains one sentence: **no in-engine key is compared against a
  reference; cross-comparison happens inside ref-bench or not at all.**

## D. STANDING INSTRUCTION — single-ray probes are identity checks, not
measurements.

Verified worse than reported (header): the facade probe's distance
wanders 6.7–9.2 across landed runs and at least once landed on a
different material family entirely. The instruction:

1. **A single ray may confirm a PREDICTED CONSTANT that is invariant to
   where in the family it lands** — `districtGround` col matching
   `TextureGrade x GroundGrade` is such a check, which is why §A's use
   of it survives this section. It may NOT be read for anything luma-,
   distance- or composition-valued: those are functions of where the ray
   happened to land that run.
2. **Before comparing any probe across runs, compare its pinning fields
   first** (`d:`, the material name). If they moved, the probe moved,
   and the delta is evidence about the ray, not the world. The
   `noonFacade` halving is the worked example: all ten sub-terms "moved"
   because the ray did.
3. **Street-level questions go to the grid sampler** (2,304 rays with
   denominators), never to a single ray. Single-ray emits are retained
   as identity checks only.
4. `meanLuma` is REFUSED as series evidence until its three-line
   ambiguity is repaired per the whole-run/sample-line rule (distinct
   keys, or the whole-run value onto the done line) — instrument queue
   item, by name. `shadowDrop` readings are quoted only with their
   cluster named; identifying the covariate that splits its bimodal
   series (the wet/rain `frames.tsv` join is the candidate) comes BEFORE
   the next use — a number from an unexplained mixture is two numbers
   wearing one name.

How much standing reasoning rests on unpinned rays, audited this
session: the one load-bearing use — §A — carried its own "one ray, one
point, one district" caveat and rested the family-wide claim on the code
reading plus the ordered `groundAlbedoBy`, so **no landed conclusion
needs retraction**. A verifier sweep goes to the queue by name — every
`SurfaceUnder`-style single-ray emit, and which conclusions quote it —
because "I found no other instance" is a claim about my memory, not
about the tree.

## E. The GroundGrade space note — YES: recorded here, and beside the
constant.

`GroundGrade` is 0.55 as the stored (gamma) value of a material
`_Color`; in this Linear project the shader multiplies by its linear
form, ≈0.267 — a ~3.7x darkening in light terms, not 1.8x. Anyone doing
linear-light arithmetic with "0.55" is off by 2x, which is precisely how
leg 1 read as plausible. Checked before writing: **Call 2's derivation
of 0.55 is UNTOUCHED** — it matched the archived frame's effective
multiplier in the SAME stored-value space, self-consistent end to end —
so the constant stands; only cross-space arithmetic was ever at risk.
One-line comment at the constant (`AssetLibrary.cs:522`) naming the
stored value, the linear equivalent, and which one the shader uses:
within the resident's hand-apply authority, rides the dispatch train.

## Additions to "what the next session must NOT re-litigate"

- **§A stands on the near/far gradient alone.** Do not quote the
  "1.8–2.2x gain" or any albedo-vs-rendered ratio from the 14f964a
  section — the dry lift's magnitude is unmeasured until `groundGainBy`
  lands.
- **No factor versus GTA is quotable** until the mattes land; the only
  citable form is direction — brighter than every reference relative to
  its frame, 7 of 7.
- **Single-ray probes are identity checks** (§D). A cross-run delta in
  one is not a finding until its pinning fields are shown unmoved.
- **`GroundGrade` "0.55" is a stored gamma value, ≈0.267 linear.** State
  the space whenever doing arithmetic with it, and never divide a
  gamma-stored number by a linear one.

## Addendum, same day — the stills-read third leg, and four attachments

> The horizon reading landed while this section was being written. Ruled
> here so §A's evidentiary basis is stated once, in one place. Adopted
> from the reader with attribution (not re-run here): ground 0.858 vs
> sky 0.326 in `district_copper`, the 7/7 floating-skyline measurement
> (450/1280 columns, median gap 26 px), the chrome-jacket pixels, the
> day12_noon +0.010 margin, and "72 gates, all about additions".
> Verified against source THIS session before adopting the leg:
> `SceneLighting.cs:290–295` sets the sky dome's horizon stop to
> `RenderSettings.fogColor` BY DESIGN (the seam argument), and
> `LightModel.FogColour`'s day arm is authored ~0.44 luma
> (`LightModel.cs:504–506`) while `SkyColour`'s day zenith is authored
> ~0.8 (`:315–316`).

**A-addendum. Leg 3 is ADOPTED as the PRIMARY leg — in a corrected
form — and it sharpens the finding at source.** Two corrections to the
proposed wording, then the ruling:

1. "A diffuse surface cannot out-radiate its own illuminant" is strictly
   true only under a sunless sky; with direct sun in the model (there
   is one — `SunwardDir` is real), a sky PATCH is not the whole
   illuminant and bright ground against darker sky is commonplace in
   photographs. The airtight, albedo-free, same-space form is
   CONVERGENCE: at the horizon, atmosphere dominates whatever the
   surface is, so far ground must approach the colour it stands
   against. Ground 0.858 beside sky 0.326 in one JPEG cannot both be
   the same atmosphere. That form needs no albedo, no colour space, no
   sun assumption.
2. And the source check makes it stranger and more useful: the code
   already forces horizon-sky = fog colour (`SceneLighting.cs:295`,
   written to make this seam "impossible"), and the authored day fog is
   ~0.44 luma. So far ground at 0.858–0.944 exceeds not only the
   sampled sky but the very colour distance is supposed to pull it
   toward. **The bright-at-distance term is therefore NOT the authored
   fog colour** — leg 2's parenthetical "(fog/atmosphere blending
   toward a near-white colour)" is hereby retired as a mechanism guess
   disproved at source. The finding is narrower and harder: an
   UNIDENTIFIED distance-dependent brightening that outruns both the
   fog and the sky. Known suspects, in rule-3 order for the landing
   read: a second fog writer (this exact two-writer fault is recorded
   as already having happened once, in `FogColour`'s own comment), an
   image-effect/grade term, or the sampled "sky" band not being the
   band assumed — the 0.326 reading against a ~0.8 authored zenith and
   ~0.44 authored horizon is its OWN open discrepancy, flagged, not
   diagnosed. The landing read quotes the existing fog emits
   (`SimDirector.cs:9513, :9533, :11802`) beside the mask numbers so
   the live `fogColor` is a printed fact, not an authored one.

   §A now rests on legs 3 and 2 as ONE finding — a distance-dependent
   brightening in the light path — with leg 3 primary (frame-internal,
   albedo-free, space-free) and leg 2 as corroboration. All standing
   orders unchanged: `GroundGrade` frozen, no lever before the masked
   series, falsifiers (a)/(b) intact.

**Skyline.** `skylineBaseDrop` + `skylineAfloat=N/23` (world-space,
render-free) REPLACE the queued `skylineFootGap` in the second
instrument batch and in the §D3 builder brief — the better instrument
for the same question, and the 7/7 measurement upgrades D1 from
eyeballed to measured. D2's premise ruling needed no strengthening and
its ranking does not move.

**The blunt answer, recorded because it changes how the work should be
described**: the content is landing — stone, cobbles, 219 chimney pots,
aerials, cranes, British fascias, and two frames that read RIGHT — and
the horizon plus the light are what is hiding it. That is the smaller,
more fixable problem, and it confirms the standing order of work:
lighting lever first (after the masked series), skyline second, decals
after. When Jafar next asks, this is the one-line shape: the town is
there; the light and the skyline are lying about it.

**Chrome bodies — new named item, ranked behind skyline, ahead of
decals.** The diagnosis method is the house style and is accepted:
settled by an EXISTING landed number (`bodyAlbedo` tops at 0.46, so a
0.999 pixel cannot be texture — it is specular), not by eye. Per rule
2: a `bodyGloss` printer (per-material smoothness/metallic of the worn
set, done line) joins the second instrument batch; the material fix is
sized from its landed values, not dispatched blind.

**day12_noon darker than 7 of 10 nights, margin +0.010** — the reader's
own flag is right: that margin is the 0.136-vs-0.135 class, a rounding,
not a measurement, and `darker10of10` is structurally within-day and
cannot see it. A cross-day noon-vs-night margin PRINTER (series, no
threshold, no gate) joins the second instrument batch; any bound waits
for the printed series per rule 2. No conclusion is drawn from the
+0.010 today, in either direction.

**"72 gates green, 0 red, and all 72 ask what a system ADDED"** —
recorded as the standing statement of rule 4's lesson: every gate
measures an addition, no gate asks what the frame looks like, which is
why the stills are read before any gate, every build. The second
instrument batch IS the repair path — each item in it converts a
looked-at fault into a number. No gate is weakened, none is invented
today.

**Net effect on the dispatch: NONE.** The train's contents stand as
listed (mask batch + `groundAlbedoBy` + `groundGainBy` + space fixes +
staging fix; nothing that moves a lever). The second instrument batch
grows by name: `skylineBaseDrop`/`skylineAfloat` (replacing
`skylineFootGap`), `bodyGloss`, the cross-day noon/night margin
printer, alongside the reader's earlier list.

---

# Ground-gain batch review — A–E confirmed against the tree; one stale comment found; one standing rule declared (director, 25 Aug 2026)

> Review of the builder batch executing §B of the measurement-audit ruling
> above (`groundGainBy` + the three-point order + the `:915–917` rewrite +
> the `:522` space note). Every load-bearing claim verified against the
> tree this session, not the report: `GroundGain.cs` read whole;
> `SimDirector.cs:10726–10772` (classifier and `Add` three lines apart,
> `c.linear` at :10769), `:15077–15091` (done-line emit and its comment);
> `AssetLibrary.cs:524–531` (the `:522` gamma note), `:907–955` (the
> rewritten comment quoting the retracted sentence), `:1007–1042`
> (`GroundSurfaceOf` / `GroundSourceAlbedo` → `MatAlbedo` / wrapper);
> `CoreTests/Program.cs:13314–13418` (exact accepting string, the trap
> pair, the rejecting cases). RULING: **APPROVE-TO-COMMIT after ONE
> one-line comment correction** (§D below), within the resident's
> hand-apply authority.

- **A. CONFIRMED.** The exact emit string is pinned in CoreTests; the
  ratio-of-means-not-mean-of-ratios distinction is pinned by the
  graded-copies case (concrete 8.571, where a mean of ratios gives 7.500);
  numerator and denominator come from one `Add` three lines after the one
  classifier call (`GroundSurfaceOf`), on the actual `sharedMaterial` the
  ray hit — a graded copy carries its own colour; `c.linear` at the call
  site, `GroundSourceAlbedo` → `MatAlbedo` (`m.color.linear`) on the
  source side; whole-run, on the done line, beside a comment saying the
  per-shot means live elsewhere and in a different space.
- **B. RULED SOUND, and the framing stands.** The two sides of
  `groundGainRays` are one condition counted at two points three lines
  apart in one loop (`logical.Length == 0 → continue` feeds both
  `_groundRaysGround++` and `Add`, whose own empty-drop cannot fire from
  this caller) — equal by construction, so `a != b` is the classifier
  disagreeing with itself and nothing else. The residual risk the
  resident named is real: the `a/b` shape reads as coverage to a grepper
  who never sees the comments. Because this key has NEVER landed, renaming
  is free exactly once — the next rung, queued by name, not blocking:
  **on mismatch the value grows a word** (`a/b/disagree`), the
  `nothing_measured`/`source0` idiom applied to the self-check, so the
  failure case cannot read as benign partial coverage. The healthy shape
  stays grep-stable.
- **C. CONFIRMED, with one precision the record keeps.** The 2.05..2.09
  trap is written at the emit site inside `GroundMaskRead`
  (`SimDirector.cs:10753–10759`) where a reader meets the number, echoed
  on the done line and in `GroundGain`'s header; the Rec.601/709 bias is
  named there with its measured 0.008%. Precision: the RATIOS are computed
  by the code under test (the tally divides 0.55 by the operand and the
  printed strings 2.049 and 2.089 are asserted), but the linear operands
  0.2684 and 0.26333 are pinned constants in the test, not derived in it.
  I verified both by hand this session — 0.55^2.2 ≈ 0.2684, exact sRGB
  ((0.55+0.055)/1.055)^2.4 ≈ 0.2633 — so the figures stand; a future
  editor changing `GroundGrade` must re-derive both operands, and this
  sentence is where that instruction lives.
- **D. CONFIRMED — with ONE stale comment the sweep missed, fix required
  before commit.** No live reference to `SurfaceNames.IsOneOf`,
  `AssetLibrary.IsGroundSurface` or `GroundGain.Rays` survives; the
  remaining mentions are comments recording the removals, the builder's
  report, and this file's `:868` describing pre-fix code as history —
  correct survivals all. But `GroundGain.cs:57` (the `Add` doc comment)
  still says "so `Rays` can be compared against the mask's own ground-ray
  count" — naming the deleted property, in the file whose batch deleted
  it: rule 1's second corollary, one line. Required correction: point the
  sentence at the comparison `Emit` performs (`groundGainRays`), not at a
  member that no longer exists. One-line hand-apply; no re-brief.
- **E. RULED A STANDING RULE, not two ad-hoc decisions — and it already
  has a third instance in flight.** The rule, in the words the next
  session reads: **measurement arithmetic and formatting live in Core,
  where CoreTests run them; the Game layer supplies only membership,
  order and live state (lists, materials, cameras). An emit written in
  the Game layer ships unrun in this container, and an unrun formatter
  printing a plausible string is the silent-instrument fault.**
  `SurfaceNames` and `GroundGain` are its first two instances; the
  already-queued NoSpaces-to-Core move (verdict-integrity §E above) is
  its third and was argued from the same precedent — three arguments for
  one rule is the definition of a rule nobody wrote down. The resident
  adds one line stating it to `.claude/rules/instruments.md` (the file
  loaded when editing measurement code), riding this same commit train;
  this section is the dated authority for that line.

Two patterns ratified for reuse, by name. **Quote the corpse**: a comment
retraction quotes the retracted sentence verbatim inside the repair
(`AssetLibrary.cs:924–932` is the exemplar), so the error cannot be
re-derived as if new — adopted as the house shape for every comment
retraction from here. And the builder's first CoreTest assertion rejecting
the CORRECT output (`Split('=')` on a value that legitimately contains
`=`), caught because the accepting case was actually run before shipping,
is rule 5b operating as designed — recorded as evidence the discipline
works, no action.

**Net: APPROVE-TO-COMMIT** after the one-line `GroundGain.cs:57` fix and
with the two riders (the `instruments.md` rule line; the
`groundGainRays`-mismatch-word queue item, named). Then the train
dispatches unchanged — this key's first landed series is what sizes the
lighting move, and nothing in this batch moves a lever.

---

# Fable-usage ruling — what one BATCH is, and where verification lives (director, 25 Aug 2026)

> Jafar, verbatim, today: *"have we actually been minimizing fable usage
> now (no more than necessary)? fable has its own usage limit and counts
> double against the full weekly limit."* The measured answer is NO — 9
> director spawns of 36 agents today (25%), five of them summing to 519k
> tokens, the day's total roughly 0.9M Fable tokens, ~1.8M at double
> weighting. The coordinator's four named causes are ratified as the
> diagnosis (verification briefed to the decision-maker; small batches
> multiplying trigger-1 reviews; a confirmation pass split from its
> ruling; one review paying twice across a usage-limit kill). The
> `director_cadence` repair — reference is now the last commit touching
> `ledger/Assets/Scripts`, not `HEAD` — is RATIFIED: it removes spawns
> that reviewed nothing, and weakens no trigger.

The six mandatory triggers are Jafar's and none of them moves. What was
never defined is the word "batch" in trigger 1, and the ambiguity is
what multiplied spawns. Ruled, in a form that cannot be read as licence
to skip a review:

1. **A batch is all builder work that lands in ONE reviewed commit.**
   The coordinator ACCUMULATES builder reports rather than committing
   each as it arrives, closing the batch at a natural boundary: a CI
   dispatch, a landing read, a queue reorder, or work that has become
   mutually dependent. Two hard edges: nothing accumulates past one
   dispatch cycle (a batch that waits a day is a stale queue wearing a
   different name), and a red-verify fix or evidence-channel repair
   never waits for a batch.
2. **Batching reduces spawn COUNT, never review DEPTH.** Every commit
   containing builder work still requires a director row — that is the
   trigger, unchanged, and `director_cadence` enforces it. Splitting
   builder work across commits to dodge a review is therefore
   impossible by construction; accumulating IS the only way to
   economise, which is the correct incentive.
3. **Verifier-first.** Any brief whose main content is
   claim-confirmation goes to a tier-2 verifier (read-only Opus) FIRST;
   the director is spawned on the verified position and RULES. The
   director still spot-checks the load-bearing citations — a report is
   a claim, a verifier's included — but against the verifier's named
   lines, which is minutes, not an audit. The ground-gain review above
   is the worked counter-example: its §§A–D were tier-2 work sent to
   tier 1.
4. **One decision, one spawn.** No confirmation pass separate from its
   ruling; a spawn killed mid-ruling RESUMES from its partial text and
   does not re-verify what it had already verified.

**Residence**: this defines a term the triggers left undefined; it
relaxes nothing, so it does not need Jafar's sign-off — but the
triggers live in CLAUDE.md's HYBRID RESIDENT section, and a definition
recorded only here will not be read at the moment of spawning. The
resident adds the batch definition and the verifier-first order there,
dated, citing this section and Jafar's question verbatim; if Jafar
reads any of it as loosening, his word reverts it. Until that edit
lands, this section is the authority.

The one-line answer for Jafar when he is next answered, in plain terms:
no — a quarter of today's agents were the expensive one; the causes are
named and fixed (verification moved to the cheaper tier, reviews now
batched per commit, the pointless-respawn bug repaired), and the
expected shape from here is roughly half the spawns for the same
oversight.

---

# Landing 3a4e335 — first `groundGainBy` read, ruling on A–D (director, 25 Aug 2026)

> First use of verifier-first (Fable-usage ruling, item 3): the tier-2
> position is taken as ESTABLISHED; I spot-checked citations only.
> Spot-checks done this session: `GroundSurfaceOf` confirmed a pure name
> match with no geometry test (`AssetLibrary.cs:1007–1008`);
> `FilmGrade.Bypass` confirmed real, static, default false
> (`FilmGrade.cs:204`); the landed row matches `runs/3a4e335.txt:87`
> verbatim; the verdict itself is GREEN (`gatesFailed=0 pass=True`), so
> nothing here is urgent. **One citation correction, direction only**:
> `TrafficHost.cs:1025` is `v.Id % 2 == 0 ? Metal : Concrete` — ODD ids
> feed `concrete`, not even ids. The substantive claim (~half the
> default-kind vehicles land in the `concrete` bucket) is unchanged; the
> parity is recorded so nobody later patches the wrong branch of that
> ternary.

## A. `groundGainBy` KEEPS ITS NAME AND GAINS THE FILTER THAT MAKES THE
NAME TRUE. Until the filtered version lands, NO row of 3a4e335's
`groundGainBy` — not only `concrete` — is quotable as ground.

Not renamed (the name states the intended question, and the question is
right); not withdrawn (deleting a key on its first landing for a fixable
classifier fault is the ratchet shape — the fix is three lines and rides
the very next dispatch, so no unfiltered landing need ever occur). The
coordinator's interim "concrete is unreadable" is WIDENED: `concrete` is
merely the worst (44% of rays, facades + odd-id vehicle paint + the `_b`
facade variant collapsed by `SurfaceNames.cs:46`); `sidewalk` carries
street furniture; `asphalt` and `kerb` purity is UNESTABLISHED in either
direction. A bucket not proven contaminated is not thereby proven clean —
so the honest description of this landing is "surface-NAMED buckets over
whatever the rays hit", and every per-row magnitude waits for the filter.
The filter lives at the RAY SITE (`SimDirector.cs:~10740`), not in
`GroundSurfaceOf`: the classifier answers "which family is this material"
and structurally cannot answer "is this surface ground" — its comment
gains one line saying the ray site supplies the geometry test, so nobody
later "fixes" the classifier by handing it geometry it cannot have.

**Also ruled dead with the buckets: finding 3's fitted statistics.** The
R2 −8.655, the negative b, the b=0 constrained fit are honest arithmetic
over four contaminated pairs at n=1; the QUALITATIVE conclusion —
rendered luma decoupled from source albedo — survives on finding 4's
mechanism and on the asphalt row's sheer magnitude, but the fitted
NUMBERS are not quotable forward, anywhere, ever. A regression over four
points whose buckets do not mean their names is not a measurement.

## B. The lighting diagnosis SURVIVES, and the lever WIDENS BY NAME: the
standing phrase "the lighting stack" now means the LIGHT-TO-JPEG PATH —
in-scene light AND `FilmGrade` — and no sub-lever is picked until the
Bypass A/B separates them.

§A stands untouched: legs 3 and 2 are frame-internal and albedo-free, and
findings 3–4 cannot reach them. What findings 3–4 add is two-fold:

1. **The addendum's "UNIDENTIFIED distance-dependent brightening" suspect
   list gains the post stack as a first-class suspect.** Bloom is
   additive, albedo-blind, and SPATIAL — far ground abuts the bright
   horizon in screen space, so sky bloom bleed is a candidate mechanism
   for the very convergence violation leg 3 measured. The ACES shoulder
   compressing everything toward near-white (rendered rows encode to
   sRGB 0.597–0.742) is the other. The Bypass A/B is therefore decisive
   for the addendum's open discrepancy too, not just for this key.
2. **A fact the record has not said until now, said plainly: EVERY
   frame-sampled number in this fork is POST-GRADE** — ground rows, sky
   band, near/far pairs alike. The numerator of `groundGainBy` is
   `tonemap(exposure x light x albedo) + bloom + grain` read off the
   encoded frame; the 68x on asphalt is exactly what an additive,
   albedo-blind term does to a ratio as the denominator falls, and is
   quotable ONLY as that signature — never as "gain of the light".

Nothing about "the surface is not the lever" moves. `GroundGrade` stays
frozen in both directions; falsifiers (a)/(b) stand; and no exposure,
fog, tonemap, or bloom constant moves until `groundGainByRaw` beside
`groundGainBy` says WHICH term is lifting the road.

## C. The verifier's measurement is APPROVED, with the order CLARIFIED
and three amendments — ONE dispatch, not two.

"Normal filter FIRST" is ruled to mean first IN THE TALLY, not first in
a separate round trip: the filter conditions BOTH emits (graded and raw),
so the A/B never describes a contaminated row, and the batching rule
makes the second round trip pure waste. Contents:

1. `hit.normal.y > 0.9` at the ray site, applied before bucketing;
   per-row DROPPED-ray count and per-row TOP CONTRIBUTING MATERIAL NAME
   printed (both the verifier's own proposals, adopted — they are rule
   3b's denominator and the legibility that lets `mat_concrete_b` and
   vehicle paint convict themselves). The 0.9 is a geometric classifier,
   not a tuned bound — ground is horizontal by construction — and the
   dropped-count printer is its audit: if `kerb` collapses to near-zero
   rays, the vertical kerb faces WERE the bucket, and that is a finding
   about the old rows, not a fault in the filter.
2. `FilmGrade.Bypass` A/B in the SAME build: `groundGainByRaw` beside
   `groundGainBy`, same rays, same filter, colour space named at both
   emits per `instruments.md`, the 2.05-cluster gamma trap extended to
   the raw key's comment.
3. No gate, no bound, no lever. This landing makes n=2; the band
   mechanism stays the standing §B one (series first, band from
   evidence, director close-out).

## D. CONFIRMED — everything that moves a lever or sets a bound stays
BLOCKED. n=1 on this key, ±4% run-to-run noise floor (the kerb-vs-
concrete 4% gap is inside it and is not read), rows not yet meaning
their name, and the verdict green so nothing forces haste. Added to the
blocked-by-name list: any conclusion quoting finding 3's fitted
statistics (§A above).

## The next dispatch, ranked

1. **Normal filter on the ground tally** + per-row dropped count +
   per-row top material name (§C.1) — the change that makes
   `groundGainBy` mean its name.
2. **`FilmGrade.Bypass` A/B**: `groundGainByRaw` beside the graded key,
   same rays, same filter, spaces named (§C.2) — the only measurement
   that can separate ambient lift / ACES shoulder / bloom, for this key
   AND for the addendum's open sky discrepancy.
3. The already-approved unlanded riders of the standing train, unchanged.
4. **Nothing that moves a lever**: no exposure, fog, tonemap, bloom,
   `GroundGrade`, or `AlbedoScale` change; no skyline geometry; no
   decals.

## Additions to "what the next session must NOT re-litigate"

- **No row of 3a4e335's `groundGainBy` is quotable as ground**, and
  finding 3's R2/b fit numbers are not quotable at all.
- **"The lighting stack" in every standing order now reads
  "light-to-JPEG path, in-scene light plus FilmGrade"**; the sub-lever
  is chosen only off the landed Bypass A/B, once.
- **The 68x asphalt figure is the signature of an additive/compressive
  post term over a raw denominator** — never quote it as a gain of the
  light, and never "fix" it by moving albedo.
- **`TrafficHost.cs:1025`: ODD vehicle ids feed `concrete`** (verified
  this session). Do not patch the even branch.
- **`groundAlbedoBy` and `groundGainBy` denominators are different
  moments and different populations** (verifier finding 7, adopted) —
  do not cross-check one against the other.

---

# Dispatch review of 06f51f39 — filter + Bypass A/B batch, A–G, and one commit-message retraction (director, 25 Aug 2026)

> Review of commit `06f51f39`, which executes the 3a4e335 ruling's §C
> (the up-facing filter and the `FilmGrade.Bypass` A/B, ONE dispatch).
> Unusual shape, recorded so it does not become precedent by silence:
> the batch was COMMITTED unreviewed, labelled WIP, because the loop was
> stopped at Jafar's request mid-flight and unpushed work is lost work
> in this container. That call was right; this review therefore gates
> the DISPATCH, not the commit, and nothing below re-litigates the
> commit's existence. Verifier-first: the tier-2 position is taken as
> established; spot-checks done this session against the tree, not the
> report: `GroundGain.cs` read whole (`Emit` :153–194, `EmitRaw`
> :207–233, `TopMat` :239–248, `Safe` :272–288); the ray site
> `SimDirector.cs:10855–10958` (`GroundUpDot = 0.9f` declared :10713
> with the not-a-tuned-bound rationale, test at :10884, `Drop` +
> `continue` at :10892–93, single `Add` with both numerators :10953,
> raw pixel at the same `row * w + col` :10946); the emit pair
> :15289/:15314; `CoreTests/Program.cs:13314–13537` (kerb-collapse
> print fixture :13343/:13384, no-raw case :13428–33, dirty-name
> rejecting case :13492–13503, mode :13520–30, ordinal tie :13531–36);
> `WorldBuilder.cs:618–625` (kerbs are 0.2m strips as predicted);
> `ledger/.verify-footer` present on disk — green, 3834 CoreTests,
> Game layer compiles (179 files), cadence reference = this commit.

## RETRACTION FIRST — the message on commit 06f51f39 is FALSE about the
sweep, and this paragraph is the correction of record.

Corpse-quote, per the house shape: the commit message says *"the comment
sweep is INCOMPLETE"*. **It is false. The sweep FINISHED, and its fixes
are inside that same commit** — verified this session: the `SUBSET`
paragraph at `SimDirector.cs:10601–10604` and the `sits inside`/SUBSET
rewrite at `SurfaceNames.cs:55–72` are on disk. The coordinator has
named the cause itself: the sentence was asserted from the builder's
last STREAMED line, not from the disk — rule 1, applied to an agent's
output stream, which is a comment about the work and not the work. The
commit is pushed and stands as history; the corrections live in TWO
places because the false sentence lives in the commit feed, which
nobody can edit: (1) this paragraph, in the record every ground session
reads; (2) one line in `queue.md` beside the ground items — resident
hand-apply, exact text: *"NOTE: 06f51f39's message says the comment
sweep is incomplete — FALSE, the sweep finished and landed in that same
commit (decision-ground-albedo.md, 25 Aug dispatch review). Do not
re-brief it."* The queue gets the line because the queue is where a
session believing the message would mint the re-do item. Nobody re-does
the sweep.

## A. CONFIRMED — the three-field key is an improvement, and the identity
is what answers my own two-field objection.

`groundGainRays=admitted/notup/mask` carries its own audit on the line:
`admitted + notup == mask` by construction (the caller's
`logical.Length == 0 → continue` precedes `_groundRaysGround++`, and
`Add`/`Drop`'s empty-name guards are unreachable from that caller), and
the delivered example checks by inspection — 6 + 11 = 17. The two-field
`a/b` I flagged could only be read as coverage; the three-field triple
can be CHECKED as a sum, and a reader who mistakes it for a fraction
gets numbers that refuse the reading. Per-row, the tail is
self-labelling words (`@3up/0notup`), not positions. The queued
mismatch-word rung CARRIES OVER in its new form: on
`admitted + notup != mask` the value grows the word `disagree` — still
queued, still not blocking, because a mismatch is already legible as
three numbers that do not add, which the old shape could not say at all.

## B. CONFIRMED — the `^name` printer is a MODE and its rejecting case
was actually run.

`TopMat` is a mode over ADMITTED rays with an ordinal tie-break (pinned:
three `mat_concrete_b` beat one `mat_concrete` :13528; `mat_alpha` beats
`mat_zebra` on a tie :13534); `^none` for an empty row and `^unnamed`
for a nameless material are both words, not blanks. The sanitiser's
rejecting fixture is the literal horror case — `mat kerb, spaced=odd@1
(Instance)` — and the assertions are the right three: the verdict does
not split (3 space-separated tokens), no fifth row appears, and the
folded name `^mat_kerb__spaced_odd_1` survives whole. This is the
printer that lets `mat_concrete_b` and vehicle paint convict themselves,
which is what 3a4e335's 44% contamination needed and lacked.

## C. CONFIRMED STRUCTURAL. One filter, one ray set, is enforced by
shape, not by adjacency.

One `GroundGain` object (`_groundGain`, :10683); the geometry test
(`hit.normal.y <= GroundUpDot` → `Drop` + `continue`) sits ABOVE the
single `Add`, so a rejected ray reaches neither arm; both numerators
enter through that one `Add`, with the raw pixel read at the same
`row * w + col` as the graded one; and the raw emit deliberately prints
neither `notup` nor `^mat` — admission is ONE decision, and
`@<raw>of<admitted>up` with the two equal is the on-the-line proof the
two keys describe one ray set. The mask-family keys keep their
unfiltered regime, guarded in words at :10875–83 — the regime-change
rule applied prospectively, correctly. `GroundUpDot = 0.9f` is exactly
the ordered geometric classifier and nothing here tunes it.

## D. CONFIRMED. A failed bypass prints words, not a black road.

`rawKnown=false` moves no raw sum, and `EmitRaw` prints
`nothing_measured@0of<admitted>up` — asserted at :13428–33. A raw row
reading `0.0000` would be read as "black before the grade", which is a
CONCLUSION of the A/B, and this batch correctly makes that misreading
unprintable. Both directions are in the selftest (populated raw rows in
the pinned strings; the no-raw case synthetic).

## E. CONFIRMED — pre-writing the interpretation is right HERE, because
it is a falsifiable prediction executing an existing ruling, not a
pre-commitment.

The 3a4e335 ruling §C.1 already said, before this code existed: "if
`kerb` collapses to near-zero rays, the vertical kerb faces WERE the
bucket — a finding about the old rows, not a fault in the filter." The
comment at `GroundGain.Emit` restates that ruling where the reader
meets the number, with the geometry (`WorldBuilder.cs:618–625`, 0.2m
strips — verified) as its basis. The CoreTest fixture pins how the
collapse PRINTS (five synthetic Drops in, `0up/5notup^none` out), not
that it occurs — the formatter is under test, the world is not. The
fence, stated so the prediction cannot harden into a gate: **a kerb row
landing `@Nup` with N>0 is DATA, not a fault** — sliver tops sampled —
and neither outcome goes red, because nothing is gated. This is the
house prediction shape (the `groundPatch` F6 precedent): written in
advance, falsifiable in both directions, read at the landing.

## F. THE THREE DOCS: nothing is edited in place. Two are LOGs already
covered; the third's stale sketch is corrected HERE, append-only.

- `agent-reports/ground-gain.md` — LOG, banner "NOT CURRENT once
  landed"; it landed at 3a4e335, so §3/§8's two-field grammar and the
  "divides one's output by the other's" sentence are covered history.
  No edit.
- `agent-reports/ground-gain-verified.md` — LOG, banner "NOT CURRENT
  once the normal filter lands", i.e. it retires itself at THIS
  dispatch's landing; its 3a4e335 row in the old grammar is a true
  quote of a real landed line. No edit.
- This file's §B sketch (the `:918` region, measurement-audit ruling):
  corpse-quote — it sketches
  `groundGainBy=[asphalt:<renderedLinear>/<sourceAlbedo>=<ratio>/...]`
  with no `@…up/…notup^…` tail, because it was written before the
  3a4e335 landing forced the filter. **The grammar of record is the
  delivered one, pinned in CoreTests**: per row
  `name:<ren>/<src>=<ratio>@<n>up/<d>notup^<topmat>`, done-line triples
  `groundGainRays=admitted/notup/mask` and `groundGainRawRays=raw/
  admitted`, raw rows `@<raw>of<admitted>up`. Read the sketch as
  superseded mechanism prose; this file is append-only per the standing
  file warning, so the correction lives here, not at the sketch.

Confirmed with the coordinator: nothing in the 3a4e335 ruling is
falsified by the delivered shape — §C.1's two printers are delivered as
specified, plus the mask-count third field, which strengthens the
self-check and changes no ordered semantics.

## G. CLEARED TO DISPATCH.

Verify is green on disk (footer read this session, not quoted from
memory); no lever moves, no bound is set anywhere in the batch — the
only new constant is the ordered geometric classifier; the filter and
the A/B ride as ONE dispatch per §C's "first in the tally, not first in
a round trip". Reading order at the landing, in one place:

1. Line 1 sha and the `NO PLAYER LOG` line before any frame or number.
2. `groundGainRays`: admitted + notup == mask, or stop — the classifiers
   disagree and nothing else is readable. Then `groundGainRawRays=a/b`:
   a == b is the one-ray-set proof; a < b means the bypass render failed
   on some shots and the raw rows are means over fewer rays — read
   `groundGainRawShots` before comparing arms.
3. Ratios clustering 2.05..2.09 on EITHER arm: the gamma trap inside the
   instrument, rule 3, before any sentence about light.
4. The kerb row per §E — either outcome is a finding, neither is red.
5. This landing makes n=2 on a repaired key: NOTHING moves a lever off
   it. The sub-lever choice (ambient lift vs ACES shoulder vs bloom) is
   sized from the landed A/B split per the 3a4e335 §B order, and the
   band mechanism stays series-first with a director close-out.

Not re-litigated from here: the 06f51f39 message's sweep sentence is
retracted above — do not re-brief the sweep; the `:918` sketch grammar
is superseded — quote the CoreTests-pinned shape only.

---

# Landing review of 36b90c9 — the A/B answers, A–E ruled (director, 25 Aug 2026)

> The Bypass A/B landed clean: sum identity holds
> (`groundGainRays=4974/1078/6052`, 4974+1078=6052), one-ray-set proof
> holds (`groundGainRawRays=4974/4974`), 961 of 2742 concrete rays
> rejected as vertical. Tier-2 verifier established the position;
> spot-checks done this session against the tree and the landed run,
> not the report: `FilmGrade.cs:226` bypass-first and exactly one
> `OnRenderImage` under `ledger/Assets/Scripts`; the single `Add` at
> `SimDirector.cs:10953`; the fog toggle at `:9077-9079`; the raw/graded
> rows and the anti-ordering read directly off `runs/36b90c9.txt:87`
> (asphalt 0.0075 albedo / 0.1499 raw vs kerb 0.0670 / 0.1417).
> Appended by the resident from director-supplied text: the whole-file
> rewrite this Write-only session would have needed is the operation
> that once destroyed 380 lines, and the record outranks the ceremony.

## A. The grade half is CLOSED AS UNDERSTOOD and the lever is HELD.

Adopted: the graded arm is `r * ACES(3.44 * raw)` with one free
`r = 0.834`, all four materials inside ±5%; the bypass is structural,
bloom is excluded, the aperture is one number. Nobody re-derives this.
But the same landing shows the RAW arm is where the fault lives —
asphalt reads 19.98x its own albedo BEFORE the grade touches it — so an
aperture set now would be calibrated against a world about to change,
and re-set after the raw term is attributed: two lever moves where one
suffices, on a key at n=1 since the filter changed its regime. The
06f51f39 review's §G.5 ("nothing moves a lever off this landing")
stands. The aperture moves ONCE, off a printed series taken after the
raw-side term is attributed — rule 2, and one move instead of two.

## B. Next-measurement order AMENDED: (1) stays first, (3) is promoted
to second, (2) is CUT.

1. **Per-material `hit.distance` into the SAME `GroundGain.Add` call**
   (`SimDirector.cs:10953`) — same ray, no new render. It closes the
   fog term arithmetically for nothing, and it is ALSO the
   grazing-angle proxy the specular suspect needs (an aerial camera's
   long rays are its grazing rays), so it serves both hypotheses from
   one field. Emit per row as mean plus spread, statistic named on the
   line per the instrument rules.
2. **Smoothness A/B: an arm forcing `_GlossMapScale = 0` on the ground
   materials, same rays** — the only item that tests the actual
   suspect. Same shape as the Bypass A/B; both arms print their ray
   counts so the one-ray-set proof carries over.
3. The verifier's (2) — a third render arm with `Bypass=true; fog=false`
   — is cut, twice over: the fog model is already structurally dead
   (anti-ordering, §"fog suspicion" of this landing), and the arm would
   lean on exactly the toggle finding C leaves unproven. If the
   distance field somehow revives fog, this arm can be re-queued then.

## C. The `fogOff` rung is ILLEGIBLE, NOT CONVICTED — and the arithmetic
on printed numbers says equality is the EXPECTED reading at facade
distance.

Finding adopted as a rule-3b fault: `fogOff` equals `all` to three
decimals in every kept run, and nothing in the output distinguishes
"fog contributes nothing here" from "the toggle at `SimDirector.cs:9077`
never reaches that render". But do not read the equality as evidence of
a dead toggle: the probe's own line prints `d:8.4` and
`density=0.0131` (ExponentialSquared), and exp(-(8.4*0.0131)^2) = 0.988
— a ~1.2% pull toward fogRGB, which on 0.082 is +0.001 and vanishes at
three printed decimals. A WORKING toggle prints exactly what the
history shows. At ground-tour depths (20.8–43.8m) the same arithmetic
gives a 7–28% blend, decisively visible.

The repair is 5b's corollary — plant the condition: a third reading in
the facade ladder with fog forced dense (density x10, restored in the
existing `finally`), printed beside `fogOff`. If the planted reading
moves, the toggle reaches the render and `fogOff==all` becomes a
legible pass; if it does not, the rung is dead and every historical
`fogOff` is retired. Until that lands, NO fog measurement may cite the
`fogOff` rung.

## D. Asphalt's DENOMINATOR is under audit; the ratios are quotable only
as "large", the orderings survive.

Adopted: `MeanTexLuma` blits to an 8x8 ARGB32 linear RT, whose 8-bit
quantum (0.0039) is over half asphalt's reported 0.0075, and whether
mip selection yields a true box mean was not established. The cheapest
test is approved: print `MeanTexLuma` beside the texture's CPU-side
mean, same dispatch. Until it lands: the 67x / 19.98x asphalt figures
are not quotable as numbers, only as "the raw arm is far above any
direct-light account". What SURVIVES D either way: the fog refutation
(asphalt-below-kerb ordering holds at ±1 quantum; 0.0075 vs 0.0670)
and the grade model in §A (its fit is over rendered lumas, with albedo
only labelling rows).

## E. `gates.py --series` reading a schema change as a world change:
REAL, QUEUED, not this dispatch.

`groundGainRays` went `6041/6041` → `4974/1078/6052` and `--series`
counted "changed 1 time(s)". A format change is a regime change, and
this file's own rules say no statistic survives one — the reader should
print a REGIME MARK at a schema boundary, not a change count across it.
Local tool, no render, no urgency now that it is named: queue item
"series-schema-mark", builder work, its accepting case is the live
history file per the instrument selftest rule.

## The specular suspect's standing

Reflection-probe / GI specular is ADOPTED AS LEADING SUSPECT, MEASUREMENT
ONLY. It is inferred (albedo-blind by construction, probe live per
`LightModel.cs`, `_GlossMapScale` wetness-driven, and the landed
`districtGround` line shows asphalt at gloss 0.78 / glossScale 0.93 /
probes:1) and supported by two within-frame picture reads (wet-dark
beside dry-bright in `district_gullwing`; dark sky over near-white
ground in `district_ironside`) — which are hypotheses, not numbers
(rule 4). No smoothness, probe or material lever moves off a picture.
Dispatch item 2 is its test.

## The next dispatch, ranked, ONE batch

1. Per-material ray distance in the same `Add` (B.1).
2. Smoothness A/B arm, `_GlossMapScale = 0` (B.2).
3. `fogOff` planted-density self-proof rung (C).
4. `MeanTexLuma` vs CPU-side texture mean, printed side by side (D).
5. NOTHING that moves a lever: no exposure, aperture, fog, tonemap,
   bloom, smoothness or albedo change ships in this batch.

Queued, not dispatched: `series-schema-mark` (E).

## Not re-litigated from here

- The grade model (exposure x ACES, one free `r`) is settled; only the
  aperture VALUE remains open, and it is set once, later, off a series.
- Fog as the raw-arm explanation is dead by anti-ordering; no `(k,f)`
  refits.
- `fogOff==all` is not evidence of a dead toggle (the d:8.4 arithmetic
  above); it is evidence of nothing until the planted rung lands.
- For the record: the verifier retracted its own `noonFacade` −25%
  finding against the series and refused `aoSpread` as ambiguous —
  that is the instrument-first discipline working, noted so the
  retraction is not re-found as a fresh anomaly.

---

# DIRECTOR RULING — the period skyline batch (25 Aug 2026, trigger 1)

Appended here under this session's precedent for this file: the batch
moves `groundMask*`, so its ruling belongs beside the ground-measurement
plan above, and the dispatch ordering below binds that plan's batch.
Verify green at review (3853 CoreTests, 180 Game files compiling, docs
82/82). Citations spot-checked in code, not taken from the report.

## Rulings, A-G

**A — APPROVED. The cause is found, not patched.** The replay's own
test: it PREDICTS the per-district pattern (north cameras hang, side
cameras seat) and it independently reproduces the two slots inside the
Exchange footprint that `SimDirector`'s vantage note recorded BEFORE
this analysis existed — a fact the replay was not fitted to. The fix is
in code as claimed: an offset outline of `StreetMap.BoundsOf`, walked
by perimeter length. Spot-checked: 4*(507+301.5)=3234m over 34 slots is
the 95.1m slot the report quotes, and the E/W edge span z+299..-304
matches the code comment.

**B — APPROVED, AND RATIFIED AS A STANDING PATTERN.** The insight is
correct and general: a seating metric measures distance to a datum and
says nothing about whether the datum EXISTS under the footprint. Every
hanging block read foot-gap 0.00 because it was seated at y=0 exactly —
over sea. `skylineByEdge`'s shape is right: per the axis the fault can
vary on (edge), not per district, because a per-district split would
attribute a placement fault to whichever camera faced it. Wording for
`.claude/rules/instruments.md`, to land with this commit:

    - **A placement metric ships in two halves: distance to the datum,
      and whether the datum exists under the footprint — plus a
      breakdown per the axis placement actually varies on (edge,
      region), never per camera.** Eight blocks hung over open sea at
      foot-gap 0.00 exactly; `skylineByEdge` is the half that saw it.

**C — RECORDED, and the correction runs toward me.** I told the builder
the detachment was hundreds of pixels; measured at `TourVantage`
geometry (12 px/deg at 720 lines / 60 deg vfov), the foot-to-horizon
band is ~20-40 px, consistent with the original 25 px finding. My
hundreds was foot-to-ROOFTOP — real, but a different length. The 25 px
figure STANDS and is not to be re-doubted; the builder measuring rather
than accepting a director's correction is rule 3 applied correctly to
the director, which is what tier-2/3 independence is for.

**D — APPROVED.** `GroundMinZ` is written where the slab is built and
read at the apron (one rectangle, one implementation — the fault's
actual root). Both halves of the water test are in code: the S edge is
skipped AND any slot with `at.z < apronMinZ + 55` is skipped, the 55
derived from the measured worst post-yaw footprint (96m-wide works,
49m half-extent), not chosen.

**E — APPROVED WITH ONE RIDER (a comment line, in this commit).** The
apron keeps its collider only because the per-block collider-destroy
loop never reaches it; the deliberateness lives solely in a LOG report
that instructs its own deletion once the keys land. One line at the
apron's creation: collider KEPT deliberately — `groundMask` rays must
hit visible land; stripping it makes the instrument report sky over
ground with nothing saying why. Dispatch ordering ruled below.

**F — APPROVED, verified in code.** `MakeCrane` at k=1 reproduces the
fixture exactly (`_tower_up` 1.9m square, y10..18, placed x36 z-174),
and exactly three `SimDirector` comment sites quote it. `MakeGasholder`
likewise serves both the goods-edge gasometer and the band.

**G — CHANGE REQUIRED: "queued" must mean the QUEUE.** The three
follow-ups are named only in `skyline-period.md`, a LOG that supersedes
itself on landing; none is in `queue.md`. Before commit, add one item
carrying: (i) `skylineFit` is series-first — one slot number (95.1m)
replaces the radius-dependent arc, so 1.76 under the old divisor is not
comparable and nobody quotes a fit until the new series lands; (ii)
`groundMask*` and `farFrac` re-baseline after the apron — a REGIME
CHANGE in those series, to carry the schema mark when it lands; (iii)
supersede the LOG once the four skyline keys land. Also annotate two
stale queue lines while in the file: "dockside skyline arc" (the band
is an outline now) and the DISTANT-SKYLINE greying item, whose named
towers no longer exist — the named-object measurement transfers to the
new blocks.

## Dispatch ordering for E (binding)

ONE dispatch, both batches together: the skyline/apron batch rides with
the ground-measurement batch above (per-material ray distance, gloss
A/B, fogOff rung, MeanTexLuma). Never a ground-measurement-only build
first: a pre-apron baseline is voided on the very next landing — the
exact fate of the 7/7 darkening baseline after the dry tour — and the
ground batch's items are within-run comparisons, which the apron does
not confound. The cross-run series that DO move are named in G's queue
item and get the mark. A premise fix does not queue behind a baseline.

## Close-out and the ladder

Premise: a 1988 British port horizon is works, stacks, spires, council
slabs, one crane line and a gasholder — this batch is the premise
repair, and the glass towers it retires were never chosen by anyone.
Quality: kit meshes wherever a kit has the shape (14/21), primitives
only where `prop-reach`/`prop-dimensions` show nothing on disk does —
measured before geometry, which is the standing order's shape. Next
rungs are named and queued: `city-kit-suburban` (13 models, unreached),
`detail-tank` as a ground-level dock prop. Not closed until the four
skyline keys land in a verdict and the stills are read: `skylineByEdge`
should read k/k on every edge, and the report's own header instructs
its supersession at that point.

---

# DIRECTOR RULING — the visual plan is REPLACED; cadence rules bind (25 Aug 2026, Jafar escalation: "this goal is a must")

Ruled on Jafar's direct order, delegated to the director. Full plan:
`visual-bar-spec.md` §4 (rewritten this session, whole-file Write after a
whole-file read; §1–3 and §5–8 substantially retained, §3 is a new
technique scorecard, §9 records why V0–V6 fell). This entry carries only
what BINDS other rulings in this file.

## 1. The biggest gap is named from the frames: VALUE-STRUCTURE INVERSION.

All five references: sky is the brightest broad surface, ground mid-dark
with the widest tonal variety, everything on contact shadow. Our noon
stills: near-white ground under a storm-dark sky. Cause chain: the
albedo-blind ground term (attribution batch in flight, this file) × the
3.44 noon aperture (LightModel.cs:160, calibrated against the broken
ground response) × an overcast dome authored dark. Detail work on a
clipped ground is invisible, so R0 (value structure) precedes ground
decals — which CONFIRMS Call 1 (ground first) and extends it upward
into the dome and aperture.

## 2. What this ruling does NOT touch — prior rulings all stand.

The attribution batch, its ordering, "no contested lever moves in that
batch", the skyline/apron ride-along, the aperture moving ONCE off a
post-fix printed series (36b90c9 §A), the decal unblock condition for
GROUND decals. One split: WALL-side surface history (posters, streaks)
is not blocked by the ground question and may ride any dispatch as
visible work.

## 3. TWO CADENCE RULES, standing, on the D question (measurement vs
visible), ruled by the director as the only tier that can:

  a. **Every dispatch ships at least one visible change** a person can
     point at in a still, unless a red gate blocks the build.
     Measurement-first governs LEVERS (rule 2 untouched); it is not a
     licence for measurement-only dispatches. This week produced ~15
     instrument fixes, one visible change, one regression — that
     balance is ruled a failure mode, not diligence.
  b. **Paired stills are read before any number at every landing.** The
     washout is the proof: a 3.07x exposure lift shipped and two days
     went to measuring its symptom unconnected to its cause, because no
     landing put the new noon beside the old one.

## 4. The convergence instrument (R1) is ORDERED, rides with R0:
five player-height cameras matched to the five reference compositions
(`ref_1..ref_5`, committed every run), the five hand-painted reference
mattes (already approved, unbuilt), and a small fixed panel (band
medians, shadowed:lit, ground spread). Aerial stills stop being
judgement frames. At every landing the biggest visible difference is
written in one sentence; the same sentence three landings running
becomes the next phase, whatever the plan says.

## 5. R0's gate is an ORDERING, not an invented threshold: per noon
still, skyBand > litWallBand > groundBand > shadowBand, and rendered
ground lumas ordered as source albedos (asphalt < kerb < paving).
Margins come later from the landed series; the order comes from the
references (7/7 on the sky-vs-ground half already).

## Additions to "what the next session must NOT re-litigate"

- V0–V6 is replaced by R0–R5 (`visual-bar-spec.md` §4/§9); do not
  execute against the old phase list or re-derive it from roadmap
  M17.10's stale prose — the roadmap row points at the spec.
- The 3.44 day aperture is a wrong value arrived at correctly; it is
  HELD (not reverted piecemeal) and dies with R0.b's single re-set.
- Cadence rules 3a/3b bind every dispatch and landing until Jafar
  calls the bar met.

---

# THE GROUND IS ALBEDO-BLIND, MEASURED AT EYE LEVEL — first firing of `ValuePanel`, landing `b7d232b` (25 Aug 2026)

**This is the reading the whole file has been waiting for, and it took a
camera at 1.7m to get it.** `refPlaced=5/5`, `valueShots=23/23`,
`valueRays=52992` — denominators on every row.

## 1. The value structure is inverted at street level, everywhere

Ground brighter than sky in **all five** reference cameras and **all seven**
districts:

| shot | sky | ground |
|---|---:|---:|
| ref_1 | 0.658 | **0.844** |
| ref_2 | 0.711 | **0.774** |
| ref_3 | 0.603 | **0.742** |
| ref_4 | 0.710 | **0.848** |
| ref_5 | 0.716 | **0.819** |
| district_hook | 0.406 | **0.762** |
| district_copper | 0.395 | **0.750** |
| district_ironside | 0.383 | **0.721** |
| district_downtown | 0.449 | **0.789** |
| district_strip | 0.404 | **0.741** |
| district_fairview | 0.395 | **0.796** |
| district_gullwing | 0.376 | **0.713** |

Every reference the bar is set against has sky as the brightest broad
surface. `ref_1` reads as SNOW.

## 2. And the ground barely responds to its own albedo — this is the cause

`valueAlbedoOrder`, `ref_1`, source albedo : rendered luma —

    asphalt 0.008 : 0.853    concrete 0.020 : 0.881
    sidewalk 0.021 : 0.761   kerb     0.067 : 0.862

**An 8x spread in source produces essentially no spread on screen.** Asphalt
authored near-black renders at 0.85. That is why every attempt at ground
surface history has been invisible: detail on a clipped ground cannot be
seen, and the clipping is near-total. The same shape holds in every district
row above.

## 3. WHY THIS WAS NOT SEEN FOR WEEKS — IT IS THE RAIN, NOT THE ANGLE

**RETRACTED WITHIN THE HOUR, AND THE FALSE SENTENCE IS KEPT BECAUSE IT WAS
PLAUSIBLE AND I PUBLISHED IT.** This section first read:

> *"Same run, same instant: `day1_noon` reads sky 0.445 / gnd 0.237 — the
> CORRECT order — while `ref_1` at eye level reads sky 0.658 / gnd 0.844.
> The frames the project has been judged on are the one angle that hides
> the fault."*

**Wrong, and refuted by a column I already had.** `frames.tsv` carries `rain`
and `wet` per shot. `day1_noon` is **wet=1.00** — a soaked road, which is
dark. Every `ref_*` is **wet=0.00**. So that comparison put a wet road beside
five dry ones and read the difference as camera height. It is the exact fault
this file exists to catch, committed by the resident, in the paragraph
announcing the instrument that catches it. **The director named this caveat
BEFORE the data existed** — *"ValuePanel samples must carry weather state or
the series mixes regimes"* — and it was written down and then not applied.

**Like for like, both DRY:**

| shot | height | wet | sky | ground |
|---|---|---:|---:|---:|
| `day5_noon` | review | 0.00 | 0.441 | **0.719** |
| `ref_1` | eye | 0.00 | 0.658 | **0.844** |

**The inversion is in BOTH.** The aerials never hid it. What hid it is that
`day1_noon` — the frame read at almost every landing — happens to be a
raining frame, and **a wet road is dark.** The project has been judging its
daylight value structure off its wettest daytime shot.

What eye level genuinely adds is SEVERITY (0.844 against 0.719) and a picture
a person cannot argue with. That is still worth the five cameras; it is not
the claim I made an hour ago.

## 4. What is NOT established, so nobody over-reads this

- **Weather is not yet carried per sample, and the director named this before
  the data existed.** `day1_noon` is a RAINING frame with a wet, dark road;
  `ref_1` shows a dry one. Comparing those two directly mixes regimes. **The
  §3 comparison above is therefore SUGGESTIVE, not proven** — the panel needs
  a weather field before it can be settled, and that is the next instrument
  step, ahead of any lever.
- **The daylight-vs-grade fork is still open.** A grade nonlinearity biting
  only at daylight levels fits this evidence exactly as well as an aperture
  fault. §1 and §2 do not separate them.
- **Three of five reference cameras sampled ZERO lit-wall pixels**
  (`litnone@0`), so two of the three orderings are untestable there and print
  `?` rather than a guess. Honest, and a camera-aim gap to close.
- The builder's written prediction was `1of3` on dry noon stills. `ref_3`
  landed exactly that; `ref_2` came back `2of3`. Nothing returned `3of3`, so
  its own "suspect the instrument first" alarm did not fire.

## 4b. `ref_3` SHOWS THE DETAIL IS ALREADY THERE AND BEING ERASED

Read after §4, and it changes what the fix BUYS rather than what it is. The
`ref_3` frame is not a bare white road: cracks, tyre marks, a dark centre
line and standing wet patches are all visibly present — **authored surface
history, crushed into near-white.** So the ladder rung "the ground needs more
dirt" is the wrong next move and would be wasted work: **we are not short of
ground detail, we are erasing the ground detail we already have.**

That is the §1/§2 argument made concrete. An 8x albedo spread arriving as no
spread on screen does not merely flatten the tone — it takes the contrast
range that surface history lives in and spends it. **Any further ground
authoring before the daylight path is fixed is invisible by construction**,
which is the director's R0-before-decals ordering, now visible in a frame
rather than argued from references.

Two smaller readings from the same frame, recorded so they are not
re-derived: the overcast dome has real cloud structure and reads well, so the
sky is not the weak half; and the wet patches are plainly darker than the dry
road, which is the same wet/dry split that made `day1_noon` look acceptable
for weeks.

## 5. The bar that still stands

**No lever moves on this reading.** Rule 2: one run is not a series. The
aperture moves ONCE, off a printed post-fix series, and that ruling is
unchanged. What this landing buys is that the argument is now about a number
with a denominator instead of about a JPEG.
