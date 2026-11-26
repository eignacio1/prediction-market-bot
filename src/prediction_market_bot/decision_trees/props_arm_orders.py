"""W130.2 (EXP-NBAPROPS-002): the 14 kept NBA player-prop leaves place flat DEMO orders; the fills are measured.

DEMO ONLY, flat demo stake, kelly_fraction 0. Pre-registration: 12_EXPLORATORY/nba_props_orders/PREREG.md (committed before any
order). The ADR-0072 addendum (arm orders, operator 2026-11-11) is the authority for demo orders; ADR-0072 is not edited and
arm_orders.py is untouched except that this module reuses its side rule and log helpers.

A shadow prop row (written by scripts/run_nba_engine_props_shadow.py) carries row["router_candidates"]["nba_props"]. It is
ELIGIBLE only if that record has prop_split_applied, no conflict, arm RIDE or FADE, and every applied split is one of the 14 kept
(leaf, split, split_leaf) entries of nba_props_v2.candidate.json. Anything else is a COUNTED skip with its own reason.

Gates, in order: switch -> demo host -> kill switch -> eligibility -> side -> band / time to tip (recomputed at order time) ->
idempotency (leaf, market, UTC day) -> listing -> demo-book caps (own derivation, PREREG s3) -> cash -> ADR-0072 placement
(book anchor, mid-gap skip) -> submit. Every order, would-order and skip is one line in logs/props_arm_orders/orders.jsonl with the
same event names as arm_orders ("arm_order" / "arm_would_order" / "arm_skip"), so scripts/arm_orders_read.py joins fills and
settlements on it unchanged.
Production Kalshi or real funds: never.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from prediction_market_bot.c5_execution import demo_fill_policy as pol
from prediction_market_bot.c5_execution import kill_switch_state as ksw
from prediction_market_bot.c5_execution.shadow_flat_stake import SHADOW_KILL_BAND, demo_host_ok, order_context
from prediction_market_bot.decision_trees import arm_orders as ao

BOOK = "PROPS_ARM_ORDERS"
SWITCH_ENV = "PROPS_ARM_ORDERS"
KILL_BAND = SHADOW_KILL_BAND
ORDER_EVENT, WOULD_EVENT, SKIP_EVENT = ao.ORDER_EVENT, ao.WOULD_EVENT, ao.SKIP_EVENT
OFF, DRY, ON = "off", "dry", "on"
CANDIDATE = "nba_props"
ARMS = ("RIDE", "FADE")

# PREREG s3 (each derived there; no real-money constant is read)
FLAT_STAKE_USD = 1.00
EVENT_CAP_USD = 51.00   # ceil(1120 matched rows / 22 held-out games = 50.9) x $1
DAY_CAP_USD = 408.00    # event cap x 8 games per slate

# PREREG s2: band windows in hours to tip (pregame_shadow PREGAME_WINDOWS: T2 4-8 h, T3 15-60 min)
BAND_HOURS = {"T2": (4.0, 8.0), "T3": (0.25, 1.0)}

_ROOT = Path(__file__).resolve().parents[3]
MAP_PATH = _ROOT / "12_EXPLORATORY" / "nba_props_splits" / "nba_props_v2.candidate.json"


def mode() -> str:
    v = (pol.switch_value(SWITCH_ENV) or "").strip().lower()
    return v if v in (ON, DRY) else OFF


def order_log_path() -> Path:
    return pol.log_path().parent / "props_arm_orders" / "orders.jsonl"


def _append(entry: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    e = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "book": BOOK, **entry}
    with open(path, "a") as fh:
        fh.write(json.dumps(e, sort_keys=True, default=str) + "\n")


def kept_entries(path: Path = MAP_PATH) -> dict:
    """{(leaf, split, split_leaf): arm} for the kept entries of the candidate map, plus the file's sha256."""
    raw = Path(path).read_bytes()
    doc = json.loads(raw)
    kept = {(s["leaf"], s["split"], s["split_leaf"]): s["arm"] for s in doc["splits"] if s.get("kept")}
    return kept, hashlib.sha256(raw).hexdigest()


