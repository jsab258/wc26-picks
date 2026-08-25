# The two white plinths — unwrapped (builder account)

LOG — 25 Aug 2026. NOT CURRENT after the next landing.
Builder report (systems-builder), for item D of the batch review in
`decision-ground-albedo.md`. Nothing committed; the tree is left dirty for
director review. Every claim below was checked against the source in this
session.

---

## 1. WHAT CHANGED — two call sites in `WorldBuilder.cs`, nothing else

`ledger/Assets/Scripts/Game/WorldBuilder.cs`, the only file edited.

`PhoneBox_plinth` (was :2433) now reads:

    MakeBox("PhoneBox_plinth", at + new Vector3(0, 0.05f, 0),
        new Vector3(1.05f, 0.1f, 1.05f), AssetLibrary.Concrete);

`PostBox_plinth` (was :2461) now reads:

    MakeBox("PostBox_plinth", at + new Vector3(0, 0.04f, 0),
        new Vector3(0.62f, 0.08f, 0.62f), AssetLibrary.Concrete);

The `Tint(...)` wrapper and its `Color.white` argument are gone from both.
Sizes, positions, names and the `AssetLibrary.Concrete` logical surface are
byte-identical to before. `MakeBox` returns a `GameObject` that both sites
already discarded — `Tint` returned the same object — so dropping the
wrapper is an expression-statement discard, not a lost reference.

**Beyond the two deletions I added comments at both sites** (8 lines at the
phone box, 3 at the pillar box, back-referencing it). Flagged here because
the order said nothing else moves: comments cannot confound the
measurement, and the decision record's own "must NOT re-litigate" list says
*do not "restore" a tint via MPB* — with no note at the site, a bare
`MakeBox(..., Concrete)` is indistinguishable from every other bare
`MakeBox` in the file and re-adding a tint looks like an improvement. Strip
them if you disagree; they are the only non-deletion in the diff.

## 2. WHY THE UNWRAP DOES WHAT THE RECORD SAYS — verified, not assumed

`AssetLibrary.cs:896` (read only, not edited):

    static readonly string[] WetSurfaces = { Asphalt, Sidewalk, Kerb, Concrete };

`Concrete` is in the family, so the shared `mat_concrete` material takes
`GroundGrade` through `BaseColour` (`AssetLibrary.cs:535-540`, folded in at
`:572` on the dry base) and is walked by the wetness loops at `:811` and
`:883`. `MakeBox` hands the renderer `AssetLibrary.Material(logical)` —
that same shared instance (`WorldBuilder.cs:3970-3978`). So bare Concrete
is the graded, wetness-tracking material, and the plinths now move with the
road for the first time.

Why they did not before: `WorldBuilder.Tint` (:2551 in the pre-change file)
does `mpb.SetColor("_Color", c)` and `r.SetPropertyBlock(mpb)`. A property
block REPLACES the material's `_Color` for that renderer; it does not
multiply it. `Color.white` therefore pinned both plinths at raw texture,
full white, immune to both the grade and the weather.

## 3. THE TWIN SWEEP — every `Tint(` call site in the Game layer

`grep -rn "Tint(" ledger/Assets/Scripts/ --include=*.cs`, all 16 hits, each
one opened and read. Colours are the literal RGB passed.

| site | object | colour passed | ground level? |
|---|---|---|---|
| `WorldBuilder.cs:516` | `Yellow_*` kerb lines | `0.62/0.52/0.18` | YES, y+0.045 |
| `WorldBuilder.cs:543` | `Zebra_*` stripes | `0.85/0.86/0.84` | YES, y+0.055 |
| `WorldBuilder.cs:557` | `Belisha_*_ball` | `0.95/0.62/0.12` | no, y+2.65 |
| `WorldBuilder.cs:2311` | `Parked_*_body` | `paint` (see below) | no, y+0.62 |
| `WorldBuilder.cs:2314` | `Parked_*_cabin` | `paint` (see below) | no, y+1.28 |
| `WorldBuilder.cs:2433` | **`PhoneBox_plinth`** | **`Color.white`** | **YES — REMOVED** |
| `WorldBuilder.cs:2445` | `PhoneBox_glass_*` | `0.16/0.19/0.22` | no, y+1.35 |
| `WorldBuilder.cs:2448` | `PhoneBox_bar_*` | `0.62/0.07/0.07` | no |
| `WorldBuilder.cs:2450` | `PhoneBox_sign_*` | `0.90/0.88/0.80` | no, y+2.25 |
| `WorldBuilder.cs:2461` | **`PostBox_plinth`** | **`Color.white`** | **YES — REMOVED** |
| `WorldBuilder.cs:2484` | `PostBox_slot` | `0.10/0.10/0.10` | no, y+0.98 |
| `StreetFurniture.cs:392` | `NoEntry_*` disc | `0.60/0.09/0.09` | no, y+1.95 |
| `WorldBuilder.cs:2551` | the definition | — | — |
| `WorldBuilder.cs:1756` | a comment, not a call | — | — |
| `RealBody.cs:659` | DIFFERENT `Tint` (see §4) | HSV via `Wardrobe.Wash` | — |
| `RealBody.cs:1142` | its one call | `ch/cs/cv` + sheet albedo | — |

