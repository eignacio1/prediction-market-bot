# T-589 — T4 ledger durability (Wave 39, Block 39.1) — Results

**Session:** `t4-ledger-durability` · **Branch:** `session/20260930T001343Z-t4-ledger-durability` · **Date:** 2026-09-29
**IDs claimed:** T-589 (T-588 was taken by 39.2). ADR-0067 written as PROPOSED (unique in the tree; appears elsewhere only in my claim row). No GG numbers claimed. `GOVERNANCE_GAP_LOG.md` and `DECISION_LOG.md` were not written.
**Nothing was deployed, no service restarted, no live pool file touched, no sizing/kelly line touched, no Kalshi order placed.** All measurements ran on copies of `logs/.vps_portfolio_cache_*.json`.

**Caveat on every timing figure below:** measured on a macOS laptop, not the VPS. Ratios and shapes transfer; absolute ms do not.

---

## D0 — Land predecessors and sync

| ref | sha |
|---|---|
| shared `main` (before) | `9f2b83759db4fab62ac3385f0deebb6384d70fb1` |
| `origin/main` at session start | `f293c0e` |
| worktree base (merge-base with origin/main at claim) | `de790ec7bf9fc77cf688e6e847cee30bac9878a8` (my claim row on top of f293c0e) |
| worktree HEAD (after D6) | `fd3fc117665fd2bd571753e370d1000a5551b45d` |
| `origin/main` now | `0870f14fe2d0a372979e2025e07fed485638aff9` (moved during the session; not mine) |

- **Fast-forward of the shared `main` tree was NOT done.** Exact refusal: `.git/index.lock` exists, held by PID 25860 (a macOS Virtualization VM XPC process). I did not remove the lock or work around it. The shared tree therefore still reads `9f2b837`, 28 commits behind. The worktree was created from `origin/main` instead, which gave the same content. **Hand-back: someone must release the lock and fast-forward the shared tree.**
- **Unmerged Wave 38 branches:** none. Both Wave 38 branches were cherry-equivalent to commits already on `origin/main`.

## D1 — Atomic write in `_save()` (commit `c6dce64`)

`_save()` now writes via `_atomic_write_text`: temp file in the same directory (`O_EXCL`, `<name>.tmp.<pid>.<uuid8>`), mode and owner copied from the prior file, `write` + `flush` + `fsync`, `os.replace`, best-effort directory fsync, all inside the existing flock. Temp file is unlinked on any exception. Locking and `_reload_locked` are untouched.

Tests: `tests/test_paper_trader_atomic_write.py`, 14 cases. Interruptions are injected at real boundaries, never by mocking `_save`: `RLIMIT_FSIZE` (kernel refuses the write mid-file, SIGXFSZ ignored), `os._exit` between write and rename, `fsync` raising `OSError(ENOSPC)`.
- (a) interrupted save leaves on-disk bytes identical and parseable: 3 tests
- (b) no temp left after success / failure: 3 tests
- (c) round trip through the real `_reload_locked`: 1 test, plus a probe proving `os.replace` runs while the flock is held
- (d) mode preserved for 0600/0640/0664/0644, uid/gid preserved, new-file mode equals what `write_text` gave under the umask

**Fail-before / pass-after:** on the old code 6 of 14 fail behaviourally (fsync failure, kernel-refused write, hard kill, no-temp-after-failure, temp-in-target-dir, flock probe); the other 8 pass on both versions by design (they pin behaviour that must not change). After: 14/14 pass.

**Residual, accepted:** SIGKILL between temp write and rename leaves an inert stale `*.tmp.*` file beside the pool. The ledger itself is untouched (asserted).

## D2 — Cost of a save (`scripts/bench_paper_trader_save.py`, commit `2bc0227`)

Source: real T4 pool copy, 8,819,710 B, 5,986 rows (63 open + 3,923 closed + 2,000 rejected). Scales duplicate `closed_positions` under fresh `position_id`s. Median of 15 saves.

