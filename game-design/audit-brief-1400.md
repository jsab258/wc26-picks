# Audit brief — for the 14:00 CEST session

Jafar's plan: **full audit and test → fix → one more build → playtest.**
This is the scope, so that session starts auditing instead of orienting.

---

## The state in one paragraph

All three acts are wired and run end to end. Three districts exist. The
endgame resolves off world state and its distribution has been measured.
CoreTests 1391, SimHarness 71, lint and ShapeCheck clean. **The last full
green in-engine run was two hours before this was written, and it was green
having tested almost none of the game** — see "the honest part" below.

---

## What is DONE and verified

| | verified how |
|---|---|
| Act I — the week, seven pressure points | sim gate `actOne` |
| Act II — seven pressure points | sim gate `actTwo` (added today) |
| Act III — audit, inspector, last day, five endings | CoreTests + sim gate `actThree` + balance lab |
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
2. `FAILING GATES: a, b, c` — the sim names its own failures instead of
   hiding them in a thirty-term `&&`. **Read it in the Actions web UI**: open
   the run, click the job, read the `Verdict` step. That has always worked;
   only this sandbox's log truncation made it look hard (see known-unresolved).
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

   One gap is pinned rather than fixed: the rackets read `IncomePerDay` flat,
   so a starved district pays the same round as a rich one. The test asserts
   the CURRENT behaviour and names decisions-pending #9, so it reads as a held
   decision rather than an oversight.

## Known-unresolved at handover

- **The failing gate has still never been read**, across FOUR red builds.
  Worth knowing why, because it cost most of a morning:

  The job-log API returns a fixed ~4KB tail, and GitHub's own post-job cleanup
  (licence deactivation, git config unwinding) writes about that much AFTER
  every user step. The budget is consumed by hooks nobody controls, so
  "print it later in the job" can never work — I tried it three times.
  Artifacts hold the full `sim-report.json` but sit on a blob host this
  environment's egress policy denies with a 403 (a policy denial: report it,
  do not retry). The check-run API returns job output, and it was empty
  because nothing had ever written a job summary.

  **`GITHUB_STEP_SUMMARY` does not work either** — tested on a completed,
  failed job: `check_run.output` came back empty. For Actions jobs that field
  is not populated from the job summary.

  So four channels are ruled out by test: end of the sim step, a final step,
  artifacts (egress 403), and the check-run summary. What is left is the ~4KB
  log tail, and the fifth attempt attacks the NOISE instead of the position:
  `actions/checkout` with `persist-credentials: false` (nothing here pushes,
  and the credential costs ~1.5KB of git-config unwinding in post-job), plus
  a Verdict step that prints a compact block rather than the ~1.2KB done-line.

  **THE IMPORTANT DISTINCTION, and it took far too long to state:** the verdict
  is not missing. It is printed, it is in the log, and it is plainly visible in
  the Actions web UI — open the run, click the job, read the `Verdict` step.
  The whole problem is that MY retrieval path truncates. A human with a browser
  has never been blocked by any of this.

  So if attempt five also fails: **just look at it in the browser.** Do not
  spend another build cycle on the plumbing. Five attempts is already more
  than a logging problem deserves and it must not eat the audit session.

  The same holds for the artifacts: `sim-report.json` has every gate value and
  downloads fine from the browser. Only the sandbox's egress policy blocks it.
- My `dayJobOk` fix is therefore **a prediction, not a diagnosis**. It stands
  on its own merits (the day job was the one open-city system the sim left to
  the bot's legs) but it has never been confirmed as the cause. If the verdict
  names something else, fix that instead of inheriting the guess.
- **The strongest candidate, found by reading the last GREEN run instead of
  waiting:** that run ended `verdict=LostExposed` on day six. Losing the week
  calls `EndCampaign`, which raises an end panel and sets `InputLocked` — and
  the won-week path has a sim bypass while the lost path never did, because
  until the coverage floor existed nothing after a loss was ever exercised.
  So the bot was frozen behind "the week is settled" while the sim asserted
  things about the open city, and the day job in particular needs legs.

  The floor now calls `Ui.DismissEndScreen()` and unlocks the player, and
  reports `endScreen=`. **Still a candidate, not a confirmed cause** — the
  verdict has not been read even once.
- Two facts I stated today were wrong and corrected: a "20+ minute Unity
  install" (twice) read off an **in-progress** API snapshot that lags. Both
  installs were ~7½ minutes. Only `started_at`/`completed_at` on a COMPLETED
  step is real.

## Suggested audit order

1. Read the verdict line of the latest build. Fix whatever it names.
2. Build HEAD green, in-engine, with `coverageOk=True` — that is the first
   run that will have genuinely exercised the second half of the game.
3. The vacuous-assertion sweep is done; do not repeat it. If something new
   is added, apply the same question to it: does anything actually read this?
4. Only then: playtest, with `day-2026-07-27.md` as the what-changed guide.
