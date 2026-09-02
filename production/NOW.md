# NOW: what is in flight (read this FIRST, before the queue)

STATUS: LIVE. Verified 2026-09-02 00:40Z.

A session that resets loses everything not written down. The queue says what
to do NEXT; this file says what is ALREADY MOVING, which is the thing a fresh
session would otherwise duplicate, abandon, or wait for forever.

Keep it current or delete it. A stale NOW is worse than none, because it
looks like a live state.

## STOPPED FOR BUDGET. READ THIS BEFORE STARTING ANYTHING.

`production/budget.md` records the position: Jafar's newest reading is 8
percent, taken during the evening of 1 September, and TWENTY agent spawns
landed after it, three of them `studio-director`, which carries its own
weekly limit and counts double. Nothing in this container can read his usage
page, so the day is UNMEASURED rather than young, and the file's own rule for
an unmeasured day is to prefer stopping.

THE ONE THING NEEDED FROM JAFAR IS A NUMBER. Until he gives one: no builder
spawns, no director spawns, no verifier spawns. Reading landed results and
committing finished work are free and are allowed.

Midnight passing does not change this. The daily allocation is a discipline
laid over a WEEKLY limit and a UTC rollover hands nothing back.

## In flight

- Nothing running. Three builders and one director completed and their work
  landed in one reviewed commit under the ruling
  `game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md`.
- ON JAFAR'S PC, WAITING FOR ONE CLICK: `START THE STUDIO MACHINE.bat` at the
  top of the project. A `fetch-the-vignette-surfaces` request is queued for
  it. Clicking it fetches two CC0 surfaces, attributes them in the same run,
  and prints whether the watcher will start itself at sign-in. It also
  answers the dormancy question, which no amount of reading can: an idle
  watcher and a dead one are indistinguishable until a request exists.

## Waiting on Jafar

1. A usage number. This is the blocker.
2. One click on the bat above. Not blocking; the request waits.

## What the director ruled tonight, so nobody re-opens it

- The CLAUDE.md cut is SAFER than the file it replaced, and NOT YET SAFE. It
  landed under a condition: queue 020 gives the pointers and the casebooks an
  instrument. Until that exists the cut is trusted, not tested.
- Step 4 is FOLDED. The 26 procedural lines go to the D1b shared scene
  generator, which must exist anyway for the engine comparison. Step 4 is the
  seven 2D image lines, now queue 025. The "runnable tonight" claim was
  WITHDRAWN: `prompts.json` has no entry for any of the seven.
- `director_cadence` keeps measuring the TREE. Measuring the staged set would
  let a 459-line batch land as five 92-line commits. One exemption, 018(f): a
  commit whose staged set touches no work prefix passes, with the tree total
  printed beside the exemption, guarded by a new pre-commit hook.
- The agent log grows a `stop` event, ONE instrument for its three consumers,
  research first (queue 024). Step one is printing a payload nobody has read.
- Do NOT dispatch `make-the-pictures`. There is nothing to make yet.

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
