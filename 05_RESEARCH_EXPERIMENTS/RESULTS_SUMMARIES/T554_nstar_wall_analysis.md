# T-554/GG-285 — n*-Wall Gate-Reachability Analysis

**Tier:** STANDARD. Analysis and decision request. No gate, threshold, parameter, or pre-registered verdict is changed by this document. EXP-027's `UNDERPOWERED` verdict stands unmodified.

**Date:** 2026-09-17. **Data:** fresh VPS pull this session (`.vps_portfolio_cache_mlb.json`, `.vps_portfolio_cache_mlb_t4.json`) via `scripts/run_power_calc.py --out exp_output/T554-POWER-CALC`; NFL figures from `exp_output/NFL/exp027_hyp012_result.json` (T-550, 2026-09-15/16 re-run, unmodified).

---

## Deliverable 1 — the wall, per cell

| Cell | clean_n | mean $/bet | sd $/bet | sd/mean | n* | n* in real cadence |
|---|---|---|---|---|---|---|
| T1 | 0 (raw_n=466) | — | — | — | not computable (clean_n<2) | — |
| T2 | 0 (raw_n=2) | — | — | — | not computable (clean_n<2) | — |
| T3 | 0 (raw_n=0) | — | — | — | not computable (clean_n<2) | — |
| T4M-PROJ | 765 (raw_n=2994) | $0.05193 | $1.46279 | 28.17x | 8,587 | **43.3 weeks ≈ 10.0 months ≈ 1.6–1.7 MLB seasons** |
| NFL moneyline (EXP-027) | 14 (n_prospective_resolved=16) | $0.03214 | $0.49920 | 15.53x | 2,610.35 | **≈197.4 weeks ≈ 45.6 months of active game-time ≈ 11.0 NFL seasons ≈ ~11 elapsed calendar years** |

**T1/T2/T3:** variance is not estimable at all — `clean_n<2`. T1's `raw_n=466` with `clean_n=0` is the known epoch-contamination pattern (GG-124); T2 has essentially never traded (`raw_n=2`); T3 has never traded (`raw_n=0`). These three cells do not have a wall — they have no measurement at all. That is a worse starting position than a large-but-distant n*, not a better one.

**T4M-PROJ cadence derivation:** measured directly by `run_power_calc.py` from the clean cohort's own observed timestamp span — 765 clean bets over a 26.995-day span = 198.37 bets/week (`cadence_immature=false`, span exceeds the 14-day maturity floor). `n*/cadence = 8587 / 198.37 = 43.30 weeks`. Converting to months (÷4.348 weeks/month) = 9.96 months. Converting to MLB seasons (regular season ≈ 26–27 weeks, April–early October): 43.30/26.5 ≈ 1.63 seasons.

**NFL cadence derivation:** the backtest script has no span-based cadence measurement (unlike `run_power_calc.py`), so this is derived from the cohort's own observed clean rate applied to the season's known schedule size — not measured over a multi-week span, since only Week 1 has resolved. Clean rate = 14/16 = 0.875. Season-wide clean games ≈ 272 × 0.875 ≈ 238. NFL's 272 games run across an 18-week regular season ⇒ ≈15.11 games/week scheduled ⇒ ≈13.22 clean games/week. `n*/cadence = 2610.35 / 13.22 ≈ 197.4 weeks ≈ 45.6 months of active game-time`. In season units: 197.4/18 ≈ **10.97 ≈ 11.0 NFL seasons**.

**Important distinction the "months of active cadence" figure obscures:** NFL games only occur ~18 of 52 weeks a year. 45.6 months of *active* game-time does not mean 45.6 months of *elapsed calendar time* — it means roughly 11 full NFL seasons, each contributing ~4.15 months of active play separated by ~8 months of dead time. Elapsed wall-clock time to close this gate, at one season per year, is **~11 calendar years**, not ~3.8. This is the single most consequential number in this analysis and is stated explicitly because "45.6 months" alone reads far more tractable than it is.

---

## Deliverable 2 — is P&L-per-bet the right gate statistic? (calculation shown, gate not challenged)

EXP-027's own reported calibration reads are already informative at sample sizes where the P&L gate is nowhere close: 2025 backtest, `n=284`, Brier=0.2210, ECE=0.0661; 2026 prospective, `n=16`, Brier=0.2290, ECE=0.1739. Both are conventional, actionable calibration reads at those sample sizes in the forecasting literature. Neither n is remotely adequate for P&L (`n*=2610.35`).

**Quantified gap, using the same variance-derived formula APR-0024 already uses (`n* = ((z_α+z_β)·σ/μ)²`), inverted to ask: what σ would P&L need in order for its own current sample size to already be adequate — i.e., to match the sample size at which calibration is already read as informative?**

