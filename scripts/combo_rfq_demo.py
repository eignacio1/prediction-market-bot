"""W127.3 Part A (B-024): request quotes in the Kalshi DEMO for NBA same-game combos the pricer can fully price. DEMO ONLY.

Runs on the box (demo credentials live there, env only). Prices production same-game combos with the shadow writer's own code
(game draws + combo_price), mirrors each combo into the demo exchange if the demo does not already list it, sends one RFQ of one
contract, and records: quote / no quote, quoted price vs the engine P and vs the product of legs, time to quote, and whether a
demo accept was possible. At most MAX_ACCEPTS_PER_RUN accepts; Kelly 0; caps are in c5_execution/kalshi_rfq.py. If the demo
answers that RFQs or combos are unsupported, the run records NONE with the API response and stops.

  BOT_ENV=paper PM_COMBO_RFQ_DEMO=on PYTHONPATH=src:. python3 scripts/combo_rfq_demo.py [--now ISO] [--no-refresh] [--out DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.c5_execution import kalshi_rfq as R  # noqa: E402

WINDOW_MIN = (30.0, 1800.0)   # minutes to tip: tonight's slate (a 30 h look-ahead; combos exist ~2 days before the game)
POLL_S = 3.0
POLL_TOTAL_S = 90.0
ACCEPT_WAIT_S = 45.0
MIN_ENGINE_SE = 0.01


def enabled() -> bool:
    return os.environ.get("PM_COMBO_RFQ_DEMO", "off").strip().lower() in ("on", "1", "true")


def eligible(row: dict) -> bool:
    """Fully priced, resolved, tight MC error, no flags (same filter the combo pre-registration scores on)."""
    return (row.get("engine_p") is not None and row.get("resolved") and (row.get("mc_se") or 1) <= MIN_ENGINE_SE
            and not row.get("flags") and not row.get("legs_unpriced"))


def pick_sample(rows: list, k: int) -> list:
    """Deterministic spread over leg counts: sort by (hash of ticker), take round-robin from leg-count buckets 2-3 / 4-6 / 7+."""
    buckets: dict = {"2-3": [], "4-6": [], "7+": []}
    for r in sorted((r for r in rows if eligible(r)), key=lambda r: hashlib.sha256(r["market_ticker"].encode()).hexdigest()):
        n = r["n_legs"]
        buckets["2-3" if n <= 3 else "4-6" if n <= 6 else "7+"].append(r)
    out = []
    while len(out) < k and any(buckets.values()):
        for b in buckets.values():
            if b and len(out) < k:
                out.append(b.pop(0))
    return out


def nightly_remaining(ledger: Path, day: str) -> int:
    used = 0
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("event") == "rfq_created" and r.get("day") == day:
                used += 1
    return max(0, R.MAX_RFQS_PER_NIGHT - used)


def quote_metrics(q: dict, engine_p: float, p_naive) -> dict:
    """Quote body -> what we would pay. The maker posts bids on both sides: buy YES costs 1 - no_bid, buy NO costs 1 - yes_bid."""
    yb, nb = float(q.get("yes_bid_dollars") or 0), float(q.get("no_bid_dollars") or 0)
    buy_yes = round(1 - nb, 4) if nb > 0 else None
    buy_no = round(1 - yb, 4) if yb > 0 else None
    out = dict(yes_bid=yb, no_bid=nb, buy_yes_price=buy_yes, buy_no_price=buy_no, overround=round(yb + nb, 4) if (yb and nb) else None)
    if buy_yes is not None:
        out["yes_minus_engine"] = round(buy_yes - engine_p, 4)
        out["yes_minus_product"] = round(buy_yes - p_naive, 4) if p_naive is not None else None
    if buy_no is not None:
        out["no_minus_engine_no"] = round(buy_no - (1 - engine_p), 4)
    return out


def accept_side(m: dict, engine_p: float):
    """The side whose quoted price is furthest below the engine's fair price (descriptive pick; demo size, Kelly 0)."""
    cands = []
    if m.get("buy_yes_price") is not None:
        cands.append((engine_p - m["buy_yes_price"], "yes"))
    if m.get("buy_no_price") is not None:
        cands.append(((1 - engine_p) - m["buy_no_price"], "no"))
    return max(cands)[1] if cands else None


