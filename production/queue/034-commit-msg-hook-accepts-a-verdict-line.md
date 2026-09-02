line: infrastructure (governance)
spec: this file
acceptance: a commit whose subject is a verification-footer line is REFUSED; the accepting case (an ordinary subject) still passes; both outcomes fixtured
max_sessions: 1
status: READY 2026-09-02. Small. Found by committing one.

`.githooks/commit-msg` refuses a subject identical to HEAD's, which was
written after two commits carried the previous commit's message. It does
NOT refuse a subject that is a verification-footer line, and on 2 September
a commit landed whose entire message, subject included, was the footer.

THE CAUSE IS THE PART WORTH KEEPING, because the rule that was supposed to
prevent this is the rule that let it through. CLAUDE.md says to write the
message to a FILE rather than into an unquoted heredoc, because a backticked
identifier has twice been executed by the shell. The resident did that. But
`verify-gate.sh` is a PreToolUse hook, so when it blocks it blocks THE WHOLE
SHELL CALL, and the heredoc that writes the message file is inside the same
call as `git commit`. The message was never written. A later call ran
`cat ledger/.verify-footer >> "$S/mz.txt"` against a file that did not
exist, and `>>` CREATES rather than fails, so the message became the footer
and nothing else.

Two candidate guards, neither built:

1. Refuse a subject matching the footer's shape (it begins with a known
   verdict key and carries `key=value` pairs). Narrow and cheap.
2. Refuse a subject longer than some bound, which the footer's first line
   always exceeds. Cruder, and it would also catch an over-long human
   subject, which is arguably a feature.

Whichever lands, the accepting case is an ordinary subject and it is
asserted FIRST, per the guard rule this project already has.

A separate and larger lesson, not this item's work: writing the message file
in a DIFFERENT tool call from the commit removes the coupling entirely. That
is a habit change rather than a guard, so it is written here rather than
enforced.
