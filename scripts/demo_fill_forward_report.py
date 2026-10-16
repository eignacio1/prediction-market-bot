"""W68.2 Part B / ADR-0072: the forward test reports itself. DEMO ONLY. Daily, after the 11:00 UTC T1 run.

Reads logs/demo_fill_policy.jsonl (the order/skip/cancel log) and, read-only against the Kalshi DEMO
API, each order's fill count and each filled market's settlement. Per book (paper = MLB T1/T4 orders,
shadow = SHADOW-cell flat stakes) and sport, per arm: orders, skips by reason, cancels and outcomes,
cancel success rate, fills, win rate on fills, settle minus price on fills, and fills per week projected
against the ADR-0072 judged n (~550 per arm in 8 weeks).

It also checks the ADR-0072 turn-off conditions. A tripped condition writes both switches as `off` to the untracked
deploy/demo_fill.override.env (read last by the policy; GG-587) and logs a `turn_off` event. Output:
exp_output/FORWARD_TEST/demo_fill_forward_report.json, plus one summary line on stdout.

Honest gaps (reported as such, never guessed): the 30-minute markout condition needs candle data this
job does not collect (NOT_EVALUABLE); the SHADOW control arm places no order by design (control_arm skip),
so shadow treatment-minus-control cannot be formed from fills.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot.atomic_io import atomic_write_text  # noqa: E402  GG-754
from prediction_market_bot.c5_execution.demo_fill_policy import is_venue_transient  # noqa: E402  GG-841

JUDGED_N = 550
WEEKS = 8
ENV_FILE = REPO / "deploy" / "demo_fill.env"
OUT = REPO / "exp_output" / "FORWARD_TEST" / "demo_fill_forward_report.json"
SWITCH_KEYS = ("DEMO_FILL_PLACEMENT_RULE", "SHADOW_FLAT_STAKE")
CANCEL_FAIL_MAX = 0.10
SKIP_RATE_MAX = 0.90
# ADR-0072 addendum 2026-10-14 (operator): listing skips are demo-catalog gaps (GG-564), not placement-rule skips.
# W73.1: the cancel path was fixed (GG-645/623) and the test re-armed at this instant (W72.1 read-back, 2026-10-14T00:44Z
# slice start). Cancel failures before it come from the superseded code; counting them re-tripped the turn-off at
# 2026-10-14T11:25Z on 10-13's 8/8 pre-fix failures. The ">10% in a day" rule is unchanged, evaluated on post-fix attempts.
CANCEL_PATH_FIX_EPOCH = datetime(2026, 10, 13, 23, 58, tzinfo=timezone.utc)
LISTING_SKIP_REASONS = frozenset({"not_listed_on_demo"})
NO_OUTCOME_S = 15 * 60

SPORTS = (("KXMLB", "MLB"), ("KXNBA", "NBA"), ("KXNHL", "NHL"), ("KXNFL", "NFL"))


def sport_of(ticker: Any) -> str:
    t = str(ticker or "").upper()
    return next((s for p, s in SPORTS if t.startswith(p)), "OTHER" if t else "UNKNOWN")


def _ts(r: dict) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(r.get("ts")))
    except ValueError:
        return None


def load_events(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if isinstance(r, dict) and _ts(r) is not None:
            out.append(r)
    return out


def book_of(r: dict) -> str:
    """Shadow ids are `run_id|ticker`; paper position ids carry no '|'."""
    ident = str(r.get("row_id") or r.get("position_id") or "")
    return "shadow" if ("|" in ident or r.get("event", "").startswith("shadow_")) else "paper"


def ticker_of(r: dict) -> str:
    t = r.get("ticker")
    if t:
        return str(t)
    return str(r.get("row_id") or "").rsplit("|", 1)[-1] if "|" in str(r.get("row_id") or "") else ""


def order_price_side(order: dict) -> tuple[Optional[str], Optional[float]]:
    """(side, per-contract price paid in dollars) from an order GET, defensive about cents/dollars."""
    side = order.get("side")
    try:
        fc = float(order.get("fill_count_fp") or order.get("fill_count") or 0)
        cost = sum(float(order.get(k) or 0) for k in ("taker_fill_cost_dollars", "maker_fill_cost_dollars"))
        if fc > 0 and cost > 0:
            return side, cost / fc
        raw = order.get("yes_price_dollars") if side == "yes" else order.get("no_price_dollars")
        if raw is None:
            raw = order.get("yes_price") if side == "yes" else order.get("no_price")
            raw = None if raw is None else float(raw) / 100.0
        return side, None if raw is None else float(raw)
    except (TypeError, ValueError):
        return side, None


def lookup_fill(client: Any, order_id: str, ticker: str, cache: dict) -> dict:
    """Terminal results are cached so a settled order is never re-fetched."""
    hit = cache.get(order_id)
    if hit and hit.get("settled"):
        return hit
    ok, data = client._get(f"/portfolio/orders/{order_id}", authenticated=True)
    if not ok or not isinstance(data, dict):
        return {"status": "unretrievable"}
    order = data.get("order", data)
    side, price = order_price_side(order)
    try:
        fills = float(order.get("fill_count_fp") or order.get("fill_count") or 0)
    except (TypeError, ValueError):
        fills = 0.0
    rec: dict[str, Any] = {"status": order.get("status"), "fills": fills, "side": side, "price": price, "settled": False,
                           "last_update": order.get("last_update_time")}
    if fills > 0:
        mok, mdata = client._get(f"/markets/{ticker}")
        m = (mdata.get("market", mdata) if mok and isinstance(mdata, dict) else {}) or {}
        res = str(m.get("result") or "").lower()
        if res in ("yes", "no") and side in ("yes", "no"):
            rec.update(settled=True, won=(res == side))
    elif str(order.get("status")) in ("canceled", "cancelled", "expired"):
        # Terminal and unfilled: the order itself cannot change. E3 (W76.1) also needs the counterfactual
        # outcome of the side it WOULD have bought; the order is re-read until its market has resolved.
        mok, mdata = client._get(f"/markets/{ticker}")
        m = (mdata.get("market", mdata) if mok and isinstance(mdata, dict) else {}) or {}
        res = str(m.get("result") or "").lower()
        if res in ("yes", "no") and side in ("yes", "no"):
            rec.update(settled=True, nf_won=(res == side))
        else:
            rec["nf_pending"] = True
            rec["settled"] = str(m.get("status")) in ("finalized", "settled") and not res  # voided: nothing to learn
    cache[order_id] = rec
    return rec


TERMINAL_STATUSES = ("executed", "filled", "canceled", "cancelled", "expired")


TERMINAL_SLACK_S = 30


def _historical_404_terminal(r: dict, fills_for: Optional[Callable[[str, str], dict]]) -> bool:
    """GG-596/GG-646: a logged cancel_failed whose response was HTTP 404 is already_terminal only when the
    order was terminal BEFORE the cancel attempt (last_update_time <= attempt ts + slack). An order that was
    exchange-canceled at market close hours after a failed 60s cancel is a real failure. No lookup, no
    timestamp, or an unparseable one stays a failure (unverified)."""
    resp = r.get("response")
    if fills_for is None or not (isinstance(resp, dict) and str(resp.get("error")) == "HTTP 404"):
        return False
    st = fills_for(r.get("order_id"), ticker_of(r))
    if str(st.get("status") or "").lower() not in TERMINAL_STATUSES:
        return False
    attempt = _ts(r)
    try:
        terminal_at = datetime.fromisoformat(str(st.get("last_update")).replace("Z", "+00:00"))
    except ValueError:
        return False
    if attempt is None:
        return False
    if terminal_at.tzinfo is None:
        terminal_at = terminal_at.replace(tzinfo=timezone.utc)
    if attempt.tzinfo is None:
        attempt = attempt.replace(tzinfo=timezone.utc)
    return terminal_at <= attempt + timedelta(seconds=TERMINAL_SLACK_S)


def build_report(events: list[dict], now: datetime, fills_for: Optional[Callable[[str, str], dict]],
                 window_note: str = "", since: Optional[datetime] = None) -> dict:
    if since is not None:
        events = [r for r in events if _ts(r) >= since]
    cells: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {
        "orders": 0, "rejected": 0, "skips": Counter(), "control_skips": 0,
        "cancel_scheduled": 0, "cancel_ok": 0, "cancel_failed": 0, "cancel_failed_venue": 0,
        "cancel_already_terminal": 0, "no_outcome": 0,
        "fill_orders": [], "first_ts": None})
    outcome: dict[str, str] = {}
    sched: dict[str, tuple[datetime, str, str]] = {}
    for r in events:
        ev = r.get("event")
        if ev in ("cancel_ok", "cancel_failed", "cancel_already_terminal"):
            outcome[r.get("order_id")] = ev
    day_cancel: dict[str, Counter] = defaultdict(Counter)
    day_skip: dict[str, Counter] = defaultdict(Counter)
    for r in events:
        ev, ts = r.get("event"), _ts(r)
        arm = "control" if (ev == "shadow_order" and r.get("arm") == "control") else "treatment"
        key = (book_of(r), sport_of(ticker_of(r)), arm)
        c = cells[key]
        if c["first_ts"] is None or ts < c["first_ts"]:
            c["first_ts"] = ts
        day = ts.date().isoformat()
        if ev == "shadow_order":
            if r.get("ok"):
                c["orders"] += 1
                if r.get("order_id"):
                    c["fill_orders"].append((r["order_id"], ticker_of(r)))
            else:
                c["rejected"] += 1
            day_skip[day]["orders"] += 1
        elif ev in ("shadow_skip", "skip"):
            reason = str(r.get("reason"))
            if reason == "control_arm":
                c["control_skips"] += 1
            elif reason in LISTING_SKIP_REASONS:
                c["skips"][reason] += 1
                day_skip[day]["listing_skips"] += 1
            else:
                c["skips"][reason] += 1
                day_skip[day]["skips"] += 1
        elif ev == "cancel_scheduled":
            c["cancel_scheduled"] += 1
            if book_of(r) == "paper":
                c["orders"] += 1
                day_skip[day]["orders"] += 1
                c["fill_orders"].append((r["order_id"], ticker_of(r)))
            oid = r.get("order_id")
            # GG-754: epoch-gated like the cancel-failure check - a pre-fix orphan must not re-trip the turn-off forever
            if oid not in outcome and ts >= CANCEL_PATH_FIX_EPOCH and (now - ts).total_seconds() > NO_OUTCOME_S:
                c["no_outcome"] += 1
        elif ev in ("cancel_ok", "cancel_failed", "cancel_already_terminal"):
            if ev == "cancel_failed" and _historical_404_terminal(r, fills_for):
                ev = "cancel_already_terminal"  # GG-596: pre-fix rows; the order was already terminal
            if ev == "cancel_failed" and (r.get("venue_transient") or is_venue_transient(r.get("response"))):
                ev = "cancel_failed_venue"  # ADR-0072 addendum 2026-10-15: exchange 5xx / network, reported apart
            c[ev] += 1
            if ts >= CANCEL_PATH_FIX_EPOCH:
                day_cancel[day][ev] += 1
    cell_out = []
    for (book, sport, arm), c in sorted(cells.items()):
        if c["first_ts"] is None:
            continue
        rows = [fills_for(oid, tk) for oid, tk in c["fill_orders"]] if fills_for else []
        nonfill = [x for x in rows if x.get("fills", 0) <= 0 and "nf_won" in x]
        nf_wins = sum(1 for x in nonfill if x["nf_won"])
        filled = [x for x in rows if x.get("fills", 0) > 0]
        settled = [x for x in filled if x.get("settled") and x.get("price") is not None]
        wins = sum(1 for x in settled if x.get("won"))
        attempts = c["cancel_ok"] + c["cancel_failed"]
        days = max((now - c["first_ts"]).total_seconds() / 86400.0, 1.0)
        per_week = len(filled) / days * 7.0 if fills_for else None
        cell_out.append({
            "book": book, "sport": sport, "arm": arm,
            "orders": c["orders"], "rejected": c["rejected"],
            "skips_by_reason": dict(c["skips"]), "control_arm_skips": c["control_skips"],
            "cancels": {"scheduled": c["cancel_scheduled"], "ok": c["cancel_ok"], "failed": c["cancel_failed"],
                        "failed_venue_transient": c["cancel_failed_venue"],
                        "already_terminal": c["cancel_already_terminal"],
                        "no_outcome_over_15m": c["no_outcome"]},
            "cancel_success_rate": (c["cancel_ok"] / attempts) if attempts else None,
            "fills": len(filled) if fills_for else None,
            "fills_settled": len(settled) if fills_for else None,
            "win_rate_on_fills": (wins / len(settled)) if settled else None,
            "settle_minus_price_on_fills": (sum((1.0 if x["won"] else 0.0) - x["price"] for x in settled) / len(settled)) if settled else None,
            "non_fills_resolved": len(nonfill),
            "win_rate_on_non_fills": (nf_wins / len(nonfill)) if nonfill else None,
            "fills_per_week": per_week,
            "projected_fills_8wk": None if per_week is None else per_week * WEEKS,
            "on_pace_for_550_in_8wk": None if per_week is None else per_week * WEEKS >= JUDGED_N,
            "observed_days": round(days, 2),
            "control_note": ("SHADOW control arm (W69.1/GG-586): model-mid order, no cancel; treatment-minus-control formable from fills"
                             if book == "shadow" else "paper control orders are not in this log"),
        })
    # ---- ADR-0072 turn-off conditions ----
    trips: list[dict] = []
    checks: dict[str, Any] = {}
    last_days = sorted(day_cancel)[-2:]
    worst = max(((d, day_cancel[d]["cancel_failed"] / max(1, day_cancel[d]["cancel_ok"] + day_cancel[d]["cancel_failed"]))
                 for d in last_days), key=lambda x: x[1], default=(None, 0.0))
    checks["cancel_fail_rate_gt_10pct_in_a_day"] = {"worst_day": worst[0], "rate": worst[1],
                                                  "venue_transient_failures_by_day": {d: day_cancel[d]["cancel_failed_venue"] for d in last_days},
                                                  "scope": "our-side failures only; exchange 5xx / network errors reported in their own line", "epoch": CANCEL_PATH_FIX_EPOCH.isoformat(),
                                                  "tripped": worst[1] > CANCEL_FAIL_MAX}
    sk_days = [d for d in sorted(day_skip) if d != now.date().isoformat()][-3:]
    rates = [day_skip[d]["skips"] / (day_skip[d]["skips"] + day_skip[d]["orders"]) for d in sk_days
             if day_skip[d]["skips"] + day_skip[d]["orders"] > 0]
    checks["skip_rate_gt_90pct_three_days"] = {"days": sk_days, "rates": rates,
                                               "scope": "policy skips only; listing skips reported separately",
                                               "listing_skips_by_day": {d: day_skip[d]["listing_skips"] for d in sk_days},
                                               "tripped": len(sk_days) == 3 and len(rates) == 3 and all(x > SKIP_RATE_MAX for x in rates)}
    n_no = sum(x["cancels"]["no_outcome_over_15m"] for x in cell_out)
    checks["scheduled_cancel_no_outcome_15m"] = {"count": n_no, "tripped": n_no > 0}
    checks["treatment_markout_30m_worse_than_control"] = {"tripped": False, "status": "NOT_EVALUABLE",
                                                          "reason": "no markout/candle collection in this job"}
    checks["order_on_non_demo_host"] = {"tripped": False, "status": "GUARDED",
                                        "reason": "demo_host_ok() refuses at the order path; this job reads demo only"}
    for name, ch in checks.items():
        if ch.get("tripped"):
            trips.append({"condition": name, **ch})
    return {"generated_utc": now.isoformat(), "judged_n_per_arm": JUDGED_N, "weeks": WEEKS,
            "since": since.isoformat() if since else None, "cells": cell_out, "turn_off_checks": checks, "tripped": trips, "note": window_note}


def _override_for(env_path: Path) -> Path:
    return env_path.with_name("demo_fill.override.env")


def switches_active(env_path: Path = ENV_FILE) -> bool:
    """Effective state: a switch is active when the tracked config sets it AND the untracked
    override (W69.1/GG-587) does not set that key to ``off``."""
    if not env_path.exists():
        return False
    ov = {}
    try:
        for l in _override_for(env_path).read_text().splitlines():
            if "=" in l and not l.lstrip().startswith("#"):
                k, v = l.split("=", 1)
                ov[k.strip()] = v.strip()
    except OSError:
        pass
    return any(l.split("=", 1)[0].strip() in SWITCH_KEYS and not l.lstrip().startswith("#")
               and ov.get(l.split("=", 1)[0].strip(), "x") != "off"
               for l in env_path.read_text().splitlines() if "=" in l)


def turn_off(trips: list[dict], now: datetime, env_path: Path = ENV_FILE, log: Optional[Callable[[dict], None]] = None) -> bool:
    """W69.1/GG-587: write ``<switch>=off`` to the untracked, git-ignored deploy/demo_fill.override.env,
    which the policy reads last. The tracked demo_fill.env is NOT touched, so the VPS tree stays clean and
    vps_deploy.sh's dirty-tree guard never trips. Idempotent. Returns True if it changed the override."""
    if not trips or not switches_active(env_path):
        return False
    why = ",".join(t["condition"] for t in trips)
    atomic_write_text(
        _override_for(env_path),
        f"# TURNED OFF {now.isoformat()} by demo_fill_forward_report ({why}). Delete this file to re-enable.\n"
        + "".join(f"{k}=off\n" for k in SWITCH_KEYS))
    if log:
        log({"event": "turn_off", "conditions": [t["condition"] for t in trips], "env_file": str(_override_for(env_path))})
    return True


