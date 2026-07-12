# APR-0024 — Re-base G6/Commercial-Validation Sample-Adequacy on Per-Band Variance-Derived n*

**Status:** PENDING — DS sign-off required
**Amends:** CLAUDE.md § "The commercial validation gap" / § "Gate structure" (prose only, not an ADR by
itself — see § Scope below for why ADR-0024 (stop-pivot-criterion) is flagged but not superseded here)
**Drafted:** 2026-07-11, Window 2 (T-339/N-04), session `20260711T225312Z-window2-n03-n05-cleann-gate`
**Analysis source:** T-338 (`scripts/run_power_calc.py`, live 2026-07-11 pull) —
`05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T338_CLEAN_N_VS_N_STAR_MEMO.md`
**Approved by:** [pending — DS: Earl Ignacio]
**Effective:** Upon DS sign-off; governs go-forward gate language only — does not retroactively invalidate
any evidence verdict already reached under the prior heuristic (see § Does NOT Change)

---

## Why This Amendment Is Required

CLAUDE.md currently states G6 requires "30 resolved paper bets with positive P&L" and separately cites
**ADR-0024's (stop-pivot-criterion) Tier 1 (n≥150 single-sport) / Tier 2 (n≥500)** thresholds as the bar
for the commercial-validation question (GG-004). Both of these are **fixed heuristics**, not derived from
this system's actual observed bet-level variance. ADR-0024's own Tier 1/Tier 2 derivation assumes a single
constant `σ_EV ≈ $0.25/bet` across all bands to compute its n thresholds.

T-323 (`scripts/run_power_calc.py`) replaces that assumption with the real, per-band measured variance and
computes the actual sample size needed for 95% power to distinguish `edge > 0` from `edge = 0` at
`alpha=0.05` (one-sided):

```
n* = ((z_alpha + z_beta) × sigma/mu)²
```

**Live result (T-338, 2026-07-11 pull, clean_n only — CURRENT_LOGIC_EPOCH):**

| Band | clean_n | mean $/bet | stdev $/bet | n* | vs. flat heuristic |
|---|---|---|---|---|---|
| T1 | 81 | +$0.6243 | $9.1444 | **2,322** | **~15.5× the flat 150 floor** — the $0.25 assumption dramatically *underestimates* T1's true required sample. T1's proportional-Kelly sizing produces stdev/mean ≈ 14.6, far noisier than the flat heuristic assumes. |
| T4M-PROJ | 338 | +$0.0486 | $0.4140 | **787** | ~1.6× the flat 500 floor, but already 43% of the way there at a cadence that could close the gap in ~1 week (vs. T1's ~3.6 months) — the two bands are not remotely on the same adequacy timeline under either framework. |
| T2 / T3 | 0 / 0 | — | — | insufficient data | Not yet assessable under either framework. |

**The core problem this APR addresses:** a single flat n-threshold, applied uniformly, is wrong in *both*
directions at once — it under-powers T1 (declaring "commercial validation reached" at n=150 when the real
variance-derived requirement is 2,322) and over-powers T4M-PROJ relative to its actual noise profile in the
opposite direction. Continuing to gate on the flat number risks exactly the failure mode ADR-0024 itself was
written to prevent: declaring a verdict (positive or negative) before the sample is actually adequate to
support it.

---

## Scope — what this APR does and does not touch

**This APR proposes a prose amendment to CLAUDE.md's gate narrative and MEMORY_BANK.md's gate-progress
language**, replacing references to the flat 30/150/500 heuristic with `clean_n ≥ n*` (per band, computed
live via `scripts/run_power_calc.py`).

**It does NOT supersede ADR-0024 outright.** ADR-0024 (stop-pivot-criterion) is a halt-trigger ADR — it
governs when to STOP an already-deployed strategy showing confirmed negative EV, a different decision from
G6's live-capital PROMOTION gate. Per Hard Rule 3 (ADRs are immutable; changes require a superseding ADR),
if DS wants ADR-0024's own Tier 1/Tier 2 n-thresholds and `σ_EV≈$0.25` assumption formally replaced with the
per-band `n*` methodology (rather than just having G6's separate promotion-gate prose point at `n*`), **that
is a distinct action requiring its own superseding ADR** — flagged here as an open question for DS to decide
at sign-off (see Review Checklist item 5), not pre-decided by this APR.

**Also flagged, not resolved:** CLAUDE.md's existing prose already conflates "G6 promotion" language with
ADR-0024's "commercial validation" Tier 1/2 language in a few places (e.g. citing ADR-0024 Tier 1 as if it
were itself a G6 milestone). This APR does not attempt to disentangle that conflation — it is noted so DS
can decide whether a future APR/ADR should separate "G6 live-capital promotion criteria" from "ADR-0024
stop-pivot criteria" as two cleanly distinct gates, the way APR-0022 already separated G6 from the T4
Activation Gate for the NBA-era per-bucket floors.

---

## Proposed New Gate Language

**Replaces**, in CLAUDE.md § "The commercial validation gap" and § "Gate structure", references to the flat
30/150/500 bet counts with:

> Commercial-validation and G6 sample-adequacy are evaluated per active band against `clean_n ≥ n*`, where
> `n*` is the variance-derived sample size (95% power, alpha=0.05, one-sided) computed live from that band's
> own observed clean-epoch mean and stdev of P&L-per-bet via `scripts/run_power_calc.py` (T-323). This
> replaces the flat 30/150/500 heuristic, which assumed a single `σ_EV≈$0.25/bet` across all bands — a
> materially wrong assumption for both T1 (real stdev $9.14/bet) and T4M-PROJ (real stdev $0.41/bet).
> `n*` is re-derived on every governance scan (`.claude/hooks/governance_scan.sh`, T-338) and is not a fixed
> constant — it will shift if a band's underlying mean/variance shifts (e.g. after a C3 recalibration,
> T-343).
>
> **Per-band status as of 2026-07-11 (provisional — cadence spans <14 days, re-derive at maturity):**
> T1: clean_n=81/n*=2,322 (ETA ~15.8 weeks at current cadence). T4M-PROJ: clean_n=338/n*=787 (ETA ~0.9
> weeks). T2/T3: insufficient data. **No active band currently meets `clean_n ≥ n*`.**

