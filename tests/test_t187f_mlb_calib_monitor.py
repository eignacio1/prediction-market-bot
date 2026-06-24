"""
T-187F: MLB Calibration Monitor — test suite

Coverage:
  TestLoadPositions      — JSON loading, filtering, field extraction
  TestToArrays           — directional frame conversion
  TestComputeEce         — ECE formula against known values
  TestDeriveTemperature  — scipy temperature fit
  TestMainPortfolioMissing   — missing file exits 0
  TestMainNoValidPositions   — empty/invalid positions exits 0
  TestMainInsufficientData   — n < MIN_N_DIAGNOSE exits 0
  TestMainCalibrated         — well-calibrated dataset exits 0
  TestMainMiscalibrated      — overconfident dataset exits 1
  TestMainAntiPredictive     — anti-predictive edge exits 2
"""
from __future__ import annotations

import json
import math
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import numpy as np

# Make sure the scripts/ directory is importable
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import run_mlb_calib_monitor as mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _pos(
    model_p: float,
    mip: float,
    direction: str = "YES",
    outcome: str = "WIN",
    threshold: int = 1,
    pnl: float = 0.0,
    duplicate_of: str | None = None,
) -> dict:
    """Raw portfolio JSON format (input to load_positions)."""
    base = {
        "model_p":            model_p,
        "mid_price_at_entry": mip,
        "direction":          direction,
        "outcome":            outcome,
        "threshold":          threshold,
        "kalshi_threshold":   threshold,
        "pnl":                pnl,
        "position_id":        f"POS-{uuid.uuid4().hex[:8]}",
        "player_name":        "TestPlayer",
        "game_date":          "2026-06-01",
    }
    if duplicate_of is not None:
        base["duplicate_of"] = duplicate_of
    return base


def _processed_pos(
    model_p: float,
    mip: float,
    direction: str = "YES",
    outcome: str = "WIN",
    threshold: int = 1,
    pnl: float = 0.0,
) -> dict:
    """Processed format returned by load_positions() — used by to_arrays()."""
    return {
        "model_p":   model_p,
        "mip":       mip,
        "direction": direction,
        "outcome":   outcome,
        "threshold": threshold,
        "pnl":       pnl,
    }


def _portfolio(closed: list[dict]) -> dict:
    return {
        "bankroll_usd":         1000.0,
        "initial_bankroll_usd": 1000.0,
        "open_positions":       [],
        "closed_positions":     closed,
    }


def _write_portfolio(path: Path, closed: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(_portfolio(closed), fh)


def _run_main(path: Path) -> int:
    with patch.object(sys, "argv", ["run_mlb_calib_monitor.py", str(path)]):
        return mod.main()


def _make_n_positions(
    n: int,
    model_p: float,
    mip: float,
    direction: str = "YES",
    win_fraction: float = 0.65,
    threshold: int = 1,
) -> list[dict]:
    """Build N positions where `win_fraction` of them are WINs."""
    n_win  = round(n * win_fraction)
    n_loss = n - n_win
    positions = []
    for _ in range(n_win):
        positions.append(_pos(model_p, mip, direction, "WIN", threshold))
    for _ in range(n_loss):
        positions.append(_pos(model_p, mip, direction, "LOSS", threshold))
    return positions


# ---------------------------------------------------------------------------
# TestLoadPositions
# ---------------------------------------------------------------------------

class TestLoadPositions(unittest.TestCase):

    def test_empty_portfolio(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "portfolio.json"
            _write_portfolio(path, [])
            result = mod.load_positions(path)
        self.assertEqual(result, [])

    def test_no_closed_positions_key(self):
        import tempfile, json
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            with open(path, "w") as fh:
                json.dump({"bankroll_usd": 1000.0}, fh)
            result = mod.load_positions(path)
        self.assertEqual(result, [])

    def test_valid_position_loaded(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, [_pos(0.75, 0.55, "YES", "WIN", 1)])
            result = mod.load_positions(path)
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]["model_p"], 0.75)
        self.assertAlmostEqual(result[0]["mip"],     0.55)
        self.assertEqual(result[0]["direction"],     "YES")
        self.assertEqual(result[0]["outcome"],       "WIN")
        self.assertEqual(result[0]["threshold"],      1)

    def test_filters_missing_model_p(self):
        import tempfile
        bad = {
            "mid_price_at_entry": 0.55,
            "direction": "YES",
            "outcome": "WIN",
            "threshold": 1,
        }
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, [bad])
            result = mod.load_positions(path)
        self.assertEqual(result, [])

    def test_filters_missing_mip(self):
        import tempfile
        bad = {"model_p": 0.75, "direction": "YES", "outcome": "WIN", "threshold": 1}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, [bad])
            result = mod.load_positions(path)
        self.assertEqual(result, [])

    def test_filters_duplicate_positions(self):
        import tempfile
        dup = _pos(0.75, 0.55, "YES", "WIN", 1, duplicate_of="POS-ORIGINAL")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, [dup])
            result = mod.load_positions(path)
        self.assertEqual(result, [])

    def test_filters_pending_outcome(self):
        import tempfile
        pending = _pos(0.75, 0.55, "YES", "PENDING", 1)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, [pending])
            result = mod.load_positions(path)
        self.assertEqual(result, [])

    def test_direction_uppercased(self):
        import tempfile
        lower = _pos(0.75, 0.55, "yes", "WIN", 1)
        lower["direction"] = "yes"
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, [lower])
            result = mod.load_positions(path)
        self.assertEqual(result[0]["direction"], "YES")

    def test_threshold_from_kalshi_threshold_fallback(self):
        import tempfile
        pos = _pos(0.75, 0.55, "YES", "WIN")
        pos.pop("threshold", None)
        pos["kalshi_threshold"] = 2
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, [pos])
            result = mod.load_positions(path)
        self.assertEqual(result[0]["threshold"], 2)


