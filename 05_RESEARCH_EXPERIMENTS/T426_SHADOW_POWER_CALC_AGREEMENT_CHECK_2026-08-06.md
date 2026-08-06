# T-426 — Shadow Decoupled-Store Power-Calc: Task 1 Agreement Check FAILED

**Date:** 2026-08-06 | **Task:** T-426 | **Branch:** `session/20260806T051203Z-shadow-power-calc`

## Outcome

**Task 1 (agreement check) did not pass.** Per the task's explicit scope fence — "if they
disagree, that discrepancy is the finding and it outranks the rest of this task" — Task 2
(full-population Brier/calibration, fired vs. declined) and Task 3 (n-for-verdict comparison)
were **not run**. No shadow figure from this session should be treated as governance-grade. This
document is the deliverable in full.

**A new governance gap was registered as a direct result: GG-166 (CRITICAL).** It is more
severe than a shadow-measurement discrepancy — it shows the live paper-trading ledger's own
resolution engine has been silently grading a meaningful fraction of T4M-PROJ positions against
the wrong day's box score. See `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-166 for the full record.

## Mandatory caveats (carried forward verbatim from the task brief)

**(a) The cycle log is FROZEN at 64,396 rows by GG-163** (ESPN 403s, 723/723, since
2026-08-04T23:41Z). This session measured a static file. A stable row count is *not* evidence the
daily-refresh path works — it has not been exercised against a growing log since GG-163 began.

**(b) The unresolved-ticker count is a floor, not a settled number, per GG-163's second consumer**
(`run_resolve_mlb.py`'s own ESPN fallback shares the same blocked UA). The precondition doc
(`DECOUPLED_MEASUREMENT_STORE_2026-08-05.md`) cited 1,943/2,021 resolved (96.1%, 78 unresolved).
This session's completed store build measured **1,938/2,021 resolved (95.9%), 83 unresolved** —
five more unresolved than the precondition doc's figure, on the same frozen log. This drift is
consistent with caveat (b): the resolvable set can shrink between runs even with no new data,
because whether a given ticker resolves depends on transient upstream API state (MLB Stats API
`FINAL`-status gating, GG-069), not just on the frozen row set. **Treat 95.9% as the current
floor, not 96.1%.**

## Task 1 — Agreement check

### Setup

- **Ledger:** `logs/t4_mlb_resolved_ledger.jsonl`, filtered to `band == "T4M-PROJ"`, resolved
  (`outcome in {WIN, LOSS}`, `model_p is not None`), and clean
  (`is_clean_for_band(logic_epoch, "T4M-PROJ")`, floor = epoch 12 per GG-149).
- **Store:** `logs/t4_mlb_outcome_store.jsonl` (T-421, this session's completed build — 2,021/2,021
  tickers attempted, 1,938 resolved).
- **Join:** ledger position's `kalshi_ticker` → store row keyed by `ticker`.
- **Baseline reconciliation ledger figure** (from an unmodified re-run of `run_power_calc.py`,
  `exp_output/T323-POWER-CALC/power_calc_results.json`):
  ```
  [T4M-PROJ] clean_n=157 (raw_n=2193), n*=267, needs 110 more.
  mean_pnl/bet=$+0.3793, stdev_pnl/bet=$1.8821, cadence=275.2/wk
  ```

### Definitional reconciliation (per the task brief's instruction to check this before concluding either number is "wrong")

The brief flagged two candidate reasons for a numeric gap that would *not* indicate a real
problem: (1) the ledger counts **positions**, the store counts **tickers**, and one ticker can
carry more than one position; (2) clean-epoch filtering is ledger-side only, the store has no
epoch concept. Both were checked and **neither explains the actual disagreement found**:

- Clean cohort: 157 clean positions → 93 unique tickers (confirms candidate reason 1 is real —
  tickers do carry multiple positions, e.g. threshold-1 and threshold-2 variants of the same
  player/game). 156/157 positions matched a resolved store row (1 position's ticker was
  unresolved in the store).
- But candidate reason 1 only explains *why* n_positions ≠ n_tickers — it does not explain why a
  ticker's `actual_hits` value itself would differ between the two sources. `actual_hits` is a
  per-game fact (how many hits the player got), not a per-threshold or per-position fact, so it
  should be identical across every position sharing a ticker's game, regardless of clean-epoch
  filtering. It is not.

### Result: large, non-trivial disagreement

Of **156 matched, store-resolved positions**:

| Comparison | Agree | Disagree | Disagree rate |
|---|---|---|---|
| `actual_hits` (ledger vs. store) | 87 | **69** | **44.2%** |
| Derived `outcome` (WIN/LOSS, re-derived from store's `actual_hits` + ledger's own threshold/direction) | 109 | **47** | **30.1%** |

This is not measurement noise. It is the finding.

### Root cause: confirmed, not merely hypothesized

Checked whether disagreement correlates with a mismatch between the ledger's own `game_date`
field and the true game date embedded in that position's `kalshi_ticker` (Kalshi's
`KXMLBHIT-{YYMONDD}...` ticker format reliably encodes the real date — this is the same
ticker-derived-date technique GG-164 used to characterize the cycle log's `game_date` corruption):

```
rows_checked=156
hits_agree    & ledger_game_date==ticker_date:   49
hits_agree    & ledger_game_date!=ticker_date:   38
hits_disagree & ledger_game_date==ticker_date:    0
hits_disagree & ledger_game_date!=ticker_date:   69
```

**100% of the 69 hit-disagreements occur exactly when `game_date` is corrupted. 0% of
date-matched positions disagree.** This is a clean, mechanistic correlation, not a
coincidence — and it is fully explained by code, not just data:

1. `run_t4_mlb_live.py:1519` stamps `game_date = date.today().isoformat()` — UTC wall-clock at
   write time — onto the position record at bet-entry. This is the exact GG-164 bug pattern
   (most MLB games span the UTC midnight boundary, so `game_date` is off-by-one for the majority
   of positions by construction).
2. `run_resolve_mlb.py`'s `_fetch_mlb_hits()` (lines ~193-221) later queries the MLB Stats API
   using that same corrupted `game_date` as an **exact-match key** against
   `split.get("date") == game_date` in the player's season game log.
3. When the (wrong) recorded date happens to *also* be a real game day for that player's team —
   common, since MLB teams play near-daily — the query does not fail. It silently returns a valid
   split from a **different game**, with no error, no warning, and no distinguishable signal in
   the resulting record.
4. Sample (`Yordan Alvarez`, `KXMLBHIT-26JUL312015TEXHOU-HOUYALVAREZ44-*`): ledger records
   `game_date="2026-08-01"`; the ticker's true date is `2026-07-31`; ledger `actual_hits=1.0`
   (from whatever game Aug 1 resolved to); the decoupled store, deriving date from the ticker,
   correctly resolves the July 31 game and gets `actual_hits=2.0`.

**This directly contradicts GG-164's own "why it survived" field**, which asserted the field
"isn't used as a resolution join key anywhere in the existing pipeline." It is — via the
ledger's own `game_date`, propagated from the same write-time bug, consumed by
`run_resolve_mlb.py` as the literal resolution key. See GG-166 for the full record.

### Shadow figures (informational only — NOT governance-grade, gate failed)

Restricted to the 156-position matched cohort, using the ledger's own recorded `pnl` (the store
has no price/stake data, so this is not an independent P&L recomputation — it is the same pnl
figures already in the ledger, just re-aggregated over the store-corroborated subset):

