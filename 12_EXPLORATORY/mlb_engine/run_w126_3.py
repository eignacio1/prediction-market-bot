"""W126.3 Part C (EXP-MLBSIM-001, PREREG_W126_3.md): the PA-level joint simulation scored on the held-out 2026 season.

usage: PYTHONPATH=src python 12_EXPLORATORY/mlb_engine/run_w126_3.py [store_root] [archive_glob] [n_draws]
League rates frozen on PA < 2026-01-01. Report only: calibration per family vs naive and vs the W122.4 independent-NB board; market gap
(Kalshi mid as BENCHMARK) on the archive window. Writes RESULTS_W126_3.json."""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.mlb_engine import board as bd  # noqa: E402
from prediction_market_bot.mlb_engine import joint_board as jb  # noqa: E402
from prediction_market_bot.mlb_engine import market_line as mk  # noqa: E402
from prediction_market_bot.mlb_engine import model_lineup as ml  # noqa: E402
from prediction_market_bot.mlb_engine import pa_model as pm  # noqa: E402

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "mlb_store"
ARCH = sys.argv[2] if len(sys.argv) > 2 else "exp_output/PRICE_ARCHIVE/prices_*.jsonl"
NDRAW = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
T = ROOT / "tables"
FAMS = ("moneyline", "total", "spread", "team_total")
SPLIT = "2026-01-01"


def _chunk(inp, lo, hi):
    return {k: v[lo:hi] for k, v in inp.items()}


def _price(args):
    inp, seed = args
    return jb.price_games(inp, n=NDRAW, seed=seed)


def price_parallel(inp, workers=7, parts=28):
    G = len(inp["game_pk"])
    edges = np.linspace(0, G, parts + 1).astype(int)
    jobs = [(_chunk(inp, edges[i], edges[i + 1]), 1000 + i) for i in range(parts)]
    with ProcessPoolExecutor(workers) as ex:
        return pd.concat(list(ex.map(_price, jobs)), ignore_index=True)


def long_family(b, fam):
    rows = []
    for side in ("home", "away"):
        for k in bd.rungs(fam):
            col = bd.column(fam, side, k)
            if col is None or col not in b:
                continue
            rows.append(pd.DataFrame({"game_pk": b.game_pk, "side": side, "k": k, "p": b[col].to_numpy(),
                                      "y": bd.realized(b, fam, side, k)}))
            if fam in ("total", "moneyline"):
                break
    return pd.concat(rows, ignore_index=True)


def gains(s, base_col):
    p, q, y = s.p.to_numpy(), s[base_col].to_numpy(), s.y.to_numpy()
    return {"n_obs": int(len(s)), "brier_model": ml.brier(p, y), f"brier_{base_col}": ml.brier(q, y),
            "logloss_model": ml.logloss(p, y), f"logloss_{base_col}": ml.logloss(q, y),
            "gain_brier_ci": ml.boot_gain(p, q, y, "brier"), "gain_logloss_ci": ml.boot_gain(p, q, y, "logloss"),
            "mean_p": float(p.mean()), "mean_y": float(y.mean())}


def hits_frame(inp, pa, b):
    """Long table of batter-hit rungs: p from the sim, y = that batter's hits in that game (PA table), naive set by caller."""
    h = pm.prep(pa)
    h = h[h.cls.isin([2, 3, 4, 5])].groupby(["game_pk", "batter"]).size().reset_index(name="hits")
    rows = []
    for i, side in enumerate(("away", "home")):
        for sl in range(9):
            rows.append(pd.DataFrame({"game_pk": inp["game_pk"], "side": side, "slot": sl + 1, "batter": inp["batter_id"][:, i, sl],
                                      "p1": b[f"{side}_slot{sl + 1}_hits_ge_1"].to_numpy(), "p2": b[f"{side}_slot{sl + 1}_hits_ge_2"].to_numpy()}))
    r = pd.concat(rows, ignore_index=True).merge(h, on=["game_pk", "batter"], how="left")
    r["hits"] = r.hits.fillna(0)
    return r


def corr_check(b):
    """Realized vs simulated correlation of same-game legs (signs and rough size)."""
    hr, ar = b.home_runs.to_numpy(), b.away_runs.to_numpy()
    out = {}
    pairs = {"home_win~home_runs>=5": (hr > ar, hr >= 5), "home_win~away_runs>=5": (hr > ar, ar >= 5),
             "home_runs>=5~total>=9": (hr >= 5, hr + ar >= 9)}
    for name, (a, c) in pairs.items():
        sim_a = b["p_home_ml"] if name.startswith("home_win") else b["home_runs_ge_5"]
        out[name] = {"realized_corr": float(np.corrcoef(a.astype(float), c.astype(float))[0, 1])}
    return out


