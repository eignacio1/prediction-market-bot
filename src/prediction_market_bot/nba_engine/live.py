"""EXP-044 live entry: price tonight's NBA board from the pinned v1 engine at tip-60 min and log it beside the archive quote.

Thin by design. It calls ``engine.simulate`` / ``board`` / ``ratings`` unchanged (pinned commit cfdc423, PR #363) and the
one ticker parser the EXP-038 arm already uses. It places no order, reads no ledger and writes only its own JSONL.

Strike rule (``quant/ladder.py``): ticker suffix N pays on X > N - 0.5, i.e. P(X >= N) for integer X; the engine's
``p_*_ge(n)`` takes that same N.
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from prediction_market_bot.c1_signal_ingestion import nba_factors as F, nba_point_in_time as P
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import COMPLETION_BUFFER, ESPN_TO_NBA_ABBR
from prediction_market_bot.nba_engine import engine as E, ratings as R
from prediction_market_bot.pregame_shadow.nba_forecaster import parse_market_ticker
from prediction_market_bot.quant.ladder import parse_ts

ENGINE_COMMIT = "cfdc423"      # PR #363, W93.3 — the engine EXP-044 pins
K = 10.0                       # ratings shrinkage; chosen on a calibration season in 93.3 (won every test season)
CAL_SEASON = 2026              # calibration season for the 2026-27 arm
SEASON = 2027
N_SIM = 4000                   # as in the 93.3 held-out score
LEAD = timedelta(minutes=60)
MAX_QUOTE_AGE = timedelta(minutes=45)   # the archive samples about every 20 min; older than this = no quote, row skipped
OUT_DIR = Path("exp_output/NBA_ENGINE_LIVE")
ARCHIVE_DIR = Path("exp_output/PRICE_ARCHIVE")
SERIES = ("KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL", "KXNBATEAMTOTAL")


def load_history(raw: str) -> pd.DataFrame:
    """Team-game table from a rebuilt event store (``<raw>/schedule|espn_schedule|team_box``)."""
    rd = lambda n: pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{raw}/{n}/*.parquet"))], ignore_index=True)
    sch, esp, tb = rd("schedule"), rd("espn_schedule"), rd("team_box")
    tg = F.team_game_table(sch, tb, P.tip_table(sch, esp))
    return tg[tg["season_type"] == "regular-season"].reset_index(drop=True)   # 93.3 scored regular season only


def calibrate(tg: pd.DataFrame, k: float = K, cal_season: int = CAL_SEASON) -> dict:
    """hca, level bias, shape (s_p, s_e) from the calibration season's as-of residuals (copy of the 93.3 ``calibrate``)."""
    g = R.game_inputs(R.add_ratings(tg[tg["season"] <= cal_season], k=k))
    g = g[g["season"] == cal_season]
    mu_h, mu_a = g["mu_poss"] * g["ppp_h"] / 100.0, g["mu_poss"] * g["ppp_a"] / 100.0
    rm = (g["home_pts"] - g["away_pts"]) - (mu_h - mu_a)
    rt = (g["home_pts"] + g["away_pts"]) - (mu_h + mu_a)
    s_p, s_e = E.fit_shape(rm.to_numpy(), rt.to_numpy(), float(g["mu_poss"].mean()), float((mu_h + mu_a).mean()))
    return dict(hca=float(rm.mean()), tbias=float(rt.mean()), s_p=s_p, s_e=s_e, n_cal_games=int(len(g)), K=k)


def team_rating(tg: pd.DataFrame, team_id, season: int, cut: pd.Timestamp, k: float = K) -> dict:
    """As-of rating of one team for a game starting at ``cut``: same formula as ``ratings.add_ratings`` (tested equal)."""
    out = {}
    prev = tg[tg["season"] == season - 1]
    cur = tg[(tg["team_id"] == team_id) & (tg["season"] == season) & ((tg["tip_latest"] + COMPLETION_BUFFER) <= cut)]
    for c in R.STATS:
        p_team = prev.loc[prev["team_id"] == team_id, c]
        prior = float(p_team.mean()) if len(p_team) else float(prev[c].mean())
        out[c] = (float(cur[c].sum()) + k * prior) / (len(cur) + k)
    out["n_prior"] = int(len(cur))
    return out


