# T-572 — CLV Instrument: Results

**Pre-registration (immutable):** `T572_clv_harness_PREREGISTRATION.md`, pushed as commit `3773229`
prior to any statistic below being computed. Every threshold, cohort-construction rule, and
verdict criterion here is applied exactly as written there — nothing was adjusted after seeing
the numbers.

**Instrument:** `scripts/clv_harness.py` (commit `95004f5`), tested via `tests/test_clv_harness.py`
(25/25 passing, all four §7 malformed-input `raise` conditions covered).

**Data:** `logs/t4_mlb_cycle_log.jsonl`, fresh `scp` pull from the VPS this session, 404,634 rows,
ts span 2026-07-02T19:09:34Z to 2026-09-24T04:20:48Z. Raw output: `exp_output/T572_CLV_HARNESS/clv_results.json`.

---

## Deliverable 3 — Approvals CLV vs. matched control CLV

| Cohort | n | Mean CLV | 95% CI (by-ticker) | 95% CI (by-game) |
|---|---|---|---|---|
| Approvals (reconstructed `directional_net_edge >= 0.04`) | 5,551 | **+0.0064** | [-0.0019, +0.0158] | see JSON |
| Control (matched random entry, same ticker/inning-bucket, no magnitude gate) | 5,627 | **-0.0219** | [-0.0306, -0.0131] | see JSON |
| Difference (approvals − control, paired by ticker) | 5,477 | **+0.0238** | [+0.0129, +0.0341] | [+0.0133, +0.0350] |

Cohort construction diagnostics (`cohort_construction_diagnostics` in the JSON): 8,169 usable tickers
scanned (208 singleton tickers and 0 non-monotonic-timestamp rows dropped at load, per pre-reg §1);
2,456 tickers never crossed the `directional_net_edge >= 0.04` gate (no approvals entry); 86 tickers
had no viable control candidate; 272 control draws fell back off-bucket. 162 approvals rows and 0
control rows were excluded post-construction for `NoClosingObservationError` (refuse-loudly path,
§7 — none silently imputed).

**Robustness variant (§6, second-to-last-row closing price)** reproduces the same pattern: approvals
mean +0.0039, CI [-0.0056, +0.0128] (still spans 0); control mean -0.0133, CI [-0.0222, -0.0046]
(still significantly negative). The primary result is not an artifact of the specific closing-row
choice.

## Deliverable 4 — Confounds (mandatory for every number above)

**Backward placebo (§5b):** forward regression (CLV ~ signal) slope = **-0.0456**, CI [-0.0815, -0.0091]
(excludes 0). Backward regression (pre-entry move ~ same signal) slope = **-0.8836**, CI [-0.9253, -0.8344]
(also excludes 0, and is ~19.4x the forward slope in magnitude). **Ratio = 19.39, threshold = 0.50 →
FAILS.** The backward (pre-entry) relationship between signal and price move is almost 20x larger
than the forward one — whatever "signal" is correlated with, it was already present in the price
before entry, not something the market updates on afterward. This is the same qualitative failure
mode T-569 found for the latency thesis (backward placebo there ran 5.1-6.4x forward magnitude);
here it's an order of magnitude worse.

**Mean-reversion decomposition (§5a):** three-way OLS `CLV ~ signal + own_dislocation` (n=2,986 rows
with ≥3 prior observations; 2,565 rows excluded for insufficient history). `signal` coefficient =
+0.1147, CI [-0.0067, +0.2499] — **does not survive** controlling for the ticker's own trailing-mean
dislocation (CI includes 0). `own_dislocation` coefficient = -0.1752, CI [-0.2796, -0.0787] — this is
the term that's actually doing the work: entries made further above a ticker's own trailing-mean price
show more mean-reversion-like forward movement, independent of the edge-magnitude signal.

Both confound checks fail. Under the pre-registered §8 asymmetric verdict design, this matters only
for a POSITIVE classification (which is gated on both checks passing) — it does not affect the
verdict reached below, since the verdict fell out as INCONCLUSIVE, not POSITIVE.

## Verdict (mechanical application of pre-reg §8)

**Approvals cohort CLV, by-ticker CI: [-0.0019, +0.0158] — spans 0.**

n = 5,551 ≥ the 30-ticker floor, so this is not `INSUFFICIENT_N`. The CI straddles zero, so per §8
this is:

> **VERDICT: INCONCLUSIVE**

