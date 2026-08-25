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

**Closed 23 Aug and moved to `roadmap-history.md`:** the day/night
exposure fix (aperture was the lever, noon:night 1.25 -> **2.35:1**;
the Clamp ceiling and the rain term would each have eaten it silently
— both still live, do not re-raise without reading the history entry),
and the sills + ground roughness binding. Full accounts there.

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

1. **CLAUDE.md's `director_cadence` PARAGRAPH IS NOW FALSE — NEXT DIRECTOR
   SPAWN.** It says "Two candidate fixes, neither built". **The stronger one
   is built and live**: the gate now requires a decision RECORD in
   `game-design/decision-*.md` closing with `<!--RULING spawn=STAMP-->`,
   the stamp quoted verbatim from the log row. Both outcomes were watched on
   real data tonight — it REFUSED the director's own unstamped ruling ("a
   spawn row is attendance, not a review") and went `REVIEWED` once stamped.
   Selftest 38 -> 53 fixtures, and the refusal message now tells you to
   RESUME a killed director rather than restart one. Touching CLAUDE.md is a
   mandatory director trigger, so this waits for the next spawn rather than
   being edited here — but it must not wait long: a rules file that describes
   a hole as open when it is closed sends the next session to build it twice.

1. **DIRECTOR RULED THE DRESSING BATCH, 25 Aug — `decision-dressing-batch.md`.**
   **A: commit now, commit is not dispatch.** Re-DISPATCH stays barred until
   the hang fix AND the parser-breaking audit fixes land — the first build
   back is the run everyone reads. **B: the welded diamond REJECTS** (a US
   diamond on a post is the loudest wrong-country tell there is; the premise
   outranks a free asset). The rolled plate is honest **iff** no US livery
   survives the 45° roll — **confirm off the first still, not off the
   apex-midpoint number.** **C: signage is a named gap, and it queues HIGH** —
   street nameplates first: named streets whose names cannot be read is the
   information moat with a hole in it. **D: closes as first-working, with two
   that do NOT close** — `kitAlbedo`'s cap is a silently-biting instrument
   fault, not a rung, so it rides the audit-fix commit; and the duplicated
   TextMesh idiom is signage's FIRST task, because building signage otherwise
   mints a third private copy. Onto the ladder by name: the pub-sign board
   (the kit ships a mast arm with no plate) and a British terrace — the
   terrace's next rung is blank, so it is a RESEARCH task, not a fetch.
   **E: bank the `walk_start` re-pick and attach it to the image-gen
   delivery** — one interruption, two one-click items.

1. **AFTER THE SKYLINE/APRON LANDS — three follow-ups, and they are here
   because a LOG that supersedes itself is not a queue.** (i) **`skylineFit`
   is SERIES-FIRST**: one slot number (95.1m) now replaces the
   radius-dependent arc, so the 1.76 measured under the old divisor is NOT
   comparable — nobody quotes a fit until the new series lands. (ii)
   **`groundMask*` and `farFrac` RE-BASELINE**: the apron is a REGIME CHANGE
   in those series (ground/sky boundary rises +22px in hook, +73px in
   copper), so they carry the schema mark when it lands and cross-run
   comparisons across the boundary are void. (iii) **Supersede
   `agent-reports/skyline-period.md`** once the four skyline keys land — its
   own header instructs it. **Not closed until `skylineByEdge` reads k/k on
   every edge in a landed verdict and the stills are read.**

1. **CHEAP CI GREEN — 311 reds, one cause.** Account in `roadmap-history.md`.
   **OPEN:** the Windows/mac Verdict steps report the SIM, so "lint failed"
   and "the sim did not run" read alike.

1. **REJECTING FIXTURES REPINNED — ALL THREE DONE 25 Aug.**
   `lint-conditional-reach` now builds a synthetic ladder in a temp dir and
   carries a WRITE SENTRY that refuses any write under `ledger/`. Its
   denominator is a finding: **one** conditional type over 88 Game files.

1. **NOTE: `06f51f39`'s message says the comment sweep is incomplete —
   FALSE; it finished and landed in that same commit.** Do not re-brief it.
   Asserted from a builder's last STREAMED line rather than the disk. **This
   keeps happening: on 25 Aug three more agents' last lines read as
   unfinished ("Now the documents", "I'll start by reading") when two had
   finished and one had written nothing. A streamed line is a comment about
   the work, not the work — check the disk, every time.**

1. **THE DRY TOUR LANDED; ALBEDO IS RULED OUT.** Every `district_*` row
   before the day-5 move is incomparable. `GroundGrade` does NOT move
   again — the lever is the light-to-JPEG path. Ruling:
   `decision-ground-albedo.md`.
