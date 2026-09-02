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

- **RUN 3 IS THE NIGHT RUN, and it starts on the push that lands this file.**
  The sentinel `production/d1-probe/RUN-IMAGEGEN` carries `limit: all` and
  `max_minutes: 240`; the push trigger fires imagegen plus one cheap
  core-tests run on ubuntu-latest and nothing else. Landed under the ruling
  `game-design/decision-2026-09-02-imagegen-run3-banked-means-in-the-commit.md`.

- **RULE 9 HOLD, in force from the landing push until the night lands.**
  `ledger-pc` is one PC and a batch running is a Unity build waiting.
  DISPATCH NOTHING at `ledger-pc` until a commit whose subject reads
  `Meridian pictures from <sha>` CONTAINS the landing commit. That means the
  Windows build, the Unreal probe, the MSVC setup and the vignette fetch all
  wait. Check ancestry, never branch movement: capture the landing sha, then
  `git merge-base --is-ancestor <landing-sha> <pictures-commit>`.

- **READING ORDER when the night lands, and the order is the point.** Open
  the pictures before any number (rule 4). Then read, in this order:
  1. `imagegenVerdict=` and `wroteThisRun=` on the verdict's done line.
  2. `pathsWithAChange=` and `alreadyInHead=`. These are what run 2 could not
     say. BANKED with `pathsWithAChange=0` means the night added nothing to
     git no matter how many pictures the GPU made, and NOTHING-NEW exits 1
     deliberately so that case cannot read green.
  3. `skipped=` against `remadeUnrecorded=`. `skipped=14 remadeUnrecorded=0`
     is the hand-recovered `made.json` proven correct; a non-zero
     `remadeUnrecorded` means recovered rows did not match and GPU time was
     spent making what already existed.
  4. `blank` counts with their denominators, then `attribution=`, which read
     `failure` on run 2 and is still undiagnosed.

- **WHAT RUN 2 SETTLED, so nobody re-litigates it.** The stopper is gone
  (`stopper=none shaFrom=checkout`), all four work steps ran, and generation
  used the GPU for real. What run 2 could NOT say was whether anything
  reached the repository, which is the single thing run 3's verdict is now
  built to answer. Queue 045 is LANDED.

- NEXT ACTION after the night: queue 046, the assets are not in the frame.
  Ordered ahead of generating more pictures.

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
