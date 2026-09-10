# 248. THE IMAGE PASS: somebody opens every image and records what is in it

STATUS: READY, 2026-09-10. Filed under the close-out ruling of 2026-09-10,
section 10, as the named next rung above first working.

## Why this exists

D18 in images is enforced AT THE PROMPT AND NOWHERE AFTER IT.
`tools/imagegen/imagegen.py`'s `validate_spec` reads the words sent to the
model; nothing reads what came back. The content gate says so itself, at
`content-gate.py` 1392 to 1396: "No word gate can see that. Somebody opens the
file."

The batch that filed this item is the proof. It knew of ONE rendered copy of
the outside Fairview comparison and there were TWO, found by a glob and a look
rather than by any instrument. A second copy carrying children sat in the tree
while every gate read green.

## Done looks like

Open every image file under the gallery's own sources, which are
`gallery.py:151`: `production/d1-probe`, `production/frames`,
`game-design/sim-shots`, `production/art`. The compare boards under
`production/art/compare/` are IN SCOPE and are the likeliest carriers, because
they embed outside sheets.

For each file record, as yes or no: children, drink, gambling, slur text.

Print `imagesExamined=N` FRESH. Do not reuse the gallery's count of 72 from
2026-09-10: its own comment says it decays, and a denominator copied from
another run is the fault this project keeps catching.

A file that could not be opened prints the words "nothing measured" and is
named. A zero ships its denominator: "0 with children of N examined", never a
bare 0.

## Dependencies and risk

None. It is manual by construction until queue 249 answers whether a machine
can do it.

Risk: it is long and boring, which is exactly why it has never been done, and
why the one instrument that could have caught the second Fairview copy was a
person looking.
