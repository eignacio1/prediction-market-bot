#!/usr/bin/env python3
"""H4 (W123.4): adverse selection on real demo fills (Part A) and simulated two-sided quoting (Part B).

Rules are frozen in 12_EXPLORATORY/edge_location/HYPOTHESIS.md section 6 (Addendum A). Read-only; no orders.
Inputs (all local files, paths as args): recs.jsonl (per-order join), archive_compact.tsv.gz, settle/<SERIES>.json.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from prediction_market_bot.quant.money import fee_rate  # noqa: E402

BUCKETS = [(0, 2, "0-2h"), (2, 6, "2-6h"), (6, 24, "6-24h"), (24, 1e9, "24h+")]
TICK = 0.01
MAX_GAP_S = 15 * 60
MIN_GAMES = 20
MIN_REAL_FILLS = 10
SEED = 20261120
DRAWS = 2000


def _ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def bucket(h: float) -> str | None:
    for lo, hi, name in BUCKETS:
        if lo <= h < hi:
            return name
    return None


def game_of(event_ticker: str) -> str:
    return event_ticker.split("-", 1)[1] if "-" in event_ticker else event_ticker


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def cluster_boot(pairs, draws=DRAWS, seed=SEED):
    """pairs: list of (game, value). Resample games with replacement; return (point, lo90, hi90, lo95, hi95, p_one_sided_le0)."""
    by = defaultdict(list)
    for g, v in pairs:
        by[g].append(v)
    games = list(by)
    sums = [(sum(by[g]), len(by[g])) for g in games]
    rng = random.Random(seed)
    stats = []
    for _ in range(draws):
        s = n = 0
        for _ in games:
            a, b = sums[rng.randrange(len(games))]
            s += a
            n += b
        stats.append(s / n if n else 0.0)
    stats.sort()
    q = lambda p: stats[min(draws - 1, int(p * draws))]
    point = sum(v for _, v in pairs) / len(pairs)
    p_le0 = sum(1 for x in stats if x <= 0) / draws
    return point, q(0.05), q(0.95), q(0.025), q(0.975), p_le0


def bh(pvals: dict, q=0.10):
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    cut = -1
    for i, (_, p) in enumerate(items, 1):
        if p <= q * i / m:
            cut = i
    return {k for i, (k, _) in enumerate(items, 1) if i <= cut}


def load_recs(path):
    out = []
    for line in open(path):
        r = json.loads(line)
        if "_note" in r:
            continue
        out.append(r)
    return out


def part_a(recs):
    """Adverse selection: E[won - price | unfilled] - E[won - price | filled], settled orders only."""
    rows = []
    for r in recs:
        if r.get("outcome") != "resolved" or r.get("won") is None:
            continue
        try:
            h = (_ts(r["close_time"]) - _ts(r["ts"])) / 3600.0
        except Exception:
            continue
        b = bucket(h)
        if b is None:
            continue
        rows.append(dict(fam=r["series"], arm=r["arm"], placement=r["placement"], bucket=b, filled=bool(r["filled"]),
                         edge=(1.0 if r["won"] else 0.0) - float(r["price"]), won=1.0 if r["won"] else 0.0,
                         game=game_of(r["event_ticker"]), markout=r.get("markout") or {}))
    return rows


def as_table(rows):
    """AS per (family, bucket) with the pre-registered fallbacks. Returns dict key -> (as, n_fill, level)."""
    def calc(sel):
        f = [x["edge"] for x in sel if x["filled"]]
        u = [x["edge"] for x in sel if not x["filled"]]
        return (mean(u) - mean(f), len(f), len(u)) if f and u else (float("nan"), len(f), len(u))
    fams = sorted({x["fam"] for x in rows})
    pooled_all = calc(rows)
    tab = {}
    for fam in fams:
        fam_rows = [x for x in rows if x["fam"] == fam]
        fam_pool = calc(fam_rows)
        for _, _, b in BUCKETS:
            cell = calc([x for x in fam_rows if x["bucket"] == b])
            if cell[1] >= MIN_REAL_FILLS and not math.isnan(cell[0]):
                tab[(fam, b)] = (cell[0], cell[1], "cell")
            elif fam_pool[1] >= MIN_REAL_FILLS and not math.isnan(fam_pool[0]):
                tab[(fam, b)] = (fam_pool[0], fam_pool[1], "family")
            else:
                tab[(fam, b)] = (pooled_all[0], pooled_all[1], "all-pooled")
    return tab, pooled_all



def a_report(rows):
    """Part A tables: filled vs unfilled win rate, edge (won - price) and mean markouts of fills, by dimension."""
    out = {}
    for dim in ("fam", "arm", "placement", "bucket"):
        groups = defaultdict(list)
        for x in rows:
            groups[x[dim]].append(x)
        tab = []
        for k, xs in sorted(groups.items()):
            f = [x for x in xs if x["filled"]]
            u = [x for x in xs if not x["filled"]]
            mo = {}
            for h in ("h1", "h5", "h30", "close", "settle"):
                v = [x["markout"].get(h) for x in f if x["markout"].get(h) is not None]
                mo[h] = (mean(v), len(v)) if v else (None, 0)
            tab.append(dict(key=k, n_fill=len(f), n_unfill=len(u), win_fill=mean([x["won"] for x in f]) if f else None,
                            win_unfill=mean([x["won"] for x in u]) if u else None,
                            edge_fill=mean([x["edge"] for x in f]) if f else None,
                            edge_unfill=mean([x["edge"] for x in u]) if u else None,
                            games_fill=len({x["game"] for x in f}), markout=mo))
        out[dim] = tab
    return out

def load_settle(d):
    res = {}
    for p in Path(d).glob("*.json"):
        for t, v in json.load(open(p)).items():
            if v.get("result") in ("yes", "no"):
                res[t] = 1.0 if v["result"] == "yes" else 0.0
    return res


def simulate(archive_path, settled, max_gap_s=MAX_GAP_S):
    """Yield one dict per simulated fill. Snapshots grouped per ticker, time-ordered."""
    by = defaultdict(list)
    with gzip.open(archive_path, "rt") as f:
        for line in f:
            p = line.rstrip("\r\n").split("\t")
            if len(p) < 8 or p[2] not in settled:
                continue
            try:
                bid, ask = float(p[4]), float(p[5])
            except ValueError:
                continue
            by[p[2]].append((_ts(p[0]), p[1], p[3], bid, ask, p[7]))
    fills = []
    for tk, snaps in by.items():
        snaps.sort()
        won = settled[tk]
        for i in range(len(snaps) - 1):
            t0, series, ev, bid, ask, close = snaps[i]
            t1, _, _, nbid, nask, _ = snaps[i + 1]
            if t1 - t0 > max_gap_s or t1 <= t0:
                continue
            if not (0 < bid < ask < 1) or round(ask - bid, 4) < 3 * TICK - 1e-9:
                continue
            try:
                h = (_ts(close) - t0) / 3600.0
            except Exception:
                continue
            b = bucket(h)
            if b is None:
                continue
            qb, qa = round(bid + TICK, 4), round(ask - TICK, 4)
            base = dict(fam=series, bucket=b, game=game_of(ev))
            if nask <= qb:
                fills.append({**base, "side": "bid", "price": qb, "gross": won - qb, "fee": fee_rate(series, qb, "maker")})
            if nbid >= qa:
                fills.append({**base, "side": "ask", "price": qa, "gross": qa - won, "fee": fee_rate(series, qa, "maker")})
    return fills


def part_b(fills, as_tab):
    cells = defaultdict(list)
    for x in fills:
        cells[(x["fam"], x["bucket"])].append(x)
    out = []
    pv = {}
    for key, xs in sorted(cells.items()):
        games = {x["game"] for x in xs}
        as_v, as_n, as_lvl = as_tab.get(key, (float("nan"), 0, "none"))
        if math.isnan(as_v):
            as_v, as_lvl = 0.0, "none(0 used)"
        row = dict(fam=key[0], bucket=key[1], fills=len(xs), games=len(games), as_term=as_v, as_n=as_n, as_level=as_lvl)
        if len(games) < MIN_GAMES:
            row["status"] = "UNDERPOWERED"
            row["gross"] = mean([x["gross"] - x["fee"] for x in xs])
        else:
            net = [(x["game"], x["gross"] - x["fee"] - as_v) for x in xs]
            gro = [(x["game"], x["gross"] - x["fee"]) for x in xs]
            row["status"] = "judged"
            row["net"] = cluster_boot(net)
            row["gross_ci"] = cluster_boot(gro)
            pv[key] = row["net"][5]
        out.append(row)
    return out, pv


def verdict(rows, pv):
    judged = [r for r in rows if r["status"] == "judged"]
    if not judged:
        return "UNDERPOWERED", "no family x horizon cell reaches %d games" % MIN_GAMES, set()
    keep = bh(pv)
    win = [r for r in judged if (r["fam"], r["bucket"]) in keep and r["net"][1] > 0]
    if win:
        return "SUPPORTED", "%d cell(s) net > 0, 90%% interval above 0, BH q=0.10 over K=%d" % (len(win), len(judged)), keep
    return "NOT SUPPORTED", "no judged cell has net > 0 with interval excluding 0 after BH (K=%d)" % len(judged), keep


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--recs", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--settle", required=True)
    ap.add_argument("--json-out")
    ap.add_argument("--max-gap-min", type=float, default=MAX_GAP_S / 60)
    a = ap.parse_args(argv)
    rows = part_a(load_recs(a.recs))
    tab, pooled = as_table(rows)
    settled = load_settle(a.settle)
    fills = simulate(a.archive, settled, a.max_gap_min * 60)
    brows, pv = part_b(fills, tab)
    v, why, keep = verdict(brows, pv)
    res = dict(part_a=a_report(rows), max_gap_min=a.max_gap_min, verdict=v, why=why, partA_rows=len(rows), pooled_as=pooled, sim_fills=len(fills), cells=brows,
               as_table={"%s|%s" % k: v_ for k, v_ in tab.items()}, bh_keep=["%s|%s" % k for k in keep])
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
