"""W109.4 Part A -- pull minute candles for sampled settled NBA / NFL / NHL prop events. Public GET only. Resumable.
usage: fetch_props.py CACHE_DIR EVENTS_PER_SERIES MARKETS_PER_EVENT [SERIES ...]"""
import json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))
from prediction_market_bot.quant import props_candles as P  # noqa: E402

SERIES = ("KXNBA3PT KXNBAAST KXNBABLK KXNBAPRA KXNBAPTS KXNBAREB KXNBASTL KXNFLANYTD KXNFLFG KXNFLFIRSTTD KXNFLPASSATT "
          "KXNFLPASSCOMP KXNFLPASSINT KXNFLPASSTDS KXNFLPASSYDS KXNFLREC KXNFLRECYDS KXNFLRSHATT KXNFLRSHYDS KXNFLTD "
          "KXNHLAST KXNHLFIRSTGOAL KXNHLGOAL KXNHLPTS KXNHLSAVE").split()

def main():
    root, ev_cap, mk_cap = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    series = sys.argv[4:] or SERIES
    fetch = P.make_fetch(sleep=0.3)
    for s in series:
        have = P.load_cache(root, s)
        ms = [m for m in P.list_settled(fetch, s) if float(m.get("volume_fp") or 0) > 0]
        pick = P.sample_events(ms, ev_cap)
        by = {}
        for m in pick:
            by.setdefault(m["event_ticker"], []).append(m)
        todo = []
        for ev, lst in by.items():
            todo += random.Random(ev).sample(lst, min(mk_cap, len(lst)))
        todo = [m for m in todo if m["ticker"] not in have]
        print(s, "settled", len(ms), "events", len(by), "todo", len(todo), flush=True)
        out = open(P.cache_path(root, s), "a")
        for m in todo:
            st, en = P.parse_ts(m["open_time"]), P.parse_ts(m["close_time"]) + 60
            cs = P.fetch_candles_one(fetch, m["ticker"], st, en, 1) or P.fetch_candles(fetch, [m["ticker"]], st, en, 1).get(m["ticker"]) or []
            out.write(json.dumps({"t": m["ticker"], "ev": m["event_ticker"], "res": m["result"], "open": m["open_time"],
                                  "close": m["close_time"], "occ": m.get("occurrence_datetime"),
                                  "exp": m.get("expected_expiration_time"), "vol": m.get("volume_fp"),
                                  "strike": m.get("floor_strike"), "c": cs}) + "\n")
            out.flush()
main()
