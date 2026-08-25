> **STATUS — LOG, 2026-08-25. NOT CURRENT** once the call site lands.
> Builder report. The code is on disk and uncommitted; the one line that
> makes it run is NOT applied — see "The call site the director owes it".
> Supersede or delete when the placement lands and a verdict shows it.

# Street clutter — what landed, what did not, and one reversed verdict

## The file

`ledger/Assets/Scripts/Game/StreetDressing.cs`, 555 lines, new.
Declared type: **`public static class StreetDressing`** in `namespace
Ledger.Game` — chosen to MATCH the filename deliberately, because
`tools/lint-filetype.py` takes trap names off filename stems and fourteen
Game-layer files declare no type of their own name. This one does.

Public entry point: **`StreetDressing.Build()`** — takes nothing, returns
nothing, guards on `WorldBuilder.TownPlanEnabled`, parents everything it
makes under one `StreetDressing` GameObject.

Three placements, in the order the resume brief set:

1. **`planter`** — `city_kit_suburban_planter`, normalised to its measured
   1.31m height. Two per long driveable edge in Copper Row and the
   Exchange, at the thirds, one side chosen by hash, centred 1.3m out from
   the kerb (measured: that puts a 2.22m-deep tub at 0.19..2.41m of a 2.6m
   `BlockSetback` pavement).
2. **`yard_fence`** — `fence` / `fence_1x2` / `fence_1x3` / `fence_1x4`,
   variants `1x1`..`1x4`, all normalised to 2.00m. One run per tile of each
   block's yard centre line, along the block's long axis, model chosen by
   the PROBED yard depth.
3. **`works_cluster`** + `works_cone` / `works_barrier` / `works_lamp` —
   a coned taper, a barrier line across the shut lane in alternating red
   and white, and one or two works lamps carrying a real amber point light.

Everything goes through `AssetLibrary.TryInstantiateProp`, is normalised by
its own MEASURED world-bounds height (`MakeLamp`'s pattern — the FBX are
~0.074 m/unit and the import scale is unknown in this container, so one
uniform factor off the height is the only honest way to get 12.40m of fence
to be 12.40m), seated on its measured `bounds.min.y`, repainted through
`WorldBuilder.TintFurniture` so the family lands in `kitAlbedo` with a
painter's name, and stripped of colliders.

**No fallback primitives, deliberately.** Every sibling placer falls through
to a tinted box. That is exactly what makes a miss invisible — a grey box at
the right size reads as dressing from ten metres, which is how
`city_kit_*_bench` missed for a week. A miss here draws nothing and files
`Missed`.

## The instrument

**There is exactly one `KitDressing` instance in the project.** Verified:

    $ grep -rn "new Ledger.Core.KitDressing()\|new KitDressing()" ledger/Assets/Scripts/
    ledger/Assets/Scripts/Game/WorldBuilder.cs:3492:            new Ledger.Core.KitDressing();

    $ grep -rl "KitTally" ledger/Assets/Scripts/
    WorldBuilder.cs  SimDirector.cs  TrafficHost.cs  StreetDressing.cs

`StreetDressing` files into `WorldBuilder.KitTally`, which is what
`SimDirector.cs:16058` prints. **The first draft of this file declared its
own instance**, which would have printed a populated `kitDressing=` carrying
the lamp path's real numbers while every family here read `nothing-offered`
— the deliberate signal that no call was ever made. A verdict stating
confidently that a running pass never ran is worse than a missing number;
the class note in the file records it so it cannot be re-derived.

20 filing sites. `Offered` at every site, exactly one of `Placed`/`Missed`
at every outcome (`Stand` files both itself, including the prefab-loads-but-
has-no-renderer case), `Measured` per placed run, `Flagged` for the refusals.

Families filed: `planter`, `yard_fence` (variants `1x1`..`1x4`),
`works_cluster`, `works_cone`, `works_barrier`, `works_lamp` (flag
`KitDressing.FlagLit`).

