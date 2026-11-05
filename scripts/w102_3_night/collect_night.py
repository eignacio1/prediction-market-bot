"""W102.3 Part B: READ-ONLY collector. Run on the box (stdin): venv/bin/python - < collect_night.py <sheet.json> <out.json> [DATE_TAGS,...]
For every ticker on the sheet's games of the given date tags: market status/result (Kalshi demo GET /markets) and,
for each shadow order logged on that ticker, the order's fill (GET /portfolio/orders). No orders placed, nothing written but <out>."""
import json, os, sys, collections
from pathlib import Path
sys.path[:0] = ["src", "."]
os.environ["BOT_ENV"] = "paper"
import scripts.demo_fill_forward_report as fr
from prediction_market_bot import t4_fill_status as tfs
from prediction_market_bot.c5_execution.shadow_flat_stake import demo_host_ok
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
tfs._load_dotenv_if_needed(Path(".env")); os.environ["BOT_ENV"] = "paper"
sheet, out = sys.argv[1], sys.argv[2]
tags = (sys.argv[3] if len(sys.argv) > 3 else "26NOV03").split(",")
d = json.load(open(sheet))
tickers = sorted({p["ticker"] for g in d["games"] if any(t in g["game"] for t in tags) for p in g["picks"]})
client = KalshiMarketClient.from_env()
assert demo_host_ok(), "not demo host"
res = {}
for tk in tickers:
    ok, m = client._get(f"/markets/{tk}")
    m = (m.get("market", m) if ok and isinstance(m, dict) else {}) or {}
    res[tk] = {"status": m.get("status"), "result": m.get("result")}
orders = collections.defaultdict(list)
want = set(tickers)
for line in open("logs/demo_fill_policy.jsonl"):
    if '"shadow_order"' not in line: continue
    try: e = json.loads(line)
    except Exception: continue
    if e.get("ticker") in want and e.get("ok") and e.get("order_id"):
        orders[e["ticker"]].append({"order_id": e["order_id"], "arm": e.get("arm"), "side": e.get("side"), "price_yes": e.get("price_yes"),
                                    "stake_usd": e.get("stake_usd"), "ts": e.get("ts")})
cache = {}
for tk, lst in orders.items():
    for o in lst:
        o["fill"] = fr.lookup_fill(client, o["order_id"], tk, cache)
json.dump({"markets": res, "orders": orders}, open(out, "w"), default=str)
print(len(tickers), "tickers;", sum(len(v) for v in orders.values()), "orders;", collections.Counter(v["status"] for v in res.values()))
