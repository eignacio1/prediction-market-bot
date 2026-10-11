"""W58.3 calibration engine: seal gate, known-answer metrics, NHL T3 / GG-401, read-only."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from prediction_market_bot.pregame_shadow import calibration_engine as ce

NOW = datetime(2026, 10, 7, tzinfo=timezone.utc)


def _rows(n_games, p=0.7, y=1.0, mid=0.5, start="2026-10-01T00:00:00Z"):
    return [{"market_ticker": f"M{i}", "band": "T1", "ts_utc": f"2026-10-01T00:{i % 60:02d}:00Z", "game_key": f"G{i:04d}",
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
    fast = __import__("dataclasses").replace(pol, boot_b=50)          # B only affects CI width, not the gate under test
    assert ce.compute_scores(fast, "T3", _rows(2500), {"GG-401": False})["status"] == "JUDGED"


def test_mlb_postseason_rows_counted_never_scored():
    out = ce.compute_scores(ce.PREREG["MLB"], "T1", _rows(900, start="2026-10-05T00:00:00Z"), {})
    assert out["judged_n"] == 0 and out["status"] == "SEALED" and not (ce.SCORE_KEYS & out.keys())
    assert out["scored_rows_available"] == 0


def test_counts_only_without_prereg():
    out = ce.compute_scores(ce.policy_for("XYZ"), "T1", _rows(500), {})
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
    c = next(x for x in res["cells"] if x["sport"] == "NHL")
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


# ── W59.2 Part B: release mechanics ───────────────────────────────────────────

def _games(n, start_day=1, flip_from=None, p=0.62, y_const=None):
    """n games, one row each, distinct start times in order; y alternates so Brier is non-degenerate."""
    from datetime import timedelta
    base = datetime(2026, 10, 1, tzinfo=timezone.utc)
    out = []
    for i in range(n):
        st = (base + timedelta(hours=6 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        y = float(i % 2) if (flip_from is None or i < flip_from) else float((i + 1) % 2)
        if y_const is not None:
            y = y_const
        out.append({"market_ticker": f"M{i:03d}", "band": "T1", "ts_utc": f"2026-10-01T00:{i % 60:02d}:{i // 60:02d}Z",
                    "game_key": f"G{i:03d}", "p_yes": p, "mid": 0.5, "yes_bid": 0.49, "yes_ask": 0.51, "y": y,
                    "p_clim": 0.5, "start_time_utc": st})
    return out


def test_59_emits_nothing_60_emits_verdict_61_does_not_change_first_look():
    pol = ce.PREREG["NFL"]
    r59 = ce.compute_scores(pol, "T1", _games(59), {})
    assert not ({"scores", "verdict", "release"} & r59.keys()) and not (ce.SCORE_KEYS & r59.keys())
    r60 = ce.compute_scores(pol, "T1", _games(60), {})
    assert r60["status"] == "JUDGED" and r60["release"]["look"] == 60 and len(r60["release"]["games"]) == 60
    assert r60["verdict"]["verdict"] in {"RULED_OUT", "SHADOW", "CANDIDATE-PENDING-CAPACITY"}
    # the verdict is computed on exactly those 60 games: same as scoring them directly
    direct = ce.scoring.score_cell(_games(60))
    assert r60["scores"]["delta_brier_vs_market"] == direct["delta_brier_vs_market"]
    assert r60["scores"]["bootstrap"] == {"B": 2000, "seed": 20261002, "unit": "game-cluster"}
    # game 61 (with an opposite outcome) must not move the first look
    r61 = ce.compute_scores(pol, "T1", _games(61) , {})
    assert r61["scores"] == r60["scores"] and r61["verdict"] == r60["verdict"]
    assert r61["judged_n"] == 61 and r61["scores_over_games"] == 60


def test_late_settling_earlier_game_cannot_change_a_released_look():
    pol = ce.PREREG["NFL"]
    rows60 = _games(60)
    first = ce.compute_scores(pol, "T1", rows60, {})
    # a game that STARTED before every other one settles late (postponed/straggler) with an extreme outcome
    late = dict(_games(1)[0], market_ticker="MLATE", game_key="GAAA-LATE", start_time_utc="2026-09-30T00:00:00Z", y=0.0, p_yes=0.99)
    unfrozen = ce.compute_scores(pol, "T1", rows60 + [late], {})
    assert unfrozen["scores"] != first["scores"]                      # order alone would have rewritten the look
    frozen = ce.compute_scores(pol, "T1", rows60 + [late], {}, frozen={"look": 60, "games": first["release"]["games"]})
    assert frozen["scores"] == first["scores"] and frozen["release"]["frozen"] is True


def test_game_order_is_start_time_then_game_key_not_arrival():
    rows = [dict(_games(1)[0], game_key=k, start_time_utc=s, ts_utc=t)
            for k, s, t in (("B", "2026-10-02T00:00:00Z", "2026-10-01T00:00:01Z"),
                            ("A", "2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z"),
                            ("C", "2026-10-01T00:00:00Z", "2026-10-09T00:00:00Z"))]
    assert ce._games_in_order(rows) == ["C", "A", "B"]


def test_manifest_is_write_once_and_tamper_evident(tmp_path):
    cell = {"cell": "NFL_NFL_X_T1"}
    rel = ce.compute_scores(ce.PREREG["NFL"], "T1", _games(60), {})["release"]
    now = datetime(2026, 10, 7, tzinfo=timezone.utc)
    assert ce.persist_release(tmp_path, cell, rel, now) is not None
    assert ce.persist_release(tmp_path, cell, dict(rel, games=["other"]), now) is None      # never overwritten
    assert ce.load_manifest(tmp_path, cell)["games"] == rel["games"]
    p = ce.manifest_path(tmp_path, cell, 60)
    m = json.loads(p.read_text()); m["games"][0] = "TAMPERED"; p.write_text(json.dumps(m))
    assert ce.load_manifest(tmp_path, cell) is None                                           # digest mismatch -> not trusted


@pytest.mark.parametrize("p,y,expect", [(0.9, 0.0, "RULED_OUT"), (0.5, None, "SHADOW"), (0.62, None, "SHADOW")])
def test_verdict_rules(p, y, expect):
    # p=0.9 on all-lose games is worse than the 0.5 market with CI wholly < 0 -> RULED_OUT;
    # p == market, or a noisy small edge deficit whose CI spans 0, -> SHADOW
    out = ce.compute_scores(ce.PREREG["NFL"], "T1", _games(60, p=p, y_const=y), {})
    assert out["verdict"]["verdict"] == expect


def test_verdict_candidate_needs_edge_under_both_fees():
    pol = ce.PREREG["NFL"]
    sc = lambda lo, hi, e7, ek: {"delta_brier_vs_market": {"mean": (lo + hi) / 2, "ci95": [lo, hi]},        # noqa: E731
                                 "delta_brier_vs_climatology": {"mean": 0.01, "ci95": [0.0, 0.02]},
                                 "e_net_entry_expected_k007": {"mean": e7}, "e_net_entry_expected_kmult": {"mean": ek}}
    assert ce.verdict(pol, "JUDGED", sc(0.01, 0.03, 0.02, 0.03), 60)["verdict"] == "CANDIDATE-PENDING-CAPACITY"
    assert ce.verdict(pol, "JUDGED", sc(0.01, 0.03, -0.01, 0.03), 60)["verdict"] == "SHADOW"       # edge fails under k007
    assert ce.verdict(pol, "JUDGED", sc(-0.03, -0.01, 0.0, 0.0), 60)["verdict"] == "RULED_OUT"
    assert ce.verdict(pol, "PRELIMINARY", sc(0.01, 0.03, 1, 1), 60) == {}                          # no verdict below a look


def test_nhl_uses_its_own_bootstrap_spec_and_rules():
    pol = ce.PREREG["NHL"]
    assert (pol.boot_b, pol.per_game_mean, pol.rules) == (10_000, True, "exp036")
    sc = {"delta_brier_vs_market": {"mean": -0.01, "ci95": [-0.02, -0.001]}, "delta_brier_vs_climatology": None,
          "e_net_entry_expected_k007": {"mean": -0.01}, "e_net_entry_expected_kmult": {"mean": -0.01}}
    assert ce.verdict(pol, "JUDGED", sc, 2500)["verdict"] == "RULED_OUT"
    assert ce.verdict(pol, "JUDGED", sc, 1000)["verdict"] == "SHADOW-continue"                      # (b) needs n>=2500


def test_first_look_report_format_and_no_score_below_look():
    from prediction_market_bot.pregame_shadow import first_look_report as flr
    cells = [c for c in flr.synthetic_cells(nhl_boot_b=30) if c["cell"] in ("SYN_NFL_model_worse", "SYN_NFL_real_edge", "SYN_NFL_59_games")]
    txt = flr.render_report(cells, "T", synthetic=True)
    assert "SYNTHETIC" in txt and "**RULED_OUT**" in txt and "**CANDIDATE-PENDING-CAPACITY**" in txt
    row59 = next(l for l in txt.splitlines() if l.startswith("| SYN_NFL_59_games"))
    assert "SEALED (59 of 60)" in row59 and "none (not at a look)" in row59 and "+" not in row59.replace("SYN_NFL_59_games", "")
    assert flr.render_report(cells, "T", synthetic=True) == txt        # deterministic


# ── W60.2: NBA policy (EXP-038) ──────────────────────────────────────────────

def test_nba_policy_matches_exp038():
    p = ce.PREREG["NBA"]
    assert p.looks == (150, 400) and p.boot_b == 2000 and p.boot_seed == 20261006
    assert p.mode == "sealed_until_look" and p.rules == "exp038" and p.has_climatology
    assert len(p.undefined) == 3 and any("GG-529" in u for u in p.undefined)


def test_nba_sealed_below_judged_n_no_score_no_verdict():
    out = ce.compute_scores(ce.PREREG["NBA"], "T1", _rows(149), {})
    assert out["status"] == "SEALED" and out["status_text"] == "SEALED (149 of 150)"
    assert not (ce.SCORE_KEYS & out.keys()) and "undefined_rules" in out


def test_nba_release_at_exactly_judged_n_and_one_past_does_not_change_the_look():
    at = ce.compute_scores(ce.PREREG["NBA"], "T1", _rows(150, y=lambda i: float(i % 2 == 0)), {})
    past = ce.compute_scores(ce.PREREG["NBA"], "T1", _rows(151, y=lambda i: float(i % 2 == 0)), {})
    assert at["status"] == "JUDGED" and at["scores_over_games"] == 150 and at["release"]["look"] == 150
    assert past["scores_over_games"] == 150 and past["release"]["games"] == at["release"]["games"]
    assert past["scores"] == at["scores"]            # incl. bootstrap CI: same games, same seed
    assert at["verdict"]["verdict"] in ("SHADOW", "RULED_OUT", "CANDIDATE-PENDING-CAPACITY")


def test_nba_preseason_rows_never_counted():
    pre = [{**r, "excluded_from_judged_n": True, "season_phase": "preseason"} for r in _rows(400)]
    out = ce.compute_scores(ce.PREREG["NBA"], "T1", pre, {})
    assert out["judged_n"] == 0 and out["status"] == "SEALED" and not (ce.SCORE_KEYS & out.keys())
    by_phase = [{**r, "season_phase": "preseason"} for r in _rows(400)]           # label alone is enough
    assert ce.compute_scores(ce.PREREG["NBA"], "T1", by_phase, {})["judged_n"] == 0
    reg = [{**r, "market_ticker": "R" + r["market_ticker"], "game_key": "R" + r["game_key"]} for r in _rows(149)]
    mixed = ce.compute_scores(ce.PREREG["NBA"], "T1", pre + reg, {})
    assert mixed["judged_n"] == 149 and mixed["status"] == "SEALED"


def test_nba_unresolved_after_second_look_when_ci_spans_zero():
    v = ce.verdict(ce.PREREG["NBA"], "JUDGED",
                   {"delta_brier_vs_market": {"mean": 0.001, "ci95": [-0.01, 0.012]},
                    "e_net_entry_expected_k007": {"mean": 0.0}, "e_net_entry_expected_kmult": {"mean": 0.0}}, 400)
    assert v["verdict"] == "UNRESOLVED"
    v1 = ce.verdict(ce.PREREG["NBA"], "JUDGED",
                    {"delta_brier_vs_market": {"mean": 0.001, "ci95": [-0.01, 0.012]},
                     "e_net_entry_expected_k007": {"mean": 0.0}, "e_net_entry_expected_kmult": {"mean": 0.0}}, 150)
    assert v1["verdict"] == "SHADOW"


def test_nba_cells_listed_before_first_row_and_preseason_dir_never_read(tmp_path):
    (tmp_path / "exp_output/PREGAME_SHADOW_PRESEASON").mkdir(parents=True)
    (tmp_path / "exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T1.jsonl").write_text('{"x":1}\n')
    res = ce.run(tmp_path)
    nba = [c for c in res["cells"] if c["sport"] == "NBA"]
    assert len(nba) == 15 and all(c["rows"] == 0 and c["status"] == "SEALED" for c in nba)
    assert {c["market_type"] for c in nba} == {"MONEYLINE", "SPREAD", "GAME_TOTAL", "TEAM_TOTAL", "PLAYER_POINTS"}
    assert all("PRESEASON" not in c["source"] for c in nba)


# ── W65.1: NBA player-points policy (EXP-039) ────────────────────────────────

def test_nba_pts_policy_matches_exp039():
    p = ce.PREREG["NBA_PTS"]
    assert p.looks == (300, 800) and p.boot_b == 2000 and p.boot_seed == 20261009
    assert p.unit == "player_game" and p.rules == "exp038" and p.mode == "sealed_until_look"


def test_nba_pts_sealed_below_300_player_games():
    out = ce.compute_scores(ce.PREREG["NBA_PTS"], "T1", _rows(299), {})
    assert out["status"] == "SEALED" and out["status_text"] == "SEALED (299 of 300)"
