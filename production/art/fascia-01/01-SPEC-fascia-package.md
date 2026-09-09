# The fascia package: cornice and console brackets

STATUS: SPEC. Station 1 of five for the first package of the twelve-package
batch. Written 2026-09-09. Governed by `canon.md`, which outranks this file,
`production/specs/asset-interface.md`, which is the shape every number below
has to fit, and `ledger-v2/research/license-allowlist.md`, which is law.

BOM line: `C15_fascia_cornice_console`, group C, the frontage at eye level.
Assets: `fascia_cornice_01`, `fascia_console_01`.

## 0. What this package is, and the split it had to decide first

The brief asked for the shopfront fascia as a real mesh in the street, with
the lettering remaining the decal's job where that is the right split. The
street already has both halves as something else:

- the fascia BOARD is six boxes, `east_parade_fascia0` to `5`, 6.000 x 0.550 x
  0.120 m, surface `wood`, read out of `production/specs/vignette-pieces.json`
  on 2026-09-09;
- the fascia LETTERING is four decals, `decal_00_fascia_mickeys`,
  `decal_01_fascia_fish_market`, `decal_02_fascia_ritas_pawn`,
  `decal_03_fascia_steam_laundry`, 2.350 / 5.300 / 4.690 / 5.340 m wide, each
  an atlas page and a UV rect in its `asset` field, sitting 0.010 m in front of
  the board at z=4.995 against the board's face at z=5.005.

### THE SPLIT, AND IT IS SETTLED BY ARITHMETIC RATHER THAN BY TASTE

GEOMETRY GETS THE CORNICE AND THE CONSOLES. THE DECAL KEEPS THE LETTERS.

Three reasons, in the order of how much they decide:

1. RELIEF AGAINST SHADOW, measured against the light this town has. An applied
   letter on a 1990 fascia stands 6 to 25 mm off the board. Under the overcast
   sky canon fixes as the visual target there is no hard sun to throw a letter
   shadow, so 25 mm of relief buys a sub-pixel gradient at the 3 to 15 m the
   street is read from. The cornice is 0.215 m deep and oversails the board by
   0.095 m (measured, section 4), and what it throws is not a gradient: it is a
   dry strip above a wet band and a hard horizontal shadow line across a 36 m
   terrace. The same money spent on letters buys nothing the decal does not
   already have. GEOMETRY GOES WHERE THE SHADOW IS.
2. A NEW SHOP MUST NOT BE A PIPELINE CHANGE. `asset-interface.md` says the file
   name is the ID and that ID has to agree in four places. Letters as geometry
   means Meridian's fifth shop is a fifth GLB, a fifth bill-of-materials line, a
   fifth uasset and a fifth import; letters as a decal means it is one generated
   texture on a route that has already produced four. The cornice and the
   console are the opposite case: they are the SAME object on every unit of a
   terrace built at one time, so one asset serves six bays.
3. THE LETTERING ROUTE ALREADY WORKS AND IS NOT THE GAP. Nothing in this
   package touches the four existing decals, their positions, their widths or
   their atlas rects.

WHAT THE EXISTING FASCIA BOARD KEEPS. The six `east_parade_fascia*` boxes stay
exactly as they are, and the new geometry is placed in air that is currently
empty (above the band) or inside the board and its pier (behind it). Nothing is
deleted and no existing piece moves, which is why this package cannot regress a
frame that has already been judged.

## 1. Canon constraints, each one checked against canon.md rather than recalled

