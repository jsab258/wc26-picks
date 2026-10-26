import unittest

from autopilot.lineup import EMPTY, SLOT_ELIGIBILITY, hungarian, optimize

POS = {"qb1": "QB", "qb2": "QB", "qb3": "QB", "rb1": "RB", "rb2": "RB", "rb3": "RB",
       "wr1": "WR", "wr2": "WR", "wr3": "WR", "te1": "TE", "te2": "TE", "k1": "K", "d1": "DEF"}


def ranked(ranks, sf_bonus=0):
    def cost(pid, slot):
        if POS[pid] not in SLOT_ELIGIBILITY[slot]:
            return None
        c = ranks[pid]
        return c - sf_bonus if slot == "SUPER_FLEX" and POS[pid] == "QB" else c
    return cost


class HungarianTest(unittest.TestCase):
    def test_flex_does_not_steal_from_dedicated_slot(self):
        # Greedy "best player into first open slot" would put A in row 0 and
        # leave row 1 (only A eligible) unfilled; the optimum swaps them.
        big = 1e9
        self.assertEqual(hungarian([[1, 2], [3, big]]), [1, 0])


class OptimizeTest(unittest.TestCase):
    slots = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX", "K", "DEF"]
    roster = list(POS)
    ranks = {"qb1": 6, "qb2": 30, "qb3": 90, "rb1": 2, "rb2": 15, "rb3": 45,
             "wr1": 3, "wr2": 12, "wr3": 40, "te1": 28, "te2": 120, "k1": 1, "d1": 1}

    def test_superflex_starts_second_qb(self):
        res = optimize(self.slots, [], self.roster, ranked(self.ranks))
        self.assertEqual(res.starters[self.slots.index("SUPER_FLEX")], "qb2")
        self.assertEqual(res.starters[self.slots.index("FLEX")], "wr3")
        self.assertEqual(res.starters[0], "qb1")

    def test_qb_bonus_tips_close_calls(self):
        ranks = dict(self.ranks, qb2=50)  # rb3 (45) beats qb2 on raw ECR...
        plain = optimize(self.slots, [], self.roster, ranked(ranks))
        self.assertEqual(plain.starters[self.slots.index("SUPER_FLEX")], "rb3")
        lean = optimize(self.slots, [], self.roster, ranked(ranks, sf_bonus=10))
        self.assertEqual(lean.starters[self.slots.index("SUPER_FLEX")], "qb2")  # ...until the bonus

    def test_locked_players_stay_put(self):
        current = ["qb1", "rb1", "rb3", "wr1", "wr2", "te1", "wr3", "qb2", "k1", "d1"]
        # rb3/wr3 already playing (locked) so they keep their slots; the best
        # player left over (rb2) then takes the open SUPER_FLEX from qb2.
        res = optimize(self.slots, current, self.roster, ranked(self.ranks), locked={"rb3", "wr3"})
        self.assertEqual(res.starters, current[:7] + ["rb2", "k1", "d1"])
        self.assertEqual(set(res.locked), {"rb3", "wr3"})

    def test_locked_bench_player_cannot_come_in(self):
        current = ["qb1", "rb1", "rb3", "wr1", "wr2", "te1", "wr3", "qb2", "k1", "d1"]
        res = optimize(self.slots, current, self.roster, ranked(self.ranks), locked={"rb2"})
        self.assertNotIn("rb2", res.starters)

    def test_no_changes_when_only_order_differs(self):
        current = ["qb1", "rb2", "rb1", "wr2", "wr1", "te1", "wr3", "qb2", "k1", "d1"]
        res = optimize(self.slots, current, self.roster, ranked(self.ranks))
        self.assertEqual(res.changes, [])

    def test_unknown_slots_left_alone_and_empty_filled(self):
        slots = ["QB", "RB", "DL"]
        res = optimize(slots, [EMPTY, "rb2", "idp9"], ["qb1", "rb1", "rb2", "idp9"],
                       lambda pid, slot: None if pid == "idp9" else ranked(self.ranks)(pid, slot))
        self.assertEqual(res.starters, ["qb1", "rb1", "idp9"])

    def test_not_enough_players_leaves_slot_empty(self):
        res = optimize(["QB", "TE"], [], ["qb1"], ranked(self.ranks))
        self.assertEqual(res.starters, ["qb1", EMPTY])


if __name__ == "__main__":
    unittest.main()
