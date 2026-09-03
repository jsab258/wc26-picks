> **STATUS: LOG, 2026-08-25. NOT CURRENT** after the next landing.

# Stills review — landing 14f964a

Artifact first, gates last. Every visual claim below is a HYPOTHESIS with the
quantity that would settle it. Nothing here was diagnosed from source.

## 0. What I opened

`game-design/sim-shots/` holds **22 JPEGs**. I opened **18** visually and
measured **all 22** numerically.

The **4 I did not read as evidence** are `hunt_day12_noon`, `hunt_day12_night`,
`hunt_day13_noon`, `hunt_day13_night` — and that is itself finding F0 below.

Opened: `review_day1_noon`, `review_day1_dusk`, `review_day1_night`,
`review_day2_noon`, `review_day2_wet`, `review_day2_night`, `review_day2_close`,
`review_day5_noon`, `review_day5_night`, `review_street`, `clips`, and the seven
districts `hook / copper / ironside / downtown / strip / fairview / gullwing`.

Before-pair extracted from **fae0c707** ("Sim stills from 6137608"), the commit
whose verdict names the previous run — not from tree `6137608`, which still
carries the b88adbb-era stills.

---

## F0 — PROVENANCE: four pictures in this directory are 1-3 runs old, and this
## run wrote fresh ledger rows describing them

`frames.tsv` at HEAD is headed `# commit 14f964a...` and contains rows
`day12_noon`, `day12_night`, `day13_noon`, `day13_night`. The JPEGs those rows
describe were last written by:

    hunt_day12_noon/night   a41d0d5b   "Sim stills from b88adbb"
    hunt_day13_noon/night   c895cac8   "Sim stills from a4b05f2"

Neither this run's stills commit (`7ec933f3`) nor the previous one (`fae0c707`)
touched a `hunt_*` file. So the sim rendered and measured day12/day13 this run
and the pictures were not staged.

**Measured, so this is not an inference:** `frames.tsv` says
`day12_noon meanLuma=0.079`; the file on disk measures **0.114**. Same for
day13_noon — ledger `0.495`, file **0.303**. The picture is not the one the row
describes.

Anyone opening `hunt_day13_noon.jpg` today reads a picture from 22 August as
evidence about 14f964a. This is the `git add <directory>` failure mode from the
other side: not stale files claimed as new, but new *rows* claimed over stale
files.

- **Settle it with:** have `sim-shots-stage.sh` emit `framesStaged=N/M` on the
  done line — count of ledger rows written vs JPEGs actually staged. Any row
  without a staged picture should print its name. Alternatively drop the
  unstaged rows from `frames.tsv`, so the ledger cannot describe a file that is
  not there.
- **Confidence: certain.** This is file provenance and byte measurement, not a
  visual judgement.

---

## 1. Does the street read as a British port town?

**In the wet/overcast frames, yes — and it is the best this project has looked.**
`review_day1_noon` is a genuinely convincing rainy British side street: dark wet
tarmac, a yellow line running true along the kerb, tactile paving at the shop
front, "VARGA WATCH & CLOCK" over a shuttered window, a Hook Street plate, rain
streaks, a rolled shutter. The road there measures **luma 0.218** and the
pavement **0.057**. That is asphalt. That is right.

**In every dry frame, no — the town is under snow.** All seven district shots
and `review_day5_noon` render the entire ground plane — road, pavement, kerb,
quay — as near-white. This is the single dominant fault in the landing and it
swamps everything else.

**Measured, 14px patches, this run:**

| frame | what | R,G,B | luma |
|---|---|---|---|
| review_day1_noon | road, foreground | 52,56,64 | **0.218** |
| review_day1_noon | pavement | 12,15,22 | **0.057** |
| review_day2_noon | road, foreground | 138,139,144 | 0.546 |
| district_copper | road near | 129,137,154 | 0.534 |
| district_strip | road near | 167,170,173 | 0.665 |
| district_ironside | quay pavement | 176,180,186 | 0.705 |
| district_hook | road near | 197,196,201 | 0.771 |
| review_day5_noon | pavement | 206,206,206 | **0.809** |
| district_downtown | road far | 213,212,216 | 0.835 |
| district_fairview | road centre | 215,215,215 | 0.842 |
| district_hook | road far | **244,240,237** | **0.944** |

