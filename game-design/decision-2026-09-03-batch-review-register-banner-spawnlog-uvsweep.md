# Ruling: the 3 September two-builder batch (register gate, banner law, spawn log, UV sweep)

> **STATUS: LOG, 2026-09-03.** Director ruling on the batch pending in the
> tree at spawn 2026-09-03T15:59:53Z. NOT CURRENT once the dictated edits in
> section 6 are applied and the batch is committed; from then the committed
> files, `production/NOW.md` and the queue items named in section 7 are the
> reading copies and this is their history.
Reviewed by reading. Section 0 says what was not measured.

VERDICT: LAND AS ONE COMMIT, after the dictated edits in section 6 are
applied, two of which are ordered rather than optional (the SubagentStop hook
is registered, and its output file is added to the cadence gate's evidence
list). Nothing goes back to a builder before the commit. Three queue items are
created and two existing items gain a step. THE UNREAL STOP RULE IS NOT
DISCHARGED BY THIS BATCH; it can only be discharged by a landed run, and this
ruling authorises exactly one, on two conditions, in section 4.

---

## 0. What this ruling did not measure

This director has Read, Glob, Grep and Write and no shell. Nothing below was
run. In particular, none of the resident's git numbers (159 paths, 278 changed
lines under `game-design/`, the em-dash character count 6279 to 6140) and
none of the builder's transcript series (453 transcripts, fable 159 with
median 12, opus 144 with median 45 and peak 138, 170 with a limit notice, 148
with no turn) were reproduced here. What WAS read independently is stated
under each ruling with the command shape and the count, so a reader can tell
a reading from a repetition. The two selftests and the gate were not run;
their fixtures were read.

---

## 1. The register gate (`tools/producer-check.py`, `production/outbox/README.md`)

What was read: the whole tool (1153 lines), the README, the four brief files'
first lines, the `producer_register` check in `ledger/verify.py` (lines 1079
to 1121), and `.claude/agents/producer.md`. Grep for the marker
`PRODUCER-REGISTER-EXEMPT`: 8 hits, four of them on line 3 of the four briefs
(inside the 8-line window), the rest in the tool and the README. The frozen
`PRE_REGISTER` tuple names exactly those four paths. Grep for a line beginning
`HEADLINE` anywhere outside `tools/`: 0 hits.

### (a) A gate whose only live reading is `filesChecked=0`: not a ratchet, but it has no real accepting artifact

Rule 5b's ratchet is a guard that has never been watched passing. This gate
has been, twice, on fixtures: a synthetic compliant outbox message (walked 3,
checked 1, exempt 2, failed 0) and the live tree (walked 5, exempt 5, checked
0), and the live reading prints `filesChecked=0/nothing-measured` into the
verify footer in those words, so the footer cannot be read as a pass. Five
synthetic rejecting trees each go red. That is both outcomes watched.

What it lacks is an accepting case on a REAL message that exists in the
tree. `production/NOW.md` records that the first live Producer message was
refused four times and then passed; grep finds no such message on disk. The
one artifact that would prove the register survives real prose is not in the
repository. ORDER: if the resident still has that text, run it through the
check; if it passes, file it as
`production/outbox/2026-09-03-<slug>.unprompted.md` in this commit, and the
gate's first live reading becomes `filesChecked=1`. If it fails today's
check (the link floor became unconditional after it was sent), record that
sentence in NOW.md and do not file it. If the text is gone, NOW.md says
"nothing measured" for the register on real prose.

The ban list's false-positive rate on ordinary English is unmeasured: `job`,
`commit\w*`, `branch\w*`, `gate`, `PR` are all whole-word bans and all occur
in normal sentences. That is a series to read off the first ten real
messages, not a bound to set now. The tool already prints the per-section
advisory with its denominator for exactly this purpose.

### (b) Two mechanisms: right, not ceremony, with one hole named

A marker alone is an escape hatch anyone can type at the top of a 600-word
message; a list alone is invisible to a reader of the file. Requiring both
means widening the exemption is a reviewed diff of the tool. The rejecting
fixtures cover both single-mechanism cases (marker without listing, listing
without marker). Upheld.

THE HOLE: `production/briefs/latest.md` is a MOVING NAME on a FROZEN list.
`tools/runner/run-night.ps1` line 84 copies the night brief onto that path.
The first night run after this commit therefore produces one of two
outcomes: the copy carries no marker and the gate goes red on a
machine-written file ("listed without a marker"), or a later writer copies
the old head across and a file dated after the register is exempt under a
marker that says it predates the register. Neither bites today (STATUS.md:
the night runner has never written a log in this tree), but it is a
predictable red. Queue 074.

