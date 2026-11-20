"""W122.4 Part A: the MLB board priced from one engine; back-test 2025+2026 regular seasons; market gap on the archive window.

usage: PYTHONPATH=src python 12_EXPLORATORY/mlb_engine/run_w122_4.py [store_root] [archive_glob]
Train: seasons before 2025 (2025 tests are scored by a model fitted on <2025; 2026 by <2026 incl. 2025). Per family: Brier/log
loss of model vs naive (train frequency) on every rung, game-clustered bootstrap CIs. Market gap only where the Kalshi archive
has a last pre-game quote (>=10 min before first pitch): 2026-08-04 on. Lineups are as-played (probable starters are the
live input); that is a stated limit of this back-test, not hidden. Writes RESULTS_W122_4.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.mlb_engine import board as bd
from prediction_market_bot.mlb_engine import lineup_aware as la
from prediction_market_bot.mlb_engine import market_line as mk
from prediction_market_bot.mlb_engine import model_lineup as ml

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "mlb_store"
ARCH = sys.argv[2] if len(sys.argv) > 2 else "exp_output/PRICE_ARCHIVE/prices_*.jsonl"
T = ROOT / "tables"
FAMS = ("moneyline", "total", "spread", "team_total")


def stack(b, d_train_freq, fam):
    """Long table of (game_pk, side, k, p, y, naive) for every rung of a family from a priced board."""
    rows = []
    for side in ("home", "away"):
        for k in bd.rungs(fam):
            col = bd.column(fam, side, k)
            if col is None or col not in b:
                continue
            y = bd.realized(b, fam, side, k)
            p = b[col].to_numpy()
            if fam == "moneyline":
                pass
            rows.append(pd.DataFrame({"game_pk": b.game_pk, "game_date": b.game_date, "side": side, "k": k, "p": p, "y": y}))
            if fam in ("total", "moneyline"):
                break  # total rungs are side-free; moneyline home only
    return pd.concat(rows, ignore_index=True)


def main():
    t = {k: pd.read_parquet(T / f"{k}.parquet") for k in ("pitches", "pa", "games", "lineups")}
    pa = t["pa"]
    out = {"calibration": {}, "market": {}}
    for season, train_before in ((2025, "2025-01-01"), (2026, "2026-01-01")):
        tr_mask = pa["game_date"] < train_before
        mu = float(pa[tr_mask].woba_value.sum() / pa[tr_mask].woba_denom.sum())
        d = la.design_lineup(t["games"], t["lineups"], pa, t["pitches"], mu)
        yr = pd.to_datetime(d.game_date).dt.year
        train, test = d[d.game_date < train_before], d[(yr == season)]
        m = ml.RunModel(la.LINEUP_FEATURES).fit(train)
        b = bd.price_board(m, test)
        trb = bd.price_board(ml.RunModel(["is_home"]).fit(train), train)  # naive = train frequency per rung
        for fam in FAMS:
            s, sn = stack(b, None, fam), stack(trb, None, fam)
            naive = sn.groupby(["side", "k"]).y.mean().reset_index(name="naive")
            s = s.merge(naive, on=["side", "k"], how="left")
            out["calibration"][f"{season}/{fam}"] = {
                "n_games": int(b.shape[0]), "n_rung_obs": int(len(s)),
                "brier_model": ml.brier(s.p.to_numpy(), s.y.to_numpy()), "brier_naive": ml.brier(s.naive.to_numpy(), s.y.to_numpy()),
                "logloss_model": ml.logloss(s.p.to_numpy(), s.y.to_numpy()), "logloss_naive": ml.logloss(s.naive.to_numpy(), s.y.to_numpy()),
                "gain_vs_naive_brier_ci": ml.boot_gain(s.p.to_numpy(), s.naive.to_numpy(), s.y.to_numpy(), "brier"),
                "mean_p": float(s.p.mean()), "mean_y": float(s.y.mean())}
            print(season, fam, out["calibration"][f"{season}/{fam}"])
        if season == 2026:
            g = t["games"][["game_pk", "game_date", "home_team", "away_team"]]
            dup = g.duplicated(["game_date", "home_team", "away_team"], keep=False)
            g = g[~dup & (g.game_date >= "2026-01-01")]
            c = mk.last_pregame(ARCH, series=("KXMLBGAME", "KXMLBTOTAL", "KXMLBSPREAD", "KXMLBTEAMTOTAL"))
            out["archive_contracts"] = int(len(c))
            bb = b.merge(g, on=["game_pk"], suffixes=("", "_g"))
            ml_m = mk.moneyline(c)
            j = ml_m.merge(bb, left_on=["game_date", "home", "away"], right_on=["game_date", "home_team", "away_team"])
            y = bd.realized(j, "moneyline", "home", 0)
            out["market"]["moneyline"] = _cmp(j.p_home_ml.to_numpy(), j.p_home_mkt.to_numpy(), y)
            for fam, series in (("total", "KXMLBTOTAL"), ("spread", "KXMLBSPREAD"), ("team_total", "KXMLBTEAMTOTAL")):
                out["market"][fam] = _rung_market(c, series, fam, bb)
    safe_out(Path(__file__).parent / "RESULTS_W122_4.json").write_text(json.dumps(out, indent=1, default=float))


def _cmp(p, pm, y):
    return {"n": int(len(y)), "brier_model": ml.brier(p, y), "brier_market": ml.brier(pm, y),
            "logloss_model": ml.logloss(p, y), "logloss_market": ml.logloss(pm, y),
            "gain_vs_market_brier": ml.boot_gain(p, pm, y, "brier"), "mean_p": float(np.mean(p)), "mean_mkt": float(np.mean(pm)),
            "mean_y": float(np.mean(y))}


def _rung_market(c, series, fam, bb):
    r = mk.team_rungs(c, series) if fam != "total" else _total(c)
    if r.empty:
        return {"n": 0}
    rows = []
    for _, x in r.iterrows():
        side = "total" if fam == "total" else ("home" if x.team == x.home else "away" if x.team == x.away else None)
        if side is None:
            continue
        gm = bb[(bb.game_date == x.game_date) & (bb.home_team == x.home) & (bb.away_team == x.away)]
        if len(gm) != 1:
            continue
        gm = gm.iloc[0]
        k = int(x.k)
        col = bd.column(fam, "home" if side == "total" else side, k)
        if col not in gm.index or pd.isna(gm[col]):
            continue
        y = bd.realized(pd.DataFrame([gm]), fam, "home" if side == "total" else side, k)[0]
        rows.append({"p": float(gm[col]), "mkt": float(x.mid), "y": y, "hs": float(x.hs), "k": k})
    df = pd.DataFrame(rows)
    if df.empty:
        return {"n": 0}
    o = _cmp(df.p.to_numpy(), df.mkt.to_numpy(), df.y.to_numpy())
    o["mid_vs_outcome_by_k"] = df.groupby("k").agg(n=("y", "size"), mkt=("mkt", "mean"), y=("y", "mean"), model=("p", "mean")).round(3).to_dict("index")
    return o


def _total(c):
    t = c[c.series == "KXMLBTOTAL"].copy()
    t["k"] = t.side.astype(int)
    t["mid"] = (t.bid + t.ask) / 2
    t["hs"] = (t.ask - t.bid) / 2
    return t


if __name__ == "__main__":
    main()
