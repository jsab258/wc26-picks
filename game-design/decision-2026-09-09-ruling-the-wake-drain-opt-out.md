# Ruling: the wake-drain opt-out, where its decision lives and how strict it is

> **STATUS: LOG, 2026-09-09. NOT CURRENT.** Director ruling at spawn
> 2026-09-09T17:13:31Z on item A1 of the batch ruling, which is follow-through
> on a decision already made today rather than a new question. NOT CURRENT once
> the conditions in section 6 are met and the batch is committed.
> CARRIES OUT: `game-design/decision-2026-09-09-batch-of-fifteen-the-wake-hook-the-rights-table-and-what-he-is-told.md`
> section 8, A1, filed non-blocking for a commit and BLOCKING before the
> executor's first run.

VERDICT: all three APPROVED. The split is right and the hook is not in fact
untested. The strictness is right and it sets a standing rule for this project.
The binary reading is sufficient for a docstring that labels it as a reading,
which this one does, in three places. The wake record faed9289 discharges
honestly, with one residual named and carried, not waved.

WHAT I DID NOT MEASURE, first, because it governs everything below. I have no
Bash tool in this spawn. Every tally in this record (`77 passed 0 failed of
77`, `123 passed 0 failed`, the rung-1 and rung-2 hook transcript, the md5
pair) is the BUILDER'S, read by me as text in a brief, not run by me. I read
the four files. The numbers become conditions in section 6, and the resident
prints them or the batch does not commit. This record's authority is over the
three design questions, not over whether the code passes.

## 1. Where the decision lives: the split is right, and it is stronger than the brief claims

RULED: the hook forwards, the tool decides. Correct, and correct for the
project's stated reason rather than by taste.

`.claude/hooks/wake-drain.sh` lines 158 to 161 build the argument vector and
pass `--wake-drain "$WAKE_DRAIN"` only under `[ -n "${WAKE_DRAIN+set}" ]`, so
never-set and set-to-empty arrive at the tool as `None` and `""`, two facts.
The comparison is one function, `tools/wake-queue.py:is_opted_out` (line 754,
`return value == OPT_OUT`), beside the constant that spells the value (line
234) and the printer that shows it (`env_shown`, line 757). That is the
standing instrument rule applied exactly: measurement arithmetic and
formatting live where the tests run, and the untested layer supplies live
state and nothing else. The hook already refuses to re-type the Stop payload
for the same reason; the opt-out follows the pattern the file already had
rather than inventing a second one.

The brief's premise that "a hook is a file nobody runs a test against" is
FALSE HERE, and that matters. `_run_hook` (line 1155) runs this bash file with
a real payload on stdin and a planted `WAKE_DRAIN`; the accepting case at 1362
and the rejecting case at 1375 are the same record with and without the value.
The hook is the most tested file in `.claude/hooks/`. So the split is not a
retreat from an untestable layer, it is single-siting a comparison that would
otherwise exist twice.

The `15)` arm in the hook's case statement (line 171) stays, for the reason
given there: a reader of the hook can see the opt-out exists. It is not
redundant with the `0|2|11|12|13|14` arm in meaning, only in effect.

THE ONE DEFECT, NAMED AND QUEUED, NOT BLOCKING. The test that the arm exists
is a text assertion on the hook's source, `"    15)" in ...read_text()` (line
1501). It catches the arm being deleted. It cannot catch the arm being wrong,
because BOTH the arm and the unmodelled fallthrough exit 0, and the accepting
case asserts only that exactly one `reason=opted-out` line is present, which a
fallthrough would also satisfy while adding its own `PERMIT-UNASSESSED` line.
The discriminating assertion is one line: on the opt-out run, assert
`PERMIT-UNASSESSED` is ABSENT from stdout. NEXT RUNG, queue item, named: "the
opt-out arm is asserted behaviourally, not by grepping its own source". This
is a ladder rung and not a block because both paths permit, and fail-open is
the deliberate posture of the whole file.

## 2. The strictness: approved, and it becomes the standing rule

RULED: exact, case-sensitive, whole-string, untrimmed `off`, and every other
value including `OFF`, `off ` and the empty string blocks. Approved as
written.

