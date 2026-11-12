"""Parse archive claim files into point-in-time frames.

Every row keeps ``as_of`` (the date the table was read), ``source`` and
``source_time`` so a consumer can refuse a row that post-dates the decision it
feeds.  ``verification`` is carried through exactly as published (REPORTED
unless the bot has set it); the bot's own grade lives in GRADES, not here.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

import pandas as pd

SPORT_DIRS = {"nba": "nba", "nhl": "nhl", "nfl": "nfl", "mlb": "mlb"}
KEEP = (
    "id", "sport", "subject_type", "subject", "metric", "split", "value", "population_n",
    "source", "source_date", "source_time", "asof", "applies_to", "season",
    "extracted_from", "verification", "confidence", "game_id",
)


class ArchiveError(RuntimeError):
    pass


def table_family(extracted_from: str | None) -> str:
    """Normalise ``extracted_from`` to a table family, e.g. 'NBA.com Teams Opponent Shooting'.

    Drops the parenthetical (season / location / period) so one family spans
    seasons and splits.
    """
    s = (extracted_from or "").split("(")[0].strip()
    s = re.sub(r"\s*table\b.*$", "", s, flags=re.I).strip()
    s = re.sub(r"\d{4}-\d{2}", "", s).strip(" :,")
    return s or "unknown"


def _read_jsonl(path: Path) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class Archive:
    """A pinned, read-only view.  ``root`` is a checkout; ``sha`` is recorded on every frame."""

    def __init__(self, root: Path | str, sha: str):
        self.root = Path(root)
        self.sha = sha
        if not (self.root / "L3-split").is_dir():
            raise ArchiveError(f"{self.root} is not an archive checkout")

    # --- discovery -------------------------------------------------
    def split_files(self, sport: str) -> list[Path]:
        return sorted((self.root / "L3-split" / SPORT_DIRS[sport]).rglob("*.jsonl"))

    def snapshot_files(self, sport: str, kind: str) -> list[Path]:
        return sorted((self.root / "L3-snapshots" / SPORT_DIRS[sport]).glob(f"{kind}-*.jsonl"))

    # --- frames ----------------------------------------------------
    def split_frame(self, sport: str, family: str | None = None, season: int | None = None,
                    contains: str | None = None) -> pd.DataFrame:
        """Claims for a sport as one frame, filtered by table family / season (2025 = 2025-26)."""
        rows = []
        for p in self.split_files(sport):
            for r in _read_jsonl(p):
                fam = table_family(r.get("extracted_from"))
                if family and fam != family:
                    continue
                if season is not None and str(r.get("season")) != str(season):
                    continue
                if contains and contains not in (r.get("extracted_from") or ""):
                    continue
                d = {k: r.get(k) for k in KEEP}
                d["family"] = fam
                d["file"] = p.name
                d["value_num"] = _num(r.get("value"))
                rows.append(d)
        df = pd.DataFrame(rows)
        if not df.empty:
            df["archive_sha"] = self.sha
            df["as_of"] = pd.to_datetime(df["asof"], errors="coerce")
            df["source_time_utc"] = pd.to_datetime(df["source_time"], errors="coerce", utc=True)
        return df

    def families(self, sport: str) -> pd.DataFrame:
        """Table families present for a sport: row counts, seasons, files."""
        df = self.split_frame(sport)
        if df.empty:
            return df
        return (df.groupby("family").agg(rows=("id", "size"), seasons=("season", lambda s: sorted(set(map(str, s)))),
                                         files=("file", "nunique")).reset_index())

    def snapshots(self, sport: str, kind: str) -> pd.DataFrame:
        """Game-day snapshot records (NBA lineups/refs, NHL goalies/refs), one row per game per file."""
        rows = []
        for p in self.snapshot_files(sport, kind):
            for r in _read_jsonl(p):
                r = dict(r)
                r["file"] = p.name
                rows.append(r)
        df = pd.DataFrame(rows)
        if not df.empty:
            df["archive_sha"] = self.sha
        return df
