# The work stack

> **STATUS — LIVE**, verified 2026-08-04. What gets picked up next, in order.
> The plan is `roadmap.md` and it wins; this is the next few hours of it.

## Why this file exists

On 3 August I dispatched five Windows builds in two hours and, four times,
**ended the turn instead of picking up the next thing** — twenty, thirty-two,
nineteen and twenty-eight minutes with nothing of mine landing. AUTO MODE rule 2
already forbade exactly that, in my own words, and I broke it four times in one
afternoon.

The cause was not forgetting the rule. It was that **the moment after a dispatch
is a decision point**, and a decision point at the end of a long turn is where
turns end. Nothing was written down, so "what next" meant re-deriving priorities
from a 400-line roadmap, and that is enough friction to lose to.

So the queue is written BEFORE the dispatch, and the rule becomes mechanical:
dispatch, then take the top non-CI item off this list. No judgement required at
the point where judgement was failing.

It lives in the repository rather than in a task list because the container is
ephemeral and the task list is not — rule 12's principle, applied to my own
scheduling instead of to CI's output.

## How to use it

- **Every item is sized to fit inside one build round trip (~28 min).** An item
  that cannot be finished in that window gets split until it can, or it will be
  abandoned half-done when the build lands.
- **CI-needed items are marked.** Those get batched into the next dispatch;
  they are never a reason to stop working.
- Take from the top. Move finished items out — this file records what is NEXT,
  not what happened. Done work is in the git log.

---

## Now

### Startable right now, in order

1. **Read `bc4c689` and `69e03a6` when they land.** The first carries the
   `ALL GATES` line actually reaching the verdict; the second carries the
   per-tick bubble sampling and `bodyReadWhen`. Both answer questions that are
   currently open rather than confirming something already known.
2. **Then promote the gate-label keys from gate-only to REQUIRED** in
   `verdict-keys`. They are always present once `ALL GATES` prints, so deleting
   `atRecruit` from a label would be caught. Needs two or three landed runs
   first — several labels build their text conditionally and which keys are
   stable is not yet known. Do not promote blind.
3. **NOT YET — 9 of 43 is a mandate only if the RIG did them.** Twenty-one
   percent looked like a clear reason to build the enforcement, and that was
   too fast. A crossing after the player takes the camera back is the beat
   correctly getting out of the way; a crossing while the beat is still
   composing is a shot reversing itself. `lineCrossed` pools the two and they
   want opposite responses. `lineCrossedLive` splits them and is building now.
   **Zero live means the enforcement is dead code that would look like a
   feature. Nine means write it.** Do not build before that number lands.
4. **ANSWERED AND CLOSED — nothing ever stands in the way.** Twenty shots
   aimed, **zero** blocked, no blocker to name. The foreground clutter in
   three stills is BESIDE the sight line, not on it, and every judgement made
   about it by eye was wrong in the same direction. Rule 4 again: a picture is
   excellent evidence something is wrong and poor evidence of what. Nothing to
   do here; do not reopen it without a number.

3b. **THE PLAYER DOES NOT GET DARKER AT NIGHT, AND THAT REVERSES THE REVERSAL
   BELOW.** Two readings, each with the crowd measured at the same instant:

       noon   player lum 10.8  crowd median 19.5  range  4.00..62.85
       night  player lum 11.9  crowd median  2.8  range  1.50..11.75

   The crowd's luminance collapses by a factor of seven between noon and
   midnight. **The player's does not move at all** — 10.8 to 11.9 — so at
   night they sit at the very top of the crowd's whole range, the brightest
   body on the street, which is exactly what the night stills show.

   So "it is the shape, not the colour" was right about NOON and wrong as a
   general claim, and I could only tell because `bodyReadWhen` names the frame.
   This is not a wardrobe problem and not a mesh problem: the player's material
   is not responding to the light the way every other body does. That is a
   rendering fault with a specific shape, and it is findable.
