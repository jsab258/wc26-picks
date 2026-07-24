# M0 Tech Spike — Build Plan

## What M0 is, in plain words

Before building the game, we build the smallest possible thing that **proves the risky
ideas actually work together**. Not a demo, not pretty, not fun yet — a proof. Think of it
as building one wall of the house with the actual bricks, wiring, and plumbing before
ordering materials for the whole street.

If any core assumption fails (AI dialogue too slow, too expensive, feels dead; simulation
too heavy), we find out here — in weeks, having built one block — instead of months in,
having built a city. And nothing is thrown away: every system in M0 is the seed of the
real one.

## What exists when M0 is done

A downloadable Windows build. You walk around one city block as a third-person character.
Day turns to night. Three background NPCs live their little routines (home → work → bar).
Inside the bar is **Lena** — the outfit's old bookkeeper and our first real character:

- You talk to her by typing (mic later). She answers in her own voice (TTS), in character,
  driven by her character card.
- She **remembers**. Talk to her Tuesday, come back Thursday — she brings it up. Her memory
  is a markdown file you can literally open and read.
- She has a **suspicion** value. Tell her a lie that contradicts something she saw or heard
  and it rises — visibly changing how she talks to you.
- A debug "Ledger" panel shows her memory stream and suspicion live, so we can watch the
  machinery think.

## The checklist (what I build)

1. **Unity project skeleton** — Unity 6 + HDRP, third-person controller (Starter Assets),
   input, camera, repo-friendly project settings.
2. **The block** — graybox layout (simple volumes for buildings/streets) dressed with free
   HDRP-compatible assets and real lighting. One corner made *good-looking* as the visual
   quality probe. (Buying a proper city asset pack is a later decision I'll bring you
   options for — M0 proves systems, not beauty.)
3. **Clock & day/night** — game time, time slots, lighting cycle.
4. **Schedule sim v0** — 3 NPCs with daily routines and Mixamo-animated characters.
5. **The Lena stack** (the heart of M0):
   - character card (markdown) → system prompt assembly
   - memory stream (markdown) + retrieval (relevance/recency/importance)
   - nightly reflection pass (summarizes the day into beliefs)
   - LLM call (Haiku-class, provider-agnostic client) with player input treated as untrusted
   - hard game-state gate demo: one fact she *cannot* be talked out of
   - TTS voice out, streaming, subtitles-first
   - suspicion variable moved by contradiction checks, not by the LLM
6. **Conversation UI v0** — functional, not styled (UI design is a decision round with you
   later).
7. **Instrumentation** — cost per conversation-minute and reply latency logged from day one.
8. **Automated builds** — GitHub Actions + game-ci so every push produces a downloadable
   Windows build automatically. No dev tools needed on your machine, ever.

## Pass/fail tests (how we know M0 succeeded)

- **Memory**: reference on day 3 something said on day 1 → she recalls it correctly.
- **Integrity**: try to convince her of something she witnessed otherwise → she refuses,
  suspicion rises; jailbreak-style prompts don't break character.
- **Feel**: reply latency ≤ ~4s to first spoken word; conversation feels like a person,
  not a chatbot (subjective — you judge).
- **Cost**: a 10-minute conversation costs cents, measured, with the target ≤ $0.05/hr
  ambient extrapolation.
- **Performance**: 60 fps on the block with sim running.

## The few one-time manual steps on your side

Batched, with exact instructions when we get there:
1. A **Unity account** (free Personal license) — needed for the automated build system.
2. An **LLM API key** (I'll bring provider/cost options as a decision) and a **TTS key**.
3. **Playtesting**: M0 is a Windows build — you'll walk around it on your PC.
   Hardware confirmed (2026-07): mid-range gaming PC, built ~early 2025. Performance
   target set accordingly: 60 fps at 1080p–1440p, HDRP medium-high settings.

## Explicitly NOT in M0

Combat, rackets, money, gossip between NPCs (M1), more than one deep character, real UI
design, story content, character customization, purchased asset packs.

## Order of work

Skeleton → block+clock → schedule NPCs → Lena stack (longest) → UI/debug panel →
instrumentation → CI builds → your playtest → verdict against the tests above → M1 plan.
