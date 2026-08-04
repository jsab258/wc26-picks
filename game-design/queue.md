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

### THE 17:00 BUILD ANSWERED FIVE THINGS AND CORRECTED ME ON TWO

**THE WASH WORKS, AND THE STREET STILL LOOKS LOUD.** Distance of the applied
wardrobe from white went to a median of 19.1, and the people wearing nothing
distinguishable fell from a predicted 39% of the roster to a measured 7.7% of
4,904 washes. Both halves landed. The noon frame still shows two women in
bright yellow trousers, so the rule is right and its ANCHOR is wrong: the wash
maps the wardrobe onto [0.45, 1.0], and a multiply capped at 1.0 cannot bring
a value-0.9 albedo under a 0.46 ceiling. `bodyAlbedo` now measures the sheets
being multiplied, once per model, so the ceiling can be set from evidence
instead of taste. **Read it before touching the constant.**

**THE SAMENESS HAS A NUMBER: FOURTEEN PEOPLE, EIGHT FACES.** Median 8 distinct
models among 14 bodies, worst 8 of 17. That is six duplicates in a typical
frame, and it is the first time the roadmap's two-day-old sentence has been
anything but a sentence.

**I WAS WRONG THAT THE PAINT PATH MIGHT BE DEAD, AND THE LIFETIME COUNTERS
SAID SO IMMEDIATELY.** `bodySkinnedEver=0 bodyDressedEver=736
bodyKeptEver=4904` — one renderer in eight IS painted with the wardrobe's coat
material, so the cast brightness lift is live on the crowd, not dead code.
Item 6 below is a real fault rather than a cleanup. Also `SkinnedEver=0`
across a whole run: nothing has ever been painted as flesh, which `BodyParts`
was written to do and wants its own look.

**THE FEET ARE FIXED.** Planted feet now sit 0.035 above the road against
0.046 for every frame — closer, which is the right sign. This morning it was
0.177 against 0.050, backwards. `ikPlantDisagreed=9785` says how big the old
error was.

**THE CROWD IS ESSENTIALLY THERE.** Median gap 0.42m against a body width of
0.45, from 0.30 five builds ago.

**AND THE FRAME GATE IS NOT WHAT I TOLD JAFAR IT WAS.** I said it was the
runner's software rasteriser and the game was inside budget. The gate reads
the game's half ONLY, so it is a real red — but the game's half is wall-clock
too, and across eight runs its share of the frame sits at 2.6-3.4% while the
absolute figure swings 11.4 to 15.7ms either side of the 12ms ceiling. A
369ms run and a 489ms run are the same game on machines a third apart. So the
ms reading is tracking the runner, which is exactly what moving the gate onto
the game's half was supposed to prevent. `gameShare` is printed now; the gate
is left RED and unmoved, because moving a bound to make red go away is the
thing CLAUDE.md forbids by name, and swapping in a share nobody has read a
series of would be the same mistake wearing a better statistic.

**THE BIN NUDGE WAS WALKING BINS THROUGH WALLS.** `dressedPulled=2
dressedWorstPull=3.75` read as the bound having been short. `Dressing.
WallOffset` is a constant 0.45, so a 3.75m pull put a bin 3.3m behind its own
face plane. The reach is bounded at the wall now and the next run will
probably read 0 pulled and 8 stuck, which is the honest answer:
`dressedRoadDepth` prints how far the carriageway runs out from each stuck
item's wall, as the whole series, and the fix is a level fix.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

**The order is Jafar's, 4 August.** He asked why a day looked like almost
nothing and the honest half of the answer was that most of it was invisible to
him. So the top of this list is whatever a player would notice, every time,
whatever state anything else is in. The full four rules are in CLAUDE.md under
AUTO MODE.

1. **WHAT THE STREET LOOKS LIKE — the wash ran, and a third of the city was
   wearing a multiply by white.** *(CI, in the next dispatch)* Two fixes ago
   the count was `bodyTinted=1` because the counter had been snapshotted and
   restored around every walker's attach. That was fixed and the count went to
   5,334, and the frame did not change — two women in the same bright yellow
   trousers, one of them the player.

   **The count was true and could not answer the question.** A wash of pure
   white is applied exactly as successfully as any other and changes no pixel.
   The wash took the band's hue and half its saturation at value **1.0**, and
   black is v 0.09-0.20 against grey's 0.26-0.44 at the same hue and the same
   saturation 0.02-0.10 — so value is the only axis separating a fifth of the
   city from a sixth of it, and value was the axis being discarded. Replicated
   over the real roster: **39% of people washed to within 5% of white.**

   Fixed in `Core/Wardrobe.Wash`, normalised against `MaxValue` so the
   brightest coat passes through untouched, with the floor taken from a swept
   series rather than a preference and a CoreTest holding both ends.
   `bodyWashWhite` / `bodyWashSampled` / `bodyWashNone` are the readings that
   would have caught it. **Judge it from the frame, then read the median.**

   Still true and NOT fixed by this: ten body models against forty-three named
   people means at least two people on screen always share a mesh. The wash is
   what has to carry the difference, which is why it mattered that it was doing
   nothing for a third of them.

