# Ruling: queue 077, the gate's clock is the date in the file's name

> **STATUS: LOG, 2026-09-04.** Director ruling on the one-builder batch
> pending in the tree at spawn 2026-09-04T06:37:10Z: `tools/producer-check.py`,
> 285 insertions, 25 deletions, nothing committed. NOT CURRENT once the batch
> is committed; from then the committed tool, `production/NOW.md` and the
> queue items named in section 5 are the reading copies and this is their
> history.
Reviewed by reading under a budget cap (77 percent of an 80 percent weekly
limit). Section 0 says what was and was not measured.

VERDICT: LAND AS ONE COMMIT, with the two dictated edits in section 6
applied in the same commit (one sentence in the Producer's brief, one
correction line in the 3 September record and its copy in NOW.md).

## 0. What was measured, and by whom

Nothing was re-run in this spawn. The resident measured, in the turn before
this one, and the numbers are taken as printed: selftest 50 passed, 0 failed,
13 rejecting fixtures, 7 rejecting gate fixtures in 17 measured gate runs
(was 41); `--gate` PASS `filesChecked=1 filesExempt=5 filesWalked=6
filesDatePinned=1/1`; the same gate PASS at `--now 2026-09-08T12:00` (which
FAILED before the change at -51.0 hours) and at `--now 2027-06-01T12:00`;
single-file refusals at 4.0 hours and at 2.4 hours; gate refusal of an undated
name with a deadline (`filesDatePinned=0/1`); gate refusal of a same-day
deadline at 9.0 hours read at a 2027 clock.

What this spawn read, not ran: `MIN_DEADLINE_HOURS = 24` at
`tools/producer-check.py` line 76, unchanged; `deadline_hours` (lines 322 to
339), the UNPINNED branch of `check` (501 to 514), `gate_clock` (1140 to
1156), the per-file pin in `gate` (1254 to 1262); `ledger/verify.py` line
1083; `.claude/agents/producer.md` lines 93 to 119; queue 074; the 3
September record, section 1(a). Repo-wide grep for the token
`filesChecked=1`: one hit, the 3 September record line 60, out of the whole
tree.

## 1. Approve or reject: APPROVED

The named failure mode was a repair that lets both the served 57-hour deadline
and a 4-hour deadline through. Three measured refusals exclude it: 4.0 hours
refused in the single-file check; 9.0 hours refused by the gate at a clock two
years out, so the pin does not excuse a short deadline; an undated name with a
deadline refused as a finding, so the pin cannot be escaped by dropping the
date. The bound the rule reads did not move (line 76 is still 24). What moved
is WHICH instant the gate subtracts from, and the instrument now says which
one on every file (`asOf=`) and in the footer (`filesDatePinned=1/1`, a
numerator beside the count it was taken over). This is a repair.

One thing the batch is not: proof that the send check ran. See section 2.

## 2. Midnight is right, and the hole it does not open

The choice is between the three instants a day-only name can offer.

- Midnight (chosen). The gate's reading is always LARGER than any send-check
  reading taken later that day, so "the send check accepted it on day D"
  implies "the gate accepts the file dated D" at every future clock. That is
  the property queue 077 was opened for, and it holds only at midnight.
- End of day. The gate reads up to 24 hours FEWER than the send check did, so
  a message accepted at 09:00 with a 27-hour deadline goes red at commit.
  That is the landmine back in a different costume.
- Noon. Neither property, and a message accepted before noon can still be
  refused after it.

Midnight is right. The hole the resident asks about is real but is not opened
by midnight; it is opened by the name carrying a DAY rather than an instant,
and every in-day pin has it at some width. Its shape: a writer who skips the
send check can commit a next-day ISO deadline (read as 09:00, so 33.0 hours
from midnight) at 23:00 on the file's date, 10 real hours out, and the gate
passes it. A backdated filename is the same hole one day wider. Today the
writer is the Producer agent following a brief, not an adversary, and the
send check is the instrument for the 24-hour floor; the gate's promise is the
narrower one it can actually keep: never a same-day deadline, never an undated
deadline, never a retroactive refusal.

