# Ruling: the 2026-09-05 standing order becomes the queue, and the wake half is priced before it is armed

> **STATUS: LOG, 2026-09-05.** Director ruling at spawn 2026-09-05T09:02:36Z
> on the queue refill that decomposed Jafar's standing order of 2026-09-05
> into queue files 088 to 104 (092 unused by the planner), on the inbound
> route decision that blocks his item 1, and on eight questions the resident
> put in one spawn. NOT CURRENT once the dictated edits in section 9 are
> applied; from then the queue files, `production/NOW.md` and
> `production/budget.md` are the reading copies and this is their history.

VERDICT: APPROVED WITH AMENDMENTS. Two files are rejected as written (094,
095) and must carry the text in section 9 before a builder is briefed on
them. The rest land with the smaller amendments in section 9. Queue 092 is
assigned. Item 1's inbound clause is amended, in the exact words of section
1.4, and the amendment is put to Jafar as a card because the sentence is his.
Queue 079 moves into 095's pass (section 7d).

## 0. What was measured, and what was not

Read in this spawn, not remembered: all sixteen queue files; NOW.md's order;
`production/budget.md` in full; queue 068, 076 and 082; the newest 8 rows of
`.claude/agent-log.tsv`; `tools/producer-check.py` lines 1059 to 1280 (the
gate walk, `TREE_DEFAULT_KIND`, `PRE_REGISTER`); `tools/runner/run-night.ps1`
lines 67 to 90; `tools/runner/telegram-bot.py` lines 63 and 355 to 367;
`tools/pc-watcher.py` lines 696 to 745; `.claude/agents/producer.md` lines 14
to 93; roadmap-v2 rows R to 6; `ledger/.verify-footer`; `.git/logs/HEAD`
lines 412 and 413.

Counted: the systems in item 4 by splitting on commas, TWENTY-SEVEN. The
agent definitions: 14 `model:` lines, opus 11, fable 2, sonnet 1, which is
what 101 says. A glob for `tools/**/*judge*` matched 0 paths, so NO JUDGE
TOOL EXISTS; the only file under `ledger/` naming `content/dialogue` is
`verify.py`. `git ls-remote` for night branches (0 of 4 heads) and the
repository's visibility (public) were the resident's measurements, written
into 103 and 097 before this spawn read them, and are taken as printed. The
webhook route's `http_status=401` is the resident's measurement in 088 lines
105 to 131 and is the reason this ruling is over three routes, not four.

Nothing was run: this spawn has no shell. Every number below that is not a
line count is the resident's or the planner's, and is named as such.

THIS DIRECTOR WAS KILLED BY A SESSION LIMIT AND RESUMED. Nothing was re-read
on resumption; the record was already drafted from the reads above, and the
resumption added section 1.2(b)'s evidence statement and section 7(d).

THE STAMP AND THE REFERENCE. The footer written at 08:49:35Z reads
`reference = code commit caf62748@2026-09-04T09:07:25Z`. My row is
2026-09-05T09:02:36Z, newer. But `.git/logs/HEAD` line 413 shows a commit at
09:05:41Z, three minutes AFTER my row, titled "The order becomes 16 queue
files, and the route that looked like the answer is shut", which the brief
said was uncommitted. If that commit touched any of the eight scope prefixes
the gate will print my stamp as stale. The resident then RESUMES this
director; it does not write a newer stamp itself, and it does not commit
builder work behind a stale one.

THE SPLIT FOR THIS SPAWN, as the standing rule requires: studio 2, game 0,
basis spawns (the planner row and this row), points unmeasured. Section 6
says why it is not in points.

PREMISE CHECK, CLAUDE.md section 0: nothing in the sixteen contradicts it.
Late-analog setting untouched; nothing purchased (GitHub Pages is free on a
public repository, the bot is standard library, the planner role runs on a
tier already in use); the licence allowlist gains nothing; GTA V is not
cited. Item 11 of the order confirms D1 and D2 unchanged.

## 1. The inbound route, and what "a few minutes" honestly means this week

### 1.1 The finding stands and no wording softens it

