"""W80.3 Part A: run-box entry, positive control for the granularity-index machine. Read-only on the event store."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nfl_engine import granularity_index as gi

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "exp_output" / "NFL_EVENTS" / "raw"
OUT = Path(__file__).parent / "results"

cols = ["game_id", "play_id", "season", "week", "season_type", "posteam", "defteam", "play_type", "qb_kneel",
        "qb_scramble", "two_point_attempt", "yards_gained", "success", "epa", "tackled_for_loss", "rush_attempt"]
pbp = pd.concat([pd.read_parquet(p, columns=cols) for p in sorted((RAW / "pbp").glob("pbp_*.parquet"))])
ftn = pd.concat([pd.read_parquet(p, columns=["game_id", "play_id", "n_defense_box"]) for p in sorted((RAW / "ftn").glob("ftn_*.parquet"))])
ftn = ftn.drop_duplicates(["game_id", "play_id"])
d = pbp[(pbp.season_type == "REG") & (pbp.play_type == "run") & (pbp.qb_kneel != 1) & (pbp.qb_scramble != 1)
        & (pbp.two_point_attempt != 1)].merge(ftn, on=["game_id", "play_id"], how="left")
d["box_n"] = d.n_defense_box.where(d.n_defense_box > 0)
d["box"] = np.where(d.box_n.isna(), None, np.where(d.box_n >= 8, "loaded", "light"))
d["stuffed"] = (d.yards_gained <= 0).astype(float)
d["success"] = d.success.astype(float)
n_all, n_box = len(d), int(d.box_n.notna().sum())
print(f"rushes={n_all} with_box={n_box} ({n_box/n_all:.1%})")
d = d.dropna(subset=["box"])

specs = {
    "def_success": gi.SplitSpec("defteam", "box", "success", higher_is_better=False),
    "off_success": gi.SplitSpec("posteam", "box", "success", True),
    "off_stuffed": gi.SplitSpec("posteam", "box", "stuffed", False),
    "def_stuffed": gi.SplitSpec("defteam", "box", "stuffed", True),
}
tabs = {k: gi.game_table(d, s) for k, s in specs.items()}
# how often each defense shows a light box
share = d.groupby(["season", "defteam"]).box.apply(lambda s: (s == "light").mean()).reset_index(name="light_share")
share_n = d.groupby(["season", "defteam"]).size().reset_index(name="n")
share = share.merge(share_n)
share.to_csv(safe_out(OUT / "defense_light_box_share.csv"), index=False)

res = {"coverage": {"rushes": n_all, "with_box": n_box}, "stability": {}, "ranks_2026": [], "league": {}}
for k, s in specs.items():
    for g in (4, 6, 8, 12):
        for b in ("loaded", "light"):
            res["stability"][f"{k}|{b}|g{g}"] = gi.stability(d, s, b, g, table=tabs[k])
# league means + k per bucket
league, K = {}, {}
for k, s in specs.items():
    sp = gi.split(d, s, table=tabs[k])
    for b in ("loaded", "light"):
        sub = sp[sp[s.by] == b]
        league[(k, b)] = float(sub.s.sum() / sub.n.sum()); K[(k, b)] = gi.estimate_k(sub)
res["league"] = {f"{k}|{b}": {"mean": v, "k": K[(k, b)]} for (k, b), v in league.items()}

# 2026 to date ranks
g26 = int(d[d.season == 2026].groupby("defteam").game_id.nunique().max())
rows = []
for k, s in specs.items():
    for unit in sorted(d[d.season == 2026][s.unit].unique()):
        for b in ("loaded", "light"):
            gms = int(d[(d.season == 2026) & (d[s.unit] == unit)].game_id.nunique())
            r = gi.rank(d, s, unit, b, 2026, gms, table=tabs[k])
            if r["ok"]:
                r["entry"] = k
                r["stability"] = res["stability"].get(f"{k}|{b}|g{min((4, 6, 8, 12), key=lambda x: abs(x-gms))}")
                rows.append(r)
res["ranks_2026"] = rows
pd.DataFrame([{k: v for k, v in r.items() if k != "stability"} for r in rows]).to_csv(safe_out(OUT / "ranks_2026.csv"), index=False)

# 2026 matchup crosses: week 7 hypothetical = every ordered (off, def) pair is too many; use the actual 2026 games played
sched = pd.concat([pd.read_parquet(p) for p in (RAW / "schedules").glob("schedules_*.parquet")])
sched = sched[(sched.season == 2026) & (sched.game_type == "REG")]
off_sp = gi.split(d, specs["off_success"], season=2026, table=tabs["off_success"])
dfn_sp = gi.split(d, specs["def_success"], season=2026, table=tabs["def_success"])
off_st = gi.split(d, specs["off_stuffed"], season=2026, table=tabs["off_stuffed"])
dfn_st = gi.split(d, specs["def_stuffed"], season=2026, table=tabs["def_stuffed"])
sh = d[d.season == 2026]
def_share = sh.groupby("defteam").box.value_counts(normalize=True).unstack().fillna(0)
off_faced = sh.groupby("posteam").box.value_counts(normalize=True).unstack().fillna(0)
lg_share = sh.box.value_counts(normalize=True).to_dict()
def ns(frame, unit, b, col):
    r = frame[(frame[col] == unit) & (frame.box == b)]
    return (float(r.n.iloc[0]), float(r.s.iloc[0])) if len(r) else (0.0, 0.0)
def bk(spec, b): return spec.by
cross_rows = []
for _, g in sched.iterrows():
    for o, df in ((g.away_team, g.home_team), (g.home_team, g.away_team)):
        if o not in off_faced.index or df not in def_share.index: continue
        freq = gi.show_frequency(def_share.loc[df].to_dict(), off_faced.loc[o].to_dict(), lg_share)
        out = {}
        for tag, (osp, dsp) in {"success": (off_sp, dfn_sp), "stuffed": (off_st, dfn_st)}.items():
            ok, dk = ("off_" + tag, "def_" + tag)
            off = {b: ns(osp, o, b, "posteam") for b in ("loaded", "light")}
            dfn = {b: ns(dsp, df, b, "defteam") for b in ("loaded", "light")}
            lgm = {b: league[(ok, b)] for b in ("loaded", "light")}
            kk = {b: K[(ok, b)] for b in ("loaded", "light")}
            ov = {"off": (sum(v[0] for v in off.values()), sum(v[1] for v in off.values())),
                  "dfn": (sum(v[0] for v in dfn.values()), sum(v[1] for v in dfn.values())),
                  "league": sum(freq_b * lgm[b] for b, freq_b in lg_share.items()), "k": float(np.nanmean([x for x in kk.values() if np.isfinite(x)] or [np.inf]))}
            c = gi.cross(off, dfn, lgm, freq, kk, ov)
            out[tag] = c
        cross_rows.append({"week": int(g.week), "off": o, "def": df, "light_freq": freq.get("light"),
                           "succ_expected": out["success"].expected, "succ_delta": out["success"].delta,
                           "stuff_expected": out["stuffed"].expected, "stuff_delta": out["stuffed"].delta})
cx = pd.DataFrame(cross_rows)
cx.to_csv(safe_out(OUT / "matchup_crosses_2026.csv"), index=False)
res["extreme_crosses"] = {
    "success_delta_top": cx.nlargest(5, "succ_delta").to_dict("records"),
    "success_delta_bottom": cx.nsmallest(5, "succ_delta").to_dict("records"),
    "stuff_delta_top": cx.nlargest(5, "stuff_delta").to_dict("records"),
}
safe_out(OUT / "part_a_results.json").write_text(json.dumps(res, indent=1, default=str))
print("stability (trait? by bucket, g=8):")
for key, v in res["stability"].items():
    if key.endswith("g8") or key.endswith("g12"):
        print(key, v.get("trait"), v.get("r_spearman_brown"), v.get("ci95"), v.get("n_unit_seasons"), v.get("reason"))
print(res["league"])
print(cx.describe().T[["mean", "std", "min", "max"]])
print(cx.nlargest(5, "succ_delta")); print(cx.nsmallest(5, "succ_delta"))
