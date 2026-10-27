"""Whole-league run against fixture data and a fake Sleeper writer."""

import unittest

from autopilot import fantasypros as fp
from autopilot.config import DEFAULTS
from autopilot.engine import League
from autopilot.rankings import IdMap, RankList

PLAYERS = {pid: {"full_name": pid, "position": pos, "fantasy_positions": [pos], "team": team}
           for pid, pos, team in [
               ("qb_a", "QB", "KC"), ("qb_b", "QB", "BUF"), ("rb_c", "RB", "DET"), ("rb_d", "RB", "NYJ"),
               ("wr_e", "WR", "MIA"), ("wr_f", "WR", "SEA"), ("te_g", "TE", "LV"), ("k_1", "K", "KC"),
               ("qb_fa", "QB", "TB"), ("wr_fa", "WR", "CHI"), ("k_fa", "K", "MIN")]}
PLAYERS["DET"] = {"first_name": "Detroit", "last_name": "Lions", "position": "DEF",
                  "fantasy_positions": ["DEF"], "team": "DET"}
PLAYERS["wr_f"]["injury_status"] = "Out"
NOW, KICKOFF = 1_000, 10_000


def ecr(week, rows):
    return {"week": str(week), "type": "test", "players": [
        {"player_id": pid, "player_name": pid, "player_position_id": "DST" if pid == "DET" else PLAYERS[pid]["position"],
         "player_team_id": PLAYERS[pid]["team"], "rank_ecr": rank, "pos_rank": pos_rank,
         "player_bye_week": "14", "player_opponent": "vs. X", "player_game_kickoff_ts": KICKOFF,
         "player_game_status": "created"} for pid, rank, pos_rank in rows]}


LISTS = {
    fp.WEEKLY_OP["PPR"]: ecr(7, [("qb_a", 5, "QB1"), ("rb_c", 8, "RB1"), ("wr_e", 10, "WR1"), ("qb_fa", 20, "QB2"),
                                 ("qb_b", 30, "QB3"), ("rb_d", 45, "RB2"), ("te_g", 60, "TE1"),
                                 ("wr_fa", 70, "WR2"), ("wr_f", 80, "WR3")]),
    fp.WEEKLY_K: ecr(7, [("k_fa", 1, "K1"), ("k_1", 12, "K2")]),
    fp.WEEKLY_DST: ecr(7, [("DET", 3, "DST1")]),
    fp.ROS_K: ecr(0, [("k_fa", 20, "K20"), ("k_1", 15, "K15")]),
    fp.ROS_DST: ecr(0, [("DET", 3, "DST3")]),
    fp.ROS_OVERALL["PPR"]: ecr(0, [("rb_c", 5, "RB1"), ("wr_e", 9, "WR1"), ("rb_d", 60, "RB2"), ("qb_a", 70, "QB1"),
                                   ("te_g", 90, "TE1"), ("qb_fa", 100, "QB2"), ("wr_fa", 150, "WR2"),
                                   ("qb_b", 200, "QB3"), ("wr_f", 300, "WR3")]),
}


class FakeWrite:
    def __init__(self):
        self.calls = []

    def pending_waivers(self, league_id):
        return []

    def set_starters(self, *args):
        self.calls.append(("starters", *args))

    def submit_waiver_claim(self, *args):
        self.calls.append(("claim", *args))


class FakeSession:
    def __init__(self, roster):
        self.now, self.state, self.players = NOW, {"week": 7}, PLAYERS
        self.write = FakeWrite()
        self.read = type("R", (), {"rosters": lambda _, lid: [roster, {"roster_id": 2, "owner_id": "x",
                                                                        "players": ["wr_x"]}],
                                   "matchups": lambda _, lid, week: []})()
        idmap = IdMap(PLAYERS, {pid: pid for pid in PLAYERS})
        self.lists = {slug: RankList(data, idmap, NOW) for slug, data in LISTS.items()}

    def ranks(self, slug):
        return self.lists[slug]


LEAGUE = {"league_id": "L", "name": "Test", "status": "in_season",
          "roster_positions": ["QB", "RB", "WR", "TE", "SUPER_FLEX", "K", "DEF", "BN", "BN"],
          "scoring_settings": {"rec": 1}, "settings": {"waiver_type": 2, "waiver_budget": 100}}


