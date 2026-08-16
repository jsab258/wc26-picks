# The street spec — dimensions derived, not desired

> **STATUS — SPEC**, drafted 2026-08-16, unbuilt. The prerequisite for
> the topology re-plan: this document is written BEFORE any road moves,
> because the current map was built the other way round and the cost is
> measured (queue.md: ~110 parcel ceiling citywide). Validation gates at
> the bottom; nothing here is done until they pass.

## The principle

Every dimension derives from the BUILDING TYPOLOGY upward. A street's
width is what its buildings and traffic need; a block's depth is what
two building rows and a yard need; the grid pitch falls out of the
arithmetic. The current map inverted this — pitch first, buildings
squeezed into what remained — and the instruments priced the mistake:
one building per block edge, citywide.

## 1. Building typology (the ground truth everything derives from)

| type | frontage | depth | where |
|---|---|---|---|
| terrace house | 4.5–7m | 4.5–6m | residential streets everywhere |
| shop + flats over | 5.5–9m | 7–9m | high streets, market quarter |
| pub / corner premises | 8–11m | 8–10m | corners, one per few blocks |
| warehouse / shed | 12–30m | 10–16m | Ironside, backs elsewhere |
| villa | 8–11m | 8–10m | Fairview only, detached |
| yard between rows | — | 4–6m | inside every terraced block |

## 2. Block dimensions (derived)

Terraced blocks are RECTANGLES, not squares — long frontages on the
named street, short ends on the side streets. This is the single
biggest shape change from the current map, whose square blocks give
every street the same monotonous rhythm.

- **Block depth** = two rows + yard = 5.5 + 5 + 5.5 ≈ **16–19m buildable**
  (+ 2×2.6m setback ⇒ ~21–24m face-to-face).
- **Block length** = 5–10 parcels ≈ **35–70m** frontage.
- Copper Row runs shorter blocks (35–45m) for its older, denser read;
  Fairview and Gullwing longer (55–70m); the Hook in between.
- Ironside keeps bigger plots: 30–40m × 25–30m, sheds and yard walls.

## 3. Street taxonomy (UK-honest widths)

| type | carriageway | pavements | carries |
|---|---|---|---|
| high street / avenue | 9–10m (2 lanes + parking) | 3m each | buses, lights, shops, zebras |
| terrace street | 6.5–7.5m | 2m each | parked cars both kerbs, give-way ends |
| service lane / mews | 3–4m | none | bins, rear yards, no through traffic |
| the esplanade (Gullwing) | 7m | 6m promenade seaward | the front |

Grid pitch follows: avenue-to-avenue ≈ block length + carriageway
(≈ 45–80m by district) along the main axis; block depth + street
(≈ 28–34m) across. Roughly 2–4× today's pitch on the long axis —
which is where the missing building mass comes from.

## 4. Junctions, control, crossings (warrant rules, not sprinkles)

- **Lights** only where avenue crosses avenue near a core. Everything
  else: give-way paint on the minor arm (already built).
- **Zebras + belisha beacons** on pedestrian desire lines: outside the
  covered market, by bus stops, at school-run corners — placed by rule
  (near a place with footfall), not by hash (the current placement is a
  hash and says so honestly; the re-plan replaces it).
- **Corner radii**: tight (1–2m) on terrace streets — tight corners
  slow cars and read Victorian; generous only where buses turn.
- **One-ways**: none in v1. They multiply route-model risk for a feel
  gain fog mostly hides. Revisit with evidence.

## 5. Parking grammar (already built, restated as rules)

Single yellows on core commercial edges; unrestricted elsewhere;
half-on-kerb on any carriageway under 7m; never across a zebra, a
junction mouth, or a place doorway.

## 6. Migration contract (what the re-plan must NOT break)

- **Places**: each of the 61 keeps its street NAME and its relative
  position along that street; coordinates are recomputed from the new
  edge, never hand-guessed. A migration script derives old→new, and
  `massInRoad`/the places gate re-baseline in the same commit, stated
  in the message.
- **Node ids**: the founding Hook ids (`j1_1`…) are named in the bus
  circuit and tests. The founding cross keeps its ids; renames happen
  only where a node genuinely ceases to exist.
- **The bar** does not move. Act I happens in it.
- **Gates**: every spatial gate re-baselines explicitly in the re-plan
  commit, or the re-plan does not land.

## 7. Validation gates (in order, before any keep decision)

1. **Paper pass**: with the new tables, predicted `terraceParcels`
   ≥ 400 citywide (the counters already exist to check the prediction).
2. **One build**, judged at player height on `review_street.jpg`: an
   unbroken terrace run of ≥ 8 frontages in a single street view.
3. **Sim holds**: walkers, traffic, confabs, places gates green two
   consecutive runs; `offRoadWho` stays "none" or names a pre-existing
   culprit.
4. Only then: the old expression path retires.
