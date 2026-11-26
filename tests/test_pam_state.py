"""W129.4: PAM state tables. Look-ahead and trade-from-date contracts."""
import pytest

from prediction_market_bot.pam import (AvailabilityProfile, PamValidationError, PlayerState, StateStore,
                                       TraitReliability, team_as_of)


def ps(team, as_of, known, game, **kw):
    return PlayerState(sport="nba", player_id="p1", game_id=game, team=team, as_of_ts=as_of, known_at=known,
                       source="t", version="v1", **kw)


def test_row_known_after_decision_never_returned(tmp_path):
    st = StateStore(tmp_path)
    st.append([ps("AAA", "2025-01-01T20:00:00Z", "2025-01-01T20:00:00Z", "g1", teammates_out=1)])
    # a late-known correction written for the same decision time
    st.append([ps("AAA", "2025-01-01T20:00:00Z", "2025-01-02T09:00:00Z", "g1", teammates_out=4)])
    r = st.as_of("player_state", "nba", "p1", "2025-01-01T21:00:00Z")
    assert r.teammates_out == 1
    assert st.as_of("player_state", "nba", "p1", "2025-01-03T00:00:00Z").teammates_out == 4


def test_future_as_of_row_not_returned(tmp_path):
    st = StateStore(tmp_path)
    st.append([ps("AAA", "2025-01-05T20:00:00Z", "2025-01-05T20:00:00Z", "g9")])
    assert st.as_of("player_state", "nba", "p1", "2025-01-01T00:00:00Z", known_at="2030-01-01T00:00:00Z") is None


def test_trade_changes_team_from_its_date(tmp_path):
    st = StateStore(tmp_path)
    st.append([ps("AAA", "2025-01-01T20:00:00Z", "2025-01-01T20:00:00Z", "g1"),
               ps("BBB", "2025-02-01T20:00:00Z", "2025-02-01T20:00:00Z", "g2")])
    rows = st.load("nba", "player_state")
    assert team_as_of(rows, "p1", "2025-01-31T23:00:00Z") == "AAA"
    assert team_as_of(rows, "p1", "2025-02-01T21:00:00Z") == "BBB"
    assert team_as_of(rows, "p1", "2024-12-01T00:00:00Z") is None


def test_naive_timestamp_rejected():
    with pytest.raises(PamValidationError):
        ps("AAA", "2025-01-01T20:00:00", "2025-01-01T20:00:00", "g1")


def test_trait_row_visible_only_after_fit_known(tmp_path):
    st = StateStore(tmp_path)
    st.append([TraitReliability(sport="nba", stat="points", as_of_ts="2026-11-21T00:00:00Z",
                                known_at="2022-07-01T00:00:00Z", source="s", version="v1", r_split_half=0.9)])
    assert st.as_of("trait_reliability", "nba", "points", "2022-01-01T00:00:00Z") is None
    assert st.as_of("trait_reliability", "nba", "points", "2023-01-01T00:00:00Z").r_split_half == 0.9


def test_availability_validation_and_roundtrip(tmp_path):
    st = StateStore(tmp_path)
    a = AvailabilityProfile(sport="nba", player_id="p1", as_of_ts="2025-01-01T00:00:00Z",
                            known_at="2025-01-01T00:00:00Z", source="s", version="v1",
                            gp_by_season={"2024": [60, 82]})
    st.append([a])
    assert st.load("nba", "availability_profile")[0] == a
    with pytest.raises(PamValidationError):
        AvailabilityProfile(sport="nba", player_id="p1", as_of_ts="2025-01-01T00:00:00Z",
                            known_at="2025-01-01T00:00:00Z", source="s", version="v1", gp_by_season={"2024": [90, 82]})


def test_required_provenance():
    with pytest.raises(PamValidationError):
        PlayerState(sport="nba", player_id="p", game_id="g", team="A", as_of_ts="2025-01-01T00:00:00Z",
                    known_at="2025-01-01T00:00:00Z", source="", version="v")
