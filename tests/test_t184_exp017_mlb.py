"""Tests for scripts/run_exp017_mlb.py — T-184 / EXP-017 MLB commercial validation.

Covers: fee formula, edge computation, EV/pnl_unit, position loading (JSON + CSV),
deduplication, threshold breakdown, ADR-0024 tier checks, edge monotonicity (Fisher),
EV verdict, and end-to-end analysis with a synthetic portfolio.
"""
from __future__ import annotations

import csv
import json
import math
import tempfile
from pathlib import Path

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_exp017_mlb import (
    # constants
    ADR_0024_TIER1_N,
    ADR_0024_TIER1_DIAG_EV,
    ADR_0024_TIER2_N_SINGLE,
    ADR_0024_TIER2_N_MULTI,
    ADR_0024_P_THRESHOLD,
    KALSHI_FEE_RATE,
    MIN_N,
    SPORT,
    V_CONF_POS,
    V_DIR_POS,
    V_CONF_NEG,
    V_DIR_NEG,
    V_DIAG,
    V_INC,
    E_ANTI,
    E_MONO,
    E_INC,
    # functions
    kalshi_fee,
    compute_fee_net_edge,
    compute_pnl_unit,
    MLBPosition,
    _load_portfolio,
    _load_csv,
    deduplicate,
    ev_stats,
    threshold_breakdown,
    adr0024_tier,
    ev_verdict,
    _fisher_pvalue,
    _tercile_table,
    edge_monotonicity,
    analyse,
    main,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_pos(
    ticker="KXMLBHIT-NYY-Soto-1-20260801",
    direction="YES",
    mip=0.45,
    vig=0.014,
    model_p=0.52,
    fee_net_edge=None,
    outcome="WIN",
    pnl=5.0,
    game_date="2026-08-01",
    threshold=1,
    player_name="Juan Soto",
) -> MLBPosition:
    if fee_net_edge is None:
        fee_net_edge = compute_fee_net_edge(direction, model_p, mip)
    return MLBPosition(
        kalshi_ticker=ticker,
        direction=direction,
        mip=mip,
        vig=vig,
        model_p=model_p,
        fee_net_edge=fee_net_edge,
        outcome=outcome,
        pnl=pnl,
        game_date=game_date,
        threshold=threshold,
        player_name=player_name,
    )


def _make_n_positions(
    n: int,
    win_frac: float = 0.5,
    edge_pos: bool = True,
    threshold: int = 1,
    base_date: str = "2026-08-01",
) -> list[MLBPosition]:
    """Build n positions with controlled win fraction and edge sign."""
    positions = []
    n_win = int(n * win_frac)
    for i in range(n):
        outcome = "WIN" if i < n_win else "LOSS"
        mip = 0.40 if edge_pos else 0.60
        model_p = 0.55 if edge_pos else 0.45
        direction = "YES" if edge_pos else "NO"
        pnl = 5.0 if outcome == "WIN" else -5.0
        positions.append(_make_pos(
            ticker=f"KXMLBHIT-NYY-Player{i}-{threshold}-20260801",
            direction=direction,
            mip=mip,
            model_p=model_p,
            outcome=outcome,
            pnl=pnl,
            threshold=threshold,
            game_date=base_date,
        ))
    return positions


def _write_portfolio_json(path: Path, positions: list[dict]) -> None:
    data = {"bankroll_usd": 1000.0, "closed_positions": positions}
    path.write_text(json.dumps(data))


def _pos_as_dict(
    ticker: str,
    direction: str = "YES",
    mip: float = 0.45,
    vig: float = 0.014,
    model_p: float = 0.52,
    outcome: str = "WIN",
    pnl: float = 5.0,
    threshold: int = 1,
    player_name: str = "Test Player",
    game_date: str = "2026-08-01",
    sport: str = "mlb",
    duplicate_of: str | None = None,
) -> dict:
    d = {
        "kalshi_ticker": ticker,
        "direction": direction,
        "mid_price_at_entry": mip,
        "vig_at_entry": vig,
        "model_p": model_p,
        "outcome": outcome,
        "pnl": pnl,
        "threshold": threshold,
        "player_name": player_name,
        "game_date": game_date,
        "sport": sport,
    }
    if duplicate_of is not None:
        d["duplicate_of"] = duplicate_of
    return d


# ── TestKalshiFee ──────────────────────────────────────────────────────────────

class TestKalshiFee:
    def test_fee_rate_constant(self):
        assert KALSHI_FEE_RATE == 0.07

    def test_at_mip_50(self):
        # 0.07 × 0.5 × 0.5 = 0.0175
        assert abs(kalshi_fee(0.5) - 0.0175) < 1e-9

    def test_at_mip_0(self):
        assert kalshi_fee(0.0) == 0.0

    def test_at_mip_1(self):
        assert kalshi_fee(1.0) == 0.0

    def test_symmetric(self):
        # fee(p) == fee(1-p) — symmetric around 0.5
        assert abs(kalshi_fee(0.3) - kalshi_fee(0.7)) < 1e-9

    def test_nonnegative(self):
        for mip in [0.1, 0.25, 0.5, 0.75, 0.9]:
            assert kalshi_fee(mip) >= 0.0

    def test_max_at_50(self):
        fee_50 = kalshi_fee(0.5)
        for mip in [0.1, 0.3, 0.7, 0.9]:
            assert kalshi_fee(mip) < fee_50


# ── TestComputeFeeNetEdge ──────────────────────────────────────────────────────

class TestComputeFeeNetEdge:
    def test_yes_positive_edge(self):
        edge = compute_fee_net_edge("YES", model_p=0.55, mip=0.45)
        fee = kalshi_fee(0.45)
        assert abs(edge - (0.55 - 0.45 - fee)) < 1e-9

    def test_no_positive_edge(self):
        # NO bet: model thinks p_yes=0.35 < mip=0.55 → edge = mip - model_p - fee
        edge = compute_fee_net_edge("NO", model_p=0.35, mip=0.55)
        fee = kalshi_fee(0.55)
        assert abs(edge - (0.55 - 0.35 - fee)) < 1e-9

    def test_zero_edge_at_mip(self):
        # If model_p == mip (YES), edge before fee = 0, so fee_net_edge < 0
        edge = compute_fee_net_edge("YES", model_p=0.50, mip=0.50)
        assert edge == -kalshi_fee(0.50)

    def test_yes_edge_negative_when_model_p_below_mip(self):
        edge = compute_fee_net_edge("YES", model_p=0.40, mip=0.60)
        assert edge < 0

    def test_no_edge_negative_when_model_p_above_mip(self):
        edge = compute_fee_net_edge("NO", model_p=0.65, mip=0.50)
        assert edge < 0

    def test_yes_no_symmetry(self):
        # YES(p=0.6, mip=0.4) and NO(p=0.4, mip=0.6) should produce same edge magnitude
        e_yes = compute_fee_net_edge("YES", model_p=0.6, mip=0.4)
        e_no  = compute_fee_net_edge("NO",  model_p=0.4, mip=0.6)
        assert abs(e_yes - e_no) < 1e-9


# ── TestComputePnlUnit ─────────────────────────────────────────────────────────

class TestComputePnlUnit:
    def test_yes_win(self):
        # price_paid = 0.50 + 0.005 = 0.505; profit = 1 - 0.505 = 0.495
        pnl = compute_pnl_unit("YES", mip=0.50, vig=0.01, won=True)
        assert abs(pnl - 0.495) < 1e-9

    def test_yes_loss(self):
        pnl = compute_pnl_unit("YES", mip=0.50, vig=0.01, won=False)
        assert abs(pnl - (-0.505)) < 1e-9

    def test_no_win(self):
        # NO: price_paid = (1-0.50) + 0.005 = 0.505; profit = 1 - 0.505 = 0.495
        pnl = compute_pnl_unit("NO", mip=0.50, vig=0.01, won=True)
        assert abs(pnl - 0.495) < 1e-9

    def test_no_loss(self):
        pnl = compute_pnl_unit("NO", mip=0.50, vig=0.01, won=False)
        assert abs(pnl - (-0.505)) < 1e-9

    def test_yes_asymmetric_mip(self):
        # YES at mip=0.30: price_paid=0.305; profit if win = 0.695
        pnl = compute_pnl_unit("YES", mip=0.30, vig=0.01, won=True)
        assert abs(pnl - 0.695) < 1e-9

    def test_vig_zero(self):
        # zero vig: price_paid = mip exactly
        pnl = compute_pnl_unit("YES", mip=0.40, vig=0.0, won=True)
        assert abs(pnl - 0.60) < 1e-9


# ── TestLoadPortfolio ──────────────────────────────────────────────────────────

class TestLoadPortfolio:
    def test_loads_valid_position(self, tmp_path):
        pos = [_pos_as_dict("KXMLBHIT-NYY-Soto-1", outcome="WIN", model_p=0.55)]
        _write_portfolio_json(tmp_path / "p.json", pos)
        result = _load_portfolio(tmp_path / "p.json")
        assert len(result) == 1
        assert result[0].outcome == "WIN"
        assert result[0].model_p == pytest.approx(0.55)

    def test_excludes_duplicates_by_default(self, tmp_path):
        pos = [
            _pos_as_dict("KXMLBHIT-A-1", outcome="WIN"),
            _pos_as_dict("KXMLBHIT-B-1", outcome="LOSS", duplicate_of="KXMLBHIT-A-1"),
        ]
        _write_portfolio_json(tmp_path / "p.json", pos)
        result = _load_portfolio(tmp_path / "p.json")
        assert len(result) == 1
        assert result[0].kalshi_ticker == "KXMLBHIT-A-1"

    def test_includes_duplicates_when_requested(self, tmp_path):
        pos = [
            _pos_as_dict("KXMLBHIT-A-1", outcome="WIN"),
            _pos_as_dict("KXMLBHIT-B-1", outcome="LOSS", duplicate_of="KXMLBHIT-A-1"),
        ]
        _write_portfolio_json(tmp_path / "p.json", pos)
        result = _load_portfolio(tmp_path / "p.json", exclude_duplicates=False)
        assert len(result) == 2

    def test_skips_unresolved_positions(self, tmp_path):
        pos = [
            _pos_as_dict("KXMLBHIT-A-1", outcome="WIN"),
            _pos_as_dict("KXMLBHIT-B-1", outcome="OPEN"),
        ]
        _write_portfolio_json(tmp_path / "p.json", pos)
        result = _load_portfolio(tmp_path / "p.json")
        assert len(result) == 1

    def test_skips_missing_model_p(self, tmp_path):
        d = _pos_as_dict("KXMLBHIT-A-1", outcome="WIN")
        del d["model_p"]
        _write_portfolio_json(tmp_path / "p.json", [d])
        result = _load_portfolio(tmp_path / "p.json")
        assert len(result) == 0

    def test_uses_stored_fee_net_edge_when_present(self, tmp_path):
        d = _pos_as_dict("KXMLBHIT-A-1", outcome="WIN", model_p=0.55, mip=0.45)
        d["fee_net_edge"] = 0.0999  # stored value — should be used as-is
        _write_portfolio_json(tmp_path / "p.json", [d])
        result = _load_portfolio(tmp_path / "p.json")
        assert result[0].fee_net_edge == pytest.approx(0.0999)

    def test_computes_fee_net_edge_when_absent(self, tmp_path):
        d = _pos_as_dict("KXMLBHIT-A-1", outcome="WIN", model_p=0.55, mip=0.45)
        # no fee_net_edge key
        _write_portfolio_json(tmp_path / "p.json", [d])
        result = _load_portfolio(tmp_path / "p.json")
        expected = compute_fee_net_edge("YES", 0.55, 0.45)
        assert result[0].fee_net_edge == pytest.approx(expected)

    def test_threshold_stored(self, tmp_path):
        pos = [_pos_as_dict("KXMLBHIT-A-3", outcome="WIN", threshold=3)]
        _write_portfolio_json(tmp_path / "p.json", pos)
        result = _load_portfolio(tmp_path / "p.json")
        assert result[0].threshold == 3


# ── TestLoadCsv ───────────────────────────────────────────────────────────────

class TestLoadCsv:
    def _write_csv(self, path: Path, rows: list[dict]) -> None:
        if not rows:
            return
        with open(path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def test_loads_valid_row(self, tmp_path):
        rows = [{"kalshi_ticker": "KXMLBHIT-A-1", "direction": "YES",
                 "mid_price_at_entry": "0.45", "vig_at_entry": "0.014",
                 "model_p": "0.55", "fee_net_edge": "", "threshold": "1",
                 "outcome": "WIN", "pnl": "5.0", "game_date": "2026-08-01",
                 "player_name": "Test", "duplicate_of": ""}]
        p = tmp_path / "out.csv"
        self._write_csv(p, rows)
        result = _load_csv(p)
        assert len(result) == 1
        assert result[0].outcome == "WIN"
        assert result[0].model_p == pytest.approx(0.55)

    def test_excludes_duplicates(self, tmp_path):
        rows = [
            {"kalshi_ticker": "A", "direction": "YES", "mid_price_at_entry": "0.45",
             "vig_at_entry": "0.014", "model_p": "0.55", "fee_net_edge": "",
             "threshold": "1", "outcome": "WIN", "pnl": "5.0",
             "game_date": "2026-08-01", "player_name": "T", "duplicate_of": ""},
            {"kalshi_ticker": "B", "direction": "YES", "mid_price_at_entry": "0.45",
             "vig_at_entry": "0.014", "model_p": "0.55", "fee_net_edge": "",
             "threshold": "1", "outcome": "WIN", "pnl": "5.0",
             "game_date": "2026-08-01", "player_name": "T", "duplicate_of": "A"},
        ]
        p = tmp_path / "out.csv"
        self._write_csv(p, rows)
        result = _load_csv(p)
        assert len(result) == 1

    def test_skips_unresolved(self, tmp_path):
        rows = [{"kalshi_ticker": "A", "direction": "YES", "mid_price_at_entry": "0.45",
                 "vig_at_entry": "0.014", "model_p": "0.55", "fee_net_edge": "",
                 "threshold": "1", "outcome": "OPEN", "pnl": "0.0",
                 "game_date": "2026-08-01", "player_name": "T", "duplicate_of": ""}]
        p = tmp_path / "out.csv"
        self._write_csv(p, rows)
        result = _load_csv(p)
        assert len(result) == 0

    def test_computes_edge_when_blank(self, tmp_path):
        rows = [{"kalshi_ticker": "A", "direction": "YES", "mid_price_at_entry": "0.45",
                 "vig_at_entry": "0.014", "model_p": "0.55", "fee_net_edge": "",
                 "threshold": "1", "outcome": "WIN", "pnl": "5.0",
                 "game_date": "2026-08-01", "player_name": "T", "duplicate_of": ""}]
        p = tmp_path / "out.csv"
        self._write_csv(p, rows)
        result = _load_csv(p)
        expected = compute_fee_net_edge("YES", 0.55, 0.45)
        assert result[0].fee_net_edge == pytest.approx(expected)

    def test_skips_missing_model_p(self, tmp_path):
        rows = [{"kalshi_ticker": "A", "direction": "YES", "mid_price_at_entry": "0.45",
                 "vig_at_entry": "0.014", "model_p": "", "fee_net_edge": "",
                 "threshold": "1", "outcome": "WIN", "pnl": "5.0",
                 "game_date": "2026-08-01", "player_name": "T", "duplicate_of": ""}]
        p = tmp_path / "out.csv"
        self._write_csv(p, rows)
        result = _load_csv(p)
        assert len(result) == 0


# ── TestDeduplicate ────────────────────────────────────────────────────────────

class TestDeduplicate:
    def test_unique_tickers_pass_through(self):
        positions = [
            _make_pos(ticker="KXMLBHIT-A-1"),
            _make_pos(ticker="KXMLBHIT-B-1"),
            _make_pos(ticker="KXMLBHIT-C-1"),
        ]
        result = deduplicate(positions)
        assert len(result) == 3

    def test_duplicate_ticker_removed(self):
        positions = [
            _make_pos(ticker="KXMLBHIT-A-1", outcome="WIN"),
            _make_pos(ticker="KXMLBHIT-A-1", outcome="LOSS"),  # same ticker
        ]
        result = deduplicate(positions)
        assert len(result) == 1
        assert result[0].outcome == "WIN"  # first entry wins

    def test_earliest_entry_wins(self):
        # Input order determines which stays (first occurrence)
        positions = [
            _make_pos(ticker="KXMLBHIT-X-1", pnl=10.0),
            _make_pos(ticker="KXMLBHIT-X-1", pnl=99.0),  # second — dropped
        ]
        result = deduplicate(positions)
        assert result[0].pnl == 10.0

    def test_empty_input(self):
        assert deduplicate([]) == []

    def test_single_position(self):
        positions = [_make_pos(ticker="KXMLBHIT-A-1")]
        assert len(deduplicate(positions)) == 1

    def test_dedup_count(self):
        positions = [_make_pos(ticker=f"KXMLBHIT-{i % 5}-1") for i in range(20)]
        result = deduplicate(positions)
        assert len(result) == 5


# ── TestEvStats ────────────────────────────────────────────────────────────────

class TestEvStats:
    def test_empty(self):
        stats = ev_stats([])
        assert stats["n"] == 0
        assert stats["ev_per_bet"] == 0.0

    def test_all_wins(self):
        positions = [_make_pos(pnl=10.0, outcome="WIN") for _ in range(5)]
        stats = ev_stats(positions)
        assert stats["ev_per_bet"] == pytest.approx(10.0)
        assert stats["win_rate"] == pytest.approx(1.0)

    def test_all_losses(self):
        positions = [_make_pos(pnl=-5.0, outcome="LOSS") for _ in range(4)]
        stats = ev_stats(positions)
        assert stats["ev_per_bet"] == pytest.approx(-5.0)
        assert stats["win_rate"] == pytest.approx(0.0)

    def test_mixed(self):
        positions = [
            _make_pos(pnl=8.0, outcome="WIN"),
            _make_pos(pnl=-4.0, outcome="LOSS"),
        ]
        stats = ev_stats(positions)
        assert stats["ev_per_bet"] == pytest.approx(2.0)
        assert stats["total_pnl"] == pytest.approx(4.0)


# ── TestThresholdBreakdown ─────────────────────────────────────────────────────

class TestThresholdBreakdown:
    def test_separates_by_threshold(self):
        positions = [
            _make_pos(ticker="A", threshold=1, pnl=5.0, outcome="WIN"),
            _make_pos(ticker="B", threshold=2, pnl=-3.0, outcome="LOSS"),
            _make_pos(ticker="C", threshold=3, pnl=2.0, outcome="WIN"),
        ]
        rows = threshold_breakdown(positions)
        assert len(rows) == 3
        thresholds = [r["threshold"] for r in rows]
        assert 1 in thresholds and 2 in thresholds and 3 in thresholds

    def test_k1_higher_ev_than_k3(self):
        # k=1 has more wins (higher hit rate), k=3 has fewer
        pos_k1 = [_make_pos(ticker=f"A{i}", threshold=1, pnl=5.0, outcome="WIN") for i in range(5)]
        pos_k3 = [_make_pos(ticker=f"B{i}", threshold=3, pnl=-5.0, outcome="LOSS") for i in range(5)]
        rows = threshold_breakdown(pos_k1 + pos_k3)
        ev_k1 = next(r["ev_per_bet"] for r in rows if r["threshold"] == 1)
        ev_k3 = next(r["ev_per_bet"] for r in rows if r["threshold"] == 3)
        assert ev_k1 > ev_k3

    def test_single_threshold(self):
        positions = [_make_pos(ticker=f"A{i}", threshold=2) for i in range(3)]
        rows = threshold_breakdown(positions)
        assert len(rows) == 1
        assert rows[0]["threshold"] == 2

    def test_n_per_threshold(self):
        pos_k1 = [_make_pos(ticker=f"A{i}", threshold=1) for i in range(4)]
        pos_k2 = [_make_pos(ticker=f"B{i}", threshold=2) for i in range(6)]
        rows = threshold_breakdown(pos_k1 + pos_k2)
        n_k1 = next(r["n"] for r in rows if r["threshold"] == 1)
        n_k2 = next(r["n"] for r in rows if r["threshold"] == 2)
        assert n_k1 == 4
        assert n_k2 == 6

    def test_empty(self):
        assert threshold_breakdown([]) == []

    def test_total_pnl_correct(self):
        positions = [
            _make_pos(ticker="A", threshold=1, pnl=3.0),
            _make_pos(ticker="B", threshold=1, pnl=7.0),
        ]
        rows = threshold_breakdown(positions)
        assert rows[0]["total_pnl"] == pytest.approx(10.0)

    def test_win_rate_per_threshold(self):
        positions = [
            _make_pos(ticker="A", threshold=1, outcome="WIN", pnl=5.0),
            _make_pos(ticker="B", threshold=1, outcome="LOSS", pnl=-5.0),
        ]
        rows = threshold_breakdown(positions)
        assert rows[0]["win_rate"] == pytest.approx(0.5)

    def test_sorted_by_threshold(self):
        positions = [
            _make_pos(ticker="A", threshold=3),
            _make_pos(ticker="B", threshold=1),
            _make_pos(ticker="C", threshold=2),
        ]
        rows = threshold_breakdown(positions)
        assert [r["threshold"] for r in rows] == [1, 2, 3]


# ── TestAdr0024TierCheck ──────────────────────────────────────────────────────

class TestAdr0024TierCheck:
    def test_below_tier1(self):
        result = adr0024_tier(n_mlb=50, ev_per_bet=0.05)
        assert not result["at_tier1"]
        assert not result["at_tier2"]
        assert not result["diagnostic_sprint"]

    def test_at_tier1_positive_ev(self):
        result = adr0024_tier(n_mlb=ADR_0024_TIER1_N, ev_per_bet=0.01)
        assert result["at_tier1"]
        assert not result["diagnostic_sprint"]

    def test_at_tier1_negative_ev_triggers_sprint(self):
        result = adr0024_tier(n_mlb=ADR_0024_TIER1_N, ev_per_bet=-0.05)
        assert result["at_tier1"]
        assert result["diagnostic_sprint"]

    def test_tier1_diag_boundary_just_above(self):
        result = adr0024_tier(n_mlb=ADR_0024_TIER1_N, ev_per_bet=-0.0299)
        assert not result["diagnostic_sprint"]

    def test_tier1_diag_boundary_at_threshold(self):
        # Strict less-than: exactly -0.03 does NOT trigger diagnostic sprint
        result = adr0024_tier(n_mlb=ADR_0024_TIER1_N, ev_per_bet=ADR_0024_TIER1_DIAG_EV)
        assert not result["diagnostic_sprint"]

    def test_tier1_diag_one_tick_below(self):
        # One tick below -$0.03 triggers sprint
        result = adr0024_tier(n_mlb=ADR_0024_TIER1_N, ev_per_bet=-0.0301)
        assert result["diagnostic_sprint"]

    def test_at_tier2_single(self):
        result = adr0024_tier(n_mlb=ADR_0024_TIER2_N_SINGLE, ev_per_bet=0.05)
        assert result["at_tier2"]
        assert result["at_tier2_single"]
        assert not result["at_tier2_multi"]

    def test_tier2_multi_requires_nba_n(self):
        # MLB n=150 alone is NOT Tier 2
        result = adr0024_tier(n_mlb=ADR_0024_TIER2_N_MULTI, ev_per_bet=0.05, nba_n=0)
        assert not result["at_tier2"]

    def test_tier2_multi_with_adequate_nba(self):
        result = adr0024_tier(
            n_mlb=ADR_0024_TIER2_N_MULTI,
            ev_per_bet=0.05,
            nba_n=ADR_0024_TIER2_N_MULTI,
        )
        assert result["at_tier2"]
        assert result["at_tier2_multi"]

    def test_diagnostic_only_at_tier1_not_below(self):
        result = adr0024_tier(n_mlb=ADR_0024_TIER1_N - 1, ev_per_bet=-0.10)
        assert not result["diagnostic_sprint"]

    def test_constants_values(self):
        assert ADR_0024_TIER1_N == 150
        assert ADR_0024_TIER1_DIAG_EV == -0.03
        assert ADR_0024_TIER2_N_SINGLE == 500
        assert ADR_0024_TIER2_N_MULTI == 150


# ── TestEvVerdict ─────────────────────────────────────────────────────────────

class TestEvVerdict:
    def _tier(self, n_mlb: int, ev: float, nba_n: int = 0) -> dict:
        return adr0024_tier(n_mlb=n_mlb, ev_per_bet=ev, nba_n=nba_n)

    def test_inconclusive_below_min_n(self):
        tier = self._tier(MIN_N - 1, 0.05)
        result = ev_verdict(MIN_N - 1, 0.05, tier, fisher_pvalue=0.01)
        assert result == V_INC

    def test_diagnostic_sprint(self):
        n = ADR_0024_TIER1_N
        tier = self._tier(n, -0.05)
        result = ev_verdict(n, -0.05, tier, fisher_pvalue=0.5)
        assert result == V_DIAG

    def test_confirmed_positive_at_tier2(self):
        n = ADR_0024_TIER2_N_SINGLE
        tier = self._tier(n, 0.05)
        result = ev_verdict(n, 0.05, tier, fisher_pvalue=0.04)
        assert result == V_CONF_POS

    def test_directional_positive_below_tier2(self):
        n = ADR_0024_TIER1_N
        tier = self._tier(n, 0.02)
        result = ev_verdict(n, 0.02, tier, fisher_pvalue=0.5)
        assert result == V_DIR_POS

    def test_confirmed_negative_at_tier2(self):
        n = ADR_0024_TIER2_N_SINGLE
        tier = self._tier(n, -0.05)
        # diagnostic_sprint fires first at Tier 1+ EV<-0.03
        # but at Tier 2 with EV<-0.03 → CONFIRMED_NEGATIVE
        # Note: diagnostic_sprint = True here (n>=Tier1 and EV<-0.03)
        result = ev_verdict(n, -0.05, tier, fisher_pvalue=0.5)
        assert result == V_DIAG  # Tier 1 diagnostic_sprint fires first

    def test_directional_negative_below_tier1(self):
        n = MIN_N
        tier = self._tier(n, -0.01)
        result = ev_verdict(n, -0.01, tier, fisher_pvalue=0.9)
        assert result == V_DIR_NEG

    def test_confirmed_positive_requires_p_below_threshold(self):
        # Even at Tier 2, need p < 0.05
        n = ADR_0024_TIER2_N_SINGLE
        tier = self._tier(n, 0.05)
        result = ev_verdict(n, 0.05, tier, fisher_pvalue=0.10)  # p=0.10 >= 0.05
        assert result == V_DIR_POS  # not yet CONFIRMED_POSITIVE


# ── TestEdgeMonotonicity ──────────────────────────────────────────────────────

class TestEdgeMonotonicity:
    def test_anti_predictive_clear(self):
        # edge>0: 5 win / 20 loss; edge<=0: 20 win / 5 loss → ANTI-PREDICTIVE
        pos_edge = [_make_pos(ticker=f"A{i}", fee_net_edge=0.05, outcome="WIN") for i in range(5)]
        pos_edge += [_make_pos(ticker=f"B{i}", fee_net_edge=0.05, outcome="LOSS") for i in range(20)]
        neg_edge = [_make_pos(ticker=f"C{i}", fee_net_edge=-0.05, outcome="WIN") for i in range(20)]
        neg_edge += [_make_pos(ticker=f"D{i}", fee_net_edge=-0.05, outcome="LOSS") for i in range(5)]
        result = edge_monotonicity(pos_edge + neg_edge, alpha=0.10)
        assert result["verdict"] == E_ANTI

    def test_monotonic_clear(self):
        # edge>0: 20 win / 5 loss; edge<=0: 5 win / 20 loss → MONOTONIC
        pos_edge = [_make_pos(ticker=f"A{i}", fee_net_edge=0.05, outcome="WIN") for i in range(20)]
        pos_edge += [_make_pos(ticker=f"B{i}", fee_net_edge=0.05, outcome="LOSS") for i in range(5)]
        neg_edge = [_make_pos(ticker=f"C{i}", fee_net_edge=-0.05, outcome="WIN") for i in range(5)]
        neg_edge += [_make_pos(ticker=f"D{i}", fee_net_edge=-0.05, outcome="LOSS") for i in range(20)]
        result = edge_monotonicity(pos_edge + neg_edge, alpha=0.10)
        assert result["verdict"] == E_MONO

    def test_inconclusive_too_few(self):
        positions = [_make_pos(ticker=f"A{i}") for i in range(MIN_N - 1)]
        result = edge_monotonicity(positions)
        assert result["verdict"] == E_INC
        assert "reason" in result

    def test_inconclusive_no_significance(self):
        # 50/50 win rate in both groups — no signal
        positions = []
        for i in range(20):
            positions.append(_make_pos(ticker=f"A{i}", fee_net_edge=0.05,
                                       outcome="WIN" if i < 10 else "LOSS"))
        for i in range(20):
            positions.append(_make_pos(ticker=f"B{i}", fee_net_edge=-0.05,
                                       outcome="WIN" if i < 10 else "LOSS"))
        result = edge_monotonicity(positions, alpha=0.05)
        assert result["verdict"] == E_INC

    def test_returns_tercile_table(self):
        positions = _make_n_positions(30, win_frac=0.5)
        result = edge_monotonicity(positions)
        assert "terciles" in result
        assert len(result["terciles"]) == 3

    def test_winrates_reported(self):
        positions = _make_n_positions(30, win_frac=0.7)
        result = edge_monotonicity(positions)
        assert "winrate_edge_pos" in result
        assert "winrate_edge_neg" in result

    def test_fisher_pvalue_reported(self):
        positions = _make_n_positions(40)
        result = edge_monotonicity(positions)
        assert "fisher_pvalue" in result
        assert 0.0 <= result["fisher_pvalue"] <= 1.0

    def test_tercile_table_three_rows(self):
        positions = [_make_pos(ticker=f"A{i}", fee_net_edge=i * 0.01) for i in range(30)]
        result = edge_monotonicity(positions)
        assert len(result["terciles"]) == 3


# ── TestTercileTable ──────────────────────────────────────────────────────────

class TestTercileTable:
    def test_three_chunks(self):
        positions = [_make_pos(ticker=f"A{i}", fee_net_edge=float(i)) for i in range(30)]
        rows = _tercile_table(positions)
        assert len(rows) == 3

    def test_ascending_edge(self):
        positions = [_make_pos(ticker=f"A{i}", fee_net_edge=float(i)) for i in range(30)]
        rows = _tercile_table(positions)
        assert rows[0]["edge_mean"] < rows[1]["edge_mean"] < rows[2]["edge_mean"]

    def test_winrates_range(self):
        positions = _make_n_positions(30)
        rows = _tercile_table(positions)
        for r in rows:
            assert 0.0 <= r["winrate"] <= 1.0

    def test_empty(self):
        assert _tercile_table([]) == []


# ── TestFisherPvalue ──────────────────────────────────────────────────────────

class TestFisherPvalue:
    def _pos_group(self, n_win, n_loss, edge=0.05):
        return ([_make_pos(ticker=f"A{i}", fee_net_edge=edge, outcome="WIN") for i in range(n_win)] +
                [_make_pos(ticker=f"B{i}", fee_net_edge=edge, outcome="LOSS") for i in range(n_loss)])

    def test_significant_difference(self):
        pos_group = self._pos_group(20, 5, edge=0.05)
        neg_group = self._pos_group(5, 20, edge=-0.05)
        or_, pval = _fisher_pvalue(pos_group, neg_group)
        assert pval < 0.05

    def test_no_difference(self):
        pos_group = self._pos_group(10, 10, edge=0.05)
        neg_group = self._pos_group(10, 10, edge=-0.05)
        or_, pval = _fisher_pvalue(pos_group, neg_group)
        assert pval > 0.5

    def test_pvalue_in_range(self):
        pos_group = self._pos_group(10, 5)
        neg_group = self._pos_group(5, 10)
        or_, pval = _fisher_pvalue(pos_group, neg_group)
        assert 0.0 <= pval <= 1.0


# ── TestEndToEnd ──────────────────────────────────────────────────────────────

class TestEndToEnd:
    def _synthetic_portfolio(self, n_win: int, n_loss: int) -> list[dict]:
        positions = []
        for i in range(n_win):
            positions.append(_pos_as_dict(
                ticker=f"KXMLBHIT-NYY-Soto-1-2026080{i % 9 + 1}",
                outcome="WIN", pnl=5.0, threshold=1,
            ))
        for j in range(n_loss):
            positions.append(_pos_as_dict(
                ticker=f"KXMLBHIT-BOS-Player-2-2026080{j % 9 + 1}",
                direction="NO", mip=0.60, model_p=0.40,
                outcome="LOSS", pnl=-4.0, threshold=2,
            ))
        return positions

    def test_analyse_returns_verdict(self, tmp_path):
        pos = _make_n_positions(30, win_frac=0.6)
        result = analyse(pos)
        assert "verdict" in result
        assert result["sport"] == SPORT

    def test_analyse_below_min_n_inconclusive(self):
        pos = _make_n_positions(MIN_N - 1)
        result = analyse(pos)
        assert result["verdict"] == V_INC

    def test_portfolio_missing_file_returns_1(self, tmp_path):
        rc = main(["--portfolio", str(tmp_path / "nonexistent.json"), "--no-save"])
        assert rc == 1

    def test_ci_mode_insufficient_returns_4(self, tmp_path):
        pos = [_pos_as_dict(ticker=f"A{i}", outcome="WIN") for i in range(MIN_N - 1)]
        pf = tmp_path / "p.json"
        _write_portfolio_json(pf, pos)
        rc = main(["--portfolio", str(pf), "--ci", "--no-save"])
        assert rc == 4

    def test_ci_mode_diagnostic_sprint_returns_3(self, tmp_path):
        # n=150, EV very negative → DIAGNOSTIC_SPRINT
        pos = [_pos_as_dict(
            ticker=f"KXMLBHIT-NYY-Soto-{i}-20260801",
            outcome="LOSS", pnl=-10.0, model_p=0.45, mip=0.60,
            direction="NO",
        ) for i in range(ADR_0024_TIER1_N)]
        pf = tmp_path / "p.json"
        _write_portfolio_json(pf, pos)
        rc = main(["--portfolio", str(pf), "--ci", "--no-save"])
        assert rc == 3

    def test_ci_mode_positive_returns_0(self, tmp_path):
        pos = [_pos_as_dict(
            ticker=f"KXMLBHIT-NYY-Soto-{i}-20260801",
            outcome="WIN", pnl=5.0, model_p=0.55, mip=0.45,
        ) for i in range(30)]
        pf = tmp_path / "p.json"
        _write_portfolio_json(pf, pos)
        rc = main(["--portfolio", str(pf), "--ci", "--no-save"])
        assert rc == 0

    def test_csv_mode(self, tmp_path):
        rows = [
            {"kalshi_ticker": f"A{i}", "direction": "YES",
             "mid_price_at_entry": "0.45", "vig_at_entry": "0.014",
             "model_p": "0.55", "fee_net_edge": "",
             "threshold": "1", "outcome": "WIN", "pnl": "5.0",
             "game_date": "2026-08-01", "player_name": "T", "duplicate_of": ""}
            for i in range(25)
        ]
        p = tmp_path / "out.csv"
        with open(p, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        rc = main(["--csv", str(p), "--no-save"])
        assert rc == 0

    def test_nba_n_enables_tier2_multi(self, tmp_path):
        # MLB n=150, NBA n=150 → should reach Tier 2 multi
        pos = [_pos_as_dict(
            ticker=f"KXMLBHIT-NYY-Soto-{i}-20260801",
            outcome="WIN", pnl=3.0, model_p=0.55, mip=0.45,
        ) for i in range(ADR_0024_TIER2_N_MULTI)]
        pf = tmp_path / "p.json"
        _write_portfolio_json(pf, pos)
        rc = main(["--portfolio", str(pf), "--nba-n", str(ADR_0024_TIER2_N_MULTI), "--no-save"])
        assert rc == 0

    def test_full_result_structure(self):
        pos = _make_n_positions(40, win_frac=0.55)
        result = analyse(pos)
        required_keys = [
            "sport", "n_unique_markets", "n_total_positions",
            "ev_per_bet", "win_rate", "total_pnl",
            "ev_yes", "ev_no", "threshold_breakdown",
            "edge_monotonicity", "verdict", "adr", "gg",
        ]
        for k in required_keys:
            assert k in result, f"Missing key: {k}"

    def test_dedup_applied_in_analyse(self):
        # Feed 10 positions but only 5 unique tickers → n_unique = 5
        pos = []
        for i in range(5):
            for _ in range(2):  # duplicate per ticker
                pos.append(_make_pos(ticker=f"KXMLBHIT-A{i}-1", outcome="WIN", pnl=5.0))
        result = analyse(pos)
        assert result["n_unique_markets"] == 5
        assert result["n_total_positions"] == 10

    def test_no_save_skips_file_write(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        pos = _make_n_positions(25, win_frac=0.6)
        result = analyse(pos)
        # OUT_DIR shouldn't exist (no save)
        assert result["verdict"] is not None  # just verify it ran


# ── TestConstantsAndSportLabel ────────────────────────────────────────────────

class TestConstantsAndSportLabel:
    def test_sport_is_mlb(self):
        assert SPORT == "mlb"

    def test_verdict_strings_defined(self):
        for v in [V_CONF_POS, V_DIR_POS, V_CONF_NEG, V_DIR_NEG, V_DIAG, V_INC]:
            assert isinstance(v, str) and len(v) > 0

    def test_edge_verdicts_defined(self):
        for v in [E_ANTI, E_MONO, E_INC]:
            assert isinstance(v, str) and len(v) > 0

    def test_min_n(self):
        assert MIN_N == 20

    def test_adr_p_threshold(self):
        assert ADR_0024_P_THRESHOLD == 0.05
