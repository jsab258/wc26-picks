# The playtest plan — Jafar's Windows machine, live voices on

> **STATUS — LIVE**, verified 2026-08-22. Retargeted by Jafar's own words
> ("I'll try to run it on my windows machine after visual stuff is done.
> live voices/speech should be working too"). The Mac-Air framing below
> this section is HISTORICAL — kept because it is the argument for work
> that shipped, not a description of the next session.

## The goal

Jafar plays LEDGER on his Windows machine once the visual pass settles.
Live voice generation is ON: his machine has the GPU and DirectML the
Air lacked, the game's speech backend already prefers DirectML and
falls back to CPU with a printed reason, and the whole export pipeline
lives on that machine from the bark-rendering sessions.

## The Windows session, step by step

1. **Pull the repo** on the PC (`wc26-picks` in the user folder, from
   the bark days) so the voice tools are current.
2. **Run `tools\voice-live\CAN THE CAST SPEAK.bat`** — the one-click
   end-to-end check. If it asks for the environment, `1 RESTORE THE
   ENVIRONMENT.bat` first (or `2 TRY THE EXPORT.bat` rebuilds it
   unattended). The one-time model export for the game is
   `5 EXPORT FOR THE GAME.bat`; `7 TIME A LINE.bat` then says in a
   minute whether the GPU makes speech real-time.
3. **Download the game**: the `LEDGER-Windows` artifact on the newest
   green build run, unzip anywhere.
4. **Run `9 PUT THE VOICES IN THE GAME.bat`** — it finds the unzipped
   build itself (Downloads, Desktop, home), installs the models and
   voices, and names what it picked.
5. **Start the build and walk up to somebody.** The done-line's speech
   counters and the backend's own printed reason are the first things
   to read if anything is silent.

## Faster builds — the runner on Jafar's PC (optional, 22 Aug)

`tools\runner\1 SET UP THE BUILD RUNNER.bat` (right-click, Run as
administrator) moves the Windows builds onto his PC: the GPU renders
the sim ~20x faster than the cloud machine's software rasteriser and
the Unity install caches between builds, so the ~28-minute round trip
drops to roughly 6-10 after the first run. One paste from him (a
registration token GitHub shows behind his login); the script pushes
`tools/runner/READY.txt` and **the loop then flips the build
workflow's `runs-on` to `[self-hosted, ledger-pc]` by itself** —
that marker landing is the signal. Builds queue while his PC is off;
`2 REMOVE THE RUNNER.bat` plus a one-line revert undoes everything.

## The old Mac plan (historical)

The section below planned the 19 August Air session: no DirectML, so
live voice was off and the recorded bank carried conversations. That
constraint died with the machine change; nothing else in it is load-
bearing for the Windows session.

Jafar and two friends play LEDGER Wednesday–Friday, on a MacBook Air,
passing the laptop around. The build has to launch, look like a place
rather than a greybox, control acceptably on a trackpad, teach its first
five minutes, survive café wifi, and let three different people play
without inheriting each other's ghosts. Live voice generation is OFF the
table on this machine (no DirectML) and accepted: characters use the
recorded bank, conversations are text. Maximum roadmap progress, but only
where it shows inside a three-day session.

## What the research established (checked, with anchors)

> **Now historical**: every fault this section names except the
> animation re-pick and the Air's resolution control was FIXED in the
> two batches of 15 Aug — the work log above each fix is in "The work,
> in order" below. Kept as written because it is the argument for the
> plan's shape, not a report on today's code.

**The world is already textured and nobody can see it.** Twelve real 1K
photographs (ambientCG, CC0) ship in `StreamingAssets/CityPack/textures`
and load at runtime — and `AssetLibrary.cs:137` multiplies every one by a
noir tint that crushes ten of twelve surfaces below 0.19 albedo (asphalt
0.045, windows 0.041). The film grain is 2–35× louder than the surviving
texture detail. The procedural fallback applies the same tint twice
(baked into pixels AND multiplied). This is the greybox, in one line.

**There is no skybox anywhere.** The sky is a flat grey fog-colour card
(`SceneLighting.cs:99`), while a correct three-stop gradient
(`SkyColour/HorizonColour/GroundColour`, `LightModel.cs:227-258`) is
computed every frame and fed only to ambient light. Wet reflections
currently reflect the grey card — on the one surface the art direction
is built around.

**A fifth of the street is not people.** `X Bot` and `Y Bot` — grey
untextured rig mannequins — sit in the body pick pool
(`RealBody.cs:459`) with nothing excluding them. Of the other eight
Mixamo bodies, three are wrong for 1980s/90s Britain (Sporty Granny's
tracksuit, The Boss's modern suit, Big Vegas), four are marginal, none
is positively right. **Adding bodies needs no code**: drop FBX in
`Assets/Characters/`, everything downstream is automatic — the
roadmap's "purchase decision" claim was wrong, it is a download. The
character catalogue (`characters_available.txt`) is gitignored, so all
picks so far were made blind, by name.

**Only 3 of 42 downloaded animation clips are wired** (idle/walk/run,
one shared controller for every body — `CharacterPrefab.cs:257`). The
walk-start/stop clips are literally catwalk sashays (a regex mis-hit,
`pick_animations.py:95`). The harvest on Jafar's disk already contains
`Old Man Walk`, `Female Start Walking`, `Leaning On A Wall`, `Carrying`,
`Walking With Shopping Bag` — never picked. A re-pick is seconds and
needs no token.

**Conversations need an Anthropic key at runtime.** F2 panel →
`secrets.json` in persistentDataPath (`Secrets.cs`); the env var won't
survive a Finder launch. Cost ≈ 1¢ per typed line, a long evening well
under a dollar — but it is Jafar's key and Jafar's spend. Without a key
every character answers `"(no API key configured)"`. Worst case on
dropping wifi: **4 minutes 14 seconds** of "thinking..." (60s timeout ×
4 attempts + backoff, `LlmClient.cs:64-72`, no cancel). Only other
network dependency: none.

**The trackpad will fight the camera.** Mouse-look is unbuttoned and
always on; `Cursor.lockState` appears nowhere in the codebase. The OS
cursor floats over the game permanently.

**Three friends share one identity.** "New game" deletes the autosave
but keeps every NPC's memory file (`persistentDataPath/memories/*.md`,
reloaded on construction) — player two inherits player one's
reputation, and deletes player one's save. "Press R to start the week
over" actually dumps to the title screen.

**The Mac build itself.** The 4 Aug failure was the known `TrafficHost`
compile error (read from the run log), long fixed; a fresh build is
running now. Real blockers found in the workflow: the artifact ZIP
**strips the executable bit** (the .app cannot launch as downloaded —
needs `chmod +x` or a workflow fix to zip before upload), Gatekeeper
quarantine needs `xattr -dr`, the architecture is unpinned (possibly
x86_64-under-Rosetta — must check `lipo`), the licence step lacks the
retry the Windows job got on 4 Aug, and the trigger watches only 2
paths so three days of changes can accumulate unbuilt.

**Performance on an Air.** The graphics preset defaults to **High**
(360 shaft cones). Worse: the post stack (6–8 full/part-res blits per
frame, `FilmGrade.cs`) scales with pixel count, runs at native Retina
(~4.3 Mpx), and **is not reduced by the preset at all**. There is no
resolution or render-scale control anywhere. The CI frame gate
(game 12.93ms vs 12ms budget) is a separate, smaller matter.

**What already works and needs nothing:** title screen with slots and
options; nine rebindable keys; Escape pause with save-and-quit; the
recorded voice bank (tracked in the repo, plays on any platform); fonts;
shaders are Metal-safe; zero Windows-only APIs outside the `LEDGER_ONNX`
guard; saves are atomic with backups.

## The work, in order — what shows on screen first

### Tonight (Sat) — the platform stops being a guess — **DONE 15 Aug**
1. ~~Mac workflow repair~~ **DONE, validated green same evening**: zip
   before upload (permissions survive), `lipo -archs` printed, licence
   retry, `-e` bug fixed, triggers widened, step summary added.
2. ~~Read the in-flight mac run~~ **DONE**: green, artifact
   `LEDGER-macOS` 347 MB, expires 2026-08-29.

### Sunday — the two big visual levers, one batch — **CODE DONE 15 Aug
### evening, verified green; stills judgement pending the dispatch**
3. ~~Untint the textures~~ **DONE**: `TextureGrade` (0.82/0.84/0.88)
   replaces the tint-multiply when a texture is present; `SetWetness`
   darkens the grade; tint keeps its procedural-base and no-texture
   jobs. Judged on stills next, iterated by changing one constant.
4. ~~Skybox~~ **DONE**: `Hidden/LedgerSky` gradient driven per-frame
   from the three computed colours, horizon stop = fog colour so the
   seam is impossible; camera clears to Skybox with SolidColor
   fallback; dry reflections refresh via thresholded environment
   updates; wet ground keeps its own probe capture.
5. ~~Facade variety + tiling~~ **DONE**: position-hash facades, tiling
   aspect-corrected against the bound texture.
6. ~~Bots out of the pool~~ **DONE**: `IsMannequin` (one
   implementation, Editor writer + runtime pool both call it), no
   Body_XBot/YBot prefab written at all; default body is Joe.
7. ~~Mac-experience batch~~ **DONE**: cursor locks in play and frees
   for menus/panels/pause/end (policy beside the input-lock policy it
   mirrors); New game AND R-restart wipe `memories/`; R restarts
   straight into a fresh week (was: title screen); quit-to-menu now
   tears down by scene reload (was: second city built over the first
   on New game — read from code, never caught by the sim); LLM 15s
   timeout + 1 retry both clients; chips skip the router (faster and
   cheaper per press); Cmd-Q/close-box saves; first-run preset Medium
   (sim pinned to High so every committed still and verdict number
   stays comparable).
8. ONE Windows dispatch for stills — **tonight's remaining step**.
   Iterate the grade off the stills (overnight/morning).

### Monday — people and playability (Jafar's PC in the loop)
9. **Characters, his half (~10 min)**: fresh Mixamo token → catalogue
   dump (un-ignore `characters_available.txt`) → I pick names in era →
   `MORE-BODIES` fetch → `REPICK` with the expanded WANTS (old walks,
   female start/stop, lean, carry, shopping bag, idles, argue, phone —
   the WANTS list lands in the repo tonight so his one run gets all).
10. **Characters, my half**: per-physique locomotion controllers so an
    old body gets `Old Man Walk` and female bodies the female
    start/stop; wardrobe wash already handles the rest.
11. **Resolution/render-scale option** (the one lever the Air needs) +
    post-stack cost drop on Low/Medium.
12. Onboarding: the three toasts become a taught first five minutes;
    prompts print the *bound* key, not a hardcoded letter; toast queue
    so a bark cannot eat a beat.
13. Second stills round; frame-gate work only if time allows.

### Tuesday — freeze and prove
14. Feature freeze at noon. Final builds (Windows + Mac).
15. **Jafar's 15-minute Mac smoke test** off the RUNBOOK (written by
    then): Gatekeeper dance, chmod if needed, F2 key entry, walk, talk,
    save, quit, relaunch, Continue. Fix only what the smoke test finds.
