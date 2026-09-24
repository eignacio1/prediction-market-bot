#!/usr/bin/env python3
"""
Closing-Line-Value (CLV) Instrument (T-572, 2026-09-24)
=========================================================

WHY THIS EXISTS
---------------
Two prior measurement paths on T4M-PROJ are either exhausted (T-569: the
latency thesis is NOT SUPPORTED -- forward slope of delta_mip on gross_edge
is wrong-signed, backward placebo ran 5.1-6.4x forward) or unusable at
adequate n this wave (T-571/GG-300: only 34/765 approvals are
Kalshi-confirmed, headline reverses on that subset per GG-301). CLV needs
only the price archive (a ticker-keyed, timestamped `mip` series) -- no
settlement/outcome data -- and answers a different question than either
prior path: did the price an entry was made at beat the price the market
later settled on, for the side taken.

Methodology is pre-registered and immutable:
  05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T572_clv_harness_PREREGISTRATION.md
Do not change the CLV definition, entry/closing rules, cohort construction,
confound designs, or verdict thresholds here without a superseding
pre-registration document. This module implements that document; it does
not re-derive methodology.

REUSABLE INSTRUMENT, NOT A ONE-OFF SCRIPT
------------------------------------------
`compute_clv_row()` takes the general contract (ticker, entry_ts,
entry_price, side, size_or_none) against a loaded price series and returns
one row's CLV plus bookkeeping. `cohort_aggregate()` takes a list of such
rows (or raises/logs exclusions per the malformed-input contract below) and
returns equal-weighted (and, when sizes are present, size-weighted) means
with dual-clustered (by-ticker, by-game) block-bootstrap CIs. Every future
cell that has a ticker-keyed timestamped price series and a defined entry
rule can reuse this without touching T4-MLB-specific code -- the T4-MLB
entry/control construction lives in `build_t4mlb_cohorts()`, kept separate
from the generic instrument.

REFUSE LOUDLY, NEVER IMPUTE
----------------------------
`compute_clv_row()` raises `NoClosingObservationError` /
`TickerNotFoundError` / `InvalidSideError` / `InvalidEntryPriceError` on the
four malformed-input conditions specified in the pre-registration §7. It
never returns a silently-imputed CLV. Cohort-building code is responsible
for catching these per-row and logging exclusions with counts and reasons --
the row-level function itself must not swallow them (tests enforce this).

Usage (T4-MLB application, Deliverable 3):
  python3 scripts/clv_harness.py \
      --cycle-log logs/t4_mlb_cycle_log.jsonl \
      --out exp_output/T572_CLV_HARNESS/clv_results.json
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal, Sequence

import numpy as np

Side = Literal["YES", "NO"]

MIN_EDGE_TO_APPROVE = 0.04  # risk.py, ADR-0020 -- reconfirmed this session
KALSHI_FEE_RATE = 0.07  # run_t4_mlb_live.py:1165, ADR-0016 taker fee
BACKWARD_PLACEBO_RATIO_THRESHOLD = 0.50  # T572_..._PREREGISTRATION.md §5(b), matches T-569
N_BOOTSTRAP = 1000
MIN_QUALIFYING_TICKERS = 30  # T572 pre-reg §8 floor, matches T-569's 30-event floor


# --------------------------------------------------------------------------- #
# Exceptions -- the "refuse loudly" contract (pre-reg §7)
# --------------------------------------------------------------------------- #

class ClvHarnessError(Exception):
    """Base for all harness-raised errors -- never caught silently by compute_clv_row."""


class TickerNotFoundError(ClvHarnessError):
    pass


class NoClosingObservationError(ClvHarnessError):
    pass


class InvalidSideError(ClvHarnessError):
    pass


class InvalidEntryPriceError(ClvHarnessError):
    pass


# --------------------------------------------------------------------------- #
# Core data structures
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class PriceObservation:
    ts: str
    mip: float
    inning: int | None = None
    gross_edge: float | None = None
    p_t4: float | None = None
    vig: float | None = None


@dataclass(frozen=True)
class TickerSeries:
    ticker: str
    game_id: str
    observations: tuple[PriceObservation, ...]  # sorted ascending by ts


@dataclass(frozen=True)
class ClvRow:
    ticker: str
    game_id: str
    entry_ts: str
    entry_price: float
    entry_mip: float
    side: Side
    size: float | None
    closing_ts: str
    closing_mip: float
    clv: float
    backward_ts: str
    backward_mip: float
    backward_move: float  # side_sign * (entry_mip - backward_mip)
    signal: float  # directional_net_edge (or raw gross_edge for unconditioned controls)
    own_dislocation: float | None  # None if <3 prior rows available
    bucket_fallback: bool = False


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load_ticker_series(cycle_log_path: str | Path) -> dict[str, TickerSeries]:
    """Group cycle-log rows by ticker, sorted ascending by ts, dt<=0 pairs dropped.

    Tickers with exactly 1 usable row (no possible closing observation
    distinct from any entry) are dropped here and their count returned
    alongside the series map, per pre-reg §1.
    """
    raw: dict[str, list[dict]] = defaultdict(list)
    with open(cycle_log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            raw[d["ticker"]].append(d)

    series: dict[str, TickerSeries] = {}
    singleton_count = 0
    dropped_nonmonotonic = 0
    for ticker, rows in raw.items():
        rows.sort(key=lambda r: r["ts"])
        obs: list[PriceObservation] = []
        last_ts: str | None = None
        for r in rows:
            if last_ts is not None and r["ts"] <= last_ts:
                dropped_nonmonotonic += 1
                continue
            obs.append(
                PriceObservation(
                    ts=r["ts"],
                    mip=r["mip"],
                    inning=r.get("inning"),
                    gross_edge=r.get("gross_edge"),
                    p_t4=r.get("p_t4"),
                    vig=r.get("vig"),
                )
            )
            last_ts = r["ts"]
        if len(obs) < 2:
            singleton_count += 1
            continue
        game_id = ticker.split("-")[1] if "-" in ticker else ticker
        series[ticker] = TickerSeries(ticker=ticker, game_id=game_id, observations=tuple(obs))

    series = dict(series)
    series["__meta__singleton_dropped__"] = singleton_count  # type: ignore[assignment]
    series["__meta__nonmonotonic_dropped__"] = dropped_nonmonotonic  # type: ignore[assignment]
    return series


def _pop_meta(series: dict[str, TickerSeries]) -> tuple[dict[str, TickerSeries], int, int]:
    s = dict(series)
    singleton = s.pop("__meta__singleton_dropped__", 0)  # type: ignore[arg-type]
    nonmono = s.pop("__meta__nonmonotonic_dropped__", 0)  # type: ignore[arg-type]
    return s, singleton, nonmono  # type: ignore[return-value]


# --------------------------------------------------------------------------- #
# Row-level CLV computation -- the general reusable contract
# --------------------------------------------------------------------------- #

def compute_clv_row(
    ticker: str,
    entry_ts: str,
    entry_price: float,
    side: Side,
    size_or_none: float | None,
    series_map: dict[str, TickerSeries],
    *,
    signal: float = 0.0,
    closing_index_from_end: int = 1,
) -> ClvRow:
    """Compute one row's CLV against the loaded price series.

    Input contract: (ticker, entry_ts, entry_price, side, size_or_none).
    `closing_index_from_end=1` -> last observation (primary, pre-reg §2).
    `closing_index_from_end=2` -> second-to-last (robustness variant, §6).

    Raises loudly (never imputes) on:
      TickerNotFoundError      -- ticker absent from series_map
      InvalidSideError         -- side not in {"YES", "NO"}
      InvalidEntryPriceError   -- entry_price None/NaN/<=0/>=1
      NoClosingObservationError -- no observation strictly after entry_ts
                                    at the requested closing_index_from_end
    """
    if side not in ("YES", "NO"):
        raise InvalidSideError(f"side must be YES or NO, got {side!r}")
    if entry_price is None or (isinstance(entry_price, float) and math.isnan(entry_price)):
        raise InvalidEntryPriceError(f"entry_price is None/NaN for {ticker}@{entry_ts}")
    if not (0.0 < entry_price < 1.0):
        raise InvalidEntryPriceError(
            f"entry_price {entry_price} out of (0,1) for {ticker}@{entry_ts}"
        )
    if ticker not in series_map:
        raise TickerNotFoundError(f"ticker {ticker!r} not present in series_map")

    ts_obs = series_map[ticker]
    after = [o for o in ts_obs.observations if o.ts > entry_ts]
    if len(after) < closing_index_from_end:
        raise NoClosingObservationError(
            f"{ticker}@{entry_ts}: no observation at closing_index_from_end="
            f"{closing_index_from_end} (only {len(after)} rows strictly after entry_ts)"
        )
    closing_obs = after[-closing_index_from_end]

    entry_candidates = [o for o in ts_obs.observations if o.ts <= entry_ts]
    entry_mip = entry_candidates[-1].mip if entry_candidates else None
    if entry_mip is None:
        # entry_ts predates this ticker's first observation -- treat the
        # nearest observation at/after entry_ts as the entry reference
        # rather than imputing; if none exists this is unreachable because
        # `after` was already required non-empty above.
        entry_mip = after[0].mip

    side_sign = 1.0 if side == "YES" else -1.0
    closing_mip = closing_obs.mip
    clv = side_sign * (closing_mip - entry_mip)

    open_mip = ts_obs.observations[0].mip
    open_ts = ts_obs.observations[0].ts
    backward_move = side_sign * (entry_mip - open_mip)

    prior = [o for o in ts_obs.observations if o.ts < entry_ts]
    own_dislocation: float | None = None
    if len(prior) >= 3:
        trailing_mean = sum(o.mip for o in prior) / len(prior)
        own_dislocation = entry_mip - trailing_mean

    return ClvRow(
        ticker=ticker,
        game_id=ts_obs.game_id,
        entry_ts=entry_ts,
        entry_price=entry_price,
        entry_mip=entry_mip,
        side=side,
        size=size_or_none,
        closing_ts=closing_obs.ts,
        closing_mip=closing_mip,
        clv=clv,
        backward_ts=open_ts,
        backward_mip=open_mip,
        backward_move=backward_move,
        signal=signal,
        own_dislocation=own_dislocation,
    )


# --------------------------------------------------------------------------- #
# T4-MLB-specific: reconstructing the live pipeline's directional approval
# gate (run_t4_mlb_live.py:1165,1259-1269,1328 -- confirmed this session).
# --------------------------------------------------------------------------- #

def _directional_net_edge(obs: PriceObservation) -> tuple[Side | None, float | None, float | None]:
    """Returns (direction, directional_net_edge, entry_price) or (None, None, None)
    if the row carries no signal (null gross_edge, or gross_edge == 0)."""
    if obs.gross_edge is None or obs.p_t4 is None or obs.vig is None:
        return None, None, None
    mip = obs.mip
    kalshi_fee = KALSHI_FEE_RATE * mip * (1.0 - mip)
    if obs.gross_edge > 0.0:
        direction: Side = "YES"
        directional_gross_edge = obs.gross_edge
    elif obs.gross_edge < 0.0:
        direction = "NO"
        directional_gross_edge = (mip - obs.p_t4) - obs.vig
    else:
        return None, None, None
    directional_net_edge = directional_gross_edge - kalshi_fee
    entry_price = mip if direction == "YES" else (1.0 - mip)
    return direction, directional_net_edge, entry_price


def build_t4mlb_cohorts(
    series_map: dict[str, TickerSeries], *, seed: int = 572
) -> tuple[list[dict], list[dict], dict]:
    """Builds the approvals cohort (§3a) and matched control cohort (§3b).

    Returns (approvals_entries, control_entries, diagnostics) where each
    entry dict has the fields needed to call compute_clv_row: ticker,
    entry_ts, entry_price, side, size_or_none=None, signal.
    Diagnostics records exclusion counts per pre-reg §2/§3's logging
    requirement -- nothing is silently dropped.
    """
    rng = random.Random(seed)
    diag = {
        "tickers_scanned": 0,
        "no_qualifying_row": 0,
        "no_closing_observation_excluded": 0,
        "control_no_candidate_after_fallback": 0,
        "control_bucket_fallback_count": 0,
    }

    def inning_bucket(inning: int | None) -> str:
        if inning is None:
            return "unknown"
        if inning <= 3:
            return "early"
        if inning <= 6:
            return "mid"
        return "late"

    approvals_by_ticker: dict[str, dict] = {}
    for ticker, ts_obs in series_map.items():
        diag["tickers_scanned"] += 1
        qualifying_idx = None
        qualifying_direction = None
        qualifying_edge = None
        qualifying_entry_price = None
        for i, obs in enumerate(ts_obs.observations):
            direction, net_edge, entry_price = _directional_net_edge(obs)
            if direction is None:
                continue
            if net_edge >= MIN_EDGE_TO_APPROVE and entry_price is not None and entry_price > 0.0:
                qualifying_idx = i
                qualifying_direction = direction
                qualifying_edge = net_edge
                qualifying_entry_price = entry_price
                break
        if qualifying_idx is None:
            diag["no_qualifying_row"] += 1
            continue
        entry_obs = ts_obs.observations[qualifying_idx]
        approvals_by_ticker[ticker] = {
            "ticker": ticker,
            "entry_ts": entry_obs.ts,
            "entry_price": qualifying_entry_price,
            "side": qualifying_direction,
            "size_or_none": None,
            "signal": qualifying_edge,
            "entry_index": qualifying_idx,
            "entry_inning_bucket": inning_bucket(entry_obs.inning),
        }

    control_entries: list[dict] = []
    for ticker, entry in approvals_by_ticker.items():
        ts_obs = series_map[ticker]
        n = len(ts_obs.observations)
        entry_idx = entry["entry_index"]
        eligible = [i for i in range(n - 1) if i != entry_idx]
        if not eligible:
            diag["control_no_candidate_after_fallback"] += 1
            continue
        bucket = entry["entry_inning_bucket"]
        same_bucket = [i for i in eligible if inning_bucket(ts_obs.observations[i].inning) == bucket]
        fallback = not bool(same_bucket)
        pool = same_bucket if same_bucket else eligible
        if fallback:
            diag["control_bucket_fallback_count"] += 1
        chosen_idx = rng.choice(pool)
        remaining_pool = list(pool)
        direction = net_edge = entry_price = None
        while remaining_pool:
            direction, net_edge, entry_price = _directional_net_edge(
                ts_obs.observations[chosen_idx]
            )
            if direction is not None:
                break
            remaining_pool.remove(chosen_idx)
            if not remaining_pool:
                break
            chosen_idx = rng.choice(remaining_pool)
        if direction is None:
            diag["control_no_candidate_after_fallback"] += 1
            continue
        chosen_obs = ts_obs.observations[chosen_idx]
        control_entries.append(
            {
                "ticker": ticker,
                "entry_ts": chosen_obs.ts,
                "entry_price": entry_price,
                "side": direction,
                "size_or_none": None,
                "signal": net_edge,
                "bucket_fallback": fallback,
            }
        )

    return list(approvals_by_ticker.values()), control_entries, diag


# --------------------------------------------------------------------------- #
# Cohort aggregation, clustering, bootstrap
# --------------------------------------------------------------------------- #

def rows_from_entries(
    entries: Sequence[dict],
    series_map: dict[str, TickerSeries],
    *,
    closing_index_from_end: int = 1,
) -> tuple[list[ClvRow], dict]:
    rows: list[ClvRow] = []
    excluded: dict[str, int] = defaultdict(int)
    for e in entries:
        try:
            row = compute_clv_row(
                ticker=e["ticker"],
                entry_ts=e["entry_ts"],
                entry_price=e["entry_price"],
                side=e["side"],
                size_or_none=e.get("size_or_none"),
                series_map=series_map,
                signal=e.get("signal", 0.0),
                closing_index_from_end=closing_index_from_end,
            )
        except ClvHarnessError as exc:
            excluded[type(exc).__name__] += 1
            continue
        if e.get("bucket_fallback"):
            row = ClvRow(**{**row.__dict__, "bucket_fallback": True})
        rows.append(row)
    return rows, dict(excluded)


def _block_bootstrap_mean_ci(
    values: Sequence[float], cluster_keys: Sequence[str], *, n_boot: int = N_BOOTSTRAP, seed: int = 1
) -> dict:
    rng = np.random.default_rng(seed)
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for v, k in zip(values, cluster_keys):
        by_cluster[k].append(v)
    clusters = list(by_cluster.keys())
    if not clusters:
        return {"mean": None, "ci_low": None, "ci_high": None, "n_clusters": 0, "n_obs": 0}
    point_mean = float(np.mean(values))
    boot_means = np.empty(n_boot)
    n_clusters = len(clusters)
    for b in range(n_boot):
        sampled = rng.choice(clusters, size=n_clusters, replace=True)
        pooled: list[float] = []
        for c in sampled:
            pooled.extend(by_cluster[c])
        boot_means[b] = np.mean(pooled) if pooled else np.nan
    ci_low, ci_high = np.nanpercentile(boot_means, [2.5, 97.5])
    return {
        "mean": point_mean,
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "n_clusters": n_clusters,
        "n_obs": len(values),
    }


def cohort_aggregate(rows: Sequence[ClvRow]) -> dict:
    """Equal-weighted mean CLV with dual-clustered (by-ticker, by-game)
    block-bootstrap 95% CIs, plus size-weighted variant if any size present.
    """
    if not rows:
        return {
            "n": 0,
            "by_ticker": _block_bootstrap_mean_ci([], []),
            "by_game": _block_bootstrap_mean_ci([], []),
            "size_weighted": None,
        }
    clv_values = [r.clv for r in rows]
    ticker_keys = [r.ticker for r in rows]
    game_keys = [r.game_id for r in rows]
    result = {
        "n": len(rows),
        "by_ticker": _block_bootstrap_mean_ci(clv_values, ticker_keys, seed=1),
        "by_game": _block_bootstrap_mean_ci(clv_values, game_keys, seed=2),
        "size_weighted": None,
    }
    sized = [r for r in rows if r.size is not None]
    if sized:
        w = np.array([r.size for r in sized])
        v = np.array([r.clv for r in sized])
        result["size_weighted"] = {"mean": float(np.sum(w * v) / np.sum(w)), "n": len(sized)}
    return result


def ols_slope_ci(
    y: Sequence[float], x: Sequence[float], cluster_keys: Sequence[str], *, n_boot: int = N_BOOTSTRAP, seed: int = 3
) -> dict:
    """Simple OLS y ~ a + b*x, slope b with cluster-robust block-bootstrap CI."""
    y_arr = np.asarray(y, dtype=float)
    x_arr = np.asarray(x, dtype=float)
    if len(y_arr) < 2 or np.std(x_arr) == 0:
        return {"slope": None, "ci_low": None, "ci_high": None, "n": len(y_arr)}
    slope, intercept = np.polyfit(x_arr, y_arr, 1)

    rng = np.random.default_rng(seed)
    by_cluster: dict[str, list[int]] = defaultdict(list)
    for i, k in enumerate(cluster_keys):
        by_cluster[k].append(i)
    clusters = list(by_cluster.keys())
    boot_slopes = np.empty(n_boot)
    for b in range(n_boot):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        idx: list[int] = []
        for c in sampled:
            idx.extend(by_cluster[c])
        if len(idx) < 2 or np.std(x_arr[idx]) == 0:
            boot_slopes[b] = np.nan
            continue
        s, _ = np.polyfit(x_arr[idx], y_arr[idx], 1)
        boot_slopes[b] = s
    ci_low, ci_high = np.nanpercentile(boot_slopes, [2.5, 97.5])
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "n": len(y_arr),
    }


def multiple_regression_slope_ci(
    y: Sequence[float], x1: Sequence[float], x2: Sequence[float], cluster_keys: Sequence[str],
    *, n_boot: int = N_BOOTSTRAP, seed: int = 4,
) -> dict:
    """OLS y ~ a + b1*x1 + b2*x2, both slopes with cluster-robust CIs."""
    y_arr = np.asarray(y, dtype=float)
    X = np.column_stack([np.ones_like(x1, dtype=float), np.asarray(x1, dtype=float), np.asarray(x2, dtype=float)])

    def fit(idx: np.ndarray) -> tuple[float, float]:
        beta, *_ = np.linalg.lstsq(X[idx], y_arr[idx], rcond=None)
        return float(beta[1]), float(beta[2])

    all_idx = np.arange(len(y_arr))
    b1, b2 = fit(all_idx)

    rng = np.random.default_rng(seed)
    by_cluster: dict[str, list[int]] = defaultdict(list)
    for i, k in enumerate(cluster_keys):
        by_cluster[k].append(i)
    clusters = list(by_cluster.keys())
    boot_b1 = np.empty(n_boot)
    boot_b2 = np.empty(n_boot)
    for b in range(n_boot):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        idx: list[int] = []
        for c in sampled:
            idx.extend(by_cluster[c])
        idx_arr = np.array(idx)
        try:
            boot_b1[b], boot_b2[b] = fit(idx_arr)
        except Exception:
            boot_b1[b], boot_b2[b] = np.nan, np.nan
    return {
        "b1_signal": b1,
        "b1_ci_low": float(np.nanpercentile(boot_b1, 2.5)),
        "b1_ci_high": float(np.nanpercentile(boot_b1, 97.5)),
        "b2_own_dislocation": b2,
        "b2_ci_low": float(np.nanpercentile(boot_b2, 2.5)),
        "b2_ci_high": float(np.nanpercentile(boot_b2, 97.5)),
        "n": len(y_arr),
    }


# --------------------------------------------------------------------------- #
# Confound checks (pre-reg §5) -- mandatory for every reported CLV number
# --------------------------------------------------------------------------- #

def backward_placebo_check(rows: Sequence[ClvRow]) -> dict:
    """§5(b). Forward: CLV ~ signal. Backward: backward_move ~ signal (same
    side-sign convention, same signal). Passes if |backward_slope| < 50% of
    |forward_slope|, OR backward CI includes 0 while forward CI does not.
    """
    if len(rows) < 2:
        return {"passes": None, "reason": "insufficient_n", "n": len(rows)}
    clv = [r.clv for r in rows]
    backward = [r.backward_move for r in rows]
    signal = [r.signal for r in rows]
    tickers = [r.ticker for r in rows]

    forward = ols_slope_ci(clv, signal, tickers, seed=11)
    backward_fit = ols_slope_ci(backward, signal, tickers, seed=12)

    if forward["slope"] is None or backward_fit["slope"] is None:
        return {"passes": None, "reason": "degenerate_regression", "forward": forward, "backward": backward_fit}

    forward_excludes_zero = not (forward["ci_low"] <= 0.0 <= forward["ci_high"])
    backward_includes_zero = backward_fit["ci_low"] <= 0.0 <= backward_fit["ci_high"]
    ratio = (
        abs(backward_fit["slope"]) / abs(forward["slope"])
        if forward["slope"] != 0
        else float("inf")
    )
    passes = (ratio < BACKWARD_PLACEBO_RATIO_THRESHOLD) or (backward_includes_zero and forward_excludes_zero)
    return {
        "passes": bool(passes),
        "ratio": ratio,
        "forward": forward,
        "backward": backward_fit,
        "forward_excludes_zero": forward_excludes_zero,
        "backward_includes_zero": backward_includes_zero,
        "threshold": BACKWARD_PLACEBO_RATIO_THRESHOLD,
    }


def mean_reversion_decomposition(rows: Sequence[ClvRow]) -> dict:
    """§5(a). Three-way OLS: CLV ~ signal + own_dislocation (rows lacking
    own_dislocation -- fewer than 3 prior observations -- are excluded and
    counted).
    """
    usable = [r for r in rows if r.own_dislocation is not None]
    excluded = len(rows) - len(usable)
    if len(usable) < 2:
        return {"passes": None, "reason": "insufficient_n", "n_usable": len(usable), "n_excluded": excluded}
    clv = [r.clv for r in usable]
    signal = [r.signal for r in usable]
    dislocation = [r.own_dislocation for r in usable]
    tickers = [r.ticker for r in usable]
    result = multiple_regression_slope_ci(clv, signal, dislocation, tickers, seed=13)
    signal_survives = not (result["b1_ci_low"] <= 0.0 <= result["b1_ci_high"])
    result["signal_survives_dislocation_control"] = signal_survives
    result["n_excluded_no_prior_history"] = excluded
    return result


# --------------------------------------------------------------------------- #
# Verdict (pre-reg §8) -- mechanical, no post-hoc adjustment
# --------------------------------------------------------------------------- #

def apply_verdict(
    approvals_agg: dict, backward_placebo: dict, mean_reversion: dict
) -> dict:
    n = approvals_agg["n"]
    if n < MIN_QUALIFYING_TICKERS:
        return {"verdict": "INSUFFICIENT_N", "n": n, "floor": MIN_QUALIFYING_TICKERS}

    by_ticker = approvals_agg["by_ticker"]
    ci_low, ci_high = by_ticker["ci_low"], by_ticker["ci_high"]

    if ci_high is not None and ci_high < 0.0:
        return {
            "verdict": "NEGATIVE",
            "reason": "approvals by-ticker CLV CI entirely below 0; NEGATIVE is not "
            "gated on confound survival per pre-reg §8 asymmetric design",
            "ci_low": ci_low,
            "ci_high": ci_high,
        }

    if ci_low is not None and ci_low > 0.0:
        backward_ok = backward_placebo.get("passes") is True
        reversion_ok = mean_reversion.get("signal_survives_dislocation_control") is True
        if backward_ok and reversion_ok:
            return {
                "verdict": "POSITIVE",
                "reason": "approvals by-ticker CLV CI entirely above 0 AND both "
                "confound checks passed (higher bar per pre-reg §8 asymmetric design)",
                "ci_low": ci_low,
                "ci_high": ci_high,
            }
        return {
            "verdict": "INCONCLUSIVE",
            "reason": "positive point estimate but failed to clear confound gate "
            f"(backward_placebo_passes={backward_placebo.get('passes')}, "
            f"signal_survives_dislocation_control={mean_reversion.get('signal_survives_dislocation_control')})",
            "ci_low": ci_low,
            "ci_high": ci_high,
        }

    return {
        "verdict": "INCONCLUSIVE",
        "reason": "approvals by-ticker CLV CI spans 0",
        "ci_low": ci_low,
        "ci_high": ci_high,
    }


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def run_t4mlb_clv_analysis(cycle_log_path: str | Path) -> dict:
    series_map, singleton_dropped, nonmonotonic_dropped = _pop_meta(load_ticker_series(cycle_log_path))

    approvals_entries, control_entries, cohort_diag = build_t4mlb_cohorts(series_map)

    approvals_rows, approvals_excluded = rows_from_entries(approvals_entries, series_map, closing_index_from_end=1)
    control_rows, control_excluded = rows_from_entries(control_entries, series_map, closing_index_from_end=1)
    approvals_rows_r2, approvals_excluded_r2 = rows_from_entries(approvals_entries, series_map, closing_index_from_end=2)
    control_rows_r2, control_excluded_r2 = rows_from_entries(control_entries, series_map, closing_index_from_end=2)

    approvals_agg = cohort_aggregate(approvals_rows)
    control_agg = cohort_aggregate(control_rows)
    approvals_agg_r2 = cohort_aggregate(approvals_rows_r2)
    control_agg_r2 = cohort_aggregate(control_rows_r2)

    # paired difference (approvals - control), matched by ticker, dual-clustered
    control_by_ticker = {r.ticker: r for r in control_rows}
    paired_diff = [
        (r.ticker, r.game_id, r.clv - control_by_ticker[r.ticker].clv)
        for r in approvals_rows
        if r.ticker in control_by_ticker
    ]
    diff_values = [d[2] for d in paired_diff]
    diff_ticker_keys = [d[0] for d in paired_diff]
    diff_game_keys = [d[1] for d in paired_diff]
    difference_agg = {
        "n": len(paired_diff),
        "by_ticker": _block_bootstrap_mean_ci(diff_values, diff_ticker_keys, seed=21),
        "by_game": _block_bootstrap_mean_ci(diff_values, diff_game_keys, seed=22),
    }

    backward_placebo = backward_placebo_check(approvals_rows)
    mean_reversion = mean_reversion_decomposition(approvals_rows)

    verdict = apply_verdict(approvals_agg, backward_placebo, mean_reversion)

    return {
        "instrument": "T-572 CLV harness",
        "preregistration": "05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T572_clv_harness_PREREGISTRATION.md",
        "data_prep": {
            "singleton_tickers_dropped": singleton_dropped,
            "nonmonotonic_rows_dropped": nonmonotonic_dropped,
            "usable_tickers": len([k for k in series_map]),
        },
        "cohort_construction_diagnostics": cohort_diag,
        "approvals": {
            "n_entries": len(approvals_entries),
            "n_rows_computed": len(approvals_rows),
            "excluded": approvals_excluded,
            "aggregate": approvals_agg,
        },
        "control": {
            "n_entries": len(control_entries),
            "n_rows_computed": len(control_rows),
            "excluded": control_excluded,
            "aggregate": control_agg,
        },
        "difference_approvals_minus_control_paired_by_ticker": difference_agg,
        "robustness_second_to_last_closing_row": {
            "approvals": {
                "n_rows_computed": len(approvals_rows_r2),
                "excluded": approvals_excluded_r2,
                "aggregate": approvals_agg_r2,
            },
            "control": {
                "n_rows_computed": len(control_rows_r2),
                "excluded": control_excluded_r2,
                "aggregate": control_agg_r2,
            },
        },
        "confounds": {
            "backward_placebo": backward_placebo,
            "mean_reversion_decomposition": mean_reversion,
        },
        "verdict": verdict,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycle-log", required=True, help="Path to t4_mlb_cycle_log.jsonl")
    parser.add_argument("--out", required=True, help="Path to write JSON results")
    args = parser.parse_args()

    result = run_t4mlb_clv_analysis(args.cycle_log)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    v = result["verdict"]
    print(f"VERDICT: {v['verdict']} -- {v.get('reason', '')}")
    print(f"Approvals n={result['approvals']['n_rows_computed']}  Control n={result['control']['n_rows_computed']}")
    print(f"Approvals CLV (by-ticker): {result['approvals']['aggregate']['by_ticker']}")
    print(f"Control CLV (by-ticker):   {result['control']['aggregate']['by_ticker']}")
    print(f"Backward placebo ratio: {result['confounds']['backward_placebo'].get('ratio')}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
