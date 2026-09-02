# NOW: what is in flight (read this FIRST, before the queue)

STATUS: LIVE. Verified 2026-09-02 00:40Z.

A session that resets loses everything not written down. The queue says what
to do NEXT; this file says what is ALREADY MOVING, which is the thing a fresh
session would otherwise duplicate, abandon, or wait for forever.

Keep it current or delete it. A stale NOW is worse than none, because it
looks like a live state.

## Where this is, 2026-09-02: the rotation fix is in the tree, the second render is the proof

THE STREET VIGNETTE RENDERED ONCE, SIDEWAYS. Run 8f19add (landed 10:22Z)
drew all four stills with every piece turned 90 degrees: the engine-side
placement probe read datumMissing=521/845 against the plan-side 0/845
(game-design/sim-shots/runs/8f19add.txt line 97), which is the two-halves
instrument catching the emitter fault the 05:43 ruling had dictated a fix
for and the 06:26 batch committed without. The fix is in the tree under
game-design/decision-2026-09-02-rotation-fix-lands.md: yaw 0 is the
identity, lying pipes are rolled cylinders, the sun sits at Unity yaw 65
and not 205, and the pipe-count guard was watched red then green.

THE NEXT UNITY DISPATCH IS THE PROOF. Read, in this order and before any
still: placement datumMissing=0/845; the shapes line equal to the CoreTests
print (cylRolled=9 cylPitched=32 cylUpright=105); sun elevation=36.0
bearing=205.0 unityYaw=65.0 appliedYaw=65.0. Then open all four stills:
cam_B square to the parade with the roofline in frame, cam_A up the kerb
line into the fog with the parade on the LEFT (Unity is left-handed, so
facing +x puts +z on the left); day shadows toward bearing 25, which is
away and a little left in cam_A and mostly right in cam_B. A datumMissing
above zero or a float the crossfall does not explain is an emitter finding,
never a plan finding, and the run is not evidence about the plan.

## The D1 question: ANSWERED, and one still open

Jafar retired the timebox on 2 September ("forget the deadline, it's not
relevant... rather spend more time to get UE working"). D1 is bounded by
`production/budget.md` and by the attempt budget on queue 027, NEVER by a
date. Ruling: `game-design/decision-2026-09-02-d1-timebox-retired.md`.

STILL OPEN and on the dashboard: if the two engines look about the same,
which wins. The existing rule says Unity and nobody has checked that with
him. It matters more now, because removing the deadline makes "they look
close" the likeliest outcome rather than "Unreal ran out of time".

## Budget

17 percent at 04:40Z, reported by Jafar. The week starts MONDAY 14:00 CEST
and the ceiling is 80 percent. A session limit was hit at about 09:20Z and
killed two agents mid-work, so the day has cost more than the last reading
shows. The mid-week reset on 1 September was an ANOMALY and must not be
expected again.

## In flight

- Nothing running. The rotation fix is reviewed and landing.
- NEXT ACTION: dispatch `ledger-build-windows.yml` by hand on the branch,
  then read the three lines above in that order before opening any still.

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
