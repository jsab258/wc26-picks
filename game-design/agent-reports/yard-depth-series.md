> **STATUS: SPEC, 2026-08-25.** The instrument and the PREDICTION it will be
> read against, written before any build carried it. The prediction section
> becomes a LOG the moment a series lands; until then nothing here is a
> reading.

# The yard-depth series — the printer, and the prediction before the run

Instrument: `ledger/Assets/Scripts/Core/YardDepth.cs`, wired in
`ledger/Assets/Scripts/Game/StreetDressing.cs`, emitted on the done line
through `Core/KitDressing.Line()`.

**NO BOUND AND NO GATE IS SET BY THIS WORK.** Rule 2: ship the printer, read
real runs, then choose a number, in that order. Nothing here goes red.

---

## 1. What set this off

The landed verdict at `71316fa`:

    yard_fence/1x1:163/0   yard_fence/1x2:0/0   yard_fence/1x3:0/0   yard_fence/1x4:3/0
    yard_fence:166/169/0/3refused

163 of 166 placements are the shortest 3.52m panel. Two mid-length variants
placed nothing; the longest placed three. That single reading supports two
explanations with OPPOSITE remedies — the yards are genuinely shallow (a
CONTENT fix) or the probe misreads them (a PROBE fix) — and no count of what
stood up can separate them. Hence: print the distribution first.

## 2. What the probe measures, and how

`StreetDressing.YardOf(block, alongX, out depth, out mid, out why)`, read from
the code rather than from the comment beside it:

* it fires **once per block**, over `StreetMap.Blocks` — 52 today;
* it walks **one ray per face**, along the block's own centre line on the LONG
  axis, from each of the two long faces inward, in **0.4m steps to 18m**;
* solidity is `WorldBuilder.PointClear(p, 0f)` — the building `Masses` list,
  **no inflation**, tested at y=0 in XZ only;
* the back of the row is the first step that is CLEAR after at least one step
  that was SOLID. `depth = backHi - backLo`, `mid` is their midpoint;
* a face that never goes solid-then-clear ends the probe with no depth at all;
* under `MinYard` (1.5m) it returns false but the DEPTH STILL EXISTS — that is
  a real reading of a party-wall gap, not an unreadable block.

Consequences that matter for reading the series, none of them hypothetical:
the depth is **one sample, not a survey** (a block whose centre line crosses
the 3.0m alley mouth `TerraceRow` cuts will report no back of row); it is
**quantised to 0.4m**; and because the two rays are independent, a block with
only ONE terrace row can return a **negative** depth — the rays cross.

`PickFence(yard, remain)` then turns on TWO inputs, not one: the depth AND the
run left on the tile. Only the deepest variant that fits BOTH is chosen, and
everything falls back to `1x1`.

## 3. The keys, and what statistic each one is

All eight are WHOLE-RUN CUMULATIVE, read once at the end of the run on the
DONE line, values space-free, each key appearing exactly once per token
(asserted by `KitDressing.BadTokens`, 28 tokens, 0 bad).

| key | shape | what it is a statistic OF |
|---|---|---|
| `yardBandCuts` | `1.50/4.21` | the two LIVE cut points, handed over by `StreetDressing` rather than copied. `cuts-unset` when nobody wired them. |
| `yardDepthSeries` | `[13.20/9.20/.../3.20/+Nmore]/n39` | THE SERIES — every measured depth, one per block, **deepest first**. Not a summary. The cap eats the SHALLOW end and announces itself. |
| `yardDepthSpread` | `1.20..3.60..13.20/n39` | min .. median .. max over the same population. Same variable as the series, not a second measurement. |
| `yardDepthBands` | `[noback:6,nogap:2,alley:37,deep:3]/n48` | a COUNT per band over blocks **WALKED** — a different, larger denominator than the series carries, on purpose. |
| `yardDepthBy` | `[the_hook:3.20..3.60..4.00/0deep/6of7,...]` | per DISTRICT: spread, **deep count**, measured-of-walked. District because that is the axis depth varies on. The deep count is there because a median cannot see a minority. |
| `yardDepthDeepest` | `fairview@-120,305/13.20` | the deepest site's district, map position and depth — one entry carrying value and place. |
| `yardProbeWhy` | `[no_back_lo:4,no_back_hi:2]/39of48` | a COUNT per reason no depth was produced, over measured-of-walked. The datum-exists half. |
| `yardPickBy` | `[1x1/alley:160,1x1/deep:1,1x4/deep:3,none/alley:12]/n176` | a COUNT per chosen-variant x band, over **SLOTS AT PICK TIME** — before the share roll and before the geometry refusal. **NOT `kitByVariant`**, which counts placements; this population is larger by construction. |

