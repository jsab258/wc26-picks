# Hours, returns and interface notes

STATUS: SPEC, written 2026-09-10. The three things Jafar named after the
gameplay sheet. The machine-readable half is `data/cab-operations.json`; this
file carries the argument.

## 1. Hours, and this is the strongest single argument in the package

| | office open | the game's own hours |
|---|---|---|
| MICKEY'S THE PUB | 11.30 to 14.30 and 17.30 to 23.00, with twenty minutes to drink up. Sunday 12 to 15 and 19 to 22.30. | shut at 23.20 |
| MICKEY'S CARS | 07.00 to 01.00 Monday to Wednesday, to 02.00 Thursday, to 03.00 Friday and Saturday, 09.00 to 01.00 Sunday | open at 01.00 five nights a week |

The pub's hours are not invented: they are the ones `atlas-01`'s own hours
notice carries, authored 2026-09-08 and drawn as a layout proof.

THE POINT IS NOT THAT LONGER IS BETTER. It is that the two curves are the
opposite shape. A pub's busiest hour is nine in the evening and its doors are
bolted at twenty past eleven. A cab office's busiest hour is midnight and it is
BUSIEST BECAUSE EVERYWHERE ELSE HAS SHUT.

Two sourced facts make that true rather than asserted:

1. Bus deregulation from 26 October 1986 thinned evening and Sunday services
   across the country (`atlas-02/research/transport-timetables.md`, sourced
   2026-09-08).
2. The studio ruled on 2026-09-09 that the last bus out of Meridian goes about
   half past ten, and the reason it gave was that "the walk home through a dark
   port town is where the game happens".

PUT THOSE TWO TOGETHER. After 22.30 every person in Meridian who goes anywhere
either walks through a dark port town or rings the player's telephone. The
studio has already ruled that the first of those is where the game happens.
This room is the switchboard of the second.

### The shape of a day, and why two are written

`data/cab-operations.json` carries an ordinary Tuesday hour by hour and then
says how a Friday differs. Two are written rather than one because the room
CHANGES CHARACTER: on a Tuesday it is a waiting room with a bench and a kettle;
on a Friday at half past midnight the counter flap is bolted and the glazed
screen is doing the job it was fitted for. A room that is two rooms at two
hours is worth more than a room that is one room.

## 2. Returns

Three different things in this trade are called a return, and the design uses
all three.

### The money returns

Nine paper sheets on a clipboard on a nail, and a list on the drivers' notice
board with nine names and a figure against each. Jobs off the radio, cash
taken, account jobs, and the week's radio rent against it, settled on a named
day.

NINE PEOPLE OWE THE PLAYER MONEY EVERY WEEK, IN PUBLIC, IN PENCIL, ON A WALL.
That is a standing relationship with a number and a visible history for the
price of one prop. It is also the honest inheritance: canon says Tom inherits
"a book of uncollectable debts", and this is the same idea with the debtors in
the next room.

LABEL: the settle model is CITED-VIA-SEARCH-MODERN in the research file (row
D1) and I could NOT date it to 1990. It is used because it is the only
description of the arrangement I found, and if the CI fetch job at queue 156
finds it is a later practice, this section is what has to change.

### The docket returns

Account work is invoiced monthly against a docket signed by the passenger. A
carbon pad in every car, a spike behind the counter, month bundles in the money
room.

A signed docket is a piece of paper carrying a person's name, a date, a route
and their own handwriting, sitting in a room the player owns. It is the book's
evidence in portable form, and unlike the book it can leave the building
without anybody noticing a page is gone.

### The lost property returns

FOUR CARDBOARD BOXES, LABELLED BY WEEK IN MARKER, AND A CARD ON THE SCREEN
THAT SAYS FOUR WEEKS.

This is the cheapest good idea in the package. A cab office is where a town's
lost property accumulates, and that gives the game:

- a reason for ANY NPC to come back to the player's building, on their own
  initiative, days after an event, and start a conversation;
- an item pipeline with a built-in delay, which is exactly what a game about
  memory and consequence wants and what a shop counter cannot provide;
- a DEADLINE, because the card says four weeks;
- and one holdall in box three that nobody has come for in three weeks. The
  design does not say what is in it. It says that on the twenty-eighth day
  somebody will.

Compare the pub's returns, authored by `atlas-01` and drawn as a proof:
DELIVERIES, PLEASE KNOCK, EMPTIES TO REAR. Under D17 the empties are void.

## 3. Interface notes

Written against `production/specs/asset-interface.md` and
`production/art/atlas-01/INTERFACE-NOTES.md`, which this file does not
contradict and does not silently extend.

