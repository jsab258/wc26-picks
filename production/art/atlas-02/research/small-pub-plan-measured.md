# Gap 1: a measured period small-pub plan

STATUS: SPEC. Commission `atlas-02`, pinned to
`f3f395c5dda6be684183ef4f02c1d0a533207bbf`. Written 2026-09-08.

WHAT THIS IS. The measured research a small British port-town pub of 1988 to
1992 is authored FROM: the carcass the built street can carry, the rooms the
period actually had, the components whose dimensions are published, the
arithmetic that turns those into a capacity, and the licensing clock that
makes a pub a place where the hours matter.

WHAT THIS IS NOT. It is not Mickey's. Canon puts Mickey's on Quay Street in
the Hook and the player owns it; laying out Mickey's is a separate piece of
authoring and this file is its input, not its substitute. Nothing here mints a
brand or a name. Every brewery, beer, machine and sign named below is real and
appears ONLY as evidence; the world's equivalents are the brand bible's to
mint.

## 0. How to read this file, and the one limit on its sourcing

Every line carries one of four labels and no line carries none.

- CITED: the claim and its source. Where the source is about a date outside
  1988 to 1992 the label says so, and the claim is then evidence about SHAPE,
  not about the window.
- DERIVED: a number computed here from cited inputs, with the arithmetic
  printed so a later reader can refute it.
- ASSUMED: a choice with no source. A builder may change it freely; nothing
  downstream should treat it as researched.
- HOLE: something looked for and not found, stated so it can be a research
  task rather than a smoothed-over invention.

THE SOURCING LIMIT, stated once and true of all five files. In this checkout
outbound HTTPS to every research host is refused by the organization egress
proxy: `en.wikipedia.org`, `www.legislation.gov.uk`, `api.parliament.uk`,
`pubheritage.camra.org.uk` and `barclayperkins.blogspot.com` were each tried
and each answered 403 to CONNECT, by WebFetch and by curl. WebSearch works.
So every citation below is the search channel's summary of a page, with the
page's title and URL recorded, and NOT a page this session read in full. Two
consequences a reader must hold: a figure could be the summariser's error, and
where a primary table was needed (the ONS RPI beer series, the Gaming Board's
1990 stake limits) the failure to retrieve it is recorded as a HOLE rather
than filled from memory.

## 1. The carcass: what the built street can carry

The street is not a mood, it is a file. `production/specs/vignette-scene.json`
and the 593 pieces generated from it fix the module a pub on Quay Street must
fit, and these are the project's own numbers rather than anybody's research.

- CITED (project file, `vignette-scene.json`): bay width 6.0 m; terrace
  carcass depth 8.0 m; storey heights 3.4 m (ground) then 2.8 m (first);
  footway 2.0 m; kerb 0.125 m; channel 0.255 m; carriageway half width 3.0 m;
  roof pitch 35 degrees; eaves at 6.30 m above the road crown; ground floor
  level +0.100 m.
- CITED (same file): the side door leaf is 1981 x 838 mm, the shop door 2040 x
  900 mm, stallriser 600 mm, transom at 2400 mm, fascia band 2850 to 3400 mm.
- CITED (external, modern): 1981 x 762 mm is the standard internal door in
  England and Wales, 1981 x 838 mm the standard external, and 838 mm is the
  Part M width. Source: "UK standard door sizes and conversion chart", Door
  Superstore, https://www.doorsuperstore.co.uk/help-and-advice/product-guides/internal-doors/uk-door-sizes-and-conversion-chart/
  . The street file and the trade standard agree, which is why the pub's
  doors need no new number.

THE CONSTRAINT THAT FALLS OUT, and it is the most useful thing in this file.
A pub is not a shop unit. One 6.0 m bay by 8.0 m depth is 48 m2 gross, which
after walls, servery, stairs, cellar head and a WC is not a pub, it is a bar
in a corridor.

- DERIVED: two bays gives 12.0 x 8.0 = 96.0 m2 gross ground floor; three bays
  gives 18.0 x 8.0 = 144.0 m2. Taking 8 percent for external and party wall
  thickness at this scale (ASSUMED, 8 percent), net internal is 88.3 m2 and
  132.5 m2 respectively.
- RECOMMENDATION (ASSUMED, and a taste card in the delivery file): a
  two-bay pub, 12.0 m of frontage, is the honest size for a back-lane port
  local. Three bays reads as a corner house or a former coaching inn and
  changes the social class of the room.

