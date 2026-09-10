# The D17 pass: every district sheet and the atlas, re-read

STATUS: SPEC, written 2026-09-10. Commissioned in the same message as the cab
office: "a town-wide pass under D17: every district sheet and the atlas
re-read". This file reports what D17 breaks and what it does not.

D17 is at `ledger-v2/respec/decision-register/D17-no-alcohol-no-gambling.md`,
and D18, ruled the same day, EXTENDS it into a permanent content rule over the
whole work. Sections 1 and 2 of this file are the D17 pass as commissioned;
SECTION 2b IS THE D18 DELTA, and it moves one of section 1's numbers.
It says alcohol and gambling are never shown, served, drunk or spoken of,
anywhere, in image or speech, and that PUBS MAY EXIST AS PLACES. It names four
places it is enforced. It does not say what it breaks, and that is what this
file is for.

## 0a. The scope boundary, ruled after this file was drafted

The coordinator ruled on 2026-09-10, filed as `production/queue/245`, that a
second world-designer lane owns WHAT A LICENSED ROOM IS FOR WHEN NOBODY IS
DRINKING, in `production/specs/the-pub-without-drink.md`. This lane owns the
street and public space.

THAT RULING REACHES TWO SECTIONS OF THIS FILE and both are corrected in place
rather than quietly reworded: the Ironside and Gullwing entries in section 2
each proposed a programme for a room, and both proposals are WITHDRAWN and
replaced by a referral. WHAT SURVIVES IS THE FINDING, which is properly this
file's: those two districts each have exactly one information venue and D17
lands on it.

## 0. How this was done, and the two things wrong with it

The instrument is `verify/d17_scan.py`, read only, run 2026-09-10. It scans
eleven shipped files, the two dialogue banks line by line, the generated image
library, and the atlas and district sheets on `origin/art/atlas-01` read with
`git show`. Its selftest runs the accepting case first.

TWO HONEST WARNINGS, both of which change how to read the numbers.

1. TWO OF THE ELEVEN FILES WERE BEING EDITED WHILE THIS RAN. `canon.md` read
   121 lines at the time of this scan and was 84 earlier in the same session,
   and `content/brands/brand-bible-v1.json` read 130 lines and was 96. Another
   agent is applying D17 to both right now. SO THE COUNTS FOR THOSE TWO FILES
   ARE A SNAPSHOT OF A MOVING TARGET and this file does not draw conclusions
   from them. Everything else was static.
2. A WORD LIST CANNOT SEE AN INSTITUTION, and this pass proves it on itself.
   The scanner found nothing at all in Ironside and Gullwing. Reading their
   sheets found the two biggest problems in the town. Both are in section 2,
   and the fact that the machine missed them is recorded as a limit of the
   machine rather than quietly fixed by widening the pattern.

## 1. The headline count, with its denominator

THE ATLAS PLACES ONE INFORMATION VENUE IN EACH OF THE SEVEN DISTRICTS. That is
D13 rider 2 made concrete: "each district contains at least one information
venue at a route crossing". Twelve landmarks, seven of them `venue: true`, one
per district exactly.

D17 TOUCHES THREE OF THE SEVEN. Four are untouched.

| district | venue | D17 | why |
|---|---|---|---|
| the Hook | H1 Mickey's, typed `pub` | TOUCHED | it is the subject of ruling 6 |
| Copper Row | C1 Market Hall | CLEAN | a market is a market |
| the Exchange | E1 Records Court cafe | CLEAN | 0 hits in the whole sheet row |
| the Parade | P1 the Tivoli, cinema | CLEAN, and it becomes the anchor of file 06 |
| Fairview | F1 Chapel and school gate | CLEAN |
| Ironside | I1 Clocking-in club | TOUCHED, and the scanner did not see it |
| Gullwing | G1 Winter Rooms arcade | TOUCHED, and the scanner did not see it |

THAT IS THE FINDING THAT MATTERS MOST: in three of the seven districts, D17
lands on the ONE ROOM THE TOWN PLAN PUT THERE TO CARRY INFORMATION. Not on
scenery. On the instrument. Two of the three are not the pub and are nobody's
current commission.

