line: infrastructure (the measurement surface)
spec: external audit 2026-09-06, P1
acceptance: no document, gate, brief or public claim cites the soak as evidence for hundreds of residents; each citation either states the real denominator or is removed; and the soak's own output states plainly what it does and does not support, with the count of citations found and changed printed
max_sessions: 1
status: P1, ready 2026-09-06, after the P0 pair. Small, and mostly a grep and a sentence.

## The fault

The soak prints growth as REPORTED, NOT GATED, and it was RUN ON SEVEN AGENTS.
It is cited as evidence for a town of hundreds.

Seven to several hundred is not an extrapolation, it is a different question.
Memory growth, gossip fan-out and schedule contention do not scale linearly in
the ways that would make seven informative about three hundred, and the run
itself never claimed they did: it says NOT GATED, which is the instrument being
honest and the citations being careless.

## What it actually supports, and say it in those words

That the sim runs 500 days twice without falling over at SEVEN agents. That is
worth having and it is not nothing. It supports no claim about population
scale, memory volume at scale, or performance at target resident count.

## The work

Find every citation by grep, not by memory: the roadmap rows, the pillars, any
agent-facing doc, any brief. Print the count found and the count changed. A
zero here ships its denominator like any other.

Then make the soak's own done line carry the sentence, so the next reader gets
it from the instrument rather than from a document that may not travel with it.

## Both halves

Accepting: the soak runs and prints what it supports, naming seven.
Rejecting: a planted document citing it for hundreds is caught by whatever
check this lands, or if no check is practical, the item says so plainly rather
than pretending a grep once is a guard.
