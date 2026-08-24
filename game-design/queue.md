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
1. **THE 0.5 TARGET IS FOR CAST SHADOWS, AND HALF MY READINGS WERE NOT ONE.**
   *(This reframes the item; the levers were the wrong argument.)* The `on:`
   stamp earned itself on its first landing: both series read
   **`on:mat_concrete_b#g1`** with identical x1 rungs (0.039|0.424), so they
   are comparable — and that wall is the SUN-PERPENDICULAR one (`nSun:0.00`),
   not a shadowed one.
   **On it, `sunSeries` shade is FROZEN: 0.039 / 0.039 / 0.039 / 0.039 /
   0.035 while the lit side falls 0.424 -> 0.184.** The key contributes
   NOTHING to that wall, so dimming it cannot raise the shade — and
   `shadowStrength` cannot either, because there is no direct sun there to
   remove. On this fixture the fill is the ONLY lever and it is capped below
   share 1.0 by a CoreTest defending something true.
   **THE INSIGHT: two physically different situations were being given one
   target.** A CAST SHADOW is a sunlit surface with the sun blocked, and the
   GTA reference puts it near half the lit brightness. A wall FACING AWAY
   from the sun is sky-lit by nature and genuinely much darker — a
   north-facing wall at noon is not a bug. The probe photographs whichever
   the step-back's camera happens to face, which is why the readings swung
   26%, why the ratios differ per wall (0.25 on brick, 0.092 on concrete),
   and why the levers behaved differently in each.
   **Next: split the question by `nSun`.** Judge cast shadows against ~0.5
   with `shadowStrength` as the lever (`shadowSeries` is dispatched), and
   judge sun-perpendicular walls on their own terms with the fill. **Do not
   set one constant from a fixture that is sometimes one and sometimes the
   other.**

1. **`farFrac` CARRIES THE SIGNAL THE OTHER TWO BANDS MISS — SERIES LANDED.**
   *(rule 12; step-back and depth series in `roadmap-history.md`.)* First
   readings: `day2_wet near=0.00 mid=0.18 **far=0.73**`, `day1_noon
   0.00/0.27/**0.54**`, `day2_noon 0.00/0.33/**0.43**`. Near is 0.00 on
   every shot and mid sits inside its bound, while the 7-20m band runs
   0.43-0.73 — and `review_day2_wet` is about 80% black wall, which no
   existing metric could see. **No bound yet, on purpose (rule 2): this is
   the series the bound comes from.** Judge it over a few more landings —
   a street SHOULD have buildings at 7-20m, so the bound is not 0, and the
   question is where "framed" becomes "photographing a wall".

1. **THE BODY BUDGET IS CLOSED AT 87.8%** — account in `roadmap-history.md`.
   The 34m draw radius was the binding constraint (now 70m) and `RealBodyCap`
   got its PC measurement: the drawn crowd costs ~1.1ms, so 12 -> 28. Hair
   CLOSED. Still live: the centre-third foot reading (FootMesh 234,
   Ch38_Shoes 224); the white pills remain unidentified with NO COMMITTED
   STILL holding one, so the next step is a measurement that fires WHILE one
   is on screen.

1. **THE INQUIRY RUNS NOW; TWO THINGS GATED ON IT STILL DO NOT.** *(moat:
   information. Not started — stage 1 has startable work.)* CLAUDE.md said
   the detective "has never once opened an investigation in the entire
   recorded history of this project"; read 24 Aug, **`inquiry=Manhunt`**.
   Corrected in place, because that sentence would send the next session at
   work already running. **Still zero and now better specified:**
   `summonsTaken=0` and `redirectRelief=0.00` WHILE the inquiry reaches
   Manhunt — so the documented phone-line cause for `summonsTaken` stands
   and the inquiry cause does not; the two had been read as one.
   *(`findingKinds=none` is NOT part of this — it is `SceneAudit`'s, where
   `clean=True findings=0` is a fault counter working. Checked after
   guessing otherwise.)*

1. **STAGE 2 (SPEECH): THE RUNTIME WAS NEVER THE PROBLEM — IT IS THE MODEL.**
   *(not started; stage 1 has startable work. The rule-12 half is DONE.)*
   The channel answered on its first run: **`speechRuntime=[Microsoft.AI.
   DirectML 1.15.2: DirectML.dll (17.7 MB); speech runtime: 3 file(s),
   LEDGER_ONNX defined in ledger/Assets/csc.rsp; RUNTIME_OK]`**. The fetch
   works, the DLLs land, the define is set. So `speechLive=0` with
   `speechNoModel=29` across 301 builds is **the voice MODEL not being in
   the build**, not a broken runtime — which is exactly the distinction that
   line was added to make, and it made it immediately.
   **So the stage opens with the model, not the runtime.** Find what
   `OnnxSpeech` loads and whether anything stages it into the Windows build
   the way `voices-into-build` stages the banked clips. **Do not spend a
   round trip re-testing the fetch** — it is green and named.

1. **BUS AND BICYCLE LANDED** (seven kinds, zero fallbacks since P). Open:
   the RIDERLESS bike — if it reads wrong, rider or parked-only.

1. **PATROL DENSITY FOLLOWS THE INQUIRY — whether it READS is unfinished.**
   Links fire (`roadmap-history.md`). Open: `patrolOnBeatMean=0.00` over 3
   shots vs `0.18` over 17 — zero of three separates nothing; judge the
   `hunt_` pair. A PARKED beacon reads where six crossings do not.

