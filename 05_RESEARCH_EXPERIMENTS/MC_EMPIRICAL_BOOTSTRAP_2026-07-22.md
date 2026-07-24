# Empirical-Bootstrap Forward Monte Carlo — Projection Report
**Date:** 2026-07-22  |  **Engine:** `scripts/mc_empirical_bootstrap.py`  |  **Sims:** 100,000/path-set  |  **Seed:** 20260722
**Data:** live VPS ledger caches (`.vps_portfolio_cache_mlb.json`, `.vps_portfolio_cache_mlb_t4.json`), refreshed 2026-07-22.

---

## Why this replaces the old MC
`mc_forward_projection.py` (GG-071/ADR-0040) drew **every** bet from one fixed win rate (0.5306) and one fixed payoff multiple (+115.8%/−100%), as a clean IID +EV coin. That crushes the real per-bet payoff spread and hard-codes an edge GG-105 says is not real — and it compounded a fantasy (**+$294k mean ending bankroll on a $1k book**).

**This engine** resamples the **real resolved bets**. Per-bet fractional bankroll impact `frac_i = pnl_i / bankroll_at_resolve_i` (reconstructed by walking the ledger in resolve order). It preserves the true win rate, the true payoff spread, and the true (anti-predictive) edge structure — because it replays what actually happened. Daily P&L is aggregated over the real cadence in log-space (per-bet empirical mean/variance preserved exactly; the daily total of 16–63 bets is a genuine near-normal sum). Real kill switches applied: **permanent 20% peak-drawdown** + **15% intraday daily-loss breaker**. Books modeled independently (dual-ledger). Start $1,000 each (normalized, per operator). Horizons 30/90/182/365 calendar days at current pace.

## The real per-bet edge (this is the whole story)
| Book | Cohort | n | Win rate | Mean edge %/bet | Per-bet σ |
|---|---|---:|---:|---:|---:|
| MAIN (T1/T2/T3) | **strict e8 (current)** | 32 | 43.8% | **−0.062%** | 0.92% |
| MAIN | post-fix e6–8 | 80 | 46.3% | −0.001% | 1.07% |
| MAIN | full history | 341 | 49.0% | +0.006% | 1.08% |
| T4 (T4M-PROJ) | **strict e8 (current)** | 142 | 43.0% | **−0.012%** | 0.044% |
| T4 | post-fix e6–8 | 469 | 58.0% | +0.0002% | 0.040% |
| T4 | full history | 1379 | 58.3% | +0.0017% | 0.041% |

**The current-architecture (epoch-8) edge is negative on both books.** Every cleaner-to-flatter reading sits at ~zero. There is no cohort in which the *current* deployed model shows a real positive edge.

---

## HEADLINE — strict epoch 8 (current architecture), $1,000 start, probability bands

### MAIN book (T1/T2/T3) — cadence ~15.5 bets/day
| Horizon | ~Bets | P(kill) [95% CI] | P(profit) | p5 | p25 | median | p75 | p95 | Median return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30d | 465 | **85.8%** [85.6–86.0] | 5.3% | $761 | $786 | $803 | $852 | $1,005 | −19.7% |
| 90d | 1,395 | **99.9%** | 1.5% | $760 | $785 | $799 | $836 | $925 | −20.1% |
| 182d | 2,821 | **100%** | 1.5% | $760 | $785 | $799 | $836 | $925 | −20.1% |
| 365d | 5,657 | **100%** | 1.5% | $760 | $785 | $799 | $836 | $925 | −20.1% |

### T4 book (T4M-PROJ) — cadence ~62.7 bets/day
| Horizon | ~Bets | P(kill) [95% CI] | P(profit) | p5 | p25 | median | p75 | p95 | Median return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30d | 1,880 | **56.4%** [56.1–56.7] | 0.0% | $793 | $797 | $799 | $808 | $823 | −20.1% |
| 90d | 5,641 | **100%** | 0.0% | $792 | $795 | $797 | $798 | $800 | −20.3% |
| 182d | 11,408 | **100%** | 0.0% | $792 | $795 | $797 | $798 | $800 | −20.3% |
| 365d | 22,878 | **100%** | 0.0% | $792 | $795 | $797 | $798 | $800 | −20.3% |

