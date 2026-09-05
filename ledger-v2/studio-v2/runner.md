# The Runner: autonomous multi-session operation (overnight and beyond)

Principle: sessions are disposable workers, the repo is the memory, a night is a loop of fresh sessions. No session should ever live long enough for auto-compaction to matter; process exit replaces /clear. Jafar never manages context.

## Components (built during the Phase 0 scaffold)

1. Work queue. production/queue/ holds task files NNN-slug.md, each with: pipeline/line, spec reference, acceptance checks, max_sessions. Folder is the state machine: queue/ to active/ to done/ or blocked/. A planner session decomposes roadmap milestones into queue tasks; tasks obey the one-brief-one-deliverable law.
2. Dispatch prompt. tools/runner/dispatch.md, fixed text: read CLAUDE.md, canon.md, current roadmap state and your task file; do the one task; verify against the gates; commit on the night branch; move the task file to done/ with a result note (or blocked/ with a reason); update your resumable state file if unfinished and enqueue a continuation task pointing at it; then exit. Never wait for input.
3. Loop script. tools/runner/run-night.ps1 (plus a run-night.bat wrapper for one click): while queue non-empty, launch claude -p with the dispatch prompt, generous --max-turns, logging each iteration to production/logs/night-YYYYMMDD/. Caps: max iterations, wall-clock limit, and a STOP file checked between iterations as the kill switch.
4. Failure policy. Two consecutive failures on the same task move it to blocked/ with the logs linked; the loop moves on. Blocked items surface in the morning brief, never silently retried all night.
5. Git discipline. Each night runs on branch night/YYYYMMDD (worktrees if agents run in parallel). An integrator task at the end of the queue merges only what passes CI and the standing gates. Main is never written directly by the runner.
6. Continuation, not compaction. A task too big for one session writes its state file and re-enqueues a continuation. Compaction is a backstop only: SessionStart hook rehydrates canon plus roadmap plus task state; PreCompact hook dumps session state to a file first. If PreCompact fires more than rarely, the tasks are cut too large; fix the planner, not the window.
7. Permissions. .claude/settings.json pre-approves the runner's tool allowlist so nothing prompts interactively. The runner may never: delete outside the repo, force-push, touch main, spend above the night budget, or reach network destinations beyond the configured allowlist.
8. Morning brief. The final queue item every night generates the brief and the decision queue per operations.md. Jafar wakes to: landed, blocked, numbers, decisions needed.

## Sizing rule
Tasks are sized so a typical session finishes one comfortably inside its turn cap. When in doubt, cut the task smaller; many small verified pieces beat one large unverified one, and the throughput ledger counts verified pieces anyway.

## Brief delivery and the guarantee chain
Reporting never depends on the health of what it reports on, and the default needs nothing outside this machine.
1. Rich brief: the final queue task (LLM) writes production/briefs/night-YYYYMMDD.md per operations.md.
2. Fallback brief: if that session fails, the loop script composes a mechanical brief with zero model calls: queue folder counts (done, blocked, untouched), night-branch git log, gate results, token ledger, tail of the last failing log.
3. Exit-path delivery (runs on success, failure, or kill switch): write the brief, copy it to production/briefs/latest.md, fire a Windows toast if the machine is awake.
4. Morning surfacing: the SessionStart hook prints the latest brief when Jafar opens Claude Code, unprompted.
5. Scheduling: the scaffold registers Windows Task Scheduler entries (via schtasks) for the nightly runner start at a configured time, so nights need no manual trigger. run-night.bat stays as the manual option; the STOP file stays as the kill switch. Claude Code writes and registers these; Windows executes them.
Escalation is TELEGRAM, ruled by Jafar 2026-09-03 (the Director's Console). No email and no n8n: both are struck from this document rather than left as options, because an option nobody chose is a decision nobody made. The bot runs on the PC and carries Blocking pushes, the morning brief, gallery images and decision cards; everything below Blocking is pulled rather than pushed. Off-machine dead-man alerting for the PC-died-overnight case stays wanted and is now the bot's silence rather than a third-party ping.
Worst case by design is never a missing brief; it is a fallback brief, or a machine you can see is off.

---

## The auto-mode operating manual, carried from CLAUDE.md (2026-09-01, task 013)

Moved intact when CLAUDE.md was cut to standing rules plus pointers. This is
the v1 loop: how it starts, how it stops, the four rules that make it
continuous, the watcher recipe and why the cron is only a watchdog.

READ IT AS OPERATING KNOWLEDGE, NOT AS THE CURRENT ROSTER. The queue it names
is game-design/queue.md, which marked itself superseded on 2026-08-31; the
live queue is production/queue/ with production/NOW.md. The scheduled-report
ceremony inside it was retired by Jafar on 22 August and the text says so.
What survives and is still load-bearing: watch by ancestry and never by branch
movement, capture the sha before dispatching, batch changes per dispatch, one
build at a time, and never end a turn without arming something.

THE WATCHDOG PARAGRAPH BELOW SAYS "IT IS DISABLED RIGHT NOW, 26 Aug". True
when written, false since 2026-09-01 16:00Z, when it was re-enabled with a
rewritten prompt. Corrected here rather than inside the moved text, per the
carry rule above. The live state and the prompt as set are in
production/watchdog-prompt.md, which is dated and wins over this file.

<!-- moved verbatim from CLAUDE.md lines 1235-1510 on 2026-09-01, task 013 -->

## AUTO MODE — THE CEREMONY IS RETIRED, THE WORK IS NOT (22 Aug, Jafar)

His words: *"yeah drop the updates, we said no more automode (you can still
keep working as discussed, judt drop the automode rules)"*. What that
changes and what it does not, decided the day he said it so no future
session re-derives it differently:

