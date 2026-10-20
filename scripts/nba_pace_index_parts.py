"""W80.2: numbers for INDEX_ENTRY_PACE.md parts 1-3 (split, rank, cross) from the point-in-time NBA game frame.

Descriptive and read-only: no model, order or registry is touched. Frame = nba_totals_applied.build_games (2016-2026 regular
season, season label = end year, so 2026 = 2025-26). Residual = total - OLS base prediction fitted on 2016-2025.
Bootstrap B=2000 seed 20261016 (same as the applied test). Rules fixed before looking:
  split  : mean residual by (a) either team on 0 days rest vs neither, (b) opponent-pace tercile of the other side's pace_ytd
           (cut points from 2016-2025), (c) home vs away team pace_ytd gap; 2016-2025 and 2026 separately.
  rank   : 2026 league-mean pace_ytd at game-number checkpoints vs the same checkpoint in 2016-2025 (percentile).
  cross  : total ~ 1 + h_pace + a_pace  vs  + (h_pace-mean)*(a_pace-mean), fitted 2016-2025, scored on 2026; MSE gain with CI.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("nta", HERE / "nba_totals_applied.py")
nta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nta)


def mean_ci(xs, b=2000, seed=nta.SEED):
    rng = random.Random(seed)
    n = len(xs)
    if n < 2:
        return {"est": None, "lo": None, "hi": None, "n": n}
    sims = sorted(sum(xs[rng.randrange(n)] for _ in range(n)) / n for _ in range(b))
    return {"est": sum(xs) / n, "lo": sims[int(0.025 * b)], "hi": sims[int(0.975 * b) - 1], "n": n}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    import numpy as np
    g = nta.build_games(a.store).copy()
    g["game_date"] = g["game_date"].astype(str).str[:10]
    g = g.sort_values(["season", "game_date", "game_id"]).reset_index(drop=True)
    m = nta.fit_models(g)
    bb = m["beta_base"]
    g["resid"] = g["total"] - (bb[0] + bb[1] * g["base_total"])
    # rest days per team, within season
    import pandas as pd
    long = pd.concat([g[["game_id", "season", "game_date", "home_team_abbreviation"]].rename(columns={"home_team_abbreviation": "t"}).assign(side="h"),
                      g[["game_id", "season", "game_date", "away_team_abbreviation"]].rename(columns={"away_team_abbreviation": "t"}).assign(side="a")])
    long["d"] = pd.to_datetime(long.game_date)
    long = long.sort_values(["season", "t", "d"])
    long["rest"] = (long.groupby(["season", "t"]).d.diff().dt.days - 1)
    long["gno"] = long.groupby(["season", "t"]).cumcount() + 1
    piv = long.pivot_table(index="game_id", columns="side", values=["rest", "gno"])
    piv.columns = [f"{x}_{y}" for x, y in piv.columns]
    g = g.merge(piv, left_on="game_id", right_index=True, how="left")
    g["b2b_any"] = ((g.rest_h == 0) | (g.rest_a == 0)).astype(float)
    tr, te = g[g.season <= 2025], g[g.season == 2026]
    cuts = np.quantile(pd.concat([tr.h_pace_ytd, tr.a_pace_ytd]).dropna(), [1 / 3, 2 / 3])
    out = {"n_train": len(tr), "n_2026": len(te), "sigma_base": m["sigma"], "split": {}, "rank": {}, "cross": {}}

    def tier(p):
        return 0 if p <= cuts[0] else (1 if p <= cuts[1] else 2)
    for name, d in (("2016-2025", tr), ("2026", te)):
        s = {}
        d2 = d.dropna(subset=["rest_h", "rest_a"])
        s["b2b_either_side"] = mean_ci(d2[d2.b2b_any == 1].resid.tolist())
        s["no_b2b"] = mean_ci(d2[d2.b2b_any == 0].resid.tolist())
        # opponent-pace tier: for each team-side, the other side's pace tier; residual of the game (game-level, both sides)
        for side, oth in (("home_team", "a_pace_ytd"), ("away_team", "h_pace_ytd")):
            for t, lbl in enumerate(("slow", "mid", "fast")):
                sub = d[d[oth].apply(tier) == t]
                s[f"{side}_vs_{lbl}_opp"] = mean_ci(sub.resid.tolist())
        s["pace_gap_home_minus_away_mean"] = mean_ci((d.h_pace_ytd - d.a_pace_ytd).tolist())
        s["pace_gap_home_minus_away_corr_resid"] = float(np.corrcoef(d.h_pace_ytd - d.a_pace_ytd, d.resid)[0, 1])
        out["split"][name] = s
    # rank: league mean of both sides' pace_ytd by game number checkpoint
    for chk in (10, 20, 30, 40):
        def lm(d):
            sub = d[(d.gno_h.between(chk - 2, chk + 2)) & (d.gno_a.between(chk - 2, chk + 2))]
            return None if sub.empty else float(pd.concat([sub.h_pace_ytd, sub.a_pace_ytd]).mean())
        hist = [lm(g[g.season == s]) for s in range(2016, 2026)]
        hist = [h for h in hist if h is not None]
        cur = lm(g[g.season == 2026])
        if cur is not None and hist:
            out["rank"][f"game_{chk}"] = {"2026": cur, "history_mean": sum(hist) / len(hist), "history_min": min(hist), "history_max": max(hist),
                                          "percentile": sum(h <= cur for h in hist) / len(hist), "n_hist_seasons": len(hist)}
    # cross
    for d in (tr, te):
        d["pm"] = d.h_pace_ytd.mean()
    pm_h, pm_a = tr.h_pace_ytd.mean(), tr.a_pace_ytd.mean()
    def X(d, cross):
        cols = [np.ones(len(d)), d.h_pace_ytd.values, d.a_pace_ytd.values]
        if cross:
            cols.append(((d.h_pace_ytd - pm_h) * (d.a_pace_ytd - pm_a)).values)
        return np.column_stack(cols)
    trn = tr.dropna(subset=["h_pace_ytd", "a_pace_ytd", "total"])
    tst = te.dropna(subset=["h_pace_ytd", "a_pace_ytd", "total"])
    bs = {c: np.linalg.lstsq(X(trn, c), trn.total.values, rcond=None)[0] for c in (False, True)}
    e0 = (tst.total.values - X(tst, False) @ bs[False]) ** 2
    e1 = (tst.total.values - X(tst, True) @ bs[True]) ** 2
    out["cross"] = {"coef_interaction": float(bs[True][3]), "mse_additive": float(e0.mean()), "mse_with_cross": float(e1.mean()),
                    "mse_gain": mean_ci((e0 - e1).tolist()), "n_test": len(tst)}
    a.out.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
