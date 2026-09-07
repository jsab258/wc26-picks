# Ruling: the inbox push fix, the plain failure sentence and the reading gate. LAND WITH AMENDMENTS

> **STATUS: LOG, 2026-09-07. NOT CURRENT** once the amended commit lands.
> Director ruling, spawned 2026-09-07T09:23:06Z, killed by a session limit at
> 10:20 UTC before it ruled, resumed 2026-09-07T10:22:00Z on the same
> uncommitted tree after `748bdf0a`: `tools/runner/inbox.py`,
> `tools/runner/outbox.py` (one call site), `tools/runner/telegram-bot.py`,
> `production/findings.txt`. 419 changed lines in the tools scope against the
> inherited 100. From the landing on, the files are the reading copies and
> this is the record of why.

VERDICT: LAND WITH AMENDMENTS. Two block the commit, because each is a false
number in the first sentence his phone shows after he restarts the bot, or
evidence he asked for that is built and does not travel:

- B1. Every count of "message(s)" his phone and the PC window print is the
  count of ALL pending files, receipts and rulings included. On his PC today
  that first sentence reads as the 254 messages plus every outbound record
  his disk holds. Section 4.
- B2. A reply's receipt, the evidence he asked for by name, is written and
  then waits for his NEXT message before anything pushes it, while the window
  says it reaches the studio on the next flush. Section 5.

A1 to A6 ride the same builder pass and do not block on their own (section
9). Everything else lands as read: the three-value split at the helper, all
seventeen call sites, the `plain` and `detail` pair through `held`, the
shape gate on readings with the never-round ruling intact, the autocrlf
accepting case with its rejecting half, the deferral of the two latent sites.

NOTHING WAS RUN. No shell in this seat. The counts in the brief (64, 82, 12,
47, 117) are the coordinator's, quoted; section 8 says what the cases I read
cover and what they cannot. The 178-character reproduction is the builder's;
section 1 checks its arithmetic against the code and does not re-measure it.

## 0. What was read, what was not run, and what I was told

Read whole: `tools/runner/inbox.py` (1121 lines); `tools/inbox-read.py`
(553); `tools/runner/outbox.py` (1417, two pages); `production/findings.txt`;
`production/inbox/README.md`; `production/outbox/README.md`; queue 106; the
ruling of 2026-09-07T00:07:11Z for shape and the head of 2026-09-05T11:26:37Z.

Read in part: `tools/runner/telegram-bot.py` 96 to 1041 and 1064 to 1802
(everything but the imports and `main`); `tools/pc-watcher.py` 515 to 535,
650 to 682, 700 to 800, 895 to 924; `tools/runner/executor.py` 628 to 660
and 715 to 745; `ledger/verify.py` 1080 to 1180, 3096 to 3250, 5212 to 5360
and every line matching `RULING|spawn=`; `tools/docs-check.py` by grep for
the banner form; `tools/producer-check.py` by grep for `GATE_TREES`;
`.claude/agent-log.tsv` 316 to 325; `.git/logs/HEAD` 432 to 439.

Counted by grep, rule 6: `git_call(` outside `inbox.py` matches ONE caller
of the inbox helper (`outbox.py:366`) and eleven calls of the executor's OWN
`git_call` plus its definition, which is a different function with a
two-value return that this batch does not touch. Inside `inbox.py`: sixteen
sites, listed in section 2. `p.stdout + p.stderr` glued across `tools/`:
eleven sites, of which four are helpers whose callers parse a value
(section 6 and the fixture helper at `inbox.py:799`) and the rest are log
tails or check output merged on purpose.

THE REFERENCE AND THE ROWS. HEAD is `748bdf0a` at 1788754551, which is
2026-09-07T04:15:51Z (1788739200 is midnight of the 7th, checked against
the 20:39:15Z reading in the previous ruling). The reference commit is at or
before HEAD. Studio-director rows after it: line 322, `2026-09-07T09:23:06Z`,
and line 323, `2026-09-07T10:22:00Z`. Neither is named by any stamp under
`game-design/` (0 matches for `spawn=2026-09-07T09` and `T10`). The first is
this review's spawn, the second its resume; both stamps are at the foot, and
the 25 Aug precedent in `director_cadence`'s docstring is that a resumed
director stamps the resume row.

