"""W125.2 / GG-2007: scripts/router_error_read.py groups ERROR / UNROUTED arm skips by cause, cell and date; read-only task."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import box_tasks  # noqa: E402
import router_error_read as rer  # noqa: E402


def _s(ts, arm, reason, sport="NBA", mt="SPREAD", band="T2"):
    return {"ts": ts, "event": "arm_skip", "arm": arm, "sport": sport, "market_type": mt, "band": band, "ticker": "T-1",
            "split_path": {"reason": reason}}


def test_groups_by_cause_collapsing_values_and_epoch_split():
    rows = [_s("2026-11-12T10:00:00Z", "ERROR", "KeyError:'KXNBASPREAD-26NOV12-A'"),
            _s("2026-11-13T10:00:00Z", "ERROR", "KeyError:'KXNBASPREAD-26NOV13-B'", sport="NFL", mt="TEAM_TOTAL", band="T1"),
            _s("2026-11-13T11:00:00Z", "UNROUTED", None, sport="NHL"),
            _s("2026-11-05T10:00:00Z", "ERROR", "KeyError:'old'"),  # pre-epoch: dropped
            _s("2026-11-13T12:00:00Z", "RIDE", "x"),  # routed arm: not an ERROR
            {"ts": "2026-11-13T12:00:00Z", "event": "arm_order", "arm": "ERROR"}]  # not a skip
    out = rer.summarise(rows)
    assert out["total_by_arm"] == {"ERROR": 2, "UNROUTED": 1}
    ck = "ERROR|KeyError:'<x>'"
    assert out["causes"][ck]["n"] == 2 and out["causes"][ck]["by_sport"] == {"NBA": 1, "NFL": 1}
    assert out["causes"]["UNROUTED|(no reason logged)"]["n"] == 1
    assert out["per_day"]["2026-11-12"] == {ck: 1}
    assert rer.summarise(rows, None)["total_by_arm"]["ERROR"] == 3
    # W126.1: all skip rows per day and sport (post-epoch), so a zero-ERROR day is distinguishable from a no-row day
    assert out["skip_rows_per_day_by_sport"] == {"2026-11-12": {"NBA": 1}, "2026-11-13": {"NFL": 1, "NHL": 1, "NBA": 1}}


def test_task_allowlisted_read_only():
    cmd = box_tasks.TASKS["router_error_read"]
    assert cmd.endswith("scripts/router_error_read.py") and ">" not in cmd.split("scripts/")[0]
