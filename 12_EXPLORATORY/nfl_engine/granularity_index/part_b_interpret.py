"""W80.3 Part B step 3: does the box cross predict a game's rush success / rushing yards beyond season-long ratings?
Score on 2022-2025 only, leave-one-season-out. Point in time: each game uses only that season's earlier weeks (>=4 games
each side) plus prior seasons for the league constants."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nfl_engine import granularity_index as gi
ROOT = Path(__file__).resolve().parents[3]; RAW = ROOT / "exp_output/NFL_EVENTS/raw"; OUT = Path(__file__).parent / "results"
cols = ["game_id","play_id","season","week","season_type","posteam","defteam","play_type","qb_kneel","qb_scramble","two_point_attempt","yards_gained","success"]
pbp = pd.concat([pd.read_parquet(p, columns=cols) for p in sorted((RAW/"pbp").glob("pbp_*.parquet"))])
ftn = pd.concat([pd.read_parquet(p, columns=["game_id","play_id","n_defense_box"]) for p in sorted((RAW/"ftn").glob("ftn_*.parquet"))]).drop_duplicates(["game_id","play_id"])
d = pbp[(pbp.season_type=="REG")&(pbp.play_type=="run")&(pbp.qb_kneel!=1)&(pbp.qb_scramble!=1)&(pbp.two_point_attempt!=1)].merge(ftn,on=["game_id","play_id"],how="left")
d["bx"] = d.n_defense_box.where(d.n_defense_box>0)
d["box"] = np.where(d.bx.isna(), None, np.where(d.bx>=8,"loaded","light"))
d["success"]=d.success.astype(float)
dd = d[d.season<=2025]
# per game outcome (all rushes, box known or not -- the target is the game's rushing, not the subset)
games = (dd.groupby(["season","week","game_id","posteam","defteam"]).agg(att=("success","size"), succ=("success","mean"), yds=("yards_gained","sum")).reset_index())
bx = dd.dropna(subset=["box"])
rows = []
for (s, wk), g in games.groupby(["season","week"]):
    prior = bx[(bx.season==s)&(bx.week<wk)]
    allp = dd[(dd.season==s)&(dd.week<wk)]
    if prior.empty: continue
    lgm = {b: prior[prior.box==b].success.mean() for b in ("loaded","light")}
    lsh = prior.box.value_counts(normalize=True).to_dict()
    o_ns = prior.groupby(["posteam","box"]).success.agg(["size","sum"]); d_ns = prior.groupby(["defteam","box"]).success.agg(["size","sum"])
    o_sh = prior.groupby("posteam").box.value_counts(normalize=True).unstack().fillna(0); d_sh = prior.groupby("defteam").box.value_counts(normalize=True).unstack().fillna(0)
    o_all = allp.groupby("posteam").success.agg(["size","sum"]); d_all = allp.groupby("defteam").success.agg(["size","sum"])
    Lall = allp.success.mean()
    for _, r in g.iterrows():
        o, df = r.posteam, r.defteam
        if o not in o_all.index or df not in d_all.index or o_all.loc[o,"size"]<60 or d_all.loc[df,"size"]<60: continue
        k = 300.0
        sh = lambda n, sm, L: (sm + k*L)/(n + k)
        base = Lall + (sh(o_all.loc[o,"size"], o_all.loc[o,"sum"], Lall)-Lall) + (sh(d_all.loc[df,"size"], d_all.loc[df,"sum"], Lall)-Lall)
        if o not in o_sh.index or df not in d_sh.index: continue
        freq = gi.show_frequency({b:d_sh.loc[df].get(b,0) for b in lgm}, {b:o_sh.loc[o].get(b,0) for b in lgm}, lsh)
        off = {b:(tuple(o_ns.loc[(o,b)]) if (o,b) in o_ns.index else (0,0)) for b in lgm}
        dfn = {b:(tuple(d_ns.loc[(df,b)]) if (df,b) in d_ns.index else (0,0)) for b in lgm}
        c = gi.cross(off, dfn, lgm, freq, {b:k for b in lgm})
        rows.append({"season":s,"week":wk,"game_id":r.game_id,"posteam":o,"defteam":df,"att":r.att,"succ":r.succ,"yds":r.yds,"base":base,"cross":c.expected,"d":c.expected-base})
X = pd.DataFrame(rows); print(len(X), "team-games"); X.to_csv(safe_out(OUT/"team_game_cross_2022_2025.csv"), index=False)
def fit(tr, te, cols, y):
    A = np.c_[np.ones(len(tr)), tr[cols]]; w = tr.att.to_numpy()
    beta = np.linalg.lstsq(A*np.sqrt(w)[:,None], tr[y]*np.sqrt(w), rcond=None)[0]
    return np.c_[np.ones(len(te)), te[cols]] @ beta
res = {}
rng = np.random.default_rng(7)
for y in ("succ",):
    e0 = np.zeros(len(X)); e1 = np.zeros(len(X))
    for s in sorted(X.season.unique()):
        tr, te = X[X.season!=s], X[X.season==s]
        e0[te.index] = (te[y] - fit(tr, te, ["base"], y))**2
        e1[te.index] = (te[y] - fit(tr, te, ["base","d"], y))**2
    w = X.att.to_numpy(); diff = (e0 - e1)
    gm = X.game_id.to_numpy(); ug = np.unique(gm); idx = {g: np.where(gm==g)[0] for g in ug}
    bs = []
    for _ in range(2000):
        pick = np.concatenate([idx[g] for g in rng.choice(ug, len(ug))])
        bs.append(np.average(diff[pick], weights=w[pick]))
    tr = X; A = np.c_[np.ones(len(tr)), tr[["base","d"]]]
    res[y] = {"n": len(X), "wmse_base": float(np.average(e0,weights=w)), "wmse_with_cross": float(np.average(e1,weights=w)),
              "gain": float(np.average(diff,weights=w)), "ci95": [float(np.percentile(bs,2.5)), float(np.percentile(bs,97.5))],
              "corr_d_resid": float(np.corrcoef(X.d, X.succ - fit(X, X, ["base"], y))[0,1]), "sd_d": float(X.d.std())}
    # yards: yds ~ att*? use yds per game directly with base, d, att
print(json.dumps(res, indent=1)); safe_out(OUT / "part_b_interpretation.json").write_text(json.dumps(res, indent=1))
