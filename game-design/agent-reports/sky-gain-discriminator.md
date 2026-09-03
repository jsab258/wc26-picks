> **STATUS: LOG, 2026-08-26. NOT CURRENT after the first build that lands `skyGain*`.**
> The instrument is built, wired and locally selftested. **NO RUN HAS CARRIED IT YET.**
> Every number here is either LANDED (read off `c03ead2`'s verdict or computed by the
> shipped `Core` on this tree) or a PREDICTION. Nothing is a reading from the new key.

# The sky-gain discriminator — rendered-over-authored, per band, per elevation

## What the sky's authored value actually is, and how I found it

It is **not a scalar**, and the instrument refuses to pretend otherwise.

I found it by opening the chain rather than by grepping for a constant.
`SceneLighting.ApplyOnce` builds one material from `Hidden/LedgerSky` and
`SceneLighting.LateUpdate` writes its stops every frame:

    _sky.SetColor(_SkyColor,     C(LightModel.SkyColour(night, rain)))
    _sky.SetColor(_HorizonColor, RenderSettings.fogColor)   // == C(LightModel.FogColour(...))
    _sky.SetColor(_GroundColor,  C(LightModel.GroundColour(night, rain)))
    _sky.SetColor(_CloudColor,   <derived from the zenith, lerped to sodium at night>)
    _sky.SetFloat(_CloudCoverage, deck)      // seeded off the CALENDAR DAY, not off rain alone
    _sky.SetFloat(_SunGlowAmt,   f(dusk, night, rain))

and `LedgerSky.shader` blends them by view elevation:

    up = pow(saturate(h), _SkyCurve);  dn = pow(saturate(-h), _GroundCurve)
    c  = lerp(_HorizonColor, _SkyColor, up);  c = lerp(c, _GroundColor, dn)
    then clouds toward _CloudColor by (noise * up * 0.85), then an ADDITIVE sun glow

**Three things fell out of reading it that change how the question is asked:**

1. **The dome's horizon stop is the FOG colour, not `HorizonColour`.** The shader's
   own comment says why (the skybox is not fogged, so any other horizon colour puts a
   seam where fogged brick meets sky). Anyone hunting "the sky is dark" in
   `LightModel.SkyColour` is looking at the wrong function for every camera that is
   not pointing up.
2. **The gradient is almost flat where our cameras look.** Computed by the shipped
   `Core` on this tree (`LightModel` + `SkyGain.DomeLuma`, linear luma, dry noon):

       elev  -5.0  0.1629      elev  10.0  0.1890
       elev   0.0  0.1640      elev  20.0  0.2434
       elev   2.0  0.1656      elev  45.0  0.4369
       elev   5.0  0.1717      elev  90.0  0.6559

   From the horizon to ten degrees up, the authored sky moves **15%**. A street camera
   is sampling the fog colour with a rounding error on top.
3. **`cover` varies inside a weather tag and the three colour stops do not.** `deck` is
   hashed off `TodayNumber`, so two dry noons on different days wear different cloud
   decks. The instrument prints `lo..hi` per stop for exactly this reason, and a spread
   appearing on `top`/`hor`/`gnd` is an alarm about the tag, not about the sky.

So `skyDomeBy` prints **six numbers per regime plus `live<n>/<shots>`**, and the
per-ray denominator is built from them by elevation. A single "the sky is authored at
X" would have been a number invented to make a division possible.

**Authored dome stops, linear luma, from the shipped `Core` (not from a reimplementation):**

| regime | top (zenith) | hor (= fog) | gnd (below) | exposure |
|---|---|---|---|---|
| dry noon `n0.00 r0.00`  | 0.6559 | 0.1640 | 0.1444 | 3.440 |
| wet noon `n0.00 r0.90`  | 0.6549 | 0.1473 | 0.1443 | 2.983 |
| dry night `n1.00 r0.00` | 0.0049 | 0.0185 | 0.0037 | 0.860 |

## What is built

