# The testing system — research, plan, build

> **STATUS — SPEC.** The design for how LEDGER is tested. Stable reference:
> build state lives in `roadmap.md`, not here. A spec that disagrees with the
> roadmap is out of date about what got built, not about what was intended.

Jafar, 2026-07-31: *"we also need to think about an ultra advanced testing
system. research and think about how AAA studios go about testing then plan,
build. then apply the system across every aspect of the game — when I tell you
to."*

**Applying it across the game is gated on his word.** This document is the
research, the plan, and the order of build.

---

## 1. What large studios actually do

Nine practices, and what each is really for. The interesting part is that
several of them exist to catch a class of bug that unit tests structurally
cannot.

**1. The pyramid, adapted.** Unit → integration → smoke-on-every-platform.
Games add a **boot test**: does the shipping build reach the main menu on each
target, every night. Cheap, and catches the whole family of "it works in the
editor".

**2. Automated playtest agents.** Ubisoft La Forge, EA SEED and others run
bots — scripted, then reinforcement-learned — that play for thousands of hours
looking for softlocks, out-of-bounds, and unreachable objectives. The value is
not that a bot plays well; it is that a bot plays *strangely*, and strange is
where the bugs are.

**3. Visual regression.** Golden screenshots per scene, compared perceptually
each build. This is how a studio catches "somebody changed a shader and every
night scene is now purple" — a class of defect that no assertion about code
will ever find.

**4. Performance as a tracked series.** Not "is this frame under 16ms" but
"is the p95 frame time worse than last week". Budgets per scene, trended, with
the commit that moved them attributable.

**5. Determinism and replay.** Record inputs, replay, assert the same end
state. In a simulation game this is the strongest test that exists: it turns
"the sim is stable" from an opinion into a check. It is also the foundation of
usable bug reports — a seed and an input log reproduces anything.

**6. Soak and chaos.** Run for hours. Save and load at every boundary. Inject
random events. Catches leaks, unbounded growth, and state that only corrupts
on the ninth day.

**7. Content validation.** Assets, references, localisation keys, dialogue
graphs — linted like code. Cheap, and the failure mode is a shipped game with a
missing string.

**8. Crash and error aggregation.** Symbolicated, deduplicated, ranked by
frequency across every run and every tester.

**9. Structured human QA.** A test matrix, severity triage, and repro steps.
Machines cannot judge feel, and feel is the thing this project says it is
selling.

## 2. Where LEDGER already stands

Unusually well, and it is worth being precise about why rather than modest.

| | what | scale |
|---|---|---|
| Unit / logic | `CoreTests` | **2,884 checks** |
| **Mutation testing** | `breakrun.py` + `breaks/*.json` | **21 specs** — reintroduce a defect, prove the test goes red |
| In-engine sim gates | `SimDirector` | **20 gated claims** over an 11-day run |
| AI playtest | `SimHarness` | LLM player vs LLM judge against a real character brain |
| Monte-Carlo balance | `BalanceLab` | 300–400 seeded campaigns per question |
| Content enumeration | `BarkGen` | walks the state space and measures repeat intervals |
| Shape / lint | `ShapeCheck`, `lint-usings.py` | 128 files, reference-independent |
| Docs | `docs-check.py` | 45 docs, LIVE/SPEC/LOG enforced |
| Deliverable | `page_check.py` | drives the listening page in a real browser |

**Mutation testing is the standout.** Most studios do not do it. "The test
suite is green" means nothing until something proves the tests would notice a
defect, and `breakrun.py` is that proof — it has already caught a check that
passed on one lucky seed and two anchors that had stopped being exercised.

## 3. The gaps, ranked by what they would have caught today

Not a wishlist. Each of these maps to a real defect from this week.

| # | gap | the incident it would have caught |
|---|---|---|
| 1 | **No call-site coverage gate** | ~40 Core APIs with no caller. `Brandish` 0, `MayFrisk` 0, `Misattribute` 0 — Phases 2–4 built, tested and disconnected |
| 2 | **No visual regression** | the caption bar, the noise ring, and any shader change; screenshots are gated on *aggregate luma*, not on the image |
| 3 | **No determinism / replay** | nothing reproduces a sim failure except re-running it and hoping |
| 4 | **No soak run** | eleven days is the longest anything has ever run; day 40 is unexplored |
| 5 | **No performance trend** | frame budgets are per-run, so a slow drift is invisible until it is a cliff |
| 6 | **No text-shape assertions** | 21 of 42 gossip templates rendered a lowercase sentence for weeks with 2,883 tests green |
| 7 | **No fuzzing of free text** | the intent router takes arbitrary player input and nothing hostile has ever been thrown at it |
| 8 | **No save/load fuzz** | round-trip is tested at chosen points, not at arbitrary ones |
| 9 | **No crash aggregation** | a run's errors die with the run |

