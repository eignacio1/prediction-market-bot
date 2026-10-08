#!/usr/bin/env python3
"""W60.1 / GG-300: fill truth for the T4M-PROJ epoch-12 clean cohort. READ-ONLY.

Only GET calls against the demo venue (authenticated=True; BOT_ENV must be paper).
Never submits, cancels or modifies anything and writes no ledger.

  1. Re-query a seeded sample of rows the T-571 pass left NOT_RETRIEVABLE and tabulate failure reasons.
  2. Paginate GET /portfolio/fills and /portfolio/settlements to the end; record retention horizons.
  3. Classify each cohort row CONFIRMED_FILLED / CONFIRMED_NOT_FILLED / UNVERIFIABLE.
  4. P&L per bet with game-clustered 95% CI: all rows vs CONFIRMED_FILLED only.

Run on the VPS:
    cd /opt/prediction-market-bot
    PYTHONPATH=src python3 scripts/w60_1_cohort_fill_truth.py \
        --portfolio logs/paper_portfolio_mlb_t4.json \
        --prior /tmp/t571_kalshi_verification_results.json --out /tmp/w60_1_results.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient  # noqa: E402
from t571_verify_t4mproj_kalshi_fills import check_order, load_t4mproj_clean_closed  # noqa: E402

FALLBACK_WINDOW = timedelta(seconds=180)
HORIZON_MARGIN = timedelta(hours=1)


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def paginate(client, path, key, limit=1000):
    items, cursor, pages = [], None, 0
    while True:
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        ok, data = client._get(path, params=params, authenticated=True)
        if not ok:
            return items, pages, f"STOPPED: {str(data)[:200]}"
        batch = data.get(key, [])
        items.extend(batch)
        pages += 1
        cursor = data.get("cursor")
        if not cursor or not batch:
            return items, pages, "COMPLETE"
        time.sleep(0.15)


def cluster_ci(pairs):
    """pairs = [(cluster, pnl)]. Mean, cluster-robust SE, 95% CI (normal; df noted)."""
    n = len(pairs)
    if n < 2:
        return {"n": n}
    mean = sum(p for _, p in pairs) / n
    by = defaultdict(float)
    cnt = Counter()
    for c, p in pairs:
        by[c] += p - mean
        cnt[c] += 1
    g = len(by)
    if g < 2:
        return {"n": n, "mean": mean, "n_clusters": g}
    se = math.sqrt(g / (g - 1) * sum(v * v for v in by.values())) / n
    try:
        from scipy import stats
        crit = float(stats.t.ppf(0.975, g - 1))
    except Exception:
        crit = 1.96
    return {"n": n, "n_clusters": g, "mean_pnl_per_bet": round(mean, 5), "se": round(se, 5),
            "ci95": [round(mean - crit * se, 5), round(mean + crit * se, 5)], "crit": round(crit, 3),
            "total_pnl": round(sum(p for _, p in pairs), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--portfolio", required=True, type=Path)
    ap.add_argument("--prior", type=Path, help="T-571 results JSON (source of the NOT_RETRIEVABLE list)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sample", type=int, default=30)
    a = ap.parse_args()

    if os.environ.get("BOT_ENV", "").lower() == "live":
        sys.exit("refusing: BOT_ENV=live (this audit is demo-only)")
    client = KalshiMarketClient.from_env()
    if not client.has_signing_key():
        sys.exit("no signing key")

    rows = load_t4mproj_clean_closed(a.portfolio)
    out = {"n_cohort_rows": len(rows), "base_env": os.environ.get("BOT_ENV")}

    # Part 1 -- failure reasons on a seeded sample of the prior NOT_RETRIEVABLE rows
    if a.prior and a.prior.exists():
        prior = json.load(open(a.prior))
        nr = [r for r in prior["results"] if r["verdict"] == "NOT_RETRIEVABLE"]
        out["prior_counts"] = prior.get("counts")
        random.seed(60)
        samp = random.sample(nr, min(a.sample, len(nr)))
        reasons, detail = Counter(), []
        for r in samp:
            c = check_order(client, r["kalshi_order_id"])
            key = c.get("reason", c.get("status"))
            reasons[str(key)[:60]] += 1
            detail.append({"order": r["kalshi_order_id"], "game_date": r.get("game_date"), **c})
            time.sleep(0.15)
        out["sample"] = {"n": len(samp), "reasons_now": dict(reasons),
                         "reasons_at_t571": dict(Counter(str(r.get("reason"))[:60] for r in samp)),
                         "detail": detail}

    # Part 2 -- full fills + settlements history
    fills, fp, fstat = paginate(client, "/portfolio/fills", "fills")
    setts, sp, sstat = paginate(client, "/portfolio/settlements", "settlements")
    fts = sorted(t for t in (parse_ts(f.get("created_time")) for f in fills) if t)
    sts = sorted(t for t in (parse_ts(s.get("settled_time")) for s in setts) if t)
    out["fills"] = {"n": len(fills), "pages": fp, "status": fstat,
                    "earliest": fts[0].isoformat() if fts else None, "latest": fts[-1].isoformat() if fts else None}
    out["settlements"] = {"n": len(setts), "pages": sp, "status": sstat,
                          "earliest": sts[0].isoformat() if sts else None, "latest": sts[-1].isoformat() if sts else None}
    horizon = fts[0] if (fts and fstat == "COMPLETE") else None

    # Part 3 -- classify
    by_order = defaultdict(list)
    by_ticker = defaultdict(list)
    for f in fills:
        by_order[f.get("order_id")].append(f)
        by_ticker[f.get("ticker")].append(f)
    sett_by_ticker = defaultdict(list)
    for s in setts:
        sett_by_ticker[s.get("ticker")].append(s)
    prior_verdict = {r["kalshi_order_id"]: r for r in prior["results"]} if a.prior else {}

    classified, via = [], Counter()
    for r in rows:
        oid, tk = r.get("kalshi_order_id"), r.get("kalshi_ticker")
        et = parse_ts(r.get("entered_at"))
        side = (r.get("direction") or "").lower()
        label, how = None, None
        if oid and oid in by_order:
            label, how = "CONFIRMED_FILLED", "order_id"
        else:
            if et:
                cands = [f for f in by_ticker.get(tk, [])
                         if (f.get("side") or "").lower() == side
                         and (t := parse_ts(f.get("created_time"))) and abs(t - et) <= FALLBACK_WINDOW]
                if cands:
                    label, how = "CONFIRMED_FILLED", "fallback_ticker_side_window"
        if label is None:
            pv = prior_verdict.get(oid, {}).get("verdict")
            if pv == "CANCELED":
                label, how = "CONFIRMED_NOT_FILLED", "order_lookup_canceled"
            elif horizon and et and et >= horizon + HORIZON_MARGIN:
                label, how = "CONFIRMED_NOT_FILLED", "inside_fills_horizon_no_match"
            else:
                label, how = "UNVERIFIABLE", "outside_horizon_or_no_timestamp"
        via[(label, how)] += 1
        classified.append({"position_id": r.get("position_id"), "label": label, "how": how,
                           "ticker_settled": bool(sett_by_ticker.get(tk)), "pnl": r.get("pnl"),
                           "outcome": r.get("outcome"),
                           "game": (tk or "").split("-")[1] if tk and "-" in tk else tk,
                           "game_date": r.get("game_date")})

    out["classification"] = {f"{l}|{h}": n for (l, h), n in sorted(via.items())}
    out["label_counts"] = dict(Counter(c["label"] for c in classified))
    out["unverifiable_but_ticker_settled"] = sum(1 for c in classified if c["label"] == "UNVERIFIABLE" and c["ticker_settled"])
    out["fallback_joins"] = sum(1 for c in classified if c["how"] == "fallback_ticker_side_window")
    out["rows_missing_order_id"] = sum(1 for r in rows if not r.get("kalshi_order_id"))

    def pairs(sel):
        return [(c["game"], float(c["pnl"])) for c in classified if sel(c) and c["pnl"] is not None]
    out["pnl_all"] = cluster_ci(pairs(lambda c: True))
    out["pnl_winloss"] = cluster_ci(pairs(lambda c: c["outcome"] in ("WIN", "LOSS")))
    out["pnl_confirmed_filled"] = cluster_ci(pairs(lambda c: c["label"] == "CONFIRMED_FILLED"))
    out["pnl_unverifiable"] = cluster_ci(pairs(lambda c: c["label"] == "UNVERIFIABLE"))
    out["pnl_confirmed_not_filled"] = cluster_ci(pairs(lambda c: c["label"] == "CONFIRMED_NOT_FILLED"))
    out["rows"] = classified
    json.dump(out, open(a.out, "w"), indent=1, default=str)
    brief = {k: v for k, v in out.items() if k != "rows" and k != "sample"}
    if "sample" in out:
        brief["sample"] = {k: v for k, v in out["sample"].items() if k != "detail"}
    print(json.dumps(brief, indent=1, default=str))


if __name__ == "__main__":
    main()
