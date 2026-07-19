#!/usr/bin/env python3
"""BTC crowd-sentiment & price-target tracker.

Sources per snapshot (each optional — any failure degrades gracefully):
  - Twitter/X via twitterapi.io   (needs TWITTERAPI_KEY; ~$0.15/1k tweets)
  - StockTwits BTC.X              (free; posters self-label Bullish/Bearish)
  - alternative.me Fear & Greed   (free)
  - BTC spot                      (CoinGecko -> Coinbase -> blockchain.info)
  - Polymarket BTC price markets  (free; real-money probabilities)
  - Deribit options skew proxy    (free; put IV - call IV at ~±10%, ~30d out)

Explicit price targets ($40k, 45,000, ...) are regex-extracted from post text.
Posts without a self-label are classified bullish/bearish/neutral by Claude
(if ANTHROPIC_API_KEY is set) or a keyword lexicon. Sentiment shares are
engagement-weighted (log of likes) so loud accounts count more.

Appends a snapshot to data/history.json and writes data/latest.json.
stdlib-only unless the optional `anthropic` package + API key are present.
"""

import json
import math
import os
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

MIN_TARGET, MAX_TARGET = 10_000, 500_000
HISTORY_CAP = 4000
Z_MIN_SNAPSHOTS = 8
Z_WINDOW_DAYS = 30
MAX_TWEETS = 400          # per run; ~4 runs/day => ~48k tweets/mo ≈ $7/mo
TWEET_QUERY = '(bitcoin OR btc OR $BTC) lang:en -filter:retweets min_faves:5'


def fetch_json(url, headers=None, timeout=25):
    hdrs = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def try_fetch(url, label, headers=None):
    try:
        return fetch_json(url, headers=headers)
    except Exception as e:  # noqa: BLE001 - any source may be flaky; never abort the run
        print(f"[warn] {label} failed: {e}", file=sys.stderr)
        return None


def first_num(d, *keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str) and v.replace(".", "", 1).isdigit():
            return float(v)
    return 0


# ---------------------------------------------------------------- sources

def get_spot():
    d = try_fetch(
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
        "coingecko",
    )
    if d and "bitcoin" in d:
        return float(d["bitcoin"]["usd"]), d["bitcoin"].get("usd_24h_change")
    d = try_fetch("https://api.coinbase.com/v2/prices/BTC-USD/spot", "coinbase")
    if d and "data" in d:
        return float(d["data"]["amount"]), None
    d = try_fetch("https://blockchain.info/ticker", "blockchain.info")
    if d and "USD" in d:
        return float(d["USD"]["last"]), None
    return None, None


def get_fear_greed():
    d = try_fetch("https://api.alternative.me/fng/?limit=1", "fear&greed")
    if d and d.get("data"):
        e = d["data"][0]
        return int(e["value"]), e["value_classification"]
    return None, None


def get_tweets(max_tweets=MAX_TWEETS):
    """Recent BTC tweets via twitterapi.io advanced search (X-API-Key auth)."""
    key = os.environ.get("TWITTERAPI_KEY")
    if not key:
        return []
    posts, cursor = [], None
    base = ("https://api.twitterapi.io/twitter/tweet/advanced_search"
            "?queryType=Latest&query=" + urllib.parse.quote(TWEET_QUERY))
    for _ in range(40):  # hard cap on requests
        url = base + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else "")
        d = try_fetch(url, "twitterapi", headers={"X-API-Key": key})
        if not d:
            break
        tweets = d.get("tweets") or d.get("data") or []
        if not tweets:
            break
        for t in tweets:
            likes = first_num(t, "likeCount", "favorite_count", "favoriteCount")
            posts.append({
                "text": (t.get("text") or "")[:500],
                "label": None,
                "source": "twitter",
                "weight": 1 + math.log10(1 + likes),
            })
        if len(posts) >= max_tweets or not d.get("has_next_page"):
            break
        cursor = d.get("next_cursor")
        if not cursor:
            break
    return posts[:max_tweets]


