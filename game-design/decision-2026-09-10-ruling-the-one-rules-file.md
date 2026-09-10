<!--RULING spawn=2026-09-10T12:06:47Z-->
# LOG: ruling on the one rules file, 2026-09-10

> **STATUS: LOG, 2026-09-10. NOT CURRENT** once the fold has landed and
> section 10 carries the printed numbers. Decision record, binding on the
> resident and on the builder who applies it. Jafar's ruling, 2026-09-10, in a
> cleanup batch: ONE rules file, CLAUDE.md plus the constitution, with
> `.claude/rules` folded in and the casebooks pushed to an appendix no session
> reads at start. This file governs the fold and nothing else.

Author: tier-1 director spawned 2026-09-10T12:06:47Z (row 521 of
`.claude/agent-log.tsv`, read this session; the row reads
`2026-09-10T12:06:47Z` TAB `studio-director` and is the latest studio-director
row in the file). If the cadence gate reports this stamp as unmatched or stale,
the resident pastes the gate's numbers into section 10 and does not touch the
stamp: a resident never stamps a ruling.

## 0. What I verified and what I did not

No shell in this spawn. I can read, grep and search; I cannot run `wc`,
`verify.py` or `git`. Everything I could not run is a condition in section 8.

**The four word counts (1996, 317, 497, 486) are the brief's, not mine.** What
I could check is consistent with them: by reading, CLAUDE.md ends at line 228,
`ledger-v2/studio-v2/constitution.md` at 14, `.claude/rules/ci.md` at 55 and
`.claude/rules/instruments.md` at 51, which are the brief's line counts
exactly. Consistent is not proven. Condition 1 prints the words.

Verified by reading, this session:

1. **What the loader put in this session's prompt.** Three project-instruction
   blocks arrived: CLAUDE.md, `.claude/rules/ci.md`, `.claude/rules/instruments.md`.
   The constitution did not arrive. No casebook arrived. This is an
   observation of one session, and it is the only direct measurement of the
   loading mechanism this project has.
2. **Both rules files open with YAML frontmatter keyed `globs:`**
   (instruments.md lines 1 to 4, ci.md lines 1 to 4).
3. **The documented key is `paths:`.** Claude Code's memory documentation
   (code.claude.com/docs/en/memory) says rules with a `paths` field load when
   Claude works with matching files, and rules without a `paths` field load
   unconditionally, like CLAUDE.md. To the loader, a `globs:` key is no
   `paths:` key. That is a mechanical cause that fits item 1; it is a reading
   of documentation beside one observation, not a controlled test. Condition
   12 is the test.
4. **CLAUDE.md has no `@` import.** Grep `^@|\s@[A-Za-z./]` over its 228
   lines: 0 hits.
5. **The guard.** `ledger/verify.py` line 1558 `CLAUDE_MD_WORDS = 2000`; line
   1589 counts `len(text.split())`; the docstring at lines 1578 to 1581 says
   in capitals that the bound is Jafar's and is not a measured one, and that
   the printed series is what may argue for moving it; the fixtures at lines
   6053 to 6085 read the constant symbolically, so they follow it.
6. **The goal-block checker** (`tools/goal-block-check.py` lines 46 to 55)
   requires the copy to OPEN the file with the goal heading and to be closed by
   the first `\n---`. The order in section 3 keeps both.
7. **Cadence scope.** `ledger/` is a work prefix (verify.py line 2931). The
   fold edits verify.py, so the fold commit is builder work that needs a
   ruling. This is the ruling.
8. **Citation counts**, by grep this session. `.claude/rules/(ci|instruments).md`:
   79 occurrences in 54 files. `constitution.md` or "constitution law": 26 in
   18. The word `casebook`: 55 in 23. The citation form "law N" (N in 1..12):
   30 in 22. The form "rule N" (N in 1..13, 3b, 5b): 1404 in 382, an upper
   bound carrying noise from other uses of the word. Both citation series are
   live and both must survive.
9. **Queue 020**, the casebook pointer check, carries the status CLOSED
   2026-09-10, unbuilt. Nothing checks today that a path under "Where the
   rest of this file went" carries what it points at.
