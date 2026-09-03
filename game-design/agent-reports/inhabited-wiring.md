# The inhabited street — wiring the garment split and the female walk

> **STATUS: LOG, 2026-08-25. NOT CURRENT**

Part 4 items 1 and 2 of `visual-bar-spec.md`, from
`research/inhabited-street.md` §1.4(a) and §1.4(c). Both were named as
"finish the wire on something already built"; both were, and one of them
turned out to be a much better wire than the research thought.

---

## 0. THE FINDING THAT CHANGED THE JOB — the research was wrong about the meshes

`research/inhabited-street.md` §2.2 says, of GTA's component drawables:

> **NEVER, and correctly** — Mixamo bodies are single welded meshes; we have
> no garment slots and building them is a modelling pipeline, not a code
> change

That is false for most of the roster, and it was checked by parsing the mesh
node names out of all eighteen FBX under `Assets/Characters` rather than by
reading the code that loads them. The research read the code; nobody had read
the assets. **Eleven of the sixteen pool bodies ship a separate upper AND
lower garment mesh:**

| model | meshes |
|---|---|
| Adam | Beard, Body, Eyelashes, Hair, **Hoodie**, **Pants**, Sneakers |
| David | Body, Eyelashes, Hair, **Hoody**, **Pants**, Sneakers |
| Elizabeth | Body, Eyelashes, Hair, Heels, **Shirt**, **Pants** |
| Joe | **Belt**, Body, Eyelashes, Hair, **Pants**, **Shirt**, Shoes, **Suit**, **Tie** |
| Kate | Body, Eyelasshes *(sic)*, Hair, **Pants**, **Shirt**, Shoes |
| Leonard | Body, **Collar**, Eyelashes, Hair, **Pants**, Shoes, **Sweater** |
| Martha | Body, Eyelashes, Hair, Heels, **Pants**, **Shirt**, **Suit** |
| Pete | Body, Boots, Eyelashes, Hair, Helmet, **Pants**, **Shirt**, **Vest** |
| Remy | Body, **Bottoms**, Eyelashes, Eyes, Hair, Shoes, **Tops** |
| Shannon | Body, Eyelashes, Hair, **Shirt**, Shoes, **Shorts**, Socks |
| The Boss | Arms, Cigar, Hat, **Jacket**, L_Eye, **Pants**, R_Eye, Shoes, Teeth_Up/Down |
| Sophie | Body, **Cloth**, Eyelashes, Hair, Sneakers, Socks — upper only |
| James | `Ch06` — one welded mesh |
| Michelle | `Ch03` — one welded mesh |
| Big Vegas | BodyGeo, BrowsAnimGeo, EyesAnimGeo, MouthAnimGeo — welded + face parts |
| Sporty Granny | same shape as Big Vegas |

So a navy coat over stone trousers is a **naming problem**, not a modelling
pipeline. Materials do not have to be split with it: Kate carries six meshes
on two materials, and `Tint` writes a `MaterialPropertyBlock`, which is
per-RENDERER state — different renderers sharing one atlas still take
different wash colours.

---

## 1. WIRE ONE — coat, trousers and skin can now differ

**Before.** `RealBody.TryAttach` walked every renderer, and any renderer whose
material carried a texture got `Tint(r, ch, cs, cv, sheet)` — **one colour, on
every mesh, head included.** `BodyParts.Assign` was never consulted because it
sits on the untextured path, which no shipped model has reached since texture
extraction landed (`bodyParts=[nothing to paint — all 9 renderer(s) came
textured]` in the landed verdict at `36b90c9`).

**After.** The textured renderers are gathered first, then classified once over
the whole model by a new Core rule, then washed per class.

- `Core/BodyParts.Garments(string[])` → `Own` / `Whole` / `Upper` / `Lower`.
- **Upper** takes the existing coat draw. **Lower** takes a SECOND
  `Wardrobe.Dress` under salt 11 (Physique spends 1–8, the body-model pick
  uses 23). **No cast lift on the lower draw** — the street identifies the
  player by their coat, and lifting both would put two bright garments on one
  body under a ceiling that exists to stop exactly that.
