# Open-City Balance Findings (Monte-Carlo, 2026-07-26)

> **STATUS: LOG, 2026-07-26. NOT CURRENT.** A record of what was true on the
> day, kept because the reasoning is worth having. **Do not read it as the
> present state** — for that, `roadmap.md`. Items called "open" here have
> very likely been closed since.

BalanceLab extension: 300 seeded 21-day campaigns per plan (week 1 with
smart damage control, then open mode + empire per plan). Lab mirrors the
in-game wiring: same tunables, same Fall consequences, same rival ladder.

## Results (300 runs/plan)

| plan | reached open | end cash | falls/run | cut off | rival stage | racket $ | broke |
|---|---|---|---|---|---|---|---|
| Control (no empire) | 99.7% | $2825 | 0.06 | 0% | 0.0 | 0 | 0% |
| Aggressive (debt+squeeze, 2 crew, 2 rounds) | 99.7% | $3138 | 0.61 | 0% | 3.7 | $1708 | 0% |
| Cautious (clean buy, 1 crew, 1 round, slow) | 99.7% | $2512 | 0.12 | 0% | 1.0 | $469 | 0% |

## Reading

1. **No death spiral.** Zero bankruptcies anywhere: the stage-2 rival tax
   ($40/day) plus heat-taxed takings never compounds into an unrecoverable
   hole, because the Fall clears heat (the street *knows*, so it stops
   guessing) and the bar's base income survives everything. The scarring
   fail state is survivable in practice, not just in principle.
2. **Aggression is high-drama, thin-margin.** +$313 over control (+11%)
   buys 10x the Falls and a rival at poach/threat stage. That is a
   defensible v1 shape — the empire's real payoff is capacity and position,
   not raw cash — but if playtests want empire to feel more lucrative,
   first knobs: racket income up (60/80 -> 80/100) or rival tax onset later
   (stage-2 threshold 0.5 -> 0.6).
3. **Caution loses money inside 21 days.** The $900 clean purchase hasn't
   amortized by day 21 (+$480 income at zero heat, plus wash capacity).
   Long-game correct, short-window negative — a genuinely interesting
   choice, and worth surfacing diegetically (Lena could say the shop pays
   for itself in a month).
4. **The rival ladder gets fully exercised** under aggression (avg 3.7 =
   poach attempts routine, threats common), and never wakes under control —
   attention is doing its job as an *observation* system.
5. **Nobody gets cut off** — bots keep making drops. The outfit-rivalry
   pivot (cut-off as the path to full independence) stays theoretical until
   a policy skips drops deliberately; fine for v1, revisit when the rackets
   can replace drop income deliberately.

## Decision

No tuning changes shipped now: the curves are sound and the interesting
tensions (risk/reward, short/long money) are where design wants them.
Knobs above are documented for the first human playtest of open mode.