PREMISE, CLAUDE.md section 0: standard library only, nothing purchased, no
licence entry, no account used. Item (a) of his order is the inbound half of
the one channel he has to the studio, and item 2 of the Meridian Test cannot
be measured by a director who cannot hear him. Nothing here contradicts the
premise or touches the game.

HIS WORDS, AS THEY REACHED ME. The brief gives three ordered instructions:
find and fix the failing push; failures as one plain sentence saying what
failed, whether his message is safe, what happens next, internals to the
log; stop parsing his ordinary questions as budget readings. The code
carries two quotations attributed to him today: `push_pending` 562 to 567,
"failures read as one plain sentence: what failed, whether my message is
safe, what happens next; internals go to the log", and
`looks_like_a_reading` 314 to 316, "only parse a reading when the message is
a bare number or answers a reading request". Neither sentence exists
anywhere else in the repository (grep over `.md`, `.txt`, `.tsv`, `.json`,
`.py`), so this record is where they are written down, and section 3 notes
where the second one and the code differ.

## 1. The diagnosis, re-derived from the code rather than from the brief

THE OLD SHAPE. `git_call` returned one string, stdout and stderr glued, and
`push_pending` tested it against `^[0-9a-f]{40}$` after `hash-object`. On a
checkout with `core.autocrlf` on, `hash-object -w --path <rel>` runs the
line-ending conversion, succeeds on stdout with the sha, and prints on stderr
"warning: in the working copy of '<rel>', LF will be replaced by CRLF the
next time Git touches it". Glued, the match fails; the caller reports "could
not store"; nothing is pushed; the message stays on disk; the retry a minute
later does the same. That is a six-day silent stop with a green exit code
under it, and the class is exactly rule 12's: the feedback channel itself
was the broken thing.

THE ARITHMETIC OF 178. The flattened old string is the sha (40), a space
(1), the warning's head "warning: in the working copy of '" (33), the path,
and the tail "', LF will be replaced by CRLF the next time Git touches it"
(59), so 133 plus the path length. 178 needs a 45-character relative path,
which is `production/inbox/` (17) plus `YYYY-MM-DDTHHMMZ-` (17) plus `.md`
(3) plus an eight-digit update id. The old message capped that string at
120 and announced 58 dropped, which is what he saw. Consistent; not
re-measured here; and the wording is the modern git form, so a PC running an
older git would have shown a different count and the same fault.

THE FIX IS AT THE RIGHT LEVEL. `git_call` (162 to 212) now returns
`(rc, stdout, stderr)`, each stripped, with the four failure returns (126
refused, 127 no git, 124 timeout, 125 OSError) putting their reason in the
third slot and an empty second. `why(out, err)` (156 to 159) reads stderr
first, stdout only when stderr is empty. A value parsed out of a diagnostic
stream is a class of bug, and the split at the helper means no future
caller in this file can reintroduce it. Ruled correct.

THE ACCEPTING CASE HAS ITS REJECTING HALF INSIDE IT (1075 to 1106). The
fixture turns `core.autocrlf` on in a real repository, writes a message with
LF, runs the real `hash-object` through the real `git_call`, and asserts
three things in order: rc 0 and a 40-hex sha on stdout; the words "warning"
and "crlf" on stderr, so a git that stopped warning fails the case rather
than passing it vacuously; and "warning" absent from stdout. Then
`push_pending` lands the file and `pending_all` is empty. That is rule 5b as
written. What it cannot prove: that his PC's git prints the same warning
(the incident already proved that) or that the push succeeds against GitHub
from his PC (section 8).

ONE COUNT IN THE DOCSTRING IS WRONG. `git_call` 175 to 176 says the split
is "at this level rather than at the four call sites". Seven sites in this
file parse a value from stdout (section 2), eight with `outbox.py`. A6.

## 2. Question 1: the seventeen call sites, read one by one

Value sites, where stdout is parsed and stderr must not reach the parser:

- 410, `log -1 --format=%ct <ref>`: `out.strip().isdigit()`, stdout. Right.
- 507, `rev-parse --verify --quiet <tip>^{commit}`: sha regex on stdout. Right.
- 523, `ls-tree -r --name-only`: paths split from stdout. Right.
- 624, `hash-object -w --path`: sha regex on `blob`, `warn` read only by
  `why` on failure. THE FIXED LINE. Right.
- 640, `write-tree`: sha regex on `tree`. Right.
- 655, `commit-tree`: sha regex on `commit`. Right.
- 674, `ls-remote origin refs/heads/pc-inbox`: `remote.split()[0]`, stdout,
  guarded by `rc == 0 and remote.strip()`. Right, and this is the effect
  check the CI rule asks for.
- `outbox.py:366`, `log -1 --format=%H %ct -- <rel>`: `out.split()` on
  stdout. Right.

Diagnostic sites, where only rc decides and both streams feed `why`:

- 612 and 616, `read-tree <tip>` and `read-tree --empty`. Right.
- 633, `update-index --add --cacheinfo`. Right.
- 664, `push --force`: rc only, `why(pout, perr)` into `detail` at the 160
  cap. Right.
- 683, `update-ref`: result discarded, with the comment saying why. Right.

Selftest sites:

- 904, `rev-parse HEAD`: `len(out) == 40` on stdout. Right.
- 906 and 909, the refused `fetch` and `pull`: the reason is read from the
  THIRD slot (`rc, _o, out`), which is where the 126 return puts it. Right.
- 1089, the autocrlf `hash-object`: sha from the second slot, warning from
  the third. Right.

No site was converted the wrong way. `blob.strip()`, `tree.strip()` and
`commit.strip()` re-strip what `git_call` already stripped; harmless.

## 3. Question 2: does the reading gate change anything he did not ask for

WHAT THE GATE DOES (`looks_like_a_reading` 311 to 334, the call at 789).
After removing "percent", "per cent" and "%", the message must match
`^[+-]?\d+(?:[.,]\d+)?$`. So "77", " 77% ", "77 percent", "+77", "76.5",
"76,5", "77.0" and "101" all still reach `parse_reading` and are taken or
refused exactly as the 2026-09-05 ruling says; the selftest rows at 1468 to
1476 hold five of the refusals and 1489 to 1492 the next good one. Prose
falls through to the filing path with no refusal. `pending` is untouched, so
the question stays open and `/budget` or a bare number still answers it.
That is item (c) as the brief states it, and the never-round ruling is
intact. Ruled correct.

WHAT HE DID NOT ASK FOR AND NOW GETS, in two shapes.

The trailing full stop. "77." does not match: the optional group needs a
digit after the point, so the regex ends at "77" with "." unmatched. Before
this batch "77." went to `parse_reading`, was refused as not a whole number,
and he was told what to send. Now it is filed as a message for the studio
with the echo and the awake sentence and no read-back. A phone that inserts
a full stop on a double space produces exactly this string. The same holds
for "77!" and "77 %.". It is not silent in the strict sense, because the
reply is the filing reply rather than "Read back: total 77 percent", but no
sentence says it was not taken. A1 makes one trailing full stop part of the
number's shape in BOTH functions, which is not a rounding and not a guess:
"77." records 77, "77.." and "76.5" are still refused. A1 rides the pass.

The worded reading. "total 77", "77 and 62", "it's about 77" are prose by
his own word "bare", and prose they stay. During an open question a prose
message that carries a digit is the ambiguous case, and A2 gives it one
sentence on the filing reply: the question is still open and a bare whole
number answers it. Not a refusal, not a lecture, and absent from prose with
no digit in it, so it does not follow him around for the hours the question
stays open.

WHERE HIS SENTENCE AND THE CODE DIFFER, recorded and not built. The quoted
sentence says "a bare number OR answers a reading request". The code
implements "a bare number WHILE a request is open". A message that answers
the request in Telegram's own sense, a swipe-reply to the budget question,
carries `reply_to_message` with the question's message id, and the receipt
this batch adds is exactly what would let the bot know that id. That is the
literal second half of his sentence and it is not in this batch. Filed
(section 11, a). If the brief's rendering is his words and the docstring's
is the builder's, nothing is missing; the record says both so the next
reader does not have to guess.

