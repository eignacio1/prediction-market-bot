"""Coverage, key and cross-source checks for the NHL event store (W83.3).

Fail-closed: any violation makes ``main`` exit non-zero. Thresholds are set from the measured build
(``02_ARCHITECTURE_DESIGN/NHL_ENGINE/DATA_LAYER.md``), and every exception carries its reason.

Per season (``check_season``):
  coverage   every finished counting game in the schedule has play-by-play, box score and shifts
  keys       no duplicate (game_id, event_id) events, no duplicate shifts, no null game_id
  reconcile  play-by-play goals (shootout excluded, +1 for the shootout winner) equal the box-score final score;
             play-by-play shots-on-goal + goals equal the box-score team shots on goal
  detail     share of shot events carrying x/y, shot type and shooter id: *reported*, not failed, because the NHL
             feed is thinner in earlier seasons (the table records what each season has)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nhl_event_store import (DEFAULT_MANIFEST, DEFAULT_ROOT, FINAL_STATES,
                                                                       TABLES, utc_stamp)

COVERAGE_FLOOR = {"has_pbp": 0.999, "has_box": 0.999, "has_shifts": 0.995}
GOAL_RECONCILE_FLOOR = 0.995
SOG_RECONCILE_FLOOR = 0.98
SHOT_TYPES = ("shot-on-goal", "missed-shot", "blocked-shot", "goal")


@dataclass
class Report:
    seasons: dict = field(default_factory=dict)
    failures: list = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.failures.append(msg)


def reconcile(recon: pd.DataFrame, games: pd.DataFrame) -> dict:
    """Share of games whose pbp goals / shots match the schedule's final score and the box-score shots on goal."""
    r = recon.merge(games[["game_id", "home_score", "away_score", "last_period_type"]], on="game_id", how="left")
    so = r["last_period_type"] == "SO"
    # a shootout is decided 1 goal apart in the final score: credit that goal to the side that won it
    h = r["pbp_goals_home"] + (so & (r["home_score"] > r["away_score"])).astype(int)
    a = r["pbp_goals_away"] + (so & (r["away_score"] > r["home_score"])).astype(int)
    has = r["pbp_goals_home"].notna() & r["home_score"].notna()
    goal_ok = ((h == r["home_score"]) & (a == r["away_score"]))[has]
    out = {"goal_reconcile": float(goal_ok.mean()) if len(goal_ok) else None, "goal_checked": int(has.sum())}
    have_sog = r["pbp_sog_home"].notna() & r["box_home_sog"].notna() if {"pbp_sog_home", "box_home_sog"} <= set(r) else None
    if have_sog is not None and have_sog.any():
        ok = ((r["pbp_sog_home"] == r["box_home_sog"]) & (r["pbp_sog_away"] == r["box_away_sog"]))[have_sog]
        out.update({"sog_reconcile": float(ok.mean()), "sog_checked": int(have_sog.sum())})
    else:
        out.update({"sog_reconcile": None, "sog_checked": 0})
    return out


def detail_shares(events: pd.DataFrame) -> dict:
    shots = events[events["type"].isin(SHOT_TYPES)] if "type" in events else events.iloc[0:0]
    if shots.empty:
        return {"shots": 0}
    return {"shots": int(len(shots)),
            "xy": float(shots["x"].notna().mean()), "shot_type": float(shots["shot_type"].notna().mean()),
            "shooter": float(shots["shooter_id"].notna().mean()),
            "strength_state": float(events["home_skaters"].notna().mean()) if len(events) else 0.0}


