# DIRECTOR RULING: the D1 timebox is retired; measurement (a) fails by non-convergence, never by a date; the tilt toward Unreal is an allocation, not a reading (2 Sep 2026)

> **STATUS — LOG, 2026-09-02. NOT CURRENT once the dictated edits R1a to R1n are applied, queue item 031 exists and the dashboard's read_d1 reads the retired shape; from then the D1 register, production/d1-probe/plan.md, measurements.md, the queue, production/budget.md and NOW.md are the reading copies and this file is their history.**

This document carries exactly one em-dash, in the banner above, because
`tools/docs-check.py` line 55 hard-codes that character in the regex it
accepts. Named as a finding three rulings ago; still not a licence.

Eighth ruling since 1 September. This role has no shell: every number below
was read from a file this session, and the file and line are named beside
it. Nothing here was taken from a builder's or the resident's report.

## What Jafar ruled, verbatim

Answering the recommendation to pre-register how D1 closes if Unreal could
not produce a textured still by 2026-09-12:

"yes but forget the deadline, it's not relevant. doesn't make sense to set
a hard deadline when we can work continuously, we are limited by 5h and
weekly usage limits in claude. rather spend more time to get UE working,
that's what will help us achieve our main goal"

He accepted the reasoning and removed the clock it rested on. Three
consequences follow and none of them is the resident's to settle alone: a
timebox written into several documents and one ruling is retired; the
failure mode of measurement (a) was a date and now needs another; and a
stated preference for investing in Unreal must not become a thumb on a
comparison that is judged blind.

## What was verified before ruling

- My own row: `.claude/agent-log.tsv` line 198, `2026-09-02T06:47:37Z
  studio-director`, the newest in the file. `.git/logs/HEAD` lines 300 to
  338: the vignette batch is commit `d25a4770` at epoch 1788330360
  (06:26:00Z); the newest commit is `ef93ad03` at 06:41:51Z; my row is
  newer than every commit in the reflog.
- Every file the grep for `2026-09-14`, `2026-09-12`, `14 September`, `12
  September` and `timebox` found outside `legacy/`, each opened at the hit:
  `ledger-v2/respec/decision-register/D1-engine-probe.md` (9 lines, in
  full); `production/d1-probe/plan.md` (lines 1, 4, 13, 106, 114, in full);
  `game-design/decision-D1b-rescope.md` (lines 25, 37, 96, in full);
  `production/week-plan.md` line 47 (in full); `THIRD-PARTY.md` lines 243
  to 245; `production/queue/027-ue-vignette-emitter.md` line 5 (in full);
  `production/queue/004-d1-unity-street-ceiling.md` lines 3, 6, 7 (in
  full); `production/NOW.md` lines 65 to 82 (in full);
  `game-design/decisions-pending.md` lines 14 to 37 (in full);
  `production/briefs/latest.md` line 74; `ledger-v2/handoff/HANDOFF.md` line
  22; `game-design/decision-2026-09-01-production-prep-sequence.md` line
  124; `production/specs/vignette-fetch-01.json` line 108;
  `tools/dashboard/build-dashboard.py` 600 to 642 (`read_d1`), 691 to 694,
  2488 to 2499 (its fixture); `STATUS.md` line 43.
- `ledger-v2/respec/roadmap-v2.md` in full (17 lines). IT CARRIES NO DATE.
  `game-design/decisions-pending.md` line 29 says the timebox is written
  into it; that is wrong, and the correction is dictated below. What the
  roadmap carries is the standing rule at line 16, "every phase with a taste
  gate also gets a time or attempt budget at kickoff", and
  `ledger-v2/studio-v2/constitution.md` law 10 says the same: "an attempt or
  time budget". Both permit an attempt budget. That is the hinge of Ruling 2.
- The previous ruling, `decision-2026-09-02-vignette-batch-canon-crews-d1-
  timebox.md`, in full: Ruling 7 (last sentence), Ruling 10 (heading and
  last paragraph), Ruling 11 (all three readings).
