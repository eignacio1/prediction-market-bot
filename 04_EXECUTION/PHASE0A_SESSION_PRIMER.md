# Phase 0-A Session Primer (parking note, 2026-07-31)

**Branch:** `session/20260731T152256Z-phase0a-raw-capture` (pushed to origin)
**Worktree:** `PM-worktrees/20260731T152256Z-phase0a-raw-capture`

## Status: ALL TASKS COMPLETE (Task 1, Task 2, GG-152 follow-up, Q1-Q6 review), pushed. Only outstanding item is the same-day Task 1 re-check once tonight's slate resolves (not yet actionable — see bottom).

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

### Follow-up items (2026-07-31, later same session)
- User supplied two small follow-ups after Task 1/2 closed: register a GG for the `BOT_ENV` vocabulary mismatch (`_kalshi_base_url()` never matches documented `ENV-03`, silently misroutes live-intent order submission to demo), and correct `VENUE_REGISTRY.md` to record `usage_tier=basic` as demo-scoped, not the live tier. Both done, commit `6dc6a3d`: **GG-152 registered** (OPEN, G6 precondition, no code fix shipped per explicit instruction pending operator sign-off), `VENUE_REGISTRY.md` V-001 corrected, `.env.example:22` discrepancy flagged unresolved, `PHASE0A_PARKING_NOTES.md` created (environment question resolved: `/series`,`/markets` are production-unconditional regardless of `BOT_ENV`; only `/account/limits` followed BOT_ENV to demo).
- Q1-Q6 "ARE WE COMPROMISED" adversarial review — **run this session** (commit follows). See summary below.

### Q1-Q6 review summary (2026-07-31)
- **Q1 (hard limits):** `risk.py` `_HARD_LIMITS` unchanged (`max_single_event_exposure_usd=500`, `max_drawdown_pct=0.20`, `max_portfolio_deployment_pct` via ADR-0026); `execution_bands.py` kelly_fractions match known state — MAIN/T1/T4M-PROJ zeroed per ADR-0048 (2026-07-29, GG-135 ruin-geometry remediation), T4-PROJ/T5-ARITH (NBA) inert since NBA is dark. Nothing new.
- **Q2 (stub scan):** CLEAN (governance hook, this session) — no `# stub|# placeholder|# TBD|# todo` hits in `src/`.
- **Q3 (architecture coherence):** No change to the three largest post-G4 builds this session; this session touched only docs (VENUE_REGISTRY, GOVERNANCE_GAP_LOG, DECISION_LOG) plus a raw-capture script that was never committed to `src/`.
- **Q4 (interface evolution):** `evaluate_forecast` (risk.py:352), `open_position`/`exit_position` (paper_trader.py:380/596), `submit_order` (kalshi_client.py:553) all present, signatures not touched this session.
- **Q5 (decision traceability):** `DEFAULT_KELLY_FRACTION=0.25`, `MIN_EDGE_TO_APPROVE=0.04` (ADR-0020), and all three `_HARD_LIMITS` trace to the 2026-05-29 RETROACTIVE DECISION_LOG block. No orphaned constants found.
- **Q6 (what am I worried about):**
  1. **GG-152 itself** — the standout finding this session. Unstaffed, no T-NNN, explicitly a G6 precondition. Flagging again here so it isn't lost in the doc shuffle: this must be resolved (with operator sign-off) before `BOT_ENV=ENV-03` is ever set for real.
  2. **Governance gap burn-down is trending the wrong way** — live scan this session: 27 open / 150 total, +9 over the last 14 days (+0.64/day), trend GROWING. Not a new gap in itself and not actioned here (out of this session's scope), but worth surfacing to Earl directly rather than letting it sit silently in scan output.
  3. Nothing else rose to the level of a new concern — Q1/Q4/Q5 constants and interfaces all check out unchanged against their last-known-good state.
- No new GG registered from Q1-Q5 (nothing new found); Q6 concerns are either already covered by GG-152 or are an operator-visibility note, not a new gap.

### Re-check still due (not actionable yet)
Same-day re-check of Task 1 (epoch-12 sizing / `t4_offsetting_suppressed` counts) after tonight's MLB slate resolves. As of 2026-07-31T19:05Z the slate is live (first pitch 18:20Z) — not yet resolved. Re-verify in a fresh session once games are final (expect epoch-12 rows to exist by tomorrow morning).

### Scope discipline maintained
No writes to `src/`, `execution_bands.py`, `risk.py`, `paper_trader.py`. No orders placed. No classification/tabulation performed on captured data.
