# Production plan — voice, characters, art direction, feel, budget

> **STATUS: SPEC.** The design for voice, characters, art direction, feel, budget. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees
> with the roadmap is out of date about what got built, not about what
> was intended.

**Status: PROPOSAL for Jafar, 2026-07-28.** Answers his six questions after
the M15 playtest. Nothing here has been bought or started. Prices are
estimates from what I know and **must be re-checked at purchase time** —
treat them as order-of-magnitude, not quotes.

---

## 1. Voice / TTS — the questions I need answered first

He is right that this is the whole ballgame: *"we are letting AI do what
KCD2/GTA5 used voice actors for, it can't sound obviously AI."* Before I
write a line of integration code, six things decide the entire approach.

### 1a. The finding that changes the architecture

**Most of our speech does not need to be generated at runtime.** Split it:

| Channel | Volume | Runtime? | Implication |
|---|---|---|---|
| Ambient life, barks, recognition, refusals | Large but FINITE | No | Pre-generate offline, ship as audio assets, zero runtime cost |
| Named-cast free dialogue (LLM) | Unbounded | Yes | Streaming TTS, per-hour cost, latency matters |

That split is the difference between a viable product and an unshippable
one, because of this:

**Rough runtime cost per hour of play, cast dialogue only** — assume 20
conversations/hour, ~6 replies each, ~25 words ≈ 900 characters, so ~18k
characters/hour:

- Premium emotional TTS (ElevenLabs-class, ~$0.15–0.30 / 1k chars):
  **~$3–5 per hour of play.** Unshippable as a paid product; fine for our
  own playtesting.
- Commodity TTS (OpenAI-class, ~$0.015 / 1k chars): **~$0.25/hour.**
  Viable, but this is also the tier that sounds most obviously synthetic.
- **Local model on the player's GPU (XTTS/F5/Kokoro-class): $0/hour**, no
  API dependency, works offline — at the cost of install size, a GPU
  requirement, and quality that needs testing.

**Therefore the recommended shape:** premium voices for the ten named cast
members (low volume, highest quality bar, much of it pre-generatable), and
either commodity-cheap or local for everything else. Ambient barks get the
premium treatment ONCE, offline, because they are finite.

### 1b. What actually makes TTS sound "obviously AI"

Not the timbre — modern models are fine there. The tells are:
- **Flat affect and uniform pacing.** Every line the same energy.
- **Wrong emphasis** on the semantically loaded word.
- **No breath, no hesitation, no overlap.** Real speech has friction.
- **Wrong reading of ambiguity** — "That's *your* problem" vs "That's your
  *problem*."
- **Emotional monotony across context** — the same delivery whether the
  character is frightened or bored.

Mitigations that actually work: models with explicit style/emotion control;
per-line direction (we know the speaker's suspicion, loyalty, and stance —
we can pass "wary, lowered voice" as a style tag from real game state);
generating 2–3 takes and keeping the best; and deliberate imperfection
(room tone, breath, occasional stumble).

**We have an unfair advantage here:** the game already computes the
emotional state behind every line. Most TTS work is done blind; ours can be
directed from the simulation.

### 1c. THE QUESTIONS I NEED ANSWERED

1. **Setting and accent.** The names are Slavic (Zlatko, Vesna, Rita,
   Joey) but the writing is English. Is this a fictional Eastern European
   port, an émigré quarter in an English-speaking city, or somewhere
   unnamed? **This matters more than the model choice** — non-native
   accents are the single thing current TTS does least convincingly. If
   the answer is "everyone has a Slavic accent in English", the quality bar
   gets much harder to clear and I would push back toward "unnamed city,
   neutral voices with regional character in the WRITING rather than the
   accent."
2. **Era.** Cars, telephones, ledgers, no computers — I have been writing
   toward interwar/post-war. Confirm, because it drives voice casting,
   music, and every art decision below.
3. **Shipping model.** Personal project / demo / actual commercial release?
   This decides whether $3/hour runtime cost is acceptable.
4. **Player-supplied keys?** The game already asks for an Anthropic key.
   Is "bring your own TTS key" acceptable, or must it work out of the box?
5. **Full voice or partial?** Fully voiced cast + ambient? Or the KCD2-lite
   approach — cast voiced, crowd barks voiced, long-tail dialogue text?
6. **Local model acceptable?** Adds GPU requirement and ~1–3GB install, in
   exchange for zero runtime cost and offline play.

### 1d. BENCHMARK RESULT #1 — piper, the control case: FAILED (2026-07-28)

