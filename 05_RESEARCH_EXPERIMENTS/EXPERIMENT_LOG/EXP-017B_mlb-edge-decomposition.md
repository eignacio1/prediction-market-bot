# Experiment Record — EXP-017B: MLB T1 Edge Decomposition

**Status:** COMPLETE
**Experiment ID:** EXP-017B (child of EXP-017)
**Owner:** RL
**Hypothesis tested:** Is the EXP-017 Tier-1 edge (+$0.1009/bet) BROAD or a favourable subset? (follow-on to GG-004)
**Research question:** GG-004 internal-validity companion
**Started / Completed:** 2026-07-06

---

## Objective

EXP-017 established a DIRECTIONAL_POSITIVE Tier-1 verdict for MLB T1. Before pivoting project focus to edge/enhancer work, decompose that aggregate along every axis the position records support, to determine whether the edge is broad or subset-driven. Not a re-verdict — a decomposition.

## Data / Code Reference

| Item | Detail |
|------|--------|
| Portfolio | `logs/.vps_portfolio_cache_mlb.json` (n=151 closed; reproduces EXP-017 headline to 4 dp) |
| Script | `scripts/run_exp017b_decomp_mlb.py` (deterministic seed=17, 10k bootstrap, md5-stable) |
| Base commit | e250a29 |
| Method | Identical to EXP-017 (filters, dedup by ticker, EV=Σpnl/n). `fee_net_edge` recomputed direction-aware per GG-077. |

## Results (summary — full table in FINDINGS)

- Aggregate EV/bet +$0.1009 but bootstrap 95% CI [−$1.86, +$2.13], P(EV>0)=53.4% — not distinguishable from zero.
- Direction: NO n=140 +8.71%/staked (+$125.50); YES n=11 −62.11%/staked (−$110.27). Fisher YES-vs-NO p=0.056.
- Non-monotonic in edge: mid-band (0.03–0.06) −23%/staked at n=41 while extremes behave.
- Tail concentration: 20 bets (edge>0.10) hold +$131.26 (>100% of net); 6 bets (tail ∩ mip≥0.70) hold +$85.98. Strip the tail → every view negative.
- T2/T3 overlays contributed nothing (t3_signal all NEUTRAL, injury_signal all False) — ties to GG-027/GG-094.

## Interpretation

Edge is NOT broad: NO-only, non-monotonic, tail-concentrated, aggregate-insignificant. Raised calibration-defect vs variance as candidate causes → resolved by EXP-017C.

## Confidence

7/10 on the decomposition conclusions (multiple independent cuts agree); small-n throughout.

## Verification

Invariants pass (subgroup n and PnL sum to totals); determinism confirmed (md5 identical across runs); headline reproduces EXP-017.

## Links

- Findings: `exp_output/EXP-017B-DECOMP/FINDINGS.md` · Results JSON: `exp_output/EXP-017B-DECOMP/exp017b_decomp_results.json`
- Parent: EXP-017 · Downstream: EXP-017C, EXP-017D · Governance: GG-004, GG-098, ADR-0042
