# DELIVERY: art/atlas-02

STATUS: DELIVERED, 2026-09-08. Commission `atlas-02`, pinned to
`f3f395c5dda6be684183ef4f02c1d0a533207bbf`, the full forty characters as
`game-design/art-collaboration.md` section 5 records it.

This file's PRESENCE is the signal the daily wake reads, so it is written to
be accurate rather than optimistic. What is here is here; what is not is named
below with the same weight.

## What is in this commission

RESEARCH ONLY. Five gap files under `production/art/atlas-02/research/`, each
answering one of the five gaps named in the standing order, each with its
sources dated and its holes named.

| file | lines | gap | how far it got |
|---|---|---|---|
| `research/small-pub-plan-measured.md` | 334 | 1, measured period small-pub plan | FILLED |
| `research/hillside-housing-dated-series.md` | 216 | 2, dated hillside housing series | FILLED |
| `research/household-contents-and-upstairs.md` | 210 | 3, household contents and upstairs | FILLED |
| `research/adult-clothing-by-occupation.md` | 179 | 4, adult clothing by occupation | PARTIAL, and says so in its own first paragraph |
| `research/transport-timetables.md` | 182 | 5, transport timetables | PARTIAL on the timetable as an object, filled on the dated facts |

All five were reached. Three are filled to the standard the brief set. Two are
partial and each carries a warning label at the top of its own file rather
than only here, so a builder who opens one without reading this cannot be
misled by it.

## What is NOT in this commission, stated so nobody looks for it

- THE TWELVE-PACKAGE CATALOGUE BATCH IS NOT STARTED. Jafar's standing order
  puts the twelve packages through the five stations AFTER the grate proves
  the mesh route. The grate has not proved it: the newest commit on this
  branch is "Run 2 of the mesh route, and this one is a measurement rather
  than a fix attempt". So no package is designed, no package is specified, and
  nothing here should be read as one.
- MICKEY'S IS NOT LAID OUT. Gap 1 is the research Mickey's will be authored
  FROM. It fixes the building carcass, the room set, the components and the arithmetic;
  it does not place a single wall of the player's pub.
- NO BRANCH, NO COMMIT. Files are written in this checkout for the resident to
  place, per the instruction that opened this commission.
- NO ASSET, NO MESH, NO TEXTURE. Nothing was fetched, so there is no
  third-party content in this delivery and nothing for the attribution sweep
  to see. Stated explicitly because a delivery that fetched nothing and a
  delivery that fetched something unattributed look the same from outside.
- NOTHING ADDRESSED TO JAFAR anywhere in these files, and no status report.
  The taste questions are at the bottom of this file as candidate cards with
  defaults, for the resident to route.

## The do-not-touch list

Every file written by this commission is under
`production/art/atlas-02/`. Nothing was written or read-modified in
`production/d1-probe/DISPATCH`, `.github/workflows/`,
`production/next-three.json`, the material generator, `CLAUDE.md`,
`.claude/rules/` or `ledger-v2/studio-v2/`. Nothing validates this; it is
stated so it can be checked in one command.

## The limit that shaped every file, and it is not a small one

OUTBOUND HTTPS TO EVERY RESEARCH HOST IS REFUSED IN THIS CHECKOUT. WebFetch
and curl were both tried against `en.wikipedia.org`,
`www.legislation.gov.uk`, `api.parliament.uk`, `pubheritage.camra.org.uk` and
`barclayperkins.blogspot.com`; every one answered 403 to CONNECT from the
organization egress proxy. Per `/root/.ccr/README.md` a policy denial is
reported rather than retried or routed around, so it is reported here.

WebSearch works, and every citation in these files is therefore the search
channel's SUMMARY of a named page rather than a page this session read in
full. Consequences, stated so a later reader can price them:

1. A figure could be a summariser's error rather than the source's claim. Two
   were caught this way: the published full weight of a beer firkin is given
   as 75 lb by one source and 72 kg by another, and the arithmetic in gap 1
   shows both are impossible, so the file ships a derived 51 kg with the
   contradiction printed beside it.
