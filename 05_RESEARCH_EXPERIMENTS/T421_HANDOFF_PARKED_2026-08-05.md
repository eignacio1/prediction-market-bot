# T-421 — Decoupled Outcome Store — PARKED (diagnostics only, no code written)

**Status:** paused mid-session (token budget), session-start protocol complete, no `src/` changes made.
Branch: `session/20260805T054940Z-decoupled-outcome-store`. Worktree: `PM-worktrees/20260805T054940Z-decoupled-outcome-store`.

## Session-start protocol — result

Steps 0-4 + Step 4 ops health all run. Clean: Step 1 (no unlogged decisions), Step 2 (no stubs),
Step 3 (37 OPEN / 46 headers = 46 status lines, structural assertion passes). Step 4: T1 MLB
player-matching normal (17-36/run), 0 bets placed today (expected, `kelly_fraction=0.0` still in
force per ADR-0048/R1 — not a new finding), T4 MLB systemd active, T1 NBA correctly dark
off-season, dashboard clean (0 restarts, 0 OOM-kills). The one `SemanticFloorViolation` hit in
`paper_mlb_cron.log` is dated **2026-07-11** (stale history in the log, bankroll snapshot in that
block reads $877.85 vs current $683.91) — not a live incident.

**ARE WE COMPROMISED? (Q1-Q6) was NOT completed** — session paused during the pre-build
verification step below, before reaching the adversarial checklist. Do not skip it next session;
re-run it before writing any code.

## THE FINDING — live cycle log schema has drifted, reshapes the task

Per the task brief's own instruction ("if the schema drifted, that is the finding and it reshapes
this task") — it did. Checked the **live** VPS file, not the stale local cache
(`logs/.vps_t4_mlb_cycle_log_cache.jsonl`, last written 2026-07-14 — do not trust it):

- Live file: `/opt/prediction-market-bot/logs/t4_mlb_cycle_log.jsonl`, **64,396 rows** (not 24,744
  — the local cache is roughly 2.6x smaller than live and 3 weeks stale).
- Row `ts` range: 2026-07-02T19:09:34Z → 2026-08-04T04:13:57Z. 30 distinct `game_date` values.
- Last write was **2026-08-04T04:13:57Z**, ~25.5h before this check (2026-08-05T05:51Z) — plausibly
  just the pre-game-night gap (last night's games ended, tonight's haven't started), not
  necessarily a dead pipeline. **Not yet verified either way — check this first on resume**
  (compare against a T4 systemd restart/poll log, or just re-check after tonight's games should
  have started).

**Three distinct schema signatures, not one:**

| count | signature | has `p_t4`/`gross_edge`/`net_edge`? |
|---|---|---|
| 32,957 | 20 keys incl. `ba_l10_shrunk` | yes (full forecast, post-epoch-8 shrinkage) |
| 24,298 | 19 keys, no `ba_l10_shrunk` | yes (full forecast, pre-shrinkage / older epoch) |
| 7,141 | 16 keys incl. `vig_skip`, **no** `ba_l10`/`ba_l10_shrunk`/`gross_edge`/`net_edge`/`p_t4` | **no** |

**`p_t4` present: 57,255 / absent: 7,141** (11.1% of all rows). The 7,141 `vig_skip` rows are a
real, distinct evaluation outcome — the cycle short-circuited before computing a forecast (name
suggests a vig-based early-exit, not yet confirmed in code) — not a data-quality defect to be
dropped. They still carry `player_id`, `game_date`, `threshold`, `ticker`, so the (player_id,
game_date, threshold) join key the task specifies still applies to them; they just can't
contribute a Brier/calibration score since there's no `p_t4` to score. The join/store design must
carry a `row_type` or `has_forecast` flag rather than assuming every row is scoreable.

## Not yet started

- Join-key uniqueness verification (task flagged doubleheaders + multi-threshold as likely
  violations — not yet checked against real data).
- `fetch_actual_hits()` review in `run_resolve_mlb.py` (import-only, no edits — per hard scope
  fence).
- The join script, the store, tests, and the coverage-report doc.

## Resume instructions

1. Re-read this file, then re-verify the "last write 25.5h ago" question first — it may have
   simply been resolved by tonight's games already running.
2. Complete ARE WE COMPROMISED? Q1-Q6 (was skipped this session).
3. Proceed per the original task brief: join-key uniqueness check → outcome-join script → new
   gitignored store → tests → `05_RESEARCH_EXPERIMENTS/DECOUPLED_MEASUREMENT_STORE_2026-08-05.md`.
4. Hard scope fence still applies: no edits to `paper_trader.py`, `risk.py`,
   `run_t4_mlb_live.py`'s write path; no epoch bump; no sizing change; no ADR.

Numbers to report back once built (per task brief): live cycle-log row count (64,396 as of this
check, will grow), rows successfully outcome-joined, rows that could not be and the dominant
reason (expect: `vig_skip` rows with no `p_t4` as one major non-scoreable bucket, distinct from
genuine resolution failures on scoreable rows).
