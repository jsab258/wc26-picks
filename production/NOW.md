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

## Two decisions Jafar made on 2 September, and the work they owe

**THE ENGINE TIE-BREAK NOW GOES TO UNREAL**, reversing the standing rule.
With the deadline already retired, this is the second half of one direction:
he wants the visual ceiling and is willing to pay the loop for it. What
would reopen it is NOT a tie, but the Unreal loop proving so slow the
ceiling is never reached in practice, which is queue 032's measurement.

**D12, INFORMATION SURFACES** is recorded at
`ledger-v2/respec/decision-register/D12-information-surfaces.md`. The
player's own memory is fully surfaced in an in-game Ledger; NPC minds are
NEVER ground truth, only the player character's evidence-bounded model with
confidence levels; divergence between model and truth is intended design
space; learning what people know runs through diegetic verbs that are
themselves perceivable acts.

A DIRECTOR SPAWN IS OWED ON BOTH AND HAS NOT HAPPENED, held only by the
budget stop below. It is one spawn, not two. What it must work through:

- What "ties go to Unreal" changes in the D1 record and the decision rule,
  and how a tilt toward one engine coexists with judging the pairs blind.
  Those can both hold and a later reader will assume they cannot.
- What D12 reorders. If the information layer is the moat rather than a UI,
  the queue's current order was set before that was written down.
- D11 IS MISSING. D12's judgment-legibility clause cites it; the decision
  register holds D4 to D9, and a repo-wide grep outside legacy/ finds no D11
  and no D10 record, though verify.py cites D10 by name. Either they were
  decided outside the repo and must be written down, or something is
  misfiled. Ask Jafar rather than reconstructing them.

## Budget: STOPPED, and what clears it

17 percent at 04:40Z, reported by Jafar. The week starts MONDAY 14:00 CEST
and the ceiling is 80 percent. The mid-week reset on 1 September was an
ANOMALY and must not be expected again.

THE DAY IS UNMEASURED, WHICH IS NOT THE SAME AS FINE. Since that reading:
six builder and director spawns, and a SESSION LIMIT HIT at about 09:20Z
that killed two agents mid-work. A session limit is direct evidence of heavy
use, and nothing in this container can read the usage page. The rule for an
unmeasured day is to prefer stopping.

SO: no builder, director or verifier spawns until Jafar reports a number.
ONE number in the chat clears this entirely.

WHAT IS STILL ALLOWED, because the scarce thing is Claude usage and not
wall clock: reading landed results, running `ledger/verify.py`, committing
and pushing finished work. A stop that leaves the tree dirty across a reset
saves nothing in the currency that is actually short. This was nearly got
wrong once today, which is why it is written down.

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
