# The minicab trade, 1988 to 1992

STATUS: SPEC. Station 1 of the `mickeys-cars` commission, written 2026-09-10.
Governed by `canon.md`, which outranks this file, by D17, and by
`ledger-v2/research/license-allowlist.md`, which is law. Meridian is a
FICTIONAL BRITISH PORT TOWN and is therefore OUTSIDE LONDON, which turns out
to be the single most consequential fact in this file.

## 0. How to read a row, because the labels are the whole value

| label | means |
|---|---|
| CITED | a dated source this session read in full |
| CITED-VIA-SEARCH | the search channel's summary of a NAMED page, not the page itself |
| CITED-VIA-SEARCH-MODERN | a present-day industry source describing a practice I could NOT date to the window |
| DERIVED | arithmetic or logic from a stated fact, with the step shown |
| AUTHORED | this project's invention, owned as such |
| UNSOURCED | a thing a builder needs and I could not find. NOT a fact. |

THE CHANNEL, MEASURED TODAY AND NOT RECALLED. `WebFetch` was tried against
`www.legislation.gov.uk`, `api.parliament.uk`, `en.wikipedia.org` and
`newforest.gov.uk` on 2026-09-10 and all four answered EGRESS_BLOCKED from the
organisation proxy. `curl "$HTTPS_PROXY/__agentproxy/status"` reports the proxy
enabled with `recentRelayFailures: []`, so this is a policy denial and not a
fault, and per `/root/.ccr/README.md` it is reported rather than routed around.
WebSearch works. SO THERE IS NOT ONE ROW IN THIS FILE THAT READ A PAGE IN
FULL, and the label table above is what says so rather than a disclaimer at the
bottom. Counted over the 43 numbered rows, not estimated:

    hostsTried=4 hostsReachable=0/4 searchQueriesRun=11
    rowsTotal=43 cited=0/43 citedViaSearch=19/43 citedViaSearchModern=3/43
    derived=4/43 authored=8/43 assumed=1/43 unsourced=7/43

Re-count it in one command rather than trusting the line:

    grep -cE '^\| (L|R|O|D|M)[0-9]+ \|' production/art/mickeys-cars/01-RESEARCH-minicab-trade-1988-1992.md
    grep -coE 'UNSOURCED' production/art/mickeys-cars/01-RESEARCH-minicab-trade-1988-1992.md

That is the same limit `production/art/atlas-02/DELIVERY.md` recorded on
2026-09-08 and it has not moved. Queue item 156 is the fix and it is still the
fix.

## 1. The licensing, and why outside London is the interesting part

THE HEADLINE, and it is the reason a cab office is a good room for this game.
In 1990 a private hire firm in a provincial English district was licensed
THREE TIMES OVER, by name, with a legal duty to write down every journey. In
London it was not licensed at all. Meridian is provincial, so Mickey's Cars
lives under the heavier regime, and that regime is what furnishes the room.

