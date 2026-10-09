# W62.1 — MLB postseason shadow matcher (GG-532) + silent-arm alarm

**Status:** Part A + Part B merged and deployed (PR #195 cbbd2658; PR #198 35159a6; PR #199 7a884251 = VPS HEAD; t4-mlb restart not_needed on all three). GG-532 stays OPEN until a *scheduled* run writes post-fix rows (next T1 12:07Z; newest MLB row at 07:01Z is still 06:07Z, pre-fix).

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

## Part B — silent-arm alarm

`pregame_shadow/silent_arms.py`. Per arm: was a game scheduled to start in the last N hours (that arm's own schedule source) with zero rows written since (window start minus lead)? Pure `evaluate_arm`; loaders are separate and each failure yields `unknown` ("cannot check") — never red. Off-day / off-season / empty schedule = `idle`, not an alarm.

| Arm | Schedule source | N (h) | Why |
|---|---|---|---|
| MLB game-market shadow | cache_w47 games parquet (R/F/D/L/W, no postponed, no 07:33Z placeholders) | 12 | T1 runs every 6h; two missed T1 cycles |
| NFL shadow | schedule_extended.parquet | 12 | same cadence |
| NHL shadow | data/raw/nhl/schedule/*.json | 12 | T1 daily + T2 every 30 min while games run; 12h covers a full evening |
| NBA preseason / regular | data/raw/nba | 12 | hourly :57 cron |
| T1 MLB paper | audit_mlb.jsonl PT-/PG- sessions | 30 | PIPE-05 ~11:00Z + PIPE-06pre ~18:45Z once a day; 30h tolerates one late run |
| T4 MLB live | t4_mlb_cycle_log.jsonl | 3 | writes every 45-90s while live; 3h is far past any gap |

**Surfaces (computed on read, 60s cache, run in the venv python because the dashboard service has no pandas):** red chip per silent arm on `/project` strip; red row "SILENT ARM <name>" on Live Terminal health panel (plain text, e.g. "MLB game-market shadow: 3 games started, no rows for 19h"); `.claude/hooks/governance_scan.sh` prints all arms (alarm-only, `|| true`). Neither a green row is invented: with no silent arms the panel shows "0 of 7 arms silent".

**Proof it fires.** Fixture tests (`tests/test_silent_arms.py`, 13 pass): games + no rows -> silent; off-day -> idle; unknown schedule -> not red; per-arm windows; as-of bound. Replay on the VPS stored ledgers, MLB arm: 10-08 12:00Z ok; 15:00-21:00Z idle; **10-09 00:00Z SILENT 17.9h, 03:00Z SILENT 20.9h, 06:00Z SILENT 23.9h** (last row 10-08 06:07Z). I.e. the alarm would have gone red the first evening.

**Live verification (10-09 07:00Z, VPS 7a884251):** `/api/data` `silent_arms`: MLB ok, NFL ok, NHL ok, NBA preseason ok, NBA regular idle, T1 MLB ok, T4 idle; `/project` renders. First live deploy (PR #198) showed every arm "cannot check" (system python3 lacks pandas) — caught by the live check, fixed by PR #199. Red-chip visual at 390px not screenshotted (no browser session); layout reuses existing `.pill`/`.hw` classes.

**Known false-positive path:** a schedule that lists games Kalshi never listed markets for (T4 most exposed: only Kalshi-listed games). Documented, not mitigated; first sighting should be triaged, not silenced.
