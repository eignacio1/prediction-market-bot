"""W70.1 Part B step 4: read-only collector for the demo fill timing audit. Run on the VPS (needs the
demo key). For every ok order in logs/demo_fill_policy.jsonl it records order/fill times, prices and the
market result; kickoff comes from ESPN in demo_fill_timing_audit.py. Demo GETs only; places nothing."""
import json, os, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ["BOT_ENV"] = "paper"
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot import t4_fill_status as tf  # noqa: E402
tf._load_dotenv_if_needed(REPO / ".env")
os.environ["BOT_ENV"] = "paper"
from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient  # noqa: E402
from prediction_market_bot.c5_execution.shadow_flat_stake import demo_host_ok  # noqa: E402


def main() -> int:
    c = KalshiMarketClient.from_env()
    if not demo_host_ok() or not c.has_signing_key():
        print("REFUSED: not demo / no key", file=sys.stderr)
        return 2
    rows = [json.loads(l) for l in (REPO / "logs/demo_fill_policy.jsonl").read_text().splitlines() if l.strip()]
    orders = [r for r in rows if r.get("event") == "shadow_order" and r.get("ok") and r.get("order_id")]
    mk: dict = {}
    out = []
    for r in orders:
        tk = r["row_id"].split("|", 1)[1]
        if not tk.startswith("KXNFL"):
            continue
        ok, d = c._get(f"/portfolio/orders/{r['order_id']}", authenticated=True)
        o = (d.get("order", d) if ok and isinstance(d, dict) else {}) or {}
        rec = {"order_id": r["order_id"], "ticker": o.get("ticker") or tk, "arm": r.get("arm", "treatment"),
               "logged_ts": r["ts"], "created": o.get("created_time"), "last_update": o.get("last_update_time"),
               "status": o.get("status"), "fills": o.get("fill_count_fp"), "side": o.get("side"),
               "yes_price": o.get("yes_price_dollars"), "no_price": o.get("no_price_dollars"),
               "fill_cost": float(o.get("taker_fill_cost_dollars") or 0) + float(o.get("maker_fill_cost_dollars") or 0)}
        if float(rec["fills"] or 0) > 0:
            ok2, f = c._get("/portfolio/fills", params={"order_id": r["order_id"]}, authenticated=True)
            rec["fill_times"] = [x.get("created_time") for x in (f.get("fills", []) if ok2 and isinstance(f, dict) else [])]
            if rec["ticker"] not in mk:
                okm, m = c._get(f"/markets/{rec['ticker']}")
                mm = (m.get("market", m) if okm and isinstance(m, dict) else {}) or {}
                mk[rec["ticker"]] = mm.get("result")
            rec["result"] = mk[rec["ticker"]]
        out.append(rec)
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
