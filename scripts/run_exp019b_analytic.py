#!/usr/bin/env python3
"""
EXP-019B — Exit Sizing Validation: Full vs Partial Kelly-Inverse Exit
Analytic simulation on G3 T4 paper positions (ADR-0018 §6).

Methodology:
- For each YES T4 position from G3, reconstruct p_current(t) trajectory using
  Poisson model + linear scoring assumption.
- Exit signal fires when: p_current(t) < mip_entry - NOISE_BUFFER_BAND_T4
  (market-lag model: market still at entry price, model has downgraded)
- At exit time: sell YES at p_current(t_exit) (efficient market at exit)
  => P&L_exit = p_current(t_exit) - mip_entry ≈ -NOISE_BUFFER_BAND_T4
- Compare E[log(final_wealth)] under three policies:
    Policy 1: Hold to expiry (baseline)
    Policy 2: Full exit at first signal
    Policy 3: Partial Kelly-inverse exit at first signal

Assumptions (analytic mode — empirical validation pending EXP-019B empirical after 3 game nights):
- Linear scoring: pts_so_far(t) = actual_pts * elapsed_t / TOTAL_GAME_MIN
- Tip-off: TIP_OFF_UTC (configurable below)
- Market lags model: mip_current ≈ mip_entry throughout game
- NOISE_BUFFER_BAND_T4 = 0.13905 (EXP-019A)
- T4 pool starting size: $500 (PAPER_T4_POOL_USD)
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────
NOISE_BUFFER_BAND_T4 = 0.13905   # EXP-019A T4 value
TOTAL_GAME_MIN       = 48.0      # NBA regulation game clock
STEP_MIN             = 1.0       # simulation time step (minutes)
T4_POOL_INITIAL      = 500.0     # PAPER_T4_POOL_USD at G3 start
TIP_OFF_UTC          = "2026-06-09T00:00:00Z"   # 8 PM EDT, G3 at NYK

PROJ     = Path(__file__).parent.parent
T4_PORT  = PROJ / "logs" / "paper_portfolio_t4.json"
PREGAME  = PROJ / "logs" / "pregame_20260608.json"
OUT_PATH = PROJ / "exp_output" / "EXP-019" / "EXP-019B_results.json"

# ── Poisson CDF (stdlib) ───────────────────────────────────────────────────────
def _poisson_cdf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k >= 0 else 0.0
    total, term = 0.0, math.exp(-lam)
    for i in range(k + 1):
        total += term
        if i < k:
            term *= lam / (i + 1)
    return min(total, 1.0)

def p_poisson_over(threshold: float, lam_remaining: float, pts_so_far: float) -> float:
    """P(total_pts >= threshold | pts_so_far already, remaining λ = lam_remaining)."""
    pts_needed = threshold - pts_so_far
    if pts_needed <= 0:
        return 1.0
    k = int(pts_needed) - 1
    return 1.0 - _poisson_cdf(k, lam_remaining)

# ── Kelly fraction for YES Kalshi bet ─────────────────────────────────────────
def kelly_fraction_yes(p: float, mip: float) -> float:
    if mip <= 0 or mip >= 1:
        return 0.0
    b = (1.0 - mip) / mip      # net odds per unit stake on YES
    f = (p * b - (1.0 - p)) / b
    return max(0.0, f)

# ── Load data ─────────────────────────────────────────────────────────────────
def load_t4_positions(game_date: str = "2026-06-08") -> list[dict]:
    with open(T4_PORT) as f:
        d = json.load(f)
    return [p for p in d["closed_positions"]
            if p.get("game_date") == game_date and p.get("direction") == "YES"]

def build_lambda_map(game_date: str = "2026-06-08") -> dict:
    """Returns {(player_id, threshold): opp_adj_lambda}."""
    with open(PREGAME) as f:
        d = json.load(f)
    lmap: dict[tuple, float] = {}
    for fc in d.get("forecasts", []):
        key = (fc["player_id"], fc["kalshi_threshold"])
        lmap[key] = fc["opp_adj_lambda"]
    return lmap

# ── Simulation ────────────────────────────────────────────────────────────────
TIP_OFF_DT = datetime.fromisoformat(TIP_OFF_UTC.replace("Z", "+00:00"))

def elapsed_at_entry(entered_at: str) -> float:
    """Minutes elapsed since tip-off at position entry time."""
    entry_dt = datetime.fromisoformat(entered_at.replace("Z", "+00:00"))
    elapsed = (entry_dt - TIP_OFF_DT).total_seconds() / 60.0
    return max(0.0, min(elapsed, TOTAL_GAME_MIN))

def simulate_position(pos: dict, lam: float) -> dict:
    """
    Simulate a single YES position through the game.
    Returns per-policy P&L and exit metadata.
    """
    mip_entry       = pos["mid_price_at_entry"]
    threshold       = float(pos["kalshi_threshold"])
    actual_pts      = float(pos["actual_pts"])
    outcome         = pos["outcome"]                # "WIN" or "LOSS"
    pnl_actual      = float(pos["pnl"])             # from portfolio (hold P&L)

    t_elapsed_entry = elapsed_at_entry(pos["entered_at"])
    t_remaining_entry = TOTAL_GAME_MIN - t_elapsed_entry

    # Kelly fraction at entry
    f_entry = kelly_fraction_yes(pos["model_p"], mip_entry)

    # Step through remaining game in 1-min increments
    exit_time   = None   # elapsed minutes when exit fires
    exit_p      = None   # p_current at exit
    exit_pnl_full    = None
    exit_pnl_partial = None

    t = t_remaining_entry
    while t >= 0.0:
        elapsed = TOTAL_GAME_MIN - t
        pts_so_far  = actual_pts * (elapsed / TOTAL_GAME_MIN)
        lam_remain  = lam * (t / TOTAL_GAME_MIN)
        p_cur       = p_poisson_over(threshold, lam_remain, pts_so_far)

        # Exit condition: p_current < mip_entry - buffer (market lags model)
        if p_cur < mip_entry - NOISE_BUFFER_BAND_T4:
            exit_time = elapsed
            exit_p    = p_cur
            # Sell YES at p_current (efficient market at exit — conservative)
            exit_price_received = p_cur
            exit_pnl_full = exit_price_received - mip_entry

            # Kelly-inverse partial exit
            f_exit = kelly_fraction_yes(p_cur, p_cur)  # mip ≈ p_cur at exit
            if f_entry <= 0:
                partial_fraction = 1.0
            else:
                partial_fraction = max(0.0, 1.0 - f_exit / f_entry)
            # Blended P&L: partial_fraction exits at exit_price, remainder holds
            exit_pnl_partial = (partial_fraction * exit_pnl_full
                                + (1.0 - partial_fraction) * pnl_actual)
            break

        t -= STEP_MIN

    # Policy 1: hold (actual outcome)
    pnl_p1 = pnl_actual
    # Policy 2: full exit (if fired), else hold
    pnl_p2 = exit_pnl_full if exit_time is not None else pnl_actual
    # Policy 3: partial Kelly-inverse (if fired), else hold
    pnl_p3 = exit_pnl_partial if exit_time is not None else pnl_actual

    return {
        "ticker":           pos["kalshi_ticker"],
        "player":           pos["player_name"],
        "threshold":        threshold,
        "mip_entry":        mip_entry,
        "model_p_entry":    pos["model_p"],
        "actual_pts":       actual_pts,
        "outcome":          outcome,
        "t_remaining_entry": round(t_remaining_entry, 1),
        "exit_fired":       exit_time is not None,
        "exit_time_elapsed": round(exit_time, 1) if exit_time is not None else None,
        "exit_p_current":   round(exit_p, 4) if exit_p is not None else None,
        "pnl_p1_hold":      round(pnl_p1, 4),
        "pnl_p2_full_exit": round(pnl_p2, 4),
        "pnl_p3_partial":   round(pnl_p3, 4),
    }

# ── Aggregate ─────────────────────────────────────────────────────────────────
def e_log_wealth(pnls: list[float], initial: float) -> float:
    """E[log(W_final / W_initial)] — log-return criterion (Kelly target)."""
    total = 0.0
    w = initial
    for p in pnls:
        w_new = w + p
        if w_new <= 0:
            return float("-inf")
        total += math.log(w_new / w)
        w = w_new
    return total / len(pnls) if pnls else 0.0

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 64)
    print("EXP-019B — Exit Sizing Validation (Analytic, G3 T4 data)")
    print("=" * 64)

    positions = load_t4_positions()
    lambda_map = build_lambda_map()
    print(f"YES positions loaded:  {len(positions)}")

    results = []
    skipped = 0
    for pos in positions:
        key = (pos["player_id"], pos["kalshi_threshold"])
        lam = lambda_map.get(key)
        if lam is None or lam <= 0:
            skipped += 1
            continue
        results.append(simulate_position(pos, lam))

    if skipped:
        print(f"Skipped (no lambda):   {skipped}")

    n_fired      = sum(1 for r in results if r["exit_fired"])
    yes_losses   = [r for r in results if r["outcome"] == "LOSS"]
    yes_wins     = [r for r in results if r["outcome"] == "WIN"]
    fired_losses = [r for r in yes_losses if r["exit_fired"]]
    fired_wins   = [r for r in yes_wins   if r["exit_fired"]]

    pnls_p1 = [r["pnl_p1_hold"]      for r in results]
    pnls_p2 = [r["pnl_p2_full_exit"] for r in results]
    pnls_p3 = [r["pnl_p3_partial"]   for r in results]

    total_p1 = sum(pnls_p1)
    total_p2 = sum(pnls_p2)
    total_p3 = sum(pnls_p3)

    e_log_p1 = e_log_wealth(pnls_p1, T4_POOL_INITIAL)
    e_log_p2 = e_log_wealth(pnls_p2, T4_POOL_INITIAL)
    e_log_p3 = e_log_wealth(pnls_p3, T4_POOL_INITIAL)

    print()
    print(f"Simulated positions:   {len(results)}")
    print(f"Exit signals fired:    {n_fired}  ({100*n_fired/len(results):.1f}%)")
    print(f"  on YES losses:       {len(fired_losses)}/{len(yes_losses)}"
          f"  ({100*len(fired_losses)/max(1,len(yes_losses)):.1f}%)")
    print(f"  on YES wins (false): {len(fired_wins)}/{len(yes_wins)}"
          f"  ({100*len(fired_wins)/max(1,len(yes_wins)):.1f}%)")
    print()
    print("── P&L comparison ──────────────────────────────────────────")
    print(f"Policy 1 (hold):      total={total_p1:+.2f}  E[log_r]={e_log_p1:+.6f}")
    print(f"Policy 2 (full exit): total={total_p2:+.2f}  E[log_r]={e_log_p2:+.6f}")
    print(f"Policy 3 (partial):   total={total_p3:+.2f}  E[log_r]={e_log_p3:+.6f}")
    print()

    # Verdict
    best = max([(e_log_p2, "FULL_EXIT"), (e_log_p3, "PARTIAL_KELLY"), (e_log_p1, "HOLD")])
    print(f"Verdict (E[log_r] max): {best[1]}")

    if e_log_p2 > e_log_p1:
        lift_p2 = (e_log_p2 - e_log_p1) / abs(e_log_p1) * 100 if e_log_p1 != 0 else float("inf")
        print(f"  Full exit vs hold:   +{lift_p2:.1f}% E[log_r] lift")
    if e_log_p3 > e_log_p1:
        lift_p3 = (e_log_p3 - e_log_p1) / abs(e_log_p1) * 100 if e_log_p1 != 0 else float("inf")
        print(f"  Partial vs hold:     +{lift_p3:.1f}% E[log_r] lift")

    print()
    print("── Assumptions (analytic mode) ─────────────────────────────")
    print(f"  Linear scoring, market-lag model (mip_current ≈ mip_entry)")
    print(f"  NOISE_BUFFER_BAND_T4 = {NOISE_BUFFER_BAND_T4}")
    print(f"  TIP_OFF_UTC = {TIP_OFF_UTC}")
    print(f"  Empirical validation pending: 3 game nights trajectory data (EXP-019B empirical)")
    print("=" * 64)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "exp_id": "EXP-019B",
        "mode": "analytic",
        "game_date": "2026-06-08",
        "noise_buffer_band_t4": NOISE_BUFFER_BAND_T4,
        "tip_off_utc": TIP_OFF_UTC,
        "n_positions": len(results),
        "n_exit_fired": n_fired,
        "n_fired_on_losses": len(fired_losses),
        "n_fired_on_wins_false": len(fired_wins),
        "policy_1_hold":    {"total_pnl": round(total_p1, 4), "e_log_return": round(e_log_p1, 8)},
        "policy_2_full_exit": {"total_pnl": round(total_p2, 4), "e_log_return": round(e_log_p2, 8)},
        "policy_3_partial": {"total_pnl": round(total_p3, 4), "e_log_return": round(e_log_p3, 8)},
        "verdict": best[1],
    }
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Results saved: {OUT_PATH.relative_to(PROJ)}")

if __name__ == "__main__":
    main()
