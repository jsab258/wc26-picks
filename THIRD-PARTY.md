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
| **Where in the repo** | `game-design/picked-clips/` (the references), `voice-candidates/` (the listening pass), `ledger/Assets/Resources/voice/barks/` (335 clips synthesised from them, 5 Aug) |
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

**And on 5 August that stopped being hypothetical.** 335 bark clips were
rendered from these nineteen references and committed to
`ledger/Assets/Resources/voice/barks/`. Every one is a derivative of a CC BY
4.0 work and carries the same obligation as its reference — the credit text
above covers them, unchanged, because it was written to.

The attribution check is what noticed. It refused the commit with *"no asset
files live outside a directory this file knows about"*, naming the new folder,
which is a guard catching a licensing obligation the same hour the assets
appeared rather than at ship time. The paragraph above had the reasoning right
in advance and the DIRECTORY LIST was what went stale — a doc can be correct
about the principle and wrong about the facts, and only one of those is caught
by reading it.

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

## Fonts — PT SANS SHIPS, UNDER THE SIL OPEN FONT LICENCE 1.1

| | |
|---|---|
| **File** | `ledger/Assets/Resources/LedgerSans.ttf` |
| **Family** | PT Sans, installed under the project name `LedgerSans` |
| **Author** | ParaType Ltd. — Copyright (c) 2010, reserved names "PT Sans", "ParaType" |
| **Licence** | SIL Open Font License, Version 1.1 |
| **Licence file** | `ledger/Assets/Resources/LedgerSans.LICENCE.txt`, beside the font |
| **Obligation** | The OFL requires the licence to travel with the font. It does, in the same directory, and `tools/citypack/fetch_font.py` writes it there rather than leaving it to a document somebody updates by hand. |

**THIS SECTION SAID "NOTHING SHIPS, AND THAT IS A BUG" UNTIL 5 AUGUST, AND A
FONT HAD BEEN SHIPPING SINCE 31 JULY.** `tools/attribution-check.py` was
written for exactly this — it fails when an asset lives outside a directory
this file accounts for — and it caught it the first time anything ran it,
because nothing ever had: it was not wired into `verify.py`. Its own opening
paragraph says the original breach "survived because nothing in the plan owned
it and nothing in CI looked for it", and that stayed true of the check itself
for five days. It runs in `verify.py` now.

The obligation was never actually breached: the licence file travelled with the
font from the day it landed, because the fetcher writes it. What was wrong was
the RECORD — and for a licence, the record is the part that has to be right.

### What the game used before

`UiTheme.LoadFont` fell back to `Font.CreateDynamicFontFromOSFont(["Segoe UI",
"Arial"])`, borrowing whatever the machine had. That path remains as the
fallback when the shipped face is missing.

- **Segoe UI is licensed by Microsoft and is not redistributable.** The game
  does not redistribute it — it asks the OS — which is legal and is also why the
  typography differs per machine.
- On macOS and Linux this falls through to Arial or Unity's `LegacyRuntime.ttf`.

M17.9 / M22.4 replaces this with a face whose licence permits shipping inside a
product, and `tools/citypack/fetch_font.py` **writes the licence file next to
the font** — the OFL requires the licence to travel with the font, and a copy
beside the file is the only version of that which cannot drift from a document
somebody forgot to update.

One face, not a family: `UiTheme` uses a single family with weights done through
rich text, so eight weights would be megabytes for nothing. A **static** face
rather than a variable one, because Unity's dynamic font path does not read
variable axes — a variable font would install cleanly and render one arbitrary
weight, which looks like success and is not.

**And that constraint decided it.** The inventory pass listed what each
candidate family actually publishes in `google/fonts`, and the shortlist did not
survive contact with the evidence:

| Family | Licence dir | Static faces | Variable | Usable |
|---|---|---|---|---|
| Inter | `ofl/` | **0** | 2 | no — variable only |
| Source Sans 3 | `ofl/` | **0** | 2 | no — variable only |
| Roboto Condensed | `apache/` | — | — | no — `apache/robotocondensed` 404s |
| Libre Franklin | `ofl/` | **0** | 2 | no — variable only |
| **PT Sans** | `ofl/` | **4** | 0 | **yes — `PT_Sans-Web-Regular.ttf`** |

So the face this ships is **PT Sans**, under the SIL Open Font Licence 1.1, and
it is the only one of the five that can be shipped at all. It was listed last as
"a dependable fallback" and the fallback is what exists. The record is kept here
because the earlier version of this section named three families that cannot be
used, which is worse than naming none.

Recorded in `tools/citypack/font-candidates.json` (what each family publishes)
and `tools/citypack/font-installed.json` (what was actually taken).

Until it lands, `UiTheme.UsingShippedFont` is false and the sim verdict prints
it every run. Reported rather than gated — gating on a fetch that has not
happened paints the build red for known reasons, and a check that is red for a
known reason is a check people learn to skip. What it must never do is go
quiet, which is exactly how the project ended up not knowing it had no font.

## Textures, props, vehicles — NOTHING YET

No image files exist in the project; every surface is generated at runtime by
`ProceduralTexture.Generate`. When M17.6–17.8 land, each pack gets a row here
with its source, licence and a link, **before** it is committed.

`AssetLibrary` reads packs from `StreamingAssets/CityPack`, so the attribution
requirement attaches to that directory.

## What this project made itself

| | |
|---|---|
| **App icon** | `ledger/Assets/Resources/AppIcon/` — eight sizes, generated by `tools/make-icon.py` from the game's own palette rather than drawn, so it cannot drift from the noir pass the way a hand-made PNG would |
| **Every texture in the build today** | generated at runtime by `ProceduralTexture.Generate` until M17.6 lands a real pack |
| **All geometry** | procedural; the city, vehicles, props and held weapons are built in code |
| **Music** | procedural layer, M13 |
| **All writing** | the 2,604-line bark bank, every authored beat, every character |

`tools/attribution-check.py` knows this list, so our own files are recorded as
ours rather than reported as unaccounted for. A check that cannot tell
"third-party, needs a licence row" from "ours, needs nothing" either nags about
our own work or goes quiet about somebody else's.

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