10. **A record rests on the false premise.**
    `game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md`
    line 628 to 630 declines to load a casebook "conditionally the way it
    loads `instruments.md`". It never loaded instruments.md conditionally.
    Section 7 dictates the correction.

**Premise check** against CLAUDE.md section 0: a process change. Nothing in it
touches Meridian, the era, the moat or the visual bar. Section 0 moves intact.

**A correction to the brief.** "The fold does not add a word to what is read"
is true of the two rules files and false of the constitution. The constitution
is not read at start today (item 1). Today's start-read set is three files:

    1996 + 497 + 486 = 2979 words   (CLAUDE.md + ci.md + instruments.md)

not 3296. The constitution's 317 words are new start-read cost, and dedup is
where the fold pays for them.

## 1. Question 1: does the fold happen. YES.

Yes. Jafar ruled it, it does not contradict the premise, and the measured
facts favour it rather than merely permit it. Two of the three files a
session reads at start claim in their own headers to be conditional and are
not, so the current arrangement misstates its own cost to every reader; the
one counter that guards start-read cost watches 1996 of 2979 words and calls
the result the whole; and the only place duplicated text can be seen and cut
is one file. The constitution is the one genuine cost, 317 words that become
read at start, and it is also the one genuine gain: a document that "binds"
(CLAUDE.md line 37) but is not read at start binds only sessions that go
looking for it. The fold is accepted on the condition in section 2 that it
does not raise what a session reads at start above today's 2979 words, which
means the dedup has to earn at least the constitution's 317. The alternatives
are in section 2 as fallbacks, not rivals.

## 2. Question 2: the cap, and its arithmetic

Two numbers can be derived from the four without guessing. What each IS a
statistic of:

| number | arithmetic | what it is |
|---|---|---|
| 3296 | 1996 + 317 + 497 + 486 | sum of four last-wins counts: the fold with zero dedup. The "nothing lost" ceiling |
| 2979 | 1996 + 497 + 486 | sum of the three files the loader put in this session's prompt: the start-read cost on 2026-09-10 |

Neither is the landed size of the deduplicated file, which does not exist yet
and cannot be set from these four numbers. So:

**(a) Acceptance ceiling for the fold commit: landed count at or under 2979.**
Not a guess and not a target: it is the statement "a cleanup does not raise
what a session reads at start", written as the measured number. The word
count of the deduplicated draft is printed (condition 2) and read against it.
If it exceeds 2979 the fold is not refused; it takes shape B below.

