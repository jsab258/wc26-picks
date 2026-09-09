line: art (the visual bar)
spec: Measure why the road and the grate render as a near-white field in the near half
  of the grate camera's frames, and say which of exposure, material, lighting or a
  missing surface it is, before anything is changed.
acceptance: a number names the cause, taken off the already-committed frames, and no
  material or light is touched until it does
max_sessions: 1
status: READY 2026-09-09. Amendment A6 of
  game-design/decision-2026-09-09-the-railing-in-the-line.md, filed here because a
  non-blocking amendment is not recorded until it has a queue number, which is a rule
  this studio broke twice in one night.
  MEASURED BY EYE AND NOT YET BY ANYTHING ELSE: in ue-walk_05_grate_a.png and
  ue-walk_06_grate_b.png the band that carries the grate renders as a flat pale,
  nearly white field with a faint angular shape in it, while the carriageway 1 to 2.7 m
  further off in the same frame renders as textured grey with red aggregate. The same
  white band appears in all six crime stills where the ground planes end.
  IT NEEDS NO DISPATCH. A Pillow read over the two committed frames gives the mean and
  spread of the near band against the far band, in the same frame, with the far band as
  the control, which is the shape tools/grate-zfight.py already uses. Pixels examined is
  the denominator; set no bound.
  WHY IT MATTERS BEYOND ONE PIECE: the Meridian Test's first condition is that a person
  who loves GTA or KCD2 does not bounce off the visuals in thirty minutes. A near road
  that reads as white paper is the kind of thing that bounces them in five seconds, and
  it has been visible in every still opened tonight without anything measuring it.
  RULE 4 GOVERNS THE ORDER: a picture is strong evidence that something is wrong and
  weak evidence of what. Print the quantity before touching a material.