1. **THE DISTANT SKYLINE: GREYING HELPED, DID NOT CLOSE IT.** The tower was
   the most saturated thing in `district_downtown` at **0.469**; after the
   atlas grey it reads **0.394** — a 16% cut, and still above the brick
   beside it at 0.324. `SkylineHaze` is sat 0.15 and a greyed texture times
   it should land near that, so something is adding saturation back: fog
   (fogRGB sits near 0.196) or the patch containing sky rather than tower.
   **Next: measure a NAMED tower via `SurfaceUnder` rather than a screen
   patch** — the same fix the light series needed, for the same reason.
   *(`SkylineRepainted` also used to increment before the paint was
   attempted, reporting success for a step it had never checked. Fixed.)*

1. **THE PAVING BLOWOUT: LEVEL HALVED, VARIANCE BARELY MOVED.** `districtGround`
   returned `mat_asphalt ... glossScale:4.00` — pinned at the clamp, the code
   giving up rather than a scale — and the fix (uniform scalar once the wet
   target outruns the map) landed with `glossDropped=5 glossRestored=5`, both
   directions, not a ratchet. **Judged on the frame, like-for-like:** the
   strip's median **0.434 -> 0.219** (from 7x the adjacent road to 3.8x) but
   its p10-p90 spread only **0.654 -> 0.571**, against brick's 0.385. So the
   gloss scale owned the LEVEL and something else owns the VARIANCE — the
   texture's own contrast, or the wet reflection layer. It is still the
   highest-variance surface in the frame. **Next: `districtGround` again on
   the landing to see what `glossScale` reads now, then the reflection
   layer's strength — do not re-tune the gloss, it did its part.**

1. **EIGHTY-NINE FETCHED MODELS ON DISK, SIX REFERENCED — 25 OF THEM
   INDUSTRIAL BUILDINGS FOR A PORT TOWN.** Counted: industrial 25, roads 47,
   suburban 13, commercial 10 = **95 on disk, six referenced** (two awnings,
   `city_kit_roads_light_curved` for every lamp in town, three skyline
   buildings). Unused is the density the bar is about: barriers, cones,
   four more lamp variants, 47 road pieces, 25 industrial buildings for a
   town whose identity is its docks. Nothing to fetch or buy. **Next step
   is a READ:** put a handful through `TryInstantiateProp` and check
   `kitAlbedo`/`kitAlbedoNoTex` first — 30 materials already carry no albedo
   map, so a fetched model is not automatically a usable one.
   *(I first said ENTIRELY unused, wrongly: the code uses underscored keys,
   so a hyphenated grep found nothing and I read the absence as an answer.)*

1. **TWELVE PROP FAMILIES AT ALBEDO 1.00 ARE UNTEXTURED — `kitAlbedoNoTex=30`
   SAYS SO.** `kitAlbedo` had them at exactly 1.00 against
   `townWallAlbedo=0.15`, and 1.00 was also the instrument's silence:
   `MeanTexLuma` returns 1.0 for a null texture and `PropAlbedoUnread`
   cannot see it, because a missing texture is an early return rather than
   an exception. The split answered it — **30 materials carry no albedo map
   at all**, so those bins, benches, crates and barrels are wearing their
   material TINT and nothing else. **The fix is the tint, not a texture
   hunt**, and it is the same shape as the skyline: a kit prop arrives in
   its author's colour and this town has to repaint it.

1. ~~**THE REPAINTS CANNOT DESATURATE**~~ — **GREY SWAP IN AND RAN.**
   `kitPaint=1997/0` refuted the glTFast theory; the atlases named the cause
   (a multiply moves top-decile saturation only 0.820 -> 0.788, preserving
   channel ratios). **`kitGrey=2/0/1974`** and the mint saloon is gone from
   `review_street`. The green bicycle left is `oga-vehicles`, which goes
   through no paint site — the variant design working, not a miss.

1. **THE ARM METRIC COULD NOT TELL A WALK FROM A SCARECROW — THE LATERAL
   HALF IS BUILT.** *(on screen, `review_day2_close`: a figure with both
   arms out to the SIDES.)* The numbers acquit the rig and could not answer
   the picture: `restArmDrop=8.0` (the bind is right, no T-pose),
   `preArmDrop=103.4` (the pre-solve posture that metric exists to expose),
   `armWidest=55.1`, `armStreet=36.6`, `armStreetWorst=52.5`.
   **The gap: all of them are the angle from STRAIGHT DOWN**, so a fore/aft
   swing and a sideways splay give the same number — a walking arm 45deg
   forward reads exactly like a scarecrow's 45deg out.
   **`ArmSplayNow` drops the forward component** (projects onto the plane
   facing the body) so only the splay survives, and
   `armSplayWorst`/`armSplaySampled` land next build — a peak with its
   denominator, because "is ANYBODY" is not a median question and every
   neighbour up there is a median or a max over medians, which is what let
   three T-poses through on 4 Aug. **Not a rig change:** `restArmDrop=8.0`
   already says the bind is right, so whatever this is belongs to the
   animation or the solve. Read the pair before touching either.

1. **THE DECLUTTER: `namesClipped=0/83` — RAN, FOUND NOTHING, AND THE TEST
   IS SOUND.** *(on screen)* `collidingNames=3` over 26 samples; `PinAll`
   runs at shot time and three pairs still overlap — read `namesPinnedSum`
   (106) against `shotFixups` (27) before tuning.
   **The edge test landed with a real denominator: 83 labels examined, zero
   clipped, `namesClipWorst=0.00`** — while an earlier `review_day2_wet`
   plainly showed "Ellis" cut in half by the corner. I suspected the test
   was blind (a clamp inside `ScreenRect` would report an off-screen label
   as inside) and **read it instead of assuming: there is no clamp.** It
   returns false only when a label is FULLY off-screen, which is right —
   fully off-screen is absent, not clipped — and a partially clipped one
   reaches the edge check intact. So the zero is honest and this run's
   vantages simply had no clipped label. **Leave it for a few landings; it
   is a rare-event counter and one frame is not a rate.**

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