Refusal flags — the difference between `Offered` and placed+missed, named
rather than left as a gap: `planter/in_road`, `planter/no_room`,
`yard_fence/in_terrace`, `works_cone/off_road`, `works_barrier/off_road`.

### The done-line fragment these calls will produce

Inside the existing `kitDressing=` value (`KitDressing.Line()`), the keys
this pass moves:

    kitPlaced=<p>/<o>/<m>
    kitFamilies=<placed>/<named>/11/<n>unknown
    kitBy=[...,works_cluster:<p>/<o>/<m>,works_cone:...,works_barrier:...,
           works_lamp:...,planter:...,yard_fence:...]
    kitByVariant=[...,yard_fence/1x1:<p>/<m>,yard_fence/1x2:...,
                  yard_fence/1x3:...,yard_fence/1x4:...]
    kitAmounts=[planter:<m2>/<n>/0bad,yard_fence:<metres>/<n>/0bad]
    kitFlagsBy=[planter/in_road:<n>,works_cone/off_road:<n>,
                works_lamp/lit:<n>,yard_fence/in_terrace:<n>]/n<total>
    worksClusters=<p>/<o>   worksProps=<p>/<o>
    worksLampsLit=<lit>/<placed>
    yardFenceRuns=<p>/<o>   yardFenceMetres=<sum>/<n>/0bad
    plantersPlaced=<p>/<o>

`signPosts`, `signPlates`, `namePlatesPainted` and `sign_*` rows of `kitBy`
will read `nothing-offered` — correctly, because signage is not built (see
below).

## The call site the director owes it

**File:** `/home/user/wc26-picks/ledger/Assets/Scripts/Game/WorldBuilder.cs`
**Insert after line 319**, i.e. between `StreetFurniture.Build();` and the
`// And the parked cars after even the signs:` comment. Context as the file
stands at `e8c5949` (another builder is editing this file this turn; the
anchor is the `StreetFurniture.Build();` line inside `BuildBlock`, not the
number):

    317            // Signs last: they read the finished network, and a rule the city
    318            // obeys without telling you is indistinguishable from a bug.
    319            StreetFurniture.Build();
    -->            StreetDressing.Build();
    320            // And the parked cars after even the signs: they append to
    321            // `Masses`, and everything that reads Masses as BUILDING specs

The exact line, at the same indent (12 spaces):

            StreetDressing.Build();

**Why there.** It must run after `BuildBuildings`/`BuildDistrict`, because
every site is found by PROBING the built masses (`WorldBuilder.PointClear`)
rather than by recomputing where they were meant to go. It must run before
`BuildParkedCars`, which appends to `Masses` — a parked car is an obstacle,
not a building, and the yard probe reads `Masses` as buildings. Placing it
immediately after `StreetFurniture.Build()` satisfies both and keeps the
whole dressing phase together.

A one-line comment the director may want above it:

            // And the two city kits' clutter: planters, yard boundaries,
            // roadworks. Same phase and same rolls as the furniture above.

## Verification 1 — the warning triangle. IT IS NOT A TRIANGLE.

The survey asked: does `road-sign-object-warning` point UP (British) or DOWN
(US yield)? Bounds cannot tell, and it refused to guess. **Measured from the
mesh, and the answer is neither.**

Method: `tools/prop-dimensions.py`'s own FBX reader, assembled vertices in
the placed frame (`Model` translations applied), then the plate's outline
read directly — 36 control points, so the corners ARE the outline.

`road-sign-object-warning`, plate face at local x = -3.969 (thickness runs
x -3.969..0.031; the bracket is the x 0.015..3.765 box behind it). Outline
in (y, z):

    (-6.013, ±0.764)   (-0.756, ±6.021)   (+0.772, ±6.021)   (+6.029, ±0.764)

Narrow at the top, narrow at the bottom, widest across the middle, and
**symmetric**: apex midpoint (-6.013+6.029)/2 = 0.008, widest-band midpoint
(-0.756+0.772)/2 = 0.008. A triangle cannot be symmetric top-to-bottom.
This is a **DIAMOND on a corner with truncated corners** — the American
MUTCD warning sign, which is further from a British warning triangle than a
down-pointing triangle would have been.

