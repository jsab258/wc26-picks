import unittest

from autopilot.waivers import faab_bid, plan_stream, plan_upgrades

POS = {"fa_rb": "RB", "fa_wr": "WR", "fa_qb": "QB", "my_rb": "RB", "my_wr": "WR",
       "my_qb": "QB", "my_qb2": "QB", "my_te": "TE"}


def plan(values, mine, fas, **kw):
    args = dict(free_agents=fas, my_players=mine, value=values.get, drop_value=values.get,
                position=POS.get, protected=set(), minimums={}, roster_limit=len(mine),
                max_claims=5, min_gain=10)
    args.update(kw)
    return plan_upgrades(**args)


class UpgradeTest(unittest.TestCase):
    def test_swaps_weakest_player_for_clear_upgrade(self):
        values = {"fa_rb": 80, "my_rb": 150, "my_wr": 120}
        claims = plan(values, ["my_rb", "my_wr"], ["fa_rb"])
        self.assertEqual([(c.add, c.drop) for c in claims], [("fa_rb", "my_rb")])

    def test_requires_min_gain(self):
        values = {"fa_rb": 145, "my_rb": 150}
        self.assertEqual(plan(values, ["my_rb"], ["fa_rb"]), [])

    def test_respects_position_minimum(self):
        values = {"fa_wr": 50, "my_qb": 200, "my_qb2": 210, "my_rb": 100}
        claims = plan(values, ["my_qb", "my_qb2", "my_rb"], ["fa_wr"], minimums={"QB": 2})
        self.assertEqual([(c.add, c.drop) for c in claims], [("fa_wr", "my_rb")])

    def test_never_drops_protected_or_unscored(self):
        values = {"fa_rb": 10, "my_rb": 300}
        self.assertEqual(plan(values, ["my_rb", "my_te"], ["fa_rb"], protected={"my_rb"}), [])

    def test_open_roster_spot_needs_no_drop(self):
        values = {"fa_rb": 140, "my_rb": 150}
        claims = plan(values, ["my_rb"], ["fa_rb"], roster_limit=2)
        self.assertEqual([(c.add, c.drop) for c in claims], [("fa_rb", None)])

    def test_caps_claims_and_skips_blocked_drops(self):
        values = {"fa_rb": 10, "fa_wr": 20, "my_rb": 300, "my_wr": 290}
        claims = plan(values, ["my_rb", "my_wr"], ["fa_rb", "fa_wr"], max_claims=1,
                      blocked_drops={"my_rb"})
        self.assertEqual([(c.add, c.drop) for c in claims], [("fa_rb", "my_wr")])


class StreamTest(unittest.TestCase):
    def test_streams_when_my_kicker_is_on_bye(self):
        values = {"fa_k": 4, "my_k": None}
        c = plan_stream(free_agents=["fa_k"], mine=["my_k"], value=values.get, margin=6, open_spot=False)
        self.assertEqual((c.add, c.drop), ("fa_k", "my_k"))

    def test_keeps_kicker_when_gain_is_small(self):
        values = {"fa_k": 4, "my_k": 8}
        self.assertIsNone(plan_stream(free_agents=["fa_k"], mine=["my_k"], value=values.get,
                                      margin=6, open_spot=False))


class FaabTest(unittest.TestCase):
    tiers = [[30, 0.25], [60, 0.15], [100, 0.08], [150, 0.04]]

    def test_bid_scales_with_value(self):
        self.assertEqual(faab_bid(20, 100, self.tiers, 0), 25)
        self.assertEqual(faab_bid(90, 100, self.tiers, 0), 8)
        self.assertEqual(faab_bid(400, 100, self.tiers, 1), 1)

    def test_bid_respects_budget(self):
        self.assertEqual(faab_bid(20, 3, self.tiers, 1), 1)
        self.assertIsNone(faab_bid(20, 0, self.tiers, 1))


if __name__ == "__main__":
    unittest.main()
