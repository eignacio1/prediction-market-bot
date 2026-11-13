"""W113.2 Part A: NFL providers -- schedule/matchup snapshots, forecast PIT, no-line safety."""
from prediction_market_bot.decision_trees import filter_supply as fsup
from prediction_market_bot.nfl_engine import weather_forecast as wf
from prediction_market_bot.nfl_engine.filters import market_state_leaf
from prediction_market_bot.nfl_engine.providers import NflProviders

ROW = {"ts_utc": "2026-11-13T12:00:00+00:00", "event_ticker": "KXNFLGAME-26NOV15BUFNYJ", "sport": "NFL"}


class _Fc:
    def __init__(self, rec): self.rec = rec
    def get(self, sid, ko): return self.rec


def _prov(rec):
    return NflProviders(forecaster=_Fc(rec))


def test_week10_game_resolves_with_lines_and_matchup_from_prior_weeks_only():
    p = _prov(None)
    g = p.game(ROW)
    assert (g["home"], g["away"], int(g["week"])) == ("NYJ", "BUF", 10) and g["spread_line"] == -8.5
    th, ta, through = p.terms(ROW)
    assert through < "2026-11-13" and th is not None and ta is not None


def test_live_forecast_flows_to_a_weather_leaf_and_late_capture_is_refused():
    rec = {"kind": "live", "stadium_id": "NYC01", "kickoff_utc": "2026-11-15T18:00:00+00:00",
           "issued_utc": "2026-11-13T12:00:05+00:00", "lead_h": 53.9, "temp_f": 30.0, "wind_mph": 5.0, "precip_mm": 0.0}
    f, note = fsup.FilterSupply(nfl_providers=_prov(rec)).for_row(ROW)
    assert note is None and f["weather"] == "cold" and f["spread_bucket"] == "big"   # 5s after the row: inside the grace
    late = {**rec, "issued_utc": "2026-11-13T12:10:00+00:00"}
    f, note = fsup.FilterSupply(nfl_providers=_prov(late)).for_row(ROW)
    assert f is None and note.startswith("pit_violation")


def test_no_forecast_and_no_line_are_named_unknown_never_guessed():
    f, note = fsup.FilterSupply(nfl_providers=_prov(None)).for_row({**ROW, "event_ticker": "KXNFLGAME-26NOV15KCATL"})
    assert note is None and f["weather"] in ("unknown", "indoor")
    assert market_state_leaf(float("nan"), 44.0) == {"spread_bucket": "unknown", "total_bucket": "unknown"}


def test_forecast_lookup_is_point_in_time():
    caps = [{"stadium_id": "X", "kickoff_utc": "2026-11-15T18:00:00+00:00", "issued_utc": "2026-11-10T00:00:00+00:00", "v": 1},
            {"stadium_id": "X", "kickoff_utc": "2026-11-15T18:00:00+00:00", "issued_utc": "2026-11-14T00:00:00+00:00", "v": 2}]
    assert wf.latest_before(caps, "X", "2026-11-15T18:00:00Z", "2026-11-12T00:00:00Z")["v"] == 1
    assert wf.latest_before(caps, "X", "2026-11-15T18:00:00Z", "2026-11-09T00:00:00Z") is None


def test_split_leaves_ride_the_adapter_for_tested_entries_only():
    from prediction_market_bot.nfl_engine.filters import TESTED_SPLITS, nfl_split_filters, split_side_leaf, split_total_leaf
    f, note = fsup.FilterSupply(nfl_providers=_prov(None)).for_row(ROW)
    assert note is None
    for n in TESTED_SPLITS:
        assert f[n + "@total"] in ("high", "mid", "low", "unknown") and f[n + "@side"] in ("home_edge", "away_edge", "neutral", "unknown")
    assert "three_wr_rate@total" not in f                                   # thin entry: not exported
    assert split_total_leaf(0.9, 0.8) == "high" and split_total_leaf(None, 0.5) == "unknown"
    assert split_side_leaf("rush_stuff_rate_defence", 0.9, 0.1) == "home_edge"       # higher is better for the unit
    assert split_side_leaf("rush_stuffed_rate_offence", 0.9, 0.1) == "away_edge"     # lower is better for the unit
    assert nfl_split_filters({}, {}, keep={"third_down_success"}) == {"third_down_success@total": "unknown",
                                                                      "third_down_success@side": "unknown"}