`road-sign-warning` (the same plate on its own 3.7m post) is the identical
shape: apexes at y 35.873 and 49.120 (z ±0.840), widest at y 41.657..43.337
(z ±6.623), midpoints 42.4965 and 42.497. Symmetric to four figures.

Control: `road-sign-object-stop` reads as a true regular octagon
((±5.654, ±2.342) and (±2.342, ±5.654)), which is what it should be — so the
method distinguishes shapes rather than flattening everything.

**Consequence, and it reverses one survey verdict.**

- `road-sign-object-warning` — the plate is separate from any post, so it
  CAN be rolled 45° about its own face normal (`Quaternion.Euler(45, yaw, 0)`
  — Unity's ZXY order applies the roll in the plate's own plane first, then
  aims it), which turns the diamond into a square information plate. That is
  country-neutral and a real British form. **Still PLACE, with a roll.**
- `road-sign-warning` — the diamond is welded to its post. Rolling the object
  tips the post over, and the plate cannot be corrected without editing the
  mesh. **REJECT**, on exactly the grounds the survey used to reject the STOP
  octagon and the crossblade nameplate. Its survey row should be changed from
  PLACE to REJECT.

**This is a measurement, not a look at a frame.** Nothing here is
UNVERIFIED-IN-FRAME. The script is at
`/tmp/claude-0/-home-user-wc26-picks/b9cd91ae-0774-5237-89a0-83f5e9373b08/scratchpad/dump.py`
(scratchpad, not committed); it is ~40 lines over `prop-dimensions.py`'s
reader and is worth promoting to `tools/prop-outline.py` if anybody is going
to judge another plate shape from bounds again.

## Verification 2 — do the plates letter? NOT APPLICABLE THIS TURN, and one thing found

Signage is not built (below), so nothing renders blank. What was found while
looking for the lettering path, for whoever builds it:

- **`ShopNamesPainted` is a COUNTER, not a path.** `WorldBuilder.cs:2192`
  declares it and `:1745` increments it. The actual lettering mechanism is
  ~20 lines inline at `WorldBuilder.cs:1725-1746`: a bare `GameObject`, a
  `TextMesh` at `characterSize 0.062`, `WorldText.Adopt(tm)` for the
  back-face cull, aimed by
  `float yaw = Mathf.Atan2(-outward.x, -outward.z) * Mathf.Rad2Deg` (local
  -z is the reading direction). `StreetFurniture.Label` (`:502`) is the
  same idiom again, private, double-sided. **One idea, two implementations,
  neither reusable from a third file.** Any signage work needs a third copy
  or a promotion of `StreetFurniture.Label` to internal.
- **`road-sign-empty-hanging` has NO PLATE.** The survey calls it "post with
  overhanging arm and a blank hanging plate". Measured: post y 0..47.5u, a
  collar at y 41.5..46, and an ARM at y 42.5..45, z -1.25..-25.0, x ±1.25 —
  a 1.76m x 0.185m x 0.185m beam. There is nothing at the far end. It is a
  mast arm; the hanging board has to be built (a Cube + `Label`, which is
  actually better: a real pub sign board rather than a blank kit plate).
- **Character size is derivable, not guessable.** The fascia fits ~20-char
  shop names on a ~2.4m board at `characterSize 0.062`, so the char advance
  is ~1.94 x characterSize. A 1.42m nameplate blade with an 18-char street
  name ("Morning After Lane") wants `characterSize <= 0.037`. Worth writing
  into whatever builds the blades, because an overhanging name is the
  "blank white blade" fault wearing different clothes.

## What I did NOT do — say it plainly

**SIGNAGE IS NOT BUILT.** Five of the survey's PLACE verdicts —
`road-sign-empty`, `road-sign-empty-hanging`, `road-sign-object-street`,
`road-sign-object-warning`, `road-sign-warning` — have no code. The turn ran
out of budget on the first attempt (fifty-nine tool calls into reading
`WorldBuilder.cs` and `StreetMap.cs` with nothing on disk), and the resume
brief ordered the scope narrowed to planters, fences and roadworks with
signage dropped without apology if the budget was thin. It was.

