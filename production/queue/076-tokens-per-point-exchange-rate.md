line: infrastructure (the budget instrument)
spec: Jafar's Director's Console rulings, 2026-09-03, area B item 5
acceptance: either a printed tokens-per-point figure derived from at least two of Jafar's readings with the token totals that span them, or the words "nothing measured" plus the named reason the totals could not be read
max_sessions: 1
status: READY 2026-09-03. RESEARCH ON THE PC, cannot be answered from the build container.

## The question

Does anything on Jafar's machine report token usage per session, and if so,
can two of his percentage readings be divided by the tokens burned between
them to give a tokens-per-point exchange rate?

Today every budget estimate in this project is a spawn count multiplied by a
guess. The guess was "roughly 1.5 to 2 points per spawn", derived on
2026-09-02 by dividing spawn counts into Jafar's readings, and the spawn log
has already shown why that number is weak: a fable spawn runs a median of 12
turns and an opus spawn a median of 45, so one figure covering both is an
average of two populations that are 3.75x apart. A turn is not a token either.
The only honest denominator is tokens.

## What to establish, in this order

1. Does `claude -p ... --output-format json` report usage on that machine, and
   what fields does the object actually carry? Print one real object. Do not
   describe the schema from memory: this project has been wrong about a
   Claude Code surface twice in one week because the surface moved.
2. Do the local session transcripts under the projects directory carry
   per-message usage? The spawn-cost tool already walks 453 of them for turn
   counts and would be the natural place to add a token sum, but only if the
   field is there. If it is not there, say so with the count of transcripts
   examined beside the zero.
3. If both are available, do they AGREE on the same session. Two sources that
   disagree is a finding worth more than either number alone.

## The division, and the trap in it

The rate is (tokens burned between two readings) / (points between the same
two readings). Both halves must span THE SAME WINDOW, and the window must be
one in which Jafar did no other work on the account. Exactly one such window
exists so far: the 2026-09-03 04:50Z reading against the one before it, the
overnight run he slept through, 14 points. Every other delta in
`production/budget.md` is contaminated and is marked so in the table. If the
token totals cannot be reconstructed for that specific window, this task
returns "nothing measured" and names why, rather than dividing a clean point
delta by a contaminated token sum.

Note also that percentage points are not a fixed quantity of tokens across
tiers. If usage is reported per model, the rate is per tier or it is not a
rate. Say which was possible.

## Done looks like

A row added to `production/budget.md` under the calibration section, carrying
the figure, the window it came from, the source of the token totals, and the
date. Or, if the totals do not exist, a stated negative with the search that
proved it and the count of what was examined.
