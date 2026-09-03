# DIRECTOR RULING: the still gate was reading its own explanation and both ends are fixed; the sweep names the instrument that could not have caught it; MADE now needs a wired UV chain; run 20 dispatches before the step is split (3 Sep 2026, 08:35Z)

> **STATUS — LOG, 2026-09-03. NOT CURRENT once this batch is committed and Unreal run 20 has landed a verdict; from then the committed `production/d1-probe/` evidence, queue 062 to 064 and `production/NOW.md` are the reading copies and this file is their history.**

This document carries exactly one em-dash, in the banner, because
`tools/docs-check.py` line 55 accepts no other form.

No shell in this spawn. Every number below was read from a named file and
line this session; the builder's report and the resident's brief were read as
CLAIMS, and the workflow, the C++, the Python tool, the queue and the landed
evidence files were read as evidence.

## What I read, and what I took on report

READ AS EVIDENCE, because a wrong call here costs a dispatch or hides a grey
street behind a green number:

- `.github/workflows/ledger-probe-unreal.yml` lines 270 to 330 (the material
  block), 606 to 720 (the still gate), 744 to 880 (the staging block), 905 to
  966 (the staged line and the vignette gate), 1015 to 1065 (the commit step).
- `ue-probe/Source/LedgerProbe/Private/LedgerProbe.cpp` lines 250 to 271.
- `ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp` lines 780 to 820 and
  1283 to 1307.
- `ue-probe/Source/LedgerProbe/Public/SurfaceBind.h` lines 276 to 349.
- `ue-probe/tests/vignette-spec-test.cpp` lines 495 to 566.
- `tools/ue/make_base_material.py` lines 100 to 180.
- `tools/verdict-dupkeys.py` lines 76 to 151, `tools/verdict-read.py` lines
  370 to 440, `tools/workflow-size.py` lines 20 to 62.
- The landed evidence: `production/d1-probe/ue-shot-verdict.txt`,
  `ue-build.txt` line 12, `ue-vignette-verdict.txt` lines 39 and 83,
  `DISPATCH` lines 175 to 214.
- `ledger-v2/research/license-allowlist.md` line 5 against
  `tools/citypack/fetch_textures.py` lines 50 and 489 to 491.

TAKEN ON REPORT, and named so nobody later reads them as checked: the 458-line
total; that `ledger/verify.py` is red on exactly one item; that run 19's
`materialConnections=12/14` reproduces as `PARTIAL` under the new rule (the
rule is pure and selftested, but I did not execute it). The resident pastes
the footer FROM `ledger/.verify-footer` after this lands, never from
scrollback.

PREMISE CHECK, first duty. Nothing in this batch touches CLAUDE.md section 0:
no world fact, no era framing, no purchase, no account. The one law that could
have been breached is the allowlist, because staging textures is the first
time these 51 files reach a rendered frame. Checked, not assumed:
`fetch_textures.py` line 50 fetches from `ambientcg.com` and lines 489 to 491
record `"licence": "CC0 1.0 Universal"` per asset, and allowlist line 5 names
ambientCG among the CC0 libraries. Clear.

## Ruling A. The ratchet is genuinely fixed, and the sweep found something worse

The finding stands and it was the most valuable thing in the batch. The
landed `production/d1-probe/ue-shot-verdict.txt` carries at line 8

    # shotStatus=WROTE needs a decoded file with more than one bucket and

and line 13 is the measured line. A reader taking the FIRST match for that key
read the comment. That gate could not have failed whatever the frame was, for
as long as the header has said it in that form.

BOTH ENDS ARE FIXED AND I VERIFIED BOTH, which is the right answer rather than
belt and braces: either half alone leaves the gate one careless sentence from
unfalsifiable.

