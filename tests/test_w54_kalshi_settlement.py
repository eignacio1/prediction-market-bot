"""ADR-0071 (GG-440/GG-450): Kalshi settlement is the paper resolution source."""
import sys
from pathlib import Path

import pytest

from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def _trader(tmp_path):
    t = PaperTrader(tmp_path / "p.json", AuditLogger(log_path=tmp_path / "a.jsonl"))
    return t


def _seed(t, direction="YES", size=10.0, mid=0.40, vig=0.02, pid="p1"):
    t._state["open_positions"].append({
        "position_id": pid, "player_name": "X", "direction": direction,
        "size_usd": size, "mid_price_at_entry": mid, "vig_at_entry": vig,
        "model_p": 0.5, "logic_epoch": 12,
    })
    t._save()


def test_yes_result_books_win_for_yes(tmp_path):
    t = _trader(tmp_path); _seed(t)
    ok, c = t.settle_position_from_venue("p1", "yes", 1.0)
    ask = 0.41
    assert ok and c["outcome"] == "WIN" and c["cancelled"] is False
    assert c["pnl"] == pytest.approx(round(10 * (1 - ask) / ask, 4))
    assert c["settlement_source"] == "kalshi"


def test_no_result_books_loss_for_yes(tmp_path):
    t = _trader(tmp_path); _seed(t)
    _, c = t.settle_position_from_venue("p1", "no", 0.0)
    assert c["outcome"] == "LOSS" and c["pnl"] == -10.0


def test_no_direction_wins_on_no(tmp_path):
    t = _trader(tmp_path); _seed(t, direction="NO")
    _, c = t.settle_position_from_venue("p1", "no", 0.0)
    assert c["outcome"] == "WIN" and c["pnl"] > 0


def test_cancelled_booked_at_settlement_value_and_flagged(tmp_path):
    t = _trader(tmp_path); _seed(t)
    _, c = t.settle_position_from_venue("p1", "scalar", 0.60)
    ask = 0.41
    assert c["cancelled"] is True and c["outcome"] == "CANCELLED"
    assert c["pnl"] == pytest.approx(round(10 * (0.60 - ask) / ask, 4))
    # cancelled does not feed the same-day circuit breaker
    assert t._state.get("current_daily_loss", 0.0) == 0.0


def test_cancelled_no_direction_uses_complement(tmp_path):
    t = _trader(tmp_path); _seed(t, direction="NO")
    _, c = t.settle_position_from_venue("p1", "scalar", 0.30)
    ask = 0.60 + 0.01
    assert c["pnl"] == pytest.approx(round(10 * (0.70 - ask) / ask, 4))


def test_cancelled_requires_value(tmp_path):
    t = _trader(tmp_path); _seed(t)
    with pytest.raises(ValueError):
        t.settle_position_from_venue("p1", "scalar", None)


def test_idempotent_unknown_id(tmp_path):
    t = _trader(tmp_path)
    assert t.settle_position_from_venue("nope", "yes", 1.0) == (True, {})


def test_cancelled_counts_in_realized_pnl_but_not_win_rate(tmp_path):
    t = _trader(tmp_path); _seed(t); _seed(t, pid="p2")
    t.settle_position_from_venue("p1", "scalar", 0.0)
    t.settle_position_from_venue("p2", "yes", 1.0)
    s = t.summary()
    assert s["total_realized_pnl"] == pytest.approx(-10.0 + round(10 * 0.59 / 0.41, 4), abs=1e-3)
    assert s["win_rate"] == 1.0


def test_filter_clean_drops_cancelled():
    import run_band_monitor as rbm
    recs = [{"logic_epoch": rbm.CURRENT_LOGIC_EPOCH, "cancelled": True},
            {"logic_epoch": rbm.CURRENT_LOGIC_EPOCH}]
    assert len(rbm.filter_clean(recs, "UNTAGGED")) == 1


def test_settlement_value_parsing():
    from prediction_market_bot.run_resolve_mlb import _settlement_value
    assert _settlement_value({"settlement_value_dollars": "0.3400"}) == 0.34
    assert _settlement_value({"settlement_value": 66}) == 0.66
    assert _settlement_value({}) is None