### What this package does NOT ask for

- NO NEW SURFACE ID. Every one of the 45 measurable items names one of the
  sixteen in `asset-interface.md`, proved by the checker at 0 of 45 outside the
  list. `atlas-01`'s `cloth` is not used.
- NO SECOND MATERIAL SLOT, no embedded image, no scaling at placement, no
  change to the bounds-centre convention, no change to `BaseColorMap`,
  `NormalMap`, `RoughnessMap`, `TilingU`, `TilingV`.
- NO NEW FRAME. Local `u, v, h` maps to source `x = 3.0 + u`, `y = 0.100 + h`,
  `z = 5.125 + v`, which is `atlas-01`'s own mapping unchanged, so the two
  packages can be laid over each other without a conversion.
- NO EDIT TO THE 593 PIECES. Six front openings measured at 0.000 mm.

### What this package DOES ask for, named as asks and not as decisions

1. A READABLE TEXT SURFACE WHOSE CONTENT CAN CHANGE. The book, the settle list
   and the car board are all objects whose VALUE is that they say something
   specific and that it changes. The street's route for text today is a
   generated image baked into an atlas page and referenced by a UV rect
   (`decal_00_fascia_mickeys#0.0391,0.2773,0.9766,0.7168`). That route can draw
   a page; it cannot draw NEXT WEEK'S page. THIS IS A REAL GAP AND IT IS THE
   ONE THING THE CAB OFFICE NEEDS THAT THE PUB DOES NOT. Three candidate rungs,
   cheapest first, none chosen here: (a) a small fixed set of pre-generated
   pages, which caps the fiction at what was drawn; (b) a text layer composited
   at runtime over a blank ruled page, which is a rendering change; (c) the
   book is never read as an image and is read as an interface panel instead,
   which is cheapest and least diegetic. Jafar's card 2 in the delivery puts
   this to him because it is a feel question and not a technical one.
2. TWO NAMED ACOUSTIC APERTURES, so an audio system has something to bind to
   rather than a wall with a hole in it. `wall_cut` (1.000 m wide, head 2.100 m,
   in a 0.215 m wall) and `speaking_gap` (0.300 by 0.250 m, at 1.050 to 1.300
   m). Both are in the data file with those ids. NOTHING IS CLAIMED ABOUT WHAT
   PASSES THROUGH THEM.
3. FOUR POSITIONED SOUND SOURCES with ids: `loudspeaker`, `controller_mouth`,
   `drivers_table`, `lockup_tenant`. Positions only.
4. ONE STATE THAT IS READ FROM OUTSIDE THE BUILDING: the car board's nine
   hooks. It is the only proposed object in this package whose appearance
   carries live information, and if the answer is that nothing can do that
   yet, THE BOARD STILL WORKS AS A STATIC PROP and the design loses one idea
   rather than a room.
5. STATEFUL OPENINGS: eight doors are marked `stateful` in the data file and
   one, `second_shop_door`, is marked NOT stateful because it is sealed. That
   is a fact a navigation build should have before it tries to open it.

### What remains untested, in the pub package's own words

Door behaviour, collision, navigation, room and acoustic portals,
identity and perception slots, and schedules belong in live placement and
gameplay integration and not in a layout. Nothing in this commission tested
any of them and nothing in this commission claims to have.

## 4. The quality ladder for this commission

Asked at close, per `production/quality-ladder.md`: best available, or first
working?

| aspect | rung | next rung, from resources we have |
|---|---|---|
| the licensing research | FIRST WORKING. 19 of 43 rows are a search summary of a named page and 0 rows read a page. | queue 156, with `legislation.gov.uk/ukpga/1976/57/part/II` added to its targets. Then 14 rows upgrade in one run. |
| the office interior research | NOT WORKING, and it says so: no photograph, plan or description of any British minicab office in the window was found at all. | a fetch job against a photographic archive, which is the same run |
| the layout | BEST AVAILABLE for a layout: measured against the street, 0 findings over 6 checks, and the instrument changed the design four times. | a Blender render of the five cameras, which needs the Windows runner, not this container |
| the drawings | FIRST WORKING. Measured orthographic vector drawings, not renders. | the recipe already exists for the pub; the cab office would need its own |
| the pictures for the Parade | SPEC ONLY, RUN NOT STARTED, and the delivery says so in its first line | the resident's run |
| the interface | AN ASK, NOT A DESIGN. Item 1 above is unresolved and is card 2. | Jafar's answer, then one of the three rungs |
