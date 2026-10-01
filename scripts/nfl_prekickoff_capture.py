#!/usr/bin/env python3
"""T-601: standalone NFL pre-kickoff capture of the extended nflverse allowlist.

Calls NFLIngestionClient.capture_extended() (into a throwaway staging dir),
validates the retrieval, then APPENDS point-in-time records to the store:

    exp_output/NFL/INGESTION_CAPTURE/store/
        {schedule|team_stats}_ext_{season}_w{WW}_{stamp}.parquet   (never rewritten)
        capture_index.jsonl                                       (append-only)
        capture_rejects.jsonl                                     (append-only; refusals)

Semantics
  * Idempotent per (season, week, source): a record is appended only if the
    week-scoped content hash differs from every prior record for that key.
    Re-running with unchanged upstream content writes nothing.
  * Append, never overwrite: changed content is a NEW record with its own
    timestamp; existing files/lines are never opened for write.
  * Partial upstream data is refused (exit 2, nothing recorded as complete).
  * Captures only. Feeds no model, adapter, sizing or run path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion.nfl_ingestion import (  # noqa: E402
    NFLIngestionClient, _NFL_SCHEDULE_EXTENDED_FIELDS, _NFL_TEAM_STATS_EXTENDED_FIELDS,
)

DEFAULT_STORE = ROOT / "exp_output" / "NFL" / "INGESTION_CAPTURE" / "store"
ET = ZoneInfo("America/New_York")
# Populated pre-kickoff upstream (T-601 D1). referee / temp / wind are null until
# after the game and are therefore NOT required here -- they are still captured.
REQUIRED_PREKICKOFF = ["roof", "surface", "away_qb_id", "home_qb_id",
                       "away_coach", "home_coach"]


class PartialCapture(RuntimeError):
    pass


def kickoff_utc(gameday, gametime) -> datetime:
    if pd.isna(gameday) or pd.isna(gametime):
        raise PartialCapture("kickoff time missing (gameday/gametime null)")
    dt = datetime.strptime(f"{gameday} {gametime}", "%Y-%m-%d %H:%M").replace(tzinfo=ET)
    return dt.astimezone(timezone.utc)


def runtime_commit_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
            stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNKNOWN"


def frame_hash(df: pd.DataFrame) -> str:
    """Order-independent hash of the allowlisted content (provenance cols excluded)."""
    d = df[[c for c in df.columns if not c.startswith("_")]].copy()
    d = d.sort_values(list(d.columns), kind="mergesort").reset_index(drop=True)
    return hashlib.sha256(d.to_csv(index=False).encode()).hexdigest()


def pick_week(sched: pd.DataFrame, season: int, now: datetime, week: int | None) -> int:
    reg = sched[(sched["season"] == season) & (sched["game_type"] == "REG")]
    if week is not None:
        if reg[reg["week"] == week].empty:
            raise PartialCapture(f"no REG games for season {season} week {week}")
        return week
    upcoming = [int(w) for w, g in reg.groupby("week")
                if any(kickoff_utc(a, b) > now for a, b in zip(g["gameday"], g["gametime"]))]
    if not upcoming:
        raise PartialCapture(f"no upcoming REG week in season {season}")
    return min(upcoming)


def validate(sched: pd.DataFrame, stats: pd.DataFrame, season: int, week: int):
    """Return the target-week schedule slice, or raise PartialCapture."""
    missing = [c for c in _NFL_SCHEDULE_EXTENDED_FIELDS if c not in sched.columns] + \
              [c for c in _NFL_TEAM_STATS_EXTENDED_FIELDS if c not in stats.columns]
    if missing:
        raise PartialCapture(f"extended columns absent: {missing}")
    wk = sched[(sched["season"] == season) & (sched["week"] == week)
               & (sched["game_type"] == "REG")]
    if wk.empty:
        raise PartialCapture(f"schedule has no rows for week {week}")
    for col in ["home_team", "away_team"] + REQUIRED_PREKICKOFF:
        n = int(wk[col].isna().sum())
        if n:
            raise PartialCapture(f"{n}/{len(wk)} week-{week} games have null {col}")
    if week > 1:
        prev_teams = set(sched[(sched["season"] == season) & (sched["week"] == week - 1)
                               & (sched["game_type"] == "REG")][["home_team", "away_team"]]
                         .to_numpy().ravel())
        st = stats[(stats["season"] == season) & (stats["week"] == week - 1)]
        got = set(st["team"])
        if not prev_teams <= got:
            raise PartialCapture(
                f"team_stats week {week - 1} missing teams: {sorted(prev_teams - got)}")
        for col in _NFL_TEAM_STATS_EXTENDED_FIELDS:
            if st[col].isna().any():
                raise PartialCapture(f"team_stats week {week - 1} has null {col}")
    return wk


def last_hashes(index: Path) -> dict:
    seen: dict = {}
    if index.exists():
        for line in index.read_text().splitlines():
            r = json.loads(line)
            seen.setdefault((r["season"], r["week"], r["source"]), set()).add(r["content_sha256"])
    return seen


def run(season: int, week: int | None, store: Path, client: NFLIngestionClient,
        now: datetime | None = None, commit_sha: str | None = None) -> dict:
    store.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now(timezone.utc)
    commit_sha = commit_sha or runtime_commit_sha()
    index, rejects = store / "capture_index.jsonl", store / "capture_rejects.jsonl"
    staging = Path(tempfile.mkdtemp(prefix="nflcap_"))
    try:
        ok, manifest = client.capture_extended(season, staging)
        if not ok:
            raise PartialCapture(f"upstream fetch failed: {manifest}")
        ds = manifest["datasets"]
        if any(ds.get(n, {}).get("rows", 0) == 0 for n in ("schedule", "team_stats")):
            raise PartialCapture(f"empty dataset in capture: {ds}")
        sched = pd.read_parquet(staging / ds["schedule"]["file"])
        stats = pd.read_parquet(staging / ds["team_stats"]["file"])
        week = pick_week(sched, season, now, week)
        wk = validate(sched, stats, season, week)
        kicks = sorted(kickoff_utc(a, b) for a, b in zip(wk["gameday"], wk["gametime"]))
        preceded = [k.strftime("%Y-%m-%dT%H:%M:%SZ") for k in kicks if k > now]
        scoped = {
            "schedule": sched[(sched["season"] == season) & (sched["week"] == week)],
            "team_stats": stats,
        }
        seen, results = last_hashes(index), {}
        for name, df in scoped.items():
            key, h = (season, week, name), frame_hash(scoped[name])
            if h in seen.get(key, set()):
                results[name] = {"action": "skipped_unchanged", "content_sha256": h}
                continue
            meta = ds[name]
            stamp = meta["retrieved_at_utc"].replace(":", "").replace("-", "").split(".")[0]
            fname = f"{name}_ext_{season}_w{week:02d}_{stamp}.parquet"
            dest = store / fname
            if dest.exists():
                raise FileExistsError(f"refusing to overwrite capture: {dest}")
            df.to_parquet(dest)
            rec = {
                "season": season, "week": week, "source": name, "status": "complete",
                "captured_at_utc": meta["retrieved_at_utc"], "source_url": meta["url"],
                "upstream_sha256": meta["sha256"], "content_sha256": h,
                "rows": len(df), "file": fname,
                "kickoffs_preceded_utc": preceded, "runtime_commit_sha": commit_sha,
            }
            with index.open("a") as f:  # append-only
                f.write(json.dumps(rec, default=str) + "\n")
            results[name] = {"action": "appended", **rec}
        return {"season": season, "week": week, "results": results}
    except Exception as e:
        with rejects.open("a") as f:
            f.write(json.dumps({"at_utc": now.isoformat(), "season": season,
                                "week": week, "error": f"{type(e).__name__}: {e}",
                                "runtime_commit_sha": commit_sha}) + "\n")
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, default=None, help="default: next week with a future kickoff")
    ap.add_argument("--store", type=Path, default=DEFAULT_STORE)
    a = ap.parse_args(argv)
    from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
    a.store.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(str(a.store / "ingest_audit.jsonl"), min_severity="INFO")
    client = NFLIngestionClient(logger=logger, snapshot_id="T601-PREKICKOFF")
    try:
        out = run(a.season, a.week, a.store, client)
    except (PartialCapture, FileExistsError) as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
