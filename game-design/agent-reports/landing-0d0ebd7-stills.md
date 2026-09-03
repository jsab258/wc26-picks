# Stills read — landing 0d0ebd7

> **STATUS: LOG, 2026-08-25. NOT CURRENT** after the next landing

Every finding below is either a direct measurement of the committed JPEGs
(read-only, PIL) or is labelled a HYPOTHESIS with the quantity that would
settle it. No file in the repository was edited by this pass except this one.

---

## 0. Provenance, done first

`runs/0d0ebd7.txt` line 1 reads `# Sim verdict — 0d0ebd7 @1787632272`. No
`NO PLAYER LOG`, no `NO RUN`. The build ran.

**The new key works and it caught the thing it was built for.**

    framesStaged=17/29
    framesRows=29
    framesUnstaged=[day3_noon/day3_night/day4_noon/day4_night/day6_noon/
                    day6_night/day7_noon/day7_night/+4more-not-shown]

The cap announces itself, which is the rule. The 4 not shown are
`day8_noon day8_night day13_noon day13_night` (derived: 29 rows minus the
17 with staged pictures).

**Excluded from all evidence below:**

| excluded | why |
|---|---|
| `hunt_day13_noon.jpg`, `hunt_day13_night.jpg` | named in `framesUnstaged`. `git log -1` on both: last written by `c895cac8` — *"Sim stills from a4b05f2"*, **two landings back**. The bytes on disk are days old. |
| `frames.tsv` rows for day3/4/6/7/8/13 noon+night (12 rows) | rows describing pictures no staged file corresponds to |

`frames.tsv` still carries full rows for `day13_noon` (meanLuma 0.428) and
`day13_night` (0.123) — numbers for pictures this run did not take. That is
precisely the fault of the previous landing, still present in the ledger,
now *visible* because `framesUnstaged` names it. The instrument is doing its
job; the ledger writer has not yet been made to stop emitting the rows.

**Mirror gap the new key cannot see.** Three JPEGs are this run's bytes but
have NO `frames.tsv` row: `clips.jpg`, `review_day2_close.jpg`,
`review_street.jpg`. `framesStaged=17/29` counts only the ledger's side, so
"a row with no picture" is reported and "a picture with no row" is not.
*Quantity: add `framesOrphan=N` and `framesOrphanWho=[...]`.* Confidence HIGH
(counted: 20 fresh JPEGs, 17 with rows).

**Standing check — is this a real render?** `git show --stat 2a708418`: all
20 staged JPEGs changed byte length against the previous landing. Not an
identical-bytes-under-a-new-header pipeline finding.

**What this commit changed.** `0d0ebd7` is *"The space check had the bug
written into its own accepting fixture"* — verdict formatting and lint. No
visual lever. The expectation that the picture is unchanged is well founded.

---

## 1. Does the street read as a British port town, late-analog?

**No.** Blunt, and it is not close.

Three things overrule everything the content team has put in:

1. **A skyline of modern curtain-wall towers in all seven districts.** Sheer
   black-glass high-rises are the Los Santos silhouette. In a late-analog
   British port they are an anachronism of about thirty years.
2. **The ground renders as fresh snow in daylight.** Road foreground in
   `review_day5_noon` measures **0.775 luma**; `district_ironside`'s ground
   band is **68.9% above 0.70**. A wet British quayside is the darkest thing
   in frame, not the brightest.
3. **Night is a black void with glowing yellow stickers.** `review_day2_night`:
   **70.4% of the lower half is below 0.05 luma**, with 22 lamp toggles
   recorded and no lamp pool visible on the ground anywhere.

What is genuinely right, and worth saying because it is most of the work:
stone and brick facades with real texture, cobbled setts, chimney pots
(`chimneys=219`), roof aerials (`aerials=129`), yellow kerb lines
(`yellowLines=284`), dock cranes, shop fascias with British names
(VARGA WATCH & CLOCK, MARLOW BUTCHERS), rain, and wet road reflections.
**`hunt_day12_noon` and `review_day2_wet` genuinely read as a British port
town** — stone, cobbles, rain, warm windows. The content is there. The
horizon and the light are what destroy it. That is a smaller problem than it
looks, and a more fixable one.

---

## 2. The horizon — CONFIRMED UNCHANGED, in all seven districts

**Confidence HIGH. Measured, not assumed.**

