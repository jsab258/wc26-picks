# DELIVERY: fascia-01, the package to a real mesh in the street, and the first in-house Blender recipe

STATUS: LOG. Written 2026-09-10. Two of Jafar's items, delivered as one piece of
work because the second shapes the first. Governed by `canon.md`, which outranks
this file.

NOTHING WAS COMMITTED AND NOTHING WAS PUSHED, per the brief. Three other agents
are working; `python3 ledger/verify.py` was NOT run, per today's ruling that
verify runs alone (queue 225). Every selftest the change touches was run
directly and its count is below.

## 1. What crossed, and what did not

| station | state | evidence |
|---|---|---|
| 1 SPEC | done 2026-09-09, unchanged today | `01-SPEC-fascia-package.md` |
| 2 AUTHOR | done 2026-09-09, re-verified byte for byte today | `author/make_fascia_mouldings.py`, two GLBs |
| 3 VERIFY | DONE for the arithmetic, OPEN for the picture | `03-VERIFY-fascia-package.md`, written today because the spec cited a file that did not exist |
| 4 INTEGRATE | PREPARED, NOT CROSSED | 17 rows are in the scene spec and the 610-piece list; no engine run, because the game lane holds the runner |
| 5 RECORD | done, counting ZERO | `production/throughput.md`, 2026-W37 row, with the reason beside it |

THE PACKAGE COUNTS ZERO ON THE THROUGHPUT LEDGER and that is correct by the
ledger's own rule. Partial work counts zero. What changed today is that the
reason is now one sentence long and has a named key attached to it, instead of
being the absence of a row.

## 2. The rule 6 hole that is now closed

`ledger/Assets/Props/base-mesh/fascia_cornice_01.glb` and `fascia_console_01.glb`
were committed on 2026-09-09 and NAMED BY NOTHING. Measured, not recalled:

    glb files on disk: 39
    placed assets: 16   not_placed assets: 21   named total: 37
    on disk but NOT named anywhere: ['fascia_console_01', 'fascia_cornice_01']

They are now named by `C15_fascia_cornice_console` in
`production/specs/vignette-bill-of-materials.json` and placed by 17 rows in
`production/specs/vignette-scene.json`, and the guard that could not see them
has been repaired so that this state fails a test rather than sitting in the
tree for a week. Section 4.

## 3. Queue 228, answered by measurement, with the geometry unmoved

    consoleUnderCornicePairs=11 consoleRestingOnCornice=11/of=11
    consolePenetrationWorstMm=0.000000 consoleOverlapVolWorstM3=0.00000000
    consoleInsideCornice=NO

THE CONSOLE IS NOT INSIDE ITS CORNICE. The two share exactly one plane,
y = 3.500000; the AABB intersection volume is exactly zero; the console's y span
is OUTSIDE the cornice's. The `100.0pct@150.00mm` the gate reports is the
cornice's own height (two brick courses at the scene file's own 0.075) standing
above a bracket whose top IS its soffit. The predicate `C.MinY <= P.MaxY` is
half-open and fires on a coincident face at zero penetration.

THREE INDEPENDENTLY CORRECT FACTS MAKE THE GEOMETRY UNMOVABLE: the cornice
soffit is the fascia band top (A1, 0.0000 mm over 6), the console spans the band
(A2, 0.0000 mm over 11), therefore the console top is the cornice soffit (A3,
0.0000 mm over 11 of 11). Clearing the reading would mean lifting a cornice off
the band it protects or dropping a bracket below the thing it carries.

AND THE SAME MISSING HALF HIDES A REAL FAULT, which is why this is not special
pleading for my own rows: the two existing awnings read `coverAbMm=0.00` at the
gate and `penetrMm=370.00` and `penetrMm=810.00` here, with 0.036 and 0.048
cubic metres of real overlap into a toplight and a door spandrel. A 0.00 mm that
means 810 mm is the same instrument gap reading the other way. Full table in
`03-VERIFY` section 1.

RECOMMENDED DISPOSITION OF QUEUE 228: close the geometry question with this
measurement, and re-point the item at the instrument as card 1. Its acceptance
("`propFullyBuried` back to its pre-fascia count") cannot be met without either
moving correct geometry or changing a predicate, and which of those is right is
not the art lane's to decide.

RULED 2026-09-10, and the recommendation above is upheld. Section 6 and
amendment 4 of
`game-design/decision-2026-09-10-ruling-the-four-lane-batch.md`: the fourth
CONTACT bucket is GRANTED, card 1 is upheld, and `propFullyBuried=11/40` is
RETIRED as a standalone key. Amendment 4's note, verbatim, which the replacement
key ships with:

