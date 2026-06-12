#!/usr/bin/env python3
"""
EXP-019B Empirical — Exit Mechanics Validation on G4 Actual Data

Uses real G4 T4 positions from paper_portfolio_t4.json to validate:
  1. True-positive rate: exits that fired on eventual-LOSS tickers
  2. False-positive rate: exits that fired on eventual-WIN tickers
  3. Observed noise buffer margin vs analytic NOISE_BUFFER_BAND_T4=0.13905
  4. P&L improvement: exit_pnl vs counterfactual hold_pnl

Methodology:
  - For each ticker, determine final outcome (WIN/LOSS) from CLOSED positions.
  - EXITED positions on the same ticker inherit that outcome as counterfactual.
  - Correct exit: EXIT fired on a LOSS ticker (avoided loss).
  - False exit:   EXIT fired on a WIN ticker (abandoned winning position).
  - Noise buffer validation: observed mean(mip_at_exit - p_current_at_exit).
"""
import json
import math
from pathlib import Path

NOISE_BUFFER_BAND_T4 = 0.13905
GAME_DATE = "2026-06-10"

PROJ     = Path(__file__).parent.parent
T4_PORT  = PROJ / "logs" / "paper_portfolio_t4.json"
OUT_PATH = PROJ / "exp_output" / "EXP-019" / "EXP-019B_empirical_results.json"


def e_log_wealth(pnls: list[float], initial: float) -> float:
    total, w = 0.0, initial
    for p in pnls:
        w_new = w + p
        if w_new <= 0:
            return float("-inf")
        total += math.log(w_new / w)
        w = w_new
    return total / len(pnls) if pnls else 0.0