**`ledger/Assets/Scripts/Core/SkyGain.cs`** — the tally, the arithmetic and every
string, in Core so CoreTests runs it. **No bound, no gate, nothing compares against a
constant.** Fed from the ray loop already in `SimDirector.ValuePanelRead` — I did not
write a second ray grid; I restructured the existing one so the band decision is made
once and **both tallies are fed by one statement per ray**.

Supporting changes:

* `SimDirector.UngradedTwin(cam, w, h)` — the `FilmGrade.Bypass` render **hoisted out
  of `GroundMaskRead`**, which used to own the only copy. It now runs **once per
  committed still** and is handed to both readers. Two renders would have given the
  ground tally and the sky tally two *different* ungraded photographs of one instant
  (the grain is reseeded per frame), which is the pairs-of-maxima fault with a new
  face. It also dropped to `Color32` — byte-exact on an RGB24 readback, a quarter of
  the allocation, and it now runs on ~23 stills rather than 7.
* `ValuePanel.WeatherTag` made **public** (visibility only, format unchanged) so
  `SkyGain.RegimeTag` calls it instead of carrying a second copy.
* `AssetLibrary.SourceAlbedoOf` — `GroundSourceAlbedo`'s body, which never had a line
  of ground-specific logic in it, under a name that does not claim a facade is a road.
  The old name delegates. One implementation, two names.

### The keys, and what statistic each number is

| key | what it is |
|---|---|
| `skyGainShots` | measured / offered / **with-an-ungraded-twin** / **with-a-live-dome**. `0/19/0/0` and `0/0/0/0` cannot print alike. |
| `skyGainRays` | `sky/lit/gnd/shd/oth/of<total>` — cumulative band counts, the denominator of every mean. |
| `skyGainListed` | shown/total for the capped band list. |
| `skyDomeBy` | per regime: the six authored dome numbers, each `x` or `lo..hi`, plus `live<n>/<shots>`. |
| `skyGainBands` | per regime × band: `gr`/`rw`/`sc` are **RAY-WEIGHTED MEANS in LINEAR**; `xgrade`, `xsrc`, `xrawsrc` are **RATIOS OF MEANS**; `vig` is the ray-weighted mean of `LightModel.VignetteAt`; `@n/rn/sn` are the three denominators. |
| `skyGainElevOf` | which regime the ladder is over and how many sky rays it stands on. |
| `skyGainElevRegimes` | every regime's sky-ray count — the denominator for that choice. |
| `skyGainByElev` | the ladder: the same columns per elevation rung, over the one named regime. |

Not medians. `valueBands` prints display-referred **medians per shot**; this prints
linear **means over a regime**. Same rays, same instant, different space and different
statistic — they may not be quoted as one reading, and the class note says so.

## The discriminator, and which reading means which

Two columns, and they move opposite ways:

* **`xgrade` = graded / raw, per band.** Numerator and denominator are the same rays of
  the same scene at the same instant with one pass toggled, so every scene-referred
  term cancels and **only the common path is left**. This is the column that may be
  compared ACROSS bands.
* **`xrawsrc` = raw / source, per band.** On `sky` the source is the dome colour the
  material held at that ray's elevation, and the dome is an emission with no lighting
  in it — so on the raw arm this is a **pure transfer with a known expected value of
  1.000**. On `lit`/`gnd`/`shd` the same column is the irradiance and has no expected
  value. **That asymmetry is the discriminator.** A sky row and a ground row may not be
  compared on it, and the code says so at the emit.

| reading | meaning |
|---|---|
| sky `xrawsrc` ≈ 1.000 **and** `xgrade` even across bands | the dome renders what it was authored and the path is even-handed ⇒ **(b), the authored VALUE is the subject**, and the address is the fog-coloured horizon stop the low rungs sample |
| sky `xgrade` far **below** gnd's and lit's | **(a), and sky-specific** — the common path is not common |
| sky `xrawsrc` far from 1.000, **flat** across the ladder | a scalar sitting on the dome alone |
| sky `xrawsrc` far from 1.000 and **climbing** with elevation | a power law, not a scalar — the signature of a colour-space conversion applied twice (or not at all) between `SceneLighting.C()` and the shader. **Suspect the plumbing, not the art**; the fix is at the funnel, not at `LightModel.SkyColour` |

