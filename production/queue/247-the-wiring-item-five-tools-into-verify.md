# 247. THE WIRING ITEM: six gate-class tools into verify.py, plus the baseline compare

STATUS: BLOCKED, 2026-09-10, behind the D18 batch and the rules-file fold.
Filed under the close-out ruling of 2026-09-10, section 7. It edits
`ledger/verify.py`, so it runs under its OWN ruling and not on a resident's
read.

## The finding

Five gate-class tools have zero readers in any `.py`, `.sh`, `.yml` or `.ps1`,
and zero hits in `ledger/verify.py`. They are written, they are tested, and
nothing runs them:

`tools/goal-block-check.py`, `tools/brand-verify.py`,
`tools/dialogue-verify.py`, `tools/blocking-count.py`, `tools/brief-sheet.py`.

A SIXTH was named separately by the lane that built the D18 gate:
`tools/canon-gate.py`, unwired before that lane arrived. It is a live,
working gate: run by hand over `content/brands/brand-bible-v1.json` it reports
`clean, 0 finding(s) in 1 file(s), 130 line(s) examined, 13 era term(s) and 45
brand token(s) screened`, and its selftest passes 11 of 11. It screens for real
trade marks and era violations, which is the one gate whose failure ships a
legal problem rather than an aesthetic one, and nothing runs it.

That is rule 6 exactly: built is not running. It was found by a sweep of all
147 tracked tools that counted both filename readers and `import <stem>`
readers, the second because a Python import never writes the `.py` and a first
pass without it produced a wrong answer.

The sharpest one is the first. `CLAUDE.md:227` said `tools/goal-block-check.py`
"proves the goal block still matches" and nothing ran it, so the sentence
described a guard that never fires. It stood in TWO live places; the newer copy
in `production/ladder.md` was corrected in the batch that filed this item, and
`CLAUDE.md:227` is corrected by the fold rather than by a second edit to the
file every session reads.

## Why it was not done at the time

Jafar's instruction for that batch was "no studio building until it lands".
Wiring five gates into verify is studio building. Held deliberately, filed here
so it is not lost.

## Done looks like

Each of the five registered in `ledger/verify.py`'s check tuple, and for each,
BOTH outcomes watched, accepting case first, per rule 5b:

- a real run of the live tree that PASSES, since the live codebase is the
  accepting fixture for a tool that checks the project itself;
- a rejecting run with a synthetic fixture, never by loosening the bound;
- a done line whose every zero carries its denominator, and the words
  "nothing measured" where a tool did not run at all.

Plus THE BASELINE COMPARE from the close-out ruling section 4: a check that
`tools/content-gate.py`'s `BASELINE` is strictly smaller than it was at the
previous commit, so the baseline can shrink and cannot grow without a ruling.

## Risk

Five gates that have never run will find things. Expect the first wired run to
be red, and expect the redness to be real work rather than a wiring bug: check
which it is by running each tool by hand first and reading its output, before
concluding anything about verify.
