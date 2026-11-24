"""W125.3 H-EDGE-5: favourite-longshot at the close, per family x price bucket. Spec: PREREG.md (committed before this ran).
usage: python3 run_h5.py <nhl_store_dir> <w89_7_dir>   (reads data/ made by fetch_h5.py; writes results.json, tables.md)"""
import json, os, sys, math
from datetime import datetime, timezone, timedelta
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant.costs import taker_entry_cost  # noqa: E402
from prediction_market_bot.quant.variance import clustered_mean, icc, games_needed  # noqa: E402
from prediction_market_bot.quant.multiplicity import one_sided_p, benjamini_hochberg  # noqa: E402

BUCKETS = [(.02, .10), (.10, .25), (.25, .50), (.50, .75), (.75, .90), (.90, .980001)]
# (name, series, start cutoffs [first date, last date]); a cut-off date is a US local date -> UTC start < last+1d+08:00
FAMS = [("NHL moneyline", "KXNHLGAME", "2025-10-07", "2026-04-16", True),
        ("NBA moneyline", "KXNBAGAME", "2025-10-21", "2026-04-12", True),
        ("NBA team total", "KXNBATEAMTOTAL", "2025-10-21", "2026-04-12", False),
        ("NFL team total", "KXNFLTEAMTOTAL", "2025-09-04", "2026-01-04", False)]


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def lim(d, end=False):
    t = datetime.fromisoformat(d).replace(tzinfo=timezone.utc)
    return int((t + timedelta(days=1, hours=8)).timestamp()) if end else int(t.timestamp())


def f(x):
    try:
        return float(x)
    except Exception:
        return None


def load(fam, series, nhl_dir, w89):
    """-> list of dict(ticker, event, start, y, cs=[(end_ts,bid,ask)])."""
    sub = {"KXNBAGAME": "nba", "KXNBATEAMTOTAL": "nba", "KXNFLTEAMTOTAL": "nfl"}.get(series)
    mk_path = (os.path.join(nhl_dir, "markets", "KXNHLGAME.jsonl") if series == "KXNHLGAME"
               else os.path.join(w89, sub, "markets", series + ".jsonl"))
    res = {}
    for l in open(mk_path):
        r = json.loads(l)
        res[r["ticker"]] = (r["result"], r["event_ticker"])
    starts = json.load(open(os.path.join(HERE, "data", "starts_2025_26.json")))
    out = []
    if series == "KXNHLGAME":
        for l in open(os.path.join(nhl_dir, "candles", "KXNHLGAME.jsonl")):
            d = json.loads(l)
            t = d["ticker"]
            if t not in res or res[t][1] not in starts:
                continue
            cs = [(c["t"], c["bid"]["close"], c["ask"]["close"]) for c in d["candles"]]
            out.append(dict(ticker=t, event=res[t][1], start=ts(starts[res[t][1]]), res=res[t][0], cs=cs))
    else:
        for l in open(os.path.join(HERE, "data", f"candles_{series}.jsonl")):
            d = json.loads(l)
            t = d["ticker"]
            if not d["ok"] or t not in res:
                continue
            cs = [(c["end_period_ts"], f((c.get("yes_bid") or {}).get("close")), f((c.get("yes_ask") or {}).get("close")))
                  for c in d["candlesticks"]]
            out.append(dict(ticker=t, event=d["event"], start=ts(d["start"]), res=res[t][0], cs=cs))
    return out


def close_row(r):
    """-> (bid, ask, flag) or (None, None, reason)."""
    w = sorted((c for c in r["cs"] if r["start"] - 3 * 3600 <= c[0] <= r["start"]), key=lambda c: c[0])
    if not w:
        return None, None, "no_candle_in_3h"
    last = w[-1]
    allc = sorted(r["cs"], key=lambda c: c[0])
    bid, ask = last[1], last[2]
    flag = False
    ok_b = lambda v: v is not None and v > 0
    ok_a = lambda v: v is not None and 0 < v < 0.995
    if not ok_b(bid):
        for c in reversed([c for c in allc if last[0] - 2 * 3600 <= c[0] < last[0]]):
            if ok_b(c[1]):
                bid, flag = c[1], True
                break
    if not ok_a(ask):
        for c in reversed([c for c in allc if last[0] - 2 * 3600 <= c[0] < last[0]]):
            if ok_a(c[2]):
                ask, flag = c[2], True
                break
    if not (ok_b(bid) and ok_a(ask)):
        return None, None, "no_two_sided_quote"
    if ask <= bid:
        return None, None, "crossed"
    if ask - bid > 0.10:
        return None, None, "spread_gt_10c"
    mid = (bid + ask) / 2
    if not (0.02 <= mid <= 0.98):
        return None, None, "mid_out_of_range"
    return bid, ask, flag


def contract(series, bid, ask, y, flag):
    mid = (bid + ask) / 2
    hs = (ask - bid) / 2
    if mid >= 0.5:
        side, ms, gross = "yes", mid, y - mid
    else:
        side, ms, gross = "no", 1 - mid, (1 - y) - (1 - mid)
    cost = taker_entry_cost(series, ms, hs)
    return dict(mid=mid, side=side, gross=gross, cost=cost, net=gross - cost, flag=flag)


