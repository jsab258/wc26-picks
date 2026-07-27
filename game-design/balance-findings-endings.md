# Balance findings — the ending matrix (2026-07-27)

Run: `dotnet run --project ledger/BalanceLab -c Release`, 400 worlds per row.

The endgame's distribution had never been measured. It was known only from
unit tests, which prove that a *given* world resolves correctly and say
nothing about which worlds a player actually ends up in.

The lab now takes the same 21-day campaigns it already runs, and resolves
Act III over the world each one ends in — four ways, so the inspector's verb
and the deflection are visible as axes rather than assumed.

## What it found, in order of how bad it was

**1. A player who never built an empire had exactly one ending.**
`StraightLife` required `EmpireDissolved` — and you cannot dissolve what you
never bought. The do-nothing plan ended in *"you lose the business and you
lose the people"* 100 times out of 100, having neither. Fixed: the condition
is **no empire**, not **dissolved an empire**. Never building it is a way of
keeping your life, and it is the hardest one to play, so it gets the same
door and its own paragraph.

**2. "Both" fired 51-58% of the time.** The design calls it *rare, and earned
rather than lucky*; the player's decision was *not reachable on a first
playthrough*. It was a two-step win button: point the case elsewhere (×0.7)
and answer the inspector (×0.55), and an aggressive campaign's strain fell
from 1.00 to 0.39. Fixed: mitigation still saves you from losing everything,
and no longer BUYS you the best ending — Both additionally requires the raw
books to hold, which is a judgement about three acts of play rather than
about six mornings of paperwork. Now 13%, and only for a careful campaign.

**3. A hole in the matrix with no cell.** Empire kept, life kept, street
managed, audit survived — but books saved by handling rather than by making
sense — qualified for nothing and fell through to Burn Both. They survived
the reading; losing everything is the one thing that clearly did not happen.
`Kingdom` no longer requires the life to be gone (Both already outranks it,
so the ordering does that work).

## The matrix as it stands

| plan | inspector | Both | Kingdom | Straight | Burn | seen strain |
|---|---|---|---|---|---|---|
| Control | ignored | 0.0% | 0.0% | 49.8% | 50.3% | 0.64 |
| Control | answered | 0.0% | 0.0% | 49.8% | 50.3% | 0.35 |
| Control | stonewalled | 0.0% | 0.0% | 49.8% | 50.3% | 0.84 |
| Control | answered+deflect | 0.0% | 0.0% | 49.8% | 50.3% | 0.25 |
| Aggressive | ignored | 0.0% | 0.0% | 0.0% | **100.0%** | 1.00 |
| Aggressive | answered | 0.0% | **100.0%** | 0.0% | 0.0% | 0.55 |
| Aggressive | stonewalled | 0.0% | 0.0% | 0.0% | **100.0%** | 1.00 |
| Aggressive | answered+deflect | 0.0% | 100.0% | 0.0% | 0.0% | 0.39 |
| Cautious | ignored | 0.0% | 19.3% | 0.0% | 80.8% | 0.81 |
| Cautious | answered | 0.0% | 100.0% | 0.0% | 0.0% | 0.44 |
| Cautious | stonewalled | 0.0% | 3.0% | 0.0% | 97.0% | 0.95 |
| Cautious | answered+deflect | **13.0%** | 87.0% | 0.0% | 0.0% | 0.31 |

Reads correctly now: ignoring the audit costs you everything, stonewalling is
worse than ignoring, answering it every morning is the difference between
losing the lot and keeping the street, and keeping *both* lives is rare and
takes a campaign that was careful the whole way through.

`Quiet` is absent by construction — handing over is a deliberate act and the
lab bot never reaches for it. Its arithmetic is covered in CoreTests.

## The one thing still worth your judgement

**The inspector may now be too decisive.** The swing from "ignored" to
"answered" is total on the aggressive plan: 100% Burn Both to 100% Kingdom.
Six mornings of paperwork currently outweighs three acts of laundering
decisions. It is defensible — that row is perfect play against him, and
five cooperations out of six possible is close to maximal — but it is worth
knowing that the last week can rescue the whole campaign.

See `decisions-pending.md` #10.