**Note the director's stated shape, and where I departed from it, deliberately.** The
brief said "sky-gain ≈ ground-gain ≈ wall-gain ⇒ the common path". Read against the
code, `rendered/albedo` on a geometry band **contains the whole irradiance** and the
sky's contains none, so those three can never be equal and their inequality would prove
nothing. The comparison that carries the director's intent honestly is **`xgrade`**,
which is irradiance-free on every band by construction. `xsrc`/`xrawsrc` still ship —
they are what makes the sky's 1.000 identity readable — with the asymmetry named at the
emit so a reader cannot pick a conclusion from them.

## The prediction, written before the run

**THE IDENTITY THAT MUST BALANCE.** `skyGainRays`' five band counts equal `valueRays`'
five band counts **on the same run**, and `skyGainRays`' `of` equals `valueRays`' first
field. They are fed by one statement in one loop over one ray grid. On `c03ead2`
`valueRays=52992/44770/44245/sky8222/lit4843/gnd18654/shd12964/oth8309`, so the shape
to check is `skyGainRays=sky8222/lit4843/.../of52992` **against that run's own
`valueRays`**, not against these numbers — the sim is not frame-identical across builds.
Also internal: the five counts must sum to `of`.

**THE NUMBERS.** Dry noon, ladder regime `r0.00w0.00n0.00`, ~5,000 sky rays:

1. **`xgrade` on `gnd` lands 3.3–4.3.** LANDED arithmetic, not a guess:
   `groundGainBy` asphalt 0.4773 over `groundGainByRaw` asphalt 0.1231 = **3.88**,
   concrete 4.21, sidewalk 4.10, kerb 3.31. If the new key's `gnd` row lands outside
   that band, it is reading a different population or a different space — read alarm 1
   before reading anything else.
2. **`xgrade` on `sky` lands within a factor of ~1.5 of `xgrade` on `gnd`.** I predict
   the common path is even-handed and **(a) is NOT the answer.**
3. **`xrawsrc` on `sky` at rungs `e00..02`/`e02..05` lands WELL BELOW 1.000 — I predict
   0.10..0.40.** The arithmetic behind the prediction: the landed *graded* district sky
   is 0.1115–0.1626 linear, which is already at or below the authored horizon stop of
   **0.1640** — so for a path that multiplies the ground by ~3.9, the raw sky has to be
   roughly a quarter of what was written into the dome.
4. **It CLIMBS up the ladder rather than staying flat.** If the cause is a second sRGB
   conversion, `xrawsrc = lin(a)/a`, which computes to **0.141 at rung 1 (a=0.164),
   0.363 at 45° (a=0.4369), 0.593 at the zenith (a=0.6559)** — a factor 2–3 across the
   ladder. If it is a scalar on the dome, every rung reads the same number. **These two
   are the same key on the same line and cannot both be true.**
5. **`vig` on `sky` lands 0.72–0.90 and on `gnd` near 0.95.** The vignette is real and
   is printed so it is ruled in or out by a number: `LightModel.VignetteAt` gives
   **x1.000 centre, x0.854 top-centre, x0.720 corner** at noon. It is a contributor of
   ~15–28% and **cannot account for a factor of four** — named here so nobody reaches
   for it as the explanation.
6. **`skyGainByElev` on the wet and night regimes is NOT laddered** and
   `skyGainElevRegimes` will show the dry-noon regime with several times the sky rays of
   any other. The reading is dry-only by construction: the ladder is one named regime,
   and every band row carries `r..w..n..`.

**THE ALARMS, each saying which way to suspect.**