---

## What Does NOT Change

- **GG-004's existing DIRECTIONAL_POSITIVE Tier-1 verdict** (n=151 raw-count run, EV=+$0.1009/bet, dated
  2026-07-06) is a historical evidentiary finding reached under the prior heuristic. This APR does not
  retract or re-litigate it — it governs *go-forward* gate language only. Any claim that the commercial case
  is "proven" going forward must reference `n* `adequacy, not the historical n=150 read.
- ADR-0024's text itself (unless/until DS separately authorizes a superseding ADR per § Scope above).
- C4 risk limits, kill-switch mechanics, DS sign-off requirement (ADR-0005), or any other G6 formal
  prerequisite not related to sample-size counting.
- The per-bucket calibration floors from APR-0017/APR-0019 (T1≥66/T4≥50 eligible bets) — those are a
  different NBA-Finals-era statistical-validity mechanism (T2-A formula, calibration deviation), not the
  ADR-0024/GG-004 commercial-validation n-threshold this APR targets. DS should confirm at sign-off whether
  those floors are still live for the current MLB-active gate structure or are superseded/dormant — this APR
  does not assume either way.

---

## Broken-System Test

| Failure mode | How this APR prevents it |
|---|---|
| Declaring T1 "commercially validated" at n=150 (flat heuristic) while its real variance requires n=2,322 — a false-positive promotion risk | `n*` computed from T1's own observed stdev ($9.14/bet) directly shows the flat 150 floor is ~15.5× too low for T1 specifically |
| Sitting on T4M-PROJ's evidence for months waiting to hit a flat n=500 floor when its real, tighter variance profile only needs n=787 and could clear it in ~1 week | `n*` is computed per band, not pooled or assumed uniform — T4M-PROJ's own faster cadence and lower per-bet variance are reflected directly |
| `n*` itself being trusted before the cadence measuring it has matured, producing a falsely precise ETA | `run_power_calc.py` explicitly flags `cadence_immature=true` below `MATURE_CADENCE_SPAN_DAYS=14.0` and this APR's own proposed language carries that caveat forward rather than presenting the ETA as settled |
| A future session quietly treating T1 and T4M-PROJ as on the same timeline because they're both "G6 MLB bands" | Explicit per-band table in both this APR and the referenced T-338 memo — the ~4-month vs ~1-week gap is stated in the same sentence, not just implied by two separate numbers |

---

## Review Checklist

- [ ] `n*` methodology (T-323, `scripts/run_power_calc.py`) reviewed and accepted as the sample-adequacy
      standard for G6/commercial-validation, replacing the flat 30/150/500 heuristic in gate *prose* —
      acceptable
- [ ] Per-band live figures as of 2026-07-11 (T1 clean_n=81/n*=2,322; T4M-PROJ clean_n=338/n*=787; T2/T3
      insufficient data) reviewed — acceptable
- [ ] Historical GG-004 Tier-1 DIRECTIONAL_POSITIVE verdict (n=151) explicitly NOT retracted by this APR,
      go-forward language only — acceptable
- [ ] ADR-0024 itself is NOT superseded by this APR (prose-only amendment to CLAUDE.md/MEMORY_BANK gate
      language) — **DS decision required:** should a follow-on superseding ADR formally replace ADR-0024's
      own Tier 1/Tier 2 σ-assumption-based thresholds with the `n*` methodology, or leave ADR-0024's halt-
      trigger role as-is and treat `n*` as a separate, G6-promotion-specific standard? — pending DS choice
- [ ] The CLAUDE.md/ADR-0024 "commercial validation" vs "G6 promotion" language conflation flagged in
      § Scope is noted; DS may defer disentangling it to a future APR — acceptable to defer
- [ ] Cadence-immaturity caveat (both bands' current ETAs are provisional, re-derive at ≥14-day epoch age,
      ~2026-07-19/20) carried into the adopted gate language — acceptable

**Sign-off:** [pending]
**Date:** [pending]
**Role:** DS — Earl Ignacio
