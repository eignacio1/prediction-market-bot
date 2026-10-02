# ADR-0067: Append-Only Position Log With Periodic Snapshot (PROPOSED, NOT ACCEPTED)

**Status:** PROPOSED — drafted only (T-589, Wave 39 Block 39.1). Not accepted. No code implements it, no register row exists, no pool file is touched. Supersedes nothing. A future acceptance needs operator sign-off (ADR-0006/ADR-0024 governance) and its own implementation task.

**Author:** Claude (session `t4-ledger-durability`, T-589) · **Date:** 2026-09-29

---

## Context

`PaperTrader._save()` rewrites the whole pool file on every mutation. Deliverable 1 of this block (commit `c6dce64`) made that rewrite atomic (temp file, fsync, `os.replace`, inside the existing flock), which fixes the truncated-ledger failure. It does not change the cost shape, which is O(events × pool size).

**Measured on a copy of the real T4 pool** (`logs/.vps_portfolio_cache_mlb_t4.json`, 8,819,710 bytes, 5,986 rows = 63 open + 3,923 closed + 2,000 rejected; harness `scripts/bench_paper_trader_save.py`; full tables in `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T589_ledger_durability_results.md`):

| scale | rows | file MB | ms / save |
|---|---|---|---|
| 1x | 5,986 | 8.8 | 278 |
| 2x | 9,909 | 14.6 | 607 |
| 5x | 21,678 | 31.9 | 1,107 |
| 10x | 41,293 | 60.9 | 2,058 |

`open_position` also calls `_reload_locked()` (full read and parse) under the same flock, so one open costs about 383 ms wall on the 1x pool, all of it inside the lock. Real mutators driven through a real `PaperTrader` on a copy, counted by the new built-in `save_stats` counter:

| opens | `_save` calls | save ms | wall ms incl. reload | MB written |
|---|---|---|---|---|
| 26 (busiest observed minute) | 26 | 7,705 | 9,729 | 230 |
| 65 (median game-day) | 65 | 18,945 | 23,833 | 576 |
| 254 (busiest game-day) | 254 | 80,079 | 100,142 | 2,282 |
| 200 rejects | 200 | 74,455 | — | 1,735 |

`_save()` is called once per opened bet and once per rejected order, never per evaluation. There are 7 executable `self._save()` sites in `paper_trader.py` (`ensure_persisted`, `open_position` ×2, `exit_position`, `settle_position`, `mark_aged_open`, and the one inside `resolve_pending`); the "13" in the task brief was not reproduced. The design holds at today's measured T4 demand (busiest minute: about 16% of wall clock inside the flock). It does not hold at burst demand: an 802-open run on a pool of T4's size holds the flock for about 5 minutes and writes about 7 GB, and cost grows with pool size, so every additional resolved row makes every later bet slower. One day (2026-09-20) recorded 1,795 rejected orders, which is about 11 minutes of flock-held rewriting on their own.

## Decision (proposed)

Keep the pool JSON file as a **snapshot**, and add an append-only **event log** beside it. Every mutation appends one fsync'd log line; the snapshot is rewritten (using the D1 atomic path) only at compaction.

### Schema

`<pool>.events.jsonl`, one JSON object per line, UTF-8, `\n`-terminated:

```
{"seq": 1842, "ts": "2026-09-29T23:44:01.131Z", "op": "open|reject|close|settle|mark_aged|daily_reset|reconcile",
 "position_id": "POS-...", "row": {...full row, for open/reject...}, "patch": {...changed fields, for close/settle/mark_aged...},
 "prev": "<sha256 hex of the previous line's bytes, '' for the first line after a snapshot>", "crc": "<crc32 hex of this line without the crc field>"}
```

The snapshot gains two top-level fields: `log_seq` (last seq folded into it) and `log_head` (the `prev` hash to expect on seq `log_seq + 1`). Existing fields are unchanged. Bankroll and realized P&L remain derived from the ledger on load (GG-034); they are never logged as authoritative values.

### Write order (the ordering rule)

1. Take the existing flock. 2. Append the event line and `fsync` the log. 3. Apply it to in-memory state. 4. Return success to the caller. The snapshot is **never** written before the log line that it reflects is durable. `open_position` returns `ok=True` only after step 2 succeeds.

### Compaction

Under the flock, when any of 500 events, 5 minutes, cycle end, or shutdown is reached: write the snapshot with the D1 atomic path with `log_seq`/`log_head` set, then rename the log to `<pool>.events.<first_seq>-<last_seq>.jsonl` and start a new one. Rotated logs are kept, never deleted (no-delete constraint stands). A crash between snapshot replace and rotation is safe because replay skips `seq <= log_seq`.

### Recovery procedure

