# How to brief a builder so it builds

STATUS: LIVE, verified 2026-09-02. Written by the resident, whose briefing
fault this fixes. Queue 031 carries the incident and owes the measurement.

## The fault this exists for

Five builders in a row hit their turn limit BEFORE WRITING A LINE, and each
needed a mid-flight message telling it to stop investigating and start
writing. Every one of those restarts cost a round trip, and the reading they
did was mostly re-establishing things the brief could have simply said.

At roughly 1.5 to 2 points a spawn against an allowance of about 10 a day,
this is the single largest recoverable waste in the studio.

**It is a briefing fault, not an agent fault.** A brief that opens with a
reading list gets a session of reading. A brief that opens with facts gets
a session of building.

## The rule

**Put the facts in the brief. Cite a path only when the builder must EDIT
it, or when the content is too long to quote and too important to
paraphrase.**

If you find yourself writing "read X to understand Y", stop and write Y.
You have already read it. Paying a second agent to read it again, at agent
prices, to reach the conclusion you are holding, is the waste.

## The shape

1. **What is being built, in one paragraph.** The deliverable, not the
   context.
2. **The facts it needs, quoted.** Numbers, file paths it will edit, the
   exact text of any dictated edit, the names of the functions involved,
   what a previous run measured. Quote them; do not point at them.
3. **What is already known and must not be re-derived.** Name the
   conclusions that are settled. This is the half that saves the most,
   because an agent with a gap will always go and look.
4. **The constraints that bite**, each with its consequence: what compiles
   where, what a default silently does, what the round trip costs.
5. **The scope ceiling, out loud.** "Exactly this list. Anything else is a
   REPORTED NEXT STEP, not more build time." Say it even when it seems
   obvious; the five that overran all had obvious scope.
6. **What to report**, including what it could NOT verify, by name.

## Two things that are worth their words

**Say which claims are already verified and by whom.** A builder that cannot
tell a checked fact from a repeated one will check both, and checking is
what eats the budget.

**Say what NOT to open.** Naming the live files another builder owns costs
one line and prevents a collision that costs a batch.

## What this does not fix

The turn limit itself, and the fact that a builder cannot see how many turns
it has left. Until it can, the ceiling in the brief is the only governor,
which is why it is item 5 rather than a footnote.

Queue 031 owes the measurement: turn-to-first-write across the next five
builders, printed as a series BEFORE any bound is set from it. This document
is the intervention; that series is whether it worked.
