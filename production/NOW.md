# NOW: what is in flight (read this FIRST, before the queue)

STATUS: LIVE. Verified 2026-09-02 00:40Z.

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

- **NOTHING IS RUNNING. THE STOP RULE IS IN FORCE.** `materialConnections`
  held at 12/14 across Unreal runs 19 and 20, and the 3 September ruling says
  that means stop dispatching and fix queue 062. NO FURTHER UNREAL DISPATCH
  until the UV chain is wired. A third run would render the same grey street
  and cost the same GPU minutes to say so.

- **PHASE C IS ONE WIRE FROM DONE, and run 20 proved which wire.** Staging
  landed 51 files in both directories the binary looks in
  (`stagedTexFiles=102/102 texRootFiles=51`), `mapsFound=36/48`,
  `surfacesResolved=12/16`, `piecesTextured=563/593`. Every number read what
  it was predicted to read. The frames are still FLAT GREY because the two
  refused connections are TexCoord into both component masks, the head of the
  UV chain all three samplers hang off, and a sampler with no coordinates
  reads one constant. 563 correctly textured objects rendering as flat colour.

- **THE D1 MEASUREMENT HAS PASSED and that is the bigger news.** An agent
  generated the Unreal base material head-less, no human opened the editor, no
  uasset was hand-made: `editorBuildExit=0 materialPythonPlugin=found/1
  materialScriptReturn=2 materialBase=loaded`. Jafar's amended rule makes
  agent-loop friction the decisive measurement, and it is passing.

- **A GATE THAT COULD NOT FAIL WAS FOUND AND FIXED.** The still gate grepped
  its own evidence file for `shotStatus=`, and the file's header comment
  contained that phrase while explaining the key. It read WROTE out of its own
  explanation whatever the frame was. Both ends fixed, and the repo swept: one
  `key=`-shaped comment survives and no reader can reach it. THE OBVIOUS TOOL
  FOR THIS SWEEP IS BLIND TO IT: `verdict-dupkeys.py` skips a key whose values
  all agree, and a header quoting the passing value agrees with a passing run.
  Queue 064 is the real instrument; the dupkeys work sits behind it in 029.

- **BUDGET: UNMEASURED AND WAITING ON JAFAR.** 52 percent at 04:50Z, then a
  builder, two directors, three Unreal runs and a morning of resident turns.
  Asked for a fresh number; not yet given. Condition 4 holds, so prefer
  stopping over opening a new batch.

- NOT DISPATCHED AND DELIBERATELY SO: `production/d1-probe/DISPATCH` is a push
  trigger. Do not touch it in a commit unless a run is wanted. Run 18 banked
  nothing because a resident push moved the branch sixteen seconds before its
  commit step; run 20's evidence landed because the branch was left alone.

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
