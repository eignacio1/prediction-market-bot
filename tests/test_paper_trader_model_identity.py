"""T-589 D6 -- open_position must refuse a position with no real model_identity."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c5_execution.paper_trader import (
    MissingModelIdentityError,
    PaperTrader,
)


def _approval(**extra) -> dict:
    return {"approval_status": "APPROVED", "approved_size": 5.0, "approved_direction": "YES",
            "risk_eval_id": "R1", "forecast_id": "F1", **extra}


def _open(tr: PaperTrader, approval: dict):
    return tr.open_position(approval, "KXMLBHIT-26SEP29TESTTST-P1-1", 0.45, 0.02, "2026-09-29",
                            player_name="P", player_id=1, kalshi_threshold=1)


@pytest.mark.parametrize("bad", [None, "", "   ", "UNKNOWN", "unknown", " Unknown ", 7, ["x"]])
def test_missing_or_placeholder_identity_fails_loudly_and_writes_nothing(tmp_path, bad):
    path = tmp_path / "p.json"
    tr = PaperTrader(path, MagicMock())
    tr._save()
    before = path.read_bytes()
    approval = _approval() if bad is None else _approval(model_identity=bad)
    with pytest.raises(MissingModelIdentityError):
        _open(tr, approval)
    assert path.read_bytes() == before
    assert tr._state["open_positions"] == []


def test_key_absent_fails(tmp_path):
    tr = PaperTrader(tmp_path / "p.json", MagicMock())
    with pytest.raises(MissingModelIdentityError):
        _open(tr, _approval())


def test_real_identity_is_persisted_verbatim(tmp_path):
    path = tmp_path / "p.json"
    tr = PaperTrader(path, MagicMock())
    ok, pos = _open(tr, _approval(model_identity="  T4M-PROJ-v3 "))
    assert ok
    assert pos["model_identity"] == "T4M-PROJ-v3"
    assert json.loads(path.read_text())["open_positions"][0]["model_identity"] == "T4M-PROJ-v3"


def test_pass_or_zero_size_still_returns_without_identity(tmp_path):
    """No position is written, so no identity is needed (early return unchanged)."""
    tr = PaperTrader(tmp_path / "p.json", MagicMock())
    assert _open(tr, {"approved_size": 0.0, "approved_direction": "YES"}) == (True, {})
    assert _open(tr, _approval(approved_direction="PASS")) == (True, {})


def test_kalshi_order_never_submitted_without_identity(tmp_path):
    kc = MagicMock()
    tr = PaperTrader(tmp_path / "p.json", MagicMock(), kalshi_client=kc) \
        if "kalshi_client" in PaperTrader.__init__.__code__.co_varnames else None
    if tr is None:
        pytest.skip("PaperTrader has no kalshi_client ctor arg")
    with pytest.raises(MissingModelIdentityError):
        _open(tr, _approval())
    kc.submit_order.assert_not_called()