Bucket set changed 2026-09-10: SUNK / CONTACT / CLEAR / NO-DATUM. The
previous propFullyBuried=11/40 counted resting-on and sunk-into together
because the predicate was half-open and fired on a coincident face. The new
split is a RECLASSIFICATION, not a regression; the two awnings at 370 mm and
810 mm of real penetration stay in SUNK and the gate stays red on them.

THE REPLACEMENT IS NOT IN THE EMIT ON THIS COMMIT. `VignetteSpec.h` still
prints `propFullyBuried` at line 1828 and the predicate at line 1089 is
unchanged. The five conditions section 6 attaches to the replacement are carried
in `production/queue/228-the-fascia-props-are-buried-in-each-other.md` under
ANSWERED 2026-09-10, with the penetration series the tolerance must be read off.
Until the split lands, every `propFullyBuried` reading in this file and in
03-VERIFY is two buckets added together.

## 4. The pinned literals, and which was which

The brief warned that adding props moves a number CoreTests asserts, and
forbade editing a test to fit a diff. FOUR literals moved. Every one was a
PINNED COPY OF DATA, none was a real invariant, and each repair reads the
number and is strictly stronger than what it replaced.

| where | was | now | why it is stronger |
|---|---|---|---|
| `ledger/CoreTests/Program.cs` | `assets.Count == 16`, comment saying 37 props held | four derived checks | `== 16` cannot see a SUBSTITUTION (swap one asset for another and 16 holds) and could not see two files named by nothing; its own denominator was stale at 39 |
| `tools/art-recipes/run-recipe.py` | `piecesPlanned=593/593-read` and `piecesSkipped=0/593-read` | the relation, plus the denominator read INDEPENDENTLY from the spec file | a self-consistent pair alone would miss a recipe reading 606 of 610 and reporting 606/606, so the spec's own count is read separately |
| `tools/art-recipes/run-recipe.py` | `meshAssetsFound=16/16-named` | found equals named, and both above zero | holds as the street grows; the literal had to be re-typed, and every re-typing can widen a guard by accident |
| `ue-probe/tests/vignette-spec-test.cpp` | `propFootprintsRead=23/23` | built from the live spec's mesh-piece count, plus a separate refusal of a zero population | its own message says the assertion is a RELATION (examined over asked), not a count; `0/0` satisfies the equality and means nothing was measured, so that is refused by name |

THE CEILING THE OLD LITERAL STOOD FOR IS NOW EXPLICIT AND BETTER. The
CoreTests guard existed to stop the scene placing every held prop to make a
number go up. That ceiling is now: every prop NOT placed carries a written
reason, and placed plus excused IS the directory. Placing one more prop now
means deleting a sentence that says why it was held back, which is a reviewable
act; bumping a literal by one character was not.

    held inventory: placed=18/18 asked excused=21 placedNotAsked=none askedNotPlaced=none
    held inventory: onDisk=39 placed=18 excused=21 namedByNothing=none namedButNoFile=none
    bom placed=42/42 pieces=610 unplaced=none

EVERY REPAIRED GUARD WAS TESTED ON THE CASE IT MUST CATCH, not only the case it
must pass. Eight planted cases against the recipe runner's three checks, an
off-by-one build of the probe test that FAILS naming `39/40` against the
segment's `40/40`, a spec stripped of mesh rows that fires the new zero
refusal, and eight rejecting fixtures in the placement selftest.

## 5. A FIFTH trap, found by this change and repaired in the writer not the gate

`--ahead-of-run` writes one declaration into TWO spec files. The fascia package
moves the piece count by 17 and the PROBE count by nothing at all, because a
prop fixed to a frontage has no foot on the ground and is not foot-probed,
exactly like the two awnings. So pieces went 593 to 610 against a run at 593 (a
live gap) while probes stayed at 910 against a run that counted 910 (no gap),
and the writer stamped a key into the probe list claiming it was ahead of a run
it agreed with. CoreTests refused that key as SPENT and was right to.

THE GUARD IS UNTOUCHED. The writer now asks each file its own question:

    ahead-of-run cb4767e piecesGap=17/file=610/run=593 feetGap=0/file=910/run=910
      keyWrittenInto=pieces/- rule=a-key-describes-a-live-gap-or-it-is-not-written

## 6. The second item: the first in-house Blender recipe

`tools/art-recipes/fascia-cornice-elevation.py`. WRITTEN FROM THIS PROJECT'S OWN
SPECS. No existing recipe was opened to see how it phrased anything; the only
file read for interface was `run-recipe.py`, which is the runner and not a
recipe, and what it supplied was a contract: a name, an import with no side
effects, a `main(argv)` taking `--dry-run --root`, and the
`blender --background --factory-startup --python <recipe> -- --out DIR` line.

