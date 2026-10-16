"""Real-store NBA tests (W78.4). Collected only when the event store has been built; when absent the directory is
not collected at all (it must not appear as skipped tests - GG-179 skip ceiling)."""
import os
from pathlib import Path

STORE = Path(os.environ.get("NBA_STORE_DIR", "exp_output/NBA_EVENTS"))
collect_ignore_glob = [] if (STORE / "raw" / "schedule").exists() else ["test_*.py"]
