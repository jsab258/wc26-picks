# Gap 2: a dated hillside housing series

STATUS: SPEC. Commission `atlas-02`, pinned to
`f3f395c5dda6be684183ef4f02c1d0a533207bbf`. Written 2026-09-08.

WHAT THIS IS. The housing of Fairview, the residential hills, as a DATED
SERIES: what was built when, to what measured standard, and what a 1990 eye
sees when it looks at each layer. A hillside town is read by its dates. The
byelaw terraces are at the bottom near the work, the interwar semis took the
middle slopes when the buses arrived, the council estate took the top where
the land was cheap, and the 1980s infill took whatever was left. That order
is a design tool: the higher the camera climbs, the later the century.

WHAT THIS IS NOT. It is not a layout of Fairview and it does not lay out a
street. D13 governs street layout method and this file does not touch it.

Labels are as defined in `small-pub-plan-measured.md` section 0: CITED,
DERIVED, ASSUMED, HOLE. The same sourcing limit applies: the research hosts
are blocked by the egress proxy, so every external citation is a search-channel
summary of the named page, not a page read in full.

## The series, in build order

### A. Byelaw terrace, 1875 to 1918

- CITED: the Public Health Act 1875 and the byelaws made under it required
  streets at least 36 ft (11 m) wide, 150 sq ft (14 m2) of unbuilt space at
  the rear of each house, a minimum room height of 8 ft (2.44 m), drainage and
  a lavatory, and windows of a set size relative to the room; section 57
  required through houses, which ended the back-to-back. Source: "Byelaw
  terraced house", https://en.wikipedia.org/wiki/Byelaw_terraced_house (search
  summary); "Public Health Act 1875" (search summary).
- CITED: the Building Act 1878 added foundations, damp proof courses, wall
  thicknesses, ceiling heights, spacing between dwellings, under-floor
  ventilation and window sizes. Source: as above.
- CITED (typical rather than regulated): Victorian ceilings commonly around 9
  ft, with a documented mid-Victorian example at 8 ft 10 in downstairs and 8
  ft 7 in upstairs. Source: Period Property UK forum, "Height of Edwardian
  rooms and window heads",
  https://www.periodproperty.co.uk/forum/threads/height-of-edwardian-rooms-and-window-heads.20178/ ,
  and calendar-uk.co.uk summary. Treat as a range, not a standard: 2620 to
  2740 mm ground, 2540 to 2620 mm first.
- DERIVED, and it ties to the project's own file: `vignette-scene.json` sets
  the built street's ground storey at 3.4 m because it is a SHOP ground floor,
  and its first floor at 2.8 m. A purely residential byelaw terrace on the
  hill should NOT reuse 3.4 m; 2.7 m ground and 2.6 m first is the residential
  figure implied by the sources above. Reusing the shop height is the kind of
  quiet error that makes a residential street read as a commercial one.
- HOLE 1: I could not source a typical byelaw terrace FRONTAGE width. The
  street width (36 ft) and the rear yard (150 sq ft) are regulated and cited;
  the house width is not, in anything I could reach. The vignette file's own
  note says a British shop unit is roughly 4.5 to 6 m, which is evidence about
  shops and must not be borrowed for houses without a source.
- ASSUMED 1990 EYE, because no source here gives a proportion and the two
  fractions below are mine: soot-darkened brick or render, sash windows in
  perhaps a third of the houses and uPVC casements in the rest, a satellite
  dish appearing on gable ends from 1989, a mass-market saloon at the kerb, no
  front garden or a 1 m one, wheelie bins NOT yet universal (see HOLE 5).

### B. Council cottage estate, 1919 to 1939

- CITED: the Tudor Walters Report of October 1918 recommended two-storey
  cottages in groups of four to six, at 12 houses per acre in urban areas and
  8 elsewhere; a parlour house of 1,055 sq ft (98.0 m2) and a non-parlour
  house of 855 sq ft (79.4 m2); three rooms on the ground floor (living room,
  parlour, scullery) and three bedrooms above, two of them able to take two
  beds; a larder and a bathroom as essentials. Source: "Tudor Walters Report",
  https://en.wikipedia.org/wiki/Tudor_Walters_Report (search summary);
  Historic England, "The History of Council Housing",
  https://heritagecalling.com/2019/07/29/the-history-of-council-housing/ .
- DERIVED: 12 houses per acre is 4,047 m2 / 12 = 337 m2 of land per house,
  including the road. At a 6.5 m frontage that is a plot 52 m deep, which is
  obviously wrong, so the density figure is carrying the road, the verge and
  the open space as well as the garden. Use 12/acre for a BLOCK, never for a
  plot.
