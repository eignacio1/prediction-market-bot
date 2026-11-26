"""W130.4: look-ahead and known-answer tests for the point-in-time NBA profile and archetype mixture (synthetic data)."""
import numpy as np, pandas as pd
from prediction_market_bot.pam import nba_pit_archetype as A, nba_pit_profile as P

def _games(extra_rows=None):
    rows = []
    for pid in range(1, 41):
        for k, day in enumerate(pd.date_range("2025-11-01", periods=10, freq="3D")):
            r = {c: 0.0 for c in P.COUNT_COLS}
            r.update(pid=pid, game_id=f"g{pid}_{k}", game_date=day, season=2026, position="",
                     poss_off=60.0, poss_def=60.0, minutes=30.0, fga=10.0, rim_fga=4.0, mid_fga=2.0, three_fga=4.0,
                     fta=2.0, tov=2.0, ast=3.0 + pid % 5, dreb=5.0 + pid % 7, oreb=1.0, dreb_chances=20.0,
                     oreb_chances=10.0, blk=pid % 3, stl=1.0, opp_fga_on=40.0, opp_rim_fga=10.0)
            rows.append(r)
    return pd.DataFrame(rows + (extra_rows or []))

def test_profile_excludes_as_of_day_and_later():
    g = _games()
    cut = pd.Timestamp("2025-11-13")  # a game day: the game ON the day must be excluded
    n_before = (g[g.pid == 1].game_date < cut).sum()
    assert P.profile_as_of(g, 2026, cut).loc[1, "gp"] == n_before

def test_future_game_cannot_change_past_profile():
    g = _games()
    poison = [{**{c: 0.0 for c in P.COUNT_COLS}, "pid": 1, "game_id": "late", "game_date": pd.Timestamp("2026-03-01"),
               "season": 2026, "position": "", "poss_off": 90.0, "poss_def": 90.0, "dreb": 99.0, "dreb_chances": 99.0}]
    a = P.profile_as_of(g, 2026, "2025-12-15")
    b = P.profile_as_of(pd.concat([g, pd.DataFrame(poison)], ignore_index=True), 2026, "2025-12-15")
    pd.testing.assert_frame_equal(a, b)

def test_known_answer_rates():
    g = _games()
    f = P.profile_as_of(g, 2026, "2026-01-01")
    r = f.loc[1]
    assert abs(r["dreb_per100"] - 100 * (5 + 1) / 60) < 1e-9 and abs(r["dreb_share"] - (6 / 20)) < 1e-9
    assert abs(r["usage_per100"] - 100 * (10 + 0.44 * 2 + 2) / 60) < 1e-9

def test_mixture_valid_and_fit_uses_only_given_frame():
    g = _games()
    f = P.profile_as_of(g, 2026, "2026-01-01")
    prm = A.fit(f)
    a = A.assign(f, prm)
    assert all(abs(sum(w.values()) - 1) < 1e-9 for w in a.weights)
    assert not set(A.UNBUILT) & {k for w in a.weights for k in w}
    assert prm["n_train"] == len(f)
    # a different fit frame gives different z-scoring, so the mixture depends on the fit set only
    prm2 = A.fit(f.assign(usage_per100=f.usage_per100 * 2))
    assert prm2["mu"]["usage_per100"] != prm["mu"]["usage_per100"]


def test_pit_store_known_at_blocks_future_snapshot():
    import datetime as dt
    from prediction_market_bot.pam.schema import ArchetypeWeight, Basis, Classifier, PamRecord
    from prediction_market_bot.pam.store import resolve_as_of
    def rec(d, until, arch):
        return PamRecord(record_id=f"x:{d}", sport="nba", player_id="7", archetypes=(ArchetypeWeight(arch, 1.0),), tier="mass",
                         classified_by=Classifier(kind="model", name="mass"), effective_from=dt.date.fromisoformat(d),
                         effective_until=until, recorded_at=dt.date.fromisoformat(d), basis=Basis())
    rs = [rec("2026-01-01", dt.date(2026, 2, 1), "PRF-4"), rec("2026-02-01", None, "PRF-9")]
    assert resolve_as_of(rs, "nba", "7", "2026-01-20", known_at="2026-01-20").archetypes[0].id == "PRF-4"
    assert resolve_as_of(rs, "nba", "7", "2026-01-20", known_at="2026-03-01").archetypes[0].id == "PRF-4"  # as_of governs
    assert resolve_as_of(rs, "nba", "7", "2026-02-10", known_at="2026-01-20") is None or \
        resolve_as_of(rs, "nba", "7", "2026-02-10", known_at="2026-01-20").archetypes[0].id == "PRF-4"


def test_archetype_arm_keeps_s_probability_and_logs_cell():
    import datetime as dt
    from prediction_market_bot.pregame_shadow import nba_engine_props_archetype_forecaster as AR
    assert AR.MODEL_ID != "nba_engine_v2_props_shrunk_w129_2" and len(AR.MODEL_SHA256) == 64
    f = AR.NBAEnginePropsArchetype.cell
    class Dummy:  # exercise cell() without a full engine
        lookup = staticmethod(lambda n, t, d: ("PRF-9", 0.8) if t == "OPP" else ("PRF-7", 0.6))
        def roster(self, t, d): return [(30.0, "A B", {})]
    out = f(Dummy(), {"team": "HOM", "home": "HOM", "away": "OPP", "game_date": "2027-01-05"}, "Z Z")
    assert out == (("player_arch", "PRF-7", 0.6), ("opp_anchor", "anchor", 0.0))