1. **INSTRUMENT, NOT SUBJECT** — `xrawsrc` on any GEOMETRY band clustering near
   **2.05..2.09**. That is `GroundGain`'s written-down gamma/linear signature: one side
   of the division skipped a conversion. Settle it before reading the sky row at all.
2. **INSTRUMENT, NOT SUBJECT** — `skyGainRays` disagreeing with `valueRays` on any band.
   One statement feeds both; a disagreement means the ray site was edited so the two
   tallies see different rays, and every mean here is then over an unknown population.
3. **INSTRUMENT, NOT SUBJECT** — `skyGainShots`' third field reading 0 (`23/23/0/23`).
   No ungraded twin means every `xgrade` prints `none` and leg one of the discriminator
   is simply absent. Grep `errors` for `UngradedTwin:` — this is a render failure, not a
   fact about the sky.
4. **INSTRUMENT, NOT SUBJECT** — `skyDomeBy` printing a spread (`lo..hi`) on `top`,
   `hor` or `gnd` inside one regime tag. Those three are deterministic in (night, rain)
   and MUST be constant inside a tag; a spread means the tag is not the regime it claims
   to be. (`cover` printing a spread is correct and expected — it is seeded per day.)
5. **INSTRUMENT, NOT SUBJECT** — sky `xrawsrc` **and** sky `xgrade` both reading 1.000
   to three decimals. That is the bypass render not bypassing, or both arms reading one
   pixel array.
6. **SUBJECT, NOT INSTRUMENT** — `skyDomeBy` reading `live0/<shots>`. Then
   `Hidden/LedgerSky` never loaded, the camera cleared to a flat fog-coloured card, and
   the ladder will be **flat by construction** because the authored value really is one
   colour at every elevation. Severe, real, and named in advance so the flat ladder is
   not read as a broken instrument.

## Selftest — both cases, output pasted

**ACCEPTING FIRST.** The fixture is shaped like a real dry noon: three sky rays at two
elevations, one sunlit wall, two road rays carrying the real asphalt/kerb albedo
spread, one `other`, and **nothing in shadow** — the case that must print the words.

```
Sky gain — rendered over authored, per band and per elevation:
  ok - a real dry-noon tally prints its four band rows exactly
  ok - xsrc is a ratio of means, not a mean of ratios
  ok - the band ray counts add up on the printed line
  ok - measured/offered/with-twin/with-dome
  ok - the band list shows every row it has
  ok - the ladder names its regime and its sky-ray count
  ok - every regime's sky-ray count is the ladder choice's denominator
  ok - the ladder prints every rung, including the empty ones
  ok - the authored dome prints its six numbers rather than a scalar
  ok - no verdict value carries a space           [x8, one per emitted key]
  ok - straight up is the zenith stop
  ok - the horizon is the horizon stop
  ok - straight down is the ground stop
  ok - the sky curve keeps the horizon band broad
  ok - the mirrored gradient climbs with elevation [x19, 0..90 deg in 5s]
  ok - every rung of the ladder is reachable and in order
  ok - a run that never measured prints the words on every row
  ok - never-ran prints zero over zero, not a clean-looking zero
  ok - nineteen shots offered and none landed is not the same as never running
  ok - a shot with no ungraded twin prints the words, not a zero
  ok - the with-twin denominator is what makes that legible
  ok - a shot with no dome read prints the words on every ratio that needed it
  ok - and the dome row says so rather than printing zeros
  ok - the live-dome denominator separates a flat card from a dark dome
  ok - a source of zero says source0 rather than printing a huge gain
  ok - unknown weather prints the words
  ok - an unknown hour prints the words
  ok - and a known one is ValuePanel's tag with the hour on the end
  ok - the weather half is ValuePanel's own, called and not copied
  ok - a dry noon and a dry midnight land in different regimes
  ok - the regime with the most rays is printed first
  ok - the band cap announces when it bites
  ok - and the listed count carries the same fact as a pair
  ok - a stop that moved inside its regime prints lo..hi and one that did not prints one number
```

