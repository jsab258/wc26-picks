# The first `groundGainBy` landing, verified — the rows are not ground

> **STATUS — LOG, 2026-08-25. NOT CURRENT** once the normal filter lands.
> Tier-2 verification of the `3a4e335` landing. Written to disk by the
> coordinator; the auditor is read-only by construction. This is the first
> use of the verifier-first rule: the position below is ESTABLISHED, and the
> director rules on it rather than re-checking it.

## The landing

    groundGainBy=[asphalt:0.5109/0.0075=68.121@1994,sidewalk:0.3908/0.0205=19.022@1121,
                  kerb:0.3289/0.0670=4.911@253,concrete:0.3148/0.0210=14.998@2673]
    groundGainOf=4/4  groundGainRays=6041/6041

Self-check passed exactly. All ratios equal their own numerator over their own
denominator within the print band; `@n` sums to 6041; all four keys on line 87.

## 1. THE ROWS ARE NOT GROUND — established

`AssetLibrary.cs:1007-1008` — `GroundSurfaceOf` is
`SurfaceNames.MatchOf(m.name, WetSurfaces)`: a material-NAME comparison with
**no geometry, normal, orientation or height test**. Anything wearing a name
in the family counts as ground.

| contaminant | anchor |
|---|---|
| building facades in concrete | `WorldBuilder.cs:1127`, `:2781` — `Concrete` is IN the facade array |
| the `mat_concrete_b` facade variant, collapsed into the same row | `SurfaceNames.cs:46` strips a trailing `_b` |
| roughly half the cars | `TrafficHost.cs:1025` returns `Concrete` for even ids, consumed `:566-567` |
| street furniture bars, into `sidewalk` | `StreetFurniture.cs:328` |

**`concrete` carries 2673 of 6041 rays — 44%, the largest bucket and the most
contaminated family.** The key's NAME claims ground; its CODE claims a string
match. Treat the concrete row as unreadable until filtered.

## 2. `MatAlbedo` IS NOT AT FAULT — established, and it was the leading suspicion

All four denominators reproduced offline from the raw pack JPEGs:

| texture | source sRGB luma | predicted | landed | pred/landed |
|---|---|---|---|---|
| asphalt | 0.2663 | 0.0088 | 0.0075 | 1.17 |
| sidewalk | 0.4272 | 0.0242 | 0.0205 | 1.18 |
| kerb | **0.7228** | 0.0701 | 0.0670 | 1.05 |
| concrete | 0.4202 | 0.0217 | 0.0210 | 1.03 |

`asphalt.jpg` really is a dark photograph and `kerb.jpg` really is a bright
one — **an 8x linear spread that is real art, not measurement error.** Colour
space Linear confirmed in code (`CiBuild.cs:42`); Standard shader; `mpb:unset`;
no `_DetailAlbedoMap` anywhere in the Game layer. The instrument's own
written tripwire — ratios near 2.05-2.09 mean a gamma mismatch — **did not
fire**; ratios are 4.9 to 68.

Residual flagged rather than hidden: asphalt and sidewalk are 17-18% off the
offline reproduction while kerb and concrete are within 5%. Candidates named:
`MeanTexLuma` blits to 8x8 relying on mip selection rather than a true box
mean; the landed denominator is a ray-weighted mixture over graded copies.
Four orders below the effect, so it changes no conclusion, but it is unexplained.

## 3. NO MULTIPLICATIVE MODEL SURVIVES — established

Ray-weighted fits over the four rows:

    r = k*s       (pure multiplicative)  k=13.76            R2 = -8.655
    r = A + b*s   (additive + gain)      A=0.478 b=-4.547   R2 =  0.393
    r = A         (albedo ignored)       A=0.394            R2 =  0.000

A pure gain is WORSE than ignoring albedo. The only model beating a constant
does so with a **negative** albedo coefficient, which is physically
impossible. **Constrained to b >= 0, the best fit is b = 0** — rendered luma
is best explained by a term that does not depend on source albedo at all.
The "gain" framing is wrong for all four rows.

## 4. THE THIRD TERM NOBODY NAMED — the numerator is POST-GRADE

`FilmGrade` runs exposure, an **ACES tonemap, bloom**, vignette and grain in
`OnRenderImage`, and the mask reads the frame that was encoded to the
committed JPEG. So the numerator is `tonemap(exposure x light x albedo) +
bloom + grain` and the denominator is a raw material constant. That is not a
lighting gain under any model.

**Bloom is additive and albedo-blind, so `rendered/albedo` explodes as albedo
falls — exactly the 68x-on-the-darkest-material signature.** The rendered
values encode to sRGB 0.742 / 0.658 / 0.609 / 0.597 (189/168/155/152 of 255):
near-white, where an ACES shoulder compresses hardest. Inference, medium-high.

`exposureCurve` fits linear-out ~ scale^1.146, slightly SUPER-linear,
consistent with bloom recruiting pixels as exposure rises — but measured at
whole-frame luma 0.05-0.17 while the ground sits at 0.31-0.51, a different
operating point, so it does not settle the ground question.

## 5. THREE CAUTIONS ON READING ANY OF IT

- **n=1.** `groundGainBy` has landed once in 350 kept runs. No series exists.
- **The noise floor is ~±4%** on rendered ground luma with NO lever moved
  (seven districts, `0d0ebd7` vs `3a4e335`; ground rays 6020 -> 6041). The
  kerb-vs-concrete 4% gap is INSIDE the noise and cannot be read.
- **`groundAlbedoBy` and `groundGainBy`'s denominators are NOT a cross-check
  on each other.** Different moment (done-time last-wins vs ray-weighted
  during the tour) and different population (one shared material vs every
  graded copy the rays hit). Concrete prints 0.020 and 0.0210 for this reason,
  not rounding.

## 6. CORRECTIONS TO THE COORDINATOR'S FRAMING

- "Rendered brightness is INVERSELY ordered against albedo" — **not
  established.** The ordering breaks between concrete and kerb. The
  defensible claim is DECOUPLING WITH ASPHALT AS A HIGH OUTLIER: three of
  four are flat within ±11% while spanning 3.27x in source albedo.
- "A uniform multiplicative term cannot produce that" — **established, and
  stronger than stated**: no multiplicative term with a non-negative
  coefficient beats ignoring albedo entirely.
- "`MatAlbedo` is the likeliest fault and would explain the magnitude" —
  **disconfirmed.**

## 7. CHEAPEST DECISIVE NEXT MEASUREMENT

**First, three lines: filter the tally by `hit.normal.y > 0.9`.** `hit` is
already in hand (`SimDirector.cs:~10740`). Print the dropped-ray count per row
so the pass is legible, and print each row's top contributing material NAME so
`mat_concrete_b` and vehicle paint show themselves. This settles §1 in one
build.

**Second, same build, ~4 lines: an A/B on `FilmGrade.Bypass`** — the switch
already exists (`FilmGrade.cs:203`, used at three call sites) and the sim
already does A/B pairs. Emit `groundGainByRaw` beside `groundGainBy`. It is
the only thing that can separate an ambient lift from an ACES shoulder from
bloom. **Do the normal filter FIRST**, or the A/B describes a contaminated
row twice.

**Not worth doing yet:** anything that moves a lever or sets a bound.
