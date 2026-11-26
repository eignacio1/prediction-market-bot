#!/usr/bin/env python3
"""W129.4 Part B: NBA PAM state backfill from the event store. Streams gz JSONL per season to
exp_output/PAM_STATE/nba/ (git-ignored) and writes a committed manifest (row counts + sha256).
Usage: pam_state_backfill_nba.py [NBA_EVENTS root] [out dir] [--seasons 2023,2024]"""
from __future__ import annotations

import glob
import json
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import tip_table  # noqa: E402
from prediction_market_bot.pam import nba_state_backfill as B  # noqa: E402

INJ_DIRS = [REPO / "12_EXPLORATORY/20261012_nba_points_minutes/inj", REPO / "12_EXPLORATORY/20261013_nba_games_availability/inj2026"]
DEFAULT_ROOT = Path("/Users/earlignacio/PredictionMarketEvidence/data/exp_output/NBA_EVENTS")


def load_inj() -> dict:
    out = {}
    for d in INJ_DIRS:
        for f in sorted(glob.glob(str(d / "inj_*.json"))):
            day = pd.Timestamp(Path(f).stem.split("_")[1]).date()
            data = json.load(open(f))
            if data:
                out[day] = {k: v for k, v in data.items() if v is not None}
    return out


def rd(root: Path, kind: str) -> pd.DataFrame:
    return pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(root / "raw" / kind / "*.parquet")))], ignore_index=True)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0]) if args else DEFAULT_ROOT
    out = Path(args[1]) if len(args) > 1 else REPO / "exp_output/PAM_STATE/nba"
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--seasons="):
            only = {int(x) for x in a.split("=")[1].split(",")}
    t0 = time.time()
    written_at = pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    tips = tip_table(rd(root, "schedule"), rd(root, "espn_schedule"))
    b = B.prepare(rd(root, "player_box"), tips)
    b = B.player_priors(b)
    inj = load_inj()
    manifest = {"version": B.VERSION, "written_at": written_at, "files": {}}
    for s in sorted(b["season"].unique()):
        if only and s not in only:
            continue
        sb = b[b["season"] == s]
        n, sha = B.write_gz(out / f"player_state_{s}.jsonl.gz", B.build_player_state(sb, inj, written_at))
        manifest["files"][f"player_state_{s}"] = {"rows": n, "sha256": sha}
        n2, sha2 = B.write_gz(out / f"availability_profile_{s}.jsonl.gz", B.build_availability(sb, written_at))
        manifest["files"][f"availability_profile_{s}"] = {"rows": n2, "sha256": sha2}
        print(s, n, n2, f"{time.time()-t0:.0f}s", flush=True)
    draft = json.load(open(REPO / "12_EXPLORATORY/pam_stability/trait_reliability_draft.json"))
    n3, sha3 = B.write_gz(out / "trait_reliability.jsonl.gz", B.build_trait_reliability(draft, written_at))
    manifest["files"]["trait_reliability"] = {"rows": n3, "sha256": sha3}
    mp = REPO / "12_EXPLORATORY/pam_state/MANIFEST.json"
    mp.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    print("manifest", mp, f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