| id | claim | label | source |
|---|---|---|---|
| L1 | Part II of the Local Government (Miscellaneous Provisions) Act 1976 is ADOPTIVE: section 45 provides that a district council may resolve that Part II is to apply in its area. Different regimes therefore coexisted in adjacent districts. | CITED-VIA-SEARCH | legislation.gov.uk `ukpga/1976/57/part/II`; localgovernmentlawyer.co.uk "Private hire vehicles and contracting"; read 2026-09-10 |
| L2 | A district that has adopted is a CONTROLLED DISTRICT, and the Part II offences are drafted "in a controlled district". | CITED-VIA-SEARCH | same |
| L3 | THREE separate licences: the vehicle under section 48, the driver under section 51, the operator under section 55. Each is an offence to be without. | CITED-VIA-SEARCH | legislation.gov.uk `ukpga/1976/57/part/II`; burnley.gov.uk "Private Hire Law LGMPA 1976 Part 2"; read 2026-09-10 |
| L4 | Section 54: on granting a driver's licence the council issues a DRIVER'S BADGE in a form it prescribes, and the driver must wear it "in such position and manner as to be plainly and distinctly visible". | CITED-VIA-SEARCH | same |
| L5 | To OPERATE, outside London, means "in the course of business to make provision for the invitation or acceptance of bookings for a private hire vehicle". The office is the licensable thing, not just the car. | CITED-VIA-SEARCH | localgovernmentlawyer.co.uk, read 2026-09-10 |
| L6 | Section 56(1): every contract for the hire of a private hire vehicle is DEEMED TO BE MADE WITH THE OPERATOR WHO ACCEPTS THE BOOKING. Section 56 record-keeping covers the time and date of the booking, the name of the hirer, the time of pick-up, the point of pick-up, the destination, and the licence number of the vehicle allocated. | CITED-VIA-SEARCH | legislation.gov.uk `ukpga/1976/57/part/II`; sunderland.gov.uk operator conditions; read 2026-09-10 |
| L7 | A private hire vehicle may not display any sign consisting of or including the word "taxi" or "cab", singular or plural, or "hire", or any word of similar meaning or appearance, or any feature suggesting it is a taxi. Penalty on summary conviction: a fine not exceeding 200 pounds. | CITED-VIA-SEARCH | leeds.gov.uk private hire vehicle conditions; scambs.moderngov.co.uk proposed vehicle licence conditions; read 2026-09-10 |
| L8 | Section 71: there is NO REQUIREMENT to fit a taximeter to a private hire vehicle, and if one is fitted it must be tested and approved by the council. A private hire driver may not charge more than the fare agreed with the operator. | CITED-VIA-SEARCH | sefton "Taximeters" committee paper; burnley.gov.uk; read 2026-09-10 |
| L9 | The two licensed types: hackney carriages may be hailed in the street or wait on a rank, carry a roof light and a meter, and charge the council's set fare; private hire vehicles must be PRE-BOOKED through a licensed operator and are not fare-regulated. | CITED-VIA-SEARCH | Hart District Council licensing pages; Buckinghamshire Council taxi guidance; carried from `production/art/atlas-02/research/transport-timetables.md` section 5, which sourced it on 2026-09-08 |
| L10 | LONDON WAS THE OPPOSITE. Through the whole working window London minicabs were UNLICENSED: no licensing of operators, drivers or vehicles, and no checks on medical, driving or criminal records. Licensing arrived only with the Private Hire Vehicles (London) Act 1998, which gave the job to the body that already licensed London's taxis. | CITED-VIA-SEARCH | Hansard, Private Hire Vehicles (London) Bill, 23 January 1998; h2g2 A721144; read 2026-09-10 |
| L11 | Scale, as stated during the 1998 Bill: on the order of 80,000 London minicabs against 19,000 taxis. That is a 1998 figure quoted for London and it is NOT a 1990 figure and NOT a provincial one. | CITED-VIA-SEARCH, AND DELIBERATELY NOT SCALED | same |
| L12 | The safety campaign that produced the 1998 Act began after a widely reported London disappearance in 1986 that press coverage linked to an unlicensed minicab. THE PERSON IS NOT NAMED IN THIS FILE and must never be named in the game: canon forbids real people, and a real victim is the last place to make an exception. | CITED-VIA-SEARCH, NAME WITHHELD ON PURPOSE | charitytoday.co.uk; suzylamplugh.org campaign history; read 2026-09-10 |
| L13 | ORIGIN, for the history the building carries. The minicab began on 6 March 1961 when a London firm exploited a loophole in the Carriage Act 1869: the Act covered cabs PLYING FOR HIRE in the street and not cars answering calls made to a central office and relayed to the driver. On 19 June 1961 a second London firm put 200 small French saloons on the road at one shilling a mile, fitted with two-way radios and a meter, and the "minicab wars" followed. | CITED-VIA-SEARCH | lancasterinsurance.co.uk "Do You Remember The Renault Dauphine Minicabs"; hagerty.co.uk "Top Ten Minicabs"; read 2026-09-10. Firm and proprietor names are omitted here: they are real and the game may not carry them. |
| L14 | The distinction the whole trade turns on, restated by ministers in 1998 and unchanged through the window: only taxis may ply for hire; private hire vehicles must be pre-booked. | CITED-VIA-SEARCH | Hansard as above |

