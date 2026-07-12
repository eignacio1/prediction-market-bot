# T-338 — clean_n vs n* Per Band, Live Publish

**Date:** 2026-07-11
**Author:** Session (Window 2, T-338/N-03)
**Status:** Published — feeds T-339 (G6 APR) and T-343 (gated recalibration trigger).
**Inputs:** `scripts/run_power_calc.py` (T-323) against a fresh live VPS pull, 2026-07-11
(`logs/.vps_portfolio_cache_mlb.json`, `logs/t4_mlb_resolved_ledger.jsonl` rebuilt via
`scripts/build_t4_resolved_ledger.py`, 582 resolved rows). Raw output committed at
`exp_output/T323-POWER-CALC/power_calc_results.json`.

---

## 0. What n* means and why it isn't the flat 30/150/500 heuristic

`n*` is the variance-derived sample size needed to distinguish edge>0 from edge=0 at
alpha=0.05 / power=0.95 (one-sided z-test), computed per band from that band's own
observed mean and stdev of P&L-per-bet: `n* = ((z_alpha + z_beta) × sigma/mu)²`. A
band with high per-bet variance relative to its mean edge needs a much larger sample
than a band with the same mean edge but tighter variance — the flat GG-004 heuristic
(Tier 1 n≥150 single-sport, Tier 2 n≥500) does not account for this at all. The gap
between the two is the entire point of this memo.

---

## 1. Live results (2026-07-11 pull)

| Band | raw_n | clean_n | mean $/bet | stdev $/bet | n* | gap to n* | cadence (bets/wk) | cadence span (days) | ETA to n* | status |
|---|---|---|---|---|---|---|---|---|---|---|
| **T1** | 230 | 81 | +$0.6243 | $9.1444 | **2,322** | 2,241 | 141.7 | 4.0 | ~15.8 wks (~3.6 mo) | IMMATURE CADENCE — provisional |
| T2 | 2 | 0 | — | — | — | — | — | — | — | INSUFFICIENT_DATA (clean_n<2) |
| T3 | 0 | 0 | — | — | — | — | — | — | — | INSUFFICIENT_DATA (clean_n<2) |
| **T4M-PROJ** | 582 | 338 | +$0.0486 | $0.4140 | **787** | 449 | 473.6 | 5.0 | **~0.95 wks (~1 wk)** | IMMATURE CADENCE — provisional |

All four rows use `MIN_N=30`-consistent methodology; `cadence_immature=true` fires on
both computed bands because both cadence spans (4.0d, 5.0d) are far short of
`run_power_calc.py`'s `MATURE_CADENCE_SPAN_DAYS=14.0` — **both ETAs are provisional
extrapolations from an immature cadence window, not settled forecasts.** Treat the
ETA column as order-of-magnitude, not a committed date.

---

## 2. The strategic read: T1 and T4M-PROJ are not on the same adequacy timeline

**T1's n* (2,322) is ~15.5× the flat Tier-1 heuristic (150) and current clean_n (81)
is only 3.5% of the way there.** This is a direct consequence of T1's variance
structure, not sample bad luck: stdev/mean ≈ 14.6 — proportional Kelly-sized bets on
a per-game band produce wide per-bet P&L dispersion, so distinguishing real edge from
noise at 95% power requires a large sample. At the current (immature, 4-day) observed
cadence of ~142 clean bets/week, closing that gap is a multi-month proposition
(~3.6 months) — and that cadence estimate itself needs to mature before it can be
trusted.

**T4M-PROJ's n* (787) is much closer to reach: clean_n=338 is already 43% of the way
there, and at observed cadence (~474 clean bets/week — this band fires far more
often per CLAUDE.md's Hard Rule 9 volume framing) the remaining 449-bet gap could
close in **about a week**, not months. T4M-PROJ's flat ~$0.47 stake produces much
tighter per-bet variance (stdev/mean ≈ 8.5, still high but proportionally lower, and
far higher bet-volume flow) than T1's proportional Kelly sizing on T1's cadence.

**Implication for T-339 (G6 re-base):** if G6 is re-based on `clean_n ≥ n*`, the two
active bands reach adequacy on radically different timelines — T4M-PROJ plausibly
within 1-2 weeks, T1 not for several months. A single flat gate date does not fit
both bands under this framework; the APR should treat per-band adequacy as
independently gating, not as a single combined G6 date. This is the central finding
this memo hands to T-339.

**T2/T3 are not yet assessable.** clean_n=0/2 respectively — both bands are either
not cron-firing under the current clean epoch or resolving too slowly to have any
clean-epoch data yet. This is a separate open question from the n* framework and is
not a T-338 finding in itself; flag for follow-up if it persists past the next
epoch-review cycle.

---

## 3. Caveats

- **Cadence immaturity.** Both computed bands' cadence spans (4.0d / 5.0d) are well
  under the 14-day maturity threshold `run_power_calc.py` itself flags. ETAs will
  shift, likely materially, as more of the clean epoch (started 2026-07-05 22:45:38
  UTC, epoch age ~6.0 days as of this pull) accumulates. Re-run this calc at epoch
  age ≥14 days (~2026-07-19/20) for a non-provisional read.
- **n* assumes the observed mean/stdev are stable.** If T1 or T4M-PROJ's underlying
  edge or variance shifts materially (e.g., after a C3 recalibration, T-343), n*
  must be recomputed — it is not a fixed target.
- **This is a live pull, not a frozen snapshot.** `power_calc_results.json` is
  regenerated (not diffed) on each run; the numbers in Section 1 will already be
  stale by the next live pull. This memo is dated specifically so it can be compared
  against future re-runs, not treated as a standing constant.

---

## 4. Exit criteria status (per iteration plan v2, T-338/N-03)

- [x] `scripts/run_power_calc.py` run live against fresh VPS-pulled data.
- [x] Dated artifact published (this memo) with clean_n / n* / ETA per band.
- [ ] Governance-hook/dashboard line surfacing clean_n / n* / ETA per band on every
      session-start scan — tracked as the remaining T-338 deliverable, addressed
      immediately following this memo in the same session.