## 2. The room set the period actually had

A British pub of this vintage is a set of ROOMS, not a space. That is the
single most-often-lost period fact, and it is what makes an interior read as
1990 rather than 2015.

- CITED: CAMRA's National Inventory of Historic Pub Interiors records pubs
  whose interiors survived largely unchanged, and the recurring room set in
  its descriptions is public bar, smoke room, snug, lounge, off-sales, plus a
  drinking lobby. Source: "National Inventory of Historic Pub Interiors",
  and CAMRA Pub Heritage, https://pubheritage.camra.org.uk/ .
- CITED: an off-sales department entered from the street and labelled BOTTLE
  AND JUG, with partitions dividing public bar, off-sales, another bar and a
  dining room, is documented on a National Inventory entry. Source: London
  Pubs Group, CAMRA, https://londonpubsgroup.camra.org.uk/viewnode.php?id=57716 .
- CITED: the SIDE-CORRIDOR PLAN is a named northern urban type: a corridor
  from the entrance widens in the middle to form a drinking lobby in front of
  the servery, with rooms off it. In the North West a public bar sits on the
  street corner inside an L-shaped corridor. Source: "Variations on a Theme:
  Regional Differences in Pubs", SAHGB,
  https://www.sahgb.org.uk/features/variations-on-a-theme-regional-differences-in-our-pubs .
- CITED: rear rooms were served through a SERVING HATCH from the front bar,
  with BELL PUSHES in the panelling for service. Source: CAMRA Pub Heritage,
  Britons Protection, Manchester, https://pubheritage.camra.org.uk/pubs/80 .
- CITED (about the interwar period, so shape not window): the "improved"
  pub's rooms were refreshment room, smoke room, drinking lobby, public bar
  and out-sales, all arranged along one elongated rear servery; panelling in
  wood, cork, lino rubber or vitrolite. Source: "The Improved Public House",
  Designing Buildings,
  https://www.designingbuildings.co.uk/wiki/The%20Improved%20Public%20House ;
  "Celebrating the 20th-Century Public House", SAHGB.
- CITED: the public bar was CHEAPER than the lounge or saloon, and through the
  1970s and 1980s brewers steadily knocked pubs through into one room.
  Reported differentials range from a penny or two historically to 5p and even
  20p a pint. Source: The Pub Curmudgeon, "A pub of two sides",
  https://pubcurmudgeon.blogspot.com/2012/10/a-pub-of-two-sides.html . The
  20p figure is one anecdote in one comment thread and must not be used as
  the number.

DERIVED WHAT THIS MEANS FOR 1988 TO 1992, from the cited line that brewers
knocked pubs through steadily across the 1970s and 1980s. A pub with its rooms
intact in 1990 is either poor, stubborn, or both, and that is a
characterisation fact, not a decorating one. A knocked-through single bar with
a fruit machine where the snug partition used to be is the MAJORITY case, a
direction the source supports and not a measured share, and a surviving two-room plan
says the licensee never had the money or never wanted it.

## 3. Measured components, and where each number comes from

Anything below stated in mm can be placed at the street's own resolution.

Servery and counter
- CITED (modern UK spec, shape): bar servery counter finished height minimum
  1100 mm above finished floor level; under-bar working top 850 to 875 mm.
  Source: UK government catering specification "Bar servery counter",
  https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/33558/2011051551_Bar_servery_counter_v1_0U.pdf .
- CITED (modern trade data, shape): public-facing bar tops 508 to 610 mm
  deep; back bar 610 to 760 mm deep and 910 to 1140 mm high. Source:
  Dimensions.com, "Bar Details", https://www.dimensions.com/element/bar-details .
- ASSUMED for the period: counter top at 1050 mm rather than 1100 mm, which
  is the older British figure in common trade use; flagged because I could not
  source a period counter height. See HOLE 3.
- DERIVED, staff zone: with a 550 mm counter top and a 600 mm back bar, a
  servery needs 550 + 900 (working gangway, ASSUMED) + 600 = 2050 mm of depth
  minimum, and that is one server passing another sideways, not comfortably.

