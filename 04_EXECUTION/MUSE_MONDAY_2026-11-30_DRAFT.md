# Muse — Monday 2026-11-30 message (window draft; run 04_EXECUTION/MUSE_MONDAY_CHECKLIST.md in full before sending)

Known items so far (window, 2026-11-25):
1. **Usage budget first.** The week's allowance lasted ~24 h (reset 11-23 20:50 PT, cut off 11-24 ~20:28 PT): 523 commits from ~140
   scheduled jobs, only 58 chunks DONE (most usage spent by jobs waiting on the jammed browser and by mass job-file rewrites).
   Cut parallel queue jobs to ~15-25 so the allowance lasts seven days; snapshots reserved first; no mass job-file rewrites mid-week;
   HEARTBEAT line gains the usage % if Muse can see it.
2. **Archive restore.** Master was emptied by a1001ca5 (16:30 PT lineup run, 04:27Z); the window restored it 2026-11-25 with Earl's
   approval: ab9951c3 (parents 6aca92a3 + ba3e8963; every file from ba3e8963 + CLAIM C-1840). Muse: drop its local repair 804e69e3,
   sync to origin, and add a guard to every job: refuse to commit when the staged tree deletes more than N files.
3. **Collisions** (4 records filed 11-24): check the team / subject matches the QUEUE row before writing; record ids unique per chunk.
4. **Lineups + refs (C-2042..C-2131)**: claims stopped 11-24; resume only with a cap on concurrent runs (browser load, checklist item 11).
5. Late snapshot slots (19:00 / 19:30 PT) — confirm they ran 11-24.
6. **Families moved to bot crons (W128.5; only if `data_offload_install` is approved AND its first nightly run succeeded before the
   message goes out — check the box readback first; otherwise leave this item out):** retire as "moved to bot cron": MoneyPuck
   C-922..C-1101, C-1378..C-1751, C-2138, C-3516..C-4347; NHL officials C-3399..C-3515; NHL goalie logs C-4348..C-4763; Savant boards per
   12_EXPLORATORY/data_offload/TRIAGE.md. KEEP mlb_boxscore C-5128..C-5487 (statsapi returns 406 to the box). Point Muse's freed capacity,
   by value: NFL personnel / tendencies C-4764..C-5019 (check nflverse overlap first), browser-only NBA tables, umpscorecards / kofsports,
   snapshots and judgment work. Re-check the 500-chunk floor after the retire (muse_check.py).