5. **ANSWERED — 15 numbers, not 31 lines.** `verdict-reach.py` now reports
   only what is dropped here AND absent from everything that always prints
   (the done-line and, since the repair, every gate label). Thirty-two dropped
   lines reduce to **fifteen genuinely unreachable numbers**, spot-checked
   five-for-five against a landed verdict:

       aoD  bloomBright  grainLocal  vigEdge      — the post-processing A/B
       contradiction  corroboration  mark  backers — the denounce breakdown
       happened (frisk)  isAChoice / canTakeEverything (coat)
       public / home (blood)  marked / saw (cut)  matches  occluded

   The four post-processing ones are the interesting group: they are the A/B
   that decides whether a grade change did anything, and they have never been
   readable from this environment. The rest are one-line breakdowns of
   outcomes whose totals do arrive.

   **Next: add `[series]` or a named marker to the post A/B line only.** It is
   one word in the allowlist and it opens the only measurement family here
   with no other route home. The narration lines stay dropped — a verdict full
   of narration is a log again, which is the thing this channel exists instead
   of.
6. **Jafar runs `BODIES.bat` ~10:00 CEST**; reminder verified armed for 07:55
   UTC. This is now the ONLY route to the undressed-player problem — see the
   reversal below.
7. **Keep retiring the reach ledger** (69, down from 71). What is left is
   mostly UI surfaces and one real refactor: `Mixing.*` has no audio choke
   point.

---

**A GREEN RUN COULD NOT SAY HOW IT PASSED, AND THAT WAS TRUE OF 35 NUMBERS.**
`companionSight` came back green on `efff6fc` and reported **nothing** — because
`atRecruit` and `waited`, written an hour earlier for the sole purpose of
telling "she was there and saw nothing" from "she never arrived", both went
inside the gate LABEL, and a verdict prints labels only for FAILING gates. So
the run where the fix works is silent about how, on the one gate whose whole
problem was passing on luck for twenty-two runs.

Then the grep, and it is not one instance: **35 of the 39 named quantities
inside gate labels appear nowhere on a green run.** A whole diagnostic channel
that only opens once something is already broken. The sim prints `ALL GATES:`
every run now, green or red, and the companion distances moved to the
always-printed done-line as well.

**NEXT, and it needs two or three landed runs first (rule 2):** promote those
label keys from gate-only to REQUIRED in `verdict-keys`. Deleting `atRecruit`
from a label would then be caught. Not done blind — some labels build their
text conditionally and I do not yet know which keys are stable.

**PANEL DUMP, READ: two faults, both fixed, neither visible from the C#.** The
ledger screen said `"Mitch says it was player"` four times — the raw subject id
in a sentence a person reads, beside a line ten lines away that says "Novak"
correctly. And the DOUBT trail printed the same sentence three times for two
different people, because it took the last three ENTRIES and one repeated event
had filled the whole window. `idLeaks` gates it and names the sentence;
`RecentReasons` collapses a run and says how often.

**DO NOT `--learn` THE 8 NEW VERDICT KEYS YET.** Six are the appearance probe
and are real. `S` and `tail` are fragments of the traffic sentence that the
colon fix already removes — learning them would demand keys the next build
deletes, which is the exact false alarm that fix exists to prevent. Learn after
a build carrying the colon fix lands.

**THE PLAYER READS AS UNDRESSED, AND THE NUMBER THAT SAYS WHY WAS ALREADY
PASSING.** `bodyCoatArea=1.000` and `bodyParts=[Beta_Joints:29.6%->coat
Beta_Surface:70.4%->coat]` — the coat covers **100%** of the body, head to
feet. That metric was built to prove the coat is APPLIED, and it is green while
describing the fault exactly: one flat material with no separation between
coat, trousers, skin and hair, which is what makes the figure read as a
mannequin next to blocky but clearly-dressed NPCs. `bodyReadSat=0.510` against
`crowdReadSat=0.699` is the same thing in pixels — the player is the least
colourful body in the frame.

**REVERSED BY THE CORRECTED PROBE, AND THE MATERIAL-ZONE BUILD IS OFF.** That
"least colourful body in the frame" reading came from a crowd number that was a
pixel-weighted mean over three bodies — one near-camera body setting it almost
alone. With 24 bodies each contributing one reading and the comparison against
their median, `f06075e` says: player luminance 10.8 against a crowd median of
19.5 in a range of **4.0 to 62.9**, player saturation 0.374 against a median
0.564 in a range of **0.18 to 0.82**.