Capacity
- CITED: floor space factors, Approved Document B and fire-authority guidance:
  0.3 m2 per person for standing areas within 2 m of the serving point, 0.5 m2
  per person for general drinking areas, 1.0 m2 per person for dining;
  stairs, corridors, toilets and plant are excluded from the calculation.
  Source: Leicestershire Fire and Rescue, "Calculating Occupancy for Licensed
  Premises and Other Places of Assembly",
  https://leics-fire.gov.uk/uploads/calculating-occupancy-figures-for-licensed-premises-(2).pdf ;
  Northamptonshire Fire, "floor space factors",
  https://www.northantsfire.gov.uk/floor-space-factors/ .
- DERIVED, the two-bay pub: net internal 88.3 m2, less servery 12.0 m2, less
  stairs and cellar head 6.0 m2, less two WCs 8.0 m2, less back corridor and
  store 6.0 m2 (all four ASSUMED allowances) leaves 56.3 m2 of trading area.
  Split 15 m2 within 2 m of the counter and 41.3 m2 general: 15/0.3 = 50
  people, 41.3/0.5 = 82 people, total 132. That is the FIRE CAPACITY, an upper
  bound, and it is not a design target: a pub at its calculated capacity is a
  bad night, not a Tuesday.
- DERIVED, the busy-Friday number a scene should stage: at one third of
  capacity, 44 adults. ASSUMED fraction, and named so nobody treats 44 as
  measured.

The games, which are furniture with rules
- CITED: dartboard centre 1730 mm (5 ft 8 in) above the floor; oche 2370 mm
  (7 ft 9.25 in) horizontally from the board face; the check diagonal from
  bull to the front of the oche is 2930 mm (9 ft 7.5 in). Source: Target
  Darts, https://www.target-darts.co.uk/dartboard-setup ; "Oche",
  Wikipedia (accessed via search summary only).
- DERIVED: a darts area therefore needs 2370 mm of throw plus a body behind
  the oche (900 mm, ASSUMED) plus clearance in front of the board, so about
  3.5 m of clear length and 1.5 m of width against a wall, and no door and no
  through route inside it.
- HOLE: I could not source the standard British pub pool table size (the
  7 ft coin-operated table) or the 1990 price of a game. Named as HOLE 1.

## 4. The cellar, and what it does

The cellar is not storage. It is a temperature-controlled room with a daily
routine, a delivery event that comes through the pavement, and a three-day
clock on every cask. That routine is gameplay before it is set dressing.

- CITED: cellar temperature 11 to 13 degrees C, and a delivered cask must
  rest on the stillage at least 24 hours before tapping so the sediment
  settles below the tap. Source: Cask Marque cellar card,
  https://cask-marque.co.uk/wp-content/uploads/2017/10/a4-cask-cellar-card.pdf ;
  Beer Genius refrigeration policy sheet,
  https://www.beer-genius.co.uk/bestpractice/3.refrigeration.pdf ; Joseph Holt
  cask guide, https://www.joseph-holt.com/cask-ale-guide .
- CITED: venting uses a soft porous peg in the shive for roughly 48 to 72
  hours, then a hard peg; once tapped, a cask should be sold within three
  days. Source: Joseph Holt cask guide, as above.
- CITED: a beer firkin is 9 imperial gallons, 40.91481 litres. Source:
  "English brewery cask units" and "Firkin (unit)" (search summaries).
