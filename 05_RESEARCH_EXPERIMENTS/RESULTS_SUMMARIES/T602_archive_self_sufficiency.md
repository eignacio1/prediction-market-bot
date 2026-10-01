# T-602 — Archive self-sufficiency: settlement + depth writers

**Date:** 2026-09-30/10-01 (UTC) · **Branch:** `session/20261001T015005Z-archive-self-sufficiency` · **Writers:** `scripts/capture_settlements.py`, `scripts/capture_depth.py` (new files only) · **Tests:** `tests/test_t602_capture_{settlements,depth}.py` (14 pass)

Not touched: `archive_market_prices.py`, any existing capture window, any existing archive row, GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, sizing. Read-only, unauthenticated GETs only. Nothing installed, no crontab run, no service restarted.

## D0 — sync
Local main was `9f2b837` (stale); origin/main and the VPS were `aedfac9`. Worked from a fresh worktree off `aedfac9`; T-599/T-600/T-601 already on origin/main. The branch was later rebased onto newer main by the cron-draft step (tip then `8fb2c15`).

## D1 — settlement capture
Both defects confirmed: archive rows carry no settlement; depth sampling is per family (2 tickers/run).

**Back-capture (VPS, scratch checkout, store `/opt/t602_out/SETTLEMENT_ARCHIVE`, not the repo archive):**
- Archive holds **84,787** distinct tickers (14 series). **83,287 captured (98.2%)**; **1,500 not captured** because the venue has no terminal result for them (NFL games not yet played, MLB still open). They are absent, not guessed.
- Results: no 52,191 · yes 30,465 · **scalar 631** (see finding 2).
- Store file sha256 `054a7221…177de`, 83,287 rows, 63,180,401 bytes.

**Reconciliation vs EXP-031 cache (every ticker, result + expiration_value + settlement_ts):**
- 83,286 compared, **83,286 agree, 0 field mismatches.**
- 24,733 cache-only tickers not in the archive (EXP-031 pulled whole series; expected, not a discrepancy).
- **Discrepancies: 1.** `KXMLBTOTAL-26SEP302000BOSNYY-2` is settled `yes` in the venue now but is absent from the EXP-031 cache — it settled after EXP-031 pulled (game 2026-09-30 20:00). A timing difference, not a conflict. Neither source preferred.

**Findings for 44.1 (not registered by me):**
1. Idempotency detects content changes only through `apply_revision`, which `capture` does not call. A settlement revised upstream after first capture is not detected by routine runs. Needs a periodic `verify` pass if revisions matter.
2. 631 `scalar` results (e.g. `KXMLBF3-26SEP271520BALNYY-BAL`, settlement value 0.38). Any join that treats result as yes/no will mis-score these; EXP-031 agrees on them, so this is a property of the venue data, not of the writer.
3. The writer writes its file only after all series are fetched; a crash loses that run (a rerun redoes it safely).

## D2 — depth rate
Prior: ~1.4k–2.8k depth rows per family; KXMLBF7 7 rows / 2 tickers. For ±5% at 95% (~385 obs per stratum) across 14 series × 3 time-to-start strata ≈ 16k observations, from a season, spread over many distinct events. Chosen: **per series, 12 event-balanced tickers per hourly slot (full ladder stored), 14 series ≈ 143–168 rows/slot.** With 13 slots/day ≈ 1.9–2.2k rows/day, ~150–170 rows/series/day — more than the old F7 total every day. The 385-per-stratum target is met for most series in ~1 week; thin-event series (NFL, F-series late in day) are limited by open markets, not rate.

- **Cost:** 143 rows = 189,098 bytes (~1.3 KB/row). 13 slots/day ≈ **2.5 MB/day**; 60-day window ≈ **148 MB**; 180-day season ≈ **443 MB**. VPS free space 16 GB.
- **API volume:** 157 calls/run (143 orderbooks + 14 listings) → ~2,040 calls/day. Paced at 0.30 s ≈ 3.3 req/s for ~50 s per run ≈ 17% of the documented ~20 reads/s basic tier. The anonymous limit is undocumented and T4M-PROJ shares the account read budget in-play: **if any 429 appears, halve `--per-series`.** Within documented limits.

