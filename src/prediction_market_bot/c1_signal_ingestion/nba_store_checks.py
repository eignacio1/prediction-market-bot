"""Row-count, null, key and cross-source checks for the NBA event store (W78.4).

Every threshold was set from a measurement of the built store (DATA_LAYER.md), not guessed, and every exception
carries its reason. Fail-closed: any violation exits non-zero.

Per file:  rows > 0 · key columns present · key nulls <= ceiling · duplicate keys <= ceiling ·
           ``season`` column agrees with the file's season · completed seasons clear a minimum row count.
Cross-source: for games that count (regular season, playoffs, play-in, NBA Cup) pbp / possessions / box scores /
           officials cover the schedule. Preseason and All-Star games are excluded by name: the free box-score and
           officials tables do not carry them (measured 0%), and they get imputed tip bounds in the PIT layer.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nba_event_store import (
    DEFAULT_ROOT, SOURCES, current_season, latest_snapshot, seasons_for)

EXPECTED_EMPTY: dict = {}   # no published NBA file is legitimately empty (measured 2016-2026)

KEY_NULL_CEILING: dict = {}  # measured 0 null key cells in all 123 files; default 0 applies everywhere

DUP_CEILING = {
    "lineups": (0.06, "action_number repeats inside a game (5.1-5.3% measured every season)"),
    "shots": (0.001, "ties on (period, clock, shooter), e.g. tip-ins (0.083% max measured)"),
}

# Minimum rows for a completed season (about 75-85% of the smallest measured season).
MIN_ROWS = {
    "pbp": 450_000,          # 573,047 smallest (2020, shortened season)
    "possessions": 180_000,  # 229,998 smallest
    "lineups": 450_000,      # same row count as pbp
    "shots": 160_000,        # 202,399 smallest
    "team_box": 1_800,       # 2,286 smallest
    "player_box": 22_000,    # 28,707 smallest
    "game_rosters": 4_000,   # 5,465 smallest (2016; thinner before 2018)
    "officials": 2_700,      # 3,429 smallest
    "coaches": 130,          # 169 smallest
    "schedule": 900,         # 1,146 smallest
    "espn_schedule": 900,    # 1,157 smallest
}

COUNTING_TYPES = {"regular-season", "playoffs", "play-in", "nba-cup"}
# (child, "game") -> minimum share of counting schedule games that appear in the child.
COVERAGE_FLOOR = {"pbp": 0.995, "possessions": 0.995, "team_box": 0.995, "officials": 0.99}


@dataclass
class Report:
    rows: list = field(default_factory=list)
    coverage: list = field(default_factory=list)
    failures: list = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.failures.append(msg)


def _file_for(root: Path, name: str, season: Optional[int]) -> Optional[Path]:
    if season is None:
        return latest_snapshot(root, name)
    p = root / "raw" / name / f"{name}_{season}.parquet"
    return p if p.exists() else None


def check_frame(name: str, season: Optional[int], df: pd.DataFrame, completed: bool, rep: Report) -> dict:
    src = SOURCES[name]
    tag = f"{name} {season}"
    n = len(df)
    keys = [k for k in src.key if k in df.columns]
    missing = [k for k in src.key if k not in df.columns]
    nulls = {k: int(df[k].isna().sum()) for k in keys}
    null_rows = int(df[keys].isna().any(axis=1).sum()) if n and keys else 0
    dup = int(df.duplicated(keys).sum()) if n and not missing else 0
    row = {"source": name, "season": season, "rows": n, "key_null_rows": null_rows, "dup_keys": dup}
    if n == 0:
        if (name, season) not in EXPECTED_EMPTY:
            rep.fail(f"{tag}: 0 rows")
        return row
    if missing:
        rep.fail(f"{tag}: key columns missing {missing}")
        return row
    null_cap = KEY_NULL_CEILING.get(name, (0.0, ""))[0]
    if null_rows > null_cap * n:
        rep.fail(f"{tag}: {null_rows} rows with a null key ({null_rows / n:.4%} > {null_cap:.4%}) {nulls}")
    dup_cap = DUP_CEILING.get(name, (0.0, ""))[0]
    if dup > dup_cap * n:
        rep.fail(f"{tag}: {dup} duplicate keys ({dup / n:.4%} > {dup_cap:.4%})")
    if season is not None and "season" in df.columns:
        seasons = set(pd.to_numeric(df["season"], errors="coerce").dropna().astype(int))
        if seasons and seasons != {season}:
            rep.fail(f"{tag}: season column holds {sorted(seasons)}")
    floor = MIN_ROWS.get(name)
    if completed and floor and n < floor:
        rep.fail(f"{tag}: {n} rows < minimum {floor} for a completed season")
    return row


def coverage_check(child: str, season: int, games: set, child_games: set, rep: Report) -> None:
    share = len(games & child_games) / len(games) if games else 0.0
    rep.coverage.append({"child": child, "season": season, "share": share, "n": len(games)})
    if share < COVERAGE_FLOOR[child]:
        rep.fail(f"{child} {season}: only {share:.2%} of counting schedule games present (< {COVERAGE_FLOOR[child]:.1%})")


def run_checks(root: Path = DEFAULT_ROOT, current: Optional[int] = None) -> Report:
    root = Path(root)
    current = current or current_season()
    rep = Report()
    for name, src in SOURCES.items():
        targets = seasons_for(src, current) if src.per_season else [None]
        for season in targets:
            p = _file_for(root, name, season)
            if p is None:
                if season != current:
                    rep.fail(f"{name} {season}: file missing from store")
                continue
            completed = season is not None and season < current
            rep.rows.append(check_frame(name, season, pd.read_parquet(p), completed, rep))
    for s in seasons_for(SOURCES["schedule"], current):
        sp = _file_for(root, "schedule", s)
        if sp is None:
            continue
        sch = pd.read_parquet(sp, columns=["game_id", "season_type"])
        games = set(sch.loc[sch["season_type"].isin(COUNTING_TYPES), "game_id"].astype(str))
        for child in COVERAGE_FLOOR:
            cp = _file_for(root, child, s)
            if cp is None:
                continue
            coverage_check(child, s, games, set(pd.read_parquet(cp, columns=["game_id"])["game_id"].astype(str)), rep)
    return rep


def format_report(rep: Report) -> str:
    out = ["source,season,rows,key_null_rows,dup_keys"]
    out += [f"{r['source']},{r['season']},{r['rows']},{r['key_null_rows']},{r['dup_keys']}" for r in rep.rows]
    out += ["", "child,season,share,n_games"]
    out += [f"{c['child']},{c['season']},{c['share']:.4f},{c['n']}" for c in rep.coverage]
    return "\n".join(out)


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Check the NBA event store (rows, nulls, keys, cross-source).")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--report", action="store_true", help="print the per-file table")
    args = ap.parse_args(argv)
    rep = run_checks(args.root)
    if args.report:
        print(format_report(rep))
    print(f"files checked={len(rep.rows)} coverage checks={len(rep.coverage)} failures={len(rep.failures)}")
    for f in rep.failures:
        print("FAIL:", f, file=sys.stderr)
    return 1 if rep.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