def main() -> None:
    print("=" * 64)
    print("EXP-019B — Exit Mechanics Validation (Empirical, G4 data)")
    print("=" * 64)

    with open(T4_PORT) as f:
        portfolio = json.load(f)

    g4 = [p for p in portfolio["closed_positions"] if p.get("game_date") == GAME_DATE]
    yes_g4 = [p for p in g4 if p.get("direction") == "YES"]
    print(f"G4 YES positions:      {len(yes_g4)}")

    closed = [p for p in yes_g4 if p.get("status") == "CLOSED"]
    exited = [p for p in yes_g4 if p.get("status") == "EXITED"]
    print(f"  CLOSED (held):       {len(closed)}")
    print(f"  EXITED (exit fired): {len(exited)}")

    # Build player_id → actual_pts from CLOSED positions (ground truth)
    player_actual_pts: dict[int, float] = {}
    for pos in closed:
        pid = pos.get("player_id")
        pts = pos.get("actual_pts")
        if pid and pts is not None:
            player_actual_pts[pid] = pts

    # Determine counterfactual outcome for EXITED positions:
    # WIN if actual_pts >= kalshi_threshold, LOSS otherwise
    def infer_outcome(pos: dict):
        pid = pos.get("player_id")
        thr = pos.get("kalshi_threshold")
        pts = player_actual_pts.get(pid)
        if pts is None or thr is None:
            return None
        return "WIN" if pts >= thr else "LOSS"

    exited_with_outcome = [(pos, infer_outcome(pos)) for pos in exited]
    exited_on_loss = [pos for pos, o in exited_with_outcome if o == "LOSS"]
    exited_on_win  = [pos for pos, o in exited_with_outcome if o == "WIN"]
    exited_unknown = [pos for pos, o in exited_with_outcome if o is None]

    # All YES positions by inferred outcome
    def infer_outcome_any(pos: dict):
        if pos.get("status") == "CLOSED":
            return pos.get("outcome")
        return infer_outcome(pos)

    all_yes_with_outcome = [(pos, infer_outcome_any(pos)) for pos in yes_g4]
    loss_positions = [pos for pos, o in all_yes_with_outcome if o == "LOSS"]
    win_positions  = [pos for pos, o in all_yes_with_outcome if o == "WIN"]

    print(f"\nPlayers with known pts: {len(player_actual_pts)}")
    print(f"  WIN positions (all): {len(win_positions)}  LOSS positions (all): {len(loss_positions)}")

    tp_rate = len(exited_on_loss) / len(loss_positions) if loss_positions else 0
    fp_rate = len(exited_on_win)  / len(win_positions)  if win_positions  else 0

    print(f"\n── Exit accuracy ───────────────────────────────────────────")
    print(f"  Correct exits (on LOSS positions): {len(exited_on_loss)}")
    print(f"  False exits   (on WIN positions):  {len(exited_on_win)}")
    print(f"  Unknown outcome:                   {len(exited_unknown)}")
    print(f"\n  True-positive rate:  {tp_rate:.3f}  ({len(exited_on_loss)}/{len(loss_positions)} LOSS positions exited)")
    print(f"  False-positive rate: {fp_rate:.3f}  ({len(exited_on_win)}/{len(win_positions)} WIN positions exited)")
    print(f"  Analytic TP rate:    0.799  (433/542 — EXP-019B analytic)")
    print(f"  Analytic FP rate:    0.000")

    # Noise buffer validation
    observed_buffers = []
    for pos in exited:
        mip_exit = pos.get("exit_mip")
        p_cur    = pos.get("p_current_at_exit")
        if mip_exit is not None and p_cur is not None:
            observed_buffers.append(mip_exit - p_cur)

    if observed_buffers:
        mean_buf = sum(observed_buffers) / len(observed_buffers)
        sorted_buf = sorted(observed_buffers)
        p50_buf = sorted_buf[len(sorted_buf) // 2]
        p10_buf = sorted_buf[int(len(sorted_buf) * 0.1)]
        print(f"\n── Noise buffer observed ────────────────────────────────────")
        print(f"  Expected NOISE_BUFFER_BAND_T4: {NOISE_BUFFER_BAND_T4:.5f}")
        print(f"  Observed mean(mip - p_current): {mean_buf:.5f}")
        print(f"  Observed p50:                   {p50_buf:.5f}")
        print(f"  Observed p10 (smallest margin): {p10_buf:.5f}")
        within_20pct = abs(mean_buf - NOISE_BUFFER_BAND_T4) / NOISE_BUFFER_BAND_T4 < 0.20
        print(f"  Within ±20% tolerance: {'YES ✓' if within_20pct else 'NO — RECALIBRATE'}")

    # Counterfactual: what would EXITED positions have earned if held?
    # WIN: net = 1 - mip_entry (per unit); LOSS: net = -mip_entry (per unit)
    cf_pairs: list[tuple[float, float]] = []  # (exit_pnl, hold_pnl)
    for pos in exited:
        outcome = infer_outcome(pos)
        if outcome is None:
            continue
        ep   = pos.get("exit_pnl", 0.0)
        mip  = pos.get("mid_price_at_entry", 0.0)
        size = pos.get("size_usd", 0.0)
        if size <= 0 or mip <= 0:
            continue
        contracts = size / mip
        hold_pnl = contracts * (1.0 - mip) if outcome == "WIN" else contracts * (-mip)
        cf_pairs.append((ep, hold_pnl))

    exit_pnls    = [ep for ep, _ in cf_pairs]
    hold_pnls_cf = [hp for _, hp in cf_pairs]

    if exit_pnls:
        mean_exit = sum(exit_pnls) / len(exit_pnls)
        mean_hold = sum(hold_pnls_cf) / len(hold_pnls_cf)
        improvement = mean_exit - mean_hold
        print(f"\n── P&L comparison (EXITED positions only) ──────────────────")
        print(f"  n positions compared: {len(exit_pnls)}")
        print(f"  Mean exit P&L:        {mean_exit:+.4f}/position")
        print(f"  Mean hold P&L (cf):   {mean_hold:+.4f}/position")
        print(f"  Mean improvement:     {improvement:+.4f}/position")
        pnl_t4_initial = portfolio.get("initial_bankroll_usd", 1000.0)
        e_log_exit = e_log_wealth(exit_pnls, pnl_t4_initial)
        e_log_hold = e_log_wealth(hold_pnls_cf, pnl_t4_initial)
        print(f"  E[log_r] exit: {e_log_exit:+.8f}")
        print(f"  E[log_r] hold: {e_log_hold:+.8f}")

    # Overall verdict
    print(f"\n── Verdict ──────────────────────────────────────────────────")
    if observed_buffers:
        deviation_pct = abs(mean_buf - NOISE_BUFFER_BAND_T4) / NOISE_BUFFER_BAND_T4 * 100
        if deviation_pct <= 20:
            print(f"  NOISE_BUFFER_BAND_T4=0.13905 VALIDATED (±{deviation_pct:.1f}% observed deviation)")
        else:
            print(f"  NOISE_BUFFER_BAND_T4 NEEDS RECALIBRATION (±{deviation_pct:.1f}% deviation > 20% tolerance)")
    print(f"  TP rate: {tp_rate:.3f}  FP rate: {fp_rate:.3f}")
    analytic_tp = 0.799
    analytic_fp = 0.000
    tp_ok = abs(tp_rate - analytic_tp) / analytic_tp < 0.20
    fp_ok = fp_rate <= 0.05
    print(f"  TP vs analytic: {'OK' if tp_ok else 'DIVERGED'}  FP acceptable: {'YES' if fp_ok else 'NO'}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "exp_id":   "EXP-019B",
        "mode":     "empirical",
        "game_date": GAME_DATE,
        "noise_buffer_band_t4": NOISE_BUFFER_BAND_T4,
        "n_yes_positions":   len(yes_g4),
        "n_closed":          len(closed),
        "n_exited":          len(exited),
        "n_win_positions":    len(win_positions),
        "n_loss_positions":  len(loss_positions),
        "exit_accuracy": {
            "correct_exits_on_loss": len(exited_on_loss),
            "false_exits_on_win":    len(exited_on_win),
            "unknown_outcome":       len(exited_unknown),
            "true_positive_rate":    round(tp_rate, 4),
            "false_positive_rate":   round(fp_rate, 4),
            "analytic_tp_rate":      0.799,
            "analytic_fp_rate":      0.0,
        },
        "noise_buffer_observed": {
            "mean":         round(mean_buf, 5) if observed_buffers else None,
            "p50":          round(p50_buf, 5) if observed_buffers else None,
            "p10":          round(p10_buf, 5) if observed_buffers else None,
            "within_20pct": within_20pct if observed_buffers else None,
        },
        "pnl_comparison": {
            "n_compared":        len(exit_pnls) if exit_pnls else 0,
            "mean_exit_pnl":     round(mean_exit, 4) if exit_pnls and hold_pnls_cf and len(exit_pnls) == len(hold_pnls_cf) else None,
            "mean_hold_pnl_cf":  round(mean_hold, 4) if exit_pnls and hold_pnls_cf and len(exit_pnls) == len(hold_pnls_cf) else None,
            "mean_improvement":  round(improvement, 4) if exit_pnls and hold_pnls_cf and len(exit_pnls) == len(hold_pnls_cf) else None,
        },
    }
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved: {OUT_PATH.relative_to(PROJ)}")
    print("=" * 64)


if __name__ == "__main__":
    main()
