# The work stack

> **STATUS — LIVE**, verified 2026-08-03. What gets picked up next, in order.
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

1. **READ `billboardsStale` AND THE FOUR STILLS.** *(CI, in flight on 4ac2f0f)*
   `review_day5_night` prints two rumour lines across the frame BACKWARDS while
   `textMirrored=0`, `speechUpDot=1.000` and `nameTagsUpDot=1.000` all say the
   text is fine. Cause: bubbles aim in `LateUpdate`, `Shot` renders from
   `Update`, so **every still ever committed was drawn with the previous
   frame's aim** — a third of a second of camera movement at `meanFrame=334ms`.
   The aim is one implementation now and `Shot` re-aims before rendering.
   `billboardsStale` is how far out they were BEFORE the fix; it should be
   non-zero and the mirrored text should be gone from the frame. **Look at the
   frame first, then the number.**
2. **READ `bodyCoat`.** *(CI, same build)* The player reads as a bare mannequin
   in `day2_noon` and `day5_noon` while `bodyCoatArea=1.000 bodyClothed=True`.
   Both can be true — the meshes are painted, and painted a near-neutral. The
   coverage metric asks whether a coat material reached every mesh; nothing
   asked whether that colour is a coat. **If the band comes back grey or stone,
   it is a decision, not a bug:** the street identifies the player as "someone
   in a runner's coat" in its own rumours, so the protagonist rolling a neutral
   is a writing problem too. Do not change the palette off the JPEG.
3. **READ `[series] jobs` AND `cutOffNights`.** *(CI, same build)* One run in 64
   came back `jobsDone=0` and reddened `jobRan` and `verdictSane`. The
   distribution across every kept run: 49 finish 2/3, eight finish 3/3, **six
   finish 1/4 with the outfit cutting them off, one finishes 0/3** — so 11% of
   runs lose the outfit and `jobRan` survived six of those on luck, because the
   bot had scraped one drop in first. `verdictSane` is fixed (a cut-off outfit
   posts nothing, so those nights are unachievable exactly like frozen closes —
   the same subtraction sitting three lines away). `jobRan` is deliberately NOT
   loosened; see standing work.
4. **Read `collidingBubbles` against `bubblesOnScreen`.** *(CI)* The night
   still has two speech bubbles drawn through each other. Fifty-six confabs is
   fifty-six bubbles. `NameTags` already has the declutter and `Manages`
   already draws the line — offer bubbles to it, but **only once the number
   says how bad it is**.
5. **Read the `[panel]` line.** *(CI)* The ledger screen's live text now goes
   into the verdict. Everything built tonight ships into that panel and none
   of it has been read back yet.
6. **`claims[made=0]` — fix landed in 0ef0b10, not yet in a landed verdict.**
   *(CI)* `ProcessClaim` hung off the LLM-backed engine, which is null in the
   sim; it is `Claims.Process` now and `LawHost` calls it directly. Every
   verdict up to 264d29f predates that. **Read `claimWhy` when the next one
   lands.**
4. **Jafar runs BODIES.bat ~10:00 CEST.** README opens with the three steps;
   reminder fires 07:55 UTC.
5. **Then the skinned crowd — costed, designed, item 4b below.** Worth far
   more once the six textured models are in.
7. **THE FLAKINESS TABLE — AND THE TABLE ITSELF WAS THE THIRD THING IT
   CORRECTED.** `python3 tools/gates.py --flaky` had no time axis, so it
   reported `bodies 6/64, 9.4%` beside `claims 22/64` and I wrote "bodies is
   the biggest untouched one" onto this queue off the back of it. All six
   `bodies` failures are from a hundred-minute window on 3 August — the runs
   during which the upside-down player was being repaired — and the forty
   runs since have all passed. It was the most thoroughly FIXED thing in the
   project, ranked third-worst. Rule 3: suspect the instrument. It now reports
   how many runs ago each gate last went red, and splits live from quiet:

   | rate | last red | gate | note |
   |---|---|---|---|
   | 23/66 | 1 run ago | claims | fixed in 0ef0b10; first green verdict is dc42046 |
   | 4/66 | 8 runs ago | traffic | **I called this a one-off. It is not.** Now prints its five readings |
   | 1/66 | 3 runs ago | jobRan | real coverage hole — see standing work |
   | 1/66 | 3 runs ago | verdictSane | fixed — a cut-off outfit posts nothing |
   | 1/66 | 10 runs ago | perception | open — 32 glances, nobody stayed to notice |
   | 2/66 | 13 runs ago | harm, disposal, accident | harm fixed; the other two await `crowdedWatchers` |
   | 5/66 | 20 runs ago | allegiance | fixed — the run never poached anyone |
   | 13/66 | 22 runs ago | companionSight | fixed — the escort had no player reference |
   | 1/66 | 36 runs ago | confab | moot — the old total-failure gate, and there are 66 confabs |
   | 6/66 | 60 runs ago | bodies | fixed with the rig; `worstAt` in flight in case it returns |

   **`traffic` at 8 runs ago is now the oldest LIVE one and the real next
   target.** It used to say nothing but its name; it prints five readings now.

6. **Keep retiring the reach ledger.** 90 to 77 tonight, every one wiring
   rather than building. What is left is mostly UI surfaces
   (`OperationPlan.Bringing` needs crew selection) and one real refactor: the
   `Mixing.*` voice budget has no choke point to enforce it, because the audio
   layer plays through several `AudioSource`s directly. That is a design job,
   not a wiring, and it is the honest reason those five entries survived
   tonight.

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
