line: infrastructure (the Producer loop, outbound)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 1, outbound clause
acceptance: a Producer message file committed in the container reaches his phone without a human, and a receipt naming the file, the commit sha and the send instant lands in the repo, with outboundLatencySec printed from commit to send; a message that fails `python3 tools/producer-check.py --kind <kind>` is NOT sent and the refusal names the failing clause; a file already sent is not sent twice, proven by two passes reporting sent=1; the sender prints outboxFiles=N sent=M refused=K unsent=J and the words "nothing measured" when the outbox holds no unsent file
max_sessions: 1
status: READY 2026-09-05. SECOND of item 1. instrument-builder, finished on the PC.

## What exists and what is missing

`production/outbox/README.md` is the ruled convention: one file per unsent
message, the kind carried in the name (`.unprompted.md`, `.brief.md`,
`.answer.md`), the SENDER runs the check and sends only on a pass, and its own
words are that the day the bot lands it becomes the send path and calls the
same check.

`tools/runner/telegram-bot.py` has `--send` and `--send-file`, and neither
calls any check. Queue 083 wires the check onto the Producer content class and
is the right place for that wiring. What NOTHING does today is notice that a
new outbox file exists and send it. The Producer writes into a directory and
the message sits there until a human types a command, which is the whole gap.

## What to build

A sender on the PC, running in the same pass rhythm as the inbound watcher,
that for every file in `production/outbox/` with no receipt:

1. Runs `python3 tools/producer-check.py --kind <kind from the name> <file>`.
   The kind comes from the suffix and is never guessed: the README refuses a
   name carrying no recognised kind, and so does this.
2. Sends only on a pass, through the existing send path.
3. Writes a receipt that travels back on queue 088's transport, naming the
   file, the commit sha it was read at, and the send instant.

The receipt is what makes the send provable in the tree, which is the same hole
queue 080 names for the pre-send check: a command a human types, whose result
reaches no file, cannot be told apart from a command nobody ran.

## The traps, named so the builder does not find them at 2am

- THE CHECK RUNS ON THE SENDING SIDE, which is that PC. A check that runs in
  the container and trusts the PC to have honoured it is not a check.
- The bot's own chrome (its opening line, its questions, its read-backs) fails
  the register by construction and must not be routed through this path. Queue
  083 carries that boundary and the open question of whether the chrome is
  Producer voice; do not settle it here.
- Idempotence is by receipt, not by deleting the file. The README is explicit
  that a sent message STAYS in the outbox, so "no file" can never mean "sent".
- A message that fails the check must be reported back to the studio, not only
  logged on his disk. An unsendable message that nobody learns about is a
  Producer message that silently never arrived.

## Both halves, accepting first

Accepting: a real message file committed in the container arrives on his phone
with no human action, and its receipt is in the repo. Print
`outboundLatencySec=<n>` from the commit instant to the send instant, and say
it is one sample rather than a rate.

Rejecting, three cases: a planted message that breaks the register (over the
word cap, or with no evidence link) is refused, unsent, with the failing clause
named; a file whose name carries no recognised kind is refused naming the three
suffixes rather than picking one; and a second pass over an already-sent file
sends nothing and prints `sent=0 alreadySent=1`.

## Depends on, and what it blocks

Depends on queue 088 for the receipt route back, and on queue 083 for the check
wiring (if 083 has not landed, this task wires the check for the content class
and 083 shrinks to its open question). Blocks queue 093 and queue 095, which is
the brief this path pushes every morning. Related: queue 080, the stamp that
proves the pre-send check ran.
