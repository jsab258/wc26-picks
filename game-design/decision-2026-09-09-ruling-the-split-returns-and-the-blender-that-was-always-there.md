# Ruling: the split returns to the first screen, and the Blender that was always there

> **STATUS: LOG, 2026-09-09. NOT CURRENT.** Director ruling at spawn
> 2026-09-09T15:14:21Z on a two-piece batch, both pieces CARRYING OUT rulings
> already made today rather than opening questions: the engine split back above
> the fold in his words with its fourth case printed, and the art lane's
> Blender discovery, git assignment and staging list. NOT CURRENT once the
> conditions in section 6 are met and the batch is committed.
> BUILDS ON: `game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md`
> (14:24Z), whose section 2b piece A carries out, and whose section 1 standard
> section 5 extends. CORRECTS that record's section 2c, section 3 below.

VERDICT: A APPROVED, with one defect in the new guard named and queued rather
than blocking. B APPROVED IN FULL, with two of its three sub-questions ruled
against the builder's framing and one sweep accepted as a reading and REFUSED
as protection. MY OWN SECTION 2c OF THE 14:24 RECORD OVERCLAIMED, section 3.

## 0. What I could not run

NO BASH IN THIS SPAWN. I executed nothing: not `ledger/verify.py`, not
`tools/map.py`, not its selftest, not the art workflow, not a single grep from
a shell. Every number below was printed by a builder in another session, and
this ruling converts none of them into a measurement. Section 6 turns the
load-bearing ones into conditions on the approval, which is the device the
12:52 and 14:24 rulings used for the same reason and the device section 3 says
should have been used for one more number than it was.

What I read instead, in this session: `tools/map.py` at 2155 to 2202, 2441 to
2603, 4132 to 4159, 5091 to 5102 and 5130 to 5240;
`.github/workflows/ledger-art-blender-preview.yml` at 232 to 256 and 372 to
480; `game-design/decision-2026-09-09-ruling-the-sun-the-bootstrap-and-the-board.md`
in full; `.claude/agent-log.tsv` at 400 to 466; `tools/docs-check.py` at 130 to
147; `tools/ps-check.py` at 1 to 18; the allowlist's own first line.

PREMISE CHECK, CLAUDE.md section 0. Nothing here dates the world outside 1988
to 1992, nothing cites GTA V, nothing proposes a purchase, no account is used.
No tool enters: the allowlist's first line scopes it to weights and not to code
licences, and Blender's presence on that machine is a fact this repository
recorded on 2026-09-01, not an admission this ruling makes. No conflict.

## 1. Piece A: approved

APPROVED. The fact is back above the tiles, computed rather than typed, in
words that name no engine, and the fourth case is printed.

Three things I checked rather than took, and all three hold:

1. THE GUARD'S ANCHOR IS THE WORDING ITSELF. `GREEN_SPLIT_RX` and the plain
   sentence both derive from `HEAT_SPLIT_PLAIN` at 2185, so a reworded phrase
   moves the sentence and its reader together and only the NUMBER is compared
   against the tally. That is the correct split of what may move with the prose
   and what may not.
2. THE REGISTER GUARD IS INDEPENDENT OF IT, and it has to be, because a guard
   anchored on the wording cannot notice the wording turning back into studio
   vocabulary. Eight watched words over 36 rendered, and both guards stay.
3. ABOVE THE FOLD IS TESTED AS A POSITION IN THE BYTES, at 5206 to 5208, not as
   a pixel line. My own 14:24 ruling accepted the board as the second
   screenful, so a pixel test would have been the wrong instrument. First tile
   at 890 to 954 px is consistent with it and is not what the guard reads.

### 1a. The wording is not the shape I dictated, and the change is a correction

I dictated "19 of them are read in one build only". The page reads "19 are read
in the older build only". ACCEPTED, AND THE BUILDER IS RIGHT: my phrase was
ambiguous in a way I did not see when I wrote it, because 19 core-csharp and 0
ue-probe are BOTH "one build only", so the dictated sentence quietly assigned
the 19 to whichever build the reader already had in mind. "Older" and "newer"
name no engine, no language and no repository, and neither says which build is
better, so every constraint in section 2b holds. The precise words were the
builder's under that ruling; this one was better than mine.

### 1b. The defect I found in the new guard, named and queued

`above_tiles` at 5208 falls back to "the sentence exists anywhere on the board"
when `HEAT_FIRST_TILE` is not found, and still prints
`greenSplitAboveTheFirstTile=yes`. A marker string that stops matching after a
future restyle therefore silently turns the position check into a presence
check, while the printed key reads exactly as it does today. That is a
fail-open on a guard I inverted eight hours ago, which is the class the 14:24
ruling spent its first section on.

