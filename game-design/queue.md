# The work stack

> **STATUS — LIVE**, verified 2026-08-21. What gets picked up next, in order.
> The plan is `roadmap.md` and it wins; this is the next few hours of it.

## Why this file exists, and how to use it

The next items are written down BEFORE a dispatch and taken from the top
afterwards, so no judgement is required at the exact point where judgement was
failing. Full account in CLAUDE.md under AUTO MODE.

- **Every item fits inside one build round trip (~28 min)**, or it gets split.
- **CI-needed items are marked** and batched into the next dispatch.
- **Take from the top; move finished items out.** `roadmap-history.md` holds
  the cut blocks and `docs-check` caps this file at 400 lines, which is what
  forces the tidy.
- **`## Standing work` never empties.** Running out of short items is a refill
  signal, not a stop signal.

---

## Now

### Where the street got to

Clips: 65 filled, 0 wrong. The street talks, argues, leans, works
counters. **The front is M17.10: the visual bar is GTA V** — item 1.

**THE PLAYTEST IS RETARGETED (22 Aug, Jafar):** *"I'll try to run it on
my windows machine after visual stuff is done. live voices/speech should
be working too."* His pipeline run came back ALL CLEAR at **1.7x real
time** on DirectML — the overhang is the SERIAL stages, not the model
(~25 tok/s both ways). Speech stage's first item: **the fp16 lever,
measured on his card** (one-click converter+timer shipped 22 Aug). The
streaming overlap exists in the backend, gated on a sustainability test
his card misses by ~15%; if his number clears ~1.0x the backend needs
Float16 binds and edge conversions (fp32-typed today).
`playtest-plan.md` has the session runbook; keep speech self-checks
green on every landing.
**THE RUNNER IS REGISTERED AND FLIPPED (22 Aug): `ledger-pc` builds
on his machine**; account in `roadmap-history.md`. **ALL 72 GATES
GREEN and holding.** ~17.6 min/round on his GPU vs cloud 33-41 over
11 rounds; the BUILD is no longer the bottleneck, the dispatch
cadence is. Closed 23 Aug: hair, furniture, clip sheet, dayJob and
beats (both onto StreetMap.Route), shopfront joinery.

**PERFORMANCE IS MEASURED; THREE GUESSES DIED.** `frameCost` ladder:
all:22.4 noShadow:17.3 noPixLights:18.0 noBodies:23.3. **Shadows 5.1ms
and per-pixel lights 4.4ms hold the frame; the crowd is not in the
bill.** Dead: draw calls, vertex budget, shadow reach. Only the rungs'
DIFFERENCES are a frame time.

**THE STREET WAS NEVER AS EMPTY AS THE PICTURES.** Three faults, all
found by measuring, all closed: the draw radius stopped at 34m (now
70); `streetBodies` counted people THROUGH WALLS (linecast now); and
the cameras stood badly (`ShotMidBlockedAt=0.30` off its own bimodal
series, 12 of 13 shots fixed; the street shot also FLED the crowd).
Day frames are NOT like-for-like across these.

**23 Aug — THE DAY NOW READS AS DAY**, and it was a MEASUREMENT not
taste: a midday only a quarter brighter than a midnight. `Exposure`
had been revised SIX times off single frames; `exposureCurve` printed
the response instead, so the aperture was shown to be the lever. Day
arm 0.72 -> 2.44 lands noons 0.30-0.41, nights untouched, noon:night
1.25 -> **2.35:1**. **Two things would have eaten it silently: the
Clamp ceiling (1.85 against a noon of 1.72 — now 3.6) and the rain
term.** Three break fixtures re-anchored.

**SILLS ARE IN AND FREE** (2133, no collider; +2173 renderers with
render+rest UNCHANGED). Weathering went into the TEXTURE. **Ground
roughness maps bound, normalised by each map's own mean** — and that
binding silently killed THREE `_Glossiness` writers, see below.

