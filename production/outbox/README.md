# The Producer's outbox

STATUS: LIVE, verified 2026-09-03.

THIS DIRECTORY IS THE CONVENTION, created 2026-09-03 when Jafar ruled that
"any file under `production/briefs/` or the Producer's outbox must pass the
check for its kind before it can be committed". There was no outbox before
that ruling, and a gate pointed at a path nobody writes to is the failure
this project committed once already this morning, so the directory is
created, documented here, and walked by the gate from its first run.

## What goes here

One file per message the Producer has written and the sender has not sent
yet. The Producer writes; it cannot run the check (it has no Bash by design).
The SENDER runs the check and sends only on a pass. Today the sender is the
resident; the day the Telegram bot lands it becomes the send path and calls
the same check.

A sent message stays here. Re-checking it costs nothing, and a directory that
empties on send loses the only record of what the register actually looked
like in practice. If an archive is ever wanted, `production/outbox/sent/` is
walked too, because the gate reads this tree recursively rather than one
level, and a message that hides in a subdirectory of the outbox is exactly
the decay the recursive walk exists to stop.

## The name carries the kind, because the gate must not guess

    <YYYY-MM-DD>-<slug>.unprompted.md     120 words, the full shape
    <YYYY-MM-DD>-<slug>.brief.md          150 words, the full shape
    <YYYY-MM-DD>-<slug>.answer.md         he asked, so the length follows

    2026-09-03-street-textures.unprompted.md
    2026-09-03-how-many-objects.answer.md

The three registers differ in what is enforced, so a file whose kind the gate
has to infer is a file checked against the wrong rules. A name carrying no
recognised kind is REFUSED, and the refusal names the three suffixes rather
than picking one: guessing `unprompted` would reject a long answer that is
perfectly legal, and guessing `answer` would wave through an unprompted
message with no shape at all.

`production/briefs/` needs no suffix. Everything there is a brief and is
checked as one.

## Running it

    python3 tools/producer-check.py --kind unprompted production/outbox/FILE.md
    python3 tools/producer-check.py --gate      # every file in both trees

The gate runs inside `python3 ledger/verify.py`, so a message that breaks the
register cannot be committed even if nobody remembered to check it. The
sender still runs the single-file check before sending; the gate only makes
skipping it impossible.

## The pre-register files, and why the marker is not an escape hatch

Four files predate the register: three director briefs and one step-1 report,
written before 2026-09-03. They are not Producer messages and they fail the
register badly (the newest brief runs 632 words against a 150 cap with no
link at all). They are NOT silently exempt. Each carries the line
`PRODUCER-REGISTER-EXEMPT` in its first lines, saying so where a reader of
the file will see it, and each is named in the frozen `PRE_REGISTER` list in
`tools/producer-check.py`.

BOTH are required. A marker alone would be an escape hatch any session could
type; a list alone would be invisible to anyone reading the file. A marker on
a file the list does not name is a FAILURE, so widening the exemption means
editing the tool, which is a reviewed diff rather than a line in a document.

A SECOND FROZEN LIST, added 2026-09-06 and different in kind. Jafar ruled the
register's link band that day: at most two links per message, never to a
repository markdown file, only to the glance, map or gallery. Three files
written before that ruling would now fail it, and grading them by the date
typed into their own names would let anyone write a stale name onto a new
message and skip the band. So they are named instead, in `LEGACY_LINK_RULES`
in `tools/producer-check.py`: the two messages in this directory and
`production/briefs/2026-09-05.md`. It carries no marker line, because these
files are the record of what was written and the printed per-file line is the
reader-visible half. THE LIST NEVER WIDENS TO A FILE DATED ON OR AFTER
2026-09-06, and widening it at all means editing the tool in a reviewed diff.
The ruling is
`game-design/decision-2026-09-06-ruling-register-link-band-and-gallery.md`,
amendment A1.

WHAT THE BACKLOG WILL ACTUALLY DO ON THE FIRST SEND, measured 2026-09-06 and
NOT what anyone assumed.

Jafar ruled that older queued messages must read as historical so the first
burst does not tell him that solved problems are still current. The two
pre-2026-09-06 messages now carry a leading `HISTORICAL,` line saying when they
were written and what has changed since, and the gate excuses that one line
from the word cap for files on the frozen legacy list.

BUT THE SENDER WILL REFUSE THEM ANYWAY, and that is a different code path from
the gate. `tools/runner/outbox.py:run_check` shells out to
`producer-check.py --kind <kind> <file>`, the SINGLE-FILE path, which never
learns that a file is on `LEGACY_LINK_RULES`. Measured on both:

    2026-09-03-batch-landed-and-the-wait.unprompted.md   sender exit=1
    2026-09-05-the-console-run.unprompted.md             sender exit=1

The 2026-09-03 file reports four findings there and THREE OF THEM PREDATE the
historical marker: the link band, the link floor, and a deadline now 10.2 hours
in the PAST. The legacy grandfathering and the filename-pinned clock are both
gate-only by design.

SO THE FIRST BURST CARRIES ONLY THE MESSAGES WRITTEN ON 2026-09-06, AND
THAT IS A DECISION, NOT AN ACCIDENT. Ruled by the director 2026-09-06
(game-design/decision-2026-09-06-ruling-delivery-batch-map-availability-and-outbox.md,
section 6): the two annotated messages are gate-only and are not sent.
His ruling's intent, that the backlog must not tell him resolved
problems are current, is met more simply by not delivering them; both
bodies are superseded; the one decision they carry was ruled A by him on
2026-09-06 (production/decision-queue.md, RULED THIS WEEK); and the
answer message of 2026-09-06 tells him two older messages are held back,
so he can ask for them. The annotations stay: anyone opening those files
reads that they are historical and why. The bodies are never trimmed;
they are the record.

The sender's refusal of them is still worded as a register refusal, which
is the wrong word for a decided hold. Queue 141 makes it a named outcome.
Until it lands, two refused records for these files on the pc-inbox
branch are expected and are not a fault.
