"""Sport-agnostic pregame shadow runner (EXP-037 / D2a). EVALUATE-AND-LOG ONLY.

Lists open markets per cell's series (read-only), forecasts at as_of=now, reads the
list-endpoint book, writes ONE row per (market, evaluation) to that cell's ledger.
Nothing here imports or calls any order / position / sizing / paper-trader code
(enforced by tests/test_pregame_shadow_safety.py).
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from prediction_market_bot.pregame_shadow.bands import band_for_horizon
from prediction_market_bot.pregame_shadow.fees import e_net, fee_kmult, fee_k007
from prediction_market_bot.pregame_shadow.ledger import CellLedger


def _f(x) -> Optional[float]:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def run_once(*, forecaster, cells: list[tuple[str, str]],
             list_markets: Callable[[str], tuple[bool, list[dict]]],
             kickoff_for: Callable[[str], Optional[tuple[datetime, str]]],
             ledger_dir: Path, run_id: str, now_utc: datetime, code_sha: str,
             raw_filter: Optional[Callable[[dict], bool]] = None,
             only_bands: Optional[set] = None, ledger_extra: Optional[dict] = None,
             kickoff_miss_reason: Optional[Callable[[str], str]] = None,
             on_row: Optional[Callable[[dict], None]] = None) -> dict:
    """cells = [(MarketType name, series_ticker)]. Returns {'written': {...}, 'skipped': {...}}."""
    written: Counter = Counter()
    skipped: Counter = Counter()
    ledgers: dict[tuple[str, str], CellLedger] = {}
    for mt_name, series in cells:
        ok, raw = list_markets(series)
        if not ok:
            skipped[f"{mt_name}:list_failed"] += 1
            continue
        for m in raw:
            tkr = m.get("ticker", "")
            ev = m.get("event_ticker", "")
            if raw_filter is not None and not raw_filter(m):
                skipped[f"{mt_name}:raw_filter"] += 1
                continue
            ko = kickoff_for(ev)
            if ko is None:
                why = kickoff_miss_reason(ev) if kickoff_miss_reason else "no_kickoff"
                skipped[f"{mt_name}:{why}"] += 1
                continue
            start, src = ko
            hours = (start - now_utc).total_seconds() / 3600.0
            band = band_for_horizon(hours)
            if band is None:
                skipped[f"{mt_name}:outside_band_windows"] += 1
                continue
            if only_bands is not None and band not in only_bands:
                skipped[f"{mt_name}:band_not_requested"] += 1
                continue
            bid, ask = _f(m.get("yes_bid_dollars")), _f(m.get("yes_ask_dollars"))
            if bid is None or ask is None or bid <= 0 or ask <= 0 or ask < bid or ask >= 1:
                skipped[f"{mt_name}:no_book"] += 1
                continue
            fc = forecaster.forecast(tkr, now_utc)
            if fc is None:
                skipped[f"{mt_name}:no_forecast"] += 1
                continue
            ey, en = e_net(fc.p_yes, bid, ask, fee_k007)
            row = {
                "run_id": run_id, "ts_utc": now_utc.isoformat(), "sport": fc.sport,
                "market_type": mt_name, "band": band, "horizon_hours_to_start": round(hours, 4),
                "event_ticker": ev, "market_ticker": tkr, "p_yes": fc.p_yes, "yes_bid": bid,
                "yes_ask": ask, "mid": (bid + ask) / 2.0, "half_spread": (ask - bid) / 2.0,
                "fee_k007": fee_k007((bid + ask) / 2.0), "fee_kmult": fee_kmult((bid + ask) / 2.0),
                "e_net_yes_k007": ey, "e_net_no_k007": en, "model_id": fc.model_id,
                "model_sha256": fc.model_sha256, "feature_row_sha256": fc.feature_row_sha256,
                "start_time_utc": start.isoformat(), "start_time_source": src, "code_sha": code_sha,
            }
            led = ledgers.setdefault((mt_name, band), CellLedger(ledger_dir, fc.sport, mt_name, band, ledger_extra))
            if led.append(row):
                written[f"{mt_name}:{band}"] += 1
                if on_row is not None:  # post-persist observer; gets a copy, cannot alter the row
                    try:
                        on_row(dict(row))
                    except Exception:  # noqa: BLE001 - observer failure never affects the shadow run
                        pass
            else:
                skipped[f"{mt_name}:duplicate"] += 1
    return {"written": dict(written), "skipped": dict(skipped)}