### (c) The conditional pair cannot disable itself, but the item parser can

For `unprompted` and `brief`, `options` and `deadline` are in `RULES`
unconditionally; the `RULES_IF_NEEDS_YOU` addition applies to `answer` only
and can only ADD rules, never remove one. So the pair as wired is safe.

The self-disable is one level down and applies to every register.
`needs_you_items()` (lines 529 to 560) recognises an item by the markers the
two rules then check for: an option letter, `RECOMMEND`, `DEFAULT` or
`DEADLINE`. Its last clause drops a trailing chunk that carries none of
those. So a NEEDS YOU body written as prose ("which pavement distance do you
prefer? see the card") parses as ZERO items, `options` and `deadline` find
nothing to check, and the message passes. The check cannot tell that body
from "nothing today": the accepting fixture at line 762 and this hole are the
same code path, and no rejecting fixture covers it (the `options` fixture at
line 685 keeps option A, so it still parses as an item). Detection rests on
the presence of the very markers whose absence is the violation.

RULING: does not block this commit (the gate checks zero real files today
and the resident hand-checks before sending), but it lands before the next
unprompted message is sent. Queue 073 carries the fix and the fixture pair.

---

## 2. The banner law (`tools/migrate-status-banner.py`, `tools/docs-check.py`)

What was read independently. Grep for `STATUS[ \t]*` followed by an em-dash
under `game-design/`: 8 lines in 7 files. Seven are quotations inside
backticks in `.md` files (agent-reports yard-depth-series 222, sim-hang 373,
lint-static-denominator 406, convergence-instrument 988, sky-gain-discriminator
346 and 347, and decision-2026-09-02-vignette-batch 185). The eighth is
`game-design/clip-findings.txt` line 3, a real banner in the retired form at
banner position, in a file NEITHER tool walks because both glob `*.md`. Grep
for the ruled colon banner at line start under `game-design/`: 141 lines in
135 files, consistent with 139 rewritten plus two written in the colon form
today. Grep for the retired form under `production/` and `ledger-v2/`: 0.
Under `legacy/`: 3, in the three superseded documents.

The resident's single most-wanted second reading, "278 changed lines and 0
outside the banner regex", could not be reproduced without git. What was
checked instead: the substitution is anchored at line start, matches only
`STATUS`, optional whitespace, an em-dash, optional whitespace, and replaces
that with `STATUS: `, so by construction it cannot touch any other character;
and the after-state carries zero retired banners at banner position in any
`.md` under the walked root. The resident's diff count stands as the
resident's.

Two comment faults, rule 1, dictated in section 6: the migration docstring
says "five" inline quotations exist and this sweep leaves them alone, and
seven exist. The five was counted with the first regex, which required the
bold marks; the regex was widened (its own comment says so) and the count
beside it was not re-read. And `tools/docs-check.py`, the checker that now
refuses an em-dash banner, prints an em-dash in the first line of its own
output (line 121) and carries twelve em-dash lines in all. Old text, and this
was the opportunity the formatting law means by "opportunistically". Folds
into queue 075.

### (a) Naming the unwalked trees is enough; no second sweep

`production/` and `ledger-v2/` carry zero retired banners, so there is
nothing to sweep. `legacy/` carries three in text that is superseded, not
read by docs-check, and covered by the law's "corrected opportunistically,
never rewritten wholesale". The NOT WALKED line names all three trees. What
the line does not name is non-`.md` files under the WALKED root, which is how
`clip-findings.txt` slipped; one dictated line fixes the file, and the
migration report should name its glob the next time the script is touched.

### (b) The import direction is backwards

One implementation of the retired form is right. The OWNER is wrong: the
permanent checker, wired into verify through `docs_shape`, imports its
definition from a one-shot script, so the day someone deletes
`migrate-status-banner.py` after it has done its only job, docs-check exits 4
and verify goes red. A permanent instrument must not depend on a transient
tool. Queue 075 moves `OLD_RE` into docs-check.py and has the migration
import it from there. Until then the migration script is not deletable, and
its header must say so: dictated in section 6.

---

## 3. The spawn log (`.claude/hooks/log-agent-stop.sh`, `tools/spawn-cost.py`)

What was read: both files in full, `.claude/settings.json`, the
`DIRECTOR_WORK` and `DIRECTOR_EVIDENCE` constants in `ledger/verify.py`
(lines 2446 to 2541), `production/queue/024-agent-log-completion-event.md`,
`production/budget.md`. Glob for `.claude/agent-turns.tsv`: absent.
`.claude/agent-log.tsv`: 239 data rows under a header. Grep for the sentence
attributed to Jafar, "so calibration is per tier and turns rather than per
spawn": it exists in the two builder files and NOWHERE ELSE in the tree.

### (a) Register the hook, in this commit, with two conditions

RULING: REGISTER IT. Reasons, in order of weight.

1. Rule 6. A hook nobody registered is a shim. Today `spawn-cost --report`
   prints "nothing measured" and will do so for ever.
2. Queue 024 step one asked for a PRINTED payload from a live SubagentStop
   event and said building on an unread payload is the fault. The builder
   substituted a read of the binary. That is better than a guess and it is
   not the measurement 024 asked for. The first real row IS that measurement:
   it proves `agent_type` and `agent_transcript_path` arrive populated on this
   install, or it proves they do not.
3. The downside is bounded: the hook always exits 0, returns no JSON, and
   cannot block a subagent from ending. The worst case is one dirty file.
4. The builder was right to decline the edit: settings is configuration and
   a tier-3 does not touch it on an agent's say-so. The escalation path for
   configuration is a director ruling, which this is; the resident applies
   the block dictated in section 6.

CONDITION ONE: `.claude/agent-turns.tsv` goes into `DIRECTOR_EVIDENCE` beside
`.claude/agent-log.tsv` in the same commit. `.claude/` is a WORK prefix
(verify.py line 2461), so without the entry every stop row counts as pending
work lines toward the 100-line cadence bound: the instrument feeding itself,
which is the exact reason agent-log.tsv is on that list. The recount comment
at lines 2483 to 2498 says to re-count on any edit; dictated.

CONDITION TWO: the first row is READ (rule 4) before any number from the
turns log enters a document. The director's next spawn produces it.

A record fault: the owner's words that justify this hook are quoted only by
the builder that built it. The primary record (the console rulings or
`production/decision-queue.md` RULED) must carry the sentence, or it is a
quote with no source. The resident, who received the words, writes them
there.

### (b) The budget document is amended, not restated per tier

Rule 2. The series measures TURNS; the budget is in POINTS; the conversion is
unmeasured, and a Fable turn carrying 32k thinking tokens and an Opus turn
reading one file are not the same cost. So "3.75x more turns" does not become
"3.75x more points" and no per-tier points figure is written today. What the
series does overturn is the claim that a single per-spawn figure describes
the studio: it averages two populations whose turn medians differ by nearly
four times, and its denominator was wrong twice over (see (c)). The
calibration paragraph in `production/budget.md` is replaced with the
dictated text in section 6, which names those three faults and the
measurement that replaces the figure: two paired readings, both meters from
Jafar and the turns log between them.

RULE 12 BINDS THE NUMBERS THEMSELVES. The series exists in a scrollback and
in two code comments and in the resident's message, and in no committed
file. Before any of 12, 45, 138, 170 or 148 enters `budget.md`, the resident
prints the series into `production/spawn-cost-series-2026-09-03.txt` with
`python3 tools/spawn-cost.py --transcripts <dir>` and commits it. If that
cannot be done in this session, the paragraph carries "nothing measured in
the tree" in place of the numbers and the sentence structure stays.

Three inconsistent statements of one idea, rule 1: `budget.md` says the flat
figure "averages a 30-turn director over a 100-turn builder" (a guess written
2 Sep), `spawn-cost.py` line 10 says "a 7-turn fable reviewer with a 107-turn
opus builder", the hook header says "a 12-turn fable reviewer with a 45-turn
opus builder". Dictated to one statement carrying the medians and the date.

### (c) 148 dead spawns: a finding, not an artefact, and already out of the medians

The instrument handles it correctly: a transcript holding only synthetic
lines has no model family, so `read_transcript` gives it tier `no-model` and
`by_tier` puts it in its own bucket. The fable 12 and opus 45 medians are
clean of them. They must stay out of the medians and IN the census, because
the census is what the old calibration divided by: if those spawns were in
the agent-log count that produced "1.5 to 2 points per spawn", the figure is
low per LIVE spawn. The cost of a dead spawn is near zero on the child (a
refused request) and unmeasured on the parent (the brief written, the
re-spawn), and the 22 that hit the wall AFTER doing work (170 minus 148) are
the expensive ones: work paid for and, unless resumed, lost.

Two things to print rather than assert. The builder's comment says 149 and
"21 of these"; the resident's brief says 148; the committed series settles
which. And 453 transcripts against 239 logged spawn rows is a gap of 214
that nothing explains: either the transcripts span more than this log's
history or something spawns without SubagentStart firing. The coverage pair
`spawn-cost --report` prints (rows with a turn record over rows in
agent-log.tsv) is the instrument; it needs the hook running. Queue 024 gains
this as its step (d).

---

## 4. The UV chain (`tools/ue/make_base_material.py`)

What was read: the whole file; `production/queue/062`; run 20's
`production/d1-probe/ue-build.txt` line 12 (`materialConnections=12/14
materialScriptReturn=2 materialNote=texcoord-to-maskU-refused/texcoord-to-maskV-refused`)
and the rest of that file, which shows the cook, the packaged binary, the
still and the four vignette frames all produced AFTER `materialScriptReturn=2`.

Verified by reading: the sweep contains `("", "Input")` at position 2 and a
selftest check (line 461) refuses the file if it is ever removed, so the
sweep cannot wire fewer than runs 19 and 20; a candidate that raises counts
as a no and not the end of the sweep (line 259); the tally counts one
connection per head however many names it costs (`w.record` is called once
per head, line 765), so the denominator stays 14; readback of the graph is
recorded for BOTH routes (line 762); and the property-write route returns
True only when the graph reads back connected (line 678), which is STRONGER
evidence for the count than the pin route's boolean. The selftest reproduces
run 19's shape as 12/14 PARTIAL and the passing shape as 14/14 MADE.

### The third outcome

RULING: the COUNT may include a head made by property write. The count is a
statement about what the editor holds, and readback is the same witness for
both routes; refusing to count a connection the graph provably holds would
make `materialConnections` lie in the other direction.

The STATUS WORD may not. `MADE` overclaimed once (run 19) and was repaired by
making it require the count; a second route into the same word whose shader
effect is unproven is the same class of overclaim in the same word, and the
stop rule and the acceptance line both read that word. So the third state is
a distinct word: 14 of 14 with any head made by property write prints
`materialStatus=WIRED-BY-PROPERTY-WRITE`, and `materialScriptReturn` stays a
function of the status (2, not 0; MADE is the only 0). The workflow cooks and
captures regardless of the return, as run 20 proves, so the still arrives
either way and the still decides. Queue 062's acceptance becomes: `MADE` on a
landed run, or `WIRED-BY-PROPERTY-WRITE` plus the four frames read by a
verifier and showing tiling.

This is a builder amendment (a parameter on `material_status`, one line in
`main()`, two selftest cases). It is a PRECONDITION TO THE NEXT UNREAL
DISPATCH, not to this commit: the file cannot run until
`production/d1-probe/DISPATCH` is touched, which this commit does not do, and
Jafar's "wait for now" holds independently.

### The stop rule is not discharged

The rule (3 September ruling, carried in queue 062): the fraction is the
reading, and if it holds across two landed runs, no further dispatch until
the wire is fixed. A script cannot discharge it; only a landed run printing a
moved fraction can. What this batch does is satisfy the rule's condition for
the NEXT dispatch: a changed instrument that measures nine names in one run
rather than guessing one per 25-minute round trip, which is what "make each
run maximally informative" means.

So this ruling authorises ONE dispatch, run 21, on two conditions: the
third-state amendment above has landed, and Jafar has lifted "wait". If run
21 prints 12/14 with `none-of-9-candidates..then.property-write-refused` or
`..unavailable`, that is the answer: no scripted route wires the head, D1's
hand-edit clause is invoked, and it is reported as an answer and not retried.

---

## 5. The commit

APPROVED as one commit under this ruling, containing everything the resident
listed plus the dictated edits in section 6 and the three queue files in
section 7. Nothing is held out. `production/d1-probe/DISPATCH` is not touched.
Stage by name. Run `python3 ledger/verify.py` after the edits; a red on the
new evidence entry's recount comment is a comment to fix, never a bound to
move.

---

## 6. Dictated edits, applied by the resident before the commit

D1. `game-design/clip-findings.txt`, line 3, replace the em-dash after
`STATUS` with a colon so the line reads
`# STATUS: LIVE, verified 2026-08-21.`; and line 1 likewise:
`# THE ANIMATION CLIP DEBT: measured, and counting down only.`

D2. `tools/spawn-cost.py`, lines 10 and 11, replace
`which averages a 7-turn fable reviewer with a 107-turn opus builder` with
`which averages a 12-turn fable median with a 45-turn opus median (transcripts on the build machine, 2026-09-03)`.
`tools/migrate-status-banner.py`, line 26, replace `Five of those exist` with
`Seven of those exist`.

D3. `tools/migrate-status-banner.py`, directly after the `OLD_RE` definition
(after line 59), add:

    # IMPORTED BY tools/docs-check.py AS ITS DEFINITION OF THE RETIRED FORM.
    # Deleting this file turns docs-check red (exit 4) and verify.py with it;
    # queue 075 moves the definition to the checker and inverts the import.

D4. `.claude/settings.json`, after the `SubagentStart` block inside `hooks`,
add the block the hook's own header dictates:

    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/log-agent-stop.sh",
            "timeout": 15
          }
        ]
      }
    ]

