# Gap 5: transport timetables

STATUS: SPEC. Commission `atlas-02`, pinned to
`f3f395c5dda6be684183ef4f02c1d0a533207bbf`. Written 2026-09-08.

WHAT THIS IS. How people got about a British port town between 1988 and 1992,
what the timetable was as an OBJECT, and what the timetable was as a CLOCK.
Both halves matter here. The object is a prop with a layout a reader can
check; the clock is a schedule the simulation can run people on, and a town
whose buses stop at half past ten at night is a different crime sim from one
whose buses do not.

Labels are as defined in `small-pub-plan-measured.md` section 0. Same sourcing
limit.

## 1. Buses: the window is the aftermath of deregulation

- CITED: bus deregulation under the Transport Act 1985 came into force on 26
  October 1986, everywhere in Great Britain outside Greater London. Road
  service licensing was abolished and competition on local services was
  allowed for the first time since the 1930s. Source: "Transport Act 1985",
  https://en.wikipedia.org/wiki/Transport_Act_1985 (search summary); House of
  Commons Library Research Paper 95/57, "Deregulation of the Buses",
  https://researchbriefings.files.parliament.uk/documents/RP95-57/RP95-57.pdf .
- CITED: deregulation triggered a minibus boom; GM Buses introduced Little Gem
  minibus services in October 1986. Source: Museum of Transport Greater
  Manchester timeline, https://motgm.uk/timeline-6-deregulation.html .
- CITED: in the PTE areas patronage fell about 20 percent, fleets were cut 29
  percent, over 6,800 jobs went, and revenue fell 15 percent in real terms
  despite large fare increases. Source: Research Paper 95/57 as above, and Ian
  Savage, "Deregulation and Privatization of Britain's Local Bus Industry",
  https://faculty.wcas.northwestern.edu/ipsavage/415-manuscript.pdf .
- CITED, WEAK AND UNCORROBORATED: passenger journeys outside London fell from
  about 5.6 billion in 1985/86 to 4.8 billion by 1990/91. This came back as a
  single search-channel summary without a page I could open, so it is marked
  weak; the direction is certain, the two figures are not.
- DERIVED WHAT THIS MEANS FOR MERIDIAN, from the 1985 Act deregulation
  sources above, and it is the useful part. In 1990 a town's buses are NOT a
  single municipal network. Expect: two or more operators on
  the same profitable corridor at the same minute, competing liveries at the
  same stop, minibuses on routes that used to have double-deckers, evening and
  Sunday services thinned or gone because they are the unprofitable ones the
  council must now tender for separately, and fares that went up. A player who
  misses the last bus in Meridian is living inside a 1985 Act.
- HOLE 1: I could not source a typical last-bus time, a typical evening
  frequency, or a 1990 single fare. The last bus is currently ASSUMED at
  22:30 to 23:15 in the delivery file's taste card, and it is assumed, not
  researched.

## 2. Rail: sectors, units and the two dates a year

- CITED: BR's passenger sectors in the window are InterCity, Network
  SouthEast and Provincial, which was RENAMED REGIONAL RAILWAYS ON 3 DECEMBER
  1990. Sources: "Regional Railways",
  https://en.wikipedia.org/wiki/Regional_Railways ; "Sectorisation", British
  Rail Wiki (search summaries).
- DERIVED CONSEQUENCE, from the 3 December 1990 rename above, and it is a
  free dating device: a poster, a timetable cover or a train side that says
  Provincial is 1990 or earlier, and one that says
  Regional Railways is December 1990 or later. Two brands, one boundary, one
  date, and a port town outside the South East is Provincial or Regional
  Railways territory, not InterCity's.
- CITED: the first Class 156 Super Sprinter appeared in November 1987 and the
  last of 114 in September 1989; Class 158 Express Sprinters entered service
  from 1990 and 182 sets were built between 1989 and 1992. Sources: the Wikipedia
  articles on the Class 156 Super Sprinter and the Class 158 Express Sprinter,
  https://en.wikipedia.org/wiki/British_Rail_Class_156 and
  https://en.wikipedia.org/wiki/British_Rail_Class_158 .
- CITED: the national passenger timetable went to twice-yearly publication in
  1986, appearing in late May and late September. The 1990 summer timetable
  began on Monday 14 May 1990 and the winter timetable ran from Monday 1
  October 1990 to 12 May 1991. Sources: branchline.uk rail chronology,
  https://branchline.uk/rail_chronology/Timetable-dates.html ; the Transport
  Store listing for the national passenger timetable, 1 October 1990 to 12 May
  1991,
  https://www.transportstore.com/British-Rail-Passenger-Timetable-great-Britain-1-October-1990-To-12-May-1991-Book-22918-1111.cfm .
- WHY THAT IS WORTH HAVING: it gives a timetable prop an exact, checkable
  validity line. A fictional Meridian timetable that reads "14 May to 30
  September 1990" is period-true in its STRUCTURE even though the town is
  invented, and a reader who knows the period will believe it. A timetable
  with no dates on the cover is the tell of a prop nobody researched.

## 3. Tickets, which are small props that are easy to get wrong

- CITED: APTIS, the Accountancy and Passenger Ticket Issuing System, was
  introduced from October 1986; the last station selling Edmondson card
  tickets before full conversion was Emerson Park on 29 June 1989. Sources:
  "APTIS", https://en.wikipedia.org/wiki/APTIS ; "APTIS ticket features"
  (search summaries).