WHAT IT IS FOR. The package's entire justification is a shape, and no frame of
it exists. It renders the three views in which the claim is falsifiable, with
every number derived from the piece list:

    shot=terrace_raking   eyeXYZm=4.000/1.672/4.000 yawDeg=0.00  pitchDeg=4.00  fovVDeg=60.0
      poseFrom=the-spec-files-own-cam_A-verbatim
    shot=console_scroll   eyeXYZm=2.175/3.225/3.035 yawDeg=63.43 pitchDeg=0.00  fovVDeg=39.0
      subject=prop_fascia_console_01_0 poseFrom=derived/aim-computed
    shot=drip_soffit      eyeXYZm=5.400/1.600/4.010 yawDeg=56.31 pitchDeg=60.35 fovVDeg=50.0
      subject=prop_fascia_cornice_01_0 poseFrom=derived/aimed-at-the-cornices-own-soffit-outer-arris

Shot 1 is the file's own `cam_A`, unchanged, because the street is judged from
that camera. Shots 2 and 3 are computed by `aim_at` from the geometry under
review, so no angle in the file is a number a reader cannot re-derive.

IT INVENTS NO GEOMETRY, which is D14. Every object is a box, cylinder or quad
built from one row of `vignette-pieces.json`, or a GLB imported and never
scaled with its own bounds centre on the row's centre. A piece it cannot draw is
REFUSED BY NAME and counted; a missing GLB is never replaced with a box, because
a box standing in for a moulding is the exact failure the preview exists to
catch.

    windowPieces=199/of=610 bomLinesDrawn=13/of=42
    windowShapes=box:170/cyl:6/decal:4/mesh:19 refusedPieces=0/of=199 none
    meshAssetsAsked=3 glbFound=3/of=3 glbMissing=none
    shots=3 conditions=2 framesPlanned=6 renderPx=1600x900 samples=96

TWO CONDITIONS, BOTH READ FROM THE FILE BY NAME. `overcast_day` (sun 3, sky
1.00) is the SHIPPING condition canon fixes, under which the cornice throws no
hard sun shadow at all and what it buys is occlusion and a dry strip.
`grid_sky035_sun030` (sun 30, sky 0.35) is the file's hardest grid cell and is
labelled a DIAGNOSTIC and not a target look, because a mis-shaped moulding hides
under a dome and cannot hide under a raking light.

IT HAS NEVER RENDERED. Blender is not on PATH here and `bpy` does not import,
checked rather than assumed. `--selftest` is 30 checks, 0 failures, accepting
cases on the live street first and then six synthetic rejections. The render
path is UNCOVERED and the first real run is on the Windows runner. Card 2.

## 7. Files

WRITTEN OR CHANGED BY ME. `git status --porcelain` is in my report; nothing on
the forbidden list was touched: not `production/d1-probe/DISPATCH`, nothing
under `.github/workflows/`, not `production/next-three.json`, not the material
generator, not `CLAUDE.md`, `.claude/rules/` or `ledger-v2/studio-v2/`, and
nothing under `tools/imagegen/`, `production/art/atlas-02/` or
`production/art/compare/`.

    production/art/fascia-01/03-VERIFY-fascia-package.md          NEW
    production/art/fascia-01/DELIVERY.md                          NEW (this file)
    production/art/fascia-01/verify/fascia_contact_measure.cpp     NEW  the queue-228 measurement
    production/art/fascia-01/verify/measure_placement.py           NEW  A0..A10, re-runnable
    tools/art-recipes/fascia-cornice-elevation.py                  NEW  the in-house recipe
    tools/art-recipes/run-recipe.py                                three literals read the data now
    production/specs/vignette-scene.json                           17 rows, and the count sentence
    production/specs/vignette-bill-of-materials.json               C15 line, coverage 38 of 39
    production/specs/vignette-pieces.json                          regenerated, 610, ahead-of-run key
    production/specs/vignette-feet.json                            regenerated, 910, NO key
    ledger/CoreTests/Program.cs                                    the literal repaired, C15 authorised,
                                                                   the ahead-of-run writer, a Tally helper
    ue-probe/tests/vignette-spec-test.cpp                          one literal reads the count
    ledger/Assets/Props/base-mesh/THIRD-PARTY.md                   one em-dash corrected
    production/throughput.md                                       the 2026-W37 row, counting ZERO

## 8. What is still open, in the order it matters

1. THE ENGINE RUN. `propsAsMesh=39/40` with `propFallbackWhy` naming only
   `pavement_sign`. Until that lands this package counts zero.
2. A PICTURE OF ANY OF IT. The recipe needs one Blender run on the Windows
   runner. Six PNGs, and the runner counts them itself.
3. COLLISION on the two new assets, which no container reading can take.
4. The instrument half of queue 228, card 1.