- **SCHEDULED UPDATES ARE OFF.** No six-a-day reports, no report slots, no
  header-line format, no silence-vs-slot arithmetic. Message Jafar when
  something genuinely needs him, when he asks, or when a deliverable he is
  waiting on (a named build, a settled visual pass) is ready — with a frame
  when a frame says it better. Nothing on a clock.
- **THE CONTINUOUS WORK CONTINUES**, in his priority sequence (visual →
  voices/speech → playtest → feedback fixes → roadmap; see rule 3 below).
  Everything operational in this section — the queue discipline, the
  ancestry watchers, batching, one-build-at-a-time, verify-before-commit,
  stills before gates — stays in force: those are working rules, not the
  ceremony he retired.
- **The watchdog trigger is the restart mechanism only**: the container is
  ephemeral and a dead chain with no watchdog is a silently stopped project,
  which is the opposite of "keep working". Its prompt no longer carries
  report instructions.

  **IT IS DISABLED RIGHT NOW — 26 Aug, and this sentence used to read "stays
  enabled", which was true when written and false the moment it mattered.**
  Jafar put the project on a usage hold to Monday afternoon (85% of the
  weekly limit spent in under two days) and told me to stop. Disabling it is
  step 1 of STOPPING, below, and it is the step that makes a stop real: the
  prompt says *"take the next item from `game-design/queue.md`"*, so leaving
  it on would have restarted the loop hourly through the hold and looked
  exactly like the stop being ignored. **To resume: STARTING IT, step 1.**

  The reason this paragraph is corrected rather than quietly edited is that
  it is the file's own thesis happening to the file. A rules doc that says
  "the watchdog is enabled" while the watchdog is off is a claim with no
  instrument, read by every session, and it would have sent the next one
  looking for a fault in a loop that was deliberately parked.

The section below is kept as the operating manual for the loop; read
"report" anywhere in it as retired.

Jafar's original framing, for history: continuous autonomous building,
around the clock. *"non stop, no idle time."*

### Starting it

1. Enable the watchdog: `update_trigger` on **`trig_01EA7ybQTcsiFyrTryptqVUi`**
   with `enabled=true`. Its prompt carries the current work order — read it
   rather than re-deriving one.
2. Begin working immediately. Do not wait for the watchdog to fire; it is not
   the thing that drives the work.
3. Arm something before the turn ends (see below).

### Stopping it

1. `update_trigger` on the watchdog with `enabled=false`.
2. Kill any background watchers (`TaskStop`, or `KillBash` on a running poll).
3. Delete any pending `send_later` with `delete_trigger`, or it will wake the
   loop after you were told to stop.
4. Confirm the working tree is clean and pushed. Auto mode assumes it can be
   interrupted at any moment, so it must never hold uncommitted work.

