"""W91.2 Part A check: router traffic on the frozen local price archive, before the swap (the 11 W89.2 cells treated as
rideable, as W90.2 did) and after (ride.py reading ride_cells.toml, all IN_SAMPLE). Traffic only; no settlement.

  python 12_EXPLORATORY/ride_ladder/replay_swap.py <PRICE_ARCHIVE> out/swap_traffic.json
"""
import dataclasses, glob, json, os, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "longshot_bias")); sys.path.insert(0, os.path.dirname(HERE))
import calib as C  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.decision_trees import ride  # noqa: E402
from prediction_market_bot.decision_trees.router import Evidence, Situation, route  # noqa: E402


def sits(archive):
    seen, out = set(), []
    for f in sorted(glob.glob(os.path.join(archive, "prices_*.jsonl"))):
        for line in open(f):
            try:
                r = json.loads(line)
                bid, ask = float(r["yes_bid"]), float(r["yes_ask"])
            except (ValueError, KeyError, TypeError):
                continue
            if not bid or not ask or ask < bid:
                continue
            t = C.tier(r["event_ticker"], C.parse_ts(r["run_ts"]))
            if t is None or (r["ticker"], t) in seen:
                continue
            seen.add((r["ticker"], t))
            fam = r.get("series_ticker", "")
            out.append(Situation("nfl" if fam.startswith("KXNFL") else "mlb", fam, r["ticker"], r["event_ticker"], t, bid, ask, (ask - bid) / 2))
    return out


def main(archive, out):
    shipped = ride.load()
    old = ride.Table(ride.RideCell(**{**dataclasses.asdict(c), "status": ride.HELD_OUT}) for c in shipped.c.values())
    res = {}
    S = sits(archive)
    for name, tab in (("before_swap_all_cells_rideable", old), ("after_swap_toml_in_sample", shipped)):
        cnt = Counter(route(s, Evidence(ride=tab)).tree for s in S)
        res[name] = dict(cnt)
    res["situations"] = len(S)
    json.dump(res, open(safe_out(out), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