1. **THE TWO UNREACHED KITS: SURVEY DONE, WIRING IN FLIGHT (25 Aug).**
   Plan is `agent-reports/kit-survey.md` — 19 PLACE / 6 HOLD / 33 REJECT,
   every verdict carrying measured metres, a site and a count, and the
   rejects carrying COUNTRY grounds (the octagon, the mast-arm signal, the
   horizontal head, the low front-yard fence are all American forms). Both
   kits are CC0 and already attributed: **nothing to fetch, nothing to
   buy.** Three builders are wiring it now, on non-overlapping files —
   `Core/KitDressing.cs` (tally + formatter, where the tests run), the six
   lamp forms + Britain's missing secondary signal head in `WorldBuilder`
   and `TrafficHost`, and roadworks/signs/planters/yard-fences in a new
   `Game/StreetDressing.cs`. **Not closed until a landed verdict shows the
   `KitDressing` done-line fragment with non-zero placements AND the stills
   are read** — every one of these sites falls through to a fallback
   primitive on a miss, silently, which is how `city_kit_*_bench` missed
   for a week. Two verifications ordered by the survey and still open: the
   warning triangle must point UP (down is a US yield sign, and bounds
   cannot tell them apart), and the hanging plates letter through
   `ShopNamesPainted` or render BLANK, which reads as a fault in frame.
   The DENSITY half of the GTA V bar: what palms and hydrants do for Los
   Santos, chimney pots and dock clutter must do for Meridian.

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
1. **THE 7/7 DISTRICT DARKENING: BASELINE VOIDED BY THE DRY TOUR, DO NOT
   BISECT ACROSS IT.** All seven districts had moved -0.0005 to -0.0050 and
   `day1_noon` -0.0065 in one direction, with `shadowStrength` moving the
   WRONG way (0.93 -> 0.85 lightens), so the cause was something else in the
   batch and the plan was to re-read then bisect. **That plan is dead as
   written:** item 1 moves the tour from day 3 to day 5, so the pre-change
   pinned rows are a different regime and a bisect spanning the break would
   be reading weather as a code change. Restart the baseline from the first
   dry landing. (`frame-drift` labels every row, `ref-bench` marks pose-stable
   stills `*`; account in `roadmap-history.md`.) It did show the instrument
   working: a consistent 0.003 across seven independent shots is a thing the
   street frames could never have shown.
1. **EIGHTEEN GATES CANNOT NAME THEIR OWN FAILURE — RATCHETED AT 18 by
   `tools/gate-detail.py` in `verify`** (account in `roadmap-history.md`).
   Fix each bare gate's operands as it goes red, not en masse.

1. ~~**SIX TOOLS COMPARED A GIT ABBREVIATION TO A RUN FILENAME BY
   EQUALITY**~~ — **FIXED at all six sites** (account in
   `roadmap-history.md`). `verify` warns that the abbreviation is 8 chars and
   run stems are 7, so compare by PREFIX and never by equality.
