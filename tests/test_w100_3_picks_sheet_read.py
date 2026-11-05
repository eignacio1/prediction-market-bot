import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import picks_sheet_read as r  # noqa: E402
import box_tasks  # noqa: E402


def test_summary_counts():
    pk = lambda arm, t, rs, res=None: {"arm": arm, "ticker": t, "pick": "x", "bot_prob_for_pick": .6, "kalshi_price_yes": .5,
                                         "edge_after_fee": .05, "reasons": rs, "result": res, "demo_order": None}
    sheet = {"date": "d", "built_utc": "t", "n_picks": 3, "notes": ["n1"], "games": [
        {"game": "G1", "arms_disagree": True, "picks": [pk("a", "T1", ["why"], {"outcome": "hit"}), pk("b", "T1", ["no reasons available (old)"])]},
        {"game": "G2", "arms_disagree": False, "picks": [pk("a", "T2", ["why"])]}]}
    txt = "\n".join(r.summarize(sheet))
    assert "picks with stored reasons: 2/3" in txt and "hit=1" in txt and "open=2" in txt and "arms disagree: 1" in txt and "note: n1" in txt


def test_task_registered_read_only():
    assert box_tasks.TASKS["picks_sheet_read"].endswith("scripts/picks_sheet_read.py")