## 2. District by district, re-read

### The Hook, and its one break

- ATLAS OBJECTS: `rope fender, beer firkin, paper delivery docket, galvanised
  dustbin`. THE BEER FIRKIN BREAKS. It is one of four characteristic objects
  for the district and it is drawn on the concept sheet.
- REPLACEMENT, and it should not be a subtraction: a FISH BOX, a stencilled
  wooden crate with a dealer's mark on the end. It is a port object, it carries
  a trade name, it stacks, it rots, and the district already has a fish market
  on the built street and a cold store in the atlas. It does the firkin's job
  of saying what moves through this district, better.
- The Hook sheet row itself is CLEAN: 0 alcohol hits, 0 gambling hits.
- H1's type field says `pub`. Whatever ruling 6 decides, that field changes or
  it does not, and it is one word.

### Copper Row, and its one break

- SHEET ROW: "barber and bookmaker", "barbers and betting offices supply
  different reasons to linger". A BETTING OFFICE IS A GAMBLING BUSINESS AND
  D17 BANS IT.
- ATLAS OBJECT: `paper betting slip`. Same break.
- WHAT IS ACTUALLY LOST, and this is worth saying rather than shrugging: the
  bookmaker was doing REAL DESIGN WORK. The sheet's own words are "different
  reasons to linger", and a betting shop is a room where men stand still,
  watch a wall, and talk sideways for twenty minutes. That is an information
  venue by construction.
- REPLACEMENT THAT DOES THE SAME JOB: THE LAUNDERETTE. Waiting is not
  optional in a launderette, it is enforced by the machine, it lasts a
  measurable forty minutes, it puts strangers in a room with nothing to do,
  and it is period-perfect for 1990. The built street ALREADY HAS ONE: the
  Steam Laundry on bay 4, `decal_03_fascia_steam_laundry`, authored and
  generated. Copper Row gets a second, smaller one.
- REPLACEMENT FOR THE OBJECT: a PAWN TICKET. Period, about money and
  desperation rather than luck, and Rita's Pawn is already on the built street.
- COPPER ROW'S VENUE, the Market Hall, IS UNTOUCHED. The district survives; two
  props and one clause change.

### The Exchange

CLEAN. 0 hits in the sheet row, 0 in its four objects (`brass nameplate,
document trolley, venetian blind, landline`), and its venue is a cafe. Nothing
to do.

### The Parade, and it is the big one

- SHEET ROW: "Cinema, DRINK TRADE, taxi calls, occasional contemporary cafe or
  WINE-BAR refits". Three hits, two real breaks, and the district's stated
  identity is one of them.
- THE FOUR OBJECTS ARE ALL CLEAN: `queue rope, cinema poster case, ashtray,
  taxi landline notice`. Tobacco is not covered by D17 and the ashtray stays.
  THE TAXI LANDLINE NOTICE IS A GIFT: the atlas already put a cab telephone on
  the Parade before anybody proposed a cab office.
- THE VENUE, the Tivoli, IS CLEAN and is a cinema.
- THE REDESIGN IS FILE 06, with pictures, as commissioned.

### Fairview

CLEAN. 0 hits, and its objects are a washing line, a garden gate, a milk bottle
and a school satchel. Nothing to do.

### Ironside, WHICH THE SCANNER MISSED

- The sheet row scores 0 alcohol hits and 0 gambling hits. THE WORD LIST SEES
  NOTHING.
- READ IT INSTEAD: Ironside's only information venue is I1, THE CLOCKING-IN
  CLUB, typed `club`. A working men's club in a British industrial district in
  1990 is a drinking institution, and its whole social function ran on a bar.
  Under D17 it cannot be shown serving.
- THE PARITY ARGUMENT SAVES IT. D17 says pubs may exist as places. A club is
  the same kind of thing and the same clause reaches it, so the Clocking-in
  club EXISTS. What it needs is a reason to be full that is not drink, exactly
  as the pub does.