**THE CROWD BEHAVES.** Density arrived as 13 people in convoy down the
CARRIAGEWAY: `Steer`'s first branch tested only for SOLID blockers, so
tarmac stopped nobody and every pavement rule below it was
unreachable. Guard on how far a line RUNS ON road (12m): headingIntoRoad
13 -> 5, crowdTightest 0.04 -> 0.23; its sampling cost 1.9ms until
coarsened 0.5m -> 1.5m. The frame then showed 1-2 people — correct
behaviour, fewer visible. DO NOT chase this by loosening the guard;
the lever is where ROUTES go. **meanFrame ~28.4ms with a ~1ms NOISE
FLOOR** (a comment-only build moved it 0.9ms), so single-run diffs
under 1ms mean nothing. `places` went red once and recovered untouched
(3/289 flaky). Revert `runs-on` if he bows out.
**BEFORE THE PLAYTEST, THE FULL ULTRACODE AUDIT** (Jafar, 22 Aug:
"a full ultracode audit before playtesting is a good idea"). Multi-agent
sweep of the whole codebase against every rule in CLAUDE.md, triaged into
the queue before he downloads the build. Pre-approved, token-heavy by design.

### Startable right now — JAFAR'S SEQUENCE (22 Aug, his words):
### "1. visual, 2. voices/speech, 3. playtest, then feedback/fixes and
### then continue w roadmap." Within a stage, order by what shows on
### screen. Nothing from a later stage starts while an earlier one has
### startable work, except reading a landed verdict, which is free.

1. **M17.10 — THE VISUAL BAR IS GTA V (PS3). Jafar's order, 21 Aug, twice.**
   *(the most on-screen thing there is)* Plan in `roadmap.md` 17.10,
   decomposition and research in `visual-bar-spec.md`. The look is carried by
   surface history, density, depth, light, atmosphere — in that order; his
   overcast reference frame proves dirt+depth+density carry a frame with no
   interesting light.

   **LANDED (accounts in `roadmap-history.md`):** V0+V1 whole; build D's kit
   furniture, yellows, chimney pots, aerials, reactions; **V1.5 LINEAR
   CLOSED**. Open from those passes: the sky dome (V6).

   **FOUR SKY HDRIs ARE FETCHED AND WIRED TO NOTHING** (24 Aug).
   `ledger/Assets/Sky/polyhaven/` holds 23MB of 2k captures, banked and
   attributed, and `grep` finds ZERO Game-layer references. Built and not
   running, on the one element in every outdoor frame.

   **DECIDED 24 Aug, ON EVIDENCE: THE REFLECTION/ENVIRONMENT SOURCE ONLY,
   VISIBLE DOME UNTOUCHED.** The numbers make the pick, not a preference.
   **Glass is smoothness 0.90 and Window 0.85** (`SurfaceSpec`), on every
   facade in town — already highly reflective. What they reflect is a **64px
   cubemap baked off a three-colour gradient**, no structure at all. The
   near-black windows in every landed frame are dark BECAUSE there is
   nothing to reflect, not because they were authored dark: that is the
   largest reflective area in the game sitting on an empty environment. The
   blend shape trades a CONTINUOUS day (dusk warmth, night sodium, a per-day
   deck the ambient reads from) for photographic detail and pops between
   four fixed states; reflection-only is additive and cannot regress it.
   **Obstacles, both real:** (a) `Resources.Load` cannot reach `Assets/Sky`
   and `LoadImage` does not read `.hdr`, so the captures must MOVE under
   `Assets/Resources`, which moves the directory `attribution-check.py` maps
   to Poly Haven; (b) there is no NIGHT capture, so night keeps the
   procedural cubemap and the handover needs a ramp.

   **Ship the measurement with it:** the environment cubemap's own luma
   spread, before and after — a flat gradient and a real sky differ by an
   order of magnitude there, and that is the number that says the wire took.


   **LINEAR MPB CLASS-FAULT UNDER TEST:** MPB colours skip
   gamma-to-linear, so display-authored tints weakened at the flip. BODY
   WASH fixed first; 13 other MPB sites wait on the verdict, which was
   itself blocked by its own instrument until 23 Aug (the palest-part table
   named BlobShadow — a multiply quad sampling the pavement — four runs
   running; attribution skips Hidden/ shaders now). Real remainder: feet and
   shoes at 224-234, both tiers. **And a SECOND MPB fault is now open
   beside it:** `_Color` set through a property block on a shader that has
   no `_Color` is a silent no-op — see the kit-paint items below.

   **V6 FIRST SLICE LANDED** (dusk warmth, sun glow, sodium deck). Open
   from V6: the dome's cloud structure per time of day.
