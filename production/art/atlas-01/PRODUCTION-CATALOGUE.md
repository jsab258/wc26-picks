# Production follows the authored places

[Visual entry](DELIVERY.md) · [98-row audit](assets.html) · [First-batch data](data/first-batch.json) · [Source mesh inspections](data/mesh-inspections.json)

The 77 original BOM IDs and 21 proposed IDs are retained. Comparison with the studio BOM at **e5b33d1317e20d672e4f9e39c09e4db41d023e0f** found the same 77 IDs, not a second set to invent. Availability, suitability and integration now have separate fields. `legacy_status` preserves the previous audit without using its ambiguous “missing” category. General district pictures remain contextual targets on uninspected distant entries; they are explicitly not inspections of individual assets.

## Actual reuse findings

Eight existing GLBs were downloaded from that exact studio revision, decoded with node transforms and projected in three orthographic directions. Their measured bounds and hashes are retained. These are source-geometry pictures, not lit Blender renders, UV-quality proofs or Unreal frames. The read-only [inspection script](scripts/inspect_meshes.py) accepts an explicit input directory and reproduces them.

| Actual item / picture | Decision |
|---|---|
| [400mm diagonal grate](previews/mesh-drainage_grate_01.png) | Reuse for pilot; check recess fit and road collision. 600 vertices, 504 triangles, one slot, no images |
| [100mm perforated drain](previews/mesh-drain_cover_01.png) | Unsuitable for a road manhole. Do not commission another small drain or blindly scale this into a manhole |
| [Hooded litter bin](previews/mesh-outdoor_bin.png) | Existing, potentially useful at Gullwing; revise against that district's street furniture. Not the pub's household bin |
| [Plain notice frame](previews/mesh-framed_poster.png) | Reuse; separate paper/image plane. Actual size 0.506×0.801×0.013m |
| [Decorative lamp](previews/mesh-lamp_post_01.png) | Existing, but not the chosen utilitarian Hook road lamp. Reconsider only at a named promenade location |
| [Pavement sign](previews/mesh-pavement_sign.png) | Existing; defer. The private-door footway conflict argues against adding an A-board here |
| [Square pallet](previews/mesh-pallet.png) | Reuse candidate for repair-yard receiving, not pub circulation. 1.2m square; no EUR-pallet claim |
| [Wood barrel](previews/mesh-wood_barrel.png) | Wrong selected pub-service envelope and construction. Keep as an unassigned library asset, not a substitute for a metal cask |