- WHAT THIS FILE DOES NOT DO, under the scope boundary the coordinator ruled
  on 2026-09-10 and filed as `production/queue/245`: IT DOES NOT SAY WHAT THE
  ROOM IS FOR. That is the same question as the pub's and it belongs to the
  lane writing `production/specs/the-pub-without-drink.md`. A first draft of
  this section proposed a programme for the room, a canteen, a reading room, a
  snooker table and a union notice board, and it is WITHDRAWN as over the
  line.
- WHAT THIS FILE DOES SAY, which is the finding and is properly its own:
  IRONSIDE'S ONLY INFORMATION VENUE IS AFFECTED, nobody has noticed, and it is
  not in anybody's commission. It should be referred to the same lane and to
  the same question, and it should be referred TODAY, because the answer that
  lane reaches for the pub is almost certainly the answer for this room too and
  it would be absurd to solve the same problem twice a fortnight apart.

### Gullwing, WHICH THE SCANNER ALSO MISSED

- 0 hits in the sheet row. The object list has `arcade cabinet` and the venue is
  G1, the WINTER ROOMS ARCADE.
- READ IT INSTEAD: an amusement arcade on a British seafront in 1990 is, in
  large part, a room full of AMUSEMENT WITH PRIZES machines. That is gambling.
  The district's only information venue is a gambling hall.
- WHAT SURVIVES INTACT: video game cabinets are NOT gambling. A photo booth is
  not. A seafront attraction hall is not.
- THE DIRECTION THIS POINTS, and it is a direction and not a programme, because
  the room's contents are the other lane's question under queue 245: the
  distinction that saves Gullwing is between a GAMING arcade and an ATTRACTION
  hall. The atlas's own object, `arcade cabinet`, already reads as a video
  cabinet, which is what it always looked like, and a video cabinet is not a
  wager. THE DECISION THIS NEEDS, stated rather than assumed: whether a prize
  machine of any kind may ever appear. The safe reading of D17 is that it may
  not.
- THE SAME REFERRAL AS IRONSIDE. Gullwing's only information venue is affected
  and it is in nobody's commission.

## 2b. D18, ruled the same day, and it changes the count in section 1

`ledger-v2/respec/decision-register/D18-*.md` was ruled by Jafar on 2026-09-10,
the same day as this commission, and it EXTENDS D17 rather than replacing it.
It was read after this file was drafted, and it is recorded here rather than
folded in silently because it moves a number.

WHAT D18 ADDS THAT REACHES THIS PASS: tobacco stays; violence stays without
torture or cruelty as spectacle; killing is possible, rare, permanent and
remembered; full period swearing with no slurs; drugs as an off-screen economy
never shown; no prostitution and no sexual content; religion present and never
mocked; police corruptible as individuals and never as a thesis. AND THE ONE
THAT LANDS ON THE DISTRICTS:

**NO CHILDREN ANYWHERE, AND THE SCHOOL STANDS CLOSED for the game's window.**

D18 names some of its own damage, including the outside Fairview sheet and its
FAIRVIEW SCHOOL sign. What it does not name, and what this pass adds:

1. FAIRVIEW'S INFORMATION VENUE IS AFFECTED AFTER ALL. Section 1 marks F1,
   `Chapel / school gate`, CLEAN under D17, and that is still true. Under D18
   half of it closes. THE VENUE SURVIVES AS THE CHAPEL, because D18 says
   religion is present as part of life and never mocked, and the school gate
   becomes a closed gate with a chain on it, which is a stronger image than an
   open one and costs nothing.
   SO THE REVISED HEADLINE IS: D17 TOUCHES 3 OF THE 7 INFORMATION VENUES AND
   D17 PLUS D18 TOUCHES 4 OF THE 7. Three are untouched: the Market Hall, the
   Records Court cafe and the Tivoli.
