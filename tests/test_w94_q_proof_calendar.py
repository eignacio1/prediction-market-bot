"""W94.Q Part B: known-answer tests for the proof-calendar projection maths."""
from datetime import date

import scripts.proof_calendar as pc


def test_constant_rate_known_answer():
    # NBA 2026-27 season is active; 2/day, need 20 -> exactly the 10th active day after today (Nov 2 is day 1).
    today = date(2026, 11, 1)
    assert pc.walk(20, 2.0, "NBA", today) == date(2026, 11, 11)


def test_offseason_gap_resumes_next_season():
    # MLB paused after 2026-11-01: need 10 at 1/day from 2026-11-02 first accrues on opening day 2027-03-25.
    d = pc.walk(10, 1.0, "MLB", date(2026, 11, 2))
    assert d == date(2027, 4, 3)


def test_zero_rate_none_and_note():
    assert pc.walk(5, 0.0, "NBA", date(2026, 11, 1)) is None
    r = pc.project(5, 0, 14, "NBA", date(2026, 11, 1))
    assert r["point"] is None and "no accrual" in r["note"]


def test_interval_brackets_point():
    r = pc.project(100, 28, 14, "NBA", date(2026, 11, 1))
    assert r["lo"] <= r["point"] <= r["hi"]
    assert r["rate"] == 2.0


def test_trailing_rate_counts_only_active_days():
    # MLB window 2026-11-02..: all 14 trailing days inactive -> 0 active days, never a zero-rate penalty.
    k, active = pc.trailing_rate(["2026-10-31"], "MLB", date(2026, 11, 20))
    assert (k, active) == (0, 0)
    # NBA, today 2026-11-08: window 11-01..11-07 plus 10-25..10-31 (season opened 10-20) -> 14 active days.
    k, active = pc.trailing_rate(["2026-11-05", "2026-11-05", "2026-11-06"], "NBA", date(2026, 11, 8))
    assert (k, active) == (3, 14)


def test_reached_need():
    assert pc.project(0, 5, 14, "NBA", date(2026, 11, 1))["note"] == "reached"


def test_render_known_blob():
    blob = {"generated": "2026-11-01T00:00:00Z", "archive_games_per_day": {},
            "cells": [{"cell": "x", "sport": "NBA", "band": "T1", "market_type": "ML", "rows": 10, "judged_n": 20,
                       "settled_games": 20, "first_look_n": 40, "status_text": "", "projection": {"date": "2027-01-01"},
                       "settle_dates": ["2026-10-30"] * 14}]}
    from pathlib import Path
    out = pc.render(blob, Path(pc.REPO))
    assert "| x |" in out and "PROOF CALENDAR" in out


def test_render_counts_form_matches_list_form():
    from pathlib import Path
    base = {"cell": "x", "sport": "NBA", "band": "T1", "market_type": "ML", "rows": 10, "judged_n": 20,
            "settled_games": 20, "first_look_n": 40, "status_text": "", "projection": {"date": "2027-01-01"}}
    mk = lambda sd: {"generated": "2026-11-01T00:00:00Z", "archive_games_per_day": {}, "cells": [base | {"settle_dates": sd}]}
    a = pc.render(mk(["2026-10-30"] * 9 + ["2026-10-29"] * 5), Path(pc.REPO))
    b = pc.render(mk({"2026-10-30": 9, "2026-10-29": 5}), Path(pc.REPO))
    assert a == b


def _cell(**kw):
    base = {"cell": "NFL.x.T1", "sport": "NFL", "band": "T1", "market_type": "TOTAL", "rows": 100, "judged_n": 60,
            "first_look_n": 60, "status_text": "JUDGED", "projection": {}, "settle_dates": {"2026-10-30": 14}, "verdict": None}
    return base | kw


