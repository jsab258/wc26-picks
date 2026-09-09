# Ruling: the typed systems inventory ships labelled as the studio's reading, seven tiles retyped by the director, two fields added, three retired-contract documents named

> **STATUS: LOG, 2026-09-09. NOT CURRENT.** Director ruling at spawn
> 2026-09-09T12:52:41Z on the v2 systems inventory (69 entries), its rewritten
> validator, and the three documents still carrying the retired evidence
> contract. NOT CURRENT once the dictated edits in section 7 are applied and
> the batch is committed; from then the files are the reading copies.
> SUPERSEDES IN PART:
> `game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md`
> section 5 and the roadmap text it dictated.

VERDICT: APPROVED WITH DICTATED EDITS AND ONE OVERTURN. The v2 schema, the
typed contract and the 69 entries are accepted. Eleven of the twelve
typed-down states are upheld, seven of them against measurements I took this
spawn. ONE NOTE IS REFUTED AND REWRITTEN: the frame budget's claim that
`Core/FrameRate.cs` has no caller in the Game layer is false. Seven entries
are retyped `director/studio-director`; the other 62 ship as the builder's
reading and THE PAGE SAYS SO ON THE FIRST SCREEN. Two fields are ruled in,
`short` and `where`, with `where` required on every tile that is not absent.
`blockerStale` stays a printed series and does not go red.

## 0. What I could not run, what I read, what I counted

NO SHELL IN THIS SPAWN. I could not execute `tools/systems-inventory-check.py`,
its selftest, or `ledger/verify.py`. Every number in the brief's live series
(`entries=69`, `byStatus`, `byPhase`, `typedBy`, `evidence`, `blockerStale`) is
THE BUILDER'S, printed in another session, and this ruling does not convert any
of them into a measurement. Section 9 makes the resident print them again into
the commit message, with two of them named as conditions on this approval. A
conclusion that rests only on a number nobody printed at the commit is not
covered by this ruling.

Read in full: `production/systems-inventory.json` (all 69 entries, the
`howToRead`, the `areas` block, the `ruling` and the header),
`tools/systems-inventory-check.py`,
`production/queue/098-the-player-facing-systems-inventory-as-data.md`,
`ledger-v2/respec/roadmap-v2.md`,
`game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md`.
Read in part, at every line this ruling rests on: `tools/docs-check.py` lines
120 to 169, `tools/queue-check.py` lines 77 to 153, `ledger/verify.py` lines
3013 to 3031 and 3193 to 3245, `tools/dashboard/build-dashboard.py` lines 311
to 322, `ledger/Assets/Scripts/Game/DialogueUI.cs` around 1347 and 1573,
`ledger/Assets/Scripts/Game/WorldBuilder.cs` 1937 to 1964,
`ledger/Assets/Scripts/Core/MemoryStore.cs` 62 to 96,
`ue-probe/Source/LedgerProbe/Public/Suspicion.h` 14 to 18,
`ledger/ReachCheck/allow.json` 78 to 87,
`production/d1-probe/ue-vignette-verdict.txt` 85, 109 to 112, 131,
`production/pc-ops/inbox-flush.txt` 1 to 28.

Counted by grep or by reading the file, this spawn (the denominator is named
in every case):

- `Arrested` under `ledger/`: 3 occurrences, 0 callers. `Game/CoatHost.cs:159`
  is the definition, `Core/Homicide.cs:61` a comment recording the absence,
  `CoreTests/Program.cs:4788` a second comment. Under
  `ledger/Assets/Scripts` alone it is still 2, which is why the roadmap's
  existing sentence about 2 occurrences is STILL TRUE as scoped and must not
  be "corrected" by a future session reading my 3.
- `liveSilent=1944/1944` and `lieHeard=0/90` and `realPointed=540/3240`: read
  on line 1 of `production/stranger-test/study.txt`, one line, one run,
  `atUtc=20260906-142553`.
- `MemoryStore.cs:62` `MaxEvents = 600`, `:63` `PruneTo = 500`.
- `conversation`, `latency`, `convo`, case insensitive, in
  `game-design/sim-shots/verdict.txt`: 0 matches across 214 lines.
- `FrameRate` in `ledger/Assets/Scripts/Game`: 2 hits, and one of them is a
  LIVE CALL. See section 3, finding 8.
- `MotionMatch` in `ledger/Assets/Scripts`: 2 hits, both inside
  `Core/MotionMatch.cs`. Second source, `ledger/ReachCheck/allow.json:85`:
  "Nothing in the Game layer references MotionMatcher or MotionDatabase at
  all, checked rather than assumed."
