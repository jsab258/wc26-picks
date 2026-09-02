# D1 engine probe: execution plan (kicked off 2026-08-31, timebox retired 2026-09-02)

Authority: ledger-v2/respec/decision-register/D1-engine-probe.md, followed
exactly. The two-week timebox was RETIRED 2026-09-02 (amendment below); the decision record cites measurements, never
taste. Ties went to Unity until 2026-09-02 and go to Unreal since (register, second amendment of that date).

## The four measurements and how each is taken
a. Agent-loop friction: median edit-build-test cycle time and failed-edit
   rate on binary assets, measured over at least 20 real edits per engine,
   logged to production/d1-probe/cycles.tsv (one row per edit: engine, start,
   end, outcome). Unity numbers come from the existing CI and local loop;
   UE5 numbers from the ported slice.
b. Visual ceiling in the timebox: the same street built in both engines,
   screenshot pipeline in both, judged per D7 once judges exist, with the
   paired stills committed either way.
c. CI and instrument rebuild cost: estimated from (a) plus a written
   inventory of which of the existing instruments (screenshot pipeline,
   verdict channel, 4,163 Core tests) port mechanically and which need
   rebuilding.
d. Faces path: MetaHuman plus Audio2Face against CC4 plus Audio2Face,
   assessed on the talking-head test scene D2 names.

## AMENDED 2026-09-02: THE TIMEBOX IS RETIRED. Jafar: "forget the deadline, it's not relevant"

Ruling: game-design/decision-2026-09-02-d1-timebox-retired.md. The dates on
the two week headings below are the original plan's and no longer bind. The
probe is bounded by production/budget.md (the weekly ceiling) and by the
attempt budget on queue item 027: a director review every 6 dispatches a
phase spends without landing, 6 being the longest stretch this probe spent
on one sub-goal (the cook, runs 8 to 13), the only series that exists.
Measurement (a) is failed by non-convergence or hand-edit dependence, defined
in measurements.md, and never by a date. Later the same day Jafar REVERSED
the tie-break (register, second 2026-09-02 amendment): ties go to Unreal,
Unity wins only decisively, and "if the UE side cannot be measured, D1
closes UNRESOLVED" still means an external blocker, not a slow loop, and
never becomes either engine's win by default.

## AMENDED 2026-09-01: UNBLOCKED. UE 5.8.2 is installing; both halves run.

The launcher fault was a known bug, not an account state, and the fix took
thirty seconds once it was researched rather than reasoned about (account
of the wrong diagnosis in production/queue/done/000-d1-ue5-install.md).
Tasks 002 to 004 keep their order because the Unity measurements are needed
whichever way the engine decision goes, and they are not waiting on a
download. The paragraph below stands as written: it was the contingency, it
is no longer the situation, and its protection of the decision rule holds
regardless.

## SUPERSEDED CONTINGENCY, 2026-08-31: the UE half is blocked

The Epic launcher will not offer any engine version to Jafar's account
(symptom recorded in production/queue/blocked/000-d1-ue5-install.md). That
blocks week 1 items 1 to 3 and nothing else. Measurements a and c, and the
Unity half of b, need no UE5 and are now queue tasks 002 to 004.

THE DECISION RULE IS NOT AFFECTED AND MUST NOT BE BENT. D1 says Unreal wins
only if (b) is decisively better and (a) is tolerable, and that ties go to
Unity. A tie is a MEASURED tie. If the UE side cannot be measured at all,
D1 closes as UNRESOLVED with the blocker named, and the engine question
stays open in open-questions.md. It does not close as "Unity wins" by
default: that would be a decision made by a launcher.

## CORRECTED 2026-09-01, SAME DAY: the CI runner already does this

The paragraph below said the night runner is the mechanism by which the
probe happens at all, and that its first supervised run is D1's critical
path. That is WRONG and Jafar caught it by asking what the .bat does, which
is the question that exposes it.

TWO DIFFERENT RUNNERS, AND I NAMED BOTH "THE RUNNER":
1. The GitHub Actions self-hosted agent, C:\actions-runner-ledger, label
   `ledger-pc`, listening for jobs since 22 Aug. Dispatched from this
   container, it builds on Jafar's PC, runs the sim, captures stills and
   commits the verdict back. It needs NOTHING from him: no double-click, no
   supervision. Every still read this week came through it.
2. tools/runner/run-night.bat, written yesterday: a loop launching local
   Claude sessions against the production queue.

The confusion was mine and it cost a wrong critical path. What is true: the
container has no engine, so the WORK must happen on the PC. What is false:
that only the night runner can put it there. The CI agent has been putting
work on that PC for ten days.

WHAT EACH D1 MEASUREMENT ACTUALLY NEEDS:
a. cycle friction: mostly CI. The Unity workflow already times every step
   (checkout 64s, lint 8s, ShapeCheck 26s, unity-setup 547s, build 170s,
   sim 861s, measured off run 32294117005). A UE workflow times the same
   things. The failed-edit-rate-on-binary-assets half needs an agent
   editing binary assets, which is genuinely the night-runner case or a
   dispatched edit whose result CI reports.
b. visual ceiling: fully CI. Mirror the Unity workflow for UE, commit
   paired stills, same evidence channel.
c. instrument cost: DONE here, no machine.
d. faces: a headless UE commandlet in CI, probably; the first run may need
   the editor interactively, which is the one honest maybe.

THE NIGHT RUNNER IS STILL WANTED, for continuous autonomous development
against the queue, which is a different job from the probe. It stops being
D1's blocker and becomes its own item.

## SUPERSEDED, 2026-09-01: where the work can physically happen

Stated plainly because it changes the critical path and it is easy to miss:
the container this session runs in is Linux with no engine, so it cannot
run UE5, cannot compile against it, cannot take a screenshot from either
engine, and cannot time an edit-build-test cycle on the machine that
matters. Measurement c was done here because it is a counting job over
source. Measurements a, b and d are ALL machine-side.

The night runner is therefore not a convenience, it is the mechanism by
which the probe happens at all: it runs worker sessions ON the Windows PC
where both engines live. Its first supervised run is now the critical path
for D1, ahead of any further planning here.

Until it runs, the honest state of a, b and d is NOT STARTED rather than in
progress, and the two-week box should be read against that. If the box
expires with the runner unproven, D1 closes UNRESOLVED per the rule already
recorded; it does not close on partial measurements taken in the wrong
place.

## Week 1 (to 2026-09-07)
1. UE5 install on the build PC (JAFAR ACTION: one click, about 40 GB free
   disk needed; the installer link and steps go in the decision queue).
2. Transliterate the perception core and its tests to UE5 C++ (queue task;
   the C# source is the behavioral definition; tests must pass both sides).
3. Stand up the instrumented street scene in UE5: screenshot pipeline and
   frame-budget capture, mirroring the Unity instruments.

## Week 2 (to 2026-09-14)
4. Build the same street in both engines to each engine's ceiling within
   the box; commit paired stills daily.
5. Take measurements a through d; write cycles.tsv rows as they happen,
   never from memory.
6. Write the decision into D1 with the numbers, per its decision rule:
   Unreal wins only if (b) is decisively better AND (a) is tolerable for
   autonomous operation.

## Standing constraint carried from D1
Either way the world stays data-driven: JSON/YAML source of truth,
generators emit engine content, binary assets are build products. Work done
during the probe must not create hand-edited binary scenes.