- DERIVED CONSEQUENCE, from the last Edmondson-selling station converting on
  29 June 1989: an Edmondson card ticket, the small stiff card in the collector
  cliche, is WRONG for a 1990 station. The right prop is an APTIS card:
  credit-card sized, orange and cream, printed with origin, destination,
  class, route, price and the issuing machine's code.
- CITED: the Saver return was introduced in 1985; the SuperSaver was a cheaper
  and more restricted version; Cheap Day Return and Awayday were the day
  return products; Savers allowed a break of journey on the return portion but
  not the outward. Sources: "Off-Peak Return",
  https://en.wikipedia.org/wiki/Off-Peak_Return ; APTIS ticket features as
  above.
- HOLE 2: no fares. I could not source a 1990 single or return fare for any
  journey, nor railcard prices.

## 4. The ferry, which canon already has

Canon mints Meridian Ferry and the Meridian Harbour Board, so the town has a
ferry operation and this section is about what the period did to it.

- CITED: the Herald of Free Enterprise capsized leaving Zeebrugge on 6 March
  1987 with the loss of 193 lives, having sailed with inner and outer bow
  doors open; the master had no indicator on the bridge to tell him their
  position. Lord Justice Sheen's report called it a catalogue of errors and
  named the company's safety management as well as the immediate cause.
  Sources: MAIB report page, gov.uk,
  https://gov.uk/maib-reports/flooding-and-subsequent-capsize-of-ro-ro-passenger-ferry-herald-of-free-enterprise-off-the-port-of-zeebrugge-belgium-with-loss-of-193-lives ;
  SAFETY4SEA, "Herald of Free Enterprise: A wake-up call for Ro-Ro safety",
  https://safety4sea.com/cm-herald-of-free-enterprise-a-wake-up-call-for-ro-ro-safety/ .
- CITED: ferries were banned from sailing with loading doors open, and bridge
  indicator lights and cameras were fitted. Source: as above.
- WHAT IT MEANS IN THE WINDOW: 1988 to 1992 is the FIRST FIVE YEARS AFTER
  Zeebrugge. A Meridian ferry crew in 1990 works under new door checks and a
  bridge indicator panel that is visibly recent, and the disaster is inside
  living memory for every person on the quay. That is a period attitude, not
  just a fitting: procedure is being taken seriously because of something
  everyone watched on the news three years ago.
- HOLE 3: I could not obtain 1990 sailing frequencies or crossing times for
  any British ferry route. Every search returned current operators' pages. So
  the Meridian Ferry's frequency is a design decision, not a researched one,
  and the delivery file carries it as a taste card.

## 5. Taxis

- CITED: the two licensed types are hackney carriages, which may be hailed in
  the street or wait on a rank and carry a roof light and a meter charging the
  council's set fare, and private hire vehicles, which must be pre-booked
  through a licensed operator and are not fare-regulated. Sources: Hart
  District Council licensing pages,
  https://www.hart.gov.uk/licensing-and-permits/taxis/vehicle-licences/hackney-carriage-or-private-hire-vehicle ;
  Buckinghamshire Council taxi guidance.
- WHAT THE WINDOW ADDS: a minicab office is a room with a counter, a wall
  phone, a radio base set and a controller calling car numbers, because the
  booking is made by LANDLINE and dispatched by RADIO. There is no app, no
  card machine and no satellite navigation. That room is a very good
  late-analog interior and it is a natural information node for a gossip
  simulation: the controller knows who went where and at what time.
- HOLE 4: no 1990 meter tariffs.

## 6. The timetable as an object

This is the part a prop artist needs and the part I could not source, so it is
labelled hard.

- CITED (structure, from the rail sources above): the national timetable is a
  BOOK, published twice a year, with a validity span printed on the cover.
- ASSUMED, and every bullet here is assumed: a local bus timetable in this
  period is a folded leaflet or a card; stops carry a flag and a case with a
  paper timetable inside it; the table reads with places down the left and
  journeys as columns; separate blocks or separate tables for Mondays to
  Fridays, Saturdays, and Sundays and Bank Holidays; footnote letters against
  individual times with a key at the foot; request stops marked; the operator
  and a telephone enquiry number at the bottom, in the pre-1995 format with no
  extra 1 in the area code.
- HOLE 5: I could not source a single period bus timetable leaflet or any
  house style for one, and I could not confirm whether BR's public
  timetable used the 24-hour clock in this era, though it almost certainly
  did. Every layout claim above is therefore a reconstruction, and a builder
  should treat the LIST as a checklist to verify rather than as evidence.
- THE PHONE NUMBER RULE, which is free and correct: PhONEday, which inserted a
  1 into British area codes, was 1995. Every printed number in Meridian is
  therefore in the pre-1995 form. It appears in no source I could reach in
  this session and is recorded here as ASSUMED but high-confidence, to be
  verified before it is printed on a prop.

## 7. What the simulation can take from this file today

Three things are solid enough to build on now:

1. Two dated brand states for rail, either side of 3 December 1990.
2. An APTIS ticket rather than an Edmondson card, from 29 June 1989 onwards.
3. A deregulated bus network with competing operators, thinned evenings and
   thinned Sundays, from 26 October 1986.

Everything else in this file is either shape or a named hole, and the last
bus time, the ferry frequency and the timetable layout are the three that
would repay a second research pass most.
