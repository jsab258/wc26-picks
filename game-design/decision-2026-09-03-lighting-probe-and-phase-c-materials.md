# DIRECTOR RULING: the lighting probe and Phase C materials land, with one hand-applied line first; the control-probe design is upheld; the claimed commandlet fallback does not exist and the claim is withdrawn, not the code (3 Sep 2026, 06:0xZ)

> **STATUS — LOG, 2026-09-03. NOT CURRENT once the batch is committed and run 18 is dispatched; from then `production/NOW.md`, `production/queue/` and `production/d1-probe/DISPATCH` are the reading copies and this file is their history.**

This document carries exactly one em-dash, in the banner, because
`tools/docs-check.py` line 55 accepts no other form.

<!--RULING spawn=2026-09-03T06:02:28Z paths=game-design/decision-2026-09-03-lighting-probe-and-phase-c-materials.md,tools/ue/make_base_material.py,.github/workflows/ledger-probe-unreal.yml,ue-probe/Config/DefaultGame.ini,ue-probe/Source/LedgerProbe/Public/SurfaceBind.h,ue-probe/Source/LedgerProbe/Public/FrameStats.h,ue-probe/Source/LedgerProbe/Public/VignetteShot.h,ue-probe/Source/LedgerProbe/Public/VignetteSpec.h,ue-probe/Source/LedgerProbe/Private/VignetteShot.cpp,ue-probe/Source/LedgerProbe/Private/LedgerProbe.cpp,ue-probe/Source/LedgerProbeEditor.Target.cs,ue-probe/tests/frame-stats-test.cpp,ue-probe/tests/vignette-spec-test.cpp,production/queue/059-a-placed-lantern-is-not-a-lit-street.md,production/queue/060-a-cap-that-bit-inside-the-check-that-found-it.md,production/d1-probe/DISPATCH,production/NOW.md,production/budget.md,ledger/verify.py-->

VERDICT: LAND, then dispatch run 18. One line is hand-applied first (F1 below).
Two findings are recorded against the builder's summary and neither of them is
a code fault. Nothing here blocks the dispatch.

## The spawn row this answers

`2026-09-03T06:02:28Z`, the last row in `.claude/agent-log.tsv`, four minutes
after the builder's last row at `05:58:42Z`. The 2 September director rows
(`21:27:43Z`, `21:42:14Z`) and the 3 September `00:22:45Z` row belong to other
reviews; `00:22:45Z` is already claimed by
`game-design/decision-2026-09-03-night-batch-of-2-september.md` and none of
them is stamped here.

## THE PATHS LIST IS A CEILING, NOT A MANIFEST

Bash is disabled in this session, exactly as it was for the 00:22Z ruling, so I
could not run `git status`, `git diff`, `ledger/verify.py` or the g++ selftests.
The `paths=` line is derived from reading file contents, not from the dirty set.
The resident's protocol is the one that ruling established, unchanged:

1. `git status --porcelain`, and stage by name only paths appearing in BOTH
   that output and the `paths=` line. Naming a clean file costs nothing; no
   directory is named anywhere in this ruling.
2. ANY DIRTY PATH NOT ON THE LIST IS REPORTED BACK BEFORE THE COMMIT. Not
   committed, not discarded, not assumed to belong to the builder.
3. The two intent-to-add files get the extra step in section C. They are the
   one case where "it appears in `git status`" is not enough.

Every number in my brief (2016 changed lines, 135 checks over 2 of 2 binaries
up from 78, `albedoResolved=12/16`, 73 characters of dispatch headroom, red on
`DIRECTOR NOT SPAWNED` alone) was taken from the brief and NOT re-measured by
me. The commit footer is pasted FROM `ledger/.verify-footer` after a green run,
never from this file and never from scrollback.

## WHAT I READ AND WHAT I TOOK ON REPORT

Proportionality was the instruction and the depth is uneven on purpose. This is
one builder, and B is the D1 measurement, so B got most of the reading.

READ IN FULL, artifact opened:

- `tools/ue/make_base_material.py`, all 306 lines.
- `ue-probe/Config/DefaultGame.ini`, all 55 lines, and `DefaultEngine.ini`
  searched for plugin and Python keys (no matches, which is a finding).