**(b) Standing cap after landing: `CLAUDE_MD_WORDS` = the landed count,
exactly as verify.py's own counter prints it, set in the same commit and only
after the count is printed.** Unset until then. Reason: today the file sits 4
words under its cap (1996 of 2000) and has moved 6 words in 8 days (1990 on
2026-09-02 per queue 013's done line; 1996 today). The wall is at the file
and the wall worked. A cap of 2979 over a file that lands at, say, 2700 would
hand back 279 words of exactly the growth the guard exists to stop. Cap equal
to landed count keeps the wall where it is today. One in, one out, and the
guard's message already says where a displaced passage goes.

**(c) The series that would argue for any other number** is the footer
series since 2026-09-02: `git log` over commit messages carrying
`CLAUDE.md N/2000 words`. The verify.py docstring said this series would
exist before anyone asked; nobody has read it. Condition 3 prints it. It
cannot argue for a higher cap; it can show whether the wall was ever hit and
how often, which is the evidence for (b).

**(d) The guard's denominator changes.** It counts CLAUDE.md plus every file
under `.claude/rules/`, and prints the file count: `rulesFiles=1` is what
"one rules file" looks like as a number. Reason: the old guard bounded one of
three loaded files and described itself as bounding the start-read cost; 983
words, 33 percent of the cost, sat outside its count. After the fold, an
empty `.claude/rules/` is what makes "one" true, and a guard that cannot see
a file appear there cannot enforce it. Tested both ways (condition 4).

**(e) Is moving 2000 to the landed count "moving a bound so red goes away"?**
No, and the docstring must say why in words: the VARIABLE changes. 2000
bounded CLAUDE.md alone. The new number bounds the set the loader reads. The
same variable with a larger number would be loosening; a bound whose
denominator is corrected to match what it claims to measure is a repair, and
it lands with the arithmetic beside it so a reader who sees 2000 become 2700
does not read growth.

**(f) Jafar's number.** The 2000 is his (09-02 record, "Deliberately not
decided"). His ruling of today is the authority for the move: ONE file
carrying 2979 words of today's start-read cannot sit under a 2000 bound
without deleting roughly a thousand words of rules, which he did not ask for.
The Producer puts one line to him in this run, with the arithmetic: "The 2000
bounded CLAUDE.md alone. One file puts today's 2979 words of start-read under
the same counter; dedup brings it down; the cap becomes the landed count, and
the file is at the wall again. Yes or no." His answer is recorded in section
10. It is not a gate on the commit; a no reverses to shape B or C.

**The three shapes**, so the fallback is named before it is needed:

- **A, ruled here.** One file: CLAUDE.md + constitution + both rules files,
  deduplicated, landed at or under 2979, cap = landed count.
- **B, fallback if A prints over 2979.** CLAUDE.md + both rules files folded;
  the constitution stays at `ledger-v2/studio-v2/constitution.md`. The 317
  new words are not paid for, so they are not taken. Start-read cannot rise
  (nothing new enters the set). Cap = landed count. Jafar told "one file" was
  not reached and by how many words.
- **C, rejected.** No fold; rename `globs:` to `paths:` so the two files
  become conditional. Rejected on three grounds: it contradicts the ruling;
  path-conditional loading is the wrong instrument for rules about a KIND of
  code that lives everywhere (ledger/CoreTests/Program.cs line 20101 cites
  instruments.md and matches none of its globs, so the rule would stop being
  read exactly where it is applied); and it is unmeasured here, since the
  only proof that conditional loading works is a spawn reporting its own
  prompt, which nobody has taken.

## 3. Question 3: the order of the combined file, and the numbers

A session reads top to bottom with finite attention, so the order is: what
cannot be invented, then what outranks, then the laws in rank order, then the
mechanics, then the index. Section-level order, with what changes:

1. **The goal block.** Unchanged, verbatim, opens the file, closed by `---`
   (goal-block-check requires both; section 0 item 6).
2. **Title and preamble.** The sentence "It was 16,291 words on 2026-09-01"
   gains "and 2979 words across three files on 2026-09-10, folded into one".
3. **What outranks this file.** Item 1 keeps "`canon.md`. World facts,
   approved by Jafar." and loses its second sentence, which is constitution
   law 3 verbatim. Item 2 loses "and the laws in constitution.md bind" and
   gains "the constitution is the next section of this file and outranks the
   rest of it". The paragraph "Two are absolute and repeated here" (lines 40
   to 45) is deleted: it repeats laws 6 and 11, and "repeated here" was only
   ever a workaround for the constitution not being in the file. Its one
   clause the constitution lacks, the 31 August date and "corrected
   opportunistically, never rewritten wholesale", survives as a note under
   law 11.
4. **Section 0, what LEDGER is.** Unchanged.
5. **The constitution.** New section, twelve laws, numbers 1 to 12 unchanged,
   text verbatim with ONE permitted edit: law 6's path
   `research/license-allowlist.md` was relative to `ledger-v2/` and resolves
   to nothing from the repo root, so it becomes
   `ledger-v2/research/license-allowlist.md`. Heading states the citation
   form: "cited as constitution law N". Placed before the standing rules
   because it outranks them, and after section 0 because the premise outranks
   everything a law can say about it.
6. **The standing laws 1 to 13.** Numbers unchanged, text unchanged, order
   unchanged. Heading gains "cited as rule N". The folded clauses sit
   immediately under their parent: 3.1 to 3.7 after rule 3 and before 3b;
   12.1 to 12.7 after rule 12 and before 13.
7. **Before you commit.** Unchanged.
8. **The studio split.** Unchanged.
9. **The standard.** Unchanged.
10. **Appendix index.** Replaces "Where the rest of this file went". Section 4
    says what it carries.

**Do the ci.md and instruments.md bullets get numbers? Yes, as clauses, and
the convention is stated in the file so it cannot drift:**

