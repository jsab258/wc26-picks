line: art (the authored street, station 4 INTEGRATE)
spec: The fascia package's pieces sit on the building rather than inside each
  other, and the burial reading proves it on a run.
acceptance: propFullyBuried back to its pre-fascia count with the fascia
  pieces present, and propBurialWorst naming something other than a fascia
  piece covering another fascia piece
max_sessions: 1
status: READY 2026-09-09 22:40Z. Caught by a test rather than by an eye, on
  work that was reverted before it landed, so the finding is preserved here
  and the placement is not.

  WHAT THE BURIAL READING SAID with the fascia package in the tree:
    propBurialWorst=100.0pct@150.00mm/on=prop_fascia_console_01_0
      /by=prop_fascia_cornice_01_0/of=40
    propFullyBuried=11/40  propAnyBuried=21/40
    propBuriedOn=prop_fascia_console_01_0/100.0pct@150.00mm/by=prop_fascia_cornice_01_0;
      prop_fascia_console_01_1/100.0pct@150.00mm/by=prop_fascia_cornice_01_0;
      prop_fascia_console_01_2/100.0pct@150.00mm/by=prop_fascia_cornice_01_1;
      (+18~more~not~shown)

  ONE HUNDRED PER CENT AT 150 MM IS A CONSOLE ENTIRELY INSIDE ITS OWN CORNICE.
  Eleven of forty props fully buried, against a pre-fascia reading where the
  worst case was a barrel 45 per cent over an oil drum. The consoles are the
  brackets that carry the cornice, so they are MEANT to meet it; sitting wholly
  within it is a different thing and it is what the reading says.

  READ THE INSTRUMENT'S OWN CAVEAT BEFORE FIXING THE GEOMETRY, because it is
  printed on the same line and it may be the whole story: the depth is an AABB
  depth and the stat is the fraction of a prop's own footprint whose top is
  inside another placed piece's bounds. A bracket tucked under a projecting
  cornice is exactly the shape that reads as buried without being wrong. THE
  MEASUREMENT TO MAKE FIRST is whether the console's own bounds are inside the
  cornice's bounds, not whether its footprint is under them.

  ALSO IN THE SAME OUTPUT AND NOT THE SAME FAULT: propsAsMesh=0/40 with
  propFallbackWhy capped at (+40~more~not~shown), so every one of the forty
  props fell back to a box stand-in and the cap ate the entire reason list.
  A cap that hides one hundred per cent of its population is queue 218's shape
  in a second instrument.

  ANSWERED 2026-09-10, AND THE ACCEPTANCE ABOVE IS SUPERSEDED. Ruled in
  `game-design/decision-2026-09-10-ruling-the-four-lane-batch.md` section 6 and
  amendment 4. The geometry question is closed by measurement and the geometry
  does NOT move: `consoleInsideCornice=NO`,
  `consoleRestingOnCornice=11/of=11`, `consolePenetrationWorstMm=0.000000`,
  `consoleOverlapVolWorstM3=0.00000000`, taken by
  `production/art/fascia-01/verify/fascia_contact_measure.cpp` and written up in
  `production/art/fascia-01/03-VERIFY-fascia-package.md` section 1. The item is
  re-pointed at the instrument as card 1. This item's own acceptance
  ("propFullyBuried back to its pre-fascia count") CANNOT be met without moving
  correct geometry, and it is withdrawn as an acceptance rather than failed.

  Amendment 4, applied verbatim, is the note the replacement key ships with:

  Bucket set changed 2026-09-10: SUNK / CONTACT / CLEAR / NO-DATUM. The
  previous propFullyBuried=11/40 counted resting-on and sunk-into together
  because the predicate was half-open and fired on a coincident face. The new
  split is a RECLASSIFICATION, not a regression; the two awnings at 370 mm and
  810 mm of real penetration stay in SUNK and the gate stays red on them.

  CARD 1, AND WHAT IS NOT DONE YET. `propFullyBuried=11/40` is RETIRED as a
  standalone key by amendment 4, and the replacement keys propSunk, propContact,
  propClear and propNoDatum ARE NOT IN THE GATE'S EMIT ON THIS COMMIT. The emit
  in `ue-probe/Source/LedgerProbe/Public/VignetteSpec.h` still prints
  `propFullyBuried` at line 1828 and the half-open predicate is still
  `C.MinY <= P.MaxY` at line 1089, unchanged and deliberately not touched here
  (03-VERIFY says 1092 for the predicate and that number was true of an earlier
  state of this header; both line numbers here were read on this commit):
  section 6 attaches five conditions to the replacement (a coincidence tolerance
  set from a PRINTED SERIES, a planted coincident face landing in CONTACT, a
  planted one-micron penetration landing in SUNK, the per-edge breakdown, and
  the four keys over one printed denominator with their sum shown) and none of
  them is met by a key rename. Until they are, READ propFullyBuried AS THE NOTE
  ABOVE SAYS: it is two buckets added together, not a count of buried props.

  THE SERIES THE TOLERANCE WILL BE SET FROM ALREADY EXISTS, so the first
  condition is not starting from nothing: 03-VERIFY section 1 prints 27 cover
  pairs, 11 at exactly 0.000000 mm of penetration and 16 between 3.74 mm and
  1043.45 mm. Any tolerance in the open interval between 0 and 3.74 separates
  them on today's street, and the bound must be set by reading that series
  again at the time, not by quoting this sentence.
