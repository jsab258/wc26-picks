# Overhead cables read white against the sky — CONFIRMED, and fixed (systems-builder, 25 Aug 2026)

> **STATUS — LOG, 2026-08-25. NOT CURRENT once the next Windows build
> lands** — every pixel number below is measured off run `71316fa`'s
> committed stills, and the whole point of the change is that they should
> read differently next time. The emit that would prove it is named in
> section 4 and is NOT wired.

## 1. What the cables actually take, and where it is set

Not in `Cable()`, which is why the grep came back empty. Every span is
built as two primitives by `StreetFurniture.Segment()`, and the material
is assigned there:

    go.GetComponent<Renderer>().sharedMaterial = AssetLibrary.Material(AssetLibrary.Metal);

`AssetLibrary.Metal` resolves through `SurfaceSpec.For` (AssetLibrary.cs:1553):

    case AssetLibrary.Metal: s = Make(new Color(0.30f,0.31f,0.33f), 0.55f, 0.9f, new Vector2(1,1), "flat");

That is tint 0.30/0.31/0.33 at **smoothness 0.55, metallic 0.9** — a
mid-grey mirror. It is not near-black and nothing downstream darkens it.
So the item was NOT stale.

**The twin, found by grepping `Segment(`:** all four call sites go through
that one helper — two from `Cable()` (cross-street spans) and two from
`Wires()` (the avenue telegraph pole spans, added later for V3). The pole
wires had exactly the same fault and are fixed by the same line. Had the
fix gone into `Cable()` instead, the 96 pole wires would have kept it.

## 2. Cables, or rain? Cables — and the frame that settles it is dry

`review_day1_noon` is a raining frame (`rain=0.35`), so it cannot answer
this. `frames.tsv` supplies a clean discriminator: **`day5_noon` has
`rain=0.00` AND `wet=0.00`**. That frame still shows a continuous straight
bright line crossing both a dark stone facade and the sky, with a specular
blob where the sun catches it — one span, not the many short parallel
strokes a rain shader draws.

Then measured rather than squinted at (a picture is a hypothesis):
sampling 11 columns across the span in `review_day5_noon.jpg`, taking the
brightest pixel per column as the wire and a sky datum 14px off it **in
the same column of the same frame** (same-instant denominator):

    median wire/sky luma ratio = 2.77 over 11 columns
    wire peaks at RGB (231,243,243); sky under it runs (58,62,73)..(111,110,115)

A silhouette element reading nearly 3x brighter than the sky behind it is
the exact failure the brief describes. `rainStreak=0.152` is a separate,
live thing and is not implicated.

## 3. What changed

One file, `ledger/Assets/Scripts/Game/StreetFurniture.cs`:

- **A derived wire material**, `WireMaterial()`, cached in one static and
  shared by every span so batching survives. The pattern is
  `AssetLibrary.MaterialGraded`'s (`new Material(baseMat)`, cached).
  DERIVED rather than edited in place because **45 other call sites take
  `AssetLibrary.Metal`** — bench legs, dumpsters, bar counters, roof
  aerials — and a mirror is right for most of them.
- **Colour** `0.13/0.15/0.14`, which is `TrafficHost.SignalHousing`'s
  value; its own comment asks for "the same family as the lamp column so
  the street's ironwork agrees with itself". **Smoothness 0.12 and
  metallic 0.10** are `AssetLibrary.Roof`'s — the palette's existing entry
  for weathered outdoor metal. No number here was invented; each is cited
  to the constant it came from, in the comment.
- **A material, not a `MaterialPropertyBlock`.** Half the fault is gloss,
  which no colour set can reach, and an MPB colour skips the
  gamma-to-linear conversion `Material.SetColor` performs. `PaintKit` is
  the right tool for a kit mesh whose own material is already matte; it is
  not the right tool here.
- **Both silent-no-op traps guarded.** Every set is behind
  `HasProperty`, and because a bound `_METALLICGLOSSMAP` makes
  `_Glossiness` a no-op (the fault `SetWetness` already hit), the code
  sets `_GlossMapScale` too when the keyword is on, and reports which
  properties were actually accepted.

## 4. The number

Three new public statics, ready for the done line:

