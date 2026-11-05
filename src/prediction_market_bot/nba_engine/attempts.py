"""W102.1 (B-030): a trace for every NBA-engine runner attempt, so a run the kernel killed is visible afterwards.

Why it exists. On 2026-11-04 the OOM killer took 22 processes between 23:13Z and 00:18Z on the 961 MB box. A killed
runner prints nothing and leaves nothing: the cron log showed only bare ``Killed`` lines with no arm, no time and no game.
The two missing arms (v2 12 games, v3 18 games) could only be reconstructed from kernel logs. This module writes one
``start`` record before the heavy work and one ``end`` record after it; a ``start`` with no matching ``end`` IS a killed run.

Stdlib only, so it adds no memory. Writes ``attempts.jsonl`` beside the arm's own ``rows.jsonl``; never touches a row.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(rec) + "\n")


@contextmanager
def attempt(arm: str, out_dir: Path, now_fn=_now) -> Iterator[dict]:
    """Record start before and end after the body. A SIGKILL skips the ``end`` write, which is the signal."""
    path = Path(out_dir) / "attempts.jsonl"
    pid = os.getpid()
    _append(path, dict(event="start", arm=arm, pid=pid, ts=now_fn()))
    info: dict = {}
    try:
        yield info
    except BaseException as e:   # record the failure, then let it propagate unchanged
        _append(path, dict(event="end", arm=arm, pid=pid, ts=now_fn(), outcome="error", error=type(e).__name__))
        raise
    _append(path, dict(event="end", arm=arm, pid=pid, ts=now_fn(), outcome="ok", **info))


def read_attempts(out_dir: Path) -> list:
    p = Path(out_dir) / "attempts.jsonl"
    if not p.exists():
        return []
    out = []
    for ln in p.read_text().splitlines():
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue   # a torn last line from a kill mid-write
    return out


def unfinished(out_dir: Path) -> list:
    """Starts with no end for the same pid and arm: runs that were killed (or are running right now)."""
    open_: list = []
    for r in read_attempts(out_dir):
        if r.get("event") == "start":
            open_.append(r)
        elif r.get("event") == "end":
            for i in range(len(open_) - 1, -1, -1):
                if (open_[i]["pid"], open_[i]["arm"]) == (r.get("pid"), r.get("arm")):
                    open_.pop(i)
                    break
    return open_
