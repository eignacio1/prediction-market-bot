"""W113.4 Part B: recompute MoneyPuck team season counts (2025-26, regular, situation=all)
from the bot's own NHL event store and compare with the archive claims (read-only).
Usage: grade_nhl.py <archive_root> <nhl_events_dir> <out_csv>. Prints aggregate stats only."""
import glob, json, sys
import pandas as pd

arch, store, out = sys.argv[1:4]
ev = pd.read_parquet(f"{store}/events_2025.parquet")
g = pd.read_parquet(f"{store}/games_2025.parquet")
reg = g[g.game_type == 2]
ev = ev[ev.game_id.isin(reg.game_id)]
ev_all = ev
ev = ev[ev.period_type != "SO"]  # MoneyPuck counts exclude shootout attempts
ids = {}
for _, r in reg.iterrows():
    ids[r.home_team_id] = r.home
# away ids from events: owner_is_home False
for _, r in ev[ev.owner_is_home == False].drop_duplicates(["game_id", "owner_team_id"]).iterrows():
    pass
away = reg.merge(ev[ev.owner_is_home == False][["game_id", "owner_team_id"]].drop_duplicates(), on="game_id")
for _, r in away.iterrows():
    ids[r.owner_team_id] = r.away
names = {"ANA":"Anaheim Ducks","BOS":"Boston Bruins","BUF":"Buffalo Sabres","CGY":"Calgary Flames","CAR":"Carolina Hurricanes","CHI":"Chicago Blackhawks","COL":"Colorado Avalanche","CBJ":"Columbus Blue Jackets","DAL":"Dallas Stars","DET":"Detroit Red Wings","EDM":"Edmonton Oilers","FLA":"Florida Panthers","LAK":"Los Angeles Kings","MIN":"Minnesota Wild","MTL":"Montreal Canadiens","NSH":"Nashville Predators","NJD":"New Jersey Devils","NYI":"New York Islanders","NYR":"New York Rangers","OTT":"Ottawa Senators","PHI":"Philadelphia Flyers","PIT":"Pittsburgh Penguins","SJS":"San Jose Sharks","SEA":"Seattle Kraken","STL":"St. Louis Blues","TBL":"Tampa Bay Lightning","TOR":"Toronto Maple Leafs","UTA":"Utah Hockey Club","VAN":"Vancouver Canucks","VGK":"Vegas Golden Knights","WSH":"Washington Capitals","WPG":"Winnipeg Jets"}
t = ev.assign(team=ev.owner_team_id.map(ids))
cnt = lambda ty: t[t.type == ty].groupby("team").size()
gp = pd.concat([reg.home, reg.away]).value_counts()
sog, miss, blk, goal = cnt("shot-on-goal"), cnt("missed-shot"), cnt("blocked-shot"), cnt("goal")
rec = {
 "games_played": gp,
 "goalsFor": goal,
 "shotsOnGoalFor": sog + goal,      # candidate A: store 'shot-on-goal' excludes goals
 "shotsOnGoalFor_alt": sog,         # candidate B
 "missedShotsFor": miss,
 "hitsFor": cnt("hit"),
 "takeawaysFor": cnt("takeaway"),
 "giveawaysFor": cnt("giveaway"),
 "penaltiesFor": cnt("penalty"),
 "faceOffsWonFor": cnt("faceoff"),
 "blockedShotsByOwner": blk,
}
pen = t[t.type == "penalty"]
opp = pen.merge(pd.concat([reg[["game_id","home"]].rename(columns={"home":"team"}), reg[["game_id","away"]].rename(columns={"away":"team"})]), on="game_id", suffixes=("","_g"))
opp = opp[opp.team != opp.team_g].groupby("team_g").size()
rec["penaltiesFor_drawn"] = opp

rows = []
for f in glob.glob(f"{arch}/L3-split/nhl/splits/C-922.claims.jsonl"):
    for l in open(f):
        try: d = json.loads(l)
        except Exception: continue
        m = d["metric"].split(" (")[0]
        rows.append((d["subject"], m, d["value"]))
a = pd.DataFrame(rows, columns=["name", "metric", "value"])
inv = {v: k for k, v in names.items()}
a["team"] = a.name.map(inv)
res = []
for m, s in rec.items():
    base = m.replace("_alt", "").replace("_drawn", "")
    x = a[(a.metric == base) & a.team.notna()].drop_duplicates(["team"]).set_index("team").value
    d = pd.concat([x, s.rename("mine")], axis=1).dropna()
    d["diff"] = (d.value - d.mine).abs()
    res.append((m, len(d), float((d["diff"] == 0).mean()), float((d["diff"] <= 0.01 * d.value.abs().clip(lower=1)).mean()), float(d["diff"].max())))
print("unmapped names:", sorted(set(a[a.team.isna()].name)))
r = pd.DataFrame(res, columns=["metric", "n_teams", "exact_frac", "within_1pct_frac", "max_abs_diff"])
r.to_csv(out, index=False)
print(r.to_string())
