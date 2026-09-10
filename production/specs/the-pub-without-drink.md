# The pub without drink: what the room is for

STATUS: SPEC, written 2026-09-10. Part 4 of Jafar's commission of that date: "a
written case for what people do inside a pub with no drinking". It fills the gap
D18 leaves open, "what the pub is for without drink is a design task, not a
subtraction", for the writer replacing a void dialogue bank and the artist
dressing a room. Not a layout: `atlas-02/research/small-pub-plan-measured.md` is the
measured input and this file says which half survives D18. NOT ABOUT MICKEY'S: the ruling
of 2026-09-10 made it a minicab office and the player inherits no pub, so every
room here belongs to somebody else. LABELS, as in the research file: CITED has a
source, DERIVED prints its arithmetic, ASSUMED has neither, HOLE was looked for
and not found.

## 1. The honest difficulty, first

A British pub in 1990 with nothing to drink is not a normal place. Five things break.

**1. THE COMMITMENT DEVICE BREAKS, AND THIS IS THE REAL ONE.** Dwell time was
bought by the round: you buy for four, you are held until it is gone, then it is
somebody else's turn and you are held again. A repeating obligation that keeps a
man in one chair for three hours beside the same five men. Tea does not: a cup is
a ten-minute object and then your hands are empty.

This is mechanical, not atmospheric. I read the mill. Gossip hops only when two
conditions hold at one tick: a tie in the acquaintance graph, and
`Vector3.Distance(pa, pb) <= TalkRange` with `TalkRange = 6f`
(`GossipDirector.cs` 34, 660 to 666). A round is 6 game minutes (line 29) and a
rumour moves one hop per round. SO DWELL TIME IS LITERALLY THE INPUT: minutes
within six metres of a tie, divided by six, is how many chances the town gets.
Remove the round and you have not made the room quieter, you have cut the
denominator of the information pillar.

**2. THE LICENCE TO SPEAK TO A STRANGER BREAKS.** Drink lowered the floor on
opening a conversation with a man you had only nodded at for nine years. Sober,
six Englishmen in a small room in November is a fire crackling and nobody saying
anything. **3. AND THE TRADE BREAKS**: wet sales were the income, a house without
them has no reason to open at eleven, and opening hours are the schedule the sim
reads.

**4. THE SILHOUETTE BREAKS.** The handpumps, the optics, the mirrored back fitting,
the bottle shelf and a glass in every hand are what make a photograph of that room
read as that room. Strip them and an empty back bar reads two ways, both wrong: a
pub shut down, or a coffee place built in 2015. Meridian Test item 1 is lost at the
door. **5. AND THE WORDS BREAK**: 12 of the 48 lines in `pub-regular-v1` are
alcohol lines and 2 gambling (D17 scan), and the rhythm of more than those
fourteen is drink.

AND ONE THING THE RULE ITSELF FORBIDS, which closes a door people reach for. D18
says alcohol is never SPOKEN OF, so THE WORLD MAY NOT EXPLAIN ITSELF: no line
about why this house does not serve, no sign in the window, no temperance
plaque, no licence lost at the magistrates. The absence must be total and
unremarked, so the room has to be furnished such that nothing in it poses the
question. A room that visibly avoids something talks about it constantly.

### What the room was actually for

The pub was the only room in town that was neither work nor home, and the one
with things in it.

- THE WARMTH. CITED (`household-contents-and-upstairs.md` 1): about one household in
  five had no central heating, and a heated room you do not pay for is a reason alone.
- THE TELEPHONE. CITED, about the 1970s so shape and not window: lots of pubs
  had a pay-on-answer coin box as the only line, and the landlord, a tenant, fed
  it coins himself to call out. Source: UK payphones, Pay on Answer,
  https://sites.google.com/site/payphone500/pay-on-answer . Beside 92,000 phone
  boxes at their 1992 peak, the pub is where the lane's calls happen.
- THE FIRE, THE SLATE, THE NOTICEBOARD, THE DARTS, THE DOMINOES, THE PIANO, and
  THE LISTS: the coach trip, the club pay-in, the league fixtures.
- THE SEA through the window, the men who work on it, and SOMEBODY WHO KNEW
  EVERYBODY, behind the counter, fourteen hours a day.

