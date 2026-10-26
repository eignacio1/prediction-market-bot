#!/usr/bin/env python3
"""NHL pregame SHADOW evaluator (T-607 / EXP-036). Evaluate-and-log ONLY.

Reads Kalshi NHL markets (read-only, <=1 req/s, halved on 429), asks a forecaster for
p_yes, computes net-of-fee edge at the quoted entry price under both fee candidates, and
appends one JSONL row per (cell, run_id, market_ticker). It NEVER places an order, opens a
position, writes a pool, or touches sizing — see tests/test_nhl_shadow_safety.py.
Retire in favour of 47.2's runner once that is on origin/main.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion import nhl_ingest as ni  # noqa: E402
from prediction_market_bot.c3_forecasting.nhl_pregame import TEAM_ALIASES, split_team_codes  # noqa: E402
from prediction_market_bot.quant import money as _Q  # noqa: E402

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = {"KXNHLGAME": "NHL_MONEYLINE", "KXNHLSPREAD": "NHL_PUCK_LINE", "KXNHLTOTAL": "NHL_GAME_TOTAL"}
FEE_K = 0.07
SERIES_FEE_MULT = {"KXNHLGAME": 1.0, "KXNHLSPREAD": 1.0, "KXNHLTOTAL": 1.0}  # verified 2026-10-02
SHADOW_DIR = Path("data/shadow/nhl")
# Horizon windows in hours before start (EXECUTION_BANDS.md; T3 = final 15-60 min).
BANDS = {"T1": (12.0, 48.0), "T2": (4.0, 8.0), "T3": (0.25, 1.0)}
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


class Forecast(Protocol):  # structural match to pregame_shadow.contract.PregameForecast
    p_yes: float
    as_of_utc: datetime
    model_id: str
    model_sha256: str
    feature_row_sha256: str


class Forecaster(Protocol):
    sport: str

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[Forecast]: ...


# ------------------------------------------------------------------ pure helpers
def fee_per_contract(price: float, k: float) -> float:
    """Kalshi taker fee per contract, unrounded: k * p * (1-p)."""
    return k * price * (1.0 - price)


def edge_net(p_yes: float, yes_bid: float, yes_ask: float, k: float) -> tuple[float, float]:
    """(E_net buying YES at ask, E_net buying NO at 1-bid), per $1 contract, fees included."""
    if k == _Q.K007:  # the core owns the k007 definition (W87.1); any other k keeps the local formula
        r = _Q.net_edge(p_yes, yes_bid, yes_ask)
        return r["yes"], r["no"]
    no_ask = 1.0 - yes_bid
    ey = p_yes - yes_ask - fee_per_contract(yes_ask, k)
    en = (1.0 - p_yes) - no_ask - fee_per_contract(no_ask, k)
    return ey, en


def band_for(horizon_h: float) -> Optional[str]:
    for b, (lo, hi) in BANDS.items():
        if lo <= horizon_h <= hi:
            return b
    return None


def event_date_teams(event_ticker: str) -> Optional[tuple[str, frozenset]]:
    """KXNHLGAME-26OCT08TORVGK -> ('2026-10-08', {'TOR','VGK'}); None if unparseable."""
    try:
        tail = event_ticker.split("-", 1)[1]
        yy, mon, dd, teams = int(tail[:2]), tail[2:5], int(tail[5:7]), tail[7:]
        codes = split_team_codes(teams)  # Kalshi uses 2- and 3-letter codes; mapped to NHL-data abbrevs
        if codes is None:
            return None
        return (f"20{yy:02d}-{MONTHS.index(mon) + 1:02d}-{dd:02d}",
                frozenset(TEAM_ALIASES.get(c, c) for c in codes))
    except (IndexError, ValueError):
        return None


def build_start_index(schedule_games: list[dict]) -> dict:
    """{(local_date, frozenset(teams)): start_time_utc} from the NHL schedule."""
    return {(g["game_date"], frozenset((g["home"], g["away"]))): g["start_time_utc"] for g in schedule_games}


def resolve_start(market: dict, index: dict) -> tuple[Optional[datetime], str]:
    dt = event_date_teams(market["event_ticker"])
    if dt and (dt[0], dt[1]) in index:
        return ni_ts(index[(dt[0], dt[1])]), "nhl_schedule"
    occ = market.get("occurrence_datetime")  # Kalshi: ~expected end; start ~= occurrence - 3h
    if occ:
        return ni_ts(occ) - timedelta(hours=3), "kalshi_occurrence_minus_3h"
    return None, "unknown"


def ni_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def quote(market: dict) -> Optional[tuple[float, float]]:
    try:
        b, a = float(market["yes_bid_dollars"]), float(market["yes_ask_dollars"])
    except (KeyError, TypeError, ValueError):
        return None
    return (b, a) if 0.0 < b < a < 1.0 else None  # one-sided / empty book -> no row


def make_row(market: dict, series: str, fc: Any, start: datetime, start_src: str, now: datetime,
             run_id: str, code_sha: str, band: str) -> Optional[dict]:
    q = quote(market)
    if q is None or fc is None:
        return None
    bid, ask = q
    mult = SERIES_FEE_MULT.get(series, 1.0)
    ey7, en7 = edge_net(fc.p_yes, bid, ask, FEE_K)
    return {
        "run_id": run_id, "ts_utc": now.isoformat(), "sport": "NHL", "market_type": SERIES[series],
        "band": band, "horizon_hours_to_start": round((start - now).total_seconds() / 3600.0, 4),
        "event_ticker": market["event_ticker"], "market_ticker": market["ticker"], "p_yes": fc.p_yes,
        "yes_bid": bid, "yes_ask": ask, "mid": (bid + ask) / 2.0, "half_spread": (ask - bid) / 2.0,
        "fee_k007": FEE_K, "fee_kmult": FEE_K * mult, "e_net_yes_k007": ey7, "e_net_no_k007": en7,
        "e_net_yes_kmult": edge_net(fc.p_yes, bid, ask, FEE_K * mult)[0],
        "e_net_no_kmult": edge_net(fc.p_yes, bid, ask, FEE_K * mult)[1],
        "model_id": fc.model_id, "model_sha256": fc.model_sha256, "feature_row_sha256": fc.feature_row_sha256,
        "start_time_utc": start.isoformat(), "start_time_source": start_src, "code_sha": code_sha,
        # EXP-036 goalie amendment (2026-10-08): rows are flagged confirmed=False; no pre-drop confirmed source (GG-530).
        "confirmed": bool(getattr(fc, "confirmed", False)),
        "starter_source": getattr(fc, "starter_source", "projected_last_start"),
    }


def cell_path(root: Path, market_type: str, band: str) -> Path:
    return root / f"{market_type}_{band}.jsonl"


def append_rows(rows: list[dict], root: Path, on_row=None) -> dict[str, int]:
    """Append-only, idempotent per (run_id, market_ticker) within each cell file.
    ``on_row`` (W68.2, optional, default None): called with a COPY of each row AFTER it is persisted;
    exceptions are swallowed. This file imports nothing order-related; the callback is injected."""
    counts: dict[str, int] = {}
    seen: dict[Path, set] = {}
    for r in rows:
        p = cell_path(root, r["market_type"], r["band"])
        if p not in seen:
            seen[p] = set()
            if p.exists():
                for line in p.read_text().splitlines():
                    if line.strip():
                        d = json.loads(line)
                        seen[p].add((d["run_id"], d["market_ticker"]))
        key = (r["run_id"], r["market_ticker"])
        if key in seen[p]:
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            f.write(json.dumps(r, sort_keys=True) + "\n")
        seen[p].add(key)
        if on_row is not None:
            try:
                on_row(dict(r))
            except Exception:  # staking must never disturb the shadow ledger
                pass
        counts[f"{r['market_type']}_{r['band']}"] = counts.get(f"{r['market_type']}_{r['band']}", 0) + 1
    return counts


# ------------------------------------------------------------------ Kalshi (read-only)
def fetch_open_markets(series: str, throttle: ni.Throttle, opener=None) -> list[dict]:
    out, cursor = [], ""
    while True:
        url = f"{KALSHI}/markets?series_ticker={series}&status=open&limit=200" + (f"&cursor={cursor}" if cursor else "")
        d = ni.http_get_json(url, throttle, opener=opener)
        out.extend(d.get("markets", []))
        cursor = d.get("cursor") or ""
        if not cursor:
            return out


def _bump(counters: Optional[dict], key: str) -> None:
    if counters is not None:
        counters[key] = counters.get(key, 0) + 1


def evaluate(markets_by_series: dict[str, list[dict]], forecaster: Forecaster, start_index: dict,
             now: datetime, run_id: str, code_sha: str, force_band: Optional[str] = None,
             counters: Optional[dict] = None) -> list[dict]:
    """``counters`` (mutated in place) names every reason a market did not become a row, so no
    drop is silent. ``out_of_band`` is a normal exclusion, not a failure; every other key is a drop."""
    rows = []
    for series, markets in markets_by_series.items():
        for m in markets:
            _bump(counters, "markets_seen")
            if event_date_teams(m["event_ticker"]) is None:
                _bump(counters, "ticker_unparsed_or_team_unmapped")
            start, src = resolve_start(m, start_index)
            if start is None:
                _bump(counters, "start_unknown")
                continue
            h = (start - now).total_seconds() / 3600.0
            band = band_for(h)
            if band is None or (force_band and band != force_band):
                _bump(counters, "out_of_band")
                continue
            if quote(m) is None:
                _bump(counters, "no_valid_quote")
                continue
            fc = forecaster.forecast(m["ticker"], now)
            if fc is None:
                _bump(counters, "forecast_none:" + (getattr(forecaster, "last_abstain", None) or "unspecified"))
                continue
            row = make_row(m, series, fc, start, src, now, run_id, code_sha, band)
            if row:
                rows.append(row)
            else:
                _bump(counters, "row_not_built")
    return rows


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


class StubForecaster:
    """Dry-run only (p=0.5). Rows are written under a separate dry-run dir and labelled."""
    sport = "NHL"

    class _F:
        p_yes, model_id, model_sha256, feature_row_sha256 = 0.5, "STUB-DRYRUN", "0" * 64, "0" * 64
        as_of_utc = None

    def forecast(self, market_ticker, as_of_utc):
        f = self._F()
        f.as_of_utc = as_of_utc
        return f


def build_real_forecaster(now):
    """Frozen model + local finished-game store + current-season schedule (read-only)."""
    from prediction_market_bot.c2_feature_store.nhl_features import NhlFeatureStore
    from prediction_market_bot.c3_forecasting.nhl_pregame import NhlPregameForecaster, load_model
    model, sha = load_model()
    cur = now.year - (1 if now.month < 8 else 0)
    sched = ni.load_schedule(cur) + ni.load_schedule(cur - 1)
    return NhlPregameForecaster(model, sha, NhlFeatureStore(ni.load_games()), sched)


def main(argv=None, on_row=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", choices=list(BANDS), help="only evaluate games inside this band's window")
    ap.add_argument("--run-id", default=None, help="idempotency key; default = band + UTC date-hour")
    ap.add_argument("--root", default=str(SHADOW_DIR))
    ap.add_argument("--stub", action="store_true", help="DRY RUN with a stub forecaster (writes to --root only)")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    run_id = a.run_id or f"{a.band or 'ALL'}-{now:%Y%m%dT%H}-{uuid.uuid4().hex[:6] if a.stub else 'auto'}"
    if a.stub:
        fcst: Forecaster = StubForecaster()
    else:
        fcst = build_real_forecaster(now)
    th = ni.Throttle(1.0)
    sched = []
    for s in {now.year - (1 if now.month < 8 else 0)}:
        sched += ni.load_schedule(s)
    index = build_start_index(sched)
    mk = {s: fetch_open_markets(s, th) for s in SERIES}
    counters: dict[str, int] = {}
    rows = evaluate(mk, fcst, index, now, run_id, git_sha(), a.band, counters)
    counts = {} if a.no_write else append_rows(rows, Path(a.root), on_row=None if a.stub else on_row)
    summary = {"run_id": run_id, "ts_utc": now.isoformat(), "markets_read": {k: len(v) for k, v in mk.items()},
               "rows_evaluated": len(rows), "rows_appended_by_cell": counts, "abstention_counters": counters}
    if not a.no_write:  # run metadata ledger: one line per run, alongside the cell files
        Path(a.root).mkdir(parents=True, exist_ok=True)
        with (Path(a.root) / "run_log.jsonl").open("a") as f:
            f.write(json.dumps(summary, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
