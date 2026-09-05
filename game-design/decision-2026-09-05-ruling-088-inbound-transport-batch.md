# Ruling: queue 088, the inbound transport, lands with the wake half named and two holes filed

> **STATUS: LOG, 2026-09-05.** Director ruling at spawn 2026-09-05T11:26:37Z
> on Builder A's diff for queue 088 (`tools/runner/inbox.py`,
> `tools/inbox-read.py`, the inbox half of `tools/runner/telegram-bot.py`,
> `production/inbox/README.md`, runner.md rule 2b, the request section of
> `production/watchdog-prompt.md`) and on the two cards the Producer put at
> the top of `production/decision-queue.md`. NOT CURRENT once the dictated
> edits in section 9 are applied; from then the files are the reading copies.

VERDICT: APPROVED WITH AMENDMENTS. The commit may go once the resident has
applied section 9 and the commit message carries the three counts and the one
series named in section 10. Queue 088 does NOT close with this commit: its
acceptance is a real message from his phone, and that runs on the PC.

## 0. What was read, and what was not run

Read in this spawn, in full: `production/queue/088` with both appended
sections; `tools/runner/inbox.py` (760 lines); `tools/inbox-read.py` (374
lines); `production/inbox/README.md`; `production/watchdog-prompt.md`;
`production/decision-queue.md` lines 1 to 140; queue 090, 092, 094 (to line
40), 095 (to line 60); the 09:02:36Z ruling of today in full;
`production/NOW.md` lines 195 to 255; `.claude/agents/producer.md` lines 80
to 140; `.gitignore` for `production/`.

Read in part, the parts the ruling rests on: `tools/runner/telegram-bot.py`
lines 1 to 70, 304 to 394, 425 to 600, and every line matching
`inbox|awake|asleep|ignored|subprocess`; `tools/pc-watcher.py` lines 690 to
790 (`resync`, `deliver_before_discard`), 789 to 923 (`publish`), 925 to
984 (`one_pass`), plus every line matching `git("add"|clean|status|FETCH_HEAD`;
`ledger/verify.py` lines 905 to 935 (`pc_watcher`) and every line matching
`RULING spawn=`; `.claude/agent-log.tsv` lines 244 to 253.

Counted: call sites of `inbox-read` or `pc-inbox` outside `tools/`: THREE,
all prose (`production/inbox/README.md:15`, `production/watchdog-prompt.md:82`,
`ledger-v2/studio-v2/runner.md:131`), ZERO under `.claude/`. Studio-director
rows in the log: 55; the newest is line 252, `2026-09-05T11:26:37Z`, and line
253 is empty. Stamps in `game-design/` naming any row of today after 09:02: 0
of 0 matches for `spawn=2026-09-05T1`, so 11:26:37Z is unclaimed and is this
ruling's row.

NOTHING WAS RUN. This spawn has no shell. The selftest counts (42, 16, 30,
12, 31) and the commit-gap series (399 gaps, median 10.7, p75 18.4, p90
55.8, p95 90.3, max 7864.6, 324 of 399 under 30) are the builder's, and
section 10 makes the resident print them again before the commit so that the
record beside this ruling is a number somebody printed this turn.

PREMISE CHECK, CLAUDE.md section 0: nothing here touches the game. Standard
library only, nothing purchased, no licence entry, GTA V not cited. The PC
gains a second single-writer branch beside `pc-results`; the session still
pushes only to the work branch. Item 1 of his order is well before item 4, so
the stop-building-studio rule is not in play.

THE SPLIT FOR THIS SPAWN: studio 1, game 0, basis spawns, points unmeasured.

## 1. The whitelist is real and has no bypass (question 1)

The property that matters: `inbox.py` must never run `git fetch` in the
watcher's checkout, because `pc-watcher.resync` (lines 716 to 736) runs
`git fetch -q origin <branch>` and then `git rev-parse FETCH_HEAD` as two
processes and hard-resets to what the second one reads, and
`deliver_before_discard` (lines 775 to 779) would then force-push that HEAD
onto `pc-results`.

What the code does, read rather than reported:

- `git_call` (inbox.py line 122) is the ONLY runtime path to git. Line 129:
  `if not args or args[0] not in ALLOWED: return 126, ...`. The subprocess
  call is line 149 and is reached only past that test. `ALLOWED` (lines 73
  to 75) is thirteen subcommands; `fetch` and `pull` are absent. A global
  option first (`-c`, `-C`, `--git-dir`) is not in the tuple either, so it
  is refused too.
