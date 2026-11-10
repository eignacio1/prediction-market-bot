# Session handoff - W107.2 (B-060 information speed) - 2026-11-10T03:30Z

vision_pillar: BREADTH / EXECUTION
gap_measure: B4-adjacent - edge families measured (news / information speed); EXECUTION E1 untouched
gap_delta: news-lag measured for 3 scorable news types (to_out n=50, q_to_active n=53, ALL n=105; to_questionable and out_to_active n<=2 unscorable) at 20-min resolution; capture ready, not run
pattern_sweep: n/a (no defect fixed) - one lint failure in this block's own new file (run_study.py write not routed through safe_out), fixed there; grep of 12_EXPLORATORY found no other unrouted writers in files this block added
surface_delta: +1 registered cron component (deploy/cron.news_burst, status live in the registry but NOT installed on the box; nothing new runs until the install task is approved); no new service

## Status: DONE | B-060: measured, NO at 20-min resolution; sub-20-min unmeasured | PR #453 merged (978172a), CI green on head a90ca2d

## Result (see 12_EXPLORATORY/news_lag/RESULT.md, study_results.json)
228 reports (2026-10-21..11-09), 276 status-change events, 128 games priced, KXNBAGAME YES-mid only, post-report move in the news direction:
- ALL: +20 min +0.34c (n=105, CI -0.02..+0.76); +60 min +0.47c (n=77, CI +0.08..+1.08); +120 min -0.02c.
- to_out: +20 min +0.47c (n=50, CI -0.19..+1.35); +60 min +0.75c (n=40, CI -0.06..+1.76).
- q_to_active: +20 min +0.23c (n=53, CI -0.28..+0.69).
- Move still to come after the first snapshot (20->60 min): ALL -0.09c (n=77); to_out +0.01c (n=40). Pre-news drift ALL +0.16c (n=147).
- Cost wall (106.2): taker 1.5-2.3c each way on game lines. Every cell is far below it: NO.
Data epoch: no fills used; the 2026-11-06T01:03:42Z NO-side fill epoch does not apply.

## Part C (prepared, NOT RUN)
scripts/news_burst_capture.py (one listing call per sweep, ~20 s, 30 min, flock, 40 MB/day cap, public GET only, streams to
exp_output/KALSHI_HISTORY/news_burst/; fixture RSS test passes), deploy/cron.news_burst (55 21,22,23 UTC = 16:55/17:55/18:55 EST;
DST: shifts one hour later relative to ET during EDT, revisit in March), scripts/news_burst_capture_install.py (budget-gated,
idempotent, tested), allowlisted tasks news_burst_capture_install / _readback / _uninstall, RUNTIME_REGISTRY entry.

## OPERATOR DECISION (one)
Approve `news_burst_capture_install` by name? My recommendation: low-priority yes. It is cheap and read-only, but the prior is that
a sub-20-min window will not clear a 1.5-2.3c wall given the sub-1c total moves above. Install is refused automatically if the
SURFACE BUDGET is RED (ride_board_install is currently the box's only red - approve/clear that first or this refuses).

## Stage per factor (ADR-0075)
Injury-report availability news (status changes): aggregated + interpreted (event study vs price); NOT applied (no tradable path).
Granularity index parts: split = status transition (no star/rotation split); history rank = not computed; matchup cross = none; market map = moneyline only; application = none.

## Caveats / found-not-fixed (register-and-stop)
- No star vs rotation typing (no local minutes source); moneyline only; no NHL goalie/lineup news.
- Unmatched events: SAS@DAL 108, MEM@GSW 60, GSW@DEN 60, CHI@MIL 60, HOU@SAS 48 - likely Kalshi team-code differences or games before archive window. Worth a mapping check before any pre-registration.
- 190 events stamp at hour 0 ET - probable list re-publication; not investigated. Report file-name stamps differ from header time by up to 15 min (header used).
- tip_utc assumes evening-ET games (12-hour clock, no AM/PM): matinee games would be mis-stamped. quant/news_lag.py has dead code in _kind.
- Existing stub src/prediction_market_bot/quant/inplay_nhl.py:37 (session-start scan) untouched, out of scope.
- ROLLING_BACKLOG.json not edited. B-060 state: measured; suggest "closed NO at 20-min resolution; burst capture optional".
- Session-start protocol run in brief form per block text; hook output showed 256 open GGs, no duplicate IDs.
