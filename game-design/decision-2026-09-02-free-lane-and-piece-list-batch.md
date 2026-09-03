# DIRECTOR RULING: the free lane and the piece list land in one commit, the batch push is imagegen run 1, the window practicals are fixed in Core before Phase B, and a ruling now names the paths it reviewed (2 Sep 2026, evening)

> **STATUS: LOG, 2026-09-02. NOT CURRENT once the batch is committed with L1 to L6 applied and imagegen run 1 has landed a verdict; from then the code, the committed verdict, the queue and production/NOW.md are the reading copies and this file is their history.**

This document carries exactly one em-dash, in the banner, because
`tools/docs-check.py` line 55 accepts no other form (read this session).

Eleventh ruling since 1 September. No shell in this spawn: every number
below was read from a file this session and the file and line are named
beside it. The two builders' reports and the resident's brief were read as
CLAIMS; the diff, the fixtures and the landed run files were read as
evidence. Cost: roughly 2 points against a reading of 32 percent at 14:40Z
and no daily ration (NOW.md 79 to 82).

## What was verified

- My row: `.claude/agent-log.tsv` line 208, `2026-09-02T16:05:45Z
  studio-director`, the newest in the file. `.git/logs/HEAD` line 366: the
  newest commit is `9d690e92` at epoch 1788363615 (15:40:15Z). My row is
  newer than every commit in the reflog. Rows 204 to 207 are the four
  engine-specialist rows of this batch; row 203 (14:56:47Z) is the
  tie-break ruling, which is the row the gate is currently satisfied by.
- `ledger/verify.py`: `director_cadence` 4829 to 4976; `_cadence_read` 2713
  to 3161 (the reference rule 2936 to 2963, the stamp pairing 3128 to 3146,
  the states 3148 to 3159); `_cadence_rulings` 2649 to 2710, where line
  2702 builds a dict from every `key=value` in the stamp and reads only
  `spawn`, so an extra token is ignored, as the comment at 2485 to 2486
  promises; `DIRECTOR_WORK` 2345 to 2369 (`ledger/` and
  `.github/workflows/` are work); `DIRECTOR_EVIDENCE` 2398 to 2440 (no
  entry under `ledger/Assets/StreamingAssets/`); line 104, verify runs
  CoreTests, so a red CoreTests is a red verify.
- `.github/workflows/ledger-imagegen.yml` in full (363 lines): the push
  trigger on the sentinel 103 to 105, the concurrency group 112 to 114,
  the account and weights print 168 to 183, the sha from the checkout 189
  to 195, the batch flags 245 to 256, the commit by name 272 to 336 (the
  verdict's exit code captured at 293 to 296, `.BLANK.png` never staged
  per 300 to 306), the last step 342 to 362. Every `shell: bash` step, so
  the tee pipelines run under Actions' default `-eo pipefail`.
  `ledger-vignette-fetch.yml` 137 to 204, the model, matched clause by
  clause. `tools/runner/bootstrap-paths.cmd`, `tools/runner/python3-shim.sh`,
  `tools/imagegen/probe-machine.ps1`, `tools/attribution-check.py` and
  `game-design/agent-reports/machine-report.txt` exist.
  `ledger-core-tests.yml` 4 to 12: the batch push and run 1's own commit
  each start one cheap ubuntu job and nothing else.
- `production/d1-probe/RUN-IMAGEGEN` in full (45 lines).
  `tools/imagegen/prompts.json`: 45 ids; the 14 PNGs under
  `ledger/Assets/StreamingAssets/Decals/generated/` are exactly the first
  14 ids in file order (lines 199 to 494), so the next four in order are
  `sign_ferry`, `sign_harbour_master`, `sign_weighbridge`,
  `sign_telephone` (519 to 558), as the sentinel predicts.
