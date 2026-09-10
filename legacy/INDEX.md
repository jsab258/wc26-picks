# legacy/INDEX.md: what is archived here, and why each thing stopped

STATUS: LIVE. Verified 2026-09-10. Wrong here is a bug, not a stale log: this
file is the only readable record of what left the working tree, and an archive
nobody can read back is a deletion with extra steps.

THE RULING THIS FILE EXISTS FOR, Jafar 2026-09-10, verbatim: "Archive, never
delete. Everything retired moves under legacy/ with one index file naming what
it was and why it stopped." Recorded at
`ledger-v2/respec/decision-register/D16-engine-unreal.md` alongside the engine
decision that caused most of it.

Every path below moved with `git mv`, so `git log --follow <path>` reaches the
file's whole history from its new home.

## Counts for the 2026-09-10 sweep

    pathGroupsMoved=6 trackedFilesMoved=510 trackedBytesMoved=878629
    untrackedBuildArtefactsCarried=24/24-gitignored-obj-under-Recurrence
    listItemsMovedInFull=4/13 movedInPart=1/13 leftInPlace=8/13
    trackedFilesLeftInPlace=763 probeProjectsLeft=11/12 theirTrackedFiles=23
    liveReadersUpdated=3 gatesRerunGreenAfterTheMove=3/3

The three gates re-run after the moves, with the numbers they printed:

    tools/systems-inventory-check.py  evidence=204/204-resolved problems=0/1970-checks
    tools/attribution-check.py        stray=0/2833-assetFiles walked=5043..5045
    tools/docs-check.py               171/171-clean-under-game-design

`attribution-check` walked 5043 files before this index existed and 5045 after,
because other agents were committing in the same window. The figure the gate
turns on, `assetFiles=2833` with `stray=0`, did not move: the sweep was run
before the first move and twice after, and no asset file changed directory.

`ledger/verify.py` was NOT run: it runs alone and other agents were working.
Every claim below about a verify.py gate is read off `ledger/verify.py` at the
line cited, not off a run.

## What moved, 2026-09-10

### 1. The Recurrence probe project

Was: `ledger/Recurrence`, a C# console probe (`Program.cs`, `Density.cs`,
`Recurrence.csproj`) that compiled `Assets/Scripts/Core` and exercised the
recurrence side of the population model.

For: answering whether the same people come back to the same places on the
same days, before anything rendered.

Why it stopped: D16 retired Unity to the legacy reference build, and this is
the only one of the twelve probe projects with NO reader anywhere. Measured
2026-09-10: zero hits for the path `ledger/Recurrence` across `tools/`,
`.github/workflows/`, `ledger/verify.py`, every `.csproj` and every `.json` in
the repo. The eleven others all have a named runner and stayed (section
"Left in place", item 3).

Now at: `legacy/unity-reference-build/probes/Recurrence/`

Read it back: the source is whole. It does NOT build where it sits, because
`Recurrence.csproj` carries `<Compile Include="../Assets/Scripts/Core/**/*.cs" />`
and that relative path no longer resolves four directories down. Rebuilding it
means either restoring the directory beside `ledger/Assets` or repointing that
one include at `ledger/Assets/Scripts/Core`. Left broken rather than silently
rewritten, so the next reader sees the cost of the move instead of inheriting a
path nobody ruled on.

    trackedFiles=3 bytes=25535 untrackedObjReleaseArtefactsCarried=24

### 2. The act drafts, v1 era

Was: `game-design/act1-draft.md`, `act2-draft.md`, `act3-draft.md`, dated
2026-09-03 in the tree and written in the v1 design era.

For: the three-act narrative on-ramp for the v1 game, including the Fall and
the dated audit beat.

Why it stopped: narrative v2 is phase 3 of `ledger-v2/respec/roadmap-v2.md` and
is unwritten. `production/systems-inventory.json` types that entry as
"Narrative v2 is phase 3 and unwritten", so these are raw material for a
rewrite rather than the spec anything is built against.

Now at: `legacy/v1-era/act-drafts/`

    files=3 bytes=20771

### 3. The audit findings, v1 era

Was: `game-design/audit-findings-2026-07-27.md` (165543 bytes, the big one),
`game-design/completeness-audit-2026-07-31.md`,
`game-design/voice-audit-2026-07-30.md`.