The player is in the lower half on both axes and **comfortably inside the
crowd's spread** — not an outlier and not the palest thing on the street. So
what reads as undressed is the SHAPE: a smooth anatomical mesh among blocky
clothed ones. **No wardrobe, palette or material-zone change touches that**, and
a week of colour work would have been spent on a hypothesis a corrected
instrument refutes in one run. It points at the textured models, which is
`BODIES.bat`.

**And `bodyReadLum` is not comparable across runs** — 35.7 on one, 10.8 on the
next, with no change to how the player is measured. The probe runs on every
shot and the last one wins, so one number came off a noon frame and the other
off midnight. `bodyReadWhen` names the frame now. Player-vs-crowd within one
run is unaffected; that was always the comparison.

**Landed and green: `0eeee6d`, `efff6fc`, `6ca5db4`, `180f626` — four in a row.**

**CONFIRMED ON `180f626`, and each of these was unreadable this morning:**
`idLeaks=0` — no rumour calls the player by their database key any more.
`doubtShown=3 doubtHeld=24 doubtWho=Lena` — Lena carries twenty-four reasons
and the panel shows three DIFFERENT ones, where it used to show one sentence
three times. `companionAtRecruit=9.2` against the 23.8m that made the gate red,
`companionDist=4.2`, `deedWaitedDays=0` — the escort is recruited near, so the
two-day wait never has to fire. That gate is green for a REASON now, and the
distinction between that and green-by-luck is what the whole `ALL GATES` repair
bought.

**`textVisibleAtAway=130` EQUALS `textVisible=130`,** so the worst
facing-away instant was also the busiest instant and the ratio is honest: 65 of
130 visible world texts face away at that moment. With `textMirrored=0` that is
`Cull Back` doing its job, not a fault.

**NOT YET READ, and do not read them as a regression without a series:**
`billboardsStale` went 5 → 27 and `billboardWorstDeg` 157.9 → 160.9 between two
green runs. Both are run PEAKS, which is the statistic that just turned out to
be unable to tell sixteen bubbles from a hundred and sixteen. Wait for
`bubbleOverlap`'s series to land and give billboards the same treatment before
touching anything.

---

**RESOLVED — `companionSight` on a commit that changed no code.** It failed
with `dist=23.8m` on a queue-only edit, twenty-two runs after it last went red.
A gate that fails on identical code is measuring luck.

The distance probe named its own answer: its comment asked for exactly this
number — *"if it comes back at forty metres the explanation is settled; if it
comes back at two, the fault is somewhere else entirely and I would have fixed
proximity for nothing."* Twenty-four metres settles it. The escort was recruited
by WALKER-LIST ORDER, wherever she happened to be standing in the city, and the
deed was staged before she had walked over. The roadmap's claim that this was
fixed covers only the earlier half — she knows where the player is now, and
knowing does not teleport her.

**Fixed in `efff6fc` and building:** recruit the nearest eligible walker, and
make the deed wait for her — with a two-day timeout, because a deed that waits
for ever stages nothing and `deeds=0` fails four other gates for a reason none
of them could name. `atRecruit` and `waited` are in the label so "she was there
and saw nothing" and "she never arrived" stay different findings.

Everything below is read off `7dc6334`, which is green.

1. **THE DROPS: `jobsDone` 1 → 2, and the trace names both remaining causes.**

       d1:MISSED[from=18m nearest=2.8m@01h]   d2:done[from=6m  nearest=2.1m@22h]
       d8:MISSED[from=8m  nearest=8.4m@22h]   d12:done[from=15m nearest=1.4m@00h]
       d13:MISSED[from=16m nearest=7.0m@23h]

   d12 was a miss before the loiter fix and is a delivery now. **d1 simply ran
   out of night** — eighteen metres at 22:00, 2.8m by 01:00, against a 2.5m
   radius, so it was thirty centimetres and one hour short. Not a broken check;
   the hour stamp is what proves it. **d8 never went at all** — its closest
   approach EQUALS its starting distance — and `beats=[… evening_d8 …]` is why:
   an authored evening beat outranks the job in the sim's target selection, the
   same collision the loiter had. **That one is a design question, not a bug:**
   a player would face the same choice between an evening scene and a night
   drop, and whether "evening" should be allowed to run into 22:00–02:00 is
   Jafar's call. Do not quietly re-rank it.