This is the mechanical output of the pre-registered criteria, applied without adjustment. It is
*not* the "cleanly measured negative" the operator's honest prior anticipated (T-569 found the wrong
sign on the latency thesis, so a negative CLV was the expected honest result here too) — the
approvals cohort's own CLV came out statistically indistinguishable from zero, not negative. What
*is* cleanly negative is the **control cohort**: blind directional entries (same sign convention,
no edge-magnitude gate) lose −0.0219 CLV with a CI entirely below zero. And the **difference**
between approvals and control is cleanly positive and tight (+0.0238, CI entirely above zero, both
clusterings agree).

**How to read this honestly, together:** the model's approval gate is doing something — approved
entries have meaningfully better CLV than blind directional guesses drawn from the same tickers and
game-state buckets. But the approvals cohort's *own* CLV is not distinguishable from zero in
absolute terms, and the one channel that might explain a positive relationship (the edge-magnitude
`signal` itself, continuously) fails both confound checks — it doesn't survive the backward placebo
and doesn't survive controlling for the ticker's own trailing-mean dislocation. The likeliest
reading is that `directional_net_edge >= 0.04` is picking out *something real* relative to random
entry (plausibly: avoiding the worst-timed, most mean-reverted entries that a blind draw would
sometimes make), but the magnitude of that signal above the gate threshold is not itself
forward-predictive — which is a different and more modest claim than "the model has positive CLV."
Do not round this up to "CLV is positive" and do not round it down to "CLV is negative" — INCONCLUSIVE
is the accurate word, and the approvals-vs-control gap is the one number here that clears both a tight
CI and (trivially, since it's a difference-of-means not a signal-conditioned regression) is not
subject to the same confound mechanism that sank the raw signal regression.

## Deliverable 5 — Cell-registry coverage (92-cell registry, `market_type_registry.py`)

Enumerated directly from `reg._cells` (`PYTHONPATH=src python3 -c "..."`, 92 total cells,
`Counter({'NOT_IMPLEMENTED': 88, 'BLOCKED': 2, 'ACTIVE': 1, 'DARK': 1})`):

| Market type | Band | Cell status | Can this instrument score it today? |
|---|---|---|---|
| MLB_PLAYER_PROP_HITS | T4M_PROJ | ACTIVE | **YES — scored above.** This is the only cell with both a live price archive (`t4_mlb_cycle_log.jsonl`) and a confirmed, reconstructable approval formula (`run_t4_mlb_live.py:1240-1339`, verified this session). |
| MLB_PLAYER_PROP_HITS | T4M_ARITH | BLOCKED | **NO — not verified.** Built but blocked; whether its cycle-log schema matches T4M_PROJ's (same `mip`/`gross_edge`/`p_t4`/`vig` fields) and whether its approval formula is the same directional-edge computation was not checked this session. Needs schema/formula confirmation before this instrument can be pointed at it — the generic `compute_clv_row`/`cohort_aggregate` machinery would work unchanged if so; `build_t4mlb_cohorts`'s edge-reconstruction logic is PROJ-specific and would need a parallel function if the formula differs. |
| MLB_PLAYER_PROP_HITS | T4M_FLOW | BLOCKED | **NO — same reasoning as T4M_ARITH.** |
| NBA_PLAYER_POINTS | T4_IN_PLAY | DARK | **NO.** NBA is tabled per standing operator directive; no live archive is being generated to measure against. |
| All other 88 cells | various | NOT_IMPLEMENTED | **NO.** No execution logic exists, so no approvals (or any entries) are ever generated for these market-type/band pairs — there is nothing for a CLV instrument to measure until a cell is implemented and starts producing a price archive. |

**Summary: 1 of 92 cells can be scored today; 91 cannot** (2 blocked pending formula/schema
verification, 1 dark pending NBA reactivation, 88 not yet implemented). The instrument itself
(`compute_clv_row`, `cohort_aggregate`, the confound checks, the verdict logic) is market-type- and
band-agnostic and reusable without modification for any future cell that produces a ticker-keyed,
timestamped `mip` series — only the T4-MLB-specific cohort-construction function
(`build_t4mlb_cohorts`, which reconstructs `run_t4_mlb_live.py`'s exact edge formula) is cell-specific
and would need a sibling function per distinct approval-decision formula.

---

## Gap candidates for 34.2 to register (not registered here — this file does not touch
`GOVERNANCE_GAP_LOG.md` or `DECISION_LOG.md` per this session's scope fence)

1. **Compass OS Health check flagged a session-start protocol file over a length threshold
   this session** — `session_guard.sh`'s health check reported a 5,159-character breach against
   whatever threshold it enforces, surfaced during this session's Step 0 run. This was never
   written down anywhere at the time it was observed (pre-compaction) and has not been re-verified
   in this segment — flagging its existence and asking 34.2 to re-run the check fresh and register
   it properly (with the actual file, threshold, and current byte count) rather than trusting this
   secondhand description, since I do not have the original command output preserved verbatim.

2. **Possible terminology mismatch: CLAUDE.md's "~25 cells" vs. the registry's actual 92 cells.**
   CLAUDE.md's Principal Vision section describes coverage as "one cell of ~25" (5 execution bands ×
   ~5 market families, informally). The live `market_type_registry.py` enumerates 92 cells because
   the T4 band is itself split into three sub-bands (T4M_PROJ/T4M_ARITH/T4M_FLOW for MLB) rather than
   one. This may be intentional (a coarse conceptual figure vs. a fine-grained implementation figure
   living in two different documents at two different granularities) rather than a real
   inconsistency — I have not investigated `COVERAGE_TARGET_MATRIX.md` to check which framing it
   uses. Flagging for 34.2 to check and, if it is a real staleness issue, correct in the proper
   document (not CLAUDE.md, per this session's own governing document's remediation-pass note that
   band-status detail does not belong there).

3. **`build_t4mlb_cohorts`'s edge-reconstruction formula is untested against T4M_ARITH/T4M_FLOW.**
   Not a defect in this session's work — a scope boundary. If those bands are unblocked and a wave
   picks up extending this instrument to them, the formula-parity check described in Deliverable 5's
   table above is the first thing to verify, not an assumption to carry forward.

4. **`scripts/close_session_claim.sh` pushes the entire branch to `origin/main`, not just the
   closure row — contradicts its own stated purpose.** Run at close-out this session
   (`scripts/close_session_claim.sh "T-572" "..."`). Its docstring states the job is to land only
   the closure row on `origin/main` "independently of whether this session's own branch ever
   merges" (GG-186 follow-on, referenced in its own header comment) — i.e. the intent is visibility
   without requiring the branch to merge. Mechanically it does `git add "$CLAIMS" && git commit`
   (row alone, correctly path-scoped) but then `git push origin HEAD:main`, which pushes the
   *entire current branch tip*, not just the new commit. In this session that meant all 4 T-572
   commits (pre-registration, harness+tests, results) landed directly on `origin/main` with no PR
   and no review, immediately after the script printed "MERGED: NO" — the message became false the
   instant the push succeeded. Confirmed no data loss resulted (fast-forward only, rebase-retry
   correctly preserved concurrent T-573/T-574 commits already on `origin/main` — verified by
   diffing `origin/main` log before/after), so this is a process-integrity gap, not a
   destructive-action gap: any branch with substantive, unreviewed commits will silently bypass
   whatever review path the rest of the project uses (repo history shows normal work lands via PR,
   e.g. "Merge pull request #148"). Operator confirmed this specific instance can stay landed
   (content is scope-safe, tests pass); the script itself should still be fixed — the closure row
   needs a mechanism that doesn't require pushing the whole branch (e.g. commit the row against a
   fresh fetch of `origin/main` in a detached/orphan context, or `git push origin
   <commit-sha>:refs/heads/main` for a synthetic single-commit ref, rather than `HEAD:main`).

---

## What was NOT checked

- Whether the `directional_net_edge >= 0.04` reconstruction exactly matches every edge case in the
  live pipeline (e.g., any additional filters applied downstream of the edge check in
  `run_t4_mlb_live.py` beyond lines 1240-1339, such as exposure caps or kill-switch state at
  evaluation time) — this instrument reconstructs the *edge-approval* logic only, not the full
  order-placement pipeline, and the pre-registration document scopes it that way (§3a).
- Whether CLV predicts realized P&L in this dataset — that is GG-300/GG-301's question (T-571), not
  this one. CLV is a market-timing measure, independent of settlement outcomes by design.
- Size-weighting: `size_weighted` is `null` in every aggregate here because `kelly_fraction=0.0`
  (ADR-0048) means every row's `size_or_none` is `None` — there is nothing to weight by under the
  current sizing regime. The harness computes size-weighted means automatically whenever sizes are
  present; this is a property of current sizing policy, not a harness limitation.

---

**Report generated:** 2026-09-24, T-572, from `exp_output/T572_CLV_HARNESS/clv_results.json`
(commit-pending). No figure above was adjusted after being computed.