This is visible rather than silent: `KitDressing`'s catalogue names
`sign_post`, `sign_plate_name` and `sign_plate_warning`, so `kitBy` prints
`sign_post:nothing-offered` every run until somebody wires them, and
`signPosts` / `signPlates` / `namePlatesPainted` all print
`nothing-offered`. The design work above (sites, densities against a
measured junction census, the 45° roll, the mast-arm finding, the character
size) is done and written down; only the code is missing.

Also not done, named rather than left implied:

- **`fence_2x2` / `2x3` / `3x2` / `3x3` remain HOLD** — but their named
  dependency is now DISCHARGED, see below. Somebody should take the decision.
- **Works lamps do not switch off by day.** `WorldBuilder.Lamps` is private
  and `SetLampsEnabled` walks only that list; `RegisterNightLight` takes a
  `Renderer`, not a `Light`. The lamp burns continuously (defensible — a
  live works site does) at 0.95/6m, which under a noon sun is a faint warm
  pool at the barrier's foot. Queue item named in the file:
  **`worldbuilder-night-light-registry`** — a public
  `RegisterNightLamp(Light)` and one line in `SetLampsEnabled`'s sweep.
- **`Label`/fascia-text duplication** — queue item
  **`label-helper-unify`**.
- **`kitAlbedo` truncates at 24 keys**, which the survey already flagged.
  This pass adds up to 6 more `city_kit_*` keys behind that cap. Not
  touched (it lives in `AssetLibrary`/`SimDirector`, both owned elsewhere
  this turn).

## Two measurements worth keeping, both discharging open questions

**1. The street census, printed rather than assumed.** `Core/StreetMap.cs`
compiled standalone with `HookMap.cs` (scratchpad `mapprobe`, `dotnet run`):

    junctions        97
    driveable edges  154, of which 112 are >= 30m
    blocks           52
    block width      35.0 / 47.9 / 65.1   (min / median / max)
    block depth      15.0 / 21.9 / 31.1
    named streets    52
    driveable edges by district — Hook 48, Copper Row 23, Ironside 18,
      the Exchange 18, the Parade 23, Fairview 12, Gullwing 12

Every density constant in the new file is a probability against that census
with the product written into its comment (roadworks 0.18 on Copper
Row/Ironside long edges + 0.04 elsewhere ~ 8.8 clusters against the survey's
6-10; planters 0.50 over 41 Copper Row + Exchange edges ~ 20 against 15-25).
None of them is a feel.

**2. `fence-1x2`, `-1x3` and `-1x4` ARE NOT STRAIGHT RUNS.** The survey
calls them straight and derives "the 12.40m run is one per terrace back plot
at our 12m parcel depth — a measured fit rather than a coincidence" from it.
Their own bounds contradict it: all three are 43.75u (3.24m) DEEP, which no
straight panel is (the single `fence` is 0.56m). The vertex footprint shows
why — each is a **U**: a long back run of posts and panels along x, plus a
2.96m RETURN panel at each end running in z.

    fence      x -23.75..23.75  z  -3.75..3.75   straight, 3.52m
    fence-1x2  x -43.75..43.75  z -20.00..23.75  U, 6.47m back + 2.96m returns
    fence-1x3  x -63.75..63.75  z -20.00..23.75  U, 9.44m back + 2.96m returns
    fence-1x4  x -83.75..83.75  z -20.00..23.75  U, 12.40m back + 2.96m returns

That makes the U the BETTER object — three sides of a terrace back yard is
what it is — but it needs 2.96m of yard to stand in.

**And the yard depth, which is the four HOLDs' named dependency.**
`TerraceBlock` caps each row at `(blockDepth - 3) / 2`, so against the block
census above:

    Copper Row     depth 15.0  ->  yard 3.0m
    the Parade     depth 17.3  ->  yard 3.0m
    the Hook       depth 21.9  ->  yard 3.0-3.9m
    the Exchange   depth 26.5  ->  yard 3.0m   (offices, 12-15m rows)
    Fairview       depth 26.5  ->  yard 6.5-10.5m
    Gullwing       depth 28.8  ->  yard 6.8-10.8m
    Ironside       depth 31.1  ->  yard 7.1-13.1m