- `ue-probe/LedgerProbe.uproject` and `Source/LedgerProbeEditor.Target.cs`.
- `ue-probe/Source/LedgerProbe/Public/SurfaceBind.h`, all 295 lines.
- The light-probe half of `FrameStats.h`, lines 288 to 497.
- The material block of `.github/workflows/ledger-probe-unreal.yml`, lines 281
  to 314, and the staging block, lines 994 to 1008.
- `ledger/verify.py`: `director_cadence` and its stamp grammar, `tools_tracked`,
  `queue_depth`, `workflow_size`.
- `tools/queue-check.py` head and its `FLOOR`, plus a directory listing of
  `production/queue/`.
- `ledger-v2/respec/decision-register/D1-engine-probe.md`, all three amendments.

TAKEN ON THE BUILDER'S REPORTED EVIDENCE, not re-run here:

- The g++ selftest counts, and that they cover both binaries.
- `albedoResolved=12/16` and the `AssetLibrary.cs` cross-check identifying
  card, interior, multiply and paint_yellow as Unity's procedural surfaces. I
  did not open `AssetLibrary.cs`. The claim is cheap to falsify later and the
  absence is now named on the verdict rather than silent, which was the point.
- The 73-character headroom, which `workflow_size` prints and which the
  resident will read again from the footer after F1.
- The whole of the diff outside the files listed above.

NOT VERIFIABLE FROM THIS CONTAINER BY ANYONE, and named so nobody later reads
this ruling as coverage: whether `-run=pythonscript` starts at all on that
machine, whether the material compiles, whether the cook carries it, and every
number the two new printers will emit. The builder said NOTHING MEASURED and
that is the correct state of both printers today.

## A. The control probe is the right design, and it is not yet a bound

UPHELD. This is the strongest part of the batch and it is upheld on the reason
it was built for, not on taste: rule 2 says do not set a threshold you have not
measured, and "did this light reach a pixel" needs an epsilon because temporal
antialiasing and dither move pixels by a code value or two on their own. The
two ways to get that epsilon are to invent one and to measure one. A control
probe that toggles nothing, taken in the same run, on the same camera, at the
same frame counts, measures it. That is a negative control and it is the
correct instrument.

Three things in the code make it more than a gesture, and I checked each:

- `PixelsDarkerWithLightOn` is the auto-exposure detector, and it is the part
  that makes the difference interpretable at all. Pixels brightening when a
  light goes off is physically impossible for a light in isolation, so a
  non-trivial count there condemns the whole difference. Without it, an
  exposure ramp would read as a lantern doing work.
- `RoseAtLeast` is powers of two and the comment says plainly that no number
  there was chosen and a bound comes later from real runs. The histogram ships
  as a series. Correct under rule 2.
- The denominators are attached to the right things.
  `lightsReachedFrame=%d/%d` is ReachedFrame over Probed, not over Eligible,
  which is the only defensible denominator: reached is a statistic of what was
  probed. `lightRestoreMismatch=%d/%d` carries Probed as well.
  `lightProbeStatus=NOTHING-MEASURED` fires when Probed is zero rather than
  printing `0/0` as though it had looked. That is rule 3b done properly.
- The peak tile carries `PeakMeanOn` and `PeakMeanOff` captured at the tile
  where the delta peaks, which is the `xAtWorst` pattern from the instrument
  rules rather than two maxima from different places divided together.

TWO LIMITS, NAMED NOW SO THAT NOBODY SETS A BOUND THROUGH THEM LATER. Neither
blocks anything today, because no bound is set today.

1. ONE CONTROL PER NIGHT SHOT IS ONE SAMPLE, AND A NOISE FLOOR IS A
   DISTRIBUTION. A single control tells you what the noise DID once, not what
   it CAN do. When the bound is eventually read from these controls it must be
   read as at-worst across N controls with N printed, never from one run's
   single control, and the key that carries it must say which statistic it is.
   `controlProbes=%d` already prints N, so the material for doing this right is
   there. Doing it wrong would be rule 2 with extra steps.
2. THE NO-OP CONTROL DOES NOT EXERCISE THE TOGGLE PATH. The real probe captures
   a reference, mutates a light's visibility, captures, and restores. The
   control captures twice and mutates nothing. Any perturbation caused by the
   mutation itself, an invalidated render state or a disturbed temporal history,
   is present in the measurement and absent from the control, so the control can
   UNDERSTATE the floor of the path it is the floor for. The next rung is a sham
   toggle: set a light to the value it already holds, or off and back on, then
   capture. Same cost, strictly tighter control. This goes on the ladder as the
   named next rung for this aspect, per the standing order.

