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


def test_w78_3_points_rows_do_not_mask_a_silent_nba_game_arm(tmp_path):
    """GG-892: nba_shadow globbed NBA_*.jsonl, which also matches NBA_NBA_PLAYER_POINTS_*; live points rows hid a dead game arm."""
    from datetime import datetime, timedelta, timezone
    from prediction_market_bot.pregame_shadow import silent_arms as sa
    led = tmp_path / "exp_output" / "PREGAME_SHADOW"
    led.mkdir(parents=True)
    ts = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    (led / "NBA_NBA_PLAYER_POINTS_T1_MULTI_DAY.jsonl").write_text(json.dumps({"ts_utc": ts}) + "\n")
    by = {i.spec.key: i for i in sa.load_inputs(tmp_path)}
    assert by["nba_shadow"].last_row_ts is None
    assert by["nba_player_points_shadow"].last_row_ts is not None
    (led / "NBA_NBA_MONEYLINE_T1_MULTI_DAY.jsonl").write_text(json.dumps({"ts_utc": ts}) + "\n")
    assert {i.spec.key: i for i in sa.load_inputs(tmp_path)}["nba_shadow"].last_row_ts is not None


# ── W79.1: T1-only arm (NFL QB challenger) + GG-892 glob sweep across every sport ─────────────────────────────

def _qb(starts, rows):
    return ArmInput(SPECS["nfl_qb_challenger"], list(starts), max(rows) if rows else None, "", list(rows))


def test_w79_1_t1_only_arm_served_in_its_window_is_ok_after_kickoff():
    """The live false alarm: SEA@DEN kicked off 10-16 00:15Z, QB rows ran 10-14 06:14Z..10-15 12:14Z (horizon 42.0->12.0),
    and at 10-16 06:08Z the old recency rule said 'silent 17.8h'. A T1-only arm is done 12h before kickoff."""
    start = datetime(2026, 10, 16, 0, 15, tzinfo=timezone.utc)
    rows = [datetime(2026, 10, 14, 6, 14, tzinfo=timezone.utc) + timedelta(hours=6 * i) for i in range(5)]
    now = datetime(2026, 10, 16, 6, 8, tzinfo=timezone.utc)
    r = evaluate_arm(_qb([start], rows), now)
    assert r["status"] == "ok" and r["games_in_window"] == 1


def test_w79_1_t1_only_arm_with_no_row_in_the_game_window_is_still_silent():
    start = datetime(2026, 10, 16, 0, 15, tzinfo=timezone.utc)
    stale = [datetime(2026, 10, 11, 6, 14, tzinfo=timezone.utc)]         # an older game's rows only
    r = evaluate_arm(_qb([start], stale), datetime(2026, 10, 16, 6, 8, tzinfo=timezone.utc))
    assert r["status"] == "silent" and "T1 window" in r["text"]
    assert evaluate_arm(_qb([start], []), datetime(2026, 10, 16, 6, 8, tzinfo=timezone.utc))["status"] == "silent"


def test_w79_1_t1_only_arm_one_served_one_unserved_game_is_silent():
    s1, s2 = datetime(2026, 10, 16, 0, 15, tzinfo=timezone.utc), datetime(2026, 10, 16, 3, 0, tzinfo=timezone.utc)
    rows = [s1 - timedelta(hours=20)]    # inside game 1's 12-48h window and game 2's too -> both served
    now = datetime(2026, 10, 16, 6, 0, tzinfo=timezone.utc)
    assert evaluate_arm(_qb([s1, s2], rows), now)["status"] == "ok"
    s3 = datetime(2026, 10, 16, 5, 0, tzinfo=timezone.utc)     # window opens 10-14 05:00 (04:00 with slack)
    r = evaluate_arm(_qb([s1, s3], [s1 - timedelta(hours=46)]), now)   # row 10-14 02:15: inside game 1's window only
    assert r["status"] == "silent" and r["text"].startswith("NFL QB challenger shadow is SILENT: 1 of 2")