So: **four districts have a 3m back ALLEY (straight panel is the right
object) and three have a real YARD (the U drops in).** That answers
`fence-2x2`'s HOLD directly — "if our yards are ~6m the L drops straight in"
— for Fairview, Gullwing and Ironside, and refuses it for the other four.

**The code does not hardcode any of that.** It PROBES the built masses every
run (`YardOf`/`BackOfRow` walk inward from each block face until the terrace
row goes solid and then clear again) and returns false when a face has no
terrace at all. The arithmetic above is a reading of `TerraceBlock`; the
buildings are the thing that is actually there. Eight blocks once hung over
open sea because a placement measured its distance to a datum without asking
whether the datum existed under the footprint — so the placement here ships
in two halves: where the line goes, and whether there is a yard under it.

## What I ran locally

`python3 ledger/verify.py`, footer read from `ledger/.verify-footer` on
disk:

`python3 ledger/verify.py` — **exit 1, NOT GREEN, and
`ledger/.verify-footer` DOES NOT EXIST ON DISK**, which is correct: a red
run deletes it. So there is no footer to paste and this section says so
rather than quoting a green one from scrollback.

**The one red gate is `director_cadence`, and it is red BY DESIGN for
builder work awaiting review** — it is not a fault in this code:

    DIRECTOR NOT SPAWNED: 1792 changed line(s) (496 tracked + 1296 untracked
    in 2 new file(s)) vs 100 threshold under Assets/Scripts, 0 director
    row(s) newer than the reference ... — spawn studio-director for the
    batch review, then re-run verify

The two new files are `Core/KitDressing.cs` (the other builder's) and
`Game/StreetDressing.cs` (mine). Spawning the director is the director's
step, not a builder's.

**Every technical check passed**, from the same run:

    0 lint errors
    0 shape errors (189 files, 3 with conditional code)
    0 shadowed Core types
    0 nested-type errors (253 Core types)
    0 static/instance errors (75 members, 555 bodies)
    0 filename-as-type errors (189 files, 13 filenames that are not types)
    0 namespace-as-value errors (189 files, 4 segments in scope)
    0 raw avenue reads (183 files)
    Game layer compiles (183 files)
    3976 CoreTests
    docs 91/91 clean, 27 queue items ready, 0 stale anchors

**And `gamecheck` was run on its own to confirm the new file is inside that
compile** — 183 `.cs` files exist under `ledger/Assets/Scripts` and
`StreetDressing.cs` is one of them, and gamecheck reports exactly 183:

    $ python3 tools/gamecheck.py
    gamecheck: Game layer compiles — 183 files, 1 known reference-assembly gap(s)

    $ find ledger/Assets/Scripts -name '*.cs' | wc -l
    183

That is stronger than a ShapeCheck green — ShapeCheck is
reference-independent and blind to anything needing a name resolved, which
is the family that has cost this project five round trips. It is still not
sufficient: a type error against a Unity API only shows in the Windows
build.

Also run: `grep -rn "new Ledger.Core.KitDressing()\|new KitDressing()"
ledger/Assets/Scripts/` (one hit, `WorldBuilder.cs:3492`) and
`grep -rn "city_kit_suburban\|construction_cone\|construction_barrier\|
construction_light\|StreetDressing" ledger/Assets/Scripts/` excluding the
new file (zero hits — no twin placer for any key this file adds).

## Not committed

Working tree left dirty on purpose. New file:
`ledger/Assets/Scripts/Game/StreetDressing.cs`. This report:
`game-design/agent-reports/street-clutter.md`. Nothing else in the tree is
mine — `WorldBuilder.cs`, `TrafficHost.cs`, `SimDirector.cs`,
`CoreTests/Program.cs` and `Core/KitDressing.cs` were modified by the other
two builders this turn.
