# CLAUDE.md — how to work on LEDGER

Read this first, every session. It is not style guidance. **Every rule below
exists because it was broken, and the incident is named so the rule is
believable rather than decorative.**

---

## 1. Never assert what you have not just checked

The single most expensive habit. Four separate incidents in one day.

- I told Jafar the four Lena voice candidates were four different people. They
  were one person four times. **I had read my own code comment instead of my
  own code** — the comment said "sharing a voice defeats casting" and meant it
  about a different axis.
- I told him the Mixamo character drop was the biggest open blocker in the
  project and he should go do it. **It had shipped the day before.** I quoted a
  "STILL OPEN" list dated three days earlier from the middle of a 1,500-line
  file.
- I reported a re-run was in progress that I had never issued.
- I said 30 clips came from the wrong corpus and wrote a commit deleting them.
  They came from the right one.

**The rule.** Before stating a fact about this repo — what exists, what is
wired, what shipped, what a number is — run the command that proves it, in the
same turn. A memory of having checked is not a check. If you cannot check it,
say "I have not verified this."

**Corollary: your own comments and docs are not evidence.** Read the code.

**Second corollary: when you change code, you have changed the comments about
it.** Four in one night, each true when written and quietly false afterwards —
and every one of them misled somebody, usually me:

| said | reality |
|---|---|
| `actions/checkout`: "Nothing here pushes" | I had just added a step that pushes. It failed six times and reported success. |
| `NpcWalker`: a name is "not there at all across the road" | Full at 4m, visible at 11m, while talking range is 3m. |
| `TrafficHost`: "sixteen blocks; a dozen or so reads as a working district" | Written when the game was one district. There are seven. |
| `Tier2Batch`: "never brighter than the cast" | Nothing enforced it, and the crowd used a brighter value than the other spawner. |

A comment is a claim with no test attached, so it decays silently and the decay
is invisible in a diff that does not touch it. **Before finishing a change,
re-read the comments on everything it touched — including the ones you did not
edit — and grep for the claim you have just falsified elsewhere.** The
`persist-credentials: false` comment was eleven lines above the step I broke.

## 2. Never set a threshold you have not measured

- `nightNotDarker` compared one noon frame to one night frame and failed at
  0.136 against 0.135. That is a rounding, not a measurement.
- `deedSlotSets` sat ungated for days because I refused to invent a number —
  that refusal was correct, and the fix was to make the run **print the series**
  so a threshold could come from evidence.

**The rule.** If you need a threshold, first make the system report the value,
run it, look, then set it. When a gate is failing, ask whether the instrument
or the subject is wrong before touching either.

**This covers the METRIC and the AGGREGATOR, not just the number.** Both were
got wrong in one night, and neither is a threshold:

- The §4.7 places gate read `alley=53 market=53`, I called the count saturated
  by hearing and re-gated on eye-witnesses only. That was one sample. The alley
  pick had simply happened to stand in the open, and the next run — printing all
  four columns — read 3 / 53 / 3, which is the claim exactly. I had moved a gate
  onto a worse metric to fix a problem that did not exist, and had to move it
  back.
- The AO gate bounded a fraction ABOVE 50% while `MeasureAoOnce` kept the
  MAXIMUM of its rounds. A maximum answers "did the pass ever reach the frame";
  it cannot answer "is the pass everywhere", because it maximises the very
  quantity the ceiling exists to keep small — so adding rounds made it trip on
  its own. One run read 80%; the round series read
  `[26.9 26.4 26.4 22.8 23.0 23.0 5.9 5.9 5.9]`, median 23.

So: choosing WHICH number a gate reads, and which statistic summarises it, needs
the same evidence as choosing the threshold — and one run is not evidence.
Print the series first. When a gate asks two questions, give each the statistic
that answers it, and do not move the bound to make red go away.

## 3. Suspect the instrument first

Three times in one month the tool was the thing at fault:

- `breakrun.py` reverted one file of a two-file spec, so break N leaked into
  break N+1 and a SURVIVED could be reported as RED.
