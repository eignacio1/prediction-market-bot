"""W121.2 EXP-NBAPROPS-001 scorer (spec: PREREG.md, frozen before any outcome was read).
Usage: PYTHONPATH=src python3 score_props.py PRICE_DIR settled.json box.json profiles.json out.json
Builds prop rows (layer-1 market state from the price archive), tags the four player splits (point in time), scores each
(leaf x split leaf) per arm on the later 30% of games (fit on the earlier 70%), game-clustered bootstrap, BH q=0.10."""
import collections, datetime as dt, glob, json, re, sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent.parent))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_ingest import kalshi_code
from prediction_market_bot.decision_trees.filters import nba_props as NP
from prediction_market_bot.quant import retro_route as rr

SER = {"KXNBAPTS": ("NBA_PLAYER_POINTS", "points"), "KXNBAREB": ("NBA_PLAYER_REBOUNDS", "rebounds"),
       "KXNBAAST": ("NBA_PLAYER_ASSISTS", "assists"), "KXNBA3PT": ("NBA_PLAYER_THREES", "threes")}
BANDS = {"T1": (12 * 3600, 48 * 3600), "T2": (4 * 3600, 8 * 3600), "T3": (15 * 60, 60 * 60)}
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
TK = re.compile(r"(KXNBA\w+)-(\d\d)([A-Z]{3})(\d\d)([A-Z]{3})([A-Z]{3})-([A-Z]{3})(.+)-(\d+)$")
ARMS3 = ("RIDE", "FADE", "MOMENTUM")


def ts(s):
    return dt.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp()


def load_snaps(d):
    S = collections.defaultdict(list)
    for f in sorted(glob.glob(d + "/prices_2026-11-*.jsonl")):
        for l in open(f):
            if '"KXNBAPTS"' not in l and '"KXNBAREB"' not in l and '"KXNBAAST"' not in l and '"KXNBA3PT"' not in l:
                continue
            x = json.loads(l)
            if x.get("status") != "active":
                continue
            b, a = float(x["yes_bid"]), float(x["yes_ask"])
            if not (0 < b < a < 1):
                continue
            S[x["ticker"]].append((ts(x["run_ts"]), b, a))
    for v in S.values():
        v.sort()
    return S


def build(snaps, settled, box):
    pl, tdates = collections.defaultdict(list), collections.defaultdict(list)
    for gid, g in box.items():
        d = dt.date.fromisoformat(g["date"])
        for t in g["box"]["players"]:
            code = kalshi_code(t["team"]["abbreviation"])
            tdates[code].append(d)
            ks = t["statistics"][0]["keys"]
            mi = ks.index("minutes")
            for a in t["statistics"][0]["athletes"]:
                st = a.get("stats") or []
                try:
                    m = float(st[mi]) if st and not a.get("didNotPlay") else None
                except ValueError:
                    m = None
                if m and m > 0:
                    pl[(code, a["athlete"]["displayName"])].append((d, m))
    tip = {}
    for tk, v in snaps.items():
        ev = tk.rsplit("-", 2)[0] if tk.count("-") >= 3 else tk
        m = TK.match(tk)
        if m:
            e = (m[1], m[2] + m[3] + m[4] + m[5] + m[6])
            tip[e] = max(tip.get(e, 0), v[-1][0])
    ladder = collections.defaultdict(dict)  # (event, player, series, ts) -> {thr: mid}
    for tk, v in snaps.items():
        m = TK.match(tk)
        if m:
            for t_, b, a in v:
                ladder[(m[1], m[2] + m[3] + m[4] + m[5] + m[6], m[7] + m[8], t_)][int(m[9])] = (b + a) / 2
    prof = json.load(open(sys.argv[4]))
    rows, skip = [], collections.Counter()
    for s in settled:
        m = TK.match(s["ticker"])
        if not m or s["ticker"] not in snaps:
            skip["unparsed_or_no_snapshots"] += 1
            continue
        series, yy, mon, dd, away, home, team, pcode, thr = m[1], int(m[2]), MON[m[3]], int(m[4]), m[5], m[6], m[7], m[8], int(m[9])
        day = dt.date(2000 + yy, mon, dd)
        e = (series, m[2] + m[3] + m[4] + m[5] + m[6])
        t_tip = tip[e]
        name = (s["title"] or "").split(":")[0].strip()
        v = snaps[s["ticker"]]
        mt, stat = SER[series]
        opp = home if team == away else away
        prior = [mm for d, mm in pl.get((team, name), []) if d < day]
        pg = [d for d in tdates[team] if d < day]
        leaves = NP.prop_filters(prof=prof, row_season=2026, team=team, opp=opp, home=home, away=away, stat=stat,
                                 prior_minutes=prior, prev_game=max(pg) if pg else None, game_day=day)
        for band, (lo, hi) in BANDS.items():
            win = [x for x in v if lo <= t_tip - x[0] <= hi]
            if not win:
                skip["no_snapshot_in_" + band] += 1
                continue
            t0, b, a = win[-1]
            old = [x for x in v if x[0] <= t0 - 6 * 3600 and t0 - x[0] <= 18 * 3600]
            mid = (b + a) / 2
            move = mid - (old[-1][1] + old[-1][2]) / 2 if old else None
            lad = ladder[(series, e[1], m[7] + pcode, t0)]
            nxt = [k for k in lad if k > thr]
            gap = mid - lad[min(nxt)] if nxt else None
            if gap is not None and gap < -1e-9:
                skip["ladder_incoherent"] += 1
                continue
            rows.append({"sport": "NBA", "market_type": mt, "band": band, "market_ticker": s["ticker"], "run_id": band,
                         "event_ticker": f"{series}-{e[1]}", "mid": mid, "yes_bid": b, "yes_ask": a, "y": 1.0 if s["result"] == "yes" else 0.0,
                         "ts_utc": t0, "start_time_utc": t_tip, "move": move, "p_yes": None, "splits": leaves,
                         "ladder": None if gap is None else ("tight" if gap < 0.06 else "wide" if gap > 0.20 else "normal")})
    return rows, skip