def get_stocktwits(max_pages=5):
    """StockTwits BTC.X stream: users self-label posts Bullish/Bearish."""
    posts, max_id = [], None
    for _ in range(max_pages):
        url = "https://api.stocktwits.com/api/2/streams/symbol/BTC.X.json?limit=30"
        if max_id:
            url += f"&max={max_id}"
        d = try_fetch(url, "stocktwits")
        if not d or "messages" not in d:
            break
        for m in d["messages"]:
            sent = None
            ent = m.get("entities") or {}
            if isinstance(ent.get("sentiment"), dict):
                basic = ent["sentiment"].get("basic")
                if basic == "Bullish":
                    sent = "bull"
                elif basic == "Bearish":
                    sent = "bear"
            likes = first_num(m.get("likes") or {}, "total")
            posts.append({
                "text": (m.get("body") or "")[:500],
                "label": sent,  # None => needs classification
                "source": "stocktwits",
                "weight": 1 + math.log10(1 + likes),
            })
        cursor = d.get("cursor") or {}
        if not cursor.get("more"):
            break
        max_id = cursor.get("max")
    return posts


def get_polymarket(limit=10):
    """Open Polymarket BTC price markets with real-money YES probabilities."""
    d = try_fetch("https://gamma-api.polymarket.com/events"
                  "?tag_slug=bitcoin&closed=false&limit=60", "polymarket")
    if not isinstance(d, list):
        return []
    out = []
    for ev in d:
        for m in ev.get("markets") or []:
            q = m.get("question") or ev.get("title") or ""
            if not re.search(r"\b(bitcoin|btc)\b", q, re.I):
                continue
            if not re.search(r"\$\s?\d|\d+\s*[kK]\b", q):
                continue  # only price-level markets
            try:
                prices = m.get("outcomePrices")
                if isinstance(prices, str):
                    prices = json.loads(prices)
                yes = round(100 * float(prices[0]), 1)
            except Exception:  # noqa: BLE001
                continue
            vol = first_num(m, "volumeNum", "volume")
            out.append({"q": q.strip()[:120], "yes": yes, "vol": round(vol)})
    out.sort(key=lambda x: -x["vol"])
    return out[:limit]


def get_deribit_skew(spot):
    """Downside-fear proxy: put IV minus call IV at ~±10% strikes, ~30d expiry.

    Positive = traders pay more for crash protection than for upside.
    """
    if not spot:
        return None
    d = try_fetch("https://www.deribit.com/api/v2/public/"
                  "get_book_summary_by_currency?currency=BTC&kind=option", "deribit")
    if not d or "result" not in d:
        return None
    now = datetime.now(timezone.utc)
    by_expiry = {}
    for o in d["result"]:
        try:
            _, exp_s, strike_s, cp = o["instrument_name"].split("-")
            exp = datetime.strptime(exp_s, "%d%b%y").replace(tzinfo=timezone.utc)
            iv = o.get("mark_iv")
            if iv is None:
                continue
            by_expiry.setdefault(exp, []).append((float(strike_s), cp, float(iv)))
        except Exception:  # noqa: BLE001 - skip malformed instruments
            continue
    candidates = [e for e in by_expiry if 20 <= (e - now).days <= 45]
    if not candidates:
        return None
    exp = min(candidates, key=lambda e: abs((e - now).days - 30))
    opts = by_expiry[exp]
    puts = [(abs(k - spot * 0.9), iv) for k, cp, iv in opts if cp == "P"]
    calls = [(abs(k - spot * 1.1), iv) for k, cp, iv in opts if cp == "C"]
    if not puts or not calls:
        return None
    put_iv = min(puts)[1]
    call_iv = min(calls)[1]
    return {
        "skew": round(put_iv - call_iv, 1),
        "put_iv": round(put_iv, 1),
        "call_iv": round(call_iv, 1),
        "expiry": exp.date().isoformat(),
        "dte": (exp - now).days,
    }


# ------------------------------------------------------- target extraction

TARGET_PATTERNS = [
    re.compile(r"\$\s?(\d{1,3}(?:,\d{3})+)"),          # $40,000
    re.compile(r"\$?\s?(\d{2,3})(?:\.\d)?\s*[kK]\b"),  # 40k / $45K / 42.5k
    re.compile(r"\$\s?(\d{4,6})\b"),                   # $40000
]


