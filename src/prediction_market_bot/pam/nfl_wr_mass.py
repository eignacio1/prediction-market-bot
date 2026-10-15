"""NFL WR mass-tier classifier (W75.1 Part B). Rule-based, point-in-time per season, free data only.

Inputs: nflverse pbp + participation (route on targeted plays) + rosters (position, ids). A classification built
from season S data takes effect 1 March of S+1 and is superseded by the S+1 record, so no engine can read a label
that used data from its own or a later season. Thresholds are fixed a priori (not fitted) and listed in
``qualitative_data/pam/nfl/taxonomy.json``.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import ArchetypeWeight, Basis, Classifier, Modifier, PamRecord

REPO = Path(__file__).resolve().parents[3]
RAW = REPO / "exp_output" / "NFL_EVENTS" / "raw"
VERSION = "nfl_wr_mass_v1"
MIN_TARGETS = 50
PRUNE = 0.20
DEEP_ROUTES = {"GO", "POST", "CORNER", "WHEEL"}
SHORT_ROUTES = {"SCREEN", "SWING", "QUICK OUT", "SLANT", "HITCH/CURL"}


def _clip(x):
    return float(np.clip(x, 0.0, 1.0))


def load_targets(season: int, raw: Path = RAW) -> pd.DataFrame:
    p = pd.read_parquet(raw / "pbp" / f"pbp_{season}.parquet")
    p = p[(p.season_type == "REG") & (p.pass_attempt == 1) & p.receiver_player_id.notna() & p.air_yards.notna()].copy()
    pt = pd.read_parquet(raw / "participation" / f"participation_{season}.parquet")[["nflverse_game_id", "play_id", "route"]]
    pt = pt.rename(columns={"nflverse_game_id": "game_id"})
    pt["route"] = pt["route"].replace("", np.nan)
    return p.merge(pt, on=["game_id", "play_id"], how="left")


def wr_ids(season: int, raw: Path = RAW) -> pd.DataFrame:
    r = pd.read_parquet(raw / "rosters" / f"rosters_{season}.parquet")
    r = r[r.position == "WR"].drop_duplicates("gsis_id")[["gsis_id", "pfr_id", "full_name"]]
    return r.dropna(subset=["gsis_id"])


def features(t: pd.DataFrame, ids: pd.DataFrame, min_targets: int = MIN_TARGETS) -> pd.DataFrame:
    team_tgt = t.groupby("posteam").size().rename("team_tgt")
    g = t[t.receiver_player_id.isin(ids.gsis_id)].groupby("receiver_player_id")
    f = pd.DataFrame({
        "targets": g.size(), "adot": g.air_yards.mean(),
        "deep_rate": g.air_yards.apply(lambda s: (s >= 20).mean()),
        "short_rate": g.air_yards.apply(lambda s: (s <= 3).mean()),
        "team": g.posteam.agg(lambda s: s.mode().iat[0]),
        "name": g.receiver_player_name.agg(lambda s: s.mode().iat[0]),
    })
    rec = t[t.complete_pass == 1].groupby("receiver_player_id").yards_after_catch.mean()
    f["yac_per_rec"] = rec.reindex(f.index)
    rt = t.dropna(subset=["route"]).groupby("receiver_player_id").route
    f["route_n"] = rt.size().reindex(f.index).fillna(0)
    f["route_deep"] = (rt.apply(lambda s: s.isin(DEEP_ROUTES).mean())).reindex(f.index)
    f["tgt_share"] = f.targets / f.team.map(team_tgt)
    f = f[f.targets >= min_targets].dropna(subset=["yac_per_rec"])
    return f.join(ids.set_index("gsis_id")[["pfr_id"]])


def scores(r: pd.Series) -> dict[str, float]:
    rd = r.route_deep if r.route_n >= 20 and not np.isnan(r.route_deep) else None
    vert_parts = [_clip((r.adot - 9) / 6), _clip((r.deep_rate - 0.10) / 0.20)] + ([_clip((rd - 0.20) / 0.25)] if rd is not None else [])
    return {
        "WR-VERT": float(np.mean(vert_parts)),
        "WR-YAC": float(np.mean([_clip((r.yac_per_rec - 3.5) / 3), _clip((r.short_rate - 0.25) / 0.30)])),
        "WR-VOL": _clip((r.tgt_share - 0.14) / 0.12),
        "WR-MID": _clip(1 - abs(r.adot - 10) / 5),
    }


def weights(sc: dict[str, float]) -> dict[str, float]:
    tot = sum(sc.values())
    if tot <= 0:
        return {"WR-MID": 1.0}
    w = {k: v / tot for k, v in sc.items()}
    w = {k: v for k, v in w.items() if v >= PRUNE} or {max(w, key=w.get): 1.0}
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


def classify(f: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for gid, r in f.iterrows():
        w = weights(scores(r))
        rows.append({"gsis_id": gid, "w": w, "primary": max(w, key=w.get)})
    return pd.DataFrame(rows).set_index("gsis_id")


def to_records(season: int, f: pd.DataFrame, c: pd.DataFrame, labels: dict, recorded_at: _dt.date,
               prior_ids: dict[str, str] | None = None) -> list[PamRecord]:
    eff = _dt.date(season + 1, 3, 1)
    out = []
    for gid, r in f.iterrows():
        w = c.loc[gid, "w"]
        ids = {"gsis_id": gid}
        if isinstance(r.pfr_id, str):
            ids["pfr_id"] = r.pfr_id
        out.append(PamRecord(
            record_id=f"nfl:wr:{season}:{gid}", sport="nfl", player_id=gid,
            archetypes=tuple(ArchetypeWeight(k, v, labels[k]) for k, v in sorted(w.items(), key=lambda kv: -kv[1])),
            tier="mass", classified_by=Classifier("rule", VERSION, "1"), effective_from=eff, recorded_at=recorded_at,
            basis=Basis((str(season),), ("nflverse pbp", "nflverse participation", "nflverse rosters"),
                        f"{int(r.targets)} targets, aDOT {r.adot:.1f}, tgt share {r.tgt_share:.3f}, YAC/rec {r.yac_per_rec:.1f}"),
            confidence=min(1.0, r.targets / 120.0), supersedes=((prior_ids[gid],) if prior_ids and gid in prior_ids else ()),
            snapshot_id=f"nfl_wr_mass_{season}", taxonomy_version=VERSION, id_map=ids, player_name=r["name"],
            backdated=True,
            backdating_rationale=f"Rule applied retrospectively on {recorded_at}; uses only season {season} data, effective {eff} (after season end). No later data used.",
            extra={"features": {k: (None if pd.isna(r[k]) else round(float(r[k]), 4)) for k in
                                ("targets", "adot", "deep_rate", "short_rate", "yac_per_rec", "tgt_share", "route_deep", "route_n")}},
        ))
    return out