def cell_stats(rows, fit_g, test_g):
    """-> per-arm fit means, chosen arm, held-out net per game for that arm."""
    fit, test = [r for r in rows if rr.game_id(r) in fit_g], [r for r in rows if rr.game_id(r) in test_g]
    fg = {rr.game_id(r) for r in fit}
    if len(fit) < rr.MIN_FIT_ROWS or len(fg) < rr.MIN_FIT_GAMES:
        return {"thin": True, "fit_rows": len(fit), "fit_games": len(fg)}
    means = {}
    for a in ARMS3:
        v = [n[a] for n in map(rr.arm_nets, fit) if n[a] is not None]
        means[a] = sum(v) / len(v) if v else None
    best = max((a for a in ARMS3 if means[a] is not None), key=lambda a: means[a], default=None)
    arm = best if best and means[best] > 0 else "NO_BET"
    out = {"thin": False, "fit_rows": len(fit), "fit_games": len(fg), "fit_means": means, "arm": arm}
    if arm != "NO_BET":
        by = collections.defaultdict(list)
        for r in test:
            n = rr.arm_nets(r)[arm]
            if n is not None:
                by[rr.game_id(r)].append(n)
        out["test_games"] = len(by)
        out["test_rows"] = sum(len(x) for x in by.values())
        if len(by) >= 2:
            mean, lo, hi, p = rr.boot_ci(by)
            out.update(test_mean=mean, ci_lo=lo, ci_hi=hi, p=p)
    return out


def main(pdir, settled_p, box_p, prof_p, outp):
    snaps = load_snaps(pdir)
    rows, skip = build(snaps, json.load(open(settled_p)), json.load(open(box_p)))
    rr.add_moves  # moves are computed against the snapshot 6h earlier (PREREG), not the previous row
    fit_g, test_g = rr.split_games(rows)
    res = {"rows": len(rows), "games": len({rr.game_id(r) for r in rows}), "fit_games": len(fit_g), "test_games": len(test_g),
           "skip": dict(skip), "coverage": {}, "cells": [], "market_state": []}
    for sp in NP.SPLIT_NAMES:
        ok = sum(1 for r in rows if r["splits"][sp] != "unknown")
        res["coverage"][sp] = {"joined": ok, "total": len(rows), "leaves": dict(collections.Counter(r["splits"][sp] for r in rows))}
    base = collections.defaultdict(list)
    for r in rows:
        base[rr.leaf_key(r)].append(r)
    for k, rs in base.items():
        st = cell_stats(rs, fit_g, test_g)
        res["market_state"].append({"leaf": list(k), **st})
    cells = collections.defaultdict(list)
    for r in rows:
        for sp in NP.SPLIT_NAMES:
            lf = r["splits"][sp]
            if lf != "unknown":
                cells[(sp, lf) + rr.leaf_key(r)].append(r)
    pv = {}
    for k, rs in cells.items():
        st = cell_stats(rs, fit_g, test_g)
        c = {"split": k[0], "split_leaf": k[1], "leaf": list(k[2:]), **st}
        if not st["thin"] and st["arm"] != "NO_BET" and st.get("test_games", 0) >= rr.MIN_TEST_GAMES and "p" in st:
            pv[k] = st["p"]
        res["cells"].append(c)
    rej = rr.bh_reject(pv)
    for c in res["cells"]:
        k = (c["split"], c["split_leaf"]) + tuple(c["leaf"])
        c["bh"] = k in rej
        c["kept"] = bool(not c["thin"] and c["arm"] != "NO_BET" and c.get("test_games", 0) >= rr.MIN_TEST_GAMES and c.get("test_mean", 0) > 0)
        c["why"] = ("kept_earned" if c["bh"] and c["kept"] else "kept_unearned" if c["kept"] else
                    "thin" if c["thin"] else "no_arm_positive_in_fit" if c["arm"] == "NO_BET" else
                    "heldout_games_lt_10" if c.get("test_games", 0) < rr.MIN_TEST_GAMES else "heldout_net_not_positive")
    res["tested_for_bh"] = len(pv)
    json.dump(res, open(safe_out(outp), "w"), indent=1, default=str)
    cnt = collections.Counter(c["why"] for c in res["cells"])
    print("rows", res["rows"], "games", res["games"], "skip", dict(skip))
    print("coverage", {k: f'{v["joined"]}/{v["total"]}' for k, v in res["coverage"].items()})
    print("cells", len(res["cells"]), dict(cnt), "BH tested", len(pv))


if __name__ == "__main__":
    main(*sys.argv[1:6])