All three steps matter. Disabling the cron alone leaves a background watcher
that will re-invoke the loop, and it will look like the stop was ignored.

### The four rules that make it continuous

**1. Work until genuinely blocked, not until one task is done.** A turn can
carry hours. Finish something, pick up the next thing, keep going.

**2. Never wait on CI.** Only the Game layer needs the ~28-minute Windows round
trip. Core, CoreTests, the measurement tools, the docs and every Python tool run
here in seconds. Dispatch the build and start the next non-CI item in the SAME
turn. A build in flight is a reason to switch tasks, not to stop.

**2b. READ THE INBOX AT EVERY DISPATCH BOUNDARY AND AT THE TOP OF EVERY TURN.**
One command, one fetch, seconds:

    python3 tools/inbox-read.py

    The files it delivers are UNTRACKED until committed. Stage them BY NAME
    in the next batch commit: `pc-inbox` is force-pushed and disposable, and
    the work branch is the only durable record of what he said.

That is the container half of the inbound path (queue 088). Anything Jafar
typed into the bot on his phone is a dated file on the `pc-inbox` branch about
a minute later, and this is the only thing that ever looks. It prints his
words, `delivered=N/M`, and `inboundLatencySec` measured from Telegram's `date`
field to the PC's commit instant; with nothing on the branch it prints the
words "nothing measured" beside `delivered=0/0`, so an empty inbox never reads
like a broken reader. The boundaries that matter are the same ones rule 2 is
about: before a spawn, after a spawn returns, and before ending a turn. THE
STUDIO CANNOT BE WOKEN BY A MESSAGE. While no turn is running his message
waits for the daily trigger at 04:00 UTC, up to 24 hours; the bot tells him so
in its reply, and closing that gap is queue 092.

**`game-design/queue.md` is what you pick up.** This rule was already written,
in these words, and I broke it four times in one afternoon — twenty, thirty-two,
nineteen and twenty-eight minutes of nothing landing, each one right after a
dispatch. The rule was not forgotten; the problem is that *the moment after a
dispatch is a decision point*, and re-deriving priorities from a 400-line
roadmap at the end of a long turn is enough friction to lose to. So the next
items are written down BEFORE the dispatch and taken from the top afterwards,
with no judgement required at the exact point where judgement was failing.
Keep it current: a stale queue is worse than none, because it looks like a plan.

**AND IT MUST NOT BE ABLE TO EMPTY.** The queue fixed the gaps for exactly one
hour — eighteen commits, longest gap eight minutes — and then produced three
more of 21, 28 and 28 minutes. Not because the rule was forgotten. Because the
queue RAN OUT, and its own instruction guaranteed it would: *every item sized to
fit inside one build round trip* means an hour of good work consumes the list.
An empty list reads exactly like an empty afternoon, and the two have completely
different next actions.

So: a `## Standing work` section that never empties — unbuilt milestones, a
system to read for false comments, a still to turn into a number. When `## Now`
has nothing startable, **decompose a standing item into it. That is a refill
signal, not a stop signal.** `tools/queue-check.py` runs inside `verify.py` and
fails the commit when fewer than three items can be started without waiting on
CI, so the queue running thin is something you are told before it costs an hour
rather than something you notice afterwards.

**3. Be woken by the event, not the clock.** Arm it with Bash
`run_in_background: true`, which re-invokes you within seconds of it exiting.
**Watch for a build that CONTAINS the commit you care about** — not for the
branch to move, and not for a run named after the sha you dispatched:

    SHA=$(git rev-parse HEAD)
    for i in $(seq 1 100); do sleep 30
      git fetch -q origin claude/game-dev-ai-automation-2h67ix 2>/dev/null
      git merge-base --is-ancestor "$SHA" origin/claude/game-dev-ai-automation-2h67ix 2>/dev/null \
        && git pull -q --no-rebase origin claude/game-dev-ai-automation-2h67ix 2>/dev/null
      python3 tools/landed.py --contains "$SHA"; rc=$?
      [ $rc = 0 ] && exit 0          # landed WITH an answer
      [ $rc = 3 ] && exit 3          # landed with NOTHING — re-dispatch, do not wait
    done; echo "timed out"; python3 tools/landed.py --contains "$SHA"

