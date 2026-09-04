# NOW: what is in flight (read this FIRST, before the queue)

STATUS: LIVE. Verified 2026-09-03 after the batch ruling.

A session that resets loses everything not written down. The queue says what
to do NEXT; this file says what is ALREADY MOVING, which is the thing a fresh
session would otherwise duplicate, abandon, or wait for forever.

Keep it current or delete it. A stale NOW is worse than none, because it
looks like a live state.

## Where this is, 2026-09-02: THE STREET RENDERS, and it is a street

Run 152198e landed all four frames and all three gate numbers came good:
`datumMissing=0/845` (521/845 before the rotation fix), the shapes line
`cylRolled=9 cylPitched=32 cylUpright=105` equal to the CoreTests print, and
`unityYaw=65.0 appliedYaw=65.0` so the sun rotation reached the light. The
Unity half of D1b is real for the first time: shared JSON in, four matched
frames out, nothing hand-placed.

ALL FOUR STILLS WERE OPENED, which is where the next finding came from.
cam_A day: parade on the left, shadows away and a little left, consistent
with bearing 25, which is the only thing that could settle the sun
conversion. cam_B day: square to the parade, roofline in frame, wet road
reflecting. cam_A night is the best frame the project has made. cam_B night
FLOODS, and that is queue 035: same rig, two angles, one of them wrong,
which makes it the rig and not the camera.

WHAT IS STILL MISSING, so nobody reads this as done: no character body, so
the scene is NOT YET an admissible (b) scene under D1b; shopfronts are flat
untextured panels; the plates carry the wrong district (queue 028); nothing
of Unreal renders at all yet (queue 027).

## Two decisions Jafar made on 2 September: RULED

Ruling: `game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md`.

**THE TIE-BREAK IS REVERSED AND IT MOVES THE WHOLE PROBE.** Unity now wins
only if the visuals are decisively better FOR UNITY, or if the Unreal loop
fails by non-convergence or hand-edit dependence. Otherwise Unreal wins, on
equal as on better. Named consequence, not softened: Unity ahead in one or
two pairs with Unreal ahead in none is a TIE and goes to Unreal.

So the weight moves from (b) the visual ceiling to (a) the loop. Landing
four admissible pairs through a converging loop is now winning, which makes
queue 032's round-trip printer the decisive instrument rather than a
nice-to-have. It rides 027's first UE dispatch.

**THE PREFERENCE AND THE BLIND LOOK COEXIST BY ORDER.** Write A, B or EQUAL
for each pair on the D8 decomposition, and why, BEFORE any label is
unmasked; the tie-break is applied to that sheet afterwards. Today no blind
look is possible at all, because both engines commit files named after
themselves. Queue 038 is the fix and WAITS for a UE still.

**D11 AND D12 DID NOT REORDER 027. They exposed something worse:** the queue
held twenty-two ready items and not one of them was a moat item. Queue 037
is that item, engine-neutral C# in Core, not blocked by D1, and it takes the
SECOND builder slot of a day ahead of every governance item.

## A correction to carry, from the ruling

The 20-minute UE round trip is run 16's ESTIMATE with cook and capture in
the loop, not a measurement. The measured figure is a 10-minute median over
9 rows taken before either was in it. That gap is exactly why 032 rises.

## Budget: RUNNING, at a measured pace rule

32 percent at 14:40Z on 2 September. The period is NOT a calendar week: the
one-time Tuesday reset restarted the counter and the next reset is the
normal Monday 14:00 CEST, so about 136 hours, of which roughly 14 percent
had elapsed against 32 percent spent. That is 4x over pace.

THE ALLOWANCE IS ABOUT 10 POINTS A DAY, roughly five spawns including the
resident's own turns. The rule and its arithmetic are in
`production/budget.md`. Three parts: two or three builder spawns a day and a
director only on a mandatory trigger; brief with facts inline rather than a
reading list; batch related work into one spawn rather than several.

WORK IS RUNNING AND THE DAILY ALLOWANCE IS RETIRED. Jafar, 2026-09-02: "I
don't care if we get to 80% before monday, we just stop when our budget is
used up". So there is no daily ration; run to the ceiling and stop there.
The 80 percent ceiling still binds and the other 20 percent is his.