- `LedgerProbe.cpp` lines 264 to 271 now write the explanation in prose ("A
  shot status of WROTE needs...") and add a standing line to the header
  itself: NO COMMENT IN THIS HEADER WRITES A KEY WITH AN EQUALS AND A VALUE.
- The gate at workflow line 713 filters `^\s*#` before `Select-String`.
- The SAME fix is applied to the vignette gate at line 961, which reads
  `captureStatus`, and `VignetteShot.cpp` line 816 now writes `materialBase
  reads MISSING when...` in prose rather than as a pair.

THE SWEEP, done here rather than filed. Repo-wide, the only surviving
`key=value` text inside a header comment written by any evidence writer is
`luma=(0.299R+0.587G+0.114B)/255`, in both cpp files. No gate reads `luma=`,
and the done line's keys are `shotMeanLuma`, `shotMinLuma`, `shotMaxLuma`, so
no live first-match reader can reach it. Left alone, named here so the next
sweep does not rediscover it as a finding. The other three key readers on the
UE side are `head -1 | grep -q "$SHORT"` on line 1 (the sha check, immune),
`grep -q "probeReached=end"` and `grep -q "setupReached=end"` (reach markers,
no header mentions them).

AND THE PART THAT MATTERS MORE THAN THE FIX. `tools/verdict-dupkeys.py`,
which item E proposes to point at `production/d1-probe/`, COULD NOT HAVE
CAUGHT THIS and will not catch the next one. Two reasons, both read this
session:

1. `collisions()` line 144 skips any key whose value sets are identical
   across families: `if len({frozenset(v) for v in values.values()}) < 2:
   continue`. The header said WROTE and the measured line said WROTE, so the
   sets matched and the tool stays silent. It is silent EXACTLY when the
   header quotes the passing value, which is EXACTLY when the ratchet exists.
   The tool is anti-correlated with the danger it would be credited for.
2. It skips only two named prose markers (line 79) and does not skip `#`
   lines at all, so pointed at these files it will emit header keys as
   findings.

So filing "point dupkeys at d1-probe" as the sweep would have banked a clean
result from an instrument that cannot see the fault. That is the shape rule 3b
exists for, one layer up. The sweep instrument is a different, smaller thing
and it is queue 064 below: a lint that refuses any `key=value` inside a
comment line of a verdict-shaped file, run over the emitters AND the committed
files.

ONE GAP I ACCEPT RATHER THAN CLOSE, with the reason. The repaired reader has
never been watched REJECTING (rule 5b), because there is no pwsh in this
container and the only fixture available proves the accepting case. I am not
holding run 20 for it, because the direction of the residual risk is now safe:
before the fix the gate failed OPEN (a bad frame passed silently); after it,
an unmatched key yields `$status = "NONE"` and exit 1, so it fails CLOSED. A
fail-closed reader that is wrong is visible and cheap; a fail-open one is what
we just paid for. The rejecting case rides queue 064.

## Ruling B. "wired == asked" is the right bar. Keep it

Accepted as written, and the reasoning is not "it is stricter".

The status word is read by a human deciding whether Phase C is done. Run 19's
material saved fine, made 3 of 3 parameters, and left the TexCoord head of the
UV chain unwired, which makes every sampler in that material read one texel.
That is a material that is textured in name and flat in the frame, which is
precisely the failure this whole batch exists to end. MADE beside a grey
street is the same class of fault as ruling A, one layer up: a word that
cannot be false. Two clauses out of three is not a material.

I verified the implementation is where it belongs. `material_status` (lines
115 to 135) and `material_return` (138 to 143) are pure functions in the
tested layer with `--selftest`, the return code is a FUNCTION of the status so
the run 19 contradiction cannot be printed again, and the line carries
`materialVerdictIs=materialScriptReturn/not-the-editor-process-exit` so a
reader is told which number is the verdict. `asked <= 0` returning PARTIAL is
the rule 3b guard: 0 of 0 cannot read as MADE.

THE OBJECTION, ANSWERED. "PARTIAL is the expected status of the next several
runs" is an argument for a second number that moves while the word stands
still, not an argument for a softer word. That number exists and is printed:
`materialConnections=12/14`. The series 12/14, 13/14, 14/14 is readable under
a constant PARTIAL, so nothing is lost by the strict bar.

CONSEQUENCE MEASURED BEFORE ACCEPTING, because a status that fails a step is a
different decision. Nothing gates on `materialStatus`: the line is appended to
`$L` in the build step (workflow line 305) and the step carries on, the cook
does not read it, and the vignette gate at line 962 reads `captureStatus`
only. PARTIAL costs nothing mechanical. It changes only what the word means to
a reader, which is the point.

STANDING RULE I ATTACH, so an expected red does not become an ignored one:
when `materialConnections` fails to move between two consecutive runs while
the status is PARTIAL, that is the signal to stop dispatching and fix the
refusal (queue 062), not to dispatch again.

## Ruling C. Run 20 first. The split is the NEXT edit to that block, and nothing else is

Seventeen characters is not a margin and the builder is right to raise it. But
I read the instrument before ruling on it, and it changes the shape of the
risk: `tools/workflow-size.py` line 51 sets `KNOWN_GOOD = 23184` as the
largest `run:` block ever ACCEPTED, against one observation of 24868 that
failed. The cliff is somewhere in 23184 to 24868 and the tool says so rather
than pretending to know. So the 17 characters is headroom against a
WATERMARK, not against a cliff, and the block as it stands today is at a size
that has shipped repeatedly.

DECISION: run 20 goes first.

1. The block is under the watermark now, and `workflow_size` is wired into
   `verify.py` (line 1405, called at 5718), so green covers it.
2. Splitting first means run 20's entire evidence flows through a step
   arrangement nobody has ever dispatched. Run 19's single achievement was
   head-less material generation working INSIDE that step. Moving the one
   thing that just started working, on the run whose purpose is to test the
   textures, is two changes and one measurement.
3. The split is not cosmetic. The material block reads `$ue`, `$buildBat` and
   `$proj` and appends to `$L`, the build log array, all step-local. A new
   step must re-derive them and re-plumb `$L` through a file or a step output,
   and its own failure mode is a step appending to the wrong log. That belongs
   to a run whose purpose is to test it.

AND THE BOUND IS NOT MOVED, which is the half that keeps this from being a
deferral. THE NEXT EDIT TO THAT RUN BLOCK IS THE SPLIT. Not the next
convenient one: the next one. No further character may be added to it, and if
run 20's read-out demands a change there, queue 063 lands first. A margin that
is spent by whoever happens to arrive next is how the number got to 17.

## Ruling D. Dispatch immediately on landing, in the same push, and then hold the branch

Yes. Conditions, all mechanical, all from failures this project has already
paid for:

1. ONE COMMIT for the whole batch INCLUDING the run 20 entry in
   `production/d1-probe/DISPATCH`. Not two pushes: the second push is run 18's
   exact killer.
2. CAPTURE THE SHA BEFORE PUSHING, and watch by ancestry (is there a landed
   run whose commit CONTAINS mine), never by branch movement or run name.
3. NOTHING IS PUSHED TO THIS BRANCH UNTIL RUN 20's COMMIT LANDS. This binds
   the resident's own turns: no NOW.md tidy-up, no dashboard commit, no queue
   file. Run 18 reported success on every step, took 4m46s and banked nothing
   because a resident push moved the branch sixteen seconds before its commit
   step. Work continues in the tree, uncommitted.
4. THE RUN 20 ENTRY NAMES THE NEW KEYS. Lines 192 and 213 of that file tell
   the next reader to read `materialScriptExit`, which no longer exists. Do
   NOT edit the run 18 and 19 entries: they are a log of what those runs
   printed and rewriting them is falsifying a record. The new entry says what
   changed and what to read.
5. WHAT RUN 20 DECIDES, written before it runs so it cannot be reinterpreted
   afterwards: `texRoot` names a directory, and `materialsStatus` reports
   pieces bound with maps found. `stagedTexFiles=<n>/<asked*dests>` and
   `stagedTexNote` say whether the copy happened; `texRootTried` says where it
   looked if it did not. The street looking textured is the picture. Those
   keys are the measurement, and per rule 4 the stills are opened first and
   the numbers printed before anything is concluded from the frame.

I checked the staging destination itself, because a wrong destination burns a
dispatch and this is the second attempt at it. Workflow line 833 joins
`CityPackTextures` onto `$proj` and `$binDir`, the same two variables that
line 801 already uses to deliver `vignette-pieces.json`, which the binary
demonstrably finds (`piecesEmitted=593/593` in the landed vignette verdict).
The binary's first two candidates, `VignetteShot.cpp` lines 1302 and 1303, are
the project directory and the exe directory. Same two places, by the same
mechanism, with precedent inside the same step. The destinations are cleared
before the copy (line 837) so a previous run's file cannot be counted as this
one's, and the copy is file by file. Correct.

## Ruling E. Three new items, two folds, and one of them is not the tidy-up it looks like

- **062, THE UV CHAIN HEAD REFUSES TO WIRE.** New item, not folded, because a
  named blocker hidden inside a large item stops being read. Carries run 19's
  note verbatim, `texcoord-to-maskU-refused/texcoord-to-maskV-refused`.
  Acceptance: `materialConnections=14/14` with `materialStatus=MADE` on a
  landed run. This is the live blocker of Phase C and it is first in line
  after run 20 reads out.
- **063, THE MATERIAL BLOCK GETS ITS OWN STEP.** New item, carrying ruling C's
  binding: it is the next edit to that run block, ahead of any other change to
  it. Acceptance: `workflow-size.py` prints both blocks under the watermark
  AND a landed run still carries `materialStatus` into `ue-build.txt`. FOLD
  `materialScriptMinutes` INTO IT: the timer at workflow line 304 wraps the
  `UnrealEditor-Cmd` process, so it measures editor startup plus script while
  its name claims the script. It is one rename or one re-placement once the
  step boundary exists, and it does not earn its own item.
- **064, A COMMENT MAY NOT WRITE A KEY.** New item, and this is the one that
  stops ruling A recurring: a lint refusing `key=value` inside a comment line
  of a verdict-shaped file, run over the emitters and over the committed
  evidence, shipped with its selftest accepting-case first per the standing
  rule. It carries the rejecting case ruling A could not run, and its named
  next rung is the real one for this aspect: the gate readers still live in
  YAML where no test can reach them, while `make_base_material.py` just showed
  the correct shape by moving the status decision into a tested layer.
- **FOLD THE DUPKEYS ITEM INTO 029**, with ruling A's finding attached in
  writing: dupkeys cannot see this shape (line 144) and does not skip `#`
  lines, so whoever points it at `production/d1-probe/` decides comment
  handling FIRST and does not report its silence as a clean result. It goes
  after 064, not before, and it is not the sweep.
- **FOLD INTO 042**, found by me and not on the builder's list:
  `director_cadence`'s evidence table (`verify.py` lines 2458 to 2470) names
  `ue-build.txt`, `ue-machine.txt`, `ue-verdict.txt`, `ue-shot-verdict.txt`,
  `ue-shot.png` and `msvc-setup.txt` by exact path, and does NOT name
  `ue-vignette-verdict.txt` or the four `ue-vign_*.png`. They fall to
  `pathsOther`, so nothing is blocked and nothing is miscounted as work today.
  Harmless now, a hole the first time someone asks why the vignette outputs
  are unclassified.

## The quality ladder at close

Best available or first working? For the batch's own aspect, the instrument
that decides whether a UE frame is usable, this is a genuine rung up: the
gate went from unfalsifiable to fail-closed, and the material status went from
a word that could not be false to a rule with a series behind it. The next
rung is named and it is 064's tail clause, so the aspect is not blank. For the
street itself, nothing has moved yet. Run 20 is what turns 51 staged files
into a measurement.

<!--RULING spawn=2026-09-03T08:35:35Z paths=.github/workflows/ledger-probe-unreal.yml,ue-probe/Source/LedgerProbe/Private/LedgerProbe.cpp,ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp,ue-probe/Source/LedgerProbe/Public/SurfaceBind.h,ue-probe/Source/LedgerProbe/Public/VignetteSpec.h,ue-probe/tests/vignette-spec-test.cpp,tools/ue/make_base_material.py,production/d1-probe/DISPATCH,production/NOW.md,production/queue/029-verdict-keys-and-vignette-prefix.md,production/queue/042-cadence-ruling-names-its-paths.md,production/queue/062-uv-chain-head-refuses-to-wire.md,production/queue/063-material-block-gets-its-own-step.md,production/queue/064-a-comment-may-not-write-a-key.md,game-design/decision-2026-09-03-texture-staging-and-the-still-gate-ratchet.md-->
