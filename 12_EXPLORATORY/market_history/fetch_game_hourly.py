"""W88.3: pre-game Kalshi prices for one game-market series, one market per event, hourly candles around game start.
Public unauthenticated GETs only, via scripts/board_survey_sports_store (verbatim raw rows kept under --out/raw).
Writes --out/<SERIES>_pregame.jsonl: one row per event with the first-listed team's market, its result, and the hourly
candles in [occurrence - LOOKBACK_H, occurrence]. Choosing one market per event is enough for a two-outcome game market:
the other side is 1 - p and the pre-game price used is the mid of this side (the same convention W84.3 used)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import board_survey_sports_store as bs  # noqa: E402

LOOKBACK_H = 6


def one_per_event(markets: list[dict]) -> list[dict]:
    """First-listed (sorted by ticker) market of each event."""
    by_event: dict[str, dict] = {}
    for m in sorted(markets, key=lambda x: x["ticker"]):
        by_event.setdefault(m.get("event_ticker") or m["ticker"].rsplit("-", 1)[0], m)
    return list(by_event.values())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--from-iso", required=True, help="keep events whose occurrence/close is >= this UTC instant")
    ap.add_argument("--to-iso", default="2100-01-01T00:00:00Z")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rate", type=float, default=1.5)
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    client = bs.Client(pause=1.0 / a.rate)
    store = bs.Store(out / "raw")
    cj, _ = client.get("/historical/cutoff")
    cutoff = bs.iso_ts(cj["market_settled_ts"])
    lo, hi = bs.iso_ts(a.from_iso), bs.iso_ts(a.to_iso)
    mk = [m for m in bs.list_markets(client, store, a.series, cj["market_settled_ts"]) if m.get("result") in ("yes", "no")]
    def when(m): return bs.iso_ts(m.get("occurrence_datetime") or m["close_time"])
    mk = [m for m in one_per_event(mk) if lo <= when(m) < hi]
    print(f"{a.series}: {len(mk)} events in window", flush=True)
    path = out / f"{a.series}_pregame.jsonl"
    done = set()
    if path.exists():
        done = {json.loads(l)["ticker"] for l in path.open()}
    with path.open("a") as fh:
        for i, m in enumerate(mk):
            if m["ticker"] in done:
                continue
            occ = when(m)
            try:
                cs = bs.candles(client, store, a.series, m, occ - LOOKBACK_H * 3600, occ + 60, 60, cutoff)
            except bs.FetchFailed as e:
                print("FAILED", m["ticker"], e, flush=True); continue
            fh.write(json.dumps({"ticker": m["ticker"], "event_ticker": m.get("event_ticker"), "occurrence_ts": occ,
                                 "result": m["result"], "candles": cs}, sort_keys=True) + "\n"); fh.flush()
            if i % 100 == 0:
                print(i, client.stats(), flush=True)
    print("done", client.stats(), flush=True)


if __name__ == "__main__":
    main()
