# Third-party assets and their licences

**This file is an obligation, not a courtesy.** The voice corpus this game is
cast from is CC BY 4.0, and CC BY requires attribution — shipping without it is
a licence breach, not an oversight. It was missing entirely until the
completeness audit on 2026-07-31 found that no `LICENSE`, no credits screen and
no attribution file existed anywhere in the project.

`tools/attribution-check.py` verifies that every directory of third-party
content in the repo has an entry here, so a new asset drop cannot land without
one. **If you add assets, add a row. The build fails otherwise.**

---

## Voices — CC BY 4.0, attribution REQUIRED

| | |
|---|---|
| **What** | Reference recordings for all 19 cast voices |
| **Source** | **CVSTR VCTK Corpus** (Centre for Speech Technology Research, University of Edinburgh) |
| **Licence** | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| **Where in the repo** | `game-design/picked-clips/`, `voice-candidates/` |
| **Speakers used** | p227 p228 p231 p238 p241 p244 p245 p249 p256 p263 p265 p266 p272 p273 p276 p282 p287 p288 p292 |

**Required attribution text, to appear in the shipped credits:**

> Voice reference recordings derived from the CSTR VCTK Corpus (Centre for
> Speech Technology Research, University of Edinburgh), used under CC BY 4.0.

**Why this corpus and no other.** The project's standing rule is that voices may
only come from corpora whose contributors donated their voices to build speech
technology, and **no identifiable public figures, ever.** VCTK contributors
recorded specifically for speech research. That rule is not negotiable and it is
the reason no commercial voice library was considered.

**What changes if the voices are synthesised.** M17.2 clones these references
with chatterbox. A derived voice is still a derivative of a CC BY work, so this
attribution stays regardless — synthesis does not launder the obligation.

## Character models and animation — Adobe Mixamo

| | |
|---|---|
| **What** | 41 animation clips and two base bodies (X Bot, Y Bot) |
| **Source** | Adobe Mixamo |
| **Licence** | Mixamo's own terms — royalty-free use in a product, no redistribution of the assets as assets |
| **Where in the repo** | `ledger/Assets/Characters/` |

**The constraint that matters:** Mixamo content may ship inside a game, and may
not be redistributed as a standalone asset library. Nothing here does the
latter; the FBX files are tracked because they are project inputs.

## Engine — Unity

| | |
|---|---|
| **What** | Unity 6000.0.58f1, built-in render pipeline |
| **Licence** | Unity Personal |
| **Obligation** | Unity Personal requires the "Made with Unity" splash. It is not currently in the build — M22.3 |

## Fonts — NOTHING SHIPS, AND THAT IS A BUG

`UiTheme.LoadFont` calls `Font.CreateDynamicFontFromOSFont(["Segoe UI",
"Arial"])`, so the game borrows whatever the machine has.

- **Segoe UI is licensed by Microsoft and is not redistributable.** The game
  does not redistribute it — it asks the OS — which is legal and is also why the
  typography differs per machine.
- On macOS and Linux this falls through to Arial or Unity's `LegacyRuntime.ttf`.

M17.9 / M22.4 replaces this with a font that ships under a licence permitting
it. Until then the credits cannot name a typeface, because there isn't one.

## Textures, props, vehicles — NOTHING YET

No image files exist in the project; every surface is generated at runtime by
`ProceduralTexture.Generate`. When M17.6–17.8 land, each pack gets a row here
with its source, licence and a link, **before** it is committed.

`AssetLibrary` reads packs from `StreamingAssets/CityPack`, so the attribution
requirement attaches to that directory.

---

## The rule for anything added later

1. Only sources whose licence permits use in a commercial game.
2. **The licence text goes in this file before the asset goes in the repo.**
3. Attribution-required licences (CC BY, and most CC0 packs *request* it even
   though they do not require it) get their exact required wording recorded
   above, not paraphrased.
4. No identifiable public figure's voice, likeness or name, ever.
5. `tools/attribution-check.py` runs in CI and fails on an asset directory with
   no entry here.
