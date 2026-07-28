# Finite counterparty purses — M13 spec (player decision, 2026-07-27)

> *"add it to the end of the roadmap and spec/build it"*

## The gap

The living economy (M7) made the district's money finite in one direction:
squeezing the street lowers prosperity, prosperity lowers what your bar takes.
That half is real and the balance lab proves it.

But every *counterparty* still has infinite pockets. Rita owes $180 and Rita
pays $180, in one movement, whenever you ask. The street can be starving and
the man in front of you still produces the exact sum from nowhere. That is a
payout table wearing a person's face, and it is the same failure the rest of
this project is built to avoid.

KCD2 gets this right in a way most games do not: **traders hold a finite
purse.** You loot four suits of plate and physically cannot convert them to
cash in one place — you sell what the armourer can actually pay, then walk to
the next town or wait days for his purse to refill. It turns money into a
logistics problem and makes the map bigger without adding a metre of map.

The version of that which belongs in THIS game is not logistics. It is:
**who has the cash, and what do they want for fronting it.** That is a
conversation, and conversations are what this game is made of.

## The design

### 1. Everybody who might pay you has a purse

A purse is what somebody can lay hands on *today*: not their wealth, not
their income — the money in the drawer. Three numbers, none of them ever
shown:

| | |
|---|---|
| **Cash** | what is in the drawer right now |
| **Weekly** | what flows through them in an ordinary week |
| **Ceiling** | the most they would ever keep to hand rather than spend or bank |

Purses top up daily by a seventh of Weekly, **scaled by the district's
prosperity**. This is the part that matters: squeezing the street does not
just cost you bar takings, it drains the pockets you are trying to collect
from. Two turns of the same screw, and the second one is the one that hurts,
because it arrives when you are relying on being paid.

Purses are generated on demand from a stable hash of the person's id, so the
system covers all three thousand residents without anybody authoring three
thousand numbers, and the same person always has the same means.

### 2. Asking for more than somebody has gets you what they have

`Collect` currently has three outcomes: paid, begged, refused. It gets a
fourth and it is the interesting one: **paid what they could.** They empty
the drawer, the balance stays on the page, and they remember that you stood
there while they counted.

This changes the shape of a big marker. A $400 debt against a man who turns
over $90 a week is not one collection, it is a relationship — four visits, or
one visit and a decision about what you are willing to do to shorten it.

### 3. They can go and get it — and that costs them something

A debtor who was emptied and still owes will, if they have anybody to go to,
**borrow from a patron** overnight. Next time you ask, the money is there.

What it costs is the point:

- The patron is now owed a favour, recorded as real world state rather than
  as flavour text. The Director can read it and act on it.
- The debtor's loyalty to *you* falls harder than a straight payment would
  cost, because you are the reason they had to go asking.
- The patron's purse is now lighter, so the money moved rather than
  appearing. The district's cash is conserved.

You will often not know this happened. You will notice that they paid, and
that they are colder about it than the money explains.

### 4. Legibility, as everywhere else

No purse number is ever shown. Being short is somebody turning the drawer
round so you can see it. Borrowing is somebody paying you in full and not
meeting your eye. If it cannot be said as a circumstance it does not get
said.

## What is NOT in scope

- **Rackets.** Racket income is already coupled to the district through
  prosperity; putting a per-business till on top would double-count the same
  pressure and make the empire loop fiddly rather than deeper.
- **The player's own money.** Already finite; that is the Wallet.
- **Banking, interest, credit lines, or a lending market.** One patron, one
  favour. A lending economy is a different game.
- **Trader purses for buying goods.** There is no goods trade in LEDGER —
  the KCD parallel is instructive, not literal.

## The failure mode to watch, learned from KCD2

KCD2's early economy is tight and memorable, and then blacksmithing and
alchemy turn into money printers and it stops existing. The equivalent risk
here is that finite purses make early collection *harder* while some other
channel stays unlimited, so the player simply routes around it.

So: the balance lab runs against this before it is called done, and the
number that must hold is the one that already holds — aggressive play must
not dominate. If purses make collection weaker without making anything else
weaker, they have moved the optimum rather than deepened the choice.