The same nominal surfaces span **0.057 to 0.944 — a factor of sixteen.** Real
asphalt sits at 0.04-0.20 albedo and photographs around 0.25-0.40 sRGB in sun;
0.84-0.94 is the reflectance of fresh snow. `district_hook`'s far road at
244,240,237 is brighter than white printer paper.

The split is clean along weather, from `frames.tsv`: every frame that reads
correctly has `rain>0 wet=1.00`; every frame that reads as snow has
`rain=0 wet=0`. So the hypothesis is **not** "the albedo change did not land" —
it is that the ground only looks like ground when a wet overlay is darkening it,
and under dry direct sun the surface blows out. Overcast frames did darken:
`district_copper` ground band -8.1%, `district_strip` -8.0%, `district_ironside`
-6.0%, `district_gullwing` -6.1%, `review_day2_noon` -14.1% against the previous
run. The change landed. It was nowhere near enough.

A number already in the verdict is suggestive and I flag it as a *hypothesis to
check, not a conclusion*: `bodyAlbedo=[... vs wardrobe max 0.46]`. Every garment
in the game is capped at 0.46 albedo while the road was just set to 0.55. If
both are read in the same space, the road is by construction brighter than any
coat any character wears — which is what the frames look like.

- **Settle it with:** a `groundLumaNoon` / `groundLumaWet` pair — median sRGB
  luma of the pixels below the horizon, printed per shot on the shot line beside
  the existing `rain` and `wet`, plus a `>0.80` blown-out fraction. Today that
  fraction reads **23.1%** for `review_day5_noon`, **17.9%** for
  `district_fairview`, **0.0%** for `review_day1_noon`. Also print the sampled
  albedo of the asphalt, pavement, kerb and concrete materials *separately* —
  the frames suggest pavement/concrete did not move with asphalt, and one
  number cannot show that.
- **Confidence: certain that the dry ground is far too bright.** At the edge of
  the artifact: whether it is the albedo value, the exposure, or a missing wet
  overlay. Do not act on the cause; print the four material albedos.

---

## 2. Anything BRIGHT that should not be

**F1 — The whole dry ground.** See above. This is the brightest thing in the
frame set and it is the ground. The zebra stripes and lane markings are now
*darker* than the tarmac they are painted on in `district_hook` and
`district_fairview`, which inverts the intended reading exactly.

**F2 — Two glowing green boxes on the pavement, `district_strip`, bottom edge**
at roughly (378,690) and (900,692). Measured **221,240,219 luma 0.920** and
**210,240,210 luma 0.907** — brighter than anything else in a frame with no sun
on it, and a hue no other object in the set uses. They read as emissive or as
untextured objects fallen back to a default. A pair of matched saturated-green
blocks on a British pavement is not something the set otherwise contains.
- **Settle it with:** print the material name and emission colour of the two
  brightest non-window objects per shot (`brightestObj=<name>:<luma>`), the way
  `bodyBrightestPart=Ch38_Shoes:237.6` already does for bodies. If they are
  meant to be telecom cabinets, their albedo is the finding; if they are
  emissive, the emission is.
- **Confidence: high that they are anomalously bright.** Their identity is a
  hypothesis — at this scale they are ~30px objects.

