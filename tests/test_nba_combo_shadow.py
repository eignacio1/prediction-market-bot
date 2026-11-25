"""W126.4 Part C: the combo shadow writer is off by default and its pure core logs engine P, product, quote state and unpriced legs."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import nba_combo_shadow as W  # noqa: E402
from prediction_market_bot.nba_engine.sgp_price import GameDraws  # noqa: E402

SUF = "26NOV24BOSWAS"
NOW = datetime(2026, 11, 24, 22, 0, tzinfo=timezone.utc)


def _combo(t, legs, **kw):
    return {"ticker": t, "mve_selected_legs": [{"event_ticker": l.split("-")[0] + "-" + SUF, "market_ticker": l, "side": s} for l, s in legs], **kw}


def _g():
    r = np.random.default_rng(0)
    return GameDraws(100 + r.integers(0, 20, 5000), 100 + r.integers(0, 20, 5000), {})


def test_off_by_default(monkeypatch, capsys):
    monkeypatch.delenv("PM_COMBO_SHADOW", raising=False)
    assert W.main([]) == 0 and "COMBO_SHADOW_OFF" in capsys.readouterr().out


def test_rows_carry_quote_engine_p_and_unpriced_legs():
    ml, tot, stl = f"KXNBAGAME-{SUF}-WAS", f"KXNBATOTAL-{SUF}-215", f"KXNBASTL-{SUF}-BOSJTATUM0-2"
    quoted = _combo("C1", [(ml, "yes"), (tot, "no")], yes_ask_dollars="0.2", yes_ask_size_fp="30", volume_fp="0")
    unp = _combo("C2", [(ml, "yes"), (stl, "yes")], yes_bid_dollars="0.01", yes_bid_size_fp="5")
    late = _combo("C3", [(ml, "yes")], yes_ask_dollars="0.5", yes_ask_size_fp="9")
    tips = lambda s: NOW + timedelta(minutes=120)
    rows = W.build_rows([quoted, unp], lambda s: _g(), tips, NOW, "r1")
    a, b = rows
    assert a["quote_state"] == "-ask" and a["yes_ask"] == 0.2 and 0 < a["engine_p"] < 0.5 and a["p_product_of_legs"] is not None
    assert a["fee_at_ask_default"] == 0.0112 and a["fee_multiplier_verified"] is False
    assert b["engine_p"] is None and b["legs_unpriced"][0]["reason"] == "steals_not_modelled" and b["p_priced_subset"] is not None
    assert W.build_rows([late], lambda s: _g(), lambda s: NOW + timedelta(minutes=400), NOW, "r1") == []   # outside the 0-3h window