Not one of those things is drink. The room was a general-purpose social instrument
on which alcohol was the busiest single function, never the only one.

## 2. The decision

**THE ROOM STAYS, ITS DOORS STAY OPEN, AND ITS TRADE CHANGES: tea and coffee
from an urn, hot food over the counter, tobacco, the telephone, the room hired
out by the hour, and the games league. The counter stays a counter. The three
information organs of the new trade are THE COUNTER, THE BOARD AND THE BOOK.**

THE SHAPE IS NOT INVENTED. Britain built this building type and named it. CITED,
about the 1860s to 1880s so evidence about shape and not the window: in 1867
temperance campaigners bought a pub in Leeds and ran it as a public house
without the beer, named the British Workman; the coffee tavern movement that
followed in the late 1870s put hundreds of alcohol-free pubs across the country;
they sold tea, coffee, cocoa and hot and cold food; and their stated aim was the
three Rs of Reading, Recreation and Refreshment. Sources: Historic England,
"Temperance Buildings: The Way Out of Darkest England",
https://heritagecalling.com/2026/01/08/temperance-buildings-the-way-out-of-darkest-england/ ;
Cassell's Family Magazine 1879, "Coffee Taverns and the Temperance Movement",
https://www.victorianvoices.net/ARTICLES/CFM/CFM1879/CFM1879-CoffeeTaverns.pdf .
Reading, Recreation and Refreshment IS this design, named by somebody else a
century earlier: the board, the games, the counter.

### What replaces the round, which is the only question that matters

**THE FIXTURE REPLACES THE ROUND.** A league holds you better than a round
because it is written down in advance: you cannot leave at half past nine when
your team is eight a side and you are one of the eight. CITED, about present-day
leagues of long standing so shape and not window: British pub darts and dominoes
leagues run a winter season from about September to May, one night a week, home
and away, commonly eight a side, and the two games are routinely one league.
Source: Wakefield Darts and Dominoes Monday Night League,
https://www.wakefielddarts.uk/ with its rules page.

Read it as a simulation input, not a pastime. On a home night eight men FROM
ANOTHER DISTRICT, carrying their own ties to their own lane, are inside six
metres of the home eight for two hours, on a date printed in September. DERIVED
from the 6-minute tick: about 20 gossip rounds, each a chance for every
co-present tied pair. The round was a private clock; the fixture is a PUBLIC
one, knowable by the player, and it moves talk BETWEEN districts.

The other dwell engines, in descending order of what they buy:

- THE HIRE. The back or upstairs room let by the hour for cash: union branch, angling
  club, funeral tea, coach trip, pay-in night. Each a named group with a start time.
- THE WAIT. A call back on the coin box, the rain, a last bus deregulation has
  made unreliable (`transport-timetables.md` 1).
- THE FOOD. Eating holds a man forty minutes and changes the arithmetic: CITED in
  the pub research, the dining floor space factor is 1.0 m2 per person against
  0.5 standing, so a room that feeds people holds half as many twice as long. And
  THE WARM, which costs nothing and is period-true.

### Why the other shape is worse

THE REJECTED SHAPE: never depict the licensed side, keep the camera in the
corridor, the snug and the yard, let the bar be a room the game does not enter.

1. **THE GAME HAS NO CAMERA AUTHORITY.** A room the camera declines to enter is a
   room with a locked door, and a pub whose bar is locked is a facade. This
   promise is kept or broken by a door the player will push.
2. **IT DEPICTS BY NEGATIVE SPACE, WHICH THE RULE ALSO FORBIDS.** A building whose
   every frame is arranged around the thing just out of shot is a building about
   that thing, and every line where a man cannot say what he is holding says it.
3. **IT SWITCHES OFF AN INSTRUMENT.** The atlas puts one information venue per
   district at a route crossing, D13 rider 2, and D18 lands on three of the seven.
   Taking the main room off camera turns a venue into scenery, and the answer to a
   rule that hits your instruments is not to stop reading one.

ONE THING IT IS RIGHT ABOUT, kept: the corridor, the hatch and the yard are good
listening posts, and they stay, in a building the player may also enter.

