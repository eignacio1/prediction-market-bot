"""W91.2 Part B: the ladder ride -- when a strike's quote sits off its own ladder by more than the cost to take it,
does the strike settle toward the ladder, and does its quote move toward the ladder within 1h / 3h?

Usage: python 12_EXPLORATORY/ride_ladder/ladder_ride.py <PRICE_ARCHIVE> <settle_cache.json> <out dir inside 12_EXPLORATORY>
Measure-only. Select on the first half of games in time, score on the second half. Net of cost = fee k007 plus
crossing the spread (YES at the ask, NO at 1 - bid). Game-clustered intervals; BH at q=0.10 over testable first-half cells.
"""
import glob
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "longshot_bias"))
from _fence import safe_out  # noqa: E402
import calib  # noqa: E402
from prediction_market_bot.quant.inference import benjamini_hochberg, cluster_bootstrap, pooled_cluster_test  # noqa: E402
from prediction_market_bot.quant.ladder import parse_ticker  # noqa: E402
from prediction_market_bot.quant.ladder_loo import loo_ladder_prices  # noqa: E402
from prediction_market_bot.quant.money import fee_k007  # noqa: E402

KINDS = {"KXNFLTOTAL": "total", "KXMLBTOTAL": "total", "KXNFLTEAMTOTAL": "total", "KXMLBTEAMTOTAL": "total",
         "KXNFLSPREAD": "margin", "KXMLBSPREAD": "margin"}
MIN_GAMES, Q = 20, 0.10