> Letters (3b, 5b) are laws of equal rank added beside a parent. Decimals
> (3.1, 12.4) are clauses under a law, carrying the specifics the law states
> in principle. A new law after 13 takes 14. A clause never becomes a law by
> renumbering, and no number is ever reused.

Why decimals and not 14 onward: the bullets are not new laws. Every one of
them either restates a law already numbered (and is deleted) or specialises
one (and becomes its clause). Why blocks under 3 and 12 rather than each
clause under its nearest principle: the two files are read as blocks by the
people who need them (an instrument author reads all of instruments.md; a CI
diagnoser reads all of ci.md), the mapping is one move rather than twenty,
and a clause moved later to a better parent would change its number, which
is the one thing this section exists to prevent. Rule 3 is THE instrument
rule; rule 12 is THE channel rule. The choice is recorded so a later session
does not re-derive it.

The two citation series coexist today and both survive: "rule N" is
CLAUDE.md's, "constitution law N" is the constitution's (tools/docs-check.py
line 25 uses it). Section headings carry the form. Nothing is renumbered to
merge them.

## 4. Question 4: the appendix, as a loading mechanism

A heading does not make a file unread. The mechanism, stated positively from
the documentation and this session's observation:

> A file is read at session start if it is CLAUDE.md, or sits under
> `.claude/rules/` (any file without a `paths:` key, which includes a file
> with a `globs:` key), or is `@`-imported from one of those. A file that is
> none of the three is not read at start. That is the whole mechanism.

The casebooks at `ledger-v2/studio-v2/casebook-*.md` are none of the three
today, and none arrived in this session's prompt. **They are already the
appendix no session reads at start.** The ruling therefore does not move
them:

- Moving gains nothing in loading.
- It costs a rewrite across 55 `casebook` citations in 23 files and the 23
  `moved verbatim from CLAUDE.md` markers in 8 files that the 09-02 ruling
  placed, for no change in what a session reads.
- The defect in the appendix is not where it is but that nothing checks its
  pointers (queue 020, closed unbuilt on 2026-09-10). That is the next rung,
  named in section 9.

"Appendix" is the name of the index section at the bottom of the one rules
file. It lists, by rule number as today, what each casebook and framework
document carries; drops the two `.claude/rules/` pointers, which point at
nothing after the fold; adds the constitution's old path as a moved-from; and
carries the mechanism sentence above in one line, so the next session cannot
repeat the 09-02 mistake of believing a header. The sentence costs about
forty words and prevents the exact error that produced this ruling.

Proof, not prose: condition 12 is the next director spawn after the commit
reporting which "Contents of" blocks its own prompt carried. Exactly one
project-instructions block, CLAUDE.md, is what "one rules file" means to the
loader. That is the same instrument that detected the three today.

## 5. Question 5: the false sentence

`.claude/rules/instruments.md` lines 8 to 10: "Loaded when editing
measurement code". False: it loaded in this session, in which no measurement
code was opened before the prompt was built. Cause, per section 0 items 2 and
3: the frontmatter key is `globs:`; the loader's key is `paths:`; a file
without `paths:` loads unconditionally. `ci.md` carries the same `globs:`
frontmatter and the same implied claim in its `description:` line, without a
prose sentence.

What happens to it:

1. **In shape A or B, both files are deleted in the fold commit** and the
   sentence dies with the file. The record of WHY it was false is this
   section, not a comment in a file that no longer exists.
2. **If the fold does not land in the batch this ruling covers**, the sentence
   is corrected on sight as a one-line fix the resident may hand-apply,
   exact text in section 7 (c). A rules file that misstates its own loading
   is a live defect whatever else happens.
3. **The `globs:` key is NOT renamed to `paths:` as a side effect, in either
   case.** That would silently make a rule every session reads into a rule
   some sessions read, a change in the read set that needs its own
   measurement (a spawn reporting its prompt), and it is shape C, rejected.
4. **The 09-02 record is corrected** (section 7 (a)), because a decision
   record that declines an option "the way it loads instruments.md" teaches
   the next reader the false mechanism.

## 6. The fold, clause by clause