def summary_line(rep: dict) -> str:
    parts = []
    for c in rep["cells"]:
        f = "n/a" if c["fills"] is None else str(c["fills"])
        s = "n/a" if c["settle_minus_price_on_fills"] is None else f"{c['settle_minus_price_on_fills']:+.2f}"
        parts.append(f"{c['book']}/{c['sport']}: orders={c['orders']} fills={f} s-p={s}")
    t = [x["condition"] for x in rep["tripped"]]
    return ("FORWARD-TEST (ADR-0072) " + rep["generated_utc"][:16] + "Z | " + ("; ".join(parts) or "no events yet")
            + " | turn-off: " + ("TRIPPED " + ",".join(t) if t else "none tripped"))


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=None)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--env-file", default=str(ENV_FILE))
    ap.add_argument("--no-fills", action="store_true", help="skip demo API reads (log-only counts)")
    ap.add_argument("--since", default=None, help="ISO ts; read-back window (e.g. the cancel-path re-arm epoch)")
    ap.add_argument("--no-act", action="store_true", help="report only; never edit the switch config")
    a = ap.parse_args(argv)
    os.environ["BOT_ENV"] = "paper"  # demo only; .env must not flip the host
    from prediction_market_bot.c5_execution import demo_fill_policy as pol
    now = datetime.now(timezone.utc)
    events = load_events(Path(a.log) if a.log else REPO / pol.DEFAULT_LOG)
    outp = Path(a.out)
    cache_p = outp.with_name("demo_fill_forward_cache.json")
    cache: dict = {}
    try:
        cache = json.loads(cache_p.read_text())
    except (OSError, ValueError):
        pass
    fills_for = None
    note = ""
    if not a.no_fills:
        try:
            from prediction_market_bot import t4_fill_status as tf
            tf._load_dotenv_if_needed(REPO / ".env")
            os.environ["BOT_ENV"] = "paper"
            from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
            from prediction_market_bot.c5_execution.shadow_flat_stake import demo_host_ok
            client = KalshiMarketClient.from_env()
            if not demo_host_ok():
                note = "fills skipped: host is not demo"
            elif not client.has_signing_key():
                note = "fills skipped: no signing key"
            else:
                fills_for = lambda oid, tk: lookup_fill(client, oid, tk, cache)  # noqa: E731
        except Exception as e:  # noqa: BLE001 - report must still be written from the log
            note = f"fills skipped: {type(e).__name__}"
    since = datetime.fromisoformat(a.since.replace("Z", "+00:00")) if a.since else None
    rep = build_report(events, now, fills_for, note, since)
    if since is not None:
        a.no_act = True  # a windowed read-back never edits the switch config
    if not a.no_act and turn_off(rep["tripped"], now, Path(a.env_file), pol.append_log):
        rep["switches_turned_off"] = True
    rep["switches_active"] = switches_active(Path(a.env_file))
    outp.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(outp, json.dumps(rep, indent=2, default=str) + "\n")
    try:
        atomic_write_text(cache_p, json.dumps(cache))
    except OSError:
        pass
    print(summary_line(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