Jafar ran the benchmark and listened. Verbatim:

> "very obviously synthetic, no emphasis, very unnatural"

Per test:

| test | result | reading |
|---|---|---|
| consistency (10 lines, one character) | *"consistent but literally all of them sound the same"* | passed **degenerately** — uniformity, not character |
| direction (same line BORED vs GRAVE) | *"same"* | **total failure**, the most important result on this page |
| emphasis ("That's **your** problem") | *"no stress"* | failure |
| numbers ($120, day 8) | *"read correctly"* | pass — but table stakes |
| long dialogue | *"doesn't change but I wouldn't call it alive"* | flat |
| speed | median RTF **0.04** on CPU | 25× faster than real time |

**This is exactly what the control case is for.** Piper was included to set a
floor: *if something more expensive is not audibly better than this, it is
not worth its cost.* We now have that floor, and it is measured rather than
guessed.

**What it proves, beyond piper.** Look at which tests failed: direction,
emphasis, aliveness. Those are precisely the tells listed in §1b, and they
are all the same underlying thing — **a model that maps text to phonemes
cannot be directed.** Piper has no input for how a line is meant to be said,
so it was never going to pass tests 2, 3 and 5. Its speed proves the same
point from the other side: 0.04 RTF is cheap because the model is not
reasoning about delivery at all.

**Therefore the decisive criterion is no longer quality-in-general — it is
whether an engine takes direction.** That single property is what makes our
unfair advantage (§1b: the game already knows how every speaker feels) worth
anything. A gorgeous engine that ignores direction gives us pre-recorded
voice acting with extra steps; a merely good engine that takes direction
gives us something no recorded cast can do.

Benchmark v5 is rebuilt around that:

- **chatterbox** added, specifically because it exposes an `exaggeration`
  control. The bench now maps every case's stage direction to a scalar, with
  BORED at 0.25 and GRAVE at 0.8, so the headline test is a real A/B.
- **kokoro and xtts made to actually run.** They installed but never loaded:
  kokoro was missing `misaki[en]` (its phonemiser, which also bundles
  espeak-ng so Windows needs no MSI), and xtts refused to synthesise without
  reference clips when it ships ~58 built-in speakers. Both were my bugs.
- **One venv per engine**, because these packages pin conflicting torch
  versions and installing one silently broke the next.
- **eleven** available opt-in as a paid ceiling reference, so "is local good
  enough" is answered against a real upper bound rather than an argument.

### 1e. BENCHMARK RESULT #2 — kokoro passes on speed, fails on direction

| engine | audio | median RTF | direction | verdict |
|---|---|---|---|---|
| kokoro | yes | **0.33 on CPU** | *"grave and bored are exactly the same"* | fast enough to be live; cannot be directed |
| piper | yes | 0.04 | none | the floor, already judged |
| chatterbox | **no** | — | — | `TypeError: 'NoneType' object is not callable` on load |
| xtts | **no** | — | — | `ModuleNotFoundError: torch` — my installer bug |

**Kokoro's result was predicted and is worth stating plainly: it has no
input for emotion, so it was never going to pass.** The bench marks it
`directable = False`. The only lever available was pace, and pace alone is
not direction. So it fails the headline test for the same structural reason
piper does.

What kokoro DID prove is the speed case, and that is not nothing. **0.33 RTF
on a CPU with no GPU at all** is inside the live-dialogue budget, and on a
GPU it would be several times faster. That makes kokoro a real candidate for
the channel where direction matters least — anonymous crowd ambience, where
the point is that the street is talking, not what any one person feels.

**Two of the four engines have still never run**, and both failures are
mine to fix rather than findings about the engines:

- **xtts** died with a bare `ModuleNotFoundError: torch` after pip exited 0.
  The install had failed and `--quiet` hid the reason. The benchmark now
  verifies every install by importing the engine's own module, and re-runs
  pip loudly when that fails. An install is not finished until the thing it
  installed can be imported.
- **chatterbox** loaded its models — all 3.2 GB of them downloaded — and then
  threw `TypeError: 'NoneType' object is not callable`. The traceback named
  it: `self.watermarker = perth.PerthImplicitWatermarker()`. `resemble-perth`
  wraps its own imports in a try/except and binds the name to **None** when
  they fail, so a broken dependency never surfaces as an ImportError — it
  surfaces 3.2 GB later, on a line that looks perfectly fine. Diagnosed and
  stubbed with a no-op, with a note that the stub must not survive into a
  shipping build: the watermarker exists so generated speech stays
  identifiable as generated, and if chatterbox wins we fix perth and keep it.

