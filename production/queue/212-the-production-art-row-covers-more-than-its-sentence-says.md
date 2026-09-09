line: instrument
spec: tools/attribution-check.py has a WATCHED row for `production/art` whose text reads
  "Blender previews only, under production/art/*/previews", and adds that a DELIVERY under
  the same commission is somebody's and is not covered by this row. The art lane's compare
  output lands at production/art/compare/<name>, which that row silently swallows: the sweep
  passes and the row's own sentence is no longer true of what it covers. Narrow the row to
  what it says, or widen its sentence to what it covers, and print which.
acceptance: the live tree passes with the row's coverage counted and printed, and a planted
  file under production/art that the row's sentence does not describe is UNCLASSIFIED rather
  than silently covered.
max_sessions: 1
status: READY 2026-09-09. FOUND TWICE IN ONE EVENING by two builders working on different
  files, which is itself the argument: a row whose text and whose glob disagree will be
  rediscovered by whoever next puts a file under that prefix.
  NOTHING IS BEING HIDDEN TODAY. The compare pictures are genuinely ours, drawn on this
  project's own weights from this project's own prompt, so no third-party claim is being
  swallowed. What is wrong is that the sweep would report the same clean number if one were.
  Baseline for the fix to preserve: walked=4917 assetFiles=2789 unclassified=0 rows=16, and
  production/art currently matches 0 files.
  QUEUE 153 ALREADY OWNS THE NARROWING and this item should fold into it rather than compete.