Every line of both rules files is accounted for here. D = deleted as a
duplicate of a numbered law (the words saved are measured in condition 2, not
estimated here). Incidents named in a deleted or folded line must be shown
present in the named casebook (condition 8); a pointer to a casebook that
does not carry the passage is the hazard queue 013 named.

**instruments.md, eleven bullets, to rule 3:**

| source | fate | text carried |
|---|---|---|
| bullet 1, statistic OF | **3.1** | say what the number is a statistic of (peak, median, last-wins, cumulative, at-worst) in the name or the comment beside the emit. The most-cited bullet ("first bullet of instruments.md" in three records), so it keeps the first position |
| bullet 2, zero ships denominator | D (3b) | 3b says it in full |
| bullets 3, 4, 5: cap token, no spaces, done line vs sample line | **3.2** | one format clause: values carry no spaces (use `/` and `..`); a cap announces itself as `(+N more not shown)`; whole-run numbers on the done line, per-sample on the sample line, never both under one key, never one pair across lines a grep will merge |
| bullet 6, xAtWorst | **3.3** | a numerator's denominator is captured at the instant the numerator peaks, and named so |
| bullet 7, new bound needs a printed series | D (2) | rule 2's first two sentences |
| bullet 8, arithmetic lives where the tests run | **3.4** | ruled a standing rule 25 Aug; the unrun formatter is the silent-instrument failure |
| bullet 9, placement metric in two halves | **3.5** | distance to the datum and whether the datum exists; breakdown per the axis placement varies on, never per camera; the eight blocks over open sea |
| bullet 10, selftest ships with the tool | **3.6** | accepting case first; the live codebase is the accepting fixture, the rejecting fixture synthetic, so doing the work can never break the tool |
| bullet 11, two numbers | **3.7** | before concluding from two numbers, read the code that produces them and ask whether either can move while the other stands still. The repeated conclusion ("one number twice") stays in rule 2 only |
| frontmatter, heading sentence, footer | D | the footer's casebook pointer moves to the appendix index |

**ci.md, nine bullets, to rule 12:**

| source | fate | text carried |
|---|---|---|
| bullet 1, silent: run the entry point | **12.1** | when something is silent, run the existing entry point and read its output before proposing a mechanism; THE ENTRY POINT IS CHEAPER THAN THE ARGUMENT. Ruled by Jafar 2026-09-08. The Telegram incident (four refuted explanations, the fifth guess, four receipts of sixteen) moves verbatim to casebook-build-and-evidence.md with a marker |
| bullet 2, the committed file's shape | **12.2** | a `key=value` verdict naming its commit on line 1, per-run copies keyed by short sha; log tails, step summaries and artifact hosts have all failed, a committed file has not. Rule 12's body already names the channel; this is its shape |
| bullet 3, effects not exit code | **12.3** | jobs have reported success while deleting content, pushing nothing, truncating their own logs |
| bullet 4, NO RUN | **12.4** | a run that measured nothing says so and never carries the previous run's files forward under its own name |
| bullet 5, stage by name | **12.5** | never `git add <directory>` |
| bullet 6, watch by ancestry | **12.6** | capture the sha before dispatching; dispatch takes a branch |
| bullet 7, expensive jobs opt-in | D (9) | rule 9 verbatim. No edit to rule 9's text; `workflow_dispatch` is in the casebook |
| bullet 8, batch per dispatch | **12.7** | the round trip costs the same carrying one change or six; respect the stated concurrency limit, because seats and shared runners fail silently in the only channel you can read |
| bullet 9, cap in a log step | D (3b) | 3b's last sentence; the `head -N` incident shown present in casebook-build-and-evidence.md |
| frontmatter, footer | D | as above |

**constitution.md, fourteen lines:** title becomes the section heading; laws 1
to 12 verbatim; law 6's path made root-relative (section 3, item 5); a note
under law 11 carrying the 31 August date clause from CLAUDE.md lines 43 to 45.
A three-line pointer stays at the old path (section 7 (b)), because 26
citations in 18 files name it and a pointer outside the loader's three paths
costs no session a word.

