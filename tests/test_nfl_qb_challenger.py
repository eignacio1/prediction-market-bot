"""W65.3: NFL QB challenger -- look-ahead, pairing with frozen features, safety, engine and silent-arm coverage."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import NFLPregameFeatureBuilder
from prediction_market_bot.c1_signal_ingestion.nfl_qb_features import (
    CHALLENGER_FEATURE_NAMES, NFLQBFeatureBuilder, shrunk_mean)

TEAMS = ["AAA", "BBB", "CCC", "DDD"]
REPO = Path(__file__).resolve().parent.parent


def _league(n_weeks=14, seed=3):
    rng = np.random.default_rng(seed)
    sched, stats, d0 = [], [], date(2025, 9, 7)
    for w in range(n_weeks):
        gd = d0 + timedelta(days=7 * w)
        order = TEAMS[w % 4:] + TEAMS[:w % 4]
        for h, a in ((order[0], order[1]), (order[2], order[3])):
            gid = f"g{w}{h}{a}"
            sched.append(dict(game_id=gid, gameday=gd.isoformat(), home_team=h, away_team=a, season=2025, game_type="REG",
                              home_score=float(rng.integers(10, 35)), away_score=float(rng.integers(10, 35)),
                              home_qb_id=f"q{h}{w // 5}", away_qb_id=f"q{a}{w // 5}", home_rest=7, away_rest=7))
            for t, o in ((h, a), (a, h)):
                stats.append(dict(game_id=gid, team=t, opponent_team=o, off_epa=float(rng.normal(0, 5))))
    return pd.DataFrame(sched), pd.DataFrame(stats)


def _asof(d: date):
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def test_shrunk_mean_k0_is_plain_weighted_and_large_k_is_prior():
    v = np.array([1.0, 2.0, 3.0])
    assert abs(shrunk_mean(v, 1.0, 0.0, 99.0) - 2.0) < 1e-9
    assert abs(shrunk_mean(v, 1.0, 1e9, 7.0) - 7.0) < 1e-3


def test_same_games_as_frozen_and_audit_flags_projected():
    s, t = _league()
    ch, fr = NFLQBFeatureBuilder(t, s), NFLPregameFeatureBuilder(t, s)
    d = _asof(date(2025, 11, 30))
    c, f = ch.row("AAA", "BBB", d, 7, 7), fr.row("AAA", "BBB", d, 7, 7)
    assert c is not None and f is not None
    assert list(c["features"]) == CHALLENGER_FEATURE_NAMES or set(c["features"]) == set(CHALLENGER_FEATURE_NAMES)
    assert c["audit"]["qb_source"] == "projected_prior_game_starter"
    assert c["features"]["rest_diff"] == f["features"]["rest_diff"]
    # no history before the first game -> both builders decline (same game set)
    assert ch.row("AAA", "BBB", _asof(date(2025, 9, 1)), 7, 7) is None
    assert fr.row("AAA", "BBB", _asof(date(2025, 9, 1)), 7, 7) is None


def test_no_lookahead_future_results_cannot_change_a_row():
    s, t = _league()
    d = _asof(date(2025, 11, 2))
    base = NFLQBFeatureBuilder(t, s).row("AAA", "BBB", d, 7, 7)
    s2, t2 = s.copy(), t.copy()
    fut = pd.to_datetime(s2.gameday).dt.date >= date(2025, 11, 2)    # the as-of day itself and later
    s2.loc[fut, ["home_score", "away_score"]] = 99.0
    s2.loc[fut, ["home_qb_id", "away_qb_id"]] = "FUTURE_QB"
    t2.loc[t2.game_id.isin(s2[fut].game_id), "off_epa"] = 1e6
    mut = NFLQBFeatureBuilder(t2, s2).row("AAA", "BBB", d, 7, 7)
    assert base["features"] == mut["features"] and base["sha256"] == mut["sha256"]


def test_qb_term_is_the_prior_games_starter_not_the_current_one():
    s, t = _league()
    d = _asof(date(2025, 11, 30))
    base = NFLQBFeatureBuilder(t, s).row("AAA", "BBB", d, 7, 7)
    s2 = s.copy()                                  # today's game listing a different starter must not matter
    today = s2.gameday == "2025-11-30"
    s2.loc[today, ["home_qb_id", "away_qb_id"]] = "TODAYS_QB"
    assert NFLQBFeatureBuilder(t, s2).row("AAA", "BBB", d, 7, 7)["audit"] == base["audit"]


def test_model_artifact_loads_and_scores_in_unit_interval():
    from prediction_market_bot.pregame_shadow.nfl_qb_model import NFLQBChallengerModel
    from prediction_market_bot.pregame_shadow.nfl_model import p_yes_for
    m = NFLQBChallengerModel.load(str(REPO / "models" / "nfl_qb_challenger_v1.json"))   # sha256 verified
    s, t = _league()
    row = NFLQBFeatureBuilder(t, s).row("AAA", "BBB", _asof(date(2025, 11, 30)), 7, 7)
    p = p_yes_for(m, row["features"], "NFL_MONEYLINE", subject_is_home=True)
    q = p_yes_for(m, row["features"], "NFL_MONEYLINE", subject_is_home=False)
    assert 0 < p < 1 and abs(p + q - 1) < 1e-6
    meta = json.loads((REPO / "models" / "nfl_qb_challenger_v1_meta.json").read_text())
    assert meta["artifact_sha256"] == m.sha256


def test_tampered_artifact_is_refused(tmp_path):
    import pytest
    from prediction_market_bot.pregame_shadow.nfl_qb_model import NFLQBChallengerModel
    a = json.loads((REPO / "models" / "nfl_qb_challenger_v1.json").read_text())
    a["sigma_margin"] += 1.0
    p = tmp_path / "m.json"
    p.write_text(json.dumps(a))
    with pytest.raises(Exception):
        NFLQBChallengerModel.load(str(p))


def test_calibration_engine_lists_challenger_under_c2_rule(tmp_path):
    from prediction_market_bot.pregame_shadow import calibration_engine as ce
    pol = ce.PREREG["NFLQB"]
    assert pol.looks == (60, 150) and pol.rules == "exp037" and "984" in pol.citation   # states the withdrawal
    d = tmp_path / "exp_output" / "PREGAME_SHADOW_NFLQB"
    d.mkdir(parents=True)
    (d / "NFLQB_NFL_MONEYLINE_T1.jsonl").write_text("")
    cells = [c for c in ce.discover_cells(tmp_path) if c["sport"] == "NFLQB"]
    assert [c["cell"] for c in cells] == ["NFLQB_NFL_MONEYLINE_T1"]
    assert cells[0]["band"] == "T1" and cells[0]["market_type"] == "MONEYLINE"


def test_silent_arm_spec_registered():
    from prediction_market_bot.pregame_shadow import silent_arms as sa
    assert "nfl_qb_challenger" in sa.SPECS


def test_frozen_settle_glob_does_not_touch_challenger_files(tmp_path):
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    import run_pregame_shadow_settle as st
    (tmp_path / "NFLQB_NFL_MONEYLINE_T1.jsonl").write_text("{}\n")
    assert st.settle(tmp_path, pd.DataFrame({"home_score": [], "away_score": []}), {}) == {}


def test_cron_block_is_new_lines_only_and_off_round_minutes():
    txt = (REPO / "deploy" / "cron_exp037_pregame_shadow.conf").read_text()
    blk = txt.split("# BEGIN W65.3 NFLQB")[1].split("# END W65.3 NFLQB")[0]
    jobs = [l for l in blk.splitlines() if l and not l.startswith("#")]
    assert len(jobs) == 2 and all(j.split()[0] not in ("0", "30") for j in jobs)
    assert "sizing" in blk and "run_nfl_qb_challenger_shadow.py" in jobs[0]


def test_engine_lists_challenger_cell_before_first_row(tmp_path):
    from prediction_market_bot.pregame_shadow.calibration_engine import discover_cells
    cells = discover_cells(tmp_path)
    assert any("NFLQB_NFL_MONEYLINE_T1" in str(c) for c in cells)
