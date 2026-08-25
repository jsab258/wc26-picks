> **STATUS — LOG, 2026-08-25. NOT CURRENT** once landed.

# groundGainBy — rendered over source, per ground material

Executes item 1 of the 25 Aug "Measurement audit of the 14f964a ruling", §B:
the division `AssetLibrary.cs:915-917` ordered and that nothing could
perform. Instruments only. No lever moved, no bound set, no gate added.

## 1. Why the ordered division was impossible

Verified against the tree, not quoted. `groundMaskMeanBy` is keyed by
DISTRICT (`hook`, `copper`, `ironside`); `groundAlbedoBy` is keyed by
MATERIAL (`asphalt`, `sidewalk`, `kerb`, `concrete`); and the mask's ray loop
pooled every ground ray into one `gSum/gN` per shot behind a single family
test. The two lists share no name, so "per name" named nothing.

Two further faults in the same sentence, found while fixing it and now
written beside the key:

- **SPACE.** `groundAlbedoBy` is LINEAR (`MatAlbedo` is `m.color.linear`'s
  luma times a texture mean read through a `RenderTextureReadWrite.Linear`
  blit). `groundMaskMeanBy` is a luma of the committed frame's sRGB-encoded
  pixels. Dividing them is a ~2x colour-space error before any physics.
- **MOMENT.** `groundAlbedoBy` is read once at done time, last-wins.
  `groundMaskMeanBy` was captured seven shots earlier. A quotient of two
  instants measures neither.

## 2. What ships

`SimDirector.GroundMaskRead`, inside the existing ray loop, one dictionary,
no extra render, no second ray grid:

    groundGainBy=[asphalt:0.6000/0.0400=15.000@3,sidewalk:0.8000/0.4000=2.000@1,
                  kerb:nothing_measured@0,concrete:0.3000/0.0350=8.571@2]
    groundGainOf=3/4 groundGainRays=6/6

(shown wrapped; the emit is one line, three space-separated `key=value`
tokens, no space inside any value — asserted by CoreTest.)

Row shape `name:<renderedLinear>/<sourceLinear>=<ratio>@<rays>`.

**Statistic, named because a reader cannot recover it from the number:**
each side is a RAY-WEIGHTED MEAN over every ray in the run that landed on
that material, across all seven district shots — not a peak, not a median,
not per shot. The ratio is a RATIO OF MEANS, not a mean of ratios; the two
diverge when graded copies of one logical carry different albedos, and the
ratio of means is the one that stays exact when they do. A CoreTest pins
that distinction (8.571 against the 7.500 a mean of ratios would print).

**Same ray, same instant.** The numerator is the pixel this ray landed on in
the texture that was encoded to the committed JPEG. The denominator is
`MatAlbedo` of `hit.collider`'s `sharedMaterial` — the material that same
ray hit, read at that same moment. Not a name looked up later, not a base
material: a graded copy carries a different colour from its base, and
`Material(logical)` BUILDS on a miss, which would make the measurement
create what it measures.

**Whole-run, so it is on the done line.** The per-shot ground means stay on
`groundMaskMeanBy`. One weather by construction: `DistrictTour` walks all
seven cameras inside one loop with no time step, so pooling is honest. Dry
against wet is a JOIN at read time (`rain`/`wet` are the last two columns of
every `frames.tsv` row) and not a second key.

## 3. Denominators

- `@<n>` per row — the rays that row is a mean OF.
- `groundGainOf=<materials with rays>/<materials offered>`.
- `groundGainRays=<bucketed>/<mask ground rays>` — **a self-check, not a
  statistic.** Both count the same rays through the two halves of one
  classifier and are equal by construction; `a != b` means the classifier
  disagreed with itself and is the first thing to read on the line.
- A material no ray landed on prints `name:nothing_measured@0` — words,
  underscored. A run that toured nothing prints four such rows plus
  `groundGainOf=0/4 groundGainRays=0/0`, which cannot read as clean.
- A zero source prints `=source0`, not an enormous gain.

## 4. The trap, recorded before the first reading

