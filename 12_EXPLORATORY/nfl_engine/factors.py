"""EXPLORATORY -- reusable NFL factor builder (W75.2, ADR-0075 s1).

One builder, any factor class: event store + as_of -> per-(unit, cell) values, point-in-time, with volume and
success, empirical-Bayes shrunk, opponent-adjusted. A factor class is a `FactorSpec`; the first (F5/F6: coverage
shell x offensive personnel x motion) is `COVERAGE_X_PERSONNEL`. The next class (e.g. pressure vs protection)
is a new FactorSpec over the same play table -- no new builder.

Point-in-time: a play is usable at `as_of` iff its game's kickoff + 4h <= as_of (the `post_game` rule of
nfl_point_in_time). Nothing here reads a row dated after as_of.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")
POST_GAME_LAG = timedelta(hours=4)
RAW = "exp_output/NFL_EVENTS/raw/"


def personnel_group(s) -> str | None:
    """'1 C, 2 G, ... 1 RB, 1 TE, 3 WR' -> '11' (RB,TE digits); 'other' for >=7 OL oddities handled by caller."""
    if not isinstance(s, str):
        return None
    rb = re.search(r"(\d) RB", s)
    te = re.search(r"(\d) TE", s)
    code = f"{int(rb.group(1)) if rb else 0}{int(te.group(1)) if te else 0}"
    return code if code in ("11", "12", "21", "22", "10", "13", "01", "20", "00") else "other"


def kickoff_utc(gameday: str, gametime: str | None) -> pd.Timestamp:
    h, m = (gametime or "13:00").split(":")[:2]
    y, mo, d = map(int, gameday.split("-"))
    return pd.Timestamp(datetime(y, mo, d, int(h), int(m), tzinfo=ET).astimezone(timezone.utc))


def build_play_table(root: str | Path, seasons: list[int]) -> pd.DataFrame:
    """Offensive scrimmage plays with coverage (participation), motion (FTN) and outcomes (pbp). Raw store only."""
    root = Path(root)
    sched = pd.read_parquet(next((root / RAW / "schedules").glob("*.parquet")))
    sched = sched[sched.game_type.isin(["REG", "WC", "DIV", "CON", "SB"])]
    ko = {r.game_id: kickoff_utc(r.gameday, r.gametime) for r in sched.itertuples()}
    out = []
    for s in seasons:
        b = pd.read_parquet(root / RAW / f"pbp/pbp_{s}.parquet",
                            columns=["game_id", "play_id", "season", "week", "posteam", "defteam", "play_type", "epa", "success", "season_type"])
        b = b[b.play_type.isin(["pass", "run"]) & b.epa.notna() & b.posteam.notna()]
        pp = root / RAW / f"participation/participation_{s}.parquet"
        if pp.exists():
            p = pd.read_parquet(pp, columns=["game_id", "play_id", "offense_personnel", "defense_coverage_type", "defense_man_zone_type"])
            b = b.merge(p, on=["game_id", "play_id"], how="left")
        else:
            for c in ("offense_personnel", "defense_coverage_type", "defense_man_zone_type"):
                b[c] = None
        fp = root / RAW / f"ftn/ftn_{s}.parquet"
        if fp.exists():
            f = pd.read_parquet(fp, columns=["game_id", "play_id", "is_motion"]).drop_duplicates(["game_id", "play_id"])
            b = b.merge(f, on=["game_id", "play_id"], how="left")
        else:
            b["is_motion"] = np.nan
        out.append(b)
    d = pd.concat(out, ignore_index=True)
    d["kickoff"] = d.game_id.map(ko)
    d = d[d.kickoff.notna()].copy()
    d["pers"] = d.offense_personnel.map(personnel_group)
    d["shell"] = d.defense_coverage_type
    d["manzone"] = d.defense_man_zone_type.replace({"": None})
    d["motion"] = d.is_motion.map({True: "M", False: "S", 1.0: "M", 0.0: "S"})
    d["epa"] = d.epa.astype(float)
    d["success"] = d.success.astype(float)
    d["off"], d["dfn"] = d.posteam, d.defteam
    d["game_idx"] = d.groupby("season").game_id.transform(lambda x: pd.factorize(x)[0])
    return d


@dataclass(frozen=True)
class FactorSpec:
    name: str
    cell: tuple[str, ...]          # columns defining the cell (e.g. shell, pers, motion)
    unit_side: str = "dfn"         # which team the value is attributed to: "dfn" (defense's rate) or "off"
    require: tuple[str, ...] = ()  # columns that must be non-null for a play to count
    min_season: int = 2018


COVERAGE_X_PERSONNEL = FactorSpec("F5F6_coverage_x_personnel_x_motion", ("shell", "pers", "motion"),
                                  require=("shell", "pers"), min_season=2018)
COVERAGE_X_PERSONNEL_NOMOTION = FactorSpec("F5F6_coverage_x_personnel", ("shell", "pers"),
                                           require=("shell", "pers"), min_season=2018)


def pit(plays: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    return plays[plays.kickoff + POST_GAME_LAG <= as_of]


def eb_k(df: pd.DataFrame, by: str, val: str = "epa") -> float:
    """Method-of-moments shrinkage strength k = sigma2_within / tau2_between (in plays), floor 20."""
    g = df.groupby(by)[val].agg(["mean", "count", "var"]).dropna()
    g = g[g["count"] >= 5]
    if len(g) < 5:
        return 150.0
    s2 = float((g["var"] * (g["count"] - 1)).sum() / (g["count"] - 1).sum())
    tau2 = max(float(g["mean"].var() - (s2 / g["count"]).mean()), 1e-6)
    return float(min(max(s2 / tau2, 20.0), 5000.0))


def baselines(P: pd.DataFrame) -> tuple[pd.Series, pd.Series, float]:
    """Opponent baselines at as_of: each offense's overall EPA/play (shrunk) -- the adjustment for 'who they faced'."""
    lg = float(P.epa.mean())
    k = eb_k(P, "off")
    g = P.groupby("off").epa.agg(["sum", "count"])
    off = (g["sum"] + k * lg) / (g["count"] + k)
    k2 = eb_k(P, "dfn")
    g2 = P.groupby("dfn").epa.agg(["sum", "count"])
    dfn = (g2["sum"] + k2 * lg) / (g2["count"] + k2)
    return off - lg, dfn - lg, lg