**F3 — A large flat orange slab fills the lower-left of `review_day1_night`.**
Measured at (300,600): **216,143,32 luma 0.589** — an untextured, unshaded plane
the same hue family as the lit-window emissives (a window sampled at (800,80)
reads 237,207,72). It occupies roughly a quarter of the frame at street level
with a black railing silhouetted against it. Either a wall being lit to
saturation by an unclamped lamp, or an emissive window quad at enormous scale.
Whichever, it is the brightest surface in the night set and the street behind it
is invisible.
- **Settle it with:** `nightBrightestSurface=<name>:<luma>:<areaPct>` on the
  night shot line. An area percentage is the part that matters — a bright
  100px window is fine, a bright 25%-of-frame plane is not.
- **Confidence: certain something is wrong here.** Cause is open.

**F4 — Every lit window is a flat, uniformly saturated rectangle** with a hard
orange border and no interior, in all five night frames. At night these are the
only readable objects, so the town reads as a black field with yellow stickers
on it. This is a look-quality finding rather than a defect, but against the
stated GTA V bar it is the most conspicuous gap in the night set.
- **Settle it with:** nothing numeric is needed to see it; the number that would
  track progress is the fraction of night-frame pixels that are neither
  near-black nor window-emissive — today that is very small. `review_day5_night`
  ground band is **luma 0.038** and `review_day2_wet` is **0.046**.

**Not a finding, checked:** the red circular sign at the right of
`review_day1_noon` / `review_day2_noon` is a UK no-entry sign on a pole. It is
correct and should stay.

---

## 3. THE PLINTH ANSWER — they are gone

I found red pillar-box cylinders in `review_day5_noon` (x≈945) and
`review_day1_dusk` (x≈645), and scanned vertically through each into its
footing.

    review_day5_noon   body y=368..412  luma 0.12-0.20
                       footing y=416    112,77,81   luma 0.332
                       ground beside                luma 0.474 / 0.521

    review_day1_dusk   body y=633..687  luma 0.03-0.05
                       footing y=693    67,59,57    luma 0.237
                       ground beside                luma 0.163 / 0.183

**In neither case is there a bright disc.** In `review_day5_noon` the base is
*darker* than the ground around it — it reads as contact shadow, which is what
you want. In `review_day1_dusk` it is 1.3x the surrounding paving, consistent
with a kerb edge catching light, and nowhere near the 0.8+ a pure-white pad
would give. A white plinth immune to rain would have shown as an obvious bright
ellipse in the dusk frame, where the ground is at 0.18. It did not.

**The plinth removal landed.** I could not positively identify a phone box in
any frame at this resolution, so this answer covers the pillar box in two frames
and is silent on the phone box.
- **Settle it with:** a one-line `plinthCount=0/N` — number of surviving
  pure-white ground pads out of props checked — so the next run does not need a
  human with a pixel probe.
- **Confidence: high for the pillar box. Unverified for the phone box.**

---

## 4. MISSING or FLOATING

**F5 — The skyline towers float above the ground plane.** `district_copper`,
column scan at x=670:

    y=150..190   dark tower body        luma 0.09-0.17
    y=195..215   SKY  (70,85,104)       luma 0.326      <-- 25px gap
    y=220..230   ground (219,219,219)   luma 0.859

There are **25 pixels of sky between the bottom of the tower and the horizon.**
An object standing on the ground and further away has its base *on or below* the
horizon line — never in a gap of sky above it. The same gap is visible by eye in
`district_strip` (the left-hand cluster) and `district_hook`. Either the towers
hover, or the ground plane stops short of the skyline and leaves void behind it.
- **Settle it with:** print, for each skyline proxy, `y` of its lowest vertex
  minus the ground plane `y` at that `x` — `skylineFootGap=<max>` on the done
  line, with the count of towers examined so a zero is legible.
- **Confidence: high.** The measurement is unambiguous; only the cause is open.

**F6 — A dozen black modernist skyscrapers on a British port town's horizon.**
Visible in `hook`, `copper`, `strip`, `gullwing`, `ironside`. Forty-storey
glass-and-steel towers, some with spires. This is Los Santos, not Meridian in
1988. Whether or not F5 is fixed, these read as the wrong city and they are the
first thing the eye goes to in five of the seven district shots.
- **Settle it with:** no measurement needed — a content decision. The count is
  the number: I count 12+ distinct towers in `district_strip` alone.
