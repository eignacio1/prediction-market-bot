"""NFL event store: one reproducible build of the free nflverse sources (W73.2, ADR-0073 stage 1).

Sources (all free, public nflverse-data GitHub releases, no login): plays, participation, FTN charting,
snap counts, injuries, depth charts, weekly rosters, PFR advanced stats, officials, schedule/games.
Every stored row carries ``_as_of`` (UTC time the file was retrieved), ``_source`` and the canonical key
columns, so a point-in-time query (``nfl_point_in_time``) never has to guess what was known when.

Layout (git-ignored; ``*.parquet`` is already ignored repo-wide, and the root is listed explicitly too)::

    exp_output/NFL_EVENTS/raw/<source>/<source>_<season>.parquet      # per-season sources
    exp_output/NFL_EVENTS/raw/schedules/games_<as_of>.parquet         # rolling file, one snapshot per build
    exp_output/NFL_EVENTS/raw/officials/officials_<as_of>.parquet     # rolling file, one snapshot per build

The committed artefact is the manifest (row counts, sha256 of the downloaded bytes, source Last-Modified
and ETag, null counts of the key columns), ``02_ARCHITECTURE_DESIGN/NFL_ENGINE/event_store_manifest.json``.

Nothing here touches an order, a position, a stake or a ledger row. Demo/paper/shadow research data only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

RELEASE_BASE = "https://github.com/nflverse/nflverse-data/releases/download"
DEFAULT_ROOT = Path("exp_output/NFL_EVENTS")
DEFAULT_MANIFEST = Path("02_ARCHITECTURE_DESIGN/NFL_ENGINE/event_store_manifest.json")
USER_AGENT = "prediction-market-bot/nfl-event-store (research; contact: repo owner)"


def current_season(today: Optional[dt.date] = None) -> int:
    """NFL season in progress or just finished: the season year turns over in March."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    return today.year if today.month >= 3 else today.year - 1


@dataclass(frozen=True)
class Source:
    """One nflverse file family.

    ``kind`` is how the point-in-time contract treats the rows (see ``nfl_point_in_time``):
    ``post_game`` (only games that finished before the query game), ``weekly`` (injury-report style,
    week rule), ``dated`` (own timestamp column), ``schedule`` (pre-game context whitelist).
    ``last_season`` None means "through the current season"; a fixed value means the file family ends
    there (a 404 above it is expected and not an error).
    """

    name: str
    tag: str
    filename: str                      # may contain {season}
    kind: str
    first_season: Optional[int]        # None for single-file sources
    last_season: Optional[int] = None
    game_col: Optional[str] = None     # source column holding the nflverse game id
    play_col: Optional[str] = None     # source column holding the play id (play-level sources)
    key: tuple = ()                    # canonical key columns that must be non-null and unique
    note: str = ""
    required_cols: tuple = field(default_factory=tuple)

    @property
    def per_season(self) -> bool:
        return self.first_season is not None


SOURCES: dict[str, Source] = {s.name: s for s in [
    Source("pbp", "pbp", "play_by_play_{season}.parquet", "post_game", 1999,
           game_col="game_id", play_col="play_id", key=("game_id", "play_id"),
           required_cols=("game_id", "play_id", "epa", "posteam", "defteam", "week", "season")),
    Source("participation", "pbp_participation", "pbp_participation_{season}.parquet", "post_game", 2016,
           game_col="nflverse_game_id", play_col="play_id", key=("game_id", "play_id"),
           note="no 2026 file published yet (GG-730); the in-progress season may be absent, picked up automatically once published"),
    Source("ftn", "ftn_charting", "ftn_charting_{season}.parquet", "post_game", 2022,
           game_col="nflverse_game_id", play_col="nflverse_play_id", key=("game_id", "play_id")),
    Source("snaps", "snap_counts", "snap_counts_{season}.parquet", "post_game", 2012,
           game_col="game_id", key=("game_id", "team", "pfr_player_id")),
    Source("injuries", "injuries", "injuries_{season}.parquet", "weekly", 2009,
           key=("season", "week", "team", "gsis_id"),
           note="no publication timestamp in 2025+ files (GG-732); older files carry date_modified"),
    Source("depth_charts", "depth_charts", "depth_charts_{season}.parquet", "dated", 2001,
           key=("season", "snapshot", "team", "player_id", "depth_slot"),
           note="2001-2024 weekly schema (club_code, week); 2025+ timestamped schema (dt)"),
    Source("rosters", "weekly_rosters", "roster_weekly_{season}.parquet", "weekly", 2002,
           key=("season", "week", "team", "player_id")),
    Source("pfr_pass", "pfr_advstats", "advstats_week_pass_{season}.parquet", "post_game", 2018,
           game_col="game_id", key=("game_id", "team", "pfr_player_id")),
    Source("pfr_rush", "pfr_advstats", "advstats_week_rush_{season}.parquet", "post_game", 2018,
           game_col="game_id", key=("game_id", "team", "pfr_player_id")),
    Source("pfr_rec", "pfr_advstats", "advstats_week_rec_{season}.parquet", "post_game", 2018,
           game_col="game_id", key=("game_id", "team", "pfr_player_id")),
    Source("pfr_def", "pfr_advstats", "advstats_week_def_{season}.parquet", "post_game", 2018,
           game_col="game_id", key=("game_id", "team", "pfr_player_id")),
    Source("officials", "officials", "officials.parquet", "post_game", None, game_col="game_id",
           key=("game_id", "official_id"), note="rolling single file; snapshotted per build"),
    Source("schedules", "schedules", "games.parquet", "schedule", None, game_col="game_id",
           key=("game_id",), note="rolling single file; lines are closing values (GG-733); snapshotted per build"),
]}

