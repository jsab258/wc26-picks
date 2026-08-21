# Visual bar — asset sources, verified

> **STATUS — SPEC.** Research landed 2026-08-21 (agent run, ~90 min, methods
> below). Source table for M17.10 fetches. `visual-bar-spec.md` holds the
> plan this feeds; fetches ride the `props-fetch`/`citypack-fetch` workflow
> shape with attribution rows in THIRD-PARTY.md.

## Verification legend — read this before trusting a row

The research container's proxy 403-blocks kenney.nl, polyhaven, ambientcg,
quaternius, poly.pizza, opengameart, itch.io. What works from here:
`raw.githubusercontent.com` and git clones. So every row is tagged:

- **[FETCHED]** — bytes downloaded or git tree enumerated during research.
- **[URL-IN-USE]** — the exact URL appears in a third-party public fetch
  script, several with sha256 and download dates of Jun–Jul 2026.
- **[PAGE-CONFIRMED]** — page + licence confirmed via search snippets; URL
  derived from a proven pattern, this exact file unfetched.
- **[UNVERIFIED]** — credible claim, nothing confirmable from here.
- **[CC-BY]** — needs attribution. Everything untagged is CC0.

CI fetch patterns proven by third parties: `ambientcg.com/get?file=<ID>_<RES>-<FMT>.zip`,
`dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/<slug>_2k.hdr`,
`kenney.nl/media/pages/assets/<slug>/<hash>-<ts>/<file>.zip` (hash rotates on
pack update — scrape the asset page for the current link; use a browser UA;
one repo reports Cloudflare blocking bare curl, so keep the OpenGameArt
mirrors as fallback), `opengameart.org/sites/default/files/<file>`,
`static.poly.pizza/<uuid>.glb`.

## A. Street furniture