2. FAIRVIEW'S OBJECT LIST. `school satchel` is one of its four characteristic
   objects and the atlas draws it on the sheet. The object is not banned; its
   MEANING is, because a satchel with nobody to carry it is a prop with no
   owner. Replacement in the same spirit as the Hook's firkin: a WIRE MILK
   CRATE ON A DOORSTEP, which is already the district's second object, or a
   canvas shopping bag on a garden wall.
3. ONE OF THE ATLAS'S FOUR DAILY FLOWS IS A SCHOOL RUN. `working_town` WT2 is
   "Homes to school to market, 08:15 and 15:15", from Foundry Court to the
   Market Hall by way of F1. THE MIDDLE LEG IS VOID. The flow itself survives
   with its times and its endpoints: people go from the hill to the market in
   the morning and back in the afternoon, and they no longer stop at a gate on
   the way.
4. AND IT CAUGHT THIS COMMISSION'S OWN WORK. The first draft of
   `data/cab-operations.json` had a school run in the Tuesday routine twice
   and a school contract in the accounts. All three are corrected in that file
   and the correction is recorded in it, because a peak with no cause is worse
   than a peak with the wrong cause.

WHAT D18 DOES NOT CHANGE ANYWHERE IN THIS PASS: the Hook, Copper Row, the
Exchange, the Parade, Ironside and Gullwing findings are all unaffected. The
Parade design in file 06 contains no children and its image spec now carries
D18's clause positively, validated at `problems=0/1itemsExamined`.

## 3. What D17 breaks outside the district sheets

### The generated image library

`imagesInLibrary=45 d17RelevantImages=4/45`, and the four are not equal.

| id | what it draws | verdict |
|---|---|---|
| `fascia_mickeys` | a signboard reading MICKEY'S | SAFE. The prompt says "pub fascia", but the ARTIFACT is a name on a board, and D17 lets pubs exist as places. Nothing to redraw. |
| `poster_bingo` | a poster reading BINGO, EVERY NIGHT | BREAKS. Gambling, drawn, shipped. AND IT CARRIES A SECOND FAULT: its `binds_to` says "the amusement arcade window, Quay Street". Quay Street is in the Hook and the atlas puts the arcade in Gullwing, so the image library and the atlas disagree about where the town's arcade is. |
| `poster_darts` | a darts league fixture sheet | THE ARTIFACT IS SAFE. Darts is neither drink nor a wager. Its BINDING breaks: "the Sailors' Rest, pinned by the bar". |
| `interior_bar_back` | the back of a bar, facing bottle shelves | BREAKS. It is the only D17 break among the ten generated decals actually PLACED on the built street. |

`generatedDecalsPlacedOnTheStreet=10 ofThoseD17Relevant=2/10`, and of those two
one is `fascia_mickeys`, which is safe. SO THE 593-PIECE STREET CARRIES EXACTLY
ONE D17 BREAK: `decal_05_interior_bar_back`, at x=18.000. That is a smaller
number than anybody would guess and it is worth stating plainly.

A CURIOSITY IN THE SAME ROW, found by reading rather than by the scanner:
`interior_bar_back`'s own `binds_to` says "the card behind Mickey's lit
window", but the piece list places it at x=18.000, which is bay 2, under
`decal_02_fascia_ritas_pawn`. So the shipped street has a bar back behind a
pawnshop window and Mickey's own window shows shop shelves. That mismatch
predates D17 and is not this commission's to fix, but whoever replaces the
decal should know the intent and the placement never agreed.

### A brand nobody minted

`poster_darts` and `tools/imagegen/prompts.json` both name THE SAILORS' REST, a
pub. It is in no canon line and no brand bible entry. That is not a D17 finding,
it is a brand-bible finding found while doing this one, and it is reported
because a shipped image naming an unminted business is exactly the class of
thing the bible exists to prevent.

### The dialogue banks, and this is the most interesting number in the file

| bank | lines | alcohol lines | gambling lines | UNTOUCHED |
|---|---|---|---|---|
| `pub-regular-v1` | 48 | 12 | 2 | 34 of 48 |
| `crime-witness-v1` | 24 | 2 | 0 | 22 of 24 |

