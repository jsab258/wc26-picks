> **STATUS — LOG, 2026-08-25. NOT CURRENT** once wired.
> Survey and measurement only; nothing in this report is wired. The next
> dispatch executes it. Supersede or delete when the placements land.

# Placement plan — city-kit-roads and city-kit-suburban

Every model in the two kits that no line of the Game layer names. Measured
with `tools/prop-dimensions.py` from each FBX's own vertex data, not from a
manifest. Verdicts are mine; the numbers are the files'.

## The count is 58, not 60

`prop-reach` reads roads 47/2 named/**45 unused** and suburban 13/0/**13
unused**. 45 + 13 = 58. (`prop-reach`'s headline 149 is the ALL-KITS total
and is not either of these.)

## The instrument: I could not make it over-report, and I found a hole

Rule 3 says suspect the ruler. `prop-reach` matches normalised model keys
against Game-layer string literals, so a key built from a variable, a folder
scan or a computed name would read as unused when it is not. I opened every
dynamic call site rather than grepping past it:

| site | how the key is built | route `prop-reach` sees |
|---|---|---|
| `WorldBuilder.cs:2714` benches | `benches[pick]`, array of whole literals | exact |
| `WorldBuilder.cs:3149` bins | `bins[binPick]`, array of whole literals | exact |
| `WorldBuilder.cs:3829` skyline | `models/stacks/industrial[h % n]`, arrays of whole literals | exact |
| `WorldBuilder.cs:2287` cars | `"car_kit_" + stem`, literal prefix + literal stem | prefix |
| `AssetLibrary.cs:1132` | `Resources.Load("Props/Prop_" + key)` | the single funnel; composes a CALLER's key, does not scan a folder |

There is no folder-wide load anywhere in the prop path, so no model can be
reached without some literal naming it. **The unused label holds for all 58.**

**But its accepting case is 63% blind, and blind on exactly this family.**
`prop-reach` validates itself against `kitAlbedo`, the verdict's ground-truth
listing of keys the sim actually instantiated — a good idea, and the tool
handles the cap honestly (it drops `+Nmore` rather than parsing it as a name).
The landed verdict reads `kitAlbedo=[...24 keys.../+14more]`, so the check saw
24 of 38. The 24 visible are all `base_mesh_*`, `oga_vehicles_*` and
`car_kit_*`: **every `city_kit_*` key the last run placed is behind the cap**,
so the cross-check gives zero independent confirmation for the one kit family
this survey is about. It got the right answer here because the code reading
above is stronger evidence than the cross-check. It will get worse the moment
this plan lands — 19 new keys against a listing that already truncates at 24.

**Raise the cap, or emit a second `kitKeys=[..]` line carrying names only
(no albedo), before any of these placements is measured.** Otherwise the
proof-of-placement for most of the new work is invisible in the only channel
that can be read here.

## Scale: 1 FBX unit is about 0.074 m, derived not assumed

These files are not in metres. Two independent, code-driven anchors:

- `WorldBuilder.MakeLamp` scales `light-curved` to a **5.2 m** height target;
  measured height **67.50 u** → 0.0770 m/u.
- `TrafficHost` scales `traffic-light` to a **3.6 m** target; measured height
  **51.50 u** → 0.0699 m/u.

They agree within 10%. Taking **0.074 m/u** and checking it against four
real-world objects in the same kit: cone 9.38 u → 0.69 m (real 0.5–0.75);
works barrier 22.5 u long → 1.67 m (real ~2.0); road tile 100 u → 7.4 m (a
two-lane street with kerbs); fence 27 u → 2.00 m. Consistent throughout, and
the suburban kit shares the unit (house frontages land at 9.5–13.5 m).

**Both call sites rescale on instantiate anyway, so the load-bearing number is
the PROPORTION, not the absolute** — which is what decided the two most
valuable calls below (the nameplate and the terrace rejection).

## Verdicts — 19 PLACE / 6 HOLD / 33 REJECT

Metres are the measured units x 0.074. `w/h/d` is the FBX's own bounds.

### city-kit-roads — 45 unused (14 PLACE / 2 HOLD / 29 REJECT)

| model | verts | w x h x d (u) | w x h x d (m) | verdict | where / why |
|---|---:|---|---|---|---|
| `construction-barrier` | 32 | 13.5 x 13.0 x 22.5 | 1.00 x 0.96 x 1.66 | **PLACE** | 1.67m long x 0.96m high works barrier -- the shape of the British red-and-white pedestrian barrier. 2-4 per cluster, plus a run closing the market street to traffic. |
| `construction-cone` | 48 | 7.5 x 9.4 x 7.5 | 0.56 x 0.69 x 0.56 | **PLACE** | 0.56 x 0.69 x 0.56m -- a real cone is 0.5-0.75m, so this is 1:1 and needs no rescale. Period-neutral, 48 verts, and the cheapest density win on the board. 3-8 per roadworks cluster, ~6-10 clusters: roadworks on Copper Row, dock loading bays, the market's closed lane. |
| `construction-light` | 88 | 7.5 x 23.4 x 7.5 | 0.56 x 1.73 x 0.56 | **PLACE** | 1.73m works lamp on a stand. Pairs with the barrier and, unlike the other two, it EARNS ITS PLACE AT NIGHT: an amber point source at eye height is exactly what the night frame is short of, and it is the only new light source in either kit. 1-2 per cluster. |
| `light-curved-cross` | 137 | 40.0 x 67.5 x 40.0 | 2.96 x 4.99 x 2.96 | **PLACE** | Four-arm swan-neck, 5.0m, 2.96m arm span. Old-town crossroads islands only, ~3-5. Same MakeLamp path. |
| `light-curved-double` | 78 | 5.0 x 67.5 x 40.0 | 0.37 x 4.99 x 2.96 | **PLACE** | Twin-arm swan-neck on one column, 5.0m. Dock approach road and the Exchange's central street, where a single arm lights one kerb only. ~8-12. Reuse MakeLamp exactly: 5.2m height target, near-black green paint, colliders stripped. |
| `light-square` | 38 | 5.0 x 60.0 x 23.8 | 0.37 x 4.44 x 1.76 | **PLACE** | Square sodium lantern head, 4.4m. Britain in the 80s/90s ran a MIX: cast swan-necks on old streets, square-head sodium on newer roads. This is the newer-district lamp -- Gullwing and the Exchange, ~10-14. One district lookup, no new code path. |
| `light-square-cross` | 80 | 42.5 x 60.0 x 42.5 | 3.14 x 4.44 x 3.14 | **PLACE** | Four-arm square head, 4.4m. Newer-district junctions, ~2-4. Completes a 2x3 district table (curved/square x single/double/cross) driven off DistrictAt. |
| `light-square-double` | 57 | 5.0 x 60.0 x 42.5 | 0.37 x 4.44 x 3.14 | **PLACE** | Twin square head, 4.4m. Newer-district dual-frontage streets, ~5-8. |
| `road-bend-barrier` | 68 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | wrong system: 7.4m modular deck tile with a moulded kerb lip; our roads are continuous ribbons with 2K asphalt |
| `road-bend-square-barrier` | 28 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | same tile grid; adopting it downgrades road surface to a flat palette colormap |
| `road-crossroad-barrier` | 64 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | tile grid; StreetMap junctions are not on a 7.4m module |
| `road-curve-barrier` | 104 | 200.0 x 8.0 x 200.0 | 14.80 x 0.59 x 14.80 | **REJECT** | 14.8m tile; would force the whole road builder onto a grid |
| `road-curve-intersection-barrier` | 89 | 200.0 x 8.0 x 200.0 | 14.80 x 0.59 x 14.80 | **REJECT** | as above |
| `road-driveway-double-barrier` | 44 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | tile grid, and a double driveway crossover is a US suburban form |
| `road-driveway-single-barrier` | 30 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | tile grid |
| `road-end-barrier` | 16 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | tile grid |
| `road-end-round-barrier` | 76 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | tile grid; a rounded cul-de-sac head is US-suburban |
| `road-intersection-barrier` | 40 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | tile grid |
| `road-roundabout-barrier` | 385 | 300.0 x 8.0 x 300.0 | 22.20 x 0.59 x 22.20 | **HOLD** | 22.2m island: Britain has roundabouts and Meridian has none, but this tile needs the road builder to cut a hole for it AND our asphalt to run up to it. Named dependency: a StreetMap junction type that reserves a circular parcel. |
| `road-side-barrier` | 16 | 131.0 x 8.0 x 100.0 | 9.69 x 0.59 x 7.40 | **REJECT** | tile grid |
| `road-side-entry-barrier` | 120 | 131.0 x 8.0 x 100.0 | 9.69 x 0.59 x 7.40 | **REJECT** | tile grid; slip-road geometry, no slip roads here |
| `road-side-exit-barrier` | 120 | 131.0 x 8.0 x 100.0 | 9.69 x 0.59 x 7.40 | **REJECT** | tile grid; slip-road geometry |
| `road-sign-empty` | 24 | 5.0 x 47.5 x 5.0 | 0.37 x 3.52 x 0.37 | **PLACE** | Bare 3.5m post, 0.37m square section, no plate. The universal mounting post for every road-sign-object-* plate below, and a standalone post in its own right. ~20-30. |
| `road-sign-empty-hanging` | 64 | 9.0 x 47.5 x 29.5 | 0.67 x 3.51 x 2.18 | **PLACE** | Post with overhanging arm and a blank hanging plate, 3.5m x 2.18m reach. THE British port-town object: pub signs, ship chandlers, the harbourmaster's board. ~12-20 on shopfronts and the dock gate. Depends on the existing name-painting path (ShopNamesPainted) to letter the plate. |
| `road-sign-object-stop` | 36 | 7.7 x 12.6 x 12.6 | 0.57 x 0.93 x 0.93 | **REJECT** | Octagon. The shape is carried by GEOMETRY, not lettering (the kit's texture is a flat palette), so an unlettered red octagon on a British street still reads American. Britain gives way on an inverted triangle. |
| `road-sign-object-street` | 32 | 4.3 x 6.0 x 19.2 | 0.31 x 0.44 x 1.42 | **PLACE** | Plate only: 1.42m x 0.44m x 0.31m -- a 3.2:1 blade, which is exactly a British street nameplate (typical UK plate ~1.2m x 0.3m). Wall-mounted at terrace corners and on low posts at junctions. ~1-2 per named street. Feeds the information moat directly: the game has named streets and no way to read a name off the street. |
| `road-sign-object-warning` | 36 | 7.7 x 13.4 x 13.4 | 0.57 x 0.99 x 0.99 | **PLACE** | Triangular plate, 0.99m x 0.99m face. Mounts on existing lamp columns and on road-sign-empty. Dock gate approaches, yard entrances, the level crossing. ~8-12. VERIFY IN THE FIRST FRAME: the triangle must point UP (British warning). If it points down it is a US yield sign and gets pulled -- bounds cannot tell the two apart and I did not guess. |
| `road-sign-stop` | 60 | 7.8 x 49.4 x 13.8 | 0.57 x 3.66 x 1.02 | **REJECT** | Same octagon on a post. Country grounds. |
| `road-sign-street` | 88 | 19.6 x 47.5 x 19.6 | 1.45 x 3.52 x 1.45 | **REJECT** | Tall crossblade nameplate on a 3.5m pole -- the American form. The British nameplate is the road-sign-object-street PLATE above, wall-mounted or on a low post. Rejecting the pole and placing the plate is the whole finding. |
| `road-sign-warning` | 60 | 7.7 x 49.9 x 14.7 | 0.57 x 3.69 x 1.09 | **PLACE** | Same triangle on its own 3.7m post, for sites with no column to borrow. ~4-6. Same point-up verification. |
| `road-slant-barrier` | 16 | 100.0 x 33.0 x 100.0 | 7.40 x 2.44 x 7.40 | **REJECT** | 2.4m road ramp; Meridian is a flat tidal port |
| `road-slant-curve-barrier` | 214 | 200.0 x 58.0 x 100.0 | 14.80 x 4.29 x 7.40 | **REJECT** | 4.3m ramp, flat town |
| `road-slant-high-barrier` | 16 | 100.0 x 58.0 x 100.0 | 7.40 x 4.29 x 7.40 | **REJECT** | 4.3m ramp, flat town |
| `road-split-barrier` | 262 | 100.0 x 8.0 x 200.0 | 7.40 x 0.59 x 14.80 | **REJECT** | dual-carriageway split; no dual carriageways in a port town's street plan |
| `road-square-barrier` | 16 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | tile grid |
| `road-straight-barrier` | 16 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | tile grid |
| `road-straight-barrier-end` | 12 | 100.0 x 8.0 x 100.0 | 7.40 x 0.59 x 7.40 | **REJECT** | tile grid |
| `road-straight-barrier-half` | 16 | 100.0 x 8.0 x 50.0 | 7.40 x 0.59 x 3.70 | **REJECT** | tile grid |
| `sign-highway` | 114 | 13.2 x 70.7 x 100.0 | 0.98 x 5.23 x 7.40 | **REJECT** | 7.4m-wide gantry board, 5.2m tall. Meridian has no motorway and no dual carriageway; an interstate-scale green board over a town street is US furniture. |
| `sign-highway-detailed` | 166 | 13.2 x 82.2 x 100.0 | 0.98 x 6.08 x 7.40 | **REJECT** | 6.1m tall gantry board. Same. |
| `sign-highway-wide` | 90 | 13.2 x 70.7 x 100.0 | 0.98 x 5.23 x 7.40 | **HOLD** | 7.4m x 5.2m board -- the ONE right size for a port entrance gantry over the dock gate, one instance. Named dependency: a re-lettered face (the kit ships a flat palette, so the board is blank) and a dock-gate anchor in WorldBuilder. Right shape, wrong signage until then. |
| `traffic-light-hanging` | 136 | 11.8 x 50.9 x 29.5 | 0.87 x 3.77 x 2.18 | **REJECT** | Signal on an overhanging mast arm. Britain mounts signals on vertical posts at the stop line; the mast-arm-over-the-junction is unmistakably North American. |
| `traffic-light-object-hanging` | 72 | 9.8 x 14.3 x 6.1 | 0.72 x 1.06 x 0.45 | **REJECT** | Head with a hanging mast bracket. Same country grounds. |
| `traffic-light-object-horizontal` | 80 | 9.8 x 6.1 x 14.3 | 0.72 x 0.45 x 1.06 | **REJECT** | Horizontal 3-aspect head, 1.06m long x 0.45m tall. Horizontal signals are American; Britain is vertical only. |
| `traffic-light-object-vertical` | 84 | 9.8 x 14.3 x 6.1 | 0.72 x 1.06 x 0.45 | **PLACE** | Vertical 3-aspect head, 0.45m x 1.06m, no pole. THE British signal form, and the gap is specific: TrafficHost places one whole pole+head per approach, where a British junction has a primary head at the stop line AND a secondary at low level on the near post. Mount on the existing Signal_ posts and on road-sign-empty. ~2 per signalled approach. |

### city-kit-suburban — 13 unused (5 PLACE / 4 HOLD / 4 REJECT)

| model | verts | w x h x d (u) | w x h x d (m) | verdict | where / why |
|---|---:|---|---|---|---|
| `building-type-a` | 707 | 130.0 x 83.4 x 102.8 | 9.62 x 6.17 x 7.61 | **REJECT** | 9.62m frontage on a 1.26:1 near-square plan, 6.17m tall (h/w 0.64 -- squat). Meridian's terrace parcels are ~6x12m, a 1:2 plan: narrow frontage, deep. This is the opposite proportion and it is 3.6m too wide for the parcel before any styling question. Country grounds too: a wide, squat, shallow-roofed detached mass is a US suburban house, not a British terrace or villa. |
| `building-type-b` | 1088 | 182.8 x 113.8 x 114.0 | 13.53 x 8.42 x 8.44 | **REJECT** | 13.53m frontage, 1.60:1 plan, 8.42m tall. Widest of the three and the furthest from a 6m parcel. Same country grounds. |
| `building-type-c` | 720 | 128.6 x 103.4 x 102.8 | 9.52 x 7.65 x 7.61 | **REJECT** | 9.52m frontage, 1.25:1 plan, 7.65m tall. Same as type-a. NOTE: Fairview is the villas district and is the one place a detached mass fits the plan -- but a British villa is a steep-roofed 8-9m ridge on a deeper plot, not this. The gap is real; it belongs on the quality ladder as a fetch, not filled with these. |
| `fence` | 56 | 47.5 x 27.0 x 7.5 | 3.52 x 2.00 x 0.56 | **PLACE** | 3.52m run, 2.00m high, 0.56m thick. At 2m solid this is a yard boundary / builder's hoarding, not a picket -- period-neutral and country-neutral in that form. Back-alley boundaries between terrace back yards (the alleys currently have nothing behind them) and dock yard perimeters in Ironside. ~40-60 runs. |
| `fence-1x2` | 104 | 87.5 x 27.0 x 43.8 | 6.47 x 2.00 x 3.24 | **PLACE** | 6.48m straight run, same 2.00m height. Longer alley and yard boundaries; fewer draw calls than two singles. ~20-30. |
| `fence-1x3` | 136 | 127.5 x 27.0 x 43.8 | 9.44 x 2.00 x 3.24 | **PLACE** | 9.44m straight run. Dock yard perimeter in Ironside, ~15-25. |
| `fence-1x4` | 168 | 167.5 x 27.0 x 43.8 | 12.40 x 2.00 x 3.24 | **PLACE** | 12.40m straight run -- one run per terrace back plot at our 12m parcel depth, which is a measured fit rather than a coincidence. ~15-25. |
| `fence-2x2` | 152 | 87.5 x 27.0 x 83.7 | 6.47 x 2.00 x 6.20 | **HOLD** | Pre-formed L/U enclosure, 6.48 x 6.20m footprint. That is a US back-yard footprint and our alley-side yards have never been measured. Named dependency: print the alley-side yard footprint from WorldBuilder, then decide -- if our yards are ~6m the L drops straight in and saves the corner-mitring the straight runs need. |
| `fence-2x3` | 184 | 127.5 x 27.0 x 83.7 | 9.44 x 2.00 x 6.20 | **HOLD** | 9.44 x 6.20m enclosure. Same dependency. |
| `fence-3x2` | 200 | 87.5 x 27.0 x 123.8 | 6.47 x 2.00 x 9.16 | **HOLD** | 6.48 x 9.16m enclosure. Same dependency. |
| `fence-3x3` | 232 | 127.5 x 27.0 x 123.8 | 9.44 x 2.00 x 9.16 | **HOLD** | 9.44 x 9.16m enclosure. Same dependency. |
| `fence-low` | 112 | 127.5 x 17.0 x 83.7 | 9.44 x 1.26 x 6.20 | **REJECT** | 1.26m-high L-shaped low fence on a 9.44 x 6.20m front-yard footprint. A painted low fence around a front lawn is the most American object in either kit; British front boundaries are low brick walls, railings or hedges. |
| `planter` | 120 | 40.0 x 17.7 x 30.0 | 2.96 x 1.31 x 2.22 | **PLACE** | 2.96 x 2.22m footprint, 1.31m tall -- a municipal concrete planter, not a domestic pot. Bang on period: British town centres pedestrianised their high streets through the 80s and filled them with exactly this, doubling as vehicle barriers. Market street and the Exchange forecourt, ~15-25. Also the only greenery in a grey town, which is what the GTA-bar frame decomposition keeps asking for. |

Keys are `city_kit_roads_<stem>` and `city_kit_suburban_<stem>`, dashes
normalised to underscores — `PropPrefab.Key` and `TryInstantiateProp` share
that rule, written twice, which is the shape this project keeps finding wrong
on the copy nobody looks at.

## Attribution

`tools/attribution-check.py` already covers both kits: `.fbx` is in its
`ASSET_SUFFIXES`, `ledger/Assets/Props` reports **197 asset file(s)**
attributed, and it asserts no asset lives outside a directory it knows about.
`Assets/Props/THIRD-PARTY.md` names both kits — CC0 1.0 from Kenney,
city-kit-roads 48 files, city-kit-suburban 14 files. **Nothing needs fetching
and nothing needs buying: every model in this plan is already on disk and
already attributed.** No new file extension is introduced, so the sweep's
suffix list needs no change.

## The numbers that would prove it is running (rule 6)

A placement plan with no proposed counter cannot be verified afterwards, and
this project once shipped ~40 of 61 APIs called by nothing. Each key below is
a WHOLE-RUN count and belongs on the **done line**, not the shot line, and
each ships its denominator so a zero cannot read as health. No spaces in any
value; bracketed lists for structure.

| key | statistic | what a zero would mean without the denominator |
|---|---|---|
| `lampVariants=N/5` | distinct lamp models instantiated, of 5 offered | "the district table never branched" and "only one lamp exists" look identical |
| `lampsByKind=[curved:N/curved_double:N/curved_cross:N/square:N/square_double:N/square_cross:N]` | per-kind whole-run counts | a variant silently missing from the fetch |
| `signPosts=N signPostsOffered=M` | posts placed / junction sites offered | no junctions vs. the post never loaded |
| `signPlates=N signPlatesOffered=M` | nameplate + warning plates mounted / mount sites | the mount path dead vs. no sites |
| `namePlatesPainted=N/signPlates` | plates that got lettering | a blank white blade reads as a fault in the frame; `ShopNamesPainted` is the shape to copy |
| `worksClusters=N worksProps=M` | roadworks clusters / props inside them | a cluster that placed nothing |
| `worksLampsLit=N/worksLamps=M` | works lamps EMITTING / placed | placed-but-dark is the whole point of this model |
| `secondaryHeads=N/signalPosts=M` | vertical heads mounted / signal posts existing | M>0 with N=0 is a dead mount path, and nothing else would say so |
| `yardFenceRuns=N yardFenceMetres=F` | runs and total metres | a run count alone cannot tell one 12.4m run from twelve 3.5m ones |
| `plantersPlaced=N plantersOffered=M` | placed / sites offered | — |

**And the one that binds all of them: every new key must appear in
`kitAlbedo`'s listing.** That is the reach-auditor's ground truth and the only
thing that proves the KIT MODEL is standing there rather than the fallback
primitive — every one of these call sites falls through to a box on a miss,
silently, which is how `city_kit_*_bench` missed for a week. See the cap
finding above: `kitAlbedo` truncates at 24 today.

## What this plan does NOT solve, for the ladder

Neither kit contains a British terrace, and the three suburban houses are the
wrong country and the wrong proportion for our 6x12m parcels (1.26:1 near-
square against our 1:2). Fairview is the villas district and is the one place
a detached mass fits the plan, but a British villa is a steep-roofed 8–9m
ridge, not a 6.2m squat box. **That is a named gap for the quality ladder — a
fetch, not a compromise.** Same for a GIVE WAY triangle: rejecting the STOP
octagon leaves British junction signage unrepresented.
