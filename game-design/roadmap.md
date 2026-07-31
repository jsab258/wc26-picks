# LEDGER — roadmap

> **STATUS — LIVE, verified 2026-07-31.** the plan and the build state. If this
> and another doc disagree, this wins.
> Kept current. If it is wrong, that is a bug in this file.

**One screen of where the project is, what is being built, and what is at
risk.** Anything dated, any post-mortem, any superseded plan lives in
`roadmap-history.md`. If a section here starts growing a chronology, it is in
the wrong file.

---

## Now

**M16 — perception, weapons and violence.** The largest feature in the project,
and the one that changes the framing: a crime game in a city that perceives,
reacts and remembers. Spec: `weapons-spec.md`.

| phase | | state |
|---|---|---|
| 1 | vision, hearing, masking, investigation | **shipped, gated** |
| 1b | vignette, noise ring, four attention channels, captions | **shipped, gated** |
| 2 | witnesses, slots, ID ladder, delivery window, misattribution | **shipped; ghost outstanding** |
| 3 | melee, carry, concealment, the frisk, blood | **building** |
| 4 | provenance, acquisition, disposal, accidents | **building** |
| 5 | firearms | deliberately last, not started |

**Also in flight:** integrating the Mixamo bodies (assets are in the repo; no
code references them yet), and casting the 15 named characters who still fall
through to a crowd voice.

## Shipped

| | | |
|---|---|---|
| M0–M5 | tech spike → vertical slice, hooks, suspicion, the week campaign | ✅ |
| M6 / M6.5 | the open city and Empire v1; the intent router | ✅ |
| M7 / M7.5 | the living economy; operation planning and access | ✅ |
| M8 | the Director — nightly world-level authoring | ✅ |
| M9 | population scale — thousands via generation + LOD | ✅ |
| M10 | phones and the distance layer | ✅ |
| M11 | violence staged — the consequence layer (melee moved to M16) | ✅ |
| M12 | streets and cars | ✅ |
| M13 | finite counterparty purses | ✅ |
| M14 | districts 4–7 — all seven on the ground | ✅ |
| M15 | the world speaks for itself (M15.3 held for a playtest) | ✅ |
| — | Acts I, II and III written and wired; Copper Row; the British setting | ✅ |

## Next, in order

1. **Finish M16 Phases 3 and 4** — the Core is built and tested; most of it has
   no call site in the game, so this is wiring and gating rather than new
   systems.
2. **M17 — the game looks and sounds like itself.** Integrate the Mixamo
   bodies, generate the 19 cast voices, cast the 15 characters who have none,
   curate the barks, source CC0 effort foley.
3. **M18 — the second life.** Home, family, companionship, lifestyle, vice.
   The lowest scores on the board are all the same half of the premise.
4. **M19 — the city pushes back.** Faction allegiance, law as a *tool* rather
   than a threat, notoriety, player competence, visible odds.
5. **M20 — the shape of a playthrough.** Onboarding, pacing, replayability,
   succession that matters before the ending.
6. **M21 — firearms.** M16 Phase 5, deliberately last.
7. **M22 — ship.** Performance, platforms, controller, accessibility, QA.

Reasoning, targets and the open scope call: **`after-m16.md`**. Scores per
dimension: `agency-model.md`, re-scored against the code on 2026-07-31.

## At risk

- **Windows CI is red.** `nightNotDarker` was one noon frame against one night
  frame out of eleven days and failed on a thousandth; the gate now uses the
  whole series and prints it. Unverified until the next run.
- **The animation import** is the only piece that cannot be checked locally at
  all — Unity decides, and the first evidence is a CI screenshot.
- **Phases 2–4 were built, tested and disconnected.** A gap analysis over 61
  public Core APIs found 2 untested and roughly 40 with no call site in the
  game. That is this project's oldest failure mode and the reason the current
  work is wiring rather than building.

## Waiting on Jafar

**Nothing.** The queue in `decisions-pending.md` is empty for the first time
since it was opened.

## The rules this project runs on

- **Measure before you gate.** A threshold set without a measured value is how
  `nightNotDarker` came to fail on noise and `deedSlotSets` went ungated for
  days.
- **Check the ruler before the reading.** Three times this month the instrument
  was the thing at fault — `breakrun.py` reverting one file, the bark manifest
  written to an untracked path, a diagnostic sampling one speaker and reporting
  on a corpus.
- **Built is not running.** A system with no call site is not a feature, and it
  will look exactly like one in a code review.
- **Nothing here requires a purchase.** Characters, animations and voices all
  came free; the last purchase on the list was decided free on 2026-07-31.
