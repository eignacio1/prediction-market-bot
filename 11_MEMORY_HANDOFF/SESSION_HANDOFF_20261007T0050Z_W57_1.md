# SESSION HANDOFF — W57.1 (T-699..T-700, GG-489) — PARTIAL, TRUNCATED AT BUDGET

**Status:** PARTIAL | PR #171 merged (CI run 37551677853 green) | features-sync run 37552551967 was still in_progress at close.

**Root cause (D1, evidence from VPS read-only):** (1) statsapi returns HTTP 406 to the VPS on every endpoint tested (schedule, gameLog R and P). (2) PIPE-05FX cron (22:30 UTC) passes no `--include-postseason`; regular season ended 2026-09-27 and CSV's max game_date is 2026-09-27, so the 7-day halt fires on genuinely stale data. Also: VPS CSV is degraded (121 players of ~575; opp_sp/team features 100% blank).

**Fix (D2, merged):** `.github/workflows/mlb_features_sync.yml` (23:17 + 10:17 UTC) regenerates with postseason on a runner, gated by `scripts/verify_mlb_feature_csv.py` (unchanged MLB_FEATURE_CSV_CONTRACT + >=300 players), atomic push to VPS. Negative test: stale VPS CSV refused. Deploy summary: t4-mlb restart `not_needed`. Crontab untouched; 7-day halt untouched.

**NOT DONE:**
- GG-489 is claimed but NOT registered in GOVERNANCE_GAP_LOG.md (D0 miss). Register it first.
- D3: read run 37552551967 result; if success, VPS read-only: fresh CSV (max game_date ~2026-10-05), hand-run the exact T1 cron command (`0 11` PIPE-05 line), confirm passes PIPE-05, rows per T1/T2/T3 player-hits cell.
- D4: results doc W57_1_mlb_hits_results.md; resolve GG only with D3 evidence.
- Consumer enumeration (GG-072 rule): run_mlb_pregame.py (PIPE-06pre -> T3/T4 pregame) shares the contract; check its same-day log for the same HALT.

**Operator decision:** VPS 22:30 cron still overwrites the CSV with degraded output daily; the 23:17/10:17 runs re-assert before 11:00 T1. Removing that line needs the operator's written line.

**Strategic decisions:** None. **Resume:** read run 37552551967 (`gh run view 37552551967 --log`), then D3.
