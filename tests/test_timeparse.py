"""GG-1934 known answers: the one tolerant parser accepts what Kalshi and our logs emit, on Python 3.9 rules."""
from datetime import datetime, timezone

from prediction_market_bot.timeparse import parse_ts

UTC = timezone.utc


def test_kalshi_five_digit_fraction_with_z():
    assert parse_ts("2026-11-12T03:04:05.12345Z") == datetime(2026, 11, 12, 3, 4, 5, 123450, tzinfo=UTC)


def test_nine_digit_fraction_truncates_to_micros():
    assert parse_ts("2026-11-12T03:04:05.123456789+00:00") == datetime(2026, 11, 12, 3, 4, 5, 123456, tzinfo=UTC)


def test_plain_z_and_offset_normalise_to_utc():
    assert parse_ts("2026-11-12T03:04:05Z") == datetime(2026, 11, 12, 3, 4, 5, tzinfo=UTC)
    assert parse_ts("2026-11-11T19:04:05-08:00") == datetime(2026, 11, 12, 3, 4, 5, tzinfo=UTC)


def test_naive_is_utc_and_datetime_passes_through():
    assert parse_ts("2026-11-12T03:04:05") == datetime(2026, 11, 12, 3, 4, 5, tzinfo=UTC)
    d = datetime(2026, 11, 12, 3, 4, 5)
    assert parse_ts(d) == d.replace(tzinfo=UTC)


def test_garbage_and_empty_are_none():
    for bad in (None, "", "not-a-time", "2026-13-40T00:00:00Z"):
        assert parse_ts(bad) is None
