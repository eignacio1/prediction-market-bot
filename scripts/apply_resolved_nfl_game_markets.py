#!/usr/bin/env python3
"""
T-527 game-market resolver -- the NFL analogue of scripts/apply_resolved_hits.py
(the existing MLB player-prop resolver, NOT modified here; this script sits
beside it).

Iterates open NFL game-market positions (NFL_MONEYLINE / NFL_SPREAD /
NFL_GAME_TOTAL / NFL_TEAM_TOTAL) in the paper portfolio, fetches each game's
final score from ESPN (c1_signal_ingestion/nfl_espn_results.py), derives
actual_stat/stat_label via c5_execution/game_market_settlement.py (T-527's
derivation module), and calls PaperTrader.settle_position() -- the same
sport-agnostic settlement primitive MLB uses (paper_trader.py ~line 915),
unmodified (GG-034 file-lock invariant).

A position whose settlement would be ambiguous under settle_position()'s
boolean `actual_stat >= threshold` model (a moneyline exact tie, or an exact
push on a spread/total/team-total) is REFUSED, not guessed -- see
check_settlement_ambiguity() and game_market_settlement.py's module
docstring for the Kalshi rule sourcing (NFLGAME.pdf's Tie provision).

Dry-run by default; --apply required to write. Backs up the portfolio file
before writing, exactly like apply_resolved_hits.py.

Usage:
    BOT_ENV=paper PYTHONPATH=src python3 scripts/apply_resolved_nfl_game_markets.py [--apply]

T-527 scope note: per explicit task instruction, this script is NOT run
against any real position in this block -- it is built and unit-tested
(tests/test_apply_resolved_nfl_game_markets.py) against a synthetic
portfolio only. Wiring it to a live NFL portfolio is a separate, later
task (21.1) -- no such portfolio exists yet, so PORTFOLIO_PATH below points
at a file that does not currently exist on disk.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("BOT_ENV", "paper")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c1_signal_ingestion.nfl_espn_results import (  # noqa: E402
    NFLGameResult,
    fetch_nfl_final_score,
)
from prediction_market_bot.c5_execution.game_market_settlement import (  # noqa: E402
    SettlementAmbiguityError,
    check_settlement_ambiguity,
    derive_actual_stat,
)
from prediction_market_bot.c5_execution.market_type_registry import MarketType  # noqa: E402
from prediction_market_bot.c5_execution.paper_trader import PaperTrader  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

SESSION_ID = f"NFL-GAME-RESOLVE-{uuid.uuid4().hex[:8].upper()}"

LOG_DIR = Path(os.environ.get("LOG_DIR", str(_SRC_ROOT / "logs")))
# No NFL portfolio exists yet -- T-527 builds the resolution path only (see
# module docstring). This mirrors run_resolve_mlb.py's paper_portfolio_mlb.json
# naming convention for the day a live NFL portfolio is wired up (21.1).
PORTFOLIO_PATH = Path(
    os.environ.get("NFL_PORTFOLIO_PATH", str(LOG_DIR / "paper_portfolio_nfl.json"))
)

_GAME_MARKET_TYPES = frozenset(
    {
        MarketType.NFL_MONEYLINE,
        MarketType.NFL_SPREAD,
        MarketType.NFL_GAME_TOTAL,
        MarketType.NFL_TEAM_TOTAL,
    }
)
_GAME_MARKET_TYPE_VALUES = frozenset(mt.value for mt in _GAME_MARKET_TYPES)

# Kalshi's NFL team-code alphabet (32 teams), confirmed against ESPN's own
# abbreviations for every code cross-checked in T-527. Needed to split an
# event ticker's concatenated two-team segment (e.g. "CHITEN" -> "CHI"+"TEN",
# "GBDAL" -> "GB"+"DAL") unambiguously, since codes are 2 or 3 letters with
# no separator between them.
_NFL_TEAM_CODES = frozenset(
    {
        "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
        "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
        "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG",
        "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WSH",
    }
)

_EVENT_DATE_PREFIX_LEN = 7  # "26AUG29": 2-digit year + 3-letter month + 2-digit day


def parse_event_teams(ticker: str) -> tuple[str, str]:
    """Extract the two team codes from a Kalshi event ticker's middle
    segment, e.g. "KXNFLGAME-26AUG29CHITEN-CHI" -> ("CHI", "TEN").

    The middle segment is a 7-char date code followed by the two team codes
    concatenated with no separator. Order is NOT guaranteed home-first or
    away-first -- T-527 found real tickers with both orderings -- so this
    returns an unordered pair; callers that need home/away must try both
    orderings against the actual game data (see resolve_score_either_order).

    Raises ValueError if the ticker doesn't have exactly 3 hyphen-segments,
    the event segment is too short, or no split of the post-date remainder
    matches two known team codes.
    """
    parts = ticker.split("-")
    if len(parts) != 3:
        raise ValueError(f"ticker {ticker!r} does not have 3 hyphen-segments")
    event_segment = parts[1]
    if len(event_segment) <= _EVENT_DATE_PREFIX_LEN:
        raise ValueError(
            f"ticker {ticker!r} event segment {event_segment!r} too short "
            f"to hold a date prefix plus two team codes"
        )
    teams_concat = event_segment[_EVENT_DATE_PREFIX_LEN:]
    for split_at in range(1, len(teams_concat)):
        a, b = teams_concat[:split_at], teams_concat[split_at:]
        if a in _NFL_TEAM_CODES and b in _NFL_TEAM_CODES:
            return a, b
    raise ValueError(
        f"ticker {ticker!r}: could not split {teams_concat!r} into two "
        f"known NFL team codes"
    )


def resolve_score_either_order(
    game_date: str, team_a: str, team_b: str
) -> NFLGameResult | None:
    """Try fetch_nfl_final_score() with both (team_a, team_b) home/away
    orderings, since parse_event_teams() cannot determine which team is
    home from the ticker alone. Returns the first non-None NFLGameResult
    (fetch_nfl_final_score's own home/away fields are authoritative,
    sourced from ESPN directly), or None if neither ordering matches a
    final game on that date."""
    result = fetch_nfl_final_score(game_date, team_a, team_b)
    if result is not None:
        return result
    return fetch_nfl_final_score(game_date, team_b, team_a)


def _backup_portfolio(path: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_name(f"{path.stem}.pre_resolve_{ts}{path.suffix}")
    shutil.copy2(path, backup_path)
    return backup_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    print(f"Portfolio path: {PORTFOLIO_PATH}")
    print(f"Session ID:     {SESSION_ID}")
    print(f"Mode:           {'APPLY (will write)' if args.apply else 'DRY RUN (no writes)'}")

    if not PORTFOLIO_PATH.exists():
        print(f"\nNo portfolio file at {PORTFOLIO_PATH} -- nothing to resolve.")
        return

    if args.apply:
        backup_path = _backup_portfolio(PORTFOLIO_PATH)
        print(f"Backup written: {backup_path}")

    logger = AuditLogger(LOG_DIR / "audit_nfl.jsonl", min_severity="INFO")
    trader = PaperTrader(PORTFOLIO_PATH, logger)

    open_positions = [
        p
        for p in trader.get_state().get("open_positions", [])
        if p.get("market_type") in _GAME_MARKET_TYPE_VALUES and p.get("status") == "OPEN"
    ]
    print(f"{len(open_positions)} open NFL game-market position(s) found.\n")

    settled: list[dict] = []
    refused: list[str] = []
    unresolved: list[str] = []

    for pos in open_positions:
        position_id = pos["position_id"]
        ticker = pos["kalshi_ticker"]
        market_type = MarketType(pos["market_type"])
        game_date = pos["game_date"]
        threshold = pos["kalshi_threshold"]

        try:
            team_a, team_b = parse_event_teams(ticker)
        except ValueError as exc:
            print(f"  {position_id}  {ticker}  -> SKIP (ticker parse failed: {exc})")
            unresolved.append(position_id)
            continue

        game_result = resolve_score_either_order(game_date, team_a, team_b)
        if game_result is None:
            print(f"  {position_id}  {ticker}  {game_date}  -> not final yet / not found, skipping")
            unresolved.append(position_id)
            continue

        try:
            actual_stat, stat_label = derive_actual_stat(
                market_type,
                ticker,
                home_team_code=game_result.home_team_code,
                away_team_code=game_result.away_team_code,
                home_score=game_result.home_score,
                away_score=game_result.away_score,
            )
            check_settlement_ambiguity(market_type, actual_stat, threshold)
        except SettlementAmbiguityError as exc:
            print(f"  {position_id}  {ticker}  -> REFUSED (ambiguous settlement): {exc}")
            refused.append(position_id)
            continue
        except ValueError as exc:
            print(f"  {position_id}  {ticker}  -> SKIP (derivation error: {exc})")
            unresolved.append(position_id)
            continue

        print(
            f"  {position_id}  {ticker}  actual_stat={actual_stat} ({stat_label})  "
            f"threshold={threshold}"
        )
        if args.apply:
            ok, closed_pos = trader.settle_position(
                position_id=position_id,
                actual_stat=actual_stat,
                stat_label=stat_label,
                session_id=SESSION_ID,
            )
            if ok and closed_pos:
                pnl = closed_pos.get("pnl", 0.0)
                outcome = closed_pos.get("outcome", "?")
                print(f"    -> settled: outcome={outcome} pnl={pnl:+.2f}")
                settled.append(closed_pos)
            else:
                print(f"    -> settle_position() returned ok={ok} (already settled or not found)")

    print("\n--- Summary ---")
    print(f"Open NFL game-market positions: {len(open_positions)}")
    print(f"Settled this run:               {len(settled)}")
    print(f"Refused (ambiguous):            {len(refused)}")
    print(f"Unresolved (no final score / parse error): {len(unresolved)}")
    if not args.apply:
        print("\nDRY RUN -- no writes made. Re-run with --apply to settle these positions.")


if __name__ == "__main__":
    main()