1. **THE BLACK NOON WALL: THE FILL IS CAPPED, AND A CoreTest SAID SO.**
   `ambientSeries` measured shade|lit at six fill multipliers: `x1.0
   0.102|0.408 = 0.25 / x1.5 0.35 / **x2.0 0.235|0.475 = 0.50** / x2.5 0.63
   / x3.0 0.75 / x4.0 0.89`. x2.0 lands the ~0.5 the GTA noons show, so
   `AmbientDayShare` was set to 1.50 — **and the day-fill test went red on
   the spot**: "the day FILL is dimmer than the dome it derives from — a sky
   can be bright without every shaded wall being bright". That is a physical
   claim and it is right; `AmbientOf` returns `dome * share`, so any share
   at or above 1.0 asserts a wall seeing PART of the hemisphere gets what
   the WHOLE sky emits. Reverted to 0.75.
   **So the ratio is not the fill's to fix alone — that is the finding.**
   The fill tops out below share 1.0, about x1.33 of today, which the series
   puts near 0.32: a real gain, not the target. **A ratio has a numerator.**
   `sunSeries` measures the key DOWNWARD (x1.00/0.85/0.70/0.55/0.40) with
   the same shade|lit pairs, because an overcast British port is exactly
   where a low sun-to-sky ratio belongs — it is what overcast MEANS — and
   that variable has never been measured. **Set the pair together when it
   lands**, and expect the answer to be mostly key, not fill.
   **Both builds photographed different walls**, said out loud: the earlier
   one `mat_concrete_b nSun:0.00` (ambient-only, `shadowOff` moving nothing,
   0.039), this one `mat_brick_grey_b nSun:0.62` with `shadowOff` TRIPLING
   the third (0.102 -> 0.310) — a sunlit wall in a cast shadow. The ratio
   target is about cast shadows, so it belongs to the second.

1. **THE STILLS NO LONGER PHOTOGRAPH WALLS.** *(rule 12; step-back and
   depth series landed — account in `roadmap-history.md`.)* `farFrac`
   (7-20m) is added for the case that passes both existing bands. **And the
   black-wall frame ACQUITTED this metric:** that wall sat at `d:6.8`,
   inside the mid band and under its bound, and it was DARK rather than
   badly framed — do not tighten the bound to chase it.

1. **RAIN: DIRECTION FIXED; COVERAGE OPEN; AND IT RAINS ON A DAY THE DOC
   CALLS DRY.** A Box shape emits along the shape's FORWARD and nothing
   rotated the emitter, so rain was thrown SIDEWAYS at 26m/s. `rainLowest`
   went from a STRUCTURAL floor of **+5.7m** to **-28.5m**. The item had
   been closed on "wet frames read as streaks in lamp cones". They do. The
   lamp cones are above the lamps.
   **Coverage NOT fixed:** mid-left 0.26% -> 1.10%, mid-centre 1.38%, but
   top-right 0.00% and bottom-left 0.03% — the 38m box, the 12m forward
   offset, the 1.1s life.
   **AND `review_day1_noon` NOW HAS RAIN IN IT** while this file says days
   1-2 are dry on every run. Nothing committed could settle that: there is
   no `rain` key in the verdict and `rainBelow` is a last-wins sample.
   Likeliest: it always rained and the sideways emitter put it out of shot —
   a hypothesis, written as one. `frames.tsv` carries `rain` and `wet` PER
   SHOT now, because a dark frame and a wet one are different findings.

1. **THE BODY BUDGET IS CLOSED AT 87.8%** — account in `roadmap-history.md`.
   The 34m draw radius was the binding constraint (now 70m) and `RealBodyCap`
   got its PC measurement: the drawn crowd costs ~1.1ms, so 12 -> 28. Hair
   CLOSED. Still live: the centre-third foot reading (FootMesh 234,
   Ch38_Shoes 224); the white pills remain unidentified with NO COMMITTED
   STILL holding one, so the next step is a measurement that fires WHILE one
   is on screen.

1. **STAGE 2 (SPEECH): THE LIVE ROUTE HAS NEVER ONCE RUN, IN 301 BUILDS —
   AND THE REASON IS NOW A VERDICT LINE.** *(the stage itself is not
   started; stage 1 has startable work. This part is rule 12, which
   outranks the ordering: a blocked channel is the highest-leverage bug.)*
   `gates.py --constant` finds twelve speech keys never anything but zero.
   The router accounts for every ask (`Asked` is DERIVED): `speechAsked=205
   speechBanked=176 speechLive=0 speechNoModel=29`, with
   `speechStepsPerSec=unmeasured` separating "a slow card" from "never ran".
   **What none of it could say is WHY**, because the `Fetch the speech
   runtime` step is `continue-on-error` and its failure was one echo into a
   job log this environment cannot tail — so "the fetch 404s", "the runtime
   loaded but no voice model shipped" and "off by design" were
   indistinguishable, with different next actions. The step tees its outcome
   now and `sim-shots-commit.sh` emits `speechRuntime=[...]`, OUTSIDE the
   player.log branch so a build that dies before the sim still answers it.
   **Read it next landing; it decides what the speech stage opens with.**
   **Why it matters:** as things stand the playtest would be the FIRST time
   that path has ever run in a built game.