- Of the thirteen, none can write `FETCH_HEAD`: `push` writes the remote and
  the remote-tracking ref `refs/remotes/origin/pc-inbox`, which nothing in
  the watcher reads; `ls-remote` writes no local ref at all; `update-ref` is
  called once, line 481, on `refs/ledger-inbox/tip`; `read-tree`,
  `update-index` and `write-tree` are called only with `GIT_INDEX_FILE` set
  (lines 413 to 440), so the real index is never opened and `.git/index.lock`
  is never taken, which is also what keeps `one_pass` line 937 from reading
  the bot as "busy".
- The second subprocess site, `_fixture_git` (line 534), is selftest
  scaffolding: called from `_repos` and `_selftest` in inbox.py, and from the
  two other selftests. `telegram-bot.py` imports no `subprocess` and its only
  git touches are `inbox._fixture_git` at lines 749 and 760, inside its
  selftest. The runtime path from a Telegram message to git is
  `handle_text` to `file_message` to `inbox.file_and_push` to `git_call`,
  and nothing else.
- The parent comes from `refs/ledger-inbox/tip` (line 64), a ref the watcher
  never names; the effect of the push is read back with `ls-remote` (line
  472) and compared to the commit sha, so "everything up-to-date" cannot pass
  as a push.
- The message file is untracked in that checkout, `resync` says in its own
  docstring that untracked files survive the reset, and `publish` stages a
  NAMED list (lines 809 to 868 plus `casting_files`) with `git add -f --
  *here`, so an inbox file can never be swept onto `pc-results`. No
  `git clean` exists in pc-watcher (0 matches).

One consequence of the whitelist the builder named and I accept as a known
tail: with no local tip (a fresh clone) the branch is REWRITTEN from what the
PC's disk holds (lines 414 to 419, `replaced=True`), because without a fetch
the bot cannot chain onto a remote commit whose objects it does not have.
Messages on the branch that the container never read would be lost in that
case. The window is a re-clone while the studio is asleep; the watcher resets
rather than re-clones, and section 6 makes the container's copy durable. Named
in NOW.md by section 9, not fixed.

RULING: the guard is real, it is tested on both outcomes (lines 642 to 651),
and the design constraint holds.

## 2. The throwaway-repo substitute for `--once` (question 2)

The builder was right not to force `pc-watcher.py --once` here: it would have
hard-reset a checkout carrying its own uncommitted diff (rule 5). The
substitute measured the property the pass depends on, on real repositories in
the shape his PC is in (bare origin, a `watcher` clone standing on the work
branch with the remote-tracking ref set, lines 545 to 566): HEAD unchanged
after a push (line 663), nothing staged and every new status line `??` (line
673), no `index.lock` (line 676), HEAD equal to the fetched branch sha, which
is exactly `deliver_before_discard`'s short circuit at line 767 (line 684),
and the work branch on the remote unmoved (line 691).

RULING: adequate to COMMIT on. The pass's three steps read HEAD, the index
lock and the branch sha, and all three were asserted on the real shapes. Not
adequate to CLOSE on. The real pass is owed by the PC channel, not by a hand
on the PC: nobody there runs commands, and the watcher loop is already
running. The artifact is the first `pc-results` commit whose committer instant
is later than the first `pc-inbox` commit, which proves `resync`,
`deliver_before_discard` and `publish` completed with the inbox commit present
in that clone. The resident writes both instants into 088's file when it
moves to done, and 093 records the same round trip.

## 3. The trigger line, and whether a recorded copy is a good idea (question 3)

RULING: THE RESIDENT SETS IT IN THIS SAME COMMIT. It is dictated text applied
to a trigger, which is the resident's own hand under the studio split, and it
costs no builder pass. Until it is set the only overnight wake does not read
the inbox, which is rule 6 sitting on the one call site that matters. The
sequence is: read the daily trigger's prompt as it stands, append the line in
section 9.1, update the trigger, paste the WHOLE prompt as set into the
section with STATUS LIVE and the instant, then commit. Reading it to append
one line means the full copy can be recorded today; 095's builder then only
adds the brief tool's name to it. If the trigger cannot be updated in this
turn, the section stays NOT YET SET, NOW.md says so in one line, and the
commit still goes: the transport is useful while a turn is running.

