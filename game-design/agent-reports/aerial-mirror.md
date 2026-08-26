# Rooftop aerials took the same mid-grey mirror — fixed (systems-builder, 25 Aug 2026)

> **STATUS — LOG, 2026-08-25. NOT CURRENT once the next Windows build
> lands.** Nothing below is measured off a frame that contains the change:
> the Game layer does not compile in this container, so every claim here is
> either a value read out of source, a count read out of the last landed
> verdict, or a prediction that the emit in section 5 exists to settle.
> The emit is **NOT wired** — `SimDirector.cs` was another agent's file this
> cycle. The exact one-line call site is in section 5.

## 1. The fault, and why it is the cables' fault verbatim

`AssetLibrary.Metal` resolves at `AssetLibrary.cs:1553` to tint
0.30/0.31/0.33 at **smoothness 0.55, metallic 0.9** — a mid-grey mirror.
Measured on the overhead spans, which are the same treatment on the same
kind of geometry: a **median 2.77x the luma of the sky in the same column**,
11 columns of a dry frame (`rain=0.00 wet=0.00`), peaking at RGB
231,243,243. A thin member sweeps every normal across its width, so
somewhere along it the specular condition is always met and the whole member
lights up at once.

Roof aerials are that geometry and worse placed. Members are **0.035m
square** — thinner than the 0.05m spans — and they stand ON the roofline,
which is the one position in the frame where the background is sky from
every camera in the game. The last landed run built **`aerials=129` on
`chimneys=219`** (verdict `b7d232b`), so the mirror was on 129 rooflines.

## 2. What changed, in `WorldBuilder.cs` (the only file touched)

All three sites named in the brief, plus the material they now take:

| line (post-change) | what |
|---|---|
| `1228` | `AerialMembers = 0; AerialMembersMatte = 0;` beside `int cn = 0, aerials = 0;` — zeroed with the build pass they count |
| `1244–1249` | the aerial block's own comment now says the members take the derived matte metal and why |
| `1257` (was 1249) | `AerialMast_{cn}` — `MakeBox(..., AssetLibrary.Metal)` → `AerialMember(...)` |
| `1266` (was 1258) | `AerialBoom_{cn}` — same |
| `1276` (was 1267) | `AerialEl_{cn}_{el}` — same |
| `1295–1317` | `AerialProps`, `AerialMembers`, `AerialMembersMatte` — the instrument |
| `1319–1367` | `AerialGalv` / `AerialSmoothness` / `AerialMetallic` and the reasoning above them |
| `1369–1393` | `AerialMaterial()` — derived, cached, both no-op traps guarded |
| `1395–1408` | `AerialMember()` — builds through `MakeBox`, re-materials, counts |

The shape is `StreetFurniture.WireMaterial`'s, deliberately: a **derived
material**, cached in one static, shared by every member, so batching
survives and `AssetLibrary.Metal` is untouched for everybody else. Not a
`MaterialPropertyBlock` — half the fault is gloss, which no colour set
reaches, and an MPB colour skips the gamma-to-linear conversion
`Material.SetColor` performs.

Both silent-no-op traps are guarded. Every set is behind `HasProperty`; and
because a bound `_METALLICGLOSSMAP` makes `_Glossiness` a no-op (the fault
`SetWetness` already hit in this project), `_GlossMapScale` is set as well
when the keyword is on, with `AerialProps` naming which the shader took.

The fallback is visible rather than silent: if the derivation returns null
the member keeps the shared `Metal` it was built with, and
`AerialMembersMatte` does not move — so `0/645` says "the derivation
failed", which is a different fault from `0/0`, "no aerial was built".

## 3. The judgement: an aerial is not a wire, and it is cited either way

**A rooftop aerial takes `AssetLibrary.Roof`'s palette entry WHOLE** —
colour 0.17/0.18/0.20, smoothness 0.12, metallic 0.1, `AssetLibrary.cs:1552`.

The wire took a split: `TrafficHost.SignalHousing`'s near-black
(0.13/0.15/0.14) for colour, because a span is street ironwork and that
comment asks for the lamp column's family; and only gloss/metallic from
`Roof`, as the palette's weathered-outdoor-metal entry.

That colour reasoning does not transfer, so it was not reused. An aerial is
galvanised steel bolted to a chimney stack, weathering in the same salt air
as the slates a foot beneath it, and it catches more sky than anything at
street level. `Roof` is both the palette's weathered-outdoor-metal entry
**and the literal material of the thing it stands on**, so taking it whole
is one citation rather than two, and it lands the aerial slightly LIGHTER
than the wire black on purpose: an aerial as dark as a telegraph wire is the
same fault in the other direction, a black scratch on the skyline instead of
a white one.

