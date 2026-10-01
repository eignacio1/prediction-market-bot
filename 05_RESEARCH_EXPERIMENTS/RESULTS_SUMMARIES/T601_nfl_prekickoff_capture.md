# T-601 — NFL pre-kickoff capture (Wave 43.3)

**Status:** D0–D6 COMPLETE; cron DRAFTED, NOT installed. **Decisions logged:** n/a — GOVERNANCE_GAP_LOG / DECISION_LOG owned by 43.1; candidates listed under "GAPS FOR 43.1".

## D0 — Predecessors and sync
- T-593's code is already on main (`91c1455`); its branch has nothing to land (merging it would delete T-595's work). Nothing merged.
- Before: worktree created at `633e1b5`. After sync (`pull --rebase origin main`): `d27d60e`; claim commit `b7522e5` (T-601; T-600 was taken by 43.2 12 s earlier, guard refused, re-claimed and re-verified unique).
- Brief's path `src/prediction_market_bot/nfl_ingestion.py` does not exist; real path is `.../c1_signal_ingestion/nfl_ingestion.py`.

## D1 — What is lost, per week
T-597's premise is **partly wrong**. The release `games.csv` is a rolling snapshot, but it is a copy of `nflverse/nfldata` `data/games.csv`, which is git-versioned (~10-min commits). Point-in-time state at any past kickoff is reconstructable from that history (1,116 commits since 2026-09-08 read; 92 sampled; HEAD of nfldata matches the release: 0 mismatching extended cells). Also, T-597's "Week 4 (played)" is wrong: week 4's first kickoff is Thu 2026-10-02 00:15Z, ~23 h after the first live run.

Reconstruction of state at kickoff −15/−60/−180 min vs. today's final values (176 cells = 16 games × 11 fields per week):

| Week | Games | Pre-kickoff null | Final null | Cells differing pre→final | Verdict |
|---|---|---|---|---|---|
| 1 | 16 | 50 | 12 | 39 | **Recoverable** from nfldata history; the difference is almost entirely referee/temp/wind, which upstream fills only after the game |
| 2 | 16 | 52 | 12 | 41 | Recoverable (same) |
| 3 | 16 | 50 | 6 | 46–48 | Recoverable (same); −180 min differs by 2 cells from −60 min, i.e. some late movement exists |
| 4 | 16 | 49 | 49 | 0 (not kicked off) | **Not lost**; live capture covers it (D3) |
| 5–18 | 15,14,14,14,15,14,13,16,14,15,16,16,16,16 (= 224 incl. wk 4) | n/a | n/a | n/a | **Unknown/future**: nothing to lose yet |

What is genuinely **unrecoverable: none observed.** Referee, temp, wind are null pre-kickoff and appear only post-game, so they are not point-in-time-perishable pre-kickoff fields at all (a capture before kickoff gets nulls). Observed first-population lead before kickoff (week 5): QB id/name 215–311 h, coach/surface/roof 742–838 h; week 6 QBs not yet populated; observed value changes in sampled commits: 0 (lower bound, sampling).

**Unknown, stated as unknown:** (a) sampled change counts are lower bounds; (b) persistence of nfldata history beyond what I read (2026-09-08 on) was not tested, so recoverability depends on upstream keeping history; (c) `stats_team` has no tested upstream history; it is cumulative past results, not forward-looking, so low perishability, but untested.

Weeks remaining: 15 (wk 4–18), 224 games. Capture from here to January yields, at ≥1 record per week per source, ≈15 weeks × 2 sources of point-in-time rows covering 224 games (D5 gives the value).