def check_season(season: int, games: pd.DataFrame, events: pd.DataFrame, shifts: pd.DataFrame,
                 recon: pd.DataFrame, rep: Report) -> dict:
    fin = games[games["game_state"].isin(FINAL_STATES)]
    info: dict = {"schedule_games": int(len(games)), "finished": int(len(fin)),
                  "events": int(len(events)), "shifts": int(len(shifts))}
    if len(fin) == 0:
        rep.fail(f"{season}: no finished games in schedule")
        return info
    for col, floor in COVERAGE_FLOOR.items():
        share = float(fin[col].mean())
        info[col] = round(share, 5)
        missing = fin.loc[~fin[col], "game_id"].tolist()
        info[col + "_missing"] = missing[:25]
        info[col + "_missing_n"] = len(missing)
        if share < floor:
            rep.fail(f"{season}: {col} coverage {share:.4f} < {floor} (missing {len(missing)}, e.g. {missing[:3]})")
    if len(events):
        dup = int(events.duplicated(["game_id", "event_id"]).sum())
        info["dup_events"] = dup
        if dup:
            rep.fail(f"{season}: {dup} duplicate (game_id, event_id) events")
    if len(shifts):
        dup = int(shifts.duplicated(["game_id", "player_id", "period", "shift_number"]).sum())
        info["dup_shifts"] = dup
        if dup:
            rep.fail(f"{season}: {dup} duplicate shifts")
    if games["game_id"].isna().any():
        rep.fail(f"{season}: null game_id in schedule")
    rc = reconcile(recon, games)
    info.update(rc)
    if rc["goal_reconcile"] is not None and rc["goal_reconcile"] < GOAL_RECONCILE_FLOOR:
        rep.fail(f"{season}: goal reconcile {rc['goal_reconcile']:.4f} < {GOAL_RECONCILE_FLOOR}")
    if rc["sog_reconcile"] is not None and rc["sog_reconcile"] < SOG_RECONCILE_FLOOR:
        rep.fail(f"{season}: shots-on-goal reconcile {rc['sog_reconcile']:.4f} < {SOG_RECONCILE_FLOOR}")
    info["detail"] = detail_shares(events)
    return info


def run(root: Path, seasons: Optional[list] = None) -> Report:
    rep = Report()
    recon_all = pd.DataFrame(json.loads((root / "recon.json").read_text()))
    found = sorted(int(p.stem.split("_")[1]) for p in root.glob("games_*.parquet"))
    for s in seasons or found:
        games = pd.read_parquet(root / f"games_{s}.parquet")
        ev = pd.read_parquet(root / f"events_{s}.parquet") if (root / f"events_{s}.parquet").exists() else pd.DataFrame()
        sh = pd.read_parquet(root / f"shifts_{s}.parquet") if (root / f"shifts_{s}.parquet").exists() else pd.DataFrame()
        rep.seasons[s] = check_season(s, games, ev, sh, recon_all[recon_all["season"] == s], rep)
    return rep


def build_manifest(root: Path, rep: Report) -> dict:
    """Row counts and sha256 per parquet, plus the per-season coverage table: the one committed store artifact."""
    files = {}
    for t in TABLES:
        for p in sorted(root.glob(f"{t}_*.parquet")):
            files[p.name] = {"rows": int(len(pd.read_parquet(p, columns=None))),
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    return {"built_utc": utc_stamp(), "source": "api-web.nhle.com (public, unauthenticated GETs)",
            "contract": "src/prediction_market_bot/c1_signal_ingestion/nhl_point_in_time.py",
            "failures": rep.failures, "seasons": rep.seasons, "files": files}


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--manifest", type=Path, default=None, help=f"write the manifest (default path {DEFAULT_MANIFEST})")
    a = ap.parse_args(argv)
    rep = run(a.root)
    if a.manifest:
        a.manifest.write_text(json.dumps(build_manifest(a.root, rep), indent=1, default=str) + "\n")
    body = json.dumps({"seasons": rep.seasons, "failures": rep.failures}, indent=1, default=str)
    if a.out:
        a.out.write_text(body)
    print(body if not a.out else f"{len(rep.seasons)} seasons, {len(rep.failures)} failures")
    for f in rep.failures:
        print("FAIL", f, file=sys.stderr)
    return 1 if rep.failures else 0


if __name__ == "__main__":
    sys.exit(main())
