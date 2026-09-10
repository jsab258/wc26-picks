# Plans and elevations: Mickey's Cars on Quay Street

STATUS: SPEC. Station 1 of five for the cab-office option, written 2026-09-10.
Governed by `canon.md`, by D17, by `production/specs/asset-interface.md`, which
is the shape every number here has to fit, and by the licence allowlist.

THE NUMBERS DO NOT LIVE IN THIS FILE. They live in `data/cab-office.json`, they
are measured by `verify/check_cab_office.py`, and they are drawn by
`author/draw_cab_office.py`. This file says what was decided and why. If a
number here ever disagrees with the data file, the data file wins and the
disagreement is a defect in this file.

## 0. What D17 leaves standing, and it is most of it

D17 says: "The siting, the two bays and the fascia STAND. They are architecture
and they do not depend on what is served." It also VOIDS by name the beer
store, the pump clips, the cask line and the free-house question.

So the honest accounting of what changing the trade costs, item by item, is
short:

| what atlas-01 authored | under the cab office |
|---|---|
| the carcass, two bays, 12.0 x 8.0 m, 3.4 and 2.8 m storeys | UNCHANGED |
| the six front openings | UNCHANGED, and measured at 0.000 mm, 6 of 6 |
| the fascia band, the pilasters, the stallrisers, the cornice | UNCHANGED |
| the private stair, 19 risers, 18 goings at 0.240, landing 4.62 to 5.60 | CARRIED UNCHANGED |
| the whole flat above: bedroom, living room, book room, kitchen, bath | CARRIED UNCHANGED. D17 does not reach it. |
| the yard, the 1.8 m wall, the 1.2 m gate, the 2.4 m rear lane | CARRIED, widened from 6.0 to 12.0 because the premises doubled |
| the 1958 brick WC | CARRIED UNCHANGED, and it gets busier |
| the beer store, 1.935 x 2.085 | VOID by D17, and REFILLED as the money room |
| the counter, the back bar, the snug screen, the pump clip, the cask line | GONE, and replaced by a counter, a glazed screen and a radio shelf |
| the fascia LETTERING | one word added: MICKEY'S becomes MICKEY'S CARS |

THAT IS THE WHOLE BILL. Choosing the cab office throws away one counter, one
screen, one shelf and one pump clip, none of which is built, and keeps the
carcass, the stair, the flat, the yard, the WC and the frontage, all of which are
authored. A reader deciding between pub and cab office should price the change
at that and not at "a new building".

## 1. The layout, in one paragraph each

THE SOUTH BAY IS THE PUBLIC HALF. In at the shop door, a waiting room 4.70 m
wide and 3.20 m deep with a bench under the window, a coin box on the stair
partition, a price board and the council's street plan of the town on the wall.
Across the room, a counter 0.600 m deep with its top at 1.050 m, a glazed
screen above it to 2.100 m, a 0.30 by 0.25 m speaking gap at mouth height, and
a counter flap at the north end that is the only way through. Behind it the
control side: a chair, a writing ledge 0.270 m below the counter top, the book
on a lectern, two telephones, an answering machine, the radio shelf on the
cross-wall, and a loudspeaker on a bracket at 2.400 m angled at the counter.

THE NORTH BAY IS THE TRADE'S HALF. Drivers come in by their OWN door, the
second bay's side door, and never through the public room. A drivers' room with
a bench, a formica table, four chairs and no two the same, a kettle, a
dartboard, a notice board with the rota and the settle list on it, and a
portable radio on the sill. Behind that, the proprietor's corner: Tom's desk,
the filing cabinet and the coats. Behind THAT, a lock-up let weekly for cash to
a man who repairs televisions, with its own padlocked door and its own way out
to the yard.

BETWEEN THEM, ONE CUT. The party wall between the two bays is NOT removed. A
1.000 m opening with a painted timber lintel and scarred plaster, cut in 1984
when the north shop closed, and it lands BEHIND the counter line. That single
decision produces the whole social geometry: the public and the drivers are
never in one room, never see each other, and both can hear the radio.

## 2. Why the cross-wall stays, which is the design's one real argument

A terrace cross-wall is structural. Taking it out needs a beam, a builder and
money, and the premises this package describes has never had any of the three:
its history is a beer house that became a cab office by painting one word on a
sign. So the wall stays and one hole gets cut in it, which is what actually
happened to thousands of these buildings.

The gameplay consequence is not a side effect, it is the point. `atlas-02`'s
card 2 already argued the same thing for the pub and Jafar's studio took it as
part of the ruling: "the rooms SURVIVE. A public bar and one snug, not knocked
through, because most pubs were knocked through in the 1970s and 1980s and the
ones that were not are the ones whose licensee never had the money." The cab
office inherits that reasoning intact. TWO ROOMS ARE TWO ACOUSTIC AND SOCIAL
SPACES, and a game about who heard what needs two rather than one.

## 3. The drawings

Five sheets, in `drawings/`, each as SVG and PNG from one geometry pass so the
two can never differ. NONE OF THEM IS A RENDER: Blender is not installed in
this container, measured three ways by the fascia package on 2026-09-09 and not
re-argued here. These are measured orthographic drawings.

