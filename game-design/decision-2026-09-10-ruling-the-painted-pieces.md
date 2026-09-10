<!--RULING spawn=2026-09-10T08:21:21Z-->
# LOG: ruling on the painted pieces, queue 223, 226 and 227, 2026-09-10

> **STATUS: LOG, 2026-09-10. NOT CURRENT** once the conditions in section 7
> are printed and the batch is committed. Decision record, binding on the
> resident for this commit.
Author: tier-1 director, stamp above naming row 510 of
`.claude/agent-log.tsv`, read this session (`2026-09-10T08:21:21Z` TAB
`studio-director`, the newest director row in the log at the time of writing).

Scope: 1629 changed lines, one builder, reported at a clean boundary. Six
questions put to me plus the print-before-commit conditions.

STAMP NOTE for the resident. The stamp is the bare timestamp, verbatim from
the log, because `_cadence_epoch` in `ledger/verify.py` strips the trailing Z
and hands the rest to `fromisoformat`: any suffix after the Z lands the stamp
in `unmatched` and the ruling clears nothing while looking correct. If the
hook has since written a newer `studio-director` row for this spawn, print
the tail of `.claude/agent-log.tsv` and set the stamp to
`rulingUnruledNewest` as `verify.py --cadence` prints it. Two fresh spawns
with one ruling is green (verify's own fixture a14), so an extra director row
does not block; a malformed stamp does.

## 0. What I verified personally, and what I did not

I have no shell in this spawn. I can read files and grep; I cannot run a
suite, open a still, or run git. So this section splits the two, and nothing
outside the first list may be quoted later as a measurement.

VERIFIED BY ME THIS SESSION, by reading the files named:

  V1. `tools/surface-tint-check.py` EXISTS on disk, 178 lines, and it is the
  tool the comment promises: it parses both copies, treats Unity's switch as
  authoritative, prints `N surface(s) compared` as its denominator, prints
  the words `NOTHING MEASURED` on every un-parsed path, and ships a
  `--selftest` whose accepting case is the live tree and comes first, with
  synthetic rejecting fixtures after it. THE BRIEF I WROTE SAID THIS TOOL
  DOES NOT EXIST. That was false when I wrote it. Section 5 is rewritten
  around what is actually missing.

  V2. NOTHING CALLS IT. A grep for `surface-tint-check` across every `.py`,
  `.yml`, `.yaml` and `.sh` in the repo returns one file: the tool itself.
  `ledger/verify.py` does not run it and no workflow step does.

  V3. The comment that promises it, `ue-probe/Source/LedgerProbe/Public/
  SurfaceBind.h` lines 240 to 247, claims more than the tool does twice
  over: it says the tool "parses both files and refuses any disagreement, in
  the container, before a dispatch", where the tool compares TINTS ONLY (its
  own docstring says smoothness, emission, tiling and pattern are copied and
  not compared) and nothing runs it in the container or anywhere else.

  V4. `ledger/Assets/Scripts/Game/StreetVignetteHost.cs` reaches
  `AssetLibrary` for a material at exactly two sites, line 238 and line 299,
  and both call `AssetLibrary.Material`. Neither `MaterialVariant` nor
  `MaterialGraded` appears anywhere in that file. `MaterialVariant` is
  defined at `AssetLibrary.cs:271` and its only caller is
  `MaterialGraded:315`, which this host does not call, so there is no
  indirect path either. THE BUILDER'S REFUTATION OF MY BRIEF IS CONFIRMED on
  the Unity side. The Unreal side of that claim I did not verify.

  V5. `ledger/Assets/StreamingAssets/Vignette/scene.json` contains ZERO
  occurrences of the token `C15` (30 occurrences of `yellow`, `C15` or
  `fascia` case-insensitively, all of them the other two tokens). That is
  consistent with the builder's report that the staged product is stale.
  What a complete C15 fascia entry looks like I did not verify.

  V6. Queue 226's own filename is
  `226-the-yellow-line-art-is-held-and-three-files-say-it-is-not.md`. It says
  THREE where the builder found FOUR. The filename is a sixth instance of the
  same undercount, and section 4 deals with it.

