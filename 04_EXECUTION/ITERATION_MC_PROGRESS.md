# Iteration MC Progress — ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md

Cross-window progress log (Hard Rule 10: re-read fresh before appending; each window appends its own lines, path-scoped commit).

C2 DONE commit=abd92ae
C3 DONE commit=abd92ae — pre-existing T-341 infra in run_band_monitor.py/monitor.py (tercile edge_monotonicity + calibration slope CI, both warn-only, never trigger_kill_switch) already satisfies the ask; verified cron live via `crontab -l` on VPS (Mondays 14:20 UTC), last output 2026-07-20. No new code needed for C3 — C2's per-band clean_n fix is what restores its ability to actually fire (GG-124's blackout previously kept every band UNDERPOWERED, so alarms never had a chance to trigger).