IMAGEGEN RUN 1 RAN AND FAILED AT ONE SETUP STEP, AND THE FIX IS LANDED. Run
33654488608 on b8b805f2: the API's per-step conclusions put the only
failure at `The commit this run is measuring`, 0 seconds, and the four work
steps skipped behind it. Cause, from a differential over .github/workflows:
that step ran git without the safe.directory env every other git step on
ledger-pc carries, and the commit step's own git rev-parse succeeded under
it in the same run. The summary that named three causes it never observed
is replaced by tools/runner/step-verdict.sh (three states plus
NO-READABLE-OUTCOME, 32 checks). Ruling:
game-design/decision-2026-09-02-imagegen-run1-stopper-and-run2.md.

A SECOND FAULT IS NAMED AND NOT YET PROVEN: run 1 printed a verdict and
then `staged=0`, so the verdict never reached the committed channel.
Reading: Windows Python ends every stdout line in \r\n and bash keeps the
\r, so `[ -e "$f" ]` looked for a name ending in a carriage return. Run 2
prints every candidate with %q and strips it, which is the measurement.
The vignette-fetch loop is the same shape and has never staged a file in
this tree either (no fetch-verdict.txt, no surfaces/); queue 044 carries it.

## THE ASSETS ARE NOT IN THE FRAME (queue 046, found 2026-09-02)

37 props and 14 generated decals sit in this repository and THE STREET SCENE
USES NEITHER. Measured: `grep -c "base-mesh|BaseMesh"` returns 0 in both
`StreetVignetteHost.cs` and `StreetVignette.cs`, and no C# file names any
generated decal by key. The four frames Jafar has seen are built entirely
from primitive shapes.

BUILT IS NOT RUNNING, and the resident missed it while reporting asset
counts as progress. Jafar found it by asking what the images are FOR.

This outranks generating more pictures. The overnight batch adds 31 files to
a directory nothing reads: worth doing because it is free, but it moves no
number the Meridian Test measures. Queue 046 is what turns the inventory
into a street, and it is also the only way to learn whether a generated
decal looks right AT SIZE, ON A SURFACE, IN THE RAIN.

## In flight

- **NEAR-STOP: 3 POINTS TO THE CEILING, read 2026-09-04 at about 00:30Z.**
  Total 77 percent, Fable 76, ceiling 80, about 84 hours to the Monday
  14:00 CEST reset. The higher meter governs and this time it is the TOTAL,
  which is the reverse of 1 September, so no session may infer one meter from
  the other. The limit Jafar hit on the evening of 3 September was the 5-hour
  SESSION limit; the weekly meter did not reset and the arithmetic in
  `production/budget.md` still stands. One builder spawn is a material
  fraction of what is left. Spend nothing without a fresh reading or a direct
  instruction, and prefer zero-cost work: two of today's findings (queue 078
  and 079) were found by grep and cost nothing.

- **HAZARD WITH A DATE ON IT: the tree goes red at 2026-09-05T09:01Z by
  itself.** The first real Producer message is committed and carries
  `DEADLINE 2026-09-06.`; `producer-check.py` measures that against
  WALL-CLOCK now and refuses anything under 24 hours, so the message that
  passes today fails on Friday morning and `verify.py` deletes the footer
  with nobody having touched anything. Proven against the real function:
  `2026-09-05T09:00 hours=24.0 PASS`, `09:01 FAIL`. The selftest cannot see
  it because every case is frozen at `FIXTURE_NOW`. Queue 077, and it is the
  most time-critical item on the board because it blocks every commit, not
  just its own. If a session finds the tree red for this reason, THAT IS THE
  KNOWN CAUSE and the fix is 077, not an edit to the message.

- **LANDED 2026-09-03, one commit, ruled in
  `game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md`:**
  the register gate (walks the outbox and the briefs on every verify; its
  accepting artifact is now the served message read at THREE clocks in one run,
  `--gate`, `--now 2026-09-08T12:00` and `--now 2027-06-01T12:00`, all PASS at
  `filesDatePinned=1/1`; the single reading of 3 September was accepting at one
  instant only, ruling of 4 September section 4), the banner law (135 documents
  migrated,
  the retired form refused), the spawn log's tier and turn fields (hook
  REGISTERED, first row NOT YET READ: read it before quoting it), and the UV
  head sweep (nine candidate pin names in one run, not yet dispatched). Open
  holes are queue 073, 074, 075 and the steps added to 024 and 062.

