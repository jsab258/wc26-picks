line: infrastructure (the budget instrument)
spec: game-design/decision-2026-09-04-ruling-067-telegram-bot-first-pass.md, section 2
acceptance: a reading Jafar gives the bot on his phone arrives in production/budget.md as a dated row carrying BOTH meters and a source field, without him typing anything into a terminal; proven by one real round trip on the PC, not by a selftest
max_sessions: 1
status: READY 2026-09-04. FIRST after 062 step 2 and run 21 unless Jafar reorders. instrument-builder or engine-specialist.

## The gap

The bot asks for both meters with number buttons and writes the answer to
`production/logs/telegram-budget.log`, which is gitignored. So the reading
lands on Jafar's disk where NO SESSION CAN READ IT. Getting readings out of
him is the single thing that blocked this studio for the whole week of
1 September: work stopped four separate times waiting for a number he had to
type into a browser.

Ruled acceptable for one weekend only, on the reasoning that un-ignoring the
log would not have helped either: a file on the PC still needs a push to reach
the repo, and a .bat that runs git can sit waiting on an editor, which is what
happened on 26 August.

## What it has to do

The reading reaches `production/budget.md` as a row in the existing table,
with the date, both meters, and the note field. It must carry a
`source=button|typed` field, because a button press and a typed integer are
different evidence: the buttons are a 5 or 10 point grid and the meter reports
integers, so a button answer may be a ROUNDING of what he saw. A row that
cannot say which it was cannot be trusted near the ceiling.

## The trap, and it is the reason this is not trivial

The push has to happen without a human at a keyboard, and the machine that has
the reading is not the machine that holds this session. Whatever route is
chosen (the bot commits and pushes, or the night runner picks the log up, or
the log is un-ignored and a later session reads it), the route must not be able
to hang: no interactive git, no editor, no credential prompt. The 26 August
incident is the precedent and `tools/lint-bat-editor.py` is the guard.

## Both halves

Accepting: one real reading given on the phone appears as a committed row.
Rejecting: a malformed answer (a word, a number over 100, one meter only) is
refused by the bot with a message, and NO row is written. A route that writes
a row for a junk answer has made the budget table lie, which is worse than
having no route at all.