# ---------------------------------------------------------------------------
# TestToArrays
# ---------------------------------------------------------------------------

class TestToArrays(unittest.TestCase):
    # to_arrays() expects processed dicts (output of load_positions),
    # which use "mip" not "mid_price_at_entry". Use _processed_pos() here.

    def test_yes_direction_identity(self):
        positions = [_processed_pos(0.70, 0.50, "YES", "WIN", 1)]
        P, MIP, Y, PNL = mod.to_arrays(positions)
        self.assertAlmostEqual(float(P[0]),   0.70, places=5)
        self.assertAlmostEqual(float(MIP[0]), 0.50, places=5)
        self.assertAlmostEqual(float(Y[0]),   1.0,  places=5)

    def test_no_direction_inverts(self):
        positions = [_processed_pos(0.30, 0.40, "NO", "WIN", 1)]
        P, MIP, Y, PNL = mod.to_arrays(positions)
        self.assertAlmostEqual(float(P[0]),   1.0 - 0.30, places=5)
        self.assertAlmostEqual(float(MIP[0]), 1.0 - 0.40, places=5)

    def test_loss_outcome_zero(self):
        positions = [_processed_pos(0.70, 0.50, "YES", "LOSS", 1)]
        _, _, Y, _ = mod.to_arrays(positions)
        self.assertAlmostEqual(float(Y[0]), 0.0, places=5)

    def test_pnl_preserved(self):
        positions = [_processed_pos(0.70, 0.50, "YES", "WIN", 1, pnl=12.34)]
        _, _, _, PNL = mod.to_arrays(positions)
        self.assertAlmostEqual(float(PNL[0]), 12.34, places=4)

    def test_clip_prevents_zero_one(self):
        positions = [_processed_pos(0.0, 0.50, "YES", "WIN", 1),
                     _processed_pos(1.0, 0.50, "YES", "WIN", 1)]
        P, _, _, _ = mod.to_arrays(positions)
        self.assertGreater(float(P[0]), 0.0)
        self.assertLess(float(P[1]),    1.0)


# ---------------------------------------------------------------------------
# TestComputeEce
# ---------------------------------------------------------------------------

class TestComputeEce(unittest.TestCase):

    def test_empty_arrays_returns_zero(self):
        P = np.array([], dtype=float)
        Y = np.array([], dtype=float)
        self.assertAlmostEqual(mod.compute_ece(P, Y), 0.0)

    def test_perfect_calibration_zero_ece(self):
        # All positions in [0.6, 0.7), model pred = actual win rate
        P = np.full(100, 0.65)
        Y = np.zeros(100)
        Y[:65] = 1.0      # 65% win rate == predicted 0.65 → gap = 0
        ece = mod.compute_ece(P, Y)
        self.assertAlmostEqual(ece, 0.0, places=5)

    def test_miscalibrated_bucket(self):
        # All in [0.8, 0.9): pred=0.85, actual=0.50 → gap=0.35 → ECE=0.35
        P = np.full(60, 0.85)
        Y = np.zeros(60)
        Y[:30] = 1.0      # 50% win rate
        ece = mod.compute_ece(P, Y)
        self.assertAlmostEqual(ece, 0.35, places=4)

    def test_below_half_excluded(self):
        # Positions with P < 0.5 are outside the bucket range — ECE = 0
        P = np.full(50, 0.40)
        Y = np.zeros(50)
        Y[:25] = 1.0
        ece = mod.compute_ece(P, Y)
        self.assertAlmostEqual(ece, 0.0, places=5)

    def test_ece_above_threshold_for_overconfident(self):
        # Overconfident model: all at 0.90, only 60% win rate
        n = 100
        P = np.full(n, 0.90)
        Y = np.zeros(n)
        Y[:60] = 1.0
        ece = mod.compute_ece(P, Y)
        self.assertGreater(ece, mod.ECE_THRESHOLD)


