"""Descriptive look (W94.2 Part C): do caller tendencies line up with the gap between Kalshi's implied team total
and the schedule-line-implied team total, 2026 REG games? Descriptive only: no test is claimed, no order is implied."""
import glob, json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out

SCHED, ASOF, ARCH, OUT = sys.argv[1:5]
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
rows = {}
for f in sorted(glob.glob(f"{ARCH}/prices_2026-*.jsonl")):
    for ln in open(f):
        if '"KXNFLTEAMTOTAL"' not in ln:
            continue
        r = json.loads(ln)
        m = re.match(r"KXNFLTEAMTOTAL-(\d\d)([A-Z]{3})(\d\d)([A-Z]+)-([A-Z]+)(\d+)$", r["ticker"])
        if not m:
            continue
        bid, ask = float(r["yes_bid"]), float(r["yes_ask"])
        if ask <= 0 or bid < 0 or ask - bid > 0.10:
            continue
        key = (r["event_ticker"], m.group(5), int(m.group(6)))
        rows[key] = (r["run_ts"], (bid + ask) / 2, f"20{m.group(1)}-{MON[m.group(2)]:02d}-{m.group(3)}")  # last snapshot wins
df = pd.DataFrame([(k[0], k[1], k[2], v[0], v[1], v[2]) for k, v in rows.items()],
                  columns=["event", "team", "strike", "ts", "p", "date"])
df = df[df.p.between(0.02, 0.98)]
# P(X >= strike) ladder -> median-ish expected team total: first strike where p crosses 0.5 (linear interp)
def implied(g):
    g = g.sort_values("strike")
    if len(g) < 3 or g.p.max() < 0.5 or g.p.min() > 0.5:
        return np.nan
    return float(np.interp(0.5, g.p.values[::-1], g.strike.values[::-1]))
imp = df.groupby(["event", "team", "date"]).apply(implied).rename("k_tt").reset_index().dropna()
s = pd.read_parquet(SCHED)
s = s[(s.season == 2026) & (s.game_type == "REG")].copy()
s["gameday"] = s.gameday.astype(str)
long = pd.concat([
    s.assign(team=s.home_team, line_tt=(s.total_line - s.spread_line) / 2)[["gameday", "team", "line_tt", "season", "week"]],
    s.assign(team=s.away_team, line_tt=(s.total_line + s.spread_line) / 2)[["gameday", "team", "line_tt", "season", "week"]]])
imp = imp.merge(long, left_on=["date", "team"], right_on=["gameday", "team"], how="inner")
asof = pd.read_parquet(ASOF)
res = {"n_team_games_with_kalshi_ladder": int(len(imp)), "note": "descriptive; implied = strike where P(X>=k)=0.5 from last tight snapshot"}
if len(imp):
    imp["gap"] = imp.k_tt - imp.line_tt
    res["gap_mean"] = float(imp.gap.mean()); res["gap_sd"] = float(imp.gap.std())
    a26 = asof[asof.season == 2026] if "season" in asof else asof.iloc[0:0]
    res["asof_rows_2026"] = int(len(a26))
    if len(a26):
        m = imp.merge(a26, on=["team", "week"], how="inner") if "team" in a26 else imp.iloc[0:0]
        res["n_joined"] = int(len(m))
        for f in ("pass_oe", "go4_oe", "pace", "lead_oe"):
            c = f"est_{f}"
            if c in m and m[c].notna().sum() > 10:
                x = m[[c, "gap"]].dropna()
                res[f"corr_{f}_gap"] = float(np.corrcoef(x[c], x.gap)[0, 1]); res[f"n_{f}"] = int(len(x))
json.dump(res, open(safe_out(OUT), "w"), indent=1)
print(json.dumps(res, indent=1)); print(asof.columns.tolist())