For: three dated sweeps of the v1 codebase and content: what existed, what was
missing, and which cast members had no usable voice.

Why it stopped: all three are dated findings about a July tree, superseded by
the v2 respec of 2026-08-31 and by `production/systems-inventory.json`, which
is the live typed reading of system state. A findings document decays exactly
like a comment, and CLAUDE.md rule 3 says a document claiming something is
missing is an analysis and not evidence. Measured before the move: zero
readers across `.py`, `.sh`, `.yml`, `.json` and `.md`.

Now at: `legacy/v1-era/audits/`

    files=3 bytes=179798

### 4. The day and night logs, v1 era

Was: `game-design/day-2026-07-27.md`, `night-2026-07-26.md`,
`night-2026-07-30.md`, `overnight-2026-07-29.md`, `overnight-2026-07-30.md`.

For: the per-session logs of what the studio did on five days and nights in
late July 2026, written before `production/NOW.md` and the decision-record
convention existed.

Why it stopped: the record is now a dated decision record under `game-design/`
plus `production/NOW.md` for what is moving. These five are the predecessor
format, true on one day and not since. Measured before the move: zero readers
across `.py`, `.sh`, `.yml`, `.json` and `.md`.

Now at: `legacy/v1-era/logs/`

    files=5 bytes=81602

### 5. The two stale week plans

Was: `production/week-plan.md` (week of 2026-08-31, W36) and
`production/week-plan-2026-09-02.md`.

For: the weekly points budget and what fitted inside it.

Why it stopped: both carry `STATUS: LOG` and say so themselves: "superseded
2026-09-08 by the regime change". Jafar's ruling of 2026-09-08, quoted in both:
"the plan is now Max 20x; every rate computed before this reading is void." The
numbers are left as written, because a deleted number cannot be audited.

NOT MOVED, and this is the third file Jafar's "stale week plans" does not
cover: `production/week-plan-2026-09-08.md` is `STATUS: LIVE`, is the W37 plan
covering Monday 2026-09-07 to Sunday 2026-09-13, and today is 2026-09-10. It is
the live plan and it stayed.

Now at: `legacy/week-plans/`

    files=2 bytes=7850

### 6. The refusal records for the message of 3 September

Was: 494 files matching `production/outbound/*.refused-<8hex>.txt`.

For: one record per refused send attempt of one Producer message, written by
`tools/runner/outbox.py` so that a refusal is a receipt rather than a silence.

Why it stopped: the message they refuse is already retired. It is
`legacy/outbox/2026-09-03-batch-landed-and-the-wait.EXPIRED.md`, whose own first
line says the Unreal run it asked about has since gone. Every one of the 494
refuses that single message base, so the records cannot hold anything that can
still be sent.

Measured before the move, because one of these files COULD have stopped a live
retry loop:

    refusalRecords=494 distinctMessageBases=1 holdYes=0/494 holdNo=494/494

`tools/runner/outbox.py:holds_for` is the reader: it walks the outbound
directory for `<base>.refused-` records and a record only holds when its
`hold:` field reads `yes`. Zero of 494 do, so nothing here was holding
anything. The base is also absent from `production/outbox/`, so there is no
message left for them to be about.

Jafar's message said 483. The measured count on 2026-09-10 was 494; the
difference is retries that landed after the number he read, which is
`tools/producer-day.py`'s own comment ("483 of the 506 records") going stale
the way a count in prose does.

What the move bought, measured rather than asserted. Before, the refusals
crowded out the deliveries in the producer's daily receipts block. After
(`python3 tools/producer-day.py --print`):

    receipts (production/outbound, 39 record(s) walked): sent=15 refused=0 replies=14 photos=0 cards=7 unreadable=0

The 39 receipts that remain in `production/outbound` were NOT archived. Jafar's
list named the refusal records only, and a receipt is the proof a message
arrived.

Now at: `legacy/outbound-refusals-2026-09-03/`

    files=494 bytes=563073

## Live readers updated in the same move

Three, and each was re-run green afterwards rather than reasoned about.

