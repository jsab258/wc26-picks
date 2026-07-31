# Shopping list — characters and animation

> **STATUS — LIVE, verified 2026-07-31.** what still needs buying, and what no longer does.
> Kept current. If it is wrong, that is a bug in this file.

**For Jafar. Written 2026-07-28. Nothing here has been bought.**

The brief was "minimal manual work for me", so this is written as a
checklist rather than as research. Everything I could decide, I decided.
What is left is the part only an account holder can do.

**Total: $0–80.** Three of the four items are free.

**Prices and product names must be re-checked when you actually buy** — I am
working from knowledge, not from a live store page, and asset stores rename
and re-bundle things constantly. If a name below does not exist any more, the
"what it must have" column is the real spec; match against that.

---

## 1. Characters — the only thing that costs money

**What to search for on the Unity Asset Store:** `POLYGON` by **Synty
Studios**. That is the publisher; the POLYGON series is their low-poly
modular range.

**Which pack:** whichever POLYGON set is closest to **city / noir /
gangster / crime / urban 1980s-90s**. Candidates that have existed under
these or similar names — check what is current:

- **POLYGON Gang Warfare** — closest to the setting by a distance
- **POLYGON City** — the generic urban set, good fallback
- **POLYGON Noir** — if it exists now, buy this one instead of the others

**WAIT FOR A SALE.** Synty discount heavily and often — publisher sales,
seasonal sales, and Humble Bundle appearances. Full price is roughly $60–90
per pack; on sale it is usually $20–40. There is nothing in the build that
is blocked on this arriving today, so paying full price would be paying for
nothing. If you see 50% or better, buy.

**Buy ONE pack, not three.** More packs is more art that has to be made to
agree with itself, and mixing two art styles looks worse than one style used
consistently. If the pack is short a character type I will build it from the
modular parts.

### What the pack MUST have — check these before paying

| Requirement | Why it matters here |
|---|---|
| **Humanoid rig** (Mecanim-compatible) | Non-negotiable. Without it Mixamo animations do not retarget and the whole free-animation plan collapses |
| **Modular parts** — swappable heads, tops, legs | We need ~700 background people out of one purchase. Without modularity the crowd is six clones |
| **Silhouette variety** — hats, coats, bags | The gaze and stance systems need characters legible at 30m. A coat is a MECHANIC in this game and must read across a street |
| **Not photoreal** | Stylised is the chosen direction. Realism with a $80 budget guarantees looking cheap |
| **Licence permits commercial use** | Standard Unity Asset Store licence does. Just confirm nothing says "editorial only" |

### What it does NOT need

Facial blendshapes, LODs, PBR textures, and included animations. I do not
need any of them, and paying more for a pack that has them is waste.

---

## 2. Animations — FREE

**Mixamo** (mixamo.com, Adobe). Free with an Adobe account, free for
commercial use, no per-download cost.

**Do nothing here.** Once the characters land I download what we need
myself. Listed only so you know it is covered and not a hidden cost.

---

## 3. Look-at IK — FREE

**Unity Animation Rigging** package, installed from Package Manager inside
the project. Free, first-party.

**Do nothing here.** This is the one that makes M15.2's gaze system read as
people watching you rather than as capsules rotating — but it is a package
install, and I do that.

---

## 4. Locomotion controller — FREE

Hand-built on the momentum already in `Assets/Scripts/Core/Feel.cs`, which is
tested. Buying one for $50–100 would mean throwing that away and adopting
someone else's movement model.

**Do nothing here.** Listed so the earlier $50–100 line in the budget is
explicitly cancelled rather than silently dropped.

---

## THE ACTUAL CHECKLIST

1. Unity Asset Store → search **Synty POLYGON**
2. Pick the pack closest to **urban crime / noir**
3. Check: **humanoid rig**, **modular parts**, **commercial licence**
4. **If not on sale, add to wishlist and wait.** Nothing is blocked
5. Buy it, then in Unity: `Window → Package Manager → My Assets → Download → Import`
6. Tell me the pack name

That is all. Step 6 is the one I need — once I know which pack, I do the
rest: retargeting, the modular crowd generator, the wardrobe system that
makes the coat legible, and the gaze rig.

---

## Two things I am deliberately NOT asking you to buy

**Environment and prop packs ($0–40 in the budget).** I want to exhaust
**Kenney** (kenney.nl, CC0) and **Poly Haven** (polyhaven.com, CC0) first.
Both are free and public domain, and between them they cover most street
furniture. I will come back with a specific gap if one exists rather than
buying a bundle against a vague need.

**Audio libraries ($0–25).** Most of the game's sound is synthesised at
runtime already, and **freesound.org** covers a lot of the rest. Same
approach: name the gap, then buy.

---

## What happens after the pack lands

In rough order, all my time and no more money:

1. Retarget Mixamo's idle/walk/run/talk/sit onto the rig
2. Blend trees, driven by the existing momentum in `Core/Feel.cs`
3. The modular crowd generator — one pack into hundreds of distinct people
4. Wardrobe, so the coat is visible at distance because it is a mechanic
5. Animation Rigging look-at, so the gaze system finally reads
6. Foot IK, so feet plant on kerbs instead of sliding
7. The injury limp, which currently exists only in the footstep rhythm,
   moves onto the body
