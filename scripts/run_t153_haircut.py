#!/usr/bin/env python3
"""
T-153 / GG-022 — Fill-Realism Haircut on All Paper P&L
=======================================================
Applies a bid-ask spread haircut to every closed paper position (T1 + T4)
to estimate what realised P&L would have been under taker-fill assumptions.

Background (GG-022):
  Paper fills execute at assumed prices that do not model bid-ask spread
  crossing.  T1 positions use mid + vig/2 (vig_at_entry ≈ 0.01 for most
  bets, true p50 spread ≈ 0.06–0.08).  T4 exited positions use pure mid
  on both entry and exit — the most optimistic assumption.  All G6-facing
  P&L carries the "unhaircut paper fills" caveat until this script is run.

Haircut rules:
  WIN/LOSS positions (T1 and T4 resolved):
    paper_fill = mid + vig/2  (for YES)  or  (1-mid) + vig/2  (for NO)
    real_fill  = mid + s/2    (for YES)  or  (1-mid) + s/2    (for NO)
    haircut    = size × (s/2 - vig/2) / (paper_fill × real_fill)   [wins only]
    haircut    = 0                                                   [losses]
    Note: if vig/2 >= s/2 the paper model is already conservative; haircut = 0.

  EXITED positions (T4 only — exit_position() uses pure mid on both legs):
    paper_entry_fill = entry_mid
    real_entry_fill  = entry_mid + s/2
    paper_exit_fill  = exit_mip
    real_exit_fill   = exit_mip - s/2  (selling at bid)
    haircut = paper_pnl - real_pnl  (always ≥ 0 when s > 0)

Spread model (from logs/spread_observations.jsonl, G4 data only):
  Three buckets by entry mid-price:
    low  (<0.30):  p50=0.0600  mean=0.0771
    mid  (0.30–0.70): p50=0.0700  mean=0.1013
    high (>0.70):  p50=0.0400  mean=0.0641

Caveats:
  - Spread model is based on in-play G4 data only (n=5,166 real observations).
    Pre-game (T1) markets may have tighter or wider spreads.
  - T1 positions are resting/limit orders submitted to Kalshi.  If filled as
    MAKER, the spread cost may be zero (other side crosses to us).  This
    script applies the same spread model to T1 and T4 as a conservative
    upper bound on T1 haircut.
  - EXITED two-leg haircut assumes same spread model at both entry and exit.
    Exit markets may be wider (in-play, near resolution) → this may
    understate the two-leg haircut.
  - G5 positions are still OPEN; this report covers G1–G4 only.

Usage:
  PYTHONPATH=src python3 scripts/run_t153_haircut.py [--spread p50|mean]
"""
import argparse
import json
import sys
from pathlib import Path

PROJ         = Path(__file__).parent.parent
SPREAD_LOG   = PROJ / "logs" / "spread_observations.jsonl"
PORT_T1      = PROJ / "logs" / "paper_portfolio.json"
PORT_T4      = PROJ / "logs" / "paper_portfolio_t4.json"
OUT_DIR      = PROJ / "exp_output" / "T153"
OUT_JSON     = OUT_DIR / "T153_haircut_results.json"

# --- Spread model (derived from EXP-019C / spread_observations.jsonl G4) ---
SPREAD_MODEL_P50  = {"low": 0.0600, "mid": 0.0700, "high": 0.0400}
SPREAD_MODEL_MEAN = {"low": 0.0771, "mid": 0.1013, "high": 0.0641}

TEST_TICKER_PREFIXES = ("NBA_TEST", "NBA_EXIT_TEST")


def _spread_bucket(mid: float) -> str:
    if mid < 0.30:
        return "low"
    if mid <= 0.70:
        return "mid"
    return "high"


def _spread_for(mid: float, model: dict[str, float]) -> float:
    return model[_spread_bucket(mid)]


