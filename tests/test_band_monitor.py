"""Tests for scripts/run_band_monitor.py — T-255/T-258, GG-099/GG-100/GG-098.

Covers: band splitting (T-253 tags), T4 ledger loading (T-254) with GG-077
defense-in-depth (never trust a stored edge field, even an already-correct one),
the MIN_N=30 UNDERPOWERED gate (GG-098), a synthetic genuinely anti-predictive
fixture the monitor must flag, a synthetic "NO-majority" fixture that would fool
a naive YES-frame-only edge computation but must NOT fool this monitor (the
GG-100 inversion, closed for this new guard per GG-054), and a T1 regression
anchor against the real live book reproducing EXP-017's direction-aware result.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_exp017_mlb import compute_fee_net_edge, E_ANTI, E_MONO, E_INC
from run_band_monitor import (
    MIN_N,
    BOOK_BANDS,
    load_pool_by_band,
    load_t4_ledger,
    to_mlb_positions,
    analyze_band,
    run_all_bands,
    main,
)

REAL_PORTFOLIO = Path(__file__).parent.parent / "logs" / ".vps_portfolio_cache_mlb.json"


# ── helpers ──────────────────────────────────────────────────────────────────────

def _make_rec(
    ticker="KXMLBHIT-A-1",
    direction="YES",
    mip=0.45,
    model_p=0.55,
    vig=0.014,
    outcome="WIN",
    pnl=1.0,
    size=1.0,
    threshold=1,
    game_date="2026-08-01",
    player_name="Test Player",
    band="T1",
    fne=None,
) -> dict:
    """Builds a dict matching exactly what load_pool_by_band()/load_t4_ledger()
    produce internally (_dir/_mip/_model_p/_win/_pnl/_size/_fne/_thr/_event)."""
    win = 1 if outcome == "WIN" else 0
    if fne is None:
        fne = compute_fee_net_edge(direction, model_p, mip)
    event = 1 if ((direction == "YES") == (win == 1)) else 0
    return {
        "kalshi_ticker": ticker,
        "direction": direction,
        "_dir": direction,
        "_mip": mip,
        "_model_p": model_p,
        "_win": win,
        "_pnl": pnl,
        "_size": size,
        "_fne": fne,
        "_thr": threshold,
        "_event": event,
        "vig_at_entry": vig,
        "game_date": game_date,
        "player_name": player_name,
        "band": band,
    }


def _pos_as_dict(ticker, direction="YES", mip=0.45, model_p=0.55, vig=0.014,
                  outcome="WIN", pnl=1.0, size=1.0, threshold=1,
                  game_date="2026-08-01", player_name="T", band="T1") -> dict:
    """Raw closed_position dict, as PaperTrader/T-253 would write it to disk."""
    return {
        "kalshi_ticker": ticker,
        "direction": direction,
        "mid_price_at_entry": mip,
        "vig_at_entry": vig,
        "model_p": model_p,
        "outcome": outcome,
        "pnl": pnl,
        "size_usd": size,
        "threshold": threshold,
        "game_date": game_date,
        "player_name": player_name,
        "band": band,
    }


def _write_portfolio(path: Path, positions: list[dict]) -> None:
    path.write_text(json.dumps({"bankroll_usd": 1000.0, "closed_positions": positions}))


def _write_t4_ledger(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def _t4_ledger_row(ticker, direction="YES", mip=0.5, model_p=0.6, outcome="WIN",
                    pnl=1.0, size=1.0, threshold=1, band="T4M-PROJ",
                    stored_edge=None) -> dict:
    """A row as build_t4_resolved_ledger.py writes it. stored_edge lets a test
    plant a deliberately WRONG value in the "edge" column to prove the monitor
    ignores it (GG-077 defense-in-depth even though the ledger script itself
    already computes edge direction-aware)."""
    if stored_edge is None:
        stored_edge = compute_fee_net_edge(direction, model_p, mip)
    return {
        "band": band, "position_id": f"POS-{ticker}", "kalshi_ticker": ticker,
        "player_name": "T", "threshold": threshold, "direction": direction,
        "game_date": "2026-08-01", "model_p": model_p, "mip": mip, "vig": 0.02,
        "edge": stored_edge, "outcome": outcome, "pnl": pnl, "size_usd": size,
    }


def _make_n_recs(n: int, win_frac: float, direction: str, edge_positive: bool,
                  band="T1") -> list[dict]:
    n_win = int(n * win_frac)
    recs = []
    for i in range(n):
        outcome = "WIN" if i < n_win else "LOSS"
        if direction == "YES":
            mip, model_p = (0.40, 0.55) if edge_positive else (0.60, 0.45)
        else:
            mip, model_p = (0.60, 0.45) if edge_positive else (0.40, 0.55)
        recs.append(_make_rec(ticker=f"T{i}", direction=direction, mip=mip,
                               model_p=model_p, outcome=outcome,
                               pnl=1.0 if outcome == "WIN" else -1.0, band=band))
    return recs


# ── load_pool_by_band ────────────────────────────────────────────────────────────

class TestLoadPoolByBand:
    def test_splits_by_band(self, tmp_path):
        pos = ([_pos_as_dict(f"A{i}", band="T1") for i in range(3)] +
               [_pos_as_dict(f"B{i}", band="T2") for i in range(2)])
        p = tmp_path / "p.json"
        _write_portfolio(p, pos)
        by_band = load_pool_by_band(p)
        assert len(by_band["T1"]) == 3
        assert len(by_band["T2"]) == 2
        assert by_band["T3"] == []

    def test_untagged_bucket_catches_missing_band(self, tmp_path):
        pos = [_pos_as_dict("A1", band="T1")]
        d = pos[0]
        del d["band"]
        p = tmp_path / "p.json"
        _write_portfolio(p, [d])
        by_band = load_pool_by_band(p)
        assert "UNTAGGED" in by_band
        assert len(by_band["UNTAGGED"]) == 1

    def test_all_book_bands_always_present(self, tmp_path):
        p = tmp_path / "p.json"
        _write_portfolio(p, [_pos_as_dict("A1", band="T1")])
        by_band = load_pool_by_band(p)
        for b in BOOK_BANDS:
            assert b in by_band


# ── load_t4_ledger ───────────────────────────────────────────────────────────────

class TestLoadT4Ledger:
    def test_loads_rows(self, tmp_path):
        rows = [_t4_ledger_row(f"T{i}") for i in range(5)]
        p = tmp_path / "ledger.jsonl"
        _write_t4_ledger(p, rows)
        recs = load_t4_ledger(p)
        assert len(recs) == 5
        assert recs[0]["_dir"] in ("YES", "NO")

    def test_missing_file_returns_empty(self, tmp_path):
        assert load_t4_ledger(tmp_path / "nope.jsonl") == []

    def test_gg077_defense_in_depth_ignores_stored_edge_even_when_present(self, tmp_path):
        # The ledger's own "edge" column is already direction-aware (T-254), but
        # this monitor must NEVER trust an upstream field's sign under any
        # circumstance — plant a deliberately wrong stored edge and confirm the
        # monitor recomputes from scratch instead.
        row = _t4_ledger_row("T1", direction="NO", model_p=0.35, mip=0.55,
                              stored_edge=-0.9999)
        p = tmp_path / "ledger.jsonl"
        _write_t4_ledger(p, [row])
        recs = load_t4_ledger(p)
        expected = compute_fee_net_edge("NO", 0.35, 0.55)
        assert recs[0]["_fne"] == pytest.approx(expected)
        assert recs[0]["_fne"] != pytest.approx(-0.9999)


# ── to_mlb_positions adapter ─────────────────────────────────────────────────────

class TestToMlbPositions:
    def test_field_mapping(self):
        rec = _make_rec(ticker="X1", direction="NO", mip=0.6, model_p=0.4, outcome="WIN")
        positions = to_mlb_positions([rec])
        assert len(positions) == 1
        pos = positions[0]
        assert pos.kalshi_ticker == "X1"
        assert pos.direction == "NO"
        assert pos.mip == 0.6
        assert pos.model_p == 0.4
        assert pos.outcome == "WIN"
        assert pos.fee_net_edge == pytest.approx(compute_fee_net_edge("NO", 0.4, 0.6))


# ── analyze_band: MIN_N gate (GG-098) ────────────────────────────────────────────

class TestAnalyzeBandUnderpowered:
    def test_below_min_n_returns_underpowered_not_a_verdict(self):
        recs = _make_n_recs(MIN_N - 1, win_frac=0.9, direction="YES", edge_positive=True)
        result = analyze_band("T2", recs)
        assert result["verdict"] == "UNDERPOWERED"
        assert "edge_monotonicity" not in result
        assert result["anti_predictive_alarm"] is False

    def test_at_min_n_returns_a_verdict(self):
        recs = _make_n_recs(MIN_N, win_frac=0.5, direction="YES", edge_positive=True)
        result = analyze_band("T1", recs)
        assert result["verdict"] == "ANALYZED"

    def test_min_n_is_30_per_ab_harness_discipline(self):
        assert MIN_N == 30


# ── analyze_band: synthetic anti-predictive fixture (GG-054/T-258) ─────────────

class TestAnalyzeBandSyntheticAntiPredictive:
    def test_flags_genuine_anti_predictive_signal(self):
        # edge>0 cohort loses more than edge<=0 cohort — a real, unambiguous
        # anti-predictive pattern the monitor must not miss.
        pos_edge = [_make_rec(ticker=f"P{i}", direction="YES", mip=0.40, model_p=0.55,
                               outcome="WIN" if i < 6 else "LOSS", pnl=1.0 if i < 6 else -1.0)
                    for i in range(30)]
        neg_edge = [_make_rec(ticker=f"N{i}", direction="YES", mip=0.60, model_p=0.45,
                               outcome="WIN" if i < 24 else "LOSS", pnl=1.0 if i < 24 else -1.0)
                    for i in range(30)]
        result = analyze_band("T1", pos_edge + neg_edge)
        assert result["verdict"] == "ANALYZED"
        assert result["edge_monotonicity"]["verdict"] == E_ANTI
        assert result["anti_predictive_alarm"] is True

    def test_healthy_monotonic_signal_does_not_alarm(self):
        pos_edge = [_make_rec(ticker=f"P{i}", direction="YES", mip=0.40, model_p=0.55,
                               outcome="WIN" if i < 24 else "LOSS", pnl=1.0 if i < 24 else -1.0)
                    for i in range(30)]
        neg_edge = [_make_rec(ticker=f"N{i}", direction="YES", mip=0.60, model_p=0.45,
                               outcome="WIN" if i < 6 else "LOSS", pnl=1.0 if i < 6 else -1.0)
                    for i in range(30)]
        result = analyze_band("T1", pos_edge + neg_edge)
        assert result["edge_monotonicity"]["verdict"] == E_MONO
        assert result["anti_predictive_alarm"] is False


# ── the GG-100 inversion trap: NO-majority, direction-aware correctness ────────

class TestAnalyzeBandNoMajorityDirectionAwareGuard:
    """Reproduces the exact shape of GG-100's real bug on a synthetic book:
    a naive YES-frame-only edge (model_p - mip - fee, no direction flip) sign-
    inverts the cohort split for NO bets, which can turn a genuinely MONOTONIC
    signal into a false ANTI-PREDICTIVE alarm. This test proves analyze_band's
    real (direction-aware) computation is immune to that inversion, using a
    fixture explicitly constructed so the naive formula WOULD get it wrong."""

    def _fixture(self):
        # True direction-aware edge positive, NO bets, well-signaled, mostly WIN.
        true_pos = [_make_rec(ticker=f"TP{i}", direction="NO", mip=0.65, model_p=0.30,
                               outcome="WIN" if i < 24 else "LOSS",
                               pnl=1.0 if i < 24 else -1.0)
                    for i in range(30)]
        # True direction-aware edge negative/zero, NO bets, mostly LOSE.
        true_neg = [_make_rec(ticker=f"TN{i}", direction="NO", mip=0.55, model_p=0.60,
                               outcome="WIN" if i < 6 else "LOSS",
                               pnl=1.0 if i < 6 else -1.0)
                    for i in range(30)]
        return true_pos, true_neg

    def test_naive_yes_frame_formula_would_invert_this_fixture(self):
        # Proof the fixture is a real trap, not a strawman: a naive formula
        # that ignores direction assigns cohorts backwards here.
        true_pos, true_neg = self._fixture()
        for r in true_pos:
            naive_edge = r["_model_p"] - r["_mip"]  # YES-frame formula, no direction flip
            assert naive_edge < 0   # true-positive-edge NO bets look "negative" to the naive formula
        for r in true_neg:
            naive_edge = r["_model_p"] - r["_mip"]
            assert naive_edge > 0   # true-negative-edge NO bets look "positive" to the naive formula

    def test_monitor_is_not_fooled_by_the_inversion(self):
        true_pos, true_neg = self._fixture()
        result = analyze_band("T1", true_pos + true_neg)
        # Correct, direction-aware verdict: the truly-positive-edge cohort wins
        # more -> MONOTONIC (or at worst INCONCLUSIVE) — must NOT be ANTI-PREDICTIVE.
        assert result["edge_monotonicity"]["verdict"] != E_ANTI
        assert result["anti_predictive_alarm"] is False
        mono = result["edge_monotonicity"]
        assert mono["winrate_edge_pos"] > mono["winrate_edge_neg"]


# ── run_all_bands integration ────────────────────────────────────────────────────

class TestRunAllBandsIntegration:
    def test_runs_across_all_bands(self, tmp_path):
        pos = (
            [_pos_as_dict(f"A{i}", band="T1", outcome="WIN" if i % 2 == 0 else "LOSS",
                          pnl=1.0 if i % 2 == 0 else -1.0) for i in range(40)]
            + [_pos_as_dict(f"B{i}", band="T2") for i in range(2)]
        )
        pf = tmp_path / "p.json"
        _write_portfolio(pf, pos)
        ledger = tmp_path / "t4.jsonl"
        _write_t4_ledger(ledger, [_t4_ledger_row(f"T{i}",
                                                  outcome="WIN" if i % 2 == 0 else "LOSS",
                                                  pnl=1.0 if i % 2 == 0 else -1.0)
                                   for i in range(40)])
        results = run_all_bands(pf, ledger)
        assert results["T1"]["verdict"] == "ANALYZED"
        assert results["T2"]["verdict"] == "UNDERPOWERED"
        assert results["T3"]["verdict"] == "UNDERPOWERED"
        assert results["T4M-PROJ"]["verdict"] == "ANALYZED"

    def test_missing_t4_ledger_reports_no_data(self, tmp_path):
        pf = tmp_path / "p.json"
        _write_portfolio(pf, [_pos_as_dict("A1", band="T1")])
        results = run_all_bands(pf, tmp_path / "missing.jsonl")
        assert results["T4M-PROJ"]["verdict"] == "NO_DATA"


# ── CI exit codes (T-257: warn-only, never a kill signal) ───────────────────────

class TestCiExitCode:
    def test_healthy_book_returns_0(self, tmp_path):
        pos = [_pos_as_dict(f"A{i}", band="T1",
                             outcome="WIN" if i % 2 == 0 else "LOSS",
                             pnl=1.0 if i % 2 == 0 else -1.0) for i in range(40)]
        pf = tmp_path / "p.json"
        _write_portfolio(pf, pos)
        rc = main(["--portfolio", str(pf), "--t4-ledger", str(tmp_path / "none.jsonl"),
                    "--ci", "--out", str(tmp_path / "out")])
        assert rc == 0

    def test_anti_predictive_book_returns_1(self, tmp_path):
        pos_edge = [_pos_as_dict(f"P{i}", direction="YES", mip=0.40, model_p=0.55, band="T1",
                                  outcome="WIN" if i < 6 else "LOSS",
                                  pnl=1.0 if i < 6 else -1.0) for i in range(30)]
        neg_edge = [_pos_as_dict(f"N{i}", direction="YES", mip=0.60, model_p=0.45, band="T1",
                                  outcome="WIN" if i < 24 else "LOSS",
                                  pnl=1.0 if i < 24 else -1.0) for i in range(30)]
        pf = tmp_path / "p.json"
        _write_portfolio(pf, pos_edge + neg_edge)
        rc = main(["--portfolio", str(pf), "--t4-ledger", str(tmp_path / "none.jsonl"),
                    "--ci", "--out", str(tmp_path / "out")])
        assert rc == 1


# ── T-258 regression anchor: real T1 book, direction-aware, matches EXP-017 ────

@pytest.mark.skipif(not REAL_PORTFOLIO.exists(), reason="live VPS cache not present in this checkout")
class TestT1RegressionAnchor:
    """Reproduces the exact GG-100 diagnosis on the real, live T1-only book
    (n=167): direction-aware Fisher p~=0.246 (NOT anti-predictive; the stored-
    edge/GG-100 bug would have shown p=0.0236 and a false ANTI-PREDICTIVE
    alarm), and a calibration slope CI that includes 1."""

    def test_t1_band_reproduces_direction_aware_verdict(self):
        by_band = load_pool_by_band(REAL_PORTFOLIO)
        t1 = by_band["T1"]
        assert len(t1) >= MIN_N
        result = analyze_band("T1", t1, seed=17, boot=10000)
        mono = result["edge_monotonicity"]
        assert mono["verdict"] == E_INC
        assert mono["fisher_pvalue"] == pytest.approx(0.24615828583796262, abs=0.02)
        assert result["anti_predictive_alarm"] is False
        fit = result["calibration"]
        assert fit["b_ci"][0] <= 1.0 <= fit["b_ci"][1]
        assert not fit["b_excludes_1"]
