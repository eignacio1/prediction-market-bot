"""
Tests for scripts/apply_resolved_nfl_game_markets.py (T-527, T-535).

No real PaperTrader, AuditLogger, or network call is ever exercised here --
PaperTrader/AuditLogger are mocked at the module level and
fetch_nfl_final_score is monkeypatched, so this file never touches a real
(production) portfolio file or ESPN. This matches the task's explicit
constraint: "Do not settle a single real position in this block." The one
exception is the idempotency block at the bottom (T-535/Deliverable 2): it
uses a REAL PaperTrader/AuditLogger, because double-settlement can only be
disproven against the real ledger-mutation path in settle_position(), not a
MagicMock that returns the same canned tuple regardless of ledger state --
but it still writes only to a pytest tmp_path, never to a real portfolio
file, and fetch_nfl_final_score is still monkeypatched there too (no network
call anywhere in this file).

Coverage:
  - parse_event_teams(): both team-code orderings seen in real tickers this
    build (home-first "CHITEN", away-first "GBDAL"); malformed tickers raise.
  - resolve_score_either_order(): falls back to the swapped ordering when the
    first attempt returns None.
  - main(): a resolvable moneyline position is settled only under --apply,
    never in dry-run; an unparseable ticker and a not-yet-final game are
    both left unresolved without calling settle_position(); a moneyline
    exact tie is refused (SettlementAmbiguityError) and never settled even
    under --apply; a missing portfolio file returns early without ever
    constructing a PaperTrader.
  - Idempotency (T-535): running the resolver twice --apply over the same
    real (tmp_path) portfolio file cannot double-settle -- the ledger's
    bytes are identical before and after the second pass.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

MODULE_PATH = Path(__file__).parent.parent / "scripts" / "apply_resolved_nfl_game_markets.py"
_spec = importlib.util.spec_from_file_location("apply_resolved_nfl_game_markets", MODULE_PATH)
resolver = importlib.util.module_from_spec(_spec)
sys.modules["apply_resolved_nfl_game_markets"] = resolver
_spec.loader.exec_module(resolver)

from prediction_market_bot.c1_signal_ingestion.nfl_espn_results import NFLGameResult  # noqa: E402


# ---------------------------------------------------------------------------
# parse_event_teams
# ---------------------------------------------------------------------------

def test_parse_event_teams_home_first_ticker():
    assert resolver.parse_event_teams("KXNFLGAME-26AUG29CHITEN-CHI") == ("CHI", "TEN")


def test_parse_event_teams_away_first_ticker():
    # Real T-527 finding: ordering is not consistently home-first.
    assert resolver.parse_event_teams("KXNFLGAME-25SEP28GBDAL-DAL") == ("GB", "DAL")


def test_parse_event_teams_wrong_segment_count_raises():
    with pytest.raises(ValueError, match="3 hyphen-segments"):
        resolver.parse_event_teams("KXNFLGAME-25SEP28GBDAL")


def test_parse_event_teams_unrecognized_codes_raise():
    with pytest.raises(ValueError, match="could not split"):
        resolver.parse_event_teams("KXNFLGAME-25SEP28ZZQQXX-DAL")


# ---------------------------------------------------------------------------
# resolve_score_either_order
# ---------------------------------------------------------------------------

def test_resolve_score_either_order_first_ordering_hits():
    fake_result = NFLGameResult("HOU", "TEN", 26.0, 0.0, "STATUS_FINAL")
    with patch.object(resolver, "fetch_nfl_final_score", return_value=fake_result) as mock_fetch:
        result = resolver.resolve_score_either_order("2025-09-28", "HOU", "TEN")
    assert result is fake_result
    mock_fetch.assert_called_once_with("2025-09-28", "HOU", "TEN")


def test_resolve_score_either_order_falls_back_to_swapped_ordering():
    fake_result = NFLGameResult("DAL", "GB", 40.0, 40.0, "STATUS_FINAL")
    with patch.object(
        resolver, "fetch_nfl_final_score", side_effect=[None, fake_result]
    ) as mock_fetch:
        result = resolver.resolve_score_either_order("2025-09-28", "GB", "DAL")
    assert result is fake_result
    assert mock_fetch.call_count == 2
    mock_fetch.assert_any_call("2025-09-28", "GB", "DAL")
    mock_fetch.assert_any_call("2025-09-28", "DAL", "GB")


def test_resolve_score_either_order_both_fail_returns_none():
    with patch.object(resolver, "fetch_nfl_final_score", return_value=None):
        assert resolver.resolve_score_either_order("2025-09-28", "GB", "DAL") is None


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def _moneyline_position(position_id="P1", ticker="KXNFLGAME-25SEP28HOUTEN-HOU"):
    return {
        "position_id": position_id,
        "kalshi_ticker": ticker,
        "market_type": "nfl_moneyline",
        "game_date": "2025-09-28",
        "kalshi_threshold": 0,
        "status": "OPEN",
    }


def _run_main(tmp_path, argv, open_positions, game_result, portfolio_exists=True):
    """Wire up a fake PaperTrader/AuditLogger/fetch_nfl_final_score and run main()."""
    portfolio_path = tmp_path / "paper_portfolio_nfl.json"
    if portfolio_exists:
        portfolio_path.write_text("{}")

    mock_trader = MagicMock()
    mock_trader.get_state.return_value = {"open_positions": open_positions}
    mock_trader.settle_position.return_value = (
        True,
        {"outcome": "YES", "pnl": 12.34},
    )
    mock_trader_cls = MagicMock(return_value=mock_trader)

    with patch.object(resolver, "PORTFOLIO_PATH", portfolio_path), \
         patch.object(resolver, "PaperTrader", mock_trader_cls), \
         patch.object(resolver, "AuditLogger", MagicMock()), \
         patch.object(resolver, "fetch_nfl_final_score", return_value=game_result), \
         patch.object(sys, "argv", ["apply_resolved_nfl_game_markets.py", *argv]):
        resolver.main()

    return mock_trader, mock_trader_cls


def test_main_dry_run_never_settles(tmp_path):
    game_result = NFLGameResult("HOU", "TEN", 26.0, 0.0, "STATUS_FINAL")
    mock_trader, _ = _run_main(tmp_path, [], [_moneyline_position()], game_result)
    mock_trader.settle_position.assert_not_called()


def test_main_apply_settles_resolvable_position(tmp_path):
    game_result = NFLGameResult("HOU", "TEN", 26.0, 0.0, "STATUS_FINAL")
    mock_trader, _ = _run_main(tmp_path, ["--apply"], [_moneyline_position()], game_result)
    mock_trader.settle_position.assert_called_once()
    _args, kwargs = mock_trader.settle_position.call_args
    assert kwargs["position_id"] == "P1"
    assert kwargs["actual_stat"] == 26.0
    assert kwargs["stat_label"] == "point_margin_for_HOU"
    # Backup made before writing.
    backups = list(tmp_path.glob("paper_portfolio_nfl.pre_resolve_*.json"))
    assert len(backups) == 1


def test_main_unparseable_ticker_left_unresolved(tmp_path):
    bad_pos = _moneyline_position(ticker="not-a-real-ticker-shape")
    game_result = NFLGameResult("HOU", "TEN", 26.0, 0.0, "STATUS_FINAL")
    mock_trader, _ = _run_main(tmp_path, ["--apply"], [bad_pos], game_result)
    mock_trader.settle_position.assert_not_called()


def test_main_game_not_final_left_unresolved(tmp_path):
    mock_trader, _ = _run_main(
        tmp_path, ["--apply"], [_moneyline_position()], game_result=None
    )
    mock_trader.settle_position.assert_not_called()


def test_main_moneyline_tie_refused_even_under_apply(tmp_path):
    tie_pos = _moneyline_position(ticker="KXNFLGAME-25SEP28GBDAL-DAL")
    tie_result = NFLGameResult("DAL", "GB", 40.0, 40.0, "STATUS_FINAL")
    mock_trader, _ = _run_main(tmp_path, ["--apply"], [tie_pos], tie_result)
    mock_trader.settle_position.assert_not_called()


def test_main_non_game_market_position_ignored(tmp_path):
    prop_pos = _moneyline_position()
    prop_pos["market_type"] = "mlb_player_prop_hits"
    game_result = NFLGameResult("HOU", "TEN", 26.0, 0.0, "STATUS_FINAL")
    mock_trader, _ = _run_main(tmp_path, ["--apply"], [prop_pos], game_result)
    mock_trader.settle_position.assert_not_called()


def test_main_missing_portfolio_file_returns_early(tmp_path):
    _mock_trader, mock_trader_cls = _run_main(
        tmp_path, [], [_moneyline_position()], game_result=None, portfolio_exists=False
    )
    mock_trader_cls.assert_not_called()


# ---------------------------------------------------------------------------
# Idempotency (T-535/Deliverable 2) -- REAL PaperTrader + AuditLogger, not
# mocks. "Idempotency is mandatory whatever else you build. Prove it with a
# test that runs the resolver twice over the same input and asserts the
# ledger is byte-identical after the second pass." Only fetch_nfl_final_score
# is monkeypatched (no network call); the portfolio file lives entirely under
# pytest's tmp_path -- never a real/production ledger.
# ---------------------------------------------------------------------------

from prediction_market_bot.c5_execution.paper_trader import PaperTrader  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402


def _seed_real_portfolio(portfolio_path: Path, open_positions: list[dict]) -> None:
    """Write a portfolio file matching PaperTrader._load_or_init()'s shape,
    seeded with real (non-mocked) open positions."""
    state = {
        "bankroll_usd": 1000.0,
        "initial_bankroll_usd": 1000.0,
        "total_realized_pnl": 0.0,
        "current_daily_loss": 0.0,
        "daily_loss_date": "2025-09-28",
        "open_positions": open_positions,
        "closed_positions": [],
        "rejected_positions": [],
        "created_at": "2025-09-28T00:00:00+00:00",
        "last_updated": "2025-09-28T00:00:00+00:00",
    }
    portfolio_path.write_text(json.dumps(state, indent=2))


def _real_moneyline_position(position_id="REAL-P1"):
    # Real completed 2025-09-28 game: HOU (home) 26 - TEN (away) 0 (live-
    # verified via ESPN this session). settle_position() requires these
    # exact fields on the position record (paper_trader.py settle_position()).
    return {
        "position_id": position_id,
        "kalshi_ticker": "KXNFLGAME-25SEP28HOUTEN-HOU",
        "market_type": "nfl_moneyline",
        "game_date": "2025-09-28",
        "kalshi_threshold": 0,
        "status": "OPEN",
        "direction": "YES",
        "size_usd": 25.0,
        "mid_price_at_entry": 0.70,
        "vig_at_entry": 0.03,
        "player_name": "HOU_vs_TEN_moneyline",
    }


def test_main_apply_twice_is_idempotent_byte_identical_ledger(tmp_path):
    portfolio_path = tmp_path / "paper_portfolio_nfl_idempotency.json"
    _seed_real_portfolio(portfolio_path, [_real_moneyline_position()])

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    game_result = NFLGameResult("HOU", "TEN", 26.0, 0.0, "STATUS_FINAL")

    with patch.object(resolver, "PORTFOLIO_PATH", portfolio_path), \
         patch.object(resolver, "LOG_DIR", log_dir), \
         patch.object(resolver, "fetch_nfl_final_score", return_value=game_result), \
         patch.object(sys, "argv", ["apply_resolved_nfl_game_markets.py", "--apply"]):
        resolver.main()

    bytes_after_first_run = portfolio_path.read_bytes()
    state_after_first_run = json.loads(bytes_after_first_run)
    assert state_after_first_run["open_positions"] == []
    assert len(state_after_first_run["closed_positions"]) == 1
    assert state_after_first_run["closed_positions"][0]["outcome"] == "WIN"

    with patch.object(resolver, "PORTFOLIO_PATH", portfolio_path), \
         patch.object(resolver, "LOG_DIR", log_dir), \
         patch.object(resolver, "fetch_nfl_final_score", return_value=game_result), \
         patch.object(sys, "argv", ["apply_resolved_nfl_game_markets.py", "--apply"]):
        resolver.main()

    bytes_after_second_run = portfolio_path.read_bytes()
    assert bytes_after_second_run == bytes_after_first_run, (
        "second --apply pass over an already-settled portfolio must not "
        "touch the ledger file at all: no OPEN game-market positions remain "
        "for it to find, so settle_position() (and therefore _save()) is "
        "never called a second time"
    )


def test_settle_position_is_itself_idempotent_real_trader(tmp_path):
    """Lower-level companion to the byte-identical main() test above: calling
    settle_position() a second time directly for an already-settled
    position_id is a documented no-op ("idempotent -- already settled is a
    no-op" per its own docstring) that returns before _save() is ever
    reached -- so it performs zero file writes, not merely a same-content
    rewrite."""
    portfolio_path = tmp_path / "paper_portfolio_nfl_settle_twice.json"
    _seed_real_portfolio(portfolio_path, [_real_moneyline_position(position_id="REAL-P2")])
    logger = AuditLogger(tmp_path / "logs" / "audit_nfl.jsonl", min_severity="INFO")
    trader = PaperTrader(portfolio_path, logger)

    ok1, closed1 = trader.settle_position(
        position_id="REAL-P2", actual_stat=26.0, stat_label="point_margin_for_HOU"
    )
    assert ok1 is True
    assert closed1["outcome"] == "WIN"
    bytes_after_first_settle = portfolio_path.read_bytes()

    ok2, closed2 = trader.settle_position(
        position_id="REAL-P2", actual_stat=26.0, stat_label="point_margin_for_HOU"
    )
    assert ok2 is True
    assert closed2 == {}  # documented no-op return for an already-settled id
    bytes_after_second_settle = portfolio_path.read_bytes()

    assert bytes_after_second_settle == bytes_after_first_settle
