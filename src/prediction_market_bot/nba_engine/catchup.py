"""W102.1 (B-030): in-window catch-up for the NBA engine arms, cheap when nothing is stale.

Root cause it answers (docs: 12_EXPLORATORY/nba_engine_coverage_w102/ROOT_CAUSE.md). A game is priced only if a runner
completes while ``tip-60 <= now < tip``. The cron lines give each arm one fire per 10 minutes with no retry; when the kernel
kills a fire (961 MB box, ~500 MB per runner) the next fire is the only chance, and a burst of kills removes several in a row.
v2 is also chained behind v1 in one ``sh -c``, and v3 waits at most 240 s on the shared lock then exits silently.

What this does. One stdlib process (a few MB) reads each arm's ``status.json``. An arm that completed a run within
``MAX_AGE`` is left alone. A stale arm is run ONCE, alone and sequentially (two runners are never resident together), and a
run that dies by signal is retried once. Runs are idempotent per event, so a catch-up can never double-log a game.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

from prediction_market_bot.nba_engine.attempts import attempt

MAX_AGE = timedelta(minutes=12)    # cron cadence is 10 min; older than 12 means a fire was lost
RUN_TIMEOUT_S = 600
ARMS = {
    "v1": ("prediction_market_bot.nba_engine.live", Path("exp_output/NBA_ENGINE_LIVE")),
    "v2": ("prediction_market_bot.nba_engine.live_v2", Path("exp_output/NBA_ENGINE_LIVE_V2")),
    "v3": ("prediction_market_bot.nba_engine.live_v3", Path("exp_output/NBA_ENGINE_LIVE_V3")),
}


def last_run(out_dir: Path) -> Optional[datetime]:
    st = Path(out_dir) / "status.json"
    try:
        t = datetime.fromisoformat(json.loads(st.read_text())["as_of"])   # 3.9-safe: offset form only
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except (OSError, ValueError, KeyError, TypeError):
        return None


def stale_arms(now: datetime, arms: dict = ARMS, max_age: timedelta = MAX_AGE) -> list:
    out = []
    for name, (_, d) in arms.items():
        t = last_run(d)
        if t is None or now - t > max_age:
            out.append(name)
    return out


def _spawn(module: str, raw: str) -> int:
    return subprocess.run([sys.executable, "-m", module, "--raw", raw, "--no-refresh"],
                          timeout=RUN_TIMEOUT_S, stdout=subprocess.DEVNULL).returncode


def run_arm(name: str, raw: str, arms: dict = ARMS, spawn: Callable = _spawn) -> str:
    module, d = arms[name]
    outcome = "ok"
    for tries in (1, 2):
        with attempt(f"catchup:{name}:try{tries}", d) as info:
            try:
                rc = spawn(module, raw)
            except subprocess.TimeoutExpired:
                rc = -999
            info["returncode"] = rc
        if rc == 0:
            return "ok" if tries == 1 else "ok_after_retry"
        outcome = "killed" if rc < 0 else "error"
        if rc >= 0:
            break          # a normal error exit is not retried: it would fail the same way
    return outcome


def main(argv: Optional[list] = None, now: Optional[datetime] = None, spawn: Callable = _spawn) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Run only the NBA engine arms whose last completed run is stale.")
    ap.add_argument("--raw", default="exp_output/NBA_EVENTS/raw")
    a = ap.parse_args(argv)
    now = now or datetime.now(timezone.utc)
    stale = stale_arms(now, ARMS)
    result = {n: run_arm(n, a.raw, arms=ARMS, spawn=spawn) for n in stale}
    print(json.dumps(dict(as_of=now.isoformat(), stale=stale, result=result)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
