# Audit brief — for the 14:00 CEST session

Jafar's plan: **full audit and test → fix → one more build → playtest.**
This is the scope, so that session starts auditing instead of orienting.

---

## The state in one paragraph

All three acts are wired and run end to end. Three districts exist. The
endgame resolves off world state and its distribution has been measured.
CoreTests 1344, SimHarness 71, lint and ShapeCheck clean. **The last full
green in-engine run was two hours before this was written, and it was green
having tested almost none of the game** — see "the honest part" below.

---

## What is DONE and verified

| | verified how |
|---|---|
| Act I — the week, seven pressure points | sim gate `actOne` |
| Act II — seven pressure points | sim gate `actTwo` (added today) |
| Act III — audit, inspector, last day, five endings | 1344 CoreTests + sim gate `actThree` + balance lab |
| Three districts (Hook, Copper Row, Ironside) | CoreTests geography + population |
| Traffic, signals, vehicles, the car | CoreTests + sim gates |
| Phones (M10), harm (M11), purses (M13) | CoreTests + sim gates |
| Front end (menu, options, pause, rebinding) | UI smoke test, `panelsBad == 0` |
| Save/load of everything above | codec round-trips, in-engine overlay |

## What is DONE but NOT felt

**Nobody has played the endgame.** Act III is measured, not experienced. The
ending distribution is in `balance-findings-endings.md`; whether the six days
have the right *shape* is a question only playing answers. Same for Act II's
pacing — the seven fire correctly and nobody has watched them space out.

## What is PENDING

Two items, **both Jafar's calls, both written up with recommendations and
numbers in `decisions-pending.md`. Neither should be built without an answer.**

- **#9 — the rackets are the last infinite pocket.** The purse spec skipped
  them citing "already coupled through prosperity". Half true: the take drains
  the street; nothing lets the street limit the take. You collect the same
  sixty a day from a district you have starved.
- **#10 — the inspector may be too decisive.** Ignored is 100% Burn Both,
  answered every morning is 100% Kingdom on the aggressive plan. Six mornings
  of paperwork outweighs three acts of laundering. One constant, dialled
  either way in a minute — but what it should FEEL like is a playtest answer.

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
2. `FAILING GATES: a, b, c` — the sim's last log line on failure, and the
   workflow echoes the verdict after the tail so it survives truncation.
3. The "does anything actually read this" pattern — applied to `LedgerState`
   (every field must be able to change the ending) and to three closed
   vocabularies (`Checks`, `Effects`, `Pressures`). Not yet applied to
   `Economy.FactorFor`, `Empire.DailyTick`'s income modifiers
   (`NewCrewTaxing`, `TributeShare`, `SharedRacketId` — each a multiplier that
   could be computed and dropped), or the Access/Operation vocabularies.

## Known-unresolved at handover

- The build in flight when this was written had **not** yet reported which
  gate failed on its predecessor. My `dayJobOk` fix is **a prediction, not a
  diagnosis** — I never read the failing gate. If the verdict line names
  something else, fix that instead of inheriting my guess.
- Two facts I stated today were wrong and corrected: a "20+ minute Unity
  install" (twice) read off an **in-progress** API snapshot that lags. Both
  installs were ~7½ minutes. Only `started_at`/`completed_at` on a COMPLETED
  step is real.

## Suggested audit order

1. Read the verdict line of the latest build. Fix whatever it names.
2. Build HEAD green, in-engine, with `coverageOk=True` — that is the first
   run that will have genuinely exercised the second half of the game.
3. Sweep for more vacuous assertions (list above).
4. Only then: playtest, with `day-2026-07-27.md` as the what-changed guide.