THE RULE THIS SETS, one sentence, for any value anywhere in this project that
disables a guard: A VALUE THAT TURNS A GUARD OFF IS PARSED AS ONE EXACT
STRING, EVERY OTHER VALUE LEAVES THE GUARD ON, AND THE LINE PRINTS THE VALUE
IT ACTUALLY SAW.

The reasoning is asymmetry of failure and visibility, not tidiness. A refused
near miss costs one block that prints `wakeDrain=off_` and is fixed by typing
three lower-case letters. An accepted near miss is a permit nobody intended,
in a session nobody is watching, on a guard whose entire purpose is to not be
silently absent. Recoverable against unrecoverable, which is the same trade
the file already makes for fail-open, pointed the other way. A permissive
parser would also have to decide what `0`, `no` and `none` mean, and each
answer is a second place the value's meaning lives.

The strictness is only defensible BECAUSE the near miss is visible, so the two
halves are one decision and neither ships alone. `env_shown` (line 757)
carries that half: whitespace becomes `_` rather than being stripped, so
`off ` prints `off_` and can never read as the string that permits, and unset
and empty print `(unset)` and `(empty)` rather than collapsing into one blank.
`wakeDrain=` rides EVERY drain line (line 835), not only the opted-out one, so
a session that blocked while somebody believed it had opted out is told which
value the hook saw at the boundary where it blocked. If a future change
removes `wakeDrain=` from the blocking line, the strictness ruled here lapses
with it and must be re-argued.

The denominator discipline holds on the permit path too, and I checked it
rather than taking the brief's word: `due_fraction` (line 505) returns the
words `nothing-measured` both when the directory would not open and when it
holds no record, so an opt-out can never print `0/0` and read as "I declined
to block on a clean queue" when it saw nothing at all. Rule 3b on the one
surface where a clean-looking lie would be invisible.

## 3. The binary reading: sufficient, because it is labelled as a reading

RULED: a code reading of one named build, labelled as such at every site that
carries the claim, is SUFFICIENT for the docstring. It is not downgraded.

The claim is that Stop fires under `claude -p`. The reading is at
`tools/wake-queue.py` lines 112 to 135: version 2.1.266 from `claude
--version`, the only hook-disabling mode naming itself (`--bare`), the Stop
payload built in the same turn-end branch that enforces `--max-turns` which is
the flag the executor passes, and the emitter's only gate being subagents
rather than modes. Three independent grounds, quoted, from one identified
build.

What makes this sufficient is the label, and the label is present at all three
sites: the tool docstring line 133 "NOT OBSERVED, said rather than blurred: no
`claude -p` was run to watch it, here or anywhere in this repository (there is
no CLI in this container)"; the hook docstring line 72; and
`executor.py:session_env`'s docstring line 941. The selftest's NOT COVERED
line carries it into the tally, so the suite that prints a green number does
not print it over the top of an unobserved claim. That is rule 1 satisfied in
the only way it can be satisfied in a container with no CLI: the fact stated
is "this build's code says so", which IS what was checked, and it is not
dressed as "we watched it happen".

Downgrading it further would buy nothing and cost something. There is no
cheaper decisive measurement available here, and the failure mode if the
reading is wrong is not silent: Stop never fires under `claude -p`, the
opt-out is inert, and the executor session is not diverted, which is the
outcome the opt-out exists to produce. A wrong reading here degrades to the
desired behaviour by a different mechanism. That asymmetry is why this one
does not block.

THE OBSERVATION IS STILL OWED, and it is owed at the first moment it can be
taken. Section 6 carries it as a condition on the executor's first real run,
not as a queue item that decays.

## 4. The discharge of faed9289: honest, with the residual named

The record's instruction is "discharge when the executor journal prints the
opted-out line". Read literally, that condition is NOT met and cannot be met
in this container: the executor has never run against a real message, there is
no CLI here, and I found no selftest that exercises `self.record("session-exit",
... wakeDrain=...)` at `executor.py` line 1538. The `session-exit` line with
`wakeDrain=off` on it has not been printed by anything.

