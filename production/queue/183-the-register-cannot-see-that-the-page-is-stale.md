line: instrument (the Producer's gate)
spec: The register's gate reads the served commit and its age, from
  production/map-notified.json (last.pageCommit, last.at) or from a committed
  served-verdict file when one exists, and prints servedPageAgeHours= and
  servedPageCommit= on the gate's done line beside filesChecked. PRINTED AND NOT
  GATED until a series has been read.
acceptance: two outcomes watched, a fixture with a fresh reading and one with a reading
  older than a day, both printing, neither refusing
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09. Dictated as C2 by
  game-design/decision-2026-09-09-the-hook-comparison-the-ruled-link-and-the-stale-pages.md
  section 3.4.
  WHY IT EXISTS. The register enforces a link floor: every message that speaks must
  carry a link to the glance, the map or the gallery. It cannot see whether those pages
  are CURRENT. Measured 2026-09-09: of 48 publish runs, 4 succeeded, the last at
  2026-09-07T20:23:12Z on commit 45de6c21, and the 30 runs since all failed. So for a
  day and a half every message passing the floor carried a link to a real page showing
  Sunday evening's state.
  A STALE PAGE IS WORSE THAN A 404, and that is the whole argument for this item: a 404
  tells him something is wrong and a stale page does not. tools/map.py already carries
  the same reasoning in its own main(), "a stale map that still looks current is worse
  than a page saying why there is no map today".
  RULE 2 GOVERNS THE BOUND: print the series first, gate later or never.