**And the fix I shipped for xtts did not run.** v6 added an install probe;
the broken `.venv-xtts` from v5 still carried its "installed" stamp, so the
early return fired and the environment sailed straight past the check added
to catch exactly it. A stamp records that we once finished installing, not
that the result works, and only the second of those is worth anything.
Cached environments are now re-probed and repaired every run — which is the
general lesson, not an xtts one.

### 1f. THE IDEA THAT CHANGES WHAT "DIRECTABLE" MEANS

Two engines are down to one testable property between them, so this is worth
saying before the next run rather than after.

**A cloning engine does not need an emotion dial, because the reference clip
IS the direction.** XTTS and chatterbox both copy the delivery of whatever
audio they are given. Feed a grave reference and the line comes out grave.

That reframes the whole benchmark. Cloning was listed here as the answer to
the pre-generated/live seam; it is also a second, entirely different route
to direction — and the one that does not depend on a model exposing a
parameter some maintainer might remove.

It scales, too, which is the part that makes it practical: the game knows
the mood of every line it will ever produce, and there are only a handful of
moods. Five minutes of reference audio per character covers thousands of
barks. The bench now looks for `lena.wav`, `lena.grave.wav` and
`lena.bored.wav` and picks by the same stage direction the scalar engines
get, so the headline BORED-vs-GRAVE test becomes a real A/B for cloning
engines as well.

### 1g-ter. DIRECTML WORKS ON HIS GPU, AND torch-directml IS OUT (5 Aug)

**Measured on Jafar's machine, which is the only place it could be measured:**

    onnxruntime 1.24.4, DirectML AVAILABLE - DmlExecutionProvider, CPUExecutionProvider
    torch-directml   ImportError: DLL load failed importing torch_directml_native
    chatterbox       ModuleNotFoundError: Could not import module 'LlamaModel'

**The first line is the one that matters and it is a yes.** ONNX Runtime sees
and offers his AMD GPU. That is the precondition for the only route that could
ever ship, confirmed on real hardware rather than assumed in either direction.

**The other two are one fault, and it was the probe's own bat that caused it.**
`torch-directml` pins `torch==2.4.1`; `chatterbox-tts` requires 2.6.0.
Installed into one environment, pip uninstalled one torch and installed the
other, leaving binaries that cannot load — the run died on `torchvision\_C.pyd`,
"Entry Point Not Found", before rendering anything. The chatterbox failure is
the same resolver collateral one layer along: a transformers new enough for the
new torch no longer exports `LlamaModel` under the name chatterbox imports.

So the week-old claim "torch-directml does not carry models of this shape" now
has an error message under it, and the real reason is duller and more final: a
**version deadlock**, not a capability gap. Two packages with incompatible pins
need two environments, or one of them needs not to be there.

**It costs nothing that mattered.** Route B was never shippable — it drags
Python and a multi-gigabyte checkpoint into the build — and existed only to buy
a speed number early. **ONNX Runtime on DirectML uses no torch at run time at
all**: torch is needed once, on our machine, to EXPORT, and a CPU is fine for
that. `onnxruntime-directml` has no torch dependency in either direction.

**And it fixes the ordering.** Ask whether DirectML can see a GPU and run a
model BEFORE asking anything about chatterbox — it needs no torch, takes
seconds, and it is what decides whether the export is worth attempting. The
probe asked in the wrong order and nearly buried a yes under two unrelated
noes.

### 1g-bis. THE BENCHMARK ASKED THE WRONG QUESTION FOR LIVE DIALOGUE (5 Aug)

Jafar, asked which AMD card he has: *"does it matter? it should work for any
gamer with a half-decent AMD or NVIDIA card."*

It does not, and the question was wrong. The benchmark below chose an engine by
QUALITY ON A DEV BOX. For the offline bark bank that is right and the choice
stands. For live dialogue it is not a criterion at all, because that code runs
on a stranger's machine — so the requirement is **vendor-neutral, on a
mid-range gamer GPU, shipped inside a Unity build**, and nothing below was ever
measured against it.

**What that rules out:** ROCm under WSL2 (AMD-only, recent cards only, and it
asks a player to install a Linux subsystem to hear a voice — a dev-machine
answer, never a ship path). And PyTorch itself, probably: shipping a Python
runtime plus torch plus a multi-gigabyte checkpoint inside a game is a
distribution problem larger than the feature.