## 4. Question 3: does anything of git's reach the chat, and B1

EVERY PATH TO HIS PHONE, read: `reply_text` failure (777 to 785) and
`ruling_reply_text` failure (744 to 757) both go through `plain_failure`
(760 to 774), which reads `plain` and never `detail`, and whose fallback
when `plain` is unset is words rather than git's text. The three `PLAIN_`
constants (568 to 570) carry no sha, no path, no rc. `held` (573 to 581) is
the only way a failure return is built, so the pair cannot drift. The
selftest asserts the absence of "fatal:", "error:", "warning:", "git ",
"not shown", "origin", "refs/" and "production/inbox/" on the failure reply
(994 to 998), and the bot's own row does the same on the held-message reply
(1507 to 1510). The success replies name the file and the branch by design;
`flush_inbox`'s and `skip_backlog`'s replies carry no git text. Two paths
print a Python exception type name to his phone (`file_message` 710 to
712, `handle_callback` 880 to 883); not git's, not this batch's, filed
(section 11, c). RULED: nothing of git's reaches the chat on any path.

B1, THE NUMBER THAT DOES. `push_pending` sets `pending` and `pushed` from
`pending_all` (595, 690), which is messages plus outbound records plus
rulings (`tracked_files` 308 to 311). Four sentences then call that count
"message(s)":

- `plain_failure` 771 to 774: "Nothing is lost: %d message(s) are waiting".
- `flush_inbox` 742 to 744: "The %d message(s) I was holding on the PC are
  on the branch now."
- `file_and_push` 713 to 717, the window: `inboxPending=%d` and
  `inboxPushed=%d/%d`, whose docstring at 548 to 552 says the bot's
  `inboxPending` is about his messages and must not fold receipts in.

Before this batch outbound records were rare (a Producer send, a refusal).
After it every reply writes one, so the inflation is systematic: one held
message, one reply, one receipt, and the next failure says "3 message(s)
are waiting" after he sent two. And the FIRST sentence his phone shows after
he restarts the fixed bot comes from `flush_inbox(every=0)` at `run()` 1094:
"The N message(s) I was holding", where N is the 254 plus every outbound
record on that disk that no push has ever carried (the outbox README at 121
to 124 says two refused records are expected there if the sweep ever ran;
that is a prediction, not a count). A false number on the one path this
batch was built to make truthful. Rule 3b. BLOCKS.

The existing selftest cannot see it: the held-push case (967 to 1010) runs
before any receipt exists in that fixture, so `pending` is one message and
"1 message(s)" is true there.

## 5. Question 4: the reply receipt, B2 and the denominators

WHAT IT WRITES (`record_reply` 635 to 671). One `.receipt.txt` per reply
with a message id, named `<utc>-reply-<id>.receipt.txt`, kind
`reply-to-his-message`, through `outbox.render_receipt` with no file
commit and a stated reason for the missing latency. The name matches
`OUTBOUND_RE` (the row at 1537 to 1539 asserts it), so the container reader
delivers it and the branch carries it. Written after the send, so a send
that throws leaves no receipt. The rejecting row (1549 to 1552) proves no id
means no file. Correct as far as it goes.

B2, IT DOES NOT TRAVEL. `flush_inbox` (721 to 747) decides whether to push
from `pending_files` (733), which is messages only; `outbox_pass` pushes
only when the sweep wrote a record of its own (1124 to 1125);
`frames_pass` likewise (1188). So a receipt reaches the branch only when
something else pushes: his next message, his next tap, a Producer send. At
startup the opening line and the budget question write two receipts and
the flush at 1094 pushes nothing unless messages are held. The window then
says "It reaches the studio on the next flush" (668 to 670), which is
false. For the round trip he wants proven today: he sends one message, the
bot replies, the receipt sits, the studio reads the message and cannot
report the reply's id until he sends a second one. Built, not running, on
the path it was built for. Rule 6, rule 1. BLOCKS.