- The corpus diagnostic read 60 *consecutive* rows of a speaker-ordered dataset
  and reported on "the corpus". It had seen one person.
- `BarkGen` wrote its manifest to whatever directory the shell was standing in,
  so the tracked copy silently went stale.
- A gap analysis I ran said alarm propagation was unwired. Reading `NpcWalker`
  showed it already emitted. **The analysis was wrong, not the code.**

**The rule.** When a result is surprising, check the ruler before the reading.
When your own analysis says something is missing, open the file and look.

## 4. Open the artifact you are shipping

The listening page was published with **six faults**, all invisible from the
Python that generated it and all found in the first sixty seconds of actually
loading it: no viewport tag, no picking UI at all, a fixed bar sitting on top
of the controls, a row that cast a vote when you pressed play, a page that
scrolled sideways, and a `\n` in a non-raw string that killed every control on
the page. Then the *standalone* build silently dropped the speaker ids — the
page published as the fix for "you can't tell these apart" was the page you
could not tell apart on.

**The rule.** If the deliverable is a page, open it in a browser at the size it
will be used. If it is audio, check its duration and metadata. If it is a file,
read it back. `tools/voice-fetch/page_check.py` does this for the listening
page; write the equivalent for anything new.

**ALL of it, and never the gate INSTEAD of the artifact.** Every build commits
four stills. Three separate faults have now been found by a human opening one
of them and none by a gate: a hand lookup that could only see one body tier, a
white capsule drawn over the bought body, and that body lying flat on its back
in the road. In the third case I opened the NIGHT frame to check a window
question, read `playerPrimitive=False` off the done-line, and called the body
confirmed — while the noon frame in the same directory showed it on its back,
magenta. My own checkpoint had said *"LOOK at review_day1_noon.jpg and confirm
a skinned figure"*, and I substituted a passing number for the instruction I
had written myself.

A gate reports what it was built to ask. All twenty in `SimDirector` ask about
what a system ADDED — is it there, is it the right size, did it bind — and not
one asked what the frame LOOKS like, which is why all three faults sailed
through green. So: **read every still, every build, before reading any gate,
and never let a green reading stand in for the frame it claims to describe.**
When a still shows something wrong, the fix is a NUMBER that would have caught
it — `playerPrimitive`, `bodyUp`, `collidingNames` all exist because a picture
found what nothing was measuring.

**And then: LOOKING IS NOT MEASURING.** The night the sim first committed
screenshots, I opened them and condemned four correct things off the back of a
1280x720 JPEG:

- three textures as "off-brief" — rust-red asphalt, mossy paving, ochre brick.
  `SurfaceSpec`'s noir tint had already stripped every one of them. The render
  disagreed with the source files I had judged them from.
- a bench as a sign board mounted wrong. `Plate` was correct and always had been.
- the new vehicle wheels as oversized. Printed, they came out at dia/hi 0.40 and
  dia/len 0.14 for a car — within a few percent of a real one.

Each time I was one step from re-picking assets or "fixing" working geometry.

A picture is excellent evidence that something is WRONG and poor evidence of
WHAT or WHY. It has a resolution, a compression artefact and a palette, and at
street distance in fog those hide more than they show. So: a visual judgement is
a HYPOTHESIS. Before acting on it, make the run print the quantity — the tiled
colour, the ratio, the dimension — and read that. Every one of the four
reversals above was settled by a number in under a minute, and three of them
would have cost a CI round trip and a wrong commit.

## 5. Look before you destroy, and make the guard know the difference

- A cancelled CI run committed its empty output directory and **deleted 24
  clips Jafar had already listened to and picked from.** The step reported
  success.
- The guard I then wrote refused any run producing fewer clips — and would have
  thrown away the *corrected* set for being smaller. A guard that cannot tell a
  regression from an improvement is a ratchet.
- `rm -rf ../../voice-candidates/*` in CI deleted sixteen characters' clips on
  a run that was only asked to fetch three.