- **Own** — faces, hair, eyelashes, brows, mouth, teeth, shoes, socks, hats,
  a cigar — is left carrying the artist's texture and is not washed at all.
  Not washed white: a multiply by white is the same pixels but not the same
  NUMBER, and pushing every face through `Tint` would bury `WashNearWhite`'s
  wardrobe fault under skin that was never meant to be dressed.
- **Whole** is the welded case, and it takes the coat draw over the entire
  figure — byte-for-byte what every body got before this change, so James,
  Michelle, Big Vegas and Sporty Granny are not regressed by it.

**The structural rule, which is `Assign`'s applied to a new axis.** `Ch21_Body`
is Kate's bare arms because her shirt and trousers are separate meshes;
`Elvis_BodyGeo` is the whole of Big Vegas including his clothes because nothing
else on him is a garment. Both are called "body". Only the model's structure
tells them apart, and structure is checkable: *a model with any garment mesh
treats skin as skin; a model with none treats skin as the whole person.* Face
parts stay `Own` under both branches — Big Vegas's brows are the same fault at
a smaller size.

**`Words` now splits camelCase.** Read off the roster, not imagined:
`Elvis_BrowsAnimGeo` is one word under separator-splitting alone, matches
nothing, and gets washed with the coat colour. A lowercase letter followed by
an uppercase one is a word boundary, and it is still EQUALITY afterwards —
`browsanimgeo` never becomes `brows` by containment, only by being cut at the
capital. `Beta_Surface` is unchanged (no lower-to-upper transition inside
either word) and the CoreTest named after the naked-player bug is asserted
again immediately after the split, first in the list.

`brows` and `mouth` joined `BodyParts.Bare` because the camel split made them
reachable and both are bare skin by any reading. `eyelasshes` joined it too —
that is Kate's shipped spelling and the model file is the authority.

**No second palette.** Both draws are `Wardrobe.Dress` over the same eight
authored bands, the same `MaxValue = 0.46` ceiling, the same `Mix` fold. One
idea, one implementation. Nothing here authors a colour.

**The word lists carry no invented synonyms.** `coat`, `blouse`, `parka`,
`jeans`, `skirt` are not on any shipped mesh and are not in the list. The next
drop's vocabulary arrives as a READING — `bodyPartsUnknown` reports the
renderer names nothing matched, so a drop whose garments are called
`Ch44_Anorak` shows up as a name instead of silently rendering like a welded
model.

### What this will do to numbers that already have a series

`bodyTinted` and the whole `bodyWash*` family counted every textured renderer.
They now count CLOTH only; faces and hair are counted by `bodyPartsOwn`
instead. **Their landed series has a regime change at this commit and will
fall against their own history — that fall is the fix, not a regression.**
Said in the code beside the counter, because a number keeps its name when the
question it answers moves.

**One thing to READ in the next still rather than assume.** Skin renderers used
to be pulled toward `MaxValue` by the coat wash along with everything else.
They are now at the model's own albedo, which the measured sheet series puts as
high as 0.78. Faces may read brighter. `bodyBrightestPart` already names which
mesh was the palest thing in a frame, so this is instrumented — no ceiling has
been invented for skin, because there is no reading yet that says one is
needed.

---

## 2. WIRE TWO — women walk the female cycle

`walk_f__Female Walk` has been in `Assets/Characters/B` since the B harvest and
`tools/clip-reach.py` listed it under DISK-ONLY. What was holding it was a
comment in `CharacterPrefab.ArchetypeFor`:

> *"'old' is the only special archetype until a female walk clip actually
> exists in the harvest; wiring an archetype whose clips cannot arrive would
> be rule 6 in advance."*

Correct the day it was written, false ever since the clip landed, and it read
like a decision rather than a stale claim. Every woman in Meridian walked the
male cycle behind it.

**`Core/BodyArchetype`** now owns the rule: `Of(stem)` → `default` / `old` /
`female`, `ControllerName(arch, idleKey)`, `ControllerCarries(name, arch)`,
`Roster(stems)`. It is in Core because two callers in two assemblies need the
same answer — the Editor writes one controller per archetype at import time,
the runtime reads the controller name back to prove the wire reached the street
— and because neither assembly compiles in this container.

