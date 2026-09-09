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
