"""Turn FantasyPros ECR lists into lookups keyed by Sleeper player id."""

import csv
import io
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .net import request

# Community-maintained cross-site player id table (fantasypros_id <-> sleeper_id).
DP_IDS_URL = "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv"
TEAM_ALIASES = {"JAC": "JAX", "WSH": "WAS", "LVR": "LV", "OAK": "LV", "LA": "LAR", "STL": "LAR", "SD": "LAC"}
_SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")


def norm_team(team):
    team = (team or "").upper()
    return TEAM_ALIASES.get(team, team)


def norm_name(name):
    name = (name or "").lower().replace(".", "").replace("'", "")
    name = _SUFFIX.sub("", name)
    return re.sub(r"[^a-z]", "", name)


def load_fp_to_sleeper(cache_dir):
    path = Path(cache_dir) / "db_playerids.csv"
    if not path.exists() or time.time() - path.stat().st_mtime > 24 * 3600:
        text = request(DP_IDS_URL, timeout=60)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    rows = csv.DictReader(io.StringIO(path.read_text()))
    return {r["fantasypros_id"]: r["sleeper_id"] for r in rows
            if r["fantasypros_id"] not in ("", "NA") and r["sleeper_id"] not in ("", "NA")}


class IdMap:
    def __init__(self, sleeper_players, fp_to_sleeper):
        self.players = sleeper_players
        self.fp_to_sleeper = fp_to_sleeper
        self.by_name = defaultdict(list)
        for pid, p in sleeper_players.items():
            name = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}"
            for pos in p.get("fantasy_positions") or [p.get("position")]:
                self.by_name[(norm_name(name), pos)].append(pid)

    def sleeper_id(self, fp):
        pos = fp["player_position_id"]
        if pos == "DST":
            team = norm_team(fp.get("player_team_id"))
            return team if team in self.players else None
        sid = self.fp_to_sleeper.get(str(fp["player_id"]))
        if sid in self.players:
            return sid
        cands = self.by_name.get((norm_name(fp["player_name"]), pos), [])
        if len(cands) > 1:
            team = norm_team(fp.get("player_team_id"))
            cands = [c for c in cands if self.players[c].get("team") == team] or cands
        return cands[0] if len(cands) == 1 else None


@dataclass
class Rank:
    rank: int
    pos_rank: str
    name: str
    team: str
    bye: bool
    kickoff: int | None
    started: bool


class RankList:
    """One ECR list (e.g. weekly PPR superflex), indexed by Sleeper id."""

    def __init__(self, ecr, idmap, now=None):
        now = time.time() if now is None else now
        self.week = int(ecr.get("week") or 0)
        self.label = ecr.get("type", "?")
        self.by_id = {}
        self.unmatched = []
        self.team_kickoff = {}
        for p in ecr["players"]:
            kickoff = p.get("player_game_kickoff_ts")
            team = norm_team(p.get("player_team_id"))
            if kickoff:
                self.team_kickoff[team] = kickoff
            sid = idmap.sleeper_id(p)
            if not sid:
                self.unmatched.append(p["player_name"])
                continue
            bye = bool(self.week) and (str(p.get("player_bye_week")) == str(self.week)
                                       or (p.get("player_opponent") == "" and not kickoff))
            started = bool(kickoff and kickoff <= now) or p.get("player_game_status") in ("inprogress", "closed")
            if sid not in self.by_id:  # first (best) entry wins on rare duplicates
                self.by_id[sid] = Rank(int(p["rank_ecr"]), p.get("pos_rank") or "", p["player_name"],
                                       team, bye, kickoff, started)

    def get(self, sid):
        return self.by_id.get(sid)

    def first_kickoff(self):
        times = [t for t in self.team_kickoff.values() if t]
        return min(times) if times else None
