# Gameplay sheet: Mickey's Cars

STATUS: SPEC, written 2026-09-10. Jafar named the five parts of this sheet in
the commission and they are its five sections: where you overhear, the book,
the radio, the yard, the escape.

WHAT THIS SHEET IS AND IS NOT. Every position, distance and occlusion in it is
authored in `data/cab-office.json` and measured by
`verify/check_cab_office.py`. NONE OF IT IS A CLAIM ABOUT AUDIBILITY,
RECOGNITION OR NAVIGATION. The pub package's sentence governs unchanged: an
architectural sightline grants no witness fact, and acoustics, speaker timing,
attention and the five-rung identification ladder remain integration work.
What a designed room can promise is that the OPPORTUNITY exists, is placed on
purpose, and is different from one spot to the next. That is what is measured
below.

## 1. Where you overhear

THE ROOM'S ONE IDEA: the screen stops your hands and never stops your ears, and
there is a 0.30 by 0.25 m hole in it at the height of a seated man's mouth.

Five listening posts, and they are DIFFERENT rather than nearer and further.
This is the sheet's most important table because it is what a pub cannot do:
a pub has one room and one bar, and a listener is either near it or far from
it. Here the yield changes in KIND.

| post | where | what reaches it | what does not |
|---|---|---|---|
| AT THE COUNTER | u 3.350, v 3.200, standing at the speaking gap | the controller's half of every telephone call; every address he reads to a car; the loudspeaker at 2.400 m angled this way | the drivers' room, round the cross-wall |
| ON THE BENCH | u 3.900, v 0.900, sat under the window, 3.5 m back | the loudspeaker, quieter; the controller's raised voice; the next customer's call on the coin box, 1.4 m away | the telephone at conversational level |
| IN THE DRIVERS' ROOM | u 8.400, v 2.000 | the drivers themselves at full level; the loudspeaker through the 1.000 m cut | the counter, and everything a customer says |
| IN THE YARD | u 6.000, v 9.500, under the dead lamp | doors, cars, the drivers' room window if it is open, and the lock-up over a partition that stops 0.700 m short of the ceiling | anything said at the counter |
| ON THE FOOTWAY | v -1.625, outside on the public pavement | nothing spoken. THIS POST IS FOR THE EYES, and it is the one below. | everything |

FOUR SPEAKERS, positioned rather than assumed: the loudspeaker (u 5.8925, v
4.200, h 2.400), the controller's mouth (u 3.350, v 4.350, h 1.150), the
drivers' table (u 9.000, v 1.600, h 1.150) and the lock-up tenant (u 10.000, v
6.500, h 1.500). Four sources, five posts, and no two posts hear the same set.

### The eyes, and this is measured

THE CAR BOARD IS READABLE FROM THE PUBLIC PAVEMENT AND THE BOOK IS NOT. That
sentence is the design and here are its numbers.

- The car board is on the REAR wall at v 7.785, h 1.300 to 2.100: nine numbered
  hooks, a 60 mm brass disc on every hook whose car is IN. AN EMPTY HOOK IS A
  CAR THAT IS OUT.
- Measured: at 1.600 m eye height on the footway, 21 positions 0.5 m apart,
  THE BOARD IS SEEN FROM 9. The range that sees it is u 2.0 to 6.0; outside it
  the cross-wall or the window jamb cuts the ray. So the player must STAND IN
  THE RIGHT PLACE ON THE PAVEMENT, which is a small, honest, physical skill and
  not a menu.
- The same ray to the book passes the counter face at 0.973 m, under the 1.050
  m counter top. BLOCKED, from every one of the 21.
- WHAT THAT BUYS: a player who has never been inside can learn HOW MANY CARS
  ARE OUT from the street, at any hour, without speaking to anybody. A player
  who wants to know WHERE THEY WENT has to get past a counter.

### The inverse window, which is the other half

The drivers' room window carries a net wired at 1.500 m. Measured from the same
footway eye: a hand at 0.850 m crosses the glass at 1.255 m and is OCCLUDED; a
head at 1.650 m crosses at 1.623 m and is NOT. So through one frontage the
player sees a BOARD and no hands in the north window, and hands and no board in
the south. One building, two opposite observation conditions, both measured.

## 2. The book

THE BOOK IS NOT A PROP. It is a legal requirement with six columns, and the
columns are section 56 of the Local Government (Miscellaneous Provisions) Act
1976 (research file, row L6): the time and date of the booking, the name of the
hirer, the time of pick-up, the point of pick-up, the destination, and the
licence number of the vehicle allocated.