- HOLE 2: the 70 ft separation between facing houses that is often attributed
  to Tudor Walters did not appear in any source I could reach. Do not use it.
- ASSUMED 1990 EYE, the superlative being my judgement and not a sourced
  ranking: this is the Right to Buy layer, and it is the single most dating
  feature of a 1990 British estate. See section C below.

### C. Interwar speculative semi, 1919 to 1939, mostly 1930s

- CITED: steep hipped roof in plain clay tile with overhanging eaves,
  brickwork detail, render at first floor, a two-storey bay with a pitched
  roof over; large bowed bays and mock timber framing in the gable; whole-wall
  render painted to imitate concrete, or pebbledash to the upper storey only;
  suntrap bays with a curved side and horizontal metal glazing bars are a
  1930s option. Source: "Early 20th Century Housing: The Interwar Period",
  https://www.propertyinvestmentsuk.co.uk/early-20th-century-housing/ , and
  the Routledge chapter "Housing between the wars",
  https://s3-eu-west-1.amazonaws.com/s3-euw1-ap-pe-ws4-cws-documents.ri-prod/9780367027582/Part_5_Interwar.pdf .
- CITED, WEAK: a typical 1930s semi is about 8 to 10 m deep and 6 to 7 m wide,
  narrower at the front (one bay window wide) and slightly wider at the rear;
  interwar semis run 85 to 100 m2 of usable floor area. Source:
  mylocallondonbuilder.co.uk and epcguide.co.uk, both modern renovation
  guidance rather than a survey. LABELLED WEAK ON PURPOSE: these are the only
  frontage numbers I could get for any house type in this file, and they come
  from trade blogs. If one dimension in this document is worth verifying
  before a kit is cut, it is this one.
- DERIVED: a 6.5 m half-semi plus a 1.5 m side gap (ASSUMED) gives a 16 m
  module for a pair, which is 2.67 of the street file's 6.0 m bay. The
  hillside kit therefore CANNOT reuse the terrace bay pitch, and that is the
  measured reason for a separate residential kit rather than a preference.

### D. Postwar council, 1945 to 1980

- CITED: the Parker Morris report Homes for Today and Tomorrow (1961) set a
  minimum net floor area of 84.5 m2 for a 5-person two-storey centre-terrace
  house and 93.8 m2 for a 5-person three-storey house; the standards applied
  to New Town housing from 1967 and to all council housing from 1969, and were
  rescinded in 1980. Source: "Parker Morris Committee",
  https://en.wikipedia.org/wiki/Parker_Morris_Committee (search summary);
  Julia Park, "One Hundred Years of Housing Space Standards",
  http://housingspacestandards.co.uk/assets/space-standards_onscreen_print.pdf .
- WHY THE 1980 DATE MATTERS IN THE WINDOW: a Fairview council house built in
  1972 is measurably bigger than a private house built in 1986 two streets
  away. That inversion is true, dated and countable, and it is exactly the
  sort of fact that makes a town read as a real place with a history rather
  than a set.
- HOLE 3: I found nothing usable on system-built or prefabricated council
  housing of the 1950s and 1960s (Airey, Cornish, Wates, no-fines concrete)
  and nothing on the 1980s condition of those types, which is a real
  omission for a hillside estate. Named as a task.

### E. Private estate, 1975 to 1990

- CITED: homes built in England between 1981 and 1990 average 83.9 m2, and the
  frequently quoted 76 m2 "smallest in Europe" figure traces to a 1996 report
  analysing properties built in the 1980s and early 1990s; homes built after
  1991 are larger than those built in the 1980s. Sources: MHCLG, "Floor Space
  in English Homes",
  https://assets.publishing.service.gov.uk/media/5b4750e6e5274a3770774693/Floor_Space_in_English_Homes_main_report.pdf ;
  James Gleeson, "The myth of the shrinking British home",
  https://jamesjgleeson.wordpress.com/2017/02/11/the-myth-of-the-shrinking-british-home/ .
- DERIVED CONSEQUENCE, from the cited floor-space finding that post-1991
  homes are larger than 1980s ones: the newest houses in Meridian in 1990 are
  the SMALLEST houses in Meridian. Small rooms follow from the floor area; the
  rest of this list (shallow pitches, thin brick skins, integral garages,
  cul-de-sacs and turning heads) is ASSUMED period detail that no line above
  sources.

## The 1988 to 1992 overlay: what makes any of these read as 1990

This is the half that stops the series being a history lesson. Every layer
above is wearing the same decade when the player sees it.

- CITED: over 1 million council houses had been sold under Right to Buy by
  1990, with 1.5 million quoted in the same source set; the Housing Act 1980
  created the right. Sources: House of Lords Library, "Right to buy: Past,
  present and future", https://lordslibrary.parliament.uk/right-to-buy-past-present-and-future/ ;
  "Housing Act 1980" (search summary).