**What survives:** ONNX Runtime with the DirectML execution provider. DirectX
12 compute, so AMD, NVIDIA and Intel alike; ships as a DLL; callable from C#,
so it can live inside Unity with no Python anywhere.

**The open question is therefore not "does chatterbox run on AMD".** It is
whether this model can be exported to ONNX at all, and how fast it is under
DirectML — and chatterbox is a hard case: a Llama-derived backbone, a flow
decoder and a watermarker, none of which export cleanly by default.

**And it re-opens the two-engine decision at §1j**, honestly rather than by
forgetting it. That was decided about CROWD MURMUR, where one engine plainly
sufficed. Offline quality and live latency are different constraints on
different hardware, and the engine that ships to a player may not be the one
that renders our bank overnight. Chatterbox stays for the bank either way.

### 1g. THE TEST MACHINE IS AMD, AND THAT SPLITS THE DECISION IN TWO

Jafar's card is AMD. **PyTorch has no Windows AMD backend** — ROCm is Linux
only, and torch-directml does not carry models of this shape — so every
local engine in this benchmark runs on his CPU. That is not a
misconfiguration and there is nothing to fix; the earlier reading of
"gpu: none detected" as a PATH problem was wrong.

It matters much less than it first appears, because it lands on the two
channels differently:

| Channel | Runs when | AMD/CPU verdict |
|---|---|---|
| **Barks, ambience, recognition, refusals** | Offline, once, on our machine | **Unaffected.** A batch that takes a night is still a batch that takes a night. Quality is the only criterion |
| **Named-cast live dialogue** | At play time, on the player's machine | Ruled out on THIS machine. Kokoro at 0.33 RTF is the exception and the reason it stays in the running |

So the slow engines are not disqualified by this — they are disqualified
from *live* use *here*. What ships to players depends on the player's card,
not on the development box, and the tiered shape in §1a was already built
around exactly that split.

The practical consequence is only patience: chatterbox and xtts will take
minutes per engine on CPU rather than seconds. The benchmark now names the
card, explains why it cannot help, and says so before the wait rather than
after.

### 1h. BENCHMARK RESULT #3 — chatterbox clears the bar

Jafar, on the first engine to produce audio he did not immediately reject:

> "chatterbox sounds pretty good"

That is the first time anything in this benchmark has cleared the floor
piper set. Everything before it was either the floor itself or a failure to
launch.

| engine | verdict | median RTF (CPU) | takes direction |
|---|---|---|---|
| **chatterbox** | **"sounds pretty good"** | **~5.9** | yes — exaggeration control |
| kokoro | usable, uninteresting | 0.34 | no |
| piper | the floor: "very obviously synthetic" | 0.05 | no |
| xtts | still has not run | — | via reference clips |

**Its speed number was reported as 326711 and that was my bug, not the
engine's.** chatterbox returns a torch tensor shaped `(1, N)` — one channel,
N samples — and `len()` on that is 1. So every clip was recorded as 0.0
seconds long. The audio was always fine; only the ruler was broken. The real
figure, recomputed from the generation times against the same lines' known
durations, is **about 5.9 on CPU**.

This is the most dangerous class of bug this benchmark can have: it does not
look like a broken measurement, it looks like a catastrophic result, and it
would have disqualified the only engine that has passed a listening test.
The bench now measures the last axis and refuses outright to print a
real-time factor above 500, because no engine is five hundred times slower
than real time and printing the number invites someone to act on it.

**What ~6 RTF means for us, given §1g:** offline only on this machine, which
is exactly the channel chatterbox is wanted for. A 3,000-line bark bank at
~3 seconds a line is about five hours of generation — one overnight run,
once. It does not touch live dialogue, and on an NVIDIA card it would be
roughly ten times faster anyway.

### 1i. DECIDED — chatterbox, on the strength of the direction test

Jafar's listening verdicts on chatterbox, 2026-07-28:

| test | verdict |
|---|---|
| **direction — BORED vs GRAVE** | **"different with chatterbox"** |
| emphasis — "That's **your** problem" | "slightly emphasized" |
| consistency — ten lines, one character | **"was, alive"** |
| the voice itself | "don't like the actual voice" |

**The engine question is closed.** Direction was the criterion, for the
reason argued in §1d, and three engines failed it identically while one
passed. Chatterbox also passed the consistency test in the way that matters:
piper was *uniform*, chatterbox was **alive**. Emphasis landing "slightly"
is a partial pass and still strictly more than the zero everything else
scored.

