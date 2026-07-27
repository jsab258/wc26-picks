# Audit brief — for the 14:00 CEST session

Jafar's plan: **full audit and test → fix → one more build → playtest.**
This is the scope, so that session starts auditing instead of orienting.

---

## The state in one paragraph

All three acts are wired and run end to end. Three districts exist. The
endgame resolves off world state and its distribution has been measured.
CoreTests 1395, SimHarness 71, lint and ShapeCheck clean.

**As of run 30259492282 the open city is genuinely covered — `coverageOk=True`
for the first time.** That run reached this, none of which any previous build
had ever executed:

    coverageOk=True openModeForced=True daysSkipped=2 endDay=12
    directorFired=True opsOk=True planRan=True witnessCarOk=True
    vehicleFact=True actThree=True opened=True ending=Kingdom

    ACT III: audit closed day 8 — Kingdom
             (strain 0.56, heat 0.95, life 0.80, owned 1, rackets 2)

The Director fired, an operation went all the way through the real planning
path, a witness described the car, and **the endgame resolved to a real
ending in-engine for the first time in the project's history.**

It is still not a green BUILD: one gate failed, `actTwoMissed=[pp6]`, which
was a race in the gate rather than a fault in the game (see below). The fix
is pushed and building as run 3 of the morning. **If that run is green, the
audit inherits a genuinely covered build; if it is not, read what it names —
everything else in this file still holds.**

---

## What is DONE and verified

**Read the right-hand column literally.** After this morning, "there is a gate
for it" and "the gate has run" are known to be different claims, so they are
written differently here.

| | verified how |
|---|---|
| Act I — the week, seven pressure points | sim gate `actOne`, **observed passing** |
| Act II — seven pressure points | sim gate `actTwo`, **observed passing** (`actTwoOk=True`, none missed) |
| Act III — audit, inspector, last day, five endings | CoreTests + balance lab + **in-engine, run 30259492282: opened, audit closed day 8, `ending=Kingdom`.** First execution ever |
| Three districts (Hook, Copper Row, Ironside) | CoreTests geography + population, **observed** (`npcs=42`, `pop=3000`) |
| Traffic, signals, vehicles | CoreTests + sim gates, **observed** (14 vehicles, 11.7km driven, 0 off-road) |
| The car as a witness fact | CoreTests real; sim gate was **asking the wrong question** until this morning, now **observed** (`vehicleFact=True`) |
| Phones (M10), harm (M11), purses (M13) | CoreTests + sim gates, **observed passing** |
| Front end (menu, options, pause, rebinding) | UI smoke test, **observed** (`panelsBad=0`) |
| Save/load of everything above | codec round-trips, in-engine overlay |

| The Director (M8) | **observed, run 30259492282** (`directorFired=True`) — first execution ever |
| Operations planning (M7.5) | **observed, run 30259492282** (`planRan=True`) — first execution ever |

The last three rows are new as of this morning. Until run 30259492282 their
gates had never executed once; see the finding below for why.

## What is DONE but NOT felt

**Nobody has played the endgame.** Act III is measured, not experienced. The
ending distribution is in `balance-findings-endings.md`; whether the six days
have the right *shape* is a question only playing answers. Same for Act II's
pacing — the seven fire correctly and nobody has watched them space out.

**One thing to look for specifically when you do play it.** Re-reading the
whole ending matrix after decision 10 turned up something nobody had noticed:
**the inspector is completely inert for a player who never built an empire.**
Four different ways of handling six days of Tobias Reisz, and the Control
plan's outcome is 49.8 / 50.3 in every one of them. The strain he sees moves
properly and then changes nothing, because with no empire there is no Kingdom
and no Both to reach.

Defensible — nothing to inspect, nothing to find — but it means one of three
playstyles experiences the act's central verb as scenery. **Whether inert
reads as peaceful or as pointless is exactly a playtest question**, which is
why it is written up in `balance-findings-endings.md` with three options and
no change made. Do not fix it from the lab.

