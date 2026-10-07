"""W58.2 Part A (T-710): read-only Kalshi discovery of the NBA game-market series.

Public GET only (/series, /markets, /events). Prints series metadata, ticker grammar samples,
the set of team codes as Kalshi spells them, strike patterns and the earliest/latest listed game
date per series. Opens no order path.

  python3 scripts/nba_kalshi_discovery.py [--out exp_output/NBA/discovery.json]
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

BASE = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = ["KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL", "KXNBATEAMTOTAL", "KXNBAGAMES", "KXNBASUMMERGAME"]
EVENT = re.compile(r"^(KXNBA[A-Z]+)-(\d{2})([A-Z]{3})(\d{2})([A-Z]+)$")


def get(path: str, **q) -> dict:
    qs = "&".join(f"{k}={v}" for k, v in q.items() if v is not None)
    req = urllib.request.Request(f"{BASE}{path}?{qs}", headers={"User-Agent": "pmbot-readonly-discovery"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return {}


def markets_for(series: str, status: str) -> list[dict]:
    out, cursor = [], None
    while True:
        d = get("/markets", series_ticker=series, status=status, limit=1000, cursor=cursor)
        out += d.get("markets", [])
        cursor = d.get("cursor")
        time.sleep(1.0)
        if not cursor:
            return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="exp_output/NBA/discovery.json")
    a = ap.parse_args()
    report: dict = {}
    for s in SERIES:
        meta = get("/series/" + s).get("series", {})
        info = {"title": meta.get("title"), "fee_type": meta.get("fee_type"),
                "fee_multiplier": meta.get("fee_multiplier"), "frequency": meta.get("frequency")}
        for status in ("open", "unopened"):
            ms = markets_for(s, status)
            dates, suffixes, teams, samples = [], Counter(), Counter(), []
            for m in ms:
                ev = EVENT.match(m.get("event_ticker", ""))
                if ev:
                    dates.append(f"20{ev.group(2)}-{ev.group(3)}-{ev.group(4)}")
                    teams[ev.group(5)] += 1
                suf = m["ticker"].rsplit("-", 1)[-1]
                suffixes[re.sub(r"\d+", "N", suf) if len(suf) > 3 else suf] += 1
                if len(samples) < 6:
                    samples.append({k: m.get(k) for k in ("ticker", "event_ticker", "floor_strike",
                                    "yes_sub_title", "yes_bid_dollars", "yes_ask_dollars", "close_time",
                                    "expected_expiration_time")})
            info[status] = {"n_markets": len(ms), "n_events": len({m["event_ticker"] for m in ms}),
                            "date_min": min(dates) if dates else None, "date_max": max(dates) if dates else None,
                            "event_team_blobs": sorted(teams)[:80], "suffix_shapes": suffixes.most_common(12),
                            "samples": samples}
        report[s] = info
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, indent=1))
    for s, i in report.items():
        print(s, i["title"], i["fee_type"], i["fee_multiplier"],
              {st: (i[st]["n_markets"], i[st]["n_events"], i[st]["date_min"], i[st]["date_max"]) for st in ("open", "unopened")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