READ THAT LIST AGAIN AS A GAME DESIGNER. It is an event record with a
timestamp, a person, an origin, a destination and an actor, kept by law, in
the player's own building, for every journey anybody in this town takes after
the last bus.

| the object | 300 by 210 mm hardbound day book, one page per shift, ruled into six columns by hand with a biro and a steel ruler, on a sloped lectern at h 0.780 to 0.950, in a well 0.270 m below the counter top |
|---|---|
| WHO CAN READ IT | the controller. Nobody at the counter, measured above. |
| WHO CAN ASK FOR IT | an authorised officer of the council, and therefore in practice a police officer who asks nicely, which is a scene rather than a mechanic |
| WHAT A PAGE IS WORTH | one shift of the town's movements, by name and address |
| WHAT A MISSING PAGE IS WORTH | more, and it is visible: a hardbound book shows a torn page at the stitching for ever |

FIVE THINGS THE BOOK DOES THAT NO OTHER ROOM IN THE GAME CAN DO. Each is a
design intention and none is built.

1. IT REMEMBERS FOR THE PLAYER. The moat is social memory. Every other memory
   in LEDGER lives in an NPC's head and has to be got at by talking. This one
   is on a lectern in a room the player owns, and it is WRITTEN DOWN, which
   means it can be read, copied, shown to someone, lost, sold, or torn.
2. IT IS AN ALIBI MACHINE, BOTH WAYS. If the player was in car 6 at 23:40 the
   book says so. If somebody else was, the book says that too, and it says who
   drove them and where they got out.
3. IT IS EVIDENCE THE PLAYER OWNS AND THEREFORE HAS TO DECIDE ABOUT. Consequence
   persistence is a moat pillar; here it is a physical object with a decision
   attached every time anybody asks about it.
4. IT SELLS. A rival who wants to know who visited whom, a journalist, a
   detective and a jealous husband all want the same six columns.
5. IT IMPLICATES. The operator is the contracting party for every journey
   (research row L6), so the man who owns the book is legally attached to
   whatever the journey was for.

THE INTERFACE ASK THIS CREATES is named honestly in section 4 of
`04-HOURS-RETURNS-INTERFACE.md`: a page of the book must be READABLE AT A
LEGIBLE SIZE and its rows must be able to change, and the street's current
route for text is a generated decal on a fixed atlas page. That is a real gap
and this sheet does not pretend otherwise.

## 3. The radio

THE RADIO IS THE ONLY THING IN THE BUILDING THAT TALKS TO THE PLAYER WITHOUT
BEING ASKED. Every other information channel in LEDGER needs the player to
approach somebody. This one is a loudspeaker on a bracket at 2.400 m, angled
at the counter, audible in three of the five posts, and it says addresses out
loud all night.

The procedure is the design (research row R4, AUTHORED from the sourced
structure at R1): the controller calls a number, the driver answers with his
number, the controller reads out the pick-up and the destination, and THE
DRIVER READS IT BACK. Everything that matters is said twice. Read-back is a
safety habit in every radio trade there has ever been, and here it is a gift to
an eavesdropper: miss it the first time and it comes round again.

| property | value |
|---|---|
| the set | a grey steel base set 0.450 x 0.350 x 0.160 on a shelf at h 1.350 on the cross-wall, one illuminated channel lamp, a volume knob worn smooth |
| the maker | DELIBERATELY BLANK. Research row R6 could not source who licensed a private mobile radio in Britain in 1990 or in which band, so the plate is blank and the licence paper is illegible rather than invented. |
| the loudspeaker | 0.250 m cube on a steel bracket at h 2.400, u 5.8925, v 4.200 |
| the aerial | coax stapled up the corner at u 5.700, through the ceiling, to a mast on the chimney stack. IT IS VISIBLE FROM THE STREET. |
| the cars | nine, numbered. Car 3 is the one with the exhaust. |

WHAT THE RADIO IS FOR, in the moat's own terms: GOSSIP SPREADS THROUGH SCHEDULE
INTERSECTIONS, and the radio is a schedule intersection that runs all night in
one room. A player sitting on that bench for ten minutes hears where six people
in this town are going. No pub conversation delivers that, because a pub
conversation is between two people who chose each other.

