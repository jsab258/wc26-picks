# GroundGrade, tourBlockerShare, ironside re-site — builder account

LOG — 25 Aug 2026. NOT CURRENT after the next landing.
Builder report (systems-builder). Nothing committed; the tree is left
dirty for director review. Every claim below was checked against the
source or against a landed file in this session.

---

## 0. WHAT WAS VERIFIED BEFORE ANY EDIT

The decision record's code claims, checked rather than quoted:

* `AssetLibrary.cs` `TextureGrade = (0.74, 0.76, 0.80)` — confirmed, and it
  is the base colour for EVERY textured surface, not just the ground.
* `LightModel.AlbedoScale` is `Clamp(1 - 0.45*rain, 0.55, 1.0)` — confirmed,
  and it has exactly ONE caller in the whole repository, `SetWetness`.
* `SetWetness` walks `WetSurfaces = { Asphalt, Sidewalk, Kerb, Concrete }` —
  confirmed.
* **One correction to the record.** It says `SetWetness` "walks the named
  `WetSurfaces` set" as though that were one loop. It is TWO: the shared
  materials, and a second loop over `_gradedWet`, the graded copies
  registered by `MaterialGraded`. Counting `BuildMaterial` and
  `MaterialGraded`'s own dry copy, **four** sites compute a ground base
  colour, not one. A grade applied at three of them is this project's
  standing failure shape, so all four now route through one function.

---

## 1. `GroundGrade` 0.55, ground family only

`ledger/Assets/Scripts/Game/AssetLibrary.cs:522` — the constant.
`AssetLibrary.cs:535` — `BaseColour(logical, textured)`, the one function
that folds it in, for `WetSurfaces` members and nothing else.

**Call sites, all four, wired:**

    AssetLibrary.cs:321   MaterialGraded   var dry = BaseColour(logical, baseMat.mainTexture != null);
    AssetLibrary.cs:572   BuildMaterial    mat.color = BaseColour(logical, tex != null);
    AssetLibrary.cs:826   SetWetness       var baseCol = BaseColour(name, mat.mainTexture != null);
    AssetLibrary.cs:840   SetWetness/_gradedWet   var baseCol = BaseColour(name, mat.mainTexture != null);

After the change `TextureGrade` is READ in exactly one place — line 537,
inside `BaseColour` — so there is no second implementation left to drift.

`TextureGrade` itself is unchanged at `AssetLibrary.cs:451`.

**Why `BuildMaterial` is included and not only `SetWetness`.** The decision
said "folded into the same assignments `SetWetness` already writes". Doing
only that would leave a road white until the weather first moved:
`SetWetness` early-returns when the requested wetness equals `_wetness`, and
a material built after the last call keeps `BuildMaterial`'s colour. The
grade belongs on the DRY base, which is what `BaseColour` is.

**The derivation is in the comment** (`AssetLibrary.cs:461-521`), stated as
what it is: 0.55 is not a new number, it is `AlbedoScale`'s own floor — the
multiplier `review_day1_noon` (wet 1.00) ran at, and one step below the
0.595 the whole rain era ran at. It also records honestly that
`review_day1_noon`'s ground/frame is 1.00, the TOP edge of the reference
band and not its middle, so nobody reads this as a mid-band derivation.