## 4. The system — five layers, in build order

Named layers so a gate can say which one it belongs to.

### Layer 1 — REACH: does the code run at all *(build first)*

**`tools/reach-check.py`.** Enumerate every public API in `Core`, count call
sites in `Game`, and fail on anything with zero. An allowlist with a written
reason per entry, because some APIs legitimately serve tests or a future
phase — but the reason has to be typed, which is the point.

This is the gap analysis I ran by hand today, automated. It is first because
it catches the project's oldest and most repeated failure — *built is not
running* — and because it costs nothing to run.

**Done when:** the check runs in CI, the current ~40 unwired APIs are either
wired or allowlisted with reasons, and the number can only go down.

### Layer 2 — SHAPE: is the output well-formed

Assertions about the *form* of what the game produces, not its logic.

- **Text:** every generated line starts sentences with a capital, has no double
  spaces, no unresolved `{placeholder}`, no orphaned punctuation. The
  capitalisation bug lived for weeks under 2,883 passing tests.
- **Audio:** every installed clip has plausible duration, sample rate, and is
  not silence.
- **Assets:** every referenced file exists; every cast id maps to a real
  character; every bark slot meets its repeat floor.

**Done when:** a malformed line cannot reach a build, and `breakrun` proves it.

### Layer 3 — PIXELS: does it still look like itself

**Golden-frame regression.** The sim already takes noon and night screenshots
on a fixed seed. Store them as goldens; compare each run perceptually; fail on
drift beyond a threshold **derived from a measured series, not invented**.

Deliberately not pixel-exact — a software rasteriser is not deterministic
enough for that, and a check that flaps gets switched off. Perceptual distance,
with the series printed so the threshold has evidence behind it.

**Done when:** changing a shader constant fails the build with the diff
attached as an artifact.

### Layer 4 — TIME: does it survive being played

- **Determinism and replay.** A seed plus an input log reproduces a run
  exactly. Then every bug becomes a file, and `BalanceLab`'s 400 campaigns
  become 400 reproducible cases rather than 400 statistics.
- **Soak.** 100 in-game days, weekly. Assert nothing grows without bound:
  rumours, memories, deliveries in flight, allocated objects.
- **Save/load chaos.** Save and reload at a random tick, N times, and assert
  the world is identical afterwards. This is where a simulation with 3,000
  residents will break, and it will break quietly.
- **Performance as a series.** p50 and p95 frame time committed per run, so a
  regression is a graph rather than a surprise.

**Done when:** a 100-day run is green weekly and a bug can be handed over as a
seed plus a log.

### Layer 5 — ADVERSARY: what a hostile player does

- **Intent fuzzing.** Throw junk, injection attempts, 10,000-character strings
  and other languages at the router and the response validator. Nothing may
  crash, and nothing may put an unvalidated model response on screen.
- **Bot that plays badly.** The sim bot walks fixed errands. A bot that does
  the *wrong* thing — stands in doorways, talks to the same person forty times,
  commits the same crime nine days running — is where softlocks live.
- **Economy exploit search.** `BalanceLab` already runs hundreds of campaigns;
  point it at *finding the dominant strategy* rather than at confirming balance.
  If one exists, it is a design bug and better found by a machine.

**Done when:** the game cannot be crashed from the keyboard, and no strategy
dominates across 400 seeded campaigns.

## 5. What this is deliberately not

- **Not a coverage percentage.** Line coverage measures which lines ran, not
  whether anything would notice them being wrong. `breakrun.py` already answers
  the better question.
- **Not more assertions on things already asserted.** Every layer above exists
  because it catches a class the others structurally cannot.
- **Not a replacement for playing it.** Machines cannot judge feel, and feel is
  what this project says it sells. `qa-matrix.md` stays.

## 6. Build order and cost

| | layer | cost | why this order |
|---|---|---|---|
| 1 | **Reach** | hours | catches the oldest failure; needs no new infrastructure |
| 2 | **Shape** | hours | the capitalisation class; cheap and immediate |
| 3 | **Pixels** | a day | needs goldens committed and a measured threshold |
| 4 | **Time** | days | determinism is the big one and it touches the sim's spine |
| 5 | **Adversary** | days | most valuable once there is a game to attack |

Layers 1 and 2 are worth building **before** M16 Phases 3 and 4 land, because
they are exactly the checks that would have caught what Phases 2–4 did wrong.
Layers 3–5 belong after M17, when there is something worth photographing and
something worth attacking.