AND ONE GAIN. An unlicensed house is not bound by permitted hours, so the
Licensing Act 1988 window of 11:00 to 23:00 (CITED, pub research 5) no longer
governs it: it can open at six for the dock shift and at seven on a Sunday, which
a licensed pub could not. THE INFORMATION WINDOW IS LONGER THAN THE PERIOD'S REAL
PUB HAD. ASSUMED: it keeps roughly pub hours anyway, because that is when people
come.

## 3. What the player does, as verbs

Twelve. Each gathers, spends or leaves a trace; none is built, so this is the intention an interior has to support.

| verb | what it is | G / S / T |
|---|---|---|
| STAND THE TABLE A POT | buy a pot and cups for a table you did not sit at. Reciprocity survives the drink: money, a gesture, an obligation | S, and T: he stood the table a pot on Tuesday |
| PUT YOUR NAME DOWN | write yourself onto the league sheet, the coach list, the hire book, the club book | T, written, legible later to anybody including a detective. Also S |
| READ THE BOARD | fixture card, hire diary, cards in the window, work wanted, rooms to let, the funeral notice | G, and the only free information tap in the town |
| ASK IF ANYBODY RANG | the pub is the lane's telephone address. Your messages, or somebody else's | G, and S when it is somebody else's |
| WAIT BY THE COIN BOX | the box is in the passage: one speaker, one listener, no door | G, the best eavesdrop in the building |
| MAKE A CALL FROM IT | pay on answer, coins, in a passage where anybody may be standing | T: your half of it was heard |
| PLAY | darts doubles, dominoes, snooker. An hour beside one man | T, and the intention is that it RAISES THE TIE, which is the number gossip multiplies by |
| SIT THROUGH A HIRE | be in the back room for the branch meeting or the funeral tea | G, ninety minutes co-present with another district |
| LISTEN AT THE HATCH | the serving hatch to the back room, CITED in the pub research with its bell pushes | G |
| SETTLE SOMEBODY'S SLATE | pay off another man's tick for food and tobacco | S and T, written in the book, and the landlord knows |
| TAKE THE ROOM | hire the back room by the hour, for cash, under a name, in the book | T, a private meeting whose record is in somebody else's hand |
| PIN UP, OR TAKE DOWN | the board is a writable surface. Pin a card. Remove a rival's | T, and the landlord notices a missing card |

AND THE SANCTION, or none of the above has weight: GET BARRED. Barred is barred
from the board, the telephone, the fixture and the hire, which together are the
town's information utility. A reputation loss with a door attached, permanent in
the landlord's memory, costing access rather than hit points.

## 4. How gossip still moves through it

FOUR NUMBERS FROM THE CODE, read this session. `Core/Gossip.cs`:
`HopDecay = 0.8`, `MinConfidenceToShare = 0.2`, a passed rumour is
`confidence * tie * HopDecay`, one hop per round. `GossipDirector`:
`TalkRange = 6f`, tick 6 game minutes.

DERIVED, AND IT IS THE SHARPEST ARGUMENT HERE. For a first-hand sighting at
confidence 1.0 to reach a THIRD person, two hops must each clear 0.2, so
`(tie * 0.8)^2 >= 0.2`, so `tie >= 0.559`. TIES BELOW ABOUT 0.56 CANNOT CARRY A
STORY TO A THIRD PERSON AT ALL. The Phase 1 gate in `roadmap-v2.md` is "witnessed
crime reaches a second and third NPC within one in-game week", so that gate
depends on rooms holding HIGH-TIE PAIRS for many ticks. That is what this room is
for, and why a weak answer here reads later as a failed gate elsewhere.

WHO IS IN THE ROOM, AND WHY THEY STAY LONG ENOUGH.

- THE LANDLORD OR LANDLADY, fourteen hours, tied to everybody: the high-degree
  node, the one person who makes a second hop cheap. Everybody else needs luck
  to be co-present with a stranger; this one is always there.
- THE EIGHT on a league night plus the away eight: two hours, a printed date,
  cross-district edges.
- THE HIRE GROUP, ninety minutes in the back room, tied strongly to each other and
  weakly to the front bar: a strong-tie cluster parked beside a weak-tie crowd,
  the most useful shape in the building.
- THE SHIFT, arriving together: `working_town` already walks a packing shift to a room
  at 17:30. And THE WAITERS: a call back, a bus, the rain. Low tie, long dwell, and
  they carry a thing out of the district. NOBODY UNDER EIGHTEEN, per D18: the research
  cites under-14s not permitted in the bar, certificates arriving only in 1995.