Then in `.claude/hooks/log-agent-stop.sh` replace the paragraph beginning
`# NOT REGISTERED YET.` (lines 32 to 35) with:

    # REGISTERED 2026-09-03 by director ruling (game-design/decision-2026-09-03-
    # batch-review-register-banner-spawnlog-uvsweep.md). The block below is the
    # one in .claude/settings.json; the first row it writes is read before any
    # number from the turns log is quoted anywhere.

D5. `ledger/verify.py`, `DIRECTOR_EVIDENCE`, directly after the
`.claude/agent-log.tsv` entry (line 2531), add:

    (".claude/agent-turns.tsv", "agentturns",
     "the SubagentStop rows .claude/hooks/log-agent-stop.sh appends: a tier "
     "and a turn count per finished spawn, machine-written, and counting it "
     "as work would let the instrument feed itself exactly as agent-log "
     "would"),

and re-count the comment above the tuple as it instructs: line 2484,
`Re-counted 3 Sep 2026, when the turns log was added: 6 of the 16 entries`;
line 2488, `and all three .claude/ machine files`; line 2537, `one of six`.

D6. `production/spawn-cost-series-2026-09-03.txt`: the output of
`python3 tools/spawn-cost.py --transcripts <the subagents directory the
builder read>`, committed as a file. If it cannot be produced this session,
this file is not created and D7 carries the words instead of the numbers.

