# T-597 — Reality reconciliation (Wave 42.x)

**Status:** IN PROGRESS (sections appended per deliverable). **Decisions logged:** n/a — GOVERNANCE_GAP_LOG / DECISION_LOG are owned by 42.2; gaps are listed under "GAPS FOUND — FOR REGISTRATION". Session-start protocol run in full: stub scan CLEAN, GG-id uniqueness OK, 113 OPEN gaps (132 headers = 132 status lines), Step 4 VPS health all green (t4-mlb active, cycle log age 0h, dashboard NRestarts=0, 0 oom-kills).

## D0 — Predecessors and sync
| Item | Before | After |
|---|---|---|
| Shared `main` tree (untouched — holds another session's uncommitted edits) | `9f2b837`, 64 behind origin | unchanged, deliberately |
| `origin/main` | `d81742e` (T-595 close) | `d81742e` + this session's claim commit |
| This session's worktree | — | branched from `d81742e`, claim `T-597` pushed, unique on origin (re-verified after push) |
| VPS `/opt/prediction-market-bot` | `a367019` (T-595 D4) | unchanged — no deploy, no restart (only T-595 close-out docs missing) |
| T-593 (41.3) | branch `664f90f` logged "MERGED: NO" | **Nothing to land.** Its code commit `8554e12` is content-identical to `91c1455`, already on `origin/main` (`git diff` of `nfl_ingestion.py` + `test_t593_nfl_extended_capture.py` between main and the branch is empty). The branch tip differs only by stale close-out commits; merging it would *delete* T-595's work (44 files, −27k lines), so it was correctly not merged. The claim-log row "MERGED: NO" is therefore misleading: the code is on main. |
Claim note: `T-596` was taken by a concurrent session 20s before my first attempt; the guard refused, I re-claimed `T-597`.

## D1 — NFL capture: is it on?
**No. It is not on, and there is no existing schedule for it to be "inside".**

Evidence from the running system, not the repo:
1. `crontab -l` on the VPS: the only NFL entries are 7 `archive_market_prices.py --series KXNFL*` price-capture lines (Sun/Wed/Sat 17–23Z, Mon/Tue/Thu/Fri 0–3Z). None touch nflverse or `NFLIngestionClient`. There is no NFL ingestion cron and no T1 NFL game-market cron (its portfolio file was last written by a hand-run, `pre_t587_handrun_20260929`).
2. `grep -rn NFLIngestionClient src scripts` → **zero production callers**; only tests import it. `capture_extended()` has no invoker. The widened allowlist is opt-in (`include_extended=True`) and nothing passes it.
3. VPS `exp_output/NFL/INGESTION_CAPTURE/` holds only `capture_manifest_2026_20260930T050536.json` (git-tracked). The two parquet files it names exist nowhere on the VPS (`find /` → manifest only). Parquet is gitignored.
4. The only real rows are 2 parquet files in the *ended* T-593 worktree on the operator's laptop (`PM-worktrees/20260930T050102Z-nfl-ingestion-widen/...`). That is one manual run at 2026-09-30T05:05:36Z, not a capture regime.

So "per week since it was enabled" = **one snapshot, zero enabled weeks.** What that one snapshot contains (non-null counts, schedule 2026):

| wk | games | temp/wind | roof/surface | QB (4 cols) | coaches | referee |
|---|---|---|---|---|---|---|
| 1 | 16 | 10 | 16 | 16 | 16 | 16 |
| 2 | 16 | 10 | 16 | 16 | 16 | 16 |
| 3 | 16 | 13 | 16 | 16 | 16 | 16 |
| 4 | 16 | 0 | 15 / 16 | 16 | 16 | **0** |
| 5 | 15 | 0 | 12 / 15 | 15 | 15 | 0 |
| 6 | 14 | 0 | 12 / 14 | **0** | 14 | 0 |
Team stats: weeks 1–3 only, 32 rows/week, all six N5/N6 columns 32/32. All 11 schedule and 6 team-stat widened columns are present.

Spot check against nflverse, fetched fresh ~20 min after capture: schedule sha256 `62032e26…` **identical**, 272/272 rows, **0 mismatches** across all 11 extended columns; team stats 96/96 rows, **0 mismatches** across 6 columns; 3 sampled games (`2026_03_LAC_BUF`, `2026_02_CLE_TB`, `2026_03_KC_MIA`) match on temp, wind, roof, QB, referee, coach. Capture is faithful. Week 4 (played) is still unpublished upstream, so the source lags games.

**Why I stopped short of enabling it.** Every route to "on" crosses a line I was told not to cross: (a) a cron entry is new scheduling; (b) hooking `capture_extended` into `archive_market_prices.py` or its window modifies the price-capture path (standing DO NOT); (c) a manual VPS run is one more snapshot, not "on". The brief said that if I judged the line differently I should stop and say so — I judge that **there is no schedule to configure inside**, so enabling = scheduling. Operator decision needed; see D5 entry CC-B.
Cost of waiting is real and grows: the source is a rolling, post-hoc snapshot, so pre-kickoff QB/weather/referee values are only obtainable by capturing *before* each kickoff. Each week without a pre-kickoff capture permanently loses that week's point-in-time state.
