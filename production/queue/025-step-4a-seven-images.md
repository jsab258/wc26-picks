line: production (asset pipeline)
spec: production/specs/vignette-bill-of-materials.json, and decision-2026-09-02-constitution-cut-attribution-pc-channel.md Ruling 5
acceptance: seven files on disk, each attributed by the run that wrote it, none blank, review state recorded
max_sessions: 1
status: READY 2026-09-02. One content-wrangler. This IS step 4, folded: the 26 PROC lines went to the D1b scene generator, which has to exist anyway.

The seven 2D lines of the bill of materials, and nothing else:

    A5_double_yellow_lines   MANDATORY
    A9_puddle_mask           MANDATORY
    C11_lit_interior_card    MANDATORY
    E10_street_name_plate    MANDATORY
    B4_gutter_water          DRESSING
    C12_net_curtain          DRESSING
    G7_graffiti_tags         DRESSING

FOR EACH ONE, DECIDE IN THIS FILE with a one-line reason: deterministic
(Pillow, `content-sourcing.md` Tier A) or diffusion (a `prompts.json` schema 2
entry with seed, negatives and the rules clause). Two of the seven wait on
canon and must say so rather than inventing: E10 needs a canon street name and
G7 needs canon crew names.

THE RUNNABLE-TONIGHT CLAIM WAS WITHDRAWN BY THE DIRECTOR AND HERE IS WHY:
`prompts.json` has no entry for any of the seven. Grep it before assuming
otherwise.

Deliverable: the entries, plus a small generator for the deterministic ones,
then ONE `make-the-pictures` dispatch. Not seven dispatches.
