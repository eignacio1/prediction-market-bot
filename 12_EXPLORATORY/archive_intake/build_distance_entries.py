"""W113.4 Part C -- 12 NEW NBA index entries: opponent FG% and shot share allowed by exact-distance bin (NBA.com bins; the
family graded VERIFIED in GRADES.md). Uses 111.4's API unchanged (situation_splits.Situation / build_entry; build_index loaders;
score_leaves.score). Values come from the bot's event store. Run:
  PYTHONPATH=src python3 12_EXPLORATORY/archive_intake/build_distance_entries.py <settled_dir>
Writes entries/*.json, team_percentiles.json, leaf_scores.json under 12_EXPLORATORY/archive_intake/."""
import importlib.util, json, sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nba_engine import situation_splits as ss
from prediction_market_bot.archive_intake import nba_distance_filters as df


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, HERE.parent / rel)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m


bi = load("build_index", "granularity_index_nba/build_index.py")
sl = load("score_leaves", "granularity_index_nba/score_leaves.py")
EDGES = {"lt5": (0, 5), "5_9": (5, 10), "10_14": (10, 15), "15_19": (15, 20), "20_24": (20, 25), "25plus": (25, 99)}
TOTAL, SPREAD = bi.TOTAL, bi.SPREAD


def inbin(b):
    lo, hi = EDGES[b]
    return lambda f: (f.dist_exact >= lo) & (f.dist_exact < hi)


S = ss.Situation
SITS = []
for b in df.BINS:
    SITS.append(S(f"opp_fg_pct_{b}", "make", inbin(b), "team", "dfn", False, 150, ((TOTAL, "under", f"{b}ft"), (SPREAD, "cover", f"{b}ft"))))
    SITS.append(S(f"opp_fga_share_{b}", f"in_{b}", lambda f: f.dist_exact >= 0, "team", "dfn", False, 300, ((TOTAL, "over", f"{b}ft-volume"),)))


def frame():
    games = bi.load_games()
    fr = bi.load_shot_frame(games)
    fr["dist_exact"] = np.hypot(fr.x_legacy, fr.y_legacy) / 10.0
    for b in df.BINS:
        lo, hi = EDGES[b]
        fr[f"in_{b}"] = ((fr.dist_exact >= lo) & (fr.dist_exact < hi)).astype(float)
    return games, fr


def main():
    settled = sys.argv[1]
    games, fr = frame()
    season = 2026
    ent_dir = HERE / "entries"
    prof = defaultdict(dict)
    sched = bi.rd("schedule", season)
    abbr = {}
    for side in ("home", "away"):
        abbr.update(dict(zip(sched[f"{side}_team_id"], sched[f"{side}_team_abbreviation"])))
    from prediction_market_bot.nfl_engine import granularity_index as gi
    summ = []
    for sit in SITS:
        best, opp = bi.pick_units(fr, sit, season, 82)
        if best is None:
            summ.append({"name": sit.name, "ok": False}); continue
        e = {"points": {str(g): ss.build_entry(fr, sit, best, season, g, opp=opp, opp_games=g) for g in bi.SAMPLE_POINTS},
             "name": sit.name, "season": season, "unit_shown": best, "opp_shown": opp, "metric": sit.metric, "side": sit.side,
             "markets": [{"family": f, "line": l, "direction": d} for f, l, d in sit.markets], "source_family_grade": "VERIFIED (GRADES.md)"}
        safe_out(ent_dir / f"{sit.name}.json").write_text(json.dumps(e, indent=1, default=bi.jsonable))
        p = e["points"]["82"]
        summ.append({"name": sit.name, "ok": p.get("ok", False), "rank_history": p.get("rank_history"), "of_history": p.get("of_history"),
                     "trait": (p.get("stability") or {}).get("trait"), "split_half_r": (p.get("stability") or {}).get("r_spearman_brown")})
        plays, spec = ss.plays_for(fr, sit), ss.spec_for(sit)
        t = gi.split(plays, spec, season=season, games=82); t = t[t.n >= sit.min_n]
        for u, pc in zip(t.unit, t.value.rank(pct=True, method="average")):
            prof[abbr.get(u, str(u))][sit.name] = float(pc)
    safe_out(HERE / "team_percentiles.json").write_text(json.dumps(prof, indent=1))
    safe_out(HERE / "entries_summary.json").write_text(json.dumps(summ, indent=1, default=bi.jsonable))
    # per-leaf scoring on the 2026-27 shadow rows, reusing 111.4's scorer with this module's leaf function
    from prediction_market_bot.quant import retro_route as rr
    rows = sl.load_rows(settled)
    def leaves_for(row, prof_, entry):
        away, home = row["game_key"].split(":")[1].split("@")
        fam = row["market_type"].removeprefix("NBA_")
        h, a = prof_.get(home, {}).get(entry), prof_.get(away, {}).get(entry)
        return df.nf.total_leaf(h, a) if fam in df.nf.TOTAL_FAMILIES else df.side_leaf(entry, h, a)
    sl.leaves_for = leaves_for
    fams = {s.name: sorted({sl.FAMILY_OF[m[0]] for m in s.markets if m[0] in sl.FAMILY_OF}) for s in SITS}
    res = sl.score(rows, dict(prof), fams)
    fit_g, test_g = rr.split_games(rows)
    out = {"summary": {"rows": len(rows), "fit_games": len(fit_g), "test_games": len(test_g), "leaves": len(res),
                       "thin": sum(r["thin"] for r in res), "routed": sum(r["arm"] != "NO_BET" for r in res),
                       "reportable": sum("test_mean" in r for r in res), "bh": sum(r["bh"] for r in res), "drafts": sum(r["draft"] for r in res)},
           "leaves": res}
    safe_out(HERE / "leaf_scores.json").write_text(json.dumps(out, indent=1, default=bi.jsonable))
    print(json.dumps(out["summary"], indent=1)); print(json.dumps(summ, indent=0, default=bi.jsonable)[:3000])


if __name__ == "__main__":
    main()