1. Load the snapshot (always parseable under D1). Read `log_seq`, `log_head`.
2. Read the live log from the start. Discard lines with `seq <= log_seq`.
3. For each remaining line in `seq` order: require `seq == previous + 1`, `prev == expected hash`, crc valid. Apply the op; `open`/`reject` of an existing `position_id` is a no-op (idempotent), `close`/`settle` applies the patch.
4. Stop at the first line that fails (torn tail from a crash mid-append). Do not truncate or edit the log; record the stopped seq and byte offset in the audit log (C6) and continue from the state reached. A failure in the middle of the chain (line N bad, line N+1 valid) is not a torn tail: recovery halts and alarms, because that is corruption, not a crash.
5. Recompute bankroll and realized P&L from the ledger. Optionally compact.

### Readers that change, by file

Grep-derived from `paper_portfolio` / `portfolio_path` / `_reload_locked` references (`src/`, `scripts/`, `.claude/`); each file must be re-read at implementation time, and any file not listed here that opens a pool path directly is a gap in this list, not an exemption.

- **Must change (need current state):** `src/prediction_market_bot/c5_execution/paper_trader.py` (`_reload_locked`, `_save`, all 7 call sites, `ensure_persisted`, `reconcile`); `c7_monitoring/monitor.py`; `c8_dashboard/dashboard.py`; `scripts/web_dashboard.py`, `live_terminal.py`, `run_mlb_dashboard.py`, `run_session_report.py`, `run_mlb_calib_monitor.py`, `run_band_monitor.py`, `run_power_calc.py`, `assert_ledger_invariants.py`, `session_delta.sh`, `post_game_g3_resolve.sh`, `post_game_g4_resolve.sh`, `resolve_procedure.sh`, `.claude/hooks/governance_scan.sh`, `src/prediction_market_bot/run_resolve_mlb.py`. These switch to one shared `load_pool(path)` (snapshot + tail replay).
- **Direct writers (must go through the trader or a compaction call, never `write_text`):** `backfill_logic_epoch.py`, `backfill_band_field.py`, `gg271_bound_t4_rejected_positions.py`, `correct_t4_game_dates.py`, `repair_stuck_mlb_positions.py`, `t502_repair_d2_stuck_open.py`, `t503_repair_d1_d3_epoch12.py`, `apply_resolved_hits.py`, `apply_resolved_nfl_game_markets.py`.
- **Lag-tolerant (offline analysis on pulled caches):** the roughly 30 remaining `scripts/exp_*`, `run_exp*`, `t5xx_*`, `mc_*`, `build_*` scripts read `.vps_portfolio_cache_*` copies. They keep working unchanged only if the pull step (`src/.../fetch_kalshi_prices.py`, `run_resolve_local.py`, and the cache-refresh in the governance hook) pulls a freshly compacted snapshot; that pull step is the change, and each such script must surface `log_seq` staleness rather than silently reading old data (the GG-166 class of failure).

### Verification by `assert_ledger_invariants.py` (alarm-only, never `--strict`)

New assertions over the (snapshot, log) pair: (L1) `seq` is gapless and the hash chain is intact from `log_seq + 1` to head; (L2) replaying the tail over the snapshot yields no `position_id` conflicts and every `open`/`reject` id in the tail is present in the resulting state; (L3) when the snapshot was compacted at head (`log_seq == last seq`), the replayed state and the snapshot are equal after canonical serialization; (L4) tail length and age are under the compaction bounds (an unbounded tail means compaction has stopped). Violations go to stderr and the JSONL report, as today; no exit-code change.

### Accepted failure mode

- A crash between the venue accepting an order and the log append leaves an exchange order with no ledger row. This is the same window that exists today between `submit_order` and `_save`; this ADR does not close it.
- A power loss can drop at most the one event whose append had not yet returned; its caller was never told success.
- A torn final log line is ignored and reported, not repaired.
- Readers that bypass `load_pool` see a snapshot up to one compaction interval old. Accepted only for lag-tolerant analysis, and only with the staleness field surfaced.
- The two-file consistency relies on the flock; network filesystems are unsupported (same as today).
- A SIGKILL between temp write and rename leaves a stale `*.tmp.*` file next to the pool (already accepted in D1); it is inert and never read.

## Expected effect (to be re-measured at implementation)

Per bet: one appended line (about 1.4 KB, one fsync) plus a tail-only reload, instead of about 383 ms and 8.8 MB. The 802-open burst becomes roughly 2 compactions (about 0.6 s of rewrite) instead of about 5 minutes. Compaction cost still grows with pool size but is paid per 500 events, not per bet.

## Alternatives considered

- **Compact JSON separators only.** Measured: 22% fewer bytes, 52–71% less time (much of it from avoiding Python's slow `indent=` encoder path). It does not change O(events × size), and costs human readability of the ledger. Not adopted here; reasonable as a stopgap if this ADR is declined.
- **Batch saves to end of cycle.** Reduces calls but widens the crash window for opened bets and changes what the caller is told, which is a semantic change to `open_position`. Not adopted.

## Not in scope

No change to sizing, `kelly_fraction`, any band monitor's counting, `--strict`, or any deletion of rows. No relabeling of existing rows.
