# NBA engine v2/v3 coverage misses, 2026-11-04 slate (W102.1, B-030)

Coverage on the 11-04 slate: v1 56/56, v2 44/56, v3 38/56. A row is logged only if `tip-60 <= now < tip`, once per event.

## Root cause (all arms): kernel OOM on a 961 MB box, with no in-window retry
- Box: 1 vCPU, 961 MB RAM, 2 GB swap. Each engine runner is ~500 MB.
- OOM killer took 22 processes (21 python, 1 systemd) between 23:13:59Z and 00:18:42Z on 11-04. 481 OOM kills since 10-30 (first 10-30 00:08Z, last 11-05 01:27Z). No OOM since the T3 lock stagger went in (11-05 02:11Z).
- Games missed all tipped 00:00Z (ATLWAS, PHIDET) or 00:30Z (CHABKN, CHINYK, MILBOS); windows 23:00-00:30Z, i.e. the OOM burst.
- No completed v2 or v3 run between 23:02Z and 00:22Z. First logged v2 run after the window: 00:37:05Z, past those tips.

## Per arm
- **v1** completed 23:02:25Z (204 rows) and 00:22:37Z (612 rows): 56/56. It runs first in its fire and survived.
- **v2** is chained serially behind v1 in one `sh -c`. When v1 ran long or was killed, v2 never started or was killed itself. Cost: 12 games.
- **v3** does `flock -w 240` and exits silently on timeout; with v1/v2 holding the lock through the burst it never ran. Cost: 18 games.
- Earlier nights: v3 not installed 10-30 to 11-01 (0 rows). 11-02: v1 13/60, v2 37/60, v3 0/60.

## Contributing weaknesses (fixed here)
1. No in-window retry or catch-up. Fix: `nba_engine/catchup.py` (10 MB stdlib process) runs only an arm whose last completed run is >12 min old, one at a time, retrying once if killed. Cron `7,17,...,57`.
2. A killed run left no trace (bare "Killed"). Fix: `nba_engine/attempts.py`; each runner writes start/end to `attempts.jsonl`; a start with no end is a kill.
3. `live.run()` loads history and calibrates before checking for pending events, so every fire pays full memory cost (registered, not changed: frozen runner logic).

## Not established
No miss was found that was not OOM-related. Most "FAIL" fires in the scoring had no game in the window and cost nothing.

## Install
Cron line is prepared as allowlisted task `nba_engine_catchup_install` (backup + readback; `_readback`/`_uninstall` alongside). Not run; needs the operator's named approval.
