"""W113.2 Part B -- NFL granularity index, machinery once (operator directive D-06: examples are illustrations, not specs).

A *Situation* = (metric, situation filter, unit side). The generic machine (nfl_engine/granularity_index.py) supplies, for every
entry: split (point-in-time value), rank vs every team-season at the same games-played point + split-half stability, the matchup
cross (offence split x defence split x how often the situation occurs), the market map, and a filter. Application = Part C.

Sources (all free): nflverse play-by-play 2022..2026; nflverse participation 2022..2025 (defenders in box, offence / defence
personnel, formation, man-zone, coverage type); FTN charting 2022..2026 (motion yes/no, play action, blitzers, box count).
Registered gaps (paid / not published): receiver route trees by alignment, motion direction + boundary side, pre-snap
alignment distances, coverage shell at the snap beyond the participation label, 2026 participation (not yet released).

usage: python3 -E build_index.py --pbp-dir DIR --pbp26 FILE --ftn-dir DIR --part-dir DIR [--ftn26 FILE]
Inputs are untrusted downloaded data: read only.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nfl_engine import granularity_index as gi  # noqa: E402

TOTAL, TEAMTOT, SPREAD, GAME = "KXNFLTOTAL", "KXNFLTEAMTOTAL", "KXNFLSPREAD", "KXNFLGAME"
RSHYDS, PASSYDS = "KXNFLRSHYDS", "KXNFLPASSYDS"
SAMPLE_POINTS = (6, 10, 17)
SHOW_SEASON = 2025          # the prior season: the point-in-time basis for any 2026 game
YEARS = (2022, 2023, 2024, 2025)


@dataclass(frozen=True)
class Situation:
    name: str
    metric: str                 # column of the frame (0/1 for rates)
    where: object               # frame -> bool mask (the situation)
    side: str                   # "off" (posteam) | "dfn" (defteam)
    higher_is_better: bool      # for the UNIT (a defence that stuffs more is better)
    min_n: int
    markets: tuple
    needs: str = "pbp"          # pbp | part | ftn


S = Situation
RUN = lambda f: f.play_type == "run"      # noqa: E731
PASS = lambda f: f.play_type == "pass"    # noqa: E731
LOADED = lambda f: f.defenders_in_box >= 7   # noqa: E731
LIGHT = lambda f: f.defenders_in_box <= 6    # noqa: E731
WR3 = lambda f: f.offense_personnel.fillna("").str.contains("3 WR")   # noqa: E731
SITUATIONS = [
    S("rush_success_vs_loaded_box", "success", lambda f: RUN(f) & LOADED(f), "off", True, 40, ((RSHYDS, "over", "box"), (TEAMTOT, "over", "run"), (SPREAD, "cover", "run"), (TOTAL, "over", "run")), "part"),
    S("rush_success_vs_light_box", "success", lambda f: RUN(f) & LIGHT(f), "off", True, 80, ((RSHYDS, "over", "box"), (TEAMTOT, "over", "run"), (SPREAD, "cover", "run")), "part"),
    S("rush_success_allowed_loaded_box", "success", lambda f: RUN(f) & LOADED(f), "dfn", False, 40, ((RSHYDS, "under", "box"), (TEAMTOT, "under", "run"), (TOTAL, "under", "run")), "part"),
    S("rush_stuff_rate_defence", "stuffed", RUN, "dfn", True, 150, ((RSHYDS, "under", "stuff"), (TEAMTOT, "under", "stuff"), (TOTAL, "under", "stuff")), "pbp"),
    S("rush_stuffed_rate_offence", "stuffed", RUN, "off", False, 150, ((RSHYDS, "under", "stuff"), (TEAMTOT, "under", "stuff")), "pbp"),
    S("loaded_box_rate_faced", "loaded", lambda f: RUN(f) & f.defenders_in_box.notna(), "off", False, 150, ((RSHYDS, "under", "box"), (TOTAL, "under", "box")), "part"),
    S("rush_success_with_motion", "success", lambda f: RUN(f) & (f.is_motion == 1), "off", True, 40, ((RSHYDS, "over", "motion"), (TEAMTOT, "over", "motion")), "ftn"),
    S("pass_success_vs_man", "success", lambda f: PASS(f) & (f.defense_man_zone_type == "MAN_COVERAGE"), "off", True, 80, ((PASSYDS, "over", "coverage"), (TEAMTOT, "over", "coverage"), (SPREAD, "cover", "coverage")), "part"),
    S("pass_success_vs_zone", "success", lambda f: PASS(f) & (f.defense_man_zone_type == "ZONE_COVERAGE"), "off", True, 120, ((PASSYDS, "over", "coverage"), (TEAMTOT, "over", "coverage"), (SPREAD, "cover", "coverage")), "part"),
    S("pass_success_allowed_vs_man", "success", lambda f: PASS(f) & (f.defense_man_zone_type == "MAN_COVERAGE"), "dfn", False, 80, ((PASSYDS, "under", "coverage"), (TOTAL, "under", "coverage")), "part"),
    S("pass_success_vs_cover3", "success", lambda f: PASS(f) & (f.defense_coverage_type == "COVER_3"), "off", True, 80, ((PASSYDS, "over", "coverage"), (TEAMTOT, "over", "coverage")), "part"),
    S("pass_success_allowed_cover6_vs_3wr", "success", lambda f: PASS(f) & (f.defense_coverage_type == "COVER_6") & WR3(f), "dfn", False, 20, ((PASSYDS, "under", "cover6"), (TOTAL, "under", "cover6")), "part"),
    S("pass_success_3wr_sets", "success", lambda f: PASS(f) & WR3(f), "off", True, 150, ((PASSYDS, "over", "personnel"), (TEAMTOT, "over", "personnel"), (TOTAL, "over", "personnel")), "part"),
    S("pass_success_allowed_vs_3wr", "success", lambda f: PASS(f) & WR3(f), "dfn", False, 150, ((PASSYDS, "under", "personnel"), (TOTAL, "under", "personnel")), "part"),
    S("three_wr_rate", "wr3", lambda f: f.offense_personnel.notna() & (PASS(f) | RUN(f)), "off", True, 300, ((TOTAL, "over", "personnel"), (PASSYDS, "over", "personnel")), "part"),
    S("pass_success_with_motion", "success", lambda f: PASS(f) & (f.is_motion == 1), "off", True, 60, ((PASSYDS, "over", "motion"), (TEAMTOT, "over", "motion")), "ftn"),
    S("play_action_success", "success", lambda f: PASS(f) & (f.is_play_action == 1), "off", True, 60, ((PASSYDS, "over", "play-action"), (TEAMTOT, "over", "play-action")), "ftn"),
    S("pass_success_vs_blitz", "success", lambda f: PASS(f) & (f.n_blitzers >= 1), "off", True, 60, ((PASSYDS, "over", "blitz"), (TEAMTOT, "over", "blitz")), "ftn"),
    S("blitz_rate_defence", "blitz", PASS, "dfn", True, 250, ((PASSYDS, "under", "pressure"), (TOTAL, "over", "variance")), "ftn"),
    S("red_zone_td_rate", "touchdown", lambda f: (PASS(f) | RUN(f)) & (f.yardline_100 <= 20), "off", True, 80, ((TEAMTOT, "over", "red-zone"), (TOTAL, "over", "red-zone")), "pbp"),
    S("red_zone_td_rate_allowed", "touchdown", lambda f: (PASS(f) | RUN(f)) & (f.yardline_100 <= 20), "dfn", False, 80, ((TEAMTOT, "under", "red-zone"), (TOTAL, "under", "red-zone")), "pbp"),
    S("third_down_success", "success", lambda f: (PASS(f) | RUN(f)) & (f.down == 3), "off", True, 100, ((TEAMTOT, "over", "third-down"), (TOTAL, "over", "third-down"), (SPREAD, "cover", "third-down")), "pbp"),
    S("third_down_success_allowed", "success", lambda f: (PASS(f) | RUN(f)) & (f.down == 3), "dfn", False, 100, ((TEAMTOT, "under", "third-down"), (TOTAL, "under", "third-down")), "pbp"),
    S("explosive_pass_rate", "explosive", lambda f: PASS(f) & f.yards_gained.notna(), "off", True, 150, ((PASSYDS, "over", "explosive"), (TOTAL, "over", "explosive")), "pbp"),
    S("explosive_pass_rate_allowed", "explosive", lambda f: PASS(f) & f.yards_gained.notna(), "dfn", False, 150, ((PASSYDS, "under", "explosive"), (TOTAL, "under", "explosive")), "pbp"),
]


def load_frame(a) -> pd.DataFrame:
    cols = ["season", "season_type", "week", "game_id", "play_id", "posteam", "defteam", "play_type", "success", "yards_gained",
            "touchdown", "down", "yardline_100", "epa"]
    fs = []
    for y in YEARS:
        p = pd.read_parquet(Path(a.pbp_dir) / f"pbp_{y}.parquet", columns=cols)
        pa = pd.read_parquet(Path(a.part_dir) / f"participation_{y}.parquet",
                             columns=["nflverse_game_id", "play_id", "defenders_in_box", "offense_personnel",
                                      "defense_man_zone_type", "defense_coverage_type"])
        pa = pa.set_axis(["game_id"] + list(pa.columns[1:]), axis=1)
        ft = pd.read_parquet(Path(a.ftn_dir) / f"ftn_{y}.parquet",
                             columns=["nflverse_game_id", "nflverse_play_id", "is_motion", "is_play_action", "n_blitzers"])
        ft = ft.set_axis(["game_id", "play_id"] + list(ft.columns[2:]), axis=1)
        f = p.merge(pa.drop_duplicates(["game_id", "play_id"]), on=["game_id", "play_id"], how="left") \
             .merge(ft.drop_duplicates(["game_id", "play_id"]), on=["game_id", "play_id"], how="left")
        fs.append(f)
    f = pd.concat(fs, ignore_index=True)
    f = f[(f.season_type == "REG") & f.play_type.isin(["pass", "run"]) & f.posteam.notna() & f.defteam.notna()].copy()
    f["stuffed"] = (f.yards_gained <= 0).astype(float)
    f["loaded"] = (f.defenders_in_box >= 7).astype(float)
    f["wr3"] = f.offense_personnel.fillna("").str.contains("3 WR").astype(float)
    f["blitz"] = (f.n_blitzers >= 1).astype(float)
    f["explosive"] = (f.yards_gained >= 20).astype(float)
    f["touchdown"] = f.touchdown.astype(float)
    f["one"] = 1
    return f


def plays_for(f: pd.DataFrame, s: Situation, side=None):
    side = side or s.side
    d = f[s.where(f)].copy()
    d["unit"] = d.posteam if side == "off" else d.defteam
    return d.dropna(subset=["unit", s.metric])


def spec_for(s: Situation, side=None) -> gi.SplitSpec:
    return gi.SplitSpec("unit", "one", s.metric, s.higher_is_better, s.min_n)


def jsonable(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if o != o else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(type(o))


def build_entry(f, s, unit, games, opp=None):
    plays, spec = plays_for(f, s), spec_for(s)
    t = gi.game_table(plays, spec)
    r = gi.rank(plays, spec, unit, 1, SHOW_SEASON, games, table=t)
    st = gi.stability(plays, spec, 1, games, min_half_n=max(5, s.min_n // 6), table=t)
    out = {"split": r, "stability": st}
    me = gi.split(plays, spec, season=SHOW_SEASON, games=games, table=t)
    out["frequency_per_game"] = (float(me[me.unit == unit].n.iloc[0]) / games) if (me.unit == unit).any() else None
    if opp is not None:
        other = "dfn" if s.side == "off" else "off"
        oplays, ospec = plays_for(f, s, other), spec_for(s, other)
        ot = gi.split(oplays, ospec, season=SHOW_SEASON, games=games)
        mine = me[me.unit == unit]
        theirs = ot[ot.unit == opp]
        lg = float(me.s.sum() / me.n.sum())
        if len(mine) and len(theirs):
            k = gi.estimate_k(me)
            off_, dfn_ = (mine, theirs) if s.side == "off" else (theirs, mine)
            c = gi.cross({1: (float(off_.n.iloc[0]), float(off_.s.iloc[0]))}, {1: (float(dfn_.n.iloc[0]), float(dfn_.s.iloc[0]))},
                         {1: lg}, {1: 1.0}, {1: k})
            out["cross"] = {"unit": unit, "opponent": opp, "expected": c.expected, "league": lg,
                            "frequency_per_game": out["frequency_per_game"]}
    return out


def team_table(f, s, season=SHOW_SEASON, games=17):
    plays, spec = plays_for(f, s), spec_for(s)
    sp = gi.split(plays, spec, season=season, games=games)
    sp = sp[sp.n >= s.min_n]
    sp["pct"] = sp.value.rank(pct=True, method="average")
    return sp[["unit", "n", "value", "pct"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pbp-dir", required=True)
    ap.add_argument("--part-dir", required=True)
    ap.add_argument("--ftn-dir", required=True)
    a = ap.parse_args()
    f = load_frame(a)
    safe_out(HERE / "entries").mkdir(exist_ok=True)
    rows, table = [], {}
    for s in SITUATIONS:
        plays, spec = plays_for(f, s), spec_for(s)
        me = gi.split(plays, spec, season=SHOW_SEASON, games=17)
        me = me[me.n >= s.min_n]
        if me.empty:
            rows.append({"name": s.name, "ok": False, "reason": f"no team reaches n>={s.min_n} in {SHOW_SEASON}", "markets": len(s.markets)})
            continue
        best = me.sort_values("value", ascending=not s.higher_is_better).iloc[0].unit
        other = "dfn" if s.side == "off" else "off"
        om = gi.split(plays_for(f, s, other), spec_for(s, other), season=SHOW_SEASON, games=17)
        om = om[om.n >= s.min_n]
        opp = om.sort_values("value", ascending=other == "dfn").iloc[0].unit if len(om) else None
        e = {"points": {str(g): build_entry(f, s, best, g, opp) for g in SAMPLE_POINTS},
             "name": s.name, "season": SHOW_SEASON, "unit_shown": best, "opp_shown": opp, "metric": s.metric, "side": s.side,
             "higher_is_better": s.higher_is_better, "source": s.needs,
             "markets": [{"family": fam, "line": l, "direction": d} for fam, l, d in s.markets],
             "application": "pending Part C (score_leaves.py)"}
        safe_out(HERE / "entries" / f"{s.name}.json").write_text(json.dumps(e, indent=1, default=jsonable))
        p17 = e["points"]["17"]
        rows.append({"name": s.name, "ok": bool(p17["split"].get("ok")), "unit": best, "value": p17["split"].get("value"),
                     "n_plays": p17["split"].get("n_plays"), "rank_history": p17["split"].get("rank_history"),
                     "of_history": p17["split"].get("of_history"), "trait": (p17["stability"] or {}).get("trait"),
                     "split_half_r": (p17["stability"] or {}).get("r_spearman_brown"), "markets": len(s.markets), "source": s.needs})
        t = team_table(f, s)
        table[s.name] = {r.unit: {"pct": float(r.pct), "value": float(r.value), "n": int(r.n)} for r in t.itertuples()}
    safe_out(HERE / "index.json").write_text(json.dumps(rows, indent=1, default=jsonable))
    safe_out(HERE / "team_percentiles.json").write_text(json.dumps(
        {"data_through_utc": "2026-02-15T00:00:00Z", "basis": f"{SHOW_SEASON} regular season, 17 games, percentile of raw value among teams "
         "with n >= min_n", "entries": table}, indent=1))
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
