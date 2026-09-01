# DIRECTOR RULING: the cadence bound is MEASURED at 100, the two-builder batch lands, one overturn confirmed (1 Sep 2026, late)

> **STATUS — LOG, 2026-09-01. NOT CURRENT once the dictated edits in Ruling 1 are in ledger/verify.py and queue item 018 exists; from then the constants and their comments in ledger/verify.py are the reading copy and this file is their history.**

The banner carries the only em-dash in this document, because
`tools/docs-check.py` hard-codes that character in the regex it accepts.
Named as a finding in the previous ruling and queued there; not a licence.

Fifth ruling of the day. This role has no shell. Every number below that
was produced by running something is the resident's or a builder's; my
check is that the code exists at the cited line and asserts what the number
claims. Where I could not check, it says so.

## What was verified before ruling

- `ledger/verify.py`: `DIRECTOR_WORK` has 8 entries (2296 to 2320) and
  `DIRECTOR_EVIDENCE` has 14 (2349 to 2388), counted by reading. The
  classifier (2464 to 2473) tests evidence first, exact path or prefix by
  trailing slash. The pathspec is derived (2534). The `other` pins for
  `production/queue/`, `production/specs/`, `ledger-v2/` and `CLAUDE.md`
  exist as assertions (3768 to 3771). Fixture a19 asserts a 6188-line
  manifest counts zero (4100 to 4114). r18's literal carries `claude:0`
  (4357). The series printer (3446 to 3524) reads `_cadence_classify`, the
  same function the gate reads, and prints the raw row above the summaries.
- `_meshgen_suite` (545 to 588) keeps three outcomes distinct and anchors its
  regex on the label. `propview()` and `meshgen_suite()` are IN the check
  list (5574), so this is running, not merely built. Accepting fixtures at
  5142 to 5153 (59/0 and 102/0), rejecting at 5240 to 5247 (a traceback with
  no count line, and 99/3).
- `tools/meshgen/propview.py` 598 to 609: the grid assertion is
  `ceil(sqrt(n))` at any n, as ordered.
- The fetch batch, all four files read in full. `fetch_vignette.py` borrows
  `get`, `sizes_of`, `links_for` from `tools/citypack/fetch_textures.py`;
  all three exist (lines 90, 115, 274). `--plan` needs no network; the
  selftest runs the accepting case first on the live pair, then two
  synthetic rejects and one header measurement. The spec's six targets are
  premise-consistent (pebbledash, roller shutter, tarmac patch, a period
  British hatchback) and every source named is on the licence allowlist
  (`ledger-v2/research/license-allowlist.md` line 5: Poly Haven, ambientCG,
  Sketchfab CC0 filter). Nothing is purchased, no account is used.
- `tools/attribution-check.py` line 106 to 124: `.glb` is absent. Glob finds
  37 `.glb` files, all under `ledger/Assets/Props/base-mesh/`. Queue 016's
  claim is correct. `THIRD-PARTY.md` line 186 names
  `ledger/Assets/Decals/ambientcg/` while the watched path is
  `ledger/Assets/StreamingAssets/Decals` (attribution-check line 68). Queue
  017 item 1 is correct.
- The row in the brief, re-counted: 50 non-zero values, 70 zeroes, 120
  walked. Values strictly above 100 begin at 110; 26 of them. Upper median
  of the 50 is index 25, which is 124. All three summaries in the brief are
  consistent with the row. `4388` and `1053` are present in the row; `6188`
  is not.
- My own row: `.claude/agent-log.tsv` line 184.

## Ruling 1: the batch LANDS, with dictated comment corrections in the same commit

Both halves are the best version this container can produce of things it
cannot run, and each says so at the seam. Nothing weakens an instrument;
two instruments that ran nowhere now run on every verify. The fetch half
records the licence obligation before the bytes, which is the order the
allowlist law wants.

