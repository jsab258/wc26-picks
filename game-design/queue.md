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

### MONDAY: JAFAR'S CLIPS LANDED AND THE STREET IS ALIVE.
The Mixamo harvest came in complete — 54 slots, zero missing, and
the pick replaced two absurd July survivors (walk start/stop were
FASHION CATWALK turns). Ten clips had no consumer at all; they have
one now. People talk, argue, lean, look bored, smoke outside the
pub, work counters, carry shopping — `activityPeak` 1 -> 18 once the
states went on ALL FOUR controllers rather than the canonical one
(the first version reached one body in the city and its own commit
message quoted the rule about denominators it then omitted). The old-
person gait is live off `idle_old`/`walk_old`. The crowd stops being
boxes within 14m, perf-neutral: same cap, better allocation.

Also closed: the intermittent traffic red (a cab idling on a rank
spur, which is a LANE, so `OnRoad` called correct behaviour a fault —
the gate was measuring the model), zebra crossings with belisha
beacons, cables that only hang where two buildings hold them, the
width-aware bubble cap, every chimney smoking, and the two white
pills at the kerb.

THE PILLS COST FOUR BUILDS AND THE LESSON IS RULE ONE. I identified
them three times off a 1280x720 JPEG — capsule, default material,
smoke — and all three were wrong; `undressed=0` and `capsules=0`
each killed a class, the smoke retune changed nothing. Nine lines of
numpy over the committed frame then answered it in one turn: exactly
two tall white blobs, and the city builds exactly two pillar boxes,
0.48 by 1.1m, both. Their red was a property-block tint that never
reached the renderer; the colour now lives in a shared material,
where nothing can quietly overwrite it. **MEASURE THE FRAME. The
image analysis is cheap, it is in the repo already, and it beat
three confident readings.**

NEXT: T3 queue points and standing destinations; then the freeze
decision (recommendation KEEP, unchanged and now stronger); then the
street-spec topology re-plan, whose case is the ~110 parcel ceiling.

### THE PLAYTEST PUSH OWNS THE QUEUE UNTIL WEDNESDAY 19 AUGUST.
**The plan is `playtest-plan.md`** — MacBook Air, three players, four
days. Order there wins over order here. Everything below stands but
YIELDS: live speech is parked (no DirectML on the machine), the visual
and playability work in the plan takes every slot. The deterministic
retry design, the constant-gate plants and the frame-gate CPU work
resume Thursday.

**Sat 15 Aug, end of night: Saturday page done, Sunday page done AND
JUDGED, most of Monday's no-Jafar items done early.** Run edbce5b
proved the batch (Skybox live, bodyChoices=8, tposeBodies=0, preset
probe passing, errors=0) and answered the grade question in numbers:
noon meanLuma 0.44-0.49 with 40-48% bright pixels — overshot into
seaside-morning. Iteration 2 (0.74/0.76/0.80) landed on cdef923 and
SETTLED IT: every matched dry noon came down (worst 0.494→0.446,
bright 48→39%), nights held 0.10-0.13, and the noon still reads
overcast port with the brick fully legible. Weather is not pinned
between runs, so per-day medians mislead — same-shot dry-day pairs
are the honest comparison and both runs' files carry them. The grade
stays; further cuts start re-crushing the brick.
Also landed tonight: render scale option (+ the options panel height
fix), post stack joined the preset (AO's DepthNormals prepass gated),
toast queue + ambient barks, onboarding teaches walking first with
live bindings, PLAYTEST-RUNBOOK.md drafted, and the two-week-old £/$
harness red fixed (core tests green again). Still open before Wed:
judge cdef923's stills; Jafar's Mixamo session then per-physique
controllers; Tuesday freeze + final builds + smoke test. The glowing
box in day2_night's plaza is the bar sign's bare back face — one-line
material fix, queue it behind the playtest-critical work.

### LIVE SPEECH — PARKED until after the playtest (resume Thursday)

The one-paragraph state, full accounts in the git log: the C# side
speaks on Jafar's card (~1.1x realtime, pops fixed, cast complete at
23 voices). The "ah" filler is a deterministic bad draw per
(voice, line) — our sampler fixes the seed — so the fix is DETECT AND
RETRY WITH THE SEED PERTURBED, designed, not built. Streaming and fp16
are closed (worse, measured). `put-voices-in-build.py` is selftested
but has never run against a real build — that is the first Thursday
item. No live speech on the playtest Mac (no GPU): recorded bank only,
and the verdict's speech keys already measure that path.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

