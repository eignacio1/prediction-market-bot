# W99.3 results (flex lane: B-036 + B-037 + B-017)

Purpose: PLUMBING. Measures: installs that can pass the gate 0 -> 4; arms whose rows carry reasons 3 -> 6; NBA store lag ~2 days -> under 1 day (pending install + first refresh).

## Part A - install gate (B-036): DONE
PR #405 merged (`d7ba397`). `scripts/install_batch_w99.py` runs t3_lock -> nba_events_refresh -> nba_engine_v3 -> picks_builder under ONE gate rule: a red is exempt only if it is a `NOT INSTALLED`/`STALE` key a step of this batch is about to install, or a named silent arm whose step has a line to install. Healthcheck faults, other arms' silences, foreign NOT INSTALLED still block. Box tasks `install_batch_w99_install|_readback|_uninstall` allowlisted. Tests: `tests/test_w99_3_install_batch.py` (the 11-03 red set passes; +fault / +other arm / +foreign key block; partial failure names the step).

## Part B - every arm says why (B-037, GG-1630): DONE
PR #407 merged (`292b863`). NHL shadow, NBA player points (EXP-039/040) and NBA engine v1/v2/v3 rows carry the top 3 counterfactual reasons (re-price with ONE input at its baseline; reason = (p_base - p_cf) x 100 points toward YES) or a `reasons_note`. The picks sheet shows them. Logging only: no price, threshold, order or stake changed. Tests: `tests/test_w99_3_reasons.py` (6, known-answer property included).

## Part C - NBA store on time (B-017): PR #409, install HELD
Diagnosis: the store's last game trailed by ~2 days because the only refresh (12:33Z) runs BEFORE the sources publish the previous day (ESPN box ~13:28Z, nba_stats schedule + pbp ~15:15Z). With fresh sources the same code reaches last_game_date = yesterday (2026-11-02 at probe time), 0 mismatches, 0.0 known-answer diff. The fault is the schedule, not the code. Fix: a second refresh at 15:46Z (minute free in hour 15; before the 16:02Z runner); the 12:33Z line is untouched; misleading comment corrected; entry registered. Test: `tests/test_w99_3_nba_refresh.py`.
Read-back (store last game = yesterday) is NOT yet done: it needs the held install plus the next 15:46Z run. Order of events: operator runs `install_batch_w99_install`, then after 15:46Z run `install_batch_w99_readback` and read `status.json`.
Faster free source (R-110): not needed; the sources publish by 15:15Z, the refresh is after that.
Noted: one game dropped for missing pbp (`no_pbp:1`) - the table keeps the box-score side; registered as a note, not changed.

## Registered, not fixed (Hard Rule 11)
- `tests/test_seat_interface.py` and `tests/test_tensions.py` are un-collectable on the existing tree.
- The `MARKERS` substring/prefix overlap (`nba_engine.live` vs `nba_engine.live_v3`) can recur in other cron installers.
