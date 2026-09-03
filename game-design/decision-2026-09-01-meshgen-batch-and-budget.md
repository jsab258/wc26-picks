# DIRECTOR RULING: the meshgen batch, the dead builder, and the budget docs (1 Sep 2026)

> **STATUS: LOG, 2026-09-01. NOT CURRENT once the three fixes land.**
> A director ruling on the meshgen batch and on the budget documents.
> Its live consequences are the fixes in tools/meshgen/ and the two
> corrections already applied to production/budget.md.


> **STATUS: LOG, 2026-09-01. NOT CURRENT once the batch lands with the three
> named fixes and the two governance corrections below; from then the code,
> its selftest, and production/budget.md are the reading copies and this file
> is their history.**

First builder batch reviewed under Jafar's order that the studio split is
used from here on. Reviewed by reading the code, not a report: the builder
died at its turn limit before writing one.

## What was verified this session, before ruling

- Read all 2,128 lines of `tools/meshgen/meshgen.py`, all 255 of
  `tools/meshgen/blender/clean_lod.py`, the local batch spec, the allowlist,
  `production/budget.md`, `production/week-plan.md`, `production/NOW.md`,
  and `production/queue/010-widen-director-cadence.md`.
- Spot-checked the resident's claims. Meshy and Tripo appear only in the
  BANNED refusal table with the no-purchase reason: confirmed by reading.
  Denominators: confirmed (manifest counts done/skipped/failed/attempted/
  not_attempted/in_spec; licence gate prints its examined count and says in
  words that 0 over 0 is not a pass; probe prints N of M requirements met;
  --series prints n beside min/median/max). Kill switch checked between
  items and between stages: confirmed. I did NOT execute the selftest; this
  role has no shell, so the 86/0 figure is the resident's reading and my
  check of it is that the code of every claimed section exists and asserts
  what the resident said it asserts, accepting case first throughout.
- The standing traps were checked one by one. Resume opens and re-measures
  every file before skipping (outputs_ok), and the selftest proves a
  corrupted output is redone despite a manifest row saying done. The
  wall-clock cap reports STOPPED 12/40 and announces the 28 not attempted.
  Nothing deletes a directory; the publisher stages files by name and drops
  anything outside the repo. The probe's accepting case (a qualifying
  machine) is tested, not just the refusal.
- Allowlist conformance: SOURCE_LICENCES_OK matches the law's CC0 sources;
  the TRELLIS row honestly records that upstream's README names submodules
  under non-MIT licences where the allowlist row says MIT flat, and marks
  every trellis output ship_ok=false until a decision record exists. That
  is stricter than the allowlist's own row and correct under PROCESS
  clause 2. Grepped: no existing decision file anywhere mentions trellis,
  so nothing satisfies that requirement today.
- Premise: props for a late-analog British port town, nothing purchased,
  everything local. No conflict.

## Ruling 1: the batch LANDS, conditional on three named fixes

The work is good. It is the correct answer to the budget problem, it obeys
the instrument discipline this file's constitution demands, and its honest
list of what is unrun (TRELLIS, Blender, both .bat files) is exactly how an
untestable half should be shipped. But three defects were found by reading,
and the first is a gate that this very document would defeat.

**Fix 1, blocker. `find_decision_records` accepts a mention as a record.**
It matches `if key in t and "licen" in t` over every
`game-design/decision-*.md`. This ruling names trellis and licences, so the
moment this file lands, the licence gate would find "a decision record for
trellis" and flip trellis outputs to ship_ok=true, with no record of the
submodule weights licences ever written. The mechanism built so that "we
decided that at some point" cannot stand in for a record is satisfied by
the review paperwork that says a record is still owed. Fix: require an
explicit literal marker (for example a line `TOOL-DECISION: trellis`) and
add both selftest cases: a file that merely mentions the tool and the word
licence must NOT count, and a file carrying the marker must. This ruling
file is a ready-made live rejecting fixture. The fix must land in the same
commit as the batch, because this file lands with it.

**Fix 2. The Tripo ban cannot fire.** The BANNED key is `tripo-service`,
so a spec that writes "Tripo" passes `banned_hits` untouched. The word
boundary regex already protects "tripod", which is presumably what the
suffix was defending against; the key should be `tripo`, with a rejecting
fixture added.

**Fix 3. A refusal cites a document that does not exist.** `trellis_mesh`
tells the person on a trellis-capable machine to "See
tools/meshgen/README.md, which names every step". There is no README.md in
`tools/meshgen/`; the builder evidently died before writing it, and the
selftest's README check is conditional on existence, so the absence is
silent. Either write the short README (install steps, upstream's
Linux-only warning, the exit-code table) or point the message at the probe
report. A refusal pointing at a missing file is a blocked feedback channel
on the one machine that will read it.