def extract_targets(text):
    found = set()
    for pat in TARGET_PATTERNS:
        for m in pat.finditer(text):
            raw = m.group(1).replace(",", "")
            try:
                v = float(raw)
            except ValueError:
                continue
            if "k" in m.group(0).lower():
                v *= 1000
            if MIN_TARGET <= v <= MAX_TARGET:
                found.add(round(v))
    return sorted(found)


# ---------------------------------------------------------- classification

BULL_WORDS = ("bullish|moon|mooning|pump|pumping|long|longing|buy|buying|bought|"
              "accumulate|accumulating|bottomed|breakout|undervalued|higher|rip|"
              "ripping|calls|dca|hodl|dip.buy")
BEAR_WORDS = ("bearish|dump|dumping|short|shorting|sell|selling|sold|crash|"
              "crashing|capitulation|rekt|lower|bleed|bleeding|puts|overvalued|"
              "dead.cat|rug|bubble|ponzi")
BULL_RE = re.compile(rf"\b(?:{BULL_WORDS})\b", re.I)
BEAR_RE = re.compile(rf"\b(?:{BEAR_WORDS})\b", re.I)


def classify_rules(text):
    score = len(BULL_RE.findall(text)) - len(BEAR_RE.findall(text))
    return "bull" if score > 0 else "bear" if score < 0 else "neutral"


LLM_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "i": {"type": "integer"},
                    "s": {"type": "string", "enum": ["bull", "bear", "neutral"]},
                    "t": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                },
                "required": ["i", "s", "t"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}

LLM_SYSTEM = (
    "You classify short social-media posts about Bitcoin. For each post decide "
    "the author's stance on BTC price direction: 'bull' (expects up / buying), "
    "'bear' (expects down / selling or waiting for lower), or 'neutral' "
    "(unclear, joke, question, or off-topic). Sarcasm counts for its intended "
    "meaning. If the post states an explicit numeric BTC price target or "
    "expectation in USD, return it as 't' (e.g. 'waiting for 40k' -> 40000); "
    "otherwise t is null."
)


def classify_llm(posts, model):
    """Classify posts lacking a self-label. Returns True if the LLM was used."""
    try:
        import anthropic  # noqa: PLC0415 - optional dependency
    except ImportError:
        return False
    client = anthropic.Anthropic()
    pending = [(i, p) for i, p in enumerate(posts) if p["label"] is None]
    for start in range(0, len(pending), 40):
        chunk = pending[start:start + 40]
        payload = [{"i": i, "text": p["text"][:240]} for i, p in chunk]
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=8000,
                system=LLM_SYSTEM,
                output_config={"format": {"type": "json_schema", "schema": LLM_SCHEMA}},
                messages=[{"role": "user", "content": json.dumps(payload)}],
            )
            text = next(b.text for b in resp.content if b.type == "text")
            for item in json.loads(text)["items"]:
                idx = item["i"]
                if 0 <= idx < len(posts) and posts[idx]["label"] is None:
                    posts[idx]["label"] = item["s"]
                    t = item.get("t")
                    if t and MIN_TARGET <= t <= MAX_TARGET:
                        posts[idx]["llm_target"] = round(t)
        except Exception as e:  # noqa: BLE001 - degrade to rules, never abort
            print(f"[warn] LLM classification chunk failed: {e}", file=sys.stderr)
            return False
    return True


# -------------------------------------------------------------- aggregate

def bear_z_score(history, now, bear_pct):
    cutoff = (now - timedelta(days=Z_WINDOW_DAYS)).isoformat()
    prior = [s["bear_pct"] for s in history
             if s.get("bear_pct") is not None and s["ts"] >= cutoff]
    if len(prior) < Z_MIN_SNAPSHOTS:
        return None
    mean = statistics.mean(prior)
    sd = statistics.pstdev(prior)
    if sd < 1e-9:
        return None
    return round((bear_pct - mean) / sd, 2)


