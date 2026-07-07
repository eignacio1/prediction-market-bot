# EXP-017B — Edge Decomposition of the Tier-1 T1 MLB Book

**Date:** 2026-07-06 **Parent:** EXP-017 / GG-004 / ADR-0024
**Data:** `logs/.vps_portfolio_cache_mlb.json` (live VPS book, 151 unique resolved MLB positions, game-days 2026-06-30 → 2026-07-05)
**Script:** `scripts/run_exp017b_decomp_mlb.py` (deterministic, seed=17, 10k bootstrap; md5-stable across runs)
**Status:** Analysis only. Nothing written to shared navigation/governance files — Earl decides what to log.

---

## The question

EXP-017 produced a headline verdict: n=151, EV/bet **+$0.1009**, WR 49.7%, PnL **+$15.23**, `DIRECTIONAL_POSITIVE`, ADR-0024 Tier 1 reached. Before building any enhancer (PAM, psych gradients, multi-factor formulas), decompose that number: **is the edge broad, or a favourable subset?**

Verdict: **Not broad. The edge is real but tail-concentrated, non-monotonic, and not statistically established at the aggregate.** The Tier-1 milestone stands as a milestone; the underlying edge does not yet stand as a proven, calibrated signal.

Methodology matches EXP-017 exactly (same filters, same dedup by ticker, dollar EV/bet = Σpnl/n). `fee_net_edge` recomputed direction-aware per GG-077. Two metrics reported throughout: **dollar EV/bet** (official) and **pnl-per-$1-staked** (sizing-neutral), because YES bets are ~2× larger and a losing bet forfeits full stake — so the dollar metric is sizing-confounded.

---

## Finding 1 — The aggregate +$0.10 is not distinguishable from zero

Bootstrap 95% CI on dollar EV/bet = **[−$1.86, +$2.13]**, P(EV>0) = **53.4%**. The point estimate is positive; the interval straddles zero by a wide margin. At n=151 the book is a near-coin-flip on the dollar metric. This does not contradict Tier 1 (which is a sample-size gate, not a significance gate) — but it means "positive EV" is a point estimate, not an established fact.

## Finding 2 — The entire edge is on the NO side; YES is actively destructive

| dir | n | WR | $/staked | PnL | P(EV>0) |
|-----|----|------|----------|--------|---------|
| NO  | 140 | 52.1% | **+8.71%** | **+$125.50** | 80.9% |
| YES | 11 | 18.2% | **−62.11%** | **−$110.27** | 0.5% |

11 YES bets (7% of the book) erase ~88% of the NO book's profit. This is **not** a sizing artifact — YES is −62% *per dollar staked*. Fisher YES-vs-NO win-rate p = 0.056 (borderline significant even at n=11). The YES signal is anti-predictive in this sample.

## Finding 3 — The edge signal is NON-MONOTONIC (the real scientific flag)

A calibrated edge signal should be monotonic: more model edge → more realized profit. It isn't. By recomputed fee-net-edge bucket (pnl-per-$1-staked):

| edge bucket | n | $/staked |
|-------------|----|----------|
| ≤0 | 3 | −100% |
| (0, 0.03] | 42 | +7.8% |
| (0.03, 0.06] | 41 | **−23.3%** ← negative mid-band |
| (0.06, 0.10] | 45 | −5.1% |
| >0.10 | 20 | **+34.3%** |

The **mid-conviction band loses** while the extremes behave. This is a calibration defect, not just variance — n=41 in the losing (0.03,0.06] bucket is not tiny. The model's medium-edge calls are its worst calls.

## Finding 4 — Profit is concentrated in ~20 bets; strip them and the book is negative

| view | n | $/staked | PnL | P(EV>0) |
|------|----|----------|--------|---------|
| Full book | 151 | +0.94% | +$15.23 | 53.4% |
| NO only | 140 | +8.71% | +$125.50 | 80.9% |
| **NO minus conviction tail (>0.10)** | 121 | **−2.03%** | **−$21.84** | 41.2% |
| **Full minus conviction tail (>0.10)** | 131 | **−9.39%** | **−$116.03** | 14.3% |
| Clean book (NO ∩ edge>0) | 137 | +9.02% | +$129.66 | 81.5% |

