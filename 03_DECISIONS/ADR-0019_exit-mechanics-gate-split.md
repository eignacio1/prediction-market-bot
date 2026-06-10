# ADR-0019 — Band Exit Mechanics: Implementation Gate vs Activation Gate

**Status:** ACCEPTED — APR-0019 signed 2026-06-09  
**Date:** 2026-06-09 SESSION 42  
**Decisions logged:** true  
**Author:** Claude Code  
**Approved by:** DS (Earl Ignacio) — 2026-06-09 SESSION 42  
**Supersedes:** ADR-0018 §Context final paragraph (implementation gate language only)  
**Related:** ADR-0018 (band exit mechanics framework), GG-017, T-146, T-147

---

## Context

ADR-0018 §Context states: "Code implementing exit mechanics is blocked until EXP-019 produces and validates each parameter via the methodology here."

EXP-019A analytic is COMPLETE:
- NOISE_BUFFER_BAND_T1/T2/T3 = 0.22053 (2σ_p at Q2 midpoint, σ_λ_ingame=1.45)
- NOISE_BUFFER_BAND_T4 = 0.13905 (2σ_p at Q3/Q4 firing window, σ_λ=0.5)
- NOISE_BUFFER_BAND_T5 = 0.13328 (near-deterministic final 3 minutes)

EXP-019B analytic is COMPLETE:
- 1,114 G3 T4 YES positions analyzed
- 79.9% of YES losses correctly exit (433/542)
- 0% false exits on YES wins (0/572)
- E[log_r] +0.5% lift vs hold
- **PARTIAL_KELLY = FULL_EXIT**: Kelly fraction collapses to ≈0 at exit boundary, so Policy 1 (full exit) and Policy 2 (Kelly-inverse partial exit) are equivalent. Implementation always uses full exit.

EXP-019A empirical validation (σ_p vs observed trajectory variance) and EXP-019B empirical validation (n≥50 exit events per band from real trajectories) are PENDING — blocked on ≥3 game nights of trajectory data from `logs/t4_position_trajectories.jsonl`. With 2 NBA Finals games remaining (G4 Jun 10, G5 possible), this data will be available early in the 2026-27 preseason.

ADR-0018's monolithic implementation gate creates a problem: with the dark period approaching, we cannot write code during dark period if the gate applies to implementation. The analytic derivation is strong and the parameter values are stable. Writing code now and activating later is lower risk than writing code from scratch next season with no prior analysis.

---

## Decision

**Split ADR-0018's single gate into two tiers:**

### Tier 1 — Code Implementation Gate (CLOSED as of this ADR)

**Condition:** EXP-019A analytic COMPLETE AND EXP-019B analytic COMPLETE.  
**Rationale:** The NOISE_BUFFER_BAND values are analytically derived from first principles (Poisson CDF sensitivity × σ_λ). The analytic derivation chain is documented and reproducible. EXP-019B confirms the analytic buffer eliminates false exits at 0% and captures 79.9% of genuine loss exits. These results justify writing code with hardcoded analytic constants.

**Status:** SATISFIED. T-146 and T-147 may proceed to implementation.

Constants used in implementation (flagged as pending empirical validation):
```python
NOISE_BUFFER_BAND_T4:    float = 0.13905  # EXP-019A analytic — empirical validation pending EXP-019B
NOISE_BUFFER_BAND_T1:    float = 0.22053  # EXP-019A analytic — empirical validation pending EXP-019B
NOISE_BUFFER_BAND_T2:    float = 0.22053  # same as T1 (same σ_λ basis)
NOISE_BUFFER_BAND_T3:    float = 0.22053  # same as T1
NOISE_BUFFER_BAND_T5:    float = 0.13328  # EXP-019A analytic — T5 near-deterministic
EXIT_MIN_TIME_REMAINING: float = 3.0      # no exits in final 3 min (T5 takes over)
```

### Tier 2 — Activation Gate (OPEN — pre-activation requirement)

**Condition:** EXP-019A empirical: observed σ_p in trajectory logs within 20% of analytic σ_p. EXP-019B empirical: n≥50 exit events per band (or combined if per-band n insufficient), Policy 1 exits confirmed in ≥70% of genuine loss positions. EXP-019C spread model: spread_cost_band populated for all bands.

**When satisfied:** If analytic NOISE_BUFFER_BAND values are confirmed by empirical data, activate with no constant changes. If empirical values differ materially (>20%), update constants via ADR amendment and re-run tests before activation.

**Consequence of non-satisfaction:** Constants updated via ADR; tests re-run. No code rewrite required — only constant changes.

---

## Full Exit Policy (EXP-019B finding)

EXP-019B found that Policy 2 (Kelly-inverse partial exit) is equivalent to Policy 1 (full exit always) because at the exit signal boundary, `f_star_current = max(0, (p_current - mip_current) / (1-mip_current))`. When exit fires (`mip_current > p_current + NOISE_BUFFER_BAND`), `p_current < mip_current`, so `f_star_current < 0` → clamped to 0. Kelly says "hold nothing." Full exit is always the Kelly-optimal action when the exit signal fires.

**Implementation consequence:** No partial exit logic needed. When exit signal fires → exit 100% of position.

---

## What ADR-0018 governs that this ADR does NOT change

- The exit signal formulation (Section 1) — unchanged
- The noise buffer derivation methodology (Section 2) — unchanged
- The cost model framework (Section 4) — EXIT_NET_COST_BAND still required for activation; analytic taker fee approximation used in paper implementation
- The per-band p_current computation method (Table in Section 1) — unchanged
- The T4 live cycle as universal exit evaluator — unchanged
- All parameter values specified in ADR-0018 (there were none — this ADR is first to specify them)

---

## Governance obligations created

1. T-152: Before activation — run EXP-019B empirical (n≥50 exit events), compare NOISE_BUFFER_BAND_T4 to observations. Update constants via ADR amendment if empirical value deviates >20% from 0.13905.
2. T-153: Before activation — run EXP-019C spread model (EXIT_NET_COST_BAND for time_remaining buckets) and incorporate into exit condition if materially > taker_fee approximation.
3. EXP-019B/C are now pre-activation gates, not pre-implementation gates.