def test_losing_look_closes_the_fade_arm_not_the_cell():
    rows = pc.engine_rows({"cells": [_cell(verdict="RULED_OUT", looks=[60, 150])]}, date(2026, 11, 3), "m")
    assert rows[0]["proj"] == "FADE ARM CLOSED (routed)" and not rows[0]["proj"].startswith("CLOSED")
    assert "stays SHADOW" in rows[0]["note"] and "routed" in rows[0]["second_state"]


def test_second_look_state_and_judged_left():
    rows = pc.engine_rows({"cells": [_cell(verdict="SHADOW", looks=[60, 150])]}, date(2026, 11, 3), "m")
    assert rows[0]["second"].startswith("n=150 (90 left):")


def test_single_look_cell_says_none_pre_registered():
    rows = pc.engine_rows({"cells": [_cell(looks=[60])]}, date(2026, 11, 3), "m")
    assert rows[0]["second"] == "none pre-registered"


def test_retired_cell10_closed_in_static_rows_and_render():
    rows = {r["id"]: r for r in pc.static_rows({}, date(2026, 11, 3))}
    assert rows["EXP-042 cell 10"]["proj"].startswith("CLOSED") and "RETIRED" in rows["EXP-042 cell 10"]["note"]
    assert not rows["EXP-042 cell 9"]["proj"].startswith("CLOSED") and not rows["EXP-042 cell 11"]["proj"].startswith("CLOSED")
    assert all("second" in r for r in rows.values())


# ---- W101.2: NFLQB season mapping + aggregate mode (B-039 / GG-1720) ----
def test_nflqb_uses_nfl_season():
    assert pc.season_sport("NFLQB") == "NFL"
    assert pc.is_active("NFLQB", date(2026, 11, 8)) == pc.is_active("NFL", date(2026, 11, 8))
    assert pc.is_active("NFLQB", date(2026, 11, 8))


def _blob():
    cell = {"cell": "NFLQB_NFL_MONEYLINE_T1", "sport": "NFLQB", "market_type": "MONEYLINE", "band": "T1",
            "rows": 528, "judged_n": 47, "settled_games": 47, "first_look_n": 60, "looks": [60, 150],
            "settle_dates": {"2026-10-26": 5, "2026-11-02": 6}, "projection": {"date": "2026-11-13"}}
    return {"generated": "2026-11-05", "cells": [cell], "archive_games_per_day": {}}


def test_aggregate_record_shape_and_second_state():
    rows = pc.aggregate(_blob(), pc.REPO)
    r = next(x for x in rows if x["id"] == "NFLQB_NFL_MONEYLINE_T1")
    assert set(r) == set(pc.AGG_KEYS)
    assert r["rows_n"] == 528 and r["settled_games"] == 47
    assert "second look n=150" in r["second_state"]
    ids = [x["id"] for x in rows]
    assert "EXP-045" in ids


def test_exp045_is_dated_look():
    r = next(x for x in pc.aggregate(_blob(), pc.REPO) if x["id"] == "EXP-045")
    assert r["first_look"] == "2027-01-12"
    assert "337" in r["second_state"]


def test_nba_second_state_flags_gg529_without_defining_it():
    b = _blob()
    b["cells"] = [{"cell": "NBA_X_T1", "sport": "NBA", "market_type": "PLAYER_POINTS", "band": "T1", "rows": 1,
                   "judged_n": 0, "first_look_n": 150, "looks": [150, 400], "settle_dates": {}, "projection": {}}]
    r = next(x for x in pc.aggregate(b, pc.REPO) if x["id"] == "NBA_X_T1")
    assert "GG-529" in r["second_state"] and "undefined" in r["second_state"]


def test_aggregate_cli_is_compact_json(tmp_path, capsys):
    f = tmp_path / "b.json"
    f.write_text(__import__("json").dumps(_blob()))
    assert pc.main(["--aggregate", "--input", str(f)]) == 0
    out = capsys.readouterr().out.strip()
    parsed = __import__("json").loads(out)
    assert "\n" not in out and isinstance(parsed, list)
    assert out == __import__("json").dumps(parsed, separators=(",", ":"))