def main():
    t0 = time.time()
    t = {k: pd.read_parquet(T / f"{k}.parquet") for k in ("pa", "games", "lineups")}
    pa, games = t["pa"], t["games"]
    league = pm.fit_league(pm.prep(pa[pa.game_date < SPLIT]))
    hist = pm.PAHistory(pa, games)
    g26 = games[games.game_date >= SPLIT]
    inp = pm.game_inputs(g26, t["lineups"], hist, league)
    G = len(inp["game_pk"])
    print("games priced:", G, "of", len(g26))
    cache = safe_out(HERE / '_cache' / f'w126_3_board_{NDRAW}.parquet')
    if cache.exists():
        b = pd.read_parquet(cache)
    else:
        b = price_parallel(inp)
        b.to_parquet(safe_out(cache))
    res = games.set_index("game_pk")[["home_runs", "away_runs", "home_team", "away_team"]]
    b = b.merge(res, left_on="game_pk", right_index=True)
    out = {"exp": "EXP-MLBSIM-001", "n_draws": NDRAW, "games_in_2026": int(len(g26)), "games_priced": int(G),
           "seconds": round(time.time() - t0), "calibration": {}, "vs_w122_4_nb": {}, "market": {}, "limits": [
               "no park/weather/home-field term", "as-played lineups (small leak)", "KXMLBHIT market comparison not built (no name bridge)",
               "F3/F5/F7 series not priced", "games table includes any postseason rows in 2026"]}
    # naive from the training window
    tr = games[games.game_date < SPLIT].rename(columns={"home_team": "home_team", "away_team": "away_team"}).copy()
    tr["game_pk"] = tr.game_pk
    trb = pd.DataFrame({"game_pk": tr.game_pk, "home_runs": tr.home_runs, "away_runs": tr.away_runs})
    for fam in FAMS:
        s = long_family(b, fam)
        sn = long_family(trb.assign(**{c: 0.0 for c in b.columns if c not in trb.columns and c not in ("game_pk",)}), fam) if False else None
        ys = []
        for side in ("home", "away"):
            for k in bd.rungs(fam):
                if bd.column(fam, side, k) is None:
                    continue
                ys.append({"side": side, "k": k, "naive": float(bd.realized(trb, fam, side, k).mean())})
                if fam in ("total", "moneyline"):
                    break
        s = s.merge(pd.DataFrame(ys), on=["side", "k"], how="left")
        out["calibration"][fam] = gains(s, "naive")
        out["calibration"][fam]["by_k"] = s.groupby(["side", "k"]).agg(p=("p", "mean"), y=("y", "mean")).round(3).reset_index().to_dict("records")
        print(fam, {k: v for k, v in out["calibration"][fam].items() if k != "by_k"})
    # batter hits vs naive (per-slot league frequency in the training lineups)
    h_tr = pm.prep(pa[pa.game_date < SPLIT])
    h_tr = h_tr[h_tr.cls.isin([2, 3, 4, 5])].groupby(["game_pk", "batter"]).size().reset_index(name="hits")
    lu = t["lineups"][t["lineups"].slot.between(1, 9)].merge(games[["game_pk", "game_date"]], on="game_pk")
    lu = lu[lu.game_date < SPLIT].merge(h_tr, on=["game_pk", "batter"], how="left").fillna({"hits": 0})
    nv = lu.groupby("slot").hits.agg(n1=lambda s: (s >= 1).mean(), n2=lambda s: (s >= 2).mean())
    hf = hits_frame(inp, pa, b).merge(nv, left_on="slot", right_index=True)
    for kk, (pc, nc) in {"hits_ge_1": ("p1", "n1"), "hits_ge_2": ("p2", "n2")}.items():
        s = pd.DataFrame({"p": hf[pc], "naive": hf[nc], "y": (hf.hits >= int(kk[-1])).astype(float)})
        out["calibration"][kk] = gains(s, "naive")
        print(kk, out["calibration"][kk])
    out["correlation_realized"] = corr_check(b)
    # W122.4 baseline for the same families
    base = json.load(open(HERE / "RESULTS_W122_4.json"))["calibration"]
    for fam in FAMS:
        w = base.get(f"2026/{fam}")
        if w:
            out["vs_w122_4_nb"][fam] = {"nb_brier": w["brier_model"], "nb_logloss": w["logloss_model"],
                                        "sim_brier": out["calibration"][fam]["brier_model"], "sim_logloss": out["calibration"][fam]["logloss_model"],
                                        "nb_n_games": w["n_games"]}
    # market gap on the archive window, Kalshi mid as benchmark
    import run_w122_4 as w4
    g = games[["game_pk", "game_date", "home_team", "away_team"]]
    dup = g.duplicated(["game_date", "home_team", "away_team"], keep=False)
    g = g[~dup & (g.game_date >= SPLIT)]
    c = mk.last_pregame(ARCH, series=("KXMLBGAME", "KXMLBTOTAL", "KXMLBSPREAD", "KXMLBTEAMTOTAL"))
    out["archive_contracts"] = int(len(c))
    bb = b.drop(columns=["home_team", "away_team", "game_date"]).merge(g, on="game_pk")
    if len(c):
        j = mk.moneyline(c).merge(bb, left_on=["game_date", "home", "away"], right_on=["game_date", "home_team", "away_team"])
        out["market"]["moneyline"] = w4._cmp(j.p_home_ml.to_numpy(), j.p_home_mkt.to_numpy(), bd.realized(j, "moneyline", "home", 0))
        for fam, series in (("total", "KXMLBTOTAL"), ("spread", "KXMLBSPREAD"), ("team_total", "KXMLBTEAMTOTAL")):
            out["market"][fam] = w4._rung_market(c, series, fam, bb)
    for fam, v in out["market"].items():
        print("market", fam, {k: v[k] for k in v if k in ("n", "brier_model", "brier_market", "gain_vs_market_brier")})
    safe_out(HERE / "RESULTS_W126_3.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
