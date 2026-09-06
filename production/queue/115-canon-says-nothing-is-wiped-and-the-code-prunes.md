line: simulation (Core, and canon)
spec: external audit 2026-09-06, P1. canon.md outranks every document and every agent, so this is a canon conflict rather than a bug report
acceptance: a stated ruling on which is true, the OTHER one changed to match, and the change recorded; if pruning stays, canon.md and every public claim about permanent memory change with it, and the claims are found by grep rather than by memory
max_sessions: 1
status: P1, ready 2026-09-06, after the P0 pair. MANDATORY DIRECTOR RULING: this touches canon, which outranks everything.

## The conflict

`canon.md` says nothing is ever wiped. `MemoryStore` prunes at 600 events,
under a comment saying that is not forgetting.

Both cannot be true. A comment asserting that a prune is not forgetting is the
shape this project has a rule about: the code's own words are not evidence
about the code.

## Why this is P1 and not a tidy

PERMANENT MEMORY IS THE MOAT. The project's own framing is social memory at 93
against a best-in-class of 60, and consequence persistence at 95. If events are
pruned at 600, then the claim is bounded in a way no public statement about it
currently mentions, and every score resting on "nothing is ever wiped" rests on
something narrower.

## What a ruling has to decide, and it is not a preference

Which is TRUE, then change the other. The two honest outcomes:
- PRUNING IS WRONG: canon holds, the prune goes, and something has to answer
  what happens at scale instead. That answer must be measured, not asserted,
  and note queue 116: the soak that would be cited as evidence ran on seven
  agents.
- PRUNING IS RIGHT: canon changes, and so does every public claim about
  permanent memory. Find them by grep, not by memory, and print the count of
  files changed against the count that mentioned it.

## Both halves

Accepting: whichever way it goes, a test proves the behaviour the ruling
chose, and it fails if the other behaviour returns.
Rejecting: a state that satisfies neither, or a canon edit with no
corresponding code test, is the failure. A ruling that changes only the
comment has changed nothing.