2. **THE FEET — the fix is in flight and the test is the two drop medians.**
   *(CI)* Two runs agreed that the frames the blend called planted were
   indistinguishable from every other frame, which is the two-clocks answer.
   The plant now comes from the feet: the LOWER foot is the planted one, which
   needs no constant at all and is true of a run, a limp and a stand as well as
   a walk. `ikPlantDisagreed` says how often the old procedural answer differed,
   so the size of the fault is reported rather than claimed — and the two drop
   medians, which have landed on top of each other twice, should now come apart.

3. **THE CROWD STOPS STANDING INSIDE ITSELF.** *(CI)* The median gap between
   two people has been pinned near 0.30m against a body width of 0.45 for five
   builds, and the arithmetic says why: a walker counts as arrived within 0.2m
   of its scheduled point, so two people sent to the SAME point settle within
   0.4m of each other and the separation nudge fights the schedule to a draw. A
   place is now a small ring rather than a metre of ground, with each person's
   spot fixed by name. In flight. Read the median, and look at the night frame.

4. **EIGHT BINS ARE STANDING IN THE ROAD**, of 176 pieces of facade clutter,
   measured for the first time today. Vehicles are clean — that half of the
   same picture was disproved. Small, visible in a still, and the fix is a
   placement nudge rather than a refusal: rejecting placements on a bound
   nobody has read is the ratchet rule five is about.

5. **M21 — THE NOTORIETY ROW IS CLOSED; THE NEXT SUB-PIECE IS A SURFACE.**
   Landed 4 Aug: notoriety has its own accumulation and decay, two sources
   (violence and informing), a proven effect on a real door, a rival who RINGS
   you instead of a summit you travel to, and a newspaper — the one channel in
   this game with no hops, so an act can become known to people who were not
   there. All Core, all tested, all with callers.
   **What is left needs UI and therefore a round trip each**: a surface the
   player accuses somebody FROM, and the third answer to the rival's call —
   picking up and saying no, which needs a prompt because inventing an answer
   for the bot would put a decision the player owns inside the harness.
   The Core-shaped work that remains is M22, the shape of a playthrough:
   onboarding, pacing, replayability, succession. Entirely unbuilt.

6. **THE CAST BRIGHTNESS LIFT IS APPLIED TO THE WHOLE CROWD, AND IT IS NOT
   DEAD CODE — THE COUNTERS I ADDED TO CHECK THAT SAID SO IN ONE RUN.**
   `RealBody.TryAttach` lifts the coat's value to 0.68 with a comment saying
   "the player is a named character", and `TryAttachExtra` calls straight
   through it, so every walker gets it too. `Wardrobe.MaxValue = 0.46` exists
   precisely so nobody in the crowd outshines the cast, and the code walks
   past it for everybody.

   I wrote here that this was probably dead on today's models, on the strength
   of `bodySkinned=0 bodyDressed=0` — a LAST-WINS reading that describes
   whichever walker the LOD granted last and cannot support a claim about the
   run. The lifetime versions came back `bodySkinnedEver=0 bodyDressedEver=736
   bodyKeptEver=4904`: one renderer in eight is painted with the lifted coat.
   So this is live and visible.

   **What it needs and does not have is a cast test.** `VoiceBank.Cast` is the
   nearest thing and its own comment says its ids do not all match the roster,
   so borrowing it would put a silent mismatch in the wardrobe — a named
   character under one id would get crowd brightness and the same person under
   another would not. The honest shape is a flag through
   `TryAttach`/`TryAttachExtra`, except the named cast walk the street as
   `NpcWalker` too, so the call path does not separate them either.
   **Decide the test first, then wire it.**

   And a second finding sitting in the same numbers: `bodySkinnedEver=0` over
   a whole run means nothing in this city has ever been painted as FLESH.
   `BodyParts.IsFlesh` exists, is tested, has the sur-face fix in it, and has
   never once returned true in a build. That is rule 6 — built, tested, and
   not running.

