# Tour cameras re-sited: `district_gullwing` and `district_downtown`

> **STATUS — LOG, 2026-08-24. NOT CURRENT** once the next Windows build lands
> and replaces these predictions with readings. Builder report
> (engine-specialist) for decision 1 item (b) in
> `decisions-2026-08-24-shadow-gap-and-template-sync.md`. Nothing here is
> committed; the tree change is `SimDirector.cs` only.

## What changed

One file, `ledger/Assets/Scripts/Game/SimDirector.cs`, +199/-19:

| line | what |
|---|---|
| 10032 | `int _tourResited, _tourResiteAsked;` — the re-site's own denominator |
| 10052-10171 | the reasoning, the measurements and the POSE REGIME DECLARATION, on `DistrictTour` |
| 10183 | the loop body now calls `TourVantage(d, out var eye, out var look)` — `CentreOf` and the eye/look arithmetic moved into it |
| 10240-10275 | `TourVantage` — one placement rule, five districts unchanged, two re-sited |
| 14476 | `tourResited={n}/{m}` on the done line |

Five vantages are byte-identical in effect: `CentreOf`, 34m south, 14m up,
aimed at 1.6m. Nothing else in the file moved.

## Why those two frames photograph nothing (measured, not guessed)

Both stills were opened first (rule 4). `district_gullwing` is a dark facade
at arm's length; `district_downtown` is one unlit surface with a sliver of
skyline. The landed b88adbb rows say the same thing numerically: meanLuma
0.154 and 0.096 at a dry noon against 0.42-0.61 for the other five, with
`lumaThirds` flat at 0.071/0.082/0.063 and 0.090/0.090/0.078.

The cause is neither lighting nor the districts. It is
`WorldBuilder.BuildSkyline`: its ring radius is `250 + 22*(0..6) + (0|46)` =
250..428m, and the Exchange's middle crossing is 301m from the origin while
Gullwing's is 312m — both inside the band. Replaying that function's own
deterministic hash, and scaling each picked model by its measured bounds from
`tools/prop-dimensions.py` (FBX pivots checked to be XZ-centred, not assumed:
`building-m` lo/hi -65.8..65.8 x, -85..85 z; `building-r` -124.2..124.2 x,
-63.6..63.6 z):

| slot | model, scaled to 34m tall | footprint |
|---|---|---|
| 11 | `city-kit-industrial_building-m` | 29.5 x 38.1m at (277.7,-154.9) → x 262.6..292.8, z -174.2..-135.6 |
| 25 | `city-kit-industrial_building-r` | 60.6 x 31.0m at (-317.1,-24.5) → x -348.4..-285.8, z -42.1..-6.9 (4° yaw) |

**Gullwing's middle crossing (275.2,-147.2) is inside slot 11**, and the old
eye at (275.2,-181.2) stood 7.3m off its south face. **The old downtown eye
(-301.0,-29.4) stood inside slot 25's footprint.** Nearest skyline mass to
each of the other five crossings: Fairview 44.0m, the Parade 53.0m, Copper Row
161m, Ironside 240m, the Hook 263m — which is why five of seven are fine.

**This is a world fault, not a camera fault, and it is NOT fixed here.** The
skyline ring stands on top of two districts; re-aiming a camera is the
evidence for that item, not its repair. It belongs on the queue as a
`BuildSkyline` exclusion (a slot whose footprint overlaps a district's
`BoundsOf` box should move outward or be dropped, with a count printed so the
drop cannot read as clean).

## How the new vantages were chosen

By simulating `ShotSightlines` itself — the same 84-ray (12x7) grid, the same
120m cap, the same 60° vertical FOV at 16:9 — against a box model of the
world: block rectangles from `StreetMap`'s own construction (avenue lines
scaled ×2.15/×1.15, 8m carriageways, 2.6m setback), terrace rows at the
district's own depth and height family, plus the skyline masses above.

**The accepting case is the landed data** (b88adbb `frames.tsv`), and the
model reproduces five of the seven rows:

| row | landed near/mid/far/depth | model |
|---|---|---|
| hook | 0.00 / 0.00 / 0.43 / 23.6 | 0.00 / 0.00 / 0.33 / 26.7 |
| copper | 0.00 / 0.00 / 0.05 / 28.3 | 0.00 / 0.00 / 0.05 / 28.2 |
| strip | 0.00 / 0.00 / 0.14 / 26.4 | 0.00 / 0.00 / 0.10 / 26.7 |
| fairview | 0.00 / 0.00 / 0.32 / 28.4 | 0.00 / 0.00 / 0.31 / 28.1 |
| downtown | 0.00 / 0.00 / 0.70 / 15.9 | 0.00 / 0.00 / 0.71 / 15.4 |
| ironside | 0.00 / 0.25 / 0.01 / 32.7 | 0.00 / 0.00 / 0.33 / 27.5 (legacy sheds modelled crudely) |
| gullwing | 0.00 / 0.00 / 0.25 / 27.9 | 0.00 / 0.00 / 1.00 / 9.2 (over-counts the shed) |

The two misses are both about masses the model treats as solid: the fetched
sheds are hollow meshes and Unity does not return backface hits, so rays pass
through them. Both new vantages have no shed in front of them, so their
predictions rest only on the district geometry the model reproduces well.