`district_copper`: ground begins at **y=212**. Column luma profiles read
`dark tower → flat sky → ground` with the sky run 17-63 rows tall and its
standard deviation under 0.03:

    x=1060  towerBase y=187  groundStarts y=212  skyGap 25px
    x=1075  towerBase y=187  groundStarts y=212  skyGap 25px
    x= 530  towerBase y=186  groundStarts y=212  skyGap 26px
    x= 680  towerBase y=181  groundStarts y=212  skyGap 31px
    x=  90  towerBase y=183  groundStarts y=212  skyGap 29px
    x= 264  towerBase y=149  groundStarts y=212  skyGap 63px

**The previous landing's 25 px reproduces exactly** at x=1060 and x=1075.
Nothing moved, as expected.

Floating columns per frame (a column counts only if a flat sky run separates
tower from ground):

| frame | floating columns | gap px min / median / max |
|---|---|---|
| district_copper | 450 / 1280 | 6 / **26** / 165 |
| district_strip | 159 / 1280 | 6 / 7 / 117 |
| district_ironside | 77 / 1280 | 6 / 119 / 163 |
| district_hook | 73 / 1280 | 6 / 14 / 125 |
| district_downtown | 41 / 1280 | 6 / 7 / 15 |
| district_fairview | 18 / 1280 | 6 / 13 / 27 |
| district_gullwing | 10 / 1280 | 6 / 8 / 32 |

**7 of 7.** The premise violation and the float are both unchanged.
`skyline=23/23 skylineDock=6/6` → 17 non-dock towers, all repainted, none
reaching the ground.

**Cross-examination.** `skyline=23/23`, `skylineRepainted=23`,
`skylineDock=6/6`, `skylineFit=1.76`, `skylineWidest=88.5/50.3` are all
green, and all seven ask *"is every piece present, sized and repainted"*.
Not one asks whether a piece's base reaches the ground, and none can ask
whether a curtain-wall tower belongs in 1987.

**Quantity to settle it next run:** for each of the 23 skyline pieces, print
`worldY of its lowest vertex minus terrain height at its (x,z)` —
`skylineBaseDrop=[min/median/max]` plus `skylineAfloat=N/23`. A piece whose
base sits above the ground plane is arithmetic, not a judgement, and the
number is available without a render.

---

## 3. The ground — CONFIRMED SAME. Nothing moved that nobody intended.

**Confidence HIGH.**

Source albedo is byte-identical across the two landings:

    PREV  districtGround=[mat_asphalt/col:0.41,0.42,0.44/...gloss:0.78...]
    NOW   districtGround=[mat_asphalt/col:0.41,0.42,0.44/...gloss:0.78...]

(only `d:19.3`→`19.7`, a camera distance). Rendered, measured off the JPEGs:

| sample | luma |
|---|---|
| `review_day5_noon` road foreground | **0.775** |
| `review_day5_noon` pavement foreground | 0.688 |
| `district_ironside` ground band mean | 0.691 |
| `district_copper` ground at horizon | 0.858 |

Sits inside the 0.77-0.94 band reported last landing. Confirmed, not
contradicted. Corroborating verdict keys also flat: `skyVsWall`
0.286/0.855 → **0.282/0.855**, `wallOverSky` 2.99 → **3.03**.

**The sharper way to state the fault, because it is scale-free.** In
`district_copper` the ground at the horizon is **0.858** and the sky directly
above it is **0.326**. The ground is **2.6x brighter than the sky lighting
it.** Under any overcast dome that is impossible, and it does not depend on
knowing the exposure or the tonemap. `wallOverSky=3.03` says the same thing
about the walls and is already printed.

**A new number this build that needs a custody statement before anyone uses
it.** `groundAlbedoBy=[asphalt:0.008/sidewalk:0.021/kerb:0.067/concrete:0.020]`
is absent from `14f964a.txt` and present here. It says asphalt albedo is
**0.008**. `districtGround` in the same file says **0.41**. Two keys named
for the albedo of the same surface, in one verdict, differing by **51x**.
One of them is not measuring what its name says.
*Quantity: state in the emit comment what each is a statistic of — sampled
texel mean, material `_Color`, or post-grade rendered value — and print the
sample count beside each.* Confidence HIGH that they disagree; no view on
which is right. **Do not quote either in a conclusion until that is settled** —
this is the two-numbers-from-one-variable check failing in the other
direction.

---

## 4. The two plinths — one answered, one NOT FOUND. I will not guess.

### Pillar box: no bright disc. Improvement holds, with a caveat that matters.

`review_day5_noon`, red cylinder at x997-1050 / y380-440. Pavement luma:

    at its foot          0.377
    60px to the left     0.477
    to the right         0.497

The contact reads **darker** than the surround — a contact shadow, which is
what should be there. **No bright white disc.** Confidence MEDIUM, not HIGH,
and the reason is the caveat: **the pavement is itself at 0.688-0.775 luma,
so a pure-white plinth would be nearly invisible against it.** This
measurement cannot separate *"the tint was removed"* from *"the tint is still
white and the over-bright ground is hiding it"*. Fix the ground and this
question re-opens.

