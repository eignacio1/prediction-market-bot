"""W58.3 calibration engine: seal gate, known-answer metrics, NHL T3 / GG-401, read-only."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from prediction_market_bot.pregame_shadow import calibration_engine as ce

NOW = datetime(2026, 10, 7, tzinfo=timezone.utc)


def _rows(n_games, p=0.7, y=1.0, mid=0.5, start="2026-10-01T00:00:00Z"):
    return [{"market_ticker": f"M{i}", "band": "T1", "ts_utc": f"2026-10-01T00:{i % 60:02d}:00Z", "game_key": f"G{i}",
             "p_yes": p, "mid": mid, "yes_bid": mid - 0.01, "yes_ask": mid + 0.01, "y": y if not callable(y) else y(i),
             "p_clim": 0.5, "start_time_utc": start} for i in range(n_games)]


def test_sealed_cell_never_emits_score_even_when_called_directly():
    out = ce.compute_scores(ce.PREREG["NFL"], "T1", _rows(59), {})
    assert out["status"] == "SEALED" and out["status_text"] == "SEALED (59 of 60)"
    assert not (ce.SCORE_KEYS & out.keys())


def test_nfl_looks_at_60_and_scores_earliest_60_only():
    out = ce.compute_scores(ce.PREREG["NFL"], "T1", _rows(100), {})
    assert out["status"] == "JUDGED" and out["scores_over_games"] == 60
    assert out["scores"]["brier_model"] == pytest.approx(0.09)


def test_nhl_preliminary_label_and_t3_sealed_while_gg401_open():
    pol = ce.PREREG["NHL"]
    prelim = ce.compute_scores(pol, "T1", _rows(10), {"GG-401": True})
    assert prelim["status_text"] == "PRELIMINARY (n=10 of 2500)" and "scores" in prelim
    sealed = ce.compute_scores(pol, "T3", _rows(5000), {"GG-401": True})
    assert sealed["status"] == "SEALED" and not (ce.SCORE_KEYS & sealed.keys())
    assert ce.compute_scores(pol, "T3", _rows(5000), {})["status"] == "SEALED"   # unknown = open
    assert ce.compute_scores(pol, "T3", _rows(5000), {"GG-401": False})["status"] == "JUDGED"


def test_mlb_postseason_rows_counted_never_scored():
    out = ce.compute_scores(ce.PREREG["MLB"], "T1", _rows(900, start="2026-10-05T00:00:00Z"), {})
    assert out["judged_n"] == 0 and out["status"] == "SEALED" and not (ce.SCORE_KEYS & out.keys())
    assert out["scored_rows_available"] == 0


def test_counts_only_without_prereg():
    out = ce.compute_scores(ce.policy_for("NBA"), "T1", _rows(500), {})
    assert out["status"] == "COUNTS ONLY" and not (ce.SCORE_KEYS & out.keys())


def test_known_answer_metrics():
    # y alternates 1,0; model p=0.7 -> Brier .09/.49 mean .29 ; market .5 -> .25 ; clim .5 -> .25
    rows = _rows(100, y=lambda i: float(i % 2 == 0))
    s = ce.compute_scores(ce.PREREG["NFL"], "T1", rows, {})["scores"]
    assert s["brier_model"] == pytest.approx(0.29)
    assert s["brier_market"] == pytest.approx(0.25)
    assert s["delta_brier_vs_market"]["mean"] == pytest.approx(-0.04)   # negative: model worse
    assert s["delta_brier_vs_climatology"]["mean"] == pytest.approx(-0.04)
    assert s["delta_brier_vs_market"]["ci95"][0] <= -0.04 <= s["delta_brier_vs_market"]["ci95"][1]


def test_decomposition_exact_when_p_constant_per_bin():
    ps, ys = [0.7] * 10, [1.0] * 7 + [0.0] * 3        # perfectly reliable single bin
    d = ce.brier_decomposition(ps, ys)
    assert d["reliability"] == pytest.approx(0.0) and d["resolution"] == pytest.approx(0.0)
    assert d["uncertainty"] == pytest.approx(0.21)
    assert d["reliability"] - d["resolution"] + d["uncertainty"] == pytest.approx(0.21)
    ps2, ys2 = [0.9] * 10, [1.0] * 5 + [0.0] * 5      # overconfident
    d2 = ce.brier_decomposition(ps2, ys2)
    assert d2["reliability"] == pytest.approx(0.16)
    assert d2["reliability"] - d2["resolution"] + d2["uncertainty"] == pytest.approx(0.41)  # = mean Brier
    bins = ce.reliability_bins(ps2, ys2)
    assert bins[9]["n"] == 10 and bins[9]["obs_freq"] == 0.5


def test_mlb_has_no_climatology_field():
    s = ce.compute_scores(ce.PREREG["MLB"], "T1", _rows(150, start="2027-04-01T00:00:00Z"), {})["scores"]
    assert "brier_climatology" not in s and "delta_brier_vs_climatology" not in s and s["climatology"] == "unavailable"


def test_projection_counts_only():
    rows = [{**r, "start_time_utc": f"2026-10-0{1 + i % 5}T00:00:00Z"} for i, r in enumerate(_rows(30))]
    sched = ["2026-10-0%d" % (1 + i % 5) for i in range(40)] + ["2026-10-%d" % (10 + i % 15) for i in range(60)]
    pj = ce.project_first_look(ce.PREREG["NFL"], rows, NOW, sched, "2026-10-01T00:00:00Z")
    assert pj["date"] and pj["date"] > "2026-10-07"
    assert ce.project_first_look(ce.PREREG["MLB"], rows, NOW)["note"].startswith("judged games begin")


def test_gg_status_parse_and_unreadable_is_open(tmp_path):
    (tmp_path / "03_DECISIONS").mkdir()
    (tmp_path / "03_DECISIONS/GOVERNANCE_GAP_LOG.md").write_text("### GG-401 — x\n**Status:** OPEN · **Severity:** HIGH\n")
    assert ce.gg_is_open(tmp_path, "GG-401")
    (tmp_path / "03_DECISIONS/GOVERNANCE_GAP_LOG.md").write_text("### GG-401 — x\n**Status:** RESOLVED · **Severity:** HIGH\n")
    assert not ce.gg_is_open(tmp_path, "GG-401")
    assert ce.gg_is_open(tmp_path / "nowhere", "GG-401")


def test_run_is_read_only_and_nhl_joins_ledger(tmp_path):
    d = tmp_path / "data/shadow/nhl"; (d / "settled").mkdir(parents=True)
    led = [{"run_id": "r", "market_ticker": f"M{i}", "band": "T3", "ts_utc": "2026-10-01T00:00:00Z",
            "event_ticker": f"E{i}", "p_yes": .6, "mid": .5, "yes_bid": .49, "yes_ask": .51,
            "start_time_utc": "2026-10-01T00:00:00Z"} for i in range(3)]
    (d / "NHL_MONEYLINE_T3.jsonl").write_text("".join(json.dumps(r) + "\n" for r in led))
    (d / "settled/NHL_MONEYLINE_T3.jsonl").write_text("".join(
        json.dumps({"run_id": "r", "market_ticker": f"M{i}", "outcome": 1}) + "\n" for i in range(3)))
    before = {p: p.read_bytes() for p in d.rglob("*.jsonl")}
    res = ce.run(tmp_path, NOW)
    c = res["cells"][0]
    assert c["settled_games"] == 3 and c["status"] == "SEALED" and "scores" not in c
    assert before == {p: p.read_bytes() for p in d.rglob("*.jsonl")}


def test_module_imports_only_scoring_and_stdlib():
    import ast
    tree = ast.parse(Path(ce.__file__).read_text())
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not [m for m in mods if "c5_execution" in m or "c4_risk" in m or "execution_bands" in m]


# ── W59.2 Part A: schedule-based projection ───────────────────────────────────

def _sched(start, per_day_pattern):
    """One date string per scheduled game. per_day_pattern: {offset_days: n_games}."""
    from datetime import timedelta
    d0 = datetime.strptime(start, "%Y-%m-%d")
    return sorted((d0 + timedelta(days=o)).strftime("%Y-%m-%d") for o, n in per_day_pattern.items() for _ in range(n))


def _settled(n):
    return _rows(n)


def test_projection_follows_weekly_schedule_not_linear_rate():
    # Weekly slate (16 games every 7 days). 20 settled of 32 scheduled since 2026-10-01 -> coverage 0.625.
    sched = _sched("2026-10-01", {0: 16, 7: 16, 14: 16, 21: 16, 28: 16})
    now = datetime(2026, 10, 9, tzinfo=timezone.utc)
    out = ce.project_first_look(ce.PREREG["NFL"], _settled(20), now, sched, "2026-10-01T00:00:00Z")
    # need 40 more; 48 left (dates >= 10-09: wk 10-15 x16, 10-22 x16, 10-29 x16) -> 0.625/game:
    # 10-15: 10, 10-22: 20, 10-29: 30 ... need 40 > 48*0.625=30 -> not reachable in the schedule.
    assert out["reachable"] is False and out["date"] is None
    assert out["coverage"] == pytest.approx(0.625)


def test_projection_date_lands_on_slate_day_plus_settle_lag():
    sched = _sched("2026-10-01", {0: 10, 7: 10, 14: 10, 21: 10, 28: 10, 35: 10})
    now = datetime(2026, 10, 9, tzinfo=timezone.utc)
    out = ce.project_first_look(ce.PREREG["NFL"], _settled(20), now, sched, "2026-10-01T00:00:00Z")
    # past = 10-01 + 10-08 slates = 20 scheduled, 20 settled -> coverage 1.0; need 40, 40 left (4 slates)
    # -> the 40th lands on the last slate 11-05, +1 day settle lag
    assert out["date"] == "2026-11-06" and out["reachable"] is True
    # a linear trailing rate would put this on a different (earlier) day; the date must sit on a slate day + lag
    assert out["date"] in {"2026-11-06"}


def test_projection_none_without_schedule_or_before_season():
    assert "no published schedule" in ce.project_first_look(ce.PREREG["NFL"], _settled(3), NOW, None)["note"]
    mlb = ce.project_first_look(ce.PREREG["MLB"], [], NOW, None)
    assert mlb["date"] is None and "2027-03-01" in mlb["note"]


def test_projection_coverage_unmeasurable_with_tiny_sample():
    out = ce.project_first_look(ce.PREREG["NFL"], _settled(1), NOW, ["2026-10-06"] * 2 + ["2026-10-20"] * 50, "2026-10-05T00:00:00Z")
    assert out["date"] is None and "unmeasurable" in out["note"]


def test_projection_reached_returns_no_date():
    out = ce.project_first_look(ce.PREREG["NFL"], _settled(60), NOW, ["2026-10-20"])
    assert out["note"] == "first look reached"
