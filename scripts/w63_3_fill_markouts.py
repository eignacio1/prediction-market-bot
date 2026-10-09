#!/usr/bin/env python3
"""W63.3 Part B step 3: fill markouts / adverse selection (offline analysis of cached demo GETs).

Inputs (from w63_3_fetch_orders.py / w63_3_fetch_candles.py): venue json, candles json; plus both
ledgers and fill sidecars. Held-side convention: all prices are for the side the bot holds
(YES -> yes quote, NO -> 1 - yes quote). Markout = held-side mid at (anchor + h) - anchor price,
so positive = the market moved in the holder's favour. Filled orders anchor at the fill (price =
fill price) and, separately, at submit (price = fill price, to compare with non-fills); never-filled
orders anchor at submit (price = the resting limit, i.e. the price they would have paid).
Mid is only used when the candle is two-sided (bid > 0 and ask < 1); otherwise that horizon is NA.
CIs are game-clustered bootstrap (4,000 resamples). Read-only; no venue access.
"""
from __future__ import annotations
import argparse, bisect, json, math, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot import t4_fill_status as tf  # noqa: E402

HORIZONS = (1, 5, 30)
MISSING: list[str] = []  # CONFIRMED_FILLED rows whose fill record is not in the cached history
VALID: list[dict] = []  # sampled never-filled orders: GET'd order vs the ledger-derived submit time/limit


def ledger_limit(p):
    """Held-side limit the client submits: the ledger's held-side mid floored to the cent."""
    m = fnum(p.get("mid_price_at_entry"))
    return None if m is None else math.floor(m * 100 + 1e-9) / 100.0


def ts(s) -> float:
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()


def fnum(*vals):
    for v in vals:
        if v not in (None, ""):
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return None


def px(d: dict, base: str):
    """order/fill price in dollars for yes_price/no_price (cents or *_dollars)."""
    dol = fnum(d.get(f"{base}_dollars"))
    if dol is not None:
        return dol
    c = fnum(d.get(base))
    return None if c is None else c / 100.0


class Candles:
    def __init__(self, rows):
        self.rows = sorted(rows or [], key=lambda r: r["end_period_ts"])
        self.t = [r["end_period_ts"] for r in self.rows]

    def quote(self, t, side, max_age=1800):
        i = bisect.bisect_right(self.t, t) - 1
        if i < 0 or t - self.t[i] > max_age:
            return None
        r = self.rows[i]
        b = fnum(r["yes_bid"].get("close_dollars")) if r.get("yes_bid") else None
        a = fnum(r["yes_ask"].get("close_dollars")) if r.get("yes_ask") else None
        if b is None or a is None:
            return None
        if side == "NO":
            b, a = 1 - a, 1 - b
        return {"bid": b, "ask": a, "two_sided": b > 0 and a < 1, "age_s": t - self.t[i]}


def ci(rows, key):
    by = defaultdict(list)
    for r in rows:
        if r.get(key) is not None:
            by[r["game"]].append(r[key])
    vals = [v for g in by.values() for v in g]
    if not vals:
        return {"n": 0, "mean": None, "ci95": None}
    return {"n": len(vals), "games": len(by), "mean": round(mean(vals), 4), "ci95": tf.cluster_bootstrap_ci(by)}