All eight are [The Base Mesh through M3-org](https://github.com/M3-org/base-meshes), CC0-1.0 per the library licence and studio THIRD-PARTY.md. No purchase or replacement library is needed for the two selected pilot meshes. Existing GLBs remain at `ledger/Assets/Props/base-mesh/<mesh_id>.glb`; no duplicated production binaries are committed here. Bounds include all referenced source nodes, so counts can differ from an importer's welded/LOD mesh. No LOD or UV suitability is inferred from these projections.

Three existing generated PNGs were also opened: [Mickey's fascia](references/studio-fascia_mickeys.png), [darts notice](references/studio-poster_darts.png), [opening hours](references/studio-notice_opening_hours.png). Fascia spelling and colour are useful; lamps, mouldings, blank surroundings and 2:1 composition prevent direct use on the 10.91:1 plate. The darts body is unreadable and includes an unrelated streetscape; the hours image includes a whole window and no usable times. Preserve these sources. The authored vector proofs below address exact layout and text without spending another GPU run on lettering. Their source paths and SHA-256 values are in [studio-asset-review.json](data/studio-asset-review.json). These PNGs are earlier studio AI outputs, not outputs of this commission's continuation.

## First production batch: frontage and bar reading

Twelve work packages, sixteen named initial placements. This is a bounded first batch, not a claim that the pub or all distant interiors are inventoried. [first-batch.json](data/first-batch.json) is the executable specification: stable BOM ID, mesh ID, source-space bounds-centre placements, exact dimensions, quantities, authored variants, dependencies, acquisition steps, per-item collision/gameplay notes and planning allowances. Every row below has its own target or actual asset picture. All custom dimensions are authored; current manufacturer cask dimensions are explicitly only a space comparator.

| Order / ID | Target, required count and authoring route | Constraint |
|---|---|---|
| 1 A7_gully_grate | [Actual grate](previews/mesh-drainage_grate_01.png), 1; reuse | 0.4m square; keep it out of door swing and test recess |
| 1 E12_a_board_posters | [Actual frame](previews/mesh-framed_poster.png), 1; reuse | One indoor case; no extra pavement board |
| 2 C5_shopfront_assembly | [Fascia body](previews/target-a01_pub_fascia_body.png), 1 unique; hand model | 6×0.55×0.12m; source openings untouched |
| 2 C6_fascia_lettering | [Lettering plate](previews/target-a01_mickeys_fascia_plate.png), 1 unique; vector composition | Reconciles existing `fascia_mickeys` brief, not a new competing ID |
| 3 A01_PUB_BAR | [Counter target](previews/target-a01_pub_counter.png), 1 unique; hand model | Exact existing run; washing-end detail is a proposed later refinement, not in repair render |
| 3 A01_PUB_TILL | [Till target](previews/target-a01_pub_till.png), 1; hand model | Matches existing 0.45×0.30×0.45m proxy; exact period design needs review |
| 3 A01_PUB_BEER | [Hand-pull target](previews/target-a01_pub_beer_engine.png), 1; hand model | One cask line; four-cask store set is phase 2, not included in count |
| 3 A01_PUB_FURNITURE | [Table target](previews/target-a01_pub_table.png), 2; reuse one custom design | Different named wear at front and snug; same dimensions |
| 3 A01_PUB_SNUG | [Screen target](previews/target-a01_pub_screen.png), 1; hand model | Retain 1.45m height and observed hand-ray condition |
| 4 C12_net_curtain | [Net target](previews/target-a01_pub_net.png), 1; manual/cloth authoring | Alpha and perception integration unresolved; do not fake transparency with an opaque prop |
| 4 E13_household_dustbin | [Metal-bin target](previews/target-a01_pub_metal_bin.png), 2; hand model | Chosen Hook collection, not nationwide period rule |
| 4 A01_PUB_NOTICES | [Paper target](previews/target-a01_pub_notice_paper.png), 3 named graphics; vector | Exact text and individual sizes in 2D briefs; three different placements |

Custom authoring is justified by the particular dimensions and fictional identity, not a requirement to use scripts for every object. Reuse two real source meshes; hand model joinery/equipment; use cloth/manual folds for nets; typeset signs; use local image generation only for a surface study. Designed scripts draw chosen geometry, not rooms or random dressing. The estimate fields total planning allowances only; elapsed human effort was not timed, so these are not measured production rates.

The interface is now reconciled: metres, glTF +Y up/-Z forward, life-size geometry, arbitrary source pivot with bounds-centre placement, one untextured slot and no embedded images. Each proposed mesh has one listed existing surface. Richer paint, paper, alpha and mixed finishes require separately supported pieces or Claude's future interface work. Exact UV density (512px/m near the player) and any texture/geometry budget are provisional, not an engine target. Collision, opened doors, cash actions, beer service, acoustic portals and NPC schedules remain placement/gameplay bindings. The first batch is a reviewable specification, not a set of integration-ready GLBs.

## Town-wide production order and uncertainty

| Phase / families and unique assemblies | Named use and deliberate differences | Inventory limit |
|---|---|---|
| 0 / A01_PUB_SHELL, FLOOR, STAIR, YARD, GATE | Exact source pub shell, stairs and five cameras; service yard and privacy/escape review | Recipe repaired; no Blender result. Private threshold and WC need design resolution before finished joinery |
| 1 / twelve packages above | Mickey's frontage, front room, counter and nearby kerb | Fully specified first batch, provisional appearance |
| 2 / remaining pub furniture, BEER, UPPER; C8/C9/D8 | Fixed benches; four metal casks/two stillages; private kitchen/bath/bed/book room; individual doors/windows | Layout exists, but detailed equipment/household inventory and access design remain partial. No procedural interior completion |
| 3 / A01_FACADE_FAMILIES, C2–C14, D1–D8; A/B street surfaces | Hook: altered grocer, fish shop, cafe, chandler, barber; repaired brick, tile stallrisers, aluminium glazing, stock and rear uses | Twelve frontages have uses; ten detailed neighbouring interiors still to author. Inspect existing materials in engine before replacements |
| 4 / A01_MARKET_HALL, RETORT_WORKS, QUAYS, HARBOUR_BOARD | Copper: stall/shop service families; Ironside: repair bays, barriers, handling gear; Hook: tidal ladders/edge/cargo assembly | Employment/routes designed; structures schematic. Vehicles/cranes/boats need dated references and authored loads |
| 5 / A01_RECORDS_COURT, TIVOLI, WINTER_ROOMS, SCHOOL_GATE | Exchange: post-war offices and formal grounds; Parade: modern refits and cinema; Gullwing: boarding houses and laundry; Fairview: villas, altered terraces, flats and retaining walls | Named assemblies are not full asset inventories. Shared window/door/roof families receive district-specific proportions and alterations |
| Across phases / E, F, G, H | Furniture, wardrobe, vehicles, signs, waste, surfaces, lighting and weather | No cloned district dressing; adult wardrobe, vehicles, bus/school/institution contents and household possessions need deeper period reference. Weather is engine work, not an acquired prop |

## Small pilot and observation request

[pilot-request.json](pilot-request.json) is **pending, not dispatched**. It reuses the studio imagegen lane and the existing `fascia_mickeys` identifier, plus one proposed surface-study ID. It does not install a model, change prompts.json, reserve the PC or create a scheduler. Claude must reconcile the input records with that lane. The five-camera recipe request remains separate and already exists at repair source 40811f56825ac0737b818689f5e138396d7218a2.

Pilot scope: one existing grate, one notice frame with an authored paper proof, and the dimension-correct fascia proof against one small generated paint study. Run dry diffuse daylight first, then the existing evening treatment. Check 1.7m eye height at 1m and 5m, plus street approach. Judge legibility, scale, edge silhouette, glare and repeated texture; do not count a file or import as acceptance. A colour sample supplies no trustworthy normal/roughness by itself. Keep attempts, rejects, revisions, images and per-run timings; request human review duration rather than inventing it.

Measured now: 8 actual mesh inspections, 3 existing-image inspections, 4 newly authored vector proofs. **New GPU attempts 0; accepted finished 3D assets 0; accepted generated production images 0; local GPU time 0.** Source generation counts elsewhere in the repo describe earlier studio work, not this pilot. Human review time and future render time are unknown. No throughput estimate is derived from the 98 audit rows or the check count.