THE NEXT RUNG, which closes the hole and is a rule 6 item in its own right,
because nothing in the tree currently proves the send check was ever run:
the single-file check, on acceptance, writes the instant it accepted into the
file (one `checked-at: <ISO datetime>` line); the gate pins to that stamp when
present, requires the stamp's date to equal the date in the name, and falls
back to midnight of the name only for files older than the stamp. Then the
artifact carries the evidence that the call happened. Queue it, small; not in
this batch.

## 3. UNPINNED is a finding, and 074 gains one line

Right. The two alternatives are both the landmine: a wall-clock fallback for
undated names re-imports the time bomb for exactly the files that are hardest
to see, and a pass makes "drop the date" the way round the floor. A finding
that names the fix in its own text (line 511: "Name the file
`<YYYY-MM-DD>-<slug>.<kind>.md`") is the honest third state, and the footer
counts it (`filesDatePinned=n/checked`), so an unpinned file cannot hide in a
green run.

Today nothing rides on it: `latest.md` is on the frozen list, so the gate
never reaches its deadline rule, and the 1/1 is over the one file actually
checked.

Queue 074 changes by one line, not in direction. Under its option A (verdict
of whichever dated brief `latest.md` is byte-identical to) the gate must take
the CLOCK from the matched brief as well as the verdict, or a copy that is a
faithful image of a passing brief comes out UNPINNED and red. Under option B
`latest.md` leaves the gated trees or carries no deadline, and the question
does not arise. Add to 074's acceptance line: "`latest.md` never reaches the
deadline rule UNPINNED: it either inherits the clock of the dated brief it
resolves to, or carries no deadline." The lean to B stands.

## 4. Recording the overturned conclusion: both places, neither rewritten

The 3 September record, section 1(a), ordered the first real message filed so
that "the gate's first live reading becomes `filesChecked=1`", and NOW.md
recorded that reading as answering the no-accepting-artifact concern. The
builder showed the reading was accepting at ONE instant and would have turned
red on 2026-09-05T09:01Z with nothing in the tree changing. That is rule 5b
in its time-dependent form: a guard that reads a clock has been watched
passing only when it has been watched passing at two instants further apart
than its bound. The instrument now prints that (three `--now` values, one
verdict).

How it is recorded, ruled:

- The 3 September record is LOG. It is not rewritten; a dated correction
  line is APPENDED at the site, directly under section 1(a), pointing here.
  Text in section 6.
- NOW.md is LIVE. Its sentence is REPLACED, not annotated; a live file
  carries the current state and nothing else.
- This record carries the full overturn (this section).
- Rule 1: grep for the SENTENCE, not the site. The token `filesChecked=1` has
  one hit repo-wide (the old record, line 60); NOW.md phrases the same
  conclusion differently, so the resident greps NOW.md for the wording used
  there before editing, and reports the hit count in the commit message.

Suggested, not ordered: one paragraph under rule 5b in
`ledger-v2/studio-v2/casebook-claims.md` recording the incident, since it is
the first time a guard here passed by being read at a lucky instant. Queue
it with the other doc items if the resident agrees; do not write it now.

## 5. The six noticed items

(a) QUEUE, small, as one item with (b): every rejecting gate fixture names
the rule it expects to be refused under (a fixture that asserts only
"refused" cannot tell the right refusal from a wrong one, rule 5b), and the
reason map already exists. Acceptance: 7/7 gate fixtures name a rule.

(b) QUEUE, folded into (a): one derivation of `linked_sections`, the two
discarded ones removed, grep shows one site.

(c) DROP AS A QUEUE ITEM, APPLY AS DICTATED TEXT. The convention is already
written where the writer reads it (`.claude/agents/producer.md` lines 96 to
98, and `production/outbox/README.md`); what is missing is one sentence
saying the date is the clock. Section 6 dictates it.

(d) The resident is right. "Landed on 2026-09-03 with 30 passing assertions
over 13 rejecting fixtures" is a dated claim about the landing, and the
resident's own series (30 at landing, 41 before this batch, 50 after) shows
the count has moved twice since. Refreshing it to 50 would misdate a live
count as the landing count and be stale by the next fixture. DROP the update.
If that docstring is ever touched for another reason, cut the count rather
than refresh it: the verify footer prints the live number. This spawn could
not check 30 against history; the resident holds that series.

(e) DROP. Seventeen gate runs over six files, no measured cost, and rule 2
forbids a bound without a series. The selftest already prints its run count,
which is the series; revisit when the outbox is large enough for someone to
notice the wait.

(f) FOLD INTO (c): one clause in the dictated sentence. The code (line 337)
reads `tomorrow` as 24.0 flat and never resolves it against any clock, so the
honest description is "literal hours, no clock", not "the day after the
file's date".

## 6. Dictated edits, applied in the same commit

6.1 `.claude/agents/producer.md`, directly after the three filename patterns
at lines 96 to 98, one paragraph:

    THE DATE IN THE NAME IS THE CLOCK. `producer-check --gate` measures every
    deadline in a file from midnight of the date in its own name, so a file
    is dated the day it is sent and never earlier, and a name without a date
    fails the gate the moment it states a deadline. The pre-send
    `producer-check <file>` still measures from the wall clock, and a
    deadline must clear the 24-hour floor on both. An ISO-date deadline is
    read as 09:00 on that day; a relative form (`tomorrow`, `2 days`) is
    read as its literal hours against no clock at all.

6.2 `game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md`,
appended as the last paragraph of section 1(a), after line 69:

    CORRECTION 2026-09-04. `filesChecked=1` was an accepting reading at one
    instant only: the gate measured deadlines from the wall clock and this
    message would have gone red at 2026-09-05T09:01Z with nothing in the tree
    changing. The concern in this section is answered by the reading at
    three instants in one run, not by this one. Ruled in
    `game-design/decision-2026-09-04-ruling-077-deadline-clock-pin.md`,
    section 4.

6.3 `production/NOW.md`: the sentence recording `filesChecked=1` as answering
1(a) is replaced by: "The register gate's accepting artifact is the served
message read at three clocks in one run (`--gate`, `--now 2026-09-08T12:00`,
`--now 2027-06-01T12:00`, all PASS, `filesDatePinned=1/1`); the single
reading of 3 September was accepting at one instant only, ruling of 4
September section 4."

6.4 Queue 074: the one acceptance clause from section 3.

## 7. Queue items the resident files (names suggested)

- 080 producer-check: send check stamps its accepting instant into the file;
  gate pins to the stamp (section 2). Small. Closes the rule 6 gap on the
  send check.
- 081 producer-check tidy: 7/7 gate fixtures name a rule; one
  `linked_sections` (section 5 a and b). Small.

RENUMBERED BY THE RESIDENT, 2026-09-04. This ruling suggested 078 and 079 and
both were already taken, by the exclusion-list inventory and by the queue gate
that reads the retired `game-design/queue.md`, filed overnight while this
review was not yet running. Filed as 080 and 081 instead. The collision is the
same one that put the tokens-per-point item at 076: a director and a resident
both pick the next free number from a directory listing taken at different
moments.
- Optional: casebook-claims paragraph under 5b (section 4).

Not filed: (d), (e).

## 8. Quality ladder at close

First working, not best available, and the next rung is named: 078. The gate
now keeps a promise it can prove at every clock; the 24-hour floor at send
time is still kept only by a check nothing proves was run.

<!--RULING spawn=2026-09-04T06:37:10Z-->
