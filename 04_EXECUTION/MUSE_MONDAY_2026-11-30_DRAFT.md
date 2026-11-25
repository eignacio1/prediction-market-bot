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