### What L1 to L14 build, before a single thing is invented

FIVE FEATURES OF THE ROOM ARE DERIVED FROM STATUTE AND ARE NOT DESIGN CHOICES.
This is the paragraph that makes the cab office cheap to author and hard to get
wrong.

1. THERE IS A BOOK, and its columns are section 56's list. DERIVED from L6.
2. THERE IS A TELEPHONE AND A WAITING ROOM, because a private hire vehicle
   cannot be hailed: the customer must ring the office or come to its counter.
   DERIVED from L9 and L14.
3. THERE IS A PRICE LIST ON THE WALL AND NO METER, because the fare is what the
   operator agrees and a meter is optional and rarely fitted. DERIVED from L8.
4. THE SIGN SAYS CARS AND NOT TAXI, and the vehicles carry no roof light,
   because the word is unlawful on the vehicle. DERIVED from L7.
5. THE OPERATOR IS THE CONTRACTING PARTY, so the man at the counter is legally
   on the hook for every journey and has a reason to care who is in the car.
   DERIVED from L6.

## 2. Radio cabs, and how despatch actually worked

THE SHAPE IS SOURCED AND THE HARDWARE IS NOT. Say so before the table.

| id | claim | label | source |
|---|---|---|---|
| R1 | The booking arrives by LANDLINE and is despatched by RADIO. The office is a base station, the cars are mobiles, and the controller calls car numbers. No app, no card machine, no satellite navigation. | CITED-VIA-SEARCH for the two-radio structure at L13's origin; otherwise carried from `atlas-02/research/transport-timetables.md` section 5, written 2026-09-08 | as above |
| R2 | Trunked "Band Three" public-access radio networks launched in the United Kingdom during the 1980s in the 175 to 225 MHz range, named after the old Band III television service, and taxi fleets were among their users. The networks closed around 2003. | CITED-VIA-SEARCH | radioswap.co.uk product listing for a Band 3 175-225 MHz trunked mobile taxi radio; superiorsignals.co.uk trunking page; read 2026-09-10 |
| R3 | A nine-car firm has no reason to buy trunked airtime. The cheap answer is one channel, one base set with a desk microphone, and a whip aerial on a mast. | DERIVED from R2 plus the firm's size at section 5 | shown, not cited |
| R4 | THE PROCEDURE, and it is the room's whole information design: the controller calls a number and waits; the driver answers with his number; the controller reads out the pick-up and the destination; the driver READS IT BACK. Everything that matters is said aloud twice. | AUTHORED, from R1's structure | see the gameplay sheet |
| R5 | Whether a provincial firm in 1990 used procedure words, numbered or lettered its cars, or had selective calling that opens one car's speaker. | UNSOURCED | nothing found |
| R6 | Which body licensed a private mobile radio base station in Britain in 1990, under which Act, in which band, at what channel spacing, and what it cost. | UNSOURCED | eleven searches returned United States regulations, present-day equipment and general descriptions. NOT ANSWERED. |
| R7 | Printed telephone numbers in the window carry NO extra 1 in the area code, because the renumbering that inserted it was 1995. | ASSUMED, HIGH CONFIDENCE, carried at the same label from `atlas-02/research/transport-timetables.md`, which also could not source it | not upgraded, because I did not source it either |

R6 IS THE BIGGEST SINGLE HOLE IN THIS FILE and it matters to exactly one prop:
the faceplate of the base set and whatever licence paper hangs beside it. The
design's answer is to leave the maker's plate BLANK and the licence paper
illegible, which is honest, rather than to invent a regulator.