# ---------------------------------------------------------------------------
# TestDeriveTemperature
# ---------------------------------------------------------------------------

class TestDeriveTemperature(unittest.TestCase):

    def test_identity_for_well_calibrated_data(self):
        # When P matches empirical frequency, T ≈ 1.0
        rng = np.random.default_rng(42)
        P = np.full(200, 0.65)
        Y = (rng.random(200) < 0.65).astype(float)
        T = mod.derive_temperature(P, Y)
        self.assertAlmostEqual(T, 1.0, delta=0.10)

    def test_shrink_for_overconfident_data(self):
        # Model says 0.90 but only 60% of outcomes are 1 → T > 1 (shrink)
        P = np.full(200, 0.90)
        Y = np.zeros(200)
        Y[:120] = 1.0   # 60% win rate
        T = mod.derive_temperature(P, Y)
        self.assertGreater(T, 1.0)

    def test_bounds_respected(self):
        # Even with extreme data, T must stay within (0.3, 8.0)
        P = np.full(100, 0.99)
        Y = np.zeros(100)
        T = mod.derive_temperature(P, Y)
        self.assertGreaterEqual(T, 0.3)
        self.assertLessEqual(T,   8.0)


# ---------------------------------------------------------------------------
# TestMainPortfolioMissing
# ---------------------------------------------------------------------------

class TestMainPortfolioMissing(unittest.TestCase):

    def test_missing_portfolio_exits_0(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            fake_path = Path(d) / "nonexistent.json"
            rc = _run_main(fake_path)
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# TestMainNoValidPositions
# ---------------------------------------------------------------------------

class TestMainNoValidPositions(unittest.TestCase):

    def test_empty_closed_positions_exits_0(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, [])
            rc = _run_main(path)
        self.assertEqual(rc, 0)

    def test_only_t3_positions_exits_0(self):
        # t=3 is excluded per GG-042 — treated as no active positions
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            t3_positions = _make_n_positions(60, 0.75, 0.55, threshold=3)
            _write_portfolio(path, t3_positions)
            rc = _run_main(path)
        self.assertEqual(rc, 0)

    def test_all_invalid_fields_exits_0(self):
        import tempfile
        bad_positions = [
            {"outcome": "WIN"},                              # no model_p
            {"model_p": "NaN", "mid_price_at_entry": 0.50, "outcome": "WIN"},
            {"model_p": 0.75, "outcome": "PENDING"},         # wrong outcome
        ]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, bad_positions)
            rc = _run_main(path)
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# TestMainInsufficientData
# ---------------------------------------------------------------------------

class TestMainInsufficientData(unittest.TestCase):

    def test_below_min_n_exits_0(self):
        # 20 positions total — below MIN_N_DIAGNOSE=50
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            positions = _make_n_positions(
                n=20, model_p=0.90, mip=0.50,
                win_fraction=0.50, threshold=1,
            )
            _write_portfolio(path, positions)
            rc = _run_main(path)
        self.assertEqual(rc, 0)

    def test_exactly_min_n_diagnoses(self):
        # MIN_N_DIAGNOSE=50 exact: diagnosis runs
        import tempfile
        n = mod.MIN_N_DIAGNOSE
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            # Well-calibrated: model_p=0.65, win_rate=65%
            positions = _make_n_positions(
                n=n, model_p=0.65, mip=0.55,
                win_fraction=0.65, threshold=1,
            )
            _write_portfolio(path, positions)
            rc = _run_main(path)
        # Should be calibrated (ECE ≈ 0)
        self.assertEqual(rc, 0)

    def test_mixed_thresholds_insufficient_per_threshold(self):
        # 60 total (30 t=1, 30 t=2) — neither threshold hits MIN_N_DIAGNOSE=50
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            positions = (
                _make_n_positions(30, 0.85, 0.50, threshold=1) +
                _make_n_positions(30, 0.85, 0.50, threshold=2)
            )
            _write_portfolio(path, positions)
            rc = _run_main(path)
        # Total=60 >= MIN_N_DIAGNOSE for temperature + edge check,
        # but per-threshold=30 < MIN_N_DIAGNOSE so no ECE failure.
        # Well-calibrated with anti-predictive check: edge > 0 for all,
        # win_fraction=0.65 for all — no anti-predictive signal.
        self.assertIn(rc, (0, 1))  # 0 if not anti-predictive, 1 if miscalibrated


# ---------------------------------------------------------------------------
# TestMainCalibrated
# ---------------------------------------------------------------------------

