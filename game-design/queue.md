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

### NO RED. The newest run is `pass=True` with no failing gate at all.

**Perception is fixed and the fix is confirmed, not hoped for.**
`slamRings=[#1:drawn@62m #2:drawn@61m #3:drawn@62m #4:drawn@58m]` where every
previous run had `noring` or one lucky draw in four. The cause was arithmetic:
a street that talks at 58 swallows a door at 55, and the sim spent all four of
its chances inside somebody else's sound. The slam now waits for a gap.

**`slamsDeferred=1188` is the number to keep.** That many ticks wanted to slam
and could not, which says a quiet moment on this street is genuinely rare. It
is also the honest denominator for anyone who later reads four clean draws and
concludes the world is quiet.

**`jobRan` came back green on its own**, which is what a 3-in-99 flaky gate
does. The `held:` tally is in flight and is still the thing to read — a green
run does not tell you whether a probe was stealing the bot on the red ones.

### THE BODIES ARE UNTEXTURED FOR A REASON NOW NAMED, and it was not the one
### I fixed first

`materialImportMode = ImportViaMaterialDescription` was the first try and the
per-body report says it was not enough: every body has materials — Michelle 1,
Remy 6, The Boss 4, thirty across ten models — every one on the Standard shader
and every one `notex`. The materials import fine; the textures never arrive.
Checked on disk too: no `.fbm` and no `Textures` folder anywhere under
`Assets/Characters`, so nothing has ever unpacked the embedded media.

Explicit extraction is in flight, with a force-reimport after it so materials
can bind to assets that did not exist when the model was last read.

**That round trip was earned by the report disagreeing with me.**
`bodyKeptMats=0` alone would have sent me back to the importer a second time.

### SETTLED — the night-still text heap is speech, not nameplates

`namesTracked` peaked at **0** across the whole run, `collidingNames=0`,
`worstNamePair=[none]`, and the worst overlapping world-text pair is a street
sign against a copy of itself. The frame's illegible text is **speech bubbles**,
and nothing in this codebase has ever measured how big a piece of world text
gets.

`worstNameFrac=0.306` is honest and answers the wrong question: at
`worstNameCentreMetres=1.21` with `worstNameBoundsY=0.29` the arithmetic checks
out, so a label genuinely 1.2m away IS a third of the screen tall. Both names
and bubbles now carry a median and a sample count beside the peak. **No
threshold until the series lands.**

And `namesTracked=0` sat beside `nameTagsActive=43` in the same verdict, which
cannot both describe a working instrument. `textWalked`, `textProjected`,
`bubblesTracked` and `namesManagedEver` are the denominators that separate
"nothing survived the filters" from "nothing was ever offered".

### SETTLED — the eight bodies landed

`bodyChoices` 5 -> 10, all eight registered with valid human avatars. The noon
frame shows the player as a real human mesh with proper limbs and a walk pose;
the foreground walkers were still box mannequins at that point, and everybody was one flat
colour.

`bodyKeptMats=0` says why: `RealBody` keeps a renderer's own material only when
it carries a texture, so zero kept means no material on any body has one. The
textures ARE in the files — counted by PNG signature, Michelle 4, Remy 22,
Sophie 6, Joe 6, Martha 6, The Boss 3, Big Vegas and Sporty Granny 1 each, and
only the two stand-ins have none. Nothing in the model importer has ever
mentioned materials, so every body imported on an unchosen default. Fixed and in
flight, with a per-body material report so the next build says which half failed.

### DONE — the walkers are not boxes any more

Kept only for the hazard, which is the reusable part. `RealBody.TryAttach`
publishes `Attached`, `Why`, `Upright`, `Skinned`, `Dressed`, `Kept`, `Parts`,
the coverage fractions and the bind and scaled pose readings — and FIVE clauses
of the `bodies` gate read those meaning THE PLAYER. Anything that attaches a
body which is not his must go through `TryAttachExtra`, which saves and restores
every one of them. Attaching without that makes all five describe the last body
attached, silently, and a corrupted gate reads exactly like a passing one.