| Canon | What it forbids or requires here | How this package answers |
|---|---|---|
| Era 1988 to 1992, late analog | No object may imply a mobile, the internet or anything post-1992 | A painted timber cornice and console brackets are Victorian or Edwardian joinery still standing in 1990. There is no electrical part, no illumination, no plastic and no fixing that did not exist. |
| No 1950s and no 1970s framing | The 1970s aluminium box fascia is the period's other truth and is NOT in this package | Stated and deliberately deferred, section 7, so that a later reader cannot mistake its absence for an oversight. |
| Visual target photoreal, wet, overcast, grimy | Geometry must earn its cost in weather, not in detail | The whole package exists for a drip groove and a shadow line, which are weather features. The drip is at 0.1550 to 0.1750 m from the wall, outboard of the 0.120 m board face, so water leaves the cornice clear of the sign. |
| No real brands, no real people | A fascia is where a brand would be | THIS PACKAGE CARRIES NO LETTERING, NO LOGO AND NO TEXT OF ANY KIND. There is nothing on it to infringe. The four shop names stay in the existing decals and are Meridian's own: Mickey's (minted in canon), the fish market, Rita's Pawn, the Steam Laundry. |
| The built street is Quay Street, in the Hook | Placement belongs to that street and nowhere else | All 17 placements are `east_footway` on the east parade of the one built street. The `east_parade_*` identifiers are asset names and carry no district claim, per canon. |
| Licence allowlist is law; nothing purchased | Every asset carries a licence tag | Authored in house, no fetch, no purchase, no model weights. Tagged in `ledger/Assets/Props/base-mesh/THIRD-PARTY.md`, section 6. |

## 2. Research, with dates and what could not be found

Searched 2026-09-09. Local authority shopfront design guides are the only
dimensioned British source that is public, and most of the PDFs are blocked by
this container's egress proxy, so where a number comes from the search
channel's summary of a document rather than from the document's own page, THIS
FILE SAYS SO. That distinction is the whole point of the labels.

- FASCIA DEPTH. Search-channel summary of several UK local authority shopfront
  design guides (West Oxfordshire Design Guide 17, Test Valley SPD, North
  Lincolnshire, Herefordshire draft 2008, RBKC 2010), read 2026-09-09:
  "Traditional fascias do not exceed 380mm in depth" and fascias "should not be
  excessively deep, generally less than approximately 400mm". CONFLICT WITH
  THIS STREET, RECORDED RATHER THAN RESOLVED AWAY: the street's band is 0.550
  m, and that number is not a choice either, it is arithmetic already in
  `vignette-scene.json` (fascia_bottom 2.85 to the 3.40 underside of the first
  floor). The guidance describes what a CONSERVATION OFFICER WANTS; a 1990 port
  town parade is full of bands that are deeper than that, which is exactly why
  the guidance had to be written. The street's 0.550 stands, and the consoles
  are sized to the band rather than to the cited range so the proportion holds.
- CORNICE, FUNCTION AND FORM. Same channel, same day: "Traditional fascias
  generally have a projection above in the form of a moulded cornice (often
  with lead flashing), which is both decorative and functional, giving a clear
  edge to the top of the shopfront and affording weather protection", and "The
  cornice is a narrow projecting detail over the fascia whose functions are to
  keep rain off the fascia sign and to provide a strong definition to the top
  of the shopfront." The drip groove and the outward wash in section 3 are
  that sentence turned into geometry.
- CONSOLES. Same channel, same day: "Consoles are brackets at each end of the
  fascia which help to visually terminate the top of pilasters, and are a
  feature of traditional shopfronts that should always be retained or
  restored", with a size given as "their projection above the fascia typically
  between 15-30 centimetres high". THAT SENTENCE IS AMBIGUOUS IN THE SUMMARY
  and is labelled so: it can be read as the console's height or as how far it
  stands above the fascia, and the underlying PDF is blocked here. It is
  therefore NOT used as the console's height. The height used is the street's
  own measured band, 0.550 m, because a console that stops short of the fascia
  bottom leaves the board's end grain open and no joiner does that.
- STALLRISER. Same channel: "Stallrisers should not exceed approximately 450mm
  in height (or 18 inches) or the depth of the fascia, whichever is less." Not
  used by this package, recorded because the street's stallriser is 0.600 and a
  later package will meet the same conflict.
- THE PERIOD'S OTHER FASCIA, the one this package deliberately does not build.
  Search-channel summary, 2026-09-09: "From the 1970s onwards, most illuminated
  signage for shopfronts comprised a box-like case fabricated from aluminium
  extrusions and other kit-like parts designed to contain arrays of fluorescent
  tubes, capped with a lid and featuring a Perspex panel as the sign face."
  That is the 1988 to 1992 high street as much as the timber cornice is.
  Section 7 says why it is a second package and not this one.
