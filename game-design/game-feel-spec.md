# Game feel — the full spec, benchmarked against KCD2 / GTA5

**Status: SPEC, 2026-07-28.** Jafar: *"you just listed a few things, I hope
this isn't all. benchmark is KCD2/GTA5 (yes I know we won't get there, but
aspirationally/directionally)."* He was right — the earlier list was a
handful of items. This is the real taxonomy.

**Target set to MAX MATURITY.** Almost none of it costs money; nearly all of
it is my time. Items marked **[NOW]** work on capsules and can be built
today. Items marked **[MODELS]** need the character purchase first.

---

## 0. The definition

Game feel is the *tactile response of the moment to moment* — the difference
between a character who **moves** and one who **teleports smoothly**. It is
almost entirely made of things no player consciously notices and every player
feels. It is also the thing that most reliably separates "prototype" from
"product," which is exactly where LEDGER sits today.

The uncomfortable truth: **you can fix 70% of "this feels cheap" without a
single art asset.** We have done none of it.

**Update 2026-07-28 — the first pass is in.** Momentum, turn radius, camera
spring, speed-linked FOV, look-ahead, camera collision, head bob, the limp,
surface-aware footstep variants, input buffering and forgiveness windows all
exist. The maths lives in `Assets/Scripts/Core/Feel.cs` rather than in a
MonoBehaviour, and is covered by 44 checks in CoreTests — because every one
of these is invisible in a screenshot and obvious in the hands, which is the
worst possible combination for a system with no tests. Eight deliberate
regressions (instant velocity, welded camera, frame-rate-dependent lag, a
limp that changes speed, a turret turn, a buffer that never expires, decel
slower than accel, a camera that sweeps on teleport) were each reintroduced
and each caught.

---

## 1. Input and response **[NOW]**

- **Input buffering.** A key pressed 100ms before an action becomes legal
  still registers. Without it the game feels like it is ignoring you.
- **Forgiveness windows.** Interaction prompts stay valid a beat after you
  step out of range.
- **No input lag.** Fixed-timestep input sampling; never poll input in a
  coroutine.
- **Frame pacing over frame rate.** A locked, consistent 60 feels far better
  than an unlocked 90 that stutters. *Stutter destroys feel faster than low
  fidelity does* — this is the single most under-rated item on this page.

## 2. Locomotion **[NOW for most]**

- **Momentum.** Acceleration and deceleration curves; you lean into a start
  and settle out of a stop. Currently: instant velocity, which is the single
  most "prototype" thing about moving around LEDGER.
- **Turn radius.** Body rotates over time; sharp reversals cost a moment.
- **Gait states** with blended transitions: idle → walk → jog → run, plus
  **injured**, **tired**, **carrying**. We already simulate injury and never
  show it — a limp is free characterisation from data we already have.
- **Foot IK** so feet plant on kerbs and stairs instead of sliding. **[MODELS]**
- **Root-motion vs code-driven** decision, made once, applied everywhere.
  **DECIDED 2026-07-28: CODE-DRIVEN.** Made deliberately BEFORE the
  animations land, because after they land it is a rewrite. The momentum,
  turn rate and gait in `Core/Feel.cs` are already tested and frame-rate
  independent; root motion would put authority for movement inside animation
  clips we did not author and cannot test, and the two would fight. The cost
  is accepted and named: foot sliding, which foot IK fixes and which is
  cheaper to fix than a movement model is to replace.
- **Slope and stair handling** that does not judder.
- **Head bob and hand sway**, subtle, scaled to gait — off by default in
  options for motion sensitivity.

## 3. Camera **[NOW]**

This is where the biggest cheap win in the whole document lives.

- **Spring-arm with lag** — the camera follows, it is not welded on.
- **FOV widens with speed**, narrows when you stop. Free sense of pace.
- **Look-ahead** in the direction of travel.
- **Landing/impact settle** — a small dip, quickly recovered.
- **Collision** that slides rather than clipping through geometry.
- **Focus pulls** — shallow depth of field when a conversation opens, so the
  street softens behind the person you are talking to. Cheap, and it does
  more for "cinematic" than any post effect.

## 4. Audio feedback **[NOW]**

- **Footsteps by surface** (asphalt / wet asphalt / wood / gravel / interior
  tile) **× gait × 4–6 random variants each**, so it never sounds looped.
  Currently one sound, always.
- **Foley**: clothing rustle, keys, the coat being put on and taken off.
  **BUILT 2026-07-28** — and the coat became a real verb at the same time,
  with a wind-up you can change your mind during, rather than a boolean
  with a toast attached.
- **Reverb zones** — the bar sounds like a room, the alley sounds like an
  alley, the street sounds like outside. Nothing sells a *place* faster.
- **Occlusion**: voices muffled through a wall or a door. **Speech only so
  far.** General audio occlusion needs per-source 3D audio and every source
  in the game is currently 2D — that is a real refactor, not a tweak, and
  half-doing it would mean a muffled bin next to an unmuffled car. Named
  here as outstanding rather than quietly counted as done.
