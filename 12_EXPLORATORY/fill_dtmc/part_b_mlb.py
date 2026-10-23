"""W86.3: E3 identity for the MLB paper books (the population behind E3 = 25.4% / 28.9% vs 48.3% / 52.1%).

win_fill - win_nonfill = (win_fill - mid_fill) [adverse selection] + (mid_fill - mid_nonfill) [price chosen]
                         + (mid_nonfill - win_nonfill). mid = price of the side taken (mid_price_at_entry), same
for fills and non-fills, so the middle term is selection-by-price, NOT queue position: queue position and time
resting are not logged for these books at all.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util
_s = importlib.util.spec_from_file_location("pb", Path(__file__).with_name("part_b_fills.py"))
pb = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pb)


def run(d, book, status):
    pos = json.load(open(Path(d) / book))["closed_positions"]
    fs = {}
    for l in open(Path(d) / status):
        r = json.loads(l)
        fs[r["position_id"]] = r["fill_class"]
    f, n = [], []
    for x in pos:
        if x.get("outcome") not in ("WIN", "LOSS"):
            continue
        k = fs.get(x["position_id"])
        row = (x["kalshi_ticker"].split("-")[1], float(x["outcome"] == "WIN"), x["mid_price_at_entry"])
        (f if k == "CONFIRMED_FILLED" else n if k == "CONFIRMED_NOT_FILLED" else []).append(row)
    m = lambda rows, i: sum(r[i] for r in rows) / len(rows)
    wf, wn, pf, pn = m(f, 1), m(n, 1), m(f, 2), m(n, 2)
    return {"n_fills": len(f), "n_nonfills": len(n), "win_fill": wf, "win_nonfill": wn, "gap": wf - wn,
            "mid_fill": pf, "mid_nonfill": pn,
            "adverse_selection (win_fill - mid_fill)": wf - pf, "price_chosen (mid_fill - mid_nonfill)": pf - pn,
            "nonfill_edge (mid_nonfill - win_nonfill)": pn - wn,
            "win_fill_ci95_game_clustered": pb.wilson_game_boot([(g, w) for g, w, _ in f]),
            "win_nonfill_ci95_game_clustered": pb.wilson_game_boot([(g, w) for g, w, _ in n])}


if __name__ == "__main__":
    out = {"t4_mlb": run(sys.argv[1], "paper_portfolio_mlb_t4.json", "t4_mlb_fill_status.jsonl"),
           "t1_mlb": run(sys.argv[1], "paper_portfolio_mlb.json", "t1_mlb_fill_status.jsonl")}
    p = safe_out(sys.argv[2])
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
