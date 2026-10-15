"""Real-store NFL tests (W73.2). Collected only when the event store has been built (the nfl_event_store workflow
builds it, then runs this directory). When absent the directory is not collected at all - it must not appear as
skipped tests, which would eat the GG-179 skip ceiling for a condition that is expected on every other CI run."""
import os
from pathlib import Path

STORE = Path(os.environ.get("NFL_STORE_DIR", "exp_output/NFL_EVENTS"))
collect_ignore_glob = [] if (STORE / "raw" / "schedules").exists() else ["test_*.py"]
