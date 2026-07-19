# wc26-picks

Two static phone-friendly dashboards, served via GitHub Pages:

- **`index.html`** — WC26 picks (live odds, EV-max engine).
- **`btc.html`** — BTC crowd-sentiment & price-target tracker.

## BTC crowd-sentiment tracker

Automates the "fade the herd" read: (a) how bullish/bearish is the crowd right
now vs. its own recent baseline, and (b) what price is the crowd anchored on
("everyone waiting for $40k").

**How it works**

- `.github/workflows/btc-sentiment.yml` runs every 6 hours (plus on-demand via
  *Actions → BTC sentiment tracker → Run workflow*). It refreshes the weekly
  backtest (`scripts/btc_backtest.py`), then takes a live snapshot
  (`scripts/btc_sentiment.py`).
- Live sources (every failure degrades gracefully — a snapshot is always
  written):
  - **Twitter/X** via [twitterapi.io](https://twitterapi.io) — needs a
    `TWITTERAPI_KEY` repo secret. ~400 recent BTC tweets per run
    (`min_faves:5`, no retweets), engagement-weighted by log-likes so loud
    accounts count more. ≈$7/mo at 4 runs/day. Without the secret the tracker
    runs StockTwits-only.
  - **StockTwits BTC.X** (free; posters self-label Bullish/Bearish).
  - **alternative.me Fear & Greed index** (free).
  - BTC spot (CoinGecko → Coinbase → blockchain.info).
  - **Polymarket** BTC price markets — real-money YES probabilities.
  - **Deribit options skew** — put IV minus call IV at ~±10% strikes ~30 days
    out; positive = traders paying up for crash protection.
- `scripts/btc_backtest.py` (weekly): full Fear & Greed history since 2018 +
  Coinbase daily candles → median forward BTC returns 30/90/180 days after
  extreme-fear/greed days vs. baseline, shown on the dashboard so the
  contrarian premise is checkable against history.
- Explicit price targets (`$40k`, `45,000`, `$38000`…) are regex-extracted
  from post text and bucketed into a histogram vs. spot.
- Unlabeled posts are classified bullish/bearish/neutral:
  - **With an `ANTHROPIC_API_KEY` repo secret**: Claude classifies them (and
    extracts implied targets). Model defaults to `claude-haiku-4-5`
    (override with a `BTC_SENTIMENT_MODEL` env var in the workflow) — a few
    hundred short posts per run costs well under a cent.
  - **Without a key**: a keyword lexicon (free, cruder — misses sarcasm).
- Aggregates append to `data/history.json`; `data/latest.json` carries the
  current snapshot + target list. `btc.html` renders both.
- The **contrarian meter** computes a z-score of the current bearish share vs.
  the trailing 30 days. `z ≥ 1.5` with bears > bulls flags a
  *contrarian-bullish* extreme (and the mirror image for tops). It reports
  "calibrating" until ~8 snapshots (≈2 days) exist.

**Setup notes**

- The cron only fires on the **default branch** — merge to `main` to activate.
  Until then, use the manual *Run workflow* button on this branch.
- Optional: add `ANTHROPIC_API_KEY` under *Settings → Secrets and variables →
  Actions* for LLM classification.
- The workflow commits `data/*.json` back to the branch it runs on
  (`permissions: contents: write` is already declared).
