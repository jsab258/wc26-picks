# Balance findings — the living economy (M7)

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
now. He doesn't explain the difference*"). Losing Mirek is now something
the player did, not something the difficulty curve did.

Supplier loss is consequently 0% across all three lab plans, because the
lab's players always have money. The path is still live and still tested:
CoreTests drives a campaign that never pays, and Mirek stops coming.

## What the lab does not cover

- The suppliers now walk and can be talked to; the lab has no conversation
  layer, so their dialogue and the settle-up verb are covered by the
  in-engine sim and by hand, not here.
- Districts beyond Hook Street. The economy is per-district by
  construction, but only one district exists to simulate.
