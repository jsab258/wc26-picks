"""Sleeper clients.

Reads use the documented public REST API (https://docs.sleeper.com, no auth).
Writes use the private GraphQL endpoint the Sleeper web app itself calls,
authenticated with your session token. That endpoint is undocumented and
unsupported: it can change without notice, and automated use may conflict with
Sleeper's terms. Everything that writes is opt-in (``--apply``).
"""

import base64
import json
import os
import time
from pathlib import Path

from .net import HttpError, get_json, post_json

REST = "https://api.sleeper.app/v1"
GRAPHQL = "https://api.sleeper.app/graphql"
PLAYERS_MAX_AGE = 3 * 3600  # fresh enough for game-day injury news, still light on Sleeper


class SleeperRead:
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)

    def state(self):
        return get_json(f"{REST}/state/nfl")

    def user(self, username):
        user = get_json(f"{REST}/user/{username}")
        if not user:
            raise SystemExit(f"Sleeper user '{username}' not found")
        return user

    def leagues(self, user_id, season):
        return get_json(f"{REST}/user/{user_id}/leagues/nfl/{season}") or []

    def league(self, league_id):
        return get_json(f"{REST}/league/{league_id}")

    # Rosters and lineups go through Sleeper's CDN and can be minutes stale; the
    # throwaway query parameter fetches the current state.
    def rosters(self, league_id):
        return get_json(f"{REST}/league/{league_id}/rosters?_={int(time.time() * 1000)}")

    def matchups(self, league_id, week):
        return get_json(f"{REST}/league/{league_id}/matchups/{week}?_={int(time.time() * 1000)}") or []

    def players(self):
        path = self.cache_dir / "sleeper_players_nfl.json"
        if path.exists() and time.time() - path.stat().st_mtime < PLAYERS_MAX_AGE:
            return json.loads(path.read_text())
        data = get_json(f"{REST}/players/nfl", timeout=120)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return data


def token_claims(token):
    """Decode (without verifying) the JWT payload, for sanity checks only."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except (IndexError, ValueError):
        return {}


class SleeperWrite:
    def __init__(self, token):
        self.token = token.strip()

    @classmethod
    def from_env(cls):
        token = os.environ.get("SLEEPER_TOKEN", "").strip()
        return cls(token) if token else None

    def _gql(self, query, variables):
        try:
            resp = post_json(GRAPHQL, {"query": query, "variables": variables},
                             headers={"Authorization": self.token}, retries=1)
        except HttpError as e:
            raise RuntimeError(f"Sleeper GraphQL HTTP {e.status}: {e.body[:300]}") from None
        if resp.get("errors"):
            msgs = "; ".join(err.get("message", str(err)) for err in resp["errors"])
            raise RuntimeError(f"Sleeper rejected the request: {msgs}")
        return resp["data"]

    def set_starters(self, league_id, roster_id, starters, week, league_leg):
        """Save the lineup for NFL ``week``.

        Sleeper keeps a lineup per week ("matchup leg"). roster_update_starters only
        covers the league's current leg, which lags a day behind (it advances when
        waivers run) and otherwise silently keeps the old lineup. So write the
        week's leg, also the roster when the league is on that week, and verify.
        """
        q = """mutation update_matchup_leg($leagueId: String!, $rosterId: Int!, $round: Int!, $leg: Int!,
  $starters: [String]) {
  update_matchup_leg(league_id: $leagueId, roster_id: $rosterId, round: $round, leg: $leg, starters: $starters) {
    leg round starters
  }
}"""
        leg = self._gql(q, {"leagueId": league_id, "rosterId": roster_id, "round": week, "leg": week,
                            "starters": starters})["update_matchup_leg"]
        if not leg or leg.get("starters") != starters:
            raise RuntimeError(f"Sleeper didn't accept the week {week} lineup")
        if int(league_leg or 0) == int(week):
            rq = """mutation roster_update_starters($leagueId: String!, $rosterId: Int!, $starters: [String]) {
  roster_update_starters(league_id: $leagueId, roster_id: $rosterId, starters: $starters) {
    roster_id starters
  }
}"""
            roster = self._gql(rq, {"leagueId": league_id, "rosterId": roster_id,
                                    "starters": starters})["roster_update_starters"]
            if not roster or roster.get("starters") != starters:
                raise RuntimeError("Sleeper didn't accept the lineup")
        return leg

    def submit_waiver_claim(self, league_id, roster_id, add, drop=None, bid=None):
        q = """mutation submit_waiver_claim($leagueId: String!, $k_adds: [String], $v_adds: [Int],
  $k_drops: [String], $v_drops: [Int], $k_settings: [String], $v_settings: [Int]) {
  submit_waiver_claim(league_id: $leagueId, k_adds: $k_adds, v_adds: $v_adds,
    k_drops: $k_drops, v_drops: $v_drops, k_settings: $k_settings, v_settings: $v_settings) {
    transaction_id type status leg adds drops roster_ids
  }
}"""
        variables = {
            "leagueId": league_id,
            "k_adds": [add], "v_adds": [roster_id],
            "k_drops": [drop] if drop else [], "v_drops": [roster_id] if drop else [],
        }
        if bid is not None:
            variables["k_settings"] = ["waiver_bid"]
            variables["v_settings"] = [int(bid)]
        return self._gql(q, variables)["submit_waiver_claim"]

    def pending_waivers(self, league_id):
        q = """query league_transactions_filtered($leagueId: String!, $rosterIdFilters: [Int],
  $typeFilters: [String], $legFilters: [Int], $statusFilters: [String], $limit: Int) {
  league_transactions_filtered(league_id: $leagueId, roster_id_filters: $rosterIdFilters,
    type_filters: $typeFilters, leg_filters: $legFilters, status_filters: $statusFilters, limit: $limit) {
    transaction_id type status creator roster_ids adds drops settings
  }
}"""
        data = self._gql(q, {"leagueId": league_id, "rosterIdFilters": [], "typeFilters": ["waiver"],
                             "legFilters": [], "statusFilters": ["pending"], "limit": 100})
        return data["league_transactions_filtered"] or []
