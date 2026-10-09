# W62.2 — Exploratory part 2 results (EXPLORATORY — not a verdict)

## Part A — secure the history (2026-10-09)
- **Defect registered:** GG-538 (GG-533 was reserved by W61.3, never registered).
- **Fetch status:** complete. 892 settled KXNFLGAME markets listed = 892 candle sets (1m and 60m); 0 without hourly candles; 880 ok / 12 flagged.
  Coverage by close month in `KALSHI_HISTORY_MANIFEST.md`; 666 are the 2025 season, 226 are 2026-season (ineligible, not read).
- **Rebuild:** `candles/` and `markets/` regenerated from the extended `raw/` into a scratch `--store`; tracked `markets/` and `VALIDATION.json` untouched.
- **Durable copy:** VPS `/opt/prediction-market-bot/exp_output/KALSHI_HISTORY/` (`raw/` + `rebuilt_2026-10-09/`); 12G free; all 5 sha256 match local.
- **Charter:** data section added (addendum 2026-10-09).
- **Open for operator:** refresh the stale tracked `markets/`+`VALIDATION.json`? scheduled VPS copy of `raw/`?