def build(book, portfolio, sidecar, venue, candles):
    status = tf.load_fill_status(Path(sidecar))
    fills_by_order = defaultdict(list)
    for f in venue["fills"]:
        fills_by_order[f.get("order_id")].append(f)
    fills_by_id = {f.get("fill_id") or f.get("trade_id"): f for f in venue["fills"]}
    out = []
    for p in json.load(open(portfolio))["closed_positions"]:
        oid, side = p.get("kalshi_order_id"), p.get("direction")
        st = status.get(p["position_id"], {})
        o = venue["orders"].get(oid) if oid else None
        cls = st.get("fill_class")
        if cls not in (tf.CONFIRMED_FILLED, tf.CONFIRMED_NOT_FILLED) or not oid:
            continue
        derived = not o or bool(o.get("_error"))
        if derived:
            # Unsampled never-filled order: submit time = ledger entered_at, limit = ledger held-side
            # entry price (the client prices the limit at the model's mid). Validated on the sample.
            o = {"type": "limit(ledger)", "time_in_force": "good_till_canceled(ledger)", "status": "never_filled"}
            t_sub, limit = ts(p["entered_at"]), ledger_limit(p)
        else:
            t_sub = ts(o["created_time"])
            limit = px(o, "yes_price" if side == "YES" else "no_price")
            if cls == tf.CONFIRMED_NOT_FILLED:
                VALID.append({"dt_s": t_sub - ts(p["entered_at"]) if p.get("entered_at") else 0.0,
                              "dlimit": None if limit is None or ledger_limit(p) is None else round(limit - ledger_limit(p), 4)})
        cd = candles.get(p["kalshi_ticker"])
        C = Candles(cd) if cd else None
        payoff = 1.0 if p.get("outcome") == "WIN" else (0.0 if p.get("outcome") == "LOSS" else None)  # held-side result
        r = {"book": book, "pos": p["position_id"], "game": tf.game_key(p), "cls": cls, "side": side,
             "band": p.get("band"), "ticker": p["kalshi_ticker"], "order_type": o.get("type"), "derived": derived,
             "tif": o.get("time_in_force"), "order_status": o.get("status"), "limit": limit,
             "ledger_mid": p.get("mid_price_at_entry"), "ledger_entry": p.get("entry_price_paid"),
             "win": 1.0 if p.get("outcome") == "WIN" else 0.0}
        q0 = C.quote(t_sub, side) if C else None
        r["venue_bid"], r["venue_ask"] = (q0["bid"], q0["ask"]) if q0 else (None, None)
        r["two_sided_at_submit"] = bool(q0 and q0["two_sided"])
        if q0 and limit is not None:
            r["limit_minus_ask"] = round(limit - q0["ask"], 4)
            r["limit_minus_bid"] = round(limit - q0["bid"], 4)
            if q0["two_sided"]:
                r["limit_minus_venue_mid"] = round(limit - (q0["bid"] + q0["ask"]) / 2, 4)
        if r["ledger_mid"] is not None and q0 and q0["two_sided"]:
            lm = r["ledger_mid"] if side == "YES" else 1 - r["ledger_mid"]
            r["ledger_mid_minus_venue_mid"] = round(lm - (q0["bid"] + q0["ask"]) / 2, 4)
        fl = fills_by_order.get(oid, []) or [fills_by_id[i] for i in st.get("matched_fill_ids", []) if i in fills_by_id]
        fl = sorted(fl, key=lambda f: f["created_time"])
        r["filled_without_fill_record"] = cls == tf.CONFIRMED_FILLED and not fl
        if cls == tf.CONFIRMED_FILLED and fl:
            cnt = sum(fnum(f.get("count_fp"), f.get("count")) or 0 for f in fl)
            fp = [px(f, "yes_price" if side == "YES" else "no_price") for f in fl]
            w = [fnum(f.get("count_fp"), f.get("count")) or 0 for f in fl]
            price = sum(a * b for a, b in zip(fp, w)) / cnt if cnt else fp[0]
            t_fill = ts(fl[0]["created_time"])
            r.update(fill_price=round(price, 4), is_taker=any(f.get("is_taker") for f in fl),
                     secs_to_fill=round(t_fill - t_sub, 1), anchor_price=price)
            qf = C.quote(t_fill, side) if C else None
            r["fill_mid"] = round((qf["bid"] + qf["ask"]) / 2, 4) if qf and qf["two_sided"] else None
            r["fill_vs_mid_at_fill"] = round(price - r["fill_mid"], 4) if r["fill_mid"] is not None else None
            for h in HORIZONS:
                qh = C.quote(t_fill + 60 * h, side) if C else None
                m = (qh["bid"] + qh["ask"]) / 2 if qh and qh["two_sided"] else None
                r[f"mo_fill_{h}m"] = None if m is None else round(m - price, 4)
                qs = C.quote(t_sub + 60 * h, side) if C else None
                ms = (qs["bid"] + qs["ask"]) / 2 if qs and qs["two_sided"] else None
                r[f"mo_sub_{h}m"] = None if ms is None else round(ms - price, 4)
            # pre-fill drift: how far did the market move against us between submit and fill?
            if q0 and q0["two_sided"] and r["fill_mid"] is not None:
                r["drift_sub_to_fill"] = round(r["fill_mid"] - (q0["bid"] + q0["ask"]) / 2, 4)
        elif cls == tf.CONFIRMED_FILLED:
            MISSING.append(book)
            continue  # classified filled but the fill record is not in the cached history: excluded, counted below
        else:
            if limit is None:
                continue
            r["anchor_price"] = limit
            for h in HORIZONS:
                qs = C.quote(t_sub + 60 * h, side) if C else None
                ms = (qs["bid"] + qs["ask"]) / 2 if qs and qs["two_sided"] else None
                r[f"mo_sub_{h}m"] = None if ms is None else round(ms - limit, 4)
        a = r.get("anchor_price")
        r["mo_settle"] = None if payoff is None or a is None else round(payoff - a, 4)
        ll = ledger_limit(p)
        r["mo_settle_at_ledger_px"] = None if payoff is None or ll is None else round(payoff - ll, 4)
        r["ledger_px"] = ll
        r["immediate"] = (r.get("secs_to_fill") is not None and r["secs_to_fill"] <= 60)
        out.append(r)
    return out