- `production/d1-probe/measurements.md` in full; `cycles.tsv` in full (9
  rows, 4 pass, 5 fail, all on 1 September); `DISPATCH` in full (runs 1 to
  16); `FETCH-VIGNETTE` in full; `ue-verdict.txt` (line 1 names `db8097d`,
  so run 16 has not landed).
- `game-design/sim-shots/verdict.txt` line 1 (`d25a477 @1788330360`), line
  92 (`gatesChecked=72`), line 94 (`vignette=NO-RUN`), line 95 (`simExit=1`),
  `dayMark` lines to day 13; no `vign_*` file anywhere under `game-design/`.
  `.github/workflows/ledger-build-windows.yml` 500 to 569: the vignette step
  now carries `if: always()` with a comment at 523 to 532 saying the step
  was skipped on its first run. `tools/sim-shots-commit.sh` 194 to 209.
- `.github/workflows/ledger-probe-unreal.yml`: every step name and timeout
  (86 to 687); the build step 198 to 347. A cold-build failure commits the
  LAST 40 LINES of the build log (line 253); a cook failure pulls every
  error line from the whole log with both caps announced (315 to 327).
- `production/budget.md`, `production/quality-ladder.md`, `production/
  queue/007`, the status lines of queue 020 to 029, the queue file list
  (next free number 031), `game-design/decisions-answered.md` 1 to 40,
  `tools/docs-check.py` 41 to 73, `ledger/verify.py` 2470 to 2476 and 3128
  to 3132 (the stamp must name a director row newer than the reference
  commit), `ledger-v2/studio-v2/operations.md` lines 5, 85, 138 to 144.

## Ruling 1: what the retirement changes, document by document

The rule for every edit: the retired date stays visible as history where the
document is a LOG, and disappears where the document is read as live. The
text is dictated so nothing is judged at apply time. Line numbers are as
read this session; the resident confirms each by grep before editing.

**R1a. `ledger-v2/respec/decision-register/D1-engine-probe.md`**, the
source of truth. Append after line 8, one paragraph:

```
AMENDED 2026-09-02: the two-week timebox is RETIRED by Jafar ("forget the deadline, it's not relevant"; his full words in game-design/decision-2026-09-02-d1-timebox-retired.md). The probe is bounded by production/budget.md and by the attempt budget on queue item 027 (constitution law 10), never by a date. Measurement (a) fails by non-convergence or hand-edit dependence as defined in production/d1-probe/measurements.md. Decision rule unchanged: Unreal wins only if (b) is decisively better and (a) is tolerable; ties go to Unity.
```

**R1b. `production/d1-probe/plan.md`.** Line 1 becomes
`# D1 engine probe: execution plan (kicked off 2026-08-31, timebox retired 2026-09-02)`.
Line 4, `exactly. Two-week timebox; the decision record cites measurements, never`,
becomes
`exactly. The two-week timebox was RETIRED 2026-09-02 (amendment below); the decision record cites measurements, never`.
Insert after line 22, before `## AMENDED 2026-09-01: UNBLOCKED`:

```
## AMENDED 2026-09-02: THE TIMEBOX IS RETIRED. Jafar: "forget the deadline, it's not relevant"

Ruling: game-design/decision-2026-09-02-d1-timebox-retired.md. The dates on
the two week headings below are the original plan's and no longer bind. The
probe is bounded by production/budget.md (the weekly ceiling) and by the
attempt budget on queue item 027: a director review every 6 dispatches a
phase spends without landing, 6 being the longest stretch this probe spent
on one sub-goal (the cook, runs 8 to 13), the only series that exists.
Measurement (a) is failed by non-convergence or hand-edit dependence, defined
in measurements.md, and never by a date. The decision rule is unchanged,
ties go to Unity, and "if the UE side cannot be measured, D1 closes
UNRESOLVED" still means an external blocker, not a slow loop.
```

**R1c. `game-design/decision-D1b-rescope.md`** line 96,
`- **Timebox: unchanged, ends 2026-09-14. No extension granted.**`, becomes:

```
- **Timebox retired 2026-09-02 by Jafar.** This line read "unchanged, ends 2026-09-14, no extension granted" until then; the retirement and what bounds the probe instead are in game-design/decision-2026-09-02-d1-timebox-retired.md.
```

Line 37 (`Timebox ends 2026-09-14.`) stays: it records what was read on 1
September. Note for R1n: `read_d1`'s `re.search` over this file currently
finds line 37 first, not line 96, so today's "2 sources agreeing" is
agreement with the verification list, not with the ruling. Harmless while
both said the same date; the new reader must not inherit it.

**R1d. `production/week-plan.md`** line 47 becomes:

```
Items 3 to 5 were the timebox ending 2026-09-14; Jafar RETIRED it on 2026-09-02 (game-design/decision-2026-09-02-d1-timebox-retired.md). They are bounded by the rates above and production/budget.md, not by a date.
```

**R1e. `THIRD-PARTY.md`** lines 244 to 245, `is engine-neutral by ruling and
the engine is undecided until the comparison` / `timebox ends.`, become the
single line `is engine-neutral by ruling and the engine is undecided until D1 closes.`

**R1f. `production/specs/vignette-fetch-01.json`** line 108, inside a note
string: `until the D1 timebox ends` becomes `until D1 closes`. Nothing else
on the line changes; the file must still parse (`fetch_vignette.py --plan`
is the check).

**R1g. `production/queue/027-ue-vignette-emitter.md`.** Line 5 becomes:

```
status: READY 2026-09-02. engine-specialist. THE CRITICAL PATH on merit, not on a clock: the timebox was retired 2026-09-02 (game-design/decision-2026-09-02-d1-timebox-retired.md); this item stays first because it is the only queued work that moves the Phase 0 exit gate.
```

Append at the end of the file:

```
## RULED 2026-09-02 (director, decision-2026-09-02-d1-timebox-retired.md)

ATTEMPT BUDGET, constitution law 10, in place of the retired date. Every
line in production/d1-probe/DISPATCH names the phase it serves and what the
run will prove. When a phase has spent 6 dispatches without landing, the
next dispatch WAITS for a director review of that phase's series:
converging (each failure diagnosed from a committed file, each dispatch
carrying a new hypothesis or a better instrument) or not. Six is the
longest stretch the probe spent on one sub-goal (the cook, runs 8 to 13),
the only series that exists; it is a review trigger, not a kill.
max_sessions stays 3 and is refilled on merit by a director, never by
default and never by a date.

WHAT FAILS MEASUREMENT (a) HERE: production/d1-probe/measurements.md, the
section ruled 2026-09-02. In short: three dispatches running on one failure
mode with no new diagnosis, or a phase that cannot land without a hand-made
asset.

THE FIRST UE DISPATCH CARRIES QUEUE 031 (the loop investment). Phase A needs
no UE round trip; the first dispatch that does (Phase B) rides the
signature dump and the compile-only lane, and every line of the emitter
that can be compiled and run by g++ in this container is (the FrameStats.h
pattern): the vignette-pieces.json reader, the transform arithmetic, the
shot list, the verdict formatting. A dispatch tests only the lines that
cannot be tested here.

THE UNITY HALF IS OWED ON THE SAME TERMS. No pair is judged until both
engines have committed all four vign_* stills, and a Unity fault gets the
same fix-and-redispatch as a UE one. On d25a477 the Unity vignette step was
skipped (verdict line 94, vignette=NO-RUN, with the sim itself reaching day
13); the if: always() fix is in ledger-build-windows.yml lines 523 to 532
and the re-dispatch rides the next push.
```