**Em-dashes.** Both rules files carry them (ci.md lines 21, 32, 41, 45;
instruments.md lines 12, 17, 25, 32). Text written into the one file on
2026-09-10 falls under the formatting law; they become colons or full stops
in the fold. Condition 9 prints the count.

**Citations.** The 79 citations of the two paths split by surface. LIVE
surfaces are rewritten to the clause number ("CLAUDE.md rule 3.4", "rule
12.6"): code comments and docstrings (ue-probe, tools, ledger/verify.py,
CoreTests, StreetVignettePlacement.cs), the three workflows, the two casebook
headers, CLAUDE.md itself, `production/NOW.md`, `production/watchdog-prompt.md`,
`production/decision-queue.md`, the open queue cards and the one spec JSON.
Dated records (`game-design/decision-*`, `game-design/agent-reports/*`,
`production/findings.txt`, `production/art/*/DELIVERY.md`, `legacy/`) are
LOG: they cite a path that existed on their day and are not rewritten.
Condition 7 prints the before and after counts and lists every surviving hit.

## 7. Dictated texts

Apply verbatim.

**(a) Append to
`game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md`,
under a heading `## CORRECTION 2026-09-10`:**

> CORRECTION 2026-09-10. The bullet under "Deliberately not decided" that
> reads "the way it loads `instruments.md`" rests on a premise that was
> false when written. `.claude/rules/instruments.md` and `ci.md` were loaded
> into every session unconditionally: their frontmatter key was `globs:`, the
> loader's key is `paths:`, and a rules file without `paths:` loads like
> CLAUDE.md. Measured by the director spawned 2026-09-10T12:06:47Z reading
> its own prompt, which carried both files in full. The option this bullet
> declined was therefore never on offer in the form described. Ruled in
> `decision-2026-09-10-ruling-the-one-rules-file.md`.

**(b) The pointer left at `ledger-v2/studio-v2/constitution.md` after the
move (shape A only):**

> # Studio v2 Constitution: moved
>
> The twelve laws moved verbatim into CLAUDE.md, section "The constitution",
> on 2026-09-10 (ruling `game-design/decision-2026-09-10-ruling-the-one-rules-file.md`).
> Cite them as "constitution law N". Nothing was renumbered.

**(c) If the fold does not land in this batch, replace lines 8 to 10 of
`.claude/rules/instruments.md` with:**

> Loaded in EVERY session, whatever the frontmatter above says: its `globs:`
> key is not the loader's key and has never gated anything (ruling
> 2026-09-10). Instrument faults are the quietest class there is: a broken
> feature shows; a broken instrument shows you the wrong world.

**(d) The mechanism line for the appendix index section of the one file:**

> Nothing below is read at session start. The mechanism is location, not a
> heading: a file is read at start if it is CLAUDE.md, or sits under
> `.claude/rules/` (a `globs:` key does not gate it), or is `@`-imported from
> one of those; these files are none of the three. Proven by a director
> reading its own prompt, 2026-09-10.

## 8. Conditions the resident must PRINT before the commit

All printable, none requiring judgement. A number that differs from this
ruling blocks the commit until the difference is written into section 10.

1. `wc -w` on the four files BEFORE the fold, pasted: CLAUDE.md,
   constitution.md, ci.md, instruments.md. Expected 1996, 317, 497, 486.
   If any differs, recompute 3296 and 2979 from the printed numbers and
   write both into section 10; the ceiling is the recomputed 2979.
2. The deduplicated draft's count by verify.py's own counter
   (`python3 -c` over `len(open(p).read().split())` or `claude_md_size(path)`)
   AND `wc -w` beside it. Print `landed=N`, `foldDedup=3296-N`,
   `startReadDelta=N-2979`. Accept shape A only if `startReadDelta` is zero
   or negative; otherwise shape B, same ceiling, and the Producer's line to
   Jafar says so with the number.
3. The footer series: `git log --format=%s%n%b | grep -o 'CLAUDE.md [0-9]*/2000 words'`
   or the equivalent over `ledger/.verify-footer` history, pasted in full
   with its count of entries. This is the series the docstring promised.