What HAS been measured, per the builder, is the strictly more informative half
of that condition: the end-to-end case at `executor.py` 2441 to 2458 runs the
REAL spawn closure inside `run_session` with no injected spawn, against a
shell stand-in for the CLI that prints what it was handed, and asserts the
child received `WAKE_DRAIN=off` and that `res["wakeDrain"]` read back out of
the environment this process built equals it. The journal line's value is that
same field, passed straight through at line 1541. The only thing unobserved is
the formatting of a line whose input is proven.

SO: the discharge is HONEST, and I approve it, on the condition that the
discharge is not read later as "the journal line was seen". It was not. What
was seen is the value that line will carry, produced through the real spawn.
The residual, an observed `session-exit` line carrying `wakeDrain=off` from a
real executor run, is a section 6 condition on the executor's first run,
alongside the Stop-fires observation, because both are answered by the same
single event and neither should be waited for twice.

The dishonest version of this discharge, which is what I checked for and did
not find, would be a record closed on a green tally whose green came from
`session_env` alone. It did not: the accepting case goes through the spawn
production uses. And `_not_started` (line 989) reports `wakeDrain=nothing-
measured`, so a spawn that never started can never contribute a line that
reads as an opt-out.

## 5. The ladder, asked at close

The opt-out: BEST AVAILABLE for the decision surface, given no CLI in this
container. Next rungs, both named and both cheap: the behavioural assertion in
section 1, and the observed journal line in section 4. Neither is blank, so
this aspect is finished rather than researched.

The wake queue as a whole: still FIRST WORKING, unchanged from this morning's
ladder entry, and its other next rung, a read `blocksBeforeDischarge` series,
is untouched by today's work. `blocks: 1` on faed9289 is the first datum that
series will ever have.

## 6. Conditions the resident checks before committing, and one after

Mechanical. Every one of these is a number I did not print.

1. `python3 tools/wake-queue.py --selftest` prints `77 passed, 0 failed` or
   better, with zero failed, and the printed line is quoted in the commit
   message. If the count is below 77, the opt-out cases did not all run.
2. `python3 tools/runner/executor.py --selftest` prints `123 passed, 0 failed`
   with zero failed. If its POSIX stand-in case printed `NOT RUN`, that is a
   skipped end-to-end opt-out case and section 4's discharge argument does not
   hold; say so and do not discharge.
3. `production/wakes/2026-09-09T1600Z-faed9289.wake.txt` carries
   `dischargedAt` set and `blocks: 1`, and no other record's `blocks` moved.
   The rung-1 permit was run on a copy precisely so it could not spend one.
4. `python3 ledger/verify.py` green, footer pasted FROM `ledger/.verify-footer`
   and never from the scrollback.
5. `director_cadence` clears on this record's stamp. If it does not, the stamp
   names a row that is not newer than the reference commit and the fault is
   the stamp, not the gate. Do not touch the gate.

AFTER, and this is the blocking half of A1: BEFORE THE EXECUTOR'S FIRST REAL
RUN, read its journal for the `session-exit` line and confirm two things off
that one event, `wakeDrain=off` on the line, and that a due wake record on
disk at that moment was not blocked. That single observation discharges both
residuals in this record, section 3's and section 4's.

## 7. What this spawn did not do

I ran nothing. I read `.claude/hooks/wake-drain.sh` entire,
`tools/wake-queue.py` at lines 90 to 271, 490 to 530, 700 to 860 and 1350 to
1502, the `WAKE_DRAIN` sites in `tools/runner/executor.py`, the wake record,
and section 8 of the batch ruling. I did not read the rest of either selftest,
so my statement that no test exercises the `session-exit` journal line rests
on a grep for `session-exit` in `executor.py` returning only line 1538 and its
comment; if a test reaches it by another name, section 4's residual is already
closed and the record should say so.

<!--RULING spawn=2026-09-09T17:13:31Z paths=.claude/hooks/wake-drain.sh,tools/wake-queue.py,tools/runner/executor.py,production/wakes/2026-09-09T1600Z-faed9289.wake.txt,game-design/decision-2026-09-09-ruling-the-wake-drain-opt-out.md-->