**R1h. `production/queue/004-d1-unity-street-ceiling.md`.** Line 3 becomes
`acceptance: the reference street built to the Unity ceiling under the budget (the timebox was retired 2026-09-02); paired stills committed per dispatch; no hand-edited binary scenes`.
Insert after line 4:
`status: STARTED 2026-09-02 as the vignette's Unity half (queue 025, 027, 028): production/specs/vignette-scene.json and StreetVignetteHost.cs are this item's build; done when the four Unity vign_* stills have landed and been opened.`
Lines 6 to 7, `Build the agreed reference street to the Unity ceiling inside the timebox,` / `committing stills daily so the comparison has a dated series rather than`,
become `Build the agreed reference street to the Unity ceiling under the budget,` / `committing stills per dispatch so the comparison has a series rather than`.

**R1i. `production/NOW.md`** lines 65 to 82 (the section `## The D1
question that is Jafar's, not the studio's`) are replaced by:

```
## The D1 question: ANSWERED by Jafar 2026-09-02, the timebox is retired

His words: "yes but forget the deadline, it's not relevant. doesn't make
sense to set a hard deadline when we can work continuously, we are limited
by 5h and weekly usage limits in claude. rather spend more time to get UE
working, that's what will help us achieve our main goal"

Ruled in game-design/decision-2026-09-02-d1-timebox-retired.md. No date
bounds D1; the budget does (production/budget.md), plus an attempt budget
on queue 027 (a director review every 6 dispatches a phase spends without
landing). Measurement (a) fails by NON-CONVERGENCE (three dispatches on one
failure mode with no new diagnosis) or by HAND-EDIT DEPENDENCE (a phase that
cannot land without a hand-made asset), never by a date. The decision rule
is unchanged, ties still go to Unity, and the pairs are still judged blind:
the tilt toward Unreal decides how much evidence UE gets to produce, never
what the evidence says. 027 stays first on merit; 031 (the loop investment)
rides its first UE dispatch. One question is open for Jafar in
decisions-pending.md: whether "ties go to Unity" stands (recommended: yes).
```

The rest of NOW.md is the resident's to refresh in the same commit: the
STOPPED section at lines 12 to 26 predates the 04:40Z reading; line 49 is
still true (nothing has rendered the vignette); lines 54 to 60 should say
the Unity job landed on `d25a477` with `vignette=NO-RUN` and that run 16 and
the fetch had not landed at 06:47Z.

**R1j. `game-design/decisions-pending.md`.** Lines 29 to 30, `the 2026-09-14
timebox in decision-D1b-rescope.md and roadmap-v2.md is` / `retired;`,
become:

```
the 2026-09-14 timebox in decision-D1b-rescope.md and production/d1-probe/plan.md is
retired (roadmap-v2.md never carried the date; it carries the standing rule
"time or attempt budget", which the ruling satisfies with an attempt budget);
```

After line 37 append `Ruled: game-design/decision-2026-09-02-d1-timebox-retired.md.`
And insert, directly under `## WHAT IS WAITING` and its two-line note
(after line 12), the one question this ruling leaves for him:

```
### Does "ties go to Unity" still stand? (added 2026-09-02 by the director)

**In plain terms.** You removed the deadline and said to spend more time
getting Unreal working. That changes how much the studio invests in the
Unreal side. It does NOT, on its own, change the rule that decides the
comparison: Unreal wins only if its frames are decisively better in a blind
look AND its edit-build-see loop is tolerable; a tie goes to Unity. Nobody
has changed that rule, and the studio will not read your words as changing
it unless you say so.

| | what it means | what it costs |
|---|---|---|
| A | **The rule stands.** Ties go to Unity; Unreal must win the blind look decisively. | Nothing. It is what is written. |
| B | **Ties go to Unreal.** If the frames tie, the engine with the higher published ceiling wins. | A slower loop chosen on a tie, paid in the weekly budget on every rung from then on. |

**Recommendation: A**, from your own reasoning: the constraint is Claude
usage, and a faster loop spends less of it per rung. A tie means both
pipelines reached the same ceiling on this scene, and then the loop cost is
the only difference left.
```

**R1k. `production/budget.md`.** Insert after line 24 (`Ceiling for LEDGER:
80% of the weekly limit. The other 20% is his.`):