| scale | rows | bytes (indent=2) | ms/save | MB written/save | bytes (compact) | ms (compact) | saving |
|---|---|---|---|---|---|---|---|
| 1x | 5,986 | 8,819,710 | 278.2 | 8.82 | 6,904,555 | 108.4 | 22% bytes / 61% ms |
| 2x | 9,909 | 14,601,696 | 607.2 | 14.60 | 11,388,158 | 175.0 | 22% / 71% |
| 5x | 21,678 | 31,947,650 | 1,106.8 | 31.95 | 24,838,963 | 373.4 | 22% / 66% |
| 10x | 41,293 | 60,857,575 | 2,057.5 | 60.86 | 47,256,973 | 985.5 | 22% / 52% |

**Compact separators: NOT switched.** Byte saving is a flat 22%. The ms saving (52–71%) is mostly Python's `json` taking its slow pure-Python path whenever `indent=` is set, not I/O. Neither changes the O(events × pool size) shape, which is the actual problem (D3/D4). Readability cost if adopted: the ledger becomes one line, so line-oriented inspection and `git diff`/`grep -n` on it stop being useful. Revisit only if ADR-0067 is declined.

## D3 — `_save()` call counter and realistic cycle

**Call sites:** 7 executable `self._save()` sites in `paper_trader.py` (`ensure_persisted`, `open_position` ×2, `exit_position`, `resolve_pending`, `settle_position`, `mark_aged_open`), **not 13** as the brief stated. The 13 was not reproduced (see Gaps). Outside that file only `scripts/gg271_bound_t4_rejected_positions.py:173` calls `_save` directly.

**Instrumentation (commit `4b7a2af`):** `_save()` is now a thin wrapper around `_save_impl()`; it records `calls`, cumulative `ms`, `bytes`, and per-caller `by_site` in `PaperTrader.save_stats`. It changes no behaviour. Full `tests/test_paper_trader.py` (51) passes with it.

**What "one realistic cycle" was, honestly:** live games cannot be replayed offline, so this is a **modelled** cycle, not a capture from the running `t4-mlb` process. I drove the real `PaperTrader.open_position` (real `_reload_locked` and `_save`, `pool_isolated=True`, no Kalshi client, so no order-throttle sleeps) against a copy of the real pool, with counts taken from measured cadence.

Real cadence from `entered_at` on the pool (3,986 open+closed rows over 46 days): mean 86.7 bets/active day, median 65, max 254; recent days 115, 135, 238, 144, 204, 102, 54; busiest minutes 26, 24, 22 opens. Rejections: 1,795 on 2026-09-20, 205 on 2026-09-21.

| driven | `_save` calls | save ms | wall ms incl. reload | MB written |
|---|---|---|---|---|
| 1 open | 1 | 292.6 | 382.7 | 8.8 |
| 26 opens (busiest observed minute) | 26 | 7,705 | 9,729 | 230 |
| 65 opens (median day) | 65 | 18,945 | 23,833 | 576 |
| 254 opens (busiest day) | 254 | 80,079 | 100,142 | 2,282 |
| 200 rejects | 200 | 74,455 | — | 1,735 |

Saves occur once per opened bet and per rejected order, **not per evaluation**. Evaluations that do not fire do no I/O on the pool.

**Does the full-file-rewrite design hold at the throughput Wave 38 demonstrated?**
- At today's measured T4 demand: **survivable.** Busiest minute (26 opens) is about 9.7 s of each 60 s, about 16% of wall clock inside the flock, about 230 MB/min written.
- At the Wave 38 shape (802 opens + 288 rejects ≈ 1,090 saves in one run): **no.** At roughly 0.3–0.4 s per save on a T4-size pool that is about 5–7 minutes of flock-held time and about 7–10 GB written, with every other runner blocked on the lock. (The 802 figure is the NFL game-market runner; its own pool is small, so this is a projection onto a T4-size pool, not a measurement of NFL.)
- Under a rejection storm (1,795 rejects in a day): about 11 min/day and about 16 GB.
- Cost is O(N·S) and S grows with every resolved row, about 2 s/save at 10x.
- Latent today: ADR-0048 zeroed `kelly_fraction`, so T1 and T4M-PROJ place no sized bets. The problem returns when sizing resumes.

