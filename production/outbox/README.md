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