ON THE BUILDER'S REPORT, UNVERIFIED BY ME: every count in the batch summary.
The 355 checks and 0 failures against a baseline rebuilt at HEAD from 300;
frame-stats 108/0; core-port 2517/0 over 2498 golden rows; crime-probe 198/0;
CoreTests builds clean; 1623 added lines swept with 0 em-dashes; RoadLines011
at 216.0/180.3/47.7 with yellowness 150.5 against 3.4, -0.3, 4.6, 4.6 and 4.8
for the five white sets; 610 pieces now and 593 last landed; 51 staged pack
files of which 15 unused; 14 library surfaces, 2 procedural, 36 maps. A count
in this ruling is a CLAIM TO BE CHECKED. If a printed number in section 7
differs from the number recorded here, the commit is blocked until the
difference is written into this file.

## 1. The batch: APPROVED WITH AMENDMENTS

Approved in substance. Three things the builder did are why it is approved
rather than refused, and they are the behaviours this studio is trying to buy:
it refuted the brief I wrote instead of implementing it, it declined to make a
number green by making the picture worse, and it flagged its own second reader
instead of leaving it for a later session to find.

Three amendments bind. A and B block the commit; C is a condition on what the
verdict prints.

AMENDMENT A (question 5, the guard). The tool exists (V1). What is missing is
a CALLER (V2) and a comment whose scope matches the tool's (V3). Both land in
this batch:

  A1. Wire it so it runs without being remembered. Either a check inside
  `ledger/verify.py` that shells `tools/surface-tint-check.py` and goes red on
  its non-zero exit, or an explicit container step before dispatch. One of
  them, not a promise of both. Built is not running (rule 6), and a guard
  nobody calls is a comment with a shebang.

  A2. Correct the comment to the truth of what now exists. Dictated text,
  replacing the sentence from "and tools/surface-tint-check.py" to "decays",
  with the bracketed choice resolved to whichever A1 landed:

      // the literal from that switch, and tools/surface-tint-check.py parses
      // both files and refuses a disagreement ON THE TINTS ONLY. It runs from
      // [ledger/verify.py | the container step named in the workflow], so it
      // cannot be forgotten. Smoothness, emission, tiling and pattern are
      // copied here too and NOTHING compares them: widen the tool before
      // trusting a green line about a narrower thing. A copied constant with
      // no check over it is a constant that decays.

AMENDMENT B (question 4). This batch does not hand-edit
`ledger/Assets/StreamingAssets/Vignette/scene.json`. Section 4 says what
happens instead.

AMENDMENT C (question 2). The verdict prints the keys dictated in section 2.
`decalQuadsHidden=10/20` is refused as a verdict key, on its denominator, not
on the behaviour it reports.

Everything else lands as reported, subject to section 7: the SurfaceSpec tint
fallback over the 6 interior and 4 paint_yellow pieces, the second-pass
interior borrow, the ten decal cards, the untouched `_b` rule, and the
four-site yellow correction.

## 2. RULE 3, hiding ten multiply quads rather than painting them opaque: UPHELD, provisionally, with its next rung named

The question is not which number looks better. It is which of two defects a
player meets, because the premise (CLAUDE.md section 0) makes the visual
target photoreal, wet, overcast, GRIMY Britain and the Meridian Test's first
clause is that a GTA or KCD2 player does not bounce off the visuals. Grime is
premise content here, not decoration, so both options cost something real and
the ruling has to say which cost is recoverable.

An opaque grime quad is a wrong pixel asserted as content: a flat dark
rectangle on wet stone, in every frame, arguable in review, and exactly what
rule 4 means by letting a green number stand in for the frame it claims to
describe. Painting it opaque would move `piecesUnpainted` to 0 while making
the judged frame worse, which is rule 2's prohibition in different clothes:
no number moved to make red go away.

A hidden quad is an absence: invisible in the frame, unarguable in a count,
and recoverable the moment the cook can ship a second blend mode. The builder
is right that blend mode is a property of the material and not of the
instance, so no instance-level fix exists in this batch. Counted absence is
the cheaper defect.

UPHELD, with three conditions.

