# Content sourcing — what we can fetch, and what we must generate

> **STATUS — SPEC, 2026-08-25.** Research pass for M17.10 (the GTA V bar on a
> British port town, late-analog 80s/90s). It is the COMPANION to
> `visual-bar-sources.md`, not a replacement: that file is the verified fetch
> table for the packs we already decided on, this one answers the two questions
> it did not — **what free content are we still missing, and how do we make what
> nobody publishes.** Where the two disagree, this file is newer; where this
> file says GENERATE and that one says GAP, they agree.

---

## 0. How to read this, and what was actually checked

Same discipline as `visual-bar-sources.md`, because the container is still
network-restricted and a row that reads as fetched when it was only searched is
the exact failure that file's legend exists to prevent.

- **[VERIFIED-HERE]** — an HTTP status or bytes obtained from this container
  during this pass, or a fact read out of this repository's own files.
- **[MEASURED]** — a number taken from the files on disk (Pillow/`git ls-files`).
- **[SEARCH]** — licence/terms confirmed from the search result text of the
  cited page. The page itself was NOT fetched (proxy-blocked); the claim is as
  good as the citation and no better.
- **[INFERRED]** — reasoning from proven patterns. Nothing confirmed. Any
  fetch built on one of these must print what it got before it is believed.

**Egress probe run for this pass [VERIFIED-HERE], 2026-08-25:**

| host | result |
|---|---|
| `raw.githubusercontent.com` | **200** (590 bytes read) |
| `upload.wikimedia.org` | 000 — blocked |
| `commons.wikimedia.org/w/api.php` | 000 — blocked |
| `assets.publishing.service.gov.uk` | 000 — blocked |
| `ambientcg.com/api/v2` | 000 — blocked |
| `texture.ninja` | 000 — blocked |
| `api.polyhaven.com` | blocked at the WebFetch layer too |

So: **`raw.githubusercontent.com` is the only host this container can fetch
from, and everything else is a CI job.** That is unchanged from 21 Aug and it
is why every fetch below names the job that proves it, not the URL that
promises it.

---

## 1. Six findings that change the plan

Ranked by visible-impact-per-unit-of-work. The first two need no download at
all, which is why they are first.

### 1.1 The signs already carry their words and render as blank panels

`WorldBuilder.BuildNeon` iterates `NeonSigns` as `(placeId, colour, word)` and
builds **a coloured emissive cube** [VERIFIED-HERE, read the function]. The
`word` is in the data. Nothing draws it. `Dressing.HasFascia(Premises)` decides
which building kinds carry a signboard band over the ground floor — the mount
point exists, and what sits on it is a tinted plate.

GTA's streets are **lettered**: every frame in `game-design/reference/` has
shopfront type, a hand-painted fascia, a plastic box sign, a pub name. Ours
have coloured rectangles. This is not a fetch problem — no CC0 pack will ever
contain "MERIDIAN FISH BAR" — it is a **generation** problem, and it is the
single highest impact-per-hour item found in this pass. §3.1.

### 1.2 We fetch everything at 2K when 4K and 8K are free

