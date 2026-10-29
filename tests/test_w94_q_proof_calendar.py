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
