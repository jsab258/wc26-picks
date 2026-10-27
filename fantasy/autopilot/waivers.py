"""Decide which waiver claims to make, and what to bid.

All values here are "rank-like": lower is better, comparable across positions.
"""

from collections import Counter
from dataclasses import dataclass


@dataclass
class Claim:
    add: str
    drop: str | None
    add_value: float
    drop_value: float | None
    kind: str  # "upgrade" (rest-of-season) or "stream" (K/DEF for the coming week)
    bid: int | None = None


def plan_upgrades(*, free_agents, my_players, value, drop_value, position, protected,
                  minimums, roster_limit, max_claims, min_gain, blocked_drops=(),
                  max_depth=None, healthy=lambda p: True):
    """Greedy best-FA-first: each claim drops the weakest player it clearly beats.

    ``value`` scores free agents, ``drop_value`` scores my players (None means
    "never drop", e.g. we couldn't confidently rank him). A swap must improve by
    at least ``min_gain`` and may not take a position below its minimum; minimums
    count healthy players only. Past ``max_depth`` at a position (e.g. a 4th QB in
    superflex) a pickup may only replace a player at its own position.
    """
    max_depth = max_depth or {}
    counts = Counter(position(p) for p in my_players if healthy(p))
    open_spots = roster_limit - len(my_players)
    candidates = [p for p in my_players
                  if p not in protected and p not in blocked_drops and drop_value(p) is not None]
    candidates.sort(key=drop_value, reverse=True)  # weakest first
    fas = sorted((p for p in free_agents if value(p) is not None), key=value)
    claims = []
    for fa in fas:
        if len(claims) >= max_claims:
            break
        fv, fpos = value(fa), position(fa)
        deep = fpos in max_depth and counts[fpos] >= max_depth[fpos]
        if open_spots > 0 and not deep:
            claims.append(Claim(fa, None, fv, None, "upgrade"))
            open_spots -= 1
            counts[fpos] += healthy(fa)
            continue
        for d in candidates:
            dv = drop_value(d)
            if dv - fv < min_gain:
                break  # everyone after this is even better than d
            dpos = position(d)
            if dpos != fpos and deep:
                continue
            # Healthy players left at the drop's position (an injured pickup doesn't replace a healthy one).
            left = counts[dpos] - healthy(d) + (dpos == fpos and healthy(fa))
            if left < counts[dpos] and left < minimums.get(dpos, 0):
                continue
            claims.append(Claim(fa, d, fv, dv, "upgrade"))
            candidates.remove(d)
            counts[dpos] -= healthy(d)
            counts[fpos] += healthy(fa)
            break
    return claims


def plan_stream(*, free_agents, mine, value, margin, open_spot):
    """Swap a K or DEF for a free agent with a clearly better matchup this week."""
    fas = sorted((p for p in free_agents if value(p) is not None), key=value)
    if not fas:
        return None
    best = fas[0]
    if not mine:
        return Claim(best, None, value(best), None, "stream") if open_spot else None

    def v(p):  # my guy on bye / unranked counts as unusable
        return value(p) if value(p) is not None else 1e9

    ranked = sorted(mine, key=v)
    if v(ranked[0]) - value(best) < margin:
        return None
    drop = ranked[-1]
    return Claim(best, drop, value(best), value(drop), "stream")


def faab_bid(value, remaining, tiers, min_bid):
    """Bid a share of the remaining budget that grows with how good the player is.

    ``tiers`` is [[max_value, fraction], ...], checked in order.
    Returns None if we can't afford even the minimum bid.
    """
    if remaining < min_bid:
        return None
    frac = next((f for limit, f in tiers if value <= limit), 0.0)
    return max(min_bid, min(remaining, int(frac * remaining)))