- `WireSegments` — CUMULATIVE per `Build()`, every span segment created.
  The denominator.
- `WireSegmentsDark` — of those, how many took the near-black material.
- `WireProps` — last-wins token naming which properties the shader
  accepted, e.g. `color+metallic+gloss`; `none_accepted` if the shader
  refused all of them, `nothing_measured` if the material was never
  derived. No spaces, so it survives the verdict reader.

`WireSegments` is deliberately not `CableCount` in other units: a cable is
two segments and a pole wire is two segments, so a healthy run satisfies
`WireSegments == 2*(cables + poleWires)` — **318** against the landed
`cables=63 poleWires=96`. A reading that breaks that identity is a span
built through some other path.

**THE EMIT IS NOT WIRED, because `SimDirector.cs` is not mine this cycle.**
Rule 6 applies: this is built, not running, until someone adds one token.
The line to add is immediately after the existing
`poles=... poleWires=...` on the done line (SimDirector.cs:17348):

    $"wireDark={StreetFurniture.WireSegmentsDark}/{StreetFurniture.WireSegments} wireProps={StreetFurniture.WireProps} " +

Both key names are free — checked against `verdict-keys.json` and the
landed verdict (the existing `wired=` is a different token).

## 5. What I ran

`python3 ledger/verify.py` in the working tree is **RED**, and the red is
not mine: another agent has uncommitted Core work in flight
(`Core/KitDressing.cs`, `CoreTests/Program.cs`, new `Core/YardDepth.cs`)
and the failing assertion is theirs — "a fully populated run formats
exactly", on a `kitPlaced=.../kitFamilies=.../kitBy=[lamp` line.
`CoreTests.csproj` compiles `Core/**` plus five NAMED Game files, and
`StreetFurniture.cs` is not one of them, so my change cannot reach that
test.

So I re-ran it isolated: a detached worktree at `HEAD` with **only** my
file copied in, twice — the second time against the exact final text of
the file, because the first run predated a comment edit. Both runs agree:

    4049 CoreTests
    0 lint errors, 0 shape errors (190 files, 3 with conditional code)
    Game layer compiles (184 files)
    0 shadowed Core types, 0 nested-type errors, 0 static/instance errors,
    0 filename-as-type errors, 0 namespace-as-value errors
    slop 87/88   (unchanged — same as before the change)

Those five name-matching lints are the ones that matter here, because
ShapeCheck is reference-INDEPENDENT and cannot see a name that needs
RESOLVING. The worktree has since been removed.

The only red in the isolated log is line 3, `DIRECTOR NOT SPAWNED` (the
cadence gate) — expected: I was told not to commit, and that gate is the
resident's to clear. `tools/docs-check.py` passes on this report; its one
failure is another agent's `lint-avenues-exemption.md`, which has no
STATUS banner.

**There is no footer to paste. `ledger/.verify-footer` does not exist on
disk** — a red run deletes it, and both runs were red for the two reasons
above. Local green is necessary and never sufficient here anyway: nothing
in this container renders a frame, so the 2.77x becomes evidence of a fix
only when the next build's `day5_noon` is measured the same way.

## 6. Noticed, not done (rule 11)

- **`aerial-metal-mirror`** — the same shared mirror is on thin geometry
  elsewhere against the sky: `WorldBuilder.cs:1249` builds roof aerial
  masts at 0.035m square and `:1258`/`:1267` their booms and elements, all
  `AssetLibrary.Metal`. Same failure mode, same cause, and `WorldBuilder`
  is not mine this cycle. Worth one look at a district frame's roofline.
- **`column-green-shared`** — `WorldBuilder.ColumnGreen`,
  `TrafficHost.SignalHousing` and now `StreetFurniture.WireBlack` are three
  private near-blacks in one family, in three files. The house idiom is
  currently per-file constants painted through one shared helper, so I
  followed it rather than inventing a fourth convention; promoting one
  public `Ironwork` colour is a real cleanup but it touches two files I do
  not own.
- The historical sentence in `Cable()`'s comment calls the old broken
  spans "bent black scribbles floating against the sky". It describes
  anchoring in a build I cannot open, so I left it; if those stills showed
  white lines, that word is wrong and predates this change.
