"""Read-only probe: what does the T4 open_position call shape write for model_identity?
Approval mirrors run_t4_mlb_live.py:1634 (keys added after engine.evaluate_forecast)."""
import sys, tempfile, json
from pathlib import Path
sys.path.insert(0, sys.argv[1] + "/src"); sys.path.insert(0, sys.argv[1] + "/tests")
from test_paper_trader import _make_logger, _make_approval
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
t = PaperTrader(Path(tempfile.mkdtemp()) / "p.json", _make_logger())
ap = {**_make_approval(1.0), "model_p": 0.6, "edge": 0.05, "gross_edge": 0.06, "band": "T4M-PROJ",
      "entry_price_paid": 0.5, "price_stratum": "mid", "contracts": 2}
ap.pop("model_identity", None)  # T4 sends none (run_t4_mlb_live.py:1634); strip helper-injected key
print("approval has model_identity key:", "model_identity" in ap, "| run_provenance key:", "run_provenance" in ap)
try:
    ok, pos = t.open_position(approval=ap, player_name="X", player_id=1, kalshi_ticker="KXMLBHIT-26SEP30AAABBB-X1-1",
        kalshi_threshold=1, mid_price=0.5, vig=0.02, game_date="2026-09-30", session_id="probe", pool_isolated=True,
        h_so_far_at_entry=0, ab_remaining_at_entry=3)
    print("RESULT ok=%s model_identity=%r" % (ok, pos.get("model_identity")))
except Exception as e:
    print("RAISED %s: %s" % (type(e).__name__, e))
