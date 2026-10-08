# W59.3 — NBA opening-night readiness, NHL goalie verdict, ADR-0070 widened + accepted

Status per part: **A merged (#179); B DONE (verdict b); flip-check filename fix in follow-up PR; preseason cron installed 2026-10-08, first run wrote 16 T1 rows to PREGAME_SHADOW_PRESEASON/NBA_NBA_MONEYLINE_T1.jsonl; t4-mlb restart: not_needed** · B not started · C not started. Updated per part; newest state at top of each section.

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

## Part B — NHL goalie verdict: **(b) the API does not flag the starter in time** (GG-401 stays OPEN)

Source: branch `data/nhl-goalie-probe`, `goalie_source_probe.jsonl`, 15 readings from 3 probe runs (2026-10-07 01:27, 07:41, 2026-10-08 00:55 UTC). No NHL score was read.

| Reading class | Games | Starter flag present (boxscore or landing) |
|---|---|---|
| ≥15 min before puck drop, inside the 15–60 min T3 window | FLA@LAK (32.4 min) | **0 of 1** |
| ≥15 min before drop, just outside window | EDM@ANA (65.0 min) | 0 of 1 |
| ≥15 min before drop, far early (~949–1099 min) | PIT@WSH, COL@WPG, EDM@ANA | 0 of 3 (uninformative) |
| <15 min before drop | VGK@SEA (12.4) | 0 of 1 (excluded) |
| After puck drop (LIVE/CRIT, 85–148 min in) | 8 games | **0 of 8** |

Two slates (10-06/07 and 10-07/08) have ≥15-min readings. k = 0 of n = 2 in-window-or-near games (n = 5 counting far-early).

**Positive control (VPS, 2026-10-08, read-only GET):** the probe's extractor is sound. Finished boxscores `2026020044` and `2026020045` (state OFF) show `starter: true` on exactly one goalie per side. So the flag exists, but the same field is **null for games 85–148 minutes into play**. A flag that is absent mid-game will not be present before puck drop. This is why (b) and not (c): the absence is explained, not merely unobserved. Caveat stated plainly: pre-puck-drop n is small (2 informative games); the mid-game null is the stronger evidence, and it is a different time point than the one T3 needs.

**Per the W52_D rule: (b) means no StarterProvider is implemented; I stop here.** GG-401 is not resolved: **no NHL T3 score may be read.**

### Exact pre-registration amendment for the operator (EXP-036, "Model-side commitments", line 42)
Replace *"Goalie: projected starter at T1/T2, confirmed starter at T3 when the source shows it; flagged per row."* with:

> Goalie: projected starter (last start) at every band, T3 included; no confirmed-starter source is available before puck drop (W59.3 probe: `starter` flag absent pre-drop and throughout live play, present only once the game is final). Rows are flagged `confirmed=False`.

Operator choice (W52_D): adopt this amendment, or a different confirmed-starter source (none identified). Moving T3 later is impossible (cannot pass puck drop). An ADR is not required to amend a pre-registration that has no judged data yet, but that is the operator's call. This amendment is **not applied** by this session.


## Part C — ADR-0070
Not started.
