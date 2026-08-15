# The playtest plan — Wednesday 19 August, a MacBook Air, three players

> **STATUS — LIVE**, verified 2026-08-15. The plan for the four days between
> now and the playtest. Supersedes queue order until Wednesday; `queue.md`
> points here. History and working-out live in the git log, not here.

## The goal

Jafar and two friends play LEDGER Wednesday–Friday, on a MacBook Air,
passing the laptop around. The build has to launch, look like a place
rather than a greybox, control acceptably on a trackpad, teach its first
five minutes, survive café wifi, and let three different people play
without inheriting each other's ghosts. Live voice generation is OFF the
table on this machine (no DirectML) and accepted: characters use the
recorded bank, conversations are text. Maximum roadmap progress, but only
where it shows inside a three-day session.

## What the research established (checked, with anchors)

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

### Tonight (Sat) — the platform stops being a guess
1. **Mac workflow repair** (no Unity compile risk): zip the .app
   *before* upload so permissions survive; print `lipo -archs` in the
   verdict; licence retry (copy of the Windows one); fix the `-e`
   error-reporting bug; widen trigger paths to `Assets/Editor/**` and
   `Assets/Characters/**`; add a step-summary. Push AFTER the in-flight
   mac run lands (single licence seat).
2. Read the in-flight mac run: green → artifact exists; note arch.

### Sunday — the two big visual levers, one batch, one dispatch
3. **Untint the textures** (`AssetLibrary.cs:137` + `SetWetness` +
   procedural double-tint): texture present → neutral grade (~0.85
   desaturated blue-grey, tunable), tint stays only as the procedural
   generator's base. The noir look must survive — judged on stills,
   iterated same day.
4. **Skybox**: drive a gradient sky from the three already-computed
   colours; `clearFlags` → Skybox. Fixes wet reflections for free.
5. Facade variety (`i % 4` → position hash) + `SetTiling` aspect fix.
6. **Bots out of the pick pool**; default body repointed off X Bot.
7. The Mac-experience batch: cursor lock while no panel wants input;
   New-game clears `memories/`; R-restart actually restarts; LLM
   timeout 15s/1 retry + chips skip the router; `wantsToQuit` →
   SaveNow; preset defaults Medium (not High) on first run.
8. ONE Windows dispatch for stills (visual judgement) + mac build.
   Iterate the grade off the stills the same evening.

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

## Explicitly out of scope until after the playtest

Live speech on any platform, streaming, firearms (M23), credits/licence
screen (M24 22.1 — noted, owed), controller support, signing, the
frame-gate perf work beyond what the Air needs, and every `gates
--constant` plant on the queue.
