line: studio (attribution)
spec: The production/art row in tools/attribution-check.py matches by PREFIX, and
  tools/art-deliveries.py puts an outside artist's delivery under the same tree, so
  a delivered PNG would be classified as ours by a row that only ever meant the
  previews. The value says so today; the path rule does not.
acceptance: under production/art only */previews/ is ours; a delivery is classified by its
  own row, and the check learns the shape rather than a list
max_sessions: 1
status: READY. REOPENED 2026-09-10, hours after being closed, because the hole stopped
  being hypothetical. It was closed the same day as "not on the ladder", which was a
  reasonable prune of a finding nobody had measured. Then it was measured. Under
  production/art there are now 28 files of an asset kind and ZERO of them are under
  */previews: 14 in mickeys-cars/drawings, 6 in concept-fairview-2026-09-10/sheets, 4 in
  compare/hook-2026-09-09 and 4 in compare/hook-2026-09-09-pass2. So the row's stated
  reason, "Blender previews only", is now true of NONE of the files it classifies as ours,
  and the check passes green while saying it. Adding .svg to the asset kinds on 2026-09-10
  put 7 more files under that false description, which is what surfaced it.
  The per-directory ATTRIBUTION.json files do carry real licence text (the compare boards
  name Z-Image-Turbo, Apache-2.0, and the text encoder), so nothing here is unattributed
  in fact. What is wrong is the ROW, and an attribution record whose reason is false of
  every file it covers is the shape that gets believed until the day it matters.
  PRIOR STATUS, kept: filed as a finding rather than as ladder work 2026-09-08. Filed by the director ruling
  game-design/decision-2026-09-08-crimeprobe-the-grate-and-the-art-line.md,
  section 7, which files names rather than work.
