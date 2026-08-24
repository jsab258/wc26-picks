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
1. **`dayJob` IS DIAGNOSED: THE COURIER IS STUCK ON A DOOR I MADE SWING.**
   *(The one live gate: 10% of the last 40, 84 of 308 ever, never once
   diagnosed because it printed no reason.)* Gave it its operands, then read
   the tracer that already existed: `shiftTrace=[d13:**noaccept**/nearest:6.3m/
   **stalled:733** of ticks:1257/**on:Bldg69_door@0.2m**]`. The courier spent
   **58% of the run pressed against a door at 0.2m**, never got within 6.3m
   of the board, missed the noon accept window, so `ShiftsWorked` stayed 0.
   **Cause is mine, from today:** `MakeBox` uses `CreatePrimitive`, which
   ships a BoxCollider. Recessed 12cm into the facade it sat harmlessly
   inside the wall; the moment `DoorHost` turns the hinge, ~1m of collider
   sweeps the PAVEMENT. Removed — the wall still blocks, `DoorHost` uses
   distances not raycasts, `WinBox` set the precedent. **Judge on `dayJob`
   and `stalled` next landing.** *(Cannot explain the 84 historical reds —
   doors swung only today — so expect improvement, not a cure.)*
   *(`jobsDone=2` beside `shifts=0` is NOT a contradiction: `JobsDone` is the
   racket's drops, `ShiftsWorked` the courier's rounds. Checked.)*

1. **SIX TOOLS COMPARED A GIT ABBREVIATION TO A RUN FILENAME BY EQUALITY.**
   `%h` sizes itself to stay unambiguous; as the repo grew it went **7 -> 8**
   while run files kept 7, so every `sha in have` stopped matching — **0 of
   333 against 400 commits** — and nothing failed, because unmatched runs
   fall into a bucket sorted by SHA. Fixed at all six sites.
   **The cause was `==`, not `%h`, and my first guard could not have caught
   it:** tested against the broken state it passed identically (122 hits
   either way), because a prefix match happily compares 8 chars to 7. Replaced
   with the invariant that really broke — abbreviation width vs stem width,
   FALSE today (8 vs 7), reported as a warning since the tools prefix-match
   now. **Corrected gate picture:** one live gate, `dayJob` 10% recent vs
   27.3% lifetime, improving; all else quiet. "Five gates at 15-38%" and
   "`claims` WORSENING" **withdrawn**.

1. **TWO RUNS TRUNCATED AT EXACTLY 4 SHOTS — IT IS MY PROBE, NOT THE
   MACHINE.** Both stopped after day1_noon/dusk/night + day2_noon, and
   **exactly one Game-layer commit separates them from the last COMPLETE
   build** (`3e3cdc2`, the probe change). Same point twice = deterministic.
   **I had said the arithmetic cleared my code — that was wrong.** I counted
   operations and concluded cost; the fault is not cost. **Retract the
   suggestion that Jafar's desktop was to blame.**
   **Two faults found in that commit by reading the ordering:** the guard's
   two extra `FrameShot` calls ran AFTER the rung loop, so they measured at
   `shadowStrength` 0.55 rather than the shipped 0.93 — a wrong anchor AND
   two needless full render+ReadPixels stalls. `ShadowStrengthRungs[0]` IS
   0.93, so the anchor was already measured; both renders deleted.
   **And the structural fix: the probe is wrapped in try/catch now.** Twenty
   five shots, every gate and the whole done line were lost twice to a
   diagnostic that only describes them. `probeFailure=[...]` ships beside the
   others so a silent probe and a crashed one stay distinguishable — and a
   caught throw will NAME the fault, which is what neither truncated run
   could do. **This is containment, not a diagnosis: if it truncates again
   with `probeFailure=none`, the cause is elsewhere and the run survives to
   say so.**

