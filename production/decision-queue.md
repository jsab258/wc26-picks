# The decision queue

STATUS: LIVE. The single home for decisions awaiting Jafar, and the single
record of what he ruled. Written by the Producer, read by the dashboard and by
the bot. Chat is never a record: anything decided in conversation is written
here in the same turn.

THE FLOW, ruled by Jafar 2026-09-03 and AMENDED 2026-09-10 when he ruled one
decision register. A card waits here until he rules or the studio takes it at its
default. A ruled card becomes a register entry and LEAVES THIS FILE: a D-record
under `ledger-v2/respec/decision-register/` when it affects architecture or
identity, a lighter entry in
`ledger-v2/respec/decision-register/queue-rulings-2026-09.md` otherwise. The
dashboard reads WAITING here for its needs-you count and the register for what is
decided. The old shape kept the lighter entries in this file; that is what made
this file a second decision store, and it is why they moved.

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

Nothing waits here. Ruled by Jafar 2026-09-09: the studio takes every decision
that has a recommendation and a default. A card appears below only when the studio
has looked and CANNOT form one, at most one a week, and it carries buttons.


## ON US, NOT ON HIM

A card sits here when it was a real ask and a later measurement showed the
nearest blocker is the studio's own, so there is nothing for Jafar to do yet.
It returns to WAITING the moment our half is cleared and the ask is still live.
Nothing here is pushed to his phone, by construction: `cards.waiting_cards`
filters on the WAITING heading and this is not it.

### The pages cannot be published until the studio's branch may deploy
CLASS: DECISION
added 2026-09-06, from queue 139

Every publish run since 2026-09-05T17:19, eleven of eleven, has failed in
seconds with zero steps executed:

    Branch "claude/game-dev-ai-automation-2h67ix" is not allowed to
    deploy to github-pages due to environment protection rules.

So the glance, the map and the gallery have never been served from this
branch, and every link the Producer's register allows points at a page
that does not exist yet. The card ruled A on 2026-09-05 said Pages "is
not refused"; that was true of the repository setting it measured and
not of the environment rule that refuses the deploy. Only a repository
admin can change it.

- A. GitHub, Settings, Environments, github-pages, deployment branches:
  add `claude/game-dev-ai-automation-2h67ix`.
- B. Name a branch already allowed; the studio publishes from it.

RECOMMENDATION A: one setting, nothing else moves.
DEFAULT: the studio waits. There is no action it can take in your place.
DEADLINE: none set. Nothing decays while it waits, and every day it waits
the Producer's messages link to nothing.

AMENDED 2026-09-09, AND THE AMENDMENT MOVES IT OFF HIS PHONE. Measured on publish
run 48 (commit 650f0755, 06:28Z): the job now fails BEFORE it reaches the deploy,
on our own gate.

    tools/gallery.py --selftest: FAILED. 11 passed, 1 failed, over 10 check(s)
      FAIL the live repository renders a gallery and every check passes
             got: failed=pageBytes
    ##[error]Process completed with exit code 3.

The gallery embeds every picture as base64, the live repository outgrew its own
1000000 byte budget (1000108, twelve pictures dropped), and the publisher runs
that selftest as a gate. Eight consecutive runs this morning, numbers 41 to 48,
failed this way. So the sentence at the top of this card, "every publish run has
failed in seconds with zero steps executed", describes 2026-09-06 and is NOT what
is happening today: runs now execute, get further, and die on us.

AND THE CARD'S OTHER SENTENCE IS ALSO WRONG, CORRECTED 2026-09-09 08:50Z. It says
the three pages "have never been served from this branch". Of 48 publish runs,
FOUR SUCCEEDED: 12, 13, 14 and 18, the last at 2026-09-07T20:23:12Z on commit
45de6c21, which is exactly the pageCommit recorded in production/map-notified.json.
THE PAGES EXIST AND ARE ABOUT 36 HOURS STALE. That is why this card is here rather
than on his phone: the ask it carries was written against a total outage that is
not the current fault, and the current fault is ours.

WHAT IS STILL UNKNOWN, and it is named rather than guessed: whether the
environment protection rule also still refuses the deploy. No run has reached the
deploy step since, so there is no evidence either way. The step summary still
prints `pagesEnableHttp: 403`, which is the agent proxy's answer and not
GitHub's, so it is not evidence about the environment either. The order of
operations is therefore ours first: un-embed the gallery, let a run reach the
deploy, and read what it says. That is the standing rule in `.claude/rules/ci.md`,
run the existing entry point and read its output before proposing a mechanism. If
the environment rule bites after that, this card returns to WAITING unchanged and
option A is still one setting.

---

## WHERE THE DECIDED CARDS WENT, 2026-09-10

Everything this file had already decided moved, verbatim, to
`ledger-v2/respec/decision-register/queue-rulings-2026-09.md`: the TAKEN BY THE
STUDIO section, both RULED THIS WEEK sections, and the two standing orders in
Jafar's own words. Jafar ruled on 2026-09-10 that the project keeps ONE decision
register and that this file keeps OPEN cards only, so a reader asking what is
still on anybody sees only what is still open here, and a reader asking what was
settled goes to the register and finds every kind of ruling in one place.

The register's index is
`ledger-v2/respec/decision-register/rulings-log.md`. It lists the D-numbered
spine, every director ruling under `game-design/decision-*.md` in date order, and
this file's moved cards.

A RULED CARD NO LONGER STAYS HERE. When Jafar rules, or the studio takes a card
at its default, the entry is written into the register in the same turn and the
card leaves this file. The heading `RULED THIS WEEK` is retired: a card that is
ruled is a register entry, not a queue entry.

---

## RETIRED

`game-design/decisions-pending.md` is retired as of 2026-09-03. Its one live
card is above. Its answered cards stay there as history and are not migrated;
the ones that became decisions are D11, D12 and D13 in the register, and the
engine tie-break and deadline rulings live in the 2 September decision records.
