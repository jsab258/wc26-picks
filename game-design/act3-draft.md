# Act III — The Ledger Comes Due

Drafted 2026-07-27 (player: *"do content (Act III, Copper Row) and system
(phones), then I'll test"*). Per doc §8: a triggered crisis forces the books
open, and the endgame matrix is **empire × life**.

Same design bet as Acts I and II: the machinery we already built IS the act's
skeleton, and authored meaning lays over it. Every pressure point fires on
CONDITIONS. No dates, no timers.

**Act III opens** when the Table has been answered (Act II's PP7) AND one of
the two ledgers has become undeniable — Ellis's case is strong enough to name
the rackets, or the empire is large enough that the bar cannot explain its own
money. The question Act I asked was *what did you inherit*. Act II asked *how
big can this get before the lives touch*. Act III asks the only question left:
**which of these two lives is the real one, and what are you willing to spend
to find out.**

---

## The crisis: the books open

Act III's opening image is not a raid. It is **an audit** — the least dramatic
possible instrument, which is what makes it frightening. Somebody with a
mandate asks to see the pub's books, and the pub's books are the one document
in this game that has been quietly lying since day one.

Everything the player has done to the ledger is now evidence in the other
direction. Laundered too little and the racket money has nowhere to have come
from. Laundered too much and the bar earned more than a bar on this street
possibly could. **The lie has a shape, and the shape is now being measured.**

That is the crisis, and it cannot be fought — only survived, deflected onto
somebody, or answered by choosing which life to keep.

---

## The four endings, as STATES rather than as a menu

The matrix is *empire × life*. The critical design rule: **the player never
picks an ending from a list.** Each ending is a condition the world can be in
when the crisis resolves, and more than one can be live at once — in which
case the player's last decisions choose between them.

| | **Empire survives** | **Empire lost** |
|---|---|---|
| **Life survives** | **Both** — hardest. Requires the information landscape actively managed: the day circle must not hold the rackets as fact, and Ellis's case must be answerable. | **The Straight Life** — you give up the business to keep the people. |
| **Life lost** | **The Kingdom** — you keep everything you built and nobody is left who knew you before it. | **Burn Both** — the ledger takes it all. |

And the fifth, which is the one the design doc calls out specially and the one
I care most about:

> **The Quiet Ending — hand the empire to a crew member you built up, and see
> if what you built survives you.**

This is not a fifth cell in the matrix; it is a way of *leaving* it. It has
the hardest precondition of the five and it is the only ending where the game
keeps running for a few days after your last decision, so the player can watch
whether their successor holds.

### What each ending actually requires

Deliberately expressed in state the game already tracks, so none of this is a
new subsystem:

- **Both** — day-circle heat about the rackets below the fact threshold, AND
  Ellis's case answerable (her strongest lead discredited, bought, or
  contradicted), AND at least one day-life relationship still above trust.
  Very hard. Should be rare and should feel earned rather than lucky.
- **The Kingdom** — empire intact, every day-life loyalty below trust or
  departed. The game does not editorialise; the last scene is simply somebody
  who used to know you being polite.
- **The Straight Life** — the empire dissolved by the player (businesses sold,
  rackets ended, crew paid off) before the audit closes. Money is lost. The
  people stay.
- **Burn Both** — the audit closes with the empire intact and the day circle
  holding it as fact. This is the default outcome of doing nothing, which is
  correct: the ledger comes due whether or not you answer it.
- **The Quiet Ending** — a crew member with high competence, high loyalty,
  independence earned (the existing promotion machinery), and no live feud
  with anyone else in the crew. Hand it over, and the game plays three more
  days without you in charge.

---

## Pressure points

**PP1 — The Letter (fires: act opens).**
Not a person. A letter, on the counter, in the morning, addressed to the bar
rather than to you. Authored: the letter's text, which is courteous and
entirely procedural and mentions a date. The player can read it, ignore it,
show it to Lena — and Lena, who has kept the true books since before you
arrived, is the only person who fully understands what it means.

**PP2 — What Lena Knows (fires: PP1 read, and Lena's loyalty above trust).**
The bookkeeper's scene. She has been keeping two sets of books this whole
time and she tells you exactly how much of the lie will hold and exactly
where it will not. **This is the single most valuable piece of information in
the game and it is gated entirely on a relationship**, which is the thesis of
the project stated as a mechanic. If her loyalty is low she says less; if she
has been skimmed or lied to, she says almost nothing and is not lying about
why.

**PP3 — Ellis's Offer (fires: Ellis's case strength above the naming
threshold).**
She does not arrest anybody. She offers a trade, in her own voice: somebody
else. Give her the arm that has been hardest on you — Sera's dockside, the
machine, or Danny's crew — with enough to make it stick, and the audit finds
what it needs elsewhere. The cost is that everything you hand over came from
somebody who told you, and the mill knows who talks.

**PP4 — The Succession Question (fires: any crew member reaches independence
AND the audit is live).**
Somebody in your crew realises what you are about to lose, and asks for it.
Not a betrayal — an offer. Authored: their pitch, in their own register.
Systemic: whether they could actually hold it is computed, and the player is
NOT shown the number. You are being asked to judge a person, which is what
this game is for.

**PP5 — Who You Call (fires: the audit's final day).**
The phone layer (M10) pays off here. On the last day the player can reach
exactly a few people, and reaching one costs the chance to reach another —
messages left with people, somebody unreachable at the worst moment. The set
of people you *can* call is your whole campaign expressed as a contact list.

**PP6 — The Ledger Comes Due (fires: the audit closes).**
The act's summit and the game's last authored scene. Not a boss and not a
choice screen: the books are opened, and what happens is computed from the
state the player has spent three acts building. Then the ending that the
world qualifies for plays, and if more than one qualifies, the last thing
the player did decides.

**PP7 — After (fires: the Quiet Ending only).**
Three more days. You are not in charge. You watch your successor run it —
their competence and loyalty driving the same racket and rival machinery,
without you — and the game ends on whether it held. **The only ending with an
epilogue, because it is the only one that asks a question the player cannot
answer themselves.**

---

## What this needs built

1. `ActThree` in Core: act-open condition, audit state with a closing day,
   the five ending conditions as pure functions of world state, and the
   resolution that picks between live ones. **Tested**, because "which ending
   did the player earn" is exactly the kind of thing that must never be
   decided by a coin flip or by the model.
2. The audit's pressure on the ledger — reading laundering history in both
   directions (too little, too much).
3. Succession: can this crew member hold it? Reuses competence, loyalty,
   independence and feuds.
4. Seven authored text moments.
5. The epilogue mode for the Quiet Ending.

## Answered by Jafar, 2026-07-27

1. **"Both" is NOT achievable on a first playthrough.** Confirmed. It stays
   visible in hindsight as a thing that was possible once you understand what
   the information landscape is — the first campaign teaching you what the
   second one is for.
2. **The Quiet Ending's epilogue is watch-only.** No verbs. Three days, and
   you are not in charge of them.
3. **You CAN refuse Ellis and still reach "Both"** — but only through the
   information landscape. That makes refusing her the hardest and most
   interesting line in the act, which is the point of allowing it.

## Still open — the biggest one, and I should have asked it first

**Is an audit the right crisis at all?** It is the least dramatic instrument
available and that is exactly why I chose it: a courteous procedural letter is
frightening in a way a raid is not, and it turns three acts of laundering
decisions into the thing that convicts you. But this is the ending of the
game, and a raid, a betrayal, or a death are all defensible instead. Not
building the wiring until this is settled.