- DERIVED WHAT IT LOOKS LIKE, the mixed row following from a part sell-off of
  1.5 million homes into rows that were uniform before it, and this is the
  workhorse of the whole file: a council terrace in 1990 is a CHEQUERBOARD. The bought houses have a new front door,
  often with a bullseye or sunburst glass panel, a porch that no other house
  in the row has, uPVC windows, sometimes stone cladding on the front
  elevation, and a paved-over front garden with a car on it. The unsold houses
  next door still have the council's standard door, the council's window and
  the council's fence. One row, two maintenance regimes, visible from the
  street. LABEL: the mechanism and the numbers are CITED; the specific list of
  alterations (bullseye glass, cladding, porch) is ASSUMED period knowledge
  that no source I could reach confirms, and it is flagged as HOLE 4 rather
  than presented as researched.
- CITED: uPVC accounted for 75 percent of the 12 million windows sold each
  year to British homeowners by the mid-1980s; double glazing rose from about
  16 percent of homes around 1979 to over 60 percent by the end of the 1990s.
  Source: "1980s to Now: the evolution of uPVC windows",
  https://www.windor.co.uk/news/1980s-to-now-the-evolution-of-upvc-windows/ ;
  bluemanorwindows.co.uk history. DERIVED: at 1990 the town is somewhere near
  the middle of that curve, so a street should be MIXED, not uniformly uPVC
  and not uniformly timber. A number between 30 and 45 percent replaced is the
  honest reading of the two endpoints, and it is derived, not measured.
- CITED: Sky had placed 750,000 dishes by April 1990 and had sold a million by
  late 1990; BSB launched 25 March 1990 with the Squarial, a flat square
  antenna 38 cm across, and had sold only about 100,000 dishes by late 1990;
  the two merged in November 1990. Sources: National Science and Media Museum,
  "Sky Wars", https://www.scienceandmediamuseum.org.uk/objects-and-stories/sky-wars-satellite-broadcasting ;
  "Squarial", https://en.wikipedia.org/wiki/Squarial (search summary).
- WHAT TO DO WITH IT: a round dish on a 1990 wall is common and a SQUARIAL is
  rare, and after November 1990 a squarial is a dead object still bolted to
  the wall, which is a free and perfectly dated piece of storytelling. It also
  gives a rough density: roughly one dish per twenty to thirty households in a
  town of average take-up in 1990 (DERIVED from a million dishes against
  about 22 million households, and stated as an order of magnitude only).
- CITED: at the 1991 Census, 18.5 percent of households in England and Wales
  had no central heating and 1.3 percent lacked or shared a bath or inside WC.
  Source: 1991 Census profile for England and Wales,
  https://www.conwy.gov.uk/en/Council/Archived/Statistics-and-research/Census/Census-1991/Assets/documents-Comp-areas/England-Wales-1991-Census-profile.pdf .
- WHAT TO DO WITH IT: roughly one house in five on the hill still has a coal
  or gas fire as its heat, which means chimneys in use, a coal bunker or a
  gas fire in the front room, condensation on the glass and a cold upstairs.
  In a wet overcast port town that is atmosphere with a census behind it.

## The hillside itself

- CITED, but AMERICAN and therefore shape only: local and residential streets
  are commonly held to 8 to 12 percent gradient (1 in 12 to 1 in 8), with 8
  percent the conservative target. Source: AASHTO guidance as summarised at
  quora and mikegravel.org; a US municipal code (Massachusetts) gives 8
  percent on principal streets, 10 percent on minor streets.
- HOLE 5: I could not find a British highway or design-guide gradient limit,
  nor any British source on stepped terraces, retaining wall heights or
  hillside plot terracing. This is the weakest part of this file and the
  hillside is in its title, so it is named plainly rather than covered over.
- WHAT SURVIVES ANYWAY, as geometry rather than as research: at 1 in 10, a
  6.0 m module drops 600 mm, which is close to two risers; so a terrace
  climbing a hill either steps its party walls in half-storey jumps or lets
  the ground floor stay level and grows an underbuild that is a cellar at one
  end and a garage at the other. Both are DERIVED consequences of the
  gradient, and both are worth a kit piece.

## Holes, collected

1. Byelaw terrace frontage width from a real source.
2. The 70 ft facing-house separation, unverified, currently unusable.
3. System-built council housing of the 1950s and 1960s and its 1980s state.
4. The specific visual alterations Right to Buy owners made, from a source
   rather than from memory.
5. British street gradient limits and hillside layout practice.
6. Wheelie bin adoption date in British towns, which decides whether the back
   lane has bins or dustbins, and I could not date it at all.