def factor_values(plays: pd.DataFrame, as_of: pd.Timestamp, spec: FactorSpec, *, prior_seasons_only: int | None = None,
                  k_cell: float | None = None) -> pd.DataFrame:
    """Per (unit, cell): n, share-of-unit-snaps, raw EPA/play, success, opponent-adjusted EPA, shrunk EPA, shrunk share.

    unit_side 'dfn': what the defense *does* (share) and what happens *against* it in that cell (EPA allowed).
    Opponent adjustment: play EPA minus the facing offense's (or defense's, for unit_side 'off') PIT baseline.
    Shrinkage: cell EPA toward the league cell mean (EB, method of moments), cell share toward league cell share.
    """
    P = pit(plays, as_of)
    if prior_seasons_only is not None:
        P = P[P.season <= prior_seasons_only]
    P = P[P.season >= spec.min_season]
    off_b, dfn_b, lg = baselines(P)
    unit, other = (spec.unit_side, "off" if spec.unit_side == "dfn" else "dfn")
    ob = off_b if spec.unit_side == "dfn" else dfn_b
    P = P.assign(adj=P.epa - P[other].map(ob).fillna(0.0))
    for c in spec.require:
        P = P[P[c].notna()]
    cells = list(spec.cell)
    P = P.dropna(subset=cells)
    g = P.groupby([unit] + cells).agg(n=("epa", "size"), epa=("epa", "mean"), succ=("success", "mean"), adj=("adj", "mean"))
    tot = P.groupby(unit).size().rename("unit_n")
    g = g.join(tot, on=unit)
    g["share"] = g.n / g.unit_n
    league = P.groupby(cells).agg(l_epa=("adj", "mean"), l_n=("adj", "size"))
    league["l_share"] = league.l_n / league.l_n.sum()
    g = g.join(league, on=cells)
    k = k_cell if k_cell is not None else eb_k(P.assign(cellkey=["|".join(t) for t in P[cells].astype(str).itertuples(index=False)]).assign(
        u=lambda x: x[unit] + "|" + x.cellkey), "u", "adj")
    g["epa_shrunk"] = (g.n * g.adj + k * g.l_epa) / (g.n + k)
    ks = 100.0
    g["share_shrunk"] = (g.n + ks * g.l_share) / (g.unit_n + ks)
    g.attrs["k_cell"] = k
    g.attrs["n_plays"] = int(len(P))
    return g.reset_index()