1. **BUS AND BICYCLE LANDED** (seven kinds, zero fallbacks since P). Open:
   the RIDERLESS bike — if it reads wrong, rider or parked-only.

1. **PATROL DENSITY FOLLOWS THE INQUIRY — whether it READS is unfinished.**
   Links fire (`roadmap-history.md`). Open: `patrolOnBeatMean=0.00` over 3
   shots vs `0.18` over 17 — zero of three separates nothing; judge the
   `hunt_` pair. A PARKED beacon reads where six crossings do not.

1. **THE DISTANT SKYLINE — CLOSED FROM A DOC, AND THE CAUSE IS THE REPAINT
   ITEM.** The far tower is the most saturated thing in `district_downtown`
   (**0.469** vs brick 0.324, sky 0.222); fog cannot account for it, since
   `fogRGB` sits near 0.196 and a fogged object cannot be MORE saturated
   than the fog. `SkylineHaze` is a good desaturated grey-blue (sat 0.15)
   and `skylineRepainted=23` says it applied — **a multiply cannot
   desaturate**, so the kit's hue survived. Same fix: grey the atlas.
   **Fixed on the way:** `SkylineRepainted` incremented the moment the kit
   existed, BEFORE the paint was attempted. It counts acceptances now.

1. **THE PAVING BLOWOUT: DIAGNOSED FIRST TIME BY ITS PROBE, AND FIXED.**
   `districtGround` came back **`mat_asphalt ... glossScale:4.00`** — pinned
   at its clamp, which is not a scale but the code giving up. The wet target
   wants a near-mirror and `asphalt_r` is a rough-asphalt map whose mean is
   a quarter of it, so multiplying by 4 does not raise the surface to the
   target, it multiplies its **variance** by four — a p10-p90 luma spread of
   0.654 against 0.141 for the road beside it.
   **A wet surface's smoothness is the WATER, not the stone** — a film of
   water is uniform, which is what makes it a mirror — so past the point
   where the map cannot carry the target, `SetSmoothness` sets it aside for
   the uniform scalar. Dry keeps the map. The threshold is not invented: it
   is exactly where the old code began to clamp, i.e. where it started
   lying. Restored when the target comes back in reach, or a street that
   dried would stay uniform for ever (a ratchet). Read
   `glossDropped`/`glossRestored` — one count cannot tell "wet" from "never
   dried again".

1. **EIGHTY-NINE FETCHED MODELS ARE ON DISK AND UNUSED, AND 25 OF THEM ARE
   INDUSTRIAL BUILDINGS FOR A PORT TOWN.** *(rule 6 aimed at art, and the
   standing order: best AVAILABLE result, not the first working one.)*
   Counted 24 Aug: `city-kit-industrial` 25 models, `city-kit-roads` 47,
   `city-kit-suburban` 13, `city-kit-commercial` 10 — **95 on disk, six
   referenced**: two awnings, `city_kit_roads_light_curved` for the lamp
   posts, and three `low-detail-building-*` for the skyline.
   **What is sitting unused is exactly the density the GTA-V bar is about:**
   construction barriers, cones and lights; `light-square`,
   `light-*-double`, `light-*-cross` lamp variants beside the one curved
   lamp the whole town wears; 47 road pieces; and 25 industrial buildings
   for a town whose identity is its docks. Nothing to fetch, nothing to buy.
   **Next step is a read, not a build:** open a handful in the sim's own
   pipeline (`TryInstantiateProp` + `kitAlbedo`) and see whether they arrive
   at a usable albedo, because the twelve `base_mesh_*` families at 1.00
   above say a fetched model is not automatically a usable one.
   *(And I first reported these as ENTIRELY unused, which was wrong: the
   code uses underscored keys — `city_kit_roads_light_curved` — so a
   hyphenated grep found nothing and I concluded from its absence. Rule 1:
   one spelling searched is not a search.)*