1. `production/systems-inventory.json`, three `evidence` paths for the narrative
   entry, repointed from `game-design/act{1,2,3}-draft.md` to
   `legacy/v1-era/act-drafts/`. `tools/systems-inventory-check.py` resolves
   every evidence path and reports `path_missing` for one that does not, so the
   move would have turned it red. After:
   `evidence refs=204 resolved=204/204`, `problems=0/checks=1970`, identical to
   the baseline taken before any file moved.
2. `production/week-plan-2026-09-08.md`, two references to the plans it
   supersedes, repointed to `legacy/week-plans/`. The live plan quotes both
   void numbers and names the files they came from, so a stale path there would
   make the void arithmetic unfindable.
3. `game-design/open-city-spec.md`, two backticked references to
   `act1-draft.md`, repointed to `legacy/v1-era/act-drafts/act1-draft.md`.

Left deliberately unedited: `game-design/process.md` line 97, a dated 2026-07-26
table row naming `act1-draft.md`. It is a historical row in a log, and editing
the text of a dated record to match today's layout is revisionism. The path is
findable from this index.

Two counts move as a side effect of archiving Recurrence, and neither is a
threshold. `ledger/verify.py:tools_tracked` prints
`N tool project(s) ... tracked` from `ROOT.glob("*/*.csproj")` and
`tools/map.py:code_only` reports `projects`; both read `ledger/*/*.csproj`,
which went from 17 to 16 (measured 2026-09-10). Named here so a number moving
is not mistaken for something breaking.

## Left in place, with the reason, 2026-09-10

Eight of the thirteen items on Jafar's list stayed, because a live reader calls
them and "archive, never delete" is not "archive and let the build fall over".
Each reason is a line of code at a cited location, not a judgement.

### 1. game-design/sim-shots, WHOLE, including runs/

407 tracked files: 45 at the top level plus 362 under `runs/`.

THIS IS THE JUDGEMENT CALL AND IT CAME OUT FULLER THAN EXPECTED. CLAUDE.md
rule 12 names this directory as the feedback channel that works: "a file
committed by CI, under `game-design/sim-shots/`". The recommendation put to me
was to archive the historical contents and keep the channel alive. Having read
the readers, I kept the directory whole instead, because the history is not
history: it is a series that live instruments aggregate.

What reads it, measured:

    tools/gates.py:212,1065,1218,1551   RUNS.glob("*.txt") over ALL of runs/
    tools/d1-cycles.py:51,78            collect_history(runs_dir=RUNS)
    tools/d1-cycles.py:52               verdict.txt, the latest verdict
    tools/verdict-read.py:404           verdict.txt
    tools/ref-bench.py:362              frames.tsv, six landed revisions
    tools/runner/telegram-bot.py:2766   brief_<day>.jpg, the daily message
    tools/runner/brief.py:1134          brief_2026-09-10.jpg
    tools/runner/outbox.py:119,1250     SHOTS_DIR and the per-run link
    tools/report-frame.py:34,101        SHOTS, the frame the Producer sends
    tools/dashboard/build-dashboard.py:116  GATE_KEEP set from 358 of these runs

`tools/gates.py` globs every `runs/*.txt` to build its series and its
denominators. Archiving any subset would shrink every denominator it prints
while every number stayed plausible, which is the silent-instrument failure
`.claude/rules/instruments.md` was written for. `tools/dashboard/build-dashboard.py`
sets its `GATE_KEEP` cap from a sweep of 358 of these files and says so in the
comment beside the constant, so the series is load-bearing even where it is
only read once.

The pictures the current and next brief reference, kept by name and reason:

    brief_2026-09-10.jpg   today's brief, named at tools/runner/brief.py:1134
    brief_2026-09-11.jpg   tomorrow's brief, already committed and referenced
    verdict.txt            the latest verdict, where every reader already looks
    verdict-keys.json      the key contract the verdict readers parse against
    frames.tsv             the six-revision series tools/ref-bench.py measures
    clips.tsv              the clip index beside clips.jpg

And the directory already bounds itself: `tools/sim-shots-commit.sh:441` keeps
the newest twenty `runs/*.txt` and deletes the rest on every landed run. A
second, manual pruning regime fighting that one is how two conventions end up
running at once. The 362 files on disk are the backlog that prune has not
reached, and if the backlog should be cut, the place to do it is that line,
once, not here.

