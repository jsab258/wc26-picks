# Art direction as rules — what artists know, encoded so we can check it

> **STATUS — SPEC, 2026-08-25.** Research for M17.10 / `visual-bar-spec.md` §4.
> Not a plan and not a landing report. Every principle here is stated as
> something a build can CHECK or a pipeline can BUILD; anything that could not
> be reduced to that is in §8 (Rejected) rather than dressed up as advice.
> Sourced claims carry a URL. Everything marked **[measured]** was computed in
> this session on the committed frames; everything marked **[inference]** is
> mine and has no citation behind it.

---

## 0. The one method that makes the rest safe

We have five GTA V frames committed byte-exact in `game-design/reference/` and
seven pose-stable district stills committed every build. **Every bound in this
document is derived from the reference distribution, not invented.** That is
CLAUDE.md rule 2 applied to art direction: an art principle tells you WHICH
number to compute; the references tell you what value it should take.

The corollary matters more than any individual rule: **a principle we cannot
compute on both sides is not a recommendation.** `tools/ref-bench.py` already
runs one instrument over refs and stills; every metric below is specified as an
addition to that same instrument, so the comparison can never become two
instruments arguing.

**What I did this session.** Wrote a throwaway probe computing eleven candidate
art-direction statistics on all five references and all seven district stills,
and read the series. Six of the eleven separate the two populations; five do
not, and the five are in §8 so nobody re-derives them as promising. The probe
is reproduced in §9 and should be folded into `ref-bench.py` rather than
shipped as a second tool.

---

## 1. THE MEASURED FINDINGS — the spine of everything below

All values **[measured]** this session, 1280x720 LANCZOS resample, Rec.601 luma,
same convention as `ref-bench.py`. `REF` = the five GTA V frames. `SIM` = the
seven `district_*.jpg` stills at HEAD.

| statistic | what it is a statistic OF | REF range | SIM range | separated? |
|---|---|---|---|---|
| `skyOverGround` | median luma of top 20% of rows ÷ median luma of bottom 35% | **1.35 .. 5.79** | **0.54 .. 1.25** | **TOTAL** |
| `skyBandP50` | median luma, top 20% of rows | **0.690 .. 0.836** | **0.356 .. 0.392** | **TOTAL, no overlap** |
| `hueArcAt` | centre of the densest 60° hue arc, chromatic pixels only | **30° .. 50°** (amber) ×5 | **220° .. 230°** (blue) ×5, 30–40° ×2 | **near-total** |
| `hueArc60` | share of chroma inside that one 60° arc | 0.557 .. **0.957** (med 0.84) | 0.484 .. 0.775 (med 0.56) | strong |
| `v3which` | which of dark/mid/light holds the largest area | light ×3, dark ×2, **mid ×0** | **mid ×5**, light ×2 | **categorical** |
| abs(`warmSplit`) | (R−B) of top luma quartile − (R−B) of bottom quartile | **0.079 .. 0.242** | 0.007 .. 0.060 | **TOTAL** |
| `satP50` / `satP99` | median / 99th pct HSV saturation | 0.159–0.342 / 0.495–**0.758** | **0.058**–0.248 / 0.542–**0.803** | shape differs |
| `chromShare` | fraction of pixels with S>0.15 | 0.534 .. 0.820 | 0.288 .. 0.712 | partial |

And from the existing instrument, run this session for context:

    ground/frame mean    REF 0.387..0.981     SIM 1.008..1.355   (all seven above every reference)
    GROUND PATCH surface REF 0.205..0.382     SIM 0.012..0.267   (five of seven below every reference)

**Read together these say one thing in four ways.** Our frames are lit upside
down (sky half as bright as the references', ground brighter than the frame
mean where no reference is), they are mid-grey where no reference is mid-grey,
their chroma sits in the blue arc where every reference sits in the amber arc,
and they have no warm/cool separation at all in any weather.

That is not five problems. **[inference]** It is one problem — an ambient term
that is blue, flat and applied to everything — presenting five ways, and it is
consistent with the `visual-bar-spec.md` §4 R0 cause chain rather than a new
finding. The value of the numbers is that each one is now a testable rule with
a reference-derived bound, and three of them (`hueArcAt`, `warmSplit`,
`v3which`) are dimensions nothing in this project measures today.

