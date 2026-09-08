# The mesh asset interface

SPEC. What a GLB must be for LEDGER to place it without anybody touching an
editor. One page. Every number here was measured from the sixteen props
already shipping, on 2026-09-08, by `python3 tools/ue/import_prop_meshes.py
--measure`; re-run that to re-measure rather than trusting this paragraph.

## Units, axes, pivot

| Thing | Rule | How it is checked |
|---|---|---|
| Unit | **Metres.** One glTF unit is one metre. | The importer compares your GLB's measured size to the size the bill of materials asked for. |
| Up axis | **+Y up**, the glTF default. Do not pre-rotate to Z-up. | Unreal's importer converts; the probe reads the converted bounds back and prints the delta. |
| Forward | **-Z**, the glTF default. A prop meant to face a viewer faces -Z. | Nothing can check this; it is why each placement carries its own `yaw_deg`. |
| Scale | **Ship it life size. Nothing is ever rescaled at placement.** A prop that is the wrong size is a prop to remake. | `propScale=1/never-scaled/dims-policy` on every run. |
| Pivot | **Anywhere you like.** The pivot is not a contract. | The engine places your mesh's own *bounding box centre* at the point the spec names, using the bounds it reads off the imported asset. Measured pivots in the shipping set run from base (most) to top-back (`awning_02`, -1.318 m) to centred (`poster`, -0.502 m). |

The pivot freedom is the one thing an artist coming from another pipeline will
not expect, and it is deliberate: `production/specs/vignette-scene.json`,
`held_props.pivot_note` states it as law, because six source pivots measured
six different ways and no convention was going to survive the next download.

## Geometry budget, measured from the shipping set

Verts 56 to 2362 (median about 800), triangles to match, one mesh node or two,
no LODs, no skeleton, no animation. A prop an order of magnitude heavier than
that is a conversation, not a drop-in.

## Materials

**One material slot. Unlit, untextured, plain.** Every shipping prop measures
exactly one slot and zero embedded images, and that is the interface, not an
accident: the street overwrites slot 0 with its own surface material and never
looks at slot 1.

- The look comes from the piece's `surface` field, not from your GLB.
- Surfaces available today: `asphalt concrete kerb sidewalk brick_red
  brick_grey plaster wood metal glass window interior card roof paint_yellow
  multiply`. Pick the nearest; a new one is a decision record.
- The three map parameters the street's material exposes are `BaseColorMap`,
  `NormalMap`, `RoughnessMap`, plus scalars `TilingU` and `TilingV`. They are
  declared in `ue-probe/Source/LedgerProbe/Public/SurfaceBind.h` and are a
  contract nothing at runtime can check, so do not rename them from your side.
- Ship more than one slot and the run says so: `propMaterialSlotsOver1=N/M`.

## Stable IDs

The file name is the ID. `lamp_post_01.glb` is asset id `lamp_post_01`, and
that id appears in four places that must agree:

1. the file, at `ledger/Assets/Props/base-mesh/<id>.glb`;
2. a line of `production/specs/vignette-bill-of-materials.json`, which decides
   WHICH props the street wants and records why each rejected one was rejected;
3. the `"asset"` field of every piece in `production/specs/vignette-pieces.json`
   that places it (that file is GENERATED; edit
   `production/specs/vignette-scene.json` and regenerate);
4. the uasset the import step makes, `/Game/Ledger/Props/SM_<id>`.

IDs are `[A-Za-z0-9_-]` only, lower case by habit, and a hyphen becomes an
underscore in the uasset name. Anything else is refused by name at import
rather than sanitised, because a silently renamed asset is a mesh the game
looks for at a path that does not exist.

## Gameplay bindings are piece fields, not mesh features

Nothing about behaviour lives in the GLB. A placement is one object in
`held_props.items` and becomes one piece with these fields:

| Field | Means |
|---|---|
| `asset` | the stable ID above |
| `bom` | the bill-of-materials line that justifies it being in the scene at all |
| `name` | unique instance name; the engine's handle for this exact object |
| `surface` | which CityPack surface dresses it |
| `x_m` `y_m` `z_m` | where its **bounding box centre** goes, metres, y up |
| `sx_m` `sy_m` `sz_m` | its measured size, which the import step asserts against the GLB |
| `yaw_deg` `pitch_deg` `roll_deg` | rotation about that centre |
| `emissive` | true puts a point light 0.05 m under the centre |
| `edge` `region` | which part of the street it belongs to, for the per-edge placement breakdown |
| `place` (scene file only) | `ground`, `set_in`, `wall` or `stack`: which datum the y is derived from |

## Handing one over

Drop the `.glb` in `ledger/Assets/Props/base-mesh/`, add its licence line to
`THIRD-PARTY.md` beside it, add an item to `held_props.items` in
`production/specs/vignette-scene.json` with its measured `dims_m`, regenerate
the piece list, and dispatch `ledger-mesh-import`. You will get back a line
naming what loaded, at what size, with how many collision primitives, and how
far off the centre landed. Nobody opens an editor at any point.
