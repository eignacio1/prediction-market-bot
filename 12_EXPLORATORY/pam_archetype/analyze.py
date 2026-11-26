import sys, json, pandas as pd
sys.path.insert(0, "src")
from prediction_market_bot.pam import nba_pit_profile as P, nba_pit_archetype as A
D = "/Users/earlignacio/PredictionMarketEvidence/data/exp_output/NBA_EVENTS/raw/"
TRAIN, EVAL = [2022, 2023, 2024, 2025], 2026
def load(s):
    r = lambda t: pd.read_parquet(f"{D}{t}/{t}_{s}.parquet")
    return P.game_table(r("pbp"), r("possessions"), r("player_box"), r("schedule"))
games = pd.concat([load(s) for s in TRAIN + [EVAL]], ignore_index=True)
games.to_parquet("/tmp/w130_games.parquet") if False else None
tr = pd.concat([P.profile_as_of(games, s, f"{s}-07-01", min_poss=1500).assign(season=s) for s in TRAIN])
params = A.fit(tr)
ev = P.profile_as_of(games, EVAL, "2026-07-01", min_poss=1500)
asg = A.assign(ev, params)
print(len(tr), len(ev)); print(asg.top.value_counts().sort_index())
deep = [json.loads(l) for l in open("qualitative_data/pam/nba/records.jsonl")]
rows = []
for r in deep:
    pid = int(r["player_id"])
    if pid in asg.index:
        dt = max(r["archetypes"], key=lambda a: a["weight"])["id"]; dw = {a["id"]: a["weight"] for a in r["archetypes"]}
        w = asg.loc[pid, "weights"]
        rows.append((r["player_name"], dt, asg.loc[pid, "top"], dt in w, sum(min(dw.get(k,0), w.get(k,0)) for k in set(dw)|set(w))))
df = pd.DataFrame(rows, columns=["name","deep_top","pit_top","deep_top_in_pit","overlap"])
print(len(df), "top1 agree", (df.deep_top==df.pit_top).mean(), "deep top in PIT set", df.deep_top_in_pit.mean(), "mean overlap", df.overlap.mean())
print(pd.crosstab(df.deep_top, df.pit_top))
for pid, n in [(1627826, "Zubac"), (1641705, "Wembanyama")]:
    print(n, asg.loc[pid, "weights"], asg.loc[pid, "confidence"]); print(ev.loc[pid, ["gp","poss","dreb_per100","oreb_per100","oreb_share","dreb_share","oreb_mix","blk_per100","opp_rim_rate_on","opp_rim_fg_on","usage_per100","rim_share","three_share","ast_per100"]].round(3).to_dict())