Conditions. All are comment or label text, dictated here so nothing is
judged at apply time. They exist because the cadence builder fixed the
docstring's "seven prefixes" at line 4804 and did not grep for the twin,
which is rule 1's third corollary applied to the number eight.

1. **Line 2255**: the comment block from 2252 to 2264 is replaced by the
   text in Ruling 2 below (it carries the bound's new provenance).
2. **Line 2487**: `cannot work for seven` becomes `cannot work for a set of
   eight`.
3. **Line 3849**: `a set of seven prefixes since 1 Sep` becomes `a set of
   eight prefixes since 1 Sep`.
4. **Lines 2383 to 2384**, the `verifyfooter` reason, currently "the ONE
   evidence path that sits inside a work prefix", which the paragraph
   twenty lines above it (2333 to 2348) already says is false. Replace the
   reason string with:
   `"written by every green verify run; the first evidence path to sit inside a work prefix and, since 1 Sep, one of five (counted above)"`
5. **Lines 2884 to 2887**, the false first-parent claim. Replace the comment
   with:
   ```
   # THE REFERENCE INSTANT. `git log -1 -- <pathspec>` walks the FULL history
   # with git's default path simplification (not first-parent; that is a
   # separate flag) for the newest commit that CHANGED a path in the scope.
   # On this linear branch the two agree; if merges ever appear, a side-branch
   # commit can be the answer, which is the right answer to "when was this
   # scope last touched". Empty output means no such commit is reachable HERE,
   # which is two different worlds (never happened / not fetched) and both
   # fall back to HEAD.
   ```
6. **Line 3450**: `then where the inherited bound sits in` becomes `then
   where the bound sits in`. **Line 4512**: `and says the bound is
   inherited` becomes `and says where the bound came from`. The fixture at
   4510 reads `DIRECTOR_MIN_SOURCE` itself, so it survives the relabel
   without an edit; the two labels would not.
7. **`production/queue/015-wire-propview-selftest.md` moves to `done/`**
   with a status line naming this ruling. Its acceptance is met: both
   selftests run inside verify with counts in the footer (5574), and every
   widening it carried is in the constants.
8. **Queue item 018 is created** with the content in "Queue items" below.
9. **Stage by name**: `ledger/verify.py`, `tools/meshgen/propview.py`,
   `THIRD-PARTY.md`, `tools/attribution-check.py`,
   `tools/props/fetch_vignette.py`, `production/specs/vignette-fetch-01.json`,
   `production/queue/016-attribution-blind-to-glb.md`,
   `production/queue/017-fetch-route-followups.md`,
   `production/queue/018-verify-cadence-followups.md`, the 015 move, and
   this file. Never a `__pycache__` directory.
10. **The commit message quotes all four selftest counts from a run made
    AFTER edits 1 to 6**, never the brief's 77, 44, 59 and 102.
11. **Commit before pulling**, for the reason the previous ruling gave: a
    props publish from Jafar's PC moves the reference past my row, and the
    remedy is to resume this director, never to edit the stamp.

Applied by the resident under the one-line-correction clause: every edit is
dictated text with no logic in it. If the selftest count moves from 77 or
44 after these edits, stop and read which fixture moved before committing;
none of the six should touch a fixture's outcome.

## Ruling 2: the bound is 100, and it is now MEASURED, not inherited

The label changes tonight. The number does not, and here is the row it was
read from, so the next reader sees the evidence and not a summary:

    non-zero sorted: 2 4 8 10 11 12 14 18 19 19 21 26 30 32 34 34 38 47 51 57
                     67 79 81 89 | 110 124 144 145 153 161 180 183 228 279
                     299 327 333 363 509 585 725 1053 1206 1610 1614 1939
                     2274 2499 2811 4388
    zeroes=70 of 120 walked; non-zero median=124 p90=1939 max=4388
    at 100: 26 of 120 substantial

Three options were weighed against the row, not against each other's prose:

| bound | sits in | substantial | what it changes against 100 |
|---|---|---|---|
| 50 | the gap 47..51, four lines wide | 32 of 120 | adds six commits between 51 and 89 to mandatory review |
| **100** | **the gap 89..110** | **26 of 120** | nothing |
| 200 | the gap 183..228 | 18 of 120 | exempts the eight commits between 110 and 183 |

The honest thing to say about "sits in a gap" first: in a series of fifty
values spread from 2 to 4388 there are gaps everywhere, and 183..228 is a
wider one than 89..110. Gap-sitting was the whole argument for the old 100
and it is a weak argument on its own. What decides it is the absence of any
evidence for moving: the eight commits at 110 to 183 lines are instrument
and tool edits of exactly the size this gate exists to put in front of a
director, no harm is on record from reviewing them and none from the six
below 89 going unreviewed, and the one red on the board tonight is a
702-line batch that is substantial under every candidate. Moving a bound
while red is on the board is the move rule 2 forbids, and it is forbidden
even when the red is legitimate, because the next person cannot tell the
two cases apart from the diff.

So: **100 stands, relabelled MEASURED 1 Sep 2026 from this row.** The word
INHERITED leaves every printed line. Dictated text for lines 2252 to 2264:

```
# WHERE THE 100 CAME FROM, TWICE. It was first set from a printed series of
# per-commit changed lines under `ledger/Assets/Scripts` alone, where it sat
# in a real gap (nothing between 81 and 107). When the scope widened to the
# eight prefixes below (1 Sep) that series became a different population and
# the bound was carried as INHERITED until a series under the new scope had
# been printed and read.
#
# MEASURED 1 SEP 2026 (director ruling, game-design/decision-2026-09-01-
# cadence-bound-and-batch-review.md) from `--cadence-series 120` under the
# eight-prefix scope with the props outputs excluded: 70 zeroes of 120;
# non-zero sorted ... 67 79 81 89 | 110 124 144 ...; non-zero median 124,
# p90 1939, max 4388; 26 of 120 substantial at 100. The bound sits in the
# gap 89..110 of that row as it sat in 81..107 of the old one, and nothing
# in the row argued for either neighbour: 200 would exempt the eight commits
# between 110 and 183, 50 would add six between 51 and 89, and no harm is on
# record for either band. The printer that produced the row stays beside it:
#     python3 ledger/verify.py --cadence-series 120
# REVISIT when a per-prefix series exists (the printer's next rung, queue
# 018) or when a fresh 120-commit row shows a value inside 89..110.
DIRECTOR_MIN_SOURCE = ("MEASURED 1 Sep 2026 from --cadence-series 120 under "
                       "the eight-prefix scope (gap 89..110, 26 of 120 over); "
                       "a per-prefix series is the next rung")
```

**Revisit conditions, precisely, so this is not INHERITED wearing a new
word:**

1. A per-prefix series is printed (018) and shows any prefix as a distinct
   population, for instance `content/` dialogue banks sitting systematically
   above `tools/` edits. Then the next rung is a per-prefix bound, not a
   compromise value. This is the question the previous ruling asked and it
   CANNOT be answered today: `--cadence-series` prints one total per commit
   and the `biggest:` line is `sha:total`. No instrument in the project can
   see two populations under one number yet, so the question is a research
   task with a name, not a decision deferred.
2. After roughly 60 more commits under this scope, a fresh
   `--cadence-series 120` shows a value inside 89..110, or the zeroes
   fraction changes regime (70 of 120 today).
3. A false red, quoted with the instance: a commit the resident judges not
   to have needed a director, refused at over 100 lines. One instance is a
   note; three is a ruling.

Not a revisit condition: the gate going red on a batch someone would rather
have committed. That is the gate working.

## Ruling 3: the overturn is CONFIRMED, from the row

The previous ruling's parenthetical said the series' three largest readings
(6188, 4388, 1053) "are the machine-written props files that Ruling 3
removes". The post-change classifier excludes both props files by exact
path, and fixture a19 asserts a 6188-line manifest counts zero. The
post-change row still contains 4388 and 1053 and its max is 4388. A value
that survives an exclusion cannot be the thing excluded, so two of the
three were never props files. The reclassification removed one large
reading, as the builder said, and the docstring the builder wrote at 4827
to 4832 had this right ("the largest reading in the window, 6188, commit
0615d189, leaves the series entirely, along with 123 and 78") before the
brief raised it.

The builder's identification of `e640e001` as 2302 lines of hand-written
`meshgen.py` plus specs and Blender scripts is NOT verified by me; I have
no shell and did not open that commit. It is also not load-bearing: 4388
is substantial under every bound considered above, and the bound reasoning
in Ruling 2 was done on the row, which needs no knowledge of what any one
reading was.

The previous ruling is a LOG and is not edited. This paragraph is its
correction; a reader who finds the parenthetical there finds the row here.

## Ruling 4: the five things the builder named as undone

| # | item | disposition |
|---|---|---|
| 1 | `verify.py` whole-file em-dash sweep | **Queued**, unchanged from the previous ruling's Ruling 6 item 2. The file carries 435 lines with the character tonight by my grep (438 in the previous ruling; the difference is lines the batch rewrote clean). The builder's added lines are clean, which is the rule for new text. Not a landing condition. |
| 2 | Line 2884 says `git log -1 -- <path>` walks first-parent history | **Condition on this batch**, Ruling 1 item 5. It is a false comment on the reference-instant logic, which is the exact code the batch changed; rule 1's second corollary says a change finishes by re-reading the comments beside it. Text dictated, no logic. |
| 3 | `pathsEvidence ... by N of M rule(s)` counts labels as N and rules as M | **Queued as 018(a)**. `evidence_hits` is keyed by label (a19's own assertion is `propsout == 2`), so the phrase prints "1 of 14 rule(s)" for two rules hit under one label, and `d1out` has done the same for five rules since before this batch. A number wearing the wrong unit in every footer is a rule 2 fault, and the fix moves a17's literal at 4044, so it is a logic change with a fixture and does not go in under the correction clause. |
| 4 | Untracked files under `.claude/` count as work until committed | **Queued as 018(c), with the finding narrowed.** The reader uses `ls-files --others --exclude-standard` (2953), so this is true of every work prefix, not `.claude/` specially, and gitignored files are already excluded. `.gitignore` has no `.claude` entry (grep: no match), so a local settings file would count forever; the fix for that is one gitignore line, not the gate. What the gate lacks is a NAME beside the count: the summary prints `N untracked in M new file(s)` and never says which, so the day this inflates it will be a number nobody can act on. |
| 5 | Three implementations of the "N passed, M failed" parse | **Queued as 018(b), with the count corrected to FOUR.** Lines 572, 659, 698 and 2191 (`frame-drift`, which the builder's grep missed). The builder was right to name the duplication rather than refactor inside a batch already carrying the reclassification; the count being wrong by one is rule 1's third corollary doing what it always does. `_meshgen_suite` is the one to keep: it is the only one of the four that distinguishes "no count line" from "failed", and the other three read a missing line as one bare RED with no denominator. |

## Two things nobody named

- **`_meshgen_suite` line 577**: a tool that exits non-zero after printing
  `0 failed` reports "0 of N check(s) FAILED: selftest failed". Red, so not
  dangerous, but the string contradicts itself. Folded into 018(b).
- **`game-design/voice-conds/*.bin`**, 23 files by glob. I have NOT
  verified what they are. If they are per-speaker conditioning derived from
  VCTK recordings they are derivatives of a CC BY 4.0 work under the same
  reasoning `attribution-check.py` applies to the barks, and neither `.bin`
  nor that directory is known to the sweep. This is exactly the sweep 016
  already orders ("sweep the set itself against what the project actually
  holds"); it is named here so 016's builder looks at it rather than adding
  one suffix and stopping. Whether `.bin` belongs in a suffix allow-list at
  all is the builder's call, with the answer written beside the set.

## The fetch half, specifically

Lands as-is. Two notes for the record, neither a condition:

- The builder's "tested both ways" for the vignette row is a claim about a
  manual run; the selftest in `attribution-check.py` has no fixture for the
  "recorded ahead of the assets" branch. The branch predates this batch,
  the live run is its accepting case tonight (the directory does not exist,
  the token does), and the rejecting case is the same branch with the token
  absent, which the builder says it ran. Acceptable; 016's builder should
  add that fixture while in the file, because a guard branch with no
  rejecting fixture is rule 5b waiting.
- The proxy denials are recorded in the spec as measured, with the hosts
  and codes named. That is the right shape: a blocked channel written down
  rather than routed around, and the container doing the deciding from a
  committed catalogue whose narrow denominator the spec states in its own
  words.

## Queue items

**018-verify-cadence-followups.md** (infrastructure, instruments, one
instrument-builder, one session):

- (a) `pathsEvidence` phrase: count RULES hit, not labels. Keep
  `evidence_hits` by label for the printed breakdown and add a rule count
  beside it; a17 and a19 assert the true numbers. Accepting case: the live
  tree.
- (b) One selftest-count parser. Fold `ref_bench`, `decal_ink` and the
  `frame-drift` check (2191) into the shape `_meshgen_suite` has (rename
  it; it is no longer meshgen-specific), keeping the three outcomes and
  fixing the "0 of N FAILED" string on a non-zero exit. The fixtures at
  5142 to 5153 and 5240 to 5247 are the model; each folded check gets its
  own accept and reject.
- (c) When `untracked_files > 0`, print the largest untracked work path(s),
  capped and announced. And one `.gitignore` line for `.claude/*.local.*`
  if such a file ever appears; not before, because a gitignore entry for a
  file that does not exist is a claim nobody tests.
- (d) The bound's next rung: `--cadence-series` prints `label:lines` per
  commit beside the total, so the two-populations question in Ruling 2 can
  be read off a row. Print first; a per-prefix bound, if any, is ruled from
  what it prints.

Already queued and unchanged: the formatting-law lint and whole-file sweep
(verify.py first), the docs-check banner regex, the premise-touch kind gate
research, the prop contact sheet. 016 and 017 are accepted as written.

Next free number after this ruling: 019.

## Quality ladder

The gate's rung tonight: bound measured under the live scope. Next rung:
per-prefix series (018d). The fetch route's rung: proven as far as the
container can reach, with the licence row ahead of the bytes. Next rung:
the first `--probe` run on the PC, which answers the two ABSENT lines and
picks the shutter by eye from fifteen previews. The rung after that is the
one Jafar can see: a shutter on a shopfront in the D1b frame.

## Deliberately not decided

- Whether one bound fits `content/` and `tools/`. Not decidable from any
  row the project can print tonight; 018(d) is the instrument, and the
  decision follows its first printed series.
- C4_render_pebbledash's route change from FETCH to GENERATE/2D. The spec
  names it as a director question and it is one; it waits for the probe,
  because ruling it before the Decal and Substance types have been asked
  is deciding from an absence in the wrong list.
- The `.bin` question above. Named for 016's sweep, not ruled.

## For the next session in one line each

- Land: the batch as staged in Ruling 1 item 9, after edits 1 to 6, with
  counts from a fresh run in the message. Commit before pulling.
- Queue: create 018 from the text above; move 015 to done.
- Spawn: one instrument-builder for 016 (with the `.bin` question and the
  ahead-of-bytes fixture in its brief), do-not-commit standing. 018 can
  follow in the same builder's next session or a second spawn; it does not
  block anything.
- No Fable spawn until a builder batch touching the scope needs review.
  018 will; 016 and 017 will not unless they exceed 100 lines, and 016
  probably will not.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 184):

    2026-09-01T23:21:58Z	studio-director

<!--RULING spawn=2026-09-01T23:21:58Z-->
