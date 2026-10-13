"""W71.3 team-level availability features (EXPLORATORY; no order/registry imports). Reuses the W69.3 point-in-time helpers unchanged."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PM = HERE.parent / "20261012_nba_points_minutes"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(PM))
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location("w69_features", PM / "features.py")
W69 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(W69)

from prediction_market_bot.c1_signal_ingestion import nba_ingest as N  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_player_ingest as P  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_player_features import PlayerFeatureBuilder  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import _dt, et_date, et_midnight_utc  # noqa: E402

EXTRA = ["h_out_min", "a_out_min", "d_out_min", "h_inj_missing", "a_inj_missing"]


def load_all_inj(*dirs: str) -> dict:
    out: dict = {}
    for d in dirs:
        for k, v in W69.load_inj(d).items():
            out.setdefault(k, {}).update(v)
    return out


def team_out_min(fb, inj, game, team, start):
    """(out_min, inj_missing) for one team-game; point-in-time per W69.3 rules."""
    snap = W69.snapshot(inj, start)
    if snap is None:
        return 0.0, 1.0
    cutoff = min(start, et_midnight_utc(et_date(start)))
    tot = 0.0
    for pid, nm in W69._team_candidates(fb, team, cutoff).items():
        st = W69._recent(fb, pid, team, cutoff)
        if st and W69.status_of(snap, nm) in ("Out", "Doubtful"):
            tot += st["min10"]
    return tot, 0.0


def build_extra(raw_games: Path, raw_players: Path, inj_dirs, seasons=(2023, 2024, 2025, 2026)) -> dict:
    """{game_id: {EXTRA...}} for regular-season games in ``seasons`` that have a player store record."""
    games, stores = [], []
    for s in seasons:
        games += list(N.load_season(s, raw_games)["games"].values())
        stores.append(P.load_players(s, raw_players))
    fb = PlayerFeatureBuilder(games, stores)
    gmap = {g["game_id"]: g for g in games}
    inj = load_all_inj(*inj_dirs)
    out = {}
    for store in stores:
        for gid, rec in store["games"].items():
            g = gmap.get(gid)
            if g is None or g["season_type"] != 2:
                continue
            start = _dt(rec["start_time_utc"])
            h, hm = team_out_min(fb, inj, g, g["home"], start)
            a, am = team_out_min(fb, inj, g, g["away"], start)
            out[gid] = {"h_out_min": h, "a_out_min": a, "d_out_min": h - a, "h_inj_missing": hm, "a_inj_missing": am}
    return out
