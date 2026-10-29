"""EXP-044b live entry: the v2 challenger prices the same board at the same instant and logs beside v1 (EXP-044).

v2 = v1's as-of team means (``ratings``) + an estimated score correlation + a train-only logistic calibration step
(``engine_v2``). Parameters are fit once per run on seasons TRAIN_SEASONS (all before the arm's first game) and hashed
into every row. Closed-form probabilities, no simulation. Reuses ``live`` helpers unchanged; edits nothing in v1.

Places no order, reads no ledger and writes only its own JSONL.
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

from prediction_market_bot.nba_engine import engine_v2 as V, live as L, ratings as R
from prediction_market_bot.pregame_shadow.nba_forecaster import parse_market_ticker

TRAIN_SEASONS = (2024, 2025, 2026)   # the three seasons before the 2026-27 arm, as the held-out study used T-3..T-1
OFFS = (-6, -3, 0, 3, 6)             # strike offsets around each game's own mean, as in the study
OUT_DIR = Path("exp_output/NBA_ENGINE_LIVE_V2")


def _train_rows(p: V.V2Params, g: pd.DataFrame) -> pd.DataFrame:
    """Closed-form raw probability and outcome at strikes around each training game's own v2 mean."""
    rows = []
    for _, r in g.iterrows():
        mu_h, mu_a = r["mu_poss"] * r["ppp_h"] / 100.0, r["mu_poss"] * r["ppp_a"] / 100.0
        m, t = V.game_means(p, mu_h, mu_a)
        mg, tt = r["home_pts"] - r["away_pts"], r["home_pts"] + r["away_pts"]
        rows.append(("ml", m, t, 1, float(mg >= 1)))
        c_m, c_t = int(np.floor(m)) + 1, int(np.floor(t)) + 1
        for o in OFFS:
            rows.append(("spread", m, t, c_m + o, float(mg >= c_m + o)))
            rows.append(("total", m, t, c_t + o, float(tt >= c_t + o)))
        for mm, mean, pts in ((m, (t + m) / 2, r["home_pts"]), (-m, (t - m) / 2, r["away_pts"])):
            c = int(np.floor(mean)) + 1
            for o in OFFS:
                rows.append(("team_total", mm, t, c + o, float(pts >= c + o)))
    d = pd.DataFrame(rows, columns=["family", "m", "t", "n", "y"])
    d["raw"] = [V.raw_prob(p, f, m, t, n) for f, m, t, n in zip(d.family, d.m, d.t, d.n)]
    return d


def fit_frozen(hist: pd.DataFrame, k: float = L.K, seasons=TRAIN_SEASONS) -> V.V2Params:
    """Fit v2 on ``seasons`` of the regular-season history only: level and SDs by out-of-sample residual, Platt per family."""
    g = R.game_inputs(R.add_ratings(hist[hist["season"] <= max(seasons)], k=k))
    g = g[g["season"].isin(seasons)]
    mu_h, mu_a = g["mu_poss"] * g["ppp_h"] / 100.0, g["mu_poss"] * g["ppp_a"] / 100.0
    p = V.fit_params(mu_h.to_numpy(), mu_a.to_numpy(), g["home_pts"].to_numpy(), g["away_pts"].to_numpy())
    d = _train_rows(p, g)
    platt = {f: V.fit_platt(x["raw"].to_numpy(), x["y"].to_numpy()) for f, x in d.groupby("family")}
    return V.with_platt(p, platt)


