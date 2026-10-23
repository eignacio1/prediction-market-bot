"""W86.3 Part B: order-life chain and the E3 accounting identity, from the demo-fill-policy logs.

Inputs (copies of box logs): demo_fill_policy.jsonl, demo_fill_forward_cache.json, markouts.jsonl.
Timed chain: orders submitted on/after the markout epoch (fill_ts exists only then). States are elapsed-time bins; the
logs carry no queue position or book path, so "behind others" / "book moved away" are NOT observable (registered gap).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402

for _n in ("dtmc", "part_a_size"):
    _s = importlib.util.spec_from_file_location("w86_" + _n, HERE / (_n + ".py"))
    globals()[_n] = importlib.util.module_from_spec(_s)
    _s.loader.exec_module(globals()[_n])

EPOCH = "2026-10-21T04:30"
EDGES = [2.0, 5.5, 10.0, 60.0, 300.0, 1800.0, 7200.0]
ASSUMED_LATE_CANCEL_S = 7201.0  # cancelled orders with no logged cancel time: assume exit after the last edge


def ts(s: str) -> float:
    return part_a_size.parse_ts(s).timestamp()


def sport_of(ticker: str) -> str:
    for k in ("NFL", "NHL", "NBA", "MLB"):
        if k in ticker.split("-")[0]:
            return k
    return "OTHER"


def wilson_game_boot(items, reps=300, seed=86):
    """items: list of (game, x) with x numeric; clustered-by-game bootstrap of the mean."""
    import random
    g = defaultdict(list)
    for k, x in items:
        g[k].append(x)
    keys = list(g)
    if len(keys) < 5:
        return None
    rng = random.Random(seed)
    ms = []
    for _ in range(reps):
        pool = []
        for _k in keys:
            pool.extend(g[keys[rng.randrange(len(keys))]])
        ms.append(sum(pool) / len(pool))
    ms.sort()
    allv = [x for v in g.values() for x in v]
    return [sum(allv) / len(allv), ms[int(.025 * reps)], ms[int(.975 * reps)], len(allv), len(keys)]


def main(data: str, out_json: str) -> None:
    D = Path(data)
    cache = json.load(open(D / "demo_fill_forward_cache.json"))
    so, cancel_ts, last_ts = {}, {}, ""
    for line in open(D / "demo_fill_policy.jsonl"):
        r = json.loads(line)
        last_ts = max(last_ts, r["ts"])
        if r["event"] == "shadow_order" and r.get("ok"):
            r.setdefault("ticker", r.get("row_id", "|").split("|", 1)[-1])  # older rows carry only row_id
            so[r["order_id"]] = r
        elif r["event"] == "cancel_ok":
            cancel_ts[r["order_id"]] = r["ts"]
    mk = {}
    for line in open(D / "markouts.jsonl"):
        r = json.loads(line)
        mk[r["order_id"]] = r

    # ---- E3 identity over every cached, settled order, by arm x sport -------------------------------------------
    ident: Dict[str, dict] = {}
    cell_items = defaultdict(lambda: {"f": [], "n": []})
    for oid, c in cache.items():
        o = so.get(oid)
        if not o or not c.get("settled"):
            continue
        arm = o.get("arm") or "pre-arm"
        sp = sport_of(o["ticker"])
        paid = c["price"] if c["side"] == "yes" else 1 - c["price"]
        gk = part_a_size.game_key(o["ticker"])
        if c["status"] == "executed" and "won" in c:
            cell_items[(arm, sp)]["f"].append((gk, float(c["won"]), paid))
        elif c["status"] == "canceled" and "nf_won" in c:
            cell_items[(arm, sp)]["n"].append((gk, float(c["nf_won"]), paid))
    for (arm, sp), d in sorted(cell_items.items()):
        if len(d["f"]) < 20 or len(d["n"]) < 20:
            continue
        wf = sum(x[1] for x in d["f"]) / len(d["f"])
        wn = sum(x[1] for x in d["n"]) / len(d["n"])
        pf = sum(x[2] for x in d["f"]) / len(d["f"])
        pn = sum(x[2] for x in d["n"]) / len(d["n"])
        ident["%s|%s" % (arm, sp)] = {
            "n_fills": len(d["f"]), "n_nonfills": len(d["n"]),
            "win_fill": wf, "win_nonfill": wn, "gap": wf - wn,
            "price_paid_fill": pf, "price_paid_nonfill": pn,
            "adverse_selection_fill (win_fill - price_fill)": wf - pf,
            "price_chosen (price_fill - price_nonfill)": pf - pn,
            "nonfill_edge (price_nonfill - win_nonfill)": pn - wn,
            "gap_check (sum of three)": (wf - pf) + (pf - pn) + (pn - wn),
            "win_fill_ci95_game_clustered": wilson_game_boot([(g, w) for g, w, _ in d["f"]]),
            "win_nonfill_ci95_game_clustered": wilson_game_boot([(g, w) for g, w, _ in d["n"]]),
        }

    # ---- timed chain for post-epoch orders ------------------------------------------------------------------------
    lives = defaultdict(lambda: defaultdict(list))   # (arm, sport) -> game -> lives
    dropped = defaultdict(int)
    fills_by_bin = defaultdict(list)                 # (arm, sport, bin) -> [(game, won)]
    for oid, o in so.items():
        if o["ts"] < EPOCH or oid not in cache:
            continue
        c = cache[oid]
        arm, sp, gk = o.get("arm") or "pre-arm", sport_of(o["ticker"]), part_a_size.game_key(o["ticker"])
        t0 = ts(o["ts"])
        if c["status"] == "executed" and oid in mk:
            t = max(0.0, ts(mk[oid]["fill_ts"]) - t0)
            lives[(arm, sp)][gk].append((t, "F"))
            if c.get("settled") and "won" in c:
                fills_by_bin[(arm, sp, dtmc.bin_of(t, EDGES))].append((gk, float(c["won"])))
        elif c["status"] == "canceled" and oid in cancel_ts:
            lives[(arm, sp)][gk].append((max(0.0, ts(cancel_ts[oid]) - t0), "C"))
        elif c["status"] == "resting":
            lives[(arm, sp)][gk].append((max(0.0, ts(last_ts) - t0), "O"))
        elif c["status"] == "canceled":
            lives[(arm, sp)][gk].append((ASSUMED_LATE_CANCEL_S, "C"))   # sensitivity: see 'assumed_late_cancel'
            dropped[(arm, sp, "assumed_late_cancel")] += 1
        else:
            dropped[(arm, sp, c["status"])] += 1
    chain = {}
    for (arm, sp), g in sorted(lives.items()):
        allv = [l for v in g.values() for l in v]
        if len(allv) < 50:
            continue
        s = dtmc.summarise(dtmc.estimate(allv, EDGES), EDGES)
        ci = dtmc.cluster_bootstrap(g, EDGES, lambda z: z["p_fill"])
        ft = sorted(t for t, e in allv if e == "F")
        chain["%s|%s" % (arm, sp)] = {
            "fill_time_s_p10_p50_p90": [ft[int(x * len(ft))] for x in (.1, .5, .9)] if ft else None,
            "n_orders": len(allv), "n_games": len(g), "n_fill": sum(1 for _, e in allv if e == "F"),
            "n_cancel": sum(1 for _, e in allv if e == "C"), "n_censored": sum(1 for _, e in allv if e == "O"),
            "p_fill": s["p_fill"], "p_fill_ci95_game_clustered": ci[1:] if ci else None,
            "expected_time_to_fill_given_fill_s": s["expected_time_to_fill_given_fill_s"],
            "fill_cdf_by_bin_edge_s": s["fill_cdf_by_bin_edge"],
        }
    by_bin = {}
    for (arm, sp, b), v in sorted(fills_by_bin.items()):
        if len(v) >= 30:
            by_bin["%s|%s|bin%d(<%ss)" % (arm, sp, b, EDGES[b] if b < len(EDGES) else "inf")] = wilson_game_boot(v)
    out = {"epoch": EPOCH, "edges_s": EDGES, "e3_identity": ident, "chain": chain,
           "win_rate_of_fills_by_time_to_fill_bin [mean, lo, hi, n, games]": by_bin,
           "dropped_orders_no_exit_time": {"|".join(k): v for k, v in dropped.items()},
           "limits": "queue position and book path not logged; timed bins stand in for the path"}
    p = safe_out(out_json)
    p.write_text(json.dumps(out, indent=1))
    print("wrote", p)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
