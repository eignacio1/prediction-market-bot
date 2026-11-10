"""W105.4 (B-053) analysis runner. Rules are the frozen Part 1 of RIDE_BOARD_PREREGISTRATION_2026-11-06.md.
Usage: python3 analyze.py compact_quotes.tsv.gz out.json   (out must lie inside 12_EXPLORATORY/, enforced by safe_out)
Input columns: epoch, series, event, ticker, yes_mid, yes_bid, yes_ask (bid/ask blank when absent).
"""
import collections
import gzip
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant.inference import cluster_bootstrap, pooled_cluster_test
from prediction_market_bot.quant.multiplicity import holm
from prediction_market_bot.quant.price_dynamics import big_move_events, move_sigma, moves, settle_proxy
from prediction_market_bot.quant.ride_net import net_pnl, quote_at, split_games

K = 3.0
MAX_GAP, REFRACT, H60, TOL60 = 1800.0, 3600.0, 3600.0, 600.0
MIN_GAMES = 15
TIGHT = 0.01
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
DATE_RE = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})")


def ticker_date(event):
    m = DATE_RE.search(event)
    if not m or m.group(2) not in MON:
        return None
    return datetime(2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)), tzinfo=timezone.utc).date()


def fnum(x):
    return float(x) if x not in ("", None) else None


def load(path):
    data = collections.defaultdict(lambda: collections.defaultdict(list))  # series -> ticker -> rows
    with gzip.open(path, "rt") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 7:
                continue
            try:
                data[p[1]][p[3]].append((float(p[0]), float(p[4]), fnum(p[5]), fnum(p[6]), p[2]))
            except ValueError:
                continue
    return data


def summarize(by_game, rule_key):
    """by_game: game -> list of values. Returns dict with n, games, mean, lo, hi, p_one_sided(mean<=0)."""
    vals = {g: v for g, v in by_game.items() if v}
    if not vals:
        return {"n": 0, "games": 0}
    mean, lo, hi = cluster_bootstrap(vals)
    r = {"n": sum(len(v) for v in vals.values()), "games": len(vals), "mean": mean, "lo": lo, "hi": hi}
    r["p"] = pooled_cluster_test([(g, x) for g, v in vals.items() for x in v])["p_one_sided"]
    return r


def main(src, dst):
    data = load(src)
    out = {"params": {"k": K, "max_gap_s": MAX_GAP, "refractory_s": REFRACT, "exit_s": H60, "tol_s": TOL60,
                      "tight_half_spread": TIGHT}, "families": {}}
    for fam in sorted(data):
        tick = {tk: sorted(rows) for tk, rows in data[fam].items()}
        ev_of = {tk: rows[0][4] for tk, rows in tick.items()}
        first = {}
        for tk, rows in tick.items():
            g = ev_of[tk]
            first[g] = min(first.get(g, rows[0][0]), rows[0][0])
        fit, held = split_games(first)
        mid = {tk: [(t, m) for t, m, _, _, _ in rows] for tk, rows in tick.items()}
        quotes = {tk: [(t, b, a) for t, _, b, a, _ in rows] for tk, rows in tick.items()}
        qd = {tk: {t: (t, b, a) for t, b, a in q} for tk, q in quotes.items()}
        sigma = move_sigma([d for tk, s in mid.items() if ev_of[tk] in fit for _, d, _ in moves(s, MAX_GAP)])
        # cells[(split,rule,book,exit)] -> game -> [values]
        cells = collections.defaultdict(lambda: collections.defaultdict(list))
        dropped = collections.Counter()
        n_ev = collections.Counter()
        for tk, s in mid.items():
            g = ev_of[tk]
            split = "fit" if g in fit else "held"
            ev_date = ticker_date(g)
            sp = settle_proxy(s)
            for e in big_move_events(s, K, sigma, MAX_GAP, REFRACT, [], TOL60, settle=False):
                if not (0.05 <= e["price"] - e["move"] <= 0.95):
                    continue
                n_ev[split] += 1
                entry = qd[tk].get(e["t"])
                exit_q = quote_at(quotes[tk], e["t"] + H60, TOL60)
                sign = 1.0 if e["move"] > 0 else -1.0
                for rule in ("FADE", "FOLLOW"):
                    r = net_pnl(fam, sign, rule, entry, exit_q, sp, ev_date)
                    if r is None:
                        dropped[(split, "no_entry_quote")] += 1
                        continue
                    for book in ("all", "tight") if r["half_spread"] <= TIGHT else ("all",):
                        if "net60" in r:
                            cells[(split, rule, book, "net60")][g].append(r["net60"])
                        if "netset" in r:
                            cells[(split, rule, book, "netset")][g].append(r["netset"])
        rec = {"sigma_fit": sigma, "n_games": {"fit": len(fit), "held": len(held)},
               "n_events": dict(n_ev), "dropped": {f"{a}:{b}": c for (a, b), c in dropped.items()}, "cells": {}}
        for (split, rule, book, ex), bg in sorted(cells.items()):
            rec["cells"].setdefault(f"{rule}|{book}|{ex}", {})[split] = summarize(bg, None)
        out["families"][fam] = rec
        print(fam, dict(n_ev), flush=True)
    # primary Holm: held-out, all-books, 60-min, both rules, families with >= MIN_GAMES held-out games
    keys = [(f, r) for f, rec in out["families"].items() for r in ("FADE", "FOLLOW")
            if rec["cells"].get(f"{r}|all|net60", {}).get("held", {}).get("games", 0) >= MIN_GAMES]
    ps = [out["families"][f]["cells"][f"{r}|all|net60"]["held"]["p"] for f, r in keys]
    for (f, r), h in zip(keys, holm(ps, 0.05) if ps else []):
        out["families"][f]["cells"][f"{r}|all|net60"]["held"]["p_holm"] = h["p_adj"]
        out["families"][f]["cells"][f"{r}|all|net60"]["held"]["holm_reject"] = h["reject"]
    out["primary_tests"] = len(keys)
    json.dump(out, open(safe_out(dst), "w"), indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