THIRTY-FOUR OF THE FORTY-EIGHT LINES IN THE PUB REGULAR BANK SURVIVE D17 WORD
FOR WORD. And of those 34, a judged read finds 31 THAT NAME NO ROOM FEATURE AT
ALL: no stool, no counter, no round, no pumps. Lines like "Police wagon went up
Quay Street twice today. Twice is a pattern, once is a Tuesday." are not pub
lines. They are TOWN lines said by a man who is sitting down somewhere.

That number cuts both ways and both cuts are reported in section 5 and in
`07-CASE-FOR-THE-PUB.md`, because a package that only argues its own side is
not a decision aid.

### One number that looks alarming and is not

`tools/imagegen/prompts.json` scores 36 alcohol hits and 13 gambling hits, more
than any other file, and only 4 of its 45 items are D17-relevant. The
explanation is that most of the hits are INSIDE THE GUARD: the forbidden-token
list that keeps real brewery trade marks out of generated images contains the
names of breweries. A gate that lists what it forbids will always trip a
scanner that looks for the same words. THIS IS THE FALSE-POSITIVE CLASS THE
STUDIO HAS ALREADY RECORDED TWICE, learning entries L2 and L19, and the
recorded answer is REWORD, NEVER LOOSEN. Nothing here suggests loosening
anything, and this scanner's pattern was not widened to hide it.

## 4. What D17 does NOT break, counted

Because a pass that only lists damage is not a pass.

- FOUR OF THE SEVEN information venues: the Market Hall, the Records Court
  cafe, the Tivoli, the chapel and school gate.
- TWENTY-SIX OF THE TWENTY-EIGHT district objects in the atlas.
- FIVE OF THE SEVEN district sheet rows.
- ALL 593 PIECES OF THE BUILT STREET. Not one piece of geometry is affected:
  `production/specs/vignette-pieces.json` scores 0 alcohol hits and 0 gambling
  hits over 704 lines. The break is one decal, not a wall.
- FORTY-ONE OF THE FORTY-FIVE generated images, and 8 of the 10 placed ones.
- FIFTY-SIX OF THE SEVENTY-TWO authored dialogue lines across the two banks.
- THE WHOLE OF FAIRVIEW AND THE WHOLE OF THE EXCHANGE.
- THE TOWN'S SHAPE. Not one route, contour, block, transition or work flow in
  the atlas is touched. `working_town`'s four daily flows all survive: a
  packing shift going to Mickey's at 17:30 is a man going somewhere after work,
  and what he does when he gets there is the thing ruling 6 is about.

## 5. The three things this pass recommends, none of them decided here

1. IRONSIDE AND GULLWING SHOULD BE REFERRED TO THE LANE WRITING
   `production/specs/the-pub-without-drink.md`, TODAY. They are not in this
   commission, they are the same problem, and they are the same QUESTION: a
   room whose social function ran on something D17 forbids, which now needs a
   reason to be full. Whatever answer that lane reaches for the pub is very
   likely the answer for a works club and for a seafront attraction hall, and
   solving one problem three times a fortnight apart would be the waste this
   referral exists to prevent. Their street-side treatment, which IS this
   lane's kind of work, should follow after the Parade sheet the same way.
2. THE ONE STREET BREAK SHOULD BE REPLACED, NOT DELETED.
   `decal_05_interior_bar_back` is a lit interior card at x=18.000. Under D17 a
   pawnshop's own interior behind that window is a better card than a bar was:
   a grille, a shelf of unredeemed things, a single hanging bulb. One
   generation, one manifest row, and the street gains rather than loses.
3. THE WORD-LIST GATE D17 ORDERS SHOULD BE BUILT KNOWING WHAT IT CANNOT SEE.
   D17's enforcement point 3 asks for "a word-list gate over dialogue banks and
   spoken lines". This pass shows a word list finds 14 of 48 lines in one bank
   and MISSES TWO ENTIRE DISTRICTS, because "club" and "arcade" are ordinary
   words. A gate is worth building and it must ship with its own limit printed
   beside it, or the first clean run will be read as an all-clear.

