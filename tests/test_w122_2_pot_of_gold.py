"""W122.2 -- pot_of_gold candidate: new key only, v1 untouched, status gate, no look-ahead, nothing promoted outside the 17."""
import csv
import json
import os
import sys

import pytest

from prediction_market_bot.decision_trees import longshot
from prediction_market_bot.decision_trees import shadow_route as sr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "12_EXPLORATORY", "pot_of_gold"))

TK = "KXNBAGAME-26NOV22NOPGSW-NOP"


def _row(bid, ask, tk=TK, ts="2026-11-21T18:00:00+00:00", hrs=30.0, sport="NBA", mt="NBA_GAME_MONEYLINE"):
    return {"sport": sport, "market_type": mt, "band": "T3", "market_ticker": tk, "event_ticker": tk.rsplit("-", 1)[0],
            "yes_bid": bid, "yes_ask": ask, "half_spread": round((ask - bid) / 2, 4), "p_yes": 0.5,
            "horizon_hours_to_start": hrs, "ts_utc": ts}


def _table(status):
    c = longshot.LongshotCell("NBA", "KXNBAGAME", "D1", "90-95c", "all", "TAKE_FAVOURITE", "yes", status, 0.02, 0.04, None, 200)
    return longshot.Table([c]), "t.toml", "sha"


def test_v1_block_identical_with_and_without_candidates(monkeypatch):
    monkeypatch.setattr(sr, "_pot_table", lambda: _table("IN_SAMPLE"))
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "off")
    off = sr.router_fields(_row(0.91, 0.93), "KXNBAGAME", prev_mid=0.92)["router"]
    monkeypatch.setenv("PM_CANDIDATE_ARMS", "on")
    on = sr.router_fields(_row(0.91, 0.93), "KXNBAGAME", prev_mid=0.92)
    assert on["router"] == off
    assert on["router"]["orders"] == "off"
    json.dumps(on)


def test_key_only_in_pot_buckets(monkeypatch):
    monkeypatch.setattr(sr, "_pot_table", lambda: _table("IN_SAMPLE"))
    mid = sr.router_fields(_row(0.59, 0.61), "KXNBAGAME", prev_mid=0.6)["router_candidates"]
    assert "pot_of_gold" not in mid
    cheap = sr.router_fields(_row(0.05, 0.07), "KXNBAGAME", prev_mid=0.06)["router_candidates"]
    assert cheap["pot_of_gold"]["bucket"] == "5-10c"


def test_in_sample_cell_logs_no_bet_with_its_leaf_and_reason(monkeypatch):
    monkeypatch.setattr(sr, "_pot_table", lambda: _table("IN_SAMPLE"))
    p = sr.router_fields(_row(0.91, 0.93), "KXNBAGAME", prev_mid=0.92)["router_candidates"]["pot_of_gold"]
    assert p["arm"] == "NO_BET" and p["side"] is None
    assert p["leaf_id"] == "KXNBAGAME/D1/90-95c" and p["cell_status"] == "IN_SAMPLE"
    assert "not orderable" in p["reason"] and p["map_sha256"] == "sha"


def test_only_an_orderable_cell_names_an_arm(monkeypatch):
    monkeypatch.setattr(sr, "_pot_table", lambda: _table("HELD_OUT"))
    p = sr.router_fields(_row(0.91, 0.93), "KXNBAGAME", prev_mid=0.92)["router_candidates"]["pot_of_gold"]
    assert p["arm"] == "TAKE_FAVOURITE" and p["side"] == "yes"


def test_no_cell_is_no_bet(monkeypatch):
    monkeypatch.setattr(sr, "_pot_table", lambda: _table("HELD_OUT"))
    p = sr.router_fields(_row(0.91, 0.93, tk="KXNBATOTAL-26NOV22NOPGSW-T220"), "KXNBATOTAL", prev_mid=0.92)["router_candidates"]["pot_of_gold"]
    assert p["arm"] == "NO_BET" and "no cell" in p["reason"]


def test_tier_uses_only_the_row_clock():
    assert sr._pot_tier(_row(0.9, 0.92, ts="2026-11-21T18:00:00+00:00")) == "D1"      # 11-21 ET, game 11-22
    assert sr._pot_tier(_row(0.9, 0.92, ts="2026-11-20T18:00:00+00:00")) == "D2+"
    assert sr._pot_tier(_row(0.9, 0.92, ts="2026-11-22T18:00:00+00:00")) == "D0"
    assert sr._pot_tier(_row(0.9, 0.92, ts="2026-11-23T18:00:00+00:00")) is None       # after the event date: nothing
    mlb = _row(0.9, 0.92, tk="KXMLBGAME-26NOV221905NYYBOS-NYY", hrs=3.0, sport="MLB")
    assert sr._pot_tier(mlb) == "T2-6h"


def test_d0_and_late_rows_are_not_measured(monkeypatch):
    monkeypatch.setattr(sr, "_pot_table", lambda: _table("HELD_OUT"))
    p = sr.router_fields(_row(0.91, 0.93, ts="2026-11-22T18:00:00+00:00"), "KXNBAGAME", prev_mid=0.92)["router_candidates"]["pot_of_gold"]
    assert p["arm"] == "NO_BET" and "not measured" in p["reason"]


def test_candidate_error_never_blocks_the_row(monkeypatch):
    def boom():
        raise OSError("table missing")
    monkeypatch.setattr(sr, "_pot_table", boom)
    out = sr.router_fields(_row(0.91, 0.93), "KXNBAGAME", prev_mid=0.92)
    assert out["router_candidates"]["pot_of_gold"]["arm"] == "ERROR"
    assert out["router"]["branch"] != "ERROR"


def test_generator_promotes_nothing_outside_the_17(tmp_path, monkeypatch):
    import rescore_w122 as R
    cells = tmp_path / "cells.csv"
    cols = ["sport", "family", "tier", "bucket", "book", "route", "side", "status", "held_lo", "held_net", "all_n", "all_lo"]
    rows = [["NBA", "KXNBAPTS", "D1", "90-95c", "all", "TAKE_FAVOURITE", "yes", "HELD_OUT", "0.03", "0.05", "400", "0.02"],
            ["MLB", "KXMLBF5", "T2-6h", "10-15c", "all", "FADE_LONGSHOT", "no", "IN_SAMPLE", "-0.04", "0.07", "18", "-0.04"]]
    with open(cells, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    out = tmp_path / "t.toml"
    monkeypatch.setattr(R, "safe_out", lambda x: x)  # the fence refuses tmp_path; the fence has its own test
    named = [{"family": "KXMLBF5", "tier": "T2-6h", "bucket": "10-15c", "route": "FADE_LONGSHOT", "side": "no", "verdict": "IN_SAMPLE"}]
    assert R.write_table(str(cells), named, str(out)) == 2
    t = longshot.load(str(out))
    assert t.lookup("KXNBAPTS", "D1", "90-95c", "all").status == "IN_SAMPLE"      # a measured HELD_OUT outside the 17 stays a lead
    assert longshot.decide("KXNBAPTS", "D1", 0.92, 0.01, t).action == "NO_BET"
    assert t.lookup("KXMLBF5", "T2-6h", "10-15c", "all").status == "IN_SAMPLE"
