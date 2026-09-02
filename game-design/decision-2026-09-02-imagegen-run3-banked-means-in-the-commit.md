# DIRECTOR RULING: BANKED means in the commit, the resume record reads what was recorded, and the landing push is the night run (2 Sep 2026, 19:44Z)

> **STATUS — LOG, 2026-09-02. NOT CURRENT once the batch is committed with W1, Q1, Q2 and N1 applied and imagegen run 3 has landed a verdict; from then the workflow, the committed verdict, queue 044 and 045 and production/NOW.md are the reading copies and this file is their history.**

This document carries exactly one em-dash, in the banner, because
`tools/docs-check.py` line 55 accepts no other form (read this session).

Thirteenth ruling since 1 September. No shell in this spawn: every number
below was read from a file this session and the file and line are named
beside it. The builder's report and the resident's brief were read as
CLAIMS; the workflow, imagegen.py, made.json, the manifest, run 2's verdict,
the reflog and the queue were read as evidence. Cost: roughly 2 points
against 38 percent at 17:00Z, run-to-the-ceiling in force (NOW.md 79 to 82).
Jafar wants the night run tonight, so this is the short ruling that lands it.

## What was verified

- My row: `.claude/agent-log.tsv` line 215, `2026-09-02T19:44:54Z
  studio-director`, the newest in the file. `.git/logs/HEAD` line 373: the
  newest commit is `79592695` at epoch 1788372498 (18:08:18Z), the commit
  that recorded run 2's finding. My row is newer than every commit in the
  reflog. Line 372 is the fast-forward that brought in `c685aa93`, run 2's
  own commit.