- `SuspicionTracker` in `ue-probe/`: 9 hits, every one of them a comment
  saying it is NOT ported, including `Suspicion.h:14` and the probe's own
  printed key at `Private/CrimeProbe.cpp:1038`,
  `gossipSuspicionPorted=no/SuspicionTracker-out-of-scope`.
- `Arrest` in `ue-probe/`: 0 hits across 0 files.
- `Recognition` in `ue-probe/`: 3 hits, `Public/StreetVoice.h:26` naming it a
  ported member and `Public/Perception.h:48` plus `Private/Perception.cpp:55`
  using `RecognitionFamiliarity`.
- `ConversationEngine`, `class Claims`: 0 hits in `ue-probe/`.
- `ue-probe/Source/LedgerProbe/Public/*.h`: 17 headers, and `FrameStats.h`,
  `LedgerCharacter.h` and `Suspicion.h` are among them.
- `production/d1-probe/ue-vignette-verdict.txt`, 161 lines: NO key names a
  character, a walker or a person. The only `crowd` is the prop
  `prop_crowd_control_barrier_0`; the only `pawn` is the substring inside
  `quadStatus=SPAWNED`. Line 109 reads
  `surfacesAbsent=card/interior/multiply/paint_yellow`.
- `parse_roadmap` at `build-dashboard.py:321` appends `cells[0:3]` only, so a
  fourth column is invisible to it, and `roadmap-v2` appears in exactly one
  tool, `tools/dashboard/build-dashboard.py`. Editing the systems column
  cannot break a reader.
- `STATUS_RE` in `queue-check.py:80` is `^status:\s*(\S+)`, multiline, first
  match wins. `order_names` in the inventory checker parses `N. name` lines
  under a heading beginning `## The names`, and `EXPECTED_NAMES = 27`.
- `queue/037` reads `status: READY 2026-09-02`, so the Ledger notebook's
  blocker is live and not stale.
- `8aaf780d` names a real commit in this tree
  (`production/d1-probe/ue-material-log.txt:1`). `884f049c` carries
  `flushCheckoutPcHeadCommitIso=2026-09-09T10:54:40Z`, which is how I know my
  spawn row at 12:52:41Z is newer than the reference commit.
- `.claude/agent-log.tsv`: 458 rows, the last one mine, and the only
  `studio-director` row after 10:54:40Z.

PREMISE CHECK, CLAUDE.md section 0. The inventory is about a British port town
in the 1988 to 1992 window; nothing in the 69 entries dates the world
elsewhere, the phone entry names the late-analog spine explicitly, GTA V is
not cited, no purchase is proposed, no licence entry changes. The moat is
first in area order and carries 13 of the 69 tiles, which is the premise's own
ordering. No conflict.

## 1. Question 1: the page ships labelled, seven tiles retyped by me, 62 as the builder's reading

RULED: SHIP LABELLED. `typedBy=builder/tier3` is honest and stays on 62
entries. Seven entries are retyped `director/studio-director` because I
measured them myself this spawn, and one line on the FIRST SCREEN carries the
split, computed from the data and not written as prose.

Why not retype all 69 as mine. I took seven measurements. Typing 69 states
`director/studio-director` on seven measurements would attest 62 judgements I
did not make, and attribution is the ONLY guard the new contract has: the
evidence gate was removed on 9 September precisely because the state is now
somebody's judgement with a date on it. A director's name on 69 tiles he did
not check is the anonymous colour the ruling replaced, with a better name on
it. Refused, on rule 1.

Why not ship 69 unlabelled as the builder's. Jafar's words are "a human's
judgement of state, ruled by me and updated by rulings". A page that shows 69
typed tiles with no statement of whose reading they are reads as the studio's
settled view, and he has not ruled one of them. A page that says these are the
studio's reading pending his ruling invites the ruling he said he would give;
a page that is silent about it borrows his authority. Refused.

What the page must do with it, and this is the minimum, not a design:

- ONE LINE on the first screen, after the ladder and before or immediately
  under the heatmap, at most one line at 360px. Its counts are COMPUTED from
  `typedBy`, never typed into the page: the shape is "Typed by the studio,
  <oldest>..<newest>. <N> of 69 typed by a director, <M> by a builder, 0 of 69
  ruled by you. Your ruling replaces any tile." The zero ships its
  denominator, per rule 3b, because "none ruled by you" and "nobody has
  looked" are different facts and the first invites a tap.
- Per-tile attribution (`typedBy`, `typedOn`) sits in the audit view one tap
  down. Sixty-nine badges on the first screen is the measured-evidence noise
  his ruling pushed below the fold.

THE SEVEN I RETYPE, each with the measurement that justifies MY name on it.
All seven take `"typedBy": "director/studio-director"` and
`"typedOn": "2026-09-09"`, and six of them take the `where` value named in
section 4. The exact edits are section 7, D1.

