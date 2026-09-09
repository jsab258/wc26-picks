line: instrument (the brief Jafar reads)
spec: tools/morning-brief.py leads with an OUTCOME rather than a count, by reading
  something that names what changed for the game (the newest landed verdict's own
  status words, or production/next-three.json's done entries) instead of picture and
  commit totals. And it reports the studio versus game split, which it already
  computes, in every brief.
acceptance: on a morning when a crime landed and a piece reached a frame, the
  generated headline says so rather than counting pictures, and a brief that omits the
  studio versus game split does not pass
max_sessions: 1
status: READY 2026-09-09. Found by running the tool the daily wake names, AFTER a brief
  had already been written by hand and sent, which is the only reason the divergence
  was visible at all.
  MEASURED: sourcesRead=7/7, words=112/150, registerFindings=0. It works. Its headline
  is "Eighteen new pictures of the street since the previous brief, and six decisions
  are waiting for you" and its NEXT VISIBLE THING is "unknown, because nothing names
  it".
  THAT IS THE SHAPE RULED AGAINST 2026-09-06 after the first brief was wrong: "LEAD
  WITH WHERE THE PROJECT STANDS AND WHAT CHANGED FOR THE GAME. Not what was
  engineered." Eighteen pictures and ninety-one commits are what was engineered.
  WHY THE TOOL CANNOT DO BETTER TODAY: it reads counts, and an outcome is not a count.
  The night it was run on, a town composed its own sentence about a broken window and a
  drainage grate reached a frame for the first time, and nothing the tool reads could
  have told it either.
  THE SECOND HALF IS SMALLER AND IS ALSO A GAP: the wake says every brief reports the
  studio versus game split. The tool computes it (splitStudio=50/96 splitGame=46/96,
  basis spawns) and the hand-written brief that went reported the ART share instead,
  which is a different question. No gate reads for coverage, only for shape.