## 3. The office itself

THE HOLE FIRST, at the top of the section where it belongs. I could not find a
single dated photograph, plan, floor area or written description of the
interior of a British minicab office between 1988 and 1992. Not one. Every
search returned present-day operators, present-day job adverts and present-day
despatch software.

So the layout in `data/cab-office.json` is AUTHORED, and it is authored from
two things that are not guesses:

- THE FIVE STATUTORY FEATURES at the end of section 1, which fix the book, the
  telephone, the waiting room, the price list and the absence of a meter;
- THE BUILDING, which is not invented at all. Every wall, every opening and
  every level comes from `production/specs/vignette-pieces.json`, the street
  that already exists and has been rendered.

| id | claim | label |
|---|---|---|
| O1 | A counter with a glazed screen and a speaking gap, because a cash office open at two in the morning protects its cash. | AUTHORED. UNSOURCED whether provincial offices were screened in 1990; screens are ordinary now and I could not date them. |
| O2 | A waiting bench, because customers must come to the office or ring it and then wait somewhere. | DERIVED from L9 and L14 |
| O3 | A public coin box on the wall, so a customer can ring home. | AUTHORED, and supported by a dated fact this project already holds: 92,000 telephone boxes at their 1992 peak, `atlas-02/research/household-contents-and-upstairs.md`. A town where the box on the corner is the normal instrument puts one indoors as well. |
| O4 | A card index of account customers and a spike of dockets. | AUTHORED from M2 |
| O5 | A wall map of the town, annotated. | AUTHORED. A room whose job is turning an address into a car needs one, and there is nothing else in a 1990 office that could do the job. |
| O6 | A drivers' room separate from the public room, entered by its own door. | AUTHORED. It is the design's central choice and section 6 argues it. |
| O7 | Room sizes, ceiling height, counter height, screen height, the position of every object. | AUTHORED and MEASURED against the street: see `02-SPEC-plans-and-elevations.md`. |
| O8 | The paperwork on the wall: a licensing notice, an insurance reminder, a rota, a settle list. | AUTHORED from L3, L4 and D1 |

## 4. The drivers

| id | claim | label | source |
|---|---|---|---|
| D1 | Nearly all private hire drivers are SELF-EMPLOYED. Some rent the vehicle and the radio from the firm for a weekly rate; the driver keeps the fares and pays for fuel. The weekly settle has a name in the trade: "weigh-in day". | CITED-VIA-SEARCH-MODERN, AND THAT LABEL IS THE POINT | cabdirect.com "Employment Options for Taxi Drivers"; beelineradiocars.co.uk; read 2026-09-10. Every source is present-day. I could NOT date this arrangement to 1990, and it is used because it is the only description found, not because it is proven period. |
| D2 | A driver must hold a section 51 licence and wear the section 54 badge visibly. | CITED-VIA-SEARCH | as L3, L4 |
| D3 | The council must be satisfied the applicant is a fit and proper person to hold a driver's licence. | CITED-VIA-SEARCH | burnley.gov.uk; leeds.gov.uk; read 2026-09-10 |
| D4 | The car carries a council plate and no roof light, and its insurance must cover hire and reward. | CITED-VIA-SEARCH for the plate and the sign prohibition, per L7; hire and reward is general road traffic law and is carried UNSOURCED here | |
| D5 | What the plate looked like in a provincial district in 1990, whether a rear plate and a windscreen disc were both required, and what colour anything was. | UNSOURCED, and it VARIES BY DISTRICT, which is itself the point of L1 | |
| D6 | What a driver earned in a week in 1990. | UNSOURCED | |
| D7 | Nine cars, nine drivers, a night man and a woman on the day shift who has been there longer than any of them. | AUTHORED | see `data/cab-operations.json` |