1. **THE STREET IS EMPTY AT EYE LEVEL, AND EVERY POPULATION NUMBER
   SAYS IT IS FINE.** *(on screen — review_street.jpg at 0d38986, the
   first frame with nothing standing in it)* The judgement camera is
   finally clear and what it shows is a deserted city. The numbers all
   read healthy and NOT ONE of them is about the view: `walkers=55` is
   bodies anywhere in a city that grew ~2.5x in area at the topology
   stretch, `crowdWalkers=12` is exactly `CrowdWalkerCap` so the near
   cap is BINDING, and `crowdMill=136` is the GOSSIP mill — social
   agents, not a render tier. There is no cheap visible-body tier at
   all. `streetBodies` / `streetBodiesNear` / `streetBodiesLive` land
   next build, counted through the real camera at the shutter. READ
   THE SERIES BEFORE TOUCHING THE CAP: raising it is ~0.58ms/walker
   against `npcs=6.93ms` of a 12ms budget, so doubling it blows the
   frame gate that is already red. The affordable move is more bodies
   in shot per millisecond, not more walkers.

   And the comment beside `PopulationCount = 700` still says "700 puts
   roughly a dozen people out of doors within earshot at midday, which
   is a street rather than a demonstration" — measured on the city
   BEFORE the stretch. Re-read it when the numbers land.

1. **CLOSED 17 Aug — the pink figure was never a fault.** Three
   explanations went out before any was checked and measurement killed
   all three: the frame holds ZERO magenta pixels so it is not the
   error shader, it is not a broken mesh, and it is not cartoon
   proportions — she measures 7.63 heads. It is Mixamo's Sporty Granny
   rendering as authored. What the measuring DID find was two models
   nobody had looked at: The Boss (neckFrac 0.762) and Big Vegas
   (0.761) against a realistic cluster of 0.806–0.837, both now kept
   out of the pool by `Core/Proportion` rather than by a name list.
   Pool 8 -> 6. **Owed: more realistic bodies, which is a Mixamo pick
   and Jafar's step** — the sameness problem got worse to buy this.

1. **THE FRAME GATE IS THE ONLY LIVE RED, AND IT IS THE GAME'S OWN TIME.**
   **Read the breakdown, not the mean.** `mean=483.7ms` is a software
   rasteriser and says nothing; `game=17.55ms` against `gameBudget=12ms` is a
   46% overrun in OUR code and a real number on a real machine.
   `bodyLod=4.39 traffic=3.72 sun=3.15 npcs=2.77 rigs=2.06 population=1.32`.
   `gates --flaky`: `frame` has failed 28 of 141 runs and is red on the
   newest; everything else is quiet. bodyLod is a once-a-second FULL pass
   (spike, not steady cost) — spreading it round-robin is the obvious move
   BUT its verdict counters assume one atomic pass, so split the measurement
   from the sweep first or every count becomes a peak over partial passes.
   CI timings are the wrong machine for tuning: verify on the PC.

   **`sun=3.15ms` is the odd one and is not an obvious loop** — `UpdateSun`
   has none, so it is Unity-side light or shadow work being triggered every
   frame by something that only changes each game-hour. That is a real
   investigation and a plausible 3ms, which is a quarter of the whole budget.
   The queue has been dismissing this item as "not worth touching while
   render+rest is 458ms", which confuses the runner's cost with ours.

1. **THE BUBBLE STACK'S SCREEN PASS HAS NEVER ONCE RUN.**

   `bubblesScreenLifted=0` on `2d5840f` and 2 on the build before, with
   `bubblesNoBounds=0` — so the stated uncertainty is closed (a TextMesh built
   this frame DOES have usable bounds) and the pass is simply inert.

   **Two reasons, both in `LiftClearOfScreen`.** It runs once, at the bubble's
   BIRTH, when nothing has drifted into it yet — overlap develops later as
   speakers and camera move, and a one-shot test at creation cannot see that.
   And the loop is gated `_lift < MaxLift`, so it is skipped entirely for the
   bubbles already at the ceiling, which are precisely the ones it was written
   for. `NameTags.PinAll` is the shape to copy: do it at the shot, against the
   camera that renders it.

   **BUT THE FAULT HAS RECEDED AND THE RATE IS WHY.** `bubblesAtCeiling` fell
   61/156 → 15/75 → 5/66, which is 39% → 20% → 7.6%, and `collidingBubbles`
   91 → 10 → 1. None of that is the fix, which never ran: `bubblesMade` fell
   with it, because bubbles follow confabs and `confabs` swings 29–74 in this
   regime. **Read the rate, not the count** — and it is a real fall even so.
   So this drops down the list: a pass that never runs is rule 6, but it is
   guarding a residue rather than two in five.