def game_means(h: dict, a: dict) -> dict:
    return dict(mu_poss=(h["pace"] + a["pace"]) / 2, ppp_h=(h["ortg"] + a["drtg"]) / 2, ppp_a=(a["ortg"] + h["drtg"]) / 2)


def sim_game(row: dict, cal: dict, seed: int) -> E.GameSample:
    adj = cal["tbias"] / 2.0 / (row["mu_poss"] / 100.0)   # 93.3: level bias spread across both teams' ppp
    return E.simulate(row["mu_poss"], row["ppp_h"] + adj, row["ppp_a"] + adj, cal["hca"], cal["s_p"], cal["s_e"], N_SIM, seed)


def engine_p(s: E.GameSample, parsed: dict) -> Optional[float]:
    """P(contract resolves YES) from one sample; None for a ticker the engine does not price."""
    mt, subj, n = parsed["market_type"], parsed["subject"], parsed["strike"]
    home, away = parsed["home"], parsed["away"]
    if mt == "NBA_MONEYLINE":
        p = E.p_moneyline_home(s)
        return p if subj == home else 1.0 - p if subj == away else None
    k = int(round(n + 0.5))
    if mt == "NBA_GAME_TOTAL":
        return E.p_total_ge(s, k)
    if subj == home:
        return E.p_margin_ge(s, k) if mt == "NBA_SPREAD" else E.p_team_total_ge(s, "home", k)
    if subj == away:
        return E.p_away_margin_ge(s, k) if mt == "NBA_SPREAD" else E.p_team_total_ge(s, "away", k)
    return None


def read_archive(day: str, archive_dir: Path = ARCHIVE_DIR) -> list:
    out = []
    for f in sorted(glob.glob(str(archive_dir / f"prices_{day}.jsonl"))):
        with open(f) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("series_ticker") in SERIES:
                    out.append(r)
    return out


def quote_at(rows: list, cutoff: datetime) -> dict:
    """ticker -> latest archive row at or before ``cutoff`` and not older than MAX_QUOTE_AGE."""
    best = {}
    for r in rows:
        ts = parse_ts(r["run_ts"])
        if ts > cutoff or cutoff - ts > MAX_QUOTE_AGE:
            continue
        cur = best.get(r["ticker"])
        if cur is None or ts > cur[0]:
            best[r["ticker"]] = (ts, r)
    return {t: v[1] for t, v in best.items()}


def tip_index(espn_schedule: pd.DataFrame) -> dict:
    """(ET game date, home nba abbr, away nba abbr) -> tip instant (UTC)."""
    e = espn_schedule.copy()
    e["tip"] = pd.to_datetime(e["date"], utc=True, errors="coerce")
    e["et_day"] = e["tip"].dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    out = {}
    for _, r in e.dropna(subset=["tip"]).iterrows():
        key = (r["et_day"], ESPN_TO_NBA_ABBR.get(r["home_abbreviation"], r["home_abbreviation"]),
               ESPN_TO_NBA_ABBR.get(r["away_abbreviation"], r["away_abbreviation"]))
        out[key] = r["tip"].to_pydatetime()
    return out


