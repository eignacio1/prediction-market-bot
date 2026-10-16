# W76.3 — Ledger integrity (GG-748, GG-747, GG-764)

Status: PARTIAL. Part A DONE and merged (PR #265, fda73e4). Part B NOT started beyond one probe.

## Part A — done
- `atomic_io.file_lock(path)`: exclusive flock on `<path>.lock`, same convention as `PaperTrader._file_lock`.
- Converted to atomic_io (tmp + fsync + replace): `correct_t4_game_dates.py` (also holds file_lock on `--apply`), `gg271_bound_t4_rejected_positions.py`, `replay_harness_t427.py`, `tag_locked_pairs_t4_mlb.py`, plus `t437_task3_rederive_outcomes.py` (found by the sweep, not in GG-748).
- `CellLedger.append`: flock, dedup re-check under the lock, GG-672 newline repair, single O_APPEND write + fsync. `_load` reloads dedup keys when another process grew the file.
- Tests: 6 processes x 60 long rows, no row lost or torn; cross-process dedup; lock helper; apply crash-before-rename leaves ledger intact; pattern guard over the five scripts. 10 pass.
- Pre-existing, not mine: 9 failures in `tests/test_run_t4_mlb_live.py` (identical before/after, stash comparison); `tomllib` missing on local Python 3.9 breaks 3 other test files.
- Sweep: 174 hits; remainder registered as GG-850 (overlaps GG-680).
- Box read-back: deploy log `vps_deploy_decisions.jsonl` 2026-10-16T00:03:24Z outcome `deployed`, `t4_mlb_verdict: skip_live_game` (t4-mlb NOT restarted, running since 05:48 UTC; it will pick up the change at its next restart). Box HEAD fda73e44; `ledger.file_lock` imports on the box. A real runner row written through the new path is NOT yet read back; the next pregame shadow cron run will do it.

## Part B — not done
- GG-764 read-side holes (`assert_ledger_invariants.py:145`, `validators.py:379`, `run_t4_mlb_live.py:1175`): untouched.
- GG-747: premise differs from the box. Box T4 portfolio (`paper_portfolio_mlb_t4.json`, 9.44 MB, 2026-10-15 19:40) shows 4316 closed / 0 open vs the prompt's 4,309 closed / 4,275 resolved. The gap must be recomputed on a read-only copy; no number is claimed here. No judged count has been changed.

## Part B (W77.3) — the closed-vs-resolved gap (GG-747)

Source: read-only scp of `logs/paper_portfolio_mlb_t4.json` (mtime 2026-10-16T02:54Z) and `logs/t4_mlb_resolved_ledger.jsonl` (mtime 2026-10-12T14:20Z) from the box. Nothing on the box was modified.

- Portfolio: 4,316 closed (all WIN/LOSS: 2,044 / 2,272), 0 open. Ledger: 4,275 rows, 0 torn, 4,275 distinct position_ids, 0 duplicates, 0 ledger ids absent from the portfolio.
- Gap now = **41**, not 34. Every one of the 41 is epoch 12, game_date 2026-10-12 (22) / 10-13 (12) / 10-14 (7), resolved 2026-10-13T06:31Z to 10-15T06:35Z, outcome WIN 13 / LOSS 28, realized P&L -10.78.
- **Cause: staleness, not a closing path.** `t4_mlb_resolved_ledger.jsonl` is a derived snapshot rebuilt by the Monday 14:20 UTC cron (`build_t4_resolved_ledger.py`). Its last build was 2026-10-12 14:20Z; everything resolved after that is simply not in it yet. The audit's 4,309 vs 4,275 (gap 34) is the same effect at an earlier moment. No row was closed without resolving; all 41 have a valid outcome and pass the builder's filters (in-memory rebuild from the copy = 4,316 rows).
- No labelled correction row needed; no live ledger row changed.
- Judged counts: the portfolio count (4,316) is unchanged. Any verdict that reads the *resolved ledger* between Monday rebuilds is up to a week stale (41 rows, -10.78 P&L right now); the next rebuild (2026-10-19 14:20Z) will close the gap to 0. No judged count changes by this finding, but a read of the ledger mid-week is not a read of the portfolio. Registered as a note on GG-747; whether to rebuild more often is a plumbing choice for the gap agent, not a pre-registration change.
- Not done: read-back of first CellLedger rows through the W76.3 lock after the next pregame shadow cron (not yet run).