## D2 — Runner and tests
- `scripts/nfl_prekickoff_capture.py`; calls `capture_extended()` into a throwaway staging dir, validates, then appends to `exp_output/NFL/INGESTION_CAPTURE/store/` (`capture_index.jsonl`, `capture_rejects.jsonl`, parquet per record). Parquets are gitignored.
- Per record: UTC capture time, source URL, upstream sha256, week-scoped content sha256, rows, kickoffs preceded (UTC), runtime commit sha, status, partial reasons.
- Idempotent per (season, week, source) on content hash; changed content appends a new record; existing files/lines never opened for write. Partial upstream data refused (exit 2) unless `--accept-partial`, which records `status=partial` with reasons — never `complete`.
- Allowlist widened by `gametime` (kickoff; schedule fact, not market-derived). `capture_extended` fixed (unbound `stamp` when no source retrieved).
- Tests: `tests/test_t601_nfl_prekickoff_capture.py` (7) + T-593's (4) = 11 passed. Covers idempotency, append-not-overwrite (old bytes unchanged, index prefix preserved), partial-data refusal (schedule, team stats, upstream failure), provenance fields.

## D3 — Hand-runs against live nflverse (2026-10-01 01:32Z, runtime sha `f015f4d`)
- Run 0 (strict): `REFUSED: 1/16 week-4 games have null roof: ['2026_04_DAL_HOU']`. Real partial upstream data; refusal worked as specified.
- Run 1 (`--accept-partial`): schedule appended `partial` (16 rows, content `7eebf0da513b3ac6…`, upstream `3c29fd1930a3aa37…`); team_stats appended `complete` (96 rows, content `16ed270d546b72c1…`, upstream `2277499e06ee9f87…`).
- Run 2: both `skipped_unchanged`; sha256 of every store file identical before/after (schedule parquet `cf463fed…`, team_stats `7668e9e0…`, index `6e87e5fa…`); index still 2 lines.
- Column-level diff of stored parquet vs a fresh live read: schedule 0 mismatching cells across 23 columns × 16 rows; team_stats 0 across 13 columns × 96 rows (`off_epa` compared as passing+rushing); no duplicate keys; provenance columns present.
- Disclosure: my first Run 1 labelled team_stats `partial` too (gap is schedule-only). I fixed the scoping, discarded that store (session-created, untracked) and redid both runs; the figures above are from the redo.

## D4 — Cron (DRAFT, not installed)
No authorization line naming this capture exists under "Needs your decision"; per the brief, nothing installed, crontab not touched. Commented block appended to `deploy/cron.conf` (existing lines untouched): Wed 18:00Z; Thu 22:30Z; Sun 11:30Z, 15:30Z, 18:45Z, 22:30Z; Mon 22:30Z — each 80–120 min before a kickoff cluster derived from real kickoff times. Lead-time basis: D1 shows QB/coach/roof/surface populate days to weeks ahead, so early capture adds nothing; the only perishable signal is a late change, so captures sit shortly before kickoff. Gaps: Saturday games weeks 15–17 and week 18's single Sunday 18:00Z slate are not covered. Timezone assumed UTC; verify against the live crontab before any install (GG-262).

## D5 — Value
EXP-027 needs n* ≈ 2,610; the remaining 2026 season is ≈224 games (≈215 with usable rows, ≈8%). Captured data cannot make EXP-027 reach n* in 2026 and supports at most a Brier/ECE read. It also is not new evidence for 2026: the allowlisted fields are largely recoverable retroactively (D1), referee/weather carry nothing pre-kickoff, and nothing is wired to a model (DO NOT). **Honest answer: this is instrumentation for 2027 and a hedge against upstream history disappearing, not evidence for 2026.** Its main present value is a durable, hash-verified point-in-time record independent of nfldata's history persisting.

## GAPS FOR 43.1 (not written by this session)
1. T-597 states "Week 4 (played)"; week 4 has not kicked off, and its "lost" claim ignores nfldata history.
2. Brief cites a nonexistent module path.
3. `capture_extended` unbound `stamp` bug (fixed here); `capture_extended` has no kickoff times, commit sha, hash dedup or completeness checks (runner adds them).
4. Upstream DAL@HOU roof null for week 4 at capture time.
5. Pre-existing: long Compass OS Health line in MEMORY_BANK trips session guard; SemanticFloorViolation count 1.