**The rule.** Before any delete or overwrite, look at what is there. Scope
destructive commands to exactly what the operation produced. Guards check
*whether the thing succeeded*, not just whether a number went down. And copy
anything a human spent time on somewhere the pipeline cannot reach —
`game-design/picked-clips/` exists for exactly that reason and it paid for
itself within the hour.

## 5b. A guard must be tested on the case it should PASS

Four in one day, and every one of them blocked the good case rather than the
bad one:

| guard | blocked |
|---|---|
| build-ordering by git ancestry | the checkout is shallow, so the test could never succeed and the NEWEST run stopped publishing stills at all |
| `queue-check`'s standing-work test | matched `## Standing rules`, a section about how to use the queue, and certified the backstop it existed to demand |
| the anti-double-spend gate | skipped the paid step correctly, then let the step that COMMITS its output run anyway, fail, and kill the job before the work it was dispatched for |
| the enrichment audit | refused to commit unless every card passed, so a run that fixed 54 of 60 landed nothing |

Every one passed its failure case. Not one had ever been run against its
success case. And every one was reported as a clean exit by the step above it,
so the symptom was always "nothing happened" rather than "something broke".

**The rule.** A guard has two outcomes and shipping it means having watched
BOTH. Before committing one, run it against input it must ACCEPT as well as
input it must reject — and if the accepting case cannot be produced locally,
say so in the commit rather than assuming that half works. `Tier2Gen
--selftest` is the shape to copy: its first assertion is that a good card is
accepted, and that assertion is first precisely because the expensive failure
is a validator nothing survives.

**Corollary: a guard that cannot tell a regression from an improvement is a
ratchet** (rule 5). "Refuse unless perfect" throws away partial success, and
partial success is what real work looks like.

## 6. Built is not running

A gap analysis over 61 public Core APIs found **2 untested and ~40 with no call
site in the game.** Phases 2–4 of M16 were built, tested, and disconnected.
`Brandish` 0. `MayFrisk` 0. `Acquire` 0. `Misattribute` 0 — so the street could
only ever be right about who did it.

The same failure has hit the noise ring and the caption bar before: a system
built, plausible, and never once running.

**The rule.** A feature is not done when Core is tested. It is done when
something calls it and a gate proves the call happened. When you finish a
system, grep for its call sites before saying it is finished.

## 7. Estimates: name what dominates, or do not give a number

Wrong every time today. The causes were always the same two things:

- I benchmarked against a **broken** run (it was fast *because* it was
  cheating), and
- I did not check what was actually blocking — a run sat "pending" behind one
  of *my own* pushes three separate times.

**The rule.** Before giving an ETA, check the thing is actually running and
what is ahead of it in the queue. State what dominates the estimate (here: a
~28-minute CI round trip) and what could blow it up. If you do not know, say
so — that is a better answer than a number you will retract.

## 8. "I will come back to you" requires arming something

Said twice, and both times Jafar had to ask anyway. Ending a turn does not
schedule a wake-up.

**The rule.** If you say you will report back, start a background watcher in
the same turn that will fire on the condition (or a timeout). No watcher, no
promise.

## 9. Do not block yourself

Pushing a commit triggered a full 40-minute corpus fetch, three times, each one
queued in front of the run Jafar was waiting on. Once, the run that would have
*fixed* the problem was queued behind a run of the problem.

**The rule.** Know what your pushes trigger. Expensive jobs are opt-in
(`workflow_dispatch`), concurrency groups are scoped to the expensive job only,
and cheap checks never queue behind a stream.

## 10. Documents

Two failures, opposite directions, same day.

- The roadmap reached 1,525 lines of which ~85% was chronology, and I "audited"
  it by stamping a status banner on the top — certifying the mess.
- Then I over-corrected and split the plan into a second file, so you had to
  open two documents to find out what happens next.

**The rules.**
- Every doc in `game-design/` declares **LIVE / SPEC / LOG** in its first lines.
  `tools/docs-check.py` enforces it, plus: a LOG carries its date and says NOT
  CURRENT, a LIVE carries a verified date, a LIVE plan stays under 400 lines,
  and no LIVE doc contains a diary heading.