THE HAZARD IN THE OBVIOUS FIX, stated so the builder does not walk into it.
If `flush_inbox` triggers on `pending_all` and keeps its reply, then a
receipt-only push sends "The 1 message(s) I was holding", that reply writes
a receipt, the next flush pushes it and replies again, and his phone gets
one message a minute for ever. The reply after a flush must be sent only
when the pushed set contains a message or a ruling; receipts alone push in
silence with a window line. Section 9 states the behaviour and the two rows
that hold both halves.

THE CONTAINER'S DENOMINATORS. `outbound_summary` (770 to 793) files every
`receipt: sent` record under `sent`, so the done line `outbound: records=N
sent=K refused=J` that queue 089 defined as "Producer messages that reached
his phone" now counts bot chrome in `sent`. One key, two meanings. And
`outbound_lines` prints one line per sent record for every record on the
branch, for ever, so the turn-top report grows by a line per reply with no
cap and no announcement; `outbound_from_branch` (163 to 182) runs one `git
show` per record per run, so the reader's cost grows the same way. A4 gives
the summary a `replies` bucket keyed on the bot's kind, keeps `sent` as
Producer messages, and prints replies as one tally line carrying the newest
id. The reader's growth is filed (section 11, b), because it is the
container half and the fix is a disk check before each `show`.

HYGIENE, A3. The kind is wrong for the two startup messages, which reply to
nothing; the receipt's `sentEpoch` is the PC's clock at 657 when the
platform's result carries `date`; and the file is opened without
`newline="\n"` at 660, unlike every other writer on this branch, whose
docstrings say why (`write_message` 380 to 383).

`tools/inbox-read.py` needs no change to deliver them: the pattern accepts
the name, `deliver` skips files already on disk, and queue 106's untracked
gate does not watch `production/outbound/` at all, which is now a larger
hole than when it was filed and is named again in section 11.

## 6. Question 5: the two latent instances, and whether to fix pc-watcher now

`tools/pc-watcher.py:git` (524 to 527) returns one glued string. The sites
that parse a sha, read at the line:

- 724, `rev-parse FETCH_HEAD` in `resync`, then `reset --hard <that>` at
  736. A glued string is not a ref: `reset --hard` REFUSES it, `resync`
  returns False, the pass stops. Safe direction, and it stops every pass.
- 763 and 776, `rev-parse HEAD` and `rev-parse FETCH_HEAD` in
  `deliver_before_discard`, compared to each other and to `branch_sha`.
  Warnings from the same git in the same repository are the same text on
  both, so the equality tests still answer correctly; the ancestry test at
  769 with glued arguments fails closed and the code then fetches and
  compares, which again holds. Then the reset above refuses.
- 908 and 916 in `publish`: the same equal-glue argument, or a false "PUSH
  SENT NOTHING" and a stopped pass.
- 1110 is a selftest fixture. 668 is a log tail, merged on purpose, and is
  not an instance.

So the shape on his PC is: nothing is reset to the wrong place, and the
whole PC pipeline stops with the reason in a window nobody is watching,
which is the inbox incident's shape in a different tool. The trigger it
needs is git writing to stderr on `rev-parse`, which autocrlf does not
cause (no working-tree file is touched). One trigger IS plantable, and it
is the accepting fixture the fix will need: a branch named `FETCH_HEAD`
under `refs/heads/` makes the bare name ambiguous, and git resolves the
pseudo-ref while warning about the ambiguity. I state the wording from
memory of git's ref code and not from a run; the fixture must print it.

`tools/runner/executor.py:723` parses `rev-parse --short HEAD` into a label
for the status line and nothing branches on it. Harmless.

A THIRD INSTANCE, not in `production/findings.txt`. `tools/inbox-read.py:
git_run` (61 to 73) glues too, and its shape is worse than a failed parse:
`records_from_branch` (143) and `outbound_from_branch` (180) take `git show`
output as the RECORD BODY and `deliver` writes it into this checkout, so a
stderr line from that git would be written into the file as content, and
`read_inbox` (230) does the same with his message text. It runs in the
container on Linux, where nothing has warned yet. A6 adds it to the
findings file in the same words as the other two.