**Not liking the voice is not an engine problem, and the fix is better than
choosing from a menu: we do not pick a voice, we define one.** Chatterbox
clones from ~10 seconds of reference audio, so whatever we record becomes
Lena. The mood-reference mechanism from §1f then does double duty — the same
clips carry the casting AND the direction, because `lena.grave.wav` is both
"this is who she is" and "this is how she sounds when it matters".

Where those clips come from is a decision for Jafar and is queued in
`decisions-pending.md`, with a recommendation to record our own rather than
clone a public-domain reader: PD settles copyright and does not settle
consent, and a volunteer who read a novel aloud did not agree to become a
character in a crime game.

**XTTS is moot.** Its unique value was cloning; chatterbox clones too. The
dependency fix is committed, but running it now would buy a comparison
rather than a decision.

**The shape that follows from all this:**

| Channel | Engine | Why |
|---|---|---|
| Barks, ambience, recognition, refusals | **chatterbox, offline** | Directable, alive, ~6 RTF is irrelevant for a one-time batch |
| Crowd murmur | **chatterbox, offline** | See below — kokoro is dropped |
| Named-cast free dialogue | **open** | Decide after the bark bank exists and we know how far cloned voices carry |

### 1j. KOKORO IS DROPPED (2026-07-28)

> *"why are we using kokoro? will it be better than what we generated now,
> because that sounds like shit"* — Jafar

He is right and the answer is that we should not be. Kokoro was kept for one
job: live crowd murmur, on the strength of 0.34 RTF on a CPU with no GPU.
That justification does not survive contact with two facts.

**The murmur does not need to be live.** Crowd ambience is finite and
repetitive — it is the most pre-generatable speech in the game. It was only
ever a candidate for live generation because kokoro happened to be fast
enough, which is choosing the work to fit the tool.

**And a second engine costs more than it looks.** Two engines means two
voice identities, two sets of artefacts, two quality ceilings — and the
crowd would audibly not belong to the same world as the cast. One engine for
all pre-generated speech is not a compromise, it is the better result.

Chatterbox generates the crowd barks in the same overnight batch as
everything else. **One engine. Dropped, not deferred.** If
none does, the fallback is not "pay more" — it is to buy direction
structurally: generate 2–3 takes per line and pick, use distinct voices per
emotional register, and lean on the distance filtering and occlusion already
built in `Core/Acoustics.cs` to hide the seams.

---

## 2. Character models + animation — "ok, how?"

Four routes, with my recommendation.

| Route | What | Cost | Verdict |
|---|---|---|---|
| **A. Modular stylised** (Synty-class) | Mix-and-match heads/bodies/clothes, low-poly, distinctive | ~$50–200 | **RECOMMENDED** if art direction is stylised |
| **B. Character Creator 4 pipeline** | Reallusion CC4 generates unlimited realistic humans, auto-rigged, Unity export | ~$300–600 | Best if realism-lite; heavier pipeline |
| **C. MetaHuman** | Epic, photoreal, free | $0 | **Effectively out** — Unreal-first, Unity path is painful and licence-restricted |
| **D. Commission bespoke** | An artist makes our cast | $2–10k+ | Later, for the ten named cast only, if the project proves itself |

**Animation is separate from models and is where the feel lives:**
- **Mixamo** — free mocap library (idle, walk, run, talk, gesture, sit).
  Good enough for everything except the cast's key scenes.
- **Unity Animation Rigging package** — free, and this is the one that
  matters: **look-at IK** makes the gaze system I just built actually
  read. Without it, "they turn to watch you" is a rotating capsule.
- **A locomotion controller** with proper blend trees (~$50–100 on the
  asset store, or hand-built) — no snapping between idle/walk/run.
- **Occupation loops** — the market seller actually selling. This is what
  KCD2 does that reads as "alive," and it's animation work, not AI work.

**Recommended stack: modular stylised characters + Mixamo + Animation
Rigging (look-at) + a blend-tree locomotion controller.** Roughly $150–300
and a lot of my integration time.

---

## 3. Barks at quality

**Not runtime generation. Offline generation into a curated bank.**

Pipeline:
1. Enumerate the real situations the simulation produces (rumour of kind X
   at confidence Y told by archetype Z; refusal; recognition; ambient
   topic per economic state).
2. Generate many candidates per situation with the LLM, given the
   character archetype and emotional state as direction.
3. **Curate.** A human pass keeping the good ones — this is the step that
   separates "AI slop" from writing, and it is not optional.
