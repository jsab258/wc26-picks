line: studio (attribution)
spec: The production/art row in tools/attribution-check.py matches by PREFIX, and
  tools/art-deliveries.py puts an outside artist's delivery under the same tree, so
  a delivered PNG would be classified as ours by a row that only ever meant the
  previews. The value says so today; the path rule does not.
acceptance: under production/art only */previews/ is ours; a delivery is classified by its
  own row, and the check learns the shape rather than a list
max_sessions: 1
status: READY 2026-09-08. Filed by the director ruling
  game-design/decision-2026-09-08-crimeprobe-the-grate-and-the-art-line.md,
  section 7, which files names rather than work.