1. `the law and the police` (partial). `Arrested` has 3 occurrences under
   `ledger/` and 0 callers: a definition and two comments. Arrest is
   unreachable in play and the consequence spine has no terminal state.
2. `recognition and confrontation` (partial). `liveSilent=1944/1944` on line 1
   of `study.txt`. Nobody speaks to the player in the measured build.
3. `interiors you can enter` (absent, not partial). `WorldBuilder.cs:1950`
   builds `{tag}_interior` as a backdrop box and `:1952` to `:1953` DESTROYS
   its collider; the comment at `:1946` says "The proper recessed room is the
   ladder's next rung, not this one". A player cannot stand in it because
   nothing stops them walking through it. Second source: the Unreal verdict
   line 109 lists `interior` among `surfacesAbsent`. Absent is the right word
   and `partial` would have been the flattering one.
4. `permanent memory` (partial). `MaxEvents = 600`, `PruneTo = 500`. The
   pillar word is permanent and the store drops the oldest 100 at 601.
5. `spoken conversation` (partial). 0 of 214 lines in the committed sim
   verdict name conversation or latency, so phase 2's own budget is not
   measured by the instrument that gates it.
6. `the player's claims and lies` (partial). `lieHeard=0/90`: of 90 caught
   lies, 0 changed a spoken line. THE OTHER HALF OF THAT NOTE, the 0.060
   suspicion curve, is in `study-curve.txt` and I did not open it; it remains
   the builder's reading inside an entry I now own, and the note says nothing
   I have not read.
7. `the frame budget` (partial). Retyped because I CHANGED it: its note
   carried a false claim, see section 3 finding 8, and whoever rewrites a note
   owns the tile.

Cost of this choice, named: the resident applies seven two-line JSON edits and
one note as dictated text, roughly five minutes, no builder pass. The cost the
other way is an unfalsifiable page.

## 2. Question 2: the standard for typing down, in one sentence

RULED, and this sentence is the one a future session applies without
re-deriving it:

**A TILE IS GREEN ONLY IF THE THING ITS NAME PROMISES CAN HAPPEN TO A PLAYER
IN A BUILD THAT EXISTS TODAY; WORKING, CALL-SITED, GATE-GREEN CODE WHOSE
PROMISED EVENT NEVER REACHES A PLAYER IS AMBER; AND A PROMISE NOTHING IN THIS
CHECKOUT CAN DELIVER IS RED, WHATEVER THE GATES SAY.**

It is the right standard for THIS page for one reason that is not a matter of
taste: this page is the one artefact in the project that is read at a glance by
the person who decides what gets built next. A resolving call site is an
instrument reading for a builder; "can it happen to somebody" is the only
question a director's overview answers. The standard also inherits the rule
already written into the data's own `howToRead`, TYPE THE LOWER STATE WHEN
UNSURE, so there is one idea here and not two.

The standard's own cost, stated so nobody discovers it as a surprise: an
amber tile is no longer a promise that the work is nearly done. `exists` and
`partial` have stopped being a floor under a phase gate. Section 5's roadmap
edit says so in the roadmap itself.

## 3. Question 2 continued: the spot-checks, including the one I overturn

Eight findings. Seven uphold the builder; the eighth refutes a sentence.

1. `the law and the police`: UPHELD, measurement in section 1 item 1.
2. `recognition and confrontation`: UPHELD, `liveSilent=1944/1944`.
3. `interiors you can enter`: UPHELD as ABSENT, and this was the one most
   likely to be wrong in the lenient direction. The access gate is green, the
   doors and keys and doormen work, and the builder still typed red because
   the thing the NAME promises, a room you enter, has no collider anywhere in
   the tree. Correct call.
4. `permanent memory`: UPHELD, 600 and 500 read in the file.
5. `spoken conversation`: UPHELD, 0 of 214 verdict lines.
6. `the player's claims and lies`: UPHELD on the half I read, `lieHeard=0/90`.
7. `suspicion and heat`: UPHELD AND UNUSUALLY PRECISE. There IS a
   `ue-probe/.../Suspicion.h`, so a careless reader would call the note wrong.
   `Fact`, `KnowledgeBase` and `ClaimResult` are ported and `SuspicionTracker`
   is not, which the header says at line 14 and the probe PRINTS at
   `CrimeProbe.cpp:1038`. The note's phrase "the one type deliberately left
   out of the Unreal port" is exact.
