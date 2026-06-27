# ADR-0032 — MLB-G1 Gate Close

**Status:** ACCEPTED  
**Date:** 2026-06-27  
**Session:** S90  
**Operator:** Earl Ignacio  
**Scope:** MLB paper trading arm — institutional validation gate (MLB-G1)

---

## Context

The MLB paper trading arm (PIPE-05, PIPE-05.5, PIPE-05R, PIPE-06pre, PIPE-05FX, T3 MLB) was built over sessions S81–S89. All 9 MLB crons were paused pending completion of tasks T-192 through T-199 (the MLB-G1 institutional validation gate). This ADR records the completion of all MLB-G1 gate tasks and authorizes cron re-enablement.

MLB-G1 is not a capital gate. No live capital is authorized here — that requires G6 (30 resolved paper bets, positive P&L, DS sign-off). MLB-G1 is an institutional readiness gate: the arm must be architecturally sound, monitored, and defensively instrumented before it is permitted to fire.

---

## Tasks Completed

| Task | Description | Status |
|---|---|---|
| T-192 | MLB C1 ingestion integration tests | COMPLETE (S88) |
| T-193 | Feature CSV freshness guard (3-day warn / 7-day halt) | COMPLETE (S89, 23 tests) |
| T-194 | Resolution age-out: positions >48h unresolvable → `aged_open` tag + C6 WARNING | COMPLETE (S90, 15 tests) |
| T-195 | Silent fallback audit: two `except Exception: pass` in `_is_mlb_game_in_progress()` and `_fetch_live_game_pks()` now emit C6 WARNING when `logger` is provided | COMPLETE (S90, 17 tests) |
| T-196 | Cron timing comment corrected: `run_mlb_paper_trade.py` docstring and inline comment updated from 03:00 UTC to 11:00 UTC (7am ET) to match `deploy/cron.conf` | COMPLETE (S90) |
| T-197 | MLB kill switch drill: `SystemMonitor.run_kill_switch_drill()` executed; halt_time_ms=0.116; passed_sla=True; APR-0023 written | COMPLETE (S90) |
| T-198 | Governance gaps registered: GG-043 (MLB Kelly fraction) and GG-044 (C7 drift baselines) | COMPLETE (S90) |
| T-199 | Full test suite: 2044 passed / 7 skipped (up from 2012); crons re-enabled; VPS deployed; this ADR | COMPLETE (S90) |

---

## Crons Enabled

| Cron | Schedule | Pipeline |
|---|---|---|
| PIPE-05FX feature refresh | 22:30 UTC daily | `generate_mlb_features.py --seasons 2026` |
| PIPE-06pre pregame context | 16:30 UTC daily | `run_mlb_pregame.py` |
| PIPE-05 T1 paper trading | 11:00 UTC daily | `run_mlb_paper_trade.py` |
| PIPE-05.5 T2 lineup overlay | 19:30 UTC daily | `run_t2_mlb_sameday.py` |
| PIPE-05R resolution | 06:30 UTC daily | `run_resolve_mlb.py` |
| T3 MLB pre-tip scan | `*/15 20-23` and `*/15 0-3` UTC | `run_t3_mlb_pretip.py` |

**Not enabled (explicitly deferred):**
- **T4 MLB** (`run_t4_mlb_live.py`): GG-007 — T4 constants uncalibrated; deferred to MLB-G3.
- **MLB calib monitor** (`run_mlb_calib_monitor.py`): GG-044 — no closed positions; NBA drift baselines wrong for MLB; deferred to post-first-resolutions.

---

## Defensive Instrumentation Added (S90)

### T-194 — Resolution age-out
`PaperTrader.mark_aged_open(position_id, reason, session_id)` — tags positions in-place within `open_positions` when MLB Stats API cannot resolve after 48h. Capital remains deployed (bankroll invariant preserved). C6 WARNING emitted to audit_mlb.jsonl.

`run_resolve_mlb.py` — 48h age-out detection loop: positions with `game_date < today` and `actual_hits is None` are checked against age threshold. `>48h` → `mark_aged_open()` + stderr output. `≤48h` → existing skip path (logs `player_stats_fetch_failed` WARNING with `age_hours` field added).

### T-195 — Silent exception logging
`_is_mlb_game_in_progress()` (PIPE-05) and `_fetch_live_game_pks()` (PIPE-05.5) — both previously had bare `except Exception: pass` (completely silent on API failure). Both now accept optional `logger` and `session_id` parameters. When logger is provided, API failures emit `mlb_schedule_api_failed` WARNING to C6 instead of swallowing silently. Both functions remain permissive on failure (return False / empty set) — the contamination guard is conservative by design.

### T-196 — Timing comment fix
`run_mlb_paper_trade.py` module docstring and inline comment block both corrected from `03:00 UTC (11pm ET)` to `11:00 UTC (7am ET)`. The cron.conf entry was already correct (`0 11 * * *`); only the source code comments were wrong.

---

## Open Governance Gaps (registered, not resolved)

| Gap | Description | Priority |
|---|---|---|
| GG-043 | MLB Kelly fraction inherits NBA 0.10 — not MLB-calibrated | LOW (paper only) |
| GG-044 | C7 drift baselines (Brier=0.2416, ECE=0.0247) are NBA values | LOW (calib monitor disabled) |
| GG-007 | T4 MLB constants uncalibrated | LOW (T4 not enabled) |
| GG-004 | Commercial EV validation vs Kalshi market prices (EXP-017) | OPEN (G6 blocker) |

---

## Decision

All MLB-G1 gate tasks are complete. The MLB arm is cleared to run paper trades. No live capital is authorized. G6 remains the capital gate (30 resolved paper bets, positive P&L, DS sign-off per APR-0017/APR-0019/ADR-0028).

Next review point: MLB first resolved paper bet (triggers GG-043 and GG-044 resolution timeline).
