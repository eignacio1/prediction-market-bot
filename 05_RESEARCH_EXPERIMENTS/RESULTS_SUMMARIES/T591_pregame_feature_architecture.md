# T-591 — Pre-Game Feature Architecture: Results Summary

**Deliverable:** `01_SPEC/PREGAME_FEATURE_ARCHITECTURE.md` (SPEC; proposes, does not authorize). Doc-only. No src/, GGL, DECISION_LOG, model, cron or sizing change.

## Deliverable 0 — sync
Worktree base `0870f14` (contains T-586, T-587, T-584, T-581, T-588). Claim commit `d66b0c9`. Merged `origin/main` `ae49434` (T-592 D0, landing ADR-0068 and CLAUDE.md doctrine) → worktree HEAD `ae49434`. Shared-tree HEAD at session start `9f2b837`.

## Findings for later registration (no GG written here)
1. **Six-feature NFL model, one market family.** Only NFL moneyline has a real forecaster; spread, game total and team total have none, and no NFL player-prop cell exists in the registry. Registry cells for those families exist without any model able to populate them.
2. **EXP-027 adapter is not scheduled and is re-fit at every start** (not serialized); default `run_t1_nfl_game_market.main()` model is the stub. Countable evidence is 20 closed rows (T-588).
3. **NFL remainder underpowered by ~12×.** ~223 games remain (≈210 regular + ≈13 playoff); at T-554's 0.875 clean rate ≈195 new rows, ~215 total vs n\* 2,610 (≈8%). Even 100% coverage ≈243. Decision-grade for APR-0035. Forward Brier half-width at n≈215 ≈ 0.0014 (scaled from T-581), larger than the measured splits effect (−0.0007).
4. **Data already downloaded and dropped:** nflverse `games.csv` carries weather, QB, coach, referee; `stats_team_week` carries sacks/QB hits/penalties; the allowlist (`nfl_ingestion.py`) retains 10 schedule and 7 team-stat columns. Confirms T-586 N1–N6 at Payload-field cost.
5. **Docs-claimed, consumed by no run path:** EPA-split accessors (unwired, ADR-0066 recommends not accepting); `get_opp_runs_scored` (backtest script only); NBA PRF layer is NBA-only; MLB game-market families run on `StubMLBGameMarketForecastModel` with no PROVENANCE.
6. **MLB matrix depth measured:** `exp_output/MLB/mlb_feature_matrix.csv`, 132,184 rows, 2024-03-20 → 2026-07-17, 45 columns (untracked artifact in the shared tree; absent from fresh worktrees).
7. **Wave-35 discrepancy:** the arc described a per-cell "real vs stub forecaster" inventory; what closed is T-575 (feature audit) and T-588 (evidence boundary). The per-family forecaster table in §1 of the spec was derived from code, not from a Wave 35 artifact.
8. **Claim race:** T-591 was claimed twice within seconds (`7ba35f2` provenance session, `d66b0c9` this session); the other session released via `a683eee` and re-claimed as T-592. Instance of GG-162-class collision; no action taken.
9. **Q7 is vacuous in fresh worktrees** (no `logs/.vps_portfolio_cache_*`, no outcome store) — same as T-586 finding 3.

## Session-start concerns (Q6), unresolved and unregistered here
- One MLB T1 run logged `0 players in live MLB markets`, and `SemanticFloorViolation` count was 1; neither diagnosed (scope).
- T4M-PROJ countable n = 0 under the evidence predicate; 802 STUB NFL rows can inflate an epoch-only clean_n (GG-317).
- Compass OS Health line 5159 chars (>3000); governance backlog 106 open, 32 UNSPECIFIED severity.

## Assumptions carried
Clean rate 0.875 (n=16); same-event contracts correlated; NBA PRF not portable (internals unread); stadium and QB-quality tables unsourced; information-gain ratings are Judgement.