**REJECTING — and I ran it against my OWN probe rather than a synthetic fixture,
because a validator nothing survives is the expensive failure.** One denominator
changed from `sn` to `sn + 1` — the smallest wrong-denominator bug this class can have:

```
Sky gain — rendered over authored, per band and per elevation:

FAILED: a real dry-noon tally prints its four band rows exactly — [r0.00w0.00n0.00@sky:
gr0.2200/rw0.0553/sc0.1570/xgrade3.976/xsrc1.401/xrawsrc0.352@n3/rn3/sn3/vig0.867,
r0.00w0.00n0.00@lit:gr0.6800/rw0.1800/sc0.0750/xgrade3.778/xsrc9.067/xrawsrc2.400@n1/rn1/
sn1/vig0.920,r0.00w0.00n0.00@gnd:gr0.4600/rw0.1250/sc0.0053/xgrade3.680/xsrc86.250/
xrawsrc23.438@n2/rn2/sn2/vig0.950,r0.00w0.00n0.00@shd:nothing_measured@n0/rn0/sn0]
```

Note what the break did and did not move: `xgrade` is untouched (it does not use `sn`)
while `xrawsrc` on the sky went 0.264 → 0.352 and on the ground 15.625 → 23.438. **A
reader with only the sky row would have read the broken build as a healthier sky.**
The break has been reverted and the tree runs clean.

## The first real series, from the live project

`skyGain*` has not run. What the live project can be made to say **today** is the two
halves the new key divides, read separately off `c03ead2`.

**LANDED — the graded and ungraded ground, `groundGainBy` / `groundGainByRaw`:**

| material | source albedo | raw (ungraded) | graded | graded/raw |
|---|---|---|---|---|
| asphalt  | 0.0075 | 0.1231 | 0.4773 | **3.88** |
| sidewalk | 0.0205 | 0.1092 | 0.4473 | **4.10** |
| kerb     | 0.0670 | 0.1702 | 0.5632 | **3.31** |
| concrete | 0.0199 | 0.1121 | 0.4725 | **4.21** |

**This overturns a conclusion already in circulation.** "The ground is albedo-blind" has
been read as a grading problem. It is not: an **8.9x** source spread (0.0075 → 0.0670)
is already flattened to **1.38x** in the *ungraded* render, before `FilmGrade` touches
anything. Whatever blinds the road to its own albedo is **upstream of the grade**, and
the raw ground luma (0.109–0.170) sits on top of the authored fog-colour stop, **0.1640**.
That is a lead, not a finding — `skyGainBands`' `gnd` row over every dry shot is the
number that tests it against the seven district shots `groundGainBy` is limited to.

**LANDED — the sky band, `valueBands`, dry rows only, converted to linear:**

| camera family | display sky | linear sky | authored dome at the elevations they sample |
|---|---|---|---|
| 7 district (14m eye, ~20° down) | 0.368..0.440 | 0.1115..0.1626 | ~0.164 (the horizon stop) |
| 5 ref (1.7m eye, ~5° down)      | 0.591..0.696 | 0.3081..0.4423 | ~0.164..0.24 |

The district family's *graded* sky already sits **at or below the authored value**. That
single comparison is what the whole prediction hangs on.

**Two more existing conclusions this work touches:**

* `LightModel.VignetteAt` and `LightModel.VignetteParam` sat on the ReachCheck allowlist
  as **"BY DESIGN … the gate's model of it"** — modelled, never called. `VignetteAt` now
  has a live consumer at the ray site. Both entries are deleted; `reach-check` reported
  them **PAID OFF** and now reads `reach ok — 33 on the ledger, 0 unexplained`.
* `GroundMaskRead`'s comment claimed the bypass render "runs on seven" shots. True when
  written; it is now shared and runs on every committed still. The comment moved with
  the code rather than being left behind to be quoted forward.

## What is NOT done, named rather than left to be discovered

