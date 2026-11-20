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


def previous_mid(row: dict, ledger_path: Optional[str] = None) -> tuple:
    """(prev_mid, source). In-process memory first, then the cell ledger tail, else (None, 'unavailable').
    ledger_path (W115.3): the cell file of a writer that does not use PM_SHADOW_DIR naming (the NHL writer)."""
    t = row["market_ticker"]
    if t in _SEEN:
        return _SEEN[t], "process_memory"
    base = os.environ.get("PM_SHADOW_DIR", os.path.join("exp_output", "PREGAME_SHADOW"))
    path = ledger_path or os.path.join(base, f"{row.get('sport')}_{row.get('market_type')}_{row.get('band')}.jsonl")
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
                  filters_note: Optional[str] = None, ledger_path: Optional[str] = None,
                  depth: Optional[dict] = None, props: Optional[dict] = None) -> dict:
    """{'router': {...}} for a shadow row; never raises (a failure is recorded as branch ERROR).

    filters: optional {filter_name: leaf_or_bool} from nfl_engine.filters / the NBA granularity filter, computed by a
    caller that has the per-game context (W112.1: runner.run_once via filter_supply); absent -> filters_fired is [] and
    filters_note says why (the supply's note, else "no per-row filter input"). Logs the split path: the market-state leaf, then
    each tested filter condition that was kept (changed or agreed with the arm), logged only, or untested."""
    try:
        cand_prev = None
        if candidate_arms_on():  # v1's route_row updates _SEEN with this row's mid, so resolve the previous mid first
            cand_prev = prev_mid if prev_mid is not None else previous_mid(row, ledger_path)[0]
        out = {"router": route_row(row, series, prev_mid, filters, filters_note, ledger_path, depth)}
        if candidate_arms_on():  # W120.2: shadow only; the v1 block above is what orders read and is never altered
            out["router_candidates"] = candidate_fields(row, series, cand_prev, filters, ledger_path, depth, props)
        return out
    except Exception as e:  # noqa: BLE001
        # W115.3 (GG-1939): the type name alone hid the cause of 5,390 ERROR rows on the box; the message rides along.
        return {"router": {"branch": "ERROR", "side": None, "depth": None, "tier": None,
                           "reason": (type(e).__name__ + ":" + str(e))[:160], "orders": "off"}}


def candidate_arms_on() -> bool:
    """W120.2: logs the arm each candidate map would pick beside v1. ON by default (operator approved queue item 7, 2026-11-18 21:19 PT);
    PM_CANDIDATE_ARMS=off is the off-switch. Shadow only: orders follow v1."""
    return os.environ.get("PM_CANDIDATE_ARMS", "on").strip().lower() != "off"


# name -> (map version, sports it applies to or None for all, depth switch)
CANDIDATES = {"router_v2": ("v2", None, False), "nba_depth": ("v1+nba_depth", ("NBA",), True),
              "nhl_v2": ("nhl_v2", ("NHL",), False),
              # W121.2: NBA player-prop market-state leaves + 4 player splits (EXP-NBAPROPS-001); applies to NBA_PLAYER_* rows only
              "nba_props": ("nba_props", ("NBA",), False),
              # W122.4 (GG-1957): the pinned MLB 2027 pre-registered map's arm beside v1 on every MLB game-cell row; shadow only
              "mlb_2027": ("mlb_2027", ("MLB",), False)}


