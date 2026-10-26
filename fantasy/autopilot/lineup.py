"""Pick the best legal starting lineup for a Sleeper roster.

The league's ``roster_positions`` define the slots, so 1QB, superflex, extra
flexes, K/DEF or no K/DEF all fall out of the same code. Filling slots is a
small assignment problem, solved exactly (Hungarian algorithm) so a flex slot
never steals a player that a dedicated slot needed.
"""

from collections import defaultdict
from dataclasses import dataclass

SLOT_ELIGIBILITY = {
    "QB": {"QB"}, "RB": {"RB"}, "WR": {"WR"}, "TE": {"TE"}, "K": {"K"}, "DEF": {"DEF"},
    "FLEX": {"RB", "WR", "TE"},
    "WRRB_FLEX": {"WR", "RB"},
    "REC_FLEX": {"WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
}
NON_STARTING = {"BN", "IR", "TAXI"}
EMPTY = "0"
_INELIGIBLE = 1e9
_EMPTY_COST = 1e6


def starter_slots(roster_positions):
    return [s for s in roster_positions if s not in NON_STARTING]


def hungarian(cost):
    """Min-cost assignment of every row to a distinct column (rows <= cols)."""
    n, m = len(cost), len(cost[0])
    inf = float("inf")
    u, v = [0.0] * (n + 1), [0.0] * (m + 1)
    p, way = [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        p[0], j0 = i, 0
        minv, used = [inf] * (m + 1), [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], inf, 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    assign = [None] * n
    for j in range(1, m + 1):
        if p[j]:
            assign[p[j] - 1] = j - 1
    return assign


@dataclass
class LineupResult:
    starters: list
    changes: list  # (slot_index, slot, old_pid, new_pid)
    locked: list   # starters kept because their game already kicked off


def optimize(slots, current, roster, cost, locked=frozenset()):
    """Return the best starters list for ``slots``.

    ``cost(pid, slot)`` gives a lower-is-better score, or None if the player
    can't fill that slot. Players in ``locked`` (game started) can't move:
    locked starters keep their slot and locked bench players stay benched.
    Slots we don't model (IDP etc.) are left exactly as they are.
    """
    current = list(current) + [EMPTY] * (len(slots) - len(current))
    fixed = {}
    for i, slot in enumerate(slots):
        pid = current[i]
        if slot not in SLOT_ELIGIBILITY or (pid != EMPTY and pid in locked):
            fixed[i] = pid
    taken = set(fixed.values())
    pool = [pid for pid in roster if pid not in taken and pid not in locked]
    open_idx = [i for i in range(len(slots)) if i not in fixed]
    starters = list(current)
    if open_idx:
        cols = pool + [EMPTY] * len(open_idx)
        now_starting = set(current)
        matrix = []
        for i in open_idx:
            row = []
            for pid in cols:
                if pid == EMPTY:
                    row.append(_EMPTY_COST)
                    continue
                c = cost(pid, slots[i])
                # Tiny nudge so ties keep the current starter (no pointless edits).
                row.append(_INELIGIBLE if c is None else c - (1e-3 if pid in now_starting else 0))
            matrix.append(row)
        for r, col in enumerate(hungarian(matrix)):
            starters[open_idx[r]] = cols[col] if matrix[r][col] < _INELIGIBLE else EMPTY
        _keep_positions(slots, current, starters, open_idx)
    changes = [(i, slots[i], current[i], starters[i]) for i in range(len(slots)) if current[i] != starters[i]]
    kept_locked = [current[i] for i in fixed if current[i] != EMPTY and slots[i] in SLOT_ELIGIBILITY]
    return LineupResult(starters, changes, kept_locked)


def _keep_positions(slots, current, starters, open_idx):
    """Within identical slots (RB, RB...), keep players where they already sit."""
    groups = defaultdict(list)
    for i in open_idx:
        groups[slots[i]].append(i)
    for idx in groups.values():
        chosen = [starters[i] for i in idx]
        stay = {i: current[i] for i in idx if current[i] in chosen and current[i] != EMPTY}
        rest = [pid for pid in chosen if pid not in stay.values()]
        for i in idx:
            starters[i] = stay[i] if i in stay else rest.pop(0)