# Source column -> canonical column, for sources whose schema varies by era.
_TEAM_COLS = ("team", "club_code", "recent_team")
_PLAYER_COLS = ("gsis_id", "pfr_player_id")


def _first_present(df: pd.DataFrame, names) -> Optional[str]:
    return next((c for c in names if c in df.columns), None)


def canonicalise(df: pd.DataFrame, src: Source, season: Optional[int], as_of: str) -> pd.DataFrame:
    """Add canonical key columns and provenance; never drop or rewrite an original column."""
    out = df.copy()
    if src.game_col and "game_id" not in out.columns:
        out["game_id"] = out[src.game_col]
    if src.play_col and "play_id" not in out.columns:
        out["play_id"] = out[src.play_col]
    if "play_id" in out.columns:
        out["play_id"] = pd.to_numeric(out["play_id"], errors="coerce").astype("Int64")
    if season is not None and "season" not in out.columns:
        out["season"] = season
    if src.name in ("injuries", "depth_charts", "rosters"):
        tc = _first_present(out, _TEAM_COLS)
        if tc and tc != "team":
            out["team"] = out[tc]
        if "player_id" not in out.columns and "gsis_id" in out.columns:
            out["player_id"] = out["gsis_id"]
    if src.name == "depth_charts":
        # old schema: depth_team (1/2/3) x depth_position; new schema: pos_abb x pos_rank/pos_slot
        if "depth_position" in out.columns:
            out["depth_slot"] = out["depth_position"].astype(str) + "#" + out["depth_team"].astype(str)
        elif "pos_abb" in out.columns:
            out["depth_slot"] = out["pos_abb"].astype(str) + "#" + out["pos_slot"].astype(str) + "#" + out["pos_rank"].astype(str)
        if "week" not in out.columns:
            out["week"] = pd.NA  # 2025+ rows are dated, not weekly; point-in-time uses dt
        # snapshot identity: the timestamp where the file has one, else the week number
        out["snapshot"] = out["dt"].astype(str) if "dt" in out.columns else out["week"].astype(str)
    out["_source"] = src.name
    out["_as_of"] = as_of
    return out


def utc_stamp(now: Optional[dt.datetime] = None) -> str:
    return (now or dt.datetime.now(dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def file_stamp(as_of: str) -> str:
    return as_of.replace("-", "").replace(":", "")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class NotPublished(Exception):
    """HTTP 404: nflverse has no such file (expected above a source's last season)."""


def http_get(url: str, retries: int = 4, backoff: float = 2.0) -> tuple[bytes, dict]:
    last: Exception = RuntimeError("unreachable")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as resp:
                headers = {k.lower(): v for k, v in resp.headers.items()}
                return resp.read(), headers
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NotPublished(url) from e
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
        time.sleep(backoff ** attempt)
    raise RuntimeError(f"download failed after {retries} tries: {url}: {last}")


def source_url(src: Source, season: Optional[int]) -> str:
    return f"{RELEASE_BASE}/{src.tag}/{src.filename.format(season=season)}"


def seasons_for(src: Source, current: int) -> list[int]:
    if not src.per_season:
        return []
    last = src.last_season if src.last_season is not None else current
    return list(range(src.first_season, last + 1))


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
        "source": src.name,
        "season": season,
        "url": url,
        "status": "ok",
        "rows": int(len(out)),
        "columns": int(df.shape[1]),
        "source_sha256": sha256_bytes(raw),
        "source_bytes": len(raw),
        "source_last_modified": headers.get("last-modified"),
        "source_etag": headers.get("etag"),
        "key_nulls": {k: int(out[k].isna().sum()) for k in src.key if k in out.columns},
        "key_missing_cols": [k for k in src.key if k not in out.columns],
        "as_of": as_of,
        "store_file": str(path.relative_to(root)),
    }


def build(root: Path = DEFAULT_ROOT, manifest_path: Path = DEFAULT_MANIFEST, only: Optional[list] = None,
          min_season: Optional[int] = None, current: Optional[int] = None,
          fetch: Callable[[str], tuple[bytes, dict]] = http_get, now: Optional[dt.datetime] = None) -> dict:
    """Full rebuild of every selected source/season; the manifest is rewritten from the result.

    A past season inside a source's declared range that is not published is a failure (the store would have
    a silent hole); the in-progress season may be absent before kickoff; above ``last_season`` is skipped
    by construction.
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
            # The in-progress season may legitimately have no file yet (spring/summer, before kickoff).
            if entry["status"] != "ok" and season != current:
                failures.append(f"{name} {season}: {entry['status']} ({entry['url']})")
            print(f"{name:14s} {season!s:>5s} {entry['status']:14s} rows={entry.get('rows', '-')}", flush=True)
    manifest = {
        "build_as_of": as_of,
        "current_season": current,
        "builder": "prediction_market_bot.c1_signal_ingestion.nfl_event_store",
        "python": sys.version.split()[0],
        "pandas": pd.__version__,
        "sources": {n: {"tag": s.tag, "kind": s.kind, "first_season": s.first_season,
                        "last_season": s.last_season, "key": list(s.key), "note": s.note}
                    for n, s in SOURCES.items()},
        "files": entries,
        "failures": failures,
    }
    if not only and not min_season:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Build the NFL event store from free nflverse releases.")
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
