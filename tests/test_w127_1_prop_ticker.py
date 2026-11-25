"""W127.1 (GG-2009): NBA player-prop rows reach the factor adapters. The game parser knew only the four game series, so every
KXNBAPTS / REB / AST / 3PT row logged nba_event_ticker_unparsed and carried no factor filters (d6_trace_read 20261125T0039Z)."""
import pytest

from prediction_market_bot.decision_trees import filter_supply as fsup

TABLE = {"data_through_utc": "2026-06-30T00:00:00+00:00", "teams": {
    "CLE": {"clutch_offence_ppp": 0.9, "clutch_defence_ppp": 0.2}, "BOS": {"clutch_offence_ppp": 0.7, "clutch_defence_ppp": 0.8}}}


@pytest.mark.parametrize("series", ["KXNBAPTS", "KXNBAREB", "KXNBAAST", "KXNBA3PT"])
def test_prop_event_ticker_gives_the_same_teams_as_the_game_row(series):
    assert fsup.nba_game_teams(f"{series}-26NOV12BOSCLE") == ("BOS", "CLE")
    assert fsup.nba_game_teams("KXNBAGAME-26NOV12BOSCLE") == ("BOS", "CLE")


@pytest.mark.parametrize("bad", ["", None, "KXNBAPTS-26NOV12BOSXXX", "KXNBAPTS-26NOV12BOS", "KXNFLPTS-26NOV12BOSCLE", "KXNBAPTS-26NOV12BOSCLE-X"])
def test_unknown_forms_stay_unparsed(bad):
    assert fsup.nba_game_teams(bad) is None


def test_prop_row_now_gets_filters_not_unparsed():
    row = {"sport": "NBA", "event_ticker": "KXNBAPTS-26NOV12BOSCLE", "ts_utc": "2026-11-12T20:00:00+00:00"}
    f, note = fsup.nba_adapter(row, TABLE)
    assert note is None and f["clutch_defence_ppp@side"] == "home_edge"
    f2, note2 = fsup.nba_adapter({**row, "event_ticker": "KXNBAPTS-26NOV12BOSXXX"}, TABLE)
    assert f2 is None and note2 == "nba_event_ticker_unparsed"


def test_props_c2_default_on_with_env_off_switch():
    """W127.1: C2 forward logging is default ON (shadow only); PM_PROPS_C2=off turns it off."""
    import re
    from pathlib import Path
    src = Path(__file__).resolve().parents[1].joinpath("scripts", "run_nba_engine_props_shadow.py").read_text()
    m = re.search(r'os\.environ\.get\("PM_PROPS_C2", "(\w+)"\)\.lower\(\) (!=|==) "(\w+)"', src)
    assert m, "C2 switch not found"
    default, op, token = m.groups()
    def on(env):
        v = (env if env is not None else default).lower()
        return (v != token) if op == "!=" else (v == token)
    assert on(None) is True
    assert on("off") is False
    assert on("on") is True
