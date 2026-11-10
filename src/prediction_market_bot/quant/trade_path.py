"""Trade-print news-lag maths (W108.2 / B-063): the price path in the minutes around a news time, from Kalshi's public
trade prints (GET /markets/trades), plus the price a taker would actually have paid.

Pure functions plus one paginating fetcher whose HTTP call is injected.  Complements ``news_lag`` (20-minute snapshots,
which cannot see a lag shorter than one snapshot): prints carry their own timestamps, so a path by minute is possible
wherever the market traded.  A minute with no print has NO price -- paths forward-fill the last print but report how stale
it is, and entry/lag statistics only use real prints.

When it applies: a market that traded in the window; the reported time is the news time (a stamp later than the true
publication biases the lag short).  When it does not: markets that did not trade (no path), news that was public earlier
than its official stamp (lag then looks like zero or negative)."""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Sequence

from prediction_market_bot.quant import money, news_lag


@dataclass(frozen=True)
class Trade:
    ts: datetime
    yes: float          # YES price in dollars
    count: float
    taker: str          # "yes" | "no": the side the aggressor bought


def _ts(s: str) -> datetime:
    s = s.rstrip("Z")
    if "." in s:
        head, frac = s.split(".")
        s = head + "." + frac[:6].ljust(6, "0")
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def parse_trades(rows: Sequence[dict]) -> list[Trade]:
    out = [Trade(_ts(r["created_time"]), float(r["yes_price_dollars"]), float(r.get("count_fp", 1)),
                 r.get("taker_side", "yes")) for r in rows if not r.get("is_block_trade")]
    out.sort(key=lambda t: t.ts)
    return out


def fetch_trades(get_json: Callable[[str, dict], dict], ticker: str, t_lo: datetime, t_hi: datetime,
                 pause: float = 0.25, max_pages: int = 40) -> list[dict]:
    """All raw trade rows for ``ticker`` with t_lo <= created_time <= t_hi.  ``get_json(path, params)`` does the GET."""
    rows, cursor = [], None
    for _ in range(max_pages):
        p = {"ticker": ticker, "min_ts": int(t_lo.timestamp()), "max_ts": int(t_hi.timestamp()), "limit": 1000}
        if cursor:
            p["cursor"] = cursor
        d = get_json("/markets/trades", p)
        rows += d.get("trades", [])
        cursor = d.get("cursor")
        if not cursor or not d.get("trades"):
            break
        time.sleep(pause)
    return rows


def last_before(trades: Sequence[Trade], t: datetime, lookback: timedelta) -> Optional[Trade]:
    best = None
    for x in trades:
        if x.ts > t:
            break
        best = x
    return best if best is not None and t - best.ts <= lookback else None


def tail_level(trades: Sequence[Trade], t0: datetime, lo_min: float, hi_min: float, min_prints: int = 2) -> Optional[float]:
    """Count-weighted mean YES price of prints in [t0+lo, t0+hi]: the 'adjusted' level.  None if too few prints."""
    w = [x for x in trades if t0 + timedelta(minutes=lo_min) <= x.ts <= t0 + timedelta(minutes=hi_min)]
    if len(w) < min_prints:
        return None
    c = sum(x.count for x in w)
    return sum(x.yes * x.count for x in w) / c if c else None


def signed_path(trades: Sequence[Trade], t0: datetime, sign: int, minutes: Sequence[int],
                lookback_min: int = 30) -> Optional[dict]:
    """Signed move (news direction) at each minute vs the last print at/before t0.  Forward-filled last print; a minute
    before any print inside ``lookback_min`` before t0 gives None.  Returns {'ref': yes, 'path': {m: move|None}}."""
    ref = last_before(trades, t0, timedelta(minutes=lookback_min))
    if ref is None:
        return None
    path = {}
    for m in minutes:
        x = last_before(trades, t0 + timedelta(minutes=m), timedelta(minutes=lookback_min + max(m, 0)))
        path[m] = None if x is None else sign * (x.yes - ref.yes)
    return {"ref": ref.yes, "ref_age_s": (t0 - ref.ts).total_seconds(), "path": path}


def lag_to_fraction(trades: Sequence[Trade], t0: datetime, sign: int, frac: float, final: float,
                    horizon_min: int = 30, step_s: int = 15) -> Optional[float]:
    """Minutes after t0 at which the signed move (vs the last pre-news print) FIRST reaches ``frac`` x ``final``, from real
    prints only.  ``final`` is the signed full move (tail level - ref).  None when final <= 0 or never reached."""
    ref = last_before(trades, t0, timedelta(minutes=30))
    if ref is None or final <= 0:
        return None
    for x in trades:
        if x.ts <= t0 or x.ts > t0 + timedelta(minutes=horizon_min):
            continue
        if sign * (x.yes - ref.yes) >= frac * final:
            return (x.ts - t0).total_seconds() / 60.0
    return None


def entry_net(trades: Sequence[Trade], t0: datetime, sign: int, k_min: float, final_yes: float, series: str,
              patience_min: float = 10.0) -> Optional[dict]:
    """A taker who acts at t0+k: buy the news-favoured side at the first print on/after t0+k in which the aggressor bought
    that same side (YES if sign>0 else NO).  Cost = that print's price (not a mid) + the exact taker fee; value = the
    adjusted level (``final_yes``, or 1-final_yes for NO).  Net per contract, hold to the adjusted level, NO exit cost
    charged -- an upper bound on a round trip.  None if no such print within ``patience_min``."""
    want = "yes" if sign > 0 else "no"
    lo, hi = t0 + timedelta(minutes=k_min), t0 + timedelta(minutes=k_min + patience_min)
    for x in trades:
        if x.ts < lo:
            continue
        if x.ts > hi:
            break
        if x.taker == want:
            cost = x.yes if want == "yes" else 1.0 - x.yes
            value = final_yes if want == "yes" else 1.0 - final_yes
            fee = money.fee_rate(series, cost, "taker")
            return {"cost": cost, "fee": fee, "gross": value - cost, "net": value - cost - fee,
                    "wait_s": (x.ts - lo).total_seconds()}
    return None


def summarize(rows: Sequence[tuple], boots: int = 2000) -> dict:
    """rows = (game_key, value, abs_value) -> mean and game-clustered bootstrap CI (reuses news_lag's)."""
    return news_lag._summ(list(rows), boots)