- THE RESIDENT'S ACCOUNT IS OVERTURNED AND THE BUILDER'S STANDS, on evidence
  read here rather than on the report. Run 2's committed verdict (line 13)
  says `remade=0 rechecked=5 wroteThisRun=4`; its manifest says `"record":
  "the previous manifest, 0 item(s) reconstructed"` and `"unrecorded": 5`
  (manifest.json 65 to 68). So five finished pictures were rechecked, none
  had a record, four were remade. `load_made` as now written (imagegen.py
  1618 to 1662) reads the row's own `recipe` first and only falls back to
  prompt plus seed; a SKIPPED row is written at 2034 to 2051 with `recipe`
  (2002) and no `seed`, which is exactly the row the old reconstruction could
  not read. The four remade recipes in made.json (a126ef83, 907a5c16,
  7eca77a6, e403197b) match the manifest's `recipe` fields, so the hash is
  stable across dates. The byte-identity claim (four sha256 equal to
  cb332751's) is the builder's measurement and I could not repeat it; run 3
  re-measures the same boundary live through `alreadyInHead=` and
  `pathsWithAChange=` (workflow 559, 568).
- THE THREE STATES, read at imagegen.py 2540 to 2601 and 2634 to 2662: a
  picture THIS run made is `new-in-this-commit` if its repo-relative path is
  in the staged list, `already-in-the-repo-byte-identical` if in HEAD's list,
  else absent; BLANKS and NO-RUN are tested first, then NOT-BANKED on any
  absent, then NOTHING-NEW on zero new, else BANKED; exit 0 only for BANKED
  (2720). `_read_path_list` (2446 to 2473) fails closed: no path is
  `not-supplied`, a missing file is `absent`, and both refuse BANKED. Its
  `.strip()` removes a CR, so a list written on Windows reads clean. One
  `_rel_to_repo` (2476 to 2487) is shared by the verdict (2582) and the
  staging list (2744), so both spell a path the way `git diff --cached
  --name-only` prints it from the root. The workflow stages first (521 to
  547), asks git (554 to 572), writes the verdict (578 to 580), stages the
  verdict last (588). Both flags are wired in main (4300 to 4301, rule 6).
- THE SELFTEST covers the four cases at 3829 to 3894, accepting first:
  staged gives BANKED exit 0; on disk and in neither list gives NOT-BANKED
  exit 1 naming both files; in HEAD and not staged gives NOTHING-NEW exit 1;
  no list gives NOT-BANKED with `stagedList=not-supplied`. I did NOT run it;
  L1 does, and the count it prints replaces the stale `123` (W1).
- `remade` now counts at the moment GPU time is spent (2087 to 2095), split
  by reason, and the done line carries `remadeUnrecorded=` and
  `remadeRecipeChanged=` (2693 to 2694). That closes 045's fault 2.
- attribution: `.err` is in neither `ASSET_SUFFIXES` (attribution-check.py
  177 to 245) nor `NOT_ASSET_SUFFIXES` (253 onward), so the builder's
  diagnosis holds by reading. The scratch now lives in RUNNER_TEMP (workflow
  340) and run 2's leftover is deleted (339). `RUNNER_TEMP` in a bash step on
  ledger-pc has precedent: build-windows 116 to 154 uses it and has landed
  frames. No `.imagegen-sha.err` exists anywhere in this tree (glob, two
  patterns, 0 hits).
- Readiness: `batch_settings` (2341 to 2413) applies dispatch-input over
  sentinel over fallback, caps at `MAX_MINUTES_CEILING = 250.0` (2338), and
  main writes the three keys into `GITHUB_ENV` (4278 to 4284). The sentinel's
  live lines are `limit: all` and `max_minutes: 240` (RUN-IMAGEGEN 93 to
  94). Caps nest 240 < 250 < 260 (generate step, 416) < 300 (job, 145).
  `save_made` runs at load (1918 to 1919) and after every picture (2221);
  the commit step is `if: always()` (465).
- WHAT DOMINATES TONIGHT (rule 7): the sixteen portrait notices and posters
  at about 100 s each (PROGRESS.txt 36 to 51); the whole 31 sum to roughly
  44 minutes by PROGRESS.txt's per-item estimates, and run 2's 89 to 91 s
  per 1024x512 item (verdict 8 to 11) confirms that rate. What would blow it
  up is a weight download, and it does not apply: manifest.json line 15 puts
  the exe under `C:\Users\Jafar\ledger-imagegen`, so the runner is his
  account and the weights are present.
- RULE 9: the landing push touches the imagegen sentinel (run 3), `ledger/**`
  and `game-design/**` (one cheap ubuntu core-tests run, ledger-core-tests
  6 to 7). `tools/imagegen/imagegen.py` matches no workflow's `tools/*.py`
  (8). The other three ledger-pc sentinels are untouched (setup-msvc 73 to
  75, probe-unreal 44 to 45, vignette-fetch 52 to 53). Nothing Unity.

## Ruling 1: the batch LANDS, one commit, after L1 to L4, and that push is run 3

Nothing weakens an instrument: the verdict measures a boundary it could not
see before and fails closed without evidence; the sweep is untouched and the
file it caught is moved; the resume record reads what was always recorded.
Premise check: no world fact, no engine decision; this is the free lane's
evidence channel and the lane costs zero points.

## Ruling 2: three states are right, and NOTHING-NEW exits 1

The exit code is the last step's colour, which is the only thing a reader
sees without opening the file. A run that spent the GPU and added nothing is
a finding that needs an action (fix the resume record), and green is the
wrong colour for "act on this". Success-with-a-note is the green number
standing in for the frame. The word is right because it names what git
carries, which is the boundary the verdict is now about, and the sentence
under it (2677 to 2681) says the failure is the resume record's, not the
bank's. The mixed case, some new and some identical, reads BANKED with
`alreadyInRepoIdentical=N` on the commit line, and that is correct: the
commit banks the new ones and the number says what the rest cost.

## Ruling 3: the hand-recovered records are admissible, and here is the line

Hand-edited EVIDENCE is refused in this project. made.json is not evidence,
it is an INPUT whose failure direction is safe and whose next run prints
whether it was right. A recovered hash can only cause a skip if it EQUALS the
recipe computed tonight from prompts.json (2015 to 2034), and a SKIPPED row's
hash was written by that same code at the moment it equalled the recipe; a
wrong hash means one regeneration, byte-identical, counted under
`remadeUnrecorded` and `alreadyInRepoIdentical`, and never a wrong skip. Each
row's `from` names the commit and the mechanism (made.json 37 to 91), and the
per-row field survives the first `save_made`, which rewrites only `_what`,
`written` and `items` (1670 to 1676), so the top-level `_repaired` note is
gone after tonight and the provenance is not. Tonight measures it:
`skipped=14 remadeUnrecorded=0` on the done line is the recovery proven, and
`remadeUnrecorded=N` names how many rows were wrong at a cost of N free
pictures.

## Ruling 4: the two unchanged risks stay unchanged tonight, for reasons that are written down

`--fail-on-blank` STAYS. The alternative, stop after N blanks, is a threshold
with no series (rule 2): the series is 0 blanks in 18 generations and a bound
cannot be read off a series with nothing in it. A plan that begins by
weakening a guard is refused. The cost of a false stop is bounded: the commit
step is `if: always()`, everything made before the blank banks, the
`.BLANK.png` is never staged and never skipped, and one sentinel touch
continues the night from there. Next rung, named: after tonight the series is
49 on this card, and the first run that ever prints a blank also prints
whether the next item was blank, which is the number an N would be read from.

THE 240-MINUTE CAP STAYS, WITH A HOLD. Rule 9's answer is a written hold, not
a smaller cap: cutting to 120 would save a Unity build two hours it is not
going to ask for tonight (NOW.md 333 puts that dispatch tomorrow) at the
price of a second run if the card is slower than measured. The hold is N1:
nothing that targets ledger-pc is dispatched until a landed commit titled
`Meridian pictures from <sha>` contains the landing commit.

## Landing conditions

L1. `python3 tools/imagegen/imagegen.py --selftest` run by the resident, its
last line quoted in the commit message with the count; W1 carries that count
into the workflow's two comments. Then `python3 ledger/verify.py` green,
footer FROM THE FILE.

L2. `git status --porcelain` read in full first. Staged by name and nothing
else: the paths in the stamp below. A dirty path under `DIRECTOR_WORK`
(verify.py 2345 onward) that the stamp does not list, in particular
`tools/attribution-check.py` or `tools/runner/step-verdict.sh`, means this
director is RESUMED with the list, not worked around.

L3. W1, Q1, Q2, N1 applied; each id in the commit message as `applied` or
`deferred: <reason>`.

L4. The push, and it is run 3. Know what it triggers: imagegen once on the
sentinel, core-tests once on ubuntu. Nothing else on ledger-pc.

THE LINE THAT STARTS THE NIGHT, after the one reviewed commit:

    git push origin claude/game-dev-ai-automation-2h67ix

## Dictated edits

**W1. `.github/workflows/ledger-imagegen.yml`** lines 93 and 378: replace
`123` in `(123 checks, both outcomes)` and in `2 seconds and 123 checks` with
the count the selftest's last line prints under L1. If it prints 123, W1 is
`applied: unchanged, selftest prints 123`.

**Q1. `production/queue/045-banked-means-nothing-was-banked.md`** line 5
becomes:

```
status: LANDED 2026-09-02 (game-design/decision-2026-09-02-imagegen-run3-banked-means-in-the-commit.md). Fault 1 was not a lost commit: the four PNGs run 2 made were byte-identical to cb332751's, git add changed nothing in the index, and staged=5 counted git add calls; the workflow now prints gitAddCalls= and pathsWithAChange=. imagegen_verdict takes --staged-list and --in-head-list, names BANKED (exit 0) / NOTHING-NEW / NOT-BANKED with file names, and refuses BANKED without a list; the workflow stages first, asks git, writes the verdict, stages it last. Fault 2: the cause was load_made rebuilding recipes from prompt+seed while SKIPPED rows carry no seed; it now reads the recorded recipe, save_made runs at load, and remade is split into remadeUnrecorded and remadeRecipeChanged. The authority line says batchStatus and imagegenVerdict are different questions. attribution=failure was the sha step's own .err scratch file, moved to RUNNER_TEMP. Proven by run 3's committed verdict, not by this line.
```

**Q2. `production/queue/044-imagegen-tested-layer-edges.md`** line 3, append
before the final newline:

```
; (4) the commit step's `$(grep -c . "$STAGEDLIST" || echo 0)` prints two numbers when the count is zero, because grep -c prints 0 and exits 1; a log line, not the verdict, fix with `grep -c . file; true` or a python count; (5) item (1)'s two `fresh` copies now sit at imagegen.py 2517 (null-safe) and 2748 (not)
```

**N1. `production/NOW.md`** lines 120 to 144 (from `## In flight` through
`should be dispatched on the strength of one.`) become:

```
## In flight

- IMAGEGEN RUN 3, THE NIGHT RUN, fired by the push that landed
  game-design/decision-2026-09-02-imagegen-run3-banked-means-in-the-commit.md.
  Sentinel: limit all, max_minutes 240. Forecast: 14 skipped free, 31
  generated, about 45 to 65 minutes, dominated by sixteen portrait items at
  about 100 s each; no download, the runner is Jafar's account and the
  weights are present (manifest.json 15).
  RULE 9 HOLD: dispatch nothing that targets ledger-pc (Unity build, probe,
  setup, vignette fetch) until a landed commit titled `Meridian pictures
  from <sha>` CONTAINS the landing commit. Watch by ancestry.
  Read, in this order: the verdict's line 1 (the landing sha); the `steps`
  line; the `commit` line, where `picsThisRun=31 newInThisCommit=31` is the
  night banked and `alreadyInRepoIdentical=N` means N recovered records were
  wrong and cost GPU only; the done line, where `skipped=14
  remadeUnrecorded=0` is the recovery proven and `NOTHING-NEW` or
  `NOT-BANKED` names files; the log's `gitAddCalls= pathsWithAChange=`,
  `alreadyInHead=` and `shaSource=` lines. Then open the PNGs, every one,
  before any report (rule 4).
- RUN 2'S ACCOUNT IS CORRECTED. The pictures DID stage: all four were
  byte-identical to cb332751's, so `git add` changed nothing in the index
  and `staged=5` counted git add calls. The GPU time was wasted because
  load_made rebuilt recipes from prompt+seed and SKIPPED rows carry no seed,
  so fourteen finished pictures reconstructed as zero. Both fixed; 045 is
  LANDED; 044 carries the edges. Run 1's staged=0 did not recur: run 2
  reached git add on five paths, and whether a \r was stripped is in its
  stage-candidate lines, 044 item (3).
- NEXT ACTION, tomorrow: read run 3 as above and report to Jafar with one
  picture from it. Then slot 1 is the 027 Phase A close-out (040, A2, 041),
  one engine-specialist, one Unity dispatch at the end and only after the
  hold above clears; slot 2 is 037. Queue 046 still outranks more pictures.
```

**Not edited, and why.** `tools/attribution-check.py`: the sweep caught a
real file and is not loosened. `ledger-vignette-fetch.yml`: 044 item (3).
`tools/runner/step-verdict.sh`: not in this batch. `canon.md`: no world fact
touched. `production/quality-ladder.md`: 045 closes on run 3's verdict, and
the next rung is 044 plus 046.

## Deliberately not decided

- Whether a run that banks 31 and remakes 14 identical is a good night or a
  wasted quarter-hour. The commit line prints both numbers; the reading is
  tomorrow's.
- Whether the stop rule should be N blanks. No series has a blank in it.

## For the next session in one line each

- Apply W1, Q1, Q2, N1; run the selftest and quote its last line; `git
  status` against the stamp; verify; one commit staged by name listing every
  id; push, and that push is run 3.
- When run 3 lands: line 1, the steps line, the commit line, the done line,
  the four log lines, then every PNG; one report to Jafar with a picture.
- Resume this director, never restart, if git status shows a pending work
  path the stamp does not list, if the selftest prints anything but PASS, or
  if run 3's verdict reads NOT-BANKED.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 215):

    2026-09-02T19:44:54Z	studio-director

<!--RULING spawn=2026-09-02T19:44:54Z paths=.github/workflows/ledger-imagegen.yml,tools/imagegen/imagegen.py,production/d1-probe/RUN-IMAGEGEN,ledger/Assets/StreamingAssets/Decals/generated/made.json,production/queue/045-banked-means-nothing-was-banked.md,production/queue/044-imagegen-tested-layer-edges.md,production/NOW.md,game-design/decision-2026-09-02-imagegen-run3-banked-means-in-the-commit.md-->