* **Nothing has run.** Every prediction above is unlanded. The Game layer does not
  compile in this container and no local tool renders a frame, so the Unity API surface
  in the ray-site rewrite (`RenderSettings.skybox`, `Material.GetColor/GetFloat`,
  `Camera.backgroundColor`, the `Color32` readback) is first compiled by the Windows
  build. ShapeCheck is reference-independent and passed: `Game layer compiles (186 files)`.
* **`DomeLuma` does not model the cloud layer or the sun glow.** Stated at the function.
  Both fade to nothing at the horizon (`up`, and `smoothstep(0,0.10,h)`), so the low
  rungs the street cameras sample are the rungs the mirror is exact on; the high rungs
  carry the omission and `cloud`/`cover`/`glow` on `skyDomeBy` are its size.
* **No bound, no gate, no threshold anywhere.** One landing is not a series.
* Band rows are ordered by admitted rays descending so the cap cannot bite the row with
  the most evidence in it. That ordering is a decision about the cap and it is argued at
  the method rather than here.

## Residual, named

`verify` reports `1075 verdict keys, 115 new (run --learn)` — informational, not gated.
The eight `skyGain*`/`skyDomeBy` keys are among the new ones. Learning them writes a
tracked file, so it is the resident's call at commit time, not mine.

## Files

* `ledger/Assets/Scripts/Core/SkyGain.cs` — new
* `ledger/Assets/Scripts/Core/ValuePanel.cs` — `WeatherTag` public, format unchanged
* `ledger/Assets/Scripts/Game/SimDirector.cs` — `UngradedTwin` hoisted and shared, ray
  site restructured to one filing statement per ray, `_skyGain`, `AuthoredLinearLuma`,
  eight emits
* `ledger/Assets/Scripts/Game/AssetLibrary.cs` — `SourceAlbedoOf`
* `ledger/CoreTests/Program.cs` — `TestSkyGain`
* `ledger/ReachCheck/allow.json` — two paid-off entries removed

## Verify footer

**Provenance, because it matters here.** The footer below was read from
`ledger/.verify-footer` **on disk**, written by the green run at 04:02Z, never from
scrollback. It describes the tree at `503 tracked` changed lines minus the last edit —
the `twinUsable` length guard added afterwards took it from 486 to 503 tracked, and
`verify` was re-run and exited **0** on that tree too.

**The footer file is not on disk right now and the reason is not mine.** At 04:05Z a
`studio-director` wrote `game-design/decision-2026-08-26-sky-discriminator-batch.md`
ruling on this batch, and its banner reads `**STATUS — LOG, 26 Aug 2026.` where
`tools/docs-check.py` matches `\*\*STATUS — LOG, (\d{4}-\d{2}...)`. That is the same
format mistake I made in this file and fixed; `docs-check` reports **exactly one
problem** and every other stage in the same run prints ok. A red run deletes the footer
by design, which is why it cannot be regenerated until that one date is written as
`2026-08-26`. **I have not touched it** — a builder editing the ruling record that
reviews its own batch is the spawn-row hole with better manners. One character, the
resident's or the director's to make.

My own two docs checks pass: `ok sky-gain-discriminator.md — LOG entry carries its
date` and `ok — LOG entry says it is not current`.


