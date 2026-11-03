"""W98.1 / B-030: every archived game is either logged or accounted for with a reason; rows are never altered."""
import json
from datetime import datetime, timedelta, timezone

from prediction_market_bot.nba_engine import live as L

NOW = datetime(2026, 11, 3, 1, 0, tzinfo=timezone.utc)
P = lambda d, h, a: dict(game_date=d, home=h, away=a)


def _seen():
    return {"E_DONE": P("2026-11-02", "BOS", "NYK"), "E_MISSED": P("2026-11-02", "DAL", "OKC"),
            "E_FUTURE": P("2026-11-03", "LAL", "DEN"), "E_NOTIP": P("2026-11-02", "MIA", "ORL")}


def _tips():
    return {("2026-11-02", "BOS", "NYK"): NOW - timedelta(hours=2), ("2026-11-02", "DAL", "OKC"): NOW - timedelta(minutes=30),
            ("2026-11-03", "LAL", "DEN"): NOW + timedelta(hours=3)}


def test_misses_are_exactly_unlogged_past_tip_or_no_tip():
    m = {x["event_ticker"]: x["reason"] for x in L.coverage_misses(_seen(), _tips(), {"E_DONE"}, NOW)}
    assert m == {"E_MISSED": "window_closed_without_a_successful_run", "E_NOTIP": "no_tip_in_schedule"}


def test_slate_logged_in_full_has_no_misses():
    assert L.coverage_misses(_seen(), _tips(), {"E_DONE", "E_MISSED", "E_NOTIP", "E_FUTURE"}, NOW) == []


def test_tip_equal_now_counts_as_closed():
    seen = {"E": P("2026-11-02", "DAL", "OKC")}
    assert L.coverage_misses(seen, {("2026-11-02", "DAL", "OKC"): NOW}, set(), NOW)[0]["reason"].startswith("window_closed")


def test_write_coverage_is_idempotent_and_leaves_rows_alone(tmp_path):
    rows = tmp_path / "rows.jsonl"
    rows.write_text('{"event_ticker": "E_DONE"}\n')
    misses = L.coverage_misses(_seen(), _tips(), {"E_DONE"}, NOW)
    assert L.write_coverage(tmp_path, misses, NOW) == 2
    assert L.write_coverage(tmp_path, misses, NOW + timedelta(minutes=10)) == 0
    got = [json.loads(l) for l in (tmp_path / "coverage.jsonl").read_text().splitlines()]
    assert {g["event_ticker"] for g in got} == {"E_MISSED", "E_NOTIP"}
    assert rows.read_text() == '{"event_ticker": "E_DONE"}\n'