2. Where a primary table was the right answer, the failure to retrieve it is a
   named HOLE and not a filled-in memory: the ONS RPI beer price series, the
   General Household Survey durables tables, the Gaming Act stake limits in
   force in 1990, and the CAMRA heritage guides that would have carried a real
   room-by-room pub description.
3. THE SINGLE HIGHEST-VALUE FOLLOW-UP IS A CI FETCH JOB, because CI is where
   this project's network already lives. Three targets would close most of
   what is open: the Argos catalogues for 1990 and 1992 on the public web
   archive at archive.org (prices for gaps 3 and 4), the CAMRA Real Heritage Pubs guides
   (real pub interiors for gap 1), and the ONS beer price series CZMT.

## What each gap established, in one line each

1. PUB. The street's own file fixes the carcass (6.0 m bay, 8.0 m depth, 3.4 m
   and 2.8 m storeys), the period room set is cited from CAMRA and SAHGB, the
   capacity is derived from the published fire-safety floor space factors
   (0.3, 0.5 and 1.0 m2 per person), the cellar runs on cited numbers (11 to
   13 degrees C, 24 hours to settle, three days once tapped, a 40.91 litre
   firkin at a derived 51 kg full), and the licensing clock is dated to the
   day (all-day opening from August 1988, twenty minutes drinking-up time,
   under-14s barred until 1995, gill measures until the end of 1994).
2. HOUSING. A six-layer dated series from the 1875 byelaw terrace to the
   1981-1990 private estate at a cited average of 83.9 m2, with the Right to
   Buy chequerboard, the uPVC curve and the satellite dish as the three things
   that make any layer read as 1990.
3. HOUSEHOLD. Ownership rates as dials rather than prop lists: 18.5 percent
   with no central heating at the 1991 Census, 55 percent with a microwave by
   1991, 92,000 phone boxes at their 1992 peak, doorstep milk at or above 45
   percent, and an exactly dated coin and note set for a purse in 1990.
4. CLOTHING. The dock labour scheme abolished on 3 July 1989, which changes
   who wears the coat rather than the coat; the donkey jacket cited to its
   construction; and the police uniform pinned to the pre-1994 kit, which is
   the loudest available period error and is now closed off.
5. TRANSPORT. Bus deregulation from 26 October 1986 and what it does to
   evenings and Sundays; Provincial becoming Regional Railways on 3 December
   1990, which dates any poster on sight; APTIS tickets rather than Edmondson
   cards from mid-1989; and the first five years after Zeebrugge as the
   attitude on a ferry deck.

## What could not be found, collected across all five files

The per-file lists are authoritative; this is the index.

- A DIMENSIONED SURVEY OF ANY REAL SMALL PUB. No room size in gap 1 is claimed
  as measured from a real building; every dimension is the project's own
  street file, a published component standard, or printed arithmetic.
- Pub pool table size and price, cellar headroom, period counter height, beer
  line runs, 1990 gaming machine limits, the beer price series, and the exact
  Sunday permitted hours from primary text.
- Byelaw terrace frontage width, the disputed 70 ft facing-house separation,
  system-built council housing, British street gradient limits and hillside
  layout practice, and wheelie bin adoption.
- The GHS and Social Trends durables series for 1988 to 1992, prepayment meter
  type dates, duvet share, and a source for the four-channel line-up.
- Hi-vis and safety boot standards in the window, what a 1990 trawlerman
  actually wore, men's business dress, publican and bar staff dress, and
  clothing prices anywhere.
- Last bus times, evening frequencies, any 1990 fare or tariff, ferry sailing
  frequencies, and any period bus timetable leaflet or its house style.

## One finding the street's bill of materials should hear

Gap 1 derives that a pub needs a PAVEMENT BEER DROP: a hatch of roughly 1100
x 1100 mm in the 2.0 m footway, clear of the 0.125 m kerb and the 0.255 m
channel, over a cellar whose floor sits about 2.4 m below the road crown. The
593 pieces have a gully grate in the channel and two manholes in the
carriageway, and nothing at all in the footway; no beer drop anywhere. That is not a defect in the street; it is a piece the pub will need when
it is authored, and it is named here so it enters the bill of materials as a
known requirement rather than as a surprise.