- WHAT COULD NOT BE FOUND, named so nothing downstream has to guess. No
  dimensioned British cornice or console SECTION drawing with a date was
  reachable: every source found gives depth and height envelopes and prose, not
  a moulding profile with ordinates. So the two profiles in section 3 are
  AUTHORED within the cited envelopes from the named functions (throating,
  corona, wash, scroll), and they are not a traced copy of anybody's drawing.
  Also not found: a dated figure for how far a rainwater downpipe bracket
  stands off a wall, which is why the 0.0200 m clearance in section 4 is
  labelled CHOSEN rather than cited.
- ALSO RELEVANT AND DATED, the statutory frame the period actually had:
  the Town and Country Planning (Control of Advertisements) Regulations 1989
  (SI 1989/670, legislation.gov.uk), in force across the working window and
  replaced by SI 1992/666, granted deemed consent to many fascia signs subject
  to conditions and did not permit illumination "unless reasonably required".
  It is not a dimension and nothing here depends on it; it is recorded because
  a 1990 shop sign existed inside that regime and a later package about signage
  will want it.

## 3. The two assets, with every dimension's source

Both are EXTRUDED PROFILES, which is what a moulding is: a section run along a
length. The profiles are given as explicit (depth from the wall, height) point
lists in metres in `author/make_fascia_mouldings.py`, which is the authoring
recipe and the only place the numbers live.

### fascia_cornice_01, measured 5.8920 x 0.1500 x 0.2150 m

| Number | Value | Source |
|---|---|---|
| Depth | 0.2150 | DERIVED. One British brick on its length. `vignette-scene.json` facade note: "A British brick is 215 x 102.5 x 65 mm". Must exceed the 0.120 board projection so rain leaves clear of the sign; it exceeds it by 0.095. |
| Height | 0.1500 | DERIVED. Two courses at `vignette-scene.json` `brick_course_m` 0.075, which that file derives as 65 mm brick plus a 10 mm bed joint. |
| Length | 5.8920 | DERIVED, AND NOT THE BAY. 6.0000 (bay, `east_parade_fascia0.sx_m`) less the 0.068 m D5 downpipe less twice the 0.0200 clearance. See section 4. |
| Profile | 12 points | AUTHORED within the cited envelope: flat bed, throating (drip groove) at 0.1550 to 0.1750 and 0.0120 deep, upright corona 0.0480, cyma recta back to a 0.2070 cap, then a wash falling outward at 27 degrees so water sheds to the drip. |
| Surface | `wood` | The existing fascia board is `wood`; a cornice over a timber fascia is timber. On the allowed list in `asset-interface.md`. |

### fascia_console_01, measured 0.2400 x 0.5500 x 0.1800 m

| Number | Value | Source |
|---|---|---|
| Height | 0.5500 | MEASURED off this street. `vignette-scene.json` fascia_bottom 2.85 to the 3.40 first-floor underside; the same 0.550 as `east_parade_fascia0.sy_m`. The console spans the band it terminates. |
| Width | 0.2400 | DERIVED FROM A CLEARANCE. The largest round 10 mm width that clears the 0.068 m downpipe at x=9.000 from a pilaster centre at x=8.825. Measured clearance 0.0210 m. Narrower than the 0.350 pilaster it stands on, which is normal: the console sits within the pier. |
| Depth | 0.1800 | DERIVED BY BRACKETING. It must exceed the 0.1200 board projection, and it must stop short of the 0.2150 cornice, because a cornice oversails its consoles. 0.1800 leaves 0.0350. |
| Profile | 14 points | AUTHORED. A scroll silhouette: a 0.060 toe with a nose at 0.0740, a hollow, then the S out to full projection at the neck and a flat 0.0220 under the cornice. |
| Side relief | 0.0120 | A per-station taper of one part in fifteen on the two outer slabs, which puts a chamfer down each side and leaves a raised centre panel, without a stepped ring that could leave a degenerate face. |
| Surface | `wood` | Shopfront joinery fixed to a `brick_red` pier. Timber on brick is correct; the pier is the building and the console is the shopfront. |

