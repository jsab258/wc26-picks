"""FantasyPros Expert Consensus Rankings (ECR).

The rankings pages embed the full consensus as a ``var ecrData = {...}`` JSON
blob, which is what we read. If FANTASYPROS_COOKIE is set (copied from a logged
in browser session) it is sent along, so pages render with your account.
"""

import json
import os
import re

from .net import request

BASE = "https://www.fantasypros.com/nfl/rankings"

# FantasyPros page slugs per scoring format.
WEEKLY_OP = {"PPR": "ppr-superflex", "HALF": "half-point-ppr-superflex", "STD": "superflex"}
WEEKLY_FLEX = {"PPR": "ppr-flex", "HALF": "half-point-ppr-flex", "STD": "flex"}
WEEKLY_QB, WEEKLY_K, WEEKLY_DST = "qb", "k", "dst"
ROS_OVERALL = {"PPR": "ros-ppr-overall", "HALF": "ros-half-point-ppr-overall", "STD": "ros-overall"}

_ECR_START = re.compile(r"var\s+ecrData\s*=\s*")
_cache = {}


def parse_ecr(html):
    m = _ECR_START.search(html)
    if not m:
        raise ValueError("ecrData not found on page (layout changed or login wall?)")
    data, _ = json.JSONDecoder().raw_decode(html, m.end())
    return data


def fetch(slug):
    if slug not in _cache:
        headers = {}
        cookie = os.environ.get("FANTASYPROS_COOKIE", "").strip()
        if cookie:
            headers["Cookie"] = cookie
        html = request(f"{BASE}/{slug}.php", headers=headers, timeout=60)
        _cache[slug] = parse_ecr(html)
    return _cache[slug]


def scoring_format(scoring_settings):
    """Map a Sleeper league's points-per-reception to the nearest ECR format."""
    rec = float(scoring_settings.get("rec", 0) or 0)
    if rec >= 0.75:
        return "PPR"
    if rec >= 0.25:
        return "HALF"
    return "STD"