## Candidate taste cards for the resident to route

Each carries a default so the work continues while he sleeps.

CARD 1: IS MICKEY'S A FREE HOUSE OR A TIED HOUSE?
Default: FREE HOUSE, owned outright. Canon says Mickey "left him the pub",
which reads as a freehold rather than a brewery tenancy, and a free house lets
the Beer Orders of 1989 be the WEATHER around the player (rivals buying up
newly freed pubs, brewers under a 31 October 1992 deadline) rather than a
leash on him. The alternative, a tied tenancy, gives the player a brewery
landlord with real leverage and a legal right to one guest cask beer, which is
a richer pressure but sits awkwardly with an inheritance. Consequence either
way: it changes who can lean on the player and what a rival can threaten.

CARD 2: HOW BIG IS THE PUB ON THE STREET?
Default: TWO BAYS, 12.0 m of frontage by 8.0 m deep, which is 96 m2 gross and
a derived fire capacity of about 130, of which a busy Friday would stage
roughly 44 adults. Three bays, 18.0 m, reads as a corner house or a former
coaching inn and quietly raises the pub's social class. Two bays is the
back-lane port local the premise describes.

SMALLER DEFAULT, folded in unless he says otherwise: the rooms SURVIVE. A
public bar and one snug, not knocked through, because most pubs were knocked
through in the 1970s and 1980s and the ones that were not are the ones whose
licensee never had the money. That reads as the half-dead inheritance the
premise starts from, and it gives the interior two acoustic and social spaces
instead of one.

## Quality ladder: best available, or first working?

FIRST WORKING, honestly, and the next rung has a name. The research is as
good as a search-only channel can make it, and the blocked-host list is the
reason rather than an excuse. The next rung is the CI fetch job in the limit
section above: three targets, one run, and gaps 1, 3 and 4 all move at once.
Until that runs, the two partial files stay partial and are labelled so at the
top of each.

## The canon gate was run over this delivery, and what it cost

MEASURED, not assumed: `python3 tools/canon-gate.py` over all six files.

- First run: RED, 18 findings in 6 files, 1297 lines examined, 13 era terms
  and 45 brand tokens screened.
- Final run of the delivery as authored: CLEAN, 0 findings in 6 files, 1304
  lines examined, same 13 era terms and 45 brand tokens screened.
- AFTER THE DIRECTOR'S AMENDMENTS A8, A11 AND A12, re-run 2026-09-08 over the
  seven files the delivery now has: CLEAN, 0 findings in 7 files, 1368 lines
  examined, same 13 era terms and 45 brand tokens screened. The line count is
  the sum of the seven files on disk; the earlier 1304 described six files
  before the labels and REVIEW.md were added, and is kept above rather than
  silently updated because it is what that run measured.

Every one of the 18 was the false-positive class the studio has already
recorded twice (learning entries L2 and L19): a document ABOUT the period
naming the things the period had, or stating the ban rather than breaking it.
The recorded answer is REWORD, NEVER LOOSEN, and that is what was done. The
gate was not touched, no exemption was added and no pattern was widened.

What the rewording cost, stated so a reader can price it rather than assume it
was free:

- Building fabric is now called the carcass, which is the street file's own
  word (`C1_terrace_carcass`). No loss.
- Two makes of car at a kerb became "a mass-market saloon". That detail was
  ASSUMED rather than sourced, and canon forbids real vehicle marques in the
  world anyway, so the reword is more correct, not less.
- The two era terms in the "what must not be in shot" list are now written as
  "no mobile handset" and "no networked computer service of any kind". Meaning
  preserved.
- The national rail operator is written by its period initials, and two
  citation titles are described rather than quoted. The URLs are untouched and
  carry the exact identity, so nothing is unverifiable.
- ONE REAL LOSS, and it is disclosed in the file where it happens: in
  `adult-clothing-by-occupation.md` the source URL for the period nylon
  leisure suit is WITHHELD, because the screened token is the article's slug
  and no rewording can keep both the URL and the gate. The host, the claim and
  a way to find the article in one search are all still there. That is the
  only place in this delivery where a citation is less complete than the
  research made it, and it is named rather than quietly dropped.