`paint` for the parked cars is `GameController.KitPaints[...]`
(`TrafficHost.cs:988-996`): navy, black, burgundy, bottle green, grey,
stone — every channel between 0.12 and 0.48. No white reachable.

**THERE IS NO THIRD PURE-WHITE SITE.** `Color.white` appears four more
times in the whole of `Assets/Scripts` and not one is a surface tint:
`WorldBuilder.cs:2397` (smoke particle gradient), `AssetLibrary.cs:1239` (a
fallback when a material has no `_Color` to READ), `ClipSheet.cs:269` (a UI
key colour), `GameController.cs:3408` (a light colour lerped toward white
by daylight).

**What IS true of every row above, and is the deeper twin:** because `Tint`
REPLACES `_Color`, *no* tinted object can darken with wetness or carry the
ground grade — the plinths were only the extreme case, where the
replacement colour was 1.0. Two of these sit on the road surface and are
explicitly ORDERED TO STAY (paint reading lighter than wet tarmac is
correct), so they are reported, not touched:

- **`Zebra_*` at `0.85/0.86/0.84` is the brightest surviving ground-level
  tint** and the nearest thing to a third white site. Zebra stripes on a
  0.55 road will read very bright, by design and by order.
- `Yellow_*` at `0.62/0.52/0.18` is the other one, mid-value.
- `PhoneBox_sign_*` at `0.90/0.88/0.80` is the highest-value tint left in
  the file, but it is a cream sign band 2.25m up a red box, not a ground
  surface next to graded tarmac.

Adjacent, NOT a `Tint` site and NOT changed: `TrafficHost.cs:1008`
`PatrolWhite = 0.88/0.88/0.90`, applied through `AssetLibrary.PaintKit`,
whose comment states it is a multiply that preserves the model's internal
ratios. Different mechanism, and the comment says its value was chosen to
stay under the palette ceiling.

## 4. A NAME COLLISION WORTH KNOWING BEFORE THE NEXT GREP

`RealBody.cs:659` declares a **second, unrelated `Tint`** —
`Tint(Renderer, double hue, double saturation, double value, double
albedo)`, private, one caller at `:1142`. It runs the wardrobe wash and
converts to linear BY HAND precisely because MPB colours skip the
gamma→linear conversion. Any future `grep "Tint("` returns both families;
they share nothing but four letters.

## 5. COMMENTS RE-READ FOR CLAIMS THE DELETION FALSIFIED

Everything within reach of the two edits, whether or not it was touched:

- `PhoneBox` docstring (:2425-2429) — describes shell, cap, glazing, bars,
  sign band, and said the RED is a property-block multiply. Says nothing
  about the plinth or its colour, so **not falsified by the deletion** — but
  false on its own terms, and **now corrected under §6.2**.
- `PostBox` docstring (:2456) — "red drum on a plinth": **still true**, the
  plinth is still there.
- `PostBox_drum` comment (:2467-2474) — the account of the MPB not reaching
  that renderer and the colour moving into the material. **Still true, and
  now has a sibling**: it is the same mechanism biting a second way.
- `MakeBoxCol` docstring (:3955-3959) — "a flat colour ... whose material
  must not be a tint that can go missing", naming pillar box and phone box.
  **Still true and unaffected**: the plinths never used `MakeBoxCol`.
- `Tint`'s own docstring (:2549-2550, now shifted) — said "colour multiply".
  Against a texture that is what it looks like; against the material colour
  it is a REPLACE, which is this whole finding. **NOW CORRECTED under §6.1**;
  it was left alone at first because the order scoped this to two deletions,
  and the coordinator then took it into the batch.

Nothing outside `WorldBuilder.cs` references either plinth: `grep -rn
"plinth"` returns 5 hits, three of them these sites plus the `PostBox`
docstring, and two in `TrafficHost.cs:830-833` about a lamp plinth on a
patrol car roof — a different object entirely.

## 6. THREE MORE COMMENT REPAIRS — ordered by the coordinator after §7

Comment-only, no expression changed, so the measurement this batch exists
to obtain cannot move.

1. **`Tint`'s docstring** (now :2559). Said "Property-block colour multiply".
   It now says plainly that a property block REPLACES `_Color` for that
   renderer — a multiply against the TEXTURE and a replace against the
   MATERIAL — and carries the consequence, which is the part worth keeping:
   a tinted object gets neither the ground grade nor the wetness walk,
   because both are written to the shared material's colour and the block
   overwrites it. It then says which jobs a tint is right and wrong for, and
   points at both plinths and at `PostBox_drum`.
