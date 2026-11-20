"""W121.2: results.json (score_props.py) -> decision_trees/leaf_maps/nba_props_v2.json.

Run: python3 12_EXPLORATORY/nba_props_splits/build_map.py
`leaves` are the market-state leaves in the v1 record format (arm from the fit window only, held-out carried for the log).
`splits` are every scored (split x split-leaf x leaf) cell with its verdict; only `kept` ones can change an arm at runtime,
and `earned` (BH-significant) is carried so the log says which is which. Nothing here sets an order or a stake."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402

# Emitted inside 12_EXPLORATORY (fence); the reviewed copy is placed at
# src/prediction_market_bot/decision_trees/leaf_maps/nba_props_v2.json by a normal committed change.
OUT = HERE / "nba_props_v2.candidate.json"


def main() -> None:
    r = json.loads((HERE / "results.json").read_text())
    leaves = {}
    for m in r["market_state"]:
        lid = "|".join(str(x) for x in m["leaf"])
        thin = bool(m.get("thin"))
        test = None
        if m.get("test_games") is not None and "test_mean" in m:
            test = {"games": m["test_games"], "rows": m.get("test_rows"), "mean": m["test_mean"],
                    "ci": [m.get("ci_lo"), m.get("ci_hi")], "p": m.get("p")}
        leaves[lid] = {"arm": m.get("arm", "NO_BET"), "thin": thin, "bh": False,
                       "fit": {a: v for a, v in (m.get("fit_means") or {}).items() if v is not None},
                       "fit_games": m["fit_games"], "fit_rows": m["fit_rows"], "test": test}
    splits = []
    for c in r["cells"]:
        splits.append({"split": c["split"], "split_leaf": c["split_leaf"], "leaf": "|".join(str(x) for x in c["leaf"]),
                       "arm": c.get("arm", "NO_BET"), "kept": bool(c.get("kept")), "earned": c.get("why") == "kept_earned",
                       "why": c.get("why", "thin"),
                       "bh": bool(c.get("bh")), "test_games": c.get("test_games"), "test_mean": c.get("test_mean")})
    doc = {"version": "nba_props_v2", "key": "sport|market_type|band|favprice_bin|move_bin",
           "source": "12_EXPLORATORY/nba_props_splits/results.json (EXP-NBAPROPS-001, PREREG ec39007)",
           "rule": "fit earliest 70% of games, score latest 30%; kept = not thin, arm != NO_BET, >=10 held-out games, held-out mean net > 0; earned = also BH q=0.10",
           "n_leaves": len(leaves), "n_splits": len(splits), "n_kept": sum(s["kept"] for s in splits),
           "n_earned": sum(s["earned"] for s in splits), "leaves": leaves, "splits": splits}
    safe_out(OUT).write_text(json.dumps(doc, indent=1, sort_keys=True))
    print(f"wrote {OUT}: {doc['n_leaves']} leaves, {doc['n_splits']} splits, {doc['n_kept']} kept, {doc['n_earned']} earned")


if __name__ == "__main__":
    main()
