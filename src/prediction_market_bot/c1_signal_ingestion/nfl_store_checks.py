"""Row-count, null, key and cross-source checks for the NFL event store (W73.2).

Every threshold below was set from a measurement of the built store (see DATA_LAYER.md), not guessed, and every
exception carries the reason. The checks are fail-closed: any violation exits non-zero, which stops the
``nfl_event_store`` workflow before the manifest is committed.

Per file:  rows > 0 (documented exceptions only) · key columns present · key nulls <= ceiling ·
           duplicate keys <= ceiling · ``season`` column agrees with the file's season.
Per source: completed seasons clear a minimum row count (a truncated download would not).
Cross-source: play-level sources are subsets of pbp; pbp games all exist in the schedule.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nfl_event_store import (
    DEFAULT_ROOT, SOURCES, current_season, latest_snapshot, seasons_for)

# (source, season) pairs where the published file is legitimately empty / near-empty.
EXPECTED_EMPTY = {("snaps", 2012): "nflverse publishes a 0-row 2012 snap_counts file"}

# Max fraction of rows with a null in any key column (default 0). Reasons are measurements of the real files.
KEY_NULL_CEILING = {
    "rosters": (0.001, "a few weekly-roster rows carry no gsis_id (0.07% max measured)"),
    "depth_charts": (0.05, "2025+ depth-chart rows for unsigned/practice-squad players have no gsis_id (3.9% max measured)"),
}

# Max fraction of rows that duplicate an earlier row on the key (default 0).
DUP_CEILING = {
    "injuries": (0.0005, "two duplicated injury lines in 2024"),
    "rosters": (0.07, "weekly rosters list a player twice in one week (5.9% max measured, 2002-2015)"),
    "depth_charts": (0.05, "2001-2024 weekly depth charts repeat a player in a slot (4.5% max measured)"),
}

# Minimum rows for a completed season, per source (about 60-90% of the smallest measured season).
MIN_ROWS = {
    "pbp": 40_000,            # smallest completed season measured 44,969 (2001)
    "participation": 40_000,  # 45,184-50,714 measured
    "ftn": 38_000,            # 41,643 in 2022
    "snaps": 20_000,
    "injuries": 3_000,
    "depth_charts": 20_000,
    "rosters": 10_000,
    "pfr_pass": 500,
    "pfr_rush": 1_000,
    "pfr_rec": 1_500,
    "pfr_def": 3_000,
}

# Minimum share of the child source's game ids / play ids found in the parent (pbp / schedules).
COVERAGE_FLOOR = {
    ("participation", "pbp", "play"): 0.97,
    ("ftn", "pbp", "play"): 0.97,
    ("pbp", "schedules", "game"): 1.0,
}


@dataclass
class Report:
    rows: list = field(default_factory=list)       # one dict per file
    coverage: list = field(default_factory=list)   # one dict per cross-source check
    failures: list = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.failures.append(msg)


def _file_for(root: Path, name: str, season: Optional[int]) -> Optional[Path]:
    if season is None:
        return latest_snapshot(root, name)
    p = root / "raw" / name / f"{name}_{season}.parquet"
    return p if p.exists() else None


def check_frame(name: str, season: Optional[int], df: pd.DataFrame, completed: bool, rep: Report) -> dict:
    """Checks for one source-season frame; appends failures to ``rep`` and returns its summary row."""
    src = SOURCES[name]
    tag = f"{name} {season}"
    n = len(df)
    missing = [k for k in src.key if k not in df.columns]
    nulls = {k: int(df[k].isna().sum()) for k in src.key if k in df.columns}
    null_rows = int(df[[k for k in src.key if k in df.columns]].isna().any(axis=1).sum()) if n else 0
    dup = int(df.duplicated([k for k in src.key if k in df.columns]).sum()) if n and not missing else 0
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


def run_checks(root: Path = DEFAULT_ROOT, current: Optional[int] = None) -> Report:
    root = Path(root)
    current = current or current_season()
    rep = Report()
    for name, src in SOURCES.items():
        targets = seasons_for(src, current) if src.per_season else [None]
        for season in targets:
            p = _file_for(root, name, season)
            if p is None:
                # The in-progress season may be unpublished before kickoff; anything else is a hole.
                if season != current:
                    rep.fail(f"{name} {season}: file missing from store")
                continue
            completed = season is not None and season < current
            rep.rows.append(check_frame(name, season, pd.read_parquet(p), completed, rep))

    # cross-source coverage, per season
    pbp_seasons = seasons_for(SOURCES["pbp"], current)
    sched_p = latest_snapshot(root, "schedules")
    if sched_p is not None:
        sched_ids = set(pd.read_parquet(sched_p, columns=["game_id"])["game_id"])
        for s in pbp_seasons:
            p = _file_for(root, "pbp", s)
            if p is None:
                continue
            games = set(pd.read_parquet(p, columns=["game_id"])["game_id"].dropna())
            share = len(games & sched_ids) / len(games) if games else 0.0
            rep.coverage.append({"child": "pbp", "parent": "schedules", "season": s, "level": "game",
                                 "share": share, "n": len(games)})
            if share < COVERAGE_FLOOR[("pbp", "schedules", "game")]:
                rep.fail(f"pbp {s}: only {share:.2%} of games are in the schedule")
    for child in ("participation", "ftn"):
        for s in seasons_for(SOURCES[child], current):
            cp, pp = _file_for(root, child, s), _file_for(root, "pbp", s)
            if cp is None or pp is None:
                continue
            c = pd.read_parquet(cp, columns=["game_id", "play_id"]).dropna()
            pb = pd.read_parquet(pp, columns=["game_id", "play_id"]).dropna()
            have = set(zip(pb["game_id"], pb["play_id"].astype(int)))
            hit = sum((g, int(p_)) in have for g, p_ in zip(c["game_id"], c["play_id"]))
            share = hit / len(c) if len(c) else 0.0
            rep.coverage.append({"child": child, "parent": "pbp", "season": s, "level": "play",
                                 "share": share, "n": len(c)})
            if share < COVERAGE_FLOOR[(child, "pbp", "play")]:
                rep.fail(f"{child} {s}: only {share:.2%} of plays are in pbp")
    return rep


def format_report(rep: Report) -> str:
    out = ["source,season,rows,key_null_rows,dup_keys"]
    out += [f"{r['source']},{r['season']},{r['rows']},{r['key_null_rows']},{r['dup_keys']}" for r in rep.rows]
    out += ["", "child,parent,season,level,share,n"]
    out += [f"{c['child']},{c['parent']},{c['season']},{c['level']},{c['share']:.4f},{c['n']}" for c in rep.coverage]
    return "\n".join(out)


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Check the NFL event store (rows, nulls, keys, cross-source).")
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
