#!/usr/bin/env python3
"""T-573 Deliverable 1b: exclude the lookup-key/ticker-normalization explanation
for the 731 NOT_RETRIEVABLE T4M-PROJ rows, BEFORE trusting any retention-ceiling number.

Two parts:
  A) Confirmed-row ticker sanity check: for a sample of CONFIRMED-FILLED rows
     (order_id retrieves via GET /portfolio/orders/{id}), does that order's own
     "ticker" field match the ledger's kalshi_ticker for the same position_id,
     character-for-character? If confirmed-real rows' tickers match cleanly,
     the ledger's kalshi_ticker field is a trustworthy key in general -- a
     necessary (not sufficient) precondition for trusting ticker-based
     unreachability findings on the 731.

  B) Alternate-key probe on a sample of NOT_RETRIEVABLE rows: for rows whose
     single-order lookup (by id) AND ticker-filtered listing both come back
     empty, try:
       - event-level query: GET /portfolio/orders?event_ticker=<event-ticker>
         (ticker minus the final "-<SIDE><THRESH>" selector suffix)
       - series-level query: GET /portfolio/orders?series_ticker=KXMLBHIT
         combined with a tight ts window around game_date, scanned for ANY
         order regardless of ticker
       - a raw date-bounded order listing with NO ticker/series filter at all,
         same ts window, to catch a ticker string that doesn't parse into any
         of the above (e.g. a normalization mismatch broad enough that no
         substring of it is a valid key)

If ANY unreachable row resolves under an alternate key, STOP -- this script
prints a loud banner and the caller (session) must halt the census and report
the collision rather than proceeding to Deliverable 1/2.

Read-only. Never submits/cancels/modifies. authenticated=True on every call
(T-556: _get() defaults to authenticated=False -> resolves to PRODUCTION
regardless of BOT_ENV -- always pass explicitly).

Run ON THE VPS (credentials only live there):
    cd /opt/prediction-market-bot
    PYTHONPATH=src python3 /tmp/t573_lookup_key_exclusion.py \
        --portfolio logs/paper_portfolio_mlb_t4.json \
        --out /tmp/t573_lookup_key_exclusion_results.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1] if "__file__" in dir() else Path(".")
sys.path.insert(0, str(REPO_ROOT / "src"))

from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient  # noqa: E402
from prediction_market_bot import logic_epoch as le  # noqa: E402


def load_t4mproj_clean_closed(portfolio_path: Path) -> dict:
    with open(portfolio_path) as f:
        portfolio = json.load(f)
    closed = portfolio.get("closed_positions", [])
    rows = {
        p["position_id"]: p
        for p in closed
        if p.get("band") == "T4M-PROJ" and le.is_clean_for_band(p.get("logic_epoch"), "T4M-PROJ")
    }
    return rows


def event_ticker_from(ticker: str) -> str | None:
    """KXMLBHIT-26JUL311420NYYCHC-CHCABREGMAN3-1 -> KXMLBHIT-26JUL311420NYYCHC"""
    parts = ticker.split("-")
    if len(parts) < 2:
        return None
    return "-".join(parts[:2])


def series_ticker_from(ticker: str) -> str | None:
    parts = ticker.split("-")
    return parts[0] if parts else None


def game_date_window(game_date: str) -> tuple[int, int]:
    """Wide +/- 1 day window as Unix epoch seconds (int) -- the API rejects
    RFC3339 strings for min_ts/max_ts with HTTP 400 ("strconv.ParseInt" on the
    raw string), confirmed empirically against the live endpoint."""
    d = datetime.strptime(game_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo = d - timedelta(days=1)
    hi = d + timedelta(days=2)
    return int(lo.timestamp()), int(hi.timestamp())


def part_a_confirmed_ticker_check(client: KalshiMarketClient, filled_results: list[dict], portfolio_by_pid: dict) -> list[dict]:
    out = []
    for r in filled_results:
        pid = r["position_id"]
        order_id = r["kalshi_order_id"]
        row = portfolio_by_pid.get(pid, {})
        ledger_ticker = row.get("kalshi_ticker")
        ok, data = client._get(f"/portfolio/orders/{order_id}", authenticated=True)
        order = None
        if ok and isinstance(data, dict):
            order = data.get("order", data) if isinstance(data.get("order", data), dict) else None
        kalshi_ticker = order.get("ticker") if order else None
        match = (ledger_ticker is not None and kalshi_ticker is not None and ledger_ticker == kalshi_ticker)
        out.append({
            "position_id": pid,
            "kalshi_order_id": order_id,
            "ledger_kalshi_ticker": ledger_ticker,
            "kalshi_returned_ticker": kalshi_ticker,
            "exact_match": match,
        })
        time.sleep(0.15)
    return out


def part_b_alternate_key_probe(client: KalshiMarketClient, nr_sample: list[dict], portfolio_by_pid: dict) -> list[dict]:
    out = []
    for r in nr_sample:
        pid = r["position_id"]
        row = portfolio_by_pid.get(pid, {})
        ticker = row.get("kalshi_ticker")
        game_date = r.get("game_date")
        entry = {"position_id": pid, "kalshi_order_id": r.get("kalshi_order_id"), "ticker": ticker, "game_date": game_date}

        if not ticker:
            entry["note"] = "no ticker on ledger row -- cannot probe"
            out.append(entry)
            continue

        def _tickers_for_this_position(orders):
            """Only orders whose OWN ticker field exactly equals this position's ledger
            ticker count as resolving this position -- an event/series/window query
            returns every sibling market's orders too (other players, other thresholds,
            same game), and that sibling traffic is not evidence about THIS row."""
            return [o for o in orders if isinstance(o, dict) and o.get("ticker") == ticker]

        event_ticker = event_ticker_from(ticker)
        ok, data = client._get("/portfolio/orders", {"event_ticker": event_ticker}, authenticated=True)
        orders = data.get("orders", []) if ok and isinstance(data, dict) else []
        n_event_total = len(orders) if ok else None
        n_event_match = len(_tickers_for_this_position(orders)) if ok else None
        entry["event_ticker"] = event_ticker
        entry["event_level_orders_found_TOTAL"] = n_event_total
        entry["event_level_orders_MATCHING_THIS_TICKER"] = n_event_match
        time.sleep(0.15)

        series_ticker = series_ticker_from(ticker)
        lo, hi = game_date_window(game_date) if game_date else (None, None)
        params = {"series_ticker": series_ticker}
        if lo and hi:
            params["min_ts"] = lo
            params["max_ts"] = hi
        ok, data = client._get("/portfolio/orders", params, authenticated=True)
        orders = data.get("orders", []) if ok and isinstance(data, dict) else []
        n_series_total = len(orders) if ok else None
        n_series_match = len(_tickers_for_this_position(orders)) if ok else None
        entry["series_ticker"] = series_ticker
        entry["series_window_orders_found_TOTAL"] = n_series_total
        entry["series_window_orders_MATCHING_THIS_TICKER"] = n_series_match
        time.sleep(0.15)

        if lo and hi:
            ok, data = client._get("/portfolio/orders", {"min_ts": lo, "max_ts": hi}, authenticated=True)
            orders = data.get("orders", []) if ok and isinstance(data, dict) else []
            n_nofilter_total = len(orders) if ok else None
            n_nofilter_match = len(_tickers_for_this_position(orders)) if ok else None
            entry["nofilter_window_orders_found_TOTAL"] = n_nofilter_total
            entry["nofilter_window_orders_MATCHING_THIS_TICKER"] = n_nofilter_match
            time.sleep(0.15)
        else:
            entry["nofilter_window_orders_found_TOTAL"] = None
            entry["nofilter_window_orders_MATCHING_THIS_TICKER"] = None

        resolved = any(
            isinstance(entry.get(k), int) and entry[k] > 0
            for k in ("event_level_orders_MATCHING_THIS_TICKER", "series_window_orders_MATCHING_THIS_TICKER", "nofilter_window_orders_MATCHING_THIS_TICKER")
        )
        entry["RESOLVED_UNDER_ALTERNATE_KEY"] = resolved
        out.append(entry)
        print(f"  {pid} {game_date} event_total={entry['event_level_orders_found_TOTAL']} event_match={entry['event_level_orders_MATCHING_THIS_TICKER']} series_total={entry['series_window_orders_found_TOTAL']} series_match={entry['series_window_orders_MATCHING_THIS_TICKER']} nofilter_total={entry['nofilter_window_orders_found_TOTAL']} nofilter_match={entry['nofilter_window_orders_MATCHING_THIS_TICKER']} RESOLVED={resolved}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--portfolio", required=True, type=Path)
    ap.add_argument("--verification-results", required=True, type=Path,
                     help="t571_kalshi_verification_results.json (has FILLED/NOT_RETRIEVABLE verdicts)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--nr-sample-per-date", type=int, default=3)
    args = ap.parse_args()

    client = KalshiMarketClient.from_env()
    if not client.has_signing_key():
        print("ERROR: No RSA signing key loaded. Set VENUE_PRIVATE_KEY_PATH.", file=sys.stderr)
        sys.exit(1)

    portfolio_by_pid = load_t4mproj_clean_closed(args.portfolio)
    verif = json.load(open(args.verification_results))
    results = verif["results"]

    filled = [r for r in results if r["verdict"] == "FILLED"]
    nr = [r for r in results if r["verdict"] == "NOT_RETRIEVABLE"]

    print(f"=== PART A: confirmed-ticker check on {len(filled)} FILLED rows ===")
    part_a = part_a_confirmed_ticker_check(client, filled, portfolio_by_pid)
    n_match = sum(1 for x in part_a if x["exact_match"])
    n_checkable = sum(1 for x in part_a if x["ledger_kalshi_ticker"] and x["kalshi_returned_ticker"])
    print(f"PART A: {n_match}/{n_checkable} confirmed-FILLED rows' ledger ticker == Kalshi-returned ticker exactly ({len(part_a)} total attempted)")

    from collections import defaultdict
    nr_by_date = defaultdict(list)
    for r in nr:
        nr_by_date[r["game_date"]].append(r)
    sample = []
    for date, rows in sorted(nr_by_date.items()):
        sample.extend(rows[:args.nr_sample_per_date])

    print(f"\n=== PART B: alternate-key probe on {len(sample)} NOT_RETRIEVABLE rows across {len(nr_by_date)} dates ===")
    part_b = part_b_alternate_key_probe(client, sample, portfolio_by_pid)
    n_resolved = sum(1 for x in part_b if x.get("RESOLVED_UNDER_ALTERNATE_KEY"))

    out = {
        "part_a_confirmed_ticker_check": {
            "n_match": n_match,
            "n_checkable": n_checkable,
            "n_total": len(part_a),
            "rows": part_a,
        },
        "part_b_alternate_key_probe": {
            "n_sampled": len(sample),
            "n_dates": len(nr_by_date),
            "n_resolved_under_alternate_key": n_resolved,
            "rows": part_b,
        },
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, default=str)

    print(f"\nwrote {args.out}")
    if n_resolved > 0:
        print("!" * 70)
        print(f"!!! STOP: {n_resolved} unreachable row(s) RESOLVED under an alternate key.")
        print("!!! The 731 ceiling is measuring a lookup-key bug, not retention.")
        print("!!! Halt the census. GG-300's headline is provisional.")
        print("!" * 70)
    else:
        print(f"No unreachable rows resolved under alternate keys ({n_resolved}/{len(sample)}). "
              f"Lookup-key explanation NOT supported by this sample -- proceeding is warranted, "
              f"subject to sample-size caveats stated in the report.")


if __name__ == "__main__":
    main()
