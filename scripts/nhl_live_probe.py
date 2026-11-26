#!/usr/bin/env python3
"""W129.7 -- READ-ONLY probe of the NHL live feed (box task `nhl_live_probe`). Writes nothing under data/ or exp_output/.

  default        list live games, sample the play-by-play of up to --games of them --samples times, report
                 HTTP latency percentiles, whether the clock advances between samples, and staleness verdicts.
  --market-move  also poll the Kalshi game-winner market of each sampled game and time every GOAL seen in the feed
                 against the first Kalshi mid move of >= --jump cents (feed lead/lag, resolution = poll interval).

DATA RULE: NHL data is fetched and measured, never used to train anything (Content-Signal ai-train=no).
Imports no order code.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.c1_signal_ingestion import nhl_ingest as ni  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nhl_live as nl  # noqa: E402

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"


def pct(xs: list[float], q: float) -> float:
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


def game_market(th: ni.Throttle, st: dict) -> str | None:
    """Home-team game-winner ticker for the game (open market whose event matches the teams)."""
    d = ni.http_get_json(f"{KALSHI}/markets?series_ticker=KXNHLGAME&status=open&limit=200", th)
    for m in d.get("markets", []):
        t = m["ticker"]
        if st["home"] in t.split("-")[1] and st["away"] in t.split("-")[1] and t.endswith("-" + st["home"]):
            return t
    return None


def mid(th: ni.Throttle, ticker: str) -> float | None:
    m = ni.http_get_json(f"{KALSHI}/markets/{ticker}", th).get("market", {})
    try:
        b, a = float(m["yes_bid_dollars"]), float(m["yes_ask_dollars"])
    except (KeyError, TypeError, ValueError):
        return None
    return (b + a) / 2 if 0 < b < a < 1 else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=4)
    ap.add_argument("--samples", type=int, default=6)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--market-move", action="store_true")
    ap.add_argument("--jump", type=float, default=3.0, help="cents")
    a = ap.parse_args(argv)
    th, thk = ni.Throttle(1.0), ni.Throttle(0.25)
    sc = ni.http_get_json(f"{ni.BASE}/score/now", th)
    games = sc.get("games", [])
    live = [g for g in games if g.get("gameState") in nl.LIVE_STATES]
    print(f"feed: /score/now HTTP ok; {len(games)} games listed, {len(live)} live "
          f"(states: {sorted({g.get('gameState') for g in games})})")
    if not live:
        print("IDLE: no live game to sample (the parser and the saved-game test still stand)")
        return 0
    pick = [int(g["id"]) for g in live[:a.games]]
    tick = {}
    if a.market_move:
        for gid in pick:
            st = nl.fetch_state(gid, th)
            tick[gid] = game_market(thk, st)
            print(f"  market for game {gid} {st['away']}@{st['home']}: {tick[gid]}", flush=True)
    hist: dict[int, list[dict]] = {g: [] for g in pick}
    mids: dict[int, list[tuple[float, float]]] = {g: [] for g in pick}
    lat, verdicts = [], {}
    for i in range(a.samples):
        t_round = time.monotonic()
        for gid in pick:
            st = nl.fetch_state(gid, th)
            lat.append(st["latency_ms"])
            prev = hist[gid][-1] if hist[gid] else None
            why = nl.staleness(st, prev, nl.utcnow())
            verdicts[why or "ok"] = verdicts.get(why or "ok", 0) + 1
            st["_t"] = time.monotonic()
            hist[gid].append(st)
            if a.market_move and tick.get(gid):
                m = mid(thk, tick[gid])
                if m is not None:
                    mids[gid].append((time.monotonic(), m))
        time.sleep(max(0.0, a.interval - (time.monotonic() - t_round)))
    print(f"latency ms over {len(lat)} fetches: p50 {pct(lat, .5):.0f}  p90 {pct(lat, .9):.0f}  max {max(lat):.0f}  mean {statistics.mean(lat):.0f}")
    print("staleness verdicts:", json.dumps(verdicts, sort_keys=True))
    adv = sum(1 for g in pick for x, y in zip(hist[g], hist[g][1:])
              if x["clock_running"] and (y["period"], y["clock_s"]) != (x["period"], x["clock_s"]))
    run = sum(1 for g in pick for x in hist[g][:-1] if x["clock_running"])
    print(f"clock advanced between consecutive samples while running: {adv}/{run}")
    for gid in pick:
        h = hist[gid]
        goals = [(h[k]["_t"], h[k]) for k in range(1, len(h))
                 if (h[k]["score_h"], h[k]["score_a"]) != (h[k - 1]["score_h"], h[k - 1]["score_a"])]
        line = f"  game {gid} {h[0]['away']}@{h[0]['home']} period {h[-1]['period']} clock_s {h[-1]['clock_s']} score {h[-1]['score_a']}-{h[-1]['score_h']}"
        print(line + f" goals seen in window: {len(goals)}")
        if a.market_move:
            for t_goal, _s in goals:
                m = mids[gid]
                base = next((v for t, v in reversed(m) if t < t_goal - a.interval), None)
                jump = next((t for t, v in m if base is not None and t >= t_goal - a.interval and abs(v - base) * 100 >= a.jump), None)
                print(f"    goal detected by feed at t+{t_goal - hist[gid][0]['_t']:.0f}s; kalshi mid move >= {a.jump:g}c: " +
                      ("not within window" if jump is None else f"{jump - t_goal:+.1f}s vs feed (resolution ~{a.interval:g}s)"))
    print("DONE: read-only; nothing written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
