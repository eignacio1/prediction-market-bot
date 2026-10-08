# W59.3 — NBA opening-night readiness, NHL goalie verdict, ADR-0070 widened + accepted

Status per part: **A in PR** · B not started · C not started. Updated per part; newest state at top of each section.

## Part A — NBA readiness

| Check | Result (all measured 2026-10-07 unless stated) |
|---|---|
| Kalshi lists opening night (2026-10-20)? | **Yes, moneyline only:** 3 games / 6 markets (KXNBAGAME). Spread/total list only 1-2 days ahead; team total (KXNBATEAMTOTAL) has zero listings. |
| VPS dry run (scratch ledger dir, deleted afterwards; live ledger untouched) | T1 6 rows, T2 2 rows, T3 2+2 rows for opening-night moneylines. Rows logged, no order path. |
| Cron coverage of a 7–10 PM ET slate | Simulated against `deploy/cron.nba_shadow`: per game 6 T1, 4 T2, 4 T3 runs. Adequate. |
| **Premise check: "preseason rows are being banked"** | **FALSE.** Live runs only log `no_kickoff` skips for preseason (schedule index is regular-season only by design). Fixed by a separate, labelled ledger — below. |
| Preseason ledger | `scripts/run_nba_pregame_shadow.py --preseason` → `exp_output/PREGAME_SHADOW_PRESEASON/`, every row carries `season_phase="preseason"`, `excluded_from_judged_n=true`; refuses to write into `PREGAME_SHADOW/`. Judged ledgers byte-identical in format (tests). Cron: `deploy/cron.nba_shadow_preseason` (own block, one line, :57, remove after 10-20). |
| Live Terminal | `_season_state` now has NBA (in-season from 2026-10-20 through ~06-22; preseason is "off", so idle ledgers are not red). New `freshness.nba_shadow` panel row "SHADOW NBA ledgers (SHADOW, $0 stake)" — source `exp_output/PREGAME_SHADOW/NBA_*.jsonl`, shows age, dimmed when stale; "awaiting" when no file. `Live Terminal.html` and embedded `_HTML` kept byte-identical. |

### 10-21 flip check (do NOT flip now)

Run on/after 2026-10-21 (read-only; prints the exact `promote_cell_status(..., superseding_reference="EXP-038")` lines for cells with ≥1 valid judged row; exit 1 if none qualify):

```
ssh prediction-market-vps "cd /opt/prediction-market-bot && venv/bin/python scripts/w59_3_nba_flip_check.py"
```

Cells with `FLIP-OK` get the registry edit (same pattern as `_EXP037_NFL_SHADOW_CELLS`); `NO-ROWS` cells stay NOT_IMPLEMENTED. Expected 10-21: moneyline T1/T2/T3 qualify; team total will not.

### Safety
No order, position, fill, stake or `kelly_fraction` change; no live-ledger write. New tests: `tests/test_w59_3_nba_preseason.py` (14 passing with the NBA safety suite).

### Screenshots
Before/after real-browser captures: pending post-deploy (`scripts/browser_check_dashboard.py`).

## Part B — NHL goalie verdict
Not started.

## Part C — ADR-0070
Not started.