**No number here was invented.** Both candidate values were already in the
palette; the choice between them is the judgement, and it is written into
the comment above `AerialGalv` in those terms. Whether 0.17 is far enough
down is what section 5's emit and the next dry frame are for — I have not
seen a frame with this change in it and do not claim one.

## 4. Every `AssetLibrary.Metal` site I examined and left alone

45 non-comment references across `Assets/Scripts` (`grep -rn`, comment lines
excluded), of which 33 are in `WorldBuilder.cs`. The fault needs BOTH thin
geometry AND sky behind it; a box has fixed normals per face and does not
sweep the specular lobe, and anything below the roofline is read against
brick.

| site | left alone because |
|---|---|
| `587` Belisha pole (0.09m sq, 2.5m) | thin and partly against sky, but 2.6x the aerial's width and street-level; a real Belisha post is banded black/white, so its colour is a DIFFERENT open question — queued, not silently folded in |
| `1199` roof tank (1.2m cube) | on the skyline but a CUBE — three visible faces, fixed normals, no sweep. A galvanised water tank is legitimately shiny |
| `1518/1524/1553` fire escape deck, rail, run | on a back wall, read against brick from an alley, never against sky |
| `1838` shopfront mullions (0.10–0.12m) | at 2.6m on a facade, against the shop behind them |
| `2209–2241` bar counter, stool legs, sign bracket/frame | interior and street-level; a bar counter SHOULD be a mirror |
| `2293/2294` dumpster + lid | a box, street-level |
| `2553/2556/2701` vehicle body, cabin, glass | overpainted by `paint` / `glass` at the call site, so `Metal` is only the base; a car body is a mirror by definition |
| `2743` pillar-box letter slot | 0.3 x 0.05 x 0.04, `Tint`ed to 0.1/0.1/0.1 at the call site, and a slot in a pillar box has a pillar box behind it |
| `2976/2977` bench legs | 0.21m off the ground |
| `3444` bin box, `3449` drainpipe (0.16m) | drainpipe is vertical against the wall for its full height — wall behind it, never sky |
| `4015/4016` **primitive lamp pole + head** | THE INTERESTING ONE — see below |
| `4736–4793` gasholder drum, columns, ring | a deliberate landmark whose whole point is a big metal silhouette; changing it is an art call, not a bug fix |
| `4826` church finial | one piece, `w*0.06`, at the top of a spire — genuinely against sky, but a gilded/metal finial catching light is what a finial is for |
| `TrafficHost` (7), `PlayerCar` (1), `StreetFurniture:626` | not my files this cycle |

**And the family is BOUNDED, which is worth knowing before anyone goes
looking for a fourth site.** I read all fourteen `Make(new Color(...))`
entries in `AssetLibrary`'s palette and `Metal` at 0.55 / **0.9** is the only
one with metallic above 0.1. `Glass` (0.90 / 0.2) and `Window` (0.85 / 0.1)
are smoother but nearly dielectric, and both are flat panes rather than
swept cylinders. So `aerial-metal-mirror` and `overhead-cables` are the
whole of this class unless someone adds a mirror to the palette; there is no
third surface to grep for.

**`4015/4016`, the twin worth naming and NOT fixed here.** The KIT lamp gets
`AssetLibrary.PaintKit(rends, ColumnGreen)` at `3972` — the dark green
ironwork. The primitive fallback 43 lines later takes raw
`AssetLibrary.Metal`: two lamps in one street would look completely
different depending on whether the kit loaded. I did not change it, and the
reason is a number rather than scope alone: the landed verdict reads
**`kitBy=[lamp:354/354/0/0refused]`** and
`lampsByKind=[...]/n354of354` — **354 of 354 lamps came from the kit, zero
misses**, so `KitTally.Missed("lamp", ...)` and the primitive path beneath
it never execute. Editing dead code would be unverifiable by construction
(rule 6, in reverse). Queue it as **`lamp-fallback-mirror`**: one line,
`AssetLibrary.PaintKit`/`Tint` the fallback pole with `ColumnGreen` which is
already in this file, to be done when something makes the fallback
reachable or as insurance before a kit-loading change.

## 5. The emit that is owed — `SimDirector.cs`, NOT wired by me

