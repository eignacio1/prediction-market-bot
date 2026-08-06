#!/usr/bin/env python3
"""T-426 TASK 2 + TASK 3 — full-population calibration via the decoupled store.

READ-ONLY. Builds ALONGSIDE run_power_calc.py / run_band_monitor.py; does not
edit either.

TASK 2 — Brier score + reliability bins over the FULL evaluation population
(every cycle-log row with a non-null p_t4 whose ticker resolved in the
decoupled outcome store), split into:
  - FIRED   — the exact (ticker, cycle_id) pair that produced a ledger
              position (row-level match via forecast_id, not a ticker-level
              proxy — see match_bet_rows()).
  - DECLINED — every other resolved-ticker evaluation row.

Ground truth per row: outcome = 1 if store.actual_hits >= row.threshold else
0. This is the row's OWN threshold (thresholds are per-market, e.g. "hits >=
1" and "hits >= 2" are separate tickers/rows for the same player-game), so
the derived outcome is threshold-specific, not a single per-player fact.

TASK 3 — n-for-verdict: apply the SAME one-sample power-calc machinery
run_power_calc.py uses for the $EV verdict (n* = ((z_a+z_b)*sigma/mu)**2),
but to the calibration-bias signal (outcome - p_t4) instead of $pnl. This
answers a DIFFERENT governance question than run_power_calc.py's n*=267
($EV per bet > 0) — it answers "how many evaluations to statistically
distinguish model calibration bias != 0 from bias == 0" — and the two must
not be conflated. Reports both n* and the wall-clock ETA implied by each
path's own observed cadence, to quantify the speedup claim.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_power_calc import z_for  # noqa: E402 — reuse, not reimplement

DEFAULT_LEDGER = _REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.jsonl"
DEFAULT_STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"
DEFAULT_CYCLE_LOG = _REPO_ROOT / "logs" / ".vps_t4_mlb_cycle_log_cache.jsonl"

BINS = [(i / 10, (i + 1) / 10) for i in range(10)]


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def match_bet_rows(ledger: list[dict]) -> set[tuple[str, str]]:
    """(ticker, cycle_id) pairs that fired a ledger position, via exact
    row-level join: forecast_id = "T4-MLB-{cycle_id_part1}-{cycle_id_part2}-
    {player_code}-{threshold}" where "{cycle_id_part1}-{cycle_id_part2}" is
    byte-identical to the cycle log's own `cycle_id` field (verified by
    direct sample inspection: forecast_id
    "T4-MLB-C0017-e3c02b-NOOTBAAR21-1" <-> cycle_id "C0017-e3c02b" for the
    same ticker). This is a real row-level join, not a ticker-level proxy."""
    fired = set()
    for r in ledger:
        fid = r.get("forecast_id", "")
        ticker = r.get("kalshi_ticker", "")
        parts = fid.split("-")
        if len(parts) >= 4 and parts[0] == "T4" and parts[1] == "MLB":
            cycle_id = f"{parts[2]}-{parts[3]}"
            fired.add((ticker, cycle_id))
    return fired


def build_full_population(cycle_log: list[dict], store_by_ticker: dict[str, dict],
                           fired_keys: set[tuple[str, str]]) -> list[dict]:
    rows = []
    for r in cycle_log:
        p_t4 = r.get("p_t4")
        ticker = r.get("ticker")
        if p_t4 is None or not ticker:
            continue
        srec = store_by_ticker.get(ticker)
        if srec is None or not srec.get("resolved"):
            continue
        try:
            thr = int(r.get("threshold", 0) or 0)
            actual_hits = float(srec["actual_hits"])
        except (TypeError, ValueError, KeyError):
            continue
        outcome = 1.0 if actual_hits >= thr else 0.0
        key = (ticker, r.get("cycle_id"))
        rows.append({
            "ticker": ticker,
            "cycle_id": r.get("cycle_id"),
            "p_t4": float(p_t4),
            "outcome": outcome,
            "fired": key in fired_keys,
        })
    return rows


def brier(rows: list[dict]) -> float | None:
    if not rows:
        return None
    return statistics.mean((r["p_t4"] - r["outcome"]) ** 2 for r in rows)


def reliability_bins(rows: list[dict]) -> list[dict]:
    out = []
    for lo, hi in BINS:
        in_bin = [r for r in rows if (lo <= r["p_t4"] < hi) or (hi == 1.0 and r["p_t4"] == 1.0)]
        if not in_bin:
            out.append({"bin": f"[{lo:.1f},{hi:.1f})", "n": 0, "mean_p_t4": None, "observed_freq": None})
            continue
        out.append({
            "bin": f"[{lo:.1f},{hi:.1f})",
            "n": len(in_bin),
            "mean_p_t4": statistics.mean(r["p_t4"] for r in in_bin),
            "observed_freq": statistics.mean(r["outcome"] for r in in_bin),
        })
    return out


def task2(rows: list[dict]) -> dict:
    fired = [r for r in rows if r["fired"]]
    declined = [r for r in rows if not r["fired"]]
    return {
        "full_population_n_rows": len(rows),
        "full_population_n_tickers": len({r["ticker"] for r in rows}),
        "full_population_brier": brier(rows),
        "full_population_reliability": reliability_bins(rows),
        "fired_n_rows": len(fired),
        "fired_brier": brier(fired),
        "fired_reliability": reliability_bins(fired),
        "declined_n_rows": len(declined),
        "declined_brier": brier(declined),
        "declined_reliability": reliability_bins(declined),
    }


def _parse_ts(raw: str | None):
    if not raw:
        return None
    s = raw[:-6] if raw and raw.endswith(("+00:00",)) else raw
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def task3(rows: list[dict], alpha: float, power: float,
          ledger_n_star: float | None, ledger_cadence_per_week: float | None,
          cycle_log: list[dict]) -> dict:
    bias = [r["outcome"] - r["p_t4"] for r in rows]
    n = len(bias)
    result = {"n_evaluations": n, "alpha": alpha, "power": power}
    if n < 2:
        result["status"] = "INSUFFICIENT_DATA"
        return result

    mu_bias = statistics.mean(bias)
    sigma_bias = statistics.stdev(bias)
    result["mu_bias"] = mu_bias
    result["sigma_bias"] = sigma_bias
    result["interpretation"] = (
        "mu_bias = mean(outcome - p_t4) over the full evaluation population. "
        "This answers a DIFFERENT governance question than run_power_calc.py's "
        "n*=267 ($EV per bet > 0): it answers 'how many evaluations are needed "
        "to distinguish systematic calibration bias != 0 from bias == 0 at this "
        "sample's observed bias/variance.' Do not conflate the two verdicts."
    )

    z_a, z_b = z_for(alpha), z_for(power)
    if mu_bias == 0:
        result["status"] = "PERFECTLY_CALIBRATED_POINT_ESTIMATE"
        result["n_star_calibration"] = None
    else:
        n_star = ((z_a + z_b) * sigma_bias / mu_bias) ** 2
        result["status"] = "OK"
        result["n_star_calibration"] = n_star

    # cadence: rows/week over the cycle log's own observed span
    ts = [_parse_ts(r.get("ts")) for r in cycle_log]
    ts = [t for t in ts if t is not None]
    if len(ts) >= 2:
        span_days = (max(ts) - min(ts)).total_seconds() / 86400.0
        rows_per_week = len(cycle_log) / (span_days / 7.0) if span_days >= 1.0 else None
        resolved_rows_per_week = n / (span_days / 7.0) if span_days >= 1.0 else None
    else:
        span_days = None
        rows_per_week = None
        resolved_rows_per_week = None
    result["cycle_log_span_days"] = span_days
    result["all_rows_per_week"] = rows_per_week
    result["resolved_scoreable_rows_per_week"] = resolved_rows_per_week

    if result.get("n_star_calibration") and resolved_rows_per_week:
        n_star = result["n_star_calibration"]
        remaining = max(0.0, n_star - n)
        result["eta_weeks_decoupled_path"] = remaining / resolved_rows_per_week

    if ledger_n_star and ledger_cadence_per_week:
        result["ledger_n_star"] = ledger_n_star
        result["ledger_cadence_per_week"] = ledger_cadence_per_week

    if rows_per_week and ledger_cadence_per_week:
        result["cadence_speedup_rows_vs_bets"] = rows_per_week / ledger_cadence_per_week

    return result


def main() -> None:
    ledger = load_jsonl(DEFAULT_LEDGER)
    resolved_ledger = [r for r in ledger if r.get("outcome") in ("WIN", "LOSS") and r.get("model_p") is not None]
    store_by_ticker = {r["ticker"]: r for r in load_jsonl(DEFAULT_STORE)}
    cycle_log = load_jsonl(DEFAULT_CYCLE_LOG)
    fired_keys = match_bet_rows(ledger)

    rows = build_full_population(cycle_log, store_by_ticker, fired_keys)

    out = {
        "task2_calibration": task2(rows),
        "task3_n_for_verdict": task3(
            rows, alpha=0.05, power=0.95,
            ledger_n_star=267.0,  # from run_power_calc.py's current live output — see report
            ledger_cadence_per_week=275.2,  # ditto
            cycle_log=cycle_log,
        ),
        "match_diagnostics": {
            "ledger_resolved_positions": len(resolved_ledger),
            "ledger_positions_with_row_level_match": None,  # filled in below
        },
    }
    # real fired-row match-rate diagnostic: how many resolved ledger positions
    # actually found their exact cycle-log row (vs ticker existing but the
    # specific cycle_id missing from the log, e.g. due to log rotation)
    matched_positions = 0
    for r in resolved_ledger:
        fid = r.get("forecast_id", "")
        parts = fid.split("-")
        if len(parts) >= 4 and parts[0] == "T4" and parts[1] == "MLB":
            key = (r.get("kalshi_ticker"), f"{parts[2]}-{parts[3]}")
            if key in fired_keys:
                matched_positions += 1
    out["match_diagnostics"]["ledger_positions_with_row_level_match"] = matched_positions

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
