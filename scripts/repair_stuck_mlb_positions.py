#!/usr/bin/env python3
"""
T-422 out-of-band repair for the 22 aged_open T1/MAIN MLB positions
(diagnosed T-416/T-418, root-caused T-422). NOT part of the production
pipeline — a one-shot, manually invoked tool. Deliberately lives in
scripts/, not src/, per this session's hard scope fence (no production
code changes; every src/ edit is an epoch bump and a clean_n reset).

Root cause (T-422, corrects GG-161's "cron-window-correlated API
degradation" framing): run_resolve_mlb.py's fetch_actual_hits() always
tries gameType="P" (postseason) when gameType="R" finds no split for the
date. Mid-regular-season, "P" 406s deterministically (confirmed 5/5,
any time of day — MLB's Stats API has no postseason data to serve yet).
_fetch_mlb_hits()'s circuit-breaker failure/success counters are
module-level globals shared across the whole _resolve_pool() run, so
this guaranteed P failure interrupts the 3-consecutive-successes streak
needed to reset the breaker (GG-089/T-242) after almost every position,
tripping it partway through nearly every daily run. GG-084's own
documented Fastly-CDN datacenter-IP block ("can escalate over the course
of a run") is real and separate, but the pointless P call roughly
doubles the request volume feeding that escalation. Once tripped, the
breaker collapses retries to a single probe for the rest of the run
(rrm.py:190-191), so genuinely-resolvable positions (Julio Rodriguez's
3 of 4 dates) lose their retry margin and fail alongside the permanently
data-absent majority (Mechanism 1, T-416).

This script avoids the cascade entirely: it calls gameType="R" only
(never "P"), resets the breaker before starting, and runs at low volume
(22 positions, once) well outside the 06:30 UTC cron. It also fixes the
ESPN fallback's 403 (GG-163's exact mechanism, independently confirmed
here for run_resolve_mlb.py's own ESPN client, not just T4's): ESPN
blocks the literal "Mozilla/5.0" User-Agent that _ESPN_HEADERS sends;
dropping the header (bare requests default UA) returns 200. This script
monkeypatches that one constant in-process — it does not touch
run_resolve_mlb.py on disk.

Usage:
    BOT_ENV=paper PYTHONPATH=src python3 scripts/repair_stuck_mlb_positions.py --apply
Default (no --apply) is a dry run: fetches and reports what WOULD resolve,
writes nothing, and does not call settle_position().

UPDATE (same session, live VPS testing): the theory above (circuit-breaker
cascade from the "P" fallback) turned out to be necessary-but-incomplete.
Direct testing against the live datacenter IP found the ACTUAL blocker for
every one of Julio Rodriguez's 3 recoverable dates: `_is_game_final()`
(rrm.py:143-164) confirms finality via `GET /api/v1/schedule?gamePk=X` —
and THAT SPECIFIC QUERY SHAPE 406s deterministically (5/5) from the VPS's
datacenter IP, while the *exact same endpoint* queried as
`?sportId=1&date=YYYY-MM-DD` returns 200 with the same games (confirmed:
gamePk 822868, present and "Final" in the date-form response, 406 in the
gamePk-form request, both tested seconds apart from the same process).
The primary `gameLog` stats call (`/api/v1/people/{id}/stats`) is NOT
blocked at all right now — it returns 200 and the correct split. So the
real chain is: gameLog split found -> gamePk extracted -> finality check
406s -> `_is_game_final` swallows the exception (`except Exception: return
False`) -> `_fetch_mlb_hits` treats "confirmed not final" identically to
"actually not final yet" and returns None -> position stays stuck forever,
even though the game finished 200-800+ hours ago and the hit count was
sitting right there in the first response. This is GG-084's datacenter-IP
block (real, already documented) but scoped far more narrowly than "the
whole gameLog/schedule surface is unreliable" — it is one query-parameter
shape on one sub-endpoint. This script's `_finality_via_date_schedule()`
below re-implements the same finality check using the working query shape
instead of the broken one, and skips the "P" fallback (still genuinely
useless mid-season — confirmed separately, 5/5 406 regardless of query
shape) rather than relying on rrm._fetch_mlb_hits()/_is_game_final() as-is.

UPDATE 2 (same session): even with the query-shape fix above, running this
script's full 22-position batch FROM THE VPS degraded the PRIMARY gameLog
call itself to 100% 406 partway through the run — not just the finality
sub-call. This reproduces GG-084's documented "escalates over the course of
a run" behavior verbatim: the VPS's datacenter IP cannot reliably complete
a full-batch resolution run at any request volume approaching ~20+
sequential calls, regardless of query-shape correctness. The real fix is
architectural, not a further query patch: separate fetching (needs a
network) from applying (pure local file I/O). This script remains a valid
single-machine tool if ever run from a network NOT subject to GG-084 with
`--apply`, and is kept for its diagnostic value, but it was NOT what
actually produced the 5/22 result reported in
05_RESEARCH_EXPERIMENTS/T416_STUCK_POSITIONS_DIAGNOSIS.md. That result came
from running this same fetch logic (see `fetch_hits_unblocked_network.py`
in this directory) from a network unaffected by GG-084, writing a results
JSON, then applying it via `apply_resolved_hits.py` on the VPS with zero
further network calls. Reproduce the full repair via:

    # From a network NOT subject to GG-084 (i.e. NOT the VPS):
    python3 scripts/fetch_hits_unblocked_network.py stuck_positions.json resolved_hits.json
    # Then, ON the VPS, pure local apply (no network calls):
    BOT_ENV=paper PYTHONPATH=src python3 scripts/apply_resolved_hits.py resolved_hits.json --apply
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

os.environ.setdefault("BOT_ENV", "paper")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

import prediction_market_bot.run_resolve_mlb as rrm  # noqa: E402
from prediction_market_bot.c5_execution.paper_trader import PaperTrader  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

SESSION_ID = f"REPAIR-MLB-{uuid.uuid4().hex[:8].upper()}"
_DAY_SCHEDULE_CACHE: dict[str, dict[int, str]] = {}


def _finality_via_date_schedule(game_pk: int, game_date: str) -> bool:
    """Replaces rrm._is_game_final() with the working query shape.

    rrm._is_game_final() calls `/api/v1/schedule?gamePk=X`, which 406s
    deterministically from this VPS's datacenter IP (confirmed live, this
    session). `/api/v1/schedule?sportId=1&date=YYYY-MM-DD` hits the same
    endpoint, returns the same games, and is NOT blocked. Caches one
    day's response per game_date so a day with multiple stuck positions
    only fetches the schedule once.
    """
    if game_date not in _DAY_SCHEDULE_CACHE:
        states: dict[int, str] = {}
        try:
            resp = requests.get(
                f"{rrm._MLB_BASE_URL}/api/v1/schedule",
                params={"sportId": 1, "date": game_date},
                timeout=rrm._REQUEST_TIMEOUT_S,
            )
            resp.raise_for_status()
            data = resp.json()
            for d in data.get("dates", []):
                for g in d.get("games", []):
                    pk = g.get("gamePk")
                    if pk is not None:
                        states[pk] = g.get("status", {}).get("abstractGameState", "")
        except Exception as exc:
            print(f"  [FINALITY] date={game_date}: schedule fetch failed: "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr)
        _DAY_SCHEDULE_CACHE[game_date] = states
    return _DAY_SCHEDULE_CACHE[game_date].get(game_pk) == "Final"


def _fetch_hits_fixed(player_id: int, game_date: str) -> float | None:
    """Re-implements rrm._fetch_mlb_hits(game_type="R") with the finality
    check routed around the broken gamePk-query shape. Regular season only
    — gameType="P" is skipped entirely (confirmed separately: 406s 100% of
    the time mid-season, any query shape, not worth the round trip)."""
    year = int(game_date[:4])
    try:
        time.sleep(rrm._RATE_LIMIT_S)
        resp = requests.get(
            f"{rrm._MLB_BASE_URL}/api/v1/people/{player_id}/stats",
            params={"stats": "gameLog", "group": "hitting", "season": str(year), "gameType": "R"},
            timeout=rrm._REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
        stats_arr = data.get("stats", [])
        if not stats_arr:
            return None
        for split in stats_arr[0].get("splits", []):
            if split.get("date", "") == game_date:
                game_pk = split.get("game", {}).get("gamePk")
                if game_pk is None or not _finality_via_date_schedule(game_pk, game_date):
                    return None
                return float(split.get("stat", {}).get("hits", 0))
        return None
    except Exception as exc:
        print(f"  [MLB-API-FIXED] player_id={player_id} game_date={game_date}: "
              f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def _backup_portfolio(path: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_name(f"{path.stem}.pre_repair_{ts}{path.suffix}")
    shutil.copy2(path, backup_path)
    return backup_path


def _age_hours(game_date: str) -> float:
    try:
        game_dt = datetime.strptime(game_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - game_dt).total_seconds() / 3600
    except ValueError:
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually call settle_position() and write the portfolio file. "
             "Without this flag, only fetches and reports (no writes).",
    )
    args = parser.parse_args()

    portfolio_path = rrm.PORTFOLIO_PATH
    print(f"Portfolio path: {portfolio_path}")
    print(f"Session ID:     {SESSION_ID}")
    print(f"Mode:           {'APPLY (will write)' if args.apply else 'DRY RUN (no writes)'}")

    if args.apply:
        backup_path = _backup_portfolio(portfolio_path)
        print(f"Backup written: {backup_path}")

    # GG-163's fix direction applied locally: ESPN blocks the literal
    # "Mozilla/5.0" UA; dropping the header entirely (bare requests default
    # UA) returns 200. Confirmed by direct A/B curl/requests test this
    # session. Monkeypatch only affects this process's in-memory copy of the
    # constant — run_resolve_mlb.py on disk is untouched.
    rrm._ESPN_HEADERS = {}

    logger = AuditLogger(rrm.LOG_DIR / "audit_mlb.jsonl", min_severity="INFO")
    trader = PaperTrader(portfolio_path, logger)

    open_positions = trader.get_state().get("open_positions", [])
    stuck = [p for p in open_positions if p.get("aged_open") is True]

    print(f"\n{len(open_positions)} open position(s) total, {len(stuck)} tagged aged_open.\n")

    resolved_r = []
    resolved_espn = []
    still_stuck = []

    for pos in stuck:
        player_id = int(pos.get("player_id", 0))
        player_name = pos.get("player_name", "unknown")
        game_date = pos.get("game_date", "")
        threshold = pos.get("kalshi_threshold")
        position_id = pos.get("position_id", "")
        age_h = _age_hours(game_date)

        # Regular season only (gameType="P" is skipped entirely — confirmed
        # 406 100% of the time mid-season) with the finality check routed
        # around the broken gamePk-query shape (see _fetch_hits_fixed docstring).
        hits = _fetch_hits_fixed(player_id, game_date)
        source = "MLB-R"

        if hits is None:
            hits = rrm._espn_fetch_hits(player_name, game_date)
            source = "ESPN"

        if hits is None:
            print(f"  [STUCK]  {player_name:<20} {game_date}  thr={threshold}  "
                  f"{position_id}  age={age_h:.0f}h  — still no result (MLB-R and ESPN both empty)")
            still_stuck.append(pos)
            continue

        print(f"  [FOUND]  {player_name:<20} {game_date}  thr={threshold}  "
              f"{position_id}  age={age_h:.0f}h  hits={hits:.0f}  source={source}")

        if args.apply:
            ok, closed_pos = trader.settle_position(
                position_id=position_id,
                actual_stat=hits,
                stat_label="actual_hits",
                session_id=SESSION_ID,
            )
            if ok and closed_pos:
                pnl = closed_pos.get("pnl", 0.0)
                outcome = closed_pos.get("outcome", "?")
                print(f"           -> settled: outcome={outcome} pnl={pnl:+.2f}")
                (resolved_r if source == "MLB-R" else resolved_espn).append(closed_pos)
            else:
                print(f"           -> settle_position() returned ok={ok} "
                      f"(already settled or not found — no-op)")
        else:
            (resolved_r if source == "MLB-R" else resolved_espn).append(pos)

    total_resolved = len(resolved_r) + len(resolved_espn)
    print(f"\n--- Summary ---")
    print(f"Stuck positions examined: {len(stuck)}")
    print(f"Resolved via MLB-R:       {len(resolved_r)}")
    print(f"Resolved via ESPN:        {len(resolved_espn)}")
    print(f"Still stuck:              {len(still_stuck)}")
    print(f"Total resolved:           {total_resolved} / {len(stuck)}")
    if not args.apply:
        print("\nDRY RUN — no writes made. Re-run with --apply to settle these positions.")


if __name__ == "__main__":
    main()
