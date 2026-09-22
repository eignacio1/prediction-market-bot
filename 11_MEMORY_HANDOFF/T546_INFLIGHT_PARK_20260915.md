# T-546/GG-277 — in-flight parking note (session limit hit mid-task)

**Branch:** `session/20260915T003417Z-settle-first-nfl-position`, pushed through commit `b2569fc`. Worktree clean, nothing uncommitted.

## Where this left off

1. Session-start protocol: run (Steps 0-4, Q1-Q7) but never formally written up to the operator — no user-facing report was sent yet.
2. Gap-log pickup note added to GG-274 and pushed (`b2569fc`) as required first commit.
3. **GATE check: COMPLETE.** Confirmed via VPS `find /opt/prediction-market-bot -iname '*nfl*'` and direct path checks: **zero** NFL T1 positions exist. No `paper_portfolio_t1_nfl_game_market.json`, no `audit_t1_nfl_game_market.jsonl` anywhere on the VPS filesystem. T-543's 2026-09-11 finding is still current.
4. Per task instructions (do not stop on zero — open one): attempted to run `nfl_exp027_adapter.py` on the VPS to open a live position.
   - First attempt failed: `ModuleNotFoundError: No module named 'numpy'` — fixed by using `venv/bin/python` instead of system `python3` (VPS has a venv at `/opt/prediction-market-bot/venv`).
   - Second attempt got much further — EXP-027 model fit cleanly in-process (2734 train games, reproduced pre-registration LR+Platt, `[store] VERIFIED: 4/4 sample checks`) — then failed at `KalshiMarketClient.from_env()`: **`OSError: VENUE_API_KEY not set. Load .env before importing.`**
   - Root cause (not yet fixed): `VENUE_API_KEY` IS present in `/opt/prediction-market-bot/.env` (`grep -c VENUE_API_KEY .env` = 1), but plain `source .env` inside a non-interactive SSH one-liner does not appear to export it into the Python subprocess env. The repo's own cron pattern (`deploy/cron.conf`) uses `export $(grep -v '^#' .env | xargs)` instead of `source .env` — **that's the likely fix to try next**, e.g.:
     ```
     ssh prediction-market-vps "cd /opt/prediction-market-bot && export \$(grep -v '^#' .env | xargs) && BOT_ENV=paper PYTHONPATH=src venv/bin/python src/prediction_market_bot/nfl_exp027_adapter.py"
     ```
   - **Confirmed clean/no side effects from the failed attempts:** neither `logs/audit_t1_nfl_game_market.jsonl` nor `logs/paper_portfolio_t1_nfl_game_market.json` exist on the VPS — both failures occurred before any file write (AuditLogger construction did not create the file; PaperTrader was never even constructed — `from_env()` raised first). No live order risk either way (`kalshi_client=None` unconditionally, `run_t1_nfl_game_market.py:424`, verified by direct read).
   - VPS git HEAD confirmed to be an ancestor of `origin/main` (`61b51f2...`) — deploy is current, no drift, no need to redeploy before retrying.

## Next step for the resuming session

1. Fix the env-export issue above and retry `nfl_exp027_adapter.py` on the VPS.
2. Confirm the resulting row's `model_identity`/provenance is `"EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"`, not the stub string — this satisfies the "which model produced the row" requirement (GG-267/T-544).
3. If it opens a position (`OPENED`): proceed to Deliverable 1 (ESPN score fetch, VPS-only per GG-266, cross-checked against a second source).
4. If it refuses (`REFUSED_STAKE`/`REFUSED_NO_EDGE`/etc. — all valid non-failure outcomes per ADR-0058): report the outcome_counts dict and refusal codes from the audit log, hand back per task instructions.
5. Formally write up the session-start protocol results to the operator (Steps 0-4 + Q1-Q7) — gathered but never sent as a user-facing report this session.
6. All DO-NOTs from the original task still apply unchanged (no live order, no `settle_position()` edits, no MLB/T4 touches, no kelly/cron/promotion changes).

No destructive or irreversible action was taken this session beyond the two intentional pushed commits (session claim, GG-274 pickup note) and two failed/no-op remote script invocations.
