"""W105.2 Part B runner: counterfactual placement rules on recorded demo shadow orders. READ-ONLY on inputs; writes result.json.

Usage: python3 run_w105_orders.py <FT dir> quant_w105_orders/result.json   (out path is relative to 12_EXPLORATORY via safe_out)
  FT dir holds demo_fill_forward_cache_rescored.json (GG-1810 derived file), markouts/markouts.jsonl,
  orders_ok.jsonl ([order_id, ts, row_id, price_yes, stake]) and shadow_orders.jsonl (policy-log shadow_order rows).
Population: demo shadow orders (NFL/NBA/NHL), intended side YES, ordered before the GG-1771 epoch 2026-11-06T01:03:42Z.
Intended side comes from the shadow_order row (GG-1793), so NON-FILLS are now side-correct too.
Post-epoch n is stated and reported separately (it is 0 in the pulled data).
"""
import json
import sys
from collections import Counter

sys.path.insert(0, "src")
sys.path.insert(0, "12_EXPLORATORY")
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant import placement as pl  # noqa: E402

EPOCH = "2026-11-06T01:03:42"


def load(ft):
    cache = json.load(open(f"{ft}/demo_fill_forward_cache_rescored.json"))
    mk = {}
    for l in open(f"{ft}/markouts/markouts.jsonl"):
        r = json.loads(l)
        mk[r["order_id"]] = r
    sh = {}
    for l in open(f"{ft}/shadow_orders.jsonl"):
        e = json.loads(l)
        if e.get("ok"):
            sh[e["order_id"]] = e
    start = json.load(open(f"{ft}/markouts/EPOCH.json"))["collection_start"][:19]
    pre, post, dropped = [], [], Counter()
    for l in open(f"{ft}/orders_ok.jsonl"):
        oid, ts, rid, p, _ = json.loads(l)
        c, s = cache.get(oid), sh.get(oid)
        if ts[:19] < start:
            dropped["before_collection_start"] += 1
            continue
        if not c or not c.get("settled") or not s:
            dropped["unsettled_or_unmatched"] += 1
            continue
        side = (s.get("intended_side") or s.get("side") or "").lower()
        filled = c.get("fills", 0) > 0
        won = c.get("won") if filled else c.get("nf_won")
        if won is None:
            dropped["no_outcome"] += 1
            continue
        m = mk.get(oid)
        mk1 = None if (m is None or m.get("h1") is None) else m["h1"]
        ticker = rid.split("|", 1)[1]
        row = dict(oid=oid, ts=ts, game=ticker.rsplit("-", 1)[0], sport=ticker.split("-")[0][2:5], side=side, price=p,
                   filled=filled, mk=mk1, arm=s.get("arm"), won=bool(won),
                   pnl=(float(won) - p) if filled else None)
        if ts[:19] >= EPOCH:
            post.append(row)
        else:
            pre.append(row)
    return pre, post, dropped


def main(ft, out):
    pre, post, dropped = load(ft)
    yes = [r for r in pre if r["side"] == "yes"]
    res = {"population": "demo shadow orders NFL/NBA/NHL; intended side YES; pre-epoch",
           "n_pre_all_sides": len(pre), "n_pre_yes": len(yes), "n_pre_no_excluded_mirror_priced": sum(r["side"] == "no" for r in pre),
           "n_post_epoch_all_sides": len(post), "dropped": dict(dropped),
           "yes_fills": sum(r["filled"] for r in yes),
           "yes_fills_with_h1": sum(1 for r in yes if r["filled"] and r["mk"] is not None),
           "games": len({r["game"] for r in yes}), "arms": dict(Counter(r["arm"] for r in yes))}
    # analysis set: non-fills + fills with a known 1-minute markout (a fill with unknown markout would count as 0)
    A = [r for r in yes if (not r["filled"]) or r["mk"] is not None]
    res["n_analysis"] = len(A)
    edges = [0.0, 0.2, 0.35, 0.5, 0.65, 0.8, 1.01]
    res["markout_h1_by_price"] = pl.bucket_markout(A, edges)
    fl = [r for r in A if r["filled"]]
    res["threshold_fit_h1"] = pl.fit_price_threshold([r["price"] for r in fl], [r["mk"] for r in fl], [r["game"] for r in fl])
    res["fill_rate_by_price"] = [{"lo": lo, "hi": hi, "n": len(s), "fill_rate": (sum(r["filled"] for r in s) / len(s) if s else None)}
                                 for lo, hi in zip(edges[:-1], edges[1:]) for s in [[r for r in A if lo <= r["price"] < hi]]]
    rules = {"no_rule (baseline)": lambda r: True,
             "dont_rest_ge_0.80": lambda r: r["price"] < 0.80,
             "dont_rest_ge_0.65": lambda r: r["price"] < 0.65,
             "dont_rest_ge_0.50": lambda r: r["price"] < 0.50}
    th = res["threshold_fit_h1"].get("threshold")
    if th is not None:
        rules[f"dont_rest_ge_fitted_{th:.2f}"] = lambda r, t=th: r["price"] < t
    res["rules_markout_h1"] = {k: pl.evaluate_rule(A, f, "mk") for k, f in rules.items()}
    sett = [r for r in yes]          # settle P&L: every settled YES order, fills carry pnl, non-fills 0
    res["rules_settle_pnl"] = {k: pl.evaluate_rule(sett, f, "pnl") for k, f in rules.items()}
    res["arm_contrast_markout_h1"] = {f"{a}->{b}": pl.arm_contrast(A, a, b, "mk")
                                      for a, b in (("control", "treatment"), ("control", "adopt")) if a in res["arms"] and b in res["arms"]}
    res["not_testable"] = ["cancel_after_t: fill/cancel times in the pulled cache are collector-observed (hours late), not exchange times",
                           "post_at_mid_minus_k_ticks: a recorded order has no outcome at a price it did not rest at; read via arm_contrast",
                           "distance_from_mid / book depth: first logged by PR #440 (W105.2); n(orders with the fields) = 0 until they accrue"]
    json.dump(res, open(safe_out(out), "w"), indent=1, default=float)
    print(json.dumps({k: res[k] for k in ("n_pre_yes", "n_pre_no_excluded_mirror_priced", "n_post_epoch_all_sides", "yes_fills", "yes_fills_with_h1", "games", "arms", "n_analysis", "dropped")}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
