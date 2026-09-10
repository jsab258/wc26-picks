line: simulation (Core)
spec: external audit 2026-09-06, second half of the P0 order: "then audit every other place a model-supplied field reaches state unchecked"
acceptance: a printed inventory of every field that arrives from model JSON and can influence state, each with the check that constrains it or the words "nothing constrains it", counted against the total; every unconstrained one either gets a check that can refuse or a recorded ruling saying why it is safe
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work0, ready 2026-09-06, immediately after queue 113. Do not start before it: 113 sets the shape a constraint has to take.

## Why a sweep and not just the one fix

`check:none` was found by an outside reader, not by us, and our own suite
certified it. That is evidence about the CLASS, not just the instance. The
question this item answers is: WHAT ELSE ARRIVES FROM THE MODEL AND REACHES
STATE, and what stops it.

Known entry points to start from, not to be treated as the whole list:
`IntentRouter.cs` around lines 440 to 480 reads `kind`, `check`, `effect`,
`target` and a magnitude out of `MiniJson`. `target` is already narrowed
against `ctx.KnownPeople` and an unrecognised one becomes empty, which is the
SHAPE A GOOD CONSTRAINT HAS: the model may pick from what exists, not invent.
Use it as the model for the others.

## What the inventory must print

One row per field: where it enters, what it can reach, the check that
constrains it, and whether that check CAN REFUSE. A field whose check cannot
refuse is counted as unconstrained, because that is what `check:none` was.

Every zero ships its denominator: "0 unconstrained of N examined", never a bare
clean result.

## The trap

Do not count a VOCABULARY CHECK as a constraint. `Checks.Known(check)` passed
`none` happily; membership in a list of allowed values says the field is
well-formed, not that its effect is bounded. Those are different questions and
conflating them is how this got through.

## Both halves

Accepting: the live tree, inventoried, with every constrained field showing the
check that can refuse it.
Rejecting: a planted field that reaches state with only a vocabulary check is
counted as unconstrained and named.

AND DO NOT COUNT BINDING AS DIFFICULTY. `Adjudicator.Binds` refuses a
requirement nobody in the declared range could fail; it says nothing about a
requirement almost nobody in play would fail. `cash:1`, `hour:1` and `heat:99`
all bind and barely constrain. THE MODEL STILL CHOOSES HOW HARD. A floor on
each amount is a bound, and rule 2 wants the series first: wallets, hours and
heat as played, and the amounts the model names. Inventory the amount field as
"constrained against formality, unconstrained above it" and file the series as
its own item.

NOTE FOR THE RECORD, because the resident asserted otherwise: this paragraph
was NOT in this file when the P0 review ran. The resident repeated a builder's
claim that it was, the director checked and found 0 hits, and it is here now
because of that check rather than because the claim was true.
