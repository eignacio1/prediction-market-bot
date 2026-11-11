"""W109.1 Part C: one applied path end to end -- factor -> filter -> tree -> a price for KXNBAGAME (moneyline), scored held-out
against the Kalshi pre-game price. Test season 2026 (= 2025-26; Kalshi NBA game markets start 2025-10).

Run: PYTHONPATH=src python3 12_EXPLORATORY/nba_arch_w109/applied_path.py <NBA_EVENTS raw> <w89_7/nba dir> <out json inside 12_EXPLORATORY/>
Protocol = study_v3 (K on season T-1; v2 params on in-coverage T-3..T-1; Platt on training predictions only; season T unseen).
Tree prices: T1 (20h to tip: ratings only, params fit WITHOUT lineup factors) and T3 (1h to tip: + lineup/availability, params fit
WITH them). Market = mid of the last hourly candle ending <= start - 1h (the T3 decision time), flipped to the home side; rows
whose market outcome disagrees with the game outcome are dropped and counted. Filter: lineup-driven shift |m_T3 - m_T1| vs its
own training-season distribution (the gate: only a game whose lineup news is in the tail is a candidate bet).
No demo fills or P&L epoch is read: historical Kalshi quotes only. Net = flat 1 contract at the quote, BEFORE fees.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
EX = HERE.parent
for d in ("nba_board", "nba_engine_live", "nba_engine_v3", ""):
    sys.path.insert(0, str(EX / d))
import study_a as SA  # noqa: E402
import study_v3 as S3  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nba_engine import decision_tree as D, ratings as R  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_forecaster import parse_market_ticker  # noqa: E402
from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402

T = 2026
LEAD_S = 3600
THRESHOLDS = (0.02, 0.05, 0.10)


def quotes(kdir: Path):
    """One ticker per event; keeps all candles -- the cut is applied against the game's tip time (the engine's tip_earliest)."""
    out = {}
    for line in (kdir / "candles" / "KXNBAGAME.jsonl").open():
        r = json.loads(line)
        pt = parse_market_ticker(r["ticker"])
        if not pt or r["event_ticker"] in out:
            continue
        out[r["event_ticker"]] = dict(result=r["result"], home=pt["home"], away=pt["away"], date=pt["game_date"],
                                      listed=pt["subject"], candles=r["candles"])
    return out


def _close(c, side):
    d = c.get(side) or {}
    return d.get("close_dollars") or d.get("close")  # the file carries `close`; some pulls carry `close_dollars`


def last_quote(candles, cut):
    best = None
    for c in candles:
        if c["end_period_ts"] <= cut and _close(c, "yes_bid") and _close(c, "yes_ask"):
            best = c
    return best


def main(raw, kdir, out):
    kdir = Path(kdir)
    tg = SA.load(raw)
    tg = tg[tg.season_type == "regular-season"]
    F = pd.read_parquet(os.environ.get("V3_FACTORS") or EX / "nba_engine_v3" / "v3_factors.parquet")  # untracked build artifact; see factors_frame.py
    F = F[F.season >= 2023].dropna(subset=S3.COLS)
    best = None
    for k in SA.KS:
        g = R.game_inputs(R.add_ratings(tg[tg.season <= T - 1], k=k))
        g = g[g.season == T - 1]
        mu_h, mu_a = SA.reg_means(g)
        mse = float(np.mean(((g.home_pts - g.away_pts) - (mu_h - mu_a)) ** 2) + np.mean(((g.home_pts + g.away_pts) - (mu_h + mu_a)) ** 2))
        if best is None or mse < best[1]:
            best = (k, mse)
    k = best[0]
    gall = R.game_inputs(R.add_ratings(tg[tg.season <= T], k=k))
    gall = gall[gall.index.astype(str).isin(F.index)]
    gt, gtr = gall[gall.season == T], gall[gall.season.between(T - 3, T - 1)]
    p_core, c_core = S3.train_variant(gtr, F, S3.VARIANTS["v2_core"])
    p_all, c_all = S3.train_variant(gtr, F, S3.VARIANTS["v3_all"])

    sch = pd.concat([pd.read_parquet(f) for f in sorted((Path(raw) / "schedule").glob("*.parquet"))])
    from prediction_market_bot.c1_signal_ingestion.nba_ingest import ESPN_TO_KALSHI
    ab = {}
    for r in sch.itertuples():
        ab[int(r.home_team_id)] = ESPN_TO_KALSHI.get(r.home_team_abbreviation, r.home_team_abbreviation)
        ab[int(r.away_team_id)] = ESPN_TO_KALSHI.get(r.away_team_abbreviation, r.away_team_abbreviation)

    def tree_row(gid, r, hours, p, centers, names):
        x = centers.apply({c: float(F.at[str(gid), c]) for c in names}) if names else {}
        mu_h, mu_a = r["mu_poss"] * r["ppp_h"] / 100.0, r["mu_poss"] * r["ppp_a"] / 100.0
        return D.price(p, "ml", mu_h, mu_a, x, hours)

    rows = []
    for gid, r in gt.iterrows():
        a = tree_row(gid, r, 20.0, p_core, c_core, [])
        b = tree_row(gid, r, 1.0, p_all, c_all, S3.COLS)
        rows.append(dict(game_id=str(gid), home=ab.get(int(r.home_team)), away=ab.get(int(r.away_team)),
                         tip=pd.Timestamp(r.tip_earliest), y=float(r.home_pts > r.away_pts), p_t1=a.p, p_t3=b.p, m_t1=a.m, m_t3=b.m,
                         used=",".join(b.used)))
    G = pd.DataFrame(rows)
    G["date"] = G.tip.dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    q = quotes(kdir)
    drop, joined = {}, []
    for ev, v in q.items():
        m = G[(G.home == v["home"]) & (G.away == v["away"]) & (G.date == v["date"])]
        if len(m) != 1:
            kk = "no_game_match" if m.empty else "ambiguous"
            drop[kk] = drop.get(kk, 0) + 1
            continue
        g = m.iloc[0]
        c = last_quote(v["candles"], int(g.tip.timestamp()) - LEAD_S)
        if c is None:
            drop["no_pre_game_quote"] = drop.get("no_pre_game_quote", 0) + 1
            continue
        home_listed = v["listed"] == v["home"]
        y_mkt = float(v["result"] == "yes") if home_listed else float(v["result"] == "no")
        if y_mkt != g.y:
            drop["outcome_disagrees"] = drop.get("outcome_disagrees", 0) + 1
            continue
        yb, ya = float(_close(c, "yes_bid")), float(_close(c, "yes_ask"))
        bid, ask = (yb, ya) if home_listed else (1 - ya, 1 - yb)
        joined.append(dict(g, bid=bid, ask=ask, mid=(bid + ask) / 2, spread=ask - bid))
    J = pd.DataFrame(joined)
    res = dict(test_season=T, K=k, n_train=int(len(gtr)), n_test_with_factors=int(len(gt)), n_scored=int(len(J)), dropped=drop)
    if J.empty:
        safe_out(EX / out).write_text(json.dumps(res, indent=1, default=float))
        print(res)
        return
    J["shift"] = (J.m_t3 - J.m_t1).abs()
    # filter gate calibrated on TRAINING games only: top-decile |lineup shift| under the fitted p_all
    tr_shift = []
    for gid, r in gtr.iterrows():
        mu_h, mu_a = r["mu_poss"] * r["ppp_h"] / 100.0, r["mu_poss"] * r["ppp_a"] / 100.0
        x = c_all.apply({c: float(F.at[str(gid), c]) for c in S3.COLS})
        tr_shift.append(abs(sum(c * x.get(f, 0.0) for f, c in p_all.shift_margin.items())))
    gate = float(np.quantile(tr_shift, 0.90))
    J["gated"] = J["shift"] >= gate
    res["gate_shift_pts_train_p90"] = gate

    def brier_block(d):
        out_ = {"n": int(len(d))}
        for c in ("p_t1", "p_t3", "mid"):
            out_["brier_" + c] = float(((d[c] - d.y) ** 2).mean())
        for a, b in (("p_t3", "mid"), ("p_t1", "mid"), ("p_t3", "p_t1")):
            diff = ((d[a] - d.y) ** 2 - (d[b] - d.y) ** 2).to_numpy()
            mean, lo, hi = cluster_bootstrap({str(i): [x] for i, x in zip(d.game_id, diff)})
            out_[f"{a}_minus_{b}"] = dict(delta=mean, lo=lo, hi=hi)
        return out_

    res["brier_all"] = brier_block(J)
    res["brier_gated"] = brier_block(J[J.gated]) if J.gated.sum() >= 20 else dict(n=int(J.gated.sum()), note="below 20, not scored")
    res["median_spread"] = float(J.spread.median())

    def net(d, col, thr):
        pnl, n = [], []
        for r in d.itertuples():
            p = getattr(r, col)
            if p - r.ask > thr:
                pnl.append((r.y - r.ask, r.game_id))
            elif r.bid - p > thr:
                pnl.append(((1 - r.y) - (1 - r.bid), r.game_id))
        if not pnl:
            return dict(bets=0)
        mean, lo, hi = cluster_bootstrap({gid: [v] for v, gid in pnl})
        return dict(bets=len(pnl), mean_pnl_per_contract=mean, lo=lo, hi=hi, hit=float(np.mean([v > 0 for v, _ in pnl])))

    res["net_before_fees"] = {f"{col}@{thr}": net(J if scope == "all" else J[J.gated], col, thr)
                              for scope in ("all", "gated") for col in ("p_t3",) for thr in THRESHOLDS
                              for col in (col,) if True} if False else {
        f"{scope}/{col}@{thr}": net(J if scope == "all" else J[J.gated], col, thr)
        for scope in ("all", "gated") for col in ("p_t3", "p_t1") for thr in THRESHOLDS}
    safe_out(EX / out).write_text(json.dumps(res, indent=1, default=float))
    J.drop(columns=["tip"]).to_csv(safe_out(EX / out[: -len(".json")] + "_rows.csv.gz"), index=False)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