- **Distance filtering** on all speech: a bark at fifteen metres is
  low-passed and quiet. (This also disguises TTS engine seams — see the
  voice plan.)
- **Impact and interaction sounds matched to material.** **BUILT
  2026-07-28** — metal rings, glass is bright and short, wood is a dull
  knock. A single generic thud is how a world announces that nothing in it
  is really there.

## 5. World response **[NOW]**

- **Doors with mass**: handle, swing, latch, and a slight camera nudge.
- **Objects react to being brushed** — a bin, a bottle, a chair. **BUILT
  2026-07-28.** A world where the bins are welded to the pavement is a world
  of scenery; one where a bin rocks when you clip it is a world of objects,
  and the difference costs a nudge and a sound rather than an art budget.
- **Puddles splash** **BUILT 2026-07-28** — and deliberately not on every
  step, because a splash under every footfall reads as wading rather than as
  walking on wet ground. Footprints in the wet and rain landing ON things are
  still outstanding.
- **NPCs react to being bumped** — a stumble, a look, a word. Right now you
  walk through a crowd like a ghost, which quietly tells the player that
  none of it is real.

## 6. Interaction grammar **[NOW]**

Every verb should have: **anticipation → action → consequence → recovery.**
Instant state flips are the hallmark of a prototype.

- Contextual prompts that **fade in and out**, never pop.
- Money that has a weight and a sound.
- Wearing the coat should take a moment and read on the body. **[MODELS]**

## 7. State written on the body **[MODELS, mostly]**

KCD2's masterstroke, and we already simulate almost all the state:

- **Injury → limp**, favouring a side, slower gait. *We have the data today.*
- **Fatigue → breathing**, slower recovery.
- **Rain → wet**, visibly.
- **The coat** on or off, visible at distance — it is a mechanic, so it must
  be legible from across a street.
- **Money**: a bulge in the coat when carrying a lot of dirty cash would be
  a beautiful, diegetic, entirely free-to-simulate tell.

## 8. Transitions **[NOW]**

- No hard cuts anywhere: fades, camera moves, a held beat.
- **Continuous** day/night lighting, not stepped.
- Menu ↔ game transitions that are not an instant swap.
- The Fall's three lost days deserve a real transition — it is the biggest
  moment in the game and currently it is a toast.

## 9. Feedback discipline **[NOW]**

- Every player action gets a response inside 100ms, even if only a sound.
- Never two channels for one event (the audit already caught toasts fighting
  each other for one slot).
- Silence is a choice, not an absence.

## 10. Controller and haptics **[LATER — P6]**

Rumble on impact, on the door, on the money. Deferred, but the input layer
should be built so it is not a rewrite.

---

## What I would build first, in order

1. **Camera craft + movement momentum.** Biggest felt change per hour, works
   on capsules, no assets. (§2, §3) — **BUILT 2026-07-28.**
2. **Footsteps by surface + reverb zones + distance filtering.** Transforms
   the *place*, and the distance filter is needed by the voice work anyway.
   (§4) — **BUILT 2026-07-28.** Footstep surfaces and variants, a reverb
   zone driven by which space you are standing in, distance filtering,
   occlusion, and the model tied back into the gossip mill so how well you
   heard something decides how sure the rumour you carry away is. See
   `Assets/Scripts/Core/Acoustics.cs`.
3. **Interaction grammar and door weight** — prompts that fade, doors that
   have mass, NPCs that react to being bumped. (§5, §6) — **BUILT
   2026-07-28.** Verbs have anticipation/action/consequence/recovery; doors
   are damped springs that overshoot, settle and latch; the prompt fades and
   is buffered and forgiving; walking into someone staggers them and buys
   their attention. Remaining in §5: objects reacting to being brushed, and
   puddles that splash.
4. **The limp.** Free characterisation from data we already have, and a
   perfect demonstration of the whole "stage it, don't show it" principle.
   — **BUILT 2026-07-28**, and it needed no model: a limp is an ASYMMETRY,
   so the alternating stride length and the heavier footfall on the good leg
   carry it entirely through sound and cadence.
5. **Transitions**, especially the Fall. — **BUILT 2026-07-28.** The Fall
   now drops a curtain, changes the world under full black where the join
   cannot be seen, holds the words long enough to be uncomfortable, and
   returns into a different morning. Remaining in §8: continuous rather
   than stepped day/night, and menu transitions.

Then everything in **[MODELS]** the moment the character purchase lands.

---

## Honest expectation setting

Doing all of the above gets LEDGER from "prototype" to "competent indie."
It does **not** get to KCD2 — that gap is animation quality, art direction
and production values, and it is bought with an art team, not a to-do list.

But this is the part where the gap closes fastest per pound spent, and it is
almost entirely free. It is also invisible when done right, which is why it
gets skipped, and why skipping it is exactly what makes a game feel cheap.
