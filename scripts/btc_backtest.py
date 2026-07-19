#!/usr/bin/env python3
"""Backtest: do Fear & Greed extremes mark BTC bottoms/tops?

Pulls the full alternative.me Fear & Greed history (since Feb 2018) and BTC-USD
daily candles from Coinbase, then computes forward returns 30/90/180 days after
days in each F&G bucket vs. the all-days baseline. Writes data/backtest.json.

Skips itself if the existing file is fresher than MAX_AGE_DAYS (override with
FORCE_BACKTEST=1). stdlib only.
"""

import json
import os
import statistics
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "backtest.json"
MAX_AGE_DAYS = 7
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

FWD_WINDOWS = (30, 90, 180)
BUCKETS = [
    ("fng<=10",  lambda v: v <= 10),
    ("fng<=20",  lambda v: v <= 20),
    ("fng<=25",  lambda v: v <= 25),
    ("fng>=75",  lambda v: v >= 75),
    ("fng>=85",  lambda v: v >= 85),
]


def fetch_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_fng_history():
    d = fetch_json("https://api.alternative.me/fng/?limit=0")
    out = {}
    for e in d["data"]:
        day = datetime.fromtimestamp(int(e["timestamp"]), tz=timezone.utc).date()
        out[day.isoformat()] = int(e["value"])
    return out


def get_daily_closes(start, end):
    """Coinbase Exchange daily candles, paginated (max 300 candles/request)."""
    closes = {}
    cur = start
    while cur < end:
        chunk_end = min(cur + timedelta(days=299), end)
        url = ("https://api.exchange.coinbase.com/products/BTC-USD/candles"
               f"?granularity=86400&start={cur.isoformat()}T00:00:00Z"
               f"&end={chunk_end.isoformat()}T00:00:00Z")
        try:
            rows = fetch_json(url)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] candles {cur}..{chunk_end} failed: {e}", file=sys.stderr)
            rows = []
        for r in rows:  # [time, low, high, open, close, volume]
            day = datetime.fromtimestamp(r[0], tz=timezone.utc).date()
            closes[day.isoformat()] = float(r[4])
        cur = chunk_end + timedelta(days=1)
    return closes


def fwd_stats(days, closes_by_date, dates_index, window):
    rets = []
    for d in days:
        i = dates_index.get(d)
        if i is None:
            continue
        j = i + window
        if j < len(ALL_DATES):
            d2 = ALL_DATES[j]
            if d2 in closes_by_date:
                rets.append(closes_by_date[d2] / closes_by_date[d] - 1)
    if not rets:
        return None
    return {
        "n": len(rets),
        "median": round(100 * statistics.median(rets), 1),
        "mean": round(100 * statistics.mean(rets), 1),
        "win": round(100 * sum(1 for r in rets if r > 0) / len(rets), 1),
    }


def find_episodes(rows, closes, dates_index, threshold=20, min_len=3):
    """Consecutive runs of F&G <= threshold, with the 90d return from the low."""
    episodes, run = [], []
    for d, v, _ in rows:
        if v <= threshold:
            run.append((d, v))
        else:
            if len(run) >= min_len:
                episodes.append(run)
            run = []
    if len(run) >= min_len:
        episodes.append(run)
    out = []
    for run in episodes:
        start, end = run[0][0], run[-1][0]
        min_fng = min(v for _, v in run)
        i = dates_index.get(end)
        ret90 = None
        if i is not None and i + 90 < len(ALL_DATES):
            d2 = ALL_DATES[i + 90]
            if d2 in closes and end in closes:
                ret90 = round(100 * (closes[d2] / closes[end] - 1), 1)
        out.append({"start": start, "end": end, "days": len(run),
                    "min_fng": min_fng, "ret_90d_after": ret90})
    return out[-12:]


ALL_DATES = []


def main():
    if OUT.exists() and not os.environ.get("FORCE_BACKTEST"):
        try:
            gen = json.loads(OUT.read_text()).get("generated", "")
            if gen and (datetime.now(timezone.utc)
                        - datetime.fromisoformat(gen)) < timedelta(days=MAX_AGE_DAYS):
                print("backtest fresh, skipping")
                return
        except Exception:  # noqa: BLE001 - malformed file => regenerate
            pass

    now = datetime.now(timezone.utc)
    fng = get_fng_history()
    start = datetime.fromisoformat(min(fng)).date()
    closes = get_daily_closes(start, now.date())
    print(f"fng days={len(fng)} price days={len(closes)}")

    rows = [(d, v, closes[d]) for d, v in sorted(fng.items()) if d in closes]
    if len(rows) < 500:
        print("[warn] insufficient overlap, not writing backtest", file=sys.stderr)
        return

    global ALL_DATES
    ALL_DATES = [d for d, _, _ in rows]
    dates_index = {d: i for i, d in enumerate(ALL_DATES)}
    closes_by_date = {d: c for d, _, c in rows}

    baseline = {str(w): fwd_stats(ALL_DATES, closes_by_date, dates_index, w)
                for w in FWD_WINDOWS}
    buckets = []
    for label, pred in BUCKETS:
        days = [d for d, v, _ in rows if pred(v)]
        buckets.append({
            "label": label,
            "n_days": len(days),
            "fwd": {str(w): fwd_stats(days, closes_by_date, dates_index, w)
                    for w in FWD_WINDOWS},
        })

    weekly = rows[::7]
    out = {
        "generated": now.replace(microsecond=0).isoformat(),
        "start": rows[0][0],
        "end": rows[-1][0],
        "n_days": len(rows),
        "baseline": baseline,
        "buckets": buckets,
        "episodes": find_episodes(rows, closes_by_date, dates_index),
        "series": {
            "dates": [d for d, _, _ in weekly],
            "fng": [v for _, v, _ in weekly],
            "close": [round(c, 2) for _, _, c in weekly],
        },
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out) + "\n")
    print(f"backtest written: {rows[0][0]}..{rows[-1][0]} ({len(rows)} days)")


if __name__ == "__main__":
    main()