The transport is about a minute: the watcher fetches every 60 seconds
(`time.sleep(max(10, a.seconds))`, line 1416) and `resync` is a hard reset
to the fetched sha (line 736), so a file on a branch of its own reaches the
container the next time something in the container looks. The wake is not:
a turn begins only when a trigger fires or Jafar types, the live trigger is
daily at 04:00Z, and the webhook route was measured shut by the resident
(`http_status=401`, credential sealed to one service). Three routes remain
and the resident named them correctly.

### 1.2 The ruling on the routes

(a) POLL AT EVERY DISPATCH BOUNDARY AND AT THE TOP OF EVERY TURN IS BUILT
TODAY, and it is not a route so much as the reader every route needs. It
costs one fetch. It is queue 088 as written, with the call sites named in
section 9.

(b) A RECURRING TRIGGER IS NOT ARMED TODAY, AND THE EVIDENCE THE REFUSAL
RESTS ON IS THE ABSENCE OF A SERIES, NOT THE RESIDENT'S ESTIMATE. The "76
firings against 3 points" line in NOW.md names a firing count and a
headroom; the inference that those firings were unaffordable was the
resident's judgement, made at 3 points of headroom where any spend at all
was the wrong bet. It is not evidence that a firing is expensive, it is not
evidence that one is cheap, and this ruling uses it for neither. What IS
known: a persisted firing delivers a user turn and reads the whole
conversation from cache (NOW.md, "NOT a free reader"), so its cost scales
with a conversation this long; how much, in points, nobody has printed.
Setting a cadence is setting a bound, and rule 2 forbids a bound without a
series. That is the whole of the evidence the refusal rests on: there is no
series.

WHAT WOULD MAKE ARMING IT SAFE, and this is the whole list: one printed
`pointsPerFiring` with its resolution, from a clean window in which nothing
else spent (queue 092, section 3); a kill switch the bot can pull from his
phone, because the container cannot read the meter; a one-shot that deletes
the test trigger at the window's end, armed in the same turn that armed the
trigger (rule 8); and Jafar choosing the cadence against the printed
number. With those four in place the trigger IS the route that closes item
1 as he wrote it, and this ruling says so plainly rather than leaving it to
be inferred from a refusal.

076 IS NOT THE MEASUREMENT OF THIS QUANTITY. 076 prices a token; turning a
firing into points through it needs the token count of a firing in THIS
session, and the transcripts 076 walks are the PC's `claude -p` sessions,
not this container's. 092 measures a firing in points directly, from two of
his readings. 076 stays what it is: the rate that would make spawn costs
points, which section 6 needs.

(c) THE PC STARTING A FRESH SESSION IS NOT RECOMMENDED THIS WEEK. It is
real, it is minutes always, and it is the same unmeasured spend as (b) in
different clothes, per message rather than per firing, under a week ruled
NO CROSSING. It also cannot continue an item that is in flight in this
conversation. It stays on the table as the route if (b) proves unaffordable
and Jafar still wants minutes at night; the studio's design already assumes
a fresh session can run from NOW.md, so it is not a dead route, only an
unpriced one.

THE CADENCE IS JAFAR'S CALL, against a printed number. It is his points per
wake and his acceptance sentence, and the studio's job is to hand him the
number with its resolution. Until he rules, the studio is awake-only.

### 1.3 What "never waiting more than a few minutes" means this week

WHILE A TURN IS RUNNING: the reader fires at the start of the turn and at
every spawn boundary, so a message waits for the current spawn to end. How
long that is has never been printed as a wall-clock series (the one sample in
queue 076 is a three-turn Producer spawn that ran over eight minutes), so
"minutes to an hour" is the honest phrase and `inboundLatencySec` from 088
is the printer that replaces it.

WHILE NO TURN IS RUNNING: until the 04:00Z trigger or until Jafar opens the
session. Up to 24 hours. The bot says so in its reply and names the next
wake, so silence is never ambiguous; that reply line is in 088's acceptance
by this ruling.

FOR THE SUNDAY JUDGEMENT: "know what is happening" is served by the outbound
half (the 06:00 CEST brief, images, the paused-and-back-at line) and needs no
wake at all. "Run the week" is served during the working day while turns run,
and at night only by a wake. So item 1's outbound half and items 1b, 1c and
3 carry most of Sunday, and the wake half decides whether "run" means any
hour or the hours the studio is working.