NOT BLOCKING. The batch improves on a page that had the fact off the screen
entirely, and the art render is ahead of it tonight. But it gets a name and a
rung, queue item E in section 7: the key distinguishes three states, above,
below and no-first-tile-marker, and the rejecting rung plants a board whose
marker is absent. A guard that cannot tell "correct" from "I could not look" is
rule 3b with markup around it.

## 2. Piece A's zero: accepted, and it is the finding

`heatGreenWhere=both.4/core-csharp.19/repo.3` printed three of four cases,
sorted, and the missing member was the whole point of the exercise. The
replacement at 2457 to 2479 prints all four in a fixed order with the
population phrase required as an argument, appends anything outside the fixed
set rather than dropping it, and the board accepts a zero only as "none of the
N". The docstring's own sentence is the right one: A ZERO NOBODY PRINTS IS A
ZERO NOBODY READS.

## 3. RULED: MY SECTION 2c OVERCLAIMED. Plainly, and here is the exact shape

YES. Section 2c of the 14:24 record said of the Unreal probe's green count
that "it is zero out of 26 with its denominator printed" and that "a zero with
a denominator is the cheapest protection this project has and it is now
available for this question". NO RUN IN THIS REPOSITORY HAD EVER EMITTED THAT
ZERO. The tally iterated the keys it happened to hold, so the number existed
only as an absence, and the sentence describing an instrument reading as
available described a reading nothing had produced.

The fact survives and the conclusion stands: the run now prints `ue-probe.0`
and the three consequences in 2c bind unchanged. THAT IS NOT A DEFENCE. Two
separate faults sit under a conclusion that happened to be true:

1. THE NUMBER WAS A SUBTRACTION PRESENTED AS A MEASUREMENT. 26 minus 19 minus
   4 minus 3 is 0 only if those four cases partition the greens, and NOTHING
   PRINTED OR CHECKED THAT CLOSURE. A green tile carrying a fifth value, or
   whitespace in a value, would have satisfied the arithmetic and falsified the
   claim, which is why the replacement key appends out-of-set members instead
   of dropping them. Two numbers derived from one variable are one number
   twice, and a residual is the purest form of it.
2. THE BODY OUTRAN ITS OWN CONDITION. Section 5 condition 4 of that record DID
   put the split under a condition on the next run, which is the device that
   works. Section 2c then quoted the value in prose as though the condition had
   already returned. A reader of the body alone, which is every future session
   in a hurry, met a printed measurement that did not exist.

THE STANDING RULE, and this is the sentence a future session applies without
re-deriving it:

**A RULING MAY NOT QUOTE A NUMBER NO RUN HAS PRINTED. If a ruling needs a
number that has not been emitted, it ORDERS THE EMIT and states the value only
as a condition on the approval, in the conditional voice, never as a finding in
the body; and a number obtained by subtracting printed numbers from a printed
total is NOT a printed number, because it inherits an unchecked assumption that
the printed members exhaust the set.**

Filed as a miss against the 14:24 record and against no person. The instrument
that caught it is the builder reading the emit rather than the ruling, which is
the tier working as designed.

## 4. What one tile of 69 means for the board's green

The new whole-file census, printed by the builder and conditioned in section 6:
`heatTilesByWhere=core-csharp.45/both.6/ue-probe.1/repo.10` over all 69.
EXACTLY ONE TILE NAMES THE NEWER BUILD AT ALL, and it is typed partial, not
green.

This is stronger than 2c's finding and it changes what "0 of 26" means. Read
alone, `ue-probe.0` over 26 green tiles sounds like 26 things were examined on
the newer build and none came back green. It is not that. THE DENOMINATOR FOR
THE NEWER BUILD IS 1 OF 69 ROWS OF ANY COLOUR. The zero is a statement about
COVERAGE, not about quality, and the two read identically on the page.

RULED, extending 2c's second consequence from green to the whole board and
binding from today:

- NO DOCUMENT, GATE OR REPORT MAY CITE ANY COUNT FROM THIS BOARD AS EVIDENCE
  ABOUT THE UNREAL SIDE, green or otherwise. Any claim about that side names
  its own denominator of rows measured there, which is 1 of 69 today.
- THE BOARD IS NOT A READINESS INSTRUMENT FOR THE BUILD THAT WILL BE PLAYED AND
  CANNOT BECOME ONE BY CHANGING COLOURS. It becomes one only when rows are
  measured on that side, one parity row at a time, which is the ladder rung 2c
  already named.
