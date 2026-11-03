"""W98.1 Part C: v3's availability and lineup factors, the two index parts left open in W96.1 (rank vs history at the same point in
a season; matchup cross), point-in-time, and whether either changes v3's held-out Brier.

Factors (all from the game-level frame of factors_frame.py; nothing is read that is unknown before tip):
  rank   a team's value (exp_missing, lineup_net) as a percentile among PRIOR seasons' team-games at the same point in the season
         (game position within the season +-5%); d_ = home - away, s_ = home + away. History = seasons strictly before the game's season.
  cross  availability x opponent strength: h_exp_missing * a_lineup_net, a_exp_missing * h_lineup_net (whose missing share matters against which
         opponent); d_ = home-side - away-side, s_ = sum.
Variants are scored against v3_all (the frozen v3 factor set) and v2_core on identical games, protocol of study_v3.py (not edited).
Applies when: pre-tip pricing of spread / team-total lines where an injury report exists (as v3). Known-answer test: tests/test_w98_1_nba_index_factors.py.
Run: PYTHONPATH=src python3 study_partc_w98.py <NBA_EVENTS raw> <v3_factors.parquet> <out json inside 12_EXPLORATORY/>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import study_v3 as S3  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nba_engine import engine_v3 as V3  # noqa: E402
import study_v2 as S2  # noqa: E402
import study_a as SA  # noqa: E402

WIN = 0.05


def history_rank(F: pd.DataFrame, col_h: str, col_a: str) -> pd.DataFrame:
    """Percentile of each team-game value among prior seasons' team-games at the same season position. NaN with no history."""
    F = F.sort_index()
    pos = F.groupby("season").cumcount() / F.groupby("season")["season"].transform("size")
    out_h, out_a = np.full(len(F), np.nan), np.full(len(F), np.nan)
    for s in sorted(F.season.unique()):
        prior = F[F.season < s]
        if prior.empty:
            continue
        ppos = (prior.groupby("season").cumcount() / prior.groupby("season")["season"].transform("size")).to_numpy()
        pv = np.concatenate([prior[col_h].to_numpy(), prior[col_a].to_numpy()])
        pp = np.concatenate([ppos, ppos])
        m = (F.season == s).to_numpy()
        for i in np.where(m)[0]:
            near = pv[np.abs(pp - pos.iloc[i]) <= WIN]
            near = near[np.isfinite(near)]
            if len(near) >= 30:
                out_h[i] = (near < F[col_h].iloc[i]).mean() + 0.5 * (near == F[col_h].iloc[i]).mean()
                out_a[i] = (near < F[col_a].iloc[i]).mean() + 0.5 * (near == F[col_a].iloc[i]).mean()
    return pd.DataFrame({"h": out_h, "a": out_a}, index=F.index)


def add_factors(F: pd.DataFrame) -> pd.DataFrame:
    F = F.copy()
    for k in ("exp_missing", "lineup_net"):
        r = history_rank(F, f"h_{k}", f"a_{k}")
        F[f"d_rank_{k}"], F[f"s_rank_{k}"] = r.h - r.a, r.h + r.a
    ch, ca = F.h_exp_missing * F.a_lineup_net, F.a_exp_missing * F.h_lineup_net
    F["d_cross_missing_net"], F["s_cross_missing_net"] = ch - ca, ch + ca
    return F


NEW = {"rank": ["d_rank_exp_missing", "s_rank_exp_missing", "d_rank_lineup_net", "s_rank_lineup_net"],
       "cross": ["d_cross_missing_net", "s_cross_missing_net"]}


def register():
    for c in sum(NEW.values(), []):
        V3.FACTORS[c] = ("margin" if c.startswith("d_") else "total", c, "W98.1 Part C index factor (study only)")
    base = S3.VARIANTS["v3_all"]
    S3.VARIANTS = {"v2_core": [], "v3_all": base, "v3_all+rank": base + NEW["rank"], "v3_all+cross": base + NEW["cross"],
                   "v3_all+rank+cross": base + NEW["rank"] + NEW["cross"]}
    S3.COLS = sorted({c for v in S3.VARIANTS.values() for c in v})


def main(raw, fpath, out):
    register()
    F = add_factors(pd.read_parquet(fpath))
    F.to_parquet(safe_out(HERE / "v3_factors.parquet"))   # study_v3.main reads this file name
    S3.main(raw, out)
    sc = pd.read_csv(HERE / (out[: -len(".json")] + "_rows.csv.gz"))
    extra = {}
    for scope, sub in (("pooled", sc), *[(str(T), sc[sc.season == T]) for T in S3.TESTS]):
        extra[scope] = {}
        for fam, d in list(sub.groupby("family")) + [("ALL", sub)]:
            extra[scope][fam] = {}
            for v in ("v3_all+rank", "v3_all+cross", "v3_all+rank+cross"):
                d = d.assign(**{"b_" + v: (d[v] - d.y) ** 2, "b_v3_all": (d["v3_all"] - d.y) ** 2})
                m, lo, hi = S2.boot(d, "b_" + v, "b_v3_all")
                extra[scope][fam][v + "_minus_v3_all"] = dict(delta=m, lo=lo, hi=hi)
    safe_out(HERE.parent / (out[: -len(".json")] + "_vs_v3all.json")).write_text(json.dumps(extra, indent=1, default=float))
    for fam, r in extra["pooled"].items():
        print(fam, {k: (round(v["delta"], 5), round(v["lo"], 5), round(v["hi"], 5)) for k, v in r.items()})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