```
Told by Jafar 2026-09-02, retiring the D1 deadline: "we are limited by 5h
and weekly usage limits in claude". Dates are not a planning unit here. Any
bound on a piece of work is written in dispatches, sessions or points of
this ceiling, never as a calendar date. Ruling:
game-design/decision-2026-09-02-d1-timebox-retired.md.
```

**R1l. `production/d1-probe/measurements.md`.** Append at the end:

```
## What fails measurement a, ruled 2026-09-02 (the timebox is retired)

Until 2 September (a) was going to be failed by a date: no textured UE
still of the shared scene by 2026-09-12 12:00Z would read NOT TOLERABLE.
Jafar retired the date. What fails (a) now is a property of the series in
DISPATCH and cycles.tsv, never of the calendar:

1. NON-CONVERGENCE. Three consecutive dispatches on one phase fail on the
   same failure mode and the committed evidence cannot name the cause. Two
   is the worst this probe has printed (the setup section above: two
   failures took two round trips each, and those were the two where the
   step could not say why). Three is the first point outside the record.
   At three, a director is spawned and either closes (a) NOT TOLERABLE on
   the series or names the instrument change that makes the failure
   readable (rule 12); the count restarts only when the instrument changed,
   never when the guess did.
2. HAND-EDIT DEPENDENCE. A phase that cannot land without a hand-made
   binary asset. D1b's admissibility rule already disqualifies the still;
   the finding here is about the loop: a failed-edit rate of 100 percent on
   that asset class, which is the UE-specific friction (a) was written to
   catch. One interactive session for SETUP (a plugin, a licence prompt) is
   a named ask to Jafar and is not this; a hand-made asset is.
3. THE COST HALF stays a printed pair, not a bound: median cycle and
   dispatches spent for the SAME job (the four vign_* stills) in each
   engine, quoted in the close-out beside the (b) reading. No number is set
   for "tolerable" because no series covers a UE scene with content yet;
   when both engines have the job landed the pair is put to Jafar with the
   blind reading, and a close that cannot quote the pair is not a close.

Rows in cycles.tsv from the compile-only lane (queue 031) carry the word
compile-only in whatWasEdited and are never pooled with full-loop rows: a
lane that does less is faster because it does less.
```

**R1m. `production/quality-ladder.md`** line 34, the `Engine loop (D1)`
row, becomes:

```
| Engine loop (D1) | Build, port and cook measured on the real machine; a UE compile is checked blind, one full round trip per hypothesis (median 10 min over 9 rows, before any cook or capture was in the loop). | Queue 031: the installed engine's own declarations for every symbol the emitter names, committed before the code is written; a compile-only lane that answers "does it compile" without a cook or a capture; everything engine-free compiled and run by g++ here before dispatch. |
```

**R1n. `tools/dashboard/build-dashboard.py`, `read_d1`** (instrument-
builder, code, covered by this row; reviewed by the next director before
commit). The instrument reads two sources that must agree; after R1b and
R1c neither carries `ends <date>` in the shape it expects, so today it
would print "unavailable" with a reason, which is honest and temporary.
The new reader: in the plan, `kicked off (\d{4}-\d{2}-\d{2}), (ends|timebox
retired) (\d{4}-\d{2}-\d{2})`; in the ruling, search `[Tt]imebox retired
(\d{4}-\d{2}-\d{2})` FIRST and only if absent the old `ends` pattern. Both
retired with one date: measured, `day N since kickoff 2026-08-31, no end
date: timebox retired 2026-09-02; the bound is production/budget.md and the
attempt budget on queue 027`, note naming both sources. Retired in one and
not the other, or two different dates: refuse as disagreement, exactly as
now. Row name `D1 engine probe (timebox)` becomes `D1 engine probe`.
Fixtures: accepting FIRST on the live tree (both retired, same date); then
rejecting (plan retired, ruling still `ends`); rejecting (retired dates
differ); and the existing `ends` disagreement fixture kept. Report both
outputs.