SKIPPED-ALREADY-OFF IS THE RIGHT REFUSAL, and it is the same rule as the
control. Photographing a light that is already off yields a difference of zero
that is arithmetically true and semantically false: it means nothing was
toggled, not that the lantern fails to reach the frame. Printing it as a
measurement would put a zero beside the word lantern and a later session would
read it as a dark lantern. It is counted in its own key, kept out of the
`lightsReachedFrame` denominator, and the status line separates it from a
budget skip and from a frame that would not decode. Three different facts with
three different next actions, kept apart. That is the correct call and I would
have ordered it if it were absent.

## B. The material generator is genuinely head-less. This is the D1 answer, pending CI

This got the reading time because D1's second amendment of 2 September makes
(a) decisive and defines its failure as non-convergence or hand-edit
dependence. The question was whether anything here is a human step wearing a
script's clothes. I looked for one specifically and did not find one.

WHAT ACTUALLY HAPPENS, traced end to end:

- The asset is created by `unreal.AssetToolsHelpers` inside
  `UnrealEditor-Cmd.exe` under `-unattended -nopause -nosplash`. No editor
  window, no human. Every expression is placed, every connection is attempted
  through a guarded helper that counts `wired` against `asked`, and the result
  is written as `key=value` to a file rather than a log tail.
- The step ordering was the real bug the builder found and it was a genuine
  one. `LedgerProbeEditor` is now built immediately before the script runs. A
  C++ project cannot open its editor without its editor module, and an
  unattended editor asked to rebuild one exits rather than asking. That fix is
  what makes the head-less claim possible at all.
- THE COOK TRAP IS HANDLED, and this is the thing I expected to catch and did
  not. Nothing in the project references `/Game/Ledger/M_LedgerSurface`; the
  runtime loads it by path. An unreferenced asset is not cooked, and the
  failure would have been an untextured street with every count green, which is
  this project's signature fault. `DefaultGame.ini` line 43 carries
  `+DirectoriesToAlwaysCook=(Path="/Game/Ledger")` with the failure shape
  written out beside it. The material is made after the timed builds and before
  `BuildCookRun`, so the cold build number stays a cold build number and the
  asset exists when the cooker runs.
- The textures are not editor imports. They are decoded at runtime and bound
  through dynamic instances, which needs no editor, so the one binary asset is
  genuinely one.
- The uasset is staged BY NAME with a `[ -f ]` guard so a run whose editor
  never started cannot stage the DELETION of the last good run's asset. That is
  the CI rule applied correctly, and the reasoning is in the workflow comment.

SO THE ANSWER TO JAFAR'S QUESTION IS: NO, on the design, no human opens the
Unreal editor, and the design is now specific enough to be wrong in public.
UNVERIFIED UNTIL RUN 18 LANDS, and the builder was right to say so.

FINDING B1, AND IT IS THE ONE PLACE THE SUMMARY OVERSTATES THE ARTIFACT. The
builder reported that the workflow "probes and prints found or NOT-FOUND with a
C++ commandlet fallback". THERE IS NO FALLBACK. I searched the workflow for
commandlet and fallback: the only hits are an unrelated sha fallback at line
121 and two comments about the cook commandlet. `ue-probe/Source` contains no
editor module and no commandlet class; the Source tree is eight files and I
listed them all. The workflow runs `-run=pythonscript` unconditionally and, if
nothing is written, prints `materialStatus=NO-LINE` plus up to twelve
interesting log lines with the overflow announced.

THE CODE IS FINE. THE CLAIM IS WITHDRAWN. I am not ordering a fallback built,
because a second path would muddy the very measurement this run exists to take:
if the Python route cannot run unattended, that IS the D1 finding and it should
arrive clean. What I am refusing is the sentence, because a later session
reading "there is a fallback" would size the risk wrongly. This is the verifier
default from the studio split applied to a builder's prose: the discrepancy is
real, its cause is a summary written faster than the diff, and the cheapest
decisive measurement was a grep, which I ran.