`SimDirector.cs` was another agent's file this cycle. Both keys are new —
the only existing `aerial*` key in the landed verdict is `aerials=`. Neither
value contains a space. Both are whole-run numbers and the insertion point
is inside the **done-line** statement (no `;` between 17014 and 17400, so
`aerials=` at 17038 and `wireDark=` at 17358 are one line), which is where
they belong.

Insert after `SimDirector.cs:17038`, matching `wireDark`'s shape at 17358:

```csharp
                      $"aerials={WorldBuilder.AerialCount} " +
                      // Five members per aerial (mast, boom, three
                      // elements), both counted inside the same
                      // `AerialMember` call, so this is a same-instant
                      // numerator over its own denominator and not two
                      // totals: `0/0` is "no aerial was built", `0/N` is
                      // "the matte metal failed to derive and the mirror is
                      // still on every roofline". `aerialProps` says which
                      // sets the shader accepted — half the fault is GLOSS,
                      // which no colour set reaches.
                      $"aerialMatte={WorldBuilder.AerialMembersMatte}/{WorldBuilder.AerialMembers} " +
                      $"aerialProps={WorldBuilder.AerialProps} " +
                      $"shopSurrounds={WorldBuilder.ShopSurrounds} " +
```

**What to read when it lands.** `aerials=129` last run, so a healthy build is
`aerialMatte=645/645` (5 x 129) and `aerialProps=color+metallic+gloss`, plus
`+glossmap` if the fetched pack bound a map. `aerialProps=nothing_measured`
means `AerialMaterial` was never called at all — a chimney or `Roll` fault,
not a shader one. And the picture question the numbers cannot answer: open a
noon still and look at whether the rooflines still carry bright ticks.

## 6. A comment my change falsified in a file I do not own

`StreetFurniture.cs:266–268`, inside `WireMaterial`'s doc comment:

> `/// DERIVED, NOT EDITED IN PLACE: 45 other call sites take`
> `/// `AssetLibrary.Metal` — bench legs, dumpsters, bar counters, roof`
> `/// aerials — and a mirror is right for most of them.`

It names **roof aerials** as one of the sites where the mirror is correct,
which stopped being true this hour. One-word fix, for whoever owns that file
next: replace `roof aerials` with `car bodies` (or `a gasholder`), both of
which are on the list in section 4 and stay mirrors. I did not touch it —
file ownership.

The count itself is fine and I checked rather than assumed: 45 non-comment
references, 40 once the palette entry and the two derived materials' own
fallbacks come out. My own comment cites the measured pair rather than
repeating "45" unchecked.

## 7. The third item in the family — evidence, not a change

`WorldBuilder.ColumnGreen` (0.15/0.17/0.15), `TrafficHost.SignalHousing`
(0.13/0.15/0.14) and `StreetFurniture.WireBlack` (0.13/0.15/0.14) are three
private near-blacks in one family across three files. **I did not promote a
shared `Ironwork` colour** — it touches files I do not own and it is queued.

What my work adds to the case: `AerialGalv` (0.17/0.18/0.20) is a FOURTH
private constant in the same neighbourhood, and it is the one that most
wants a shared home, because it is not a fourth opinion — it is
`AssetLibrary.Roof`'s tint copied by value into `WorldBuilder` so the
material derivation can reach it. `AssetLibrary` already owns that number.
The honest shape when someone takes the queued item is probably not one
`Ironwork` colour but **`AssetLibrary` exposing its surface entries as
readable values**, so a derived material can cite a palette entry instead of
transcribing it — and a transcription is a comment with a number in it,
which is the thing this project has a whole rules file about.

Also noticed and not touched: `WorldBuilder.cs:2821` holds
`FurnitureMetal = 0.30/0.31/0.33`, a hand-copy of `Metal`'s exact tint, and
the same transcription problem pointing the other way.

## 8. What I ran

`python3 ledger/verify.py` — **exit 1**, and the single red is
`director_cadence`, which is builder work awaiting review and is what it is
supposed to say. A red run DELETES `ledger/.verify-footer`, so there is no
footer file on disk to paste; the footer text is in section 9, quoted from
the run's own output with the red named. Everything that could see this
change is green in it: `0 lint errors`, `0 shape errors (191 files)`,
`0 shadowed Core types`, `0 static/instance errors (75 members, 562 bodies)`,
`0 filename-as-type errors`, `0 namespace-as-value errors`,
`Game layer compiles (185 files)`, `4090 CoreTests`.

