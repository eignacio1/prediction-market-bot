"""W111.3 Part A: export the W110.5 per-leaf arm map to 12_EXPLORATORY/retro_route/leaf_map.json (copied verbatim into decision_trees/ for the router).
usage: export_leaf_map.py [results.json]. Fit-window fields only decide the arm; held-out fields are carried for the
log (status), never used to choose. Pure file transform, no network."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _fence import safe_out

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else f"{HERE}/results.json"
OUT = f"{HERE}/leaf_map.json"  # fenced; copy to src/prediction_market_bot/decision_trees/leaf_map.json (a test asserts they match)
d = json.load(open(SRC))["route"]
leaves = {}
for l in d["leaves"]:
    k = "|".join(str(x) for x in l["leaf"])
    leaves[k] = {"arm": l["arm"], "thin": l["thin"], "fit_rows": l["fit_rows"], "fit_games": l["fit_games"],
                 "fit": {a: [round(m, 5), n] for a, (m, n) in l["fit"].items()},
                 "test": ({k2: l[k2] for k2 in ("test_mean", "test_lo", "test_hi", "test_n_games") if k2 in l} or None),
                 "bh": l["bh"]}
doc = {"source": "12_EXPLORATORY/retro_route/results.json (W110.5)", "key": "sport|market_type|band|favprice_bin|move_bin",
       "fit_games": d["fit_games"], "test_games": d["test_games"],
       "note": "arm chosen on the fit window only; test fields are the held-out status carried for the log",
       "leaves": leaves}
json.dump(doc, open(safe_out(os.path.normpath(OUT)), "w"), indent=0, sort_keys=True)
print(len(leaves), "leaves ->", os.path.normpath(OUT))