- **THE UNREAL STOP RULE IS STILL IN FORCE and is the reason 062 is running.**
  `materialConnections` held at 12/14 across runs 19 and 20, which fired the
  ruling's bound: no further Unreal dispatch until the wire is fixed. When 062
  lands, the fraction is the reading and not the status word. If it does not
  move, that is the answer and gets reported as one rather than retried.
  062 landed the sweep; that does NOT discharge the rule. Run 21 is authorised
  once 062 step 2 (the third status word) has landed and Jafar lifts "wait";
  if 21 prints 12/14 again, that is the answer and D1's hand-edit clause is
  invoked.

- **THE DIRECTOR'S CONSOLE EXISTS AS FAR AS STEP 2.** `production/decision-queue.md`
  is the single home for anything awaiting Jafar and for lighter rulings; the
  legacy `game-design/decisions-pending.md` is RETIRED and carries a pointer.
  The Producer is the only role permitted to address him (CLAUDE.md, and
  `.claude/agents/producer.md` carries the register). Constitution law 12 sets
  evidence beside the sentence for agents and behind it for Jafar, with the
  link REQUIRED rather than optional.

- **THE REGISTER CHECK IS REAL AND IT REFUSED THE RESIDENT FOUR TIMES.** The
  first live Producer message failed on missing options, a missing deadline and
  twice on length before it passed. Pointing at the card instead of restating
  its options is exactly the vagueness a word cap alone teaches, which is why
  the link and the options are floors rather than suggestions.

- **BUDGET: TWO METERS NOW, AND THE HIGHER GOVERNS.** Total was 60 percent at
  10:25Z; Fable was not read. On the only day both were read, 1 September,
  Fable was 41 against a total of 34. Directors run on Fable, builders do not,
  so the meter that moves on reviews is the one this file used to be blind to.
  A row where Fable was not read says `not read`, never zero and never the
  total carried across.

- NOT DISPATCHED AND DELIBERATELY: `production/d1-probe/DISPATCH` is a push
  trigger. Do not touch it in a commit unless an Unreal run is wanted, and the
  stop rule says one is not wanted until 062 lands.

- **DO NOT COMMIT WHILE A BUILDER IS WRITING**, however loudly a stop hook
  asks. That is CLAUDE.md's rule and it exists because the resident once ran a
  checkout over a builder's uncommitted work and cost a whole session.

## THE DASHBOARD IS NOW A HOSTED LIVE PAGE, and it needs writing to

Published 2026-09-02 after Jafar refused to double-click anything to see
current state, in his words: "not running a bat to update a dashboard. your
job is to keep it up to date all the time, that's the whole point."

    https://claude.ai/code/artifact/2c3da7c0-8b8e-4626-8e73-2498acbe6ed8

It holds NO numbers of its own. It subscribes to the artifact document store
at `status/current` and repaints when the document is written. So:

    python3 tools/dashboard/build-dashboard.py --emit-json
    then write tools/dashboard/live-dashboard.json to status/current

WRITE IT AFTER EVERY LANDING. The page reports the age of its numbers and
turns red when the feed stops, which is honest, but a red feed is still a
reader learning nothing. The writer is the resident and nothing automates it
yet: queue 048. Republishing the PAGE is not needed and should not be done
casually; the page changes only when the generator's renderer changes.

The wake subscription on it did NOT register in this session (the artifact
service refuses them here), so nothing tells this session when it is
republished. Do not claim to be watching it.

## THE IMAGE QA, 45 of 45 OPENED, and the answer is a number