**Not edited, and why.** `ledger-v2/respec/roadmap-v2.md`: no date in it;
its standing rule is satisfied by Ruling 2. `ledger-v2/handoff/HANDOFF.md`
line 22: the dated origin package, whose item 3 defers to the register
"exactly as specified"; the register now carries the amendment.
`production/briefs/latest.md` and `2026-09-02.md`: sent artifacts; the next
brief corrects. `decision-2026-09-01-production-prep-sequence.md` line 124
and the previous ruling: LOGs; this record is their amendment. `STATUS.md`:
regenerated by the session hook from R1n. `canon.md`: unchanged; nothing in
this ruling touches a world fact.

**What is moot in the ruling of 2 September, by number.** Ruling 7's last
sentence: the sentinel scaffolding is deleted when the workflows reach
`main`, with no earliest date. Ruling 10's heading and last paragraph: the
order stands on merit (Ruling 4 below), and "until 14 September" reads
"until D1 closes, or a director refill fills a UE wait". Ruling 11: readings
1 and 3 are moot, since no box expires; reading 2's pre-registration
survives with its date replaced by R1l's criteria, and its distinction from
"cannot be measured" survives verbatim. Ruling 11's estimate stands: the
date going does not make the loop faster.

## Ruling 2: what fails measurement (a) now

The sharp question. D1's rule is that Unreal wins only if (b) is decisively
better AND (a) is tolerable for autonomous operation. "Tolerable" was going
to be failed by a date. If nothing can fail it, the rule has become "(b)
alone", which nobody ruled. So (a) keeps a failure mode, and it is a
property of the series rather than of the calendar, defined in R1l:
non-convergence (the same failure mode three dispatches running with no new
diagnosis, three being the first point outside the printed worst of two),
or hand-edit dependence (a phase that cannot land without a hand-made
asset). Both are things the pipeline either does or does not do; neither
is taste, and neither is a date.

The cost half of (a), median cycle and dispatches for the same job in each
engine, is printed and put to Jafar at close beside the blind reading. No
bound is set on it, because no series covers a UE scene with content (rule
2), and a close that cannot quote the pair is not a close.

Constitution law 10 and the roadmap's standing rule require an attempt or
time budget at kickoff. The time budget is gone; the attempt budget is R1g:
a director review at 6 dispatches per phase without a landing, derived
from the longest sub-goal the probe has printed (the cook, runs 8 to 13),
and `max_sessions: 3` refilled on merit by a director. It is a review
trigger, not a kill, so it cannot ratchet; and it is mechanical, so (a)
cannot go unasked because nobody spawned the question.

D1 therefore closes in one of three ways, and no fourth: (i) both engines
land the four admissible pairs, (a)'s pair is printed, the blind look is
taken, and the rule as written decides; (ii) (a) fails by R1l, and D1
closes UNITY on its own clause with (b) recorded UNMEASURED and why; (iii)
an external blocker (a launcher, a licence) stops the UE side being
measured at all, and D1 closes UNRESOLVED, which is what that phrase was
written for. A loop that is slow but converging is none of these and keeps
going, on the budget.

## Ruling 3: the tilt toward Unreal and the blind reading coexist, and here is how

Jafar's direction is an ALLOCATION: 027 first, the loop investment funded,
the attempt budget refillable on merit, no date. The blind judging is a
READING: four pairs by id with the engine stripped, judged after both sets
exist, with (a)'s numbers printed before the look. The allocation decides
how much evidence the UE side gets to produce. The reading decides what the
evidence says. The one is an input to the denominator and never to the
verdict, and this record exists so that a later reader sees the
investment was decided here as allocation and not slipped in as a thumb.

