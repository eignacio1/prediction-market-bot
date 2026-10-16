#!/usr/bin/env python3
"""W80R.2/80P.3 Task 3: NBA pace/efficiency -> the Kalshi NBA totals price (KXNBATOTAL), 2025-26 regular season.
ADR-0075 stage target: interpreted -> applied (a tested path from the fact to a price, against the market).

Rules fixed BEFORE any result was computed (W80R, 2026-10-16):
  Factor. W79.3's pace+efficiency term, point-in-time as of tip (nba_factors.rolling_asof, season-to-date):
    base model  total ~ 1 + base_total                                   (base_total = mean of the teams' ytd totals)
    full model  total ~ 1 + base_total + pace_mean + eff_mean + pace_dev_mean
    both fitted by OLS on 2016-2025 regular seasons ONLY; sigma = full-model residual SD on that fit.
    term = full prediction - base prediction (points) for each 2025-26 game.
  Market. KXNBATOTAL "Over X" (strike_type greater, X = floor_strike), settled, 2025-26 regular season, joined to the
    game on (ET date, away, home) from the event ticker. One market per game: the strike nearest the BASE prediction
    (pre-game information only), ties -> lower strike. Price p = mid of the prevailing 1-minute quote at tip - 60 min
    (tip = tip_latest from the point-in-time tip table), valid iff 0 < bid <= ask < 1.
  Tests (bootstrap over games, B = 2000, seed 20261016, 95% percentile CI):
    REAL       total_2025-26 ~ 1 + pred_base + term over every 2025-26 regular-season game: coef on term.
    PRICED     market-implied mean  mu = X + sigma * Phi^-1(p);  mu ~ 1 + pred_base + term: coef b on term
               = share of the term the price holds (1.0 = fully, in the term's own points).
    RESIDUAL   (y - p) ~ 1 + term/sigma, y = 1 if the market settled yes: slope c = edge left after the price.
  Verdict (ADR-0075 / partnership-loop vocabulary):
    NOT REAL         REAL CI lower bound <= 0
    REAL-NOT-PRICED  REAL lower > 0 and RESIDUAL lower > 0
    REAL-AND-PRICED  REAL lower > 0, PRICED lower > 0, RESIDUAL lower <= 0
    INVISIBLE        REAL lower > 0, PRICED CI spans 0, RESIDUAL lower <= 0
  Modal expectation stated before looking: REAL-AND-PRICED (game totals are the most-attended NBA line; pace/efficiency
  is the first thing any totals model uses).

Usage:  PYTHONPATH=src python3 scripts/nba_totals_applied.py --store <NBA store root> --cache <dir> --out <json>
Public unauthenticated Kalshi GETs only (paced client from scripts/board_survey_sports_store.py). Writes --cache, --out.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

SERIES = "KXNBATOTAL"
SEASON = 2026                     # 2025-26 in the store's season numbering
CUSTODY_FROM = datetime(2026, 8, 1, tzinfo=timezone.utc)
B, SEED = 2000, 20261016  # analyse() uses B; tests pass smaller b where they call boot_coef directly
PRICE_LEAD = timedelta(minutes=60)
WINDOW = timedelta(hours=3)
MONTHS = {m: i for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}
FULL = ["base_total", "pace_mean", "eff_mean", "pace_dev_mean"]


# ---------------------------------------------------------------- pure helpers (tested)
def parse_event(ev: str):
    """KXNBATOTAL-25OCT21HOUOKC -> (date(2025,10,21), 'HOU', 'OKC'); None if it does not parse."""
    try:
        tail = ev.split("-", 1)[1]
        yy, mon, dd, teams = tail[:2], tail[2:5], tail[5:7], tail[7:]
        if len(teams) != 6 or mon not in MONTHS:
            return None
        return datetime(2000 + int(yy), MONTHS[mon], int(dd)).date(), teams[:3], teams[3:]
    except (IndexError, ValueError):
        return None


def norm_cdf_inv(p: float) -> float:
    return statistics.NormalDist().inv_cdf(min(max(p, 1e-6), 1 - 1e-6))


def ols(X: list[list[float]], y: list[float]) -> list[float]:
    """Least squares via normal equations (small k)."""
    k = len(X[0])
    xtx = [[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)]
    xty = [sum(r[i] * yy for r, yy in zip(X, y)) for i in range(k)]
    a = [row[:] + [v] for row, v in zip(xtx, xty)]
    for c in range(k):
        piv = max(range(c, k), key=lambda r: abs(a[r][c]))
        a[c], a[piv] = a[piv], a[c]
        for r in range(k):
            if r != c and a[c][c]:
                f = a[r][c] / a[c][c]
                a[r] = [x - f * z for x, z in zip(a[r], a[c])]
    return [a[i][k] / a[i][i] for i in range(k)]


def boot_coef(rows: list[dict], xcols: list[str], ycol: str, idx: int, b: int = B, seed: int = SEED) -> dict:
    X = [[1.0] + [r[c] for c in xcols] for r in rows]
    y = [r[ycol] for r in rows]
    est = ols(X, y)[idx]
    rng = random.Random(seed)
    sims = []
    n = len(rows)
    for _ in range(b):
        ii = [rng.randrange(n) for _ in range(n)]
        try:
            sims.append(ols([X[i] for i in ii], [y[i] for i in ii])[idx])
        except ZeroDivisionError:
            continue
    sims.sort()
    return {"est": est, "lo": sims[int(0.025 * len(sims))], "hi": sims[int(0.975 * len(sims)) - 1], "n": n}


def verdict(real: dict, priced: dict, resid: dict) -> str:
    if real["lo"] <= 0:
        return "NOT REAL"
    if resid["lo"] > 0:
        return "REAL-NOT-PRICED"
    if priced["lo"] > 0:
        return "REAL-AND-PRICED"
    return "INVISIBLE"


def pick_markets(markets: list[dict], games: dict) -> list[dict]:
    """One market per joined game: strike nearest the base prediction (ties -> lower strike)."""
    by_ev = {}
    for m in markets:
        if m.get("strike_type") != "greater" or m.get("result") not in ("yes", "no") or m.get("floor_strike") is None:
            continue
        key = parse_event(m.get("event_ticker", ""))
        if not key or key not in games:
            continue
        by_ev.setdefault(key, []).append(m)
    out = []
    for key, ms in sorted(by_ev.items()):
        g = games[key]
        best = min(ms, key=lambda m: (abs(float(m["floor_strike"]) - g["pred_base"]), float(m["floor_strike"])))
        out.append({**g, "ticker": best["ticker"], "strike": float(best["floor_strike"]), "y": 1.0 if best["result"] == "yes" else 0.0,
                    "settled": best.get("settlement_ts") or best.get("close_time")})
    return out


def quote_mid(candles: list[dict], ts: int):
    last = None
    for c in sorted(candles, key=lambda c: c["end_period_ts"]):
        if c["end_period_ts"] > ts:
            break
        last = c
    if not last:
        return None
    def f(side):
        s = last.get(side) or {}
        v = s.get("close", s.get("close_dollars"))
        return None if v in (None, "") else float(v)
    b, a = f("yes_bid"), f("yes_ask")
    if b is None or a is None or not (0 < b <= a < 1):
        return None
    return (b + a) / 2


# ---------------------------------------------------------------- data (store + Kalshi)
def build_games(store: Path):
    """Point-in-time game frame 2016-2026 regular season, exactly W79.3's pipeline without its season filter."""
    import pandas as pd
    from prediction_market_bot.c1_signal_ingestion.nba_data_rules import eligible_games, game_quality
    from prediction_market_bot.c1_signal_ingestion.nba_factors import game_frame, rolling_asof, team_game_table
    from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import tip_table
    import nba_factors_first_read as w793
    sch, box, off = w793.load(store, "schedule"), w793.load(store, "team_box"), w793.load(store, "officials")
    espn = w793.load(store, "espn_schedule")
    tips = tip_table(sch, espn)
    q = game_quality(sch.assign(game_id=sch.game_id.astype(str)), box.assign(game_id=box.game_id.astype(str)),
                     off.assign(game_id=off.game_id.astype(str)), tips)
    elig = eligible_games(q)
    tg = team_game_table(sch, box, tips)
    tg = tg[tg.game_id.isin(elig) & (tg.season_type == "regular-season") & tg.season.between(2016, SEASON)].copy()
    tg["net"] = tg["ortg"] - tg["drtg"]
    tg = rolling_asof(tg, cols=("pace", "ortg", "drtg", "total", "net"))
    tg["pace_dev_l10"] = tg["pace_l10"] - tg["pace_ytd"]
    g = game_frame(tg, ["pace_ytd", "ortg_ytd", "drtg_ytd", "total_ytd", "pace_dev_l10"]).reset_index()
    g["base_total"] = (g.h_total_ytd + g.a_total_ytd) / 2
    g["pace_mean"] = (g.h_pace_ytd + g.a_pace_ytd) / 2
    g["eff_mean"] = (g.h_ortg_ytd + g.a_ortg_ytd + g.h_drtg_ytd + g.a_drtg_ytd) / 4
    g["pace_dev_mean"] = (g.h_pace_dev_l10 + g.a_pace_dev_l10) / 2
    s = sch.drop_duplicates("game_id", keep="last").assign(game_id=lambda d: d.game_id.astype(str))
    g = g.merge(s[["game_id", "game_date", "home_team_abbreviation", "away_team_abbreviation"]], on="game_id", how="left")
    g = g.merge(tips[["tip_latest"]], left_on="game_id", right_index=True, how="left")
    return g.dropna(subset=FULL + ["total"])