def build_spread_model_from_log() -> dict:
    """Recompute spread stats from the JSONL log for reference."""
    if not SPREAD_LOG.exists():
        return {}
    obs = []
    for line in SPREAD_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        if any(o["ticker"].startswith(p) for p in TEST_TICKER_PREFIXES):
            continue
        if o["bid"] is None or o["ask"] is None or o["mid"] is None or o["mid"] <= 0:
            continue
        obs.append({"mid": o["mid"], "spread": o["ask"] - o["bid"]})

    buckets: dict[str, list[float]] = {"low": [], "mid": [], "high": []}
    for o in obs:
        buckets[_spread_bucket(o["mid"])].append(o["spread"])

    result = {}
    for name, values in buckets.items():
        if values:
            values.sort()
            n = len(values)
            result[name] = {
                "n": n,
                "mean": round(sum(values) / n, 5),
                "p50": round(values[n // 2], 5),
                "p90": round(values[int(n * 0.9)], 5),
            }
    return result


def haircut_win_loss(pos: dict, spread_model: dict[str, float]) -> float:
    """
    Haircut for a WIN/LOSS position (resolved via close_positions).

    P&L formula in paper_trader:
      YES win: size * (1 - yes_ask) / yes_ask   where yes_ask = mid + vig/2
      NO win:  size * (1 - no_ask)  / no_ask    where no_ask  = (1-mid) + vig/2
      loss:   -size

    Real fill adds spread/2 instead of vig/2.
    Haircut = paper_win_pnl - real_win_pnl for WIN positions; 0 for LOSS.
    """
    outcome = pos.get("outcome", "LOSS")
    if outcome != "WIN":
        return 0.0

    size      = pos["size_usd"]
    mid       = pos["mid_price_at_entry"]
    vig       = pos["vig_at_entry"]
    direction = pos["direction"]
    spread    = _spread_for(mid, spread_model)

    half_vig    = vig / 2.0
    half_spread = spread / 2.0

    if half_spread <= half_vig:
        # Paper model is already at or beyond true spread cost — no haircut needed.
        return 0.0

    if direction == "YES":
        paper_fill = mid + half_vig
        real_fill  = mid + half_spread
    else:  # NO
        paper_fill = (1.0 - mid) + half_vig
        real_fill  = (1.0 - mid) + half_spread

    if paper_fill <= 0 or real_fill <= 0:
        return 0.0

    # Haircut = size × (real_fill - paper_fill) / (paper_fill × real_fill)
    return round(size * (real_fill - paper_fill) / (paper_fill * real_fill), 6)


def haircut_exited(pos: dict, spread_model: dict[str, float]) -> float:
    """
    Haircut for an EXITED position (T4 only — exit_position() uses pure mid).

    Paper P&L:
      YES: size * (exit_mip / entry_mip - 1)
      NO:  size * ((1-exit_mip) / (1-entry_mip) - 1)

    Real P&L (entry at ask, exit at bid):
      YES: size / (entry_mid + s/2) * (exit_mip - s/2) - size
      NO:  size / ((1-entry_mid) + s/2) * ((1-exit_mip) - s/2) - size
    """
    size       = pos["size_usd"]
    entry_mid  = pos["mid_price_at_entry"]
    exit_mip   = pos.get("exit_mip")
    direction  = pos["direction"]

    if exit_mip is None:
        return 0.0

    spread = _spread_for(entry_mid, spread_model)
    half_s = spread / 2.0

    if direction == "YES":
        # Paper
        paper_pnl = size * (exit_mip / entry_mid) - size if entry_mid > 0 else 0.0
        # Real
        real_entry = entry_mid + half_s
        real_exit  = exit_mip - half_s
        real_pnl   = size / real_entry * real_exit - size if real_entry > 0 else 0.0
    else:  # NO
        entry_no = 1.0 - entry_mid
        exit_no  = 1.0 - exit_mip
        # Paper
        paper_pnl = size * (exit_no / entry_no) - size if entry_no > 0 else 0.0
        # Real
        real_entry_no = entry_no + half_s
        real_exit_no  = exit_no - half_s
        real_pnl      = size / real_entry_no * real_exit_no - size if real_entry_no > 0 else 0.0

    return round(paper_pnl - real_pnl, 6)


def analyse_portfolio(
    positions: list[dict],
    spread_model: dict[str, float],
    label: str,
) -> dict:
    """Compute per-position haircuts and aggregate stats."""
    rows = []
    for pos in positions:
        status = pos.get("status", "CLOSED")
        if status == "EXITED":
            hc = haircut_exited(pos, spread_model)
            pnl = pos.get("exit_pnl", 0.0)
            typ = "EXITED"
        else:
            hc  = haircut_win_loss(pos, spread_model)
            pnl = pos.get("pnl", 0.0)
            typ = pos.get("outcome", "LOSS")

        rows.append({
            "position_id": pos["position_id"],
            "type": typ,
            "direction": pos["direction"],
            "mid": pos["mid_price_at_entry"],
            "size_usd": pos["size_usd"],
            "paper_pnl": round(pnl, 4),
            "haircut": round(hc, 4),
            "haircut_pct_of_pnl": round(hc / pnl * 100, 1) if pnl > 0 else None,
            "adjusted_pnl": round(pnl - hc, 4),
        })

    n       = len(rows)
    n_win   = sum(1 for r in rows if r["type"] == "WIN")
    n_loss  = sum(1 for r in rows if r["type"] == "LOSS")
    n_exit  = sum(1 for r in rows if r["type"] == "EXITED")

    total_paper_pnl    = round(sum(r["paper_pnl"] for r in rows), 4)
    total_haircut      = round(sum(r["haircut"] for r in rows), 4)
    total_adjusted_pnl = round(total_paper_pnl - total_haircut, 4)
    total_staked       = round(sum(r["size_usd"] for r in rows), 2)

    return {
        "label": label,
        "n_positions": n,
        "n_win": n_win,
        "n_loss": n_loss,
        "n_exited": n_exit,
        "total_staked_usd": total_staked,
        "total_paper_pnl": total_paper_pnl,
        "total_haircut_usd": total_haircut,
        "total_adjusted_pnl": total_adjusted_pnl,
        "haircut_pct_of_paper_pnl": round(
            total_haircut / total_paper_pnl * 100, 1
        ) if total_paper_pnl != 0 else None,
        "pnl_change_pct_of_staked": round(
            total_haircut / total_staked * 100, 2
        ) if total_staked > 0 else None,
        "positions": rows,
    }


def _sep(title: str = "") -> None:
    w = 68
    if title:
        print(f"\n── {title} {'─' * (w - len(title) - 4)}")
    else:
        print("─" * w)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spread", choices=["p50", "mean"], default="p50",
        help="Spread estimate to use: p50 (default, central) or mean (upper bound)"
    )
    args = parser.parse_args()

    spread_model = SPREAD_MODEL_P50 if args.spread == "p50" else SPREAD_MODEL_MEAN

    print("=" * 68)
    print("T-153 / GG-022 — Fill-Realism Haircut Report")
    print(f"Spread model: {args.spread.upper()}  "
          f"(low={spread_model['low']:.4f}  mid={spread_model['mid']:.4f}  "
          f"high={spread_model['high']:.4f})")
    print("=" * 68)

    # Load portfolios
    t1_port = json.loads(PORT_T1.read_text())
    t4_port = json.loads(PORT_T4.read_text())

    t1_closed = t1_port.get("closed_positions", [])
    t4_closed = t4_port.get("closed_positions", [])

    print(f"\nPositions loaded:  T1={len(t1_closed)}  T4={len(t4_closed)}")
    print("(G5 positions still OPEN — not included in this report)")

    # Print live spread model stats for reference
    live_model = build_spread_model_from_log()
    if live_model:
        _sep("Spread model (G4 in-play data)")
        for bkt, stats in live_model.items():
            print(f"  {bkt:5s}: n={stats['n']:5d}  mean={stats['mean']:.4f}  "
                  f"p50={stats['p50']:.4f}  p90={stats['p90']:.4f}")

    # --- T1 analysis ---
    t1_result = analyse_portfolio(t1_closed, spread_model, "T1")
    _sep("T1  (resolved positions, G1–G4)")
    print(f"  Positions:   {t1_result['n_positions']}  "
          f"(wins={t1_result['n_win']}  losses={t1_result['n_loss']})")
    print(f"  Total staked:        ${t1_result['total_staked_usd']:,.2f}")
    print(f"  Paper P&L:           ${t1_result['total_paper_pnl']:+,.4f}")
    print(f"  Haircut:            -${t1_result['total_haircut_usd']:,.4f}")
    print(f"  Adjusted P&L:        ${t1_result['total_adjusted_pnl']:+,.4f}")
    print(f"  Haircut as % staked: {t1_result['pnl_change_pct_of_staked']:.2f}%")
    print()
    print("  NOTE: T1 bets are resting (limit) orders submitted to Kalshi.")
    print("  If filled as MAKER, spread cost = 0 and this haircut is an")
    print("  UPPER BOUND.  Treat with caution.")

    # --- T4 analysis ---
    t4_result = analyse_portfolio(t4_closed, spread_model, "T4")
    _sep("T4  (resolved + exited positions, G3–G4)")
    print(f"  Positions:   {t4_result['n_positions']}  "
          f"(wins={t4_result['n_win']}  losses={t4_result['n_loss']}  "
          f"exited={t4_result['n_exited']})")
    print(f"  Total staked:        ${t4_result['total_staked_usd']:,.2f}")
    print(f"  Paper P&L:           ${t4_result['total_paper_pnl']:+,.4f}")
    print(f"  Haircut:            -${t4_result['total_haircut_usd']:,.4f}")
    print(f"  Adjusted P&L:        ${t4_result['total_adjusted_pnl']:+,.4f}")
    print(f"  Haircut as % staked: {t4_result['pnl_change_pct_of_staked']:.2f}%")
    print()
    print("  NOTE: T4 exited positions apply TWO-LEG haircut (entry ask +")
    print("  exit bid).  WIN/LOSS positions apply ONE-LEG (entry only).")

    # --- Combined ---
    total_paper  = t1_result["total_paper_pnl"] + t4_result["total_paper_pnl"]
    total_hc     = t1_result["total_haircut_usd"] + t4_result["total_haircut_usd"]
    total_adj    = total_paper - total_hc
    total_staked = t1_result["total_staked_usd"] + t4_result["total_staked_usd"]

    _sep("Combined (T1 + T4, G1–G4)")
    print(f"  Total staked:        ${total_staked:,.2f}")
    print(f"  Paper P&L:           ${total_paper:+,.4f}")
    print(f"  Total haircut:      -${total_hc:,.4f}")
    print(f"  Adjusted P&L:        ${total_adj:+,.4f}")
    print(f"  Haircut as % staked: {total_hc / total_staked * 100:.2f}%")

    # --- G6 materiality ---
    _sep("G6 materiality assessment")
    print(f"  Haircut direction:   ANTI-CONSERVATIVE (paper overstates P&L)")
    if abs(total_hc) < 5.0:
        verdict = "LOW — haircut < $5; G6 Tier 2 P&L slope assessment unaffected"
    elif abs(total_hc) < 20.0:
        verdict = "MEDIUM — haircut $5–$20; report adjusted figures in G6 evidence"
    else:
        verdict = "HIGH — haircut > $20; adjusted P&L materially changes G6 picture"
    print(f"  Materiality:         {verdict}")
    print()
    print("  G5 haircut not included (positions still OPEN).")
    print("  Rerun this script after G5 resolves to get final G1–G5 figure.")

    # --- Save results ---
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "script": "run_t153_haircut.py",
        "governance": "T-153 / GG-022",
        "spread_estimate": args.spread,
        "spread_model": {k: v for k, v in spread_model.items()},
        "t1": {k: v for k, v in t1_result.items() if k != "positions"},
        "t4": {k: v for k, v in t4_result.items() if k != "positions"},
        "combined": {
            "total_staked_usd": round(total_staked, 2),
            "total_paper_pnl": round(total_paper, 4),
            "total_haircut_usd": round(total_hc, 4),
            "total_adjusted_pnl": round(total_adj, 4),
            "haircut_pct_of_staked": round(total_hc / total_staked * 100, 2),
        },
        "g6_materiality": verdict,
        "caveats": [
            "T1 resting orders may be maker fills (zero spread cost) — haircut is upper bound",
            "Spread model from G4 in-play data only; pre-game spreads may differ",
            "T4 exited two-leg haircut assumes same spread at entry and exit",
            "G5 positions still OPEN — not included",
        ],
    }
    with open(OUT_JSON, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved: {OUT_JSON.relative_to(PROJ)}")
    print("=" * 68)


if __name__ == "__main__":
    main()
