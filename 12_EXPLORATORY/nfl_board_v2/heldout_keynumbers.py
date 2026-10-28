"""W93.4 Part A: rolling-origin held-out key-number check. Library = seasons < S; board centred on each S-game's
closing line/total; compare expected vs observed counts of |margin|=k and a same-median Gaussian baseline."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "src")
sys.path.insert(0, "12_EXPLORATORY")
from _fence import safe_out
from prediction_market_bot.nfl_engine.board_v2 import build_library, price_board, key_number_counts
from statistics import NormalDist
N = NormalDist()
P = "exp_output/NFL_EVENTS/raw/schedules/schedules_20261020T001136Z.parquet"
s = pd.read_parquet(P)
s = s[s.home_score.notna() & s.spread_line.notna() & s.total_line.notna() & (s.game_type == "REG")] if "game_type" in s else s[s.home_score.notna() & s.spread_line.notna()]
KS = [1, 2, 3, 4, 6, 7, 10, 14]
SEASONS = list(range(2012, 2026))
boards, obs = [], []
for S in SEASONS:
    lib = build_library(s, before_season=S)
    for r in s[s.season == S].itertuples():
        boards.append(price_board(lib, r.spread_line, r.total_line))
        obs.append(int(abs(r.home_score - r.away_score)))
obs = np.array(obs)
eng = key_number_counts(boards, KS)
# Gaussian baseline: margin ~ N(line, 13.5) discretised, per game (sd from library residuals)
lines = np.concatenate([s[s.season == S].spread_line.to_numpy() for S in SEASONS])
res = (s[s.season.isin(SEASONS)].home_score - s[s.season.isin(SEASONS)].away_score - s[s.season.isin(SEASONS)].spread_line)
sd = float(res.std())
out = {"n_games": int(len(obs)), "seasons": [SEASONS[0], SEASONS[-1]], "gauss_sd": sd, "k": {}}
for k in KS:
    pg = np.array([N.cdf((k + .5 - L) / sd) - N.cdf((k - .5 - L) / sd) + N.cdf((-k + .5 - L) / sd) - N.cdf((-k - .5 - L) / sd) for L in lines])
    o = int((obs == k).sum()); e, v = eng[k]
    out["k"][k] = dict(observed=o, engine=round(e, 1), engine_z=round((o - e) / v ** .5, 2), gauss=round(float(pg.sum()), 1),
                       gauss_z=round((o - pg.sum()) / (pg * (1 - pg)).sum() ** .5, 2))
    print(k, out["k"][k])
json.dump(out, open(safe_out("12_EXPLORATORY/nfl_board_v2/heldout_keynumbers.json"), "w"), indent=1)
