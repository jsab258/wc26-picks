# Single-ray probes — the sweep, and two refutations

> **STATUS — LOG, 2026-08-25. NOT CURRENT** once the probes are pinned.
> Read-only sweep by measurement-auditor. Written to disk by the
> coordinator: the auditor has no write tool by construction and correctly
> refused to write via Bash, since that changes state. Briefing error mine.

## Counts, with denominators

| | |
|---|---|
| verdict emits examined (committed manifest) | **1076** (1075 `always` + 1 conditional) |
| simple-name keys swept | 1066, across **323** measuring runs |
| `Physics` cast sites in the Game layer | **18** across 6 files, 11 in `SimDirector.cs` |
| emits whose value comes from a SINGLE RAY | **6**, all from ONE helper |
| of those, NAKED (no identity at all) | **0** |
| of those, partial identity that READS AS AGREEMENT | **3** |

## Two refutations — do not build on the header claims

**`districtGround` does NOT drift.** The series refutes it: 16/16 runs
`mat_asphalt`, 16/16 `nSun:0.79`, `d:` spread 19.3–19.8 — half a metre on
flat identical asphalt at an identical sun angle. Its `col:` changes
(0.44 -> 0.74 -> 0.41) track authored lever moves, which is the probe
working rather than failing. **The published ruling's use of it survives.**

**`noonFacade` is NOT a single-ray probe.** `LeftThirdMedian`
(`SimDirector.cs:9355`) is a median over ~76,800 pixels. Its ten sub-terms
did not move because a ray moved — they moved because **the camera faced a
different wall**. Different fault, different fix: sending it to a grid
sampler cannot help an uncontrolled camera aim.

**`shadowDrop` is not single-ray either** — whole-frame `ImageStats.Darkened`,
a max over noons. Its bimodality covariate is ALREADY instrumented and
landed: `shadowPeakDay` reads `3/0.90 -> 0.0437`, `2/0.00 -> 0.2406`,
`3/0.90 -> 0.0653`, `3/0.90 -> 0.0605`. Consistent with rain, but n=4 with
one point in the upper cluster — corroborating, not settled.

`noonFacadeOf`'s `Min(6,...)` cap DOES announce itself (`/+Nmore`, `:9184`).
Suspected otherwise; checked.

## The finding — one ray printed three times, and it reads as agreement

`SurfaceUnder` (`SimDirector.cs:8714`) is the only single-ray verdict
producer in the Game layer. Five call sites, six keys.

| key | site | identity shipped |
|---|---|---|
| `noonFacadeMat` | `:9204` | FULL — `d:`, `nSun:`, `nUp:`, material, tex, gloss |
| `districtGround` | `:10509` | FULL |
| `shadowPairOn` | `:9024` (rays `:9323`,`:9325`) | FULL x2 + viewport coords |
| `ambientSeries` `on:` | `:9131` | **material name only** |
| `sunSeries` `on:` | same `onWall` var | **material name only** |
| `shadowSeries` `on:` | same `onWall` var | **material name only** |

`onWall` is assigned ONCE at `:9131` and stamped into all three series, so
**the three stamps cannot disagree — they are one stamp three times.** It
keeps only `.Split('/')[0]`, the material name. Proof, both keys on the
same line:

    c865582  noonFacadeMat  mat_brick_grey_b#g1  d:1.8  nSun:0.00   (line 77)
    c865582  ambientSeries  on:mat_brick_grey_b#g1                  (line 77)
    0d0ebd7  noonFacadeMat  mat_brick_grey_b#g1  d:8.9  nSun:0.62   (line 87)
    0d0ebd7  ambientSeries  on:mat_brick_grey_b#g1                  (line 87)

A **7.1-metre subject change onto a wall the sun never reaches**, and the
stamp is byte-identical.

CLAUDE.md's own sentence — *"a stamp that is always the same is worse than
no stamp because it looks like agreement"* — is written in the comment
directly above `onWall`, about the INITIALISER case. It is true here for a
second reason nobody looked for: one idea, two ways to be wrong, and only
the first was guarded. **Fix: stamp `d:` and `nSun:` too, not just `[0]`.**

Second, smaller: `:9131` and `:9204` are two separate rays at the same
viewport point, taken at different moments. The comment at `:9190`
documents this deliberately, so it is not a slip — but `on:` and
`noonFacadeMat` can legitimately disagree and nothing in the verdict says so.

## Ranked by whether a published conclusion quotes it

1. **`districtGround`** — 16 mentions in 7 docs, including the published
   ruling (`decision-ground-albedo.md:556,750,969`). Drift REFUTED above.
2. **`noonFacade` / `noonFacadeMat`** — 6 mentions in 4 docs. Drift
   established and WORSE than the header: `d:` spans **1.8 to 9.2**,
   material flips brick<->concrete in **4 of 17** runs, `nSun` flips
   0.62<->0.00.
3. **`ambientSeries`** — 1 mention (`queue.md:378`, the ambient-fill
   claim). Partial stamp, per the finding above. ACTIVE.
4. `sunSeries`, `shadowSeries`, `shadowPairOn` — 0 mentions. LATENT.

## The bigger bad-shape class — 58 of 1066

`verdict-read.py --collisions` reports 22 on the newest verdict; the sweep
across all 323 runs found **58 manifest keys carrying more than one
distinct value in a single run**. The load-bearing cluster is the whole
per-frame sky/grade family — emitted once per shot, read file-wide by
`gates.py --series`: `meanLuma` (**quoted 21 times in 7 docs**), `maxLuma`,
`brightPct`, `satPct`, `satStrength`, `ambSky`, `bgRGB`, `fogRGB`,
`density`, `k`, `srcG`, `n`. Same repair as `meanLuma`, twelve keys not one.

**Dead reading, incidental:** `shadowWhen` is `12` in every landed run and
its own comment at `:7700` says it can only ever be 12 or -1. It answers
"did the probe fire", not "when" — a name asking a question the number
cannot answer.

## Established vs inferred

**Established from series and verdict data:** the inventory, the `on:`-stamp
proof, both refutations, the drift magnitudes, the 58 ambiguous keys,
`shadowWhen`. **Inferred:** the rain covariate for `shadowDrop` (n=4).
**Caveat:** `SimDirector.cs` was dirty in the working tree during the sweep
(a live builder); line numbers were re-verified at `md5 e0ae3717...`.
