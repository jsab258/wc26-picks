line: infrastructure (the Producer register)
spec: game-design/decision-2026-09-04-ruling-067-telegram-bot-first-pass.md, section 3
acceptance: a Producer message sent through the bot passes producer-check for its kind before it leaves, proven both ways; and the bot's own chrome is exempt by a stated rule rather than by omission
max_sessions: 1
status: READY 2026-09-04. instrument-builder, small.

## The deviation, stated as what it is

Jafar ruled on 3 September that any Producer message must pass the register
check before it can be committed, and the intent was clearly that no message
reaches him unchecked. The bot now has a send path that calls no check.

RULED A DEVIATION FROM THE LETTER, NOT THE SUBSTANCE, and the reason is
measurable: there are 0 invocations of `--send` or `--send-file` anywhere in
the repository, so no Producer message goes through the bot this weekend. The
hole is the same size it was before the bot existed. It stops being true the
first time anything calls that path.

## The correction the ruling made to the builder's own note

The README first said `send()` is the single choke point so wiring the check
there is a one-place change. That is wrong and would have made the bot
unusable: `send()` also carries the bot's own chrome, its opening line, its
budget question, its read-back, and those fail the register's SHAPE by
construction because they are not five-section Producer messages.

So the check is wired on the PRODUCER CONTENT CLASS, meaning `--send-file`
from the outbox first, then the brief and the Blocking push, and never on
`send()` itself.

## The open question that is Jafar's, not a builder's

Are the bot's fixed strings chrome, or are they the Producer speaking? They
read as the studio talking to him, and one of them already trips the register's
ban list on the word `repo`. If they are Producer voice, they need the
register; if they are chrome, the exemption needs to be written down rather
than assumed. Do not decide this in a builder pass. Put it to him.