D7. `production/budget.md`, replace the paragraph at lines 56 to 59 (from
`The live calibration, and it is weak:` to `is what replaces it.`) with:

    The live calibration, and it is weak in three named ways: a spawn costs
    roughly 1.5 to 2 points, derived 2026-09-02 from spawn counts in
    `.claude/agent-log.tsv` against Jafar's readings. (1) It is a flat
    average over two populations whose turn counts differ by 3.75x: on
    2026-09-03 the transcripts on the build machine read a fable median of
    12 turns and an opus median of 45, peak 138, series at
    `production/spawn-cost-series-2026-09-03.txt`. (2) Its denominator
    counted spawns that never produced a turn: 148 of 453 transcripts hold
    only a session-limit notice, so per LIVE spawn the figure is higher than
    stated. (3) Its denominator is 239 logged rows against 453 transcripts on
    the machine, a gap nobody has explained. Turns are not points: the
    conversion is unmeasured, and no per-tier points figure is written until
    two paired readings exist, both meters from Jafar and the turns log
    between them. Ruled 2026-09-03,
    game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md;
    queue 024 carries the measurement.

If D6 was not produced, the numbers in (1) and (2) read `nothing measured in
the tree` and the series path is omitted; the figures the resident and the
builder quoted are then not in this file.

