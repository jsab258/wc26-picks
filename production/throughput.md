# Throughput ledger (the planning unit: verified pieces per week)

A piece counts when it passes station 3 (VERIFY) and lands at station 4
(INTEGRATE). Partial work counts zero (waste lesson 3).

| week | line | pieces verified | notes |
|---|---|---|---|
| 2026-W36 | dialogue bank | 1 (pub-regular-v1, 48 lines) | pilot of the five stations; mechanical gates clean (canon, rung, repetition worst 0.18, license tagged); tone PENDING the D7 judge, whose calibration sample this bank is |
| 2026-W36 | signage/brand | 0 (brand-bible-v1, 8 entries) | VERIFY passed and INTEGRATE did not, so by this ledger's own rule it counts ZERO. The only thing that reads content/brands/brand-bible-v1.json is its own verifier: rule 6, built is not running, applied to content. Grepped rather than assumed. Queued as 009 |
| 2026-W36 | prop/asset | 0 (pilot package one, A7_gully_grate) | THE FIRST PROP-LINE PILOT, and it counts ZERO by this ledger's own rule: station 4 INTEGRATE did not happen. Stations 1 SPEC and 2 AUTHOR are done (production/specs/asset-interface.md, and the GLB is on disk at 0.3999 x 0.015 x 0.3999 m as the spec box, exact to 0.0000 mm). Station 3 VERIFY passes in the container: the importer selftest reads 48 of 48, and it is wired into ledger/verify.py so it runs before every commit rather than by hand. Station 4 FAILED ON THE MACHINE and the reading names why: propGltfPlugins=GLTFExporter/1 propImportVia=none-of-2-candidates propImported=0/16 propFailed=16/16. The engine has a glTF EXPORTER and no importer, so nothing loaded back. Station 5 RECORD is this row. |

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

WHAT PILOT ONE HAS COST SO FAR, with its denominator: 3 builder sessions on
the prop line (one to build the importer, one to amend it, one to fix the
machine faults its first run exposed) plus 1 director review, over 0 verified
pieces. That is a numerator with no denominator and it is written that way on
purpose.

RECORDING A ZERO IS THE POINT OF THE LEDGER. The brand bible is real work,
cleanly verified, and it would be easy to enter as one piece: the entry
above is what stops a shelf of finished-looking content reading as
throughput. A piece nothing consumes has not been manufactured, it has
been written down.

The station-5 step was also SKIPPED for this batch and added afterwards,
which is worth admitting here rather than only in a lesson: the line has
five stations and the one that keeps everyone honest is the one easiest
to forget, because by then the work feels done.