Awaiting its first build; `walkerBodies` is the number that closes it.

### NOTORIETY IS HEAT WEARING A SECOND NAME — decomposed from M21, no CI needed

The roadmap says "a number that gates doors, with no press and no reputation
events". Read the code: **the gating half already exists and the driver is the
fault.**

- `Access.KeyKind.Notoriety` gates doors on `s.Notoriety`, and has for weeks.
- `AccessHost` feeds it **`Notoriety = CurrentHeat`**. That is one variable
  under two names — the fault the rules picked up this morning on the music
  layers, in a completely different system.
- `Violence.Notoriety(witnessCount, killed)` — the real "how notorious was this
  act" model, with the comment *"a brawl outside the bar at noon is the day's
  news; the same fight in an alley at three is a sound somebody half-heard"* —
  is unit-tested and **has no game caller at all**.

**Why it matters rather than being tidy.** Heat is how hot you are RIGHT NOW and
it falls when the police lose interest. Notoriety is how KNOWN you are and it
should not fall for the same reason — a famous man stays famous after the heat
dies. Wiring them together means a door that opens because the law stopped
looking, which is the opposite of what a reputation gate is for, and it means
the player can never build the one thing an empire needs.

**The work, and it is Core-shaped so it needs no round trip:** give notoriety
its own accumulation — it rises on notable acts through `Violence.Notoriety`,
witnessed deeds and denouncements, and decays far more slowly than heat. Then
`AccessHost` feeds it that instead of the heat it currently mirrors.
`CoreTests` can prove the two diverge, which is the whole claim.

**Check the roadmap row when it lands** — it currently describes a gap that is
half closed and half misdiagnosed.

### RED — the frame gate, and the walker bodies did it. THIS LEADS.

**44 walker bodies attached, 0 failed, and the noon still shows a street with
no boxes in it.** That is the change working. It also broke the frame budget and
the series says so unambiguously rather than by suspicion.

`meanFrame` over 111 landed runs: median 342, quartiles 334/340/347, never once
above 369. The two newest are **570 and 668**. That is outside everything the
project has ever recorded, so it is not runner noise.

| | before | after |
|---|---|---|
| game (attributed) | 7.92ms | **13.37ms** against a 12ms budget |
| rigs | 1.08 | 2.33 |
| traffic | 1.72 | **3.78** |
| sun | 1.72 | 2.77 |
| npcs | 2.45 | 3.10 |
| render+rest | 307 | 557 |

**READ THE TABLE BEFORE ACTING ON IT.** Traffic more than doubled and the sun
went up 61%, and neither has the faintest connection to skinned meshes. That
rules out "the bodies cost game CPU" as a complete explanation and points at the
thing this runner does: **it has no GPU and software-rasterises everything, so
rendering competes with game code for the same core.** When render cost rises,
every wall-clock game-side timer inflates with it. `game=13.37ms` is therefore
NOT a clean game-side number here, and the gate is attributing to game code a
cost that is mostly render.

**So do not loosen the budget and do not "optimise" traffic.**

**AND THE GEOMETRIC NUMBERS WERE ALREADY THERE — I said they were missing and
they were not.** They also settle it, and they say the cost is REAL rather than
an artefact:

| | before | after |
|---|---|---|
| skinned renderers | 1 | **221** |
| skinned bones | 52 | **8,353** |
| skinned vertices | 16,338 | **1,037,694** |

A million skinned vertices a frame, up sixty-three-fold, across 44 bodies —
about 23k each, which is what a Mixamo character costs. **That is genuine work
on any machine, GPU or not**, so the earlier reading of "mostly render
contention" was half right and the wrong half was the comforting one. The render
cost rose because there is sixty-three times more skinned geometry to render.

That makes the LOD answer not a nicety but the actual fix, and it now has a
number to aim at: eight nearby bodies would be ~190k vertices, which is the
order the rest of this scene is built at.

