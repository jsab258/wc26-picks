line: studio (how the resident works, not what it builds)
spec: this file. One near-miss, 2026-09-06, caught before it was pushed.
acceptance: none to build. This is a standing lesson looking for the right
  home, probably `.claude/rules/` rather than a queue item.
max_sessions: 1
status: READY 2026-09-06, and NOT for this weekend. Jafar ruled the weekend
  game work only and this is process. Filed so it is not lost.

## What happened

The resident wrote a commit message with a heredoc and ran `git commit -F` on
it IN ONE Bash call. The `verify-gate` hook blocked that call, correctly:
`production/d1-probe/DISPATCH` had changed after the last green footer.

THE BLOCK KILLED THE WHOLE INVOCATION, SO THE HEREDOC NEVER RAN. The message
file was never written.

After re-running verify, the second attempt committed with `-F` against that
same path, which still held an unrelated message from earlier in the session.
The commit went in under the subject "The register gate checks its first real
message, and that message is a landmine" attached to a diff about the Unreal
probe's dispatch. Caught by reading the commit back, amended before the push.

## The shape of it

A BLOCKED CALL RUNS NONE OF ITS PARTS. So a write and the command that
consumes it must not share an invocation with anything a guard can refuse. The
failure is silent in the worst way: the guard's message is about the file it
refused, and says nothing about the write that never happened, so the operator
reads a refusal about DISPATCH and has no reason to suspect the message file.

It is a near relative of a fault this project already knows: `-F` against a
stale path is the same class as pasting a footer from the scrollback. Both
take a value from somewhere that looks current and is not. The existing rule
says write the message to a file rather than an unquoted heredoc, and that
rule is what put the file there; it does not yet say the file must be written
in its own call, or that the commit must be read back.

## What would have caught it

Reading the commit back. `git log -1 --format=%s` after every commit, before
the push, cost one line and is what caught it here.

## Where this probably belongs

Not the queue. `.claude/rules/` or the operations casebook, beside the footer
rule it extends. Filed here rather than written into a rules file on a
weekend Jafar reserved for game work.