## What is PENDING

**One item: a green in-engine build that proves it covered the open city.**
Nothing else is waiting on a decision.

Decisions #9 and #10 were answered by Jafar this morning and both are built —
see the bottom of this file for what changed and what it measured.

Deferred by decision, not blocked: districts 4-7, melee, HDRP/city pack/voice,
LLM cost model.

---

## The honest part — read this before auditing anything

Today's most useful finding was not a feature. **A build passed having tested
almost none of the game**: the sim bot lost the week on day six, so the open
city never opened, so every gate guarding itself on `OpenMode` passed *on its
own precondition being false* — empire, Director, operations, Act II, Act III.
Nine simulated days, the entire second half skipped, CI green.

Four more of the same shape were found by looking for it:

- `perfOk` passed when the profiler had recorded **nothing at all**
- the traffic following-distance check passed its own "never measured" sentinel
- 24 endgame tests passed **unchanged** after a gate went in, because their
  fixtures had no racket income and could not exercise it
- `dayJobOk` had never once been evaluated

The rule that came out of it, now in `roadmap.md`: **a conditional check is
worth its green tick only if something asserts the condition was reached.**

**So the audit's first question should not be "do the tests pass".** It should
be "what do they pass *on*". Three tools now exist for that:

1. `coverageOk` — fails the build if a nine-day run skipped the open city.
2. `FAILING GATES: a, b, c` — the sim names its own failures instead of
   hiding them in a thirty-term `&&`. Read it with the `get_job_logs` call at
   the top of this file, or in the Actions web UI. Both work; only the wrong
   API call ever made this look hard.
3. The "does anything actually read this" pattern. Applied so far to:
   `LedgerState` (every field must be able to change the ending — found the
   collapsed life axis), three closed vocabularies (`Checks`, `Effects`,
   `Pressures` — each must have a handler), and every money modifier
   (`Economy.FactorFor`'s inputs, and the empire's `NewCrewTaxing`,
   `TributeShare`, `SharedRacketId` and crew cut).

   The sweep is now **finished**: five closed lists — `Checks`, `Effects`,
   `Pressures`, `KeyKind`, `Approach` — plus `LedgerState`'s fields and every
   money modifier. **Four of the five vocabularies came back clean.** One did
   not: two of the ten door-key kinds had no doorman line, so the two doors
   where the clock IS the point got a flat "lets you past" while a bribe, a
   hook and a reputation each got a sentence.

   That is the proportionate result and it is stated that way on purpose —
   most of these tests stop the next bug rather than having caught one. Do not
   invent further sweeps for their own sake.

   The one gap that was pinned rather than fixed — the rackets reading
   `IncomePerDay` flat, so a starved district paid the same round as a rich
   one — is **closed**: Jafar answered decision 9 with "couple it" and the
   test was flipped from asserting the old behaviour to demanding the new.

## HOW TO READ THE VERDICT — solved, and it was never a plumbing problem

```
mcp__github__get_job_logs(run_id=<id>, failed_only=true,
                          return_content=true, tail_lines=200)
```

That returns the whole `SimDirector: done.` line and the `FAILING GATES`
list intact. **Use `failed_only=true` with `run_id`. Do not use `job_id`** —
the per-job call is the one that returns a ~4KB tail, and it is what made
this look impossible for most of a morning.

Five builds went on moving the print statement around: end of the sim step, a
final step, artifacts (egress 403, a real policy denial), `GITHUB_STEP_SUMMARY`
via `check_run.output` (verified empty for Actions jobs), then log-noise
reduction. All of it was unnecessary. The verdict was in the log the whole
time and the call was wrong. Two lessons, and the second is the one that
generalises: when a channel looks blocked, re-check the *retrieval* before
rebuilding the *sender* — and a browser was always the trivial fallback.