D8. `production/NOW.md`. Line 3 becomes
`STATUS: LIVE. Verified 2026-09-03 after the batch ruling.` The bullet
beginning `**TWO BUILDERS RUNNING, on disjoint files.**` is replaced with:

    - **LANDED 2026-09-03, one commit, ruled in
      `game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md`:**
      the register gate (walks the outbox and the briefs on every verify; no
      real message is in the tree yet, so its live reading is
      `filesChecked=0/nothing-measured`), the banner law (135 documents
      migrated, the retired form refused), the spawn log's tier and turn
      fields (hook REGISTERED, first row NOT YET READ: read it before quoting
      it), and the UV head sweep (nine candidate pin names in one run, not
      yet dispatched). Open holes are queue 073, 074, 075 and the steps added
      to 024 and 062.

The bullet beginning `**THE UNREAL STOP RULE IS STILL IN FORCE` gains this
sentence at its end:

    062 landed the sweep; that does NOT discharge the rule. Run 21 is
    authorised once 062 step 2 (the third status word) has landed and Jafar
    lifts "wait"; if 21 prints 12/14 again, that is the answer and D1's
    hand-edit clause is invoked.

D9. Queue status lines. `production/queue/062-uv-chain-head-refuses-to-wire.md`,
line 3 becomes:
`acceptance: materialConnections=14/14 with materialStatus=MADE on a LANDED run, or 14/14 with materialStatus=WIRED-BY-PROPERTY-WRITE plus the four frames read by a verifier and showing tiling; never a local claim`
and this is appended to the file:

    ## STEP 1 LANDED 2026-09-03, STEP 2 BEFORE DISPATCH

    Step 1: the nine-candidate sweep, `materialUvHeadVia`,
    `materialUvHeadTriedAtWorst`, `materialUvHeadReadback`, selftest 11 to 30
    cases. Ruled: the count may include a head made by the last-resort
    property write; the status word may not. Step 2, a precondition to run
    21: `material_status` takes the count of heads made by property write,
    and 14 of 14 with that count above zero prints
    `materialStatus=WIRED-BY-PROPERTY-WRITE` with `materialScriptReturn=2`;
    two selftest cases, accepting first. Ruling:
    game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md.