4. Voice the survivors with the premium model, offline.
5. Ship as audio + text. Zero runtime cost, unlimited quality headroom.

Target: **~2,000–5,000 lines**, versus the ~40 hand-written templates in
today's build (which will start repeating within minutes — that is a real
defect in what I shipped this morning, and this is its fix).

---

## 4. Art direction — elaborate and suggest

### The strategic frame
Competing with KCD2 on realism is a losing game: they have an art army and
we do not, and realism is the one lane where a small budget guarantees we
look cheap. Disco Elysium, Pentiment and Obra Dinn are deeply immersive on
small budgets because their style is coherent, distinctive, and
*achievable*.

### Four candidates

**A. STYLISED NOIR — RECOMMENDED.**
Period-plausible forms, heavily restricted palette, strong directional
light. Faces simplified but expressive; silhouette-first design (hats,
coats, distinctive shapes) so characters read at distance — which is
exactly what the gaze/stance system needs.
- Palette: desaturated blue-greys and wet stone, punctured by warm sodium
  pools from streetlamps and bar windows.
- **Weather and fog do the heavy lifting.** Volumetric fog, rain, steam
  from gratings: they cut draw distance (a performance win), hide
  low-detail geometry (a budget win), and create mood (an art win). This
  is the single highest-leverage art decision available to us.
- Post: film grain, vignette, slight bloom on light sources.
- Reference: the street level of *Blade Runner*, the palette of *Road to
  Perdition*, the character read of *Disco Elysium*.
- **Why it fits THIS game:** it is a game about perception, rumour and
  what people think they saw. A subjective, high-contrast, half-obscured
  world is thematically correct, not just cheap.

**B. Interwar realism-lite.** Period-accurate, simplified materials.
Honest but lands in the uncanny valley and costs the most. Not recommended.

**C. Hard graphic / extreme stylisation** (1-bit, heavy dither, à la Obra
Dinn). Cheapest and most distinctive, but fights the game's need for
readable faces and subtle social signals. Not recommended, though a
striking option if budget collapses.

**D. Diorama / tilt-shift.** Wrong — it distances the player, and this game
needs intimacy.

### If A is chosen, the concrete first pass
1. Lighting and fog rebuild (free, biggest single visual gain). **DONE.**
2. Wet-surface materials + reflections (cheap, high production value). **DONE.**
3. Rain and its audio (cheap, transformative). **DONE 2026-07-28** — the
   first art commit shipped rain you could see and not hear, which is worse
   than no rain: the eye and the ear disagree and the ear wins.
4. Restricted palette enforced across every existing material. **DONE
   2026-07-28** — and it was genuinely missing. The lighting had been moved
   to noir and the materials left exactly where they started, which is why
   the world read as generically grey rather than as a chosen palette. All
   nine surfaces now pull toward blue-grey and darker, verified rather than
   eyeballed: 9/9 cooled or neutralised, 9/9 darkened. Contrast is a
   RELATIONSHIP — warm lamps against warm walls is not contrast, so the
   walls had to give.
5. Modular period building/prop packs consistent with the palette. **NOT
   DONE, and on hold** — the character direction moved toward semi-realistic
   (Mixamo) on 2026-07-28, and stylised low-poly buildings would clash with
   that. Buying environment art before the character look is settled would
   be paying for a mismatch.

Still outstanding from §4's own list: **film grain, vignette, and bloom on
light sources.** Named in the art direction and not built.

---

## 5. Game feel — what I mean

The moment-to-moment tactile response. The difference between a character
who *moves* and one who *teleports smoothly*. Concretely, what LEDGER lacks:

- **Movement weight** — acceleration and deceleration curves rather than
  instant velocity; a turn that takes a moment.
- **Animation blending** — no snapping between idle/walk/run.
- **Camera craft** — subtle sway, slight positional lag, FOV widening when
  running, a small settle when you stop.
- **Footsteps by surface** — stone, wood, gravel, puddle, with variation
  so it never sounds looped.
- **Interaction feedback** — a door that has a handle sound, an animation,
  and a tiny camera nudge; money that has a weight to it.
- **Breath and effort** when running; a different gait when hurt (we
  already model injury — it should be visible in the walk).
- **Continuous time-of-day** light transitions rather than steps.
- **UI sound** with a consistent material identity.

None of it is expensive. All of it is what people mean when they say a game
feels "finished" versus "a prototype."

---

## 6. Budget estimate

**Upfront, one-time (asset purchases):**