FINDING B2, AND IT IS WHY F1 EXISTS. `materialPythonPlugin=found/N` searches
the engine tree for `PythonScriptPlugin.uplugin`. That measures PRESENCE ON
DISK. It does not measure whether the plugin is ENABLED for this project, and
those are different facts. The uproject declares no `Plugins` block, by the
builder's deliberate and correct refusal, and `DefaultEngine.ini` has no plugin
key either. So if the installed 5.8 engine does not enable that plugin by
default, `-run=pythonscript` does not run, and the verdict will read
`materialPythonPlugin=found/1` beside a dead script. A key that says found
while the thing it names did nothing is the quiet instrument fault this project
keeps paying for.

I cannot check that engine's default from this container and I am not going to
assert it either way. F1 removes the question instead of answering it.

## C. Intent-to-add is legitimate, and it is NOT sufficient for the commit

The check is `tools_tracked`, and it proves tracking with
`git ls-files --error-unmatch`. An intent-to-add entry satisfies that, so
`git add -N` did make the check honest rather than silencing it: the fault
`tools_tracked` exists to catch is a workflow naming a script that is not in
the repository, producing local green and CI red with no code difference
between them. `make_base_material.py` is named in the workflow, so the check
was correct to go red and the builder's response was the right shape.

THE HAZARD IS AT THE COMMIT, NOT AT THE CHECK. Intent-to-add records a path
with no content. `git write-tree` excludes those entries, so a commit that
stages only the paths on a list can land the batch with those two files absent
or empty, and `tools_tracked` will have been green the entire time. That is the
same local-green CI-red shape one layer further out.

RESIDENT, MECHANICALLY, BEFORE THE COMMIT:

1. `git add -- <path>` explicitly for BOTH intent-to-add files, by name, so
   content is staged and not just intent.
2. After the commit, `git show --stat HEAD` and confirm both appear with a
   non-zero line count. A file listed with no lines is the failure this step
   exists to catch.
3. I could not enumerate the two files: `tools/ue/` contains exactly one file,
   `make_base_material.py`, so that is one of them, and I could not identify
   the second without git. Do not guess it. `git status --porcelain` shows
   intent-to-add as a space followed by A, distinct from a staged add. Report
   the second path in the batch note.

QUEUE ITEM, filed with the rest: `tools_tracked` cannot distinguish an
intent-to-add entry from a committed file, and its whole purpose is to prove a
file will exist for CI. It should compare the staged blob against the empty
blob, or read `git status --porcelain` for the intent-to-add shape, and it
should print what it examined either way. Selftest ships with it, accepting
case first, per the instrument rules.

## D. The three declared holes: none blocks the dispatch, all three are named

D1, NO EMISSIVE MATERIALS. Queue item, not a blocker for run 18. The seven
lights are real lights, so the street is lit; what is missing is the glowing
surface of the fixture. It does NOT block this dispatch and it DOES block
something else, which matters more: the D1b blind pair judgement. If one engine
renders a glowing lamp housing and the other renders a dark one, the pair
differs by CONTENT and not by RENDERER, and measurement (b) stops measuring
what it claims to. The sheet must not be judged until both engines treat
emissive the same way, or until the difference is recorded on the sheet before
any label is unmasked. Filed as a gate on the pair judgement, not on the run.

D2, TILING FROM THE TWO LARGEST DIMENSIONS. Queue item. The simplification is
declared in the code comment and, more importantly, on the verdict itself:
`tilingModel=two-largest-dimensions/not-per-face-uvs` ships beside every number
it produced, and `metresPerTile` is printed as the stated convention it is
rather than a measured bound. A named simplification that travels with its
output is a queue item. An unnamed one would have been a finding. Next rung is
per-face UVs.

D3, SEVENTY-THREE CHARACTERS OF DISPATCH HEADROOM. This one gets a rule rather
than a queue item, because the ceiling is enforced AT DISPATCH and not at
commit, so overrunning it does not fail a check, it fails the run. Precedent is
in the DISPATCH log at run 16: the capture was extracted into its own step for
exactly this reason at 22040 characters against 23184.

THE BUILD STEP IS FROZEN AFTER F1. No further edit to that step until it has
been split, and splitting it is the queue item. F1 spends 36 of the 73 and the
resident confirms the remainder from the footer. If `workflow_size` comes back
red or the printed headroom is under 20 characters, STOP and escalate rather
than trimming a comment to fit, because trimming the comment is how the ceiling
was hit the first time.

## E. Queue housekeeping happens AFTER the dispatch, and it is no longer optional