16. Final artifact + `PLAYTEST-RUNBOOK.md` (download link, setup
    incantations, controls card, known limits, "if wifi dies,
    conversations degrade — the street keeps talking").

### Wednesday — play. Nothing ships Wednesday morning.

## What Jafar has to do (the critical path — nothing here is optional)

| when | what | time |
|---|---|---|
| Sun or Mon | Fresh Mixamo token → run the catalogue dump + fetch + re-pick bats (exact clicks will be in the runbook and chat) | ~10 min |
| by Tue | Anthropic API key for the playtest + explicit OK on the spend (measured estimate: an evening of heavy play stays **under $1**; three days well under $10) | 2 min |
| any time | Confirm the MacBook Air is Apple Silicon (M-series) — decides whether Rosetta matters | 10 sec |
| Mon or Tue | The 15-minute smoke test on the actual MacBook | 15 min |

## Decisions taken here (veto any of them)

- Playtest voice = recorded bank; live speech work is **parked** until
  after (the deterministic-sampler retry fix is designed and queued).
- Preset defaults Medium; players can go Low/High in Options.
- "New game" wipes NPC memories; friends use the manual save slots for
  their own runs.
- No code signing/notarisation (an Apple Developer ID is a purchase):
  the runbook carries the two-line Gatekeeper incantation instead.
- The frame-time CI gate stays red-tolerated until the visual work
  lands; a Air-side render-scale control beats shaving 0.9ms of CPU.

## Risks, named

- **The tint retune goes muddy or garish.** Mitigation: iterated on
  stills Sunday; the post stack (grain/vignette/AO) carries the noir
  mood and stays untouched.
- **The Mac artifact fails on real hardware in some way CI cannot see.**
  Mitigation: Tuesday smoke test is mandatory; Monday build exists as a
  fallback candidate; worst case the Windows tower build is the
  playtest and the Air is the lobby music.
- **Mixamo token/harvest friction eats Monday.** Mitigation: everything
  I control (WANTS, name lists, bat fixes) lands tonight so his ten
  minutes are actually ten minutes; the current eight bodies with bots
  excluded are the fallback street.
- **Café wifi.** Mitigation: 15s timeout + 1 retry lands Sunday; the
  no-key/no-net degrade is clean (street keeps talking); the F1 panel
  shows spend live.

## Scope change, Sunday 16 Aug — Jafar: "textures and models have to
## come before playtest. max polish."

Models and texture detail move INTO the pre-Wednesday scope. Landed
same morning: the CC0 model-kit pipeline end to end (fetch job,
prefab ingestion, swap-in for traffic vehicles, benches and bins,
every site keeping its primitive fallback) and normal maps end to end
(fetch, pack check, runtime bump maps with the DXT5nm swizzle, shader
variant kept). Both fetches run in CI; candidate model names are
corrected from committed kit listings, then one Windows build judges
meshes + relief + the settled grade together on stills.

## Explicitly out of scope until after the playtest

Live speech on any platform, streaming, firearms (M23), credits/licence
screen (M24 22.1 — noted, owed), controller support, signing, the
frame-gate perf work beyond what the Air needs, and every `gates
--constant` plant on the queue.
