"""T-595 / Wave 41 D2: forward-only model_identity stamping for T4M-PROJ.

Nothing here touches, relabels or backfills an existing row (GG-228).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
os.environ.setdefault("BOT_ENV", "paper")
os.environ.setdefault("BOT_C4_ACTIVE", "true")

import prediction_market_bot.run_t4_mlb_live as runner  # noqa: E402
from prediction_market_bot import logic_epoch as le  # noqa: E402

_spec = importlib.util.spec_from_file_location("build_t4_resolved_ledger", ROOT / "scripts/build_t4_resolved_ledger.py")
builder = importlib.util.module_from_spec(_spec)
sys.path.insert(0, str(ROOT / "scripts"))
_spec.loader.exec_module(builder)


# --- step 1: the stamp -------------------------------------------------------
def test_identity_shrunk_only_when_exactly_true():
    assert runner.t4m_proj_model_identity(True) == runner.T4M_PROJ_MODEL_IDENTITY
    for v in (False, None, 1, "yes", 0):
        assert runner.t4m_proj_model_identity(v) == runner.T4M_PROJ_MODEL_IDENTITY_RAW_FALLBACK


def _ctx(tmp_path, fc):
    (tmp_path / "pregame_mlb_20260930.json").write_text(json.dumps({"forecasts": [fc], "sport": "mlb"}))
    with patch.object(runner, "_LOGS_DIR", tmp_path):
        by_pid, _, _ = runner._load_pregame_context()
    return by_pid[1][0]


_FC = {"player_id": 1, "player_name": "A B", "kalshi_ticker": "KXMLBHIT-26SEP30AAABBB-X1-1",
       "kalshi_threshold": 1, "p_estimate": 0.6, "ba_l10": 0.27}


def test_loader_flags_shrunk_present(tmp_path):
    c = _ctx(tmp_path, {**_FC, "ba_l10_shrunk": 0.255})
    assert c["ba_l10_shrunk_present"] is True and c["ba_l10_shrunk"] == 0.255


def test_loader_flags_shrunk_absent(tmp_path):
    c = _ctx(tmp_path, dict(_FC))
    assert c["ba_l10_shrunk_present"] is False and c["ba_l10_shrunk"] == 0.27


# --- step 3: registry --------------------------------------------------------
def test_registry_classification():
    row = lambda i: {"model_identity": i}
    assert le.evidence_class(row(runner.T4M_PROJ_MODEL_IDENTITY)) == le.EVIDENCE_MODEL
    assert le.evidence_class(row(runner.T4M_PROJ_MODEL_IDENTITY_RAW_FALLBACK)) == le.EVIDENCE_UNATTRIBUTED
    assert le.evidence_class(row("UNKNOWN")) == le.EVIDENCE_UNATTRIBUTED
    assert le.evidence_class({}) == le.EVIDENCE_UNATTRIBUTED


def test_registry_does_not_attribute_historical_shape():
    # A historical row: epoch-clean but identity "UNKNOWN" -> not countable.
    epoch = le.CURRENT_LOGIC_EPOCH
    assert not le.is_countable_evidence({"logic_epoch": epoch, "model_identity": "UNKNOWN"}, "UNTAGGED")
    assert le.is_countable_evidence({"logic_epoch": epoch, "model_identity": runner.T4M_PROJ_MODEL_IDENTITY}, "UNTAGGED")


# --- step 2: builder passthrough --------------------------------------------
def _closed(**kw):
    p = {"position_id": "p1", "forecast_id": "f1", "kalshi_ticker": "KXMLBHIT-26SEP30AAABBB-X1-1",
         "outcome": "WIN", "model_p": 0.6, "mid_price_at_entry": 0.5, "vig_at_entry": 0.02,
         "direction": "YES", "kalshi_threshold": 1, "logic_epoch": 1}
    p.update(kw)
    return p


def _build(tmp_path, positions):
    f = tmp_path / "pf.json"
    f.write_text(json.dumps({"closed_positions": positions}))
    return builder.build_ledger(f)[0]


def test_builder_passes_identity_verbatim(tmp_path):
    rows = _build(tmp_path, [_closed(model_identity=runner.T4M_PROJ_MODEL_IDENTITY),
                             _closed(position_id="p2", model_identity="UNKNOWN")])
    assert [r["model_identity"] for r in rows] == [runner.T4M_PROJ_MODEL_IDENTITY, "UNKNOWN"]


def test_builder_does_not_invent_identity_for_old_rows(tmp_path):
    (row,) = _build(tmp_path, [_closed()])
    assert "model_identity" in row and row["model_identity"] is None
    assert le.evidence_class(row) == le.EVIDENCE_UNATTRIBUTED


# --- PaperTrader carries the stamp ------------------------------------------
def test_paper_trader_stamps_supplied_identity():
    from test_paper_trader import _make_logger, _make_approval
    from prediction_market_bot.c5_execution.paper_trader import PaperTrader
    t = PaperTrader(Path(tempfile.mkdtemp()) / "p.json", _make_logger())
    ap = {**_make_approval(1.0), "model_p": 0.6, "edge": 0.05, "gross_edge": 0.06, "band": "T4M-PROJ",
          "entry_price_paid": 0.5, "price_stratum": "mid", "contracts": 2,
          "model_identity": runner.T4M_PROJ_MODEL_IDENTITY}
    ok, pos = t.open_position(approval=ap, player_name="X", player_id=1, kalshi_ticker="KXMLBHIT-26SEP30AAABBB-X1-1",
        kalshi_threshold=1, mid_price=0.5, vig=0.02, game_date="2026-09-30", session_id="t", pool_isolated=True,
        h_so_far_at_entry=0, ab_remaining_at_entry=3)
    assert ok and pos["model_identity"] == runner.T4M_PROJ_MODEL_IDENTITY
