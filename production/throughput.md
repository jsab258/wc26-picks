# Throughput ledger (the planning unit: verified pieces per week)

A piece counts when it passes station 3 (VERIFY) and lands at station 4
(INTEGRATE). Partial work counts zero (waste lesson 3).

| week | line | pieces verified | notes |
|---|---|---|---|
| 2026-W36 | dialogue bank | 1 (pub-regular-v1, 48 lines) | pilot of the five stations; mechanical gates clean (canon, rung, repetition worst 0.18, license tagged); tone PENDING the D7 judge, whose calibration sample this bank is |
| 2026-W36 | signage/brand | 0 (brand-bible-v1, 8 entries) | VERIFY passed and INTEGRATE did not, so by this ledger's own rule it counts ZERO. The only thing that reads content/brands/brand-bible-v1.json is its own verifier: rule 6, built is not running, applied to content. Grepped rather than assumed. Queued as 009 |
| 2026-W36/W37 | prop/asset | 22 (pilot package one, A7_gully_grate) | THE FIRST PROP-LINE PILOT. It counted ZERO for three days by this ledger's own rule, station 4 INTEGRATE not having happened, and it crossed on 2026-09-09. Stations 1 SPEC and 2 AUTHOR are done (production/specs/asset-interface.md, and the GLB is on disk at 0.3999 x 0.015 x 0.3999 m as the spec box, exact to 0.0000 mm). Station 3 VERIFY passes in the container: the importer selftest reads 48 of 48, and it is wired into ledger/verify.py so it runs before every commit rather than by hand. Station 4 DID NOT HAPPEN, and the reason RECORDED HERE FIRST WAS WRONG: this row said "the engine has a glTF EXPORTER and no importer, so nothing loaded back". That was an instrument fault twice over and it is corrected by measurement, not by argument. Run 2 on f3f395c printed propGltfCanTranslate=3/3 with eleven Interchange plugins present, so the engine CAN translate glTF headlessly; the failure was the importer script treating a None return from its own load-back as the engine refusing. Run 3 on 7f12005 then imported 15 of 16: propImported=15/16 propSaved=15/16 propUassetsOnDisk=16 propUassetBytesOnDisk=1736681, the grate resolved at 0.0474 mm worst against its spec box, and sixteen real .uasset files are committed under ue-probe/Content/Ledger/Props/. IT COUNTS TWENTY-TWO, AND IT COUNTED ZERO FOUR HOURS EARLIER. Run 33 on 76e4238 placed the imported meshes in the walk build: propsAsMesh=22/23 where every earlier run read 0/23, propStandIns=1/23, propPlacedWithCollision=22/22 propPlacedCollisionUnread=0/22, and the one fallback is pavement_sign, whose source GLB holds three mesh nodes and whose resolver correctly refuses to choose among them. STATION 4 INTEGRATE HAS HAPPENED. The grate itself reads propBurialSubject=prop_drainage_grate_01_0/via=loaded-asset/collision=YES, and via=loaded-asset rather than via=box-stand-in is the word that says this is a placed reading and not spec arithmetic.

JAFAR'S ACCEPTING CASE IS MET AS OF RUN 36, 2026-09-09: ue-walk_05_grate_a.png has the drainage grate dead centre, diagonal slots and a frame, nothing across it, taken from the third standpoint after two were refused with rail_post1 named. The piece is a real imported mesh with collision at the road surface and it is now in a picture. WHAT IS NOT SETTLED is how it LOOKS: the grate and the band around it render near-white with almost no material read, which is queue 176 and the visual bar rather than the prop route. THE PARAGRAPH BELOW IS KEPT AS WRITTEN because a superseded reason is evidence of how the row got here.

WHAT WAS STILL NOT MET WHEN THIS ROW WAS LAST EDITED, and the distinction is the whole value of keeping this row honest. He asked for the grate as a real mesh WITH COLLISION IN A WALK CLIP. It is a real mesh with collision, measured. It is not in a clip, because propFullyBuried=1/23 and the one is the grate: it sits under the carriageway and the channel both, 20.00 mm of cover at the west footprint edge and 10.25 mm at the last sampled cell, so no camera can see it. THAT IS A STREET-SPEC FAULT AND NOT A PIPELINE FAULT, and the pipeline is what this ledger measures. Twenty-two pieces are verified; the pilot's own showpiece is verified and invisible.

