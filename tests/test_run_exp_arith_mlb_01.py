"""Tests for scripts/run_exp_arith_mlb_01.py — T-219 / EXP-ARITH-MLB-01 backtest runner.

Covers: cycle-log JSONL loading (incl. malformed-line tolerance), h_needed/qualifies
filtering, direction inference, earliest-wins ticker dedup, resolution-cache building
(fake resolver — no real network calls in this suite), outcome/pnl computation,
EV stats, ADR-0024 tiering, edge monotonicity (Fisher), grid sweep shape, and the
no-cycle-log-file graceful path through main().
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("BOT_ENV", "paper")

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_exp_arith_mlb_01 import (
    ArithCycle,
    ResolvedBet,
    ENTRY_WINDOW_GRID,
    CONFIDENCE_GATE_GRID,
    _ARITH_ENTRY_WINDOW_DEFAULT,
    _ARITH_CONFIDENCE_GATE_DEFAULT,
    _MIN_EDGE,
    MIN_N,
    V_INC,
    V_DIR_POS,
    V_DIR_NEG,
    E_MONO,
    E_ANTI,
    E_INC,
    load_cycle_log,
    h_needed,
    qualifies,
    direction_of,
    dedupe_earliest,
    build_resolution_cache,
    kalshi_fee,
    compute_pnl_unit,
    resolve_bets,
    ev_stats,
    adr0024_tier,
    ev_verdict,
    _fisher_pvalue,
    edge_monotonicity,
    evaluate_cell,
    run_grid_sweep,
    main,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_cycle(
    ticker="KXMLBHIT-NYY-Soto-2-20260601",
    player_id=660670,
    player_name="Juan Soto",
    game_date="2026-06-01",
    threshold=2,
    h_so_far=1,
    p_t4=0.85,
    mip=0.60,
    vig=0.02,
    gross_edge=None,
    ts="2026-06-01T01:00:00Z",
) -> ArithCycle:
    if gross_edge is None:
        gross_edge = p_t4 - mip - vig
    return ArithCycle(
        ticker=ticker, player_id=player_id, player_name=player_name,
        game_date=game_date, threshold=threshold, h_so_far=h_so_far,
        p_t4=p_t4, mip=mip, vig=vig, gross_edge=gross_edge, ts=ts,
    )


def _write_cycle_log(path: Path, records: list[dict]) -> None:
    with open(path, "w") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")


def _cycle_record(**overrides) -> dict:
    rec = {
        "ts": "2026-06-01T01:00:00Z",
        "cycle_id": "CL-01",
        "session_id": "TEST",
        "game_date": "2026-06-01",
        "ticker": "KXMLBHIT-NYY-Soto-2-20260601",
        "player_name": "Juan Soto",
        "player_id": 660670,
        "threshold": 2,
        "p_t4": 0.85,
        "mip": 0.60,
        "vig": 0.02,
        "gross_edge": 0.23,
        "net_edge": 0.20,
        "ba_l10": 0.30,
        "h_so_far": 1,
        "ab_so_far": 2,
        "ab_remaining": 2,
        "inning": 6,
        "batting_slot": 3,
    }
    rec.update(overrides)
    return rec


# ── load_cycle_log ─────────────────────────────────────────────────────────────

class TestLoadCycleLog:
    def test_missing_file_returns_empty(self, tmp_path):
        assert load_cycle_log(tmp_path / "nope.jsonl") == []

    def test_loads_valid_records(self, tmp_path):
        path = tmp_path / "cl.jsonl"
        _write_cycle_log(path, [_cycle_record(), _cycle_record(ticker="T2", player_id=2)])
        cycles = load_cycle_log(path)
        assert len(cycles) == 2
        assert cycles[0].ticker == "KXMLBHIT-NYY-Soto-2-20260601"
        assert cycles[0].player_id == 660670
        assert cycles[0].game_date == "2026-06-01"

    def test_skips_malformed_lines(self, tmp_path):
        path = tmp_path / "cl.jsonl"
        with open(path, "w") as fh:
            fh.write(json.dumps(_cycle_record()) + "\n")
            fh.write("not json at all\n")
            fh.write(json.dumps({"ticker": "missing_fields"}) + "\n")  # KeyError -> skip
            fh.write("\n")  # blank line -> skip
            fh.write(json.dumps(_cycle_record(ticker="T3", player_id=3)) + "\n")
        cycles = load_cycle_log(path)
        assert len(cycles) == 2
        assert {c.ticker for c in cycles} == {"KXMLBHIT-NYY-Soto-2-20260601", "T3"}


# ── h_needed / qualifies / direction ────────────────────────────────────────────

class TestQualification:
    def test_h_needed(self):
        c = _make_cycle(threshold=2, h_so_far=1)
        assert h_needed(c) == 1

    def test_qualifies_within_entry_window_and_gate(self):
        c = _make_cycle(threshold=2, h_so_far=1, p_t4=0.85, mip=0.60, vig=0.02)
        assert qualifies(c, entry_window=1, confidence_gate=0.80)

    def test_rejects_h_needed_zero(self):
        c = _make_cycle(threshold=2, h_so_far=2, p_t4=0.99, mip=0.10, vig=0.02)
        assert not qualifies(c, entry_window=1, confidence_gate=0.80)

    def test_rejects_outside_entry_window(self):
        c = _make_cycle(threshold=3, h_so_far=1, p_t4=0.85, mip=0.10, vig=0.02)  # h_needed=2
        assert not qualifies(c, entry_window=1, confidence_gate=0.80)
        assert qualifies(c, entry_window=2, confidence_gate=0.80)

    def test_rejects_below_confidence_gate(self):
        c = _make_cycle(threshold=2, h_so_far=1, p_t4=0.75, mip=0.60, vig=0.02)
        assert not qualifies(c, entry_window=1, confidence_gate=0.80)

    def test_rejects_below_min_edge(self):
        c = _make_cycle(threshold=2, h_so_far=1, p_t4=0.85, mip=0.83, vig=0.01)  # edge ~0.01
        assert not qualifies(c, entry_window=1, confidence_gate=0.80)

    def test_direction_yes_above_half(self):
        c = _make_cycle(p_t4=0.85)
        assert direction_of(c) == "YES"

    def test_direction_no_below_half(self):
        c = _make_cycle(p_t4=0.30, mip=0.10, vig=0.01)
        assert direction_of(c) == "NO"


# ── dedupe_earliest ──────────────────────────────────────────────────────────────

class TestDedup:
    def test_one_per_ticker_earliest_wins(self):
        cycles = [
            _make_cycle(ticker="T1", ts="2026-06-01T02:00:00Z", h_so_far=1),
            _make_cycle(ticker="T1", ts="2026-06-01T01:00:00Z", h_so_far=0),  # earlier
            _make_cycle(ticker="T2", ts="2026-06-01T01:30:00Z"),
        ]
        deduped = dedupe_earliest(cycles)
        assert len(deduped) == 2
        t1 = next(c for c in deduped if c.ticker == "T1")
        assert t1.ts == "2026-06-01T01:00:00Z"
        assert t1.h_so_far == 0


# ── resolution cache / pnl / outcome ────────────────────────────────────────────

class TestResolution:
    def test_build_resolution_cache_dedupes_pairs_and_calls_resolver_once_each(self):
        cycles = [
            _make_cycle(ticker="T1", player_id=1, game_date="2026-06-01"),
            _make_cycle(ticker="T1b", player_id=1, game_date="2026-06-01"),  # same pair
            _make_cycle(ticker="T2", player_id=2, game_date="2026-06-01"),
        ]
        calls = []

        def fake_resolver(player_id, game_date):
            calls.append((player_id, game_date))
            return {1: 2.0, 2: 0.0}.get(player_id)

        cache = build_resolution_cache(cycles, fake_resolver)
        assert cache == {(1, "2026-06-01"): 2.0, (2, "2026-06-01"): 0.0}
        assert len(calls) == 2  # one per unique (player_id, game_date), not per cycle

    def test_kalshi_fee_formula(self):
        assert kalshi_fee(0.5) == pytest.approx(0.07 * 0.5 * 0.5)

    def test_compute_pnl_unit_yes_win(self):
        pnl = compute_pnl_unit("YES", mip=0.60, vig=0.02, won=True)
        assert pnl == pytest.approx(1.0 - (0.60 + 0.01))

    def test_compute_pnl_unit_yes_loss(self):
        pnl = compute_pnl_unit("YES", mip=0.60, vig=0.02, won=False)
        assert pnl == pytest.approx(-(0.60 + 0.01))

    def test_resolve_bets_yes_win_when_actual_meets_threshold(self):
        c = _make_cycle(threshold=2, h_so_far=1, p_t4=0.85, mip=0.60, vig=0.02)
        cache = {(c.player_id, c.game_date): 2.0}  # actual_hits == threshold
        bets = resolve_bets([c], cache)
        assert len(bets) == 1
        assert bets[0].outcome == "WIN"
        assert bets[0].direction == "YES"

    def test_resolve_bets_yes_loss_when_actual_below_threshold(self):
        c = _make_cycle(threshold=2, h_so_far=1, p_t4=0.85, mip=0.60, vig=0.02)
        cache = {(c.player_id, c.game_date): 1.0}
        bets = resolve_bets([c], cache)
        assert bets[0].outcome == "LOSS"

    def test_resolve_bets_drops_unresolved(self):
        c = _make_cycle()
        cache = {}  # no entry -> None
        assert resolve_bets([c], cache) == []

    def test_resolve_bets_no_direction_win_when_actual_below_threshold(self):
        c = _make_cycle(threshold=2, h_so_far=1, p_t4=0.30, mip=0.10, vig=0.02)  # direction NO
        cache = {(c.player_id, c.game_date): 1.0}  # actual < threshold -> NO wins
        bets = resolve_bets([c], cache)
        assert bets[0].direction == "NO"
        assert bets[0].outcome == "WIN"


# ── EV stats / tier / verdict / monotonicity ────────────────────────────────────

def _make_bet(outcome="WIN", pnl=0.40, gross_edge=0.10, ticker="T1") -> ResolvedBet:
    return ResolvedBet(
        ticker=ticker, direction="YES", mip=0.5, vig=0.02, model_p=0.85,
        gross_edge=gross_edge, outcome=outcome, pnl=pnl,
        game_date="2026-06-01", threshold=2, player_name="X",
    )


class TestEvAndVerdict:
    def test_ev_stats_empty(self):
        assert ev_stats([])["n"] == 0

    def test_ev_stats_basic(self):
        bets = [_make_bet(outcome="WIN", pnl=1.0), _make_bet(outcome="LOSS", pnl=-1.0)]
        stats = ev_stats(bets)
        assert stats["n"] == 2
        assert stats["win_rate"] == 0.5
        assert stats["total_pnl"] == pytest.approx(0.0)

    def test_adr0024_tier_below_tier1(self):
        tier = adr0024_tier(n=10, ev_per_bet=0.05)
        assert not tier["at_tier1"]
        assert not tier["at_tier2"]

    def test_adr0024_tier_diagnostic_sprint(self):
        tier = adr0024_tier(n=200, ev_per_bet=-0.10)
        assert tier["at_tier1"]
        assert tier["diagnostic_sprint"]

    def test_ev_verdict_inconclusive_below_min_n(self):
        tier = adr0024_tier(n=5, ev_per_bet=0.10)
        assert ev_verdict(n=5, ev_per_bet=0.10, tier=tier, fisher_pvalue=0.01) == V_INC

    def test_ev_verdict_directional_positive(self):
        tier = adr0024_tier(n=30, ev_per_bet=0.10)
        assert ev_verdict(n=30, ev_per_bet=0.10, tier=tier, fisher_pvalue=0.50) == V_DIR_POS

    def test_ev_verdict_directional_negative(self):
        tier = adr0024_tier(n=30, ev_per_bet=-0.01)
        assert ev_verdict(n=30, ev_per_bet=-0.01, tier=tier, fisher_pvalue=0.50) == V_DIR_NEG

    def test_edge_monotonicity_inconclusive_below_min_n(self):
        mono = edge_monotonicity([_make_bet()] * 3)
        assert mono["verdict"] == E_INC
        assert "reason" in mono

    def test_edge_monotonicity_monotonic_signal(self):
        pos = [_make_bet(outcome="WIN", gross_edge=0.10, ticker=f"P{i}") for i in range(15)]
        neg = [_make_bet(outcome="LOSS", gross_edge=-0.10, ticker=f"N{i}") for i in range(15)]
        mono = edge_monotonicity(pos + neg, alpha=0.10)
        assert mono["verdict"] == E_MONO

    def test_edge_monotonicity_anti_predictive_signal(self):
        pos = [_make_bet(outcome="LOSS", gross_edge=0.10, ticker=f"P{i}") for i in range(15)]
        neg = [_make_bet(outcome="WIN", gross_edge=-0.10, ticker=f"N{i}") for i in range(15)]
        mono = edge_monotonicity(pos + neg, alpha=0.10)
        assert mono["verdict"] == E_ANTI


# ── Grid sweep / evaluate_cell ──────────────────────────────────────────────────

class TestGridSweep:
    def test_grid_shape(self):
        cache: dict = {}
        grid = run_grid_sweep([], cache)
        assert len(grid) == len(ENTRY_WINDOW_GRID) * len(CONFIDENCE_GATE_GRID)

    def test_evaluate_cell_counts_qualifying_and_resolved(self):
        cycles = [
            _make_cycle(ticker="T1", player_id=1, threshold=2, h_so_far=1, p_t4=0.85, mip=0.60, vig=0.02),
            _make_cycle(ticker="T2", player_id=2, threshold=1, h_so_far=0, p_t4=0.90, mip=0.70, vig=0.02),
            _make_cycle(ticker="T3", player_id=3, threshold=3, h_so_far=1, p_t4=0.60, mip=0.10, vig=0.02),  # h_needed=2
        ]
        cache = {(1, "2026-06-01"): 2.0, (2, "2026-06-01"): 1.0, (3, "2026-06-01"): 4.0}
        cell = evaluate_cell(cycles, entry_window=1, confidence_gate=0.80, hits_cache=cache)
        assert cell["n_qualifying_cycles"] == 2
        assert cell["n_resolved"] == 2
        assert cell["entry_window"] == 1
        assert cell["confidence_gate"] == 0.80

    def test_evaluate_cell_wider_window_admits_more(self):
        cycles = [
            _make_cycle(ticker="T3", player_id=3, threshold=3, h_so_far=1, p_t4=0.60, mip=0.10, vig=0.02),  # h_needed=2
        ]
        cache = {(3, "2026-06-01"): 4.0}
        narrow = evaluate_cell(cycles, entry_window=1, confidence_gate=0.50, hits_cache=cache)
        wide = evaluate_cell(cycles, entry_window=2, confidence_gate=0.50, hits_cache=cache)
        assert narrow["n_qualifying_cycles"] == 0
        assert wide["n_qualifying_cycles"] == 1


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
        out_path = tmp_path / "exp_output" / "EXP-ARITH-MLB-01" / "EXP-ARITH-MLB-01_results.json"
        assert out_path.exists()
        result = json.loads(out_path.read_text())
        assert result["n_raw_cycles"] == 0
        assert result["verdict"] == V_INC
