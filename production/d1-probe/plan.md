# D1 engine probe: execution plan (kicked off 2026-08-31, ends 2026-09-14)

Authority: ledger-v2/respec/decision-register/D1-engine-probe.md, followed
exactly. Two-week timebox; the decision record cites measurements, never
taste. Ties go to Unity.

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

## AMENDED 2026-08-31: the UE half is blocked, the Unity half runs first

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
