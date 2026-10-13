# W69.3 — NBA player points: projected-minutes challenger — RESULTS (EXPLORATORY)
Plan: `20261012_nba_points_minutes/README.md` (frozen before fitting; one pre-fit amendment, 2-hourly slot grid). Data: `results.json`. Run once, seed 20261012, B=20000, game-cluster bootstrap, m=8 → corrected CI 99.375%. Δ = Brier(arm) − Brier(ctrl_refit); negative = better. Folds A (test 2025) and B (test 2026) pooled.

## Integrity
* Actual frozen artifact on 2026 reproduces `ctrl_refit` Brier to 1e-15 at all four strikes (0.16345 / 0.13377 / 0.09136 / 0.05483). The control is the frozen model.
* **Coverage defect:** no injury report was found for any 2026 date Jan–Apr (95 dates, all empty; the URL pattern or archive does not serve them). Games with a report: 2023 1190/1230, 2024 1189/1231, 2025 1189/1231, **2026 417/1231 (34%)**. Fold B's injury arm therefore sees injuries only for Oct–Dec 2025; the rest is `inj_missing=1`. The 2026 injury result is diluted and not a clean test.
* Starter flag is a proxy (`min_rank`); report is snapshotted ≥4h before tip, so late scratches are unseen.

## Result (Δ Brier vs ctrl_refit; corrected CI; by test season 2025 / 2026)
| arm | strike | all Δ | corrected CI | 2025 / 2026 | star (pts10≥15) Δ | star CI | star 2025 / 2026 |
|---|---|---|---|---|---|---|---|
| minutes_box | 10 | −0.00043 | [−0.00063, −0.00023] | − / − | −0.00034 | [−0.00045, −0.00023] | − / − |
| minutes_box | 15 | −0.00022 | [−0.00034, −0.00010] | − / − | −0.00052 | [−0.00071, −0.00031] | − / − |
| minutes_box | 20 | −0.00012 | [−0.00019, −0.00005] | − / − | −0.00044 | [−0.00065, −0.00022] | − / − |
| minutes_box | 25 | −0.00006 | [−0.00011, −0.00002] | 0 / − | −0.00021 | [−0.00037, −0.00003] | − / − |
| **minutes_inj** | 10 | −0.00086 | [−0.00138, −0.00037] | − / − | −0.00051 | [−0.00084, −0.00017] | **+** / − |
| **minutes_inj** | **15** | **−0.00047** | **[−0.00079, −0.00015]** | − / − | **−0.00099** | **[−0.00155, −0.00041]** | − / − |
| minutes_inj | 20 | −0.00004 | [−0.00025, +0.00018] | − / + | −0.00060 | [−0.00124, +0.00005] | − / − |
| minutes_inj | 25 | **+0.00032** | [+0.00016, +0.00048] | + / + | **+0.00097** | [+0.00040, +0.00155] | + / + |

## Verdict against the pre-written rule
Rule: ≥1 strike with corrected CI excluding zero favourably, favourable in both test seasons, and star point estimate favourable. **Strike 15 of `minutes_inj` meets it.** Strike 10 fails (star 2025 is unfavourable). Strike 25 is significantly *worse*.
**Honest reading:** the effect is real but tiny (|Δ| ≤ 0.001 Brier, same order as the expected-modal bound 0.002), `minutes_box` (no injury data) already captures much of the gain at 10/15/20, and the injury arm degrades the top strike. The injury increment over `minutes_box` was not a pre-specified contrast and is not claimed. 2026 injury coverage is 34%. The market comparison is infeasible (no archived KXNBAPTS history).

## PROPOSED pre-registration (NOT ACCEPTED — operator decision)
* **Name:** EXP-040-P (proposed). Challenger `minutes_inj`, **strike 15 only** (strike 10/20/25 not registered; 25 shows harm, so any registered use of the arm must exclude it).
* **Judged against the MARKET (Kalshi KXNBAPTS ≥15 mid, de-vigged), not vs frozen EXP-039**, on rows dated after acceptance, logged beside EXP-039 from the 10-20 opening night if accepted before then. Same first-look rule as EXP-039: n=300 player-games for the cell, game-cluster bootstrap, B=2000.
* **Expected modal outcome (stated now):** edge vs market negative to zero. The gain over a frozen model that the market already prices (the market sees late scratches this model does not) is expected to be absorbed; the registration is a test of whether any availability signal survives against the market, and a null is informative.
* Model frozen as fit on seasons 2023–2025 (calibrate 2025) with the plan's recipe before any logging; no retraining (Hard Rule 4).

## Next mechanism if the operator declines
Fix the 2026 report coverage (source gap) and re-test the injury increment over `minutes_box` as the single pre-specified contrast; or switch to a true starter/lineup feed.

## Wired W70.2 (2026-10-12/13)

**What was wired (PR #238, merged; VPS HEAD 62443040 read back over ssh).** `NBAPlayerPointsMinutesForecaster` is built from `models/nba_player_points_minutes_v1.json` and refuses to construct unless sha256 == `c47cbac7...548527`. Runtime point-in-time injury fetch (`c1_signal_ingestion/nba_injury_reports.py`): same ET 2-hourly grid as the study, slot <= min(now, tip-4h), asserted in code; none available -> `inj_missing=1`. The arm runs inside `scripts/run_nba_player_points_shadow.py` after EXP-039 (existing cron lines, no new cron), strike 15 only, ledger `exp_output/PREGAME_SHADOW_EXP040/NBAMIN_*.jsonl` (preseason dir in preseason mode). Every row carries `artifact_sha256`, `injury_snapshot`, `injury_snapshot_utc`, `mean_points` and the minutes features. EXP-039 rows are byte-identical (`row_extra` default is empty; tested). No stake, order or kelly change; EXP-040 does not stake. Silent-arm spec and D1 manifest entry added. Tests: `tests/test_exp040_minutes_arm.py`.

**Finding: GG-610's "34% coverage" is a URL problem.** The league renamed the injury PDFs on 2025-12-22 (`..._{HH}_{MM}{AM|PM}.pdf`, every 15 min); the old name returns 403 after that date. PR #241 fixes the live fetch only (`url_for`, User-Agent header, `pypdf` dependency). The study code and its coverage figure are untouched; a re-test of the injury increment with full 2026 coverage is now possible and is the "next mechanism" above.

**Finding: VPS had no 2025-26 player box scores,** so EXP-039 and EXP-040 would have logged nothing. Backfilled `data/raw/nba/players_2026.json` (1231 box scores). The 2026 store is static; the daily cron only refreshes 2027.

**Read-back.** Direct forecaster harness on the VPS against the real schedule: 12 of 12 forecasts carried the artifact sha and injury fields (injury time null: no report published). No ledger rows exist yet: no KXNBAPTS markets are open, so the preseason run and dry runs wrote nothing.

**Caveats.** Preseason has no published injury reports, so preseason rows will have `inj_missing=1`. `min_rank` is degenerate early (21-day rotation window empty). Parser quirk ("og" for OG Anunoby) is only partly covered by the token-subset fallback. 2027 store is empty, so early-season rows lean on 2025-26 history. Merge of #238 went in with CI red on 6 pre-existing, unrelated failures (same 6 as the prior main run).

**Pre-registered modal outcome unchanged:** edge vs market negative to zero; first look n=300 player-games.