@lru_cache(maxsize=None)
def _cand_ev(version: str, depth_on: bool):
    import hashlib

    path = lm.map_path(version)
    with open(path, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    ev = Evidence(ride=ride.load(), leaf_map=lm.LeafMap.load(path), depth_on=depth_on,
                  prop_splits=lm.default_prop_splits() if version == "nba_props" else None)
    return ev, os.path.basename(path), sha


def candidate_fields(row: dict, series: str, prev_mid: Optional[float], filters: Optional[dict],
                     ledger_path: Optional[str], depth: Optional[dict], props: Optional[dict] = None) -> dict:
    """{name: {arm, branch, side, leaf_id, reason, map, map_version, map_sha256}} for each candidate that applies to the
    row's sport. A candidate that errors logs ERROR with its message; it never blocks the row or touches v1's block."""
    out: dict = {}
    sport = str(row.get("sport", "")).upper()
    for name, (version, sports, dep) in CANDIDATES.items():
        if sports is not None and sport not in sports:
            continue
        if name == "nba_props" and not str(row.get("market_type", "")).startswith("NBA_PLAYER_"):
            continue
        rec = {"map_version": version}
        try:
            ev, fname, sha = _cand_ev(version, dep)
            rec.update(map=fname, map_sha256=sha)
            s = Situation(sport=row.get("sport", ""), family=series, ticker=row["market_ticker"], event=row["event_ticker"],
                          tier=tier_for_hours(row.get("horizon_hours_to_start")), yes_bid=row["yes_bid"],
                          yes_ask=row["yes_ask"], half_spread=row.get("half_spread"), model_p=row.get("p_yes"),
                          market_type=row.get("market_type"), band=row.get("band"), prev_mid=prev_mid,
                          filters=filters or None, depth=(depth or {}).get("leaves") or None,
                          props=(props if name == "nba_props" else None) or None)
            r = route(s, ev)
            d = r.leaf
            rec.update(arm=d.arm if d else r.tree, branch=r.tree, side=r.side, leaf_id=d.leaf_id if d else None,
                       reason=";".join(map(str, r.reasons))[:160])
            if name == "nba_props":  # W121.2: which splits fired and whether they are BH-earned, and the leaves that were logged only
                ps = r.prop_split
                rec.update(prop_leaves=props or None, prop_split_kept=ps["kept"] if ps else [], prop_split_earned=ps["earned"] if ps else [],
                           prop_split_applied=bool(ps and ps["arm"] and not ps["conflict"]), prop_split_conflict=bool(ps and ps["conflict"]))
        except Exception as e:  # noqa: BLE001
            rec.update(arm="ERROR", branch="ERROR", side=None, leaf_id=None, reason=(type(e).__name__ + ":" + str(e))[:160])
        out[name] = rec
    return out


def _depth_fields(depth: Optional[dict], ds: Optional[dict]) -> dict:
    """W119.2: depth leaves, pinned archive SHA and the depth-split verdict, logged on every NBA row (switch on or off).
    Nothing is added to rows without depth input, so non-NBA and v1 rows are byte-identical to before."""
    if not depth:
        return {}
    return {"depth_leaves": depth.get("leaves"), "depth_archive_sha": depth.get("archive_sha"),
            "depth_season": depth.get("season"), "depth_logged_only": depth.get("logged_only"),
            "depth_split_applied": bool(ds and ds["kept"] and ds["arm"] and not ds["conflict"]),
            "depth_split_kept": ds["kept"] if ds else [], "depth_split_conflict": bool(ds and ds["conflict"])}


def route_row(row: dict, series: str, prev_mid: Optional[float] = None, filters: Optional[dict] = None,
              filters_note: Optional[str] = None, ledger_path: Optional[str] = None,
              depth: Optional[dict] = None) -> dict:
    """The router block for a row. Raises on a malformed row (router_fields records that as branch ERROR)."""
    move_src = "caller"
    if prev_mid is None:
        prev_mid, move_src = previous_mid(row, ledger_path)
    s = Situation(sport=row.get("sport", ""), family=series, ticker=row["market_ticker"], event=row["event_ticker"],
                  tier=tier_for_hours(row.get("horizon_hours_to_start")), yes_bid=row["yes_bid"],
                  yes_ask=row["yes_ask"], half_spread=row.get("half_spread"), model_p=row.get("p_yes"),
                  market_type=row.get("market_type"), band=row.get("band"), prev_mid=prev_mid, filters=filters or None,
                  depth=(depth or {}).get("leaves") or None)
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
           **_depth_fields(depth, r.depth_split),
           "move_source": move_src if prev_mid is not None else f"na:{move_src}"}
    return out


def hook_for(ledger_path_for=None, supply=None):
    """W115.3: the router hook for a shadow writer that does not go through pregame_shadow.runner (the NHL writer).
    Returns ``extra_for(row) -> {'router': {...}}``: filters from the supply (known before the row's ts_utc), the previous
    mid from the writer's own cell file, then the same router_fields the runner calls. Logging only; never raises."""
    def extra_for(row: dict) -> dict:
        try:
            from prediction_market_bot.decision_trees.filter_supply import default_supply
            sup = supply or default_supply()
            flt, note = sup.for_row(row)
            series = str(row.get("market_ticker", "")).split("-", 1)[0]
            path = str(ledger_path_for(row)) if ledger_path_for else None
            return router_fields(row, series, filters=flt, filters_note=note, ledger_path=path, depth=getattr(sup, "depth_for_row", lambda r: None)(row))
        except Exception as e:  # noqa: BLE001
            return {"router": {"branch": "ERROR", "side": None, "depth": None, "tier": None,
                               "reason": ("hook:" + type(e).__name__ + ":" + str(e))[:160], "orders": "off"}}
    return extra_for
