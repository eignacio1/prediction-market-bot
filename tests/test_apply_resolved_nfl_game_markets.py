"""
Tests for scripts/apply_resolved_nfl_game_markets.py (T-527).

No real PaperTrader, AuditLogger, or network call is ever exercised here --
PaperTrader/AuditLogger are mocked at the module level and
fetch_nfl_final_score is monkeypatched, so this file never touches a real
portfolio file or ESPN. This matches the task's explicit constraint: "Do not
settle a single real position in this block."

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
"""
from __future__ import annotations

import importlib.util
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
