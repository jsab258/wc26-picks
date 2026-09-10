# DELIVERY: art/mickeys-cars

STATUS: SPEC AUTHORED AND VERIFIED, NO RUN STARTED, NOTHING COMMITTED,
2026-09-10. Written in-house in the studio checkout under the in-house clause
of `game-design/art-collaboration.md` section 2, so nothing outside
`production/art/mickeys-cars/` was written or modified.

THE WORD DELIVERED IS NOT USED ABOUT THE PICTURES. Two drawn sheets exist for
the Parade and one photoreal sheet is SPECIFIED AND NOT RUN:
`generationRunsStarted=0 imagesGenerated=0`.

This file is written to be accurate rather than optimistic. What is here is
here; what is not is named below with the same weight.

## 1. What Jafar commissioned, and what came back

| commissioned | delivered | where |
|---|---|---|
| research on the minicab trade 1988 to 1992 | 43 numbered rows, labelled | `01-RESEARCH-minicab-trade-1988-1992.md` |
| plans and elevations to the pub package's standard | 5 measured sheets, SVG and PNG, plus the layout as data | `02-SPEC-plans-and-elevations.md`, `data/cab-office.json`, `drawings/` |
| a gameplay sheet in his five named parts | overhear, the book, the radio, the yard, the escape | `03-GAMEPLAY-sheet.md` |
| hours, returns and interface notes | all three, plus the quality ladder | `04-HOURS-RETURNS-INTERFACE.md`, `data/cab-operations.json` |
| a town-wide D17 pass over every district sheet and the atlas | 7 districts, 7 venues, counted, plus a D18 delta | `05-D17-town-pass.md`, `verify/d17_scan.py` |
| the Parade's nightlife redesigned without drink, with pictures | 2 drawn sheets now, 1 photoreal sheet specified and not run | `06-PARADE-nightlife-without-drink.md`, `data/parade-night.json`, `data/parade-night-sheet-2026-09-10.json` |
| the honest case FOR the pub | the comparative case, with a checklist for what would have to be true | `07-CASE-FOR-THE-PUB.md` |

## 2. Every file, by path

    production/art/mickeys-cars/
      DELIVERY.md                                   this file
      01-RESEARCH-minicab-trade-1988-1992.md        199 lines
      02-SPEC-plans-and-elevations.md               176 lines
      03-GAMEPLAY-sheet.md                          227 lines
      04-HOURS-RETURNS-INTERFACE.md                 168 lines
      05-D17-town-pass.md                           336 lines
      06-PARADE-nightlife-without-drink.md          224 lines
      07-CASE-FOR-THE-PUB.md                        166 lines
      data/cab-office.json                          the layout, every number
      data/cab-operations.json                      hours, returns, accounts, people
      data/parade-night.json                        the Parade identity
      data/parade-night-sheet-2026-09-10.json       image spec, schema 2, NOT RUN
      author/draw_cab_office.py                     5 sheets from the data
      author/draw_parade_night.py                   2 sheets from the data
      verify/check_cab_office.py                    6 checks, selftest, 0 findings
      verify/d17_scan.py                            read-only scanner, selftest
      drawings/cab-ground-plan.{svg,png}
      drawings/cab-front-elevation.{svg,png}
      drawings/cab-counter-section.{svg,png}
      drawings/cab-yard-and-escape.{svg,png}
      drawings/cab-street-rank.{svg,png}
      drawings/parade-night-elevation.{svg,png}
      drawings/parade-night-clock.{svg,png}

29 files. Nothing outside this directory.

## 3. The design, in five sentences

Mickey's Cars is a private hire office on bays 0 and 1 of Quay Street, 12.0 by
8.0 m, with the party wall between the two bays LEFT STANDING and one 1.000 m
opening cut in it behind the counter, so the public and the drivers are never
in the same room and both can hear the radio. The public half is a waiting
room, a counter with a glazed screen and a 0.30 by 0.25 m speaking gap, and a
control side with the radio, the two telephones and THE BOOK, which section 56
of the Local Government (Miscellaneous Provisions) Act 1976 requires the
operator to keep with the time, the hirer, the pick-up and the destination of
every journey. The trade's half is a drivers' room entered by its own door,
the proprietor's corner, and a lock-up sub-let for cash to a man who repairs
television sets and whose partition stops 0.700 m short of the ceiling. Behind
both is the pub package's own yard, widened, with its 1958 WC, which every
driver crosses at every hour of the night. The cars stand at the kerb, because
the yard was MEASURED and refused: a car cannot turn from a 2.4 m lane through
a 1.2 m gate.