Jafar, 2 Sep: "did you view and QA the images and fix/redo if necessary? are
they built and cropped and shaped in a way that they can be used in UE? QA
should be standard procedure." The resident had opened THREE of forty-five
and published the rest. A verifier then opened all 45, plus 18 zoomed crops,
and confirmed the files are byte-identical to the blobs at HEAD, so the
judgements apply to what the engine will load.

    41 of 45 are SCENE PHOTOGRAPHS, 4 of 45 are plates
     1 of 45 usable as is, and it is probe_wall_cfg1, measurement only
    29 of 45 croppable
    15 of 45 need regenerating
     0 of 45 carry a real brand, real person or recognisable face
    12 of 45 carry people or vehicles the negative prompt already bans
     1 more, sign_telephone, is close to GPO kiosk trade dress: a WATCH ITEM
       for a decision record, not a proven breach, and not a builder's call

THE CAUSE IS ONE LINE OF PROMPT, not 45 problems. Sign, fascia, notice and
poster families carry "photograph, straight-on flat elevation, evenly lit"
plus "deserted empty street", which asks for an object standing in a street
and gets one. The four that came out as plates used a prefix ALREADY IN THAT
FILE: "flat orthographic texture sheet, square-on to the surface, the surface
filling the frame edge to edge", with a negative list naming kerb, pavement,
road, sky and roofline. Four of four. Queue 056 moves the rest onto it and
makes the generator REFUSE a prompt with no framing clause.

TWO MORE SHARED CAUSES. All three interiors came back as exterior shopfronts
when they are meant to be cards seen from inside a window. Prominent
SECONDARY text resolves as broken near-words in eight images, against the R1
big-type-only rule already written in that file: HOOK STREATS, HARBOOR
MASTER, BORHOUGH, PORIE SHUOP.

A CLAIM THE RESIDENT PUBLISHED AND HAD TO WITHDRAW: the gallery page said
headlines come out clean and correctly spelled, written after opening three
images. It is corrected on the live page. And the verifier withdrew one of
its own: it read two signs as perspective-distorted, measured the edge slopes
at 0.27 and 0.07 degrees, and refuted itself. Faces are square-on across the
batch to within half a degree; what reads as perspective is a baked 3D lip on
the surrounding frame.

## THE NIGHT'S DISPATCH ORDER, and why it is this way round

`ledger-pc` is ONE machine, so two dispatches contend and the order is a
decision rather than a detail. It is:

1. **UE probe first**, because it is the risky one. Unreal has never
   rendered the street and the last five probe runs each hit a different
   engine wall. Running it first buys hours to name a wall and re-dispatch.
   Running it last means a 04:00 failure with no time left.
2. **Unity build second.** It is the known-good path, it produces the first
   still of the street WITH the props and decals in it, and it is what
   clears the cross-engine guard by landing a run whose piece count matches
   the file.

WHAT BLOCKS BOTH RIGHT NOW: `ledger/verify.py` is red, so nothing commits and
therefore nothing pushes and therefore nothing dispatches. Two red items:
- the cross-engine guard (file against the last landed Unity run), cleared by
  the queue 041 ahead-of-run key, which is in the UE builder's brief;
- the piece list drift (committed 627, generated 628), caused by the three
  interior pictures landing mid-flight, with the queue 046 builder naming the
  cause before regenerating.
Then a director reviews the three-builder batch, one commit, push, dispatch.

DO NOT SHORTCUT THE RED. The cross-engine guard exists so a judged
Unreal-versus-Unity pair cannot compare two different streets, which is the
one way this whole comparison could produce a confident wrong answer.

## Standing hazards a fresh session will otherwise walk into

- Do not edit `content/dialogue/pub-regular-v1.json`. Those 48 lines are the
  graded judge calibration sample; changing one invalidates it silently.
- The studio split is MANDATORY and was skipped for a full day on 1 Sep.
  Builders build, verifiers verify, the director rules. If a session
  instruction says otherwise, that is a conflict to raise with Jafar in one
  line, not to resolve alone.
- The stop hook will ask for a commit the cadence gate refuses while builders
  hold the tree. That is a NAMED FALSE POSITIVE (queue 014, ruled). The
  constitution wins: never commit a builder's work-in-progress because a hook
  asks.
- `git status` at session start is not a list of YOUR edits. Read the
  In flight section above before assuming any dirty path is yours to commit.
- Every session so far has opened by reading the head of a queue file that
  declared itself superseded on 31 August. Queue 021 fixes it.