If Jafar wants this archived anyway, the work is not a `git mv`: it is updating
`tools/gates.py` and `tools/d1-cycles.py` to read two roots, and re-deriving
`GATE_KEEP` from the smaller series. That is a director's spawn and a CI round
trip, not a tidy-up.

### 2. ledger/breaks, 22 tracked files

`ledger/verify.py:2841` globs `ROOT/"breaks"/*.json` and, at line 2862, returns
RED when the walk yields zero anchors:

    if anchors == 0:
        return False, ("STALE ANCHORS: ... %d spec(s) in ledger/breaks/ "
                       "yielded 0 anchors, so nothing was compared")

(quoted with its separator elided, because the formatting law bans the
character `ledger/verify.py` uses there.)

That guard was added on purpose, because an empty `breaks/` printed the same
green string for 259 commits. Moving the directory turns the break-anchor gate
red on the next run with nothing to show for it. `ledger/breakrun.py` is the
other reader. Leave until someone decides whether break specs survive the
C++ port at all, which is a premise question, not a filing question.

### 3. Eleven of the twelve probe projects, 23 tracked files

Each has a named runner. Archiving any of them breaks that runner.

    Adversary     ledger/verify.py:2415 dotnet run --project Adversary
    BackendCheck  ledger/verify.py:825  loop over (BackendCheck, SpeechBench)
    SpeechBench   ledger/verify.py:825  same loop
    BarkGen       ledger/verify.py:2259 dotnet run --project BarkGen
    ConvoProbe    ledger/verify.py:1972 dotnet run --project ConvoProbe --dry
    ShapeCheck    ledger/verify.py:121 plus ledger-build-windows.yml:177 and ledger-build-mac.yml:54
    Tier2Gen      ledger/verify.py:1098 --selftest, plus tier2-generate.yml
    GameCheck     ledger/verify.py:1476 runs tools/gamecheck.py, which builds it
    ReachCheck    tools/reach-check.sh:27, the one invocation, called by verify.py and ledger-core-tests.yml
    SimHarness    ledger-ai-playtest.yml:25, tools/ci-checks.sh:87, and a --tests root in reach-check.sh
    BalanceLab    a --tests root in tools/reach-check.sh:31

`tools/reach-check.sh` is the sharpest case: it passes CoreTests, SimHarness,
BalanceLab, BarkGen and Tier2Gen as `--tests` roots in one argument list that
exists precisely because there used to be two copies of it and they drifted.
Removing a test root there silently reclassifies Core methods as "tested,
unwired".

### 4. ledger/Assets/Scripts/Game, 89 tracked files

The Unity game scripts stayed, and this is the item furthest from what Jafar
asked for, so the reason is given in full.

The five harnesses D16 says must keep running COMPILE these files. Measured in
the `.csproj` files themselves:

    CoreTests     Game/ActOne.cs, AccessSetup.cs, EconomySetup.cs, OperationSetup.cs
    Soak          Game/EconomySetup.cs
    StrangerTest  Game/LenaSetup.cs, CastSetup.cs, OperationSetup.cs
    SaveChaos     Core only
    PerceptionGolden  Core only

Beyond that:

    production/systems-inventory.json   57 distinct Game/*.cs cited as evidence, and tools/systems-inventory-check.py fails a path that does not resolve
    tools/surface-tint-check.py:45      UNITY = ledger/Assets/Scripts/Game/AssetLibrary.cs, a hard path
    tools/voice-cast-check.py:20        reads the cast ids out of Game/CastTier1.cs
    tools/systems-inventory-check.py:866  uses Game/GameController.cs as its ACCEPTING fixture
    tools/gamecheck.py:91               counts Game/**/*.cs and its allow-list FAILS when a known error stops occurring
    tools/reach-check.sh:28             scans Core AND Game as the reachability surface
    ledger/verify.py:121                ShapeCheck scans Assets/Scripts
    ledger-build-windows.yml:166,177    lint-usings and ShapeCheck over Assets/Scripts

The `gamecheck.py` allow-list is the trap. It holds one known error,
`'RenderSettings' does not contain a definition for 'customReflectionTexture'`,
and it is deliberately built to fail when that error STOPS appearing. The three
files that produce it (`StreetVignetteHost.cs`, `SkyEnvironment.cs`,
`WetReflections.cs`) are all Unity-bound Game scripts, so archiving them turns
a verify.py gate red by design, not by accident.

