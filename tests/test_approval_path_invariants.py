"""
T-325 (Workstream C1) — invariant/property tests on the bet-approval path.

Encodes the exact bug classes behind GG-087 and GG-077 as properties so a
regression in either mechanism fails a fast, general test rather than
waiting to be caught in a resolved-bet audit:

  (i)   direction symmetry (GG-087) — a NO bet derived from a negative
        gross_edge and the mirror YES bet derived from the positive
        gross_edge of equal magnitude must be treated with equal-magnitude
        directional edge; negative gross_edge must be actionable, not
        silently discarded.
  (ii)  fee-sign invariance (GG-077) — paper_trader.py's inline
        fee_net_edge computation (open_position()) and
        run_mlb_paper_trade.py's independent _directional_edge() must
        agree for both YES and NO across randomized inputs.
  (iii) edge-frame / no-double-flip invariance — open_position() must
        derive fee_net_edge from approval["gross_edge"] (raw YES-frame,
        ADR-0016), never from re-flipping an already direction-flipped
        approval["edge"] value, even when a caller (e.g. run_t4_mlb_live.py)
        supplies both keys in the same approval dict.

Governing principle (ITERATION_PLAN_calibration_hardening.md): a test here
is not done until it is demonstrably tied to the exact GG-087/GG-077 bug
mechanics -- not a restatement of "the code does what the code does."
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.run_mlb_paper_trade import _directional_edge

_PAST_DATE = "2026-05-30"
_RUN_T4_MLB_LIVE = _SRC / "prediction_market_bot" / "run_t4_mlb_live.py"


def _make_logger():
    logger = MagicMock()
    logger.info.return_value = True
    logger.warning.return_value = True
    logger.error.return_value = True
    logger.log.return_value = True
    return logger


def _make_approval(size: float, direction: str = "YES", **extra) -> dict:
    return {
        "approval_status": "APPROVED",
        "approved_size": size,
        "approved_direction": direction,
        "risk_eval_id": "RISK-TEST001",
        "forecast_id": "FCST-TEST001",
        **extra,
    }


def _open_position_isolated(approval: dict, mid: float, vig: float = 0.02) -> dict:
    """Run the real open_position() path in a throwaway temp dir, pool_isolated
    so bankroll-sufficiency checks never interfere with property inputs."""
    with tempfile.TemporaryDirectory() as d:
        trader = PaperTrader(Path(d) / "p.json", _make_logger())
        ok, pos = trader.open_position(
            approval=approval,
            player_name="Test", player_id=1,
            kalshi_ticker="KXMLBHIT-TEST", kalshi_threshold=1,
            mid_price=mid, vig=vig, game_date=_PAST_DATE,
            pool_isolated=True,
        )
        assert ok
        return pos


# ---------------------------------------------------------------------------
# (i) Direction symmetry — GG-087
# ---------------------------------------------------------------------------
#
# run_t4_mlb_live.py's direction-derivation block (source lines ~1027-1037)
# is inline in a large polling-loop function, not independently importable.
# _t4_derive_direction() below is a pure transcription of that block. The
# pin test immediately following asserts the live source still contains this
# exact text, so an edit to the real block that isn't mirrored here fails
# loudly instead of silently invalidating the property coverage below.

_T4_DIRECTION_BLOCK_SOURCE = '''\
            if gross_edge > 0.0:
                direction = "YES"
                directional_gross_edge = gross_edge
            elif gross_edge < 0.0:
                direction = "NO"
                directional_gross_edge = -gross_edge
            else:
                evaluated += 1
                continue

            directional_net_edge = directional_gross_edge - kalshi_fee
'''


def _t4_derive_direction(gross_edge: float, kalshi_fee: float):
    """Pure transcription of _T4_DIRECTION_BLOCK_SOURCE. Returns
    (direction, directional_gross_edge, directional_net_edge) or None for
    the zero-edge no-op branch."""
    if gross_edge > 0.0:
        direction = "YES"
        directional_gross_edge = gross_edge
    elif gross_edge < 0.0:
        direction = "NO"
        directional_gross_edge = -gross_edge
    else:
        return None
    directional_net_edge = directional_gross_edge - kalshi_fee
    return direction, directional_gross_edge, directional_net_edge


class TestT4DirectionBlockSourcePin:
    @pytest.mark.property
    @pytest.mark.unit
    def test_live_source_still_matches_pinned_transcription(self):
        text = _RUN_T4_MLB_LIVE.read_text()
        assert _T4_DIRECTION_BLOCK_SOURCE in text, (
            "run_t4_mlb_live.py's GG-087 direction-derivation block has "
            "changed. Update _t4_derive_direction() and "
            "_T4_DIRECTION_BLOCK_SOURCE in this file to match before "
            "trusting the direction-symmetry property tests below."
        )


class TestDirectionSymmetry:
    """GG-087: the live T4 loop was structurally YES-only prior to the fix
    -- any gross_edge <= 0 was treated as noise and the cycle was skipped,
    discarding NO-direction edge signal measured at 41.6x the volume of the
    YES-side signal acted on. Post-fix, direction must be derived from the
    sign of gross_edge, and the magnitude of the directional edge carried
    forward must be identical regardless of which side of zero gross_edge
    fell on."""

    @pytest.mark.property
    @pytest.mark.unit
    def test_negative_gross_edge_is_actionable_not_discarded(self):
        # This is the exact pre-fix failure mode: a real, tradeable NO
        # signal (gross_edge=-0.15) must resolve to an actionable NO bet,
        # not be dropped.
        result = _t4_derive_direction(-0.15, 0.01)
        assert result is not None
        direction, directional_gross_edge, _ = result
        assert direction == "NO"
        assert directional_gross_edge == pytest.approx(0.15)

    @pytest.mark.property
    @pytest.mark.unit
    @given(
        g=st.floats(min_value=-0.99, max_value=0.99, allow_nan=False, allow_infinity=False)
        .filter(lambda x: abs(x) > 1e-9),
        fee=st.floats(min_value=0.0, max_value=0.02, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=300, deadline=None)
    def test_direction_symmetry_mirrors_under_negation(self, g, fee):
        pos_result = _t4_derive_direction(g, fee)
        neg_result = _t4_derive_direction(-g, fee)
        assert pos_result is not None and neg_result is not None

        dir_pos, dge_pos, dne_pos = pos_result
        dir_neg, dge_neg, dne_neg = neg_result

        # Mirrored raw edge -> opposite direction label, but identical
        # directional-edge magnitude. A YES-only bug (or any asymmetric
        # handling of the sign) breaks this equality.
        assert dir_pos != dir_neg
        assert dge_pos == pytest.approx(dge_neg)
        assert dge_pos == pytest.approx(abs(g))
        assert dne_pos == pytest.approx(dne_neg)


# ---------------------------------------------------------------------------
# (ii) Fee-sign invariance — GG-077
# ---------------------------------------------------------------------------
#
# Two independent real implementations of the same fee-netting formula
# exist in production: paper_trader.py's inline computation inside
# open_position(), and run_mlb_paper_trade.py's standalone _directional_edge().
# GG-077 was exactly a divergence between these mechanics (the flip was
# applied to fee_contaminated but not to fee_net_edge). This property drives
# both real functions with the same randomized inputs and asserts agreement.

class TestFeeSignInvariance:
    @pytest.mark.property
    @pytest.mark.unit
    @given(
        gross_edge=st.floats(min_value=-0.99, max_value=0.99, allow_nan=False, allow_infinity=False)
        .filter(lambda x: abs(x) > 1e-9),
        mid=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
        direction=st.sampled_from(["YES", "NO"]),
    )
    @settings(max_examples=300, deadline=None)
    def test_paper_trader_matches_directional_edge_fn(self, gross_edge, mid, direction):
        fee = round(0.07 * mid * (1.0 - mid), 6)
        expected = round(_directional_edge(direction, gross_edge, fee), 6)

        approval = _make_approval(10.0, direction, gross_edge=gross_edge, model_p=0.5)
        pos = _open_position_isolated(approval, mid=mid)

        assert pos["fee_net_edge"] == expected


# ---------------------------------------------------------------------------
# (iii) Edge-frame / no-double-flip invariance
# ---------------------------------------------------------------------------
#
# run_t4_mlb_live.py's fc_record carries BOTH gross_edge (raw YES-frame,
# ADR-0016) and edge (already direction-flipped + fee-netted). paper_trader.py
# open_position() must derive fee_net_edge from gross_edge alone
# (approval.get("gross_edge", approval.get("edge", 0.0)) -- gross_edge wins
# when present) and must never re-flip the already-flipped edge value on
# top of it. A backward-compat fallback path (gross_edge absent, only edge
# present) must apply exactly one flip, not zero and not two.

class TestNoDoubleFlip:
    @pytest.mark.property
    @pytest.mark.unit
    @given(
        p_t4=st.floats(min_value=0.05, max_value=0.95, allow_nan=False, allow_infinity=False),
        mip=st.floats(min_value=0.05, max_value=0.95, allow_nan=False, allow_infinity=False),
        vig=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=300, deadline=None)
    def test_no_double_flip_when_caller_supplies_both_keys(self, p_t4, mip, vig):
        gross_edge = p_t4 - mip - vig
        assume(abs(gross_edge) > 1e-9)
        direction = "YES" if gross_edge > 0 else "NO"
        fee = round(0.07 * mip * (1.0 - mip), 6)
        directional_gross = gross_edge if direction == "YES" else -gross_edge
        # This is exactly what run_t4_mlb_live.py stores as fc_record["edge"]:
        # already direction-flipped and fee-netted before it ever reaches
        # open_position().
        directional_net_edge = directional_gross - fee

        approval = _make_approval(
            10.0, direction,
            gross_edge=gross_edge,
            edge=directional_net_edge,
            model_p=p_t4,
        )
        pos = _open_position_isolated(approval, mid=mip, vig=vig)

        correct = round(directional_gross - fee, 6)
        assert pos["fee_net_edge"] == correct

        if direction == "NO":
            # A double-flip regression would instead re-flip the
            # already-flipped edge value: -directional_net_edge - fee.
            # Assert we are not silently landing there.
            wrong_double_flip = round(-directional_net_edge - fee, 6)
            if wrong_double_flip != correct:
                assert pos["fee_net_edge"] != wrong_double_flip

    @pytest.mark.property
    @pytest.mark.unit
    def test_fallback_to_edge_key_is_single_flip_only(self):
        # Backward-compat path (paper_trader.py: approval.get("gross_edge",
        # approval.get("edge", 0.0))) -- older callers that only ever wrote
        # "edge" (raw YES-frame) must still get exactly one flip for NO, not
        # a double flip and not zero flips.
        mid = 0.40
        fee = round(0.07 * mid * (1.0 - mid), 6)
        raw_yes_frame_edge = 0.12  # only "edge" present, no "gross_edge" key
        approval = _make_approval(10.0, "NO", edge=raw_yes_frame_edge, model_p=0.28)

        pos = _open_position_isolated(approval, mid=mid)

        assert pos["fee_net_edge"] == round(-raw_yes_frame_edge - fee, 6)