**Verdict: the design does not hold at burst throughput → D4 applies.**

## D4 — ADR-0067 (PROPOSED)

`03_DECISIONS/ADR-0067_append-only-position-log.md`. Status PROPOSED, no register row, not accepted. Contains: event schema (seq, hash chain, crc), write-order rule (log fsync before snapshot ever reflects it), compaction, the 5-step recovery procedure (snapshot then tail replay, idempotent by `position_id`, halt on mid-chain corruption vs ignore torn tail), the by-file reader list (must-change / direct writers / lag-tolerant), new `assert_ledger_invariants.py` assertions L1–L4 (alarm-only), accepted failure modes, and the alternatives considered (compact JSON, batching). Stopped there as instructed; no implementation.

## D5 — Growth of `closed_positions` (real data, read-only)

| pool | file bytes | closed rows | closed bytes | share of file | B/closed row | keys/row | growth |
|---|---|---|---|---|---|---|---|
| mlb_t4 | 8,819,710 | 3,923 | 5,414,333 | 61% | 1,380 | 39 | about 85 closed/active day over 46 days, about 118 KB/active day; recent 100–240/day, about 140–330 KB/day |
| mlb | 615,698 | 468 | 541,597 | 88% | 1,157 | 35 | about 19 closed/active day, about 22 KB/day |
| nba | 162,413 | 158 | 152,297 | 94% | 964 | 29 | 5 active days; frozen (dark) |

Also in mlb_t4: open rows 84,503 B; rejected 2,833,607 B (2,000 rows, capped by the GG-271 ring buffer, so bounded). `closed_positions` is the only unbounded list. Books: mlb_t4 bankroll 1000.0, realized −88.83; mlb 733.75 / −106.01; nba 751.10 / −248.90. **Nothing proposed that deletes or drops a row.**

## D6 — `model_identity` mandatory at `open_position` (commits `eed471f`, `fd3fc11`)

`open_position` now raises `MissingModelIdentityError(ValueError)` when `approval["model_identity"]` is absent, non-string, blank, or literal `UNKNOWN` (case-insensitive, whitespace-trimmed). No default. The check runs after the existing `size <= 0 or PASS` early return and **before** any venue order or ledger mutation. The stored value is the stripped string. No row was backfilled or relabeled. Tests: `tests/test_paper_trader_model_identity.py`, 12 pass (bad values write nothing and leave bytes identical; the Kalshi client is never called without identity). `_make_approval` in `tests/test_paper_trader.py` now supplies `model_identity="TEST-MODEL"`; `test_paper_trader.py` 51/51 pass.

**Read-only census of rows currently reading "UNKNOWN":**

| pool | list | rows | literal "UNKNOWN" | key absent |
|---|---|---|---|---|
| mlb_t4 | open | 63 | 63 | 0 |
| mlb_t4 | closed | 3,923 | 929 | 2,994 |
| mlb_t4 | rejected | 2,000 | 2,000 | 0 |
| mlb | open | 17 | 0 | 17 |
| mlb | closed | 468 | 0 | 468 |
| mlb | rejected | 16 | 0 | 16 |
| nba | closed | 158 | 0 | 158 |

In mlb_t4 **zero rows carry any real identity**; the newest rows are the literal "UNKNOWN".

### ⚠ This change is NOT safe to deploy as-is

The live T4 runner writes "UNKNOWN" today, so it does not supply `model_identity`. **Deploying D6 before callers are migrated would make every `open_position` call from those runners raise.** Per instructions this was pushed to the session branch only.

Production callers that call `open_position` and must be migrated first: `run_t4_mlb_live.py` (~l.1680), `run_t1_mlb_game_market.py:373`, `run_t1_nfl_game_market.py:415` (already supplies one), `run_t2_mlb_sameday.py:546`, `t4_live_runner.py:614`, `run_t4_live.py:760`, `run_paper_trade.py:692`, `run_mlb_paper_trade.py:1036`, `scripts/replay_harness_t427.py:146`. (`run_t4_live.py:543` is an `exit_position` call and is unaffected.)