On the copy itself. It IS a second copy and it WILL drift without a check;
the file says so at line 20. It is still right to keep, because the
alternative was tried on 2026-09-01 and failed (budget.md asserted what the
prompt said with nothing anyone could open). The next rung, which costs
nothing and rides 095's recording: the prompt's own last line instructs the
session to compare what it is reading against the recorded section and write
the difference into NOW.md before anything else. A session reading the prompt
holds both texts, so drift is detected once a day by the reader that suffers
from it. Section 9.1 dictates that line.

## 4. `AWAKE_WITHIN_MIN = 30` (question 4)

The series exists and its statistic is named: 399 gaps, and the bound sits
where 324 of them (81 percent) fall under it. The limitation is stated in the
code (lines 89 to 91): a commit-gap series is not a commit-age series. The
age distribution is length-biased, long gaps own more clock time, and the
series mixes asleep nights (the 7864-minute maximum is five and a half days)
with working gaps, so the true false-ASLEEP rate at a random awake moment is
higher than 19 percent. The direction is the safe one: false-ASLEEP costs him
nothing, and the reply says "If it is only mid-step you will hear sooner."

The costly error, false-AWAKE, is bounded by construction: it can only occur
in the 30 minutes after the last commit of a session. Lowering the bound
shrinks that window and raises false-ASLEEP during long builder spawns.

RULING: the measured proxy stands, with three conditions. The reply says
"looks" and names its basis (it does, `studio_sentence` lines 321 to 336).
The resident re-prints the series this turn (section 10) so the bound has a
printed series beside it in the commit that lands it. And 094 replaces the
proxy with the studio saying so itself. Refusing to guess would be worse: the
`unknown` branch already exists for the no-ref case, and using it always
would throw away the one useful bit while keeping the same worst case.

