# 244. The content gate's denominator excludes the branch that feeds the art pipeline

STATUS: READY, 2026-09-10. Found by the resident checking a "nothing measured"
line in the D18 gate's own report, per rule 3: suspect the instrument first.

## What the gate reported, and what is actually true

`tools/content-gate.py` landed clean: `hitsNew=0 hitsBaselined=197
stringsScanned=9780 filesOpened=32 declaredAbsent=2`. The two declaredAbsent
entries are `production/art/atlas-01/data/atlas.json` and
`production/art/atlas-01/DISTRICTS.md`, reported as not in the tree and not
tracked by git, with `stringsExamined=0`.

Both statements are true of THIS BRANCH and the conclusion drawn from them is
wrong. The files are not missing. They live on `origin/art/atlas-01`, and
`tools/imagegen/sheet-furniture.py:49` reads one of them there ON PURPOSE:

    ATLAS_BLOB = "origin/art/atlas-01:production/art/atlas-01/data/atlas.json"

Verified: `git cat-file -s` returns 36819 bytes for the atlas and 5650 for
DISTRICTS.md on that branch, and line 13 of DISTRICTS.md carries word for word
the sentence the Fairview delivery quotes as its provenance. The provenance
citation is honest. The gate simply cannot reach it.

## Why that is worse than a missing file, not better

The atlas is not inert reference. It is INPUT to the sheet generator. So content
flows from a branch the gate never scans into pictures the gate is supposed to
govern, and the gate reports clean the whole time.

What is actually sitting on that branch, unscanned, found by grepping the blob
directly:

- `DISTRICTS.md:10`, Copper Row: "Independent food/hardware shops, stalls,
  barber and BOOKMAKER". A bookmaker is a betting shop. D17 and D18 remove
  gambling entirely. `tools/content-gate.py` catches the token `bookmaker` in
  the working tree and would have caught this one.
- `DISTRICTS.md:13`, Fairview: "washing court, SCHOOL and bus".
- `DISTRICTS.md:51`: "The SCHOOL CHAPEL and steps are the named landmark".

D18 says the school stands closed for the game's window, the building there and
nobody in it, so a school as a named landmark is not automatically a violation.
A bookmaker is.

## The general shape, which is the point of this item

The gate's denominator is the working tree of one branch. The project has 6
remote branches, and at least one of them holds authored content that feeds
generation. A zero over 9780 strings reads as "the project is clean" and means
"one branch of six is clean". That is rule 3b exactly: the denominator counted
less than the set the conclusion covers.

## Done looks like

`tools/content-gate.py` scans content-bearing branches, not only the checkout,
by reading blobs with `git show` the same way `sheet-furniture.py` already does.
Specifically:

- a named list of content-bearing refs, with the reason each is on the list, so
  the set is auditable and does not silently grow or shrink;
- the done line prints `branchesScanned=N/M` and names any ref it could not
  read, in words, rather than reporting a smaller clean number;
- `declaredAbsent` keeps existing but changes meaning: it fires only when a
  path is absent from EVERY scanned ref, which is the condition that actually
  warrants the words "nothing measured";
- the accepting case first, per rule 5b: a run over the live refs; and a
  rejecting fixture that plants a banned token on a scratch ref and proves the
  cross-branch read fires, because a cross-branch scanner that silently reads
  nothing looks exactly like a clean project.

Then the `bookmaker` row is fixed on the art branch and Copper Row gets a
different trade, which is a one-word change with no art consequence: the sheet
for Copper Row has not been drawn yet.

## Dependencies and risk

Depends on queue 243 only in ordering, since both edit the same tool's report.
Risk if ignored: the next district sheet is generated from a row naming a
betting shop, and the picture is drawn, judged and shipped before anybody reads
the atlas by hand.

## A second example, found after this item was written

The same unscanned file, `DISTRICTS.md:12`, describes the Parade as "Cinema,
drink trade, taxi calls, occasional contemporary cafe/wine-bar refits". Both
"drink trade" and "wine-bar" are tokens the gate catches in the working tree,
and both feed the sheet generator from a branch it never reads. So the hole is
not a single stale row: it is the district table itself, which is the top of the
funnel for every district sheet still to be drawn.

## THE HARD GATE, ruled 2026-09-10 at the close-out

Until this item lands: NO `tools/imagegen/sheet-furniture.py` RUN AND NO
IMAGEGEN DISPATCH THAT READS `ATLAS_BLOB`. Gates, not pauses: art work that
does not read the atlas is unaffected and proceeds.

The reason is not caution. The leak already happened once and is rendered into
a picture that is in the tree today: the SCHOOL SATCHEL caption on our own half
of `fairview_theirs_vs_ours_finished.jpg` was composited from the atlas, and
queue 242 section 4 carries the detail. Atlas strings reach rendered sheets
through the compositor, so an unscanned atlas is not a documentation problem.

## The only conclusion sentence this gate's clean run permits

Ruled at the close-out, to be used in the commit message and anywhere else the
result is stated:

    content-gate clean over THIS BRANCH'S WORKING TREE: hitsNew=0 over
    stringsScanned=9780 in filesOpened=32. origin/art/atlas-01, which
    tools/imagegen/sheet-furniture.py:49 reads on purpose, is unscanned; a
    grep of the blob found one hit (DISTRICTS.md:10 "bookmaker"); the
    87-rule scan has not run over it: nothing measured. Queue/244.

The gate itself was honest at the line: it prints `declaredAbsent=2` with
`stringsExamined=0` on each, which is "nothing measured" said correctly. What
was wrong was the sentence a reader would build on top of it.
