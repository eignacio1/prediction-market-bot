"""W80.3 Part B step 4: is the run-box cross priced in Kalshi 2025 player rushing-yards markets? Read-only on the thin raw store.
Method follows 77.2 (market_tests/closing_line.py): regress the price (and the outcome) on the term; b = share priced.
Target: pre-game mid ~30 min before kickoff from the 1-minute-or-coarser candles in the sample (NOT last_price, which is post-game)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _fence import safe_out  # noqa: E402
ROOT = Path(__file__).resolve().parents[3]; OUT = Path(__file__).parent / "results"
THIN = Path(sys.argv[1])
sched = pd.concat([pd.read_parquet(p) for p in (ROOT/"exp_output/NFL_EVENTS/raw/schedules").glob("schedules_*.parquet")])
sched = sched[(sched.season == 2025) & (sched.game_type == "REG")].copy()
sched["ko"] = pd.to_datetime(sched.gameday + " " + sched.gametime, errors="coerce").dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
sched["key"] = sched.away_team + sched.home_team
cx = pd.read_csv(OUT / "team_game_cross_2022_2025.csv"); cx = cx[cx.season == 2025]
mk, cd = {}, {}
for l in open(THIN):
    if l.startswith('{"kind":"markets_page"'):
        for m in json.loads(l)["payload"]["markets"]:
            if m["event_ticker"].startswith(("KXNFLRSHYDS-25", "KXNFLTEAMTOTAL-25")): mk[m["ticker"]] = m
    elif l.startswith('{"kind":"candles"'):
        o = json.loads(l); t = o["key"].split("|")[0]
        if t.startswith(("KXNFLRSHYDS-25", "KXNFLTEAMTOTAL-25")): cd.setdefault(t, []).extend(o["payload"]["candlesticks"])
rows = []
for t, c in cd.items():
    m = mk.get(t)
    if not m or m.get("result") not in ("yes", "no"): continue
    ev = m["event_ticker"].split("-")[1]            # 25DEC28PITCLE
    ab = ev[7:]; ds = pd.to_datetime(ev[:7], format="%y%b%d").strftime("%Y-%m-%d")
    g = sched[(sched.gameday == ds) & sched.key.map(lambda k: k == ab or k.replace("LA", "LAR") == ab or k.replace("JAX", "JAC") == ab)]
    if len(g) != 1: rows.append({"ticker": t, "skip": "no_game_match"}); continue
    g = g.iloc[0]; team = t.split("-")[2][:3]
    if t.startswith("KXNFLRSHYDS"):
        team = t.split("-")[2][len(ab):][:3] if False else t.split("-")[2][len(ab):][:3]
    # pre-game mid: last candle ending <= ko - 30 min with both bid and ask
    cut = (g.ko - pd.Timedelta(minutes=30)).timestamp()
    def px(q): return q.get("close_dollars", q.get("close")) if q else None
    pts = sorted((x["end_period_ts"], (float(px(x["yes_bid"])) + float(px(x["yes_ask"]))) / 2) for x in c
                 if x["end_period_ts"] <= cut and px(x.get("yes_bid")) is not None and px(x.get("yes_ask")) is not None)
    if not pts: rows.append({"ticker": t, "skip": "no_pregame_candle"}); continue
    rows.append({"ticker": t, "game_id": g.game_id, "fam": t.split("-")[0], "strike": m["floor_strike"], "p": pts[-1][1],
                 "y": 1.0 if m["result"] == "yes" else 0.0, "team_raw": t.split("-")[2], "home": g.home_team, "away": g.away_team})
R = pd.DataFrame(rows)
print(R.get("skip", pd.Series(dtype=str)).value_counts().to_dict(), "usable:", int(R.p.notna().sum()) if "p" in R else 0)
R = R[R.p.notna()].copy()
def team_of(r):
    alias = {"JAX": "JAC", "LA": "LA"}
    hits = [tm for tm in (r.home, r.away) if r.team_raw.startswith(alias.get(tm, tm))]
    return max(hits, key=len) if hits else None
R["team"] = R.apply(team_of, axis=1)
R = R.merge(cx[["game_id", "posteam", "d"]].rename(columns={"posteam": "team"}), on=["game_id", "team"], how="left")
print("team resolved:", int(R.team.notna().sum()), "of", len(R), "| cross joined:", int(R.d.notna().sum()))
R = R.dropna(subset=["d"])
R = R[(R.p > 0.02) & (R.p < 0.98)]
res = {"n_markets": int(len(R)), "n_games": int(R.game_id.nunique()), "by_family": R.fam.value_counts().to_dict()}
if len(R) >= 10:
    R["lp"] = np.log(R.p / (1 - R.p)); R["resid_y"] = R.y - R.p
    R["lp_dm"] = R.lp - R.groupby("fam").lp.transform("mean")
    rng = np.random.default_rng(11); gm = R.game_id.to_numpy(); ug = np.unique(gm); idx = {g: np.where(gm == g)[0] for g in ug}
    def slope(x, y): return float(np.cov(x, y)[0, 1] / np.var(x)) if np.var(x) > 0 else float("nan")
    for name, y in (("price_on_d (logit p, family-demeaned)", R.lp_dm), ("outcome_resid_on_d (y - p)", R.resid_y)):
        b = slope(R.d, y); bs = []
        for _ in range(2000):
            pk = np.concatenate([idx[g] for g in rng.choice(ug, len(ug))]); bs.append(slope(R.d.to_numpy()[pk], y.to_numpy()[pk]))
        res[name] = {"slope": b, "ci95": [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))]}
    res["sd_d"] = float(R.d.std())
print(json.dumps(res, indent=1)); safe_out(OUT / "part_b_application.json").write_text(json.dumps(res, indent=1))
