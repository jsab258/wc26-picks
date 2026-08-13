# The work stack

> **STATUS — LIVE**, verified 2026-08-04. What gets picked up next, in order.
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

### LIVE SPEECH — WHERE IT STANDS, 13 AUGUST

**PROVEN.** The three whole-line graphs run on Jafar's card and produce a
voice he approved by ear twice — one line, then five in two voices, a
line ~5.2s for 4.1s of speech. **GUIDANCE STAYS AND SHIPS** (`--rows 2`,
the exporter's default): no-guidance is 1.5× faster per STEP and loses
it per LINE, because the model without its second opinion generates more
tokens for the same words — "No." came out 19 tokens guided and 46
unguided, which Jafar heard blind as "slowed, stretched". This file said
the opposite for a day and I quoted it forward on 13 Aug before checking
`1c2afb2`, which is rule 1 exactly: my own doc is not evidence.
Startup is 38s, not the 178 this file
claimed for a day (the four-step solver cut it and nobody re-measured),
and the cause is 1.3GB of weights rather than DirectML (CPU opens it in
39.5s) or graph optimisation (disabling costs 59s). It blocks nothing
now: opening moved off the main thread.

**THE C# SIDE HAS NOW MADE A SOUND — 13 Aug, `csharp-speaks-3`.** For
the whole project until this run, `speechStarted=0 speechSpoken=0` in
every recorded verdict and `speechNoModel` in the dozens: the game had
asked for live speech and been refused for want of a model every time,
because no build ever had one, and Python driving the graphs is not the
game driving them. `SpeechBench` now opens `OnnxSpeech` — the game's own
backend class — and runs `SpeechLoop.Run`, the game's own decision loop,
against the real graphs on the RX 6700:

    loop stop=Finished tokens=80 steps=81 seconds=1.57 usable=True
    decoded 76800 samples = 3.20s of speech in 2.80s

3.2s of audio for 4.37s of work, and it is a real waveform: peak 27857,
rms 2702, 43% near-silence, which is what speech with pauses looks like.
Awaiting Jafar's ears — it speaks Rocco's Thursday line, the same one he
approved whole and rejected streamed, so the doubling fault has a direct
comparison.

**TWO NUMBERS FROM THAT RUN WANT READING.** The bound step is FLAT —
`pos10=17.2 pos100=17.4 pos200=17.3 pos400=17.2`, fit `17.3ms+-0us/pos`
— against the host path's `35.1ms+157us/pos`. Long lines therefore cost
no more per step than short ones, which is the thing device-resident KV
was for. And decode came in at 2.80s where the Python whole-line path
measures 1.6s; the obvious suspect is first-call warmup on the decode
graph in a fresh process, and it is a suspicion, not a measurement —
the bench decodes exactly once so it cannot tell warmup from cost.

**WHAT IS STILL UNPROVEN: any of this inside Unity.** No build has ever
carried the graphs. `put-voices-in-build.py` (landed 13 Aug, selftested
both ways) drops them into a downloaded build — the step nobody had
written and the reason every build so far fell back to the bank. It has
not been run against a real build yet.

**STREAMING IS CLOSED.** Block attention makes a chunk's audio final on
the small model exactly, but on the shipped weights the render moved
1.8 of full scale, the doubling Jafar heard SURVIVED, and the voice
went robotic. These weights are offline-trained whatever the code
retains. Full account in `chunked_attention`'s docstring. It buys
nothing today anyway: five chunks cost 7.9s against 1.7s whole. fp16 is
dead too — no faster, and overflowing.

**THE CAST IS FOUR SHORT and the reason was a layer back**: Aldous,
Danny, June and Zlata had no entry in the voice FETCHER, so no clip
could be fetched and no voice picked; each drew a crowd voice silently.
Entries added 13 Aug, and the fetch is queued as `fetch-four-voices` —
the corpus is 403 from this container, so it runs on Jafar's machine,
which is also the half that does not need him. **What is left for him
is the half that does**: open `tools/voice-fetch/ledger-voices-out/`'s
page, listen, type four numbers into `picks.txt`, run `--install`.

**THE BANK'S "HOLES" ARE MOSTLY NOT HOLES — 13 Aug, measured.** This
item stood for days as "53 of 381 asked lines had no clip, generation
work, not yet costed", and the premise was wrong. Most of those misses
cannot be rendered by anybody.

`VoiceBank.ClipName` keys a clip by (voice, EXACT text). A gossip
TELLING is built by `StreetVoice.Exchange` as a template plus
`{what} = Trim(r.Summary)`, and the summary is itself assembled at run
time — `"someone in a runner's coat — maybe Sam — was handling a package
past midnight"`, plus the address, plus the vehicle. So every telling of
a real rumour is a sentence nobody has ever rendered, and the space is
unbounded rather than merely large.

What the bank actually holds, counted: 336 atomic lines × 6 street
voices = 2,010 clips, all on disk and correct. **42 of those 336 are the
`exchange.tell.*` family and every one is instantiated with a single
specimen rumour** — "the new owner was at the warehouse on Tuesday" —
so their 252 clips can only play for a rumour that says exactly that.
`Recognition` and `Ambient` are literal throughout (zero interpolations
between them, checked) and are genuinely banked. The pair slots' halves
are all present as atomic lines: 2,268 pairs checked, 0 missing.

So the rumour half of the street — the part that says out loud what the
social memory remembers, which is the moat — **can only ever be voiced
live.** That is not a scope decision to take; it is what the pipeline
is, and it is why live speech is load-bearing rather than a garnish.

**THE NUMBER NOW SAYS WHICH KIND OF MISS IT IS.** `speechNoClip` kept
its meaning and its landed series; `speechNoClipComposed` is the share
that could never have been rendered, carried on `SpokenLine.Composed`
from the one site that composes. What is left is the real backlog, and
until a run lands nobody knows how big it is — it may well be zero.

### Startable right now, ORDERED BY WHAT SHOWS ON SCREEN

1. **THE FIRST PLAYER-HEIGHT FRAME (dfefd62) FINDS THREE THINGS NO
   ELEVATED STILL COULD:** the RAIN fills the sky as dense dark
   scribble at eye level — far too many streaks, far too long, a
   player-facing weather fault the top-down view flattered; the street
   plates do NOT stack from player height, so the nameplate-heap item
   collapses to a review-camera artifact and the declutter is vindicated
   (managed-labels peak 6, orphans 0); and the pink figure reads as
   ERROR-SHADER MAGENTA on one body variant — a missing material, not a
   pose. Next: thin/shorten rain streaks judged against this frame, and
   name the magenta body's material (the census's who-fields will carry
   it once its material check looks for magenta too).