A split is possible: 11 of the 89 use no `UnityEngine` symbol at all
(AccessSetup, ActOne, CastSetup, EconomySetup, EmpireSetup, LenaSetup,
OnnxSpeech, OperationSetup, Perf, SecretsSetup, Tier2Setup) and are in practice
part of the reference surface D16 keeps. The other 78 are the engine-bound
layer. Doing that split means editing nine readers and re-deriving
`gamecheck.py`'s allow-list, and it cannot be validated from here: the Game
layer's only compiler is `ledger/GameCheck` under `verify.py`, which I was
instructed not to run. Director's call plus one CI round trip.

### 5. ledger/Assets/Characters, 91 tracked files

Two reasons, and the first is that the instruction does not resolve.

"the v1 character bodies" matches NOTHING in this repository: zero hits for
"v1 bod", "v1 character", "bodies v1" across every `.md` and `.json`. What is
on disk is eighteen body FBX from three Mixamo drops (2026-08-04, two drops;
2026-08-18, "ten more character bodies, picked from the real catalogue") plus
82 animation clips under A, B, C and D. There is no marked v1 set to move, and
guessing which six of eighteen he meant risks archiving a body the live roster
classifies.

Second, the live readers:

    ledger/Assets/Scripts/Core/BodyArchetype.cs:51  the roster is "read off the eighteen FBX in Assets/Characters"
    ledger/Assets/Editor/CharacterImport.cs:41      const CharacterFolder = "Assets/Characters/", a Unity AssetDatabase path
    ledger/Assets/Editor/CharacterPrefab.cs:35      const BodyModel = "Assets/Characters/Joe.fbx"
    tools/body-proportions.py:83,389                lists and parses every .fbx in that directory
    tools/attribution-check.py:49                   the row "ledger/Assets/Characters": "Mixamo", 82 asset files of 91 walked

That last one is licence law. `.fbx` is an asset suffix, and
`attribution-check.py` sweeps for "asset files outside a directory this file
knows about". Moving the FBX to `legacy/` without moving the WATCHED row turns
them into strays and `ledger/verify.py:1638` red.

CoreTests is NOT a blocker here, and that was checked rather than assumed: it
quotes renderer names as string literals (`Elvis_BodyGeo`, `Ch21_Eyelasshes`)
and reads no file from the directory.

What this needs from Jafar: which bodies are v1. One line from him makes this a
ten-minute move with one licence row edited and `attribution-check.py` re-run
to prove it.

### 6. game-design/picked-clips, 23 tracked files

`ledger/verify.py:2301` runs `tools/voice-cast-check.py`, which at line 36 sets
`CLIPS = game-design/picked-clips`, iterates it at line 95, and fails with
"cast as '<id>' but no clip in picked-clips". Moving the directory fails that
gate for every cast member at once. Also a WATCHED licence row
(`"game-design/picked-clips": "VCTK"`, 23 asset files of 23 walked), the source
`tools/voice-live/precompute-voices.py` computes the conditioning from, and the
fixture `tools/shape-check.py:432` rejects against.

### 7. game-design/voice-conds, 47 tracked files

`ledger/verify.py:1016` runs `tools/stage-voice-assets.py`, which stages the
nineteen voices out of `game-design/voice-conds` into the build;
`.github/workflows/ledger-build-windows.yml:195` runs the same script. It is
also a WATCHED licence row with the longest reasoning in that file (46 asset
files of 47 walked): each `.bin`/`.npz` pair is a transformed representation of
a VCTK recording and carries its parent's CC BY obligation.

### 8. game-design/voice-live, 17 tracked files

The PC watcher's return channel, not an archive: `tools/pc-watcher.py:810-820`
names twelve specific files under this directory as the artefacts it pushes
back from Jafar's machine so they can be heard from here. A WATCHED licence row
too (13 asset files of 17 walked). Live speech is a moat pillar and nothing
about D16 retires it.

### 9. voice-candidates, 67 tracked files

`.github/workflows/voice-candidates.yml` writes into this directory on every
run (lines 288 to 325, including seeding from and rewriting `listen.html`), and
`tools/voice-fetch/standalone_page.py:15` reads it as `SRC`. A WATCHED licence
row as well (65 asset files of 67 walked). The casting page is how a voice gets
picked; archiving the candidates archives the instrument.