## 4. What was measured, with denominators

`python3 production/art/mickeys-cars/verify/check_cab_office.py`, 6 checks,
`findings=0`:

- six front openings moved by `0.000 mm`, `6/6` against the street's pieces
- `45` content boxes parsed of 48 designed items; the 3 that are heaps rather
  than objects are PRINTED BY NAME rather than skipped
- `0/45` outside the carcass; `0/45` naming a surface outside the 16 in
  `asset-interface.md`
- the car board is seen from `9/21` footway positions 0.5 m apart, u 2.0 to 6.0
- the book is BLOCKED: the ray crosses the counter face at 0.973 m under a
  1.050 m top
- the net separates hands from heads at the glass by 0.123 m, which is the
  thinnest margin in the package and is printed because it is thin
- routes: `0 clashes in 724 samples` over 6 routes at a 0.30 m body, against 26
  blocking objects, with 16 more passed under and 3 flush, and the split
  printed
- selftest: accepting case first, `0` findings added; synthetic rejecting case
  caught

`python3 production/art/mickeys-cars/verify/d17_scan.py`, read only, selftest
passes.

`python3 tools/canon-gate.py` over the 14 prose, data and code files:
`clean, 0 findings in 14 files, 5208 lines examined, 13 era terms and 45 brand
tokens screened`. ONE REAL FINDING WAS FIXED TO GET THERE: the word carcass had
been written as a screened brand token in four places, which is the correction
`atlas-02` already had to make on 2026-09-08. REWORD, NEVER LOOSEN, and the
gate was not touched.

THE FIFTEENTH FILE IS EXCLUDED FROM THAT RUN AND HERE IS WHY, rather than
hidden: `data/parade-night-sheet-2026-09-10.json` scores 45 canon-gate findings
because it CONTAINS THE FORBIDDEN-TOKEN LIST, copied byte for byte from
`tools/imagegen/prompts.json` as the schema requires. The gate reads the same
list and reports the file for containing it. This is the recorded
false-positive class and it is precedented in this lane's own most recent spec:
`production/art/concept-fairview-2026-09-10/fairview-sheet-2026-09-10.json`
scores 50 findings for the same reason on the same day.

`tools/imagegen`'s own validator over that spec: FIRST RUN `problems=2/1`, both
correct refusals; SECOND AND THIRD RUNS `problems=0/1itemsExamined`,
`posExclusionHits=0/637wordsScanned`, `forbiddenTokenHits=0/107tokens`,
`negativeActive=False`, estimated 152 seconds.

## 5. The research rows that are UNSOURCED, named as the report asks

Seven of the 43 numbered rows are UNSOURCED, and they are not facts.

| row | what could not be found |
|---|---|
| R5 | whether a provincial firm in 1990 used procedure words on air, numbered or lettered its cars, or had selective calling |
| R6 | WHICH BODY licensed a private mobile radio base station in Britain in 1990, under which Act, in which band, at what spacing, at what cost. ELEVEN SEARCHES, NOT ANSWERED. |
| D5 | what a private hire vehicle's council plate looked like, and whether one or two were required. It VARIES BY DISTRICT, which is the point of L1. |
| D6 | what a driver earned in a week in 1990 |
| M4 | any 1990 tariff, meter rate, licence fee or radio rent figure |
| O1 | whether provincial counter screens existed in 1990 |
| O-section | THE LARGEST HOLE: no photograph, plan, floor area or written description of the interior of ANY British minicab office between 1988 and 1992 was found. Not one. |