- **Confidence: certain about what is drawn.** Whether they are intended is not
  mine to say — but nothing in the brief claims to draw them.

**F7 — `review_day2_wet` is a camera buried in a wall.** The frame is ~90% black
wall with four lit windows and a "Quay Street" plate. Ground band luma **0.046**;
no street, no sky, no horizon. `frames.tsv` records it with
`nearFrac=0.00 midFrac=0.26 farFrac=0.69`, so the sim believes it photographed a
street. It is a wasted review slot and it will silently pass any gate that reads
the ledger rather than the picture.
- **Settle it with:** a `camClear=<metres>` per shot — distance from the camera
  to the first surface along the view axis — and a floor on it. Anything under
  ~1m is a shot inside geometry.
- **Confidence: certain.**

**F8 — `review_day2_close` shows a face breaking apart.** The character
close-up has silver/white polygon shards across the cheek, jaw and shoulder that
do not belong to any facial feature: a jagged sliver crossing the chin, a
detached triangle off the right shoulder, another floating free at (880,425)
with nothing behind it. The eyes and mouth read as separate flat plates sitting
proud of the head.

This is the one I am least sure of and I want to say so plainly. It is a dark
frame, the subject is close, and JPEG at this compression level does ugly things
to specular highlights on a dark surface. It could be eyelash/eyebrow cards
catching a rim light. But a *detached* polygon with sky behind it is not a
compression artefact.
- **Settle it with:** the max distance of any skinned vertex from its bind-pose
  neighbour, per body — `skinBurst=<max>` with the body count as denominator.
  Or simply re-shoot `day2_close` at noon: if the shards persist in daylight
  they are geometry.
- **Confidence: LOW-MEDIUM. This is a hypothesis at the edge of what the frame
  can carry.** Do not touch a rig on the strength of it.

**F9 — Untextured white bodies in the animation contact sheet.** `clips.jpg`
(1980x2420, ~180 clips x 3 thumbs) is overwhelmingly a textured figure in a dark
suit. Against that, a small number of clips render a **flat white/silver
untextured body**: row 5 columns 12-14 (and that one is also inverted, head at
the bottom), row 6 columns 4-6, row 3 column 3. The horizontal and prone poses
elsewhere are almost certainly legitimate fall/dive/knockdown clips and I am
**not** calling those a fault — the untextured ones are a different thing,
because no animation can remove a material.
- **Settle it with:** `clipsUntextured=N/M` — per clip, the mean saturation of
  the body pixels; a textured suit and a default white material are far apart.
  Print the clip names.
- **Confidence: high that some clips render untextured. Certain that most of the
  odd poses are fine.**

**F10 — `district_fairview` renders with no people in it.** I see vehicles,
lamps and traffic lights and not one pedestrian. `district_downtown` shows one
possible figure. Given "a district that renders empty" is a fault that has
happened here before, this is worth a count rather than an eye.
- **Settle it with:** `districtBodies=<name>:<n>` per district shot. A zero with
  the district named is legible; a missing number is not.
- **Confidence: medium — small figures at this scale are easy to miss.**

**F11 — Mirrored shop-sign text.** In `review_street` the left-hand shopfront
sign at ~(415,337) and the right-hand one at ~(775,340) both render their
lettering **reversed**. Same in `review_day2_night` at ~(775,425). The street
plates ("Quay Street", "Hook Street") are correct; it is the shop fascias.
This is the sign being read from its back face.
- **Settle it with:** the project already has `textFacingAway` / `textVisible`.
  They are peaks, and per CLAUDE.md they have been divided against each other
  wrongly before. What is needed is the count of fascia signs whose forward
  normal points away from the camera **at the instant of each screenshot**,
  printed on the shot line with its denominator.