def fit_models(g) -> dict:
    tr = g[g.season.between(2016, 2025)]
    rows = tr[FULL + ["total"]].to_dict("records")
    bb = ols([[1.0, r["base_total"]] for r in rows], [r["total"] for r in rows])
    bf = ols([[1.0] + [r[c] for c in FULL] for r in rows], [r["total"] for r in rows])
    resid = [r["total"] - (bf[0] + sum(b * r[c] for b, c in zip(bf[1:], FULL))) for r in rows]
    return {"beta_base": bb, "beta_full": bf, "sigma": statistics.pstdev(resid), "n_train": len(rows)}


def season_games(g, m: dict) -> dict:
    out = {}
    for r in g[g.season == SEASON].to_dict("records"):
        pb = m["beta_base"][0] + m["beta_base"][1] * r["base_total"]
        pf = m["beta_full"][0] + sum(b * r[c] for b, c in zip(m["beta_full"][1:], FULL))
        d = r["game_date"]
        d = d.date() if hasattr(d, "date") and not isinstance(d, type(datetime.now().date())) else d
        key = (datetime.fromisoformat(str(d)[:10]).date(), r["away_team_abbreviation"], r["home_team_abbreviation"])
        out[key] = {"game_id": r["game_id"], "pred_base": pb, "term": pf - pb, "total": float(r["total"]),
                    "tip": str(r["tip_latest"])}
    return out


