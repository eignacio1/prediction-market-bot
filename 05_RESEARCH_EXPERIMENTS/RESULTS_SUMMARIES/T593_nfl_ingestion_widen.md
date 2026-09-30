# T-593 — NFL ingestion widening (Wave 40, N1–N6 payload tier)

**Status:** capture path built and exercised live; no feature wired into any model. **Decisions logged:** n/a (GGL/DECISION_LOG owned by 41.1 — nothing written to either).

## Premise corrections
- The brief's path for `nfl_ingestion.py` was wrong; real path is `src/prediction_market_bot/c1_signal_ingestion/nfl_ingestion.py`.
- Finding 40.2 is **confirmed**: the allowlist kept 10 schedule / 7 team-stat columns and discarded weather, QB, coach, referee, sacks, QB hits, penalties — all present upstream.
- No ingestion-side capture store existed (readers cached parquet ad hoc), so `capture_extended()` is the capture path.

## D1 — columns per nflverse source
| Source | Delivered upstream | Retained before | Retained now (opt-in `include_extended`) | Still dropped |
|---|---|---|---|---|
| `schedules/games.csv` | full schedule incl. weather/QB/coach/ref/market | 10 core | +`temp, wind, roof, surface, away_qb_id/name, home_qb_id/name, away_coach, home_coach, referee` (N1–N4) | market lines/odds (circular, T-586 §5); `result`, `total` (outcome leakage); `stadium/location/gametime/div_game` (N7 inputs — "new accessor" tier, not payload) |
| `stats_team/stats_team_week_<yr>.csv` | full team-week stats | 7 (+ EPA splits, T-581 opt-in) | +`attempts, carries` (N5 pace), `sacks_suffered, def_sacks, def_qb_hits, penalties` (N6) | everything else (e.g. `def_tds`) — allowlist, not passthrough |

Core column lists are unchanged (`data_contracts.py` mirrors them); extension is opt-in, same pattern as T-581.

## D2 — allowlist and storage
Added fields are named in code (`_NFL_SCHEDULE_EXTENDED_FIELDS`, `_NFL_TEAM_STATS_EXTENDED_FIELDS`). Missing extended field in source → hard failure (extended mode only).
Storage delta (CSV-equivalent, includes the two provenance columns added at capture; 2026 season file): schedule +48.3 KB / 18 weeks ≈ **+2.7 KB/week**; team stats +13.9 KB / 3 played weeks ≈ **+4.6 KB/week**. On disk (parquet) the whole capture is 35 KB.
Readers: 103 NFL tests pass (t526, t581, t593, store, backtest, T1 game-market, results); `NFLTeamStatsStore.build_from_team_stats` builds 32 teams from the extended frames.

## D3/D4 — backfill and capture store
Source is a rolling snapshot: one retrieval covers all 2026 weeks; no historical versions exist.
- Retrieved 2026-09-30T05:05:36Z: `.../releases/download/schedules/games.csv` (sha256 `62032e26…4e91`, 2,182,348 B, 272 rows) and `.../stats_team/stats_team_week_2026.csv` (sha256 `8e4ec146…a42a`, 40,384 B, 96 rows). Manifest: `exp_output/NFL/INGESTION_CAPTURE/capture_manifest_2026_20260930T050536.json` (tracked; parquet is gitignored).
- Fill (games/week): wx temp/wind wk1–2 10/16, wk3 13/16, wk4+ 0 (indoor/unset or not yet published); roof/surface/coach populated all weeks; referee wk1–3 only; QB wk1–5 only (wk6+ null); team stats wk1–3, 32 rows/week, all six fields 32/32.
- **Unrecoverable:** point-in-time state before earlier kickoffs (QB/weather/referee as they stood pre-game for weeks 1–3) — the file only shows post-hoc values. Nothing invented; nulls left null. Forward captures must be repeated pre-kickoff to get true point-in-time values. Deep history 2014–2025 is retrievable in one call per season; not pulled (operator decision — post-hoc values, so leakage-prone for any pregame use).
- Append-only: timestamped filenames, `FileExistsError` on collision, per-row `_retrieved_at_utc`/`_source_url`.

## D5 — not captured
N7 travel inputs (stadium, location, gametime, div_game) — different tier; market columns and outcomes — excluded by design; nothing scheduled, no cron added.