2. **`PhoneBox`'s docstring** (:2428-2435). Said "Red is a property-block
   multiply over the plaster base". **Doubly false, and checked before
   rewriting**: the shell, cap and dome go through `MakeBoxCol` ->
   `AssetLibrary.Opaque(red)` (:2443, :2445, :2447), a REAL shared material
   — not a property block, and so not a multiply either. Only
   `PhoneBox_bar_*` (:2456) still uses `Tint`. This is comment decay from
   the pillar box's repair: `PostBox_drum` moved off the property block for
   cause and got its comment updated, and the phone box was the twin nobody
   re-read.
3. **The class docstring** (:6-8). Said "a purchased pack later". Nothing in
   this project is purchased (CLAUDE.md §0); it now says a FETCHED pack, and
   says why in one clause.

**The one "multiply" wording left, deliberately:** `PostBox_drum` (:2489),
"The property-block multiply is not reaching this renderer". Left alone
because its CLAIM is about reach rather than about the operator, and it is
a dated account of a diagnosis that still stands — under replace semantics
a block that reached with red would have shown red, and the drum was white.
Named here so the next grep for the word finds this paragraph.

## 7. WHAT WAS RUN, AND THE RED THAT IS NOT THIS CHANGE

**`python3 ledger/verify.py` — rc=1, `ledger/.verify-footer` ABSENT.** Two
causes, neither in this diff, and both verified against the tree:

1. **`DIRECTOR NOT SPAWNED`** — 562 changed lines under `Assets/Scripts`
   against a threshold of 100, with no `studio-director` row newer than
   HEAD. **HEAD MOVED underneath this task**: `80a91049` (00:26:00Z) ->
   `74253838` (00:44:36Z), and the newest director row is 00:31:43Z. This
   is the batch-review escalation gate doing its job on a commit that is
   not mine; only the director can clear it. The 562 lines are the pooled
   uncommitted work of three builders — `AssetLibrary.cs` and
   `SimDirector.cs` are another agent's live batch.
2. **`UNTRACKED/ABSENT TOOL(S): tools/ci-checks.sh(untracked)`** — a new
   tool another agent has not staged yet. `tools/reach-check.sh` was in
   this list one run earlier and is gone from it now, which is that agent
   working, not drift.

**An earlier full run of the same tree, before HEAD moved, was GREEN
(rc=0, footer written), with this change already in place.** That run is
the evidence that the plinth edit passes; the red above arrived with a
commit and a sibling's untracked file.

Everything a Game-layer edit is checked by is clean in the red run:

    0 lint errors
    0 shape errors (183 files, 3 with conditional code)
    Game layer compiles (177 files)
    0 filename-as-type errors (183 files, 13 filenames that are not types)
    0 namespace-as-value errors (183 files, 4 segments in scope)
    0 static/instance errors (75 members, 523 bodies)
    0 nested-type errors (248 Core types)
    0 shadowed Core types (274 types, 87 Game files)
    docs 61/61 clean
    3761 CoreTests

The five name-resolution lints were also run individually: all rc=0.

**On the director's `WorldBuilder`-is-not-a-type warning: checked, and it
does not apply to this file.** `WorldBuilder.cs:11` declares `public static
class WorldBuilder`. The trap is real for the 13 filenames `lint-filetype`
counts as non-types (`TrafficHost.cs` declares `partial class
GameController`), but this is not one of them, and the pre-existing
`WorldBuilder.Tint(disc, ...)` at `StreetFurniture.cs:392` is legal and
passes that lint today. This change introduced no new type reference.

**`docs 61/61` did not move when this file was added, and that is correct
rather than a miss:** `tools/docs-check.py:42` globs `game-design/*.md`, one
level, so nothing in `agent-reports/` is examined. The LOG header at the top
of this file is convention, matching its siblings, not an enforced check.

## 8. NOTICED, NOT DONE — for the queue

1. **`tintedGroundPeak` — an instrument, and it is instrument-builder's.**
   Nothing measures the albedo of MPB-tinted objects against the graded
   road; the plinths were found by a person reading code. Shape: max
   `_Color` value over objects with a property block at y < 0.3, with the
   COUNT of tinted ground objects as its denominator, series first and no
   bound (rule 2's order). It would have printed 1.00 for as long as this
   bug existed. **A reader already exists to borrow:** `SimDirector`'s
   `SurfaceUnder` deliberately reads the property block rather than
   `sharedMaterial` (see its comment, "THE PROPERTY BLOCK IS READ, AND THAT
   IS THE POINT"), but it is ONE ray down the middle of the dark third at
   noon — it would have caught a plinth only by luck.
2. **Thirteen MPB sites are named in `SimDirector` as still waiting on a
   verdict** for the gamma-to-linear shortfall (comment at the noon facade
   ladder). Unrelated to this change, but it is the same mechanism and the
   same file family; whoever takes item 1 should read it first.
