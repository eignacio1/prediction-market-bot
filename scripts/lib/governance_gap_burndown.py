#!/usr/bin/env python3
"""Governance-gap open/total burn-down tracker (T-368).

GOVERNANCE_GAP_LOG.md has no structured per-gap open/close date field (only
free-text prose dates buried in Status cells), so burn-down cannot be
derived by parsing the log's own history. This module tracks it instead via
a small, self-maintained JSONL snapshot history file, appended to on every
governance_scan.sh run. It is READ-ONLY with respect to the gap log's
content — open/total counts are passed in as already-computed grep results
from governance_scan.sh; this module never reads GOVERNANCE_GAP_LOG.md.
"""
from __future__ import annotations

import json
import os
import sys
import time

LOOKBACK_SEC = 14 * 86400
HISTORY_CAP = 200


def load_history(hist_path: str) -> list[dict]:
    history: list[dict] = []
    if os.path.exists(hist_path):
        with open(hist_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    history.append(json.loads(line))
                except Exception:
                    pass
    return history


def save_history(hist_path: str, history: list[dict]) -> None:
    os.makedirs(os.path.dirname(hist_path) or ".", exist_ok=True)
    with open(hist_path, "w") as f:
        for h in history[-HISTORY_CAP:]:
            f.write(json.dumps(h) + "\n")


def render_summary(open_n: int, total_n: int, history: list[dict], now: float) -> str:
    resolved_n = max(0, total_n - open_n)
    pct_open = (open_n / total_n * 100) if total_n else 0.0
    lines = [f"  {open_n} open / {total_n} total ({resolved_n} resolved, {pct_open:.1f}% open)"]

    candidates = [h for h in history if now - h.get("ts", now) <= LOOKBACK_SEC and "open" in h]
    if candidates:
        baseline = min(candidates, key=lambda h: h["ts"])
        days = max((now - baseline["ts"]) / 86400, 1e-6)
        delta = open_n - baseline["open"]
        rate = delta / days
        trend = "SHRINKING" if delta < 0 else "GROWING" if delta > 0 else "FLAT"
        lines.append(f"  Burn-down: {delta:+d} over {days:.1f}d ({rate:+.2f}/day) — trend: {trend}")
    else:
        lines.append(
            f"  Burn-down: insufficient history yet ({len(history)} prior snapshot(s) "
            "within 14d — need >=2 spread over time)"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    open_n, total_n, hist_path = int(argv[1]), int(argv[2]), argv[3]
    now = time.time()

    history = load_history(hist_path)
    print(render_summary(open_n, total_n, history, now))

    history.append({"ts": now, "open": open_n, "total": total_n})
    save_history(hist_path, history)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
