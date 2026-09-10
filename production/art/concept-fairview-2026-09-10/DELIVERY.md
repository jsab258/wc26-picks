# DELIVERY: art/concept-fairview-2026-09-10

STATUS: SPEC AUTHORED AND VERIFIED, RUN NOT STARTED, 2026-09-10. Written
in-house in the studio checkout under the in-house clause, so nothing outside
`production/art/concept-fairview-2026-09-10/` was written or modified.

WHAT IS IN THIS COMMISSION: one image spec, one sentinel entry, and the
provenance table that is the point of the exercise. NO IMAGE EXISTS YET. The
run is the resident's: the sentinel push belongs to them and the game lane
holds the runner today by Jafar's queueing rule, so this commission stops at
the validated spec on purpose, and the word DELIVERED is not used.

## 1. The ruling this executes

Jafar, 2026-09-10: the local image lane is the concept route, the outside
sheets stay as reference, ours are produced by the three-pass method, and the
remaining six district sheets follow one per day. The next sheet is the test of
original concept art: its prompt is authored from the form bible, the atlas and
the research, with no use of the outside account's prompt files, sent beside
their sheet for the same district, saying which words came from which source.
And: the outside account is retired from production, so this is the production
route rather than a comparison, and the sheet has to stand on its own.

## 2. The district, and how it was chosen

FAIRVIEW, the residential hills.

Seven districts, the Hook done, six left. The outside account has a sheet for
every one of the seven plus one of Mickey's, so the side-by-side requirement
did not narrow the choice at all: all six remaining districts satisfy it. The
rule that did narrow it was WHICH DISTRICT THIS PROJECT'S OWN SOURCES CAN
AUTHOR, because that is what the test is about:

1. Two of the five research files this lane delivered on 8 September are
   Fairview files. `hillside-housing-dated-series.md` is the hill's housing as
   a dated series, 216 lines, and `household-contents-and-upstairs.md` is what
   is inside those houses, 210 lines. No other district has two.
2. The atlas names the gap this sheet fills, in its own words:
   `production/art/atlas-01/DISTRICTS.md` line 13 says of Fairview "Existing
   concept represents upper hill. R06/R07 and Plymouth R11 justify a wider
   household/terrain study". Their sheet is admittedly partial for this
   district, and the study they name as justified is the research we already
   have.
3. The atlas carries Fairview geometry an authored prompt can stand on:
   a height band of 18 to 46 m, two named routes, a named landmark, four
   materials with hex colours, and four characteristic objects.

So Fairview is where our evidence is thickest AND where their sheet is weakest
by their own note, which is the sharpest available test of whether this studio
can author a concept rather than translate one.

## 3. What was not opened

`production/art/atlas-01/data/concept-prompts.json`,
`concept-edit-prompts.json`, `concept-final-prompts.json`,
`concept-period-prompts.json` and `pilot-image-inputs.json` were NOT read, for
Fairview or for any other district.

ONE DISCLOSURE, because the point of the exercise is whether the concept is
ours. The file whose shape this spec copies,
`tools/imagegen/compare-hook-2026-09-09-pass2.json`, embeds the outside
account's HOOK prompt verbatim in its `source` block, and reading that file is
what the brief asked for. Their phrasing for a DIFFERENT district was therefore
in view while this was written. What was taken from it is the nine top-level
keys and nothing else. Two places where a reader could reasonably suspect an
echo are named in the table rather than left to be found: row 4, the paper
border, and row 46, the closing sentence.

## 4. The files

| file | what it is |
|---|---|
| `production/art/concept-fairview-2026-09-10/fairview-sheet-2026-09-10.json` | the spec, schema 2, four items, 688 by 1024 |
| `production/art/concept-fairview-2026-09-10/SENTINEL-ENTRY.txt` | the exact lines for the resident to append to `production/d1-probe/RUN-IMAGEGEN`. NOT appended here: the sentinel is the runner's discipline and the run is the resident's |
| `production/art/concept-fairview-2026-09-10/sheets/` | where the run will write. Does not exist yet |

## 5. The provenance table

48 rows, one per meaningful phrase of the prompt. Generated from the spec's own
`source.provenance` block rather than retyped, so the two cannot drift. Label
INVENTED means the phrase came from no source: 8 rows of 48 carry INVENTED
somewhere in their label, and they are rows 4, 17, 28, 33, 34, 44, 45 and 46.

EVERY PHRASE IN THE TABLE IS A VERBATIM QUOTE from the authored prompt, checked
mechanically rather than by eye: 0 of 48 rows failed a case-insensitive
substring test against the prefix, the prompt and the appended rules clause.
Three phrases had drifted from the prompt during the trim described in section
8 and were corrected to what the prompt actually says. A phrase written as two
spans joined by a slash quotes two separate places in the prompt.

