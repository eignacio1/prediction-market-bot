"""W84.2 driver (writes only under 12_EXPLORATORY via safe_out; the mass-tier files are then copied to qualitative_data/pam/nba/ by hand): assign (Part A), grade Muse, stability (Part B1). Writes to qualitative_data/pam/nba/ and results dir.

    python3 run.py --store <NBA_EVENTS/raw> --claims <claims.jsonl> --out <qualitative_data/pam/nba> --results <dir>
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import mass_tier as mt
from _fence import safe_out

MET = ("MET", "MET_PARTIAL")


def names_frame(pg):
    n = pg.drop_duplicates(["season", "person_id"])[["season", "person_id", "first_name", "family_name", "team_tricode"]].copy()
    n["name"] = n["first_name"].fillna("") + " " + n["family_name"].fillna("")
    n["key"] = n["name"].map(mt.norm)
    return n


def jsonable(x):
    if isinstance(x, (np.floating, float)):
        return None if np.isnan(x) else round(float(x), 4)
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


def season_end_rows(se, names):
    nm = names.set_index(["season", "person_id"])
    rows = []
    keep = ["gp", "mpg", "usg", "ts", "ast_pct", "tov_pct", "oreb_pct", "dreb_pct", "blk_pct", "ftr", "tpa_rate", "tp_pct", "pf36",
            "rim_freq", "rim_fg", "rim_att_pg", "mid_att_pg", "mid_efg", "pu3_att_pg", "pu3_pct", "bench_usg", "bench_g", "m17_z",
            "trans_freq", "trans_ppp", "post_poss_pg", "roll_poss_pg", "touches_pg", "drives_pg", "potast_pg"]
    for (s, pid), r in se.iterrows():
        x = r.to_dict()
        a = mt.assign_row(x)
        rows.append({
            "season": int(s), "person_id": int(pid), "name": nm.loc[(s, pid), "name"], "team": nm.loc[(s, pid), "team_tricode"],
            "qualified": bool(r["qualified"]),
            "signals": {k: jsonable(x.get(k)) for k in keep if k in x},
            "signal_sources": {"event_store": "computed", "muse_reported": [k for k in ("trans_freq", "trans_ppp", "post_poss_pg", "roll_poss_pg",
                               "touches_pg", "drives_pg", "potast_pg") if mt._ok(x.get(k))]},
            "factors": {k: v for k, v in a.items() if k.startswith("PRF")},
            "modifiers": {k: v for k, v in a.items() if k.startswith("M-")},
        })
    return rows


def counts(rows):
    out = {}
    for s in mt.SEASONS:
        rs = [r for r in rows if r["season"] == s]
        q = [r for r in rs if r["qualified"]]
        d = {"player_seasons": len(rs), "qualified": len(q), "factors": {}}
        for fid in mt.ALL_IDS:
            key = "factors" if fid.startswith("PRF") else "modifiers"
            c = {"MET": 0, "MET_PARTIAL": 0, "NOT_MET": 0, "UNSCORED": 0}
            for r in q:
                c[r[key][fid]["status"]] += 1
            d["factors"][fid] = c
        out[str(s)] = d
    return out


def flags_for(sig, ids):
    recs = sig.to_dict("records")
    return pd.DataFrame([{f: mt.status(f, r)[0] in MET for f in ids} for r in recs], index=sig.index)


def stable_tab(a, b, ids, label):
    """a, b: boolean frames indexed identically (qualified in both). Per factor: n, base rate, retention, kappa."""
    rows = []
    for f in ids:
        x, y = a[f].values, b[f].values
        n = len(x)
        if n == 0 or x.sum() + y.sum() == 0:
            rows.append({"factor": f, "scope": label, "n": n, "met_a": int(x.sum()), "met_b": int(y.sum()), "retention": None, "kappa": None})
            continue
        po = (x == y).mean()
        pe = x.mean() * y.mean() + (1 - x.mean()) * (1 - y.mean())
        kappa = (po - pe) / (1 - pe) if pe < 1 else None
        ret = (x & y).sum() / x.sum() if x.sum() else None
        rows.append({"factor": f, "scope": label, "n": n, "met_a": int(x.sum()), "met_b": int(y.sum()),
                     "retention": None if ret is None else round(float(ret), 3), "kappa": None if kappa is None else round(float(kappa), 3)})
    return rows


def scoreable_ids(rows):
    """Factors/modifiers that have at least one scored clause for some player-season, from the event store alone (no Muse)."""
    ids = []
    for fid in mt.ALL_IDS:
        key = "factors" if fid.startswith("PRF") else "modifiers"
        if any(r[key][fid]["status"] != "UNSCORED" for r in rows):
            ids.append(fid)
    return ids


def stability(pg, se_by_season, ids):
    out = []
    half_cols = [c for c in mt.SUM_COLS if c in pg.columns]
    store_ids = [i for i in ids if i not in ("PRF-6", "PRF-7", "PRF-13", "M-17")]  # Muse-snapshot or team-relative: no split-half
    for s in mt.SEASONS:
        d = pg[pg.season == s].copy()
        d["gno"] = d.groupby("person_id").cumcount()
        d["half"] = (d["gno"] % 2)  # odd/even games: removes schedule-order drift; split-half reliability
        sums = {h: d[d.half == h].groupby("person_id")[half_cols].sum() for h in (0, 1)}
        common = sums[0].index.intersection(sums[1].index)
        sa, sb = mt.signals_from_sums(sums[0].loc[common]), mt.signals_from_sums(sums[1].loc[common])
        ok = (sa.gp >= 8) & (sb.gp >= 8) & (sa.mpg >= mt.QUAL_MPG) & (sb.mpg >= mt.QUAL_MPG)
        sa, sb = sa[ok], sb[ok]
        for fid in store_ids:
            pass
        fa, fb = flags_for(sa, store_ids), flags_for(sb, store_ids)
        out += stable_tab(fa, fb, store_ids, f"split-half(odd/even games) {s}")
    # YoY on season-end flags (store-computed + Muse-reported where available)
    for s in mt.SEASONS[:-1]:
        a, b = se_by_season[s], se_by_season[s + 1]
        idx = a[a.qualified].index.get_level_values(1).intersection(b[b.qualified].index.get_level_values(1))
        A = a.reset_index(level=0, drop=True).loc[idx]
        B = b.reset_index(level=0, drop=True).loc[idx]
        yids = [i for i in ids]
        fa, fb = flags_for(A, yids), flags_for(B, yids)
        out += stable_tab(fa, fb, yids, f"year-over-year {s}->{s + 1}")
    return pd.DataFrame(out)


def muse_grade(muse, pg, names):
    """GP recompute. Play-type records are per team stint -> compare to store GP for that team; tracking records are
    player-season totals -> compare to store GP summed over teams."""
    gp_t = pg.groupby(["season", "person_id", "team_tricode"])["g"].sum().to_frame("store_gp").reset_index()
    gp_s = pg.groupby(["season", "person_id"])["g"].sum().to_frame("store_gp").reset_index()
    m = muse.dropna(subset=["gp"]).copy()
    m["key"] = m["player"].map(mt.norm)
    nm = names[["season", "person_id", "key"]].drop_duplicates(["season", "key"])
    m = m.merge(nm, on=["season", "key"], how="left")
    unmatched = int(m.person_id.isna().sum())
    m = m.dropna(subset=["person_id"])
    m["fam"] = np.where(m.metric.str.startswith("play-type frequency"), "play-type frequency", np.where(
        m.metric.str.startswith("play-type points"), "play-type PPP", "tracking: " + m.metric.str.split(" ").str[0]))
    pt = m[m.fam.str.startswith("play-type")].merge(gp_t, left_on=["season", "person_id", "team"], right_on=["season", "person_id", "team_tricode"], how="left")
    tr = m[m.fam.str.startswith("tracking")].merge(gp_s, on=["season", "person_id"], how="left")
    m = pd.concat([pt, tr], ignore_index=True)
    unmatched += int(m.store_gp.isna().sum())
    m = m.dropna(subset=["store_gp"]).copy()
    m["diff"] = m["gp"] - m["store_gp"]
    m["match"] = m["diff"] == 0
    m["near"] = m["diff"].abs() <= 1
    g = m.groupby(["fam", "season"]).agg(n=("match", "size"), exact=("match", "sum"), within1=("near", "sum"),
                                          mean_diff=("diff", "mean"), min_diff=("diff", "min"), max_diff=("diff", "max"))
    g["exact_rate"] = (g["exact"] / g["n"]).round(4)
    by_season = m.groupby("season").agg(n=("match", "size"), exact=("match", "sum"), within1=("near", "sum"))
    return m, g, by_season, unmatched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--claims", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--results", required=True)
    a = ap.parse_args()
    out, res = Path(a.out), Path(a.results)
    pg = mt.load_player_games(Path(a.store))
    names = names_frame(pg)
    muse = mt.load_muse(Path(a.claims))
    msig, muse_k, joined = mt.muse_signals(muse, names[["season", "person_id", "key"]].drop_duplicates(["season", "key"]))
    se_all = mt.season_end(pg, msig)
    rows = season_end_rows(se_all, names)
    with open(safe_out(out / "mass_tier_season_end.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")
    cn = counts(rows)
    # Muse coverage
    cov = {}
    for s in mt.SEASONS:
        q = se_all.loc[s]
        q = q[q.qualified]
        cov[str(s)] = {"qualified": int(len(q)), "with_muse_playtype": int(q["trans_freq"].notna().sum()) if "trans_freq" in q else 0}
    safe_out(out / "mass_tier_counts.json").write_text(json.dumps({"qualifier": {"gp": mt.QUAL_GP, "mpg": mt.QUAL_MPG}, "counts": cn, "muse_coverage": cov}, indent=1))
    # point-in-time 2026
    pit = mt.pit_table(pg, 2026)
    pit["pit_qualified"] = (pit.gp >= mt.PIT_GP) & (pit.mpg >= mt.QUAL_MPG)
    pq = pit[pit.pit_qualified].copy()
    recs = pq.to_dict("records")
    met, unsc = [], []
    for r in recs:
        mm = []
        for fid in mt.ALL_IDS:
            st, _ = mt.status(fid, r, pit=True)
            if st in MET:
                mm.append(fid)
        met.append("|".join(mm))
    pq["factors_met"] = met
    pq[["person_id", "game_id", "game_date", "gp", "factors_met"]].to_csv(safe_out(out / "mass_tier_pit_2026.csv"), index=False)
    # Muse grade
    mg, g, bys, unmatched = muse_grade(muse, pg, names)
    g.to_csv(safe_out(res / "muse_grade_gp.csv"))
    mg[~mg.match][["player", "season", "metric", "split", "gp", "store_gp", "diff", "id"]].head(200).to_csv(safe_out(res / "muse_grade_gp_mismatches.csv"), index=False)
    # stability
    ids = scoreable_ids(rows)
    se_by = {s: se_all.loc[s].assign(_s=s).drop(columns="_s") for s in mt.SEASONS}
    se_by = {s: se_all[se_all.index.get_level_values(0) == s] for s in mt.SEASONS}
    st = stability(pg, se_by, ids)
    st.to_csv(safe_out(res / "stability.csv"), index=False)
    summary = {"muse_grade": {"n": int(len(mg)), "exact": int(mg.match.sum()), "within1": int(mg.near.sum()), "unmatched_names": unmatched,
                              "by_family_season": g.reset_index().to_dict("records"), "by_season": bys.reset_index().to_dict("records")},
               "pit_rows": int(len(pit)), "pit_qualified_rows": int(len(pq))}
    safe_out(res / "partA_summary.json").write_text(json.dumps(summary, indent=1, default=jsonable))
    print(json.dumps(summary["muse_grade"], indent=1, default=jsonable)[:3000])
    print(json.dumps(cn["2026"]["factors"], default=jsonable)[:2500])


if __name__ == "__main__":
    main()