def list_markets(client) -> list[dict]:
    out, seen = [], set()
    for path, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
        cursor = None
        while True:
            j, _ = client.get(path, series_ticker=SERIES, limit=1000, cursor=cursor, **extra)
            for m in j.get("markets") or []:
                if m["ticker"] not in seen:
                    seen.add(m["ticker"]); out.append(m)
            cursor = j.get("cursor") or None
            if not cursor or not j.get("markets"):
                break
    return out


def fetch_candles(client, cache: Path, pick: dict) -> list:
    f = cache / f"{pick['ticker']}.json"
    if f.exists():
        return json.loads(f.read_text())
    import board_survey_sports_store as bs
    tip = datetime.fromisoformat(pick["tip"].replace("Z", "+00:00"))
    if tip.tzinfo is None:
        tip = tip.replace(tzinfo=timezone.utc)
    start, end = int((tip - WINDOW).timestamp()), int(tip.timestamp())
    cs = None
    for path in (f"/historical/markets/{pick['ticker']}/candlesticks", f"/series/{SERIES}/markets/{pick['ticker']}/candlesticks"):
        try:
            j, _ = client.get(path, start_ts=start, end_ts=end, period_interval=1)
            cs = j.get("candlesticks") or []
            if cs:
                break
        except bs.FetchFailed:
            continue
    cs = cs or []
    f.write_text(json.dumps(cs))
    return cs


def analyse(all_games: dict, picks: list[dict], sigma: float) -> dict:
    real = boot_coef(list(all_games.values()), ["pred_base", "term"], "total", 2)
    priced_rows, resid_rows = [], []
    for p in picks:
        if p.get("p") is None:
            continue
        mu = p["strike"] + sigma * norm_cdf_inv(p["p"])
        priced_rows.append({"mu": mu, "pred_base": p["pred_base"], "term": p["term"]})
        resid_rows.append({"r": p["y"] - p["p"], "z": p["term"] / sigma})
    priced = boot_coef(priced_rows, ["pred_base", "term"], "mu", 2)
    resid = boot_coef(resid_rows, ["z"], "r", 1)
    brier_mkt = statistics.mean((p["y"] - p["p"]) ** 2 for p in picks if p.get("p") is not None)
    return {"real": real, "priced": priced, "residual": resid, "brier_market": brier_mkt,
            "n_priced_markets": len(priced_rows), "verdict": verdict(real, priced, resid)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", type=Path, required=True)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pause", type=float, default=0.3)
    a = ap.parse_args(argv)
    import board_survey_sports_store as bs
    a.cache.mkdir(parents=True, exist_ok=True)
    g = build_games(a.store)
    m = fit_models(g)
    games = season_games(g, m)
    client = bs.Client(pause=a.pause)
    mk_file = a.cache / "_markets.json"
    markets = json.loads(mk_file.read_text()) if mk_file.exists() else list_markets(client)
    mk_file.write_text(json.dumps(markets))
    markets = [x for x in markets if x.get("close_time") and
               datetime.fromisoformat(x["close_time"].replace("Z", "+00:00")) < CUSTODY_FROM]
    picks = pick_markets(markets, games)
    for i, p in enumerate(picks):
        tip = datetime.fromisoformat(p["tip"].replace("Z", "+00:00"))
        tip = tip if tip.tzinfo else tip.replace(tzinfo=timezone.utc)
        p["p"] = quote_mid(fetch_candles(client, a.cache, p), int((tip - PRICE_LEAD).timestamp()))
        if i % 100 == 0:
            print(i, len(picks), client.stats(), flush=True)
    res = {"model": m, "n_season_games": len(games), "n_markets_listed": len(markets), "n_picks": len(picks),
           **analyse(games, picks, m["sigma"]),
           "rules": "see module docstring (fixed before results)", "series": SERIES, "season": "2025-26 regular"}
    a.out.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "model"}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
