# The decision queue

STATUS: LIVE. The single home for decisions awaiting Jafar, and the single
record of what he ruled. Written by the Producer, read by the dashboard and by
the bot. Chat is never a record: anything decided in conversation is written
here in the same turn.

THE FLOW, ruled by Jafar 2026-09-03. A card waits here until he rules. A ruled
card becomes a register entry: a D-record under
`ledger-v2/respec/decision-register/` when it affects architecture or identity,
a lighter RULED entry in this file otherwise. The dashboard reads WAITING for
its needs-you count and the register for what is decided.

Every card carries: a CLASS, two to four options, a recommendation, a default,
and a deadline no shorter than 24 hours, because until the bot exists Jafar may
not open this for a day.

THE CLASS IS A FIELD, NOT A JUDGEMENT MADE AT SEND TIME, so routing is data:
`CLASS: BLOCKING | DECISION | REVIEW | FYI`, defined in
`production/interrupt-classes.md`. BLOCKING pushes now, DECISION rides the
morning brief, REVIEW waits for the weekly, FYI is never pushed. A card with no
CLASS line is UNCLASSIFIED and is reported as such, never routed as FYI by
default: a default route is how a Blocking item lands on a page nobody opened.
Irreversible items wait for Jafar and never guess.

---

## WAITING

### Create the Telegram bot, so Monday is not blocked on it
added 2026-09-03. CLASS: DECISION. DUE BEFORE MONDAY 14:00 CEST.

The bot is the first thing built after the reset and it is the only item whose
blocker is you rather than the studio. Nothing here can create it: the studio
cannot use your accounts, and every external host is blocked from the build
machine anyway.

WHAT IT NEEDS FROM YOU, about five minutes in Telegram:
- Message @BotFather, send `/newbot`, name it, and it hands back a token.
- Message your new bot once, so it has a chat to talk to, and get the chat id.
- Put both through the existing PC channel into `tools/runner/config.local`,
  which is uncommitted by design. Neither is ever committed or printed.

- A. Do it before Monday. The bot lands first after the reset, as ruled.
- B. Do it later and the bot slips; the console still works, but pushes,
  decision buttons and voice notes all wait on it.
- C. Change your mind about Telegram and say what instead.

RECOMMENDATION A. It is five minutes of yours against the first item of the
week for the studio.
DEFAULT B if unruled: the studio builds the glance first and the bot when the
token arrives, because a bot with no token is not a thing that can be tested.
DEADLINE 2026-09-07.
EVIDENCE: `production/queue/067-telegram-bot-on-the-pc.md` carries the full
specification, including that the bot is the send path and calls the register
check itself, so nothing unchecked ever leaves.

---

### How close should strangers stand?
CLASS: DECISION
added 2026-08-04, still open, and it now has the picture it was waiting for

Crowds pack to 45 cm apart, which is touching distance, and 36 people can
stand inside a two-metre circle. That is the separation rule working exactly
as written: it only stops bodies overlapping and nothing models personal
space. Whether that reads as a busy street or as a riot is a judgement off a
picture, not a number the studio should pick.

- A. 0.7 m. Crowded market street, people almost touching.
- B. 1.0 m. Normal British pavement distance between strangers.
- C. 1.4 m. Reserved, wary, a town where people keep their distance.

RECOMMENDATION B, because Meridian is a working port town and not a festival.
DEFAULT B if unruled by 2026-09-07, the Monday reset.
EVIDENCE: `game-design/sim-shots/vign_camA_night.jpg` is the street with people
absent; the crowd still that would settle this does not exist yet, which is the
honest reason this has waited a month.

---

## RULED THIS WEEK

### 2026-09-03: the next builder goes on the Unreal wire, not the Ledger
CLASS: DECISION
RULED BY JAFAR. Option A. One session.

Phase C is one unconnected pin from a textured Unreal street: 563 of 593
objects carry textures and every frame is grey because the texture coordinates
are unwired. The alternative was starting the Ledger, the social memory
system. A was chosen because it finishes something.

CARRIED INTO: `production/queue/062-uv-chain-head-refuses-to-wire.md`, which
is the live blocker, and it becomes the first show-moment row, "first textured
Unreal street", when item 9 of the console lands.
LIGHTER RULING, not a D-record: it schedules work rather than changing
architecture or identity.

---

## RETIRED

`game-design/decisions-pending.md` is retired as of 2026-09-03. Its one live
card is above. Its answered cards stay there as history and are not migrated;
the ones that became decisions are D11, D12 and D13 in the register, and the
engine tie-break and deadline rulings live in the 2 September decision records.