I checked the gate before ordering the sequence, because the obvious risk was
that housekeeping turns verify red at the worst moment. It cannot.
`queue_depth` runs `tools/queue-check.py`, which reads `game-design/queue.md`
and nothing else. The `production/queue/` directory is not counted, so marking
five items landed and filing eight new ones moves no gate in either direction.
The `FLOOR = 3` is safe whichever order this happens in.

I also confirmed the premise of the complaint rather than taking it: the
directory listing goes 049, then 056, 059, 060. Items 050 to 055, 057 and 058
are genuinely absent, and 041, 046, 047, 056 and 027 are genuinely present.

SO THE ORDER IS: dispatch first, file second. The dispatch is the long pole and
it occupies a machine that is idle right now; the filing is offline work that
fits comfortably inside the round trip. Doing it first would leave a PC idle
while markdown is written.

AND IT IS NOW A DEBT WITH AN EVENT ATTACHED, NOT A CLOCK. Two rulings have
ordered this and neither was carried out, which is why item 060 exists while
050 to 055 do not: the queue is being appended to and not reconciled. The
resident does not open new work after run 18 is dispatched until the eight
items exist and the five landed ones are marked. If a session ends before that,
it is the first thing the next one does. An order given three times without an
event attached is a preference, and this is the third time.

## F. Dispatch immediately on landing, with one line applied first

YES, DISPATCH ON LANDING. The PC is idle, the run is informative whatever
happens, and it carries both items in one round trip, which is the batching
rule. Even the worst plausible outcome for Phase C still returns the lighting
probe, the clipping histogram and the four frames, so this is not a run that
can come back empty.

F1, THE ONE HAND-APPLIED LINE, AND THE ONLY THING BETWEEN THIS BATCH AND THE
DISPATCH. Add `-EnablePlugins=PythonScriptPlugin` to the argument array of the
`UnrealEditor-Cmd.exe` invocation at workflow line 303, beside the existing
`-unattended -nopause -nosplash -stdout`.

WHY THIS AND NOT THE UPROJECT. The builder's refusal to name the plugin in the
uproject was correct and stands: a uproject naming a missing plugin fails to
load, and that would cost the ENTIRE run, build, cook, frames and light probe,
to protect one phase. The command line has a strictly better failure profile.
If the plugin is present, this enables it. If the switch is unrecognised or the
plugin is absent, the editor ignores an unknown token and the run proceeds
exactly as it would have. There is no outcome where this line costs more than
it can save, and what it can save is the most likely remaining cause of an
ambiguous Phase C.

I have not verified the switch name against 5.8 from this container and I am
recording that rather than implying otherwise. Its failure mode is benign,
which is the whole reason it is worth applying blind. The run itself reports
the answer: `materialScriptExit`, `materialStatus` and `materialLogInteresting`
together say whether Python ran.

RESIDENT SEQUENCE:

1. Apply F1. Stage the intent-to-add files by name with content, per C.
2. Run `ledger/verify.py`. Confirm `cadence ok` and `REVIEWED`, and confirm
   `workflow steps ok` with its printed headroom above 20. Paste the footer
   FROM `ledger/.verify-footer`.
3. One commit for the batch. Append the run 18 line to
   `production/d1-probe/DISPATCH` naming what is UNRUN until this run: whether
   the Python route starts unattended, whether the material compiles and saves,
   whether the cook carries `/Game/Ledger`, whether any texture binds, and both
   light-probe printers, which have never seen a real frame.
4. Touch `production/d1-probe/DISPATCH` and push, which is the dispatch.
5. Then, and only then, section E.

## What I did not do, so the next session does not assume it

I did not read `AssetLibrary.cs`, the tests, `VignetteShot.cpp` beyond the
grep that located the light-probe caller, or the clipping half of `FrameStats.h`
beyond its done line. I did not run verify, git or g++, because Bash was
disabled. The `albedoResolved=12/16` explanation and the 135 selftest checks
are the builder's evidence, accepted as reported and cheap to falsify from run
18's verdict.

## Ladder, at close

Named rungs, so no aspect closes with a blank one: light probe, a sham-toggle
control and a bound read as at-worst across N controls. Materials, per-face UVs
and emissive surfaces. Tool registry, an intent-to-add-aware `tools_tracked`.
Workflow, the build step split so the next change is not a dispatch risk. None
of these is a research task; all four are known work with a known shape, which
is the correct state for an aspect that is moving.