| pack | fetch | licence | contents / fit |
|---|---|---|---|
| **The Base Mesh mirror, 900 GLBs** [FETCHED] | `raw.githubusercontent.com/M3-org/base-meshes/main/models/<name>/<name>.glb` | CC0 | THE category-A fill: `decorative_bollard_01/02`, `rounded_concrete_bollard`, `wooden_square_bollard`, `outdoor_bin`, `mesh_bin`, `swing_bin`, `cigarette_bin`, `skip` (builder's skip!), `park_bench`, `garden_bench_01`, `ornate_bench`, `lamp_post_01`, `traffic_cone_01/02`, `pavement_sign`, `finger_post_sign_01-03`, `drain_cover_01`, `drainage_grate_01`, `crowd_control_barrier`, pallets ×4, `oil_barrel`, `wood_barrel`, crates ×3, `poster`, `framed_poster`, `awning_01/02`, `roll_top_chimney`, `weathertop_chimney`, `trunk_protection_railing`. Untextured, real-world scale — a FEATURE: SurfaceSpec tints them like everything else |
| **KayKit City Builder Bits** [FETCHED] | `git clone https://github.com/KayKit-Game-Assets/KayKit-City-Builder-Bits-1.0.git` | CC0 (LICENSE read) | bench, streetlight, trafficlight ×3, trash ×2, dumpster, firehydrant, watertower, road tiles, 5 boxy cars with separate wheels |
| **Kenney City Kit Roads 2.0** [URL-IN-USE, sha256 2C1644A2…] | `kenney.nl/media/pages/assets/city-kit-roads/74288c9459-1741864740/kenney_city-kit-roads.zip` | CC0 | 72 models: roads, lightposts, barriers, construction fences |
| **Kenney City Kit Industrial 1.0** [URL-IN-USE, sha256 99A09FF1…] | `kenney.nl/media/pages/assets/city-kit-industrial/5fcb837741-1750838303/kenney_city-kit-industrial_1.0.zip` | CC0 | factories, warehouses, chimneys, storage tank — the docklands backbone |
| Kenney Pirate Kit / Watercraft Kit / Train Kit [PAGE-CONFIRMED] | scrape `kenney.nl/assets/<slug>` (OGA mirrors exist) | CC0 | docks/piers/rowboats; boats; freight wagons for rail sidings |
| **Quaternius street_pack** [FETCHED] | `raw.githubusercontent.com/trebeljahr/quaternius-showcase/main/public/glb/street_pack/<File>.glb` | CC0 | Streetlight_Single/Double/Triple, TrafficLight ×2, signs ×3 |
| Kenney-CCO flat mirror, 366 GLBs [FETCHED] | `raw.githubusercontent.com/Kenney-CCO/Kenney-CCO.glb/main/<name>.glb` | CC0 | single-file cherry-picks: bench, trashcan, cone, barrels, boxes |
| OGA shipping container + 6-colour texture pack [PAGE-CONFIRMED] | scrape `opengameart.org/content/container-0` and `/content/shipping-container-texture-pack` | CC0 | container mesh + wrap textures for box primitives — the port signifier |
| Poly Pizza (Google Poly archive) [pattern URL-IN-USE] | scrape model page for uuid → `static.poly.pizza/<uuid>.glb` | **per item: CC0 or [CC-BY] 3.0** — read the page | the likeliest source for phone box, pillar box, bus shelter, parking meter, trolley, double-decker; licence read per item at fetch time |

**Not found CC0-fetchable anywhere:** K6 phone box, pillar box, bus shelter,
telegraph pole, TV aerial, dock crane, parking meter. **Verdict: author these
procedurally in Core** — each is a primitive composition well inside existing
competence, tinted by SurfaceSpec, and the Britishness pass wanted most of
them anyway. Fire escapes: not sourced AND not wanted — they are American;
drainpipes are the British vertical.

## B. Grime and decals (the V2 layer)

| pack | fetch | licence | contents |
|---|---|---|---|
| **ambientCG decal sweep** [PAGE-CONFIRMED families; URL pattern URL-IN-USE] | enumerate `ambientcg.com/api/v2/full_json?type=Decal&include=downloadData`, then `ambientcg.com/get?file=<ID>_2K-PNG.zip` | CC0 | `Leaking005`, `LeakingSubstance001` + family (water stains!), `RoadLines001-018+` (worn road paint!), `ManholeCover011`+, `AsphaltDamageSet001` (potholes/repairs), `Sticker001+` |
| ambientCG masks [PAGE-CONFIRMED] | same pattern | CC0 | `SurfaceImperfections001-014` (dirt/wear masks), `Scratches001-005`, `Moss001/002` (damp growth), CorrugatedSteel category (roller shutters) |
| OGA Torn Posters [PAGE-CONFIRMED] | `opengameart.org/sites/default/files/torn-posters.png` (verify filename once from CI) | CC0 | 1024² torn-poster collage — base layer; period-FICTIONAL ads authored in-house go on top (real 80s ads are copyrighted, and in-world brands are better anyway) |
| TextureCan / 3DTexel decals [UNVERIFIED — proxy-blocked] | CI-verify before use | claimed CC0 | 3DTexel claims 280+ decals incl. graffiti — the only CC0-graffiti claim found |
| Graffiti tags — **GAP** | — | — | author ~20 period tags in-house: 80s/90s UK tags were simple marker/chrome, and in-world tags can name in-game crews — a social-memory tie-in, not just paint |
| Chewing gum — **GAP, do not source** | — | — | a dark ellipse at 0.9 roughness; one line of decal generator |

Poly Haven has NO decal category — confirmed absent; do not wait for it.

## C. Vehicles (boxy 80s/90s)

| pack | fetch | licence | contents |
|---|---|---|---|
| Kenney Car Kit 3.1 (owned) [URL-IN-USE] | already in repo | CC0 | sedan/hatchback/van/delivery/truck/taxi + **15 debris parts** (bumper, door, tire) — stripped/crashed cars for a crime game |
| **OGA Free Low Poly Vehicles Pack** [PAGE-CONFIRMED] | scrape `opengameart.org/content/free-low-poly-vehicles-pack` | CC0 | sedan, hatchback, van, taxi, bus, truck+trailer, pickup, limo, 4 police variants — separated wheels suit TrafficSim |
| **Quaternius Public Transport** via OGA mirror [PAGE-CONFIRMED] | scrape `opengameart.org/content/lowpoly-public-transport` | CC0 | 12 vehicles incl. THE BUS — repaint to regional livery |
| OGA Low Poly Vehicles / 3D Vehicles packs [PAGE-CONFIRMED] | scrape pages | CC0 | estate car ("wagon" — very 80s Britain), lorries, untextured clay variants |
| KayKit cars [FETCHED] | with the KayKit clone | CC0 | hatchback, sedan, stationwagon, taxi, police — separate wheels |
| Quaternius Cars Pack | via `poly.pizza/bundle/Cars-Bundle-FE5IWe6OMk` scrape | CC0 | 8 semi-realistic 2018-era shapes (boxier than modern) — NOT in the GitHub mirror (checked) |

## D. Buildings / facade

| pack | fetch | licence | contents |
|---|---|---|---|
| Kenney City Kit Commercial 2.1 [URL-IN-USE, sha256 F8B09B08…] | `kenney.nl/media/pages/assets/city-kit-commercial/a742d900eb-1753115042/kenney_city-kit-commercial_2.1.zip` | CC0 | shops + commercial buildings (we hold an older fetch — this is the current pin) |
| Kenney City Kit Suburban 2.0 [URL-IN-USE] | `kenney.nl/media/pages/assets/city-kit-suburban/2c871b7af2-1745479373/kenney_city-kit-suburban_20.zip` | CC0 | 40 houses, fences, driveways |
| **Kenney Retro Urban Kit 2.0** [zip audited by third party, sha256 19201CBC…] | scrape `kenney.nl/assets/retro-urban-kit` or OGA mirror | CC0 | 124 deliberately DATED urban models — potentially the best period fit; style-check one build before wholesale adoption (its low-res textures may fight our surfaces; the geometry may be the win) |
| Kenney Building Kit [URL-IN-USE] | `kenney.nl/media/pages/assets/building-kit/967871cedd-1743244741/kenney_building-kit.zip` | CC0 | modular walls/windows/roofs — pairs with GroundFloor |
| Quaternius buildings_pack_3 [FETCHED] | trebeljahr mirror, `buildings_pack_3/<File>.glb` | CC0 | 1–3 storey modulars with SIGN PLATES and balconies — blade-sign mounting points |
| Base Mesh chimneys + awnings [FETCHED] | (see A) | CC0 | roll-top chimney is the classic terrace pot |
| Polyhaven hero props [URL-IN-USE pattern] | `dl.polyhaven.org/file/ph-assets/Models/gltf/1k/<slug>/<slug>_1k.gltf` — `street_lamp_01`, `Barrel_01/02`, `wooden_crate_01`, `modular_urban_apartments_facade` (118K tris, hero only) | CC0 | photoreal scanned close-up props; slug case matters |
| Quaternius Downtown City MegaKit — **itch-only flow, EXCLUDED** from CI | needs one manual click at $0 | CC0 (audited) | 153 models incl. AC units, drains, kerbs. Only if Jafar clicks once and we cache it; do not build the pipeline around it |

## E. Sky HDRIs — Poly Haven, all CC0, pattern URL-IN-USE

`dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/<slug>_2k.hdr`

| hour | primary | alt |
|---|---|---|
| overcast noon | **belfast_open_field** (literally Belfast light) | overcast_soil_puresky |
| golden dusk | **industrial_sunset_puresky** (port-town dusk; URL verbatim in PlayCanvas examples) | evening_road_01 |
| night | **kloppenheim_04** (overcast night, distant glow — the British urban night) | satara_night (warm lamps), moonless_golf (darkest) |
| foggy morning | **misty_farm_road** | kloofendal_misty_morning_puresky |

md5 per file at `api.polyhaven.com/files/<slug>` for pinning.

## F. Trees / weeds (northern European — no palms anywhere above)

| pack | fetch | licence | contents |
|---|---|---|---|
| Quaternius nature_pack [FETCHED] | trebeljahr mirror | CC0 | **BirchTree 1-5 in live/AUTUMN/DEAD states** — dead birches by the gasworks are the palette |
| Quaternius simple_nature_pack [FETCHED] | trebeljahr mirror | CC0 | trees, bushes, **Grass1-3 tufts** — pavement-crack weeds, scaled and desaturated |
| Kenney Nature Kit [URL-IN-USE] | `kenney.nl/media/pages/assets/nature-kit/37ac38a37b-1677698939/kenney_nature-kit.zip` | CC0 | 330+ pieces in our geometry language |
| Base Mesh tree-pit railing [FETCHED] | (see A) | CC0 | the Victorian tree-guard read |

## Top fetches by impact (the V2/V3 fetch order)

1. Base Mesh selective raw fetch (~30 files) — most of street furniture in one already-verified pass.
2. Kenney Industrial — the docklands skyline.
3. ambientCG decal sweep via API — the entire grime layer in one CI step.
4. Poly Haven HDRI four-pack — all four hours.
5. Kenney Roads 2.0 — lampposts, barriers, fences.
6. KayKit clone — traffic lights, hydrant, bins + boxy cars.
7. OGA container pair — the port.
8. OGA transport + vehicles packs — the bus and the estate car.
9. Kenney Retro Urban — style-check first.
10. ambientCG masks (imperfections/scratches/moss/corrugated) — shutters and damp.

## Excluded, with reasons

itch.io flows (csrf+signed URL, no plain curl) · Sketchfab/Asset Store/
BlendSwap/Free3D/CGTrader/TurboSquid (login walls) · pngmart-class graffiti
PNGs (licence-laundering risk) · the google_poly GitHub mirror (2,300 GLBs,
opaque UUIDs, no manifest, CC-BY anyway) · HuggingFace dumps (blocked by
project rules) · Kimbatt/cc0-textures (torrents only).