`persist-credentials: false` and the compact Verdict step are still in the
workflow. They are harmless and mildly useful; they are not what fixed this.

## What the verdict said, and what it cost

`FAILING GATES: director, ops, witnessCar, coverage` — four gates, two bugs,
and neither was in the game. **Both were in the tests, and both were the same
mistake in different clothes.**

**1. Three gates were unsatisfiable.** The Director, the operations plan and
Act III all staged on `now.Day >= 9`, and day 9 cannot be reached in a
nine-day run: the Fall moves the calendar three days forward instead of
simulating them, so a fall late on day 8 lands the world on day 11 and
`Finish()` runs before hour 11 comes round again. Those three gates had never
once been evaluated. The reason four red builds never said so is the vacuum
the coverage floor was written to drain — while `OpenMode` was false each gate
passed on its own precondition being unmet. **Closing the vacuum is what
exposed the trap.** The floor worked exactly as intended.

Fixed by keying staging on the open city EXISTING rather than on a date, and
by having the sim reclaim days the clock skips (reported as `daysSkipped`) —
three days inside is world time, not simulated time, and counting it as
coverage is how "nine simulated days" quietly became "however many the bot had
left".

**2. The car gate was asking about the Fall.** `RunTheFall` clears every rumor
about the player — three days inside and the street stops guessing because it
now knows. Correct beat, and one of the better ones. But the gate read the
mill at the END of the run, so with a fall in the middle it was asking "did
the Fall happen" and answering truthfully. Now latched hourly while the run
happens.

**The pattern, named because it is three-for-three today:** a gate about
something that HAPPENED must be latched when it happens. Reading a mutable
world at the end and treating the answer as history is what broke the perf
gate, the car gate, and — in the other direction — what the day-9 staging
assumed. Apply this to anything new.

## Still unconfirmed at handover

- My earlier `dayJobOk` fix was **a prediction, not a diagnosis**, and the
  verdict did not name it. It stands on its own merits; it was never the bug.
- The end-screen freeze theory was also never the cause. The floor's
  `Ui.DismissEndScreen()` reports `endScreen=True` and is worth keeping, but
  `dayJobOk=True` and `actTwoOk=True` were already passing.
- Two facts I stated earlier were wrong and corrected: a "20+ minute Unity
  install" (twice) read off an **in-progress** API snapshot that lags. Both
  installs were ~7½ minutes. Only `started_at`/`completed_at` on a COMPLETED
  step is real.

## Suggested audit order

1. Read the verdict of the latest build with the call at the top of this file.
   Fix whatever it names.
2. Build HEAD green, in-engine, with `coverageOk=True` — that is the first
   run that will have genuinely exercised the second half of the game, and as
   of this handover it has still never happened.
3. The vacuous-assertion sweep is done; do not repeat it. If something new
   is added, apply both questions to it: does anything actually read this,
   and **is it latched or is it read off a world that moves?**
4. Only then: playtest, with `day-2026-07-27.md` as the what-changed guide.

## Two decisions Jafar answered this morning — already built

- **#9, the rackets.** "Couple it." `Empire.DailyTick` now takes a street
  factor; a starved district pays less, and somebody says why. The pinned test
  that asserted the old behaviour was flipped to demand the coupling.
- **#10, the inspector.** "Halve the relief now." `ScopeFactor`'s cooperation
  term 0.09 → 0.045. Stonewalling keeps its full 0.15; the asymmetry is
  deliberate — being difficult moves him further than cooperating does.

Measured over 400 worlds a row: the aggressive plan went 100% Kingdom → 100%
Burn Both; cautious-and-answered went 100% Kingdom → 48/52 Kingdom/Burn.
Cautious rounds fell 468 → 434 as prosperity dropped to 0.40 — decision 9
biting. Full table in `balance-findings-endings.md`.

**Whether that is the right FEEL is a playtest question, not a lab question.**
Both constants are one-line dials if the audit session wants them moved.