CONDITION 2a, the next rung is named, not blank. The first working result is
ten hidden quads; the best available result is a multiply or translucent
material in the cook with the ten quads rendered in both hosts. That is the
next rung and it opens as a queue item in this batch, titled so it is
findable: "decal multiply blend in the cook, both hosts, ten quads". Without
it this aspect closes with a blank next rung, which makes it a research task
and not a finished aspect (`production/quality-ladder.md`).

CONDITION 2b, what the verdict must print. `decalQuadsHidden=10/20` counts
the wrong set: 20 is all decals and the ten cards were never candidates for
hiding, so the key reads "half the decals failed" when the true statement is
"every multiply decal is pending and every card painted". Rule 3b: ask what
the denominator COUNTED. Print instead, on the done line, whole-run numbers,
no spaces inside any value:

    decalCardsPainted=10/10
    decalMultiplyPending=10/10 reason=no-blend-mode-in-cook
    piecesUnpainted=10/610 expected=10 ruling=decision-2026-09-10-ruling-the-painted-pieces
    pairDivergence=decal-multiply-ue-hidden-unity-rendered

Each is a last-wins whole-run count and the comment at the emit site says so
(`.claude/rules/instruments.md`, first bullet).

The fourth key matters most and the builder was right to name it rather than
bury it. The judged artifact is a PAIR of streets. Unity renders the grime,
Unreal does not, so the pair is genuinely unmatched today and the verdict says
so in words a later reader cannot mistake for parity. Do not close it by
hiding the quads in Unity too: that is making both frames worse to make one
key clean.

CONDITION 2c, the bound, so nobody reads the number as a regression and
nobody gets a ratchet. The gate asserts `piecesUnpainted == 10` and
`decalMultiplyPending == 10`, equality and not an upper bound, and the
assertion message names this file. Eleven is a regression and trips it. Nine
means the cook work landed and also trips it, deliberately, because that is a
ruling-level change that should not slide in unread. A guard that cannot tell
a regression from an improvement is a ratchet (rule 5b); this one tells them
apart by refusing both and forcing a read. It ships tested on the case it
should PASS first, then on a planted 11 produced by disabling one card route,
and the planted run is printed, never the bound loosened.

## 3. RULE 4, my brief was wrong, and the divergence question

My brief told the builder that Unreal was missing a `_b` variant rule the
Unity host has. V4 above confirms the builder and refutes me, and I verified
it myself rather than accepting the report: two material call sites in
`StreetVignetteHost.cs`, both `AssetLibrary.Material`, no `MaterialVariant`,
no `MaterialGraded`, and no indirect path since `MaterialGraded:315` is
`MaterialVariant`'s only caller. Zero of the 610 pieces ask for a `_b` file in
Unity. The Unreal half of the builder's claim is unverified by me.

MY BRIEF WAS WRONG, recorded plainly because that is the whole point of
writing it down: a wrong premise in a brief silently re-frames every judgement
made on top of it and no downstream measurement catches it. The cost of my
error is the pass the builder spent proving my sentence false, and that was
the correct order of work.

THE DIVERGENCE QUESTION, ruled as a standing answer because it will recur:
NO. While the judged artifact is a pair of frames from two engines, a rule
that changes what one engine renders may not be added to one engine alone. It
lands in both hosts in one batch or it does not land. A more varied Unreal
street is not an improvement if it makes the pair incomparable; that is
destroying the instrument to improve the sample, the one plan shape I refuse
outright. The `_b` rule therefore becomes a single queue item naming both
hosts, and its done condition is a matched pair, not a prettier street. When
it does land it already has its honest counter: `AssetLibrary.VariantsUsed`
at `AssetLibrary.cs:288` exists precisely so that "the city is varied" and
"the fetch landed nothing and everything fell back" cannot read alike, and
the done line prints it.

