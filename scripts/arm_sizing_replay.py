#!/usr/bin/env python3
"""W112.2 Part C: replay routed shadow rows through arm_sizing.size_for (read-only; writes only the report you name).

Reads <dir>/*.jsonl (default exp_output/PREGAME_SHADOW, the ledger the routed shadow rows are appended to), keeps rows
from the last --days days that carry a router arm, and sizes each at the flat demo stake with the caps in order of the
ledger (per event, per day, per arm budget; the same-game cluster cap needs shared draws, which a shadow row does not
carry, so it is reported as 'not exercised' here and is covered by the known-answer tests).

Output: stake per arm, caps that bound, the share of rows with a size_for decision, and the Kelly-shaped stake logged
beside the flat one (never placed). Pre-epoch (before 2026-11-06T01:03:42Z) rows are YES-only mirror-priced and are
reported separately from post-epoch all-side rows, never mixed.
Usage: python3 scripts/arm_sizing_replay.py [--dir D] [--days 14] [--now ISO] [--out FILE.md] [--json FILE.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot.c4_risk_engine import arm_sizing as az  # noqa: E402

EPOCH = datetime(2026, 11, 6, 1, 3, 42, tzinfo=timezone.utc)


class _Cell:  # the replay sizes by (market_type, band) text; no registry import needed for a report
    def __init__(self, market_type, band):
        self.market_type, self.band = market_type, band


def _ts(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def load(dirpath: Path, now: datetime, days: int):
    lo = now - timedelta(days=days)
    for f in sorted(dirpath.glob("*.jsonl")):
        with f.open() as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                t = _ts(r.get("ts_utc"))
                arm = (r.get("router") or {}).get("arm")
                if t and lo <= t <= now and arm:
                    yield t, r, arm


def replay(rows):
    """rows: iterable of (ts, row, arm). Ledger-ordered: event/day/arm open stakes accumulate as the replay walks."""
    ev, day, armd = defaultdict(float), defaultdict(float), defaultdict(float)
    out = {"pre": defaultdict(lambda: defaultdict(float)), "post": defaultdict(lambda: defaultdict(float))}
    caps = {"pre": Counter(), "post": Counter()}
    n = {"pre": Counter(), "post": Counter()}
    for t, r, arm in sorted(rows, key=lambda x: x[0]):
        ep = "post" if t >= EPOCH else "pre"
        d0 = t.date().isoformat()
        bid, ask = r.get("yes_bid"), r.get("yes_ask")
        side = (r.get("router") or {}).get("side")
        price = None
        if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
            price = ask if side != "no" else 1.0 - bid
        p_yes = r.get("p_yes")
        p_win = p_yes if side != "no" else (None if p_yes is None else 1.0 - p_yes)
        ctx = az.SizingContext(price=price, p_win=p_win, open_event_usd=ev[(r.get("event_ticker"), d0)],
                               open_day_usd=day[d0], open_arm_usd=armd[(arm, d0)])
        dec = az.size_for(arm, _Cell(r.get("market_type"), r.get("band")), ctx)
        ev[(r.get("event_ticker"), d0)] += dec.stake_usd
        day[d0] += dec.stake_usd
        armd[(arm, d0)] += dec.stake_usd
        n[ep][arm] += 1
        out[ep][arm]["stake"] += dec.stake_usd
        out[ep][arm]["kelly_shaped"] += dec.kelly_shaped_usd or 0.0
        for c in dec.binding_caps:
            caps[ep][(arm, c)] += 1
    return out, caps, n


def report(out, caps, n, days, now):
    L = [f"# W112.2 Part C - shadow rows replayed through size_for (last {days} days to {now.isoformat()})", "",
         "Flat demo stake, Kelly 0, nothing placed. Same-game cluster cap: not exercised (shadow rows carry no shared draws); "
         "covered by tests/test_arm_sizing.py. Pre-epoch (YES-only, mirror-priced) and post-epoch (all sides) are never mixed.", ""]
    for ep, title in (("pre", "Pre-epoch (before 2026-11-06T01:03:42Z), YES-only"), ("post", "Post-epoch, all sides")):
        L += [f"## {title}", "", "| Arm | Rows | Flat stake (USD) | Kelly-shaped, logged (USD) | Caps that bound |", "|---|---|---|---|---|"]
        if not n[ep]:
            L += ["| (no routed rows in window) | 0 | 0 | 0 | - |", ""]
            continue
        for arm in sorted(n[ep]):
            b = ", ".join(f"{c} x{k}" for (a2, c), k in sorted(caps[ep].items()) if a2 == arm) or "none"
            L.append(f"| {arm} | {n[ep][arm]} | {out[ep][arm]['stake']:.2f} | {out[ep][arm]['kelly_shaped']:.2f} | {b} |")
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(REPO / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--now", default=None)
    ap.add_argument("--out")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    now = _ts(a.now) if a.now else datetime.now(timezone.utc)
    d = Path(a.dir)
    if not d.is_dir():
        print(f"no shadow directory at {d}: nothing to replay (rows live on the box)", file=sys.stderr)
        return 2
    out, caps, n = replay(load(d, now, a.days))
    text = report(out, caps, n, a.days, now)
    if a.out:
        Path(a.out).write_text(text + "\n")
    if a.json:
        Path(a.json).write_text(json.dumps({"days": a.days, "now": now.isoformat(),
                                            "rows": {e: dict(n[e]) for e in n},
                                            "stake_usd": {e: {k: dict(v) for k, v in out[e].items()} for e in out}}, indent=1))
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
