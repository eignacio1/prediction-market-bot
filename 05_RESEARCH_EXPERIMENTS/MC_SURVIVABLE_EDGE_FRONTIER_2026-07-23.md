# Survivable-Edge Frontier — Window B2
**Date:** 2026-07-23  |  **Engine:** `scripts/mc_survivable_edge_sweep.py` (new; wraps `mc_empirical_bootstrap.py`'s real per-book ledger data)  |  **Seed:** 20260722  |  **Sims:** 8,000/grid-point, 30,000/bisection-point (see Method)
**Origin:** Window B2, `ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md` — follow-on to `MC_EMPIRICAL_BOOTSTRAP_2026-07-22.md`'s structural finding (Window B1 governance gap: MAIN book's variance × cadence trips the 20% drawdown kill ~100%/yr even at zero edge).
**Data:** live VPS ledger caches (`.vps_portfolio_cache_mlb.json`, `.vps_portfolio_cache_mlb_t4.json`), refreshed 2026-07-23 (one day fresher than the source report; MAIN strict-e8 n=55/T4 strict-e8 n=306, vs 32/142 in the 2026-07-22 report — more bets have resolved since).

---

## What this answers that the source report didn't

`MC_EMPIRICAL_BOOTSTRAP_2026-07-22.md` replayed the *observed* cohorts (strict-e8, post-fix e6-8, full-history) and found all of them near-zero-to-negative edge, both books near-certain to hit the 20% kill within a year. This sweep asks the counterfactual: **holding each book's real per-bet variance shape and real cadence fixed, what edge would need to exist, and how much room is there in Kelly-fraction / drawdown-kill-switch width / cadence, before a genuine positive edge stops getting killed by variance anyway?**

## Method

