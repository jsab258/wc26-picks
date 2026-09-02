line: production (asset pipeline)
spec: production/specs/vignette-bill-of-materials.json
acceptance: a director ruling naming step 4's true scope; step 4a's 7 image lines either dispatched to the PC channel or refused with a stated reason; the 26 PROC lines placed on their merits rather than costed as overnight work
max_sessions: 1
done: 2026-09-02 by director ruling game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md. Ruled FOLD (Ruling 5): the 26 PROC lines belong to the D1b shared scene generator, which must exist anyway. Step 4 is the seven 2D lines, now queue 025. The runnable-tonight claim is withdrawn.
status: READY 2026-09-01. Blocked on a DECISION, not on work: the resident must not re-cost a ruled step alone.

Written 2026-09-01 by the resident, from the landed BOM. It needs a
director ruling before step 4 is dispatched, because it changes what
step 4 IS, not merely how big it is.

## The finding

The ruled sequence (game-design/decision-2026-09-01-production-prep-sequence.md,
Ruling 2 step 4) calls step 4 "First full BOM batch overnight, mechanical
gates only", costed at "near zero Claude (generate the spec from the BOM,
dispatch, read results next session)".

Read against the BOM that has since landed, that costing holds for a
minority of the work and is wrong for the majority.

`production/specs/vignette-bill-of-materials.json`, 77 items:

    GENERATE 33   HAVE 32   FETCH 5   ENGINE 6   BLOCKED 1

and the 33 GENERATE lines split by `make_by`:

    PROC 26   2D 7

Only the 7 `2D` lines are image generation, and only those are the free
overnight work the ruling costed at near zero Claude:

    A5_double_yellow_lines   MANDATORY   double yellow line pair
    A9_puddle_mask           MANDATORY   where standing water sits
    C11_lit_interior_card    MANDATORY   what a lit window shows at night
    E10_street_name_plate    MANDATORY   canon street name plate
    B4_gutter_water          DRESSING    gutter water decal strip
    C12_net_curtain          DRESSING    net curtain or blind
    G7_graffiti_tags         DRESSING    period tags, in-world crews

The other 26 are `PROC`: kerbstone runs, gully recesses, ground planes,
emitted by the scene generator from the shared JSON. That is CODE. It is
Claude-priced builder work and no amount of overnight GPU time produces
any of it.

## Why this needs a ruling and not just a resident edit

Step 4 was placed in the sequence as the cheap step that compounds step 3.
If 26 of its 33 lines are builder sessions, its position and its cost are
both open questions, and the resident should not re-cost a ruled step
alone. Two candidate shapes, for the director to choose between or reject:

- SPLIT: step 4a is the 7 images, genuinely near-zero Claude, dispatch as
  soon as the PC channel is live. Step 4b is the procedural generator,
  costed honestly as builder sessions and placed on its merits.
- FOLD: the 26 PROC lines are not step 4 at all but part of the D1b shared
  scene generator, which already has to exist for the engine comparison,
  and step 4 shrinks to the 7 images plus the 5 fetches.

The second looks right from here and is exactly the kind of read a
resident should not ratify on its own.

## The number that must not be carried forward

The overnight capacity arithmetic measured earlier this week, roughly 6.4
seconds per material and about 4,500 a night, with disk as the binding
constraint at about 200 GB at 4K against 90.7 GB free, was measured for a
BULK MATERIAL LIBRARY. It does not describe this scene. Seven images is
minutes, and disk does not bind at all. The resident wrote that arithmetic
into `production/NOW.md` against step 4 before reading the BOM split and
corrected it in the same session; it is recorded here so the next reader
does not re-derive it from the older note.

## Done looks like

A director ruling that names step 4's true scope, and either a dispatched
7-image request or a stated reason it waits.
