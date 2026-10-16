"""Store-check tests (W78.4): injected faults must fire (positive controls)."""
import pandas as pd

from prediction_market_bot.c1_signal_ingestion import nba_store_checks as chk


def box(n=3_000, season=2020):
    return pd.DataFrame({"game_id": [f"00{i // 2}" for i in range(n)], "team_id": [i % 2 for i in range(n)], "season": season})


def run(df, name="team_box", season=2020, completed=True):
    rep = chk.Report()
    chk.check_frame(name, season, df, completed, rep)
    return rep.failures


def test_clean_frame_passes():
    assert run(box()) == []


def test_empty_and_truncated_fail_but_in_progress_season_may_be_short():
    assert run(box(0))
    assert any("minimum" in f for f in run(box(100)))
    assert run(box(100), completed=False) == []


def test_null_duplicate_missing_key_and_wrong_season_fire():
    df = box()
    assert run(df.assign(team_id=df.team_id.where(df.index > 0)))
    assert any("duplicate" in f for f in run(pd.concat([df, df.head(5)])))
    assert any("missing" in f for f in run(df.drop(columns="team_id")))
    assert any("season column" in f for f in run(df.assign(season=2019)))


def test_documented_duplicate_ceiling_allows_lineups_but_not_more():
    n = 500_000
    ok = pd.DataFrame({"game_id": ["g"] * n, "action_number": range(n), "season": 2020})
    dups = ok.copy(); dups.loc[:int(n * 0.05), "action_number"] = 0
    assert run(dups, "lineups") == []
    worse = ok.copy(); worse.loc[:int(n * 0.2), "action_number"] = 0
    assert any("duplicate" in f for f in run(worse, "lineups"))


def test_coverage_floor_fires():
    rep = chk.Report()
    chk.coverage_check("pbp", 2020, {"a", "b", "c", "d"}, {"a", "b", "c"}, rep)
    assert rep.failures and rep.coverage[0]["share"] == 0.75
    rep2 = chk.Report()
    chk.coverage_check("pbp", 2020, {"a"}, {"a"}, rep2)
    assert rep2.failures == []


def test_missing_file_for_completed_season_is_a_failure(tmp_path):
    rep = chk.run_checks(tmp_path, current=2027)
    assert rep.failures and any("missing from store" in f for f in rep.failures)
