# Balance findings — the living economy (M7)

> **STATUS: LOG, 2026-07-28. NOT CURRENT.** A record of what was true on the
> day, kept because the reasoning is worth having. **Do not read it as the
> present state** — for that, `roadmap.md`. Items called "open" here have
> very likely been closed since.

Run: 300 open-city campaigns per plan, 21 in-game days each, smart damage
control throughout. Same harness that proved the open economy has no death
spiral; the district simulation is now inside it and gated by it.

## The numbers

| plan | reach% | end cash | falls | broke% | street | prices | supplier lost |
|---|---|---|---|---|---|---|---|
| Control (takes nothing) | 100% | $2279 | 0.07 | 0% | 0.48 | 1.00 | 0% |
| Aggressive | 100% | $2185 | 0.62 | 0% | 0.22 | 1.21 | 0% |
| Cautious | 100% | $1866 | 0.15 | 0% | 0.39 | 1.07 | 0% |

*street: 0–1, 0.55 is ordinary · prices: 1.00 is ordinary*

## What it says

**The loop works, and it is a real trade.** Aggressive play earns **$1697**
in racket income over three weeks and ends with **$94 less** than a
campaign that ran no rackets at all. The rackets pay; the street pays for
the rackets; the bar's till is where the bill arrives. There is no
dominant strategy, which is the entire point of building this rather than
adding another income source.

**A campaign that takes nothing is unchanged.** Control sits at street 0.48
and prices 1.00 — a takings factor of about 0.98, which is invisible. That
matters: the economy was added underneath a game people are about to play,
and it must not have quietly rebalanced the week they already know.

**No collapse, no inflation.** Prices top out at 1.21 under the most
aggressive play the lab can produce. Prosperity bottoms at 0.22 — "hurting"
— and the takings factor's floor (0.35) was never reached. Zero
bankruptcies across all 900 campaigns.

## One tuning decision worth recording

The first build lost a supplier in **100%** of aggressive campaigns. That
is not difficulty, it is a scripted event wearing a simulation's clothes —
the player made no decision and got a guaranteed outcome.

Changed so that **neglect loses a supplier, and a poor neighbourhood only
makes him dearer.** Paying on time buys more standing (0.28/week) than the
worst squeeze-and-heat drift can take away (0.245/week), so a man who is
paid every Thursday keeps coming however hard you squeeze the street — he
just charges more for it, and you hear him do it ("*he asks $118 for it
now. He doesn't explain the difference*"). Losing Mitch is now something
the player did, not something the difficulty curve did.

Supplier loss is consequently 0% across all three lab plans, because the
lab's players always have money. The path is still live and still tested:
CoreTests drives a campaign that never pays, and Mitch stops coming.

## What the lab does not cover

- The suppliers now walk and can be talked to; the lab has no conversation
  layer, so their dialogue and the settle-up verb are covered by the
  in-engine sim and by hand, not here.
- Districts beyond Hook Street. The economy is per-district by
  construction, but only one district exists to simulate.

---

## M13 — finite counterparty purses (2026-07-27)

The spec set one bar before this could be called done: *if purses make
collection weaker without making anything else weaker, they have moved the
optimum rather than deepened the choice.* That is KCD2's own failure mode in
reverse, and it is the thing worth checking.

400 weeks per policy. Two new rows, plus two that turned out to prove nothing
and are kept because knowing why is worth a line:

| policy | avg$ | collected | visits | part-payments |
|---|---|---|---|---|
| collector | 1642 | 60 | 1.0 | 0.0 |
| collector+purse | 1642 | 60 | 1.0 | 0.0 |
| warm-collect | 1762 | 180 | 2.0 | 0.0 |
| **warm-collect+purse** | **1762** | **180** | **3.0** | **1.0** |

**The plain collector rows are identical, and that is correct rather than a
null result.** Sam's authored loyalty is 0.3, so he refuses whatever is in his
pocket and the purse is never opened; Rocco is willing and can afford his $60
outright. Nothing about finite purses can matter to a player who never made
anybody willing to pay in the first place.

**The warm rows are the test.** They model a player who did the favours first
and is now collecting from people who want to pay. Without purses, willing
means paid in full on the spot: two visits, $180, done. With purses, willing
means paying what is in the drawer — Sam produces $45 against a $120 marker,
goes to his uncle that night, and closes it out on a later visit.

**Same money. Same end cash to the dollar. One more visit and one
part-payment.** That is exactly the intended result: the shape of collection
changed and the optimum did not move. Nothing was nerfed, and a debt stopped
being a transaction.

The open-city table is unchanged by this — aggressive play still earns $1697
in rackets and still finishes $94 behind a campaign that runs none.

**What this does NOT yet test:** a squeezed street's effect on purses. In week
mode prosperity sits at the ordinary half by construction, so the coupling
that drains your debtors' pockets when you squeeze the district is proven in
CoreTests and not yet in the lab. It needs the open-city path to collect
debts, which it currently does not. Worth doing; not a blocker, and stated
here rather than left as an impression that the lab covered it.
