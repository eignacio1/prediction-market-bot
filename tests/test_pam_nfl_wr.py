import datetime as dt

import pytest

from prediction_market_bot.pam import PamStore, pam_as_of
from prediction_market_bot.pam import nfl_wr_mass as m


def test_weights_sum_prune_and_fallback():
    w = m.weights({"WR-VERT": 0.5, "WR-YAC": 0.05, "WR-VOL": 0.3, "WR-MID": 0.15})
    assert abs(sum(w.values()) - 1) < 1e-9 and "WR-YAC" not in w and "WR-MID" not in w
    assert m.weights({"WR-VERT": 0, "WR-YAC": 0, "WR-VOL": 0, "WR-MID": 0}) == {"WR-MID": 1.0}


def test_committed_store_point_in_time():
    recs = PamStore().load("nfl")
    assert len(recs) > 200 and all(r.tier == "mass" and r.backdated for r in recs)
    for r in recs:
        season = int(r.basis.seasons[0])
        assert r.effective_from == dt.date(season + 1, 3, 1)  # takes effect only after the season it used
        assert abs(sum(a.weight for a in r.archetypes) - 1) < 1e-6
    one = next(r for r in recs if r.basis.seasons == ("2024",))
    gid = one.player_id
    assert pam_as_of("nfl", gid, dt.date(2025, 2, 28)) is None or pam_as_of("nfl", gid, dt.date(2025, 2, 28)).basis.seasons == ("2023",)
    assert pam_as_of("nfl", gid, dt.date(2025, 3, 1)).basis.seasons == ("2024",)  # positive control


def test_season_chain_supersedes():
    recs = PamStore().load("nfl")
    by = {r.record_id: r for r in recs}
    chained = [r for r in recs if r.supersedes]
    assert chained
    for r in chained:
        old = by[r.supersedes[0]]
        assert old.player_id == r.player_id and int(old.basis.seasons[0]) + 1 == int(r.basis.seasons[0])
