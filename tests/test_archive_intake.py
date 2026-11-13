from pathlib import Path

from prediction_market_bot.archive_intake.archive import Archive, table_family

FIX = Path(__file__).parent / "fixtures" / "archive_intake"


def test_table_family_drops_season_and_location():
    assert table_family("NBA.com Teams Opponent Shooting table (2025-26, Location=All, 5ft Range)") == "NBA.com Teams Opponent Shooting"
    assert table_family("MoneyPuck season summary teams.csv (2025, regular, situation=all)") == "MoneyPuck season summary teams.csv"


def test_split_frame_keeps_point_in_time_fields():
    a = Archive(FIX, "deadbeef")
    df = a.split_frame("nba", family="NBA.com Teams Opponent Shooting", season=2025)
    assert len(df) == 6
    assert {"as_of", "source", "source_time_utc", "archive_sha", "value_num", "verification"} <= set(df.columns)
    assert (df["archive_sha"] == "deadbeef").all()
    assert df["value_num"].notna().all()
    assert (df["verification"] == "REPORTED").all()


def test_snapshots_goalies():
    a = Archive(FIX, "deadbeef")
    df = a.snapshots("nhl", "goalies")
    assert len(df) == 2 and "snapshot_at_utc" in df.columns


def test_season_filter_excludes():
    assert Archive(FIX, "x").split_frame("nhl", season=1999).empty