### The decision and plan fold, same day, a DIFFERENT list

Items 1 to 9 above are the archive lane's list. Jafar also ruled, in the same
cleanup batch of 2026-09-10, one decision register and one plan. That fold
examined three more path groups and MOVED NONE OF THEM UNDER `legacy/`, so the
archive gained no files from it. Its counts, with denominators:

    pathGroupsExamined=3 pathGroupsMovedToLegacy=0/3 filesMovedToLegacy=0
    filesRelocatedWithinTheLiveTree=1 (the decided half of the card queue)
    registerFilesCreated=2 liveReadersUpdated=1/1-needed
    liveReadersThatBLOCKEDamove=4 gatesRerunAfterTheEdits=3/3-unchanged

The three gates re-run after the edits, with the numbers they printed, each
identical to the number it printed before:

    build-dashboard.py --selftest  139-passed/1-failed/1-not-run (the failure is
                                   the pre-existing "D1 countdown derives from
                                   the real dates: nothing-measured", printed by
                                   the unedited file at HEAD too)
    build-dashboard read_phases    rows=8 current=phase-0
    map.py visual_ladder           rows=7 columnsFound=4/4 badStatuses=0 current=rung-1

`ledger/verify.py` was NOT run, by the batch's own instruction: it runs alone and
other lanes were writing. Every claim below about a verify.py gate is read off
`ledger/verify.py` at the line cited, not off a run.

### 10. ledger-v2/respec/roadmap-v2.md, 1 tracked file

Jafar's ruling made `production/ladder.md` plus `production/queue/` the plan, so
this file's phase rows and exit gates were copied into `production/ladder.md`
and are maintained there. The FILE could not move, for three readers:
`CLAUDE.md:133` names it as the plan and `.claude/agents/planner.md:3` tells the
planner to decompose its milestones, and a separate lane owns both of those
paths this batch may not touch; and
`tools/dashboard/build-dashboard.py:417` sets
`SOURCES["roadmap"] = "ledger-v2/respec/roadmap-v2.md"`, which `read_phases` at
line 577 reads and `parse_roadmap` at line 311 parses into the dashboard's
current-phase reading. The file stays at its path, carries a banner saying it is
no longer the plan, and keeps its table parseable. When CLAUDE.md and the planner
brief are repointed it can move, and the dashboard source moves with it.

### 11. production/quality-ladder.md, 1 tracked file

The close question, best available or first working, is asked here, and
`CLAUDE.md:205` names this file as the place it is asked, with
`.claude/agents/world-designer.md:90` repeating the clause to that agent. Both
are in the lane this batch may not touch. A second reason is mechanical: the
obvious fold target is `production/ladder.md`, and `tools/map.py:1884` calls
`table_rows(text)` over that WHOLE file and treats the first table's header as
the rung contract (`columnsAsked=4`), so pasting this file's three aspect tables
in would break the project overview's first screen. Measured 2026-09-10: zero
code readers of this path, over every tracked `.py`, `.yml`, `.yaml`, `.sh` and
`.json` in the repository, so the two documents above are the whole reason. It
stays, bannered as an instrument of the plan rather than a second plan.

### 12. game-design/decision-*.md, 71 tracked files

The director's own rulings, folded INTO the register as index entries rather
than moved: `ledger-v2/respec/decision-register/rulings-log.md` carries one line
per ruling, in date order, with the path each lives at. The files themselves are
the live substrate of the commit gate. `ledger/verify.py:3124-3125` sets
`DIRECTOR_DECISION_DIR = "game-design"` and
`DIRECTOR_DECISION_GLOB = "decision-*.md"`, and line 3332 globs that directory IN
THE WORKING TREE for the `<!-- RULING spawn=... -->` stamps `director_cadence`
requires before a commit of builder work is allowed. THOSE TWO NUMBERS WERE
MEASURED ON 2026-09-10 AND HAD ALREADY MOVED 54 LINES THAT MORNING under another
lane's edits, so grep the symbols rather than trusting the numbers. Measured 2026-09-10: 68 of
71 files carry such a stamp and four are dated today, so moving them would pull
the stamp out from under the very commit that lands this fold. Moving them needs
that glob to move first, which is a change to the commit gate and a director's
call, not a cleanup's. THE COUNT IS A READING AT AN INSTANT: the brief said 70
and a concurrent lane added the 71st while the index was being generated.