1. **THE SHADOW RATIO IS 0.06 AND THE MISSING QUANTITY IS INDIRECT LIGHT.**
   With the y-flip fixed, lit holds at 0.129 across every rung — the
   invariant physics demands — so shade **0.008 -> 0.016** and the ratio
   **0.062 -> 0.124** against a 0.5 target. *(The earlier "3.4x lift" was
   measured through the y-flip; withdrawn.)*
   **Cause is architectural, checked not guessed: no indirect light exists
   here** — no lightmaps (runtime world), no realtime GI, no probes (the only
   `lightProbeUsage` sets it Off). A cast shadow gets AMBIENT ALONE:
   `lit = sun*N + ambient`, `shade = ambient`.
   **Which makes the target reachable by the lever I rejected.** Ratio 0.5
   needs ambient to EQUAL the sun's contribution — the definition of
   OVERCAST, which is what Meridian is. Lowering the KEY raises the ratio by
   lowering `lit` while `shade` cannot move. `sunSeries` looked ruinous only
   because it ran on the thirds, where the left third was a `nSun:0.00` wall.
   Both series run on the found pair now, stamped `pair/` or `thirds/`.
   **Read the pair series next: expect shade flat, lit falling.**

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

1. **PAVING BLOWOUT: LEVEL HALVED, VARIANCE BARELY MOVED.** `districtGround`
   found `glossScale:4.00` — pinned at the clamp, the code giving up. Fixed
   (uniform scalar once the wet target outruns the map; `glossDropped=5
   glossRestored=5`, both directions). **On the frame:** median 0.434 ->
   0.219, spread only 0.654 -> 0.571 vs brick 0.385. Gloss owned the LEVEL;
   texture contrast or the wet reflection owns the VARIANCE. **Next: read
   `districtGround` again, then reflection strength — do not re-tune gloss.**

1. **89 FETCHED MODELS ON DISK, SIX REFERENCED.** industrial 25, roads 47,
   suburban 13, commercial 10 = 95; six used. Unused is the density the bar
   is about — barriers, cones, four lamp variants, 47 road pieces, **25
   industrial buildings for a town whose identity is its docks**. **Next is a
   READ:** a handful through `TryInstantiateProp`, check `kitAlbedo` first.

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

1. **THE SPLAY DISTRIBUTION LANDED: median 29.3, p90 43.4, worst 120.8.**
   *(on screen, `review_day2_close`.)* Every other arm number is an angle
   from straight DOWN, so a fore/aft swing and a sideways splay read alike;
   `ArmSplayNow` projects onto the plane facing the body so only splay
   survives. The peak alone could not tell a `wave` (wired, firing) from a
   scarecrow — **the distribution can, and it says the street is fine**: a
   median of 29 degrees is an arm hanging with a walk swing, and 120 is the
   tail, not the norm. **Judge the p90 of 43 against the animation set**
   before calling it: 43 degrees at the ninth decile is a wide-ish idle, not
   a T-pose. `restArmDrop=8.0` says the bind is right either way.

1. **DECLUTTER: `namesClipped=0/83` — RAN, FOUND NOTHING, TEST SOUND.**
   `collidingNames=3` over 26 samples; three pairs still overlap after
   `PinAll` — read `namesPinnedSum` (106) vs `shotFixups` (27) before tuning.
   I suspected the edge test was blind and **read `ScreenRect` rather than
   assuming: no clamp** — it rejects only FULLY off-screen labels, so a
   partially clipped one reaches the check. Rare-event counter.

1. **FIVE OF SEVEN DISTRICTS HAD NO SHOPS AT ALL.** `the_Hook:shop73
   Copper_Row:shop4` and **zero everywhere else** — the Exchange is the
   financial district and had no commercial frontage; the Parade is the
   entertainment strip and was 37 houses and 24 flats. Shops were gated on
   `nearCore` alone and the dense cores sit in the Hook, so that flag had
   been answering "is this the Hook". Found by reading the new counter's
   OUTPUT, not the code. Two shares per district now (at a core and away
   from one); the Hook keeps 0.55 since frame-drift is calibrated on it.
   **Read `premisesByDistrict` next landing** — the mix is the judgment.

1. **THE DRESSING GATE WENT GREEN ON BUILD T** — 382 far-city pieces where it
   carried 37. **The old frame item under it is RETIRED, three regime changes
   stale** (it argued from a software rasteriser's 666ms). On the real GPU
   the frame is `game=5.6ms` of ~27.5ms, `perfOk` green, render four fifths.
   Start from the `frameCost` ladder in `## Now`.
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