THE REASON THIS ROW MOVED TWICE BEFORE IT MOVED HERE, kept because a deleted number cannot be audited. Run 3 printed propCollisionPrims=0/15 and it was read as fifteen meshes with no collision. That was not a measurement: EditorStaticMeshLibrary.get_simple_collision_count refuses by RETURNING -1 rather than raising, the importer believed any non-None return, and a refusal became a measured absence. Run 4, on a rebuilt reader, printed propCollisionPrims=15/15 with propCollisionVia=not-needed/already-had-1=15. THE MESHES HAD COLLISION ALL ALONG; the glTF import put a primitive on every one and nothing needed adding. The grate itself reads RESOLVED, saved=yes, simplePrims=1, bodySetup=present, 0.0474 mm worst against its spec box. So the ASSET half of Jafar's accepting case is finished and measured. THE ROW STILL COUNTS ZERO because station 4 INTEGRATE has not happened: the walk build has never placed one prop mesh (propsAsMesh=0/23, propStandIns=23/23), and the grate is specified 13.4 mm below the top of the continuous channel slab that spans it, so no frame can show it. A piece nothing places has not been manufactured. A mesh with no body setup photographs clean and a walking character falls through it. Station 5 RECORD is this row. |

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

- RUNNER TIME, the only clock this project measures directly. THREE runs of the
  mesh workflow have published a verdict. Run 2 on f3f395c:
  meshEditorBuildMinutes=1.42 propImportMinutes=0.18. Run 3 on 7f12005: 1.33
  and 0.27. Run 4 on a870a10: 1.37 and 0.35. So 1.60, 1.60 and 1.72 minutes,
  and that figure is the SUM OF
  THE TWO STEPS THE VERDICT TIMES, not the job: checkout, editor start and the
  commit-and-push step are outside it and unmeasured. ONE EARLIER RUN published
  NOTHING, so it contributes no minutes and is not averaged in;
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

OVER 22 VERIFIED PIECES, AND THIS IS THE FIRST TIME THIS FILE HAS HAD A
DENOMINATOR AT ALL.

THE ROUND TRIP, measured push to landed evidence rather than estimated, which is
the only wall clock this project owns:

- mesh run 4, dispatched 2026-09-08T23:23:49Z, evidence committed 23:25:56Z:
  2 min 07 s.
- run 33, dispatched 2026-09-09T01:01:57Z, evidence committed 01:07:39Z:
  5 min 42 s. That one is a cold build, a cook, a packaged launch, two crimes,
  a gossip round, 30 frames and a clip.

So the machine half of a piece is minutes, and it was always going to be. THE
COST IS THE STUDIO HALF AND IT IS SESSIONS.

WHAT A PIECE COST, AND THE SHAPE OF THE ANSWER MATTERS MORE THAN THE NUMBER.
Twenty-two pieces crossed station 4 in one run, on a pipeline that took the whole
of 8 September to build. Dividing the build cost by 22 would be arithmetic and
not a measurement: THE FIRST PIECE COST THE PIPELINE AND THE TWENTY-SECOND COST
NOTHING. The two figures that can be stated honestly are:

- SETUP, once: 22 engine-specialist and 7 instrument-builder spawns on 8 and 9
  September, plus 11 director spawns. WHAT THAT DENOMINATOR COUNTS: every engine
  and instrument spawn on those two days across the crime probe, the walk clip,
  the mesh import, the caption tool and the burial instrument together. The log
  holds an agent type and a timestamp and nothing that would let the prop line's
  share be read out of it, so this is an UPPER BOUND on the prop line's setup and
  not a measurement of it.
- MARGINAL, per piece after the pipeline exists: ZERO SESSIONS AND ABOUT
  0.35 MINUTES OF RUNNER TIME, that being propImportMinutes over the sixteen
  assets in one run. A twenty-third piece needs a GLB and nothing else, which is
  the number the twelve-package batch should be planned against.

AND THE HONEST CAVEAT ON THE MARGINAL FIGURE: it is measured over sixteen assets
that were already authored. It prices the IMPORT of a piece and not the MAKING of
one. What it takes to author a GLB worth importing is unmeasured, and the
twelve-package batch is what will measure it.

RECORDING A ZERO IS THE POINT OF THE LEDGER. The brand bible is real work,
cleanly verified, and it would be easy to enter as one piece: the entry
above is what stops a shelf of finished-looking content reading as
throughput. A piece nothing consumes has not been manufactured, it has
been written down.

The station-5 step was also SKIPPED for this batch and added afterwards,
which is worth admitting here rather than only in a lesson: the line has
five stations and the one that keeps everyone honest is the one easiest
to forget, because by then the work feels done.