def summarize(rows):
    S = {}
    for book in sorted({r["book"] for r in rows}):
        b = [r for r in rows if r["book"] == book]
        F = [r for r in b if r["cls"] == tf.CONFIRMED_FILLED]
        N = [r for r in b if r["cls"] == tf.CONFIRMED_NOT_FILLED]
        s = {"n_filled": len(F), "n_not_filled": len(N), "order_types": dict(__import__("collections").Counter(f"{r['order_type']}|{r['tif']}|derived={r['derived']}" for r in b)),
             "filled_taker_share": round(sum(1 for r in F if r.get("is_taker")) / len(F), 3) if F else None,
             "secs_to_fill_median": sorted(r["secs_to_fill"] for r in F)[len(F) // 2] if F else None,
             "venue_two_sided_at_submit": {"filled": sum(r["two_sided_at_submit"] for r in F), "not_filled": sum(r["two_sided_at_submit"] for r in N)},
             "settle_markout": {"filled": ci(F, "mo_settle"), "not_filled": ci(N, "mo_settle")},
             "mean_price": {"filled": round(mean(r["anchor_price"] for r in F), 4) if F else None, "not_filled": round(mean(r["anchor_price"] for r in N), 4) if N else None}}
        for k in ("limit_minus_ask", "limit_minus_bid", "limit_minus_venue_mid", "ledger_mid_minus_venue_mid"):
            s[k] = {"filled": ci(F, k), "not_filled": ci(N, k)}
        for h in HORIZONS:
            s[f"markout_{h}m"] = {"filled_from_fill": ci(F, f"mo_fill_{h}m"), "filled_from_submit": ci(F, f"mo_sub_{h}m"),
                                  "not_filled_from_submit": ci(N, f"mo_sub_{h}m")}
        s["fill_price_vs_mid_at_fill"] = ci(F, "fill_vs_mid_at_fill")
        s["drift_submit_to_fill"] = ci(F, "drift_sub_to_fill")
        s["settle_markout_at_ledger_px"] = {"filled": ci(F, "mo_settle_at_ledger_px"), "not_filled": ci(N, "mo_settle_at_ledger_px")}
        s["win_rate"] = {"filled": ci(F, "win"), "not_filled": ci(N, "win")}
        imm = [r for r in F if r["immediate"]]
        late = [r for r in F if not r["immediate"]]
        s["filled_immediate_le60s_vs_resting"] = {
            "n_immediate": len(imm), "n_resting": len(late),
            "win_rate_immediate": ci(imm, "win"), "win_rate_resting": ci(late, "win"),
            "settle_at_fill_px_immediate": ci(imm, "mo_settle"), "settle_at_fill_px_resting": ci(late, "mo_settle")}
        sf = sorted(r["secs_to_fill"] for r in F)
        s["secs_to_fill_quantiles"] = {q: sf[min(len(sf) - 1, int(q * len(sf)))] for q in (0.1, 0.25, 0.5, 0.75, 0.9)} if sf else None
        s["fill_vs_limit"] = ci([dict(r, fvl=round(r["fill_price"] - r["limit"], 4)) for r in F if r.get("limit") is not None], "fvl")
        by_band = {}
        for band in sorted({str(r["band"]) for r in b}):
            Fb = [r for r in F if str(r["band"]) == band]
            Nb = [r for r in N if str(r["band"]) == band]
            by_band[band] = {"filled": ci(Fb, "mo_settle"), "not_filled": ci(Nb, "mo_settle")}
        s["settle_markout_by_band"] = by_band
        S[book] = s
    return S


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default="/tmp/w63_3_venue.json")
    ap.add_argument("--candles", default="/tmp/w63_3_candles.json")
    ap.add_argument("--out", default="/tmp/w63_3_markouts.json")
    ap.add_argument("--repo", default=str(REPO))
    a = ap.parse_args(argv)
    repo = Path(a.repo)
    venue, candles = json.load(open(a.venue)), json.load(open(a.candles))
    rows = []
    for book, (pf, sc) in tf.BOOKS.items():
        rows += build(book, repo / pf.relative_to(tf.REPO_ROOT), repo / sc.relative_to(tf.REPO_ROOT), venue, candles)
    v = [x for x in VALID if x["dlimit"] is not None]
    res = {"summary": summarize(rows), "n_rows": len(rows), "filled_excluded_no_fill_record": {b: MISSING.count(b) for b in set(MISSING)},
           "ledger_derivation_check": {"n_sampled": len(VALID),
                                       "max_abs_submit_time_diff_s": max((abs(x["dt_s"]) for x in VALID), default=None),
                                       "limit_matches_ledger": sum(1 for x in v if abs(x["dlimit"]) < 0.0051), "of": len(v)}}
    Path(a.out).write_text(json.dumps({**res, "rows": rows}))
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