def frozen_params_hash(cal: dict) -> str:
    blob = json.dumps(dict(commit=ENGINE_COMMIT, K=K, cal_season=CAL_SEASON, n_sim=N_SIM,
                           cal={k: round(v, 6) if isinstance(v, float) else v for k, v in sorted(cal.items())}), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def price_event_rows(event_rows: dict, parsed_by_ticker: dict, tg: pd.DataFrame, team_ids: dict, cal: dict,
                     tip: datetime, now: datetime, seed: int) -> list:
    """Rows for one game: engine p beside the archive quote nearest at or before tip - 60 min. ``now`` is the run time."""
    any_p = next(iter(parsed_by_ticker.values()))
    home, away = any_p["home"], any_p["away"]
    if home not in team_ids or away not in team_ids:
        return []
    cut = pd.Timestamp(tip)
    h = team_rating(tg, team_ids[home], SEASON, cut)
    a = team_rating(tg, team_ids[away], SEASON, cut)
    s = sim_game(game_means(h, a), cal, seed)
    rows = []
    for t, q in event_rows.items():
        p = parsed_by_ticker[t]
        pe = engine_p(s, p)
        if pe is None or q.get("yes_mid") is None:
            continue
        rows.append(dict(ticker=t, event_ticker=p["event_ticker"], family=p["market_type"], game_date=p["game_date"],
                         home=home, away=away, subject=p["subject"], strike_n=None if p["strike"] is None else int(round(p["strike"] + 0.5)),
                         p_engine=float(pe), p_market=float(q["yes_mid"]), half_spread=q.get("half_spread"),
                         quote_ts=q["run_ts"], tip_utc=tip.isoformat(), logged_at=now.isoformat(),
                         n_games_home=h["n_prior"], n_games_away=a["n_prior"], engine_commit=ENGINE_COMMIT))
    return rows


def run(raw: str, espn_schedule: pd.DataFrame, current_tg: pd.DataFrame, now: Optional[datetime] = None,
        out_dir: Path = OUT_DIR, archive_dir: Path = ARCHIVE_DIR) -> dict:
    """Log rows for every game whose tip - 60 min has passed and that is not yet logged. Idempotent per event."""
    now = now or datetime.now(timezone.utc)
    hist = load_history(raw)
    tg = pd.concat([hist, current_tg[current_tg["season_type"] == "regular-season"]], ignore_index=True)
    cal = calibrate(hist)
    pid = frozen_params_hash(cal)
    abbr_id = {}
    sched = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{raw}/schedule/*.parquet"))], ignore_index=True)
    for side in ("home", "away"):
        for _, r in sched.drop_duplicates(f"{side}_team_id").iterrows():
            abbr_id[r[f"{side}_team_abbreviation"]] = r[f"{side}_team_id"]
    tips = tip_index(espn_schedule)
    out_dir.mkdir(parents=True, exist_ok=True)
    f_out = out_dir / "rows.jsonl"
    done = set()
    if f_out.exists():
        done = {json.loads(l)["event_ticker"] for l in f_out.read_text().splitlines() if l.strip()}
    logged, skipped = 0, []
    for day in sorted({(now + timedelta(days=d)).strftime("%Y-%m-%d") for d in (0, 1)}):
        arch = read_archive(day, archive_dir) + read_archive((now - timedelta(days=1)).strftime("%Y-%m-%d"), archive_dir)
        by_event = {}
        for r in arch:
            p = parse_market_ticker(r["ticker"])
            if p:
                by_event.setdefault(p["event_ticker"], {})[r["ticker"]] = p
        for ev, parsed in by_event.items():
            if ev in done:
                continue
            p0 = next(iter(parsed.values()))
            tip = tips.get((p0["game_date"], p0["home"], p0["away"]))
            if tip is None or now < tip - LEAD or now >= tip:
                continue
            q = quote_at([r for r in arch if r["ticker"] in parsed], tip - LEAD)
            q = {t: v for t, v in q.items() if t in parsed}
            if not q:
                skipped.append((ev, "no_quote_at_tip_minus_60"))
                continue
            rows = price_event_rows(q, parsed, tg, abbr_id, cal, tip, now, seed=int(hashlib.sha256(ev.encode()).hexdigest()[:6], 16))
            for r in rows:
                r["params_hash"] = pid
            with open(f_out, "a") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
            done.add(ev)
            logged += len(rows)
    status = dict(as_of=now.isoformat(), rows_logged_this_run=logged, events_logged_total=len(done), skipped=skipped, params_hash=pid)
    (out_dir / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    return status


def main(argv: Optional[list] = None) -> int:
    import argparse
    from prediction_market_bot.c1_signal_ingestion import nba_current_season as C
    ap = argparse.ArgumentParser(description="EXP-044: log v1 engine prices at tip-60 beside the Kalshi archive quote.")
    ap.add_argument("--raw", required=True, help="NBA event store root holding schedule/espn_schedule/team_box (<= 2026)")
    ap.add_argument("--current-dir", type=Path, default=C.DEFAULT_OUT, help="where nba_current_season writes team_game_2027.parquet")
    ap.add_argument("--no-refresh", action="store_true", help="use the current-season table as it is")
    a = ap.parse_args(argv)
    if not a.no_refresh:
        C.refresh(a.current_dir)
    espn, _ = C.fetch("espn_schedule")
    cur = pd.read_parquet(a.current_dir / f"team_game_{C.SEASON}.parquet")
    print(json.dumps(run(a.raw, espn, cur), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