- CITED, and CONTRADICTORY, which is the point: one supplier lists a 9 gallon
  stainless firkin as 16 in diameter by 19 in high (406 x 483 mm), 22 lb
  empty, 75 lb full (F.H. Steinbart,
  https://fhsteinbart.com/product/firkinkeg108gallon/ ), while a brewery guide
  says a full firkin weighs roughly 72 kg (Joseph Holt, as above).
- DERIVED, and this is the number to use: 40.91 litres of beer at about
  1.01 kg/litre is 41.3 kg, so a cask that weighed 75 lb (34.0 kg) full would
  weigh less than the beer inside it, and 72 kg would mean a 31 kg empty cask.
  Both published figures fail the check. Empty steel firkin 10 kg (the 22 lb
  figure, which is plausible) plus 41.3 kg of beer gives 51 kg FULL. Use 51
  kg for handling, animation weight and whether one man can lift it: he
  cannot lift it comfortably, he rolls it, and that is why the trade uses
  skids and drop pads.
- CITED: deliveries go down through a pavement hatch onto a cellar drop pad,
  lowered on hook and rope, or run down barrel skids; catch pads are commonly
  600 x 600 mm, 900 x 900 x 300 mm or 1000 x 1000 x 300 mm; external beer
  drop doors are galvanised steel replacements for the traditional timber
  trap. Source: SHS Handling Solutions, https://www.shshandlingsolutions.com/dray-brewery-products ;
  Handle-It drop pads, https://handle-it.com/industry-solutions/brewery-and-dray-handling-equipment/drop-pads/ ;
  Cellar Access external beer drop, https://www.cellaraccess.co.uk/External%20Beer%20Drop.html .
- DERIVED, and it lands on the street file: the drop must sit in the 2.0 m
  footway, in front of the pub, clear of the 0.125 m kerb and the 0.255 m
  channel. A 1000 x 1000 mm pad implies a hatch opening of about 1100 x 1100
  mm, which fits the footway with 450 mm each side. That is a piece the
  street's bill of materials does not currently have, and the delivery file
  names it.
- DERIVED, cellar depth: ground floor is at +0.100 m. A cellar with 2.2 m
  clear headroom (ASSUMED, see HOLE 2) and a 0.3 m floor structure puts the
  cellar floor at about -2.4 m relative to the road crown, and the cellar
  ceiling just under the bar floor. A cask on a stillage at 450 mm (ASSUMED)
  with a 483 mm cask on it needs under a metre, so headroom is set by the
  cellarman, not the stock.
- HOLE 2: I could not find a British figure for minimum pub cellar headroom
  or an area-per-barrel planning rule. The search returned American craft
  brewery guidance (12 to 15 ft brewhouse ceilings, square feet per barrel of
  ANNUAL capacity), which is a different building type answering a different
  question and is not used here.
- HOLE 4: beer line runs. I could establish that 3/16 in bore line and
  insulated pythons are the trade norm and that swan neck taps clamp to beer
  engines (a1barstuff, Harry Masons, Kegworks), but not the period maximum
  cellar-to-bar run, nor whether a 1990 back-street pub had cooled lines at
  all. A builder should not state a distance.

## 5. The licensing clock, which is the pub's schedule

This is the half of the research the simulation actually consumes: when the
doors open, when the bell goes, who may be inside.

- CITED: the Licensing Act 1988 extended permitted hours in England and Wales
  to 11:00 to 23:00, removing the compulsory afternoon closure that had run
  from 15:00 to 17:30; pubs began opening all day on 22 August 1988 (one
  source in the same set says 21 August; see the note below). Sources:
  "Licensing Act 1988" (search summary of the Wikipedia article and of
  legislation.gov.uk/ukpga/1988/17/enacted); "When did pubs in England start
  opening all day?", https://eboots.co.uk/wiki/when-did-pubs-in-england-start-opening-all-day .
- CITED: the same Act substituted twenty minutes for ten minutes as
  DRINKING-UP TIME in section 63(1) of the Licensing Act 1964. Source: search
  summary of legislation.gov.uk for the 1988 Act.
- CITED: under the Licensing Act 1964 Sunday, Christmas Day and Good Friday
  permitted hours ran from noon to 22:30 with a five-hour break beginning at
  14:00. Source: search summary of legislation.gov.uk/ukpga/1964/26/part/III.
  The commonly quoted "12 to 3 and 7 to 10:30" is the same shape with the
  break placed differently, and the difference matters if a scene turns on
  the exact minute. FLAGGED: do not hard-code Sunday minutes from this file
  without a primary read. See HOLE 5.
- CITED: children under 14 were not permitted in the bar; children's
  certificates, which let an under-14 take a meal in a bar until 20:00,
  became available only from 3 January 1995. Source: House of Commons Library
  briefing "Children in pubs",
  https://researchbriefings.files.parliament.uk/documents/SN04908/SN04908.pdf ;
  Morning Advertiser, "Children in pubs: Licensing law".
  DERIVED CONSEQUENCE FOR THE WINDOW, from the certificate scheme starting in
  1995 and the window ending in 1992: in 1988 to 1992 a child in Mickey's bar
  is a breach, and a child in the corridor, the yard or the licensee's own rooms
  is not. That is a usable social rule with a date on it.
- CITED: spirits in England and Wales were sold in one sixth of a gill
  (23.7 ml) or other gill fractions; imperial spirit measures ceased to be
  permissible after 31 December 1994, when 25 ml and 35 ml took over. Source:
  Scotch Whisky Association Q&A, https://www.dcs.ed.ac.uk/home/jhb/whisky/swa/56.html ;
  Morning Advertiser, "Know your measures".
  HOLE 9: whether 25 ml was already a lawful measure in 1990 needs SI 1988/2039
  read as made; the 1994 amendment's wording suggests it was.
- CITED: the Capacity Measures (Intoxicating Liquor) Regulations 1988
  allowed a brim pint measure to be crown stamped at anything between 568.3
  ml and 602.3 ml, an excess allowance of 34 ml. Source: Metric Views,
  https://metricviews.uk/2007/11/11/would-lined-beer-glasses-solve-the-pint-problem/ .
  DERIVED CONSEQUENCE, from the 1988 regulations above: the 1990 glass is a
  CROWN-STAMPED BRIM measure, and NOT a CE-marked lined glass. That it is most
  often the nonic, with its bulge below the rim, is ASSUMED. A
  lined glass in shot is a 2007-and-later object.
- HOLE 6: gaming machines. The Gaming Act 1968 governs amusement-with-prizes
  machines in pubs and caps stake and prize, but I could not retrieve the
  values in force in 1990. Do not put a number on the fruit machine's payout.

## 6. The commercial weather, 1989 to 1992

- CITED: the Supply of Beer (Tied Estate) Order 1989 required brewers owning
  more than 2,000 licensed premises to dispose of, or release from tie, half
  the excess over 2,000 by 31 October 1992, creating roughly 11,000 more free
  houses, and required national brewers to let their publicans buy wines,
  spirits and soft drinks anywhere and to sell at least one draught
  cask-conditioned GUEST BEER. Sources: legislation.gov.uk/uksi/1989/2390 and
  Hansard, "Supply of Beer (Tied Estates)", 14 December 1989 (search
  summaries); "Beer Orders" (search summary).
- CITED: at the end of the 1980s six national brewers accounted for about 75
  percent of UK beer production and controlled just over half of all pubs,
  split between managed houses and tenancies. Source: House of Commons Trade
  and Industry Committee report,
  https://publications.parliament.uk/pa/cm200405/cmselect/cmtrdind/128/12805.htm .
- WHY THIS IS WORTH HAVING, and it is a story fact rather than a decorating
  one: a tenant of a big brewery in 1990 is living through the loosening of
  the tie, with a legal right to one guest cask beer and a landlord under a
  1992 deadline. A free house is a different economic animal. The delivery
  file carries this as a taste card, because which one Mickey's is changes
  who visits it, who leans on it, and what a rival can threaten.
- HOLE 7, prices. I could not retrieve the ONS RPI average-price series for
  draught bitter (series CZMT) or the Brewers Society handbook. What I can
  state: Hansard of 29 April 1993 gives March 1993 draught bitter at 132p and
  draught lager at 149p a pint (api.parliament.uk, search summary), and
  secondary sources give 1988 examples of 112p in Soho and 83p in Bradford
  (retrowow.co.uk) and "about 1.10" for 1990. So the 1988 to 1992 window sits
  in a band of roughly 85p to 125p for bitter with a strong regional spread,
  and a port-town back-street public bar belongs at the LOW end of it. Use
  the band, name it as a band, and do not print a false precision.

## 7. Holes, collected, so they can become tasks

1. British pub pool table dimensions and 1990 coin price.
2. Minimum cellar headroom and any British area-per-cask planning figure.
3. Period bar counter height, as against the modern 1100 mm minimum.
4. Maximum period beer line run, and whether cooled lines were normal in a
   small 1990 pub.
5. The exact Sunday permitted hours in force in the window, from primary text.
6. Gaming Act stake and prize limits in force in 1990.
7. The ONS or Brewers Society beer price series for 1988 to 1992.
8. Whether 25 ml was a lawful spirit measure before 1995, from SI 1988/2039
   as made. HOLE 9 in section 3.
9. A REAL MEASURED PLAN. I could not obtain a dimensioned survey of any
   specific small pub: CAMRA's inventory descriptions are qualitative, the
   Historic England listing guides are typological, and the two PDF guides
   that would carry room-by-room detail (Sheffield's Real Heritage Pubs, the
   national Real Heritage Pubs guide) are on hosts this session cannot fetch.
   Everything dimensional above is therefore either the project's own street
   file, a published component standard, or DERIVED arithmetic, and no room
   size in this file is claimed as measured from a real pub.
