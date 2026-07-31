# Phase 0-A Session Primer (parking note, 2026-07-31)

**Branch:** `session/20260731T152256Z-phase0a-raw-capture` (pushed to origin)
**Worktree:** `PM-worktrees/20260731T152256Z-phase0a-raw-capture`

## Status: DELIVERABLE COMPLETE, pushed. Report-out to user still pending.

### Task 1 (epoch-12 verification) — DONE
- Deployed VPS SHA confirmed = source-of-truth epoch-12 boundary (commit `66bb0d3c`, GG-149), verified as ancestor of live HEAD `2084449`, not trusted via git log alone.
- Fresh portfolio pull (`build_t4_resolved_ledger.py --pull`): **zero epoch-12 rows**, both closed and open. Root-caused as expected: epoch-12 deployed 08:00Z, last live game ended ~05:01Z (pre-deploy), today's slate (first pitch 18:20Z) hadn't started at check time (15:25Z). NOT the `kelly_size_zero` failure mode — no live window has occurred since deploy yet. **Re-verify after tonight's slate completes** — that's the real test of $1.00 sizing + offsetting-suppression counts.
- `t4_offsetting_suppressed` count: not yet meaningfully measurable (no epoch-12 activity yet).

### Task 2 (raw Kalshi capture) — DONE, committed, pushed
Commit `6afc297` on this branch. Files in `exp_output/PHASE0_SURVEY/`:
- `series_all.json` — 12,355 series, unfiltered, 1 page (no cursor needed).
- `account_limits.json` — `usage_tier=basic`, read bucket 400/refill 200/s, write bucket 100/refill 100/s. **Caveat: authenticated call followed `BOT_ENV` routing (`ENV-01` → demo sandbox base URL)** — so this may be the DEMO account's limits, not necessarily production's. Flag this to Earl; worth a follow-up call with `BOT_ENV=live` if the demo/live tiers could differ.
- `markets_sample.json` — 220 MLB-looking series (ticker/title/category contains "MLB" or "BASEBALL"), `status=open`, full pagination. Includes lots of non-hits-market MLB series (awards, streaks, KBO/NPB/WBC — filter was intentionally broad per task spec, not narrowed to KXMLBHIT).
- `capture_manifest.json` — 226 calls logged (path, params, timestamps, ok/status, record count, cursor).

Capture script used (not committed, lived in scratchpad): calls `KalshiMarketClient.from_env()._get(...)` directly — no hand-rolled RSA signing, per task constraint. `.env` was read from the **main tree** (`Prediction Markets/.env`), not copied into the worktree (worktrees don't inherit gitignored files) — reproduce via `PHASE0A_ENV_FILE=".../Prediction Markets/.env"` env var if re-running.

### Still pending
1. Task #2 (Q1-Q6 "ARE WE COMPROMISED" adversarial review) — not run this session. Scope was read-only capture/verification; judgment call was to prioritize the blocking deliverable given context pressure. Should still be done, at least abbreviated, before calling the session fully closed.
2. Final chat report to user: tier+budgets, series count, MLB-related count, Task 1 result, closing with Assumptions/Key Risks/Validation Checks/Confidence. Explicitly do NOT classify/tabulate the market data — that's the Cowork window's job.
3. Consider a same-day re-check of Task 1 after tonight's MLB slate resolves (epoch-12 rows should exist by tomorrow morning).

### Scope discipline maintained
No writes to `src/`, `execution_bands.py`, `risk.py`, `paper_trader.py`. No orders placed. No classification/tabulation performed on captured data.
