"""Load config.toml: global settings plus optional per-league overrides."""

import tomllib
from dataclasses import dataclass, field

DEFAULTS = {
    # Only consulted with --apply; a dry run never writes anything.
    "auto_lineup": True,
    "auto_waivers": False,
    # In SUPER_FLEX, a QB counts as this many ECR spots better than his rank.
    # ECR superflex ranks already favour QBs; this encodes "lean QB" on top.
    "superflex_qb_bonus": 10,
    # Sleeper injury designations we never start.
    "bench_statuses": ["Out", "IR", "PUP", "Sus", "Doubtful", "NA", "DNR", "COV"],
    "max_claims": 2,
    # A pickup must beat the player it replaces by this many ROS ECR spots.
    "min_gain": 20,
    # FAAB: [best-allowed value, share of remaining budget], first match wins.
    "faab_tiers": [[30, 0.25], [60, 0.15], [100, 0.08], [150, 0.04]],
    "stream_k_def": True,
    "stream_margin": 6,
    # Names or Sleeper ids the bot must never drop.
    "never_drop": [],
    # Override minimum players kept per position, e.g. {QB = 3}.
    "min_roster": {},
}


@dataclass
class Config:
    username: str
    leagues: list = field(default_factory=list)
    defaults: dict = field(default_factory=dict)
    overrides: dict = field(default_factory=dict)

    def for_league(self, league_id):
        merged = {**DEFAULTS, **self.defaults}
        merged.update(self.overrides.get(str(league_id), {}))
        return merged


def load(path):
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    username = raw.get("sleeper_username", "").strip()
    if not username or username.startswith("YOUR_"):
        raise SystemExit(f"Set sleeper_username in {path}")
    unknown = set(raw.get("defaults", {})) - set(DEFAULTS)
    for league_cfg in raw.get("league", {}).values():
        unknown |= set(league_cfg) - set(DEFAULTS)
    if unknown:
        raise SystemExit(f"Unknown config keys: {', '.join(sorted(unknown))}")
    return Config(username, [str(x) for x in raw.get("leagues", [])],
                  raw.get("defaults", {}), {str(k): v for k, v in raw.get("league", {}).items()})