Three more rows are CITED-VIA-SEARCH-MODERN, which is a weaker label than it
looks: D1, M2 and M3 describe the weekly settle and the account docket from
PRESENT-DAY industry sources and COULD NOT BE DATED TO 1990. They are used
because they are the only descriptions found, and if the CI fetch job finds
they are a later practice, section 2 of `04-HOURS-RETURNS-INTERFACE.md` is what
changes.

AND THE CHANNEL, MEASURED TODAY: `hostsTried=4 hostsReachable=0/4`.
`legislation.gov.uk`, `api.parliament.uk`, `en.wikipedia.org` and a council PDF
host all answered EGRESS_BLOCKED. `rowsTotal=43 cited=0/43`. NOT ONE ROW IN THE
FILE READ A PAGE IN FULL. Queue 156 is the fix; add
`legislation.gov.uk/ukpga/1976/57/part/II` to its targets and 14 rows upgrade
in one run.

## 6. What the D17 pass found across the districts

THE HEADLINE, with its denominator: the atlas places exactly ONE information
venue in each of the seven districts. D17 touches THREE of the seven. D17 plus
D18 touches FOUR. Three are untouched: the Market Hall, the Records Court cafe
and the Tivoli.

| district | venue | verdict |
|---|---|---|
| the Hook | Mickey's, typed `pub` | TOUCHED, and it is ruling 6 itself. One of its four characteristic objects is void; A STENCILLED FISH BOX replaces it. |
| Copper Row | Market Hall | VENUE CLEAN. One clause of its sheet row is void and one of its four objects with it. A LAUNDERETTE does the same design job better, and the built street already has one. |
| the Exchange | Records Court cafe | CLEAN. 0 findings in the whole row and in all four of its objects. |
| the Parade | the Tivoli | VENUE CLEAN. Two of the five clauses in its sheet row are void and three survive. ALL FOUR of its characteristic objects survive, including the taxi landline notice. |
| Fairview | chapel and school gate | CLEAN UNDER D17, TOUCHED UNDER D18: the school stands closed, so the venue survives as THE CHAPEL and one of its four objects loses its meaning. |
| Ironside | Clocking-in club | TOUCHED, AND THE WORD-LIST SCANNER DID NOT SEE IT. Referred to the pub-without-drink lane. |
| Gullwing | Winter Rooms arcade | TOUCHED, AND THE SCANNER DID NOT SEE THAT EITHER. Referred the same way. |

The removed objects and the sheet-row phrases are named in `05-D17-town-pass.md`, which is the removal record; a delivery describes what is on the sheet and does not name what came off it (ruling 2026-09-10 section 14).

OUTSIDE THE DISTRICT SHEETS: the generated image library was classified image
by image, and the built street carries EXACTLY ONE BREAK out of the ten
generated decals placed on it. One of the four flagged images also disagrees
with the atlas about which district the town's arcade is in, which is a
district finding hiding inside an asset row. THE CLASSIFICATION, THE ASSET IDS
AND THE FULL COUNTS ARE IN `05-D17-town-pass.md` SECTION 8.1.

THE MOST INTERESTING NUMBER IN THE PASS, and it cuts both ways: of the 48 lines
in `pub-regular-v1`, 34 SURVIVE UNTOUCHED, and of those 34, 31 name no room
feature at all. THE PER-LINE COUNTS FOR BOTH BANKS ARE IN `05-D17-town-pass.md`
SECTION 8.2.

FOUND WHILE DOING THE PASS AND NOT PART OF IT: the generated image library and
`tools/imagegen/prompts.json` both name THE SAILORS' REST, a pub that is in no
canon line and no brand bible entry. That is a brand-bible finding and it is
reported rather than fixed.

## 7. What is NOT in this commission

- NO GLB, NO MESH, NO TEXTURE, NO IMPORT, NO ENGINE RUN, NO BLENDER. Blender is
  not installed here. The five cab sheets and two Parade sheets are MEASURED
  ORTHOGRAPHIC DRAWINGS and not renders, and each one says so on its own face.
- NO GENERATION RUN. `generationRunsStarted=0 imagesGenerated=0`. The photoreal
  Parade sheet is a validated spec and nothing more.
- NO CANON CHANGE, and the one the cab office would need is named instead:
  `canon.md` line 10 and line 48 both say the pub, and BOTH WOULD HAVE TO BE
  EDITED BY JAFAR. Nothing here pre-empts that.