## D3 — hand-runs (VPS, scratch checkout of this branch)
| Run | Writer | Result | Store sha256 after |
|---|---|---|---|
| 1 | depth | 143 written, 157 calls, 0 failed | `e0b1766a…eeb2` (143 lines) |
| 2 | depth, immediate | 0 written, 143 skipped, 14 calls | `e0b1766a…eeb2` (identical) |
| 1 | settlement, full | 83,287 written | `054a7221…177de` |
| 2 | settlement, immediate, **3 series only** (KXMLBGAME, KXNFLTEAMTOTAL, KXMLBF7) | 0 written; 5,175 already captured; 452 non-terminal | `054a7221…177de` (identical) |
| 3 | settlement, full (later, ~35 min after run 1) | 22 written (new settlements, see addendum), 83,287 already captured, 1,478 non-terminal, 1,507 calls, 0 failed | `7584b1ba…1b21`, 83,309 rows |

Row counts + per-row field comparison against the source were done through the reconciliation above (83,286/83,286 agree on result, expiration_value, settlement_ts). Depth rows were not compared field-by-field against a second source: depth has no second source, and the book is a point-in-time snapshot. Run 2 settlement was scoped (3 series) for time; the full run 3 is the full-universe proof.

## D4 — drafted cron lines (commented, NOT installed; no authorization line)
```
# 30 9 * * *      cd $PROJ && PYTHONPATH=$PYTHONPATH $PYTHON scripts/capture_settlements.py capture --archive exp_output/PRICE_ARCHIVE --store exp_output/SETTLEMENT_ARCHIVE >> logs/capture_settlements_cron.log 2>&1
# 10 17-23 * * *  cd $PROJ && PYTHONPATH=$PYTHONPATH $PYTHON scripts/capture_depth.py --store exp_output/DEPTH_ARCHIVE >> logs/capture_depth_cron.log 2>&1
# 10 0-5 * * *    cd $PROJ && PYTHONPATH=$PYTHONPATH $PYTHON scripts/capture_depth.py --store exp_output/DEPTH_ARCHIVE >> logs/capture_depth_cron.log 2>&1
```
Settlement 09:30Z: after the last MLB (~05–06Z) and NFL (~04:30Z) games settle; already-captured tickers cost no fetch. Depth at :10, which collides with no existing capture line (price archive :00/:20/:40, NFL :05/:25/:45). Absent an authorization line: skipped.

## D5 — dashboard
No line naming `pmbot-web-dashboard` in OPERATOR_CONSOLE.md or ACTIVE_QUEUE.md (only descriptive GG-269 text). **Restart skipped.** Read-only `GET /api/data` on the VPS reports running `process.sha = f962a57c…`, started 2026-10-01T02:25:20Z — a restart by someone else, not this session. That is the running sha; it was not verified against the file on disk or `rejected_counts`/`t4_cycle_tail` here.

## Addendum — settlement run 3
Run 3 (full universe, rc=0) appended **22 rows**, all for tickers that settled *after* run 1 (settlement_ts 02:02:16Z–02:35:26Z; series KXMLBF5, KXMLBF5SPREAD, KXMLBF5TOTAL, KXMLBTOTAL) — i.e. games finishing while the hand-runs were in progress, not duplicates.
- Duplicate tickers in the store: **0** (83,309 rows, 83,309 distinct).
- The first 63,180,401 bytes of the file hash to `054a7221…` — **byte-identical to the run-1 file**; run 3 only appended.
- Idempotency therefore proven on the full archive: every previously captured ticker skipped, none rewritten.
- Caveat: the "1,500 uncaptured" figure in D1 is as of run 1; as of run 3 it is 1,478.