**Read:** at the current (negative) edge, both books are near-certain to trip the 20% permanent kill switch — MAIN within a month, T4 within a quarter. The kill switch is working exactly as designed: it stops a bleeding book. The median outcome is "stopped out at −20%."

---

## Cohort sensitivity (why the cohort choice matters)

### MAIN book
| Cohort | Mean edge | P(kill) 30d | P(kill) 365d | Median 365d | P(profit) 365d |
|---|---:|---:|---:|---:|---:|
| strict e8 | −0.062%/bet | 85.8% | 100% | $799 | 1.5% |
| post-fix e6–8 | −0.001%/bet | 53.8% | 100% | $896 | 31.2% |
| full history | +0.006%/bet | 49.8% | 100% | $919 | 36.5% |

**Structural finding (new):** even the ~**zero-edge** MAIN cohorts hit a 20% drawdown ~**100% within a year**. At ~1% per-bet volatility and 15 bets/day, pure variance trips a 20%-from-peak drawdown eventually — *regardless of edge*. The MAIN book's variance is too large relative to the 20% kill-switch for the current near-zero edge to survive. Edge alone won't fix this; the sizing/variance/kill-switch geometry has to change too.

### T4 book
| Cohort | Mean edge | P(kill) 30d | P(kill) 365d | Median 365d | P(profit) 365d |
|---|---:|---:|---:|---:|---:|
| strict e8 | −0.012%/bet | 56.4% | 100% | $797 | 0.0% |
| post-fix e6–8 | +0.0002%/bet | **0.0%** | **0.0%** | $1,054 | 80.8% |
| full history | +0.0017%/bet | **0.0%** | **0.0%** | $1,472 | 100% |

**T4 is structurally different — and more promising.** Its per-bet variance is tiny (0.04% — small stakes on a big book). At zero-to-slightly-positive edge (post-fix cohort) it **survives with 0% kill** and grinds +5%/yr. The full-history +47%/yr is **not trustworthy** — it includes the pre-vig-fix contaminated epochs (e1–e3). The honest current-clean T4 read is the post-fix cohort: roughly flat, low-variance, survivable. The problem on T4 is *edge*, not *ruin*.

---

## Assumptions
1. **Normalized $1,000 start** both books (operator directive). Real cash: MAIN $652 (down, remainder tied in 34 open positions), T4 $1,000.
2. **Cohort per-bet distribution and cadence persist** across the horizon (stationarity). 182/365d extend beyond the current MLB season — read horizons as "~N more bets at current pace," not literal calendar time.
3. Per-bet outcomes are **net of fees** (ledger `pnl` is realized net).
4. Daily aggregation is **CLT in log-space** with the exact empirical per-bet mean/variance; higher moments wash out over the horizon (sums of hundreds–thousands of bets).

## Key risks / caveats
- **Strict-e8 n is small** (MAIN 32, T4 142) → the negative mean is partly small-sample noise. This is *why* three cohorts are shown. It is nonetheless the only read of the *current* architecture, and it agrees with GG-105.
- **Kill switch evaluated at day-close** (can lag an intraday breach by ≤1 day) → reported kill probabilities are, if anything, **slightly understated** (conservative).
- Bootstrap assumes bets are **exchangeable within a cohort** — real within-game/within-day correlation is not modeled; true tail risk may be marginally higher.

## Validation checks
- Internal consistency verified: cohorts with 100% kill but non-zero P(profit) reconcile (paths that ran >25% above start before being killed freeze at 0.8×peak > $1,000).
- Kill dynamics scale correctly with drift and variance across all six cohorts (negative-drift → fast certain kill; zero-drift high-variance MAIN → certain-but-slower kill; zero-drift low-variance T4 → survives).
- Engine reproduces the mechanical point of the old MC (variance drives tails) without its fatal fixed-multiple/fixed-winrate error.

## Confidence
**Medium-High** that the current deployed model has **no positive edge** on either book (three independent cohorts + GG-105 agree). **High** on the structural finding that the MAIN book's variance-vs-20%-DD geometry self-terminates even at zero edge. **Medium** on the exact strict-e8 kill *magnitudes* (small-n, stationarity). **Low** trust in the full-history T4 +47%/yr (contaminated cohort — do not cite externally).
