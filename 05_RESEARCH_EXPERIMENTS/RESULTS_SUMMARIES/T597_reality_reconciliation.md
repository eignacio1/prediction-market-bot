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

## D2 — T3 (`mlb_player_prop_hits:T3`) measurement

**Verdict: MISFILED (as a speed-paid-for shallow cell) — with one stated caveat on what "execution advantage" could mean here.**

Evidence (VPS, `/opt/prediction-market-bot/logs`, measured 2026-09-30 ~04:00Z):

| Test | Measured | Source |
|---|---|---|
| Cadence | every 15 min, 20:00-23:45Z and 00:00-03:45Z (32 runs/day); 3,058 report files since 2026-06-26 | crontab; `t3_mlb_*.json` |
| Achieved end-to-end latency (scheduled minute -> report written) | median 30.1s, p95 96.4s, max 220.0s, **0 of 3,058 > 300s** | file mtime minus 15-min slot; upper bound (includes cron start + Python import + Kalshi fetch) |
| SLA | 300s (`execution_bands.py` T3), met on every run | `BandConfig.execution_sla_s` |
| Tree depth | 1 scalar comparison: `price_drift = current_mid - t1_mid` vs `MOMENTUM_THRESHOLD`; then a multiplier on the cached T1 edge. Inputs: T1 direction, T1 mid, T1 edge, live mid. No model, no features. | `run_t3_mlb_pretip.py:184-215` |
| Order path | **None.** Docstring: "Read-only scan — never places orders." `kelly_fraction=0.0` (ADR-0048). Output is a JSON report only. | `run_t3_mlb_pretip.py:29,265` |
| Execution advantage at horizon | **None measurable.** The SLA is met, but nothing executes; the 900s poll interval is 3x the 300s SLA the band claims its edge window needs. No latency-thesis measurement exists for T3 (T-569 measured T4M-PROJ only). | above |

Reading against the horizon doctrine (ADR-0068): T3 is a shallowest-tree cell (one drift comparison) claiming a speed band's SLA, but its realized cadence is slow and it has no order path, so the shallowness is not paid for in execution speed. Latency is fine; there is simply nothing to be fast *at*. That is "shallow without being fast" in the operative sense -> MISFILED.
Caveat: the 30s median shows the *compute* is fast enough for a speed band; what is missing is a poll rate and order path that would use it. Whether T3 should be rebuilt to earn its band, or reassigned, is an operator decision -> drafted in D5, not applied.

Doc drift found: `EXECUTION_BANDS.md` lines 240-244 say T2/T3 cron lines are "commented out until Phase 7 activation"; both are live on the VPS. T3 also reports weights of 0.10 (line 222) while code is 0.0 (ADR-0048).

## D4 — T1 tree: 18 features, not 78

**Measured:** the production T1 MLB model (`mlb-v1-a1c25470`, `models/mlb_v1_model_meta.json` on the VPS) has `feature_count: 18`, all quantitative, **0 qualitative**: `b2b_flag, ba_l10, bb_rate_l10, days_rest, h_l10_mean, hr_rate_l10, is_home_game, k_rate_l10, obp_l10, opp_runs_allowed_l10, opp_sp_bb9_l5, opp_sp_era_l5, opp_sp_is_known, opp_sp_k9_l5, ops_l10, park_factor_hits, slg_l10, team_id`. The live run confirms it: `run_mlb_paper_trade.py` logs "18 features | thresholds=[1, 2]" on every run. LR + per-threshold Platt, trained 2026-06-24 (ADR-0004). Note `ba_l10_shrunk` (ADR-0047) is in the feature CSV but is **not** in the trained model's 18 — the shrinkage does not reach the model (registered below).

**History of the 78:** first appears in commit `b1d3110` (2026-05-29) in `EXECUTION_BANDS.md`, `STRATEGY_OVERVIEW.md` and the `execution_bands.py` comments as "78 features (31 quant + 47 qual), QS-2026-05-28-002" — the NBA experiment model (EXP-008/009/010, all NBA, still say 78 accurately). It described NBA, written before any MLB model existed. The MLB T1 model was trained 2026-06-24 with 18. So **it was never true of MLB T1**; it stopped describing the live system the day the pool switched to MLB. Nobody re-derived it; ADR-0068 and CLAUDE.md inherited it.

**Corrected (restating docs only; no ADR Decision section touched):** `EXECUTION_BANDS.md` (3 places + table row), `STRATEGY_OVERVIEW.md` (2), `execution_bands.py` (2 comments; no behavior change, parses clean).
**Not corrected — outside my ownership, see gaps:** `CLAUDE.md:111` ("full 78-feature pipeline"), and ADR-0068's context. NBA-specific `run_exp0xx.py` and `train_and_save_model.py` correctly describe the NBA model and are left alone.
Also stale in the same table (out of D4 scope): T1 Kelly shown as 0.25; code is 0.0 (ADR-0048).

## D3 — Registry corrections for `mlb_player_prop_hits` T1/T2/T3

**This section RECORDS REALITY. Nothing here is a promotion, band reassignment, activation or deactivation.**

Each cell verified independently on the VPS (2026-09-30):

| Cell | Was | Now | Independent evidence |
|---|---|---|---|
| T1 | NOT_IMPLEMENTED | SHADOW | cron `0 11` `run_mlb_paper_trade.py`; recent runs log "players in live MLB markets" (73/70/32) and "Bets placed today: 0"; 18-feature model evaluates; `kelly_fraction=0.0` (ADR-0048); `paper_portfolio_mlb.json` last written 2026-08-06, 0 open positions |
| T2 | NOT_IMPLEMENTED | SHADOW | cron `30 19` `run_t2_mlb_sameday.py`; 2026-09-29 report: t2_evaluated=4, scratches=3, live_game_skips=12, bets_placed=0; kelly 0.0 |
| T3 | NOT_IMPLEMENTED | SHADOW | cron every 15 min; 3,058 reports; read-only, no order path (D2); kelly 0.0 |
| T4M-PROJ | ACTIVE | **unchanged** | kelly 0.0 while registered ACTIVE ("only cell placing live bets") — that is the GG-320 question; drafted in D5, not touched |

Why SHADOW and not ACTIVE/DARK: `CellStatus.SHADOW` is defined as "paper-evaluate this cell without betting", which is exactly the measured behavior. DARK means paused; these run daily. `citing_decision="ADR-0048"` (the zeroing). Each cell's `notes` carries "records reality, not promotion". Tests updated (`tests/test_market_type_registry.py`: T1 assertion and the allowed-status set); 48 pass, 243 across all registry-consuming tests. Any move toward ACTIVE would require formula-assertion coverage and is only drafted (D5).
Not done: no generated coverage matrix in `02_ARCHITECTURE_DESIGN/` was regenerated from the registry (see gaps).