HOW WHAT THEY HEARD LEAVES WITH THEM, three routes, no new machinery.

1. THE AWAY LEG. The away eight go home to their own lane and their own ties: a
   fixture list is a scheduled weekly transfer of talk between districts.
2. THE TELEPHONE. What was said in the bar is repeated into the coin box in the
   passage and reaches another district in seconds.
3. THE MESSAGE. The landlord takes a message for a man with no telephone and hands
   it over tomorrow, with commentary: a rumour with a delivery address.

WHAT THE ROOM NO LONGER DOES: hold a man four hours on a wet Monday with no
fixture and no hire. So the WEEK HAS SHAPE: two league nights, a hire night, a
pay-in night, three thin ones, and a town where Thursday is worth more than
Monday beats a town with one crowd every night.

## 5. What it looks like

### Fixtures that stay

The counter, at the research's ASSUMED 1050 mm. The mirrored back fitting with
different things on it. The bell pushes and the serving hatch. The partitions and
etched glass IF this house kept its rooms, which the research says means it never
had the money: a characterisation fact, not a decorating one. Lino inside the
door, carpet beyond. The fixed wall bench in buttoned vinyl, cast-iron table legs,
stools with one bad leg. The dartboard at 1730 mm to the bull with its oche at
2370 mm, CITED and measured. The dominoes table with its baize. The fire. The
piano with the lid up and rings burned into it. The ashtrays, the tobacco behind
the counter, the cigarette machine: tobacco stays and that room is full of smoke.
The clock five minutes fast, the team photographs, the tiled threshold with the
house's name in it, the lamp bracket over the door, the coin box in the passage.
And the cellar below, its pavement plate still in the footway, reading as a coal
plate, because the ironwork was always the same ironwork.

### Fixtures that go

Everything named in 1.4, plus the measures, the spirit shelf, the glass washer, the
drip trays, the bar towels, the crown-stamped brim glasses, the price list, the
bottle-and-jug off-sales hatch, the bell for drinking-up time and the twenty
minutes it rang for, and the stillage, casks, drop pad, hook and rope below. Then
the fruit machine, the bingo poster, the betting slip and the dog track card: the
gambling half, gone by the same rule.

### Fixtures to invent, and the first is the whole frame

1. **THE URN.** A chrome twin tea urn where the pumps were, dented skirt, drip
   tray, steaming. The same chrome in the same place, it is what the eye lands on,
   and steam in a cold wet room is photographic gold. Urn wrong, room wrong.
2. **THE FOOD COUNTER.** Glass-fronted pie case with a bulb too hot for it, thick
   white cups on saucers, a boiler with a brass tap, a wire crate of minerals, a
   jug under muslin, pickled eggs, a crisp rack on a card.
3. **THE BOARD**, cork and green baize in beading, cards three deep: work wanted,
   a van for sale, a room to let, the coach trip, a funeral notice, a written
   appeal for a missing cat. Beside it **THE FIXTURE CARD**, pinned by the hatch,
   eight a side, home and away, the other houses' names on it, PARTLY DRAWN
   ALREADY (see costs), and **THE HONOURS BOARD**, painted, winners by year, last
   entry 1991: a dating device needing no caption.
4. **THE BOOK.** A hardbound hire diary on the counter end, the week ruled out by
   hand, names, hours, a mark for paid. Deliberate twin of the cab office's day
   book and deliberately different: THE CAB BOOK RECORDS MOVEMENTS, THE PUB BOOK
   RECORDS MEETINGS.
5. **THE MESSAGE SPIKE** by the coin box, folded notes with names on them, a
   pencil on a string. And **THE PAPERS ON BATONS**, today's front page legible,
   dating the scene and feeding the Argus into the room.

### A wet Tuesday night at eye level