def make_signal(bear_z, bull_pct, bear_pct, fng, anchored_below):
    if bear_z is None:
        return "calibrating"
    if bear_z >= 1.5 and bear_pct > bull_pct:
        return "crowd_bearish_extreme"
    if bear_z <= -1.5 and bull_pct > bear_pct:
        return "crowd_bullish_extreme"
    if bear_pct > bull_pct + 10 or (fng is not None and fng <= 25) or anchored_below:
        return "leaning_bearish"
    if bull_pct > bear_pct + 10 or (fng is not None and fng >= 75):
        return "leaning_bullish"
    return "neutral"


def main():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    spot, spot_chg = get_spot()
    fng, fng_label = get_fear_greed()
    posts = get_tweets() + get_stocktwits()
    polymarket = get_polymarket()
    skew = get_deribit_skew(spot)
    sources = {}
    for p in posts:
        sources[p["source"]] = sources.get(p["source"], 0) + 1
    print(f"spot={spot} fng={fng} posts={sources} "
          f"polymarket={len(polymarket)} skew={skew and skew['skew']}")

    method = "none"
    if posts:
        n_selflabeled = sum(1 for p in posts if p["label"] is not None)
        if os.environ.get("ANTHROPIC_API_KEY"):
            model = os.environ.get("BTC_SENTIMENT_MODEL", "claude-haiku-4-5")
            method = "llm" if classify_llm(posts, model) else "rules"
        else:
            method = "rules"
        for p in posts:
            if p["label"] is None:
                p["label"] = classify_rules(p["text"])
        print(f"self-labeled={n_selflabeled} method={method}")

    targets = []
    for p in posts:
        tv = extract_targets(p["text"])
        if "llm_target" in p:
            tv = sorted(set(tv) | {p["llm_target"]})
        targets.extend(tv)

    n = len(posts)
    wsum = {"bull": 0.0, "bear": 0.0, "neutral": 0.0}
    for p in posts:
        wsum[p["label"]] += p.get("weight", 1)
    total_w = sum(wsum.values())
    bull_pct = round(100 * wsum["bull"] / total_w, 1) if total_w else None
    bear_pct = round(100 * wsum["bear"] / total_w, 1) if total_w else None
    neutral_pct = max(0.0, round(100 - bull_pct - bear_pct, 1)) if total_w else None

    target_median = round(statistics.median(targets)) if targets else None
    below_spot_pct = (round(100 * sum(1 for t in targets if t < spot) / len(targets), 1)
                      if targets and spot else None)
    anchored_below = bool(target_median and spot and target_median <= spot * 0.9)

    DATA_DIR.mkdir(exist_ok=True)
    hist_path = DATA_DIR / "history.json"
    history = json.loads(hist_path.read_text()) if hist_path.exists() else []

    z = bear_z_score(history, now, bear_pct) if bear_pct is not None else None
    signal = (make_signal(z, bull_pct, bear_pct, fng, anchored_below)
              if bear_pct is not None else "no_data")

    snapshot = {
        "ts": now.isoformat(),
        "spot": round(spot, 2) if spot else None,
        "spot_change_24h": round(spot_chg, 2) if spot_chg is not None else None,
        "fng": fng,
        "fng_label": fng_label,
        "n_posts": n,
        "bull_pct": bull_pct,
        "bear_pct": bear_pct,
        "neutral_pct": neutral_pct,
        "n_targets": len(targets),
        "target_median": target_median,
        "targets_below_spot_pct": below_spot_pct,
        "anchored_below": anchored_below,
        "skew": skew["skew"] if skew else None,
        "bear_z": z,
        "signal": signal,
        "method": method,
    }
    history.append(snapshot)
    history = history[-HISTORY_CAP:]
    hist_path.write_text(json.dumps(history, indent=1) + "\n")

    latest = dict(snapshot)
    latest["targets"] = sorted(targets)[:300]
    latest["sources"] = sources
    latest["skew_detail"] = skew
    latest["polymarket"] = polymarket
    (DATA_DIR / "latest.json").write_text(json.dumps(latest, indent=1) + "\n")
    print(f"snapshot written: signal={signal} bull={bull_pct}% bear={bear_pct}% "
          f"targets={len(targets)} median={target_median}")


if __name__ == "__main__":
    main()