`Game layer compiles` is reference-INDEPENDENT and is necessary, never
sufficient — anything needing a name RESOLVED is invisible to it. The two
resolution risks here were checked by hand: `WorldBuilder` declares no
member named `Material` or `Renderer` (so `static Material _aerialMat;`
binds to `UnityEngine.Material`, and `new Material(...)` already appears at
`387` and `2475` in this file), and nothing here writes a bare `Game`.

Uncommitted tree at the time of writing also holds `CLAUDE.md` and
`.claude/agent-log.tsv` changes that are **not mine**, and an untracked
`game-design/agent-reports/lint-static-denominator.md` from another agent.
My change is `ledger/Assets/Scripts/Game/WorldBuilder.cs` alone.

## 9. Footer

**There is no footer on disk to paste: `ledger/.verify-footer` does not
exist**, because both runs were red and a red run deletes it
(`ls: cannot access 'ledger/.verify-footer': No such file or directory`,
checked after each). What follows is the run's own output, verbatim, with
the red left in it.

**Run 1 — the isolated reading.** At this point the only file modified under
`Assets/Scripts` was `WorldBuilder.cs` (129 changed lines, all mine), so
this footer is about my change and nothing else.

```
--- verification footer ---
DIRECTOR NOT SPAWNED: 129 changed line(s) (129 tracked + 0 untracked in 0 new file(s)) vs 100 threshold under Assets/Scripts, 0 director row(s) newer than the reference of 137 log row(s) examined, reference = code commit f26ed5fd@2026-08-25T22:13:12Z (27 director row(s) in the log, all older than that reference; newest 2026-08-25T22:07:11Z vs reference 2026-08-25T22:13:12Z), rulingRecords=0/3 rulingFiles=4 rulingUnmatched=0 rulingRowsUnruled=0/0 rulingUnruledNewest=none - 0 ruling record(s) paired to a director row newer than the reference, of 3 stamp(s) in 4 decision file(s) scanned; 3 stamp(s) name a row at or before the reference (a ruling on an older batch) - spawn studio-director for the batch review, then re-run verify; fable spend, READING ONLY (no bound, nothing here is gated): directorSpawns=0/3 fableShareDay=23/110@2026-08-25 fableShareAll=27/137 fableAgents=studio-director agentFilesRead=10 [53/53 selftest fixtures], 0 lint errors, 0 shape errors (191 files, 3 with conditional code), 0 shadowed Core types, ... 22 queue items ready, docs 103/103 clean, ... Game layer compiles (185 files), speech backend + bench compile, 0 unreachable behind #if (1 type(s) checked), 0 nested-type errors (255 Core types), 0 static/instance errors (75 members, 562 bodies), 0 raw avenue reads, 9 DEFERRED (185 files), 0 filename-as-type errors (191 files, 13 filenames that are not types), 0 namespace-as-value errors (191 files, 4 segments in scope), ... 1075 verdict keys, 102 new (run --learn), verdict format ok (selftest + newest run), verdictSpaced=35/137 not gated, dupkeys ok (selftest); ... gates 18 bare / 41 detailed, ceiling 18, 29 save-chaos checks, 3 soak checks (500 days x2), 84 adversary checks, 0 stale anchors, clips ok (64 read, 2 known finding(s)), clip picker ok, 4090 CoreTests.
---------------------------
NOT GREEN - do not paste this into a commit message as if it were.
```

Elided with `...` only where the footer lists checks untouched by this
change; nothing red was removed, and `DIRECTOR NOT SPAWNED` is the whole of
the red. The full run is at `verify.log` in the session scratchpad.

**Run 2 — after the one comment correction in section 6, and CONTAMINATED.**
Exit 1, same single red, but by then other agents had landed work in
`Core/ValuePanel.cs`, `Game/SimDirector.cs`, `CoreTests/Program.cs` and
`tools/lint-static.py`, so it reads 206 changed lines and 4104 CoreTests and
is not a reading about me. Two things in it are worth passing on because
they are NOT mine and will confuse the next reader of that footer:

- `0 static/instance errors (75 members, **29 bodies**)` — run 1 walked
  **562** bodies. That is the in-flight `tools/lint-static.py` rewrite, and
  a denominator collapsing by 20x is exactly the shape rule 3b exists for.
  Worth a look before that lint is committed.
- the `docs` entry vanished from the footer entirely. Run directly,
  `tools/docs-check.py` reports `1 problem(s)`:
  `FAIL lint-static-denominator.md declares a status in its first 8 lines —
  no STATUS banner`, which is the other agent's untracked report, not this
  one. `aerial-mirror.md` passes both its checks
  (`LOG entry carries its date`, `LOG entry says it is not current`).