2. **THE SHADER IS CLEARED — BUT NOT BY THE RATIO I QUOTED.**
   `textMirrored=0` is the evidence and it is sound: no text is facing away
   while off the culling shader, so `Cull Back` works and **I misread the
   picture**. What was backwards will have been a speech bubble, which skips
   `WorldText` deliberately and therefore skips its cull.

   **The 47% I quoted alongside it was not a legitimate figure.**
   `textFacingAway=70` and `textVisible=149` were independent run-peaks — the
   frame with the most text facing away need not be the frame with the most text
   in it — and I wrote "read the RATIO" onto this queue about two numbers that
   could not be divided. `textVisibleAtAway` is captured with the numerator now.
   Third instance tonight of peaks-from-different-instants, and the second in my
   own code. What was backwards in
   `review_day5_night` will have been a speech bubble: those deliberately skip
   `WorldText`, which means they also skip its `Cull Back`, and they are the one
   kind of world text in this game that draws its own reverse. That is written
   into `SpeechBubble` now. The fix, if the number ever says bubbles are being
   read backwards, is a third shader with LedgerText's cull and the built-in's
   depth behaviour.

3. **THE REDIRECT RAN IN THE GAME.** `redirected=1 pointedAt=kest
   pointedOnDay=9`, and `redirectRelief=0.00` at the end of a seventeen-day run
   because the relief decays over four days — which is the mechanism working,
   read eight days later. M21's law-as-a-tool is now a complete verb end to end.

4. **THE WATCHED SPOT IS GENUINELY WATCHED.** `crowdedWatchers=39
   crowdedIsWatched=True` against `quietSpotWatchers=0`, so `disposal` and
   `accident` finally compare a place somebody can see against one nobody can.
   Both green.

5. **THE SLAM RINGS NAME THEIR OWN CULL.**
   `slamRings=[#1:shadowed@81m #2:drawn@62m #3:shadowed@81m #4:drawn@62m]` —
   two of four drew, and the two that did not were **shadowed**, at 81m against
   the drawn pair's 62m. So `perception`'s one red run was four slams that all
   happened to land shadowed. The fix is to PLANT one where the ring is not,
   never to loosen the bound — and the radius difference says where to look.

6. **TRAFFIC: `clamps=10 clampsPerKm=0.23 tailsBehindStart=0`.** The corrected
   tails metric reads zero, which is what it should read when `Cross`'s entry
   check is doing its job, and the clamp rate is a tenth of the bound measured
   from CoreTests. `gap=0.00` remains the clamp's signature at sample time.

6b. **READ `bodyReadLum`/`bodyReadSat` AGAINST `crowdReadLum`/`crowdReadSat`.**
   *(CI)* New probe, and the point of it: `bodyCoat` says the player's coat is a
   solid denim blue while the noon frame shows a figure that reads as bare
   plastic. Both are true — every existing body metric asks about the MATERIAL
   and none asked what the pixels come out as after the grade. A player who
   reads as dressed sits in the same range as the clothed people around them.
   **A comparison, never a threshold:** the bound does not exist until the
   series does, and the bounding box around a person contains pavement, which
   biases both readings the same way and is exactly why they are only compared
   with each other.

6c. **THE `[panel]` DUMP HAD ONLY EVER SHOWN ITS FIRST SCREENFUL.** It truncated
   at 1400 characters from the start, and LIABILITIES alone — twelve rumours at
   ~120 characters — fills that. So DOUBT, THE STREET and both competence lines
   added tonight have never been readable through the one channel that can read
   this game. It keeps both ends now and drops the middle. **Re-read the panel
   when the next build lands; most of it is being seen for the first time.**

