line: production (the channel)
spec: game-design/decision-2026-09-03-batch-review-register-banner-spawnlog-uvsweep.md, ruling 1(c)
acceptance: a NEEDS YOU body that is not a recognised nothing-form and parses to zero items is refused by the `options` rule, naming what it could not find; `NEEDS YOU: nothing today.` still passes; both shipped as --selftest fixtures, accepting case first; the live gate stays green
max_sessions: 1
status: READY 2026-09-03. instrument-builder, small. Lands before the next unprompted Producer message is sent.

## The hole

`needs_you_items()` in `tools/producer-check.py` recognises an item by the
markers the `options` and `deadline` rules then check for: an option letter,
RECOMMEND, DEFAULT or DEADLINE. A trailing chunk carrying none of them is
dropped. So a NEEDS YOU section written as prose, with a question and no
lettered options, no recommendation, no default and no deadline, parses as
zero items, both rules find nothing to check, and the message passes in every
register. The check cannot tell that body from "nothing today". Detection
rests on the presence of the very markers whose absence is the violation.

## The fix, specified

A short list of nothing-forms (`nothing`, `none`, `nothing today`, `nothing
needs you`, and the like), matched at the start of the section body. A NEEDS
YOU body that is non-empty, matches none of them, and yields zero items is a
finding under `options`: "NEEDS YOU carries text this check cannot read as an
item (no A./B. options, no RECOMMENDATION, no DEFAULT, no DEADLINE); write it
as one, or say nothing". The list of nothing-forms is printed with the
finding so a writer can see what would have passed.

## The fixtures

Accepting first: the existing `empty` fixture (`NEEDS YOU: nothing today.`)
keeps passing. Rejecting: `GOOD` with its NEEDS YOU replaced by
`NEEDS YOU: which pavement distance do you prefer? See the card.` is refused
by `options` and by no other rule, so it joins the one-rule-per-fixture check.