### What the street gets: 17 placements

SIX CORNICES, one per bay, x = 6, 12, 18, 24, 30, 36.

ELEVEN CONSOLES of twelve pilaster centres, x = 3.175, 8.825, 9.175, 14.825,
15.175, 20.825, 21.175, 27.175, 32.825, 33.175, 38.825.

THE TWELFTH IS DESIGNED OUT, NOT FORGOTTEN, and this is the package's one piece
of authored variation. Bay 3 (x=24) is the only bay with an awning and no
fascia lettering, which makes it the parade's empty unit; its right-hand
console at x=26.825 is gone the way a console goes in a port town, clipped off
and never put back. The count therefore reads 11 of 12 with the absence named,
never a bare 11. A terrace built at one time has ONE moulding repeated, which
is what a builder does; the variation on a real street comes from what happened
to it afterwards, so the variation here is ABSENCE and not a second design.

## 4. Acceptance checks, written as things that can be MEASURED

Each is an arithmetic statement over `production/specs/vignette-pieces.json`
and the two GLBs. Every one of the ten was measured on 2026-09-09 and the
results are in `03-VERIFY-fascia-package.md`; the numbers below are the BOUNDS,
not the readings.

| # | Check | Bound | Measured by |
|---|---|---|---|
| A1 | Cornice soffit minus fascia band top, over 6 cornices | 0.000 mm exactly | arithmetic on the piece list |
| A2 | Console centre y minus fascia band centre y, over 11 consoles | 0.000 mm exactly | arithmetic on the piece list |
| A3 | Console top minus cornice bottom, over 11 consoles | 0.000 mm exactly | arithmetic on the piece list |
| A4 | Cornice oversail past the fascia board face | greater than 0.000 m | arithmetic on the piece list |
| A5 | Cornice oversail past the console face | greater than 0.000 m | arithmetic on the piece list |
| A6 | Minimum x clearance from any new piece to any east D5 downpipe, over every pair sharing both y and z | at least 0.0200 m, and the pair count ships with it | arithmetic on the piece list |
| A7 | Every new piece's rear face on the building line z=5.1250 | 0.000 mm exactly, over 17 | arithmetic on the piece list |
| A8 | Interpenetration with any east piece that is not C5 or C15 | 0 clashes, and the pairs-examined count ships with the zero | arithmetic on the piece list |
| A9 | Interpenetration with C5 | exactly 22, and they must all be ENCLOSED (console rear inside its own pilaster and its bay's fascia board) | arithmetic on the piece list |
| A10 | Decal height lost behind a cornice | reported with its denominator, not bounded | arithmetic on the piece list, CONTAINMENT and not overlap, because a decal has sz=0 and an overlap test on a zero-thickness plane can only ever return zero |
| A11 | GLB measured dims minus the spec box, worst axis, over every asset the street asks for | 0.0000 mm at tolerance 0.001 | `python3 tools/ue/import_prop_meshes.py --measure` |
| A12 | Mesh nodes per GLB | exactly 1, or the street's resolver correctly refuses to choose and places a box stand-in, which is what `pavement_sign` does | `import_prop_meshes.glb_mesh_names` |
| A13 | Material slots and embedded images per GLB | 1 slot, 0 images | `tools/meshgen/meshgen.py --series` and `glb_stats` |
| A14 | Verts and triangles inside the library's measured series | within 36..4182 verts | `python3 tools/meshgen/meshgen.py --series ledger/Assets/Props/base-mesh` |
| A15 | Regenerating the GLBs produces identical bytes | sha256 equal | `sha256sum` on two runs |

THE CLEARANCE OF 0.0200 m IS CHOSEN, NOT CITED, and it is labelled so because
no dated figure for the stand-off of a downpipe bracket was reachable (section
2). What it is traded against: smaller and the joint stops reading as a joint
at the quantisation the piece list uses; larger and the cornice starts reading
as a row of separate planks. The gate reads the MEASURED minimum, not the
chosen number.

WHAT NO EXISTING INSTRUMENT MEASURES, stated rather than left as a gap for
somebody to discover. A1 to A10 are arithmetic over the piece list, and there
is no committed tool that re-runs them, so they are a ONE-TIME MEASUREMENT and
they will decay exactly the way a comment decays. The next rung is to fold
them into the per-edge placement breakdown that already exists on the Unreal
side, which is a queue item and not this package's work, because Jafar's ruling
of 2026-09-09 is that no new instrument is built for the art lane this week.

## 5. Authoring route: what already existed and what did not

Checked in this container on 2026-09-09 rather than assumed:

- `blender` is not on PATH and `bpy` does not import.
- `trimesh`, `pygltflib` and `gltflib` are all absent.
- `tools/meshgen/meshgen.py`'s `local` backend NORMALISES A MESH THAT ALREADY
  EXISTS (measure, decimate, LOD, export) and refuses without Blender.
- the three files in `tools/art-recipes/` are Blender recipes; the blockout's
  own receipt says "spatial blockout only; no engine export".

SO THE PROJECT OWNS A glTF READER IN TWO PLACES AND NO glTF WRITER ANYWHERE.
That is the finding, and it is a finding about the whole twelve-package batch
and not about this package: `production/throughput.md` prices a twenty-third
piece at "a GLB and nothing else" and then says honestly that what it takes to
author a GLB worth importing is unmeasured. It was unmeasured because there
was no way to write one here.

`author/make_fascia_mouldings.py` is the smallest thing that closes it for this
package: 2 profiles, a sweep, an ear clip, and a GLB writer, stdlib only. IT IS
NOT AN INSTRUMENT. It measures nothing the studio reads, gates nothing, prints
no verdict key and sits under `production/art/fascia-01/` rather than under
`tools/`. Whether the batch wants a real generator under `tools/` is a decision
for after the week Jafar's no-new-instrument ruling covers, and it is card 3.

## 6. Licence

LEDGER's own work, authored in house. Nothing fetched, nothing purchased, no
model weights run, no third-party geometry, texture, UV set or byte. Both files
contain only positions, normals, UVs and indices computed from the numbers in
the authoring recipe, plus one untextured material with no image.

Tagged at `ledger/Assets/Props/base-mesh/THIRD-PARTY.md`, whose first sentence
had to be corrected on the same day: it said "Every .glb in this directory is
CC0 1.0 from The Base Mesh", and the first in-house mesh to land there made
that a false licensing claim rather than a stale count.

THE GLBs ARE DELIBERATELY NOT ALSO KEPT UNDER `production/art/fascia-01/`.
`tools/attribution-check.py`'s `OURS` row for `production/art` says in its own
value that it covers "Blender previews only, under production/art/*/previews",
and two authored GLBs there would have been classified as ours by a row that
says it does not cover them. The check would have gone green on a sentence that
had stopped being true, which is the exact failure that row was written to
prevent. They live at the contract path `asset-interface.md` names and are
reproducible from one command, byte for byte.

## 7. What is NOT in this package, so nobody looks for it

- THE 1970s ALUMINIUM BOX FASCIA. Cited and dated in section 2 and it is the
  other half of the period's truth: a port town parade in 1990 has units whose
  original fascia is hidden behind a Perspex-faced box screwed over the
  joinery. It is a SECOND package, not a silent omission, for three reasons
  that are all about landing this one: a box fascia covers the consoles and
  often the cornice, so it is a REPLACEMENT case rather than an addition and it
  would have to delete existing pieces; its sign face is translucent and lit,
  which is an `emissive` and material conversation; and its lettering is a
  different decal route from a painted board. Partial work counts zero, and a
  package that reached for three assets and landed none would be worth less
  than one that landed two.
- LEAD FLASHING over the cornice. Real, cited, and 1 to 2 mm thick: it is a
  material and a grime decal, not geometry.
- ANY CHANGE TO THE FASCIA BOARD, THE LETTERING DECALS, THE PILASTERS OR THE
  DOWNPIPES. Every one of those is existing data this package reads and does
  not write.
- THE WEST SIDE. The west frontage has no C5 shopfront assembly, so it has no
  fascia band for a cornice to sit on.