- NO INTERIOR OF A LICENSED ROOM. The coordinator ruled the boundary on
  2026-09-10 (`production/queue/245`) and it reached three places in this
  package: the Institute Hall's interior in the Parade file, and the Ironside
  and Gullwing room proposals in the D17 pass. ALL THREE ARE WITHDRAWN IN
  PLACE, with the withdrawal written into the file rather than reworded away.
- NO MINTING. The nine Parade unit names, the borough council, and the radio
  set's maker are PROPOSALS for the brand bible.
- NOTHING ADDRESSED TO JAFAR, and no status report. The taste questions are at
  the bottom of this file as cards for the Producer to route.

## 8. The do-not-touch list, and an honest problem with proving it

MEASURED, not asserted, with `git status --porcelain -- <path>`:

    production/d1-probe/DISPATCH   modifiedPaths=0
    .github/workflows              modifiedPaths=0
    production/next-three.json     modifiedPaths=0
    CLAUDE.md                      modifiedPaths=0
    .claude/rules                  modifiedPaths=0
    ledger-v2/studio-v2            modifiedPaths=0

All six clean. Every file this commission wrote is one of the 29 under
`production/art/mickeys-cars/`, and that directory is a single `??` entry.

AND HERE IS THE PROBLEM, reported rather than glossed: `git status --porcelain`
over the whole tree shows 746 modified paths outside this directory, including
`canon.md`, `content/brands/` and `tools/imagegen/`, all of which are the two
other agents named in this commission's brief. THE IN-HOUSE CLAUSE SAYS THE
RESIDENT PRINTS `git status --porcelain` TO PROVE THE LIST HELD. THAT PROOF
DOES NOT WORK WHEN THREE AGENTS SHARE ONE CHECKOUT: the command cannot
attribute a change to an author. The six scoped readings above are the strongest
proof available from this container, and the convention should be told so.

## 8b. THE IMAGEGEN GATE, and what this commission ran

Ruled by the coordinator 2026-09-10, blocked on `production/queue/244`: do not
run `tools/imagegen/sheet-furniture.py` and do not dispatch imagegen for
anything reading `ATLAS_BLOB`. Hand-authored SVG and PNG drawings are not
affected; citing the atlas in a document is not affected.

VERIFIED IN THIS CONTAINER RATHER THAN ACCEPTED: `ATLAS_BLOB` is
`sheet-furniture.py:49` and `sheet-furniture.py` is the ONLY file in
`tools/imagegen/` that reads that branch. `imagegen.py` contains zero
references to the atlas.

WHAT THIS COMMISSION RAN:

    sheetFurnitureInvocations=0  imagegenDispatches=0  imagesGenerated=0
    imagegenFunctionsCalledReadOnly=10  ofThoseSideEffecting=0/10

The ten are `load_spec`, `spec_line`, `validate_spec`, `build_prompt`,
`build_negative`, `scan_exclusions`, `check_forbidden`, `item_cfg`,
`negative_state`, `estimate_seconds`. The validation path and the gated path
are DISJOINT, and that is a reading, not an assurance.

`data/parade-night-sheet-2026-09-10.json` CARRIES ATLAS STRINGS and is
therefore exactly the file that would trip the leak if composited. It is
stamped DO NOT GENERATE in its own `_STATUS` and `_GATE` blocks and it stops at
a validated spec.

THE SPEC'S OWN ATLAS STRINGS WERE SCANNED SEPARATELY, because a clean spec is
not a lifted gate. Ten strings carried, the prompt 577 words, and every reading
came back at zero. THE GATE STILL APPLIES REGARDLESS: the rule is about the
mechanism, and a clean spec composited by a leaking compositor is still a leak.
THE COUNTS, WITH THEIR ZEROS INTACT, ARE IN `05-D17-town-pass.md` SECTION 8.3
AND IN THAT SPEC'S OWN `_STATUS` BLOCK. Neither file is corpus.

## 8c. Two answers to the pub question, on purpose

