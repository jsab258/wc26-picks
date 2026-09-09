line: art (the visual bar) and instruments, jointly
spec: The Hook sheet's panel bounds are recorded in a file that the comparison
  reads, so no session locates them again and none locates them wrong.
acceptance: a tool prints the reference photograph's box and its three band
  boxes, with the rule that found them, and the recorded numbers match a fresh
  run of that rule over hook.png
max_sessions: 1
status: READY 2026-09-09 21:00Z, filed from a fault of this studio's own making.

  WHAT HAPPENED. The reference row that has driven rung 1 all day cropped
  hook.png at (0,768,1024,1536) and called that the lower panel. 244 of those
  768 rows, 32 per cent, are the sheet's material swatch strip and its
  near-white caption band, and the crop also omits 106 rows off the TOP of the
  street photograph. The caption band alone reads mean=0.9566 p95=0.9723, and
  it is what produced the claim "the two bright ends nearly agree". They do
  not: reference street p95=0.8239 against ours 0.9532.

  THE BOUNDS WERE ALREADY IN THIS REPO AND A SESSION RE-DERIVED THEM WRONGLY.
  This is the sharper form of the item and it was found after the item was
  first written. production/specs/vignette-scene.json, the cam_hook entry's own
  note, records "the panel content area is x 11 to 1012 and y 662 to 1278 of
  the 1024x1536 sheet", written when cam_hook was placed FROM that panel. It
  agrees with tonight's independent measurement to one pixel at each far edge.
  So the afternoon's crop was not a hard problem solved badly, it was a solved
  problem nobody read. The item is therefore NOT "find the bounds", it is
  "make the comparison READ the bounds that already exist", and the second
  copy is the thing to delete rather than to add.

  HOW THE REAL BOUNDS WERE FOUND INDEPENDENTLY, and it is the rule to ship. Near-uniform
  bright rows are the sheet's cream gutters: std<0.02 and mean>0.85 over the
  row. That finds runs at 655..661 and 1279..1291, and trimming the cream
  margin off both axes by the same rule gives the photograph as x 11..1013,
  y 662..1279, 1002x617. THE EYE GOT THIS WRONG FIRST: reading the boundary
  off a downscaled composite put the swatch strip inside the photograph.

  WHY A FILE AND NOT A COMMENT. The bounds are used by any comparison against
  this sheet, and three sessions have now measured this image. A comment
  recording them decays; a file the comparison READS cannot be wrong without
  the comparison being wrong with it, which is the difference between a claim
  and an instrument.

  THE SELFTEST SHIPS WITH IT, ACCEPTING CASE FIRST: hook.png is the accepting
  fixture, and the rejecting fixture is synthetic, a sheet with no gutter at
  all, which must read "nothing measured" rather than a clean zero.
