"""T-472/GG-191: regression coverage for run_paper_trade.py's (NBA)
_ticker_to_game_date wrapper. The underlying grammar (parse_ticker_date /
derive_game_date) is exhaustively tested in test_market_type_registry.py;
this file only confirms the wrapper's own contract -- delegate, and return
None (never raise, never fall back to a wall-clock value) on any parse
failure."""

import os

os.environ.setdefault("BOT_ENV", "paper")
os.environ.setdefault("BOT_C4_ACTIVE", "true")

import prediction_market_bot.run_paper_trade as runner


class TestTickerToGameDate:
    def test_valid_ticker_derives_date(self):
        assert runner._ticker_to_game_date(
            "KXNBAPTS-26JUN05NYKSAS-JT27.5"
        ) == "2026-06-05"

    def test_malformed_tail_refuses(self):
        assert runner._ticker_to_game_date("KXNBAPTS-INVALID-TICKER") is None

    def test_unregistered_series_refuses(self):
        assert runner._ticker_to_game_date(
            "KXNBAUNKNOWNSERIES-26JUN05NYKSAS-JT27.5"
        ) is None


class TestFrozenBookGuard:
    """GG-630 / W71.2: the old NBA paper book is frozen; main() must return before any
    venue client, trader or market fetch is touched."""

    def test_constant_is_frozen(self):
        assert runner.NBA_BOOK_FROZEN is True

    def test_main_returns_before_any_order_path(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setattr(runner, "LOG_DIR", tmp_path)

        def _boom(*a, **k):
            raise AssertionError("order path reached while book is frozen")

        monkeypatch.setattr(runner.KalshiMarketClient, "from_env", _boom)
        monkeypatch.setattr(runner, "PaperTrader", _boom)
        assert runner.main() is None
        out = capsys.readouterr().out
        assert out.count("FROZEN") == 1 and "GG-630" in out
        assert not (tmp_path / "paper_portfolio.json").exists()

    def test_guard_off_when_unfrozen(self, monkeypatch):
        monkeypatch.setattr(runner, "NBA_BOOK_FROZEN", False)
        assert runner._frozen_book_guard() is False