One rung folded forward rather than taken now: the AWAKE branch names no
worst case, and the selftest asserts it must not (line 630). Given the
bounded false-AWAKE window, one sentence ("if it has in fact just stopped,
the worst case is the next wake at 04:00 UTC") would close the costly error
entirely. It is a string plus a flipped assertion, so it is builder work and
rides the same authorised pass as section 8's fix.

## 5. Three selftests decay unwatched (question 5)

True and confirmed: `ledger/verify.py` runs `pc-watcher.py --selftest`
(lines 920 to 934) and nothing for `inbox.py`, `inbox-read.py` or
`telegram-bot.py`. The bot was already unwired when 067 landed on 2026-09-04,
so this commit extends the gap by one module and one tool rather than opening
it.

RULING: rides 095's pass, which is already inside verify.py (the 079 counter)
and is item 1c, authorised. One checker each, parsing the count line the
tools already print (`N passed, M failed, K case(s) run`), red on any
failure or on no count line. Not a blocker: the compensating control until
then is section 10, the three selftests run by hand this turn with counts in
the commit message. If it does not fit 095's session it returns to the queue
under a number the resident allocates (section 9.9).

## 6. The record does not persist by itself (question 6)

`inbox-read.py` writes delivered files untracked (line 175) and says so
(line 237). `production/inbox/` is not gitignored (the only `production/`
entries are `logs/` and `scratch/`). `pc-inbox` is force-pushed and its
history is disposable, and section 1 names the case where it is rewritten, so
the work branch is the only durable record of what he said.

RULING: two halves. Today, a process rule: delivered files are staged BY NAME
into the next batch commit by the resident, written into rule 2b and the
README (sections 9.2, 9.3). The reader must not commit them itself: it runs
at dispatch boundaries in a tree carrying builder work, and one reviewed
commit per batch is the standing law. The gate, so the rule cannot be
forgotten: verify.py refuses a commit while `production/inbox/` holds an
untracked message file, printing `inboxUntracked=N/M` over the files matching
`NAME_RE`, and "nothing measured" when the folder is empty. That is verify.py
work and rides 095's pass with section 5. Out of 088's scope: its acceptance
never says committed, and this is a named gap, not a re-brief.

## 7. The two cards, and the gap the Producer filed (question 7)

Not using a pop-up question was RIGHT. Item 2 of his order says the session's
pop-ups become cards, and a pop-up is exactly the thing he retired. Telling
him in the terminal that the cards exist was also right: it is the only
channel that exists today, and item 2's own words say the remedy is a gap
filed, which this spawn is.

What closes it is already ordered: 089 (the sender, second in the order)
puts a card on his phone as text with its options lettered; 090 (third)
adds the buttons and the fold. The inbound half of the ruling channel exists
from this commit: he can type "card 1: A" to the bot, it lands in the inbox,
and the resident folds it by hand until 090. So the gap is one-directional
and closes when 089 lands, which is the next pass.

THE DEADLINES. Card one defaults to C and spends nothing, so its deadline
stands as written. Card two's default acts, and a default that acts on a card
nobody delivered is a studio decision dressed as his. The 09:02 ruling set
default A for a reason that still holds (the exposure already exists), and I
do not reverse it; I condition it. RULING: the default acts on 2026-09-07
only if the card has reached him by then through a channel with a receipt
(089's message id) or by his own acknowledgement in the session, and at
least 24 hours have passed since; otherwise the deadline moves day by day
with delivery. Section 9.5 dictates the sentence.

TWO CLAIMS IN THE CARDS THAT RUN AHEAD OF THEIR EVIDENCE, corrected in
section 9.5. Card one says "Transport works: what you send arrives." The
accepting case has not run; the transport is built and his first message is
its test, and the card must say that (rule 1). Card one's evidence link for
the shut webhook route points at queue 092, which only refers onward; the
measurement (`http_status=401`) is in queue 088's appended section. Card two
says "so Pages works"; the measurement was that the repository is public, and
097 is what proves Pages. "Is available" is what was measured.

## 8. Two things the seven did not ask, one of them a hole in "never dropped"

(a) `Bot.skip_backlog` (telegram-bot.py lines 304 to 319) is called at every
start (line 583) and discards every update that arrived while the bot was
not running, counting them in the PC window only. Under 067 that was right:
replaying three days of budget answers would have been noise. Under 088 the
population changed: those updates are now his inbound messages. A message
sent to a closed bot window (his PC asleep, the window closed) is never
filed, never on the branch, and he is not told. The docstring's "it is never
dropped" (line 23) is true of a failed push and false of this case. It is
the night case item 1 is about.

RULING: not a blocker for this commit, because the fix is builder work (file
the backlog's text messages from the configured chat with their own Telegram
`date`, reply once with the count, apply none of them as budget answers, with
both outcomes in the selftest) and 088's one session is spent. It rides
Builder C's pass, 090 with 104, which is the bot's input handling in the same
function, and is authorised. Today the hole is named where it will be read:
the bot's docstring (9.4), the README (9.3) and NOW.md (9.8). Fallback number
requested in 9.9.

(b) The exception path in `file_message` (lines 344 to 350) tells him the
message is NOT saved. `git_call` never raises, so the only realistic raiser
is `write_message` before the file exists, and the sentence is accurate for
it. Noted, nothing to do.

(c) `inbox-read.py` prints the NOTE about reading a stale copy only for
`unreachable`; a `no-branch` answer with a stale tracking ref (the branch
deleted remotely) would read the old copy without one. A tail; noted for
094's builder, not dictated.

## 9. Dictated edits, applied by the resident before the commit

9.1 `production/watchdog-prompt.md`, the 088 section. The line to set in
`trig_013itgDeay6t41BHEmaYFbAj`, replacing the builder's draft:

    FIRST, READ THE INBOX: `python3 tools/inbox-read.py`. Anything Jafar sent the bot is a dated file on the `pc-inbox` branch and this is the only thing that ever looks at it. Answer him through the Producer before planning the day, and stage the delivered files by name in the day's first commit.

And as the prompt's LAST line:

    THIS PROMPT IS RECORDED in production/watchdog-prompt.md. If what you are reading differs from that section, write the difference into production/NOW.md before anything else.

Then replace the section's STATUS with "LIVE, set <instant>Z" and paste the
prompt as set, whole. If the trigger cannot be updated this turn, leave the
STATUS as it is and add to NOW.md: "The daily trigger does not yet call the
inbox reader; the overnight wake reads nothing until it does."

9.2 `ledger-v2/studio-v2/runner.md`, rule 2b, append: "The files it delivers
are UNTRACKED until committed. Stage them BY NAME in the next batch commit:
`pc-inbox` is force-pushed and disposable, and the work branch is the only
durable record of what he said."

9.3 `production/inbox/README.md`, after the "How to read them" section, add
two sentences: "Delivered files are untracked until the next batch commit
stages them by name; the work branch is the record, `pc-inbox` is the
transport. A message sent while the bot on the PC is NOT running is skipped
at the bot's next start, counted in the PC window and not filed; until the
fold in queue 090's pass lands, the bot's silence is the signal to resend
after its opening message."

9.4 `tools/runner/telegram-bot.py`, docstring, after line 23 ("it is never
dropped."): "A message that arrives while this bot is NOT running is the
other case: `skip_backlog` counts it at the next start and does not file it,
so it is lost to the inbox until the fold in queue 090's pass lands."

9.5 `production/decision-queue.md`, card one: replace "Transport works: what
you send arrives." with "The transport is built and lands today; the first
message you send the bot is its test." Point the link under "was tested and
is shut" at
`production/queue/088-the-inbound-path-from-his-phone-to-this-session.md`.
Card two: replace "so Pages works" with "so Pages is available". Append to
its DEFAULT line: "The default acts only once this card has reached you, by
the bot with a receipt or by your own word in the session, and 24 hours have
passed since; until then the deadline moves with it."

9.6 `production/queue/088`, status line, append: "Container half landed
2026-09-05 (ruling
game-design/decision-2026-09-05-ruling-088-inbound-transport-batch.md).
Stays open until the accepting case on the PC: the first real message's
`inboundLatencySec` line committed in the tree, and a `pc-results` commit
whose committer instant is later than the first `pc-inbox` commit, both
instants written here."

9.7 `production/queue/095`, body, one paragraph: "FOLDED IN BY THE RULING OF
2026-09-05 (088 batch), section 5 and 6: `ledger/verify.py` gains one
checker each for `tools/runner/inbox.py --selftest`,
`tools/inbox-read.py --selftest` and `tools/runner/telegram-bot.py
--selftest`, parsing the count line each prints and red on any failure or no
count line; and one gate that refuses a commit while `production/inbox/`
holds an untracked message file, printing `inboxUntracked=N/M` and "nothing
measured" on an empty folder. If it does not fit this session it returns to
the queue under its own number."

`production/queue/090`, body, one paragraph: "FOLDED IN BY THE RULING OF
2026-09-05 (088 batch), sections 4 and 8: `Bot.skip_backlog` files the
backlog's text messages from the configured chat with their own Telegram
`date`, replies once with the count, applies none of them as budget answers,
both outcomes in the selftest; and the AWAKE branch of
`inbox.studio_sentence` names the next wake as the worst case, with line 630's
assertion inverted. If it does not fit this session it returns to the queue
under its own number."

9.8 `production/NOW.md`, under item 1, two lines: "088's container half is
in; the transport has two named holes until 090's pass: a message sent while
the PC bot is off is skipped at its next start, and a fresh clone of the PC
checkout rewrites `pc-inbox` from its own disk." And the trigger line from
9.1 if it could not be set.

9.9 ASKED OF THE RESIDENT, not chosen here: two queue numbers, allocated only
if the folds in 9.7 do not fit their passes. One for the verify.py wiring
and the inbox gate; one for the backlog filing and the AWAKE worst-case
sentence. Until then they are folds inside authorised passes, as 079 was.

## 10. The commit

The message is written to a file, never an unquoted heredoc, and carries,
printed this turn and not copied from the builder's report:

- `python3 tools/runner/inbox.py --selftest`, `python3 tools/inbox-read.py
  --selftest`, `python3 tools/runner/telegram-bot.py --selftest`: the three
  count lines as printed.
- The commit-gap series behind `AWAKE_WITHIN_MIN`, from
  `git log -400 --format=%ct HEAD` piped through a sorter that prints the
  gap count, median, p75, p90, p95, max and the count at or under 30
  minutes. The numbers will differ slightly from the builder's because HEAD
  has moved; that is fine, the point is a printed series beside the bound.
- `python3 ledger/verify.py` green, footer pasted from
  `ledger/.verify-footer`.

Then the batch: the builder's files, the edits of section 9, this record.
Nothing under `production/inbox/` yet, because no message has arrived.

QUALITY LADDER. First working, not best available, and the rungs are named:
the wake half is 092 then a cadence he sets; the awake proxy is 094; the
"never dropped" claim is 090's fold; the record's durability is 095's gate;
the prompt copy's drift is the self-check line in 9.1. The transport itself
has one blank rung, the no-tip rewrite, which is a research question (can a
bot that may not fetch ever chain onto a branch it did not write) and is
named in NOW.md rather than answered.

<!--RULING spawn=2026-09-05T11:26:37Z-->
