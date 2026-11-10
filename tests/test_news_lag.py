from datetime import datetime, timedelta, timezone

from prediction_market_bot.quant import news_lag as nl

TEXT = """Injury Report: 11/01/26 08:15 PM Page 1 of 1
Game Date Game Time Matchup Team Player Name Current Status Reason
11/01/2026 07:30 (ET) BKN@IND Brooklyn Nets Brown Jr., Mikel Out Injury/Illness - Lower Back, Injury Management
Demin, Egor Questionable Injury/Illness - Knee Bilodeau, Tyler Out G League - Two-Way
Indiana Pacers NOT YET SUBMITTED"""


def test_parser_suffix_and_comma_reason():
    rows = nl.parse_injury_text(TEXT)
    assert [(r.player, r.status, r.g_league) for r in rows] == [
        ("Brown Jr., Mikel", "Out", False), ("Demin, Egor", "Questionable", False), ("Bilodeau, Tyler", "Out", True)]
    assert rows[0].team == "Brooklyn Nets" and rows[0].side == "away" and rows[0].matchup == "BKN@IND"


def _row(status, player="A, B"):
    return nl.Row("2026-11-01", "07:30", "BKN@IND", "away", "Brooklyn Nets", player, status, False)


def test_events_direction_and_first_appearance_ignored():
    t = datetime(2026, 11, 1, 23, 0, tzinfo=timezone.utc)
    ev = nl.report_events([_row("Questionable")], [_row("Out"), _row("Out", "C, D")], t)
    assert len(ev) == 1 and ev[0].sign == -1 and ev[0].kind == "to_out"
    ev = nl.report_events([_row("Questionable")], [_row("Available")], t)
    assert ev[0].sign == 1 and ev[0].kind == "q_to_active"


def _planted(lag_min, jump=0.05, step=20):
    """price jumps by `jump` (against the team) lag_min after news at t0; snapshots every `step` minutes"""
    t0 = datetime(2026, 11, 1, 20, 0, tzinfo=timezone.utc)
    s = []
    for k in range(-6, 12):
        t = t0 + timedelta(minutes=k * step + 1)
        s.append((t, 0.60 - (jump if (t - t0).total_seconds() / 60 >= lag_min else 0)))
    e = nl.Event(t0, "2026-11-01", "BKN@IND", "Brooklyn Nets", "away", t0 + timedelta(hours=5), "to_out", -1, "A, B")
    return e, s


def test_planted_lag_recovered():
    e, s = _planted(lag_min=30)
    p = nl.signed_profile([e], lambda _e: s, [20, 60])
    assert abs(p["horizons"][20]["mean_signed"] - 0.0) < 1e-9      # lag longer than one snapshot: not yet visible at +20
    assert abs(p["horizons"][60]["mean_signed"] - 0.05) < 1e-9     # visible at +60
    assert abs(nl.increment(lambda _e: s, [e], 20, 60)["mean_signed"] - 0.05) < 1e-9
    assert p["pre"]["mean_signed"] == 0.0                          # no leak before the news


def test_sub_snapshot_lag_is_invisible_as_increment():
    e, s = _planted(lag_min=5)       # instant at 20-min resolution: whole move is in the first post-news snapshot
    assert abs(nl.increment(lambda _e: s, [e], 20, 60)["mean_signed"]) < 1e-9
