# The work stack

> **STATUS — LIVE**, verified 2026-08-15. What gets picked up next, in order.
> The plan is `roadmap.md` and it wins; this is the next few hours of it.

## Why this file exists, and how to use it

The moment after a dispatch is a decision point, and a decision point at the
end of a long turn is where turns end. On 3 August that cost four gaps of
twenty to thirty minutes with nothing landing. So the next items are written
down BEFORE the dispatch and taken from the top afterwards, with no judgement
required at the exact point where judgement was failing. The full account is in
CLAUDE.md under AUTO MODE.

- **Every item fits inside one build round trip (~28 min)**, or it gets split,
  or it will be abandoned half-done when the build lands.
- **CI-needed items are marked.** They are batched into the next dispatch and
  are never a reason to stop working.
- **Take from the top. Move finished items out** — this records what is NEXT.
  Done work is in the git log, and `roadmap-history.md` holds the cut blocks;
  `docs-check` caps a live plan at 400 lines, which is what forces the tidy.
- **`## Standing work` never empties.** When `## Now` has nothing startable,
  decompose a standing item into it. Running out of short items is a refill
  signal, not a stop signal.

---

## Now

### Where the street got to

The Mixamo harvest landed complete — 67 clips, no duplicates — and the street
came alive with it: people talk, argue, lean, smoke, work counters, carry
shopping. **But three of the 67 play the wrong motion — see item 1.** Accounts
in `roadmap-history.md`. NEXT: T3 queue points and standing destinations.

### THE PLAYTEST — DEPRIORITISED 18 Aug, by Jafar

*"Don't worry about timelines or the near goal or play testing. Just keep
building."* `playtest-plan.md` stays live as the Mac setup record and its
sequence resumes when he asks. Both items this section waited on are closed
(the Mixamo session ran; the per-physique controllers exist). Live speech
stays parked — no DirectML on the Air. The glowing box in day2_night's plaza
is the bar sign's bare back face, one line, low priority.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

