# VERIFY: the fascia package, every reading taken on 2026-09-10

STATUS: LOG. Station 3 of five for `C15_fascia_cornice_console`. Governed by
`canon.md`, which outranks this file. Every number below was produced by a
command run in this container on 2026-09-10 and the command is printed beside
it, because a reading without its command is a claim.

THIS FILE WAS MISSING UNTIL TODAY AND THE SPEC CITED IT. Section 4 of
`01-SPEC-fascia-package.md` says "the results are in
`03-VERIFY-fascia-package.md`", and that file did not exist: the package had
SPEC, AUTHOR and a prepared INTEGRATE, and its verification lived only in a
session's scrollback. So the ten acceptance checks were re-measured from
scratch today rather than transcribed from a date nobody can re-run.

## 0. The headline, in the two numbers the commission asked for

CONSOLE INSIDE ITS CORNICE: NO. Measured, not argued.
`consoleRestingOnCornice=11/of=11 consolePenetrationWorstMm=0.000000
consoleOverlapVolWorstM3=0.00000000 consoleInsideCornice=NO`

THE MESH IS IN THE STREET SPEC AND NOT YET IN THE ENGINE. The 17 rows are in
`production/specs/vignette-scene.json` and the 610-piece list both engines build
from; `propsAsMesh` has not been re-measured because the engine run is the game
lane's today. Station 4 is therefore NOT crossed and the throughput row says
ZERO. Section 6 names the key that will cross it.

## 1. Queue 228: the measurement it asked for FIRST, and what it means

AMENDMENT 4, 2026-09-10. Every `propFullyBuried=11/40` in this section is
RETIRED as a standalone key by section 6 and amendment 4 of
`game-design/decision-2026-09-10-ruling-the-four-lane-batch.md`. Read it with
this note beside it:

Bucket set changed 2026-09-10: SUNK / CONTACT / CLEAR / NO-DATUM. The
previous propFullyBuried=11/40 counted resting-on and sunk-into together
because the predicate was half-open and fired on a coincident face. The new
split is a RECLASSIFICATION, not a regression; the two awnings at 370 mm and
810 mm of real penetration stay in SUNK and the gate stays red on them.

The replacement keys are NOT in the gate's emit on this commit and the five
conditions attached to them are carried in
`production/queue/228-the-fascia-props-are-buried-in-each-other.md`. The
penetration series printed below (11 pairs at exactly 0.000000 mm, 16 between
3.74 mm and 1043.45 mm over 27 cover pairs) is the series the coincidence
tolerance must be read off when it does land.

Queue 228 reported, with the fascia rows in the tree:

    propBurialWorst=100.0pct@150.00mm/on=prop_fascia_console_01_0
      /by=prop_fascia_cornice_01_0/of=40
    propFullyBuried=11/40  propAnyBuried=21/40

and said: READ THE INSTRUMENT'S OWN CAVEAT FIRST, because the measurement to
make is whether the console's own bounds sit inside the cornice's bounds, which
is a different question from the one the gate answers.

### The reading reproduced in the container, with no engine

    g++ -std=c++11 -O1 -Wall -o vignette-spec-test ue-probe/tests/vignette-spec-test.cpp
    ./vignette-spec-test production/specs/vignette-pieces.json

prints the live burial series off the committed piece list, because
`VignetteSpec.h`'s `SpecBoxBounds` exists to let the container exercise the same
arithmetic with no engine present. It reproduces queue 228 exactly:
`propFullyBuried=11/40`, `propAnyBuried=21/40`,
`propBurialWorst=100.0pct@150.00mm/on=prop_fascia_console_01_0/by=prop_fascia_cornice_01_0/of=40`,
and all eleven fully buried props are consoles, each covered by its own
cornice, each at 400 of 400 cells and 150.00 mm.

### THE MEASUREMENT QUEUE 228 ASKED FOR, AND IT IS A DIFFERENT NUMBER

`production/art/fascia-01/verify/fascia_contact_measure.cpp` includes the same
header and calls the same `BurialCandidates` and `ReadBurialCell`, so the
straddle test is not reimplemented. It adds the half the gate does not print.
For a prop top T and a straddling cover spanning Cmin to Cmax:

| quantity | what it is | the gate prints it |
|---|---|---|
| Cmax minus T | how much cover stands ABOVE me | YES, as `deepestMm` |
| T minus Cmin | how far OF ME is inside the cover | NO |

    g++ -std=c++11 -O1 -Wall -I ue-probe/Source/LedgerProbe/Public \
        -o fascia_contact_measure \
        production/art/fascia-01/verify/fascia_contact_measure.cpp
    ./fascia_contact_measure production/specs/vignette-pieces.json

    propsExamined=40 propsWithACoverOverTheirTop=21/of=40 coverPairs=27
    contactPairs=11/of=27 sunkPairs=16/of=27
    penetrationWorstMm=1043.45/on=prop_wooden_crate_01_1/by=prop_wooden_crate_01_0
    consoleUnderCornicePairs=11 consoleRestingOnCornice=11/of=11
    consolePenetrationWorstMm=0.000000 consoleOverlapVolWorstM3=0.00000000
    consoleInsideCornice=NO

Every one of the eleven console rows reads:

    propTopM=3.500000 coverAbMm=150.00 penetrMm=0.00 overlapM3=0.00000000
    propSpanInsideCover(x/y/z)=in/out/in RESTING-ON cells=400/400

So: THE CONSOLE'S BOUNDS ARE NOT INSIDE THE CORNICE'S. They share exactly one
plane, y = 3.500000. The AABB intersection volume is exactly zero. The y span is
`out`, which is the axis that decides the question. The 150.00 mm is THE
CORNICE'S OWN HEIGHT standing above the console's top, not a depth of the
console inside anything: two brick courses at the scene file's own
`brick_course_m` of 0.075.

WHY THE PREDICATE FIRES. `VignetteSpec.h` line 1092 asks `C.MinY <= P.MaxY`
with the candidate filter `C.MaxY > P.MaxY`, a half-open interval [Cmin, Cmax).
A cover whose underside IS the prop's top satisfies it with zero penetration.
The header's own text says a cell is buried when "the prop's top surface is
inside that piece"; a surface lying on a boundary is not inside it, so the
reading and the sentence disagree at exactly one case, and that case is what a
bracket carrying a cornice IS.

### THE GEOMETRY DOES NOT MOVE, and three independently correct facts forbid it

1. A1: the cornice soffit is the fascia band top, 3.500000, exactly. A cornice
   sits on the band it protects.
2. A2: the console spans the band, 2.950000 to 3.500000, which is
   `east_parade_fascia0.sy_m` exactly. A console that stops short leaves the
   board's end grain open and no joiner does that.
3. Therefore the console top and the cornice soffit are the same plane. A3
   measures it at 0.0000 mm over 11 of 11.

Any change that clears the burial reading would either lift the cornice off the
band or drop the console below the thing it carries, and both are worse
geometry chosen to satisfy an AABB predicate. So the package's answer to queue
228 is the measurement above and NOT a moved piece.

### AND THE MISSING HALF IS NOT ONLY A FALSE ALARM: IT HIDES A REAL ONE

The same table, on rows this package did not write:

    prop_awning_02_0  east_parade_toplight1           coverAbMm=0.00  penetrMm=370.00  overlapM3=0.03569760
    prop_awning_02_0  east_parade_shopdoor1_spandrel  coverAbMm=0.00  penetrMm=810.00  overlapM3=0.04762800
    prop_awning_02_1  east_parade_toplight3           coverAbMm=0.00  penetrMm=370.00  overlapM3=0.03569760
    prop_awning_02_1  east_parade_shopdoor3_spandrel  coverAbMm=0.00  penetrMm=810.00  overlapM3=0.04762800

The gate prints 0.00 mm for these and the series reads them as harmless. The
penetration half says each awning stands 370 mm inside a toplight and 810 mm
inside a door spandrel, with 0.036 and 0.048 cubic metres of real overlap. That
is the SAME missing number reading the other way: 150.00 mm that means nothing
and 0.00 mm that means 810. One half of a placement metric cannot separate
resting-on from sunk-into in either direction, which is the standing pattern in
`.claude/rules/instruments.md` stated for a second instrument. Card 1.

Discrimination on the live street, so the new half is not an excuse: 16 of 27
cover pairs read SUNK-INTO at penetrations from 3.74 mm to 1043.45 mm, 11 of 27
read RESTING-ON at exactly zero, and the eleven are exactly the consoles.

## 2. Acceptance checks A0 to A10: measured, and now re-runnable

    python3 production/art/fascia-01/verify/measure_placement.py

`placementChecks=11/of=11-passing failures=none specPieces=610`

