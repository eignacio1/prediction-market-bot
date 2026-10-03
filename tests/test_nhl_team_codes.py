"""GG-403 / 51.2: Kalshi uses 2-letter codes (SJ/TB/LA/NJ) that the 3+3 parsers silently dropped.
Tickers are real, from a read-only Kalshi pull on 2026-10-03."""
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from prediction_market_bot.c3_forecasting.nhl_pregame import TEAM_ALIASES, parse_ticker, split_team_codes

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("nhl_shadow_eval", ROOT / "scripts" / "nhl_shadow_eval.py")
ev = importlib.util.module_from_spec(spec)
sys.modules["nhl_shadow_eval"] = ev
spec.loader.exec_module(ev)

# (market ticker, away NHL abbrev, home NHL abbrev) -- every previously failing code appears.
REAL = [
    ("KXNHLGAME-26OCT08SJSTL-SJ", "SJS", "STL"), ("KXNHLGAME-26OCT08SJSTL-STL", "SJS", "STL"),
    ("KXNHLGAME-26OCT08MINTB-TB", "MIN", "TBL"), ("KXNHLGAME-26OCT06FLALA-LA", "FLA", "LAK"),
    ("KXNHLGAME-26OCT06UTANJ-NJ", "UTA", "NJD"), ("KXNHLGAME-26OCT03LASJ-LA", "LAK", "SJS"),
    ("KXNHLGAME-26OCT03NJNYI-NJ", "NJD", "NYI"), ("KXNHLGAME-26OCT03WSHTB-TB", "WSH", "TBL"),
    ("KXNHLGAME-26OCT01TBNYR-TB", "TBL", "NYR"), ("KXNHLGAME-26OCT01PHINJ-NJ", "PHI", "NJD"),
    ("KXNHLGAME-26SEP30LACOL-LA", "LAK", "COL"), ("KXNHLGAME-26SEP26ANALA-LA", "ANA", "LAK"),
    ("KXNHLGAME-26SEP23LAANA-LA", "LAK", "ANA"), ("KXNHLGAME-26SEP22TBNSH-TB", "TBL", "NSH"),
    ("KXNHLGAME-26SEP20NSHTB-NSH", "NSH", "TBL"), ("KXNHLGAME-26SEP20NYINJ-NJ", "NYI", "NJD"),
    ("KXNHLGAME-26SEP24NJNYR-NJ", "NJD", "NYR"), ("KXNHLGAME-26SEP26SJVGK-SJ", "SJS", "VGK"),
    ("KXNHLGAME-26SEP22VGKSJ-SJ", "VGK", "SJS"),
]


@pytest.mark.parametrize("ticker,away,home", REAL)
def test_real_tickers_parse_and_map_to_nhl_abbrevs(ticker, away, home):
    i = parse_ticker(ticker)
    assert i is not None and (i["away"], i["home"]) == (away, home)
    assert i["team"] in (away, home)
    d = ev.event_date_teams(ticker.rsplit("-", 1)[0])
    assert d is not None and d[1] == frozenset((away, home))


def test_two_letter_codes_in_spread_and_total_tickers():
    s = parse_ticker("KXNHLSPREAD-26OCT03LASJ-SJ3")
    assert (s["team"], s["strike"], s["away"], s["home"]) == ("SJS", 2.5, "LAK", "SJS")
    assert parse_ticker("KXNHLSPREAD-26OCT03NJNYI-NJ2")["team"] == "NJD"
    t = parse_ticker("KXNHLTOTAL-26OCT03WSHTB-6")
    assert (t["strike"], t["home"]) == (5.5, "TBL")


def test_three_letter_regression_and_garbage():
    assert parse_ticker("KXNHLGAME-26OCT08TORVGK-TOR")["home"] == "VGK"
    assert split_team_codes("ZZQQ") is None and split_team_codes("SJ") is None  # unevidenced 2-letter codes
    assert parse_ticker("KXNHLGAME-26OCT08SJSTL-XXX")["team"] == "XXX"  # unknown side is caught by forecast()
    assert parse_ticker("KXNHLGAME-26OCT08ZZQQ-ZZ") is None  # unevidenced 2-letter pair -> unparsed (and counted)


def test_alias_targets_are_the_nhl_data_abbrevs():
    assert TEAM_ALIASES == {"SJ": "SJS", "TB": "TBL", "LA": "LAK", "NJ": "NJD"}


def test_abstention_counters_name_every_drop():
    NOW = datetime(2026, 10, 3, 18, tzinfo=timezone.utc)  # 5h to start -> T2

    class Fc:
        sport, last_abstain = "NHL", None

        def forecast(self, t, as_of):
            self.last_abstain = "no_game_match"
            return None

    def m(tk, et, bid="0.50", ask="0.54"):
        return {"ticker": tk, "event_ticker": et, "yes_bid_dollars": bid, "yes_ask_dollars": ask,
                "occurrence_datetime": "2026-10-04T02:00:00Z"}

    mk = {"KXNHLGAME": [m("KXNHLGAME-26OCT03LASJ-LA", "KXNHLGAME-26OCT03LASJ"),
                        m("KXNHLGAME-26OCT03ZZQQ-ZZ", "KXNHLGAME-26OCT03ZZQQ"),
                        m("KXNHLGAME-26OCT03LASJ-SJ", "KXNHLGAME-26OCT03LASJ", bid="0", ask="0.5")]}
    c: dict = {}
    assert ev.evaluate(mk, Fc(), {}, NOW, "r", "sha", counters=c) == []
    assert c["markets_seen"] == 3
    assert c["ticker_unparsed_or_team_unmapped"] == 1
    assert c["forecast_none:no_game_match"] == 2  # the two quoted markets
    assert c["no_valid_quote"] == 1