def cell(rows, label):
    n = len(rows)
    out = dict(label=label, n=n, games=len({r["g"] for r in rows}))
    if n == 0:
        return out
    ys = [r["net"] for r in rows]
    cl = [r["g"] for r in rows]
    cm = clustered_mean(ys, cl, 0.90)
    out.update(gross=sum(r["gross"] for r in rows) / n, cost=sum(r["cost"] for r in rows) / n, net=cm["mean"],
               se=cm["se"], lo=cm["lo"], hi=cm["hi"], mid=sum(r["mid"] for r in rows) / n,
               win=sum(1 for r in rows if r["gross"] > -r["mid"] * 0 and r["y_side"] == 1) / n)
    out["testable"] = out["games"] >= 30 and n >= 100 and cm["se"] == cm["se"] and cm["se"] > 0
    if out["testable"]:
        out["z"] = cm["mean"] / cm["se"]
        out["p"] = one_sided_p(out["z"])
    else:
        sd = (sum((v - cm["mean"]) ** 2 for v in ys) / max(n - 1, 1)) ** 0.5
        try:
            ic = max(icc(ys, cl), 0.0)
            out["games_needed_1c"] = games_needed(sd, n / out["games"], ic, 0.01)
        except Exception:
            out["games_needed_1c"] = None
    return out


def main(nhl_dir, w89):
    drops, allrows, famnotes = {}, {}, {}
    for name, series, d0, d1, ml in FAMS:
        raw = load(name, series, nhl_dir, w89)
        lo, hi = lim(d0), lim(d1, True)
        dr = {"loaded": len(raw), "outside_season": 0, "void_result": 0}
        rows = []
        for r in raw:
            if not (lo <= r["start"] < hi):
                dr["outside_season"] += 1
                continue
            if r["res"] not in ("yes", "no"):
                dr["void_result"] += 1
                continue
            b, a, fl = close_row(r)
            if b is None:
                dr[fl] = dr.get(fl, 0) + 1
                continue
            y = 1.0 if r["res"] == "yes" else 0.0
            c = contract(series, b, a, y, fl)
            c.update(g=r["event"].split("-", 1)[1], event=r["event"], ticker=r["ticker"], start=r["start"],
                     y_side=(y if c["side"] == "yes" else 1 - y))
            rows.append(c)
        if ml:  # one row per game: the favourite listing (mid >= .5); the longshot listing is the descriptive mirror
            byg = {}
            for c in rows:
                byg.setdefault(c["g"], []).append(c)
            fav, mir = [], []
            for g, L in byg.items():
                L.sort(key=lambda c: (-c["mid"], c["ticker"]))
                fav.append(L[0])
                mir += [c for c in L[1:] if c["mid"] < 0.5]
            dr["games_with_two_listings"] = sum(1 for L in byg.values() if len(L) == 2)
            allrows[name] = dict(test=[c for c in fav if c["mid"] >= 0.5], mirror=mir)
        else:
            allrows[name] = dict(test=rows, mirror=[])
        drops[name] = dr
    cells = []
    for name, series, d0, d1, ml in FAMS:
        for part in ("test", "mirror"):
            for lo_b, hi_b in BUCKETS:
                rr = [c for c in allrows[name][part] if lo_b <= c["mid"] < hi_b]
                if not rr:
                    continue
                if ml and part == "test" and lo_b < 0.5:
                    continue
                if ml and part == "mirror" and lo_b >= 0.5:
                    continue
                for variant in ("all", "no_backfill"):
                    use = rr if variant == "all" else [c for c in rr if not c["flag"]]
                    c = cell(use, f"{name}|{part}|[{lo_b:.2f},{min(hi_b,.98):.2f})|{variant}")
                    c.update(family=name, part=part, bucket=[lo_b, min(hi_b, .98)], variant=variant)
                    if use:
                        ss = sorted(r["start"] for r in use)
                        med = ss[len(ss) // 2]
                        for nm, sel in (("early", [r for r in use if r["start"] < med]), ("late", [r for r in use if r["start"] >= med])):
                            if sel:
                                cm = clustered_mean([r["net"] for r in sel], [r["g"] for r in sel], 0.90)
                                c[nm] = dict(n=len(sel), games=len({r["g"] for r in sel}), net=cm["mean"], lo=cm["lo"], hi=cm["hi"])
                    cells.append(c)
    tested = [c for c in cells if c["part"] == "test" and c["variant"] == "all" and c.get("testable")]
    bh = benjamini_hochberg([c["p"] for c in tested], 0.10) if tested else []
    for c, b in zip(tested, bh):
        c["q"], c["bh_reject"] = b["q"], b["reject"]
    for c in cells:
        if c["part"] != "test" or c["variant"] != "all":
            continue
        if not c.get("testable"):
            c["verdict"] = "UNDERPOWERED"
        elif c["lo"] > 0 and c["bh_reject"]:
            c["verdict"] = "SUPPORTED"
        elif c["lo"] > 0:
            c["verdict"] = "LEAD"
        else:
            c["verdict"] = "NOT SUPPORTED"
    json.dump(dict(drops=drops, cells=cells, n_tested_for_bh=len(tested)), open(safe_out(os.path.join(HERE, "results.json")), "w"), indent=1)
    L = ["| family | part | bucket | variant | n | games | mid | gross | cost | net | 90% interval | verdict | q |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cells:
        if c["n"] == 0:
            continue
        L.append("| {family} | {part} | [{b0:.2f},{b1:.2f}) | {variant} | {n} | {games} | {mid:.3f} | {gross:+.4f} | {cost:.4f} | {net:+.4f} | [{lo:+.4f}, {hi:+.4f}] | {v} | {q} |".format(
            family=c["family"], part=c["part"], b0=c["bucket"][0], b1=c["bucket"][1], variant=c["variant"], n=c["n"], games=c["games"],
            mid=c["mid"], gross=c["gross"], cost=c["cost"], net=c["net"], lo=c["lo"], hi=c["hi"],
            v=c.get("verdict", "descriptive"), q=("%.3f" % c["q"]) if "q" in c else ""))
    L += ["", "drops: " + json.dumps(drops)]
    open(safe_out(os.path.join(HERE, "tables.md")), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
