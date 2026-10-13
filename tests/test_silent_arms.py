"""W62.1 Part B: the silent-arm alarm fires on games-with-no-rows and stays quiet on off-days."""
import json
from datetime import datetime, timedelta, timezone

from prediction_market_bot.pregame_shadow.silent_arms import (
    SPECS, ArmInput, evaluate_arm, last_ts_in_files, silent_arms)

NOW = datetime(2026, 10, 8, 20, 0, tzinfo=timezone.utc)
H = lambda h: NOW - timedelta(hours=h)


def _arm(key="mlb_shadow", starts=(), last=None, note=""):
    return ArmInput(SPECS[key], None if starts is None else list(starts), last, note)


def test_games_but_no_rows_is_silent():
    r = evaluate_arm(_arm(starts=[H(5), H(2)], last=H(19)), NOW)
    assert r["status"] == "silent" and r["games_in_window"] == 2 and r["hours_silent"] == 19
    assert "SILENT" in r["text"] and "19h" in r["text"]


def test_games_and_recent_rows_is_ok():
    assert evaluate_arm(_arm(starts=[H(5)], last=H(1)), NOW)["status"] == "ok"


def test_off_day_is_not_an_alarm_even_with_old_rows():
    r = evaluate_arm(_arm(starts=[H(40)], last=H(60)), NOW)    # last game 40h ago, outside the 12h window
    assert r["status"] == "idle" and r["hours_silent"] is None


def test_no_schedule_at_all_off_season_is_idle():
    assert evaluate_arm(_arm(starts=[], last=None), NOW)["status"] == "idle"


def test_future_games_are_not_counted():
    assert evaluate_arm(_arm(starts=[NOW + timedelta(hours=3)], last=None), NOW)["status"] == "idle"


def test_row_just_before_window_counts_via_lead():
    # game at the window's left edge, served by a T3 row written 40 min before the window opened
    r = evaluate_arm(_arm(starts=[H(11.9)], last=H(12.7)), NOW)
    assert r["status"] == "ok"
    assert evaluate_arm(_arm(starts=[H(11.9)], last=H(13.5)), NOW)["status"] == "silent"


def test_never_any_rows_is_silent_with_plain_words():
    r = evaluate_arm(_arm(starts=[H(2)], last=None), NOW)
    assert r["status"] == "silent" and r["hours_silent"] is None and "no rows found" in r["text"]


def test_unreadable_schedule_is_unknown_not_red():
    r = evaluate_arm(_arm(starts=None, note="schedule: FileNotFoundError"), NOW)
    assert r["status"] == "unknown" and "cannot check" in r["text"]


def test_per_arm_window_t4_is_3h_t1_is_30h():
    assert evaluate_arm(_arm("t4_mlb", starts=[H(2)], last=H(4)), NOW)["status"] == "silent"
    assert evaluate_arm(_arm("t4_mlb", starts=[H(5)], last=H(9)), NOW)["status"] == "idle"
    assert evaluate_arm(_arm("t1_mlb", starts=[H(20)], last=H(25)), NOW)["status"] == "ok"
    assert evaluate_arm(_arm("t1_mlb", starts=[H(20)], last=H(40)), NOW)["status"] == "silent"


def test_rollup_lists_only_silent():
    out = silent_arms([_arm(starts=[H(2)], last=H(30)), _arm("nfl_shadow", starts=[], last=None),
                       _arm("nhl_shadow", starts=None)], NOW)
    assert [a["key"] for a in out["silent"]] == ["mlb_shadow"] and len(out["unknown"]) == 1


def test_last_ts_respects_until_bound(tmp_path):
    p = tmp_path / "MLB_X_T1.jsonl"
    p.write_text("\n".join(json.dumps({"ts_utc": t}) for t in
                           ["2026-10-08T01:43:00+00:00", "2026-10-09T06:07:00+00:00"]) + "\n")
    assert last_ts_in_files([p], until=NOW) == datetime(2026, 10, 8, 1, 43, tzinfo=timezone.utc)
    assert last_ts_in_files([p]) == datetime(2026, 10, 9, 6, 7, tzinfo=timezone.utc)


def test_w67_1_nba_player_points_is_its_own_arm(tmp_path):
    from prediction_market_bot.pregame_shadow import silent_arms as sa
    keys = [i.spec.key for i in sa.load_inputs(tmp_path)]
    assert "nba_player_points_shadow" in keys and "nba_shadow" in keys


class TestDataPrereqs:
    """GG-621 / W71.2: players_2026.json must exist with >1,000 games or EXP-039/040 starve silently."""

    def _write(self, tmp_path, n):
        import json
        p = tmp_path / "data" / "raw" / "nba"
        p.mkdir(parents=True)
        (p / "players_2026.json").write_text(json.dumps({"season": 2026, "games": {str(i): {} for i in range(n)}}))

    def test_missing(self, tmp_path):
        from prediction_market_bot.pregame_shadow.silent_arms import data_prereqs
        assert data_prereqs(tmp_path)[0]["status"] == "missing"

    def test_thin(self, tmp_path):
        from prediction_market_bot.pregame_shadow.silent_arms import data_prereqs
        self._write(tmp_path, 1000)
        assert data_prereqs(tmp_path)[0]["status"] == "thin"

    def test_ok(self, tmp_path):
        from prediction_market_bot.pregame_shadow.silent_arms import data_prereqs
        self._write(tmp_path, 1231)
        d = data_prereqs(tmp_path)[0]
        assert d["status"] == "ok" and d["rows"] == 1231

    def test_unreadable(self, tmp_path):
        from prediction_market_bot.pregame_shadow.silent_arms import data_prereqs
        self._write(tmp_path, 1)
        (tmp_path / "data/raw/nba/players_2026.json").write_text("{not json")
        assert data_prereqs(tmp_path)[0]["status"] == "unreadable"
