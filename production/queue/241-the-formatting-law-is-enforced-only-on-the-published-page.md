# 241. The formatting law is enforced only on the published page, not where text is written

STATUS: READY, 2026-09-10. Found by the resident while reviewing the cleanup
batch for commit, not looked for.

## What is true

The formatting law is absolute: no em-dashes and no italic text in anything
written from 31 August on. It is one of the two laws CLAUDE.md repeats.

The enforcement is `check_formatting` in `tools/map.py`, which has a real
both-outcome selftest at `tools/map.py:7158` that bites on an em-dash and on an
italic. `tools/docs-check.py` separately refuses the retired em-dash STATUS
banner across all 172 documents under `game-design/`.

Neither reaches a source file. `check_formatting` runs on what the map and the
glance PUBLISH, and `docs-check` looks at the banner line. So an em-dash written
into a Python string, a C# string, a JSON data field or a code comment is
written, committed and never seen.

## The measurement

Over the uncommitted cleanup batch of 2026-09-10: 36 added lines carry an
em-dash, out of 3638 added lines in tracked modifications. The new untracked
files are clean, 0 of them.

Where the 36 sit:

- `ledger/CoreTests/Program.cs`, 1 line, inside a `Console.WriteLine` that
  prints a test heading a human reads.
- `tools/imagegen/prompts.json`, most of the rest, in `binds_to` fields and in
  the commentary beside them.
- A handful in prose added to the same file today.

## Why it matters more than tidiness

The law exists because an em-dash is a tell: it is how a reader knows a
paragraph was written by a machine that was not watching itself. A law enforced
at the published page and nowhere else means every source file drifts, and the
drift arrives at the page later through any string the page quotes. `map.py:809`
already records exactly that happening: a simulation verdict carried an em-dash
and quoting it would have reddened the page.

## Done looks like

A check, run by `ledger/verify.py`, that refuses an em-dash in any line ADDED
relative to the last commit, across the tracked tree, with:

- the accepting case first, per rule 5b: a real run of the live tree that passes
  once the existing 36 are dealt with;
- a rejecting fixture that is synthetic, a planted em-dash in a scratch file;
- a denominator on every zero: "0 em-dash line(s) of N added line(s) examined",
  and the words "nothing measured" when there is no diff to read;
- a cap that announces itself when it bites, per the instrument rules.

It must check ADDED lines, not the whole tree. Older text is corrected
opportunistically and never rewritten wholesale, and a whole-tree check would
demand the wholesale rewrite the law forbids.

## Dependencies and risk

Depends on nothing. The risk is the one this queue item is itself an example of:
a new gate that goes red on 36 pre-existing lines blocks every commit until
somebody fixes text that is not what they were working on. So the gate ships
with those 36 as a named, dated baseline inside the tool, with a comment saying
the baseline is to be emptied and never grown.