`yardPickBy` is the key that separates the two causes of a short panel:
`1x1/alley` is a shallow yard, `1x1/deep` is a deep yard with no run left, and
no count of placements can tell them apart.

## 4. THE PREDICTION — written before the run

Local evidence, measured here rather than assumed. `StreetMap` is engine-free,
so the block census runs in this container (`Core/StreetMap.cs`, 52 blocks):

    Copper Row     n= 8   width 35.0   depth 15.0
    the Parade     n= 8   width 39.3   depth 17.3
    the Hook       n=16   width 47.9   depth 21.9
    the Exchange   n= 6   width 56.5   depth 26.5
    Fairview       n= 4   width 56.5   depth 26.5
    Gullwing       n= 4   width 60.8   depth 28.8
    Ironside       n= 6   width 65.1   depth 31.1

Every block inside a district is IDENTICAL in size — the grid is regular.

And `WorldBuilder.TerraceBlock`, read (not remembered):

    inner   = kerbDepth - 2 * BlockSetback(2.6)
    halfAvail = (inner - 3) / 2
    depthN = depthS = min(RowDepth, halfAvail)     rows front on the inner face
    gap    = inner - depthN - depthS

**Whenever the cap binds (`RowDepth >= halfAvail`), `gap = inner - (inner-3) =
3.00 EXACTLY, independent of block size.** The 3m yard is a CONSTANT in
`TerraceBlock`, not a property of the map. `RowDepth` is 12-15 for the
Exchange, 8-10 for Fairview, 9-11 for Gullwing, 9-12 elsewhere. **Ironside is
never terraced at all** — `BuildBlockSpecs` excludes it by name and gives it
detached warehouse sheds.

So, per district, before the run:

| district | expected `yardDepthBy` | why |
|---|---|---|
| the Hook (16), the Parade (8), the Exchange (6) | a NARROW SPIKE at ~3.0 (2.6-3.4 after the 0.4m step), `0deep` | the cap binds; the gap is the constant 3.0 |
| Fairview (4), Gullwing (4) | 3.0 to ~5.5, a few `deep` | `RowDepth` sits near `halfAvail`, so the cap binds only sometimes |
| Copper Row (8) | **NEGATIVE, around -7.4**, `0deep` | `halfAvail`=3.4 < the 4.2 `deepEnough` test, so ONE row is built and the two rays cross it from opposite sides |
| Ironside (6) | the deep ones, or `noback` | not terraced; sheds, not a perimeter |

**P1.** `yardDepthBands` `deep` lands between **2 and 6** of n=52. (A deep
block's FIRST slot always has `remain` >= 23m, so it always picks `1x4`; only
three `1x4` landed, and the share roll is 0.80.)
**P2.** the Hook / the Parade / the Exchange come back as a spike at ~3.0 with
`0deep` — a spread there instead of a spike falsifies my reading of
`TerraceBlock`.
**P3.** `copper_row` is negative.
**P4.** `yardPickBy` is dominated by `1x1/alley`; `1x4/deep` is 3-6.
**P5.** cross-check: `yard_fence` offered (169) divided by the non-`none`
picks in `yardPickBy` should be ~0.80, the `FenceShare` roll. If it is not,
one of the two counters files in the wrong place — and that is an instrument
finding, not a street finding.

### Which reading means what

**THE YARDS ARE GENUINELY SHALLOW → CONTENT FIX.** P1-P4 hold: ~30 blocks
spiked at 3.0, `deep` ~3, `noback` ~0, `1x1/deep` small. Then the repeating
boundary is not a bug at all — `halfAvail` pins every terraced yard at exactly
3.0m and the kit has no straight panel shorter than 3.52m, so the alleys can
only ever get one model. The remedies are content-side: more short-panel forms
at ~3m, or change the `3f` in `halfAvail` so yards vary by district.

**THE PROBE IS AT FAULT → PROBE FIX.** Any of:
* `noback` above ~10 — the single centre ray is landing in the 3.0m alley
  mouths (`alleyT` is 0.25-0.75 along the run, so the centre is squarely in
  range) and blocks that HAVE yards are being skipped;
* every district identical to two decimals despite block depths spanning
  15.0-31.1 — that is a constant wearing a measurement's clothes
  (the `6.57..6.57..6.57` shape), not a reading;
* negative depths on blocks that are genuinely two-rowed (anything but
  Copper Row) — the two rays are crossing where they should not.

**A THIRD CAUSE NEITHER FORK NAMED, and the instrument can see it:**
`1x1/deep` large. That is the depth being fine and the TILING being what
forces the short panel — the greedy walk consuming the run 12.40m at a time
and leaving remainders too short for a U. Its fix is neither content nor the
probe; it is `PickFence`'s remainder handling. It is called out here because
if it is what lands, reading the series as "the yards are shallow" would send
the next session at the wrong file.

## 5. Selftest — run, both cases, output as it printed

```
Yard depth — the distribution that decides which fence is even legal:
  ok - the series prints every measured depth, deepest first, over its own count
  ok - and the spread beside it carries min, median and max, none of which can answer another's question
  ok - the band census is over blocks WALKED, which is the denominator the series does not carry
  ok - and the live cut points print beside the band names that mean them
  ok - per district: spread, deep count, and measured-of-walked
  ok - the deepest yard names where to stand to look at it
  ok - and every block that produced no depth says why, over the same denominator
  ok - a short panel in a deep yard and one in an alley are different rows
  ok - a median of forty sites reads shallow with a deep yard among them
  ok - and the count and the position are what can see it
  ok - an unwired band prints the word, never a plausible band
  ok - and so does the pick cross-tab, on the same word
  ok - while the series survives it, because it needs no cut point
  ok - a pass that never ran says so in words, not in zeros
  ok - and the two count keys ship the denominator that says nothing was walked
  ok - a probe that files no reason is named, not dropped
  ok - and forty-eight unreadable blocks are not zero blocks
  ok - a NaN depth is refused as a sample and counted as unreadable
  ok - the series cap announces itself and keeps the deep end
  ok - and so does the district cap
  YARDDEPTH-ONLINE [...23 kit keys...] yardBandCuts=1.50/4.21 yardDepthSeries=[3.60]/n1 yardDepthSpread=3.60..3.60..3.60/n1 yardDepthBands=[noback:1,nogap:0,alley:1,deep:0]/n2 yardDepthBy=[copper_row:3.60..3.60..3.60/0deep/1of1,the_exchange:nothing-measured/0deep/0of1] yardDepthDeepest=copper_row@-88,120/3.60 yardProbeWhy=[no_back_of_row:1]/1of2 yardPickBy=[1x1/alley:1]/n1
  ok - the fragment carrying the yard keys walks twenty-eight tokens
  ok - and no yard value can truncate at a space or an unbalanced bracket, over 28 tokens
  ok - a district name with a space in it is folded, not truncated
  ok - and so is a reason the Game layer invented
  ok - placements and picks are different populations and print apart
