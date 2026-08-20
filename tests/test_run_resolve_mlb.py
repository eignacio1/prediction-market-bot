"""T-472/GG-191: regression coverage for run_resolve_mlb.py's
_ticker_to_game_date wrapper. The underlying grammar (parse_ticker_date /
derive_game_date) is exhaustively tested in test_market_type_registry.py;
this file only confirms the wrapper's own contract -- delegate, and return
None (never raise, never fall back to a wall-clock value) on any parse
failure."""

import os

os.environ.setdefault("BOT_ENV", "paper")
os.environ.setdefault("BOT_C4_ACTIVE", "true")

import prediction_market_bot.run_resolve_mlb as runner


class TestTickerToGameDate:
    def test_valid_ticker_derives_date(self):
        assert runner._ticker_to_game_date(
            "KXMLBHIT-26AUG011610MIANYM-T1.5"
        ) == "2026-08-01"

    def test_malformed_tail_refuses(self):
        assert runner._ticker_to_game_date("KXMLBHIT-INVALID-TICKER") is None

    def test_unregistered_series_refuses(self):
        assert runner._ticker_to_game_date(
            "KXMLBUNKNOWNSERIES-26AUG011610MIANYM-T8.5"
        ) is None