**Test impact, measured** (13 test files that call `open_position`, run before vs after D6 on the same commit lineage): baseline **11 failed / 1,137 passed**; after D6 **117 failed / 1,031 passed**. **106 new failures**, all from callers/fixtures lacking `model_identity`, in 12 files:

| file | new failures |
|---|---|
| test_t187e_mlb_resolve.py | 27 |
| test_t159_portfolio_invariants.py | 21 |
| test_t146_t147_exit_mechanics.py | 17 |
| test_run_t4_mlb_live.py | 16 |
| test_t194_mlb_age_out.py | 7 |
| test_t164_order_throttle.py | 4 |
| test_t174_pnl_reconciliation.py | 4 |
| test_approval_path_invariants.py | 3 |
| test_golden_replay.py | 3 |
| test_replay_harness_t427.py | 2 |
| test_gg303_order_id_write_defect.py | 1 |
| test_run_t1_nfl_game_market.py | 1 |

**Pre-existing failures, unchanged by this session** (the same 11 fail on the parent commit): `test_run_t1_mlb_game_market.py` 6, `test_run_t1_nfl_game_market.py` 5. Per Hard Rule 11 I did not fix them or the 106 above; migrating callers and fixtures is its own task.

---

## GAPS FOUND -- FOR REGISTRATION BY 39.2 OR WAVE 40

1. **D6 caller breakage / live T4 writes "UNKNOWN".** The live T4 runner (and every MLB/NBA path) supplies no `model_identity`. All 2,000 rejected and 63 open mlb_t4 rows are the literal "UNKNOWN". 106 tests newly fail on the D6 branch. Migration of the 9 production callers plus ~12 test files must precede any deploy of D6. Severity: blocks deploy of D6.
2. **Pre-existing test failures: 11** in `test_run_t1_mlb_game_market.py` (6) and `test_run_t1_nfl_game_market.py` (5), failing on the parent commit, cause not investigated here.
3. **Write/read amplification in the hot path.** `open_position` does a full `_reload_locked` (read+parse of the whole pool) and a full rewrite under the flock for every bet: about 383 ms and 8.8 MB per open on a 1x T4 pool. Cost grows with every resolved row (about 2 s/save at 10x). Addressed only by ADR-0067 if accepted.
4. **Rejection-storm amplification.** Every rejected order is also a full save (about 372 ms). 1,795 rejects on 2026-09-20 ≈ 11 min of flock-held time and about 16 GB.
5. **NFL/other burst risk.** An 802-open run (Wave 38, NFL game-market runner) projects to about 5–7 min of flock-held time on a T4-size pool.
6. **`ensure_persisted` calls `_save` outside the file lock**, unlike every other save site. Not fixed (out of scope).
7. **Stale temp file after SIGKILL.** D1 leaves an inert `*.tmp.<pid>.<id>` beside the pool if the process is hard-killed mid-save. Needs a periodic sweep or a documented ignore rule for readers that glob the directory.
8. **"13 call sites" claim not reproduced.** The brief said 13; the file has 7 executable `_save` sites. Someone should find where 13 came from (possibly counting comments/docstrings or another file).
9. **`.git/index.lock` held by a VM process (PID 25860)** blocked the shared-tree fast-forward; the shared `main` is 28 commits behind and now further behind `origin/main` (`0870f14`).
10. **Q7 (`assert_ledger_invariants.py`) is vacuous in a worktree**, since the pool caches are not present there, and it writes its report under the worktree's `logs/`. A worktree session can report Q7 "clean" having checked nothing.
11. **`_save` is called directly by `scripts/gg271_bound_t4_rejected_positions.py:173`** and by the ADR-0067 direct-writer list (9 repair/backfill scripts write pool files outside the trader). Any move to a snapshot+log design needs each routed through one path.
12. **Modelled, not captured, cycle.** D3's cycle numbers are modelled from measured cadence on a laptop copy; a VPS-side capture of `save_stats` from a running `t4-mlb` process has not been taken (no restart was authorized, and the counter is not deployed).
