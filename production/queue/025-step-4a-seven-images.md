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

---

## THE SEVEN DECISIONS, made 2026-09-02, one line of reason each

Deterministic means Pillow, `content-sourcing.md` Tier A: no model, no
network, no account, no licence question, and it runs in the dev container
(Pillow 12.3.0 and numpy 2.4.6, checked this session). Diffusion means an
entry in `tools/imagegen/prompts.json` schema 2 with a seed, its negatives and
the shared rules clause, taken on the one batch dispatch.

| line | route | why, in one line |
|---|---|---|
| A5_double_yellow_lines | DETERMINISTIC | Two 100 mm bands with a 100 mm gap is a MEASUREMENT the BOM already states, and no diffusion model holds a constant band width or a seamless tile; the paint edge and the wear are seeded noise over exact geometry. |
| A9_puddle_mask | DETERMINISTIC | A mask is data, not a picture: it has to tile and its value has to MEAN "standing water here", and thresholded value noise gives both, where a model gives a photograph of a puddle with somebody else's lighting baked into it. |
| B4_gutter_water | DETERMINISTIC | A strip whose alpha ramps into the kerb line, generated from the same kerb geometry as A5 so the two line up; a painted strip would have to be matched to the kerb by eye, every time the kerb moves. |
| C11_lit_interior_card | DIFFUSION | This one is DEPICTED CONTENT, not geometry: shelves, a bar back, a stair landing seen through glass at night is painting, which is Tier A's stated weakness and the model's stated strength. Three cards, three seeds. |
| C12_net_curtain | DETERMINISTIC | A net curtain is a regular weave plus a vertical gather, which is a grid and a sine: Pillow draws it with correct alpha and no perspective, and a model would bake a room, a window frame and a viewing angle into a texture that has to sit flat behind any opening. |
| E10_street_name_plate | DETERMINISTIC, canon-locked | Lettering on a plate is Tier A's own example, and diffusion cannot spell reliably. See the canon note below: the NAME is not blocked, the plate's authority legend and the choice of which street is. |
| G7_graffiti_tags | BLOCKED ON CANON, no entry written | A tag names a crew; `canon.md` mints no crew names, so writing a prompt today means inventing one, and canon outranks this file. Route when it unblocks: DETERMINISTIC, because the crew name has to be legible and diffusion cannot spell it. |

Count: five deterministic, one diffusion, one blocked. Denominator seven.

### The canon note on E10, because the brief's premise was worth checking

`canon.md` line 13, quoted exactly: "Streets minted: Quay Street, Weighhouse
Lane, Tannery Row." So the street NAME input exists and nothing has to be
invented to make this plate. The deterministic generator reads those names out
of `canon.md` at run time and REFUSES any string that is not in it, so the
"do not invent a name to unblock yourself" rule is enforced by the tool rather
than remembered by a person.

What is genuinely open, and is a director question rather than a builder one:

1. WHICH street the vignette depicts. The generator makes a plate for all
   three minted names so the scene JSON picks by name rather than waiting.
2. THE AUTHORITY LEGEND. A British plate of this period usually carries a
   council or borough line above the name. `canon.md` mints seven DISTRICTS
   (the Hook, Copper Row, the Exchange, the Parade, Fairview, Ironside,
   Gullwing) and no council. The plates therefore carry a canon DISTRICT line
   and no council name. If Jafar mints a council, that is the better legend
   and it is one string away.

### The canon block on G7, stated so nobody re-derives it

`canon.md` names three rival organisations by their heads (Aldous Vane, Sera
Kest called the Widow, Danny Ro) and names no crew the way a wall would: no
tag, no initials, no street name for the crew itself. The brand bible section
records what canon still owes and crew names are not even on that list. So
this line needs Jafar to mint between three and five short tag names, and it
stays out of `prompts.json` until he does. Twenty tags off three or four
names, with the marker and chrome variants, is one short generator run once
the names exist.

### Two rungs named rather than left blank

- The plate face is PT Sans (`ledger/Assets/Resources/LedgerSans.ttf`, SIL
  OFL, already attributed), because it is the only face on disk with its
  licence beside it. A condensed grotesque (League Gothic or Oswald, both OFL
  and both probed reachable through raw.githubusercontent) is the more
  period-correct plate face and is one fetch away. Named, not taken, tonight.
- The deterministic outputs are 2K. Nothing has measured how they read at
  street distance in either engine yet, so 4K is a rung with a trigger rather
  than a default: if the D1b frame shows the paint edge smearing, regenerate.

## RULED 2026-09-02 (director, decision-2026-09-02-vignette-batch-canon-crews-d1-timebox.md)

G7 IS UNBLOCKED. `canon.md` now carries five tag names (TANNER, SNIDE, GULL,
QUAY FIRM, PARADE RATS), minted on delegated authority after Jafar declined
the naming. The route stays deterministic: a tag must spell its crew.

E10 CARRIES A FINDING. All three street plates stamp `the Hook` as their
district legend, because `make_vignette_2d.py` line 289 takes
`districts[0]` rather than reading a street-to-district map, and canon had
none when the plates were made. Canon has one now (Quay Street in the Hook,
Weighhouse Lane in Copper Row, Tannery Row in Ironside), so two of the three
plates are wrong.

REGENERATING DOES NOT FIX IT, measured by the resident: the generator was
re-run after canon gained the map and produced byte-different but
district-identical plates, because it never reads the map. The fix is in the
generator, and it is item 028's work, not a re-run.

Both are item 028.
