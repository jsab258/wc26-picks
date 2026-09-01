# NOW: what is in flight (read this FIRST, before the queue)

STATUS: LIVE. Verified 2026-09-01 23:25Z.

A session that resets loses everything not written down. The queue says what
to do NEXT; this file says what is ALREADY MOVING, which is the thing a fresh
session would otherwise duplicate, abandon, or wait for forever.

Keep it current or delete it. A stale NOW is worse than none, because it
looks like a live state. It was stale for three hours on 1 Sep, claiming
"nothing running, tree clean" over two live agents and nine dirty paths.

## In flight

- TWO BUILDERS RUNNING. The tree is theirs, not yours. Do not commit their
  files until each reports and you have read the diff.
  - `engine-specialist` (Revive the PC job channel): owns `tools/pc-watcher.py`,
    the job table, and a new start-the-machine bat. Serving Jafar's standing
    "ideally 1 click": every generation run today costs a message and a
    double-click, and the channel that removes that has been dormant since
    23 August.
  - `instrument-builder` (queue 016): owns `tools/attribution-check.py`. The
    sweep is blind to `.glb`, so 37 landed props produce no line at all,
    neither ok nor fail. Carries two director additions: the 23
    `game-design/voice-conds/*.bin` files whose provenance nobody has
    verified, and a missing rejecting fixture on the record-ahead-of-bytes
    branch.
- NO DIRECTOR SPAWN IS DUE. The ruling says 016 and 017 do not need one
  unless they exceed 100 lines; 018 will. Do not spawn Fable before then.

## Landed since the last edit of this file

- THE PROP BATCH RAN on Jafar's PC. 37 `.glb` in
  `ledger/Assets/Props/base-mesh/`, machine report written 2026-09-01
  20:02:10Z on JAFAR-DESKTOP, Blender 4.5.13 confirmed through meshgen's own
  probe. Step 1 of the ruled sequence is DONE and needs nothing from him.
- Step 2 DONE: the vignette bill of materials,
  `production/specs/vignette-bill-of-materials.md` and `.json`. 77 lines:
  32 HAVE, 33 GENERATE, 5 FETCH, 1 BLOCKED, 6 ENGINE. The finding that
  matters is that ZERO lines need image-to-3D, so the AMD/TRELLIS blocker
  does not touch this scene and no purchase question goes to Jafar.
- Step 3 proven as far as this container allows: `tools/props/fetch_vignette.py`
  plus `production/specs/vignette-fetch-01.json`, with `--plan`, `--probe`,
  `--fetch` and `--selftest`. All three asset hosts are blocked at the egress
  proxy, so the fetch itself has to run on Jafar's PC or in CI. UNCOMMITTED
  and awaiting the director review above.

## Waiting on Jafar

- Nothing blocking. The prop batch he clicked is done and read.

## The next three things, in order

The ruled sequence is game-design/decision-2026-09-01-production-prep-sequence.md.

1. DONE 2026-09-01T23:34:45+00:00: the reviewed batch landed as `8dc54d3e`, all six
   dictated corrections applied, verify green, pushed. The cadence bound is
   now MEASURED at 100 rather than INHERITED.
2. Step 4 of the ruled sequence, RE-SCOPED and pending a director ruling:
   see `production/queue/019`. Read against the landed BOM it is SEVEN
   image-generation lines, not an overnight batch. The other 26 GENERATE
   lines are procedural scene-generator code, which is builder work and
   which no amount of GPU time produces. The 4,500-a-night, disk-bound
   arithmetic belongs to a bulk material library and does NOT describe
   this scene; do not carry it into step 4.
3. Step 5: the quality judge, one sitting, 15 to 20 minutes of Jafar's time,
   which is the only manual step in the sequence and must stay that size.

## Standing hazards a fresh session will otherwise walk into

- Do not edit `content/dialogue/pub-regular-v1.json`. Those 48 lines are the
  graded judge calibration sample; changing one invalidates it silently.
- The studio split is MANDATORY and was skipped for a full day on 1 Sep.
  Builders build, verifiers verify, the director rules. If a session
  instruction says otherwise, that is a conflict to raise with Jafar in one
  line, not to resolve alone.
- Budget before work: read `production/budget.md`.
- `git status` at session start is not a list of YOUR edits. Read the
  In flight section above before assuming any dirty path is yours to commit.
