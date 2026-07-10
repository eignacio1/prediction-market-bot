"""Tests for scripts/run_band_monitor.py — T-255/T-258/T-322, GG-099/GG-100/GG-098.

Covers: band splitting (T-253 tags), T4 ledger loading (T-254) with GG-077
defense-in-depth (never trust a stored edge field, even an already-correct one),
the MIN_N=30 UNDERPOWERED gate (GG-098) — now applied to clean_n, not raw_n
(T-322) — a synthetic genuinely anti-predictive fixture the monitor must flag,
a synthetic "NO-majority" fixture that would fool a naive YES-frame-only edge
computation but must NOT fool this monitor (the GG-100 inversion, closed for
this new guard per GG-054), clean_n/raw_n epoch-filtering behavior (T-322),
and a T1 regression anchor against the real live book reproducing EXP-017's
direction-aware result on the raw pool (decoupled from analyze_band's clean_n
filter, since the anchor's purpose is GG-100 direction-aware correctness, not
epoch provenance).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "scripts"
_SRC = Path(__file__).parent.parent / "src"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import run_exp017_mlb as e17
import run_exp017c_calibration_mlb as c17c
from run_exp017_mlb import compute_fee_net_edge, E_ANTI, E_MONO, E_INC
from run_band_monitor import (
    MIN_N,
    BOOK_BANDS,
    load_pool_by_band,
    load_t4_ledger,
    to_mlb_positions,
    filter_clean,
    analyze_band,
    run_all_bands,
    build_summary,
    main,
)
from prediction_market_bot.logic_epoch import CURRENT_LOGIC_EPOCH

REAL_PORTFOLIO = Path(__file__).parent.parent / "logs" / ".vps_portfolio_cache_mlb.json"
OLD_EPOCH = CURRENT_LOGIC_EPOCH - 1 if CURRENT_LOGIC_EPOCH > 1 else 99


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
    logic_epoch=CURRENT_LOGIC_EPOCH,
) -> dict:
    """Builds a dict matching exactly what load_pool_by_band()/load_t4_ledger()
    produce internally (_dir/_mip/_model_p/_win/_pnl/_size/_fne/_thr/_event).

    Defaults `logic_epoch=CURRENT_LOGIC_EPOCH` (T-322) so existing fixtures
    remain "clean" by default and continue exercising analyze_band's ANALYZED
    path; pass logic_epoch=None or an old epoch int to test the clean_n filter
    itself."""
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
        "logic_epoch": logic_epoch,
    }


def _pos_as_dict(ticker, direction="YES", mip=0.45, model_p=0.55, vig=0.014,
                  outcome="WIN", pnl=1.0, size=1.0, threshold=1,
                  game_date="2026-08-01", player_name="T", band="T1",
                  logic_epoch=CURRENT_LOGIC_EPOCH) -> dict:
    """Raw closed_position dict, as PaperTrader/T-253 would write it to disk.
    Defaults `logic_epoch=CURRENT_LOGIC_EPOCH` (T-322, mirrors _make_rec)."""
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
        "logic_epoch": logic_epoch,
    }


def _write_portfolio(path: Path, positions: list[dict]) -> None:
    path.write_text(json.dumps({"bankroll_usd": 1000.0, "closed_positions": positions}))


def _write_t4_ledger(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def _t4_ledger_row(ticker, direction="YES", mip=0.5, model_p=0.6, outcome="WIN",
                    pnl=1.0, size=1.0, threshold=1, band="T4M-PROJ",
                    stored_edge=None, logic_epoch=CURRENT_LOGIC_EPOCH) -> dict:
    """A row as build_t4_resolved_ledger.py writes it. stored_edge lets a test
    plant a deliberately WRONG value in the "edge" column to prove the monitor
    ignores it (GG-077 defense-in-depth even though the ledger script itself
    already computes edge direction-aware). Defaults `logic_epoch=
    CURRENT_LOGIC_EPOCH` (T-322, mirrors build_t4_resolved_ledger.py's
    passthrough)."""
    if stored_edge is None:
        stored_edge = compute_fee_net_edge(direction, model_p, mip)
    return {
        "band": band, "position_id": f"POS-{ticker}", "kalshi_ticker": ticker,
        "player_name": "T", "threshold": threshold, "direction": direction,
        "game_date": "2026-08-01", "model_p": model_p, "mip": mip, "vig": 0.02,
        "edge": stored_edge, "outcome": outcome, "pnl": pnl, "size_usd": size,
        "logic_epoch": logic_epoch,
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
    """Reproduces the exact GG-100 diagnosis on the real, live T1-only RAW book
    (n=167): direction-aware Fisher p~=0.246 (NOT anti-predictive; the stored-
    edge/GG-100 bug would have shown p=0.0236 and a false ANTI-PREDICTIVE
    alarm), and a calibration slope CI that includes 1.

    T-322: deliberately bypasses analyze_band() and calls e17/c17c directly on
    the RAW pool, not the clean_n-filtered one. analyze_band() now always
    clean-filters (see TestCleanNFiltering below), so it would run on a
    different (smaller, epoch-restricted) cohort than the one this anchor's
    magic numbers were derived against — that cohort has its own T-322 tests.
    This anchor's job is only to prove direction-aware correctness (GG-100)
    stays correct on raw history, independent of the epoch-provenance filter."""

    def test_t1_band_reproduces_direction_aware_verdict(self):
        by_band = load_pool_by_band(REAL_PORTFOLIO)
        t1 = by_band["T1"]
        assert len(t1) >= MIN_N
        positions = to_mlb_positions(t1)
        mono = e17.edge_monotonicity(positions, alpha=0.10)
        assert mono["verdict"] == E_INC
        assert mono["fisher_pvalue"] == pytest.approx(0.24615828583796262, abs=0.02)
        assert mono["verdict"] != E_ANTI
        import random as _random
        fit = c17c.calib_fit_ci(t1, 10000, _random.Random(17))
        assert fit["b_ci"][0] <= 1.0 <= fit["b_ci"][1]
        assert not fit["b_excludes_1"]


# ── clean_n / raw_n epoch filtering (T-322) ─────────────────────────────────────

class TestCleanNFiltering:
    def test_filter_clean_keeps_current_epoch_only(self):
        clean = _make_rec(ticker="C1", logic_epoch=CURRENT_LOGIC_EPOCH)
        old = _make_rec(ticker="O1", logic_epoch=OLD_EPOCH)
        missing = _make_rec(ticker="M1", logic_epoch=None)
        recs = filter_clean([clean, old, missing])
        assert len(recs) == 1
        assert recs[0]["kalshi_ticker"] == "C1"

    def test_missing_logic_epoch_excluded_same_as_old_epoch(self):
        # Pre-T-320 history has no logic_epoch key at all — must be excluded,
        # not silently treated as clean (matches governance_scan.sh's
        # `p.get('logic_epoch') == CURRENT_LOGIC_EPOCH` comparison exactly).
        recs = [_make_rec(ticker=f"X{i}", logic_epoch=None) for i in range(MIN_N + 5)]
        result = analyze_band("T1", recs)
        assert result["verdict"] == "UNDERPOWERED"
        assert result["raw_n"] == MIN_N + 5
        assert result["clean_n"] == 0

    def test_raw_n_above_floor_but_clean_n_below_floor_is_underpowered(self):
        # raw_n alone clears MIN_N, but only a handful are clean -> must still
        # be UNDERPOWERED. This is the exact scenario T-322 exists to prevent:
        # a contaminated majority must never paper over a thin clean cohort.
        clean = [_make_rec(ticker=f"C{i}", logic_epoch=CURRENT_LOGIC_EPOCH) for i in range(5)]
        old = [_make_rec(ticker=f"O{i}", logic_epoch=OLD_EPOCH) for i in range(50)]
        result = analyze_band("T1", clean + old)
        assert result["raw_n"] == 55
        assert result["clean_n"] == 5
        assert result["verdict"] == "UNDERPOWERED"

    def test_analyzed_result_reports_both_raw_and_clean_n(self):
        recs = _make_n_recs(MIN_N, win_frac=0.5, direction="YES", edge_positive=True)
        result = analyze_band("T1", recs)
        assert result["verdict"] == "ANALYZED"
        assert result["raw_n"] == MIN_N
        assert result["clean_n"] == MIN_N
        assert result["n"] == MIN_N

    def test_old_epoch_contamination_does_not_change_clean_verdict(self):
        # A pile of old-epoch records with the OPPOSITE (anti-predictive)
        # pattern must not leak into a verdict built only from clean records.
        clean_pos = [_make_rec(ticker=f"CP{i}", direction="YES", mip=0.40, model_p=0.55,
                                outcome="WIN" if i < 24 else "LOSS",
                                pnl=1.0 if i < 24 else -1.0)
                     for i in range(30)]
        clean_neg = [_make_rec(ticker=f"CN{i}", direction="YES", mip=0.60, model_p=0.45,
                                outcome="WIN" if i < 6 else "LOSS",
                                pnl=1.0 if i < 6 else -1.0)
                     for i in range(30)]
        # Old-epoch records, deliberately anti-predictive-shaped, would flip
        # the verdict if incorrectly blended in.
        contaminated = _make_n_recs(40, win_frac=0.9, direction="YES",
                                     edge_positive=False, band="T1")
        for r in contaminated:
            r["logic_epoch"] = OLD_EPOCH
        result = analyze_band("T1", clean_pos + clean_neg + contaminated)
        assert result["clean_n"] == 60
        assert result["raw_n"] == 100
        assert result["edge_monotonicity"]["verdict"] == E_MONO
        assert result["anti_predictive_alarm"] is False

    def test_brier_murphy_and_reliability_present_on_analyzed_result(self):
        recs = _make_n_recs(MIN_N, win_frac=0.5, direction="YES", edge_positive=True)
        result = analyze_band("T1", recs)
        assert "brier_murphy" in result
        assert "reliability_curve" in result
        bm = result["brier_murphy"]
        assert bm["recompose_ok"] is True
        assert 0.0 <= bm["brier_full"] <= 1.0


# ── build_summary (T-322 exit criterion) ────────────────────────────────────────

class TestBuildSummary:
    def test_analyzed_band_summary_shape(self):
        recs = _make_n_recs(MIN_N, win_frac=0.5, direction="YES", edge_positive=True)
        results = {"T1": analyze_band("T1", recs)}
        summary = build_summary(results)
        assert set(summary["T1"].keys()) == {"verdict", "p", "brier", "n"}
        assert summary["T1"]["n"] == MIN_N
        assert summary["T1"]["verdict"] in (E_ANTI, E_MONO, E_INC)
        assert summary["T1"]["brier"] is not None
        assert summary["T1"]["p"] is not None

    def test_underpowered_band_summary_has_null_p_and_brier(self):
        recs = _make_n_recs(MIN_N - 1, win_frac=0.5, direction="YES", edge_positive=True)
        results = {"T2": analyze_band("T2", recs)}
        summary = build_summary(results)
        assert summary["T2"]["verdict"] == "UNDERPOWERED"
        assert summary["T2"]["p"] is None
        assert summary["T2"]["brier"] is None
        assert summary["T2"]["n"] == MIN_N - 1

    def test_no_data_band_summary_present_not_omitted(self):
        results = {"T4M-PROJ": {"band": "T4M-PROJ", "verdict": "NO_DATA", "n": 0,
                                 "reason": "no ledger", "anti_predictive_alarm": False}}
        summary = build_summary(results)
        assert "T4M-PROJ" in summary
        assert summary["T4M-PROJ"]["verdict"] == "NO_DATA"