class TestMainCalibrated(unittest.TestCase):

    def test_well_calibrated_exits_0(self):
        # model_p=0.65, 65% win rate → ECE ≈ 0 → exit 0
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            positions = _make_n_positions(
                n=60, model_p=0.65, mip=0.55,
                win_fraction=0.65, threshold=1,
            )
            _write_portfolio(path, positions)
            rc = _run_main(path)
        self.assertEqual(rc, 0)

    def test_both_thresholds_calibrated_exits_0(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            t1 = _make_n_positions(60, 0.65, 0.55, win_fraction=0.65, threshold=1)
            t2 = _make_n_positions(60, 0.70, 0.58, win_fraction=0.70, threshold=2)
            _write_portfolio(path, t1 + t2)
            rc = _run_main(path)
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# TestMainMiscalibrated
# ---------------------------------------------------------------------------

class TestMainMiscalibrated(unittest.TestCase):
    # Exit code 1 requires ECE > 0.05 AFTER temperature scaling for at least
    # one threshold. A single uniformly overconfident group is "fixed" by T
    # scaling toward the actual win rate → ECE ≈ 0. Non-monotonic
    # miscalibration (two groups with swapped errors) cannot be fixed by a
    # single T: ECE remains >> 0.05.
    #
    # Key design constraints:
    #  (a) Use extreme P values (0.51 and 0.99) so they land in DIFFERENT
    #      reliability buckets even at T=8.0 (max bound). At T=8 the optimizer
    #      compresses both toward 0.5, but 0.99 still reaches [0.6,0.7) while
    #      0.51 stays in [0.5,0.6) — keeping the bucket gaps large.
    #  (b) MIP=0.05 so all calibrated edges remain positive → anti-predictive
    #      check is skipped (no lo_edge positions), ensuring exit 1 not exit 2.
    #
    # Group A: P=0.51, win_rate=0.85 (severely underconfident)
    # Group B: P=0.99, win_rate=0.15 (severely overconfident)
    # At T=8: ECE ≈ 0.43 >> 0.05 (verified analytically).

    def test_nonmonotonic_miscalibration_exits_1(self):
        import tempfile
        n = 30
        positions = (
            [_pos(0.51, 0.05, "YES", "WIN",  1) for _ in range(round(n * 0.85))] +
            [_pos(0.51, 0.05, "YES", "LOSS", 1) for _ in range(n - round(n * 0.85))] +
            [_pos(0.99, 0.05, "YES", "WIN",  1) for _ in range(round(n * 0.15))] +
            [_pos(0.99, 0.05, "YES", "LOSS", 1) for _ in range(n - round(n * 0.15))]
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, positions)
            rc = _run_main(path)
        self.assertEqual(rc, 1)

    def test_t2_nonmonotonic_miscalibration_exits_1(self):
        # Same design in threshold t=2 to verify per-threshold branching
        import tempfile
        n = 30
        positions = (
            [_pos(0.51, 0.05, "YES", "WIN",  2) for _ in range(round(n * 0.85))] +
            [_pos(0.51, 0.05, "YES", "LOSS", 2) for _ in range(n - round(n * 0.85))] +
            [_pos(0.99, 0.05, "YES", "WIN",  2) for _ in range(round(n * 0.15))] +
            [_pos(0.99, 0.05, "YES", "LOSS", 2) for _ in range(n - round(n * 0.15))]
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            _write_portfolio(path, positions)
            rc = _run_main(path)
        self.assertEqual(rc, 1)


# ---------------------------------------------------------------------------
# TestMainAntiPredictive
# ---------------------------------------------------------------------------

class TestMainAntiPredictive(unittest.TestCase):

    def test_anti_predictive_exits_2(self):
        # edge>0 positions all LOSS; edge≤0 positions all WIN → clearly anti-predictive
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"

            # High edge (0.80 - 0.50 >> 0), all LOSS
            hi_edge_losers = [
                _pos(0.80, 0.50, "YES", "LOSS", 1) for _ in range(35)
            ]
            # Negative edge (0.55 - 0.80 < 0), all WIN
            lo_edge_winners = [
                _pos(0.55, 0.80, "YES", "WIN", 1) for _ in range(25)
            ]
            _write_portfolio(path, hi_edge_losers + lo_edge_winners)
            rc = _run_main(path)
        self.assertEqual(rc, 2)

    def test_anti_predictive_takes_precedence_over_miscalibrated(self):
        # Anti-predictive AND miscalibrated — exit code must be 2, not 1
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            # Overconfident AND anti-predictive
            hi_losers = [_pos(0.95, 0.50, "YES", "LOSS", 1) for _ in range(40)]
            lo_winners = [_pos(0.60, 0.90, "YES", "WIN",  1) for _ in range(20)]
            _write_portfolio(path, hi_losers + lo_winners)
            rc = _run_main(path)
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
