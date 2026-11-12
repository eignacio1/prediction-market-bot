"""W110.3 Part B / W111.3 Part A -- the router's decision for a pre-game shadow row. Logging only: no order path, no sizing.

Applies to rows the shadow runner writes (bands T1/T2/T3, horizon known). Does not apply to in-play rows (none are
written here). Since W111.3 the per-leaf arm map (W110.5, fit window only) decides; every row logs leaf_id, arm,
arm_source and the filters that fired. A thin or unseen leaf is logged NO_BET with the reason.
The move bin needs the ticker's previous mid: it is read from the cell's ledger tail (PM_SHADOW_DIR, default
exp_output/PREGAME_SHADOW); where that is unavailable the move bin is "na" and move_source says so.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from prediction_market_bot.decision_trees import leaf_map as lm
from prediction_market_bot.decision_trees import ride
from prediction_market_bot.decision_trees.coverage import DEPTH
from prediction_market_bot.decision_trees.router import Evidence, Situation, route

TAIL_BYTES = 2_000_000
_LAST_MID: dict = {}  # (cell file, size) -> {ticker: mid}
_SEEN: dict = {}  # ticker -> mid, set by this process after each decision


def tier_for_hours(h: Optional[float]) -> Optional[str]:
    """Same buckets as calib.tier (>=24 T>24h, >=6 T6-24h, >=2 T2-6h, else T0-2h)."""
    if h is None or h <= 0:
        return None
    return "T>24h" if h >= 24 else "T6-24h" if h >= 6 else "T2-6h" if h >= 2 else "T0-2h"


@lru_cache(maxsize=1)
def _ev() -> Evidence:
    return Evidence(ride=ride.load(), leaf_map=lm.default_map())


def _ledger_tail_mids(path: str) -> dict:
    import json

    out: dict = {}
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            fh.seek(max(0, size - TAIL_BYTES))
            data = fh.read().decode("utf-8", "ignore").splitlines()
        for line in data[1:] if size > TAIL_BYTES else data:
            try:
                r = json.loads(line)
                out[r["market_ticker"]] = float(r["mid"])
            except Exception:  # noqa: BLE001
                continue
    except OSError:
        return {}
    return out


def previous_mid(row: dict) -> tuple:
    """(prev_mid, source). In-process memory first, then the cell ledger tail, else (None, 'unavailable')."""
    t = row["market_ticker"]
    if t in _SEEN:
        return _SEEN[t], "process_memory"
    base = os.environ.get("PM_SHADOW_DIR", os.path.join("exp_output", "PREGAME_SHADOW"))
    path = os.path.join(base, f"{row.get('sport')}_{row.get('market_type')}_{row.get('band')}.jsonl")
    try:
        key = (path, os.path.getsize(path))
    except OSError:
        return None, "unavailable"
    if key not in _LAST_MID:
        _LAST_MID.clear()
        _LAST_MID[key] = _ledger_tail_mids(path)
    m = _LAST_MID[key].get(t)
    return (m, "ledger_tail") if m is not None else (None, "unavailable")


_NEUTRAL = ("unknown", "neutral", "mid", "calm", "")


def router_fields(row: dict, series: str, prev_mid: Optional[float] = None, filters: Optional[dict] = None,
                  filters_note: Optional[str] = None) -> dict:
    """{'router': {...}} for a shadow row; never raises (a failure is recorded as branch ERROR).

    filters: optional {filter_name: leaf_or_bool} from nfl_engine.filters / the NBA granularity filter, computed by a
    caller that has the per-game context (W112.1: runner.run_once via filter_supply); absent -> filters_fired is [] and
    filters_note says why (the supply's note, else "no per-row filter input"). Logs the split path: the market-state leaf, then
    each tested filter condition that was kept (changed or agreed with the arm), logged only, or untested."""
    try:
        move_src = "caller"
        if prev_mid is None:
            prev_mid, move_src = previous_mid(row)
        s = Situation(sport=row.get("sport", ""), family=series, ticker=row["market_ticker"], event=row["event_ticker"],
                      tier=tier_for_hours(row.get("horizon_hours_to_start")), yes_bid=row["yes_bid"],
                      yes_ask=row["yes_ask"], half_spread=row.get("half_spread"), model_p=row.get("p_yes"),
                      market_type=row.get("market_type"), band=row.get("band"), prev_mid=prev_mid, filters=filters or None)
        r = route(s, _ev())
        d = r.leaf
        if s.mid is not None:
            _SEEN[row["market_ticker"]] = s.mid
        fired = sorted(k for k, v in (filters or {}).items() if v is True or (v and str(v) not in _NEUTRAL))
        sp = r.split
        out = {"branch": r.tree, "side": r.side, "depth": DEPTH.get(row.get("band"), "stripped"), "tier": s.tier,
               "reason": ";".join(map(str, r.reasons)), "orders": "off",
               "leaf_id": d.leaf_id if d else None, "arm": d.arm if d else None,
               "arm_source": lm.ARM_SOURCE if d else None, "thin": d.thin if d else None,
               "filters_fired": fired,
               "filters_note": None if filters is not None else (filters_note or "no per-row filter input"),
               "filters_n": len(filters) if filters else 0,
               "split_kept": sp["kept"] if sp else [], "split_logged_only": sp["logged_only"] if sp else [],
               "split_untested_n": len(sp["untested"]) if sp else 0, "split_conflict": bool(sp and sp["conflict"]),
               "arm_pre_split": r.arm_pre_split,
               "split_path": (d.leaf_id + (" > " + " > ".join(sp["kept"]) if sp and sp["kept"] else "")) if d else None,
               "move_source": move_src if prev_mid is not None else f"na:{move_src}"}
        return {"router": out}
    except Exception as e:  # noqa: BLE001
        return {"router": {"branch": "ERROR", "side": None, "depth": None, "tier": None,
                           "reason": type(e).__name__, "orders": "off"}}