8. OVERTURNED, `the frame budget`. Its note ends "Core/FrameRate.cs has no
   caller in the Game layer walked here". THAT IS FALSE.
   `Game/DialogueUI.cs:1350` declares `FrameRate _frames;` and
   `Game/DialogueUI.cs:1354` calls `_frames.Tick(Time.unscaledDeltaTime)`
   inside `Update()`, with a comment at `:1347` saying it is ticked every frame
   whether the panel is open or not; `:1573` and `:1574` call `_frames.Line()`
   and read `_frames.Hitching` for the F1 panel. Corroboration that this is not
   an unreached API: `FrameRate` has 0 hits in `ledger/ReachCheck/allow.json`,
   which is the list of APIs allowed to have no caller.
   THE STATUS STANDS AT `partial` on its other half, which I did not refute:
   no budget for the Unreal street at a resident count is set in this
   checkout, and that is phase 1's gate. Only the reason changes, and the note
   is rewritten in section 7, D2.

RULE 1's SENTENCE SWEEP, because a false claim's copies sit wherever a later
reader was writing. `no caller in the Game layer` plus `has no caller` plus
`no callers`, whole repo: 20 hits. Three are in this inventory. Two of those
three are TRUE as written (`MotionMatch`, checked twice; `Arrested`, checked).
One is the false one above. The remaining hits are casebooks, agent briefs,
the reach-check allow list and code comments, and ONE of them is a claim of
the same shape about a different system that I did not check:
`ledger/Assets/Scripts/Game/LawHost.cs:18`, "no callers in the Game layer
either". That is adjacent work, not this change: it goes to the queue by name
in section 10.

## 4. Question 4: both fields are ruled IN, with their exact shape

### 4a. `short`: YES, optional, and for ten entries the value is Jafar's own words

`"short"`: an optional single-line string, the display label a tile uses when
the name does not fit. Validator rungs: a string, single line, non-empty, no
leading or trailing space, STRICTLY SHORTER than `name`, and UNIQUE across the
file (two tiles reading the same label is worse than one tile reading long).
Not required anywhere, and NO LENGTH THRESHOLD IS SET IN THE INSTRUMENT,
because no rendered width has been measured at 360px in any session. What I
measured instead is the distribution of the 69 `name` lengths as read from the
file: 48, 40, 34, 34, 30, 30, then 29 and down. Six names are 30 characters or
more and the seventh is 29, so the six the brief names are the six, and the
gap is in the data rather than in my head. The pixel measurement is the next
rung, named in section 10.

The ten values, dictated. Where Jafar's sentence of 9 September supplies a
label, HIS WORDS ARE THE VALUE and the studio invents nothing:

    the what-they-know HUD for wanted states      -> what-they-know HUD
    phone boxes and answering machines            -> phone boxes
    witnesses and what they caught                -> witnesses
    concept art and the town atlas                -> concept art
    graphics settings including the local-LLM toggle -> graphics settings
    failure states and autosave policy            -> failure states
    first hour and tutorial                       -> first hour
    loading and streaming                         -> loading
    time and calendar display                     -> time display
    credits and attributions                      -> credits

The last six of those are his 9 September words. The page shows `short` when
it is present and the FULL NAME WRAPPED, never clipped, when it is not: a
silently truncated label is the unreadable-output fault of rule 12 on the one
screen he reads.

### 4b. `where`: YES, required on every tile that is not absent

`"where"`: one of `core-csharp | ue-probe | both | repo`, REQUIRED when
`status` is `exists` or `partial` (62 entries today), FORBIDDEN when `status`
is `absent` (7 today). The asymmetry mirrors the one the validator already
enforces for `evidence` and it is the same logic: a system that is nowhere
cannot be somewhere, and a tile that names an engine for a thing that does not
exist is a claim with a location on it.

WHAT THE WORD MEANS, and this definition is load-bearing because the wrong one
makes the field flatter rather than inform. `where` is WHICH CODEBASE THIS
TILE'S COLOUR IS ABOUT.

- `core-csharp`: the colour is a reading of the C# game under `ledger/`, and
  nothing on the Unreal side has been measured for this statement.
- `ue-probe`: the colour is a reading of the Unreal probe only.
- `both`: the same statement has something MEASURED behind it on each side, a
  golden parity row or a printed key, not merely a ported header.
- `repo`: the colour is about files and process and neither engine.

A PORTED HEADER WITH NO MEASUREMENT BEHIND IT IS `core-csharp`, NOT `both`,
and the note says how far the port got. That is the same lower-state-when-
unsure rule the data already carries, and it is what stops the field becoming
the second flattering thing on the page: `both` must be earned by a
measurement, and `CoreGolden.h` is where the builder looks for one.

Required on the first screen, because Q4 is right that this is the field that
decides whether the page is honest: the tile carries the engine as a short
corner mark and the heatmap's computed line carries the split (how many green
tiles are `core-csharp` only). Three colours stay three colours; this is a
mark and a count, not a fourth colour. The page computes both numbers from the
data. I am naming no count here, because no tool has printed one.

