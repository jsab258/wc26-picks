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

### RULED 2026-09-05 BY JAFAR: run 21 goes, item 6 of his standing order.

His words, recorded in production/NOW.md item 6 of the 2026-09-05 standing
order: "Then the game: 062 step 2, run 21. THE FIRST TEXTURED FRAMES COME TO
HIM AS IMAGES." That lifts the "wait for now" of 2026-09-03 and is condition
two of
game-design/decision-2026-09-05-ruling-062-step-2-third-status-word.md
section 5. Condition one, step 2 committed, is met by the commit carrying this
entry. Dispatch follows in its own commit with the sha captured first. If 21
prints materialConnections=12/14 that is the answer, reported and not retried.

### RULED 2026-09-05 BY JAFAR: A. Run the wake test tonight.

His words: "Card 1: A, run the wake test tonight." So the fifteen-minute
night is authorised: twenty-four firings, priced to within four hundredths of
a point, with the kill switch and the self-deleting trigger the card named.
ONE THING THE CARD DID NOT ANTICIPATE AND THE RESIDENT MUST HONOUR: the same
message ordered continuous building today, and the test night's own acceptance
refuses a contaminated window. So the window opens only when the build run has
stopped, and it needs his two readings at both ends. Queue 092 carries it.

### What may the studio spend to wake for your messages at night?
CLASS: DECISION
added 2026-09-05, from today's ruling on your standing order

You asked that anything you send the bot reach the studio within a few
minutes. The transport is built and lands today; the first message you send the bot is its test. The waking half does not.
Nothing on your PC can reach into the studio to start it, a turn begins only
when a trigger fires or you type, and the only trigger in place fires once a
day. So a message sent while the studio is asleep waits for the next turn, up
to 24 hours.

A fourth route, a doorbell your PC could ring to wake the session (a webhook),
[was tested and is shut](https://github.com/jsab258/wc26-picks/blob/claude/game-dev-ai-automation-2h67ix/production/queue/088-the-inbound-path-from-his-phone-to-this-session.md):
it refused the exact request your PC would send, because its key is sealed to
one service. Of the three routes left, only a fast recurring trigger closes
your item as you wrote it, and it is not armed because what one firing costs
has never been measured. Choosing a cadence without that number would be
guessing with your meter.

The test night, if you choose one: the studio wakes on a trigger with nothing
to do but read the inbox and answer anything waiting, and you type both meter
readings as whole numbers, once when the window opens and once when it closes.
Anything else using the account inside that window, you or the studio,
contaminates the number, and a contaminated number is refused rather than
published. There is a kill switch: one command to the bot from your phone
stops the firings at the next one, because the studio cannot read the meter
and a night running hot cannot notice by itself. The trigger removes itself
when the window ends.

Whichever you choose, until one wake has been priced and you have set the
cadence against that price, your item reads as
[the ruling](https://github.com/jsab258/wc26-picks/blob/claude/game-dev-ai-automation-2h67ix/game-design/decision-2026-09-05-ruling-standing-order-refill-and-the-wake-half.md)
amends it: anything you send lands as a dated note and reaches the studio
within a minute of its next turn; the bot's reply says whether the studio is
awake or asleep and, if asleep, when it next wakes.

- A. Every fifteen minutes for one six-hour night: twenty-four firings, each
  priced to within four hundredths of a point. The studio's guess for the
  whole night is about one point, and that is a guess, not a measurement.
- B. Every hour for one night first: six firings, each priced only to within
  a sixth of a point. Cheaper, and too coarse to price a five-minute cadence.
- C. Awake-only this week, no test. A message sent at night waits for the
  morning.

RECOMMENDATION A: it prices the cadence you actually asked for, at a cost
small enough to spend once.
DEFAULT C if unruled, because a default may not spend your meter; only your
ruling can.
DEADLINE 2026-09-07, the Monday reset. Nothing is armed before you rule, and
the night runs only when you can give both readings.

### RULED 2026-09-05 BY JAFAR: A. Publish as designed.

His words: "Card 2: A, publish as designed." The glance publishes with the
budget bar, on a page anyone with the URL can read, which he has now ruled
knowingly. Queue 097 is unblocked and does not wait for the default.

### The glance would be readable by anyone: publish it as designed?
CLASS: DECISION
added 2026-09-05, from today's ruling on your standing order

You asked to be told if GitHub Pages were refused. It is not refused: the
project on GitHub is public, so Pages is available and the glance can open on your
phone. What needs your ruling is the consequence, not the refusal. A Pages
site on a public project is readable by anyone who has the URL, and the glance
carries your budget percentages on both meters, the needs-you count and the
top item. Nothing new is exposed, because
[the budget page](https://github.com/jsab258/wc26-picks/blob/claude/game-dev-ai-automation-2h67ix/production/budget.md)
those percentages come from is already public in the same project. That is a
reason this is not a new leak. It is not a reason it is fine, which is why
this is your call and not a builder's, and why the work that publishes it
[waits for your ruling](https://github.com/jsab258/wc26-picks/blob/claude/game-dev-ai-automation-2h67ix/production/queue/097-publish-the-glance-so-it-opens-on-his-phone.md).

- A. Publish as designed, budget bar and all.
- B. Publish without the budget bar. The needs-you count and the top item
  still show; the meters do not.
- C. Do not publish. The glance stays a file inside the project, and a glance
  you cannot open from your phone is a file, not a glance.

RECOMMENDATION A: the exposure already exists, and the glance is the one thing
built to open on your phone.
DEFAULT A if unruled. This is the one card whose default acts, because the The default acts only once this card has reached you, by the bot with a
receipt or by your own word in the session, and 24 hours have passed since;
until then the deadline moves with it.
exposure already exists and holding the page back would not undo it.
DEADLINE 2026-09-07, the Monday reset.



### 2026-09-04: the Telegram bot exists. RULED A, and it is done.

Jafar created the bot and put the token and chat id into
`tools/runner/config.local` on the PC, gitignored. The card asked for five
minutes; it got them before the deadline it named.

WHAT THIS UNBLOCKS: queue 067 goes from BLOCKED to READY and takes third place
in Monday's order, behind 062 step 2 and Unreal run 21. It was going to be
first after the reset; it moved back one place because the two Unreal items
end in something Jafar can look at and the bot does not.

THE STANDING RULE THAT COMES WITH IT, and it binds every agent: the file is
never printed, echoed, committed, quoted into a log or included in an error
message. A tool that cannot read it says `config.local unreadable` and quotes
nothing. `.gitignore` line 98 already covers the path, checked rather than
assumed, but a gitignore stops a commit and does not stop a print, and a print
is how this class of file actually leaks.

DO NOTHING WITH IT BEFORE MONDAY 14:00 CEST. Ruled by Jafar 2026-09-04.

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
