"""Point-in-time + interface checks for the EXPLORATORY F8 unit-availability factor (W76.2)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "nfl_engine"))
import availability as A  # noqa: E402

A.HIST_MIN = 1   # tiny synthetic store: only two prior games
RATES = {"Out": 1.0, "Doubtful": 0.9, "Questionable": 0.3}


def _store(tmp_path, extra_future_snap=False):
    # AAA hosts BBB: w1 Sun 09-01, w2 Thu 09-05, w3 Sun 09-15, w4 Sun 09-22. Starter OL "Al Tackle" (AAA) played w1, w2.
    games = [("2024_01_BBB_AAA", 1, "Sunday", "2024-09-01"), ("2024_02_BBB_AAA", 2, "Thursday", "2024-09-05"),
             ("2024_03_BBB_AAA", 3, "Sunday", "2024-09-15"), ("2024_04_BBB_AAA", 4, "Sunday", "2024-09-22")]
    sched = pd.DataFrame([dict(game_id=g, season=2024, game_type="REG", week=w, weekday=d, gameday=day, gametime="13:00",
                               home_team="AAA", away_team="BBB", home_score=20, away_score=17) for g, w, d, day in games])
    raw = tmp_path / "exp_output" / "NFL_EVENTS" / "raw"
    (raw / "snaps").mkdir(parents=True, exist_ok=True); (raw / "injuries").mkdir(parents=True, exist_ok=True)
    rows = [dict(game_id=g, season=2024, game_type="REG", week=w, player="Al Tackle", position="T", team="AAA",
                 offense_snaps=70.0, offense_pct=1.0, defense_snaps=0.0, defense_pct=0.0)
            for g, w in (("2024_01_BBB_AAA", 1), ("2024_02_BBB_AAA", 2))]
    if extra_future_snap:   # a week-4 row must never feed week 3's starter share
        rows.append(dict(game_id="2024_04_BBB_AAA", season=2024, game_type="REG", week=4, player="Al Tackle", position="T", team="AAA",
                         offense_snaps=1.0, offense_pct=0.01, defense_snaps=0.0, defense_pct=0.0))
    pd.DataFrame(rows).to_parquet(raw / "snaps" / "snaps_2024.parquet")
    pd.DataFrame([dict(season=2024.0, game_type="REG", team="AAA", week=w, full_name="Al Tackle", report_status="Out",
                       date_modified=pd.Timestamp("2024-09-01", tz="UTC")) for w in (2, 3)]
                 + [dict(season=2024.0, game_type="REG", team="BBB", week=3, full_name="Bo Other", report_status=None,
                         date_modified=pd.Timestamp("2024-09-01", tz="UTC"))]).to_parquet(raw / "injuries" / "injuries_2024.parquet")
    return sched


def test_thursday_week_of_report_is_not_used_and_sunday_is(tmp_path):
    sched = _store(tmp_path)
    flags, tg, pit = A.build_flags(tmp_path, sched, [2024])
    lost = A.lost_table(flags, tg, RATES)
    assert np.isnan(lost.loc[("2024_02_BBB_AAA", "AAA")]).all()           # Thursday: week-of report excluded by the contract
    assert lost.loc[("2024_03_BBB_AAA", "AAA"), "OL"] > 0.9               # Sunday: final report usable, starter share ~1
    assert np.isnan(lost.loc[("2024_04_BBB_AAA", "AAA")]).all()           # no report row that week -> None, not 0
    used = flags[flags.usable]
    wk = used.merge(tg[["game_id", "team", "week"]], on=["game_id", "team"]).assign(season=2024)
    for gid in used.game_id.unique():
        pit.assert_no_leak(wk[wk.game_id == gid][["season", "week"]], "weekly", gid)


def test_future_snaps_never_enter_starter_share(tmp_path):
    base = A.build_flags(tmp_path, _store(tmp_path), [2024])[0]
    fut = A.build_flags(tmp_path, _store(tmp_path, extra_future_snap=True), [2024])[0]
    a = base[base.game_id == "2024_03_BBB_AAA"].share.to_numpy()
    b = fut[fut.game_id == "2024_03_BBB_AAA"].share.to_numpy()
    assert len(a) == 1 and len(a) == len(b) and np.allclose(a, b)


def test_factor_returns_none_without_usable_report_and_signs(tmp_path):
    sched = _store(tmp_path)
    flags, tg, _ = A.build_flags(tmp_path, sched, [2024])
    lost = A.lost_table(flags, tg, RATES)
    f = A.AvailabilityFactor(lost, sched.rename(columns={"home_team": "home", "away_team": "away"}),
                             coef={"OL": -1.0, "SK": 0, "DL": 0, "CB": 0, "BK": 0}, center={})
    assert f.points(pd.Timestamp("2024-09-05", tz="UTC"), "AAA", "BBB") is None
    assert f.points(pd.Timestamp("2024-09-15", tz="UTC"), "AAA", "BBB") < -0.9   # AAA's tackle out -> AAA scores less
    assert f.points(pd.Timestamp("2024-09-15", tz="UTC"), "BBB", "AAA") == 0.0   # opposing offense unaffected
    assert f.points(pd.Timestamp("2024-09-15", tz="UTC"), "ZZZ", "BBB") is None