def applied_entries(leaf_id: str, kept_list: list) -> list:
    """['minutes_trend@player=flat->RIDE', ...] -> [(leaf, 'minutes_trend@player', 'flat', 'RIDE'), ...]"""
    out = []
    for t in kept_list or []:
        try:
            lhs, arm = str(t).rsplit("->", 1)
            name, leaf = lhs.split("=", 1)
        except ValueError:
            return [("", str(t), "", "")]
        out.append((leaf_id, name, leaf, arm))
    return out


def eligibility(rec: Optional[dict], kept: dict) -> tuple:
    """(None, matched) when the nba_props candidate record is a kept-leaf order candidate, else (reason, [])."""
    if not rec:
        return "no_props_candidate", []
    if rec.get("branch") == "ERROR" or rec.get("arm") == "ERROR":
        return "candidate_error", []
    if rec.get("prop_split_conflict"):
        return "conflict", []
    if not rec.get("prop_split_applied"):
        return "no_split_applied", []
    arm = rec.get("arm")
    if arm not in ARMS:
        return "not_ride_or_fade", []
    ent = applied_entries(rec.get("leaf_id") or "", rec.get("prop_split_kept") or [])
    if not ent:
        return "no_split_applied", []
    for leaf, name, sl, a in ent:
        if kept.get((leaf, name, sl)) != a or a != arm:
            return "not_a_kept_leaf", []
    return None, ent


def hours_to_tip(row: dict, now: datetime) -> Optional[float]:
    s = row.get("start_time_utc")
    if not s:
        return None
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (t - now).total_seconds() / 3600.0


def _read(path: Path) -> list:
    out = []
    try:
        for line in path.read_text().splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    except FileNotFoundError:
        pass
    return out


def order_key(leaf_id: str, ticker: str, day: str) -> str:
    return f"{leaf_id}|{ticker}|{day}"


def already_ordered(key: str, log: list, m: str) -> bool:
    """True when this (leaf, market, day) already has an accepted order (or, in dry mode, a would-order)."""
    ev = (ORDER_EVENT,) if m == ON else (WOULD_EVENT,)
    return any(e.get("event") in ev and e.get("order_key") == key and (m != ON or e.get("ok")) for e in log)


def cap_reason(event: str, stake: float, day: str, log: list) -> Optional[str]:
    today = [e for e in log if e.get("event") == ORDER_EVENT and e.get("ok") and str(e.get("ts", "")).startswith(day)]
    if sum(float(e.get("stake_usd") or 0) for e in today if e.get("event_ticker") == event) + stake > EVENT_CAP_USD + 1e-9:
        return "demo_book_event_cap"
    if sum(float(e.get("stake_usd") or 0) for e in today) + stake > DAY_CAP_USD + 1e-9:
        return "demo_book_day_cap"
    return None


