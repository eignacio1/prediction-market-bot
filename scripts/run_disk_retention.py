#!/usr/bin/env python3
"""W118.4 / B-102: cron entry for disk retention -- gzip-compress old, reader-verified evidence files and cap journald.
Never deletes evidence (see src/prediction_market_bot/disk_retention.py). Dry run: `scripts/run_disk_retention.py --dry-run`."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot import disk_retention  # noqa: E402

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    sys.exit(disk_retention.main((["--apply"] if not any(a == "--dry-run" for a in sys.argv[1:]) else []) + ["--root", str(ROOT)] + args))