### 1.4 Item 1 must be amended, and here is the exact change

The ACCEPTING CASE sentence stands as written: "he sends a question from his
phone and gets a register-compliant answer back, and he taps a button and
the queue shows the ruling." It carries no time bound and it can be met.

The INBOUND clause cannot be met as written while the studio sleeps. His
words: "reaches the session through the PC channel, never waiting more than
a few minutes." The studio's proposed replacement, to be put to him as a
card and not applied until he rules:

    Inbound: anything he sends the bot lands as a dated file in an inbox and
    reaches the session through the PC channel within a minute of the next
    turn; the bot's reply says whether the studio is awake or asleep and, if
    asleep, when it next wakes. Waking the studio for a message, rather than
    waiting for its next turn, is armed only once the cost of one wake has
    been measured and Jafar has chosen the cadence against that number.

Queue 093 prints a latency beside each of its four rows (section 9), so on
Sunday the "few minutes" clause is read from a number and not from a memory.

## 2. The sixteen files

Every file carries both outcomes, accepting first, and every zero I found
ships a denominator or the words "nothing measured". The planner did that
part well and it is the part that usually goes missing. What follows is
what a builder could satisfy without the thing working, and the fix.

REJECTED AS WRITTEN, two files:

- 094. Jafar's 1b has three sentences and the acceptance tests two. "A
  studio silent more than two hours with no reset time on file is flagged as
  a Blocking item" is in the body and absent from the acceptance, so a
  builder lands the parser and the sleep and the item reads as done with
  the silence detector unbuilt. "Says so again when it resumes" names no
  resume signal, so it cannot be tested. The runner's own deadline rule
  (never sleep past the night's wall clock) is body only. Section 9 has the
  text.
- 095. Three holes. First, "every brief reports the studio versus game
  split" is Jafar's standing rule over the whole list, and nothing in the
  acceptance makes a brief without it fail; a tool passing the register with
  no split line satisfies 095 and breaks his rule. Second, `splitBasis=` is
  a `key=value`, and the register bans verdict keys in anything he reads, so
  as written the brief either fails the check or the check is weakened;
  the key goes on the tool's done line and the split goes in the message in
  words. Third, the fallback-brief conflict the file itself names is body
  only, and "the 04:00 UTC daily trigger will call it" is a claim about a
  prompt nobody in the tree can read: the daily trigger's prompt has no
  recorded copy, which the `production/watchdog-prompt.md` contract requires
  for the hourly one and must require for this one.

AMENDED, one clause each, text in section 9: 088 (call sites named and
grepped; the awake-or-asleep reply line; the two clocks named), 089 (the
receipt carries the platform's returned message id, so the send is an effect
and not an exit code; a refused message travels back to the tree), 090 (the
fold's call site), 091 (the receipt carries the returned photo descriptor),
093 (a latency per row), 096 (where the Producer's sentence is read from),
097 (a request that never completes prints "nothing measured", distinct from
a 404), 101 (one sentence struck), 103 (one dependency added).

AS WRITTEN: 098 (with sections 4 and 5), 099 (with one reading: "decisions"
on a tile are the D-record or card the `blocker` field names, never a lookup
by name), 100, 102, 104.

One reading I checked rather than accepted: 090's claim that the bot cannot
see a tap. `Bot.handle` reads `update.get("message") or
update.get("edited_message")` and counts everything else as `other` (lines
355 to 367). True. And 104's claim about the grid: `BUDGET_KEYS` at line 63.
True.

## 3. Queue 092: the cost of one wake

The planner was right that "readings he taps reach the repo" is 082's
deliverable verbatim; section 5 rules that. So 092 goes to the thing item 1
is actually blocked on, and it is part of item 1, not a new process item.

    line: infrastructure (the Producer loop, inbound: the wake half)
    spec: production/NOW.md item 1 inbound clause as amended by
      game-design/decision-2026-09-05-ruling-standing-order-refill-and-the-wake-half.md
      section 1.4; queue 088, "The half that does not work"
    acceptance: one night window, bounded by two readings from Jafar of BOTH
      meters as typed integers at its two ends, with no other work on the
      account and no other trigger firing inside it, during which a
      temporary recurring trigger fires with a null prompt (run the 088
      reader; answer any pending message through the outbox; otherwise end
      the turn), printing pointsPerFiring=delta/N with N counted from the
      session's own turns and not from the schedule, the resolution 1/N
      named beside it, and the variant named (persist into this session, or
      a fresh session); a window in which any other spawn or any use of
      Jafar's own fell is labelled contaminated and the number is REFUSED
      rather than published; the trigger is deleted at the window's end by
      a one-shot armed in the same turn that armed it, and a kill-switch
      file the bot writes on his command disables it at the next firing,
      both proven; readings that did not arrive print the words "nothing
      measured" with firings=N and no delta
    max_sessions: 1
    status: BLOCKS the wake half of item 1. Needs Jafar for one night and
      two readings. The cadence of the TEST night is his choice on the
      card; nothing is armed before he rules.

The card's options, for the Producer: A, a 15-minute null-firing night (24
firings in six hours, resolution 0.04 points per firing, and at the
resident's unmeasured guess about one point); B, an hourly night first
(six firings, resolution 0.17, cheap and too coarse to price a five-minute
cadence); C, awake-only this week, no test. Recommendation A. DEFAULT C if
unruled, because the default may not spend. Whichever variant runs first,
the fresh-session one must first prove it can do the job at all (one firing
that reads the inbox and lands an outbox file on the branch) before its cost
is counted; nothing in the tree says a non-persisted trigger has the repo or
the tools.

The kill switch matters because the container cannot read the meter: a
night that runs hot has no way to notice by itself. The bot's `/stopwake`
writes a file on the inbox branch; the trigger's prompt reads it first and
disables the trigger.

## 4. The seventh field: KEEP

Jafar wrote six fields by hand and the planner added `evidence`, required
only for `exists` and `partial`. It stays, on rule 1 and on the incident in
NOW.md: 37 props and 14 decals were counted as progress while
`grep -c "base-mesh|BaseMesh"` returned 0 in both street scripts. A status
word nobody can check is prose in a data costume, and the map's colour is
worth exactly what the status word is worth.

The constraints that make it his field and not the studio's: it is read by
the validator and may sit behind the tap on the map (constitution law 12,
evidence behind the sentence), it is never a tile field of its own, `absent`
entries carry none, and it is named to him in one clause when item 4 lands
so he can strike it. Adding to a hand-written spec is not automatically
right; adding the one field that makes his own status word checkable is.

## 5. Twenty-seven, and 092 does not carry his readings

The count is 27. I split the sentence on its commas and got the planner's
list exactly; the "and" pairs (save and load, map and minimap, and the
rest) are one item each because he wrote them as one, and "including the
local-LLM toggle" is inside graphics settings by his own wording. "At
minimum" means `entries=N` may exceed 27 and `covered=27/27` may not fall
short. The 28 came from the resident's brief to the planner, not from Jafar,
so there is nothing to tell him: reporting the studio's own arithmetic slip
to him is a self-correction narrative the register bans, and the outcome for
him did not change. 098 keeps its note, trimmed to name the resident's brief
as the source.

082 is the file for "readings he taps reach the repo without him", and one
file is right. But the planner's claim that "082 now depends on 088 and is
amended by 104" is not in 082: its spec line still cites the 4 September
ruling and its status line says nothing of either. Section 9 dictates the
lines. One design point folded in: `production/budget.md` is tracked and the
container edits it, which is the two-writer problem 090 names for the
decision queue, so a reading travels as a record on 088's branch and a fold
tool writes the row, never the PC editing budget.md on the work branch.

## 6. The split cannot be in points, and he is told once

`production/budget.md` line 87 is law: turns are not points, the conversion
is unmeasured, and no per-tier points figure enters that file until two
paired readings exist. A split "in points" today would be a spawn count
multiplied by the 1.5-to-2 guess, which is a number nobody printed, and I
refuse it. So the instruction cannot be done as asked today.

What satisfies its purpose honestly: the brief carries the split in words,
in the BUDGET section, counted in sessions, with the phrase that the count
is sessions and not points until the rate is measured. The first brief that
carries it says so once. The tool's done line prints
`splitBasis=spawns` and the machine-readable pair goes to the console page
he can tap, never into the message. `producer-check --kind brief` REQUIRES
the split sentence and admits its two numbers on that line only, which is a
one-line change to the ruled register made under his own instruction of
today.

The way it becomes points, so this is a rung and not a shrug: 082 lands his
readings in budget.md without him; each pair of readings brackets a window;
the agent log gives the spawns in it by tier; a week of clean windows (he is
asleep) gives points per spawn by tier as a fitted series, and only then a
split in points. 092 prices a null wake, 076 prices a token; neither alone
prices a spawn.

## 7. The three conflicts, and a fourth the footer raised

(a) 096 SUPERSEDES 068, and this ruling is the move the planner could not
make. 096 carries 068's five ruled items verbatim and in order. When 096
lands, the integrator moves 068 to `production/queue/done/` with one line
at its head: superseded by 096, all five items carried. Not before 096
lands: a retired file with no successor in the tree is the 31 August queue
incident again.

(b) THE FALLBACK BRIEF WOULD RED THE TREE, confirmed in the code. The gate
walks `production/briefs/` with `TREE_DEFAULT_KIND` making every file a
brief (line 1080); `PRE_REGISTER` names four files and `latest.md`; a
`night-YYYYMMDD.md` with no marker and no listing reaches `check(text,
"brief", ...)` at line 1261 and fails on shape and link. Three rulings:
095's tool is the ONE writer of every brief including the fallback, and the
inline `@(...)` block at `run-night.ps1` lines 79 to 82 is deleted in 095's
diff; `git add production/briefs` at line 85 becomes staging by name, per
`.claude/rules/ci.md`; and 103 does not run before 095 has landed (added to
103's dependencies). The copy over `latest.md` is legal today only because
`latest.md` is on the frozen list, which is the hole queue 074 owns; 095
must not make it worse and 074's lean to option B stands.

(c) 100 TOUCHES THE ROADMAP AND NEEDS ITS OWN STAMPED RULING. This record
does not cover its diff. The resident spawns a director when 100's diff is
in the tree, and that record lists every system that moved phase with one
line each, refuses any new phase row, and shows docs-check green with every
row's word count printed. A fold that reschedules half the player-facing
surface is a plan change, and it gets a plan change's review.

(d) 079 MOVES UP, INTO 095's PASS, AND NOT AS A PASS OF ITS OWN. The live
footer reads `22 queue items ready` before and after sixteen files landed,
because the count reads `game-design/queue.md`, retired 31 August, and never
opens `production/queue/`. That number sits in the one channel every session
and director reads; this director read it and it disagreed with the
directory listing. 095 has to count the same directory for the brief, and
two counters for one quantity that disagree in one tree is the fault the
instruments rule names: one implementation per idea. So 095's builder points
the footer's counter at `production/queue/`, printing ready, blocked and
done with the retired path named as not read, and the brief and the footer
read ONE counter. Cost: no extra pass; it rides item 1c, which is
authorised, so no pass Jafar has not authorised is spent. If it does not fit
in 095's session, it goes back to item 9 and NOW.md carries one line: the
footer's ready count reads the retired queue and is not to be quoted until
079 lands. Either way the wrong number is not quoted as evidence again. This
is a reorder inside one pass and this record says so, which is what the
standing rule about new process items asks.

## 8. The order of work for the rest of today, and what he is told

His list is the order. The sequencing below is only about which files two
builders cannot share.

1. Builder A: 088, alone, first. Everything in item 1 stacks on its branch,
   and Jafar can test the transport tonight by sending the bot one message.
   Reviewed and committed on its own so it lands early.
2. In parallel after A lands: Builder B, 089 with 091 (both are the sender
   on the PC, same loop, same file); Builder D, 095 with 079's half (a new
   tool, `producer-check.py`, `run-night.ps1`, the footer's counter in
   `verify.py`; no overlap with B). One director review for the pair.
3. Builder C: 090 with 104 (both are the bot's input handling, same
   function). Then 094. Then 093 when Jafar has two minutes, and not before
   088, 089 and 090 have all landed.
4. Then 096, 097 (with its card ruled or defaulted), 098, 099, 100 with its
   own ruling, 101. After 100 lands the studio stops building studio, and
   101 is item 5 of his order rather than a new process item, so it runs;
   the sentence in 101 saying otherwise is struck.
5. Then the game: 062 step 2, run 21, the first textured frames to him as
   images through 091. Then 102, whose choice is a director ruling that
   must compare the bark line (the footer reads 2604 bark lines, voice
   generated and into the build) against the candidates 102 lists, because
   no judge tool exists today and the roadmap's own Phase 0 row names the
   dialogue bank. Then 103, after 094 and 095.

ESTIMATE, with its calibration: a spawn costs roughly 1.5 to 2 points,
derived 2026-09-02 and weak in the three ways budget.md names. Today's plan
is five builders and two or three directors, so 10 to 16 points. The whole
list is about 14 builders and 5 directors, 28 to 38 points, leaving roughly
34 to 44 of the 72 for items 6 to 9. What dominates is builder overrun (three
of four on 1 September) and dead directors (two of three on the night of 2
September); what could blow it up is a builder briefed with a reading list.
Brief with the facts inline.

WHAT HE IS TOLD, through the Producer and in the register, today: the
transport half of item 1 lands today and the bot will answer whether the
studio is awake; the card in section 3 with the amended sentence of section
1.4 as its consequence; the Pages exposure card from 097's addendum, DECISION
class, default publish-as-designed because budget.md is already public in
the same repository and the card says so; the split in words, sessions not
points, once. Until 089 lands the outbox reaches him only if he opens the
session, which is why 089 is second.

## 9. Dictated edits, applied by the resident before any builder is briefed

9.1 `production/queue/088`, acceptance line, append: "; the reader's call
sites are named and shown by grep, at minimum the daily trigger's prompt
(whose recorded copy lands in the tree under the watchdog-prompt contract)
and the dispatch checklist in `ledger-v2/studio-v2/runner.md`; the bot's
reply to every filed message says awake or asleep and, if asleep, names the
next wake; and `inboundLatencySec` names both clocks it subtracts (Telegram's
`date`, the PC's commit instant)".

9.2 `production/queue/089`, acceptance line, append: "; the receipt carries
the message id the platform returned, so a receipt with no id is refused;
and a refused message travels back to the tree as a record on 088's branch
with the failing clause, printed as refused=K on the container side".

9.3 `production/queue/090`, acceptance line, append: "; the fold's call
site is named and is the 088 reader at the dispatch boundary".

9.4 `production/queue/091`, acceptance line, append: "; the receipt carries
the photo descriptor the platform returned (its sizes), which is the
artifact for arrived-as-a-photo".

9.5 `production/queue/093`, acceptance line, replace "each of the four
steps carries its instant" with "each of the four steps carries its instant
and `stepLatencySec` from the previous row's instant", and append: "; the
run uses the wake route as it will stand on Sunday, and the file names which
route that was".

9.6 `production/queue/094`, acceptance line, append: "; with the newest
work-branch commit older than two hours and no state file, the bot raises a
CLASS: BLOCKING card, and with a state file whose reset is ahead it does
not, both proven with planted clocks, printing silenceHours beside the
two-hour bound and the two instants compared; resumed means the state file
cleared by the container's first turn after the reset, with the newest
commit instant as the fallback signal, and the bot's back-again line names
which; a reset beyond the runner's own wall-clock deadline ends the night
with that reason in the log rather than sleeping past it".

9.7 `production/queue/095`, acceptance line, append: "; the brief carries
the studio versus game split in words in its BUDGET section, counted in
sessions with the sentence that it is sessions and not points until the
rate is measured, and `python3 tools/producer-check.py --kind brief` REFUSES
a brief with no split sentence, proven with a planted brief; `splitBasis=`
appears on the tool's done line and nowhere in the message;
`tools/runner/run-night.ps1` no longer writes a brief of its own, proven by
`grep -c 'Fallback brief' tools/runner/run-night.ps1` reading 0 and by
staging by name; the daily trigger's prompt is recorded in the tree and
names this tool; and the queue counts the brief prints and the counts the
verify footer prints come from ONE counter reading `production/queue/`,
printed as ready, blocked and done with the retired `game-design/queue.md`
named as not read (queue 079), proven by the footer changing when a file is
added". Body: replace "Either the fallback is generated by this same tool
(preferred, one writer) or it is named and exempted through the tool, never
by a marker alone" with "The fallback is generated by this same tool, one
writer; ruled 2026-09-05." Add one line: "If the 079 half does not fit in
this session, it returns to item 9 and NOW.md says the footer's ready count
is not to be quoted until it lands."

9.8 `production/queue/096`, acceptance line, append: "; the Producer's
dated sentence is read from one named path, and the file says which".

9.9 `production/queue/097`, acceptance line, append: "; a request that does
not complete (proxy refusal, timeout) prints the words "nothing measured"
with the error, and is never reported as 404". Status line, append: "The
exposure question in the addendum is a DECISION card, default A, publish as
designed, because budget.md is already public in the same repository; 097
waits for the ruling or the default, not longer."

9.10 `production/queue/101`, strike the sentence "It is a new process item,
so under the standing rule it goes to the queue and waits if item 4 has
already landed when its turn comes." Replace with: "It is item 5 of the
standing order and runs after item 4; ruled 2026-09-05."

9.11 `production/queue/103`, dependencies: add queue 095 beside 094, with
the reason in section 7(b).

9.12 `production/queue/082`, spec line becomes: "production/NOW.md,
'JAFAR'S STANDING ORDER, 2026-09-05', item 1, readings clause; and
game-design/decision-2026-09-04-ruling-067-telegram-bot-first-pass.md,
section 2". Status line becomes: "READY 2026-09-05. Carries item 1's
readings clause. Depends on queue 088 for the route: the reading travels as
a record on the inbox branch and a fold tool in the container writes the
budget.md row, never the PC editing that file on the work branch. The
`source` field is amended by queue 104 (typed only, the retired value named
so older rows stay readable). After 088." Acceptance line, replace "a source
field" with "a source field per queue 104".

9.13 `production/queue/098`, in the section "The names": replace "The brief
that commissioned this task said 28" with "The resident's brief to the
planner said 28; Jafar never did".

9.14 Create `production/queue/092-the-cost-of-one-wake.md` with the front
matter in section 3 and a body carrying sections 1.2(b), 1.3 and 3 of this
record in the planner's register, including the four things that make
arming safe, the options and the kill switch.

9.15 `production/NOW.md`, under item 1: one line, "Inbound clause AMENDED
pending Jafar's ruling; the proposed sentence and the reason are in
game-design/decision-2026-09-05-ruling-standing-order-refill-and-the-wake-half.md
section 1.4; queue 092 prices the wake." Under "In flight": the order of
work from section 8, items 1 to 5, with the note that 088 lands on its own;
and one line, "The verify footer's `22 queue items ready` reads the retired
queue (079) and is not to be quoted until 095 lands its counter."

9.16 `production/queue/079`, status line, append: "Folded into queue 095's
pass by the ruling of 2026-09-05, section 7(d); returns here only if it does
not fit."

9.17 `production/decision-queue.md`, WAITING: the two cards from sections 3
and 8, written by the Producer in the ruled shape (CLASS, options,
recommendation, default, deadline no shorter than 24 hours). Not written by
this director.

## 10. Quality ladder at close

First working, not best available, and the next rungs are named. The wake
half's rung is 092, then a cadence set by Jafar from what it prints. The
split's rung is 082's automatic readings and a fitted per-tier series, after
which the brief says points. The inbound latency's rung is a printed series
from 088 replacing the phrase "minutes to an hour". The queue count's rung
is one counter under both readers (7d). The judge for 102 is a blank rung
and is therefore a research task before the pilot's verify step, whichever
content type the 102 ruling picks.

<!--RULING spawn=2026-09-05T09:02:36Z-->