## What is NOT archived, by D16, and this is not a courtesy

These keep running and no part of this sweep touched them:

    ledger/CoreTests  ledger/Soak  ledger/SaveChaos  ledger/PerceptionGolden
    ledger/StrangerTest  ledger/Assets/Scripts/Core

The C# Core is the source of truth the C++ port is checked against. That is the
whole reason the Unity retirement is an archive and not a deletion: a port with
no reference is a rewrite, and a rewrite is how behaviour drifts without anyone
being able to name the moment.

## Archived before 2026-09-10

Indexed here because one index file means one, not one per sweep.

### The v1 design package, superseded 2026-08-31 by the v2 respec

`legacy/design-doc.md` (52412 bytes), `legacy/roadmap.md` (47282 bytes),
`legacy/visual-bar-spec.md` (26157 bytes).

Was: the v1 design document, the v1 roadmap, and the visual bar specification
written against it.

Why they stopped: the LEDGER v2 respec package landed on 2026-08-31 and
supersedes all prior roadmaps, design docs and specs. Authority moved to
`ledger-v2/`, entry point `ledger-v2/handoff/HANDOFF.md`; world facts moved to
`canon.md`. Each file carries the superseded banner at its own top, so an
excerpt read from the middle still says so. They are inputs, not law, and
nothing in them may be cited as current without checking `ledger-v2/` first.
`legacy/roadmap.md` also carries the GTA V on PS3 visual bar that D8 retired.

### The CLAUDE.md passages cut on 2026-09-01

`legacy/claude-md-superseded-2026-09-01.md` (3088 bytes).

Was: passages live in CLAUDE.md until task `production/queue/013` cut that file
down to standing rules.

Why they stopped: superseded, but they record real orders Jafar gave, so they
were moved rather than deleted. The rest of that cut went to the casebooks
under `ledger-v2/studio-v2/`, by rule number, listed at the bottom of
CLAUDE.md.

### Retired outbox messages

`legacy/outbox/`, 2 files.

Was: `2026-09-03-batch-landed-and-the-wait.EXPIRED.md` plus the README that
defines the directory.

Why it stopped: the message was written, never sent, and can no longer be sent.
Its own first line says the Unreal run it asked about has since gone and the
street it promised now shows its textures. The 494 refusal records for this
exact message are the sweep of 2026-09-10, section 6 above, and they now sit at
`legacy/outbound-refusals-2026-09-03/`.

## How to add to this file

One entry per archived thing, in the sweep's own section, carrying: what it
was, what it was for, WHY IT STOPPED with the ruling or measurement behind it,
the date, and the new path. Then the counts, with denominators. Before moving
anything, grep for what reads it: a path a workflow, a live tool or
`ledger/verify.py` still calls is a path that breaks the gate when it moves,
and either the reader moves in the same commit or the path stays and the reason
is written in the "Left in place" section.

### 23. The standalone voice page builder

Was: `tools/voice-fetch/standalone_page.py`, last touched 2026-07-31.

For: building the voice-candidate audition page as ONE self-contained file, with
all 114 clips inlined as data: URIs, so it could be opened on a phone from a
link with no web server. That constraint is what forced the mp3 trimming beside
it.

Why it stopped: it is the only orphan in the studio's 147 tracked tools. Nothing
names it and nothing imports it: 0 readers across every tracked `.py`, `.sh`,
`.yml` and `.ps1`, checked both by filename and by `import`/`from <stem> import`,
which is the check that matters here because a Python import never writes the
`.py`. Its two dependencies stay in the working tree and are NOT archived, both
having live readers: `mp3trim.py` is imported by this file alone but also named
in the roadmap history, and `mp3probe.py` is imported by
`tools/shape-check.py:29`.

The auditions it built are decided. The voice line now runs through the corpora
work, and a future audition page would be regenerated rather than resurrected.

Now at: `legacy/v1-era/voice-fetch/`

    files=1 bytes=3549 orphanSweep=1-orphan/11-docs-only/135-reached-by-code-of-147-examined