1. **ABOUT A THIRD OF THE CLIPS ARE THE WRONG ANIMATION — twenty-one of
   sixty-seven.** *(on screen; the re-pick runs on Jafar's machine)* The
   "ten" finding was right and far too small. What found the rest is the
   travel column I had written off the day before: `Walking` reads 0.00m
   and `Standing Arguing` 3.75m, and I called the instrument broken
   because a standing argument cannot travel that far. It can, if the file
   does not contain a standing argument.

   **The renders agree with travel in every case checked** — and **`walk` is
   a stationary guard pose with the hands up**, so the slot the whole street
   is named after does not contain a walk. The picker screens on both axes
   now, hips for upright-or-floor and travel for does-it-move, with bounds
   from the measured gap. Twenty-one rejected, forty-six accepted.

   **For Friday:** the re-pick REFUSES a candidate whose contents contradict
   its name and tries the next. Where the catalogue has an alternative that
   is a fix; where it has only the one name (`thinking` matches "Thinking"
   and nothing else) the slot reports MISSING. **Holes are the right outcome
   and they are the information** — a slot that cannot be filled from a
   2,846-name harvest says the harvest needs redoing, not re-picking.

   **Not caught, and said so:** `sit` renders standing at 96cm and passes
   both axes. The three sitting clips read 18, 94 and 96, none at chair
   height, so there is no correct example to set a band from.
   Full account in `clip-findings.txt`.

1. **TWO OF THE SIX REVIEW STILLS ARE PHOTOGRAPHS OF A WALL.** *(the
   evidence channel itself — rule 12)* `review_day2_noon` on `e6634a1` is a
   stone wall across the right half with a street sign on it;
   `review_day5_noon` is roof and awning slabs across the middle with the
   street visible only in gaps. A third of the primary evidence this project
   reads every build shows almost no street.

   **No gate could have said so, and that is the interesting part.** Every
   one asks about a SYSTEM — are the billboards aimed, is text the right way
   round, did the bodies get skinned — and all of them pass perfectly on a
   picture of a wall. `review_street` has had a declutter loop since a lamp
   column filled its frame; the DAY stills never got one and are taken
   wherever the sim's camera happens to be standing.

   **`shotBlocked*` ships this build and MOVES NOTHING, on purpose.** The
   loop needs a bound and I do not have one: I can see two frames are bad and
   cannot say what fraction that is. Guessing it is expensive both ways — too
   low and every still starts backing away from ordinary streets, since this
   city is terraced and a wall five metres off is most compositions, and a
   dozen code comments citing these file names quietly start describing
   different pictures; too high and nothing happens and it reads as fixed.

   **NEXT BUILD: read `shotBlockedSeries` beside `shotBlockedWhere`.** Six
   fractions, one per still, and the two named above should be legibly
   different from the four good ones. If they are not, the ray grid is
   measuring the wrong thing and that is the finding. Then the loop lands
   with a number under it.

1. **THE DENOMINATOR PAID FOR ITSELF THE FIRST TIME IT RAN, and the law
   tier was broken.** `e6634a1` read `looseEnds=6/0/[Owed:6]/open6/1of6` —
   six evenings, exactly ONE tier live on each — beside `inquiry=Manhunt
   pressNamed=1 homNamed=9 redirected=1 pointedAt=kest`. The detective was
   hunting the player and the paper had printed her name, and the evening
   screen said the law was not open. Without the open count that reads as
   "Owed simply outranked it", which is what I would have concluded.

   Cause: the tier asked `string.IsNullOrEmpty(Homicides.PointedAt)` — is
   anybody else named — and NOTHING EVER CLEARS THAT NAME. Only the relief
   expires, after four days. One successful redirect, ever, closed the tier
   for the rest of the run. It reads the live relief now. Tested both ways
   off the real book, and the accepting case is the one the old condition
   could never reach.

   **What to read next build:** the open count. If it is 2 or more the lower
   tiers fire and are outranked; if it is still 1 with a manhunt running,
   something else in the chain is dead. **Crew has also never opened**
   (`crew=2`, no member below the poach floor) — that is the next one to
   check if the count does not move.

1. **THE RAIN READS AS BLACK SCRATCHES AT EYE LEVEL — RECOVERED, NOT
   RESOLVED.** *(player-height frame, dfefd62)* Fine from the elevated
   camera, dense dark striation from the player's eyes, likely sized for a
   downward view. **Cannot be judged on any frame since — every run has
   come back dry, so this needs a wet run rather than another look.** The
   magenta half of that report is REFUTED and named so it cannot return.

1. **THE BODY BUDGET IS CLOSED AT 87.8% — the account is in
   `roadmap-history.md`.** What is still live is three separate things:

   **The band, not the budget.** 13.1 walkers in frame per pass and only 6.5
   inside the 34m band: half the people you can see are too far away to ever
   be skinned. Belongs with the population item, not here.

   **The white pills are still unidentified, and NOT ONE OF THE SIX STILLS
   ON `e6634a1` HAS ONE.** Measured rather than squinted at: the two pale
   figures in `review_street.jpg` read `#5d626f` and `#66676a` on their lit
   quarter, against the buildings behind them at `#7f838f`. They are darker
   than the walls. And the brightest 1% of that frame sits entirely in one
   place — x576-704, y320-384, the harbour at the vanishing point — not on
   any body. I had written "two of them, one in a T-pose" off the picture
   before measuring it, which is the sixth wrong identification of this and
   the exact trap rule 4's second half describes.

   So the claim `bodyAlbedo` named them was wrong (it measures source
   TEXTURES, not the render), "the cast is too bright for the palette" is
   retracted, and now "it is visible in the stills we have" is retracted too.
   **It is intermittent and no committed frame currently contains one**, so
   the next step is a measurement that fires WHILE one is on screen — the
   still-reading route is closed until a frame actually catches one.

   **The T-pose is real and separate.** One figure in `review_street.jpg` has
   arms straight out. That is `armStreet`'s tail, and CLAUDE.md's own note
   says a median across bodies structurally cannot see it.

   **`bodyWashUnreached=534` against `bodyTinted=1326`, and nobody has
   looked.** 40% of bodies render DARKER than the band, because their sheet
   is darker and a multiply only subtracts. Not a bug in the wash — a real
   limit on how much of the palette reaches the street.

   **`RealBodyCap = 12` needs a PC measurement, not a CI one.** Its comment
   prices a dozen skinned bodies against a runner with no GPU at all.
   Plausibly the cheapest large win for how full the street looks.

1. **NO BUS AND NO BICYCLE EXIST IN THE KIT — 10 of 28 vehicles are
   still primitives.** `vehiclesKitted=18/28`,
   `vehicleFellBack=[bus,bike x9]` on its first run. Checked: all 50
   models in the car-kit listing ARE extracted, and neither a bus nor
   a bicycle is among them. So this is a sourcing gap, not a bug, and
   the fix is another CC0 kit — not more code. Bikes are nine of the
   ten, so one bicycle model closes almost all of it.

   **THE POLICE CAR IS IN — awaiting its first build.** "Wrong era, wrong
   town" was a guess about a file nobody had opened. It is a plain saloon a
   fifth longer than the sedan, and its body maps to the WHITE region of the
   shared colormap (#cbcbde) where every other car maps to mid-slate. White
   saloon, slate stripe, one blue beacon on a plinth we add — the kit has no
   light bar. Exempt from the noir multiply, which would have turned it into
   the dark saloon it exists to not be. Its front push bar is one named mesh
   (`grill`) and is dropped. **Landed: `vehiclesKitted` 18/28 -> 21/28.**
   `ambulance` and `firetruck` stay out with a reason rather than an
   assumption — both are mid-slate in this palette.

1. **PATROL DENSITY NOW FOLLOWS THE INQUIRY — awaiting its first build.**
   `PatrolWeightFor(Inquiry)` is a pure Core function: None 1, Procedure 2,
   Investigation 3, Manhunt 5, which on 28 vehicles is 2 patrol cars quiet
   against 6 under a manhunt. Conversion happens right after `SetHour` and
   only on PARKED cars, so nothing changes shape in front of the player, and
   the changed ids come back so their bodies are rebuilt rather than Core
   believing something the street does not show.

   **Read next build:** `inquiry patrolWeight patrolWant patrolNow
   patrolsChanged patrolBodies`, all on one line. `patrolsChanged` without
   `patrolBodies` is the wiring broken; `patrolNow` short of `patrolWant`
   through a whole run means the dormant tail is never long enough and the
   conversion needs a second moment.

1. **THE FRAME GATE IS RED AND THE COST HAS MOVED — this item was two regime
   changes stale.** **Read the breakdown, not the mean**: `mean=666.4ms` is a
   software rasteriser and says nothing; `game=24.53ms` against a 12ms budget
   is a 104% overrun in OUR code.

   Current: `npcs=9.48 bodyLod=4.68 mix=3.75 traffic=2.51 sun=1.27
   population=1.40 rigs=1.25`. **`npcs` is now the dominant cost** and this
   item used to say `npcs=2.77` with bodyLod on top — the series says npcs has
   tripled (~2.3-3.3 → ~4.4 → ~8.6-9.5 across three regimes) while `game` went
   14→18→24ms. Start there, not at bodyLod.

   **`sun` is settled and the old paragraph here was wrong.** It read 3.15ms
   because the whole audio mix ran inside the sun's timer; `mix` was split out
   of it and `sun` is 1.27ms now, with the landed series confirming the step.
   Nothing to chase.

   bodyLod is a once-a-second FULL pass, so spreading it round-robin needs the
   measurement split from the sweep first or every count becomes a peak over
   partial passes. Tune on the PC, not CI.

1. **THE BUBBLE STACK'S SCREEN PASS BARELY RUNS.** `bubblesScreenLifted=1` of
   `bubblesMade=54` with `bubblesAtCeiling=16`. Two reasons, both in
   `LiftClearOfScreen`: it runs once at the bubble's BIRTH, before anything
   has drifted into it, and the loop is gated `_lift < MaxLift` so it skips
   exactly the bubbles at the ceiling it was written for. `NameTags.PinAll`
   is the shape to copy — do it at the shot, against the camera that renders
   it. **The recession claimed here before ("7.6% at ceiling") does not hold
   on `e6634a1`: 16 of 54 is 30%.**

3. **THE DWELL FIX TRADES A VISIBLE FAULT FOR AN INVISIBLE SAVING.**
   `bodyLodMs=4.68` against `populationMs=1.40` — the LOD pass costs three
   times the reband it hides inside. **Decide against `gameShare`, not
   milliseconds:** at `render+rest=641.83ms` on a software runner a few ms is
   noise here and real on a player's machine, which is why this is undone.

8. **KEEP RETIRING THE REACH LEDGER — 35 entries**, `StreetMap.OnStreet` off it
   tonight because the place-setback question needed exactly the wider
   containment test the entry said it was waiting for. **AND READ THE ENTRY'S
   REASON, NOT JUST ITS NAME**: two were wrong this morning, and the two
   sampled tonight (`Combat.Breathe`, `VoiceBank.PoolVoices`) were both honest.

9. **JUDGE THE LIMP FROM A FRAME.** The pose limp was a sixteenth of the audio
   one and is now the same size; at capability 0.30 the bad leg's stride is
   44cm shorter than the good one, which is a lot. `Gait.MaxAsymmetry`'s own
   comment says above about 0.5 it stops reading as injured and starts reading
   as broken animation. Nobody has looked at one yet.

10. **M22, THE SHAPE OF A PLAYTHROUGH** — the largest Core-shaped piece left.
   One sub-item is startable now: `PopulationSeed = 20260726` is hardcoded, a
   second seed gives 699 of 700 different people, and there is no new-game
   surface to choose one. **It must not be randomised** — CI determinism
   depends on it — so this is a surface, not a change to the default.

11. **THE LAW REACHES MANHUNT NOW — this item was written when it stopped at
   Procedure and is superseded.** `e6634a1` reads `inquiry=Manhunt homSaw=9
   homWouldTalk=3 homNamed=9 homPressure=2.71 pressNamed=1
   pressHeadline=[KILLING ON THE HOOK: POLICE NAME THE PUBLICAN]`. The whole
   chain the old text called open — witnesses who can name you, pressure past
   `ManhuntAt`, the paper printing it — is running end to end.

   **The one thing that was still broken it could not see**, because the
   evening screen has its own opinion: the law tier read shut on all six
   evenings anyway. That is the redirect bug, fixed, and it is the item above.

   **Still worth a look:** `homWouldTalk=3` of `homSaw=9`, so two thirds of
   witnesses would say nothing to a detective — plausible for this town and
   never checked against the design. And `pointedAt=kest` in every run:
   staged, so probably honest, but a branch nobody has sampled. Item 12's
   list.

12. **THE REST OF WHAT `gates --constant` FOUND, AND IT IS A WORK LIST.**
   Sixty keys have never been anything but zero across 131 runs. Most are fault
   counters doing their job — `errors=0`, `idLeaks=0`, `blankLabels=0`,
   `panelsBad=0`, `offRoad=0`. These are the ones that are not:

   - **`threat` has only ever seen one outcome.** `brandishes=1` a run, so
     `called=0 complied=0 undraw=False` CANNOT be sampled — one brandish gives
     one answer, `FleeScreaming` every time. Plant several, at people with
     different nerve.
   - **`departed=0` and `carriedOut=0` are the live zeros**; `adds` reads 10,
     and this entry claimed otherwise for four builds off prose.
   - **`groundless=False`** — a carry has never been groundless.
   - **`summonsTaken=0` — fixed 5 August, awaiting its own build.** The nightly
     pass sampled the player's position at breakfast against lines live at hour
     21; now sampled at the ring hour. **The plant is deliberately NOT in the
     same build**, so a moving `summonsTaken` is attributable to this alone.

   **The rule for every one of these is the same and it is rule 5b's
   corollary: PLANT the condition, never loosen the bound.** And do them one
   or two at a time — a build carrying five new staged behaviours cannot
   attribute a red gate to any of them.

## Next

- **Raise the population rather than cutting districts.** Measured, reversing
  the old plan: seven districts at 1,400 gives 43.5 distinct faces a week
  against 47.4 for three at 700, and 2,100 beats the cut outright. **And the
  empty street above may make this urgent rather than optional.**
- **Tier the cast.** 47 distinct faces a week, 13 near enough to read, a knee at
  ~50 covering 92% of a resident's week, 68 rigs at 1.1ms of 12ms. **The
  machine does not bound the cast at fifty; only authoring does.**
- **M17.2 voices** — no longer held on the writing verdict (78). A SPEND, not
  authorised.
- **Is fifty-six conversations a run too many?** A judgement off a still: 16-42
  under the old flat-road test, 7 after the pace slowed, 30-56 now it asks
  about junctions.

## Blocked, and on whom

- **Settled decisions now live in `design-doc.md` §18** — the era and its
  currency among them — so they are recorded once and not re-argued here.

- **CLOSED 18 Aug — a character mesh needed no purchase at all.** This entry
  said only Jafar could buy one; Mixamo bodies are a free download and the
  pool is FOURTEEN against 43 named people. Right about the gap, wrong about
  the price, for weeks.
- **API spend is quoted in FRANCS; the game's money stays £.** Jafar is in
  Switzerland. The £ in the design doc is a deliberate fiction decision — a
  British pub — and quoting both in one unit is how "a few pounds" reached him
  for a bill he pays in CHF. Two tasks authorised 3 Aug, both done; the writing
  probe re-run authorised 5 Aug. Nothing beyond that.

## How to keep this file honest

- **Dispatch, then immediately take item 1 of Now.** A build in flight is a
  reason to switch tasks, never a reason to stop. **Arming a watcher is the
  PRECONDITION for ending a turn, not permission to end one** — both are
  required and only one of them feels like progress.
- **Batch Game-layer changes**; each build keeps its own verdict under
  `sim-shots/runs/<sha>.txt`, but the single Personal licence seat means one
  build at a time. **And prefer a local answer** — before dispatching, ask
  whether the question is actually about Unity. Item 1 above is not.

## Standing work

**This section never empties, and that is its entire job.** The queue ran dry
on 3 August because every item was sized to fit one build round trip, so an
hour of good work consumed the list and an empty list read as an empty
afternoon. When `## Now` has nothing startable, decompose one of these into it
— running out of short items is a refill signal, not a stop signal.

### THE FIVE THINGS THE DESIGN DOC DEFINES AND NOBODY HAD PLANNED (18 Aug)

Jafar asked for the design doc to be checked for anything defined and never
planned. Five, each now placed in a milestone and each startable without CI or
his machine. Full statements in `roadmap.md`; `design-doc.md` §18 has the
account and the denominator of what was checked and found sound.

1. ~~**The session-hook guarantee** (M22)~~ — **BUILT AND HOLDING.**
   `looseEnds=6/0/[Owed:6]`: six evenings closed, none empty, so the guarantee
   is real. What is open is the READING, not the tiers — see `## Now`.
2. ~~**Romance** (M18)~~ — **PROMOTED TO ITS OWN MILESTONE, M18.5, 18 Aug by
   Jafar.** Statement, done-when and risk are in `roadmap.md`.
3. **Smuggling** (M21) — a port town whose Act III threat is Customs and Excise,
   with no smuggling to be caught at. Runs on the `Racket` substrate the other
   three use.
4. **The other day-job tracks** (M18) — `Core/DayJob` is the courier round,
   singular; the doc offers bar/courier/office on the first morning.
5. **Interiors beyond the pub** (M20) — every other door is a threshold.

**And one now unblocked:** reaction animation (flinch, greet, turn-to-look) read
"blocked on the Mixamo clip session" for weeks. That session ran on 18 August;
`flinch`, `greet`, `wave`, `glance`, `point` and `head_no` are on disk and the
perception events they wire to already fire. Wiring, not sourcing.

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
  at least one comment that is now false — three found in one day, one in the
  file being edited at the time. The supply is unlimited and each one found is
  a bug that would otherwise have been believed.
- **Turn a still into a number.** Five faults found by opening a frame and none
  by a gate — the newest, rumour text printed backwards across `day5_night`
  while three orientation metrics read perfect. Anything a frame shows that no
  metric names is a metric worth adding.

- **THE DROP PIPELINE, AND WHAT IS LEFT OF IT.** Two of six windows miss in a
  typical run. The first cause was the waypoint's own collider sitting thirty
  centimetres outside its completion radius, now fixed; the second — steered
  the whole window, stalled seven metres out — has no explanation and
  `stalled=` lands next build. **Deliberately not loosened**: accepting a run
  that never exercised the pipeline is rule 6 exactly.
