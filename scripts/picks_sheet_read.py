#!/usr/bin/env python3
"""Read-only summary of exp_output/PICKS_SHEET/picks_latest.json (W100.3, B-026): picks per game, reasons coverage,
result fill, arms that disagree, and builder notes. Changes nothing."""
from __future__ import annotations

import argparse
import collections
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def summarize(sheet: dict) -> list:
    games = sheet.get("games", [])
    picks = [p for g in games for p in g.get("picks", [])]
    per_game = [len(g.get("picks", [])) for g in games]
    out = [f"sheet {sheet.get('date')} built {sheet.get('built_utc')} n_picks={sheet.get('n_picks')} games={len(games)}"]
    if per_game:
        out.append(f"picks/game: median {statistics.median(per_game)} max {max(per_game)} min {min(per_game)}")
    arms = collections.Counter(p["arm"] for p in picks)
    out.append("by arm: " + ", ".join(f"{a}={n}" for a, n in sorted(arms.items())))
    no_reason = sum(1 for p in picks if any(r.startswith("no reasons available") for r in p.get("reasons", [])))
    out.append(f"picks with stored reasons: {len(picks) - no_reason}/{len(picks)}")
    notes = collections.Counter(r for p in picks for r in p.get("reasons", []) if r.startswith("no reasons available"))
    for r, n in notes.most_common(5):
        out.append(f"  no-reason cause: {n} x {r}")
    res = collections.Counter((p.get("result") or {}).get("outcome", "open") for p in picks)
    out.append("results: " + ", ".join(f"{k}={v}" for k, v in sorted(res.items())))
    orders = collections.Counter("placed" if (p.get("demo_order") or {}).get("placed") else
                                 ("skip: " + str((p.get("demo_order") or {}).get("reason")) if p.get("demo_order") else "no order row") for p in picks)
    out.append("demo orders: " + "; ".join(f"{k}={v}" for k, v in orders.most_common(6)))
    out.append(f"games where arms disagree: {sum(1 for g in games if g.get('arms_disagree'))}")
    big = sorted(games, key=lambda g: -len(g.get("picks", [])))[:3]
    for g in big:
        out.append(f"  biggest: {g['game']} {len(g['picks'])} picks over {len({p['ticker'] for p in g['picks']})} tickers")
    for n in sheet.get("notes", []):
        out.append(f"note: {n}")
    for p in picks[:3]:
        out.append(f"sample: {p['arm']} | {p['pick']} | bot {p['bot_prob_for_pick']} vs {p['kalshi_price_yes']} | edge {p['edge_after_fee']} | {p['reasons']}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(ROOT, "exp_output/PICKS_SHEET/picks_latest.json"))
    a = ap.parse_args(argv)
    try:
        with open(a.path) as fh:
            sheet = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"cannot read {a.path}: {e}")
        return 1
    print("\n".join(summarize(sheet)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
