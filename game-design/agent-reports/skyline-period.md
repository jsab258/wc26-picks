> **STATUS — LOG, 2026-08-25. NOT CURRENT** once landed
> Written from local arithmetic and the landed `36b90c9` stills. Nothing in
> here has been through a Windows build. Supersede or delete once
> `skylineKinds` / `skylineFootGap` / `skylineByEdge` land in a verdict.

# The skyline is period, and it stands on something

## What was wrong, and it was one fault wearing two faces

`BuildSkyline` placed 34 slots on a CIRCLE of radius 250–428m about the
world origin. The town is not round: `StreetMap.BoundsOf` over all seven
districts gives x −430..344, z −184..179, and the ground slab is that plus a
40m shoulder — a rectangle **854m wide by 443m deep**, centred (−43, −2.3).
Nothing related the two.

Replaying the old arithmetic in Python against those bounds (`StableHash`
reproduced exactly, 34 slots, `dir.z < −0.55` dropped):

    standing 23   on ground 15   OFF GROUND 8

`skyline=23/23` in the landed verdict confirms the 23. All eight off-ground
slots are on the **north** side, at z 223..352, beyond the ground's z edge of
219.4. Two more (slots 25 and 26, at (−317,−24) and (−270,29)) land INSIDE
the Exchange's block rectangle — which `SimDirector`'s own vantage note had
already recorded as "a WORLD fault and it is not fixed here".

That is why the districts disagreed. It is not a global offset and a
correction that shifted everything would have sunk the districts that were
already right:

| frame | looks | slots it faces | ground under them |
|---|---|---|---|
| `district_hook` | towers hang | 0–4, 31–33 (z 223..352) | none — past z 219.4 |
| `district_copper` | towers hang | same north group | none |
| `district_gullwing` | towers **seated** | 9,10,11 (x 258..358, z −53..−155) | yes — inside the rect |

The ground rectangle is 854 wide and 443 deep, so a ring of one radius is
inside it on the long axis and outside it on the short one. East and west
stood; north hung.

**Size of the detachment, measured rather than eyeballed.** `TourVantage`
puts the district eye at y=14 looking at y=1.6 from 34m away — a 20° downward
pitch; at 720 lines and a 60° vertical field that is 12 px/degree, so the
horizon line sits at y≈120. From the hook eye the ground's far edge is ~253m
away and projects at atan(14/253)=3.17° below the horizon, y≈158. A block at
300m that WAS seated would project at 2.67°, y≈152. The hanging blocks'
feet sit at the horizon, y≈115..140. So the sky band between foot and
ground edge is **roughly 20–40 px**, which is the same order as the 25 px
the original finding measured in `district_copper`. The visually enormous
gap — hundreds of pixels — is between the feet and the ROOFTOPS below them,
not between the feet and the horizon; both are real, only one is a length
this arithmetic can predict.

## What the horizon is made of now

Checked before writing geometry, not after: `tools/prop-reach.py` lists seven
kits, `tools/prop-dimensions.py` measures every model in them. **No kit on
disk contains a crane, a gasholder, a spire or a slab block.** What it does
contain is 20 `city-kit-industrial` buildings (squat wide masses, 208×147 and
132×73 — mills and sheds), four chimneys (20×100 to 100×170) and
`detail-tank` (85×42), which was the one model in that kit no line of the
Game layer named.

| kind | source | count (offline replay) |
|---|---|---|
| `works` | kit — `city-kit-industrial_building-a..t` | 8 |
| `stack` | kit — `city-kit-industrial_chimney-*` | 5 |
| `tank` | kit — `city-kit-industrial_detail-tank` | 1 |
| `spire` | primitive composite | 3 |
| `slab` | primitive composite | 2 |
| `crane` | primitive composite, shared with the quay | 1 |
| `gasholder` | primitive composite, shared with the quay | 1 |

14 of 21 composed from fetched models, 7 from primitives.

Gone: `city-kit-commercial_low-detail-building-a/b/c`, three slim 50×200 to
50×225 towers with curtain-wall banding — the silhouette of a contemporary
financial district, arrived at because they were the first models that fitted
a height target.

