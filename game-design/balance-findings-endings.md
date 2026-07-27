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
| Control | answered | 0.0% | 0.0% | 49.8% | 50.3% | 0.50 |
| Control | stonewalled | 0.0% | 0.0% | 49.8% | 50.3% | 0.84 |
| Control | answered+deflect | 0.0% | 0.0% | 49.8% | 50.3% | 0.35 |
| Aggressive | ignored | 0.0% | 0.0% | 0.0% | **100.0%** | 1.00 |
| Aggressive | answered | 0.0% | 0.0% | 0.0% | **100.0%** | 0.77 |
| Aggressive | stonewalled | 0.0% | 0.0% | 0.0% | **100.0%** | 1.00 |
| Aggressive | answered+deflect | 0.0% | **100.0%** | 0.0% | 0.0% | 0.54 |
| Cautious | ignored | 0.0% | 21.5% | 0.0% | 78.5% | 0.79 |
| Cautious | answered | 0.0% | **47.8%** | 0.0% | **52.3%** | 0.61 |
| Cautious | stonewalled | 0.0% | 3.3% | 0.0% | 96.8% | 0.94 |
| Cautious | answered+deflect | **14.8%** | 85.3% | 0.0% | 0.0% | 0.43 |

*Re-measured 2026-07-27 after decisions 9 and 10 landed. The rows above are
the CURRENT numbers; the pre-decision ones are in git history if wanted.*

Reads correctly now: ignoring the audit costs you everything, stonewalling is
worse than ignoring, answering it every morning is the difference between
losing the lot and keeping the street, and keeping *both* lives is rare and
takes a campaign that was careful the whole way through.

`Quiet` is absent by construction — handing over is a deliberate act and the
lab bot never reaches for it. Its arithmetic is covered in CoreTests.

## What decision 10 did to it

~~The inspector may now be too decisive.~~ **Answered and built.** The
cooperation relief was halved (0.09 → 0.045) and stonewalling kept its full
weight. Read the Aggressive block above: answering every morning used to turn
100% Burn Both into 100% Kingdom, and now it does not move the outcome at all
— it moves the *strain*, 1.00 to 0.77, which is real but no longer enough to
launder a campaign that was never clean. The last week can no longer rescue
everything; it can only rescue something that was nearly saveable.

Cautious-and-answered is now the genuinely interesting row: **47.8/52.3**, a
coin-flip that the campaign's own history decides. That is the shape this
matrix should have had all along.

## A NEW observation, for the playtest — not yet a decision

**The inspector is completely inert for a player who never built an empire.**
Look down the Control block: four different ways of dealing with six days of
Tobias Reisz, and the outcome is 49.8 / 50.3 in every single one. The strain
he sees moves properly (0.84 down to 0.35) and then changes nothing, because
with no empire there is no Kingdom and no Both to reach — Straight Life
against Burn Both is decided on the life axis, which the audit does not touch.

That is arguably correct: there is nothing to inspect, so inspecting harder
finds nothing. But it means **one of the three playstyles experiences the
entire third act as scenery** — its central verb has no consequence for them.
Worth feeling before deciding. Three honest options if it turns out to matter:
let the audit reach the life (his attention costs you evenings), give the
straight player something of their own to protect, or accept it and make sure
the writing says "there is nothing here to find" rather than staying silent.

**My recommendation: play it first.** The lab cannot tell you whether inert
reads as peaceful or as pointless, and that distinction is the whole question.