Two guards make that real rather than declared. First, the Unity side is
owed on the same terms (R1g's last paragraph): a Unity fault gets the same
fix-and-redispatch, and nothing is judged until both sides' four stills
are committed. Starving one side is the quiet way to bias a blind look.
Second, "ties go to Unity" is UNCHANGED by his words. He said where to
invest; he did not say how to score, and the studio will not infer the
second from the first. If he wants the tie-break changed, that is a
strategic call and it is his: R1j puts it to him in one line, with my
recommendation that it stands, argued from his own constraint (a faster
loop spends less of the weekly ceiling per rung).

## Ruling 4: the queue order stands, on merit rather than on a clock

027 first: it is the only queued item that moves a Phase 0 exit gate ("D1
decision recorded with measurements", roadmap row 0), every visual rung on
the ladder waits on the engine (quality-ladder.md line 38), and Jafar's
direction says the same. 028 second, because the body makes the scene
admissible in both engines (D1b line 70) and is content-side work that can
run while a UE round trip is in flight. 031 rides 027's first UE dispatch
and is not a separate round trip. 029 is resident-only and free. 020 to
024, 026 and 030 keep their places behind those, until D1 closes or a
director refill fills a UE wait with one of them; refill is the existing
escalation and needs no new rule.

The two builders this ruling authorises (engine-specialist for 027 Phase A
plus 031; instrument-builder for R1n) are briefs, not diffs: the diffs are
reviewed by the next director before commit, per the standing split. And
they wait for a usage number: the 17 percent reading at 04:40Z has seven
builders and two directors behind it, which by budget.md's own rule makes
the day unmeasured until Jafar reads it again. The dictated edits and this
record cost no model time and land now.

## Ruling 5: the right response to "more time" is a cheaper loop, and here is what

Removing the box does not make a blind round trip cheaper. The previous
ruling's engineering read stands: what dominates the UE path is C++ written
without a compiler against a loop that answers in ten minutes (cycles.tsv,
median over 9 rows) and will answer in twenty once a cook and a capture are
in it (DISPATCH run 16's own estimate), and what blows it up is one drifted
5.8 signature failing the whole probe. More attempts through that loop buy
attempts. The investment that makes "more time" worth having is in the
loop, and it is queue item 031 (engine-specialist, one session, riding
027's first UE dispatch):

1. **Ask the engine for its signatures before writing against them.**
   `ue-probe/signatures.txt`, one symbol per line, listed by the builder
   BEFORE the emitter is written. A workflow step on the runner searches
   the installed engine's public headers for each and commits
   `production/d1-probe/ue-signatures.txt`: engine version and commit on
   line 1, then per symbol the file, the line and the declaration, or NOT
   FOUND; `signatures found=N/M` on the done line. A NOT FOUND is a finding
   before a compile rather than after one, and the dominant risk named
   above becomes a read rather than a guess.
2. **A compile-only lane.** A `compile-only` prefix on the DISPATCH line
   (or a `workflow_dispatch` input) that runs checkout, bootstrap,
   signatures, cold build and the commit step, skipping cook and capture.
   Compile errors are pulled from the WHOLE build log by pattern with both
   caps announced, the way the cook step already does at lines 315 to 327;
   today a compile failure commits a 40-line tail (line 253), which is the
   cap-bites-silently shape this project has a rule about. The lane prints
   its round trip on the done line and its cycles.tsv rows are labelled
   compile-only and never pooled with full-loop rows.
3. **Engine-free first.** The emitter's `vignette-pieces.json` reader, its
   transform arithmetic (the scene's bearing sense and unit scale against
   UE's frame, asserted by a fixture the builder derives and not by a
   frame), the shot list and the verdict formatting live in headers with no
   Unreal type, compiled and run by g++ in `ledger/verify.py` before any
   dispatch, accepting case first. That also lands the carried follow-up
   from 027, wiring `frame-stats-test.cpp` into `verify.py` so the 25 checks
   cannot rot. The UE-facing code is spawn, transform, material parameter,
   capture, and a dispatch tests only those lines.

Not in 031: a local UE build in this container (no engine, no headers,
blocked hosts), and any change to the decision rule.

Item file, dictated, `production/queue/031-ue-loop-investment.md`:

```
line: production (D1 comparison, the loop)
spec: game-design/decision-2026-09-02-d1-timebox-retired.md, Ruling 5
acceptance: (1) production/d1-probe/ue-signatures.txt committed by a run, line 1 the engine version and the commit, one block per symbol in ue-probe/signatures.txt with file, line and declaration, NOT FOUND per missing symbol, and found=N/M on the done line; (2) a compile-only lane of ledger-probe-unreal.yml that stops after the cold build and commits ue-build.txt with every error line from the whole build log, caps announced, round trip printed; (3) every engine-free line of the emitter under ue-probe/tests/ compiled and run by g++ from ledger/verify.py, accepting case first, frame-stats-test.cpp included
max_sessions: 1
status: READY 2026-09-02. engine-specialist. Rides queue 027's first UE dispatch; not a separate round trip.

Why this and not more attempts through the loop, what each of the three
parts is, and what is out of scope: Ruling 5 of the spec above, in full.
The builder reads the ruling, not this stub.
```

## Findings not ruled, with the cheapest decisive measurement

- **The Unity vignette measured nothing on `d25a477`.** Verdict line 94
  `vignette=NO-RUN`; the sim reached day 13 and `gatesChecked=72`, so the
  batch did not break the sim; the step was skipped because an earlier
  step's exit was non-zero (`simExit=1`, line 95) and the vignette step had
  no `if: always()`. The fix is in the tree at workflow lines 523 to 532.
  Measurement: `git log -1 -- .github/workflows/ledger-build-windows.yml`
  and `git status` say whether it is committed; if not, it lands in the
  ruling's commit as a genuine fix already written. Re-dispatch the Unity
  build by hand after the push. NOW.md line 49 stays true until then.
- **E5 of the previous ruling may not have been applied.**
  `production/d1-probe/FETCH-VIGNETTE` line 18 still reads `not yet
  dispatched`. Measurement: `git diff HEAD -- production/d1-probe/FETCH-
  VIGNETTE` and `git log -1 -- production/d1-probe/FETCH-VIGNETTE`. If the
  file was created in the batch the fetch fired anyway (a new file is a
  change to its path); the words are still wrong and E5 is applied in this
  commit.
- **Run 16 and the fetch had not landed at 06:47Z** (`ue-verdict.txt` names
  `db8097d`; no `fetch-verdict.txt` exists). Watch by ancestry; both are
  serial behind the Unity job on one runner (Ruling 7 of the previous
  record). Read `ue-shot-verdict.txt` for `shotStatus` before anything else
  UE-side.
- **`docs-check.py` line 55** still hard-codes the em-dash. Queue 020 owns
  the checker; the resident appends the line number to it.

## Deliberately not decided

- The engine. Ruling 2 says how D1 closes; it does not close it.
- Whether "ties go to Unity" stands. Jafar's, put to him in R1j.
- Any number for "tolerable" on the cost half of (a). No series.
- The width of the compile-only lane's error patterns. The builder reads
  a real failing log before choosing them; the cook step's list is the
  starting point, not the answer.

## For the next session in one line each

- Apply R1a to R1m by hand, each line confirmed by grep first; write 031
  from R5's stub; apply E5 if the diff says it is missing.
- Check whether the `if: always()` workflow fix is committed; if not, stage
  it by name in the same commit.
- Run verify; commit once, staged by name; push (no sentinel is touched, so
  no self-hosted job fires); re-dispatch the Unity build by hand.
- Refresh NOW.md: the budget section to the 04:40Z reading and the spawns
  since; the three-jobs paragraph to what landed; the D1 section to R1i.
- One line to Jafar: the deadline is retired as he asked and what bounds
  D1 instead; the one question (ties go to Unity, recommend yes); a usage
  number.
- After the number: spawn the engine-specialist (027 Phase A plus 031) and
  the instrument-builder (R1n); both diffs go to the next director before
  commit.
- When run 16 lands: `shotStatus` first, then the still (rule 4); its
  dispatch count starts the 027 series at zero, not at sixteen.

Spawn row, quoted verbatim from `.claude/agent-log.tsv` (line 198):

    2026-09-02T06:47:37Z	studio-director

<!--RULING spawn=2026-09-02T06:47:37Z-->