*Quantity to settle it independently of the ground:* print the plinth
renderer's material `_Color` directly — `plinthTint=[phonebox:r,g,b /
pillarbox:r,g,b]`. One line, no render needed, and it is immune to the
camouflage.

### Phone box: NOT PRESENT IN ANY STAGED FRAME.

A saturation sweep across all 20 fresh JPEGs for a tall narrow red volume
returns nothing. Every red street object found is a ~44x65 px cylinder. The
verdict says `callboxStaged=True callboxWhy=[steered]` and `phonesOk=True
lines=8`, so the sim has phone boxes; **no committed still shows one.**

**Question 4 is half-answerable from this landing and I am not answering the
other half.** *Quantity: add a `review_callbox` shot, or print
`callboxInShot=N/22`, so "the plinth is fine" and "nobody photographed it"
stop looking identical.*

### And the object I did measure may not be a pillar box.

Crop of the red cylinder (`hunt_day12_noon`, x740-860): a smooth red cylinder
with a **dark grey/black cap** and no aperture slot, no fluting, no cypher.
A British pillar box is red including its cap. `kitAlbedo` lists
`base_mesh_outdoor_bin`, `base_mesh_cigarette_bin`, `base_mesh_swing_bin`.
**HYPOTHESIS: this is a litter bin, and the pillar box was never in shot
either.** *Quantity: print the prefab name of the nearest red street furniture
per shot — `redStreetProp=[name@dist]`.* Confidence MEDIUM.

---

## 5. Bright / floating / sunk / missing / empty

### 5.1 Bodies wearing chrome. No gate asks about gloss. Confidence HIGH.

`clips.jpg` row 5 cols 13-15 and row 6 cols 4-6: suits render as **polished
silver with mirror streaks following the mesh curvature**, not fabric.

Corroborated in a street frame — `review_day2_close`, jacket patch
(150,520)-(260,600): **mean luma 0.158, max 0.999.** A fully clipped white
specular on cloth in a frame whose mean is 0.117.

The number that makes this a finding rather than an impression:
`bodyAlbedo=[0.01/0.05/.../0.46] vsWardrobeMax:0.46`. **No body has an albedo
above 0.46**, so nothing on a body can reach 255 by texture. It is specular.

Green gates that cannot see it: `capsules=0`, `undressed=0`,
`bodiesUndressed=0`, `bodyParts=[nothing to paint — all 9 renderer(s) came
textured]`, `bodyTinted=2938`. Every one asks *is it clothed / is it painted*.
None asks *how shiny is it*. This is the same shape as the white capsule and
the body on its back: a green wardrobe gate beside a wrong-looking body.

*Quantity: `bodyGloss=[median/p90/max]` and `bodyMetallic=[max]` over the
cast's materials, with the offending renderer named — `bodyGlossWorstWho`.*

### 5.2 An emissive slab on a bench. Confidence MEDIUM (HYPOTHESIS as to cause).

`review_day2_wet` at (985-1075, 355-388): flat quad, **rgb 189,102,15, mean
luma 0.446, max 0.774**. The bench under it measures **0.064**. Frame mean is
**0.117**. A flat plane at 7x its own support in a night frame.
*Quantity: print emission for props within 3m of the camera at that shot —
`propEmissive=[name/emissionRGB]`.*

### 5.3 Light shafts render as hard opaque wedges. Confidence MEDIUM.

`hunt_day12_night`: ~5 pale triangles with hard straight edges running from
lamp head to ground, reading as paper cones rather than volumetric scatter.
`shafts=362`, unchanged from the previous landing.
*Quantity: `shaftEdgeAlpha` at the cone boundary and `shaftSoftness` in px;
a volumetric shaft has no hard silhouette edge.*

### 5.4 A noon frame darker than seven of the ten night frames. Confidence HIGH.

    day   noon    night   margin
    1     0.242   0.104   +0.138
    2     0.391   0.093   +0.298
    3     0.241   0.121   +0.120
    4     0.410   0.112   +0.298
    5     0.420   0.108   +0.312
    6     0.261   0.090   +0.171
    7     0.370   0.139   +0.231
    8     0.407   0.083   +0.324
    12    0.089   0.079   +0.010   <-- 
    13    0.428   0.123   +0.305

`day12_noon` at **0.089** is darker than day1, 3, 4, 5, 7, 13 and 6 nights.
`hunt_day12_noon` opened and confirmed: it looks like night.

`lumaPairs=[... darker10of10 ...]` is GREEN. It is a **within-day** test, and
within-day it is correct. The margin on day 12 is **+0.010** — the same class
of non-measurement as the `nightNotDarker` 0.136-vs-0.135 incident. The
question it structurally cannot ask is *"does any noon look like night"*.

*Quantity: print `noonFloor=min(noon meanLuma)` beside
`nightCeiling=max(night meanLuma)` and gate on the gap between the two
populations, not on ten independent pairs.*

### 5.5 World text half the frame wide, and it moved in a build with no lever.

`review_day5_night`, "Quay Street": white glyph bbox spans x136-888,
y347-**719** — **0.588 of frame width, 0.517 of height, clipped by the bottom
edge**. Confidence HIGH (pixel measurement).

The part that needs a person:

    worstWorldFrac   PREV 0.089  ->  NOW 0.153   (+72%)
    namesClipWorst   PREV 0.16   ->  NOW 0.84    (5.2x)

**This build changed no visual lever.** A 5.2x move in text clipping across
an instruments-only commit is either an instrument that changed definition or
something that moved unintentionally. Both are worth an hour before the next
dispatch. *Quantity: `git log -p` the emit site for `namesClipWorst` between
14f964a and 0d0ebd7; if the code is untouched, this is a real regression and
needs `namesClipWorstWhere=[shot]` to locate it.* Confidence HIGH that it
moved; NO view on which cause.

### 5.6 `windowsLit=0` while the windows are plainly lit. Confidence HIGH.

`windowsLit=0` and `windowsShopLit=0` on the done line, against
`windowsLitAtShot=2477`, `windowsShopLitAtShot=363`, `windowsHourAtShot=23`.
Identical in both landings. `review_day2_night` and `review_day1_night` show
dozens of lit windows.

A whole-run number and a per-shot number under near-identical names, and the
whole-run one reads as a fault. *Quantity: rename to `windowsLitAtEnd` and
print `windowsLitPeak` beside it, or drop the ambiguous key.*

### 5.7 Flat emissive window quads. Confidence MEDIUM.

`review_day1_night` / `review_day2_night`: lit windows are uniform saturated
yellow rectangles with heavy bloom, no mullion, no curtain, no interior
falloff. Sampled window patch rgb 205,170,59. `windowGlow` reports face
b/r 0.12-0.55 against `target b/r=0.45`, so the *colour* is instrumented; the
*flatness* is not. *Quantity: `windowFaceLumaStd` within a lit pane — a real
window is not uniform.*

### 5.8 `slabsAloft=1480`, unchanged, uncontested.

`slabsAloftWho=[Bldg135_cornice@y6.5w28 / Bldg135_win_zN_1_0@y4.4w23 /
Bldg135_win_zP_1_0@y4.4w23 / Bldg135_fascia@y3.2w21]`. 1480 is a large count
sitting green beside `boxesAfloat=0/384`. Not visible in any staged frame
(Bldg135 is not in shot), so **no visual confirmation either way** — flagged
because the number is large and nobody is treating it as red. Confidence LOW
as a visual finding; HIGH that it is unexamined.

### 5.9 No district renders empty.

All 7 contain buildings, roads, props and vehicles. `district_ironside` is
the closest to empty: 68.9% of its ground band above 0.70 luma with almost no
feature, reading as a white plain — but that is the ground fault (§3), not a
missing district.

### 5.10 Low-confidence, listed so it is not lost.

- **Single yellow kerb lines** where a British street would carry doubles.
  `yellowLines=284`. *Quantity: `yellowLineDoubles=N/284`.* Confidence LOW —
  cannot resolve one line from two at this distance and resolution.
- **Identical contact-sheet triplets.** Two clip groups in `clips.jpg` show
  three visually identical cells. `sheetSlid=59 sheetSlidOf=192`.
  *Quantity: per-clip mean absolute pixel difference between the three
  sampled cells — `sheetCellDelta=[min/median]`, and name any clip at 0.*
  Confidence LOW as a fault (a held pose is legitimate content).

---

## 6. Gates against the artifact, both directions

`gatesChecked=72 gatesFailed=0`. Every gate green.

**In the frame, claimed by nothing:** floating tower bases (7/7 districts),
chrome bodies, the emissive slab in `day2_wet`, hard-edged light wedges,
ground brighter than sky.

**Claimed green, contradicted by the frame:** `windowsLit=0` (windows are
lit); `lumaPairs darker10of10` (a noon frame is darker than seven nights);
`skyline=23/23` (all present — none touching the ground).

**Red gates whose fault the artifact does not show:** none. There are no red
gates.

The pattern is the one already written down: all 72 ask what a system ADDED.
Not one asks what the frame LOOKS like.