| Item | Low | High | Note |
|---|---|---|---|
| Characters (modular stylised) | $50 | $200 | Route A |
| — or Character Creator 4 pipeline | $300 | $600 | Route B instead |
| Locomotion controller | $0 | $100 | Hand-buildable |
| Animations (Mixamo) | $0 | $0 | Free |
| Environment: buildings/props packs | $150 | $700 | Period-consistent |
| Audio: ambience + SFX libraries | $50 | $300 | |
| Bark voice generation (one-time, ~3k lines) | $30 | $120 | ~180k chars |
| **Upfront total (Route A)** | **~$280** | **~$1,420** | |
| **Upfront total (Route B)** | **~$530** | **~$1,820** | |

**Recurring, per hour of play:**

| Item | Cost/hour | Note |
|---|---|---|
| LLM dialogue | <$0.05 | existing target, already measured by CostTracker |
| TTS — premium streaming | $3–5 | **unshippable commercially** |
| TTS — commodity streaming | ~$0.25 | viable |
| TTS — local model | $0 | + GPU requirement, install size |

**Optional / later:**
- Bespoke character art for the ten named cast: $2,000–10,000+
- Original music: $0 (we have procedural) to $2,000+
- Professional sound design pass: $1,000+

**Headline: roughly $300–1,500 gets us models, animation, environment art,
audio libraries and a fully voiced bark bank.** The recurring TTS cost for
live dialogue is the real strategic decision, and it points hard at a local
model or a tiered approach.

### REVISED 2026-07-28 — THIS SUPERSEDES THE TABLE ABOVE

Jafar: *"budget is definitely too much. how far can we get with 100–200?"*
Answer: most of the way, if we buy only what cannot be built or found free.
Every number above this line is the unconstrained estimate and is kept only
so the trade-offs stay visible. **The binding plan is this one.**

| Item | Low | High | How it got cheap |
|---|---|---|---|
| Characters — modular stylised, on sale | $30 | $80 | Synty-class packs are ~70% off several times a year; wait for one |
| Locomotion controller | $0 | $0 | Hand-built on the momentum already in `Core/Feel.cs` |
| Animations — Mixamo | $0 | $0 | Free |
| Look-at IK — Unity Animation Rigging | $0 | $0 | Free package, and the one that makes the gaze system read |
| Environment / props | $0 | $40 | Kenney + Poly Haven CC0 first; buy only what is missing |
| Audio libraries | $0 | $25 | freesound + we already synthesise most of it |
| Bark voice generation, one-time | $40 | $120 | Or **$0** on a local engine — the benchmark decides this |
| **Revised total** | **~$70** | **~$265** | |

Two things to hold onto when reading any figure in this document:

1. **Scope must be stated with the number.** The ~$150–300 in §2 is the
   character-and-animation stack ALONE, written before this revision. The
   ~$70–265 here is EVERYTHING. Quoting one against the other is comparing
   a part to the whole, and I have already done that once.
2. **The bark line is the only genuinely uncertain one**, and it collapses
   to zero if a local engine clears the quality bar. That is what the TTS
   benchmark is for.

**The honest caveat:** buying assets does not make a game look coherent.
Art direction and integration do, and that is my time, not money. The
budget above is the cheap half of the problem.

---

## 7. What I need from Jafar to proceed

1. **Answers to the six voice questions in §1c** — especially setting/accent
   and shipping model.
2. **Art direction: confirm A (stylised noir) or pick another.**
3. **A budget ceiling**, so I can spec exact products rather than ranges.
4. **Character route A or B** (follows from art direction).

With those four, I can produce a specific shopping list with named products
and current prices for approval, and start on the free work immediately —
lighting/fog/palette, game feel, look-at rigging, and the offline bark
generation pipeline, none of which need a purchase.


---

## §2b. THE BARK BANK — steps 1 and 2, BUILT 2026-07-28

### Step 1: enumeration, and why it is a program rather than a document

**The list of things this street can say is not a design document. It is a
property of the code.** `Core/StreetVoice.cs` branches on real state, and
every branch it can reach is a slot that needs lines. A hand-written list of
those slots is wrong the day somebody adds a branch.

So `ledger/BarkGen` walks the actual state space — every combination of
confidence, nerve, loyalty, greed, suspicion, leash, coat, hour, prosperity,
price level, injury and feud — drives the real `StreetVoice` functions with
it, and reports what came out. `dotnet run --project BarkGen` writes
`game-design/barks.json`.

Three things fell out of that which a written list could not have given.

