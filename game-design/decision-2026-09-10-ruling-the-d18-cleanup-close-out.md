<!--RULING spawn=2026-09-10T12:25:43Z-->
# LOG: ruling on the D18 cleanup close-out, 2026-09-10

> **STATUS: LOG, 2026-09-10. NOT CURRENT** once the two commits in section 9
> have landed carrying the printed lines section 11 requires. Director ruling
> on Jafar's cleanup and canon batch of 2026-09-10, before the resident commits
> it. Escalation was tripped four ways (Core, canon.md, a changed conclusion,
> a close-out) and this one record covers all four. It binds the resident and
> the builders named in it. Section 14 was added after sections 1 to 13, on
> the coordinator's request, and rules on 14 new gate hits found after the
> first thirteen sections were acted on.

Author: tier-1 director spawned 2026-09-10T12:25:43Z, row 522 of
`.claude/agent-log.tsv`, the last row in the file (522 lines counted by grep
this session; the row reads `2026-09-10T12:25:43Z` TAB `studio-director`). If
the cadence gate reads this stamp as unmatched or stale, the resident pastes
the gate's own numbers into section 11 and does not touch the stamp: a
resident never stamps a ruling.

VERDICT: APPROVED FOR COMMIT, AS TWO COMMITS IN A FIXED ORDER, WITH FOUR
DICTATED EDITS, TWO CROPS, AND ONE QUESTION TO JAFAR ANSWERED IN THIS RUN.
Nothing in the batch is refused. One of the ten questions was wider than the
brief knew: there are TWO rendered copies of the outside Fairview sheet in the
working tree, not one, and both leave.

## 0. What I verified and what I did not