- **`roadmap.md` is the tiebreak and contains the plan itself.** Not a pointer
  to the plan. History goes to `roadmap-history.md`.
- A milestone entry is not a title. It states what is in it, why it sits there,
  **what done looks like as something measurable**, dependencies, and risk.

## 11. Scope: do the asked thing

Asked whether a macOS build was *possible*, I built the CI job. Jafar:
*"never asked for a mac build, only if it's possible."*

**The rule.** A question is a question. Answer it, and offer the work
separately.

## 12. If you cannot read the output, fix that before anything else

For one whole night I diagnosed this project by inference, because every
channel out of a CI job was blocked and I kept working around it instead of
repairing it:

- the log API returns a fixed ~4KB **byte** tail, so nothing mid-log is
  reachable and GitHub's own post-job cleanup fills that window every run;
- `get_check_run` returns the step summary EMPTY — and a comment in the
  workflow asserted that channel worked;
- artifacts are on a host this environment denies outright.

So three separate faults were diagnosed from a step's **duration** (2m10s of
retry sleep meaning six failed pushes) and from a branch that had not moved,
and a 291-byte artefact standing in for "the directory was empty". That is
divination, and I did hours of it before doing the ten-minute fix.

**The rule.** A blocked feedback channel is not an inconvenience to route
around, it is the highest-leverage bug on the board — fix it FIRST, and prefer
a channel this environment can definitely read. In this repo that means a file
in the repository. Everything since has been settled in seconds by
`game-design/sim-shots/`.

---

## Project mechanics you will otherwise learn the hard way

**The Game layer does not compile here.** Only `Core` does. Locally you get
`ledger/verify.py` — lint, ShapeCheck (Roslyn, reference-independent
diagnostics only), stale-anchor detection, 2,884 CoreTests, and break-runs.
A type error against a Unity API is invisible until the Windows CI build, which
takes ~28 minutes. **Batch Game-layer changes; never claim a phase is done on a
local green.**

**You can SEE and READ the game — use it.** Every Windows build commits four
stills and a verdict to `game-design/sim-shots/`, overwritten each run:

    review_day{1,2}_{noon,night}.jpg    what the street actually looks like
    verdict.txt                         the done-line, FAILING GATES, the sky
                                        readings, the places line, glyph and
                                        wardrobe counts, wheel proportions
    runs/<sha7>.txt                     the same verdict, kept per commit

`git pull` and read them. Do NOT try to tail the job log — see rule 12. The
verdict is committed, so `git log -- game-design/sim-shots/verdict.txt` gives a
HISTORY of measurements: that is how the AO ceiling was shown to be sitting
inside its own instrument's noise across five runs. Adding a number to that file
costs one line and pays for itself the first time a gate fails.

**DISPATCH BUILDS IN PARALLEL.** The Windows job is `workflow_dispatch` with no
concurrency group, so nothing queues it — several can run at once, and that is
how a day of serial hypotheses turns into two waves. Five round trips on the
upside-down player cost two and a half hours because I sent one question at a
time when I could have sent three. Each run keeps its own `runs/<sha7>.txt`, so
concurrent builds are concurrent ANSWERS rather than one answer overwriting
another.

**`verdict.txt` is the last run to LAND, which is not the newest commit.** Two
builds ran together and the one on the older commit finished second and laid
its output over the newer one's — so the file everything treats as "latest"
held the stale answer, and only the sha on line one said so. Runners here vary
by twenty minutes, so dispatch order tells you nothing about landing order. The
workflow now keeps whichever verdict came from the newer commit and lets the
loser contribute only its `runs/` file. **Check the sha on line 1 anyway**, and
when you dispatched a specific question, read `runs/<sha7>.txt` and not the
default.

**Always run `ledger/verify.py` before committing.** It prints the footer that
goes in the commit message, measured rather than remembered — it exists because
I put unmeasured test counts in two commit messages.

