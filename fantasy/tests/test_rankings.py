import json
import unittest

from autopilot.engine import superflex_template, template_value
from autopilot.fantasypros import parse_ecr, scoring_format
from autopilot.rankings import IdMap, RankList

SLEEPER = {
    "9221": {"full_name": "Jahmyr Gibbs", "position": "RB", "fantasy_positions": ["RB"], "team": "DET"},
    "6804": {"full_name": "Jordan Love", "position": "QB", "fantasy_positions": ["QB"], "team": "GB"},
    "4984": {"full_name": "Josh Allen", "position": "QB", "fantasy_positions": ["QB"], "team": "BUF"},
    "777": {"full_name": "Marvin Harrison Jr.", "position": "WR", "fantasy_positions": ["WR"], "team": "ARI"},
    "JAX": {"first_name": "Jacksonville", "last_name": "Jaguars", "position": "DEF",
            "fantasy_positions": ["DEF"], "team": "JAX"},
}


def fp(pid, name, pos, team, rank, kickoff=None, bye="9", opp="vs. X", status="created"):
    return {"player_id": pid, "player_name": name, "player_position_id": pos, "player_team_id": team,
            "rank_ecr": rank, "pos_rank": f"{pos}{rank}", "player_bye_week": bye, "player_opponent": opp,
            "player_game_kickoff_ts": kickoff, "player_game_status": status}


ECR = {"week": "7", "type": "Weekly PPR", "players": [
    fp(22968, "Jahmyr Gibbs", "RB", "DET", 1, kickoff=1000, status="closed"),
    fp(19246, "Jordan Love", "QB", "GB", 2, kickoff=5000),
    fp(1, "Marvin Harrison", "WR", "ARI", 3, kickoff=5000),       # no id map entry -> name match
    fp(2, "Josh Allen", "QB", "BUF", 50, bye="7", opp=""),
    fp(3, "Jacksonville Jaguars", "DST", "JAC", 4, kickoff=6000),  # FP team code alias
]}


class RankingsTest(unittest.TestCase):
    def setUp(self):
        idmap = IdMap(SLEEPER, {"22968": "9221", "19246": "6804"})
        self.ranks = RankList(ECR, idmap, now=2000)

    def test_parse_embedded_json(self):
        html = f"<script>var ecrData = {json.dumps(ECR)};\nvar other = 1;</script>"
        self.assertEqual(parse_ecr(html)["week"], "7")

    def test_matching_flags_and_locks(self):
        r = self.ranks
        self.assertTrue(r.get("9221").started)          # game kicked off before `now`
        self.assertFalse(r.get("6804").started)
        self.assertEqual(r.get("777").rank, 3)           # "Marvin Harrison" ~ "Marvin Harrison Jr."
        self.assertTrue(r.get("4984").bye)
        self.assertEqual(r.get("JAX").rank, 4)
        self.assertEqual(r.unmatched, [])
        self.assertNotIn("BUF", r.team_kickoff)

    def test_superflex_template_skips_byes(self):
        tmpl = superflex_template(self.ranks, SLEEPER)
        self.assertEqual(tmpl["QB"], [2])  # Allen on bye isn't "QB2" this week
        self.assertEqual(template_value(tmpl, "QB", 1), 2)
        self.assertGreater(template_value(tmpl, "QB", 3), 2)

    def test_scoring_format(self):
        self.assertEqual(scoring_format({"rec": 1.0}), "PPR")
        self.assertEqual(scoring_format({"rec": 0.5}), "HALF")
        self.assertEqual(scoring_format({}), "STD")


if __name__ == "__main__":
    unittest.main()