THE SIX `where` VALUES FOR MY OWN SEVEN TILES, dictated so the builder does not
retype what I typed. `interiors you can enter` is absent and takes none.

    the law and the police          core-csharp   (Arrest: 0 hits in ue-probe)
    recognition and confrontation   core-csharp   (the silence was measured in the Unity sweep; Recognition is named ported in StreetVoice.h and nothing measures it there)
    permanent memory                core-csharp   (600 and 500 were read in the C#; whether the ported header carries the same cap is not measured)
    spoken conversation             core-csharp   (ConversationEngine: 0 hits in ue-probe)
    the player's claims and lies    core-csharp   (no Claims type in ue-probe; the reading is study.txt)
    the frame budget                core-csharp   (the 0.24 ms is Unity's; FrameStats.h exists and no Unreal street budget does, which is the colour)

Why this cannot wait for a follow-up item: 26 green tiles that are green in a
codebase Jafar is not looking at, with D1 still the only open decision, is
exactly the page that flatters. The field and its validator rung go in THIS
batch, in the builder pass of section 8, not behind a queue number.

## 5. Question 3: the three retired-contract documents, by name

### 5a. `production/queue/098-the-player-facing-systems-inventory-as-data.md`: AMENDED BY ADDITION, nothing deleted

This file is NOT only history: `order_names()` parses its `## The names`
section every time `ledger/verify.py` runs, and `EXPECTED_NAMES = 27` makes
the validator print CANNOT RUN and exit 3 if the heading or the count changes.
So it cannot be retired, moved or rewritten wholesale.

Nothing in it is deleted, for a reason: the `status:` line's own claim (27
entries, 61 evidence references resolving) is the true record of what landed on
5 September, and striking the acceptance it was measured against would leave a
dated claim with nothing behind it. Two passages are marked RETIRED in place by
the insertions in section 7, D4:

- THE CLAUSE THAT DIES AS A REQUIREMENT, in the `acceptance:` line: "an entry
  whose status is exists or partial and whose evidence path does not resolve in
  this checkout is REFUSED". It stays on the page as the record of the old
  acceptance and is marked as retired above it.
- THE SECTION THAT DIES AS A REQUIREMENT: "## A seventh field, added here with
  its reason", whose sentence "`evidence`, REQUIRED when status is exists or
  partial" is the retired contract in its clearest form. Its own last
  paragraph says "a director may cut it"; this ruling is that cut.
- WHAT SURVIVES AND IS RESTATED, because it was never wrong: "What may not
  happen is a status word that nobody can check." Under the typed contract the
  check is attribution, not a path.
- UNTOUCHABLE: the `## The names` heading, the 27 numbered lines, and the first
  word of the `status:` line.

### 5b. `game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md`: LEFT STANDING, with a forward pointer

LEFT STANDING, not amended. It declares `STATUS: LOG, 2026-09-05. NOT CURRENT.`
in its own first lines, and a log is true of one dated day by construction.
Rewriting a dated ruling's text is worse than dating it: the formatting law
says older text is corrected opportunistically and never rewritten wholesale,
and this project keeps its incidents intact on purpose.

Two things make the forward pointer necessary rather than optional. First, the
file contains a SECOND copy of the retired sentence, inside the roadmap block
dictated at section 9 D1, so a pointer at section 5 alone would miss it; the
pointer therefore goes in the STATUS block at the top, where a reader of either
copy will have passed it. Second, section 5's three limits are STILL TRUE and
still the best short statement of why a path is not a gate (a token in a
comment satisfies the check; a false `absent` cannot be refuted; the
denominator is external). Those three survive this ruling and are worth
reading. Exact insertions: section 7, D5.

### 5c. `ledger-v2/respec/roadmap-v2.md`: AMENDED, four edits, and the new census named

AMENDED. The column is a hand census dated 2026-09-05 against a file that now
holds 69 entries, so it is stale data with a date on it, which is the one
failure mode a dated census is supposed to prevent. Nothing downstream can
break: `parse_roadmap` appends `cells[0:3]` and the fourth column is invisible
to the only tool that reads this file.

THE NEW PHASE CENSUS, from the builder's printed `byPhase` line and carried
into the column as phase totals only:

    R=0  0=7  1=12  2=23  3=13  4=2  5=2  6=10     sum 69 of 69

THE PER-PHASE STATUS BREAKDOWN DIES AND IS NOT REPLACED. The old cells read
"3 of 27: 2 exists, 1 partial". No tool in any session has printed a status-by-
phase cross-tab, so writing "12 of 69: 5 exists, 6 partial, 1 absent" would be
a number nobody measured, assembled by hand from two independent tallies. The
cells carry the phase total and nothing else until the validator prints the
cross-tab, which is section 10's first queue item.

Row law, checked before the edit rather than after: every fourth cell LOSES
words (seven words to three in the worst case) or stays the same length (phase
R), so no row can cross the 80-word cap, and the worst row at 70 of 80 can
only fall. TWO CELLS CURRENTLY CARRY IDENTICAL TEXT, phase 0 and phase 5 both
read "1 of 27: 1 partial", so the resident replaces BY ROW and never by a
global find and replace. Exact edits: section 7, D6.

## 6. Question 5: `blockerStale` stays a printed series and does NOT refuse

RULED: PRINTED SERIES, no bound, no red. Two refusals that already exist stay
red and are the right ones: a blocker naming NO queue file, and a blocker
naming NO decision record. Those are broken references. A blocker naming a
LANDED item or a SETTLED decision is a reference to a world that moved on, and
it does not refuse.

The evidence I am ruling from, and what each piece can and cannot support:

- The series as printed by the builder, not by me: `queueLanded=0/18
  decisionSettled=0/33`. Both zeros ship denominators, so today's file is
  clean and the clean is distinguishable from nothing measured.
- The detector works. The brief reports two blockers in the first draft
  pointing at finished work, caught by this series, and every `D12` blocker
  stale because D12 was decided on 2 September. I corroborated the live end of
  that myself: `map and minimap` now reads `blocker: none` with a note naming
  D12's decision date, and `queue/037` reads `READY 2026-09-02`, so the
  Ledger notebook's blocker is genuinely live. The instrument is doing its
  job as a series.
- WHY RED WOULD BE WRONG, and this is the decisive one. `queue_is_landed`
  reads `production/queue/*` and `decision_is_open` reads the decision
  register. A refusal therefore fires from files the commit did not touch:
  landing queue 160 would turn `ledger/verify.py` red for the next commit to
  touch anything at all, and the ONLY way to clear that red is to edit a
  TYPED STATE under commit pressure. Jafar ruled on 9 September that a state
  changes by a ruling. A gate that forces a state change to make red go away
  is rule 2's prohibition pointed at the data instead of the threshold, and
  it would make this page lie on exactly the days the studio is busiest.
- The asymmetry is already the project's: `absent` may not cite evidence, but
  a false `absent` cannot be refused. A false `exists` costs a phase its gate;
  a stale blocker costs a builder a look at the wrong queue item. The cheaper
  fault gets the cheaper instrument.

WHAT CHANGES, because a series nobody reads is the same as no series. Three
requirements, none of them a bound: the two counts appear in the audit view one
tap down with their denominators; they appear in the morning brief so a stale
blocker is seen by a human daily; and a director's close-out reads them, with a
non-zero count cleared by a retype inside a ruling, which is the only mechanism
allowed to change a typed state. The rung after that is a bound set FROM the
series once real runs have produced a maximum worth bounding, in that order,
never the reverse.

## 7. Dictated edits, applied by the resident before the commit

D1. `production/systems-inventory.json`, seven entries. In each, replace
`"typedBy": "builder/tier3",` with `"typedBy": "director/studio-director",`
and leave `"typedOn": "2026-09-09",` as it stands (the date is today and is
correct for my typing too). The seven, by `name`: `the law and the police`,
`recognition and confrontation`, `interiors you can enter`, `permanent
memory`, `spoken conversation`, `the player's claims and lies`, `the frame
budget`. No other entry's attribution changes.

D2. Same file, the same entry `the frame budget`: replace its whole `note`
value with this single line, verbatim.

    Typed down for one reason: no budget for the Unreal street at a resident count is set in this checkout, which is phase 1's gate. The Unity sim's 0.24 ms against its own 4.00 ms over 24702 samples is carried from the builder's read of the last landed run. CORRECTED 2026-09-09 by the director: Core/FrameRate.cs IS called from the Game layer every frame, at Game/DialogueUI.cs:1354 inside Update, and Line() and Hitching feed the F1 panel.

D3. Same file, the header: replace the value of `"typedAgainst"` with
`"this checkout at commit <short sha of HEAD at the commit>"`, reading the sha
at commit time rather than copying `8aaf780d`. `8aaf780d` is a real commit in
this tree but I cannot prove from here that it is the one this file was typed
against, and a provenance field that names the wrong commit is the evidence
channel's own failure mode. If the sha differs from `8aaf780d`, say so in the
commit message in one clause.

D4. `production/queue/098-the-player-facing-systems-inventory-as-data.md`, two
insertions, nothing deleted. Neither inserted line may begin with the word
`status:`, because `queue-check.py` takes the first such line in the file.

Insert directly AFTER the `status:` line:

    contract-retired: 2026-09-09. The `acceptance:` line above and the section "A seventh field, added here with its reason" below describe the RETIRED contract. Jafar ruled on 2026-09-09 that a typed state is the standard on the map page and that evidence is provenance, never the licence for a status word; the guard that replaced it is attribution, typedBy and typedOn on every entry. Both passages stay as the record of what was accepted on 5 September and neither is a live requirement. The live contract is game-design/decision-2026-09-09-ruling-typed-systems-inventory.md and the docstring of tools/systems-inventory-check.py. STILL LIVE IN THIS FILE: the "## The names" heading and its 27 numbered lines, parsed by that tool as the coverage denominator (order_names, EXPECTED_NAMES=27); change the heading or the count and the validator prints CANNOT RUN and exits 3.

Insert directly under the heading `## A seventh field, added here with its reason`:

    RETIRED 2026-09-09, kept as the record. The requirement below, evidence REQUIRED when status is exists or partial, was cut by Jafar's ruling of 2026-09-09 and by game-design/decision-2026-09-09-ruling-typed-systems-inventory.md. This section's own last paragraph reserved that cut for a director, and this is it. What survives unchanged is its warning: a status word nobody can check is still the fault this project repeats, and 37 props and 14 decals were once counted as progress while the grep returned 0.

D5. `game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md`,
two insertions, nothing reworded. Insert at the end of the STATUS block at the
top, as a continuation of the block quote:

    > SUPERSEDED IN PART 2026-09-09: section 5's evidence contract, and the roadmap text dictated in section 9 D1, were retired by game-design/decision-2026-09-09-ruling-typed-systems-inventory.md. Section 5's three limits are still true and still worth reading.

Insert as the first line of the body of section 5, under its heading:

    SUPERSEDED 2026-09-09 by game-design/decision-2026-09-09-ruling-typed-systems-inventory.md, question 3: evidence no longer licenses a status word. The three limits below still hold, and the first of them is why.

D6. `ledger-v2/respec/roadmap-v2.md`, four edits, BY ROW and never by a global
replace (two cells share their text).

1. The header row's fourth cell becomes
   `Systems carried (production/systems-inventory.json, typed census read 2026-09-09)`.
2. The eight fourth cells become, in row order: `0 of 69, by design`,
   `7 of 69`, `12 of 69`, `23 of 69`, `13 of 69`, `2 of 69`, `2 of 69`,
   `10 of 69`. Phase 0 and phase 5 both read `1 of 27: 1 partial` today and
   take DIFFERENT new values, 7 and 2.
3. Replace the first paragraph of `## The systems column: what it counts, and
   what it does not` (the paragraph beginning "A whole-file census" and ending
   "the queued row-law checker's job.") with:

    A whole-file census of `production/systems-inventory.json`, grouped by its `phase` field, copied by hand from the validator's printed `byPhase` line on 2026-09-09 and carried here as phase totals only. The eight cells sum to 69 of 69, so every system names a row and every row can say what it carries. Phase R carries 0 by design: it is the respec and holds no system. The per-phase status breakdown these cells used to carry is GONE and is not replaced by hand: no tool prints a status-by-phase cross-tab, and a breakdown assembled from two separate tallies is a number nobody measured. The cross-tab, and a checker that compares this column to the file, are the queued row-law item.

4. Replace the paragraph beginning `IT IS NOT A GATE READING.` (through "never
   a gate reading for it.") with:

    IT IS NOT A GATE READING, AND SINCE 2026-09-09 IT IS NOT EVEN A PATH. Jafar ruled on 2026-09-09 that status on that page is a TYPED JUDGEMENT, attributable to a person and a date and changed by a ruling rather than by a grep; `exists` no longer means that a path resolves. The standard the typing follows: a tile is green only if the thing its name promises can happen to a player in a build that exists today. So a count of `exists` is a reading of somebody's judgement, never a gate reading, and never a floor a gate may stand on. Phase 2 now carries 23 entries, among them the what-they-know HUD its own milestone clause names, typed absent. Ruling: game-design/decision-2026-09-09-ruling-typed-systems-inventory.md.

5. Append, after the `## The fold of 2026-09-05` section, a new section:

    ## The typed contract of 2026-09-09

    Ruling: `game-design/decision-2026-09-09-ruling-typed-systems-inventory.md`. The inventory moved from 27 entries to 69 and from an evidenced status to a typed one; the systems column above was re-read from the new census on 2026-09-09. The fold section above is the record of 5 September and its arithmetic was true of the 27-entry file, so it is not re-counted here. Its sentence about `Arrested` having 2 occurrences is still true as scoped: 2 under `ledger/Assets/Scripts`, 3 under `ledger/`, 0 callers in both readings.

## 8. The builder pass, one session, the instrument builder already on this file

Ordered AFTER D1 to D3 are applied, so the attribution is in the tree before
the fields land:

- `short` and `where` added to `production/systems-inventory.json` per section
  4, with the ten `short` values and the six `where` values dictated there.
  THE BUILDER MUST NOT CHANGE `typedBy`, `typedOn` or `note` on the seven
  entries named in D1.
- `where` values for the remaining entries, typed by the builder under its own
  `typedBy`, using the definition in 4b: a ported header with no measurement
  behind it is `core-csharp`, `both` is earned by a printed key or a golden
  parity row, studio and content entries about files and process are `repo`.
- `tools/systems-inventory-check.py`: `where` joins the existing fixed-set
  loop (`for field, allowed in (...)`) so there is ONE implementation of the
  idea; required-when-not-absent and forbidden-when-absent are two rungs;
  `short` gets the four shape rungs of 4a. ACCEPTING FIRST, with the live file
  as the accepting fixture, then the planted refusals: `where="unity"`, an
  `exists` entry with no `where`, an `absent` entry carrying `where`, a
  `short` longer than its name, two entries sharing a `short`.
- The page: the computed attribution line of section 1, the engine mark and
  the computed split of section 4b, the full name wrapped when `short` is
  absent.

NOT IN THIS PASS, and a builder may not add it on the way past: the
status-by-phase cross-tab (section 10), and anything in `game-design/` or
`ledger-v2/` other than what this record dictates.

## 9. What the commit must print, and the two conditions on this approval

Every line pasted into the commit message verbatim, from the run and not from
this record. I ran nothing, so nothing here is a measurement.

1. `python3 tools/systems-inventory-check.py`: the `entries=` line, the
   `byStatus:` line, the `byPhase:` line, the `typedBy:` line and the
   `blockerStale:` line.
2. `python3 tools/systems-inventory-check.py --selftest`: the final
   `selftest: passed=N/M rungs` line, with the accepting count.
3. `python3 tools/docs-check.py` summary line, after this file exists.
4. `python3 tools/queue-check.py` done line, after D4.
5. `python3 ledger/verify.py`, footer pasted FROM `ledger/.verify-footer`.

CONDITION ONE. `byPhase` must read
`R=0/69 0=7/69 1=12/69 2=23/69 3=13/69 4=2/69 5=2/69 6=10/69` or the roadmap
column dictated in D6 is wrong and THIS APPROVAL DOES NOT APPLY to that edit.
Print what it says, not what is expected.

CONDITION TWO. `typedBy` must show `director.7` and `builder.62` summing to
69 with `untyped=0/69`, or D1 was applied to the wrong number of entries. If
it differs, say by how much and stop rather than adjusting the data to match
this record.

## 10. The quality ladder at close, and the queue items this ruling files

Best available or first working, per aspect, with the next rung named. None is
blank.

- The inventory: at "a typed page whose every tile is attributable". Next
  rung: tiles ruled by Jafar, `typedBy` role `jafar` above 0. That is a tap,
  not a build, and section 1's computed line is what asks for it.
- The validator: at "shape, vocabulary and attribution checked, 29 rungs".
  Next rung: the status-by-phase cross-tab printed, which is what lets the
  roadmap column stop being a hand copy.
- The roadmap column: at "copied by hand from a printed series, dated". Next
  rung: the row-law checker comparing the column to the tool's own census
  (queue 107).
- `blockerStale`: at "printed with denominators". Next rung: read daily, in
  the brief and in the audit view. The rung after that is a bound set from the
  series.
- `short`: at "a label chosen from Jafar's own words for the six that do not
  fit". Next rung: the rendered width measured at 360px, so the trigger is a
  pixel count and not a gap in a character-length distribution.

Queue items this ruling files, numbers the resident's to assign, none started
now:

- A. The status-by-phase cross-tab in `tools/systems-inventory-check.py`, one
  printed line with its denominators, plus the row-law comparison against the
  roadmap's fourth column. Blocks nothing; unblocks the column.
- B. Audit the comment claims of the shape "has no caller", starting with
  `ledger/Assets/Scripts/Game/LawHost.cs:18`. One of three such claims in the
  inventory was false this spawn, and the same sentence shape sits in code
  comments where nothing re-checks it. Rule 1's own failure mode.
- C. `typedAgainst` written by the tool from HEAD rather than typed by hand, so
  the provenance field cannot name a commit the file was not typed against.
- D. The rendered-width measurement behind `short`, per the ladder above.

<!--RULING spawn=2026-09-09T12:52:41Z paths=production/systems-inventory.json,tools/systems-inventory-check.py,tools/map.py,production/queue/098-the-player-facing-systems-inventory-as-data.md,game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md,ledger-v2/respec/roadmap-v2.md,game-design/decision-2026-09-09-ruling-typed-systems-inventory.md-->
