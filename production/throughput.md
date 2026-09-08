# Throughput ledger (the planning unit: verified pieces per week)

A piece counts when it passes station 3 (VERIFY) and lands at station 4
(INTEGRATE). Partial work counts zero (waste lesson 3).

| week | line | pieces verified | notes |
|---|---|---|---|
| 2026-W36 | dialogue bank | 1 (pub-regular-v1, 48 lines) | pilot of the five stations; mechanical gates clean (canon, rung, repetition worst 0.18, license tagged); tone PENDING the D7 judge, whose calibration sample this bank is |
| 2026-W36 | signage/brand | 0 (brand-bible-v1, 8 entries) | VERIFY passed and INTEGRATE did not, so by this ledger's own rule it counts ZERO. The only thing that reads content/brands/brand-bible-v1.json is its own verifier: rule 6, built is not running, applied to content. Grepped rather than assumed. Queued as 009 |
| 2026-W36 | prop/asset | 0 (pilot package one, A7_gully_grate) | THE FIRST PROP-LINE PILOT, and it counts ZERO by this ledger's own rule: station 4 INTEGRATE did not happen. Stations 1 SPEC and 2 AUTHOR are done (production/specs/asset-interface.md, and the GLB is on disk at 0.3999 x 0.015 x 0.3999 m as the spec box, exact to 0.0000 mm). Station 3 VERIFY passes in the container: the importer selftest reads 48 of 48, and it is wired into ledger/verify.py so it runs before every commit rather than by hand. Station 4 DID NOT HAPPEN, and the reason RECORDED HERE FIRST WAS WRONG: this row said "the engine has a glTF EXPORTER and no importer, so nothing loaded back". That was an instrument fault twice over and it is corrected by measurement, not by argument. Run 2 on f3f395c printed propGltfCanTranslate=3/3 with eleven Interchange plugins present, so the engine CAN translate glTF headlessly; the failure was the importer script treating a None return from its own load-back as the engine refusing. Run 3 on 7f12005 then imported 15 of 16: propImported=15/16 propSaved=15/16 propUassetsOnDisk=16 propUassetBytesOnDisk=1736681, the grate resolved at 0.0474 mm worst against its spec box, and sixteen real .uasset files are committed under ue-probe/Content/Ledger/Props/. IT STILL COUNTS ZERO, and the reason is now measured rather than read off a number that turned out to be false. Run 3 printed propCollisionPrims=0/15, which was taken as fifteen meshes with no collision. IT WAS NOT A MEASUREMENT. EditorStaticMeshLibrary.get_simple_collision_count refuses by returning -1 rather than raising, the importer treated any non-None return as an answer, and the tally turned a refusal into a measured absence. So the true reading of run 3 is that NOTHING READ whether any of the fifteen has collision, which is a different fact and a weaker one. Jafar's accepting case is the grate WITH COLLISION in a walk clip, and until a route both sets it and reads it back, the piece is unverified for want of a measurement rather than for want of collision. A mesh with no body setup photographs clean and a walking character falls through it. Station 5 RECORD is this row. |

## Cost per verified piece, and the calibration it rests on

ASKED FOR BY JAFAR 2026-09-08 for pilot package one. The honest answer this
week is that it is UNDEFINED, not zero: the denominator is zero verified
pieces, and a cost divided by no pieces is not a number. Recording it as zero
would be the false claim with a number on it that rule 3b exists to stop.

THE CALIBRATION, stated so the first real figure can be read against
something. The only cost unit this project can OBSERVE is the session. Nothing
inside the container can read Jafar's usage page, which is a standing
instruction of his and not a limitation to be worked around, so a token figure
here would be invented. What can be measured is:

- SESSIONS, counted from `.claude/agent-log.tsv` spawn rows, which is the same
  denominator `directorSpawns` and `gameShareDay` already use in the verify
  footer, so the number is comparable to figures this project already prints.
- JAFAR'S OWN READINGS in `production/budget.md`, bracketing the work. Those
  are percentages of an allowance, not of this project: the 2026-09-08 rows
  say in his words that the window was not clean and that the change must not
  be attributed wholly to this work.

SO THE FIGURE, WHEN THERE IS ONE, IS SESSIONS PER VERIFIED PIECE, and any
percentage beside it is an UPPER BOUND on studio cost rather than a
measurement of it. That distinction is the calibration. It is the same one the
budget file has carried since 2026-09-06 and it is the reason no per-session
point rate has ever been computed from a dirty window.

WHAT PILOT ONE HAS COST SO FAR, with its denominator, read off the log and the
verdict files on 2026-09-08 rather than recalled:

- RUNNER TIME, the only clock this project measures directly. Two runs of the
  mesh workflow have published a verdict. Run 2 on f3f395c:
  meshEditorBuildMinutes=1.42 propImportMinutes=0.18. Run 3 on 7f12005: 1.33
  and 0.27. So 1.60 minutes each, and that figure is the SUM OF
  THE TWO STEPS THE VERDICT TIMES, not the job: checkout, editor start and the
  commit-and-push step are outside it and unmeasured. A third run fired earlier
  and published NOTHING, so it contributes no minutes and is not averaged in;
  the cost of a run that measures nothing is real and is recorded as a count,
  one, rather than folded into a mean.
- STUDIO SESSIONS. 17 engine-specialist spawns on 2026-09-08, and WHAT THAT
  DENOMINATOR COUNTED MATTERS: it is every engine spawn that day across the
  crime probe, the walk clip and the mesh import together. The log records an
  agent type and a timestamp and nothing else, so the prop line's share of the
  17 cannot be read out of it. Attributing all 17 to the props would be a
  numerator borrowed from three lines, and that is exactly the shape rule 3b
  calls a false claim with a number on it. Plus 2 director reviews, both of
  which were about the prop line and are attributable.

OVER 0 VERIFIED PIECES. That is a numerator with no denominator and it is
written that way on purpose.

WHAT WOULD MAKE IT A NUMBER: collision, measured as a sweep that hits the
placed grate rather than as a primitive count, and one frame of the walk clip
showing a character stopped by it. At that point the denominator becomes 1 and
the first real sessions-per-verified-piece figure exists. Until then the
division is refused.

RECORDING A ZERO IS THE POINT OF THE LEDGER. The brand bible is real work,
cleanly verified, and it would be easy to enter as one piece: the entry
above is what stops a shelf of finished-looking content reading as
throughput. A piece nothing consumes has not been manufactured, it has
been written down.

The station-5 step was also SKIPPED for this batch and added afterwards,
which is worth admitting here rather than only in a lesson: the line has
five stations and the one that keeps everyone honest is the one easiest
to forget, because by then the work feels done.