1. **A T-POSED FIGURE THE ARM MEDIANS CANNOT SEE.** *(on screen)*
   `review_day1_night.jpg` (b01ea7d): a figure in pink, both arms straight
   out, on a street `armStreet=10.7/armStreetWorst=15.3` calls healthy —
   the median-across-bodies blind spot again (the worst is a max over
   medians). One frame, one body: a hypothesis. The number: per-body count
   of arms within 5 degrees of horizontal held over a second, emitted as
   `tposeBodies` with the body id. **RETRACTION, 13 Aug: every tpose
   number so far was INVERTED** — the latch read `< 5` from straight
   DOWN, counting hanging arms held still. Both bucket stories void,
   corrected to hold above 75, and the pink still is the only real
   evidence until the recount lands. (The capsule half closed into the
   census item above; the nameplate-heap half closed into item 1, which
   shows plates do not stack from player height.)

1. **THE FRAME GATE IS THE ONLY LIVE RED, AND IT IS THE GAME'S OWN TIME.**
   Latest split: game 16.7ms against its 12ms budget — bodyLod 3.8,
   traffic 3.6, npcs 3.0, mix 2.3, rigs 2.0. bodyLod is a once-a-second
   FULL pass (spike, not steady cost) — spreading it round-robin is the
   obvious move BUT its verdict counters assume one atomic pass
   (duplication, injury, primitive counts per sweep); split the
   measurement from the sweep before splitting the sweep, or every
   count becomes a peak over partial passes. CI timings are the wrong
   machine for tuning; treat this as spike-shape work, verified on the
   PC.

   `gates --flaky`: `frame` has failed 28 of 141 runs and is red on the newest.
   Everything else is quiet — `perf` last failed a run ago, nothing else in
   sixteen.

   **Read the breakdown, not the mean.** `mean=483.7ms` is a software
   rasteriser and says nothing; `game=17.55ms` against `gameBudget=12ms` is a
   46% overrun in OUR code and it is a real number on a real machine.
   `bodyLod=4.39 traffic=3.72 sun=3.15 npcs=2.77 rigs=2.06 population=1.32`.

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