You come in out of horizontal rain and the door sticks. The ceiling is low and the
colour of strong tea, and it is that colour from the smoke, not the paint. One
shaded bulb over the dominoes and nothing else lit properly, so the far end is a
brown darkness with a fire in it. The windows run with condensation because the urn
has been on since seven and nobody opens a window in November, and the glass shows
the street as smeared orange. The lino by the door is black in a half circle where
the rain gets in. Six people, three of whom are not talking and do not intend to. A
woman behind the counter, sleeves pushed up, drying cups, a cloth over her
shoulder, who looked at you before the door shut. Wet wool, tobacco and bleach with
tea under it. The telephone in the passage rings twice and stops. Somebody shuffles
dominoes face down on baize and it is the loudest thing in the room, and the fire
is banked because the man whose job that is has gone home.

## 6. What this costs

Counted where it can be. Dialogue and image counts are the D17 scan's
(`production/art/mickeys-cars/05-D17-town-pass.md` 3); geometry is the pieces
file's.

| material | keep | rewrite or replace |
|---|---|---|
| `content/dialogue/pub-regular-v1.json`, 48 lines | 34 survive word for word | 14: 12 alcohol, 2 gambling |
| the same bank AS A PUB BANK | nothing | about 16 NEW lines, because 31 of the surviving 34 name no room feature at all. They are town lines said by a man sitting down somewhere, and that is a fault, not a saving |
| `content/dialogue/crime-witness-v1.json`, 24 | 22 | 2 |
| `production/specs/dialogue-pub-regular-v1.md` | the 9-cell structure, rung discipline, the toma exclusion | line 26, which tells writers to use beer, plus the room vocabulary clause |
| the 593-piece street | ALL 593. Not one piece of geometry moves | nothing. `vignette-pieces.json` scores 0 over 704 lines |
| generated images, 45 in the library, 10 placed on the street | 41, and 9 of the 10 placed | `poster_bingo`, and `interior_bar_back`, the one placed break, at x=18.000 |
| `poster_darts.png` | THE ARTIFACT IS KEPT and it is invented fixture 4 | two strings: its prompt says beer-stained, and its binding names the Sailors' Rest, in no canon line and no brand bible entry |
| `small-pub-plan-measured.md`, 341 lines this session, sections 0 to 7 | 1, 2, 3 and 6 stand | 4, the cellar, becomes history rather than input; 5 loses its permitted hours, spirit measures and children clause |

WHAT IT SAVES, since a table that only spends is dishonest. Four of the pub research's
nine holes stop mattering: the price series, the spirit measure, the gaming stake
limits, half the licensing clock. And the street break was already going to be replaced
by the pawnshop interior the D17 pass recommends, right for that slot because x=18.000
sits under the pawn fascia; the pub's lit window wants a NEW card: urn, pie case, cups.

NEW PIECES ASKED FOR: 8 invented fixtures, of which 1 is already drawn and needs two
strings changed, 1 is a new lit interior card (one generation, one manifest row), and 6
are modelled or drawn from scratch. Plus 5 or 6 house names the brand bible owes, one
already shipped inside a generated image and therefore owed twice. The period-truth
risk in 1.4 does not go away: a British player over forty will notice, which is why the
urn matters most. An audience notices an absence and forgives a substitution.

## 7. What I am not sure about

Each with the question that would settle it. None is hidden above.

1. **WHETHER THE ROOM READS AS OPEN.** The case rests on substitution reading as
   furniture rather than absence. SETTLED BY: one rendered still of the Tuesday
   night room, asked "open, or shut down". Cheaper than any argument, and it is the
   Meridian Test's own instrument.