No shell in this spawn: I could read, grep, glob and open images. I ran no
test, no gate and no git command. Every count in the brief (2978 changed lines
in tools/, 510 renames, 4354 CoreTests, selftest 90/0, the content-gate done
line, the census validator's 2594 checks) is the lane's own number, and
section 11 makes the resident print the ones a decision here rests on.

Read at the lines this ruling rests on, this session:

- `canon.md` 30 to 39 and 63 to 107.
- `ledger-v2/respec/decision-register/D18-content-rule.md`, whole file, 57 lines.
- `ledger-v2/respec/decision-register/D17-no-alcohol-no-gambling.md` lines
  10, 22, 28 to 41, and `D3-comedy-register.md:3`, by grep.
- `tools/gates.py` line 40 and 208 to 215, 1062 to 1067, 1215 to 1220,
  1548 to 1553; `tools/dashboard/build-dashboard.py` 108 to 121.
- `tools/glance.py` 56 to 64 and 1664 to 1677; `tools/gallery.py` 134 to 157.
- `tools/content-gate.py` lines 51, 88 to 89, 123 to 126, 262, 392 to 394,
  408 to 410, 554 to 556, 813 to 818, 946 to 979, 1112 to 1118, 1384 to
  1397, and the baseline grep hits at 1140 to 1674.
- `tools/imagegen/sheet-furniture.py` 36 to 75.
- `tools/systems-inventory-check.py:111`; `production/systems-inventory.json`
  1430 to 1489.
- `production/ladder.md` 146 to 157; `.claude/agents/world-designer.md` 28 to 37.
- `production/queue/242`, `243`, `244`, the first 40 to 50 lines of each.
- `production/art/mickeys-cars/05-D17-town-pass.md` 134 to 147, and
  `cab-office.json:775`, `cab-ground-plan.svg:207` by grep.
- `production/art/concept-fairview-2026-09-10/DELIVERY.md` lines 15 to 21
  and 147, by grep.
- `tools/docs-check.py` 125 to 147, for the banner this file must carry.

Opened, per rule 4: `game-design/sim-shots/fairview_theirs_vs_ours.jpg`,
`production/art/concept-fairview-2026-09-10/sheets/fairview_theirs_vs_ours_finished.jpg`,
`production/art/concept-fairview-2026-09-10/sheets/fairview_sheet_finished.png`,
`game-design/sim-shots/district_fairview.jpg`. What each shows is in section 2.

Not verified by me: the C# lines cited for question 6, the `git cat-file`
sizes in queue/244, the canon-gate fix, and every test and selftest count.
Section 11 prints them.

## 1. canon.md edited by a builder: the D18 section STANDS, the CCTV line is REDUCED to what Jafar has said, the second camera is his question

Two edits, two verdicts.

THE D18 SECTION STANDS. It is not a verbatim transcription and does not claim
to be; it is a composite, and every clause traces to a record Jafar approved:
the eleven rule lines to `D18-content-rule.md` lines 9 to 23, in his order;
"PUBS MAY EXIST AS PLACES" to `D17-no-alcohol-no-gambling.md:10`, in
capitals there too; "what the pub is for without drink is a design task" to
D17:34; "seaside-postcard innuendo under Tone" to canon's own Tone line 43
and `D3-comedy-register.md:3`; "the building is there and nobody is in it"
paraphrases D18 lines 43 to 44, "the building stands, the children do not".
The five enforcement sites match D18 lines 25 to 33. Nothing in the section is
the builder's own world fact.

THE CCTV LINE DOES NOT STAND AS WRITTEN. The builder was right that the old
line is inconsistent with canon's own rule: D18 says alcohol is never shown or
spoken of, and an off-licence named as a place in canon is alcohol spoken of.
A subtraction forced by Jafar's own rule is a builder's to apply. An addition
is not. "The ferry terminal has a camera" is a new world fact with gameplay
weight (CCTV is a witness type and its tapes are stealable objects,
`ledger-v2/research/gta6-triage.md:34`), and canon is approved by Jafar, not
proposed to him inline. Provisional language ("struck on sight if Jafar
prefers") does not belong in a facts document either.

Dictated: replace canon.md lines 34 to 38, from "CCTV rare" through the
closing parenthesis, so the paragraph reads

    fixers, cash and paper. CCTV rare: the bank, and a second site that is
    Jafar's to name (the off-licence was struck 2026-09-10 under D18 and
    nothing was minted in its place), tape recycled weekly. One camcorder in
    town, a rare witness type. No internet, no mobiles in ordinary pockets.

The question goes to Jafar through the Producer in this run (section 12),
with the builder's proposal as the suggested answer. When he answers, the
resident replaces the parenthetical with his site, his words and the date, as
a one-line edit under this ruling. The commit does not wait on him: the
reduced line is true today.

The sentence, not the site (rule 1). Copies of "the bank and the off-licence"
found by grep this session: `.claude/agents/world-designer.md:34`, a live
brief, corrected below; `ledger-v2/handoff/canon-task.md:13`,
`ledger-v2/research/gta6-triage.md:34` and
`game-design/decision-2026-09-08-the-lookup-that-lied-and-the-art-line-in-house.md`
lines 249 and 482, dated records, left as they are and named here so nobody
rediscovers them. Dictated for the brief, lines 33 to 34: replace "CCTV rare,
the bank and the off-licence, as canon says." with "CCTV rare, at the sites
canon names and no others." A brief that repeats canon's sites drifts the day
canon changes; a brief that points at canon does not.

## 2. D18 reaches the retired sheet, Jafar already said so, and there are TWO copies

VERDICT: D18 reaches it, by Jafar's own record. `D18-content-rule.md` lines
39 to 44 name "the outside Fairview sheet" with "two children on the steps and
a FAIRVIEW SCHOOL sign" as the immediate cost of the rule and say none of it
"survives D18 unchanged". Whether a retired comparison is inside the rule was
answered when the rule was dictated. "Retired from production" describes the
account; the pixels are in the working tree, which is the work.

WHAT I OPENED. Glob for `**/*fairview*` returns two comparison sheets, and
the gate's own `--enforceable` text (`tools/content-gate.py:1393`) names the
second one, not the first:

1. `game-design/sim-shots/fairview_theirs_vs_ours.jpg`. Left half "THEIRS,
   Fairview": FAIRVIEW SCHOOL nameplate in both views, two small figures in
   dark uniform at the gate in the upper view, an adult with a child carrying
   a satchel in the lower view, swatch strip captioned SCHOOL SATCHEL. Right
   half "OURS": two adults in each view, no nameplate, swatches uncaptioned.
   Matches the resident's reading in queue/242 exactly.
2. `production/art/concept-fairview-2026-09-10/sheets/fairview_theirs_vs_ours_finished.jpg`.
   Same outside sheet on the left: same children, same nameplates, same
   SCHOOL SATCHEL swatch. Right half "OURS, drawn in house, furniture
   composited from the atlas": two adults, no nameplate, and this half DOES
   carry captions: SCHOOL BROW, SCHOOL STEPS, and a swatch captioned SCHOOL
   SATCHEL.
3. `production/art/concept-fairview-2026-09-10/sheets/fairview_sheet_finished.png`,
   our standalone finished sheet: identical to the right half of item 2.
4. `game-design/sim-shots/district_fairview.jpg`: a sim blockout render, no
   figures at all. Out of scope.

So queue/242's "our own sheet is already compliant" is true of the sim-shots
copy and not of the finished one. The captions on our finished half are
`sheet-furniture.py` output, and its object list is the atlas's
(`DELIVERY.md:147`: "school satchel" from `atlas.json districts id=fairview
objects`). That is queue/244's shape, already rendered once: a string from the
branch the gate cannot scan, printed onto a sheet. The satchel token is
baselined at six sites (`content-gate.py` 1112 to 1118) and D18 lines 41 to
42 name the school satchel as not surviving unchanged, so the caption is a
KNOWN hit whose fix is the furniture data under queue/243 followed by a
re-composite once 244 lands. Bare "school" in a place name passes by the
gate's own rule (`content-gate.py` 392 to 394) and by D18: the building
stands. The crop below does not fix the caption and is not meant to.

THE DENOMINATOR OBJECTION, MEASURED. The archive lane's finding as cited does
not reach these files. `tools/gates.py:40` defines
`RUNS = ROOT / "game-design" / "sim-shots" / "runs"`, and each of the four
cited lines (212, 1065, 1218, 1551) reads `RUNS`, the `runs/` subdirectory;
`build-dashboard.py:116` says in its own comment that its 358 files are "every
kept run in game-design/sim-shots/runs/". Neither reads the top level. Two
tools DO: `tools/glance.py:62` (block 4, the frame it shows) and
`tools/gallery.py:151` (rglob, counted 37 under sim-shots on 2026-09-10,
printed beside its denominator). A move would shift the gallery's printed
count by one, visibly, and break the path queue/242 cites. So: not moved, and
the finding stands corrected in scope, which matters because the next reader
would otherwise treat the whole directory as untouchable.

DICTATED: crop both comparisons to their right half, in place, same path,
re-encoded once. For each path P of items 1 and 2, in this order:

1. `git rev-parse HEAD:P`, and paste the blob id into queue/242 under a line
   reading "original, with the outside half, is blob <id> in history". Rule
   5: the outside account's work is preserved where the pipeline cannot reach
   it. Git history is not the work; the working tree is.
2. `python3 -c "import sys; from PIL import Image; p=sys.argv[1]; im=Image.open(p); w,h=im.size; im.crop((w//2,0,w,h)).save(p,quality=92); print('cropped',p,'before=%dx%d'%(w,h),'after=%dx%d'%(w-w//2,h))" P`
   PIL is already a project dependency (`glance.py:1674`).
3. OPEN THE RESULT. Confirm the header reads OURS, two adult figures per
   view, no FAIRVIEW SCHOOL nameplate, no figure of child height. If the
   split is not at the midline the crop shows it at once; measure the panel
   edge and redo with that x rather than guessing.

Both printed lines go in the commit message. The gallery count is unchanged
by construction (same paths, same file count). The glance page may pick the
newer file for block 4; that is the compliant half, which is fine.

## 3. The dartboard: UPHELD

Darts is a game, not a wager, and the rule text agrees at four places read
this session: D17:41 says pub games "are not added as systems", which bans the
system and not the object; `content-gate.py` lines 88 to 89 and 554 to 556
encode "PUB GAMES ARE NOT GAMBLING" with a darts line as an ACCEPTING fixture;
the commission's own D17 pass (`05-D17-town-pass.md` 139 to 142) already
reasoned it for the cab office, "a game and not a wager", and applied the
same reading to the snooker table; `cab-office.json:775` and
`cab-ground-plan.svg:207` carry it as object 31. A drivers' room in 1990 had a
dartboard. Condition, which the gate's `betting` token already enforces:
nothing is ever played for money on it, in any line.

## 4. The 197-hit baseline is an INSTRUMENT, on four conditions that keep it one

A baseline is an exemption when it can grow and nobody reads it; it is an
instrument when it can only shrink and every run prints it. This one, read at
`content-gate.py` 948 to 979:

- keyed `file|rule|sha1(text)[:12]`, so a one-character edit is new writing
  (selftest lines 1594 to 1596 test the key both ways) and a fixed line whose
  entry remains fails with its own exit code (queue/243: exit 4);
- lives INSIDE `tools/content-gate.py`, a cadence prefix, so growing it is
  builder work in tools/ that `director_cadence` blocks without a ruling. The
  mechanical protection exists already; nobody built it for this, but it is
  there;
- printed on every run as `hitsBaselined=197`, a last-wins count at HEAD, not
  a peak;
- its own comment says "NOT TO BE GROWN" and that `--baseline-write` is a
  separate invocation typed on purpose.

Conditions:

1. The starting series is recorded here: 197 hits, 121 distinct texts,
   stamped 2026-09-10; by channel speech 157/99, prompt 36/12, spec 28/22,
   veto 1/1, brand 0/0 (queue/243's table).
2. Every commit that touches the baseline prints `hitsBaselined` before and
   after in its message, and after is strictly lower. A commit where it is
   not lower is refused by the resident; a ruling is the only way past.
3. `--baseline-write` is not run before queue/243 closes, except under a
   ruling that says why. Its "wrote N" line is pasted whenever it runs.
4. Queue/243 is done when `BASELINE = ()` and the done line reads
   `hitsBaselined=0` beside its `stringsScanned`.

Condition 2 is a manual ratchet. The mechanical one (verify.py comparing the
count against the last committed value) is one compare and belongs in the
wiring item of section 7, after the batch lands, per Jafar's "no studio
building until it lands".

## 5. The atlas hole: NOT a blocker on this commit, a HARD GATE on the next art dispatch, and the conclusion is corrected here

The gate is honest at the line and wrong in the prose. The done line prints
`declaredAbsent=2` and both entries print `stringsExamined=0`, which is
"nothing measured" said correctly (`content-gate.py` 813 to 818 even records
that D18 cites the atlas). What was wrong is the sentence built on it, that
the project is clean. The only conclusion this ruling permits, in the commit
message or anywhere:

    content-gate clean over THIS BRANCH'S WORKING TREE: hitsNew=0 over
    stringsScanned=9780 in filesOpened=32. origin/art/atlas-01, which
    tools/imagegen/sheet-furniture.py:49 reads on purpose, is unscanned; a
    grep of the blob found one hit (DISTRICTS.md:10 "bookmaker"); the
    87-rule scan has not run over it: nothing measured. Queue/244.

Why not a blocker: the fix is a gate change (read the blob when the tree copy
is absent, and decide what verify.py does on a checkout with no remote ref)
plus a content edit on another branch. Neither is a one-line fix, and holding
the D18 enforcement commit for it leaves the working tree unprotected longer.

Why a hard gate on art: section 2 shows the leak already happened once. Atlas
strings reach rendered sheets through the compositor. Until 244 lands, no
`sheet-furniture.py` run and no imagegen dispatch that reads `ATLAS_BLOB`.
Gates, not pauses: the resident writes that sentence into queue/244 and into
`production/NOW.md` if an art item is moving.

## 6. The four PARTIAL tiles: typed correctly, and Jafar is owed one sentence

VERDICT: the departure was correct. The status field is a measurement or it
is nothing; `tools/systems-inventory-check.py:111` gives it three values,
`exists`, `partial`, `absent`, and `absent` beside `Core/Harm.cs` declaring
`Injury` would be a false statement with a director's `typedBy` on it. The
four entries (`systems-inventory.json` 1430 to 1489) read `partial`,
`where: core-csharp`, `typedBy: director/resident`, `typedOn: 2026-09-10`,
and the validator accepted them.

What Jafar meant is also true, and the record says both. He typed them ABSENT
because he has never perceived any of them, and rule 6 is on his side: nothing
in the brief names a gate proving any of the four call sites fired in a run.
Nothing measured. So the next rung for all four is a run gate or a demo clip,
and until one exists "partial" means "code and a call site, unproven in play".

Owed: one Producer sentence (section 12), not an apology. Condition: the four
call sites are printed by grep in the commit message, since I did not read
them: `Core/Harm.cs` for `InjuryKind`, `Game/OperationHost.cs:131`
`LastInjury`, `Core/Gossip.cs` 706 and 738 with `Game/DialogueUI.cs:2214`,
`Game/Audio.cs:830` with `Game/DialogueUI.cs:1546`, `Game/RoomTone.cs` with
`Core.Acoustics.OutsideBleed`.

## 7. The five unwired tools: wired in the next batch under its own ruling; the false sentence does not wait that long, and it exists TWICE

Grep this session for `goal-block-check`: readers are docs, queue items and
the tool's own selftest line; no `.py`, `.sh` or `.yml` calls it. The brief is
right. The sentence "proves the goal block still matches" is false as a
description of what runs, and it stands in TWO live places: `CLAUDE.md:227`
and `production/ladder.md` lines 152 to 153, and the second is a LIVE plan in
this batch, which makes it new writing today.

- `production/ladder.md` 152 to 153, dictated: replace "and
  `tools/goal-block-check.py` proves the copy in `CLAUDE.md` still matches
  that source." with "and `tools/goal-block-check.py`, run by hand (nothing
  calls it yet; see the wiring item), checks that the copy in `CLAUDE.md`
  matches that source."
- `CLAUDE.md:227` waits exactly one commit: the fold (section 8) rewrites the
  file under `decision-2026-09-10-ruling-the-one-rules-file.md`, which already
  requires the checker green at its line 436. The fold builder gets this
  sentence for the spot: "`tools/goal-block-check.py`, run by hand before any
  commit touching either file, checks that the goal block matches its
  source." Two edits to CLAUDE.md in two commits is churn on the file every
  session reads.
- Interim: the resident runs `python3 tools/goal-block-check.py` now and
  pastes its output into this commit's message. The sentence is then true of
  this commit by hand, which is what the fix admits it always was.

Wiring all five (`goal-block-check.py`, `brand-verify.py`,
`dialogue-verify.py`, `blocking-count.py`, `brief-sheet.py`) plus the baseline
compare of section 4 is ONE queue item, filed now, called THE WIRING ITEM in
this record, run after the batch and the fold land, under its own ruling
because it edits `ledger/verify.py`. Not before: Jafar's words.

## 8. The fold ruling: UPHELD; the fold lands in the NEXT commit

Upheld in full: 2979 words is today's start-read cost, measured against what
the loader put in a spawn's prompt (CLAUDE.md, `.claude/rules/ci.md`,
`.claude/rules/instruments.md`; not the constitution). This spawn received the
same three, and `instruments.md` still opens "Loaded when editing measurement
code" while I edited nothing. 2979 is the acceptance ceiling for the fold
commit and the standing cap stays UNSET until the deduplicated draft's count
prints.

The fold is not in this batch: `.claude/` churn is 7 lines over 2 files, and
a fold of two rules files into one cannot be 7 lines. It lands in the commit
after this one, carrying section 7's sentence.

## 9. TWO commits, in this order

1. THE BATCH: everything under the cadence prefixes (tools/, content/,
   ledger/, .claude/), canon.md, the 510 archive renames and `legacy/`, the
   store collapse, the census, the queue files, the dictated edits of
   sections 1, 2 and 7, and this ruling. One commit, because this stamp names
   one row and the gate compares it against the last code commit; two code
   commits would leave the second without a ruling newer than the first. The
   renames ride with it and prove themselves in the message:
   `git diff --cached -M --diff-filter=R --name-status | wc -l` printed
   (expected 510) and the same with `--diff-filter=D` printed (expected 0).
2. THE COMMISSION: `production/art/mickeys-cars/`, art and documents, on the
   resident's read, citing section 3 for the dartboard. Second, so nothing
   lands between this stamp and the code commit it covers.

## 10. Quality ladder at close: first working, named, with the rung above it

FIRST WORKING: D18 in images is enforced at the prompt and nowhere after it.
`validate_spec` reads the words sent to the model; nothing reads what came
back. The gate says so itself (`content-gate.py` 1392 to 1396: "No word gate
can see that. Somebody opens the file."), and section 2 is the proof in this
very batch: the brief and queue/242 knew of one rendered copy and there were
two, found by a glob and a look, not by any instrument.

Next rung, manual, filed now: THE IMAGE PASS. Open every image file under the
gallery's SOURCES (`gallery.py:151`: `production/d1-probe`,
`production/frames`, `game-design/sim-shots`, `production/art`), record per
file children / drink / gambling / slur text as yes or no, print
`imagesExamined=N` fresh (gallery's 72 of 2026-09-10 has already decayed by
its own comment), and the compare boards under `production/art/compare/` are
in scope because they embed outside sheets.

Rung after that is blank, so a RESEARCH TASK, filed now: is there a vision
model on `ledger-v2/research/license-allowlist.md` that can read a sheet for
the D18 classes? If yes, name it with its weights licence in a decision
record; if no, record that the rung is manual until one exists.

Smaller first-working aspects, each with its rung: the word list is token
level (a bet-shaped sentence with no token passes; next rung is a phrase list
with a planted miss-rate printed, under 243); the four PARTIAL tiles have no
run gate (section 6); the baseline is 197 (section 4); the gate reads one
branch (section 5).

## 11. Conditions on the batch commit, all printed into the message from the terminal

1. `python3 ledger/verify.py` green; footer pasted FROM `ledger/.verify-footer`.
2. The content-gate done line verbatim, followed by the scope sentence of
   section 5.
3. `python3 tools/canon-gate.py` output. The brief reports the 11 false brand
   findings were caught; it does not print the number after the fix, and no
   conclusion rests on a number nobody printed.
4. `python3 tools/goal-block-check.py` output (section 7).
5. The two `cropped ... before= after=` lines (section 2) and the two blob
   ids recorded in queue/242.
6. The rename and deletion counts (section 9).
7. The four call-site greps (section 6).
8. After the dictated edits: the `python3 tools/docs-check.py` line
   (ladder.md and this file are in its set), and canon.md lines 33 to 37 and
   world-designer.md lines 32 to 34 re-read and pasted.
9. The message written to a file, never an unquoted heredoc.
10. Added with section 14: the content-gate done line AFTER the commission's
    reword, `hitsNew=0 hitsBaselined=197 staleBaseline=0` with its
    `stringsScanned`, pasted beside the line from item 2.

## 12. To Jafar, through the Producer, this run

One message, judgment not status, with the link to this record:

1. QUESTION, answered in this run: canon named the off-licence as the town's
   second CCTV site; D18 struck it. Which is the second site? The builder
   proposes the ferry terminal. Until he answers, canon says "a second site
   that is Jafar's to name".
2. Four of the systems he asked to be typed ABSENT have code and a call site
   (injury and healing, bribes and intimidation, foley, ambient beds) and are
   typed PARTIAL with the file and line beside each. None has a gate proving
   it fires in play, so from his chair ABSENT is still what it feels like;
   the next rung per tile is a run gate.
3. What the gate caught: 197 lines in 121 distinct texts on this branch, all
   listed and dated, 0 new writing; one known hit on the art branch it cannot
   yet reach, a bookmaker on Copper Row.
4. The two Fairview comparison sheets are cropped to our half; the outside
   half with the children is in history only.

## 13. Queue items the resident files with this commit

- THE WIRING ITEM (section 7): five tools into `ledger/verify.py`, plus the
  baseline compare of section 4. After the fold. Own ruling.
- THE IMAGE PASS (section 10): manual, with `imagesExamined=N`.
- THE VISION-MODEL RESEARCH TASK (section 10): allowlist first.
- Amend queue/242: the second file, both blob ids, and the SCHOOL SATCHEL
  caption on our finished half as a 243 dependency with a re-composite after
  244.
- Amend queue/244: the hard gate on art dispatch (section 5).

## 14. Added on the coordinator's request: the 14 new hits in the commission's delivery are REWORDED, not baselined and not exempted

The request. After sections 1 to 13 were applied, `python3
tools/content-gate.py --report` exits 1 with `hitsNew=14 hitsBaselined=197
staleBaseline=0 stringsScanned=10056 filesOpened=33`, all 14 in
`production/art/mickeys-cars/DELIVERY.md` lines 156 to 159, a D17 town-pass
table whose rows name the removed objects inside backticks (`beer firkin`,
`bookmaker`, `paper betting slip`, `drink trade`, `wine-bar refits`). Four
options were put to me. Section 4 condition 3 makes this mine.

VERDICT: OPTION 3, REWORD, and it is a deduplication rather than a rerouting.
The table is a removal record, and the same objects already sit by name in
the decision-class file beside the delivery. The delivery restates them; the
restatement goes and a pointer replaces it. Nothing is baselined, nothing is
exempted, and the tool changes by two comment lines. The commission does the
edit, since the delivery is theirs and it is more than one line.

What I read for this, this session: `tools/content-gate.py` 790 to 828 (the
corpus table, `DECLARED_ABSENT`, `EXEMPT`); `DELIVERY.md` 148 to 163;
`05-D17-town-pass.md` lines 79, 93 and 98 by grep, which name `beer firkin`,
"barber and bookmaker" and the bookmaker's design job in full, in the file
that is NOT corpus; the 19 atlas-02 baseline entries at `content-gate.py`
1091 to 1109; `production/art/atlas-02/DELIVERY.md` lines 74 to 158 by grep.

WHY NOT THE BASELINE (option 1). The baseline is defined at
`content-gate.py` 952 to 957 as the hits that already existed when the gate
first ran, and it says of every one of them that they fail D18. These rows do
not fail D18: its scope is image and speech, and a record of what was removed
is neither. Baselining them would record a falsehood (that they are violations
awaiting rewrite) and grow a list section 4 says only shrinks. Wrong category
and wrong direction, and a ruling that grants it would be the first hand-added
entry, which the baseline's own comment names as the shape with no teeth.

THE PRECEDENT DOES NOT CUT THAT WAY, read rather than remembered. The atlas-02
hits at lines 74, 79, 87, 96, 124 to 125, 140, 144 and 154 to 158 of its
delivery are a design description of a pub with beer in it: a firkin's full
weight, the ONS beer price series, a pavement beer drop, brewery tenancy and
a guest cask under the 1989 Beer Orders. That is pre-D17 design text which
D17 voided, the exact thing the baseline exists for, and queue/243 rewrites
it. The coordinator's "exactly this shape" is refuted by reading: those lines
describe the world as it was designed; these four rows describe what was taken
out of it.

WHY NOT AN EXEMPTION (option 2). The corpus comment at 797 to 800 is right: a
delivery describes what is on the sheet, and text a player reads on a picture.
Exempting the file un-scans 262 strings that can describe visible art;
exempting the class un-scans every delivery to come. The reason section 4
would require me to write beside the exemption is "this delivery cannot
describe visible art", and that is false.

WHY NOT A MARKED REGION (option 4). Barred for this batch by Jafar, and the
wrong shape regardless: a fence any writer can open is a per-line exemption
machine. If a per-region mechanism is ever wanted it goes through the wiring
item under a ruling. Not filed now, because option 3 costs nothing that needs
it.

WHY OPTION 3 IS NOT ROUTING AROUND THE GATE. The gate cannot tell a
description from a removal record; it is a word list over files, and its own
authors accepted that granularity when their clause "nothing served or drunk"
fired on `drunk` in every prompt and they reworded the clause rather than
exempt it. That is the precedent, and it is theirs: when the instrument is
coarse, the writing adapts. This project already keeps its removal records in
decision-class files (`EXEMPT` names "the decisions that made it"), and the
commission's own `05-D17-town-pass.md` is that file, already carrying these
objects by name. The delivery is not losing a record; it is losing a
duplicate, which rule 1 wants gone anyway. The residual hole, a writer putting
a description of visible art in a non-corpus file, exists today for every
non-corpus file and is not widened by this.

THE STANDING RULE, from today: A CORPUS FILE DESCRIBES WHAT IS THERE. What
was removed is named in the decision-class record beside it, which the corpus
file cites by path. A corpus file never names a removed object, not even in
backticks, not even to say it is gone.

Dictated for the commission, `DELIVERY.md` lines 154 to 162: keep the table,
keep the headline above it (three of seven touched under D17, four under D17
plus D18, three untouched), keep the verdict words (TOUCHED, VENUE CLEAN,
CLEAN), keep the replacements by name (a stencilled fish box, a launderette),
drop every removed object's name and every quoted sheet-row phrase, and add
one sentence under the table: "The removed objects and the sheet-row phrases
are named in `05-D17-town-pass.md`, which is the removal record; a delivery
describes what is on the sheet and does not name what came off it (ruling
2026-09-10 section 14)." Apply it to rows 156 to 160, not only the four that
fired: row 160 names `school satchel`, the same shape, and the table should
not fail the day a rule is widened.

Dictated for the tool, two comment lines after `content-gate.py:799`, under
this ruling as a cadence-prefix edit, no code:

    # A delivery names what is ON the sheet. What came OFF it is named in the
    # D17/D18 pass file beside it, which is not corpus. Ruling 2026-09-10 s14.

Then `python3 tools/content-gate.py --report` again, and its done line goes
in the batch commit message as section 11 item 10. If a hit remains in the
delivery and it is the same shape, it gets the same treatment; if it is not
the same shape, it is a description of the art and the commission fixes the
art, not the words.

Order unchanged from section 9: the commission rewords in the working tree,
verify goes green, the batch commits, the commission commits.