class EngineTest(unittest.TestCase):
    def run_league(self, **cfg):
        roster = {"roster_id": 1, "owner_id": "me", "settings": {"waiver_budget_used": 0},
                  "players": ["qb_a", "qb_b", "rb_c", "rb_d", "wr_e", "wr_f", "te_g", "k_1", "DET"],
                  # Bad lineup: injured WR starts, RB in SUPER_FLEX while a QB sits.
                  "starters": ["qb_a", "rb_c", "wr_f", "te_g", "rb_d", "k_1", "DET"]}
        session = FakeSession(roster)
        league = League(session, LEAGUE, "me", {**DEFAULTS, "auto_waivers": True, **cfg})
        lines = league.run("all", apply=True, redact=False)
        return session.write.calls, "\n".join(lines), league

    def test_full_run(self):
        calls, report, league = self.run_league(min_roster={"WR": 1})
        self.assertEqual(league.errors, 0, report)
        self.assertEqual(calls[0], ("starters", "L", 1, ["qb_a", "rb_c", "wr_e", "te_g", "qb_b", "k_1", "DET"], 7, None))
        claims = [c[3:] for c in calls if c[0] == "claim"]
        # qb_fa is a superflex-valued upgrade; both QBs we have start (protected),
        # so the weakest droppable player (injured wr_f) goes. K streamed at min bid.
        self.assertIn(("qb_fa", "wr_f", 25), claims)
        self.assertIn(("k_fa", "k_1", 0), claims)
        self.assertIn("superflex", report)

    def test_pending_claims_count_toward_weekly_limit(self):
        roster = {"roster_id": 1, "owner_id": "me", "settings": {"waiver_budget_used": 0},
                  "players": ["qb_a", "qb_b", "rb_c", "rb_d", "wr_e", "wr_f", "te_g", "k_1", "DET"],
                  "starters": ["qb_a", "rb_c", "wr_f", "te_g", "rb_d", "k_1", "DET"]}
        session = FakeSession(roster)
        session.write.pending_waivers = lambda lid: [{"roster_ids": [1], "adds": {"wr_fa": 1}, "drops": {}},
                                                     {"roster_ids": [1], "adds": {"qb_fa": 1}, "drops": {}}]
        league = League(session, LEAGUE, "me", {**DEFAULTS, "auto_waivers": True, "min_roster": {"WR": 1}})
        report = "\n".join(league.run("waivers", apply=True, redact=False))
        self.assertEqual([c for c in session.write.calls if c[0] == "claim" and c[3] in ("qb_fa", "wr_fa")], [])
        self.assertIn("already pending", report)

    def test_star_kicker_on_bye_gets_streamer_for_a_spare_bench_player(self):
        k_row = LISTS[fp.WEEKLY_K]["players"][1]
        wr_row = next(r for r in LISTS[fp.ROS_OVERALL["PPR"]]["players"] if r["player_id"] == "wr_f")
        LISTS[fp.ROS_K]["players"][1]["pos_rank"], k_row["player_bye_week"], wr_row["pos_rank"] = "K2", "7", "WR40"
        try:
            calls, report, _ = self.run_league(min_roster={"WR": 1}, max_claims=0)
        finally:
            LISTS[fp.ROS_K]["players"][1]["pos_rank"], k_row["player_bye_week"], wr_row["pos_rank"] = "K15", "14", "WR3"
        self.assertIn(("k_fa", "wr_f", 0), [c[3:] for c in calls if c[0] == "claim"])
        self.assertIn("too good to drop", report)

    def test_keeps_top12_kicker_instead_of_streaming(self):
        LISTS[fp.ROS_K]["players"][1]["pos_rank"] = "K2"   # k_1 is now an elite kicker
        try:
            calls, report, league = self.run_league(min_roster={"WR": 1})
        finally:
            LISTS[fp.ROS_K]["players"][1]["pos_rank"] = "K15"
        self.assertNotIn("k_fa", [c[3] for c in calls if c[0] == "claim"])
        self.assertIn("Keeping k_1", report)

    def test_default_minimums_count_only_healthy_players(self):
        calls, report, _ = self.run_league()
        drops = [c[4] for c in calls if c[0] == "claim"]
        # wr_f is Out, so cutting him costs no healthy WR depth; the healthy rb_d/wr_e stay.
        self.assertIn("wr_f", drops)
        self.assertNotIn("wr_e", drops)
        self.assertNotIn("rb_d", drops)

    def test_dry_run_writes_nothing(self):
        roster_session = FakeSession({"roster_id": 1, "owner_id": "me", "players": ["qb_a"], "starters": []})
        League(roster_session, LEAGUE, "me", dict(DEFAULTS)).run("all", apply=False, redact=False)
        self.assertEqual(roster_session.write.calls, [])


if __name__ == "__main__":
    unittest.main()


class SetStartersTest(unittest.TestCase):
    """The lineup must land in the right week, and a silent no-op must be an error."""

    def make(self, echo_leg=True, echo_roster=True):
        from autopilot.sleeper import SleeperWrite
        sent = []

        class W(SleeperWrite):
            def _gql(self, query, variables):
                sent.append((query.split("(")[0].split()[-1], variables))
                starters = variables["starters"] if echo_leg else ["old"]
                if "update_matchup_leg" in query:
                    return {"update_matchup_leg": {"leg": variables["leg"], "round": variables["round"],
                                                   "starters": starters}}
                return {"roster_update_starters": {"starters": variables["starters"] if echo_roster else ["old"]}}
        return W("t"), sent

    def test_writes_the_weeks_leg_and_the_roster_only_when_current(self):
        w, sent = self.make()
        w.set_starters("L", 1, ["a", "b"], 8, 7)          # league still on week 7 (Tuesday)
        self.assertEqual([(n, v.get("leg"), v.get("round")) for n, v in sent], [("update_matchup_leg", 8, 8)])
        sent.clear()
        w.set_starters("L", 1, ["a", "b"], 8, 8)          # league on week 8 (game days)
        self.assertEqual([n for n, _ in sent], ["update_matchup_leg", "roster_update_starters"])

    def test_silent_no_op_is_an_error(self):
        w, _ = self.make(echo_leg=False)
        with self.assertRaises(RuntimeError):
            w.set_starters("L", 1, ["a", "b"], 8, 7)