def params_hash(p: V.V2Params) -> str:
    blob = json.dumps(dict(commit=L.ENGINE_COMMIT, K=L.K, train=list(TRAIN_SEASONS), hca=round(p.hca, 6), tbias=round(p.tbias, 6),
                           sd_margin=round(p.sd_margin, 6), sd_total=round(p.sd_total, 6),
                           platt={f: [round(a, 6), round(b, 6)] for f, (a, b) in sorted(p.platt.items())}), sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def engine_p(p: V.V2Params, m: float, t: float, parsed: dict) -> Optional[float]:
    """Calibrated P(contract resolves YES); None for a ticker the engine does not price. Strike rule as v1 (P(X >= N))."""
    mt, subj, n = parsed["market_type"], parsed["subject"], parsed["strike"]
    home, away = parsed["home"], parsed["away"]
    if mt == "NBA_MONEYLINE":
        ph = V.calibrated(p, "ml", V.raw_prob(p, "ml", m, t, 1))
        return ph if subj == home else 1.0 - ph if subj == away else None
    k = int(round(n + 0.5))
    if mt == "NBA_GAME_TOTAL":
        return V.calibrated(p, "total", V.raw_prob(p, "total", m, t, k))
    fam = "spread" if mt == "NBA_SPREAD" else "team_total"
    if subj == home:
        return V.calibrated(p, fam, V.raw_prob(p, fam, m, t, k))
    if subj == away:
        return V.calibrated(p, fam, V.raw_prob(p, fam, -m, t, k))
    return None


def price_event_rows(event_rows: dict, parsed_by_ticker: dict, tg: pd.DataFrame, team_ids: dict, p: V.V2Params,
                     tip: datetime, now: datetime, pid: str) -> list:
    any_p = next(iter(parsed_by_ticker.values()))
    home, away = any_p["home"], any_p["away"]
    if home not in team_ids or away not in team_ids:
        return []
    cut = pd.Timestamp(tip)
    h = L.team_rating(tg, team_ids[home], L.SEASON, cut)
    a = L.team_rating(tg, team_ids[away], L.SEASON, cut)
    gm = L.game_means(h, a)
    m, t = V.game_means(p, gm["mu_poss"] * gm["ppp_h"] / 100.0, gm["mu_poss"] * gm["ppp_a"] / 100.0)
    rows = []
    for tk, q in event_rows.items():
        pr = parsed_by_ticker[tk]
        pe = engine_p(p, m, t, pr)
        if pe is None or q.get("yes_mid") is None:
            continue
        rows.append(dict(ticker=tk, event_ticker=pr["event_ticker"], family=pr["market_type"], game_date=pr["game_date"],
                         home=home, away=away, subject=pr["subject"],
                         strike_n=None if pr["strike"] is None else int(round(pr["strike"] + 0.5)),
                         p_engine=float(pe), p_market=float(q["yes_mid"]), half_spread=q.get("half_spread"),
                         quote_ts=q["run_ts"], tip_utc=tip.isoformat(), logged_at=now.isoformat(),
                         n_games_home=h["n_prior"], n_games_away=a["n_prior"], engine_version="v2",
                         engine_commit=L.ENGINE_COMMIT, params_hash=pid))
    return rows


def run(raw: str, espn_schedule: pd.DataFrame, current_tg: pd.DataFrame, now: Optional[datetime] = None,
        out_dir: Path = OUT_DIR, archive_dir: Path = L.ARCHIVE_DIR) -> dict:
    """Log rows for every game whose tip - 60 min has passed and that is not yet logged. Idempotent per event."""
    now = now or datetime.now(timezone.utc)
    hist = L.load_history(raw)
    tg = pd.concat([hist, current_tg[current_tg["season_type"] == "regular-season"]], ignore_index=True)
    p = fit_frozen(hist)
    pid = params_hash(p)
    abbr_id = {}
    sched = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{raw}/schedule/*.parquet"))], ignore_index=True)
    for side in ("home", "away"):
        for _, r in sched.drop_duplicates(f"{side}_team_id").iterrows():
            abbr_id[r[f"{side}_team_abbreviation"]] = r[f"{side}_team_id"]
    tips = L.tip_index(espn_schedule)
    out_dir.mkdir(parents=True, exist_ok=True)
    f_out = out_dir / "rows.jsonl"
    done = set()
    if f_out.exists():
        done = {json.loads(l)["event_ticker"] for l in f_out.read_text().splitlines() if l.strip()}
    logged, skipped = 0, []
    for day in sorted({(now + timedelta(days=d)).strftime("%Y-%m-%d") for d in (0, 1)}):
        arch = L.read_archive(day, archive_dir) + L.read_archive((now - timedelta(days=1)).strftime("%Y-%m-%d"), archive_dir)
        by_event = {}
        for r in arch:
            pr = parse_market_ticker(r["ticker"])
            if pr:
                by_event.setdefault(pr["event_ticker"], {})[r["ticker"]] = pr
        for ev, parsed in by_event.items():
            if ev in done:
                continue
            p0 = next(iter(parsed.values()))
            tip = tips.get((p0["game_date"], p0["home"], p0["away"]))
            if tip is None or now < tip - L.LEAD or now >= tip:
                continue
            q = L.quote_at([r for r in arch if r["ticker"] in parsed], tip - L.LEAD)
            q = {t: v for t, v in q.items() if t in parsed}
            if not q:
                skipped.append((ev, "no_quote_at_tip_minus_60"))
                continue
            rows = price_event_rows(q, parsed, tg, abbr_id, p, tip, now, pid)
            with open(f_out, "a") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
            done.add(ev)
            logged += len(rows)
    status = dict(as_of=now.isoformat(), rows_logged_this_run=logged, events_logged_total=len(done), skipped=skipped,
                  params_hash=pid, rho=round(p.rho, 4), hca=round(p.hca, 3))
    (out_dir / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    return status


def main(argv: Optional[list] = None) -> int:
    import argparse
    from prediction_market_bot.c1_signal_ingestion import nba_current_season as C
    ap = argparse.ArgumentParser(description="EXP-044b: log v2 challenger prices at tip-60 beside the Kalshi archive quote.")
    ap.add_argument("--raw", required=True, help="NBA event store root holding schedule/espn_schedule/team_box (<= 2026)")
    ap.add_argument("--current-dir", type=Path, default=C.DEFAULT_OUT)
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
