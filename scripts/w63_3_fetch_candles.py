#!/usr/bin/env python3
"""W63.3 Part B step 2: read-only demo-venue 1-minute candlestick GETs for every ticker in both books.

Window per ticker: [first entry - 10min, last entry + 4h]. Writes /tmp/w63_3_candles.json
({ticker: [candlestick, ...]}). Demo only. Run on the VPS after w63_3_fetch_orders.py.
"""
from __future__ import annotations
import json, os, sys, time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _ts(s: str) -> int:
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def main() -> int:
    if os.environ.get("BOT_ENV", "").lower() == "live":
        print("refusing BOT_ENV=live"); return 2
    os.environ["BOT_ENV"] = "paper"
    from prediction_market_bot import t4_fill_status as tf
    tf._load_dotenv_if_needed(REPO / ".env")
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    client = KalshiMarketClient.from_env()
    win: dict[str, list[int]] = {}
    for _b, (pf, _sc) in tf.BOOKS.items():
        for p in json.load(open(pf))["closed_positions"]:
            t = p["kalshi_ticker"]; e = _ts(p["entered_at"])
            lo, hi = win.get(t, [e, e]); win[t] = [min(lo, e), max(hi, e)]
    out, errs = {}, 0
    for i, (t, (lo, hi)) in enumerate(win.items()):
        series = t.split("-")[0]
        ok, d = client._get(f"/series/{series}/markets/{t}/candlesticks",
                            params={"start_ts": lo - 600, "end_ts": hi + 4 * 3600, "period_interval": 1}, authenticated=True)
        if ok and isinstance(d, dict):
            out[t] = d.get("candlesticks", [])
        else:
            errs += 1; out[t] = None
        time.sleep(0.12)
        if i % 300 == 0:
            print(i, len(win), "errs", errs, flush=True)
    Path("/tmp/w63_3_candles.json").write_text(json.dumps(out))
    print("tickers", len(out), "errs", errs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
