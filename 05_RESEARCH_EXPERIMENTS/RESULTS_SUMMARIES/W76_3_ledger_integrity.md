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