NOTHING MEASURED ABOUT ORIGINALITY, 2026-09-10, per condition 6 and amendment 2
of `game-design/decision-2026-09-10-ruling-the-four-lane-batch.md`. Read the
zero above with these words beside it. What the denominator COUNTED is 48 rows
checked for exact overlap BETWEEN THIS TABLE AND THIS SHEET'S OWN PROMPT, which
is a fidelity test on the table and not a test against the contaminating text at
all. No test in this commission has been pointed at the hazard that exposure
produces, which is PARAPHRASE, and no rejecting run exists: a row copied from
`tools/imagegen/compare-hook-2026-09-09-pass2.json` has never been planted and
shown to be caught. Rows 4 and 46 are the author's own named suspicions and they
remain open. The paraphrase measure, the catching run and the blind rewrite are
section 10 of that ruling, queued and not done here.

Line numbers are as the files stand at this commit. Atlas rows cite a key path
rather than a line, because the atlas is JSON on the `origin/art/atlas-01`
branch at commit 46d7d7592a38ceeecff7954d404fcce555a6d5c9.

| # | phrase, quoted from the prompt | label | source and where | why that source says it |
|---|---|---|---|---|
| 1 | FAIRVIEW, the residential hills of Meridian, a fictional British port town | CANON | canon.md, lines 9 to 11 | canon names the seven districts and calls this one Fairview (residential hills). |
| 2 | in 1990 | CANON+DERIVED | canon.md, line 32 | canon gives the window 1988 to 1992. 1990 is its middle year, chosen so that every dated object in the research resolves to one year instead of a range. |
| 3 | Two stacked photoreal panels inside a pale paper border: top an orientation view, bottom the same district at standing eye height / Two small rows along the bottom of the sheet | ATLAS-SHEET-FORMAT | production/art/atlas-01/DISTRICTS.md, line 3 | the atlas states what a district sheet contains: an establishing image, a player-height image, materials and characteristic objects. That is the format requirement, and it is where the four-part structure comes from. |
| 4 | inside a pale paper border | INVENTED | NOTHING | a margin so the sheet reads as a printed sheet rather than a photograph. DISCLOSURE: the pass-2 Hook spec I was told to model the file shape on embeds the outside sheet's own prompt, which asks for restrained cream margins, so I had seen that a margin was wanted before I chose these words. The wording here is mine and the colour is different; the idea of a margin is not solely mine. |
| 5 | camera at 1.6 m | PROJECT-SPEC | game-design/art-collaboration.md, line 106 | 1.6 m is this project's own eye height for the built street, and the judgement rule in game-design/town-plan.md lines 48 to 51 is that every phase is judged on player-height stills. |
| 6 | from the crest road at 40 m, looking south and downhill | ATLAS+DERIVED | production/art/atlas-01/data/atlas.json, routes id=crest (School Brow), contours 35 and 45, districts id=fairview height_m [18,46] | the crest height is interpolated from the atlas contours at School Brow's own coordinates: at east 320 the 35 m line runs at north 880.6 and the 45 m line at 947.9, and the road is at north 915, which is 40.1 m. South is downhill because the atlas land polygon puts the water at low north. |
| 7 | the grey water of the harbour basin, dock cranes in silhouette, a tall brick works chimney further right | ATLAS+DERIVED | production/art/atlas-01/data/atlas.json, landmarks H2 Old Basin [370,245] and I2 Retort works [125,380] | from School Brow [445,940] the basin is 699 m away and about 40 m below, bearing south and slightly west; the works chimney is 645 m away on a wider southwest bearing, which puts it further right in a view facing south. Bearings and distances computed from those coordinates, printed in the delivery. |
| 8 | dock cranes in silhouette / a tall brick works chimney further right | PROJECT-DOC | game-design/town-plan.md, lines 67 to 71 | the surviving urban observations ask for landmarks for orientation, crane silhouettes over the dock district and a chapel mass. D14 retires that document's visual ceiling, which is why nothing of its stylised target is used here. |
| 9 | from the crest road at 40 m, looking south and downhill | FORM-BIBLE | production/art/atlas-01/TOWN-FORM-BIBLE.md, line 29, morphology rule 7 | rule 7 reserves long views for work and orientation, which is WHY the upper panel is a long view down the hill to the docks rather than a pretty skyline, and why the lower panel is closed in by the terrace instead. |
| 10 | Contour-following terraces / Stone retaining walls and flights of steps between streets | FORM-BIBLE | production/art/atlas-01/TOWN-FORM-BIBLE.md, line 28, morphology rule 6 | rule 6 makes Fairview's hills canon-required fiction expressed by contour-following terraces, retaining walls and stair shortcuts. |
| 11 | grow older as they descend | RESEARCH-DERIVED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 9 to 12 | our own research states the build order as a design tool: byelaw terraces at the bottom near the work, interwar on the middle slopes, council at the top, 1980s infill in what was left, and the higher the camera climbs the later the century. |
| 12 | rendered council cottage pairs in groups of four | RESEARCH-CITED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 62 to 67 | Tudor Walters, October 1918: two-storey cottages in groups of four to six. |
| 13 | bay-fronted semis with hipped roofs and pebbledash upper storeys on the middle slopes | RESEARCH-CITED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 84 to 88 | cited interwar speculative semi: steep hipped roof in plain clay tile, render at first floor, a two-storey bay, pebbledash to the upper storey only. |
| 14 | soot-darkened brick terraces lowest near the work | RESEARCH-ASSUMED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 54 to 58 | the file labels its own 1990 eye for the byelaw layer as ASSUMED, and so is this phrase. |
| 15 | one short cul-de-sac of small thin-brick 1980s houses on the last plot | RESEARCH-CITED+ASSUMED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 128 to 141 | CITED: homes built in England 1981 to 1990 average 83.9 m2 and post-1991 homes are larger, so the newest houses in Meridian in 1990 are the smallest. The file itself labels the cul-de-sac, the thin brick skin and the shallow pitch as ASSUMED. |
| 16 | party-wall chimney stacks with clay pots | PROJECT-DOC | game-design/town-plan.md, lines 54 to 58 | contiguous rows with shared party walls and chimney stacks on the party walls. |
| 17 | a television aerial on every stack | INVENTED | NOTHING | our household research (lines 175 to 179) labels the four-channel line-up itself ASSUMED and HOLE 4, and nothing in our files counts aerials. The aerial on every roof is my inference from a country with four terrestrial channels and no cable. |
| 18 | one round satellite dish on a gable end | RESEARCH-CITED+DERIVED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 174 to 185 | CITED: 750,000 dishes placed by April 1990, a million sold by late 1990, the flat square antenna rare at about 100,000. DERIVED density: roughly one dish per twenty to thirty households, stated in that file as an order of magnitude. One dish in a view of many roofs is that density, and the round dish rather than the square one is the common case. |
| 19 | A slate-roofed chapel and a railed school yard mid-slope | ATLAS | production/art/atlas-01/data/atlas.json and production/art/atlas-01/DISTRICTS.md, landmarks F1 Chapel / school gate [330,835]; DISTRICTS.md line 51 | F1 is Fairview's named landmark and the atlas types it church with venue true; DISTRICTS.md line 51 calls the school chapel and steps the named landmark. The slate roof is my choice and is unsourced. |
| 20 | Chapel Road | ATLAS | production/art/atlas-01/data/atlas.json, routes id=hill, name Chapel Road (proposal) | an atlas-authored route through Fairview. It is marked a proposal in the atlas and is not in canon's minted street list, which names only Quay Street, Weighhouse Lane and Tannery Row. |
| 21 | gradient 1 in 9 | ATLAS+DERIVED | production/art/atlas-01/data/atlas.json, routes id=hill points [[270,700],[320,820]] against contours 10 and 20 | the lower length climbs from about 9.5 m to about 23.9 m over 130.0 m, which is 1 in 9.0. Cross-checked against hillside-housing-dated-series.md lines 197 to 201, whose cited residential range is 8 to 12 percent; 1 in 9 is 11.1 percent, inside it. That citation is American and shape-only, and HOLE 5 of that file says no British gradient limit could be found. |
| 22 | chapel gate 60 m up | ATLAS+DERIVED | production/art/atlas-01/data/atlas.json, landmark F1 [330,835] against a camera at about [300,780] | 62.6 m by Pythagoras, rounded down to 60 m. |
| 23 | ONE ROW UNDER TWO MAINTENANCE REGIMES | RESEARCH-CITED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 148 to 164 | CITED: over 1 million council houses sold under Right to Buy by 1990, 1.5 million quoted in the same source set, the right created by the Housing Act 1980. Our file's own sentence is One row, two maintenance regimes, visible from the street, line 160, and that sentence is what this clause compresses. |
| 24 | a new hardwood door with a sunburst glass panel, a brick porch added to the front, white plastic casement windows, stone cladding across the ground floor and a front garden paved over with a mass-market saloon on it | RESEARCH-ASSUMED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 153 to 164, flagged there as HOLE 4 | THE MECHANISM IS CITED AND THIS ALTERATION LIST IS NOT. Our own file says the specific alterations are ASSUMED period knowledge that no source it could reach confirms, and names it HOLE 4. Carried because it is the most legible way to draw a sold house beside a rented one, and carried with the label visible. |
| 25 | painted timber windows | RESEARCH-CITED+DERIVED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 165 to 173 | CITED: plastic frames were 75 percent of the 12 million windows sold a year by the mid-1980s and double glazing rose from about 16 percent of homes around 1979 to over 60 percent by the end of the 1990s. DERIVED: a 1990 street is MIXED, somewhere between 30 and 45 percent replaced, so one house plastic and the next timber is the sourced reading. |
| 26 | Party walls step up in half-storey jumps as the ground climbs and the end house sits on an underbuild, a cellar at one end and a garage at the other | RESEARCH-DERIVED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 206 to 211 | geometry rather than citation: at 1 in 10 a 6.0 m module drops 600 mm, close to two risers, so a terrace on a hill either steps its party walls or grows an underbuild. Our file derives both and calls both worth a kit piece. |
| 27 | Kerb and pavement run unbroken uphill | PROJECT-DOC | game-design/town-plan.md, lines 59 to 66 | pavements as continuous strips at constant width with kerb lines unbroken through the run. |
| 28 | the pavement stepped with a steel handrail | INVENTED | NOTHING | the steps are sourced (form bible rule 6, stair shortcuts). The handrail and its material are mine; HOLE 5 of the hillside file says it could find no British source on hillside layout, stepped terraces or retaining wall heights. |
| 29 | Galvanised steel dustbins with lids against the wall by a side door | PROJECT-SPEC | production/specs/vignette-scene.json, line 347 | the built street's own spec: the galvanised British dustbin of this period is about 18 in across and 24 in tall, 0.46 by 0.61 m, set back 1.60 m from the kerb against the wall by the side door, because that is where a household bin waits. Our household research line 192 separately forbids a wheeled bin until its adoption can be dated. |
| 30 | a wire crate of glass milk bottles on a doorstep | ATLAS+RESEARCH-CITED | production/art/atlas-01/data/atlas.json and production/art/atlas-02/research/household-contents-and-upstairs.md, districts id=fairview objects includes milk bottle; household lines 50 to 55 | CITED: doorstep milk was 45 percent of the retail market as late as 1995, so in 1990 it is at or above that and is majority behaviour rather than nostalgia. The wire crate is my object choice. |
| 31 | a concrete coal bunker in the side passage / a thread of coal smoke from one chimney | RESEARCH-CITED | production/art/atlas-02/research/hillside-housing-dated-series.md, lines 186 to 193 | CITED: at the 1991 Census 18.5 percent of households had no central heating. Our file turns that into roughly one house in five with a coal or gas fire, chimneys in use and a coal bunker. One smoking chimney in a terrace is that rate drawn. |
| 32 | sheets on a wire washing line in the back yard seen through the passage | ATLAS+FORM-BIBLE | production/art/atlas-01/data/atlas.json and production/art/atlas-01/TOWN-FORM-BIBLE.md, districts id=fairview objects includes wire washing line; form bible line 24, morphology rule 2 | rule 2 separates public frontage from working depth and gives passages named destinations, so the washing is seen THROUGH a passage rather than on the street. DISTRICTS.md line 13 also names a washing court in lower Fairview. |
| 33 | a pressed metal street nameplate on a garden wall reading CHAPEL ROAD in black capitals on white | PROJECT-SPEC+INVENTED | production/specs/vignette-scene.json, line 670 | the bill of materials carries E10_street_name_plate as MANDATORY and BLOCKED ON AN IMAGE THAT DOES NOT EXIST, because no street name plate is in the generated directory or in the prompt library. Putting one legible plate in this sheet answers an open, named, mandatory gap, which is why it earns a third string of lettering. The plate's colours and the pressed metal are mine and unsourced. |
| 34 | a steel lamp column | INVENTED | NOTHING | nothing in our files describes period street lighting. Named as a research gap in the delivery, and the lamp is deliberately described without a lantern type so the sheet does not assert one. |
| 35 | three nonidentifiable people in ordinary British clothes of 1990 | CANON+OURS | canon.md, line 71 | canon forbids real people. The count of three is ours, carried from the Hook sheet this lane drew, and is a composition choice rather than a sourced density. |
| 36 | one in a black donkey jacket with leather shoulder panels walking uphill | RESEARCH-CITED | production/art/atlas-02/research/adult-clothing-by-occupation.md, lines 39 to 49 | CITED: medium-length unlined jacket in black or dark blue thick Melton wool with the shoulders reinforced front and back in leather or PVC, in wide use through the 1980s among dockers, builders, miners and binmen. The same file's HOLE 1 forbids hi-vis on this authority, which is why nobody in this sheet wears any. |
| 37 | EXACTLY THREE PIECES OF LETTERING IN THE WHOLE SHEET / each crisp and correctly spelled, every other surface plain unlettered render, brick, paint and glass | OURS-MEASURED | tools/imagegen/compare-hook-2026-09-09-pass2.json and production/d1-probe/RUN-IMAGEGEN, pass-2 _comment block; the sentinel's run-6 note | this lane's own measurement: of four pass-1 Hook draws the pub fascia was legible on one seed and garbled on three, and every secondary fascia was an illegible smear on all four, so pass 2 named exactly two strings and made the rest plain. Three is one fewer than the four strings the sheet that worked carried. |
| 38 | an upper row of four flat material swatches, light warm grey pebbledash, dull red clay roof tile, dark green privet, grey-brown coursed retaining stone | ATLAS+DERIVED | production/art/atlas-01/data/atlas.json, districts id=fairview materials [[pebbledash,#bcb6a5],[red tile,#89564c],[privet,#50624c],[retaining stone,#88877c]] | the four materials are the atlas's four for this district, in its order. The colour words are my reading of its four hex values: 188,182,165 light warm grey; 137,86,76 dull red; 80,98,76 dark muted green; 136,135,124 warm mid grey. |
| 39 | three objects against the paper border, a wire crate of glass milk bottles, a low timber garden gate, a leather school satchel | ATLAS | production/art/atlas-01/data/atlas.json, districts id=fairview objects [wire washing line, garden gate, milk bottle, school satchel] | three of the atlas's own four characteristic objects for Fairview. The fourth, the wire washing line, is placed in the lower panel instead of the objects row, so all four appear. |
| 40 | Both rows plain and unlabelled | OURS-MEASURED | tools/imagegen/compare-hook-2026-09-09-pass2.json, _comment block | the swatch labels were conceded on the Hook sheet for the measured reason that at 8 steps every extra string degrades the lettering that works. Same concession here, same reason, and it is a judgement Jafar can reverse. |
| 41 | Flat overcast light after rain, wet tarmac, damp render / Slate-grey overcast sky | CANON | canon.md, line 42 | photoreal, wet, overcast, grimy Britain; weather and grime are the strategy. The form bible line 36 offers dry diffuse daylight as a verification condition, and canon outranks it, so this sheet is wet. |
| 42 | soot streaks below the gutters, moss in the kerb joints | FORM-BIBLE | production/art/atlas-01/TOWN-FORM-BIBLE.md, line 36 | grime follows water paths, hands, deliveries and heating, and does not cover every surface equally. Both placements are water paths. |
| 43 | Photoreal throughout, everything period-correct for 1990 | CANON+OURS | canon.md, lines 32 to 36 and 42 | POSITIVE FORMS OF EXCLUSIONS, which is this lane's rule: a diffusion model reads the noun and draws it, so the corresponding nouns sit in the negative field instead. See the translation list. |
| 44 | a mass-market saloon on it | CANON+INVENTED | canon.md, line 71 | canon makes every vehicle fictional, so no model, marque or shape is named. The phrase is mine. |
| 45 | the title FAIRVIEW, the small subtitle CONCEPT PROPOSAL | ATLAS-SHEET-FORMAT+INVENTED | production/art/atlas-01/DISTRICTS.md, line 3 | the atlas states that these sheets are concept proposals and not reference photographs or rendered geometry, so the sheet says so on its face. The two words are mine. |
| 46 | A proposal drawn for review. | INVENTED | NOTHING | my own closing sentence, in place of the outside sheet's This is proposed art, which I deliberately did not reuse. |
| 47 | one printed sheet filling the frame edge to edge, | TOOL-REQUIREMENT | tools/imagegen/prompts.json, line 172 | style.framing_required is copied verbatim from our own prompt library and build_prompt refuses any prompt whose kind prefix lacks it, by id, before the download. The rest of the prefix wording is mine. |
| 48 | invented fictional shop name only, no real company names, no real brand logos, no trade marks, no real person, no recognisable faces, no celebrity likeness | LIBRARY-VERBATIM | tools/imagegen/prompts.json, content_rules.rules_clause | copied byte for byte from our own library, together with all 45 forbidden_tokens, and verified equal by comparison rather than by eye. This is the one exclusion clause allowed in a positive prompt and the renderer appends it to every prompt. |

## 6. What I could not source, stated plainly

These are the eight INVENTED rows and the research holes behind them. An
invented period detail is worse than an admitted gap because nothing
downstream can tell them apart, so each one is named here as well as labelled
in the table.

1. ROW 34, THE STREET LAMP. Nothing in any of our files describes British
   street lighting of 1988 to 1992: not the column, not the lantern, not the
   lamp type. The prompt says "a steel lamp column" and deliberately asserts no
   lantern. NAMED AS A RESEARCH TASK: sodium versus mercury, column height and
   spacing, and what a 1990 residential street actually had.
2. ROW 28, THE HANDRAIL ON THE STEPPED PAVEMENT. The steps are sourced to the
   form bible's rule 6; the handrail is mine. The hillside research's own HOLE
   5 says it could find no British source on street gradient limits, stepped
   terraces, retaining wall heights or hillside plot terracing, and calls that
   the weakest part of the file.
3. ROW 33, THE NAMEPLATE'S APPEARANCE. That a nameplate belongs there is
   sourced hard: `production/specs/vignette-scene.json` line 670 records
   `E10_street_name_plate` as MANDATORY and BLOCKED ON AN IMAGE THAT DOES NOT
   EXIST. Pressed metal, black capitals, white ground is mine.
4. ROW 17, A TELEVISION AERIAL ON EVERY STACK. Our household file labels even
   the four-channel line-up as ASSUMED, its HOLE 4, and nothing counts aerials.
5. ROW 4, THE PAPER BORDER, and ROW 46, THE CLOSING SENTENCE. Mine, with the
   disclosure in section 3.
6. ROW 44, THE MASS-MARKET SALOON. Canon makes every vehicle fictional, so no
   marque, model or silhouette is named. The phrase is mine and is deliberately
   vague.
7. ROW 45, THE SUBTITLE WORDING. That the sheet should say it is a proposal is
   sourced to `DISTRICTS.md` line 3. The two words CONCEPT PROPOSAL are mine.

AND THE TWO ROWS THAT ARE SOURCED TO A HOLE RATHER THAN TO A FACT, which is a
different and more dangerous thing than an invention, because they look
researched:

8. ROW 24, THE ALTERATIONS ON THE BOUGHT HOUSE. The Right to Buy mechanism and
   the numbers are CITED (over 1 million council houses sold by 1990, Housing
   Act 1980). The specific alterations, the sunburst glass door panel, the
   porch, the stone cladding, are our own research's HOLE 4: ASSUMED period
   knowledge that no source it could reach confirms. Carried because it is the
   most legible way to draw a sold house beside a rented one, and carried with
   the label showing.
9. ROW 14, THE SOOT-DARKENED LOWEST TERRACES. The research labels its own 1990
   eye for that housing layer ASSUMED.

A CONFLICT BETWEEN TWO OF OUR OWN DOCUMENTS, resolved in the spec and raised
as a card rather than settled silently. `TOWN-FORM-BIBLE.md` line 36 withdraws
the blanket exclusion of wheeled bins as unsupported. Our household research
line 192 and the hillside file's HOLE 6 say the adoption date could not be
found at all, and that a wheeled bin must not be placed until it can be. This
spec excludes the wheeled bin and uses the galvanised dustbin the built
street's own spec already dimensions at 0.46 by 0.61 m. Undated loses.

## 7. Three things deliberately left out

Each is a judgement, not an oversight, and each is reversible.

1. A TELEPHONE KIOSK. Canon's era line makes the phone box infrastructure at
   its 1992 peak, and a residential hill with a house in five lacking a phone
   wants one. It is out because canon's brands section still records the
   telephone operator's kiosk mark and lettering as OWED, and because a kiosk
   is a fourth string of lettering in an unminted brand.
2. A BUS STOP WITH A TIMETABLE CASE. Named by the atlas's Fairview row. Out
   because a timetable case invites lettering the text budget cannot pay for.
3. A MILK FLOAT. Doorstep milk is cited as majority behaviour in 1990, so the
   bottles carry the fact; the float is a vehicle and canon makes every vehicle
   fictional, so it would be a shape to invent for no gain.

## 8. Text versus objects, which is the trade-off this sheet is built around

THREE STRINGS OF LETTERING, one fewer than the sheet that worked: the title
FAIRVIEW, the subtitle CONCEPT PROPOSAL, and the nameplate CHAPEL ROAD. A
residential district has no shop fascias, which is what buys the room for the
nameplate, and the nameplate is the one piece of lettering this project's bill
of materials records as mandatory and missing. If a string has to go, that is
the one to drop.

THE OBJECTS ARE NOT TEXT AND DO NOT SPEND THE SAME BUDGET. The measured
finding from pass 2 is that a negative only vetoes and cannot summon: the Hook
negative kept every yacht out and the working port never arrived, because the
model filled the water from its own average and the average British waterside
is prettier than a working dock. Fairview's equivalent of the working gear is
the domestic gear, so it is named positively, as objects: galvanised dustbins
with lids by a side door, a wire crate of glass milk bottles on a doorstep, a
concrete coal bunker, sheets on a wire washing line seen through the passage, a
thread of coal smoke from one chimney, a steel handrail on the stepped
pavement, a steel lamp column, chimney stacks with clay pots, one round
satellite dish. Nine objects, zero of them lettering.

EVERY EXCLUSION IS IN THE `negative` FIELD AND NONE IS IN THE POSITIVE HALF.
That is the fault that refused run 6, and the measurement is in section 9: 0
exclusion words of 542 and of 387 words scanned.

## 9. Verification, every number printed by the tool rather than asserted

    validate_spec: 0 problem(s) of 4 item(s) examined
    fairview_sheet           positiveExclusions=0/542wordsScanned negativeExclusions=0/89wordsScanned forbiddenHits=0/45tokensScanned framingClausePresent=True negativeActive=False seed=20260916 688x1024
    fairview_sheet_s2        positiveExclusions=0/542wordsScanned negativeExclusions=0/89wordsScanned forbiddenHits=0/45tokensScanned framingClausePresent=True negativeActive=False seed=20260917 688x1024
    fairview_sheet_short     positiveExclusions=0/387wordsScanned negativeExclusions=0/89wordsScanned forbiddenHits=0/45tokensScanned framingClausePresent=True negativeActive=False seed=20260918 688x1024
    fairview_sheet_short_s2  positiveExclusions=0/387wordsScanned negativeExclusions=0/89wordsScanned forbiddenHits=0/45tokensScanned framingClausePresent=True negativeActive=False seed=20260919 688x1024
    rules_clause carried in 4 of 4 composed prompts
    rules_clause identical to library: True
    forbidden_tokens identical to library: True count 45

THE CONTENT RULES ARE CARRIED, NOT HAND-LISTED, and the two values were
compared rather than eyeballed. Writing a spec from scratch last night dropped
that block, which is the clause forbidding real company names, real brand
logos, trade marks and recognisable faces, and only the tool's own dry run
caught it.

THE CANON GATE IS RED ON THIS FILE AND THAT IS THE KNOWN FALSE-POSITIVE CLASS,
measured against its siblings rather than waved away:

    this spec                                      RED - 50 finding(s), 754 line(s) examined
    tools/imagegen/prompts.json (the library)      RED - 47 finding(s), 891 line(s) examined
    tools/imagegen/compare-hook-2026-09-09-pass2.json (the spec that ran)  RED - 50 finding(s), 280 line(s) examined
    tools/imagegen/compare-hook-2026-09-09.json    RED - 50 finding(s), 374 line(s) examined

Every imagegen spec is red, because a spec must CARRY the 45 banned brand
tokens in order to screen for them, and the gate screens for those tokens. The
half that matters was measured separately, per item:

    POSITIVE prompts: eraTerms 0 of 13 screened, brandTokens 0 of 45 screened, 4 of 4 items
    NEGATIVE prompts: eraTerms 1 of 13 screened ("mobile phone"), brandTokens 0 of 45, 4 of 4 items

The one era term is the phrase "mobile phone" sitting in the list of nouns to
push AWAY, which is canon being obeyed rather than broken, and is the same
position it occupies in the pass-2 spec that ran. Per learning entry L19 the
answer to this class is to reword and never to loosen the gate; here there is
nothing to reword, because the word is the instruction. NO EXEMPTION WAS ADDED
and no gate was touched.

## 10. What the run will cost

From the tool's own estimator, not a typed guess:

    estimate_seconds per image at 688x1024 cfg1.0 = 152.4 s
    4 items = 609.7 s = 10.2 min

And the measured precedent beside it, off the committed manifest of the last
run at this exact size, `production/art/compare/hook-2026-09-09-pass2/manifest.json`:
161.1, 161.0, 160.8 and 160.9 seconds, median 161.0 s, 4 of 4 written, blank 0
of 4 checked. So the measured figure is 644 s, 10.7 min, about 6 percent above
the estimator. `max_minutes: 30` in the sentinel entry is a ceiling with
roughly three times the headroom, unchanged from the last run.

ZERO MONEY. The run is local on Jafar's own PC, the weights are
Z-Image-Turbo Q4_K under Apache-2.0 which is on the licence allowlist, and
nothing is purchased or fetched from a paid account.

## 11. The sentinel entry, and why it is a file and not an append

`SENTINEL-ENTRY.txt` in this directory holds the exact lines. They were proved
to parse by running the tool's own `--batch-settings` over a COPY of the
sentinel with the lines appended, so the real file was never touched:

    batch limit=4 source=sentinel-file/lastOf5
    batch only=fairview_sheet,fairview_sheet_s2,fairview_sheet_short,fairview_sheet_short_s2 source=sentinel-file/lastOf4
    batch max_minutes=30 source=sentinel-file/lastOf5
    batch spec=production/art/concept-fairview-2026-09-10/fairview-sheet-2026-09-10.json source=sentinel-file/lastOf4
    batch out=production/art/concept-fairview-2026-09-10/sheets source=sentinel-file/lastOf4

Both `spec` and `out` are present, which the workflow requires: it REFUSES a
one-off spec named with no out, because `write_attribution` rewrites
ATTRIBUTION.json in the output directory from the run's own manifest.

ONE THING THE RESIDENT HAS TO CHECK BEFORE THE BOARDS CAN BE LINKED.
`tools/gallery.py` line 141 reads
`SOURCES = ("production/d1-probe", "production/frames", "game-design/sim-shots")`,
and this commission's output directory is under none of them. Whatever
surfaced the Hook compare boards, it was not that tuple. One line, measured and
printed, as the 9 September decision already required for the compare
directory.

## 12. A fault in the instrument, found while validating and not fixed here

`tools/imagegen/imagegen.py` line 407, on the CPU path only, prints "CPU mode:
batch CAPPED AT THE FIRST 2 ITEMS at half size ... the remaining 10 are listed
in the manifest as not attempted". The 10 is hardcoded and assumes the
12-item library. Against this 4-item spec the truth is 2, and the dry run on
this machine printed the wrong number: a denominator that is not a statistic of
the loaded spec. It never reaches Jafar's PC, which has a card and takes the
GPU path, so it is a quiet instrument fault rather than a live one. NOT FIXED
HERE: the tool is the material generator and outside what this commission may
write. Handed over as a one-line repair.

## 13. The do-not-touch list, stated so it can be checked in one command

Every file this commission wrote is under
`production/art/concept-fairview-2026-09-10/`. Nothing was written or
read-modified in `production/d1-probe/DISPATCH`,
`production/d1-probe/RUN-IMAGEGEN`, `.github/workflows/`,
`production/next-three.json`, `tools/imagegen/`, `tools/canon-gate.py`,
`tools/gallery.py`, `CLAUDE.md`, `.claude/rules/` or `ledger-v2/studio-v2/`.
Nothing was committed and nothing was pushed. No run was started.

## 14. Candidate cards, for the resident to route. Each has a default so the
work continues.

CARD A. TWO ARMS OR FOUR SEEDS. This run spends two seeds on the authored
prompt at 549 words and two on the same concept cut to 400, because the one
adherence fact the lane has measured is that at 296 words the model dropped
three requested objects on all four pass-1 draws. WHAT THE CUT COSTS, MEASURED
RATHER THAN DESCRIBED: of 33 named elements present in the authored arm, the
trimmed arm keeps 20 and drops 13, and the 13 are the cul-de-sac, the
bay-fronted semis, the groups of four, the underbuild, the works chimney, the
coal bunker, the lamp column, the unbroken kerb, the moss, the damp render, the
hardwood door, the chain-link fence and the chapel gate. All three lettering
strings, all four swatches, all three objects and both cameras are identical. The cost is that the
lettering hedge drops from four seeds to two, and lettering is what failed on
three of four pass-1 draws. DEFAULT, already in the spec: two arms. The
alternative is four seeds of the authored prompt with the length question left
for the Copper Row sheet.

CARD B. THE SWATCH AND OBJECT ROWS STAY UNLABELLED. Same concession the Hook
sheet made, same measured reason: at 8 steps every extra string of lettering
degrades the lettering that works. The outside sheets label their swatches, so
this is a visible difference rather than a hidden one. DEFAULT: unlabelled.

CARD C. THE WHEELED BIN. Two of our own documents disagree, section 6. DEFAULT:
excluded until the adoption date is found, with the dustbin the built street
already dimensions. The research task that settles it is one line of the
hillside file's hole list.

CARD D. WHAT THE NEXT SHEET IS. Five districts remain after this one. The same
rule that chose Fairview would choose COPPER ROW next, because canon's own
district order puts it first among those left and its market quarter is the one
remaining district with a named landmark, a minted street and a graffiti tag
in canon. DEFAULT: Copper Row tomorrow, and the named research gap to fill
first is period market-stall and shopfront trade, which no atlas-02 file
covers.