7. **STILL OPEN AND NOT YET LOOKED AT:** `collidingBubbles` against
   `bubblesOnScreen` (sixty-six confabs is sixty-six bubbles, and the night
   still has two drawn through each other); the review camera standing inside a
   street sign; and speech-bubble
   decluttering.

   **CORRECTION: the Empire IS saved.** I wrote here and in a commit message
   that "the whole Empire — crew, cuts, rackets — is absent from `SaveCodec`",
   off a grep of the wrong file. `SaveCodec.Capture` takes an `extra`
   dictionary, `GameController.ExtraFlags()` puts `{"empire", Empire.Capture()}`
   in it, and `EmpireBook.Capture` writes businesses, crew, cuts, rackets, arms
   and the seed. What was genuinely missing was only the two fields added an
   hour ago, and they are in now with a round-trip test.

8. **Jafar runs `BODIES.bat` ~10:00 CEST**; reminder fires 07:55 UTC. Then the
   skinned crowd, costed and designed, worth far more once six textured models
   are in.

8b. **THE THIRD COMPETENCE BRICK — RESEARCHED, NOT GUESSED, AND IT IS NOT THE
   SHAPE I EXPECTED.** The design note's third example is *"do this one yourself
   because the lad would botch it and four people see your face instead of
   his."* The obvious build is a face-count: yours against your crew's. **The
   game already collapses that distinction and is right to.** A witness to a
   runner's round files `new Fact("player", "racket_<id>_d<day>", "seen")` — the
   SUBJECT is the player, and the rumour text says so out loud: *"{runner} was
   working a {racket} round for the new owner."* The street connects your people
   to you, which is the whole premise.

   What actually differs is CONFIDENCE: `0.45 + 0.35 * (1 - runner.Competence)`,
   so a capable runner produces a weaker link to you and a clumsy one a stronger
   one. That is already a good mechanic and nobody has ever seen it.

   **So the brick is not "count faces", it is "how much of what the street holds
   about you came from you being seen, against your people being seen".** Both
   populations are in the mill and separable by predicate — the night job's
   facts against `racket_*`. Two numbers and a sentence, and the delegation
   decision finally has a visible price.

9. **Keep retiring the reach ledger** (71). What is left is mostly UI surfaces
   and one real refactor: `Mixing.*` has no audio choke point.

### Answered tonight, kept only as evidence

- **The "list order standing in for a real criterion" sweep is DONE — two real
  sites, both fixed, and the rest are correct.** After the companion recruit
  turned out to pick by walker-list position, CLAUDE.md's new corollary says to
  grep for the shape rather than wait to trip over it. The second site was
  misattribution: every witness was handed the same arbitrary walker to be wrong
  about, so eight misnamings in a run all pointed at one person chosen by list
  index. It reads the mill now — whoever a witness holds their strongest rumour
  about is who comes to mind. Everything else that looked like it (`Arms[0]`
  twice in the ledger panel, `EllisInterviews[0]`, `OpenTargets.FirstOrDefault`,
  `Hosts[0]`) is either a max-scan SEED, which is the correct idiom, or a
  genuine first. **Nobody needs to run this hunt again.**

- `billboardsStale=5 billboardWorstDeg=75.2`, all 54 re-aimed at shot time —
  every still ever committed had been drawn with the previous frame's aim.
- `bodyCoat=[denim hsv=0.60/0.36/0.59 rgb=96,118,149]` — **reversed me.** The
  player's coat is mid-blue, not grey; a JPEG through a noir grade made it look
  like bare plastic and I was one step from re-rolling the palette. What
  survives is a judgement for Jafar: it still READS as undressed at noon.
- Traffic: `gap=0.00` on a third of runs is the de-overlap clamp, proven by
  `gapWhy` showing leader tail and follower nose at the same metre. The gate
  reads clamps-per-metre now. The 39 "tails behind an edge start" were my own
  metric counting a bus being long; `Cross`'s entry check is reached and works.
- `verdictSane` required job-nights from an outfit that had cut the player off.
  11% of runs end that way and `jobRan` had been passing on luck in six of seven.
- The flakiness table had no time axis and ranked `bodies` — fixed 60 runs ago —
  as the third-worst live gate.
- `verdict-keys` reported 465 measurements missing from a build that never ran.