| # | bound | reading on 2026-09-10 |
|---|---|---|
| A0 | 0 rotated pieces of 17 | `rotated=0/of=17` |
| A1 | 0.0000 mm exactly over 6 | `worst=0.0000mm/on=all-6-at-exactly-zero bandTopM=3.500000` |
| A2 | 0.0000 mm exactly over 11 | `worst=0.0000mm/on=all-11-at-exactly-zero bandCentreYM=3.225000` |
| A3 | 0.0000 mm exactly over 11 | `worst=0.0000mm/pairsFound=11/of=11` |
| A4 | greater than 0 | `oversailM=0.095000 boardFaceZM=5.005000 corniceFaceZM=4.910000` |
| A5 | greater than 0 | `oversailM=0.035000 consoleFaceZM=4.945000` |
| A6 | at least 0.0200 m | `minM=0.020000/at=prop_fascia_cornice_01_0/to/east_parade_dp1/pairsExamined=85` |
| A7 | 0.0000 mm exactly over 17 | `worst=0.0000mm buildingLineZM=5.1250` |
| A8 | 0 clashes | `clashes=0/of=5168-pairs-examined` |
| A9 | exactly 22, all enclosed | `hits=22/of=612-pairs-examined notEnclosed=0` |
| A10 | reported, not bounded | `worstLostM=0.000000/decalsExamined=4/of=4` |

A0 IS NEW AND IT IS THE ASSUMPTION THE OTHER TEN REST ON: every other check
treats a row's six numbers as its world bounds, which is true only while no
piece is turned. It is asserted rather than assumed.

A10 READS ZERO AND THE ZERO IS REAL: no lettering height is lost, because the
four decals span 2.950 to 3.500 and the cornice begins at 3.500. The test is
containment of a zero-thickness plane in the cornice's z span, not overlap, as
the spec requires.

A6's 0.0200 m IS STILL LABELLED CHOSEN, not cited: no dated figure for a
downpipe bracket stand-off was reachable. The measured minimum equals it over
85 examined pairs.

THE SPEC SAID THESE TEN WOULD DECAY LIKE A COMMENT. They now have a command,
with a selftest whose eight rejecting fixtures all fire: a cornice lifted 1 mm
fails A1 and A3, a console widened to 0.500 m fails A9's enclosure and A6's
clearance, a cornice pushed 50 mm back fails A7, a street stripped of C15 says
"nothing measured" rather than printing clean zeros, and one rotated console
makes A0 refuse by name.

    python3 production/art/fascia-01/verify/measure_placement.py --selftest
    measure_placement selftest: 12 check(s), 0 failure(s)

## 3. The assets themselves: A11 to A15

    python3 tools/ue/import_prop_meshes.py --measure
      fascia_cornice_01  baseY=-0.0750 verts=300 meshes=1 [5.892, 0.15, 0.215]
      fascia_console_01  baseY=-0.2750 verts=296 meshes=1 [0.24, 0.55, 0.18]
      worstMm=0.0000/over=18/tolMm=0.001 verdict=SPEC-BOX-IS-THE-GLB

    python3 tools/ue/import_prop_meshes.py --selftest
      175 check(s), 0 failure(s)        (reads the LIVE spec, so 18 assets now)

    python3 tools/meshgen/meshgen.py --series ledger/Assets/Props/base-mesh
      39 file(s) found, 0 unreadable
      verts: n=39 min=36 median=848 max=4182
      largest dimension (m): n=39 min=0.1 median=1.0011 max=5.892

    python3 production/art/fascia-01/author/make_fascia_mouldings.py --out <tmp>
      authoredPackages=2/2 authoredMeshNodesEach=1 authoredBoxWorstMm=0.0000000
      sha256 of both regenerated files equals the committed bytes

A11 0.0000 mm at tolerance 0.001 over 18 assets. A12 one mesh node each. A13
one material slot, zero images. A14 300 and 296 verts, inside the library's
measured 36 to 4182. A15 byte-identical regeneration, both files.

THE 5.892 m MAXIMUM DIMENSION IN THE LIBRARY IS NOW THE CORNICE. That is the
longest held prop in the repository and it is worth saying out loud rather than
leaving in a series: the previous maximum was about 1 m. Nothing measured here
objects to it, and the engine-side consequence (one 5.892 m actor per bay
rather than six 1 m ones) is a rendering question no container reading can
answer. Card 3.

## 4. Licence

`python3 tools/attribution-check.py` prints `attribution ok`, with
`sweep walked=4980 assetFiles=2801 unclassified=0 ruled=4980/4980 rows=16`.
`ledger/Assets/Props/base-mesh/THIRD-PARTY.md` names both files as LEDGER's own
work in its own section, with the sentence that would make that section false
written down beside it. Nothing was fetched and nothing was purchased.