2. **THE PUB SAVINGS CLUB IS A HOLE.** I searched for the British practice of a
   pub Christmas or hamper club with weekly payments taken by the landlord and
   did not find it. What I found is SHOP based: a register held by a shopkeeper,
   weekly subscriptions, 1950s Britain
   (https://belfasthistory.org/the-christmas-clubs-of-the-nineteen-fifties/ ), so
   the pay-in night is ASSUMED. SETTLED BY: a local or oral history source naming a
   pub club and its book.
3. **THE SLATE IS ASSUMED**, and so is the coin box being the house's only line
   in 1990, since the pay-on-answer source is about the 1970s. SETTLED BY: a
   cited account of pub credit in the 1980s, and a BT or Post Office
   Telecommunications source on pub installations late in the decade.
4. **WHAT SHARE OF TRADE FOOD COULD CARRY.** No figure found inside the window.
   The nearest is 2016, 50 percent drink against 31 percent catering (Mintel and
   Morning Advertiser summaries), outside the window and not to be used. SETTLED
   BY: a Brewers Society or Mintel report from 1988 to 1992.
5. **ONE ROOM OR TWO.** The research says knocked-through was the majority case
   by 1990 and that surviving rooms mean a poor or stubborn licensee. This design
   wants two, because the hatch and the corridor are its posts. SETTLED BY: the
   taste card below.
6. **WHETHER THE LEAGUE TRIPS THE GAMBLING CLAUSE.** The D17 pass asked this of a
   snooker table and answered that a game is not a wager. A league adds entry
   fees, a trophy and a coach fund. SETTLED BY: extending that ruling in one
   line. Default: no money ever crosses a board, fees go in a book, the prize is
   a trophy and a photograph.
7. **THE MILL DOES NOT KNOW ABOUT WALLS, AND THIS DESIGN NEEDS IT TO.** The
   `Together` predicate is euclidean distance under 6 m with no occlusion term
   (`GossipDirector.cs` 660 to 666) and `GossipDirector` never references
   `Acoustics`, though `Core/Acoustics.cs` carries an `occluded` flag through
   `Intelligibility`, `CanMakeOutWords` and `WhoOverheard`. So the PLAYER's
   overhearing respects walls and NPC to NPC gossip does not: in a two-room house
   the back room and the front bar talk through a shut door, deleting the
   separation this layout exists for. SETTLED BY: at integration, an occlusion
   term in `Together` or a hire room more than 6 m from the counter. Named here
   so no interior is authored against a promise the code does not keep.
8. **THE NAMES.** The fixture card cannot be drawn until 5 or 6 houses are
   minted. SETTLED BY: the brand bible, the only thing that may mint them.

## 8. The two rooms this also answers, referred here under queue 245

The coordinator ruled on 2026-09-10 that this lane owns what a licensed room is for
when nobody is drinking, and the D17 pass withdrew its proposals for two rooms and
referred them here. Each is a district's ONLY information venue.

**I1, THE CLOCKING-IN ROOMS, Ironside.** A working men's club ran on a bar, and the
parity clause that lets pubs exist reaches a club. Take the decision above
unchanged and change only what membership implies: the counter opens at six for the
shift, the board carries union business and overtime lists instead of vans for
sale, the hire is the branch meeting, and the game is full-size snooker under a low
shade rather than darts. It keeps its name for the reason the name exists: you
clock in, and then you come here. ONE DIFFERENCE THAT MATTERS TO THE MOAT:
membership is a written list with subscriptions against it, so the room knows who
belongs and the player is a visible guest until somebody signs him in.

**G1, THE WINTER ROOMS, Gullwing.** Not the same problem: the break here is
gambling, not drink. The distinction that saves it is GAMING machine against
ATTRACTION, and the atlas's own `arcade cabinet` already reads as a video cabinet,
which is not a wager. So: rows of upright cabinets, table football, a photo booth
with a curtain, a tea counter with a glass case, a shove-halfpenny board with no
stake on it, and the first-floor ballroom that has not opened since 1979 and whose
sprung floor the whole town remembers. NO PRIZE MACHINE OF ANY KIND, the safe
reading of the rule, needing confirmation rather than assumption. Its dwell engine
is not the fixture, it is the weather: a seafront hall in the rain holds whoever
is on the front.

## What this hands forward, and the cards it owes Jafar

TO THE WRITER replacing `pub-regular-v1`: keep 34, rewrite 14, add about 16 naming
the counter, the board, the book, the fixture and the coin box. TO THE ARTIST: the
three lists in 5, the eye-level paragraph, the urn first. TO THE BRAND BIBLE: 5 or
6 house names, and the Sailors' Rest minted or struck from two manifest rows.

THREE TASTE CARDS for the resident to route, each with a default so work continues
while he sleeps. ONE, ONE ROOM OR TWO in the houses the player enters; default
two, because the hatch and the corridor are the posts, and it is needed before any
interior is laid out. TWO, DOES THE LEAGUE CARRY FEES AND A TROPHY; default a
trophy and a book yes, money crossing a board never. THREE, THE EARLY OPENING, an
unlicensed house opening at six for the dock shift where the period's licensed pub
could not; default yes, and it is a gain for the information pillar rather than a
liberty with the period.
