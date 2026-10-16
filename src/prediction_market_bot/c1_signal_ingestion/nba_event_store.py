"""NBA event store: one reproducible build of the free sportsdataverse NBA sources (W78.4, ADR-0073 stage 1).

Sources (all free, public ``sportsdataverse/sportsdataverse-data`` GitHub releases, no login): play-by-play,
possessions, on-court lineups per event, shot locations, team and player box scores, game rosters, officials,
coaches, the nba_stats schedule/results table, the ESPN schedule (carries the tip-off instant) and the ESPN
injury snapshot. stats.nba.com itself is unreachable from here and is never scraped around.

Every stored row carries ``_as_of`` (UTC time the file was retrieved), ``_source`` and the canonical key
columns, so a point-in-time query (``nba_point_in_time``) never has to guess what was known when.

Season label = the calendar year the season ENDS (2026 = 2025-26). Coverage starts at 2016 (2015-16).

Layout (git-ignored; ``*.parquet`` is already ignored repo-wide, and the root is listed explicitly too)::

    exp_output/NBA_EVENTS/raw/<source>/<source>_<season>.parquet     # per-season sources
    exp_output/NBA_EVENTS/raw/injuries/injuries_<as_of>.parquet      # rolling snapshot, one per build

The committed artefact is the manifest (row counts, sha256 of the downloaded bytes, source Last-Modified and
ETag, key null counts), ``02_ARCHITECTURE_DESIGN/NBA_ENGINE/event_store_manifest.json``.

Nothing here touches an order, a position, a stake or a ledger row. Demo/paper/shadow research data only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nfl_event_store import (  # generic, sport-free helpers
    NotPublished, file_stamp, http_get, sha256_bytes, sha256_file, utc_stamp)

RELEASE_BASE = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download"
DEFAULT_ROOT = Path("exp_output/NBA_EVENTS")
DEFAULT_MANIFEST = Path("02_ARCHITECTURE_DESIGN/NBA_ENGINE/event_store_manifest.json")
FIRST_SEASON = 2016   # 2015-16: earliest season whose play-by-play carries the on-court lineup + possession tables
NBA_STATS_LAST = 2026  # nba_stats files end at the last completed season; 2027 is ESPN-schedule-only until tip-off


def current_season(today: Optional[dt.date] = None) -> int:
    """NBA season in progress or just finished, by ending year: the label turns over in October."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    return today.year + 1 if today.month >= 10 else today.year


@dataclass(frozen=True)
class Source:
    """One sportsdataverse file family.

    ``kind`` is how the point-in-time contract treats the rows (see ``nba_point_in_time``):
    ``post_game`` (only games that finished before the query game), ``schedule`` (pre-game context whitelist),
    ``season_static`` (season-level table, not point-in-time safe: refused by ``view``), ``snapshot`` (own
    as-of date; refused for any game before it).
    """

    name: str
    tag: str
    filename: str                      # may contain {season}
    kind: str
    first_season: Optional[int]        # None for single-file sources
    last_season: Optional[int] = None  # None = through the current season
    game_col: Optional[str] = None     # source column holding the game id
    key: tuple = ()                    # canonical key columns that must be non-null and unique
    note: str = ""

    @property
    def per_season(self) -> bool:
        return self.first_season is not None


SOURCES: dict[str, Source] = {s.name: s for s in [
    Source("pbp", "nba_stats_pbp", "nba_play_by_play_{season}.parquet", "post_game", FIRST_SEASON, NBA_STATS_LAST,
           game_col="game_id", key=("game_id", "order_index"),
           note="action_number is not unique within a game; order_index is"),
    Source("possessions", "nba_stats_possessions", "nba_possessions_{season}.parquet", "post_game", FIRST_SEASON,
           NBA_STATS_LAST, game_col="game_id", key=("game_id", "start_order_index")),
    Source("lineups", "nba_stats_game_lineups", "nba_lineups_{season}.parquet", "post_game", FIRST_SEASON,
           NBA_STATS_LAST, game_col="game_id", key=("game_id", "action_number"),
           note="on-court five per event; action_number repeats inside a game (measured), so it is a join key, not unique"),
    Source("shots", "nba_stats_shots", "shots_{season}.parquet", "post_game", FIRST_SEASON, NBA_STATS_LAST,
           game_col="game_id", key=("game_id", "period", "clock", "person_id"),
           note="no clean event key in the file; ties on (period, clock, shooter) are legitimate (tip-ins)"),
    Source("team_box", "nba_stats_team_boxscores", "team_boxscores_{season}.parquet", "post_game", FIRST_SEASON,
           NBA_STATS_LAST, game_col="game_id", key=("game_id", "team_id")),
    Source("player_box", "nba_stats_player_boxscores", "player_boxscores_{season}.parquet", "post_game", FIRST_SEASON,
           NBA_STATS_LAST, game_col="game_id", key=("game_id", "person_id")),
    Source("game_rosters", "nba_stats_game_rosters", "game_rosters_{season}.parquet", "post_game", FIRST_SEASON,
           NBA_STATS_LAST, game_col="game_id", key=("game_id", "player_id"),
           note="who was on the game-day roster; published with the result, so treated as post-game"),
    Source("officials", "nba_stats_officials", "officials_{season}.parquet", "post_game", FIRST_SEASON, NBA_STATS_LAST,
           game_col="game_id", key=("game_id", "official_id"),
           note="crew assignment time is not published; NBA posts crews ~9am game day, but the file is post-game so it is excluded until a timestamp exists (GAP)"),
    Source("coaches", "nba_stats_coaches", "coaches_{season}.parquet", "season_static", FIRST_SEASON, NBA_STATS_LAST,
           key=("season", "team_id", "coach_id"),
           note="end-of-season staff table with no dates: not point-in-time safe (GAP)"),
    Source("schedule", "nba_stats_schedules", "nba_schedule_{season}.parquet", "schedule", FIRST_SEASON, NBA_STATS_LAST,
           game_col="game_id", key=("game_id",),
           note="results table: date + teams are pre-game facts, scores are not; no tip time (see espn_schedule)"),
    Source("espn_schedule", "espn_nba_schedules", "nba_schedule_{season}.parquet", "schedule", FIRST_SEASON, None,
           game_col="id", key=("id",),
           note="carries the tip-off instant (UTC); the only 2026-27 schedule source. status/score columns are post-game"),
    Source("injuries", "espn_nba_injuries", "injuries_2027.parquet", "snapshot", None, None,
           key=("injury_id", "as_of_date"),
           note="daily injury-list snapshots, one row per listed player per as_of_date, only from 2026-09-08 on; "
                "there is NO free injury history before that (GAP, GG-register)"),
]}