**HuggingFace and most external hosts are blocked from this container** (403
through the proxy). Anything corpus-related must go through CI, so make each
run maximally informative rather than a single blind attempt.

**Verify a workflow's effects, not just its exit code.** A CI job here has
reported success while: deleting the clips, pushing nothing, producing zero
output for every character it was asked for, and committing a truncated log.

**Branch:** `claude/game-dev-ai-automation-2h67ix`. Never open a PR unless
asked. Never make a purchase or use an account — every purchase is Jafar's.

**Voice sourcing consent rule:** only corpora whose contributors donated their
voices to build speech technology, and **no identifiable public figures, ever.**

---

## AUTO MODE

Jafar's name for it. He will say **"start auto mode"** or **"stop auto mode"**,
and both must work from a cold session — which is why this is here and not only
in a trigger prompt. The container is ephemeral; a file in the repository is the
only thing that survives it.

**What it is.** Continuous autonomous building, around the clock, with a short
plain update six times a day. Not a cycle. Not a cadence. Jafar's words, after
I got it wrong twice: *"non stop, no idle time."*

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
**Watch for a verdict naming the sha you dispatched** — not for the branch to
move:

    SHA=<the sha you built>
    for i in $(seq 1 100); do sleep 30
      git fetch -q origin claude/game-dev-ai-automation-2h67ix 2>/dev/null
      V=$(git show origin/claude/game-dev-ai-automation-2h67ix:game-design/sim-shots/verdict.txt 2>/dev/null | head -1)
      case "$V" in *"$SHA"*) echo "VERDICT LANDED: $V"; exit 0;; esac
    done; echo "timed out; last verdict line: $V"

**THE OBVIOUS VERSION IS WRONG AND I SHIPPED IT INTO THIS FILE.** It watched
`git ls-remote` for the branch head to change, on the reasoning that the job
commits stills so the branch advancing IS the build landing. That is true when
nothing else is pushing. In auto mode I push constantly — and the watcher fired
forty seconds later on MY OWN COMMIT, reporting "BUILD LANDED" while the verdict
still named the previous build. A watcher that cannot tell my push from CI's is
the ruler being wrong, and it would have had me reading a stale verdict as a
fresh one for the rest of the session.

The verdict's first line carries the sha it was built from. Match on that and
the signal cannot be forged by anything I do.

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

### Reporting

Six times a day, daytime only: **07:00, 10:00, 13:00, 16:00, 19:00 and 22:00
CEST** — UTC hours 05, 08, 11, 14, 17, 20. Run `date -u +%H` and check before
writing anything. Every other firing works in SILENCE and ends with no
user-facing message. The 07:00 report is the overnight summary.

**It opens with a header line so it can be FOUND**, then five to seven short
plain sentences:

    **LEDGER — 16:00** *(update 4 of 6)*

Then: what got done; where we are on the roadmap (read `roadmap.md`'s screen
table — do not recite from memory, and fix it if it is wrong before quoting it);
what is next; what decision is needed from Jafar, or "nothing needed from you".
Lead with anything visibly broken. **No code block, no template, no shas, no
metric names, no file paths.**

**The header exists because Jafar twice asked where an update was that had
already been sent.** Both times it was there and both times it read as more
conversation — I had followed the rule that it goes last with nothing after it,
which is right, and lost the signal anyway because nothing marked it. A report
he cannot find when scanning back is a report that did not happen, and the fix
is one line rather than more words.

He has said twice that updates were too long and too technical, and once that a
report was buried mid-message and he never saw it. Say *"the player is upside
down"*, not the name of the metric that measured it.

---

## The standard

Jafar: *"it has to be EXCEPTIONALLY GOOD from a game feel and UI/UX point of
view. we don't ship low quality / AI slop here."*

And the framing every plan is judged against: unmistakably deeper than KCD2
while looking unmistakably worse, and at peace with that trade. The moat is
social memory 93, consequence persistence 95, information 90 — against a
best-in-class of 60, 85 and 65. Everything else is in service of it.