1. **THE SIM HUNG BEFORE THE DAY-1 BEAT ON `e8c5949` — DISPATCHING IS
   BARRED UNTIL IT IS FIXED.** Measured: healthy runs reach `dayMark day=1`
   at ~20s, frame ~306, **5 of 5**; this one reached **zero** beats in
   1440s. So the old wording of this item ("the sim overruns its 24-min
   kill, `hangTail` fired and was useless") had the symptom and not the
   shape — it is not an overrun of a long run, it is a stop before the first
   beat. The build ran, wrote a verdict, and produced **no done line, no
   gates, no stills**; the staging guard correctly refused to restage the
   previous run's pictures under this commit's name, so the JPEGs on the
   branch are NOT evidence about it. Ten new `OnAnimatorIK` warnings against
   **THE IK LEAD IS DEAD AND IT WAS MINE. I wrote here: "Ten new
   `OnAnimatorIK` warnings against 0 in each of the five previous runs."
   FALSE.** `tools/sim-shots-commit.sh:227` gates the whole raw tail behind
   `if ! grep -q "SimDirector: done."`, so a healthy run CANNOT report the
   warning — the field is absent, not zero. Counted over every kept run:
   352 total, 3 with no done line, 3 carrying a raw tail at all, and **the
   warning is in 3 of those 3.** It is what the tail always shows. I compared
   a printed field against an ABSENT one and called it a regime break — a
   zero with no denominator, quoted rather than deleted because it was
   plausible and cost a builder real budget to refute. Nor was
   `CharacterRig.cs:435` ever silent: `StampAvatar()` runs every LateUpdate
   for every humanoid rig and Unity throttles the warning. **A guard there
   would have spent a round trip on a non-fault.**
   **Two live candidates, and the bisect is TWO wide, not one:** 14 commits
   went out unbuilt since the last good run and exactly two touch
   `ledger/Assets` — `677beb64` and `e72f58a3`. Candidate B is simply an
   intermittent, and it is not ruled out. The stall is localised between the
   first rendered frame and in-game noon day 1, which excludes the whole
   expensive night-gated half (`MeasureAo`, `MeasureWindowGlow`,
   `MeasureCrowdCost` never ran).
   **DIAGNOSED (`agent-reports/sim-hang-e8c5949.md`): STALLED, not crashed
   and not slow.** The heartbeat already existed and answered it — healthy
   runs beat at 19-20s/frame ~306, ten a run; this one emitted ZERO in 1440s,
   and a merely-2x-slow runner still gets five. Over all 352 kept runs, 7 ran
   with no done line by the elapsed-time reading, 3 by a content grep — rare
   either way, and NOT a one-off. The build step already
   computes `$timedOut` and `$p.ExitCode` and throws both away, so "killed at
   24 min" and "crashed" arrive identical — being fixed. **Two measurement
   faults `e72f58a3` introduced, neither the hang:** `ArchetypeRead` /
   `ControllerRead` / `TrouserRead` are last-wins strings OUTSIDE the
   save/restore set, so they describe whichever walker attached last while
   sitting beside player readings (the `namesTracked=2` fault again); and
   `bodyTinted` / `bodyWash*` change POPULATION at this commit (every
   textured renderer -> cloth only), which the commit message declares but
   the verdict does not, so the next series-reader sees an unexplained fall.

1. **BODY BUDGET CLOSED AT 87.8%** (account in `roadmap-history.md`). Live:
   the centre-third foot reading, and white pills with no committed still.

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


1. **PATROL DENSITY FOLLOWS THE INQUIRY — whether it READS is unfinished.**
   Open: `patrolOnBeatMean=0.00` over 3 shots vs `0.18` over 17 — zero of
   three separates nothing. A PARKED beacon reads where six crossings do not.

1. **THE DISTANT SKYLINE — EVERY OLD READING IS VOID (25 Aug).** The twelve
   glass towers it measured were retired as a premise violation; 21 period
   blocks replace them. **The METHOD transfers:** measure a NAMED object via
   `SurfaceUnder`, never a screen patch — a patch cannot say whether it
   caught tower or the sky beside it. Re-take once the blocks land.

1. **THE FETCHED MODELS HAVE A REACH LEDGER: `tools/prop-reach.py`, in
   `verify`.** 213 models on disk; **73 named as of the dressing batch**, up
   from 62 — `city-kit-suburban` is no longer an ENTIRE KIT UNREACHED. Per
   kit, because one number cannot carry both questions.
   **Still open, biggest first:** the rest of `city-kit-roads` (signage is
   the named gap — director ruled it queues HIGH);
   `city-kit-industrial_detail-tank`, 84.8 x 41.5 x 51.5, a squat dock tank
   needing a ground placement site rather than a skyline slot; car-kit 39
   unused, base-mesh 23, oga-vehicles 23.
   **MEASURE WITH `prop-dimensions` BEFORE PLACING ANY OF THEM.** Those
   numbers overturned the obvious plan for the industrial band: commercial
   skyline models are slim towers (50x200), industrial ones squat masses
   (208x147), so reusing the tower height target would have built one wall of
   interpenetrating geometry no still could diagnose. **And bounds are not
   enough on their own** — the survey called two models triangles from their
   bounds and the OUTLINE proved them US diamonds.



1. **Smuggling** (M21) — **BUILT** (account in `roadmap-history.md`).
   Remainders: a player verb to recruit the signer, and gambling behind it.
   Read `cargoes`/`manifests` next build.
2. **The other day-job tracks** (M18) — `Core/DayJob` is the courier round,
   singular; the doc offers bar/courier/office on the first morning.
3. **Interiors beyond the pub** (M20) — every other door is a threshold.

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
- **Read a system and write down what it actually does.** Every system here
  has at least one comment now false, and each one found is a bug that would
  otherwise have been believed. **Read the code that produces a number too**
  — three faults in `CollidingNames` came from reading it, not its readings.
- **Turn a still into a number.** Five faults found by opening a frame and none
  by a gate. Anything a frame shows that no metric names is a metric worth
  adding.
- **DROPS DELIVER EVERY RUN.** Open: the d12 shape — a night the job
  never owned (`held:waypoint`, ran=0) while the skip plant says it
  stopped at day 11. Trace-first: read TraceJob's window source against
  the active-job timing before any change.
