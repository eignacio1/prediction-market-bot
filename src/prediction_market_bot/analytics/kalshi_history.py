"""Reader for the validated Kalshi history store at ``exp_output/KALSHI_HISTORY`` (Wave 47 / 47.1 D4).

    from prediction_market_bot.analytics.kalshi_history import prevailing_quote, settlement

Prevailing-quote rule (same rule Gate 2 / EXP-035 froze for KXMLBTOTAL): the close of the latest candle with
``end_period_ts <= t``; 1-minute candles first, hourly fallback; otherwise ``None`` (unmatched). The returned
``as_of_candle_ts`` lets the caller judge staleness. A bid or ask may be ``None`` when that candle's close quote
is null. Candle windows in the store: hourly over [open, close+1h]; 1-minute over the last 48h before close.
Store layout and provenance: see ``scripts/kalshi_history_build.py`` and ``exp_output/KALSHI_HISTORY/VALIDATION.json``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

STORE = Path(__file__).resolve().parents[3] / "exp_output" / "KALSHI_HISTORY"
_idx: dict[tuple, dict] = {}


def _series(ticker: str) -> str:
    return ticker.split("-")[0]


def _load(kind: str, series: str, store: Path) -> dict:
    """Byte-offset index of one jsonl file: key -> [offsets]. Rows are read lazily on lookup."""
    k = (str(store), kind, series)
    if k not in _idx:
        offs: dict = {}
        p = store / kind / f"{series}.jsonl"
        if p.exists():
            with open(p, "rb") as fh:
                pos = fh.tell()
                for line in iter(fh.readline, b""):
                    r = json.loads(line)
                    key = r["ticker"] if kind == "markets" else (r["ticker"], r["period_min"])
                    offs[key] = pos
                    pos = fh.tell()
        _idx[k] = offs
    return _idx[k]


def _row(kind: str, key, series: str, store: Path):
    off = _load(kind, series, store).get(key)
    if off is None:
        return None
    with open(store / kind / f"{series}.jsonl", "rb") as fh:
        fh.seek(off)
        return json.loads(fh.readline())


def _epoch(t) -> int:
    if isinstance(t, (int, float)):
        return int(t)
    if isinstance(t, str):
        s = t.replace("Z", "+00:00")
        t = datetime.fromisoformat(s)
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return int(t.timestamp())


def prevailing_quote(market_ticker: str, t_utc, store: Path = STORE):
    """(yes_bid, yes_ask, as_of_candle_ts) at time ``t_utc`` (datetime, ISO string or epoch), or None."""
    t = _epoch(t_utc)
    series = _series(market_ticker)
    for period in (1, 60):
        row = _row("candles", (market_ticker, period), series, store)
        if not row:
            continue
        best = None
        for c in row["candles"]:
            if c["t"] <= t:
                best = c
            else:
                break
        if best is not None:
            return best["bid"]["close"], best["ask"]["close"], best["t"]
    return None


def settlement(market_ticker: str, store: Path = STORE):
    """Settlement result string ('yes'/'no'; scalar results pass through) or None if the market is not in the store."""
    row = _row("markets", market_ticker, _series(market_ticker), store)
    return None if row is None else row["result"]