1. **TWELVE PROP FAMILIES SIT AT ALBEDO 1.00 AGAINST A TOWN AT 0.15.** The
   `kitAlbedo` measurement landed and nobody had read it: swing bin, oil
   barrel, skip, park bench, finger post, garden bench, two crates, pallet,
   three bins — **all exactly 1.00** against `townWallAlbedo=0.15`, 6.7x the
   walls on objects down every street. **But 1.00 was also the instrument's
   silence:** `MeanTexLuma` returns 1.0 for a null texture and
   `PropAlbedoUnread` cannot see it, because a missing texture is an early
   return rather than an exception — so "a white bin" and "a bin with no
   albedo map" printed identically and want different fixes.
   `kitAlbedoNoTex` splits them. **Read it before touching the twelve.**

1. **THE REPAINTS ALL APPLY AND CANNOT DO THE JOB — A MULTIPLY CANNOT
   DESATURATE. FIX SHIPPED; JUDGE ON THE LANDING.** My glTFast theory is
   REFUTED by its own probe: **`kitPaint=1997/0`, refused by `[none]`**,
   `skylineRepainted=23`. The paint lands everywhere and the objects are
   still wrong. **Measured on the atlases:** multiplying by
   `SkylineHaze(0.34,0.36,0.40)` moves top-decile saturation **0.820 ->
   0.788** (`car-kit`) and **0.733 -> 0.686** (`city-kit-commercial`) —
   four to six per cent, because a multiply preserves channel ratios.
   `PatrolWhite`'s comment says so outright: a virtue there, the problem
   here. **Shipped:** `GreyCopy` greys each atlas once, luma-weighted so the
   modelling and slate stripe survive, as a cached VARIANT — atlases are
   shared with props we deliberately do not repaint. Colour space
   round-tripped, not converted. **Read `kitGrey=atlases/failed/renderers`;**
   zero greyed beside non-zero `kitPaint` is the swap not running. **Do NOT
   chase this with darker paints** — the saturation is the author's.

1. **THE DECLUTTER: NAMEPLATES AND BUBBLES, MEASURED, OPEN.** *(on screen)*
   `collidingNames=3` over 26 samples — five labels at the peak, 3 of their
   10 pairs overlapping. `PinAll` runs at shot time and three still overlap:
   read `namesPinnedSum` (106) against `shotFixups` (27) before tuning;
   `bubblesLiftedSum=1` says the de-overlap moved a bubble once in a run.
   The bubble median mixed two samplers (71 tick vs 26 shot) and is split
   now — **I read a 0.33 -> 0.00 move as the fix working** when what moved
   was the street.
   **AND THE FRAME EDGE IS A COLLIDER TOO, which this vocabulary did not
   have.** `review_day2_wet` renders "Ellis" cut in half by the bottom-right
   corner — found by opening the still, which is where five of this
   project's faults have come from and none from a gate.
   `namesClipped=n/tested` with `namesClipWorst` (overhang as a fraction of
   the label's OWN width, because "12 pixels off" means nothing without
   knowing whether the label is 20 or 200 wide) lands next build.
   **MEASURED, NOT FIXED, deliberately:** sliding a label inward detaches a
   nameplate from the person it names, which is a worse lie than a clipped
   one; hiding it is the other repair, and a name you cannot read may not be
   serving anybody. Which is right depends on how OFTEN and by how much, and
   neither number existed. Rule 2 — print the series, then choose.

1. **FIVE OF SEVEN DISTRICTS HAD NO SHOPS AT ALL.** `the_Hook:shop73
   Copper_Row:shop4` and **zero everywhere else** — the Exchange is the
   financial district and had no commercial frontage; the Parade is the
   entertainment strip and was 37 houses and 24 flats. Shops were gated on
   `nearCore` alone and the dense cores sit in the Hook, so that flag had
   been answering "is this the Hook". Found by reading the new counter's
   OUTPUT, not the code. Two shares per district now (at a core and away
   from one); the Hook keeps 0.55 since frame-drift is calibrated on it.
   **Read `premisesByDistrict` next landing** — the mix is the judgment.

1. **THE DRESSING GATE WENT GREEN ON BUILD T** — the far city carries 382
   pieces where it carried 37. **The old frame item under it is RETIRED: it
   was three regime changes stale**, arguing from a software rasteriser's
   666ms. On the real GPU the frame is `game=5.6ms` of ~27.5ms with `perfOk`
   green, and the render is four fifths of it. Anything here starts from the
   `frameCost` ladder in `## Now`, not from those numbers.