def test_w79_1_frozen_arms_keep_the_recency_rule():
    assert SPECS["nfl_shadow"].t1_window_h is None and SPECS["mlb_shadow"].t1_window_h is None
    assert evaluate_arm(_arm("nfl_shadow", starts=[H(5)], last=H(19)), NOW)["status"] == "silent"


def test_w79_1_game_cells_mirror_the_runner_cells():
    """GAME_CELLS must equal each runner's CELLS, or a new cell silently falls out of (or into) its arm's alarm."""
    import ast
    from pathlib import Path
    from prediction_market_bot.pregame_shadow.silent_arms import GAME_CELLS
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    for sport, fn in (("MLB", "run_mlb_pregame_shadow.py"), ("NFL", "run_pregame_shadow.py"),
                      ("NBA", "run_nba_pregame_shadow.py")):
        for node in ast.parse((scripts / fn).read_text()).body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CELLS":
                assert sorted(n for n, _ in ast.literal_eval(node.value)) == sorted(GAME_CELLS[sport]), fn
                break
        else:
            raise AssertionError(f"no CELLS in {fn}")
    nhl = next(n for n in ast.parse((scripts / "nhl_shadow_eval.py").read_text()).body
               if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SERIES")
    assert sorted(ast.literal_eval(nhl.value).values()) == sorted(GAME_CELLS["NHL"])


def test_w79_1_other_arms_files_never_mask_a_silent_arm_in_any_sport(tmp_path):
    """GG-892 sweep: a fresh row in a foreign-arm file that shares the sport prefix must not count for the game arm."""
    from prediction_market_bot.pregame_shadow import silent_arms as sa
    ts = json.dumps({"ts_utc": (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()}) + "\n"
    led = tmp_path / "exp_output" / "PREGAME_SHADOW"
    nhl = tmp_path / "data" / "shadow" / "nhl"
    qb = tmp_path / "exp_output" / "PREGAME_SHADOW_NFLQB"
    pre = tmp_path / "exp_output" / "PREGAME_SHADOW_PRESEASON"
    for d in (led, nhl, qb, pre):
        d.mkdir(parents=True)
    foreign = [led / "MLB_MLB_PLAYER_HITS_T1.jsonl", led / "NFL_NFL_PLAYER_PASS_YDS_T1.jsonl",
               led / "NBA_NBA_PLAYER_POINTS_T1.jsonl", pre / "NBA_NBA_PLAYER_POINTS_T1.jsonl",
               nhl / "NHL_PLAYER_SHOTS_T1.jsonl", nhl / "run_log.jsonl",
               qb / "NFLQB_NFL_PLAYER_PASS_YDS_T1.jsonl"]
    for p in foreign:
        p.write_text(ts)
    by = {i.spec.key: i for i in sa.load_inputs(tmp_path)}
    for k in ("mlb_shadow", "nfl_shadow", "nfl_qb_challenger", "nhl_shadow", "nba_preseason_shadow", "nba_shadow"):
        assert by[k].last_row_ts is None, k
    for p, k, sport, pfx, d in ((led / "MLB_MLB_RUN_LINE_T2.jsonl", "mlb_shadow", "MLB", "MLB_", led),
                                (led / "NFL_NFL_TEAM_TOTAL_T3.jsonl", "nfl_shadow", "NFL", "NFL_", led),
                                (qb / "NFLQB_NFL_MONEYLINE_T1.jsonl", "nfl_qb_challenger", "NFL", "NFLQB_", qb),
                                (nhl / "NHL_PUCK_LINE_T1.jsonl", "nhl_shadow", "NHL", "", nhl),
                                (pre / "NBA_NBA_SPREAD_T1.jsonl", "nba_preseason_shadow", "NBA", "NBA_", pre)):
        p.write_text(ts)
        assert {i.spec.key: i for i in sa.load_inputs(tmp_path)}[k].last_row_ts is not None, k
