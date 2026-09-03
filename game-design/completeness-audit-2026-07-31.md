# Completeness audit — is the roadmap actually a plan for a finished game?

> **STATUS: LOG, 2026-07-31. NOT CURRENT.** A dated audit of what the roadmap
> covers and what it does not. The findings were folded into `roadmap.md` the
> same night; that file is the plan and this one is the evidence.

Jafar, after I confirmed there are no textures in the project: *"huge oversight.
makes me question the thoroughness and completeness of the whole plan/roadmap.
validate."*

Correct response, and the answer is that he is right — there are **nine** gaps,
the textures were one of them, and they share a single cause.

---

## The cause, first, because it predicts the rest

**The roadmap was derived from the work queue, not from a definition of done.**

Every milestone in it is a set of *behaviours*: perception and violence (M16),
the second life (M18), the city pushing back (M19), the shape of a playthrough
(M20), firearms (M21). Those are excellent and they are the moat. M17 is the one
milestone that is not a systems milestone, and it lists exactly four things —
bodies, voices, barks, foley — which are the four things somebody happened to be
working on when it was written.

Nothing in the roadmap was ever derived by asking *what does a shippable game
need, and which of those do we have*. It was derived by asking *what are we
building next*. A plan built that way is complete about the things you are
already thinking about and silent about everything else, and the silence looks
exactly like coverage.

That is the same failure as `built is not running`, one level up. A system with
no call site looks finished in a code review; a category with no milestone looks
finished in a roadmap.

---

## What was checked, and how

Not by reading the roadmap and asking whether it felt complete — by enumerating
what a shipping game of this kind contains and checking each against the repo
with a command. The evidence column is what the command returned.

| # | category | state | evidence |
|---|---|---|---|
| 1 | **Surface textures** | ✗ nothing | `find Assets -type f ! -name "*.cs"` → 44 fbx, 4 shader, 0 image files. Every surface is `ProceduralTexture.Generate` — tiling noise, brick and plank patterns |
| 2 | **Environment / prop models** | ✗ nothing authored | 10 `CreatePrimitive` call sites across `WorldBuilder`, `StreetFurniture`, `TrafficHost`. The city is boxes |
| 3 | **Vehicle models** | ✗ nothing authored | same — vehicles are primitives with a colour hint |
| 4 | **Weapon models** | ✗ nothing at all | 19 weapons in `Arsenal` as data; no mesh, no held-object rendering. A game whose spec says *the threat is the main use of a weapon*, in which the weapon is invisible |
| 5 | **Fonts** | ⚠ borrowed from the OS | `UiTheme.LoadFont` → `Font.CreateDynamicFontFromOSFont(["Segoe UI", "Arial"])`. Ships no font. Segoe UI is Microsoft-licensed and not redistributable; on macOS and Linux this falls through to Arial or Unity's legacy fallback, so the game's typography differs per machine |
| 6 | **UI icons** | ✗ none | no icon references in `UiTheme`; the interface is text-only |
| 7 | **Credits / attribution / licences** | ✗ none | no `LICENSE`, no credits screen, no attribution file. **VCTK is CC BY 4.0 — attribution is required, not optional.** Mixamo carries its own terms. Any CC0 texture pack usually requests it |
| 8 | **Localisation** | ✗ none | no localisation infrastructure anywhere in `Assets/Scripts`; every player-facing string is a C# literal. English-only may be the right call — it has never been recorded as a call |
| 9 | **Packaging / release** | ✗ none | no app icon, no splash, no store metadata. CI produces a build artefact and nothing turns that into something a person installs |

### Two things that are NOT gaps, checked before claiming they were

- **Film grain, vignette and bloom.** `production-plan-audio-art.md` §4 still
  says these are *"named in the art direction and not built"*. That line is
  stale: `FilmGrade.cs` exists and the CI verdict reports `bloomHit=27.93
  bloomRise=0.0855 grainSpread=0.00040`. The doc is out of date, not the build.
- **The asset ingestion path.** `AssetLibrary` already resolves textures,
  materials and props from `StreamingAssets/CityPack` with a procedural
  fallback, so a real pack drops in with **no code change**. The hook was built
  months ago and nothing has ever been put in it.

---

## The one that was already known and got lost

`production-plan-audio-art.md` §4, item 5 of the concrete first pass:

> **Modular period building/prop packs consistent with the palette. NOT DONE,
> and on hold** — the character direction moved toward semi-realistic (Mixamo)
> on 2026-07-28, and stylised low-poly buildings would clash with that.

That hold was correct when it was written, and **its blocker cleared on
2026-07-30** when the Mixamo bodies landed. Nothing picked it up, because the
item lived in a SPEC document and the roadmap — the file that is supposed to be
the tiebreak about what happens next — never carried it at all.

A blocked item in a spec with no corresponding roadmap row is an item that
unblocks silently and then waits forever.

---

## What this does not change

The strategy survives the audit intact, and it is worth saying so rather than
over-correcting. *Unmistakably deeper than KCD2 while looking unmistakably
worse* is still the trade, and the target for the visual work is **coherent and
readable**, not photoreal. One palette and one material response across seven
districts beats scattered high-resolution assets — which is the same argument
§4 made when it chose stylised noir, and the reason none of this needs a budget.

**Nothing in the fix requires a purchase.** CC0 PBR sources cover every surface
name `AssetLibrary` already asks for; CC0 prop and vehicle models exist; open
fonts with the right period character are free.

---

## The method change, so this does not recur

The roadmap now carries a **ship checklist** — the nine categories above plus
the ones that were already covered — and a milestone is not allowed to claim a
category it has not named. The check is cheap and it is the one that would have
caught all nine: *for each thing a finished game contains, which milestone owns
it, and what does done look like?*

Any category with no owning milestone is a gap, whether or not anybody is
currently thinking about it.
