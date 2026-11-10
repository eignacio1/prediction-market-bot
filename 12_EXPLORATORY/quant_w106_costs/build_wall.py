"""W106.2 cost-wall tables. Reads spread.json (box aggregate) + constants quoted from 105.2 / 89.2(W92.2). Prints JSON."""
import json, os, collections, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from prediction_market_bot.quant import costs as C
H = os.path.dirname(__file__)
d = json.load(open(os.path.join(H, "spread.json")))
bands = d["bands"]; mid = [(a + b) / 2 for a, b in bands]
# A2: n-weighted mean half-spread per series x tts
agg = collections.defaultdict(lambda: [0, 0.0])
for s, b, t, n, m, md in d["rows"]:
    agg[(s, t)][0] += n; agg[(s, t)][1] += n * m
a2 = {f"{s}|{t}": {"n": n, "half_spread": round(w / n, 4)} for (s, t), (n, w) in agg.items()}
# A1: fee per contract by price, taker vs maker (multiplier-1 series), schedule coef 0.07 / 0.0175
fees = {str(p): {"taker": round(C.fee_per_contract("KXNFLGAME", p, "taker"), 4),
                 "maker_upper": round(0.0175 * p * (1 - p), 4)} for p in (.05, .10, .20, .35, .50, .65, .80, .90)}
# B2: maker economics by price bucket, 105.2 1-min markout (pre-epoch YES only), fee at bucket mid (upper bound coef)
mk = {"<0.20": (0.10, 0.0047), "0.20-0.35": (0.275, 0.0065), "0.35-0.50": (0.425, 0.0119),
      "0.50-0.65": (0.575, 0.0196), "0.65-0.80": (0.725, 0.0227), ">=0.80": (0.88, 0.0411)}
b2 = {}
for k, (p, mo) in mk.items():
    f = 0.0175 * p * (1 - p)
    b2[k] = {"markout": -mo, "maker_fee_upper": round(f, 4), "net_per_fill": round(-mo - f, 4)}
print(json.dumps({"A1_fees": fees, "A2": a2, "B2": b2}, indent=1))