**`SHA` IS THE COMMIT AT DISPATCH, NOT THE COMMIT WHEN YOU GET ROUND TO ARMING
— AND THE RECIPE ABOVE DOES NOT SAY SO, WHICH COST 5 AUGUST A DEAD WATCHER.**
The paragraphs below are all about the ancestry test defeating a forgery. This
is the other end of the same problem and it survived both rewrites: `git
rev-parse HEAD` is evaluated when the watcher is ARMED, so dispatching, then
doing another twenty minutes of work and five commits, then arming, watches for
a commit the runner could not possibly have checked out. It waits the full
fifty minutes and reports nothing, and NOTHING ABOUT IT LOOKS BROKEN — the
output is the same "not yet" line a healthy watcher prints.

Two ways out and the second is better. Capture `SHA=$(git rev-parse HEAD)`
BEFORE the dispatch and arm from that variable. Or read the run's real
`head_sha` back from `actions_list` after dispatching and watch THAT — which is
the only version that cannot be wrong, because it asks the runner what it
actually took rather than guessing from local state. It also tells you
immediately when the runner grabbed a commit newer than yours, which is the
case the whole ancestry test exists for.

**EXIT 3 IS NEW AND IT IS THE ONE THAT WAS COSTING HALF-HOURS.** A build whose
licence activation fails, or whose Game layer will not compile, still commits a
verdict — so the ancestry test says LANDED, correctly, and the old recipe
reported success. On 4 August I read one of those as an answer and went looking
for numbers that were never written. "The build carried your change" and "the
build measured anything" are different facts, and only the second is what a
watcher waits for. `landed.py` now separates them, and prefers the newest run
that MEASURED something over a newer one that did not — the first version
returned on the newest containing run whatever it held, which hid an available
answer behind an empty build the very first time it was tested.

**BOTH OBVIOUS VERSIONS ARE WRONG AND I SHIPPED BOTH INTO THIS FILE.**

The first watched `git ls-remote` for the branch head to change, reasoning that
the job commits stills so the branch advancing IS the build landing. True when
nothing else is pushing. In auto mode I push constantly, and it fired forty
seconds later on MY OWN COMMIT while the verdict still named the previous build.

The second — the one that stood here until 4 August — matched the verdict's
first line against the sha I dispatched. That fixed the forgery problem and
introduced a quieter one: **`workflow_dispatch` does not pin a commit.** It
takes a BRANCH, and the runner checks out whatever that branch points at when
it STARTS. Push twice in the ten minutes a job waits for a runner and it builds
the third commit, not yours.

Measured, not suspected: four builds dispatched at `aa0e906`, `d5b3741`,
`bdcbe3f` and `69e03a6`, and **not one of those four shas was ever built**. The
runs that came back are named after later commits, two of them made by the CI
job committing its own stills. Every watcher armed on those four was waiting
for a file that could not appear — and none of them looked broken, because they
had fired correctly on earlier runs where HEAD happened not to move. A watcher
that works often enough to look right is worse than one that never works.

The question was never "is there a run named X". It is **"is there a run whose
commit CONTAINS X"**, which is an ancestry test and cannot be forged by my own
pushes either: my commits are not descendants of themselves-plus-CI's-work
until CI does the work. `tools/landed.py --contains` is that test, and it names
which run answered so the next step does not need a second lookup.

Cap it around 50 minutes so a dead run cannot hang the loop. If something else
blocks you, `send_later` goes down to one-minute granularity.

**4. Never end a turn without arming something — AND ARMING IS NOT ENDING.**
No watcher, no `send_later`, no pending work means the project has silently
stopped. This is rule 8 with a mechanism attached.

But arming a watcher is the *precondition* for ending a turn, not permission to
end one, and reading it as permission is what survived both repairs. Measured
after the second fix: nine commits in seventy-four minutes with gaps of 2, 5, 3,
**30**, 12, 1, 10, 11. The thirty was a dispatch, a watcher, and a stop — with
four standing items sitting unused on the queue.

So the mechanisms built for this solve the wrong half. `queue-check` guarantees
work is AVAILABLE; nothing can make it be CONSUMED, because no check inside
`verify.py` can see a turn boundary. Availability was never the binding
constraint.

**The rule, and it is a rule because it cannot be a tool: a turn ends only when
nothing is startable.** With a standing section that cannot be completed, that
state does not exist — so after arming a watcher, open `queue.md` and start the
next thing in the same turn. Every time. The watcher is what makes the result
reachable later; it is not the work.

