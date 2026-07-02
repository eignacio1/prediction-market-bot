"""Tests for scripts/run_exp_flow_mlb_01.py — EXP-FLOW-MLB-01 backtest runner
(ADR-0039 / GG-067 / F-FLOW-01).

Covers: cycle-log JSONL loading (incl. FLOW-specific fields ba_l10/ab_so_far/
inning/batting_slot), the ticker+inning score_diff join, per-game synthetic-key
grouping, the blowout-sustain state machine (mirrors T4MlbFlowEvaluator.evaluate()
exactly — must reject until sustained, reset when the gap closes, and re-require
the sustain window on a fresh blowout), p_flow recomputation via the adjusted
ba_l10, earliest-wins dedup, resolution/outcome/pnl, the effect-existence
diagnostic, grid sweep shape, and the no-cycle-log-file graceful path through
main(). No real ESPN/network calls — score_diff lookups are constructed directly
or via a monkeypatched load_score_diff_lookup.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("BOT_ENV", "paper")
os.environ.setdefault("BOT_C4_ACTIVE", "true")

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import run_exp_flow_mlb_01 as flow_mod
from run_exp_flow_mlb_01 import (
    FlowCycle,
    ResolvedBet,
    RUN_THRESHOLD_GRID,
    SUSTAIN_INNINGS_GRID,
    _BLOWOUT_RUN_THRESHOLD_DEFAULT,
    _BLOWOUT_SUSTAIN_INNINGS_DEFAULT,
    _MIN_EDGE,
    MIN_N,
    V_INC,
    load_cycle_log,
    join_score_diff,
    build_score_diff_lookups,
    compute_flow_bets,
    dedupe_earliest_flow,
    resolve_flow_bets,
    evaluate_cell,
    run_grid_sweep,
    effect_existence_diagnostic,
    main,
)
from prediction_market_bot.run_t4_mlb_live import _compute_ab_remaining, p_hits_gte_threshold


# ── Helpers ────────────────────────────────────────────────────────────────────

# away=BAL, home=LAA (per kalshi_client.py docstring ticker convention)
_TICKER_LAA_HOME = "KXMLBHIT-26JUN241607BALLAA-LAAJADELL7-2"
_TICKER_BAL_AWAY = "KXMLBHIT-26JUN241607BALLAA-BALHENDERSON22-2"


def _make_cycle(
    ticker=_TICKER_LAA_HOME,
    player_id=1,
    player_name="Test Player",
    game_date="2026-06-01",
    threshold=2,
    h_so_far=0,
    ab_so_far=2,
    inning=5,
    batting_slot=3,
    ba_l10=0.30,
    mip=0.30,
    vig=0.02,
    ts="2026-06-01T01:00:00Z",
) -> FlowCycle:
    return FlowCycle(
        ticker=ticker, player_id=player_id, player_name=player_name,
        game_date=game_date, threshold=threshold, h_so_far=h_so_far,
        ab_so_far=ab_so_far, inning=inning, batting_slot=batting_slot,
        ba_l10=ba_l10, mip=mip, vig=vig, ts=ts,
    )


def _cycle_record(**overrides) -> dict:
    rec = {
        "ts": "2026-06-01T01:00:00Z",
        "cycle_id": "CL-01",
        "session_id": "TEST",
        "game_date": "2026-06-01",
        "ticker": _TICKER_LAA_HOME,
        "player_name": "Test Player",
        "player_id": 1,
        "threshold": 2,
        "p_t4": 0.50,
        "mip": 0.30,
        "vig": 0.02,
        "gross_edge": 0.18,
        "net_edge": 0.15,
        "ba_l10": 0.30,
        "h_so_far": 0,
        "ab_so_far": 2,
        "ab_remaining": 2,
        "inning": 5,
        "batting_slot": 3,
    }
    rec.update(overrides)
    return rec


def _write_cycle_log(path: Path, records: list[dict]) -> None:
    with open(path, "w") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")


def _lookup_row(batting_abbr: str, defense_abbr: str, inning: int, half: str, score_diff: float) -> dict:
    return {
        "inning": inning, "half": half,
        "batting_team_abbr": batting_abbr, "defense_team_abbr": defense_abbr,
        "score_diff": score_diff, "is_batting_team_leading": score_diff > 0,
    }


def _lookup(rows: list[dict], away_abbr="BAL", home_abbr="LAA") -> dict:
    return {(away_abbr, home_abbr, r["inning"], r["half"]): r for r in rows}


# ── load_cycle_log ─────────────────────────────────────────────────────────────

class TestLoadCycleLog:
    def test_missing_file_returns_empty(self, tmp_path):
        assert load_cycle_log(tmp_path / "nope.jsonl") == []

    def test_loads_valid_records_with_flow_fields(self, tmp_path):
        path = tmp_path / "cl.jsonl"
        _write_cycle_log(path, [_cycle_record(), _cycle_record(ticker="T2", player_id=2)])
        cycles = load_cycle_log(path)
        assert len(cycles) == 2
        assert cycles[0].ba_l10 == 0.30
        assert cycles[0].ab_so_far == 2
        assert cycles[0].inning == 5
        assert cycles[0].batting_slot == 3

    def test_skips_malformed_lines(self, tmp_path):
        path = tmp_path / "cl.jsonl"
        with open(path, "w") as fh:
            fh.write(json.dumps(_cycle_record()) + "\n")
            fh.write("not json at all\n")
            fh.write(json.dumps({"ticker": "missing_fields"}) + "\n")
            fh.write("\n")
            fh.write(json.dumps(_cycle_record(ticker="T3", player_id=3)) + "\n")
        cycles = load_cycle_log(path)
        assert len(cycles) == 2
        assert {c.ticker for c in cycles} == {_TICKER_LAA_HOME, "T3"}


# ── join_score_diff ──────────────────────────────────────────────────────────────

class TestJoinScoreDiff:
    def test_resolves_home_batter_to_bottom_half(self):
        lookup = _lookup([_lookup_row("LAA", "BAL", 5, "bottom", -7.0)])
        c = _make_cycle(ticker=_TICKER_LAA_HOME, inning=5)
        result = join_score_diff(c, {"2026-06-01": lookup})
        assert result == (-7.0, False)

    def test_resolves_away_batter_to_top_half(self):
        lookup = _lookup([_lookup_row("BAL", "LAA", 5, "top", 7.0)])
        c = _make_cycle(ticker=_TICKER_BAL_AWAY, inning=5)
        result = join_score_diff(c, {"2026-06-01": lookup})
        assert result == (7.0, True)

    def test_returns_none_when_game_date_not_in_lookups(self):
        c = _make_cycle(game_date="2099-01-01")
        assert join_score_diff(c, {}) is None

    def test_returns_none_when_inning_not_reconstructed(self):
        lookup = _lookup([_lookup_row("LAA", "BAL", 5, "bottom", -7.0)])
        c = _make_cycle(ticker=_TICKER_LAA_HOME, inning=9)
        assert join_score_diff(c, {"2026-06-01": lookup}) is None


# ── build_score_diff_lookups ─────────────────────────────────────────────────────

class TestBuildScoreDiffLookups:
    def test_calls_loader_once_per_unique_game_date(self, monkeypatch):
        calls = []

        def fake_loader(game_date):
            calls.append(game_date)
            return {}

        monkeypatch.setattr(flow_mod, "load_score_diff_lookup", fake_loader)
        cycles = [
            _make_cycle(game_date="2026-06-01"),
            _make_cycle(ticker="T2", game_date="2026-06-01"),
            _make_cycle(ticker="T3", game_date="2026-06-02"),
        ]
        lookups = build_score_diff_lookups(cycles)
        assert sorted(calls) == ["2026-06-01", "2026-06-02"]
        assert set(lookups.keys()) == {"2026-06-01", "2026-06-02"}


# ── compute_flow_bets: blowout-sustain state machine ────────────────────────────

class TestComputeFlowBets:
    def _lookup_for_home_trailing(self) -> dict[str, dict]:
        rows = [
            _lookup_row("LAA", "BAL", 3, "bottom", -7.0),
            _lookup_row("LAA", "BAL", 4, "bottom", -7.0),
            _lookup_row("LAA", "BAL", 5, "bottom", -7.0),
        ]
        return {"2026-06-01": _lookup(rows)}

    def test_not_yet_sustained_produces_no_bet(self):
        lookups = self._lookup_for_home_trailing()
        cycles = [
            _make_cycle(inning=3, ts="2026-06-01T01:00:00Z"),
            _make_cycle(inning=4, ts="2026-06-01T01:05:00Z"),
        ]
        bets = compute_flow_bets(cycles, lookups, run_threshold=6, sustain_innings=2)
        assert bets == []

    def test_sustained_blowout_produces_bet_with_trailing_mult(self):
        lookups = self._lookup_for_home_trailing()
        cycles = [
            _make_cycle(inning=3, ts="2026-06-01T01:00:00Z"),
            _make_cycle(inning=4, ts="2026-06-01T01:05:00Z"),
            _make_cycle(inning=5, ts="2026-06-01T01:10:00Z", h_so_far=0, ab_so_far=2,
                        batting_slot=3, ba_l10=0.30, mip=0.05, vig=0.0),
        ]
        bets = compute_flow_bets(cycles, lookups, run_threshold=6, sustain_innings=2)
        assert len(bets) == 1
        bet = bets[0]
        assert bet.player_trailing is True
        assert bet.ba_adjusted == pytest.approx(min(1.0, 0.30 * 1.15))
        ab_remaining = _compute_ab_remaining(2, 5, 3)
        expected_p_flow = p_hits_gte_threshold(0, 2, bet.ba_adjusted, ab_remaining)
        assert bet.p_flow == pytest.approx(expected_p_flow)
        assert bet.gross_edge == pytest.approx(expected_p_flow - 0.05 - 0.0)

    def test_leading_batter_gets_discount_mult(self):
        rows = [
            _lookup_row("LAA", "BAL", 3, "bottom", 7.0),
            _lookup_row("LAA", "BAL", 4, "bottom", 7.0),
            _lookup_row("LAA", "BAL", 5, "bottom", 7.0),
        ]
        lookups = {"2026-06-01": _lookup(rows)}
        cycles = [
            _make_cycle(inning=3, ts="2026-06-01T01:00:00Z"),
            _make_cycle(inning=4, ts="2026-06-01T01:05:00Z"),
            _make_cycle(inning=5, ts="2026-06-01T01:10:00Z", h_so_far=0, ab_so_far=2,
                        batting_slot=3, ba_l10=0.30, mip=0.60, vig=0.02),
        ]
        bets = compute_flow_bets(cycles, lookups, run_threshold=6, sustain_innings=2)
        assert len(bets) == 1
        assert bets[0].player_trailing is False
        assert bets[0].ba_adjusted == pytest.approx(min(1.0, 0.30 * 0.80))

    def test_blowout_gap_resets_start_inning(self):
        # Blowout at inning 3, closes at inning 4 (score_diff below threshold),
        # resumes at inning 5 -> must resatisfy the sustain window counting from
        # the inning-5 restart (qualifies at inning 7 = 5+2), not credit the
        # earlier inning-3 start (which would have qualified as early as inning 6).
        rows = [
            _lookup_row("LAA", "BAL", 3, "bottom", -7.0),
            _lookup_row("LAA", "BAL", 4, "bottom", -2.0),  # gap closes
            _lookup_row("LAA", "BAL", 5, "bottom", -7.0),  # blowout restarts
            _lookup_row("LAA", "BAL", 6, "bottom", -7.0),
            _lookup_row("LAA", "BAL", 7, "bottom", -7.0),
        ]
        lookups = {"2026-06-01": _lookup(rows)}
        cycles = [
            _make_cycle(inning=3, ts="2026-06-01T01:00:00Z"),
            _make_cycle(inning=4, ts="2026-06-01T01:05:00Z"),
            _make_cycle(inning=5, ts="2026-06-01T01:10:00Z"),
            _make_cycle(inning=6, ts="2026-06-01T01:15:00Z"),
            _make_cycle(inning=7, ts="2026-06-01T01:20:00Z", h_so_far=0, ab_so_far=2,
                        batting_slot=3, ba_l10=0.30, mip=0.05, vig=0.0),
        ]
        bets = compute_flow_bets(cycles, lookups, run_threshold=6, sustain_innings=2)
        assert len(bets) == 1
        assert bets[0].ticker == cycles[4].ticker

    def test_no_blowout_at_all_produces_no_bets(self):
        rows = [_lookup_row("LAA", "BAL", n, "bottom", -1.0) for n in range(3, 7)]
        lookups = {"2026-06-01": _lookup(rows)}
        cycles = [_make_cycle(inning=n, ts=f"2026-06-01T01:0{n}:00Z") for n in range(3, 7)]
        bets = compute_flow_bets(cycles, lookups, run_threshold=6, sustain_innings=2)
        assert bets == []

    def test_below_min_edge_produces_no_bet(self):
        lookups = self._lookup_for_home_trailing()
        cycles = [
            _make_cycle(inning=3, ts="2026-06-01T01:00:00Z"),
            _make_cycle(inning=4, ts="2026-06-01T01:05:00Z"),
            # p_flow at these inputs is ~0.119 (see test_sustained_blowout_produces_bet_...);
            # mip=0.10/vig=0.02 puts edge within a hair of zero, well under _MIN_EDGE.
            _make_cycle(inning=5, ts="2026-06-01T01:10:00Z", h_so_far=0, ab_so_far=2,
                        batting_slot=3, ba_l10=0.30, mip=0.10, vig=0.02),
        ]
        bets = compute_flow_bets(cycles, lookups, run_threshold=6, sustain_innings=2)
        assert bets == []

    def test_unparseable_ticker_is_skipped(self):
        cycles = [_make_cycle(ticker="not-a-ticker", inning=5)]
        bets = compute_flow_bets(cycles, {}, run_threshold=6, sustain_innings=2)
        assert bets == []


# ── dedupe_earliest_flow / resolve_flow_bets ────────────────────────────────────

class TestDedupAndResolve:
    def test_dedupe_one_per_ticker_earliest_wins(self):
        bets = [
            flow_mod.FlowBet(
                ticker="T1", player_id=1, player_name="X", game_date="2026-06-01",
                threshold=2, h_so_far=1, ba_l10=0.30, ba_adjusted=0.30, mip=0.30, vig=0.02,
                p_flow=0.60, gross_edge=0.28, player_trailing=True, ts="2026-06-01T02:00:00Z",
            ),
            flow_mod.FlowBet(
                ticker="T1", player_id=1, player_name="X", game_date="2026-06-01",
                threshold=2, h_so_far=0, ba_l10=0.30, ba_adjusted=0.30, mip=0.30, vig=0.02,
                p_flow=0.40, gross_edge=0.08, player_trailing=True, ts="2026-06-01T01:00:00Z",
            ),
        ]
        deduped = dedupe_earliest_flow(bets)
        assert len(deduped) == 1
        assert deduped[0].ts == "2026-06-01T01:00:00Z"

    def _make_bet(self, ticker="T1", player_id=1, game_date="2026-06-01", threshold=2,
                  p_flow=0.60, mip=0.30, vig=0.02) -> "flow_mod.FlowBet":
        return flow_mod.FlowBet(
            ticker=ticker, player_id=player_id, player_name="X", game_date=game_date,
            threshold=threshold, h_so_far=0, ba_l10=0.30, ba_adjusted=0.345, mip=mip, vig=vig,
            p_flow=p_flow, gross_edge=p_flow - mip - vig, player_trailing=True, ts="2026-06-01T01:00:00Z",
        )

    def test_resolve_yes_win(self):
        bet = self._make_bet(p_flow=0.60)
        resolved = resolve_flow_bets([bet], {(1, "2026-06-01"): 2.0})
        assert len(resolved) == 1
        assert resolved[0].direction == "YES"
        assert resolved[0].outcome == "WIN"

    def test_resolve_no_when_below_threshold_predicted(self):
        bet = self._make_bet(p_flow=0.30, mip=0.10)
        resolved = resolve_flow_bets([bet], {(1, "2026-06-01"): 3.0})
        assert resolved[0].direction == "NO"
        assert resolved[0].outcome == "LOSS"

    def test_resolve_drops_unresolved(self):
        bet = self._make_bet()
        assert resolve_flow_bets([bet], {}) == []


# ── evaluate_cell / run_grid_sweep / effect_existence_diagnostic ────────────────

class TestGridAndDiagnostic:
    def _full_setup(self):
        rows = [
            _lookup_row("LAA", "BAL", 3, "bottom", -7.0),
            _lookup_row("LAA", "BAL", 4, "bottom", -7.0),
            _lookup_row("LAA", "BAL", 5, "bottom", -7.0),
        ]
        lookups = {"2026-06-01": _lookup(rows)}
        cycles = [
            _make_cycle(ticker=_TICKER_LAA_HOME, player_id=1, inning=3, ts="2026-06-01T01:00:00Z"),
            _make_cycle(ticker=_TICKER_LAA_HOME, player_id=1, inning=4, ts="2026-06-01T01:05:00Z"),
            _make_cycle(ticker=_TICKER_LAA_HOME, player_id=1, inning=5, ts="2026-06-01T01:10:00Z",
                        h_so_far=0, ab_so_far=2, batting_slot=3, ba_l10=0.30, mip=0.05, vig=0.0),
        ]
        hits_cache = {(1, "2026-06-01"): 2.0}
        return cycles, lookups, hits_cache

    def test_evaluate_cell_shape(self):
        cycles, lookups, hits_cache = self._full_setup()
        cell = evaluate_cell(cycles, lookups, run_threshold=6, sustain_innings=2, hits_cache=hits_cache)
        assert cell["run_threshold"] == 6
        assert cell["sustain_innings"] == 2
        assert cell["n_qualifying_cycles"] == 1
        assert cell["n_unique_tickers"] == 1
        assert cell["n_resolved"] == 1
        assert cell["n_trailing"] == 1
        assert cell["n_leading"] == 0

    def test_grid_shape(self):
        grid = run_grid_sweep([], {}, {})
        assert len(grid) == len(RUN_THRESHOLD_GRID) * len(SUSTAIN_INNINGS_GRID)

    def test_effect_existence_diagnostic_splits_trailing_leading(self):
        cycles, lookups, hits_cache = self._full_setup()
        result = effect_existence_diagnostic(cycles, lookups, 6, 2, hits_cache)
        assert result["trailing"]["n"] == 1
        assert result["trailing"]["mean_ba_l10"] == pytest.approx(0.30)
        assert result["leading"]["n"] == 0


# ── main() — no-data graceful path only (no real network calls in this suite) ──

class TestMainNoData:
    def test_main_missing_cycle_log_returns_zero_without_ci(self, tmp_path, capsys):
        rc = main(["--cycle-log", str(tmp_path / "nope.jsonl"), "--no-save"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "BLOCKED" in captured.err

    def test_main_missing_cycle_log_returns_four_with_ci(self, tmp_path):
        rc = main(["--cycle-log", str(tmp_path / "nope.jsonl"), "--ci", "--no-save"])
        assert rc == 4

    def test_main_missing_cycle_log_saves_inconclusive_result(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        rc = main(["--cycle-log", str(tmp_path / "nope.jsonl")])
        assert rc == 0
        out_path = tmp_path / "exp_output" / "EXP-FLOW-MLB-01" / "EXP-FLOW-MLB-01_results.json"
        assert out_path.exists()
        result = json.loads(out_path.read_text())
        assert result["n_raw_cycles"] == 0
        assert result["verdict"] == V_INC
