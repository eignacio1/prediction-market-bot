#!/usr/bin/env python3
"""W129.6 Part B: replay the NFL in-play pricer over recorded games (EXP-NFLINPLAY-001). Read-only; writes one JSON report.

Fit set = 2026 weeks 1-6 (fits s2 only); scored set = 2026 weeks 7-11; market set = 2025 games with KXNFLGAME candles
(moneyline Brier vs the Kalshi mid at the same timestamp, round cost, scoring-play-to-market-move lag).
Data: ESPN core plays + site summary pickcenter, cached as JSON under --cache (default exp_output/NFL_INPLAY_REPLAY, not committed).
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.c1_signal_ingestion import nfl_live_feed as feed  # noqa: E402
from prediction_market_bot.quant import inplay_nfl as q  # noqa: E402

_SB = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
_SUM = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
_KALSHI_ALIAS = {"ARI": "ARI", "WSH": "WAS", "LAR": "LA", "JAC": "JAX"}
SEED = 20261125


def _j(url, params=None):
    js, err = feed._get(url, params, delays=(2, 5))
    if js is None:
        raise RuntimeError(f"{url} {params}: {err}")
    return js


def list_events(season, week, cache: Path):
    f = cache / f"sb_{season}_{week}.json"
    if f.exists():
        return json.loads(f.read_text())
    js = _j(_SB, {"dates": season, "seasontype": 2, "week": week, "limit": 30})
    out = []
    for e in js.get("events", []):
        c = e["competitions"][0]
        if e["status"]["type"]["name"] != "STATUS_FINAL":
            continue
        h = [x for x in c["competitors"] if x["homeAway"] == "home"][0]
        a = [x for x in c["competitors"] if x["homeAway"] == "away"][0]
        out.append({"id": e["id"], "date": e["date"], "week": week, "home_id": h["team"]["id"], "home": h["team"]["abbreviation"],
                    "away": a["team"]["abbreviation"], "hs": int(h["score"]), "as": int(a["score"])})
    f.write_text(json.dumps(out))
    return out


def load_game(ev, cache: Path):
    f = cache / f"g_{ev['id']}.json"
    if f.exists():
        return json.loads(f.read_text())
    plays, err, _ft = feed.fetch_plays(ev["id"])
    if err or not plays:
        return None
    s = _j(_SUM, {"event": ev["id"]})
    pc = (s.get("pickcenter") or [{}])[0]
    g = {"ev": ev, "plays": [feed.normalise(p) for p in plays], "spread": pc.get("spread"), "total": pc.get("overUnder")}
    f.write_text(json.dumps(g))
    time.sleep(0.2)
    return g


def rows_for(g, fixed_ft="2026-01-01T00:00:00Z"):
    ev = g["ev"]
    st = feed.states_from_plays(g["plays"], ev["id"], ev["home_id"], ev["home"], ev["away"], fixed_ft, replay=True)
    return [s for s in st if 0 < s.secs_left_reg <= 3600 and s.period <= 4]


def fit(games, weighted=True):
    rm, mm, rt, mt = [], [], [], []
    for g in games:
        if g["spread"] is None or g["total"] is None:
            continue
        M, T = -float(g["spread"]), float(g["total"])
        fm, ft = g["ev"]["hs"] - g["ev"]["as"], g["ev"]["hs"] + g["ev"]["as"]
        for s in rows_for(g):
            yg = s.yards_to_endzone
            mean = q.margin_mean(s.home_score - s.away_score, s.secs_left_reg, M, s.possession, yg, s.down)
            rm.append(fm - mean); mm.append(s.secs_left_reg / 60)
            tau = s.secs_left_reg / 60
            mu = (s.home_score + s.away_score) + T * tau / 60 + (q.drive_ep(yg, s.down))
            rt.append(ft - mu); mt.append(tau)
    return q.estimate_sigma2(rm, mm, weighted), q.estimate_sigma2(rt, mt, weighted)


def cboot(per_game, b=2000):
    """Game-clustered bootstrap of the mean of per-game (sum, n) pairs."""
    rng = random.Random(SEED)
    n = len(per_game)
    if n == 0:
        return None
    est = []
    for _ in range(b):
        sm = sn = 0.0
        for _i in range(n):
            x, k = per_game[rng.randrange(n)]
            sm += x; sn += k
        est.append(sm / sn if sn else float("nan"))
    est.sort()
    return [est[int(0.025 * b)], est[int(0.975 * b)]]


def score(games, s2m, s2t):
    fam = {k: {"games": {}} for k in ("moneyline", "spread", "total")}
    for g in games:
        if g["spread"] is None or g["total"] is None:
            continue
        ev = g["ev"]
        M, T = -float(g["spread"]), float(g["total"])
        fm, ft = ev["hs"] - ev["as"], ev["hs"] + ev["as"]
        spread_line = M
        for s in rows_for(g):
            mg = s.home_score - s.away_score
            tot = s.home_score + s.away_score
            yg = s.yards_to_endzone
            ps = {
                "moneyline": (q.p_home_win(mg, s.secs_left_reg, M, s2m, s.possession, yg, s.down),
                              q.p_home_win(0, 3600, M, s2m), 1.0 if fm > 0 else (0.5 if fm == 0 else 0.0)),
                "spread": (q.p_margin_gt(mg, s.secs_left_reg, M, s2m, spread_line, s.possession, yg, s.down),
                           q.p_margin_gt(0, 3600, M, s2m, spread_line), 1.0 if fm > spread_line else 0.0),
                "total": (q.p_total_gt(tot, s.secs_left_reg, T, s2t, T, yg, s.down),
                          q.p_total_gt(0, 3600, T, s2t, T), 1.0 if ft > T else 0.0),
            }
            for k, (pm, pb, y) in ps.items():
                a = fam[k]["games"].setdefault(ev["id"], [0.0, 0.0, 0])
                a[0] += (pm - y) ** 2; a[1] += (pb - y) ** 2; a[2] += 1
    out = {}
    for k, v in fam.items():
        gs = list(v["games"].values())
        n = sum(x[2] for x in gs)
        if not n:
            out[k] = {"rows": 0}
            continue
        bm = sum(x[0] for x in gs) / n
        bb = sum(x[1] for x in gs) / n
        out[k] = {"games": len(gs), "rows": n, "brier_model": round(bm, 4), "brier_pregame_const": round(bb, 4),
                  "model_minus_const": round(bm - bb, 4),
                  "model_minus_const_ci95_game_clustered": cboot([(x[0] - x[1], x[2]) for x in gs])}
    return out


def market_set(cache: Path, s2m, store: Path):
    """2025 games with KXNFLGAME candles: Brier vs Kalshi mid, round cost, scoring-play-to-move lag."""
    from prediction_market_bot.analytics import kalshi_history as _kh
    prevailing_quote = lambda tk, t: _kh.prevailing_quote(tk, t, store=store)  # noqa: E731
    evs = []
    for w in range(10, 19):
        try:
            evs += list_events(2025, w, cache)
        except Exception:  # noqa: BLE001
            continue
    res = {"games": 0, "rows": 0, "sq_model": 0.0, "sq_mkt": 0.0, "cost_sum": 0.0, "lags": [], "censored": 0, "per_game": []}
    for ev in evs:
        d = datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone(timezone.utc)
        a, h = (_KALSHI_ALIAS.get(ev["away"], ev["away"]), _KALSHI_ALIAS.get(ev["home"], ev["home"]))
        tk = None
        for dd in (0, -1, 1):
            day = datetime.fromtimestamp(d.timestamp() + dd * 86400, timezone.utc)
            cand = f"KXNFLGAME-{day:%y}{day:%b}{day:%d}".upper() + f"{a}{h}-{h}"
            if prevailing_quote(cand, d.timestamp() + 3 * 3600):
                tk = cand
                break
        if not tk:
            continue
        g = load_game(ev, cache)
        if not g or g["spread"] is None:
            continue
        M = -float(g["spread"])
        y = 1.0 if ev["hs"] > ev["as"] else (0.5 if ev["hs"] == ev["as"] else 0.0)
        sq_m = sq_k = cost = 0.0
        n = 0
        prev_mid = None
        for s in rows_for(g):
            if not s.wallclock_utc:
                continue
            t = datetime.strptime(s.wallclock_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            qt = prevailing_quote(tk, t)
            if not qt or qt[0] is None or qt[1] is None:
                continue
            mid = (qt[0] + qt[1]) / 2
            p = q.p_home_win(s.home_score - s.away_score, s.secs_left_reg, M, s2m, s.possession, s.yards_to_endzone, s.down)
            sq_m += (p - y) ** 2; sq_k += (mid - y) ** 2; cost += (qt[1] - qt[0]) / 2; n += 1
            if s.scoring_play and prev_mid is not None:
                for k in range(1, 31):   # first 1-min candle where the mid has moved >= 3c from the mid at the play
                    q2 = prevailing_quote(tk, t + 60 * k)
                    if q2 and q2[0] is not None and abs((q2[0] + q2[1]) / 2 - mid) >= 0.03:
                        res["lags"].append(60 * k)
                        break
                else:
                    res["censored"] += 1
            prev_mid = mid
        if n:
            res["games"] += 1; res["rows"] += n; res["sq_model"] += sq_m; res["sq_mkt"] += sq_k; res["cost_sum"] += cost
            res["per_game"].append((sq_m - sq_k, n))
    lags = sorted(res["lags"])
    n = res["rows"]
    return {"games": res["games"], "rows": n,
            "brier_model": round(res["sq_model"] / n, 4) if n else None, "brier_kalshi_mid": round(res["sq_mkt"] / n, 4) if n else None,
            "model_minus_kalshi_ci95_game_clustered": cboot(res["per_game"]) if n else None,
            "mean_half_spread_cost": round(res["cost_sum"] / n, 4) if n else None,
            "scoring_play_to_3c_move_s": {"n": len(lags), "median": statistics.median(lags) if lags else None,
                                          "q1": lags[len(lags) // 4] if lags else None, "q3": lags[3 * len(lags) // 4] if lags else None,
                                          "no_move_within_1800s": res["censored"]}}


def _kh_default():
    from prediction_market_bot.analytics import kalshi_history as kh
    return kh.STORE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(ROOT / "exp_output" / "NFL_INPLAY_REPLAY"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--kalshi-store", default=None, help="KALSHI_HISTORY dir (local archive; absent in a fresh worktree)")
    ap.add_argument("--skip-market", action="store_true")
    a = ap.parse_args()
    cache = Path(a.cache); cache.mkdir(parents=True, exist_ok=True)
    fit_g, sc_g = [], []
    for w in range(1, 12):
        for ev in list_events(2026, w, cache):
            g = load_game(ev, cache)
            if g:
                (fit_g if w <= 6 else sc_g).append(g)
    s2m, s2t = fit(fit_g)                     # v2 (sum r^2 / sum tau): the reported estimator
    v1m, v1t = fit(fit_g, weighted=False)     # v1 (mean r^2/tau): the first look, kept for the record
    out = {"exp": "EXP-NFLINPLAY-001", "fit_games": len(fit_g), "scored_games": len(sc_g), "s2_margin_pm": round(s2m, 4), "s2_total_pm": round(s2t, 4),
           "scored": score(sc_g, s2m, s2t),
           "first_look_v1_estimator": {"s2_margin_pm": round(v1m, 4), "s2_total_pm": round(v1t, 4), "scored": score(sc_g, v1m, v1t)}}
    if not a.skip_market:
        out["market_set_2025_moneyline"] = market_set(cache, s2m, Path(a.kalshi_store) if a.kalshi_store else _kh_default())
    out["not_scored"] = "team_total (no free team-total lines); spread/total vs Kalshi (no archive candles)"
    txt = json.dumps(out, indent=1, default=str)
    print(txt)
    if a.out:
        Path(a.out).write_text(txt)


if __name__ == "__main__":
    main()