### Jafar asked why twenty-four hours looked like almost nothing

4 August, and he was half right, which is the half that matters. Measured
before answering rather than after: **347 commits and 133 builds in the day**,
so the loop was not idle. And **about a third of those commits were about my
own MEASUREMENTS being wrong rather than about the game**, and **7 of the last
30 builds returned no answer at all** — a compile error or two builds fighting
over the same Unity licence seat, half an hour each, nothing to show.

The one thing he could actually see took the whole day to arrive: the street
went from smooth featureless dummies to people with skin, clothes and a walk.
Everything else was invisible to him, and a lot of it was invisible because it
was me arguing with my own instruments — one nameplate counter has now given
four contradictory readings and no player will ever see it.

**Four rules follow, and they are his, not mine.**

**1. BATCH THE BUILD.** Several changes per dispatch, not one question per
dispatch. A round trip is ~28 minutes whether it carries one change or six.
And **ONE AT A TIME**, which is where the evidence has now landed. The licence
seat is a single Personal activation, and every level of concurrency has cost a
build: four dispatches killed two, three killed one, and TWO killed both —
15:23 on 4 August, `c7329a3` and `2cfe851`, each reporting "first licence
attempt: failure, second: failure". That is three data points in one direction
and none the other way.

Parallel dispatch was never wrong about the goal — it was answering "how do I
stop waiting half an hour per question". Batching answers that better and
costs nothing: six changes in one build is one round trip, six builds is six
chances at the seat. So the two rules are a pair, and the batching one is what
makes this one affordable.

**2. A MEASUREMENT THAT CONTRADICTS ITSELF TWICE GETS DELETED, NOT EXPLAINED.**
The rule this replaces was "measure again with a better instrument", and it is
how one counter consumed four round trips. The second contradiction is the
signal: at that point the cheapest correct move is to delete the number and
keep the behaviour fix, because a metric nobody can interpret is worth less
than the hours it takes to interpret it. Exception, and only this one: the
number is load-bearing for a gate that is currently red.

**3. ORDER THE QUEUE BY JAFAR'S SEQUENCE, THEN BY WHAT SHOWS ON SCREEN.**
His order, 22 Aug, verbatim: *"1. visual, 2. voices/speech, 3. playtest,
then feedvack/fixes and then continue w roadmap."* The visual bar
finishes first, then live speech readiness for his Windows session, then
the playtest itself, then whatever it surfaces, and only then the rest
of the roadmap. Within a stage the old rule holds: not by what is open, not by
what is nearly finished, not by what I happen to be holding in my head. The
standard is immersion first, so the top of `## Now` is the item a player would
notice, every time. Everything else is below it whatever its state.

**4. EVERY REPORT CARRIES A PICTURE.** He asked "is it just not visible to me"
about a day whose single biggest change is a JPEG sitting in the repository. A
report that describes the street without showing it is making him take my word
for the one thing he can check himself. Send the noon frame with the update —
and where something changed, send the before beside it.

`tools/report-frame.py` finds both, because a rule that depends on remembering
to go and look is a rule that decays and this file is mostly a list of things
that decayed. It walks back to the last commit whose verdict says a sim
actually RAN — a build that died on a licence seat still commits, and one on 4
August committed six stills it could not have made — and it refuses to hand
over a frame rather than offering a stale one. Tested both ways: it finds the
pair on today's repository, and with the verdicts hidden it says do not attach
a picture, say the build produced nothing.

### Why the cron is only a watchdog

**I built the loop wrong twice and the second version sounded reasonable.** The
first was a three-hour cycle. The second was hourly, and I justified it as
"matched to the CI round trip" — it was matched to nothing, and left up to
fifty-nine minutes of idle per hour. Jafar: *"why hourly? i said non stop, no
idle time. there must be a better way."*

The root cause is worth remembering because it will recur: **cron's minimum
interval is one hour**, so I designed around the limit of the tool I had picked
instead of noticing it was the wrong tool. The work is driven by the event chain
above. The cron exists for exactly one case — the chain dying (container
reclaimed, a turn erroring out, a watcher lost) — and restarts it. Without it,
one bad turn ends the project silently.