RULED: the deferral stands. The fault is real and fails in the safe
direction; Jafar's standing rule for this batch is no work outside the
ordered items until the round trip is proven; and a change to the tool that
hard-resets his checkout is the one change that should not ride a batch
whose purpose is to get a message through. It is the FIRST item after the
round trip is proven, all three files in one pass, each with a planted
warning as its accepting case, and it goes in the queue with a name now
(section 11, d). Not a research task: the worked example is in `inbox.py`.

## 7. Scope, and the ladder

ASKED: (a), (b), (c), and the receipt he asked for by implication when he
asked for the reply's id. Every changed line I read is one of those four.
The findings file is the right place for what was found and not done, and
it says why.

ADJACENT, named and not done here: the reply-to half of his sentence (a),
the reader's growth (b), Python type names on his phone (c), the three
glued helpers (d), queue 106 (e).

THE LADDER. The split at the helper is the best available for the fault:
not a second regex, not a filter on the warning's text, and no future
caller can regress it. The plain sentence is best available for what he
asked: three facts in his order, a helper that makes forgetting impossible,
and a selftest that checks each fact by name. The reading gate is first
working, and its next rung is not blank: A1, A2, and the reply-to half.
The receipt is first working; B2 makes it run, A3 and A4 make it honest,
and its next rung is the reader that stops re-reading what it already has.

## 8. What the green counts cover, and what they cannot

Covered in the container, and I read the cases: the split on a real
repository with the real warning; both refusals of the whitelist through the
third slot; the held message, its plain sentence checked fact by fact, its
window half, its recovery; the shape gate both ways with five refusals, one
prose message during an open question, and the next good reading; the
receipt with an id, the receipt refused without one, the name the reader
accepts, and the file's presence in `pending_all`; the wiring rows in the
bot with `reply` captured so nothing touches the wire.

NOT covered, and not coverable from here: the push against GitHub from his
PC with his credential; his git's warning wording; whether `flush_inbox`
at startup carries the 254 in one commit (the arithmetic says one
`commit-tree` and one push, and ~500 short git processes before it); the
sentence on his phone that comes out of that flush, which is B1's; the
receipt's journey, which is B2's. The first restart is the accepting case
for all of them, and after the amendments its failure modes are counted
rather than silent.

The 82 in the bot's suite is the harness count after `botconfig` runs
inside it; the row at 1783 prints the two exits side by side, so a red
config reader cannot hide under a green case count. Read, not run.

## 9. The amendments, stated as behaviour

B1, `tools/runner/inbox.py` and `tools/runner/telegram-bot.py`, BLOCKS THE
COMMIT. `inbox.py` gains one helper that counts the entries of a path list
under `INBOX_DIR`, and the result of `push_pending` carries the split
alongside the lists. `plain_failure` with the noun "message" says how many
MESSAGES are waiting, and when other records are waiting too it says so in
its own clause ("and K record(s) of the PC's own"); with the noun "item" it
counts everything, as now. `flush_inbox`'s reply counts messages the same
way. `file_and_push`'s window keys `inboxPending` and `inboxPushed` count
messages, with a second pair for the records so the window loses nothing.
Selftest: one row plants a receipt beside one held message with the push
remote broken and asserts "1 message(s) are waiting" and the clause naming
one record; one row asserts the recovery reply says one message; one row
asserts the window keys.

B2, `tools/runner/telegram-bot.py`, BLOCKS. `flush_inbox` decides from
`pending_all` and pushes whatever is waiting. It sends the phone reply ONLY
when the pushed set contains at least one path under `INBOX_DIR` or
`RULING_DIR`; a push of receipts alone writes one window line naming the
count and sends nothing. The window line in `record_reply` becomes true as
written. Selftest, accepting case first: a held message beside a receipt,
flush pushes both, exactly one reply, counting one message; then a receipt
alone, flush pushes it, `pending_all` is empty, and `said` is unchanged.
The second row is the guard against the one-message-a-minute loop, and it
must exist before the trigger changes.

A1, same file and the same pass. `looks_like_a_reading` and `parse_reading`
each remove ONE trailing full stop after the percent words, before the
shape test. "77." records 77; "77..", "76.5", "77.0" are refused as now.
Two rows: accept "77." as 77 through `handle_text` with the question open;
reject "77..". Recorded here as consistent with the 2026-09-05 ruling: no
rounding, no guessing, the same class of stripping as "%".