**ITERATION 3** is on `TextureGrade`'s own comment at `AssetLibrary.cs:424`,
with iteration 2's stated failure criterion and today's dry numbers side by
side (day5_noon 0.496/40.46, fairview 0.516/41.61, gullwing 0.537/44.94,
ironside 0.608/54.31, from run 6137608's `frames.tsv`) — four frames inside
or above the band that was declared the failure state, which is the evidence
that iterations 1-2 were judged through a rain mask.

**`groundOverFrame` is NOT mine** and the comment says so: it is
`tools/ref-bench.py`'s, band 0.41-0.97 recomputed per run, ours today
1.23-1.38 sunlit. Checked in this session: `ref-bench.py` already contains
`groundOverFrame` (definition at line 441, computation at 758), the file is
modified in the working tree by the other builder, and I did not touch it.

**One consequence named rather than hidden.** `WetSurfaces` contains
`Concrete`, and `mat_concrete` is one shared material — pavement AND the
skyline masses and town walls made of it. Those darken by 0.55 too. Measured
contamination of the "facades are the control group" claim: 4% of the noon
facade sample (`noonFacadeOf` = brick 95%, concrete_b 2%, concrete 2%). It
is also not new behaviour — every rainy frame this game has shipped already
drove that same material to this same 0.55. If a still shows concrete WALLS
too dark, the fix is to split the ground family out of `WetSurfaces`, not to
move the constant.

---

## 2. `tourBlockerShare` — the identity the distance bands throw away

`SimDirector.cs:9768` — `BlockerReachM = 8f`, declared NOT MEASURED with
what it does rest on: the one obstruction in the set is 3.95m by the world's
own coordinates, and the existing mid band stops looking at 7m, so 8m counts
a straddling object whole instead of splitting it between two instruments.
It ships the printer that will set it properly — every entry carries the
winning collider's distance.

`SimDirector.cs:9990` — the kept fields, with the evidence for why a new
number was needed rather than a bound on `midFrac`.

**Call sites:**

    SimDirector.cs:9872-9900   ShotSightlines — per-ray nearest non-player COLLIDER,
                               tallied into owned/ownedAt inside BlockerReachM
    SimDirector.cs:10751       tour branch — one formatted row per district,
                               same instant, same camera as tourNearSeries
    SimDirector.cs:10782       non-tour branch — series + peak with name and
                               distance captured in the SAME assignment
    SimDirector.cs:14760       done line — tourBlockerShare / tourBlockerHits /
                               tourBlockerReach
    SimDirector.cs:14769       done line — shotBlockerShareWorst / ...At /
                               ...Median / ...Shots

**Keys added (7):**

    tourBlockerShare=[district_hook:0.00@-/clear/...]   per district, share@dist/collider
    tourBlockerHits=<rays hit inside reach>/<rays cast>  the denominator, 7 x 84
    tourBlockerReach=8.0                                 the bound, printed with the reading
    shotBlockerShareWorst=0.00                           peak over non-tour shots
    shotBlockerShareAt=[<collider>@<m> in <shot>]        the peak's own object and frame
    shotBlockerShareMedian=0.00                          is that the camera's normal state
    shotBlockerShareShots=0                              denominator for both of the above

It is a MAX OVER OBJECTS, and that is the whole point: `tourDepthBy` is a
median over the same 84 rays and ranked the blocked camera as the CLEAREST
in the set at 32.7m, because 63 rays sailed past the crane and the median
followed them. `midFrac` saw it correctly at 0.25 and cannot distinguish one
crane owning 21 rays from 21 rays clipping 21 different walls — which is a
street corridor and is fine.

**The non-tour half exists for rule 5b's corollary and it is not padding.**
The ironside re-site lands in this same commit and removes the tour's only
obstruction; every tour eye is 14m up, and the steepest ray of a 60-degree
frustum pitched 20 degrees down meets the ground at 18.3m slant range, so no
tour ray can hit anything inside 8m unless a building stands beside the
lens. A landing of seven 0.00s would be a number with no demonstration that
it can ever be anything else. The street shots are the accepting case and
they are measured, not assumed: 6137608 read `shotNearFracWorst=0.23` and
`shotMidBefore=0.64`.

---

## 3. Ironside re-sited off the crane

`SimDirector.cs:10496` — `ironside_j2_1` added to the crossing map.
`SimDirector.cs:10512` — Ironside joins Gullwing on the east approach.
`SimDirector.cs:10320-10420` — EXCEPTION THREE: the evidence, the vantage,
the regime break and the predictions.

**The obstruction, computed rather than eyeballed.** `CentreOf(ironside)` is
(36.55, -144.9) — `AvenuesX[2]=17` x2.15, `AvenuesZ[1]=-126` x1.15, scaled
about the origin. The default eye is therefore (36.55, 14, -178.9), which
`frames.tsv` confirms as camX 36.6 camZ -178.9.
`WorldBuilder.BuildLandmarks` puts `Crane_2_tower_up` at x36 z-174, 1.9m
square, spanning y10..18. The eye is inside that box in x and in y and
3.95m south of its near face. The engine's aim ray said
`Crane_2_tower_up@4.01m`. The two agree.

**The vantage was chosen from the numbers.** `farFrac=0.01` says one ray in
84 finds anything between 7 and 20m, and `parcelsByDistrict` on that run
lists six districts and NOT Ironside — no terrace parcels at all, four sheds
and two tenements in the whole district. So stepping back along the same
axis buys an empty plain: the frame loses its obstruction and gains nothing.
Ironside's only mass is the three quay cranes and the gasometer. The camera
therefore TURNS to put those cranes in frame at distance instead of removing
them, and stands on a carriageway instead of inside a block: Ironside's
block pitch is 39.1m in z against a 34m standoff plus a 4m half-avenue, so
the default south eye stands 1.1m INSIDE the block south of its crossing,
while the east eye stands in the 8m gap with 4m clear either side.

New pose: eye (70.55, 14, -144.9), yaw 270, aimed at the SAME crossing the
default picks. Only the approach turns. The three cranes fall at 45.2m,
74.5m and 108.5m, 40.1/23.0/15.5 degrees off axis, inside a 45.7-degree
half-frustum (60 vertical at 16:9, `Feel.BaseFov=60`) — dock skyline down
the left of the frame, every one more than five times `BlockerReachM` away.

`tourResited` goes 2/2 to 3/3, and the comment records why Ironside is the
sharpest case for that denominator: its re-site asks for the SAME point the
fallback would pick, so a failed lookup would silently put the eye back 4m
from the crane with every coordinate in `frames.tsv` still looking
plausible.

**Pose regime break declared for `district_ironside` and no other row.** Its
`ref-bench` pose-stable series, its `frame-drift` row, its `tourDepthBy`
entry and its `lumaThirds` all reset. The other six cameras deliberately do
not move: they are the control for the ground change landing beside them.

---

## 4. TWIN GREP — what the "grep for the same bug" sweep found

**Ground-grade idea.** Four base-colour sites found and all four wired (§1).
`AlbedoScale` has one caller. `MaterialVariant` writes no colour of its own;
`MaterialGraded`'s copies are covered through `_gradedWet`. `TextureGrade`
is now read in exactly one place.

**FINDING, NOT FIXED — outside my files (`WorldBuilder.cs`).** `Tint()`
(WorldBuilder.cs:2551) writes an MPB `_Color`, which OVERRIDES the shared
material's colour per renderer. Four sites stand ground materials under an
MPB and therefore receive neither `GroundGrade` nor the wetness darkening:

    WorldBuilder.cs:516    Yellow_*        Sidewalk, MPB (0.62,0.52,0.18)   — yellowLines=284
    WorldBuilder.cs:543    zebra stripe    Sidewalk, MPB (0.85,0.86,0.84)
    WorldBuilder.cs:2433   PhoneBox_plinth Concrete, MPB Color.white
    WorldBuilder.cs:2461   PostBox_plinth  Concrete, MPB Color.white

The two plinths are the sharp ones: pure white MPB on a ground material
means they have never darkened in rain either, and against a road at 0.55
they will read as white discs at the foot of every phone box and post box.
Paint not darkening is defensible; a white concrete plinth is not.
QUEUE ITEM: **"ground MPB tints bypass GroundGrade — the two white
plinths"**.

**Blocker-measurement idea.** Three other `ViewportPointToRay` sweeps exist
in `SimDirector` (8691 surface probe, 9134 material census, 9283 shade/lit
pair). None of them asks "is anything in the way", so none is a twin; the
84-ray frustum grid remains a single implementation, as `ShotSightlines`'
docstring claims. That docstring said "two questions, two statistics" and
now says three — corrected, since my change falsified it.

**Comments falsified by these changes and fixed:** `SetWetness`'s "its base
colour is `TextureGrade`" (now `TextureGrade x GroundGrade`);
`DistrictTour`'s "TWO OF THE SEVEN" and "FIVE OF SEVEN" headings; "THIS IS A
POSE REGIME BREAK, FOR TWO ROWS AND NO OTHERS"; the `tourResited` 2/2
paragraph; `ShotSightlines`' two-statistics claim.

---

## 5. PREDICTED NEXT LANDING — predictions, not measurements

    districtGround      col:0.74,0.76,0.80  ->  col:0.41,0.42,0.44   (x0.55, dry)
    groundOverFrame     1.23..1.38 sunlit   ->  0.78..0.98
                        0.98..1.02          ->  0.62..0.73
                        0.61..0.78 wet      ->  0.39..0.49   AT OR UNDER THE FLOOR
    tourBlockerShare    [ironside:0.25@4.0m/Crane_2_tower_up]
                                            ->  [ironside:0.00@-/clear], all seven clear
    tourBlockerHits     (new)               ->  0/588 expected; non-zero means
                                                something stands beside a tour lens
    shotBlockerShareWorst (new)             ->  0.15..0.35 on a street shot, named
    tourResited         2/2                 ->  3/3
    ironside row        near 0.00 mid 0.25 far 0.01, depth 32.7m, camX 36.6 camZ -178.9
                                            ->  near 0.00 mid 0.00 far 0.15..0.50,
                                                depth 25-60m, camX 70.6 camZ -144.9 yaw 270
    ironside lumaThirds 0.863/0.329/0.867 (middle DARKEST, only district)
                                            ->  middle no longer the minimum

The ground/frame arithmetic is written out rather than asserted: the ratio
does not scale by 0.55, because the frame mean contains the ground. With g
the ground's share of frame luminance the ratio moves by 0.55/(1-0.45g) —
0.64 at g=0.3, 0.71 at g=0.5.

**The wet row is the flagged risk, and the decision record already named its
lever:** if wet frames leave the band, RAISE `AlbedoScale`'s floor, do not
touch `GroundGrade`. One lever per question.

**The judging instruction, for the read:** `groundOverFrame` series first;
`groundPatch` only on frames that are in band; and the still against
`review_day1_noon`'s ground, because a number gates this and a picture
confirms it.

---

## 6. WHAT I RAN

    tools/lint-shadow.py       0 shadowed Core types (274 types, 87 Game files)
    tools/lint-nested.py       0 nested-type errors (248 top-level Core types)
    tools/lint-static.py       0 static/instance errors (75 members, 523 bodies)
    tools/lint-filetype.py     0 filename-as-type errors (183 files)
    tools/lint-namespace.py    0 namespace-as-value errors (183 files)
    tools/verdict-emit-dupkeys.py          0 same-line duplicate keys
                                           (109 log calls across 177 files)
    tools/verdict-emit-dupkeys.py --selftest   ok (7 checks, accepting case first)
    python3 ledger/verify.py               EXIT 0, footer written

**Verify is GREEN, and the ref-bench worry did not materialise:** the footer
reads `101 ref-bench checks (0 failed)`, so the other builder's selftest fix
is already in the working tree. Also in the footer: `Game layer compiles
(177 files)`, `3761 CoreTests`, `1075 verdict keys, 26 new (run --learn)` —
seven of those 26 are mine, the rest are not.

**NOT VERIFIABLE HERE, and this is the honest limit.** The Game layer does
not compile against Unity in this container and ShapeCheck is
reference-independent, so `Collider` as a dictionary key, the
`Dictionary<Collider,int>` allocation per sweep and `StreetMap.Node`
resolving `ironside_j2_1` are all first compiled by the Windows build.
Nothing here renders a frame, so every number in §5 is a prediction.

---

## 7. NOTICED, NOT DONE (rule 11)

1. **"Ground MPB tints bypass GroundGrade — the two white plinths."** §4.
   `WorldBuilder.cs`, outside my brief.
2. **"The aperture's upper bound was measured on frames with a white
   road."** `Core/LightModel.cs:137` bounds the exposure target above using
   "run edbce5b's noons came back 0.44-0.49 mean with 40-48% bright" —
   frame means that the white ground substantially produced. Darkening the
   ground lowers frame mean luma, so that ceiling is no longer binding the
   way it was. Not a falsified comment (the readings stand), but a number
   whose QUESTION moved. It must be re-judged on the post-fix series, not
   now, and not by me — one lever per question.
3. **"Ironside may simply be empty."** `parcelsByDistrict` lists six
   districts and not Ironside: no terrace parcels, four sheds, two
   tenements. The re-site makes that legible rather than fixing it — today's
   frame cannot tell "Ironside is empty" from "Ironside is behind a crane".
   That is a WORLD item, and the next landing's ironside frame is its
   evidence.
4. **`shotBlockerShare` on the review stills is emitted but not gated.** No
   landed series exists, so any bound would be invented (rule 2). Set it
   from the printed series after two or three landings.