def act(row: dict, client: Any, now: Optional[datetime] = None, log: Optional[Path] = None,
        kept: Optional[dict] = None, map_sha: Optional[str] = None) -> Optional[dict]:
    """One shadow prop row -> at most one demo order. None when the switch is OFF. Never raises on a refusal; every outcome is logged."""
    m = mode()
    if m == OFF:
        return None
    now = now or datetime.now(timezone.utc)
    path = log or order_log_path()
    if kept is None:
        kept, map_sha = kept_entries()
    ticker = row.get("market_ticker")
    rid = f"{row.get('run_id')}|{ticker}"
    rec = (row.get("router_candidates") or {}).get(CANDIDATE)
    leaf_id = (rec or {}).get("leaf_id")
    day = now.strftime("%Y-%m-%d")
    key = order_key(str(leaf_id), str(ticker), day)
    base = {"row_id": rid, "ticker": ticker, "event_ticker": row.get("event_ticker"), "sport": row.get("sport"),
            "market_type": row.get("market_type"), "band": row.get("band"), "mode": m, "arm": (rec or {}).get("arm") or "UNROUTED",
            "leaf_id": leaf_id, "order_key": key, "kelly_fraction": 0, "map_sha256": map_sha, "prereg": "EXP-NBAPROPS-002",
            "split_path": {"kept": (rec or {}).get("prop_split_kept"), "earned": (rec or {}).get("prop_split_earned"),
                           "reason": (rec or {}).get("reason")}}

    def out(event, reason, **kw):
        r = {"event": event, "reason": reason, **base, **kw}
        _append(r, path)
        return r

    if not demo_host_ok():
        return out(SKIP_EVENT, "production_host_refused")
    halted = ksw.halt_reason(band_name=KILL_BAND)
    if halted:
        return out(SKIP_EVENT, "kill_switch_halted", meta=halted)
    why, _matched = eligibility(rec, kept)
    if why:
        return out(SKIP_EVENT, why)
    arm = rec["arm"]
    side = ao.side_for(arm, row, {"side": rec.get("side")})
    if side is None:
        return out(SKIP_EVENT, "side_disagrees")
    mid = row.get("mid")
    if not ticker or mid is None:
        return out(SKIP_EVENT, "row_missing_fields")
    h = hours_to_tip(row, now)
    if h is None:
        return out(SKIP_EVENT, "no_start_time")
    if h <= 0:
        return out(SKIP_EVENT, "tip_passed", hours_to_start=h)
    lo, hi = BAND_HOURS.get(str(leaf_id).split("|")[2] if leaf_id and leaf_id.count("|") >= 4 else "", (None, None))
    if lo is None or not (lo <= h < hi):
        return out(SKIP_EVENT, "outside_band", hours_to_start=h)
    base["hours_to_start_at_order"] = round(h, 4)
    logrows = _read(path)
    if already_ordered(key, logrows, m):
        return out(SKIP_EVENT, "already_ordered")
    would = "treatment" if pol.assigned(rid) else "control"
    base["adr0072_assignment"] = would
    why = pol.listing_skip_reason(client, ticker)
    if why:
        return out(SKIP_EVENT, "listing:" + str(why))
    stake = FLAT_STAKE_USD
    why = cap_reason(row.get("event_ticker") or ticker, stake, day, logrows)
    if why:
        return out(SKIP_EVENT, why, stake_usd=stake)
    why = pol.cash_skip_reason(client, stake)
    if why:
        return out(SKIP_EVENT, "cash:" + str(why), stake_usd=stake)
    dec = pol.decide(client, ticker, side, float(mid), rid)
    if dec.action != "SUBMIT":
        return out(SKIP_EVENT, "placement:" + str(dec.reason), meta=dec.meta, stake_usd=stake)
    price_yes = dec.mid_price
    entry = price_yes if side == "yes" else 1.0 - price_yes
    if m == DRY:
        return out(WOULD_EVENT, "dry_run_no_order", side=side, stake_usd=stake, price_yes=price_yes, entry_price=entry,
                   placement="rest_touch")
    order = client.submit_order(ticker=ticker, side=side, size_usd=stake, mid_price=price_yes, band=KILL_BAND,
                                client_order_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"props-arm-orders/{key}")))
    r = {"event": ORDER_EVENT, "ok": order.ok, "order_id": order.order_id, "stake_usd": stake, "side": side,
         "price_yes": price_yes, "entry_price": entry, "error": order.error, "placement": "rest_touch",
         **ao.submit_context(row, side, dec.meta, now), **base}
    if not order.ok:
        r["reason"] = "submit_rejected"
        r.update(pol.refusal_context(client, None))
    else:
        r["reason"] = "ok"
    _append(r, path)
    if order.ok and order.order_id:
        pol.schedule_cancel(client, order.order_id, rid, ticker)
    return r
