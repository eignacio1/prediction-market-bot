# W62.2 — Exploratory part 2 results (EXPLORATORY — not a verdict)

## Part A — secure the history (2026-10-09)
- **Defect registered:** GG-538 (GG-533 was reserved by W61.3, never registered).
- **Fetch status:** complete. 892 settled KXNFLGAME markets listed = 892 candle sets (1m and 60m); 0 without hourly candles; 880 ok / 12 flagged.
  Coverage by close month in `KALSHI_HISTORY_MANIFEST.md`; 666 are the 2025 season, 226 are 2026-season (ineligible, not read).
- **Rebuild:** `candles/` and `markets/` regenerated from the extended `raw/` into a scratch `--store`; tracked `markets/` and `VALIDATION.json` untouched.
- **Durable copy:** VPS `/opt/prediction-market-bot/exp_output/KALSHI_HISTORY/` (`raw/` + `rebuilt_2026-10-09/`); 12G free; all 5 sha256 match local.
- **Charter:** data section added (addendum 2026-10-09).
- **Open for operator:** refresh the stale tracked `markets/`+`VALIDATION.json`? scheduled VPS copy of `raw/`?

## Part B — NFL first-look expectations (2026-10-09)
- Doc: `NFL_FIRST_LOOK_EXPECTATIONS.md`; study + results: `20261009_nfl_first_look_expectations/`. Isolation test 16/16.
- **Headline:** measured per-game paired-Brier SD ≈ 0.106 vs the pre-registration's assumed 0.07 -> MDE 0.038 (n=60) / 0.024 (n=150), not 0.025 / 0.016. The look cannot see the 2025-sized gap (-0.008 vs market).
- Modal verdict vs market: SHADOW (keep accruing) ~91%; RULED_OUT ~9%; CANDIDATE <1%.
- Limits: market comparison is moneyline only; spread/total vs climatology use the sportsbook line as a single-strike proxy; team-total not estimated.
- **Operator note:** the assumed SD in EXP-037 §4 looks optimistic; a second-look decision (n=150 / week 18) is unchanged by this doc, but the operator may want to know the first look is under-powered by design.