- **Editor**: `ArchetypeFor` delegates to `BodyArchetype.Of`; `BuildLocomotion`
  gains a `female` branch taking `ClipFor("walk_f") ?? ClipFor("walk")`; the
  variant asset path is `BodyArchetype.ControllerName`, so the string the
  Editor writes and the string the runtime compares are one string.
- Female bodies keep the idle-variant spread (`SpreadsIdle`), because the
  archetype axis is the WALK and two women at a corner should still not
  breathe in unison. `old` stays out — `idle_old` is its own pose.

**Why a name list and not a measurement.** `Proportion` argues, correctly, that
a hand-written list of names is a judgement with no number under it — and
replaces one with a measured ratio. That argument does not carry here: whether
Mixamo's `Kate` is a woman is a fact about the ASSET, and no bone height
separates `Kate` from `Joe` without also separating tall men from short ones.
What the list owes instead is visibility, and `bodyKinds` is it.

**Sporty Granny is `old`, not `female`, and that is a judgement said out loud.**
She is both and there is no `walk_old_f`; age wins because the stoop and the
shortened stride separate a walk from the crowd more than sex does. If a
`walk_old_f` ever lands, that is the line to change.

---

## 3. THE TWO COUNTERS, and which statistic each is

    bodyPartsDistinct=n/total     bodyPartsWelded=n  bodyPartsUpperOnly=n
    bodyPartsOwn=n                bodyPartsUnknown=[names]
    bodyTrousers=[band hsv=h/s/v]
    walkFemale=n/total            bodyKinds=[stem:arch/...]
    bodyController=[arch->name]

**`bodyPartsDistinct` — CUMULATIVE, counted per body ATTACH.** Numerator:
bodies given both an upper-garment draw and a lower-garment draw. Denominator:
bodies on which the wardrobe washed anything at all. Body LOD grants and
revokes continuously, so a walker granted a body four times is four events —
**it is a count of dressing events, not of citizens**, and it is read on the
done line, never inside a screenshot hook. `bodyPartsWelded` and
`bodyPartsUpperOnly` are the two off-diagonal cases named rather than summed
away, and the three sum to the denominator by construction, so a reader can
check the arithmetic on the line.

**`walkFemale` — CUMULATIVE, same units.** Numerator: attachments whose model
is a woman AND whose Animator arrived holding a `female` controller.
Denominator: attachments whose model is a woman. It reads the Animator rather
than re-asking `BodyArchetype.Of` — asking the classifier twice would print a
perfect score on a build where the Editor step never wrote a female controller,
and two numbers derived from one variable are one number twice.

**Below-equal is the state to watch**: `BuildLocomotion` falls back to `walk`
when `walk_f` is missing, and a woman on the male cycle looks completely
normal. `bodyKinds` is the denominator's denominator — it says whether the pool
has women at all, which `0/0` cannot.

**No bound and no gate on either.** There is no landed series yet and a
threshold set off one run is invented. What the numbers are FOR: eleven of the
sixteen pool models ship both garment meshes, so a healthy `bodyPartsDistinct`
should settle near that share once the body picks spread across the roster —
that is a PREDICTION to check the first series against, not a bound.

---

## 4. The other unreferenced clips, ranked for a LATER batch — not wired here

`clip-reach` went 41 → 40 DISK-ONLY. Ranked by what a still would show:

1. **`walk_stop`, `walk_start_f`, `walk_stop_f`, `turn_left`, `turn_right`** —
   the transitions. Without them a walker snaps between standing and full
   stride, which is the single most mannequin-like thing a crowd does. Needs
   real transition work (conditions, exit times) rather than another blend-tree
   child, so it is its own batch.
   **AND `walk_start` IS A MIS-PICK — DO NOT WIRE IT AS IT STANDS.** The file
   on disk is `walk_start__Start Walking Backwards_4f5d….fbx`;
   `tools/mixamo-pick/pick_animations.py:165` matches `\bstart walking\b` and
   "Start Walking Backwards" satisfies it. Wiring that would have every man in
   the city set off backwards. `walk_start_f` (`Female Start Walking`),
   `walk_stop` (`Stop Walking`) and `walk_stop_f` (`Female Stop Walking`) are
   all correct.