def run(client, rows: list, combos: dict, now: datetime, out_dir: Path, sleep=time.sleep, clock=time.monotonic) -> dict:
    day = now.strftime("%Y-%m-%d")
    ledger = out_dir / "COMBO_RFQ_DEMO.jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)

    def log(rec: dict) -> None:
        rec.update(ts_utc=datetime.now(timezone.utc).isoformat(), day=day)
        with open(ledger, "a") as f:
            f.write(json.dumps(rec) + "\n")

    budget = min(nightly_remaining(ledger, day), R.MAX_RFQS_PER_RUN)
    sample = pick_sample(rows, budget)
    summary = dict(day=day, candidates=sum(eligible(r) for r in rows), sampled=len(sample), nightly_budget=budget,
                   created=0, quoted=0, no_quote=0, accepted=0, executed=0, not_listed_on_demo=0, none_reason=None)
    live: dict = {}
    for r in sample:
        t = r["market_ticker"]
        mk = client.market(t)
        if not mk["ok"]:
            c = combos.get(t) or {}
            cr = client.create_combo(c.get("mve_collection_ticker", ""), [
                {"market_ticker": l["market_ticker"], "event_ticker": l["event_ticker"], "side": l["side"]} for l in c.get("mve_selected_legs", [])]
            ) if c.get("mve_collection_ticker") else {"ok": False, "status": None, "body": {"error": "no_collection_ticker"}}
            if not cr["ok"]:
                summary["not_listed_on_demo"] += 1
                log(dict(event="not_listed_on_demo", market_ticker=t, get=mk, create=cr))
                continue
            demo_t = (cr["body"].get("market_ticker") or t)
        else:
            demo_t = t
        res = client.create_rfq(demo_t)
        if not res["ok"]:
            log(dict(event="rfq_failed", market_ticker=t, demo_ticker=demo_t, resp=res))
            if res["status"] in (400, 404, 403, 405, 501) and summary["created"] == 0:
                summary["none_reason"] = res
                break      # demo does not support this: record NONE with the API response and stop
            continue
        rid = res["body"].get("id")
        summary["created"] += 1
        live[rid] = dict(row=r, demo_ticker=demo_t, t0=clock(), quote=None, tq=None)
        log(dict(event="rfq_created", market_ticker=t, demo_ticker=demo_t, rfq_id=rid, contracts_fp=R.CONTRACTS_FP, engine_p=r["engine_p"],
                 p_product_of_legs=r["p_product_of_legs"], n_legs=r["n_legs"], minutes_to_tip=r["minutes_to_tip"], prod_quote_state=r["quote_state"]))

    deadline = clock() + POLL_TOTAL_S
    while live and clock() < deadline and any(v["quote"] is None for v in live.values()):
        for rid, v in live.items():
            if v["quote"] is not None:
                continue
            qs = client.quotes(rid)
            lst = (qs["body"].get("quotes") or []) if qs["ok"] else []
            if lst:
                v["quote"], v["tq"] = lst[0], clock() - v["t0"]
        sleep(POLL_S)

    for rid, v in live.items():
        r = v["row"]
        if v["quote"] is None:
            summary["no_quote"] += 1
            log(dict(event="no_quote", rfq_id=rid, market_ticker=r["market_ticker"], waited_s=round(clock() - v["t0"], 1)))
            continue
        summary["quoted"] += 1
        m = quote_metrics(v["quote"], r["engine_p"], r["p_product_of_legs"])
        rec = dict(event="quote", rfq_id=rid, market_ticker=r["market_ticker"], quote_id=v["quote"].get("id"), time_to_quote_s=round(v["tq"], 1),
                   engine_p=r["engine_p"], p_product_of_legs=r["p_product_of_legs"], n_legs=r["n_legs"], **m)
        side = accept_side(m, r["engine_p"])
        rec["accept_possible"] = side is not None
        if side and summary["accepted"] < R.MAX_ACCEPTS_PER_RUN and v["quote"].get("id"):
            ac = client.accept(rid, v["quote"]["id"], side)
            rec.update(accepted_side=side, accept_resp=ac)
            if ac["ok"]:
                summary["accepted"] += 1
                end = clock() + ACCEPT_WAIT_S
                while clock() < end:
                    qq = client.quotes(rid)
                    st = next((x.get("status") for x in (qq["body"].get("quotes") or []) if x.get("id") == v["quote"].get("id")), None) if qq["ok"] else None
                    rec["final_status"] = st
                    if st in ("executed", "cancelled"):
                        break
                    sleep(POLL_S)
                if rec.get("final_status") == "executed":
                    summary["executed"] += 1
        log(rec)

    for rid in live:
        c = client.cancel_rfq(rid)
        log(dict(event="rfq_cancel", rfq_id=rid, resp_status=c["status"]))
    log(dict(event="run_summary", **summary))
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw" / "nba_props"))
    ap.add_argument("--out", default=str(ROOT / "exp_output" / "COMBO_RFQ_DEMO"))
    ap.add_argument("--no-refresh", action="store_true")
    ap.add_argument("--now")
    ap.add_argument("--draws", type=int, default=4000)
    a = ap.parse_args(argv)
    if not enabled():
        print(json.dumps({"event": "COMBO_RFQ_DEMO_OFF", "reason": "PM_COMBO_RFQ_DEMO is not on"}))
        return 0
    import nba_combo_shadow as S
    from run_nba_engine_props_shadow import load_tips, refresh
    from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    now = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    raw = Path(a.raw)
    if not a.no_refresh:
        refresh(raw / "box.json", raw / "tips.json", now)
    games, pl = F.parse_box(json.loads((raw / "box.json").read_text()))
    fc = F.NBAEngineProps(games, pl, load_tips(raw / "tips.json"))
    cache: dict = {}

    def draws_for(suf):
        if suf not in cache:
            cache[suf] = S.game_draws(fc, suf, a.draws)[0]
        return cache[suf]

    tips: dict = {}

    def tip_for(suf):
        k = fc.kickoff_for_event("KXNBAGAME-" + suf)
        tips[suf] = (k[0].isoformat() if k else None)
        return k and k[0]

    S.WINDOW_MIN = WINDOW_MIN
    S.UNQUOTED_SAMPLE = 1.0            # every combo is a candidate: an RFQ does not need a standing quote
    fetched = S.fetch_open_combos()
    combos = {m["ticker"]: m for m in fetched if S.same_game(m)}
    rows = S.build_rows(list(combos.values()), draws_for, tip_for, now, now.strftime("%Y%m%dT%H%M%SZ"))
    stages = dict(fetched=len(fetched), same_game=len(combos), rows=len(rows), engine_p=sum(r.get("engine_p") is not None for r in rows),
                  resolved=sum(bool(r.get("resolved")) for r in rows), mc_se_ok=sum((r.get("mc_se") or 1) <= MIN_ENGINE_SE for r in rows),
                  flagged=sum(bool(r.get("flags")) for r in rows), unpriced=sum(bool(r.get("legs_unpriced")) for r in rows),
                  window_min=list(WINDOW_MIN), games_seen=len(tips), tips_loaded=len(fc.tips), tips_keys=[[k[0], sorted(k[1])] for k in list(fc.tips)[:6]], tips_file_bytes=(raw / "tips.json").stat().st_size if (raw / "tips.json").exists() else None, games_no_tip=sorted(g for g, t in tips.items() if t is None)[:8],
                  tips_sample=dict(sorted(tips.items())[:8]), min_to_tip=sorted(r["minutes_to_tip"] for r in rows if r.get("minutes_to_tip") is not None)[:5])
    summary = run(R.DemoRfqClient.from_env(), rows, combos, now, Path(a.out))
    summary["stages"] = stages
    print(json.dumps({"event": "COMBO_RFQ_DEMO_RUN", **summary}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