def load(archive):
    """-> {(series, event, group): {hour_key: [(ts, ticker, bid, ask)]}}, one snapshot per clock hour per ladder."""
    snaps = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(archive, "prices_*.jsonl"))):
        for line in open(f):
            r = json.loads(line)
            s = r["series_ticker"]
            if s not in KINDS or r.get("yes_mid") is None:
                continue
            try:
                bid, ask = float(r["yes_bid"]), float(r["yes_ask"])
                ts = calib.parse_ts(r["run_ts"])
                team = parse_ticker(r["ticker"])[1]
            except (ValueError, KeyError):
                continue
            if ask < bid or ask <= 0 or bid < 0:
                continue
            group = team if "TEAMTOTAL" in s else ""
            snaps[(s, r["event_ticker"], group)].setdefault(int(ts // 3600), []).append((ts, r["ticker"], bid, ask))
    return snaps


def build_records(snaps):
    """Per (ticker, hour): mid, bid, ask, ladder price L. Returns list of dicts and index {ticker: {hour: rec}}."""
    recs, idx = [], defaultdict(dict)
    for (s, ev, _g), hours in snaps.items():
        kind = KINDS[s]
        for h, rows in hours.items():
            ts = rows[0][0]
            if calib.tier(ev, ts) is None:
                continue
            ladder = [{"ticker": t, "bid": b, "ask": a} for (_ts, t, b, a) in rows]
            for t, L in loo_ladder_prices(ladder, kind).items():
                b, a = next((b, a) for (_x, tt, b, a) in rows if tt == t)
                if not 0.05 <= 0.5 * (b + a) <= 0.95:
                    continue
                rec = {"series": s, "game": ev, "ticker": t, "ts": ts, "h": h, "bid": b, "ask": a,
                       "mid": 0.5 * (b + a), "L": L, "tier": calib.tier(ev, ts)}
                recs.append(rec)
                idx[t][h] = rec
    return recs, idx


def trigger(rec):
    """Side and net edge if the ladder price is taken at the quote, else None."""
    L, b, a = rec["L"], rec["bid"], rec["ask"]
    ey = L - a - fee_k007(a)
    q = 1.0 - b
    en = (1.0 - L) - q - fee_k007(q)
    e, side = (ey, "yes") if ey >= en else (en, "no")
    return (side, e) if e > 0 else None


def later(idx, rec, hours):
    """Same ticker's record `hours` later (same clock-hour key, tolerate +-1 hour of drift)."""
    for dh in (0, 1, -1):
        r = idx[rec["ticker"]].get(rec["h"] + hours + dh)
        if r is not None and r["ts"] > rec["ts"]:
            return r
    return None


def gapbin(e):
    return "net<2c" if e < 0.02 else "net2-5c" if e < 0.05 else "net5c+"


def ci(vals_by_game):
    m, lo, hi = cluster_bootstrap(vals_by_game, b=1000, seed=calib.SEED)
    return {"mean": m, "lo": lo, "hi": hi, "games": len(vals_by_game), "n": sum(len(v) for v in vals_by_game.values())}


def main(archive, settle_path, outdir):
    settle = {t: (1.0 if v["result"] == "yes" else 0.0) for t, v in json.load(open(settle_path)).items()}
    recs, idx = build_records(load(archive))
    rows = []
    for r in recs:
        tg = trigger(r)
        if tg is None or r["ticker"] not in settle:
            continue
        side, e = tg
        y = settle[r["ticker"]]
        s = 1.0 if side == "yes" else -1.0
        m1, m3 = later(idx, r, 1), later(idx, r, 3)
        row = {"series": r["series"], "game": r["game"], "tier": r["tier"], "gap": gapbin(e), "net_edge": e,
               "book": "tight" if (r["ask"] - r["bid"]) / 2 <= 0.01 else "wide", "side": side,
               "pnl": calib.side_pnl(side, y, r["bid"], r["ask"]), "toward_settle": s * (y - r["mid"]),
               "move1h": None if m1 is None else s * (m1["mid"] - r["mid"]),
               "move3h": None if m3 is None else s * (m3["mid"] - r["mid"]),
               "strike_moves": None if m3 is None else s * (m3["mid"] - r["mid"]),
               "ladder_moves": None if m3 is None else -s * (m3["L"] - r["L"]),
               "gap_c": s * (r["L"] - r["mid"]), "date": str(calib.game_start(r["game"])[1])}
        rows.append(row)
    dates = sorted({r["date"] for r in rows})
    split = dates[len(dates) // 2] if dates else ""
    first = [r for r in rows if r["date"] < split]
    second = [r for r in rows if r["date"] >= split]

    def bygame(rs, key):
        d = defaultdict(list)
        for r in rs:
            if r[key] is not None:
                d[r["game"]].append(r[key])
        return d

    summary = {"triggers": len(rows), "snapshots_scored": len(recs), "split_date": split,
               "first_half": len(first), "second_half": len(second)}
    for name, rs in (("all", rows), ("first", first), ("second", second)):
        summary[name] = {k: ci(bygame(rs, k)) for k in ("pnl", "toward_settle", "move1h", "move3h") if bygame(rs, k)}
    both = [r for r in rows if r["strike_moves"] is not None]
    summary["who_corrects"] = {
        "n": len(both),
        "strike_moves_toward_ladder_mean": sum(r["strike_moves"] for r in both) / max(1, len(both)),
        "ladder_moves_toward_strike_mean": sum(r["ladder_moves"] for r in both) / max(1, len(both)),
        "share_strike_moved_more": sum(r["strike_moves"] > r["ladder_moves"] for r in both) / max(1, len(both)),
    }

    def cells_of(rs):
        c = defaultdict(list)
        for r in rs:
            c[(r["series"], r["tier"], r["gap"], r["book"])].append(r)
        return c

    cf, cs = cells_of(first), cells_of(second)
    keys, tests = [], {}
    for k, rs in cf.items():
        if len({r["game"] for r in rs}) >= MIN_GAMES:
            t = pooled_cluster_test([(r["game"], r["pnl"]) for r in rs], b=1500)
            keys.append(k)
            tests[k] = t
    flags = benjamini_hochberg([tests[k]["p_one_sided"] for k in keys], Q) if keys else []
    cells = []
    for k, fl in zip(keys, flags):
        t = tests[k]
        c = {"kind": "LADDER", "family": k[0], "tier": k[1], "gap": k[2], "book": k[3], "first_n_games": t["n_games"],
             "first_mean": t["mean"], "first_ci95": t["ci95"], "first_p": t["p_one_sided"], "selected_bh": bool(fl and t["mean"] > 0)}
        rs2 = cs.get(k, [])
        if c["selected_bh"]:
            if len({r["game"] for r in rs2}) >= MIN_GAMES:
                t2 = pooled_cluster_test([(r["game"], r["pnl"]) for r in rs2], b=1500)
                c.update(second_mean=t2["mean"], second_ci95=t2["ci95"], second_n_games=t2["n_games"],
                         status="HELD_OUT" if t2["ci95"][0] > 0 else "FAILED")
            else:
                c.update(second_n_games=len({r["game"] for r in rs2}), status="FAILED", note="second half underpowered")
        cells.append(c)
    summary["cells_tested_first_half"] = len(keys)
    summary["cells_selected_bh"] = sum(c["selected_bh"] for c in cells)
    summary["cells_held_out"] = sum(c.get("status") == "HELD_OUT" for c in cells)
    # descriptive second-half by family (no selection) so a null is not mistaken for a power failure
    summary["second_half_by_family"] = {s: ci(bygame([r for r in second if r["series"] == s], "pnl"))
                                        for s in KINDS if any(r["series"] == s for r in second)}
    json.dump(summary, open(safe_out(os.path.join(outdir, "ladder_ride_summary.json")), "w"), indent=1)
    json.dump(cells, open(safe_out(os.path.join(outdir, "ladder_ride_cells.json")), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