The 20-bet conviction tail (fne>0.10) holds **+$131.26 — more than 100% of the book's net**. Within it, **6 bets** (tail ∩ mip≥0.70) carry **+$85.98**. Remove the tail and every remaining view goes negative. So ~13% of the book is carrying the result, and ~4% (6 bets) carries the majority of it.

## Finding 5 — Supporting patterns

- **Win rate is a misleading health metric here.** k=2 (2+ hits) wins 66.7% but loses money (−4.35%/$); k=1 wins 35.4% but makes money (+8.83%/$). Payout asymmetry dominates raw hit rate.
- **Edge is contrarian-at-high-mip.** NO bets at mip≥0.70 return +64.7%/$ (n=20); NO bets at mip<0.30 return −13.2%/$ (n=48). The model earns when it fades a market that strongly expects a hit.
- **Possible decay (low power).** Early game-days +15.5%/$, late −7.9%/$. Only 5 days / ~30 bets each — flagged, not concluded. Could be the tail bets happening to land early.
- **T2/T3 overlays contributed nothing.** `t3_signal` = NEUTRAL and `probable_injury_signal` = False on all 151 positions. Ties directly to GG-027 (PAM/environment-classifier not wired into live T2/T3). No qualitative signal is currently reaching the book.

---

## Assumptions

- The cached VPS book (151 closed) is the same population as the GG-004 2026-07-06 re-run. **Verified**: headline reproduces to 4 dp ($0.1009, 49.67%, $15.23).
- `pnl` and `size_usd` as stored by `paper_trader.py` are correct. Not independently re-derived from resolution outcomes here (see Risks).
- Bootstrap CIs share one seeded RNG stream across splits → order-dependent but fully deterministic; interval widths are large enough that offset is immaterial.

## Key Risks

- **n is small and the tail is smaller.** The entire positive result rests on ~20 bets whose own bootstrap CI ([−$3.57, +$16.86]) straddles zero. Do not over-fit to this shape.
- **Survivorship / regime.** 5 consecutive early-July game-days is one market regime. The contrarian-high-mip pattern may not generalize.
- **Acting on subgroups mines noise.** These splits are exploratory, not pre-registered. Any rule derived here (e.g., "only bet fne>0.10") must be validated forward on fresh bets, not backtested on this same set.

## Validation Checks (done)

- Headline reproduces exactly vs GG-004. ✅
- Invariants: subgroup n sums to 151 across every split; direction PnL sums to total (±1e-6). ✅
- Determinism: identical md5 across repeat runs. ✅
- fee_net_edge recomputed direction-aware (GG-077), not read from stored field. ✅

## Confidence

- **High** that the edge is NOT broad — it is tail-concentrated, NO-only, and non-monotonic. Multiple independent cuts agree.
- **High** that YES should be quarantined pending investigation.
- **Medium** that the >0.10 conviction tail is a *real* repeatable edge vs a lucky 20 bets — the tail CI straddles zero; this is the single most important thing to resolve with more sample.
- **Low** on the time-decay signal (underpowered).

---

## Recommended next actions (for Earl to approve)

1. **Quarantine YES bets** in the MLB book pending a root-cause pass — they are ~significantly anti-predictive and cost the book $110. (Cheap, high-value, config-level.)
2. **Investigate the non-monotonic mid-band** (0.03–0.06 edge). This is the calibration question that gates every enhancer: if the base edge signal isn't monotonic, enhancers layer onto a miscalibrated axis. Prime candidate for the Platt-recalibration / feature-review track.
3. **Prioritize the >0.10 conviction tail for forward validation** — it is the only clean positive signal. Tag new bets ≥0.10 edge and watch whether the tail holds out-of-sample. This is the fastest path to converting the Tier-1 milestone into a defensible edge claim.
4. **Do NOT start enhancer builds (PAM, psych gradients) until #2 is understood.** Also note Finding 5: T2/T3 qualitative signal isn't even reaching the book (GG-027) — that wiring gap is a prerequisite, consistent with the earlier outlook.
5. **Re-run this decomposition on a schedule** as sample accumulates toward Tier 2 (n≥500) — it is the standing internal-validity companion to EXP-017.