2. **`pockets`, `laugh`, `shake_hands`, `sit_talk`, `sit_drink`, `rummage`,
   `lift`, `yell`** — pure additions to `CharacterPrefab.ActivitySlots` plus an
   ask in `NpcWalker`. Takes idle/activity variety from 4 toward the 5–8 the
   sourced guidance calls convincing. Cheapest visible batch on the list.
3. **`jog`** — one more blend-tree child above `walk`; escorts already hurry at
   2.6 m/s and currently play the walk cycle stretched.
4. **`stairs_up`, `stairs_down`** — need the walker to know it is on stairs;
   real work, real payoff on the quay steps.
5. **`back_away`** — a reaction retreat; `NpcWalker.React` is the existing
   consumer shape.
6. **The combat and knockdown set** — `guard`, `guard_enter`, `guard_exit`,
   `block_start/hold/end/broken`, `strike`, `strike_alt`, `shove`, `shoved`,
   `take_hit`, `knockdown`, `stagger`, `collapse`, `get_up`, `lie_still`,
   `hands_up`, `draw_gun`, `draw_holster`, `draw_reach`, `fall_stairs` —
   **twenty of the forty**, all gated on Standoff/Combat reaching the street
   rather than on animation wiring. None of them shows in an ambient still,
   so they are last on a "visible in a frame" ranking even though they are the
   biggest block.
7. **Still genuinely EMPTY (the harvest hole): `smoke`, `thinking`** — and
   `NpcWalker` already asks for `smoke` at corners and homes, so that ask is
   refused every time it fires. A fetch, not a wire.

---

## 5. Comments re-read, and the ones this change falsified

| where | was | now |
|---|---|---|
| `CharacterPrefab.ArchetypeFor` | "'old' is the only special archetype until a female walk clip actually exists in the harvest" | quoted and corrected in place; the clip has existed since the B harvest |
| `RealBody`, the `Parts` assembly | "`parts=()` … every renderer arrived textured … there was nothing left to paint" | a textured renderer is no longer "nothing to paint"; the line now names every mesh under either rule and the old sentence is quoted so it cannot be re-derived |
| `RealBody.Tinted` | a lifetime count of renderers washed | still true, but the POPULATION changed to cloth-only; the regime change is stated beside the counter |
| `RealBody`, "SO THE TEXTURE STAYS AND THE WARDROBE COMES BACK AS A WASH" / "NO NEW COLOUR" | one triple, one wash | two draws from the same table, stated as such; each draw is still "no new colour" |
| `BodyParts.Bare` | a fixed list | `brows`, `mouth`, `eyelasshes` added with the models they were measured on |
| `BodyParts`, hair paragraph | "painting it either is wrong" | unchanged and now enforced on the textured path too, which is cited in the new section |

**Not edited, flagged for the director instead** (they are SPEC documents, and
editing a spec is a decision rather than a wiring job):
`research/inhabited-street.md` §2.2's "Mixamo bodies are single welded meshes;
we have no garment slots" is false for eleven of sixteen bodies, and §1.4(a)'s
"`BodyParts.Assign` … is never consulted" and §1.4(c)'s `walk_f` entry are both
now historical. `visual-bar-spec.md` P4's stand paragraph carries the same two
claims.

---

## 6. What was run

`python3 ledger/verify.py` — green. `3901 CoreTests`, `0 lint errors`,
`0 shape errors (187 files)`, `Game layer compiles (181 files)`,
`0 filename-as-type errors`, `0 namespace-as-value errors`,
`0 static/instance errors`, `35 on the reach ledger` with no unreached entry.
`python3 tools/clip-reach.py` — `walk_f` has moved from DISK-ONLY into TREE;
DISK-ONLY is 40.

**The Game layer does not compile here** beyond the shape and name-resolution
lints, so nothing above is a claim about a Unity API until the Windows build
returns. The two counters have never been printed by a running sim.
