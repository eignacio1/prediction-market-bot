"""Gate 2 matching helpers (EXP-035 / T-605). Synthetic only."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import board_survey_sports_gate2 as g2  # noqa: E402


def c(ts, b, a):
    return {"end_period_ts": ts, "yes_bid": {k: f"{b:.4f}" for k in ("close", "high", "low", "open")},
            "yes_ask": {k: f"{a:.4f}" for k in ("close", "high", "low", "open")}}


def test_prevailing_is_latest_at_or_before_t_not_next_change():
    ms = [c(400, .5, .55), c(100, .4, .45)]
    cd, how, srt, idx = g2.prevailing(ms, [], 250)
    assert how == "minute" and cd["end_period_ts"] == 100 and idx == 0
    assert g2.prevailing(ms, [], 100)[0]["end_period_ts"] == 100          # <= inclusive


def test_hourly_fallback_then_unmatched():
    assert g2.prevailing([c(400, .5, .55)], [c(50, .3, .35), c(10, .2, .25)], 250)[1:2] == ("hourly",)
    assert g2.prevailing([c(400, .5, .55)], [c(50, .3, .35), c(10, .2, .25)], 250)[0]["end_period_ts"] == 50
    assert g2.prevailing([c(400, .5, .55)], [], 250)[1] == "unmatched"


def test_agrees_tolerance_and_g3_neighbours():
    run = ("x", .40, .45)
    assert g2.agrees(run, c(1, .41, .44)) and not g2.agrees(run, c(1, .43, .45))
    assert g2.g3_contains(run, [c(1, .38, .43), c(2, .41, .47)]) and not g2.g3_contains(run, [c(1, .5, .6)])
