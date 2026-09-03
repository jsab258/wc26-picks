line: production (the reporting channel Jafar reads)
spec: this file
acceptance: an open decision on the dashboard carries enough to answer it there: the plain-terms framing, the options with what each costs, and the studio's recommendation, rendered from decisions-pending.md rather than retyped; a card whose source has no options renders the heading and says which part is missing rather than looking complete; any truncation announces itself through tools/capsay.py, which is the one implementation of that idea in this repo
max_sessions: 1
status: READY 2026-09-02. instrument-builder, small. Found when Jafar read the inbox and had to ask the chat "any more details about this decision?"

## The finding

The Decision inbox renders the `###` heading of each waiting card and nothing
else. The heading is the QUESTION. Everything that makes it answerable, the
plain-terms framing, the options table, what each costs and what the studio
recommends, is written in `game-design/decisions-pending.md` and never
reaches the page.

So the one panel on the dashboard that exists to get a decision OUT of Jafar
gives him no way to make one. He reads a title, comes to the chat, and asks
for the body. That is the dashboard failing at the single job it was built
for, and it failed quietly: the panel looks complete, because a heading with
a count beside it looks like a finished item rather than a truncated one.

## Why this is the dashboard's own rule, not a feature request

Every truncation in this project announces itself. A cap that bites in
silence is the fault the whole reporting channel is built around, and here an
entire card body is dropped with no notice at all. The panel does not say
"heading only", it just shows the heading.

## The work

Render the body. The cards are already written to be read by one person in
one sitting: a plain-terms paragraph, a table of options with costs, and a
recommendation. Take them from the source file so the page can never drift
from what the register says, and so a card edited in the repo is answerable
on the page within one write of the live document.

## The trap

Do not summarise the card. A summary of a decision is a new decision quietly
made by whoever wrote the summary, and the options are exactly where that
would do damage. Render what is there, or say which part is missing.
