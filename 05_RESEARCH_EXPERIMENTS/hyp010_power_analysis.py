#!/usr/bin/env python3
"""HYP-010 pre-registration power analysis — Phase 2 gate 2.3.

Answers one question: at the sample size that actually exists, can gate 2.3
distinguish a skilled team-totals model from the market?

Two candidate gate metrics are compared:
  (1) BRIER vs market-implied, scored per game  (gate 2.3 as originally written)
  (2) SELECTED-SUBSET EV — P&L per bet over the subset where |model_p - mkt_p| > vig,
      powered via the APR-0024 variance-derived n* standard

Run:  python3 05_RESEARCH_EXPERIMENTS/hyp010_power_analysis.py
No dependencies beyond the stdlib. Deterministic under the seeds below.

Derived inputs (measured 2026-08-15 from exp_output/PRICE_ARCHIVE/prices_2026-08-*.jsonl,
16 files, 2026-08-01 .. 2026-08-16 — re-derive before citing, ADR-0050 §10):
  KXMLBTOTAL observations ......... 64,969
  distinct game-events ............ 214
  distinct game-dates ............. 16
  threshold lines per game ........ 12  (totals 3..14)
  half_spread, active, mid .05-.95: median 0.0050  mean 0.0095  p90 0.0150  (n=57,814)
  (baseline, the market the bot trades today)
  KXMLBHIT half_spread ...........: median 0.0150  mean 0.0591  p90 0.1550  (n=76,235)
"""

import random
import statistics as st

# ---- derived constants -------------------------------------------------------
N_GAMES_ARCHIVE = 214       # distinct KXMLBTOTAL game-events, 2026-08-01..16
LINES_PER_GAME = 12         # totals 3..14
VIG = 0.010                 # round-trip ~= 2 x median half_spread (0.0050)

# Effective independent unit is the GAME, not the (game, line) row: the 12 lines
# on one game resolve off a single realized run total and are heavily correlated.
# Scoring 214*12 = 2,568 rows as independent would inflate power ~12x and produce
# a threshold that cannot honestly fail.

_clip = lambda x: min(max(x, 0.01), 0.99)


# ---- metric 1: Brier vs market ----------------------------------------------
def paired_brier(model_noise, market_noise, n_games, reps=1200, seed=7):
    """Paired per-game Brier difference (market - model). Positive => model better.

    Null is NOT 'model == market' (that has zero variance and is degenerate).
    Null is 'model is an independent forecaster of equal skill'.
    """
    rng = random.Random(seed)
    out = []
    for _ in range(reps):
        s = 0.0
        for _ in range(n_games):
            p = rng.uniform(0.30, 0.70)          # totals cluster near 50/50
            pm = _clip(p + rng.gauss(0, market_noise))
            pd = _clip(p + rng.gauss(0, model_noise))
            y = 1 if rng.random() < p else 0
            s += (pm - y) ** 2 - (pd - y) ** 2
        out.append(s / n_games)
    return out


# ---- metric 2: selected-subset EV -------------------------------------------
def selected_ev(model_noise, market_noise, n_games, lpg=LINES_PER_GAME, seed=11):
    """P&L per bet over the subset where |model_p - market_p| > VIG."""
    rng = random.Random(seed)
    pnl = []
    for _ in range(n_games):
        base = rng.uniform(0.30, 0.70)
        for _ in range(lpg):
            p = min(max(base + rng.gauss(0, 0.12), 0.02), 0.98)
            pm = _clip(p + rng.gauss(0, market_noise))
            pd = _clip(p + rng.gauss(0, model_noise))
            e = pd - pm
            if abs(e) <= VIG:
                continue
            y = 1 if rng.random() < p else 0
            if e > 0:
                pnl.append((1 - pm - VIG) if y else -(pm + VIG))
            else:
                pnl.append((pm - VIG) if not y else -((1 - pm) + VIG))
    return pnl


def n_star(pnl):
    """APR-0024 variance-derived sample size: 95% power, alpha=.05 one-sided."""
    m, sd = st.mean(pnl), st.pstdev(pnl)
    if m <= 0:
        return None
    return ((1.645 + 0.842) * sd / m) ** 2


def main():
    print("=" * 78)
    print("METRIC 1 — BRIER vs market, n=%d games (gate 2.3 as written)" % N_GAMES_ARCHIVE)
    print("model = NEAR-PERFECT (noise 0.005): an upper bound on achievable skill.")
    print("=" * 78)
    print(f"{'mkt noise':>9} {'mean dBrier':>12} {'crit(5%)':>9} {'power':>6}  verdict")
    effects = {}
    for mk in (0.03, 0.05, 0.08, 0.12, 0.20):
        null = paired_brier(mk, mk, N_GAMES_ARCHIVE)
        crit = st.mean(null) + 1.645 * st.pstdev(null)
        alt = paired_brier(0.005, mk, N_GAMES_ARCHIVE)
        pw = sum(1 for x in alt if x > crit) / len(alt)
        effects[mk] = (st.mean(alt), st.pstdev(null))
        print(f"{mk:>9.3f} {st.mean(alt):>+12.5f} {crit:>9.4f} {pw:>6.2f}  "
              f"{'DETECTABLE' if pw >= 0.8 else 'UNDERPOWERED'}")

    print("\nGames required for 80% power (se scales 1/sqrt(n)):")
    for mk, (eff, se) in effects.items():
        need = N_GAMES_ARCHIVE * ((2.487 * se) / eff) ** 2
        print(f"  market noise {mk:.3f}: effect {eff:+.5f} -> ~{need:,.0f} games"
              f"   (archive 214 · full MLB season 2,430)")

    print()
    print("=" * 78)
    print("METRIC 2 — SELECTED-SUBSET EV, same %d games (proposed gate)" % N_GAMES_ARCHIVE)
    print("=" * 78)
    print(f"{'mkt':>5} {'model':>6} {'bets':>6} {'pnl/bet':>9} {'sd':>6} {'n*':>9}  verdict")
    for mk in (0.03, 0.05, 0.08):
        for mn in (0.005, 0.02):
            s = selected_ev(mn, mk, N_GAMES_ARCHIVE)
            if len(s) < 30:
                print(f"{mk:>5.2f} {mn:>6.3f} {len(s):>6}  too few bets")
                continue
            m, sd = st.mean(s), st.pstdev(s)
            ns = n_star(s)
            if ns is None:
                print(f"{mk:>5.2f} {mn:>6.3f} {len(s):>6} {m:>+9.4f} {sd:>6.3f} "
                      f"{'n/a':>9}  NEGATIVE EDGE (see caveat)")
                continue
            v = ("POWERED by archive" if len(s) >= ns
                 else f"short {ns - len(s):,.0f} bets (~{ns / (len(s) / N_GAMES_ARCHIVE):,.0f} games)")
            print(f"{mk:>5.2f} {mn:>6.3f} {len(s):>6} {m:>+9.4f} {sd:>6.3f} {ns:>9,.0f}  {v}")

    print("""
CAVEAT, stated because it is a real limit of this simulation and not a finding:
the mkt=0.03 / model=0.005 row shows NEGATIVE edge for a near-perfect model. That
is a selection artifact — when model noise is far below market noise, |model-market|
is dominated by MARKET noise, so the filter selects on the market's error rather
than the model's information, and pays vig on the mistakes. Real selection would
condition on model confidence, not raw disagreement. Do not read that row as
"a perfect model loses money"; read it as "raw-disagreement selection is the wrong
selector at high model skill." The powered/underpowered conclusion does not depend
on this row.""")


if __name__ == "__main__":
    main()
