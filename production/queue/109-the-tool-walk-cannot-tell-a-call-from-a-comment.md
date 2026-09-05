line: infrastructure (the guards)
spec: found 2026-09-05 when a commit went red on a file that has never existed and that nothing calls
acceptance: the tool walk refuses a path that is genuinely referenced and missing, and ACCEPTS a path that appears only inside a comment or a string that names a proposal; both fixtures synthetic, accepting case first, and the live tree is the accepting case for the whole walk
max_sessions: 1
status: READY 2026-09-05. NOT STARTED THIS WEEK by Jafar's rule that after item 4 the studio stops building studio. instrument-builder, small.

## What happened

The console batch went red on:

    UNTRACKED/ABSENT TOOL(S): tools/verdictfmt.py(absent)

`tools/verdictfmt.py` HAS NEVER EXISTED. It appears exactly once in the whole
codebase, measured: one comment in `tools/gates.py` proposing it as "the right
home" for a formatter duplicated three times. Nothing imports it, nothing runs
it, no workflow names it.

## Why the check said otherwise

The walk in `ledger/verify.py` starts at the workflows and follows
`tools/[A-Za-z0-9_./-]+\.(py|sh)` TRANSITIVELY through every file it reaches,
which is the right idea: an untracked file two hops out breaks CI as loudly as
one hop out, and the first version of that walk stopped at one hop and missed
a real script.

But it is a REGEX OVER RAW TEXT. It cannot tell a call from a comment. So a
path written inside a comment, in a file that is reachable from a workflow,
becomes a hard dependency the repository must satisfy.

The chain here runs through a COMMENT in a workflow too: line 521 of
`ledger-probe-unreal.yml` mentions `verdict-read.py` in prose, which pulls that
file into the walk, and so on.

## What was done instead, and why this item exists

The comment in `gates.py` was reworded to name the idea without writing a path
that the walk reads as a reference, and it says so in the comment. THAT IS A
HOLDING FIX, not the repair: the next person who writes a sensible path into a
comment recreates it, and the fault is in the walk rather than in the prose.

## The trap in fixing it

DO NOT simply skip comment lines. The walk's value is that it follows real
references through shell and Python, and a reference inside a string is
sometimes exactly how a tool is invoked (`run(["python3", "tools/x.py"])`). A
fix that ignores every quoted path has blinded the walk to the thing it exists
to catch.

So the distinction to implement is between a path that is USED and a path that
is merely MENTIONED, and the honest version may be to keep following comments
but report a comment-only reference as a SEPARATE, non-blocking finding with
its own count, rather than as an absent dependency.

## Both halves

Accepting: the live tree, which today contains one comment-only mention, goes
green while every real workflow-named tool is still checked and counted.
Rejecting: a planted workflow naming a genuinely missing script still goes red
and names it. A fix that passes both by looking at nothing has removed the
guard.