**The decision this actually poses:** 44 simultaneous skinned bodies is the
named cast, which was the deliberate choice. The proper answer if it is too many
is LOD — real bodies for walkers near the player, mannequins beyond — because
the cast size should not be bounded by a frame budget when only a handful are
ever on screen. Walkers currently choose their body at SPAWN, so that is a real
change rather than a constant.

**The work, and it is now specific:** walkers choose their body at SPAWN, so LOD
means swapping at runtime — attach a real body when a walker enters the near
band and drop back to a mannequin when it leaves. `Population` already bands
people and `CrowdWalkerCap` already bounds the near set, so the machinery to ask
"who is close" exists; what does not exist is a body that can be exchanged
without losing the rig's state.

### Startable right now, in order

**The 12:03 build answered four of the five questions that were in flight, and
the run is `pass=True` with no failing gate.**

1. **THE NAME HEAP — my last diagnosis was WRONG and the impossibility survives.**

   I said `namesManagedEver` was frozen by being captured on a sparse sampler,
   moved it to the run end, and **it still reads 24 against 42 offered in one
   frame.** Every offer adds to the managed set, so that cannot be true, and the
   explanation I gave is not the explanation.

   What was found instead, while checking: the four text counters were
   LAST-WINS while the three bucket counts printed beside them are PEAKS.
   Consecutive runs swung `textProjected` 111 to 48 and `textInvisible` 277 to
   346 — nothing changed except where the last shot pointed. All five are peaks
   now, so the next reading is the first where they can honestly be compared.

   **Do not re-diagnose from the current numbers.** They are a peak and four
   last-wins values that were never taken at the same moment, which is why three
   readings of this metric have now produced three wrong answers.
   The denominators settled it: 391 texts walked, **260 rejected as invisible**,
   95 projected, `namesTracked=1` — on a run whose day-2 noon still has a dozen
   names piled illegibly in the corner. `Renderer.isVisible` means "rendered by
   ANY camera last frame", not "in this camera's view", and the review camera
   has not rendered when the measurement is taken. Replaced with a real frustum
   test in both `CollidingNames` and `SpeechBubble.Rects`. **The next run's
   `collidingNames`, `nameFracP90` and `bubbleFracP90` are the first honest
   readings of any of them** — every earlier value was taken over a population
   that excluded the frames with heaps in.
2. **FOOT IK — the ray is innocent, read `ikPlantedMedian` next.**
   `ikWorstHit=[Road_10]` and `ikGroundMissed=0`: the ground ray finds the road
   every time, so the body's own capsule — the suspect that was plausible enough
   to act on — is not it. The animated foot really is off the ground, half a
   metre at worst and about a fifth typically.

   The overall median cannot accuse anything, because a SWINGING foot should be
   off the ground and the blend correctly asks for no correction there. The
   planted-only median is the discriminating number and it is in flight.

   **Suspect, named before the reading so it cannot be fitted afterwards:**
   `Rig.PlantBlend` is driven by `CharacterRig.Phase`, the PROCEDURAL gait
   phase, while the foot comes from a Mixamo clip with its own timing. Two
   independent clocks for one idea — the shape that has already cost this
   project the arms, the billboards and the ground raycast twice each. If
   `ikPlantedMedian` comes back near the overall median, that is it, and the fix
   is to derive the plant from the foot's own height rather than from a phase
   that knows nothing about the clip.
3. **THE DROP IS FIXED — 4 of 6, up from 2 of 5.** Making the bot run while a
   drop is open did it, and the traces confirm the mechanism rather than just
   the outcome: `d12` covered 22.2m in 13 ticks where walking managed 1.15m per
   tick, and two drops that opened at 3m and 7m completed in 2 and 3 ticks.
   Planting the condition, not loosening the bound.

   **The predicted side effect happened and was already counted.**
   `nightRunNotices` went 143 to 320 because there is now a second reason to be
   running; `dropRuns=214` is how many ticks that was, so the two can be told
   apart. That number was added in the same commit as the change precisely so
   this would not read as the night-run probe going haywire.

   **The 30cm case is CHECKED and it is not a braking bug.** `d13` missed at
   2.8m against a 2.5m radius, and the obvious suspect was the approach easing.
   Read it: `want *= Clamp01(far / 2f)`, so the bot moves at FULL speed at any
   distance above two metres and 2.8m is nowhere near the taper. It walked 20.9m
   of a 22m approach and the window closed while it was still moving.

   So it is a timing boundary rather than a mechanism, and there is nothing to
   fix in the bot. **Do not widen the completion radius** — that is the gate
   measuring itself. If it recurs, the honest lever is which day the drop is
   posted on, not how close counts as close.