3. **THE DWELL FIX TRADES A VISIBLE FAULT FOR AN INVISIBLE SAVING.**
   `bodySpell=5.41` median over 1,143 spells against a derivable 4.7s
   (`BandSlack`/`crowdSpeed`), and the perf split says `bodyLod=2.59ms` against
   `population=1.31ms` — the LOD pass costs twice the reband it was hiding
   inside, spending it on 1,157 prefab instantiates. **Decide against
   `gameShare`, not against milliseconds:** the frame gate reads
   `gameShare=3.43%` with `render+rest=458ms` on a software-rendering runner,
   so a 1ms saving is noise there and would be real on a player's machine.
   That is the whole difficulty and it is why this has not been done.

6. **THE FRAME GATE'S BIGGEST ITEM IS NOW TWO NUMBERS.** *(CI)* `population=
   4.08ms` covered a pass that runs every frame and one that runs once a
   second; read apart they are 1.31ms and 2.59ms. Neither is worth touching
   while `render+rest` is 458ms on a software runner — see item 3.

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

11. **THE LAW NOW ASKS, AND IT STOPS AT THE FIRST STAGE.**
   `inquiry` reads **Procedure** in the four newest runs and **None** in the
   sixty-three before them, changing exactly once, at `0720f52`. That is the
   `AuditClosed` staging landing and holding — not a lucky run — and it is the
   first movement in the whole recorded history of the key.

   **The old text under this number said the law had NEVER asked, sixty for
   sixty.** True when written and false the moment the staging landed, which is
   comment decay in a document rather than in code. It stood for four builds
   because `gates --series inquiry` answered *"no landed run carries that
   name"* — the tool matched numbers only, so every categorical value in the
   verdict was unreadable and its refusal read as a spelling mistake. Fixed
   5 August; the series is what corrected this entry.

   **What is open now is the SECOND stage, and it is one number.** `homSaw=29
   homWouldTalk=7 homNamed=0`: twenty-nine people saw a killing, seven would
   talk to a detective, and not one can put a name to it — so `homPressure`
   sits at 0.40 and cannot reach `ManhuntAt`. `pressNamed=0` is still correct
   and still not a fault: `Press.Print` names you at
   `law >= Inquiry.Investigation` and the stage is one below it.
   `redirected=1 pointedAt=kest redirectRelief=0.00` is the same story — the
   redirect relieves a pressure that has not been built.

   **`homSawStored`/`homHoldsIt` are in flight and split it three ways:**
   stored=0 means the register never took the witness list, stored=29 with
   holds=0 means `FileWith` is not writing, and holds=29 with named=0 means the
   confidence bar. Different afternoons, one reading.

   **And `pointedAt=kest` in all 67 runs** — the redirect has never once
   pointed at anybody else. Staged, so probably honest, but it is the shape of
   a branch nobody has sampled and it belongs in item 12's list.

12. **THE REST OF WHAT `gates --constant` FOUND, AND IT IS A WORK LIST.**
   Sixty keys have never been anything but zero across 131 runs. Most are fault
   counters doing their job — `errors=0`, `idLeaks=0`, `blankLabels=0`,
   `panelsBad=0`, `offRoad=0`. These are the ones that are not:

   - **`threat` has only ever seen one outcome.** `brandishes=1` a run, so
     `called=0 complied=0 undraw=False` are three responses that CANNOT be
     sampled — one brandish can only produce one answer, and it has been
     `FleeScreaming` every time. Plant more than one, at people with different
     nerve, or the other three branches stay theoretical for ever.
   - **CLOSED — `contradiction=0.00` is by design; the branch has run 46
     times.** The zero is the FIRST denouncement, left uncontradicted on
     purpose so the probe cannot alter the outcome beside it. It is in
     `EXPLAINED_ZEROS` now so the tool stops offering it as work.
   - **`departed=0` ONLY — `adds` READS 10.** This entry said "she is
     recruited and never leaves and never brings anybody. Two branches, no
     runs." `companion[with=June recruited=1 departed=0 noted=3 exposure=3
     adds=10 carriedOut=0]`. `--constant` listed `departed` alone and was
     right; the prose here added `adds=0` on its own and was wrong for four
     builds. The live zeros are `departed` and `carriedOut`.
   - **`groundless=False`** — a carry has never been groundless.
   - **`summonsTaken=0` — fixed 5 August, awaiting its own build.**
     `SummonsHost.Nightly` runs at the day close and tested the player's LIVE
     position against lines live at hour 21, so the hour came from the ring
     and the position came from breakfast; now sampled at the ring hour, with
     a third miss reason so the new case cannot read as the old one. **The
     plant is deliberately NOT in the same build**, so a moving
     `summonsTaken` is attributable to this and nothing else.
   - **`reliabilityFiled` moved and came back, and that is honest.** Series
     0,1,1,2,1,1,1 then 0 newest, and `reliabilityRead` says why: zero drops
     were skipped in that run, so zero filed is correct. Rule 5b's corollary
     — make the skip deterministic rather than read the zero as a regression.

   **The rule for every one of these is the same and it is rule 5b's
   corollary: PLANT the condition, never loosen the bound.** And do them one
   or two at a time — a build carrying five new staged behaviours cannot
   attribute a red gate to any of them.

## Next

- **Raise the population rather than cutting districts.** Measured and it
  reverses the old plan: seven districts at 1,400 people gives 43.5 distinct
  faces a week against 47.4 for three at 700, and 2,100 beats the cut outright.
  What is NOT measured is whether a fuller city still reads as a port rather
  than a crowd — a question for a still. Note `CrowdWalkerCap = 12` bounds how
  many are out of doors within earshot whatever the headcount is, so this buys
  FAMILIARITY and changes the frame not at all.
- **Tier the cast.** 47 distinct faces a week, 13 near enough to read, a knee at
  ~50 people covering 92% of a resident's week; 68 rigs cost 1.1ms of a 12ms
  budget. **The machine does not bound the cast at fifty; only authoring does.**
- **M17.2 voices** — no longer held on the writing verdict, which came back 78.
  Note this is a SPEND and Jafar has not authorised it.
- **Is fifty-six conversations a run too many?** A judgement off a still rather
  than a number. The history: 16-42 a run under the old flat-road test, 7 after
  the walking pace slowed, 30-56 now the test asks about junctions.

## Blocked, and on whom

- **THE MONEY DOES NOT MATCH THE DECADE, and it is a decision rather than a
  fault.** The cast deals in shillings, half a crown, pence and two-and-six —
  pre-decimal British currency, gone in 1971 — while `Tier2Gen` dates the world
  to the eighties and nineties by listing CDs, pagers and car phones as
  in-period. Seven references across the sixty cards, now counted by `--audit`
  and deliberately not rejected: refusing sixty cards over an unmade decision is
  the ratchet rule 5 warns about. Two ways out, both cheap, and it is Jafar's
  call: move the era back, or move the money forward. Worth noting the era is
  load-bearing rather than flavour — a late-analog city is what makes missed
  calls, wiretaps and being unreachable into mechanics.

- **A character mesh.** Only Jafar can buy one, and it is now the single
  largest immersion gap in the project — see roadmap 17.1b.
- **API spend is quoted in FRANCS; the game's money stays £.** Jafar is in
  Switzerland. The £ in the design doc is a deliberate fiction decision — a
  British pub — and quoting both in one unit is how "a few pounds" reached him
  for a bill he pays in CHF. Two tasks authorised 3 Aug, both done; the writing
  probe re-run authorised 5 Aug. Nothing beyond that.

## Done, kept here only until the next tidy

Cleared 5 August — the git log is the record.

## How to keep this file honest

- **Dispatch, then immediately take item 1 of Now.** A build in flight is a
  reason to switch tasks, never a reason to stop.
- **Arming a watcher is the PRECONDITION for ending a turn, not permission to
  end one.** Both are required and only one of them feels like progress.
- **Batch Game-layer changes, and dispatch hypotheses in parallel** — each build
  keeps its own verdict under `sim-shots/runs/<sha>.txt`, so concurrent builds
  are concurrent answers.
- **Prefer a local answer.** Before dispatching, ask whether the question is
  actually about Unity. Item 1 above is not.

## Standing work

**This section never empties, and that is its entire job.** The queue ran dry on
3 August after an hour of good work, because every item was sized to fit inside
one build round trip — so an hour of good work consumed the list, and an empty
list read as an empty afternoon. Three gaps of 21, 28 and 28 minutes followed.

When `## Now` has nothing startable in it, the next action is to take one of
these and decompose it into `## Now` — NOT to end the turn. Running out of short
items is a refill signal, not a stop signal.

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
- **M22, the shape of a playthrough.** Onboarding, pacing, replayability,
  succession. Also unbuilt and also Core-shaped.
- **Read a system and write down what it actually does.** Every system in this
  project has at least one comment that is now false; three were found today,
  one of them in the file being edited at the time. The supply is effectively
  unlimited and each one found is a bug that would otherwise have been believed.
- **Turn a still into a number.** Five faults have now been found by opening a
  frame and none by a gate — the newest being rumour text printed backwards
  across `day5_night` while three separate orientation metrics read perfect.
  Anything a frame shows that no metric names is a metric worth adding.

- **THE DROP PIPELINE, AND WHAT IS LEFT OF IT.** `jobRan` says `JobsDone >= 1`
  and means "a drop can be made end to end". Two of six windows miss in a
  typical run and both causes are now named: the first was the waypoint's own
  collider, thirty centimetres outside its completion radius, and it is fixed.
  The second — ten of sixteen metres covered, steered the whole window, stalled
  seven metres out — has no explanation, and `stalled=` lands next build to say
  whether he stopped or merely walked slowly. **Deliberately not loosened**:
  accepting a run that never exercised the pipeline is rule 6 exactly.