**No second crane system.** `MakeCrane` is `BuildLandmarks`' own quay-crane
recipe lifted out unchanged; `BuildLandmarks` now calls it at k=1 and the
three wharf cranes are bit-identical, part names included
(`Crane_2_tower_up` is still 1.9m square at x36 z−174 spanning y10..18, which
three `SimDirector` comments quote as a fixture). Same for `MakeGasholder`
and the goods-edge gasometer.

**Heights are real-object ranges**, written into the switch: a level-luffing
dockside crane 30–35m to the cab, a mill chimney 30–60m and a works stack
80–100m, an industrial storey ~4m over 4–8 floors, a bulk tank 10–20m, a
four-lift gasholder frame ~40m, a parish spire 30–45m, a council block
12–21 storeys of 2.7m.

**The mix is a judgement and says so.** Two twelve-entry arrays. The DRAW,
though, was chosen by printing the series: `StableHash` is a 31-multiplier
over strings differing only in their last characters, so most divisors
collapse the mix — `h/13%12` gives 9 slabs and no spires at all,
`h/50000%12` gives 10 spires and no works. `h%12` is the one that spreads.
`skylineKinds` is the instrument that lets the next run re-weight on
evidence.

## The band, and the water

The band is now an **offset outline of the town's own bounds**: 120m beyond
the last street for the near rank, out to 315m for the far one, the same
standoff in every direction. Slots walk the perimeter by LENGTH rather than
by angle, because equal angular steps around a 1014×603m rectangle crowd its
short ends.

**The south edge carries nothing — that is the sea**, and the quay cranes are
the silhouette there. Dropping the south edge is not sufficient, and this is
the part that nearly landed wrong: the east and west edges run from z+299 down
to z−304, and everything below the shore is water. Both halves of the test
ship — the S edge is skipped, and any slot with `at.z < apronMinZ + 55` is
skipped too. 55m is measured: the widest thing the band can place is a
`works` at its 38m target off `building-s` (212×83.68×91.63 → 96m wide, up to
49m of AABB half-extent once the slot's yaw turns it).

**The apron** is one plane of the same concrete material the ground already
uses, 4cm below it so the two cannot z-fight, spanning x −830..744 and z
**−224..579**. Its south edge is `GroundMinZ` — read off the slab as it is
built, not recomputed, because two implementations of one rectangle is how
the band came to have no relation to the ground in the first place. Replayed
offline with each kind's worst-case post-yaw footprint: **no block's
footprint leaves the apron**.

## The instrument

Four keys, arithmetic and formatting in `Ledger.Core.Skyline` where the tests
run:

    skylineKinds=[crane:1,gasholder:1,slab:2,spire:3,stack:5,tank:1,works:8]/n21
    skylineFootGap=<worst>/<median>/n21
    skylineFootWorstAt=Skyline_0_works@-31,294
    skylineByEdge=[N:11/11,E:5/5,S:0/0,W:5/5]

`skylineFootGap`'s worst is the largest deviation **in either direction**,
signed and unbounded — a block sunk 4m is as wrong as one hanging 4m, and a
raw maximum would report 0.00 for the first. No bound, no gate; the series
comes first.

**And it could not have found this fault on its own**, which is why
`skylineByEdge` ships beside it: every hanging block WAS seated at y=0
exactly. The ground simply stopped. `skylineByEdge` is seated/standing per
compass edge, all four printed every run — per EDGE and not per district
because that is the axis the fault varied on, and a per-district figure would
have attributed a placement fault to whichever camera happened to face it.

## Two things fixed on the way past

- Both the scale and the seating read `GetComponentInChildren<Renderer>()`,
  which returns ONE renderer; on a multi-part mesh that measures a part and
  seats the whole by it. `TotalBounds` unions them.
- The haze repaint lived inside the kit branch only. It is one call outside
  both branches now, so a third branch cannot miss it.

## Not done, and named

- **`skylineFit` has no landed value under the new spacing.** The band's slot
  is one number (95.1m) instead of an arc that changed with radius, so the
  1.71× ambiguity is gone, but 1.76 was the last reading under the old
  divisor and the new one is not comparable. Read the series before anyone
  quotes a fit number again.
- **The apron has a collider**, so `groundMask` rays hit it and report ground
  where the frame shows ground. That is deliberate — a collider-less apron
  would make the instrument report sky over visible land — but it means the
  ground-mask numbers move, and by how much is a landing question.
- **`city-kit-suburban` is still entirely unreached** (13 models). Not this
  item's business; it was already on the board.
