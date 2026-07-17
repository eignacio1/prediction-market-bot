"""
EXP-017: EV Validation Against Actual Kalshi Market Prices
===========================================================
Experiment ID:   EXP-017
Phase:           Phase 6 (G6 blocker — live capital evidence)
Hypothesis:      OQ-023 — does the model generate positive EV against actual
                 Kalshi market prices, not a 0.50 null baseline?
Governance gap:  GG-004 (OPEN) — until this runs, commercial case is unproven
Known issue:     KI-017 — all prior EV figures used market_implied_prob=0.50
Blocks gate:     G6 (ADR-0005 live capital authorization)

Background:
    Every prior EV figure (+$0.0958/bet, +$0.0855/bet) was computed using
    market_implied_prob = 0.50 — a coin flip, not an informed market.
    This experiment replaces 0.50 with actual Kalshi mid-prices to answer
    the real commercial question: does the model beat professional market
    makers who have injury data, advanced stats, and betting flow?

Part A — Sensitivity analysis (RUNS NOW, no Kalshi data required):
    Sweep market_implied_prob from 0.40 to 0.60.
    Shows at what market price level the model's edge disappears.
    Answers: how efficiently priced would Kalshi need to be to eliminate edge?

Part B — Historical price validation (REQUIRES kalshi_prices.csv):
    Load actual Kalshi mid-prices for TEST-period player/game/threshold combos.
    Compute: model_p - kalshi_mid_price for each matched row.
    Report: mean EV, % bets still passing MIN_EDGE, win rate.
    This is the definitive commercial case answer.

Data requirements:
    Part A: exp_output/EXP-005/EXP-005_feature_matrix.csv
            exp_output/EXP-005/EXP-005_forecast_test.csv
    Part B: exp_output/EXP-017/kalshi_prices.csv (operator must provide — see below)

Kalshi prices CSV format (Part B):
    Required columns:
        player_id       int    (NBA player_id — same as feature matrix)
        game_date       str    (YYYY-MM-DD)
        kalshi_threshold int   (discrete threshold from KXNBAPTS ticker)
        kalshi_mid_price float  (mid-price at time of bet: (ask+bid)/2)
        kalshi_vig      float  (spread: ask - bid)
    Optional:
        kalshi_ticker   str    (full ticker, e.g. KXNBAPTS-25NOV18LAL-JAMESLE-20)

    How to collect (options in priority order):
        1. Kalshi API: GET /trade-api/v2/markets?series_ticker=KXNBAPTS&closed=true
           Filter by game dates in TEST period (2025-04-14 to present). Requires VENUE_API_KEY.
        2. EXP-004 Part B output: if run previously, extract from EXP-004/EXP-004_results.json
        3. Paper portfolio logs: extract actual mid_price_at_entry from paper_portfolio.json

    Matching logic: EXP-017 matches kalshi_threshold to pts_l10_mean (rolling average)
    per player. Only rows where abs(kalshi_threshold - pts_l10_mean) <= 3 are included.
    This ensures we're comparing model predictions to the right market.

How to run:
    # Part A only (no Kalshi data needed):
    PYTHONPATH=src python3 src/prediction_market_bot/run_exp017.py

    # Part A + Part B (requires kalshi_prices.csv):
    PYTHONPATH=src python3 src/prediction_market_bot/run_exp017.py \\
        --kalshi-prices exp_output/EXP-017/kalshi_prices.csv

Security (NFR-05):
    No API keys required unless operator adds Part B live-fetch.
    No order placement. BOT_C4_ACTIVE must NOT be set.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from typing import Any

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

EXP_ID = "EXP-017"
SESSION_ID = f"EXP-017-{uuid.uuid4().hex[:8].upper()}"

FEATURE_CSV  = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
FORECAST_CSV = Path("exp_output/EXP-005/EXP-005_forecast_test.csv")
OUTPUT_DIR   = Path("exp_output/EXP-017")

# ADR-0004 / risk.py thresholds
MIN_EDGE_TO_APPROVE    = 0.02
FEATURE_WINDOW         = 10
THRESHOLD_MATCH_MARGIN = 3   # abs(kalshi_threshold - pts_l10_mean) <= 3 to be included

# Measured vig from 37 live KXNBAPTS markets on 2026-05-28 (OKC-SAS game)
MEASURED_VIG_20260528  = 0.01

# Sensitivity sweep: market_implied_prob values to test in Part A
SENSITIVITY_SWEEP = [0.40, 0.43, 0.45, 0.47, 0.49, 0.50, 0.51, 0.52, 0.53, 0.55, 0.57, 0.60]


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _load_test_dataset() -> pd.DataFrame:
    """
    Load and merge EXP-005 feature matrix + forecast test CSV.

    Returns merged DataFrame with columns:
        player_id, player_name, game_date, pts_l10_mean,
        y_target, p_estimate, train_test_label
    """
    if not FEATURE_CSV.exists():
        print(f"ERROR: Feature matrix not found: {FEATURE_CSV}", file=sys.stderr)
        sys.exit(1)
    if not FORECAST_CSV.exists():
        print(f"ERROR: Forecast test CSV not found: {FORECAST_CSV}", file=sys.stderr)
        sys.exit(1)

    feat = pd.read_csv(FEATURE_CSV)
    fcast = pd.read_csv(FORECAST_CSV)

    # Build actual outcome column from feature matrix
    feat["pts"] = pd.to_numeric(feat["pts"], errors="coerce")
    feat[f"pts_l{FEATURE_WINDOW}_mean"] = pd.to_numeric(
        feat[f"pts_l{FEATURE_WINDOW}_mean"], errors="coerce"
    )
    feat["y_target"] = (
        (feat["pts"] >= feat[f"pts_l{FEATURE_WINDOW}_mean"])
        .where(feat["pts"].notna() & feat[f"pts_l{FEATURE_WINDOW}_mean"].notna())
        .astype("Int8")
    )

    # Keep only TEST rows with valid targets and temporal integrity
    test_feat = feat[
        (feat["train_test_label"] == "TEST")
        & feat["y_target"].notna()
        & feat["temporal_cutoff"].notna()
    ].copy()

    # Normalize merge keys
    test_feat["player_id"] = pd.to_numeric(test_feat["player_id"], errors="coerce")
    test_feat["game_date"]  = test_feat["game_date"].astype(str)

    fcast["player_id"] = pd.to_numeric(fcast["player_id"], errors="coerce")
    fcast["game_date"]  = fcast["game_date"].astype(str)

    # Merge on player_id + game_date (both exist in forecast CSV)
    merged = test_feat.merge(
        fcast[["player_id", "game_date", "p_estimate"]],
        on=["player_id", "game_date"],
        how="inner",
    )

    # Deduplicate (each player/game should have one prediction)
    merged = merged.drop_duplicates(subset=["player_id", "game_date"])
    return merged


def _load_kalshi_prices(csv_path: Path) -> pd.DataFrame | None:
    """Load operator-provided Kalshi historical prices CSV."""
    if not csv_path.exists():
        return None

    required = {"player_id", "game_date", "kalshi_threshold", "kalshi_mid_price"}
    df = pd.read_csv(csv_path)
    missing = required - set(df.columns)
    if missing:
        print(f"ERROR: kalshi_prices.csv is missing columns: {missing}", file=sys.stderr)
        print(f"  Required: {required}", file=sys.stderr)
        return None

    df["player_id"]         = pd.to_numeric(df["player_id"], errors="coerce")
    df["game_date"]         = df["game_date"].astype(str)
    df["kalshi_threshold"]  = pd.to_numeric(df["kalshi_threshold"], errors="coerce")
    df["kalshi_mid_price"]  = pd.to_numeric(df["kalshi_mid_price"], errors="coerce")
    df["kalshi_vig"]        = pd.to_numeric(df.get("kalshi_vig", MEASURED_VIG_20260528),
                                             errors="coerce").fillna(MEASURED_VIG_20260528)
    return df.dropna(subset=required)


# ---------------------------------------------------------------------------
# Part A: Sensitivity sweep
# ---------------------------------------------------------------------------

def run_part_a(df: pd.DataFrame) -> dict[str, Any]:
    """
    Sweep market_implied_prob from 0.40 to 0.60.

    For each assumed market price, compute:
    - Fraction of TEST rows where edge = p_estimate - mip > MIN_EDGE_TO_APPROVE
    - Mean EV per bet (flat $1 stake, measured vig applied)
    - Win rate on those bets

    The sweep shows at what market efficiency the model's edge disappears.
    """
    print("\n" + "=" * 65)
    print("PART A — Sensitivity Sweep (no Kalshi price data required)")
    print("=" * 65)
    print(f"TEST rows: {len(df):,}  |  MIN_EDGE: {MIN_EDGE_TO_APPROVE}  |  VIG: {MEASURED_VIG_20260528}")
    print(f"\n{'MIP':>6} {'Bets YES':>9} {'Bets NO':>9} {'Bets PASS':>10} "
          f"{'Win%':>7} {'EV/bet':>9} {'Total P&L':>11}")
    print("-" * 65)

    p_est = df["p_estimate"].to_numpy(dtype=float)
    y     = df["y_target"].astype(int).to_numpy()
    half_spread = MEASURED_VIG_20260528 / 2.0

    rows = []
    for mip in SENSITIVITY_SWEEP:
        edge      = p_est - mip
        yes_bets  = edge > (MIN_EDGE_TO_APPROVE + half_spread)
        no_bets   = edge < -(MIN_EDGE_TO_APPROVE + half_spread)

        n_yes  = int(yes_bets.sum())
        n_no   = int(no_bets.sum())
        n_pass = len(p_est) - n_yes - n_no
        n_bets = n_yes + n_no

        yes_ask = mip + half_spread
        no_ask  = (1.0 - mip) + half_spread

        pnl_yes = np.where(yes_bets, np.where(y == 1, 1.0 - yes_ask, -yes_ask), 0.0)
        pnl_no  = np.where(no_bets,  np.where(y == 0, 1.0 - no_ask,  -no_ask),  0.0)
        total_pnl = float((pnl_yes + pnl_no).sum())
        ev_per_bet = total_pnl / n_bets if n_bets > 0 else 0.0

        win_yes = int((yes_bets & (y == 1)).sum())
        win_no  = int((no_bets  & (y == 0)).sum())
        win_rate = (win_yes + win_no) / n_bets if n_bets > 0 else 0.0

        marker = " ◄ (null/EV-004)" if mip == 0.50 else ""
        print(f"{mip:>6.2f} {n_yes:>9,} {n_no:>9,} {n_pass:>10,} "
              f"{win_rate:>6.1%} {ev_per_bet:>+9.4f} {total_pnl:>+11.2f}{marker}")

        rows.append({
            "market_implied_prob": mip,
            "n_yes_bets":  n_yes,
            "n_no_bets":   n_no,
            "n_pass":      n_pass,
            "n_bets":      n_bets,
            "win_rate":    round(win_rate, 4),
            "ev_per_bet":  round(ev_per_bet, 6),
            "total_pnl":   round(total_pnl, 4),
        })

    # Find break-even MIP (where EV flips negative)
    ev_at_050 = next((r["ev_per_bet"] for r in rows if r["market_implied_prob"] == 0.50), None)
    positive_mips = [r["market_implied_prob"] for r in rows if r["ev_per_bet"] > 0]
    breakeven_upper = max(positive_mips) if positive_mips else None

    print(f"\nSummary:")
    print(f"  EV at null (MIP=0.50): {ev_at_050:+.4f}/bet")
    if breakeven_upper is not None:
        print(f"  Model edge is positive at all tested MIP values up to {breakeven_upper:.2f}")
        print(f"  Interpretation: Kalshi prices would need to exceed {breakeven_upper:.2f} "
              f"to eliminate model edge entirely")
    else:
        print(f"  Model edge is negative at all tested MIP levels — edge is structurally weak")

    print(f"\n  Commercial question (OQ-023): still open — sensitivity shows directional range,")
    print(f"  but actual Kalshi prices are required for a definitive answer (Part B).")

    return {
        "part": "A",
        "test_rows":      len(df),
        "vig_assumed":    MEASURED_VIG_20260528,
        "sweep_results":  rows,
        "ev_at_null_050": ev_at_050,
        "breakeven_upper_mip": breakeven_upper,
        "conclusion":     "Sensitivity complete — provides directional answer but not commercial validation",
    }


# ---------------------------------------------------------------------------
# Part B: Historical Kalshi price validation
# ---------------------------------------------------------------------------

def run_part_b(df: pd.DataFrame, prices: pd.DataFrame) -> dict[str, Any]:
    """
    For each TEST row with a matched Kalshi price, compute:
        edge_vs_market = p_estimate - kalshi_mid_price

    Match logic:
        inner join on player_id + game_date
        filter: abs(kalshi_threshold - pts_l10_mean) <= THRESHOLD_MATCH_MARGIN
        this ensures we're comparing the model prediction to the right market

    Reports:
        - Distribution of edge_vs_market vs edge_vs_null
        - Fraction still passing MIN_EDGE gate vs actual prices
        - Mean EV, win rate on market-benchmarked bets
        - Injury-filtered result (exclude rows where model vs market > 0.25 gap)
    """
    print("\n" + "=" * 65)
    print("PART B — Historical Kalshi Price Validation")
    print("=" * 65)
    print(f"Kalshi price rows loaded: {len(prices):,}")

    # Join
    joined = df.merge(
        prices[["player_id", "game_date", "kalshi_threshold",
                "kalshi_mid_price", "kalshi_vig"]],
        on=["player_id", "game_date"],
        how="inner",
    )
    print(f"Rows after join (player_id + game_date): {len(joined):,}")

    if joined.empty:
        print("  WARNING: No rows matched after join. Check that player_id and game_date "
              "formats are identical between the feature matrix and kalshi_prices.csv.")
        return {"part": "B", "status": "NO_MATCHES", "matched_rows": 0}

    # Threshold matching filter
    pts_col = f"pts_l{FEATURE_WINDOW}_mean"
    joined["threshold_delta"] = (joined["kalshi_threshold"] - joined[pts_col]).abs()
    matched = joined[joined["threshold_delta"] <= THRESHOLD_MATCH_MARGIN].copy()
    print(f"Rows after threshold match (|kalshi_threshold - pts_l10_mean| ≤ {THRESHOLD_MATCH_MARGIN}): {len(matched):,}")

    if matched.empty:
        print(f"  WARNING: No rows passed threshold match filter. "
              f"Consider increasing THRESHOLD_MATCH_MARGIN (currently {THRESHOLD_MATCH_MARGIN}).")
        return {"part": "B", "status": "NO_THRESHOLD_MATCHES", "matched_rows": 0}

    # Injury filter: rows where |model_p - kalshi_mid| > 0.25 are likely injury-priced
    matched["injury_suspect"] = (matched["p_estimate"] - matched["kalshi_mid_price"]).abs() > 0.25
    n_injury = int(matched["injury_suspect"].sum())

    def _analyze(subset: pd.DataFrame, label: str) -> dict[str, Any]:
        p_est = subset["p_estimate"].to_numpy(dtype=float)
        mip   = subset["kalshi_mid_price"].to_numpy(dtype=float)
        vig   = subset["kalshi_vig"].to_numpy(dtype=float)
        y     = subset["y_target"].astype(int).to_numpy()
        half_spread = vig / 2.0

        edge_vs_market = p_est - mip
        edge_vs_null   = p_est - 0.50

        yes_bets = edge_vs_market > (MIN_EDGE_TO_APPROVE + half_spread)
        no_bets  = edge_vs_market < -(MIN_EDGE_TO_APPROVE + half_spread)
        n_yes = int(yes_bets.sum())
        n_no  = int(no_bets.sum())
        n_bets = n_yes + n_no

        yes_ask = mip + half_spread
        no_ask  = (1.0 - mip) + half_spread

        pnl_yes = np.where(yes_bets, np.where(y == 1, 1.0 - yes_ask, -yes_ask), 0.0)
        pnl_no  = np.where(no_bets,  np.where(y == 0, 1.0 - no_ask,  -no_ask),  0.0)
        total_pnl  = float((pnl_yes + pnl_no).sum())
        ev_per_bet = total_pnl / n_bets if n_bets > 0 else 0.0

        win_yes  = int((yes_bets & (y == 1)).sum())
        win_no   = int((no_bets  & (y == 0)).sum())
        win_rate = (win_yes + win_no) / n_bets if n_bets > 0 else 0.0

        # Fraction of bets passing vs null that still pass vs market
        yes_null = (edge_vs_null > (MIN_EDGE_TO_APPROVE + half_spread))
        no_null  = (edge_vs_null < -(MIN_EDGE_TO_APPROVE + half_spread))
        n_bets_null = int(yes_null.sum()) + int(no_null.sum())
        pct_retained = n_bets / n_bets_null if n_bets_null > 0 else 0.0

        print(f"\n  [{label}]")
        print(f"  Rows: {len(subset):,}  |  YES bets: {n_yes:,}  NO bets: {n_no:,}  PASS: {len(subset)-n_bets:,}")
        print(f"  Bets passing vs null: {n_bets_null:,}  |  Retained vs market: {pct_retained:.1%}")
        print(f"  Win rate: {win_rate:.1%}  (YES wins: {win_yes}/{n_yes}, NO wins: {win_no}/{n_no})")
        print(f"  EV per bet vs market: {ev_per_bet:+.4f}")
        print(f"  Total P&L: {total_pnl:+.2f}")

        mean_edge_vs_market = float(np.mean(edge_vs_market))
        mean_edge_vs_null   = float(np.mean(edge_vs_null))
        print(f"  Mean edge vs market: {mean_edge_vs_market:+.4f}  (vs null: {mean_edge_vs_null:+.4f})")

        if n_bets == 0:
            verdict = "NO_BETS"
        elif ev_per_bet > 0:
            verdict = "POSITIVE_EV"
        else:
            verdict = "NEGATIVE_EV"

        print(f"  Verdict: {verdict}")

        return {
            "label":            label,
            "n_rows":           len(subset),
            "n_yes_bets":       n_yes,
            "n_no_bets":        n_no,
            "n_bets_vs_market": n_bets,
            "n_bets_vs_null":   n_bets_null,
            "pct_bets_retained": round(pct_retained, 4),
            "win_rate":         round(win_rate, 4),
            "ev_per_bet":       round(ev_per_bet, 6),
            "total_pnl":        round(total_pnl, 4),
            "mean_edge_vs_market": round(mean_edge_vs_market, 4),
            "mean_edge_vs_null":   round(mean_edge_vs_null, 4),
            "verdict":          verdict,
        }

    raw_result      = _analyze(matched, "RAW (all matched rows)")
    filtered        = matched[~matched["injury_suspect"]].copy()
    filtered_result = _analyze(filtered, f"INJURY-FILTERED ({n_injury} suspect rows removed)")

    # OQ-023 / GG-004 verdict
    print(f"\n  GG-004 / OQ-023 VERDICT:")
    if raw_result["verdict"] == "POSITIVE_EV" and filtered_result["verdict"] == "POSITIVE_EV":
        verdict = "CONFIRMED — model generates positive EV vs actual Kalshi prices"
    elif filtered_result["verdict"] == "POSITIVE_EV":
        verdict = "CONDITIONAL — positive EV in injury-filtered set; raw set negative (injury pricing effect)"
    elif raw_result["verdict"] == "NO_BETS" or filtered_result["verdict"] == "NO_BETS":
        verdict = "INCONCLUSIVE — insufficient bets passed MIN_EDGE gate vs actual prices"
    else:
        verdict = ("NEGATIVE — model does NOT generate positive EV vs actual Kalshi prices. "
                   "G6 EV evidence is unavailable; paper P&L is the only commercial argument.")
    print(f"  {verdict}")

    return {
        "part":            "B",
        "matched_rows":    len(matched),
        "injury_suspect":  n_injury,
        "raw":             raw_result,
        "injury_filtered": filtered_result,
        "verdict":         verdict,
    }


# ---------------------------------------------------------------------------
# Part B (Live): Pre-game log + portfolio EV validation
# ---------------------------------------------------------------------------

def _load_pregame_forecasts(pregame_dir: Path) -> pd.DataFrame:
    """Load pregame_YYYYMMDD.json files from dir. Deduplicates by kalshi_ticker,
    keeping the earliest capture (T1 night-before window)."""
    records = []
    for f in sorted(pregame_dir.glob("pregame_*.json")):
        try:
            data = json.loads(f.read_text())
            for fc in data.get("forecasts", []):
                fc["source_file"] = f.name
                records.append(fc)
        except Exception as e:
            print(f"  WARNING: skipping {f.name}: {e}", file=sys.stderr)
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df["forecast_at"] = pd.to_datetime(df["forecast_at"], utc=True)
    # keep earliest capture per market (T1 = night before, lowest forecast_at)
    df = df.sort_values("forecast_at").drop_duplicates(subset="kalshi_ticker", keep="first")
    return df.reset_index(drop=True)


def _load_portfolio_outcomes(portfolio_path: Path) -> pd.DataFrame:
    """Load closed_positions from portfolio JSON. Adds y_target (1=YES outcome)."""
    data = json.loads(portfolio_path.read_text())
    positions = data.get("closed_positions", [])
    if not positions:
        return pd.DataFrame()
    df = pd.DataFrame(positions)
    df["actual_pts"]      = pd.to_numeric(df["actual_pts"], errors="coerce")
    df["kalshi_threshold"] = pd.to_numeric(df["kalshi_threshold"], errors="coerce")
    # y_target=1 if YES outcome (actual_pts >= threshold)
    df["y_target"] = (df["actual_pts"] >= df["kalshi_threshold"]).astype(int)
    return df


def run_part_b_live(pregame_dir: Path, portfolio_path: Path) -> dict[str, Any]:
    """
    Part B (Live): EV validation using pre-game JSON logs + resolved paper portfolio.

    Uses actual Kalshi entry prices (mid_price_at_entry) from the portfolio,
    matched with model p_estimates from pre-game forecast logs via kalshi_ticker.

    Statistical note: n=2 unique resolved markets at time of writing (far below
    APR-0017 floor of >= 66). Result is directional only; GG-004 remains OPEN.
    """
    APR_FLOOR = 66

    print("\n" + "=" * 65)
    print("PART B (LIVE) — Pre-Game Log + Portfolio EV Validation")
    print("GG-004 | OQ-023 | Source: pre-game logs + resolved portfolio")
    print("=" * 65)

    pregame_df   = _load_pregame_forecasts(pregame_dir)
    portfolio_df = _load_portfolio_outcomes(portfolio_path)

    if pregame_df.empty:
        print("  ERROR: No pregame forecasts found in directory.", file=sys.stderr)
        return {"part": "B_live", "status": "NO_PREGAME_DATA"}
    if portfolio_df.empty:
        print("  ERROR: No closed positions in portfolio.", file=sys.stderr)
        return {"part": "B_live", "status": "NO_PORTFOLIO_DATA"}

    n_unique_markets = portfolio_df["kalshi_ticker"].nunique()
    n_positions      = len(portfolio_df)
    print(f"\n  Pregame unique markets (earliest T1 per ticker): {len(pregame_df)}")
    print(f"  Portfolio closed positions: {n_positions} entries, {n_unique_markets} unique markets")
    print(f"\n  APR-0017 statistical floor: >= {APR_FLOOR} unique resolved markets")
    print(f"  This run: n={n_unique_markets} unique markets — DIRECTIONAL ONLY, not conclusive")

    # Join all portfolio positions with pregame p_estimate via kalshi_ticker
    all_pos = pregame_df[["kalshi_ticker", "p_estimate"]].merge(
        portfolio_df[[
            "kalshi_ticker", "player_name", "kalshi_threshold",
            "mid_price_at_entry", "vig_at_entry", "direction",
            "actual_pts", "y_target", "outcome", "entered_at",
        ]],
        on="kalshi_ticker", how="inner",
    )

    if all_pos.empty:
        print("  WARNING: No kalshi_ticker matches between pregame forecasts and portfolio.")
        return {"part": "B_live", "status": "NO_MATCHES", "n_unique_markets": 0}

    all_pos["entered_at"] = pd.to_datetime(all_pos["entered_at"], utc=True)

    # Per-unique-market subset: earliest portfolio entry per ticker
    unique_pos = (
        all_pos.sort_values("entered_at")
        .drop_duplicates(subset="kalshi_ticker", keep="first")
        .copy()
    )

    # -------------------------------------------------------------------
    # Per-market detail
    # -------------------------------------------------------------------
    print(f"\n  --- Per-market detail ({len(unique_pos)} unique markets) ---")
    for _, row in unique_pos.iterrows():
        p_est    = float(row["p_estimate"])
        mip      = float(row["mid_price_at_entry"])
        vig      = float(row["vig_at_entry"])
        half_vig = vig / 2.0
        y        = int(row["y_target"])
        direction = str(row["direction"])

        edge_vs_market = p_est - mip          # positive = YES edge, negative = NO edge
        edge_vs_null   = p_est - 0.50

        if direction == "YES":
            price_paid = mip + half_vig
            pnl_unit   = (1.0 - price_paid) if y == 1 else -price_paid
        else:
            price_paid = (1.0 - mip) + half_vig
            pnl_unit   = (1.0 - price_paid) if y == 0 else -price_paid

        print(f"\n  Market: {row['kalshi_ticker']}")
        print(f"    Player: {row['player_name']}")
        print(f"    Bet: {direction} over {row['kalshi_threshold']} pts")
        print(f"    Model p_estimate: {p_est:.4f}  |  Kalshi mid at entry: {mip:.4f}  |  Vig: {vig:.3f}")
        print(f"    Edge vs market: {edge_vs_market:+.4f}  (vs null 0.50: {edge_vs_null:+.4f})")
        print(f"    Actual pts: {row['actual_pts']}  |  y_target={y}  |  outcome={row['outcome']}")
        print(f"    P&L per unit stake: {pnl_unit:+.4f}")

    # -------------------------------------------------------------------
    # Aggregate analysis helper
    # -------------------------------------------------------------------
    def _analyze_live(subset: pd.DataFrame, label: str) -> dict[str, Any]:
        p_est     = subset["p_estimate"].to_numpy(dtype=float)
        mip       = subset["mid_price_at_entry"].to_numpy(dtype=float)
        vig       = subset["vig_at_entry"].to_numpy(dtype=float)
        y         = subset["y_target"].astype(int).to_numpy()
        half_vig  = vig / 2.0
        direction = subset["direction"].to_numpy()

        edge_vs_market = p_est - mip
        edge_vs_null   = p_est - 0.50

        # Use actual direction from C4 (already approved vs MIN_EDGE)
        yes_bets = direction == "YES"
        no_bets  = direction == "NO"
        n_yes  = int(yes_bets.sum())
        n_no   = int(no_bets.sum())
        n_bets = n_yes + n_no

        yes_price = mip + half_vig
        no_price  = (1.0 - mip) + half_vig

        pnl_yes = np.where(yes_bets, np.where(y == 1, 1.0 - yes_price, -yes_price), 0.0)
        pnl_no  = np.where(no_bets,  np.where(y == 0, 1.0 - no_price,  -no_price),  0.0)
        total_pnl  = float((pnl_yes + pnl_no).sum())
        ev_per_bet = total_pnl / n_bets if n_bets > 0 else 0.0

        win_yes  = int((yes_bets & (y == 1)).sum())
        win_no   = int((no_bets  & (y == 0)).sum())
        win_rate = (win_yes + win_no) / n_bets if n_bets > 0 else 0.0

        mean_edge_market = float(np.mean(edge_vs_market))
        mean_edge_null   = float(np.mean(edge_vs_null))

        print(f"\n  [{label}]")
        print(f"  n={len(subset)}  |  YES bets: {n_yes}  NO bets: {n_no}")
        print(f"  Win rate: {win_rate:.1%}  (YES wins: {win_yes}/{n_yes}, NO wins: {win_no}/{n_no})")
        print(f"  EV per bet vs market: {ev_per_bet:+.4f}  |  Total P&L: {total_pnl:+.4f}")
        print(f"  Mean edge vs market: {mean_edge_market:+.4f}  (vs null: {mean_edge_null:+.4f})")

        verdict = "POSITIVE_EV" if ev_per_bet > 0 else ("NO_BETS" if n_bets == 0 else "NEGATIVE_EV")
        print(f"  Verdict: {verdict}")

        return {
            "label":             label,
            "n":                 len(subset),
            "n_yes_bets":        n_yes,
            "n_no_bets":         n_no,
            "win_rate":          round(win_rate, 4),
            "ev_per_bet":        round(ev_per_bet, 6),
            "total_pnl":         round(total_pnl, 6),
            "mean_edge_vs_market": round(mean_edge_market, 4),
            "mean_edge_vs_null": round(mean_edge_null, 4),
            "verdict":           verdict,
        }

    print(f"\n  --- Aggregate analysis ---")
    result_unique = _analyze_live(unique_pos, f"Per unique market (n={len(unique_pos)}, first entry price)")
    result_all    = _analyze_live(
        all_pos,
        f"All positions (n={len(all_pos)}) — NOT independent (idempotency bug; {n_unique_markets} unique markets)"
    )

    # -------------------------------------------------------------------
    # GG-004 verdict
    # -------------------------------------------------------------------
    print(f"\n  GG-004 / OQ-023 VERDICT:")
    if result_unique["verdict"] == "POSITIVE_EV":
        verdict = (
            f"DIRECTIONAL_POSITIVE — positive EV vs actual Kalshi prices "
            f"(EV={result_unique['ev_per_bet']:+.4f}/bet, n={len(unique_pos)} unique markets). "
            f"Statistical power INSUFFICIENT: n << APR-0017 floor of >= {APR_FLOOR}. "
            f"GG-004 remains OPEN. Accumulate >= {APR_FLOOR} resolved markets for confirmatory run."
        )
    else:
        verdict = (
            f"DIRECTIONAL_NEGATIVE — negative or zero EV vs actual Kalshi prices "
            f"(EV={result_unique['ev_per_bet']:+.4f}/bet, n={len(unique_pos)} unique markets). "
            f"Statistical power INSUFFICIENT: n << APR-0017 floor of >= {APR_FLOOR}. "
            f"GG-004 remains OPEN."
        )
    print(f"  {verdict}")
    print(f"\n  GG-004 STATUS: OPEN — n={n_unique_markets} resolved markets (floor: >= {APR_FLOOR})")

    return {
        "part":                     "B_live",
        "n_unique_markets":         n_unique_markets,
        "n_portfolio_positions":    n_positions,
        "statistical_floor_apr_0017": APR_FLOOR,
        "statistical_power":        "INSUFFICIENT",
        "per_unique_market":        result_unique,
        "all_positions_not_independent": result_all,
        "verdict":                  verdict,
        "gg_004_status":            "OPEN",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-017: EV vs actual Kalshi prices")
    parser.add_argument(
        "--kalshi-prices",
        type=Path,
        default=None,
        help="Path to operator-provided Kalshi historical prices CSV (enables Part B CSV mode)",
    )
    parser.add_argument(
        "--from-pregame",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Directory containing pregame_YYYYMMDD.json files (enables Part B live mode). "
            "Requires --portfolio to supply resolved outcomes."
        ),
    )
    parser.add_argument(
        "--portfolio",
        type=Path,
        default=None,
        help="Path to paper_portfolio JSON file with closed_positions (required for --from-pregame).",
    )
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"EXP-017: EV Validation Against Actual Kalshi Market Prices")
    print(f"Governance gap: GG-004 (OPEN) | Blocks: G6")
    print(f"Session: {SESSION_ID}")
    print(f"Run at: {_utc_now()}")
    print(f"{'='*65}")

    # Guard
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set — refusing to run in live mode.", file=sys.stderr)
        sys.exit(1)

    # Load data
    print(f"\n[DATA] Loading EXP-005 feature matrix + forecast test CSV...")
    df = _load_test_dataset()
    print(f"  TEST rows loaded: {len(df):,}  |  Unique players: {df['player_id'].nunique()}")
    y_true = df["y_target"].astype(int).to_numpy()
    print(f"  Class balance: {int((y_true==1).sum())} positive / {int((y_true==0).sum())} negative")
    print(f"  p_estimate range: [{df['p_estimate'].min():.3f}, {df['p_estimate'].max():.3f}]")

    # Part A
    results_a = run_part_a(df)

    # Part B — three modes: live (--from-pregame), CSV (--kalshi-prices), or skipped
    if args.from_pregame is not None:
        portfolio_path = args.portfolio
        if portfolio_path is None:
            print(
                "ERROR: --from-pregame requires --portfolio <path/to/paper_portfolio.json>",
                file=sys.stderr,
            )
            sys.exit(1)
        if not args.from_pregame.is_dir():
            print(f"ERROR: --from-pregame path is not a directory: {args.from_pregame}", file=sys.stderr)
            sys.exit(1)
        if not portfolio_path.exists():
            print(f"ERROR: portfolio file not found: {portfolio_path}", file=sys.stderr)
            sys.exit(1)
        results_b = run_part_b_live(args.from_pregame, portfolio_path)
    elif args.kalshi_prices is not None:
        prices = _load_kalshi_prices(args.kalshi_prices)
        if prices is not None:
            print(f"\n[PART B] Kalshi prices loaded: {len(prices):,} rows")
            results_b = run_part_b(df, prices)
        else:
            print(f"\n[PART B] SKIPPED — kalshi_prices.csv failed validation.", file=sys.stderr)
            results_b = {"part": "B", "status": "LOAD_FAILED", "path": str(args.kalshi_prices)}
    else:
        print(f"\n{'='*65}")
        print("PART B — SKIPPED (no Part B arguments provided)")
        print("=" * 65)
        print("  Option 1 — Live mode (pre-game logs + portfolio):")
        print("    python run_exp017.py --from-pregame exp_output/EXP-017/ \\")
        print("        --portfolio exp_output/EXP-017/paper_portfolio_invalidated.json")
        print("  Option 2 — CSV mode (historical prices CSV):")
        print("    python run_exp017.py --kalshi-prices exp_output/EXP-017/kalshi_prices.csv")
        results_b = {
            "part": "B",
            "status": "SKIPPED",
            "reason": "No Part B arguments provided",
        }

    # Summary
    print(f"\n{'='*65}")
    print("EXP-017 SUMMARY")
    print(f"{'='*65}")
    print(f"  TEST set: {len(df):,} rows")
    print(f"  Part A (sensitivity): EV at MIP=0.50 = {results_a['ev_at_null_050']:+.4f}/bet")
    if results_a["breakeven_upper_mip"] is not None:
        print(f"  Part A: Edge positive up to MIP={results_a['breakeven_upper_mip']:.2f} in sweep")
    else:
        print(f"  Part A: Edge negative at all swept MIP values")

    part_b_status = results_b.get("status", "")
    part_b_gg_status = results_b.get("gg_004_status", "")
    if part_b_status in ("SKIPPED", "LOAD_FAILED", "NO_MATCHES", "NO_THRESHOLD_MATCHES",
                         "NO_PREGAME_DATA", "NO_PORTFOLIO_DATA"):
        print(f"  Part B: {part_b_status} — commercial question (OQ-023 / GG-004) still open")
        print(f"  GG-004 STATUS: OPEN — EXP-017 Part B has not been run")
    else:
        verdict = results_b.get("verdict", "UNKNOWN")
        print(f"  Part B: {verdict}")
        # GG-004 only RESOLVES on CONFIRMED (full statistical power, positive EV)
        is_resolved = "CONFIRMED" in verdict and "DIRECTIONAL" not in verdict
        if part_b_gg_status:
            print(f"  GG-004 STATUS: {part_b_gg_status}")
        else:
            print(f"  GG-004 STATUS: {'RESOLVED' if is_resolved else 'OPEN — commercial case not proven'}")

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "exp_id":       EXP_ID,
        "session_id":   SESSION_ID,
        "run_at":       _utc_now(),
        "governance_gap": "GG-004",
        "open_question":  "OQ-023",
        "test_rows":    len(df),
        "part_a":       results_a,
        "part_b":       results_b,
    }
    out_path = OUTPUT_DIR / "EXP-017_results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n  Results saved: {out_path}")


if __name__ == "__main__":
    main()