AND IT WORKS THE OTHER WAY, WHICH IS BETTER. The controller can be LIED TO. A
booking is a name, an address and a time given over a telephone by somebody who
is not in the room. That is a hook for the player to place a car somewhere, and
a hook for somebody to place the player.

## 4. The yard

12.0 by 6.0 m behind the building, a 1.8 m wall, a 1.2 m timber gate, and a
2.4 m rear lane beyond it. All four numbers are `atlas-01`'s and are CARRIED
unchanged: this is the pub's yard, wider because the premises is wider.

THE YARD IS A THOROUGHFARE AND THAT IS WHY IT IS GOOD. The WC is the 1958 brick
one in the yard, so every driver and the controller crosses the yard at every
hour of the night. A back space nobody enters is scenery; a back space with a
lavatory at the end of it has a witness in it for free, on a schedule, all
night.

Four authored facts, each with a cause:

1. THE YARD IS HALF LIT. The bulkhead over the control door has had no bulb
   since August. The one over the lock-up works, because the tenant replaced
   his own. THE LIT HALF IS NOT THE HALF THE ESCAPE USES.
2. THE LOCK-UP TENANT IS A SECOND KEYHOLDER. He repairs television sets, is in
   from about ten to about four and on Saturday mornings, and his partition
   stops 0.700 m below the ceiling, so he hears the radio, the telephone and
   every argument without ever being in the room. He is a witness who was never
   present, which is exactly the shape of testimony the game's perception model
   is built to handle.
3. NO CAR EVER ENTERS THE YARD, and this was MEASURED and refused rather than
   designed around: the lane is 2.4 m and the gate is 1.2 m, and widening
   either to make a design work would be editing authored data for convenience.
4. THE YARD IS OVERLOOKED FROM ABOVE by four rear windows of the flat and by
   both neighbours' upper windows. The 1.8 m wall stops a view from the lane
   and stops nothing from above.

## 5. The escape

TWO ESCAPES, and the second is the one the pub cannot have.

### The slow one, which is the pub's route and is measured

Counter, through the flap, across the control side, out the control door, into
the yard, behind the WC annex, through the 1.2 m gate, south along the rear
lane, west down the 3.0 m terrace-end passage, back onto Quay Street. MEASURED:
383 samples, 0 clashes at a 0.30 m body radius. It never crosses a neighbour's
property, which was `atlas-01`'s rule and is kept.

AND IT IS SEEN. Overlooked from above by six windows, and half the yard is lit.
This route is slower and MORE witnessed than the pub's, because the pub's yard
was 6.0 m wide and this one is 12.0 m with a working lamp on it. That is a cost
of the cab office and it is stated as one.

### The fast one, and its honest conditions

OUT THE DRIVERS' DOOR, ACROSS THE PAVEMENT, INTO A CAR.

The rank is the east kerb outside the office: three cars nose to tail, 14.10 m
of them, standing on double yellow lines the street already has, over a gully
grate the street already has at x=12.000. The player's own firm's cars, with
the player's own firm's keys, thirty seconds from the counter.

WHAT THIS DEPENDS ON, and none of it was looked at by this commission: that
vehicles can be entered, that they can be driven, that traffic exists, and that
a pursuit means anything. IF THOSE DO NOT EXIST, THIS ESCAPE DOES NOT EXIST,
and the cab office should be judged on the slow one alone. It is written here
as a design intention with its dependency named, which is the only honest way
to carry it.

WHAT IT COSTS EVEN IF IT WORKS: a car is the most identifiable object in a
British port town in 1990. It has a plate on the back with the council's
licence number on it (research row D4). Nine cars, nine numbers, and every one
of them is written in the book. THE FAST ESCAPE IS THE MOST TRACEABLE ACT IN
THE GAME, and that is not a flaw, it is the moat: consequence persistence 95.
Taking a car is a decision with a permanent, written, numbered record of
itself, made by the player, in the player's own book.

## 6. What this sheet does NOT claim

- That anything is audible. No acoustic model was consulted, no portal exists,
  no attenuation was computed. Five posts and four sources are POSITIONS.
- That anything is recognisable. The identification ladder is relationship
  gated, per canon, and no sightline here changes that.
- That the routes are navigable. Door movement, collision and real navigation
  are untested, in the pub package's own words, and remain so.
- That the book, the radio or the board have any interface. They do not, and
  `04-HOURS-RETURNS-INTERFACE.md` names what they would need.
- That the fast escape is possible. See above.