4. `CLAUDE_MD_WORDS` set to the landed count in the same commit; the
   docstring rewritten to carry the arithmetic of section 2 (what 2000
   bounded, what N bounds, why the variable changed); the footer line
   printing `CLAUDE.md N/N words rulesFiles=1 rulesDirFiles=0`. Then both
   halves of rule 5b: the live tree green; a planted one-word file under
   `.claude/rules/` red with `rulesDirFiles=1` in the message; removed,
   green again. Paste all three lines.
5. `python3 tools/goal-block-check.py` green, and `--selftest` green.
6. `python3 tools/docs-check.py` green, this file counted among the LOG
   documents.
7. Citation sweep. `rg -c '\.claude/rules/(ci|instruments)\.md'` before
   (expected 79 in 54) and after; every surviving hit listed by path, and
   every listed path either a dated record under `game-design/`, a
   `game-design/agent-reports/` file, `production/findings.txt`, a
   `DELIVERY.md`, or under `legacy/`. Any other survivor is a live surface
   missed. Same for `studio-v2/constitution\.md` (expected 26 in 18), live
   surfaces rewritten to "CLAUDE.md, the constitution, law N".
8. Destination check for every incident named in a deleted or folded line
   (section 6): the Telegram 2026-09-08 incident and the `head -N` incident,
   each shown present in `ledger-v2/studio-v2/casebook-build-and-evidence.md`
   by a pasted grep hit carrying a `moved verbatim` marker; per-file marker
   counts printed for every path the appendix index names. A destination
   with zero markers blocks the commit.
9. Formatting law on the landed file: `rg -c '\x{2014}' CLAUDE.md` printing
   0 beside `wc -l`, and a grep for single-asterisk or underscore italics
   printing 0 beside the same line count. Zero with its denominator, or it
   cannot tell nothing from fine.
10. `ls -la .claude/rules/` pasted: absent or empty.
11. Rule 6 sweep of the clause numbers: `rg -n 'rule (3\.[1-7]|12\.[1-7])'`
    after the rewrite, count pasted, so the new ids are shown to be cited
    and not merely assigned.
12. POST-COMMIT, recorded in section 10 by the first director spawned after
    the landing: the list of "Contents of ..." project-instruction blocks in
    its own prompt. Expected: exactly one, CLAUDE.md. Two or more means the
    loader reads something this ruling does not know about, and that is a
    finding, not a formatting question.
13. The cadence gate's numbers pasted: rulingStamps, rulingFresh,
    rulingStale, rulingUnmatched. This stamp must land FRESH.
14. The Producer's one line to Jafar (section 2 (f)) sent and answered in the
    same run, his words pasted into section 10.

## 9. Quality ladder at close

Best available, or first working? The fold as ruled is the first working
result. The rungs above it, named so they are tasks and not a blank:

- **The pointer check** (queue 020, closed unbuilt 2026-09-10). The appendix
  index is a list of paths with claims about what each carries, and nothing
  verifies the claim. Re-queue under its own name, acceptance as 020 wrote
  it, now reading the appendix index rather than "Where the rest went".
- **The loader measurement as a standing check.** Condition 12 is a
  one-time reading. The rung above it is every director spawn printing the
  count of instruction blocks in its prompt as one line, so a second rules
  file cannot appear unread for a week.
- **The rule-held test**, from the 09-02 ladder and still blank: a session
  that breaks a rule and can be shown to have read it. Research task; no
  mechanism named yet.

## 10. Landing

Filled by the resident with printed numbers. Empty until then.

- Condition 1 counts:
- Condition 2: landed=, foldDedup=, startReadDelta=, shape taken:
- Condition 3 series (entries, min, max):
- Condition 4 three lines:
- Condition 7 before/after and survivors:
- Condition 8 marker counts per destination:
- Condition 9 zeros with denominators:
- Condition 12, next director's block list:
- Condition 13 cadence numbers:
- Condition 14, Jafar's words:

Sources read this session for the loading mechanism:
[How Claude remembers your project](https://code.claude.com/docs/en/memory),
mirrored at [docs.claude.com](https://docs.claude.com/en/docs/claude-code/memory)
and [docs.anthropic.com](https://docs.anthropic.com/en/docs/claude-code/memory).