All 24 crossing/approach combinations per district were scored. The chosen two:

**downtown** — Exchange Street × Court Street (`downtown_j1_2`, -365.5,39.1),
eye 34m south at (-365.5, 14, 5.1), yaw 0.
- keeps the north-looking pose of the other five, so the sun-relative geometry
  does not move (noon azimuth is due south, elevation 52°, per
  `GameController.UpdateSun`);
- two-sided: the corridor runs between block x[-426,-369.5] and block
  x[-361.5,-305], building lines 6.6m either side of the carriageway;
- slot 25's nearest face is 14.1m BEHIND the eye and 18.1m to its right — out
  of frustum — and its 26.6m noon shadow falls east of the corridor (x
  -351..-291 at 12:30 azimuth), not on it;
- rejected sibling: the same street one crossing south (eye -365.5, -29.4) has
  the shed 18m to the right and 20m ahead, i.e. in frame.

**gullwing** — Promenade × Bathhouse Row (`gullwing_j0_1`, 206.4,-147.2), eye
34m east at (240.4, 14, -147.2), yaw 270.
- the approach turns because Gullwing's ONLY two-sided street is Bathhouse
  Row: the district has 3×3 crossings, its one north-south avenue with blocks
  on both sides is the middle one, and slot 11 is standing on it;
- looking west, the terraces of blocks x[210.4,271.2] (rows at z -163.8..-153.8
  and -140.6..-133.2 after setback) flank the road for 27m;
- slot 11 is 22.6m BEHIND the lens and slot 10 is 48.5m behind — nothing with
  a forward component;
- rejected sibling: north up Promenade (0.19/41.0) is one-sided — a terrace on
  the right and open ground on the left.

## Predicted next landing (predictions, not measurements)

| row | camX / camZ / camYaw | near | mid | far | depth |
|---|---|---|---|---|---|
| district_gullwing | 240.4 / -147.2 / 270 | 0.00 | 0.00 | 0.30 ±0.10 | 25-30m |
| district_downtown | -365.5 / 5.1 / 0 | 0.00 | 0.00 | ~0.71 | ~15m |

Downtown's pair is **deliberately the same as the broken row's**: 12-22m
offices 6.6m from a 14m lens fill the near bands exactly as a wall does, so
the sight-line pair structurally cannot answer this question and must not be
read as if it had. The numbers that move are photometric —

- gullwing meanLuma up from 0.154 toward the five's dry-noon band (0.42-0.61),
  `lumaThirds` no longer flat;
- downtown meanLuma up from 0.096 (brightPct 0.50 today) with a visible road
  strip and a thirds split. **Fork:** if it lands under 0.15 with flat thirds
  again, the shed was not the cause and the next question is the Exchange's own
  massing and light.

Also predicted: `tourResited=2/2`; both rows leave `tourDepthBy`'s short end
(downtown's 15.9 was the shortest of the seven); `shotNudges` unchanged on the
tour, since near/mid at 0.00 keep `ShotBlockedAt`/`ShotMidBlockedAt` from
firing — if the tour's nudge count moves, that assumption was wrong and the
frame was not taken from the vantage placed here.

For `ref-bench`: both rows should become READABLE under the low-content
annotation being built in parallel — their ground-band statistic should rise
above the five references' floor. Whether their `shadowRatio` then lands
inside 0.157..0.388 is the open question decision 1 named; nothing here should
be read as answering it.

## The regime break, stated

`district_gullwing` and `district_downtown` before this commit and after it
are **not comparable** — different vantage, and for gullwing a different yaw.
Everything keyed to those two rows resets: `ref-bench`'s pose-stable series
for them, `frame-drift`'s district rows (which will read this landing as
enormous drift, correctly), their `tourDepthBy` entries, and
`district_downtown`'s `districtGround` probe. Read the next landing as a new
baseline, not as a delta. The other five are untouched and keep their history.

## Verified locally / unverifiable until CI

Green: five name-shape lints (`lint-shadow` 274 types/87 files, `lint-nested`
248 Core types, `lint-static` 522 bodies, `lint-filetype` 183 files,
`lint-namespace` 183 files), `verdict-emit-dupkeys` (0 same-line duplicates
over 109 log calls), and `python3 ledger/verify.py` to GREEN
(`ledger/.verify-footer` written; 3761 CoreTests, 0 shape errors, 0 raw avenue
reads).

**Unverifiable until CI.** ShapeCheck is reference-independent, so the Unity
API surface here — `StreetMap.Node` returning a `StreetNode`, the transform
writes, `Vector3` construction — is first compiled by the Windows build. And
no local tool renders a frame: every number in the prediction table is a box
model's output, not a reading. CI must confirm, in `runs/<sha7>.txt` and
`frames.tsv`:

1. `tourResited=2/2` — anything less means a junction id did not resolve and
   that row fell back to the broken middle crossing;
2. `district_downtown` camX -365.5 camZ 5.1 camYaw 0 and `district_gullwing`
   camX 240.4 camZ -147.2 camYaw 270 in `frames.tsv`;
3. meanLuma and lumaThirds on those two rows (the proving numbers);
4. `tourShots=7` still, and the tour's `shotNudges` unmoved;
5. the two stills opened by eye before any gate is read.