- The whole-file census belongs where the marks are decoded, one tap down, and
  not on the face: the face carries one fact and it is his sentence. Queue item
  F, not this change, because it is adjacent and not asked.

## 5. Piece B: approved, with the lesson stated against the builder's framing

APPROVED, all three faults. B1's five-root search prints per root whether it
exists and what its children are called, orders by version from the parent
directory name and asks the winner for its own version, and `artBlenderPickedBy`
already says how it chose. B2's array fix is the whole fix and the measurement
is in the comment beside it rather than in a session nobody can find. B3 is the
one nobody asked for and the most expensive one avoided: `git add` is atomic
over its pathspecs, so five rendered frames plus one absent verdict staged
nothing at exit 128, and the list is now built from what is on disk with
`artCommitInputs` printing both halves separately.

### 5a. The dispatch versus the grep: BOTH are true, and they are not in tension

The resident's self-recorded fault is RIGHT and the round trip was ALSO
justified. Stating it as one or the other loses the actual lesson.

`production/mesh-reports/blender-setup.txt` was committed on 2026-09-01 by this
project's own setup workflow, running on that machine, naming the host, the
path, the version and `onPath=no`, verified by running the binary. Three
hardcoded candidates were written instead, all of them guesses about a machine
that had already reported its own answer. THE GREP WAS FREE AND WOULD HAVE
ANSWERED B1 EXACTLY. That is the fault, and it is the same shape as ci.md's
standing rule: THE ENTRY POINT IS CHEAPER THAN THE ARGUMENT, extended one step
to the evidence the entry point already committed.

But the grep could not have found B2 or B3, because both are faults in steps
that had never executed, and no amount of reading finds a fault in code that
has never run against a real directory. So the dispatch was not wasted: it was
SPENT ON THE WRONG QUESTION and paid for two others. The correct account, which
is what a future session needs:

**BEFORE A DISPATCH ASKS THE MACHINE A QUESTION ABOUT ITSELF, GREP WHAT THE
MACHINE HAS ALREADY COMMITTED ABOUT ITSELF; SPEND THE ROUND TRIP ONLY ON
QUESTIONS THAT REQUIRE EXECUTION.** And, as a direct extension of the 14:24
standard on derived populations: A STEP THAT LOOKS FOR A TOOL DERIVES ITS
CANDIDATES FROM WHAT THE PROJECT'S OWN SETUP INSTALLS, NEVER FROM A LIST OF
PLACES SOMEBODY EXPECTED IT TO BE.

### 5b. Two routes to one instruction: KEPT, and now it has to prove itself

The inline `-c safe.directory` beside the `env:` triple stays. The standing
rule that one idea gets one implementation is about DIVERGENCE, and its target
is two pieces of LOGIC that can disagree about a decision. This is one
constant value delivered on two inert transports, and queue 152 asked for the
belt and braces after dubious ownership killed the mesh import silently.
Removing half of a redundancy a ruling asked for is a bigger change than
quoting it, and the builder was right to refuse it inside a fix for something
else.

THE CONDITION THAT STOPS IT BECOMING SUPERSTITION, because two routes neither
of which has been proven necessary is exactly how a cargo cult starts: the next
art dispatch PRINTS WHICH ROUTE IS IN FORCE, one key, from git's own view of
its configuration rather than from the workflow's belief about it. When one
route is shown sufficient on that machine, the other goes in a change that
names this record. Queue item G.

### 5c. The sweep is accepted as a reading and REFUSED as protection

31 files walked, 18 workflows and 13 shell scripts, 4 setting nullglob, 1
carrying the shape with 7 sites, now 0, with 4 remaining detector hits in 2
files verified by running them. The denominators are right, the false positives
were disposed of by execution rather than by argument, and the builder's report
that its FIRST detector read 0 while the known fault sat in the tree, then
fixed the predicate and proved it on a planted fixture before trusting the
zero, is rule 3 done in the correct order and is the best single act in this
batch.

BUT THE DETECTOR DID NOT LAND. I searched `tools/` for the predicate's
distinguishing tokens and found it in no checker. So "0 of 31" is a reading
taken once by a script that no longer exists, and the tree can regrow this
fault tomorrow with nothing to notice. A SWEEP WHOSE DETECTOR DOES NOT LAND IS
A READING, NOT A GUARD, AND MAY NOT BE REPORTED AS ONE.

Not blocking, for the same reason as 1b: the art render is ahead of it tonight.
Queue item H, and it lands in `tools/ps-check.py`, which already parses every
workflow and exists for precisely this failure family, with the planted fixture
as the rejecting rung and today's fixed workflow as the accepting one.

### 5d. What a lane that has never completed once may claim

The sentence, applicable without re-deriving it:

**A LANE THAT HAS NEVER COMPLETED ONCE MAY CLAIM ONLY THAT ITS STEPS ARE
WRITTEN, NEVER THAT THEY WORK, BECAUSE EVERY STEP BEHIND THE FIRST FAILURE IS
UNEXECUTED CODE WHOSE FAULTS ARE HIDDEN IN ORDER; ITS ONLY HONEST STATUS IS HOW
MANY OF ITS STEPS HAVE EVER RUN, OUT OF HOW MANY IT HAS.**

Three dispatches, three faults, each invisible until the one before it was
fixed, is not bad luck: it is the arithmetic of an unrun pipeline, and it
predicts a fourth. Nobody should be surprised by one, and nobody should say the
lane works until a run has produced a committed frame.

## 6. The conditions on this approval

Every line pasted into the commit message VERBATIM from the run, never from
this record. I ran nothing, so nothing above is a measurement.

1. `python3 tools/map.py --selftest`: the passed count over its checks.
   CONDITION: 151 over 38, accepting case first. Fewer checks than 38 with a
   green result means rungs were removed, and this approval does not apply.
2. `python3 tools/map.py` on a real run: the `heatGreenTilesByWhere` and
   `heatTilesByWhere` keys in full, plus the `typedAttribution` line.
   CONDITION: the green tally reads `core-csharp.19/both.4/ue-probe.0/repo.3`
   summing to 26 with its population phrase attached, and
   `greenSplitOnTheBoard=1/1-required-since-the-ruling` with the counts key
   matching the counted key. IF THE WHOLE-FILE CENSUS PRINTS ANYTHING OTHER
   THAN `core-csharp.45/both.6/ue-probe.1/repo.10` over 69, SECTION 4 OF THIS
   RECORD IS WRONG AND IS CORRECTED IN THE SAME COMMIT rather than left
   standing. That is the device section 3 says I failed to hold myself to.
3. `python3 tools/systems-inventory-check.py`: CONDITION unchanged from the
   14:24 record, `typedBy` director 7 and builder 62 summing to 69, untyped 0.
4. `python3 tools/ps-check.py` and `python3 tools/docs-check.py`, the latter
   after this file exists.
5. `python3 ledger/verify.py`, footer pasted FROM `ledger/.verify-footer`.
   CONDITION: `director_cadence` green with this record's stamp. If it is not,
   the stamp or the spawn row is wrong and the commit does not go in on a
   hand-edited gate.
6. ON THE NEXT ART DISPATCH, not before the commit: the prediction stands as
   the builder wrote it and is the acceptance criterion.
   `artBlenderChosen=C:\LedgerTools\blender\4.5.13\blender-4.5.13-windows-x64\blender.exe`
   with `artBlenderVersion=Blender~4.5.13~LTS`, plus `artCommitInputs` with its
   three counts and `artCommitStaged=N/N-matched`. A DIFFERENT PATH IS NOT A
   FAILURE OF THIS RULING: it is the search working and the eight-day-old
   report being stale, and the run says which.

## 7. The quality ladder at close, and the queue

Best available or first working, per aspect, next rung named. None is blank.

- The board's split sentence: at "computed, in his register, read back off the
  rendered bytes, with the zero shaped so it cannot lose its denominator".
  Next rung: the position guard that cannot pass when it could not look, item E.
- The board as an instrument about two builds: at "honest about which build its
  green is in". Next rung is unchanged and is the only one that matters,
  `both` above 4 of 26 and `ue-probe` above 1 of 69, one measured parity row at
  a time.
- The art lane: at "three faults fixed, zero runs completed". Next rung is a
  committed frame, and no rung above it may be discussed until then.
- The lane's git handling: at "one array, one route proven, one route assumed".
  Next rung: the run says which route is in force, item G.
- The nullglob class: at "found, fixed and counted once". Next rung: the
  detector in the tree with both rungs, item H.

Queue items filed, numbers the resident's to assign, none started now. Items A
to D of the 14:24 record stand.

- E. The position guard's three states in `check_typed_attribution`, with a
  rejecting rung for the missing marker.
- F. The whole-file `where` census into the provenance sheet, one tap down,
  never on the face.
- G. The key naming which `safe.directory` route is in force, and the removal
  of the other once it is proven redundant.
- H. The unquoted-glob-assignment detector into `tools/ps-check.py`, accepting
  and rejecting fixtures both.

<!--RULING spawn=2026-09-09T15:14:21Z paths=tools/map.py,map.html,.github/workflows/ledger-art-blender-preview.yml,game-design/decision-2026-09-09-ruling-the-split-returns-and-the-blender-that-was-always-there.md-->