1. ~~**The session-hook guarantee** (M22)~~ — **BUILT AND HOLDING.** What is
   open is the READING, not the tiers — see `## Now`.
2. ~~**Romance** (M18)~~ — **PROMOTED TO M18.5, 18 Aug by Jafar.**
3. ~~**Smuggling** (M21)~~ — **BUILT 21 Aug night** on the `Racket`
   substrate: cargo rhythm, Tibor signs, manifests feed the audit's heat,
   sim stages it, six CoreTests. Remainders: a player verb to recruit the
   signer; gambling waits behind it. Read `cargoes`/`manifests` next build.
4. **The other day-job tracks** (M18) — `Core/DayJob` is the courier round,
   singular; the doc offers bar/courier/office on the first morning.
5. **Interiors beyond the pub** (M20) — every other door is a threshold.

**Reactions are LIVE and measured** (flinch/glance/wave/point/head_no
all firing; most refusals are glance cooldowns doing their job).
**greet reads 0of0 and that is the SIM'S ECONOMY, not a wire fault**:
it needs a loyal (≥0.35) need-route crew member passing the player and
the sim skims, so the condition never exists. Deliberately NOT
planted — a staged loyal runner would pollute the crew-decay gates.
The wire is proven by the five kinds sharing its path.

### The quality ladder (standing order 16 Aug: best available, not first working)

Before closing any visible item, ask: best available result, or first working
one? Take the next rung or name it here. A blank next rung is a research task.

| aspect | rung now | known next rung, free |
|---|---|---|
| textures | 2K colour+normal; roughness on walls AND ground (24 Aug, normalised so the wet calibration held: reflMax 0.89 unchanged); vertical run-off streaks in brick/plaster/concrete | AO maps; a second albedo variant per surface |
| buildings | procedural terraces, photo surfaces, pots+aerials, shopfront depth (V4), painted joinery, window SILLS (24 Aug, 2133) | window REVEALS (a recess needs an opening in the mass, not a proud box); door furniture |
| doors | 376 leaves on hinges, damped-spring swing, latch + creak, DOORWAY approach not a radius; proven live (`doorSwing=376/6/6/0/1`) | a shove — `HitStop` is unreachable at the shipped damping (8.4% overshoot vs a 15% stop, two CoreTests), so the thump needs a door pushed rather than eased; then walkers using doors |
| kit props | repaint applies everywhere (`kitPaint=1997/0`) | grey each kit colormap once at load, preserving luma — a multiply cannot desaturate (0.820 -> 0.788 measured) |
| vehicles | Kenney kit + town paints | curated higher-fidelity CC0 set (Quaternius/Sketchfab), same pipeline |
| props | Kenney + Base Mesh furniture, yellows (build D) | dock clutter density read; higher-tier swaps |
| characters | Mixamo bodies, gait archetypes | Jafar's clip session; combat set is disk-only |
| lighting | REAL noon shadows + deepened AO + grade; linear closed; V6 first slice | the AMBIENT FILL — a sun-perpendicular wall reads 0.039 against a lit 0.431, and `ambientSeries` is dispatched to set it; then HDRI as the environment source |
| animation feel | walk/idles + 18 activities + 6 reactions wired | reaction states for the rigs that refuse them — X's reactWhy reads noState:339 against cooldown:97, so most asks die on a controller with no state for the slot; then smoke/thinking re-harvest; walk transitions (disk-only) |
| audio | foley, barks, procedural score | voices into build (Thu); positional street sounds |

- **M21, the two ledgers.** Empire growth, law as a tool, what expansion costs
  you. Entirely unbuilt, entirely Core, so entirely doable here without a round
  trip. This is the largest piece of unwritten game left.
- **M22, the shape of a playthrough.** Onboarding, pacing, replayability and
  succession — also unbuilt and also Core-shaped.
- **Read a system and write down what it actually does.** Every system
  here has at least one comment that is now false, and each one found is
  a bug that would otherwise have been believed. **Read the code that
  produces a number too** — three faults in `CollidingNames` came from
  reading it, not from its readings.
- **Turn a still into a number.** Five faults found by opening a frame and none
  by a gate. Anything a frame shows that no metric names is a metric worth
  adding.
- **DROPS DELIVER EVERY RUN.** Open: the d12 shape — a night the job
  never owned (`held:waypoint`, ran=0) while the skip plant says it
  stopped at day 11. Trace-first: read TraceJob's window source against
  the active-job timing before any change.