---

## 2. VALUE STRUCTURE — rank 1 by impact-per-effort

### What artists know

**Notan.** A Japanese design idea, standard in Western painting teaching:
reduce the image to two or three massed values and judge the design from that
alone. "If your notan reads clearly from across the room, your full painting
will too", and "one value, either light or dark, should dominate in the picture
plane"
([Alvalyn](https://alvalyn.com/value-mapping-the-notan-principle/),
[Artists Network](https://www.artistsnetwork.com/art-mediums/pastel/the-value-of-notan/),
[art in context](https://artincontext.org/notan/)).
The three-value sketch is the working form: a dark, a middle and a light, massed,
with unequal areas.

**Shape hierarchy.** Neil Blevins' primary/secondary/tertiary framing: squint
and the details vanish, leaving the big shapes; secondary shapes sit on the
primaries; tertiary shapes are the detail. Explicit guidance: vary size within
each tier, spread detail rather than clumping it, and **keep areas of almost no
detail** so there is somewhere for the eye to rest
([Soulburn Studios](http://www.neilblevins.com/art_lessons/composition_primary_secondary_and_tertiary_shapes/composition_primary_secondary_and_tertiary_shapes.htm),
[Fine Art Tutorials](https://finearttutorials.com/guide/visual-hierarchy/)).

**Atmospheric perspective.** Distant objects lose contrast and shift toward the
sky colour; the named failure modes are painting backgrounds too dark or too
saturated, keeping distant edges too sharp, and ignoring value compression
([21 Draw](https://www.21-draw.com/add-depth-to-your-art-with-atmospheric-perspective/),
[Russell Collection](https://russell-collection.com/what-is-atmospheric-perspective/)).

**And the physics that settles our specific argument.** The CIE standard
overcast sky (Moon & Spencer, 1942) has the zenith **three times brighter than
the horizon**, with no dependence on sun azimuth
([EnergyPlus engineering reference](https://bigladdersoftware.com/epx/docs/9-0/engineering-reference/daylight-factor-calculation.html)).
And in photographic practice a correctly exposed daylight shot has **sky 3 to 5
stops brighter than a correctly lit face**
([Tools for Film](https://www.toolsforfilm.com/blog/day-for-night-technique)).
An overcast British sky is not a dark ceiling; it is the brightest object in
the scene and it is brightest overhead. `visual-bar-spec.md` R0.c asserts this
from reference frame 3; the CIE sky model is the citation it was missing.

### The rules

**R-V1 — SKY IS THE BRIGHTEST BROAD MASS (daylight).** `skyOverGround >= 1.35`
at noon and morning, dry or overcast, on every eye-level still. The floor is
the reference MINIMUM, not a margin I chose. Today: 0.54 .. 1.25 across seven,
so this is red seven times out of seven and is the same fault R0 already owns —
it gains a single number and a per-still verdict key.
*Statistic: ratio of two medians of one decode, both from the same frame.*

**R-V2 — NO MID-GREY MUSH.** Bucket display luma into dark `<0.25`, mid
`0.25..0.60`, light `>=0.60` and emit which bucket holds the most area. No
reference is mid-dominant; five of our seven are. Rule: **mid must not be the
largest of the three groups on a daylight still**, and the largest group must
hold `>= 0.37` of the frame (reference minimum 0.370).
*Statistic: three area shares of one frame; the verdict key is a word, so emit
`v3which=mid` and the three shares as `v3=0.296/0.383/0.321` — no spaces.*

**R-V3 — DEPTH MUST COST CONTRAST, MEASURED IN DEPTH.** Emit local contrast and
mean saturation per depth bin from the DEPTH BUFFER (say 5 bins to the far
plane) and require both to fall monotonically outward. **Do not use a screen-space
near/far band split** — I tried it (`lcNearOverFar`) and it fails, because in an
eye-level shot the "far" band is full of building detail and the "near" band is
empty road; refs and sims overlap completely (§8). This is the one value rule
that needs engine work rather than a frame statistic, and it is worth it: with
depth bins it also becomes the gate for the fog/aerial-desat tuning R5 owns.

**R-V4 — THREE DETAIL TIERS, WITH REST.** Placement rule, not a frame rule: every
dressed street segment carries primary silhouette (buildings, cranes, gable
ends), secondary (poles, vehicles, bins, phone box, pillar box), tertiary
(decals, drainpipes, aerials, kerb grime) — **and at least one span per block
deliberately left at primary+secondary only.** Checkable from the placement
data we already have: emit props-per-50m split by bounding-box tier, and the
count of 50m spans whose tertiary count is zero. Today `prop-reach` counts kits;
it does not count tiers. **[inference]** the "areas of rest" half is the part
that is always skipped and is why uniformly-dressed procedural streets read as
wallpaper.

---

## 3. COLOUR DISCIPLINE — rank 2, and the cheapest fix in the document

### What artists know

**Limited palette with unequal proportions.** The 60-30-10 rule: a dominant
field, a secondary, an accent. "Equal amounts of three colors feel like an
argument. A field, a partner, and a spark feel like a decision"
([CompositePaint](https://compositepaint.com/learn/60-30-10-rule/),
[Diamond Vogel](https://www.diamondvogel.com/architectural/blog/603010-rule)).

**Temperature separation.** Light warm, shadow cool, on props and forms —
volume is created by temperature as much as by value, and a warm object over a
cool one reads as in front even at equal value
([Nasty Rodent, Color Theory for Game Art](https://nastyrodent.com/color-theory-for-game-art/),
[Room 8 Studio](https://room8studio.com/news/game-art-analysis-pt-2-atmosphere/)).
Room 8's other line is the one to put on the wall: give colour feedback in
**production language — value range, temperature direction, palette
reference** — not in adjectives.

**Unifying assets from many sources** — our exact problem. Four techniques,
ordered by how automatable they are:

1. **Albedo range clamping.** Real dielectric base colours occupy a narrow band.
   The DONTNOD/Lagarde chart's rule, as reported in
   [Iri Shinsoj's albedo chart](https://shinsoj.artstation.com/blog/Q9j6/pbr-color-space-conversion-and-albedo-chart)
   and the [Polycount discussion](https://polycount.com/discussion/215236/albedo-material-vaules-chart):
   **do not go below 30–50 sRGB, do not exceed 240 sRGB**, with 60–240 the
   normal working band for non-metals. Textures scraped from a dozen free
   libraries violate this constantly — baked lighting, blown scans, crushed
   JPEGs — and a violated albedo is the single most reliable way to make one
   asset refuse to sit in a scene.
2. **A shared grading LUT** applied after everything
   ([LUTs for Game Artists](https://www.numberanalytics.com/blog/luts-for-game-artists)).
   Necessary and not sufficient: a LUT cannot fix an asset whose albedo is
   wrong, it only makes the wrongness consistent.
3. **Texel density consistency.** "Players notice density mismatches more than
   they notice absolute resolution"; the working standards are ~512 px/m for
   background props and ~1024 px/m for hero assets
   ([StraySpark](https://www.strayspark.studio/blog/texture-resolution-guide-games-512-1k-2k-4k),
   [Beyond Extent deep dive](https://www.beyondextent.com/deep-dives/deepdive-texeldensity)).
4. **One shared surface-history layer over everything** — world-space grunge,
   wetness, dirt, applied by the shader rather than per asset. This is what
   actually makes kitbash read as one place. **[inference]**, but it is the
   common thread through every "unify your assets" answer I read.

### The rules

**R-C1 — THE PALETTE ARC.** Compute the densest 60° hue arc over chromatic
pixels (S>0.15). Every GTA reference lands at **30–50°** — amber/brick/tarmac —
and holds 0.56–0.96 of its chroma there. Five of our seven land at **220–230°**,
blue. Rule: **`hueArcAt` must sit in 15°..60°, and `hueArc60 >= 0.55`** (the
reference floor). A British port town's own materials — red and buff brick,
rust, sandstone, tarmac, timber, sodium light — are all inside that arc already,
so this rule is not a Los Santos import; the blue is our ambient, not our
content.

**R-C2 — TEMPERATURE SEPARATION EXISTS, IN EITHER DIRECTION.** `warmSplit` =
mean(R−B) of the brightest luma quartile minus mean(R−B) of the darkest.
References: **+0.079, +0.150, +0.242 on the sunlit frames, −0.090 and −0.104 on
the overcast ones**. Ours: −0.032 .. +0.060, i.e. nothing, in every weather.
Rule: **abs(`warmSplit`) >= 0.079** on every daylight still. The SIGN is a
weather fact, not a bug: sun warm / sky-shadow cool gives positive, and a large
cool overcast source with warm bounce off brick gives negative. **Gate the
magnitude, never the sign** — gating the sign would forbid the two reference
frames that look most like Meridian.

**R-C3 — SATURATION HAS A CEILING AND A FLOOR, AND OURS ARE BOTH WRONG.**
References: median saturation 0.159–0.342 with p99 never above **0.758**. Ours:
median as low as 0.058 with p99 up to **0.803**. Our frames are greyer overall
AND have hotter individual pixels — the classic "desaturated grade plus a few
unclamped emissives" signature. Rule: **`satP99 <= 0.758` and `satP50 >= 0.159`**.
Both bounds are reference extremes.

**R-C4 — ALBEDO VALIDATION AT INGEST, on every fetched texture.** A pipeline
step, not a frame gate: reject or auto-correct any base-colour map whose
5th percentile is below sRGB 30 or 95th above sRGB 240, and report per texture
`albedoP05/albedoP95/clampedBy`. **This is the highest-leverage automated step
in the whole document** because it runs once per asset, offline, in Python we
can write today, needs no CI round trip, and it is the reason free assets from
a dozen sources clash. Ship it with its denominator: `texturesExamined=N` beside
`texturesClamped=M`, or a clean run is unreadable (rule 3b).

**R-C5 — TEXEL DENSITY BANDS.** Compute px/m per material from texture
resolution and UV area at import; require every street-level asset inside one
band (propose 384–1024 px/m, a band to be set from the printed series of what
our current assets actually are — do not adopt the 512 figure until we have
looked). Emit the distribution, then set the bound. Two objects at 5x different
density next to each other is the loudest "asset soup" tell there is.

---

## 4. BRITAIN, 1988 — the markers that stop this reading as Los Santos

### The light is different, and it is arithmetic

**[measured, my computation]** Solar elevation at solar noon is
`90 − |latitude − declination|`. For a north-east English port at 54.5°N against
Los Santos (Los Angeles, 34.05°N):

| | June solstice | equinox | December solstice |
|---|---|---|---|
| Meridian 54.5°N | **58.9°** — shadow 0.60× height | **35.5°** — shadow 1.40× | **12.1°** — shadow 4.68× |
| Los Santos 34.05°N | 79.4° — shadow 0.19× | 56.0° — shadow 0.68× | 32.5° — shadow 1.57× |

**The sun is never overhead here.** At our latitude the best midsummer noon is
lower than Los Santos' *equinox*, and a British winter noon throws a shadow
nearly five times the height of what casts it. Everything the references show
about long raking shadows is not a dramatic choice we have to earn — at 54°N it
is what noon looks like.

**R-B1 — SUN ELEVATION CLAMP.** Cap noon sun elevation at **59°** and drive it
from date; emit `sunElevNoon` per still. A Los-Santos-height noon sun is the
single fastest way to make a British street read as somewhere else, and it is a
one-line fix in the sky/sun driver. **[inference]** on the "fastest way", but the
elevation table is arithmetic.

**R-B2 — WEATHER MIX MATCHES THE CLIMATE.** The UK averages about **1,403
sunshine hours a year** (Manchester ~1,420, London ~1,675), against a maritime
climate described as often cloudy, with Glasgow and Manchester among Europe's
cloudiest cities
([Soly, citing UK averages](https://soly-energy.co.uk/blog/local-hours-of-sun-in-the-united-kingdom/),
[Statista annual UK sunshine series](https://www.statista.com/statistics/610566/total-annual-sunshine-hours-uk/)).
1,403 hours against ~4,400 daylight hours is **under a third of daylight with
the sun out.** Rule: the sim's weather draw for daylight hours should be roughly
**2:1 overcast-or-wet against dry-sun**, and `weatherDrawn=` should print the
counts so the mix is auditable rather than assumed. Consequence, and it is the
important one: **overcast is our DEFAULT frame, so R0.c (bright overcast dome)
is not a side case — it is the main case**, and reference frame 3 is the
reference that matters most to us.

**R-B3 — SODIUM NIGHT.** British street lighting through the 80s and into the
90s was low-pressure sodium (SOX): **monochromatic at 589 nm, colour rendering
index 0** — it does not render colour at all
([Flagstaff Dark Skies](https://flagstaffdarkskies.org/low-pressure-sodium-lighting/),
[SOX lamp spec](https://normanlamps.com/low-pressure-sodium)).
Under it, a red car and a green door are the same amber-grey. This is a gift:
it is a period marker, a mood, and a *simplification* all at once.
Rule: under street-lamp illumination, chroma collapses toward hue ~40–50° —
check it with the §1 probe restricted to lamp-lit pixels, requiring
`hueArc60 >= 0.85` and `hueArcAt` in 35°..55° on night stills. Our night frames
currently read `satOver60` up to 0.383 and blue-dominant, which is the opposite
of a sodium street. **[inference]** on the exact bounds — set them from a night
series once the lamps are sodium-tinted; the CRI-0 physics is sourced.

### The materials and the accents

Sourced: regional brick is the defining British surface — iron-rich clays give
the **red and orange** of northern terraces (Accrington red is named), chalk-rich
clays the **buff and yellow** London stock, "and when people picture it, they
picture the blackened surface after 100 years of pollution"
([Imperial Bricks regional guide](https://www.imperialbricks.co.uk/guidance/uk-brick-colours-regional-guide/),
[Building London on stock brick](https://buildinglondon.blog/2022/07/12/41-londons-canary-yellow-stock-brick/comment-page-1/),
[Reclaimed Brick Company](https://reclaimedbrickcompany.co.uk/blogs/yard-display/georgian-victorian-bricks)).
Roofs are **Welsh slate, dark grey to black**. **Pebbledash render** enveloped
the facades of humble terraced houses in the late 20th century
([Building Conservation](https://www.buildingconservation.com/articles/pebbledash/pebbledash.htm)).

Street furniture, with the colours specified rather than described:
- **K6 telephone box** — the commonest British kiosk, introduced 1935, painted
  **BS381C red 538** ([The Telephone Box](http://www.the-telephone-box.co.uk/),
  [Culture Wikia](https://culture.fandom.com/wiki/Red_telephone_box)).
- **Belisha beacon** — "a yellow-coloured globe lamp atop a tall black and white
  striped pole" at pedestrian crossings, national since 1934
  ([Belisha beacon](https://en.wikipedia.org/wiki/Belisha_beacon)).
- **Pillar boxes** — 800 types, each carrying the reigning monarch's cypher
  ([Historic England, street furniture](https://heritagecalling.com/2022/01/21/from-lamp-posts-to-litter-bins-the-stories-behind-englands-street-furniture/)).

**R-B4 — THE ACCENT BUDGET.** The British street is a low-chroma field —
brick, render, slate, tarmac, soot — punctuated by a very small number of
**mandated, identical, high-chroma objects**: pillar-box red, Belisha yellow,
and (period) sodium amber. That is 60-30-10 handed to us by the Post Office.
Rule: emit `accentPx` = fraction of frame at S>0.6, **required to be non-zero
and under the reference ceiling of 0.078** (`satOver60`, reference max). Today
our daylight stills run 0.006–0.041 — inside the ceiling but with the chroma
in the wrong arc (R-C1). **[inference]:** the accent objects are also the
cheapest possible content — a red box is a primitive — and they are worth more
per polygon than anything else on the list, because they are unmistakable.

**R-B5 — WET GROUND IS THE BRITISHNESS MULTIPLIER. [inference]**, but it follows
from R-B2: if most daylight hours are wet or recently wet, the ground is a
partial mirror most of the time. Wet tarmac converts a flat ground plane into
a source of vertical smear-reflections of everything above it — which is
simultaneously the cheapest available "surface history", the cheapest depth
cue, and correct for the setting. `WetReflections` exists in the repo. Gate:
ground-band tonal spread (R2's existing gate) under wet, plus `wetFrac` on the
done line.

### What to avoid, stated as a check

**[inference]**, from the reference decomposition in `visual-bar-spec.md` §2 and
the material sources above: fire escapes, hydrants, yellow school buses, stop
signs, overhead wooden utility poles carrying power to houses, wide setbacks,
and palm-scale street trees are all American tells. British equivalents:
**drainpipes** (the vertical line on every rear elevation), chimney stacks with
pots, TV aerials, **double yellow lines**, sodium lanterns on swan-neck steel
columns, railings, wheelie-less metal dustbins, and the dock kit — containers,
pallets, rope bollards, crane silhouettes. Checkable as a prohibited-prefab list
in `prop-reach`: `bannedPlaced=0` with `bannedChecked=N` beside it.

---

## 5. SMALL TEAMS THAT HIT A HIGH BAR — what they did instead of manpower

**Playdead, INSIDE — "Low Complexity, High Fidelity".** Lighting authored as
separate diffuse, specular and bounce entities; analytic primitive-based ambient
occlusion rather than geometric; local shadowed volumetrics; screen-space
reflections; and **dithering specifically so that subtle art detail is not lost
to colour banding**
([GDC session, archived](https://archive.org/details/GDCEU2016Gjoel),
[GDC Vault](https://www.gdcvault.com/play/1023002/Low-Complexity-High-Fidelity-INSIDE)).
**What was load-bearing:** the *atmosphere* systems (fog, volumetrics, water),
not the asset count. **What was sacrificed:** geometric and texture complexity
almost entirely — the title of the talk is the strategy.

**The Astronauts, The Vanishing of Ethan Carter.** Photogrammetry, at a time
when almost no indie and few AAA studios used it: ~40–50 photographs per object
through Agisoft Photoscan, giving geometry and texture together. Their own
framing: they scanned so that players "stop seeing assets and start seeing the
world"
([The Astronauts blog](https://www.theastronauts.com/2014/03/visual-revolution-vanishing-ethan-carter/),
[PC Gamer](https://www.pcgamer.com/find-out-why-the-vanishing-of-ethan-carter-is-so-ridiculously-good-looking/)).
**Load-bearing:** real-world surface irregularity, obtained by capture rather
than by labour. **Sacrificed:** authorial control of every surface, and they
inherited baked lighting they had to fight.
**For us:** photogrammetry is closed (no camera, no site), but CC0 scan
libraries are the same asset class, and R-C4's albedo validation is precisely
the de-lighting discipline that class requires.

**Campo Santo, Firewatch.** Two GDC talks on translating a bold 2D graphic style
into 3D with a tiny art team, explicitly about how small art teams should spend
their time
([GDC 2015](https://archive.org/details/GDC2015Ng),
[GDC 2016](https://archive.org/details/GDC2016Ng)).
**[inference]**, since the talk video is not fetchable from this container: the
strategy is stylisation-as-constraint — pick a look whose rules are cheap to
satisfy everywhere, then satisfy them everywhere. That option is **closed to us
by decision**: Jafar set the bar at GTA V photoreal-ish, twice.

**The Chinese Room** is the closest parallel available and it is a British one.
*Everybody's Gone to the Rapture* recreated a Shropshire village in **1984**;
*Still Wakes the Deep* a Scottish oil rig in **1975**, built on three stated art
pillars — "Making it Personal", "Authenticity", "A Terrible Beauty" — with the
team interviewing rig engineers and working from BP's documentary archives, and
an art director who had lived in 1970s Scotland
([Wikipedia](https://en.wikipedia.org/wiki/Still_Wakes_the_Deep),
[GamingBolt on the art direction video](https://gamingbolt.com/still-wakes-the-deep-developer-discusses-world-building-art-direction-and-more-in-new-video),
[Rapture](https://en.wikipedia.org/wiki/Everybody%27s_Gone_to_the_Rapture)).
**Load-bearing: period research as a production input, not as flavour.** They
converted archive access into asset lists. That is directly copyable and costs
nothing but reading — the equivalent here is a named period-marker list per
district feeding the placement rules, which §4 begins.

**The one that is actually our shape.** None of the four had our constraint
(no artist at all, everything automated). The nearest analogue in the sources is
procedural set dressing with **rule assets, placement layers and exclusion
volumes**, where "a solo developer or two-person team can populate kilometres of
terrain that would otherwise require an environment art team of five or more"
([StraySpark](https://www.strayspark.studio/products/procedural-placement-tool)).
**[inference]:** our advantage is that a rule applied to seven districts is the
same work as a rule applied to one, and our disadvantage is that a rule applied
everywhere is *visible* everywhere — which is why R-V4's "areas of rest" and the
repetition work in §6 are not polish, they are the tax on the method.

**What everyone sacrificed, and it is the same thing four times: variety of
approach.** Each picked a narrow band of technique and drove it to the end.
**[inference]:** the failure mode for us is the opposite — a wide, thin spread
of half-landed techniques, which is exactly what `visual-bar-spec.md` §3's
scorecard describes.

---

## 6. THE 80/20 OF "LOOKS EXPENSIVE" — ranked

Ranked by **visible impact per unit of work for THIS project at HEAD**, which
means a cheap fix to a totally-failing dimension outranks an expensive fix to a
partly-working one. Sourced where a source exists; the ordering is
**[inference]** and it is mine.

| # | do this | why it is here | cost | check |
|---|---|---|---|---|
| **1** | **Fix the value inversion** (R-V1, R-V2) | totally separated from the references on two independent statistics, 7/7 and 5/7; nothing else can be judged until it lands | already in flight (R0) | `skyOverGround>=1.35`, `v3which!=mid` |
| **2** | **Albedo validation at ingest** (R-C4) | one offline Python pass over every fetched texture, no CI round trip, fixes the root cause of asset clash rather than masking it | ~half a day, local | `texturesClamped/texturesExamined` |
| **3** | **Palette arc + saturation shape** (R-C1, R-C3) | near-total separation (amber 30–50° vs our blue 220–230°); the fix is grade/ambient parameters, not content | hours, one build | `hueArcAt`, `hueArc60`, `satP50`, `satP99` |
| **4** | **Temperature separation** (R-C2) | totally separated — refs never below 0.079, we never above 0.060 — and it is what makes a surface read as lit rather than tinted | one build | `abs(warmSplit)>=0.079` |
| **5** | **Contact darkening everywhere** (AO/vertex-bake, §7.2 of the spec) | "the visual improvement from contact shadows under furniture, characters and vegetation is significant… almost always worth keeping on" ([SuperRenders](https://superrendersfarm.com/article/ambient-occlusion-explained-ssao-hbao-gtao-2026)); reference frame 3 carries an overcast street on contact darkening alone | build-time bake, zero runtime | existing AO gate + a paired still |
| **6** | **Sun elevation clamp + weather mix** (R-B1, R-B2) | two parameter changes that convert the whole game's light from generic to British, and make overcast the case we tune | ~an hour | `sunElevNoon<=59`, `weatherDrawn` counts |
| **7** | **Surface history on the ground** (spec R2) | the reference decomposition's #1, and `GROUND PATCH surface` is below every reference on five of seven stills | large, content | ground-band tonal spread |
| **8** | **Street density with three size tiers and rest** (R-V4, spec R3) | 47-model kit with one model placed; density is what the references never lack | large, mostly automatable | props-per-50m by tier |
| **9** | **Sodium night** (R-B3) | period-correct, mood, AND a simplification of the hardest lighting case | small | night `hueArc60`, `hueArcAt` |
| **10** | **Texel density banding** (R-C5) | real, and invisible until 1–9 are done | medium | px/m distribution |

**Below the line, deliberately:** resolution, polygon counts, shadow map size,
reflection quality. **[inference]:** every one is a knob that improves a frame
that is already correctly composed and cannot rescue one that is not — and our
frames are not.

---

## 7. WHAT THIS MEANS FOR THE INSTRUMENT

Six additions to `tools/ref-bench.py`, all computed identically on refs and
stills, all cheap (numpy + PIL, both present; no cv2, no scipy):

    skyBandP50 / wallBandP50 / groundBandP50 / skyOverGround   R-V1
    v3dark / v3mid / v3light / v3which                          R-V2
    hueArc60 / hueArcAt / chromShare                            R-C1
    warmLit / warmShadow / warmSplit                            R-C2
    satP50 / satP99 / satOver60                                 R-C3, R-B4
    (night variants of the hue arc, lamp-lit pixels only)       R-B3

Instrument discipline, per `.claude/rules/instruments.md`:
- Each key names the statistic it is: `skyOverGround` is a ratio of two medians
  **of one decode**, so numerator and denominator are the same instant by
  construction — the failure mode §2 of CLAUDE.md documents cannot occur here.
- `v3which` is a WORD; emit the three shares as `v3=0.296/0.383/0.321`, never
  with spaces.
- `hueArc60` needs a denominator: when fewer than 200 chromatic pixels exist the
  probe must print `hueArc60=nochroma` rather than a number, or a black frame
  reads as a perfectly disciplined palette.
- These are per-still numbers and belong on the per-still line, never the done
  line.
- Every bound above is a reference EXTREME, printed in §1 with the full series
  beside it. When the series changes regime — R0 landing will change all of
  them — the series takes a regime mark and the bounds are re-read, not nudged.

---

## 8. REJECTED — measured and did not separate, or could not be made checkable

Recorded so nobody re-derives them as promising. All **[measured]** on the same
5 refs + 7 stills.

| candidate | result | why it failed |
|---|---|---|
| notan **evenness** (entropy of the 3-value split) | REF 0.877–0.997, SIM 0.778–0.995 — total overlap | photographs of real streets are not tidy three-value designs; only WHICH group dominates separates (R-V2), not how unevenly |
| `v3dominant` (largest group's share) | REF 0.370–0.568, SIM 0.379–0.639 — overlap | same reason |
| detail-scale ladder (std at 1:2, 1:8, 1:32) | fine/big ratio REF 1.058–1.204, SIM 1.104–1.212 — overlap | luma std at three downsample levels is dominated by overall contrast, not by shape hierarchy. R-V4 uses placement data instead |
| screen-space aerial perspective (`lcNearOverFar`) | REF 0.340–0.846, SIM 0.167–0.994 — overlap | the band split is confounded by composition, not depth. Replaced by R-V3's depth-buffer version |
| ground autocorrelation for tiling (`tileAuto`) | 0.837–0.989 everywhere | autocorrelation of raw luma is dominated by the low-frequency lighting gradient. Would need a high-pass pre-pass; untested, so it is a hypothesis, not a metric |
| clipping (`clipHi`, `clipLo`) | both ≤0.004 on refs, ≤0.002 on ours | we are not clipping. A real check that we happen to pass — keep it as a guard, do not spend on it |
| `deepDark` (share below luma 0.10) | REF 0.003–0.172, SIM 0.021–0.077 — inside the reference range | our frames DO have dark pixels; the problem is where they are, not whether they exist |

**And one honest caveat about the whole exercise.** `ref-bench.py`'s own
docstring says it, and it applies to every number here: this is a steering
proxy, not a quality score. Two frames can share all fourteen statistics and
share no quality. Nothing above knows what a chimney pot is. **The judge is
Jafar with our frame beside his frame** — these rules decide which build is
worth his minute.

---

## 9. The probe, for folding into `ref-bench.py`

Written and run this session; kept out of `tools/` deliberately, because a
second instrument beside `ref-bench.py` is the "one idea, two implementations"
fault CLAUDE.md rule 1 warns about. The metric bodies to lift:

- **band medians**: rows `0..0.20H` sky, `0.20..0.65H` wall, `0.65H..H` ground,
  medians of Rec.601 luma; `skyOverGround` = sky ÷ ground, guarded at zero.
- **three-value split**: fixed cuts at 0.25 and 0.60 on display luma; emit the
  three area shares and the argmax as a word.
- **hue arc**: HSV hue of pixels with S>0.15, 36-bin circular histogram, sliding
  6-bin (60°) window, take max; the arc centre is the reported `hueArcAt`.
  Refuses with `nochroma` below 200 qualifying pixels.
- **warm split**: `mean(R−B)` over pixels above the 75th luma percentile minus
  the same over pixels below the 25th. One decode, one frame, both quartiles
  from the same pixels.
- **saturation**: HSV S, median / 99th percentile / share above 0.60.

Accepting case for the selftest, per the house rule: the five reference frames
must all pass R-V1, R-C1, R-C2 and R-C3, since the bounds are their own extremes
— if any reference fails its own bound, the arithmetic changed and the tool is
wrong, not the game. Rejecting case: a synthetic flat mid-grey frame, which must
come back `hueArc60=nochroma` and fail R-V1 rather than reading as disciplined.