## Next

**CORRECTED — "raise the population" and "make the street busier" are two
different changes and this queue conflated them.** `CrowdWalkerCap = 12` bounds
how many bodies are out of doors within earshot, whatever `CityPlan.Count` is,
and it was set from measurement rather than ambition: at 3,000 residents there
were 333 people standing within 34m of the bar door, so the caps were not
thinning a crowd, they were choosing 28 out of a mob and spawning every one on
top of the player. Raising the count from 700 to 1,400 buys FAMILIARITY — 43.5
distinct faces a week against 47.4 — and changes the frame not at all. Whether
a dozen people in a plaza reads as a street or as a demonstration is a judgement
for Jafar off a still, not a number for me to move against a measured decision.


6. **Raise the population instead of cutting districts.** Measured, and it
   reverses the plan: seven districts at 1,400 people gives 43.5 distinct faces
   a week against 47.4 for three at 700, and 2,100 beats the cut outright. What
   is NOT measured is whether a fuller city still reads as a port rather than a
   crowd — that is a question for a still. Change the headcount, look, decide.
7. **Tier the cast — and the runtime is not the constraint.** All three sides
   measured. Design: 47 distinct faces a week, 13 near enough to read, a knee at
   ~50 people covering 92% of a resident's week. Witnesses: no fewer than ~20
   near an event. Runtime: 68 rigs cost 1.1ms of a 12ms budget. **The machine
   does not bound the cast at fifty; only authoring does.**
8. **M17.2 voices** — no longer held. The writing verdict came back 78 and the
   risk it was gating (paying to voice something that needs rewriting) is
   retired. Note this is a SPEND and Jafar has not authorised it.
9. **Six cards still lack example lines**, down from sixty. Small, local, no key
   needed to identify them.

- **IS FIFTY-SIX CONVERSATIONS A RUN TOO MANY?** A judgement about how
  talkative a street should feel, which is Jafar's off a still and not mine
  off a number. The history: 16–42 a run (mean ~24) under the old flat-3.0m
  road test, 7 after the walking pace slowed, and 56 now the test asks about
  junctions instead. So the junction rule is more permissive than the old one
  was even before the regression. It is defensible — the old test was
  rejecting 96% of pairs by asking for something the world never produces —
  but "defensible" is not the same as "right", and the number that decides it
  is how the street READS, not how it counts. Worth a look at the night still
  once the speech bubbles stop overlapping.

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
- **Any further API spend.** The 3 August authorisation covered two tasks, both
  done, ~£0.85. Nothing else is approved and nothing else gets spent.

## Done, kept here only until the next tidy

- The upside-down player, closed by looking at the frame: two independent
  faults in our own rig, both fixed, a figure on its feet in the noon still.
- The nameplate that measured 2,119 times the frame height — the screen-rect
  helper projected two diagonal corners of a rotating box. Now 0.825.
- The rest days were never unrun; I read screenshot filenames as run length.
- Parallel builds; the work queue and its checker; the Tier-2 generator's
  thirteen writing rules with a no-key self-test; example lines for 54 of the
  60 generated cards; the conversation probe and a measured 78; per-character
  geometric cost; M19 input parity.

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

- **PLANT A COMPLETED DROP, so `jobRan` proves the pipeline instead of the
  bot's luck.** The gate says `JobsDone >= 1` and means "a drop can be made end
  to end: posted, walked to, completed, paid, laundered". What it measures is
  whether the bot won a footrace. Across 64 runs the outfit cuts the player off
  on seven, and on six of those `jobsDone=1` cleared the bound by accident — so
  the gate has been passing for the wrong reason far more often than it has
  failed. **Deliberately not loosened**: accepting "cut off before any drop"
  would let a run that never exercised the drop pipeline pass silently, which is
  rule 6 exactly. The fix is to make one drop reliably complete. `[series] jobs`
  now prints each drop's day, the distance when it opened and the closest the
  bot got, which says whether it was walking and ran out of night or never went
  — read that before choosing a mechanism. Prime suspect is `frameWorstMs=43666`:
  one forty-three-second frame crosses 02:00 while the walk gets a single step.
