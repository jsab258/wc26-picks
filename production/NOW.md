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

IN FLIGHT RIGHT NOW: imagegen run 1. Queue 039's workflow and 027 Phase A
(the flat piece list, 546 pieces, three guards) were reviewed together and
landed under game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md.
Landing the batch pushed production/d1-probe/RUN-IMAGEGEN, and that push
IS the first imagegen dispatch: four signs on ledger-pc, zero Claude
points, 4.5 minutes if the weights are already on the runner's account and
a 7 to 10 GB download first if they are not.

## In flight

- Imagegen run 1, fired by the batch push. Watch by ancestry for a commit
  titled `Meridian pictures from <sha>`. Read, in this order, before
  opening anything: ledger/Assets/StreamingAssets/Decals/generated/
  imagegen-verdict.txt line 1 (the sha must be the batch's), the
  `done imagegenVerdict=` line (BANKED, BLANKS or NO-RUN with its why),
  then the run log's `runnerAccount=` and `weightsDirectory=` lines. Then
  open the four PNGs. A red is a finding with its cause in the verdict,
  never a broken runner. Run 1's own commit moves the cadence reference
  (queue 042 item 2 says why); expected, not a fault.
- NEXT ACTION, tomorrow: slot 1 is the 027 Phase A close-out (queue 040
  window practicals in Core, Phase A2 the feet file, queue 041 the
  acknowledgement key), one engine-specialist, one Unity dispatch at the
  end; the night frame will show THREE lit bays, not six, and that is the
  JSON applied. Slot 2 is 037. The report to Jafar after run 1 carries
  one of the four signs as its picture, or the verdict's why if red.

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
