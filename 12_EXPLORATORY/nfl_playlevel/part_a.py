"""W128.3 Part A: play-level aggregates per team-game (EXP-NFLPLAYLEVEL-001).

Source (nflverse, free): pbp + pbp_participation (2016-2025; 2026 is not served) + ftn_charting (2022-2026), read from the
git-ignored event store at exp_output/NFL_EVENTS (build: c1_signal_ingestion/nfl_event_store.py --only pbp participation ftn schedules).
No market outcome (score, line, price) is read here. Output: team_game_playlevel.csv, one row per (game_id, team), counts only; the
point-in-time rolling tendencies are built from these counts, games strictly before the priced game, in run_playlevel.py / the filter.
"""
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out
import re
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "exp_output/NFL_EVENTS/raw"
TWO_HIGH = {"COVER_2", "2_MAN", "COVER_4", "COVER_6"}
ONE_HIGH = {"COVER_0", "COVER_1", "COVER_3", "COVER_9"}


def pers_class(s):
    """'1 C, 2 G, 1 QB, 1 RB, 2 T, 1 TE, 3 WR' -> '11' (RB digit, TE digit); 'other' if WR != 3 with 1RB 1TE etc. returned as RBTE."""
    if not isinstance(s, str):
        return None
    c = {k: int(n) for n, k in re.findall(r"(\d+) (\w+)", s)}
    return f"{c.get('RB', 0)}{c.get('TE', 0)}"


def load():
    pb, pa, ft = [], [], []
    for f in sorted((RAW / "pbp").glob("pbp_*.parquet")):
        s = int(f.stem[-4:])
        if s < 2016:
            continue
        d = pd.read_parquet(f, columns=["game_id", "play_id", "season_type", "week", "posteam", "defteam", "play_type", "qb_kneel", "qb_spike", "epa", "success", "pass", "rush"])
        d["season"] = s
        pb.append(d[(d.season_type == "REG") & d.play_type.isin(["pass", "run"]) & (d.qb_kneel != 1) & (d.qb_spike != 1) & d.posteam.notna()])
    for f in sorted((RAW / "participation").glob("participation_*.parquet")):
        pa.append(pd.read_parquet(f, columns=["game_id", "play_id", "offense_personnel", "defense_man_zone_type", "defense_coverage_type"]))
    for f in sorted((RAW / "ftn").glob("ftn_*.parquet")):
        ft.append(pd.read_parquet(f, columns=["game_id", "play_id", "is_motion"]))
    return pd.concat(pb), pd.concat(pa), pd.concat(ft)


def main():
    pb, pa, ft = load()
    d = pb.merge(pa, on=["game_id", "play_id"], how="left").merge(ft, on=["game_id", "play_id"], how="left")
    d["has_part"] = d.offense_personnel.notna()
    d["pc"] = d.offense_personnel.map(pers_class)
    d["is11"] = (d.pc == "11").astype(int)
    d["is12"] = (d.pc == "12").astype(int)
    d["isrb2"] = d.pc.fillna("").str[:1].isin(["2", "3"]).astype(int)
    cov = d.defense_coverage_type.fillna("")
    d["has_cov"] = ((d["pass"] == 1) & (cov != "") & ~cov.isin(["COMBO", "BLOWN"])).astype(int)
    d["two_high"] = (d.has_cov.eq(1) & cov.isin(TWO_HIGH)).astype(int)
    d["one_high"] = (d.has_cov.eq(1) & cov.isin(ONE_HIGH)).astype(int)
    d["man"] = (d.has_cov.eq(1) & d.defense_man_zone_type.eq("MAN_COVERAGE")).astype(int)
    d["has_ftn"] = d.is_motion.notna().astype(int)
    d["motion"] = (d.is_motion == True).astype(int)  # noqa: E712
    d["epa2"] = d.epa.where(d.two_high == 1)
    d["epa1"] = d.epa.where(d.one_high == 1)
    d["epa11_2"] = d.epa.where((d.two_high == 1) & (d.is11 == 1))
    g = d.groupby(["game_id", "season", "week", "posteam"])
    off = g.agg(off_plays=("epa", "size"), off_part=("has_part", "sum"), off_p11=("is11", "sum"), off_p12=("is12", "sum"), off_prb2=("isrb2", "sum"),
                off_ftn=("has_ftn", "sum"), off_motion=("motion", "sum"), off_cov=("has_cov", "sum"), off_vs2=("two_high", "sum"),
                off_vs1=("one_high", "sum"), off_epa=("epa", "sum"), off_succ=("success", "sum"),
                off_epa_vs2=("epa2", "sum"), off_epa_vs1=("epa1", "sum"), off_epa11_vs2=("epa11_2", "sum"),
                off_n11_vs2=("epa11_2", "count")).reset_index().rename(columns={"posteam": "team"})
    dd = d.groupby(["game_id", "defteam"]).agg(def_cov=("has_cov", "sum"), def_two_high=("two_high", "sum"), def_man=("man", "sum"),
                                                def_epa_allowed=("epa", "sum"), def_plays=("epa", "size")).reset_index().rename(columns={"defteam": "team"})
    out = off.merge(dd, on=["game_id", "team"], how="left")
    out = out.sort_values(["season", "week", "game_id", "team"]).reset_index(drop=True)
    safe_out(Path(__file__).parent / "team_game_playlevel.csv").write_text(out.to_csv(index=False))
    cov_rate = out.groupby("season").apply(lambda x: pd.Series({"team_games": len(x), "part_cov": x.off_part.sum() / x.off_plays.sum(),
                                                               "cov_plays": x.off_cov.sum(), "ftn_cov": x.off_ftn.sum() / x.off_plays.sum()}))
    print(cov_rate.round(3).to_string())


if __name__ == "__main__":
    main()