WHAT D1 TO D7 GIVE THE GAME, and it is more than clothing: the drivers are not
employees. They are nine self-employed men and women who owe the office money
every week, who keep their own takings, who are licensed by name and photograph
by a council that can take the licence away, and who are in and out of one room
all night. That is a cast with motive, leverage and a shared room, delivered by
the trade's own structure rather than by a writer.

## 5. The money

| id | claim | label |
|---|---|---|
| M1 | The fare is AGREED, not metered. The price board on the wall is the firm's law. | DERIVED from L8 |
| M2 | Cash in a dish, and account work invoiced monthly against dockets signed by the passenger. | AUTHORED for the docket; the account model is CITED-VIA-SEARCH-MODERN only |
| M3 | The office's own income: weekly radio rent from each driver rather than a share of each fare. | CITED-VIA-SEARCH-MODERN per D1, AUTHORED as this firm's choice |
| M4 | Any 1990 tariff, meter rate, licence fee, radio rent figure or driver's earnings. | UNSOURCED. Named as a hole rather than filled with a plausible number. |
| M5 | There is no national count of licensed private hire vehicles for 1988 to 1992 to calibrate against: comparable Department for Transport taxi and private hire records were first collected in 2005. | CITED-VIA-SEARCH | gov.uk taxi statistics collection; taxi and private hire vehicle statistics 2020; read 2026-09-10 |
| M6 | The trade's clock, and this one is a PROJECT fact rather than a research one: the last bus leaves Meridian about half past ten, ruled by the studio 2026-09-09 (`production/decision-queue.md`). After that, anybody going anywhere goes by cab. | DERIVED from a studio ruling |
| M7 | Bus deregulation from 26 October 1986 thinned evening and Sunday services across the country, which is the condition M6 describes. | CITED-VIA-SEARCH, carried from `atlas-02/research/transport-timetables.md`, which sourced it the same way on 2026-09-08 and is not upgraded here |

M6 AND M7 TOGETHER ARE THE COMMERCIAL CASE FOR THE ROOM AND ALSO THE
GAMEPLAY CASE. The firm's money is made between half past ten and three in the
morning. So is the game's.

## 6. What could not be found, collected in one place

Eleven searches, four blocked hosts, and these remain open. Each is a named
task and not a shrug.

1. THE INTERIOR OF ANY BRITISH MINICAB OFFICE, 1988 to 1992: no photograph, no
   plan, no description. The largest hole here.
2. THE RADIO REGIME: licensing body, Act, band, channel spacing, cost (R6).
3. PROCEDURE ON AIR: procedure words, car numbering, selective calling (R5).
4. THE VEHICLE PLATE: form, colour, whether one or two, in any district (D5).
5. MONEY: any 1990 fare, radio rent, licence fee or weekly earning (M4).
6. WHETHER THE SETTLE MODEL IS PERIOD at all, as opposed to present-day (D1).
7. WHETHER PROVINCIAL COUNTER SCREENS EXISTED IN 1990 (O1).
8. A COUNT of licensed operators or vehicles anywhere in England in the window
   (M5 says the series does not start until 2005).
9. THE FULL TEXT of the 1976 Act: `legislation.gov.uk` is blocked from this
   container, so every section number above is a summary of that page and not
   the page. IF ONE THING IN THIS FILE IS RE-SOURCED FIRST, IT IS THIS.

THE FIX FOR ALL NINE IS THE SAME AND IT ALREADY HAS A QUEUE NUMBER: 156, a CI
fetch job on a machine whose network works. Add to its target list
`legislation.gov.uk/ukpga/1976/57/part/II` and the Hansard pages named at L10.

## 7. The one thing a designer should take from this file

A PUB IS A ROOM WHERE PEOPLE TALK. A CAB OFFICE IS A ROOM THAT IS LEGALLY
REQUIRED TO WRITE DOWN WHERE EVERYONE WENT.

That is not a preference and it is not a metaphor: it is section 56, and it
puts a book on a lectern with six columns in it, in a room the player owns,
open at the hours the game is about. Everything in the gameplay sheet comes
out of that sentence.
