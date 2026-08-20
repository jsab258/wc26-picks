# The work stack

> **STATUS — LIVE**, verified 2026-08-15. What gets picked up next, in order.
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

The Mixamo harvest landed complete — 67 clips — and the street came alive with
it: people talk, argue, lean, smoke, work counters, carry shopping. **But
twenty-one of the 67 play the wrong motion — item 1.** Accounts in
`roadmap-history.md`. NEXT: T3 queue points and standing destinations.

**THE PLAYTEST IS DEPRIORITISED (18 Aug, Jafar):** *"Don't worry about
timelines or the near goal or play testing. Just keep building."*
`playtest-plan.md` stays live as the Mac setup record. Live speech stays
parked — no DirectML on the Air.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

1. **ABOUT A THIRD OF THE CLIPS ARE THE WRONG ANIMATION — twenty-one of
   sixty-seven.** *(on screen; the re-pick runs on Jafar's machine)* Found by
   the travel column I had written off the day before: `Walking` reads 0.00m
   and `Standing Arguing` 3.75m. **`walk` is a stationary guard pose with the
   hands up**, so the slot the whole street is named after does not contain a
   walk. The picker screens on both axes now — hips for upright-or-floor,
   travel for does-it-move — with bounds from the measured gap. Twenty-one
   rejected, forty-six accepted.

   **For Friday:** the re-pick REFUSES a candidate whose contents contradict
   its name and tries the next; a slot the catalogue cannot fill reports
   MISSING. **Holes are the right outcome and they are the information.**
   **Not caught, and said so:** `sit` renders standing at 96cm and the three
   sitting clips read 18, 94 and 96, so there is no correct example to set a
   band from. Account in `clip-findings.txt`.

1. **THE STILLS NO LONGER PHOTOGRAPH WALLS, AND THE METRIC IS STILL TOO
   NARROW.** *(rule 12)* The camera steps back off anything filling more than
   a quarter of the frame at arm's length, bound from a measured bimodal
   series, exercised on a real 0.83 case. Account in `roadmap-history.md`.
   **The median ray distance SHIPS THIS BUILD.** Same 84-ray grid, one pass,
   both numbers: the fraction still answers "is the camera against a wall" and
   `shotDepthMedian` answers "can it see the street" — which is what
   `review_day5_noon` needed, slabs across the middle at ten metres reading
   near zero on the fraction. No bound on it: there is no landed series yet.

   **And the tour got its own pair**, `tourDepthBy=[...]` keyed by district and
   sorted shortest-first, because "which districts look unbuilt" needs the name
   attached to the number and a sorted series structurally cannot carry one.
   **A prediction is written into the emitter before the run**: the tour camera
   is 14m up and 34m back at about 20 degrees down, so flat empty ground should
   read north of 40m and a built street ten to twenty. If all seven come back
   within a few metres of each other the ground plane is dominating and the
   metric is the wrong shape — say so, do not reinterpret it.

   **Also fixed while in there:** the `!_touring` block's own comment claimed
   the blocked-frame series excluded the district tour. The `Add` sat outside
   that block, so seven teleported frames had been going into it.

1. **THE CREW TIER OF `looseEnds` NEVER OPENS** — `crew=2`, nobody below the
   poach floor, so it has never once fired in the project's recorded history.
   Same shape as the Law tier, off for entire runs until the denominator
   caught it (fixed, landed `[Law:1,Owed:5]/open7/2of6`). **Plant the
   condition, do not loosen the floor.**

1. **THE RAIN READS AS BLACK SCRATCHES AT EYE LEVEL.** *(player-height frame,
   dfefd62)* Fine from the elevated camera, dense dark striation from the
   player's eyes, likely sized for a downward view. **Every run since has come
   back dry — this needs a WET run, not another look.** The magenta half of
   that report is REFUTED.

1. **THE BODY BUDGET IS CLOSED AT 87.8% — account in `roadmap-history.md`.**
   Three things stay live. **The band, not the budget:** 13.1 walkers in frame
   per pass, only 6.5 inside the 34m band, so half the people you can see can
   never be skinned.

   **The white pills are unidentified and NO COMMITTED STILL HAS ONE.** The
   pale figures in `review_street.jpg` measure `#5d626f`/`#66676a` against
   buildings at `#7f838f` — DARKER than the walls — and that frame's brightest
   1% is entirely the harbour. I called them white off the picture, the sixth
   wrong identification. **Next step is a measurement that fires WHILE one is
   on screen.** The T-pose in that frame is real and separate — `armStreet`'s
   tail, which a median cannot see.

   **`bodyWashUnreached=534` against `bodyTinted=1326`** — 40% of bodies render
   darker than the band because a multiply only subtracts. A limit, not a bug.
   **`RealBodyCap = 12` needs a PC measurement**, not a CI one.

1. **NO BUS AND NO BICYCLE EXIST IN THE KIT — the remaining primitives.**
   `vehicleFellBack=[bus,bike x6]`. All 50 car-kit models ARE extracted and
   neither is among them, so this is a sourcing gap: another CC0 kit, not more
   code. One bicycle model closes almost all of it. (The police car is in;
   account in `roadmap-history.md`.)

1. **PATROL DENSITY FOLLOWS THE INQUIRY — and the measurement of whether it
   READS is still not finished.** Weight by stage (None 1 ... Manhunt 5),
   converted only on parked cars, routed to a beat in the player's district,
   stood down when the inquiry clears. Every link fires. Account and the four
   wrong theories in `roadmap-history.md`.

   **What is open:** `patrolOnBeatMean=0.00` over 3 shots against `0.18` over
   17 — zero of three separates nothing. The `hunt_` pair photographs the
   manhunt now, so the next build has frames to judge from. **Still unread:**
   six cars that never stop are six brief crossings; a patrol PARKED with its
   beacon lit stays in frame. A feature, not a knob.

1. **THE VERDICT STEP IS 416 CHARS OFF A HARD CEILING AND FAILS AT DISPATCH,
   NOT AT COMMIT.** *(CI)* A 422 at dispatch means NO Windows build at all.
   **The real fix is extraction**, as `sim-shots-stage.sh` proves: move the
   step body to a script file. Until then every comment there is a coin flip.

1. **THE DISTANT SKYLINE WAS PALE LAVENDER OVER A NOIR STREET.** *(on screen,
   `district_strip` — the top third of the frame)* Kit props arrive wearing
   whatever their author painted them, and `BuildSkyline`'s kit branch kept
   them while its own `else` branch built the same tower out of
   `AssetLibrary.Concrete` and looked right. **The fix already existed one
   system over:** `TrafficHost` repaints kit cars for exactly this reason —
   its comment says the kit ships "holiday-brochure mint" and the first stills
   had every car wearing it. Same shape, and the skyline never got it.

   Tinted to agree with its own fallback rather than to an invented colour,
   and darker than the near town because these stand at the map's far edge —
   a skyline brighter than the street in front of it is the specific thing
   that read as wrong. `skylineRepainted` ships beside `skyline=n/m` so the
   repaint cannot silently stop running, which is how this survived.

1. **AND FOUR MORE KIT-PROP SITES ARE UNPAINTED — A QUESTION, NOT A FIX.**
   Awnings and cars go through a repaint; benches, bins, street lights and the
   crate stack do not. **Deliberately not mass-repainted:** the skyline was
   wrong because it was BRIGHTER than everything around it at distance, and a
   green bench is perfectly plausible. Acting on the resemblance alone is the
   rule-4 mistake of treating a picture as evidence of WHAT. **The measurement
   is a brightness comparison between kit props and the town palette, on the
   frame**, not another look.

1. ~~**A STREET PLATE FILLS HALF THE MANHUNT FRAME**~~ — **GONE, AND NOT
   BECAUSE ANYONE AIMED AT IT.** `worstWorldFrac=0.037` with the plate named,
   and the new `hunt_day13_noon` shows "Quay" small at the right edge. The
   camera moved as a side-effect of the district fix. **The metric agrees with
   the frame, which is the point** — it now exists for the next time, and the
   raycast blindness it was written for is real regardless.

1. **A THIRD OF SPEECH BUBBLES OVERLAP, AND THE PASS THAT SHOULD FIX IT FIRED
   ONCE IN A WHOLE RUN.** *(on screen)* `bubbleOverlapMedian=0.33` over 39
   samples — a MEDIAN, so it describes a typical frame rather than a bad
   moment — and the still shows "That's … ends with …" printed through "was
   Novak … came to".

   **The denominators added this session are what made it readable:**
   `bubblesLiftedSum=1` against `shotFixups=27`. The control is
   `namesPinnedSum=106` over the same 27 shots — the site runs, the pattern
   works, and it is the bubble de-overlap specifically that does not.

   **And the measurement was in the wrong place to ever say so.**
   `CollidingNames` ran three hundred lines ABOVE the three passes that move
   text, so `collidingBubbles` and `bubbleOverlapMedian` reported the state the
   repairs then acted on — a number that can only see the problem and never
   the fix. Moved below all three; it also puts `collidingNameSamples` and
   `shotFixups` on the same shots (they read 26 and 27). **Next build's median
   is the first one that describes a committed frame** — read it before
   touching `LiftAtShot`.

1. **THE NAMEPLATE HEAP IS MEASURED AT LAST AND THE INSTRUMENTS AGREE WITH
   THE PICTURE.** *(on screen)* `collidingNames=3` over 26 samples, worst at
   `day13_noon`; `worstNamePair=[Noor|Sam]`, `namesAtWorstName=5`,
   `textPersonLabels=10`. Five labels projected at the peak, **3 of their 10
   possible pairs overlapping** — a heap, as the frame shows. The
   "counter says 0, picture says heap" argument is over; account in
   `roadmap-history.md`. **What is open is the DECLUTTER**: `PinAll` runs at
   shot time and three pairs still overlap. Read `namesPinnedSum` against
   `shotFixups` next build before anyone tunes it.

1. **THE VERDICT HAS AMBIGUOUS KEYS AND NOTHING HAD EVER LOOKED — 30 same-line
   and 5 cross-line, measured.** `tools/verdict-dupkeys.py` is new and reports
   them; `verify.py` runs its selftest as a gate and prints the file's counts.

   **The two that mattered are fixed.** `collidingWorldText` read **5** on the
   glyphs line and **9** on the done line of one run — the glyphs line was
   emitted on **day 2** of a seventeen-day run while its peaks kept rising for
   another fifteen days, so it has been publishing a partial as a summary since
   it was written. It is emitted at the end of the run now. And `clean=`
   appeared TWICE on the done line, 310 from the purse and 0 from the Act III
   snapshot; the snapshot's pair is `a3clean`/`a3dirty` now.

   **What is left is a real backlog.** The remaining same-line hits are lines
   carrying several sub-records at once — `Traffic: wheels` puts a dimension
   and a ratio both under `hi=`, and two lines repeat a whole per-walker record
   three times. A grep gets an arbitrary one of three. **The fix is one line
   per record**, as the sky readings already do.

   **AND THE GATE IS NOT ON YET, ON PURPOSE.** The landed verdict still carries
   the collisions — it came from the build before the repair, so gating now
   would go red on arrival (rule 5b's corollary). **Turn the file check into a
   gate once a verdict lands clean.**

1. **AND THE SAME COUNTER IMMEDIATELY FOUND A BIGGER ONE: FIVE OF SEVEN
   DISTRICTS HAD NO SHOPS AT ALL.** `the_Hook:shop73 Copper_Row:shop4` and
   **zero everywhere else** — the Exchange is the financial district and had no
   commercial frontage; the Parade is the entertainment strip and was 37 houses
   and 24 flats. Shops were gated on `nearCore` alone and the dense cores sit
   in the Hook, so the flag had been answering "is this the Hook".

   **The warehouse fault a second time, in the branch immediately below it** —
   and found by reading the new counter's output, not the code. Two shares per
   district now (at a core and away from one), because both are real: a
   district has a character and its centre carries more trade than its edges.
   The Hook keeps 0.55 at a core, since every frame-drift check is calibrated
   on it. Tested both ways — five districts must have shops, and the Parade
   must out-trade Fairview by a clear margin, or "everywhere is a high street"
   would pass. **Read `premisesByDistrict` again next build.**

   **Ironside has only 7 dressed frontages against 40-135 elsewhere**, because
   it is excluded from terracing and takes the legacy block path. The
   industrial quarter is nearly undressed. Noted, not chased.

1. **THE FRAME GATE IS RED AND THE COST HAS MOVED — this item was two regime
   changes stale.** **Read the breakdown, not the mean**: `mean=666.4ms` is a
   software rasteriser and says nothing; `game=24.53ms` against a 12ms budget
   is a 104% overrun in OUR code.

   Current: `npcs=9.48 bodyLod=4.68 mix=3.75 traffic=2.51 sun=1.27
   population=1.40 rigs=1.25`. **`npcs` is now the dominant cost** — the series
   says it tripled (~2.3-3.3 → ~4.4 → ~8.6-9.5 across three regimes) while
   `game` went 14→18→24ms. Start there, not at bodyLod (a once-a-second FULL
   pass; spreading it round-robin needs the measurement split from the sweep
   first, and tuning belongs on the PC). **`sun` is settled** — it read 3.15ms
   only because the audio mix ran inside its timer.

1. ~~**The session-hook guarantee** (M22)~~ — **BUILT AND HOLDING.** What is
   open is the READING, not the tiers — see `## Now`.
2. ~~**Romance** (M18)~~ — **PROMOTED TO M18.5, 18 Aug by Jafar.**
3. **Smuggling** (M21) — a port town whose Act III threat is Customs and
   Excise, with no smuggling to be caught at. Runs on the `Racket` substrate.
4. **The other day-job tracks** (M18) — `Core/DayJob` is the courier round,
   singular; the doc offers bar/courier/office on the first morning.
5. **Interiors beyond the pub** (M20) — every other door is a threshold.

**And one now unblocked:** reaction animation. `flinch`, `greet`, `wave`,
`glance`, `point` and `head_no` are on disk since 18 August and the perception
events they wire to already fire. Wiring, not sourcing.

### The quality ladder (standing order 16 Aug: best available, not first working)

Before closing any visible item, ask: best available result, or first working
one? Take the next rung or name it here. A blank next rung is a research task.

| aspect | rung now | known next rung, free |
|---|---|---|
| textures | 2K colour+normal landed; roughness wired on walls | ground roughness (SetWetness must drive _GlossMapScale); AO maps |
| buildings | procedural terraces, photo surfaces | window reveals/sills relief; per-district trim |
| vehicles | Kenney kit + town paints | curated higher-fidelity CC0 set (Quaternius/Sketchfab), same pipeline |
| props | Kenney kits, partial coverage | fill the miss list (benches!); higher-tier swaps |
| characters | Mixamo bodies, gait archetypes | Jafar's clip session; reaction anims (T3) |
| lighting | gradient sky, noir grade, wet streets | clouds (T4); noon shadows/AO; HDRP post-playtest |
| animation feel | walk/idle variants | flinch/greeting/turn-to-look wired to perception |
| audio | foley, barks, procedural score | voices into build (Thu); positional street sounds |

- **M21, the two ledgers.** Empire growth, law as a tool, what expansion costs
  you. Entirely unbuilt, entirely Core, so entirely doable here without a round
  trip. This is the largest piece of unwritten game left.
- **M22, the shape of a playthrough.** Onboarding, pacing, replayability and
  succession — also unbuilt and also Core-shaped.
- **Read a system and write down what it actually does.** Every system here has
  at least one comment that is now false — the supply is unlimited, and each
  one found is a bug that would otherwise have been believed. **Read the code
  that produces a number too**: three faults in `CollidingNames` on 20 August,
  found by reading rather than by any reading it produced.
- **Turn a still into a number.** Five faults found by opening a frame and none
  by a gate. Anything a frame shows that no metric names is a metric worth
  adding.
- **THE DROP PIPELINE.** Two of six windows miss in a typical run. The
  waypoint-collider cause is fixed; the second — steered the whole window,
  stalled seven metres out — has no explanation and `stalled=` lands next
  build. **Deliberately not loosened** (rule 6).