## 8. The compliance record, moved here from the delivery

RULED by the coordinator 2026-09-10, one step on from the section 14 ruling
that governs section 6 of `DELIVERY.md`. The standing rule is that A CORPUS
FILE DESCRIBES WHAT IS THERE. `production/art/*/DELIVERY.md` is corpus by
`tools/content-gate.py:798-800`; THIS FILE IS NOT. A delivery that also REPORTS
ON COMPLIANCE mixes two kinds of writing, and only one of them belongs in a
scanned file, so the compliance half lives here and the delivery points at it.

Five items moved. NOTHING IS DELETED AND NO ZERO IS DROPPED: a zero is evidence
and it survives the move in its exact key=value form, because a paraphrase of a
reading is not the reading.

### 8.1 The generated image library, classified

`d17RelevantImages=4/45`. The four, by id, with the verdict already argued in
section 3 of this file: `fascia_mickeys` SAFE as an artifact, `poster_bingo`
BREAKS on gambling, `poster_darts` SAFE as an artifact with a broken binding,
`interior_bar_back` BREAKS.

AND THE SECOND FAULT IN THE SAME ROW: `poster_bingo`'s `binds_to` reads "the
amusement arcade window, Quay Street". Quay Street is in the Hook and the atlas
puts the town's arcade in Gullwing, so the image library and the atlas disagree
about where the arcade is. That is a district finding hiding inside an asset
row and it is the reason this classification is worth keeping at all.

`generatedDecalsPlacedOnTheStreet=10 ofThoseD17Relevant=2/10`, and one of the
two is `fascia_mickeys`, which is safe. SO THE 593-PIECE STREET CARRIES EXACTLY
ONE BREAK: `decal_05_interior_bar_back`, at x=18.000. The pieces themselves
score `alcoholHits=0 gamblingHits=0` over 704 lines.

### 8.2 The dialogue banks, counted per line

    pub-regular-v1:   lines=48 alcoholLines=12 gamblingLines=2 untouched=34/48
    crime-witness-v1: lines=24 alcoholLines=2  gamblingLines=0 untouched=22/24

And of the 34 untouched lines in the first bank, 31 NAME NO ROOM FEATURE AT
ALL. That number cuts both ways and both cuts are argued in
`07-CASE-FOR-THE-PUB.md` section 2.

### 8.3 The Parade image spec, content-scanned

The spec at `data/parade-night-sheet-2026-09-10.json` carries atlas strings and
is gated from generation by `production/queue/244`. Scanned separately, because
a clean spec is not a lifted gate:

    atlasStringsCarriedIntoTheSpec=10 d17OrD18Dirty=0/10
    promptWords=577 alcoholHits=0 gamblingHits=0 childrenWord=False

THE ZEROS ARE THE EVIDENCE AND THEY ARE PRINTED IN FULL. The ten strings are
the four Parade materials, the four Parade objects, the venue and the route.
None of the ten is alcohol, gambling or a child.

THE GATE STILL APPLIES REGARDLESS: the rule is about the mechanism and not
about this author's judgement, and a clean spec composited by a leaking
compositor is still a leak.

### 8.4 The rule has two numbers

The register carries D17, "no alcohol and no gambling", and D18, the permanent
content rule that extends it, both ruled 2026-09-10. `tools/imagegen`'s refusal
message names D18; the coordinator names D18; this package's files were drafted
against D17 and carry the D18 delta at section 2b above. NEITHER IS STALE, but
a reader who meets only one of them will think the other is, and the two
records should cross-reference each other.

### 8.5 Why this section exists at all

The director considered exempting `DELIVERY.md` from the content gate and
REFUSED, because that file can describe visible art and un-scanning it would
blind 262 other strings. That reasoning holds and this section is not a way
round it. What it separates is two kinds of writing that were sharing one file:
a description of what is on the sheet, which is scanned, and a report on
compliance, which names the rule's own categories in order to say a count and
therefore cannot survive a scan by construction.
