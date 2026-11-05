"""W102.3 Part B analysis (offline): sheet JSON + collect_night.py output -> numbers for last_settled_night.md."""
import json, sys, collections, statistics as st
sys.path[:0] = ["src"]
from prediction_market_bot.pregame_shadow import picks_sheet as ps
sheet, night, tag = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(sheet)); nt = json.load(open(night))
games = [g for g in d["games"] if tag in g["game"]]
raw = [p for g in games for p in g["picks"]]
for p in raw: p.pop("result", None)
dd = ps.dedupe([dict(p) for p in raw])
res = nt["markets"]
settled = [{"market_ticker": t, "y": 1.0 if v["result"] == "yes" else 0.0 if v["result"] == "no" else None} for t, v in res.items()]
ps.attach_results(dd, settled)
fills = collections.defaultdict(list)
for t, lst in nt["orders"].items():
    for o in lst:
        f = o.get("fill") or {}
        fills[(t, o.get("side"))].append(f)
def filled(p):
    fl = [f for f in fills.get((p["ticker"], p["side"]), []) if (f.get("fills") or 0) > 0]
    return fl
def ordered(p):
    return bool(fills.get((p["ticker"], p["side"])))
out = {"games": len(games), "picks_raw": len(raw), "picks_distinct": len(dd),
       "with_result": sum(1 for p in dd if p.get("result")),
       "ordered": sum(1 for p in dd if ordered(p)), "filled": sum(1 for p in dd if filled(p))}
print(json.dumps(out))
hits = [p for p in dd if p.get("result")]
print("distinct hit/miss/push", collections.Counter(p["result"]["outcome"] for p in hits))
print("mean pnl/contract at logged price, all distinct", round(st.mean(p["result"]["pnl_per_contract"] for p in hits), 4))
F = [p for p in dd if filled(p) and p.get("result")]
print("filled n", len(F), collections.Counter(p["result"]["outcome"] for p in F))
if F:
    print("filled: mean pnl/contract at pick-time Kalshi price", round(st.mean(p["result"]["pnl_per_contract"] for p in F), 4))
    # at actual fill price (side-frame dollars), fee ignored; weights = fills
    num = den = 0.0
    for p in F:
        fl = filled(p)
        y = 1.0 if res[p["ticker"]]["result"] == "yes" else 0.0
        win = y if p["side"] == "yes" else 1 - y
        for f in fl:
            if f.get("price") is not None:
                num += (win - f["price"]) * f["fills"]; den += f["fills"]
    print("filled: mean (settle - fill price) per contract, fee excluded, contract-weighted", round(num / den, 4) if den else None, "contracts", den)
    gaps = [(p["kalshi_price_yes"] if p["side"] == "yes" else 1 - p["kalshi_price_yes"]) for p in F]
    print("filled: mean pick-time kalshi price (side frame)", round(st.mean(gaps), 4), "mean bot prob", round(st.mean(p["bot_prob_for_pick"] for p in F), 4),
          "hit rate", round(sum(1 for p in F if p["result"]["outcome"] == "hit") / len(F), 4))
NF = [p for p in dd if p.get("result") and not filled(p)]
print("not filled n", len(NF), "mean pnl", round(st.mean(p["result"]["pnl_per_contract"] for p in NF), 4) if NF else None,
      "hit rate", round(sum(1 for p in NF if p["result"]["outcome"] == "hit") / len(NF), 4) if NF else None)
# disagreement: per game, picks on opposite sides of the same underlying bet
bg = collections.defaultdict(list)
for p in dd: bg[p["game"]].append(p)
rows = []
for g, ps_ in bg.items():
    sides = collections.defaultdict(set)
    for p in ps_:
        sides[p["ticker"]].add(p["side"])
    conflict = sum(1 for t, s in sides.items() if len(s) > 1)
    arms = {a for p in ps_ for a in p.get("arms", [p["arm"]])}
    rows.append((conflict, len(ps_), g, len(arms)))
for r in sorted(rows, reverse=True)[:6]: print("disagree", r)
json.dump({"dd": dd}, open(sys.argv[4], "w"), default=str)
