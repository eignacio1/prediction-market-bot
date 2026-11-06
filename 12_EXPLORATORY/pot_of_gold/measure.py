"""W105.6 Part B runner: pot-of-gold routes on the local price archive + Kalshi settlements. Read-only on inputs.

  python 12_EXPLORATORY/pot_of_gold/measure.py --archive <PRICE_ARCHIVE> --settle <dir> --out 12_EXPLORATORY/pot_of_gold/out
Per (sport, family, tier, bucket, book, route): first two-sided pre-start snapshot per (ticker, tier); 70/30 time-ordered
game split; net per contract at the quote after the exact fee; game-clustered interval; Holm across hold-out cells.
"""
from __future__ import annotations

import argparse, csv, glob, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "longshot_bias"))
import calib as C  # noqa: E402
from prediction_market_bot.quant import longshot_bias as L  # noqa: E402

TIGHT = 0.01
MIN_GAMES_HELD = 20
SPORTS = ("NHL", "NBA", "NFL", "MLB")


def sport_of(series: str) -> str:
    for s in SPORTS:
        if series.startswith("KX" + s):
            return s
    return "OTHER"


def scan(archive):
    first = {}
    for f in sorted(glob.glob(os.path.join(archive, "prices_*.jsonl"))):
        with open(f) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                try:
                    bid, ask = float(r.get("yes_bid")), float(r.get("yes_ask"))
                except (TypeError, ValueError):
                    continue
                if not bid or not ask or ask < bid:
                    continue
                mid = (bid + ask) / 2.0
                if L.pot_bucket(mid) is None:
                    continue
                ev = r["event_ticker"]
                ts = C.parse_ts(r["run_ts"])
                t = C.tier(ev, ts)
                if t is None or t == "D0":
                    continue
                key = (r["ticker"], t)
                if key not in first:
                    first[key] = {"ticker": r["ticker"], "series": r["series_ticker"], "game": ev, "tier": t,
                                  "p": mid, "bid": bid, "ask": ask, "hs": (ask - bid) / 2.0, "ts": ts}
    return list(first.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--settle", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    assert "12_EXPLORATORY" in out, "writes stay inside 12_EXPLORATORY/"
    os.makedirs(out, exist_ok=True)
    settle = C.load_settlements(a.settle)
    snaps = scan(a.archive)
    rows, skipped = [], 0
    for s in snaps:
        y = settle.get(s["ticker"])
        if y is None:
            skipped += 1
            continue
        s["y"] = y
        s["sport"] = sport_of(s["series"])
        s["bucket"] = L.pot_bucket(s["p"])
        s["book"] = "tight" if s["hs"] <= TIGHT else "wide"
        rows.append(s)
    # time-ordered split per sport (by game date)
    fit_games = {}
    for sp in SPORTS:
        gd = {}
        for r in rows:
            if r["sport"] == sp:
                _, d = C.game_start(r["game"])
                gd[r["game"]] = d
        fit_games[sp] = L.split_games(gd, 0.7) if gd else set()
    cells = defaultdict(lambda: {"fit": [], "held": []})
    for r in rows:
        part = "fit" if r["game"] in fit_games[r["sport"]] else "held"
        for book in (r["book"], "all"):
            cells[(r["sport"], r["series"], r["tier"], r["bucket"], book)][part].append(r)
    results = []
    for (sp, fam, t, b, book), parts in sorted(cells.items()):
        sides = ("no", "yes")
        for side in sides:
            low = b in L.LOW_BUCKETS
            route = (L.FADE_LONGSHOT if side == "no" else L.BUY_LONGSHOT) if low else (L.TAKE_FAVOURITE if side == "yes" else L.BUY_LONGSHOT)
            allrows = parts["fit"] + parts["held"]
            ef = L.evaluate_cell(parts["fit"], side, boot=500) if parts["fit"] else {"n": 0, "games": 0}
            eh = L.evaluate_cell(parts["held"], side, boot=500) if parts["held"] else {"n": 0, "games": 0}
            ea = L.evaluate_cell(allrows, side, boot=500)
            results.append({"sport": sp, "family": fam, "tier": t, "bucket": b, "book": book, "route": route, "side": side,
                            "fit": ef, "held": eh, "all": ea})
    # Holm across hold-out cells that were positive in fit and have enough games
    cand = [r for r in results if r["fit"].get("net_mean", -1) > 0 and r["held"].get("games", 0) >= MIN_GAMES_HELD]
    rej = L.holm_one_sided([r["held"]["p_one"] for r in cand]) if cand else []
    holm = {id(r): rj for r, rj in zip(cand, rej)}
    for r in results:
        f, h = r["fit"], r["held"]
        if f.get("n", 0) == 0 or f.get("net_mean", -1) <= 0:
            st = "UNTESTED" if f.get("n", 0) < 30 else "FAILED"
        elif h.get("games", 0) < MIN_GAMES_HELD:
            st = "IN_SAMPLE"
        elif holm.get(id(r)) and h["net_lo"] > 0:
            st = "HELD_OUT"
        elif h["net_mean"] <= 0:
            st = "FAILED"
        else:
            st = "IN_SAMPLE"
        r["status"] = st
    with open(os.path.join(out, "cells.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sport", "family", "tier", "bucket", "book", "route", "side", "status", "fit_n", "fit_games", "fit_net",
                    "held_n", "held_games", "held_net", "held_lo", "held_hi", "held_p", "all_n", "all_games", "all_gap", "all_net", "all_lo"])
        for r in results:
            f, h, a_ = r["fit"], r["held"], r["all"]
            g = lambda d, k: round(d[k], 4) if k in d else ""
            w.writerow([r["sport"], r["family"], r["tier"], r["bucket"], r["book"], r["route"], r["side"], r["status"],
                        f.get("n", 0), f.get("games", 0), g(f, "net_mean"), h.get("n", 0), h.get("games", 0), g(h, "net_mean"),
                        g(h, "net_lo"), g(h, "net_hi"), g(h, "p_one"), a_.get("n", 0), a_.get("games", 0), g(a_, "gap"),
                        g(a_, "net_mean"), g(a_, "net_lo")])
    by = defaultdict(lambda: defaultdict(int))
    for r in results:
        by[r["sport"]][r["status"]] += 1
    summ = {"settled_tickers": len(settle), "snapshots_in_buckets": len(snaps), "joined": len(rows), "unsettled": skipped,
            "games_by_sport": {sp: len({r['game'] for r in rows if r['sport'] == sp}) for sp in SPORTS},
            "holm_candidates": len(cand), "holm_rejected": sum(rej), "status_by_sport": {k: dict(v) for k, v in by.items()}}
    json.dump(summ, open(os.path.join(out, "summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
