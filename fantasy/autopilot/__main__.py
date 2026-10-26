"""CLI: python -m autopilot {lineup,waivers,all} [--apply]"""

import argparse
import os
import sys
import time
from pathlib import Path

from .config import load
from .engine import League, Session
from .sleeper import SleeperRead, SleeperWrite, token_claims

HERE = Path(__file__).resolve().parent.parent


def main(argv=None):
    ap = argparse.ArgumentParser(prog="autopilot", description=__doc__)
    ap.add_argument("task", choices=["lineup", "waivers", "all"])
    ap.add_argument("--apply", action="store_true",
                    help="submit changes to Sleeper (needs SLEEPER_TOKEN); default is a dry run")
    ap.add_argument("--config", default=HERE / "config.toml")
    ap.add_argument("--league", action="append", default=[], help="only this league id (repeatable)")
    ap.add_argument("--redact-waivers", action="store_true",
                    help="don't print claim details (for public CI logs)")
    ap.add_argument("--cache-dir", default=HERE / ".cache")
    args = ap.parse_args(argv)

    cfg = load(args.config)
    read = SleeperRead(args.cache_dir)
    write = SleeperWrite.from_env()
    if args.apply and not write:
        sys.exit("--apply needs the SLEEPER_TOKEN environment variable")

    session = Session(read, write, args.cache_dir)
    user = read.user(cfg.username)
    out = [f"## Sleeper autopilot · week {session.state['week']} · "
           f"{'APPLY' if args.apply else 'dry run'} · {args.task}"]
    if write:
        claims = token_claims(write.token)
        if claims.get("user_id") and str(claims["user_id"]) != str(user["user_id"]):
            sys.exit("SLEEPER_TOKEN belongs to a different Sleeper user than sleeper_username")
        if claims.get("exp") and claims["exp"] - time.time() < 14 * 86400:
            out.append(f"> ⚠️ SLEEPER_TOKEN expires {time.strftime('%Y-%m-%d', time.gmtime(claims['exp']))}; "
                       "grab a fresh one soon.")

    wanted = set(args.league) or set(cfg.leagues)
    leagues = [lg for lg in read.leagues(user["user_id"], session.state["league_season"])
               if not wanted or lg["league_id"] in wanted]
    if not leagues:
        out.append("No matching NFL leagues found for this season.")
    errors = 0
    for data in leagues:
        league = League(session, data, user["user_id"], cfg.for_league(data["league_id"]))
        out += league.run(args.task, apply=args.apply, redact=args.redact_waivers)
        out.append("")
        errors += league.errors

    text = "\n".join(out)
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(text + "\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
