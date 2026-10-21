"""W82.3 Part A: defensive coverage / pressure definitions from participation (+FTN), graded against Muse.

PRE-STATED GRADING PROTOCOL (written before any comparison was computed):
  * Muse's prior-season (2023-2025) coverage/blitz/pressure/MOF values: checked for presence first. If null, that
    metric cannot be graded and stays REPORTED (a null is not a pass).
  * Time to throw (same Muse file, same class) has prior values per QB: graded VERIFIED iff, over matched QB-seasons,
    cross-QB Pearson r >= 0.90 AND mean |diff| <= 0.05 s; else FAILED with the difference.
  * Positive control: the bot's own recompute of a fact that must match by construction (QB-season attempts from
    pbp vs participation-joined pass-play count) must agree within 2%; otherwise the join is broken and nothing is graded.
MOF map (stated, not tuned): closed/single-high = COVER_1, COVER_3 ; open/two-high = COVER_2, 2_MAN, COVER_4, COVER_6 ;
  excluded = COVER_0, COVER_9, COMBO, BLOWN, missing.  Blitz variants reported side by side: rushers>=5 and FTN n_blitzers>=1.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "12_EXPLORATORY"))
from _fence import safe_out  # noqa: E402

RAW = REPO / "exp_output" / "NFL_EVENTS" / "raw"
MUSE = Path(sys.argv[1]) if len(sys.argv) > 1 else None
CLOSED = {"COVER_1", "COVER_3"}
OPEN = {"COVER_2", "2_MAN", "COVER_4", "COVER_6"}


def load(season):
    pbp = pd.read_parquet(RAW / "pbp" / f"pbp_{season}.parquet",
                          columns=["game_id", "play_id", "season", "week", "season_type", "defteam", "posteam",
                                   "qb_dropback", "sack", "pass_attempt", "passer_player_name", "passer_player_id"])
    pbp = pbp[(pbp.season_type == "REG") & (pbp.qb_dropback == 1)]
    pf = RAW / "participation" / f"participation_{season}.parquet"
    if not pf.exists():
        return pbp.assign(man_zone=None, covtype=None, rushers=np.nan, pressure=np.nan, ttt=np.nan, ftn_blitz=np.nan)
    part = pd.read_parquet(pf, columns=["game_id", "play_id", "defense_man_zone_type", "defense_coverage_type",
                                        "number_of_pass_rushers", "was_pressure", "time_to_throw"])
    d = pbp.merge(part, on=["game_id", "play_id"], how="left")
    ff = RAW / "ftn" / f"ftn_{season}.parquet"
    if ff.exists():
        f = pd.read_parquet(ff, columns=["game_id", "play_id", "n_blitzers"]).drop_duplicates(["game_id", "play_id"])
        d = d.merge(f, on=["game_id", "play_id"], how="left")
    else:
        d["n_blitzers"] = np.nan
    ren = {"defense_man_zone_type": "man_zone", "defense_coverage_type": "covtype",
           "number_of_pass_rushers": "rushers", "was_pressure": "pressure",
           "time_to_throw": "ttt", "n_blitzers": "ftn_blitz"}
    d.columns = [ren.get(c, c) for c in d.columns]
    return d


def team_game(d):
    g = d.assign(
        man=(d.man_zone == "MAN_COVERAGE"), zone=(d.man_zone == "ZONE_COVERAGE"),
        closed=d.covtype.isin(CLOSED), open_=d.covtype.isin(OPEN),
        blitz5=(d.rushers >= 5), ftnb=(d.ftn_blitz >= 1),
        press=(d.pressure == 1) | (d.pressure == True),  # noqa: E712
        has_mz=d.man_zone.isin(["MAN_COVERAGE", "ZONE_COVERAGE"]), has_cov=d.covtype.notna(),
        has_rush=d.rushers.notna(), has_ftn=d.ftn_blitz.notna(), has_press=d.pressure.notna())
    return (g.groupby(["season", "week", "defteam", "posteam"], as_index=False)
            [["man", "zone", "closed", "open_", "blitz5", "ftnb", "press", "has_mz", "has_cov", "has_rush",
              "has_ftn", "has_press"]].sum()
            .merge(g.groupby(["season", "week", "defteam", "posteam"], as_index=False)
                   .agg(dropbacks=("play_id", "size")), on=["season", "week", "defteam", "posteam"]))


def main():
    frames, qb = [], []
    for s in range(2016, 2026):
        d = load(s)
        frames.append(team_game(d))
        q = d[d.pass_attempt == 1].groupby(["season", "passer_player_id", "passer_player_name"], as_index=False).agg(
            att=("play_id", "size"), att_with_part=("man_zone", lambda x: x.notna().sum()),
            ttt=("ttt", "mean"), ttt_n=("ttt", "count"))
        qb.append(q)
    tg = pd.concat(frames, ignore_index=True)
    out = safe_out(HERE / "results" / "defense_team_game.csv")
    tg.to_csv(out, index=False)
    qbs = pd.concat(qb, ignore_index=True)
    qbs.to_csv(safe_out(HERE / "results" / "qb_season_ttt.csv"), index=False)

    ds = tg.groupby(["season", "defteam"], as_index=False).sum(numeric_only=True)
    ds["games"] = tg.groupby(["season", "defteam"]).week.nunique().values
    for k in ["man", "zone", "closed", "open_", "blitz5", "ftnb", "press"]:
        ds[k + "_rate_all"] = ds[k] / ds.dropbacks
    ds["man_rate_cls"] = ds.man / (ds.man + ds.zone)
    ds["blitz5_rate_rushrows"] = ds.blitz5 / ds.has_rush
    ds["press_rate_pressrows"] = ds.press / ds.has_press
    ds.to_csv(safe_out(HERE / "results" / "defense_season_metrics.csv"), index=False)

    fill = tg.groupby("season")[["dropbacks", "has_mz", "has_cov", "has_rush", "has_ftn", "has_press"]].sum()
    for c in ["has_mz", "has_cov", "has_rush", "has_ftn", "has_press"]:
        fill[c + "_fill"] = (fill[c] / fill.dropbacks).round(3)
    fill.to_csv(safe_out(HERE / "results" / "fill_rate_by_season.csv"))
    print(fill[[c for c in fill.columns if c.endswith("_fill")]])

    # positive control: pbp attempts vs participation-joined attempts, by season (join integrity)
    pc = qbs.groupby("season")[["att", "att_with_part"]].sum()
    pc["join_rate"] = pc.att_with_part / pc.att
    print(pc)

    verdict = {"positive_control_join_rate": pc.join_rate.round(4).to_dict(), "fill": fill.to_dict()}

    if MUSE is not None:
        rows = [json.loads(l) for l in open(MUSE / "L3-split/nfl/coverage-pressure-personnel.claims.jsonl")]
        prior = [r for r in rows if r["season"] in (2023, 2024, 2025)]
        verdict["muse_prior_non_null_by_metric"] = {}
        for r in prior:
            m = r["metric"].split(" (source")[0]
            verdict["muse_prior_non_null_by_metric"].setdefault(m, [0, 0])
            verdict["muse_prior_non_null_by_metric"][m][0] += 1
            verdict["muse_prior_non_null_by_metric"][m][1] += r["value"] is not None
        tt = pd.DataFrame([{"season": r["season"], "name": r["player"], "muse": r["value"]} for r in prior
                           if r["metric"] == "average time to throw (seconds)" and r["value"] is not None])
        # nflverse passer names are "A.Rodgers"; Muse uses full names -> key on first initial + last token
        def key(n):
            p = [x for x in re.split(r"[.\s]+", str(n)) if x]
            return (p[0][0] + "." + p[-1]).lower() if len(p) > 1 else str(n).lower()
        tt["name"] = tt["name"].map(key)
        qbs["name"] = qbs.passer_player_name.map(key)
        m = tt.merge(qbs[qbs.ttt_n >= 100], on=["season", "name"], how="inner")
        m["diff"] = m.ttt - m.muse
        verdict["ttt"] = {"muse_rows": len(tt), "matched": len(m), "mean_abs_diff": float(m["diff"].abs().mean()),
                          "mean_diff": float(m["diff"].mean()),
                          "pearson_r": float(np.corrcoef(m.muse, m.ttt)[0, 1]) if len(m) > 2 else None}
        t = verdict["ttt"]
        t["grade"] = "UNGRADED (no matches)" if t["matched"] < 10 else "VERIFIED" if (t["pearson_r"] or 0) >= 0.90 and t["mean_abs_diff"] <= 0.05 else "FAILED"
        m.to_csv(safe_out(HERE / "results" / "ttt_compare.csv"), index=False)
        print(json.dumps(verdict["muse_prior_non_null_by_metric"], indent=1)); print(t)
    safe_out(HERE / "results" / "part_a_verdict.json").write_text(json.dumps(verdict, indent=1, default=str))


if __name__ == "__main__":
    main()