`production/specs/the-pub-without-drink.md` is being written by a separate
lane, commissioned before `07-CASE-FOR-THE-PUB.md` existed. The coordinator has
acknowledged the overlap as their own error and ruled that BOTH ARE FINISHED
AND BOTH ARE READ, with one named as the reference rather than the two
averaged. Nothing here is trimmed for it. The two answer the same question from
different places: the other lane answers it directly, and this one answers it
as the comparative case inside the package the decision is made from.

## 9. Two numbers that moved under this commission and are somebody else's

1. `tools/imagegen/prompts.json` carried 107 forbidden tokens when this
   commission copied them; the Fairview sheet of the same day records 45, and
   `tools/canon-gate.py` still reports 45 screened because it now SUBTRACTS the
   content-rule tokens. Three counts of one list. Nothing is wrong; a reader
   comparing them without this paragraph would think something was.
2. THE RULE HAS TWO NUMBERS, D17 and D18, both ruled 2026-09-10 and the second
   extending the first. The tool's refusal message names one; the coordinator
   names one; this package's files were drafted against the other and carry a
   delta at section 2b of the town pass. NEITHER IS STALE, and WHICH IS WHICH
   IS SET OUT IN `05-D17-town-pass.md` SECTION 8.4. But a reader who
   meets only one of them will think the other is, and the two documents should
   cross-reference each other.

## 10. Taste cards for the Producer to route, each with a default

CARD 1: PUB OR CAB OFFICE, which is ruling 6 itself.
DEFAULT: THE PUB STAYS, as Jafar's own message says, until he rules. This
package's job was to make the cab office good enough to lose to fairly, and
`07-CASE-FOR-THE-PUB.md` argues the other side with a testable checklist of
what would have to be true. The one fact worth putting on a card: A PUB SHUTS
AT ELEVEN AND THIS ROOM IS BUSIEST AT MIDNIGHT, and the studio has already
ruled that the last bus goes at half past ten because the walk home through a
dark port town is where the game happens.

CARD 2: IS THE BOOK A READABLE OBJECT OR AN INTERFACE PANEL?
DEFAULT: A READABLE OBJECT, drawn from a small set of pre-generated pages. The
cab office's best idea is a book with six columns of who went where; it is only
worth what it says, and the street's text route today is a generated image
baked into an atlas page, which can draw a page but not NEXT WEEK'S page. Three
rungs are named in `04-HOURS-RETURNS-INTERFACE.md` section 3. This is a feel
question, not a technical one, which is why it is a card.

CARD 3: MAY A PRIZE MACHINE EVER APPEAR?
DEFAULT: NO. It is the safe reading of D17 and it is what saves Gullwing's
arcade as an attraction hall rather than a gaming one. The Parade's amusements
contain none. If the answer is yes with conditions, two district identities
change and it should be said once rather than argued three times.

CARD 4: THE AUTHORITY'S NAME.
DEFAULT: DRAW IT ILLEGIBLE UNTIL CANON MINTS IT. A private hire office displays
an operator's licence and its cars carry a council plate, so the licensing
authority's name is a visible object in this design. `canon.md` mints the
Meridian Harbour Board and no council. BOROUGH OF MERIDIAN is proposed and not
minted, and until it is the plate is drawn with the authority line unreadable.

## 11. The quality ladder at close

Asked as `production/quality-ladder.md` requires: best available, or first
working? The full table is section 4 of `04-HOURS-RETURNS-INTERFACE.md`. In one
line each:

- LICENSING RESEARCH: first working, and the next rung is queue 156 with one
  URL added to it.
- THE OFFICE INTERIOR RESEARCH: NOT WORKING, and it says so. No source exists
  in reach.
- THE LAYOUT: best available for a layout. Measured, 0 findings over 6 checks,
  and THE INSTRUMENT CHANGED THE DESIGN FOUR TIMES, once because the lock-up's
  bench ran across the lock-up's own door.
- THE DRAWINGS: first working. Vector, measured, not renders. The next rung
  needs the Windows runner.
- THE PARADE PICTURES: SPEC ONLY, RUN NOT STARTED, and this file says so in its
  first paragraph.
- THE INTERFACE: an ask, not a design. Card 2.