`production/queue/024-agent-log-completion-event.md`, line 5 becomes:
`status: STEP 1 SUBSTITUTED 2026-09-03: the payload was read off the binary rather than printed from a live event, and the hook is now REGISTERED so the first real row is the printed payload 024 asked for. Read it. Then step (d) below. instrument-builder.`
and this is appended:

    STEP THREE (d), added 2026-09-03: the coverage pair. `spawn-cost --report`
    prints rows-with-a-turn-record over rows in agent-log.tsv; 453
    transcripts on the machine against 239 logged rows is unexplained, and
    148 of the 453 (149 by the code comment; the committed series decides)
    never produced a turn. Then the per-tier POINTS figure: two paired
    readings from Jafar, both meters, with the turns log between them. Until
    that prints, budget.md carries turns and not points per tier.

---

## 7. Queue items ordered (files written beside this ruling)

- `production/queue/073-needs-you-without-markers-passes.md`: the item parser
  hole in 1(c), with the fixture pair.
- `production/queue/074-latest-md-is-a-moving-name-on-a-frozen-list.md`: the
  hole in 1(b), and the night runner writing a non-register brief into a
  gated tree.
- `production/queue/075-docs-check-owns-the-retired-form.md`: invert the
  import in 2(b), and purge docs-check.py's own twelve em-dash lines while
  the file is open.

---

## 8. The quality ladder at close

Register gate: first working. Next rung is real messages in the outbox
producing the per-section series the advisory already prints, then a
per-claim bound read off it. Named in the step-2 ruling; not blank.

Banner law: best available for the walked root. Next rung is 075 (the
checker owns its definition). The unwalked trees are a decision the checker
already names, not a rung.

Spawn log: first working and not yet running. Next rung is the first row,
then the coverage pair, then the paired meter readings. Named in 024.

UV chain: a measurement replacing a guess, which is the right rung for a
question nothing in this container can answer. Next rung is run 21, and the
rung after it is the still gate reading tiling rather than a status word.

---

<!--RULING spawn=2026-09-03T15:59:53Z paths=.claude/settings.json,.claude/hooks/log-agent-stop.sh,.claude/agent-log.tsv,tools/producer-check.py,tools/migrate-status-banner.py,tools/docs-check.py,tools/spawn-cost.py,tools/ue/make_base_material.py,ledger/verify.py,production/outbox/README.md,production/briefs/2026-08-31.md,production/briefs/2026-09-02.md,production/briefs/latest.md,production/briefs/2026-09-03-directors-console-step-1.md,production/NOW.md,production/budget.md,production/decision-queue.md,production/spawn-cost-series-2026-09-03.txt,production/queue/024-agent-log-completion-event.md,production/queue/062-uv-chain-head-refuses-to-wire.md,production/queue/067-telegram-bot-on-the-pc.md,production/queue/068-the-five-second-glance.md,production/queue/069-the-health-panel.md,production/queue/070-show-moments-as-dated-rows.md,production/queue/071-cadence-and-landing-clean.md,production/queue/072-can-the-mobile-app-attach-to-the-pc-session.md,production/queue/073-needs-you-without-markers-passes.md,production/queue/074-latest-md-is-a-moving-name-on-a-frozen-list.md,production/queue/075-docs-check-owns-the-retired-form.md,STATUS.md,game-design/clip-findings.txt,game-design/**.md(135-banner-files),game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md-->
