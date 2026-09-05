line: infrastructure (the Producer loop, rulings)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", item 1, rulings clause
acceptance: a WAITING card in production/decision-queue.md arrives on his phone with one button per option, and one tap moves that card to RULED THIS WEEK carrying the date, the option letter and RULED BY JAFAR, with the WAITING count printed before and after and falling by exactly one; a tap on a card that is not in WAITING, and a second tap on an already ruled card, are both refused with the reason recorded and the file BYTE-UNCHANGED; a callback from any chat that is not the configured one is refused and counted; a card carrying fewer than two options is not sent at all and says which card and why; the sender prints cardsSent=N/M waiting and the words "nothing measured" when nothing is waiting; the fold's call site is named and is the 088 reader at the dispatch boundary
max_sessions: 1
status: READY 2026-09-05. THIRD of item 1. instrument-builder, finished on the PC.

## The card format is already ruled, so nothing here invents one

`production/decision-queue.md` requires every card to carry a CLASS, two to
four options, a recommendation, a default and a deadline no shorter than 24
hours. The live card ("How close should strangers stand?") is the accepting
fixture: options are `- A. ...` lines, and the routing field is
`CLASS: BLOCKING | DECISION | REVIEW | FYI` defined in
`production/interrupt-classes.md`. BLOCKING pushes now, DECISION rides the
morning brief, REVIEW waits for the weekly, FYI is never pushed. An
UNCLASSIFIED card is reported as such and never routed as FYI by default.

## Two mechanism facts the builder will otherwise discover late

1. THE BOT CANNOT SEE A BUTTON TAP TODAY. `Bot.handle` reads
   `update["message"]` or `update["edited_message"]` and counts everything else
   as `other`. An inline keyboard tap arrives as a `callback_query`, which is a
   different update kind, and it also needs answering (`answerCallbackQuery`),
   or his phone keeps showing a spinner. The budget flow's reply keyboard is
   NOT the right shape here: a reply keyboard sends back plain text, so a
   tapped "A" and a typed "A" are indistinguishable and both collide with the
   pending budget question. A ruling must carry which card it rules.
2. TWO WRITERS ON ONE FILE. `production/decision-queue.md` is tracked and the
   container edits it. The PC must not edit the same file on the same branch,
   or the first conflict is a lost ruling. So the tap writes a RULING RECORD
   on the inbox branch (card id, option letter, tap instant, and nothing that
   identifies the chat), and a fold tool in the container applies records to
   the file deterministically.

## What done looks like

He taps, the record lands by queue 088's route within a minute, and after one
fold the queue shows the ruling in the shape the file already uses for
"2026-09-03: the next builder goes on the Unreal wire": the card under RULED
THIS WEEK, the option named, RULED BY JAFAR, and nothing else rewritten.

The fold is deterministic and refuses rather than guessing. It never edits a
card's text, never invents a CLASS, and never rules a card whose record names
an option letter that card does not offer.

## Both halves, accepting first

Accepting: the live WAITING card is sent, tapped and folded, and the diff to
`production/decision-queue.md` is exactly the move plus the ruling lines.
Prove the needs-you count with a number either side.

Rejecting, four cases, each leaving the file byte-unchanged: a record naming a
card that is not in WAITING; a second record for a card already ruled; a
callback from a chat that is not the configured one; and a record naming an
option letter the card does not offer. Each refusal is recorded with its
reason, because a refusal nobody can read is the same as a silent drop.

## Depends on, and what it blocks

Depends on queue 088 for the record's route back into the repo. Blocks queue
093, whose second half is exactly this round trip. Related: queue 073, the
needs-you count that must move when a card is ruled.