- **Confidence: high.** Reversed glyphs are legible even at this size.

**F12 — Road decals sit at 45 degrees to the road.** Grey diamond quads on the
carriageway in `hook`, `copper`, `gullwing`, `downtown`, `strip` — rotated off
the road axis, reading as flat stickers rather than patches or manhole covers.
`roadDecals=1081` is in the verdict, so something is placing a lot of them.
- **Settle it with:** median absolute angle between each decal's local axis and
  its road segment's direction — `decalYawErr` with the decal count beside it.
- **Confidence: medium.** Their identity is a guess; their misalignment is
  visible.

---

## 5. Cross-examination of the gates

**There are no FAILING GATES in `verdict.txt`.** The landing is green.

Against the biggest finding in the frames — the snow-white ground — the verdict
contains exactly three ground keys:

    groundless=False
    roadDecals=1081
    roadLumaSpread=0.1959

**`roadLumaSpread` is a spread, not a level.** It answers "does the road vary" —
and a uniformly snow-white road has a perfectly healthy spread. Nothing in the
verdict reads how *bright* the ground is. That is why F1 is green: no gate was
asking. This is the exact shape CLAUDE.md rule 4 describes — twenty gates asking
what a system added, none asking what the frame looks like.

The same holds for F5 (nothing measures a prop's distance to the ground plane),
F7 (nothing measures camera-to-geometry clearance) and F9 (nothing measures clip
material).

**One instrument fault noticed in passing:** `bodyAlbedo` is emitted as
`bodyAlbedo=[0.01 0.05 0.05 ...]` — spaces inside a value, which the project's
own rule forbids and which `verdict-read.py` truncates. Four more keys do the
same: `rounds`, `worstWorldPair`, `gapWhy`, `massInRoad`, `speechVoicesWhy`.
Anyone grepping `bodyAlbedo=` gets `[0.01` and no sign anything was lost.

---

## 6. Ranked

| # | finding | confidence | the number that settles it |
|---|---|---|---|
| F1 | dry ground renders as snow (0.66-0.94 luma) | certain | `groundLumaNoon` median + `>0.80` blown fraction, per shot; four material albedos printed separately |
| F0 | 4 stale JPEGs carry fresh ledger rows | certain | `framesStaged=N/M`, naming unstaged rows |
| F5 | skyline towers float 25px above the ground | high | `skylineFootGap` with tower count |
| F6 | 12+ glass skyscrapers on a British port horizon | certain (drawn) | content decision, not a measurement |
| F11 | shop fascia text renders mirrored | high | fascias facing away, at the shot instant, with denominator |
| F7 | `review_day2_wet` is a camera inside a wall | certain | `camClear` metres, floor at ~1m |
| F2 | two glowing green boxes, luma 0.92 | high | `brightestObj=<name>:<luma>` per shot |
| F3 | flat orange slab, 25% of `day1_night` | certain (present) | `nightBrightestSurface` with area% |
| F9 | some animation clips render untextured white | high | `clipsUntextured=N/M`, named |
| F4 | night = black field with flat yellow window stickers | certain (look) | fraction of night pixels neither black nor emissive |
| F12 | road decals rotated 45deg to the road | medium | `decalYawErr` beside `roadDecals` |
| F10 | `district_fairview` reads empty of people | medium | `districtBodies=<name>:<n>` |
| F8 | face geometry shards in `day2_close` | **low-medium** | `skinBurst` max, or re-shoot at noon |

**Do not act on F8 without a number.** It is exactly the class of judgement this
project has been burned by.

## 7. What is genuinely good

`review_day1_noon` and `review_day1_dusk` are the strongest frames the project
has produced. Wet tarmac at 0.218, pavement at 0.057, a correct yellow line, a
readable Hook Street plate, tactile paving, rain, a sodium dusk sky over a
silhouetted terrace. That is a British port town. Whatever the dry frames need,
it is what those two already have.