Nothing else blocks. Named for the queue, not for this commit: the
`clean_lod.py` target-height heuristic effectively scales by
max(depth, height) and can pick depth on a prop deeper than tall; it is
reachable only through target_height_m, which only the trellis backend
sets, and trellis cannot run on the current machine. It goes on the queue
beside the TRELLIS decision record as "resolve before any trellis run".
Also queued: `_check_lod_ladder` sorts LOD names lexically (wrong past
LOD9), and `write_reports` appends the last 12 log lines with no "+N more"
marker. Small, real, not tonight.

Commit scope: `tools/meshgen/` (the `__pycache__` dirs are gitignored),
the three specs, and this file, in one reviewed commit after the fixes and
a rerun selftest whose count the commit message quotes from the run, not
from memory.

Quality ladder entry: current rung is "pipeline exists, selftested,
unrun on real Blender". Next rung, named: the first real batch on Jafar's
PC over the 37 CC0 props, which is also the accepting case for everything
this container cannot execute. The rung after: materials from ambientCG
through the same licence gate.

## Ruling 2: do NOT resume the dead builder

The constitution says a killed spawn is resumed, never restarted. That
rule exists so work is not paid for twice, and it is what I am obeying by
refusing the resume: the builder's work survives in full, and the only
artifact its death cost was its report. This review is now that report,
at tier-1 depth rather than the builder's own summary. Resuming a
222k-token agent replays its whole history to produce prose nobody needs,
in a week holding about 6 points a day.

The three fixes are new, narrow work, not a restart of the old task: one
fresh tier-3 builder spawn, briefed with the exact function names and the
fixture requirements above, do-not-commit standing, told NOT to re-read
the whole file. The resident reviews the diff, reruns the selftest, and
lands everything in the one commit named in Ruling 1. If the resident
judges any single fix to be genuinely one line, the constitution already
permits hand-applying that one; fix 1 is not one line.

## Ruling 3: the budget and week plan are APPROVED, with two corrections

"Spend Claude on deciding, spend the PC on producing" is ratified as the
week's organising rule. It is the premise applied to money: nothing is
purchased, the tools are local, and the plan correctly names the trap that
the overnight runner spends the same budget later rather than less. The
ordering (governance gate first, local generation second, the timeboxed
engine comparison third) is right, and the stop conditions are mechanical,
legible, and none of them loosens an instrument. NOW.md contradicts
nothing; its refusal to let the stop-hook pressure sweep unreviewed work
into a commit is the constitution applied correctly under pressure.

**Correction 1: derive the 6, in the file.** The printed arithmetic gives
46 points over 5.8 remaining days, which is 7.9 points a day. The docs say
"about 6" without naming the gap, so 6 reads as invented, and this project
does not let its own governance doc do what it forbids every gate to do.
One sentence in budget.md fixes it: 7.9 is the ceiling-exact rate, 6 keeps
roughly a quarter in reserve for estimate error and for the fact that the
series behind all of this is a single dated row. With that sentence the
number is a derived bound with a named margin, and I endorse it. The
per-session usage row Jafar supplies is the right instrument; keep the
series growing.

**Correction 2: the watchdog prompt must exist in the tree.** budget.md
claims "the watchdog prompt points at it". I could not verify that claim:
the prompt lives in the trigger system, which this review cannot read, and
a governance claim that no artifact in the repository can confirm is
exactly the class of assertion this project forbids. The resident pastes
the current prompt text, its enabled state, and the date into a repo file
(production/watchdog-prompt.md, or a section of budget.md) whenever it
changes. Note the standing fact from CLAUDE.md: the watchdog was DISABLED
on 26 Aug for the usage hold; if it has been re-enabled or reworded since,
the tree must say so, because an hourly restart loop in a 6-point-a-day
week is itself a budget hazard.

## For the next session in one line each

- Land: meshgen batch plus fixes 1 to 3, one commit, selftest rerun quoted.
- Spawn: one narrow tier-3 builder for the fixes; the dead one stays dead.
- Queue: trellis height heuristic, LOD name sort, report cap marker,
  TRELLIS decision record before any trellis output ships.
- Docs: derive the 6 in budget.md; watchdog prompt text and state into the
  tree.

Ruling stamp, naming my spawn row verbatim from `.claude/agent-log.tsv`
(`2026-09-01T16:24:47Z	studio-director`):

<!--RULING spawn=2026-09-01T16:24:47Z-->