Per book, pulls the **full-history** cohort's real resolved bets (largest n → most stable variance estimate; the three cohorts' `std_frac` are within ~15% of each other per the source report, so cohort choice is not sensitive) via the existing `load_book_fracs`/`cohort_fracs`. Discards the empirical **mean** (which is what's actually being asked "what if this were different") but keeps the empirical **variance shape** (`sig_g_base = std(log1p(frac))`) — this is the book's real payoff-spread/heterogeneity, not a distributional assumption.

Three independently swept levers, each applied as a multiplier/override on the book's real baseline, using the *same* day-by-day compounding + kill mechanics as `mc_empirical_bootstrap.py` (15% intraday breaker in log-space, 20%-from-peak permanent kill at day-close):
- **`kelly_mult`** — scales both mean *and* stdev of per-bet log-return (bigger stake ⇒ proportionally bigger P&L swing at a fixed per-unit-stake edge — this is a stake-scaling model).
- **`cadence_mult`** — scales real observed bets/calendar-day (MAIN 15.83/day, T4 67.09/day as of this pull).
- **`kill_dd`** / **`daily_breaker`** — override the real risk.py 0.20 / ADR-0012 0.15 constants, sweep only, no live-code dependency.

**Part A (bisection):** minimum `target_edge` such that 1yr P(kill) ≤ 10%, holding **kelly_mult=1, cadence_mult=1, kill_dd=0.20, daily_breaker=0.15** — i.e., today's real risk config.

**Part B (grid):** for five illustrative `target_edge` scenarios (0%, +0.02%, +0.05%, +0.10%, +0.20%/bet — spanning from breakeven through a clearly-positive hypothetical; **not empirical claims**, chosen to bracket the real cohorts' near-zero mean_frac readings), sweep each lever alone (others held at real current values) and report the frontier value that holds 1yr P(kill) ≤ 10%.

This script does not touch or depend on any live `risk.py`/`execution_bands.py` constant — pure forward-looking research output, feeds a future ADR (Window B3), not self-executing.

---

## Part A — minimum edge needed at TODAY'S real sizing/cadence/kill-switch

| Book | Real cadence | Real σ (per-bet log-return) | Min edge for 1yr P(kill)≤10% | Verified P(kill) at that edge |
|---|---:|---:|---:|---:|
| **MAIN (T1/T2/T3)** | 15.83 bets/day | 1.081% | **+0.169%/bet** | 10.0% |
| **T4 (T4M-PROJ)** | 67.09 bets/day | 0.041% | **−0.0005%/bet** | 8.5% |

**Read:** MAIN needs a per-bet edge roughly **27× larger** than its best-ever observed cohort mean (full-history +0.006%/bet) just to hold 1-year kill risk at 10% — at today's sizing. This is the quantitative confirmation of the Window B1 governance gap: no plausible near-term calibration fix (Window A) closes a 27x gap in mean edge; the sizing/kill-switch geometry itself has to change (Window B3). T4, by contrast, is already near the survivability boundary at ~zero edge — confirming the source report's read that **T4 is edge-limited, not ruin-limited**: it doesn't need a sizing fix, it needs Window A's calibration fix to actually land a positive mean.

---

## Part B — Kelly-fraction / cadence / drawdown-width frontier, by assumed edge

### MAIN book (T1/T2/T3)

| Assumed edge | Max Kelly mult. survives | Max cadence mult. survives | Min DD-width survives |
|---:|---:|---:|---:|
| 0.00%/bet | **0.10×** | none up to 10× cut | none up to 50% |
| +0.02%/bet | 0.10× | none up to 10× cut | none up to 50% |
| +0.05%/bet | 0.25× | none up to 10× cut | 50% |
| +0.10%/bet | 0.50× | none up to 10× cut | 30% |
| +0.20%/bet | **1.00× (current)** | 3.0× | 20% (current) |

### T4 book (T4M-PROJ)

| Assumed edge | Max Kelly mult. survives | Max cadence mult. survives | Min DD-width survives |
|---:|---:|---:|---:|
| 0.00%/bet | 1.5× | 3.0× | 15% |
| +0.02%/bet | 3.0× (grid ceiling) | 3.0× | 10% |
| +0.05%/bet | 3.0× (grid ceiling) | 3.0× | 10% |
| +0.10%/bet | 3.0× (grid ceiling) | 3.0× | 10% |
| +0.20%/bet | 3.0× (grid ceiling) | 3.0× | 10% |

*(Full grid points behind each frontier value are in `logs/mc_survivable_edge_sweep.json`.)*

---

## The non-obvious structural finding: Kelly cuts hit variance quadratically, cadence cuts only linearly

At zero edge, cutting MAIN's stake size (Kelly fraction) to **10% of current is sufficient to survive** (P(kill)=1.2%) — but cutting bet **frequency** (cadence) to 10% of current is **not sufficient** (P(kill)=79%), and neither is widening the drawdown kill switch all the way to 50% (P(kill)=71.5%).

**Why:** total variance over a horizon accrued from N independent bets each with per-bet stdev σ is `N·σ²`. Scaling stake by `k` scales σ to `k·σ`, so total variance scales as `N·(kσ)² = k²·N·σ²` — **quadratic** in the stake multiplier. Scaling cadence by `c` instead scales `N` to `c·N` at unchanged per-bet σ, so total variance scales as `c·N·σ²` — only **linear**. A 10× cut therefore removes ~100× the variance via Kelly but only ~10× the variance via cadence. Widening the drawdown-kill threshold doesn't touch variance at all — it only gives more room before the (still-enormous) variance eventually wanders past it, which the grid confirms is nowhere near enough for MAIN's real σ at zero-to-near-zero edge.

**Implication for Window B3's ADR:** if MAIN's edge doesn't clear roughly +0.17%/bet (the Part A threshold), **Kelly-fraction reduction is the only lever with enough leverage to matter** — cadence throttling and drawdown-width widening are both order-of-magnitude too weak on their own to rescue survivability at the book's real variance. A combined fix (smaller Kelly + modest DD widening) is worth modeling in B3, but Kelly reduction should be the primary lever, not a secondary one.

T4's much smaller per-bet σ (0.041% vs MAIN's 1.081%, ~26× smaller) means all three levers have far more headroom there even at zero edge (max Kelly 1.5×, max cadence 3.0× current already survive) — consistent with T4 being edge-limited rather than sizing-limited.

---

## Caveats (inherited from the source engine + new to this sweep)

- Same caveats as `mc_empirical_bootstrap.py`: day-close kill evaluation (mildly conservative/understated kill probabilities), bootstrap exchangeability assumption (real within-game/within-day correlation not modeled), stationarity over the horizon.
- **New:** `kelly_mult` is a **stake-scaling** approximation (linear scaling of frac before `log1p`), not a probability-edge model — it holds only to the extent per-bet fracs stay small (they do, all ≤~2% even at the grid's 3× ceiling), so `log1p` linearity is a reasonable approximation here; it would not be at large fracs.
- The five `target_edge` scenarios are **illustrative brackets**, not predictions of what Window A's calibration fix will actually deliver — A2's post-fix edge estimate (not yet available) should be substituted into Part A/B once landed, per the iteration plan's resume-gate #2 ("B frontier shows the risk config admits survival at the post-fix edge").
- Grid ceilings (Kelly 3.0×, cadence 3.0×, DD 50%) were chosen to bracket the current config with headroom; T4's frontier hit the Kelly-mult grid ceiling at several edge levels (reported as "3.0× (grid ceiling)" — the true max Kelly headroom for T4 at those edges is higher than 3.0×, not measured here, since 3.0× already far exceeds any real sizing change under consideration).

## Confidence

**High** on the qualitative finding (Kelly-fraction cuts dominate cadence/DD-width cuts for ruin reduction at MAIN's real variance) — this follows from the variance-scaling algebra above, independent of the small-n cohort noise concerns that apply to the source report's cohort-specific edge readings. **Medium** on the exact Part A threshold (+0.169%/bet for MAIN) — sensitive to the assumed variance shape (full-history cohort), though cohort choice moves `std_frac` by <15% per the source report, so the threshold should not move by more than a similar order. **Medium-Low** on T4's exact frontier values at the grid ceiling (headroom beyond 3.0× Kelly not measured).
