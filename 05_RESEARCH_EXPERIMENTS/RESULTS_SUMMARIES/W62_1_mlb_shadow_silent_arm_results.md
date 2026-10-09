# W62.1 — MLB postseason shadow matcher (GG-532) + silent-arm alarm

**Status:** Part A in progress (code + tests, awaiting merge/deploy). Part B not started.

## Part A — reproduction (VPS, 2026-10-09 06:16Z, read-only dry-run)

W61.2's mechanism is **partly confirmed, partly corrected**:

* **The arm was not fully silent.** The scheduled 06:07Z T1 run wrote 33 rows (CWS@CLE 2026-10-10 20:00 ET, matched fine). The T2/T3 ledgers were quiet since 10-08 01:43Z because no event was inside their 4-8h / 15-60min windows with a *matching* schedule row.
* **Ticker time is not a systematic placeholder.** Every settled postseason event in the ledger (10-06 .. 10-07, 7 events) has ticker time == cache start (diff 0.00h). The one mismatch is `KXMLBGAME-26OCT081700CLECWS`: ticker 17:00 ET, cache 20:00 ET (diff 3.00h) — a single event whose game was moved after listing. That one event cost the arm its T2/T3 rows for the 10-08 game.
* **Placeholder rows are real and have a signature:** every 2026 L/W preview row carries start `07:33:00Z` (LAD@MIL 10-11 is a real-team placeholder; 10-12.. are generic "NL High/NL Low" rows with no team match).
* Open events today (11): CWS@CLE 10-10 matches (4 series); LAD/MIL 10-11 matches teams but is a 07:33Z placeholder; 10-12/14/15 have no team row at all.

## Part A — fix

`match_game` (mlb_forecaster.py): teams + **ET game date**; the ticker HHMM only breaks same-day ties (doubleheader → nearest start; equidistant → refused). Kickoff is always the cache's. Placeholder-only day → skip reason `schedule_placeholder`; no row → `no_kickoff`. Pre-game guarantee unchanged: a started game has negative horizon → `outside_band_windows`, no row; no backfill.

Consumer disposition (GG-072 rule):
| Consumer | Disposition |
|---|---|
| `MLBForecaster.forecast` (via `game()`) | fixed (same matcher) |
| `run_mlb_pregame_shadow.py` kickoff_for | fixed; passes new `kickoff_miss_reason` |
| `mlb_settlement.find_final` | **broken the same way** (ticker time vs final's start, TOL 45 min) — a postseason row written under the new rule would never have settled when the ticker time is off. Fixed with the same `match_game`. |
| `runner.run_once` | new optional `kickoff_miss_reason` kwarg, default unchanged; NFL/NHL/NBA callers untouched |
| NFL/NBA forecasters, dashboards | do not use MLBScheduleIndex / read ledgers only — no change |

Tests: `tests/test_mlb_schedule_match.py` (ticker≠cache, late-evening ET date, placeholder, no-row, doubleheader, equidistant, settlement mismatch, runner writes/never-after-start/placeholder reason).
