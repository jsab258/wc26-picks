# What each kind of picture means

Continuation provenance: `previews/evidence-revisions`, `town-work-and-home`, `hook-uses`, `mickeys-service-options` and `target-*` are original SVG design studies, rasterised with the existing Sharp bundle. `previews/mesh-*` project actual studio GLB triangles with node transforms; they are neither lit Blender renders nor engine frames. `artwork/*.svg` and their preview PNGs are four original exact-text layout proofs using system fonts, not final font-cleared textures. `references/studio-*.png` are three retained studio AI outputs read at e5b33d1317e20d672e4f9e39c09e4db41d023e0f, with hashes in data/studio-asset-review.json. No new AI image generation, Blender render or Unreal frame occurred in this continuation. The initial concepts below remain unchanged.

All new design work is a proposal dated 2026-09-08, based on the owner's pin 7722b45cb3dcee2fbcee26675fae4fef641cbba7. [data/source-lock.json](data/source-lock.json) records source-document hashes and the owner's overrides. No studio pin was invented.

| Files | Origin | Evidential limit |
|---|---|---|
| concepts/hook, copper, exchange, parade, fairview, ironside, gullwing, mickeys.png | Built-in OpenAI image_gen service, generated for this commission and selectively edited after visual inspection | AI concepts. No Blender, Unreal or shared-PC image generator was invoked. Model version and random seed were not exposed by the tool; these are not deterministic renders |
| previews/atlas-overview, gameplay-overlay, hook-detail and district-*-plan.svg/png | Original authored coordinates in data/atlas.json, Python SVG drawing, Sharp PNG rasterisation | Broad layout and relationships are intentional; no real town graph was traced. Contours are schematic, not a surveyed heightfield |
| previews/mickeys-*.svg/png | Explicit pub JSON, drawn plans and elevations | Dimensioned authoring proposal. Perspective concept detail does not supersede the plans |
| previews/reference-hull and reference-kasbah.svg/png | Original annotations/diagrams and embedded dated reference evidence | Reference photographs/maps, not Meridian concept or game geometry. See references/RIGHTS.md |
| previews/asset-audit-phone.png | Headless Edge screenshot of this package's HTML at 390px width, filtered to A01_PUB_BAR | Browser layout check only |
| references/source-street-day.png and street-evidence-contact.png | Retained images from the pinned project's production/d1-probe directory | Earlier game evidence, not a new run. Contact sheet contains camA/camB day/night and walk 00 through 04 |
| recipes/mickeys_blockout.py | Authored Blender Python source from the pub JSON | Syntax checked only. No .blend or geometry render is claimed |

Initial image requests are retained in data/concept-prompts.json; targeted corrections and the Mickey's request are in concept-edit-prompts.json, concept-final-prompts.json and concept-period-prompts.json. Original imagegen outputs remain in the tool's own output directory; the reviewed final copies are included here. Hashes in INVENTORY.md identify exactly the copies delivered. Concept art may still contain incidental lettering and approximated small objects; no incidental mark is approved as an exportable logo, vehicle design or production texture.

Maps were reviewed for coastline, north direction, seven district identities, named destinations, label separation and the source street connection. Pub drawings were reviewed for the east bay 0 location, left/right facade orientation, roof ridge direction, private/public access, service route and the snug sightline. The image edits corrected an early-period costume/vehicle bias, oversized skyline churches, a reversed fish-shop order, an invented harbour view through the service lane, a high screen, aisle-obstructing stools and a wheeled bin. These are art corrections, not proof of photoreal game performance.

Blender context ground strips are cropped, flat spatial aids with the source road/footway widths and axes. They do not replace the source street's cambered ground system. Glass in the recipe is opaque proxy material. Image concepts do not prove shader compilation, transparency, door swing clearance, physics, acoustic transmission, recognition, memory or spoken consequences.

The inherited art/asset/Blender conventions were searched at the pin and were not found. This package therefore defines only commission-local assumptions in INTERFACE-NOTES.md. No review record, art acceptance or integration receipt has been manufactured.