THE 15 UNUSED PACK FILES: a fact to record, not a fault to fix, and not waste.
Fifteen of 51 staged pack files unused by both engines in this scene
(builder's report, unverified by me) is only a problem if something CLAIMS
they are in the frame. So the staging tool prints the three numbers together
and none of them is recoverable only by subtraction:

    packFilesStaged=51 packFilesReferenced=36 packFilesUnused=15

Anyone who then wants the fifteen on screen goes through the `_b` queue item,
both hosts, and not a quiet one-sided wiring.

## 4. Question 4, the fifth copy of the yellow claim in a staged build product

`ledger/Assets/StreamingAssets/Vignette/scene.json` is a build product of
`tools/stage-vignette-scene.py`.

OWNERSHIP: the generator owns it, and the builder's refusal to hand-edit is
UPHELD on its stated ground, which is correct. A hand-edited generated file is
worse than a stale one, because the next regeneration silently reverts the fix
and nobody is watching that moment. The fifth copy of the false yellow claim
is fixed in `tools/stage-vignette-scene.py` and re-staged. If the queue-226
fix already corrected the generator, this batch regenerates and commits the
product, staged BY NAME and never by `git add` on the directory
(`.claude/rules/ci.md`). If the generator is not yet correct, the generator
fix is a named queue item and this ruling records that the false sentence
survives in exactly one place.

THE STALENESS: a FAULT, and of a class this project has already paid for, but
not a fault this batch must finish. V5 confirms the token `C15` appears zero
times in the staged file. A stale generated file in the tree is
indistinguishable from a current one at read time, which is the same failure
mode as a run carrying the previous run's files under its own name. Three
things follow, in priority order:

  4a. The generator writes a provenance line into what it generates: the
  generator's name and the commit it ran at. A stale product then announces
  itself instead of being argued about. This is the real fix for the class and
  it is a small one.

  4b. `ledger/verify.py` gains a check that regenerating produces no diff, so
  drift is red rather than archaeological. Tested on the passing case first,
  then on a planted stale product.

  4c. The current staleness is recorded in the queue item with its evidence
  (zero `C15` occurrences in the staged file), not in a conversation.

4a and 4b may land in this batch or the next. 4c lands in this batch.

AND THE SIXTH COPY, which nobody counted: queue 226's own filename says
`three-files-say-it-is-not` where the builder found four sites (V6). Do not
rename the file; add one line to its body stating that the title undercounts,
that the true count was four plus the staged product, and that the count was
found by grepping the SENTENCE rather than the site. That is rule 1's second
half working exactly as intended, and the record should show it did.

## 5. Question 5, the unguarded second reader: THE QUESTION WAS WRONG AND THE ANSWER IS AMENDMENT A

I briefed this as a comment promising a tool that does not exist. V1 says the
tool exists and is good: accepting case first, synthetic rejecting fixtures,
`NOTHING MEASURED` on every un-parsed path, a denominator that counts what was
compared rather than what exists. Ruling on the question as asked would have
ordered work that was already done, which is its own kind of waste, so the
instrument got suspected first (rule 3) and the file got opened.

What IS unguarded is narrower and real, and the batch may not land carrying
it: nothing runs the tool (V2), and the comment claims both a wider scope and
a run-time that do not exist (V3). A comment that over-claims a guard retires
the reader's suspicion, which is the same decay shape one size smaller. A1 and
A2 in section 1 are the fix, both in this batch.

The builder flagged the duplicate rather than leaving it. That is why this is
an amendment and not a refusal.

## 6. Question 6, queue 227's honest denominator: ACCEPTED as worked out, with the printing fixed

The arithmetic is right: 14 library surfaces asked, 2 procedural by
declaration, pack population 12, reading 12 of 12. It agrees with the UE side,
where `SurfaceBind.h:248` declares `ProceduralSurfaceCount()` as 2 and the
name array is `{"interior", "paint_yellow"}`, which I read this session.
Accepted, with three conditions on the printing, from rule 3b and
`.claude/rules/instruments.md`:

  6a. All three numbers on the done line, so none is recoverable only by
  subtraction and no reader does arithmetic to learn what was examined:

      surfacesAsked=14 surfacesProcedural=2/14 surfacesResolved=12/12

  6b. The interior's two borrowed maps counted apart and named, same done
  line, since these are whole-run numbers:

      mapsFound=36/36 mapsBorrowedInterior=2

  6c. If either denominator is ever zero, the line prints `nothing measured`
  and does not print a clean ratio. A 12/12 over an empty input set is the
  silent-instrument failure, and this tool is new enough that the empty case
  has not happened yet.

No key above carries a space inside its value; use `/` and `..` for structure.

## 7. Conditions the resident must PRINT before committing

Prints, not assurances. Every count in section 0's second list is unverified
by me, so the resident re-runs and pastes the output. If one of these cannot
be produced, the commit waits and the reason is written into this file.

  7.1 `python3 ledger/verify.py` green, footer pasted FROM
  `ledger/.verify-footer` and never from the scrollback, since red deletes the
  file and an absent footer is an absent pass. Read the CLAUDE.md word count
  it prints.

  7.2 The five suites re-run with their counts and denominators printed:
  vignette-spec-test checks and failures WITH the HEAD sha its baseline was
  rebuilt at (a baseline whose origin commit is unprinted is not a baseline);
  frame-stats; core-port with its golden row count; crime-probe; the CoreTests
  build result. The builder reported 355/0 against 300, 108/0, 2517/0 over
  2498, 198/0, clean.

  7.3 The formatting sweep printed with its denominator and BOTH halves of the
  law: em-dashes and italics, hits beside lines swept. The builder reported 0
  em-dashes over 1623 added lines and reported no italics sweep. A zero
  without its denominator cannot tell nothing from fine.

  7.4 `python3 tools/surface-tint-check.py` run, its done line printed with
  the surfaces-compared denominator, and `--selftest` run with its
  "N ok, M failed, over K check(s)" line printed. I read this tool but have
  never seen it execute; an unrun checker printing a plausible string is the
  silent-instrument failure.

  7.5 The call-site grep that proves A1 landed: the line in `ledger/verify.py`
  or the workflow that invokes the tool, pasted, plus the file and line of the
  corrected comment from A2. Built is not running.

  7.6 The paint line from a LANDED CI run whose commit CONTAINS the batch
  commit, captured by ancestry and not by branch movement or run name, with
  the sha recorded BEFORE dispatch: `paintRoutes=pack.580/tint.10/
  decal-card.10/decal-multiply.0`, `piecesUnpainted=10/610`, and the 2b keys.
  A run that measured nothing says `NO RUN` and does not carry the previous
  run's stills under its own name.

  7.7 The stills OPENED and READ, both engines, before any gate colour is
  quoted: the Unreal street and the Unity street side by side, looking for the
  ten absent grime quads and for any tint that reads as plastic. Read every
  still before reading any gate. Then print a quantity for whatever the eye
  flagged, because looking is strong evidence that something is wrong and weak
  evidence of what.

  7.8 The yellow sentence grepped across the whole tree by SENTENCE and not by
  site, printing the total hit count and every path. Expected: four sites
  corrected, one remaining hit in the staged `scene.json` per section 4, plus
  queue 226's filename per V6. Any further copy is a finding and the commit
  waits.

  7.9 Call-site greps, printed, for the tint fallback and the interior map
  borrow: the function and line that actually call them. Core being tested is
  not a call site.

  7.10 The 2c guard run twice, both runs printed: the passing case at
  `piecesUnpainted=10`, then the planted 11.

  7.11 `git status --porcelain` for `tools/surface-tint-check.py` and
  `ledger/Assets/StreamingAssets/Vignette/scene.json`, printed. I cannot run
  git: whether the tool is tracked, whether the staged product carries
  uncommitted changes, and whether anything stages a whole directory are facts
  this commit turns on.

  7.12 `tools/docs-check.py` and `tools/goal-block-check.py` green, printed.
  This file declares LOG with its date in its first lines because docs-check
  requires both that and the words NOT CURRENT within the first 8 lines.

  7.13 The queue items this ruling requires exist as files under
  `production/queue/`, paths printed: the multiply blend rung (2a), the `_b`
  variant pair item (section 3), the `scene.json` provenance and staleness
  item (4a, 4b, 4c), and the one-line correction in queue 226 (section 4).

  7.14 `python3 ledger/verify.py --cadence` printed, showing
  `rulingRowsUnruled` and `rulingUnruledNewest`, so the stamp at the top of
  this file is confirmed to name a real director row newer than the reference
  commit rather than landing in `unmatched`.

## 8. What this ruling does not authorise

No pull request. No purchase and no account use. Nothing to Jafar from any
tier but the Producer. No threshold, bound or denominator in this batch moved
to make a red number green; if one needs moving it comes back here. The
director who wrote the wrong `_b` brief and the false "that tool does not
exist" premise is the author of this file, and V1 and V4 stand above both.
