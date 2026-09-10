line: instrument
spec: tools/map.py's `above_tiles` helper degrades to a presence check when its anchor
  HEAT_FIRST_TILE is not found in the bytes, and still prints
  greenSplitAboveTheFirstTile=yes. Make a missing anchor read as MISSING or as the words
  "nothing measured", never as a pass, and print how many anchors were searched for.
acceptance: the live page passes with the anchor found and counted, and a planted page whose
  first-tile marker is renamed prints the missing-anchor outcome rather than yes.
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09. FOUND BY THE DIRECTOR WHO HAD INVERTED THAT GUARD EIGHT HOURS
  EARLIER, reading its code rather than its output. The guard's whole job since the 14:24
  ruling is to keep one sentence ABOVE the tiles; a restyle that renames the tile marker
  would leave the guard green while the sentence sank below the fold, which is the exact
  page the ruling overturned.
  IT IS A RATCHET IN THE PRECISE SENSE THE RULES NAME: it cannot tell a regression from an
  improvement, because the failure mode of its own anchor is indistinguishable from success.