*NFL — target n = 284 (the size at which Brier/ECE are already treated as informative):*
```
σ_required = √n · μ / (z_α+z_β) = √284 · 0.03214286 / 3.28971 = 16.8523 · 0.03214286 / 3.28971 ≈ 0.1647
```
Observed σ = 0.49920. **The observed σ is 3.03x larger than what would already be adequate at n=284** (0.4992/0.1647 = 3.03; squared = 9.19 ≈ 2610.35/284, self-consistent).

*T4M-PROJ — target n = 765 (its own current clean_n):*
```
σ_required = √765 · 0.05193307 / 3.28971 = 27.6586 · 0.05193307 / 3.28971 ≈ 0.4366
```
Observed σ = 1.46279. **The observed σ is 3.35x larger than what would already be adequate at n=765** (1.4628/0.4366 = 3.35; squared = 11.23 ≈ 8587/765, self-consistent).

**Why the gap exists (structural, not a proposal to change the gate):** Brier score and ECE are bounded statistics — each per-observation term lies in `[0,1]` by construction, because they measure forecast-outcome distance directly. P&L-per-bet carries payoff variance on top of forecast error: a win pays out at the market's implied odds (a multiplicative factor that can be several multiples of stake) and a loss forfeits the stake outright. That multiplicative payoff structure is what pushes real σ to 15–28x the mean, not the underlying forecasting skill — EXP-027's own Brier/ECE numbers show the forecasting skill itself is measurable at n in the low hundreds. A rigorous forward Brier-specific n* (rather than this inversion) would require raw per-game squared-error values, which are not retained in `exp_output/NFL/exp027_hyp012_result.json`; only the aggregate is stored. A conservative Popoviciu bound on a `[0,1]`-bounded statistic (σ≤0.5, the maximum possible) is too loose to use for comparison — it would put a worst-case calibration n* in the same order of magnitude as P&L's, but that bound assumes the model is maximally uncertain and wrong half the time, which contradicts the same data showing accuracy 0.56–0.61. The honest statement is: the inversion calculation above is rigorous and uses only reported numbers; a literal forward n* for Brier/ECE is directionally supportive (bounded metrics structurally cannot reach P&L's variance) but not computable to the same precision without raw per-game data this session does not have access to and is not in scope to regenerate.

**This is not a proposal to replace the gate.** It establishes the size of the difference for the APR to carry.

---

## Deliverable 3 — the strategic consequence, cell by cell

**G6 as currently written cannot close on P&L evidence within any practical horizon for either cell with a measurable wall:**

- **T4M-PROJ:** TRUE. ~1.6–1.7 MLB seasons of continuous, uninterrupted cadence at the *current* measured rate (198.4 clean bets/week) is required just to reach `n*`, before any consideration of whether the sign or magnitude of the edge holds up over that horizon. This is the least-bad cell — over a year, not over a decade — but "not over a decade" is not the same as "practical." A single-digit number of MLB seasons at the bot's single existing cell is still a multi-year commitment before G6 can close on P&L alone.
- **NFL moneyline (EXP-027):** TRUE, more severely. ~11 NFL seasons / ~11 elapsed calendar years at the current clean rate. This is not a practical horizon under any reasonable definition — it exceeds the operating life of most systems in this space, let alone a single operator's iteration cycle.
- **T1, T2, T3:** TRUE by construction, and worse than either measured cell — there is no `n*` to even project against, because there is no variance estimate. A wall you can measure is at least a wall you can plan against; T1/T2/T3 do not have that.

**Is there a cell where this is NOT true?** No — not among the cells with any resolved data. **Naming the cell "worth prioritizing" on this evidence is therefore not a matter of finding one where the wall is already reachable; none is.** It is a matter of relative severity: T4M-PROJ's wall (≈1.6 seasons) is roughly 6–7x shorter than NFL moneyline's (≈11 seasons), and unlike T1/T2/T3 it has an actual, positive, currently-measured mean. If the coverage target's ~25-cell expansion is weighed against this analysis, **T4M-PROJ is the cell where continued cadence is closest to closing the gate on its own evidence** — not because it is close in absolute terms, but because every other cell is either categorically worse (T1/T2/T3: no data) or an order of magnitude further (NFL: ~7x the wait).

**The coverage target compounds the problem, not dilutes it.** Each of the ~25 target cells starts its own P&L clock from `clean_n=0` on activation. If NFL moneyline's own wall is representative of what a new, thinly-attended-relative-to-props game-market cell looks like, each new cell added under the current gate is a multi-year-to-decade-plus P&L commitment, running in parallel with T4M-PROJ's own ~1.6-season wall, none of which close early under the gate as written.

---

## Deliverable 4 — APR

Drafted, not decided: `00_ADMIN/APR-0035_pnl_gate_reachability_decision_request.md`.