Written at the emit site and pinned to arithmetic in CoreTests: **ratios
clustering near 2.05..2.09 are a gamma/linear mismatch inside the
instrument, not a lighting gain.** That is exactly the stored 0.55 divided
by the same 0.55 in linear — 0.2684 by the pow-2.2 approximation, 0.26333 by
the exact sRGB curve `Color.linear` uses, giving 2.049 and 2.089. Two
CoreTests feed those pairs in and assert the printed strings, so the figure
in the comment is a computation rather than a remembered number.

Where the conversion happens: `px` is a `RGB24` readback of an sRGB render
target, so the pixels are the display-referred values the JPEG carries.
`Color.linear` converts the numerator; the denominator is already linear.

One measured bias, kept rather than reconciled: the numerator uses
`ImageStats.Luma` (Rec.601, shared with every other frame reading in
`SimDirector`) and `MatAlbedo` uses Rec.709 weights. On the four ground
tints — all near-neutral — the two disagree by **0.008%**, four orders of
magnitude under the effect. Making the numerator disagree with its sibling
`groundMaskMeanBy` would be the worse fault.

## 5. Why a new Core file

`Ledger.Core.GroundGain` holds the tally and the formatting for the same
reason `SurfaceNames` is in Core: **the Game layer never compiles in this
container, so a formatter written there ships unrun**, and an unrun
formatter that prints a plausible string is exactly the silent-instrument
failure this project keeps paying for. In Core, CoreTests runs it — the
accepting case is an exact expected string.

It duplicates nothing. It holds NO list of ground surfaces
(`AssetLibrary.WetSurfaces` is passed in, so a fifth ground material grows a
row with no edit anywhere), it does no colour conversion (the caller
converts and the caller's comment names the space), and it does no albedo
maths (`MatAlbedo` is the one source instrument, reached through
`AssetLibrary.GroundSourceAlbedo`).

## 6. Three dead APIs removed, not kept

`tools/reach-check.sh` caught two of these within a minute of the first
green build; the third was found by grepping for the twin.

| removed | why |
|---|---|
| `SurfaceNames.IsOneOf` | the family test and the namer are one idea; `groundGainBy` divides one's output by the other's, so two loops over one list put a division across a seam. Callers ask `MatchOf(...).Length > 0`. |
| `AssetLibrary.IsGroundSurface` | its only caller was the ray loop, which now calls `GroundSurfaceOf`. The twin of the deletion above — found by grep, not by the checker, which only audits Core. |
| `GroundGain.Rays` | a public property whose only reader was a CoreTest; the same count is already in `groundGainRays`. |

Grepped after: `IsGroundSurface` and `IsOneOf` survive only in the comments
that record their removal, plus one line of this decision record's own
history (`decision-ground-albedo.md:868`, describing the pre-fix code, which
is correct as history). The stale reference in `SimDirector`'s mask header
comment was repaired in the same change.

## 7. Comment repairs ordered by the director

- **`AssetLibrary.cs:915-917`** — the retracted sentence is quoted in the new
  text so the error cannot be re-derived, followed by where the division now
  lives and the two traps above. The key keeps a stated purpose: the
  family-wide SOURCE check that `districtGround`'s single downtown ray
  cannot give.
- **`AssetLibrary.cs:522`** — "0.55 IS A STORED (GAMMA) VALUE, AND IT IS NOT
  A 1.8x DARKENING ... the multiplier the light path actually sees is 0.263 —
  a 3.8x darkening, not 1.8x", with the pointer to the 2.05..2.09 trap.

## 8. No bound, no gate

Nothing compares `groundGainBy` against a constant. Series first, from
landed runs, per the director's standing rule and rule 2's order of
operations. Reading order at the landing: `groundMaskRays` chain first (that
instruction is unchanged), then `groundGainRays=a/b` for classifier
agreement, then the ratios — and if they cluster near 2.05, suspect this
instrument before concluding anything about light.

## 9. What could not be checked here

The Game layer does not compile in this container. `AssetLibrary.cs` and
`SimDirector.cs` are first compiled by the Windows build; the five
name-resolution lints, ShapeCheck and lint-static are green on both. The
CoreTests cover the tally, the formatter and the string rule. The two Unity
API assumptions the round trip will settle are `Color.linear` on the readback
pixel and `MatAlbedo` being callable per ray without a stall (its texture
luma is cached per `Texture`, so the blit runs at most once per ground
texture).