| sheet | what it settles |
|---|---|
| `cab-ground-plan` | the layout, with a 48-item schedule of contents and the six routes |
| `cab-front-elevation` | what the street sees: the fascia, the sealed door, the net, the mast |
| `cab-counter-section` | the two sightlines, drawn to scale with their measured heights on them |
| `cab-yard-and-escape` | the yard, the half-lit lamps, the gate, the escape and the lane |
| `cab-street-rank` | the rank, the yellow lines, the gully and the west court |

## 4. What was MEASURED rather than asserted

`python3 production/art/mickeys-cars/verify/check_cab_office.py`, run
2026-09-10, six checks, findings 0. The readings, not the bounds:

- SIX FRONT OPENINGS MOVED BY 0.000 mm, 6 of 6, against the street's own
  pieces. Nothing in this design touches an aperture that has already been
  rendered.
- 45 CONTENT BOXES parsed of 48 designed items; 3 could not be reduced to a box
  and the checker PRINTS THEIR NAMES rather than skipping them silently
  (`drivers/chairs`, `lockup/sets_stacked`, `lockup/cardboard`, all of which
  are heaps rather than objects).
- 0 of 45 outside the carcass, at a 0.16 m slack that allows a fitting to sit
  in a wall's own thickness.
- 0 of 45 name a surface the street cannot dress, against the 16 in
  `asset-interface.md`, read from that file rather than typed here.
- SIGHTLINE A, the car board from the public footway at 1.600 m eye height:
  SEEN FROM 9 OF 21 positions 0.5 m apart, over the u range 2.0 to 6.0. Outside
  that range the cross-wall or the aperture edge cuts it off.
- SIGHTLINE B, the book: the ray to it passes the counter face at 0.973 m,
  which is UNDER the 1.050 m counter top. BLOCKED.
- SIGHTLINE C, the drivers' room under a net wired at 1.500 m: a hand at 0.850
  m crosses the glass at 1.255 m and is OCCLUDED; a head at 1.650 m crosses at
  1.623 m and is NOT. The net separates hands from heads by 0.123 m of margin
  at the glass, which is the thinnest number in this package and is printed
  because it is thin.
- ROUTES: 0 clashes in 724 samples over 6 routes at a 0.30 m body radius,
  against 26 blocking objects; 16 more objects sit above 1.100 m and are passed
  under, and 3 are flush and are not obstacles at all. The split is printed
  because "0 clashes" against an obstacle list that quietly excluded everything
  would be worth nothing.
- THE SELFTEST runs the accepting case first (the live layout, 0 findings
  added) and then a synthetic rejecting case (one opening nudged 5 mm), which
  it catches.

FOUR OBJECTS AND FIVE ROUTES MOVED BECAUSE OF WHAT THE CHECKER PRINTED, and
one of the four was a real fault rather than a tidy-up: the lock-up's repair
bench ran the full width of the room and across the lock-up's own doorway. It
is now 1.500 m long and stops clear of the door, and the row in the data file
says why in its own text.

## 5. Discrepancies found in existing files, recorded and not smoothed away

1. `production/art/atlas-01/data/mickeys.json` gives `front_glass` as start
   2.22, width 3.33. The street's own piece `east_parade_glass0` is x=6.869,
   sx=3.562, which is u 2.088 to 5.650. THE TWO DISAGREE by 0.132 m at the
   south jamb and 0.232 m at the north. The street piece is used here and the
   blockout's two numbers are recorded as wrong.
2. The same file gives `floor_thickness` 0.2, which would put the finished
   first floor at y=3.600. The carcass piece is y=3.200, sy=6.200, so the
   storeys run from 0.100 and the first floor is at 3.500. THE CARCASS WINS
   because it is the shipped piece.
3. The same file uses the material `cloth` for three items. `asset-interface.md`
   lists SIXTEEN surfaces and `cloth` is not one of them; a new surface ID is a
   decision record. Nothing in this package asks for one, and the checker
   proves it: 0 of 45 outside the list.

None of the three is edited by this commission. They are named so that whoever
builds the winning option meets them on paper instead of in an import.

## 6. What is NOT in this package

- NO GLB, NO MESH, NO TEXTURE, NO IMPORT, NO ENGINE RUN. `asset-interface.md`
  wants a measured `.glb` per prop, and this commission produces none: it is a
  layout and a case, not a batch.
- NO EDIT ANYWHERE OUTSIDE `production/art/mickeys-cars/`. Not to the scene, the
  piece list, the bill of materials, the decals, canon, the brand bible or the
  image tools.
- NO CANON CHANGE, AND THE ONE THIS OPTION WOULD NEED IS NAMED INSTEAD.
  `canon.md` says "the Hook (old port, the player's pub)" at line 10 and "left
  him the pub, Mickey's, in the Hook" at line 48. Choosing the cab office needs
  BOTH of those edited, and that is Jafar's to do and nobody else's. The
  package does not pre-empt it and does not soften it: IF THE CAB OFFICE WINS,
  CANON CHANGES IN TWO PLACES.
- NO VEHICLE ASSET. The rank is dimensioned at an AUTHORED 4.30 by 1.70 m
  envelope, because no measured vehicle envelope in metres exists anywhere in
  this repository and the kit rows in `game-design/agent-reports/` carry squash
  ratios rather than dimensions.