**1. The repetition figure, which was damning.** Not "does this slot have
lines" but *how many seconds of play before the player hears one twice*,
computed from the schedulers that actually speak them. Every slot in the
game repeated inside ninety seconds. The ambient family — the one a player
hears most, one exchange every thirteen seconds on a busy street — repeated
inside **twenty-six**.

**2. Reachability.** No stance on the ladder turned out to be unreachable,
which is worth knowing and was not knowable before.

**3. The pairing bug, which no line count could see.** Openers and replies
were chosen with `seed` and `seed + 1` from banks of equal length, so
opener[i] was *always* followed by reply[i+1]. Fourteen banks of fourteen
produced **fourteen fixed conversations, not a hundred and ninety-six**, and
writing more lines would never have changed it.

That third one is the argument for having built the enumerator *before*
writing the lines. It also caught my first two attempts at fixing it:
`seed * 7 + 3` was **worse** than the bug (seven divides fourteen, so the
replies collapsed to two), and `seed * 97` was no better (both indices were
functions of one number, and a bijection is a bijection however prime you
make it). The actual fix is a second independent input, and there was an
obvious one sitting there: **the person answering.** The same remark now
gets a different answer from a different neighbour, which is what it should
have been doing all along. Hashed with FNV-1a rather than
`string.GetHashCode`, which is randomised per process on .NET Core and would
have made the same save produce different conversations on every launch.

### Step 2: generation

Banks taken from 2–4 lines to **fourteen per slot**, 24 slots. 58 lines →
420, and 126+ distinct *conversations* per band rather than 14.

The writing rule for the ambient family, which is most of it: **deliberately
ordinary.** Nothing in `Ambient` is about the player, and the moment a line
reaches for interest it stops being a city and starts being a stage set with
something to tell you. Weather, a wound that will not heal, the landlord,
Thursday.

Fourteen is a cap rather than a target. Past that the answer is to vary the
*state* that picks the band, not to write a fifteenth way of saying "cold
one" — and BarkGen now reports a slot at its cap as done rather than
flagging it forever, because a warning that never clears trains people to
ignore it.

### Step 3: curation — JAFAR'S

Read `game-design/barks.json` (or just the banks in `StreetVoice.cs`). Cut
anything that sounds like a video game. The bar is whether you could hear it
through a wall on a real street and not notice it was written.

Voicing waits on the reference clips (`tools/voice-fetch/`), and at ~6 RTF
on this hardware the whole bank is one overnight run.


## 17.2 scope — what "generate the cast voices" actually costs

Measured 2026-08-01 from `game-design/barks.json` and `Core/VoiceBank`, because
the milestone said "low risk" and the arithmetic says otherwise.

    bark lines                     2,604
    DISTINCT strings               2,604   (no duplicates to collapse)
    mean length                    97 chars, median 103, max 167
    x 6 crowd pool voices         15,624 clips   1.52M characters
    x all 19 cast voices          49,476 clips

`VoiceBank.ClipName` keys a recording by (voice, normalised text), so distinct
text is exactly what has to be synthesised — there is no dedup left to find.

**Why this is a decision and not a task.** A voice-cloning model on a CPU
runner is the dominating cost and nobody has measured its rate here. Even at an
optimistic ten seconds a clip, the crowd bank alone is ~43 hours of runner time
— eight of GitHub's six-hour jobs — for audio the game then deliberately
destroys: `Acoustics.AsHeard` drops words by distance and noise, and the
committed night still shows a bark arriving as *"The ... old ....thi.e...told,
... there."*

**The options.**

1. **Principals voiced, crowd barks stay text.** Cheapest by orders of
   magnitude and costs nothing the player can hear clearly. The crowd keeps its
   six pool voices for the lines that matter — greetings, reactions, the ones
   spoken at conversational range.
2. **Generate the full crowd bank** across many dispatched runs. Honest, slow,
   and the result is mostly inaudible.
3. **Generate the loudest slots only.** The 42 slots are not equal: `AS YOU
   PASS` and `OVERHEARD` are heard at range, `DISTINCT CONVERSATIONS` (2,268 of
   the 2,604 lines) is the pair-generated bulk.

**Recommended: 1, then 3 for the slots a player stands closest to.**

**First step under any option:** a dispatched run that generates twenty clips
and reports seconds-per-clip. Every number above except the rate is measured;
the rate is the one that decides the schedule, and estimating it is exactly the
mistake rule 7 names. Do not build the full pipeline before that run.