## 5. Everything else that reads the piece list, measured after the change

Queue 207: a change that replaces a source owes one prediction per consumer.
These are MEASUREMENTS, not predictions, except where marked.

| consumer | reading | command |
|---|---|---|
| CoreTests, whole suite | `All 4315 checks passed` (4310 before) | `dotnet ledger/CoreTests/bin/Release/net8.0/CoreTests.dll` |
| bill of materials | `bom placed=42/42 pieces=610 unplaced=none` | same run |
| held inventory | `onDisk=39 placed=18 excused=21 namedByNothing=none namedButNoFile=none` | same run |
| cross-engine count | `CROSS-ENGINE AHEAD-OF-RUN cb4767e file=610 run=593`, key live | same run |
| probe list | `CROSS-ENGINE agreed file=910 run=cb4767e counted=910`, no key | same run |
| vignette-spec-test | `PASS: 0 of 293 check(s) failed` (275 before) | `./vignette-spec-test production/specs/vignette-pieces.json` |
| frame-stats-test | `108 check(s), 0 failure(s)` | `./frame-stats-test` |
| core-port-test | `2517 check(s), 0 failure(s) over 2498 golden row(s)` | `./core-port-test ue-probe/perception-golden.txt` |
| crime-probe-test | `198 check(s), 0 failure(s)` | `./crime-probe-test content/dialogue/crime-witness-v1.json` |
| docs-check | `179/179 clean under game-design/` | `python3 tools/docs-check.py` |
| attribution-check | `attribution ok`, 0 unclassified of 4980 | `python3 tools/attribution-check.py` |
| run-recipe selftest | `46 passed, 0 failed (of 46 case(s))` | `python3 tools/art-recipes/run-recipe.py --selftest` |
| new recipe selftest | `30 check(s), 0 failure(s)` | `python3 tools/art-recipes/fascia-cornice-elevation.py --selftest` |
| THE ENGINE RUN, PREDICTED | `propMeshesAsked=18/40 propSources=18/18 propImported=18/18 propSaved=18/18 propsAsMesh=39/40 propStandIns=1/40` with `propFallbackWhy` naming ONLY `pavement_sign` | not run: the game lane holds the runner |
| THE BURIAL KEYS, PREDICTED | `propFullyBuried=11/40 propAnyBuried=21/40 propBurialWorst=100.0pct@150.00mm/on=prop_fascia_console_01_0/by=prop_fascia_cornice_01_0/of=40` | measured here by the header's own arithmetic; the run reads its own `GetActorBounds` and nothing is scaled, so it should agree |

## 6. The verdict key that will prove the mesh reached the street

The grate crossed station 4 on `propsAsMesh=22/23`, and `via=loaded-asset`
rather than `via=box-stand-in` is the word that separates a placed reading from
spec arithmetic. The same pair, on the new denominator:

    propsAsMesh=39/40 propStandIns=1/40
    propFallbackWhy names pavement_sign and NOTHING ELSE

39 AND NOT 40, and the missing one is named in advance so a shortfall cannot be
explained after the fact: `pavement_sign`'s source GLB holds three mesh nodes
and the resolver correctly refuses to choose among them. If the reading is
37/40 with the two fascia assets in `propFallbackWhy`, THE MESH DID NOT REACH
THE STREET and this package still counts zero.

The import half is proven separately by `propImported=18/18 propSaved=18/18`,
up from 15/16, because a uasset that never saved cannot be placed.

## 7. What is NOT verified here, stated rather than left to be found

- HOW IT LOOKS. Nothing in this file is a picture. The package's whole argument
  is a shadow line and a scroll silhouette, and no frame of either exists.
  `tools/art-recipes/fascia-cornice-elevation.py` is written, plans six frames
  off this piece list and passes 30 of 30 of its own checks, and HAS NEVER
  RENDERED: Blender is not in this container and the first real run is on the
  Windows runner. That is the open half of station 3.
- COLLISION ON THE NEW MESHES. `propCollisionPrims` is an engine-side reading
  and no run has taken it for these two assets. A mesh with no body setup
  photographs clean and a character walks through it, which is the grate's own
  recorded lesson.
- THE MATERIAL. Both assets are `wood` and carry one untextured slot. Whether
  `wood` on a 0.215 m moulding reads as painted joinery at 3 to 15 m is queue
  176's question and not this package's.
