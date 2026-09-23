#!/usr/bin/env python3
"""T-565: reproduce/extend the T4M-PROJ model-vs-market calibration benchmark.

Reproduces the CLAIM figures from the LIVE VPS ledger (not the local mirror),
per the pre-registered criteria in
05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T565_PREREGISTRATION_calibration_model_vs_market.md.

Read-only: loads a portfolio JSON snapshot already pulled from the VPS via scp.
Does not touch kelly_fraction, sizing, or any production file.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from prediction_market_bot import logic_epoch as le  # noqa: E402
from prediction_market_bot.c5_execution.market_type_registry import MarketType  # noqa: E402
from prediction_market_bot.c7_monitoring.monitor import (  # noqa: E402
    ForecastOutcomeRecord,
    _compute_brier,
    _compute_ece,
)

MARKET_TYPE_FOR_BAND_PREFIX = {
    # band -> MarketType, for the cell-aware clean check where unambiguous.
    "T4M-PROJ": MarketType.MLB_PLAYER_PROP_HITS,
    "T1": MarketType.MLB_PLAYER_PROP_HITS,
    "T2": MarketType.MLB_PLAYER_PROP_HITS,
    "T3": MarketType.MLB_PLAYER_PROP_HITS,
}


@dataclass
class Row:
    band: str
    logic_epoch: int | None
    game_date: str
    model_p: float
    market_price: float
    y: int
    outcome_label: str
    pnl: float


def load_portfolio(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def build_rows(closed_positions: list[dict]) -> list[Row]:
    rows = []
    skipped_missing_field = 0
    for p in closed_positions:
        try:
            actual_hits = p["actual_hits"]
            threshold = p["kalshi_threshold"]
            model_p = p["model_p"]
            market_price = p["mid_price_at_entry"]
            band = p["band"]
            game_date = p["game_date"]
            outcome_label = p["outcome"]
            pnl = p["pnl"]
        except KeyError:
            skipped_missing_field += 1
            continue
        y = 1 if actual_hits >= threshold else 0
        rows.append(
            Row(
                band=band,
                logic_epoch=p.get("logic_epoch"),
                game_date=game_date,
                model_p=float(model_p),
                market_price=float(market_price),
                y=y,
                outcome_label=outcome_label,
                pnl=float(pnl),
            )
        )
    if skipped_missing_field:
        print(f"[warn] {skipped_missing_field} closed rows skipped: missing required field", file=sys.stderr)
    return rows


def clean_filter(rows: list[Row], band: str) -> list[Row]:
    return [r for r in rows if r.band == band and le.is_clean_for_band(r.logic_epoch, band)]


def paired_bet_level(rows: list[Row]) -> dict:
    diffs = [
        (r.model_p - r.y) ** 2 - (r.market_price - r.y) ** 2
        for r in rows
    ]
    n = len(diffs)
    mean_diff = sum(diffs) / n
    var = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
    se = math.sqrt(var / n)
    t = mean_diff / se if se > 0 else float("nan")
    return {"n": n, "mean_diff": mean_diff, "se": se, "t": t, "df": n - 1}


def paired_day_clustered(rows: list[Row]) -> dict:
    by_day: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        d = (r.model_p - r.y) ** 2 - (r.market_price - r.y) ** 2
        by_day[r.game_date].append(d)
    day_means = [sum(v) / len(v) for v in by_day.values()]
    n_days = len(day_means)
    mean_of_days = sum(day_means) / n_days
    var = sum((d - mean_of_days) ** 2 for d in day_means) / (n_days - 1)
    se = math.sqrt(var / n_days)
    t = mean_of_days / se if se > 0 else float("nan")
    return {
        "n_days": n_days,
        "mean_diff": mean_of_days,
        "se": se,
        "t": t,
        "df": n_days - 1,
        "day_span_min": min(by_day) if by_day else None,
        "day_span_max": max(by_day) if by_day else None,
    }


def cohort_summary(rows: list[Row], label: str) -> dict:
    if not rows:
        return {"label": label, "n": 0}
    records = [ForecastOutcomeRecord(p_estimate=r.model_p, outcome=r.y, market_implied_prob=r.market_price) for r in rows]
    market_records = [ForecastOutcomeRecord(p_estimate=r.market_price, outcome=r.y, market_implied_prob=r.market_price) for r in rows]
    model_brier = _compute_brier(records)
    model_ece = _compute_ece(records)
    market_brier = _compute_brier(market_records)
    base_rate = sum(r.y for r in rows) / len(rows)
    mean_model_p = sum(r.model_p for r in rows) / len(rows)
    climatology_brier = base_rate * (1 - base_rate)
    skill = 1 - model_brier / climatology_brier if climatology_brier > 0 else float("nan")
    bet_level = paired_bet_level(rows)
    day_clustered = paired_day_clustered(rows)
    total_pnl = sum(r.pnl for r in rows)
    n_wins = sum(1 for r in rows if r.outcome_label == "WIN")
    win_rate = n_wins / len(rows)
    game_dates = sorted({r.game_date for r in rows})

    return {
        "label": label,
        "n": len(rows),
        "n_game_days": len(game_dates),
        "game_date_min": game_dates[0] if game_dates else None,
        "game_date_max": game_dates[-1] if game_dates else None,
        "model_brier": model_brier,
        "model_ece": model_ece,
        "market_brier": market_brier,
        "base_rate": base_rate,
        "mean_model_p": mean_model_p,
        "skill_vs_climatology": skill,
        "paired_bet_level": bet_level,
        "paired_day_clustered": day_clustered,
        "total_pnl": total_pnl,
        "pnl_per_bet": total_pnl / len(rows),
        "win_rate": win_rate,
    }


def print_summary(s: dict) -> None:
    if s["n"] == 0:
        print(f"{s['label']}: n=0, skipped")
        return
    print(f"--- {s['label']} ---")
    print(f"n={s['n']}  n_game_days={s['n_game_days']}  span={s['game_date_min']}..{s['game_date_max']}")
    print(f"model_brier={s['model_brier']:.4f}  model_ece={s['model_ece']:.4f}")
    print(f"base_rate={s['base_rate']:.4f}  mean_model_p={s['mean_model_p']:.4f}  skill={s['skill_vs_climatology']:.3f}")
    print(f"market_brier={s['market_brier']:.4f}")
    bl = s["paired_bet_level"]
    print(f"paired(bet-level): diff={bl['mean_diff']:+.4f} se={bl['se']:.4f} t={bl['t']:.2f} df={bl['df']}")
    dc = s["paired_day_clustered"]
    print(f"paired(day-clustered): diff={dc['mean_diff']:+.4f} se={dc['se']:.4f} t={dc['t']:.2f} df={dc['df']} n_days={dc['n_days']}")
    print(f"pnl_total={s['total_pnl']:+.2f}  pnl_per_bet={s['pnl_per_bet']:+.4f}  win_rate={s['win_rate']:.3f}")
    print()


MLB_PORTFOLIO_FILES = [
    "paper_portfolio_mlb_t4.LIVE.20260922.json",   # T4M-PROJ (and 365 pre-band-tracking rows)
    "paper_portfolio_mlb.LIVE.20260922.json",       # T1 / T2 (raw_n=2, below MIN_N)
]


def main() -> None:
    out_dir = REPO_ROOT / "exp_output" / "T565_calibration_benchmark"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[Row] = []
    results = {}
    diagnostics = {"portfolios": [], "excluded_no_band": {}, "excluded_no_hits_field": {}}

    for fname in MLB_PORTFOLIO_FILES:
        path = out_dir / fname
        portfolio = load_portfolio(path)
        n_closed = len(portfolio.get("closed_positions", []))
        n_rejected = len(portfolio.get("rejected_positions", []))
        print(f"portfolio file: {fname}")
        print(f"  last_updated={portfolio.get('last_updated')}  closed={n_closed}  rejected={n_rejected}")
        diagnostics["portfolios"].append(
            {"file": fname, "last_updated": portfolio.get("last_updated"), "closed": n_closed, "rejected": n_rejected}
        )
        file_rows = build_rows(portfolio.get("closed_positions", []))
        rows.extend(file_rows)
        n_no_band = sum(1 for p in portfolio.get("closed_positions", []) if p.get("band") is None)
        diagnostics["excluded_no_band"][fname] = n_no_band
        if fname == MLB_PORTFOLIO_FILES[0]:
            rejected_raw = portfolio.get("rejected_positions", [])
    print()

    # --- Deliverable 2: primary claim reproduction, T4M-PROJ clean cohort ---
    t4mproj_clean = clean_filter(rows, "T4M-PROJ")
    primary = cohort_summary(t4mproj_clean, "T4M-PROJ clean (Deliverable 2 primary)")
    print_summary(primary)
    results["deliverable_2_primary"] = primary

    # --- Deliverable 4: per-(market_type-implied band) extension, MIN_N=30 ---
    # NOTE: only bands present in a closed_positions row's `band` field can be
    # clean-filtered via is_clean_for_band(); rows with band absent entirely
    # (365 in the T4 file, all NBA rows in paper_portfolio.json) are excluded
    # here and reported separately in diagnostics -- not assigned a band.
    MIN_N = 30
    all_bands = sorted({r.band for r in rows})
    cell_table = []
    for band in all_bands:
        band_clean = clean_filter(rows, band)
        if len(band_clean) < MIN_N:
            cell_table.append({"band": band, "clean_n": len(band_clean), "status": "OMITTED_BELOW_MIN_N"})
            continue
        s = cohort_summary(band_clean, f"band={band} clean")
        cell_table.append({"band": band, "clean_n": len(band_clean), "status": "COMPUTED", "summary": s})
        print_summary(s)
    results["deliverable_4_cell_table"] = cell_table

    # --- Deliverable 4: rejected_positions cohort ---
    # rejected_positions rows structurally lack actual_hits/outcome/pnl (never
    # placed -> never resolved). build_rows() therefore returns an empty list
    # for them; this is reported as a finding (unscorable), not routed around.
    rej_rows = build_rows(rejected_raw)
    rej_summary = cohort_summary(rej_rows, "rejected_positions (all, no clean filter)")
    print_summary(rej_summary)
    results["deliverable_4_rejected_cohort"] = rej_summary
    results["diagnostics"] = diagnostics

    out_path = out_dir / "t565_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