A2, same file. When `pending` is set and a message is filed as prose, the
filing reply carries one sentence if and only if the message contains a
digit: "The budget question is still open; a bare whole number answers it."
Three rows: digit during an open question, sentence present; no digit,
absent; digit with no open question, absent.

A3, same file. The receipt's kind is `bot-message`; `sentEpoch` is the
platform's `date` from the result when it is an int, the PC's clock
otherwise with the window saying so; the file is opened with
`newline="\n"`. One row asserts the kind and the epoch from a planted
result carrying `date`.

A4, `tools/runner/outbox.py`. `outbound_summary` files records whose kind is
`bot-message` under a new `replies` list; `sent` keeps its meaning;
`outbound_lines` prints replies as one line, `outbound replies=K
newestMessageId=<id>`, and the done line gains `replies=K`. Two rows: a
planted reply receipt lands in `replies` and not `sent`; the done line
carries both. `tools/inbox-read.py` needs no change for this; its selftest
tally row (473 to 475) still holds because it plants no reply receipt.

A5, `tools/runner/inbox.py` 175 to 176. "the four call sites" becomes the
counted seven, eight with `outbox.py`.

A6, `production/findings.txt`. The 2026-09-07 entry gains
`tools/inbox-read.py:git_run` with its three sites (143, 180, 230) and the
sentence that its shape is content written into a record rather than a
failed parse. Dictated text, hand-applied.

The builder states the new selftest counts; this record does not guess them.

## 10. What the resident prints before the commit

1. The builder's diff for B1, B2 and A1 to A6, read against sections 3 to 5.
2. `python3 ledger/verify.py`, the footer pasted FROM `ledger/.verify-footer`.
   Expected: the six selftest rows green with counts above 64, 82, 12 and 47
   by the stated numbers; the cadence line naming this record and one of
   the two rows below; `docs` clean with this file counted as LOG.
3. `grep -n "p.stdout + p.stderr" tools/runner/inbox.py` shows exactly one
   hit, line 799, the fixture helper, which is not `git_call`.
4. `grep -n "pending_files" tools/runner/telegram-bot.py` shows no hit
   inside `flush_inbox`.
5. `grep -n "reply-to-his-message" tools/` returns nothing.
6. The commit message carries, in words: the fault (a warning glued to a
   sha), the number of days it held (six), the number of his messages on
   the PC (254, his count), and the sentence that the first restart of the
   bot on his PC is the accepting case for the push and that nothing here
   has run there.
7. The Producer's message asking him to restart the bot goes out AFTER this
   commit lands on the work branch and not before, so one restart carries
   the fix and the amendments together. It says what he will see first: one
   message naming how many of his messages went, then his normal replies.

## 11. Filed and waiting (names, not work)

a. A SWIPE-REPLY IS AN ANSWER. `handle_text` treats a message whose
   `reply_to_message` id is the id the budget question's receipt recorded as
   a reading attempt whatever its shape. The literal second half of his
   sentence. Small, after the round trip.
b. THE READER STOPS RE-READING. `records_from_branch` and
   `outbound_from_branch` in `tools/inbox-read.py` read from disk when the
   file is already here and run `git show` only for what is new;
   `outbound_lines` caps the per-record lines and announces the cap.
c. NO PYTHON ON HIS PHONE. The two replies that print an exception type
   name say "the PC could not write the file" and put the type in the
   window.
d. THE THREE GLUED HELPERS, one pass: `tools/pc-watcher.py:git`,
   `tools/runner/executor.py:git_call`, `tools/inbox-read.py:git_run`, each
   returning three values, each with a planted-warning accepting case (the
   `refs/heads/FETCH_HEAD` ambiguity for the watcher). FIRST after the
   round trip is proven, by this ruling.
e. QUEUE 106 gains weight: `production/outbound/` now grows by a file per
   reply, and it is the one of the three directories the untracked gate
   does not watch.

<!--RULING spawn=2026-09-07T09:23:06Z-->
<!--RULING spawn=2026-09-07T10:22:00Z-->
