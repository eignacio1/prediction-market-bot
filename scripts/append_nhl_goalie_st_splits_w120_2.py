"""W120.2 Part B -- log the W119.1 NHL goalie and special-teams split verdicts in decision_trees/filter_splits.json.

Why append and not rebuild: leaf_scores.json was re-scored on more games in W119.1, so a full rebuild would also flip 20 kept flags
on the older NHL splits, which changes v1's logged NHL arms (and the demo orders that follow them). This adds ONLY the goalie /
special_teams entries, every existing entry byte-identical. Each new entry keeps its real verdict in ``verdict`` and is written
``kept: false, why: "<verdict>|logged_not_applied_to_v1"``: the router logs it as a tested split (D6 layer 3 stump rule, W117.3)
and never splits on it. Idempotent. Run: python3 scripts/append_nhl_goalie_st_splits_w120_2.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "src" / "prediction_market_bot" / "decision_trees" / "filter_splits.json"
NEW_FILTERS = ("goalie@", "special_teams@")


def _builder():
    spec = importlib.util.spec_from_file_location("build_filter_splits_w112", ROOT / "scripts" / "build_filter_splits_w112.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def new_entries() -> list:
    out = []
    for s in _builder().nhl_splits():
        if not s["filter"].startswith(NEW_FILTERS):
            continue
        s = dict(s)
        s["verdict"] = "kept" if s["kept"] else s["why"]
        s["kept"], s["why"] = False, s["verdict"] + "|logged_not_applied_to_v1"
        s["source"] = "W119.1 goalie + special teams (nhl_factors_w112/leaf_scores.json); logged by W120.2"
        out.append(s)
    return out


def main() -> int:
    doc = json.loads(PATH.read_text())
    key = lambda s: (s["sport"], s["series"], s["filter"], s["leaf"])  # noqa: E731
    have = {key(s) for s in doc["splits"]}
    add = [s for s in new_entries() if key(s) not in have]
    doc["splits"] += add
    doc["n"] = len(doc["splits"])
    doc["n_kept"] = sum(s["kept"] for s in doc["splits"])
    PATH.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"added={len(add)} n={doc['n']} n_kept={doc['n_kept']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
