# 242. Two checks on the Fairview sheets: the outside sheet's children, and our own grey wheelie bin

STATUS: READY, 2026-09-10. Found by the resident opening
`game-design/sim-shots/fairview_theirs_vs_ours.jpg` to verify a claim the D18
record makes, per rule 4. One finding confirms the record, one is new.

## 1. The D18 claim is confirmed, and it is larger than the record says

`ledger-v2/respec/decision-register/D18-content-rule.md` names, as the
immediate cost of the no-children rule, that the outside Fairview sheet has two
children on the steps and a FAIRVIEW SCHOOL sign. Opened and confirmed, with
more than the record lists. On the OUTSIDE panel, left half of the comparison:

- a FAIRVIEW SCHOOL sign on the gate post, legible, in BOTH of its two views;
- figures reading as children in school uniform in both views, not one;
- a swatch in the material strip captioned SCHOOL SATCHEL.

OUR OWN sheet, the right half, has no children and no school sign: two adults
walking in the lower view, none in the upper, and no nameplate. But it is NOT
fully compliant, and the first version of this item said it was. See the
correction in section 4.

So the remediation is confined to the outside artifact, which Jafar had already
retired from production on 2026-09-10 for a different reason. It is not work on
our own art.

## 2. What has to be decided, and by whom

D18 says no children anywhere, none rendered. The outside sheet is not being
produced any more, but it is a rendered image sitting in
`game-design/sim-shots/`, which is the evidence channel Jafar looks at.

DO NOT SIMPLY MOVE IT, BUT NOT FOR THE REASON THIS ITEM FIRST GAVE. See the
correction in section 4: the denominator objection is real, and it is about
`game-design/sim-shots/runs/`, not the top level where these two files live.

The decision needed is whether D18's no-children rule reaches a retired
comparison image from an outside account that exists only as the record of a
decision already taken. Director call, and it should be taken with the D18
enforcement ruling rather than alone.

## 3. The new finding: a grey wheelie bin in our own sheet

Our own second panel has a grey wheelie bin at the kerb, and the outside sheet
uses metal dustbins and milk bottles on the doorstep instead.

THIS IS A QUESTION, NOT A CLAIM. I could not check it: this container's egress
proxy blocks the sources that would date British wheeled-bin rollout, and the
project's own research folder returns nothing on refuse collection. So the
period accuracy of a wheelie bin in a working port town between 1988 and 1992
is UNKNOWN here and is not asserted either way.

Why it is worth an item anyway: the premise is LATE-ANALOG and the drift this
project keeps catching runs in one direction, toward the 1950s and 1970s. This
would be the first drift caught running the OTHER way, toward too modern, and
that direction has no guard at all. A single object that reads as 1996 in a
1990 street is exactly the kind of thing a player who loves KCD2 notices
without being able to say why.

## Done looks like

Someone with a source dates the UK rollout of domestic wheeled bins, writes one
line into `canon.md` fixing what Meridian's streets put their rubbish in, and
either the bin stays with that line as its warrant or the sheet is regenerated
with what the line says. The same line then belongs in the image spec content
clause, so no future prompt has to guess.

## Dependencies and risk

Depends on a source this container cannot reach, so it is a question for Jafar
or for a session with egress. Risk if ignored: low individually, and this is
the class of detail that decides Meridian Test condition 1, so it is filed
rather than dropped.


## 4. What this item got wrong, corrected 2026-09-10 by the close-out ruling

Two claims above were refuted by measurement. Both are corrected at their own
sites and not only here, because a correction filed at the bottom of a document
is a correction the next reader does not reach.

FIRST, THE DENOMINATOR OBJECTION WAS CITED OUT OF SCOPE. `tools/gates.py:40`
defines `RUNS = ROOT / "game-design" / "sim-shots" / "runs"`, and all four cited
lines, 212, 1065, 1218 and 1551, read `RUNS`. `build-dashboard.py:116` says in
its own comment that its 358 files are every kept run in
`game-design/sim-shots/runs/`. NEITHER READS THE TOP LEVEL. Two tools do:
`tools/glance.py:62` and `tools/gallery.py:151`, and both PRINT their counts, so
a move there would be visible rather than silent. The objection stands for
`runs/` and does not reach these two files. Correcting it matters: left as
written, the next reader treats the whole directory as untouchable.

SECOND, THERE ARE TWO COPIES AND OUR HALF IS NOT CLEAN. The comparison exists
twice: `game-design/sim-shots/fairview_theirs_vs_ours.jpg` and
`production/art/concept-fairview-2026-09-10/sheets/fairview_theirs_vs_ours_finished.jpg`.
Both carried the children and the nameplates on the outside half. The `_finished`
copy additionally carries a SCHOOL SATCHEL caption on OUR half, composited from
the atlas: that is queue 244's cross-branch leak, already rendered into a picture
once. It is a baselined hit at six sites and its fix is the furniture data under
queue 243 followed by a re-composite once 244 lands. The crop did not fix it and
was never meant to. Bare "school" in a street name passes by the gate's own rule
and by D18, which says the building stands and nobody is in it.

## 5. What was done, with the numbers

Both files are cropped IN PLACE to our half, same path, re-encoded once, under
the close-out ruling. Rule 5 applies and the originals are preserved where the
pipeline cannot reach them:

    original, with the outside half, is blob fd5361f12913b9582f1c3403ededb58c870734f2 in history
      for game-design/sim-shots/fairview_theirs_vs_ours.jpg
    original, with the outside half, is blob 2d657c105be2b17b7dcbfd01b35229e3572e9612 in history
      for production/art/concept-fairview-2026-09-10/sheets/fairview_theirs_vs_ours_finished.jpg

THE MIDLINE WAS THE WRONG CUT AND THE PICTURE SAID SO. Cropping at `w//2` left a
visible strip of the outside panel down the left edge of the `_finished` copy.
The gutter was then MEASURED rather than guessed, by finding the columns that are
near-black down the full height of the image:

    game-design/.../fairview_theirs_vs_ours.jpg          gutter=614..623   midline=621  offBy=-7
    production/.../fairview_theirs_vs_ours_finished.jpg  gutter=1016..1029 midline=993  offBy=+23

    cropped game-design/sim-shots/fairview_theirs_vs_ours.jpg before=1242x962 after=628x962
    cropped production/art/concept-fairview-2026-09-10/sheets/fairview_theirs_vs_ours_finished.jpg before=1987x1568 after=971x1568

Both results were OPENED afterwards, not inferred from the arithmetic. Each
header reads OURS, each lower view has two adult figures and the upper has none,
neither has a FAIRVIEW SCHOOL nameplate, and neither has a figure of child
height. The `SCHOOL SATCHEL` swatch caption is still on the `_finished` copy,
exactly as section 4 says it would be.