```

Twenty-five assertions. The accepting case is first on purpose: the expensive
failure is a printer nothing survives.

### Wiring proof (rule 6 — built is not running)

    StreetDressing.cs:303   WorldBuilder.KitTally.Yards.Cuts(MinYard, DeepYard);
    StreetDressing.cs:324   WorldBuilder.KitTally.Yards.Walked(...)   once per BLOCK
    StreetDressing.cs:349   WorldBuilder.KitTally.Yards.Picked(...)   once per SLOT
    SimDirector.cs:16816    WorldBuilder.KitTally.Line()              bare, done line

`Walked` is called BEFORE the `continue` that skips an unusable block, which
is the whole point: a series over placements can only describe sites that
worked.

## 6. Verify — read from disk, not from scrollback

`ledger/.verify-footer` **does not exist**. `python3 ledger/verify.py` exits 1
and prints `NOT GREEN — do not paste this into a commit message as if it
were`, so there is no footer to quote and the absence is the reading.

The single red on the final run is **`DIRECTOR NOT SPAWNED`** — 688 changed
lines against a 100-line threshold under `Assets/Scripts` with no
`studio-director` row newer than the reference commit. That is the resident's
mechanical escalation, not a fault in this work, and it is not something a
builder may clear.

Every check that covers this work passed on that same run: 0 lint errors,
0 shape errors (191 files), Game layer compiles (185 files), 0 static/instance
errors, 0 filename-as-type errors, 0 namespace-as-value errors, verdict format
ok, emit dupkeys ok (0 same-line duplicate keys across 112 log calls in 185
files), **4,090 CoreTests**, docs-check 102/102 clean.

One correction worth recording rather than quietly fixing: an earlier run
carried a **third** red, `DOCS: yard-depth-series.md declares a status in its
first 8 lines — no STATUS banner`, and that one WAS this work. `docs-check.py`
matches `**STATUS — LIVE|SPEC|LOG` and a plain `STATUS: LIVE` line does not
satisfy it. Fixed here; docs-check now reads 102/102.

`1075 verdict keys, 102 new (run --learn)` is unrelated to this work — that
compares the manifest against the LANDED verdict at `71316fa`, which cannot
contain keys that have never been built. The eight keys here will show up as
new only after a build carries them, and learning them is the resident's call.

## 7. What must NOT happen next

Do not set a threshold off the first landed series. One run is not evidence
(rule 2), and the two of the three causes above that are code-side would each
be made invisible by a bound chosen now.
