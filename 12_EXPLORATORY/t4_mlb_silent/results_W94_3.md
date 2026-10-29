# W94.3 results — T4 MLB "silent" alarm (2026-10-29)

**Verdict: the process was not dead. The alarm read a scheduled start 4 minutes before first pitch.**

## Cause (Part A)
- Alarm: `pregame_shadow/silent_arms.py`, arm `t4_mlb` (window 3h, lead 0). It counts a game as "started" at `start_utc` from the games cache, and requires a cycle-log row newer than `now - 3h`.
- 2026-10-29 00:04Z: MIL@TB (`KXMLBHIT-26OCT282000MILTB`) had cached start 00:00:00Z. Last cycle-log row was 2026-10-28 04:29:46Z (previous night's game), 19.64h earlier. Gauge: SILENT.
- Box evidence: first row of the game at 00:08:14Z; rows every cycle after (00:10:26Z C0241); `t4-mlb` active since 2026-10-27 04:58:35Z, NRestarts=0; box silent_arms at 00:17Z: `silent=[]`, `t4_mlb=ok`.
- T4 writes a row only once a live batter state exists, so it is quiet from the scheduled start to first pitch by design.
- Recurrence (box cycle log vs cache start, games since 2026-09-27; lag = first row after start): typical 8-16 min on `:00` starts — 10-24 16.4, 10-25 9.8, 10-27 10.1, 10-28 7.7, 10-29 8.2. Cache starts are rounded to the hour or half hour (no actual first-pitch time). Any night whose previous row is >3h old reads RED for ~8-16 min after the scheduled start.
- Not this cause, not explained here (lag far above the pattern): 10-06 22:00Z (218 min), 10-12 21:00Z (106 min), 10-18 21:08Z (1620 min). Possibly doubleheaders, postponed or untracked games; not checked. Registered for follow-up (GG-1441).

## Fix (Part B)
**No code changed.** The only candidate is a start-grace on the gauge (e.g. 0.5h after scheduled start, covers the measured max of 16.4 min), which the block bars ("never the gauge"). Recommendation to the window: add `start_grace_h=0.5` for `t4_mlb` only, with a regression test on the 2026-10-29 00:04Z case (replay: SILENT today, ok with grace) and a test that a real 43h outage (GG-163) still alarms. Hard Rule 13 sweep: other arms are not exposed — the pregame arms count rows up to `lead_h` before the window and `t1_mlb` has a 30h window; `t4_mlb` is the only live-only arm.
- Budget read back: silent arms 1 -> 0 on the box (2026-10-29 00:17Z). It will go RED again for ~10 min at each night's first pitch until the grace lands.
- Hard Rule 14 consequence: an install attempted inside a first-pitch window will read RED; install outside it.