```
shadow_clean_n_positions = 156
shadow_mu_pnl_per_bet    = $0.3881
shadow_sigma_pnl_per_bet = $1.8849
```

These are close to the `run_power_calc.py` baseline ($0.3793 / $1.8821) *only because pnl itself
was not recomputed* — they inherit whatever error is already baked into the ledger's `pnl` field
for the 44% of positions with wrong `actual_hits`/`outcome`. Closeness here is not evidence of
correctness; it would look the same whether or not GG-166's corruption exists, since this figure
never independently recomputes pnl from the store's own hit values. This is exactly why Task 1
gates Task 2/3: a superficial "the shadow number looks similar" check would have missed the
real problem entirely.

## What this means for GG-004 / the G6 gate

The current T4M-PROJ power-calc baseline (`clean_n=157`, `mean_pnl/bet=$+0.3793`) is the number
the commercial-validation gate (APR-0024, GG-004) is being evaluated against. If a comparable
~30-44% fraction of the full 157-position clean cohort carries wrong outcome/pnl (this session
only directly verified the 156/157 subset that also matched a resolved store row), the mean,
stdev, and resulting `n*` are all unverified as currently computed. **Recommend treating GG-166
as a G6 blocker alongside GG-004** until the ledger is re-resolved against the corrected or
ticker-derived date and the power-calc baseline is recomputed.

## Scope fence compliance

Read-only. No `src/` changes. `run_power_calc.py` was not modified — its baseline was reproduced
via an unmodified run, and Task 1's shadow computation was built alongside it in a separate
script (`scripts/run_t426_shadow_power_calc.py`). Task 2/3 scripts
(`scripts/run_t426_full_population_calibration.py`) were written in a prior session but were
**not executed** this session, per the explicit instruction that a failed Task 1 makes the
discrepancy the entire deliverable.

## Files

- `scripts/run_t426_shadow_power_calc.py` — Task 1 script (run, output captured above).
- `scripts/run_t426_full_population_calibration.py` — Task 2/3 script, written, **not run**
  (gated by Task 1's failure).
- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-166 (new, CRITICAL).
- `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` — 2026-08-06 T-426 entry.