```
director cadence ok (1235 changed line(s) (503 tracked + 732 untracked in 1 new file(s)) vs 100
threshold under Assets/Scripts, over threshold, REVIEWED; 1 director row(s) newer than the
reference of 158 log row(s) examined; reference = code commit c03ead22@2026-08-26T02:11:15Z
(HEAD 2026-08-26T03:23:23Z is +3 non-code commit(s) later); rulingRecords=1/6 rulingFiles=7
rulingUnmatched=0 rulingRowsUnruled=0/1 rulingUnruledNewest=none — 1 ruling record(s) paired to
a director row newer than the reference, of 6 stamp(s) in 7 decision file(s) scanned; 5 stamp(s)
name a row at or before the reference (a ruling on an older batch)); fable spend, READING ONLY
(no bound, nothing here is gated): directorSpawns=1/11 fableShareDay=3/21@2026-08-26
fableShareAll=30/158 fableAgents=studio-director agentFilesRead=10 — COUNT of studio-director
rows over ALL spawn rows since that same reference commit / SHARE over the newest UTC day
present in the log / CUMULATIVE share over every log row [53/53 selftest fixtures], 40 footer-
string fixtures (accepting and rejecting), 0 lint errors (186 file(s) walked of 192 present; 6
file(s) of the 2 root(s) given went UNWALKED (Scripts/Editor)), 0 shape errors (192 files, 3
with conditional code), 0 shadowed Core types (287 Core type(s) across 88 Game file(s)), 15 tool
project(s) + 21 workflow-named tool(s) in 9 workflow(s) tracked, 33 on the reach ledger, shape
ok (23 clip(s) cast/23 probed, 42 bark slot(s)/2604 line(s), manifest paths nothing-measured of
1 path-shaped in 7 file(s)), voice cast ok (0 uncast of 7 tier-1 principal(s); 17 cast voice(s),
2 alias(es), 23 clip(s)), voice-gen ok (25 checks, 2010-line batch), barks current (2604 lines
enumerated, 0 drifted), voice-live ok (147 checks, 3 skipped without torch: stft_patch.py
fixture.py kv_cache.py), voice assets ok (4 checks, 23 voices stageable), voices-into-build ok
(16 checks), pc-watcher ok (23 checks), slop 87/88 (19 patterns, 4776 strings), 13 card-writing
rules, 60 cards shipped as edited, 40 probe calls staged (4 of 4 card(s) wanted, ids read from
ConvoProbe), 22 queue items ready, docs 117/117 clean, template sync DEFERRED (deferred to
playbook-sync-hybrid-resident, 4/4 sections, fingerprint 8e2fa98b9d793081, 25 fixtures), 16
attribution check(s), Game layer compiles (186 files), speech backend + bench compile, 0
unreachable behind #if (1 type(s) checked), 0 nested-type errors (256 Core types), 0
static/instance errors (75 members, 29 bodies), 0 raw avenue reads, 9 DEFERRED (186 files), 0
filename-as-type errors (192 files, 13 filenames that are not types), 0 namespace-as-value
errors (192 files, 4 segments in scope), workflow steps ok (17088 under the dispatch ceiling),
pwsh steps NOT CHECKED (no PowerShell — dotnet tool install --global PowerShell), sheet reader
ok (7 checks), prop reader ok (14 checks), prop reach ok, 228 model file(s) on disk minting 213
key(s) (15 shadowed by 12 key collision(s), last path wins), 74 key(s) named by the Game layer,
139 with no name match (4452 literal(s) scanned) [selftest 16 rung(s)], 108 ref-bench checks (0
failed), 42 decal-ink checks (0 failed) — 16 set(s), 2 unnamed, 40 frame-drift checks (0
failed), 1075 verdict keys, 115 new (run --learn), verdict format ok (selftest + newest run),
verdictSpaced=35/143 not gated, dupkeys ok (selftest); landed verdict: 16 same-line and 5 cross-
line ambiguous key(s) over 139 record line(s), 1 prose line(s) skipped, emit dupkeys ok (0, 112
log call(s) across 186 file(s))), runs map to commits (356 of 356 within 2405) — the whole
history, no window; expect all 356; unplaced=0; NOTE abbrev is 8 chars and run files are 7 —
compare by PREFIX, never by equality, gates 31 bare / 40 detailed, ceiling 31 [arithmetic:
31+40+0=71 table entries walked], 29 save-chaos checks, 3 soak checks (500 days x2), 84
adversary checks, 0 stale anchors (205 anchor(s) in 22 break spec(s)), clips ok (64 read, 2
known finding(s)), clip picker ok (65 shipped name(s) read, 64 accepted, posture screen 9
accepted/5 refused, 137 of 145 pattern(s) match a catalogued name), 4163 CoreTests.
```