- `tools/props/fetch_visual.py` line 277 builds `ambientcg.com/get?file={aid}_2K-{fmt}.zip` — hard-coded 2K, no override [VERIFIED-HERE].
- `tools/citypack/choices.json` says `"resolution": "2K-JPG"` [VERIFIED-HERE].
- Shipped surfaces measure 2048² and decals 2048² (64 of them), 512² (16), 2048×1024 (12) [MEASURED].
- ambientCG publishes **up to 8K, CC0, free, no account** ([SEARCH](https://docs.ambientcg.com/api/v2/full_json/), [ambientcg.com](https://ambientcg.com/)).
- Poly Haven HDRIs are fetched from the `/hdr/2k/` path; 4k/8k exist on the same host [VERIFIED-HERE for the 2k path in code; [INFERRED] for the others].

This is the 1K-when-2K-was-one-field-away incident from CLAUDE.md, one rung up
and still open. **The recommendation is not "4K everything"** — it is 4K for the
surfaces the player stands on and walks past at 1.5m (asphalt, pavement, the
brick at arm's length; frames 3 and 5 are eye-level shots and that is where
smearing shows), 2K for everything above the first storey. That is a
measurement to take, not a preference: bump one surface, read the still.

### 1.3 `.glb` is invisible to the attribution sweep FIXED 1 SEP, and the finding was bigger than one suffix

The original finding, kept because the correction below is only readable
against it: `ASSET_SUFFIXES` in `tools/attribution-check.py` lists `.fbx .png
.jpg .jpeg .tga .psd .wav .mp3 .ogg .ttf .otf .bundle .obj .blend .hdr .exr
.webp` and **not `.glb`, not `.gltf`, not `.mtl`** [VERIFIED-HERE]. The check
passed only because the affected directories also held attributed files, so
`Props` reported "197 asset file(s) attributed" while 49 files in the same
tree were not counted at all, and the final sweep, "no asset files live
outside a directory this file knows about", could not see a stray `.glb`
anywhere in the repository. Third instance of the same fault (`.hdr`/`.exr` on
24 Aug, `.webp` the same day).

**ONE MEASUREMENT IN THAT PARAGRAPH WAS WRONG AND IS CORRECTED HERE.** It said
the 37 `.glb` sit under `ledger/Assets/Props/base-mesh` **and**
`Props/oga-vehicles/lowpoly-public-transport`. Measured 1 Sep: all 37 are in
`base-mesh`, and `lowpoly-public-transport` holds no `.glb` at all. What it
holds is 12 `.obj` with 12 `.mtl` and 12 `.fbx`, which is a different pack in
a different format, and the count happened to come out right anyway.

**WHAT LANDED, AND IT IS NOT THE SUFFIX LIST.** Queue item 016 fixed the list
(`.glb .gltf .mtl .bin .npz .flac` added) but the list was the symptom. The
tool now declares a second set, `NOT_ASSET_SUFFIXES`, and the union of the two
must cover every file walked; anything in neither is UNCLASSIFIED, printed by
name with its denominator, and fails. Removing `.glb` again reproduces the
original bug and the tool now says so twice on the live tree, once as
`base-mesh: no asset file among 38 walked` and once as `37 unclassified of
3830 walked`. So the recommendation this section used to end with, pad the
list with `.dae .usdz .svg .tif .tiff` against future fetches, is DECLINED on
purpose: a list padded with formats nobody has fetched is a bound chosen first
and defended afterwards, and the residue check means the day one lands it
names itself on the first run. `.flac` is the one exception and it has
evidence rather than a guess behind it: `tools/voice-live/speak.py` and
`tools/voice-cast-check.py` already scan for it.

**AND THE SWEEP FOUND TWO THINGS THE ORIGINAL PASS DID NOT LOOK FOR.**
`game-design/voice-conds` (23 `.bin` + 23 `.npz`, VCTK-derived conditioning)
was on no watched row and had no visible suffix, so it was invisible twice
over. And `ledger/Assets/Props/oga-vehicles` (59 files from OpenGameArt) sits
inside the `Props` row, so its files were being counted under the **Kenney**
token and reported as attributed. Both now carry their own rows, and
THIRD-PARTY.md carries an OpenGameArt section it did not have.

### 1.4 Poly Haven is used for skies only

`fetch_visual.py` pulls four HDRIs and nothing else from Poly Haven
[VERIFIED-HERE]. Poly Haven also publishes **CC0 textures and CC0 models** on
the same CDN with the same no-account fetch — including scanned street props.
`visual-bar-sources.md` lists the model pattern as "URL-IN-USE" but nothing
calls it. Free photoreal detail we have already licensed ourselves out of
nothing to take.

### 1.5 Official British road signage exists as open artwork

The DfT publishes **600+ traffic sign images from *Know Your Traffic Signs*, as
JPG and EPS, under the Open Government Licence** — free reuse in any medium,
attribution to the OGL, one stated restriction that matters to us (reproduce
signs accurately and not in a misleading context)
([SEARCH](https://www.gov.uk/guidance/traffic-sign-images)). Wikimedia Commons
additionally hosts UK traffic sign SVGs tagged OGL
([SEARCH](https://commons.wikimedia.org/wiki/File:UK_traffic_sign_616.svg)).

EPS/SVG is the good news: it is **vector**, so it rasterises to any resolution
we want, in CI, with no upscaling and no photograph. Nothing else in this
project's British-ness list is available in a form that clean. §2.1.

### 1.6 The AI-image question has a defensible answer, and it is not "avoid it"

The voice rule — *only corpora whose contributors donated their voices, no
identifiable public figures ever* — has an exact image analogue, and applying
it gives a ladder rather than a ban. §4.

---

## 2. PART 1 — what exists, free, that we are not using

### 2.1 New sources worth wiring, ranked

Everything in this table is **free and requires no purchase**. The account
column is the one to read first.

| # | source | what it gives Meridian | licence | account | CI-fetchable | verification |
|---|---|---|---|---|---|---|
| 1 | **GOV.UK traffic sign images** — `gov.uk/guidance/traffic-sign-images` | 600+ official UK signs, JPG **and EPS vector**: give way, no waiting, weight limits, dock/quay warnings, direction plates | **OGL** (v2 stated on the page) — attribution, reproduce accurately | **no** | yes — zips on `assets.publishing.service.gov.uk` | [SEARCH] |
| 2 | **Wikimedia Commons UK sign SVGs** | the same signs as SVG, plus period variants | OGL / CC-BY-compatible, per file | **no** | yes — `commons.wikimedia.org/w/api.php` + `upload.wikimedia.org` | [SEARCH] |
| 3 | **Google Fonts raw** — `raw.githubusercontent.com/google/fonts/main/<licdir>/<family>/<file>.ttf` | the letterforms for every sign, poster, notice and number plate | OFL 1.1 / Apache — licence file must travel with the font | **no** | **yes, and from this container** | **[VERIFIED-HERE]** — 11 of 14 probed faces returned 200 (see §3.1) |
| 4 | **Poly Haven textures + models** (`dl.polyhaven.org`) | CC0 scanned surfaces and props at 2k–8k; we take only 4 HDRIs today | CC0 | **no** | yes — same host and pattern already in use | [VERIFIED-HERE for the HDRI path in our code; pattern for textures/models [INFERRED] — resolve via `api.polyhaven.com/files/<slug>` in the job |
| 5 | **ambientCG at 4K/8K** and its unfetched categories | the resolution rung of §1.2, plus categories we never swept: corrugated steel, paving, kerbs, roof tiles, rust, wet asphalt | CC0 | **no** | **yes — one field in a file we already run** | [VERIFIED-HERE for our 2K pin; 8K availability [SEARCH] |
| 6 | **Texture Ninja** (`texture.ninja`) | **5,100+ CC0 high-resolution photographs** of surfaces and objects — the input side of the photo→PBR pipeline in §3.3, and the source for poster paper, rust, peeling paint | CC0 | **no** | yes | [SEARCH] |
| 7 | **3dtextures.me** | CC0 PBR sets, strong on brick/plaster/damp | CC0 | **no** | yes | [SEARCH] |
| 8 | **TextureCan** | CC0 PBR ≥4K + some CC0 models | CC0 | **no** | yes | [SEARCH] |
| 9 | **cgbookcase** | 566 CC0 tileable PBR sets (2K free; 4K is a Patreon tier — **take the 2K, never pay**) | CC0 | **no** | yes | [SEARCH] |
| 10 | **ShareTextures** | CC0 4K sets, architect-made, European stock | CC0 (some patron-only files — skip those) | **no** | yes | [SEARCH] |
| 11 | **OpenGameArt industrial/harbour** — "High quality industrial asset pack", "3TD Harbour Pack" in *CC0 ASSETS 3D LOW POLY* | tanks, towers, chimneys, pipes, containers — the dockside backbone we listed as a gap | CC0 (per page — read each) | **no** | yes — the existing OGA scrape in `fetch_visual.py` already does this shape | [SEARCH] |
| 12 | **Smithsonian Open Access 3D** | CC0 scanned objects; period-generic props only, weak for British street furniture | CC0 | api key is free/optional | yes | [INFERRED] |
| 13 | **poly.pizza** | the likeliest home of a phone box / pillar box / bus shelter | **per item: CC0 or CC-BY 3.0 — read the page** | **no** for web download; **yes** for the API key | yes (scrape) | [SEARCH] |
| 14 | **Sketchfab** — incl. a "Generic 80s European car" (Escort/Golf-shaped) | the one genuinely period-correct vehicle shape found anywhere | per model; CC0 exists | **YES — download requires a logged-in account or an OAuth/API token** | only with Jafar's token | [SEARCH] |
| 15 | **BlenderKit free tier** | 48k–100k assets, CC0 and royalty-free, incl. materials | CC0 / RF, commercial ok | **YES — free account, API key** | with a key [INFERRED] | [SEARCH] |
| 16 | **Thingiverse / Printables** | genuinely accurate **K6 phone box**, pillar box, bollards — measured from the originals by British modellers | **per item, and NC IS COMMON** — CC-BY-NC-SA is unusable for us | Thingiverse: probably not; **Printables: yes** | conditionally | [SEARCH] |
| 17 | **Fab / Quixel Megascans free tier** | photoscanned surfaces at a quality above everything else here | Fab Standard Licence; non-Unreal use and what is still free after the 2024–25 migration is **not clear** | **YES — Epic account** | no — human step | [SEARCH] |
| 18 | **Unity Asset Store free section** | Unity-native packs, some European | Asset Store EULA: use in a game yes, redistribute as assets no | **YES — Unity account (we have one for the build)** | no — human step | [INFERRED] |

### 2.2 Reference-only sources — right for measurement, wrong for shipped pixels

These are photograph archives. They are worth a great deal as *reference* (what
does a Tyneside terrace's brick coursing actually look like, how wide is a
British pavement, what colour is a 1988 shop awning) and they are a licence
trap as *content*.

| source | what | licence | why reference-only |
|---|---|---|---|
| **Geograph Britain and Ireland** | **6.2M geolocated British photographs**, incl. docks, terraces, signage | **CC BY-SA 2.0**; API key free ([SEARCH](https://www.geograph.org.uk/help/api)) | SA: an adapted image must itself be CC BY-SA. Shippable, but it encumbers that texture and every derivative of it — see §4.5 |
| **Mapillary** | street-level imagery, UK covered, faces/plates blurred | **CC BY-SA 4.0**, free API with a Meta account ([SEARCH](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data)) | same SA logic, plus an attribution-display requirement |
| **Flickr Commons** (Tyne & Wear Archives & Museums; National Archives UK; British Library) | British industrial, shipyard and dock photography, some to 1980 | **"No known copyright restrictions" is NOT a licence** — it is a statement of the institution's knowledge ([SEARCH](https://www.flickr.org/programs/flickr-commons/no-known-copyright-restrictions-how-it-works/)) | fine to look at; a claim we cannot stand behind if we ship pixels from it |
| **OS OpenData / EA LIDAR** (OGL) | real British street layouts and building heights | OGL | not pixels at all — a plausible input to `CityPlan` if we ever want real block geometry. Parked, not rejected |

**The line, stated once so it is not re-derived:** a photograph we may look at
is not a photograph we may bake. Reference informs a *measurement* (a ratio, a
colour, a height) or a *description* that we then author from scratch. Pixels
that ship come from CC0, from OGL, or from us.

### 2.3 Excluded, with reasons

- **3D Scan Store free samples** — free samples are **non-commercial only**, and they require a newsletter signup ([SEARCH](https://www.3dscanstore.com/terms-and-conditions-licensing)). Hard no; do not revisit.
- **Scan the World / most MyMiniFactory heritage scans** — predominantly CC BY-NC. Hard no.
- **Textures.com free tier** — account, credit limits, and a licence that restricts redistribution of the images themselves. Not worth the terms when six CC0 libraries exist.
- **CGTrader / TurboSquid / Free3D "free" sections** — account walls and per-item licences that are frequently "personal use". No.
- **itch.io $0 flows** — CSRF + signed URLs, no plain curl. Already excluded on 21 Aug; still true.
- **Real 1980s–90s British posters, adverts, shop signage, packaging** — see §4.4. These are in copyright for decades yet. Never.

---

## 3. PART 2 — generating what does not exist

This is the half that matters. Ranked by impact-per-work, and deliberately in
the order that puts the zero-risk deterministic methods first.

### 3.1 Tier A — deterministic composition. Posters, fascias, notices, plates.

**The single best lever in this document.** No model, no network, no account,
no licence question, and it runs in this container today: **Pillow 12.3.0 and
numpy 2.4.6 are installed** [VERIFIED-HERE].

The inputs are all things we already have the right to:

- **Letterforms** — OFL faces from `google/fonts` via raw.githubusercontent, which is the one host that works from here. Probed this pass [VERIFIED-HERE, HTTP 200]: `ofl/leaguegothic`, `ofl/oswald`, `ofl/anton`, `ofl/bebasneue`, `ofl/archivoblack`, `ofl/alfaslabone`, `ofl/abrilfatface`, `ofl/playfairdisplay`, `ofl/rye`, `ofl/courierprime`, `ofl/hammersmithone`. (404 at the paths guessed for Special Elite and Ultra — filename/dir differs; resolve from the directory listing the way `fetch_font.py` already does rather than guessing again.) That set covers the period range a British high street needs: a condensed grotesque for a fascia, a fat slab for a chip shop, a didone for a pub, a typewriter face for a notice in a window.
- **Paper, ink, wear** — CC0 grunge from ambientCG's imperfection/scratch sets (already fetched) and Texture Ninja photographs.
- **Words** — ours. The bark bank is 2,604 lines of this game's own English; the shops, pubs and firms are named in `HookMap`/`Dressing`/the empire roster.

What it produces, in rough order of what a player sees:

1. **Shop fascias** for every `HasFascia` premises — name, trade line, a period-plausible layout, painted-on-board or plastic-box treatment, weathered.
2. **Neon/box signs with actual letters** for `NeonSigns`, which already carry the word (§1.1).
3. **Posters and flyposting** — gig bills, ferry timetables, missing-cat notices, union meetings, planning notices. GTA frame 1's wall is four layers deep and one of them is torn poster residue.
4. **Official notices** — dock regulations, NO TIPPING, parking restrictions, warehouse door numbering; and **number plates** (British format, period-correct, yellow rear/white front), which are a per-vehicle detail the reference frames all have.
5. **Pub and street name plates**, which in Britain are cast or painted, not printed.

**Wiring:** `tools/decals/make_signage.py` writes PNGs into
`StreamingAssets/Decals/generated/` plus a manifest; the same job writes the
`THIRD-PARTY.md` row saying *ours, generated from OFL faces*, with the OFL
licence files travelling beside the fonts exactly as `fetch_font.py` already
does. **Runtime proof:** a `signsLettered=` count on the done line beside a
ground-truth list of which premises got which sign, or it is a pipeline that
can ingest signage rather than signage (rule 6).

**Effort:** small. **Impact:** the largest single visual delta available
without a fetch. **Risk:** none.

### 3.2 Tier B — procedural in code. Grime, damp, rust, salt, repetition.

What can be computed rather than fetched, and it is more than we are computing:

- **Weathering masks from noise** — FBM for smoke and soot gradients, Worley/cellular for salt bloom and spalled render, ridged noise for tar snakes and crack networks, directional streak noise for rain-shadow staining under sills and downpipes. A port town's specific signature is **salt**: white bloom low on the wall, rust bleeding from every fixing, moss in the north-facing joints. None of that is a download.
- **Placement-driven dirt rather than baked dirt** — the same mask reads differently if it is driven by geometry: darker at the wall/ground junction, heavier under a projecting sill, streaked below a gutter. Cheap, and it is what makes GTA frame 3 read as real with no interesting light in it.
- **Killing the tiling repeat.** This is the highest-value shader item found: **hex-tiling / histogram-preserving blending** (Heitz & Neyret 2018; Mikkelsen's practical real-time adaptation, JCGT 2022) turns one CC0 asphalt tile into a non-repeating ground plane. Reference implementations exist publicly ([mmikk/hextile-demo](https://github.com/mmikk/hextile-demo), [JCGT paper](https://jcgt.org/published/0011/03/05/paper-lowres.pdf), [Heitz's page](https://eheitzresearch.wordpress.com/722-2/)) — **check the licence of any code before copying it and prefer implementing from the paper**, which carries no licence question at all. Frame 3's road is five asphalt tones and no visible repeat; ours is one tile stamped in a grid.
- **The offline half of the same idea** — the Unity Grenoble tool "make your texture tileable with histogram-preserving blending" ([demo](https://unity-grenoble.github.io/website/demo/2020/10/16/demo-histogram-preserving-blend-make-tileable.html)) is what turns an arbitrary CC0 *photograph* into a tileable material, which is what §3.3 needs.

**Effort:** medium (shader work, and the Game layer costs a 28-minute round
trip). **Impact:** high and everywhere. **Risk:** none.

### 3.3 Tier C — photo → PBR

Turning a CC0 photograph into a full material set. Two known tools, and the
recommendation is to take neither wholesale:

| tool | licence | verdict |
|---|---|---|
| **Materialize** (Bounding Box Software) | **GPL-3**, source is a Unity project ([SEARCH](https://github.com/BoundingBoxSoftware/Materialize)) | Does exactly the job — height/normal/AO/edge from a diffuse photo, plus seamless tiling. But it is a **GUI Unity application**, so it is a human step, not a CI step; and its **shader packs are GPL and must never enter our Unity project.** Its *outputs* are unencumbered. |
| **DeepBump** | **GPL**, U-Net/MobileNetV2, has a **command-line mode** ([SEARCH](https://github.com/HugoTini/DeepBump)) | The CI-shaped one: normal → height → curvature from a single image, headless. GPL applies to the tool we run, not to the PNGs it emits. Runs on CPU. |

**The honest engineering call:** the arithmetic here (Sobel → normal, Poisson
solve → height, occlusion sweep → AO, offset-and-heal → seamless) is textbook
and a hundred lines of numpy. Reimplementing it in `tools/textures/` keeps CI
self-contained, keeps GPL code out of the repo, and puts the maths where the
tests run — which is the standing instrument rule. Use DeepBump's CLI where the
learned normal genuinely beats the derivative one, and measure the difference
before deciding rather than assuming.

**Effort:** medium. **Impact:** high — it is what unlocks Texture Ninja's 5,100
CC0 photographs as materials instead of as wallpaper. **Risk:** none, if the
GPL tools stay outside the game project.

### 3.4 Tier D — diffusion models

Ranked by provenance first, because that is this project's rule, and capability
second. See §4.1 for why the order is this way.

| model | training data | model licence | our position |
|---|---|---|---|
| **Mitsua Diffusion One / CC0** | museum Open Access + public domain + opt-in only; explicitly no scraped copyright images ([SEARCH](https://huggingface.co/Mitsua/mitsua-diffusion-one)) | Mitsua Open RAIL-M | **The exact image analogue of the VCTK rule.** Weakest output quality of the four. First choice on principle. |
| **CommonCanvas-XL-C** | CommonCatalog-C — ~25M **Creative-Commons, commercially-licensed** Flickr images; no-derivatives images excluded ([SEARCH](https://huggingface.co/common-canvas/CommonCanvas-XL-C), [paper](https://ar5iv.labs.arxiv.org/html/2310.16825)) | model weights CC BY-SA 4.0 (the `-NC` variants are **unusable**, note the suffix) | **Best defensible quality.** Take the `-C` variant only, and record that the `-NC` twin exists so nobody grabs the wrong one. |
| **Public Diffusion** (Spawning) | public domain / CC0 only ([SEARCH](https://spawning.substack.com/p/a-fireside-chat-with-the-creators)) | **release status and licence unconfirmed** | Watch item. Verify before use. |
| **FLUX.1 [schnell]** | undisclosed web-scale | **Apache 2.0**, commercial use explicit, outputs unrestricted ([SEARCH](https://huggingface.co/black-forest-labs/FLUX.1-schnell)) | Legally the cleanest *licence* and the strongest *output*, with the provenance objection we rejected for voices. §4.1 rung 3. **`FLUX.1 [dev]` is non-commercial — never.** |

**Hardware reality, and it is the binding constraint [VERIFIED-HERE]:**
`game-design/live-speech-latency.md` records that **the dev machine has an AMD
GPU** ("CUDA is not a lever for this machine"). That kills **Dream Textures**
outright — it requires Nvidia or Apple Silicon ([SEARCH](https://github.com/carson-katri/dream-textures)) — and it means the practical
routes are (a) CPU inference in CI, where FLUX schnell's 4 steps are minutes
per image and GitHub's 6-hour job cap forces chunking, or (b) a batch on
Jafar's Windows machine, which is **the shape the voice pipeline already uses**
(`tools/voice-live/*.bat`, run by him, outputs committed). Precedent exists;
re-use it rather than inventing a third pattern.

**Where diffusion is actually worth it, if used at all:** *not* fascias and
notices (Tier A does those better, more legibly and with no risk), *not*
tileable materials (Tier C from real CC0 photographs beats a hallucinated
brick). It is worth it for **painterly one-offs**: a faded ghost-sign mural, a
pub's hand-painted swinging sign, an illustrated advert — things that would
otherwise need an illustrator. Small count, high per-item value, every one
human-reviewed.

### 3.5 Image-to-3D for the props nobody publishes

`visual-bar-sources.md` concluded that the K6 phone box, pillar box, bus
shelter, telegraph pole, TV aerial, dock crane and parking meter are **not
CC0-fetchable anywhere**, and that we should author them procedurally. That
conclusion stands — a K6 is a box, a dome, a crown and a grid of panes, which
is well inside `Core`'s existing competence, and procedural geometry gets
`SurfaceSpec` tinting for free.

What is new since that pass is a second route for the ones procedural geometry
does badly (a crane's lattice, a Victorian bracket lamp): **single-image-to-3D
under MIT licences** — **TripoSR** (Stability/Tripo, MIT, sub-second on a
consumer GPU) and **Microsoft TRELLIS** (MIT, image or text → mesh)
([SEARCH](https://github.com/microsoft/TRELLIS), [TripoSR](https://tasarim.ai/en/models/triposr)). **Hunyuan3D-2 carries regional usage
restrictions — do not use it** ([SEARCH], same comparison).

The catch is the input image: feeding it a copyrighted photograph makes the
mesh a derivative of that photograph. Feed it **our own Tier-A/Tier-D
rendering** of the object, or a CC0 photograph, and the provenance chain stays
clean. Rank this below procedural authoring, and treat it as the fallback for
two or three hero props rather than a pipeline.

### 3.6 Photogrammetry from open photo archives — no, as a pipeline

Asked directly, and the answer from the heritage literature is that
reconstruction from historical photographs is **real but expert, manual and
per-building**: it needs multi-view overlap or single-view perspective
restitution with geometric constraints and control points, and it is done as a
research exercise on individual monuments
([SEARCH](https://isprs-archives.copernicus.org/articles/XLII-2/259/2018/isprs-archives-XLII-2-259-2018.pdf), [SEARCH](https://link.springer.com/chapter/10.1007/978-3-031-85187-2_4)).
Archive photographs of British terraces are single-viewpoint, unknown-camera
and — for the 1980s — in copyright besides. **Reject it as a content pipeline.**

**What survives from it, and it is worth having:** the *single-image
rectification* half. Given one square-on CC0 photograph of a facade, a
homography (four corners → rectangle) produces a rectified, measurable facade
texture, and §3.2's tiling operator makes it repeatable. That is fifty lines of
numpy, not photogrammetry, and it is the realistic way to get British brick
coursing and window proportions that are *right* rather than *plausible*.

### 3.7 Upscaling — last, and only after taking the bigger variant

**Real-ESRGAN** is BSD-3-Clause with a Vulkan/ncnn build that needs no CUDA
([SEARCH](https://github.com/xinntao/Real-ESRGAN)), so it is usable and it runs
on an AMD machine. But upscaling a 2K CC0 texture when the 4K and 8K originals
are one URL field away (§1.2) is the exact mistake CLAUDE.md's standing order
names. **Order: take the bigger variant; then generate; then, only for content
that exists at one resolution and nowhere else, upscale.**

---

## 4. PART 3 — the licence and provenance position

### 4.1 The ladder, which is the voice rule applied to pixels

The voice rule is *only corpora whose contributors donated their voices to
build speech technology, and no identifiable public figures, ever.* Two clauses:
a **consent** clause about the training data, and an **absolute** clause about
who appears in the output. Both transfer.

| rung | method | provenance | ship? |
|---|---|---|---|
| **1** | **Deterministic composition** — our words, OFL letterforms, CC0 grunge, code (§3.1, §3.2) | every input licensed to us by its author for exactly this | **yes, unreservedly.** Default. |
| **2** | **CC0/OGL content, transformed by code** — photo→PBR, rectification, tiling (§3.3) | CC0 waives; OGL grants | **yes.** Record the source per file. |
| **3** | **Diffusion trained on consented/PD/CC data** — Mitsua, CommonCanvas-XL-C | the direct analogue of VCTK: contributors licensed the work for reuse | **yes**, with human review of every image. |
| **4** | **Diffusion trained on undisclosed web-scale data** — FLUX schnell (Apache 2.0) | the licence is clean; the *provenance* is the objection we accepted for voices | **only by an owner decision, recorded**. Not to be adopted silently by a builder. |
| **5** | **Anything from a scraped or laundered image dump**; NC-licensed assets; "no known copyright restrictions"; real brand or period ad artwork | unknowable, or knowably not ours | **never.** |

Rung 4 is the honest tension in this document. The licence position is
*better* than rung 3's in one respect (Apache 2.0 vs CC BY-SA weights), and the
ethical position is worse in exactly the way that made us refuse commercial
voice libraries. It is a decision, and by the studio split it belongs to the
director/owner, not to a builder or to this file.

### 4.2 What the law actually says, as of this pass

- **UK, and this is our jurisdiction of interest:** *Getty Images (US) Inc & ors v Stability AI Ltd* **[2025] EWHC 2863 (Ch), 4 November 2025** — Getty abandoned its primary copyright claims at trial; Stability won on secondary infringement; the court endorsed the view that **the model contains no copies of the training works**; only "extremely limited" trade mark findings against early Stable Diffusion versions ([SEARCH](https://www.twobirds.com/en/insights/2025/uk/stability-ai-defeats-getty-images-copyright-claims-in-first-of-its-kind-dispute-before-the-high-cour), [SEARCH](https://www.lw.com/en/insights/getty-images-v-stability-ai-english-high-court-rejects-secondary-copyright-claim)). **Read the trade mark half as the operative one for us**: the risk that materialised was *a mark showing up in an output*, not the training.
- **US copyrightability:** the Copyright Office's Part 2 report (29 January 2025) holds that **purely AI-generated output is not copyrightable**, and that **prompts alone — however detailed — do not confer authorship**; human modification, arrangement and expressive input can ([SEARCH](https://www.copyright.gov/ai/), via [Skadden](https://www.skadden.com/insights/publications/2025/02/copyright-office-publishes-report), [Jones Day](https://www.jonesday.com/en/insights/2025/02/copyrightability-of-ai-outputs-us-copyright-office-analyzes-human-authorship-requirement)).

**What that means concretely for LEDGER:** we can *ship* rung-3/4 images. We
may not be able to *stop anyone copying them* in the US. That argues for using
generation on **volume filler** (a hundred posters nobody will steal) and
authoring by hand or by deterministic code anything that is part of the game's
identity. It is a product argument, not only a legal one.

### 4.3 The absolute clauses — the image analogue of "no public figures"

Non-negotiable, and they should be added to `THIRD-PARTY.md`'s standing rules:

1. **No identifiable real person** in any generated or fetched image — no faces from a photograph, no likeness of a public figure, no name. Same clause as the voice rule, same seriousness. Diffusion models will produce celebrity-adjacent faces unprompted; a human looks at every image before it lands.
2. **No real trade marks, logos, brand names, packaging or livery.** This is *trade mark* law, which is separate from copyright and survives every training-data argument — and it is precisely where Getty's only wins landed. GTA itself does this: every brand in Los Santos is invented. **Meridian's brands are Meridian's**, which is better content anyway: an in-world chandler, an in-world brewery, an in-world ferry line tie into social memory the way a real logo never could.
3. **No copying of real signage from photographs**, even OGL/CC0 ones, where the sign carries a mark. The traffic signs of §1.5 are the exception by design — they are *public regulatory artwork* published for reuse — and even there the OGL asks that signs be reproduced accurately and not misleadingly.

### 4.4 Period British material is still in copyright — this is why we invent

A 1985 poster, advert, packet or shop sign is an artistic work whose UK
copyright runs for the author's life plus 70 years, and Crown copyright for 50
years from publication. **Nothing from the game's own period is anywhere near
public domain, and nothing will be for decades.** There is no archive, no
"vintage" pack and no clever licence reading that changes it — the packs that
sell "80s advert textures" are selling other people's work.

So the period look is reached by **authoring in the period's visual language** —
its letterforms, its printing limitations, its colour, its layout conventions —
with our own content in it. That is a Tier A job, and it is the same conclusion
`visual-bar-sources.md` reached for torn posters, reached again from the legal
side.

### 4.5 ShareAlike, stated precisely so it is not over- or under-read

CC's own guidance: **ShareAlike binds *adaptations*, not *collections*** — a
game that includes a BY-SA texture alongside other assets is a collection, and
the SA obligation attaches to the adapted material, not to the whole game
([SEARCH](https://wiki.creativecommons.org/wiki/ShareAlike_interpretation)).
But a texture *made from* a BY-SA photograph **is** an adaptation and must be
offered under BY-SA, and where that material is deeply integrated the practical
scope of what a third party may take gets uncomfortably fuzzy
([SEARCH](https://www.gamedeveloper.com/business/creative-commons-is-not-a-smart-source-for-video-game-assets)).

**Our position:** BY-SA sources (Geograph, Mapillary, CommonCanvas weights) are
allowed for **reference and for tooling**, and BY-SA *pixels* only by an
explicit decision recorded per file in `THIRD-PARTY.md` with the SA obligation
written out. CC0 and OGL have no such question, and we have enough of both.

### 4.6 What to add to `THIRD-PARTY.md` when any of this lands

- A **"generated by us"** section distinguishing *deterministically composed from licensed inputs* (rung 1–2: name the fonts and their OFL files, name the CC0 sets) from *model-generated* (rung 3–4: name the model, its licence, its training-data claim, and the date of the human review).
- The **OGL attribution wording**, verbatim, for the traffic sign artwork.
- The **absolute clauses** of §4.3 as numbered standing rules beside the existing "no identifiable public figure's voice, likeness or name, ever" — which, read closely, already says *likeness*. The image rule is not new. It has just never been applied to a pixel.

---

## 5. The ranked worklist

Impact is "what a player sees in the noon frame"; work is calendar-honest, with
the note that every Game-layer change costs a ~28-minute round trip.

| # | item | impact | work | where it runs | account | risk |
|---|---|---|---|---|---|---|
| 1 | **Lettered signage generator** (§3.1) — fascias, neon words, plates | **highest** | small | **here, no network** | none | none |
| 2 | **ambientCG/Poly Haven resolution bump for eye-level surfaces** (§1.2) | high | **one field + a measurement** | props-fetch CI | none | repo size — measure |
| 3 | **Poster / notice / flyposting set** (§3.1) | high | small–medium | here | none | none |
| 4 | **Hex-tiling / histogram-preserving ground** (§3.2) | high | medium (shader + a build) | Game layer, CI | none | none if implemented from the paper |
| 5 | **UK traffic sign artwork, OGL** (§1.5) | high for Britishness | small | CI fetch (`assets.publishing.service.gov.uk`) | none | attribution + accuracy clause |
| 6 | **Procedural weathering: salt, rust, damp, streaks** (§3.2) | high | medium | Core + shader | none | none |
| 7 | **Poly Haven textures + models** (§1.4) | medium–high | small | props-fetch CI | none | none |
| 8 | **Photo→PBR from Texture Ninja / 3dtextures / TextureCan** (§3.3, §2.1) | medium–high | medium | CI | none | keep GPL tools out of the project |
| 9 | **OGA industrial + harbour packs** (§2.1 row 11) | medium (dockside) | small | existing OGA scrape | none | per-page licence read |
| 10 | **`.glb` in the attribution sweep** (§1.3) | none visible — **but it is the check that guards every row above** | trivial | verify.py | none | — |
| 11 | **Facade rectification from CC0 photos** (§3.6) | medium | medium | here/CI | none | source must be CC0 |
| 12 | **Sketchfab 80s European car + BlenderKit** (§2.1 rows 14–15) | medium (period vehicles) | small once a token exists | CI with Jafar's token | **YES** | per-item licence |
| 13 | **Image-to-3D hero props, MIT models** (§3.5) | medium | medium–large | his machine or CPU CI | none | input image provenance |
| 14 | **Diffusion for painterly one-offs** (§3.4) | medium | large (hardware) | his machine (voice precedent) | none for weights | §4.1 rung 3/4 decision |
| 15 | **Fab/Megascans, Unity Asset Store** (§2.1 rows 17–18) | potentially high | human step per asset | manual | **YES** | licence unclear for non-UE |

---

## 6. Wiring notes, so none of this lands as a pipeline with nothing in it

Four rules, each of which this project has already paid for once:

1. **The manifest is written by the job that writes the files.** Every fetch or generation step writes its own `THIRD-PARTY.md` and `ATTRIBUTION.json` beside the output, in the same run, the way `fetch_visual.py` and `fetch_font.py` do. A licence record that a human updates separately drifts, and for a licence the record is the part that has to be right.
2. **Extend `ASSET_SUFFIXES` in the same change that introduces a new file type** — `.glb` is missing today (§1.3), and `.svg` will be missing the day the traffic signs land.
3. **Fetched is not shipped.** Every drop needs a code path that NAMES the files — checked against the loader's normalisation, by grepping the *normalised key* rather than the filename — and a runtime count on the done line (`signsLettered=`, `decalsPlaced=`, `propsPlaced=`) with a ground-truth list of what actually instantiated. The extracted project had 150 of 213 fetched models named by no line of code; that is the failure this rule exists for.
4. **Measure before you place.** Bounds, vertex count and pivot from each model's own numbers; actual resolution and channel count from each texture, before it is bound to anything. The measured proportions decide the design, not the other way round.