- `tools/imagegen/imagegen.py`: `blank_verdict` 1255 to 1278 (three
  answers, `unknown` is not a pass); the loop's stop 1900 to 1919 (checked
  before the next item, so an undecodable PNG is seen); the skip logic
  1961 to 2021 and the limit stop 2022 to 2037 (after the free skip, so it
  counts generations); the rename to `.BLANK.png` at 2115;
  `imagegen_verdict` 2285 to 2405 (re-measures every manifest-named file
  from disk, `manifestIsThisRun`, BLANKS tested before NO-RUN at 2384 to
  2396); `staged_file_list` 2446 to 2466 (nothing but the verdict when the
  manifest is another run's); the lane fixtures 3307 to 3459, of which the
  `--limit` pair at 3372 to 3394 asserts `fake4.seen == ids[2:4]`, a value
  positional semantics cannot produce (it would be `[]`), so the fixture
  is not vacuous by construction; `--verdict` wired at 3757.
- `ledger/Assets/Scripts/Core/StreetVignettePieces.cs` in full (452
  lines): `PieceLine` 121 to 151 (sixteen fields, roll at 145), `Write`
  200 to 365, `Parse` 385 to 428 (fail-closed on a missing key, 430 to
  448). `production/specs/vignette-pieces.json` lines 1 to 60: line 10
  `pieces=546 unique_names=546 emissive=4 multi_rotation=0`, line 11 the
  shapes line `cylRolled=9 cylPitched=32 cylUpright=105`, line 13 the
  lantern block, line 15 the tiling table; six `_interior` pieces by grep.
- `ledger/CoreTests/Program.cs` 19566 to 19982: the layer comment 19568 to
  19587, `Difference` 19598 to 19617, `TryReadEmittedPieces` 19639 to
  19655, `TryReadRunStamp` 19666 to 19682, `WriteVignettePieces` 19714 to
  19740 (called only from `--write-vignette-pieces`, lines 37 to 39), the
  three questions 19811 to 19972, `MULTI_ROTATION_EXPECTED = 0` at 19982.
  `TestStreetVignette` 19299 to 19363: the piece total is PRINTED at 19301
  and asserted nowhere (grep `Pieces.Count ==` hits nothing in the file),
  which is the builder's 537 finding, confirmed in the code.
- `game-design/sim-shots/runs/152198e.txt` line 94 `plan pieces=546
  feet=845`, line 95 `emitted pieces=546/546 errors=0`, line 98
  `probes=845 datumMissing=0/845`; `8f19add.txt` line 95 carries the same
  emitted line, so the cross-engine check has two landed runs to read and
  picks the newer by epoch.
- `ledger/ReachCheck/allow.json` grep for `StreetVignettePieces`,
  `Difference`, `TryReadEmittedPieces`, `TryReadRunStamp`: nothing, so the
  revert is real. `ledger/ReachCheck/Program.cs` 43 to 65: consumers are
  Core, Game, `--also` dirs and `--tests` dirs, and a member called only
  from tests reads as tested-unwired (47 to 54). Grep of
  `ledger/Assets/Scripts/Game` for `StreetVignettePieces`: nothing. So
  `Write`, `Parse`, `Number`, `PieceLine` and the three counters have no
  Game caller either, and whether the reach tool flags them is NOT
  something I can read from here; L3 measures it.
- The window practicals. `production/specs/vignette-scene.json` 268 to
  276: `lit_bays [0, 2, 5]`, `shop_intensity 1.6`, `shop_range_m 7.0`,
  `flat_intensity 0.8`, `flat_range_m 5.0`, no colour. Grep of
  `ledger/Assets/Scripts` for `shop_intensity|lit_bays|LitBays`: nothing,
  so Core never reads the block. `StreetVignetteHost.cs` 259 to 272: every
  `_interior` piece gets `Color(1f, 0.86f, 0.62f)`, range 7, intensity 1.6.
  Six interior cards exist, so the landed night frames light six bays
  against a JSON that says three.
- `StreetVignette.cs` `Foot5` 274 to 291 (the swap at 282, the fields a
  probe carries at 288 to 289); `GroundAt` used at `Program.cs` 19296 with
  an out level and an out edge. `production/queue/`: 039 is the highest
  number; 027, 033, 039 in full; `README.md` 1 to 31.

## Ruling 1: the batch LANDS, one commit, after L1 to L6

Both halves are the work the queue asked for, nothing weakens an
instrument, and three instruments that did not exist now do (the blank
verdict re-measured at commit, the drift guard with its round trip, the
cross-engine count). Premise check: nothing here touches world facts or the
engine decision; the piece list is the D1b shared-JSON rule made
mechanical, which serves the moat's instrument rather than the moat
itself, and that is the right shape for slot 1 under the 14:56 ruling.

**Landing conditions, exact, nothing judged at apply time.**

L1. `python3 ledger/verify.py` green, footer FROM THE FILE. The commit
message quotes the CoreTests count (the brief says 4234) and the
`imagegen --selftest` count (123/123) from runs after every edit below.

L2. Staged by name and nothing else: `.github/workflows/ledger-imagegen.yml`,
`production/d1-probe/RUN-IMAGEGEN`, `tools/imagegen/imagegen.py`,
`ledger/Assets/Scripts/Core/StreetVignettePieces.cs`,
`production/specs/vignette-pieces.json`, `ledger/CoreTests/Program.cs`,
this record, and the owed text of W1, S1, T1, T2, N1, Q1, Q2, Q3 below.
BEFORE staging, `git status --porcelain` is read in full: any pending path
inside `DIRECTOR_WORK` (verify.py 2345 to 2369) that is not in the
`paths=` list of this record's stamp is NOT covered by this ruling; it is
left out of the commit and this director is RESUMED with the list, never
restarted (Ruling 7 says why).

L3. THE REACH MEASUREMENT, which nobody has quoted. Run the reach check
the way `ledger-core-tests.yml` runs it (`tools/reach-check.sh`) and quote
its summary line in the commit message. Two outcomes, both decided here:
if no `StreetVignettePieces` member is reported unreached, nothing to do;
if `Write`, `Parse`, `Number`, `PieceLine`, `MultiRotationCount`,
`EmissiveCount` or `UniqueNameCount` are reported, the entries go into
`ledger/ReachCheck/allow.json` as BY DESIGN, each with this reason:
`BY DESIGN: the generator and reference reader of production/specs/vignette-pieces.json, called by ledger/CoreTests --write-vignette-pieces and the drift guard; the consumers are the Unreal emitter, which reads the FILE, and the C++ reader transliterated from Parse. No Game caller exists or should (decision-2026-09-02-free-lane-and-piece-list-batch.md, Ruling 3).`
The resident's instruction "never an allow entry" is corrected in
writing: the ledger's own header (allow.json 3 to 8) names BY DESIGN as
one of two acceptable reasons, and this is that case. What stays
forbidden is an entry for a helper that belongs in the test harness, which
is what the builder correctly moved instead (Ruling 3).

L4. W1 applied to the workflow comment (Ruling 2), because the phrase "two
independent things" will be read by the next person as two classifiers.

L5. Every edit id in this record listed in the commit message as `applied`
or `deferred: <reason>`, per the 10:42 ruling's Ruling 5, and the next
director greps that list first.

L6. Push. Know what it triggers (rule 9): `ledger-imagegen.yml` on the
sentinel, once; `ledger-core-tests.yml` on `ledger/**` and
`game-design/**`, cheap. Nothing Unity, nothing on the licence seat.

## Ruling 2: the free lane. Two gates on the process, one classifier, and the push IS the dispatch

**Two gates or one counted twice.** Both gates call `blank_verdict` over
`png_stats` of a file (imagegen.py 2101 and 2336). They are independent in
MOMENT and INPUT: the loop measures each PNG as it is written and stops
the batch (1908 to 1919); the verdict measures every file the manifest
names, from disk, at commit time, and refuses a manifest stamped by any
other run (2302, 2386 to 2387). So a manifest that says OK about a blank
file, a file replaced or missing after generation (2331 to 2333), a
generator run without the flag, and a stale manifest under a new run's
name are each caught by the second gate when the first cannot see them.
They are NOT independent in CLASSIFIER: a bound that is wrong passes
both. That is acceptable for two reasons that are both on the record: the
bound was read off a printed series (`png_series`, 2509 to 2532, "This is
what BLANK_MAX_SPREAD was read off"), and rule 4 opens the PNGs before
anything is called banked. The workflow's comment overstates it, hence W1.

**`--limit` counts generations.** Confirmed in the code (the stop sits
after the free skip, 2022 to 2037) and in a fixture that positional
semantics cannot pass (3386 to 3394). Not vacuous.

**Run 1 goes tonight, because landing the batch IS run 1.** The sentinel
is a new file in this commit and the workflow's push trigger names it
(103 to 105); there is no way to land the route without firing it, and no
reason to want one: it costs zero Claude points, the runner is idle
(NOW.md 90), four pictures estimate 4.5 minutes and the download, if the
runner account differs from Jafar's, dominates and is bounded by the
130-minute ceiling. What run 1 proves is the ROUTE, not the pictures.
Read, in this order, before opening anything: the committed verdict's
line 1 (the sha, which must be the batch's); the `done imagegenVerdict=`
line (BANKED, BLANKS or NO-RUN, with its `why`); the run log's
`runnerAccount=` and `weightsDirectory=` lines, which answer the builder's
named cost. Then open all four PNGs (rule 4). A red is a finding with its
cause named in the verdict, never a broken runner.

**A consequence the workflow's rule 9 paragraph does not name.** Run 1's
own commit lands PNGs, a manifest and a verdict under `ledger/`, which is
`DIRECTOR_WORK`, and nothing in `DIRECTOR_EVIDENCE` excludes them. So the
machine's commit will move the cadence reference and spend this ruling.
Harmless tonight, since the next batch needs its own director anyway, and
wrong in principle: a machine's report about a run is evidence, not work.
Queue 042 item (2) is the one-line fix; not applied here because it edits
the gate and the gate's fixtures are where that edit is watched both ways.

**Queue 039 does not close.** Its acceptance says "the same route proven
for meshgen"; this batch proves imagegen only, and a route is proven by a
landed BANKED verdict, not by a parse. S1 records the half that landed and
the half that waits for run 1.

## Ruling 3: the piece list. The layer reasoning is confirmed, the fields all stay, and one number is not written a third time

**The three helpers belong in CoreTests.** Confirmed. `Difference`,
`TryReadEmittedPieces` and `TryReadRunStamp` ask whether committed
evidence still describes the world; no player asks that, and the 25 Aug
rule ("where the tests run") is satisfied because CoreTests executes every
line on every run. `Write` and `Parse` stay in Core for a different reason
than the builder's comment gives: not because "the Unreal emitter has to
be able to call them" (it is C++ and reads the file), but because `Parse`
is the reference reader Phase 1 transliterates, and the file's format is a
contract that belongs with the engine-neutral layer. L3 measures what the
reach tool says about them and names the answer either way.

**The four fields beyond the ruling's list all stay.** `edge` and
`region`: the per-edge breakdown is the half of the placement instrument
that saw eight blocks over open sea, and two engines reporting against two
partitions is the same fault one level up. `sun` and `surface_tiling`:
data both emitters need; a second copy of the tiling table is a second
street. `counts.multi_rotation`: measured 0 of 546 and asserted at 19933,
which is the number that lets Unreal compose Euler angles in any order;
the day it moves, the test is what says so.

**The 537 finding is recorded and not patched.** `TestStreetVignette`
prints the total and asserts the shapes line, the lantern count, and the
cameras, conditions and shots; a scene that lost nine pieces of the right
shape passes it. The total is now pinned twice: by the committed file's
bytes (drift) and by the landed run's `emitted pieces=546/546`
(cross-engine). A third hard-coded 546 in `TestStreetVignette` would be
one number three times (rule 2) and is refused.

## Ruling 4: referred item 1. The window practicals are fixed in Core BEFORE Phase B (queue 040)

The builder was right to keep them out of the file: writing a parity the
engines do not have would have been the file lying. But the fault is not
the file's, it is that Core never reads `lighting.window_practicals` and
the Host invents three numbers and ignores a fourth. Phase B's UE emitter
will either invent its own (a second street) or read nothing (a dark
parade), and the first night pair will be judged on that difference and
blamed on the renderer. So it is fixed in Core, in the local loop, before
any UE night frame exists.

Named consequence, so it is not discovered on the still: the Unity night
frame CHANGES. Today six bays are lit; the JSON says three, and its note
says why ("every unit lit is a shopping centre"). The cam_A night frame
NOW.md calls the best the project has made will lose three lit windows on
the next dispatch. That is the data decision the JSON already made,
applied; if the frame is worse for it, the value moves in the JSON, in
both engines at once, and never in a Host constant. The colour, which is
in neither, goes INTO the JSON as the Host's value with its colour space
named, because it has rendered once and is the only number that exists.

Q1 is the item. It rides the next 027 session with A2 and 041 (Ruling 8).

## Ruling 5: referred item 2. The sharp edge is a deadlock, and the acknowledgement key is required before the first layout change (queue 041)

The builder judged the cross-engine red "correct rather than annoying".
Correct in direction, and worse than annoying in mechanics: a deliberate
piece-count change makes CoreTests red, verify runs CoreTests (verify.py
104), red verify writes no footer, the convention forbids the commit, and
the Unity run that would turn it green needs the commit pushed. Nothing
in the tree can land a layout change today without breaking a rule. The
escape the builder named is therefore not an option but a prerequisite,
and its shape is ruled now so it is not designed under pressure:

- The key goes through the GENERATOR, never by hand:
  `--write-vignette-pieces --ahead-of-run <sha>` writes a top-level
  `ahead_of_unity_run` block naming the run and its count; the drift guard
  feeds the committed block back into `Write` so regeneration stays
  byte-stable.
- It EXPIRES. The cross-engine check passes on the key only while the
  named run is still the newest landed run with a piece line, and prints
  `AHEAD-OF-RUN <sha> file=N run=M acknowledged`. The moment a newer run
  lands, the key is stale: green only if that run's count equals the
  file's, and then the check demands the key's removal; red otherwise.
- Both outcomes watched, accepting first, on a planted layout change.

Before: any change to `counts.pieces`. Phase D (the body) is one; 028 is
one if its plates are geometry; 033 and 040 are not (feet and lights are
not pieces).

## Ruling 6: referred item 3. The probes go in a second file from the same generator (027 Phase A2)

Agreed that `Foot5` is never re-derived in C++. The file is
`production/specs/vignette-feet.json`, written by the same
`--write-vignette-pieces` run (one command, two files), one probe per
line from `plan.Feet` (845 today: name, bom, edge, region, x, z) plus the
datum the plan expects at that probe, from `GroundAt` (level and edge), so
the UE instrument compares a raycast to a NUMBER in the file and never
re-derives the crossfall. Same guard shape: byte-identical regeneration,
parse back, count equal to the plan's `feet=` print and to the landed
run's `probes=845` denominator (152198e.txt line 98). Not folded into the
piece file: 845 lines of probes inside a 546-piece list makes the review
diff the thing the one-piece-per-line rule was written against. 033
(rotated corners) changes this file and the drift guard is what shows it.

## Ruling 7: the gate hole. Worth closing, and the record side closes it tonight for nothing

The family, named: attendance is not review (25 Aug, closed by the
stamp); a ruling is not an application (2 Sep morning, closed by the
`applied/deferred` list); newer is not about-this (now). The gate proves
a fresh ruling EXISTS; this batch rode a ruling that reviewed a premise
question and never saw a line of it, and the gate said `REVIEWED`.

The cheapest decisive closure is the one the brief guessed, and the
format already tolerates it: `RULING_KV` parses every `key=value` in the
stamp and the reader takes only `spawn` (verify.py 2702), so a `paths=`
token costs nothing to write today and the gate learns to read it later.
This record carries one. Rejected alternative: a hash of the pending diff,
because the dictated edits legitimately change the diff after the ruling
and the hash would refuse every honest apply.

In force from this record, no tool: a ruling's stamp lists the pending
work paths it reviewed, comma-joined, no spaces; the resident compares
`git status --porcelain` against it before staging (L2); an unlisted
pending work path is uncovered and resumes the director. What this cannot
see, stated: content added to a LISTED path after the ruling. That is the
`applied/deferred` list's job, and the two conventions together are the
interim instrument until 042 lands the gate half.

Queue 042 (Q3) is the gate half, and it WAITS behind the moat and
admissibility items exactly as the 14:56 ruling's Ruling 4 orders for
governance; the convention above is what holds until then.

## Ruling 8: the next 027 session, and the order

Slot 1 tomorrow is one engine-specialist session, "027 Phase A close-out":
040 (Ruling 4), A2 (Ruling 6), 041 (Ruling 5), all Core and CoreTests, all
in the local loop, one dispatch of `ledger-build-windows.yml` at the end
to render the three lit bays and re-read `datumMissing`, the shapes line
and `windowsLit=3/6`. Phase B follows in the session after. Slot 2 stays
037. Nothing else moves.

## Dictated edits. Each id is listed in the commit message as applied or deferred with a reason

**W1. `.github/workflows/ledger-imagegen.yml`** lines 66 to 69, from `So
two independent things happen here:` to `cannot go green.`, become:

```
# So ONE classifier (imagegen.py blank_verdict, its bound read off a printed
# series) is applied at two moments to two inputs: the generator runs with
# --fail-on-blank, which measures each PNG as it is written and stops at the
# first blank or unreadable one with exit 6; and the verdict RE-MEASURES every
# PNG the manifest names, from the file's own pixels at commit time, so a
# manifest that says OK about a blank, missing or replaced file cannot go
# green. Independent in moment and input, not in classifier: a wrong bound
# passes both, which is why the PNGs are opened before anything is called
# banked (CLAUDE.md rule 4).
```

**S1. `production/queue/039-free-lane-dispatch.md`** line 5 becomes:

```
status: HALF LANDED 2026-09-02 (game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md, Ruling 2): the imagegen workflow and its sentinel are in the tree and the batch push is run 1 (four signs, zero Claude points). The meshgen half WAITS for run 1's committed verdict: a route is proven by a landed BANKED verdict and not by a parse, and proving a second tool on an unproven route is two unknowns in one run.
```

**T1. `production/queue/027-ue-vignette-emitter.md`** line 5, append to
the status line:
` Phase A LANDED 2026-09-02 (game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md): 546 pieces, sixteen fields, drift plus round-trip plus cross-engine guard. Phase A2 below, queue 040 and queue 041 are ONE engine-specialist session, the Phase A close-out, before Phase B.`

**T2. `production/queue/027-ue-vignette-emitter.md`**, insert after line
19 (the end of Phase A):

```
## Phase A2: the probes, same generator, second file

`production/specs/vignette-feet.json`, written by the same
`--write-vignette-pieces` run: one line per probe from `plan.Feet` (845
today: name, bom, edge, region, x, z) plus the datum the plan expects there
from `GroundAt` (level and edge), so the UE placement instrument compares a
raycast to a number in the file and never re-derives `Foot5` or the
crossfall in C++. Same guard shape as the piece list: byte-identical
regeneration, parse back, count equal to the plan's `feet=` print and to
the landed run's `probes=845` denominator (runs/152198e.txt line 98). Ruled
2026-09-02 (free-lane-and-piece-list ruling, Ruling 6). Queue 033 changes
this file and the drift guard is what shows it.
```

**N1. `production/NOW.md`** lines 84 to 92 (from `IN FLIGHT RIGHT NOW:` to
the end of `## In flight`) become:

```
IN FLIGHT RIGHT NOW: imagegen run 1. Queue 039's workflow and 027 Phase A
(the flat piece list, 546 pieces, three guards) were reviewed together and
landed under game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md.
Landing the batch pushed production/d1-probe/RUN-IMAGEGEN, and that push
IS the first imagegen dispatch: four signs on ledger-pc, zero Claude
points, 4.5 minutes if the weights are already on the runner's account and
a 7 to 10 GB download first if they are not.

## In flight

- Imagegen run 1, fired by the batch push. Watch by ancestry for a commit
  titled `Meridian pictures from <sha>`. Read, in this order, before
  opening anything: ledger/Assets/StreamingAssets/Decals/generated/
  imagegen-verdict.txt line 1 (the sha must be the batch's), the
  `done imagegenVerdict=` line (BANKED, BLANKS or NO-RUN with its why),
  then the run log's `runnerAccount=` and `weightsDirectory=` lines. Then
  open the four PNGs. A red is a finding with its cause in the verdict,
  never a broken runner. Run 1's own commit moves the cadence reference
  (queue 042 item 2 says why); expected, not a fault.
- NEXT ACTION, tomorrow: slot 1 is the 027 Phase A close-out (queue 040
  window practicals in Core, Phase A2 the feet file, queue 041 the
  acknowledgement key), one engine-specialist, one Unity dispatch at the
  end; the night frame will show THREE lit bays, not six, and that is the
  JSON applied. Slot 2 is 037. The report to Jafar after run 1 carries
  one of the four signs as its picture, or the verdict's why if red.
```

**Q1. `production/queue/040-window-practicals-in-core.md`**, new file:

```
line: production (D1 comparison, admissibility)
spec: game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md, Ruling 4
acceptance: Core reads lighting.window_practicals (lit_bays, shop and flat intensity and range, and a colour ADDED to the JSON as the Host's current value with its colour space named) into the Plan; StreetVignettePieces.Write emits a window_practicals block beside lantern and the drift guard is regenerated; StreetVignetteHost reads every value from the Plan, lights ONLY the listed bays, and prints `windowsLit=N/M` on the sim verdict with M the interior cards; the flat values, which light nothing today (D8_upper_windows carry no interior card), print `flatsLit=0/0 nothing-to-light` rather than vanish; CoreTests asserts 3 of 6 from the plan and the same after the round trip; one Unity dispatch shows three lit bays
max_sessions: 1
status: READY 2026-09-02. engine-specialist. Rides the 027 Phase A close-out session with A2 and 041, BEFORE Phase B.

FACTS INLINE. production/specs/vignette-scene.json 268 to 276 carries
lit_bays [0, 2, 5], shop_intensity 1.6, shop_range_m 7.0, flat_intensity
0.8, flat_range_m 5.0 and no colour. Nothing in ledger/Assets/Scripts reads
any of it (grep shop_intensity|lit_bays: 0 hits). StreetVignette.cs 1318 to
1319 is the lantern's read and the pattern; Plan fields at 197.
StreetVignetteHost.cs 259 to 272 lights every `_interior` piece (six in
production/specs/vignette-pieces.json) with Color(1, 0.86, 0.62), range 7,
intensity 1.6, shadows off. The pieces file's lantern block (line 13) is
the pattern for the new block. NAMED CONSEQUENCE: the Unity night frame
loses three lit windows; if that is worse, the value moves in the JSON for
both engines and never in a Host constant.
```

**Q2. `production/queue/041-piece-list-ahead-of-run-key.md`**, new file:

```
line: infrastructure (instruments, the cross-engine guard)
spec: game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md, Ruling 5
acceptance: `--write-vignette-pieces --ahead-of-run <sha>` writes a top-level ahead_of_unity_run block (run, pieces_then) and the drift guard feeds the committed block back into Write so regeneration stays byte-stable; the cross-engine check passes on the key ONLY while the named run is the newest landed run carrying a piece line, printing `AHEAD-OF-RUN <sha> file=N run=M acknowledged`; a newer landed run makes the key stale: green only if that run's count equals the file's, and then the check demands the key's removal; red otherwise; both outcomes watched on a planted layout change, accepting first; never hand-edited
max_sessions: 1
status: READY 2026-09-02. engine-specialist. Rides the 027 Phase A close-out session. REQUIRED before the first change to counts.pieces (Phase D's body; 028 if its plates are geometry). Without it a layout change cannot be committed: CoreTests red, verify red (verify.py line 104), no footer, and the Unity run that would clear it needs the commit.
```

**Q3. `production/queue/042-cadence-ruling-names-its-paths.md`**, new file:

```
line: infrastructure (the director cadence gate)
spec: game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md, Rulings 2 and 7
acceptance: (1) _cadence_rulings reads an optional `paths=` token (RULING_KV already parses it, verify.py 2485 to 2488 and 2702) as a comma-joined list; a fresh ruling COVERS a pending work path it lists; a stamp with no paths= covers everything and prints `rulingPathsUnscoped=1` so records from before this change stay valid; new state `uncovered` when the diff is substantial, a fresh ruling exists, and a pending work path is listed by none, printing `rulingPathsCovered=<n>/<pending work paths>` and the first uncovered path verbatim; accepting case first on the live tree (this record's stamp), rejecting case a fixture with one pending path not listed; (2) `ledger/Assets/StreamingAssets/Decals/generated/` joins DIRECTOR_EVIDENCE with the label imagegenout (the PNGs, manifest, verdict, made.json, PROGRESS.txt and ATTRIBUTION.json that ledger-imagegen.yml's own commit writes about a run), and the "5 of the 15" paragraph at verify.py 2382 to 2391 is re-counted as its own text demands
max_sessions: 1
status: WAITS 2026-09-02 behind the moat and admissibility items, per the 14:56 ruling's order for governance. Until it lands, the record-side half is IN FORCE by convention: every ruling stamp lists the paths it reviewed and the resident compares git status against it before staging (Ruling 7 and L2). Third instance of one family: attendance is not review (25 Aug), a ruling is not an application (2 Sep morning), newer is not about-this (2 Sep evening).
```

**Not edited, and why.** `ledger/verify.py`: the gate is edited only with
its fixtures, in 042. `production/quality-ladder.md`: neither 039 nor 027
closes here; the ladder question is asked at their close, and the next
rungs are already named in the queue (A2, 040, 041, the night run that
empties the imagegen queue, the meshgen half). `canon.md`: no world fact
touched. The tie-break ruling's edits T1 to T8, M1 to M4, Q1 to Q5, B1:
not re-verified in this spawn; the next director greps the 14:56 record's
list against the tree first, per the 10:42 ruling's Ruling 5.

## Deliberately not decided

- Whether three lit bays are better than six. The frame decides, and the
  value lives in the JSON.
- Whether run 1 pays the download. `runnerAccount=` and
  `weightsDirectory=` say.
- Whether the flood in cam_B night is the JSON or the conversion. Unchanged;
  the first UE night frame.
- The engine. Unchanged.
- Whether the reach tool flags the Core writer. L3 measures it and both
  answers are already ruled.

## For the next session in one line each

- Apply L1 to L6 with W1, S1, T1, T2, N1, Q1, Q2, Q3; `git status` against
  the `paths=` list before staging; verify; one commit staged by name; the
  message quotes the CoreTests count, the selftest count, the reach line
  and lists every id; push, and that push is imagegen run 1.
- When run 1 lands: line 1, the done line, the account and weights lines,
  then the four PNGs; one report to Jafar with a sign as the picture.
- Tomorrow slot 1: the 027 Phase A close-out (040, A2, 041), one Unity
  dispatch at the end; slot 2: 037.
- Resume this director, never restart, if git status shows a pending work
  path the stamp below does not list, if the reach line names anything
  outside L3's two answers, or if run 1's verdict is red for a cause the
  verdict does not name.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 208):

    2026-09-02T16:05:45Z	studio-director

<!--RULING spawn=2026-09-02T16:05:45Z paths=.github/workflows/ledger-imagegen.yml,production/d1-probe/RUN-IMAGEGEN,tools/imagegen/imagegen.py,ledger/Assets/Scripts/Core/StreetVignettePieces.cs,production/specs/vignette-pieces.json,ledger/CoreTests/Program.cs,ledger/ReachCheck/allow.json-->