7. **KEEP RETIRING THE REACH LEDGER** — 41 entries, three wired today. Each
   one retired is a public API that something actually calls.

   **AND READ THE ENTRY'S REASON, NOT JUST ITS NAME.** The ledger was
   reason-verified this morning and two more reasons were still wrong by the
   evening — the bus route and the cab ranks both described behaviour that has
   been running for weeks, when the actual gap was that nothing DREW a stop or
   a rank. The tool proves an API has no caller; nothing proves the sentence
   explaining why is still true, and a wrong reason sends somebody at work
   that finished a fortnight ago. That is now written into the ledger's own
   header.

8. **THE INJURED WALK LIKE THE UNINJURED ON THE TWELVE NEAREST PEOPLE.**
   `BadLegIsLeft` drives `Rig.Limp` through the procedural solve only, so a
   mannequin limps and a bought body does not — and the bought bodies go to
   whoever is closest. That is a GAMEPLAY signal going missing, not a
   cosmetic one: a beating is supposed to be readable off how somebody moves.
   Needs an additive Animator layer or an IK offset, which is a different job
   from the two one-liners that landed with it. **Do not wire it as one.**

9. **HEAD SCALE, SAME FAMILY, DIFFERENT DIFFICULTY.** `Mannequin` varies it
   0.93-1.07 by scaling a child transform. On a skinned mesh the head is a
   BONE, so holding a scale on it means writing to the humanoid rig every
   frame or the Animator overwrites it — `CharacterRig`'s own comments record
   that exact failure twice. Worth doing after the limp, in the same layer.

10. **AND CHECK THE CROWD GAP AGAINST THE NEW BREADTH BEFORE READING IT.**
   The gap gate compares a median spacing to a body width of 0.45, a single
   constant. Bodies are now 0.86-1.18 times as wide, so the widest person is
   0.53 and the narrowest 0.39, and a fixed 0.45 is a threshold that has
   quietly stopped asking one question. `crowdGapMedian=0.42` was read against
   the old world. **Re-read the number's question before trusting the next
   value** — this is exactly the "a number keeps its name when the question
   moves" case, and I have now shipped the change that moves it.

11. **THE NAME HEAP — AND RULE 2 NOW APPLIES TO IT.** *(CI)* The behaviour fix
   is in and is what mattered: duplicate offers made every duplicated label
   hide itself. The COUNTERS have now contradicted themselves twice.
   **If the next reading is still incoherent, delete them rather than explain
   them** — a metric nobody can interpret is worth less than the hours spent
   interpreting it, and no player will ever see this one. The four numbers now
   come from a single frame, which is the last explanation it gets.

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


8. **Raise the population instead of cutting districts.** Measured, and it
   reverses the plan: seven districts at 1,400 people gives 43.5 distinct faces
   a week against 47.4 for three at 700, and 2,100 beats the cut outright. What
   is NOT measured is whether a fuller city still reads as a port rather than a
   crowd — that is a question for a still. Change the headcount, look, decide.
9. **Tier the cast — and the runtime is not the constraint.** All three sides
   measured. Design: 47 distinct faces a week, 13 near enough to read, a knee at
   ~50 people covering 92% of a resident's week. Witnesses: no fewer than ~20
   near an event. Runtime: 68 rigs cost 1.1ms of a 12ms budget. **The machine
   does not bound the cast at fifty; only authoring does.**
10. **M17.2 voices** — no longer held. The writing verdict came back 78 and the
   risk it was gating (paying to voice something that needs rewriting) is
   retired. Note this is a SPEND and Jafar has not authorised it.

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
  bot got, which says whether it was walking and ran out of night or never went.

  **THAT HAS NOW BEEN READ, AND THE PRIME SUSPECT NAMED HERE IS DEAD.** The
  suspicion was `frameWorstMs=43666` — one forty-three-second frame crossing
  02:00 while the walk gets a single step. The traces disprove it: every
  approach reading is timestamped INSIDE the window, and the failures cluster
  in the 2–10m band against a 2.5m completion radius. This is a bot that walks
  most of the way and stops short, not one that runs out of night.

  **The misses split cleanly in two and only one half is fixed.** With the owner
  tally added, `d8:MISSED[nearest=10.6m held:loiter-hold=21]` showed a staged
  probe owning every tick of a window while the bot stood still — the loiter
  refused to START during a drop and had no guard on the HOLD that follows.
  Fixed, and `loitersCutShort` counts what it costs.

  The other half is not that: `held:job=20 nearest=9.3m` and `held:job=19
  nearest=6.9m` mean the steering was right for every tick and the bot still did
  not arrive. Ownership cannot tell "steered and walking" from "steered and not
  moving" — a conversation, a knockdown or a blocked path all read as `job`
  holding the target — so the window now counts PATH LENGTH. **Read `walked=`
  before choosing a mechanism.** `d2` covered 16.5m in 14 ticks and completed;
  `d13` covered 12.1m in 19. More time, less ground, and nothing yet says why.
