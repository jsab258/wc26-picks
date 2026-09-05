line: infrastructure (the budget instrument)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 10. Overrides the button grid the bot shipped with on 2026-09-04.
acceptance: a meter question is sent carrying NO preset keyboard, proven by asserting the sent parameters hold no keyboard array and that the previous keyboard is removed, and "77" is accepted and read back; every one of "76,5", "76.5", "77.0", "about half", "101", "-3" and the empty string is REFUSED with a message naming that a whole number from 0 to 100 is wanted, with no reading recorded and the readings counter unchanged, printed as refused=N/M answers seen; the selftest's keyboard fixture is inverted so that a returning preset grid FAILS it; and the reading is recorded with source=typed, with the retired value named so older rows stay readable
max_sessions: 1
status: READY 2026-09-05. Small. instrument-builder.

## His rule, and the reason it is not fussiness

"Ask for the exact number and take it as typed, numeric keypad where the
platform allows, REJECT anything that is not an integer rather than rounding
it. Presets are for rulings, never for measurements."

The grid the bot shipped with is 15 buttons spanning 0 to 100 in steps of 5 and
10, and the meter reports integers. So a button press can be a ROUNDING of what
he saw, and near the ceiling a rounded reading is the difference between
stopping and crossing. Queue 082 already carries a `source=button|typed` field
for exactly that reason; this item removes the ambiguity at its source instead
of recording it.

RULINGS KEEP THEIR BUTTONS. Queue 090's option buttons are a choice among named
options, which is what presets are for. Only the measurement loses them.

## What changes in the code, named

`BUDGET_KEYS` and the keyboard argument on the meter questions go. The parser
that accepts "76,5" and a bare float stops accepting them: it takes an integer
and refuses everything else, with a message that says what is wanted rather
than a bare refusal. The arithmetic below it is not the same thing as the input
and is not to be gutted by reflex: check what still needs to handle a
fractional value before deleting anything there.

## Two claims to check rather than assert

- NUMERIC KEYPAD. He said "where the platform allows". Read the Bot API for
  what it actually offers a bot: the placeholder field is already in use, and
  if there is no way to ask for a numeric keypad, the file says so plainly
  rather than shipping a comment claiming one.
- THE OLD KEYBOARD IS STILL ON HIS PHONE. A one-time keyboard sent before this
  change can persist in the chat; removing it is an explicit parameter, not a
  consequence of not sending a new one.

## The guard must be able to fail

The current selftest asserts the grid exists, with 15 buttons spanning 0 to
100. Inverted, it asserts that no meter question carries a keyboard, so a
future edit that brings the grid back turns it red. A guard that cannot tell a
regression from an improvement is a ratchet.

## Both halves, accepting first

Accepting: "77" is taken, read back, and recorded once.

Rejecting: seven cases in the list above, each refused, each leaving the
readings counter where it was. The counter is the half that catches a refusal
that quietly records anyway, and the done line prints the refusals against the
answers seen so a zero can be told from nothing having been asked.

## Depends on, and what it blocks

Depends on nothing to change the input. Queue 082 is the route that carries the
accepted reading into `production/budget.md`, and 082's `source` field is
amended by this item rather than by a separate task. Blocks nothing.