def canonicalise(df: pd.DataFrame, src: Source, season: Optional[int], as_of: str) -> pd.DataFrame:
    """Add canonical key columns and provenance; never drop or rewrite an original column."""
    out = df.copy()
    if src.game_col and "game_id" not in out.columns:
        out["game_id"] = out[src.game_col]
    if src.name != "espn_schedule" and "game_id" in out.columns:
        out["game_id"] = out["game_id"].astype(str)
    elif src.name == "espn_schedule":
        out["game_id"] = out["id"].astype(str)
    if season is not None and "season" not in out.columns:
        out["season"] = season
    out["_source"] = src.name
    out["_as_of"] = as_of
    return out


def seasons_for(src: Source, current: int) -> list[int]:
    if not src.per_season:
        return []
    last = src.last_season if src.last_season is not None else current
    return list(range(src.first_season, last + 1))


def source_url(src: Source, season: Optional[int]) -> str:
    return f"{RELEASE_BASE}/{src.tag}/{src.filename.format(season=season)}"


def store_path(root: Path, src: Source, season: Optional[int], as_of: str) -> Path:
    d = root / "raw" / src.name
    if src.per_season:
        return d / f"{src.name}_{season}.parquet"
    return d / f"{src.name}_{file_stamp(as_of)}.parquet"


def latest_snapshot(root: Path, name: str) -> Optional[Path]:
    snaps = sorted((root / "raw" / name).glob(f"{name}_*.parquet"))
    return snaps[-1] if snaps else None


def build_one(src: Source, season: Optional[int], root: Path, as_of: str,
              fetch: Callable[[str], tuple[bytes, dict]] = http_get) -> dict:
    """Download one file, canonicalise, write parquet, return its manifest entry."""
    url = source_url(src, season)
    try:
        raw, headers = fetch(url)
    except NotPublished:
        return {"source": src.name, "season": season, "url": url, "status": "not_published"}
    df = pd.read_parquet(io.BytesIO(raw))
    out = canonicalise(df, src, season, as_of)
    path = store_path(root, src, season, as_of)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, index=False)
    return {
        "source": src.name, "season": season, "url": url, "status": "ok",
        "rows": int(len(out)), "columns": int(df.shape[1]),
        "source_sha256": sha256_bytes(raw), "source_bytes": len(raw),
        "source_last_modified": headers.get("last-modified"), "source_etag": headers.get("etag"),
        "key_nulls": {k: int(out[k].isna().sum()) for k in src.key if k in out.columns},
        "key_missing_cols": [k for k in src.key if k not in out.columns],
        "as_of": as_of, "store_file": str(path.relative_to(root)),
    }


def build(root: Path = DEFAULT_ROOT, manifest_path: Path = DEFAULT_MANIFEST, only: Optional[list] = None,
          min_season: Optional[int] = None, current: Optional[int] = None,
          fetch: Callable[[str], tuple[bytes, dict]] = http_get, now: Optional[dt.datetime] = None) -> dict:
    """Full rebuild of every selected source/season; the manifest is rewritten from the result.

    A completed season inside a source's declared range that is not published is a failure (the store would have
    a silent hole). The in-progress season may be absent; above ``last_season`` is skipped by construction.
    """
    current = current or current_season()
    as_of = utc_stamp(now)
    entries: list[dict] = []
    failures: list[str] = []
    for name, src in SOURCES.items():
        if only and name not in only:
            continue
        targets = seasons_for(src, current) if src.per_season else [None]
        for season in targets:
            if min_season and season is not None and season < min_season:
                continue
            entry = build_one(src, season, root, as_of, fetch)
            entries.append(entry)
            if entry["status"] != "ok" and season != current:
                failures.append(f"{name} {season}: {entry['status']} ({entry['url']})")
            print(f"{name:14s} {season!s:>5s} {entry['status']:14s} rows={entry.get('rows', '-')}", flush=True)
    manifest = {
        "build_as_of": as_of, "current_season": current,
        "builder": "prediction_market_bot.c1_signal_ingestion.nba_event_store",
        "python": sys.version.split()[0], "pandas": pd.__version__,
        "sources": {n: {"tag": s.tag, "kind": s.kind, "first_season": s.first_season, "last_season": s.last_season,
                        "key": list(s.key), "note": s.note} for n, s in SOURCES.items()},
        "files": entries, "failures": failures,
    }
    if not only and not min_season:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Build the NBA event store from free sportsdataverse releases.")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--only", nargs="*", help="source names (default: all)")
    ap.add_argument("--min-season", type=int, help="partial build for testing; manifest is NOT written")
    args = ap.parse_args(argv)
    m = build(args.root, args.manifest, args.only, args.min_season)
    if m["failures"]:
        print("FAILURES:\n  " + "\n  ".join(m["failures"]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