4. **THE WALKER BODIES ARE WIRED — read `walkerBodies` and `walkerBodiesFailed`.**
   Done 2026-08-04 with the trap cleared first: `TryAttachExtra` saves and
   restores every static `TryAttach` publishes, so the five `bodies` gate
   clauses keep describing the player. Named cast gets skinned bodies, crowd
   keeps mannequins by choice, heights come from `Physique.For` so the variety
   survives. **Not done until the numbers come back**: `walkerBodies=0` with
   `walkerBodiesFailed` high means the prefab pick is failing;
   `walkerBodyWhy` names it. Watch `heapMb` and the geometric counts, not a
   millisecond figure — the runner has no GPU. Gait bias, bad leg and idle
   phase are carried across from `Physique.For` now, so the street should NOT
   walk in unison — check the noon still, because that was the one way real
   bodies could have read as worse than the boxes they replaced.
5. **`heatMedian`** — decides whether the street pinned at maximum unease is a
   music problem or a harness one.
6. **`measureFails`** — all four failing prose labels are named now, not one.
7. **Keep retiring the reach ledger** — 43, and every remaining reason was
   verified against the code today.

### SETTLED by the 12:03 build

- **The textures work.** `bodyKeptMats=1`, `bodyParts=[nothing to paint — all 1
  renderer(s) came textured]`, and the noon still shows a properly textured
  figure — skin, hair, a white top, yellow trousers — where yesterday she was a
  flat blue silhouette. Extraction pulled 54 textures from 10 of 10 models.
- **The ratchet fix holds.** The bodies gate passes the run that fixed the
  bodies instead of failing it for not having been painted over.
- **Foot IK is running**, first time: 2,299 frames, both feet, no undriven
  frames, and the IK pass really is enabled.
- **The compile outage is over.** One wrong type name rode 18 commits and killed
  4 builds, each dispatched to answer a different question.

---

## What last night settled, in one line each

Full accounts are in the commit messages; this is the index, and it is here
only so a reader does not re-open a closed question. **Anything with a number
beside it was measured, not judged from a still.**

- The ledger screen called the player by their database key in four rumours,
  and printed one repeated reason three times where three different ones fit.
  Both fixed and confirmed green.
- The escort was recruited by walker-list position, twenty-four metres away;
  she is picked by proximity now and arrives at nine.
- The third competence brick is a WEIGHT, not a face count, and it runs: thirty
  rumours from your own face against two from your crew.
- `ALL GATES` prints every run, so the 35 diagnostics that were readable only on
  a failing run are readable on a passing one. Confirmed landing.
- A comment took the build step past a hard size limit and broke dispatch
  outright; `workflow-size` now catches that at commit time.
- Bubbles are fine — 166 samples, median zero overlapping pairs. The peak of
  116 was a real crowd pile-up, not the normal state.
- The camera never stands in front of the player: twenty shots, zero blocked.
  Three stills' worth of eye-judgement about foreground clutter was wrong.
- Overhearing exists: an alibi told to one person is now heard by whoever is
  close enough to make out the words, capped below knowledge.
- Twenty seconds of watching somebody now carries an identification floor into
  what they witness. It never did.
- The grade cools when the player is exposed and warms when hidden — written,
  tested and unwired since it was written.
- **`workflow_dispatch` does not pin a commit.** Four builds were dispatched at
  named shas and none of those shas was ever built. Watchers must ask whether a
  run CONTAINS the commit, not whether one is named after it.

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
